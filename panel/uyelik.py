"""Üyelik: sektöre göre 'Hesabım' bölümleri, giriş yöntemi, KVKK, sadakat puanı, üye grupları ve üye yönetimi.
Hesaplar mevcut müşteri hesaplarıdır (customer_accounts); bu modül onların üzerine sektör ayarı, grup ve puan ekler."""
import re
import uuid
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import Depends, HTTPException, Request

# bölüm: (kimlik, ad, açıklama)
B = {
    "randevu": ("randevu", "Randevularım", "Yaklaşan ve geçmiş randevular, iptal / erteleme"),
    "siparis": ("siparis", "Siparişlerim", "Sipariş durumu, tekrar sipariş ver"),
    "servis": ("servis", "Servis kayıtlarım", "Cihazlarım, servis geçmişi, garanti bitişi"),
    "arac": ("arac", "Araçlarım", "Plaka, servis geçmişi, muayene ve bakım tarihi"),
    "hayvan": ("hayvan", "Evcil hayvanlarım", "Aşı takvimi, reçeteler, kontrol tarihleri"),
    "rezervasyon": ("rezervasyon", "Rezervasyonlarım", "Geçmiş konaklama / masa rezervasyonları, faturalar"),
    "uyelik": ("uyelik", "Üyelik paketim", "Paket, kalan seans, ders programı"),
    "favori": ("favori", "Favorilerim", "Favori ürünler, ilanlar ve kayıtlı aramalar"),
    "dosya": ("dosya", "Dosyalarım", "Dosya durumu, güvenli evrak yükleme, faturalar"),
    "form": ("form", "Formlarım", "Anamnez / onam formları (KVKK özel nitelikli onay)"),
    "ders": ("ders", "Derslerim", "Ders ve sınav tarihleri, ödeme planı, belgeler"),
    "etkinlik": ("etkinlik", "Etkinliklerim", "Teklifler, ödeme takvimi, galeri"),
    "talep": ("talep", "Taleplerim", "Hizmet talepleri, tekrarlayan hizmet"),
    "puan": ("puan", "Puanlarım", "Bakiye, kazanılan ve harcanan puanlar"),
    "adres": ("adres", "Adreslerim", "Adres defteri"),
    "bilgi": ("bilgi", "Bilgilerim", "Ad, telefon, şifre, hesabı sil"),
}
# paket -> (bölümler, puan var mı, puan açıklaması, hatırlatma, özel nitelikli onay)
PROFIL = {
    "kuafor": (["randevu", "puan", "bilgi"], True, "Her ziyarette puan, 10. ziyarette hediye", "Randevu hatırlatma SMS'i", False),
    "teknik": (["servis", "talep", "adres", "bilgi"], False, "", "Yıllık bakım hatırlatma", False),
    "oto": (["arac", "randevu", "puan", "bilgi"], True, "Paket kartı (10 yıkama), bakım hatırlatma", "Muayene / bakım hatırlatma", False),
    "veteriner": (["hayvan", "randevu", "bilgi"], False, "", "Aşı ve yıllık kontrol hatırlatma SMS'i", False),
    "otel": (["rezervasyon", "puan", "bilgi"], True, "Üye fiyatı, erken rezervasyon indirimi", "Giriş öncesi hatırlatma", False),
    "fitness": (["uyelik", "randevu", "puan", "bilgi"], True, "Seans kredisi, devamlılık rozeti", "Paket bitiş hatırlatma", False),
    "market": (["siparis", "adres", "favori", "puan", "bilgi"], True, "Sepet puanı, doğum günü kuponu", "", False),
    "eticaret": (["siparis", "adres", "favori", "puan", "bilgi"], True, "Sepet puanı, doğum günü kuponu", "", False),
    "lokanta": (["rezervasyon", "siparis", "favori", "puan", "bilgi"], True, "Harcamaya göre puan, hafta içi kuponu", "", False),
    "emlak": (["favori", "talep", "bilgi"], False, "", "Yeni ilan alarmı (SMS / e-posta)", False),
    "avukat": (["randevu", "dosya", "bilgi"], False, "", "Duruşma / randevu hatırlatma", False),
    "saglik": (["randevu", "form", "bilgi"], False, "", "Kontrol hatırlatma", True),
    "surucu": (["ders", "bilgi"], False, "", "Taksit ve sınav hatırlatma", False),
    "kurs": (["ders", "bilgi"], False, "", "Taksit ve sınav hatırlatma", False),
    "temizlik": (["talep", "adres", "bilgi"], True, "Düzenli hizmette indirim", "Tekrarlayan hizmet hatırlatma", False),
    "organizasyon": (["etkinlik", "bilgi"], False, "", "Ödeme takvimi hatırlatma", False),
}
GENEL = (["randevu", "siparis", "bilgi"], False, "", "", False)
GRUPLAR = ["Üye", "VIP", "Kurumsal"]
DEF = {"on": False, "zorunlu": False, "sms": True, "eposta": True, "google": False, "kvkk": True, "puan_on": None,
       "puan_100": 10, "odul_esik": 500, "odul_oran": 10, "misafir_bagla": True}


def profil(sector):
    bol, puan, pa, hat, ozel = PROFIL.get(sector, GENEL)
    return {"bolumler": [dict(zip(("id", "ad", "aciklama"), B[b])) for b in bol], "puan": puan, "puan_aciklama": pa, "hatirlatma": hat, "ozel_onay": ozel}


def _now():
    return datetime.now(timezone.utc).isoformat()


async def get_cfg(db, sector):
    d = await db.app_settings.find_one({"_id": "yp_uyelik"}, {"_id": 0}) or {}
    c = dict(DEF, **{k: v for k, v in d.items() if k in DEF})
    p = profil(sector)
    if c["puan_on"] is None:
        c["puan_on"] = p["puan"]
    if p["ozel_onay"]:
        c["kvkk"] = True
    return c, p


def register(api_router, db, deps):
    adm = deps["require_admin"]
    secret, alg = deps["JWT_SECRET"], deps["JWT_ALGORITHM"]

    async def sektor():
        d = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
        return d.get("sector") or (await db.app_settings.find_one({"_id": "sector"}, {"_id": 0}) or {}).get("key") or ""

    async def me(request: Request):
        h = request.headers.get("authorization", "")
        try:
            pl = jwt.decode(h[7:], secret, algorithms=[alg]) if h.lower().startswith("bearer ") else {}
        except Exception:                                          # noqa: BLE001
            pl = {}
        acc = await db.customer_accounts.find_one({"id": pl.get("sub")}, {"_id": 0}) if pl.get("typ") == "customer" else None
        if not acc:
            raise HTTPException(401, "Giriş yapmanız gerekiyor")
        return acc

    @api_router.get("/yp/uyelik")
    async def ayar_get(_: dict = Depends(adm)):
        sec = await sektor()
        c, p = await get_cfg(db, sec)
        n = await db.customer_accounts.count_documents({})
        ay = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        yeni = await db.customer_accounts.count_documents({"created_at": {"$gte": ay}})
        return {"cfg": c, "profil": p, "gruplar": GRUPLAR, "sayilar": {"uye": n, "yeni": yeni}, "sektor": sec}

    @api_router.put("/yp/uyelik")
    async def ayar_put(payload: dict, _: dict = Depends(adm)):
        c, _p = await get_cfg(db, await sektor())
        for k in ("on", "zorunlu", "sms", "eposta", "google", "kvkk", "puan_on", "misafir_bagla"):
            if k in payload:
                c[k] = bool(payload[k])
        for k, lo, hi in (("puan_100", 1, 1000), ("odul_esik", 10, 100000), ("odul_oran", 1, 100)):
            if k in payload:
                try:
                    c[k] = max(lo, min(hi, int(payload[k])))
                except (TypeError, ValueError):
                    pass
        if not (c["sms"] or c["eposta"] or c["google"]):
            c["eposta"] = True
        await db.app_settings.update_one({"_id": "yp_uyelik"}, {"$set": c}, upsert=True)
        if c["on"]:                                                # kayıt/giriş uçları üyelik açılınca çalışsın
            await db.app_settings.update_one({"_id": "site_features"}, {"$set": {"customer_portal_enabled": True}}, upsert=True)
        return c

    def pub(a):
        return {"id": a["id"], "ad": a.get("name", ""), "telefon": a.get("phone", ""), "eposta": a.get("email", ""), "grup": a.get("grup") or "Üye",
                "puan": int(a.get("puan") or 0), "not": a.get("uye_notu", ""), "kayit": a.get("created_at", ""), "son": a.get("last_login", "")}

    @api_router.get("/yp/uyelik/uyeler")
    async def uyeler(q: str = "", _: dict = Depends(adm)):
        rows = [pub(a) async for a in db.customer_accounts.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).limit(500)]
        q = q.strip().lower()
        if q:
            rows = [r for r in rows if q in (r["ad"] + " " + r["telefon"] + " " + r["eposta"]).lower()]
        return {"rows": rows}

    @api_router.put("/yp/uyelik/uyeler/{aid}")
    async def uye_put(aid: str, payload: dict, _: dict = Depends(adm)):
        a = await db.customer_accounts.find_one({"id": aid}, {"_id": 0})
        if not a:
            raise HTTPException(404, "Üye bulunamadı")
        s = {}
        if payload.get("grup") in GRUPLAR:
            s["grup"] = payload["grup"]
        if "not" in payload:
            s["uye_notu"] = str(payload["not"])[:500]
        if s:
            await db.customer_accounts.update_one({"id": aid}, {"$set": s})
        if payload.get("puan_ekle"):
            try:
                n = int(payload["puan_ekle"])
            except (TypeError, ValueError):
                raise HTTPException(422, "Puan sayı olmalı")
            n = max(-100000, min(100000, n))
            await db.customer_accounts.update_one({"id": aid}, {"$inc": {"puan": n}})
            await db.uye_puan.insert_one({"id": uuid.uuid4().hex[:12], "aid": aid, "puan": n, "neden": str(payload.get("neden") or "Elle")[:80], "at": _now()})
        return pub(await db.customer_accounts.find_one({"id": aid}, {"_id": 0}))

    @api_router.get("/yp/uyelik/export")
    async def disari(_: dict = Depends(adm)):
        return {"rows": [pub(a) async for a in db.customer_accounts.find({}, {"_id": 0, "password_hash": 0})]}

    async def puan_kazan(phone, tutar, ref, neden="Alışveriş"):
        """Tamamlanan randevu/siparişten üyeye puan: 100 ₺ başına ayarlı puan. Aynı kayıt iki kez puan vermez."""
        c, _p = await get_cfg(db, await sektor())
        if not (c["on"] and c["puan_on"]) or not phone:
            return 0
        d = re.sub(r"\D", "", str(phone))
        a = await db.customer_accounts.find_one({"phone_key": d[-10:]}, {"_id": 0, "id": 1}) if len(d) >= 10 else None
        n = int(float(tutar or 0) / 100 * c["puan_100"])
        if not a or n <= 0 or await db.uye_puan.find_one({"ref": ref}, {"_id": 1}):
            return 0
        await db.customer_accounts.update_one({"id": a["id"]}, {"$inc": {"puan": n}})
        await db.uye_puan.insert_one({"id": uuid.uuid4().hex[:12], "aid": a["id"], "puan": n, "neden": neden, "ref": ref, "at": _now()})
        return n
    api_router.uye_puan_kazan = puan_kazan

    @api_router.get("/public/uyelik")
    async def acik_ayar():
        c, p = await get_cfg(db, await sektor())
        return {"on": c["on"], "zorunlu": c["zorunlu"], "yontem": {"sms": c["sms"], "eposta": c["eposta"], "google": c["google"]},
                "kvkk": c["kvkk"], "ozel_onay": p["ozel_onay"], "puan_on": c["puan_on"], "bolumler": [x for x in p["bolumler"] if x["id"] != "puan" or c["puan_on"]] if c["on"] else []}

    @api_router.get("/public/uyelik/randevular")
    async def randevular(request: Request):
        a = await me(request)
        key = re.sub(r"\D", "", a.get("phone") or "")[-10:]
        out = []
        if len(key) >= 10:
            async for b in db.bookings.find({}, {"_id": 0}).sort("date", -1).limit(3000):
                if re.sub(r"\D", "", b.get("phone") or "")[-10:] == key:
                    out.append({"id": b.get("id"), "no": b.get("no", ""), "tarih": b.get("date", ""), "saat": b.get("time", ""),
                                "hizmet": ", ".join(str(i.get("name", "")) for i in (b.get("items") or []) if i.get("name")) or b.get("service", "") or "",
                                "durum": b.get("stage") or b.get("status") or ""})
                    if len(out) >= 50:
                        break
        return {"rows": out}

    @api_router.get("/public/uyelik/hesabim")
    async def hesabim(request: Request):
        a = await me(request)
        c, p = await get_cfg(db, await sektor())
        bol = [x for x in p["bolumler"] if x["id"] != "puan" or c["puan_on"]]
        led = [{k: r[k] for k in ("puan", "neden", "at")} async for r in db.uye_puan.find({"aid": a["id"]}, {"_id": 0}).sort("at", -1).limit(20)]
        puan = int(a.get("puan") or 0)
        return {"uye": pub(a), "bolumler": bol, "puan": {"acik": c["puan_on"], "bakiye": puan, "esik": c["odul_esik"], "kalan": max(0, c["odul_esik"] - puan),
                                                      "indirim": c["odul_oran"], "gecmis": led}}
