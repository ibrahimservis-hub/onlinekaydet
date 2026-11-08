"""Saha (usta) tarafı: müşteri telefonu gizleme + izlenebilir arama/mesaj köprüsü, web push bildirimleri.

TELEFON GİZLEME — dürüst sınırlar
  Mod "mask": usta ekranında ve API yanıtında numara maskelenir (0544 *** ** 04). "Ara"ya basınca numara sunucudan
              istenir; her açış kaydedilir (denetim) ve usta başına günlük sınır uygulanır. Numara ekranda hiç
              gösterilmez/kopyalanamaz ama arama anında telefonun arama uygulamasına iletilir; yani kararlı biri
              bunu yakalayabilir. Caydırıcı + izlenebilir bir önlemdir, kesin koruma değildir.
  Mod "bridge": numara ustaya asla verilmez. Arama/mesaj, ayarlanan bir sağlayıcı webhook'u üzerinden köprülenir
              (Twilio/Netgsm "click-to-call", çağrı merkezi vb.). Kesin koruma budur; sağlayıcı hesabı gerekir.

WEB PUSH — RFC 8291 (aes128gcm) + VAPID, ek paket gerektirmez (cryptography + pyjwt). Gerçek tarayıcı push
  servisleriyle (FCM/Mozilla/Apple) uçtan uca doğrulama canlı ortamda yapılmalıdır.
"""
import asyncio
import base64
import hmac
import json
import logging
import os
import struct
import time
import uuid
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

import jwt
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from fastapi import Depends, HTTPException, Request

import notify

log = logging.getLogger("fieldops")
DEFAULT_PRIVACY = {"mode": "off", "daily_reveals": 6, "bridge_url": "", "bridge_headers": ""}


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64u(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def mask_phone(p: str) -> str:
    d = "".join(ch for ch in (p or "") if ch.isdigit())
    if len(d) < 7:
        return "••••"
    return f"{d[:4]} *** ** {d[-2:]}"


# ================================================================ WEB PUSH (RFC 8291 + VAPID)
def encrypt_push(payload: bytes, p256dh: str, auth: str, *, _eph=None, _salt=None) -> bytes:
    ua_pub = _unb64u(p256dh)
    auth_secret = _unb64u(auth)
    eph = _eph or ec.generate_private_key(ec.SECP256R1())
    as_pub = eph.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    ua_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_pub)
    shared = eph.exchange(ec.ECDH(), ua_key)
    salt = _salt or os.urandom(16)
    ikm = HKDF(hashes.SHA256(), 32, auth_secret, b"WebPush: info\x00" + ua_pub + as_pub).derive(shared)
    cek = HKDF(hashes.SHA256(), 16, salt, b"Content-Encoding: aes128gcm\x00").derive(ikm)
    nonce = HKDF(hashes.SHA256(), 12, salt, b"Content-Encoding: nonce\x00").derive(ikm)
    ct = AESGCM(cek).encrypt(nonce, payload + b"\x02", None)
    return salt + struct.pack(">I", 4096) + bytes([len(as_pub)]) + as_pub + ct


def decrypt_push(body: bytes, ua_private, auth: str) -> bytes:
    """Test/doğrulama için alıcı tarafı."""
    salt, rs, idlen = body[:16], struct.unpack(">I", body[16:20])[0], body[20]
    as_pub, ct = body[21:21 + idlen], body[21 + idlen:]
    ua_pub = ua_private.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    shared = ua_private.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), as_pub))
    ikm = HKDF(hashes.SHA256(), 32, _unb64u(auth), b"WebPush: info\x00" + ua_pub + as_pub).derive(shared)
    cek = HKDF(hashes.SHA256(), 16, salt, b"Content-Encoding: aes128gcm\x00").derive(ikm)
    nonce = HKDF(hashes.SHA256(), 12, salt, b"Content-Encoding: nonce\x00").derive(ikm)
    pt = AESGCM(cek).decrypt(nonce, ct, None)
    return pt.rstrip(b"\x00")[:-1] if pt.endswith(b"\x02") else pt


async def vapid_keys(db) -> dict:
    s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0, "vapid": 1}) or {}
    if s.get("vapid"):
        return s["vapid"]
    k = ec.generate_private_key(ec.SECP256R1())
    pem = k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    pub = _b64u(k.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))
    v = {"private_pem": pem, "public": pub}
    await db.app_settings.update_one({"_id": "global"}, {"$set": {"vapid": v}}, upsert=True)
    return v


def vapid_header(endpoint: str, v: dict, subject: str = "mailto:admin@servisplus.net.tr") -> str:
    u = urlparse(endpoint)
    tok = jwt.encode({"aud": f"{u.scheme}://{u.netloc}", "exp": int((datetime.now(timezone.utc) + timedelta(hours=12)).timestamp()), "sub": subject},
                     v["private_pem"], algorithm="ES256")
    return f"vapid t={tok}, k={v['public']}"


SENDER = None      # testlerde sahte gönderici atanabilir: async def (sub, body, headers) -> status


async def _post(endpoint, body, headers):
    if SENDER:
        return await SENDER(endpoint, body, headers)
    r = await asyncio.to_thread(lambda: requests.post(endpoint, data=body, headers=headers, timeout=15))
    return r.status_code


# ================================================================ FCM (yerel Android uygulaması)
# APK, Firebase token'ını /api/tech/fcm-token ile kaydeder. Gönderim için Google hizmet hesabı gerekir:
# FCM_SERVICE_ACCOUNT_JSON (JSON metni) veya FCM_SERVICE_ACCOUNT_FILE (dosya yolu) ortam değişkeni.
# Tanımlı değilse FCM gönderimi sessizce atlanır; web push etkilenmez.
_FCM_SA = None
_FCM_TOKEN = {"tok": "", "exp": 0.0}
_FCM_LAST = {"err": ""}


def _fcm_service_account():
    global _FCM_SA
    if _FCM_SA is None:
        raw = os.environ.get("FCM_SERVICE_ACCOUNT_JSON", "").strip()
        path = os.environ.get("FCM_SERVICE_ACCOUNT_FILE", "").strip()
        try:
            if not raw and path and os.path.isfile(path):
                with open(path, encoding="utf-8") as fh:
                    raw = fh.read()
            if raw:
                _FCM_SA = json.loads(raw)
        except Exception as e:  # noqa: BLE001
            log.warning("FCM hizmet hesabı okunamadı: %s", e)
            return None
    return _FCM_SA


def _fcm_access_token(sa: dict) -> str:
    now = time.time()
    if _FCM_TOKEN["tok"] and now < _FCM_TOKEN["exp"] - 60:
        return _FCM_TOKEN["tok"]
    assertion = jwt.encode({"iss": sa["client_email"], "sub": sa["client_email"],
                            "scope": "https://www.googleapis.com/auth/firebase.messaging",
                            "aud": "https://oauth2.googleapis.com/token", "iat": int(now), "exp": int(now) + 3000},
                           sa["private_key"], algorithm="RS256")
    r = requests.post("https://oauth2.googleapis.com/token",
                      data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion}, timeout=15)
    r.raise_for_status()
    j = r.json()
    _FCM_TOKEN.update(tok=j["access_token"], exp=now + int(j.get("expires_in", 3600)))
    return _FCM_TOKEN["tok"]


def _fcm_send_one(project_id: str, access: str, token: str, title: str, body: str, url: str) -> int:
    msg = {"message": {"token": token,
                       "notification": {"title": title[:120], "body": body[:240]},
                       "data": {"url": url or "/tech"},
                       "android": {"priority": "high", "ttl": "604800s", "notification": {"channel_id": "usta"}}}}
    r = requests.post(f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send",
                      headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json; charset=utf-8"},
                      data=json.dumps(msg, ensure_ascii=False).encode("utf-8"), timeout=15)
    if r.status_code >= 300:
        _FCM_LAST["err"] = f"{r.status_code} {r.text[:300]}"
        log.warning("FCM yanıt: %s %s", r.status_code, r.text[:300])
    return r.status_code


async def fcm_push_to(db, user_ids, title: str, body: str = "", url: str = "/tech") -> int:
    """Android uygulamasına kayıtlı cihazlara FCM gönderir. Asla istisna fırlatmaz."""
    try:
        sa = _fcm_service_account()
        if not sa or not user_ids:
            return 0
        toks = [d["token"] async for d in db.fcm_tokens.find({"user_ids": {"$in": list(user_ids)}}, {"_id": 0, "token": 1})]
        if not toks:
            return 0
        access = await asyncio.to_thread(_fcm_access_token, sa)
        n = 0
        for t in toks:
            st = await asyncio.to_thread(_fcm_send_one, sa["project_id"], access, t, title, body, url)
            if st == 404:                               # UNREGISTERED: uygulama kaldırılmış
                await db.fcm_tokens.delete_one({"token": t})
            elif st < 300:
                n += 1
            else:
                log.warning("FCM gönderim hatası: %s", st)
        return n
    except Exception as e:                              # noqa: BLE001
        log.warning("fcm_push_to: %s", e)
        return 0


async def push_to(db, user_ids, title: str, body: str = "", url: str = "/tech"):
    """Kullanıcıların kayıtlı cihazlarına bildirim gönderir (web push + Android FCM). Asla istisna fırlatmaz."""
    try:
        if not user_ids:
            return 0
        try:                                            # bildirim geçmişi (uygulamada "Bildirimler" ekranı)
            now = notify._now()
            await db.push_log.insert_many([{"id": str(uuid.uuid4()), "user_id": u, "title": title, "body": body, "url": url, "at": now} for u in set(user_ids)])
        except Exception as e:                          # noqa: BLE001
            log.warning("push_log: %s", e)
        v = await vapid_keys(db)
        payload = json.dumps({"title": title, "body": body, "url": url}, ensure_ascii=False).encode()
        n = 0
        async for sub in db.push_subs.find({"user_id": {"$in": list(user_ids)}}):
            try:
                data = encrypt_push(payload, sub["p256dh"], sub["auth"])
                hd = {"Content-Encoding": "aes128gcm", "Content-Type": "application/octet-stream", "TTL": "86400", "Urgency": "high",
                      "Authorization": vapid_header(sub["endpoint"], v)}
                st = await _post(sub["endpoint"], data, hd)
                if st in (404, 410):
                    await db.push_subs.delete_one({"id": sub["id"]})
                elif st < 300:
                    n += 1
            except Exception as e:                      # noqa: BLE001
                log.warning("push hatası: %s", e)
        _FCM_LAST["err"] = ""
        n += await fcm_push_to(db, user_ids, title, body, url)
        try:                                            # yöneticinin "bildirim ulaştı mı?" kontrolü için son sonuç
            for u in set(user_ids):
                await db.push_result.update_one({"user_id": u}, {"$set": {
                    "user_id": u, "at": notify._now(), "title": title, "sent": n,
                    "fcm_tokens": await db.fcm_tokens.count_documents({"user_ids": u}),
                    "web_subs": await db.push_subs.count_documents({"user_id": u}),
                    "fcm_configured": bool(_fcm_service_account()), "fcm_error": _FCM_LAST.get("err", "")}}, upsert=True)
        except Exception as e:                          # noqa: BLE001
            log.warning("push_result: %s", e)
        return n
    except Exception as e:                              # noqa: BLE001
        log.warning("push_to: %s", e)
        return 0


async def get_privacy_settings(db) -> dict:
    import speed
    s = (await speed.cached_global(db)).get("privacy") or {}
    return {**DEFAULT_PRIVACY, **s}


def mask_job(job: dict) -> dict:
    """Usta yanıtlarında müşteri telefonunu maskeler."""
    if job and job.get("customer_phone"):
        job = dict(job)
        job["customer_phone"] = mask_phone(job["customer_phone"])
        job["phone_masked"] = True
    return job


# ================================================================ ENDPOINT'LER
# ================================================================ ARAMA SÜRESİ (SLA)
SLA_OPEN = ("atandi", "yolda")


async def sla_fields(db):
    """Yeni atamada damgalanacak alanlar: atanma zamanı + aranması gereken son an (varsayılan 15 dk)."""
    cfg = (await db.app_settings.find_one({"_id": "call_sla"}, {"_id": 0})) or {}
    if cfg.get("enabled") is False:
        return {}
    mins = max(1, min(240, int(cfg.get("minutes") or 15)))
    now = datetime.now(timezone.utc)
    return {"assigned_at": now.isoformat(), "call_due_at": (now + timedelta(minutes=mins)).isoformat(),
            "first_call_at": "", "call_by": "", "call_alerted": False}


_BF_LAST = [0.0]


async def backfill(db):
    """Atanmış ama sayaç damgası olmayan (eski/başka yoldan atanan) açık işlere sayaç başlatır.
    Her iş listesi isteğinde değil, en fazla 60 sn'de bir çalışır (uzak veritabanında her çağrı bir gidiş-dönüş)."""
    import time as _t
    if _t.monotonic() - _BF_LAST[0] < 60:
        return 0
    _BF_LAST[0] = _t.monotonic()
    try:
        f = await sla_fields(db)
        if not f:
            return 0
        r = await db.service_jobs.update_many(
            {"status": {"$in": list(SLA_OPEN)}, "assigned_technician_id": {"$nin": ["", None]},
             "$or": [{"call_due_at": {"$exists": False}}, {"call_due_at": ""}, {"call_due_at": None}]}, {"$set": f})
        return r.modified_count
    except Exception as e:                              # noqa: BLE001
        log.warning("sla backfill: %s", e)
        return 0


# ================================================================ HİZMET PUANI (5 üzerinden)
SCORE_DAYS = 180
SCORE_MIN_JOBS = 3
SCORE_W = {"call": 0.20, "go": 0.25, "finish": 0.20, "review": 0.35}
SCORE_LABEL = {"call": "Müşteriyi arama hızı", "go": "İşe gitme hızı", "finish": "İşi bitirme hızı", "review": "Müşteri yorumları"}


def _dt(v, naive_tz_hours=3):
    """ISO metni -> aware datetime (saat dilimi yoksa Türkiye saati varsayılır). Okunamazsa None."""
    v = str(v or "").strip()
    if not v:
        return None
    try:
        d = datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        try:
            d = datetime.fromisoformat(v[:10] + "T09:00:00")
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone(timedelta(hours=naive_tz_hours)))
    return d


def _step(val, bounds):
    """val <= bounds[i] ise 5-i puan; hepsini aşarsa 1."""
    for i, b in enumerate(bounds):
        if val <= b:
            return 5 - i
    return 1


def score_job(j):
    """Tek iş için bileşen puanları (olmayan veri -> anahtar yok)."""
    out = {}
    asg = _dt(j.get("assigned_at"))
    if asg:
        lim = 15
        due = _dt(j.get("call_due_at"))
        if due and due > asg:
            lim = max(1, round((due - asg).total_seconds() / 60))
        fc = _dt(j.get("first_call_at"))
        if fc:
            m = max(0, (fc - asg).total_seconds() / 60)
            out["call"] = _step(m, [lim, lim * 2, lim * 4, lim * 8])
        else:
            out["call"] = 1
        arr = _dt(j.get("on_the_way_at")) or _dt(j.get("started_at"))
        if arr:
            ref = asg
            sch = _dt(j.get("scheduled_at"))
            if sch and sch > asg:
                ref = sch
            m = (arr - ref).total_seconds() / 60
            out["go"] = 5 if m <= 0 else _step(m, [60, 120, 240, 480])
    st, en = _dt(j.get("started_at")), _dt(j.get("completed_at"))
    if st and en and en >= st and not j.get("workshop"):
        h = (en - st).total_seconds() / 3600
        out["finish"] = _step(h, [2, 4, 8, 24])
    r = (j.get("survey") or {}).get("rating")
    if isinstance(r, (int, float)) and 1 <= r <= 5:
        out["review"] = int(r)
    return out


def score_from_jobs(jobs):
    acc = {k: [] for k in SCORE_W}
    for j in jobs:
        for k, v in score_job(j).items():
            acc[k].append(v)
    parts, tw, tv = {}, 0.0, 0.0
    for k, w in SCORE_W.items():
        n = len(acc[k])
        avg = round(sum(acc[k]) / n, 2) if n else None
        parts[k] = {"label": SCORE_LABEL[k], "avg": round(avg, 1) if avg is not None else None, "n": n, "weight": int(w * 100)}
        if n:
            tw += w
            tv += w * avg
    return {"score": round(tv / tw, 1) if tw else 0, "has": bool(tw) and len(jobs) >= SCORE_MIN_JOBS, "jobs": len(jobs), "min_jobs": SCORE_MIN_JOBS, "parts": parts, "days": SCORE_DAYS}


_SCORE_PROJ = {"_id": 0, "assigned_at": 1, "call_due_at": 1, "first_call_at": 1, "on_the_way_at": 1, "started_at": 1, "completed_at": 1,
               "scheduled_at": 1, "workshop": 1, "survey": 1, "assigned_technician_id": 1}


async def tech_score(db, tid, days=SCORE_DAYS):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    jobs = await db.service_jobs.find({"assigned_technician_id": tid, "status": {"$in": ["tamamlandi", "faturalandi"]}, "completed_at": {"$gte": cutoff}},
                                      _SCORE_PROJ).to_list(5000)
    return score_from_jobs(jobs)


async def mark_called(db, job_id, user, via="tel"):
    """Aramanın başlatıldığını işe yazar (ilk kez ise first_call_at). Dönen: kayıt zamanı."""
    now = datetime.now(timezone.utc).isoformat()
    ent = {"at": now, "by": user.get("name", ""), "via": via}
    await db.service_jobs.update_one({"id": job_id, "first_call_at": ""}, {"$set": {"first_call_at": now, "call_by": user.get("name", "")}})
    await db.service_jobs.update_one({"id": job_id}, {"$push": {"calls": {"$each": [ent], "$slice": -20}}})
    return now


async def call_hook(db):
    """5 dk'lık zamanlayıcı: süresi dolup aranmamış işler için yöneticiye bir kez uyarı."""
    await backfill(db)
    now = datetime.now(timezone.utc).isoformat()
    rows = await db.service_jobs.find({"call_due_at": {"$lt": now, "$ne": ""}, "first_call_at": "", "call_alerted": {"$ne": True},
                                       "status": {"$in": list(SLA_OPEN)}}, {"_id": 0, "id": 1, "job_number": 1, "customer_name": 1, "assigned_technician_name": 1}).limit(30).to_list(30)
    for j in rows:
        await db.service_jobs.update_one({"id": j["id"]}, {"$set": {"call_alerted": True}})
        try:
            await notify.notify_owner(db, f'⚠ {j.get("assigned_technician_name") or "Usta"} müşteriyi süresi içinde aramadı: {j.get("job_number", "")} · {j.get("customer_name", "")}', "call_sla")
        except Exception as e:                          # noqa: BLE001
            log.warning("arama uyarısı: %s", e)
    return len(rows)


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]

    @api_router.get("/tech/score")
    async def my_score(user: dict = Depends(get_current_user)):
        if user.get("role") != "technician":
            raise HTTPException(403, "Yalnızca teknisyen")
        return await tech_score(db, user["id"])

    @api_router.get("/admin/tech-scores")
    async def all_scores(days: int = SCORE_DAYS, user: dict = Depends(require_admin)):
        days = max(30, min(730, int(days)))
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        techs = await db.users.find({"role": "technician"}, {"_id": 0, "id": 1, "name": 1, "is_active": 1}).to_list(2000)
        jobs = await db.service_jobs.find({"assigned_technician_id": {"$nin": ["", None]}, "status": {"$in": ["tamamlandi", "faturalandi"]}, "completed_at": {"$gte": cutoff}},
                                          _SCORE_PROJ).to_list(100000)
        by = {}
        for j in jobs:
            by.setdefault(j["assigned_technician_id"], []).append(j)
        rows = []
        for t in techs:
            sc = score_from_jobs(by.get(t["id"], []))
            rows.append({"id": t["id"], "name": t.get("name", ""), "active": t.get("is_active", True) is not False, **sc})
        rows.sort(key=lambda r: (not r["has"], -r["score"]))
        return {"days": days, "rows": rows}

    async def privacy():
        return await get_privacy_settings(db)

    @api_router.get("/fieldops/privacy")
    async def get_privacy(user: dict = Depends(get_current_user)):
        p = await privacy()
        if user.get("role") != "admin":
            return {"mode": p["mode"]}
        return p

    @api_router.put("/fieldops/privacy")
    async def put_privacy(payload: dict, _: dict = Depends(require_admin)):
        cur = await privacy()
        for k in DEFAULT_PRIVACY:
            if k in payload:
                cur[k] = payload[k]
        if cur["mode"] not in ("off", "mask", "bridge"):
            raise HTTPException(status_code=400, detail="Geçersiz mod")
        cur["daily_reveals"] = max(1, int(cur["daily_reveals"]))
        await db.app_settings.update_one({"_id": "global"}, {"$set": {"privacy": cur}}, upsert=True)
        return cur

    async def tech_job(job_id, user):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job or job.get("assigned_technician_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Bu iş size atanmamış")
        if job.get("status") in ("tamamlandi", "faturalandi", "iptal"):
            raise HTTPException(status_code=403, detail="Kapanmış işte müşteri iletişimi kapalı")
        return job

    async def count_today(user_id):
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        return await db.phone_reveals.count_documents({"user_id": user_id, "at": {"$gte": since}})

    async def log_reveal(user, job, how):
        await db.phone_reveals.insert_one({"id": str(uuid.uuid4()), "user_id": user["id"], "user_name": user.get("name", ""), "job_id": job["id"],
                                           "job_number": job.get("job_number", ""), "how": how, "at": notify._now()})

    @api_router.post("/jobs/{job_id}/reveal-phone")
    async def reveal_phone(job_id: str, user: dict = Depends(get_current_user)):
        p = await privacy()
        if user.get("role") == "admin" or p["mode"] == "off":
            job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0, "customer_phone": 1})
            return {"phone": (job or {}).get("customer_phone", "")}
        if p["mode"] == "bridge":
            raise HTTPException(status_code=403, detail="Bu hesapta numara gösterilmez. “Ara” veya “Mesaj” düğmesini kullanın.")
        job = await tech_job(job_id, user)
        if await count_today(user["id"]) >= int(p["daily_reveals"]):
            raise HTTPException(status_code=429, detail="Günlük numara görüntüleme sınırına ulaştınız. Yöneticiyle iletişime geçin.")
        await log_reveal(user, job, "reveal")
        return {"phone": job.get("customer_phone", "")}

    @api_router.post("/jobs/{job_id}/call-log")
    async def call_log(job_id: str, payload: dict = None, user: dict = Depends(get_current_user)):
        """Usta 'Ara'ya bastığında çağrılır → ilk arama zamanı işe yazılır (yalnızca arama başlatma; görüşme süresi bilinmez)."""
        if user.get("role") == "technician":
            job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0, "assigned_technician_id": 1})
            if not job or job.get("assigned_technician_id") != user["id"]:
                raise HTTPException(status_code=403, detail="Bu iş size atanmamış")
        elif user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Yetkisiz erişim")
        at = await mark_called(db, job_id, user, str((payload or {}).get("via") or "tel")[:12])
        return {"ok": True, "first_call_at": at}

    @api_router.get("/fieldops/call-sla")
    async def get_call_sla(_: dict = Depends(get_current_user)):
        cfg = (await db.app_settings.find_one({"_id": "call_sla"}, {"_id": 0})) or {}
        return {"enabled": cfg.get("enabled") is not False, "minutes": int(cfg.get("minutes") or 15)}

    @api_router.put("/fieldops/call-sla")
    async def put_call_sla(payload: dict, _: dict = Depends(require_admin)):
        cfg = {"enabled": bool(payload.get("enabled", True)), "minutes": max(1, min(240, int(payload.get("minutes") or 15)))}
        await db.app_settings.update_one({"_id": "call_sla"}, {"$set": cfg}, upsert=True)
        return cfg

    @api_router.post("/jobs/{job_id}/call")
    async def call_customer(job_id: str, user: dict = Depends(get_current_user)):
        p = await privacy()
        job = await tech_job(job_id, user) if user.get("role") != "admin" else await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if p["mode"] == "bridge" and user.get("role") != "admin":
            if not p["bridge_url"]:
                raise HTTPException(status_code=400, detail="Arama köprüsü yapılandırılmamış")
            tech = await db.users.find_one({"id": user["id"]}, {"_id": 0, "phone": 1})
            body = {"job_id": job_id, "technician_phone": (tech or {}).get("phone", ""), "customer_phone": job.get("customer_phone", "")}
            try:
                hd = {"Content-Type": "application/json", **notify._headers(p.get("bridge_headers", ""))}
                r = await asyncio.to_thread(lambda: requests.post(p["bridge_url"], json=body, headers=hd, timeout=20))
                if r.status_code >= 300:
                    raise RuntimeError(f"HTTP {r.status_code}")
            except Exception as e:                      # noqa: BLE001
                raise HTTPException(status_code=502, detail="Arama başlatılamadı: " + str(e)[:100])
            await log_reveal(user, job, "bridge_call")
            await mark_called(db, job_id, user, "bridge")
            return {"mode": "bridge", "message": "Telefonunuz birazdan çalacak; açınca müşteri aranır."}
        if p["mode"] == "mask" and user.get("role") != "admin":
            if await count_today(user["id"]) >= int(p["daily_reveals"]):
                raise HTTPException(status_code=429, detail="Günlük arama sınırına ulaştınız.")
            await log_reveal(user, job, "call")
        if user.get("role") == "technician":
            await mark_called(db, job_id, user, "call")
        return {"mode": p["mode"], "tel": job.get("customer_phone", "")}

    @api_router.post("/jobs/{job_id}/message")
    async def message_customer(job_id: str, payload: dict, user: dict = Depends(get_current_user)):
        """Numarayı göstermeden müşteriye mesaj (sağlayıcı üzerinden)."""
        job = await tech_job(job_id, user) if user.get("role") != "admin" else await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        text = (payload.get("text") or "").strip()[:500]
        if not text:
            raise HTTPException(status_code=400, detail="Mesaj boş")
        cfg = await notify.get_settings(db)
        if cfg["provider"] == "none":
            raise HTTPException(status_code=400, detail="SMS/WhatsApp sağlayıcısı tanımlı değil")
        r = await notify.send(db, cfg["customer"].get("channel", "sms"), job.get("customer_phone", ""), text, kind="tech_message", ref=job_id, cfg=cfg)
        if r["status"] != "sent":
            raise HTTPException(status_code=502, detail="Mesaj gönderilemedi")
        await log_reveal(user, job, "message")
        return {"ok": True}

    @api_router.get("/fieldops/phone-reveals")
    async def reveals(_: dict = Depends(require_admin)):
        return await db.phone_reveals.find({}, {"_id": 0}).sort("at", -1).to_list(300)

    # ---------------------------------------------------- web push
    @api_router.get("/push/public-key")
    async def push_key(_: dict = Depends(get_current_user)):
        return {"key": (await vapid_keys(db))["public"]}

    @api_router.post("/push/subscribe")
    async def push_sub(payload: dict, request: Request, user: dict = Depends(get_current_user)):
        ep, keys = payload.get("endpoint"), payload.get("keys") or {}
        if not ep or not keys.get("p256dh") or not keys.get("auth"):
            raise HTTPException(status_code=400, detail="Geçersiz abonelik")
        await db.push_subs.update_one({"endpoint": ep}, {"$set": {"endpoint": ep, "p256dh": keys["p256dh"], "auth": keys["auth"], "user_id": user["id"],
                                                                   "ua": request.headers.get("user-agent", "")[:200], "at": notify._now()},
                                                         "$setOnInsert": {"id": str(uuid.uuid4())}}, upsert=True)
        return {"ok": True}

    @api_router.post("/push/unsubscribe")
    async def push_unsub(payload: dict, user: dict = Depends(get_current_user)):
        await db.push_subs.delete_many({"endpoint": payload.get("endpoint"), "user_id": user["id"]})
        return {"ok": True}

    @api_router.post("/push/test")
    async def push_test(user: dict = Depends(get_current_user)):
        _FCM_LAST["err"] = ""
        n = await push_to(db, [user["id"]], "ServisPlus", "Test bildirimi çalışıyor ✔", "/tech" if user.get("role") == "technician" else "/admin")
        ntok = await db.fcm_tokens.count_documents({"user_ids": user["id"]})
        nweb = await db.push_subs.count_documents({"user_id": user["id"]})
        return {"sent": n, "fcm_configured": bool(_fcm_service_account()), "fcm_tokens": ntok, "web_subs": nweb, "fcm_error": _FCM_LAST["err"]}

    @api_router.get("/push/result/{uid}")
    async def push_result(uid: str, _: dict = Depends(require_admin)):
        r = await db.push_result.find_one({"user_id": uid}, {"_id": 0})
        if not r:
            r = {"user_id": uid, "none": True, "fcm_tokens": await db.fcm_tokens.count_documents({"user_ids": uid}),
                 "fcm_configured": bool(_fcm_service_account())}
        return r

    @api_router.get("/push/status")
    async def push_status(user: dict = Depends(get_current_user)):
        ntok = await db.fcm_tokens.count_documents({"user_ids": user["id"]})
        return {"fcm_configured": bool(_fcm_service_account()), "fcm_tokens": ntok, "fcm_error": _FCM_LAST.get("err", "")}

    @api_router.post("/public/site-request-notify")
    async def site_request_notify(payload: dict, request: Request):
        """Site servis talebi formundan (talep.php) gelen çağrı: yöneticilere push. Gizli anahtar zorunlu."""
        secret = os.environ.get("SITE_NOTIFY_SECRET", "")
        if not secret or not hmac.compare_digest(request.headers.get("X-SP-Secret", ""), secret):
            raise HTTPException(status_code=403, detail="Yetkisiz")
        ref = str(payload.get("ref", ""))[:40]
        name = str(payload.get("name", ""))[:80]
        svc = " ".join(x for x in [str(payload.get("service", ""))[:60], str(payload.get("brand", ""))[:40]] if x)
        where = " ".join(x for x in [str(payload.get("district", ""))[:60], str(payload.get("city", ""))[:60]] if x)
        await notify.push_admins_t(db, "Yeni site servis talebi", f"{name} · {svc} · {where} ({ref})".strip(" ·"), "/admin")
        return {"ok": True}

    @api_router.get("/me/notifications")
    async def my_notifications(user: dict = Depends(get_current_user)):
        return await db.push_log.find({"user_id": user["id"]}, {"_id": 0}).sort("at", -1).to_list(100)

    @api_router.delete("/me/notifications")
    async def clear_my_notifications(user: dict = Depends(get_current_user)):
        r = await db.push_log.delete_many({"user_id": user["id"]})
        return {"ok": True, "deleted": r.deleted_count}

    @api_router.delete("/me/notifications/{nid}")
    async def delete_my_notification(nid: str, user: dict = Depends(get_current_user)):
        await db.push_log.delete_one({"id": nid, "user_id": user["id"]})
        return {"ok": True}

    @api_router.put("/auth/me/avatar")
    async def set_my_avatar(payload: dict, user: dict = Depends(get_current_user)):
        url = str(payload.get("url") or "").strip()
        if url and not url.startswith("/api/files/"):
            raise HTTPException(status_code=400, detail="Geçersiz fotoğraf")
        await db.users.update_one({"id": user["id"]}, {"$set": {"avatar": url}})
        return {"ok": True, "avatar": url}

    @api_router.post("/tech/fcm-token")
    async def fcm_token(payload: dict, user: dict = Depends(get_current_user)):
        tok = str(payload.get("token") or "").strip()
        if not tok or len(tok) > 400:
            raise HTTPException(status_code=400, detail="Geçersiz token")
        # Aynı telefonda birden fazla hesap (ör. hem usta hem yönetici) olabilir: token'a kullanıcıları ekleriz
        await db.fcm_tokens.update_one({"token": tok},
                                       {"$set": {"token": tok, "at": notify._now()}, "$addToSet": {"user_ids": user["id"]}}, upsert=True)
        return {"ok": True}


async def ensure_indexes(db):
    await db.push_subs.create_index("endpoint", unique=True)
    await db.push_subs.create_index("user_id")
    await db.fcm_tokens.create_index("token", unique=True)
    await db.fcm_tokens.create_index("user_ids")
    await db.push_log.create_index([("user_id", 1), ("at", -1)])
    await db.phone_reveals.create_index([("user_id", 1), ("at", -1)])
