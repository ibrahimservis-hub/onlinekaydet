# -*- coding: utf-8 -*-
"""Uzun vadeli veri katmanı: Müşteri 360 (kaynak → arama → talep → iş → ciro), site içi arama kayıtları,
kaynak/anahtar kelime kârlılığı, usta puanlama (0-100 + seviye + geçmiş) ve muhasebe trend/yaşlandırma/alacak.
Mevcut verileri OKUR; yalnızca yeni koleksiyonlar (search_logs, crm_notes, tech_notes) ve işlerde isteğe bağlı
`collected_amount`/`payment_status` alanları eklenir."""
import asyncio
import re
import statistics
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:
    TR = timezone(timedelta(hours=3))

DONE = ("tamamlandi", "faturalandi")
BOT = re.compile(r"bot|crawl|spider|slurp|facebookexternalhit|headless|lighthouse|pingdom|uptime", re.I)
_rate = defaultdict(list)


def _id():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc).isoformat()


def ph10(p):
    return re.sub(r"\D", "", p or "")[-10:]


def prx(phone):
    """Boşluk/tire/parantezli kayıtlı numaralarla eşleşen regex (son 10 hane)."""
    return r"\D*".join(phone) + "$"


def _f(v, d=0.0):
    try:
        return float(v)
    except Exception:
        return d


def _dt(s):
    try:
        d = datetime.fromisoformat((s or "").replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _month(s):
    d = _dt(s)
    return d.astimezone(TR).strftime("%Y-%m") if d else ""


def _since(days):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


# ------------------------------------------------------------------ puan hesabı (saf fonksiyon)
LEVELS = [(90, "Platin"), (80, "Altın"), (70, "Gümüş"), (55, "Bronz"), (0, "Gelişim")]
WEIGHTS = {"rating": 30, "completion": 15, "rework": 15, "speed": 10, "punctual": 10, "docs": 10, "polite": 5, "cash": 5}
LABELS = {"rating": "Müşteri puanı", "completion": "Tamamlama oranı", "rework": "Tekrar arıza yok", "speed": "Hız",
          "punctual": "Dakiklik", "docs": "Fotoğraf & imza", "polite": "Nezaket", "cash": "Kasa disiplini"}
TIPS = {"rating": "Müşteriye işlem sonunda ne yapıldığını anlatın, temiz bırakın, değerlendirme linkini hatırlatın.",
        "completion": "Üstlenilen işleri iptal ettirmeyin; gelemeyeceğinizi önceden bildirin.",
        "rework": "Aynı arızaya 30 gün içinde tekrar gidiliyorsa kök nedeni bulun; parça/test notunu işe yazın.",
        "speed": "Randevuya hızlı gidin ve işi aynı gün kapatın; parça bekleyen işleri not edin.",
        "punctual": "Yola çıkınca 'Yoldayım' durumunu girin, geç kalacaksanız müşteriyi arayın.",
        "docs": "İşlem öncesi/sonrası fotoğraf ve müşteri imzasını mutlaka ekleyin.",
        "polite": "Müşteriyle nazik ve saygılı iletişim kurun.",
        "cash": "Şirkete borç ödemelerini zamanında yapın."}


def level_of(score, n_done, min_jobs=5):
    if n_done < min_jobs:
        return "Yeni"
    for lim, name in LEVELS:
        if score >= lim:
            return name
    return "Gelişim"


def _truthy_survey(v):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return 100.0 if v else 0.0
    try:
        n = float(v)
        return 100.0 if n >= 4 else (0.0 if n <= 2 else 50.0) if n <= 5 else 100.0
    except Exception:
        return 100.0 if str(v).lower() in ("evet", "yes", "true", "1") else (0.0 if str(v).lower() in ("hayir", "hayır", "no", "false", "0") else None)


def score_techs(techs, jobs_period, all_jobs, tech_debt_old):
    """techs: kullanıcı listesi; jobs_period: dönem işleri; all_jobs: tekrar-arıza için geniş liste;
    tech_debt_old: {tech_id: 90+ gün... eski borç tutarı}"""
    by = defaultdict(list)
    for j in jobs_period:
        by[j.get("assigned_technician_id", "")].append(j)
    # tekrar arıza: aynı telefon + cihaz türü, 30 gün içinde yeni iş
    seq = defaultdict(list)
    for j in all_jobs:
        k = (ph10(j.get("customer_phone")), (j.get("device_type") or "").lower())
        if k[0]:
            seq[k].append(j)
    redo_ids = set()
    for k, lst in seq.items():
        lst.sort(key=lambda x: x.get("created_at", ""))
        for a, b in zip(lst, lst[1:]):
            da, db_ = _dt(a.get("completed_at") or a.get("created_at")), _dt(b.get("created_at"))
            if a.get("status") in DONE and da and db_ and 0 <= (db_ - da).days <= 30:
                redo_ids.add(a["id"])
    hours = {}
    for j in jobs_period:
        if j.get("status") in DONE:
            a, b = _dt(j.get("created_at")), _dt(j.get("completed_at"))
            if a and b and 0 < (b - a).total_seconds() < 240 * 3600:
                hours[j["id"]] = (b - a).total_seconds() / 3600
    med = statistics.median(hours.values()) if hours else 0
    out = []
    for t in techs:
        js = by.get(t["id"], [])
        done = [j for j in js if j.get("status") in DONE]
        canc = [j for j in js if j.get("status") == "iptal"]
        comp = {}
        rated = [j["customer_rating"] for j in done if j.get("customer_rating")]
        if rated:
            comp["rating"] = (sum(rated) / len(rated) - 1) / 4 * 100
        if done or canc:
            comp["completion"] = len(done) * 100 / (len(done) + len(canc))
        if done:
            comp["rework"] = max(0.0, 100 - 250 * sum(1 for j in done if j["id"] in redo_ids) / len(done))
            hs = [hours[j["id"]] for j in done if j["id"] in hours]
            if hs and med:
                avg = sum(hs) / len(hs)
                comp["speed"] = max(0.0, min(100.0, 100 * med / avg)) if avg > med else 100.0
            ok = sum(1 for j in done if (j.get("photos_after") or []) and (j.get("signature_url") or j.get("tech_signature_url")))
            comp["docs"] = ok * 100 / len(done)
        pun = [x for x in (_truthy_survey((j.get("survey") or {}).get("punctual")) for j in done) if x is not None]
        pol = [x for x in (_truthy_survey((j.get("survey") or {}).get("polite")) for j in done) if x is not None]
        if pun:
            comp["punctual"] = sum(pun) / len(pun)
        if pol:
            comp["polite"] = sum(pol) / len(pol)
        if done or tech_debt_old.get(t["id"]):
            comp["cash"] = 100.0 if not tech_debt_old.get(t["id"]) else 40.0
        wsum = sum(WEIGHTS[k] for k in comp)
        score = round(sum(comp[k] * WEIGHTS[k] for k in comp) / wsum, 1) if wsum else 0.0
        weak = sorted(comp, key=lambda k: comp[k])[:2] if comp else []
        revenue = sum(_f(j.get("total_amount")) for j in done)
        out.append({"id": t["id"], "name": t.get("name", ""), "is_active": t.get("is_active", True), "score": score, "level": level_of(score, len(done)),
                    "done": len(done), "cancelled": len(canc), "assigned": len(js), "revenue": round(revenue, 2), "avg_ticket": round(revenue / len(done), 2) if done else 0,
                    "rating_avg": round(sum(rated) / len(rated), 2) if rated else 0, "rating_n": len(rated), "redo": sum(1 for j in done if j["id"] in redo_ids),
                    "avg_hours": round(sum(hours[j["id"]] for j in done if j["id"] in hours) / max(1, sum(1 for j in done if j["id"] in hours)), 1) if done else 0,
                    "components": [{"key": k, "label": LABELS[k], "value": round(comp[k], 1), "weight": WEIGHTS[k]} for k in WEIGHTS if k in comp],
                    "weak": [{"key": k, "label": LABELS[k], "tip": TIPS[k]} for k in weak if comp.get(k, 100) < 85]})
    out.sort(key=lambda r: (-(r["level"] != "Yeni"), -r["score"], -r["done"]))
    for i, r in enumerate(out, 1):
        r["rank"] = i
    return out


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]

    # ============================================================ CANLI ZİYARETÇİLER (ayrıntılı)
    def _vrow(x, now, window):
        from crm_extras import CHANNEL_LABELS

        def ago(iso):
            try:
                return max(0, int((now - datetime.fromisoformat(iso)).total_seconds()))
            except Exception:
                return 99999
        pages = x.get("pages") or []
        evs = x.get("events") or []
        sr = x.get("searches") or []
        idle = ago(x.get("last_seen", ""))
        return {
            "id": x.get("id"), "online": idle <= window, "idle_sec": idle,
            "first_seen": x.get("first_seen"), "last_seen": x.get("last_seen"), "duration_sec": x.get("duration_sec", 0),
            "channel": x.get("channel"), "channel_label": CHANNEL_LABELS.get(x.get("channel"), x.get("channel") or "—"),
            "source_name": x.get("source_name", ""), "campaign": x.get("campaign", ""), "term": x.get("term", ""),
            "device": x.get("device", ""), "browser": x.get("browser", ""), "os": x.get("os", ""), "screen": x.get("screen", ""),
            "city": x.get("city", ""), "ip": x.get("ip", ""), "referrer": x.get("referrer", ""),
            "landing_page": x.get("landing_page", ""), "current_page": (pages[-1].get("path") if pages else x.get("landing_page", "")),
            "current_title": (pages[-1].get("title") if pages else ""),
            "pages_count": x.get("pages_count", len(pages)),
            "path": [{"path": q.get("path"), "title": q.get("title", ""), "ts": q.get("ts")} for q in pages[-25:]],
            "searches": [{"q": q.get("q"), "results": q.get("results"), "ts": q.get("ts")} for q in sr[-6:]],
            "events": [{"type": q.get("type"), "ts": q.get("ts"), "path": q.get("path", "")} for q in evs[-12:]],
            "conv_call": x.get("conv_call", 0), "conv_whatsapp": x.get("conv_whatsapp", 0), "conv_form": x.get("conv_form", 0),
            "converted": bool(x.get("converted")),
        }

    @api_router.get("/visitors/history")
    async def visitors_history(frm: str = "", to: str = "", channel: str = "", device: str = "", action: str = "", q: str = "",
                               city: str = "", skip: int = 0, limit: int = 40, _: dict = Depends(require_admin)):
        """Geçmiş ziyaretçi oturumları: tarih aralığı (Türkiye günü) + kaynak/cihaz/eylem/sayfa/şehir filtresi."""
        now = datetime.now(timezone.utc)
        tz3 = timezone(timedelta(hours=3))

        def day_start(d, default):
            try:
                return datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=tz3)
            except Exception:
                return default
        today0 = datetime.now(tz3).replace(hour=0, minute=0, second=0, microsecond=0)
        t0 = day_start(frm, today0)
        t1 = day_start(to, today0) + timedelta(days=1)
        if t1 - t0 > timedelta(days=186):
            t0 = t1 - timedelta(days=186)
        flt = {"first_seen": {"$gte": t0.astimezone(timezone.utc).isoformat(), "$lt": t1.astimezone(timezone.utc).isoformat()}}
        if channel:
            flt["channel"] = channel[:40]
        if device:
            flt["device"] = device[:40]
        if city.strip():
            flt["city"] = {"$regex": re.escape(city.strip()[:40]), "$options": "i"}
        act = {"call": {"conv_call": {"$gt": 0}}, "whatsapp": {"conv_whatsapp": {"$gt": 0}}, "form": {"conv_form": {"$gt": 0}},
               "search": {"searches.0": {"$exists": True}}}
        ands = []
        if action == "any":
            ands.append({"$or": [{"conv_call": {"$gt": 0}}, {"conv_whatsapp": {"$gt": 0}}, {"conv_form": {"$gt": 0}}]})
        elif action == "none":
            ands += [{"conv_call": {"$not": {"$gt": 0}}}, {"conv_whatsapp": {"$not": {"$gt": 0}}}, {"conv_form": {"$not": {"$gt": 0}}}]
        elif action in act:
            ands.append(act[action])
        qq = q.strip()[:80]
        if qq:
            rx = {"$regex": re.escape(qq), "$options": "i"}
            ands.append({"$or": [{"landing_page": rx}, {"pages.path": rx}, {"pages.title": rx}, {"term": rx}, {"campaign": rx}, {"source_name": rx},
                                 {"searches.q": rx}, {"referrer": rx}]})
        if ands:
            flt["$and"] = ands
        total = await db.visitor_sessions.count_documents(flt)
        rows = await db.visitor_sessions.find(flt, {"_id": 0}).sort("first_seen", -1).skip(max(0, skip)).limit(max(1, min(limit, 100))).to_list(100)
        contacted = await db.visitor_sessions.count_documents({"$and": [flt, {"$or": [{"conv_call": {"$gt": 0}}, {"conv_whatsapp": {"$gt": 0}}, {"conv_form": {"$gt": 0}}]}]})
        searched = await db.visitor_sessions.count_documents({"$and": [flt, {"searches.0": {"$exists": True}}]})
        agg = await db.visitor_sessions.aggregate([{"$match": flt}, {"$group": {"_id": None, "d": {"$avg": "$duration_sec"}, "p": {"$avg": "$pages_count"}}}]).to_list(1)
        ch = await db.visitor_sessions.aggregate([{"$match": flt}, {"$group": {"_id": "$channel", "n": {"$sum": 1}}}, {"$sort": {"n": -1}}, {"$limit": 12}]).to_list(12)
        from crm_extras import CHANNEL_LABELS
        return {"total": total, "contacted": contacted, "searched": searched,
                "avg_duration": int((agg[0].get("d") or 0)) if agg else 0, "avg_pages": round((agg[0].get("p") or 0), 1) if agg else 0,
                "by_channel": [{"k": CHANNEL_LABELS.get(c["_id"], c["_id"] or "—"), "v": c["_id"] or "", "n": c["n"]} for c in ch],
                "channels": [{"v": k, "k": v} for k, v in CHANNEL_LABELS.items()],
                "sessions": [_vrow(x, now, 120) for x in rows]}

    @api_router.get("/visitors/live")
    async def visitors_live(window: int = 120, _: dict = Depends(require_admin)):
        from crm_extras import CHANNEL_LABELS
        now = datetime.now(timezone.utc)
        window = max(30, min(window, 900))
        since = (now - timedelta(seconds=window)).isoformat()
        recent_since = (now - timedelta(minutes=30)).isoformat()
        rows = await db.visitor_sessions.find({"last_seen": {"$gte": recent_since}}, {"_id": 0}).sort("last_seen", -1).to_list(150)

        def ago(iso):
            try:
                return max(0, int((now - datetime.fromisoformat(iso)).total_seconds()))
            except Exception:
                return 99999

        out = [_vrow(x, now, window) for x in rows]
        online = [o for o in out if o["online"]]
        tr0 = datetime.now(timezone(timedelta(hours=3))).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).isoformat()
        today = await db.visitor_sessions.count_documents({"first_seen": {"$gte": tr0}})
        calls = await db.visitor_sessions.count_documents({"first_seen": {"$gte": tr0}, "conv_call": {"$gt": 0}})
        pv = await db.pageviews.count_documents({"ts": {"$gte": tr0}})
        by_ch, by_dev, by_page = defaultdict(int), defaultdict(int), defaultdict(int)
        for o in online:
            by_ch[o["channel_label"]] += 1
            by_dev[o["device"] or "—"] += 1
            by_page[o["current_page"] or "/"] += 1
        top = lambda d, n=8: sorted(({"k": k, "n": v} for k, v in d.items()), key=lambda r: -r["n"])[:n]
        return {"now": now.isoformat(), "window": window, "online": len(online),
                "online_searching": sum(1 for o in online if o["searches"]), "online_called": sum(1 for o in online if o["conv_call"] or o["conv_whatsapp"]),
                "today": {"sessions": today, "pageviews": pv, "call_sessions": calls},
                "by_channel": top(by_ch), "by_device": top(by_dev), "by_page": top(by_page), "sessions": out}

    # ============================================================ SİTE İÇİ ARAMA KAYDI (herkese açık)
    @api_router.post("/public/track-search")
    async def track_search(payload: dict, request: Request):
        ua = request.headers.get("user-agent", "")
        if not ua or BOT.search(ua):
            return {"ok": True}
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
        now = datetime.now(timezone.utc).timestamp()
        _rate[ip] = [t for t in _rate[ip] if now - t < 60]
        if len(_rate[ip]) >= 30:
            return {"ok": True}
        _rate[ip].append(now)
        q = re.sub(r"\s+", " ", str(payload.get("q") or "")).strip().lower()[:120]
        if len(q) < 2 or len(re.sub(r"\D", "", q)) >= 7 or "@" in q:       # telefon / e-posta saklanmaz
            return {"ok": True}
        sid = str(payload.get("sid") or "")[:80]
        sess = await db.visitor_sessions.find_one({"id": sid}, {"_id": 0, "channel": 1}) if sid else None
        tr = datetime.now(timezone.utc).astimezone(TR)
        await db.search_logs.insert_one({"id": _id(), "sid": sid, "q": q, "results": int(_f(payload.get("results"), -1)), "path": str(payload.get("path") or "")[:200],
                                         "ts": _now(), "ts_dt": datetime.now(timezone.utc), "day": tr.strftime("%Y-%m-%d"), "channel": (sess or {}).get("channel", "")})
        if sid:
            await db.visitor_sessions.update_one({"id": sid}, {"$push": {"searches": {"$each": [{"q": q, "ts": _now()}], "$slice": -20}}})
        return {"ok": True}

    # ============================================================ MÜŞTERİ 360
    async def _load(days=0):
        q = {"created_at": {"$gte": _since(days)}} if days else {}
        proj = {"_id": 0, "id": 1, "job_number": 1, "customer_name": 1, "customer_phone": 1, "customer_id": 1, "device_type": 1, "device_brand_name": 1,
                "fault_description": 1, "status": 1, "total_amount": 1, "assigned_technician_id": 1, "created_at": 1, "completed_at": 1, "customer_rating": 1,
                "collected_amount": 1, "payment_status": 1, "city": 1, "address": 1, "source": 1, "channel": 1}
        return await db.service_jobs.find(q, proj).sort("created_at", -1).to_list(30000)

    def _segment(c):
        if c["jobs"] == 0:
            return "Aday"
        last = _dt(c.get("last_job_at"))
        age = (datetime.now(timezone.utc) - last).days if last else 9999
        if c["revenue"] >= 5000 or c["done"] >= 3:
            return "VIP"
        if age > 365:
            return "Pasif"
        if c["done"] >= 2:
            return "Sadık"
        return "Yeni"

    @api_router.get("/customers360")
    async def customers360(q: str = "", segment: str = "", channel: str = "", limit: int = 300, _: dict = Depends(require_admin)):
        custs = await db.customers.find({}, {"_id": 0}).to_list(20000)
        jobs = await _load()
        msgs = await db.contact_messages.find({}, {"_id": 0, "phone": 1, "name": 1, "city": 1, "channel": 1, "source": 1, "page": 1, "created_at": 1, "sid": 1, "device_type": 1}).sort("created_at", 1).to_list(30000)
        rows = {}

        def row(key, name="", phone="", city="", cid=""):
            if key not in rows:
                rows[key] = {"key": key, "id": cid, "name": name, "phone": phone, "city": city, "jobs": 0, "done": 0, "revenue": 0.0, "collected": 0.0, "last_job_at": "",
                             "first_seen": "", "channel": "", "landing": "", "term": "", "msgs": 0, "rating_sum": 0, "rating_n": 0, "devices": set()}
            return rows[key]
        for c in custs:
            k = ph10(c.get("phone")) or ("c:" + c["id"])
            r = row(k, c.get("name", ""), c.get("phone", ""), c.get("city", "") or c.get("address", "")[:30], c["id"])
            r["first_seen"] = c.get("created_at", "")
        for j in jobs:
            k = ph10(j.get("customer_phone")) or ("c:" + j.get("customer_id", "")) if (j.get("customer_phone") or j.get("customer_id")) else ""
            if not k:
                continue
            r = row(k, j.get("customer_name", ""), j.get("customer_phone", ""), j.get("city", ""), j.get("customer_id", ""))
            r["jobs"] += 1
            r["devices"].add(j.get("device_type") or "")
            if j.get("status") in DONE:
                r["done"] += 1
                r["revenue"] += _f(j.get("total_amount"))
                r["collected"] += _f(j.get("collected_amount"), _f(j.get("total_amount"))) if j.get("payment_status") != "veresiye" else _f(j.get("collected_amount"))
            if j.get("created_at", "") > r["last_job_at"]:
                r["last_job_at"] = j["created_at"]
            if j.get("customer_rating"):
                r["rating_sum"] += j["customer_rating"]
                r["rating_n"] += 1
        for m in msgs:                           # ilk dokunuş kaynağı (en eski mesaj)
            k = ph10(m.get("phone"))
            if not k:
                continue
            r = row(k, m.get("name", ""), m.get("phone", ""), m.get("city", ""))
            r["msgs"] += 1
            if not r["channel"]:
                src = m.get("source") or {}
                r["channel"] = m.get("channel") or src.get("channel", "")
                r["landing"] = (src.get("landing_page") or m.get("page") or "")[:80]
                r["term"] = src.get("term", "")
            if not r["first_seen"] or m.get("created_at", "") < r["first_seen"]:
                r["first_seen"] = m.get("created_at", "")
        out = []
        ql = q.lower().strip()
        for r in rows.values():
            r["segment"] = _segment(r)
            r["avg_ticket"] = round(r["revenue"] / r["done"], 2) if r["done"] else 0
            r["rating"] = round(r["rating_sum"] / r["rating_n"], 2) if r["rating_n"] else 0
            r["open_balance"] = round(max(0.0, r["revenue"] - r["collected"]), 2)
            r["revenue"] = round(r["revenue"], 2)
            r["devices"] = sorted(x for x in r["devices"] if x)
            if ql and ql not in (r["name"] or "").lower() and ql not in re.sub(r"\D", "", r["phone"] or "") and ql not in (r["phone"] or "") and ql not in (r["city"] or "").lower():
                continue
            if segment and r["segment"] != segment:
                continue
            if channel and r["channel"] != channel:
                continue
            out.append(r)
        out.sort(key=lambda x: -x["revenue"])
        seg = defaultdict(int)
        for r in out:
            seg[r["segment"]] += 1
        return {"total": len(out), "segments": dict(seg), "rows": out[:max(1, min(limit, 1000))]}

    @api_router.get("/customers360/{key}")
    async def customer360(key: str, _: dict = Depends(require_admin)):
        digits = re.sub(r"\D", "", key)
        cust = None
        if len(digits) >= 10:
            phone = digits[-10:]
            cust = await db.customers.find_one({"phone": {"$regex": prx(phone)}}, {"_id": 0})
        else:
            cust = await db.customers.find_one({"id": key[2:] if key.startswith("c:") else key}, {"_id": 0})
            phone = ph10((cust or {}).get("phone"))
        jq = {"$or": [{"customer_phone": {"$regex": prx(phone)}}] if phone else []}
        if cust:
            jq["$or"].append({"customer_id": cust["id"]})
        jobs = await db.service_jobs.find(jq, {"_id": 0, "photos_before": 0, "photos_after": 0, "signature_url": 0, "tech_signature_url": 0}).sort("created_at", -1).to_list(500) if jq["$or"] else []
        msgs = await db.contact_messages.find({"phone": {"$regex": prx(phone)}}, {"_id": 0}).sort("created_at", 1).to_list(200) if phone else []
        techs = {t["id"]: t.get("name", "") for t in await db.users.find({"role": "technician"}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)}
        sids = [m["sid"] for m in msgs if m.get("sid")]
        sessions = await db.visitor_sessions.find({"id": {"$in": sids}}, {"_id": 0, "ip": 0}).to_list(50) if sids else []
        journeys = []
        for s in sessions:
            journeys.append({"sid": s["id"], "first_seen": s.get("first_seen"), "channel": s.get("channel"), "source": s.get("source_name"), "campaign": s.get("campaign"), "term": s.get("term"),
                             "referrer": s.get("referrer"), "landing": s.get("landing_page"), "device": s.get("device"), "pages": s.get("pages", [])[-25:],
                             "searches": s.get("searches", []), "events": s.get("events", [])[-15:], "duration_sec": s.get("duration_sec", 0)})
        done = [j for j in jobs if j.get("status") in DONE]
        revenue = sum(_f(j.get("total_amount")) for j in done)
        collected = sum(_f(j.get("collected_amount"), _f(j.get("total_amount"))) if j.get("payment_status") != "veresiye" else _f(j.get("collected_amount")) for j in done)
        dates = sorted(j["completed_at"] for j in done if j.get("completed_at"))
        gaps = [(_dt(b) - _dt(a)).days for a, b in zip(dates, dates[1:]) if _dt(a) and _dt(b)]
        suggestions = []
        for j in done[:5]:
            dtp = (j.get("device_type") or "").lower()
            d0 = _dt(j.get("completed_at"))
            if d0 and any(x in dtp for x in ("kombi", "klima")) and (datetime.now(timezone.utc) - d0).days > 300:
                suggestions.append(f"{j.get('device_type')} için yıllık bakım zamanı (son servis {d0.astimezone(TR).strftime('%d.%m.%Y')})")
                break
        notes = await db.crm_notes.find({"key": phone or key}, {"_id": 0}).sort("at", -1).to_list(100)
        return {"customer": cust or {"name": (jobs[0].get("customer_name") if jobs else (msgs[0].get("name") if msgs else "")), "phone": phone}, "phone": phone,
                "summary": {"jobs": len(jobs), "done": len(done), "revenue": round(revenue, 2), "collected": round(collected, 2), "open_balance": round(max(0, revenue - collected), 2),
                            "avg_ticket": round(revenue / len(done), 2) if done else 0, "avg_gap_days": round(sum(gaps) / len(gaps)) if gaps else None,
                            "first_contact": (msgs[0]["created_at"] if msgs else (jobs[-1]["created_at"] if jobs else "")), "segment": _segment({"jobs": len(jobs), "done": len(done), "revenue": revenue, "last_job_at": jobs[0]["created_at"] if jobs else ""})},
                "jobs": [{"id": j["id"], "job_number": j.get("job_number"), "created_at": j.get("created_at"), "completed_at": j.get("completed_at"), "device": " ".join(x for x in [j.get("device_brand_name"), j.get("device_type")] if x),
                          "fault": (j.get("fault_description") or "")[:160], "status": j.get("status"), "total": j.get("total_amount", 0), "collected": j.get("collected_amount"),
                          "payment_status": j.get("payment_status", ""), "tech": techs.get(j.get("assigned_technician_id"), ""), "rating": j.get("customer_rating") or 0,
                          "comment": (j.get("survey") or {}).get("comment", "")} for j in jobs],
                "messages": [{"id": m["id"], "at": m.get("created_at"), "type": m.get("type"), "message": (m.get("message") or "")[:400], "status": m.get("status"), "channel": m.get("channel"), "page": m.get("page")} for m in msgs],
                "journeys": journeys, "suggestions": suggestions, "notes": notes}

    @api_router.post("/customers360/{key}/note")
    async def customer_note(key: str, payload: dict, user: dict = Depends(require_admin)):
        text = str(payload.get("text") or "").strip()[:1000]
        if not text:
            raise HTTPException(422, "Not boş olamaz")
        k = ph10(key) if len(re.sub(r"\D", "", key)) >= 10 else key
        doc = {"id": _id(), "key": k, "text": text, "by": user.get("name", ""), "at": _now()}
        await db.crm_notes.insert_one(dict(doc))
        return doc

    # ============================================================ KAYNAK / ARAMA ANALİZİ
    @api_router.get("/analytics/sources")
    async def sources(days: int = 90, _: dict = Depends(require_admin)):
        days = max(7, min(days, 730))
        since = _since(days)
        sess = await db.visitor_sessions.find({"first_seen": {"$gte": since}}, {"_id": 0, "channel": 1, "landing_page": 1, "term": 1, "source_name": 1, "campaign": 1}).to_list(100000)
        msgs = await db.contact_messages.find({"created_at": {"$gte": since}, "type": {"$in": ["servis_talebi", None]}}, {"_id": 0, "channel": 1, "source": 1, "page": 1, "job_id": 1, "device_type": 1, "phone": 1}).to_list(50000)
        jobs = {j["id"]: j for j in await _load(days + 30)}
        by_phone = defaultdict(list)
        for j in jobs.values():
            by_phone[ph10(j.get("customer_phone"))].append(j)
        ch = defaultdict(lambda: {"visits": 0, "leads": 0, "jobs": 0, "done": 0, "revenue": 0.0})
        pg = defaultdict(lambda: {"leads": 0, "done": 0, "revenue": 0.0})
        kw = defaultdict(lambda: {"leads": 0, "done": 0, "revenue": 0.0})
        dev = defaultdict(lambda: {"leads": 0, "done": 0, "revenue": 0.0})
        for s in sess:
            ch[s.get("channel") or "direkt"]["visits"] += 1
        for m in msgs:
            src = m.get("source") or {}
            c = m.get("channel") or src.get("channel") or "bilinmiyor"
            ch[c]["leads"] += 1
            j = jobs.get(m.get("job_id")) or next(iter(by_phone.get(ph10(m.get("phone")), [])), None)
            d = bool(j and j.get("status") in DONE)
            rev = _f(j.get("total_amount")) if d else 0.0
            if j:
                ch[c]["jobs"] += 1
            ch[c]["done"] += int(d)
            ch[c]["revenue"] += rev
            for store, key in ((pg, (src.get("landing_page") or m.get("page") or "?")[:70]), (kw, src.get("term") or ""), (dev, m.get("device_type") or "?")):
                if key:
                    store[key]["leads"] += 1
                    store[key]["done"] += int(d)
                    store[key]["revenue"] += rev

        def fin(dct, top=15, withvisits=False):
            rows = []
            for k, v in dct.items():
                rows.append({"name": k, **{a: (round(b, 2) if isinstance(b, float) else b) for a, b in v.items()},
                             "conv_pct": round(v["leads"] * 100 / v["visits"], 2) if v.get("visits") else None,
                             "avg_ticket": round(v["revenue"] / v["done"], 2) if v["done"] else 0,
                             "rev_per_visit": round(v["revenue"] / v["visits"], 2) if v.get("visits") else None})
            rows.sort(key=lambda r: (-r["revenue"], -r["leads"]))
            return rows[:top]
        logs = await db.search_logs.find({"ts": {"$gte": since}}, {"_id": 0, "q": 1, "results": 1}).to_list(100000)
        cnt, zero = defaultdict(int), defaultdict(int)
        for l in logs:
            cnt[l["q"]] += 1
            if l.get("results") == 0:
                zero[l["q"]] += 1
        return {"days": days, "visits": len(sess), "leads": len(msgs), "channels": fin(ch, 12), "pages": fin(pg, 15), "keywords": fin(kw, 15), "devices": fin(dev, 10),
                "site_search": {"total": len(logs), "top": sorted(({"q": k, "n": v} for k, v in cnt.items()), key=lambda x: -x["n"])[:25],
                                "zero_result": sorted(({"q": k, "n": v} for k, v in zero.items()), key=lambda x: -x["n"])[:25]},
                "note": "Kaynak verisi, ziyaretçi takibi (sid) ile gelen talepler için dolu olur; takip kodu eklendikten sonraki talepler izlenir."}

    # ============================================================ USTA PUANLAMA
    async def _tech_debt_old():
        """30 günden eski, ödenmemiş şirkete borç (FIFO) → kasa disiplini."""
        txs = await db.cash_transactions.find({"type": {"$in": ["teknisyen_borc", "teknisyen_odeme"]}}, {"_id": 0, "technician_id": 1, "type": 1, "amount": 1, "date": 1}).to_list(100000)
        per = defaultdict(lambda: {"borc": [], "odeme": 0.0})
        for t in txs:
            if t["type"] == "teknisyen_borc":
                per[t.get("technician_id", "")]["borc"].append((t.get("date", ""), _f(t["amount"])))
            else:
                per[t.get("technician_id", "")]["odeme"] += _f(t["amount"])
        old = {}
        cut = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        for tid, v in per.items():
            pay = v["odeme"]
            rest = 0.0
            for d, a in sorted(v["borc"]):
                used = min(pay, a)
                pay -= used
                if d < cut:
                    rest += a - used
            if rest > 1:
                old[tid] = round(rest, 2)
        return old

    async def _rate_techs(days, end_days_ago=0):
        techs = await db.users.find({"role": "technician"}, {"_id": 0, "password_hash": 0}).to_list(1000)
        a = (datetime.now(timezone.utc) - timedelta(days=days + end_days_ago)).isoformat()
        b = (datetime.now(timezone.utc) - timedelta(days=end_days_ago)).isoformat()
        alljobs = await _load(0)
        proj = {"_id": 0}
        per = await db.service_jobs.find({"created_at": {"$gte": a, "$lte": b}}, {**proj, "photos_before": 0}).to_list(30000)
        return score_techs(techs, per, alljobs, await _tech_debt_old() if end_days_ago == 0 else {}), techs

    @api_router.get("/tech-rating")
    async def tech_rating(days: int = 90, _: dict = Depends(require_admin)):
        days = max(7, min(days, 730))
        rows, _t = await _rate_techs(days)
        return {"days": days, "weights": [{"key": k, "label": LABELS[k], "weight": w} for k, w in WEIGHTS.items()], "rows": rows,
                "levels": [{"min": l, "name": n} for l, n in LEVELS] + [{"min": 0, "name": "Yeni (5 işten az)"}]}

    @api_router.get("/tech-rating/my")
    async def tech_rating_my(user: dict = Depends(get_current_user)):
        # Hız: 5 bağımsız hesap paralel (uzak veritabanında ardışık 15+ sorgu ~0,7 sn sürüyordu)
        (rows, _t), h2, h1, h0, notes = await asyncio.gather(
            _rate_techs(90), _rate_techs(30, 60), _rate_techs(30, 30), _rate_techs(30, 0),
            db.tech_notes.find({"technician_id": user["id"], "visible": {"$ne": False}}, {"_id": 0}).sort("at", -1).to_list(5))
        me = next((r for r in rows if r["id"] == user["id"]), None)
        hist = []
        for i, (r, _tt) in ((2, h2), (1, h1), (0, h0)):
            m = next((x for x in r if x["id"] == user["id"]), None)
            hist.append({"label": f"{(i + 1) * 30}-{i * 30} gün önce" if i else "Son 30 gün", "score": m["score"] if m else 0, "done": m["done"] if m else 0})
        return {"me": me, "of": len(rows), "rank": me["rank"] if me else None, "history": hist, "notes": notes}

    @api_router.get("/tech-rating/{tid}")
    async def tech_rating_detail(tid: str, _: dict = Depends(require_admin)):
        rows, techs = await _rate_techs(90)
        me = next((r for r in rows if r["id"] == tid), None)
        if not me:
            raise HTTPException(404, "Usta bulunamadı")
        hist = []
        _hs = await asyncio.gather(*[_rate_techs(30, i * 30) for i in (5, 4, 3, 2, 1, 0)])
        for i, (r, _tt) in zip((5, 4, 3, 2, 1, 0), _hs):
            m = next((x for x in r if x["id"] == tid), None)
            hist.append({"label": (datetime.now(TR) - timedelta(days=i * 30)).strftime("%m/%Y"), "score": m["score"] if m else 0, "done": m["done"] if m else 0, "rating": m["rating_avg"] if m else 0})
        low = await db.service_jobs.find({"assigned_technician_id": tid, "customer_rating": {"$gte": 1, "$lte": 3}}, {"_id": 0, "job_number": 1, "customer_rating": 1, "survey": 1, "completed_at": 1, "device_type": 1}).sort("completed_at", -1).to_list(8)
        notes = await db.tech_notes.find({"technician_id": tid}, {"_id": 0}).sort("at", -1).to_list(50)
        return {"tech": me, "history": hist, "low_rated": [{"job_number": j.get("job_number"), "rating": j.get("customer_rating"), "comment": (j.get("survey") or {}).get("comment", ""), "device": j.get("device_type"), "at": j.get("completed_at")} for j in low], "notes": notes}

    @api_router.post("/tech-rating/{tid}/note")
    async def tech_note(tid: str, payload: dict, user: dict = Depends(require_admin)):
        text = str(payload.get("text") or "").strip()[:600]
        kind = payload.get("kind") if payload.get("kind") in ("övgü", "uyarı", "not") else "not"
        if not text:
            raise HTTPException(422, "Metin boş olamaz")
        doc = {"id": _id(), "technician_id": tid, "kind": kind, "text": text, "by": user.get("name", ""), "at": _now(), "visible": bool(payload.get("visible", kind != "uyarı"))}
        await db.tech_notes.insert_one(dict(doc))
        return doc

    # ============================================================ MUHASEBE: TREND / YAŞLANDIRMA / ALACAK
    @api_router.get("/accounting/trends")
    async def acc_trends(months: int = 12, _: dict = Depends(require_admin)):
        months = max(3, min(months, 36))
        start = (datetime.now(TR).replace(day=1) - timedelta(days=31 * (months - 1))).replace(day=1).strftime("%Y-%m")
        txs = await db.cash_transactions.find({"type": {"$in": ["gelir", "gider", "manuel"]}}, {"_id": 0, "type": 1, "amount": 1, "date": 1, "category": 1}).to_list(200000)
        m = defaultdict(lambda: {"gelir": 0.0, "gider": 0.0, "jobs": 0})
        cats = defaultdict(float)
        for t in txs:
            k = _month(t.get("date"))
            if not k or k < start:
                continue
            if t["type"] == "gelir":
                m[k]["gelir"] += _f(t["amount"])
            elif t["type"] == "gider":
                m[k]["gider"] += _f(t["amount"])
                cats[t.get("category") or "Diğer"] += _f(t["amount"])
        for j in await _load(months * 31):
            k = _month(j.get("completed_at"))
            if k in m and j.get("status") in DONE:
                m[k]["jobs"] += 1
        rows = []
        prev = None
        for k in sorted(m):
            v = m[k]
            net = v["gelir"] - v["gider"]
            rows.append({"month": k, "income": round(v["gelir"], 2), "expense": round(v["gider"], 2), "net": round(net, 2), "margin_pct": round(net * 100 / v["gelir"], 1) if v["gelir"] else 0,
                         "jobs": v["jobs"], "avg_ticket": round(v["gelir"] / v["jobs"], 2) if v["jobs"] else 0,
                         "growth_pct": round((v["gelir"] - prev) * 100 / prev, 1) if prev else None})
            prev = v["gelir"] or prev
        tot = {"income": round(sum(r["income"] for r in rows), 2), "expense": round(sum(r["expense"] for r in rows), 2)}
        tot["net"] = round(tot["income"] - tot["expense"], 2)
        return {"months": rows, "total": tot, "expense_by_category": sorted(({"category": k, "amount": round(v, 2)} for k, v in cats.items()), key=lambda x: -x["amount"])[:12]}

    @api_router.get("/accounting/tech-aging")
    async def tech_aging(_: dict = Depends(require_admin)):
        txs = await db.cash_transactions.find({"type": {"$in": ["teknisyen_borc", "teknisyen_odeme"]}}, {"_id": 0}).to_list(200000)
        techs = {t["id"]: t.get("name", "") for t in await db.users.find({"role": "technician"}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)}
        per = defaultdict(lambda: {"borc": [], "odeme": 0.0})
        for t in txs:
            if t["type"] == "teknisyen_borc":
                per[t.get("technician_id", "")]["borc"].append((t.get("date", ""), _f(t["amount"])))
            else:
                per[t.get("technician_id", "")]["odeme"] += _f(t["amount"])
        now = datetime.now(timezone.utc)
        out = []
        for tid, v in per.items():
            pay, b = v["odeme"], {"0-7": 0.0, "8-30": 0.0, "31-60": 0.0, "60+": 0.0}
            for d, a in sorted(v["borc"]):
                used = min(pay, a)
                pay -= used
                rest = a - used
                if rest <= 0:
                    continue
                age = (now - (_dt(d) or now)).days
                b["0-7" if age <= 7 else "8-30" if age <= 30 else "31-60" if age <= 60 else "60+"] += rest
            tot = sum(b.values())
            if tot > 0.5:
                out.append({"technician_id": tid, "name": techs.get(tid, "?"), "total": round(tot, 2), **{"b_" + k.replace("-", "_").replace("+", "p"): round(x, 2) for k, x in b.items()}})
        out.sort(key=lambda r: -r["total"])
        return {"rows": out, "total": round(sum(r["total"] for r in out), 2)}

    @api_router.get("/accounting/receivables")
    async def receivables(_: dict = Depends(require_admin)):
        """Tamamlanmış ama tahsil edilmemiş (veresiye/kısmi) müşteri işleri. `payment_status`/`collected_amount` yoksa tahsil edilmiş sayılır."""
        jobs = await db.service_jobs.find({"status": {"$in": list(DONE)}, "payment_status": {"$in": ["veresiye", "kismi"]}}, {"_id": 0, "photos_before": 0, "photos_after": 0, "signature_url": 0, "tech_signature_url": 0}).to_list(5000)
        now = datetime.now(timezone.utc)
        rows, b = [], {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
        for j in jobs:
            open_ = _f(j.get("total_amount")) - _f(j.get("collected_amount"))
            if open_ <= 0.5:
                continue
            age = (now - (_dt(j.get("completed_at")) or now)).days
            b["0-30" if age <= 30 else "31-60" if age <= 60 else "61-90" if age <= 90 else "90+"] += open_
            rows.append({"id": j["id"], "job_number": j.get("job_number"), "customer": j.get("customer_name"), "phone": j.get("customer_phone"), "total": j.get("total_amount", 0),
                         "collected": _f(j.get("collected_amount")), "open": round(open_, 2), "age_days": age, "status": j.get("payment_status"), "completed_at": j.get("completed_at")})
        rows.sort(key=lambda r: -r["age_days"])
        return {"rows": rows, "total": round(sum(r["open"] for r in rows), 2), "buckets": {k: round(v, 2) for k, v in b.items()}}

    @api_router.get("/accounting/job-lookup")
    async def job_lookup(number: str, _: dict = Depends(require_admin)):
        j = await db.service_jobs.find_one({"job_number": {"$regex": "^" + re.escape(number.strip()) + "$", "$options": "i"}},
                                           {"_id": 0, "id": 1, "job_number": 1, "customer_name": 1, "total_amount": 1, "status": 1, "collected_amount": 1, "payment_status": 1})
        if not j:
            raise HTTPException(404, "Bu numarada iş yok")
        return j

    @api_router.put("/accounting/jobs/{jid}/collection")
    async def set_collection(jid: str, payload: dict, user: dict = Depends(require_admin)):
        job = await db.service_jobs.find_one({"id": jid}, {"_id": 0, "id": 1, "total_amount": 1, "collected_amount": 1, "job_number": 1, "customer_name": 1})
        if not job:
            raise HTTPException(404, "İş bulunamadı")
        total = _f(job.get("total_amount"))
        mode = payload.get("mode")
        add = _f(payload.get("amount"))
        if mode == "veresiye":
            upd = {"payment_status": "veresiye", "collected_amount": _f(job.get("collected_amount"))}
        else:
            got = _f(job.get("collected_amount")) + (add if mode == "tahsilat" else total - _f(job.get("collected_amount")))
            got = min(max(got, 0), total)
            upd = {"collected_amount": round(got, 2), "payment_status": "odendi" if got >= total - 0.5 else "kismi"}
            if mode == "tahsilat" and add <= 0:
                raise HTTPException(422, "Tutar girin")
        upd["collection_note"] = str(payload.get("note") or "")[:200]
        upd["collection_at"] = _now()
        await db.service_jobs.update_one({"id": jid}, {"$set": upd})
        return {"ok": True, **upd}


async def ensure_indexes(db):
    try:
        await db.search_logs.create_index("day")
        await db.search_logs.create_index("ts_dt", expireAfterSeconds=730 * 86400)
        await db.crm_notes.create_index("key")
        await db.tech_notes.create_index("technician_id")
    except Exception:
        pass
