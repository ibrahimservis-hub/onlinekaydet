# -*- coding: utf-8 -*-
"""Entegrasyon merkezinin gerçek bağlantı denemesi.

Yalnız okuyan, ücret doğurmayan uçlar kullanılır: bakiye sorgusu, hesap bilgisi, adres listesi.
Hiçbir SMS gönderilmez, hiçbir kayıt değiştirilmez. Doğrulanmış ucu olmayan sağlayıcıda
uydurma adres kullanmak yerine açıkça "canlı doğrulama yok" denir; alan denetimi yine yapılır.

Uçlar:
  verimor      GET  https://sms.verimor.com.tr/v2/balance          (notify.py ile aynı API)
  iletimerkezi POST https://api.iletimerkezi.com/v1/get-balance/json
  trendyol     GET  https://apigw.trendyol.com/integration/sellers/{sellerId}/addresses
  smtp         SMTP STARTTLS + oturum açma
  whatsapp     GET  https://graph.facebook.com/{phone_id}
"""
import asyncio
import base64
import json
import smtplib
import ssl

ZAMAN = 15


def _istek(yontem, url, **kw):
    """Ağ çağrısı. Testler bu işlevi değiştirir."""
    import requests
    kw.setdefault("timeout", ZAMAN)
    return requests.request(yontem, url, **kw)


def _a(row, k):
    return str(((row.get("keys") or {}).get(k) or "")).strip()


# ---------------------------------------------------------------- sağlayıcılar
def _verimor(row):
    r = _istek("GET", "https://sms.verimor.com.tr/v2/balance",
               params={"username": _a(row, "user"), "password": _a(row, "pass")})
    if r.status_code == 401:
        return False, "Kullanıcı adı ya da parola kabul edilmedi.", ""
    if r.status_code >= 400:
        return False, "Verimor yanıt vermedi (kod %s)." % r.status_code, ""
    try:
        d = r.json()
        bak = d.get("balance", d.get("credit", ""))
    except Exception:                                              # noqa: BLE001
        bak = (r.text or "").strip()[:40]
    return True, "", "Bağlantı çalışıyor. Bakiye: %s" % (bak if bak != "" else "okunamadı")


def _iletimerkezi(row):
    body = {"request": {"authentication": {"key": _a(row, "user"), "hash": _a(row, "pass")}}}
    r = _istek("POST", "https://api.iletimerkezi.com/v1/get-balance/json", json=body)
    try:
        d = r.json()["response"]
        st = d.get("status") or {}
    except Exception:                                              # noqa: BLE001
        return False, "İleti Merkezi yanıtı okunamadı: %s" % (r.text or "")[:80], ""
    if str(st.get("code")) != "200":
        return False, "İleti Merkezi: %s (kod %s)" % (st.get("message") or "kabul edilmedi", st.get("code")), ""
    b = d.get("balance") or {}
    return True, "", "Bağlantı çalışıyor. Bakiye: %s TL · %s SMS" % (b.get("amount", "?"), b.get("sms", "?"))


def _trendyol(row):
    sid = _a(row, "seller_id")
    tok = base64.b64encode(("%s:%s" % (_a(row, "api_key"), _a(row, "api_secret"))).encode()).decode()
    r = _istek("GET", "https://apigw.trendyol.com/integration/sellers/%s/addresses" % sid,
               headers={"Authorization": "Basic " + tok, "User-Agent": "%s - SelfIntegration" % sid,
                        "Accept": "application/json"})
    if r.status_code in (401, 403):
        return False, "Trendyol anahtarlarını kabul etmedi. API Key, Secret ve Satıcı No'yu kontrol edin.", ""
    if r.status_code == 404:
        return False, "Trendyol bu satıcı numarasını bulamadı.", ""
    if r.status_code >= 400:
        return False, "Trendyol yanıt vermedi (kod %s)." % r.status_code, ""
    try:
        n = len((r.json() or {}).get("supplierAddresses") or [])
    except Exception:                                              # noqa: BLE001
        n = 0
    return True, "", "Bağlantı çalışıyor. Tanımlı adres: %d" % n


def _smtp(row):
    host, kul, sif = _a(row, "host"), _a(row, "user"), _a(row, "pass")
    try:
        port = int(_a(row, "port") or 587)
    except ValueError:
        return False, "Port bir sayı olmalı (çoğu sunucuda 587).", ""
    try:
        if port == 465:
            s = smtplib.SMTP_SSL(host, port, timeout=ZAMAN, context=ssl.create_default_context())
        else:
            s = smtplib.SMTP(host, port, timeout=ZAMAN)
            s.ehlo()
            try:
                s.starttls(context=ssl.create_default_context())
                s.ehlo()
            except smtplib.SMTPNotSupportedError:
                pass
        try:
            if kul:
                s.login(kul, sif)
        finally:
            try:
                s.quit()
            except Exception:                                      # noqa: BLE001
                pass
    except smtplib.SMTPAuthenticationError:
        return False, "E-posta sunucusu kullanıcı adı ya da parolayı kabul etmedi.", ""
    except (OSError, smtplib.SMTPException) as e:
        return False, "E-posta sunucusuna bağlanılamadı: %s" % str(e)[:120], ""
    return True, "", "Bağlantı çalışıyor, oturum açıldı."


def _whatsapp(row):
    r = _istek("GET", "https://graph.facebook.com/%s" % _a(row, "phone_id"),
               params={"access_token": _a(row, "token"), "fields": "display_phone_number,verified_name"})
    if r.status_code >= 400:
        try:
            m = (r.json().get("error") or {}).get("message") or ""
        except Exception:                                          # noqa: BLE001
            m = ""
        return False, "WhatsApp kabul etmedi: %s" % (m or "kod %s" % r.status_code)[:140], ""
    try:
        d = r.json()
        ad = d.get("verified_name") or d.get("display_phone_number") or ""
    except Exception:                                              # noqa: BLE001
        ad = ""
    return True, "", "Bağlantı çalışıyor.%s" % ((" Numara: " + ad) if ad else "")


PROBES = {"verimor": _verimor, "iletimerkezi": _iletimerkezi, "trendyol": _trendyol,
          "smtp": _smtp, "whatsapp": _whatsapp}

YOK = ("Bilgiler kaydedildi ve alanlar denetlendi. Bu sağlayıcının ücretsiz sorgulanabilen "
       "bir doğrulama ucu olmadığı için canlı deneme yapılmadı; ilk gerçek işlemde doğrulanır.")


async def probe(pid, row):
    """(tamam, hata, mesaj). Ağ çağrısı ayrı iş parçacığında yapılır."""
    fn = PROBES.get(pid)
    if not fn:
        return True, "", YOK
    try:
        return await asyncio.to_thread(fn, row)
    except Exception as e:                                         # noqa: BLE001
        return False, "Bağlantı kurulamadı: %s" % str(e)[:160], ""
