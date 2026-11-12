# -*- coding: utf-8 -*-
"""Bildirim ve SMS şablonları: sektöre göre hazır metinler, duyuru ve stok/fiyat haberi.

Üç şey burada karara bağlanıyor:

1. **Metin müşterinin.** Her olayın sektöre uygun hazır bir metni var; müşteri
   düzenleyebilir, bozarsa hazır metne dönebilir. Değişkenler süslü parantezle
   yazılır ({ad}, {tarih}); tanınmayan değişken kaydedilmez, çünkü müşteriye
   "{musteri_adi}" diye bir mesaj gitmesi en kötü ihtimaldir.

2. **SMS'in kaç parça gideceği baştan görünür.** Türkçe karakterli mesaj GSM-7
   alfabesine sığmaz, UCS-2'ye düşer ve 160 değil 70 karakterde bir SMS yazılır.
   Bunu göstermeyen panel, müşteriye üç katı fatura çıkarır. Panel hem parça
   sayısını hem "Türkçe karakterleri sadeleştir" seçeneğini sunar.

3. **Gönderim izni ayrı.** Kampanya mesajı ticari iletidir; müşteri izni yoksa
   gönderilmez. Bilgilendirme (randevu, sipariş) izinden bağımsızdır.
"""
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

KANALLAR = [("sms", "SMS"), ("eposta", "E-posta"), ("whatsapp", "WhatsApp"), ("site", "Site bildirimi")]
TICARI = ("kampanya", "duyuru", "dogum_gunu", "tekrar_cagri", "sepet_hatirlatma", "fiyat_dustu")

# GSM-7 temel alfabesi. Buraya girmeyen bir harf varsa mesaj UCS-2'ye düşer.
GSM7 = set("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
           "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà")
GSM7_EXT = set("^{}\\[~]|€")                                       # bunlar 2 karakter sayılır
SADE = {"ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I",
        "ö": "o", "Ö": "O", "ş": "s", "Ş": "S", "ü": "u", "Ü": "U"}

# Değişkenler: olay kümesine göre hangisi doldurulabiliyorsa o gösterilir.
VARS = {
    "ortak": [("ad", "Müşterinin adı"), ("firma", "İşletme adı"), ("telefon", "Telefon"),
              ("link", "Site bağlantısı")],
    "randevu": [("tarih", "Randevu tarihi"), ("saat", "Randevu saati"), ("hizmet", "Hizmet"),
                ("personel", "İlgilenen kişi"), ("tutar", "Tutar"), ("iptal_link", "İptal bağlantısı")],
    "siparis": [("siparis_no", "Sipariş numarası"), ("tutar", "Tutar"), ("urun", "Ürünler"),
                ("kargo", "Kargo firması"), ("takip", "Takip numarası"), ("takip_link", "Kargo takip bağlantısı")],
    "stok": [("urun", "Ürün adı"), ("fiyat", "Yeni fiyat"), ("eski_fiyat", "Eski fiyat"),
             ("urun_link", "Ürün bağlantısı")],
    "uyelik": [("kod", "Doğrulama kodu"), ("uye_link", "Üyelik bağlantısı")],
    "kampanya": [("kampanya", "Kampanya adı"), ("kod", "Kupon kodu"), ("son_gun", "Son gün")],
}

# Olaylar: (id, küme, ad, açıklama, varsayılan kanallar, modül)
def E(eid, grup, ad, desc, kanal, modul, metin):
    return {"id": eid, "group": grup, "name": ad, "desc": desc, "channels": list(kanal),
            "module": modul, "texts": metin}


# Metinler akışa göre değişiyor: randevu işi "randevunuz", servis işi "servis kaydınız",
# e-ticaret "siparişiniz" der. Aynı olay, sektöre göre farklı cümle.
EVENTS = [
    E("randevu_olustu", "randevu", "Randevu alındı", "Müşteri randevu aldığı anda", ["sms"], "randevu",
      {"randevu": "{firma}: Randevunuz {tarih} {saat} icin alindi. Iyi gunler dileriz.",
       "servis": "{firma}: Servis kaydiniz olusturuldu. {tarih} {saat} icin bekliyoruz.",
       "kurs": "{firma}: {tarih} {saat} dersiniz kaydedildi."}),
    E("randevu_onay", "randevu", "Randevu onaylandı", "Talep onaylandığında", ["sms"], "randevu",
      {"randevu": "{firma}: {tarih} {saat} randevunuz onaylandi. Gorusmek uzere.",
       "servis": "{firma}: {tarih} {saat} servis randevunuz onaylandi."}),
    E("randevu_hatirlatma", "randevu", "Randevu hatırlatma", "Randevudan bir gün önce", ["sms"], "randevu",
      {"randevu": "{firma}: Yarin {saat} randevunuzu hatirlatiriz. Gelemezseniz lutfen bildirin: {telefon}",
       "servis": "{firma}: Yarin {saat} servis randevunuzu hatirlatiriz."}),
    E("randevu_iptal", "randevu", "Randevu iptal edildi", "İptal edildiğinde", ["sms"], "randevu",
      {"randevu": "{firma}: {tarih} {saat} randevunuz iptal edildi. Yeni randevu icin: {link}"}),
    E("gelmedi_takip", "randevu", "Gelmeyene not", "Randevuya gelmeyen müşteriye", [], "randevu",
      {"randevu": "{firma}: Bugunku randevunuzda sizi goremedik. Yeni gun icin bize yazabilirsiniz."}),
    E("siparis_alindi", "siparis", "Sipariş alındı", "Sipariş kaydedildiğinde", ["sms"], "siparis",
      {"eticaret": "{firma}: {siparis_no} numarali siparisiniz alindi. Tutar: {tutar} TL. Tesekkurler.",
       "lokanta": "{firma}: Siparisiniz alindi, hazirlamaya basliyoruz."}),
    E("siparis_hazir", "siparis", "Sipariş hazırlanıyor", "Hazırlığa geçildiğinde", [], "siparis",
      {"eticaret": "{firma}: {siparis_no} numarali siparisiniz hazirlaniyor.",
       "lokanta": "{firma}: Siparisiniz hazir, yola cikiyor."}),
    E("siparis_kargoda", "siparis", "Kargoya verildi", "Kargo firmasına teslim edilince", ["sms"], "siparis",
      {"eticaret": "{firma}: {siparis_no} siparisiniz {kargo} ile yola cikti. Takip no: {takip}"}),
    E("siparis_teslim", "siparis", "Teslim edildi", "Teslim edildiğinde", [], "siparis",
      {"eticaret": "{firma}: Siparisiniz teslim edildi. Begendiyseniz yorumunuzu bekleriz: {link}"}),
    E("siparis_iptal", "siparis", "Sipariş iptal edildi", "İptalde", ["sms"], "siparis",
      {"eticaret": "{firma}: {siparis_no} numarali siparisiniz iptal edildi. Odeme iadesi 1-7 is gunu icinde yapilir."}),
    E("iade_onay", "siparis", "İade onaylandı", "İade onaylandığında", ["sms"], "iade",
      {"eticaret": "{firma}: Iade talebiniz onaylandi. Odeme iadeniz baslatildi."}),
    E("odeme_bekliyor", "odeme", "Ödeme bekliyor", "Havale/EFT seçildiğinde", ["sms"], "kasa",
      {"eticaret": "{firma}: {siparis_no} siparisiniz icin {tutar} TL odeme bekliyoruz."}),
    E("odeme_alindi", "odeme", "Ödeme alındı", "Tahsilat yapıldığında", [], "kasa",
      {"randevu": "{firma}: {tutar} TL odemeniz alindi. Tesekkur ederiz.",
       "eticaret": "{firma}: {tutar} TL odemeniz alindi. Siparisiniz hazirlaniyor."}),
    E("stoga_geldi", "stok", "Stoğa gelince haber ver", "Tükenen ürün stoğa girdiğinde", ["sms"], "shop",
      {"eticaret": "{firma}: Bekledigin urun stokta: {urun}. Hemen bak: {urun_link}"}),
    E("fiyat_dustu", "stok", "Fiyat düştü", "Takip edilen ürünün fiyatı düşünce", ["sms"], "shop",
      {"eticaret": "{firma}: {urun} fiyati {eski_fiyat} TL yerine {fiyat} TL oldu. {urun_link}"}),
    E("sepet_hatirlatma", "stok", "Sepet hatırlatma", "Sepette ürün bırakıldığında", [], "shop",
      {"eticaret": "{firma}: Sepetinizde urun kaldi. Tamamlamak icin: {link}"}),
    E("hosgeldin", "uyelik", "Hoş geldiniz", "Yeni üyelikte", ["sms"], "uyelik",
      {"eticaret": "{firma}: Aramiza hos geldiniz! Ilk siparisinize ozel kod: {kod}",
       "randevu": "{firma}: Aramiza hos geldiniz."}),
    E("dogrulama", "uyelik", "Doğrulama kodu", "Giriş ve ödeme doğrulamasında", ["sms"], "uyelik",
      {"eticaret": "{firma} dogrulama kodunuz: {kod}. Kimseyle paylasmayin."}),
    E("dogum_gunu", "pazarlama", "Doğum günü", "Müşterinin doğum gününde", [], "pazarlama",
      {"randevu": "{firma}: Dogum gununuz kutlu olsun! Bu ay size ozel indirimimiz var.",
       "eticaret": "{firma}: Dogum gununuz kutlu olsun! Size ozel kod: {kod}"}),
    E("tekrar_cagri", "pazarlama", "Uzun süredir gelmeyen", "Belirlediğiniz süredir gelmeyen müşteriye", [], "pazarlama",
      {"randevu": "{firma}: Sizi ozledik. Bu ay randevularda size ozel indirim var: {link}"}),
    E("kampanya", "pazarlama", "Kampanya duyurusu", "Elle gönderilir", ["sms"], "pazarlama",
      {"randevu": "{firma}: {kampanya}. Detay ve randevu: {link}",
       "eticaret": "{firma}: {kampanya}. Son gun {son_gun}. {link}"}),
]
BY_ID = {e["id"]: e for e in EVENTS}
GROUPS = [("randevu", "Randevu"), ("siparis", "Sipariş ve kargo"), ("odeme", "Ödeme"),
          ("stok", "Stok ve fiyat"), ("uyelik", "Üyelik"), ("pazarlama", "Pazarlama")]
VAR_RE = re.compile(r"\{([a-z_]+)\}")


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


def _t(v, n):
    return " ".join(str(v or "").split())[:n]


def sadelestir(s):
    return "".join(SADE.get(ch, ch) for ch in str(s or ""))


def sms_info(text):
    """Mesaj kaç karakter, kaç SMS ve hangi alfabeyle gidecek?"""
    t = str(text or "")
    ucs = any(ch not in GSM7 and ch not in GSM7_EXT for ch in t)
    if ucs:
        n = len(t)
        per = 70 if n <= 70 else 67
    else:
        n = sum(2 if ch in GSM7_EXT else 1 for ch in t)
        per = 160 if n <= 160 else 153
    parts = 1 if n == 0 else -(-n // per)
    out = {"chars": n, "parts": parts, "encoding": "UCS-2 (Türkçe)" if ucs else "GSM-7", "per_part": per,
           "unicode": ucs, "left": max(per * parts - n, 0)}
    if ucs:
        sade = sadelestir(t)
        if not any(ch not in GSM7 and ch not in GSM7_EXT for ch in sade):
            s2 = sms_info(sade)
            out["simple"] = {"text": sade, "parts": s2["parts"], "chars": s2["chars"]}
    return out


def known_vars(eid):
    e = BY_ID.get(eid) or {}
    ks = list(VARS["ortak"])
    for k in ("randevu", "siparis", "stok", "uyelik", "kampanya"):
        if e.get("group") == k or (k == "siparis" and e.get("group") == "odeme") \
                or (k == "kampanya" and e.get("group") == "pazarlama"):
            ks += VARS[k]
    return ks


def check_text(eid, text):
    """Metni doğrula: tanınmayan değişken kaydedilmez."""
    t = _t(text, 900)
    if not t:
        raise HTTPException(422, "Mesaj metni boş olamaz")
    bilinen = {k for k, _ in known_vars(eid)}
    kotu = [v for v in VAR_RE.findall(t) if v not in bilinen]
    if kotu:
        raise HTTPException(422, "Şu değişkenler tanınmıyor: %s. Kullanılabilir: %s"
                            % (", ".join("{%s}" % k for k in sorted(set(kotu))),
                               ", ".join("{%s}" % k for k, _ in known_vars(eid))))
    return t


def render(text, data):
    """Değişkenleri doldur. Karşılığı olmayan değişken boş değil, anlaşılır kalır."""
    def rep(m):
        k = m.group(1)
        v = data.get(k)
        return str(v) if v not in (None, "") else "—"
    return VAR_RE.sub(rep, str(text or ""))


def ornek(eid, firma="Güzellik Salonu"):
    """Önizleme için gerçekçi örnek veri."""
    d = {"ad": "Mehmet Yıldız", "firma": firma, "telefon": "0212 000 00 00", "link": "onlinekaydet.com/salon",
         "tarih": "14 Kasım Cuma", "saat": "15:30", "hizmet": "Saç kesimi", "personel": "Elif",
         "tutar": "450", "iptal_link": "onlinekaydet.com/i/9fk2",
         "siparis_no": "SP-2026-00412", "urun": "Keten Gömlek", "kargo": "Aras Kargo",
         "takip": "7291043821", "takip_link": "araskargo.com.tr/7291043821",
         "fiyat": "719", "eski_fiyat": "899", "urun_link": "onlinekaydet.com/u/gomlek",
         "kod": "483921", "uye_link": "onlinekaydet.com/uye",
         "kampanya": "Tum urunlerde %20 indirim", "son_gun": "30 Kasim"}
    return d


def view(e, row, akis, modules):
    row = row or {}
    metin = row.get("text") or default_text(e, akis)
    kanal = row.get("channels") if row.get("channels") is not None else e["channels"]
    return dict({k: e[k] for k in ("id", "group", "name", "desc")},
                text=metin, channels=list(kanal), on=bool(row.get("on", bool(kanal))),
                custom=bool(row.get("text")), default=default_text(e, akis),
                vars=[{"key": k, "label": l} for k, l in known_vars(e["id"])],
                sms=sms_info(metin), available=(not e["module"] or e["module"] in modules),
                module=e["module"], ticari=e["id"] in TICARI)


# Akış adı ile metin anahtarı birebir aynı değil: "siparis" akışı e-ticaret metnini,
# "servis" ve "muayene" akışları servis metnini kullanır.
AKIS_METIN = {"siparis": "eticaret", "servis": "servis", "muayene": "servis", "dosya": "servis",
              "kursiyer": "kurs", "kayit": "kurs", "rezervasyon": "randevu", "ilan": "randevu",
              "etkinlik": "randevu", "randevu": "randevu"}


def default_text(e, akis):
    t = e["texts"]
    k = AKIS_METIN.get(akis, akis)
    return t.get(k) or t.get(akis) or t.get("randevu") or t.get("eticaret") or list(t.values())[0]


def register(api_router, db, deps):
    adm = deps["require_admin"]
    send = deps.get("send_sms")                                    # canlıda gerçek gönderim

    async def ayar():
        d = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
        sec = d.get("sector")
        if not sec:
            s = await db.app_settings.find_one({"_id": "sector"}, {"_id": 0}) or {}
            sec = s.get("key") or ""
        mods = d.get("modules")
        try:
            import blocks
            pk = blocks.pack(sec) or {}
            if mods is None:
                mods = list(pk.get("modules") or [])
            akis = pk.get("flow") or "randevu"
        except Exception:                                          # noqa: BLE001
            mods, akis = mods or [], "randevu"
        return sec, set(mods or []), akis

    async def firma_adi():
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        return g.get("company_name") or "İşletme"

    async def sms_acik():
        r = await db.yp_integrations.find_one({"group": "sms", "on": True, "ok": True}, {"_id": 0})
        return r

    @api_router.get("/yp/notify")
    async def listele(group: str = "", _: dict = Depends(adm)):
        _, mods, akis = await ayar()
        rows = {r["id"]: r for r in await db.yp_notify.find({}, {"_id": 0}).to_list(200)}
        items = [view(e, rows.get(e["id"]), akis, mods) for e in EVENTS]
        items = [i for i in items if i["available"]]
        if group:
            items = [i for i in items if i["group"] == group]
        ent = await sms_acik()
        return {"items": items, "flow": akis,
                "groups": [{"id": g, "name": n, "n": len([i for i in items if i["group"] == g])}
                           for g, n in GROUPS if any(i["group"] == g for i in items)],
                "channels": [{"id": k, "name": n} for k, n in KANALLAR],
                "sms_ready": bool(ent), "sms_provider": (ent or {}).get("id", ""),
                "counts": {"hepsi": len(items), "acik": len([i for i in items if i["on"]]),
                           "ozel": len([i for i in items if i["custom"]])}}

    @api_router.put("/yp/notify/{eid}")
    async def kaydet(eid: str, payload: dict, _: dict = Depends(adm)):
        e = BY_ID.get(_t(eid, 40))
        if not e:
            raise HTTPException(404, "Bildirim bulunamadı")
        _, mods, akis = await ayar()
        st = {"id": e["id"], "at": _now()}
        if "text" in payload:
            yeni = check_text(e["id"], payload["text"])
            st["text"] = "" if yeni == default_text(e, akis) else yeni
        if "channels" in payload:
            ks = [k for k, _ in KANALLAR]
            st["channels"] = [k for k in (payload.get("channels") or []) if k in ks]
        if "on" in payload:
            st["on"] = bool(payload["on"])
        await db.yp_notify.update_one({"id": e["id"]}, {"$set": st}, upsert=True)
        row = await db.yp_notify.find_one({"id": e["id"]}, {"_id": 0})
        return {"ok": True, "item": view(e, row, akis, mods)}

    @api_router.post("/yp/notify/{eid}/onizle")
    async def onizle(eid: str, payload: dict, _: dict = Depends(adm)):
        e = BY_ID.get(_t(eid, 40))
        if not e:
            raise HTTPException(404, "Bildirim bulunamadı")
        _, _mods, akis = await ayar()
        t = _t(payload.get("text"), 900) or default_text(e, akis)
        if payload.get("sade"):
            t = sadelestir(t)
        d = ornek(e["id"], await firma_adi())
        metin = render(t, d)
        return {"ok": True, "text": metin, "sms": sms_info(metin), "raw": t}

    @api_router.post("/yp/notify/{eid}/sifirla")
    async def sifirla(eid: str, _: dict = Depends(adm)):
        e = BY_ID.get(_t(eid, 40))
        if not e:
            raise HTTPException(404, "Bildirim bulunamadı")
        _, mods, akis = await ayar()
        await db.yp_notify.update_one({"id": e["id"]}, {"$set": {"text": "", "at": _now()}}, upsert=True)
        row = await db.yp_notify.find_one({"id": e["id"]}, {"_id": 0})
        return {"ok": True, "item": view(e, row, akis, mods)}

    # ------------------------------------------------------------ duyuru / toplu gönderim
    @api_router.get("/yp/notify/duyuru/liste")
    async def duyurular(_: dict = Depends(adm)):
        rows = await db.yp_duyuru.find({}, {"_id": 0}).to_list(200)
        rows.sort(key=lambda r: r.get("at") or "", reverse=True)
        return {"items": rows}

    @api_router.post("/yp/notify/duyuru")
    async def duyuru(payload: dict, _: dict = Depends(adm)):
        """Toplu bildirim: kime gideceğini ve kaç SMS tutacağını önce gösterir, sonra gönderir."""
        metin = _t(payload.get("text"), 900)
        if not metin:
            raise HTTPException(422, "Mesaj metni yazın")
        seg = _t(payload.get("segment"), 20) or "hepsi"
        if seg not in ("hepsi", "son90", "gelmeyen", "siparis_veren"):
            raise HTTPException(422, "Kitle seçimi geçersiz")
        kanal = _t(payload.get("channel"), 20) or "sms"
        musteri = await db.yp_customers.find({}, {"_id": 0}).to_list(20000)
        if not musteri:                                            # randevu geçmişinden türet
            gorulen = {}
            for b in await db.bookings.find({}, {"_id": 0, "phone": 1, "name": 1, "date": 1,
                                                 "sms_ok": 1}).to_list(20000):
                if b.get("phone"):
                    gorulen[b["phone"]] = {"phone": b["phone"], "name": b.get("name", ""),
                                           "last": b.get("date", ""), "sms_ok": b.get("sms_ok", True)}
            musteri = list(gorulen.values())
        bugun = _now()[:10]
        if seg == "son90":
            sinir = (datetime.now(TR) - timedelta(days=90)).date().isoformat()
            musteri = [m for m in musteri if (m.get("last") or "") >= sinir]
        elif seg == "gelmeyen":
            sinir = (datetime.now(TR) - timedelta(days=90)).date().isoformat()
            musteri = [m for m in musteri if (m.get("last") or "") < sinir]
        elif seg == "siparis_veren":
            tel = {o.get("customer", {}).get("phone") for o in
                   await db.yp_orders.find({}, {"_id": 0, "customer": 1}).to_list(20000)}
            musteri = [m for m in musteri if m.get("phone") in tel]
        izinli = [m for m in musteri if m.get("sms_ok", True) and m.get("phone")]
        bilgi = sms_info(metin)
        if payload.get("dene"):                                    # yalnız hesapla, gönderme
            return {"ok": True, "n": len(izinli), "atlanan": len(musteri) - len(izinli),
                    "sms": bilgi, "toplam_sms": len(izinli) * bilgi["parts"],
                    "ornek": render(metin, dict(ornek("kampanya", await firma_adi()),
                                                ad=(izinli[0]["name"] if izinli else "Müşteri")))}
        if not izinli:
            raise HTTPException(422, "Bu kitlede izinli müşteri yok")
        ent = await sms_acik()
        if kanal == "sms" and not ent:
            raise HTTPException(422, "Önce bir SMS sağlayıcısı bağlayın (Entegrasyonlar › SMS)")
        d = {"id": uuid.uuid4().hex[:12], "text": metin, "segment": seg, "channel": kanal,
             "n": len(izinli), "parts": bilgi["parts"], "total_sms": len(izinli) * bilgi["parts"],
             "state": "gonderiliyor", "at": _now(), "by": "panel", "sent": 0, "err": ""}
        await db.yp_duyuru.insert_one(dict(d))
        gonderildi, hata = 0, ""
        for m in izinli[:5000]:
            t = render(metin, {"ad": m.get("name") or "Müşteri", "firma": await firma_adi(),
                               "telefon": m.get("phone", ""), "link": "", "kampanya": "", "kod": "", "son_gun": ""})
            if send:
                try:
                    await send(m["phone"], t)
                    gonderildi += 1
                except Exception as x:                             # noqa: BLE001
                    hata = str(x)[:160]
            else:
                gonderildi += 1                                    # sağlayıcı yokken kuyruğa yazılır
            await db.yp_notify_log.insert_one({"id": uuid.uuid4().hex[:12], "event": "duyuru",
                                               "phone": m["phone"], "text": t, "channel": kanal,
                                               "state": "gonderildi" if not hata else "hata",
                                               "at": _now(), "duyuru": d["id"]})
        await db.yp_duyuru.update_one({"id": d["id"]}, {"$set": {
            "state": "bitti" if not hata else "hata", "sent": gonderildi, "err": hata}})
        return {"ok": True, "n": gonderildi, "toplam_sms": gonderildi * bilgi["parts"], "err": hata}

    # ------------------------------------------------------------ stoğa gelince / fiyat düştü
    @api_router.get("/yp/notify/takip")
    async def takipler(_: dict = Depends(adm)):
        rows = await db.yp_watch.find({}, {"_id": 0}).to_list(5000)
        urun = {p["id"]: p for p in await db.yp_products.find({}, {"_id": 0, "id": 1, "name": 1,
                                                                   "stock": 1, "price": 1}).to_list(20000)}
        for r in rows:
            p = urun.get(r.get("product")) or {}
            r["urun"] = p.get("name", "")
            r["stock"] = p.get("stock", 0)
            r["price"] = p.get("price", 0)
        rows.sort(key=lambda r: r.get("at") or "", reverse=True)
        return {"items": rows, "counts": {"stok": len([r for r in rows if r.get("kind") == "stok"]),
                                          "fiyat": len([r for r in rows if r.get("kind") == "fiyat"])}}

    @api_router.post("/yp/notify/takip")
    async def takip_ekle(payload: dict, _: dict = Depends(adm)):
        pid = _t(payload.get("product"), 24)
        tel = "".join(ch for ch in str(payload.get("phone") or "") if ch.isdigit())[-11:]
        kind = _t(payload.get("kind"), 10) or "stok"
        if kind not in ("stok", "fiyat"):
            raise HTTPException(422, "Takip türü stok veya fiyat olmalı")
        if not pid or len(tel) < 10:
            raise HTTPException(422, "Ürün ve telefon gerekli")
        p = await db.yp_products.find_one({"id": pid}, {"_id": 0})
        if not p:
            raise HTTPException(404, "Ürün bulunamadı")
        key = "%s|%s|%s" % (pid, tel, kind)
        await db.yp_watch.update_one({"key": key}, {"$set": {
            "key": key, "id": uuid.uuid4().hex[:12], "product": pid, "phone": tel, "kind": kind,
            "base_price": p.get("price", 0), "at": _now(), "sent": False}}, upsert=True)
        return {"ok": True}

    @api_router.post("/yp/notify/takip/calistir")
    async def takip_calistir(_: dict = Depends(adm)):
        """Stoğa giren ve fiyatı düşen ürünlerin takipçilerine haber ver."""
        n = await run_watch(db, deps)
        return {"ok": True, "n": n}

    @api_router.get("/yp/notify/log")
    async def kayit(_: dict = Depends(adm)):
        rows = await db.yp_notify_log.find({}, {"_id": 0}).to_list(500)
        rows.sort(key=lambda r: r.get("at") or "", reverse=True)
        return {"items": rows[:100]}

    return api_router


async def run_watch(db, deps=None):
    """Takip listesini gözden geçir: stoğa giren ve ucuzlayan ürünleri haber ver.

    Her takip bir kez bildirilir; müşteriye aynı ürün için ikinci kez mesaj gitmez.
    """
    send = (deps or {}).get("send_sms")
    rows = await db.yp_watch.find({"sent": {"$ne": True}}, {"_id": 0}).to_list(5000)
    g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
    firma = g.get("company_name") or "İşletme"
    sablon = {r["id"]: r for r in await db.yp_notify.find({}, {"_id": 0}).to_list(200)}
    n = 0
    for w in rows:
        p = await db.yp_products.find_one({"id": w.get("product")}, {"_id": 0})
        if not p:
            continue
        eid, data = None, None
        if w.get("kind") == "stok" and int(p.get("stock") or 0) > 0:
            eid = "stoga_geldi"
            data = {"urun": p.get("name", ""), "urun_link": "", "firma": firma}
        elif w.get("kind") == "fiyat":
            yeni, eski = float(p.get("sale_price") or p.get("price") or 0), float(w.get("base_price") or 0)
            if yeni and eski and yeni < eski:
                eid = "fiyat_dustu"
                data = {"urun": p.get("name", ""), "fiyat": ("%g" % yeni), "eski_fiyat": ("%g" % eski),
                        "urun_link": "", "firma": firma}
        if not eid:
            continue
        e = BY_ID[eid]
        row = sablon.get(eid) or {}
        if row.get("on") is False:
            continue
        metin = render(row.get("text") or default_text(e, "eticaret"), dict(data, ad="Müşteri"))
        if send:
            try:
                await send(w["phone"], metin)
            except Exception:                                      # noqa: BLE001
                continue
        await db.yp_notify_log.insert_one({"id": uuid.uuid4().hex[:12], "event": eid, "phone": w["phone"],
                                           "text": metin, "channel": "sms", "state": "gonderildi",
                                           "at": _now()})
        await db.yp_watch.update_one({"key": w["key"]}, {"$set": {"sent": True, "sent_at": _now()}})
        n += 1
    return n
