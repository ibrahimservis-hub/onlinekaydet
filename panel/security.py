"""Giriş güvenliği: cihaz/IP kaydı, güvenlik uyarıları, kilitleme, cihaz onayı."""
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:
    TR = timezone(timedelta(hours=3))

DEFAULT_SECURITY = {
    "enabled": True,
    "require_phone_new_device": True,   # teknisyen yeni cihazdan girerken kayıtlı telefonu doğrulat
    "block_new_device": False,          # True: yeni cihaz yönetici onaylayana kadar giremez
    "max_failures": 5,                  # 15 dk içinde hatalı deneme sınırı
    "lock_minutes": 15,
    "alert_new_ip": True,
    "alert_night_login": True,
}


def _id():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc).isoformat()


def client_ip(request: Request) -> str:
    xf = request.headers.get("x-forwarded-for", "")
    if xf:
        return xf.split(",")[0].strip()
    return request.client.host if request.client else ""


def ip_prefix(ip: str) -> str:
    if ":" in ip:                       # ipv6 -> ilk 4 blok
        return ":".join(ip.split(":")[:4])
    return ".".join(ip.split(".")[:3])


def mask_ip(ip: str) -> str:
    return ip  # panelde tam IP gösterilir (yalnızca yönetici görür)


def norm_phone(p: str) -> str:
    d = re.sub(r"\D", "", p or "")
    return d[-10:]


def device_label(ua: str) -> str:
    ua = ua or ""
    os_ = "Android" if "Android" in ua else "iPhone" if "iPhone" in ua else "iPad" if "iPad" in ua else \
        "Windows" if "Windows" in ua else "Mac" if "Mac OS" in ua else "Linux" if "Linux" in ua else "Cihaz"
    br = "Edge" if "Edg/" in ua else "Chrome" if "Chrome" in ua else "Safari" if "Safari" in ua else \
        "Firefox" if "Firefox" in ua else "Tarayıcı"
    return f"{os_} • {br}"


async def get_security(db) -> dict:
    s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
    out = dict(DEFAULT_SECURITY)
    out.update(s.get("security") or {})
    return out


async def _alert(db, user, kind, severity, text, ip, device_id, extra=None):
    doc = {"id": _id(), "user_id": user.get("id", ""), "user_name": user.get("name", user.get("email", "")),
           "role": user.get("role", ""), "type": kind, "severity": severity, "text": text, "ip": ip,
           "device_id": device_id, "status": "open", "created_at": _now(), **(extra or {})}
    await db.security_alerts.insert_one(dict(doc))
    try:
        import asyncio, notify
        asyncio.create_task(notify.dispatch_alert(db, doc))
    except Exception:
        pass
    return doc["id"]


async def check_login(db, request: Request, email: str, user: Optional[dict], password_ok: bool,
                      device_id: str = "", phone: str = "", portal: str = ""):
    """Giriş denemesini değerlendirir. İzin yoksa HTTPException atar. Başarılıysa None döner."""
    cfg = await get_security(db)
    ip = client_ip(request)
    ua = request.headers.get("user-agent", "")[:300]
    device_id = (device_id or "")[:80]
    now = datetime.now(timezone.utc)

    async def log(success, reason):
        await db.login_events.insert_one({
            "id": _id(), "user_id": (user or {}).get("id", ""), "email": email,
            "name": (user or {}).get("name", ""), "role": (user or {}).get("role", ""),
            "ip": ip, "ua": ua, "device_id": device_id, "device_label": device_label(ua),
            "success": success, "reason": reason, "at": _now(),
            "user_exists": bool(user), "portal": (portal or "")[:20]})

    if not cfg["enabled"]:
        if password_ok:
            await log(True, "")
        return

    # --- kilit (brute force)
    since = (now - timedelta(minutes=cfg["lock_minutes"])).isoformat()
    fails_email = await db.login_events.count_documents({"email": email, "success": False, "at": {"$gte": since}, "reason": "bad_password"})
    fails_ip = await db.login_events.count_documents({"ip": ip, "success": False, "at": {"$gte": since}, "reason": "bad_password"})
    if fails_email >= cfg["max_failures"] or fails_ip >= cfg["max_failures"] * 3:
        await log(False, "locked")
        if fails_email == cfg["max_failures"]:
            await _alert(db, user or {"email": email, "name": email}, "brute_force", "high",
                         f"{email} için {fails_email} hatalı giriş — hesap {cfg['lock_minutes']} dk kilitlendi", ip, device_id)
        raise HTTPException(status_code=429, detail=f"Çok fazla hatalı deneme. {cfg['lock_minutes']} dakika sonra tekrar deneyin.")

    if not user or not password_ok:
        await log(False, "bad_password")
        return

    # --- cihaz / IP kontrolü
    dev = None
    if device_id:
        dev = await db.trusted_devices.find_one({"user_id": user["id"], "device_id": device_id}, {"_id": 0})
    if dev and dev.get("status") == "blocked":
        await log(False, "blocked_device")
        await _alert(db, user, "blocked_device", "high", "Engellenmiş cihazdan giriş denemesi", ip, device_id)
        raise HTTPException(status_code=403, detail="Bu cihaz yönetici tarafından engellendi")
    has_devices = await db.trusted_devices.count_documents({"user_id": user["id"], "status": "trusted"}) > 0
    is_new_device = not (dev and dev.get("status") == "trusted")

    if is_new_device and has_devices:
        # telefon doğrulaması
        if user.get("role") == "technician" and cfg["require_phone_new_device"] and norm_phone(user.get("phone", "")):
            if not phone:
                await log(False, "need_phone")
                raise HTTPException(status_code=428, detail="Yeni cihaz algılandı. Kayıtlı telefon numaranızı girin.")
            if norm_phone(phone) != norm_phone(user.get("phone", "")):
                await log(False, "phone_mismatch")
                await _alert(db, user, "phone_mismatch", "high",
                             f"{user['name']}: yeni cihazda telefon doğrulaması başarısız", ip, device_id, {"entered_phone": phone[-4:]})
                raise HTTPException(status_code=403, detail="Telefon numarası eşleşmedi")
        if cfg["block_new_device"] and not (dev and dev.get("status") == "trusted"):
            if not dev:
                await db.trusted_devices.insert_one({
                    "id": _id(), "user_id": user["id"], "user_name": user["name"], "device_id": device_id,
                    "label": device_label(ua), "ua": ua, "ip_first": ip, "last_ip": ip, "status": "pending",
                    "first_seen": _now(), "last_seen": _now(), "logins": 0})
            await log(False, "pending_device")
            await _alert(db, user, "new_device", "high", f"{user['name']} yeni cihazdan girmeye çalıştı — onay bekliyor", ip, device_id)
            raise HTTPException(status_code=403, detail="Yeni cihaz algılandı. Yönetici onayı gerekiyor.")

    # --- başarılı giriş: kayıtlar
    known = await db.login_events.find({"user_id": user["id"], "success": True}, {"_id": 0, "ip": 1}).sort("at", -1).to_list(50)
    known_prefixes = {ip_prefix(k["ip"]) for k in known if k.get("ip")}
    new_ip = bool(known_prefixes) and ip_prefix(ip) not in known_prefixes
    await log(True, "")

    if device_id:
        if dev:
            await db.trusted_devices.update_one({"id": dev["id"]}, {"$set": {"last_seen": _now(), "last_ip": ip, "status": "trusted"}, "$inc": {"logins": 1}})
        else:
            await db.trusted_devices.insert_one({
                "id": _id(), "user_id": user["id"], "user_name": user["name"], "device_id": device_id,
                "label": device_label(ua), "ua": ua, "ip_first": ip, "last_ip": ip, "status": "trusted",
                "first_seen": _now(), "last_seen": _now(), "logins": 1})

    if has_devices or known_prefixes:
        if is_new_device and device_id and new_ip:
            await _alert(db, user, "new_location_device", "high",
                         f"{user['name']}: farklı konum (IP {ip}) ve yeni cihazdan ({device_label(ua)}) giriş", ip, device_id)
        elif is_new_device and device_id:
            await _alert(db, user, "new_device", "high" if user.get("role") == "admin" else "medium", f"{user['name']}: yeni cihazdan giriş ({device_label(ua)})", ip, device_id)
        elif new_ip and cfg["alert_new_ip"]:
            await _alert(db, user, "new_ip", "medium", f"{user['name']}: farklı IP/konumdan giriş (IP {ip})", ip, device_id)
    hour = datetime.now(TR).hour
    if cfg["alert_night_login"] and (hour >= 22 or hour < 7):
        await _alert(db, user, "night_login", "low", f"{user['name']}: gece saatinde giriş ({hour:02d}:00)", ip, device_id)


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    @api_router.get("/security/summary")
    async def sec_summary(_: dict = Depends(require_admin)):
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        return {
            "open_alerts": await db.security_alerts.count_documents({"status": "open"}),
            "high_open": await db.security_alerts.count_documents({"status": "open", "severity": "high"}),
            "pending_devices": await db.trusted_devices.count_documents({"status": "pending"}),
            "failed_24h": await db.login_events.count_documents({"success": False, "at": {"$gte": since}}),
            "logins_24h": await db.login_events.count_documents({"success": True, "at": {"$gte": since}}),
        }

    @api_router.get("/security/alerts")
    async def sec_alerts(status: Optional[str] = None, _: dict = Depends(require_admin)):
        q = {"status": status} if status else {}
        return await db.security_alerts.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)

    @api_router.post("/security/alerts/{aid}/resolve")
    async def sec_resolve(aid: str, user: dict = Depends(require_admin)):
        r = await db.security_alerts.update_one({"id": aid}, {"$set": {"status": "resolved", "resolved_by": user["name"], "resolved_at": _now()}})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Uyarı bulunamadı")
        return {"ok": True}

    @api_router.post("/security/alerts/resolve-all")
    async def sec_resolve_all(user: dict = Depends(require_admin)):
        r = await db.security_alerts.update_many({"status": "open"}, {"$set": {"status": "resolved", "resolved_by": user["name"], "resolved_at": _now()}})
        return {"ok": True, "count": r.modified_count}

    @api_router.delete("/security/alerts/{aid}")
    async def sec_alert_delete(aid: str, _: dict = Depends(require_admin)):
        await db.security_alerts.delete_one({"id": aid})
        return {"ok": True}

    @api_router.get("/security/logins")
    async def sec_logins(user_id: Optional[str] = None, success: Optional[bool] = None, role: Optional[str] = None,
                         q: Optional[str] = None, days: int = 0, limit: int = 300, _: dict = Depends(require_admin)):
        flt = {}
        if user_id:
            flt["user_id"] = user_id
        if success is not None:
            flt["success"] = success
        if role:
            flt["$or"] = [{"role": role}, {"portal": role}] if role != "unknown" else [{"user_exists": False}]
        if days and days > 0:
            flt["at"] = {"$gte": (datetime.now(timezone.utc) - timedelta(days=min(days, 365))).isoformat()}
        rows = await db.login_events.find(flt, {"_id": 0}).sort("at", -1).to_list(min(limit, 2000))
        if q:
            ql = q.lower().strip()
            rows = [r for r in rows if ql in (r.get("email", "") + " " + r.get("name", "") + " " + r.get("ip", "")).lower()]
        return rows

    @api_router.get("/security/failed-summary")
    async def sec_failed_summary(days: int = 7, _: dict = Depends(require_admin)):
        """Hatalı giriş özeti: en çok deneyen IP'ler, hedef hesaplar, rol/kapı dağılımı, günlük sayı."""
        since = (datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 90)))).isoformat()
        rows = await db.login_events.find({"success": False, "at": {"$gte": since}}, {"_id": 0}).to_list(20000)
        by_ip, by_acc, by_role, by_day = {}, {}, {}, {}
        for r in rows:
            ip = r.get("ip", "") or "?"
            a = by_ip.setdefault(ip, {"ip": ip, "count": 0, "accounts": set(), "last": ""})
            a["count"] += 1
            a["accounts"].add(r.get("email", ""))
            a["last"] = max(a["last"], r.get("at", ""))
            em = r.get("email", "") or "?"
            b = by_acc.setdefault(em, {"email": em, "name": r.get("name", ""), "role": r.get("role", ""), "exists": r.get("user_exists", bool(r.get("user_id"))), "count": 0, "ips": set(), "last": ""})
            b["count"] += 1
            b["ips"].add(ip)
            b["last"] = max(b["last"], r.get("at", ""))
            k = (r.get("role") or r.get("portal") or "bilinmiyor")
            by_role[k] = by_role.get(k, 0) + 1
            d = (r.get("at", "") or "")[:10]
            by_day[d] = by_day.get(d, 0) + 1
        top_ip = sorted(({"ip": v["ip"], "count": v["count"], "accounts": len(v["accounts"]), "last": v["last"]} for v in by_ip.values()), key=lambda x: -x["count"])[:15]
        top_acc = sorted(({"email": v["email"], "name": v["name"], "role": v["role"], "exists": v["exists"], "count": v["count"], "ips": len(v["ips"]), "last": v["last"]} for v in by_acc.values()), key=lambda x: -x["count"])[:15]
        return {"total": len(rows), "top_ips": top_ip, "top_accounts": top_acc, "by_role": by_role,
                "by_day": [{"day": k, "count": v} for k, v in sorted(by_day.items())]}

    @api_router.get("/security/devices")
    async def sec_devices(user_id: Optional[str] = None, status: Optional[str] = None, _: dict = Depends(require_admin)):
        q = {}
        if user_id:
            q["user_id"] = user_id
        if status:
            q["status"] = status
        return await db.trusted_devices.find(q, {"_id": 0}).sort("last_seen", -1).to_list(1000)

    @api_router.post("/security/devices/{did}/{action}")
    async def sec_device_action(did: str, action: str, _: dict = Depends(require_admin)):
        if action == "forget":
            await db.trusted_devices.delete_one({"id": did})
            return {"ok": True}
        st = {"trust": "trusted", "block": "blocked"}.get(action)
        if not st:
            raise HTTPException(status_code=400, detail="Geçersiz işlem")
        r = await db.trusted_devices.update_one({"id": did}, {"$set": {"status": st}})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Cihaz bulunamadı")
        return {"ok": True}

    @api_router.post("/security/users/{uid}/logout-all")
    async def sec_logout_all(uid: str, _: dict = Depends(require_admin)):
        """Kullanıcının tüm açık oturumlarını geçersiz kılar."""
        r = await db.users.update_one({"id": uid}, {"$set": {"tokens_valid_after": int(datetime.now(timezone.utc).timestamp())}})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        return {"ok": True}

    @api_router.get("/security/settings")
    async def sec_get_settings(_: dict = Depends(require_admin)):
        return await get_security(db)

    @api_router.put("/security/settings")
    async def sec_put_settings(payload: dict, _: dict = Depends(require_admin)):
        cur = await get_security(db)
        for k in DEFAULT_SECURITY:
            if k in payload:
                cur[k] = type(DEFAULT_SECURITY[k])(payload[k]) if not isinstance(DEFAULT_SECURITY[k], bool) else bool(payload[k])
        await db.app_settings.update_one({"_id": "global"}, {"$set": {"security": cur}}, upsert=True)
        return cur


async def ensure_indexes(db):
    await db.login_events.create_index([("at", -1)])
    await db.login_events.create_index("email")
    await db.trusted_devices.create_index("user_id")
    await db.security_alerts.create_index([("created_at", -1)])
