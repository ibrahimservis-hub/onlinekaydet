"""Mağaza (e-ticaret, havale ile satış), müşteri hesabı (telefon + şifre) ve site özellik anahtarları.

- Site özellikleri: mağaza / müşteri paneli / hızlı talep formu / dil seçici (admin açıp kapatır; site buna göre menü ve footer'ı gösterir)
- Mağaza: ürünler, adım adım sipariş, havale (EFT) bilgileri (admin düzenler), sipariş durumları
- Müşteri hesabı: telefon + şifre ile basit üyelik; servis geçmişi, cihazlar, siparişler
"""
import builtins
import copy
import hashlib
import re
import secrets
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request

import notify
import ortak
import shop_legal
import eticaret_plus
import shop_channels
import shop_sync
import shop_var
import b2b

CUSTOMER_TOKEN_DAYS = 30

FEATURES_DEFAULT = {
    "shop_enabled": False,
    "customer_portal_enabled": True,
    "language_enabled": True,
    "quick_request": {
        "enabled": True,
        "title": "Hızlı Servis Talebi",
        "subtitle": "Aramak yerine formu doldurun, ekibimiz sizi arasın.",
        "button": "Servis Talebi Gönder",
        "devices": ["Kombi", "Klima", "Şofben", "Beyaz Eşya", "Televizyon", "Diğer"],
        "ask_address": True,
        "mobile_menu": True,
    },
}

SHOP_DEFAULT = {
    "title": "Mağaza",
    "subtitle": "Güvenli alışveriş. Ödeme yöntemlerini sipariş adımında seçersiniz.",
    "slider_title": "Mağaza Ürünleri",
    "bank_accounts": [],           # [{bank, holder, iban, branch, note}]
    "payment_note": "Havale / EFT açıklamasına sipariş numaranızı yazınız. Ödemeniz kontrol edildikten sonra siparişiniz hazırlanır.",
    "shipping_fee": 0.0,
    "free_shipping_over": 0.0,
    "terms": "Siparişiniz, ödemenin hesabımıza ulaşmasının ardından hazırlanır. Teslimat ve iade koşulları için bizimle iletişime geçebilirsiniz.",
    "contact_phone": "0544 444 4 004",
    "order_prefix": "SP",
    "payments": {},                # bkz. PAY_DEFAULT (yöntem başına açık/kapalı, kapıda ücreti)
    "cod_max_total": 0.0,          # kapıda ödeme için sepet üst sınırı (0 = sınırsız)
    "min_order": 0.0,              # en az sepet tutarı (0 = yok)
    "card_hold_minutes": 60,       # kartla ödemesi tamamlanmayan siparişin stok tutma süresi
    "havale_hold_hours": 72,       # havalesi gelmeyen siparişin stok tutma süresi
    "legal": {},                   # bkz. LEGAL_DEFAULT (satıcı bilgileri: yasal metinlerde kullanılır)
    "legal_docs": {},              # {slug: {"html": özel metin}} — boşsa otomatik metin kullanılır
}

PAY_DEFAULT = {
    "havale": {"enabled": True, "fee": 0.0},
    "kapida_nakit": {"enabled": False, "fee": 0.0},
    "kapida_kart": {"enabled": False, "fee": 0.0},
    "kart": {"enabled": False, "fee": 0.0},      # iyzico ile kartla ödeme (anahtarlar girilmeden açılamaz)
}
PAY_LABELS = {
    "havale": ("Havale / EFT", "Sipariş numaranızı açıklamaya yazarak ödersiniz. Ödeme hesabımıza ulaşınca siparişiniz hazırlanır."),
    "kapida_nakit": ("Kapıda nakit ödeme", "Ürün teslim edilirken kuryeye nakit ödersiniz."),
    "kapida_kart": ("Kapıda kredi kartı ile ödeme", "Kurye taşınabilir POS cihazıyla gelir; kartınızı teslimatta kullanırsınız."),
    "kart": ("Kredi / banka kartı", "Güvenli ödeme sayfasında 3D Secure ile ödersiniz. Kart bilgileriniz bu sitede saklanmaz."),
}
COD_METHODS = ("kapida_nakit", "kapida_kart")
LEGAL_DEFAULT = {"seller_title": "", "tax_office": "", "tax_no": "", "mersis": "", "kep": "", "address": "", "email": "", "phone": "",
                 "return_days": 14, "delivery_days": "1-3 iş günü", "carrier": "", "return_shipping": "alici", "return_address": ""}

ORDER_STATUSES = ["odeme_bekliyor", "odeme_bildirildi", "onaylandi", "hazirlaniyor", "kargoda", "teslim_edildi", "iptal"]

_hits = {}
IYZICO = {"call": None}          # testlerde iyzico çağrısı taklit edilir


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id() -> str:
    return str(uuid.uuid4())


def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def merge_pay(raw) -> dict:
    out = copy.deepcopy(PAY_DEFAULT)
    for k, v in (raw or {}).items():
        if k in out and isinstance(v, dict):
            out[k]["enabled"] = bool(v.get("enabled", out[k]["enabled"]))
            out[k]["fee"] = max(0.0, round(_f(v.get("fee", out[k]["fee"])), 2))
    return out


def merge_legal(raw) -> dict:
    out = dict(LEGAL_DEFAULT)
    for k, v in (raw or {}).items():
        if k in out:
            out[k] = v
    return out


async def iyzico_keys(db) -> dict:
    """Firmanın iyzico anahtarları: Aç/Kapat → iyzico ya da Entegrasyonlar → ödeme (aynı kural kurumsal ödeme linkiyle)."""
    d = await db.app_settings.find_one({"_id": "sp_modules"}, {"_id": 0}) or {}
    c = dict((d.get("config") or {}).get("iyzico", {}) or {})
    if not (c.get("api_key") and c.get("secret_key")):
        ig = (await db.app_settings.find_one({"_id": "integrations"}, {"_id": 0}) or {}).get("payment") or {}
        if ig.get("provider") == "iyzico" and ig.get("api_key") and ig.get("secret"):
            c = {"api_key": ig["api_key"], "secret_key": ig["secret"], "sandbox": str(ig.get("sandbox", "0"))}
    return c if (c.get("api_key") and c.get("secret_key")) else {}


def phone_key(p: str) -> str:
    """Telefonları karşılaştırmak için son 10 hane (0555..., +90555..., 555... aynı sayılır)."""
    d = re.sub(r"\D", "", p or "")
    return d[-10:] if len(d) >= 10 else d


def valid_phone(p: str) -> bool:
    d = re.sub(r"\D", "", p or "")
    return 10 <= len(d) <= 13


def slugify(s: str) -> str:
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    s = (s or "").translate(tr).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "urun"


def rate_ok(key: str, limit: int, window: int) -> bool:
    now = time.time()
    arr = [t for t in _hits.get(key, []) if now - t < window]
    if len(arr) >= limit:
        _hits[key] = arr
        return False
    arr.append(now)
    _hits[key] = arr
    return True


def client_ip(request: Request) -> str:
    xf = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return xf or (request.client.host if request.client else "")


def clean_product(p: dict, cur: Optional[dict] = None) -> dict:
    cur = cur or {}
    name = str(p.get("name", cur.get("name", ""))).strip()[:160]
    if not name:
        raise HTTPException(422, "Ürün adı gerekli")
    specs = []
    for it in (p.get("specs", cur.get("specs", [])) or [])[:80]:
        k, v = str(it.get("k", "")).strip()[:60], str(it.get("v", "")).strip()[:300]
        if k and v:
            specs.append({"k": k, "v": v})
    images = [str(x)[:300] for x in (p.get("images", cur.get("images", [])) or [])[:12] if x]
    price = round(_f(p.get("price", cur.get("price", 0))), 2)
    if price < 0:
        raise HTTPException(422, "Fiyat negatif olamaz")
    return {
        "name": name,
        "brand": str(p.get("brand", cur.get("brand", ""))).strip()[:60],
        "model": str(p.get("model", cur.get("model", ""))).strip()[:80],
        "category": str(p.get("category", cur.get("category", ""))).strip()[:60],
        "price": price,
        "old_price": round(_f(p.get("old_price", cur.get("old_price", 0))), 2),
        "stock": int(_f(p.get("stock", cur.get("stock", 0)))),
        "track_stock": bool(p.get("track_stock", cur.get("track_stock", True))),
        "short": str(p.get("short", cur.get("short", ""))).strip()[:240],
        "description": str(p.get("description", cur.get("description", ""))).strip()[:12000],
        "specs": specs,
        "images": images,
        "sku": str(p.get("sku", cur.get("sku", ""))).strip()[:60],
        "badge": str(p.get("badge", cur.get("badge", ""))).strip()[:30],
        "featured": bool(p.get("featured", cur.get("featured", False))),
        "active": bool(p.get("active", cur.get("active", True))),
        "sort": int(_f(p.get("sort", cur.get("sort", 100)), 100)),
        "barcode": _barcode(p.get("barcode", cur.get("barcode", ""))),
        "category_id": str(p.get("category_id", cur.get("category_id", "")) or "")[:40],
        "kdv": _kdv(p.get("kdv", cur.get("kdv", 20))),
        "desi": round(max(0.0, _f(p.get("desi", cur.get("desi", 0)))), 2),
        "weight": round(max(0.0, _f(p.get("weight", cur.get("weight", 0)))), 3),
        "shelf": str(p.get("shelf", cur.get("shelf", ""))).strip()[:30],
        "min_stock": max(0, int(_f(p.get("min_stock", cur.get("min_stock", 0))))),
        "cost": round(max(0.0, _f(p.get("cost", cur.get("cost", 0)))), 2),
        "delivery_days": max(0, min(30, int(_f(p.get("delivery_days", cur.get("delivery_days", 2)), 2)))),
        "warranty_months": max(0, min(120, int(_f(p.get("warranty_months", cur.get("warranty_months", 0)))))),
        "category_ids": [str(x)[:40] for x in list(dict.fromkeys(p.get("category_ids", cur.get("category_ids", [])) or []))[:12] if x],
        "gtin": str(p.get("gtin", cur.get("gtin", ""))).strip()[:14],
        "seo_title": str(p.get("seo_title", cur.get("seo_title", ""))).strip()[:70],
        "seo_desc": str(p.get("seo_desc", cur.get("seo_desc", ""))).strip()[:170],
        "seo_keywords": str(p.get("seo_keywords", cur.get("seo_keywords", ""))).strip()[:200],
        "tags": [str(x).strip()[:30] for x in (p.get("tags", cur.get("tags", [])) or [])[:20] if str(x).strip()],
        "unit": str(p.get("unit", cur.get("unit", "Adet")) or "Adet").strip()[:15],
        "supplier": str(p.get("supplier", cur.get("supplier", ""))).strip()[:80],
        "channels": shop_channels.clean_channels(p.get("channels"), cur.get("channels")),
        "market_attrs": _market_attrs(p.get("market_attrs", cur.get("market_attrs"))),
    }


def _barcode(v) -> str:
    v = str(v or "").strip()
    if v and not shop_channels.gtin_valid(v):
        raise HTTPException(422, "Barkod geçersiz: 8, 12, 13 veya 14 haneli ve sağlama basamağı doğru (EAN/UPC) olmalı")
    return v


def _kdv(v) -> int:
    try:
        n = int(float(v))
    except (TypeError, ValueError):
        n = 20
    if n not in shop_channels.KDV_RATES:
        raise HTTPException(422, "KDV oranı %0, %1, %10 veya %20 olmalı")
    return n


def _market_attrs(v) -> dict:
    out = {}
    for mk, d in (v or {}).items():
        if mk in shop_channels.MARKETS and isinstance(d, dict):
            out[mk] = {str(k)[:20]: str(x)[:60] for k, x in list(d.items())[:60]}
    return out


async def stock_changed(db, ids):
    """Stok/fiyat değişen ürünleri açık pazaryeri kuyruğuna alır (hata siparişi bozmaz)."""
    try:
        await shop_sync._enqueue(db, list(ids))
    except Exception:                                   # noqa: BLE001
        pass


def public_product(d: dict) -> dict:
    out = {k: d.get(k) for k in ("id", "slug", "name", "brand", "model", "category", "price", "old_price", "short", "description",
                                 "specs", "images", "badge", "featured", "sku", "gtin", "barcode", "img_alt", "video", "free_ship",
                                 "delivery_days", "unit", "seo_title", "min_qty", "max_qty")}
    st = d.get("stock", 0)
    out["in_stock"] = (not d.get("track_stock", True)) or st > 0
    vs = [v for v in (d.get("variants") or []) if v.get("active", True)]
    if vs:
        out["var_axes"] = d.get("var_axes") or []
        out["variants"] = [{"id": v["id"], "opts": v.get("opts") or {}, "label": v.get("label", ""), "price": v.get("price") or d.get("price"),
                            "old_price": v.get("old_price") or 0, "image": v.get("image", ""),
                            "in_stock": (not d.get("track_stock", True)) or v.get("stock", 0) > 0,
                            "stock_left": v["stock"] if d.get("track_stock", True) and 0 < v.get("stock", 0) <= 5 else None} for v in vs]
        pr = [v["price"] for v in out["variants"]]
        out["price_min"] = min(pr) if pr else d.get("price")
        out["in_stock"] = any(v["in_stock"] for v in out["variants"])
    out["stock_left"] = st if d.get("track_stock", True) and 0 < st <= 5 else None
    return out


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    hash_password = deps["hash_password"]
    verify_password = deps["verify_password"]
    JWT_SECRET = deps["JWT_SECRET"]
    JWT_ALGORITHM = deps["JWT_ALGORITHM"]
    security = deps["security"]
    shop_sync.register(api_router, db, deps)

    # ------------------------------------------------------------------ yardımcılar
    async def get_doc(key: str, default: dict) -> dict:
        d = await db.app_settings.find_one({"_id": key}, {"_id": 0}) or {}
        out = {**default, **d}
        if key == "site_features":
            out["quick_request"] = {**default["quick_request"], **(d.get("quick_request") or {})}
        return out

    def guard(request: Request, bucket: str, limit: int, window: int):
        ip = client_ip(request)
        if not rate_ok(f"{bucket}:{ip}", limit, window):
            raise HTTPException(429, "Çok fazla istek. Lütfen biraz sonra tekrar deneyin.")
        return ip

    async def features():
        return await get_doc("site_features", FEATURES_DEFAULT)

    async def shop_cfg():
        d = await get_doc("shop_settings", SHOP_DEFAULT)
        d["payments"] = merge_pay(d.get("payments"))
        d["legal"] = merge_legal(d.get("legal"))
        return d

    async def card_ready() -> bool:
        return bool(await iyzico_keys(db))

    async def methods_public(cfg: dict) -> list:
        """Müşteriye gösterilecek ödeme yöntemleri (kapalı olanlar ve anahtarı eksik kart hiç görünmez)."""
        out = []
        ready = await card_ready()
        for k in ("kart", "kapida_nakit", "kapida_kart", "havale"):
            m = cfg["payments"][k]
            if not m["enabled"] or (k == "kart" and not ready):
                continue
            if k == "havale" and not cfg.get("bank_accounts"):
                continue                      # IBAN girilmeden havale gösterilmez
            lbl, desc = PAY_LABELS[k]
            out.append({"id": k, "label": lbl, "desc": desc, "fee": m["fee"] if k in COD_METHODS else 0.0})
        return out

    async def expire_unpaid():
        """Ödemesi gelmeyen siparişlerin stoğunu serbest bırakır (kart: dakika, havale: saat)."""
        cfg = await shop_cfg()
        now = datetime.now(timezone.utc)
        lim_c = (now - timedelta(minutes=max(15, int(_f(cfg.get("card_hold_minutes"), 60))))).isoformat()
        lim_h = (now - timedelta(hours=max(1, int(_f(cfg.get("havale_hold_hours"), 72))))).isoformat()
        rows = await db.shop_orders.find({"status": "odeme_bekliyor", "$or": [
            {"payment.method": "kart", "created_at": {"$lt": lim_c}},
            {"payment.method": "havale", "created_at": {"$lt": lim_h}}]}, {"_id": 0}).to_list(200)
        for o in rows:
            r = await db.shop_orders.update_one({"id": o["id"], "status": "odeme_bekliyor"}, {"$set": {"status": "iptal", "updated_at": _now()},
                "$push": {"history": {"status": "iptal", "at": _now(), "by": "sistem", "note": "ödeme süresi doldu"}}})
            if r.modified_count:
                await restock(o)
        return len(rows)

    def cust_token(acc: dict) -> str:
        return jwt.encode({"sub": acc["id"], "typ": "customer", "exp": datetime.now(timezone.utc) + timedelta(days=CUSTOMER_TOKEN_DAYS)},
                          JWT_SECRET, algorithm=JWT_ALGORITHM)

    async def current_customer(request: Request, required: bool = True):
        h = request.headers.get("authorization", "")
        tok = h[7:] if h.lower().startswith("bearer ") else ""
        if not tok:
            if required:
                raise HTTPException(401, "Giriş yapmanız gerekiyor")
            return None
        try:
            pl = jwt.decode(tok, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except Exception:
            if required:
                raise HTTPException(401, "Oturum süresi doldu, tekrar giriş yapın")
            return None
        if pl.get("typ") != "customer":
            if required:
                raise HTTPException(401, "Geçersiz oturum")
            return None
        acc = await db.customer_accounts.find_one({"id": pl.get("sub")}, {"_id": 0})
        if not acc and required:
            raise HTTPException(401, "Hesap bulunamadı")
        return acc

    async def cust_login_event(request: Request, acc, phone: str, ok: bool, reason: str):
        ua = request.headers.get("user-agent", "")[:300]
        try:
            label = security.device_label(ua)
        except Exception:      # noqa: BLE001
            label = ""
        await db.login_events.insert_one({
            "id": _id(), "user_id": (acc or {}).get("id", ""), "email": phone, "name": (acc or {}).get("name", ""), "role": "customer",
            "ip": client_ip(request), "ua": ua, "device_id": "", "device_label": label, "success": ok, "reason": reason, "at": _now(),
            "user_exists": bool(acc), "portal": "musteri"})

    def acc_public(a: dict) -> dict:
        return {"id": a["id"], "name": a.get("name", ""), "phone": a.get("phone", ""), "email": a.get("email", ""),
                "address": a.get("address", ""), "city": a.get("city", ""), "district": a.get("district", ""), "created_at": a.get("created_at", ""),
                "avatar": a.get("avatar", ""), "avatar_status": a.get("avatar_status", "pending" if a.get("avatar") else "")}

    async def linked_customer_ids(phone: str):
        key = phone_key(phone)
        if len(key) < 10:
            return []
        ids = []
        async for c in db.customers.find({}, {"_id": 0, "id": 1, "phone": 1}):
            if phone_key(c.get("phone", "")) == key:
                ids.append(c["id"])
        return ids

    # ================================================================== SİTE ÖZELLİKLERİ
    @api_router.get("/public/site-config")
    async def public_site_config():
        f = await features()
        s = await shop_cfg()
        return {
            "shop": {"enabled": bool(f["shop_enabled"]), "title": s["title"], "slider_title": s["slider_title"], "subtitle": s["subtitle"]},
            "customer_portal": {"enabled": bool(f["customer_portal_enabled"])},
            "language": {"enabled": bool(f["language_enabled"])},
            "quick_request": f["quick_request"],
        }

    @api_router.get("/site/features")
    async def get_features(_: dict = Depends(require_admin)):
        return await features()

    @api_router.put("/site/features")
    async def put_features(payload: dict, _: dict = Depends(require_admin)):
        cur = await features()
        if payload.get("shop_enabled"):                      # paket kontrolü: Mağaza modülü olmayan firma mağazayı açamaz
            fm = (await db.app_settings.find_one({"_id": "firm"}, {"_id": 0, "modules": 1})) or {}
            if fm.get("modules") is not None and "magaza" not in fm["modules"] and "eticaret" not in fm["modules"]:
                raise HTTPException(status_code=403, detail="“Mağaza” bu paketinizde yok. Paket yükseltmek için bizimle iletişime geçin.")
        for k in ("shop_enabled", "customer_portal_enabled", "language_enabled"):
            if k in payload:
                cur[k] = bool(payload[k])
        if payload.get("shop_enabled") and "customer_portal_enabled" not in payload:
            cur["customer_portal_enabled"] = True            # mağaza açılınca müşteri girişi / paneli de açılır (sipariş için üyelik gerekir)
        if isinstance(payload.get("quick_request"), dict):
            q, c = payload["quick_request"], cur["quick_request"]
            for k in ("enabled", "ask_address", "mobile_menu"):
                if k in q:
                    c[k] = bool(q[k])
            for k, n in (("title", 80), ("subtitle", 200), ("button", 40)):
                if k in q:
                    c[k] = str(q[k]).strip()[:n]
            if isinstance(q.get("devices"), list):
                c["devices"] = [str(x).strip()[:30] for x in q["devices"] if str(x).strip()][:12] or c["devices"]
        await db.app_settings.update_one({"_id": "site_features"}, {"$set": cur}, upsert=True)
        return cur

    # ================================================================== MAĞAZA — ADMIN
    @api_router.get("/shop/settings")
    async def get_shop_settings(_: dict = Depends(require_admin)):
        return await shop_cfg()

    @api_router.put("/shop/settings")
    async def put_shop_settings(payload: dict, _: dict = Depends(require_admin)):
        cur = await shop_cfg()
        for k, n in (("title", 80), ("subtitle", 240), ("slider_title", 80), ("payment_note", 600), ("terms", 3000), ("contact_phone", 30), ("order_prefix", 6)):
            if k in payload:
                cur[k] = str(payload[k]).strip()[:n]
        for k in ("shipping_fee", "free_shipping_over"):
            if k in payload:
                cur[k] = max(0.0, round(_f(payload[k]), 2))
        for k in ("cod_max_total", "min_order"):
            if k in payload:
                cur[k] = max(0.0, round(_f(payload[k]), 2))
        if "card_hold_minutes" in payload:
            cur["card_hold_minutes"] = int(builtins.min(1440, builtins.max(15, _f(payload["card_hold_minutes"], 60))))
        if "havale_hold_hours" in payload:
            cur["havale_hold_hours"] = int(builtins.min(720, builtins.max(1, _f(payload["havale_hold_hours"], 72))))
        if isinstance(payload.get("payments"), dict):
            pm = merge_pay({**cur.get("payments", {}), **{k: {**cur["payments"].get(k, {}), **v} for k, v in payload["payments"].items() if isinstance(v, dict)}})
            if pm["kart"]["enabled"] and not await card_ready():
                raise HTTPException(422, "Kartla ödemeyi açmak için önce iyzico anahtarlarını girin (Entegrasyonlar → Ödeme).")
            if pm["havale"]["enabled"] and not (payload.get("bank_accounts") or cur.get("bank_accounts")):
                raise HTTPException(422, "Havale / EFT için en az bir banka hesabı ekleyin.")
            if not any(m["enabled"] for m in pm.values()):
                raise HTTPException(422, "En az bir ödeme yöntemi açık olmalı.")
            cur["payments"] = pm
        if isinstance(payload.get("legal"), dict):
            lg = merge_legal({**cur.get("legal", {}), **payload["legal"]})
            for k in ("seller_title", "tax_office", "tax_no", "mersis", "kep", "address", "email", "phone", "carrier", "return_address", "delivery_days"):
                lg[k] = str(lg.get(k) or "").strip()[:300]
            lg["return_days"] = int(builtins.min(60, builtins.max(14, _f(lg.get("return_days"), 14))))
            lg["return_shipping"] = "satici" if lg.get("return_shipping") == "satici" else "alici"
            cur["legal"] = lg
        cur["updated_at"] = _now()
        if isinstance(payload.get("bank_accounts"), list):
            accs = []
            for b in payload["bank_accounts"][:8]:
                iban = re.sub(r"\s+", "", str(b.get("iban", "")).upper())[:34]
                if not (b.get("bank") or iban):
                    continue
                accs.append({"bank": str(b.get("bank", "")).strip()[:60], "holder": str(b.get("holder", "")).strip()[:100],
                             "iban": iban, "branch": str(b.get("branch", "")).strip()[:60], "note": str(b.get("note", "")).strip()[:160]})
            cur["bank_accounts"] = accs
        await db.app_settings.update_one({"_id": "shop_settings"}, {"$set": cur}, upsert=True)
        return cur

    @api_router.get("/shop/products")
    async def admin_products(_: dict = Depends(require_admin)):
        return await db.shop_products.find({}, {"_id": 0}).sort([("sort", 1), ("created_at", -1)]).to_list(2000)

    async def unique_slug(base: str, exclude_id: str = ""):
        slug, n = base, 2
        while await db.shop_products.find_one({"slug": slug, "id": {"$ne": exclude_id}}):
            slug, n = f"{base}-{n}", n + 1
        return slug

    async def sync_catalog_fields(doc: dict, pid: str = ""):
        """Kategori adı her zaman iç ağaçtan gelir; barkod ve stok kodu benzersizdir (pazaryerlerinde de aynı kimlik)."""
        ids = list(doc.get("category_ids") or [])
        if doc.get("category_id") and doc["category_id"] not in ids:
            ids.insert(0, doc["category_id"])
        if ids and not doc.get("category_id"):
            doc["category_id"] = ids[0]
        for cid in ids:
            if not await db.shop_categories.find_one({"id": cid}, {"_id": 1}):
                raise HTTPException(422, "Seçilen kategori bulunamadı")
        doc["category_ids"] = ids
        if doc.get("category_id"):
            c = await db.shop_categories.find_one({"id": doc["category_id"]}, {"_id": 0, "name": 1})
            doc["category"] = c["name"]            # ana (breadcrumb) kategori adı; ürün listesinde ve pazaryerinde bu kullanılır
        for f, lbl in (("barcode", "Barkod"), ("sku", "Stok kodu")):
            if doc.get(f) and await db.shop_products.find_one({f: doc[f], "id": {"$ne": pid}}, {"_id": 1}):
                raise HTTPException(409, f"{lbl} başka bir üründe kullanılıyor: {doc[f]}")

    @api_router.get("/shop/slug-check")
    async def slug_check(slug: str = "", id: str = "", _: dict = Depends(require_admin)):
        base = slugify(slug)
        if not base:
            raise HTTPException(422, "Adres oluşturulamadı")
        free = not await db.shop_products.find_one({"slug": base, "id": {"$ne": id}}, {"_id": 1})
        return {"slug": base, "free": free, "suggest": base if free else await unique_slug(base, id)}

    @api_router.post("/shop/products")
    async def create_product(payload: dict, _: dict = Depends(require_admin)):
        doc = clean_product(payload)
        await sync_catalog_fields(doc)
        doc.update({"id": _id(), "slug": await unique_slug(slugify(payload.get("slug") or doc["name"])), "created_at": _now(), "updated_at": _now(), "sold": 0})
        await db.shop_products.insert_one(dict(doc))
        return doc

    @api_router.put("/shop/products/{pid}")
    async def update_product(pid: str, payload: dict, _: dict = Depends(require_admin)):
        cur = await db.shop_products.find_one({"id": pid}, {"_id": 0})
        if not cur:
            raise HTTPException(404, "Ürün bulunamadı")
        upd = clean_product(payload, cur)
        await sync_catalog_fields(upd, pid)
        upd["updated_at"] = _now()
        if "price" in payload and cur.get("src"):
            upd["price_manual"] = True                  # markadan çekilen ürünün fiyatı elle değişti: otomatik güncelleme ezmesin
        if payload.get("slug"):
            upd["slug"] = await unique_slug(slugify(payload["slug"]), pid)
        await db.shop_products.update_one({"id": pid}, {"$set": upd})
        await stock_changed(db, [pid])
        return {**cur, **upd}

    @api_router.delete("/shop/products/{pid}")
    async def delete_product(pid: str, _: dict = Depends(require_admin)):
        r = await db.shop_products.delete_one({"id": pid})
        if not r.deleted_count:
            raise HTTPException(404, "Ürün bulunamadı")
        await db.shop_sync_queue.delete_many({"product_id": pid, "status": "bekliyor"})
        return {"ok": True}

    @api_router.get("/shop/orders")
    async def admin_orders(status: Optional[str] = None, q: Optional[str] = None, _: dict = Depends(require_admin)):
        flt = {}
        if status:
            flt["status"] = status
        rows = await db.shop_orders.find(flt, {"_id": 0}).sort("created_at", -1).to_list(2000)
        if q:
            ql = q.lower().strip()
            rows = [r for r in rows if ql in (r["order_no"] + " " + r["customer"].get("name", "") + " " + r["customer"].get("phone", "")).lower()]
        return rows

    @api_router.get("/shop/summary")
    async def shop_summary(_: dict = Depends(require_admin)):
        await expire_unpaid()
        rows = await db.shop_orders.find({}, {"_id": 0, "status": 1, "total": 1, "payment": 1}).to_list(20000)
        cnt = {}
        for r in rows:
            cnt[r["status"]] = cnt.get(r["status"], 0) + 1
        paid = sum(r["total"] for r in rows if r["status"] in ("onaylandi", "hazirlaniyor", "kargoda", "teslim_edildi")
                   and (r.get("payment") or {}).get("status") != "kapida_tahsil")
        cod_wait = sum(r["total"] for r in rows if (r.get("payment") or {}).get("status") == "kapida_tahsil" and r["status"] in ("onaylandi", "hazirlaniyor", "kargoda"))
        return {"counts": cnt, "revenue": round(paid, 2), "cod_pending": round(cod_wait, 2), "waiting_payment": cnt.get("odeme_bekliyor", 0) + cnt.get("odeme_bildirildi", 0),
                "products": await db.shop_products.count_documents({"active": True})}

    async def restock(order):
        for it in order.get("items", []):
            await shop_var.ver(db, it["product_id"], it["qty"], it.get("variant_id", ""))
        await stock_changed(db, [it["product_id"] for it in order.get("items", [])])
        await b2b.iade(db, order)

    @api_router.put("/shop/orders/{oid}")
    async def update_order(oid: str, payload: dict, _: dict = Depends(require_admin)):
        o = await db.shop_orders.find_one({"id": oid}, {"_id": 0})
        if not o:
            raise HTTPException(404, "Sipariş bulunamadı")
        upd = {}
        st = payload.get("status")
        if st:
            if st not in ORDER_STATUSES:
                raise HTTPException(422, "Geçersiz durum")
            if st == "iptal" and o["status"] != "iptal" and not o.get("external"):
                await restock(o)
            if o["status"] == "iptal" and st != "iptal" and not o.get("external"):
                for it in o["items"]:
                    await shop_var.ver(db, it["product_id"], -it["qty"], it.get("variant_id", ""))
                await stock_changed(db, [it["product_id"] for it in o["items"]])
            upd["status"] = st
            upd["history"] = (o.get("history") or []) + [{"status": st, "at": _now()}]
        for k, n in (("admin_note", 1000), ("tracking_no", 80), ("carrier", 60)):
            if k in payload:
                upd[k] = str(payload[k]).strip()[:n]
        if upd:
            upd["updated_at"] = _now()
            await db.shop_orders.update_one({"id": oid}, {"$set": upd})
            if upd.get("status") == "teslim_edildi" and o.get("status") != "teslim_edildi" and getattr(api_router, "uye_puan_kazan", None):
                try:
                    await api_router.uye_puan_kazan((o.get("customer") or {}).get("phone"), o.get("total"), "siparis:" + oid, "Sipariş")
                except Exception:                                  # noqa: BLE001
                    pass
        return {**o, **upd}

    @api_router.delete("/shop/orders/{oid}")
    async def delete_order(oid: str, _: dict = Depends(require_admin)):
        o = await db.shop_orders.find_one({"id": oid}, {"_id": 0})
        if not o:
            raise HTTPException(404, "Sipariş bulunamadı")
        if o["status"] != "iptal" and not o.get("external"):
            await restock(o)                                   # pazaryeri siparişinin stoğu pazaryeri akışıyla yönetilir
        await db.shop_orders.delete_one({"id": oid})
        return {"ok": True}

    # ================================================================== YÖNETİM: gelişmiş ürün listesi + toplu işlem
    def _admin_flt(p: dict) -> dict:
        import re as _re
        flt = {}
        q = str(p.get("q") or "").strip()
        if q:
            rx = {"$regex": _re.escape(q), "$options": "i"}
            flt["$or"] = [{"name": rx}, {"brand": rx}, {"model": rx}, {"sku": rx}, {"category": rx}]
        if p.get("brand"):
            flt["brand"] = p["brand"]
        if p.get("category"):
            flt["category"] = p["category"]
        a = str(p.get("active") or "")
        if a in ("1", "true"):
            flt["active"] = True
        elif a in ("0", "false"):
            flt["active"] = False
        pr = {}
        if _f(p.get("price_min")) > 0:
            pr["$gte"] = _f(p.get("price_min"))
        if _f(p.get("price_max")) > 0:
            pr["$lte"] = _f(p.get("price_max"))
        if pr:
            flt["price"] = pr
        if str(p.get("no_price") or "") in ("1", "true"):
            flt["$and"] = flt.get("$and", []) + [{"$or": [{"price": 0}, {"price": {"$exists": False}}]}]
        st = str(p.get("stock") or "")
        if st == "in":
            flt["$and"] = flt.get("$and", []) + [{"$or": [{"track_stock": False}, {"stock": {"$gt": 0}}]}]
        elif st == "out":
            flt["$and"] = flt.get("$and", []) + [{"track_stock": True, "stock": {"$lte": 0}}]
        src = str(p.get("source") or "")
        if src == "imported":
            flt["src"] = {"$exists": True}
        elif src == "manual":
            flt["src"] = {"$exists": False}
        if str(p.get("no_image") or "") in ("1", "true"):
            flt["$and"] = flt.get("$and", []) + [{"$or": [{"images": {"$size": 0}}, {"images": {"$exists": False}}]}]
        if str(p.get("featured") or "") in ("1", "true"):
            flt["featured"] = True
        return flt

    @api_router.get("/admin/shop-products/search")
    async def adm_search(q: str = "", brand: str = "", category: str = "", active: str = "", price_min: float = 0, price_max: float = 0, no_price: str = "",
                         stock: str = "", source: str = "", no_image: str = "", featured: str = "", sort: str = "new", page: int = 1, per: int = 50,
                         _: dict = Depends(require_admin)):
        per = builtins.min(200, builtins.max(10, per))
        page = builtins.max(1, page)
        p = dict(q=q, brand=brand, category=category, active=active, price_min=price_min, price_max=price_max, no_price=no_price, stock=stock, source=source, no_image=no_image, featured=featured)
        flt = _admin_flt(p)
        order = {"new": [("created_at", -1)], "name": [("name", 1)], "asc": [("price", 1)], "desc": [("price", -1)], "brand": [("brand", 1), ("name", 1)], "upd": [("updated_at", -1)]}.get(sort, [("created_at", -1)])
        total = await db.shop_products.count_documents(flt)
        rows = await db.shop_products.find(flt, {"_id": 0, "description": 0, "specs": 0}).sort(order).skip((page - 1) * per).limit(per).to_list(per)
        allr = await db.shop_products.find({}, {"_id": 0, "brand": 1, "category": 1, "active": 1, "price": 1, "src": 1}).to_list(100000)
        bc, cc = {}, {}
        n_act = n_pas = n_np = n_imp = 0
        for r in allr:
            b, c = (r.get("brand") or "").strip(), (r.get("category") or "").strip()
            if b:
                bc[b] = bc.get(b, 0) + 1
            if c:
                cc[c] = cc.get(c, 0) + 1
            if r.get("active"):
                n_act += 1
            else:
                n_pas += 1
            if not (r.get("price") or 0) > 0:
                n_np += 1
            if r.get("src"):
                n_imp += 1
        return {"items": [{"id": r["id"], "name": r["name"], "brand": r.get("brand", ""), "category": r.get("category", ""), "model": r.get("model", ""), "sku": r.get("sku", ""),
                           "price": r.get("price", 0), "old_price": r.get("old_price", 0), "stock": r.get("stock", 0), "track_stock": r.get("track_stock", True),
                           "active": bool(r.get("active")), "featured": bool(r.get("featured")), "img": (r.get("images") or [""])[0], "slug": r.get("slug", ""),
                           "imported": bool(r.get("src")), "updated_at": r.get("updated_at", "")} for r in rows],
                "total": total, "page": page, "per": per,
                "brands": sorted([{"name": k, "count": v} for k, v in bc.items()], key=lambda x: x["name"].lower()),
                "categories": sorted([{"name": k, "count": v} for k, v in cc.items()], key=lambda x: -x["count"]),
                "stats": {"all": len(allr), "active": n_act, "passive": n_pas, "no_price": n_np, "imported": n_imp}}

    @api_router.post("/admin/shop-products/bulk")
    async def adm_bulk(payload: dict, _: dict = Depends(require_admin)):
        """ids: seçili ürünler  |  filter: filtreye uyan TÜM ürünler.  action: activate, deactivate, delete, category, brand, price_percent, price_add, feature, unfeature, stock"""
        act = str(payload.get("action") or "")
        if payload.get("ids"):
            flt = {"id": {"$in": [str(x) for x in payload["ids"]][:20000]}}
        elif isinstance(payload.get("filter"), dict):
            flt = _admin_flt(payload["filter"])
        else:
            raise HTTPException(422, "Ürün seçilmedi")
        val = payload.get("value")
        now = datetime.now(timezone.utc).isoformat()
        if act in ("activate",):
            # fiyatsız ürün yayına alınmaz
            r = await db.shop_products.update_many({**flt, "price": {"$gt": 0}}, {"$set": {"active": True, "updated_at": now}})
            skipped = await db.shop_products.count_documents({**flt, "$or": [{"price": 0}, {"price": {"$exists": False}}]})
            return {"ok": True, "changed": r.modified_count, "skipped_no_price": skipped}
        if act == "deactivate":
            r = await db.shop_products.update_many(flt, {"$set": {"active": False, "updated_at": now}})
        elif act == "delete":
            r = await db.shop_products.delete_many(flt)
            return {"ok": True, "changed": r.deleted_count}
        elif act == "category":
            v = str(val or "").strip()[:60]
            if not v:
                raise HTTPException(422, "Kategori adı gerekli")
            r = await db.shop_products.update_many(flt, {"$set": {"category": v, "updated_at": now}})
        elif act == "brand":
            v = str(val or "").strip()[:60]
            if not v:
                raise HTTPException(422, "Marka adı gerekli")
            r = await db.shop_products.update_many(flt, {"$set": {"brand": v, "updated_at": now}})
        elif act in ("feature", "unfeature"):
            r = await db.shop_products.update_many(flt, {"$set": {"featured": act == "feature", "updated_at": now}})
        elif act == "stock":
            v = int(_f(val))
            r = await db.shop_products.update_many(flt, {"$set": {"stock": builtins.max(0, v), "track_stock": True, "updated_at": now}})
        elif act in ("price_percent", "price_add"):
            n = 0
            for d in await db.shop_products.find(flt, {"_id": 0, "id": 1, "price": 1, "src": 1}).to_list(20000):
                pr = d.get("price") or 0
                if pr <= 0:
                    continue
                np_ = pr * (1 + _f(val) / 100.0) if act == "price_percent" else pr + _f(val)
                np_ = round(builtins.max(0.0, np_), 2)
                await db.shop_products.update_one({"id": d["id"]}, {"$set": {"price": np_, "price_manual": True, "updated_at": now}})
                n += 1
            return {"ok": True, "changed": n}
        else:
            raise HTTPException(422, "Bilinmeyen işlem")
        return {"ok": True, "changed": r.modified_count}

    # ================================================================== MAĞAZA — HERKESE AÇIK
    async def require_shop():
        if not (await features())["shop_enabled"]:
            raise HTTPException(404, "Mağaza şu anda kapalı")

    @api_router.get("/public/shop/products")
    async def pub_products(featured: bool = False, category: str = "", q: str = ""):
        await require_shop()
        flt = {"active": True}
        if featured:
            flt["featured"] = True
        if category:
            flt["category"] = category
        rows = await db.shop_products.find(flt, {"_id": 0}).sort([("sort", 1), ("created_at", -1)]).to_list(500)
        if q:
            ql = q.lower().strip()
            rows = [r for r in rows if ql in (r["name"] + " " + r.get("brand", "") + " " + r.get("model", "") + " " + r.get("category", "")).lower()]
        cats = sorted({r["category"] for r in rows if r.get("category")})
        return {"products": [public_product(r) for r in rows], "categories": cats}

    @api_router.get("/public/shop/products/{slug}")
    async def pub_product(slug: str, request: Request):
        await require_shop()
        d = await db.shop_products.find_one({"$or": [{"slug": slug}, {"id": slug}], "active": True}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Ürün bulunamadı")
        return await b2b.uygula(db, await b2b.dealer_req(request), public_product(d), True)

    # ---- gelişmiş mağaza: sayfalı arama, facet, benzer ürünler, sitemap (additive)
    def lite(r):
        st = r.get("stock", 0)
        return {"id": r["id"], "slug": r.get("slug", r["id"]), "name": r["name"], "brand": r.get("brand", ""), "category": r.get("category", ""),
                "price": r.get("price", 0), "old_price": r.get("old_price", 0), "short": (r.get("short") or "")[:140], "img": (r.get("images") or [""])[0],
                "badge": r.get("badge", ""), "featured": bool(r.get("featured")), "in_stock": (not r.get("track_stock", True)) or st > 0,
                "has_var": bool([v for v in (r.get("variants") or []) if v.get("active", True)])}

    @api_router.get("/public/shop/search")
    async def pub_search(brand: str = "", category: str = "", q: str = "", sort: str = "pop", max: float = 0, page: int = 1, per: int = 24, min: float = 0, in_stock: bool = False, request: Request = None, discount: bool = False):
        await require_shop()
        per = builtins.min(60, builtins.max(6, per))
        page = builtins.max(1, page)
        base = await db.shop_products.find({"active": True}, {"_id": 0, "brand": 1, "category": 1}).to_list(60000)
        bmap = {}
        for r in base:
            b = (r.get("brand") or "").strip()
            if b:
                bmap.setdefault(slugify(b), b)
        flt = {"active": True}
        if brand and brand in bmap:
            flt["brand"] = bmap[brand]
        elif brand:
            flt["brand"] = "__yok__"
        if category:
            flt["category"] = category
        pr_ = {}
        if max and max > 0:
            pr_["$lte"] = max
        if min and min > 0:
            pr_["$gte"] = min
        if pr_:
            flt["price"] = pr_
        if in_stock:
            flt["$and"] = flt.get("$and", []) + [{"$or": [{"track_stock": False}, {"stock": {"$gt": 0}}]}]
        if discount:
            flt["$expr"] = {"$gt": ["$old_price", "$price"]}
        if q.strip():
            import re as _re
            rx = {"$regex": _re.escape(q.strip()), "$options": "i"}
            flt["$or"] = [{"name": rx}, {"brand": rx}, {"model": rx}, {"category": rx}, {"sku": rx}]
        order = {"asc": [("price", 1)], "desc": [("price", -1)], "name": [("name", 1)], "new": [("created_at", -1)]}.get(sort, [("featured", -1), ("sort", 1), ("created_at", -1)])
        total = await db.shop_products.count_documents(flt)
        rows = await db.shop_products.find(flt, {"_id": 0, "description": 0, "specs": 0}).sort(order).skip((page - 1) * per).limit(per).to_list(per)
        # facetler: kategori sayıları (marka filtresi içinde), marka sayıları (kategori filtresi içinde)
        cc, bc = {}, {}
        for r in base:
            b = (r.get("brand") or "").strip()
            c = (r.get("category") or "").strip()
            if (not brand or slugify(b) == brand) and c:
                cc[c] = cc.get(c, 0) + 1
            if (not category or c == category) and b:
                bc[slugify(b)] = bc.get(slugify(b), 0) + 1
        bd = await b2b.dealer_req(request)
        return {"items": [await b2b.uygula(db, bd, lite(r)) for r in rows], "total": total, "page": page, "per": per,
                "categories": sorted([{"name": k, "count": v} for k, v in cc.items()], key=lambda x: -x["count"]),
                "brands": sorted([{"slug": k, "name": bmap.get(k, k), "count": v} for k, v in bc.items()], key=lambda x: x["name"]),
                "brand_name": bmap.get(brand, "")}

    @api_router.get("/public/shop/related/{slug}")
    async def pub_related(slug: str, request: Request, n: int = 12):
        await require_shop()
        d = await db.shop_products.find_one({"$or": [{"slug": slug}, {"id": slug}], "active": True}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Ürün bulunamadı")
        proj = {"_id": 0, "description": 0, "specs": 0}
        same_cat = await db.shop_products.find({"active": True, "category": d.get("category", ""), "id": {"$ne": d["id"]}}, proj).sort([("featured", -1), ("sort", 1)]).limit(40).to_list(40)
        same_brand = await db.shop_products.find({"active": True, "brand": d.get("brand", ""), "id": {"$ne": d["id"]}}, proj).sort([("featured", -1), ("sort", 1)]).limit(40).to_list(40)
        p0 = d.get("price", 0) or 0
        sim = sorted([r for r in same_cat], key=lambda r: (0 if r.get("brand") == d.get("brand") else 1, abs((r.get("price", 0) or 0) - p0)))[:n]
        seen = {r["id"] for r in sim}
        other = [r for r in same_brand if r["id"] not in seen][:n]
        sec = []
        if d.get("related"):
            by = {r["id"]: r for r in await db.shop_products.find({"active": True, "id": {"$in": list(d["related"])}}, proj).to_list(20)}
            sec = [lite(by[i]) for i in d["related"] if i in by]
            seen |= {r["id"] for r in sec}
            sim = [r for r in sim if r["id"] not in {x["id"] for x in sec}]
        bd = await b2b.dealer_req(request)
        return {"picked": [await b2b.uygula(db, bd, x) for x in sec], "similar": [await b2b.uygula(db, bd, lite(r)) for r in sim],
                "same_brand": [await b2b.uygula(db, bd, lite(r)) for r in other]}

    @api_router.get("/public/shop/sitemap")
    async def pub_sitemap():
        await require_shop()
        rows = await db.shop_products.find({"active": True}, {"_id": 0, "slug": 1, "id": 1, "updated_at": 1, "images": 1, "name": 1}).to_list(50000)
        return {"items": [{"slug": r.get("slug", r["id"]), "updated_at": r.get("updated_at", ""), "name": r["name"], "img": (r.get("images") or [""])[0]} for r in rows]}

    @api_router.get("/public/shop/info")
    async def pub_shop_info():
        await require_shop()
        s = await shop_cfg()
        lg = s["legal"]
        ttl = (s.get("title") or "").strip()
        if not ttl or "servisplus" in ttl.lower():
            ttl = "Mağaza"
        return {"title": ttl, "subtitle": s["subtitle"], "shipping_fee": s["shipping_fee"], "free_shipping_over": s["free_shipping_over"],
                "terms": s["terms"], "contact_phone": s["contact_phone"] or lg.get("phone", ""), "payment_note": s["payment_note"],
                "payment_methods": await methods_public(s), "cod_max_total": s["cod_max_total"], "min_order": s["min_order"],
                "legal_docs": [{"slug": k, "title": t, "checkout": k in shop_legal.CHECKOUT_DOCS} for k, t in shop_legal.SLUGS]}

    # ------------------------------------------------------------------ yasal metinler
    @api_router.get("/public/shop/legal/{slug}")
    async def pub_legal(slug: str):
        await require_shop()
        if slug not in shop_legal.TITLES:
            raise HTTPException(404, "Metin bulunamadı")
        cfg = await shop_cfg()
        return {"slug": slug, "title": shop_legal.TITLES[slug], "html": shop_legal.page(slug, cfg["legal"], cfg, cfg.get("legal_docs"), cfg.get("updated_at", ""))}

    @api_router.get("/shop/legal")
    async def admin_legal(_: dict = Depends(require_admin)):
        cfg = await shop_cfg()
        docs = []
        for k, t in shop_legal.SLUGS:
            c = (cfg.get("legal_docs") or {}).get(k) or {}
            docs.append({"slug": k, "title": t, "custom": bool(c.get("html")), "html": shop_legal.doc_html(k, cfg["legal"], cfg, cfg.get("legal_docs")),
                         "default_html": shop_legal.default_html(k, cfg["legal"], cfg), "checkout": k in shop_legal.CHECKOUT_DOCS})
        return {"legal": cfg["legal"], "missing": shop_legal.missing_fields(cfg["legal"]), "docs": docs,
                "notice": "Bu metinler genel şablondur; hukuki danışman onayı önerilir."}

    @api_router.put("/shop/legal/{slug}")
    async def admin_legal_put(slug: str, payload: dict, _: dict = Depends(require_admin)):
        if slug not in shop_legal.TITLES:
            raise HTTPException(404, "Metin bulunamadı")
        cfg = await shop_cfg()
        docs = dict(cfg.get("legal_docs") or {})
        if payload.get("reset"):
            docs.pop(slug, None)
        else:
            h = str(payload.get("html", ""))[:60000]
            if len(re.sub(r"<[^>]+>", "", h).strip()) < 40:
                raise HTTPException(422, "Metin çok kısa")
            if re.search(r"<\s*(script|iframe|object|embed)|\bon\w+\s*=|javascript:", h, re.I):
                raise HTTPException(422, "Metinde betik veya gömülü içerik olamaz")
            docs[slug] = {"html": h, "at": _now()}
        await db.app_settings.update_one({"_id": "shop_settings"}, {"$set": {"legal_docs": docs, "updated_at": _now()}}, upsert=True)
        return {"ok": True}

    async def next_order_no(prefix):
        n = await db.shop_orders.count_documents({})
        while True:
            n += 1
            no = f"{prefix}-{datetime.now(timezone.utc).strftime('%y%m')}-{n:04d}"
            if not await db.shop_orders.find_one({"order_no": no}, {"_id": 1}):
                return no

    @api_router.post("/public/shop/orders")
    async def pub_create_order(payload: dict, request: Request):
        await require_shop()
        guard(request, "shop_order", 12, 900)
        if False and payload.get("sp_hp"):  # honeypot kapalı: tarayıcı otomatik doldurması gerçek müşteriyi engelliyordu
            raise HTTPException(422, "Sipariş doğrulanamadı, lütfen sayfayı yenileyip tekrar deneyin.")
        acc0 = await current_customer(request, required=False)
        if not acc0:
            raise HTTPException(401, "Sipariş vermek için giriş yapın veya üye olun.")
        cu = payload.get("customer") or {}
        name, phone = str(cu.get("name", "")).strip()[:120], str(cu.get("phone", "")).strip()[:30]
        if len(name) < 2:
            raise HTTPException(422, "Ad soyad gerekli")
        if not valid_phone(phone):
            raise HTTPException(422, "Lütfen geçerli bir telefon numarası girin.")
        address = str(cu.get("address", "")).strip()[:400]
        if len(address) < 8:
            raise HTTPException(422, "Teslimat adresi gerekli")
        if not payload.get("accept_terms"):
            raise HTTPException(422, "Mesafeli satış sözleşmesi ve ön bilgilendirme formunu kabul etmelisiniz")
        await expire_unpaid()
        cfg = await shop_cfg()
        avail = {m["id"]: m for m in await methods_public(cfg)}
        dealer = await b2b.dealer_of(db, acc0)
        if dealer:
            avail["cari"] = {"id": "cari", "label": "Cari hesap (vadeli)", "fee": 0}
        pm_id = str(payload.get("payment_method") or "").strip()
        if pm_id not in avail:
            raise HTTPException(422, "Seçtiğiniz ödeme yöntemi şu an kullanılamıyor. Lütfen başka bir yöntem seçin.")
        email = str(cu.get("email", "")).strip()[:120]
        if pm_id == "kart" and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise HTTPException(422, "Kartla ödeme için geçerli bir e-posta adresi gerekli")
        items_in = payload.get("items") or []
        if not isinstance(items_in, list) or not items_in:
            raise HTTPException(422, "Sepetiniz boş")
        items, subtotal = [], 0.0
        for it in items_in[:30]:
            qty = max(1, min(int(_f(it.get("qty"), 1)), 20))
            p = await db.shop_products.find_one({"id": it.get("product_id"), "active": True}, {"_id": 0})
            if not p:
                raise HTTPException(422, "Sepetteki bir ürün artık satışta değil")
            vid = str(it.get("variant_id") or "")
            v = shop_var.sec(p, vid)
            if p.get("variants") and not v:
                raise HTTPException(422, f"'{p['name']}' için seçenek (renk/beden vb.) seçin")
            if v and v.get("active") is False:
                raise HTTPException(422, f"'{p['name']}' ({v.get('label','')}) artık satışta değil")
            have = v["stock"] if v else p.get("stock", 0)
            if p.get("track_stock", True) and have < qty:
                raise HTTPException(422, f"'{p['name']}'{' (' + v['label'] + ')' if v else ''} için yeterli stok yok (kalan: {max(0, have)})")
            unit = await b2b.fiyat(db, dealer, p, v, (v or p)["price"])
            line = round(unit * qty, 2)
            subtotal += line
            items.append({"product_id": p["id"], "name": p["name"], "brand": p.get("brand", ""), "model": p.get("model", ""), "price": unit,
                          "qty": qty, "line_total": line, "image": ((v or {}).get("image") or (p.get("images") or [""])[0]),
                          "variant_id": vid, "variant": (v or {}).get("label", ""), "sku": (v or p).get("sku", ""), "track": p.get("track_stock", True)})
        shipping = 0.0 if (cfg["free_shipping_over"] and subtotal >= cfg["free_shipping_over"]) else float(cfg["shipping_fee"] or 0)
        if cfg["min_order"] and subtotal < cfg["min_order"]:
            raise HTTPException(422, "Minimum sipariş tutarı %.2f TL" % cfg["min_order"])
        cod_fee = float(avail[pm_id]["fee"]) if pm_id in COD_METHODS else 0.0
        total = round(subtotal + shipping + cod_fee, 2)
        await b2b.kontrol(db, dealer, subtotal, total, pm_id)
        if pm_id in COD_METHODS and cfg["cod_max_total"] and total > cfg["cod_max_total"]:
            raise HTTPException(422, "Kapıda ödeme en fazla %.2f TL'lik siparişlerde kullanılabilir. Lütfen kart veya havale seçin." % cfg["cod_max_total"])
        # stok düş (koşullu: yarışta eksiye düşmesin)
        done = []
        for it in items:
            if not await shop_var.al(db, it["product_id"], it["qty"], it.get("variant_id", ""), it.get("track", True)):
                for d in done:
                    await shop_var.ver(db, d["product_id"], d["qty"], d.get("variant_id", ""))
                raise HTTPException(422, f"'{it['name']}' stoğu az önce tükendi")
            done.append(it)
        await stock_changed(db, [d["product_id"] for d in done])
        acc = acc0
        order = {
            "id": _id(), "order_no": await next_order_no(cfg["order_prefix"] or "SP"), "status": "onaylandi" if (pm_id in COD_METHODS or pm_id == "cari") else "odeme_bekliyor",
            "customer": {"name": name, "phone": phone, "email": email, "city": str(cu.get("city", "")).strip()[:60],
                         "district": str(cu.get("district", "")).strip()[:60], "address": address},
            "note": str(payload.get("note", "")).strip()[:500], "items": items, "subtotal": round(subtotal, 2), "shipping": shipping, "cod_fee": cod_fee, "total": total,
            "account_id": acc["id"] if acc else "", "phone_key": phone_key(phone), "admin_note": "", "tracking_no": "", "carrier": "",
            "payment": {"method": pm_id, "label": avail[pm_id]["label"], "status": "kapida_tahsil" if pm_id in COD_METHODS else ("cari" if pm_id == "cari" else "bekliyor"), "amount": total},
            "consent": {"terms": True, "at": _now(), "ip": client_ip(request), "docs": shop_legal.CHECKOUT_DOCS,
                        "version": shop_legal.version(cfg["legal"], cfg, cfg.get("legal_docs"))},
            "created_at": _now(), "updated_at": _now(),
        }
        order["history"] = [{"status": order["status"], "at": _now(), "note": avail[pm_id]["label"]}]
        try:
            order["risk"] = await eticaret_plus.risk_hesapla(db, order)
        except Exception:      # noqa: BLE001
            order["risk"] = None
        await db.shop_orders.insert_one(dict(order))
        await b2b.kaydet(db, dealer, order)
        await ortak.kaydet(db, order, payload.get("ref"), dealer)
        try:
            await db.shop_carts.delete_one({"account_id": acc0["id"]})
        except Exception:      # noqa: BLE001
            pass
        await eticaret_plus.webhook_gonder(db, "siparis.olustu", {"order_no": order["order_no"], "total": total, "status": order["status"], "musteri": name, "telefon": phone, "odeme": pm_id,
                                                          "urunler": [{"ad": i["name"], "adet": i["qty"], "fiyat": i["price"]} for i in items]})
        try:
            rk = order.get("risk") or {}
            risk_not = (" · RİSK: %s (%s)" % (rk["seviye"].upper(), ", ".join(rk["nedenler"]))) if rk.get("seviye") in ("orta", "yuksek") and rk.get("bildir", True) else ""
            await notify.notify_owner_t(db, f"Yeni mağaza siparişi {order['order_no']}: {name} · {total:.2f} TL" + risk_not, kind="shop_order")
        except Exception:      # noqa: BLE001
            pass
        return {"ok": True, "order_no": order["order_no"], "total": total, "shipping": shipping, "subtotal": order["subtotal"], "cod_fee": cod_fee,
                "payment_method": pm_id, "next": "iyzico" if pm_id == "kart" else ("havale" if pm_id == "havale" else ("cari" if pm_id == "cari" else "kapida")),
                "bank_accounts": cfg["bank_accounts"] if pm_id == "havale" else [], "payment_note": cfg["payment_note"] if pm_id == "havale" else "",
                "contact_phone": cfg["contact_phone"]}

    @api_router.get("/public/shop/orders/{order_no}")
    async def pub_order(order_no: str, phone: str, request: Request):
        guard(request, "shop_track", 20, 600)
        o = await db.shop_orders.find_one({"order_no": order_no.strip().upper()}, {"_id": 0})
        if not o or phone_key(phone) != o.get("phone_key"):
            raise HTTPException(404, "Sipariş bulunamadı. Numara ve telefonu kontrol edin.")
        cfg = await shop_cfg()
        out = {k: o[k] for k in ("order_no", "status", "items", "subtotal", "shipping", "total", "created_at", "tracking_no", "carrier", "history", "payment")}
        out["customer"] = {"name": o["customer"]["name"]}
        if o["status"] in ("odeme_bekliyor", "odeme_bildirildi"):
            out["bank_accounts"], out["payment_note"] = cfg["bank_accounts"], cfg["payment_note"]
        return out

    @api_router.post("/public/shop/orders/{order_no}/paid")
    async def pub_order_paid(order_no: str, payload: dict, request: Request):
        guard(request, "shop_paid", 10, 600)
        o = await db.shop_orders.find_one({"order_no": order_no.strip().upper()}, {"_id": 0})
        if not o or phone_key(str(payload.get("phone", ""))) != o.get("phone_key"):
            raise HTTPException(404, "Sipariş bulunamadı. Numara ve telefonu kontrol edin.")
        if o["status"] != "odeme_bekliyor" and o["status"] != "odeme_bildirildi":
            raise HTTPException(400, "Bu sipariş için ödeme bildirimi gerekmiyor")
        pay = {"sender": str(payload.get("sender", "")).strip()[:120], "bank": str(payload.get("bank", "")).strip()[:60],
               "amount": round(_f(payload.get("amount"), o["total"]), 2), "note": str(payload.get("note", "")).strip()[:300], "at": _now()}
        await db.shop_orders.update_one({"id": o["id"]}, {"$set": {"payment": pay, "status": "odeme_bildirildi", "updated_at": _now()},
                                                        "$push": {"history": {"status": "odeme_bildirildi", "at": _now()}}})
        try:
            await notify.notify_owner_t(db, f"Havale bildirimi {o['order_no']}: {pay['sender'] or o['customer']['name']} · {pay['amount']:.2f} TL", kind="shop_payment")
        except Exception:      # noqa: BLE001
            pass
        return {"ok": True}

    # ================================================================== MÜŞTERİ HESABI
    @api_router.post("/public/customer/register")
    async def cust_register(payload: dict, request: Request):
        if not (await features())["customer_portal_enabled"]:
            raise HTTPException(404, "Müşteri paneli kapalı")
        guard(request, "cust_reg", 10, 900)
        if False and payload.get("sp_hp"):  # honeypot kapalı: tarayıcı otomatik doldurması gerçek müşteriyi engelliyordu
            raise HTTPException(422, "Doğrulanamadı, lütfen sayfayı yenileyip tekrar deneyin.")
        name, phone, pw = str(payload.get("name", "")).strip()[:120], str(payload.get("phone", "")).strip()[:30], str(payload.get("password", ""))
        if len(name) < 2:
            raise HTTPException(422, "Ad soyad gerekli")
        if not valid_phone(phone):
            raise HTTPException(422, "Lütfen geçerli bir telefon numarası girin.")
        if len(pw) < 6 or len(pw) > 72:
            raise HTTPException(422, "Şifre en az 6 karakter olmalı")
        key = phone_key(phone)
        riza = {}
        try:                                                       # üyelik açıksa KVKK ve (sağlıkta) özel rıza onayı şart
            import uyelik as _uy
            _sec = ((await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0})) or {}).get("sector") or ""
            _c, _p = await _uy.get_cfg(db, _sec)
            if _c["on"] and _c["kvkk"]:
                if not payload.get("kvkk_onay"):
                    raise HTTPException(422, "Devam etmek için KVKK aydınlatma metnini onaylamalısınız.")
                riza["kvkk_at"] = _now()
                if _p["ozel_onay"]:
                    if not payload.get("ozel_riza"):
                        raise HTTPException(422, "Sağlık verilerinizin işlenmesi için açık rıza vermelisiniz.")
                    riza["ozel_riza_at"] = _now()
        except HTTPException:
            raise
        except Exception:                                          # noqa: BLE001
            pass
        if await db.customer_accounts.find_one({"phone_key": key}, {"_id": 1}):
            raise HTTPException(409, "Bu telefon numarasıyla zaten üyelik var. Giriş yapın.")
        acc = {**riza, "id": _id(), "name": name, "phone": phone, "phone_key": key, "email": str(payload.get("email", "")).strip()[:120],
               "password_hash": hash_password(pw), "address": "", "city": "", "district": "", "created_at": _now(), "last_login": _now()}
        await db.customer_accounts.insert_one(dict(acc))
        await cust_login_event(request, acc, phone, True, "")
        try:
            await notify.notify_owner_t(db, f"Yeni müşteri üyeliği: {name} · {phone}", kind="customer_signup")
        except Exception:      # noqa: BLE001
            pass
        return {"token": cust_token(acc), "account": acc_public(acc)}

    @api_router.post("/public/customer/login")
    async def cust_login(payload: dict, request: Request):
        if not (await features())["customer_portal_enabled"]:
            raise HTTPException(404, "Müşteri paneli kapalı")
        phone, pw = str(payload.get("phone", "")).strip(), str(payload.get("password", ""))
        key = phone_key(phone)
        ip = client_ip(request)
        since = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        fails = await db.login_events.count_documents({"role": "customer", "success": False, "at": {"$gte": since}, "$or": [{"email": phone}, {"ip": ip}]})
        acc = await db.customer_accounts.find_one({"phone_key": key}, {"_id": 0}) if key else None
        if fails >= 8:
            await cust_login_event(request, acc, phone, False, "locked")
            raise HTTPException(429, "Çok fazla hatalı deneme. 15 dakika sonra tekrar deneyin.")
        if not acc or not verify_password(pw, acc["password_hash"]):
            await cust_login_event(request, acc, phone, False, "bad_password")
            raise HTTPException(401, "Telefon veya şifre hatalı")
        await db.customer_accounts.update_one({"id": acc["id"]}, {"$set": {"last_login": _now()}})
        await cust_login_event(request, acc, phone, True, "")
        return {"token": cust_token(acc), "account": acc_public(acc)}

    @api_router.post("/public/customer/forgot")
    async def cust_forgot(payload: dict, request: Request):
        guard(request, "cust_forgot", 3, 900)
        phone = str(payload.get("phone", "")).strip()
        acc = await db.customer_accounts.find_one({"phone_key": phone_key(phone)}, {"_id": 0}) if phone else None
        if acc:
            await db.contact_messages.insert_one({
                "id": _id(), "name": acc["name"], "phone": acc["phone"], "email": acc.get("email", ""), "city": "", "district": "",
                "device_type": "", "type": "diger", "message": "Müşteri paneli şifre sıfırlama talebi. Lütfen müşteriyi arayıp Müşteri Hesapları bölümünden geçici şifre verin.",
                "status": "yeni", "notes": "", "job_id": "", "job_number": "", "source": {"channel": "musteri_paneli"}, "channel": "musteri_paneli",
                "page": "/musteri-giris/", "sid": "", "ip": "", "created_at": _now(), "updated_at": _now()})
        return {"ok": True, "message": "Talebiniz alındı. Ekibimiz kayıtlı numaranızdan sizinle iletişime geçecek."}

    @api_router.get("/public/customer/me")
    async def cust_me(request: Request):
        acc = await current_customer(request)
        return acc_public(acc)

    @api_router.put("/public/customer/me")
    async def cust_update(payload: dict, request: Request):
        acc = await current_customer(request)
        upd = {}
        for k, n in (("name", 120), ("email", 120), ("address", 300), ("city", 60), ("district", 60)):
            if k in payload:
                upd[k] = str(payload[k]).strip()[:n]
        if payload.get("new_password"):
            if not verify_password(str(payload.get("old_password", "")), acc["password_hash"]):
                raise HTTPException(400, "Mevcut şifre hatalı")
            if len(payload["new_password"]) < 6:
                raise HTTPException(422, "Yeni şifre en az 6 karakter olmalı")
            upd["password_hash"] = hash_password(str(payload["new_password"]))
        if upd:
            await db.customer_accounts.update_one({"id": acc["id"]}, {"$set": upd})
        return acc_public({**acc, **upd})

    def clean_addr(p: dict, cur: dict = None) -> dict:
        cur = cur or {}
        g = lambda k, n: str(p.get(k, cur.get(k, ""))).strip()[:n]            # noqa: E731
        a = {"title": g("title", 40) or "Adresim", "name": g("name", 120), "phone": g("phone", 30), "city": g("city", 60), "district": g("district", 60), "address": g("address", 300)}
        if len(a["name"]) < 2:
            raise HTTPException(422, "Alıcı adı gerekli")
        if not valid_phone(a["phone"]):
            raise HTTPException(422, "Lütfen geçerli bir telefon numarası girin.")
        if not a["city"] or not a["district"]:
            raise HTTPException(422, "İl ve ilçe gerekli")
        if len(a["address"]) < 8:
            raise HTTPException(422, "Açık adres gerekli")
        return a

    @api_router.get("/public/customer/addresses")
    async def cust_addrs(request: Request):
        acc = await current_customer(request)
        return acc.get("addresses") or []

    @api_router.post("/public/customer/addresses")
    async def cust_addr_add(payload: dict, request: Request):
        acc = await current_customer(request)
        lst = list(acc.get("addresses") or [])
        if len(lst) >= 10:
            raise HTTPException(422, "En fazla 10 adres kaydedebilirsiniz")
        a = {**clean_addr(payload), "id": _id(), "default": not lst or bool(payload.get("default"))}
        if a["default"]:
            for x in lst:
                x["default"] = False
        lst.append(a)
        await db.customer_accounts.update_one({"id": acc["id"]}, {"$set": {"addresses": lst}})
        return lst

    @api_router.put("/public/customer/addresses/{aid}")
    async def cust_addr_edit(aid: str, payload: dict, request: Request):
        acc = await current_customer(request)
        lst = list(acc.get("addresses") or [])
        i = next((k for k, x in enumerate(lst) if x["id"] == aid), -1)
        if i < 0:
            raise HTTPException(404, "Adres bulunamadı")
        lst[i] = {**lst[i], **clean_addr(payload, lst[i])}
        if payload.get("default"):
            for k, x in enumerate(lst):
                x["default"] = k == i
        await db.customer_accounts.update_one({"id": acc["id"]}, {"$set": {"addresses": lst}})
        return lst

    @api_router.delete("/public/customer/addresses/{aid}")
    async def cust_addr_del(aid: str, request: Request):
        acc = await current_customer(request)
        lst = [x for x in (acc.get("addresses") or []) if x["id"] != aid]
        if lst and not any(x.get("default") for x in lst):
            lst[0]["default"] = True
        await db.customer_accounts.update_one({"id": acc["id"]}, {"$set": {"addresses": lst}})
        return lst

    @api_router.get("/public/customer/jobs")
    async def cust_jobs(request: Request):
        acc = await current_customer(request)
        ids = await linked_customer_ids(acc["phone"])
        if not ids:
            return []
        rows = await db.service_jobs.find({"customer_id": {"$in": ids}}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).sort("created_at", -1).to_list(200)
        out = []
        _tids = list({j.get("assigned_technician_id") for j in rows if j.get("assigned_technician_id")})
        _ph = {u["id"] for u in await db.users.find({"id": {"$in": _tids}, "photo_path": {"$exists": True, "$ne": ""}, "photo_status": {"$nin": ["pending", "rejected"]}}, {"_id": 0, "id": 1}).to_list(500)} if _tids else set()
        for j in rows:
            out.append({"technician_photo": (f"/api/public/track/{j['track_token']}/usta-foto" if j.get("track_token") and j.get("assigned_technician_id") in _ph else ""),
                        "id": j["id"], "job_number": j.get("job_number", ""), "status": j.get("status", ""),
                        "device": " ".join(x for x in (j.get("device_brand_name", ""), j.get("device_model", ""), j.get("device_type", "")) if x),
                        "fault": j.get("fault_description", ""), "work_done": j.get("work_done", ""), "scheduled_at": j.get("scheduled_at", ""),
                        "completed_at": j.get("completed_at", ""), "created_at": j.get("created_at", ""), "total": j.get("total_amount", 0),
                        "technician": j.get("assigned_technician_name", ""), "track_token": j.get("track_token", ""),
                        "parts": [{"name": p.get("name", ""), "qty": p.get("quantity", 1)} for p in (j.get("parts_used") or [])]})
        return out

    @api_router.get("/public/customer/devices")
    async def cust_devices(request: Request):
        acc = await current_customer(request)
        ids = await linked_customer_ids(acc["phone"])
        rows = await db.devices.find({"customer_id": {"$in": ids}}, {"_id": 0}).to_list(100) if ids else []
        return [{"id": d["id"], "brand": d.get("brand_name", ""), "model": d.get("model", ""), "type": d.get("type", ""), "serial_no": d.get("serial_no", ""),
                 "warranty_until": d.get("warranty_until", ""), "install_date": d.get("install_date", ""), "qr_token": d.get("qr_token", "")} for d in rows]

    @api_router.get("/public/customer/orders")
    async def cust_orders(request: Request):
        acc = await current_customer(request)
        rows = await db.shop_orders.find({"$or": [{"account_id": acc["id"]}, {"phone_key": acc["phone_key"]}]}, {"_id": 0}).sort("created_at", -1).to_list(100)
        cfg = await shop_cfg()
        for r in rows:
            if r["status"] in ("odeme_bekliyor", "odeme_bildirildi"):
                r["bank_accounts"], r["payment_note"] = cfg["bank_accounts"], cfg["payment_note"]
        return rows

    @api_router.post("/public/customer/request")
    async def cust_request(payload: dict, request: Request):
        """Giriş yapmış müşteri: tek tıkla servis talebi (İletişim Mesajları'na düşer)."""
        acc = await current_customer(request)
        guard(request, "cust_req", 6, 900)
        msg = str(payload.get("message", "")).strip()[:2000]
        if len(msg) < 5:
            raise HTTPException(422, "Lütfen arızayı kısaca yazın")
        doc = {"id": _id(), "name": acc["name"], "phone": acc["phone"], "email": acc.get("email", ""), "city": acc.get("city", ""), "district": acc.get("district", ""),
               "device_type": str(payload.get("device_type", ""))[:40], "type": "servis_talebi", "message": msg, "status": "yeni", "notes": "", "job_id": "",
               "job_number": "", "source": {"channel": "musteri_paneli"}, "channel": "musteri_paneli", "page": "/musteri-giris/", "sid": "", "ip": "",
               "created_at": _now(), "updated_at": _now()}
        await db.contact_messages.insert_one(dict(doc))
        try:
            await notify.notify_owner_t(db, f"Müşteri panelinden servis talebi: {acc['name']} — {msg[:80]}", kind="customer_request")
        except Exception:      # noqa: BLE001
            pass
        return {"ok": True}

    # ----- admin: müşteri hesapları
    @api_router.get("/customer-accounts")
    async def list_accounts(q: str = "", _: dict = Depends(require_admin)):
        rows = await db.customer_accounts.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(2000)
        if q:
            ql = q.lower().strip()
            rows = [r for r in rows if ql in (r["name"] + " " + r["phone"] + " " + r.get("email", "")).lower()]
        return rows

    @api_router.post("/customer-accounts/{aid}/reset-password")
    async def reset_account(aid: str, _: dict = Depends(require_admin)):
        acc = await db.customer_accounts.find_one({"id": aid}, {"_id": 0})
        if not acc:
            raise HTTPException(404, "Hesap bulunamadı")
        tmp = secrets.token_urlsafe(6).replace("-", "a").replace("_", "b")[:8]
        await db.customer_accounts.update_one({"id": aid}, {"$set": {"password_hash": hash_password(tmp)}})
        return {"ok": True, "temp_password": tmp}

    @api_router.delete("/customer-accounts/{aid}")
    async def delete_account(aid: str, _: dict = Depends(require_admin)):
        r = await db.customer_accounts.delete_one({"id": aid})
        if not r.deleted_count:
            raise HTTPException(404, "Hesap bulunamadı")
        return {"ok": True}


async def ensure_indexes(db):
    await db.shop_products.create_index("id", unique=True)
    await db.shop_products.create_index("slug")
    await db.shop_orders.create_index("order_no", unique=True)
    await db.shop_orders.create_index("phone_key")
    await db.customer_accounts.create_index("phone_key", unique=True)
    await db.customer_accounts.create_index("id", unique=True)
