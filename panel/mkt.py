"""Pazarlama Merkezi (1/2): reklam + organik kanalların iş/kâr düzeyinde ölçümü.

- Atıf (attribution): iş -> form mesajı -> ziyaret oturumu (kanal, kampanya, anahtar kelime, gclid)
- Reklam harcaması: CSV içe aktarma, elle giriş, Google Ads API senkronu (canlı hesapla DENENMEDİ)
- Kampanya/anahtar kelime kâr raporu, kanal karşılaştırma panosu, müşteri yaşam değeri
- Telefon aramaları: tıklama + webhook ile gelen arama kaydı + elle kayıt, numara havuzu (kanala göre numara)
- Çevrimdışı dönüşüm (gclid) geri bildirimi, bütçe/CPA uyarıları (zamanlayıcı)

NOT: Kâr = "tahmini şirket payı" (iş tutarı x firma yüzdesi) - reklam harcaması. Parça maliyeti kayıtlı değildir.
Google Ads / Search Console çağrıları `_http` üzerinden yapılır (testte sahte yanıtla doğrulandı).
"""
import csv
import hashlib
import hmac
import io
import logging
import re
import secrets
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta, date
from urllib.parse import parse_qs

import requests
from fastapi import Depends, HTTPException, Request

import governance
import notify

log = logging.getLogger("mkt")

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                     # pragma: no cover
    TR = timezone(timedelta(hours=3))

DONE = ("tamamlandi", "faturalandi")
ALERT_FROM_HOUR = 9
MASK = "********"
SECRET_KEYS = ("client_secret", "ads_refresh_token", "gsc_refresh_token", "developer_token")
ADS_CH = ("google_ads", "meta_ads", "diger_reklam")

DEFAULT = {
    "site_url": "https://servisplus.net.tr",
    "call_numbers": [],            # [{number, display, channel, campaign}]
    "call_secret": "",
    "cpa_limit": 0.0,              # tamamlanan iş başına azami reklam maliyeti (0 = uyarı yok)
    "no_job_days": 14, "no_job_min_spend": 300.0,
    "alerts": True,
    "campaign_alias": {},          # {"utm_campaign değeri": "Ads kampanya adı"}
    "districts": [],
    "disclaimer": "",
    "business": {"name": "ServisPlus", "phone": "", "address": "", "city": "", "price_range": "", "hours": "", "same_as": [], "areas": [], "services": []},
    "google": {"client_id": "", "client_secret": "", "ads_refresh_token": "", "gsc_refresh_token": "", "developer_token": "",
               "customer_id": "", "login_customer_id": "", "api_version": "v23", "conversion_action": "", "gsc_site": "",
               "auto_sync": False, "auto_upload": False},
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _f(x, d=0.0):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return d


def _today():
    return datetime.now(TR).date()


def _tr_day(s):
    s = s or ""
    if len(s) <= 10:
        return s[:10]
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(TR).date().isoformat()
    except ValueError:
        return s[:10]


_TRMAP = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "Ç": "c", "Ğ": "g", "İ": "i", "I": "i", "Ö": "o", "Ş": "s", "Ü": "u"})


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").translate(_TRMAP).lower()).strip("-")


def lower_tr(s):
    return (s or "").replace("İ", "i").replace("I", "ı").lower()


def last10(p):
    return re.sub(r"\D", "", p or "")[-10:]


def spend_key(day, ch, camp):
    return hashlib.md5(f"{day}|{ch}|{(camp or '').lower()}".encode()).hexdigest()


def parse_num(s):
    s = re.sub(r"[^\d,.\-]", "", str(s or ""))
    if not s or s in ("-", ".", ","):
        return 0.0
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        th = "." if dec == "," else ","
        s = s.replace(th, "").replace(dec, ".")
    elif "," in s:
        s = s.replace(",", "") if re.fullmatch(r"-?\d{1,3}(,\d{3})+", s) else s.replace(",", ".")
    elif "." in s and re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_day(s):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%b %d, %Y", "%d %b %Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


_H = {"day": {"day", "date", "gun", "tarih"}, "campaign": {"campaign", "kampanya", "kampanyaadi", "campaignname"},
      "cost": {"cost", "maliyet", "harcama", "spend", "tutar"}, "clicks": {"clicks", "tiklamalar", "tiklama"},
      "impr": {"impr", "impressions", "gosterimler", "gosterim"}, "cid": {"campaignid", "kampanyakimligi", "kampanyaid"}}


def parse_spend_csv(text):
    """Google Ads rapor CSV'sini (TR/EN, ; , veya sekme) ayrıştırır. Başlık satırından önceki başlık satırları atlanır."""
    text = (text or "").lstrip("﻿")
    lines = [l for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines[:20]):
        for delim in (",", ";", "\t"):
            cols = [re.sub(r"[^a-z0-9]", "", slug(c).replace("-", "")) for c in next(csv.reader([line], delimiter=delim), [])]
            idx = {}
            for k, al in _H.items():
                for j, c in enumerate(cols):
                    if c in al and k not in idx:
                        idx[k] = j
            if "day" in idx and "cost" in idx:
                rows = []
                for r in csv.reader(lines[i + 1:], delimiter=delim):
                    if len(r) <= max(idx.values()):
                        continue
                    d = parse_day(r[idx["day"]])
                    if not d:
                        continue
                    rows.append({"day": d, "campaign": r[idx["campaign"]].strip() if "campaign" in idx else "",
                                 "cost": parse_num(r[idx["cost"]]), "clicks": int(parse_num(r[idx["clicks"]])) if "clicks" in idx else 0,
                                 "impressions": int(parse_num(r[idx["impr"]])) if "impr" in idx else 0,
                                 "campaign_id": r[idx["cid"]].strip() if "cid" in idx else ""})
                return rows
    raise HTTPException(422, "Başlık satırı bulunamadı: dosyada 'Gün/Day' ve 'Maliyet/Cost' sütunları olmalı")


def _http(method, url, headers=None, json_body=None, data=None, timeout=40):
    r = requests.request(method, url, headers=headers, json=json_body, data=data, timeout=timeout)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text[:300]}")
    return r.json() if r.text else {}


def gclid_of(query):
    q = parse_qs((query or "").lstrip("?"))
    return (q.get("gclid") or [""])[0]


# ============================================================ ayarlar
async def get_cfg(db):
    d = await db.app_settings.find_one({"_id": "mkt"}, {"_id": 0}) or {}
    out = {**DEFAULT, **d}
    out["google"] = {**DEFAULT["google"], **(d.get("google") or {})}
    out["business"] = {**DEFAULT["business"], **(d.get("business") or {})}
    if not out.get("call_secret"):
        out["call_secret"] = secrets.token_urlsafe(18)
        await db.app_settings.update_one({"_id": "mkt"}, {"$set": {"call_secret": out["call_secret"]}}, upsert=True)
    return out


# ============================================================ Google API
def g_token(g, kind):
    rt = g.get(f"{kind}_refresh_token")
    if not (g.get("client_id") and g.get("client_secret") and rt):
        raise RuntimeError("Google bağlantı bilgileri eksik (istemci kimliği/gizli anahtar/yenileme anahtarı)")
    r = _http("POST", "https://oauth2.googleapis.com/token", data={"client_id": g["client_id"], "client_secret": g["client_secret"],
                                                                  "refresh_token": rt, "grant_type": "refresh_token"})
    return r["access_token"]


def _ads_headers(g, tok):
    h = {"Authorization": "Bearer " + tok, "developer-token": g.get("developer_token", ""), "Content-Type": "application/json"}
    if g.get("login_customer_id"):
        h["login-customer-id"] = re.sub(r"\D", "", g["login_customer_id"])
    return h


def ads_query(g, gaql):
    tok = g_token(g, "ads")
    cid = re.sub(r"\D", "", g.get("customer_id", ""))
    if not cid or not g.get("developer_token"):
        raise RuntimeError("Müşteri kimliği veya geliştirici anahtarı eksik")
    url = f"https://googleads.googleapis.com/{g.get('api_version') or 'v23'}/customers/{cid}/googleAds:search"
    out, token = [], None
    for _ in range(50):
        body = {"query": gaql, "pageSize": 10000}
        if token:
            body["pageToken"] = token
        r = _http("POST", url, _ads_headers(g, tok), body)
        out += r.get("results", [])
        token = r.get("nextPageToken")
        if not token:
            break
    return out


async def sync_spend(db, days=30):
    cfg = await get_cfg(db)
    g = cfg["google"]
    d1 = _today()
    d0 = d1 - timedelta(days=max(1, min(int(days), 400)) - 1)
    import asyncio
    res = await asyncio.to_thread(ads_query, g, "SELECT segments.date, campaign.id, campaign.name, metrics.cost_micros, metrics.clicks, metrics.impressions "
                                  f"FROM campaign WHERE segments.date BETWEEN '{d0.isoformat()}' AND '{d1.isoformat()}'")
    n = 0
    for r in res:
        day = (r.get("segments") or {}).get("date")
        c = r.get("campaign") or {}
        m = r.get("metrics") or {}
        if not day:
            continue
        doc = {"id": spend_key(day, "google_ads", c.get("name")), "day": day, "channel": "google_ads", "campaign": c.get("name", ""),
               "campaign_id": str(c.get("id", "")), "cost": round(_f(m.get("costMicros")) / 1_000_000, 2), "clicks": int(_f(m.get("clicks"))),
               "impressions": int(_f(m.get("impressions"))), "source": "api", "updated_at": _now()}
        await db.ad_spend.update_one({"id": doc["id"]}, {"$set": doc}, upsert=True)
        n += 1
    await db.app_settings.update_one({"_id": "mkt"}, {"$set": {"last_spend_sync": _now()}}, upsert=True)
    return n


def _conv_time(iso):
    try:
        dt = datetime.fromisoformat((iso or "").replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except ValueError:
        dt = datetime.now(timezone.utc)
    dt = dt.astimezone(TR)
    return dt.strftime("%Y-%m-%d %H:%M:%S") + dt.strftime("%z")[:3] + ":" + dt.strftime("%z")[3:]


async def upload_conversions(db, force_job_ids=None):
    """Tamamlanan işlerin gclid'ini Google Ads'e çevrimdışı dönüşüm olarak gönderir (90 günden eski gclid atlanır)."""
    cfg = await get_cfg(db)
    g = cfg["google"]
    if not g.get("conversion_action"):
        raise RuntimeError("Dönüşüm eylemi (conversion_action) girilmemiş")
    since = (datetime.now(timezone.utc) - timedelta(days=89)).isoformat()
    q = {"status": {"$in": list(DONE)}, "completed_at": {"$gte": since}, "ads_conv_uploaded_at": {"$in": [None, ""]}}
    jobs = await db.service_jobs.find(q, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(2000)
    if force_job_ids:
        jobs = [j for j in jobs if j["id"] in force_job_ids]
    att = await attribution(db, jobs)
    todo = [(j, att[j["id"]]["gclid"]) for j in jobs if att.get(j["id"], {}).get("gclid")]
    if not todo:
        return {"uploaded": 0, "skipped": len(jobs)}
    import asyncio
    tok = await asyncio.to_thread(g_token, g, "ads")
    cid = re.sub(r"\D", "", g.get("customer_id", ""))
    body = {"partialFailure": True, "conversions": [
        {"gclid": gc, "conversionAction": g["conversion_action"], "conversionDateTime": _conv_time(j.get("completed_at")),
         "conversionValue": round(_net(j) or _f(j.get("total_amount")), 2), "currencyCode": "TRY"} for j, gc in todo]}
    url = f"https://googleads.googleapis.com/{g.get('api_version') or 'v23'}/customers/{cid}:uploadClickConversions"
    status, err = "ok", ""
    try:
        r = await asyncio.to_thread(_http, "POST", url, _ads_headers(g, tok), body)
        if r.get("partialFailureError"):
            status, err = "partial", str(r["partialFailureError"].get("message", ""))[:300]
    except Exception as e:                              # noqa: BLE001
        status, err = "error", str(e)[:300]
    for j, gc in todo:
        await db.ads_uploads.insert_one({"id": str(uuid.uuid4()), "job_id": j["id"], "job_number": j.get("job_number", ""), "gclid": gc[:12] + "…",
                                         "status": status, "error": err, "at": _now()})
        if status != "error":
            await db.service_jobs.update_one({"id": j["id"]}, {"$set": {"ads_conv_uploaded_at": _now()}})
    return {"uploaded": len(todo) if status != "error" else 0, "status": status, "error": err}


# ============================================================ atıf + hesap
def _net(j):
    total = _f(j.get("total_amount"))
    pct = _f(j.get("technician_commission_percent"))
    share = total * pct / 100 if pct > 0 else total
    return share - _f(j.get("parts_cost"))   # parça maliyeti şirket payından düşer


async def attribution(db, jobs):
    ids = [j["id"] for j in jobs]
    out = {}
    msgs = await db.contact_messages.find({"job_id": {"$in": ids}}, {"_id": 0}).to_list(200000) if ids else []
    sids = list({m.get("sid") for m in msgs if m.get("sid")})
    sess = {s["id"]: s for s in await db.visitor_sessions.find({"id": {"$in": sids}}, {"_id": 0, "events": 0, "pages": 0}).to_list(200000)} if sids else {}
    for m in msgs:
        src = m.get("source") or {}
        s = sess.get(m.get("sid")) or {}
        out[m["job_id"]] = {"channel": src.get("channel") or m.get("channel") or s.get("channel") or "",
                            "campaign": src.get("campaign") or s.get("campaign") or "", "term": src.get("term") or s.get("term") or "",
                            "gclid": gclid_of(s.get("landing_query")), "landing": src.get("landing_page") or s.get("landing_page") or m.get("page") or "",
                            "via": "form", "sid": m.get("sid") or ""}
    calls = await db.call_log.find({"job_id": {"$in": ids}}, {"_id": 0}).to_list(50000) if ids else []
    for c in calls:
        out.setdefault(c["job_id"], {"channel": c.get("channel", ""), "campaign": c.get("campaign", ""), "term": "", "gclid": "", "landing": "",
                                     "via": "call", "sid": ""})
    for j in jobs:
        out.setdefault(j["id"], {"channel": j.get("source_channel") or "", "campaign": j.get("source_detail") or "", "term": "", "gclid": "",
                                 "landing": "", "via": "manual", "sid": ""})
    for v in out.values():
        v["channel"] = v["channel"] or "belirtilmemis"
    return out


def _rng(date_from, date_to, days=30):
    d1 = date.fromisoformat(date_to) if date_to else _today()
    d0 = date.fromisoformat(date_from) if date_from else d1 - timedelta(days=days - 1)
    return d0.isoformat(), d1.isoformat()


def _blank():
    return {"sessions": 0, "call_clicks": 0, "whatsapp": 0, "forms": 0, "calls": 0, "leads": 0, "jobs": 0, "done": 0, "revenue": 0.0, "net_est": 0.0,
            "cost": 0.0, "clicks": 0, "impressions": 0}


async def core(db, d0, d1):
    """(kanal, kampanya) bazında birleşik ölçüm."""
    cfg = await get_cfg(db)
    alias = {lower_tr(k): v for k, v in (cfg.get("campaign_alias") or {}).items()}
    spend = await db.ad_spend.find({"day": {"$gte": d0, "$lte": d1}}, {"_id": 0}).to_list(200000)
    names, ids = {}, {}
    for s in spend:
        names[lower_tr(s.get("campaign"))] = s.get("campaign")
        if s.get("campaign_id"):
            ids[str(s["campaign_id"])] = s.get("campaign")

    def canon(camp):
        c = (camp or "").strip()
        if not c:
            return "(kampanya yok)"
        lc = lower_tr(c)
        return alias.get(lc) or names.get(lc) or ids.get(c) or c

    rows = defaultdict(_blank)
    terms = defaultdict(lambda: {"sessions": 0, "calls": 0, "forms": 0, "jobs": 0, "done": 0, "revenue": 0.0, "net_est": 0.0})
    for s in await db.visitor_sessions.find({"day": {"$gte": d0, "$lte": d1}}, {"_id": 0, "events": 0, "pages": 0}).to_list(300000):
        r = rows[(s.get("channel") or "bilinmiyor", canon(s.get("campaign")))]
        r["sessions"] += 1
        r["call_clicks"] += int(s.get("conv_call") or 0)
        r["whatsapp"] += int(s.get("conv_whatsapp") or 0)
        r["forms"] += int(s.get("conv_form") or 0)
        if s.get("term"):
            t = terms[(s.get("channel") or "", s["term"])]
            t["sessions"] += 1
            t["calls"] += int(s.get("conv_call") or 0)
            t["forms"] += int(s.get("conv_form") or 0)
    for m in await db.contact_messages.find({"created_at": {"$gte": d0, "$lt": d1 + "~"}}, {"_id": 0, "channel": 1, "source": 1}).to_list(100000):
        src = m.get("source") or {}
        rows[(m.get("channel") or "bilinmiyor", canon(src.get("campaign")))]["leads"] += 1
    for c in await db.call_log.find({"day": {"$gte": d0, "$lte": d1}}, {"_id": 0}).to_list(100000):
        rows[(c.get("channel") or "bilinmiyor", canon(c.get("campaign")))]["calls"] += 1
    jobs = await db.service_jobs.find({"created_at": {"$gte": d0, "$lt": d1 + "~"}}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(200000)
    att = await attribution(db, jobs)
    for j in jobs:
        a = att[j["id"]]
        r = rows[(a["channel"], canon(a["campaign"]))]
        r["jobs"] += 1
        t = terms[(a["channel"], a["term"])] if a["term"] else None
        if t:
            t["jobs"] += 1
        if j.get("status") in DONE:
            r["done"] += 1
            r["revenue"] += _f(j.get("total_amount"))
            r["net_est"] += _net(j)
            if t:
                t["done"] += 1
                t["revenue"] += _f(j.get("total_amount"))
                t["net_est"] += _net(j)
    for s in spend:
        r = rows[(s.get("channel") or "google_ads", canon(s.get("campaign")))]
        r["cost"] += _f(s.get("cost"))
        r["clicks"] += int(_f(s.get("clicks")))
        r["impressions"] += int(_f(s.get("impressions")))
    # eski aylık harcama ayarı: ad_spend kaydı yoksa google_ads kanalına yaz
    if not spend:
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        sp = (g.get("profit") or {}).get("ad_spend") or {}
        months, cur = set(), date.fromisoformat(d0)
        while cur <= date.fromisoformat(d1):
            months.add(cur.strftime("%Y-%m"))
            cur += timedelta(days=28)
        months.add(d1[:7])
        tot = sum(_f(sp.get(m)) for m in months)
        if tot:
            ga = [k for k in rows if k[0] == "google_ads"]
            tot_s = sum(rows[k]["sessions"] for k in ga) or 0
            for k in ga:
                rows[k]["cost"] += tot * (rows[k]["sessions"] / tot_s if tot_s else 1 / len(ga))
    return rows, terms, cfg


def _verdict(r, min_spend):
    if r["cost"] <= 0:
        return "-"
    if r["done"] == 0 and r["cost"] >= min_spend:
        return "İş yok"
    if r["done"] == 0:
        return "Veri az"
    return "Kârlı" if r["net_est"] - r["cost"] > 0 else "Zararda"


def _fin(r, min_spend=300):
    r = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}
    r["contacts"] = r["leads"] + r["calls"]
    r["cpl"] = round(r["cost"] / r["contacts"], 2) if r["cost"] and r["contacts"] else None
    r["cpa"] = round(r["cost"] / r["done"], 2) if r["cost"] and r["done"] else None
    r["roas"] = round(r["revenue"] / r["cost"], 2) if r["cost"] else None
    r["profit"] = round(r["net_est"] - r["cost"], 2)
    r["verdict"] = _verdict(r, min_spend)
    return r


# ============================================================ API
def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    import asyncio
    lim = {}

    def rate_ok(key, n, window):
        now = datetime.now().timestamp()
        arr = [t for t in lim.get(key, []) if now - t < window]
        if len(arr) >= n:
            lim[key] = arr
            return False
        arr.append(now)
        lim[key] = arr
        return True

    def masked(cfg):
        c = {**cfg, "google": dict(cfg["google"])}
        for k in SECRET_KEYS:
            if c["google"].get(k):
                c["google"][k] = MASK
        return c

    # ---------------------------------------------------------- ayarlar
    @api_router.get("/mkt/settings")
    async def get_settings(_: dict = Depends(require_admin)):
        return masked(await get_cfg(db))

    @api_router.put("/mkt/settings")
    async def put_settings(payload: dict, _: dict = Depends(require_admin)):
        cur = await get_cfg(db)
        upd = {}
        if "site_url" in payload:
            u = str(payload["site_url"]).strip().rstrip("/")
            if not re.match(r"^https?://", u):
                raise HTTPException(422, "Site adresi http(s):// ile başlamalı")
            upd["site_url"] = u
        for k in ("cpa_limit", "no_job_min_spend"):
            if k in payload:
                upd[k] = max(0.0, _f(payload[k]))
        if "no_job_days" in payload:
            upd["no_job_days"] = max(3, min(90, int(payload["no_job_days"] or 14)))
        for k in ("alerts",):
            if k in payload:
                upd[k] = bool(payload[k])
        if "disclaimer" in payload:
            upd["disclaimer"] = str(payload["disclaimer"])[:400]
        if "districts" in payload:
            upd["districts"] = [str(x).strip()[:60] for x in (payload["districts"] or []) if str(x).strip()][:300]
        if "campaign_alias" in payload and isinstance(payload["campaign_alias"], dict):
            upd["campaign_alias"] = {str(k)[:120]: str(v)[:120] for k, v in payload["campaign_alias"].items()}
        if "call_numbers" in payload:
            pool = []
            for n in payload["call_numbers"] or []:
                if last10(n.get("number")):
                    pool.append({"number": re.sub(r"\D", "", n["number"]), "display": str(n.get("display") or n["number"])[:30],
                                 "channel": str(n.get("channel") or "")[:30], "campaign": str(n.get("campaign") or "")[:120]})
            upd["call_numbers"] = pool[:40]
        if isinstance(payload.get("business"), dict):
            b = {**cur["business"]}
            for k, v in payload["business"].items():
                if k in DEFAULT["business"]:
                    b[k] = [str(x).strip()[:200] for x in v if str(x).strip()][:30] if isinstance(DEFAULT["business"][k], list) else str(v)[:300]
            upd["business"] = b
        if isinstance(payload.get("google"), dict):
            g = {**cur["google"]}
            for k, v in payload["google"].items():
                if k not in DEFAULT["google"]:
                    continue
                if k in ("auto_sync", "auto_upload"):
                    g[k] = bool(v)
                elif k in SECRET_KEYS:
                    if v != MASK:
                        g[k] = str(v).strip()[:600]
                else:
                    g[k] = str(v).strip()[:300]
            upd["google"] = g
        if upd:
            await db.app_settings.update_one({"_id": "mkt"}, {"$set": upd}, upsert=True)
        return masked(await get_cfg(db))

    @api_router.get("/mkt/status")
    async def status(_: dict = Depends(require_admin)):
        cfg = await get_cfg(db)
        g = cfg["google"]
        d = await db.app_settings.find_one({"_id": "mkt"}, {"_id": 0}) or {}
        au = await db.mkt_audits.find({}, {"_id": 0, "id": 1, "score": 1, "at": 1, "status": 1}).sort("at", -1).to_list(1)
        creds = bool(g["client_id"] and g["client_secret"])
        return {"ads_ready": bool(creds and g["ads_refresh_token"] and g["developer_token"] and g["customer_id"]),
                "gsc_ready": bool(creds and g["gsc_refresh_token"] and (g["gsc_site"] or cfg["site_url"])),
                "conversion_ready": bool(g["conversion_action"]), "last_spend_sync": d.get("last_spend_sync", ""), "last_gsc_sync": d.get("last_gsc_sync", ""),
                "call_numbers": len(cfg["call_numbers"]), "spend_rows": await db.ad_spend.count_documents({}),
                "audit": au[0] if au else None, "call_webhook_path": "/api/public/call-event?token=" + cfg["call_secret"]}

    # ---------------------------------------------------------- harcama
    @api_router.get("/mkt/spend")
    async def spend_list(date_from: str = "", date_to: str = "", _: dict = Depends(require_admin)):
        d0, d1 = _rng(date_from, date_to)
        rows = await db.ad_spend.find({"day": {"$gte": d0, "$lte": d1}}, {"_id": 0}).sort("day", -1).to_list(5000)
        by = defaultdict(lambda: {"cost": 0.0, "clicks": 0, "impressions": 0})
        for r in rows:
            b = by[(r.get("channel"), r.get("campaign"))]
            b["cost"] += _f(r.get("cost"))
            b["clicks"] += int(_f(r.get("clicks")))
            b["impressions"] += int(_f(r.get("impressions")))
        return {"date_from": d0, "date_to": d1, "rows": rows[:600], "total": round(sum(_f(r.get("cost")) for r in rows), 2),
                "by_campaign": sorted([{"channel": k[0], "campaign": k[1], **{a: round(v, 2) if isinstance(v, float) else v for a, v in b.items()}}
                                       for k, b in by.items()], key=lambda x: -x["cost"])}

    @api_router.post("/mkt/spend")
    async def spend_add(payload: dict, _: dict = Depends(require_admin)):
        day = parse_day(payload.get("day"))
        if not day:
            raise HTTPException(422, "Geçerli bir gün girin (YYYY-AA-GG)")
        ch = str(payload.get("channel") or "google_ads")[:30]
        doc = {"id": spend_key(day, ch, payload.get("campaign")), "day": day, "channel": ch, "campaign": str(payload.get("campaign") or "")[:120],
               "campaign_id": str(payload.get("campaign_id") or ""), "cost": round(max(0.0, _f(payload.get("cost"))), 2),
               "clicks": int(_f(payload.get("clicks"))), "impressions": int(_f(payload.get("impressions"))), "source": "manual", "updated_at": _now()}
        await db.ad_spend.update_one({"id": doc["id"]}, {"$set": doc}, upsert=True)
        return doc

    @api_router.delete("/mkt/spend/{sid}")
    async def spend_del(sid: str, _: dict = Depends(require_admin)):
        await db.ad_spend.delete_one({"id": sid})
        return {"ok": True}

    @api_router.post("/mkt/spend/import")
    async def spend_import(payload: dict, _: dict = Depends(require_admin)):
        rows = parse_spend_csv(payload.get("csv") or "")
        ch = str(payload.get("channel") or "google_ads")[:30]
        for r in rows:
            doc = {"id": spend_key(r["day"], ch, r["campaign"]), "channel": ch, "source": "csv", "updated_at": _now(), **r}
            await db.ad_spend.update_one({"id": doc["id"]}, {"$set": doc}, upsert=True)
        return {"ok": True, "imported": len(rows), "total": round(sum(r["cost"] for r in rows), 2),
                "range": [min(r["day"] for r in rows), max(r["day"] for r in rows)] if rows else []}

    @api_router.post("/mkt/ads/sync")
    async def ads_sync(payload: dict, _: dict = Depends(require_admin)):
        g = (await get_cfg(db))["google"]
        eksik = [n for k, n in (("client_id", "istemci kimliği"), ("client_secret", "gizli anahtar"), ("ads_refresh_token", "yenileme anahtarı"),
                                ("developer_token", "geliştirici anahtarı"), ("customer_id", "müşteri kimliği")) if not g.get(k)]
        if eksik:
            raise HTTPException(400, "Google Ads otomatik çekme için henüz bağlı değil (eksik: " + ", ".join(eksik) + "). "
                                "Şimdilik hızlı yol: Google Ads → Raporlar → Kampanya raporunu CSV indirip bu sayfadaki CSV yükleme alanından içe aktarın.")
        try:
            n = await sync_spend(db, int((payload or {}).get("days") or 30))
        except Exception as e:                          # noqa: BLE001
            raise HTTPException(502, "Google Ads: " + str(e)[:300])
        return {"ok": True, "rows": n}

    @api_router.post("/mkt/ads/upload-conversions")
    async def ads_upload(_: dict = Depends(require_admin)):
        try:
            return await upload_conversions(db)
        except Exception as e:                          # noqa: BLE001
            raise HTTPException(502, "Google Ads: " + str(e)[:300])

    @api_router.get("/mkt/ads/uploads")
    async def ads_uploads(_: dict = Depends(require_admin)):
        return await db.ads_uploads.find({}, {"_id": 0}).sort("at", -1).to_list(100)

    # ---------------------------------------------------------- raporlar
    @api_router.get("/mkt/campaigns")
    async def campaigns(date_from: str = "", date_to: str = "", _: dict = Depends(require_admin)):
        d0, d1 = _rng(date_from, date_to)
        rows, terms, cfg = await core(db, d0, d1)
        ms = _f(cfg.get("no_job_min_spend"), 300)
        out = [{"channel": k[0], "campaign": k[1], **_fin(v, ms)} for k, v in rows.items()]
        out.sort(key=lambda x: (-x["cost"], -x["revenue"], -x["sessions"]))
        tt = []
        for (ch, term), v in terms.items():
            tt.append({"channel": ch, "term": term, **{a: round(b, 2) if isinstance(b, float) else b for a, b in v.items()}})
        tt.sort(key=lambda x: (-x["done"], -x["jobs"], -x["sessions"]))
        tot = _blank()
        for v in rows.values():
            for k in tot:
                tot[k] += v[k]
        return {"date_from": d0, "date_to": d1, "rows": out, "terms": tt[:80], "totals": _fin(tot, ms),
                "note": "Kâr = tahmini şirket payı (iş tutarı × firma yüzdesi) − reklam harcaması; parça maliyeti kayıtlı olmadığı için dahil değildir."}

    @api_router.get("/mkt/channels")
    async def channels(date_from: str = "", date_to: str = "", _: dict = Depends(require_admin)):
        d0, d1 = _rng(date_from, date_to, 90)
        rows, _t, cfg = await core(db, d0, d1)
        ms = _f(cfg.get("no_job_min_spend"), 300)
        ch = defaultdict(_blank)
        for (c, _camp), v in rows.items():
            for k in v:
                ch[c][k] += v[k]
        # yaşam değeri: aralıkta ilk işi açılan müşteriler (kohort), tüm zamanların işlemleri
        custs = {c["id"]: c for c in await db.customers.find({}, {"_id": 0, "id": 1, "source_channel": 1}).to_list(300000)}
        alljobs = await db.service_jobs.find({}, {"_id": 0, "customer_id": 1, "status": 1, "total_amount": 1, "technician_commission_percent": 1, "parts_cost": 1,
                                                  "created_at": 1, "source_channel": 1}).to_list(400000)
        byc = defaultdict(list)
        for j in alljobs:
            if j.get("customer_id"):
                byc[j["customer_id"]].append(j)
        coh = defaultdict(lambda: {"customers": 0, "repeat": 0, "rev": 0.0, "net": 0.0})
        for cid, js in byc.items():
            js.sort(key=lambda x: x.get("created_at") or "")
            first = js[0]
            if not (d0 <= _tr_day(first.get("created_at")) <= d1):
                continue
            c = (custs.get(cid) or {}).get("source_channel") or first.get("source_channel") or "belirtilmemis"
            dn = [j for j in js if j.get("status") in DONE]
            k = coh[c]
            k["customers"] += 1
            k["repeat"] += 1 if len(dn) >= 2 else 0
            k["rev"] += sum(_f(j.get("total_amount")) for j in dn)
            k["net"] += sum(_net(j) for j in dn)
        out = []
        for c in set(ch) | set(coh):
            v = _fin(ch[c], ms)
            k = coh[c]
            n = k["customers"]
            v.update({"channel": c, "new_customers": n, "repeat_pct": round(k["repeat"] / n * 100, 1) if n else 0,
                      "ltv": round(k["rev"] / n, 2) if n else 0, "ltv_net": round(k["net"] / n, 2) if n else 0,
                      "cac": round(v["cost"] / n, 2) if v["cost"] and n else None})
            v["ltv_cac"] = round(v["ltv_net"] / v["cac"], 2) if v["cac"] else None
            out.append(v)
        out.sort(key=lambda x: (-x["revenue"], -x["sessions"]))
        tot_done = sum(r["done"] for r in out) or 0
        org = sum(r["done"] for r in out if r["channel"] == "organik")
        ads = sum(r["done"] for r in out if r["channel"] in ADS_CH)
        tips = []
        for r in out:
            if r["channel"] in ADS_CH and r["cost"] > 0:
                if r["verdict"] == "Zararda":
                    tips.append(f"{r['channel']}: harcama {r['cost']:.0f} ₺, tahmini şirket payı {r['net_est']:.0f} ₺ — bu dönemde zararda; kampanya sekmesinden zayıf kampanyaları kısın.")
                elif r["verdict"] == "İş yok":
                    tips.append(f"{r['channel']}: {r['cost']:.0f} ₺ harcandı ama tamamlanan iş yok — iş/arama atıfının doğru çalıştığını ve kampanya hedeflemesini kontrol edin.")
                elif r["ltv_cac"] and r["ltv_cac"] >= 3:
                    tips.append(f"{r['channel']}: yaşam değeri/maliyet {r['ltv_cac']}× — ölçeklenebilir görünüyor.")
        if tot_done:
            tips.append(f"Tamamlanan işlerin %{round(org / tot_done * 100)}'i organik, %{round(ads / tot_done * 100)}'i reklam kaynaklı. Reklamı kısmadan önce 'Kampanyalar' sekmesinde reklamın net katkısını (kâr sütunu) kontrol edin.")
        unk = next((r for r in out if r["channel"] == "belirtilmemis"), None)
        if unk and tot_done and unk["done"] / tot_done > 0.3:
            tips.append("İşlerin %30'undan fazlasında kanal belirtilmemiş: iş açarken 'kaynak kanal' alanını doldurun veya aramaları 'Aramalar' sekmesinden kaydedin.")
        return {"date_from": d0, "date_to": d1, "rows": out, "tips": tips,
                "note": "Yaşam değeri: aralıkta ilk işi açılan müşterilerin bugüne kadarki tamamlanmış iş toplamı (ortalama)."}

    # ---------------------------------------------------------- aramalar
    @api_router.get("/mkt/calls")
    async def calls_list(days: int = 30, _: dict = Depends(require_admin)):
        d1 = _today()
        d0 = (d1 - timedelta(days=max(1, min(days, 365)) - 1)).isoformat()
        rows = await db.call_log.find({"day": {"$gte": d0}}, {"_id": 0}).sort("at", -1).to_list(2000)
        clicks = await db.track_events.find({"label": "call_click", "day": {"$gte": d0}}, {"_id": 0}).to_list(100000)
        sess = {}
        sids = list({c["sid"] for c in clicks if c.get("sid")})
        if sids:
            sess = {s["id"]: s for s in await db.visitor_sessions.find({"id": {"$in": sids}}, {"_id": 0, "id": 1, "campaign": 1, "term": 1, "channel": 1}).to_list(100000)}
        by = defaultdict(int)
        for c in clicks:
            s = sess.get(c.get("sid")) or {}
            by[(c.get("channel") or s.get("channel") or "", s.get("campaign") or "")] += 1
        return {"calls": rows, "answered": sum(1 for r in rows if r.get("status") == "cevaplandi"),
                "click_summary": sorted([{"channel": k[0], "campaign": k[1], "clicks": v} for k, v in by.items()], key=lambda x: -x["clicks"]),
                "click_total": len(clicks), "numbers": (await get_cfg(db))["call_numbers"]}

    async def link_call(c):
        """Arayan numaranın müşterisi varsa ve aramadan sonra 3 gün içinde iş açıldıysa otomatik bağlar."""
        l10 = c.get("from_last10")
        if not l10 or c.get("job_id"):
            return False
        cu = await db.customers.find_one({"phone": {"$regex": l10 + "$"}}, {"_id": 0, "id": 1})
        if not cu:
            return False
        try:
            end = (datetime.fromisoformat(c["at"].replace("Z", "+00:00")) + timedelta(days=3)).isoformat()
        except ValueError:
            return False
        job = await db.service_jobs.find_one({"customer_id": cu["id"], "created_at": {"$gte": c["at"][:10], "$lte": end}}, {"_id": 0, "id": 1, "job_number": 1})
        if not job:
            return False
        await db.call_log.update_one({"id": c["id"]}, {"$set": {"job_id": job["id"], "job_number": job.get("job_number", ""), "outcome": "is_oldu", "auto_linked": True}})
        return True

    async def new_call(src, d):
        pool = (await get_cfg(db))["call_numbers"]
        to = last10(d.get("to"))
        hit = next((n for n in pool if to and last10(n["number"]) == to), None)
        at = d.get("at") or _now()
        fr = last10(d.get("from"))
        doc = {"id": str(uuid.uuid4()), "source": src, "at": at, "day": _tr_day(at), "to": to,
               "from_masked": ("*******" + fr[-3:]) if fr else "", "from_last10": fr,
               "channel": (hit or {}).get("channel") or d.get("channel") or "", "campaign": (hit or {}).get("campaign") or d.get("campaign") or "",
               "duration": int(_f(d.get("duration"))), "status": d.get("status") or "cevaplandi", "outcome": d.get("outcome") or "bekliyor",
               "job_id": d.get("job_id") or "", "job_number": "", "note": str(d.get("note") or "")[:300]}
        await db.call_log.insert_one(dict(doc))
        await link_call(doc)
        return await db.call_log.find_one({"id": doc["id"]}, {"_id": 0})

    @api_router.post("/mkt/calls")
    async def calls_add(payload: dict, _: dict = Depends(require_admin)):
        return await new_call("manual", {"from": payload.get("phone"), "channel": payload.get("channel"), "campaign": payload.get("campaign"),
                                         "status": payload.get("status") or "cevaplandi", "outcome": payload.get("outcome"), "note": payload.get("note"),
                                         "at": payload.get("at")})

    @api_router.patch("/mkt/calls/{cid}")
    async def calls_patch(cid: str, payload: dict, _: dict = Depends(require_admin)):
        upd = {}
        if payload.get("outcome") in ("bekliyor", "is_oldu", "bos", "cevapsiz"):
            upd["outcome"] = payload["outcome"]
        if "note" in payload:
            upd["note"] = str(payload["note"])[:300]
        if "channel" in payload:
            upd["channel"] = str(payload["channel"])[:30]
        if "campaign" in payload:
            upd["campaign"] = str(payload["campaign"])[:120]
        if payload.get("job_number"):
            j = await db.service_jobs.find_one({"job_number": payload["job_number"]}, {"_id": 0, "id": 1, "job_number": 1})
            if not j:
                raise HTTPException(404, "İş numarası bulunamadı")
            upd.update({"job_id": j["id"], "job_number": j["job_number"], "outcome": "is_oldu"})
        if upd:
            await db.call_log.update_one({"id": cid}, {"$set": upd})
        return await db.call_log.find_one({"id": cid}, {"_id": 0})

    @api_router.delete("/mkt/calls/{cid}")
    async def calls_del(cid: str, _: dict = Depends(require_admin)):
        await db.call_log.delete_one({"id": cid})
        return {"ok": True}

    @api_router.post("/public/call-event")
    async def call_event(request: Request, token: str = ""):
        cfg = await get_cfg(db)
        if not token or not hmac.compare_digest(token, cfg["call_secret"]):
            raise HTTPException(403, "Geçersiz anahtar")
        if not rate_ok("callev", 120, 60):
            raise HTTPException(429, "Çok fazla istek")
        try:
            d = await request.json()
        except Exception:                               # noqa: BLE001
            d = dict(await request.form())
        g = lambda *ks: next((d[k] for k in ks if d.get(k)), "")
        st = str(g("status", "call_status", "CallStatus")).lower()
        status = "cevaplandi" if st in ("", "answered", "completed", "cevaplandi", "connected") else "cevapsiz"
        c = await new_call("webhook", {"to": g("to", "called", "called_number", "dialed", "Called"), "from": g("from", "caller", "caller_number", "From"),
                                       "duration": g("duration", "call_duration", "CallDuration") or 0, "status": status,
                                       "at": g("at", "time", "timestamp") or None})
        return {"ok": True, "id": c["id"]}

    @api_router.get("/public/mkt/number")
    async def public_number(request: Request, sid: str = ""):
        if not rate_ok("num:" + (request.client.host if request.client else ""), 60, 60):
            return {}
        cfg = await get_cfg(db)
        pool = cfg["call_numbers"]
        if not pool or not sid:
            return {}
        s = await db.visitor_sessions.find_one({"id": sid}, {"_id": 0, "channel": 1, "campaign": 1})
        if not s:
            return {}
        camp = lower_tr(s.get("campaign"))
        hit = next((n for n in pool if n.get("campaign") and lower_tr(n["campaign"]) == camp and camp), None) \
            or next((n for n in pool if n.get("channel") == s.get("channel") and not n.get("campaign")), None)
        return {"number": hit["number"], "display": hit["display"]} if hit else {}

    # ---------------------------------------------------------- zamanlayıcı
    async def hook(_db):
        try:
            cfg = await get_cfg(db)
            g = cfg["google"]
            now = datetime.now(TR)
            d = await db.app_settings.find_one({"_id": "mkt"}, {"_id": 0}) or {}
            for c in await db.call_log.find({"outcome": "bekliyor", "day": {"$gte": (now.date() - timedelta(days=5)).isoformat()}}, {"_id": 0}).to_list(500):
                await link_call(c)
            ready = g["client_id"] and g["client_secret"]
            if g["auto_sync"] and ready and now.hour >= 6 and d.get("last_sync_day") != now.date().isoformat():
                await db.app_settings.update_one({"_id": "mkt"}, {"$set": {"last_sync_day": now.date().isoformat()}}, upsert=True)
                try:
                    if g["ads_refresh_token"]:
                        await sync_spend(db, 14)
                except Exception as e:                  # noqa: BLE001
                    log.warning("ads sync: %s", e)
                try:
                    import mkt_site
                    if g["gsc_refresh_token"]:
                        await mkt_site.gsc_sync(db, 28)
                except Exception as e:                  # noqa: BLE001
                    log.warning("gsc sync: %s", e)
            if g["auto_upload"] and ready and g["conversion_action"] and g["ads_refresh_token"]:
                try:
                    await upload_conversions(db)
                except Exception as e:                  # noqa: BLE001
                    log.warning("conv upload: %s", e)
            if cfg["alerts"]:
                await alerts(cfg)
        except Exception:                               # noqa: BLE001
            log.exception("mkt_hook")

    async def alerts(cfg):
        now = datetime.now(TR)
        if now.hour < ALERT_FROM_HOUR:
            return
        wk = now.strftime("%G-W%V")
        d1 = now.date().isoformat()
        out = []
        d7 = (now.date() - timedelta(days=6)).isoformat()
        rows, _t, _c = await core(db, d7, d1)
        cpa_lim = _f(cfg.get("cpa_limit"))
        for (ch, camp), v in rows.items():
            if v["cost"] <= 0:
                continue
            if cpa_lim and v["done"] and v["cost"] / v["done"] > cpa_lim:
                out.append((f"{camp}:cpa:{wk}", f"Reklam uyarısı: '{camp}' son 7 günde iş başına {v['cost'] / v['done']:.0f} ₺ (limit {cpa_lim:.0f} ₺)."))
            elif cpa_lim and not v["done"] and v["cost"] >= cpa_lim:
                out.append((f"{camp}:cpa0:{wk}", f"Reklam uyarısı: '{camp}' son 7 günde {v['cost']:.0f} ₺ harcadı, tamamlanan iş yok."))
        n = int(cfg.get("no_job_days") or 14)
        rows2, _t2, _c2 = await core(db, (now.date() - timedelta(days=n - 1)).isoformat(), d1)
        for (ch, camp), v in rows2.items():
            if v["cost"] >= _f(cfg.get("no_job_min_spend"), 300) and v["jobs"] == 0 and v["leads"] == 0 and v["calls"] == 0:
                out.append((f"{camp}:nojob:{wk}", f"Reklam uyarısı: '{camp}' son {n} günde {v['cost']:.0f} ₺ harcadı; form/arama/iş yok. Kampanyayı gözden geçirin."))
        for key, text in out[:6]:
            if await db.mkt_alert_log.find_one({"key": key}):
                continue
            await db.mkt_alert_log.insert_one({"key": key, "at": _now()})
            await notify.notify_owner(db, text, kind="mkt_alert")

    governance.HOOKS.append(hook)
    api_router.mkt_hook = hook
    api_router.mkt_alerts = alerts


async def ensure_indexes(db):
    await db.ad_spend.create_index("id", unique=True)
    await db.ad_spend.create_index("day")
    await db.call_log.create_index("day")
    await db.mkt_alert_log.create_index("key")
