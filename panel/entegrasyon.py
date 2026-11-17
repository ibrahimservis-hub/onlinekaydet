# -*- coding: utf-8 -*-
"""Entegrasyon merkezi: sanal POS, kargo, e-fatura, ERP, SMS, pazaryeri ve ölçüm.

Üç kural üzerine kurulu:

1. **Sahip izin verir, müşteri bağlar.** Panelde yalnız sektör paketinde olan ve
   sahibin açık bıraktığı entegrasyonlar görünür. Müşteri kendi anahtarını kendi
   girer; destek hattına anahtar göndermez.
2. **Anahtar geri dönmez.** Kaydedilen gizli alanlar hiçbir uçta düz metin olarak
   okunmaz; panele yalnız maskelenmiş hâli (••••3821) gider. Boş gönderilen gizli
   alan "değiştirme" demektir, silme demek değildir.
3. **Bağlandı demek, çalışıyor demek değil.** Her entegrasyonun kendi denemesi
   vardır; deneme yapılmadan "bağlı" yazılmaz, deneme hatası son hata olarak
   saklanır ve panelde sebebiyle görünür.
"""
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

GROUPS = [("pos", "Sanal POS ve ödeme", "Kredi kartıyla tahsilat"),
          ("kargo", "Kargo", "Gönderi oluşturma ve takip"),
          ("efatura", "e-Fatura / e-Arşiv", "Fatura kesme ve GİB'e iletme"),
          ("erp", "Muhasebe ve ERP", "Stok, cari ve fatura aktarımı"),
          ("sms", "SMS ve bildirim", "Randevu, sipariş ve kampanya mesajları"),
          ("pazaryeri", "Pazaryeri", "Ürün, sipariş ve stok senkronu"),
          ("olcum", "Ölçüm ve reklam", "Ziyaretçi ve dönüşüm takibi"),
          ("diger", "Diğer", "")]

# F: alan tanımı. gizli=True olan alan panele asla düz metin dönmez.
def F(key, label, gizli=False, zorunlu=True, ipucu="", tip="text"):
    return {"key": key, "label": label, "secret": gizli, "required": zorunlu, "hint": ipucu, "type": tip}


API = [F("api_key", "API anahtarı", True), F("api_secret", "API gizli anahtarı", True)]
MAGAZA = API + [F("seller_id", "Satıcı / mağaza numarası")]
SMSF = [F("user", "Kullanıcı adı"), F("pass", "Şifre", True), F("header", "Mesaj başlığı (gönderici adı)")]
POSF = [F("merchant", "Üye iş yeri numarası"), F("api_key", "API anahtarı", True),
        F("api_secret", "Gizli anahtar", True),
        F("taksit", "Taksit sayısı", zorunlu=False, ipucu="Boş bırakırsanız tek çekim", tip="number")]
BANKA = [F("merchant", "Üye iş yeri numarası"), F("terminal", "Terminal numarası"),
         F("user", "Mağaza kullanıcı adı"), F("pass", "Mağaza şifresi", True),
         F("3d_key", "3D Secure anahtarı", True, zorunlu=False)]
KARGOF = [F("user", "Müşteri / kullanıcı kodu"), F("pass", "Şifre", True),
          F("musteri_no", "Müşteri numarası", zorunlu=False),
          F("odeme", "Ödeme şekli", zorunlu=False, ipucu="gonderici / alici")]
EFAT = [F("user", "Kullanıcı adı"), F("pass", "Şifre", True),
        F("vkn", "VKN / TCKN", ipucu="Faturayı kesen firmanın vergi numarası"),
        F("seri", "Fatura seri kodu", zorunlu=False, ipucu="Örnek: ONK")]
ERPF = [F("url", "Sunucu adresi", ipucu="Örnek: https://erp.firmaniz.com"),
        F("user", "Kullanıcı adı"), F("pass", "Şifre", True),
        F("sube", "Şube / depo kodu", zorunlu=False)]


def P(pid, group, name, fields, desc="", hint="", test=True):
    return {"id": pid, "group": group, "name": name, "fields": fields, "desc": desc,
            "hint": hint, "can_test": test}


CATALOG = [
    # --- sanal POS
    P("iyzico", "pos", "iyzico", POSF, "Kartla tahsilat, taksit ve iade",
      "Anahtarları iyzico panelinde Ayarlar › API anahtarları bölümünden alırsınız."),
    P("paytr", "pos", "PayTR", [F("merchant", "Mağaza numarası"), F("api_key", "Mağaza anahtarı", True),
                                F("api_secret", "Mağaza gizli anahtarı", True),
                                F("taksit", "Taksit sayısı", zorunlu=False, tip="number")],
      "Kartla tahsilat ve taksit"),
    P("param", "pos", "Param", POSF, "Kartla tahsilat"),
    P("sipay", "pos", "Sipay", POSF, "Kartla tahsilat ve taksit"),
    P("craftgate", "pos", "Craftgate", POSF, "Çoklu banka yönlendirme"),
    P("banka_pos", "pos", "Banka sanal POS'u", BANKA,
      "Garanti, İş Bankası, Yapı Kredi, Akbank, Ziraat, Halkbank, QNB, Deniz, Vakıf, Kuveyt Türk, Albaraka, TEB",
      "Bankanızın verdiği üye iş yeri ve terminal bilgilerini girin; sanal POS türünü biz seçeriz."),
    P("havale", "pos", "Havale / EFT", [F("iban", "IBAN"), F("unvan", "Hesap sahibi"),
                                        F("banka", "Banka adı", zorunlu=False)],
      "Müşteri havaleyle öderse hesap bilgileri ödeme ekranında görünür", test=False),
    P("kapida", "pos", "Kapıda ödeme", [F("ucret", "Kapıda ödeme ücreti", zorunlu=False, tip="number")],
      "Nakit veya kartla kapıda tahsilat", test=False),
    # --- kargo
    P("aras", "kargo", "Aras Kargo", KARGOF, "Gönderi oluşturma, barkod ve takip"),
    P("yurtici", "kargo", "Yurtiçi Kargo", KARGOF, "Gönderi oluşturma, barkod ve takip"),
    P("mng", "kargo", "MNG Kargo", KARGOF, "Gönderi oluşturma ve takip"),
    P("ptt", "kargo", "PTT Kargo", KARGOF, "Gönderi oluşturma ve takip"),
    P("surat", "kargo", "Sürat Kargo", KARGOF, "Gönderi oluşturma ve takip"),
    P("ups", "kargo", "UPS", KARGOF, "Yurt içi ve yurt dışı gönderi"),
    P("sendeo", "kargo", "Sendeo", KARGOF, "Gönderi oluşturma ve takip"),
    P("hepsijet", "kargo", "HepsiJET", KARGOF, "Gönderi oluşturma ve takip"),
    P("kolaygelsin", "kargo", "Kolay Gelsin", KARGOF, "Gönderi oluşturma ve takip"),
    # --- e-fatura
    P("parasut", "efatura", "Paraşüt", [F("client_id", "Uygulama kimliği"), F("client_secret", "Uygulama gizli anahtarı", True),
                                        F("user", "E-posta"), F("pass", "Şifre", True),
                                        F("firma_no", "Firma numarası")],
      "e-Arşiv, e-Fatura ve ön muhasebe"),
    P("birfatura", "efatura", "BirFatura", API, "e-Arşiv ve e-Fatura"),
    P("uyumsoft", "efatura", "Uyumsoft", EFAT, "e-Fatura ve e-Arşiv"),
    P("izibiz", "efatura", "İzibiz", EFAT, "e-Fatura ve e-Arşiv"),
    P("nes", "efatura", "NES Bilgi", EFAT, "e-Fatura ve e-Arşiv"),
    P("edm", "efatura", "EDM Bilişim", EFAT, "e-Fatura ve e-Arşiv"),
    P("qnb_efinans", "efatura", "QNB eFinans", EFAT, "e-Fatura ve e-Arşiv"),
    P("gib_earsiv", "efatura", "GİB e-Arşiv portalı",
      [F("vkn", "VKN / TCKN"), F("pass", "İnteraktif VD şifresi", True)],
      "Portal üzerinden e-Arşiv faturası",
      "Küçük hacimli satışta en ucuz yol; GİB portalının kendi sınırları geçerlidir."),
    # --- ERP / muhasebe
    P("nebim", "erp", "Nebim V3", ERPF, "Stok, cari, fatura ve sipariş aktarımı"),
    P("logo", "erp", "Logo (Tiger / GO)", ERPF, "Stok, cari ve fatura aktarımı"),
    P("mikro", "erp", "Mikro", ERPF, "Stok, cari ve fatura aktarımı"),
    P("netsis", "erp", "Netsis", ERPF, "Stok, cari ve fatura aktarımı"),
    P("dia", "erp", "DIA", ERPF, "Stok, cari ve fatura aktarımı"),
    P("akinsoft", "erp", "AKINSOFT", ERPF, "Stok ve cari aktarımı"),
    # --- SMS ve bildirim
    P("netgsm", "sms", "Netgsm", SMSF, "SMS gönderimi",
      "Mesaj başlığı Netgsm panelinde onaylı olmalı, yoksa mesaj iletilmez."),
    P("iletimerkezi", "sms", "İleti Merkezi", SMSF, "SMS gönderimi"),
    P("verimor", "sms", "Verimor", SMSF, "SMS gönderimi"),
    P("mutlucell", "sms", "Mutlucell", SMSF, "SMS gönderimi"),
    P("masgsm", "sms", "MasGSM", SMSF, "SMS gönderimi"),
    P("whatsapp", "sms", "WhatsApp Business", [F("phone_id", "Telefon numarası kimliği"),
                                               F("token", "Erişim anahtarı", True),
                                               F("waba_id", "WhatsApp hesap kimliği", zorunlu=False)],
      "Sipariş ve randevu bildirimleri"),
    P("smtp", "sms", "E-posta (SMTP)", [F("host", "Sunucu"), F("port", "Kapı", ipucu="587 veya 465", tip="number"),
                                        F("user", "Kullanıcı"), F("pass", "Şifre", True),
                                        F("from", "Gönderen adresi")],
      "Bilgilendirme e-postaları"),
    # --- pazaryeri
    P("trendyol", "pazaryeri", "Trendyol", MAGAZA, "Ürün, sipariş, stok ve kargo barkodu"),
    P("hepsiburada", "pazaryeri", "Hepsiburada", MAGAZA, "Ürün, sipariş ve stok"),
    P("n11", "pazaryeri", "N11", MAGAZA, "Ürün, sipariş ve stok"),
    P("ciceksepeti", "pazaryeri", "Çiçeksepeti", MAGAZA, "Ürün, sipariş ve stok"),
    P("amazon_tr", "pazaryeri", "Amazon TR", MAGAZA, "Hazırlanıyor: bilgileriniz kaydedilir, otomatik bağlantı henüz açık değil."),
    P("pttavm", "pazaryeri", "PttAVM", MAGAZA, "Ürün, sipariş ve stok"),
    P("pazarama", "pazaryeri", "Pazarama", MAGAZA, "Ürün, sipariş ve stok"),
    P("idefix", "pazaryeri", "İdefix", MAGAZA, "Hazırlanıyor: bilgileriniz kaydedilir, otomatik bağlantı henüz açık değil."),
    P("modanisa", "pazaryeri", "Modanisa", MAGAZA, "Hazırlanıyor: bilgileriniz kaydedilir, otomatik bağlantı henüz açık değil."),
    P("temu", "pazaryeri", "Temu", MAGAZA, "Hazırlanıyor: bilgileriniz kaydedilir, otomatik bağlantı henüz açık değil."),
    P("yemeksepeti", "pazaryeri", "Yemeksepeti", [F("webhook_key", "Bildirim anahtarı", True, ipucu="Kendiniz belirlersiniz; Yemeksepeti'ye verdiğiniz bildirim adresinde kullanılır"),
                                                  F("token", "Yemeksepeti erişim anahtarı", True, zorunlu=False, ipucu="Sipariş durumunu Yemeksepeti'ne bildirmek için"), F("komisyon", "Komisyon oranı % (kâr hesabı için)", zorunlu=False, tip="number")],
      "Gelen siparişler anında listenize düşer. Yemeksepeti'nden entegrasyon izni gerekir."),
    P("trendyol_yemek", "pazaryeri", "Trendyol Yemek", [F("seller_id", "Mağaza numarası (ID)"), F("api_key", "API anahtarı", True), F("api_secret", "API gizli anahtarı", True), F("store_id", "Restoran numarası (birden çok şubeniz varsa)", zorunlu=False, ipucu="Boşsa tüm restoranlarınız menüye dahil edilir"), F("komisyon", "Komisyon oranı % (kâr hesabı için)", zorunlu=False, tip="number")],
      "Siparişler 1-2 dakikada bir kendiliğinden gelir; menüde fiyat ve satış durumu panelden gönderilir."),
    P("getir_yemek", "pazaryeri", "Getir Yemek", [F("token", "Erişim anahtarı", True), F("orders_url", "Sipariş adresi", ipucu="Getir'in size verdiği sipariş adresi"), F("komisyon", "Komisyon oranı % (kâr hesabı için)", zorunlu=False, tip="number")],
      "Siparişler 1-2 dakikada bir kendiliğinden listenize gelir. Getir'den entegrasyon erişimi gerekir."),
    P("migros_yemek", "pazaryeri", "Migros Yemek", [F("token", "Erişim anahtarı", True), F("orders_url", "Sipariş adresi", ipucu="Migros'un size verdiği sipariş adresi"), F("komisyon", "Komisyon oranı % (kâr hesabı için)", zorunlu=False, tip="number")],
      "Siparişler 1-2 dakikada bir kendiliğinden listenize gelir. Migros'tan entegrasyon erişimi gerekir."),
    # --- ölçüm ve reklam
    P("ga4", "olcum", "Google Analytics 4", [F("id", "Ölçüm kimliği", ipucu="G- ile başlar")],
      "Ziyaretçi ve dönüşüm ölçümü", test=False),
    P("search_console", "olcum", "Google Search Console",
      [F("id", "Doğrulama kodu", ipucu="google-site-verification içindeki değer")],
      "Arama performansı", test=False),
    P("google_ads", "olcum", "Google Ads", [F("id", "Dönüşüm kimliği", ipucu="AW- ile başlar"),
                                            F("label", "Dönüşüm etiketi", zorunlu=False)],
      "Reklam dönüşümü", test=False),
    P("meta_pixel", "olcum", "Meta Pixel", [F("id", "Piksel kimliği"),
                                            F("token", "Dönüşüm API anahtarı", True, zorunlu=False)],
      "Facebook ve Instagram reklam ölçümü", test=False),
    P("tiktok_pixel", "olcum", "TikTok Pixel", [F("id", "Piksel kimliği")], "TikTok reklam ölçümü", test=False),
    P("google_merchant", "olcum", "Google Merchant", [F("id", "Satıcı kimliği"),
                                                      F("api_key", "API anahtarı", True, zorunlu=False)],
      "Ürünlerin Google Alışveriş'te görünmesi"),
    # --- diğer
    P("google_isletme", "diger", "Google İşletme Profili", [F("place_id", "İşletme kimliği"),
                                                            F("api_key", "API anahtarı", True)],
      "Google yorumlarının sitede görünmesi"),
    P("uyap", "diger", "UYAP", [F("user", "Kullanıcı adı"), F("pass", "Şifre", True)],
      "Duruşma ve dosya takibi"),
    P("canli_destek", "diger", "Canlı destek", [F("kod", "Yerleştirme kodu", tip="area")],
      "Sitenize canlı destek penceresi", test=False),
    # --- PRD §3'te sayılan diğer sağlayıcılar (alan denetimi yapılır; canlı doğrulama ucu henüz yok)
    P("paratika", "pos", "Paratika", POSF, "Kartla tahsilat ve taksit", test=False),
    P("paynet", "pos", "Paynet", POSF, "Kartla tahsilat ve taksit", test=False),
    P("moka", "pos", "Moka United", [F("dealer", "Bayi kodu"), F("user", "API kullanıcı adı"), F("pass", "API şifresi", True)], "Kartla tahsilat ve taksit", test=False),
    P("lidio", "pos", "Lidio", POSF, "Kartla tahsilat", test=False),
    P("netahsilat", "pos", "Netahsilat", POSF, "Kartla tahsilat", test=False),
    P("stripe", "pos", "Stripe", [F("publishable", "Yayınlanabilir anahtar"), F("secret", "Gizli anahtar", True)], "Yurt dışı kartlarla tahsilat", test=False),
    P("dhl", "kargo", "DHL", KARGOF, "Gönderi oluşturma ve takip", test=False),
    P("geliver", "kargo", "Geliver", [F("api_key", "API anahtarı", True)], "Tek anlaşmayla birden çok kargo", test=False),
    P("kargoist", "kargo", "Kargoist", [F("api_key", "API anahtarı", True)], "Kargo karşılaştırma ve gönderi", test=False),
    P("kargola", "kargo", "Kargola", [F("api_key", "API anahtarı", True)], "Kargo karşılaştırma ve gönderi", test=False),
    P("pts", "kargo", "PTS", KARGOF, "Gönderi oluşturma ve takip", test=False),
    P("hts", "kargo", "HTS", KARGOF, "Gönderi oluşturma ve takip", test=False),
    P("pozitif", "kargo", "Pozitif Lojistik", KARGOF, "Gönderi oluşturma ve takip", test=False),
    P("basitkargo", "kargo", "Basit Kargo", [F("api_key", "API anahtarı", True)], "Gönderi oluşturma ve takip", test=False),
    P("bizimhesap", "efatura", "Bizim Hesap", [F("api_key", "API anahtarı", True), F("firma_id", "Firma kimliği", zorunlu=False)], "Fatura kesme ve cari aktarım", test=False),
    P("logo_isbasi", "efatura", "Logo İşbaşı", [F("user", "Kullanıcı adı"), F("pass", "Şifre", True), F("vkn", "VKN / TCKN")], "e-Fatura ve e-Arşiv", test=False),
    P("hitit", "erp", "Hitit", ERPF, "Stok, cari ve fatura aktarımı", test=False),
    P("webticari", "erp", "WebTicari", ERPF, "Stok, cari ve fatura aktarımı", test=False),
    P("evobulut", "erp", "Evobulut", ERPF, "Stok, cari ve fatura aktarımı", test=False),
    P("jbi", "erp", "JBI", ERPF, "Stok, cari ve fatura aktarımı", test=False),
    P("kolaybi", "erp", "KolayBi", ERPF, "Stok, cari ve fatura aktarımı", test=False),
    P("flap", "erp", "Flap ERP", ERPF, "Stok, cari ve fatura aktarımı", test=False),
    P("asb", "erp", "ASB", ERPF, "Stok, cari ve fatura aktarımı", test=False),
    P("sentez", "erp", "Sentez", ERPF, "Stok, cari ve fatura aktarımı", test=False),
    P("eta", "erp", "ETA", ERPF, "Stok, cari ve fatura aktarımı", test=False),
    P("zirve", "erp", "Zirve", ERPF, "Stok, cari ve fatura aktarımı", test=False),
    P("luca", "erp", "Luca", ERPF, "Stok, cari ve fatura aktarımı", test=False),
    P("canias", "erp", "Canias", ERPF, "Stok, cari ve fatura aktarımı", test=False),
    P("kobikom", "sms", "Kobikom", SMSF, "SMS gönderimi", test=False),
    P("google_takvim", "olcum", "Google Takvim", [F("calendar_id", "Takvim kimliği", ipucu="Takvim ayarlarındaki 'Takvim kimliği'"), F("api_key", "API anahtarı", True)],
      "Randevuların Google Takvim'e düşmesi", test=False),
    P("facebook_catalog", "olcum", "Facebook / Instagram Katalog", [F("catalog_id", "Katalog kimliği"), F("token", "Erişim anahtarı", True)],
      "Ürünlerin Facebook ve Instagram mağazasında görünmesi", test=False),
    P("instagram", "olcum", "Instagram", [F("user_id", "Hesap kimliği"), F("token", "Erişim anahtarı", True)],
      "Gönderilerin sitede görünmesi", test=False),
    P("google_login", "olcum", "Google ile giriş", [F("client_id", "İstemci kimliği", ipucu="Google Cloud > Kimlik bilgileri")],
      "Üyelerin Google hesabıyla girmesi", test=False),
    P("facebook_login", "olcum", "Facebook ile giriş", [F("app_id", "Uygulama kimliği")], "Üyelerin Facebook hesabıyla girmesi", test=False),
    P("webhook", "diger", "Webhook / API", [F("url", "Adres (https://...)"), F("secret", "İmza anahtarı", True, zorunlu=False)],
      "Sipariş ve randevu olaylarını kendi sisteminize gönderir", test=False),
    P("zoom_meet", "diger", "Zoom / Google Meet", [F("link", "Toplantı bağlantısı", ipucu="https://meet.google.com/...")],
      "Çevrimiçi randevulara toplantı bağlantısı", test=False),
]
BY_ID = {p["id"]: p for p in CATALOG}
MODES = ("test", "canli")


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


def _t(v, n):
    return " ".join(str(v or "").split())[:n]


def mask(v):
    """Gizli değeri panele güvenle gösterilecek hâle getir."""
    v = str(v or "")
    if not v:
        return ""
    return "••••" + v[-4:] if len(v) > 4 else "••••"


def check(pid, keys, mode="test"):
    """Entegrasyon denemesi: eksik ve biçimsiz alanı söyle.

    Ağ erişimi olmadan da anlamlı bir deneme yapılır — alanların varlığı ve biçimi
    burada tutulur; gerçek çağrı canlıda `probe` ile yapılır. Böylece müşteri yanlış
    alana yapıştırdığı anahtarı dakikalar sonra sipariş kaybederek değil, hemen görür.
    """
    p = BY_ID.get(pid)
    if not p:
        raise HTTPException(404, "Entegrasyon bulunamadı")
    eksik = [f["label"] for f in p["fields"] if f["required"] and not _t(keys.get(f["key"]), 400)]
    if eksik:
        return False, "Şu alanlar boş: %s" % ", ".join(eksik)
    v = lambda k: _t(keys.get(k), 400)                             # noqa: E731
    if pid == "ga4" and not re.match(r"^G-[A-Z0-9]{4,}$", v("id").upper()):
        return False, "Ölçüm kimliği G- ile başlamalı (örnek: G-ABC123DEF4)"
    if pid == "google_ads" and not re.match(r"^AW-\d{6,}$", v("id").upper()):
        return False, "Dönüşüm kimliği AW- ile başlamalı (örnek: AW-123456789)"
    if pid in ("meta_pixel", "tiktok_pixel") and not v("id").isdigit():
        return False, "Piksel kimliği yalnız rakamlardan oluşur"
    if pid == "havale":
        iban = v("iban").replace(" ", "").upper()
        if not re.match(r"^TR\d{24}$", iban):
            return False, "IBAN 'TR' ile başlamalı ve 26 karakter olmalı"
    if pid in ("gib_earsiv", "uyumsoft", "izibiz", "nes", "edm", "qnb_efinans"):
        vkn = v("vkn")
        if not (vkn.isdigit() and len(vkn) in (10, 11)):
            return False, "VKN 10, TCKN 11 haneli olmalı"
    if pid == "smtp":
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v("from")):
            return False, "Gönderen adresi geçerli bir e-posta olmalı"
        if v("port") not in ("25", "465", "587", "2525"):
            return False, "Kapı numarası genelde 587 veya 465 olur"
    if p["group"] == "erp" and not v("url").startswith(("http://", "https://")):
        return False, "Sunucu adresi http:// veya https:// ile başlamalı"
    if pid == "netgsm" and len(v("header")) > 11:
        return False, "Mesaj başlığı en fazla 11 karakter olabilir"
    if mode == "canli" and p["group"] == "pos":
        for k in ("api_key", "api_secret", "pass"):
            if "test" in v(k).lower() or "sandbox" in v(k).lower():
                return False, "Canlı moda geçmeden önce test anahtarlarını değiştirin"
    return True, ""


def view(p, row, allowed):
    """Panelde görünecek hâli: anahtarlar maskeli, durum ve son hata açık."""
    row = row or {}
    keys = row.get("keys") or {}
    on = bool(row.get("on")) and bool(row.get("ok"))
    return {"id": p["id"], "group": p["group"], "name": p["name"], "desc": p["desc"], "hint": p["hint"],
            "can_test": p["can_test"], "allowed": allowed,
            "fields": [dict(f, value=(mask(keys.get(f["key"])) if f["secret"] else _t(keys.get(f["key"]), 400)),
                            filled=bool(_t(keys.get(f["key"]), 400))) for f in p["fields"]],
            "on": bool(row.get("on")), "ok": bool(row.get("ok")), "state": "bagli" if on else
            ("hata" if row.get("err") else ("kurulum" if row.get("keys") else "yok")),
            "mode": row.get("mode") or "test", "err": row.get("err") or "",
            "last_ok": row.get("last_ok") or "", "at": row.get("at") or ""}


def register(api_router, db, deps):
    adm = deps["require_admin"]
    probe = deps.get("probe")                                      # canlıda gerçek çağrıyı yapan yardımcı

    async def allow_list():
        """Sektör paketi + sahibin izni. None ise paketteki hepsi açık."""
        d = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
        sec = d.get("sector")
        if not sec:
            s = await db.app_settings.find_one({"_id": "sector"}, {"_id": 0}) or {}
            sec = s.get("key") or ""
        try:
            import blocks
            pack = list((blocks.pack(sec) or {}).get("integrations") or [])
        except Exception:                                          # noqa: BLE001
            pack = []
        izin = d.get("integrations_allowed")
        try:
            _m, _s, eshop = await blocks.firma_modulleri(db)
        except Exception:                                          # noqa: BLE001
            eshop = False
        if eshop:                                                  # e-ticaret açık: ödeme, pazaryeri, kargo, e-fatura, ERP hepsi gelir
            pack = list(dict.fromkeys(pack + blocks.SHOP_INT))
        if izin is None:                                           # sahip seçim yapmadıysa paketin kendi listesi
            return (set(pack) & set(BY_ID)) if pack else set(BY_ID)
        return set(izin) & set(BY_ID)                              # sahip seçtiyse söz onundur

    async def row_of(pid):
        return await db.yp_integrations.find_one({"id": pid}, {"_id": 0})

    async def log(pid, ev, note=""):
        await db.yp_int_log.insert_one({"id": uuid.uuid4().hex[:12], "int": pid, "event": ev,
                                        "note": _t(note, 300), "at": _now()})

    @api_router.get("/yp/integrations")
    async def listele(request: Request, group: str = "", _: dict = Depends(adm)):
        izin = await allow_list()
        rows = {r["id"]: r for r in await db.yp_integrations.find({}, {"_id": 0}).to_list(400)}
        items = [view(p, rows.get(p["id"]), p["id"] in izin) for p in CATALOG if p["id"] in izin]
        for i in items:
            if i["id"] == "yemeksepeti":                          # müşteri bu adresi Yemeksepeti'ye verir
                try:
                    import tenant
                    f = await db.main().firms.find_one({"db": tenant.current()}, {"_id": 0, "id": 1}) or {}
                    key = _t(((rows.get("yemeksepeti") or {}).get("keys") or {}).get("webhook_key"), 60) or "<bildirim anahtarınız>"
                    if f.get("id"):
                        i["hint"] = "Yemeksepeti'ne vereceğiniz bildirim adresi: %s/api/public/%s~yemek/yemeksepeti?k=%s" % (str(request.base_url).rstrip("/").replace("http://", "https://") if "testserver" not in str(request.base_url) and "localhost" not in str(request.base_url) else str(request.base_url).rstrip("/"), f["id"], key)
                except Exception:                                  # noqa: BLE001
                    pass
        if group:
            items = [i for i in items if i["group"] == group]
        groups = [{"id": g, "name": n, "desc": d,
                   "n": len([i for i in items if i["group"] == g]),
                   "bagli": len([i for i in items if i["group"] == g and i["state"] == "bagli"]),
                   "hata": len([i for i in items if i["group"] == g and i["state"] == "hata"])}
                  for g, n, d in GROUPS]
        return {"items": items, "groups": [g for g in groups if g["n"]],
                "counts": {"hepsi": len(items),
                           "bagli": len([i for i in items if i["state"] == "bagli"]),
                           "hata": len([i for i in items if i["state"] == "hata"]),
                           "yok": len([i for i in items if i["state"] == "yok"])}}

    async def nerede(p):
        """Bu entegrasyon panelde nerede çalışıyor? Kapatmanın neyi durduracağını göster."""
        out = []
        if p["group"] in ("sms", "diger") and p["id"] != "canli_destek":
            try:
                import bildirim
                import blocks
                d = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
                mods = d.get("modules")
                if mods is None:
                    mods = list((blocks.pack(d.get("sector") or "") or {}).get("modules") or [])
                mods = set(mods or [])
                rows = {r["id"]: r for r in await db.yp_notify.find({}, {"_id": 0}).to_list(200)}
                kanal = "whatsapp" if p["id"] == "whatsapp" else ("eposta" if p["id"] == "smtp" else "sms")
                for e in bildirim.EVENTS:
                    if e["module"] and e["module"] not in mods:    # firmanın paketinde olmayan olay gösterilmez
                        continue
                    r = rows.get(e["id"]) or {}
                    ks = r.get("channels") if r.get("channels") is not None else e["channels"]
                    if kanal in (ks or []) and r.get("on", bool(ks)):
                        out.append({"name": e["name"], "desc": e["desc"], "on": True})
            except Exception:                                      # noqa: BLE001
                pass
        if p["group"] == "pos":
            out.append({"name": "Sitede ödeme", "desc": "Müşteri kartla öderken", "on": True})
        if p["group"] == "kargo":
            out += [{"name": "Gönderi oluşturma", "desc": "Sipariş kargoya verilince", "on": True},
                    {"name": "Kargo fişi", "desc": "Takip numarası ve barkod", "on": True}]
        if p["group"] == "efatura":
            out.append({"name": "Fatura kesme", "desc": "Sipariş teslim edilince", "on": True})
        if p["group"] == "pazaryeri":
            out += [{"name": "Stok senkronu", "desc": "Satış olunca diğer kanallara bildirilir", "on": True},
                    {"name": "Sipariş aktarımı", "desc": "Pazaryeri siparişleri panele düşer", "on": True}]
        return out[:12]

    @api_router.get("/yp/integrations/{pid}")
    async def tek(pid: str, _: dict = Depends(adm)):
        p = BY_ID.get(_t(pid, 40))
        if not p:
            raise HTTPException(404, "Entegrasyon bulunamadı")
        izin = await allow_list()
        if p["id"] not in izin:
            raise HTTPException(403, "Bu entegrasyon paketinizde yok")
        return {"item": view(p, await row_of(p["id"]), True), "uses": await nerede(p)}

    @api_router.put("/yp/integrations/{pid}")
    async def kaydet(pid: str, payload: dict, _: dict = Depends(adm)):
        """Anahtarları kaydet. Boş gönderilen gizli alan eskisini korur."""
        p = BY_ID.get(_t(pid, 40))
        if not p:
            raise HTTPException(404, "Entegrasyon bulunamadı")
        if p["id"] not in await allow_list():
            raise HTTPException(403, "Bu entegrasyon paketinizde yok")
        old = await row_of(p["id"]) or {}
        keys = dict(old.get("keys") or {})
        gelen = payload.get("keys") or {}
        for f in p["fields"]:
            if f["key"] not in gelen:
                continue
            yeni = _t(gelen[f["key"]], 400)
            if f["secret"] and (not yeni or yeni.startswith("••••")):
                continue                                           # maskeli değer geri geldi: dokunma
            keys[f["key"]] = yeni
        mode = _t(payload.get("mode"), 10) or old.get("mode") or "test"
        if mode not in MODES:
            raise HTTPException(422, "Çalışma modu test veya canlı olmalı")
        ok, err = check(p["id"], keys, mode)
        on = bool(payload.get("on", old.get("on", False)))
        if ok and not old.get("ok"):
            on = True                                              # ilk başarılı bağlantı: kendiliğinden etkin (sonradan bilerek kapatılırsa kapalı kalır)
        row = {"id": p["id"], "group": p["group"], "keys": keys, "mode": mode, "on": on,
               "ok": ok, "err": "" if ok else err, "at": _now(),
               "last_ok": _now() if ok else (old.get("last_ok") or "")}
        await db.yp_integrations.update_one({"id": p["id"]}, {"$set": row}, upsert=True)
        await log(p["id"], "kaydedildi" if ok else "hata", err)
        if ok and on and not old.get("on"):                        # açıldığı andan itibaren gelen siparişler kaçmasın
            try:
                import markets_hub
                await markets_hub.baslangic(db, p["id"])
            except Exception:                                      # noqa: BLE001
                pass
        return {"ok": ok, "err": err, "item": view(p, row, True)}

    @api_router.post("/yp/integrations/{pid}/test")
    async def dene(pid: str, _: dict = Depends(adm)):
        p = BY_ID.get(_t(pid, 40))
        if not p:
            raise HTTPException(404, "Entegrasyon bulunamadı")
        row = await row_of(p["id"])
        if not row or not (row.get("keys") or {}):
            raise HTTPException(422, "Önce bilgileri girip kaydedin")
        ok, err = check(p["id"], row.get("keys") or {}, row.get("mode") or "test")
        msg = ""
        if ok and probe:
            try:
                sonuc = await probe(p["id"], row)
                ok, err = sonuc[0], sonuc[1]
                msg = sonuc[2] if len(sonuc) > 2 else ""
            except Exception as e:                                 # noqa: BLE001
                ok, err, msg = False, "Bağlantı kurulamadı: %s" % str(e)[:160], ""
        await db.yp_integrations.update_one({"id": p["id"]}, {"$set": {
            "ok": ok, "err": "" if ok else err, "at": _now(),
            "last_ok": _now() if ok else (row.get("last_ok") or "")}})
        await log(p["id"], "deneme başarılı" if ok else "deneme hatası", err or msg)
        return {"ok": ok, "err": err, "msg": (msg or "Bağlantı çalışıyor") if ok else err}

    @api_router.delete("/yp/integrations/{pid}")
    async def kaldir(pid: str, _: dict = Depends(adm)):
        p = BY_ID.get(_t(pid, 40))
        if not p:
            raise HTTPException(404, "Entegrasyon bulunamadı")
        await db.yp_integrations.delete_one({"id": p["id"]})
        await log(p["id"], "bağlantı kaldırıldı")
        return {"ok": True}

    @api_router.get("/yp/integrations/log/son")
    async def kayit(_: dict = Depends(adm)):
        rows = await db.yp_int_log.find({}, {"_id": 0}).to_list(400)
        rows.sort(key=lambda r: r.get("at") or "", reverse=True)
        for r in rows:
            r["name"] = (BY_ID.get(r.get("int")) or {}).get("name", r.get("int"))
        return {"items": rows[:80]}

    return api_router
