"""Operasyon+ modülü: otomatik usta atama (aç/kapa), alacak (tahsilat) takibi + ödeme hatırlatma,
günlük patron özeti, cihaza göre kontrol listeleri, cihaz QR etiketi + herkese açık cihaz sayfası.

Alacak takibi bir İZLEME katmanıdır: servis geliri kasaya iş tamamlanınca tahakkuk olarak işlenmeye devam eder;
`payment` alanı yoksa iş "ödendi" sayılır (eski kayıtlar bozulmaz).
"""
import io
import re
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta, date

from fastapi import Depends, HTTPException, Request
from fastapi.responses import Response

import governance
import notify

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                     # pragma: no cover
    TR = timezone(timedelta(hours=3))

DONE = ("tamamlandi", "faturalandi")
OPEN_ST = ("yeni", "atandi", "yolda", "basladi")

AUTO_DEFAULT = {"enabled": False, "mode": "auto", "require_region": False, "require_skill": False, "max_daily": 6,
                "job_minutes": 90, "weights": {"region": 35, "skill": 25, "load": 25, "rating": 15}}
REM_DEFAULT = {"enabled": False, "first_after_days": 1, "repeat_days": 7, "max_reminders": 3,
               "template": "Merhaba {ad}, {is_no} numaralı servis işinize ait {tutar} ödemeniz görünmüyor. Bilgi için: {tel}", "last_run": ""}
BRIEF_DEFAULT = {"enabled": False, "hour": 8, "last_sent_day": ""}


def _id():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc).isoformat()


def _f(x, d=0.0):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return d


def _d(s):
    return (s or "")[:10]


def _tr_day(s):
    """ISO zaman damgasını (UTC) İstanbul gününe çevirir; düz tarihse olduğu gibi döner."""
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


def _today():
    return datetime.now(TR).date()


def _parse_local(s):
    try:
        return datetime.fromisoformat((s or "").replace("Z", "")[:16])
    except ValueError:
        return None


_GRP_DEV = {"kombi": ["kombi"], "klima": ["klima"], "sofben": ["sofben"], "televizyon": ["tv", "televizyon"],
            "beyaz-esya": ["buzdolabi", "camasir", "bulasik", "kurutma", "firin", "beyaz-esya"], "ocak-firin": ["firin", "ocak"], "diger": ["diger"]}


def _norm(s):
    return (s or "").strip().lower().replace("İ", "i").replace("I", "ı")


async def _cfg(db, key, default):
    d = await db.app_settings.find_one({"_id": key}, {"_id": 0}) or {}
    out = {**default, **d}
    for k, v in default.items():
        if isinstance(v, dict):
            out[k] = {**v, **(d.get(k) or {})}
    return out


# ============================================================== OTOMATİK ATAMA
async def rank_technicians(db, job: dict, cfg: dict = None):
    cfg = cfg or await _cfg(db, "autoassign", AUTO_DEFAULT)
    W = cfg["weights"]
    techs = await db.users.find({"role": "technician", "is_active": {"$ne": False}}, {"_id": 0, "password_hash": 0}).to_list(500)
    profiles = {p["technician_id"]: p for p in await db.tech_profiles.find({}, {"_id": 0}).to_list(500)}
    cust = await db.customers.find_one({"id": job.get("customer_id")}, {"_id": 0}) or {}
    district = _norm(job.get("_district") or cust.get("district"))
    city = _norm(job.get("_city") or cust.get("city"))
    addr = _norm(job.get("customer_address") or job.get("_address"))
    dtype = _norm(job.get("device_type"))
    start = _parse_local(job.get("scheduled_at"))
    day = start.date().isoformat() if start else _today().isoformat()
    since = (_today() - timedelta(days=90)).isoformat()
    rated = defaultdict(list)
    for j in await db.service_jobs.find({"survey.rating": {"$exists": True}, "completed_at": {"$gte": since}}, {"_id": 0, "assigned_technician_id": 1, "survey": 1}).to_list(50000):
        rated[j["assigned_technician_id"]].append(j["survey"]["rating"])
    open_jobs = await db.service_jobs.find({"status": {"$in": list(OPEN_ST)}, "assigned_technician_id": {"$nin": ["", None]}}, {"_id": 0, "assigned_technician_id": 1, "scheduled_at": 1, "id": 1}).to_list(50000)
    out = []
    for t in techs:
        p = profiles.get(t["id"], {})
        reasons, ok = [], True
        if p.get("available") is False:
            ok = False
            reasons.append("bugün müsait değil")
        mine = [j for j in open_jobs if j["id"] != job.get("id") and j["assigned_technician_id"] == t["id"]]
        today_n = sum(1 for j in mine if (j.get("scheduled_at") or "").startswith(day) or not j.get("scheduled_at"))
        cap = int(p.get("max_daily") or cfg["max_daily"])
        if today_n >= cap:
            ok = False
            reasons.append(f"günlük limit dolu ({today_n}/{cap})")
        if start:
            for j in mine:
                s = _parse_local(j.get("scheduled_at"))
                if s and abs((s - start).total_seconds()) < cfg["job_minutes"] * 60:
                    ok = False
                    reasons.append("aynı saatte başka işi var")
                    break
        up = t.get("profile") or {}                      # yönetim panelindeki "Usta detayı": il / ilçeler / servis grupları
        regions = [_norm(x) for x in list(p.get("districts", [])) + list(up.get("districts", []))]
        skills = [_norm(x) for x in list(p.get("device_types", [])) + [d for g in up.get("service_groups", []) for d in _GRP_DEV.get(g, [g])]]
        ucity = _norm(up.get("city"))
        city_hit = bool(ucity) and bool(city) and ucity == city
        district_hit = bool(regions) and bool(district) and district in regions
        region_hit = bool(regions) and (district in regions or any(r and r in addr for r in regions))
        skill_hit = bool(skills) and dtype in skills
        if ucity and city and not city_hit:               # il tutmuyorsa bölgesi dışı
            region_hit = False
            if cfg["require_region"]:
                ok = False
                reasons.append("farklı ilde")
        if cfg["require_region"] and regions and not region_hit:
            ok = False
            reasons.append("bölgesi dışında")
        if cfg["require_skill"] and skills and not skill_hit:
            ok = False
            reasons.append("bu cihaz türünde uzman değil")
        r = rated.get(t["id"], [])
        avg = sum(r) / len(r) if r else 4.0
        score = (W["region"] if region_hit else (W["region"] * 0.4 if not regions else 0)) + (W["skill"] if skill_hit else (W["skill"] * 0.4 if not skills else 0)) \
            + W["load"] * max(0.0, 1 - today_n / max(1, cap)) + W["rating"] * (avg / 5.0)
        if city_hit:
            reasons.append("aynı il")
        if region_hit:
            reasons.append("bölgesinde")
        if skill_hit:
            reasons.append("cihaz uzmanı")
        reasons.append(f"yük {today_n}/{cap}")
        reasons.append(f"puan {avg:.1f}")
        d_hit = district_hit or (region_hit and not ucity)
        warn = []                                          # yanlış atamayı önlemek için uyarılar
        if ucity and city and not city_hit:
            warn.append("il")
        elif city_hit and regions and district and not d_hit:
            warn.append("ilçe")
        if skills and dtype and not skill_hit:
            warn.append("grup")
        udist = [x for x in (up.get("districts") or []) if x]
        place = " · ".join([x for x in [up.get("city") or "", ", ".join(udist[:3]) + (f" +{len(udist) - 3}" if len(udist) > 3 else "")] if x])
        tier = 0 if (city_hit and d_hit and skill_hit) else 1 if (city_hit and d_hit) else 2 if (city_hit and skill_hit) else 3 if city_hit else 4 if skill_hit else 5
        out.append({"technician_id": t["id"], "name": t["name"], "score": round(score, 1), "eligible": ok, "load": today_n, "cap": cap, "reasons": reasons,
                    "city_hit": city_hit, "district_hit": d_hit, "skill_hit": skill_hit, "rating": round(avg, 1),
                    "place": place, "groups": list(up.get("service_groups") or []), "warn": warn, "tier": tier, "city": up.get("city") or "", "has_vehicle": bool(up.get("has_vehicle"))})
    out.sort(key=lambda x: (not x["eligible"], x["tier"], -x["score"]))
    return out


async def _tech_payment_push(db, job_id: str, job_number: str, due: float, customer: str):
    """Ödeme hatırlatması gönderildiğinde işin ustasına da push bildirimi."""
    try:
        import fieldops
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0, "assigned_technician_id": 1}) or {}
        tid = job.get("assigned_technician_id")
        if tid:
            await fieldops.push_to(db, [tid], "Ödeme hatırlatması", f"{job_number} · {customer} · {due:,.0f} ₺ kalan", f"/tech/jobs/{job_id}")
    except Exception:                                   # noqa: BLE001
        pass


async def auto_assign(db, job_id: str, apply, force: bool = False):
    """Ayar açık + mod 'auto' ise atanmamış işi en uygun ustaya atar. apply(job_id, tech_id) panelin normal atama akışını çalıştırır."""
    try:
        cfg = await _cfg(db, "autoassign", AUTO_DEFAULT)
        if not force and (not cfg["enabled"] or cfg["mode"] != "auto"):
            return None
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job or job.get("assigned_technician_id") or job.get("status") not in ("yeni",):
            return None
        ranked = await rank_technicians(db, job, cfg)
        best = next((r for r in ranked if r["eligible"]), None)
        if not best:
            return None
        await apply(job_id, best["technician_id"])
        await db.service_jobs.update_one({"id": job_id}, {"$set": {"auto_assigned": True, "auto_assign_reason": ", ".join(best["reasons"])}})
        return best
    except Exception:                                   # noqa: BLE001
        import logging
        logging.getLogger("ops2").exception("auto_assign")
        return None


# ============================================================== KONTROL LİSTESİ
async def checklist_for_job(db, job: dict, create=True):
    cl = job.get("checklist")
    if cl:
        return cl
    dt = _norm(job.get("device_type"))
    tpls = await db.checklist_templates.find({"active": {"$ne": False}}, {"_id": 0}).to_list(500)
    tpl = next((t for t in tpls if _norm(t.get("device_type")) == dt and dt), None) or next((t for t in tpls if not t.get("device_type")), None)
    if not tpl:
        return None
    cl = {"template_id": tpl["id"], "name": tpl["name"], "items": [{"id": i["id"], "text": i["text"], "required": bool(i.get("required", True)), "checked": False, "at": "", "note": ""} for i in tpl["items"]]}
    if create:
        await db.service_jobs.update_one({"id": job["id"]}, {"$set": {"checklist": cl}})
    return cl


async def checklist_missing(db, job: dict):
    cl = await checklist_for_job(db, job, create=True)
    if not cl:
        return []
    return [i["text"] for i in cl["items"] if i["required"] and not i["checked"]]


# ============================================================== PATRON ÖZETİ
async def build_brief(db):
    today = _today()
    y = (today - timedelta(days=1)).isoformat()
    jobs = await db.service_jobs.find({}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(200000)
    done_y = [j for j in jobs if j.get("status") in DONE and _tr_day(j.get("completed_at")) == y]
    new_y = [j for j in jobs if _tr_day(j.get("created_at")) == y]
    canc_y = [j for j in jobs if j.get("status") == "iptal" and _tr_day(j.get("updated_at")) == y]
    open_j = [j for j in jobs if j.get("status") in OPEN_ST]
    unassigned = [j for j in open_j if not j.get("assigned_technician_id")]
    now_local = datetime.now(TR).replace(tzinfo=None)
    late = [j for j in open_j if (_parse_local(j.get("scheduled_at")) or now_local + timedelta(days=1)) < now_local - timedelta(minutes=30)]
    bad = [j for j in jobs if (j.get("survey") or {}).get("rating", 5) <= 2 and _tr_day((j.get("survey") or {}).get("at")) == y]
    rec = await receivables_data(db)
    low = sum(1 for p in await db.spare_parts.find({"is_active": {"$ne": False}, "min_stock": {"$gt": 0}}, {"_id": 0, "stock_qty": 1, "min_stock": 1}).to_list(20000)
              if _f(p.get("stock_qty")) <= _f(p.get("min_stock")))
    exp = 0
    lim = (today + timedelta(days=30)).isoformat()
    for c in await db.certificates.find({"expires_at": {"$nin": ["", None]}}, {"_id": 0, "expires_at": 1}).to_list(5000):
        if c["expires_at"] <= lim:
            exp += 1
    b = {"date": today.isoformat(), "yesterday": y, "revenue": round(sum(_f(j.get("total_amount")) for j in done_y), 2), "done": len(done_y), "new_jobs": len(new_y),
         "cancelled": len(canc_y), "open": len(open_j), "unassigned": len(unassigned), "late": len(late), "bad_reviews": len(bad),
         "bookings_pending": await db.bookings.count_documents({"status": "bekliyor"}), "messages_new": await db.contact_messages.count_documents({"status": "yeni"}),
         "receivable_total": rec["total"], "receivable_overdue": rec["overdue"], "low_stock": low, "certs_expiring": exp}
    L = [f"ServisPlus günlük özet — {today.strftime('%d.%m.%Y')}",
         f"Dün: {b['done']} iş tamamlandı, ciro {b['revenue']:,.0f} ₺; {b['new_jobs']} yeni iş, {b['cancelled']} iptal.",
         f"Açık iş: {b['open']} (atanmamış {b['unassigned']}, geciken {b['late']})."]
    if b["bad_reviews"]:
        L.append(f"⚠ Dün {b['bad_reviews']} düşük puanlı müşteri değerlendirmesi var.")
    if b["receivable_total"]:
        L.append(f"Alacak: {b['receivable_total']:,.0f} ₺ (vadesi geçen {b['receivable_overdue']:,.0f} ₺).")
    extras = [f"{b['bookings_pending']} onay bekleyen randevu" if b["bookings_pending"] else "", f"{b['messages_new']} yeni mesaj" if b["messages_new"] else "",
              f"{b['low_stock']} ürün kritik stokta" if b["low_stock"] else "", f"{b['certs_expiring']} sertifika yaklaşıyor/bitti" if b["certs_expiring"] else ""]
    extras = [e for e in extras if e]
    if extras:
        L.append("Bekleyenler: " + ", ".join(extras) + ".")
    b["text"] = "\n".join(L)
    return b


# ============================================================== ALACAK
def _pay(job):
    p = job.get("payment") or {}
    total = _f(job.get("total_amount"))
    status = p.get("status", "odendi")
    if status == "odendi":
        return {"status": "odendi", "paid": total, "due": 0.0, "due_date": p.get("due_date", ""), "history": p.get("history", [])}
    paid = _f(p.get("paid"))
    return {"status": status, "paid": paid, "due": max(0.0, round(total - paid, 2)), "due_date": p.get("due_date", ""), "history": p.get("history", [])}


async def receivables_data(db):
    jobs = await db.service_jobs.find({"payment.status": {"$in": ["odenmedi", "kismi"]}, "status": {"$in": list(DONE)}}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(50000)
    today = _today()
    buckets = {"vadesi_gelmemis": 0.0, "0-7": 0.0, "8-30": 0.0, "31-60": 0.0, "60+": 0.0}
    rows, total, overdue = [], 0.0, 0.0
    for j in jobs:
        p = _pay(j)
        if p["due"] <= 0:
            continue
        dd = p["due_date"] or _tr_day(j.get("completed_at"))
        try:
            late = (today - date.fromisoformat(dd)).days
        except ValueError:
            late = 0
        key = "vadesi_gelmemis" if late <= 0 else "0-7" if late <= 7 else "8-30" if late <= 30 else "31-60" if late <= 60 else "60+"
        buckets[key] += p["due"]
        total += p["due"]
        overdue += p["due"] if late > 0 else 0
        rows.append({"job_id": j["id"], "job_number": j.get("job_number"), "customer_id": j.get("customer_id"), "customer": j.get("customer_name"), "phone": j.get("customer_phone"),
                     "total": _f(j.get("total_amount")), "paid": p["paid"], "due": p["due"], "due_date": dd, "days_late": max(0, late), "bucket": key,
                     "reminders": j.get("payment_reminders", 0), "status": p["status"]})
    rows.sort(key=lambda r: -r["days_late"])
    by_c = defaultdict(lambda: {"due": 0.0, "jobs": 0, "max_late": 0})
    for r in rows:
        c = by_c[(r["customer_id"], r["customer"], r["phone"])]
        c["due"] += r["due"]
        c["jobs"] += 1
        c["max_late"] = max(c["max_late"], r["days_late"])
    return {"total": round(total, 2), "overdue": round(overdue, 2), "buckets": {k: round(v, 2) for k, v in buckets.items()}, "rows": rows,
            "customers": sorted([{"customer_id": k[0], "customer": k[1], "phone": k[2], **{a: (round(b, 2) if isinstance(b, float) else b) for a, b in v.items()}} for k, v in by_c.items()], key=lambda x: -x["due"])}


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]
    assign_job = deps["assign_job"]

    # ---------------------------------------------------------- otomatik atama
    @api_router.get("/autoassign/settings")
    async def aa_get(_: dict = Depends(require_admin)):
        return await _cfg(db, "autoassign", AUTO_DEFAULT)

    @api_router.put("/autoassign/settings")
    async def aa_put(payload: dict, _: dict = Depends(require_admin)):
        cur = await _cfg(db, "autoassign", AUTO_DEFAULT)
        upd = {}
        if "enabled" in payload:
            upd["enabled"] = bool(payload["enabled"])
        if payload.get("mode") in ("auto", "suggest"):
            upd["mode"] = payload["mode"]
        for k in ("require_region", "require_skill"):
            if k in payload:
                upd[k] = bool(payload[k])
        for k, lo, hi in (("max_daily", 1, 50), ("job_minutes", 15, 480)):
            if k in payload:
                upd[k] = max(lo, min(hi, int(_f(payload[k]))))
        if isinstance(payload.get("weights"), dict):
            upd["weights"] = {k: max(0.0, min(100.0, _f(payload["weights"].get(k, cur["weights"][k])))) for k in cur["weights"]}
        await db.app_settings.update_one({"_id": "autoassign"}, {"$set": upd}, upsert=True)
        return await _cfg(db, "autoassign", AUTO_DEFAULT)

    @api_router.get("/autoassign/profiles")
    async def aa_profiles(_: dict = Depends(require_admin)):
        profs = {p["technician_id"]: p for p in await db.tech_profiles.find({}, {"_id": 0}).to_list(500)}
        out = []
        for t in await db.users.find({"role": "technician"}, {"_id": 0, "id": 1, "name": 1, "is_active": 1}).to_list(500):
            p = profs.get(t["id"], {})
            out.append({"technician_id": t["id"], "name": t["name"], "is_active": t.get("is_active", True), "districts": p.get("districts", []), "device_types": p.get("device_types", []),
                        "max_daily": p.get("max_daily", 0), "available": p.get("available", True)})
        return out

    @api_router.put("/autoassign/profiles/{tid}")
    async def aa_profile_put(tid: str, payload: dict, _: dict = Depends(require_admin)):
        def lst(v):
            if isinstance(v, str):
                v = re.split(r"[,\n]", v)
            return [str(x).strip() for x in (v or []) if str(x).strip()][:60]
        doc = {"technician_id": tid, "districts": lst(payload.get("districts")), "device_types": lst(payload.get("device_types")),
               "max_daily": max(0, int(_f(payload.get("max_daily")))), "available": bool(payload.get("available", True))}
        await db.tech_profiles.update_one({"technician_id": tid}, {"$set": doc}, upsert=True)
        return doc

    @api_router.get("/autoassign/suggest")
    async def aa_suggest(job_id: str, _: dict = Depends(require_admin)):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            raise HTTPException(404, "İş yok")
        return {"ranking": await rank_technicians(db, job)}

    @api_router.get("/autoassign/preview")
    async def aa_preview(city: str = "", district: str = "", device_type: str = "", address: str = "", customer_id: str = "", _: dict = Depends(require_admin)):
        """Henüz kaydedilmemiş iş (yeni servis formu) için il / ilçe / cihaz türüne göre usta sıralaması."""
        job = {"customer_id": customer_id, "_city": city[:60], "_district": district[:60], "_address": address[:200], "device_type": device_type[:30]}
        return {"ranking": await rank_technicians(db, job)}

    @api_router.post("/autoassign/run")
    async def aa_run(_: dict = Depends(require_admin)):
        n = 0
        for j in await db.service_jobs.find({"status": "yeni", "assigned_technician_id": {"$in": ["", None]}}, {"_id": 0, "id": 1}).to_list(500):
            if await auto_assign(db, j["id"], assign_job, force=True):
                n += 1
        return {"assigned": n}

    async def aa_hook(_db):
        cfg = await _cfg(db, "autoassign", AUTO_DEFAULT)
        if cfg["enabled"] and cfg["mode"] == "auto":
            for j in await db.service_jobs.find({"status": "yeni", "assigned_technician_id": {"$in": ["", None]}}, {"_id": 0, "id": 1}).to_list(100):
                await auto_assign(db, j["id"], assign_job)

    # ---------------------------------------------------------- alacaklar
    @api_router.get("/receivables")
    async def receivables(_: dict = Depends(require_admin)):
        return await receivables_data(db)

    @api_router.get("/receivables/settings")
    async def rec_settings(_: dict = Depends(require_admin)):
        return await _cfg(db, "receivable_reminder", REM_DEFAULT)

    @api_router.put("/receivables/settings")
    async def rec_settings_put(payload: dict, _: dict = Depends(require_admin)):
        upd = {}
        if "enabled" in payload:
            upd["enabled"] = bool(payload["enabled"])
        for k, lo, hi in (("first_after_days", 0, 60), ("repeat_days", 1, 60), ("max_reminders", 1, 10)):
            if k in payload:
                upd[k] = max(lo, min(hi, int(_f(payload[k]))))
        if "template" in payload:
            upd["template"] = str(payload["template"])[:400]
        await db.app_settings.update_one({"_id": "receivable_reminder"}, {"$set": upd}, upsert=True)
        return await _cfg(db, "receivable_reminder", REM_DEFAULT)

    @api_router.put("/receivables/jobs/{job_id}")
    async def rec_set(job_id: str, payload: dict, _: dict = Depends(require_admin)):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            raise HTTPException(404, "İş yok")
        st = payload.get("status", "odenmedi")
        if st not in ("odenmedi", "odendi", "kismi"):
            raise HTTPException(422, "Geçersiz durum")
        old = job.get("payment") or {}
        dd = _d(payload.get("due_date", old.get("due_date", "")))
        if dd:
            try:
                date.fromisoformat(dd)
            except ValueError:
                raise HTTPException(422, "Vade tarihi YYYY-AA-GG olmalı")
        paid = _f(old.get("paid")) if st != "odenmedi" else 0.0
        if st == "odendi":
            paid = _f(job.get("total_amount"))
        p = {"status": st, "paid": paid, "due_date": dd, "history": old.get("history", [])}
        await db.service_jobs.update_one({"id": job_id}, {"$set": {"payment": p}})
        return _pay({**job, "payment": p})

    @api_router.post("/receivables/jobs/{job_id}/payment")
    async def rec_pay(job_id: str, payload: dict, user: dict = Depends(require_admin)):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        amt = round(_f(payload.get("amount")), 2)
        if not job or amt <= 0:
            raise HTTPException(422, "İş ve tutar gerekli")
        p = job.get("payment") or {"status": "odenmedi", "paid": 0.0, "due_date": "", "history": []}
        total = _f(job.get("total_amount"))
        paid = round(_f(p.get("paid")) + amt, 2)
        if paid > total + 0.009:
            raise HTTPException(400, f"Tutar kalan borcu aşıyor (kalan {total - _f(p.get('paid')):.2f})")
        p = {**p, "paid": paid, "status": "odendi" if paid >= total - 0.009 else "kismi",
             "history": [*p.get("history", []), {"amount": amt, "method": str(payload.get("method", "nakit"))[:20], "at": _now(), "by": user["id"]}]}
        await db.service_jobs.update_one({"id": job_id}, {"$set": {"payment": p}})
        return _pay({**job, "payment": p})

    async def rec_hook(_db):
        cfg = await _cfg(db, "receivable_reminder", REM_DEFAULT)
        if not cfg["enabled"]:
            return
        if cfg.get("last_run") and cfg["last_run"] > (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat():
            return
        await db.app_settings.update_one({"_id": "receivable_reminder"}, {"$set": {"last_run": _now()}}, upsert=True)
        data = await receivables_data(db)
        s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        cn = await notify.get_settings(db)
        for r in data["rows"]:
            if r["days_late"] < cfg["first_after_days"] or r["reminders"] >= cfg["max_reminders"]:
                continue
            last = await db.outbox.find_one({"kind": "payment_reminder", "ref": r["job_id"], "status": "sent"}, {"_id": 0, "created_at": 1}, sort=[("created_at", -1)])
            if last and last["created_at"] > (datetime.now(timezone.utc) - timedelta(days=cfg["repeat_days"])).isoformat():
                continue
            text = notify.render(cfg["template"], {"ad": (r["customer"] or "").split(" ")[0], "is_no": r["job_number"], "tutar": f"{r['due']:,.0f} ₺", "tel": s.get("company_phone", "")})
            res = await notify.send(db, cn["customer"].get("channel", "sms"), r["phone"], text, kind="payment_reminder", ref=r["job_id"], cfg=cn)
            if res and res["status"] == "sent":
                await db.service_jobs.update_one({"id": r["job_id"]}, {"$inc": {"payment_reminders": 1}})
                await _tech_payment_push(db, r["job_id"], r["job_number"], r["due"], r["customer"] or "")

    @api_router.post("/receivables/jobs/{job_id}/remind")
    async def rec_remind(job_id: str, _: dict = Depends(require_admin)):
        data = await receivables_data(db)
        r = next((x for x in data["rows"] if x["job_id"] == job_id), None)
        if not r:
            raise HTTPException(404, "Açık alacak yok")
        cfg = await _cfg(db, "receivable_reminder", REM_DEFAULT)
        s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        text = notify.render(cfg["template"], {"ad": (r["customer"] or "").split(" ")[0], "is_no": r["job_number"], "tutar": f"{r['due']:,.0f} ₺", "tel": s.get("company_phone", "")})
        cn = await notify.get_settings(db)
        res = await notify.send(db, cn["customer"].get("channel", "sms"), r["phone"], text, kind="payment_reminder_manual", ref=job_id + ":" + _now(), cfg=cn)
        if res["status"] == "sent":
            await db.service_jobs.update_one({"id": job_id}, {"$inc": {"payment_reminders": 1}})
            await _tech_payment_push(db, job_id, r["job_number"], r["due"], r["customer"] or "")
        return {"status": res["status"], "error": res.get("error", ""), "text": text}

    # ---------------------------------------------------------- patron özeti
    @api_router.get("/brief/preview")
    async def brief_preview(_: dict = Depends(require_admin)):
        return await build_brief(db)

    @api_router.get("/brief/settings")
    async def brief_settings(_: dict = Depends(require_admin)):
        return await _cfg(db, "brief", BRIEF_DEFAULT)

    @api_router.put("/brief/settings")
    async def brief_settings_put(payload: dict, _: dict = Depends(require_admin)):
        upd = {}
        if "enabled" in payload:
            upd["enabled"] = bool(payload["enabled"])
        if "hour" in payload:
            upd["hour"] = max(0, min(23, int(_f(payload["hour"]))))
        await db.app_settings.update_one({"_id": "brief"}, {"$set": upd}, upsert=True)
        return await _cfg(db, "brief", BRIEF_DEFAULT)

    @api_router.post("/brief/send-now")
    async def brief_send(_: dict = Depends(require_admin)):
        b = await build_brief(db)
        cfg = await notify.get_settings(db)
        if not cfg["admin_alert"].get("enabled"):
            raise HTTPException(400, "Önce Yedek & Denetim → Bildirim Kanalları'nda yönetici uyarılarını açın ve telefon/e-posta girin")
        await notify.notify_owner(db, b["text"], kind="daily_brief_manual")
        return {"ok": True, "text": b["text"]}

    async def brief_hook(_db):
        cfg = await _cfg(db, "brief", BRIEF_DEFAULT)
        now = datetime.now(TR)
        if not cfg["enabled"] or now.hour < cfg["hour"] or cfg.get("last_sent_day") == now.date().isoformat():
            return
        await db.app_settings.update_one({"_id": "brief"}, {"$set": {"last_sent_day": now.date().isoformat()}}, upsert=True)
        b = await build_brief(db)
        await notify.notify_owner(db, b["text"], kind="daily_brief")

    # ---------------------------------------------------------- kontrol listeleri
    def clean_items(items):
        out = []
        for i in items or []:
            t = str(i.get("text", "")).strip()[:200] if isinstance(i, dict) else str(i).strip()[:200]
            if t:
                out.append({"id": (i.get("id") if isinstance(i, dict) and i.get("id") else _id()), "text": t, "required": bool(i.get("required", True)) if isinstance(i, dict) else True})
        return out[:60]

    @api_router.get("/checklists/templates")
    async def cl_list(_: dict = Depends(require_admin)):
        return await db.checklist_templates.find({}, {"_id": 0}).sort("name", 1).to_list(500)

    @api_router.post("/checklists/templates")
    async def cl_create(payload: dict, _: dict = Depends(require_admin)):
        name = str(payload.get("name", "")).strip()[:100]
        items = clean_items(payload.get("items"))
        if not name or not items:
            raise HTTPException(422, "Ad ve en az bir madde gerekli")
        doc = {"id": _id(), "name": name, "device_type": str(payload.get("device_type", "")).strip().lower()[:40], "items": items, "active": True, "created_at": _now()}
        await db.checklist_templates.insert_one(dict(doc))
        return doc

    @api_router.put("/checklists/templates/{tid}")
    async def cl_update(tid: str, payload: dict, _: dict = Depends(require_admin)):
        upd = {}
        if "name" in payload:
            upd["name"] = str(payload["name"])[:100]
        if "device_type" in payload:
            upd["device_type"] = str(payload["device_type"]).strip().lower()[:40]
        if "items" in payload:
            upd["items"] = clean_items(payload["items"])
        if "active" in payload:
            upd["active"] = bool(payload["active"])
        await db.checklist_templates.update_one({"id": tid}, {"$set": upd})
        return await db.checklist_templates.find_one({"id": tid}, {"_id": 0})

    @api_router.delete("/checklists/templates/{tid}")
    async def cl_delete(tid: str, _: dict = Depends(require_admin)):
        await db.checklist_templates.delete_one({"id": tid})
        return {"ok": True}

    async def own_job(job_id, user):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            raise HTTPException(404, "İş yok")
        if user["role"] == "technician" and job.get("assigned_technician_id") != user["id"]:
            raise HTTPException(403, "Bu kayda erişim yetkiniz yok")
        return job

    @api_router.get("/checklists/job/{job_id}")
    async def cl_job(job_id: str, user: dict = Depends(get_current_user)):
        job = await own_job(job_id, user)
        return {"checklist": await checklist_for_job(db, job, create=user["role"] == "technician" or job.get("status") in OPEN_ST)}

    @api_router.post("/checklists/job/{job_id}/toggle")
    async def cl_toggle(job_id: str, payload: dict, user: dict = Depends(get_current_user)):
        job = await own_job(job_id, user)
        if job.get("status") in DONE and user["role"] == "technician":
            raise HTTPException(403, "Tamamlanan iş düzenlenemez")
        cl = await checklist_for_job(db, job)
        if not cl:
            raise HTTPException(404, "Kontrol listesi yok")
        for i in cl["items"]:
            if i["id"] == payload.get("item_id"):
                i["checked"] = bool(payload.get("checked"))
                i["at"] = _now() if i["checked"] else ""
                if "note" in payload:
                    i["note"] = str(payload["note"])[:200]
        await db.service_jobs.update_one({"id": job_id}, {"$set": {"checklist": cl}})
        return {"checklist": cl}

    # ---------------------------------------------------------- QR etiket + herkese açık cihaz sayfası
    @api_router.get("/qr/devices")
    async def qr_devices(q: str = "", _: dict = Depends(require_admin)):
        custs = {c["id"]: c for c in await db.customers.find({}, {"_id": 0, "id": 1, "name": 1, "district": 1}).to_list(100000)}
        rows = []
        for d in await db.devices.find({}, {"_id": 0}).sort("created_at", -1).to_list(5000):
            c = custs.get(d.get("customer_id"), {})
            hay = _norm(" ".join([d.get("model", ""), d.get("brand_name", ""), d.get("type", ""), d.get("serial_no", ""), c.get("name", "")]))
            if q and _norm(q) not in hay:
                continue
            rows.append({"id": d["id"], "brand": d.get("brand_name", ""), "type": d.get("type", ""), "model": d.get("model", ""), "serial": d.get("serial_no", ""),
                         "customer": c.get("name", ""), "district": c.get("district", ""), "token": d.get("qr_token", "")})
            if len(rows) >= 200:
                break
        return rows

    async def ensure_token(device_id):
        d = await db.devices.find_one({"id": device_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Cihaz yok")
        tok = d.get("qr_token")
        if not tok:
            import secrets
            tok = secrets.token_urlsafe(10)
            await db.devices.update_one({"id": device_id}, {"$set": {"qr_token": tok}})
        return d, tok

    @api_router.post("/qr/devices/{device_id}/token")
    async def qr_token(device_id: str, _: dict = Depends(require_admin)):
        d, tok = await ensure_token(device_id)
        return {"token": tok}

    @api_router.get("/qr/devices/{device_id}/svg")
    async def qr_svg(device_id: str, base: str, _: dict = Depends(require_admin)):
        if not re.match(r"^https?://[\w.:-]+$", base):
            raise HTTPException(422, "base geçersiz")
        d, tok = await ensure_token(device_id)
        import segno
        buf = io.BytesIO()
        segno.make(f"{base}/cihaz/{tok}", error="m").save(buf, kind="svg", scale=6, border=2, xmldecl=False)
        return Response(buf.getvalue(), media_type="image/svg+xml")

    async def _job_device_token(job_id, user):
        """İşin cihazı için QR jetonu üretir (cihaz kaydı yoksa servis kaydından otomatik oluşturur)."""
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            raise HTTPException(404, "İş bulunamadı")
        if user.get("role") != "admin" and job.get("assigned_technician_id") != user.get("id"):
            raise HTTPException(403, "Bu işe erişiminiz yok")
        dev_id = job.get("device_id") or ""
        d = await db.devices.find_one({"id": dev_id}, {"_id": 0}) if dev_id else None
        if not d:
            d = {"id": str(uuid.uuid4()), "customer_id": job.get("customer_id", ""), "brand_id": job.get("device_brand_id", ""),
                 "brand_name": job.get("device_brand_name", ""), "brand_logo": job.get("device_brand_logo", ""),
                 "type": job.get("device_type") or "diger", "model": job.get("device_model", ""), "serial_no": job.get("device_serial", ""),
                 "install_date": "", "warranty_until": "", "notes": "Servis kaydından otomatik oluşturuldu",
                 "created_at": datetime.now(timezone.utc).isoformat()}
            await db.devices.insert_one(dict(d))
            await db.service_jobs.update_one({"id": job_id}, {"$set": {"device_id": d["id"]}})
        _, tok = await ensure_token(d["id"])
        return job, d, tok

    @api_router.get("/qr/jobs/{job_id}")
    async def qr_job_info(job_id: str, base: str, user: dict = Depends(get_current_user)):
        if not re.match(r"^https?://[\w.:-]+$", base):
            raise HTTPException(422, "base geçersiz")
        job, d, tok = await _job_device_token(job_id, user)
        return {"token": tok, "url": f"{base}/cihaz/{tok}", "brand": d.get("brand_name", ""), "model": d.get("model", ""),
                "type": d.get("type", ""), "job_number": job.get("job_number", ""), "customer": job.get("customer_name", "")}

    @api_router.get("/qr/jobs/{job_id}/png")
    async def qr_job_png(job_id: str, base: str, user: dict = Depends(get_current_user)):
        if not re.match(r"^https?://[\w.:-]+$", base):
            raise HTTPException(422, "base geçersiz")
        _, _, tok = await _job_device_token(job_id, user)
        import segno
        buf = io.BytesIO()
        segno.make(f"{base}/cihaz/{tok}", error="m").save(buf, kind="png", scale=10, border=1)
        return Response(buf.getvalue(), media_type="image/png")

    _hits = defaultdict(list)

    def rate(request, key, n, win):
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
        now = time.time()
        k = (key, ip)
        _hits[k] = [t for t in _hits[k] if now - t < win]
        if len(_hits[k]) >= n:
            raise HTTPException(429, "Çok fazla deneme")
        _hits[k].append(now)

    @api_router.get("/public/device/{token}")
    async def public_device(token: str, request: Request):
        rate(request, "dev", 60, 600)
        d = await db.devices.find_one({"qr_token": token}, {"_id": 0}) if len(token) >= 8 else None
        if not d:
            raise HTTPException(404, "Etiket geçersiz")
        s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        today = _today().isoformat()
        wu = d.get("warranty_until") or ""
        history = []
        for j in await db.service_jobs.find({"device_id": d["id"], "status": {"$in": list(DONE)}}, {"_id": 0, "completed_at": 1, "work_done": 1}).sort("completed_at", -1).to_list(8):
            history.append({"date": _d(j.get("completed_at")), "summary": (j.get("work_done") or "")[:140]})
        return {"brand": d.get("brand_name", ""), "type": d.get("type", ""), "model": d.get("model", ""), "install_date": d.get("install_date", ""), "warranty_until": wu,
                "warranty_active": bool(wu) and wu >= today, "history": history, "company": {"name": s.get("company_name", ""), "phone": s.get("company_phone", "")}}

    @api_router.post("/public/device/{token}/request")
    async def public_device_request(token: str, payload: dict, request: Request):
        rate(request, "devreq", 5, 900)
        if False and payload.get("sp_hp"):  # honeypot kapalı: tarayıcı otomatik doldurması gerçek müşteriyi engelliyordu
            return {"ok": True}
        d = await db.devices.find_one({"qr_token": token}, {"_id": 0}) if len(token) >= 8 else None
        if not d:
            raise HTTPException(404, "Etiket geçersiz")
        name = str(payload.get("name", "")).strip()[:80]
        phone = re.sub(r"\D", "", str(payload.get("phone", "")))[-10:]
        if len(name) < 2 or not re.match(r"^[2-5]\d{9}$", phone):
            raise HTTPException(422, "Invalid name or phone")
        cust = await db.customers.find_one({"id": d.get("customer_id")}, {"_id": 0}) or {}
        doc = {"id": _id(), "type": "servis_talebi", "name": name, "phone": "0" + phone, "email": "", "city": cust.get("city", ""), "district": cust.get("district", ""),
               "device_type": d.get("type", ""), "brand": d.get("brand_name", ""), "message": f"[QR etiket · {d.get('model', '')} · seri {d.get('serial_no', '')}] " + str(payload.get("fault", ""))[:600],
               "status": "yeni", "note": "", "job_id": "", "job_number": "", "source": {"channel": "qr_etiket"}, "channel": "qr_etiket", "device_id": d["id"], "page": "", "sid": "",
               "ip": "", "ua": "", "created_at": _now(), "updated_at": _now()}
        await db.contact_messages.insert_one(doc)
        try:
            await notify.notify_owner_t(db, f"QR etiketten servis talebi: {name} — {d.get('brand_name', '')} {d.get('type', '')}", kind="qr_request")
        except Exception:                               # noqa: BLE001
            pass
        return {"ok": True}

    async def hook(_db):
        for h in (aa_hook, rec_hook, brief_hook):
            try:
                await h(_db)
            except Exception:                           # noqa: BLE001
                import logging
                logging.getLogger("ops2").exception("hook")

    governance.HOOKS.append(hook)


async def ensure_indexes(db):
    await db.tech_profiles.create_index("technician_id", unique=True)
    await db.devices.create_index("qr_token")
