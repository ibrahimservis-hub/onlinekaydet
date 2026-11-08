"""Ek özellikler (GÜNCELLEME 150): aylık muhasebe raporu, usta hakediş özeti, KVKK veri talebi aracı, mesaj şablonları.

Yalnızca ekleme yapar; mevcut koleksiyonların şemasını değiştirmez.
KVKK silme: kişisel veriyi anonimleştirir; mali kayıtlar (kasa hareketleri) yasal saklama için kalır, kişiyle bağı kopar.
"""
import re
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from fastapi import Depends, HTTPException

import notify


def _now():
    return datetime.now(timezone.utc).isoformat()


def _digits(s):
    return "".join(ch for ch in (s or "") if ch.isdigit())


def _ph_key(s):
    d = _digits(s)
    return d[-10:] if len(d) >= 10 else d


TPL_DEFAULT = [
    {"id": "randevu", "name": "Randevu hatırlatma", "text": "Merhaba {ad}, ServisPlus randevunuz {zaman} saatindedir. Ustamız {usta} gelecektir. Takip: {link}"},
    {"id": "yolda", "name": "Usta yolda", "text": "Merhaba {ad}, ustamız {usta} yola çıktı. Takip: {link}"},
    {"id": "tamam", "name": "İş tamamlandı", "text": "Merhaba {ad}, servis işleminiz tamamlandı ({is_no}). Bizi tercih ettiğiniz için teşekkürler."},
    {"id": "teklif", "name": "Fiyat bilgisi", "text": "Merhaba {ad}, servis kaydınız ({is_no}) için fiyat bilgisini size iletmek isteriz. Detay için bu mesaja dönebilirsiniz."},
    {"id": "garanti", "name": "Garanti bilgisi", "text": "Merhaba {ad}, {is_no} numaralı servis işleminizin garanti belgesi hazırdır. Takip: {link}"},
]


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    # ============================================================ AYLIK MUHASEBE RAPORU
    @api_router.get("/reports/monthly")
    async def monthly(year: int = 0, _: dict = Depends(require_admin)):
        y = year or datetime.now(timezone.utc).year
        txs = await db.cash_transactions.find({"date": {"$gte": f"{y}-01-01", "$lt": f"{y + 1}-01-01"}}, {"_id": 0}).to_list(200000)
        months = {f"{y}-{m:02d}": {"month": f"{y}-{m:02d}", "income": 0.0, "expense": 0.0, "tech_prim": 0.0,
                                   "tech_debt": 0.0, "tech_paid": 0.0} for m in range(1, 13)}
        cats = defaultdict(float)
        for t in txs:
            mk = str(t.get("date") or "")[:7]
            if mk not in months:
                continue
            amt = float(t.get("amount", 0) or 0)
            ty = t.get("type")
            if ty == "gelir":
                months[mk]["income"] += amt
            elif ty == "gider":
                months[mk]["expense"] += amt
                cats[(t.get("category") or "Diğer")] += amt
            elif ty == "teknisyen_prim":
                months[mk]["tech_prim"] += amt
            elif ty == "teknisyen_borc":
                months[mk]["tech_debt"] += amt
            elif ty == "teknisyen_odeme":
                months[mk]["tech_paid"] += amt
        rows = []
        for mk in sorted(months):
            r = months[mk]
            r["net"] = r["income"] - r["expense"] - r["tech_prim"]
            rows.append({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
        tot = {k: round(sum(r[k] for r in rows), 2) for k in ("income", "expense", "tech_prim", "tech_debt", "tech_paid", "net")}
        return {"year": y, "months": rows, "total": tot,
                "expense_categories": sorted(({"category": k, "amount": round(v, 2)} for k, v in cats.items()), key=lambda x: -x["amount"])}

    # ============================================================ USTA HAKEDİŞ ÖZETİ
    @api_router.get("/reports/tech-payouts")
    async def payouts(date_from: str = "", date_to: str = "", _: dict = Depends(require_admin)):
        q = {}
        if date_from or date_to:
            q["date"] = {}
            if date_from:
                q["date"]["$gte"] = date_from
            if date_to:
                q["date"]["$lte"] = date_to + "T99"
        txs = await db.cash_transactions.find(q, {"_id": 0}).to_list(200000)
        techs = {u["id"]: u for u in await db.users.find({"role": "technician"}, {"_id": 0, "password_hash": 0}).to_list(2000)}
        agg = defaultdict(lambda: {"jobs": set(), "revenue": 0.0, "prim": 0.0, "debt": 0.0, "paid": 0.0})
        for t in txs:
            tid = t.get("technician_id")
            if not tid:
                continue
            a = agg[tid]
            amt = float(t.get("amount", 0) or 0)
            ty = t.get("type")
            if ty == "teknisyen_prim":
                a["prim"] += amt
                if t.get("job_id"):
                    a["jobs"].add(t["job_id"])
            elif ty == "teknisyen_borc":
                a["debt"] += amt
            elif ty == "teknisyen_odeme":
                a["paid"] += amt
            elif ty == "gelir" and t.get("job_id"):
                a["revenue"] += amt
                a["jobs"].add(t["job_id"])
        rows = []
        for tid, a in agg.items():
            rows.append({"id": tid, "name": (techs.get(tid) or {}).get("name", "(silinmiş usta)"), "jobs": len(a["jobs"]),
                         "revenue": round(a["revenue"], 2), "prim": round(a["prim"], 2), "debt": round(a["debt"], 2),
                         "paid": round(a["paid"], 2), "balance": round(a["debt"] - a["paid"], 2)})
        rows.sort(key=lambda r: -r["prim"])
        return {"rows": rows, "total": {k: round(sum(r[k] for r in rows), 2) for k in ("jobs", "revenue", "prim", "debt", "paid", "balance")}}

    # ============================================================ KVKK
    async def _find_customers(q):
        q = (q or "").strip()
        if len(q) < 3:
            return []
        out, seen = [], set()
        rx = {"$regex": re.escape(q), "$options": "i"}
        k = _ph_key(q)
        conds = [{"name": rx}, {"email": rx}]
        if len(k) >= 7:
            conds.append({"phone": {"$regex": re.escape(k) + "$"}})
        async for c in db.customers.find({"$or": conds}, {"_id": 0}).limit(25):
            if c["id"] not in seen:
                seen.add(c["id"])
                out.append(c)
        return out

    async def _bundle(c):
        jobs = await db.service_jobs.find({"customer_id": c["id"]}, {"_id": 0, "workshop": 0}).to_list(5000)
        devs = await db.devices.find({"customer_id": c["id"]}, {"_id": 0}).to_list(2000)
        k = _ph_key(c.get("phone"))
        msgs = await db.contact_messages.find({"phone": {"$regex": re.escape(k) + "$"}} if k else {"_none": 1}, {"_id": 0, "ip": 0, "ua": 0}).to_list(2000)
        orders = await db.shop_orders.find({"phone_key": k} if k else {"_none": 1}, {"_id": 0}).to_list(2000)
        accts = await db.customer_accounts.find({"phone_key": k} if k else {"_none": 1}, {"_id": 0, "password_hash": 0}).to_list(50)
        return {"musteri": c, "cihazlar": devs, "servis_kayitlari": jobs, "mesajlar": msgs, "siparisler": orders, "hesaplar": accts}

    @api_router.get("/security/kvkk/search")
    async def kvkk_search(q: str = "", _: dict = Depends(require_admin)):
        res = []
        for c in await _find_customers(q):
            res.append({"id": c["id"], "name": c.get("name", ""), "phone": c.get("phone", ""), "email": c.get("email", ""),
                        "jobs": await db.service_jobs.count_documents({"customer_id": c["id"]}),
                        "devices": await db.devices.count_documents({"customer_id": c["id"]})})
        return {"results": res}

    @api_router.get("/security/kvkk/export/{cid}")
    async def kvkk_export(cid: str, user: dict = Depends(require_admin)):
        c = await db.customers.find_one({"id": cid}, {"_id": 0})
        if not c:
            raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
        await db.kvkk_log.insert_one({"id": str(uuid.uuid4()), "action": "export", "customer_id": cid, "by": user.get("name", ""), "at": _now()})
        return await _bundle(c)

    @api_router.post("/security/kvkk/erase/{cid}")
    async def kvkk_erase(cid: str, payload: dict, user: dict = Depends(require_admin)):
        if str(payload.get("confirm", "")).strip().upper() != "SİL" and str(payload.get("confirm", "")).strip().upper() != "SIL":
            raise HTTPException(status_code=400, detail="Onay için SİL yazın")
        c = await db.customers.find_one({"id": cid}, {"_id": 0})
        if not c:
            raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
        k = _ph_key(c.get("phone"))
        anon = {"customer_name": "Silindi (KVKK)", "customer_phone": "", "customer_address": "", "customer_email": ""}
        r1 = await db.service_jobs.update_many({"customer_id": cid}, {"$set": anon, "$unset": {"workshop.signature": "", "workshop.delivery_signature": ""}})
        r2 = await db.devices.delete_many({"customer_id": cid})
        r3 = await db.contact_messages.delete_many({"phone": {"$regex": re.escape(k) + "$"}}) if k else None
        r4 = await db.customer_accounts.delete_many({"phone_key": k}) if k else None
        r5 = await db.shop_orders.update_many({"phone_key": k}, {"$set": {"customer_name": "Silindi (KVKK)", "phone": "", "address": "", "email": ""}}) if k else None
        await db.customers.delete_one({"id": cid})
        await db.kvkk_log.insert_one({"id": str(uuid.uuid4()), "action": "erase", "customer_id": cid, "by": user.get("name", ""), "at": _now(),
                                      "jobs_anonymized": r1.modified_count, "devices_deleted": r2.deleted_count})
        return {"ok": True, "jobs_anonymized": r1.modified_count, "devices_deleted": r2.deleted_count,
                "messages_deleted": getattr(r3, "deleted_count", 0), "accounts_deleted": getattr(r4, "deleted_count", 0),
                "orders_anonymized": getattr(r5, "modified_count", 0)}

    @api_router.get("/security/kvkk/log")
    async def kvkk_log(_: dict = Depends(require_admin)):
        return await db.kvkk_log.find({}, {"_id": 0}).sort("at", -1).to_list(100)

    # ============================================================ MESAJ ŞABLONLARI
    async def _tpls():
        s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0, "msg_templates": 1}) or {}
        return s.get("msg_templates") or TPL_DEFAULT

    @api_router.get("/msg-templates")
    async def tpl_get(_: dict = Depends(require_admin)):
        return {"templates": await _tpls(), "vars": ["ad", "usta", "link", "is_no", "zaman", "adres"]}

    @api_router.put("/msg-templates")
    async def tpl_put(payload: dict, _: dict = Depends(require_admin)):
        out = []
        for t in (payload.get("templates") or [])[:30]:
            name, text = str(t.get("name", "")).strip()[:60], str(t.get("text", "")).strip()[:600]
            if name and text:
                out.append({"id": str(t.get("id") or uuid.uuid4().hex[:8])[:24], "name": name, "text": text})
        await db.app_settings.update_one({"_id": "global"}, {"$set": {"msg_templates": out or TPL_DEFAULT}}, upsert=True)
        return {"templates": out or TPL_DEFAULT}

    @api_router.post("/msg-templates/render")
    async def tpl_render(payload: dict, _: dict = Depends(require_admin)):
        job = await db.service_jobs.find_one({"id": payload.get("job_id")}, {"_id": 0, "workshop": 0})
        if not job:
            raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
        tpl = next((t for t in await _tpls() if t["id"] == payload.get("template_id")), None)
        if not tpl:
            raise HTTPException(status_code=404, detail="Şablon bulunamadı")
        base = ((await notify.get_settings(db)).get("customer") or {}).get("base_url") or "https://bayi.servisplus.net.tr"
        link = base.rstrip("/") + "/takip/" + job["track_token"] if job.get("track_token") else ""
        text = notify.render(tpl["text"], {"ad": (job.get("customer_name") or "").split(" ")[0], "usta": job.get("assigned_technician_name", ""),
                                           "link": link, "is_no": job.get("job_number", ""), "zaman": str(job.get("scheduled_at") or "")[:16].replace("T", " "),
                                           "adres": job.get("customer_address", "")})
        return {"text": text, "phone": job.get("customer_phone", "")}

    @api_router.post("/msg-templates/send")
    async def tpl_send(payload: dict, user: dict = Depends(require_admin)):
        r = await tpl_render(payload, user)
        ch = payload.get("channel") if payload.get("channel") in ("sms", "whatsapp") else "sms"
        txt = str(payload.get("text") or r["text"])[:1000]
        if not notify.norm_msisdn(r["phone"]):
            raise HTTPException(status_code=400, detail="Geçerli telefon yok")
        return await notify.send(db, ch, r["phone"], txt, kind="manual_tpl", ref=str(payload.get("job_id")))
