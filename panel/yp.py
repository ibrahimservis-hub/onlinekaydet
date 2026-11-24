# -*- coding: utf-8 -*-
"""Yeni yönetim paneli (randevuyla çalışan işler): takvim, kasa, ekip, müşteri ve raporlar.

Eski panelin uçlarına ve ekranlarına dokunmaz. Randevular siteyle aynı `bookings` koleksiyonunda durur; böylece siteden
alınan randevu bu takvime düşer, panelden girilen randevu da sitedeki boş saat hesabına girer.
Kasa (`yp_cash`), ekip (`yp_staff`) ve hizmet listesi (`yp_services`) bu panelin kendi koleksiyonlarıdır.
Ödeme alındığında kasa satırı aynı istekte yazılır: randevu ile kasa birbirinden kopamaz."""
import re
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

COLORS = ["#1155cc", "#0f766e", "#9a3412", "#6d28d9", "#be185d", "#3f6212", "#0e7490", "#7c2d12"]
STAGES = ("bekliyor", "geldi", "islemde", "tamamlandi", "gelmedi", "iptal")
OPEN = ("bekliyor", "geldi", "islemde")
METHODS = ("Nakit", "Kart", "Havale")
SOURCES = ("telefon", "salon", "site", "instagram", "whatsapp")
SEED = {
    "kuafor": [("Saç kesimi", 30, 450), ("Fön", 30, 250), ("Boya", 90, 1400), ("Röfle", 120, 2200), ("Keratin bakım", 90, 1800), ("Saç + sakal", 45, 400), ("Gelin saçı", 120, 3500)],
    "guzellik": [("Cilt bakımı", 60, 1200), ("Kaş alımı", 15, 200), ("Lazer epilasyon", 45, 1500), ("Manikür", 40, 450), ("Pedikür", 45, 500)],
    "tirnak_studyo": [("Manikür", 40, 450), ("Pedikür", 45, 500), ("Kalıcı oje", 45, 600), ("Protez tırnak", 90, 1200)],
    "spa_hamam": [("Klasik masaj", 60, 1500), ("Hamam + kese", 45, 900), ("Aromaterapi masajı", 60, 1800)],
}


def _now():
    return datetime.now(TR).replace(tzinfo=None)


def _t(v, n):
    return " ".join(str(v or "").split())[:n]


def _num(v):
    try:
        x = float(str(v).replace(",", ".")) if v not in (None, "") else 0.0
    except ValueError:
        x = 0.0
    return round(max(0.0, min(x, 10 ** 8)), 2)


def _day(v):
    v = str(v or "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        raise HTTPException(422, "Tarih geçersiz")
    return v


def _tm(v):
    v = str(v or "")
    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", v):
        raise HTTPException(422, "Saat geçersiz")
    return v


def _min(t):
    return int(t[:2]) * 60 + int(t[3:5])


def _phone(v):
    d = re.sub(r"\D", "", str(v or ""))[-10:]
    return d if len(d) == 10 else ""


# Panelde seçilen sektör paketi (16 paket) -> terim tablosundaki (70 sektör) karşılığı
PACKMAP = {"oto": "oto_servis", "emlak": "emlakci", "surucu": "surucu_kursu", "kurs": "etut_merkezi", "fitness": "spor_salonu",
           "saglik": "dis_klinigi", "organizasyon": "dugun_salonu"}
# Müşteriye ne denir (yalnız farklı olanlar; yoksa "Müşteri") ve çoğulu
MUSTERI = {"avukat": ("Müvekkil", "Müvekkiller"), "muhasebe": ("Mükellef", "Mükellefler"), "dis_klinigi": ("Hasta", "Hastalar"), "fizyoterapi": ("Hasta", "Hastalar"),
           "veteriner": ("Hasta Sahibi", "Hasta Sahipleri"), "psikolog": ("Danışan", "Danışanlar"), "diyetisyen": ("Danışan", "Danışanlar"),
           "aile_danisman": ("Danışan", "Danışanlar"), "surucu_kursu": ("Kursiyer", "Kursiyerler"), "src_kursu": ("Kursiyer", "Kursiyerler"),
           "dil_okulu": ("Öğrenci", "Öğrenciler"), "muzik_kursu": ("Öğrenci", "Öğrenciler"), "etut_merkezi": ("Öğrenci", "Öğrenciler"),
           "ozel_ders": ("Öğrenci", "Öğrenciler"), "bilgisayar_kursu": ("Öğrenci", "Öğrenciler"), "yuzme_kursu": ("Öğrenci", "Öğrenciler"),
           "anaokulu": ("Veli", "Veliler"), "spor_salonu": ("Üye", "Üyeler"), "yoga_dans": ("Üye", "Üyeler"), "lokanta": ("Misafir", "Misafirler")}
SALONLU = {"spor_salonu", "dugun_salonu", "kuafor", "guzellik", "tirnak_studyo", "estetik_merkezi", "spa_hamam", "dovme_studyo"}


def terms(key):
    """Bu işte kişiye, işe ve yere ne denir (uzman / terapist / hekim; randevu / sipariş / servis kaydı ...). Panel metinleri buna göre uyarlanır."""
    key = PACKMAP.get(key, key)
    try:
        import sektor_dil
        r = sektor_dil.ROWS.get(key) or {}
        sade = key in sektor_dil.SADE
    except Exception:                                              # noqa: BLE001
        r, sade = {}, False
    if key in ("teknik", "otel"):
        sade = False
        r = {"teknik": {"kisi": "Usta/Ustalar", "is": "Servis Kaydı/Servis Kayıtları", "yer": "Servis Takibi"},
             "otel": {"kisi": "Personel/Personel", "is": "Rezervasyon/Rezervasyonlar", "yer": "Oda Takibi"}}[key]
    if sade and not r:
        r = {"kisi": "Teknisyen/Teknisyenler", "is": "Servis Kaydı/Servis Kayıtları", "yer": "Atölye Takibi"}
    a, _, b = (r.get("kisi") or "Uzman/Uzmanlar").partition("/")
    i1, _, i2 = (r.get("is") or "Randevu/Randevular").partition("/")
    if i2 and i2.endswith("Defteri"):                              # "Randevu Defteri" -> çoğul ad "Randevular"
        i2 = {"Randevu": "Randevular", "Seans": "Seanslar"}.get(i1, i1 + "ler")
    if i1 == "Sipariş":                                            # mağaza/yemek gibi işlerde randevu = görüşme/teslimat/rezervasyon (siparişle karışmasın)
        i1, i2 = {"market": ("Teslimat", "Teslimatlar"), "lokanta": ("Rezervasyon", "Rezervasyonlar")}.get(key, ("Görüşme", "Görüşmeler"))
    m1, m2 = MUSTERI.get(key, ("Müşteri", "Müşteriler"))
    return {"musteri": m1, "musteriler": m2, "kisi": a, "kisiler": b or a, "yer": (r.get("yer") or "Koltuk Takibi").replace(" Takibi", ""),
            "is": i1, "isler": i2 or i1 + "lar", "salon": "salon" if (key in SALONLU or not r) else "işletme"}


def view(b):
    """bookings kaydı -> panel randevusu (eski panelden/siteden gelen kayıtlar da okunur)."""
    st = b.get("stage")
    if not st:
        st = {"bekliyor": "talep", "onaylandi": "bekliyor", "tamamlandi": "tamamlandi"}.get(b.get("status"), "iptal")
    items = b.get("items") or []
    total = round(max(sum(_num(i.get("price")) for i in items) - _num(b.get("discount")), 0), 2)
    paid = round(sum(_num(p.get("amount")) for p in b.get("payments") or []), 2)
    return {"id": b["id"], "no": b.get("no", ""), "name": b.get("name", ""), "phone": b.get("phone", ""), "date": b.get("date", ""), "time": b.get("time", ""),
            "dur": int(b.get("dur") or 30), "stage": st, "staff_id": b.get("staff_id", ""), "items": items, "discount": _num(b.get("discount")),
            "total": total, "paid": paid, "balance": round(max(total - paid, 0), 2), "payments": b.get("payments") or [], "note": b.get("note") or b.get("fault") or "",
            "want": b.get("device_type", ""), "source": b.get("source") or ("site" if not b.get("yp") else "telefon"), "coupon": b.get("coupon", "")}


def register(api_router, db, deps):
    adm = deps["require_admin"]

    async def sector():
        d = await db.app_settings.find_one({"_id": "sector"}, {"_id": 0}) or {}
        return d.get("key") or ""

    async def staff_all():
        rows = await db.yp_staff.find({}, {"_id": 0}).sort("order", 1).to_list(200)
        if rows or await db.app_settings.find_one({"_id": "yp_seed"}):
            return rows
        us = await db.users.find({"role": "technician", "is_active": {"$ne": False}}, {"_id": 0, "id": 1, "name": 1, "commission_percent": 1}).to_list(100)
        rows = [{"id": u["id"], "name": u.get("name", ""), "title": "", "commission": float(u.get("commission_percent") or 0), "salary": 0.0, "off": [],
                 "color": COLORS[i % len(COLORS)], "active": True, "order": i} for i, u in enumerate(us) if u.get("name")]
        if rows:
            await db.yp_staff.insert_many([dict(r) for r in rows])
        key = await sector()
        if not await db.yp_services.count_documents({}):
            sv = [{"id": uuid.uuid4().hex[:12], "name": n, "dur": d, "price": float(p), "active": True, "order": i} for i, (n, d, p) in enumerate(SEED.get(key, []))]
            if sv:
                await db.yp_services.insert_many([dict(s) for s in sv])
        await db.app_settings.update_one({"_id": "yp_seed"}, {"$set": {"at": time.time()}}, upsert=True)
        return rows

    async def cfg():
        try:
            import growth
            return (await growth.get_cfg(db)).get("booking") or {}
        except Exception:                                          # noqa: BLE001
            return {}

    @api_router.put("/yp/dash")
    async def dash_put(p: dict, user: dict = Depends(adm)):
        """Ana panelde hangi kutuların hangi sırayla görüneceği (kullanıcıya özel, her cihazda aynı). Boş liste = hepsi kapalı; null = varsayılan."""
        l = p.get("list")
        key = "yp_dash:" + str(user.get("id") or user.get("email") or "")
        if l is None:
            await db.app_settings.delete_one({"_id": key})
            return {"ok": True}
        if not isinstance(l, list) or len(l) > 40 or not all(isinstance(x, str) and 0 < len(x) <= 20 for x in l):
            raise HTTPException(422, "Geçersiz liste")
        await db.app_settings.update_one({"_id": key}, {"$set": {"list": list(dict.fromkeys(l))}}, upsert=True)
        return {"ok": True}

    @api_router.get("/yp/rehber")
    async def rehber(user: dict = Depends(adm)):
        """Yeni firma için sektöre göre kurulum adımları; her adımın bitip bitmediği gerçek veriden hesaplanır."""
        key = await sector()
        pk0 = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
        fam = __import__("sektor_dil").family_of(key, pk0.get("sector") or "")
        st = await db.app_settings.find_one({"_id": "yp_rehber"}, {"_id": 0}) or {}
        if fam not in ("randevu", "siparis"):
            return {"steps": [], "gizli": True, "bitti": True}
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        B = await cfg()
        prof = await db.app_settings.find_one({"_id": "site_profile"}, {"_id": 0}) or {}
        steps = [{"id": "firma", "ad": "Firma bilgilerini yazın", "ac": "Telefon, adres ve çalışma saatleri belgelerde ve sitede görünür.",
                  "git": "ayar", "btn": "Bilgileri yaz",
                  "bitti": bool((g.get("company_name") or "").strip() and (g.get("company_phone") or "").strip())}]
        if fam == "randevu":
            steps += [
                {"id": "hizmet", "ad": "Hizmetlerinizi ve fiyatlarını girin", "ac": "Müşteri randevu alırken bunlardan seçer.", "git": "ayar", "btn": "Hizmet ekle",
                 "bitti": await db.yp_services.count_documents({}) > 0},
                {"id": "ekip", "ad": "Çalışanlarınızı ekleyin",
                 "ac": "Takvim ve prim hesabı çalışana göre tutulur.", "git": "ekip", "btn": "Çalışan ekle",
                 "bitti": await db.yp_staff.count_documents({"active": {"$ne": False}}) > 0},
                {"id": "online", "ad": "Online randevuyu açın", "ac": "Sitenizden gelen randevular takvime düşer.", "git": "ayar", "btn": "Ayarı aç",
                 "bitti": bool(B.get("enabled"))},
                {"id": "site", "ad": "Sitenizi gözden geçirin", "ac": "Slogan, hakkında yazısı ve fotoğrafları kendi işinize göre düzenleyin.", "git": "site", "btn": "Siteyi düzenle",
                 "bitti": bool((prof.get("slogan") or "").strip() or (prof.get("about") or "").strip())},
                {"id": "ilk", "ad": "İlk randevunuzu oluşturun", "ac": "Telefonla gelen bir müşteriyi takvime ekleyin.", "git": "takvim", "btn": "Takvimi aç",
                 "bitti": await db.bookings.count_documents({}) > 0},
            ]
        else:
            ent = await db.yp_integrations.find({"state": "bagli"}, {"_id": 0, "id": 1}).to_list(50)
            ent_ids = {e["id"] for e in ent}
            odeme = {"iyzico", "paytr", "param", "sipay", "craftgate", "banka_pos", "havale", "kapida"}
            steps += [
                {"id": "urun", "ad": "İlk ürününüzü ekleyin", "ac": "Fotoğraf, fiyat ve stok girin; ürün mağazanıza kendiliğinden düşer.", "git": "urun", "btn": "Ürün ekle",
                 "bitti": await db.yp_products.count_documents({}) > 0},
                {"id": "odeme", "ad": "Ödeme yöntemini bağlayın", "ac": "Kartla ödeme, havale ya da kapıda ödeme.", "git": "entegrasyon", "btn": "Bağlan",
                 "bitti": bool(ent_ids & odeme)},
                {"id": "kargo", "ad": "Kargo firmanızı bağlayın", "ac": "Gönderi oluşturma ve takip numarası için.", "git": "entegrasyon", "btn": "Bağlan",
                 "bitti": bool(ent_ids & {"aras", "yurtici", "mng", "ptt", "surat", "ups", "sendeo", "hepsijet", "kolaygelsin"})},
                {"id": "site", "ad": "Mağaza sayfanızı gözden geçirin", "ac": "Slogan, hakkında yazısı ve fotoğrafları düzenleyin.", "git": "site", "btn": "Siteyi düzenle",
                 "bitti": bool((prof.get("slogan") or "").strip() or (prof.get("about") or "").strip())},
                {"id": "ilk", "ad": "İlk siparişinizi alın", "ac": "Mağazadan gelen ya da telefonla verilen ilk sipariş burada görünür.", "git": "siparis", "btn": "Siparişleri aç",
                 "bitti": await db.yp_orders.count_documents({}) > 0},
            ]
        n_bitti = len([x for x in steps if x["bitti"]])
        return {"steps": steps, "gizli": bool(st.get("gizli")), "bitti": n_bitti == len(steps), "n": n_bitti, "toplam": len(steps)}

    @api_router.post("/yp/rehber/gizle")
    async def rehber_gizle(payload: dict, user: dict = Depends(adm)):
        await db.app_settings.update_one({"_id": "yp_rehber"}, {"$set": {"gizli": bool(payload.get("gizli", True))}}, upsert=True)
        return {"ok": True}

    @api_router.get("/yp/lisans")
    async def lisans(_: dict = Depends(adm)):
        """Ana sayfadaki lisans/demo kartı: demo mu, bitiş tarihi, kalan süre, paket adı."""
        import tenant
        cur = tenant.current() or ""
        fid = cur.split("_f_", 1)[1] if "_f_" in cur else ""
        f = await db.main().firms.find_one({"id": fid}, {"_id": 0}) if fid else None
        if not f:
            return {"var": False}
        pkg, pkg_ad = f.get("package") or "", ""
        try:
            import firms as _f
            pk = (await _f.API["packages"]()).get(pkg) or {}
            pkg_ad = pk.get("name") or pkg
        except Exception:                                          # noqa: BLE001
            pkg_ad = pkg
        now = datetime.now(timezone.utc)
        bit = None
        try:
            bit = datetime.fromisoformat(str(f.get("expires_at") or "").replace("Z", "+00:00"))
            if bit.tzinfo is None:
                bit = bit.replace(tzinfo=timezone.utc)
        except ValueError:
            bit = None
        bas = None
        try:
            bas = datetime.fromisoformat(str(f.get("created_at") or "").replace("Z", "+00:00"))
            if bas.tzinfo is None:
                bas = bas.replace(tzinfo=timezone.utc)
        except ValueError:
            bas = None
        sn = int((bit - now).total_seconds()) if bit else None
        toplam = int((bit - bas).total_seconds()) if bit and bas and bit > bas else None
        tr = timezone(timedelta(hours=3))
        return {"var": True, "demo": bool(f.get("demo")), "paket": pkg, "paket_ad": pkg_ad, "firma": f.get("demo_firma") or f.get("name") or "",
                "bitis": bit.astimezone(tr).strftime("%Y-%m-%d %H:%M") if bit else "", "kalan_sn": sn, "toplam_sn": toplam,
                "satin_url": "https://onlinekaydet.com/satin-al.html?paket=%s&sektor=%s" % (pkg if pkg and not f.get("demo") else "", f.get("sector") or ""),
                "askida": f.get("status") == "askida"}

    @api_router.get("/yp/boot")
    async def boot(user: dict = Depends(adm)):
        st = await staff_all()
        key = await sector()
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        B = await cfg()
        sv = await db.yp_services.find({}, {"_id": 0}).sort("order", 1).to_list(500)
        pk = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
        try:
            import blocks
            mods, _sec, eshop = await blocks.firma_modulleri(db)
        except Exception:                                          # noqa: BLE001
            mods, eshop = list(pk.get("modules") or []), False
        if eshop and not await db.app_settings.find_one({"_id": "urun_ayna_v1"}, {"_id": 1}):
            try:                                                   # panel ürünlerini bir kez mağazaya aktar (önceden eklenenler)
                import urun_ayna
                n = await urun_ayna.ayna_hepsi(db)
                await db.app_settings.update_one({"_id": "urun_ayna_v1"}, {"$set": {"n": n}}, upsert=True)
            except Exception:                                      # noqa: BLE001
                pass
        try:
            import isakis
            psec = pk.get("sector") or key
            akis = len([f for f in isakis.FLOWS if psec in f["sectors"]])
        except Exception:                                          # noqa: BLE001
            akis = 0
        return {"firm": g.get("company_name") or "", "sector": key, "pack": pk.get("sector") or key,
                "terms": terms(pk.get("sector") or key), "sv": __import__("servis_dili").build(PACKMAP.get(pk.get("sector") or key, pk.get("sector") or key)), "modules": list(mods), "eticaret": bool(eshop), "work_flows": akis,
                "family": __import__("sektor_dil").family_of(key, pk.get("sector") or ""), "eski_panel": __import__("sektor_dil").family_of(key, pk.get("sector") or "") not in ("randevu", "siparis"),   # randevu ve sipariş işlerinde eski panel kapalı
                "user": user.get("name") or user.get("email") or "", "staff": st, "services": sv,
                "hours": {"start": B.get("start") or "09:00", "end": B.get("end") or "19:00", "closed": B.get("closed_weekdays") or [], "online": bool(B.get("enabled")),
                          "slot": int(B.get("slot_minutes") or 30)},
                "today": _now().date().isoformat(), "now": _now().strftime("%H:%M"),
                "dash": (await db.app_settings.find_one({"_id": "yp_dash:" + str(user.get("id") or user.get("email") or "")}, {"_id": 0}) or {}).get("list")}

    # ------------------------------------------------------------------ ekip
    def clean_staff(p, old=None):
        o = dict(old or {})
        if "name" in p or not old:
            o["name"] = _t(p.get("name"), 60)
            if len(o["name"]) < 2:
                raise HTTPException(422, "Ad yazın")
        for k, n in (("title", 60),):
            if k in p:
                o[k] = _t(p.get(k), n)
        if "commission" in p:
            o["commission"] = min(_num(p.get("commission")), 100.0)
        if "salary" in p:
            o["salary"] = _num(p.get("salary"))
        if "off" in p:
            o["off"] = sorted({int(x) for x in (p.get("off") or []) if str(x).isdigit() and 0 <= int(x) <= 6})
        if "active" in p:
            o["active"] = bool(p.get("active"))
        if p.get("color") in COLORS:
            o["color"] = p["color"]
        return o

    @api_router.post("/yp/staff")
    async def staff_add(payload: dict, _: dict = Depends(adm)):
        n = await db.yp_staff.count_documents({})
        d = {"id": uuid.uuid4().hex[:12], "title": "", "commission": 30.0, "salary": 0.0, "off": [], "color": COLORS[n % len(COLORS)], "active": True, "order": n}
        d = clean_staff(payload, d)
        await db.yp_staff.insert_one(dict(d))
        await db.app_settings.update_one({"_id": "yp_seed"}, {"$set": {"at": time.time()}}, upsert=True)
        return d

    @api_router.put("/yp/staff/{sid}")
    async def staff_put(sid: str, payload: dict, _: dict = Depends(adm)):
        old = await db.yp_staff.find_one({"id": sid}, {"_id": 0})
        if not old:
            raise HTTPException(404, "Kişi bulunamadı")
        d = clean_staff(payload, old)
        await db.yp_staff.update_one({"id": sid}, {"$set": d})
        return d

    # ------------------------------------------------------------------ hizmetler
    def clean_service(p):
        n = _t(p.get("name"), 60)
        if len(n) < 2:
            raise HTTPException(422, "Hizmet adı yazın")
        return {"name": n, "dur": max(5, min(int(_num(p.get("dur")) or 30), 600)), "price": _num(p.get("price")), "active": bool(p.get("active", True))}

    @api_router.post("/yp/services")
    async def service_add(payload: dict, _: dict = Depends(adm)):
        d = clean_service(payload)
        d.update({"id": uuid.uuid4().hex[:12], "order": await db.yp_services.count_documents({})})
        await db.yp_services.insert_one(dict(d))
        return d

    @api_router.put("/yp/services/{sid}")
    async def service_put(sid: str, payload: dict, _: dict = Depends(adm)):
        d = clean_service(payload)
        r = await db.yp_services.update_one({"id": sid}, {"$set": d})
        if not r.matched_count:
            raise HTTPException(404, "Hizmet bulunamadı")
        return dict(d, id=sid)

    @api_router.delete("/yp/services/{sid}")
    async def service_del(sid: str, _: dict = Depends(adm)):
        await db.yp_services.delete_one({"id": sid})
        return {"ok": True}

    # ------------------------------------------------------------------ randevular
    async def clean_appt(p, old=None):
        o = {}
        name = _t(p.get("name", (old or {}).get("name")), 80)
        if len(name) < 2:
            raise HTTPException(422, "Müşteri adını yazın")
        o["name"] = name
        o["phone"] = _phone(p.get("phone")) if "phone" in p else (old or {}).get("phone", "")
        o["date"], o["time"] = _day(p.get("date", (old or {}).get("date"))), _tm(p.get("time", (old or {}).get("time")))
        sid = str(p.get("staff_id", (old or {}).get("staff_id")) or "")
        if not sid or not await db.yp_staff.find_one({"id": sid}):
            raise HTTPException(422, "Randevuyu kimin yapacağını seçin")
        o["staff_id"] = sid
        items = p.get("items") if "items" in p else (old or {}).get("items") or []
        o["items"] = [{"name": _t(i.get("name"), 60), "price": _num(i.get("price")), "dur": int(_num(i.get("dur")) or 0)} for i in (items or [])[:20] if _t(i.get("name"), 60)]
        if not o["items"]:
            raise HTTPException(422, "En az bir hizmet seçin")
        o["dur"] = max(10, min(int(_num(p.get("dur")) or sum(i["dur"] for i in o["items"]) or (old or {}).get("dur") or 30), 720))
        o["discount"] = min(_num(p.get("discount", (old or {}).get("discount"))), sum(i["price"] for i in o["items"]))
        o["note"] = _t(p.get("note", (old or {}).get("note") or (old or {}).get("fault")), 600)
        src = p.get("source", (old or {}).get("source"))
        o["source"] = src if src in SOURCES else ("site" if old and not old.get("yp") else "telefon")
        return o

    async def clash(o, skip=""):
        a0 = _min(o["time"])
        a1 = a0 + o["dur"]
        for b in await db.bookings.find({"date": o["date"], "staff_id": o["staff_id"], "status": "onaylandi"}, {"_id": 0}).to_list(500):
            if b["id"] == skip or b.get("stage") not in OPEN:
                continue
            b0 = _min(b["time"])
            if a0 < b0 + int(b.get("dur") or 30) and b0 < a1:
                return b
        return None

    async def next_no():
        d = await db.app_settings.find_one_and_update({"_id": "yp_no"}, {"$inc": {"n": 1}}, upsert=True, return_document=True)
        return "RD-%d" % (1000 + int((d or {}).get("n") or 1))

    async def remember(o):
        if o.get("phone"):
            await db.yp_customers.update_one({"phone": o["phone"]}, {"$set": {"name": o["name"]}, "$setOnInsert": {"note": "", "created_at": time.time()}}, upsert=True)

    @api_router.get("/yp/appts")
    async def appts(a: str, b: str = "", _: dict = Depends(adm)):
        a = _day(a)
        b = _day(b) if b else a
        rows = await db.bookings.find({"date": {"$gte": a, "$lte": b}}, {"_id": 0}).sort([("date", 1), ("time", 1)]).to_list(5000)
        return {"rows": [view(r) for r in rows if r.get("date") and re.fullmatch(r"\d\d:\d\d", str(r.get("time") or ""))]}

    @api_router.get("/yp/requests")
    async def requests_(_: dict = Depends(adm)):
        rows = await db.bookings.find({"status": "bekliyor", "date": {"$gte": _now().date().isoformat()}}, {"_id": 0}).sort([("date", 1), ("time", 1)]).to_list(200)
        return {"rows": [view(r) for r in rows]}

    @api_router.post("/yp/appts")
    async def appt_add(payload: dict, user: dict = Depends(adm)):
        o = await clean_appt(payload)
        c = await clash(o)
        if c and not payload.get("force"):
            raise HTTPException(409, "Bu saatte %s için başka randevu var (%s %s)" % ("seçilen kişi", c.get("time"), c.get("name")))
        o.update({"id": uuid.uuid4().hex, "no": await next_no(), "yp": True, "status": "onaylandi", "stage": "bekliyor", "payments": [], "job_id": "",
                  "created_at": _now().isoformat(timespec="seconds"), "created_by": user.get("name", "")})
        await db.bookings.insert_one(dict(o))
        await remember(o)
        try:
            import eticaret_plus
            await eticaret_plus.webhook_gonder(db, "randevu.olustu", {"no": o.get("no"), "musteri": o.get("name"), "telefon": o.get("phone"), "tarih": o.get("date"), "saat": o.get("time")})
        except Exception:      # noqa: BLE001
            pass
        return view(o)

    @api_router.put("/yp/appts/{aid}")
    async def appt_put(aid: str, payload: dict, _: dict = Depends(adm)):
        old = await db.bookings.find_one({"id": aid}, {"_id": 0})
        if not old:
            raise HTTPException(404, "Randevu bulunamadı")
        o = await clean_appt(payload, old)
        paid = sum(_num(p.get("amount")) for p in old.get("payments") or [])
        if paid > sum(i["price"] for i in o["items"]) - o["discount"] + 0.001:
            raise HTTPException(422, "Alınan ödeme (%.2f ₺) yeni tutardan fazla olamaz" % paid)
        c = await clash(o, aid)
        if c and not payload.get("force"):
            raise HTTPException(409, "Bu saatte başka randevu var (%s %s)" % (c.get("time"), c.get("name")))
        if old.get("status") == "bekliyor" or not old.get("stage"):            # siteden gelen talep onaylanıyor
            o.update({"status": "onaylandi", "stage": "bekliyor", "yp": True})
            if not old.get("no"):
                o["no"] = await next_no()
        await db.bookings.update_one({"id": aid}, {"$set": o})
        await remember(o)
        return view({**old, **o})

    @api_router.post("/yp/appts/{aid}/stage")
    async def appt_stage(aid: str, payload: dict, _: dict = Depends(adm)):
        to = payload.get("to")
        if to not in STAGES:
            raise HTTPException(422, "Geçersiz durum")
        old = await db.bookings.find_one({"id": aid}, {"_id": 0})
        if not old:
            raise HTTPException(404, "Randevu bulunamadı")
        v = view(old)
        if to in ("gelmedi", "iptal") and v["paid"] > 0:
            raise HTTPException(422, "Bu randevudan ödeme alınmış; önce kasadan ödemeyi silin")
        if to in OPEN + ("tamamlandi",) and not old.get("staff_id"):
            raise HTTPException(422, "Önce randevuyu açıp kimin yapacağını ve hizmeti seçin")
        st = "onaylandi" if to in OPEN else ("tamamlandi" if to == "tamamlandi" else "iptal")
        await db.bookings.update_one({"id": aid}, {"$set": {"stage": to, "status": st, "yp": True}})
        if to == "tamamlandi" and old.get("stage") != "tamamlandi" and getattr(api_router, "uye_puan_kazan", None):
            try:
                await api_router.uye_puan_kazan(old.get("phone"), v["total"], "randevu:" + aid, "Randevu")
            except Exception:                                      # noqa: BLE001
                pass
        return view({**old, "stage": to, "status": st})

    @api_router.post("/yp/appts/{aid}/pay")
    async def appt_pay(aid: str, payload: dict, user: dict = Depends(adm)):
        old = await db.bookings.find_one({"id": aid}, {"_id": 0})
        if not old or not old.get("staff_id"):
            raise HTTPException(404, "Randevu bulunamadı")
        await need_open(_now().date().isoformat())
        v = view(old)
        amt = _num(payload.get("amount"))
        if amt <= 0:
            raise HTTPException(422, "Tutar yazın")
        if amt > v["balance"] + 0.001:
            raise HTTPException(422, "Tutar kalan borçtan fazla (%.2f ₺)" % v["balance"])
        m = payload.get("method") if payload.get("method") in METHODS else "Nakit"
        pid = uuid.uuid4().hex[:12]
        at = _now().isoformat(timespec="minutes")
        pay = {"id": pid, "amount": amt, "method": m, "at": at}
        full = amt >= v["balance"] - 0.001
        st = {"stage": "tamamlandi", "status": "tamamlandi"} if full and v["stage"] in OPEN else {}
        await db.bookings.update_one({"id": aid}, {"$push": {"payments": pay}, "$set": st} if st else {"$push": {"payments": pay}})
        await db.yp_cash.insert_one({"id": pid, "type": "in", "amount": amt, "method": m, "at": at, "desc": "%s · %s" % (old.get("name", ""), " + ".join(i["name"] for i in v["items"])),
                                     "kind": "randevu", "ref": aid, "ref_no": old.get("no", ""), "staff_id": old.get("staff_id", ""), "by": user.get("name", "")})
        return view({**old, **st, "payments": (old.get("payments") or []) + [pay]})

    # ------------------------------------------------------------------ kasa
    @api_router.get("/yp/cash")
    async def cash(a: str, b: str = "", _: dict = Depends(adm)):
        a = _day(a)
        b = _day(b) if b else a
        rows = await db.yp_cash.find({"at": {"$gte": a, "$lte": b + "T99"}}, {"_id": 0}).sort("at", -1).to_list(20000)
        open_ = [view(x) for x in await db.bookings.find({"yp": True, "status": {"$in": ["onaylandi", "tamamlandi"]}, "date": {"$lte": b}}, {"_id": 0}).to_list(20000)]
        due = [x for x in open_ if x["balance"] > 0 and x["stage"] in ("islemde", "tamamlandi")]
        return {"rows": rows, "in": round(sum(r["amount"] for r in rows if r["type"] == "in"), 2), "out": round(sum(r["amount"] for r in rows if r["type"] == "out"), 2),
                "due": round(sum(x["balance"] for x in due), 2), "due_n": len(due)}

    @api_router.post("/yp/cash")
    async def cash_add(payload: dict, user: dict = Depends(adm)):
        await need_open(_now().date().isoformat())
        amt = _num(payload.get("amount"))
        if amt <= 0:
            raise HTTPException(422, "Tutar yazın")
        desc = _t(payload.get("desc"), 120)
        if len(desc) < 2:
            raise HTTPException(422, "Ne için olduğunu yazın")
        d = {"id": uuid.uuid4().hex[:12], "type": "out" if payload.get("type") == "out" else "in", "amount": amt, "method": payload.get("method") if payload.get("method") in METHODS else "Nakit",
             "at": _now().isoformat(timespec="minutes"), "desc": desc, "kind": "elle", "ref": "", "ref_no": "", "staff_id": "", "by": user.get("name", "")}
        if payload.get("staff_id") and d["type"] == "out":                      # maaş / prim / avans ödemesi
            d["staff_id"], d["kind"] = str(payload["staff_id"])[:40], "personel"
        await db.yp_cash.insert_one(dict(d))
        return d

    async def day_closed(day):
        return await db.yp_cashclose.find_one({"day": day}, {"_id": 0})

    async def need_open(day):
        if await day_closed(day):
            raise HTTPException(409, "Bu günün kasası kapatılmış. Değiştirmek için önce Kasa bölümünden kapanışı açın.")

    @api_router.post("/yp/walkin")
    async def walkin(payload: dict, user: dict = Depends(adm)):
        """Randevusuz, mağazaya/salona gelen müşteri: hizmet + ödeme tek adımda; kayıt tamamlanmış randevu olarak kasaya işlenir."""
        now = _now()
        today = now.date().isoformat()
        await need_open(today)
        p = dict(payload)
        p["name"] = _t(p.get("name"), 80) or "Salona gelen müşteri"
        p["date"], p["time"], p["source"] = today, now.strftime("%H:%M"), "salon"
        o = await clean_appt(p)
        o.update({"id": uuid.uuid4().hex, "no": await next_no(), "yp": True, "status": "tamamlandi", "stage": "tamamlandi", "payments": [], "job_id": "", "walkin": True,
                  "created_at": now.isoformat(timespec="seconds"), "created_by": user.get("name", "")})
        total = max(sum(i["price"] for i in o["items"]) - o["discount"], 0)
        amt = _num(payload.get("amount")) if str(payload.get("amount") or "").strip() != "" else total
        if amt < 0 or amt > total + 0.001:
            raise HTTPException(422, "Alınan tutar toplamdan (%.2f ₺) fazla olamaz" % total)
        m = payload.get("method") if payload.get("method") in METHODS else "Nakit"
        if amt > 0:
            pid = uuid.uuid4().hex[:12]
            at = now.isoformat(timespec="minutes")
            o["payments"] = [{"id": pid, "amount": amt, "method": m, "at": at}]
            await db.yp_cash.insert_one({"id": pid, "type": "in", "amount": amt, "method": m, "at": at, "desc": "%s · %s" % (o["name"], " + ".join(i["name"] for i in o["items"])),
                                         "kind": "randevu", "ref": o["id"], "ref_no": o["no"], "staff_id": o["staff_id"], "by": user.get("name", "")})
        await db.bookings.insert_one(dict(o))
        await remember(o)
        return view(o)

    @api_router.put("/yp/cash/{cid}")
    async def cash_put(cid: str, payload: dict, _: dict = Depends(adm)):
        c = await db.yp_cash.find_one({"id": cid}, {"_id": 0})
        if not c:
            raise HTTPException(404, "Kayıt bulunamadı")
        await need_open(c["at"][:10])
        m = payload.get("method") if payload.get("method") in METHODS else c["method"]
        if c.get("kind") == "randevu":                                           # randevu ödemesi: tutar kalan borç sınırı içinde değişir, randevu da güncellenir
            b = await db.bookings.find_one({"id": c.get("ref")}, {"_id": 0})
            amt = _num(payload.get("amount")) if "amount" in payload else c["amount"]
            if amt <= 0:
                raise HTTPException(422, "Tutar yazın")
            if b:
                v = view(b)
                if amt > v["balance"] + c["amount"] + 0.001:
                    raise HTTPException(422, "Tutar randevu toplamından fazla olamaz")
                await db.bookings.update_one({"id": b["id"], "payments.id": cid}, {"$set": {"payments.$.amount": amt, "payments.$.method": m}})
            await db.yp_cash.update_one({"id": cid}, {"$set": {"amount": amt, "method": m}})
            return {"ok": True}
        amt = _num(payload.get("amount"))
        if amt <= 0:
            raise HTTPException(422, "Tutar yazın")
        desc = _t(payload.get("desc"), 120)
        if len(desc) < 2:
            raise HTTPException(422, "Ne için olduğunu yazın")
        await db.yp_cash.update_one({"id": cid}, {"$set": {"amount": amt, "method": m, "desc": desc, "type": "out" if payload.get("type") == "out" else "in"}})
        return {"ok": True}

    @api_router.get("/yp/cash/close")
    async def close_get(day: str = "", _: dict = Depends(adm)):
        """Günün kasa özeti (beklenen nakit) ve varsa kapanış kaydı."""
        day = _day(day) if day else _now().date().isoformat()
        rows = await db.yp_cash.find({"at": {"$gte": day, "$lte": day + "T99"}}, {"_id": 0}).to_list(20000)
        by = {}
        for r in rows:
            by[r["method"]] = round(by.get(r["method"], 0) + (r["amount"] if r["type"] == "in" else -r["amount"]), 2)
        tin = round(sum(r["amount"] for r in rows if r["type"] == "in"), 2)
        tout = round(sum(r["amount"] for r in rows if r["type"] == "out"), 2)
        return {"day": day, "in": tin, "out": tout, "net": round(tin - tout, 2), "by": by, "expected_cash": by.get("Nakit", 0), "n": len(rows), "closed": await day_closed(day)}

    @api_router.post("/yp/cash/close")
    async def close_do(payload: dict, user: dict = Depends(adm)):
        """Gün sonu: sayılan nakiti yaz, fark hesaplanır; gün kilitlenir (kapanış açılana kadar kasa değişmez)."""
        day = _day(payload.get("day")) if payload.get("day") else _now().date().isoformat()
        if await day_closed(day):
            raise HTTPException(409, "Bu gün zaten kapatılmış")
        sm = await close_get(day, None)
        raw = str(payload.get("counted") if payload.get("counted") is not None else "").strip()
        if raw == "":
            raise HTTPException(422, "Kasadaki sayılan nakit tutarını yazın")
        counted = _num(raw)
        rec = {"day": day, "in": sm["in"], "out": sm["out"], "net": sm["net"], "by_method": sm["by"], "expected_cash": sm["expected_cash"], "counted": counted,
               "diff": round(counted - sm["expected_cash"], 2), "note": _t(payload.get("note"), 300), "closed_by": user.get("name", ""), "closed_at": _now().isoformat(timespec="minutes")}
        await db.yp_cashclose.insert_one(dict(rec))
        return rec

    @api_router.delete("/yp/cash/close/{day}")
    async def close_reopen(day: str, _: dict = Depends(adm)):
        await db.yp_cashclose.delete_one({"day": _day(day)})
        return {"ok": True}

    @api_router.delete("/yp/cash/{cid}")
    async def cash_del(cid: str, _: dict = Depends(adm)):
        c = await db.yp_cash.find_one({"id": cid}, {"_id": 0})
        if not c:
            raise HTTPException(404, "Kayıt bulunamadı")
        await need_open(c["at"][:10])
        if c.get("kind") == "randevu":                                           # ödeme randevudan da düşer
            b = await db.bookings.find_one({"id": c.get("ref")}, {"_id": 0})
            if b:
                await db.bookings.update_one({"id": b["id"]}, {"$pull": {"payments": {"id": cid}}})
        await db.yp_cash.delete_one({"id": cid})
        return {"ok": True}

    # ------------------------------------------------------------------ ekip özeti (prim)
    @api_router.get("/yp/team")
    async def team(a: str, b: str, _: dict = Depends(adm)):
        a, b = _day(a), _day(b)
        st = await staff_all()
        done = [view(x) for x in await db.bookings.find({"date": {"$gte": a, "$lte": b}, "stage": "tamamlandi"}, {"_id": 0}).to_list(20000)]
        paid = await db.yp_cash.find({"kind": "personel", "at": {"$gte": a, "$lte": b + "T99"}}, {"_id": 0}).to_list(5000)
        today = _now().date().isoformat()
        tod = await db.bookings.find({"date": today, "status": {"$in": ["onaylandi", "tamamlandi"]}}, {"_id": 0, "staff_id": 1}).to_list(2000)
        out = []
        for s in st:
            mine = [x for x in done if x["staff_id"] == s["id"]]
            rev = round(sum(x["total"] for x in mine), 2)
            prim = round(rev * float(s.get("commission") or 0) / 100, 2)
            got = round(sum(p["amount"] for p in paid if p.get("staff_id") == s["id"]), 2)
            out.append({**s, "n": len(mine), "revenue": rev, "prim": prim, "paid_out": got, "payable": round(float(s.get("salary") or 0) + prim - got, 2),
                        "today": sum(1 for x in tod if x.get("staff_id") == s["id"])})
        return {"rows": out}

    # ------------------------------------------------------------------ müşteriler
    async def cust_all():
        """Müşteri başına toplanmış özet (randevulardan kendiliğinden birikir)."""
        today = _now().date().isoformat()
        cs = {c["phone"]: c for c in await db.yp_customers.find({}, {"_id": 0}).to_list(50000)}
        agg = {}
        for x in await db.bookings.find({"phone": {"$nin": ["", None]}}, {"_id": 0}).to_list(100000):
            v = view(x)
            g = agg.setdefault(v["phone"], {"phone": v["phone"], "name": v["name"], "n": 0, "spent": 0.0, "last": "", "first": "", "next": "", "noshow": 0,
                                            "cancel": 0, "balance": 0.0, "note": "", "svc": {}, "staff": {}})
            st = v["stage"]
            if st == "tamamlandi":
                g["n"] += 1
                g["spent"] = round(g["spent"] + v["paid"], 2)
                g["balance"] = round(g["balance"] + v["balance"], 2)
                g["last"] = max(g["last"], v["date"])
                g["first"] = min(g["first"] or v["date"], v["date"])
                for i in v["items"]:
                    g["svc"][i.get("name", "")] = g["svc"].get(i.get("name", ""), 0) + 1
            if st not in ("iptal", "talep") and v["staff_id"]:
                g["staff"][v["staff_id"]] = g["staff"].get(v["staff_id"], 0) + 1
            if st in ("talep", "bekliyor", "geldi", "islemde") and v["date"] >= today:
                g["next"] = min(g["next"] or v["date"], v["date"])
            if st == "gelmedi":
                g["noshow"] += 1
            if st == "iptal":
                g["cancel"] += 1
            g["name"] = v["name"] or g["name"]
        for ph, c in cs.items():
            g = agg.setdefault(ph, {"phone": ph, "name": c.get("name", ""), "n": 0, "spent": 0.0, "last": "", "first": "", "next": "", "noshow": 0,
                                    "cancel": 0, "balance": 0.0, "note": "", "svc": {}, "staff": {}})
            g["note"] = c.get("note", "")
            g["name"] = c.get("name") or g["name"]
        old = (_now().date() - timedelta(days=60)).isoformat()
        for g in agg.values():
            g["avg"] = round(g["spent"] / g["n"], 2) if g["n"] else 0
            g["fav"] = max(g["svc"], key=g["svc"].get) if g["svc"] else ""
            g["fav_staff"] = max(g["staff"], key=g["staff"].get) if g["staff"] else ""
            segs = []
            if g["n"] <= 1:
                segs.append("yeni")
            if g["n"] >= 3:
                segs.append("duzenli")
            if g["n"] and g["last"] < old and not g["next"]:
                segs.append("kayip")
            if g["balance"] > 0:
                segs.append("borc")
            if g["noshow"]:
                segs.append("gelmedi")
            if g["note"]:
                segs.append("notlu")
            if g["next"]:
                segs.append("yaklasan")
            g["segs"] = segs
        return list(agg.values())

    @api_router.get("/yp/customers")
    async def customers(q: str = "", seg: str = "", staff: str = "", svc: str = "", sort: str = "last", offset: int = 0, limit: int = 60, _: dict = Depends(adm)):
        allr = await cust_all()
        counts = {k: sum(1 for r in allr if k in r["segs"]) for k in ("yeni", "duzenli", "kayip", "borc", "gelmedi", "notlu", "yaklasan")}
        rows = allr
        q = q.strip().lower()
        if q:
            dg = re.sub(r"\D", "", q).lstrip("0")
            rows = [r for r in rows if q in r["name"].lower() or (dg and dg in r["phone"]) or q in (r.get("note") or "").lower() or any(q in k.lower() for k in r["svc"])]
        if seg:
            rows = [r for r in rows if seg in r["segs"]]
        if staff:
            rows = [r for r in rows if staff in r["staff"]]
        if svc:
            rows = [r for r in rows if svc in r["svc"]]
        keys = {"last": lambda r: (r["last"], r["name"].lower()), "spent": lambda r: (r["spent"], r["name"].lower()), "n": lambda r: (r["n"], r["name"].lower()),
                "next": lambda r: (r["next"] or "9999", r["name"].lower()), "name": lambda r: r["name"].lower()}
        rows = sorted(rows, key=keys.get(sort, keys["last"]), reverse=sort in ("last", "spent", "n"))
        offset, limit = max(offset, 0), min(max(limit, 1), 200)
        out = [{k: v for k, v in r.items() if k not in ("svc", "staff")} for r in rows[offset:offset + limit]]
        return {"rows": out, "total": len(rows), "all": len(allr), "counts": counts, "sum": {"spent": round(sum(r["spent"] for r in rows), 2), "n": sum(r["n"] for r in rows)}}

    @api_router.get("/yp/customers/{phone}")
    async def customer(phone: str, _: dict = Depends(adm)):
        ph = _phone(phone)
        c = await db.yp_customers.find_one({"phone": ph}, {"_id": 0}) or {"phone": ph, "name": "", "note": ""}
        hist = [view(x) for x in await db.bookings.find({"phone": ph}, {"_id": 0}).sort([("date", -1), ("time", -1)]).to_list(500)]
        if not c.get("name") and hist:
            c["name"] = hist[0]["name"]
        g = next((r for r in await cust_all() if r["phone"] == ph), None) or {}
        stats = {k: g.get(k) for k in ("n", "spent", "avg", "first", "last", "next", "noshow", "cancel", "balance", "fav", "fav_staff", "segs")}
        stats["svc"] = sorted(((k, v) for k, v in (g.get("svc") or {}).items() if k), key=lambda t: -t[1])[:6]
        return {"customer": c, "history": hist, "stats": stats}

    @api_router.get("/yp/appts/find")
    async def appts_find(q: str = "", a: str = "", b: str = "", stage: str = "", staff: str = "", order: str = "desc", offset: int = 0, limit: int = 80, _: dict = Depends(adm)):
        """Randevu listesi: ad/telefon/hizmet/not araması + tarih, durum, kişi süzgeçleri."""
        flt = {}
        if a or b:
            flt["date"] = {}
            if a:
                flt["date"]["$gte"] = _day(a)
            if b:
                flt["date"]["$lte"] = _day(b)
        rows = [view(r) for r in await db.bookings.find(flt, {"_id": 0}).to_list(30000) if r.get("date") and re.fullmatch(r"\d\d:\d\d", str(r.get("time") or ""))]
        q = q.strip().lower()
        if q:
            dg = re.sub(r"\D", "", q).lstrip("0")
            rows = [r for r in rows if q in r["name"].lower() or (dg and dg in r["phone"]) or q in (r["note"] or "").lower() or q in " ".join(i.get("name", "") for i in r["items"]).lower() or q in r["no"].lower()]
        grp = {"acik": ("talep", "bekliyor", "geldi", "islemde"), "tamamlandi": ("tamamlandi",), "gelmedi": ("gelmedi",), "iptal": ("iptal",)}
        if stage == "odeme":
            rows = [r for r in rows if r["stage"] == "tamamlandi" and r["balance"] > 0]
        elif stage in grp:
            rows = [r for r in rows if r["stage"] in grp[stage]]
        if staff:
            rows = [r for r in rows if r["staff_id"] == staff]
        rows.sort(key=lambda r: (r["date"], r["time"]), reverse=order != "asc")
        live = [r for r in rows if r["stage"] not in ("iptal", "gelmedi", "talep")]
        offset, limit = max(offset, 0), min(max(limit, 1), 200)
        return {"rows": rows[offset:offset + limit], "total": len(rows), "sum": {"total": round(sum(r["total"] for r in live), 2), "paid": round(sum(r["paid"] for r in live), 2),
                                                                             "balance": round(sum(r["balance"] for r in live if r["stage"] == "tamamlandi"), 2)}}

    @api_router.get("/yp/appts/{aid}")
    async def appt_one(aid: str, _: dict = Depends(adm)):
        old = await db.bookings.find_one({"id": aid}, {"_id": 0})
        if not old:
            raise HTTPException(404, "Randevu bulunamadı")
        return view(old)

    @api_router.put("/yp/customers/{phone}")
    async def customer_put(phone: str, payload: dict, _: dict = Depends(adm)):
        ph = _phone(phone)
        if not ph:
            raise HTTPException(422, "Telefon geçersiz")
        d = {"note": "\n".join(_t(l, 300) for l in str(payload.get("note") or "").split("\n"))[:2000]}
        if _t(payload.get("name"), 80):
            d["name"] = _t(payload.get("name"), 80)
        await db.yp_customers.update_one({"phone": ph}, {"$set": d, "$setOnInsert": {"created_at": time.time()}}, upsert=True)
        return {"ok": True}

    # ------------------------------------------------------------------ rapor
    @api_router.get("/yp/report")
    async def report(a: str, b: str, _: dict = Depends(adm)):
        a, b = _day(a), _day(b)
        st = {s["id"]: s for s in await staff_all()}
        allb = [view(x) for x in await db.bookings.find({"date": {"$lte": b}}, {"_id": 0}).to_list(100000)]
        rng = [x for x in allb if a <= x["date"] <= b and x["stage"] != "talep"]
        cash_ = await db.yp_cash.find({"at": {"$gte": a, "$lte": b + "T99"}}, {"_id": 0}).to_list(50000)
        first = {}
        for x in sorted(allb, key=lambda r: r["date"]):
            if x["phone"] and x["stage"] not in ("iptal", "talep"):
                first.setdefault(x["phone"], x["date"])
        seen = {x["phone"] for x in rng if x["phone"] and x["stage"] == "tamamlandi"}
        back = sum(1 for p in seen if first.get(p, a) < a)
        days = {}
        for c in cash_:
            if c["type"] == "in":
                days[c["at"][:10]] = round(days.get(c["at"][:10], 0) + c["amount"], 2)
        svc, src, per = {}, {}, {}
        for x in rng:
            if x["stage"] in ("iptal", "gelmedi"):
                continue
            src[x["source"]] = src.get(x["source"], 0) + 1
            if x["stage"] == "tamamlandi":
                for i in x["items"]:
                    g = svc.setdefault(i["name"], [0, 0.0])
                    g[0] += 1
                    g[1] = round(g[1] + i["price"], 2)
                per[x["staff_id"]] = round(per.get(x["staff_id"], 0) + x["total"], 2)
        return {"in": round(sum(c["amount"] for c in cash_ if c["type"] == "in"), 2), "out": round(sum(c["amount"] for c in cash_ if c["type"] == "out"), 2),
                "appts": sum(1 for x in rng if x["stage"] not in ("iptal",)), "noshow": sum(1 for x in rng if x["stage"] == "gelmedi"),
                "new": sum(1 for p, d in first.items() if a <= d <= b), "back": back, "seen": len(seen),
                "days": sorted(days.items()), "services": sorted(([k, v[0], v[1]] for k, v in svc.items()), key=lambda r: -r[1])[:8],
                "sources": sorted(src.items(), key=lambda r: -r[1]),
                "staff": sorted(([st.get(k, {}).get("name", "—"), v, st.get(k, {}).get("color", "#1155cc")] for k, v in per.items()), key=lambda r: -r[1])}

    # ------------------------------------------------------------------ site: herkese açık randevu
    # Siteyi gören müşteri ekibi ve hizmetleri panelden okur; boş saat kişi bazında hesaplanır (bekleyen talepler de dolu sayılır).
    hits = {}

    def limit(request, key, n, win):
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
        now = time.time()
        k = (key, ip)
        hits[k] = [t for t in hits.get(k, []) if now - t < win]
        if len(hits[k]) >= n:
            raise HTTPException(429, "Çok fazla deneme, biraz sonra tekrar deneyin")
        hits[k].append(now)

    def hm(v, d):
        try:
            return _min(_tm(v))
        except HTTPException:
            return d

    async def pub_state(pv=False):
        B = await cfg()
        staff = [r for r in await staff_all() if r.get("active", True)]
        sv = [r for r in await db.yp_services.find({}, {"_id": 0}).sort("order", 1).to_list(500) if r.get("active", True)]
        t = _now().date()
        closed = B.get("closed_weekdays") or []
        n = int(B.get("days_ahead") or 14)
        days = [(t + timedelta(days=i)).isoformat() for i in range(n + 1) if (t + timedelta(days=i)).weekday() not in closed]
        return B, staff, sv, days, bool(B.get("enabled")) or pv

    def pub_staff(r):
        return {"id": r["id"], "name": r.get("name", ""), "title": r.get("title", "")}

    def pub_service(r):
        return {"id": r["id"], "name": r.get("name", ""), "dur": int(r.get("dur") or 30), "price": r.get("price") or 0}

    @api_router.get("/public/yp/info")
    async def pub_info(request: Request, pv: int = 0):
        limit(request, "ypinfo", 120, 600)
        B, staff, sv, days, on = await pub_state(bool(pv))
        return {"enabled": on, "notice": B.get("notice") or "", "days": days if on else [], "staff": [pub_staff(r) for r in staff],
                "services": [pub_service(r) for r in sv], "start": B.get("start") or "09:00", "end": B.get("end") or "19:00"}

    async def day_state(B, staff, day):
        """Günün dolu aralıkları: kişi bazında + kişisiz (eski) kayıtlar; bekleyen talepler de dolu sayılır."""
        wd = datetime.strptime(day, "%Y-%m-%d").weekday()
        busy, anon = {}, []
        for b in await db.bookings.find({"date": day, "status": {"$in": ["bekliyor", "onaylandi"]}}, {"_id": 0}).to_list(2000):
            if b.get("stage") in ("iptal", "gelmedi") or not re.fullmatch(r"\d\d:\d\d", str(b.get("time") or "")):
                continue
            b0 = _min(b["time"])
            iv = [b0, b0 + int(b.get("dur") or 30)]
            if b.get("staff_id"):
                busy.setdefault(b["staff_id"], []).append(iv)
            else:
                anon.append(iv)
        return {"busy": busy, "anon": anon, "off": [r["id"] for r in staff if wd in (r.get("off") or [])]}

    async def free_table(B, staff, day, dur, only=""):
        """[{time, available, free:[staff_id], n}] + ham doluluk (tema kişi/hizmet seçimine göre kendisi hesaplar)."""
        s0, s1 = hm(B.get("start"), 540), hm(B.get("end"), 1080)
        step = max(15, min(int(B.get("slot_minutes") or 60), 60))
        stt = await day_state(B, staff, day)
        pool = [r["id"] for r in staff if (not only or r["id"] == only) and r["id"] not in stt["off"]] or ([] if staff else [""])
        now = _now()
        notice = int(B.get("min_notice_hours") or 0)
        out = []
        for m in range(s0, s1, step):
            if m + dur > s1:
                break
            free = [i for i in pool if not any(m < b1 and b0 < m + dur for b0, b1 in stt["busy"].get(i, []))]
            lost = sum(1 for b0, b1 in stt["anon"] if m < b1 and b0 < m + dur)
            free = free[:max(0, len(free) - lost)]
            t = "%02d:%02d" % (m // 60, m % 60)
            n = datetime.fromisoformat("%sT%s" % (day, t)) >= now + timedelta(hours=notice)
            out.append({"time": t, "available": bool(free) and n, "free": free if n else [], "n": n})
        return out, stt, s1

    def day_ok(days, day):
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(day or ""))) and day in days

    @api_router.get("/public/yp/slots")
    async def pub_slots(date: str, request: Request, dur: int = 0, staff: str = "", pv: int = 0):
        limit(request, "ypslots", 240, 600)
        B, st, _sv, days, on = await pub_state(bool(pv))
        if not on or not day_ok(days, date):
            return {"slots": []}
        rows, stt, end = await free_table(B, st, date, max(15, min(int(dur or 30), 480)), str(staff or ""))
        return {"slots": rows, "busy": stt["busy"], "anon": stt["anon"], "off": stt["off"], "end": end}

    @api_router.post("/public/yp/book")
    async def pub_book(payload: dict, request: Request):
        limit(request, "ypbook", 8, 900)
        dry = bool(payload.get("dry"))
        B, staff, sv, days, on = await pub_state(dry)
        if not on:
            raise HTTPException(400, "Online randevu şu an kapalı. Lütfen bizi arayın.")
        name = _t(payload.get("name"), 80)
        phone = _phone(payload.get("phone"))
        if len(name) < 2:
            raise HTTPException(422, "Lütfen adınızı yazın")
        if not re.fullmatch(r"[2-5]\d{9}", phone):
            raise HTTPException(422, "Lütfen geçerli bir telefon numarası girin")
        day, tm = str(payload.get("date") or ""), str(payload.get("time") or "")
        if not day_ok(days, day):
            raise HTTPException(422, "Seçilen gün uygun değil")
        _tm(tm)
        ids = [str(x) for x in (payload.get("services") or [])][:10]
        by = {r["id"]: r for r in sv}
        items = [{"name": by[i]["name"], "price": _num(by[i].get("price")), "dur": int(by[i].get("dur") or 30)} for i in ids if i in by]
        if sv and not items:
            raise HTTPException(422, "Lütfen hizmet seçin")
        dur = max(15, min(sum(i["dur"] for i in items) or 30, 480))
        want = str(payload.get("staff_id") or "")
        if want and not any(r["id"] == want for r in staff):
            raise HTTPException(422, "Seçilen kişi bulunamadı")
        slot = next((x for x in (await free_table(B, staff, day, dur, want))[0] if x["time"] == tm), None)
        if not slot or not slot["available"]:
            raise HTTPException(409, "Bu saat dolu, lütfen başka bir saat seçin")
        sid = want or (slot["free"][0] if slot["free"] else "")
        if not dry:
            doc = {"id": uuid.uuid4().hex, "name": name, "phone": phone, "date": day, "time": tm, "status": "bekliyor", "staff_id": sid, "items": items,
                   "dur": dur, "discount": 0.0, "note": _t(payload.get("note"), 600), "device_type": ", ".join(i["name"] for i in items)[:120], "source": "site",
                   "coupon": "", "job_id": "", "created_at": _now().isoformat(timespec="seconds")}
            await db.bookings.insert_one(dict(doc))
            try:
                import notify
                await notify.notify_owner_t(db, "Yeni online randevu: %s %s — %s %s" % (name, phone, day, tm), kind="booking")
            except Exception:                                      # noqa: BLE001
                pass
        return {"ok": True, "dry": dry, "message": "Randevunuz iletildi. Salon onayladığında size dönüş yapılacak.", "staff_id": sid}

