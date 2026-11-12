from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import asyncio
import re
import time
import secrets
import uuid
import random
import logging
import bcrypt
import jwt
import requests
from typing import List, Optional, Literal
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Response, UploadFile, File, Header, Query
from fastapi.responses import Response as FastAPIResponse
from pydantic import BaseModel, Field, EmailStr, field_validator
os.environ.setdefault('MOTOR_MAX_WORKERS', '4')      # paylaşımlı hosting iş parçacığı sınırı ("can't start new thread" 500 hatası)
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware.cors import CORSMiddleware

# -------------------------- Logging --------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# -------------------------- Config --------------------------
mongo_url = os.environ['MONGO_URL']
_mk = dict(
    serverSelectionTimeoutMS=int(os.environ.get('MONGO_TIMEOUT_MS', '20000')),
    connectTimeoutMS=int(os.environ.get('MONGO_TIMEOUT_MS', '20000')),
    socketTimeoutMS=60000,
    minPoolSize=int(os.environ.get('MONGO_MIN_POOL', '1')),   # sıcak bağlantı: her istekte yeni TLS el sıkışması olmasın
    maxPoolSize=int(os.environ.get('MONGO_MAX_POOL', '10')),
    maxIdleTimeMS=600000,
)
try:
    # "poll": sunucu başına ayrı akış/RTT izleme ipliği açılmaz (hosting iş parçacığı kotasını korur)
    client = AsyncIOMotorClient(mongo_url, serverMonitoringMode="poll", **_mk)
except Exception:       # noqa: BLE001  (eski pymongo)
    client = AsyncIOMotorClient(mongo_url, **_mk)
PROGRESS = lambda msg: None      # passenger_wsgi.py ilerleme gunlugu icin degistirir
import tenant
db = tenant.TenantDB(client, os.environ['DB_NAME'])    # firma hesabında istek bazlı ayrı veritabanı (tenant.py)

JWT_SECRET = os.environ.get('JWT_SECRET', 'changeme')
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_DAYS = 7
APP_NAME = os.environ.get('APP_NAME', 'kombi-klima-servis')
EMERGENT_KEY = os.environ.get('EMERGENT_LLM_KEY')
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"

storage_key = None

# Depolama: EMERGENT_LLM_KEY varsa bulut depo, yoksa (ör. cPanel) yerel disk (UPLOAD_DIR).
# STORAGE_MODE=local ile yerel disk zorlanabilir.
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR") or (ROOT_DIR / "uploads"))

def local_storage() -> bool:
    return os.environ.get("STORAGE_MODE", "").lower() == "local" or not EMERGENT_KEY

def _local_path(path: str) -> Path:
    p = (UPLOAD_DIR / path).resolve()
    if UPLOAD_DIR.resolve() not in p.parents:
        raise HTTPException(status_code=400, detail="Geçersiz dosya yolu")
    return p

def init_storage():
    global storage_key
    if local_storage():
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        return "local"
    if storage_key:
        return storage_key
    try:
        resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
        resp.raise_for_status()
        storage_key = resp.json()["storage_key"]
        logger.info("Storage initialized successfully")
        return storage_key
    except Exception as e:
        logger.error(f"Storage init failed: {e}")
        return None

def put_object(path: str, data: bytes, content_type: str) -> dict:
    if local_storage():
        p = _local_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return {"path": path, "size": len(data)}
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not available")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str):
    if local_storage():
        p = _local_path(path)
        if not p.is_file():
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        import mimetypes
        return p.read_bytes(), mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not available")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# -------------------------- Auth helpers --------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str, email: str, role: str, firm: str = "", fu: str = "") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_DAYS),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "access"
    }
    if firm:
        payload["firm"] = firm
    if fu:
        payload["fu"] = fu
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    _cu = getattr(request.state, "_cu", None)
    if _cu is not None:
        return _cu
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Yetkilendirme bulunamadı")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = speed.user_cache_get(payload["sub"])
        if user is None:
            user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
            if user:
                speed.user_cache_put(payload["sub"], user)
        if not user:
            raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Hesap pasifleştirilmiş")
        if user.get("tokens_valid_after") and payload.get("iat", 0) < user["tokens_valid_after"]:
            raise HTTPException(status_code=401, detail="Oturum sonlandırıldı")
        if user.get("role") == "admin" and await governance.two_fa_gate(db, user, request.url.path):
            raise HTTPException(status_code=403, detail="2FA_REQUIRED: Yönetici hesapları için 2 adımlı doğrulama zorunlu. Hesabım sayfasından Authy ile kurun.")
        if payload.get("fu"):
            user = dict(user)
            user["fu"] = payload["fu"]                                    # firma alt kullanıcısı: yalnız kendine atanan işleri görür
        request.state._cu = user
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Oturum süresi doldu")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz token")

async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekli")
    return user

# -------------------------- Models --------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_id: Optional[str] = ""
    phone: Optional[str] = ""
    otp: Optional[str] = ""
    portal: Optional[str] = ""
    cf_token: Optional[str] = ""


def tr_phone(v, required=False):
    """Telefonu +90XXXXXXXXXX biçimine getirir. Boşsa '' (required ise hata). Eksik/yanlışsa ValueError."""
    raw = str(v or "").strip()
    if not raw:
        if required:
            raise ValueError("Telefon numarası zorunlu")
        return ""
    d = re.sub(r"\D", "", raw)
    if d.startswith("00"):
        d = d[2:]
    if d.startswith("90") and len(d) == 12:
        d = d[2:]
    elif d.startswith("0") and len(d) == 11:
        d = d[1:]
    if len(d) != 10 or d[0] not in "2345" or len(set(d)) < 3:
        raise ValueError("Telefon numarası eksik veya hatalı. Örnek: +90 532 123 45 67")
    return "+90" + d

class TechnicianCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = ""
    commission_percent: float = 30.0
    is_active: bool = True

    @field_validator("phone", mode="before")
    @classmethod
    def _ph(cls, v):
        return v if v is None else tr_phone(v, False)

class TechnicianUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    commission_percent: Optional[float] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

    @field_validator("phone", mode="before")
    @classmethod
    def _ph(cls, v):
        return v if v is None else tr_phone(v, False)

class BrandCreate(BaseModel):
    name: str
    logo_url: Optional[str] = ""
    is_active: bool = True

class BrandUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None

class CustomerCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = ""
    address: Optional[str] = ""
    city: Optional[str] = ""
    district: Optional[str] = ""
    notes: Optional[str] = ""
    source_channel: Optional[str] = ""

    @field_validator("phone", mode="before")
    @classmethod
    def _ph(cls, v):
        return v if v is None else tr_phone(v, True)

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    notes: Optional[str] = None
    source_channel: Optional[str] = None

    @field_validator("phone", mode="before")
    @classmethod
    def _ph(cls, v):
        return v if v is None else tr_phone(v, False)

class DeviceCreate(BaseModel):
    customer_id: str
    brand_id: str
    type: str = "kombi"
    model: Optional[str] = ""
    serial_no: Optional[str] = ""
    install_date: Optional[str] = ""
    warranty_until: Optional[str] = ""
    notes: Optional[str] = ""

class PartUsed(BaseModel):
    part_id: Optional[str] = ""
    name: str
    qty: float = 1
    unit_price: float = 0
    total: float = 0
    list_price: float = 0      # stoktaki liste fiyatı (sunucu doldurur)
    unit_cost: float = 0       # parça maliyeti (stoktan sunucu doldurur)
    price_changed: bool = False

class ServiceJobCreate(BaseModel):
    customer_id: str
    device_id: Optional[str] = ""
    fault_description: str
    scheduled_at: Optional[str] = ""
    assigned_technician_id: Optional[str] = ""
    priority: Literal["dusuk", "normal", "yuksek", "acil"] = "normal"
    source_channel: Optional[str] = ""
    source_detail: Optional[str] = ""

class ServiceJobUpdate(BaseModel):
    fault_description: Optional[str] = None
    scheduled_at: Optional[str] = None
    assigned_technician_id: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    work_done: Optional[str] = None
    parts_used: Optional[List[PartUsed]] = None
    parts_none: Optional[bool] = None   # usta "parça kullanılmadı" dedi
    labor_fee: Optional[float] = None
    photos_before: Optional[List[str]] = None
    photos_after: Optional[List[str]] = None
    signature_url: Optional[str] = None
    tech_signature_url: Optional[str] = None
    pdf_note: Optional[str] = None
    cancel_reason: Optional[str] = None
    customer_rating: Optional[int] = None
    source_channel: Optional[str] = None
    tech_note: Optional[str] = Field(default=None, max_length=1000)   # yönetimden ustaya özel not (müşteri görmez, PDF'e girmez)
    # --- yalnızca yönetici (manuel kayıt düzenleme)
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    device_brand_name: Optional[str] = None
    device_model: Optional[str] = None
    device_type: Optional[str] = None
    device_serial: Optional[str] = None
    source_detail: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    manual_total: Optional[float] = None

class SparePartCreate(BaseModel):
    name: str
    sku: Optional[str] = ""
    brand_id: Optional[str] = ""
    price: float = 0
    cost: float = 0
    stock_qty: float = 0
    min_stock: float = 0
    unit: Optional[str] = "adet"
    supplier: Optional[str] = ""
    supplier_phone: Optional[str] = ""
    is_active: bool = True

class SparePartUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    brand_id: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    stock_qty: Optional[float] = None
    min_stock: Optional[float] = None
    unit: Optional[str] = None
    supplier: Optional[str] = None
    supplier_phone: Optional[str] = None
    is_active: Optional[bool] = None

class AppointmentCreate(BaseModel):
    title: str
    customer_id: Optional[str] = ""
    technician_id: Optional[str] = ""
    start_at: str
    end_at: Optional[str] = ""
    notes: Optional[str] = ""
    related_job_id: Optional[str] = ""

class CashTxCreate(BaseModel):
    type: Literal["gelir", "gider", "teknisyen_odeme", "teknisyen_borc", "teknisyen_prim", "manuel"]
    amount: float
    technician_id: Optional[str] = ""
    job_id: Optional[str] = ""
    description: str = ""
    date: Optional[str] = ""
    account_id: Optional[str] = ""
    category: Optional[str] = ""
    payment_method: Optional[str] = ""     # nakit | kart | havale | cek
    party: Optional[str] = ""              # kişi / firma
    staff_id: Optional[str] = ""
    receipt_no: Optional[str] = ""
    vat_rate: Optional[float] = None       # KDV oranı (%); boşsa ayarlardaki varsayılan
    has_invoice: Optional[bool] = None     # faturalı gider mi (KDV indirimi için)
    invoice_no: Optional[str] = ""

class QuotePartItem(BaseModel):
    name: str
    weight: Optional[float] = 1.0  # ağırlık (1-5), eşit dağıtım için varsayılan 1
    amount: Optional[float] = 0    # sistem tarafından hesaplanır

class PriceQuoteCreate(BaseModel):
    customer_name: str
    customer_phone: Optional[str] = ""
    customer_id: Optional[str] = ""
    device_brand_name: Optional[str] = ""
    device_model: Optional[str] = ""
    device_serial: Optional[str] = ""
    device_type: Optional[str] = ""
    fault_description: str = ""
    target_total: float
    labor_fee: float = 0
    parts: List[QuotePartItem] = []
    footer_note: Optional[str] = ""

class PriceQuoteUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_id: Optional[str] = None
    device_brand_name: Optional[str] = None
    device_model: Optional[str] = None
    device_serial: Optional[str] = None
    device_type: Optional[str] = None
    fault_description: Optional[str] = None
    target_total: Optional[float] = None
    labor_fee: Optional[float] = None
    parts: Optional[List[QuotePartItem]] = None
    footer_note: Optional[str] = None
    status: Optional[Literal["beklemede", "kabul", "red", "iptal"]] = None
    converted_job_id: Optional[str] = None

# -------------------------- App --------------------------
app = FastAPI(title="Kombi & Klima Servis Yönetimi")
api_router = APIRouter(prefix="/api")

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def clean_doc(doc):
    if doc and "_id" in doc:
        doc.pop("_id", None)
    return doc

# -------------------------- Cloudflare Turnstile (CAPTCHA) --------------------------
_CAP_OK = {}  # doğrulanmış token -> bitiş (2FA ikinci adımında aynı token yeniden kullanılabilsin)

async def captcha_cfg():
    d = await db.app_settings.find_one({"_id": "sp_modules"}, {"_id": 0}) or {}
    c = (d.get("config") or {}).get("turnstile") or {}
    on = bool((d.get("flags") or {}).get("turnstile"))
    if on and c.get("site_key") and c.get("secret_key"):
        return c["site_key"], c["secret_key"]
    return None

@api_router.get("/auth/captcha-config")
async def captcha_config():
    c = await captcha_cfg()
    return {"enabled": bool(c), "site_key": c[0] if c else ""}

async def captcha_check(token: str, ip: str, again: bool):
    c = await captcha_cfg()
    if not c:
        return
    token = (token or "").strip()
    now = time.time()
    for k in [k for k, v in _CAP_OK.items() if v < now]:
        _CAP_OK.pop(k, None)
    if not token:
        raise HTTPException(status_code=400, detail="Robot doğrulaması gerekli. Sayfayı yenileyip kutuyu işaretleyin.")
    if again and _CAP_OK.get(token, 0) > now:
        return
    def _verify():
        return requests.post("https://challenges.cloudflare.com/turnstile/v0/siteverify",
                             data={"secret": c[1], "response": token, "remoteip": ip}, timeout=6).json()
    try:
        r = await asyncio.to_thread(_verify)
    except Exception:
        return  # Cloudflare'e ulaşılamıyorsa yöneticiyi dışarıda bırakma (hatalı giriş kilidi yine geçerli)
    if not r.get("success"):
        raise HTTPException(status_code=400, detail="Robot doğrulaması başarısız. Sayfayı yenileyip tekrar deneyin.")
    _CAP_OK[token] = now + 180

# -------------------------- Auth Endpoints --------------------------
_FORGOT_HITS = {}

@api_router.post("/auth/forgot")
async def forgot_password(payload: dict, request: Request):
    """Personel şifre sıfırlama isteği: yöneticiye bildirim gider; yeni giriş bilgisi telefona gönderilir. Hesap var/yok bilgisi sızdırılmaz."""
    email = str(payload.get("email") or "").lower().strip()[:160]
    ip = security.client_ip(request)
    now = time.time()
    hits = [t for t in _FORGOT_HITS.get(ip, []) if now - t < 900]
    if len(hits) >= 4:
        raise HTTPException(status_code=429, detail="Çok fazla istek. Lütfen biraz sonra tekrar deneyin.")
    _FORGOT_HITS[ip] = hits + [now]
    user = await db.users.find_one({"email": email}, {"_id": 0, "id": 1, "name": 1, "role": 1, "phone": 1}) if "@" in email else None
    if user and user.get("role") in ("technician", "admin"):
        await db.password_requests.insert_one({"id": str(uuid.uuid4()), "user_id": user["id"], "name": user.get("name", ""), "email": email, "at": now_iso(), "ip": ip})
        try:
            await notify.push_admins_t(db, "Şifre sıfırlama isteği", f"{user.get('name', '')} ({email}) şifresini unuttu — Ekip bölümünden yeni şifre belirleyin", "/admin")
        except Exception:
            pass
    return {"ok": True}

@api_router.post("/auth/login")
async def login(payload: LoginRequest, response: Response, request: Request):
    email = payload.email.lower().strip()
    tenant.set_firm(None)                                                 # eski bir firma çerezi giriş aramasını bozmasın
    _fd = await db.main().firms.find_one({"login_email": email, "status": {"$ne": "silindi"}}, {"_id": 0, "db": 1, "expires_at": 1})
    _fu = None
    if not _fd:                                                           # firmanın eklediği alt kullanıcı mı?
        _fu = await db.main().firm_users.find_one({"email": email, "active": {"$ne": False}}, {"_id": 0})
        if _fu:
            _fd = await db.main().firms.find_one({"id": _fu["firm_id"], "status": {"$ne": "silindi"}}, {"_id": 0, "db": 1, "expires_at": 1})
    if not _fd:                                                           # firmanın kendi ustası / personeli (firma veritabanında)
        _fl = await db.main().firm_logins.find_one({"email": email}, {"_id": 0})
        if _fl:
            _fd = await db.main().firms.find_one({"db": _fl["db"], "status": {"$ne": "silindi"}}, {"_id": 0, "db": 1, "expires_at": 1})
    if _fd:
        if firms.expired(_fd):
            raise HTTPException(status_code=403, detail="Kullanım süreniz doldu. Lütfen yönetici ile görüşün.")
        tenant.set_firm(_fd["db"])                                        # bu istekte tüm okuma/yazma firmanın veritabanına gider
    if _fu:
        user = await db.users.find_one({"firm_owner": True})              # alt kullanıcı, ana hesapla aynı ekranı/veriyi kullanır
    else:
        user = await db.users.find_one({"email": email})
    # Usta mobil uygulaması (portal=app): teknisyen girişinde robot kutusu yok; hatalı giriş kilidi (security.check_login) yine geçerli.
    if not ((payload.portal or "") == "app" and user and user.get("role") == "technician"):
        await captcha_check(payload.cf_token, security.client_ip(request), bool((payload.otp or "").strip()))
    ok = bool(user) and await asyncio.to_thread(verify_password, payload.password, (_fu or user)["password_hash"])
    if user and ok and not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Hesabınız pasifleştirilmiş")
    bad_otp = False
    if ok and user.get("role") == "admin" and user.get("totp_enabled"):
        if not (payload.otp or "").strip():
            raise HTTPException(status_code=428, detail="otp_required")
        if not await governance.two_fa_check(db, user["id"], payload.otp):
            ok, bad_otp = False, True
    await security.check_login(db, request, email, user, ok, payload.device_id or "", payload.phone or "", payload.portal or "")
    if not ok:
        raise HTTPException(status_code=401, detail="Doğrulama kodu hatalı" if bad_otp else "E-posta veya şifre hatalı")
    token = create_access_token(user["id"], user["email"], user["role"], firm=(_fd or {}).get("db", ""), fu=(_fu or {}).get("email", ""))
    response.set_cookie(
        key="access_token", value=token, httponly=True, secure=False,
        samesite="lax", max_age=ACCESS_TOKEN_DAYS * 86400, path="/"
    )
    user.pop("password_hash", None)
    user.pop("_id", None)
    return {"token": token, "user": governance.decorate_user(user)}

@api_router.post("/auth/logout")
async def logout(response: Response, _: dict = Depends(get_current_user)):
    response.delete_cookie("access_token", path="/")
    return {"message": "Çıkış yapıldı"}

@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return governance.decorate_user(user)

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    iban: Optional[str] = None
    password: Optional[str] = None

@api_router.put("/auth/me")
async def update_me(payload: ProfileUpdate, user: dict = Depends(get_current_user)):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "phone" in update:                                  # her yerde aynı biçim: +90XXXXXXXXXX (boş bırakılamaz/yanlış olamaz)
        try:
            update["phone"] = tr_phone(update["phone"], required=user.get("role") == "technician")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    if "password" in update:
        update["password_hash"] = hash_password(update.pop("password"))
    if not update:
        raise HTTPException(status_code=400, detail="Güncellenecek alan yok")
    await db.users.update_one({"id": user["id"]}, {"$set": update})
    return await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)

@api_router.post("/auth/change-password")
async def change_password(payload: PasswordChange, user: dict = Depends(get_current_user)):
    full = await db.users.find_one({"id": user["id"]})
    if not full or not await asyncio.to_thread(verify_password, payload.current_password, full.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Mevcut şifre hatalı")
    await db.users.update_one({"id": user["id"]}, {"$set": {"password_hash": await asyncio.to_thread(hash_password, payload.new_password)}})
    return {"ok": True}

# -------------------------- Technicians (Users) --------------------------
@api_router.get("/technicians")
async def list_technicians(user: dict = Depends(get_current_user)):
    techs = await db.users.find({"role": "technician"}, {"_id": 0, "password_hash": 0}).to_list(1000)
    if user.get("role") != "admin":                      # bölge/uzmanlık bilgisi yalnızca yönetim için
        for t in techs:
            t.pop("profile", None)
    return techs

@api_router.post("/technicians")
async def create_technician(payload: TechnicianCreate, _: dict = Depends(require_admin)):
    email = payload.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if not existing and tenant.current():                                 # firma ustası: e-posta tüm platformda tekil olmalı
        existing = (await db.main().users.find_one({"email": email}) or await db.main().firms.find_one({"login_email": email})
                    or await db.main().firm_users.find_one({"email": email}) or await db.main().firm_logins.find_one({"email": email}))
    if existing:
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": hash_password(payload.password),
        "name": payload.name,
        "phone": payload.phone or "",
        "role": "technician",
        "commission_percent": float(payload.commission_percent),
        "is_active": payload.is_active,
        "created_at": now_iso()
    }
    await db.users.insert_one(user_doc)
    if tenant.current():
        await db.main().firm_logins.insert_one({"email": email, "db": tenant.current(), "user_id": user_doc["id"]})
    user_doc.pop("password_hash", None)
    user_doc.pop("_id", None)
    asyncio.create_task(notify.tech_welcome(db, dict(user_doc), payload.password))    # WhatsApp/SMS: link + kullanıcı adı + şifre
    return user_doc

@api_router.put("/technicians/{tech_id}")
async def update_technician(tech_id: str, payload: TechnicianUpdate, _: dict = Depends(require_admin)):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "password" in update:
        update["password_hash"] = hash_password(update.pop("password"))
    if not update:
        raise HTTPException(status_code=400, detail="Güncellenecek alan yok")
    res = await db.users.update_one({"id": tech_id, "role": "technician"}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Teknisyen bulunamadı")
    user = await db.users.find_one({"id": tech_id}, {"_id": 0, "password_hash": 0})
    return user

_TECH_GROUPS = ("kombi", "klima", "beyaz-esya", "televizyon", "sofben", "ocak-firin", "diger")


def _clean_list(v, n=40, ln=60):
    if isinstance(v, str):
        v = re.split(r"[,;\n]", v)
    out = []
    for x in (v or [])[:n]:
        x = str(x).strip()[:ln]
        if x and x.lower() not in [o.lower() for o in out]:
            out.append(x)
    return out


@api_router.get("/technicians/{tech_id}/profile")
async def tech_profile_get(tech_id: str, _: dict = Depends(require_admin)):
    u = await db.users.find_one({"id": tech_id, "role": "technician"}, {"_id": 0, "password_hash": 0})
    if not u:
        raise HTTPException(status_code=404, detail="Teknisyen bulunamadı")
    n = await db.technician_notes.find_one({"tech_id": tech_id}, {"_id": 0}) or {}
    done = await db.service_jobs.count_documents({"assigned_technician_id": tech_id, "status": {"$in": ["tamamlandi", "faturalandi"]}})
    return {"id": tech_id, "name": u.get("name", ""), "phone": u.get("phone", ""), "email": u.get("email", ""), "profile": u.get("profile") or {},
            "note": n.get("note", ""), "completed_jobs": done, "created_at": u.get("created_at", "")}


@api_router.put("/technicians/{tech_id}/profile")
async def tech_profile_put(tech_id: str, payload: dict, _: dict = Depends(require_admin)):
    u = await db.users.find_one({"id": tech_id, "role": "technician"}, {"_id": 0, "id": 1})
    if not u:
        raise HTTPException(status_code=404, detail="Teknisyen bulunamadı")
    try:
        exp = max(0, min(60, int(payload.get("experience_years") or 0)))
    except (TypeError, ValueError):
        exp = 0
    groups = [g for g in _clean_list(payload.get("service_groups"), 10, 30) if g in _TECH_GROUPS]
    prof = {"city": str(payload.get("city") or "").strip()[:40], "districts": _clean_list(payload.get("districts")),
            "service_groups": groups, "brands": _clean_list(payload.get("brands")), "experience_years": exp,
            "has_vehicle": bool(payload.get("has_vehicle")), "work_hours": str(payload.get("work_hours") or "").strip()[:120],
            "address": str(payload.get("address") or "").strip()[:300], "start_date": str(payload.get("start_date") or "").strip()[:10],
            "updated_at": now_iso()}
    await db.users.update_one({"id": tech_id}, {"$set": {"profile": prof}})
    if "note" in payload:
        await db.technician_notes.update_one({"tech_id": tech_id}, {"$set": {"tech_id": tech_id, "note": str(payload.get("note") or "")[:3000], "updated_at": now_iso()}}, upsert=True)
    return {"ok": True, "profile": prof}


@api_router.post("/technicians/{tech_id}/reset-credentials")
async def tech_reset_credentials(tech_id: str, _: dict = Depends(require_admin)):
    """Yeni şifre üretir (eskisi geçersiz olur); WhatsApp/SMS ile gönderilmek üzere giriş bilgilerini döner. Sağlayıcı açıksa otomatik de gönderir."""
    u = await db.users.find_one({"id": tech_id, "role": "technician"}, {"_id": 0, "password_hash": 0})
    if not u:
        raise HTTPException(status_code=404, detail="Teknisyen bulunamadı")
    alphabet = "abcdefghjkmnpqrstuvwxyzACDEFGHJKLMNPQRSTUVWXYZ23456789"
    pw = "".join(secrets.choice(alphabet) for _ in range(9))
    await db.users.update_one({"id": tech_id}, {"$set": {"password_hash": hash_password(pw)}})
    asyncio.create_task(notify.tech_welcome(db, dict(u), pw))
    return {"id": tech_id, "name": u.get("name", ""), "phone": u.get("phone", ""), "email": u.get("email", ""), "password": pw}

@api_router.delete("/technicians/{tech_id}")
async def delete_technician(tech_id: str, force: bool = False, _: dict = Depends(require_admin)):
    tech = await db.users.find_one({"id": tech_id, "role": "technician"}, {"_id": 0})
    if not tech:
        raise HTTPException(status_code=404, detail="Teknisyen bulunamadı")
    if not force:
        txs = await db.cash_transactions.find({"technician_id": tech_id}, {"_id": 0}).to_list(20000)
        balance = sum(t["amount"] for t in txs if t["type"] == "teknisyen_borc") - sum(t["amount"] for t in txs if t["type"] == "teknisyen_odeme")
        open_jobs = await db.service_jobs.count_documents({"assigned_technician_id": tech_id, "status": {"$in": ["atandi", "yolda", "basladi"]}})
        if round(balance, 2) != 0 or open_jobs:
            raise HTTPException(status_code=409, detail=f"Silinemez: kalan borç {balance:.2f} ₺, açık iş {open_jobs}. Önce hesabı kapatın ya da hesabı durdurun (veya zorla silin).")
    await db.users.delete_one({"id": tech_id, "role": "technician"})
    await db.main().firm_logins.delete_many({"user_id": tech_id})
    # Geçmiş kayıtlar (servis/kasa) isim olarak korunur; bayilik başvurusu bağı kopar
    await db.dealer_applications.update_many({"technician_id": tech_id}, {"$set": {"technician_id": "", "status": "reddedildi"}})
    return {"ok": True}

@api_router.get("/technicians/{tech_id}/balance")
async def technician_balance(tech_id: str, user: dict = Depends(get_current_user)):
    if user["role"] != "admin" and user["id"] != tech_id:
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    txs = await db.cash_transactions.find({"technician_id": tech_id}, {"_id": 0}).to_list(2000)
    # Teknisyen sahada parayı toplar; primini cebine alır, kalanı şirkete borçludur.
    total_debt = sum(t["amount"] for t in txs if t["type"] == "teknisyen_borc")
    total_paid = sum(t["amount"] for t in txs if t["type"] == "teknisyen_odeme")
    total_commission = sum(t["amount"] for t in txs if t["type"] == "teknisyen_prim")
    balance = total_debt - total_paid  # pozitif = teknisyen şirkete borçlu
    completed_jobs = await db.service_jobs.count_documents({
        "assigned_technician_id": tech_id,
        "status": {"$in": ["tamamlandi", "faturalandi"]}
    })
    tech_doc = await db.users.find_one({"id": tech_id}, {"_id": 0, "password_hash": 0})
    return {
        "technician_id": tech_id,
        "iban": (tech_doc or {}).get("iban", ""),
        "name": (tech_doc or {}).get("name", ""),
        "total_debt": round(total_debt, 2),
        "total_paid": round(total_paid, 2),
        "total_commission": round(total_commission, 2),
        "balance": round(balance, 2),
        "completed_jobs": completed_jobs,
        "transactions": sorted(txs, key=lambda x: x.get("date", ""), reverse=True)
    }

@api_router.get("/tech/pay-info")
async def tech_pay_info(user: dict = Depends(get_current_user)):
    """Usta Bakiyem sayfası: şirkete borç oranı + şirketin ödeme (IBAN) bilgileri."""
    if user.get("role") not in ("technician", "admin"):
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    shop = await db.app_settings.find_one({"_id": "shop_settings"}, {"_id": 0}) or {}
    g = await speed.cached_global(db)
    return {"commission_percent": float(user.get("commission_percent", 0) or 0),
            "accounts": [b for b in (shop.get("bank_accounts") or []) if b.get("iban")],
            "company": g.get("company_name", ""), "note": ""}

@api_router.get("/admin/badges")
async def admin_badges(user: dict = Depends(get_current_user)):
    """Admin menü rozetleri: yeni servis kaydı, gecikmiş iş, bekleyen teklif, borçlu usta, yedek uyarısı, toplam (tek istek)."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")

    async def _debtors():
        res = await db.cash_transactions.aggregate([
            {"$match": {"type": {"$in": ["teknisyen_borc", "teknisyen_odeme"]}}},
            {"$group": {"_id": {"t": "$technician_id", "y": "$type"}, "s": {"$sum": "$amount"}}}]).to_list(5000)
        bal = {}
        for r in res:
            k = r["_id"]["t"]
            bal[k] = bal.get(k, 0) + (r["s"] if r["_id"]["y"] == "teknisyen_borc" else -r["s"])
        return sum(1 for v in bal.values() if v > 0.5)

    async def _backup_warn():
        last = await db.backup_log.find({}, {"_id": 0, "at": 1}).sort("at", -1).to_list(1)
        if not last:
            return 1
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(last[0]["at"])).total_seconds() / 3600
        cfg = await governance.backup_settings(db)
        return 1 if age > int(cfg.get("interval_hours", 24)) * 2 + 1 else 0

    nowkey = datetime.now(governance.notify_tz()).strftime("%Y-%m-%dT%H:%M")
    jobs, overdue, quotes, debtors, bw, msgs, deal, warr, revs, nocall = await asyncio.gather(
        db.service_jobs.count_documents({"status": "yeni"}),
        db.service_jobs.count_documents({"status": {"$nin": ["tamamlandi", "faturalandi", "iptal"]}, "scheduled_at": {"$ne": "", "$lt": nowkey, "$exists": True}}),
        db.price_quotes.count_documents({"status": "beklemede"}),
        _debtors(), _backup_warn(),
        db.contact_messages.count_documents({"status": "yeni"}),
        db.dealer_applications.count_documents({"status": "yeni"}),
        db.warranty_claims.count_documents({"status": {"$in": ["acik", "inceleniyor"]}}),
        db.reviews.count_documents({"status": "beklemede"}),
        db.service_jobs.count_documents({"call_due_at": {"$lt": now_iso(), "$ne": ""}, "first_call_at": "", "status": {"$in": ["atandi", "yolda"]}}))
    try:                                                 # sitede şu an aktif ziyaretçi (mobil barda "Canlı" rozeti)
        import crm_extras
        live_n = await db.visitor_sessions.count_documents({"last_seen": {"$gte": (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()}})
    except Exception:                                    # noqa: BLE001
        live_n = 0
    return {"live_visitors": live_n, "call_overdue": nocall, "/admin/jobs": jobs, "jobs_overdue": overdue, "/admin/quotes": quotes, "/admin/technicians": debtors,
            "/admin/governance": bw, "messages": msgs, "backup_stale": bw, "dealers": deal, "warranty": warr, "reviews": revs,
            "total": nocall + jobs + overdue + quotes + msgs + deal + warr + revs}

@api_router.post("/public/track/{token}/reschedule")
async def track_reschedule(token: str, payload: dict, request: Request):
    """Takip sayfasından müşteri randevu değişikliği ister → İletişim Mesajları'nda 'yeni' mesaj olarak düşer."""
    ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
    now_ts = time.time()
    hist = [t for t in _RESCH.get(ip, []) if now_ts - t < 3600]
    if len(hist) >= 3:
        raise HTTPException(status_code=429, detail="Çok fazla deneme, biraz sonra tekrar deneyin")
    job = await db.service_jobs.find_one({"track_token": token}, {"_id": 0, "workshop": 0}) if len(token) >= 12 else None
    if not job:
        raise HTTPException(status_code=404, detail="Takip bağlantısı geçersiz")
    if job.get("status") in ("tamamlandi", "faturalandi", "iptal"):
        raise HTTPException(status_code=400, detail="Bu kayıt için değişiklik istenemez")
    note = str(payload.get("note") or "").strip()[:300]
    when = str(payload.get("when") or "").strip()[:60]
    hist.append(now_ts)
    _RESCH[ip] = hist
    await db.contact_messages.insert_one({
        "id": str(uuid.uuid4()), "type": "diger", "name": job.get("customer_name", ""), "phone": job.get("customer_phone", ""), "email": "",
        "city": "", "district": job.get("customer_district", ""), "device_type": job.get("device_type", ""), "brand": job.get("device_brand_name", ""),
        "message": f"[Randevu değişikliği talebi] Kayıt {job.get('job_number', '')}. İstenen zaman: {when or '-'}. {note}".strip(),
        "status": "yeni", "note": "", "job_id": job["id"], "job_number": job.get("job_number", ""), "source": {"channel": "takip"}, "channel": "takip",
        "page": "/takip", "sid": "", "ip": "", "ua": "", "created_at": now_iso(), "updated_at": now_iso()})
    await notify.push_admins_t(db, "Randevu değişikliği talebi", f"{job.get('job_number', '')} · İstenen tarih: {when or '-'}", "/admin/appointments")
    return {"ok": True}

_RESCH: dict = {}

@api_router.post("/tech/payment-notice")
async def tech_payment_notice(payload: dict, user: dict = Depends(get_current_user)):
    """Usta 'ödeme yaptım' bildirimi → admin'e İletişim Mesajları'nda yeni mesaj (kasa hareketi admin onayıyla girilir)."""
    if user.get("role") != "technician":
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    try:
        amount = float(payload.get("amount") or 0)
    except (TypeError, ValueError):
        amount = 0
    if amount <= 0 or amount > 10_000_000:
        raise HTTPException(status_code=422, detail="Geçerli bir tutar girin")
    note = str(payload.get("note") or "").strip()[:200]
    since = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
    if await db.contact_messages.find_one({"channel": "usta-odeme", "name": user.get("name", ""), "created_at": {"$gte": since}}):
        raise HTTPException(status_code=429, detail="Bildiriminiz alındı, birkaç dakika sonra tekrar deneyin")
    await db.contact_messages.insert_one({
        "id": str(uuid.uuid4()), "type": "diger", "name": user.get("name", ""), "phone": user.get("phone", ""), "email": user.get("email", ""),
        "city": "", "district": "", "device_type": "", "brand": "",
        "message": f"[Usta ödeme bildirimi] {user.get('name', '')} şirkete {amount:.2f} TL ödediğini bildirdi. {note}".strip(),
        "status": "yeni", "note": "", "job_id": "", "job_number": "", "source": {"channel": "usta-odeme"}, "channel": "usta-odeme",
        "page": "", "sid": "", "ip": "", "ua": "", "created_at": now_iso(), "updated_at": now_iso()})
    await notify.push_admins(db, "Usta ödeme bildirdi", f"{user.get('name', '')} · {amount:.2f} TL — kontrol edip kasaya işleyin", "/admin?ek=tahsilat")
    return {"ok": True}

# -------------------------- Sitede "Müşterilerimiz Ne Düşünüyor" (yalnızca GERÇEK, yayınlanmış yorumlar) --------------------------
_TRF = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u"})
_CATMAP = {"kombi": "kombi", "klima": "klima", "sofben": "sofben", "tv": "televizyon", "televizyon": "televizyon",
           "buzdolabi": "beyaz-esya", "camasir": "beyaz-esya", "bulasik": "beyaz-esya", "kurutma": "beyaz-esya", "firin": "beyaz-esya"}
_SRC: dict = {}


def _slug(x: str) -> str:
    x = (x or "").strip().lower().replace("İ", "i").translate(_TRF)
    return re.sub(r"[^a-z0-9]+", "-", x).strip("-")


async def _sr_settings() -> dict:
    d = await db.app_settings.find_one({"_id": "site_reviews"}, {"_id": 0}) or {}
    return {"enabled": bool(d.get("enabled", False)), "title": (d.get("title") or "Müşterilerimiz Ne Düşünüyor")[:80]}


@api_router.get("/site-reviews-settings")
async def sr_get(user: dict = Depends(require_admin)):
    return await _sr_settings()


@api_router.put("/site-reviews-settings")
async def sr_put(payload: dict, user: dict = Depends(require_admin)):
    cur = await _sr_settings()
    if "enabled" in payload:
        cur["enabled"] = bool(payload["enabled"])
    if payload.get("title"):
        cur["title"] = str(payload["title"]).strip()[:80]
    await db.app_settings.update_one({"_id": "site_reviews"}, {"$set": cur}, upsert=True)
    _SRC.clear()
    return cur


@api_router.get("/public/site-reviews")
async def public_site_reviews(brand: str = "", category: str = "", limit: int = 12):
    """Siteye açıkta gösterilecek yorumlar. Marka sayfası yalnız o markayı, kategori sayfası o kategoriyi, diğer sayfalar hepsini görür."""
    st = await _sr_settings()
    if not st["enabled"]:
        return {"enabled": False, "items": []}
    b, c = _slug(brand)[:40], _slug(category)[:30]
    key = (b, c, min(max(limit, 1), 24))
    hit = _SRC.get(key)
    if hit and time.time() - hit[0] < 60:
        return hit[1]
    revs = await db.reviews.find({"status": "yayinda"}, {"_id": 0, "ip": 0}).sort("created_at", -1).to_list(2000)
    jn = [r["job_number"] for r in revs if r.get("job_number") and not r.get("category")]
    if jn:   # eski yorumlarda marka/kategori yoksa servis kaydından tamamla
        jobs = {j["job_number"]: j for j in await db.service_jobs.find({"job_number": {"$in": jn[:300]}}, {"_id": 0, "job_number": 1, "device_brand_name": 1, "device_type": 1}).to_list(300)}
        for r in revs:
            j = jobs.get(r.get("job_number"))
            if j and not r.get("category"):
                r["brand"] = j.get("device_brand_name", "")
                r["category"] = _CATMAP.get(_slug(j.get("device_type", "")), "")
                await db.reviews.update_one({"id": r["id"]}, {"$set": {"brand": r["brand"], "category": r["category"]}})
    pool = revs
    if b:
        pool = [r for r in revs if _slug(r.get("brand", "")) == b]
    elif c:
        pool = [r for r in revs if _slug(r.get("category", "")) == c]
    n = len(pool)
    avg = round(sum(r.get("rating", 0) for r in pool) / n, 1) if n else 0
    items = [{"name": r.get("name", ""), "rating": r.get("rating", 5), "comment": r.get("comment", ""), "brand": r.get("brand", ""),
              "category": r.get("category", ""), "city": r.get("city", ""), "date": (r.get("created_at") or "")[:10], "reply": r.get("reply", "")}
             for r in pool if (r.get("comment") or "").strip()][:key[2]]
    out = {"enabled": True, "title": st["title"], "count": n, "avg": avg, "items": items}
    _SRC[key] = (time.time(), out)
    return out

@api_router.post("/tech/location")
async def tech_location(payload: dict, user: dict = Depends(get_current_user)):
    """Usta uygulaması açıkken konum bildirir (yalnız son konum saklanır)."""
    if user.get("role") != "technician":
        raise HTTPException(status_code=403, detail="Yalnızca teknisyen")
    try:
        lat, lng = float(payload["lat"]), float(payload["lng"])
    except Exception:
        raise HTTPException(status_code=422, detail="Konum geçersiz")
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise HTTPException(status_code=422, detail="Konum geçersiz")
    await db.users.update_one({"id": user["id"]}, {"$set": {"last_location": {"lat": round(lat, 5), "lng": round(lng, 5), "acc": round(float(payload.get("acc") or 0), 1), "at": now_iso()}}})
    return {"ok": True}

@api_router.get("/admin/tech-locations")
async def admin_tech_locations(_: dict = Depends(require_admin)):
    """Ustaların son konumu + o anki açık işi (yönetici haritası)."""
    now = datetime.now(timezone.utc)
    out = []
    techs = await db.users.find({"role": "technician", "is_active": {"$ne": False}}, {"_id": 0, "id": 1, "name": 1, "phone": 1, "last_location": 1}).to_list(500)
    for t in techs:
        loc = t.get("last_location") or {}
        row = {"id": t["id"], "name": t.get("name", ""), "phone": t.get("phone", "")}
        if loc.get("lat") is not None:
            try:
                age = int((now - datetime.fromisoformat(loc["at"])).total_seconds() // 60)
            except Exception:
                age = 99999
            row.update({"lat": loc["lat"], "lng": loc["lng"], "age_min": max(0, age)})
        j = await db.service_jobs.find_one({"assigned_technician_id": t["id"], "status": {"$in": ["yolda", "basladi"]}}, {"_id": 0, "id": 1, "job_number": 1, "status": 1, "customer_name": 1})
        if j:
            row.update({"job_id": j["id"], "job_number": j.get("job_number", ""), "job_status": j.get("status", ""), "customer": j.get("customer_name", "")})
        out.append(row)
    out.sort(key=lambda r: (r.get("lat") is None, r.get("age_min", 0)))
    return out

@api_router.get("/tech/badges")
async def tech_badges(user: dict = Depends(get_current_user)):
    """Usta alt menü rozetleri: yeni iş, bekleyen teklif, okunmamış duyuru, borç (tek istek)."""
    if user.get("role") != "technician":
        return {"jobs": 0, "quotes": 0, "ann": 0, "debt": 0}
    uid = user["id"]
    now = now_iso()

    async def _ann():
        items = await db.announcements.find({"is_active": True}, {"_id": 0, "id": 1, "audience": 1, "target_ids": 1, "expires_at": 1}).to_list(200)
        reads = {r["announcement_id"] for r in await db.announcement_reads.find({"user_id": uid}, {"_id": 0, "announcement_id": 1}).to_list(2000)}
        n = 0
        for a in items:
            if a.get("expires_at") and a["expires_at"] < now[:10]:
                continue
            if a.get("audience", "teknisyen") not in ("hepsi", "teknisyen"):
                continue
            tg = a.get("target_ids") or []
            if tg and uid not in tg:
                continue
            if a["id"] not in reads:
                n += 1
        return n

    async def _debt():
        res = await db.cash_transactions.aggregate([
            {"$match": {"technician_id": uid, "type": {"$in": ["teknisyen_borc", "teknisyen_odeme"]}}},
            {"$group": {"_id": "$type", "t": {"$sum": "$amount"}}}]).to_list(5)
        d = {r["_id"]: r["t"] for r in res}
        return max(0.0, float(d.get("teknisyen_borc", 0) or 0) - float(d.get("teknisyen_odeme", 0) or 0))

    jobs, quotes, ann, debt = await asyncio.gather(
        db.service_jobs.count_documents({"assigned_technician_id": uid, "status": "atandi"}),
        db.price_quotes.count_documents({"technician_id": uid, "status": "beklemede"}),
        _ann(), _debt())
    return {"jobs": jobs, "quotes": quotes, "ann": ann, "debt": round(debt, 2)}

# -------------------------- Brands --------------------------
@api_router.get("/brands")
async def list_brands(_: dict = Depends(get_current_user)):
    return await db.brands.find({}, {"_id": 0}).sort("name", 1).to_list(500)

@api_router.post("/brands")
async def create_brand(payload: BrandCreate, _: dict = Depends(require_admin)):
    doc = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "logo_url": payload.logo_url or "",
        "is_active": payload.is_active,
        "created_at": now_iso()
    }
    await db.brands.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.put("/brands/{brand_id}")
async def update_brand(brand_id: str, payload: BrandUpdate, _: dict = Depends(require_admin)):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    res = await db.brands.update_one({"id": brand_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Marka bulunamadı")
    return await db.brands.find_one({"id": brand_id}, {"_id": 0})

@api_router.delete("/brands/{brand_id}")
async def delete_brand(brand_id: str, _: dict = Depends(require_admin)):
    await db.brands.delete_one({"id": brand_id})
    return {"ok": True}

# -------------------------- Customers --------------------------
@api_router.get("/customers")
async def list_customers(q: Optional[str] = None, _: dict = Depends(get_current_user)):
    query = {}
    if q:
        query = {"$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"phone": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}}
        ]}
    return await db.customers.find(query, {"_id": 0}).sort("created_at", -1).to_list(2000)

@api_router.post("/customers")
async def create_customer(payload: CustomerCreate, _: dict = Depends(get_current_user)):
    if tenant.current():
        _ft = ((await db.app_settings.find_one({"_id": "firm"}, {"_id": 0})) or {}).get("features") or {}
        if _ft.get("customer_add") is False:
            raise HTTPException(status_code=403, detail="Müşteri ekleme bu hesapta kapalı")
    doc = payload.model_dump()
    doc["id"] = str(uuid.uuid4())
    doc["created_at"] = now_iso()
    await db.customers.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.post("/admin/phones/normalize")
async def phones_normalize(payload: dict, _: dict = Depends(require_admin)):
    """Mevcut kayıtlardaki telefonları +90 biçimine çevirir. apply=false → yalnız rapor; hatalı olanlar listelenir, dokunulmaz."""
    apply = bool(payload.get("apply"))
    out = {"fixed": 0, "already": 0, "invalid": []}
    for col, kind in ((db.customers, "Müşteri"), (db.users, "Kullanıcı")):
        q = {"phone": {"$nin": ["", None]}} if kind == "Müşteri" else {"role": "technician", "phone": {"$nin": ["", None]}}
        for r in await col.find(q, {"_id": 0, "id": 1, "name": 1, "phone": 1}).to_list(20000):
            try:
                n = tr_phone(r["phone"])
            except ValueError:
                out["invalid"].append({"tur": kind, "ad": r.get("name", ""), "telefon": r.get("phone", "")})
                continue
            if n == r["phone"]:
                out["already"] += 1
                continue
            out["fixed"] += 1
            if apply:
                await col.update_one({"id": r["id"]}, {"$set": {"phone": n}})
    out["invalid"] = out["invalid"][:200]
    return out

@api_router.get("/customers/{customer_id}")
async def get_customer(customer_id: str, _: dict = Depends(get_current_user)):
    cust = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not cust:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    devices = await db.devices.find({"customer_id": customer_id}, {"_id": 0}).to_list(200)
    jobs = await db.service_jobs.find({"customer_id": customer_id}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).sort("created_at", -1).to_list(200)
    repeated_faults = {}
    for j in jobs:
        key = j.get("fault_description", "").lower()[:50]
        repeated_faults[key] = repeated_faults.get(key, 0) + 1
    has_repeated = any(v > 1 for v in repeated_faults.values())
    return {"customer": cust, "devices": devices, "jobs": jobs, "has_repeated_fault": has_repeated}

@api_router.put("/customers/{customer_id}")
async def update_customer(customer_id: str, payload: CustomerUpdate, _: dict = Depends(get_current_user)):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    res = await db.customers.update_one({"id": customer_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    return await db.customers.find_one({"id": customer_id}, {"_id": 0})

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str, _: dict = Depends(require_admin)):
    await db.customers.delete_one({"id": customer_id})
    await db.devices.delete_many({"customer_id": customer_id})
    return {"ok": True}

# -------------------------- Devices --------------------------
@api_router.post("/devices")
async def create_device(payload: DeviceCreate, _: dict = Depends(get_current_user)):
    brand = await db.brands.find_one({"id": payload.brand_id}, {"_id": 0})
    if not brand:
        raise HTTPException(status_code=404, detail="Marka bulunamadı")
    doc = payload.model_dump()
    doc["id"] = str(uuid.uuid4())
    doc["brand_name"] = brand["name"]
    doc["brand_logo"] = brand.get("logo_url", "")
    doc["created_at"] = now_iso()
    await db.devices.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.delete("/devices/{device_id}")
async def delete_device(device_id: str, _: dict = Depends(require_admin)):
    await db.devices.delete_one({"id": device_id})
    return {"ok": True}

# -------------------------- Service Jobs --------------------------
async def next_job_number():
    """7 haneli rastgele iş numarası üretir, çakışma olursa tekrar dener."""
    for _ in range(20):
        n = random.randint(1000000, 9999999)
        candidate = f"SRV-{n}"
        if not await db.service_jobs.find_one({"job_number": candidate}):
            return candidate
    # Fallback: counter
    counter = await db.counters.find_one_and_update(
        {"_id": "job_number"}, {"$inc": {"seq": 1}},
        upsert=True, return_document=True
    )
    return f"SRV-{counter['seq']:07d}"


DONE_STATUSES = ("tamamlandi", "faturalandi")
AUTO_TX_TYPES = ("gelir", "teknisyen_prim", "teknisyen_borc")

async def _adjust_stock(parts, sign: int):
    """sign=-1: stoktan düş, sign=+1: stoğa geri ekle (yalnızca stoktan seçilmiş parçalar)."""
    for p in parts or []:
        if p.get("part_id"):
            await db.spare_parts.update_one({"id": p["part_id"]}, {"$inc": {"stock_qty": sign * float(p.get("qty", 0) or 0)}})

async def sync_job_ledger(before: dict, after: dict, user: dict):
    """Servis kaydı tamamlanınca stok + kasa hareketlerini üretir; sonradan düzenlenir/iptal edilirse
    aynı kaydı yeniden hesaplar (çift kayıt veya eski tutar kalmaz).
      commission_percent = teknisyenin ŞİRKETE BORÇ oranı
      company_debt = total x oran/100 ; tech_keeps = total - company_debt
    """
    was_done = before.get("status") in DONE_STATUSES
    is_done = after.get("status") in DONE_STATUSES
    if not was_done and not is_done:
        return
    changed = any(before.get(k) != after.get(k) for k in
                  ("parts_used", "labor_fee", "total_amount", "assigned_technician_id", "technician_commission_percent"))
    if was_done and is_done and not changed:
        return
    # 1) eski etkileri geri al
    if was_done:
        await _adjust_stock(before.get("parts_used"), +1)
        await db.cash_transactions.delete_many({"job_id": after["id"], "type": {"$in": list(AUTO_TX_TYPES)}})
    if not is_done:
        return
    # 2) yeni etkileri uygula
    await _adjust_stock(after.get("parts_used"), -1)
    total_amount = float(after.get("total_amount", 0) or 0)
    pct = float(after.get("technician_commission_percent", 0) or 0)
    company_debt = round(total_amount * pct / 100.0, 2)
    tech_keeps = round(total_amount - company_debt, 2)
    tech_id = after.get("assigned_technician_id", "")
    base = {"technician_id": tech_id, "job_id": after["id"], "date": after.get("completed_at") or now_iso(), "created_by": user["id"]}
    if total_amount > 0:
        await db.cash_transactions.insert_one({**base, "id": str(uuid.uuid4()), "type": "gelir", "amount": total_amount,
            "description": f"Servis Geliri - {after['job_number']} - {after['customer_name']}"})
    if tech_keeps > 0 and tech_id:
        await db.cash_transactions.insert_one({**base, "id": str(uuid.uuid4()), "type": "teknisyen_prim", "amount": tech_keeps,
            "description": f"Prim (Kasada Kalan) - {after['job_number']}"})
    if company_debt > 0 and tech_id:
        await db.cash_transactions.insert_one({**base, "id": str(uuid.uuid4()), "type": "teknisyen_borc", "amount": company_debt,
            "description": f"Şirkete Borç (%{pct:g} × {total_amount:.2f}₺) - {after['job_number']}"})

TECH_VIS_DEFAULT = {"enabled": True, "hide_from": "22:00", "show_from": "07:00", "done_days": 7}
ACTIVE_STATUSES = ("yeni", "atandi", "yolda", "basladi")

try:
    from zoneinfo import ZoneInfo
    _TR = ZoneInfo("Europe/Istanbul")
except Exception:
    _TR = timezone(timedelta(hours=3))

async def get_tech_vis() -> dict:
    s_ = await speed.cached_global(db)
    v = dict(TECH_VIS_DEFAULT)
    v.update(s_.get("tech_visibility") or {})
    return v

def _hm(x: str) -> int:
    try:
        h, m = x.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return 0

def tech_hidden_now(v: dict) -> bool:
    """Gece saatlerinde (varsayılan 22:00-07:00, İstanbul) usta müşteri verisini göremez."""
    if not v.get("enabled", True):
        return False
    now = datetime.now(_TR)
    cur = now.hour * 60 + now.minute
    a, b = _hm(v["hide_from"]), _hm(v["show_from"])
    return (cur >= a or cur < b) if a > b else (a <= cur < b)

def tech_job_visible(job: dict, v: dict) -> bool:
    if job.get("status") in ACTIVE_STATUSES:
        return True
    ref = job.get("reassigned_at") or job.get("completed_at") or job.get("updated_at") or ""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=int(v.get("done_days", 7)))).isoformat()
    return bool(ref) and ref >= cutoff

_JOB_CLOSED = ["tamamlandi", "faturalandi", "iptal"]


def _tr_norm(x):
    return (x or "").strip().replace("İ", "i").replace("I", "ı").lower().replace("i̇", "i")


def _tr_variants(q):
    q = (q or "").strip()
    out = {q, q.lower(), q.upper(), q.title(), _tr_norm(q)}
    t = q.replace("i", "İ").upper() if "i" in q else q.upper()
    out.add(t)
    out.add(q.replace("I", "ı").lower())
    return [re.escape(v) for v in out if v]


def _th_f(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def _th_hours(j):
    try:
        a = datetime.fromisoformat(str(j.get("created_at") or "").replace("Z", "+00:00"))
        b = datetime.fromisoformat(str(j.get("completed_at") or "").replace("Z", "+00:00"))
        h = (b - a).total_seconds() / 3600
        return h if 0 <= h < 24 * 60 else None
    except (ValueError, TypeError):
        return None


def _th_range(days, date_from, date_to):
    rng = {}
    if days:
        rng["$gte"] = (datetime.now(timezone.utc) - timedelta(days=min(int(days), 3650))).isoformat()
    if date_from:
        rng["$gte"] = date_from[:10]
    if date_to:
        rng["$lte"] = date_to[:10] + "T23:59:59"
    return rng


_TH_GRP = {"kombi": ["kombi"], "klima": ["klima"], "beyaz-esya": ["buzdolabi", "camasir-makinesi", "bulasik-makinesi", "kurutma-makinesi", "derin-dondurucu", "beyaz-esya"],
           "televizyon": ["televizyon", "tv"], "sofben": ["sofben"], "ocak-firin": ["ocak", "firin", "ankastre"], "diger": ["diger"]}


@api_router.get("/technicians-history")
async def technicians_history(days: int = 0, date_from: str = "", date_to: str = "", city: str = "", district: str = "", group: str = "",
                              device_type: str = "", brand: str = "", active: str = "", q: str = "", _: dict = Depends(require_admin)):
    """Usta başına iş geçmişi özeti: iş sayıları, ciro, tamamlama oranı, ortalama süre, puan, bakiye, son iş."""
    tq = {"role": "technician"}
    if active == "1":
        tq["is_active"] = {"$ne": False}
    elif active == "0":
        tq["is_active"] = False
    techs = await db.users.find(tq, {"_id": 0, "id": 1, "name": 1, "phone": 1, "is_active": 1, "profile": 1, "created_at": 1}).to_list(3000)
    wc, wd, wq = _tr_norm(city), _tr_norm(district), _tr_norm(q)
    def keep(t):
        pf = t.get("profile") or {}
        if wc and _tr_norm(pf.get("city")) != wc:
            return False
        if wd and wd not in [_tr_norm(x) for x in (pf.get("districts") or [])]:
            return False
        if group and group not in (pf.get("service_groups") or []):
            return False
        if wq and wq not in _tr_norm((t.get("name") or "") + " " + (pf.get("city") or "") + " " + " ".join(pf.get("districts") or [])):
            return False
        return True
    techs = [t for t in techs if keep(t)]
    ids = {t["id"] for t in techs}
    jq = {"assigned_technician_id": {"$in": list(ids) or ["-"]}}
    rng = _th_range(days, date_from, date_to)
    if rng:
        jq["created_at"] = rng
    if device_type:
        jq["device_type"] = device_type
    if brand:
        jq["device_brand_name"] = brand
    jobs, txs = await asyncio.gather(
        db.service_jobs.find(jq, {"_id": 0, "assigned_technician_id": 1, "status": 1, "created_at": 1, "completed_at": 1, "customer_rating": 1, "survey": 1, "total_amount": 1, "device_type": 1}).to_list(200000),
        db.cash_transactions.aggregate([{"$match": {"type": {"$in": ["teknisyen_borc", "teknisyen_odeme"]}}}, {"$group": {"_id": {"t": "$technician_id", "y": "$type"}, "s": {"$sum": "$amount"}}}]).to_list(20000))
    bal = {}
    for r in txs:
        k = r["_id"]["t"]
        bal[k] = bal.get(k, 0) + (r["s"] if r["_id"]["y"] == "teknisyen_borc" else -r["s"])
    ym = datetime.now(timezone.utc).isoformat()[:7]
    agg = {}
    for j in jobs:
        a = agg.setdefault(j["assigned_technician_id"], {"total": 0, "done": 0, "cancelled": 0, "open": 0, "month": 0, "last": "", "r": [], "rev": 0.0, "h": []})
        a["total"] += 1
        st = j.get("status")
        if st in ("tamamlandi", "faturalandi"):
            a["done"] += 1
            a["rev"] += _th_f(j.get("total_amount"))
            if (j.get("completed_at") or j.get("created_at") or "")[:7] == ym:
                a["month"] += 1
            h = _th_hours(j)
            if h is not None:
                a["h"].append(h)
        elif st == "iptal":
            a["cancelled"] += 1
        else:
            a["open"] += 1
        if (j.get("created_at") or "") > a["last"]:
            a["last"] = j.get("created_at") or ""
        r = j.get("customer_rating") or (j.get("survey") or {}).get("rating") or 0
        if r:
            a["r"].append(float(r))
    now = datetime.now(timezone.utc)
    rows = []
    for t in techs:
        a = agg.get(t["id"], {"total": 0, "done": 0, "cancelled": 0, "open": 0, "month": 0, "last": "", "r": [], "rev": 0.0, "h": []})
        pf = t.get("profile") or {}
        idle = None
        if a["last"]:
            try:
                idle = (now - datetime.fromisoformat(a["last"].replace("Z", "+00:00"))).days
            except ValueError:
                idle = None
        fin = a["done"] + a["cancelled"]
        rows.append({"id": t["id"], "name": t.get("name", ""), "phone": t.get("phone", ""), "is_active": t.get("is_active", True),
                     "city": pf.get("city", ""), "districts": pf.get("districts") or [], "groups": pf.get("service_groups") or [],
                     "place": " · ".join([x for x in [pf.get("city", ""), ", ".join((pf.get("districts") or [])[:2])] if x]),
                     "total": a["total"], "done": a["done"], "cancelled": a["cancelled"], "open": a["open"], "month": a["month"], "last": a["last"], "idle_days": idle,
                     "revenue": round(a["rev"], 2), "avg_ticket": round(a["rev"] / a["done"], 2) if a["done"] else 0,
                     "done_rate": round(100.0 * a["done"] / fin) if fin else None, "avg_hours": round(sum(a["h"]) / len(a["h"]), 1) if a["h"] else None,
                     "rating": round(sum(a["r"]) / len(a["r"]), 1) if a["r"] else 0, "rating_n": len(a["r"]), "balance": round(bal.get(t["id"], 0), 2), "created_at": t.get("created_at", "")})
    return rows


@api_router.get("/technicians-history/{tid}")
async def technician_history_detail(tid: str, days: int = 0, date_from: str = "", date_to: str = "", _: dict = Depends(require_admin)):
    """Tek usta: aylık dağılım, cihaz/marka/ilçe kırılımı, ödeme-borç hareketleri."""
    t = await db.users.find_one({"id": tid, "role": "technician"}, {"_id": 0, "password_hash": 0})
    if not t:
        raise HTTPException(status_code=404, detail="Usta bulunamadı")
    jq = {"assigned_technician_id": tid}
    rng = _th_range(days, date_from, date_to)
    if rng:
        jq["created_at"] = rng
    jobs, txs, note, custs = await asyncio.gather(
        db.service_jobs.find(jq, {"_id": 0, "status": 1, "created_at": 1, "completed_at": 1, "total_amount": 1, "device_type": 1, "device_brand_name": 1, "customer_id": 1, "customer_rating": 1, "survey": 1}).to_list(100000),
        db.cash_transactions.find({"technician_id": tid, "type": {"$in": ["teknisyen_borc", "teknisyen_odeme", "teknisyen_prim"]}}, {"_id": 0}).sort("date", -1).to_list(300),
        db.technician_notes.find_one({"tech_id": tid}, {"_id": 0}),
        asyncio.sleep(0, result=[]))
    cids = list({j.get("customer_id") for j in jobs if j.get("customer_id")})
    custs = await db.customers.find({"id": {"$in": cids}}, {"_id": 0, "id": 1, "city": 1, "district": 1}).to_list(100000) if cids else []
    cm = {c["id"]: c for c in custs}
    months, dev, brd, dst = {}, {}, {}, {}
    st = {}
    for j in jobs:
        st[j.get("status")] = st.get(j.get("status"), 0) + 1
        done = j.get("status") in ("tamamlandi", "faturalandi")
        m = ((j.get("completed_at") if done else j.get("created_at")) or j.get("created_at") or "")[:7]
        if m:
            e = months.setdefault(m, {"month": m, "done": 0, "total": 0, "revenue": 0.0})
            e["total"] += 1
            if done:
                e["done"] += 1
                e["revenue"] += _th_f(j.get("total_amount"))
        for dct, key in ((dev, j.get("device_type")), (brd, j.get("device_brand_name"))):
            if key:
                dct[key] = dct.get(key, 0) + 1
        c = cm.get(j.get("customer_id")) or {}
        k = " / ".join([x for x in [c.get("city"), c.get("district")] if x])
        if k:
            dst[k] = dst.get(k, 0) + 1
    top = lambda d, n=8: sorted([{"name": k, "count": v} for k, v in d.items()], key=lambda x: -x["count"])[:n]
    ml = sorted(months.values(), key=lambda x: x["month"])[-12:]
    for e in ml:
        e["revenue"] = round(e["revenue"], 2)
    tb = sum(x["amount"] for x in txs if x["type"] == "teknisyen_borc")
    tp = sum(x["amount"] for x in txs if x["type"] == "teknisyen_odeme")
    return {"id": tid, "name": t.get("name", ""), "phone": t.get("phone", ""), "email": t.get("email", ""), "is_active": t.get("is_active", True), "profile": t.get("profile") or {},
            "commission_percent": t.get("commission_percent", 0), "note": (note or {}).get("note", ""), "created_at": t.get("created_at", ""), "status_counts": st,
            "months": ml, "devices": top(dev), "brands": top(brd), "districts": top(dst), "debt_total": round(tb, 2), "paid_total": round(tp, 2), "balance": round(tb - tp, 2),
            "cash": [{"type": x["type"], "amount": x["amount"], "date": x.get("date", ""), "description": x.get("description", "")} for x in txs[:60]]}


@api_router.get("/technicians-history/{tid}/jobs")
async def technician_history_jobs(tid: str, page: int = 1, limit: int = 25, status: str = "", device_type: str = "", brand: str = "", q: str = "",
                                  days: int = 0, date_from: str = "", date_to: str = "", export: bool = False, _: dict = Depends(require_admin)):
    """Ustanın iş listesi (sunucu tarafı filtre + sayfalama)."""
    jq = {"assigned_technician_id": tid}
    if status == "done":
        jq["status"] = {"$in": ["tamamlandi", "faturalandi"]}
    elif status == "open":
        jq["status"] = {"$nin": _JOB_CLOSED}
    elif status:
        jq["status"] = status
    if device_type:
        jq["device_type"] = device_type
    if brand:
        jq["device_brand_name"] = brand
    rng = _th_range(days, date_from, date_to)
    if rng:
        jq["created_at"] = rng
    if q.strip():
        rx = {"$regex": "|".join(_tr_variants(q.strip()[:60]))}
        jq["$and"] = [{"$or": [{f: rx} for f in ("job_number", "customer_name", "customer_phone", "customer_address", "fault_description", "device_model")]}]
    limit = max(5, min(limit, 5000 if export else 100))
    if export:
        page = 1
    total = await db.service_jobs.count_documents(jq)
    rows = await db.service_jobs.find(jq, {"_id": 0, "id": 1, "job_number": 1, "created_at": 1, "completed_at": 1, "scheduled_at": 1, "customer_name": 1, "customer_phone": 1, "customer_address": 1,
                                           "device_type": 1, "device_brand_name": 1, "device_model": 1, "fault_description": 1, "status": 1, "total_amount": 1}).sort("created_at", -1).skip((max(1, page) - 1) * limit).limit(limit).to_list(limit)
    return {"total": total, "page": page, "limit": limit, "rows": rows}


@api_router.get("/jobs/meta")
async def jobs_meta(days: int = 15, user: dict = Depends(require_admin)):
    """Servis kayıtları listesi için özet: toplam / son N gün / eski açık kayıt sayısı + filtre seçenekleri."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 3650)))).isoformat()
    total, recent, old_open, brands, types = await asyncio.gather(
        db.service_jobs.count_documents({}),
        db.service_jobs.count_documents({"created_at": {"$gte": cutoff}}),
        db.service_jobs.count_documents({"created_at": {"$lt": cutoff}, "status": {"$nin": _JOB_CLOSED}}),
        db.service_jobs.distinct("device_brand_name"),
        db.service_jobs.distinct("device_type"),
    )
    return {"total": total, "recent": recent, "older": max(0, total - recent), "old_open": old_open, "days": days,
            "brands": sorted([b for b in brands if b], key=lambda x: x.lower())[:300], "types": sorted([t for t in types if t])[:50]}


@api_router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    technician_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    days: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    keep_open: bool = True,
    city: Optional[str] = None,
    district: Optional[str] = None,
    device_type: Optional[str] = None,
    brand: Optional[str] = None,
    q: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    await fieldops.backfill(db)
    query = {}
    if user["role"] != "technician":
        ands = []
        if q and q.strip():                               # arama: tüm tarihlerde
            rx = {"$regex": "|".join(_tr_variants(q.strip()[:60]))}
            ands.append({"$or": [{f: rx} for f in ("job_number", "customer_name", "customer_phone", "customer_address", "fault_description", "device_model", "device_serial", "device_brand_name")]})
        elif days or date_from or date_to:
            rng = {}
            if days:
                rng["$gte"] = (datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 3650)))).isoformat()
            if date_from:
                rng["$gte"] = date_from[:10]
            if date_to:
                rng["$lte"] = date_to[:10] + "T23:59:59"
            ands.append({"$or": [{"created_at": rng}, {"status": {"$nin": _JOB_CLOSED}}]} if (keep_open and days and not date_from and not date_to) else {"created_at": rng})
        if device_type:
            ands.append({"device_type": device_type})
        if brand:
            ands.append({"device_brand_name": brand})
        if city or district:
            cq = {}
            cs = await db.customers.find({}, {"_id": 0, "id": 1, "city": 1, "district": 1}).to_list(200000)
            wc, wd = _tr_norm(city), _tr_norm(district)
            ids = [c["id"] for c in cs if (not wc or _tr_norm(c.get("city")) == wc) and (not wd or _tr_norm(c.get("district")) == wd)]
            ands.append({"customer_id": {"$in": ids}})
        if ands:
            query["$and"] = ands
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    # Technicians only see their own jobs + tamamlanan kayıtlar 7 gün sonra gizlenir
    if user["role"] == "technician":
        vis = await get_tech_vis()
        if tech_hidden_now(vis):
            return []
        query["assigned_technician_id"] = user["id"]
        if user.get("fu"):
            query["assigned_to_fu"] = user["fu"]
        cutoff = (datetime.now(timezone.utc) - timedelta(days=int(vis.get("done_days", 7)))).isoformat()
        # Aktif işler her zaman; kapalı/iptal işler yalnızca son N gün (tekrar atama da süreyi yeniler)
        query["$or"] = [
            {"status": {"$in": list(ACTIVE_STATUSES)}},
            {"$and": [
                {"status": {"$in": ["tamamlandi", "faturalandi", "iptal"]}},
                {"$or": [{"completed_at": {"$gte": cutoff}}, {"reassigned_at": {"$gte": cutoff}}]}
            ]}
        ]
    elif technician_id:
        query["assigned_technician_id"] = technician_id
    _proj = {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}
    try:
        rows = await db.service_jobs.find(query, _proj).sort("created_at", -1).to_list(2000)
    except Exception:                                    # noqa: BLE001  (sıralama bellek sınırı vb.) → sırasız çek, Python'da sırala
        rows = await db.service_jobs.find(query, _proj).to_list(20000)
        rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        rows = rows[:2000]
    if user["role"] == "technician" and (await fieldops.get_privacy_settings(db))["mode"] != "off":
        rows = [fieldops.mask_job(r) for r in rows]
    return rows

@api_router.post("/jobs")
async def create_job(payload: ServiceJobCreate, user: dict = Depends(get_current_user)):
    if tenant.current() and user.get("role") == "technician" and not payload.assigned_technician_id:
        payload.assigned_technician_id = user["id"]                       # firma kendi açtığı işi kendisine atar (Atandı)
    customer = await db.customers.find_one({"id": payload.customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    device = None
    if payload.device_id:
        device = await db.devices.find_one({"id": payload.device_id}, {"_id": 0})
    technician = None
    if payload.assigned_technician_id:
        technician = await db.users.find_one({"id": payload.assigned_technician_id}, {"_id": 0, "password_hash": 0})

    job_no = await next_job_number()
    doc = {
        "id": str(uuid.uuid4()),
        "job_number": job_no,
        "customer_id": customer["id"],
        "customer_name": customer["name"],
        "customer_phone": customer["phone"],
        "customer_address": f'{customer.get("address","")} {customer.get("district","")} {customer.get("city","")}'.strip(),
        "device_id": device["id"] if device else "",
        "device_brand_id": device.get("brand_id", "") if device else "",
        "device_brand_name": device.get("brand_name", "") if device else "",
        "device_brand_logo": device.get("brand_logo", "") if device else "",
        "device_model": device.get("model", "") if device else "",
        "device_type": device.get("type", "") if device else "",
        "device_serial": device.get("serial_no", "") if device else "",
        "fault_description": payload.fault_description,
        "scheduled_at": payload.scheduled_at or "",
        "priority": payload.priority,
        "assigned_technician_id": payload.assigned_technician_id or "",
        "assigned_to_fu": (user.get("fu") or "") if tenant.current() else "",
        "assigned_technician_name": technician["name"] if technician else "",
        "technician_commission_percent": float(technician.get("commission_percent", 0)) if technician else 0.0,
        "status": "atandi" if payload.assigned_technician_id else "yeni",
        "work_done": "",
        "parts_used": [],
        "labor_fee": 0.0,
        "parts_total": 0.0,
        "total_amount": 0.0,
        "technician_commission_amount": 0.0,
        "photos_before": [],
        "photos_after": [],
        "signature_url": "",
        "tech_signature_url": "",
        "pdf_note": "",
        "cancel_reason": "",
        "customer_rating": 0,
        "source_channel": payload.source_channel or customer.get("source_channel", "") or "",
        "source_detail": payload.source_detail or "",
        "started_at": "",
        "completed_at": "",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "created_by": user["id"]
    }
    if doc["assigned_technician_id"]:
        doc.update(await fieldops.sla_fields(db))
    await db.service_jobs.insert_one(doc)
    doc.pop("_id", None)
    if doc["assigned_technician_id"]:
        asyncio.create_task(fieldops.push_to(db, [doc["assigned_technician_id"]], "Yeni iş atandı", f'{doc["job_number"]} · {doc["customer_name"]}', f'/tech/jobs/{doc["id"]}'))
        asyncio.create_task(_assigned_msg(doc))
    elif doc["status"] == "yeni":
        asyncio.create_task(ops2.auto_assign(db, doc["id"], _assign_job))
    return doc

@api_router.get("/jobs/{job_id}")
async def get_job(job_id: str, user: dict = Depends(get_current_user)):
    job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Servis kaydı bulunamadı")
    if user["role"] == "technician":
        if job.get("assigned_technician_id") != user["id"] or (user.get("fu") and job.get("assigned_to_fu") != user["fu"]):
            raise HTTPException(status_code=403, detail="Bu kayda erişim yetkiniz yok")
        vis = await get_tech_vis()
        if tech_hidden_now(vis):
            raise HTTPException(status_code=403, detail=f"İş kayıtları {vis['hide_from']}–{vis['show_from']} arasında gizlidir")
        if not tech_job_visible(job, vis):
            raise HTTPException(status_code=403, detail="Bu kayıt süresi dolduğu için ekranınızdan kaldırıldı")
        if (await fieldops.get_privacy_settings(db))["mode"] != "off":
            return fieldops.mask_job(_enrich_logo(job))
    return _enrich_logo(job)

@api_router.put("/jobs/{job_id}")
async def update_job(job_id: str, payload: ServiceJobUpdate, user: dict = Depends(get_current_user)):
    job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Servis kaydı bulunamadı")
    if user["role"] == "technician":
        if job.get("assigned_technician_id") != user["id"] or (user.get("fu") and job.get("assigned_to_fu") != user["fu"]):
            raise HTTPException(status_code=403, detail="Bu kayda erişim yetkiniz yok")
        vis = await get_tech_vis()
        if tech_hidden_now(vis):
            raise HTTPException(status_code=403, detail=f"İş kayıtları {vis['hide_from']}–{vis['show_from']} arasında gizlidir")
        if job.get("status") in ("tamamlandi", "faturalandi", "iptal"):
            raise HTTPException(status_code=403, detail="Tamamlanan iş düzenlenemez. Düzeltme için yöneticiyle iletişime geçin.")

    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    ADMIN_ONLY = ("customer_name", "customer_phone", "customer_address", "device_brand_name", "device_model",
                  "device_type", "device_serial", "source_detail", "created_at", "completed_at", "manual_total",
                  "assigned_technician_id", "priority", "scheduled_at", "source_channel", "tech_note")
    if user["role"] != "admin":
        for k in ADMIN_ONLY:
            update.pop(k, None)
    if "tech_note" in update:
        update["tech_note"] = str(update["tech_note"]).strip()[:1000]
        update["tech_note_at"] = now_iso()
        update["tech_note_by"] = user.get("name", "")
    if "manual_total" in update:
        mt = float(update.pop("manual_total"))
        pt = float(update.get("parts_total", job.get("parts_total", 0)) or 0)
        if "parts_used" in update:
            pt = sum(float(p.get("qty", 1)) * float(p.get("unit_price", 0)) for p in update["parts_used"])
        update["labor_fee"] = round(max(0.0, mt - pt), 2)

    # Handle technician assignment change (admin only)
    if "assigned_technician_id" in update and user["role"] == "admin":
        if update["assigned_technician_id"]:
            tech = await db.users.find_one({"id": update["assigned_technician_id"]}, {"_id": 0, "password_hash": 0})
            if tech:
                update["assigned_technician_name"] = tech["name"]
                update["technician_commission_percent"] = float(tech.get("commission_percent", 0))
                if job.get("status") == "yeni":
                    update["status"] = "atandi"
                if update["assigned_technician_id"] != job.get("assigned_technician_id"):
                    update.update(await fieldops.sla_fields(db))

    # Status change side effects
    if "status" in update:
        new_status = update["status"]
        if new_status == "basladi" and not job.get("started_at"):
            update["started_at"] = now_iso()
        if new_status == "yolda" and not job.get("on_the_way_at"):
            update["on_the_way_at"] = now_iso()
        if new_status in DONE_STATUSES and user["role"] == "technician" and job.get("status") not in DONE_STATUSES:
            miss = await ops2.checklist_missing(db, job)
            if miss:
                raise HTTPException(status_code=400, detail="Kontrol listesinde işaretlenmemiş zorunlu madde var: " + "; ".join(miss[:4]))
        if new_status in DONE_STATUSES and not job.get("completed_at"):
            update["completed_at"] = now_iso()

    # Recalculate parts/totals
    if update.get("parts_none") is True:
        update["parts_used"] = []
    elif update.get("parts_used"):
        update["parts_none"] = False
    if "parts_used" in update:
        for p in update["parts_used"]:
            p["qty"] = max(0.0, float(p.get("qty", 1) or 0))
            p["unit_price"] = max(0.0, float(p.get("unit_price", 0) or 0))
            p["total"] = round(p["qty"] * p["unit_price"], 2)
            sp = await db.spare_parts.find_one({"id": p["part_id"]}, {"_id": 0}) if p.get("part_id") else None
            if sp:  # stoktan seçilen: liste fiyatı ve maliyet sunucudan gelir, usta fiyatı değiştirebilir
                p["list_price"] = float(sp.get("price", 0) or 0)
                p["unit_cost"] = float(sp.get("cost", 0) or 0)
                p["price_changed"] = abs(p["unit_price"] - p["list_price"]) > 0.005
            else:   # manuel parça: maliyeti yalnızca yönetici girebilir
                p["list_price"] = 0.0
                p["price_changed"] = False
                if user["role"] != "admin":
                    p["unit_cost"] = 0.0
        update["parts_total"] = sum(p["total"] for p in update["parts_used"])
        update["parts_cost"] = round(sum(p["qty"] * float(p.get("unit_cost", 0) or 0) for p in update["parts_used"]), 2)

    parts_total = update.get("parts_total", job.get("parts_total", 0))
    labor_fee = update.get("labor_fee", job.get("labor_fee", 0))
    if "parts_used" in update or "labor_fee" in update:
        update["total_amount"] = max(0.0, float(parts_total) + float(labor_fee) - float(job.get("discount_amount", 0) or 0))
        commission_pct = update.get("technician_commission_percent", job.get("technician_commission_percent", 0))
        # YENİ MANTIK: commission_percent = teknisyenin şirkete borç oranı
        # company_debt = total × oran / 100  (teknisyenin şirkete vereceği)
        # tech_keeps   = total - company_debt  (teknisyenin cebine kalan)
        company_debt = round(float(update["total_amount"]) * float(commission_pct) / 100.0, 2)
        update["technician_commission_amount"] = round(float(update["total_amount"]) - company_debt, 2)

    await servis_ayar.enforce(db, job, update, user)       # firma ayarları: foto / imza / kapalı adım kuralları
    update["updated_at"] = now_iso()
    await db.service_jobs.update_one({"id": job_id}, {"$set": update})

    updated = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})

    # Usta bildirimi en başta ve arka planda gitsin (kasa/stok senkronunu beklemesin)
    if updated.get("assigned_technician_id") and updated.get("assigned_technician_id") != job.get("assigned_technician_id"):
        asyncio.create_task(fieldops.push_to(db, [updated["assigned_technician_id"]], "Yeni iş atandı", f'{updated.get("job_number", "")} · {updated.get("customer_name", "")}', f'/tech/jobs/{updated["id"]}'))

    # Stok + kasa defterini iş durumuna göre senkronize et
    await sync_job_ledger(job, updated, user)

    # Müşteriye otomatik mesaj (ayar açıksa)
    if updated.get("assigned_technician_id") and updated.get("assigned_technician_id") != job.get("assigned_technician_id"):
        asyncio.create_task(_assigned_msg(updated))
    if updated.get("status") in DONE_STATUSES and job.get("status") not in DONE_STATUSES:
        asyncio.create_task(notify.job_event(db, "done", updated))

    return _enrich_logo(updated)

async def _assigned_msg(job):
    try:
        await notify.job_event(db, "assigned", await _with_token(job))
        await notify.technician_event(db, job)
    except Exception:                                   # noqa: BLE001
        pass

async def _with_token(job):
    if not job.get("track_token"):
        tok = secrets.token_urlsafe(16)
        await db.service_jobs.update_one({"id": job["id"]}, {"$set": {"track_token": tok}})
        job = {**job, "track_token": tok}
    return job

@api_router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, _: dict = Depends(require_admin)):
    # Kasa kayıtlarını ve stok düşümünü de geri al
    job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Servis kaydı bulunamadı")
    if job.get("status") in DONE_STATUSES:
        await _adjust_stock(job.get("parts_used"), +1)
    deleted_tx = await db.cash_transactions.delete_many({"job_id": job_id})
    await db.service_jobs.delete_one({"id": job_id})
    return {"ok": True, "reverted_cash_transactions": deleted_tx.deleted_count}

@api_router.post("/jobs/{job_id}/reassign")
async def reassign_job(job_id: str, payload: dict, user: dict = Depends(get_current_user)):
    """Arızayı tekrar atama: müşteride aynı arıza tekrarladığında veya farklı teknisyene devretmek için."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Yalnızca yönetici tekrar atama yapabilir")
    job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Servis kaydı bulunamadı")
    new_tech_id = payload.get("technician_id", "")
    note = payload.get("note", "")
    keep_history = payload.get("keep_history", True)
    if not new_tech_id:
        raise HTTPException(status_code=400, detail="Teknisyen seçimi zorunlu")
    tech = await db.users.find_one({"id": new_tech_id, "role": "technician"}, {"_id": 0, "password_hash": 0})
    if not tech:
        raise HTTPException(status_code=404, detail="Teknisyen bulunamadı")
    if keep_history:
        # Yeni iş emri oluştur — tekrar arıza
        new_job = dict(job)
        new_job["id"] = str(uuid.uuid4())
        new_job["job_number"] = await next_job_number()
        new_job["assigned_technician_id"] = new_tech_id
        new_job["assigned_technician_name"] = tech["name"]
        new_job["technician_commission_percent"] = float(tech.get("commission_percent", 0))
        new_job["status"] = "atandi"
        new_job["work_done"] = ""
        new_job["parts_used"] = []
        new_job["labor_fee"] = 0.0
        new_job["parts_total"] = 0.0
        new_job["total_amount"] = 0.0
        new_job["technician_commission_amount"] = 0.0
        new_job["photos_before"] = []
        new_job["photos_after"] = []
        new_job["signature_url"] = ""
        new_job["tech_signature_url"] = ""
        new_job["pdf_note"] = ""
        new_job["cancel_reason"] = ""
        new_job["started_at"] = ""
        new_job["completed_at"] = ""
        new_job["created_at"] = now_iso()
        new_job["updated_at"] = now_iso()
        new_job["created_by"] = user["id"]
        new_job["reassigned_at"] = now_iso()
        new_job.update(await fieldops.sla_fields(db))
        new_job.pop("calls", None)
        new_job["original_job_id"] = job["id"]
        new_job["original_job_number"] = job["job_number"]
        new_job["fault_description"] = (note + " | " if note else "") + f"[Tekrar arıza — Önceki: {job['job_number']}] " + (job.get("fault_description") or "")
        await db.service_jobs.insert_one(new_job)
        new_job.pop("_id", None)
        return new_job
    else:
        # Mevcut işi yeni teknisyene devret
        await db.service_jobs.update_one({"id": job_id}, {"$set": {
            "assigned_technician_id": new_tech_id,
            "assigned_technician_name": tech["name"],
            "technician_commission_percent": float(tech.get("commission_percent", 0)),
            "status": "atandi",
            "completed_at": "",
            "reassigned_at": now_iso(),
            "reassign_note": note,
            "updated_at": now_iso(),
            **(await fieldops.sla_fields(db)),
        }})
        updated = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        await sync_job_ledger(job, updated, user)   # tamamlanmışsa gelir/borç/stok geri alınır
        return updated

@api_router.post("/jobs/quick")
async def quick_create_job(payload: dict, user: dict = Depends(get_current_user)):
    """Yeni müşteri + cihaz + iş emrini tek atışta oluşturur."""
    # 1. Müşteri (varsa kullan, yoksa oluştur)
    customer_id = payload.get("customer_id", "")
    if not customer_id:
        cname = (payload.get("customer_name") or "").strip()
        cphone = (payload.get("customer_phone") or "").strip()
        if not cname or not cphone:
            raise HTTPException(status_code=400, detail="Müşteri adı ve telefon zorunlu")
        try:
            cphone = tr_phone(cphone, True)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        new_cust = {
            "id": str(uuid.uuid4()),
            "name": cname,
            "phone": cphone,
            "email": payload.get("customer_email", ""),
            "address": payload.get("customer_address", ""),
            "city": payload.get("customer_city", ""),
            "district": payload.get("customer_district", ""),
            "notes": "",
            "source_channel": payload.get("source_channel", ""),
            "created_at": now_iso()
        }
        await db.customers.insert_one(new_cust)
        customer_id = new_cust["id"]
        customer = new_cust
    else:
        customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
        if not customer:
            raise HTTPException(status_code=404, detail="Müşteri bulunamadı")

    # 2. Cihaz (varsa kullan, marka/model verildiyse oluştur)
    device = None
    device_id = payload.get("device_id", "")
    brand_id = payload.get("brand_id", "")
    if device_id:
        device = await db.devices.find_one({"id": device_id}, {"_id": 0})
    elif brand_id:
        brand = await db.brands.find_one({"id": brand_id}, {"_id": 0})
        if not brand:
            raise HTTPException(status_code=404, detail="Marka bulunamadı")
        device = {
            "id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "brand_id": brand_id,
            "brand_name": brand["name"],
            "brand_logo": brand.get("logo_url", ""),
            "type": payload.get("device_type", "kombi"),
            "model": payload.get("device_model", ""),
            "serial_no": payload.get("device_serial", ""),
            "install_date": "",
            "warranty_until": payload.get("warranty_until", ""),
            "notes": "",
            "created_at": now_iso()
        }
        await db.devices.insert_one(device)

    # 3. Teknisyen
    technician = None
    tech_id = payload.get("assigned_technician_id", "")
    if tech_id:
        technician = await db.users.find_one({"id": tech_id, "role": "technician"}, {"_id": 0, "password_hash": 0})

    # 4. Servis kaydı
    job_no = await next_job_number()
    job = {
        "id": str(uuid.uuid4()),
        "job_number": job_no,
        "customer_id": customer["id"],
        "customer_name": customer["name"],
        "customer_phone": customer["phone"],
        "customer_address": f'{customer.get("address","")} {customer.get("district","")} {customer.get("city","")}'.strip(),
        "device_id": device["id"] if device else "",
        "device_brand_id": device.get("brand_id", "") if device else "",
        "device_brand_name": device.get("brand_name", "") if device else "",
        "device_brand_logo": device.get("brand_logo", "") if device else "",
        "device_model": device.get("model", "") if device else "",
        "device_type": device.get("type", "") if device else "",
        "device_serial": device.get("serial_no", "") if device else "",
        "fault_description": payload.get("fault_description", ""),
        "scheduled_at": payload.get("scheduled_at", ""),
        "priority": payload.get("priority", "normal"),
        "assigned_technician_id": tech_id,
        "assigned_technician_name": technician["name"] if technician else "",
        "technician_commission_percent": float(technician.get("commission_percent", 0)) if technician else 0.0,
        "status": "atandi" if tech_id else "yeni",
        "work_done": "",
        "parts_used": [],
        "labor_fee": 0.0,
        "parts_total": 0.0,
        "total_amount": 0.0,
        "technician_commission_amount": 0.0,
        "photos_before": [],
        "photos_after": [],
        "signature_url": "",
        "tech_signature_url": "",
        "pdf_note": "",
        "cancel_reason": "",
        "customer_rating": 0,
        "source_channel": payload.get("source_channel", "") or customer.get("source_channel", "") or "",
        "source_detail": payload.get("source_detail", ""),
        "started_at": "",
        "completed_at": "",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "created_by": user["id"]
    }
    if job["assigned_technician_id"]:
        job.update(await fieldops.sla_fields(db))
    await db.service_jobs.insert_one(job)
    job.pop("_id", None)
    if job["assigned_technician_id"]:
        # Kayıt sırasında usta seçildiyse de bildirim ve mesaj gitsin (create_job ile aynı davranış)
        asyncio.create_task(fieldops.push_to(db, [job["assigned_technician_id"]], "Yeni iş atandı", f'{job["job_number"]} · {job["customer_name"]}', f'/tech/jobs/{job["id"]}'))
        asyncio.create_task(_assigned_msg(job))
    elif job["status"] == "yeni":
        asyncio.create_task(ops2.auto_assign(db, job["id"], _assign_job))
    return job

# -------------------------- Spare Parts --------------------------
@api_router.get("/parts")
async def list_parts(_: dict = Depends(get_current_user)):
    return await db.spare_parts.find({}, {"_id": 0}).sort("name", 1).to_list(2000)

@api_router.post("/parts")
async def create_part(payload: SparePartCreate, _: dict = Depends(require_admin)):
    doc = payload.model_dump()
    doc["id"] = str(uuid.uuid4())
    doc["created_at"] = now_iso()
    await db.spare_parts.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.put("/parts/{part_id}")
async def update_part(part_id: str, payload: SparePartUpdate, _: dict = Depends(require_admin)):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    res = await db.spare_parts.update_one({"id": part_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Yedek parça bulunamadı")
    return await db.spare_parts.find_one({"id": part_id}, {"_id": 0})

@api_router.delete("/parts/{part_id}")
async def delete_part(part_id: str, _: dict = Depends(require_admin)):
    await db.spare_parts.delete_one({"id": part_id})
    return {"ok": True}

# -------------------------- Appointments --------------------------
@api_router.get("/appointments")
async def list_appointments(user: dict = Depends(get_current_user)):
    query = {}
    if user["role"] == "technician":
        query["technician_id"] = user["id"]
    return await db.appointments.find(query, {"_id": 0}).sort("start_at", 1).to_list(1000)

@api_router.post("/appointments")
async def create_appointment(payload: AppointmentCreate, user: dict = Depends(get_current_user)):
    doc = payload.model_dump()
    doc["id"] = str(uuid.uuid4())
    doc["status"] = "planlandi"
    doc["created_at"] = now_iso()
    if doc.get("customer_id"):
        c = await db.customers.find_one({"id": doc["customer_id"]}, {"_id": 0})
        if c:
            doc["customer_name"] = c["name"]
    if doc.get("technician_id"):
        t = await db.users.find_one({"id": doc["technician_id"]}, {"_id": 0})
        if t:
            doc["technician_name"] = t["name"]
    await db.appointments.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.put("/appointments/{apt_id}")
async def update_appointment(apt_id: str, payload: dict, user: dict = Depends(get_current_user)):
    allowed = {"title", "customer_id", "technician_id", "start_at", "end_at", "notes", "status", "related_job_id"}
    upd = {k: v for k, v in payload.items() if k in allowed}
    if user["role"] == "technician":
        apt = await db.appointments.find_one({"id": apt_id}, {"_id": 0})
        if not apt or apt.get("technician_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Yetkisiz")
    if upd.get("customer_id"):
        c = await db.customers.find_one({"id": upd["customer_id"]}, {"_id": 0})
        upd["customer_name"] = c["name"] if c else ""
    if "customer_id" in upd and not upd["customer_id"]:
        upd["customer_name"] = ""
    if upd.get("technician_id"):
        t = await db.users.find_one({"id": upd["technician_id"]}, {"_id": 0})
        upd["technician_name"] = t["name"] if t else ""
    if "technician_id" in upd and not upd["technician_id"]:
        upd["technician_name"] = ""
    res = await db.appointments.update_one({"id": apt_id}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Randevu bulunamadı")
    return await db.appointments.find_one({"id": apt_id}, {"_id": 0})

@api_router.delete("/appointments/{apt_id}")
async def delete_appointment(apt_id: str, _: dict = Depends(get_current_user)):
    await db.appointments.delete_one({"id": apt_id})
    return {"ok": True}

# -------------------------- Cash / Accounting --------------------------
def _day_bounds(date_from: Optional[str], date_to: Optional[str]):
    """'YYYY-MM-DD' (TR saati) -> UTC iso aralığı."""
    tr = timezone(timedelta(hours=3))
    lo = hi = None
    try:
        if date_from:
            lo = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=tr).astimezone(timezone.utc).isoformat()
        if date_to:
            hi = (datetime.strptime(date_to, "%Y-%m-%d").replace(tzinfo=tr) + timedelta(days=1)).astimezone(timezone.utc).isoformat()
    except ValueError:
        raise HTTPException(status_code=400, detail="Tarih biçimi YYYY-AA-GG olmalı")
    return lo, hi

def _date_query(field: str, date_from: Optional[str], date_to: Optional[str]) -> dict:
    lo, hi = _day_bounds(date_from, date_to)
    q = {}
    if lo:
        q["$gte"] = lo
    if hi:
        q["$lt"] = hi
    return {field: q} if q else {}

@api_router.get("/cash/transactions")
async def list_cash(date_from: Optional[str] = None, date_to: Optional[str] = None, type: Optional[str] = None,
                    technician_id: Optional[str] = None, _: dict = Depends(require_admin)):
    query = _date_query("date", date_from, date_to)
    if type:
        query["type"] = type
    if technician_id:
        query["technician_id"] = technician_id
    return await db.cash_transactions.find(query, {"_id": 0}).sort("date", -1).to_list(20000)

@api_router.get("/cash/orphans")
async def cash_orphans(_: dict = Depends(require_admin)):
    """Teknisyen türünde olup ustası seçilmemiş (bu yüzden usta bakiyesine işlemeyen) hareketler."""
    return await db.cash_transactions.find({"type": {"$in": ["teknisyen_odeme", "teknisyen_borc", "teknisyen_prim"]}, "$or": [{"technician_id": ""}, {"technician_id": None}, {"technician_id": {"$exists": False}}]}, {"_id": 0}).sort("date", -1).to_list(500)

@api_router.put("/cash/transactions/{tx_id}")
async def update_cash(tx_id: str, payload: dict, _: dict = Depends(require_admin)):
    tx = await db.cash_transactions.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Hareket bulunamadı")
    if tx.get("job_id"):
        raise HTTPException(status_code=400, detail="Servis kaydından oluşan hareket doğrudan düzenlenemez; servis kaydını düzenleyin.")
    upd = {k: v for k, v in payload.items() if k in ("amount", "description", "date", "technician_id", "type", "account_id", "category", "payment_method", "party", "staff_id", "receipt_no", "vat_rate", "has_invoice", "invoice_no")}
    if "amount" in upd:
        try:
            upd["amount"] = float(upd["amount"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Geçersiz tutar")
        if upd["amount"] <= 0:
            raise HTTPException(status_code=400, detail="Tutar sıfırdan büyük olmalı")
    if "type" in upd and upd["type"] not in ("gelir", "gider", "teknisyen_odeme", "teknisyen_borc", "teknisyen_prim", "manuel"):
        raise HTTPException(status_code=400, detail="Geçersiz tip")
    fin_t, fin_tid = upd.get("type", tx.get("type")), upd.get("technician_id", tx.get("technician_id"))
    if str(fin_t).startswith("teknisyen_") and not (fin_tid or "").strip():
        raise HTTPException(status_code=400, detail="Teknisyen seçilmedi: usta bakiyesine işlenmesi için teknisyeni seçin.")
    await db.cash_transactions.update_one({"id": tx_id}, {"$set": upd})
    return await db.cash_transactions.find_one({"id": tx_id}, {"_id": 0})

@api_router.delete("/cash/transactions/{tx_id}")
async def delete_cash(tx_id: str, _: dict = Depends(require_admin)):
    tx = await db.cash_transactions.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Hareket bulunamadı")
    if tx.get("job_id"):
        raise HTTPException(status_code=400, detail="Servis kaydından oluşan hareket silinemez; servis kaydını düzenleyin veya silin.")
    await db.cash_transactions.delete_one({"id": tx_id})
    return {"ok": True}

@api_router.post("/cash/transactions")
async def create_cash(payload: CashTxCreate, user: dict = Depends(require_admin)):
    doc = payload.model_dump()
    if doc["type"].startswith("teknisyen_"):
        if not (doc.get("technician_id") or "").strip():
            raise HTTPException(status_code=400, detail="Teknisyen seçilmedi: usta bakiyesine işlenmesi için önce teknisyeni seçin.")
        if not await db.users.find_one({"id": doc["technician_id"], "role": "technician"}, {"_id": 1}):
            raise HTTPException(status_code=400, detail="Seçilen teknisyen bulunamadı")
    doc["id"] = str(uuid.uuid4())
    doc["date"] = doc.get("date") or now_iso()
    doc["created_by"] = user["id"]
    await db.cash_transactions.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.get("/cash/summary")
async def cash_summary(date_from: Optional[str] = None, date_to: Optional[str] = None, _: dict = Depends(require_admin)):
    txs = await db.cash_transactions.find(_date_query("date", date_from, date_to), {"_id": 0}).to_list(50000)
    income = sum(t["amount"] for t in txs if t["type"] == "gelir")
    expense = sum(t["amount"] for t in txs if t["type"] == "gider")
    tech_commission = sum(t["amount"] for t in txs if t["type"] == "teknisyen_prim")
    tech_debt = sum(t["amount"] for t in txs if t["type"] == "teknisyen_borc")
    tech_paid = sum(t["amount"] for t in txs if t["type"] == "teknisyen_odeme")
    technicians = await db.users.find({"role": "technician"}, {"_id": 0, "password_hash": 0}).to_list(500)
    tech_balances = []
    all_txs = txs if not (date_from or date_to) else await db.cash_transactions.find({}, {"_id": 0}).to_list(100000)
    for t in technicians:
        debt = sum(x["amount"] for x in all_txs if x["type"] == "teknisyen_borc" and x.get("technician_id") == t["id"])
        paid = sum(x["amount"] for x in all_txs if x["type"] == "teknisyen_odeme" and x.get("technician_id") == t["id"])
        commission = sum(x["amount"] for x in all_txs if x["type"] == "teknisyen_prim" and x.get("technician_id") == t["id"])
        tech_balances.append({
            "id": t["id"], "name": t["name"], "is_active": t.get("is_active", True),
            "debt": round(debt, 2), "paid": round(paid, 2),
            "commission": round(commission, 2),
            "balance": round(debt - paid, 2)  # pozitif = şirkete borçlu
        })
    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "net_profit": round(income - expense - tech_commission, 2),
        "technician_receivable": round(tech_debt - tech_paid, 2),
        "technician_total_debt": round(tech_debt, 2),
        "technician_total_paid": round(tech_paid, 2),
        "technician_total_commission": round(tech_commission, 2),
        "technician_balances": tech_balances
    }

# -------------------------- Dashboard / Reports --------------------------
@api_router.get("/dashboard/admin")
async def admin_dashboard(_: dict = Depends(require_admin)):
    # Hız: 14+ ardışık sorgu yerine birkaç toplu sorgu, hepsi paralel (uzak veritabanında her sorgu bir gidiş-dönüş demektir)
    today = datetime.now(timezone.utc).date()
    week_start = datetime.combine(today - timedelta(days=6), datetime.min.time(), tzinfo=timezone.utc).isoformat()
    DONE_ = ["tamamlandi", "faturalandi"]
    (total_customers, total_technicians, st_rows, rev_rows, week_tx, tech_rows, techs, parts) = await asyncio.gather(
        db.customers.count_documents({}),
        db.users.count_documents({"role": "technician", "is_active": True}),
        db.service_jobs.aggregate([{"$group": {"_id": "$status", "n": {"$sum": 1}}}]).to_list(50),
        db.cash_transactions.aggregate([{"$match": {"type": "gelir"}}, {"$group": {"_id": None, "t": {"$sum": "$amount"}}}]).to_list(1),
        db.cash_transactions.find({"type": "gelir", "date": {"$gte": week_start}}, {"_id": 0, "amount": 1, "date": 1}).to_list(10000),
        db.service_jobs.aggregate([{"$match": {"status": {"$in": DONE_}}}, {"$group": {"_id": "$assigned_technician_id", "n": {"$sum": 1}}}]).to_list(2000),
        db.users.find({"role": "technician"}, {"_id": 0, "id": 1, "name": 1}).to_list(500),
        db.spare_parts.find({"$expr": {"$and": [{"$gt": ["$min_stock", 0]}, {"$lte": ["$stock_qty", "$min_stock"]}]}}, {"_id": 0}).to_list(2000),
    )
    by_status = {r["_id"]: r["n"] for r in st_rows}
    total_jobs = sum(by_status.values())
    open_jobs = sum(by_status.get(k, 0) for k in ["yeni", "atandi", "yolda", "basladi"])
    completed_jobs = by_status.get("tamamlandi", 0)
    total_revenue = float(rev_rows[0]["t"]) if rev_rows else 0.0
    statuses = ["yeni", "atandi", "yolda", "basladi", "tamamlandi", "iptal"]
    status_counts = {k: by_status.get(k, 0) for k in statuses}

    daily_revenue = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_start = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).isoformat()
        d_end = datetime.combine(d, datetime.max.time(), tzinfo=timezone.utc).isoformat()
        day_total = sum(t["amount"] for t in week_tx if d_start <= t.get("date", "") <= d_end)
        daily_revenue.append({"date": d.strftime("%d %b"), "amount": round(day_total, 2)})

    done_by = {r["_id"]: r["n"] for r in tech_rows}
    top_techs = [{"name": t["name"], "completed": done_by.get(t["id"], 0)} for t in techs]
    top_techs.sort(key=lambda x: x["completed"], reverse=True)

    return {
        "total_customers": total_customers,
        "total_technicians": total_technicians,
        "total_jobs": total_jobs,
        "open_jobs": open_jobs,
        "completed_jobs": completed_jobs,
        "total_revenue": round(total_revenue, 2),
        "status_counts": status_counts,
        "daily_revenue": daily_revenue,
        "top_technicians": top_techs[:5],
        "low_stock": parts[:10]
    }

@api_router.get("/dashboard/tech")
async def tech_dashboard(user: dict = Depends(get_current_user)):
    if user["role"] != "technician":
        raise HTTPException(status_code=403, detail="Sadece teknisyenler için")
    tech_id = user["id"]
    open_jobs = await db.service_jobs.count_documents({
        "assigned_technician_id": tech_id,
        "status": {"$in": ["atandi", "yolda", "basladi"]}
    })
    completed_today = await db.service_jobs.count_documents({
        "assigned_technician_id": tech_id,
        "status": "tamamlandi",
        "completed_at": {"$gte": datetime.now(timezone.utc).date().isoformat()}
    })
    completed_total = await db.service_jobs.count_documents({
        "assigned_technician_id": tech_id,
        "status": {"$in": ["tamamlandi", "faturalandi"]}
    })
    txs = await db.cash_transactions.find({"technician_id": tech_id}, {"_id": 0}).to_list(2000)
    debt = sum(t["amount"] for t in txs if t["type"] == "teknisyen_borc")
    paid = sum(t["amount"] for t in txs if t["type"] == "teknisyen_odeme")
    commission = sum(t["amount"] for t in txs if t["type"] == "teknisyen_prim")
    return {
        "open_jobs": open_jobs,
        "completed_today": completed_today,
        "completed_total": completed_total,
        "balance": round(debt - paid, 2),
        "total_debt": round(debt, 2),
        "total_paid": round(paid, 2),
        "total_commission": round(commission, 2),
        "commission_percent": user.get("commission_percent", 0)
    }

# -------------------------- File Upload --------------------------
def _shrink_image(data: bytes, ctype: str, ext: str):
    """Fotoğrafları orta kaliteye indirir (en uzun kenar 1600 px, JPEG %72) → sunucuda yer tutmaz.
    Şeffaf PNG (imza vb.) JPEG'e çevrilmez, yalnızca küçültülür. Hata olursa orijinal aynen saklanır."""
    try:
        if not ctype.startswith("image/") or ctype in ("image/gif", "image/svg+xml") or len(data) < 150_000:
            return data, ctype, ext
        from PIL import Image, ImageOps
        import io as _io
        im = Image.open(_io.BytesIO(data))
        im = ImageOps.exif_transpose(im)
        im.thumbnail((1600, 1600))
        buf = _io.BytesIO()
        if im.mode in ("RGBA", "LA", "P") and ("A" in im.getbands() or "transparency" in im.info):
            im.convert("RGBA").save(buf, "PNG", optimize=True)
            out, oc, oe = buf.getvalue(), "image/png", "png"
        else:
            im.convert("RGB").save(buf, "JPEG", quality=72, optimize=True, progressive=True)
            out, oc, oe = buf.getvalue(), "image/jpeg", "jpg"
        return (out, oc, oe) if len(out) < len(data) else (data, ctype, ext)
    except Exception:
        return data, ctype, ext

@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "bin"
    data = await file.read()
    ctype = file.content_type or "application/octet-stream"
    data, ctype, ext = await asyncio.to_thread(_shrink_image, data, ctype, ext)
    path = f"{APP_NAME}/uploads/{user['id']}/{uuid.uuid4()}.{ext}"
    result = await asyncio.to_thread(put_object, path, data, ctype)
    rec = {
        "id": str(uuid.uuid4()),
        "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size": result["size"],
        "uploaded_by": user["id"],
        "is_deleted": False,
        "created_at": now_iso()
    }
    await db.files.insert_one(rec)
    rec.pop("_id", None)
    return {"id": rec["id"], "path": result["path"], "url": f"/api/files/{result['path']}"}

@api_router.get("/files/{path:path}")
async def serve_file(path: str, auth: Optional[str] = Query(None), authorization: Optional[str] = Header(None)):    # Allow either header or query token
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif auth:
        token = auth
    if not token:
        raise HTTPException(status_code=401, detail="Yetkisiz")
    try:
        jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Geçersiz token")
    rec = await db.files.find_one({"storage_path": path, "is_deleted": False}, {"_id": 0})
    if not rec:
        raise HTTPException(status_code=404, detail="Dosya bulunamadı")
    data, ct = await asyncio.to_thread(get_object, path)          # disk/uzak depo okuması olay döngüsünü kilitlemesin
    return FastAPIResponse(content=data, media_type=rec.get("content_type", ct), headers={"Cache-Control": "private, max-age=86400"})

def _safe_public_url(u: str) -> bool:
    """SSRF korumasi: yalnizca http(s) ve genel (ozel/loopback/link-local olmayan) adresler."""
    import ipaddress, socket
    from urllib.parse import urlparse
    try:
        p = urlparse(u or "")
        if p.scheme not in ("http", "https") or not p.hostname:
            return False
        for fam, _t, _p, _c, sa in socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == "https" else 80)):
            ip = ipaddress.ip_address(sa[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
                return False
        return True
    except Exception:
        return False

@api_router.get("/proxy-image")
async def proxy_image(url: str = Query(...)):
    """Marka logosu gibi 3rd party imajları CORS sorunu olmadan proxy'ler (yalnız genel adresler, yalnız görsel, en çok 5 MB)."""
    try:
        def _get():
            cur = url
            for _ in range(3):                                   # yonlendirmeleri elle izle, her adimi dogrula
                if not _safe_public_url(cur):
                    raise ValueError("adres izin verilmiyor")
                r = requests.get(cur, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=False, stream=True)
                if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("Location"):
                    from urllib.parse import urljoin
                    cur = urljoin(cur, r.headers["Location"]); r.close(); continue
                r.raise_for_status()
                ct = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                if not ct.startswith("image/"):
                    raise ValueError("gorsel degil")
                data = r.raw.read(5 * 1024 * 1024 + 1, decode_content=True)
                if len(data) > 5 * 1024 * 1024:
                    raise ValueError("cok buyuk")
                return data, ct
            raise ValueError("cok fazla yonlendirme")
        data, ct = await asyncio.to_thread(_get)
        return FastAPIResponse(content=data, media_type=ct, headers={"Cache-Control": "public, max-age=86400", "X-Content-Type-Options": "nosniff"})
    except Exception as e:
        logger.warning(f"proxy-image failed for {url}: {e}")
        raise HTTPException(status_code=404, detail="Image not found")

def _logo_domain(u: str) -> str:
    from urllib.parse import urlparse
    p = urlparse(u or "")
    if p.netloc.endswith("clearbit.com"):
        return p.path.strip("/").split("/")[0]
    return (p.netloc or "").replace("www.", "")

def _fetch_logo(url: str, name: str):
    """Marka logosu: kayıtlı adres -> Google favicon -> DuckDuckGo. İlk geçerli görseli döndürür."""
    hdr = {"User-Agent": "Mozilla/5.0"}
    cands = []
    if url and "clearbit.com" not in url:
        cands.append(url)
    dom = _logo_domain(url)
    if dom:
        cands += [f"https://www.google.com/s2/favicons?domain={dom}&sz=128", f"https://icons.duckduckgo.com/ip3/{dom}.ico"]
        if url and "clearbit.com" in url:
            cands.append(url)
    for c in cands:
        try:
            r = requests.get(c, timeout=8, headers=hdr)
            ct = r.headers.get("Content-Type", "")
            if r.status_code == 200 and ct.startswith("image/") and len(r.content) > 300 and "svg" not in ct:
                return r.content, ct
        except Exception:                               # noqa: BLE001
            continue
    return None

@api_router.get("/brand-logo")
async def brand_logo(name: str):
    """Servis fişi PDF'i için aynı kaynaktan (same-origin) marka logosu; sonuç veritabanında önbelleğe alınır."""
    key = (name or "").strip().lower()[:80]
    if not key:
        raise HTTPException(404, "Logo yok")
    hit = await db.brand_logo_cache.find_one({"key": key}, {"_id": 0})
    if hit and hit.get("data"):
        import base64 as _b64
        return FastAPIResponse(content=_b64.b64decode(hit["data"]), media_type=hit.get("ct", "image/png"), headers={"Cache-Control": "public, max-age=604800"})
    brand = await db.brands.find_one({"name": {"$regex": "^" + re.escape(name.strip()) + "$", "$options": "i"}}, {"_id": 0})
    url = (brand or {}).get("logo_url", "")
    if url.startswith("/"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url)
    got = await asyncio.to_thread(_fetch_logo, url, key)
    if not got:
        raise HTTPException(404, "Logo bulunamadı")
    import base64 as _b64
    await db.brand_logo_cache.update_one({"key": key}, {"$set": {"key": key, "data": _b64.b64encode(got[0]).decode(), "ct": got[1]}}, upsert=True)
    return FastAPIResponse(content=got[0], media_type=got[1], headers={"Cache-Control": "public, max-age=604800"})

def _enrich_logo(job: dict) -> dict:
    """PDF için marka logosunu güvenilir same-origin adrese çevirir (eski clearbit adresleri artık çalışmıyor)."""
    try:
        nm = (job or {}).get("device_brand_name") or ""
        lg = (job or {}).get("device_brand_logo") or ""
        if nm and (not lg or "clearbit.com" in lg):
            from urllib.parse import quote
            job = {**job, "device_brand_logo": "/api/brand-logo?name=" + quote(nm)}
    except Exception:                                   # noqa: BLE001
        pass
    return job

# -------------------------- Price Quotes --------------------------
def _allocate_quote(target_total: float, labor_fee: float, parts: list) -> tuple:
    """Parça kalemlerine 'kalan = target_total - labor_fee' tutarını ağırlıklı dağıtır.
    Tek parça için tüm kalan ona gider. Hiç parça yoksa, kalan işçiliğe eklenir."""
    target_total = round(float(target_total or 0), 2)
    labor_fee = round(float(labor_fee or 0), 2)
    parts = parts or []
    if labor_fee > target_total:
        labor_fee = target_total
    remaining = round(target_total - labor_fee, 2)
    out_parts = []
    if not parts:
        # parça yoksa kalan tutarı işçiliğe ekle
        return round(target_total, 2), []
    total_weight = sum(max(float(p.get("weight", 1) or 1), 0.0001) for p in parts)
    accum = 0.0
    for i, p in enumerate(parts):
        w = max(float(p.get("weight", 1) or 1), 0.0001)
        if i == len(parts) - 1:
            amount = round(remaining - accum, 2)
        else:
            amount = round(remaining * w / total_weight, 2)
            accum += amount
        out_parts.append({
            "name": p.get("name", ""),
            "weight": w,
            "amount": amount
        })
    return labor_fee, out_parts

async def next_quote_number():
    counter = await db.counters.find_one_and_update(
        {"_id": "quote_seq"}, {"$inc": {"seq": 1}}, upsert=True, return_document=True
    )
    if not counter or "seq" not in counter:
        counter = await db.counters.find_one({"_id": "quote_seq"})
    return f"TKL-{counter['seq']:06d}"

@api_router.post("/quotes")
async def create_quote(payload: PriceQuoteCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ("technician", "admin"):
        raise HTTPException(status_code=403, detail="Yetki yok")
    labor_fee_final, parts_final = _allocate_quote(
        payload.target_total, payload.labor_fee, [p.model_dump() for p in payload.parts]
    )
    quote_no = await next_quote_number()
    doc = {
        "id": str(uuid.uuid4()),
        "quote_number": quote_no,
        "technician_id": user["id"],
        "technician_name": user.get("name", ""),
        "customer_id": payload.customer_id or "",
        "customer_name": payload.customer_name,
        "customer_phone": payload.customer_phone or "",
        "device_brand_name": payload.device_brand_name or "",
        "device_model": payload.device_model or "",
        "device_serial": payload.device_serial or "",
        "device_type": payload.device_type or "",
        "fault_description": payload.fault_description or "",
        "target_total": round(float(payload.target_total), 2),
        "labor_fee": labor_fee_final,
        "parts": parts_final,
        "footer_note": payload.footer_note or "",
        "status": "beklemede",
        "converted_job_id": "",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.price_quotes.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.get("/quotes")
async def list_quotes(user: dict = Depends(get_current_user)):
    query = {}
    if user["role"] == "technician":
        query["technician_id"] = user["id"]
    return await db.price_quotes.find(query, {"_id": 0}).sort("created_at", -1).to_list(2000)

@api_router.get("/quotes/{quote_id}")
async def get_quote(quote_id: str, user: dict = Depends(get_current_user)):
    q = await db.price_quotes.find_one({"id": quote_id}, {"_id": 0})
    if not q:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı")
    if user["role"] == "technician" and q.get("technician_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Bu teklife erişim yetkiniz yok")
    return q

@api_router.put("/quotes/{quote_id}")
async def update_quote(quote_id: str, payload: PriceQuoteUpdate, user: dict = Depends(get_current_user)):
    q = await db.price_quotes.find_one({"id": quote_id}, {"_id": 0})
    if not q:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı")
    if user["role"] == "technician" and q.get("technician_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Bu teklife erişim yetkiniz yok")
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    # parça/işçilik/total değişirse yeniden allocate
    if any(k in update for k in ("target_total", "labor_fee", "parts")):
        tt = update.get("target_total", q.get("target_total", 0))
        lf = update.get("labor_fee", q.get("labor_fee", 0))
        pts = update.get("parts", q.get("parts", []))
        # parts within update may be Pydantic dump already
        labor_fee_final, parts_final = _allocate_quote(tt, lf, pts)
        update["labor_fee"] = labor_fee_final
        update["parts"] = parts_final
        update["target_total"] = round(float(tt), 2)
    update["updated_at"] = now_iso()
    await db.price_quotes.update_one({"id": quote_id}, {"$set": update})
    return await db.price_quotes.find_one({"id": quote_id}, {"_id": 0})

@api_router.delete("/quotes/{quote_id}")
async def delete_quote(quote_id: str, user: dict = Depends(get_current_user)):
    q = await db.price_quotes.find_one({"id": quote_id}, {"_id": 0})
    if not q:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı")
    if user["role"] == "technician" and q.get("technician_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Bu teklife erişim yetkiniz yok")
    await db.price_quotes.delete_one({"id": quote_id})
    return {"ok": True}

class QuoteConvertPayload(BaseModel):
    customer_id: str
    device_id: Optional[str] = ""
    assigned_technician_id: Optional[str] = ""
    priority: Optional[Literal["normal", "acil"]] = "normal"
    scheduled_at: Optional[str] = ""

@api_router.post("/quotes/{quote_id}/convert")
async def convert_quote_to_job(quote_id: str, payload: QuoteConvertPayload, user: dict = Depends(get_current_user)):
    q = await db.price_quotes.find_one({"id": quote_id}, {"_id": 0})
    if not q:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı")
    customer = await db.customers.find_one({"id": payload.customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    device = None
    if payload.device_id:
        device = await db.devices.find_one({"id": payload.device_id}, {"_id": 0})
    tech_id = payload.assigned_technician_id or q.get("technician_id", "")
    technician = await db.users.find_one({"id": tech_id}, {"_id": 0, "password_hash": 0}) if tech_id else None

    job_no = await next_job_number()
    parts_used = []
    for p in q.get("parts", []):
        parts_used.append({
            "part_id": "",
            "name": p.get("name", ""),
            "qty": 1,
            "unit_price": float(p.get("amount", 0) or 0),
            "total": float(p.get("amount", 0) or 0),
        })
    parts_total = round(sum(p["total"] for p in parts_used), 2)
    labor_fee = float(q.get("labor_fee", 0) or 0)
    total_amount = round(parts_total + labor_fee, 2)
    commission_pct = float(technician.get("commission_percent", 0)) if technician else 0.0
    company_debt = round(total_amount * commission_pct / 100.0, 2)

    doc = {
        "id": str(uuid.uuid4()),
        "job_number": job_no,
        "customer_id": customer["id"],
        "customer_name": customer["name"],
        "customer_phone": customer["phone"],
        "customer_address": f'{customer.get("address","")} {customer.get("district","")} {customer.get("city","")}'.strip(),
        "device_id": device["id"] if device else "",
        "device_brand_id": device.get("brand_id", "") if device else "",
        "device_brand_name": device.get("brand_name", "") if device else "",
        "device_brand_logo": device.get("brand_logo", "") if device else "",
        "device_model": device.get("model", "") if device else "",
        "device_type": device.get("type", "") if device else "",
        "device_serial": device.get("serial_no", "") if device else "",
        "fault_description": q.get("fault_description", ""),
        "scheduled_at": payload.scheduled_at or "",
        "priority": payload.priority or "normal",
        "assigned_technician_id": tech_id,
        "assigned_technician_name": technician["name"] if technician else "",
        "technician_commission_percent": commission_pct,
        "status": "atandi" if tech_id else "yeni",
        "work_done": "",
        "parts_used": parts_used,
        "labor_fee": labor_fee,
        "parts_total": parts_total,
        "total_amount": total_amount,
        "technician_commission_amount": round(total_amount - company_debt, 2),
        "photos_before": [],
        "photos_after": [],
        "signature_url": "",
        "tech_signature_url": "",
        "pdf_note": "",
        "cancel_reason": "",
        "customer_rating": 0,
        "started_at": "",
        "completed_at": "",
        "from_quote_id": q["id"],
        "from_quote_number": q.get("quote_number", ""),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "created_by": user["id"],
    }
    await db.service_jobs.insert_one(doc)
    await db.price_quotes.update_one(
        {"id": quote_id},
        {"$set": {"status": "kabul", "converted_job_id": doc["id"], "customer_id": customer["id"], "updated_at": now_iso()}}
    )
    doc.pop("_id", None)
    return doc

# -------------------------- Settings (App-wide) --------------------------
class AppSettingsUpdate(BaseModel):
    default_pdf_note: Optional[str] = None
    company_name: Optional[str] = None
    company_phone: Optional[str] = None
    company_address: Optional[str] = None
    quote_footer_note: Optional[str] = None
    pdf_design: Optional[dict] = None
    tech_visibility: Optional[dict] = None

@api_router.get("/settings")
async def get_settings(response: Response, _: dict = Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store"
    doc = await db.app_settings.find_one({"_id": "global"}, {"_id": 0})
    if not doc:
        doc = {"default_pdf_note": "", "company_name": "", "company_phone": "", "company_address": "", "quote_footer_note": ""}
    doc.setdefault("quote_footer_note", "")
    return doc

@api_router.put("/settings")
async def update_settings(payload: AppSettingsUpdate, _: dict = Depends(require_admin)):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    await db.app_settings.update_one({"_id": "global"}, {"$set": update}, upsert=True)
    doc = await db.app_settings.find_one({"_id": "global"}, {"_id": 0})
    return doc

# -------------------------- App startup --------------------------
def _code_sig() -> str:
    import hashlib
    h = hashlib.sha1()
    try:
        for p in sorted(ROOT_DIR.glob("*.py")):
            st = p.stat()
            h.update(("%s:%d:%d;" % (p.name, st.st_size, int(st.st_mtime))).encode())
    except Exception:                                    # noqa: BLE001
        h.update(str(time.time()).encode())
    return h.hexdigest()[:16]


async def _setup_schema():
    """İndeksler + marka tohumları. Yavaş (160+ veritabanı gidiş-dönüşü) olduğu için yalnızca ilk kurulumda ve kod değiştiğinde çalışır."""
    # Indexes
    for _c, _k in (("service_jobs", [("created_at", -1)]), ("service_jobs", [("customer_id", 1), ("created_at", -1)]), ("customers", [("created_at", -1)])):
        try:
            await db[_c].create_index(_k)          # sıralama bellek sınırına (32 MB) takılmasın
        except Exception:                          # noqa: BLE001
            pass
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.customers.create_index("id", unique=True)
    await db.brands.create_index("id", unique=True)
    await db.devices.create_index("id", unique=True)
    await db.service_jobs.create_index("id", unique=True)
    await db.service_jobs.create_index("job_number", unique=True)
    await db.spare_parts.create_index("id", unique=True)
    await db.appointments.create_index("id", unique=True)
    await db.cash_transactions.create_index("id", unique=True)
    await db.price_quotes.create_index("id", unique=True)
    await db.price_quotes.create_index("quote_number", unique=True)

    PROGRESS("temel indeksler tamam, modul indeksleri")
    await crm_extras.ensure_indexes(db)
    await shop.ensure_indexes(db)
    await security.ensure_indexes(db)
    await studio.ensure_indexes(db)
    await finance.ensure_indexes(db)
    await insights.ensure_indexes(db)
    await crm360.ensure_indexes(db)
    await atolye.ensure_indexes(db)
    await governance.ensure_indexes(db)
    await finance_plus.ensure_indexes(db)
    await fieldops.ensure_indexes(db)
    await growth.ensure_indexes(db)
    await collab.ensure_indexes(db)
    await collab.seed_training(db)
    await ops2.ensure_indexes(db)
    await ops3.ensure_indexes(db)
    await mkt.ensure_indexes(db)
    await mkt_site.ensure_indexes(db)
    await ai.ensure_indexes(db)
    asyncio.create_task(speed.ensure_indexes(db))
    # Seed brands (Turkey)
    brand_seed = [
        {"name": "Vaillant", "logo_url": "https://logo.clearbit.com/vaillant.com.tr"},
        {"name": "Bosch", "logo_url": "https://logo.clearbit.com/bosch.com.tr"},
        {"name": "Buderus", "logo_url": "https://logo.clearbit.com/buderus.com.tr"},
        {"name": "Demirdöküm", "logo_url": "https://logo.clearbit.com/demirdokum.com.tr"},
        {"name": "Baymak", "logo_url": "https://logo.clearbit.com/baymak.com.tr"},
        {"name": "ECA", "logo_url": "https://logo.clearbit.com/eca.com.tr"},
        {"name": "Arçelik", "logo_url": "https://logo.clearbit.com/arcelik.com.tr"},
        {"name": "Vestel", "logo_url": "https://logo.clearbit.com/vestel.com.tr"},
        {"name": "Beko", "logo_url": "https://logo.clearbit.com/beko.com.tr"},
        {"name": "Daikin", "logo_url": "https://logo.clearbit.com/daikin.com.tr"},
        {"name": "Mitsubishi Electric", "logo_url": "https://logo.clearbit.com/mitsubishielectric.com.tr"},
        {"name": "LG", "logo_url": "https://logo.clearbit.com/lg.com"},
        {"name": "Samsung", "logo_url": "https://logo.clearbit.com/samsung.com"},
        {"name": "Airfel", "logo_url": "https://logo.clearbit.com/airfel.com"},
        {"name": "Protherm", "logo_url": "https://logo.clearbit.com/protherm.com.tr"},
        {"name": "Ferroli", "logo_url": "https://logo.clearbit.com/ferroli.com.tr"},
        {"name": "Alarko Carrier", "logo_url": "https://logo.clearbit.com/alarko-carrier.com.tr"},
        {"name": "Siemens"}, {"name": "Profilo"}, {"name": "Altus"}, {"name": "Regal"}, {"name": "Hotpoint-Ariston"}, {"name": "Indesit"}, {"name": "Candy"}, {"name": "Grundig"},
        {"name": "Miele"}, {"name": "Electrolux"}, {"name": "AEG"}, {"name": "Whirlpool"}, {"name": "Hisense"}, {"name": "Haier"}, {"name": "Sunny"}, {"name": "Philips"}, {"name": "Onvo"},
        {"name": "Sharp"}, {"name": "Toshiba"}, {"name": "Panasonic"}, {"name": "TCL"}, {"name": "Xiaomi"}, {"name": "Fujitsu"}, {"name": "General"}, {"name": "Midea"}, {"name": "Gree"},
        {"name": "Viessmann"}, {"name": "Immergas"}, {"name": "Warmhaus"}, {"name": "Simfer"}, {"name": "Franke"}, {"name": "Kumtel"}, {"name": "Teka"}, {"name": "Smeg"}, {"name": "Ariston"},
    ]
    _have = {x.get("name") for x in await db.brands.find({}, {"_id": 0, "name": 1}).to_list(5000)}     # tek sorgu (eskiden marka başına 1 sorgu)
    for b in brand_seed:
        if b["name"] not in _have:
            await db.brands.insert_one({
                "id": str(uuid.uuid4()),
                "name": b["name"],
                "logo_url": "",
                "is_active": True,
                "created_at": now_iso()
            })
    # Migration: clearbit logo URL'leri artık çalışmıyor, temizle
    await db.brands.update_many(
        {"logo_url": {"$regex": "logo.clearbit.com"}},
        {"$set": {"logo_url": ""}}
    )
    logger.info("Brands seeded")


@app.on_event("startup")
async def _reap_later():
    if os.environ.get("REAP_STALE", "0") != "1":
        return
    await asyncio.sleep(30)
    try:
        import governance
        k = await asyncio.get_running_loop().run_in_executor(None, governance.reap_stale)
        if k:
            logger.info("eski sureçler kapatildi: %s", k)
    except Exception:  # noqa: BLE001
        pass


@app.on_event("startup")
async def _reap_start():
    asyncio.get_running_loop().create_task(_reap_later())


@app.on_event("startup")
async def _limit_threads():
    """asyncio.to_thread havuzunu sınırla: hosting iş parçacığı kotasını aşmasın."""
    from concurrent.futures import ThreadPoolExecutor
    asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(max_workers=3, thread_name_prefix="spx"))
    try:
        import anyio.to_thread
        anyio.to_thread.current_default_thread_limiter().total_tokens = 4
    except Exception:  # noqa: BLE001
        pass


@app.on_event("startup")
async def startup():
    PROGRESS("baslangic: veritabani baglantisi deneniyor")
    await client.admin.command("ping")
    PROGRESS("baglanti tamam, indeksler olusturuluyor")
    # Hızlı açılış: şema kurulumu (indeks + tohum) her açılışta değil, yalnızca kod değiştiğinde. Değişiklik varsa arka planda çalışır.
    _sig = _code_sig()
    _boot = await db.app_settings.find_one({"_id": "boot"}, {"_id": 0}) or {}
    async def _run_setup():
        try:
            await _setup_schema()
            try:                                         # servis fişi tek sayfa yaması (yalnızca kod değişince; her açılışta 1,8 MB JS taranmaz)
                await pdf_yama("SPYENI2026")
            except Exception:                            # noqa: BLE001
                pass
            await db.app_settings.update_one({"_id": "boot"}, {"$set": {"sig": _sig, "at": now_iso()}}, upsert=True)
            PROGRESS("sema kurulumu tamam")
        except Exception as e:                           # noqa: BLE001
            logger.warning("şema kurulumu: %s", e)
    if not _boot:
        await _run_setup()                               # ilk kurulum: bekle (benzersiz indeksler hazır olsun)
    elif _boot.get("sig") != _sig:
        app.state.setup = asyncio.get_event_loop().create_task(_run_setup())   # güncelleme sonrası: arka planda, panel hemen açılır
        PROGRESS("kod degismis: indeksler arka planda guncelleniyor")
    else:
        PROGRESS("sema guncel: indeks adimi atlandi")
    PROGRESS("indeksler tamam, yonetici hesabi")
    if os.environ.get('SENTRY_DSN'):
        try:
            import sentry_sdk
            sentry_sdk.init(dsn=os.environ['SENTRY_DSN'], traces_sample_rate=0.0)
        except Exception as e:
            logger.warning('sentry başlatılamadı: %s', e)
    if os.environ.get('BACKGROUND_JOBS', '1') != '0':
        app.state.sched = asyncio.create_task(governance.scheduler(db))

    # Storage (uzak depo ise açılışı bekletmesin: 30 sn'ye kadar sürebilen ağ çağrısı ayrı iplikte)
    if local_storage():
        init_storage()
    else:
        asyncio.get_event_loop().run_in_executor(None, init_storage)

    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@servis.com").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Sistem Yöneticisi",
            "phone": "",
            "role": "admin",
            "commission_percent": 0,
            "is_active": True,
            "created_at": now_iso()
        })
        logger.info(f"Admin seeded: {admin_email}")
    elif os.environ.get("ADMIN_PASSWORD_SYNC", "1") != "0":
        # bcrypt doğrulaması ~0,3 sn CPU: her açılışta değil, yalnızca şifre/hash değiştiğinde (imza eşleşmiyorsa) yapılır
        import hashlib as _hl
        _adm = _hl.sha256((str(existing.get("password_hash", "")) + "|" + admin_password + "|" + JWT_SECRET).encode()).hexdigest()[:24]
        if _boot.get("adm") != _adm:
            if not verify_password(admin_password, existing["password_hash"]):
                _nh = hash_password(admin_password)
                await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": _nh}})
                logger.info(f"Admin password updated: {admin_email}")
                _adm = _hl.sha256((_nh + "|" + admin_password + "|" + JWT_SECRET).encode()).hexdigest()[:24]
            await db.app_settings.update_one({"_id": "boot"}, {"$set": {"adm": _adm}}, upsert=True)

    # Örnek usta (yalnızca geliştirme/deneme: SEED_DEMO=1). Canlıda KAPALI kalmalı.
    tech_email = "tech@servis.com"
    if os.environ.get("SEED_DEMO", "0") == "1" and not await db.users.find_one({"email": tech_email}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": tech_email,
            "password_hash": hash_password("tech123"),
            "name": "Ahmet Yılmaz",
            "phone": "0555 111 22 33",
            "role": "technician",
            "commission_percent": 30.0,
            "is_active": True,
            "created_at": now_iso()
        })
        logger.info("Sample technician seeded")


# -------------------------- Web / CRM / Analitik modülü --------------------------
import crm_extras
import security
import studio
import finance
import insights
import crm360
import atolye
import governance
import notify
import speed
import shop
import finance_plus
import fieldops
import growth
import collab
import ops2
import ops3
import rapor
import kurulum
import mkt
import mkt_site
import ai
import sp_ext
security.register(api_router, db, {"require_admin": require_admin})
studio.register(api_router, db, {"require_admin": require_admin})
finance.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user})
insights.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user})
crm360.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user})
atolye.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user})
import livechat
livechat.register(api_router, db, {"get_current_user": get_current_user})
fieldops.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user})
import ilan
ilan.register(api_router, db, {"require_admin": require_admin})
import sektor_mod
sektor_mod.register(api_router, db, {"require_admin": require_admin})
import sektor_kayit
sektor_kayit.register(api_router, db, {"require_admin": require_admin})
import yp  # yeni yönetim paneli (ayrı uçlar: /api/yp/*)
yp.register(api_router, db, {"require_admin": require_admin})
import blocks_api  # bölüm motoru: katalog, rozet, sektör paketi, sayfalar
blocks_api.register(api_router, db, {"require_admin": require_admin})
import urun  # e-ticaret ürün modülü


async def _fetch_url(u):                                               # hızlı ürün ekleme: sayfayı indir
    import httpx
    async with httpx.AsyncClient(timeout=12, follow_redirects=True,
                                 headers={"User-Agent": "Mozilla/5.0 (compatible; OnlineKaydet/1.0)"}) as cl:
        r = await cl.get(u)
        r.raise_for_status()
        return r.text[:900000]


urun.register(api_router, db, {"require_admin": require_admin, "fetch_url": _fetch_url})
import pazaryeri  # pazaryeri eşleştirme ve stok senkronu
pazaryeri.register(api_router, db, {"require_admin": require_admin, "channel_push": None})

import kampanya
kampanya.register(api_router, db, {"require_admin": require_admin})

import siparis
siparis.register(api_router, db, {"require_admin": require_admin})

import entegrasyon
entegrasyon.register(api_router, db, {"require_admin": require_admin, "probe": None})

import bildirim
bildirim.register(api_router, db, {"require_admin": require_admin, "send_sms": None})

import icerik
icerik.register(api_router, db, {"require_admin": require_admin})

@app.get("/salon", include_in_schema=False)
async def yp_sayfa():
    """Yeni yönetim paneli (randevuyla çalışan işler). Eski /admin ekranından ayrıdır."""
    from fastapi.responses import HTMLResponse
    return HTMLResponse((Path(__file__).resolve().parent / "yp_ui.html").read_text(encoding="utf-8"), headers={"Cache-Control": "no-cache", "X-Robots-Tag": "noindex"})

@app.get("/salon/logo.png", include_in_schema=False)
async def yp_logo():
    from fastapi.responses import Response as _R
    return _R(__import__("base64").b64decode((Path(__file__).resolve().parent / "yp_logo.b64").read_text()), media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})
governance.HOOKS.append(fieldops.call_hook)
finance_plus.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user})
async def _tech_hidden():
    return tech_hidden_now(await get_tech_vis())
growth.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user, "sync_job_ledger": sync_job_ledger,
                                 "quick_create_job": quick_create_job, "tech_hidden": _tech_hidden, "fault_cat": insights.fault_cat})
async def _assign_job(job_id, tech_id):
    await update_job(job_id, ServiceJobUpdate(assigned_technician_id=tech_id), {"id": "auto", "role": "admin", "name": "Otomatik atama", "email": ""})
ops2.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user, "assign_job": _assign_job})
ops3.register(api_router, db, {"require_admin": require_admin})
rapor.register(api_router, db, {"require_admin": require_admin})
kurulum.register(api_router, db, {"require_admin": require_admin})
mkt.register(api_router, db, {"require_admin": require_admin})
mkt_site.register(api_router, db, {"require_admin": require_admin})
collab.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user})
ai.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user})
speed.register(api_router, db)
governance.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user, "verify_password": verify_password, "hash_password": hash_password})
shop.register(api_router, db, {"require_admin": require_admin, "hash_password": hash_password, "verify_password": verify_password,
                            "JWT_SECRET": JWT_SECRET, "JWT_ALGORITHM": JWT_ALGORITHM, "security": security})
import firms
firms.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user, "hash_password": hash_password, "verify_password": verify_password})
import leads; leads.register(api_router, db, {"require_admin": require_admin})
sp_ext.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user, "verify_password": verify_password,
                                 "JWT_SECRET": JWT_SECRET, "JWT_ALGORITHM": JWT_ALGORITHM})
import markets_hub
markets_hub.register(api_router, db, {"require_admin": require_admin})
import gsc_auto
import spx4
spx4.register(api_router, db, {"require_admin": require_admin})
import bakim
bakim.register(api_router, db, {"require_admin": require_admin, "quick_create_job": quick_create_job, "app": app})
import kurumsal
kurumsal.register(api_router, db, {"require_admin": require_admin}, app)
import foto
foto.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user, "get_object": get_object})
import avatar
avatar.register(api_router, db, {"get_current_user": get_current_user, "get_object": get_object, "JWT_SECRET": JWT_SECRET, "JWT_ALGORITHM": JWT_ALGORITHM})
import surum
surum.register(api_router, db, {"require_admin": require_admin})
import servis_ayar
servis_ayar.setup(app, api_router, db, get_current_user, tenant)
import sektor as _sektor
_sektor.register(api_router, db, {"get_current_user": get_current_user})
import demo
demo.register(api_router, db, {"hash_password": hash_password})
import domains
import kurumsal as _kur
domains.register(api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user, "themes": _kur.THEMES})
import siteedit
siteedit.register(api_router, db, {"require_admin": require_admin, "themes": _kur.THEMES, "portal_chip": domains.portal_chip})
import sahip
sahip.register(app, api_router, db, {"require_admin": require_admin, "get_current_user": get_current_user, "create_access_token": create_access_token, "hash_password": hash_password})
gsc_auto.register(api_router, db, {"require_admin": require_admin, "JWT_SECRET": JWT_SECRET})
# Marka ürün aktarma kapatıldı (brand_import kaydedilmez; zamanlayıcı ve uç noktalar çalışmaz).
crm_extras.register(api_router, db, {
    "get_current_user": get_current_user,
    "require_admin": require_admin,
    "now_iso": now_iso,
    "hash_password": hash_password,
    "quick_create_job": quick_create_job,
})

# Include router and CORS
app.include_router(api_router)
@app.middleware("http")
async def _timing(request: Request, call_next):
    t0 = time.perf_counter()
    resp = await call_next(request)
    try:
        if request.url.path.startswith("/api/"):
            rt = request.scope.get("route")
            _ms = (time.perf_counter() - t0) * 1000
            speed.record((request.method + " " + (getattr(rt, "path", None) or request.url.path)), _ms)
            resp.headers["X-Spx"] = "pid=%d;app=%dms" % (os.getpid(), _ms)      # teşhis: yanıtı hangi süreç, uygulama içinde kaç ms'de üretti
    except Exception:                                   # noqa: BLE001
        pass
    return resp

from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=800)
app.middleware("http")(governance.make_middleware(db, get_current_user))
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def _firm_ctx(request: Request, call_next):
    """Firma jetonu taşıyan istekleri firmanın veritabanına yönlendirir (en dış katman olmalı)."""
    from fastapi.responses import JSONResponse as _JR
    ft = None
    # Herkese açık bağlantılar: yolda <firma_id>~<jeton> varsa istek o firmanın veritabanına gider, ön ek yoldan çıkarılır.
    _m = re.search(r"/([0-9a-f]{12})~", request.url.path)
    if _m and request.url.path.startswith(("/api/public/", "/takip/", "/cihaz/", "/bakim/", "/odeme/", "/teklif/", "/portal/", "/demo/")):
        _fd = await db.main().firms.find_one({"id": _m.group(1)}, {"_id": 0, "db": 1, "status": 1, "expires_at": 1})
        if not _fd or _fd.get("status") == "askida" or firms.expired(_fd):
            return _JR({"detail": "Bağlantı geçersiz"}, status_code=404)
        _np = request.url.path.replace(_m.group(1) + "~", "", 1)
        request.scope["path"] = _np
        request.scope["raw_path"] = _np.encode()
        ft = tenant.set_firm(_fd["db"])
        try:
            return await call_next(request)
        finally:
            tenant.reset(ft)
    if request.url.path.startswith("/api/public/"):
        # Müşterinin kendi alan adından (Host) ya da onun sitesinden (Origin) gelen herkese açık istekler o firmaya gider.
        try:
            _hh = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
            _og = request.headers.get("origin", "")
            _hd = await domains.host_to_firm(db, _hh)
            if not _hd and _og:
                from urllib.parse import urlparse as _up
                _hd = await domains.host_to_firm(db, _up(_og).hostname or "")
        except Exception:                               # noqa: BLE001
            _hd = None
        if _hd:
            _fd = await db.main().firms.find_one({"id": _hd["firm_id"]}, {"_id": 0, "db": 1, "status": 1, "expires_at": 1})
            if not _fd or _fd.get("status") == "askida" or firms.expired(_fd):
                return _JR({"detail": "Site geçici olarak kapalı"}, status_code=404)
            ft = tenant.set_firm(_fd["db"])
            try:
                return await call_next(request)
            finally:
                tenant.reset(ft)
    try:
        h = request.headers.get("Authorization", "")
        tk = h[7:] if h.startswith("Bearer ") else (request.query_params.get("auth") or request.cookies.get("access_token"))
        if tk:
            _pl = jwt.decode(tk, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            f = _pl.get("firm")
            if f:
                request.state.fu = _pl.get("fu", "")
                if firms.ACCESS and not request.url.path.endswith(("/auth/login", "/auth/logout")) and not await firms.ACCESS(f, _pl.get("fu", "")):
                    return _JR({"detail": "Hesabınız kapalı veya kullanım süreniz doldu"}, status_code=403)
                ft = tenant.set_firm(f)
                if firms.GATE and request.url.path.startswith("/api/"):
                    _gm = await firms.GATE(f, request.url.path)
                    if _gm:
                        tenant.reset(ft)
                        return _JR({"detail": _gm}, status_code=403)
    except Exception:                                   # noqa: BLE001
        pass
    if ft is not None and request.url.path.startswith(("/api/admin/firms", "/api/admin/firm-template", "/api/admin/packages", "/api/admin/sectors", "/api/admin/subscriptions", "/api/admin/overview")):
        tenant.reset(ft)                                # firma yöneticisi platform (sahip) uçlarına giremez
        return _JR({"detail": "Bu işlem yalnızca platform sahibine açık"}, status_code=403)
    try:
        return await call_next(request)
    finally:
        if ft is not None:
            tenant.reset(ft)

# -------------------------- Cihaz QR etiketi sayfası (/cihaz/<jeton>) — React'ten bağımsız, her zaman çalışır

async def _fbrand(h):
    """Firma alan adı/hesabından açılan herkese açık sayfalarda ServisPlus markası yerine firmanın adı görünür."""
    try:
        if not tenant.current():
            return h
        import html as _hh
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        f = await db.main().firms.find_one({"db": tenant.current()}, {"_id": 0, "name": 1}) or {}
        nm = _hh.escape(g.get("company_name") or f.get("name") or "Servis")
        h = re.sub(r'<a href="https://servisplus\.net\.tr"><img[^>]*servisplus-logo[^>]*></a>', '<span style="font:800 18px system-ui;color:#fff">%s</span>' % nm, h)
        h = re.sub(r"ServisPlus &middot; Türkiye(?:'|&#39;)nin Servis Ağı<br><a [^>]*>servisplus\.net\.tr</a>", nm, h)
        h = h.replace("ServisPlus", nm)
        return h
    except Exception:
        return h

_CIHAZ_HTML = r"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><meta name="theme-color" content="#0a1f44"><title>Cihaz Bilgisi · ServisPlus</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--nv:#0a1f44;--bl:#1155cc;--or:#f27a1a;--ord:#dc6a0c;--ink:#273142;--mut:#6b7280;--ln:#e6e8ec;--bg:#f6f7f9;--ok:#0f9d58}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font:15px/1.5 Inter,system-ui,Segoe UI,Roboto,sans-serif;color:var(--ink);-webkit-font-smoothing:antialiased}
.top{background:#fff;border-bottom:1px solid var(--ln);padding:10px 16px;display:flex;align-items:center;justify-content:space-between}
.top img{height:38px;width:auto;display:block}.top a.ph{display:inline-flex;align-items:center;gap:6px;color:#fff;background:var(--or);text-decoration:none;font-weight:700;font-size:13px;padding:9px 13px;border-radius:10px}
.hero{background:linear-gradient(160deg,var(--nv) 0%,#123a82 100%);color:#fff;padding:26px 16px 70px}
.wrap{max-width:480px;margin:0 auto}.tag{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.14);border-radius:99px;padding:5px 11px;font-size:12px;font-weight:600;letter-spacing:.02em}
.hero h1{margin:12px 0 4px;font-size:24px;line-height:1.2;font-weight:800}.hero p{margin:0;opacity:.8;font-size:14px}
.main{margin:-48px auto 0;padding:0 16px 30px;max-width:520px}.card{background:#fff;border:1px solid var(--ln);border-radius:16px;padding:16px;margin-bottom:12px;box-shadow:0 6px 20px rgba(10,31,68,.06)}
.card h2{margin:0 0 10px;font-size:15px;font-weight:700;color:var(--nv);display:flex;align-items:center;gap:8px}
.badge{display:flex;align-items:center;gap:12px;padding:14px;border-radius:12px;margin-bottom:12px;font-weight:700}
.badge.ok{background:#e7f6ee;color:#0b6b3b}.badge.no{background:#fdecec;color:#a61b1b}.badge small{display:block;font-weight:500;opacity:.85;font-size:12.5px}.badge i{font-style:normal;font-size:24px}
.kv{display:grid;grid-template-columns:1fr 1fr;gap:10px}.kv div{background:var(--bg);border-radius:10px;padding:10px 12px}.kv span{display:block;font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em;font-weight:600}.kv b{font-size:14px;color:var(--nv)}
.tl{position:relative;margin:4px 0 0 6px;padding-left:18px;border-left:2px solid var(--ln)}.tl .it{position:relative;margin-bottom:12px}.tl .it:before{content:"";position:absolute;left:-25px;top:5px;width:12px;height:12px;border-radius:50%;background:var(--bl);border:2px solid #fff;box-shadow:0 0 0 2px var(--bl)}
.tl .d{font-size:12px;color:var(--mut);font-weight:600}.tl .t{font-size:14px}.empty{color:var(--mut);font-size:14px}
label{display:block;font-size:12.5px;font-weight:600;color:var(--nv);margin:10px 0 4px}input,textarea{width:100%;padding:12px;border:1px solid #cfd6e2;border-radius:10px;font:inherit;background:#fff;color:var(--ink)}input:focus,textarea:focus{outline:2px solid #bcd1fa;border-color:var(--bl)}
.btn{width:100%;margin-top:14px;padding:14px;border:0;border-radius:12px;background:var(--or);color:#fff;font:700 16px Inter,system-ui,sans-serif;cursor:pointer;box-shadow:0 6px 16px rgba(242,122,26,.35)}.btn:hover{background:var(--ord)}.btn:disabled{opacity:.6}
.msg{margin-top:10px;font-size:14px;font-weight:600}.msg.g{color:var(--ok)}.msg.r{color:#b91c1c}
.foot{text-align:center;color:var(--mut);font-size:12px;padding:6px 16px 28px}.foot a{color:var(--bl);text-decoration:none;font-weight:600}
.sk{height:120px;border-radius:16px;background:linear-gradient(90deg,#eceff4,#f6f7f9,#eceff4);background-size:200% 100%;animation:sh 1.2s infinite}@keyframes sh{to{background-position:-200% 0}}
</style></head><body>
<div class="top"><a href="https://servisplus.net.tr"><img src="https://servisplus.net.tr/static/img/servisplus-logo.png" alt="ServisPlus"></a><a class="ph" id="call" href="tel:+905444444004">&#9742; Ara</a></div>
<div class="hero"><div class="wrap"><span class="tag">&#128274; Cihaz Servis Etiketi</span><h1 id="ttl">Yükleniyor…</h1><p id="sub">&nbsp;</p></div></div>
<div class="main" id="a"><div class="sk"></div></div>
<div class="foot">ServisPlus &middot; Türkiye'nin Servis Ağı<br><a href="https://servisplus.net.tr">servisplus.net.tr</a></div>
<script>
var T=location.pathname.split('/').filter(Boolean).pop(),A=document.getElementById('a');
function e(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
var TY={kombi:'Kombi',klima:'Klima',buzdolabi:'Buzdolabı',camasir:'Çamaşır Makinesi',bulasik:'Bulaşık Makinesi',kurutma:'Kurutma Makinesi',firin:'Fırın / Ankastre',sofben:'Şofben',tv:'Televizyon',televizyon:'Televizyon',diger:'Cihaz'};
function fd(x){if(!x)return '-';var m=String(x).match(/^(\d{4})-(\d{2})-(\d{2})/);return m?m[3]+'.'+m[2]+'.'+m[1]:e(x)}
fetch('/api/public/device/'+encodeURIComponent(T)).then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error(j.detail||'Etiket okunamadı');return j})}).then(function(d){
 var ty=TY[d.type]||d.type||'Cihaz',ph=(d.company&&d.company.phone)||'';
 document.getElementById('ttl').textContent=((d.brand||'')+' '+(d.model||'')).trim()||ty;document.getElementById('sub').textContent=ty+' · Kayıtlı cihaz';
 if(ph){var c=document.getElementById('call');c.href='tel:'+ph.replace(/[^\d+]/g,'')}
 var wb=d.warranty_active?'<div class="badge ok"><i>&#10003;</i><div>Garanti devam ediyor<small>Bitiş: '+fd(d.warranty_until)+'</small></div></div>':'<div class="badge no"><i>!</i><div>'+(d.warranty_until?'Garanti süresi dolmuş':'Garanti bilgisi bulunmuyor')+'<small>'+(d.warranty_until?'Bitiş: '+fd(d.warranty_until)+' · ücretli servis uygulanabilir':'Servis ekibimiz size yardımcı olur')+'</small></div></div>';
 var h=(d.history||[]).map(function(x){return '<div class="it"><div class="d">'+fd(x.date)+'</div><div class="t">'+(e(x.summary)||'Servis işlemi tamamlandı')+'</div></div>'}).join('');
 A.innerHTML=wb+
 '<div class="card"><h2>&#128295; Cihaz bilgileri</h2><div class="kv"><div><span>Marka</span><b>'+e(d.brand||'-')+'</b></div><div><span>Model</span><b>'+e(d.model||'-')+'</b></div><div><span>Tür</span><b>'+e(ty)+'</b></div><div><span>Kurulum</span><b>'+fd(d.install_date)+'</b></div></div></div>'+
 '<div class="card"><h2>&#128221; Servis geçmişi</h2>'+(h?'<div class="tl">'+h+'</div>':'<div class="empty">Bu cihaz için henüz tamamlanmış servis kaydı yok.</div>')+'</div>'+
 '<div class="card"><h2>&#9889; Servis talebi oluştur</h2><div class="empty" style="margin-bottom:4px">Bilgilerinizi bırakın, ekibimiz sizi arasın.</div><label for="n">Ad Soyad</label><input id="n" placeholder="Adınız" autocomplete="name"><label for="p">Cep telefonu</label><input id="p" placeholder="05xx xxx xx xx" inputmode="tel" autocomplete="tel"><label for="f">Arıza / not</label><textarea id="f" rows="3" placeholder="Cihazda ne oluyor?"></textarea><button class="btn" id="g">Servis Talebi Gönder</button><div id="s" class="msg"></div></div>';
 document.getElementById('g').onclick=function(){var b=this,s=document.getElementById('s');b.disabled=true;s.className='msg';s.textContent='Gönderiliyor…';
  fetch('/api/public/device/'+encodeURIComponent(T)+'/request',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('n').value,phone:document.getElementById('p').value,fault:document.getElementById('f').value})}).then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok)throw new Error(r.status==422?'Lütfen adınızı ve geçerli bir cep telefonu girin':(r.status==429?'Çok fazla deneme, biraz sonra tekrar deneyin':(j.detail||'Bir hata oluştu')));s.className='msg g';s.textContent='✔ Talebiniz alındı. En kısa sürede sizi arayacağız.'})}).catch(function(x){s.className='msg r';s.textContent=x.message;b.disabled=false})};
}).catch(function(x){document.getElementById('ttl').textContent='Etiket okunamadı';document.getElementById('sub').textContent='';A.innerHTML='<div class="card"><h2>Bu QR etiketi geçerli değil</h2><div class="empty">'+e(x.message)+'. Lütfen bizi arayın, size yardımcı olalım.</div></div>'});
</script></body></html>"""

_atolye_h = atolye.page_handler(db)

@app.get("/atolye/{token}", include_in_schema=False)
async def atolye_sayfasi(token: str, request: Request, fmt: str = "a4", auto: int = 0):
    r = await _atolye_h(token, fmt, auto, request)
    r.headers["Cache-Control"] = "no-store"
    return r

_BELGE_CACHE = {}

def _belge_asset(name, mode="t"):
    import base64
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public_panel", name)
    try:
        if mode == "b":
            return "data:image/jpeg;base64," + base64.b64encode(open(f, "rb").read()).decode()
        return open(f, encoding="utf-8").read()
    except Exception:
        return ""

@app.get("/belge/{code}", include_in_schema=False)
async def belge_dogrula(code: str, request: Request):
    """Belgedeki QR'ın açtığı herkese açık doğrulama sayfası: kayıtla eşleşirse belge aynen gösterilir."""
    import html as _h
    from fastapi.responses import HTMLResponse
    rec = await db.certificates.find_one({"code": code[:40]}, {"_id": 0}) if re.fullmatch(r"[A-Za-z0-9]{6,40}", code or "") else None
    head = '<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta name="theme-color" content="#0a1f44"><title>Belge Doğrulama · ServisPlus</title><style>*{box-sizing:border-box}body{margin:0;background:#eef2f7;font:15px/1.5 Inter,system-ui,Segoe UI,Arial,sans-serif;color:#0f172a}.w{max-width:560px;margin:0 auto;padding:14px}.t{text-align:center;padding:10px 0}.t img{height:42px}.b{border-radius:16px;padding:16px 18px;color:#fff;text-align:center}.ok{background:linear-gradient(135deg,#15803d,#16a34a)}.no{background:linear-gradient(135deg,#b91c1c,#dc2626)}.b h1{margin:4px 0 2px;font-size:20px}.b p{margin:0;font-size:13.5px;opacity:.95}.c{background:#fff;border-radius:14px;padding:12px 16px;margin-top:12px;border:1px solid #e2e8f0}.c div{display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-bottom:1px solid #f1f5f9;font-size:14px}.c div:last-child{border:0}.c span{color:#64748b}.c b{text-align:right}#h{margin-top:12px;position:relative}#h iframe{border:0;background:#fff;width:210mm;height:297mm;transform-origin:0 0;box-shadow:0 6px 24px rgba(15,23,42,.18)}.btn{display:block;width:100%;margin-top:12px;border:0;background:#0a1f44;color:#fff;border-radius:12px;padding:13px;font-weight:700;font-size:15px}.f{text-align:center;color:#64748b;font-size:12px;margin:16px 0}</style></head><body><div class="w"><div class="t"><img src="' + _belge_asset("logo-servisplus.jpg", "b") + '" alt="ServisPlus"></div>'
    if not rec:
        return HTMLResponse(head + '<div class="b no"><div style="font-size:34px">✖</div><h1>Belge bulunamadı</h1><p>Bu kod ServisPlus kayıtlarında yok. Belge sahte veya hatalı olabilir.</p></div><div class="f">Şüpheli durumda lütfen ServisPlus ile iletişime geçin.</div></div></body></html>', status_code=404, headers={"Cache-Control": "no-store"})
    d = await collab.cert_payload(db, rec, str(request.base_url))
    d["qr"] = d.get("qr") or ""
    if not d.get("valid"):
        return HTMLResponse(head + '<div class="b no"><div style="font-size:34px">✖</div><h1>Belge geçerli değil</h1><p>Bu kayıt var ancak ilgili kişi artık ServisPlus iş ortağı olarak aktif değil.</p></div><div class="c"><div><span>Ad Soyad</span><b>' + _h.escape(d["name"]) + '</b></div><div><span>Belge No</span><b>' + _h.escape(d["no"]) + '</b></div></div></div></body></html>', headers={"Cache-Control": "no-store"})
    ban = '<div class="b ok"><div style="font-size:34px">✔</div><h1>Belge doğrulandı</h1><p>Bu belge ServisPlus kayıtlarıyla eşleşti ve geçerlidir.</p></div>'
    rows = '<div class="c"><div><span>İş ortağı</span><b>' + _h.escape(d["name"]) + '</b></div><div><span>Belge No</span><b>' + _h.escape(d["no"]) + '</b></div><div><span>Düzenlenme</span><b>' + _h.escape(d["date"]) + '</b></div><div><span>Durum</span><b style="color:#15803d">Aktif iş ortağı</b></div></div>'
    import json as _j
    js = _belge_asset("belge.js")
    script = '<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js"></script><script>' + js + '</script><script>(function(){var d=' + _j.dumps(d).replace("</", "<\\/") + ',logo=' + _j.dumps(_belge_asset("logo-servisplus.jpg", "b")) + ',html=window.spBelge.html("belge",d,logo),h=document.getElementById("h"),fr=document.createElement("iframe");fr.srcdoc=html;h.appendChild(fr);function fit(){var k=h.clientWidth/(210*3.7795);fr.style.transform="scale("+k+")";h.style.height=(297*3.7795*k)+"px"}fit();addEventListener("resize",fit);document.getElementById("p").onclick=function(){var w=window.open("","_blank");if(!w){try{fr.contentWindow.print()}catch(e){}return}w.document.open();w.document.write(html.replace("</body>","<script>onload=function(){setTimeout(function(){print()},500)}<\\/script></body>"));w.document.close()}})();</script>'
    return HTMLResponse(await _fbrand(head + ban + rows + '<div id="h"></div><button class="btn" id="p">PDF olarak kaydet / yazdır</button><div class="f">ServisPlus · Türkiye’nin Servis Ağı · servisplus.net.tr</div></div>' + script + '</body></html>'), headers={"Cache-Control": "no-store"})

@app.get("/cihaz/{token}", include_in_schema=False)
async def cihaz_sayfasi(token: str):
    from fastapi.responses import HTMLResponse
    return HTMLResponse(await _fbrand(_CIHAZ_HTML), headers={"Cache-Control": "no-store"})

# -------------------------- Müşteri takip sayfası (/takip/<jeton>) — React'ten bağımsız, giriş istemez
_TAKIP_HTML = r"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta name="theme-color" content="#0a1f44"><title>Servis Takibi · ServisPlus</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--nv:#0a1f44;--bl:#1155cc;--or:#f27a1a;--ord:#dc6a0c;--ink:#273142;--mut:#6b7280;--ln:#e6e8ec;--bg:#f6f7f9;--ok:#0f9d58}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font:15px/1.5 Inter,system-ui,Segoe UI,Roboto,sans-serif;color:var(--ink);-webkit-font-smoothing:antialiased}
.top{background:#fff;border-bottom:1px solid var(--ln);padding:10px 16px;display:flex;align-items:center;justify-content:space-between}
.top img{height:38px;width:auto;display:block}.top a.ph{display:inline-flex;align-items:center;gap:6px;color:#fff;background:var(--or);text-decoration:none;font-weight:700;font-size:13px;padding:9px 13px;border-radius:10px}
.hero{background:linear-gradient(160deg,var(--nv) 0%,#123a82 100%);color:#fff;padding:26px 0 70px}
.wrap{max-width:520px;margin:0 auto;padding:0 16px}.tag{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.14);border-radius:99px;padding:5px 11px;font-size:12px;font-weight:600;letter-spacing:.02em}
.hero h1{margin:12px 0 4px;font-size:26px;line-height:1.2;font-weight:800}.hero p{margin:0;opacity:.8;font-size:14px}
.main{margin:-48px auto 0;padding:0 16px 30px;max-width:520px}.card{background:#fff;border:1px solid var(--ln);border-radius:16px;padding:16px;margin-bottom:12px;box-shadow:0 6px 20px rgba(10,31,68,.06)}
.card h2{margin:0 0 12px;font-size:15px;font-weight:700;color:var(--nv)}
.badge{display:flex;align-items:center;gap:12px;padding:14px;border-radius:12px;margin-bottom:14px;font-weight:700;background:#fff3e8;color:#b45309}.badge.ok{background:#e6f6ee;color:var(--ok)}.badge.x{background:#fee2e2;color:#b91c1c}.badge i{font-style:normal;font-size:26px}
.steps{list-style:none;margin:0;padding:0}.steps li{position:relative;padding:0 0 16px 34px;color:var(--mut);font-size:14px}.steps li:last-child{padding-bottom:0}
.steps li:before{content:"";position:absolute;left:8px;top:20px;bottom:-2px;width:2px;background:var(--ln)}.steps li:last-child:before{display:none}
.steps li span{position:absolute;left:0;top:1px;width:18px;height:18px;border-radius:50%;background:#fff;border:2px solid #cfd6e2}
.steps li.d{color:var(--ink)}.steps li.d span{background:var(--ok);border-color:var(--ok)}.steps li.d:before{background:var(--ok)}
.steps li.c{color:var(--nv);font-weight:700}.steps li.c span{background:var(--or);border-color:var(--or);box-shadow:0 0 0 5px rgba(242,122,26,.2)}
.kv{display:grid;grid-template-columns:1fr 1fr;gap:10px}.kv div{background:var(--bg);border-radius:10px;padding:10px 12px}.kv span{display:block;font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em;font-weight:600}.kv b{font-size:14px;color:var(--nv)}
.stars button{font-size:34px;background:none;border:0;cursor:pointer;color:#cbd5e1;padding:0 2px}.stars button.on{color:#f5a623}
input,textarea{width:100%;padding:12px;border:1px solid #cfd6e2;border-radius:10px;font:inherit;background:#fff;color:var(--ink);margin-top:8px}input:focus,textarea:focus{outline:2px solid #bcd1fa;border-color:var(--bl)}.lnk{width:100%;border:0;background:none;color:var(--bl);font:700 14px Inter,system-ui,sans-serif;padding:2px 0;cursor:pointer;text-align:left}
.btn{display:block;width:100%;margin-top:12px;padding:14px;border:0;border-radius:12px;background:var(--or);color:#fff;font:700 16px Inter,system-ui,sans-serif;cursor:pointer;text-align:center;text-decoration:none;box-shadow:0 6px 16px rgba(242,122,26,.35)}.btn:hover{background:var(--ord)}.btn:disabled{opacity:.6}
.btn.nv{background:var(--nv);box-shadow:none}
.msg{margin-top:10px;font-size:14px;font-weight:600}.msg:empty{display:none}.msg.g{color:var(--ok)}.msg.r{color:#b91c1c}.empty{color:var(--mut);font-size:14px}
.sk{height:120px;border-radius:16px;background:linear-gradient(90deg,#eceff4,#f6f7f9,#eceff4);background-size:200% 100%;animation:sh 1.2s infinite}@keyframes sh{to{background-position:-200% 0}}
.foot{text-align:center;color:var(--mut);font-size:12px;padding:6px 16px 28px}.foot a{color:var(--bl);text-decoration:none;font-weight:600}
</style></head><body>
<div class="top"><a href="https://servisplus.net.tr"><img src="https://servisplus.net.tr/static/img/servisplus-logo.png" alt="ServisPlus"></a><a class="ph" id="call" href="tel:+905444444004">&#9742; Ara</a></div>
<div class="hero"><div class="wrap"><span class="tag">&#128295; Servis Takibi</span><h1 id="ttl">Yükleniyor…</h1><p id="sub">&nbsp;</p></div></div>
<div class="main" id="a"><div class="sk"></div></div>
<div class="foot">ServisPlus &middot; Türkiye'nin Servis Ağı<br><a href="https://servisplus.net.tr">servisplus.net.tr</a></div>
<script>
var T=location.pathname.split('/').filter(Boolean).pop(),A=document.getElementById('a'),R=0;
function e(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function fd(x){if(!x)return '-';var d=new Date(x);return isNaN(d)?e(x):d.toLocaleString('tr-TR',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'})}
var ST=[['yeni','Talebiniz alındı'],['atandi','Usta atandı'],['yolda','Usta yola çıktı'],['basladi','Servis işlemi başladı'],['tamamlandi','İş tamamlandı']];
function load(){fetch('/api/public/track/'+encodeURIComponent(T)).then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok)throw new Error(j.detail||'Takip bağlantısı geçersiz');return j})}).then(function(d){
 var ph=(d.company&&d.company.phone)||'',tel=ph.replace(/[^+\d]/g,'');if(tel)document.getElementById('call').href='tel:'+tel;
 document.getElementById('ttl').textContent=d.device||'Servis kaydınız';document.getElementById('sub').textContent='Kayıt No: '+(d.job_number||'-');
 var st=d.status==='faturalandi'?'tamamlandi':d.status,done=st==='tamamlandi',iptal=st==='iptal',idx=ST.map(function(x){return x[0]}).indexOf(st);
 var h='<div class="card"><div class="badge'+(done?' ok':iptal?' x':'')+'"><i>'+(done?'&#10004;':iptal?'&#10006;':'&#128339;')+'</i><div>'+e(d.status_label||d.status)+(d.eta_left!=null&&st==='yolda'?'<div style="font-weight:500;font-size:13px">Tahmini varış: yaklaşık '+d.eta_left+' dk</div>':'')+'</div></div>';
 if(!iptal)h+='<ul class="steps">'+ST.map(function(x,i){return '<li class="'+(i<idx||done?'d':i===idx?'c':'')+'"><span></span>'+x[1]+'</li>'}).join('')+'</ul>';
 if(d.location)h+='<a class="btn nv" target="_blank" rel="noopener" href="https://www.google.com/maps?q='+d.location.lat+','+d.location.lng+'">&#128205; Ustanın konumunu haritada aç</a>';
 h+='</div><div class="card"><h2>&#128295; Servis bilgileri</h2><div class="kv"><div><span>Cihaz</span><b>'+e(d.device||'-')+'</b></div><div><span>Usta</span><b style="display:flex;align-items:center;gap:8px">'+(d.technician_photo?'<img alt="" src="/api/public/track/'+encodeURIComponent(T)+'/usta-foto" onerror="this.remove()" style="width:44px;height:44px;border-radius:50%;object-fit:cover;border:2px solid #fff;box-shadow:0 0 0 1px #cfd6e2">':'')+e(d.technician||'Atanıyor')+'</b></div><div><span>Müşteri</span><b>'+e(d.customer||'-')+'</b></div><div><span>Randevu</span><b>'+fd(d.scheduled_at)+'</b></div></div></div>';
 if(d.work_done)h+='<div class="card"><h2>&#9989; Yapılan işlem</h2>'+e(d.work_done)+(d.total!=null?'<p style="margin:10px 0 0"><b>Toplam: '+e(d.total)+' ₺</b></p>':'')+'</div>';
 if(d.survey)h+='<div class="card"><h2>Değerlendirmeniz</h2><div style="color:#f5a623;font-size:24px">'+'★'.repeat(d.survey.rating)+'</div><div class="msg g">Teşekkür ederiz!</div>'+(d.review_url?'<a class="btn" target="_blank" rel="noopener" href="'+e(d.review_url)+'">Google\'da yorum yazın</a>':'')+'</div>';
 else if(d.can_rate)h+='<div class="card"><h2>&#11088; Hizmeti puanlayın</h2><div class="stars" id="stars">'+[1,2,3,4,5].map(function(i){return '<button data-i="'+i+'">★</button>'}).join('')+'</div><textarea id="cm" rows="3" placeholder="Yorumunuz (isteğe bağlı)"></textarea><button class="btn" id="sv">Gönder</button><div id="mg" class="msg"></div></div>';
 if(!done&&!iptal)h+='<div class="card" id="rc"><button class="lnk" id="ro" type="button">&#128197; Randevu saatini değiştirmek istiyorum</button><div id="rf" style="display:none;margin-top:12px"><input id="rw" placeholder="Uygun gün/saat (örn. Yarın 14:00)"><textarea id="rn" rows="2" placeholder="Not (isteğe bağlı)"></textarea><button class="btn nv" id="rs">Talebi gönder</button></div><div id="rm" class="msg"></div></div>';
 A.innerHTML=h;
 if(done)fetch('/api/public/track/'+encodeURIComponent(T)+'/fotolar').then(function(r){return r.ok?r.json():null}).then(function(f){if(!f||!(f.before.length||f.after.length))return;
  function g(t,k,a){return a.length?'<div style="margin-bottom:10px"><div style="font-size:12px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px">'+t+'</div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px">'+a.map(function(i){var u='/api/public/track/'+encodeURIComponent(T)+'/foto/'+k+'/'+i;return '<a href="'+u+'" target="_blank" rel="noopener"><img alt="" src="'+u+'?t=1" style="width:100%;aspect-ratio:1;object-fit:cover;border:1px solid #e6e8ec;display:block"></a>'}).join('')+'</div></div>':''}
  var c=document.createElement('div');c.className='card';c.innerHTML='<h2>&#128247; Servis fotoğrafları</h2>'+g('Önce','before',f.before)+g('Sonra','after',f.after)+'<div class="empty">Fotoğraflar servis kaydınızın bir parçasıdır; büyütmek için dokunun.</div>';var w=A.querySelector('.card:nth-of-type(3)');if(w&&w.nextSibling)A.insertBefore(c,w.nextSibling);else A.appendChild(c)}).catch(function(){});
 var ro=document.getElementById('ro');if(ro)ro.onclick=function(){var f=document.getElementById('rf');f.style.display=f.style.display==='none'?'block':'none'};
 var rs=document.getElementById('rs');if(rs)rs.onclick=function(){var m=document.getElementById('rm'),w=document.getElementById('rw').value.trim();if(w.length<3){m.className='msg r';m.textContent='Lütfen uygun olduğunuz zamanı yazın';return}rs.disabled=true;
  fetch('/api/public/track/'+encodeURIComponent(T)+'/reschedule',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({when:w,note:document.getElementById('rn').value})}).then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok)throw new Error(j.detail||'Hata');m.className='msg g';m.textContent='✔ Talebiniz alındı. Sizi arayacağız.'})}).catch(function(x){m.className='msg r';m.textContent=x.message;rs.disabled=false})};
 var sr=document.getElementById('stars');if(sr)sr.onclick=function(ev){var i=+ev.target.getAttribute('data-i');if(!i)return;R=i;[].forEach.call(sr.children,function(b,k){b.className=k<i?'on':''})};
 var sv=document.getElementById('sv');if(sv)sv.onclick=function(){var m=document.getElementById('mg');if(!R){m.className='msg r';m.textContent='Lütfen puan seçin';return}sv.disabled=true;
  fetch('/api/public/track/'+encodeURIComponent(T)+'/survey',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rating:R,comment:document.getElementById('cm').value})}).then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok)throw new Error(j.detail||'Hata');load()})}).catch(function(x){m.className='msg r';m.textContent=x.message;sv.disabled=false})};
}).catch(function(x){document.getElementById('ttl').textContent='Bağlantı geçersiz';document.getElementById('sub').textContent='';A.innerHTML='<div class="card"><h2>Bu takip bağlantısı geçerli değil</h2><div class="empty">'+e(x.message)+'. Lütfen bizi arayın, size yardımcı olalım.</div></div>'})}
load();setInterval(function(){if(!document.hidden&&!document.getElementById('sv')&&!(document.getElementById('rw')||{}).value)load()},60000);
</script></body></html>"""

@app.get("/takip/{token}", include_in_schema=False)
async def takip_sayfasi(token: str):
    from fastapi.responses import HTMLResponse
    return HTMLResponse(await _fbrand(_TAKIP_HTML), headers={"Cache-Control": "no-store"})

# -------------------------- Panel arayüzü (React derlemesi) --------------------------
# FRONTEND_DIR (varsayılan: backend/../frontend_build ya da backend/public_panel) varsa panel arayüzünü de bu uygulama sunar;
# /api dışındaki her yol index.html'e düşer (SPA yönlendirmesi). Klasör yoksa hiçbir şey eklenmez.
def _frontend_dir():
    for c in (os.environ.get("FRONTEND_DIR"), str(ROOT_DIR / "public_panel"), str(ROOT_DIR.parent / "frontend_build")):
        if c and (Path(c) / "index.html").is_file():
            return Path(c).resolve()
    return None

_FE = _frontend_dir()

def _panel_dir():
    """Panel arayüz klasörü: Python uygulamasının kendi klasöründe yoksa ana dizinde static/js/main.*.js aranır."""
    if _FE:
        return _FE
    import glob
    home = Path(os.path.expanduser("~"))
    envd = os.environ.get("PANEL_DIR")
    pats = ([envd + "/static/js/main.*.js"] if envd else []) + [str(home / "*" / "static" / "js" / "main.*.js"), str(home / "*" / "*" / "static" / "js" / "main.*.js"), str(home / "*" / "*" / "*" / "static" / "js" / "main.*.js")]
    for p in pats:
        for m in sorted(glob.glob(p)):
            d = Path(m).parent.parent.parent
            if (d / "index.html").is_file():
                return d
    return None

@app.get("/api/pdf-kod", include_in_schema=False)
async def pdf_kod(k: str = ""):
    """Teşhis: servis fişi PDF üreticisinin kodunu düz metin olarak gösterir (gizli bilgi içermez)."""
    from fastapi.responses import PlainTextResponse
    if k != "SPYENI2026":
        raise HTTPException(404, "Not Found")
    FE = _panel_dir()
    if not FE:
        return PlainTextResponse("Panel arayüz klasörü bulunamadı (static/js/main.*.js). Ana dizinde panel klasörünün adını söyleyin.")
    for f in sorted((FE / "static" / "js").glob("*.js")):
        if f.stem.endswith("-pdf") or f.stem.endswith("-pdf2"):
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        j = t.find("servis-fisi.pdf")
        if j < 0:
            continue
        i = t.rfind("async function", 0, j)
        return PlainTextResponse(t[i:j + 60], headers={"Cache-Control": "no-store"})
    return PlainTextResponse("bulunamadı")

def _pdf_tek_sayfa(t: str):
    """Servis fişi PDF'i (minify edilmiş jsPDF kodu): varsayılan not bloğunu imza + QR'ın ALTINA taşır, iki sütun ve otomatik küçültme ile tek sayfaya sığdırır."""
    import re as _re
    m = _re.search(r',(\w+)\+=10,(\w+)\.show_default_note&&(\w+)\.default_pdf_note\)\{', t)
    if not m:
        return t, 0, 0, 0
    sv, rv, av = m.group(1), m.group(2), m.group(3)
    k = t.index("{", m.start()) + 1
    d, e = 1, k
    while d and e < len(t):
        d += (t[e] == "{") - (t[e] == "}")
        e += 1
    block = t[k:e - 1]
    nm = _re.search(r'(\w+)\.addPage\(\)', block)
    fm = _re.search(r'\.setFont\((\w+),"bold"\)', block)
    if not nm or not fm:
        return t, 0, 0, 0
    nv, lv = nm.group(1), fm.group(1)
    t2 = t[:m.start()] + f",{sv}+=10,!1){{" + t[k:]          # eski (imza üstü) bloğu devre dışı bırak
    ins = (f'if({rv}.show_default_note&&{av}.default_pdf_note){{let _y={sv}+1,_f=6.2,_L,_k;{nv}.setDrawColor(220);{nv}.line(12,_y,198,_y);_y+=4;'
           f'{nv}.setFont({lv},"bold");{nv}.setFontSize(7);{nv}.setTextColor(80);{nv}.text({rv}.notes_label,12,_y);_y+=3;'
           f'{nv}.setFont({lv},"normal");{nv}.setTextColor(40);'
           f'for(;;){{{nv}.setFontSize(_f);_L={nv}.splitTextToSize({av}.default_pdf_note,91);_k=Math.ceil(_L.length/2);if(_y+_k*_f*.41<=266||_f<=3.6)break;_f-=.2}}'
           f'{nv}.text(_L.slice(0,_k),12,_y);{nv}.text(_L.slice(_k),107,_y)}}')
    pat = _re.compile(r'(' + _re.escape(nv) + r'\.setFontSize\(7\),' + _re.escape(nv) + r'\.setTextColor\(150\);const \w+=' + _re.escape(rv) + r'\.show_footer_logo)')
    t3, c = pat.subn(lambda mm: mm.group(1).replace(f"{nv}.setFontSize(7)", ins + f"{nv}.setFontSize(7)", 1), t2, count=1)
    if not c:
        return t, 0, 0, 0
    t3, c3 = _re.subn(r'(\w+)\.addImage\((\w+),(\w+)\(\2\),(12|109),(\w+),70,25\)', r'\1.addImage(\2,\3(\2),\4,\5,58,16)', t3)
    t3, c4 = _re.subn(r'(\w+)\+=28,(\w+)\.setFont', r'\1+=19,\2.setFont', t3)
    # GÜNCELLEME 171: toplamların solundaki boş alana küçük önce/sonra fotoğrafları (sayfa düzenini kaydırmaz)
    pm = _re.search(r';(if\()((\w+)\.setDrawColor\(200\),\3\.line\(120,(\w+),198,\4\),)', t3)
    jm = _re.search(r'const \w+=\((\w+)\.parts_used\|\|\[\]\)\.reduce', t3)
    c5 = 0
    if pm and jm:
        pv, yv, jv, fv = pm.group(3), pm.group(4), jm.group(1), lv
        fsn = (f';try{{const _P=await Promise.race([fetch("/api/foto/pdf/"+{jv}.id,{{headers:{{Authorization:"Bearer "+localStorage.getItem("token")}}}}).then(r=>r.ok?r.json():null).catch(()=>null),new Promise(r=>setTimeout(()=>r(null),4000))]);'
               f'if(_P&&{jv}.id&&(_P.before.length||_P.after.length)){{const _G=async u=>{{try{{const r=await fetch(u,{{headers:{{Authorization:"Bearer "+localStorage.getItem("token")}}}});if(!r.ok)return null;const b=await r.blob();const im=await createImageBitmap(b);const S=150,c=document.createElement("canvas");c.width=c.height=S;const m=Math.min(im.width,im.height);c.getContext("2d").drawImage(im,(im.width-m)/2,(im.height-m)/2,m,m,0,0,S,S);return c.toDataURL("image/jpeg",.72)}}catch(_e){{return null}}}};'
               f'const _B=await Promise.all(_P.before.slice(0,3).map(_G)),_A=await Promise.all(_P.after.slice(0,3).map(_G));let _x=12;const _y={yv}+3.5,_z=14;'
               f'for(const[_t,_l]of[["ÖNCE",_B],["SONRA",_A]]){{const _o=_l.filter(Boolean);if(!_o.length)continue;{pv}.setFont({fv},"bold");{pv}.setFontSize(5.5);{pv}.setTextColor(120);{pv}.text(_t,_x,_y-1);'
               f'for(const _d of _o){{try{{{pv}.addImage(_d,"JPEG",_x,_y,_z,_z)}}catch(_e){{}}_x+=_z+1}}_x+=3}}}}}}catch(_e){{}};')
        t3 = t3[:pm.start() + 1] + fsn[1:] + t3[pm.start() + 1:]
        c5 = 1
    return t3 + "\n/*sp-pdf-v171*/", c, c3, c4

@app.get("/api/pdf-yama", include_in_schema=False)
async def pdf_yama(k: str = ""):
    """Tek seferlik: servis fişindeki 'Önemli Notlar' (varsayılan PDF notu) yazısını küçültür. Panel derlemesini yedekleyip yeni adla yazar."""
    import re as _re
    import shutil
    if k != "SPYENI2026":
        raise HTTPException(404, "Not Found")
    FE = _panel_dir()
    if not FE:
        return {"ok": False, "mesaj": "Panel arayüz klasörü bulunamadı (static/js/main.*.js)"}
    out, idx = [], FE / "index.html"
    html = idx.read_text(encoding="utf-8")
    for f in sorted((FE / "static" / "js").glob("*.js")):
        if f.stem.endswith("-pdf") or f.stem.endswith("-pdf2") or f.stem.endswith("-pdf3"):
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        if "default_pdf_note" not in t:
            continue
        n, c, c3, c4 = _pdf_tek_sayfa(t)
        if not c:
            out.append(f"{f.name}: kalıp bulunamadı")
            continue
        new = f.with_name(f.stem + "-pdf3.js")
        new.write_text(n, encoding="utf-8")
        refs = [f.name, f.stem + "-pdf.js", f.stem + "-pdf2.js"]
        if any(r in html for r in refs):
            idx.with_name("index.html.yedek-pdf3").write_text(html, encoding="utf-8")
            for r in refs[::-1]:
                html = html.replace(r, new.name)
            idx.write_text(html, encoding="utf-8")
        out.append(f"{f.name} -> {new.name}: servis şartları imzanın ALTINA taşındı, tek sayfaya sığdırıldı (not:{c}, imza:{c3}, boşluk:{c4})")
    return {"ok": True, "sonuc": out or ["yamalanacak dosya bulunamadı"], "not": "Sayfayı Ctrl+F5 ile yenileyin."}

if _FE:
    import gzip as _gz
    from fastapi.responses import Response as _Resp
    _GZC = {}

    def _static_resp(request, f, hdr):
        """Statik dosya: ETag/304 + bir kez sıkıştırılıp bellekte tutulan gzip (1,8 MB'lık JS her istekte yeniden sıkıştırılmaz)."""
        try:
            st = f.stat()
            et = '"%x-%x"' % (int(st.st_mtime), st.st_size)
            h = dict(hdr, ETag=et, Vary="Accept-Encoding")
            if request.headers.get("if-none-match") == et:
                return _Resp(status_code=304, headers=h)
            if f.suffix in (".js", ".css", ".html", ".json", ".svg", ".txt", ".xml") and st.st_size > 2000 and "gzip" in request.headers.get("accept-encoding", ""):
                k = (str(f), et)
                z = _GZC.get(k)
                if z is None:
                    if len(_GZC) > 60:
                        _GZC.clear()
                    z = _GZC[k] = _gz.compress(f.read_bytes(), 6)
                import mimetypes as _mt
                return _Resp(z, media_type=(_mt.guess_type(str(f))[0] or "application/octet-stream"), headers=dict(h, **{"Content-Encoding": "gzip"}))
            return FileResponse(f, headers=h)
        except Exception:                                # noqa: BLE001
            return FileResponse(f, headers=hdr)

if _FE:
    from fastapi.responses import FileResponse, JSONResponse

    def _index_resp(request):
        """index.html: tek sayfalık servis fişi yaması (main.XXXX-pdf3.js) sunucuda varsa, depodan/yüklemeden gelen index.html onu göstermese bile ona yönlendirir."""
        try:
            import re as _re
            f = _FE / "index.html"
            html = f.read_text(encoding="utf-8")
            m = _re.search(r'static/js/(main\.[0-9a-f]+)(?:-pdf\d?)?\.js', html)
            if m and (_FE / "static" / "js" / (m.group(1) + "-pdf3.js")).is_file():
                _pf = _FE / "static" / "js" / (m.group(1) + "-pdf3.js")
                html = _re.sub(r'static/js/main\.[0-9a-f]+(?:-pdf\d?)?\.js', "static/js/" + m.group(1) + "-pdf3.js?v=" + str(int(_pf.stat().st_mtime)), html)
            return _Resp(html, media_type="text/html", headers={"Cache-Control": "no-cache"})
        except Exception:                                # noqa: BLE001
            return _static_resp(request, _FE / "index.html", {"Cache-Control": "no-cache"})

    @app.get("/demo/{rest:path}", include_in_schema=False)
    async def demo_site(rest: str, request: Request):
        """Test/örnek: /demo/<firma_id>~/magaza — firmanın yayınlanmış sitesini (mağaza dahil) platform adresinde gösterir."""
        import re as _r3
        if not tenant.current():
            return JSONResponse({"detail": "Bulunamadı"}, status_code=404)
        _f = await db.main().firms.find_one({"db": tenant.current()}, {"_id": 0, "id": 1})
        fid = (_f or {}).get("id")
        if not fid:
            return JSONResponse({"detail": "Bulunamadı"}, status_code=404)
        fn = getattr(api_router, "site_custom_serve", None)
        r = await fn("/" + rest.strip("/"), "") if fn else None
        if not r:
            return JSONResponse({"detail": "Sayfa bulunamadı"}, status_code=404)
        h = r[0]
        if r[1].startswith("text/html"):
            base = "/demo/" + fid + "~"
            h = _r3.sub(r"""(["'])/(magaza|hesabim)""", lambda x: x.group(1) + base + "/" + x.group(2), h)
            h = h.replace("fetch('/api'+p,o)", "fetch('/api'+p.replace(/([^\\/]+)$/,'" + fid + "~$1'),o)")
            h = h.replace("<head>", "<head><meta name=robots content=noindex>", 1)
        return _Resp(h, media_type=r[1], headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex"})

    @app.get("/tema-urun/{name}.jpg", include_in_schema=False)
    async def tema_urun_gorsel(name: str):
        """Tema örnek ürünlerinin gerçek fotoğrafları (themes/img/p)."""
        import re as _r3
        p = Path(__file__).resolve().parent.parent / "themes" / "img" / "p" / (name + ".jpg")
        if not _r3.fullmatch(r"[a-z]{3,12}[1-3]", name) or not p.is_file():
            return JSONResponse({"detail": "Bulunamadı"}, status_code=404)
        return _Resp(p.read_bytes(), media_type="image/jpeg", headers={"Cache-Control": "public, max-age=604800"})

    @app.get("/tema-onizleme/{slug}.html", include_in_schema=False)
    async def tema_onizleme(slug: str):
        """Satış sitesindeki tema vitrini: statik dosyası olmayan temalar doğrudan tema deposundan gösterilir (yeni sekmede canlı önizleme)."""
        import re as _r2
        p = Path(__file__).resolve().parent.parent / "themes" / "html" / (slug + ".html")
        if not _r2.fullmatch(r"[a-z0-9-]{3,60}", slug) or not p.is_file():
            return JSONResponse({"detail": "Bulunamadı"}, status_code=404)
        import sitegen as _sg2
        raw = p.read_text(encoding="utf-8")
        try:
            th = next((t for t in __import__("json").loads((Path(__file__).resolve().parent / "themes.json").read_text(encoding="utf-8")) if t["slug"] == slug), None)
            h = _sg2.preview_html(raw, th, slug) if th else raw
        except Exception:                                                     # noqa: BLE001
            h = raw
        return _Resp(_sg2.credit(h), media_type="text/html", headers={"Cache-Control": "public, max-age=300", "X-Robots-Tag": "noindex"})

    @app.get("/tema-onizleme/{slug}/{page}.html", include_in_schema=False)
    async def tema_onizleme_sayfa(slug: str, page: str):
        """Temanın iç sayfaları (hizmetler, süreç, SSS, iletişim...) aynı örnek verilerle."""
        import re as _r2
        p = Path(__file__).resolve().parent.parent / "themes" / "html" / (slug + ".html")
        if not _r2.fullmatch(r"[a-z0-9-]{3,60}", slug) or not _r2.fullmatch(r"[a-z0-9-]{2,60}", page) or not p.is_file():
            return JSONResponse({"detail": "Bulunamadı"}, status_code=404)
        import sitegen as _sg2
        try:
            th = next((t for t in __import__("json").loads((Path(__file__).resolve().parent / "themes.json").read_text(encoding="utf-8")) if t["slug"] == slug), None)
            h = _sg2.preview_html(p.read_text(encoding="utf-8"), th, slug, page) if th else None
        except Exception:                                                     # noqa: BLE001
            h = None
        if not h:
            return JSONResponse({"detail": "Bulunamadı"}, status_code=404)
        return _Resp(_sg2.credit(h), media_type="text/html", headers={"Cache-Control": "public, max-age=300", "X-Robots-Tag": "noindex"})

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str, request: Request):
        if full_path == "api" or full_path.startswith("api/"):
            return JSONResponse({"detail": "Bulunamadı"}, status_code=404)
        if full_path in ("", "index.html"):
            return _index_resp(request)
        f = (_FE / full_path).resolve()
        if full_path and _FE in f.parents and f.is_file():
            # G178: sürümlü ek dosyalar (panel-ek.js?v=N) her açılışta yeniden sorulmasın — sürüm değişince adres değişir
            _ver = bool(request.query_params.get("v")) and f.suffix in (".js", ".css") and f.name != "spx-sw.js"
            hdr = {"Cache-Control": "public, max-age=31536000, immutable"} if (full_path.startswith("static/") or _ver) else {"Cache-Control": "no-cache"}
            return _static_resp(request, f, hdr)
        return _index_resp(request)

@app.on_event("startup")
async def _demo_adlari():
    await demo.rename_old_demos(db)


@app.on_event("startup")
async def _pdf_yama_otomatik():
    """Servis fişi yaması (-pdf3.js) eski sürümse (işaretçi yoksa) açılışta kendiliğinden yeniler; hata olursa sessizce geçer."""
    try:
        fe = _panel_dir()
        if not fe:
            return
        for f in (fe / "static" / "js").glob("main.*-pdf3.js"):
            if "sp-pdf-v171" not in f.read_text(encoding="utf-8", errors="ignore")[-200:]:
                await pdf_yama("SPYENI2026")
                break
    except Exception:                                    # noqa: BLE001
        pass


@app.on_event("startup")
async def _firm_maint_start():
    try:
        if firms.MAINT_LOOP:
            asyncio.create_task(firms.MAINT_LOOP())
    except Exception:                                    # noqa: BLE001
        pass


@app.on_event("startup")
async def _market_auto_start():
    """Pazaryeri siparişleri otomatik düşsün (5 dk'da bir; markets_hub tek işçi kilidi kullanır)."""
    try:
        if os.environ.get('BACKGROUND_JOBS', '1') != '0' and os.environ.get('MARKET_AUTO', '1') != '0':
            import markets_hub
            app.state.market_auto = asyncio.create_task(markets_hub.auto_loop(db, firms, tenant))
    except Exception:                                    # noqa: BLE001
        pass


@app.on_event("shutdown")
async def shutdown_db_client():
    t = getattr(app.state, "sched", None)
    if t:
        t.cancel()
    client.close()
