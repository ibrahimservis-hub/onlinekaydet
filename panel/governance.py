"""Yönetişim: yönetici rolleri, 2FA (TOTP), denetim kaydı, çöp kutusu, otomatik yedek, sağlık/hata izleme,
bildirim ayarları ve arka plan zamanlayıcı."""
import asyncio
import base64
import gzip
import hashlib
import hmac
import io
import json
import logging
import os
import re
import secrets
import shutil
import struct
import time
import traceback
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import requests
from bson import json_util
from fastapi import Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, Response

import notify

log = logging.getLogger("governance")
STARTED = time.time()
BACKUP_DIR = Path(os.environ.get("BACKUP_DIR") or (Path(__file__).parent / "backups"))
TRASH_DAYS = 30

# ============================================================== ROLLER
ROLES = {
    "owner": "Sahip",
    "manager": "Müdür",
    "accounting": "Muhasebe",
    "operations": "Operasyon",
    "site_editor": "Site editörü",
    "custom": "Özel yetki",
}
# alan -> "rw" | "r"
ROLE_AREAS = {
    "owner": {"ops": "rw", "finance": "rw", "reports": "rw", "site": "rw", "settings": "rw", "owner": "rw", "common": "rw"},
    "manager": {"ops": "rw", "finance": "rw", "reports": "rw", "site": "rw", "settings": "rw", "common": "rw"},
    "accounting": {"finance": "rw", "reports": "r", "ops": "r", "settings": "r", "common": "rw"},
    "operations": {"ops": "rw", "reports": "r", "settings": "r", "common": "rw"},
    "site_editor": {"site": "rw", "settings": "r", "common": "rw"},
    "custom": {},
}
ROLE_DESC = {
    "owner": "Her şey: finans, site, güvenlik, yedek, yönetici hesapları",
    "manager": "İş/usta/finans/site; güvenlik merkezi, yedek ve yönetici hesapları hariç",
    "accounting": "Yalnızca finans (kasa, muhasebe, kârlılık); iş ve müşteri verisini salt okur",
    "operations": "İş, müşteri, usta, stok, mesaj; finans ve site yok",
    "site_editor": "Yalnızca Site Stüdyosu ve medya",
    "custom": "Yöneticinin tek tek seçtiği bölümler",
}


def area_of(path: str, method: str) -> str:
    p = path[5:] if path.startswith("/api/") else path.lstrip("/")
    first = p.split("/")[0]
    if first in ("finance", "cash", "profit", "receivables"):
        return "finance"
    if first == "brief":
        return "reports"
    if first == "mkt":
        return "site" if p.startswith("mkt/pages/generate") or p.startswith("mkt/pages/plan") else "reports"
    if first == "reports":
        return "finance" if p.startswith("reports/profitability") else "reports"
    if first in ("studio", "media", "shop", "site", "customer-accounts"):
        return "site"
    if first == "admin":
        return "reports" if p.startswith("admin/gsc") else "site"
    if first in ("admin-users", "security"):
        return "owner"
    if first == "governance":
        return "common" if p in ("governance/roles",) else "owner"
    if first == "settings":
        return "settings"
    if first in ("auth", "notifications", "public", "health", "upload", "files", "proxy-image", "dashboard", "push"):
        return "common"
    return "ops"


def allowed(admin_role: str, path: str, method: str) -> bool:
    perm = ROLE_AREAS.get(admin_role or "owner", ROLE_AREAS["owner"]).get(area_of(path, method))
    if not perm:
        return False
    return perm == "rw" or method in ("GET", "HEAD", "OPTIONS")


# ============================================================== ÖZEL YETKİ (tek tek bölüm seçimi)
# (anahtar, etiket, grup)
PERM_MODULES = [
    ("dashboard", "Genel Bakış", "Genel"),
    ("jobs", "Servis Kayıtları", "Servis"), ("appointments", "Randevular", "Servis"), ("quotes", "Fiyat Teklifleri", "Servis"),
    ("warranty", "Garanti Talepleri", "Servis"), ("customers", "Müşteriler", "Servis"), ("technicians", "Teknisyenler", "Servis"),
    ("parts", "Yedek Parça", "Servis"),
    ("shop", "Mağaza · Siparişler · Yeni Sipariş · Pazaryerleri", "Mağaza & Satış"), ("coupons", "Kuponlar", "Mağaza & Satış"),
    ("site_features", "Site Özellikleri · Aç/Kapat & Entegrasyonlar", "Web Sitesi"), ("seo", "SEO · 301 · 404", "Web Sitesi"),
    ("studio", "Site Stüdyosu · Medya", "Web Sitesi"), ("integration", "Site Entegrasyonu", "Web Sitesi"),
    ("messages", "İletişim Mesajları", "Pazarlama & İletişim"), ("reviews", "Yorumlar", "Pazarlama & İletişim"),
    ("dealers", "Bayilik Başvuruları", "Pazarlama & İletişim"), ("marketing", "Pazarlama Merkezi", "Pazarlama & İletişim"),
    ("growth", "Büyüme Merkezi", "Pazarlama & İletişim"), ("visitors", "Ziyaretçiler", "Pazarlama & İletişim"),
    ("team", "Ekip Merkezi", "Ekip"), ("performance", "Performans", "Ekip"), ("announcements", "Duyurular", "Ekip"),
    ("diagnosis", "Arıza Rehberi", "Ekip"), ("brands", "Markalar", "Ekip"),
    ("accounting", "Muhasebe (kasa, usta bakiyeleri, alacaklar)", "Finans"), ("reports", "Raporlar · Kâr", "Finans"),
    ("settings", "Ayarlar", "Yönetim"),
]
PERM_KEYS = {m[0] for m in PERM_MODULES}
# yol öneki (1 veya 2 parça) -> bölüm
PREFIX_PERM = {
    "dashboard": "dashboard", "brief": "dashboard",
    "jobs": "jobs", "autoassign": "jobs", "fieldops": "jobs", "devices": "jobs", "qr": "jobs", "ai": "jobs",
    "appointments": "appointments", "quotes": "quotes", "warranty-claims": "warranty", "customers": "customers",
    "technicians": "technicians", "parts": "parts",
    "shop": "shop", "customer-accounts": "shop", "admin/market": "shop", "admin/payments": "shop",
    "growth/coupons": "coupons", "growth/coupons-report": "coupons",
    "site": "site_features", "admin/gsc": "marketing", "admin/brand-sources": "shop", "admin/brand-hub": "shop", "admin/shop-products": "shop", "admin/brand-products": "shop", "admin/modules": "site_features", "admin/merchant-api": "site_features",
    "admin/404": "seo", "admin/redirects": "seo", "admin/redirects-htaccess": "seo", "admin/seo": "seo", "admin/keywords": "seo",
    "studio": "studio", "media": "studio", "analytics/overview": "visitors", "analytics": "visitors",
    "messages": "messages", "export": "messages", "reviews": "reviews", "dealers": "dealers", "mkt": "marketing", "growth": "growth",
    "chat": "team", "checklists": "team", "training": "team", "partners": "team",
    "performance": "performance", "announcements": "announcements", "diagnosis": "diagnosis", "brands": "brands",
    "finance": "accounting", "cash": "accounting", "receivables": "accounting", "profit": "reports", "reports": "reports",
    "settings": "settings",
}
COMMON_FIRST = {"auth", "notifications", "public", "health", "upload", "files", "proxy-image", "push"}
SHARED_READ = {"customers", "technicians", "brands", "parts", "settings", "analytics", "dashboard", "export-xlsx"}


def perm_of(path: str):
    p = path[5:] if path.startswith("/api/") else path.lstrip("/")
    parts = p.split("/")
    first = parts[0]
    if first in COMMON_FIRST:
        return "common"
    if first == "governance":
        return "common" if p == "governance/roles" else "owner"
    if first in ("admin-users", "security"):
        return "owner"
    two = "/".join(parts[:2])
    if two in PREFIX_PERM:
        return PREFIX_PERM[two]
    if first in PREFIX_PERM:
        return PREFIX_PERM[first]
    if first == "export-xlsx":
        return "shared"
    return None


def allowed_user(user: dict, path: str, method: str) -> bool:
    """Özel yetkili yönetici için kesin kontrol; diğerleri eski rol mantığıyla."""
    if (user.get("admin_role") or "owner") == "custom":
        need = perm_of(path)
        read = method in ("GET", "HEAD", "OPTIONS")
        if need == "common":
            return True
        if need in (None, "owner"):
            return False
        perms = user.get("perms") or []
        ro = bool(user.get("perms_ro"))
        first = (path[5:] if path.startswith("/api/") else path.lstrip("/")).split("/")[0]
        if need == "shared":
            return read
        if need in perms:
            return read or not ro
        # ortak bakış verileri (liste/arama kutuları) yalnız okunur
        return read and first in SHARED_READ
    return allowed(user.get("admin_role") or "owner", path, method)


def decorate_user(u: dict) -> dict:
    if u and u.get("role") == "admin":
        r = u.get("admin_role") or "owner"
        u["admin_role"] = r
        u["admin_role_label"] = ROLES.get(r, r)
        u["areas"] = ROLE_AREAS.get(r, {})
        if r == "custom":
            u["perms"] = [k for k in (u.get("perms") or []) if k in PERM_KEYS]
            u["areas"] = {"ops": "rw", "finance": "rw", "reports": "rw", "site": "rw", "settings": "rw", "common": "rw"}  # menü süzmesi perms ile yapılır
    return u


# ============================================================== TOTP (RFC 6238)
def _b32(secret: str) -> bytes:
    return base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)


def totp_at(secret: str, counter: int, digits: int = 6) -> str:
    h = hmac.new(_b32(secret), struct.pack(">Q", counter), "sha1").digest()
    o = h[-1] & 15
    return str((struct.unpack(">I", h[o:o + 4])[0] & 0x7FFFFFFF) % 10 ** digits).zfill(digits)


def totp_verify(secret: str, code: str, last_counter: int = 0):
    """Geçerliyse kullanılan counter'ı döner (tekrar kullanımı engellemek için), değilse None."""
    code = re.sub(r"\D", "", code or "")
    if len(code) != 6:
        return None
    now = int(time.time() // 30)
    for c in (now - 1, now, now + 1):
        if c > last_counter and hmac.compare_digest(totp_at(secret, c), code):
            return c
    return None


def _fernet():
    from cryptography.fernet import Fernet
    key = base64.urlsafe_b64encode(hashlib.sha256((os.environ.get("JWT_SECRET", "dev") + "|2fa").encode()).digest())
    return Fernet(key)


def _hash_code(c: str) -> str:
    return hashlib.sha256(re.sub(r"[^A-Za-z0-9]", "", c).lower().encode()).hexdigest()


async def two_fa_enabled(db, user_id: str) -> bool:
    d = await db.user_2fa.find_one({"user_id": user_id, "enabled": True}, {"_id": 0, "user_id": 1})
    return bool(d)


async def two_fa_check(db, user_id: str, code: str) -> bool:
    """Giriş sırasında TOTP veya yedek kod doğrular."""
    d = await db.user_2fa.find_one({"user_id": user_id, "enabled": True})
    if not d:
        return True
    secret = _fernet().decrypt(d["secret_enc"].encode()).decode()
    c = totp_verify(secret, code, d.get("last_counter", 0))
    if c:
        await db.user_2fa.update_one({"user_id": user_id}, {"$set": {"last_counter": c}})
        return True
    h = _hash_code(code or "")
    if h in d.get("backup_hashes", []):
        await db.user_2fa.update_one({"user_id": user_id}, {"$pull": {"backup_hashes": h}})
        return True
    return False


# ---- Yöneticiler için 2FA zorunluluğu (ayar: app_settings._id="sec_policy")
_POL = {"t": 0.0, "v": False}
_TFA = {}


async def two_fa_required(db) -> bool:
    if time.time() - _POL["t"] > 20:
        d = await db.app_settings.find_one({"_id": "sec_policy"}, {"_id": 0}) or {}
        _POL.update(t=time.time(), v=bool(d.get("require_2fa")))
    return _POL["v"]


async def two_fa_gate(db, user: dict, path: str) -> bool:
    """True ise bu istek engellenmeli: zorunluluk açık, kullanıcı yönetici ve 2FA'sı yok (kurulum/giriş uçları hariç)."""
    if user.get("role") != "admin" or path.startswith("/api/auth/"):
        return False
    if not await two_fa_required(db):
        return False
    uid = user["id"]
    c = _TFA.get(uid)
    if c is None or time.time() - c[0] > 15:
        c = (time.time(), await two_fa_enabled(db, uid))
        _TFA[uid] = c
    return not c[1]


# ============================================================== DENETİM KAYDI + ÇÖP KUTUSU
TRASH_MAP = {   # url parçası -> (koleksiyon, etiket alanları)
    "jobs": ("service_jobs", ("job_number", "customer_name")),
    "customers": ("customers", ("name", "phone")),
    "devices": ("devices", ("model", "serial_no")),
    "parts": ("spare_parts", ("name", "sku")),
    "appointments": ("appointments", ("title",)),
    "cash/transactions": ("cash_transactions", ("description", "amount")),
    "quotes": ("price_quotes", ("quote_number", "customer_name")),
    "brands": ("brands", ("name",)),
    "messages": ("contact_messages", ("name", "type")),
    "dealers": ("dealer_applications", ("company", "name")),
    "warranty-claims": ("warranty_claims", ("customer_name",)),
    "reviews": ("reviews", ("name", "customer_name")),
    "announcements": ("announcements", ("title",)),
    "technicians": ("users", ("name", "email")),
    "admin-users": ("users", ("name", "email")),
    "diagnosis": ("diagnosis_kb", ("title",)),
}
_DEL_RE = re.compile(r"^/api/(" + "|".join(re.escape(k) for k in TRASH_MAP) + r")/([^/]+)$")
SKIP_AUDIT = re.compile(r"^/api/(auth/(logout)|public/|notifications|jobs/[^/]+/location|governance/health)")
NOUNS = {
    "jobs": "iş", "customers": "müşteri", "devices": "cihaz", "parts": "parça", "appointments": "randevu",
    "cash": "kasa hareketi", "quotes": "teklif", "brands": "marka", "messages": "mesaj", "dealers": "bayi başvurusu",
    "warranty-claims": "garanti talebi", "reviews": "yorum", "announcements": "duyuru", "technicians": "usta",
    "admin-users": "yönetici hesabı", "finance": "muhasebe kaydı", "studio": "site stüdyosu", "media": "medya",
    "settings": "ayarlar", "security": "güvenlik", "governance": "yönetim", "diagnosis": "arıza rehberi",
    "profit": "kârlılık ayarı", "auth": "hesap",
}
VERBS = {"POST": "oluşturdu/işlem yaptı", "PUT": "güncelledi", "PATCH": "güncelledi", "DELETE": "sildi"}
SPECIAL = {
    "publish": "Siteyi yayınladı", "restore": "Geri yükledi", "reassign": "İşi başka ustaya atadı",
    "transfer": "Hesaplar arası virman yaptı", "pay": "Ödeme yaptı", "cash-counts": "Kasa sayımı yaptı",
    "change-password": "Şifre değiştirdi", "backups": "Yedek işlemi yaptı", "reset-2fa": "2FA sıfırladı",
}


def _label(method: str, path: str) -> str:
    segs = [s for s in path[5:].split("/") if s]
    for s in reversed(segs):
        if s in SPECIAL:
            return SPECIAL[s]
    noun = NOUNS.get(segs[0], segs[0]) if segs else "kayıt"
    if segs[0] == "finance" and len(segs) > 1:
        noun = "muhasebe/" + segs[1]
    return f"{noun.capitalize()} {VERBS.get(method, method)}"


def _norm_route(path: str) -> str:
    return re.sub(r"/[0-9a-f]{8}-[0-9a-f-]{27}|/[0-9a-f]{24,}", "/{id}", path)


def _summ(doc: dict, fields) -> str:
    return " · ".join(str(doc.get(f)) for f in fields if doc.get(f))[:140]


async def audit(db, user: dict, action: str, detail: str = "", ip: str = "", **extra):
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "at": notify._now(), "user_id": (user or {}).get("id", ""),
        "user_name": (user or {}).get("name", ""), "role": (user or {}).get("role", ""),
        "admin_role": (user or {}).get("admin_role", ""), "action": action, "detail": detail, "ip": ip, **extra})


SITE_ED_OK = ("/api/brand", "/api/firm/", "/api/yp/content", "/api/yp/dil", "/api/yp/site", "/api/yp/popup", "/api/yp/redirect",
              "/api/yp/yonlendir", "/api/yp/duyuru", "/api/yp/destek", "/api/yp/logo", "/api/yp/media", "/api/yp/promo", "/api/yp/book")
FU_ROL = {}   # alt kullanıcı e-postası -> (rol, zaman)
SUB_ROL_AD = {"manager": "Müdür", "accounting": "Muhasebe", "operations": "Operasyon", "site_editor": "Site editörü", "viewer": "Yalnızca görüntüleme"}


async def fu_rol(db, email):
    now = time.time()
    c = FU_ROL.get(email)
    if c and now - c[1] < 30:
        return c[0]
    d = await db.main().firm_users.find_one({"email": email}, {"_id": 0, "rol": 1}) or {}
    r = d.get("rol") or "manager"
    FU_ROL[email] = (r, now)
    return r


def make_middleware(db, get_current_user):
    async def middleware(request: Request, call_next):
        path, method = request.url.path, request.method
        if not path.startswith("/api/") or method == "OPTIONS":
            return await call_next(request)
        user = None
        if request.headers.get("authorization") or request.cookies.get("access_token"):
            try:
                user = await get_current_user(request)      # sonuç request.state'te önbellek: ikinci DB okuması yok
            except HTTPException:
                user = None
            except Exception:                           # noqa: BLE001
                user = None
        if user and user.get("fu"):
            # firma alt kullanıcısı: ana hesap bu kullanıcıya bir rol vermiştir (Müdür, Muhasebe, Operasyon, Site editörü, Yalnızca görüntüleme)
            rol = await fu_rol(db, user["fu"])
            if path.startswith("/api/auth/") or (path in ("/api/yp/boot", "/api/firm/users") and method == "GET"):
                pass
            elif rol == "site_editor" and path.startswith(SITE_ED_OK):
                pass
            elif (method == "DELETE" and rol != "manager") or (rol == "viewer" and method not in ("GET", "HEAD")) or (rol != "viewer" and not allowed(rol, path, method)):
                if not (path.endswith("/auth/logout")) and rol is not None:
                    return JSONResponse(status_code=403, content={"detail": "Bu işlem için yetkiniz yok (rol: " + SUB_ROL_AD.get(rol, rol) + ")"})
            user = dict(user, admin_role="owner")
        if user and user.get("role") == "admin":
            # SILME YETKISI YALNIZCA SAHIP (asil admin) HESABINDADIR: diger tum yonetici rolleri (mudur, muhasebe, operasyon,
            # site editoru, ozel yetki) hicbir kaydi silemez. Tek istisna: servis kaydindaki indirimi geri alma (duzenleme sayilir).
            if method == "DELETE" and (user.get("admin_role") or "owner") != "owner" and not re.match(r"^/api/jobs/[^/]+/discount/?$", path):
                return JSONResponse(status_code=403, content={"detail": "Silme yetkisi yalnızca Sahip (admin) hesabındadır."})
            if not allowed_user(user, path, method):
                return JSONResponse(status_code=403, content={"detail": "Bu bölüm için yetkiniz yok (rol: " + ROLES.get(user.get("admin_role") or "owner", "") + ")"})
        snap = None
        m = _DEL_RE.match(path) if method == "DELETE" else None
        if user and m:
            coll, fields = TRASH_MAP[m.group(1)]
            q = {"id": m.group(2)}
            if m.group(1) == "technicians":
                q["role"] = "technician"
            if m.group(1) == "admin-users":
                q["role"] = "admin"
            snap = await db[coll].find_one(q)
        try:
            response = await call_next(request)
        except Exception as e:                          # noqa: BLE001
            await log_error(db, request, e, user)
            return JSONResponse(status_code=500, content={"detail": "Sunucu hatası. Kayıt altına alındı."})
        async def _after():
            try:
                if response.status_code >= 500:
                    await log_error(db, request, RuntimeError(f"HTTP {response.status_code}"), user, trace=False)
                if user and method in ("POST", "PUT", "PATCH", "DELETE") and response.status_code < 400 and not SKIP_AUDIT.match(path):
                    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "")
                    detail = ""
                    extra = {"method": method, "route": _norm_route(path), "status": response.status_code}
                    if snap is not None:
                        coll, fields = TRASH_MAP[m.group(1)]
                        detail = _summ(snap, fields)
                        snap.pop("_id", None)
                        await db.trash.insert_one({
                            "id": str(uuid.uuid4()), "collection": coll, "kind": m.group(1), "doc_id": m.group(2), "label": detail,
                            "doc": json.loads(json_util.dumps(snap)), "deleted_by": user.get("name", ""),
                            "deleted_at": notify._now(),
                            "expires_at": (datetime.now(timezone.utc) + timedelta(days=TRASH_DAYS)).isoformat()})
                        extra["trashed"] = True
                    await audit(db, user, _label(method, path), detail, ip, **extra)
            except Exception as e:                          # noqa: BLE001
                log.warning("audit yazılamadı: %s", e)
        if user and method in ("POST", "PUT", "PATCH", "DELETE") or response.status_code >= 500:
            asyncio.create_task(_after())          # denetim kaydı yanıtı geciktirmesin
        return response
    return middleware


def reap_stale():
    """Yeniden başlatmalardan kalan eski uygulama süreçlerini (aynı klasör, bizden eski) kapatır: hosting iş parçacığı kotasını doldurmasın."""
    import os, glob, signal
    me, killed = os.getpid(), []
    try:
        cwd = os.path.realpath(os.getcwd())
        anc, p = {me}, me
        for _ in range(6):
            try:
                p = int(open("/proc/%d/stat" % p).read().rsplit(")", 1)[1].split()[1])
            except Exception:  # noqa: BLE001
                break
            if p <= 1:
                break
            anc.add(p)
        my_start = int(open("/proc/%d/stat" % me).read().rsplit(")", 1)[1].split()[19])
        uid = os.getuid()
        for d in glob.glob("/proc/[0-9]*"):
            try:
                pid = int(d.rsplit("/", 1)[1])
                if pid in anc or "Uid:\t%d" % uid not in open(d + "/status").read():
                    continue
                if os.path.realpath(os.readlink(d + "/cwd")) != cwd:
                    continue
                st = int(open(d + "/stat").read().rsplit(")", 1)[1].split()[19])
                if st < my_start - 300:                    # bizden en az 3 sn eski
                    os.kill(pid, signal.SIGTERM)
                    killed.append(pid)
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        pass
    return killed


def _acct():
    """Hesaptaki tüm süreçlerin iş parçacığı dökümü (hosting kotası teşhisi)."""
    import os, glob
    out, tot, me = [], 0, os.getuid()
    for d in glob.glob("/proc/[0-9]*"):
        try:
            st = open(d + "/status").read()
            if "Uid:\t%d" % me not in st:
                continue
            nm = st.split("Name:\t", 1)[1].split("\n", 1)[0]
            th = int(st.split("Threads:\t", 1)[1].split("\n", 1)[0])
            tot += th
            out.append("%s:%s:%d" % (d.rsplit("/", 1)[1], nm, th))
        except Exception:  # noqa: BLE001
            pass
    return {"total_threads": tot, "procs": out[:40]}


async def log_error(db, request, exc, user=None, trace=True):
    try:
        doc = {"id": str(uuid.uuid4()), "at": notify._now(), "method": request.method, "path": request.url.path,
               "error": str(exc)[:300], "type": type(exc).__name__, "user": (user or {}).get("email", ""),
               "trace": traceback.format_exc()[-2500:] if trace else ""}
        await db.error_log.insert_one(doc)
        log.error("hata %s %s: %s", request.method, request.url.path, exc)
        last = await db.app_settings.find_one({"_id": "global"}, {"_id": 0, "last_error_notice": 1}) or {}
        if time.time() - float(last.get("last_error_notice", 0)) > 1800:          # 30 dk'da bir bildirim
            await db.app_settings.update_one({"_id": "global"}, {"$set": {"last_error_notice": time.time()}}, upsert=True)
            asyncio.create_task(notify.notify_owner(db, f"Sunucu hatası: {request.method} {request.url.path} — {str(exc)[:120]}", "error"))
    except Exception:                                   # noqa: BLE001
        pass


# ============================================================== YEDEKLEME
SKIP_BACKUP = {"system.indexes"}


def _bfile(name: str) -> Path:
    if not re.fullmatch(r"backup-[0-9A-Za-z_\-]+\.ndjson\.gz", name):
        raise HTTPException(status_code=400, detail="Geçersiz yedek adı")
    return BACKUP_DIR / name


async def make_backup(db, kind: str = "manual") -> dict:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    name = f"backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{kind}.ndjson.gz"
    path = BACKUP_DIR / name
    tmp = path.with_suffix(".tmp")
    counts = {}
    # Hız: okuma toplu (300'lük), JSON + gzip yazımı ayrı iplikte -> yedek sürerken panel istekleri bekletilmez
    f = gzip.open(tmp, "wt", encoding="utf-8", compresslevel=5)
    try:
        await asyncio.to_thread(f.write, json.dumps({"meta": {"version": 1, "created_at": notify._now(), "kind": kind}}) + "\n")
        for c in sorted(await db.list_collection_names()):
            if c in SKIP_BACKUP or c.startswith("system."):
                continue
            n = 0
            cur = db[c].find({})
            while True:
                docs = await cur.to_list(300)
                if not docs:
                    break
                await asyncio.to_thread(lambda docs=docs, c=c: f.write("".join(json_util.dumps({"c": c, "d": d}) + "\n" for d in docs)))
                n += len(docs)
                await asyncio.sleep(0)
            counts[c] = n
    finally:
        await asyncio.to_thread(f.close)
    tmp.replace(path)
    info = {"name": name, "size": path.stat().st_size, "counts": counts, "kind": kind}
    await db.backup_log.insert_one({"id": str(uuid.uuid4()), "at": notify._now(), **info, "ok": True})
    return info


def verify_backup(path: Path) -> dict:
    counts, meta = {}, None
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for i, line in enumerate(f):
                o = json_util.loads(line)
                if i == 0 and "meta" in o:
                    meta = o["meta"]
                    continue
                counts[o["c"]] = counts.get(o["c"], 0) + 1
    except Exception as e:                              # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}
    return {"ok": bool(meta), "meta": meta, "counts": counts, "total": sum(counts.values())}


async def restore_backup(db, path: Path) -> dict:
    v = verify_backup(path)
    if not v["ok"]:
        raise HTTPException(status_code=400, detail="Yedek dosyası bozuk: " + v.get("error", ""))
    pre = await make_backup(db, "pre-restore")
    batches, restored = {}, {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            o = json_util.loads(line)
            if "meta" in o:
                continue
            batches.setdefault(o["c"], []).append(o["d"])
    for c, docs in batches.items():
        await db[c].delete_many({})
        if docs:
            await db[c].insert_many(docs)
        restored[c] = len(docs)
    return {"restored": restored, "pre_restore_backup": pre["name"]}


def list_backups():
    if not BACKUP_DIR.exists():
        return []
    out = []
    for p in sorted(BACKUP_DIR.glob("backup-*.ndjson.gz"), reverse=True):
        st = p.stat()
        out.append({"name": p.name, "size": st.st_size, "at": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                    "kind": p.name.split("-")[-1].replace(".ndjson.gz", "")})
    return out


async def backup_settings(db) -> dict:
    s = (await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}).get("backup") or {}
    d = {"enabled": True, "interval_hours": 24, "keep": 14, "external_url": "", "external_headers": "", "last_auto": ""}
    d.update(s)
    return d


async def run_auto_backup(db, force=False):
    cfg = await backup_settings(db)
    if not force:
        if not cfg["enabled"]:
            return None
        last = cfg.get("last_auto")
        if last and datetime.fromisoformat(last) > datetime.now(timezone.utc) - timedelta(hours=int(cfg["interval_hours"])):
            return None
    if not force:
        att = cfg.get("last_attempt")              # yarıda kesilen yedek (uygulama kapatıldıysa) her açılışta yeniden başlamasın: 6 saatte bir dene
        if att and datetime.fromisoformat(att) > datetime.now(timezone.utc) - timedelta(hours=6):
            return None
    await db.app_settings.update_one({"_id": "global"}, {"$set": {"backup.last_attempt": notify._now()}}, upsert=True)
    info = await make_backup(db, "auto")
    await db.app_settings.update_one({"_id": "global"}, {"$set": {"backup.last_auto": notify._now()}}, upsert=True)
    autos = [b for b in list_backups() if b["kind"] == "auto"]
    for b in autos[int(cfg["keep"]):]:
        try:
            (BACKUP_DIR / b["name"]).unlink()
        except OSError:
            pass
    if cfg.get("external_url"):
        try:
            hd = notify._headers(cfg.get("external_headers", ""))
            def _put():
                with open(BACKUP_DIR / info["name"], "rb") as fh:
                    r = requests.put(cfg["external_url"].replace("{name}", info["name"]), data=fh, headers=hd, timeout=120)
                    r.raise_for_status()
            await asyncio.to_thread(_put)
            info["external"] = "ok"
        except Exception as e:                          # noqa: BLE001
            info["external"] = "hata: " + str(e)[:120]
            await notify.notify_owner(db, "Yedek dış kopyaya yüklenemedi: " + str(e)[:120], "backup")
    return info


# ============================================================== ZAMANLAYICI
HOOKS = []          # diğer modüller (async fn(db)) ekleyebilir; 5 dakikada bir çağrılır


async def scheduler(db, first_delay=45, tick=300):
    await asyncio.sleep(first_delay)
    while True:
        try:
            await run_auto_backup(db)
            await db.trash.delete_many({"expires_at": {"$lt": notify._now()}})
            cfg = (await notify.get_settings(db))["weekly_report"]
            if cfg.get("enabled"):
                now = datetime.now(notify_tz())
                last = cfg.get("last_sent") or ""
                if now.weekday() == int(cfg.get("weekday", 0)) and now.hour >= int(cfg.get("hour", 8)) and \
                        (not last or datetime.fromisoformat(last) < datetime.now(timezone.utc) - timedelta(days=6)):
                    await notify.send_weekly_report(db)
            try:
                ds = (await notify.get_settings(db))["daily_summary"]
                if ds.get("enabled"):
                    now = datetime.now(notify_tz())
                    last = ds.get("last_sent") or ""
                    if now.hour >= int(ds.get("hour", 8)) and (not last or datetime.fromisoformat(last).astimezone(notify_tz()).date() < now.date()):
                        await notify.send_daily_summary(db, notify_tz())
                await notify.survey_sweep(db)
                await notify.reminder_sweep(db, notify_tz())
            except Exception as e:                      # noqa: BLE001
                log.warning("günlük özet/anket: %s", e)
            for h in HOOKS:
                try:
                    await h(db)
                except Exception as e:                  # noqa: BLE001
                    log.warning("hook hatası: %s", e)
        except asyncio.CancelledError:
            raise
        except Exception as e:                          # noqa: BLE001
            log.warning("zamanlayıcı hatası: %s", e)
            try:
                await notify.notify_owner(db, "Zamanlayıcı hatası: " + str(e)[:120], "scheduler")
            except Exception:                           # noqa: BLE001
                pass
        await asyncio.sleep(tick)


def notify_tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Europe/Istanbul")
    except Exception:                                   # noqa: BLE001
        return timezone(timedelta(hours=3))


# ============================================================== ENDPOINT'LER
def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]
    verify_password = deps["verify_password"]
    hash_password = deps["hash_password"]

    @api_router.get("/health")
    async def health():
        try:
            await db.command("ping") if hasattr(db, "command") else None
            ok = True
        except Exception:                               # noqa: BLE001
            ok = False
        import threading as _th, os as _os
        return {"ok": ok, "uptime_s": int(time.time() - STARTED), "threads": _th.active_count(), "pid": _os.getpid(), "acct": _acct(), "names": sorted({t.name.split("_")[0].split("-")[0] for t in _th.enumerate()})[:12]}

    @api_router.get("/governance/roles")
    async def roles(_: dict = Depends(get_current_user)):
        return [{"key": k, "label": v, "desc": ROLE_DESC[k], "areas": ROLE_AREAS[k]} for k, v in ROLES.items()]

    # ---------------------------------------------------- yönetici rolleri
    @api_router.put("/governance/admins/{uid}/role")
    async def set_role(uid: str, payload: dict, me: dict = Depends(require_admin)):
        role = payload.get("role")
        if role not in ROLES:
            raise HTTPException(status_code=400, detail="Geçersiz rol")
        target = await db.users.find_one({"id": uid, "role": "admin"})
        if not target:
            raise HTTPException(status_code=404, detail="Yönetici bulunamadı")
        if (target.get("admin_role") or "owner") == "owner" and role != "owner":
            owners = [u async for u in db.users.find({"role": "admin", "is_active": {"$ne": False}}, {"admin_role": 1})
                      if (u.get("admin_role") or "owner") == "owner"]
            if len(owners) <= 1:
                raise HTTPException(status_code=400, detail="Sistemde en az bir 'Sahip' kalmalı")
        await db.users.update_one({"id": uid}, {"$set": {"admin_role": role, "tokens_valid_after": int(time.time())}, "$unset": {"perms": "", "perms_ro": ""}})
        return {"ok": True}

    @api_router.get("/governance/perm-modules")
    async def perm_modules(_: dict = Depends(get_current_user)):
        return [{"key": k, "label": l, "group": g} for k, l, g in PERM_MODULES]

    @api_router.put("/governance/admins/{uid}/perms")
    async def set_perms(uid: str, payload: dict, me: dict = Depends(require_admin)):
        target = await db.users.find_one({"id": uid, "role": "admin"})
        if not target:
            raise HTTPException(status_code=404, detail="Yönetici bulunamadı")
        perms = [k for k in (payload.get("perms") or []) if k in PERM_KEYS]
        if (target.get("admin_role") or "owner") == "owner":
            owners = [u async for u in db.users.find({"role": "admin", "is_active": {"$ne": False}}, {"admin_role": 1})
                      if (u.get("admin_role") or "owner") == "owner"]
            if len(owners) <= 1:
                raise HTTPException(status_code=400, detail="Sistemde en az bir 'Sahip' kalmalı")
        await db.users.update_one({"id": uid}, {"$set": {"admin_role": "custom", "perms": perms, "perms_ro": bool(payload.get("ro")),
                                                         "tokens_valid_after": int(time.time())}})
        return {"ok": True, "perms": perms}

    @api_router.post("/governance/admins/{uid}/reset-2fa")
    async def reset_2fa(uid: str, me: dict = Depends(require_admin)):
        await db.user_2fa.delete_one({"user_id": uid})
        _TFA.pop(uid, None)
        await db.users.update_one({"id": uid}, {"$set": {"totp_enabled": False}})
        return {"ok": True}

    # ---------------------------------------------------- 2FA
    @api_router.get("/auth/2fa/policy")
    async def tfa_policy(user: dict = Depends(get_current_user)):
        req = await two_fa_required(db)
        en = await two_fa_enabled(db, user["id"])
        return {"required": req, "enabled": en, "must_setup": bool(req and not en and user.get("role") == "admin")}

    @api_router.get("/governance/2fa-overview")
    async def tfa_overview(_: dict = Depends(require_admin)):
        rows = await db.users.find({"role": "admin"}, {"_id": 0, "id": 1, "name": 1, "email": 1, "is_active": 1}).to_list(200)
        on = {d["user_id"] async for d in db.user_2fa.find({"enabled": True}, {"_id": 0, "user_id": 1})}
        admins = [{"id": r["id"], "name": r.get("name", ""), "email": r.get("email", ""), "active": r.get("is_active", True) is not False, "enabled": r["id"] in on} for r in rows]
        return {"required": await two_fa_required(db), "admins": admins}

    @api_router.put("/governance/2fa-policy")
    async def tfa_policy_set(payload: dict, me: dict = Depends(require_admin)):
        want = bool(payload.get("required"))
        if want and not await two_fa_enabled(db, me["id"]):
            raise HTTPException(status_code=400, detail="Önce kendi hesabınızda 2 adımlı doğrulamayı (Hesabım) açın; yoksa siz de kilitlenirsiniz")
        await db.app_settings.update_one({"_id": "sec_policy"}, {"$set": {"require_2fa": want}}, upsert=True)
        _POL.update(t=0.0)
        await audit(db, me, "2FA zorunluluğunu " + ("açtı" if want else "kapattı"))
        return {"required": want}

    @api_router.get("/auth/2fa/status")
    async def tfa_status(user: dict = Depends(get_current_user)):
        d = await db.user_2fa.find_one({"user_id": user["id"]}, {"_id": 0})
        return {"enabled": bool(d and d.get("enabled")), "backup_left": len((d or {}).get("backup_hashes", []))}

    @api_router.post("/auth/2fa/setup")
    async def tfa_setup(user: dict = Depends(get_current_user)):
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Yalnızca yönetici hesapları için")
        secret = base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")
        await db.user_2fa.update_one({"user_id": user["id"]}, {"$set": {
            "user_id": user["id"], "secret_enc": _fernet().encrypt(secret.encode()).decode(), "enabled": False,
            "last_counter": 0, "backup_hashes": []}}, upsert=True)
        uri = f"otpauth://totp/ServisPlus:{user['email']}?secret={secret}&issuer=ServisPlus&digits=6&period=30"
        qr = None
        try:
            import segno
            buf = io.BytesIO()
            segno.make(uri, error="m").save(buf, kind="svg", scale=6, border=2)
            qr = "data:image/svg+xml;base64," + base64.b64encode(buf.getvalue()).decode()
        except Exception:                               # noqa: BLE001
            pass
        return {"secret": secret, "uri": uri, "qr": qr}

    @api_router.post("/auth/2fa/enable")
    async def tfa_enable(payload: dict, user: dict = Depends(get_current_user)):
        d = await db.user_2fa.find_one({"user_id": user["id"]})
        if not d:
            raise HTTPException(status_code=400, detail="Önce kurulumu başlatın")
        secret = _fernet().decrypt(d["secret_enc"].encode()).decode()
        c = totp_verify(secret, payload.get("code", ""))
        if not c:
            raise HTTPException(status_code=400, detail="Kod hatalı")
        codes = [secrets.token_hex(4) + "-" + secrets.token_hex(4) for _ in range(8)]
        await db.user_2fa.update_one({"user_id": user["id"]}, {"$set": {
            "enabled": True, "last_counter": c, "backup_hashes": [_hash_code(x) for x in codes]}})
        await db.users.update_one({"id": user["id"]}, {"$set": {"totp_enabled": True}})
        _TFA.pop(user["id"], None)
        await audit(db, user, "2FA etkinleştirdi")
        return {"ok": True, "backup_codes": codes}

    @api_router.post("/auth/2fa/disable")
    async def tfa_disable(payload: dict, user: dict = Depends(get_current_user)):
        full = await db.users.find_one({"id": user["id"]})
        if not verify_password(payload.get("password", ""), full.get("password_hash", "")):
            raise HTTPException(status_code=400, detail="Şifre hatalı")
        if not await two_fa_check(db, user["id"], payload.get("code", "")):
            raise HTTPException(status_code=400, detail="Kod hatalı")
        if await two_fa_required(db):
            raise HTTPException(status_code=400, detail="Tüm yöneticiler için 2 adımlı doğrulama zorunlu olduğundan kapatılamaz (Güvenlik sayfasından zorunluluğu kaldırın)")
        await db.user_2fa.delete_one({"user_id": user["id"]})
        _TFA.pop(user["id"], None)
        await db.users.update_one({"id": user["id"]}, {"$set": {"totp_enabled": False}})
        await audit(db, user, "2FA kapattı")
        return {"ok": True}

    # ---------------------------------------------------- denetim kaydı
    @api_router.get("/governance/audit")
    async def audit_list(q: str = "", user_id: str = "", date_from: str = "", date_to: str = "",
                         limit: int = 200, skip: int = 0, _: dict = Depends(require_admin)):
        f = {}
        if user_id:
            f["user_id"] = user_id
        if date_from or date_to:
            f["at"] = {}
            if date_from:
                f["at"]["$gte"] = date_from
            if date_to:
                f["at"]["$lte"] = date_to + "T23:59:59"
        if q:
            rx = {"$regex": re.escape(q), "$options": "i"}
            f["$or"] = [{"action": rx}, {"detail": rx}, {"user_name": rx}, {"route": rx}]
        total = await db.audit_log.count_documents(f)
        rows = await db.audit_log.find(f, {"_id": 0}).sort("at", -1).skip(skip).to_list(min(limit, 500))
        return {"total": total, "items": rows}

    # ---------------------------------------------------- çöp kutusu
    @api_router.get("/governance/trash")
    async def trash_list(_: dict = Depends(require_admin)):
        rows = await db.trash.find({}, {"_id": 0, "doc": 0}).sort("deleted_at", -1).to_list(500)
        return {"days": TRASH_DAYS, "items": rows}

    @api_router.post("/governance/trash/{tid}/restore")
    async def trash_restore(tid: str, me: dict = Depends(require_admin)):
        t = await db.trash.find_one({"id": tid})
        if not t:
            raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
        doc = json_util.loads(json.dumps(t["doc"]))
        if await db[t["collection"]].find_one({"id": t["doc_id"]}):
            raise HTTPException(status_code=409, detail="Bu kayıt zaten mevcut")
        try:
            await db[t["collection"]].insert_one(doc)
        except Exception as e:                          # noqa: BLE001
            raise HTTPException(status_code=409, detail="Geri yüklenemedi (çakışma): " + str(e)[:120])
        await db.trash.delete_one({"id": tid})
        await audit(db, me, "Çöp kutusundan geri yükledi", t.get("label", ""))
        return {"ok": True}

    @api_router.delete("/governance/trash/{tid}")
    async def trash_purge(tid: str, me: dict = Depends(require_admin)):
        await db.trash.delete_one({"id": tid})
        return {"ok": True}

    # ---------------------------------------------------- yedekler
    @api_router.get("/governance/backups")
    async def backups(_: dict = Depends(require_admin)):
        last = await db.backup_log.find({}, {"_id": 0}).sort("at", -1).to_list(1)
        return {"items": list_backups(), "settings": await backup_settings(db), "dir": str(BACKUP_DIR), "last": last[0] if last else None}

    @api_router.post("/governance/backups")
    async def backup_now(_: dict = Depends(require_admin)):
        return await make_backup(db, "manual")

    @api_router.put("/governance/backup-settings")
    async def backup_set(payload: dict, _: dict = Depends(require_admin)):
        cur = await backup_settings(db)
        for k in ("enabled", "interval_hours", "keep", "external_url", "external_headers"):
            if k in payload:
                cur[k] = payload[k]
        cur["interval_hours"] = max(1, int(cur["interval_hours"]))
        cur["keep"] = max(1, int(cur["keep"]))
        await db.app_settings.update_one({"_id": "global"}, {"$set": {"backup": cur}}, upsert=True)
        return cur

    @api_router.get("/governance/backups/{name}/download")
    async def backup_dl(name: str, _: dict = Depends(require_admin)):
        p = _bfile(name)
        if not p.exists():
            raise HTTPException(status_code=404, detail="Yedek yok")
        return FileResponse(p, filename=name, media_type="application/gzip")

    @api_router.post("/governance/backups/{name}/verify")
    async def backup_verify(name: str, _: dict = Depends(require_admin)):
        p = _bfile(name)
        if not p.exists():
            raise HTTPException(status_code=404, detail="Yedek yok")
        return await asyncio.to_thread(verify_backup, p)

    @api_router.post("/governance/backups/{name}/restore")
    async def backup_restore(name: str, payload: dict, me: dict = Depends(require_admin)):
        if payload.get("confirm") != "GERI YUKLE":
            raise HTTPException(status_code=400, detail="Onay metni hatalı")
        p = _bfile(name)
        if not p.exists():
            raise HTTPException(status_code=404, detail="Yedek yok")
        res = await restore_backup(db, p)
        await audit(db, me, "VERİTABANINI YEDEKTEN GERİ YÜKLEDİ", name)
        return res

    @api_router.delete("/governance/backups/{name}")
    async def backup_del(name: str, me: dict = Depends(require_admin)):
        p = _bfile(name)
        if p.exists():
            p.unlink()
            await audit(db, me, "YEDEK SİLDİ", name)
        return {"ok": True}

    @api_router.post("/governance/backups/upload")
    async def backup_upload(file: UploadFile = File(...), _: dict = Depends(require_admin)):
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        name = f"backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-uploaded.ndjson.gz"
        p = BACKUP_DIR / name
        with open(p, "wb") as f:
            shutil.copyfileobj(file.file, f)
        v = await asyncio.to_thread(verify_backup, p)
        if not v["ok"]:
            p.unlink()
            raise HTTPException(status_code=400, detail="Geçerli bir yedek dosyası değil")
        return {"name": name, **v}

    # ---------------------------------------------------- sağlık + hata
    @api_router.get("/governance/health")
    async def health_detail(_: dict = Depends(require_admin)):
        du = shutil.disk_usage(BACKUP_DIR if BACKUP_DIR.exists() else Path(__file__).parent)
        last = await db.backup_log.find({}, {"_id": 0}).sort("at", -1).to_list(1)
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        cfg = await backup_settings(db)
        age_h = None
        if last:
            age_h = round((datetime.now(timezone.utc) - datetime.fromisoformat(last[0]["at"])).total_seconds() / 3600, 1)
        warn = []
        if not last:
            warn.append("Hiç yedek alınmamış")
        elif age_h and age_h > cfg["interval_hours"] * 2 + 1:
            warn.append(f"Son yedek {age_h} saat önce — otomatik yedek çalışmıyor olabilir")
        if du.free / du.total < 0.1:
            warn.append("Disk alanı %10'un altında")
        return {"uptime_s": int(time.time() - STARTED), "disk_free_gb": round(du.free / 1e9, 1), "disk_total_gb": round(du.total / 1e9, 1),
                "last_backup": last[0] if last else None, "last_backup_age_h": age_h, "errors_24h": await db.error_log.count_documents({"at": {"$gte": since}}),
                "trash_count": await db.trash.count_documents({}), "outbox_failed_24h": await db.outbox.count_documents({"status": "failed", "created_at": {"$gte": since}}),
                "collections": {c: await db[c].count_documents({}) for c in ("service_jobs", "customers", "cash_transactions", "users", "audit_log")},
                "warnings": warn, "sentry": bool(os.environ.get("SENTRY_DSN"))}

    @api_router.get("/governance/errors")
    async def errors(_: dict = Depends(require_admin)):
        return await db.error_log.find({}, {"_id": 0}).sort("at", -1).to_list(100)

    @api_router.delete("/governance/errors")
    async def errors_clear(_: dict = Depends(require_admin)):
        await db.error_log.delete_many({})
        return {"ok": True}

    # ---------------------------------------------------- bildirim ayarları
    @api_router.get("/governance/notify-settings")
    async def ns_get(_: dict = Depends(require_admin)):
        return notify.masked(await notify.get_settings(db))

    @api_router.put("/governance/notify-settings")
    async def ns_put(payload: dict, _: dict = Depends(require_admin)):
        return notify.masked(await notify.save_settings(db, payload))

    @api_router.post("/governance/daily-summary-now")
    async def ds_now(_: dict = Depends(require_admin)):
        return await notify.send_daily_summary(db, notify_tz(), force=True)

    @api_router.post("/governance/notify-test")
    async def ns_test(payload: dict, _: dict = Depends(require_admin)):
        ch, to = payload.get("channel", "sms"), (payload.get("to") or "").strip()
        if not to:
            raise HTTPException(status_code=400, detail="Alıcı girin")
        return await notify.send(db, ch, to, "ServisPlus test mesajı ✔", subject="ServisPlus test", kind="test")

    @api_router.get("/governance/notify-diagnose")
    async def ns_diag(_: dict = Depends(require_admin)):
        return await notify.diagnose(db)

    @api_router.post("/governance/verimor-balance")
    async def verimor_bal(_: dict = Depends(require_admin)):
        try:
            return {"balance": await asyncio.to_thread(notify.verimor_balance, await notify.get_settings(db))}
        except Exception as e:                          # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(e)[:200])

    @api_router.post("/governance/verimor-headers")
    async def verimor_hd(_: dict = Depends(require_admin)):
        try:
            return {"headers": await asyncio.to_thread(notify.verimor_headers, await notify.get_settings(db))}
        except Exception as e:                          # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(e)[:200])

    @api_router.get("/governance/outbox")
    async def outbox(_: dict = Depends(require_admin)):
        return await db.outbox.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)

    @api_router.post("/governance/weekly-report/send")
    async def weekly_send(_: dict = Depends(require_admin)):
        return await notify.send_weekly_report(db, force=True)

    @api_router.get("/governance/weekly-report/preview")
    async def weekly_prev(_: dict = Depends(require_admin)):
        s = await notify.weekly_summary(db)
        return {"summary": s, "text": notify.weekly_text(s)}


async def ensure_indexes(db):
    await db.audit_log.create_index("at")
    await db.trash.create_index("id", unique=True)
    await db.trash.create_index("expires_at")
    await db.user_2fa.create_index("user_id", unique=True)
    await db.error_log.create_index("at")
    await db.outbox.create_index("created_at")
    await db.outbox.create_index([("kind", 1), ("ref", 1)])
