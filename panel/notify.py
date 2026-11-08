"""Bildirim kanalları: SMS / WhatsApp / e-posta gönderim adaptörü.

Sağlayıcı bilgisi (anahtar, URL, SMTP) panelden girilir; kod bu bilgi olmadan hiçbir şey göndermez.
Desteklenen sağlayıcılar:
  webhook : herhangi bir HTTP servisi (Zapier/Make/n8n/kendi SMS firmanızın REST API'si) — en esnek
  verimor : SMS (Verimor HTTP API v2, send.json) -- canlı hesapla denenmedi
  netgsm  : SMS (Netgsm GET API)            -- canlı hesapla denenmedi
  twilio  : SMS + WhatsApp (Twilio REST)    -- canlı hesapla denenmedi
  smtp    : e-posta
Her gönderim `outbox` koleksiyonuna yazılır (durum, hata).
"""
import tenant
import asyncio
import secrets
import json
import logging
import re
import smtplib
import ssl
import uuid
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from typing import Optional

import requests

log = logging.getLogger("notify")

MASK = "********"
SECRET_KEYS = {("verimor", "password"), ("netgsm", "password"), ("iletimerkezi", "hash"), ("twilio", "auth_token"), ("smtp", "password")}

TECH_TEMPLATE = ("Merhaba {usta}, size yeni bir servis kaydı atandı.\nKayıt No: {is_no}\nMüşteri: {musteri}\nAdres: {adres}\n"
                 "Cihaz: {cihaz}\nArıza: {ariza}\nZaman: {zaman}\nKayıt detayı: {link}\nHayırlı işler dileriz.")
WELCOME_TEMPLATE = ("Merhaba {ad}, ServisPlus usta paneline hoş geldiniz.\nGiriş adresi: {link}\nKullanıcı adı: {kullanici}\nŞifre: {sifre}\n"
                    "Girişten sonra şifrenizi değiştirmenizi öneririz. Hayırlı işler dileriz.")
DEFAULTS = {
    "provider": "none",                       # none | webhook | verimor | netgsm | twilio
    "webhook": {"url": "", "headers": "", "body_template": '{"channel":"{channel}","to":"{to}","text":"{text}"}'},
    "verimor": {"username": "", "password": "", "source_addr": ""},
    "netgsm": {"usercode": "", "password": "", "header": ""},
    "iletimerkezi": {"key": "", "hash": "", "sender": ""},
    "twilio": {"account_sid": "", "auth_token": "", "from_sms": "", "from_whatsapp": ""},
    "smtp": {"host": "", "port": 587, "user": "", "password": "", "from_addr": "", "tls": True},
    "admin_alert": {"enabled": False, "min_severity": "high", "channels": ["sms"], "phones": [], "emails": []},
    "customer": {
        "enabled": False, "channel": "whatsapp", "fallback_sms": True, "base_url": "https://bayi.servisplus.net.tr",
        "events": {"assigned": True, "on_the_way": True, "done": True, "survey": False},
        "templates": {
            "assigned": "Merhaba {ad}, servis kaydınız alındı. Ustamız {usta} sizinle ilgilenecek. Takip: {link}",
            "on_the_way": "Merhaba {ad}, ustamız {usta} yola çıktı. Takip: {link}",
            "done": "Merhaba {ad}, servis işleminiz tamamlandı. Bizi tercih ettiğiniz için teşekkürler.",
            "survey": "Merhaba {ad}, ServisPlus hizmetimizi 1 ile 5 arasında puanlar mısınız? {link}",
        },
    },
    "technician": {
        "enabled": None, "channel": "", "base_url": "https://bayi.servisplus.net.tr",     # enabled=None / channel="" → müşteri mesajı ayarını izler
        "template": TECH_TEMPLATE,
        "welcome_enabled": None, "welcome_template": WELCOME_TEMPLATE,                    # yeni usta hesabı → giriş bilgileri
    },
    "reminder": {"enabled": False, "minutes_before": 60, "customer": True, "technician": True,
                 "customer_template": "Merhaba {ad}, ServisPlus randevunuz {zaman} saatindedir. Ustamız {usta} gelecektir. Takip: {link}",
                 "tech_template": "Hatırlatma: {zaman} saatinde {musteri} - {adres} adresinde servis randevunuz var (Kayıt {is_no}). Detay: {link}"},
    "weekly_report": {"enabled": False, "emails": [], "weekday": 0, "hour": 8, "last_sent": ""},
    "daily_summary": {"enabled": False, "channel": "whatsapp", "phones": [], "hour": 8, "last_sent": ""},     # sabah özeti (bugün/atanmamış/gecikmiş)
}
SEV = {"low": 1, "medium": 2, "high": 3}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _merge(base, over):
    out = json.loads(json.dumps(base))
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


async def get_settings(db) -> dict:
    s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
    return _merge(DEFAULTS, s.get("notify") or {})


def masked(cfg: dict) -> dict:
    out = json.loads(json.dumps(cfg))
    for sec, key in SECRET_KEYS:
        if out.get(sec, {}).get(key):
            out[sec][key] = MASK
    return out


async def save_settings(db, incoming: dict) -> dict:
    cur = await get_settings(db)
    new = _merge(cur, incoming or {})
    for sec, key in SECRET_KEYS:                       # maskeli değer geldiyse eskisini koru
        if (incoming or {}).get(sec, {}).get(key) == MASK:
            new[sec][key] = cur[sec][key]
    await db.app_settings.update_one({"_id": "global"}, {"$set": {"notify": new}}, upsert=True)
    return new


def norm_msisdn(p: str) -> str:
    d = re.sub(r"\D", "", p or "")
    if d.startswith("00"):
        d = d[2:]
    if len(d) == 10:
        d = "90" + d
    elif len(d) == 11 and d.startswith("0"):
        d = "9" + d
    return d


# ---------------------------------------------------------------- sağlayıcılar (senkron; thread'de çalışır)
def _headers(txt: str) -> dict:
    h = {}
    for line in (txt or "").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            h[k.strip()] = v.strip()
    return h


def _send_webhook(cfg, channel, to, text, subject):
    w = cfg["webhook"]
    if not w.get("url"):
        raise RuntimeError("Webhook adresi girilmemiş")
    esc = lambda s: json.dumps(str(s or ""), ensure_ascii=False)[1:-1]
    body = w["body_template"]
    for k, v in (("channel", channel), ("to", to), ("text", text), ("subject", subject)):
        body = body.replace("{" + k + "}", esc(v))
    hd = {"Content-Type": "application/json"}
    hd.update(_headers(w.get("headers", "")))
    r = requests.post(w["url"], data=body.encode("utf-8"), headers=hd, timeout=15)
    if r.status_code >= 300:
        raise RuntimeError(f"Webhook {r.status_code}: {r.text[:200]}")
    return r.text[:200]


def _send_verimor(cfg, channel, to, text, subject):
    v = cfg["verimor"]            # Verimor yalnızca SMS gönderir: kanal "whatsapp" kalmış olsa bile SMS olarak gönderilir
    if not v.get("username") or not v.get("password"):
        raise RuntimeError("Verimor kullanıcı adı / şifre girilmemiş")
    payload = {"username": v["username"], "password": v["password"], "messages": [{"msg": text, "dest": norm_msisdn(to)}]}
    if v.get("source_addr"):
        payload["source_addr"] = v["source_addr"]
    try:
        r = requests.post("https://sms.verimor.com.tr/v2/send.json", data=json.dumps(payload).encode("utf-8"),
                          headers={"Content-Type": "application/json"}, timeout=20)
    except requests.RequestException:
        raise RuntimeError("Verimor sunucusuna bağlanılamadı (internet/engel)") from None
    if r.status_code == 401:
        raise RuntimeError("Verimor: kullanıcı adı/şifre hatalı ya da sunucu IP adresi OİM'de izinli değil")
    if r.status_code != 200:
        code = (r.text or "").strip()[:60]
        hint = {"NUMERIC_SOURCE_ADDRESS_NOT_ALLOWED": "Gönderici başlığı rakamdan oluşamaz; Verimor hesabınızda ONAYLI bir harfli başlık (örn. SERVISPLUS) tanımlı olmalı ve panelde o yazılmalı",
                "INSUFFICIENT_CREDITS": "Kontör yetersiz", "INVALID_SOURCE_ADDRESS": "Gönderici başlığı Verimor'da tanımlı/onaylı değil",
                "INVALID_DESTINATION": "Alıcı numarası geçersiz", "MESSAGE_TOO_LONG": "Mesaj çok uzun"}.get(code, "")
        raise RuntimeError(f"Verimor {r.status_code}: {code}" + (f" — {hint}" if hint else ""))
    return "kampanya:" + (r.text or "").strip()[:40]


def verimor_balance(cfg):
    v = cfg["verimor"]
    if not v.get("username") or not v.get("password"):
        raise RuntimeError("Verimor kullanıcı adı / şifre girilmemiş")
    try:
        r = requests.get("https://sms.verimor.com.tr/v2/balance", params={"username": v["username"], "password": v["password"]}, timeout=15)
    except requests.RequestException:
        raise RuntimeError("Verimor sunucusuna bağlanılamadı (internet/engel)") from None
    if r.status_code == 401:
        raise RuntimeError("Kullanıcı adı/şifre hatalı ya da sunucu IP adresi OİM'de izinli değil")
    if r.status_code != 200:
        raise RuntimeError(f"Verimor {r.status_code}: {(r.text or '')[:120]}")
    return (r.text or "").strip()


def verimor_headers(cfg):
    """Verimor hesabındaki kayıtlı gönderici başlıkları (GET /v2/headers)."""
    v = cfg["verimor"]
    if not v.get("username") or not v.get("password"):
        raise RuntimeError("Verimor kullanıcı adı / şifre girilmemiş")
    try:
        r = requests.get("https://sms.verimor.com.tr/v2/headers", params={"username": v["username"], "password": v["password"]}, timeout=15)
    except requests.RequestException:
        raise RuntimeError("Verimor sunucusuna bağlanılamadı (internet/engel)") from None
    if r.status_code == 401:
        raise RuntimeError("Kullanıcı adı/şifre hatalı ya da sunucu IP adresi OİM'de izinli değil")
    if r.status_code != 200:
        raise RuntimeError(f"Verimor {r.status_code}: {(r.text or '')[:120]}")
    try:
        d = r.json()
    except Exception:                                   # noqa: BLE001
        d = [x.strip() for x in (r.text or "").splitlines() if x.strip()]
    if isinstance(d, dict):
        d = d.get("headers") or list(d.values())
    out = []
    for x in d or []:
        out.append(str(x.get("header") or x.get("name") or x.get("source_addr") or x) if isinstance(x, dict) else str(x))
    return out


def _send_netgsm(cfg, channel, to, text, subject):
    if channel != "sms":
        raise RuntimeError("Netgsm yalnızca SMS destekler")
    n = cfg["netgsm"]
    r = requests.get("https://api.netgsm.com.tr/sms/send/get/", params={
        "usercode": n["usercode"], "password": n["password"], "gsmno": norm_msisdn(to)[-10:],
        "message": text, "msgheader": n["header"], "dil": "TR"}, timeout=20)
    code = (r.text or "").split(" ")[0].strip()
    if code not in ("00", "01", "02"):
        raise RuntimeError(f"Netgsm hata kodu: {r.text[:60]}")
    return r.text[:60]


def _send_iletimerkezi(cfg, channel, to, text, subject):
    """İleti Merkezi JSON API (resmi dokümana göre). Servis bildirimleri işlem mesajıdır: iys='0'."""
    if channel != "sms":
        raise RuntimeError("İleti Merkezi yalnızca SMS destekler")
    n = cfg["iletimerkezi"]
    body = {"request": {"authentication": {"key": n["key"], "hash": n["hash"]},
                        "order": {"sender": n["sender"], "iys": "0",
                                  "message": {"text": text, "receipents": {"number": [norm_msisdn(to)[-10:]]}}}}}
    r = requests.post("https://api.iletimerkezi.com/v1/send-sms/json", json=body, timeout=20)
    try:
        st = r.json()["response"]["status"]
    except Exception:                                    # noqa: BLE001
        raise RuntimeError(f"İleti Merkezi yanıtı okunamadı: {r.text[:80]}")
    if str(st.get("code")) != "200":
        raise RuntimeError(f"İleti Merkezi hata {st.get('code')}: {st.get('message')}")
    return str((r.json()["response"].get("order") or {}).get("id", ""))


def _send_twilio(cfg, channel, to, text, subject):
    t = cfg["twilio"]
    to_n = "+" + norm_msisdn(to)
    if channel == "whatsapp":
        frm, to_n = "whatsapp:" + t["from_whatsapp"], "whatsapp:" + to_n
    else:
        frm = t["from_sms"]
    r = requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{t['account_sid']}/Messages.json",
                      data={"From": frm, "To": to_n, "Body": text}, auth=(t["account_sid"], t["auth_token"]), timeout=20)
    if r.status_code >= 300:
        raise RuntimeError(f"Twilio {r.status_code}: {r.text[:200]}")
    return r.json().get("sid", "")


def _send_smtp(cfg, to, text, subject):
    s = cfg["smtp"]
    if not s.get("host"):
        raise RuntimeError("SMTP sunucusu girilmemiş")
    msg = EmailMessage()
    msg["Subject"] = subject or "ServisPlus bildirimi"
    msg["From"] = s.get("from_addr") or s.get("user")
    msg["To"] = to
    msg.set_content(text)
    port = int(s.get("port") or 587)
    if port == 465:
        srv = smtplib.SMTP_SSL(s["host"], port, timeout=20, context=ssl.create_default_context())
    else:
        srv = smtplib.SMTP(s["host"], port, timeout=20)
        if s.get("tls", True):
            srv.starttls(context=ssl.create_default_context())
    try:
        if s.get("user"):
            srv.login(s["user"], s["password"])
        srv.send_message(msg)
    finally:
        try:
            srv.quit()
        except Exception:
            pass
    return "ok"


def _dispatch(cfg, channel, to, text, subject):
    if channel == "email":
        return _send_smtp(cfg, to, text, subject)
    prov = cfg["provider"]
    if prov == "webhook":
        return _send_webhook(cfg, channel, to, text, subject)
    if prov == "verimor":
        return _send_verimor(cfg, channel, to, text, subject)
    if prov == "netgsm":
        return _send_netgsm(cfg, channel, to, text, subject)
    if prov == "iletimerkezi":
        return _send_iletimerkezi(cfg, channel, to, text, subject)
    if prov == "twilio":
        return _send_twilio(cfg, channel, to, text, subject)
    raise RuntimeError("SMS/WhatsApp sağlayıcısı seçilmemiş")


async def send(db, channel: str, to: str, text: str, subject: str = "", kind: str = "", ref: str = "", cfg: Optional[dict] = None, store_text: Optional[str] = None) -> dict:
    """Mesaj gönderir ve outbox'a yazar. Asla istisna fırlatmaz. store_text: kayıtta saklanacak (şifresi maskelenmiş) metin."""
    cfg = cfg or await get_settings(db)
    doc = {"id": str(uuid.uuid4()), "channel": channel, "to": to, "text": (store_text if store_text is not None else text)[:1500], "subject": subject, "kind": kind,
           "ref": ref, "status": "sending", "error": "", "created_at": _now()}
    try:
        resp = await asyncio.to_thread(_dispatch, cfg, channel, to, text, subject)
        if store_text is None:
            doc["response"] = resp
        doc["status"] = "sent"
    except Exception as e:                              # noqa: BLE001
        doc["status"] = "failed"
        doc["error"] = str(e)[:300]
        log.warning("bildirim gönderilemedi: %s", e)
    await db.outbox.insert_one(dict(doc))
    doc.pop("_id", None)
    return doc


# ---------------------------------------------------------------- yönetici güvenlik uyarısı
async def dispatch_alert(db, alert: dict):
    try:
        cfg = await get_settings(db)
        a = cfg["admin_alert"]
        if not a.get("enabled") or SEV.get(alert.get("severity"), 1) < SEV.get(a.get("min_severity", "high"), 3):
            return
        text = f"[ServisPlus Güvenlik] {alert.get('text', '')}"
        for ch in a.get("channels", []):
            targets = a.get("emails", []) if ch == "email" else a.get("phones", [])
            for t in targets:
                await send(db, ch, t, text, subject="ServisPlus güvenlik uyarısı", kind="security_alert", ref=alert.get("id", ""), cfg=cfg)
    except Exception as e:                              # noqa: BLE001
        log.warning("alert dispatch: %s", e)


async def push_admins(db, title: str, body: str = "", url: str = "/admin"):
    """Tüm yöneticilerin kayıtlı cihazlarına (Android uygulaması / web push) bildirim. Asla istisna fırlatmaz."""
    try:
        import fieldops                                  # geç içe aktarma: döngüsel bağımlılığı önler
        admins = [u["id"] async for u in db.users.find({"role": "admin"}, {"_id": 0, "id": 1})]
        await fieldops.push_to(db, admins, title, (body or "")[:240], url)
    except Exception as e:                              # noqa: BLE001
        log.warning("push_admins: %s", e)


async def notify_owner(db, text: str, kind: str = "system"):
    """Hata/yedek uyarıları: yönetici uyarı kanallarına gönderir (severity kontrolü yok).
    Ayrıca tüm yöneticilerin kayıtlı cihazlarına (Android uygulaması / web push) bildirim gönderir."""
    try:
        import fieldops                                  # geç içe aktarma: döngüsel bağımlılığı önler
        admins = [u["id"] async for u in db.users.find({"role": "admin"}, {"_id": 0, "id": 1})]
        await fieldops.push_to(db, admins, "ServisPlus", text[:200], "/admin")
    except Exception as e:                              # noqa: BLE001
        log.warning("yönetici push: %s", e)
    cfg = await get_settings(db)
    a = cfg["admin_alert"]
    if not a.get("enabled"):
        return
    for ch in a.get("channels", []):
        for t in (a.get("emails", []) if ch == "email" else a.get("phones", [])):
            await send(db, ch, t, text, subject="ServisPlus sistem uyarısı", kind=kind, cfg=cfg)


_BG_TASKS = set()


def _bg(coro):
    """Bildirimi arkaplana atar: müşterinin isteği yöneticiye bildirim gidene kadar BEKLEMEZ. Hata istek akışını bozmaz."""
    try:
        t = asyncio.get_running_loop().create_task(coro)
    except RuntimeError:                                 # çalışan döngü yoksa (beklenmez): doğrudan kapat
        coro.close()
        return None
    _BG_TASKS.add(t)
    t.add_done_callback(_BG_TASKS.discard)
    return t


async def _t(coro, sn: float = 4.0):
    """Bildirimi arkaplan görevi olarak başlatır ama en çok `sn` saniye bekler: normalde bildirim istek bitmeden iletilir
    (barındırma, yanıt bittikten sonra süreci kısıtlıyorsa kaybolmaz); yavaşsa istek yine de takılmaz, görev sürer."""
    t = _bg(coro)
    if t is None:
        return None
    try:
        await asyncio.wait_for(asyncio.shield(t), sn)
    except Exception:                                    # noqa: BLE001  (zaman aşımı/iptal: görev arkada sürer)
        pass
    return t


async def push_admins_t(db, title: str, body: str = "", url: str = "/admin"):
    return await _t(push_admins(db, title, body, url))


async def notify_owner_t(db, text: str, kind: str = "system"):
    return await _t(notify_owner(db, text, kind))


def push_admins_bg(db, title: str, body: str = "", url: str = "/admin"):
    return _bg(push_admins(db, title, body, url))


def notify_owner_bg(db, text: str, kind: str = "system"):
    return _bg(notify_owner(db, text, kind))


# ---------------------------------------------------------------- müşteri otomatik mesajı
def render(tpl: str, vars_: dict) -> str:
    out = tpl
    for k, v in vars_.items():
        out = out.replace("{" + k + "}", str(v or ""))
    return out.strip()


async def job_event(db, event: str, job: dict):
    """İş olayında (atandı / yolda / tamamlandı / anket) müşteriye otomatik mesaj. Ayar kapalıysa hiçbir şey yapmaz."""
    try:
        cfg = await get_settings(db)
        c = cfg["customer"]
        if not c.get("enabled") or not c.get("events", {}).get(event):
            return None
        phone = job.get("customer_phone") or ""
        if not norm_msisdn(phone):
            return None
        if await db.outbox.find_one({"kind": "job_" + event, "ref": job["id"], "status": "sent"}):
            return None                                  # aynı olay için çift gönderim yok
        link = ""
        if job.get("track_token"):
            link = (c.get("base_url") or "https://bayi.servisplus.net.tr").rstrip("/") + "/takip/" + tenant.public_token(job["track_token"])
        text = render(c["templates"].get(event, ""), {
            "ad": (job.get("customer_name") or "").split(" ")[0], "usta": job.get("assigned_technician_name", ""),
            "link": link, "is_no": job.get("job_number", "")})
        if not text:
            return None
        ch = c.get("channel") or "whatsapp"
        res = await send(db, ch, phone, text, kind="job_" + event, ref=job["id"], cfg=cfg)
        # WhatsApp iletilemediyse (şablon onayı yok, numara WhatsApp'ta değil vb.) SMS ile bir kez daha dene
        if res and res.get("status") == "failed" and ch == "whatsapp" and c.get("fallback_sms", True) and cfg.get("provider") != "none":
            res2 = await send(db, "sms", phone, text, kind="job_" + event, ref=job["id"], cfg=cfg)
            res2["fallback"] = True
            return res2
        return res
    except Exception as e:                              # noqa: BLE001
        log.warning("job_event: %s", e)
        return None


async def technician_event(db, job: dict):
    """Admin ustaya iş atadığında ustanın telefonuna (WhatsApp/SMS) otomatik mesaj. Ayar kapalıysa hiçbir şey yapmaz.
    Müşteri telefonu mesaja KONMAZ (usta gizlilik modları ile uyumlu)."""
    try:
        cfg = await get_settings(db)
        t = cfg.get("technician") or {}
        en = t.get("enabled")
        if en is None:
            en = (cfg.get("customer") or {}).get("enabled")      # ayrıca açılmadıysa müşteri mesajı ile birlikte çalışır
        chan = t.get("channel") or (cfg.get("customer") or {}).get("channel") or "whatsapp"
        if not en or cfg.get("provider") == "none":
            return None
        tid = job.get("assigned_technician_id")
        if not tid:
            return None
        u = await db.users.find_one({"id": tid}, {"_id": 0, "name": 1, "phone": 1})
        if not u or not norm_msisdn(u.get("phone") or ""):
            await db.outbox.insert_one({"id": str(uuid.uuid4()), "channel": chan, "to": (u or {}).get("phone", ""), "text": "", "subject": "", "kind": "tech_assigned",
                                        "ref": job["id"] + ":" + tid, "status": "failed", "error": "Ustanın telefon numarası kayıtlı değil", "created_at": _now()})
            return None
        ref = job["id"] + ":" + tid
        if await db.outbox.find_one({"kind": "tech_assigned", "ref": ref, "status": "sent"}):
            return None
        when = job.get("scheduled_at") or ""
        text = render(t.get("template", ""), {
            "usta": (u.get("name") or "").split(" ")[0], "is_no": job.get("job_number", ""), "musteri": job.get("customer_name", ""),
            "adres": " ".join(x for x in [job.get("customer_address"), job.get("customer_district"), job.get("customer_city")] if x),
            "cihaz": " ".join(x for x in [job.get("device_brand_name"), job.get("device_model"), job.get("device_type")] if x),
            "ariza": (job.get("fault_description") or "")[:300], "zaman": when[:16].replace("T", " ") if when else "En kısa sürede",
            "link": (t.get("base_url") or "").rstrip("/") + "/tech/jobs/" + job["id"]})
        if not text:
            return None
        return await send(db, chan, u["phone"], text, kind="tech_assigned", ref=ref, cfg=cfg)
    except Exception as e:                              # noqa: BLE001
        log.warning("technician_event: %s", e)
        return None


async def tech_welcome(db, user: dict, password: str):
    """Yeni usta hesabı açılınca (panelden manuel ya da başvuru onayı) ustanın telefonuna link + kullanıcı adı + şifre gönderir.
    Şifre outbox kaydında maskelenir. Ayar kapalı / sağlayıcı yok ise hiçbir şey yapmaz."""
    try:
        cfg = await get_settings(db)
        t = cfg.get("technician") or {}
        en = t.get("welcome_enabled")
        if en is None:
            en = (cfg.get("customer") or {}).get("enabled")
        if not en or cfg.get("provider") == "none" or not password:
            return None
        chan = t.get("channel") or (cfg.get("customer") or {}).get("channel") or "whatsapp"
        phone = user.get("phone") or ""
        ref = user.get("id", "")
        if not norm_msisdn(phone):
            await db.outbox.insert_one({"id": str(uuid.uuid4()), "channel": chan, "to": phone, "text": "", "subject": "", "kind": "tech_welcome", "ref": ref,
                                        "status": "failed", "error": "Ustanın telefon numarası kayıtlı değil", "created_at": _now()})
            return None
        vals = {"ad": (user.get("name") or "").split(" ")[0], "kullanici": user.get("email", ""), "sifre": password,
                "link": (t.get("base_url") or "https://bayi.servisplus.net.tr").rstrip("/") + "/login"}
        tpl = t.get("welcome_template") or WELCOME_TEMPLATE
        text = render(tpl, vals)
        masked = render(tpl, dict(vals, sifre="********"))
        return await send(db, chan, phone, text, kind="tech_welcome", ref=ref, cfg=cfg, store_text=masked)
    except Exception as e:                              # noqa: BLE001
        log.warning("tech_welcome: %s", e)
        return None


# ---------------------------------------------------------------- haftalık rapor
async def weekly_summary(db) -> dict:
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    jobs = await db.service_jobs.find({"created_at": {"$gte": since}}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(5000)
    done = await db.service_jobs.find({"completed_at": {"$gte": since}}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(5000)
    rev = sum(float(j.get("total_amount", 0) or 0) for j in done)
    tx = await db.cash_transactions.find({"created_at": {"$gte": since}}, {"_id": 0}).to_list(5000)
    inc = sum(float(t.get("amount", 0)) for t in tx if t.get("type") == "gelir")
    exp = sum(float(t.get("amount", 0)) for t in tx if t.get("type") == "gider")
    rated = [j["customer_rating"] for j in done if j.get("customer_rating")]
    src = {}
    for j in jobs:
        src[j.get("source_channel") or "belirtilmemiş"] = src.get(j.get("source_channel") or "belirtilmemiş", 0) + 1
    return {"new_jobs": len(jobs), "completed": len(done), "revenue": round(rev, 2), "cash_in": round(inc, 2),
            "cash_out": round(exp, 2), "avg_rating": round(sum(rated) / len(rated), 2) if rated else 0, "sources": src,
            "open_alerts": await db.security_alerts.count_documents({"status": "open"})}


def weekly_text(s: dict) -> str:
    srcs = ", ".join(f"{k}: {v}" for k, v in sorted(s["sources"].items(), key=lambda x: -x[1])) or "-"
    return (f"ServisPlus haftalık özet (son 7 gün)\n\nYeni iş: {s['new_jobs']}\nTamamlanan: {s['completed']}\n"
            f"Servis cirosu: {s['revenue']:.2f} TL\nKasa girişi: {s['cash_in']:.2f} TL\nKasa gideri: {s['cash_out']:.2f} TL\n"
            f"Ortalama puan: {s['avg_rating'] or '-'}\nKaynaklar: {srcs}\nAçık güvenlik uyarısı: {s['open_alerts']}\n")


async def send_weekly_report(db, force=False):
    cfg = await get_settings(db)
    w = cfg["weekly_report"]
    if not force and not w.get("enabled"):
        return {"sent": 0}
    s = await weekly_summary(db)
    sent = 0
    for to in w.get("emails", []):
        r = await send(db, "email", to, weekly_text(s), subject="ServisPlus haftalık özet", kind="weekly_report", cfg=cfg)
        sent += 1 if r["status"] == "sent" else 0
    await db.app_settings.update_one({"_id": "global"}, {"$set": {"notify.weekly_report.last_sent": _now()}}, upsert=True)
    return {"sent": sent, "summary": s}


# ---------------------------------------------------------------- günlük özet + anket süpürmesi (zamanlayıcıdan çağrılır)
_DONE_ST = ["tamamlandi", "faturalandi", "iptal"]


async def daily_numbers(db, tz) -> dict:
    now_l = datetime.now(tz)
    today = now_l.strftime("%Y-%m-%d")
    nowkey = now_l.strftime("%Y-%m-%dT%H:%M")
    openq = {"status": {"$nin": _DONE_ST}}
    today_n, unassigned, overdue, quotes, msgs = await asyncio.gather(
        db.service_jobs.count_documents({**openq, "scheduled_at": {"$regex": "^" + today}}),
        db.service_jobs.count_documents({**openq, "$or": [{"assigned_technician_id": ""}, {"assigned_technician_id": None}, {"assigned_technician_id": {"$exists": False}}]}),
        db.service_jobs.count_documents({**openq, "scheduled_at": {"$ne": "", "$lt": nowkey, "$exists": True}}),
        db.price_quotes.count_documents({"status": "beklemede"}),
        db.contact_messages.count_documents({"status": "yeni"}))
    return {"today": today_n, "unassigned": unassigned, "overdue": overdue, "quotes": quotes, "messages": msgs}


def daily_text(s: dict) -> str:
    return (f"ServisPlus günaydın ☀️\nBugün planlı iş: {s['today']}\nUsta atanmamış: {s['unassigned']}\n"
            f"Gecikmiş: {s['overdue']}\nBekleyen teklif: {s['quotes']}\nYeni mesaj: {s['messages']}")


async def send_daily_summary(db, tz, force=False):
    cfg = await get_settings(db)
    d = cfg["daily_summary"]
    if not force and not d.get("enabled"):
        return {"sent": 0}
    s = await daily_numbers(db, tz)
    sent = 0
    for ph in d.get("phones", []):
        r = await send(db, d.get("channel", "whatsapp"), ph, daily_text(s), kind="daily_summary", cfg=cfg)
        sent += 1 if r["status"] == "sent" else 0
    await db.app_settings.update_one({"_id": "global"}, {"$set": {"notify.daily_summary.last_sent": _now()}}, upsert=True)
    return {"sent": sent, "summary": s}


async def survey_sweep(db):
    """Servis bitip 2 saat geçtiyse ve puan verilmediyse müşteriye puanlama mesajı (ayar açıksa; her iş için bir deneme)."""
    cfg = await get_settings(db)
    c = cfg["customer"]
    if not c.get("enabled") or not c.get("events", {}).get("survey"):
        return 0
    now = datetime.now(timezone.utc)
    q = {"status": {"$in": ["tamamlandi", "faturalandi"]}, "survey": {"$exists": False},
         "completed_at": {"$gte": (now - timedelta(days=3)).isoformat(), "$lte": (now - timedelta(hours=2)).isoformat()}}
    jobs = await db.service_jobs.find(q, {"_id": 0, "workshop": 0}).limit(20).to_list(20)
    n = 0
    for j in jobs:
        if await db.outbox.find_one({"kind": "job_survey", "ref": j["id"]}):
            continue
        if not j.get("track_token"):
            j["track_token"] = secrets.token_urlsafe(12)
            await db.service_jobs.update_one({"id": j["id"]}, {"$set": {"track_token": j["track_token"]}})
        if await job_event(db, "survey", j):
            n += 1
    return n


async def reminder_sweep(db, tz=None):
    """Randevu saatine `minutes_before` dakika kala müşteriye ve ustaya hatırlatma (ayar açıksa; her iş/alıcı için bir kez)."""
    try:
        cfg = await get_settings(db)
        r = cfg["reminder"]
        if not r.get("enabled") or cfg.get("provider") == "none":
            return 0
        if tz is None:
            try:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo("Europe/Istanbul")
            except Exception:                           # noqa: BLE001
                tz = timezone(timedelta(hours=3))
        now_l = datetime.now(tz)
        lo, hi = now_l.strftime("%Y-%m-%dT%H:%M"), (now_l + timedelta(minutes=max(5, int(r.get("minutes_before") or 60)))).strftime("%Y-%m-%dT%H:%M")
        q = {"status": {"$nin": _DONE_ST}, "scheduled_at": {"$gte": lo, "$lte": hi}}
        jobs = await db.service_jobs.find(q, {"_id": 0, "workshop": 0}).limit(60).to_list(60)
        n = 0
        c = cfg["customer"]
        for j in jobs:
            when = (j.get("scheduled_at") or "")[:16].replace("T", " ")
            if not j.get("track_token"):
                j["track_token"] = secrets.token_urlsafe(12)
                await db.service_jobs.update_one({"id": j["id"]}, {"$set": {"track_token": j["track_token"]}})
            link = (c.get("base_url") or "https://bayi.servisplus.net.tr").rstrip("/") + "/takip/" + tenant.public_token(j["track_token"])
            if r.get("customer") and norm_msisdn(j.get("customer_phone") or "") and not await db.outbox.find_one({"kind": "job_reminder", "ref": j["id"], "status": "sent"}):
                txt = render(r.get("customer_template", ""), {"ad": (j.get("customer_name") or "").split(" ")[0], "zaman": when[11:], "usta": j.get("assigned_technician_name", "") or "ustamız", "link": link, "is_no": j.get("job_number", "")})
                res = await send(db, c.get("channel", "sms"), j["customer_phone"], txt, kind="job_reminder", ref=j["id"], cfg=cfg)
                n += 1 if res["status"] == "sent" else 0
            tid = j.get("assigned_technician_id")
            if r.get("technician") and tid:
                ref = j["id"] + ":" + tid
                u = await db.users.find_one({"id": tid}, {"_id": 0, "phone": 1, "name": 1})
                if u and norm_msisdn(u.get("phone") or "") and not await db.outbox.find_one({"kind": "tech_reminder", "ref": ref, "status": "sent"}):
                    t = cfg.get("technician") or {}
                    adres = " ".join(x for x in [j.get("customer_address"), j.get("customer_district"), j.get("customer_city")] if x)
                    txt = render(r.get("tech_template", ""), {"zaman": when[11:], "musteri": j.get("customer_name", ""), "adres": adres, "is_no": j.get("job_number", ""),
                                                              "link": (t.get("base_url") or "https://bayi.servisplus.net.tr").rstrip("/") + "/tech/jobs/" + j["id"]})
                    res = await send(db, t.get("channel") or c.get("channel", "sms"), u["phone"], txt, kind="tech_reminder", ref=ref, cfg=cfg)
                    n += 1 if res["status"] == "sent" else 0
        return n
    except Exception as e:                              # noqa: BLE001
        log.warning("reminder_sweep: %s", e)
        return 0


async def diagnose(db) -> dict:
    """Bildirim ayarlarının neden mesaj göndermediğini maddeler halinde söyler (şifre vb. gizli bilgi içermez)."""
    cfg = await get_settings(db)
    c, t, r, v = cfg["customer"], cfg.get("technician") or {}, cfg["reminder"], cfg["verimor"]
    items = []

    def add(ok, title, hint=""):
        items.append({"ok": ok, "title": title, "hint": hint})
    prov = cfg.get("provider")
    add(prov == "verimor", "Sağlayıcı: " + {"none": "seçili değil", "verimor": "Verimor"}.get(prov, str(prov)), "" if prov == "verimor" else "Sağlayıcıyı Verimor (SMS) seçip Kaydet'e basın.")
    if prov == "verimor":
        add(bool(v.get("username")) and bool(v.get("password")), "Verimor kullanıcı adı ve şifre kayıtlı", "Alanları doldurup Kaydet'e basın.")
        add(bool(v.get("source_addr")), "Gönderici başlığı girilmiş", "Boşsa Verimor hesabındaki ilk onaylı başlık kullanılır; başlığınız onaylı değilse mesaj reddedilebilir.")
    add(bool(c.get("enabled")), "“Müşteriye otomatik mesaj gönder” AÇIK", "3) bölümünde anahtarı açıp Kaydet'e basın. Kapalıysa müşteriye ve (ayrı ayarlanmadıysa) ustaya otomatik mesaj gitmez.")
    ev = c.get("events") or {}
    add(bool(ev.get("assigned")), "Müşteri: “usta atandı” olayı açık", "")
    tech_on = t.get("enabled") if t.get("enabled") is not None else c.get("enabled")
    add(bool(tech_on), "Ustaya iş atama mesajı AÇIK", "2) bölümündeki anahtarı açın (ya da müşteri mesajı açılınca birlikte açılır).")
    cch = c.get("channel") or "sms"
    add(cch == "sms", "Müşteri kanalı: " + cch.upper(), "Verimor yalnızca SMS gönderir; yine de seçili kanal WhatsApp ise artık SMS olarak gönderilir.")
    tch = t.get("channel") or cch
    add(tch == "sms", "Usta kanalı: " + tch.upper(), "")
    add(bool(r.get("enabled")), "Randevu hatırlatma açık", "İsterseniz 5) bölümünden açın (isteğe bağlı).")
    n_nophone = await db.users.count_documents({"role": "technician", "is_active": {"$ne": False}, "$or": [{"phone": ""}, {"phone": None}, {"phone": {"$exists": False}}]})
    add(n_nophone == 0, "Telefonu kayıtlı olmayan usta sayısı: %d" % n_nophone, "Ustanın telefonu yoksa ona mesaj gitmez. Teknisyenler sayfasında telefonları tamamlayın.")
    ob = await db.outbox.find({}, {"_id": 0, "to": 1, "kind": 1, "status": 1, "error": 1, "created_at": 1}).sort("created_at", -1).to_list(15)
    sent = sum(1 for o in ob if o.get("status") == "sent")
    fails = [o for o in ob if o.get("status") == "failed"][:6]
    return {"items": items, "recent_sent": sent, "recent_failed": fails, "all_ok": all(i["ok"] for i in items[:6])}
