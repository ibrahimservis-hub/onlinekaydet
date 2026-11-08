"""Büyüme modülü: satış sonrası hatırlatma motoru, bakım paketleri/abonelik, kupon, sadakat puanı,
online randevu (+site widget), teknisyen karnesi/prim, düşük stok, rota, çakışma kontrolü,
fiyat önerisi, rakip takibi, mevsimsellik, ilçe fırsat tablosu ve reklam→iş dönüşüm/ROI raporu.

Ayarlar: app_settings {_id:"growth"}. Hatırlatma ve otomatik mesajlar yalnızca ayar AÇIKSA ve bildirim
sağlayıcısı (notify) tanımlıysa gönderilir; dedupe outbox (kind+ref) üzerinden yapılır.
"""
import json
import math
import re
import statistics
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta, date
from typing import Optional
from urllib.parse import quote

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
ADS = ("google_ads", "meta_ads", "diger_reklam")

DEFAULTS = {
    "reminders": {
        "enabled": False, "warranty_days": 30, "maintenance_months": 12, "followup_days": 3, "renewal_days": 30,
        "kinds": {"warranty": True, "maintenance": True, "followup": True, "renewal": True, "review": True},
        "templates": {
            "warranty": "Merhaba {ad}, {cihaz} cihazınızın garantisi {tarih} tarihinde bitiyor. Garanti bitmeden ücretsiz kontrol için bize ulaşın: {tel}",
            "maintenance": "Merhaba {ad}, {cihaz} cihazınızın son bakımından bu yana uzun süre geçti. Yıllık bakım için randevu alın: {tel}",
            "followup": "Merhaba {ad}, {cihaz} servisinden memnun kaldınız mı? Herhangi bir sorun olursa lütfen bize ulaşın: {tel}",
            "renewal": "Merhaba {ad}, bakım paketinizin süresi {tarih} tarihinde doluyor. Yenilemek için: {tel}",
            "review": "Merhaba {ad}, değerlendirmeniz için teşekkürler! Google'da yorum yazarsanız çok seviniriz: {link}",
        },
        "last_run": "",
    },
    "google_review_url": "",
    "loyalty": {"enabled": False, "earn_pct": 2.0, "min_redeem": 50, "enabled_at": ""},
    "booking": {"enabled": False, "start": "09:00", "end": "18:00", "slot_minutes": 120, "capacity": 0, "days_ahead": 14,
                "closed_weekdays": [6], "min_notice_hours": 3, "notice": "Randevunuz onaylanınca size dönüş yapılır.",
                "default_job_minutes": 90, "confirm_sms": True},
    "bonus": {"target_jobs": 20, "min_rating": 4.0, "tiers": [{"min_score": 80, "pct": 2.0}, {"min_score": 90, "pct": 4.0}]},
    "stock": {"notify": True},
    "pricing": {"busy_threshold": 0.8, "quiet_threshold": 0.3, "busy_uplift_pct": 8.0, "quiet_discount_pct": 5.0},
}


def _id():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc).isoformat()


def _merge(base, over):
    out = json.loads(json.dumps(base))
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _d(s):
    return (s or "")[:10]


def _f(x, d=0.0):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return d


def _med(vals):
    return float(statistics.median(vals)) if vals else 0.0


def _first(n):
    return (n or "").split(" ")[0]


def norm_phone(p):
    return re.sub(r"\D", "", p or "")[-10:]


def _hm(s, dflt=0):
    try:
        h, m = s.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return dflt


def parse_local(s):
    """'2026-10-05T14:00' (yerel) -> naive datetime; hata -> None"""
    try:
        return datetime.fromisoformat((s or "").replace("Z", "")[:16])
    except ValueError:
        return None


async def get_cfg(db) -> dict:
    d = await db.app_settings.find_one({"_id": "growth"}, {"_id": 0}) or {}
    return _merge(DEFAULTS, d)


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]
    sync_job_ledger = deps.get("sync_job_ledger")
    quick_create_job = deps.get("quick_create_job")
    tech_gate = deps.get("tech_hidden")                # async () -> bool (gece gizliliği)
    fault_cat = deps.get("fault_cat") or (lambda t: "Diğer")

    async def settings():
        return await get_cfg(db)

    # =================================================================== AYARLAR
    @api_router.get("/growth/settings")
    async def get_settings(_: dict = Depends(require_admin)):
        return await settings()

    @api_router.put("/growth/settings")
    async def put_settings(payload: dict, _: dict = Depends(require_admin)):
        cur = await settings()
        new = _merge(cur, {k: v for k, v in payload.items() if k in DEFAULTS})
        if new["loyalty"].get("enabled") and not cur["loyalty"].get("enabled"):
            new["loyalty"]["enabled_at"] = _now()
        b = new["booking"]
        b["slot_minutes"] = max(30, min(480, int(b.get("slot_minutes") or 120)))
        b["days_ahead"] = max(1, min(60, int(b.get("days_ahead") or 14)))
        b["capacity"] = max(0, int(b.get("capacity") or 0))
        await db.app_settings.update_one({"_id": "growth"}, {"$set": new}, upsert=True)
        return await settings()

    # =================================================================== MESAJ YARDIMCISI
    async def send_to(phone, text, kind, ref, cfg_n=None):
        cfg_n = cfg_n or await notify.get_settings(db)
        if not notify.norm_msisdn(phone):
            return None
        prev = await db.outbox.find_one({"kind": kind, "ref": ref}, {"_id": 0, "status": 1, "created_at": 1}, sort=[("created_at", -1)])
        if prev:
            if prev["status"] == "sent":
                return None
            if prev["created_at"] > (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat():
                return None
        return await notify.send(db, cfg_n["customer"].get("channel", "sms"), phone, text, kind=kind, ref=ref, cfg=cfg_n)

    async def company_phone():
        s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        return s.get("company_phone", "")

    # =================================================================== HATIRLATMA MOTORU
    async def build_opportunities(cfg):
        r = cfg["reminders"]
        tel = await company_phone()
        today = datetime.now(TR).date()
        out = []
        custs = {c["id"]: c for c in await db.customers.find({}, {"_id": 0}).to_list(100000)}

        def item(kind, ref, cust, device, due, extra=""):
            tpl = r["templates"].get(kind, "")
            text = notify.render(tpl, {"ad": _first(cust.get("name")), "cihaz": device or "cihazınız", "tarih": due, "tel": tel,
                                       "link": cfg.get("google_review_url", "")})
            out.append({"kind": kind, "ref": ref, "customer_id": cust.get("id"), "name": cust.get("name"), "phone": cust.get("phone"),
                        "device": device, "due": due, "text": text, "info": extra})

        if r["kinds"].get("warranty"):
            lim = today + timedelta(days=int(r["warranty_days"]))
            for d in await db.devices.find({"warranty_until": {"$gte": today.isoformat(), "$lte": lim.isoformat()}}, {"_id": 0}).to_list(20000):
                c = custs.get(d.get("customer_id"))
                if c:
                    item("warranty", f"{d['id']}:{d['warranty_until']}", c, " ".join(x for x in [d.get("brand_name"), d.get("type")] if x), d["warranty_until"],
                         "garanti bitiyor")
        jobs = await db.service_jobs.find({"status": {"$in": list(DONE)}}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(200000)
        if r["kinds"].get("maintenance"):
            last = {}
            for j in jobs:
                k = (j.get("customer_id"), j.get("device_id") or j.get("device_type") or "")
                dd = _d(j.get("completed_at") or j.get("updated_at"))
                if dd and dd > last.get(k, ("", None))[0]:
                    last[k] = (dd, j)
            cutoff = (today - timedelta(days=int(r["maintenance_months"]) * 30)).isoformat()
            for (cid, dev), (dd, j) in last.items():
                if dd <= cutoff:
                    c = custs.get(cid)
                    if c and dev:
                        due = (datetime.fromisoformat(dd).date() + timedelta(days=int(r["maintenance_months"]) * 30)).isoformat()
                        item("maintenance", f"{cid}:{dev}:{dd}", c, " ".join(x for x in [j.get("device_brand_name"), j.get("device_type")] if x), due,
                             f"son servis {dd}")
        if r["kinds"].get("followup"):
            a = (today - timedelta(days=int(r["followup_days"]) + 3)).isoformat()
            b = (today - timedelta(days=int(r["followup_days"]))).isoformat()
            for j in jobs:
                dd = _d(j.get("completed_at"))
                if dd and a <= dd <= b:
                    c = custs.get(j.get("customer_id")) or {"id": j.get("customer_id"), "name": j.get("customer_name"), "phone": j.get("customer_phone")}
                    item("followup", j["id"], c, " ".join(x for x in [j.get("device_brand_name"), j.get("device_type")] if x), dd, j.get("job_number", ""))
        if r["kinds"].get("renewal"):
            lim = (today + timedelta(days=int(r["renewal_days"]))).isoformat()
            for s in await db.subscriptions.find({"status": "aktif", "end_date": {"$lte": lim, "$gte": today.isoformat()}}, {"_id": 0}).to_list(5000):
                c = custs.get(s.get("customer_id"))
                if c:
                    item("renewal", f"{s['id']}:{s['end_date']}", c, s.get("package_name", ""), s["end_date"], "paket yenileme")
        if r["kinds"].get("review") and cfg.get("google_review_url"):
            for j in jobs:
                sv = j.get("survey") or {}
                if sv.get("rating", 0) >= 4 and _d(sv.get("at")) >= (today - timedelta(days=7)).isoformat():
                    c = custs.get(j.get("customer_id")) or {"id": j.get("customer_id"), "name": j.get("customer_name"), "phone": j.get("customer_phone")}
                    item("review", j["id"], c, "", _d(sv.get("at")), f"{sv['rating']}★ puan")
        # gönderim durumu
        sent = {(o["kind"], o["ref"]) async for o in db.outbox.find({"kind": {"$regex": "^reminder_"}, "status": "sent"}, {"_id": 0, "kind": 1, "ref": 1})}
        for o in out:
            o["sent"] = ("reminder_" + o["kind"], o["ref"]) in sent
        return out

    @api_router.get("/growth/opportunities")
    async def opportunities(_: dict = Depends(require_admin)):
        cfg = await settings()
        # hatırlatma kapalı olsa da liste görülebilsin (elle gönderim için)
        rows = await build_opportunities(cfg)
        counts = defaultdict(int)
        for o in rows:
            if not o["sent"]:
                counts[o["kind"]] += 1
        return {"items": rows, "pending": dict(counts), "auto": cfg["reminders"]["enabled"]}

    @api_router.post("/growth/opportunities/send")
    async def send_opportunities(payload: dict, _: dict = Depends(require_admin)):
        cfg = await settings()
        want = {(i.get("kind"), i.get("ref")) for i in payload.get("items", [])}
        rows = [o for o in await build_opportunities(cfg) if (o["kind"], o["ref"]) in want]
        n_ok, n_fail = 0, 0
        cn = await notify.get_settings(db)
        for o in rows:
            res = await send_to(o["phone"], o["text"], "reminder_" + o["kind"], o["ref"], cn)
            if res and res["status"] == "sent":
                n_ok += 1
            elif res:
                n_fail += 1
        return {"sent": n_ok, "failed": n_fail, "total": len(rows)}

    async def run_reminders(force=False):
        cfg = await settings()
        r = cfg["reminders"]
        if not r["enabled"]:
            return {"sent": 0}
        if not force and r.get("last_run") and r["last_run"] > (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat():
            return {"sent": 0}
        await db.app_settings.update_one({"_id": "growth"}, {"$set": {"reminders.last_run": _now()}}, upsert=True)
        cn = await notify.get_settings(db)
        n = 0
        for o in await build_opportunities(cfg):
            if o["sent"]:
                continue
            res = await send_to(o["phone"], o["text"], "reminder_" + o["kind"], o["ref"], cn)
            n += 1 if res and res["status"] == "sent" else 0
        return {"sent": n}

    @api_router.post("/growth/reminders/run")
    async def reminders_run(_: dict = Depends(require_admin)):
        return await run_reminders(force=True)

    # =================================================================== İNDİRİM (kupon + sadakat ortak)
    async def apply_discount(job_id, amount, kind, code, channel, user, note=""):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            raise HTTPException(404, "İş bulunamadı")
        if _f(job.get("discount_amount")) > 0:
            raise HTTPException(400, "Bu işte zaten indirim var; önce kaldırın")
        sub = _f(job.get("parts_total")) + _f(job.get("labor_fee"))
        amount = round(min(max(amount, 0.0), sub), 2)
        if amount <= 0:
            raise HTTPException(400, "İndirim uygulanacak tutar yok (önce parça/işçilik girin)")
        pct = _f(job.get("technician_commission_percent"))
        total = round(sub - amount, 2)
        upd = {"discount_amount": amount, "discount_kind": kind, "coupon_code": code, "coupon_channel": channel, "discount_note": note,
               "total_amount": total, "technician_commission_amount": round(total - round(total * pct / 100.0, 2), 2), "updated_at": _now()}
        await db.service_jobs.update_one({"id": job_id}, {"$set": upd})
        after = {**job, **upd}
        if sync_job_ledger:
            await sync_job_ledger(job, after, user)
        return after

    async def remove_discount(job_id, user):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job or _f(job.get("discount_amount")) <= 0:
            raise HTTPException(400, "Kaldırılacak indirim yok")
        sub = _f(job.get("parts_total")) + _f(job.get("labor_fee"))
        pct = _f(job.get("technician_commission_percent"))
        upd = {"discount_amount": 0.0, "discount_kind": "", "coupon_code": "", "coupon_channel": "", "discount_note": "", "total_amount": round(sub, 2),
               "technician_commission_amount": round(sub - round(sub * pct / 100.0, 2), 2), "updated_at": _now()}
        await db.service_jobs.update_one({"id": job_id}, {"$set": upd})
        if job.get("discount_kind") == "coupon" and job.get("coupon_code"):
            await db.coupons.update_one({"code": job["coupon_code"], "used": {"$gt": 0}}, {"$inc": {"used": -1}})
        if job.get("discount_kind") == "loyalty":
            await db.loyalty_tx.delete_many({"job_id": job_id, "kind": "redeem"})
        after = {**job, **upd}
        if sync_job_ledger:
            await sync_job_ledger(job, after, user)
        return after

    # =================================================================== KUPON
    def clean_coupon(p: dict) -> dict:
        code = re.sub(r"[^A-Z0-9_-]", "", str(p.get("code", "")).upper())[:24]
        if len(code) < 3:
            raise HTTPException(422, "Kod en az 3 karakter (harf/rakam)")
        t = p.get("type") if p.get("type") in ("percent", "amount") else "percent"
        v = max(0.0, _f(p.get("value")))
        if t == "percent" and v > 100:
            raise HTTPException(422, "Yüzde 100'den büyük olamaz")
        return {"code": code, "label": str(p.get("label", ""))[:80], "type": t, "value": v, "min_total": max(0.0, _f(p.get("min_total"))),
                "max_uses": max(0, int(_f(p.get("max_uses")))), "valid_from": _d(p.get("valid_from")), "valid_to": _d(p.get("valid_to")),
                "channel": str(p.get("channel", ""))[:40], "active": bool(p.get("active", True))}

    def coupon_problem(c, subtotal=None):
        today = datetime.now(TR).date().isoformat()
        if not c or not c.get("active"):
            return "Kupon geçersiz"
        if c.get("valid_from") and today < c["valid_from"]:
            return "Kupon henüz başlamadı"
        if c.get("valid_to") and today > c["valid_to"]:
            return "Kuponun süresi dolmuş"
        if c.get("max_uses") and c.get("used", 0) >= c["max_uses"]:
            return "Kupon kullanım limiti dolmuş"
        if subtotal is not None and subtotal < _f(c.get("min_total")):
            return f"Bu kupon en az {c['min_total']:.0f} ₺ tutarda geçerli"
        return ""

    @api_router.get("/growth/coupons")
    async def list_coupons(_: dict = Depends(require_admin)):
        return await db.coupons.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)

    @api_router.post("/growth/coupons")
    async def create_coupon(payload: dict, _: dict = Depends(require_admin)):
        doc = clean_coupon(payload)
        if await db.coupons.find_one({"code": doc["code"]}):
            raise HTTPException(400, "Bu kod zaten var")
        doc.update({"id": _id(), "used": 0, "created_at": _now()})
        await db.coupons.insert_one(dict(doc))
        return doc

    @api_router.put("/growth/coupons/{cid}")
    async def update_coupon(cid: str, payload: dict, _: dict = Depends(require_admin)):
        cur = await db.coupons.find_one({"id": cid}, {"_id": 0})
        if not cur:
            raise HTTPException(404, "Kupon yok")
        doc = clean_coupon({**cur, **payload, "code": cur["code"]})
        await db.coupons.update_one({"id": cid}, {"$set": doc})
        return {**cur, **doc}

    @api_router.delete("/growth/coupons/{cid}")
    async def delete_coupon(cid: str, _: dict = Depends(require_admin)):
        await db.coupons.delete_one({"id": cid})
        return {"ok": True}

    _hits = defaultdict(list)

    def rate(request: Request, key: str, n: int, win: int):
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
        now = time.time()
        k = (key, ip)
        _hits[k] = [t for t in _hits[k] if now - t < win]
        if len(_hits[k]) >= n:
            raise HTTPException(429, "Çok fazla deneme, biraz sonra tekrar deneyin")
        _hits[k].append(now)

    @api_router.get("/public/coupon/{code}")
    async def public_coupon(code: str, request: Request):
        rate(request, "coupon", 20, 600)
        c = await db.coupons.find_one({"code": code.upper()[:24]}, {"_id": 0})
        bad = coupon_problem(c)
        if bad:
            return {"valid": False, "message": bad}
        return {"valid": True, "type": c["type"], "value": c["value"], "label": c.get("label", ""), "min_total": c.get("min_total", 0)}

    @api_router.post("/jobs/{job_id}/coupon")
    async def job_coupon(job_id: str, payload: dict, user: dict = Depends(require_admin)):
        code = str(payload.get("code", "")).upper().strip()
        c = await db.coupons.find_one({"code": code}, {"_id": 0})
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            raise HTTPException(404, "İş bulunamadı")
        sub = _f(job.get("parts_total")) + _f(job.get("labor_fee"))
        bad = coupon_problem(c, sub)
        if bad:
            raise HTTPException(400, bad)
        amt = sub * c["value"] / 100.0 if c["type"] == "percent" else c["value"]
        after = await apply_discount(job_id, amt, "coupon", code, c.get("channel", ""), user, c.get("label", ""))
        await db.coupons.update_one({"code": code}, {"$inc": {"used": 1}})
        return {"ok": True, "discount_amount": after["discount_amount"], "total_amount": after["total_amount"]}

    @api_router.delete("/jobs/{job_id}/discount")
    async def job_discount_remove(job_id: str, user: dict = Depends(require_admin)):
        after = await remove_discount(job_id, user)
        return {"ok": True, "total_amount": after["total_amount"]}

    @api_router.get("/growth/coupons-report")
    async def coupons_report(_: dict = Depends(require_admin)):
        jobs = await db.service_jobs.find({"coupon_code": {"$nin": ["", None]}}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(50000)
        g = defaultdict(lambda: {"jobs": 0, "done": 0, "revenue": 0.0, "discount": 0.0, "channel": ""})
        ch = defaultdict(lambda: {"jobs": 0, "done": 0, "revenue": 0.0, "discount": 0.0})
        for j in jobs:
            for bucket, key in ((g, j["coupon_code"]), (ch, j.get("coupon_channel") or "kanalsız")):
                b = bucket[key]
                b["jobs"] += 1
                b["discount"] += _f(j.get("discount_amount"))
                if j.get("status") in DONE:
                    b["done"] += 1
                    b["revenue"] += _f(j.get("total_amount"))
            g[j["coupon_code"]]["channel"] = j.get("coupon_channel", "")
        rnd = lambda d: {k: ({kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in v.items()}) for k, v in d.items()}
        return {"by_coupon": [{"code": k, **v} for k, v in sorted(rnd(g).items(), key=lambda x: -x[1]["revenue"])],
                "by_channel": [{"channel": k, **v} for k, v in sorted(rnd(ch).items(), key=lambda x: -x[1]["revenue"])]}

    # =================================================================== BAKIM PAKETLERİ / ABONELİK
    @api_router.get("/growth/packages")
    async def list_packages(_: dict = Depends(require_admin)):
        return await db.service_packages.find({}, {"_id": 0}).sort("created_at", 1).to_list(200)

    @api_router.post("/growth/packages")
    async def create_package(payload: dict, _: dict = Depends(require_admin)):
        name = str(payload.get("name", "")).strip()[:80]
        if not name:
            raise HTTPException(422, "Paket adı gerekli")
        doc = {"id": _id(), "name": name, "price": max(0.0, _f(payload.get("price"))), "period_months": max(1, int(_f(payload.get("period_months")) or 12)),
               "visits": max(1, int(_f(payload.get("visits")) or 1)), "description": str(payload.get("description", ""))[:500], "active": True, "created_at": _now()}
        await db.service_packages.insert_one(dict(doc))
        return doc

    @api_router.put("/growth/packages/{pid}")
    async def update_package(pid: str, payload: dict, _: dict = Depends(require_admin)):
        upd = {k: payload[k] for k in ("name", "price", "period_months", "visits", "description", "active") if k in payload}
        if "price" in upd:
            upd["price"] = max(0.0, _f(upd["price"]))
        await db.service_packages.update_one({"id": pid}, {"$set": upd})
        return await db.service_packages.find_one({"id": pid}, {"_id": 0})

    @api_router.delete("/growth/packages/{pid}")
    async def delete_package(pid: str, _: dict = Depends(require_admin)):
        if await db.subscriptions.find_one({"package_id": pid, "status": "aktif"}):
            raise HTTPException(400, "Aktif aboneliği olan paket silinemez; pasife alın")
        await db.service_packages.delete_one({"id": pid})
        return {"ok": True}

    def add_months(d: date, m: int) -> date:
        y = d.year + (d.month - 1 + m) // 12
        mo = (d.month - 1 + m) % 12 + 1
        last = [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo - 1]
        return date(y, mo, min(d.day, last))

    @api_router.get("/growth/subscriptions")
    async def list_subscriptions(status: Optional[str] = None, _: dict = Depends(require_admin)):
        q = {"status": status} if status else {}
        rows = await db.subscriptions.find(q, {"_id": 0}).sort("end_date", 1).to_list(5000)
        today = datetime.now(TR).date()
        for r in rows:
            try:
                r["days_left"] = (date.fromisoformat(r["end_date"]) - today).days
            except Exception:
                r["days_left"] = None
            if r["status"] == "aktif" and r["days_left"] is not None and r["days_left"] < 0:
                r["status"] = "suresi_doldu"
        return rows

    @api_router.post("/growth/subscriptions")
    async def create_subscription(payload: dict, user: dict = Depends(require_admin)):
        pkg = await db.service_packages.find_one({"id": payload.get("package_id")}, {"_id": 0})
        cust = await db.customers.find_one({"id": payload.get("customer_id")}, {"_id": 0})
        if not pkg or not cust:
            raise HTTPException(404, "Paket veya müşteri bulunamadı")
        try:
            start = date.fromisoformat(_d(payload.get("start_date")) or datetime.now(TR).date().isoformat())
        except ValueError:
            raise HTTPException(422, "Geçersiz başlangıç tarihi")
        price = _f(payload.get("price_paid"), pkg["price"]) if payload.get("price_paid") not in (None, "") else pkg["price"]
        doc = {"id": _id(), "customer_id": cust["id"], "customer_name": cust["name"], "customer_phone": cust.get("phone", ""),
               "package_id": pkg["id"], "package_name": pkg["name"], "device_id": payload.get("device_id", ""),
               "start_date": start.isoformat(), "end_date": add_months(start, pkg["period_months"]).isoformat(),
               "visits_total": pkg["visits"], "visits_used": 0, "price_paid": price, "status": "aktif", "visits": [], "created_at": _now()}
        await db.subscriptions.insert_one(dict(doc))
        if price > 0 and payload.get("record_income", True):
            await db.cash_transactions.insert_one({"id": _id(), "type": "gelir", "amount": price, "date": _now(), "created_by": user["id"],
                                                   "description": f"Bakım paketi - {pkg['name']} - {cust['name']}", "category": "Bakım Paketi",
                                                   "technician_id": "", "job_id": "", "subscription_id": doc["id"]})
        return doc

    @api_router.post("/growth/subscriptions/{sid}/visit")
    async def subscription_visit(sid: str, payload: dict, _: dict = Depends(require_admin)):
        s = await db.subscriptions.find_one({"id": sid}, {"_id": 0})
        if not s or s["status"] != "aktif":
            raise HTTPException(400, "Aktif abonelik bulunamadı")
        if s["visits_used"] >= s["visits_total"]:
            raise HTTPException(400, "Paketin ziyaret hakkı bitti")
        v = {"at": _now(), "job_id": payload.get("job_id", ""), "note": str(payload.get("note", ""))[:200]}
        used = s["visits_used"] + 1
        await db.subscriptions.update_one({"id": sid}, {"$set": {"visits_used": used, "status": "aktif"}, "$push": {"visits": v}})
        return {"visits_used": used, "visits_left": s["visits_total"] - used}

    @api_router.put("/growth/subscriptions/{sid}/cancel")
    async def subscription_cancel(sid: str, _: dict = Depends(require_admin)):
        await db.subscriptions.update_one({"id": sid}, {"$set": {"status": "iptal"}})
        return {"ok": True}

    # =================================================================== SADAKAT PUANI
    async def credit_loyalty():
        cfg = await settings()
        L = cfg["loyalty"]
        if not L["enabled"]:
            return 0
        n = 0
        q = {"status": {"$in": list(DONE)}, "loyalty_done": {"$ne": True}, "completed_at": {"$gte": L.get("enabled_at") or "9999"}}
        for j in await db.service_jobs.find(q, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(5000):
            pts = int(math.floor(_f(j.get("total_amount")) * _f(L["earn_pct"]) / 100.0))
            if pts > 0 and j.get("customer_id"):
                await db.loyalty_tx.insert_one({"id": _id(), "customer_id": j["customer_id"], "points": pts, "kind": "earn", "job_id": j["id"],
                                                "note": j.get("job_number", ""), "created_at": _now()})
                n += 1
            await db.service_jobs.update_one({"id": j["id"]}, {"$set": {"loyalty_done": True}})
        return n

    async def balance(cid):
        rows = await db.loyalty_tx.find({"customer_id": cid}, {"_id": 0}).sort("created_at", -1).to_list(500)
        return sum(r["points"] for r in rows), rows

    @api_router.get("/growth/loyalty")
    async def loyalty_board(_: dict = Depends(require_admin)):
        await credit_loyalty()
        agg = defaultdict(int)
        for t in await db.loyalty_tx.find({}, {"_id": 0}).to_list(100000):
            agg[t["customer_id"]] += t["points"]
        names = {c["id"]: c for c in await db.customers.find({"id": {"$in": list(agg)}}, {"_id": 0, "id": 1, "name": 1, "phone": 1}).to_list(5000)}
        return sorted([{"customer_id": k, "name": names.get(k, {}).get("name", "?"), "phone": names.get(k, {}).get("phone", ""), "points": v}
                       for k, v in agg.items()], key=lambda x: -x["points"])[:200]

    @api_router.get("/growth/loyalty/{cid}")
    async def loyalty_customer(cid: str, _: dict = Depends(require_admin)):
        await credit_loyalty()
        b, rows = await balance(cid)
        return {"balance": b, "history": rows[:50], "min_redeem": (await settings())["loyalty"]["min_redeem"]}

    @api_router.post("/growth/loyalty/{cid}/redeem")
    async def loyalty_redeem(cid: str, payload: dict, user: dict = Depends(require_admin)):
        cfg = await settings()
        if not cfg["loyalty"]["enabled"]:
            raise HTTPException(400, "Sadakat puanı kapalı")
        await credit_loyalty()
        pts = int(_f(payload.get("points")))
        job = await db.service_jobs.find_one({"id": payload.get("job_id")}, {"_id": 0})
        if not job or job.get("customer_id") != cid:
            raise HTTPException(404, "İş bulunamadı veya müşteriye ait değil")
        b, _r = await balance(cid)
        if pts < cfg["loyalty"]["min_redeem"]:
            raise HTTPException(400, f"En az {cfg['loyalty']['min_redeem']} puan kullanılabilir")
        if pts > b:
            raise HTTPException(400, f"Yetersiz puan (bakiye {b})")
        after = await apply_discount(job["id"], float(pts), "loyalty", "", "sadakat", user, f"{pts} puan")
        used = int(after["discount_amount"])
        await db.loyalty_tx.insert_one({"id": _id(), "customer_id": cid, "points": -used, "kind": "redeem", "job_id": job["id"],
                                        "note": job.get("job_number", ""), "created_at": _now()})
        return {"ok": True, "used": used, "total_amount": after["total_amount"]}

    # =================================================================== ONLİNE RANDEVU
    async def capacity(cfg):
        if cfg["booking"]["capacity"]:
            return cfg["booking"]["capacity"]
        return max(1, await db.users.count_documents({"role": "technician", "is_active": {"$ne": False}}))

    async def slot_table(cfg, day: str):
        B = cfg["booking"]
        cap = await capacity(cfg)
        s0, s1, step = _hm(B["start"], 540), _hm(B["end"], 1080), int(B["slot_minutes"])
        jobs = await db.service_jobs.find({"scheduled_at": {"$regex": "^" + day}, "status": {"$in": list(OPEN_ST)}}, {"_id": 0, "scheduled_at": 1}).to_list(2000)
        books = await db.bookings.find({"date": day, "status": {"$in": ["bekliyor", "onaylandi"]}}, {"_id": 0, "time": 1}).to_list(2000)
        starts = [m for m in range(s0, s1, step) if m + step <= s1 or m == s0]
        used = defaultdict(int)
        for j in jobs:
            dt = parse_local(j["scheduled_at"])
            if dt:
                mm = dt.hour * 60 + dt.minute
                for st in starts:
                    if st <= mm < st + step:
                        used[st] += 1
        for b in books:
            used[_hm(b["time"])] += 1
        now = datetime.now(TR).replace(tzinfo=None)
        out = []
        for st in starts:
            t = f"{st // 60:02d}:{st % 60:02d}"
            when = datetime.fromisoformat(f"{day}T{t}")
            ok = when >= now + timedelta(hours=int(B["min_notice_hours"])) and cap - used[st] > 0
            out.append({"time": t, "free": max(0, cap - used[st]), "available": ok})
        return out

    def valid_day(cfg, day):
        B = cfg["booking"]
        try:
            d = date.fromisoformat(day)
        except ValueError:
            return False
        t = datetime.now(TR).date()
        return t <= d <= t + timedelta(days=int(B["days_ahead"])) and d.weekday() not in B["closed_weekdays"]

    @api_router.get("/public/booking/config")
    async def booking_config():
        B = (await settings())["booking"]
        t = datetime.now(TR).date()
        days = [(t + timedelta(days=i)).isoformat() for i in range(int(B["days_ahead"]) + 1)
                if (t + timedelta(days=i)).weekday() not in B["closed_weekdays"]]
        return {"enabled": B["enabled"], "notice": B["notice"], "days": days if B["enabled"] else []}

    @api_router.get("/public/booking/slots")
    async def booking_slots(date: str, request: Request):
        rate(request, "slots", 60, 600)
        cfg = await settings()
        if not cfg["booking"]["enabled"] or not valid_day(cfg, date):
            return {"slots": []}
        return {"slots": await slot_table(cfg, date)}

    @api_router.post("/public/booking")
    async def booking_create(payload: dict, request: Request):
        rate(request, "booking", 5, 900)
        if False and payload.get("sp_hp"):  # honeypot kapalı: tarayıcı otomatik doldurması gerçek müşteriyi engelliyordu
            return {"ok": True}
        cfg = await settings()
        if not cfg["booking"]["enabled"]:
            raise HTTPException(400, "Online randevu kapalı")
        name = str(payload.get("name", "")).strip()[:80]
        phone = re.sub(r"\D", "", str(payload.get("phone", "")))
        phone = phone[-10:]
        if len(name) < 2:
            raise HTTPException(422, "Lütfen adınızı yazın")
        if not re.match(r"^5\d{9}$", phone) and not re.match(r"^[2-4]\d{9}$", phone):
            raise HTTPException(422, "Lütfen geçerli bir telefon numarası girin")
        day, tm = str(payload.get("date", "")), str(payload.get("time", ""))
        if not valid_day(cfg, day):
            raise HTTPException(422, "Seçilen gün uygun değil")
        slot = next((s for s in await slot_table(cfg, day) if s["time"] == tm), None)
        if not slot or not slot["available"]:
            raise HTTPException(409, "Bu saat dolu, lütfen başka bir saat seçin")
        chan = ""
        if payload.get("sid"):
            ss = await db.visitor_sessions.find_one({"id": str(payload["sid"])[:64]}, {"_id": 0, "channel": 1})
            chan = (ss or {}).get("channel", "")
        code = str(payload.get("coupon", "")).upper().strip()[:24]
        if code:
            cp = await db.coupons.find_one({"code": code}, {"_id": 0})
            if coupon_problem(cp):
                code = ""
        doc = {"id": _id(), "name": name, "phone": phone, "city": str(payload.get("city", ""))[:60], "district": str(payload.get("district", ""))[:60],
               "device_type": str(payload.get("device_type", ""))[:40], "brand": str(payload.get("brand", ""))[:40],
               "fault": str(payload.get("fault", ""))[:600], "date": day, "time": tm, "status": "bekliyor", "coupon": code, "channel": chan,
               "job_id": "", "created_at": _now()}
        await db.bookings.insert_one(dict(doc))
        try:
            await notify.notify_owner_t(db, f"Yeni online randevu: {name} {phone} — {day} {tm} ({doc['device_type']})", kind="booking")
        except Exception:                               # noqa: BLE001
            pass
        return {"ok": True, "id": doc["id"], "message": "Randevu talebiniz alındı. Onaylandığında size dönüş yapacağız."}

    @api_router.get("/growth/bookings")
    async def list_bookings(status: Optional[str] = None, _: dict = Depends(require_admin)):
        q = {"status": status} if status else {}
        return await db.bookings.find(q, {"_id": 0}).sort([("date", 1), ("time", 1)]).to_list(2000)

    @api_router.put("/growth/bookings/{bid}")
    async def update_booking(bid: str, payload: dict, _: dict = Depends(require_admin)):
        b = await db.bookings.find_one({"id": bid}, {"_id": 0})
        if not b:
            raise HTTPException(404, "Randevu yok")
        st = payload.get("status")
        if st not in ("bekliyor", "onaylandi", "iptal", "tamamlandi"):
            raise HTTPException(422, "Geçersiz durum")
        await db.bookings.update_one({"id": bid}, {"$set": {"status": st, "updated_at": _now()}})
        cfg = await settings()
        if st == "onaylandi" and cfg["booking"]["confirm_sms"] and b["status"] != "onaylandi":
            cn = await notify.get_settings(db)
            tel = await company_phone()
            await send_to(b["phone"], f"Merhaba {_first(b['name'])}, {b['date']} {b['time']} randevunuz onaylandı. Bilgi: {tel}", "booking_confirm", bid, cn)
        return {**b, "status": st}

    @api_router.post("/growth/bookings/{bid}/convert")
    async def convert_booking(bid: str, payload: dict, user: dict = Depends(require_admin)):
        b = await db.bookings.find_one({"id": bid}, {"_id": 0})
        if not b:
            raise HTTPException(404, "Randevu yok")
        if b.get("job_id"):
            raise HTTPException(400, "Zaten iş emrine çevrildi")
        if not quick_create_job:
            raise HTTPException(500, "Yapılandırma eksik")
        job = await quick_create_job({
            "customer_name": b["name"], "customer_phone": b["phone"], "customer_city": b.get("city", ""), "customer_district": b.get("district", ""),
            "device_type": b.get("device_type", ""), "device_brand_name": b.get("brand", ""),
            "fault_description": b.get("fault") or "Online randevu", "scheduled_at": f"{b['date']}T{b['time']}",
            "assigned_technician_id": payload.get("technician_id", ""), "source_channel": b.get("channel") or "web_randevu",
            "source_detail": "online randevu"}, user)
        await db.bookings.update_one({"id": bid}, {"$set": {"job_id": job["id"], "status": "onaylandi", "updated_at": _now()}})
        if b.get("coupon"):
            await db.service_jobs.update_one({"id": job["id"]}, {"$set": {"pending_coupon": b["coupon"]}})
        return {"ok": True, "job_id": job["id"], "job_number": job.get("job_number")}

    @api_router.get("/public/booking-widget.js")
    async def booking_widget():
        js = r"""(function(){
var s=document.currentScript,api=(s&&s.getAttribute('data-api'))||((s&&s.src)?s.src.replace(/\/public\/booking-widget\.js.*$/,''):'/api');
var root=document.getElementById('servisplus-randevu');if(!root)return;
function el(t,a,h){var e=document.createElement(t);for(var k in (a||{}))e.setAttribute(k,a[k]);if(h!=null)e.textContent=h;return e}
function get(u){return fetch(api+u).then(function(r){return r.json()})}
function post(u,b){return fetch(api+u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error(typeof j.detail==='string'?j.detail:'Hata');return j})})}
var T={tr:{off:'Online randevu şu an kapalı.',name:'Ad Soyad',phone:'Telefon',dist:'İlçe',day:'Gün seçin',fault:'Arıza / not',coupon:'Kupon kodu (varsa)',btn:'Randevu Talep Et',ok:'Randevu talebiniz alındı. Onaylandığında size dönüş yapacağız.',fail:'Randevu servisine ulaşılamadı.',pick:'Lütfen gün ve saat seçin.'},
en:{off:'Online booking is currently closed.',name:'Full name',phone:'Phone',dist:'District',day:'Choose a day',fault:'Fault / note',coupon:'Coupon code (optional)',btn:'Request Appointment',ok:'Your request has been received. We will confirm shortly.',fail:'Booking service is unreachable.',pick:'Please choose a day and time.'},
ar:{off:'الحجز عبر الإنترنت مغلق حالياً.',name:'الاسم الكامل',phone:'الهاتف',dist:'الحي',day:'اختر يوماً',fault:'العطل / ملاحظة',coupon:'رمز الخصم (اختياري)',btn:'اطلب موعداً',ok:'تم استلام طلبك وسنؤكد الموعد قريباً.',fail:'تعذر الوصول إلى خدمة الحجز.',pick:'يرجى اختيار اليوم والوقت.'}};
var lg=(s&&s.getAttribute('data-lang'))||(navigator.language||'tr').slice(0,2);var L=T[lg]||T.tr;
var box=el('div',{style:'font-family:inherit;max-width:460px;border:1px solid #e2e8f0;border-radius:12px;padding:16px;background:#fff'});root.appendChild(box);if(lg==='ar')box.setAttribute('dir','rtl');
get('/public/booking/config').then(function(c){
 if(!c.enabled){box.textContent=L.off;return}
 var f={};function inp(label,key,type){var w=el('div',{style:'margin-bottom:10px'});w.appendChild(el('label',{style:'display:block;font-size:13px;margin-bottom:3px'},label));var i=el(type==='area'?'textarea':'input',{style:'width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:8px;box-sizing:border-box'});if(type&&type!=='area')i.type=type;i.oninput=function(){f[key]=i.value};w.appendChild(i);box.appendChild(w);return i}
 inp(L.name,'name');inp(L.phone,'phone','tel');inp(L.dist,'district');
 var dsel=el('select',{style:'width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:8px;margin-bottom:10px'});dsel.appendChild(el('option',{value:''},L.day));
 c.days.forEach(function(d){dsel.appendChild(el('option',{value:d},d))});box.appendChild(dsel);
 var slots=el('div',{style:'display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px'});box.appendChild(slots);
 dsel.onchange=function(){f.date=dsel.value;f.time='';slots.innerHTML='';if(!dsel.value)return;get('/public/booking/slots?date='+dsel.value).then(function(r){r.slots.forEach(function(s){var b=el('button',{type:'button',style:'padding:6px 10px;border-radius:8px;border:1px solid #94a3b8;background:'+(s.available?'#fff':'#f1f5f9')+';cursor:'+(s.available?'pointer':'not-allowed')},s.time);b.disabled=!s.available;b.onclick=function(){f.time=s.time;Array.prototype.forEach.call(slots.children,function(x){x.style.background='#fff'});b.style.background='#dbeafe'};slots.appendChild(b)})})};
 inp(L.fault,'fault','area');inp(L.coupon,'coupon');
 box.appendChild(el('input',{type:'text',name:'sp_hp',tabindex:'-1',autocomplete:'off',style:'position:absolute;left:-9999px'}));
 var msg=el('div',{style:'font-size:13px;margin:8px 0'});var btn=el('button',{type:'button',style:'padding:10px 16px;border:0;border-radius:8px;background:#2563eb;color:#fff;font-weight:600;cursor:pointer'},L.btn);
 btn.onclick=function(){msg.textContent='';btn.disabled=true;post('/public/booking',f).then(function(r){msg.style.color='#047857';msg.textContent=L.ok}).catch(function(e){msg.style.color='#b91c1c';msg.textContent=e.message;btn.disabled=false})};
 box.appendChild(btn);box.appendChild(msg);if(c.notice)box.appendChild(el('div',{style:'font-size:12px;color:#64748b'},c.notice));
}).catch(function(){box.textContent=L.fail});
})();"""
        return Response(js, media_type="application/javascript", headers={"Cache-Control": "public, max-age=300", "Access-Control-Allow-Origin": "*"})

    # =================================================================== ÇAKIŞMA + ROTA
    @api_router.get("/growth/conflicts")
    async def conflicts(technician_id: str, start: str, duration: int = 0, exclude_job: str = "", _: dict = Depends(get_current_user)):
        cfg = await settings()
        dur = duration or int(cfg["booking"]["default_job_minutes"])
        a = parse_local(start)
        if not a or not technician_id:
            return {"conflicts": []}
        b = a + timedelta(minutes=dur)
        out = []
        day = a.date().isoformat()
        q = {"assigned_technician_id": technician_id, "status": {"$in": list(OPEN_ST)}, "scheduled_at": {"$regex": "^" + day}}
        for j in await db.service_jobs.find(q, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(500):
            if j["id"] == exclude_job:
                continue
            s = parse_local(j.get("scheduled_at"))
            if s and s < b and s + timedelta(minutes=dur) > a:
                out.append({"type": "job", "id": j["id"], "label": f"{j.get('job_number')} · {j.get('customer_name')}", "at": j["scheduled_at"]})
        for ap in await db.appointments.find({"technician_id": technician_id, "start_at": {"$regex": "^" + day}}, {"_id": 0}).to_list(500):
            s = parse_local(ap.get("start_at"))
            e = parse_local(ap.get("end_at")) or (s + timedelta(minutes=dur) if s else None)
            if s and e and s < b and e > a:
                out.append({"type": "appointment", "id": ap["id"], "label": ap.get("title", "Randevu"), "at": ap["start_at"]})
        return {"conflicts": out, "duration": dur}

    @api_router.get("/growth/route")
    async def route(date: Optional[str] = None, technician_id: Optional[str] = None, user: dict = Depends(get_current_user)):
        day = date or datetime.now(TR).date().isoformat()
        if user["role"] == "technician":
            technician_id = user["id"]
            if tech_gate and await tech_gate():
                return {"date": day, "stops": [], "maps_url": ""}
        elif user["role"] != "admin":
            raise HTTPException(403, "Yetkisiz")
        q = {"scheduled_at": {"$regex": "^" + day}, "status": {"$in": list(OPEN_ST)}}
        if technician_id:
            q["assigned_technician_id"] = technician_id
        jobs = await db.service_jobs.find(q, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).sort("scheduled_at", 1).to_list(200)
        stops = [{"job_id": j["id"], "job_number": j.get("job_number"), "time": (j.get("scheduled_at") or "")[11:16], "customer": j.get("customer_name"),
                  "address": j.get("customer_address", ""), "status": j.get("status"), "technician": j.get("assigned_technician_name", "")} for j in jobs]
        addr = [quote(s["address"]) for s in stops if s["address"]]
        url = ""
        if addr:
            url = "https://www.google.com/maps/dir/?api=1&travelmode=driving&destination=" + addr[-1]
            if len(addr) > 1:
                url += "&waypoints=" + quote("|".join(s["address"] for s in stops[:-1] if s["address"][:1]), safe="")[:1800]
        return {"date": day, "stops": stops, "maps_url": url}

    # =================================================================== KARNE + PRİM
    async def scorecards(month: str, cfg):
        a = month + "-01"
        y, m = int(month[:4]), int(month[5:7])
        b = add_months(date(y, m, 1), 1).isoformat()
        techs = await db.users.find({"role": "technician"}, {"_id": 0, "password_hash": 0}).to_list(500)
        jobs = await db.service_jobs.find({"completed_at": {"$gte": a, "$lt": b}, "status": {"$in": list(DONE)}}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(50000)
        allcancel = await db.service_jobs.find({"status": "iptal", "updated_at": {"$gte": a, "$lt": b}}, {"_id": 0, "assigned_technician_id": 1}).to_list(50000)
        history = await db.service_jobs.find({"status": {"$in": list(DONE)}, "completed_at": {"$gte": (date(y, m, 1) - timedelta(days=40)).isoformat(), "$lt": b}},
                                             {"_id": 0, "id": 1, "customer_id": 1, "device_type": 1, "completed_at": 1, "assigned_technician_id": 1}).to_list(100000)
        paid = {p["technician_id"]: p for p in await db.bonus_payouts.find({"month": month}, {"_id": 0}).to_list(500)}
        B = cfg["bonus"]
        rows = []
        for t in techs:
            mine = [j for j in jobs if j.get("assigned_technician_id") == t["id"]]
            rated = [(j.get("survey") or {}).get("rating") or j.get("customer_rating") or 0 for j in mine]
            rated = [r for r in rated if r]
            avg = round(sum(rated) / len(rated), 2) if rated else 0
            rev = sum(_f(j.get("total_amount")) for j in mine)
            rep = 0
            for j in mine:
                cd = _d(j.get("completed_at"))
                lo = (date.fromisoformat(cd) - timedelta(days=30)).isoformat()
                if any(h["id"] != j["id"] and h["customer_id"] == j["customer_id"] and h.get("device_type") == j.get("device_type") and h["assigned_technician_id"] == t["id"]
                       and lo <= _d(h["completed_at"]) and h["completed_at"] < j["completed_at"] for h in history):
                    rep += 1
            mins = []
            for j in mine:
                s, e = parse_local(j.get("started_at")), parse_local(j.get("completed_at"))
                if s and e and e > s:
                    mins.append((e - s).total_seconds() / 60)
            rev_rate = rep / len(mine) if mine else 0
            rating_part = (avg / 5.0 if avg else 0.8) * 40
            score = round(rating_part + (1 - rev_rate) * 30 + min(1.0, len(mine) / max(1, B["target_jobs"])) * 30, 1) if mine else 0
            pct = 0.0
            for tier in sorted(B["tiers"], key=lambda x: x["min_score"]):
                if score >= tier["min_score"]:
                    pct = _f(tier["pct"])
            eligible = bool(mine) and (not rated or avg >= B["min_rating"])
            bonus = round(rev * pct / 100.0, 2) if eligible else 0.0
            rows.append({"technician_id": t["id"], "name": t["name"], "jobs": len(mine), "revenue": round(rev, 2), "avg_rating": avg, "rated": len(rated),
                         "repeat_jobs": rep, "repeat_rate": round(rev_rate * 100, 1), "avg_minutes": round(sum(mins) / len(mins)) if mins else 0,
                         "cancelled": sum(1 for c in allcancel if c.get("assigned_technician_id") == t["id"]), "score": score, "bonus_pct": pct if eligible else 0,
                         "bonus": bonus, "paid": bool(paid.get(t["id"])), "paid_amount": (paid.get(t["id"]) or {}).get("amount", 0)})
        return sorted(rows, key=lambda r: -r["score"])

    def month_ok(m):
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", m or ""):
            raise HTTPException(422, "Ay biçimi YYYY-AA olmalı")
        return m

    @api_router.get("/growth/scorecard")
    async def scorecard(month: Optional[str] = None, _: dict = Depends(require_admin)):
        month = month_ok(month or datetime.now(TR).strftime("%Y-%m"))
        return {"month": month, "rows": await scorecards(month, await settings())}

    @api_router.get("/growth/my-score")
    async def my_score(month: Optional[str] = None, user: dict = Depends(get_current_user)):
        month = month_ok(month or datetime.now(TR).strftime("%Y-%m"))
        rows = await scorecards(month, await settings())
        mine = next((r for r in rows if r["technician_id"] == user["id"]), None)
        return {"month": month, "me": mine, "rank": (rows.index(mine) + 1) if mine else None, "of": len(rows)}

    @api_router.post("/growth/scorecard/pay")
    async def pay_bonus(payload: dict, user: dict = Depends(require_admin)):
        month = month_ok(payload.get("month"))
        tid = payload.get("technician_id")
        if await db.bonus_payouts.find_one({"month": month, "technician_id": tid}):
            raise HTTPException(400, "Bu ay için prim zaten işlendi")
        row = next((r for r in await scorecards(month, await settings()) if r["technician_id"] == tid), None)
        if not row or row["bonus"] <= 0:
            raise HTTPException(400, "Prim hak edilmemiş")
        amount = round(_f(payload.get("amount"), row["bonus"]) if payload.get("amount") not in (None, "") else row["bonus"], 2)
        await db.cash_transactions.insert_one({"id": _id(), "type": "gider", "amount": amount, "date": _now(), "created_by": user["id"], "technician_id": tid,
                                               "job_id": "", "category": "Teknisyen Primi", "description": f"Performans primi {month} - {row['name']} (karne {row['score']})"})
        await db.bonus_payouts.insert_one({"id": _id(), "month": month, "technician_id": tid, "amount": amount, "score": row["score"], "at": _now()})
        return {"ok": True, "amount": amount}

    # =================================================================== DÜŞÜK STOK
    async def low_stock_rows():
        rows = []
        for p in await db.spare_parts.find({"is_active": {"$ne": False}, "min_stock": {"$gt": 0}}, {"_id": 0}).to_list(20000):
            if _f(p.get("stock_qty")) <= _f(p.get("min_stock")):
                rows.append({"id": p["id"], "name": p["name"], "sku": p.get("sku", ""), "stock": _f(p.get("stock_qty")), "min": _f(p.get("min_stock")),
                             "supplier": p.get("supplier", "") or "Tedarikçi belirtilmemiş", "supplier_phone": p.get("supplier_phone", ""),
                             "order_qty": max(1.0, _f(p.get("min_stock")) * 2 - _f(p.get("stock_qty"))), "cost": _f(p.get("cost"))})
        return sorted(rows, key=lambda r: (r["supplier"], r["name"]))

    @api_router.get("/growth/low-stock")
    async def low_stock(_: dict = Depends(require_admin)):
        rows = await low_stock_rows()
        by = defaultdict(list)
        for r in rows:
            by[r["supplier"]].append(r)
        groups = []
        for s, items in by.items():
            text = "Merhaba, aşağıdaki ürünler için sipariş vermek istiyoruz:\n" + "\n".join(f"- {i['name']}{' (' + i['sku'] + ')' if i['sku'] else ''}: {i['order_qty']:g} adet" for i in items)
            ph = re.sub(r"\D", "", items[0].get("supplier_phone", ""))
            groups.append({"supplier": s, "phone": items[0].get("supplier_phone", ""), "items": items, "order_text": text,
                           "wa_url": ("https://wa.me/" + ("90" + ph[-10:] if ph else "") + "?text=" + quote(text)) if ph else "https://wa.me/?text=" + quote(text),
                           "est_cost": round(sum(i["order_qty"] * i["cost"] for i in items), 2)})
        return {"count": len(rows), "groups": groups}

    async def stock_hook(_db):
        cfg = await settings()
        if not cfg["stock"]["notify"]:
            return
        today = datetime.now(TR).date().isoformat()
        if await db.outbox.find_one({"kind": "low_stock", "ref": today}):
            return
        rows = await low_stock_rows()
        if not rows:
            return
        names = ", ".join(r["name"] for r in rows[:8])
        await notify.notify_owner(db, f"Düşük stok: {len(rows)} ürün minimum seviyede/altında — {names}{'…' if len(rows) > 8 else ''}", kind="low_stock")
        await db.outbox.insert_one({"id": _id(), "channel": "marker", "to": "", "text": "low_stock marker", "kind": "low_stock", "ref": today,
                                    "status": "marker", "error": "", "created_at": _now()})

    # =================================================================== ANALİZ: fiyat, rakip, mevsim, ilçe, ROI
    @api_router.get("/growth/price-suggest")
    async def price_suggest(device_type: str = "", fault: str = "", brand: str = "", _: dict = Depends(get_current_user)):
        cfg = await settings()
        since = (datetime.now(TR).date() - timedelta(days=365)).isoformat()
        jobs = await db.service_jobs.find({"status": {"$in": list(DONE)}, "total_amount": {"$gt": 0}, "completed_at": {"$gte": since}}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(50000)
        fc = fault_cat(fault) if fault else ""
        dt = device_type.lower().strip()

        def pick(strict_brand):
            r = [j for j in jobs if (not dt or (j.get("device_type") or "").lower() == dt) and (not fc or fault_cat(j.get("fault_description")) == fc)]
            if strict_brand and brand:
                r = [j for j in r if (j.get("device_brand_name") or "").lower() == brand.lower()]
            return r
        sel, basis = pick(True), "cihaz+arıza+marka"
        if len(sel) < 3:
            sel, basis = pick(False), "cihaz+arıza"
        if len(sel) < 3 and dt:
            sel, basis = [j for j in jobs if (j.get("device_type") or "").lower() == dt], "yalnızca cihaz türü"
        vals = sorted(_f(j["total_amount"]) for j in sel)
        if not vals:
            return {"n": 0, "message": "Bu kombinasyon için geçmiş veri yok.", "basis": ""}
        q = lambda p: vals[min(len(vals) - 1, int(p * (len(vals) - 1)))]
        mid = _med(vals)
        # talep yoğunluğu: önümüzdeki 3 gün doluluk
        P = cfg["pricing"]
        cap = await capacity(cfg)
        today = datetime.now(TR).date()
        days = [(today + timedelta(days=i)).isoformat() for i in range(3)]
        busy = 0
        for d in days:
            busy += await db.service_jobs.count_documents({"scheduled_at": {"$regex": "^" + d}, "status": {"$in": list(OPEN_ST)}})
        slots_per_day = max(1, (_hm(cfg["booking"]["end"], 1080) - _hm(cfg["booking"]["start"], 540)) // int(cfg["booking"]["slot_minutes"]))
        util = busy / (cap * slots_per_day * 3)
        factor, why = 1.0, "Talep normal"
        if util >= P["busy_threshold"]:
            factor, why = 1 + P["busy_uplift_pct"] / 100.0, f"Önümüzdeki 3 gün %{util * 100:.0f} dolu: fiyat +%{P['busy_uplift_pct']:g}"
        elif util <= P["quiet_threshold"]:
            factor, why = 1 - P["quiet_discount_pct"] / 100.0, f"Önümüzdeki 3 gün %{util * 100:.0f} dolu: kampanya için -%{P['quiet_discount_pct']:g} düşünülebilir"
        comp = []
        for c in await db.competitors.find({}, {"_id": 0}).to_list(500):
            for pr in c.get("prices", []):
                if fault and fc and fault_cat(pr.get("service", "")) == fc or (dt and dt in (pr.get("service") or "").lower()):
                    comp.append(_f(pr.get("price")))
        return {"n": len(vals), "basis": basis, "low": round(q(0.25)), "median": round(mid), "high": round(q(0.75)), "suggested": round(mid * factor / 5) * 5,
                "demand_factor": round(factor, 3), "demand_reason": why, "utilization": round(util, 2),
                "competitor_median": round(_med(comp)) if comp else None, "competitor_n": len(comp)}

    @api_router.get("/growth/competitors")
    async def list_competitors(_: dict = Depends(require_admin)):
        return await db.competitors.find({}, {"_id": 0}).sort("name", 1).to_list(500)

    @api_router.post("/growth/competitors")
    async def create_competitor(payload: dict, _: dict = Depends(require_admin)):
        name = str(payload.get("name", "")).strip()[:80]
        if not name:
            raise HTTPException(422, "Rakip adı gerekli")
        doc = {"id": _id(), "name": name, "district": str(payload.get("district", ""))[:60], "url": str(payload.get("url", ""))[:200],
               "notes": str(payload.get("notes", ""))[:600], "prices": [], "created_at": _now()}
        await db.competitors.insert_one(dict(doc))
        return doc

    @api_router.put("/growth/competitors/{cid}")
    async def update_competitor(cid: str, payload: dict, _: dict = Depends(require_admin)):
        upd = {k: str(payload[k])[:600] for k in ("name", "district", "url", "notes") if k in payload}
        await db.competitors.update_one({"id": cid}, {"$set": upd})
        return await db.competitors.find_one({"id": cid}, {"_id": 0})

    @api_router.post("/growth/competitors/{cid}/price")
    async def add_competitor_price(cid: str, payload: dict, _: dict = Depends(require_admin)):
        service = str(payload.get("service", "")).strip()[:80]
        price = _f(payload.get("price"))
        if not service or price <= 0:
            raise HTTPException(422, "Hizmet ve fiyat gerekli")
        e = {"service": service, "price": price, "date": _d(payload.get("date")) or datetime.now(TR).date().isoformat(), "note": str(payload.get("note", ""))[:200]}
        await db.competitors.update_one({"id": cid}, {"$push": {"prices": e}})
        return e

    @api_router.delete("/growth/competitors/{cid}")
    async def delete_competitor(cid: str, _: dict = Depends(require_admin)):
        await db.competitors.delete_one({"id": cid})
        return {"ok": True}

    @api_router.get("/growth/competitors-compare")
    async def competitors_compare(_: dict = Depends(require_admin)):
        comps = await db.competitors.find({}, {"_id": 0}).to_list(500)
        jobs = await db.service_jobs.find({"status": {"$in": list(DONE)}, "total_amount": {"$gt": 0}}, {"_id": 0, "device_type": 1, "fault_description": 1, "total_amount": 1}).to_list(50000)
        svc = defaultdict(list)
        for c in comps:
            for p in c.get("prices", []):
                svc[p["service"].strip().lower()].append((c["name"], _f(p["price"])))
        rows = []
        for s, items in svc.items():
            cat = fault_cat(s)
            ours = [_f(j["total_amount"]) for j in jobs if (cat != "Diğer" and fault_cat(j.get("fault_description")) == cat) or (j.get("device_type") or "").lower() == s]
            comp_avg = sum(p for _, p in items) / len(items)
            mine = _med(ours)
            rows.append({"service": s, "competitors": [{"name": n, "price": p} for n, p in items], "competitor_avg": round(comp_avg), "ours": round(mine) if ours else None,
                         "our_n": len(ours), "diff_pct": round((mine - comp_avg) / comp_avg * 100, 1) if ours and comp_avg else None})
        return rows

    @api_router.get("/growth/seasonality")
    async def seasonality(_: dict = Depends(require_admin)):
        jobs = await db.service_jobs.find({}, {"_id": 0, "created_at": 1, "device_type": 1}).to_list(200000)
        ym = defaultdict(lambda: defaultdict(int))
        for j in jobs:
            k = (j.get("created_at") or "")[:7]
            if re.match(r"^\d{4}-\d{2}$", k):
                ym[j.get("device_type") or "Belirtilmemiş"][k] += 1
                ym["TOPLAM"][k] += 1
        now = datetime.now(TR).date()
        out = []
        for dt, months in ym.items():
            keys = sorted(months)
            span = (int(keys[-1][:4]) - int(keys[0][:4])) * 12 + int(keys[-1][5:]) - int(keys[0][5:]) + 1 if keys else 0
            by_moy = defaultdict(list)
            for k, v in months.items():
                by_moy[int(k[5:])].append(v)
            avg_all = sum(months.values()) / max(1, span)
            idx = {m: (sum(v) / len(v)) / avg_all if avg_all else 1 for m, v in by_moy.items()} if span >= 12 else {}
            base_months = [add_months(now.replace(day=1), -i).strftime("%Y-%m") for i in range(1, 4)]
            base = sum(months.get(k, 0) for k in base_months) / 3
            base_idx = sum(idx.get(int(k[5:]), 1) for k in base_months) / 3 if idx else 1
            deseason = base / base_idx if base_idx else base
            fc = []
            for i in range(1, 4):
                m = add_months(now.replace(day=1), i)
                fc.append({"month": m.strftime("%Y-%m"), "expected": round(deseason * idx.get(m.month, 1), 1)})
            out.append({"device_type": dt, "total": sum(months.values()), "history": [{"month": k, "jobs": months[k]} for k in keys[-18:]], "index": {str(m): round(v, 2) for m, v in sorted(idx.items())},
                        "forecast": fc, "reliable": span >= 12, "months_of_data": span})
        out.sort(key=lambda r: (r["device_type"] != "TOPLAM", -r["total"]))
        notes = []
        for r in out:
            if r["device_type"] != "TOPLAM" and r["reliable"] and r["total"] >= 20:
                top = max(r["index"].items(), key=lambda x: x[1])
                if top[1] >= 1.3:
                    notes.append(f"{r['device_type']}: en yoğun ay {int(top[0])}. ay (ortalamanın %{(top[1] - 1) * 100:.0f} üstü) — yedek parça stoğu ve reklamı 1 ay önceden artırın.")
        if out and not out[0]["reliable"]:
            notes.append("Henüz 12 aylık veri yok; mevsim endeksi hesaplanamadı, tahmin son 3 ay ortalamasına dayanıyor.")
        return {"series": out, "notes": notes}

    @api_router.get("/growth/districts")
    async def districts(_: dict = Depends(require_admin)):
        custs = {c["id"]: c for c in await db.customers.find({}, {"_id": 0}).to_list(100000)}
        g = defaultdict(lambda: {"customers": set(), "jobs": 0, "done": 0, "revenue": 0.0, "leads": 0, "unconverted": 0, "bookings": 0})

        def key(c, d):
            return ((c or "").strip().title() or "—", (d or "").strip().title() or "—")
        for j in await db.service_jobs.find({}, {"_id": 0, "customer_id": 1, "status": 1, "total_amount": 1}).to_list(200000):
            c = custs.get(j.get("customer_id"))
            if not c:
                continue
            x = g[key(c.get("city"), c.get("district"))]
            x["customers"].add(c["id"])
            x["jobs"] += 1
            if j.get("status") in DONE:
                x["done"] += 1
                x["revenue"] += _f(j.get("total_amount"))
        for m in await db.contact_messages.find({}, {"_id": 0, "city": 1, "district": 1, "job_id": 1}).to_list(100000):
            x = g[key(m.get("city"), m.get("district"))]
            x["leads"] += 1
            x["unconverted"] += 0 if m.get("job_id") else 1
        for b in await db.bookings.find({}, {"_id": 0, "city": 1, "district": 1, "job_id": 1}).to_list(100000):
            x = g[key(b.get("city"), b.get("district"))]
            x["bookings"] += 1
            x["unconverted"] += 0 if b.get("job_id") else 1
        tot_done = sum(x["done"] for x in g.values())
        avg_ticket = (sum(x["revenue"] for x in g.values()) / tot_done) if tot_done else 0
        rows = []
        for (city, dist), x in g.items():
            at = x["revenue"] / x["done"] if x["done"] else avg_ticket
            demand = x["leads"] + x["bookings"]
            opp = round(x["unconverted"] * at + (demand * 0.5 * at if x["done"] < demand else 0), 0)
            tag = "Talep var, iş az" if demand >= 3 and x["unconverted"] >= 2 else ("Güçlü bölge" if x["done"] >= 5 and at >= avg_ticket else ("Yeni/az veri" if x["jobs"] < 3 else "Normal"))
            rows.append({"city": city, "district": dist, "customers": len(x["customers"]), "jobs": x["jobs"], "done": x["done"], "revenue": round(x["revenue"], 2),
                         "avg_ticket": round(at, 2), "leads": x["leads"], "bookings": x["bookings"], "unconverted": x["unconverted"], "opportunity": opp, "tag": tag})
        return sorted(rows, key=lambda r: -r["opportunity"])

    @api_router.get("/growth/roi")
    async def roi(date_from: Optional[str] = None, date_to: Optional[str] = None, _: dict = Depends(require_admin)):
        now = datetime.now(TR)
        date_to = date_to or now.strftime("%Y-%m-%d")
        date_from = date_from or (now - timedelta(days=89)).strftime("%Y-%m-%d")
        s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        spend = (s.get("profit") or {}).get("ad_spend") or {}
        sessions = await db.visitor_sessions.find({"day": {"$gte": date_from, "$lte": date_to}}, {"_id": 0, "channel": 1, "conv_call": 1, "conv_whatsapp": 1, "conv_form": 1}).to_list(300000)
        ch = defaultdict(lambda: {"sessions": 0, "calls": 0, "whatsapp": 0, "forms": 0, "leads": 0, "jobs": 0, "done": 0, "revenue": 0.0})
        for x in sessions:
            c = ch[x.get("channel") or "bilinmiyor"]
            c["sessions"] += 1
            c["calls"] += int(x.get("conv_call") or 0)
            c["whatsapp"] += int(x.get("conv_whatsapp") or 0)
            c["forms"] += int(x.get("conv_form") or 0)
        for m in await db.contact_messages.find({"created_at": {"$gte": date_from, "$lt": date_to + "~"}}, {"_id": 0, "channel": 1}).to_list(100000):
            ch[m.get("channel") or "bilinmiyor"]["leads"] += 1
        for j in await db.service_jobs.find({"created_at": {"$gte": date_from, "$lt": date_to + "~"}}, {"_id": 0, "source_channel": 1, "status": 1, "total_amount": 1}).to_list(100000):
            c = ch[j.get("source_channel") or "belirtilmemis"]
            c["jobs"] += 1
            if j.get("status") in DONE:
                c["done"] += 1
                c["revenue"] += _f(j.get("total_amount"))
        # reklam harcaması: seçili aralığa düşen ayların payı, reklam kanalları arasında oturum sayısına göre dağıtılır
        months = set()
        d0, d1 = date.fromisoformat(date_from), date.fromisoformat(date_to)
        cur = date(d0.year, d0.month, 1)
        while cur <= d1:
            months.add(cur.strftime("%Y-%m"))
            cur = add_months(cur, 1)
        total_spend = sum(_f(spend.get(m)) for m in months)
        ad_sessions = sum(ch[k]["sessions"] for k in ADS if k in ch) or 0
        ad_jobs = sum(ch[k]["jobs"] for k in ADS if k in ch) or 0
        rows = []
        for k, v in ch.items():
            sp = 0.0
            if k in ADS and total_spend:
                sp = total_spend * (v["sessions"] / ad_sessions if ad_sessions else (v["jobs"] / ad_jobs if ad_jobs else 0))
            conv = v["calls"] + v["whatsapp"] + v["forms"]
            rows.append({"channel": k, **{a: (round(b, 2) if isinstance(b, float) else b) for a, b in v.items()}, "contacts": conv,
                         "session_to_contact_pct": round(conv / v["sessions"] * 100, 1) if v["sessions"] else 0, "spend": round(sp, 2),
                         "cost_per_contact": round(sp / conv, 2) if sp and conv else None, "cost_per_job": round(sp / v["jobs"], 2) if sp and v["jobs"] else None,
                         "roas": round(v["revenue"] / sp, 2) if sp else None})
        rows.sort(key=lambda r: -r["revenue"])
        return {"date_from": date_from, "date_to": date_to, "rows": rows, "total_spend": round(total_spend, 2),
                "note": "Reklam harcaması 'Kârlılık ayarları'ndaki aylık reklam bütçesinden gelir; kanallar arasında oturum sayısına göre paylaştırılır." if total_spend else
                "Aylık reklam harcamasını Kârlılık ayarlarına girerseniz maliyet/ROAS hesaplanır."}

    # =================================================================== ZAMANLAYICI
    async def growth_hook(_db):
        try:
            await run_reminders()
            await credit_loyalty()
            await stock_hook(_db)
        except Exception:                               # noqa: BLE001
            import logging
            logging.getLogger("growth").exception("growth_hook")

    governance.HOOKS.append(growth_hook)
    api_router.growth_run_reminders = run_reminders      # test erişimi
    api_router.growth_credit_loyalty = credit_loyalty


async def ensure_indexes(db):
    await db.coupons.create_index("code", unique=True)
    await db.bookings.create_index([("date", 1), ("time", 1)])
    await db.subscriptions.create_index("customer_id")
    await db.loyalty_tx.create_index("customer_id")
