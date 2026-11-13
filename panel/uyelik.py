"""Üyelik: sektöre göre 'Hesabım' bölümleri, giriş yöntemi, KVKK, sadakat puanı, üye grupları ve üye yönetimi.
Hesaplar mevcut müşteri hesaplarıdır (customer_accounts); bu modül onların üzerine sektör ayarı, grup ve puan ekler."""
import re
import uuid
from datetime import datetime, timezone, timedelta

import asyncio
import hashlib
import secrets

import jwt
import requests
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
    "cuzdan": ("cuzdan", "Cüzdanım", "Bakiye ve hareketler"),
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
DEF = {"on": False, "zorunlu": False, "sms": False, "eposta": True, "google": False, "google_client_id": "", "kvkk": True, "puan_on": None,
       "puan_100": 10, "odul_esik": 500, "odul_oran": 10, "misafir_bagla": True,
       "cuzdan_on": False, "hatirlat_on": False, "hatirlat_gun": 3}


# sektör bölümlerine üye başına kayıt: (başlık adı, detay adı, tarih adı)
ETIKET = {"arac": ("Plaka / araç", "Servis geçmişi, notlar", "Muayene / bakım tarihi"),
          "hayvan": ("Hayvanın adı ve türü", "Aşı, reçete, notlar", "Sonraki kontrol tarihi"),
          "rezervasyon": ("Konaklama / masa", "Ayrıntı, fatura no", "Tarih"),
          "uyelik": ("Paket adı", "Kalan seans, ders programı", "Bitiş tarihi"),
          "favori": ("Favori", "Not", "Tarih"),
          "dosya": ("Dosya adı", "Durum, evrak", "Güncelleme tarihi"),
          "form": ("Form adı", "Durum", "Tarih"),
          "ders": ("Ders / sınav", "Program, ödeme planı", "Tarih"),
          "etkinlik": ("Etkinlik", "Teklif, ödeme takvimi", "Etkinlik tarihi"),
          "talep": ("Talep", "Durum, açıklama", "Tarih")}


def buton(prefix=""):
    """Sitenin sağ kenarında ortada duran Giriş yap / Hesabım sekmesi: başlık, menü ve kampanya çubuğunu örtmez."""
    return ('<style>.okuye{position:fixed;right:0;top:50%%;transform:translateY(-50%%);z-index:9400;display:flex;align-items:center;gap:6px;background:#0a1f44;color:#fff;'
            'border-radius:12px 0 0 12px;min-height:44px;padding:0 14px;font:600 13px system-ui,sans-serif;text-decoration:none;box-shadow:0 4px 18px #0a1f444d}'
            '.okuye:hover{background:#f27a1a}[dir=rtl] .okuye{right:auto;left:0;border-radius:0 12px 12px 0}'
            '@media(max-width:860px){.okuye{min-width:44px;justify-content:center;padding:0 10px}.okuye span{display:none}}</style>'
            '<a class="okuye" href="%s/hesabim" aria-label="Giriş yap / Hesabım">\U0001F464<span>Giriş yap / Hesabım</span></a>' % prefix)


def profil(sector):
    bol, puan, pa, hat, ozel = PROFIL.get(sector, GENEL)
    return {"bolumler": [dict(zip(("id", "ad", "aciklama"), B[b])) for b in bol], "puan": puan, "puan_aciklama": pa, "hatirlatma": hat, "ozel_onay": ozel}


def bolumler(c, p):
    """Sektör bölümleri; puan ve cüzdan yalnız açıksa görünür."""
    out = [x for x in p["bolumler"] if x["id"] != "puan" or c["puan_on"]]
    if c.get("cuzdan_on"):
        i = next((k for k, x in enumerate(out) if x["id"] == "bilgi"), len(out))
        out.insert(i, dict(zip(("id", "ad", "aciklama"), B["cuzdan"])))
    return out


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
        sms_hazir = bool(await db.yp_integrations.find_one({"group": "sms", "on": True, "ok": True}, {"_id": 1}))
        return {"cfg": c, "profil": p, "gruplar": GRUPLAR, "sayilar": {"uye": n, "yeni": yeni}, "sektor": sec, "sms_hazir": sms_hazir}

    @api_router.put("/yp/uyelik")
    async def ayar_put(payload: dict, _: dict = Depends(adm)):
        c, _p = await get_cfg(db, await sektor())
        for k in ("on", "zorunlu", "sms", "eposta", "google", "kvkk", "puan_on", "misafir_bagla", "cuzdan_on", "hatirlat_on"):
            if k in payload:
                c[k] = bool(payload[k])
        if "google_client_id" in payload:
            c["google_client_id"] = re.sub(r"[^A-Za-z0-9._\-]", "", str(payload["google_client_id"]))[:120]
        for k, lo, hi in (("hatirlat_gun", 1, 30), ("puan_100", 1, 1000), ("odul_esik", 10, 100000), ("odul_oran", 1, 100)):
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
                "puan": int(a.get("puan") or 0), "cuzdan": round(float(a.get("cuzdan") or 0), 2), "not": a.get("uye_notu", ""), "kayit": a.get("created_at", ""), "son": a.get("last_login", "")}

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
        if payload.get("cuzdan_ekle"):
            try:
                t = round(float(payload["cuzdan_ekle"]), 2)
            except (TypeError, ValueError):
                raise HTTPException(422, "Tutar sayı olmalı")
            t = max(-1000000, min(1000000, t))
            if float(a.get("cuzdan") or 0) + t < 0:
                raise HTTPException(422, "Bakiye eksiye düşemez")
            await db.customer_accounts.update_one({"id": aid}, {"$inc": {"cuzdan": t}})
            await db.uye_cuzdan.insert_one({"id": uuid.uuid4().hex[:12], "aid": aid, "tutar": t, "neden": str(payload.get("neden") or "Elle")[:80], "at": _now()})
        return pub(await db.customer_accounts.find_one({"id": aid}, {"_id": 0}))

    @api_router.get("/yp/uyelik/uyeler/{aid}/kayit")
    async def kayit_list(aid: str, _: dict = Depends(adm)):
        rows = [r async for r in db.uye_kayit.find({"aid": aid}, {"_id": 0}).sort("at", -1).limit(200)]
        return {"rows": rows, "etiket": {k: list(v) for k, v in ETIKET.items()}}

    @api_router.post("/yp/uyelik/uyeler/{aid}/kayit")
    async def kayit_add(aid: str, payload: dict, _: dict = Depends(adm)):
        if not await db.customer_accounts.find_one({"id": aid}, {"_id": 1}):
            raise HTTPException(404, "Üye bulunamadı")
        bolum = str(payload.get("bolum") or "")
        baslik = str(payload.get("baslik") or "").strip()[:120]
        if bolum not in ETIKET or not baslik:
            raise HTTPException(422, "Bölüm ve başlık gerekli")
        d = {"id": uuid.uuid4().hex[:12], "aid": aid, "bolum": bolum, "baslik": baslik, "detay": str(payload.get("detay") or "").strip()[:500],
             "tarih": str(payload.get("tarih") or "").strip()[:20], "at": _now()}
        await db.uye_kayit.insert_one(dict(d))
        d.pop("_id", None)
        return d

    @api_router.delete("/yp/uyelik/uyeler/{aid}/kayit/{kid}")
    async def kayit_del(aid: str, kid: str, _: dict = Depends(adm)):
        await db.uye_kayit.delete_one({"id": kid, "aid": aid})
        return {"ok": True}

    # ------------------------------------------------------------ toplu SMS
    @api_router.post("/yp/uyelik/sms")
    async def toplu_sms(payload: dict, _: dict = Depends(adm)):
        metin = str(payload.get("metin") or "").strip()[:320]
        grup = payload.get("grup") or ""
        if len(metin) < 3:
            raise HTTPException(422, "Mesaj metni yazın")
        q = {"grup": grup} if grup in GRUPLAR and grup != "Üye" else ({"$or": [{"grup": "Üye"}, {"grup": {"$exists": False}}]} if grup == "Üye" else {})
        rows = [a async for a in db.customer_accounts.find(q, {"_id": 0, "phone": 1, "name": 1, "sms_ret": 1}).limit(5000)]
        hedef = [a for a in rows if len(_pk(a.get("phone"))) >= 10 and not a.get("sms_ret")]
        if payload.get("dene"):
            return {"ok": True, "n": len(hedef), "atlanan": len(rows) - len(hedef)}
        if not await db.yp_integrations.find_one({"group": "sms", "on": True, "ok": True}, {"_id": 1}):
            raise HTTPException(422, "Önce bir SMS sağlayıcısı bağlayın (Entegrasyonlar › SMS)")
        import notify
        ok = 0
        for a in hedef:
            r = await notify.send(db, "sms", a["phone"], metin.replace("{ad}", (a.get("name") or "").split(" ")[0]), kind="uye_duyuru")
            ok += 1 if r.get("status") == "sent" else 0
        return {"ok": True, "n": len(hedef), "gonderildi": ok}

    # ------------------------------------------------------------ Excel (.xlsx) — bağımlılıksız
    @api_router.get("/yp/uyelik/export.xlsx")
    async def xlsx(_: dict = Depends(adm)):
        import io
        import zipfile
        from xml.sax.saxutils import escape
        from fastapi.responses import Response
        rows = [["Ad", "Telefon", "E-posta", "Grup", "Puan", "Cüzdan", "Kayıt tarihi"]]
        async for a in db.customer_accounts.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1):
            p = pub(a)
            rows.append([p["ad"], p["telefon"], p["eposta"], p["grup"], p["puan"], p["cuzdan"], (p["kayit"] or "")[:10]])

        def cell(v, r, c):
            ref = "%s%d" % (chr(65 + c), r + 1)
            if isinstance(v, (int, float)):
                return '<c r="%s"><v>%s</v></c>' % (ref, v)
            return '<c r="%s" t="inlineStr"><is><t>%s</t></is></c>' % (ref, escape(str(v)))
        sheet = ('<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                 + "".join('<row r="%d">%s</row>' % (i + 1, "".join(cell(v, i, j) for j, v in enumerate(r))) for i, r in enumerate(rows)) + "</sheetData></worksheet>")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
            z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
            z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Üyeler" sheetId="1" r:id="rId1"/></sheets></workbook>')
            z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            z.writestr("xl/worksheets/sheet1.xml", sheet)
        return Response(buf.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=uyeler.xlsx"})

    # ------------------------------------------------------------ favoriler (hesaba bağlı)
    @api_router.put("/public/uyelik/favori")
    async def favori(payload: dict, request: Request):
        a = await me(request)
        pid = str(payload.get("id") or "")[:60]
        if not pid:
            raise HTTPException(422, "Ürün gerekli")
        if await db.uye_favori.find_one({"aid": a["id"], "pid": pid}, {"_id": 1}):
            await db.uye_favori.delete_one({"aid": a["id"], "pid": pid})
            return {"on": False}
        await db.uye_favori.insert_one({"aid": a["id"], "pid": pid, "ad": str(payload.get("name") or "")[:120], "slug": str(payload.get("slug") or "")[:120], "at": _now()})
        return {"on": True}

    @api_router.get("/public/uyelik/favoriler")
    async def favoriler(request: Request):
        a = await me(request)
        return {"rows": [r async for r in db.uye_favori.find({"aid": a["id"]}, {"_id": 0, "aid": 0}).sort("at", -1).limit(200)]}

    # ------------------------------------------------------------ müşteriden iade talebi
    @api_router.post("/public/uyelik/iade")
    async def iade(payload: dict, request: Request):
        a = await me(request)
        no = str(payload.get("order_no") or "").strip().upper()
        o = await db.shop_orders.find_one({"order_no": no, "account_id": a["id"]}, {"_id": 0})
        if not o:
            raise HTTPException(404, "Sipariş bulunamadı")
        if o.get("status") != "teslim_edildi":
            raise HTTPException(422, "İade talebi teslim edilen siparişler için açılır")
        if await db.yp_returns.find_one({"order_no": no, "state": {"$in": ["talep", "onay", "tamam"]}}, {"_id": 1}):
            raise HTTPException(409, "Bu sipariş için zaten bir iade talebi var")
        n = await db.yp_returns.count_documents({})
        items = [{"product": "", "name": i.get("name", ""), "qty": int(i.get("qty") or 1), "price": float(i.get("price") or 0), "reason": "diger"} for i in o.get("items") or []]
        r = {"id": uuid.uuid4().hex[:12], "no": "IA-%s-%05d" % (_now()[:4], n + 1), "order": o["id"], "order_no": no,
             "customer": (o.get("customer") or {}).get("name", ""), "phone": (o.get("customer") or {}).get("phone", ""), "items": items,
             "reason": str(payload.get("reason") or "diger")[:40], "detail": str(payload.get("detail") or "")[:400], "state": "talep",
             "refund": round(sum(i["price"] * i["qty"] for i in items), 2), "cargo": "", "at": _now(), "seq": n + 1, "kaynak": "müşteri",
             "timeline": [{"at": _now(), "by": "müşteri", "state": "talep", "note": "Müşteri hesabından iade talebi"}]}
        await db.yp_returns.insert_one(dict(r))
        return {"ok": True, "no": r["no"]}

    @api_router.get("/public/uyelik/iadeler")
    async def iadeler(request: Request):
        a = await me(request)
        nos = [o["order_no"] async for o in db.shop_orders.find({"account_id": a["id"]}, {"_id": 0, "order_no": 1})]
        rows = [{k: r.get(k) for k in ("no", "order_no", "state", "refund", "at")} async for r in db.yp_returns.find({"order_no": {"$in": nos}}, {"_id": 0}).sort("at", -1)] if nos else []
        return {"rows": rows}

    # ------------------------------------------------------------ sektörel hatırlatma (tarihli kayıtlar için günlük tarama)
    async def hatirlat_tara(_db=None):
        c, p = await get_cfg(db, await sektor())
        if not (c["on"] and c.get("hatirlat_on") and p["hatirlatma"]):
            return 0
        import notify
        hedef = (datetime.now(timezone.utc) + timedelta(days=int(c.get("hatirlat_gun") or 3))).date().isoformat()
        n = 0
        async for k in db.uye_kayit.find({"tarih": hedef}, {"_id": 0}):
            ref = "uyehat:" + k["id"]
            if await db.outbox.find_one({"kind": "uye_hatirlat", "ref": ref}, {"_id": 1}):
                continue
            a = await db.customer_accounts.find_one({"id": k["aid"]}, {"_id": 0, "phone": 1, "name": 1})
            if not a or len(_pk(a.get("phone"))) < 10:
                continue
            ad = (a.get("name") or "").split(" ")[0]
            r = await notify.send(db, "sms", a["phone"], "Merhaba %s, %s tarihli \"%s\" kaydınız yaklaşıyor. Detay için hesabınıza bakabilirsiniz." % (ad, hedef[8:10] + "." + hedef[5:7], k.get("baslik", "")), kind="uye_hatirlat", ref=ref)
            n += 1 if r.get("status") == "sent" else 0
        return n
    api_router.uye_hatirlat_tara = hatirlat_tara
    try:
        import governance
        governance.HOOKS.append(hatirlat_tara)
    except Exception:                                              # noqa: BLE001
        pass

    @api_router.get("/yp/uyelik/export")
    async def disari(_: dict = Depends(adm)):
        return {"rows": [pub(a) async for a in db.customer_accounts.find({}, {"_id": 0, "password_hash": 0})]}

    def _token(a):
        return jwt.encode({"sub": a["id"], "typ": "customer", "exp": datetime.now(timezone.utc) + timedelta(days=30)}, secret, algorithm=alg)

    def _pk(p):
        return re.sub(r"\D", "", p or "")[-10:]

    async def _giris_ac(need):
        c, _p = await get_cfg(db, await sektor())
        if not (c["on"] and c[need]):
            raise HTTPException(404, "Bu giriş yöntemi kapalı")
        return c

    async def _kvkk_sart(key, payload):
        """Yeni hesap açılacaksa KVKK (ve sağlıkta özel rıza) onayı gerekir; var olan hesaba giriş etkilenmez."""
        c, p = await get_cfg(db, await sektor())
        if await db.customer_accounts.find_one({"phone_key": key}, {"_id": 1}) or not c["kvkk"]:
            return
        if not payload.get("kvkk_onay"):
            raise HTTPException(422, "Devam etmek için KVKK aydınlatma metnini onaylamalısınız.")
        if p["ozel_onay"] and not payload.get("ozel_riza"):
            raise HTTPException(422, "Sağlık verilerinizin işlenmesi için açık rıza vermelisiniz.")

    async def _hesap(key, name, phone="", email=""):
        a = await db.customer_accounts.find_one({"phone_key": key}, {"_id": 0})
        if not a:
            a = {"id": uuid.uuid4().hex[:12], "name": (name or "Üye")[:120], "phone": phone, "phone_key": key, "email": email[:120],
                 "password_hash": "", "address": "", "city": "", "district": "", "created_at": _now(), "last_login": _now()}
            await db.customer_accounts.insert_one(dict(a))
        else:
            await db.customer_accounts.update_one({"id": a["id"]}, {"$set": {"last_login": _now()}})
        return a

    def _acc(a):
        return {"id": a["id"], "name": a.get("name", ""), "phone": a.get("phone", ""), "email": a.get("email", ""), "address": a.get("address", ""),
                "city": a.get("city", ""), "district": a.get("district", ""), "created_at": a.get("created_at", "")}

    @api_router.post("/public/uyelik/sms-kod")
    async def sms_kod(payload: dict):
        await _giris_ac("sms")
        phone = str(payload.get("phone") or "").strip()[:30]
        key = _pk(phone)
        if len(key) < 10:
            raise HTTPException(422, "Lütfen geçerli bir telefon numarası girin.")
        old = await db.uye_kod.find_one({"key": key}, {"_id": 0})
        if old and old.get("at", 0) > datetime.now(timezone.utc).timestamp() - 60:
            raise HTTPException(429, "Yeni kod için bir dakika bekleyin.")
        kod = "%06d" % secrets.randbelow(1000000)
        import notify
        r = await notify.send(db, "sms", phone, "Giriş kodunuz: %s (10 dakika geçerli)" % kod, kind="uye_kod", store_text="Giriş kodunuz: ******")
        if r.get("status") != "sent":
            raise HTTPException(422, "SMS gönderilemedi. İşletmenin SMS ayarı tamamlanmamış olabilir.")
        now = datetime.now(timezone.utc).timestamp()
        await db.uye_kod.update_one({"key": key}, {"$set": {"key": key, "h": hashlib.sha256((kod + key).encode()).hexdigest(), "exp": now + 600, "at": now, "deneme": 0}}, upsert=True)
        return {"ok": True}

    @api_router.post("/public/uyelik/sms-giris")
    async def sms_giris(payload: dict):
        await _giris_ac("sms")
        phone = str(payload.get("phone") or "").strip()[:30]
        key = _pk(phone)
        kod = str(payload.get("kod") or "").strip()
        r = await db.uye_kod.find_one({"key": key}, {"_id": 0})
        now = datetime.now(timezone.utc).timestamp()
        if not r or r["exp"] < now or r.get("deneme", 0) >= 5:
            raise HTTPException(422, "Kodun süresi dolmuş. Yeni kod isteyin.")
        if hashlib.sha256((kod + key).encode()).hexdigest() != r["h"]:
            await db.uye_kod.update_one({"key": key}, {"$inc": {"deneme": 1}})
            raise HTTPException(422, "Kod hatalı.")
        await db.uye_kod.delete_one({"key": key})
        await _kvkk_sart(key, payload)
        a = await _hesap(key, str(payload.get("ad") or ""), phone)
        return {"token": _token(a), "account": _acc(a)}

    @api_router.post("/public/uyelik/google")
    async def google_giris(payload: dict):
        c = await _giris_ac("google")
        cid = c.get("google_client_id")
        if not cid:
            raise HTTPException(404, "Google girişi tamamlanmamış")
        cred = str(payload.get("credential") or "")[:4000]
        try:
            r = await asyncio.to_thread(requests.get, "https://oauth2.googleapis.com/tokeninfo", params={"id_token": cred}, timeout=10)
            d = r.json() if r.status_code == 200 else {}
        except Exception:                                          # noqa: BLE001
            d = {}
        if d.get("aud") != cid or str(d.get("email_verified")).lower() != "true" or not d.get("email"):
            raise HTTPException(401, "Google doğrulaması başarısız")
        mail = d["email"].lower()
        a = await db.customer_accounts.find_one({"email": mail}, {"_id": 0})
        if not a:
            await _kvkk_sart("g:" + str(d.get("sub") or mail), payload)
            a = await _hesap("g:" + str(d.get("sub") or mail), d.get("name") or mail.split("@")[0], "", mail)
        else:
            await db.customer_accounts.update_one({"id": a["id"]}, {"$set": {"last_login": _now()}})
        return {"token": _token(a), "account": _acc(a)}

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
        return {"on": c["on"], "zorunlu": c["zorunlu"], "yontem": {"sms": c["sms"], "eposta": c["eposta"], "google": bool(c["google"] and c.get("google_client_id"))},
                "google_client_id": c.get("google_client_id", "") if c["google"] else "",
                "kvkk": c["kvkk"], "ozel_onay": p["ozel_onay"], "puan_on": c["puan_on"], "bolumler": bolumler(c, p) if c["on"] else [], "hatirlatma": p["hatirlatma"] if c.get("hatirlat_on") else ""}

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

    @api_router.put("/public/uyelik/telefon")
    async def telefon(payload: dict, request: Request):
        """Google ile girenin telefonu yoktur; eklenince randevu ve siparişleri hesaba bağlanır, puan kazanır."""
        a = await me(request)
        phone = str(payload.get("phone") or "").strip()[:30]
        key = _pk(phone)
        if len(key) < 10:
            raise HTTPException(422, "Lütfen geçerli bir telefon numarası girin.")
        if a.get("phone") and _pk(a["phone"]) == key:
            return {"ok": True, "phone": a["phone"]}
        if await db.customer_accounts.find_one({"phone_key": key, "id": {"$ne": a["id"]}}, {"_id": 1}):
            raise HTTPException(409, "Bu telefon başka bir üyelikte kayıtlı.")
        await db.customer_accounts.update_one({"id": a["id"]}, {"$set": {"phone": phone, "phone_key": key}})
        return {"ok": True, "phone": phone}

    @api_router.get("/public/uyelik/kayitlar")
    async def kayitlar(request: Request, bolum: str = ""):
        a = await me(request)
        q = {"aid": a["id"]}
        if bolum:
            q["bolum"] = bolum
        return {"rows": [r async for r in db.uye_kayit.find(q, {"_id": 0, "aid": 0}).sort("tarih", -1).limit(100)]}

    @api_router.get("/public/uyelik/hesabim")
    async def hesabim(request: Request):
        a = await me(request)
        c, p = await get_cfg(db, await sektor())
        bol = bolumler(c, p)
        led = [{k: r[k] for k in ("puan", "neden", "at")} async for r in db.uye_puan.find({"aid": a["id"]}, {"_id": 0}).sort("at", -1).limit(20)]
        puan = int(a.get("puan") or 0)
        cled = [{k: r[k] for k in ("tutar", "neden", "at")} async for r in db.uye_cuzdan.find({"aid": a["id"]}, {"_id": 0}).sort("at", -1).limit(20)]
        return {"uye": pub(a), "bolumler": bol, "cuzdan": {"acik": c.get("cuzdan_on", False), "bakiye": round(float(a.get("cuzdan") or 0), 2), "gecmis": cled}, "puan": {"acik": c["puan_on"], "bakiye": puan, "esik": c["odul_esik"], "kalan": max(0, c["odul_esik"] - puan),
                                                      "indirim": c["odul_oran"], "gecmis": led}}
