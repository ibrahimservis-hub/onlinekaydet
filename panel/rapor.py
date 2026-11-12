"""Rapor Merkezi: servis, müşteri yolculuğu (nereden/nasıl/kaç kez girdi), usta, site ve finans raporları tek yerde.
Yalnızca OKUMA. Yeni koleksiyon/indeks yok. Hepsi yönetici yetkisiyle: GET /api/rapor/{ozet|musteri|usta|site|finans}?days=..&fmt=csv"""
import csv
import io
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

from fastapi import Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                     # pragma: no cover
    TR = timezone(timedelta(hours=3))

DONE = ("tamamlandi", "faturalandi")
CANCEL = ("iptal",)
CH = {"google_ads": "Google Ads (Reklam)", "meta_ads": "Meta Reklam", "diger_reklam": "Diğer Reklam", "organik": "Organik Arama", "sosyal": "Sosyal Medya",
      "referans": "Referans Site", "direkt": "Direkt Giriş", "telefon": "Telefon (Çağrı)", "whatsapp": "WhatsApp", "tavsiye": "Tavsiye",
      "tekrar_musteri": "Tekrar Müşteri", "bayi": "Bayi / İş Ortağı", "diger": "Diğer", "": "Belirtilmemiş", "belirtilmemis": "Belirtilmemiş", "bilinmiyor": "Belirtilmemiş"}
_C = {}


def _f(v, d=0.0):
    try:
        return float(v)
    except Exception:                                 # noqa: BLE001
        return d


def _dt(s):
    try:
        x = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return x if x.tzinfo else x.replace(tzinfo=timezone.utc)
    except Exception:                                 # noqa: BLE001
        return None


def _day(s):
    x = _dt(s)
    return x.astimezone(TR).strftime("%Y-%m-%d") if x else ""


def ph10(p):
    d = re.sub(r"\D", "", str(p or ""))
    return d[-10:] if len(d) >= 10 else ""


def _rating(j):
    r = j.get("customer_rating") or (j.get("survey") or {}).get("rating") or 0
    try:
        r = int(r)
    except Exception:                                 # noqa: BLE001
        r = 0
    return r if 1 <= r <= 5 else 0


def _pct(a, b):
    return round(a * 100.0 / b, 1) if b else 0.0


def _chg(cur, prev):
    if not prev:
        return None
    return round((cur - prev) * 100.0 / prev, 1)


def _hours(a, b):
    x, y = _dt(a), _dt(b)
    if not x or not y or y < x:
        return None
    return (y - x).total_seconds() / 3600.0


def _top(counter, n=10):
    return [{"name": k or "—", "value": v} for k, v in counter.most_common(n)]


def _csv(rows, cols, name):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow([c[1] for c in cols])
    for r in rows:
        w.writerow([("" if r.get(c[0]) is None else r.get(c[0])) for c in cols])
    return StreamingResponse(iter(["﻿" + buf.getvalue()]), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": f"attachment; filename={name}.csv"})


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    def _since(days):
        return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    async def _cached(key, ttl, fn):
        hit = _C.get(key)
        if hit and time.monotonic() - hit[0] < ttl:
            return hit[1]
        v = await fn()
        _C[key] = (time.monotonic(), v)
        if len(_C) > 60:
            for k in sorted(_C, key=lambda k: _C[k][0])[:20]:
                _C.pop(k, None)
        return v

    async def _customers_map():
        cs = await db.customers.find({}, {"_id": 0, "id": 1, "name": 1, "phone": 1, "city": 1, "district": 1, "created_at": 1, "source_channel": 1}).to_list(100000)
        return cs, {c["id"]: c for c in cs}

    JOB_F = {"_id": 0, "id": 1, "job_number": 1, "created_at": 1, "completed_at": 1, "started_at": 1, "scheduled_at": 1, "status": 1, "total_amount": 1, "collected_amount": 1,
             "payment_status": 1, "customer_id": 1, "customer_name": 1, "customer_phone": 1, "assigned_technician_id": 1, "assigned_technician_name": 1, "device_type": 1,
             "device_brand_name": 1, "source_channel": 1, "customer_rating": 1, "survey": 1, "tech_share": 1}

    # ====================================================================== ÖZET
    @api_router.get("/rapor/ozet")
    async def rapor_ozet(days: int = Query(30, ge=1, le=730), _: dict = Depends(require_admin)):
        async def build():
            since, prev_since = _since(days), _since(days * 2)
            jobs = await db.service_jobs.find({"created_at": {"$gte": prev_since}}, JOB_F).to_list(100000)
            cs, cmap = await _customers_map()
            sess = await db.visitor_sessions.find({"first_seen": {"$gte": prev_since}}, {"_id": 0, "first_seen": 1, "channel": 1, "pages_count": 1, "conv_call": 1, "conv_whatsapp": 1,
                                                                                         "conv_form": 1, "conv_dealer": 1}).to_list(200000)
            leads = await db.contact_messages.find({"created_at": {"$gte": prev_since}, "type": {"$in": ["servis_talebi", None]}}, {"_id": 0, "created_at": 1, "channel": 1}).to_list(100000)

            cur = [j for j in jobs if (j.get("created_at") or "") >= since]
            prv = [j for j in jobs if (j.get("created_at") or "") < since]

            def agg(js):
                done = [j for j in js if j.get("status") in DONE]
                rev = sum(_f(j.get("total_amount")) for j in done)
                hrs = [h for h in (_hours(j.get("created_at"), j.get("completed_at")) for j in done) if h is not None]
                rts = [r for r in (_rating(j) for j in js) if r]
                return {"jobs": len(js), "done": len(done), "cancel": sum(1 for j in js if j.get("status") in CANCEL),
                        "open": sum(1 for j in js if j.get("status") not in DONE + CANCEL), "revenue": round(rev, 2),
                        "avg_ticket": round(rev / len(done), 2) if done else 0, "avg_hours": round(sum(hrs) / len(hrs), 1) if hrs else None,
                        "rating": round(sum(rts) / len(rts), 2) if rts else None, "rating_n": len(rts),
                        "done_rate": _pct(len(done), len(js))}
            a, b = agg(cur), agg(prv)
            new_c = sum(1 for c in cs if (c.get("created_at") or "") >= since)
            new_p = sum(1 for c in cs if prev_since <= (c.get("created_at") or "") < since)
            s_cur = [s for s in sess if (s.get("first_seen") or "") >= since]
            s_prv = [s for s in sess if (s.get("first_seen") or "") < since]
            l_cur = [l for l in leads if (l.get("created_at") or "") >= since]
            l_prv = len(leads) - len(l_cur)
            # tekrar müşteri: dönemde iş açan, daha önce de işi olan
            first_job = {}
            for j in sorted(jobs, key=lambda x: x.get("created_at") or ""):
                k = ph10(j.get("customer_phone")) or j.get("customer_id")
                first_job.setdefault(k, j.get("created_at") or "")
            repeat = len({(ph10(j.get("customer_phone")) or j.get("customer_id")) for j in cur if first_job.get(ph10(j.get("customer_phone")) or j.get("customer_id"), "") < since})
            # günlük seri
            today = datetime.now(TR).date()
            dl = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(min(days, 90) - 1, -1, -1)]
            ds = {d: {"date": d, "label": d[8:] + "." + d[5:7], "jobs": 0, "done": 0, "revenue": 0.0, "sessions": 0, "leads": 0} for d in dl}
            for j in cur:
                d = _day(j.get("created_at"))
                if d in ds:
                    ds[d]["jobs"] += 1
                if j.get("status") in DONE:
                    d2 = _day(j.get("completed_at") or j.get("created_at"))
                    if d2 in ds:
                        ds[d2]["done"] += 1
                        ds[d2]["revenue"] += _f(j.get("total_amount"))
            for s in s_cur:
                d = _day(s.get("first_seen"))
                if d in ds:
                    ds[d]["sessions"] += 1
            for l in l_cur:
                d = _day(l.get("created_at"))
                if d in ds:
                    ds[d]["leads"] += 1
            for v in ds.values():
                v["revenue"] = round(v["revenue"], 2)
            st = Counter(j.get("status") or "?" for j in cur)
            dev = Counter(j.get("device_type") or "—" for j in cur)
            brand = Counter(j.get("device_brand_name") or "—" for j in cur)
            ch = Counter(CH.get(j.get("source_channel") or "", j.get("source_channel") or "Belirtilmemiş") for j in cur)
            city, dist = Counter(), Counter()
            rev_city = defaultdict(float)
            for j in cur:
                c = cmap.get(j.get("customer_id")) or {}
                cy = (c.get("city") or "—").strip() or "—"
                city[cy] += 1
                dd = ((c.get("district") or "").strip() or "—")
                dist[cy + " / " + dd] += 1
                if j.get("status") in DONE:
                    rev_city[cy] += _f(j.get("total_amount"))
            calls = sum(s.get("conv_call", 0) for s in s_cur)
            wa = sum(s.get("conv_whatsapp", 0) for s in s_cur)
            forms = sum((s.get("conv_form", 0) or 0) + (s.get("conv_dealer", 0) or 0) for s in s_cur)
            sess_n = len(s_cur)
            return {"days": days, "jobs": a, "prev": b, "chg": {"jobs": _chg(a["jobs"], b["jobs"]), "revenue": _chg(a["revenue"], b["revenue"]), "done": _chg(a["done"], b["done"]),
                                                              "customers": _chg(new_c, new_p), "sessions": _chg(sess_n, len(s_prv)), "leads": _chg(len(l_cur), l_prv)},
                    "customers": {"new": new_c, "total": len(cs), "repeat": repeat},
                    "site": {"sessions": sess_n, "pageviews": sum(s.get("pages_count", 0) for s in s_cur), "calls": calls, "whatsapp": wa, "forms": forms, "leads": len(l_cur)},
                    "funnel": [{"name": "Site oturumu", "value": sess_n}, {"name": "Talep / iletişim", "value": len(l_cur) + calls + wa},
                               {"name": "Servis kaydı", "value": a["jobs"]}, {"name": "Tamamlanan", "value": a["done"]}],
                    "daily": list(ds.values()), "status": _top(st, 12), "devices": _top(dev, 8), "brands": _top(brand, 10), "channels": _top(ch, 10),
                    "cities": [{"name": k, "value": v, "revenue": round(rev_city.get(k, 0), 2)} for k, v in city.most_common(10)], "districts": _top(dist, 12)}
        return await _cached(("ozet", days), 60, build)

    # ====================================================================== MÜŞTERİ YOLCULUĞU
    MCOLS = [("name", "Müşteri"), ("phone", "Telefon"), ("city", "İl"), ("district", "İlçe"), ("first_contact", "İlk temas"), ("channel_label", "Nereden geldi"),
             ("source", "Kaynak"), ("campaign", "Kampanya"), ("term", "Anahtar kelime"), ("landing", "İlk giriş sayfası"), ("device", "Cihaz"), ("how", "Nasıl ulaştı"),
             ("sessions", "Oturum"), ("visit_days", "Kaç gün girdi"), ("pageviews", "Sayfa görüntüleme"), ("calls", "Arama tık"), ("whatsapp", "WhatsApp tık"),
             ("forms", "Form/talep"), ("jobs", "Servis"), ("done", "Tamamlanan"), ("revenue", "Ciro"), ("rating", "Puan"), ("last_job", "Son servis"), ("tech", "Usta")]

    @api_router.get("/rapor/musteri")
    async def rapor_musteri(days: int = Query(90, ge=1, le=1460), q: str = "", channel: str = "", sort: str = "recent", limit: int = Query(400, ge=10, le=3000),
                            fmt: str = "", _: dict = Depends(require_admin)):
        since = _since(days)
        cs, cmap = await _customers_map()
        jobs = await db.service_jobs.find({}, JOB_F).to_list(200000)
        msgs = await db.contact_messages.find({}, {"_id": 0, "phone": 1, "name": 1, "city": 1, "district": 1, "channel": 1, "source": 1, "page": 1, "created_at": 1, "sid": 1,
                                                    "device_type": 1, "type": 1}).sort("created_at", 1).to_list(100000)
        rows = {}

        def row(k, name="", phone="", city="", district=""):
            if k not in rows:
                rows[k] = {"key": k, "name": name, "phone": phone, "city": city, "district": district, "first_contact": "", "channel": "", "source": "", "campaign": "", "term": "",
                           "landing": "", "device": "", "how": "", "sids": [], "calls": 0, "whatsapp": 0, "forms": 0, "jobs": 0, "done": 0, "revenue": 0.0, "rs": 0, "rn": 0,
                           "last_job": "", "techs": set(), "last_active": ""}
            r = rows[k]
            for f, v in (("name", name), ("phone", phone), ("city", city), ("district", district)):
                if v and not r[f]:
                    r[f] = v
            return r
        for c in cs:
            k = ph10(c.get("phone")) or "c:" + c["id"]
            r = row(k, c.get("name", ""), c.get("phone", ""), c.get("city", ""), c.get("district", ""))
            r["first_contact"] = c.get("created_at", "")
            r["last_active"] = max(r["last_active"], c.get("created_at", ""))
            if c.get("source_channel") and not r["channel"]:
                r["channel"] = c["source_channel"]
                r["how"] = "Elle kayıt"
        for j in jobs:
            k = ph10(j.get("customer_phone")) or ("c:" + j["customer_id"] if j.get("customer_id") else "")
            if not k:
                continue
            c = cmap.get(j.get("customer_id")) or {}
            r = row(k, j.get("customer_name", ""), j.get("customer_phone", ""), c.get("city", ""), c.get("district", ""))
            r["jobs"] += 1
            if j.get("status") in DONE:
                r["done"] += 1
                r["revenue"] += _f(j.get("total_amount"))
            if _rating(j):
                r["rs"] += _rating(j)
                r["rn"] += 1
            if (j.get("created_at") or "") > r["last_job"]:
                r["last_job"] = j.get("created_at") or ""
            r["last_active"] = max(r["last_active"], j.get("created_at") or "")
            if j.get("assigned_technician_name"):
                r["techs"].add(j["assigned_technician_name"])
            if j.get("source_channel") and not r["channel"]:
                r["channel"] = j["source_channel"]
                r["how"] = "Servis kaydı"
            if not r["first_contact"] or (j.get("created_at") or "") < r["first_contact"]:
                r["first_contact"] = j.get("created_at") or ""
        for m in msgs:
            k = ph10(m.get("phone"))
            if not k:
                continue
            r = row(k, m.get("name", ""), m.get("phone", ""), m.get("city", ""), m.get("district", ""))
            r["forms"] += 1
            r["last_active"] = max(r["last_active"], m.get("created_at") or "")
            if m.get("sid") and m["sid"] not in r["sids"]:
                r["sids"].append(m["sid"])
            src = m.get("source") or {}
            if not r["source"] and (m.get("channel") or src.get("channel")):
                r["channel"] = m.get("channel") or src.get("channel") or r["channel"]
                r["source"] = src.get("source_name", "")
                r["campaign"] = src.get("campaign", "")
                r["term"] = src.get("term", "")
                r["landing"] = (src.get("landing_page") or m.get("page") or "")[:90]
                r["how"] = "Site formu" if m.get("sid") else "Mesaj"
            if m.get("device_type") and not r["device"]:
                r["device"] = m["device_type"]
            if not r["first_contact"] or (m.get("created_at") or "") < r["first_contact"]:
                r["first_contact"] = m.get("created_at") or ""
        # dönem + arama süzgeci
        ql, qd = q.lower().strip(), re.sub(r"\D", "", q)
        sel = []
        for r in rows.values():
            if r["last_active"] < since and r["first_contact"] < since:
                continue
            if ql and ql not in (r["name"] or "").lower() and not (qd and qd in re.sub(r"\D", "", r["phone"] or "")) and ql not in (r["city"] or "").lower() and ql not in (r["district"] or "").lower():
                continue
            if channel and (r["channel"] or "belirtilmemis") != channel:
                continue
            sel.append(r)
        sel.sort(key=lambda r: (-r["revenue"], r["last_active"]) if sort == "revenue" else r["last_active"], reverse=(sort != "revenue"))
        total = len(sel)
        sel = sel[:limit]
        sids = list({s for r in sel for s in r["sids"]})
        pv, sd = {}, {}
        if sids:
            async for x in db.pageviews.aggregate([{"$match": {"sid": {"$in": sids}}}, {"$group": {"_id": "$sid", "n": {"$sum": 1}, "days": {"$addToSet": "$day"}}}]):
                pv[x["_id"]] = x
            for s in await db.visitor_sessions.find({"id": {"$in": sids}}, {"_id": 0, "id": 1, "device": 1, "browser": 1, "os": 1, "conv_call": 1, "conv_whatsapp": 1, "first_seen": 1,
                                                                             "duration_sec": 1, "referrer": 1}).to_list(len(sids)):
                sd[s["id"]] = s
        out = []
        for r in sel:
            days_set, n_pv, dur = set(), 0, 0
            first_v = ""
            for s in r["sids"]:
                p = pv.get(s)
                if p:
                    days_set.update(p["days"])
                    n_pv += p["n"]
                se = sd.get(s) or {}
                r["calls"] += se.get("conv_call", 0)
                r["whatsapp"] += se.get("conv_whatsapp", 0)
                dur += se.get("duration_sec", 0)
                if se.get("first_seen") and (not first_v or se["first_seen"] < first_v):
                    first_v = se["first_seen"]
                if not r["device"] and se.get("device"):
                    r["device"] = (se.get("device") or "") + " · " + (se.get("browser") or "")
            if r["sids"] and r["device"] and " · " not in r["device"]:
                se = sd.get(r["sids"][0]) or {}
                r["device"] = ((se.get("device") or "") + " · " + (se.get("browser") or "")).strip(" ·") or r["device"]
            ch = r["channel"] or ("" if not r["sids"] else "direkt")
            out.append({"key": r["key"], "name": r["name"], "phone": r["phone"], "city": r["city"], "district": r["district"], "first_contact": (r["first_contact"] or "")[:16].replace("T", " "),
                        "first_visit": (first_v or "")[:16].replace("T", " "), "channel": ch, "channel_label": CH.get(ch, ch or "Belirtilmemiş"), "source": r["source"], "campaign": r["campaign"],
                        "term": r["term"], "landing": r["landing"], "device": r["device"], "how": r["how"] or ("Bilinmiyor"), "sessions": len(r["sids"]), "visit_days": len(days_set),
                        "pageviews": n_pv, "duration_sec": dur, "calls": r["calls"], "whatsapp": r["whatsapp"], "forms": r["forms"], "jobs": r["jobs"], "done": r["done"],
                        "revenue": round(r["revenue"], 2), "rating": round(r["rs"] / r["rn"], 2) if r["rn"] else None, "last_job": (r["last_job"] or "")[:10], "tech": ", ".join(sorted(r["techs"]))[:60]})
        if fmt == "csv":
            return _csv(out, MCOLS, "musteri-yolculugu")
        ch_c = Counter(o["channel_label"] for o in out)
        return {"days": days, "total": total, "shown": len(out), "rows": out, "channels": _top(ch_c, 12),
                "summary": {"tracked": sum(1 for o in out if o["sessions"]), "with_job": sum(1 for o in out if o["jobs"]), "revenue": round(sum(o["revenue"] for o in out), 2),
                            "avg_visit_days": round(sum(o["visit_days"] for o in out if o["sessions"]) / max(1, sum(1 for o in out if o["sessions"])), 1)},
                "note": "Site ziyareti (kaç gün girdi, sayfa, kaynak) yalnızca site formu doldurmuş / ziyaretçi takibiyle eşleşen müşteriler için görünür; telefonla gelenler 'Telefon' / 'Elle kayıt' olarak listelenir."}

    # ====================================================================== USTA
    UCOLS = [("name", "Usta"), ("jobs", "Atanan"), ("done", "Tamamlanan"), ("cancel", "İptal"), ("open", "Açık"), ("done_rate", "Tamamlama %"), ("revenue", "Ciro"), ("avg_ticket", "Ort. fiş"),
             ("avg_hours", "Ort. süre (saat)"), ("rating", "Ort. puan"), ("rating_n", "Puan sayısı"), ("low", "Düşük puan (≤3)"), ("share", "Usta payı"), ("debt", "Şirkete borç"),
             ("top_device", "En çok cihaz"), ("top_city", "En çok bölge"), ("last_job", "Son iş")]

    @api_router.get("/rapor/usta")
    async def rapor_usta(days: int = Query(30, ge=1, le=730), fmt: str = "", _: dict = Depends(require_admin)):
        since = _since(days)
        techs = await db.users.find({"role": "technician"}, {"_id": 0, "id": 1, "name": 1, "is_active": 1, "city": 1}).to_list(5000)
        jobs = await db.service_jobs.find({"created_at": {"$gte": since}}, JOB_F).to_list(100000)
        cs, cmap = await _customers_map()
        txs = await db.cash_transactions.find({"type": {"$in": ["teknisyen_borc", "teknisyen_odeme", "teknisyen_prim"]}}, {"_id": 0, "technician_id": 1, "type": 1, "amount": 1, "date": 1}).to_list(200000)
        debt, share = defaultdict(float), defaultdict(float)
        for t in txs:
            k = t.get("technician_id")
            if t["type"] == "teknisyen_borc":
                debt[k] += _f(t.get("amount"))
            elif t["type"] == "teknisyen_odeme":
                debt[k] -= _f(t.get("amount"))
            elif t["type"] == "teknisyen_prim" and (t.get("date") or "") >= since:
                share[k] += _f(t.get("amount"))
        by = defaultdict(list)
        for j in jobs:
            by[j.get("assigned_technician_id") or ""].append(j)
        out = []
        for t in techs + [{"id": "", "name": "— Atanmamış —", "is_active": True}]:
            js = by.get(t["id"], [])
            if not js and t["id"] == "":
                continue
            done = [j for j in js if j.get("status") in DONE]
            rev = sum(_f(j.get("total_amount")) for j in done)
            hrs = [h for h in (_hours(j.get("started_at") or j.get("created_at"), j.get("completed_at")) for j in done) if h is not None and h < 24 * 60]
            rts = [_rating(j) for j in js if _rating(j)]
            dv = Counter(j.get("device_type") or "—" for j in js)
            cy = Counter(((cmap.get(j.get("customer_id")) or {}).get("city") or "—") for j in js)
            out.append({"id": t["id"], "name": t.get("name", ""), "active": t.get("is_active", True) is not False, "jobs": len(js), "done": len(done),
                        "cancel": sum(1 for j in js if j.get("status") in CANCEL), "open": sum(1 for j in js if j.get("status") not in DONE + CANCEL), "done_rate": _pct(len(done), len(js)),
                        "revenue": round(rev, 2), "avg_ticket": round(rev / len(done), 2) if done else 0, "avg_hours": round(sum(hrs) / len(hrs), 1) if hrs else None,
                        "rating": round(sum(rts) / len(rts), 2) if rts else None, "rating_n": len(rts), "low": sum(1 for r in rts if r <= 3), "share": round(share.get(t["id"], 0), 2),
                        "debt": round(max(0, debt.get(t["id"], 0)), 2), "top_device": dv.most_common(1)[0][0] if dv else "", "top_city": cy.most_common(1)[0][0] if cy else "",
                        "last_job": max((j.get("created_at") or "" for j in js), default="")[:10]})
        out.sort(key=lambda r: (-r["revenue"], -r["done"]))
        if fmt == "csv":
            return _csv(out, UCOLS, "usta-raporu")
        tot_rev = sum(o["revenue"] for o in out)
        return {"days": days, "rows": out, "summary": {"techs": sum(1 for o in out if o["id"]), "active_in_period": sum(1 for o in out if o["jobs"] and o["id"]), "revenue": round(tot_rev, 2),
                                                       "jobs": sum(o["jobs"] for o in out), "unassigned": next((o["jobs"] for o in out if not o["id"]), 0),
                                                       "total_debt": round(sum(o["debt"] for o in out), 2)}}

    # ====================================================================== SİTE
    SCOLS = [("label", "Kanal"), ("sessions", "Oturum"), ("pageviews", "Sayfa"), ("calls", "Arama tık"), ("whatsapp", "WhatsApp tık"), ("forms", "Form"), ("conv_rate", "Dönüşüm %"),
             ("bounce_rate", "Hemen çıkış %"), ("avg_duration", "Ort. süre (sn)"), ("jobs", "Servis"), ("done", "Tamamlanan"), ("revenue", "Ciro")]

    @api_router.get("/rapor/site")
    async def rapor_site(days: int = Query(30, ge=1, le=365), fmt: str = "", _: dict = Depends(require_admin)):
        async def build():
            since = _since(days)
            sess = await db.visitor_sessions.find({"first_seen": {"$gte": since}}, {"_id": 0, "events": 0, "ip": 0}).to_list(150000)
            pvs = await db.pageviews.find({"ts": {"$gte": since}}, {"_id": 0, "path": 1, "sid": 1, "day": 1, "hour": 1}).to_list(400000)
            leads = await db.contact_messages.find({"created_at": {"$gte": since}}, {"_id": 0, "city": 1, "district": 1, "device_type": 1, "brand": 1, "type": 1, "channel": 1, "page": 1, "created_at": 1}).to_list(100000)
            jobs = await db.service_jobs.find({"created_at": {"$gte": since}}, {"_id": 0, "source_channel": 1, "status": 1, "total_amount": 1}).to_list(100000)
            logs = await db.search_logs.find({"ts": {"$gte": since}}, {"_id": 0, "q": 1, "results": 1}).to_list(100000)
            chs = {}
            for s in sess:
                c = s.get("channel") or "direkt"
                r = chs.setdefault(c, {"channel": c, "label": CH.get(c, c), "sessions": 0, "pageviews": 0, "calls": 0, "whatsapp": 0, "forms": 0, "bounce": 0, "dur": 0, "conv": 0, "jobs": 0, "done": 0, "revenue": 0.0})
                r["sessions"] += 1
                r["pageviews"] += s.get("pages_count", 0)
                r["calls"] += s.get("conv_call", 0)
                r["whatsapp"] += s.get("conv_whatsapp", 0)
                r["forms"] += (s.get("conv_form", 0) or 0) + (s.get("conv_dealer", 0) or 0)
                r["bounce"] += 1 if s.get("pages_count", 0) <= 1 and not s.get("converted") else 0
                r["conv"] += 1 if s.get("converted") else 0
                r["dur"] += s.get("duration_sec", 0)
            for j in jobs:
                c = j.get("source_channel") or "belirtilmemis"
                r = chs.setdefault(c, {"channel": c, "label": CH.get(c, c), "sessions": 0, "pageviews": 0, "calls": 0, "whatsapp": 0, "forms": 0, "bounce": 0, "dur": 0, "conv": 0, "jobs": 0, "done": 0, "revenue": 0.0})
                r["jobs"] += 1
                if j.get("status") in DONE:
                    r["done"] += 1
                    r["revenue"] += _f(j.get("total_amount"))
            channels = []
            for r in chs.values():
                n = r["sessions"]
                conv = r["conv"]
                channels.append({**{k: v for k, v in r.items() if k not in ("bounce", "dur", "conv")}, "revenue": round(r["revenue"], 2), "conv_rate": _pct(conv, n), "bounce_rate": _pct(r["bounce"], n),
                                 "avg_duration": round(r["dur"] / n) if n else 0})
            channels.sort(key=lambda r: (-r["sessions"], -r["jobs"]))
            tot = len(sess)
            conv_s = sum(1 for s in sess if s.get("converted"))
            bounce = sum(1 for s in sess if s.get("pages_count", 0) <= 1 and not s.get("converted"))
            vdays = defaultdict(set)
            for p in pvs:
                vdays[p.get("sid")].add(p.get("day"))
            returning = sum(1 for v in vdays.values() if len(v) > 1)
            land = defaultdict(lambda: {"sessions": 0, "conv": 0})
            for s in sess:
                lp = (s.get("landing_page") or "/")[:80]
                land[lp]["sessions"] += 1
                land[lp]["conv"] += 1 if s.get("converted") else 0
            landing = sorted(({"name": k, "sessions": v["sessions"], "conv": v["conv"], "rate": _pct(v["conv"], v["sessions"])} for k, v in land.items()), key=lambda r: -r["sessions"])[:15]
            hours = Counter(s.get("hour", 0) for s in sess)
            wk = Counter()
            for s in sess:
                d = _dt(s.get("first_seen"))
                if d:
                    wk[d.astimezone(TR).weekday()] += 1
            wnames = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
            lc, ld, lsv, lbr = Counter(), Counter(), Counter(), Counter()
            for l in leads:
                if (l.get("city") or "").strip():
                    lc[l["city"].strip()] += 1
                    ld[(l["city"].strip() + " / " + (l.get("district") or "—").strip())] += 1
                if l.get("device_type"):
                    lsv[l["device_type"]] += 1
                if l.get("brand"):
                    lbr[l["brand"]] += 1
            cnt, zero = Counter(), Counter()
            for l in logs:
                cnt[l.get("q")] += 1
                if l.get("results") == 0:
                    zero[l.get("q")] += 1
            return {"days": days, "kpi": {"sessions": tot, "visitors": len({s["id"] for s in sess}), "pageviews": sum(s.get("pages_count", 0) for s in sess), "returning": returning,
                                           "conv_rate": _pct(conv_s, tot), "bounce_rate": _pct(bounce, tot), "avg_duration": round(sum(s.get("duration_sec", 0) for s in sess) / tot) if tot else 0,
                                           "calls": sum(s.get("conv_call", 0) for s in sess), "whatsapp": sum(s.get("conv_whatsapp", 0) for s in sess), "leads": len(leads)},
                    "channels": channels, "landing": landing, "top_pages": _top(Counter(p.get("path") for p in pvs), 15),
                    "sources": _top(Counter(s.get("source_name") or "-" for s in sess), 12), "campaigns": _top(Counter(s.get("campaign") for s in sess if s.get("campaign")), 12),
                    "terms": _top(Counter(s.get("term") for s in sess if s.get("term")), 15), "referrers": _top(Counter((re.sub(r"^https?://(www\.)?", "", s.get("referrer") or "").split("/")[0] or "(doğrudan)") for s in sess), 12),
                    "devices": _top(Counter(s.get("device") for s in sess), 6), "browsers": _top(Counter(s.get("browser") for s in sess), 6), "os": _top(Counter(s.get("os") for s in sess), 6),
                    "hourly": [{"name": f"{h:02d}", "value": hours.get(h, 0)} for h in range(24)], "weekday": [{"name": wnames[i], "value": wk.get(i, 0)} for i in range(7)],
                    "lead_cities": _top(lc, 12), "lead_districts": _top(ld, 15), "lead_services": _top(lsv, 8), "lead_brands": _top(lbr, 10),
                    "site_search": {"total": len(logs), "top": [{"name": k, "value": v} for k, v in cnt.most_common(15)], "zero": [{"name": k, "value": v} for k, v in zero.most_common(15)]},
                    "note": "Ziyaretçi şehri toplanmaz; bölge bilgisi site formundan gelen talepler üzerindendir."}
        res = await _cached(("site", days), 60, build)
        if fmt == "csv":
            return _csv(res["channels"], SCOLS, "site-kanallar")
        return res

    # ====================================================================== FİNANS
    @api_router.get("/rapor/finans")
    async def rapor_finans(days: int = Query(30, ge=1, le=730), _: dict = Depends(require_admin)):
        async def build():
            since = _since(days)
            txs = await db.cash_transactions.find({"date": {"$gte": since}}, {"_id": 0, "type": 1, "amount": 1, "date": 1, "category": 1, "payment_method": 1, "technician_id": 1}).to_list(200000)
            jobs = await db.service_jobs.find({"status": {"$in": list(DONE)}, "completed_at": {"$gte": since}}, JOB_F).to_list(100000)
            cs, cmap = await _customers_map()
            gelir = sum(_f(t["amount"]) for t in txs if t["type"] == "gelir")
            gider = sum(_f(t["amount"]) for t in txs if t["type"] == "gider")
            prim = sum(_f(t["amount"]) for t in txs if t["type"] == "teknisyen_prim")
            cat = Counter()
            for t in txs:
                if t["type"] == "gider":
                    cat[t.get("category") or "Diğer"] += _f(t["amount"])
            pm = Counter()
            for t in txs:
                if t["type"] == "gelir":
                    pm[t.get("payment_method") or "—"] += _f(t["amount"])
            rev = sum(_f(j.get("total_amount")) for j in jobs)
            coll = sum(_f(j.get("collected_amount"), _f(j.get("total_amount"))) if j.get("payment_status") != "veresiye" else _f(j.get("collected_amount")) for j in jobs)
            monthly = defaultdict(lambda: {"gelir": 0.0, "gider": 0.0})
            for t in txs:
                m = _day(t.get("date"))[:7]
                if t["type"] in ("gelir", "gider") and m:
                    monthly[m][t["type"]] += _f(t["amount"])
            dv, cy = defaultdict(float), defaultdict(float)
            for j in jobs:
                dv[j.get("device_type") or "—"] += _f(j.get("total_amount"))
                cy[(cmap.get(j.get("customer_id")) or {}).get("city") or "—"] += _f(j.get("total_amount"))
            recv = sorted(({"job": j.get("job_number"), "customer": j.get("customer_name"), "amount": round(_f(j.get("total_amount")) - (_f(j.get("collected_amount")) if j.get("collected_amount") is not None else 0), 2),
                            "tech": j.get("assigned_technician_name") or "", "date": (j.get("completed_at") or "")[:10]} for j in jobs if j.get("payment_status") == "veresiye"), key=lambda r: -r["amount"])[:20]
            return {"days": days, "kpi": {"income": round(gelir, 2), "expense": round(gider, 2), "net": round(gelir - gider, 2), "job_revenue": round(rev, 2), "collected": round(coll, 2),
                                           "receivable": round(max(0, rev - coll), 2), "tech_share": round(prim, 2), "done": len(jobs), "avg_ticket": round(rev / len(jobs), 2) if jobs else 0},
                    "monthly": [{"name": k, "gelir": round(v["gelir"], 2), "gider": round(v["gider"], 2)} for k, v in sorted(monthly.items())][-12:],
                    "expense_cats": [{"name": k, "value": round(v, 2)} for k, v in cat.most_common(10)], "pay_methods": [{"name": k, "value": round(v, 2)} for k, v in pm.most_common(8)],
                    "by_device": [{"name": k, "value": round(v, 2)} for k, v in sorted(dv.items(), key=lambda x: -x[1])[:8]], "by_city": [{"name": k, "value": round(v, 2)} for k, v in sorted(cy.items(), key=lambda x: -x[1])[:10]],
                    "receivables": recv}
        return await _cached(("fin", days), 60, build)
