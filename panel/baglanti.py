# -*- coding: utf-8 -*-
"""Bağlantı Merkezi (yalnız platform sahibi): Google, Meta (Facebook / Instagram), WhatsApp,
kart ödemesi, e-posta, ölçüm ve altyapı bağlantılarının tek yerden yönetimi.

Kurallar:
1. Gizli alanlar veritabanına şifreli yazılır (Fernet, anahtar JWT_SECRET'tan türetilir) ve panele
   asla düz metin dönmez; maskeli (••••3821) görünür. Boş ya da maskeli gelen alan "değiştirme" demektir.
2. "Bağlı" demek için deneme gerekir. Yalnız okuyan, ücret doğurmayan resmî uçlar çağrılır; denemesi
   olmayan bağlantıda bu açıkça söylenir. Anahtar değişince doğrulama sıfırlanır.
3. Açık/kapalı anahtarı ayrıdır: bilgiyi silmeden bağlantı kapatılabilir.
4. Her değişiklik ve deneme günlüğe yazılır (kim değil, ne ve ne zaman; anahtar değeri asla).
"""
import asyncio
import base64
import hashlib
import hmac
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException

import tenant

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

GROUPS = [("google", "Google", "Arama, ölçüm, reklam, harita ve giriş"),
          ("meta", "Facebook ve Instagram", "Reklam ölçümü, sayfa, hesap ve katalog"),
          ("whatsapp", "WhatsApp", "Müşteriye ve ustaya otomatik mesaj"),
          ("odeme", "Kart ve ödeme", "Paket ve abonelik tahsilatı"),
          ("mesaj", "E-posta ve bildirim", "Sistem e-postaları ve anlık bildirim"),
          ("olcum", "Diğer ölçüm ve güvenlik", "Isı haritası, TikTok, robot koruması"),
          ("altyapi", "Altyapı ve yapay zekâ", "DNS, yapay zekâ ve dış sistem bildirimi")]


def F(key, label, gizli=False, zorunlu=True, ipucu="", tip="text", secenek=None):
    d = {"key": key, "label": label, "secret": gizli, "required": zorunlu, "hint": ipucu, "type": tip}
    if secenek:
        d["options"] = secenek
    return d


def P(pid, group, name, fields, desc="", where="", test=True, public=None):
    """where: anahtarın alındığı yer (kısa yönerge). public: sayfaya basılabilecek herkese açık alanlar."""
    return {"id": pid, "group": group, "name": name, "fields": fields, "desc": desc, "where": where,
            "can_test": test, "public": public or []}


MOD = F("mode", "Ortam", zorunlu=False, tip="select", secenek=[["canli", "Canlı"], ["test", "Deneme (sandbox)"]],
        ipucu="Önce deneme ortamında deneyin; canlı anahtarlarla geçince 'Canlı'yı seçin")

CATALOG = [
    # ---------------------------------------------------------------- Google
    P("gsc", "google", "Google Search Console", [], "Arama performansı: hangi kelimeyle kaç tıklama",
      "Hizmet hesabı anahtarı ve mülk adresi Bugün sayfasındaki Search Console kartından girilir.", test=False),
    P("ga4", "google", "Google Analytics 4", [F("id", "Ölçüm kimliği", ipucu="G- ile başlar")],
      "Ziyaretçi, kaynak ve dönüşüm ölçümü", "analytics.google.com > Yönetici > Veri akışları", test=False, public=["id"]),
    P("gtm", "google", "Google Etiket Yöneticisi", [F("id", "Kapsayıcı kimliği", ipucu="GTM- ile başlar")],
      "Tüm etiketleri tek yerden yönetin. GA4 ve Ads'i buradan kuruyorsanız ikisini ayrıca açmayın; sayfa iki kez ölçülür.",
      "tagmanager.google.com", test=False, public=["id"]),
    P("google_ads", "google", "Google Ads dönüşümü", [F("id", "Dönüşüm kimliği", ipucu="AW- ile başlar"),
                                                    F("label", "Dönüşüm etiketi", zorunlu=False, ipucu="Deneme talebi gönderildiğinde sayılır")],
      "Reklamdan gelen deneme taleplerini ölçer", "ads.google.com > Araçlar > Dönüşümler", test=False, public=["id", "label"]),
    P("google_merchant", "google", "Google Merchant Center", [F("id", "Merchant kimliği"), F("api_key", "API anahtarı", True, zorunlu=False)],
      "Ürün akışı ve Google Alışveriş", "merchants.google.com", test=False),
    P("google_maps", "google", "Google Haritalar API", [F("api_key", "API anahtarı", True)],
      "Adres tamamlama, harita ve konum", "console.cloud.google.com > API'ler > Kimlik bilgileri. Anahtarı alan adı ve API ile kısıtlayın."),
    P("google_login", "google", "Google ile giriş", [F("client_id", "İstemci kimliği", ipucu=".apps.googleusercontent.com ile biter"),
                                                   F("client_secret", "İstemci gizli anahtarı", True)],
      "Kullanıcılar Google hesabıyla girer", "console.cloud.google.com > OAuth izin ekranı ve Kimlik bilgileri", test=False, public=["client_id"]),
    P("recaptcha", "google", "Google reCAPTCHA", [F("site_key", "Site anahtarı"), F("secret", "Gizli anahtar", True)],
      "Form ve deneme isteklerinde robot koruması", "google.com/recaptcha/admin", public=["site_key"]),
    # ---------------------------------------------------------------- Meta
    P("meta_pixel", "meta", "Meta Pixel ve Conversions API", [F("id", "Piksel kimliği"),
                                                              F("token", "Conversions API anahtarı", True, zorunlu=False,
                                                                ipucu="Girilirse deneme talepleri sunucudan da bildirilir"),
                                                              F("test_code", "Test olayı kodu", zorunlu=False, ipucu="Yalnız deneme; yayında boş olmalı")],
      "Facebook ve Instagram reklamlarının dönüşüm ölçümü", "business.facebook.com > Olay Yöneticisi > Ayarlar", public=["id"]),
    P("facebook_sayfa", "meta", "Facebook sayfası", [F("page_id", "Sayfa kimliği"), F("token", "Sayfa erişim anahtarı", True),
                                                   F("app_secret", "Uygulama gizli anahtarı", True, zorunlu=False),
                                                   F("verify_token", "Webhook doğrulama kodu", True, zorunlu=False, ipucu="Kendiniz belirlersiniz")],
      "Sayfa mesajları, gönderi paylaşımı ve potansiyel müşteri formları", "developers.facebook.com > Uygulamanız > Messenger ve Sayfa ayarları"),
    P("instagram", "meta", "Instagram işletme hesabı", [F("user_id", "Instagram hesap kimliği"), F("token", "Erişim anahtarı", True)],
      "Gönderileri sitede göstermek, mesajlara yanıt vermek", "developers.facebook.com > Instagram Graph API; hesap Facebook sayfasına bağlı işletme hesabı olmalı"),
    P("facebook_login", "meta", "Facebook ile giriş", [F("app_id", "Uygulama kimliği"), F("app_secret", "Uygulama gizli anahtarı", True)],
      "Kullanıcılar Facebook hesabıyla girer", "developers.facebook.com > Uygulama ayarları > Temel", public=["app_id"]),
    P("meta_katalog", "meta", "Facebook ve Instagram kataloğu", [F("catalog_id", "Katalog kimliği"), F("token", "Erişim anahtarı", True, zorunlu=False)],
      "Ürünler Facebook ve Instagram mağazasında görünür", "business.facebook.com > Commerce Manager"),
    # ---------------------------------------------------------------- WhatsApp
    P("whatsapp", "whatsapp", "WhatsApp Business (Cloud API)",
      [F("phone_id", "Telefon numarası kimliği"), F("token", "Kalıcı erişim anahtarı", True),
       F("waba_id", "WhatsApp hesap kimliği", zorunlu=False),
       F("app_secret", "Uygulama gizli anahtarı", True, zorunlu=False, ipucu="Gelen webhook imzasını doğrulamak için"),
       F("verify_token", "Webhook doğrulama kodu", True, zorunlu=False, ipucu="Kendiniz belirlersiniz; Meta'ya aynısını yazın")],
      "Randevu hatırlatma, servis durumu ve ödeme bildirimi mesajları",
      "developers.facebook.com > Uygulamanız > WhatsApp > API kurulumu. Şablon mesajlar Meta'da onaylı olmalı."),
    # ---------------------------------------------------------------- Kart ve ödeme
    P("iyzico", "odeme", "iyzico (kredi kartı)", [F("api_key", "API anahtarı", True), F("secret", "Gizli anahtar", True), MOD],
      "Kartla paket ve abonelik tahsilatı, taksit ve iade", "iyzico panel > Ayarlar > API anahtarları"),
    P("paytr", "odeme", "PayTR (kredi kartı)", [F("merchant_id", "Mağaza numarası"), F("key", "Mağaza anahtarı", True),
                                              F("salt", "Mağaza gizli anahtarı", True), MOD],
      "Kartla tahsilat ve taksit", "PayTR mağaza paneli > Bilgi", test=False),
    P("stripe", "odeme", "Stripe", [F("publishable", "Yayınlanabilir anahtar"), F("secret", "Gizli anahtar", True),
                                   F("webhook_secret", "Webhook imza anahtarı", True, zorunlu=False)],
      "Yurt dışı kartlarla tahsilat", "dashboard.stripe.com > Geliştiriciler > API anahtarları", public=["publishable"]),
    P("paypal", "odeme", "PayPal", [F("client_id", "Client ID"), F("secret", "Gizli anahtar", True), MOD],
      "PayPal ile tahsilat", "developer.paypal.com > Apps & Credentials"),
    P("havale", "odeme", "Havale / EFT hesabı", [F("iban", "IBAN"), F("unvan", "Hesap sahibi"), F("banka", "Banka", zorunlu=False)],
      "Firma abonelik ödemesini havaleyle yapacaksa görecek hesap", "", test=False, public=["iban", "unvan", "banka"]),
    # ---------------------------------------------------------------- E-posta ve bildirim
    P("smtp", "mesaj", "E-posta (SMTP)", [F("host", "Sunucu"), F("port", "Kapı", ipucu="587 veya 465", tip="number"),
                                         F("user", "Kullanıcı"), F("pass", "Şifre", True), F("from", "Gönderen adresi")],
      "Giriş, hatırlatma ve fatura e-postaları", "E-posta sağlayıcınızın SMTP bilgileri"),
    P("resend", "mesaj", "Resend (e-posta servisi)", [F("api_key", "API anahtarı", True), F("from", "Gönderen adresi")],
      "SMTP yerine API ile e-posta gönderimi", "resend.com > API Keys"),
    P("sendgrid", "mesaj", "SendGrid (e-posta servisi)", [F("api_key", "API anahtarı", True), F("from", "Gönderen adresi")],
      "SMTP yerine API ile e-posta gönderimi", "app.sendgrid.com > Settings > API Keys"),
    P("telegram", "mesaj", "Telegram bildirimi", [F("token", "Bot anahtarı", True), F("chat_id", "Sohbet kimliği")],
      "Yeni deneme talebi, ödeme ve hata bildirimi telefonunuza düşer", "Telegram'da @BotFather ile bot oluşturun; sohbet kimliği için bota yazıp getUpdates'e bakın"),
    # ---------------------------------------------------------------- Diğer ölçüm ve güvenlik
    P("clarity", "olcum", "Microsoft Clarity", [F("id", "Proje kimliği")], "Ücretsiz ısı haritası ve oturum kaydı",
      "clarity.microsoft.com > Settings > Overview", test=False, public=["id"]),
    P("tiktok_pixel", "olcum", "TikTok Pixel", [F("id", "Piksel kimliği")], "TikTok reklam ölçümü",
      "ads.tiktok.com > Events", test=False, public=["id"]),
    P("linkedin", "olcum", "LinkedIn Insight Tag", [F("id", "Ortak kimliği (partner id)")], "LinkedIn reklam ölçümü",
      "linkedin.com/campaignmanager > Insight Tag", test=False, public=["id"]),
    P("turnstile", "olcum", "Cloudflare Turnstile", [F("site_key", "Site anahtarı"), F("secret", "Gizli anahtar", True)],
      "reCAPTCHA'ya ücretsiz, çerezsiz alternatif", "dash.cloudflare.com > Turnstile", public=["site_key"]),
    # ---------------------------------------------------------------- Altyapı
    P("cloudflare", "altyapi", "Cloudflare", [F("token", "API belirteci", True), F("zone_id", "Bölge kimliği", zorunlu=False)],
      "Alan adı DNS kayıtlarını panelden yönetmek", "dash.cloudflare.com > Profil > API belirteçleri"),
    P("anthropic", "altyapi", "Claude (yapay zekâ)", [F("api_key", "API anahtarı", True)],
      "Metin önerisi, sektör içeriği ve destek yanıtı", "console.anthropic.com > API Keys"),
    P("openai", "altyapi", "OpenAI", [F("api_key", "API anahtarı", True)], "Yedek yapay zekâ sağlayıcısı", "platform.openai.com > API keys"),
    P("webhook", "altyapi", "Giden webhook", [F("url", "Adres (https://...)"), F("secret", "İmza anahtarı", True, zorunlu=False)],
      "Yeni firma, ödeme ve talep olaylarını kendi sisteminize gönderir", "", test=False),
]
BY_ID = {p["id"]: p for p in CATALOG}
MASK = "••••"
ZAMAN = 15


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


def _t(v, n=400):
    return " ".join(str(v or "").split())[:n]


# ---------------------------------------------------------------- şifreleme
def _fernet():
    from cryptography.fernet import Fernet
    k = hashlib.sha256(("baglanti|" + os.environ.get("JWT_SECRET", "changeme")).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(k))


def kilitle(v):
    v = str(v or "")
    return "enc:" + _fernet().encrypt(v.encode()).decode() if v else ""


def ac(v):
    v = str(v or "")
    if not v.startswith("enc:"):
        return v
    try:
        return _fernet().decrypt(v[4:].encode()).decode()
    except Exception:                                              # noqa: BLE001
        return ""


def mask(v):
    v = str(v or "")
    if not v:
        return ""
    return MASK + v[-4:] if len(v) > 8 else MASK


def acik_anahtarlar(p, keys):
    """Kayıtlı alanları çözülmüş hâliyle ver (yalnız sunucu içinde kullanılır)."""
    out = {}
    for f in p["fields"]:
        v = (keys or {}).get(f["key"], "")
        out[f["key"]] = ac(v) if f["secret"] else v
    return out


# ---------------------------------------------------------------- alan denetimi
def check(pid, keys):
    p = BY_ID.get(pid)
    if not p:
        raise HTTPException(404, "Bağlantı bulunamadı")
    v = lambda k: _t(keys.get(k))                                  # noqa: E731
    eksik = [f["label"] for f in p["fields"] if f["required"] and not v(f["key"])]
    if eksik:
        return False, "Şu alanlar boş: %s" % ", ".join(eksik)
    if pid == "ga4" and not re.match(r"^G-[A-Z0-9]{4,}$", v("id").upper()):
        return False, "Ölçüm kimliği G- ile başlamalı (örnek: G-ABC123DEF4)"
    if pid == "gtm" and not re.match(r"^GTM-[A-Z0-9]{4,10}$", v("id").upper()):
        return False, "Kapsayıcı kimliği GTM- ile başlamalı (örnek: GTM-ABC1234)"
    if pid == "google_ads" and not re.match(r"^AW-\d{6,}$", v("id").upper()):
        return False, "Dönüşüm kimliği AW- ile başlamalı (örnek: AW-123456789)"
    if pid == "google_login" and not v("client_id").endswith(".apps.googleusercontent.com"):
        return False, "İstemci kimliği .apps.googleusercontent.com ile bitmeli"
    if pid in ("meta_pixel", "tiktok_pixel") and not v("id").isdigit():
        return False, "Piksel kimliği yalnız rakamlardan oluşur"
    if pid in ("facebook_sayfa", "facebook_login", "instagram", "meta_katalog", "whatsapp"):
        for k in ("page_id", "app_id", "user_id", "catalog_id", "phone_id", "waba_id"):
            if v(k) and not v(k).isdigit():
                return False, "Kimlik alanı yalnız rakamlardan oluşur (%s)" % k
    if pid == "havale":
        if not re.match(r"^TR\d{24}$", v("iban").replace(" ", "").upper()):
            return False, "IBAN 'TR' ile başlamalı ve 26 karakter olmalı"
    if pid in ("smtp", "resend", "sendgrid"):
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v("from")):
            return False, "Gönderen adresi geçerli bir e-posta olmalı"
    if pid == "smtp" and v("port") not in ("25", "465", "587", "2525"):
        return False, "Kapı numarası genelde 587 veya 465 olur"
    if pid == "webhook" and not v("url").startswith("https://"):
        return False, "Adres https:// ile başlamalı"
    if pid == "telegram" and not re.match(r"^\d+:[\w-]{20,}$", v("token")):
        return False, "Bot anahtarı 123456:ABC... biçiminde olmalı"
    if pid == "stripe" and not v("publishable").startswith("pk_"):
        return False, "Yayınlanabilir anahtar pk_ ile başlamalı"
    if pid == "stripe" and not v("secret").startswith(("sk_", "rk_")):
        return False, "Gizli anahtar sk_ ile başlamalı"
    return True, ""


# ---------------------------------------------------------------- gerçek denemeler (yalnız okuyan uçlar)
def _istek(*a, **k):
    import entg_probe
    return entg_probe._istek(*a, **k)


def _hata_graph(r):
    try:
        return ((r.json().get("error") or {}).get("message") or "")[:140]
    except Exception:                                              # noqa: BLE001
        return ""


def _graph(yol, anahtar, alanlar, onek):
    r = _istek("GET", "https://graph.facebook.com/v21.0/%s" % yol, params={"access_token": anahtar, "fields": alanlar})
    if r.status_code >= 400:
        return False, "Meta kabul etmedi: %s" % (_hata_graph(r) or "kod %s" % r.status_code), ""
    try:
        d = r.json()
    except Exception:                                              # noqa: BLE001
        d = {}
    return True, "", "%s %s" % (onek, " · ".join(str(x) for x in d.values() if x and x != yol)[:120])


def _p_facebook_sayfa(k):
    return _graph(k["page_id"], k["token"], "name,fan_count", "Bağlantı çalışıyor. Sayfa:")


def _p_instagram(k):
    return _graph(k["user_id"], k["token"], "username,followers_count", "Bağlantı çalışıyor. Hesap:")


def _p_meta_katalog(k):
    if not k.get("token"):
        return True, "", "Katalog kimliği kaydedildi; erişim anahtarı girilmediği için bağlantı denenmedi."
    return _graph(k["catalog_id"], k["token"], "name,product_count", "Bağlantı çalışıyor. Katalog:")


def _p_meta_pixel(k):
    import entg_probe
    return entg_probe._meta_pixel({"keys": k})


def _p_whatsapp(k):
    import entg_probe
    return entg_probe._whatsapp({"keys": k})


def _p_smtp(k):
    import entg_probe
    return entg_probe._smtp({"keys": k})


def _p_google_maps(k):
    r = _istek("GET", "https://maps.googleapis.com/maps/api/geocode/json", params={"address": "Ankara", "key": k["api_key"]})
    try:
        d = r.json()
    except Exception:                                              # noqa: BLE001
        return False, "Google yanıtı okunamadı (kod %s)" % r.status_code, ""
    st = d.get("status")
    if st in ("OK", "ZERO_RESULTS"):
        return True, "", "Bağlantı çalışıyor, anahtar kabul edildi."
    return False, "Google kabul etmedi: %s %s" % (st, (d.get("error_message") or "")[:120]), ""


def _p_recaptcha(k):
    r = _istek("POST", "https://www.google.com/recaptcha/api/siteverify", data={"secret": k["secret"], "response": "baglanti-denemesi"})
    try:
        e = r.json().get("error-codes") or []
    except Exception:                                              # noqa: BLE001
        return False, "Google yanıtı okunamadı", ""
    if "invalid-input-secret" in e or "missing-input-secret" in e:
        return False, "Gizli anahtar geçersiz. Site anahtarıyla karıştırmış olabilirsiniz.", ""
    return True, "", "Gizli anahtar kabul edildi."


def _p_turnstile(k):
    r = _istek("POST", "https://challenges.cloudflare.com/turnstile/v0/siteverify", data={"secret": k["secret"], "response": "baglanti-denemesi"})
    try:
        e = r.json().get("error-codes") or []
    except Exception:                                              # noqa: BLE001
        return False, "Cloudflare yanıtı okunamadı", ""
    if "invalid-input-secret" in e or "missing-input-secret" in e:
        return False, "Gizli anahtar geçersiz.", ""
    return True, "", "Gizli anahtar kabul edildi."


def _p_stripe(k):
    r = _istek("GET", "https://api.stripe.com/v1/balance", headers={"Authorization": "Bearer " + k["secret"]})
    if r.status_code == 401:
        return False, "Stripe anahtarı kabul etmedi.", ""
    if r.status_code >= 400:
        return False, "Stripe yanıt vermedi (kod %s)." % r.status_code, ""
    canli = k["secret"].startswith(("sk_live", "rk_live"))
    return True, "", "Bağlantı çalışıyor (%s anahtar)." % ("canlı" if canli else "deneme")


def _p_paypal(k):
    host = "api-m.paypal.com" if k.get("mode") == "canli" else "api-m.sandbox.paypal.com"
    r = _istek("POST", "https://%s/v1/oauth2/token" % host, data={"grant_type": "client_credentials"}, auth=(k["client_id"], k["secret"]))
    if r.status_code in (401, 403):
        return False, "PayPal bilgileri kabul etmedi. Ortam (canlı/deneme) anahtarlarla uyumlu olmalı.", ""
    if r.status_code >= 400:
        return False, "PayPal yanıt vermedi (kod %s)." % r.status_code, ""
    return True, "", "Bağlantı çalışıyor (%s)." % ("canlı" if k.get("mode") == "canli" else "deneme")


def _p_iyzico(k):
    host = "api.iyzipay.com" if k.get("mode") == "canli" else "sandbox-api.iyzipay.com"
    yol = "/payment/bin/check"
    govde = '{"locale":"tr","conversationId":"baglanti","binNumber":"554960"}'
    rnd = str(int(datetime.now().timestamp() * 1000)) + secrets.token_hex(4)
    imza = hmac.new(k["secret"].encode(), (rnd + yol + govde).encode(), hashlib.sha256).hexdigest()
    yetki = base64.b64encode(("apiKey:%s&randomKey:%s&signature:%s" % (k["api_key"], rnd, imza)).encode()).decode()
    r = _istek("POST", "https://%s%s" % (host, yol), data=govde.encode(),
               headers={"Authorization": "IYZWSv2 " + yetki, "x-iyzi-rnd": rnd, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        d = r.json()
    except Exception:                                              # noqa: BLE001
        return False, "iyzico yanıtı okunamadı (kod %s)." % r.status_code, ""
    if d.get("status") == "success":
        return True, "", "Bağlantı çalışıyor (%s ortamı)." % ("canlı" if k.get("mode") == "canli" else "deneme")
    return False, "iyzico kabul etmedi: %s" % (d.get("errorMessage") or "kod %s" % r.status_code)[:140], ""


def _p_telegram(k):
    r = _istek("GET", "https://api.telegram.org/bot%s/getMe" % k["token"])
    try:
        d = r.json()
    except Exception:                                              # noqa: BLE001
        return False, "Telegram yanıtı okunamadı", ""
    if not d.get("ok"):
        return False, "Telegram bot anahtarını kabul etmedi.", ""
    return True, "", "Bağlantı çalışıyor. Bot: @%s" % (d.get("result") or {}).get("username", "")


def _p_cloudflare(k):
    r = _istek("GET", "https://api.cloudflare.com/client/v4/user/tokens/verify", headers={"Authorization": "Bearer " + k["token"]})
    try:
        d = r.json()
    except Exception:                                              # noqa: BLE001
        return False, "Cloudflare yanıtı okunamadı", ""
    if not d.get("success"):
        return False, "Cloudflare belirteci kabul edilmedi.", ""
    return True, "", "Bağlantı çalışıyor (belirteç %s)." % (d.get("result") or {}).get("status", "etkin")


def _p_anthropic(k):
    r = _istek("GET", "https://api.anthropic.com/v1/models", headers={"x-api-key": k["api_key"], "anthropic-version": "2023-06-01"})
    if r.status_code in (401, 403):
        return False, "Anthropic anahtarı kabul etmedi.", ""
    if r.status_code >= 400:
        return False, "Anthropic yanıt vermedi (kod %s)." % r.status_code, ""
    return True, "", "Bağlantı çalışıyor, anahtar kabul edildi."


def _p_openai(k):
    r = _istek("GET", "https://api.openai.com/v1/models", headers={"Authorization": "Bearer " + k["api_key"]})
    if r.status_code in (401, 403):
        return False, "OpenAI anahtarı kabul etmedi.", ""
    if r.status_code >= 400:
        return False, "OpenAI yanıt vermedi (kod %s)." % r.status_code, ""
    return True, "", "Bağlantı çalışıyor, anahtar kabul edildi."


def _p_resend(k):
    r = _istek("GET", "https://api.resend.com/domains", headers={"Authorization": "Bearer " + k["api_key"]})
    if r.status_code in (401, 403):
        return False, "Resend anahtarı kabul etmedi (gönderim-only anahtar ise bu deneme reddedilir; gönderimi ayrıca deneyin).", ""
    if r.status_code >= 400:
        return False, "Resend yanıt vermedi (kod %s)." % r.status_code, ""
    return True, "", "Bağlantı çalışıyor, anahtar kabul edildi."


def _p_sendgrid(k):
    r = _istek("GET", "https://api.sendgrid.com/v3/scopes", headers={"Authorization": "Bearer " + k["api_key"]})
    if r.status_code in (401, 403):
        return False, "SendGrid anahtarı kabul etmedi.", ""
    if r.status_code >= 400:
        return False, "SendGrid yanıt vermedi (kod %s)." % r.status_code, ""
    return True, "", "Bağlantı çalışıyor, anahtar kabul edildi."


PROBES = {"facebook_sayfa": _p_facebook_sayfa, "instagram": _p_instagram, "meta_katalog": _p_meta_katalog, "meta_pixel": _p_meta_pixel,
          "whatsapp": _p_whatsapp, "smtp": _p_smtp, "google_maps": _p_google_maps, "recaptcha": _p_recaptcha, "turnstile": _p_turnstile,
          "stripe": _p_stripe, "paypal": _p_paypal, "iyzico": _p_iyzico, "telegram": _p_telegram, "cloudflare": _p_cloudflare,
          "anthropic": _p_anthropic, "openai": _p_openai, "resend": _p_resend, "sendgrid": _p_sendgrid}

YOK = ("Bilgiler kaydedildi ve biçimi denetlendi. Bu bağlantının ücretsiz sorgulanabilen bir doğrulama ucu olmadığı için "
       "canlı deneme yapılmadı; ilk gerçek kullanımda doğrulanır.")


async def dene(pid, keys):
    """(tamam, hata, mesaj). keys çözülmüş alanlardır."""
    fn = PROBES.get(pid)
    if not fn:
        return True, "", YOK
    try:
        return await asyncio.to_thread(fn, keys)
    except Exception as e:                                         # noqa: BLE001
        return False, "Bağlantı kurulamadı: %s" % str(e)[:160], ""


def gorunum(p, row):
    row = row or {}
    keys = row.get("keys") or {}
    on, ok = bool(row.get("on")), bool(row.get("ok"))
    if p["id"] == "gsc":
        durum = "bagli" if row.get("ok") else "yok"
    else:
        durum = "bagli" if (on and ok) else ("hata" if row.get("err") else ("kapali" if (keys and ok and not on) else ("kurulum" if keys else "yok")))
    return {"id": p["id"], "group": p["group"], "name": p["name"], "desc": p["desc"], "where": p["where"], "can_test": p["can_test"],
            "fields": [dict(f, value=(mask(ac(keys.get(f["key"]))) if f["secret"] else _t(keys.get(f["key"]))),
                            filled=bool(keys.get(f["key"]))) for f in p["fields"]],
            "on": on, "ok": ok, "state": durum, "err": row.get("err") or "", "msg": row.get("msg") or "",
            "last_ok": row.get("last_ok") or "", "at": row.get("at") or ""}


def register(api_router, db, deps):
    adm = deps["require_admin"]

    def owner():
        if tenant.current():
            raise HTTPException(403, "Bu işlem yalnız platform sahibi içindir")

    async def depo():
        return await db.app_settings.find_one({"_id": "baglanti"}, {"_id": 0}) or {}

    async def yaz(pid, row):
        await db.app_settings.update_one({"_id": "baglanti"}, {"$set": {"items.%s" % pid: row}}, upsert=True)

    async def gunluk(pid, olay, not_=""):
        await db.app_settings.update_one({"_id": "baglanti_log"}, {"$push": {"items": {"$each": [
            {"id": uuid.uuid4().hex[:8], "at": _now(), "pid": pid, "olay": olay, "not": _t(not_, 200)}], "$slice": -200}}}, upsert=True)

    async def gsc_satiri():
        d = await db.app_settings.find_one({"_id": "gsc"}, {"_id": 0}) or {}
        sa = d.get("sa") or {}
        okey = bool(sa.get("client_email") and d.get("site"))
        return {"ok": okey, "on": okey, "msg": ("Mülk: %s · Hesap: %s" % (d.get("site"), sa.get("client_email"))) if okey else ""}

    @api_router.get("/admin/baglanti")
    async def liste(_: dict = Depends(adm)):
        owner()
        d = (await depo()).get("items") or {}
        items = []
        for p in CATALOG:
            row = d.get(p["id"])
            if p["id"] == "gsc":
                row = await gsc_satiri()
            items.append(gorunum(p, row))
        grp = []
        for gid, ad, alt in GROUPS:
            li = [i for i in items if i["group"] == gid]
            grp.append({"id": gid, "name": ad, "desc": alt, "n": len(li), "bagli": sum(1 for i in li if i["state"] == "bagli")})
        return {"groups": grp, "items": items,
                "counts": {"bagli": sum(1 for i in items if i["state"] == "bagli"), "hata": sum(1 for i in items if i["state"] == "hata"),
                           "toplam": len(items)}}

    @api_router.put("/admin/baglanti/{pid}")
    async def kaydet(pid: str, payload: dict, _: dict = Depends(adm)):
        owner()
        p = BY_ID.get(pid)
        if not p or pid == "gsc":
            raise HTTPException(404, "Bağlantı bulunamadı")
        d = ((await depo()).get("items") or {}).get(pid) or {}
        eski = d.get("keys") or {}
        gelen = payload.get("keys") or {}
        yeni, degisti = {}, False
        for f in p["fields"]:
            k = f["key"]
            v = _t(gelen[k], 4000 if f["type"] == "area" else 400) if k in gelen else None
            if f["secret"]:
                if v is None or v == "" or v.startswith(MASK):
                    yeni[k] = eski.get(k, "")
                else:
                    yeni[k] = kilitle(v)
            else:
                yeni[k] = eski.get(k, "") if v is None else v
            if yeni[k] != eski.get(k, ""):
                degisti = True
        if "mode" in [f["key"] for f in p["fields"]] and not yeni.get("mode"):
            yeni["mode"] = "test"
        cozulmus = acik_anahtarlar(p, yeni)
        tamam, hata = check(pid, cozulmus)
        row = dict(d)
        row.update(keys=yeni, at=_now())
        if degisti:
            row.update(ok=False, msg="", err="", last_ok="")
        if not p["can_test"] and tamam and any(yeni.values()):
            row.update(ok=True, err="", msg="Biçim denetlendi. Bu bağlantının canlı deneme ucu yok; ilk kullanımda doğrulanır.")
        if "on" in payload:
            istek = bool(payload["on"])
            if istek and not tamam:
                raise HTTPException(422, hata)
            row["on"] = istek
        if not tamam and any(yeni.values()):
            row["err"] = hata
        await yaz(pid, row)
        await gunluk(pid, "kaydedildi" if degisti else "güncellendi", "açık" if row.get("on") else "kapalı")
        return {"ok": True, "item": gorunum(p, row)}

    @api_router.post("/admin/baglanti/{pid}/test")
    async def test(pid: str, _: dict = Depends(adm)):
        owner()
        p = BY_ID.get(pid)
        if not p or pid == "gsc":
            raise HTTPException(404, "Bağlantı bulunamadı")
        d = ((await depo()).get("items") or {}).get(pid) or {}
        if not d.get("keys"):
            raise HTTPException(422, "Önce bilgileri kaydedin")
        k = acik_anahtarlar(p, d["keys"])
        tamam, hata = check(pid, k)
        msg = ""
        if tamam:
            tamam, hata, msg = await dene(pid, k)
        row = dict(d)
        row.update(ok=bool(tamam), err="" if tamam else hata, msg=msg if tamam else "", at=_now())
        if tamam:
            row["last_ok"] = _now()
        else:
            row["on"] = False
        await yaz(pid, row)
        await gunluk(pid, "deneme tamam" if tamam else "deneme hatası", msg if tamam else hata)
        return {"ok": bool(tamam), "detail": msg if tamam else hata, "item": gorunum(p, row)}

    @api_router.delete("/admin/baglanti/{pid}")
    async def kaldir(pid: str, _: dict = Depends(adm)):
        owner()
        if pid not in BY_ID or pid == "gsc":
            raise HTTPException(404, "Bağlantı bulunamadı")
        await db.app_settings.update_one({"_id": "baglanti"}, {"$unset": {"items.%s" % pid: ""}}, upsert=True)
        await gunluk(pid, "silindi")
        return {"ok": True}

    @api_router.get("/admin/baglanti-gunluk")
    async def gunluk_liste(_: dict = Depends(adm)):
        owner()
        d = await db.app_settings.find_one({"_id": "baglanti_log"}, {"_id": 0}) or {}
        return {"items": list(reversed(d.get("items") or []))[:60]}

    @api_router.get("/public/olcum")
    async def herkese_acik():
        """Siteye basılabilecek herkese açık kimlikler (yalnız açık ve doğrulanmış olanlar). Gizli alan asla dönmez."""
        d = (await depo()).get("items") or {}
        out = {}
        for pid, row in d.items():
            p = BY_ID.get(pid)
            if not p or not p["public"] or not (row.get("on") and (row.get("ok") or not p["can_test"])):
                continue
            ks = row.get("keys") or {}
            out[pid] = {k: ks.get(k, "") for k in p["public"] if ks.get(k)}
        return out


async def anahtar(db, pid):
    """Başka modüller için: açık ve doğrulanmış bağlantının çözülmüş anahtarları; yoksa None."""
    p = BY_ID.get(pid)
    row = (((await db.app_settings.find_one({"_id": "baglanti"}, {"_id": 0})) or {}).get("items") or {}).get(pid)
    if not p or not row or not row.get("on"):
        return None
    return acik_anahtarlar(p, row.get("keys") or {})
