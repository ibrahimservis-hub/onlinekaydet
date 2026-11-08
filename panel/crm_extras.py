"""
ServisPlus – Web entegrasyonu, CRM ve analitik modülü.

server.py içinden `register(...)` ile bağlanır. İçerik:
  * Public uçlar (kimlik doğrulama YOK): iletişim formu, bayilik başvurusu, yorum, ziyaretçi izleme
  * Admin uçları: mesajlar, bayilik başvuruları, garanti talepleri, yorumlar, duyurular,
    ziyaretçi / kanal analitiği, teknisyen performansı, admin kullanıcıları, bildirim sayaçları
"""
import asyncio
import re
import uuid
import time
import csv
import io
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from urllib.parse import urlparse, parse_qs

from fastapi import Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:  # tzdata yoksa sabit UTC+3
    TR = timezone(timedelta(hours=3))

# ------------------------------------------------------------------ sabitler
CHANNEL_LABELS = {
    "google_ads": "Google Ads (Reklam)",
    "meta_ads": "Meta Reklam (Instagram/Facebook)",
    "diger_reklam": "Diğer Reklam",
    "organik": "Organik Arama",
    "sosyal": "Sosyal Medya",
    "referans": "Referans Site",
    "direkt": "Direkt Giriş",
    # panelden elle girilebilen kanallar
    "telefon": "Telefon (Çağrı)",
    "whatsapp": "WhatsApp",
    "tavsiye": "Tavsiye",
    "tekrar_musteri": "Tekrar Müşteri",
    "bayi": "Bayi / İş Ortağı",
    "diger": "Diğer",
}
SEARCH_NAMES = ("google", "bing", "yandex", "duckduckgo", "yahoo", "ecosia", "baidu", "brave")
SOCIAL_DOMAINS = ("facebook.com", "fb.com", "fb.me", "instagram.com", "t.co", "twitter.com", "x.com", "youtube.com",
                  "youtu.be", "linkedin.com", "lnkd.in", "tiktok.com", "pinterest.com", "wa.me", "whatsapp.com",
                  "t.me", "telegram.org", "reddit.com")


def _host_is(host: str, domains) -> bool:
    return any(host == d or host.endswith("." + d) for d in domains)


BOT_RE = re.compile(
    r"bot|crawl|spider|slurp|lighthouse|pagespeed|chrome-lighthouse|headless|gtmetrix|pingdom|uptime|"
    r"monitor|facebookexternalhit|preview|curl|wget|python-requests|httpclient|go-http|java/|okhttp|"
    r"semrush|ahrefs|mj12|dotbot|petalbot|bytespider|amazonaws|google-read-aloud|adsbot|mediapartners", re.I)

MESSAGE_STATUSES = ["yeni", "okundu", "donus_yapildi", "isleme_alindi", "kapandi", "spam"]
DEALER_STATUSES = ["yeni", "inceleniyor", "gorusuldu", "onaylandi", "reddedildi"]
WARRANTY_STATUSES = ["acik", "inceleniyor", "serviste", "cozuldu", "reddedildi"]
ACTIVE_WINDOW_SEC = 5 * 60

# basit bellek içi hız sınırlayıcı
_RATE: dict = defaultdict(list)


def _rate_ok(key: str, limit: int, window: int) -> bool:
    now = time.time()
    arr = [t for t in _RATE[key] if now - t < window]
    if len(arr) >= limit:
        _RATE[key] = arr
        return False
    arr.append(now)
    _RATE[key] = arr
    if len(_RATE) > 20000:  # bellek sızıntısına karşı
        for k in list(_RATE.keys())[:5000]:
            _RATE.pop(k, None)
    return True


def client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    real = request.headers.get("x-real-ip", "")
    if real:
        return real.strip()
    return request.client.host if request.client else ""


def mask_ip(ip: str) -> str:
    """KVKK dostu: IPv4'ün son oktetini, IPv6'nın son bloklarını gizler."""
    if not ip:
        return ""
    if ":" in ip:
        parts = ip.split(":")
        return ":".join(parts[:3]) + ":…"
    p = ip.split(".")
    return ".".join(p[:3]) + ".x" if len(p) == 4 else ip


def parse_ua(ua: str) -> dict:
    u = ua or ""
    low = u.lower()
    if "ipad" in low or "tablet" in low:
        device = "tablet"
    elif "mobi" in low or "android" in low or "iphone" in low:
        device = "mobil"
    else:
        device = "masaüstü"
    if "edg/" in low or "edge/" in low:
        browser = "Edge"
    elif "opr/" in low or "opera" in low:
        browser = "Opera"
    elif "samsungbrowser" in low:
        browser = "Samsung Browser"
    elif "firefox" in low:
        browser = "Firefox"
    elif "chrome" in low or "crios" in low:
        browser = "Chrome"
    elif "safari" in low:
        browser = "Safari"
    else:
        browser = "Diğer"
    if "windows" in low:
        os_ = "Windows"
    elif "android" in low:
        os_ = "Android"
    elif "iphone" in low or "ipad" in low or "ios" in low:
        os_ = "iOS"
    elif "mac os" in low or "macintosh" in low:
        os_ = "macOS"
    elif "linux" in low:
        os_ = "Linux"
    else:
        os_ = "Diğer"
    return {"device": device, "browser": browser, "os": os_}


def classify_channel(search: str, referrer: str, own_host: str = "") -> dict:
    """Ziyaretin geldiği kanalı belirler (ilk dokunuş)."""
    q = {k.lower(): v[0] for k, v in parse_qs((search or "").lstrip("?")).items() if v}
    utm_source = (q.get("utm_source") or "").lower()
    utm_medium = (q.get("utm_medium") or "").lower()
    campaign = q.get("utm_campaign") or ""
    term = q.get("utm_term") or q.get("keyword") or ""
    ref_host = ""
    if referrer:
        try:
            ref_host = (urlparse(referrer).hostname or "").lower().replace("www.", "")
        except Exception:
            ref_host = ""
    if own_host and ref_host == own_host.replace("www.", ""):
        ref_host = ""  # iç yönlendirme = referrer yok

    paid_medium = utm_medium in ("cpc", "ppc", "paid", "paidsearch", "paid_search", "display", "pmax", "ads", "cpm")
    has_gclid = any(k in q for k in ("gclid", "gbraid", "wbraid", "gad_source", "gad_campaignid"))
    has_fbclid = "fbclid" in q

    if has_gclid or (paid_medium and utm_source in ("google", "adwords")):
        return {"channel": "google_ads", "source_name": "google", "medium": "cpc",
                "campaign": campaign or q.get("gad_campaignid", ""), "term": term, "click_id": True}
    if (has_fbclid and paid_medium) or (utm_source in ("facebook", "instagram", "meta", "fb", "ig") and paid_medium):
        return {"channel": "meta_ads", "source_name": utm_source or "meta", "medium": "paid",
                "campaign": campaign, "term": term, "click_id": has_fbclid}
    if paid_medium:
        return {"channel": "diger_reklam", "source_name": utm_source or ref_host or "bilinmiyor", "medium": utm_medium,
                "campaign": campaign, "term": term, "click_id": False}
    if utm_medium in ("organic", "seo"):
        return {"channel": "organik", "source_name": utm_source or ref_host or "arama", "medium": "organic",
                "campaign": campaign, "term": term, "click_id": False}
    if utm_medium in ("social", "sosyal") or (ref_host and _host_is(ref_host, SOCIAL_DOMAINS)):
        name = utm_source or ref_host.split(".")[-2 if ref_host.count(".") else 0]
        return {"channel": "sosyal", "source_name": name, "medium": "social", "campaign": campaign,
                "term": term, "click_id": False}
    if ref_host:
        labels = ref_host.split(".")[:-1] or [ref_host]
        hit = next((n for n in SEARCH_NAMES if n in labels), None)
        if hit:
            return {"channel": "organik", "source_name": hit, "medium": "organic", "campaign": campaign,
                    "term": term, "click_id": False}
    if ref_host:
        return {"channel": "referans", "source_name": ref_host, "medium": "referral", "campaign": campaign,
                "term": term, "click_id": False}
    if utm_source:
        return {"channel": "referans", "source_name": utm_source, "medium": utm_medium or "link",
                "campaign": campaign, "term": term, "click_id": False}
    return {"channel": "direkt", "source_name": "direkt", "medium": "none", "campaign": "", "term": "",
            "click_id": False}


def tr_now() -> datetime:
    return datetime.now(timezone.utc).astimezone(TR)


def tr_day(dt: Optional[datetime] = None) -> str:
    return (dt or tr_now()).astimezone(TR).strftime("%Y-%m-%d")


def clean_phone(p: str) -> str:
    return re.sub(r"[^\d+]", "", p or "")


def valid_tr_phone(p: str) -> bool:
    d = re.sub(r"\D", "", p or "")
    return 10 <= len(d) <= 13


# ------------------------------------------------------------------ modeller
class ContactIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=30)
    email: Optional[str] = Field(default="", max_length=160)
    city: Optional[str] = Field(default="", max_length=80)
    district: Optional[str] = Field(default="", max_length=80)
    device_type: Optional[str] = Field(default="", max_length=60)
    brand: Optional[str] = Field(default="", max_length=60)
    type: Optional[str] = Field(default="servis_talebi", max_length=30)
    message: Optional[str] = Field(default="", max_length=3000)
    sid: Optional[str] = Field(default="", max_length=80)
    page: Optional[str] = Field(default="", max_length=300)
    website: Optional[str] = ""  # honeypot


class DealerIn(BaseModel):
    company: str = Field(min_length=2, max_length=160)
    contact_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=30)
    email: Optional[str] = Field(default="", max_length=160)
    city: str = Field(min_length=2, max_length=80)
    district: Optional[str] = Field(default="", max_length=5000)
    service_types: Optional[str] = Field(default="", max_length=1000)
    districts: Optional[List[str]] = None            # seçilen ilçeler (liste)
    service_groups: Optional[List[str]] = None       # kombi, klima, beyaz-esya, televizyon, sofben, ocak-firin, diger
    brands: Optional[str] = Field(default="", max_length=1000)
    experience_years: Optional[int] = 0
    has_vehicle: Optional[bool] = False
    message: Optional[str] = Field(default="", max_length=3000)
    sid: Optional[str] = Field(default="", max_length=80)
    page: Optional[str] = Field(default="", max_length=300)
    website: Optional[str] = ""
    contract_accepted: Optional[bool] = False       # İş Ortağı Sözleşmesi + Gizlilik Taahhütnamesi onayı
    contract_ver: Optional[str] = Field(default="", max_length=10)


class ReviewIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default="", max_length=1500)
    city: Optional[str] = Field(default="", max_length=80)
    job_number: Optional[str] = Field(default="", max_length=30)
    website: Optional[str] = ""


class TrackIn(BaseModel):
    sid: str = Field(min_length=8, max_length=80)
    event: str = "pageview"  # pageview | ping | event
    path: Optional[str] = Field(default="/", max_length=400)
    title: Optional[str] = Field(default="", max_length=200)
    referrer: Optional[str] = Field(default="", max_length=600)
    search: Optional[str] = Field(default="", max_length=800)
    host: Optional[str] = Field(default="", max_length=120)
    label: Optional[str] = Field(default="", max_length=120)
    screen: Optional[str] = Field(default="", max_length=20)
    lang: Optional[str] = Field(default="", max_length=20)


class StatusNote(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None
    assigned_to: Optional[str] = None


class ConvertIn(BaseModel):
    technician_id: Optional[str] = ""
    brand_id: Optional[str] = ""
    device_type: Optional[str] = ""
    priority: Optional[str] = "normal"
    scheduled_at: Optional[str] = ""
    fault_description: Optional[str] = ""
    source_channel: Optional[str] = ""


_DEALER_GROUPS = ("kombi", "klima", "beyaz-esya", "televizyon", "sofben", "ocak-firin", "diger")


def _groups_from_text(t):
    t = (t or "").lower()
    m = [("kombi", "kombi"), ("klima", "klima"), ("beyaz", "beyaz-esya"), ("tv", "televizyon"), ("televizyon", "televizyon"), ("şofben", "sofben"), ("sofben", "sofben"), ("fırın", "ocak-firin"), ("ocak", "ocak-firin")]
    out = []
    for k, g in m:
        if k in t and g not in out:
            out.append(g)
    return out


class DealerTechIn(BaseModel):
    email: Optional[str] = ""
    password: Optional[str] = ""
    commission_percent: float = 30.0


class WarrantyIn(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    customer_phone: Optional[str] = ""
    job_number: Optional[str] = ""
    device: Optional[str] = ""
    issue: str = Field(min_length=2, max_length=2000)
    status: Optional[str] = "acik"
    note: Optional[str] = ""
    warranty_until: Optional[str] = ""


class WarrantyUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    job_number: Optional[str] = None
    device: Optional[str] = None
    issue: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None
    warranty_until: Optional[str] = None


class ReviewUpdate(BaseModel):
    status: Optional[str] = None  # beklemede | yayinda | gizli
    reply: Optional[str] = None


class AnnouncementIn(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    body: Optional[str] = Field(default="", max_length=3000)
    level: Optional[str] = "bilgi"  # bilgi | uyari | onemli
    audience: Optional[str] = "teknisyen"  # teknisyen | admin | hepsi
    is_active: bool = True
    expires_at: Optional[str] = ""
    image_url: Optional[str] = ""
    popup: bool = True          # usta ekranında açılır pencere olarak göster
    target_ids: Optional[List[str]] = []   # boşsa tüm ustalar; doluysa yalnızca bu ustalar


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    level: Optional[str] = None
    audience: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[str] = None
    image_url: Optional[str] = None
    popup: Optional[bool] = None
    target_ids: Optional[List[str]] = None


class AdminUserIn(BaseModel):
    email: str
    password: str = Field(min_length=6)
    name: str = Field(min_length=2, max_length=100)
    phone: Optional[str] = ""
    admin_role: Optional[str] = "owner"


class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=6)


# ------------------------------------------------------------------ kayıt
def register(api_router, db, deps: dict):
    get_current_user = deps["get_current_user"]
    require_admin = deps["require_admin"]
    now_iso = deps["now_iso"]
    hash_password = deps["hash_password"]
    quick_create_job = deps["quick_create_job"]

    def new_id() -> str:
        return str(uuid.uuid4())

    async def source_from_sid(sid: str) -> dict:
        if not sid:
            return {}
        s = await db.visitor_sessions.find_one({"id": sid}, {"_id": 0})
        if not s:
            return {}
        return {
            "channel": s.get("channel", ""), "source_name": s.get("source_name", ""),
            "medium": s.get("medium", ""), "campaign": s.get("campaign", ""),
            "term": s.get("term", ""), "landing_page": s.get("landing_page", ""),
            "referrer": s.get("referrer", ""), "device": s.get("device", ""),
        }

    async def mark_converted(sid: str, kind: str):
        if not sid:
            return
        await db.visitor_sessions.update_one(
            {"id": sid},
            {"$set": {"converted": True}, "$inc": {f"conv_{kind}": 1}},
        )

    def guard_public(request: Request, bucket: str, limit: int, window: int):
        ip = client_ip(request)
        if not _rate_ok(f"{bucket}:{ip}", limit, window):
            raise HTTPException(status_code=429, detail="Çok fazla istek. Lütfen biraz sonra tekrar deneyin.")
        return ip

    # ============================================================ PUBLIC
    @api_router.post("/public/contact")
    async def public_contact(payload: ContactIn, request: Request):
        ip = guard_public(request, "contact", 20, 600)
        if payload.website:  # honeypot dolu -> sessizce başarılı say
            return {"ok": True}
        if not valid_tr_phone(payload.phone):
            raise HTTPException(status_code=422, detail="Lütfen geçerli bir telefon numarası girin.")
        src = await source_from_sid(payload.sid)
        doc = {
            "id": new_id(),
            "type": payload.type if payload.type in ("servis_talebi", "bilgi", "sikayet", "diger") else "servis_talebi",
            "name": payload.name.strip(), "phone": clean_phone(payload.phone),
            "email": (payload.email or "").strip(), "city": (payload.city or "").strip(),
            "district": (payload.district or "").strip(), "device_type": (payload.device_type or "").strip(),
            "brand": (payload.brand or "").strip(), "message": (payload.message or "").strip(),
            "status": "yeni", "note": "", "job_id": "", "job_number": "",
            "source": src, "channel": src.get("channel", ""),
            "page": payload.page or "", "sid": payload.sid or "",
            "ip": mask_ip(ip), "ua": request.headers.get("user-agent", "")[:200],
            "created_at": now_iso(), "updated_at": now_iso(),
        }
        await db.contact_messages.insert_one(doc)
        await mark_converted(payload.sid, "form")
        import notify as _n
        await _n.push_admins_t(db, "Yeni iletişim mesajı", f"{doc.get('name', '')} · {doc.get('phone', '')}", "/admin/messages")
        return {"ok": True, "id": doc["id"]}

    @api_router.post("/public/dealer-application")
    async def public_dealer(payload: DealerIn, request: Request):
        ip = guard_public(request, "dealer", 4, 900)
        if payload.website:
            return {"ok": True}
        if not valid_tr_phone(payload.phone):
            raise HTTPException(status_code=422, detail="Lütfen geçerli bir telefon numarası girin.")
        if not payload.contract_accepted:
            raise HTTPException(status_code=422, detail="Devam etmek için İş Ortağı Sözleşmesi ve Gizlilik Taahhütnamesi’ni onaylamanız gerekir.")
        src = await source_from_sid(payload.sid)
        doc = {
            "contract": {"accepted": True, "ver": (payload.contract_ver or "1")[:10], "at": now_iso(), "ua": request.headers.get("user-agent", "")[:200]},
            "id": new_id(), "company": payload.company.strip(), "contact_name": payload.contact_name.strip(),
            "phone": clean_phone(payload.phone), "email": (payload.email or "").strip(),
            "city": payload.city.strip(), "district": (payload.district or "").strip()[:2000],
            "service_types": (payload.service_types or "").strip(), "message": (payload.message or "").strip(),
            "districts": [str(x).strip()[:60] for x in (payload.districts or []) if str(x).strip()][:60],
            "service_groups": [g for g in (payload.service_groups or []) if g in _DEALER_GROUPS][:10],
            "brands": (payload.brands or "").strip()[:300], "experience_years": max(0, min(60, int(payload.experience_years or 0))),
            "has_vehicle": bool(payload.has_vehicle),
            "status": "yeni", "notes": "", "technician_id": "",
            "source": src, "channel": src.get("channel", ""), "page": payload.page or "", "sid": payload.sid or "",
            "ip": mask_ip(ip), "created_at": now_iso(), "updated_at": now_iso(),
        }
        await db.dealer_applications.insert_one(doc)
        await mark_converted(payload.sid, "dealer")
        import notify as _n
        await _n.push_admins_t(db, "Yeni usta/bayi başvurusu", f"{doc.get('contact_name') or doc.get('company', '')} · {doc.get('phone', '')}", "/admin/dealers")
        return {"ok": True, "id": doc["id"]}

    @api_router.post("/public/review")
    async def public_review(payload: ReviewIn, request: Request):
        guard_public(request, "review", 3, 900)
        if payload.website:
            return {"ok": True}
        doc = {
            "id": new_id(), "name": payload.name.strip(), "rating": payload.rating,
            "comment": (payload.comment or "").strip(), "city": (payload.city or "").strip(),
            "job_number": (payload.job_number or "").strip(), "status": "beklemede", "reply": "",
            "origin": "site", "created_at": now_iso(),
        }
        await db.reviews.insert_one(doc)
        import notify as _n
        await _n.push_admins_t(db, "Yeni müşteri yorumu", f"{doc.get('name', '')} · {doc.get('rating', '')}★ {str(doc.get('comment', ''))[:120]}".strip(), "/admin/reviews")
        return {"ok": True}

    @api_router.get("/public/reviews")
    async def public_reviews(limit: int = 20):
        return await db.reviews.find({"status": "yayinda"}, {"_id": 0, "ip": 0}).sort("created_at", -1).to_list(min(limit, 50))

    @api_router.post("/public/track")
    async def public_track(payload: TrackIn, request: Request):
        ua = request.headers.get("user-agent", "")
        if not ua or BOT_RE.search(ua):
            return {"ok": True, "bot": True}
        ip = client_ip(request)
        if not _rate_ok(f"track:{ip}", 240, 60):
            return {"ok": True, "limited": True}
        now = datetime.now(timezone.utc)
        now_s = now.isoformat()
        tr = now.astimezone(TR)
        sid = payload.sid
        sess = await db.visitor_sessions.find_one({"id": sid}, {"_id": 0})

        if not sess:
            ch = classify_channel(payload.search or "", payload.referrer or "", payload.host or "")
            sess = {
                "id": sid, "first_seen": now_s, "last_seen": now_s, "day": tr_day(tr), "hour": tr.hour,
                **ch, **parse_ua(ua),
                "referrer": (payload.referrer or "")[:300], "landing_page": (payload.path or "/")[:300],
                "landing_query": (payload.search or "")[:400],
                "ip": mask_ip(ip), "screen": payload.screen or "", "lang": payload.lang or "",
                "pages_count": 0, "duration_sec": 0, "converted": False,
                "conv_call": 0, "conv_whatsapp": 0, "conv_form": 0, "conv_dealer": 0,
                "pages": [], "events": [],
            }
            await db.visitor_sessions.insert_one(dict(sess))

        # süre: ilk/son görülme farkı (60 dk üstü kopuk kabul edilir)
        try:
            first = datetime.fromisoformat(sess["first_seen"])
            dur = int((now - first).total_seconds())
        except Exception:
            dur = sess.get("duration_sec", 0)
        dur = max(0, min(dur, 6 * 3600))

        upd = {"$set": {"last_seen": now_s, "duration_sec": dur}}
        if payload.event == "pageview":
            upd["$inc"] = {"pages_count": 1}
            upd["$push"] = {"pages": {"$each": [{"path": (payload.path or "/")[:300], "title": (payload.title or "")[:120],
                                                 "ts": now_s}], "$slice": -40}}
            await db.pageviews.insert_one({
                "sid": sid, "path": (payload.path or "/")[:300], "title": (payload.title or "")[:120],
                "ts": now_s, "ts_dt": now, "day": tr_day(tr), "hour": tr.hour,
                "channel": sess.get("channel", ""), "device": sess.get("device", ""),
            })
        elif payload.event == "event":
            label = payload.label or ""
            inc_key = None
            if label == "call_click":
                inc_key = "conv_call"
            elif label == "whatsapp_click":
                inc_key = "conv_whatsapp"
            upd["$push"] = {"events": {"$each": [{"type": label, "ts": now_s, "path": (payload.path or "")[:200]}],
                                       "$slice": -40}}
            if inc_key:
                upd["$inc"] = {inc_key: 1}
                upd["$set"]["converted"] = True
            await db.track_events.insert_one({
                "sid": sid, "label": label, "path": (payload.path or "")[:300], "ts": now_s, "day": tr_day(tr),
                "channel": sess.get("channel", ""),
            })
        await db.visitor_sessions.update_one({"id": sid}, upd)
        return {"ok": True}

    # ============================================================ ADMIN: MESAJLAR
    @api_router.get("/messages")
    async def list_messages(status: Optional[str] = None, type: Optional[str] = None, q: Optional[str] = None,
                            _: dict = Depends(require_admin)):
        query = {}
        if status:
            query["status"] = status
        if type:
            query["type"] = type
        if q:
            rx = {"$regex": re.escape(q), "$options": "i"}
            query["$or"] = [{"name": rx}, {"phone": rx}, {"message": rx}, {"city": rx}]
        return await db.contact_messages.find(query, {"_id": 0}).sort("created_at", -1).to_list(2000)

    @api_router.put("/messages/{mid}")
    async def update_message(mid: str, payload: StatusNote, _: dict = Depends(require_admin)):
        upd = {k: v for k, v in payload.model_dump().items() if v is not None}
        if "status" in upd and upd["status"] not in MESSAGE_STATUSES:
            raise HTTPException(status_code=400, detail="Geçersiz durum")
        upd["updated_at"] = now_iso()
        res = await db.contact_messages.update_one({"id": mid}, {"$set": upd})
        if not res.matched_count:
            raise HTTPException(status_code=404, detail="Mesaj bulunamadı")
        return await db.contact_messages.find_one({"id": mid}, {"_id": 0})

    @api_router.delete("/messages/{mid}")
    async def delete_message(mid: str, _: dict = Depends(require_admin)):
        await db.contact_messages.delete_one({"id": mid})
        return {"ok": True}

    @api_router.post("/messages/{mid}/convert")
    async def convert_message(mid: str, payload: ConvertIn, user: dict = Depends(require_admin)):
        m = await db.contact_messages.find_one({"id": mid}, {"_id": 0})
        if not m:
            raise HTTPException(status_code=404, detail="Mesaj bulunamadı")
        if m.get("job_id"):
            raise HTTPException(status_code=400, detail="Bu mesaj zaten servis kaydına dönüştürülmüş")
        existing = await db.customers.find_one({"phone": m["phone"]}, {"_id": 0})
        channel = payload.source_channel or m.get("channel") or ""
        body = {
            "fault_description": payload.fault_description or m.get("message") or "Web formundan gelen servis talebi",
            "assigned_technician_id": payload.technician_id or "",
            "priority": payload.priority or "normal",
            "scheduled_at": payload.scheduled_at or "",
            "source_channel": channel,
            "source_detail": (m.get("source") or {}).get("campaign") or (m.get("source") or {}).get("source_name", ""),
        }
        if existing:
            body["customer_id"] = existing["id"]
        else:
            body.update({"customer_name": m["name"], "customer_phone": m["phone"], "customer_email": m.get("email", ""),
                         "customer_city": m.get("city", ""), "customer_district": m.get("district", "")})
        if payload.brand_id:
            body["brand_id"] = payload.brand_id
            body["device_type"] = payload.device_type or "kombi"
        job = await quick_create_job(body, user)
        # müşteriye kanal bilgisini yaz
        await db.customers.update_one(
            {"id": job["customer_id"], "source_channel": {"$in": [None, ""]}},
            {"$set": {"source_channel": channel}},
        )
        await db.contact_messages.update_one(
            {"id": mid},
            {"$set": {"job_id": job["id"], "job_number": job["job_number"], "status": "isleme_alindi",
                      "updated_at": now_iso()}},
        )
        return job

    # ============================================================ ADMIN: BAYİLİK
    @api_router.get("/dealers")
    async def list_dealers(status: Optional[str] = None, q: Optional[str] = None, _: dict = Depends(require_admin)):
        query = {}
        if status:
            query["status"] = status
        if q:
            rx = {"$regex": re.escape(q), "$options": "i"}
            query["$or"] = [{"company": rx}, {"contact_name": rx}, {"phone": rx}, {"city": rx}]
        rows = await db.dealer_applications.find(query, {"_id": 0}).sort("created_at", -1).to_list(2000)
        techs = {u["id"]: u for u in await db.users.find({"role": "technician"}, {"_id": 0, "password_hash": 0}).to_list(2000)}
        for r in rows:
            u = techs.get(r.get("technician_id") or "")
            r["technician_active"] = bool(u and u.get("is_active", True))
            r["technician_email"] = u.get("email", "") if u else ""
            if r.get("technician_id") and not u:
                r["technician_id"] = ""   # usta silinmiş
        return rows

    @api_router.put("/dealers/{did}")
    async def update_dealer(did: str, payload: StatusNote, _: dict = Depends(require_admin)):
        upd = {}
        if payload.status is not None:
            if payload.status not in DEALER_STATUSES:
                raise HTTPException(status_code=400, detail="Geçersiz durum")
            upd["status"] = payload.status
        if payload.note is not None:
            upd["notes"] = payload.note
        upd["updated_at"] = now_iso()
        res = await db.dealer_applications.update_one({"id": did}, {"$set": upd})
        if not res.matched_count:
            raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
        return await db.dealer_applications.find_one({"id": did}, {"_id": 0})

    @api_router.delete("/dealers/{did}")
    async def delete_dealer(did: str, _: dict = Depends(require_admin)):
        await db.dealer_applications.delete_one({"id": did})
        return {"ok": True}

    @api_router.post("/dealers/{did}/create-technician")
    async def dealer_to_technician(did: str, payload: DealerTechIn, _: dict = Depends(require_admin)):
        d = await db.dealer_applications.find_one({"id": did}, {"_id": 0})
        if not d:
            raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
        if d.get("technician_id"):
            raise HTTPException(status_code=400, detail="Bu başvuru için hesap zaten oluşturulmuş")
        import secrets
        digits = re.sub(r"\D", "", d.get("phone") or "")[-10:] or secrets.token_hex(3)
        email = (payload.email or f"usta{digits}@servisplus.net.tr").lower().strip()
        if await db.users.find_one({"email": email}):
            raise HTTPException(status_code=400, detail="Bu e-posta ile kayıtlı bir kullanıcı var")
        password = (payload.password or "").strip() or secrets.token_urlsafe(6)
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalı")
        uid = new_id()
        await db.users.insert_one({
            "id": uid, "email": email, "password_hash": hash_password(password),
            "name": d["company"], "phone": d["phone"], "role": "technician",
            "commission_percent": payload.commission_percent, "is_active": True,
            "dealer_application_id": did, "created_at": now_iso(),
            "partner_contract": d.get("contract") or {},
            # Başvurudaki bilgiler usta detayına aktarılır (il / ilçeler / servis grupları / marka / deneyim / araç)
            "profile": {"city": d.get("city") if d.get("city") not in (None, "-") else "", "districts": list(d.get("districts") or [x.strip() for x in re.split(r"[,;/]", d.get("district") or "") if x.strip()]),
                        "service_groups": list(d.get("service_groups") or _groups_from_text(d.get("service_types") or "")), "brands": [x.strip() for x in re.split(r"[,;]", d.get("brands") or "") if x.strip()][:30],
                        "experience_years": int(d.get("experience_years") or 0), "has_vehicle": bool(d.get("has_vehicle")),
                        "work_hours": "", "address": "", "start_date": now_iso()[:10], "updated_at": now_iso()},
        })
        if (d.get("message") or "").strip():
            await db.technician_notes.update_one({"tech_id": uid}, {"$set": {"tech_id": uid, "note": ("Başvuru notu: " + d["message"].strip())[:3000], "updated_at": now_iso()}}, upsert=True)
        await db.dealer_applications.update_one(
            {"id": did}, {"$set": {"technician_id": uid, "status": "onaylandi", "updated_at": now_iso()}})
        try:
            import notify as _nt
            asyncio.create_task(_nt.tech_welcome(db, {"id": uid, "email": email, "name": d["company"], "phone": d["phone"]}, password))
        except Exception:                                  # noqa: BLE001
            pass
        return {"ok": True, "technician_id": uid, "email": email, "password": password, "name": d["company"]}

    # ============================================================ ADMIN: GARANTİ
    @api_router.get("/warranty-claims")
    async def list_warranty(status: Optional[str] = None, _: dict = Depends(require_admin)):
        q = {"status": status} if status else {}
        return await db.warranty_claims.find(q, {"_id": 0}).sort("created_at", -1).to_list(2000)

    @api_router.post("/warranty-claims")
    async def create_warranty(payload: WarrantyIn, _: dict = Depends(require_admin)):
        doc = payload.model_dump()
        if doc["status"] not in WARRANTY_STATUSES:
            doc["status"] = "acik"
        doc.update({"id": new_id(), "created_at": now_iso(), "updated_at": now_iso()})
        await db.warranty_claims.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.put("/warranty-claims/{wid}")
    async def update_warranty(wid: str, payload: WarrantyUpdate, _: dict = Depends(require_admin)):
        upd = {k: v for k, v in payload.model_dump().items() if v is not None}
        if "status" in upd and upd["status"] not in WARRANTY_STATUSES:
            raise HTTPException(status_code=400, detail="Geçersiz durum")
        upd["updated_at"] = now_iso()
        res = await db.warranty_claims.update_one({"id": wid}, {"$set": upd})
        if not res.matched_count:
            raise HTTPException(status_code=404, detail="Talep bulunamadı")
        return await db.warranty_claims.find_one({"id": wid}, {"_id": 0})

    @api_router.delete("/warranty-claims/{wid}")
    async def delete_warranty(wid: str, _: dict = Depends(require_admin)):
        await db.warranty_claims.delete_one({"id": wid})
        return {"ok": True}

    # ============================================================ ADMIN: YORUMLAR
    @api_router.get("/reviews")
    async def list_reviews(status: Optional[str] = None, _: dict = Depends(require_admin)):
        q = {"status": status} if status else {}
        items = await db.reviews.find(q, {"_id": 0}).sort("created_at", -1).to_list(2000)
        all_r = await db.reviews.find({}, {"_id": 0, "rating": 1}).to_list(5000)
        avg = round(sum(r["rating"] for r in all_r) / len(all_r), 2) if all_r else 0
        # servis kayıtlarındaki müşteri puanları
        jobs = await db.service_jobs.find({"customer_rating": {"$gt": 0}}, {"_id": 0, "customer_rating": 1}).to_list(5000)
        javg = round(sum(j["customer_rating"] for j in jobs) / len(jobs), 2) if jobs else 0
        return {"items": items, "avg": avg, "count": len(all_r), "job_rating_avg": javg, "job_rating_count": len(jobs)}

    @api_router.post("/reviews")
    async def create_review(payload: ReviewIn, _: dict = Depends(require_admin)):
        doc = payload.model_dump()
        doc.pop("website", None)
        doc.update({"id": new_id(), "status": "yayinda", "reply": "", "origin": "panel", "created_at": now_iso()})
        await db.reviews.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.put("/reviews/{rid}")
    async def update_review(rid: str, payload: ReviewUpdate, _: dict = Depends(require_admin)):
        upd = {k: v for k, v in payload.model_dump().items() if v is not None}
        if "status" in upd and upd["status"] not in ("beklemede", "yayinda", "gizli"):
            raise HTTPException(status_code=400, detail="Geçersiz durum")
        res = await db.reviews.update_one({"id": rid}, {"$set": upd})
        if not res.matched_count:
            raise HTTPException(status_code=404, detail="Yorum bulunamadı")
        return await db.reviews.find_one({"id": rid}, {"_id": 0})

    @api_router.delete("/reviews/{rid}")
    async def delete_review(rid: str, _: dict = Depends(require_admin)):
        await db.reviews.delete_one({"id": rid})
        return {"ok": True}

    # ============================================================ DUYURULAR
    @api_router.get("/announcements")
    async def list_announcements(_: dict = Depends(require_admin)):
        items = await db.announcements.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
        total = await db.users.count_documents({"role": "technician", "is_active": {"$ne": False}})
        for a in items:
            a["read_count"] = await db.announcement_reads.count_documents({"announcement_id": a["id"]})
            a["audience_count"] = len(a.get("target_ids") or []) or total
        return items

    @api_router.get("/announcements/{aid}/reads")
    async def announcement_reads(aid: str, _: dict = Depends(require_admin)):
        reads = await db.announcement_reads.find({"announcement_id": aid}, {"_id": 0}).to_list(1000)
        names = {u["id"]: u["name"] for u in await db.users.find({"role": "technician"}, {"_id": 0}).to_list(2000)}
        return [{"user_id": r["user_id"], "name": names.get(r["user_id"], "?"), "at": r["at"]} for r in reads]

    @api_router.get("/announcements/active")
    async def active_announcements(user: dict = Depends(get_current_user)):
        now = now_iso()
        items = await db.announcements.find({"is_active": True}, {"_id": 0}).sort("created_at", -1).to_list(100)
        role = user.get("role")
        reads = {r["announcement_id"] for r in await db.announcement_reads.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)}
        out = []
        for a in items:
            if a.get("expires_at") and a["expires_at"] < now[:10]:
                continue
            aud = a.get("audience", "teknisyen")
            if not (aud == "hepsi" or (aud == "teknisyen" and role == "technician") or (aud == "admin" and role == "admin")):
                continue
            tg = a.get("target_ids") or []
            if role == "technician" and tg and user["id"] not in tg:
                continue
            a["read"] = a["id"] in reads
            out.append(a)
        return out

    @api_router.post("/announcements/{aid}/read")
    async def mark_announcement_read(aid: str, user: dict = Depends(get_current_user)):
        await db.announcement_reads.update_one({"announcement_id": aid, "user_id": user["id"]},
                                               {"$set": {"announcement_id": aid, "user_id": user["id"], "at": now_iso()}}, upsert=True)
        return {"ok": True}

    @api_router.post("/announcements")
    async def create_announcement(payload: AnnouncementIn, user: dict = Depends(require_admin)):
        doc = payload.model_dump()
        doc.update({"id": new_id(), "created_at": now_iso(), "created_by": user["name"]})
        await db.announcements.insert_one(doc)
        doc.pop("_id", None)
        try:
            import asyncio, fieldops
            ids = doc.get("target_ids") or [u["id"] async for u in db.users.find({"role": "technician", "is_active": {"$ne": False}}, {"id": 1})]
            asyncio.create_task(fieldops.push_to(db, ids, "Yeni duyuru", doc.get("title", ""), "/tech/announcements"))
        except Exception:
            pass
        return doc

    @api_router.put("/announcements/{aid}")
    async def update_announcement(aid: str, payload: AnnouncementUpdate, _: dict = Depends(require_admin)):
        upd = {k: v for k, v in payload.model_dump().items() if v is not None}
        res = await db.announcements.update_one({"id": aid}, {"$set": upd})
        if not res.matched_count:
            raise HTTPException(status_code=404, detail="Duyuru bulunamadı")
        return await db.announcements.find_one({"id": aid}, {"_id": 0})

    @api_router.delete("/announcements/{aid}")
    async def delete_announcement(aid: str, _: dict = Depends(require_admin)):
        await db.announcements.delete_one({"id": aid})
        await db.announcement_reads.delete_many({"announcement_id": aid})
        return {"ok": True}

    # ============================================================ ANALİTİK
    @api_router.get("/analytics/live")
    async def analytics_live(_: dict = Depends(require_admin)):
        since = (datetime.now(timezone.utc) - timedelta(seconds=ACTIVE_WINDOW_SEC)).isoformat()
        items = await db.visitor_sessions.find({"last_seen": {"$gte": since}}, {"_id": 0, "events": 0}) \
            .sort("last_seen", -1).to_list(200)
        for s in items:
            s["current_page"] = (s.get("pages") or [{}])[-1].get("path", s.get("landing_page", ""))
            s.pop("pages", None)
            s["channel_label"] = CHANNEL_LABELS.get(s.get("channel"), s.get("channel"))
        return {"active": len(items), "sessions": items}

    @api_router.get("/analytics/overview")
    async def analytics_overview(days: int = Query(7, ge=1, le=180), _: dict = Depends(require_admin)):
        today = tr_now()
        start_day = tr_day(today - timedelta(days=days - 1))
        day_list = [tr_day(today - timedelta(days=i)) for i in range(days - 1, -1, -1)]

        sessions = await db.visitor_sessions.find({"day": {"$gte": start_day}}, {"_id": 0, "pages": 0, "events": 0}) \
            .to_list(50000)
        today_key, yest_key = tr_day(today), tr_day(today - timedelta(days=1))
        week_key = tr_day(today - timedelta(days=6))
        month_key = tr_day(today - timedelta(days=29))

        # bugün / dün / hafta / ay (aralıktan bağımsız)
        cnt_today = await db.visitor_sessions.count_documents({"day": today_key})
        cnt_yest = await db.visitor_sessions.count_documents({"day": yest_key})
        cnt_week = await db.visitor_sessions.count_documents({"day": {"$gte": week_key}})
        cnt_month = await db.visitor_sessions.count_documents({"day": {"$gte": month_key}})
        pv_today = await db.pageviews.count_documents({"day": today_key})
        since = (datetime.now(timezone.utc) - timedelta(seconds=ACTIVE_WINDOW_SEC)).isoformat()
        active_now = await db.visitor_sessions.count_documents({"last_seen": {"$gte": since}})

        # günlük seri (kanal kırılımlı)
        by_day = {d: Counter() for d in day_list}
        for s in sessions:
            if s["day"] in by_day:
                by_day[s["day"]][s.get("channel", "direkt")] += 1
        daily = []
        for d in day_list:
            row = {"date": d, "label": datetime.strptime(d, "%Y-%m-%d").strftime("%d.%m"), "total": sum(by_day[d].values())}
            for ch in CHANNEL_LABELS:
                if by_day[d].get(ch):
                    row[ch] = by_day[d][ch]
            daily.append(row)

        # kanal tablosu
        ch_stats = {}
        for s in sessions:
            c = s.get("channel", "direkt")
            st = ch_stats.setdefault(c, {"channel": c, "label": CHANNEL_LABELS.get(c, c), "sessions": 0,
                                         "pageviews": 0, "calls": 0, "whatsapp": 0, "forms": 0, "bounce": 0,
                                         "duration": 0})
            st["sessions"] += 1
            st["pageviews"] += s.get("pages_count", 0)
            st["calls"] += s.get("conv_call", 0)
            st["whatsapp"] += s.get("conv_whatsapp", 0)
            st["forms"] += s.get("conv_form", 0) + s.get("conv_dealer", 0)
            st["bounce"] += 1 if s.get("pages_count", 0) <= 1 and not s.get("converted") else 0
            st["duration"] += s.get("duration_sec", 0)
        # iş / ciro (kanal bazlı)
        jobs = await db.service_jobs.find({"created_at": {"$gte": (today - timedelta(days=days)).astimezone(timezone.utc).isoformat()}},
                                          {"_id": 0, "source_channel": 1, "status": 1, "total_amount": 1}).to_list(50000)
        job_by_ch = {}
        for j in jobs:
            c = j.get("source_channel") or "belirtilmemis"
            r = job_by_ch.setdefault(c, {"jobs": 0, "completed": 0, "revenue": 0.0})
            r["jobs"] += 1
            if j.get("status") in ("tamamlandi", "faturalandi"):
                r["completed"] += 1
                r["revenue"] += j.get("total_amount", 0) or 0
        for c, r in job_by_ch.items():
            if c not in ch_stats:
                ch_stats[c] = {"channel": c, "label": CHANNEL_LABELS.get(c, "Belirtilmemiş" if c == "belirtilmemis" else c),
                               "sessions": 0, "pageviews": 0, "calls": 0, "whatsapp": 0, "forms": 0, "bounce": 0, "duration": 0}
        channels = []
        for c, st in ch_stats.items():
            n = max(st["sessions"], 1)
            conv = st["calls"] + st["whatsapp"] + st["forms"]
            r = job_by_ch.get(c, {"jobs": 0, "completed": 0, "revenue": 0.0})
            channels.append({
                **st, "conversions": conv, "conv_rate": round(conv * 100 / n, 1) if st["sessions"] else 0,
                "bounce_rate": round(st["bounce"] * 100 / n, 1) if st["sessions"] else 0,
                "avg_duration": round(st["duration"] / n) if st["sessions"] else 0,
                "jobs": r["jobs"], "completed_jobs": r["completed"], "revenue": round(r["revenue"], 2),
            })
        channels.sort(key=lambda x: (x["sessions"], x["jobs"]), reverse=True)

        tot = len(sessions)
        bounce = sum(1 for s in sessions if s.get("pages_count", 0) <= 1 and not s.get("converted"))
        avg_dur = round(sum(s.get("duration_sec", 0) for s in sessions) / tot) if tot else 0
        conv_sessions = sum(1 for s in sessions if s.get("converted"))

        def top(key, n=8):
            c = Counter(s.get(key) or "-" for s in sessions)
            return [{"name": k, "value": v} for k, v in c.most_common(n)]

        # sayfa bazlı
        pv_match = {"$match": {"day": {"$gte": start_day}}}
        top_pages = await db.pageviews.aggregate([
            pv_match, {"$group": {"_id": "$path", "views": {"$sum": 1}}}, {"$sort": {"views": -1}}, {"$limit": 10}
        ]).to_list(10)
        landing = Counter(s.get("landing_page") or "/" for s in sessions).most_common(10)

        # saat dağılımı
        hours = Counter(s.get("hour", 0) for s in sessions)
        hourly = [{"hour": f"{h:02d}", "value": hours.get(h, 0)} for h in range(24)]

        # kaynak / kampanya
        src_c = Counter((s.get("source_name") or "-") for s in sessions)
        camp_c = Counter(s.get("campaign") for s in sessions if s.get("campaign"))
        term_c = Counter(s.get("term") for s in sessions if s.get("term"))

        # son oturumlar
        recent = await db.visitor_sessions.find({}, {"_id": 0, "events": 0}).sort("last_seen", -1).to_list(40)
        for s in recent:
            s["channel_label"] = CHANNEL_LABELS.get(s.get("channel"), s.get("channel"))
            s["current_page"] = (s.get("pages") or [{}])[-1].get("path", s.get("landing_page", ""))
            s["pages"] = [p.get("path") for p in (s.get("pages") or [])][-8:]

        # formlar / bekleyenler
        new_msgs = await db.contact_messages.count_documents({"status": "yeni"})
        new_dealers = await db.dealer_applications.count_documents({"status": "yeni"})
        msgs_range = await db.contact_messages.count_documents({"created_at": {"$gte": (today - timedelta(days=days)).astimezone(timezone.utc).isoformat()}})
        calls_range = sum(s.get("conv_call", 0) for s in sessions)
        wa_range = sum(s.get("conv_whatsapp", 0) for s in sessions)

        return {
            "days": days,
            "kpi": {
                "active_now": active_now, "today": cnt_today, "yesterday": cnt_yest, "week": cnt_week,
                "month": cnt_month, "pageviews_today": pv_today, "sessions": tot,
                "avg_duration": avg_dur, "bounce_rate": round(bounce * 100 / tot, 1) if tot else 0,
                "conversion_rate": round(conv_sessions * 100 / tot, 1) if tot else 0,
                "calls": calls_range, "whatsapp": wa_range, "forms": msgs_range,
                "new_messages": new_msgs, "new_dealers": new_dealers,
            },
            "daily": daily,
            "channels": channels,
            "channel_labels": CHANNEL_LABELS,
            "top_pages": [{"name": p["_id"], "value": p["views"]} for p in top_pages],
            "top_landing": [{"name": k, "value": v} for k, v in landing],
            "devices": top("device"), "browsers": top("browser"), "os": top("os"),
            "sources": [{"name": k, "value": v} for k, v in src_c.most_common(10)],
            "campaigns": [{"name": k, "value": v} for k, v in camp_c.most_common(10)],
            "terms": [{"name": k, "value": v} for k, v in term_c.most_common(10)],
            "hourly": hourly,
            "recent": recent,
        }

    @api_router.get("/analytics/export")
    async def analytics_export(days: int = Query(30, ge=1, le=365), _: dict = Depends(require_admin)):
        start_day = tr_day(tr_now() - timedelta(days=days - 1))
        rows = await db.visitor_sessions.find({"day": {"$gte": start_day}}, {"_id": 0}).sort("first_seen", -1).to_list(50000)
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Tarih", "Kanal", "Kaynak", "Kampanya", "Anahtar Kelime", "Giriş Sayfası", "Sayfa Sayısı",
                    "Süre(sn)", "Cihaz", "Tarayıcı", "IP", "Arama", "WhatsApp", "Form"])
        for s in rows:
            w.writerow([s.get("first_seen", "")[:19], CHANNEL_LABELS.get(s.get("channel"), s.get("channel")),
                        s.get("source_name"), s.get("campaign"), s.get("term"), s.get("landing_page"),
                        s.get("pages_count"), s.get("duration_sec"), s.get("device"), s.get("browser"), s.get("ip"),
                        s.get("conv_call"), s.get("conv_whatsapp"), s.get("conv_form", 0) + s.get("conv_dealer", 0)])
        data = "﻿" + buf.getvalue()
        return StreamingResponse(iter([data]), media_type="text/csv; charset=utf-8",
                                 headers={"Content-Disposition": "attachment; filename=ziyaretciler.csv"})

    # ============================================================ PERFORMANS
    @api_router.get("/performance")
    async def performance(days: int = Query(30, ge=1, le=365), _: dict = Depends(require_admin)):
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        techs = await db.users.find({"role": "technician"}, {"_id": 0, "password_hash": 0}).to_list(500)
        jobs = await db.service_jobs.find({"created_at": {"$gte": since}}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(50000)
        by = defaultdict(list)
        for j in jobs:
            by[j.get("assigned_technician_id", "")].append(j)
        out = []
        for t in techs:
            js = by.get(t["id"], [])
            done = [j for j in js if j.get("status") in ("tamamlandi", "faturalandi")]
            cancelled = [j for j in js if j.get("status") == "iptal"]
            rated = [j["customer_rating"] for j in done if j.get("customer_rating")]
            hrs = []
            for j in done:
                try:
                    a = datetime.fromisoformat(j["created_at"])
                    b = datetime.fromisoformat(j["completed_at"])
                    hrs.append((b - a).total_seconds() / 3600)
                except Exception:
                    pass
            rev = sum(j.get("total_amount", 0) or 0 for j in done)
            out.append({
                "id": t["id"], "name": t["name"], "is_active": t.get("is_active", True),
                "assigned": len(js), "completed": len(done), "cancelled": len(cancelled),
                "open": len([j for j in js if j.get("status") in ("yeni", "atandi", "yolda", "basladi")]),
                "completion_rate": round(len(done) * 100 / len(js), 1) if js else 0,
                "revenue": round(rev, 2), "avg_ticket": round(rev / len(done), 2) if done else 0,
                "avg_rating": round(sum(rated) / len(rated), 2) if rated else 0, "rating_count": len(rated),
                "avg_hours": round(sum(hrs) / len(hrs), 1) if hrs else 0,
            })
        out.sort(key=lambda x: (x["completed"], x["revenue"]), reverse=True)
        unassigned = len(by.get("", []))
        return {"days": days, "technicians": out, "unassigned": unassigned}

    # ============================================================ ADMİN KULLANICILAR
    @api_router.get("/admin-users")
    async def list_admin_users(_: dict = Depends(require_admin)):
        return await db.users.find({"role": "admin"}, {"_id": 0, "password_hash": 0}).sort("created_at", 1).to_list(200)

    @api_router.post("/admin-users")
    async def create_admin_user(payload: AdminUserIn, _: dict = Depends(require_admin)):
        email = payload.email.lower().strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise HTTPException(status_code=422, detail="Geçerli bir e-posta girin")
        if await db.users.find_one({"email": email}):
            raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")
        doc = {"id": new_id(), "email": email, "password_hash": hash_password(payload.password), "name": payload.name,
               "phone": payload.phone or "", "role": "admin", "admin_role": payload.admin_role if payload.admin_role in ("owner", "manager", "accounting", "operations", "site_editor") else "manager", "commission_percent": 0, "is_active": True,
               "created_at": now_iso()}
        await db.users.insert_one(doc)
        doc.pop("_id", None)
        doc.pop("password_hash", None)
        return doc

    @api_router.put("/admin-users/{uid}")
    async def update_admin_user(uid: str, payload: AdminUserUpdate, me: dict = Depends(require_admin)):
        upd = {k: v for k, v in payload.model_dump().items() if v is not None}
        if uid == me["id"] and upd.get("is_active") is False:
            raise HTTPException(status_code=400, detail="Kendi hesabınızı pasifleştiremezsiniz")
        if "password" in upd:
            upd["password_hash"] = hash_password(upd.pop("password"))
        res = await db.users.update_one({"id": uid, "role": "admin"}, {"$set": upd})
        if not res.matched_count:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        return await db.users.find_one({"id": uid}, {"_id": 0, "password_hash": 0})

    @api_router.delete("/admin-users/{uid}")
    async def delete_admin_user(uid: str, me: dict = Depends(require_admin)):
        if uid == me["id"]:
            raise HTTPException(status_code=400, detail="Kendi hesabınızı silemezsiniz")
        if await db.users.count_documents({"role": "admin"}) <= 1:
            raise HTTPException(status_code=400, detail="Son yönetici silinemez")
        res = await db.users.delete_one({"id": uid, "role": "admin"})
        if not res.deleted_count:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        return {"ok": True}

    # ============================================================ BİLDİRİM SAYAÇLARI
    @api_router.get("/notifications/summary")
    async def notifications_summary(_: dict = Depends(require_admin)):
        since = (datetime.now(timezone.utc) - timedelta(seconds=ACTIVE_WINDOW_SEC)).isoformat()
        latest_msg = await db.contact_messages.find({"status": "yeni"}, {"_id": 0, "id": 1, "name": 1, "type": 1}) \
            .sort("created_at", -1).to_list(1)
        latest_dealer = await db.dealer_applications.find({"status": "yeni"}, {"_id": 0, "id": 1, "company": 1}) \
            .sort("created_at", -1).to_list(1)
        return {
            "new_messages": await db.contact_messages.count_documents({"status": "yeni"}),
            "new_dealers": await db.dealer_applications.count_documents({"status": "yeni"}),
            "security_alerts": await db.security_alerts.count_documents({"status": "open"}),
            "open_warranty": await db.warranty_claims.count_documents({"status": {"$in": ["acik", "inceleniyor"]}}),
            "pending_reviews": await db.reviews.count_documents({"status": "beklemede"}),
            "live_visitors": await db.visitor_sessions.count_documents({"last_seen": {"$gte": since}}),
            "latest_message": latest_msg[0] if latest_msg else None,
            "latest_dealer": latest_dealer[0] if latest_dealer else None,
        }

    # ============================================================ EXCEL (XLSX) DIŞA AKTARIM
    @api_router.get("/export-xlsx/{kind}")
    async def export_xlsx(kind: str, status: Optional[str] = None, technician_id: Optional[str] = None,
                          channel: Optional[str] = None, date_from: Optional[str] = None,
                          date_to: Optional[str] = None, basis: str = "completed",
                          q: Optional[str] = None, _: dict = Depends(require_admin)):
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
        wb = Workbook()
        ws = wb.active
        money_cols = []
        totals_cols = []
        summary = None
        if kind == "jobs":
            ws.title = "Yapılan İşler"
            query = {}
            if not status:
                status = "tamamlandi,faturalandi"
            if status != "all":
                query["status"] = {"$in": [x for x in status.split(",") if x]}
            if technician_id:
                query["assigned_technician_id"] = technician_id
            if channel:
                query["source_channel"] = channel
            field = "completed_at" if basis == "completed" else "created_at"
            rng = {}
            if date_from:
                rng["$gte"] = date_from
            if date_to:
                rng["$lte"] = date_to + "T23:59:59.999999" if len(date_to) == 10 else date_to
            if rng:
                query[field] = rng
            rows = await db.service_jobs.find(query, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).sort(field, -1).to_list(50000)
            if q:
                ql = q.lower()
                rows = [r for r in rows if ql in " ".join(str(r.get(k, "")) for k in (
                    "job_number", "customer_name", "customer_phone", "device_model", "device_brand_name",
                    "assigned_technician_name", "fault_description")).lower()]
            head = ["İş No", "Oluşturma", "Tamamlanma", "Müşteri", "Telefon", "Adres", "Marka", "Cihaz", "Model",
                    "Arıza", "Yapılan İş", "Kullanılan Parçalar", "Parça Tutarı", "İşçilik", "Toplam",
                    "Usta", "Usta Kalan", "Şirket Payı", "Durum", "Kanal", "Puan"]
            money_cols = [13, 14, 15, 17, 18]
            totals_cols = money_cols
            by_tech, by_ch = {}, {}
            data = []
            for r in rows:
                total = float(r.get("total_amount", 0) or 0)
                pct = float(r.get("technician_commission_percent", 0) or 0)
                comp = round(total * pct / 100, 2) if r.get("assigned_technician_id") else 0
                keep = round(total - comp, 2) if r.get("assigned_technician_id") else 0
                parts = ", ".join(f'{p.get("name")} x{p.get("qty")}' for p in (r.get("parts_used") or []))
                ch = CHANNEL_LABELS.get(r.get("source_channel"), r.get("source_channel") or "Belirtilmemiş")
                data.append([r.get("job_number"), (r.get("created_at") or "")[:16].replace("T", " "),
                             (r.get("completed_at") or "")[:16].replace("T", " "), r.get("customer_name"),
                             r.get("customer_phone"), r.get("customer_address"), r.get("device_brand_name"),
                             r.get("device_type"), r.get("device_model"), r.get("fault_description"),
                             r.get("work_done"), parts, float(r.get("parts_total", 0) or 0),
                             float(r.get("labor_fee", 0) or 0), total, r.get("assigned_technician_name"),
                             keep, comp, r.get("status"), ch, r.get("customer_rating") or ""])
                t = by_tech.setdefault(r.get("assigned_technician_name") or "Atanmamış", [0, 0.0, 0.0, 0.0])
                t[0] += 1; t[1] += total; t[2] += keep; t[3] += comp
                c = by_ch.setdefault(ch, [0, 0.0])
                c[0] += 1; c[1] += total
            summary = (by_tech, by_ch)
        elif kind == "customers":
            ws.title = "Müşteriler"
            rows = await db.customers.find({}, {"_id": 0}).sort("created_at", -1).to_list(50000)
            head = ["Kayıt", "Ad", "Telefon", "E-posta", "İl", "İlçe", "Adres", "Kanal", "Not"]
            data = [[(r.get("created_at") or "")[:10], r.get("name"), r.get("phone"), r.get("email"), r.get("city"),
                     r.get("district"), r.get("address"),
                     CHANNEL_LABELS.get(r.get("source_channel"), r.get("source_channel") or ""), r.get("notes")] for r in rows]
        elif kind == "cash":
            ws.title = "Kasa Hareketleri"
            query = {}
            rng = {}
            if date_from:
                rng["$gte"] = date_from
            if date_to:
                rng["$lte"] = date_to + "T23:59:59.999999" if len(date_to) == 10 else date_to
            if rng:
                query["date"] = rng
            if status:
                query["type"] = status
            if technician_id:
                query["technician_id"] = technician_id
            rows = await db.cash_transactions.find(query, {"_id": 0}).sort("date", -1).to_list(50000)
            names = {u["id"]: u["name"] for u in await db.users.find({"role": "technician"}, {"_id": 0}).to_list(2000)}
            head = ["Tarih", "Tür", "Tutar", "Usta", "İş No", "Açıklama"]
            money_cols = [3]
            data = [[(r.get("date") or "")[:16].replace("T", " "), r.get("type"), float(r.get("amount", 0) or 0),
                     names.get(r.get("technician_id"), ""), r.get("job_number", ""), r.get("description")] for r in rows]
        else:
            raise HTTPException(status_code=404, detail="Bilinmeyen dışa aktarım")
        hf = PatternFill("solid", fgColor="1D4ED8")
        ws.append(head)
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = hf
            c.alignment = Alignment(vertical="center", wrap_text=True)
        for row in data:
            ws.append(row)
        for ci in money_cols:
            for r_ in range(2, ws.max_row + 1):
                ws.cell(r_, ci).number_format = '#,##0.00 "₺"'
        if data and totals_cols:
            tr = ws.max_row + 1
            ws.cell(tr, 1, "TOPLAM").font = Font(bold=True)
            for ci in totals_cols:
                L = get_column_letter(ci)
                cell = ws.cell(tr, ci, f"=SUM({L}2:{L}{tr - 1})")
                cell.font = Font(bold=True); cell.number_format = '#,##0.00 "₺"'
        for i, h in enumerate(head, 1):
            width = max(len(str(h)), *(len(str(r_[i - 1] or "")) for r_ in data[:300])) if data else len(h)
            ws.column_dimensions[get_column_letter(i)].width = min(max(width + 2, 10), 45)
        ws.freeze_panes = "A2"
        if data:
            ws.auto_filter.ref = f"A1:{get_column_letter(len(head))}{len(data) + 1}"
        if summary:
            s2 = wb.create_sheet("Özet")
            s2.append(["Usta", "İş Sayısı", "Ciro", "Usta Kalan", "Şirket Payı"])
            for k, v in sorted(summary[0].items(), key=lambda x: -x[1][1]):
                s2.append([k, v[0], round(v[1], 2), round(v[2], 2), round(v[3], 2)])
            s2.append([])
            s2.append(["Kanal", "İş Sayısı", "Ciro"])
            hdr2 = s2.max_row
            for k, v in sorted(summary[1].items(), key=lambda x: -x[1][1]):
                s2.append([k, v[0], round(v[1], 2)])
            for rr in (1, hdr2):
                for c in s2[rr]:
                    c.font = Font(bold=True, color="FFFFFF"); c.fill = hf
            for col in "ABCDE":
                s2.column_dimensions[col].width = 22
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        fname = f"servisplus-{kind}-{datetime.now().strftime('%Y%m%d')}.xlsx"
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": f'attachment; filename="{fname}"'})

    # ============================================================ CSV DIŞA AKTARIM
    @api_router.get("/export/{kind}")
    async def export_csv(kind: str, _: dict = Depends(require_admin)):
        if kind == "messages":
            rows = await db.contact_messages.find({}, {"_id": 0}).sort("created_at", -1).to_list(20000)
            head = ["Tarih", "Tür", "Ad", "Telefon", "E-posta", "İl", "İlçe", "Cihaz", "Mesaj", "Kanal", "Durum", "Not"]
            data = [[r.get("created_at", "")[:19], r.get("type"), r.get("name"), r.get("phone"), r.get("email"),
                     r.get("city"), r.get("district"), r.get("device_type"), r.get("message"),
                     CHANNEL_LABELS.get(r.get("channel"), r.get("channel")), r.get("status"), r.get("note")] for r in rows]
        elif kind == "dealers":
            rows = await db.dealer_applications.find({}, {"_id": 0}).sort("created_at", -1).to_list(20000)
            head = ["Tarih", "Firma", "Yetkili", "Telefon", "E-posta", "İl", "İlçe", "Hizmet", "Mesaj", "Durum", "Not"]
            data = [[r.get("created_at", "")[:19], r.get("company"), r.get("contact_name"), r.get("phone"),
                     r.get("email"), r.get("city"), r.get("district"), r.get("service_types"), r.get("message"),
                     r.get("status"), r.get("notes")] for r in rows]
        else:
            raise HTTPException(status_code=404, detail="Bilinmeyen dışa aktarım")
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(head)
        w.writerows(data)
        return StreamingResponse(iter(["﻿" + buf.getvalue()]), media_type="text/csv; charset=utf-8",
                                 headers={"Content-Disposition": f"attachment; filename={kind}.csv"})


async def ensure_indexes(db):
    await db.contact_messages.create_index("id", unique=True)
    await db.contact_messages.create_index("created_at")
    await db.dealer_applications.create_index("id", unique=True)
    await db.visitor_sessions.create_index("id", unique=True)
    await db.visitor_sessions.create_index("day")
    await db.visitor_sessions.create_index("last_seen")
    await db.pageviews.create_index("day")
    await db.warranty_claims.create_index("id", unique=True)
    await db.reviews.create_index("id", unique=True)
    await db.announcements.create_index("id", unique=True)
    # ham sayfa görüntüleme/olay kayıtları 180 gün sonra silinir
    try:
        await db.pageviews.create_index("ts_dt", expireAfterSeconds=180 * 86400)
    except Exception:
        pass
