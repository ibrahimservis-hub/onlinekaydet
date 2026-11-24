# -*- coding: utf-8 -*-
"""Anında demo hesabı: satış sitesindeki forma ad, telefon ve sektör girilince örnek verili, 7 gün açık gerçek bir firma açılır.

Firma tam pakettedir (Kurumsal), örnek müşteri/usta/servis kaydı hazır gelir. Talep ayrıca satış listesine (leads) 'demo' olarak düşer.
"""
import hashlib
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
import notify
import sektor
import tenant

_RATE = {}
DEMO_DAYS = 7
GUNLUK_LIMIT = int(os.environ.get("DEMO_GUNLUK_LIMIT", "60"))   # bir günde açılabilecek toplam demo
KOD_SURE = 600                                                    # SMS kodu geçerlilik süresi (sn)
SECTOR_MAP = {"kombi": "kombi", "klima": "klima", "beyaz eşya": "beyaz_esya", "beyaz esya": "beyaz_esya", "elektronik": "elektronik",
              "bilgisayar": "bilgisayar", "tesisat": "tesisat", "elektrik": "elektrik", "güvenlik": "guvenlik", "guvenlik": "guvenlik"}
import sektor_ek
SECTOR_MAP.update(sektor_ek.SECTOR_WORDS)
SECTOR_MAP.update({k: k for k in sektor_ek.NEW})
# Araç bakım / yıkama / kaplama demoları: araç, plaka ve uygulama gerçek işe uygun görünür (paket adı = sektörün hizmet grubu)
_ARAÇ = [("Volkswagen Passat 1.6 TDI", "06 KLM 214"), ("Toyota Corolla Hybrid", "06 FTR 581"), ("BMW 320i", "34 ABV 902"), ("Renault Clio 1.0", "06 ZGK 447"),
         ("Fiat Egea Cross", "06 DNM 305"), ("Tesla Model Y", "34 EVT 118"), ("Hyundai Tucson", "06 HYT 760")]
ARAC_DEMO = {
    "oto_kaplama": [
        ("Pasta cila", "Hare ve çizik giderme, 2 aşamalı pasta cila", "2 aşamalı pasta cila uygulandı, kaporta ve tamponlar parlatıldı.", "Pasta ve cila seti", 3500.0),
        ("Seramik", "9H seramik kaplama (3 yıl koruma), boya düzeltme dahil", "Boya düzeltme yapıldı, 2 kat seramik kaplama uygulandı; kürlenme için 24 saat sonra teslim.", "Seramik kaplama sarfı", 12500.0),
        ("Cam filmi", "Yan ve arka cam filmi, ön cama ısı filmi", "Cam filmleri uygulandı, kenar ve kabarcık kontrolü yapıldı.", "Cam filmi rulosu", 4200.0),
        ("İç temizlik", "İç detay: koltuk, tavan ve plastik temizliği", "Koltuk ve tavan derin temizlendi, plastikler koruyucuyla yenilendi.", "İç temizlik kimyasalı", 2200.0)],
    "oto_yikama": [
        ("İç dış yıkama", "İç ve dış yıkama, cam ve jant silme", "İç dış yıkama yapıldı, cam ve jantlar silindi, torpido parlatıldı.", "Yıkama şampuanı ve cila", 650.0),
        ("Detay", "Detaylı iç temizlik ve kaporta cilası", "İç detay temizlik ve kaporta cilası yapıldı, kokular giderildi.", "Detay temizlik seti", 2800.0),
        ("Pasta cila", "Kaporta pasta cila, iki aşama", "İki aşamalı pasta cila uygulandı, hareler giderildi.", "Pasta ve cila seti", 3200.0),
        ("Seramik / koruma", "Hızlı seramik koruma (1 yıl)", "Boya temizlendi, hızlı seramik koruma uygulandı.", "Koruma spreyi", 3800.0),
        ("Filo aracı", "Filo aracı iç dış yıkama (haftalık)", "Filo aracı iç dış yıkandı, kayıt formu işlendi.", "Yıkama şampuanı", 450.0)],
}


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
FAULTS.update(sektor_ek.DEMO_FAULTS)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _norm_phone(s):
    d = re.sub(r"\D", "", str(s or ""))
    if d.startswith("90") and len(d) == 12:
        d = d[2:]
    if d.startswith("0"):
        d = d[1:]
    return d if len(d) == 10 and d.startswith("5") else ""


def _demo_img(key, i):
    """Örnek ürünlere sektörün fotoğrafı: themes/img/<sektor>[2|3].jpg varsa."""
    import os
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "themes", "img")
    nm = key + ("" if i % 3 == 0 else str(i % 3 + 1))
    return ["/demo-foto/%s.jpg" % nm] if os.path.isfile(os.path.join(d, nm + ".jpg")) else []


async def rename_old_demos(db):
    """Demo firmaları 'Demo 1', 'Demo 2'... adlarında tutar: biçimi bozuk veya tekrar eden adları düzeltir, firma ayarındaki adı eşitler."""
    import re as _re
    try:
        fl = await db.main().firms.find({"demo": True}, {"_id": 0}).sort("created_at", 1).to_list(5000)
        seen, todo = set(), []
        for f in fl:
            m = _re.fullmatch(r"Demo (\d+)", f.get("name") or "")
            if m and int(m.group(1)) not in seen:
                seen.add(int(m.group(1)))
            else:
                todo.append(f)
        names = {f["id"]: f.get("name") for f in fl}
        n = 0
        for f in todo:
            n += 1
            while n in seen:
                n += 1
            seen.add(n)
            names[f["id"]] = f"Demo {n}"
            await db.main().firms.update_one({"id": f["id"]}, {"$set": {"name": f"Demo {n}"}})
        for f in fl:
            nm = names[f["id"]]
            fdb = db.firm(f["db"])
            await fdb.app_settings.update_one({"_id": "global"}, {"$set": {"company_name": nm}}, upsert=True)
            await fdb.app_settings.update_one({"_id": "firm"}, {"$set": {"name": nm}}, upsert=True)
    except Exception:
        pass


def register(api_router, db, deps):
    hash_password = deps["hash_password"]

    def _ip(request):
        return (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))

    def _kh(phone, code):
        return hashlib.sha256(("%s|%s|%s" % (phone, code, os.environ.get("SECRET_KEY", "demo"))).encode()).hexdigest()

    async def sms_acik():
        try:
            return (await notify.get_settings(db.main())).get("provider") != "none"
        except Exception:      # noqa: BLE001
            return False

    @api_router.get("/public/demo/ayar")
    async def demo_ayar():
        """Site formu telefon doğrulaması isteyip istemediğini buradan öğrenir (SMS ayarı kapalıysa doğrulama yok)."""
        return {"kod": await sms_acik(), "sektorler": sorted(({"k": k, "ad": v.get("name") or k} for k, v in sektor.SECTORS.items()), key=lambda x: x["ad"])}

    @api_router.post("/public/demo/kod")
    async def demo_kod(payload: dict, request: Request):
        if str(payload.get("website") or "").strip():
            return {"ok": True}
        phone = _norm_phone(payload.get("phone"))
        if not phone:
            raise HTTPException(422, "Telefon numarası geçersiz (05xx xxx xx xx)")
        if not await sms_acik():
            return {"ok": True, "kod": False}
        now = time.time()
        ip = _ip(request)
        hist = [t for t in _RATE.get("kod:" + ip, []) if now - t < 3600]
        if len(hist) >= 6:
            raise HTTPException(429, "Çok fazla deneme, biraz sonra tekrar deneyin")
        if await db.main().demo_codes.count_documents({"phone": phone, "at": {"$gte": now - 3600}}) >= 3:
            raise HTTPException(429, "Bu telefona saatte en fazla 3 kod gönderilir")
        if await db.main().demo_codes.count_documents({"phone": phone, "at": {"$gte": now - 45}}):
            raise HTTPException(429, "Kod az önce gönderildi, birkaç saniye bekleyin")
        code = "".join(random.choice("0123456789") for _ in range(6))
        await db.main().demo_codes.insert_one({"phone": phone, "h": _kh(phone, code), "at": now, "exp": now + KOD_SURE, "tries": 0})
        hist.append(now)
        _RATE["kod:" + ip] = hist
        r = await notify.send(db.main(), "sms", phone, "OnlineKaydet demo doğrulama kodunuz: %s (10 dakika geçerli)" % code, kind="demo_kod", ref=phone,
                              store_text="OnlineKaydet demo doğrulama kodu: ******")
        if r.get("status") == "failed":
            raise HTTPException(502, "SMS gönderilemedi, lütfen tekrar deneyin veya bizi arayın: 0544 444 40 04")
        return {"ok": True, "kod": True}

    async def kod_dogrula(phone, code):
        now = time.time()
        d = await db.main().demo_codes.find_one({"phone": phone, "exp": {"$gte": now}, "used": {"$ne": True}}, {"_id": 0}, sort=[("at", -1)])
        if not d:
            raise HTTPException(422, "Doğrulama kodu bulunamadı veya süresi doldu, yeni kod isteyin")
        if d.get("tries", 0) >= 5:
            raise HTTPException(429, "Çok fazla yanlış deneme, yeni kod isteyin")
        if not secrets.compare_digest(d["h"], _kh(phone, re.sub(r"\D", "", str(code or "")))):
            await db.main().demo_codes.update_one({"phone": phone, "at": d["at"]}, {"$inc": {"tries": 1}})
            raise HTTPException(422, "Doğrulama kodu hatalı")
        await db.main().demo_codes.update_one({"phone": phone, "at": d["at"]}, {"$set": {"used": True}})

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
        _raw = str(payload.get("sector") or "").strip().lower()
        key = _raw if _raw in sektor.SECTORS else SECTOR_MAP.get(_raw, "")      # tam sektör anahtarı önce ("bilgisayar" kelime eşlemesi bilgisayar_kursu'na kayıyordu)
        if key not in sektor.SECTORS:
            raise HTTPException(422, "Sektör seçin")
        since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        if await db.main().firms.count_documents({"demo": True, "created_at": {"$gte": since}}) >= GUNLUK_LIMIT:
            raise HTTPException(429, "Bugünkü demo kontenjanı doldu. Bizi arayın, birlikte açalım: 0544 444 40 04")
        if await sms_acik():
            await kod_dogrula(phone, payload.get("code"))
        if await db.main().firms.count_documents({"demo_phone": phone, "created_at": {"$gte": since}}) >= 2:
            raise HTTPException(429, "Bu telefonla bugün demo açıldı. Giriş bilgilerinizi kaybettiyseniz bizi arayın: 0544 444 40 04")
        hist.append(now)
        _RATE[ip] = hist

        sec = sektor.SECTORS[key]
        fid = uuid.uuid4().hex[:12]
        tag = secrets.token_hex(3)
        import re as _re2
        _used = [int(m.group(1)) for x in await db.main().firms.find({"demo": True}, {"_id": 0, "name": 1}).to_list(5000) for m in [_re2.fullmatch(r"Demo (\d+)", x.get("name") or "")] if m]
        n = (max(_used) if _used else 0) + 1
        while await db.main().firms.find_one({"login_email": f"demo{n}@demo.onlinekaydet.com"}):
            n += 1
        email = f"demo{n}@demo.onlinekaydet.com"
        pw = "".join(random.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(8))
        company = f"Demo {n}"
        import sektor_dil as _sdm
        mods = list(firms.ALL_MODS)
        f = {"id": fid, "db": db.firm_db_name(fid), "name": company, "login_email": email, "contact_name": name, "phone": phone, "address": "",
             "tax_no": "", "tax_office": "", "features": {}, "status": "aktif", "created_at": _now(), "logo": "",
             "expires_at": (datetime.now(timezone.utc) + timedelta(days=DEMO_DAYS)).isoformat(), "package": "kurumsal", "modules": list(mods),
             "sector": key, "demo": True, "demo_phone": phone, "demo_firma": " ".join(str(payload.get("firm") or "").split())[:80]}
        fdb = db.firm(f["db"])
        await fdb.users.insert_one({"id": str(uuid.uuid4()), "email": email, "password_hash": hash_password(pw), "name": name, "phone": phone,
                                    "role": "admin", "commission_percent": 0.0, "is_active": True, "firm_owner": True, "created_at": _now()})
        import sektor_dil
        brands = sektor_dil.brand_docs(key, sektor.SECTORS[key].get("brands")) or await db.main().brands.find({}, {"_id": 0}).to_list(500)
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
        if "eticaret" in mods:
            await fdb.app_settings.update_one({"_id": "firm"}, {"$set": {"modules": list(mods)}}, upsert=True)
            await fdb.app_settings.update_one({"_id": "site_features"}, {"$set": {"shop_enabled": True}}, upsert=True)
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
        _mdl, _wd, _pn = sektor_ek.DEMO_META.get(key, ("Örnek model", "Arıza giderildi, test edildi.", "Yedek parça"))
        plan = [("yeni", None), ("atandi", 0), ("yolda", 0), ("basladi", 1), ("tamamlandi", 0), ("tamamlandi", 1), ("tamamlandi", 0)]
        _arac = ARAC_DEMO.get(key)
        _brand_all = {b["name"]: b async for b in fdb.brands.find({}, {"_id": 0})} if _arac else {}
        for n, (st, ti) in enumerate(plan):
            c = custs[n % len(custs)]
            dev = None
            br_n, mdl_n, ser_n, flt_n, wd_n, pn_n, price_n = br, _mdl, f"DM{n:04d}", faults[n % len(faults)], _wd, _pn, None
            if _arac:
                _pk, _is, _yap, _urun, price_n = _arac[n % len(_arac)]
                br_n = _brand_all.get(_pk) or br
                mdl_n, ser_n = _ARAÇ[n % len(_ARAÇ)]
                flt_n, wd_n, pn_n = _is, _yap, _urun
            if br_n:
                dev = {"id": str(uuid.uuid4()), "customer_id": c["id"], "brand_id": br_n["id"], "brand_name": br_n["name"], "brand_logo": br_n.get("logo_url", ""),
                       "type": "araç" if _arac else sec["type"], "model": mdl_n, "serial_no": ser_n, "created_at": _now()}
                await fdb.devices.insert_one(dev)
            t = techs[ti] if ti is not None else None
            when = datetime.now(timezone.utc) - timedelta(days=(7 - n) if st == "tamamlandi" else 0, hours=-n)
            labor, parts = (450.0 + 50 * n, 300.0 + 40 * n) if st == "tamamlandi" else (0.0, 0.0)
            if _arac and st == "tamamlandi":
                labor, parts = round(price_n * 0.8, 2), round(price_n * 0.2, 2)
            job = {"id": str(uuid.uuid4()), "job_number": f"DM-{1001 + n}", "customer_id": c["id"], "customer_name": c["name"],
                   "customer_phone": c["phone"], "customer_address": f'{c["address"]} {c["district"]} {c["city"]}',
                   "device_id": dev["id"] if dev else "", "device_brand_id": br_n["id"] if br_n else "", "device_brand_name": br_n["name"] if br_n else "",
                   "device_brand_logo": br_n.get("logo_url", "") if br_n else "", "device_model": mdl_n, "device_type": "araç" if _arac else sec["type"],
                   "device_serial": dev["serial_no"] if dev else "", "fault_description": flt_n, "scheduled_at": when.strftime("%Y-%m-%dT%H:%M"),
                   "priority": "normal", "assigned_technician_id": t["id"] if t else "", "assigned_to_fu": "",
                   "assigned_technician_name": t["name"] if t else "", "technician_commission_percent": 30.0 if t else 0.0, "status": st,
                   "work_done": wd_n if st == "tamamlandi" else "", "parts_used": ([{"name": pn_n, "qty": 1, "unit_price": parts}] if parts else []),
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

        try:
            _cats = {}
            for _i, (_n, _b, _c, _pr, _old, _st) in enumerate(sektor_ek.DEMO_URUN.get(key, [])):
                if _c not in _cats:
                    _cid = uuid.uuid4().hex[:12]
                    await fdb.shop_categories.insert_one({"id": _cid, "name": _c, "slug": _c.lower().replace(" & ", "-").replace(" ", "-"), "created_at": _now()})
                    _cats[_c] = _cid
                _slug = re.sub(r"[^a-z0-9]+", "-", _n.lower().translate(str.maketrans("çğıöşüİ", "cgiosui"))).strip("-")
                await fdb.shop_products.insert_one({"id": uuid.uuid4().hex[:12], "slug": _slug, "name": _n, "brand": _b, "category": _c, "category_id": _cats[_c], "category_ids": [_cats[_c]],
                                                    "price": float(_pr), "old_price": float(_old), "stock": _st, "track_stock": True, "active": True, "featured": _i < 3, "images": _demo_img(key, _i), "sort": _i,
                                                    "short": "Örnek ürün; fiyat, stok ve fotoğrafı panelden değiştirin.", "created_at": _now(), "updated_at": _now(), "sold": 0})
        except Exception:               # noqa: BLE001
            pass

        if _sdm.family(key) == "siparis":
            # mağaza/sipariş işlerinde Siparişler ekranı boş açılmasın: 3 örnek sipariş (demo müşterileriyle)
            try:
                prods = await fdb.shop_products.find({}, {"_id": 0}).sort("sort", 1).to_list(6)
                for k, (stt, adet) in enumerate((("onaylandi", 1), ("kargoda", 2), ("teslim_edildi", 1))):
                    if not prods:
                        break
                    pr, c = prods[k % len(prods)], custs[k % len(custs)]
                    line = round(float(pr["price"]) * adet, 2)
                    ship = 49.9
                    await fdb.shop_orders.insert_one({
                        "id": uuid.uuid4().hex[:12], "order_no": "SP-%d" % (1001 + k), "status": stt,
                        "customer": {"name": c["name"], "phone": c["phone"], "email": "", "city": c.get("city", ""), "district": c.get("district", ""), "address": c.get("address", "")},
                        "note": "Örnek sipariş (demo)", "items": [{"product_id": pr["id"], "name": pr["name"], "brand": pr.get("brand", ""), "model": "", "price": float(pr["price"]), "qty": adet,
                                                                    "line_total": line, "image": (pr.get("images") or [""])[0], "variant_id": ""}],
                        "subtotal": line, "shipping": ship, "cod_fee": 0.0, "total": round(line + ship, 2), "account_id": "", "phone_key": c["phone"][-10:],
                        "admin_note": "", "tracking_no": "" if stt == "onaylandi" else "DEMO%06d" % (k + 1), "carrier": "" if stt == "onaylandi" else "Yurtiçi Kargo",
                        "payment": {"method": "havale", "label": "Havale / EFT", "status": "odendi", "amount": round(line + ship, 2)},
                        "history": [{"status": stt, "at": _now(), "note": "Örnek"}], "created_at": _now(), "updated_at": _now(), "external": True})
            except Exception:
                pass
            # müşteri panelindeki Siparişler listesi de dolu açılsın (restoranda platform kanallarıyla)
            try:
                import dis_siparis
                kanal = ("yemeksepeti", "trendyol_yemek", "getir_yemek") if key == "lokanta" else ("site", "site", "site")
                for k, (mp, adet) in enumerate((("onaylandi", 1), ("hazirlaniyor", 2), ("teslim_edildi", 1))):
                    if not prods:
                        break
                    pr, c = prods[k % len(prods)], custs[k % len(custs)]
                    await dis_siparis.yaz(fdb, kanal[k], {"key": "ORNEK-%d" % (k + 1), "total": round(float(pr["price"]) * adet, 2), "created": None,
                                                          "lines": [{"barcode": "", "quantity": adet, "name": pr["name"], "price": float(pr["price"])}],
                                                          "customer": {"name": c["name"], "phone": c["phone"], "email": "", "city": c.get("city", ""), "district": c.get("district", ""), "address": c.get("address", "")}}, mp)
            except Exception:       # noqa: BLE001
                pass

        # satış listesine düş (sahip Talepler'de görür)
        try:
            await db.main().leads.insert_one({"id": str(uuid.uuid4()), "name": name, "phone": phone, "firm": company, "sector": sec["name"], "form": "demo-hesabi",
                                              "status": "demo", "note": f"Otomatik demo açıldı: {email}", "src": {}, "extra": {"demo_firm": fid},
                                              "created_at": _now(), "updated_at": _now()})
        except Exception:               # noqa: BLE001
            pass
        import sektor_dil as _sd
        if _sd.family(key) == "randevu":
            await fdb.app_settings.update_one({"_id": "growth"}, {"$set": {"booking.enabled": True}}, upsert=True)   # demo sitesinden online randevu denenebilsin
            # randevulu sektörlerde takvim boş görünmesin: bugün ve yarın için örnek randevular (müşteri adları demo müşterileri)
            try:
                import yp as _yp
                svs = (_yp.SEED.get(key) or [])[:6]
                if svs:
                    d0 = datetime.now(timezone(timedelta(hours=3))).date()
                    slots = [(0, "10:00", 0), (0, "11:30", 1), (0, "14:00", 0), (0, "16:00", 1), (1, "10:30", 0), (1, "13:00", 1)]
                    for k, (gun, saat, ti) in enumerate(slots):
                        sn, sd, sp = svs[k % len(svs)]
                        c = custs[k % len(custs)]
                        await fdb.bookings.insert_one({"id": uuid.uuid4().hex, "no": "RD-%d" % (1001 + k), "yp": True, "status": "onaylandi", "stage": "bekliyor",
                                                       "name": c["name"], "phone": c["phone"], "date": (d0 + timedelta(days=gun)).isoformat(), "time": saat,
                                                       "staff_id": techs[ti]["id"], "items": [{"name": sn, "price": float(sp), "dur": int(sd)}], "dur": int(sd),
                                                       "discount": 0.0, "note": "Örnek kayıt (demo)", "source": "telefon", "payments": [], "job_id": "",
                                                       "created_at": _now(), "created_by": "demo"})
                    await fdb.app_settings.update_one({"_id": "yp_no"}, {"$set": {"n": len(slots)}}, upsert=True)
            except Exception:
                pass
        return {"ok": True, "login_url": "/giris", "panel": "/salon", "email": email, "password": pw, "tech_email": techs[0]["email"], "days": DEMO_DAYS, "company": company, "family": _sd.family(key)}
