# -*- coding: utf-8 -*-
"""Anında demo hesabı: satış sitesindeki forma ad, telefon ve sektör girilince örnek verili, 7 gün açık gerçek bir firma açılır.

Firma tam pakettedir (Kurumsal), örnek müşteri/usta/servis kaydı hazır gelir. Talep ayrıca satış listesine (leads) 'demo' olarak düşer.
"""
import json
import os
import random
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request

import firms
import sektor
import tenant

_RATE = {}
DEMO_DAYS = 7
SECTOR_MAP = {"kombi": "kombi", "klima": "klima", "beyaz eşya": "beyaz_esya", "beyaz esya": "beyaz_esya", "elektronik": "elektronik",
              "bilgisayar": "bilgisayar", "tesisat": "tesisat", "elektrik": "elektrik", "güvenlik": "guvenlik", "guvenlik": "guvenlik"}
CUSTOMERS = [("Ayşe Yıldız", "Atatürk Mah. 112. Sk. No:4/3", "Çankaya", "Ankara"), ("Mehmet Kaya", "Cumhuriyet Cd. No:27/8", "Kadıköy", "İstanbul"),
             ("Fatma Demir", "Yeni Mah. 1450 Sk. No:12", "Bornova", "İzmir"), ("Ali Çelik", "Fevzi Çakmak Cd. No:55/2", "Yenimahalle", "Ankara"),
             ("Zeynep Arslan", "Bahçelievler 7. Cd. No:9", "Nilüfer", "Bursa")]
FAULTS = {"kombi": ["Isıtmıyor, E01 hatası", "Sıcak su gelmiyor", "Petek ısınmıyor, basınç düşüyor", "Yıllık bakım"],
          "klima": ["Soğutmuyor", "İç ünite su damlatıyor", "Montaj ve ilk çalıştırma", "Gaz dolumu"],
          "beyaz_esya": ["Çamaşır makinesi su almıyor", "Buzdolabı soğutmuyor", "Bulaşık makinesi boşaltmıyor", "Fırın ısınmıyor"],
          "elektronik": ["Ekranda çizgi var", "Açılmıyor", "Ses gelmiyor", "Wi-Fi bağlanmıyor"],
          "bilgisayar": ["Açılmıyor", "Ekran kırık", "Yavaş çalışıyor", "Şarj olmuyor"],
          "tesisat": ["Musluk damlatıyor", "Gider tıkanıklığı", "Su kaçağı tespiti", "Rezervuar arızası"],
          "elektrik": ["Sigorta atıyor", "Priz çalışmıyor", "Avize montajı", "Kaçak akım rölesi"],
          "guvenlik": ["Kamera görüntü vermiyor", "Kayıt cihazı açılmıyor", "Alarm panosu arıza veriyor", "Kamera montajı"]}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _norm_phone(s):
    d = re.sub(r"\D", "", str(s or ""))
    if d.startswith("90") and len(d) == 12:
        d = d[2:]
    if d.startswith("0"):
        d = d[1:]
    return d if len(d) == 10 and d.startswith("5") else ""


def register(api_router, db, deps):
    hash_password = deps["hash_password"]

    @api_router.post("/public/demo")
    async def open_demo(payload: dict, request: Request):
        if str(payload.get("website") or "").strip():
            return {"ok": True}
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
        now = time.time()
        hist = [t for t in _RATE.get(ip, []) if now - t < 3600]
        if len(hist) >= 4:
            raise HTTPException(429, "Çok fazla deneme, biraz sonra tekrar deneyin")
        name = " ".join(str(payload.get("name") or "").split())[:80]
        phone = _norm_phone(payload.get("phone"))
        if len(name) < 2:
            raise HTTPException(422, "Lütfen adınızı yazın")
        if not phone:
            raise HTTPException(422, "Telefon numarası geçersiz (05xx xxx xx xx)")
        key = SECTOR_MAP.get(str(payload.get("sector") or "").strip().lower(), "")
        if key not in sektor.SECTORS:
            raise HTTPException(422, "Sektör seçin")
        since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        if await db.main().firms.count_documents({"demo_phone": phone, "created_at": {"$gte": since}}) >= 2:
            raise HTTPException(429, "Bu telefonla bugün demo açıldı. Giriş bilgilerinizi kaybettiyseniz bizi arayın: 0544 444 40 04")
        hist.append(now)
        _RATE[ip] = hist

        sec = sektor.SECTORS[key]
        fid = uuid.uuid4().hex[:12]
        tag = secrets.token_hex(3)
        n = await db.main().firms.count_documents({"demo": True}) + 1
        while await db.main().firms.find_one({"login_email": f"demo{n}@demo.onlinekaydet.com"}):
            n += 1
        email = f"demo{n}@demo.onlinekaydet.com"
        pw = "".join(random.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(8))
        company = f"Demo {n}"
        mods = firms.ALL_MODS
        f = {"id": fid, "db": db.firm_db_name(fid), "name": company, "login_email": email, "contact_name": name, "phone": phone, "address": "",
             "tax_no": "", "tax_office": "", "features": {}, "status": "aktif", "created_at": _now(), "logo": "",
             "expires_at": (datetime.now(timezone.utc) + timedelta(days=DEMO_DAYS)).isoformat(), "package": "kurumsal", "modules": list(mods),
             "sector": key, "demo": True, "demo_phone": phone}
        fdb = db.firm(f["db"])
        await fdb.users.insert_one({"id": str(uuid.uuid4()), "email": email, "password_hash": hash_password(pw), "name": name, "phone": phone,
                                    "role": "admin", "commission_percent": 0.0, "is_active": True, "firm_owner": True, "created_at": _now()})
        brands = await db.main().brands.find({}, {"_id": 0}).to_list(500)
        if brands:
            await fdb.brands.insert_many([dict(b) for b in brands])
        await fdb.app_settings.update_one({"_id": "global"}, {"$set": {
            "company_name": company, "company_phone": phone, "company_address": "Demo adres", "is_firm": True, "has_logo": False,
            "tech_visibility": {"enabled": False, "hide_from": "22:00", "show_from": "07:00", "done_days": 36500}}}, upsert=True)
        try:
            _th = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "themes.json"), encoding="utf-8"))
            _pick = next((t for t in _th if t.get("sector") == key.replace("_", "-") or t.get("sector") == key), None) or (_th[0] if _th else None)
            if _pick:
                await fdb.app_settings.update_one({"_id": "brand"}, {"$set": {"theme": _pick["slug"], "dark": _pick.get("dark"), "accent": _pick.get("accent"), "radius": _pick.get("radius", 12)}}, upsert=True)
        except Exception:
            pass
        await fdb.app_settings.update_one({"_id": "firm_logo"}, {"$set": {"data": ""}}, upsert=True)
        await fdb.app_settings.update_one({"_id": "firm"}, {"$set": {"firm_id": fid, "name": company, "features": {}}}, upsert=True)
        await db.main().firms.insert_one(dict(f))
        await sektor.apply(fdb, key)

        # --- örnek veri: 2 usta, 5 müşteri, cihaz, 7 servis kaydı
        techs = []
        for i, (tn, tp) in enumerate((("Hasan Demir", "05320000001"), ("Murat Kaya", "05320000002"))):
            te = f"usta{i + 1}.{tag}@demo.onlinekaydet.com"
            u = {"id": str(uuid.uuid4()), "email": te, "password_hash": hash_password(pw), "name": tn, "phone": tp, "role": "technician",
                 "commission_percent": 30.0, "is_active": True, "created_at": _now()}
            await fdb.users.insert_one(u)
            await db.main().firm_logins.insert_one({"email": te, "db": f["db"], "user_id": u["id"]})
            techs.append(u)
        br = None
        names = list(sec["brands"])
        if names:
            br = await fdb.brands.find_one({"name": names[0]}, {"_id": 0}) or await fdb.brands.find_one({}, {"_id": 0})
        else:
            br = await fdb.brands.find_one({}, {"_id": 0})
        custs = []
        for cn, ad, ilce, il in CUSTOMERS:
            c = {"id": str(uuid.uuid4()), "name": cn, "phone": "05" + "".join(random.choice("0123456789") for _ in range(9)), "address": ad,
                 "district": ilce, "city": il, "created_at": _now()}
            await fdb.customers.insert_one(c)
            custs.append(c)
        faults = FAULTS.get(key) or ["Arıza"]
        plan = [("yeni", None), ("atandi", 0), ("yolda", 0), ("basladi", 1), ("tamamlandi", 0), ("tamamlandi", 1), ("tamamlandi", 0)]
        for n, (st, ti) in enumerate(plan):
            c = custs[n % len(custs)]
            dev = None
            if br:
                dev = {"id": str(uuid.uuid4()), "customer_id": c["id"], "brand_id": br["id"], "brand_name": br["name"], "brand_logo": br.get("logo_url", ""),
                       "type": sec["type"], "model": "Örnek model", "serial_no": f"DM{n:04d}", "created_at": _now()}
                await fdb.devices.insert_one(dev)
            t = techs[ti] if ti is not None else None
            when = datetime.now(timezone.utc) - timedelta(days=(7 - n) if st == "tamamlandi" else 0, hours=-n)
            labor, parts = (450.0 + 50 * n, 300.0 + 40 * n) if st == "tamamlandi" else (0.0, 0.0)
            job = {"id": str(uuid.uuid4()), "job_number": f"DM-{1001 + n}", "customer_id": c["id"], "customer_name": c["name"],
                   "customer_phone": c["phone"], "customer_address": f'{c["address"]} {c["district"]} {c["city"]}',
                   "device_id": dev["id"] if dev else "", "device_brand_id": br["id"] if br else "", "device_brand_name": br["name"] if br else "",
                   "device_brand_logo": br.get("logo_url", "") if br else "", "device_model": "Örnek model", "device_type": sec["type"],
                   "device_serial": dev["serial_no"] if dev else "", "fault_description": faults[n % len(faults)], "scheduled_at": when.strftime("%Y-%m-%dT%H:%M"),
                   "priority": "normal", "assigned_technician_id": t["id"] if t else "", "assigned_to_fu": "",
                   "assigned_technician_name": t["name"] if t else "", "technician_commission_percent": 30.0 if t else 0.0, "status": st,
                   "work_done": "Arıza giderildi, test edildi." if st == "tamamlandi" else "", "parts_used": ([{"name": "Yedek parça", "qty": 1, "unit_price": parts}] if parts else []),
                   "labor_fee": labor, "parts_total": parts, "total_amount": labor + parts,
                   "technician_commission_amount": round((labor + parts) * 0.3, 2) if st == "tamamlandi" else 0.0,
                   "photos_before": [], "photos_after": [], "signature_url": "", "tech_signature_url": "", "pdf_note": "", "cancel_reason": "",
                   "customer_rating": 5 if st == "tamamlandi" and n % 2 == 0 else 0, "source_channel": "", "source_detail": "",
                   "started_at": when.isoformat() if st in ("basladi", "tamamlandi") else "", "completed_at": when.isoformat() if st == "tamamlandi" else "",
                   "created_at": when.isoformat(), "updated_at": when.isoformat(), "created_by": ""}
            await fdb.service_jobs.insert_one(job)
            if st == "tamamlandi" and t:
                tot = labor + parts
                base = {"technician_id": t["id"], "job_id": job["id"], "date": when.isoformat(), "created_by": ""}
                await fdb.cash_transactions.insert_one({**base, "id": str(uuid.uuid4()), "type": "gelir", "amount": tot, "description": f"Servis Geliri - {job['job_number']} - {c['name']}"})
                await fdb.cash_transactions.insert_one({**base, "id": str(uuid.uuid4()), "type": "teknisyen_prim", "amount": round(tot * 0.7, 2), "description": f"Prim (Kasada Kalan) - {job['job_number']}"})
                await fdb.cash_transactions.insert_one({**base, "id": str(uuid.uuid4()), "type": "teknisyen_borc", "amount": round(tot * 0.3, 2), "description": f"Firma payı - {job['job_number']}"})

        # satış listesine düş (sahip Talepler'de görür)
        try:
            await db.main().leads.insert_one({"id": str(uuid.uuid4()), "name": name, "phone": phone, "firm": company, "sector": sec["name"], "form": "demo-hesabi",
                                              "status": "demo", "note": f"Otomatik demo açıldı: {email}", "src": {}, "extra": {"demo_firm": fid},
                                              "created_at": _now(), "updated_at": _now()})
        except Exception:               # noqa: BLE001
            pass
        return {"ok": True, "login_url": "/giris", "email": email, "password": pw, "tech_email": techs[0]["email"], "days": DEMO_DAYS, "company": company}
