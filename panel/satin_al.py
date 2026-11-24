# -*- coding: utf-8 -*-
"""Satın alma: paket seçimi, ödeme (iyzico kartı ya da havale), ödeme sonrası firma açma/yenileme,
giriş bilgisi e-postası ve numaralı fatura belgesi.

İlkeler
1. Tutarı yalnız sunucu hesaplar: paket fiyatı yönetimdeki paketlerden, KDV satış ayarından gelir.
   Tarayıcıdan tutar kabul edilmez.
2. Ödeme iyzico'ya dönüşte sunucudan doğrulanır (durum, tutar, sipariş eşleşmesi); dönen forma güvenilmez.
3. Her sipariş yalnız bir kez işlenir (atomik durum geçişi). Aynı ödeme iki kez bildirilse tek firma açılır.
4. Ödeme alınıp firma açılamazsa sipariş "isleme_hatasi" olur, para kaybolmaz; sahip panelinden yeniden işlenir.
5. Müşteri kendi siparişini yalnız sipariş numarası + erişim kodu ile görür.
"""
import asyncio
import base64
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response

import tenant

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

DURUMLAR = {"odeme_bekliyor": "Ödeme bekliyor", "havale_bekliyor": "Havale bekleniyor", "isleniyor": "İşleniyor",
            "tamamlandi": "Tamamlandı", "basarisiz": "Ödeme başarısız", "isleme_hatasi": "Ödendi, kurulum hatası",
            "iptal": "İptal"}
AYAR0 = {"kdv": 20.0, "seri": "OK", "unvan": "", "vkn": "", "vergi_dairesi": "", "adres": "", "eposta": "",
         "site_url": "https://onlinekaydet.com", "deneme_gun": 0}
_RATE = {}


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


def _t(v, n=200):
    return " ".join(str(v or "").split())[:n]


def para(x):
    return round(float(x) + 1e-9, 2)


def tl(x):
    s = "{:,.2f}".format(float(x)).replace(",", "X").replace(".", ",").replace("X", ".")
    return s[:-3] if s.endswith(",00") else s


# ---------------------------------------------------------------- iyzico (imza ve çağrı)
def _istek(*a, **k):
    import entg_probe
    return entg_probe._istek(*a, **k)


def iyzico_cagri(anahtar, yol, govde):
    host = "api.iyzipay.com" if anahtar.get("mode") == "canli" else "sandbox-api.iyzipay.com"
    g = json.dumps(govde, ensure_ascii=False, separators=(",", ":"))
    rnd = str(int(time.time() * 1000)) + secrets.token_hex(4)
    imza = hmac.new(anahtar["secret"].encode(), (rnd + yol + g).encode(), hashlib.sha256).hexdigest()
    yetki = base64.b64encode(("apiKey:%s&randomKey:%s&signature:%s" % (anahtar["api_key"], rnd, imza)).encode()).decode()
    r = _istek("POST", "https://%s%s" % (host, yol), data=g.encode(),
               headers={"Authorization": "IYZWSv2 " + yetki, "x-iyzi-rnd": rnd, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        return r.json()
    except Exception:                                              # noqa: BLE001
        return {"status": "failure", "errorMessage": "iyzico yanıtı okunamadı (kod %s)" % getattr(r, "status_code", "?")}


# ---------------------------------------------------------------- fatura belgesi (PDF)
_FONT = None


def _font():
    global _FONT
    if _FONT:
        return _FONT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    d = os.path.dirname(__file__)
    for reg, bold in (("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
                      (os.path.join(d, "fonts", "DejaVuSans.ttf"), os.path.join(d, "fonts", "DejaVuSans-Bold.ttf"))):
        if os.path.exists(reg):
            pdfmetrics.registerFont(TTFont("OKSans", reg))
            pdfmetrics.registerFont(TTFont("OKSans-B", bold))
            _FONT = ("OKSans", "OKSans-B")
            return _FONT
    try:                                                           # sistemde yazı tipi yoksa gömülü alt küme (Türkçe karakterler bozulmasın)
        import base64
        import pdf_font
        pdfmetrics.registerFont(TTFont("OKSans", io.BytesIO(base64.b64decode(pdf_font.R))))
        pdfmetrics.registerFont(TTFont("OKSans-B", io.BytesIO(base64.b64decode(pdf_font.B))))
        _FONT = ("OKSans", "OKSans-B")
        return _FONT
    except Exception:                                              # noqa: BLE001
        pass
    _FONT = ("Helvetica", "Helvetica-Bold")
    return _FONT


def fatura_pdf(fa, ayar):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    R, B = _font()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    c.setFillColorRGB(.04, .17, .13); c.rect(0, H - 34 * mm, W, 34 * mm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1); c.setFont(B, 20); c.drawString(20 * mm, H - 18 * mm, "OnlineKaydet")
    c.setFont(R, 10); c.drawString(20 * mm, H - 25 * mm, "FATURA BELGESİ")
    c.setFont(B, 11); c.drawRightString(W - 20 * mm, H - 18 * mm, fa["no"])
    c.setFont(R, 10); c.drawRightString(W - 20 * mm, H - 25 * mm, fa["tarih"])
    y = H - 50 * mm
    c.setFillColorRGB(0, 0, 0)

    def blok(x, baslik, satirlar):
        nonlocal y
        c.setFont(B, 9); c.setFillColorRGB(.3, .35, .33); c.drawString(x, y, baslik.upper())
        c.setFillColorRGB(0, 0, 0); c.setFont(R, 10)
        yy = y - 6 * mm
        for s in satirlar:
            if s:
                for p in [s[i:i + 52] for i in range(0, len(s), 52)]:
                    c.drawString(x, yy, p); yy -= 5 * mm
        return yy
    s = ayar
    y1 = blok(20 * mm, "Satıcı", [s.get("unvan"), "VKN: %s · %s" % (s.get("vkn"), s.get("vergi_dairesi")) if s.get("vkn") else "", s.get("adres"), s.get("eposta")])
    m = fa["musteri"]
    y2 = blok(110 * mm, "Alıcı", [m.get("unvan"), "VKN/TCKN: %s · %s" % (m.get("vkn"), m.get("vd")), "%s %s" % (m.get("adres"), m.get("il")), m.get("email")])
    y = min(y1, y2) - 10 * mm
    c.setFillColorRGB(.94, .93, .9); c.rect(20 * mm, y - 2 * mm, W - 40 * mm, 8 * mm, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0); c.setFont(B, 9)
    c.drawString(22 * mm, y + 1 * mm, "Açıklama"); c.drawRightString(W - 22 * mm, y + 1 * mm, "Tutar")
    k = fa["kalem"]
    y -= 8 * mm
    c.setFont(R, 10); c.drawString(22 * mm, y, k["ad"]); c.drawRightString(W - 22 * mm, y, tl(k["matrah"]) + " ₺")
    y -= 14 * mm
    for et, v, kalin in (("Ara toplam", k["matrah"], 0), ("KDV %%%s" % tl(k["kdv_oran"]), k["kdv"], 0), ("Genel toplam", k["toplam"], 1)):
        c.setFont(B if kalin else R, 11 if kalin else 10)
        c.drawString(110 * mm, y, et); c.drawRightString(W - 22 * mm, y, tl(v) + " ₺"); y -= 6 * mm
    y -= 8 * mm
    c.setFont(R, 9); c.setFillColorRGB(.3, .35, .33)
    c.drawString(20 * mm, y, "Sipariş no: %s · Ödeme: %s" % (fa["siparis_no"], fa["odeme"]))
    y -= 5 * mm
    for satir in ("Bu belge ödeme alındığında otomatik düzenlenir. Resmî e-Arşiv faturası ayrıca düzenlenip e-posta adresinize gönderilir.",):
        c.drawString(20 * mm, y, satir)
    c.showPage(); c.save()
    return buf.getvalue()


def sure_ad(fy):
    return {"aylik": "aylık", "yillik": "yıllık", "iki_yil": "2 yıllık"}.get(fy["sure"], fy["sure"])


def sure_ay(fy):
    if fy["sure"] == "iki_yil":
        return "24 ay" + (" + %d ay hediye" % (fy.get("hediye_gun", 0) // 30 // 12 * 12) if fy.get("hediye_gun") else "")
    return "12 ay" if fy["sure"] == "yillik" else "1 ay"


# ---------------------------------------------------------------- kayıt
def register(api_router, db, deps):
    adm = deps["require_admin"]

    def M():
        return db.main()

    def owner():
        if tenant.current():
            raise HTTPException(403, "Bu işlem yalnız platform sahibi içindir")

    async def ayar():
        d = await M().app_settings.find_one({"_id": "satis"}, {"_id": 0}) or {}
        return {**AYAR0, **d}

    async def sayac(ad):
        from pymongo import ReturnDocument
        r = await M().app_settings.find_one_and_update({"_id": "sayac_" + ad}, {"$inc": {"n": 1}}, upsert=True, return_document=ReturnDocument.AFTER)
        return int(r["n"])

    async def paketler():
        import firms
        return await firms.API["packages"]()

    async def fiyat(paket, sure, a=None):
        a = a or await ayar()
        pk = (await paketler()).get(paket)
        if not pk or float(pk.get("price") or 0) <= 0:
            raise HTTPException(422, "Bu paket satın alınamıyor")
        aylik = float(pk["price"])
        yillik = float(pk.get("yearly") or 0) or aylik * 10
        matrah = para(aylik if sure == "aylik" else yillik * 2 if sure == "iki_yil" else yillik)
        gun = 30 if sure == "aylik" else 365 if sure == "yillik" else 730
        hd = None
        if sure == "iki_yil":
            import site_kampanya
            hd = await site_kampanya.hediye(db)
            if hd:
                gun += hd["gun"]
        oran = float(a["kdv"])
        kdv = para(matrah * oran / 100)
        return {"paket": paket, "paket_ad": pk.get("name") or paket, "sure": sure, "gun": gun, "hediye_gun": hd["gun"] if hd else 0, "hediye_ad": hd["ad"] if hd else "",
                "matrah": matrah, "kdv_oran": oran, "kdv": kdv, "toplam": para(matrah + kdv), "aylik": aylik, "yillik": para(yillik)}

    async def yontemler():
        import baglanti
        kart = bool(await baglanti.anahtar(db.main(), "iyzico"))
        hv = await baglanti.anahtar(db.main(), "havale")
        return {"kart": kart, "havale": ({"iban": hv["iban"], "unvan": hv["unvan"], "banka": hv.get("banka", "")} if hv else None)}

    async def olay(sid, metin):
        await M().satis_siparis.update_one({"id": sid}, {"$push": {"olaylar": {"at": _now(), "t": _t(metin, 300)}}})

    def acik(o):
        """Müşteriye dönecek sipariş görünümü (erişim kodu ve iç alanlar yok)."""
        return {"no": o["no"], "durum": o["durum"], "durum_ad": DURUMLAR.get(o["durum"], o["durum"]), "paket_ad": o["fiyat"]["paket_ad"],
                "sure": o["fiyat"]["sure"], "hediye_gun": o["fiyat"].get("hediye_gun", 0), "toplam": o["fiyat"]["toplam"], "email": o["musteri"]["email"], "yontem": o.get("yontem", ""),
                "tur": o.get("tur", "yeni"), "hata": o.get("odeme_hata", ""), "fatura_no": (o.get("fatura") or {}).get("no", ""),
                "bitis": o.get("bitis", ""), "giris": o["durum"] == "tamamlandi"}

    # ------------------------------------------------------------ herkese açık: fiyat ve yöntemler
    @api_router.get("/public/satin-al/paketler")
    async def pub_paketler():
        a = await ayar()
        out = []
        for k, v in (await paketler()).items():
            if float(v.get("price") or 0) <= 0:
                continue
            out.append({"id": k, "name": v.get("name") or k, "modules": len(v.get("modules") or []), "tagline": v.get("tagline") or "",
                        "aylik": await fiyat(k, "aylik", a), "yillik": await fiyat(k, "yillik", a), "iki_yil": await fiyat(k, "iki_yil", a)})
        import sektor
        import site_kampanya
        return {"paketler": out, "kdv": a["kdv"], "hediye": await site_kampanya.hediye(db), "yontemler": await yontemler(),
                "sektorler": [{"id": k, "ad": (v.get("name") or v.get("label") or k)} for k, v in sektor.SECTORS.items()]}

    @api_router.post("/public/satin-al/siparis")
    async def siparis_ver(payload: dict, request: Request):
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
        now = time.time()
        h = [t for t in _RATE.get(ip, []) if now - t < 3600]
        if len(h) >= 12:
            raise HTTPException(429, "Çok fazla deneme, biraz sonra tekrar deneyin")
        _RATE[ip] = h + [now]
        from leads import _norm_phone
        import sektor
        ad, firma = _t(payload.get("ad"), 80), _t(payload.get("firma"), 120)
        email = _t(payload.get("email"), 120).lower()
        tel = _norm_phone(payload.get("telefon"))
        vno = re.sub(r"\D", "", str(payload.get("vergi_no") or ""))
        if len(ad) < 2: raise HTTPException(422, "Adınızı ve soyadınızı yazın")
        if len(firma) < 2: raise HTTPException(422, "Firma adını yazın")
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email): raise HTTPException(422, "Geçerli bir e-posta yazın")
        if not tel: raise HTTPException(422, "Telefon numarası geçersiz (05xx xxx xx xx)")
        if len(vno) not in (10, 11): raise HTTPException(422, "Vergi no 10, TC kimlik no 11 haneli olmalı")
        if len(_t(payload.get("vergi_dairesi"))) < 2: raise HTTPException(422, "Vergi dairesini yazın")
        if len(_t(payload.get("adres"))) < 8: raise HTTPException(422, "Fatura adresini yazın")
        if len(_t(payload.get("il"))) < 2: raise HTTPException(422, "İli yazın")
        if payload.get("kabul") is not True: raise HTTPException(422, "Sözleşme ve aydınlatma metnini onaylayın")
        sek = str(payload.get("sektor") or "")
        if sek not in sektor.SECTORS: raise HTTPException(422, "Sektörünüzü seçin")
        if payload.get("sure") == "aylik":
            raise HTTPException(422, "En az 1 yıllık paket satın alınabilir")
        sure = payload.get("sure") if payload.get("sure") in ("yillik", "iki_yil") else "yillik"
        fy = await fiyat(str(payload.get("paket") or ""), sure)
        mevcut = await M().firms.find_one({"login_email": email, "status": {"$ne": "silindi"}}, {"_id": 0, "id": 1})
        sid = uuid.uuid4().hex
        no = "OK-%d-%06d" % (datetime.now(TR).year, await sayac("siparis"))
        o = {"id": sid, "no": no, "erisim": secrets.token_urlsafe(16), "durum": "odeme_bekliyor", "tur": "yenileme" if mevcut else "yeni",
             "firm_id": (mevcut or {}).get("id", ""), "fiyat": fy, "sektor": sek,
             "musteri": {"ad": ad, "firma": firma, "email": email, "telefon": tel, "vergi_no": vno, "vd": _t(payload.get("vergi_dairesi"), 80),
                         "adres": _t(payload.get("adres"), 240), "il": _t(payload.get("il"), 60)},
             "ip": ip, "created_at": _now(), "olaylar": [{"at": _now(), "t": "Sipariş oluşturuldu"}]}
        await M().satis_siparis.insert_one(dict(o))
        return {"no": no, "k": o["erisim"], "fiyat": fy, "yontemler": await yontemler(), "tur": o["tur"]}

    async def sip_bul(no, k):
        o = await M().satis_siparis.find_one({"no": str(no), "erisim": str(k)}, {"_id": 0})
        if not o:
            raise HTTPException(404, "Sipariş bulunamadı")
        return o

    @api_router.post("/public/satin-al/odeme")
    async def odeme_baslat(payload: dict, request: Request):
        o = await sip_bul(payload.get("no"), payload.get("k"))
        if o["durum"] not in ("odeme_bekliyor", "basarisiz", "havale_bekliyor"):
            raise HTTPException(409, "Bu sipariş için ödeme başlatılamaz (%s)" % DURUMLAR.get(o["durum"], o["durum"]))
        yon = payload.get("yontem")
        ym = await yontemler()
        if yon == "havale":
            if not ym["havale"]:
                raise HTTPException(503, "Havale bilgisi şu an tanımlı değil")
            await M().satis_siparis.update_one({"id": o["id"]}, {"$set": {"durum": "havale_bekliyor", "yontem": "havale"}})
            await olay(o["id"], "Havale seçildi")
            try:
                import baglanti
                await baglanti.bildir(M(), "siparis.havale", "Havale bekleyen sipariş: %s · %s · %s ₺" % (o["no"], o["musteri"]["firma"], tl(o["fiyat"]["toplam"])), {"no": o["no"]})
            except Exception:                                      # noqa: BLE001
                pass
            return {"yontem": "havale", "havale": ym["havale"], "aciklama": o["no"]}
        if yon != "kart":
            raise HTTPException(422, "Ödeme yöntemini seçin")
        import baglanti
        k = await baglanti.anahtar(M(), "iyzico")
        if not k:
            raise HTTPException(503, "Kartla ödeme şu an kapalı." + (" Havale ile ödeyebilirsiniz." if ym["havale"] else ""))
        a = await ayar()
        m, fy = o["musteri"], o["fiyat"]
        ad_parca = m["ad"].rsplit(" ", 1)
        ip = o.get("ip") or "85.0.0.1"
        adres = {"contactName": m["ad"], "city": m["il"], "country": "Turkey", "address": m["adres"]}
        govde = {"locale": "tr", "conversationId": o["id"], "price": "%.2f" % fy["toplam"], "paidPrice": "%.2f" % fy["toplam"], "currency": "TRY",
                 "basketId": o["no"], "paymentGroup": "PRODUCT", "callbackUrl": a["site_url"].rstrip("/") + "/api/public/satin-al/donus",
                 "enabledInstallments": [1, 2, 3, 6, 9],
                 "buyer": {"id": o["id"][:20], "name": ad_parca[0], "surname": ad_parca[1] if len(ad_parca) > 1 else ad_parca[0],
                           "gsmNumber": "+90" + m["telefon"], "email": m["email"], "identityNumber": m["vergi_no"] if len(m["vergi_no"]) == 11 else "11111111111",
                           "registrationAddress": m["adres"], "ip": ip, "city": m["il"], "country": "Turkey"},
                 "shippingAddress": adres, "billingAddress": adres,
                 "basketItems": [{"id": fy["paket"], "name": "OnlineKaydet %s (%s)" % (fy["paket_ad"], sure_ad(fy)),
                                  "category1": "Yazılım aboneliği", "itemType": "VIRTUAL", "price": "%.2f" % fy["toplam"]}]}
        r = await asyncio.to_thread(iyzico_cagri, k, "/payment/iyzipos/checkoutform/initialize/auth/ecom", govde)
        if r.get("status") != "success" or not (r.get("token") and (r.get("paymentPageUrl") or r.get("checkoutFormContent"))):
            await olay(o["id"], "iyzico başlatma hatası: %s" % _t(r.get("errorMessage"), 160))
            raise HTTPException(502, "Ödeme ekranı açılamadı: %s" % (_t(r.get("errorMessage"), 120) or "iyzico yanıt vermedi"))
        await M().satis_siparis.update_one({"id": o["id"]}, {"$set": {"iyzico_token": r["token"], "yontem": "kart", "durum": "odeme_bekliyor", "odeme_hata": ""}})
        await olay(o["id"], "Kart ödemesi başlatıldı")
        return {"yontem": "kart", "url": r.get("paymentPageUrl", ""), "form": r.get("checkoutFormContent", "")}

    @api_router.post("/public/satin-al/donus")
    async def iyzico_donus(request: Request):
        """iyzico ödeme sonrası müşteriyi buraya POST eder. Forma güvenilmez: sonuç sunucudan sorgulanır."""
        try:
            f = await request.form()
            token = str(f.get("token") or "")
        except Exception:                                          # noqa: BLE001
            token = ""
        a = await ayar()
        son = a["site_url"].rstrip("/") + "/satin-al-sonuc.html"
        o = await M().satis_siparis.find_one({"iyzico_token": token}, {"_id": 0}) if token else None
        if not o:
            return RedirectResponse(son + "?hata=1", status_code=303)
        import baglanti
        k = await baglanti.anahtar(M(), "iyzico")
        yon = son + "?no=%s&k=%s" % (o["no"], o["erisim"])
        if not k:
            await olay(o["id"], "Dönüşte iyzico bağlantısı kapalı; sonuç doğrulanamadı")
            return RedirectResponse(yon, status_code=303)
        r = await asyncio.to_thread(iyzico_cagri, k, "/payment/iyzipos/checkoutform/auth/ecom/detail",
                                    {"locale": "tr", "conversationId": o["id"], "token": token})
        try:
            ok = (r.get("status") == "success" and str(r.get("paymentStatus")).upper() == "SUCCESS"
                  and abs(float(r.get("paidPrice")) - o["fiyat"]["toplam"]) < 0.01 and str(r.get("basketId") or o["no"]) == o["no"])
        except (TypeError, ValueError):
            ok = False
        if not ok:
            hata = _t(r.get("errorMessage") or ("Ödeme tamamlanamadı" if r.get("paymentStatus") != "SUCCESS" else "Tutar uyuşmadı"), 160)
            await M().satis_siparis.update_one({"id": o["id"], "durum": {"$in": ["odeme_bekliyor", "basarisiz"]}}, {"$set": {"durum": "basarisiz", "odeme_hata": hata}})
            await olay(o["id"], "Ödeme başarısız: " + hata)
            return RedirectResponse(yon, status_code=303)
        await isle(o["id"], {"yontem": "kart", "odeme_id": str(r.get("paymentId") or "")})
        return RedirectResponse(yon, status_code=303)

    @api_router.get("/public/satin-al/durum")
    async def durum(no: str, k: str):
        return acik(await sip_bul(no, k))

    @api_router.get("/public/satin-al/fatura/{no}.pdf")
    async def fatura_indir(no: str, k: str):
        o = await sip_bul(o_no_from(no), k)
        fa = await M().satis_fatura.find_one({"siparis_id": o["id"]}, {"_id": 0})
        if not fa:
            raise HTTPException(404, "Fatura henüz düzenlenmedi")
        return Response(fatura_pdf(fa, await ayar()), media_type="application/pdf", headers={"Content-Disposition": 'inline; filename="%s.pdf"' % fa["no"]})

    def o_no_from(x):
        return x

    # ------------------------------------------------------------ ödeme sonrası işlem (tek seferlik)
    async def isle(sid, odeme):
        """Ödemesi alınmış siparişi işler: firma aç/yenile, ödeme kaydı, fatura, e-posta. Aynı sipariş iki kez işlenmez."""
        from pymongo import ReturnDocument
        o = await M().satis_siparis.find_one_and_update(
            {"id": sid, "durum": {"$in": ["odeme_bekliyor", "basarisiz", "havale_bekliyor", "isleme_hatasi"]}},
            {"$set": {"durum": "isleniyor", "odeme": odeme, "odendi_at": _now()}}, return_document=ReturnDocument.AFTER)
        if not o:
            return None
        o.pop("_id", None)
        await olay(sid, "Ödeme alındı (%s)" % odeme.get("yontem"))
        try:
            import firms
            from firms import FirmIn, FirmUp
            fy, m = o["fiyat"], o["musteri"]
            sistem = {"email": "satin-alma", "name": "Satın alma", "id": "sistem", "role": "admin"}
            sifre = ""
            if o.get("firm_id") and await M().firms.find_one({"id": o["firm_id"]}):
                f = await M().firms.find_one({"id": o["firm_id"]}, {"_id": 0})
                bugun = datetime.now(timezone.utc)
                cur = f.get("expires_at") or ""
                base = datetime.fromisoformat(cur) if cur and cur > bugun.isoformat() else bugun
                kalan = max(0, (base - bugun).days + (1 if base > bugun else 0))
                await firms.API["update"](f["id"], FirmUp(package=fy["paket"], usage_days=kalan + fy["gun"], status="aktif"), sistem)
                firm_id, tur = f["id"], "yenileme"
            else:
                sifre = secrets.token_urlsafe(9)
                yeni = await firms.API["create"](FirmIn(name=m["firma"], email=m["email"], password=sifre, contact_name=m["ad"], phone=m["telefon"],
                                                        address=("%s %s" % (m["adres"], m["il"]))[:240], tax_no=m["vergi_no"], tax_office=m["vd"],
                                                        package=fy["paket"], sector=o.get("sektor") or "", usage_days=fy["gun"]), sistem)
                firm_id, tur = yeni["id"], "yeni"
            bitis = ((await M().firms.find_one({"id": firm_id}, {"_id": 0, "expires_at": 1})) or {}).get("expires_at", "")
            await M().firm_payments.insert_one({"id": uuid.uuid4().hex[:12], "firm_id": firm_id, "amount": fy["toplam"], "method": odeme.get("yontem", "kart"),
                                                "note": "Sipariş %s" % o["no"], "extend_days": 0, "at": datetime.now(timezone.utc).isoformat()})
            fa = await fatura_olustur(o)
            await M().satis_siparis.update_one({"id": sid}, {"$set": {"durum": "tamamlandi", "firm_id": firm_id, "tur": tur, "bitis": bitis,
                                                                      "fatura": {"no": fa["no"], "at": fa["tarih"]}, "earsiv": {"durum": "bekliyor", "no": ""}}})
            await olay(sid, "Firma %s, fatura %s düzenlendi" % ("açıldı" if tur == "yeni" else "süresi uzatıldı", fa["no"]))
            await bilgi_gonder(sid, sifre)
            try:
                import baglanti
                await baglanti.bildir(M(), "siparis.odendi", "Yeni satış: %s · %s %s · %s ₺" % (o["musteri"]["firma"], fy["paket_ad"], fy["sure"], tl(fy["toplam"])),
                                      {"no": o["no"], "firma": o["musteri"]["firma"], "toplam": fy["toplam"]})
            except Exception:                                      # noqa: BLE001
                pass
        except Exception as e:                                     # noqa: BLE001
            await M().satis_siparis.update_one({"id": sid}, {"$set": {"durum": "isleme_hatasi", "isleme_hata": _t(e, 300)}})
            await olay(sid, "İşleme hatası: %s" % _t(e, 200))
            try:
                import baglanti
                await baglanti.bildir(M(), "siparis.hata", "DİKKAT: ödeme alındı ama kurulum yapılamadı: %s (%s)" % (o["no"], _t(e, 120)), {"no": o["no"]})
            except Exception:                                      # noqa: BLE001
                pass
        return await M().satis_siparis.find_one({"id": sid}, {"_id": 0})

    async def fatura_olustur(o):
        mev = await M().satis_fatura.find_one({"siparis_id": o["id"]}, {"_id": 0})
        if mev:
            return mev
        a = await ayar()
        yil = datetime.now(TR).year
        fy, m = o["fiyat"], o["musteri"]
        fa = {"id": uuid.uuid4().hex, "no": "%s%d%06d" % (a["seri"], yil, await sayac("fatura_%d" % yil)), "siparis_id": o["id"], "siparis_no": o["no"],
              "tarih": datetime.now(TR).strftime("%d.%m.%Y"), "odeme": "Kredi kartı" if (o.get("odeme") or {}).get("yontem") == "kart" else "Havale / EFT",
              "musteri": {"unvan": m["firma"], "vkn": m["vergi_no"], "vd": m["vd"], "adres": m["adres"], "il": m["il"], "email": m["email"]},
              "kalem": {"ad": "OnlineKaydet %s (%s)" % (fy["paket_ad"], sure_ay(fy)), "matrah": fy["matrah"],
                        "kdv_oran": fy["kdv_oran"], "kdv": fy["kdv"], "toplam": fy["toplam"]}, "created_at": _now()}
        await M().satis_fatura.insert_one(dict(fa))
        return fa

    async def bilgi_gonder(sid, sifre=""):
        """Müşteriye giriş bilgisi + fatura bağlantısı. Şifre kayıt defterine maskeli yazılır."""
        import notify
        o = await M().satis_siparis.find_one({"id": sid}, {"_id": 0})
        a = await ayar()
        fy, m = o["fiyat"], o["musteri"]
        link = "%s/api/public/satin-al/fatura/%s.pdf?k=%s" % (a["site_url"].rstrip("/"), o["no"], o["erisim"])
        giris = ("Giriş: %s/giris\nKullanıcı adı: %s\nŞifre: {{SIFRE}}\nİlk girişte şifrenizi değiştirmenizi öneririz." % (a["site_url"].rstrip("/"), m["email"])
                 if sifre else "Mevcut şifrenizle girmeye devam edebilirsiniz: %s/giris" % a["site_url"].rstrip("/"))
        govde = ("Merhaba %s,\n\nÖdemeniz alındı, teşekkür ederiz.\n\nPaket: %s (%s)\nTutar: %s ₺ (KDV dahil)\nSipariş no: %s\nPanel süreniz: %s\n\n%s\n\nFatura belgeniz: %s\n\nSorularınız için bu e-postaya yanıt verebilirsiniz.\n\nOnlineKaydet"
                 % (m["ad"].split(" ")[0], fy["paket_ad"], sure_ay(fy), tl(fy["toplam"]), o["no"],
                    (o.get("bitis") or "")[:10], giris, link))
        cfg = await notify.get_settings(M())
        r = await notify.send(M(), "email", m["email"], govde.replace("{{SIFRE}}", sifre), subject="OnlineKaydet siparişiniz ve giriş bilgileriniz",
                              kind="satis_bilgi", ref=o["id"], store_text=govde.replace("{{SIFRE}}", "********") if sifre else None, cfg=cfg)
        durum = r.get("status") == "sent"
        await M().satis_siparis.update_one({"id": sid}, {"$set": {"eposta_gitti": durum, "eposta_hata": "" if durum else r.get("error", "")[:200]}})
        await olay(sid, "Giriş bilgisi e-postası " + ("gönderildi" if durum else "GÖNDERİLEMEDİ: " + r.get("error", "")[:100]))
        return durum

    # ------------------------------------------------------------ sahip: siparişler ve ayarlar
    @api_router.get("/admin/satis/siparisler")
    async def sip_liste(durum: str = "", _: dict = Depends(adm)):
        owner()
        q = {"durum": durum} if durum else {}
        rows = await M().satis_siparis.find(q, {"_id": 0, "erisim": 0, "iyzico_token": 0}).sort("created_at", -1).to_list(500)
        tum = await M().satis_siparis.find({}, {"_id": 0, "durum": 1, "fiyat": 1}).to_list(20000)
        say = {}
        for r in tum:
            say[r["durum"]] = say.get(r["durum"], 0) + 1
        ciro = sum(r["fiyat"]["toplam"] for r in tum if r["durum"] == "tamamlandi")
        return {"items": rows, "sayilar": say, "ciro": para(ciro), "durumlar": DURUMLAR}

    @api_router.post("/admin/satis/siparisler/{no}/{islem}")
    async def sip_islem(no: str, islem: str, payload: dict = None, _: dict = Depends(adm)):
        owner()
        payload = payload or {}
        o = await M().satis_siparis.find_one({"no": no}, {"_id": 0})
        if not o:
            raise HTTPException(404, "Sipariş bulunamadı")
        if islem == "havale-onayla":
            if o["durum"] not in ("havale_bekliyor", "odeme_bekliyor", "basarisiz"):
                raise HTTPException(409, "Bu sipariş havale onayına uygun değil (%s)" % DURUMLAR.get(o["durum"], o["durum"]))
            r = await isle(o["id"], {"yontem": "havale", "odeme_id": _t(payload.get("referans"), 60)})
            return {"ok": bool(r and r["durum"] == "tamamlandi"), "durum": (r or {}).get("durum")}
        if islem == "yeniden-isle":
            if o["durum"] != "isleme_hatasi":
                raise HTTPException(409, "Yalnız kurulum hatası olan siparişler yeniden işlenir")
            r = await isle(o["id"], o.get("odeme") or {"yontem": "kart"})
            return {"ok": bool(r and r["durum"] == "tamamlandi"), "durum": (r or {}).get("durum"), "hata": (r or {}).get("isleme_hata", "")}
        if islem == "bilgi-gonder":
            if o["durum"] != "tamamlandi" or not o.get("firm_id"):
                raise HTTPException(409, "Sipariş henüz tamamlanmadı")
            sifre = ""
            if payload.get("yeni_sifre"):                       # şifreyi sıfırla ve e-postayla gönder
                from firms import FirmUp
                import firms
                sifre = secrets.token_urlsafe(9)
                await firms.API["update"](o["firm_id"], FirmUp(password=sifre), {"email": "satin-alma", "id": "sistem", "role": "admin"})
            return {"ok": await bilgi_gonder(o["id"], sifre)}
        if islem == "iptal":
            if o["durum"] not in ("odeme_bekliyor", "basarisiz", "havale_bekliyor"):
                raise HTTPException(409, "Ödemesi alınmış sipariş iptal edilemez")
            await M().satis_siparis.update_one({"id": o["id"]}, {"$set": {"durum": "iptal"}})
            await olay(o["id"], "Sipariş iptal edildi")
            return {"ok": True}
        if islem == "earsiv":
            if o["durum"] != "tamamlandi":
                raise HTTPException(409, "Sipariş tamamlanmadı")
            await M().satis_siparis.update_one({"id": o["id"]}, {"$set": {"earsiv": {"durum": "kesildi", "no": _t(payload.get("no"), 40), "at": _now()}}})
            await olay(o["id"], "Resmî e-Arşiv no işlendi: %s" % _t(payload.get("no"), 40))
            return {"ok": True}
        raise HTTPException(404, "Bilinmeyen işlem")

    @api_router.get("/admin/satis/fatura/{no}.pdf")
    async def sip_fatura(no: str, _: dict = Depends(adm)):
        owner()
        fa = await M().satis_fatura.find_one({"siparis_no": no}, {"_id": 0})
        if not fa:
            raise HTTPException(404, "Fatura yok")
        return Response(fatura_pdf(fa, await ayar()), media_type="application/pdf")

    @api_router.get("/admin/satis/ayar")
    async def ayar_get(_: dict = Depends(adm)):
        owner()
        return await ayar()

    @api_router.put("/admin/satis/ayar")
    async def ayar_put(payload: dict, _: dict = Depends(adm)):
        owner()
        cur = await ayar()
        try:
            kdv = float(payload.get("kdv", cur["kdv"]))
        except (TypeError, ValueError):
            raise HTTPException(422, "KDV oranı sayı olmalı")
        if not 0 <= kdv <= 40:
            raise HTTPException(422, "KDV oranı 0 ile 40 arasında olmalı")
        yeni = {"kdv": kdv}
        for k in ("seri", "unvan", "vkn", "vergi_dairesi", "adres", "eposta", "site_url"):
            if k in payload:
                yeni[k] = _t(payload[k], 240)
        if yeni.get("seri") is not None and not re.fullmatch(r"[A-Za-z0-9]{1,5}", yeni.get("seri", cur["seri"])):
            raise HTTPException(422, "Fatura serisi 1-5 harf/rakam olmalı")
        if "site_url" in yeni and not re.match(r"^https?://[^\s/]+", yeni["site_url"]):
            raise HTTPException(422, "Site adresi https:// ile başlamalı")
        await M().app_settings.update_one({"_id": "satis"}, {"$set": yeni}, upsert=True)
        return await ayar()
