# -*- coding: utf-8 -*-
"""ServisPlus panel eklentisi (server.py'ye `sp_ext.register(...)` satırıyla takılır; mevcut dosyaları bozmaz).

İçerik:
  - Modül aç/kapat + site etiketleri (GA4, Google Ads, Yandex, Meta Pixel / CAPI, Merchant)  -> /api/admin/modules, /api/public/site-modules
  - SEO araçları: toplu SEO kuralları, 404 kayıtları, 301 yönlendirmeleri, link kuralları, anahtar kelime önerisi
  - Google Merchant ürün akışı (XML)
  - Panelden sipariş oluşturma (mağaza siparişlerine yazar)
  - iyzico ile kartla ödeme
  - Pazaryerleri: Trendyol, Hepsiburada, N11 (bağlantı testi, sipariş çekme, stok/fiyat gönderme)
  - Müşteri KVKK: verilerimi indir / hesabımı sil
Mağaza ürünleri, siparişler ve müşteri hesapları panelin kendi (shop.py) koleksiyonlarını kullanır.
"""
import asyncio, os, re, json, time, uuid, hmac, hashlib, base64, random, logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import jwt
import requests
from fastapi import Depends, HTTPException, Request
from fastapi.responses import Response, RedirectResponse, JSONResponse
from pydantic import BaseModel

import shop as shopmod

log = logging.getLogger("sp_ext")
HERE = Path(__file__).parent
PUBLIC_SITE = os.environ.get("PUBLIC_SITE_URL", "https://servisplus.net.tr")
PANEL_URL = os.environ.get("PANEL_PUBLIC_URL", "https://bayi.servisplus.net.tr")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(s: Any, n: int = 300) -> str:
    return re.sub(r"[<>]", "", str(s or "")).strip()[:n]


# id, grup, ad, açıklama, varsayılan
MODULES = [
    ("iyzico", "Ödeme", "iyzico ile kartla ödeme", "Mağazada kredi/banka kartı ile ödeme (3D Secure, taksit). Anahtarlar girilmeden sitede görünmez.", False),
    ("trendyol", "Pazaryeri", "Trendyol", "Sipariş çekme, stok/fiyat gönderme.", False),
    ("hepsiburada", "Pazaryeri", "Hepsiburada", "Sipariş çekme, stok/fiyat gönderme.", False),
    ("n11", "Pazaryeri", "N11", "Sipariş çekme, stok/fiyat gönderme.", False),
    ("seo_bulk", "SEO", "Toplu SEO güncelleme", "Sayfa yoluna göre başlık / açıklama / robots kuralları.", False),
    ("log404", "SEO", "404 yönetimi", "Bulunamayan adresleri kaydeder.", False),
    ("redirects", "SEO", "301 yönlendirmeleri", "Eski adresleri yenisine yönlendirir.", False),
    ("links", "SEO", "Link yönetimi", "Sayfa metninde geçen ifadeleri bağlantıya çevirir.", False),
    ("keywords", "SEO", "Google arama önerisi (anahtar kelime)", "Panelde anahtar kelime fikirleri üretir.", True),
    ("rich_snippets", "SEO", "Google Rich Snippets", "İşletme (LocalBusiness) zengin sonuç verisi.", False),
    ("breadcrumb", "SEO", "Breadcrumb (ekmek kırıntısı)", "BreadcrumbList verisi ekler.", False),
    ("social", "Sosyal Medya", "Sosyal medya hesapları", "Instagram, Facebook, X, YouTube, TikTok, LinkedIn, WhatsApp vb. Girilenler sitenin alt bilgisinde simge olarak çıkar, Google'a 'sameAs' olarak bildirilir. Boş bırakılan görünmez. Hesap adı (ör. servisplustr) veya tam adres yazılabilir.", False),
    ("turnstile", "Güvenlik", "Cloudflare Turnstile (CAPTCHA)", "Giriş ekranında bot koruması. Site ve gizli anahtar girilip açılınca giriş formunda robot doğrulaması çıkar.", False),
    ("ga4", "Takip", "Google Analytics 4", "GA4 ölçüm kodunu siteye ekler.", False),
    ("ads", "Takip", "Google Ads dönüşüm", "Form/sipariş dönüşümlerini Ads'e gönderir.", False),
    ("yandex", "Takip", "Yandex Metrika", "Metrika kodunu siteye ekler.", False),
    ("fb_pixel", "Takip", "Meta Pixel", "Tarayıcı pikseli.", False),
    ("fb_capi", "Takip", "Facebook Dönüşüm API (CAPI)", "Dönüşümleri sunucudan Meta'ya gönderir.", False),
    ("merchant", "Takip", "Google Merchant (ürün akışı)", "Merchant Center için XML ürün akışı: /api/public/feeds/merchant.xml", False),
    ("merchant_api", "Takip", "Google Merchant API", "Kimlik bilgisi girilir; ürünleri Merchant'a API ile gönderir.", False),
]
_SOC_BASE = {"instagram": "https://www.instagram.com/%s/", "facebook": "https://www.facebook.com/%s", "x": "https://x.com/%s", "tiktok": "https://www.tiktok.com/@%s",
             "pinterest": "https://www.pinterest.com/%s/", "telegram": "https://t.me/%s"}


def social_links(conf: dict) -> dict:
    """Panelde girilen sosyal hesapları güvenli, tam adrese çevirir (yalnızca http/https; boşlar atılır)."""
    out = {}
    for k, v in (conf or {}).items():
        v = str(v or "").strip()
        if not v or k not in CONFIG_FIELDS["social"]:
            continue
        if k == "whatsapp":
            d = re.sub(r"\D", "", v)
            d = ("90" + d[-10:]) if len(d) >= 10 else ""
            if d:
                out[k] = "https://wa.me/" + d
            continue
        if re.match(r"^https?://", v, re.I):
            out[k] = v[:300]
        elif k in _SOC_BASE and re.match(r"^@?[A-Za-z0-9._-]{2,60}$", v):
            out[k] = _SOC_BASE[k] % v.lstrip("@")
        elif re.match(r"^(www\.)?[a-z0-9.-]+\.[a-z]{2,}/\S*$", v, re.I):
            out[k] = "https://" + v[:290]
    return out


MODULE_IDS = [m[0] for m in MODULES]

CONFIG_FIELDS = {
    "iyzico": {"api_key": ("API Anahtarı", True), "secret_key": ("Gizli Anahtar", True), "sandbox": ("Test (sandbox) modu: 1 = test, 0 = canlı", False)},
    "trendyol": {"seller_id": ("Satıcı ID", False), "api_key": ("API Key", True), "api_secret": ("API Secret", True)},
    "hepsiburada": {"merchant_id": ("Merchant ID", False), "service_key": ("Servis Anahtarı", True), "developer": ("Geliştirici kullanıcı adı", False)},
    "n11": {"app_key": ("App Key", True), "app_secret": ("App Secret", True)},
    "social": {"instagram": ("Instagram (hesap adı veya adres)", False), "facebook": ("Facebook sayfası (ad veya adres)", False), "x": ("X / Twitter (hesap adı veya adres)", False),
               "youtube": ("YouTube kanalı (adres)", False), "tiktok": ("TikTok (hesap adı veya adres)", False), "linkedin": ("LinkedIn şirket sayfası (adres)", False),
               "pinterest": ("Pinterest (hesap adı veya adres)", False), "telegram": ("Telegram (kullanıcı adı veya adres)", False),
               "whatsapp": ("WhatsApp numarası (905xxxxxxxxx)", False), "google_review": ("Google işletme yorum bağlantısı (g.page/...)", False)},
    "turnstile": {"site_key": ("Site anahtarı (Site Key)", False), "secret_key": ("Gizli anahtar (Secret Key)", True)},
    "ga4": {"measurement_id": ("Ölçüm ID (G-XXXX)", False)},
    "ads": {"ads_id": ("Ads ID (AW-XXXX)", False), "form_label": ("Form dönüşüm etiketi", False), "order_label": ("Sipariş dönüşüm etiketi", False)},
    "yandex": {"counter_id": ("Sayaç ID", False)},
    "fb_pixel": {"pixel_id": ("Pixel ID", False)},
    "fb_capi": {"pixel_id": ("Pixel ID", False), "access_token": ("Erişim Jetonu", True), "test_code": ("Test event kodu (opsiyonel)", False)},
    "merchant": {"brand": ("Varsayılan marka", False)},
    "merchant_api": {"merchant_id": ("Merchant Center ID", False), "access_token": ("OAuth erişim jetonu", True)},
    "links": {"rules": ('Kural listesi (JSON): [{"find":"kombi servisi","url":"/kombi-servisi/"}]', False)},
    "rich_snippets": {"org_name": ("Firma adı", False), "org_phone": ("Telefon", False), "org_logo": ("Logo URL", False)},
}


class ModulesIn(BaseModel):
    flags: Optional[Dict[str, bool]] = None
    config: Optional[Dict[str, Dict[str, Any]]] = None


class RedirectIn(BaseModel):
    source: str
    target: str
    code: int = 301
    active: bool = True


class SeoRuleIn(BaseModel):
    prefix: str
    title: Optional[str] = ""
    description: Optional[str] = ""
    robots: Optional[str] = ""
    canonical: Optional[str] = ""
    active: bool = True


class AdminOrderItem(BaseModel):
    product_id: str
    qty: int = 1


class AdminOrderIn(BaseModel):
    name: str
    phone: str
    email: Optional[str] = ""
    address: Optional[str] = ""
    city: Optional[str] = ""
    district: Optional[str] = ""
    note: Optional[str] = ""
    status: str = "odeme_bekliyor"
    items: List[AdminOrderItem]


class TrackIn(BaseModel):
    event: str
    value: Optional[float] = 0
    email: Optional[str] = ""
    phone: Optional[str] = ""
    url: Optional[str] = ""
    event_id: Optional[str] = ""


class Hit404In(BaseModel):
    path: str
    referrer: Optional[str] = ""


class PayInit(BaseModel):
    order_no: str
    phone: str


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    verify_password = deps["verify_password"]
    JWT_SECRET = deps["JWT_SECRET"]
    JWT_ALGORITHM = deps["JWT_ALGORITHM"]
    adm = Depends(require_admin)

    # ------------------------------------------------------------ yardımcılar
    async def modules_doc() -> dict:
        d = await db.app_settings.find_one({"_id": "sp_modules"}, {"_id": 0}) or {}
        flags = {m[0]: m[4] for m in MODULES}
        flags.update({k: bool(v) for k, v in (d.get("flags") or {}).items() if k in flags})
        return {"flags": flags, "config": d.get("config") or {}}

    async def cfg(mid: str) -> dict:
        return (await modules_doc())["config"].get(mid, {})

    async def site_features() -> dict:
        d = await db.app_settings.find_one({"_id": "site_features"}, {"_id": 0}) or {}
        out = {**shopmod.FEATURES_DEFAULT, **d}
        out["quick_request"] = {**shopmod.FEATURES_DEFAULT["quick_request"], **(d.get("quick_request") or {})}
        return out

    async def shop_cfg() -> dict:
        d = await db.app_settings.find_one({"_id": "shop_settings"}, {"_id": 0}) or {}
        return {**shopmod.SHOP_DEFAULT, **d}

    def masked(config: dict) -> dict:
        out = {}
        for mid, vals in (config or {}).items():
            fields = CONFIG_FIELDS.get(mid, {})
            out[mid] = {k: (("•" * 6 + str(v)[-3:]) if fields.get(k, ("", False))[1] and v else v) for k, v in (vals or {}).items()}
        return out

    # ------------------------------------------------------------ modüller (yönetim)
    @api_router.get("/admin/modules")
    async def get_modules(_: dict = adm):
        d = await modules_doc()
        f = await site_features()
        return {
            "site": {"shop_enabled": bool(f["shop_enabled"]), "customer_portal_enabled": bool(f["customer_portal_enabled"]),
                     "quick_request": bool(f["quick_request"]["enabled"]), "language_enabled": bool(f["language_enabled"])},
            "modules": [{"id": m[0], "group": m[1], "label": m[2], "desc": m[3], "enabled": d["flags"][m[0]],
                         "fields": [{"key": k, "label": v[0], "secret": v[1]} for k, v in CONFIG_FIELDS.get(m[0], {}).items()]} for m in MODULES],
            "config": masked(d["config"]),
            "urls": {"merchant_feed": f"{PANEL_URL}/api/public/feeds/merchant.xml"},
        }

    @api_router.put("/admin/modules")
    async def put_modules(p: ModulesIn, _: dict = adm):
        cur = await db.app_settings.find_one({"_id": "sp_modules"}, {"_id": 0}) or {"flags": {}, "config": {}}
        flags, conf = cur.get("flags") or {}, cur.get("config") or {}
        for k, v in (p.flags or {}).items():
            if k in MODULE_IDS:
                flags[k] = bool(v)
        for mid, vals in (p.config or {}).items():
            if mid not in CONFIG_FIELDS:
                continue
            tgt = conf.get(mid, {})
            for k, v in (vals or {}).items():
                if k not in CONFIG_FIELDS[mid]:
                    continue
                if CONFIG_FIELDS[mid][k][1] and isinstance(v, str) and v.startswith("••"):
                    continue  # maskeli değer değişmedi
                tgt[k] = clean(v, 4000 if k == "rules" else 300)
            conf[mid] = tgt
        await db.app_settings.update_one({"_id": "sp_modules"}, {"$set": {"flags": flags, "config": conf, "updated_at": now_iso()}}, upsert=True)
        return await get_modules(_)

    # ------------------------------------------------------------ site için herkese açık yapılandırma
    @api_router.get("/public/site-modules")
    async def site_modules():
        d = await modules_doc()
        sf = await site_features()
        f, c = dict(d["flags"]), d["config"]
        f["shop"] = bool(sf["shop_enabled"])
        f["accounts"] = bool(sf["customer_portal_enabled"])
        f["quick_request"] = bool(sf["quick_request"]["enabled"])
        tags = {}
        if f["ga4"] and c.get("ga4", {}).get("measurement_id"):
            tags["ga4"] = c["ga4"]["measurement_id"]
        if f["ads"] and c.get("ads", {}).get("ads_id"):
            a = c["ads"]
            tags["ads"] = {"id": a["ads_id"], "form": a.get("form_label", ""), "order": a.get("order_label", "")}
        if f["yandex"] and c.get("yandex", {}).get("counter_id"):
            tags["yandex"] = c["yandex"]["counter_id"]
        if f["fb_pixel"] and c.get("fb_pixel", {}).get("pixel_id"):
            tags["fb"] = c["fb_pixel"]["pixel_id"]
        if f["fb_capi"] and c.get("fb_capi", {}).get("access_token"):
            tags["capi"] = True
        seo = {}
        if f["seo_bulk"]:
            seo["rules"] = await db.sp_seo_rules.find({"active": True}, {"_id": 0}).to_list(500)
        if f["redirects"]:
            seo["redirects"] = await db.sp_redirects.find({"active": True}, {"_id": 0, "source": 1, "target": 1, "code": 1}).to_list(3000)
        if f["links"]:
            try:
                seo["links"] = json.loads((c.get("links") or {}).get("rules") or "[]")
            except Exception:
                seo["links"] = []
        if f["rich_snippets"]:
            seo["rich"] = c.get("rich_snippets", {})
        seo["breadcrumb"] = bool(f["breadcrumb"])
        seo["log404"] = bool(f["log404"])
        pay = {"iyzico": bool(f["iyzico"] and c.get("iyzico", {}).get("api_key") and c.get("iyzico", {}).get("secret_key"))}
        social = social_links(c.get("social") or {})  # veri girildiyse modül açma gerekmez
        return JSONResponse({"flags": f, "tags": tags, "seo": seo, "pay": pay, "social": social, "v": int(time.time())}, headers={"Cache-Control": "public, max-age=30"})

    # ------------------------------------------------------------ Google Merchant ürün akışı
    @api_router.get("/public/feeds/merchant.xml")
    async def merchant_feed():
        d = await modules_doc()
        if not d["flags"]["merchant"]:
            raise HTTPException(status_code=404, detail="Kapalı")
        brand = (d["config"].get("merchant") or {}).get("brand") or "ServisPlus"
        prods = await db.shop_products.find({"active": True}, {"_id": 0}).to_list(2000)
        esc = lambda x: (str(x or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        items = []
        for p in prods:
            img = (p.get("images") or [""])[0]
            if img.startswith("/"):
                img = PANEL_URL + img
            av = "in stock" if (not p.get("track_stock", True) or int(p.get("stock", 0)) > 0) else "out of stock"
            items.append(f"<item><g:id>{esc(p['id'])}</g:id><title>{esc(p['name'])}</title><description>{esc(p.get('description') or p.get('short') or p['name'])}</description>"
                         f"<link>{PUBLIC_SITE}/magaza/?urun={esc(p.get('slug', p['id']))}</link>" + (f"<g:image_link>{esc(img)}</g:image_link>" if img else "") +
                         f"<g:availability>{av}</g:availability><g:price>{float(p.get('price', 0)):.2f} TRY</g:price><g:brand>{esc(p.get('brand') or brand)}</g:brand>"
                         f"<g:condition>new</g:condition>" + (f"<g:mpn>{esc(p['sku'])}</g:mpn>" if p.get("sku") else "<g:identifier_exists>no</g:identifier_exists>") + "</item>")
        xml = ('<?xml version="1.0" encoding="UTF-8"?><rss xmlns:g="http://base.google.com/ns/1.0" version="2.0"><channel><title>ServisPlus Mağaza</title>'
               f"<link>{PUBLIC_SITE}</link><description>ServisPlus ürünleri</description>{''.join(items)}</channel></rss>")
        return Response(xml, media_type="application/xml")

    @api_router.post("/admin/merchant-api/push")
    async def merchant_api_push(_: dict = adm):
        d = await modules_doc()
        c = d["config"].get("merchant_api", {})
        if not (d["flags"]["merchant_api"] and c.get("merchant_id") and c.get("access_token")):
            raise HTTPException(status_code=400, detail="Merchant API kapalı ya da kimlik bilgisi eksik")
        prods = await db.shop_products.find({"active": True}, {"_id": 0}).to_list(500)
        ok, errs = 0, []
        for p in prods:
            img = (p.get("images") or [""])[0]
            img = PANEL_URL + img if img.startswith("/") else img
            body = {"offerId": p["id"], "contentLanguage": "tr", "feedLabel": "TR",
                    "productAttributes": {"title": p["name"], "description": p.get("description") or p["name"], "link": f"{PUBLIC_SITE}/magaza/?urun={p.get('slug', p['id'])}",
                                          "imageLink": img, "availability": "IN_STOCK" if (not p.get("track_stock", True) or int(p.get("stock", 0)) > 0) else "OUT_OF_STOCK",
                                          "price": {"amountMicros": str(int(float(p.get("price", 0)) * 1_000_000)), "currencyCode": "TRY"}, "condition": "NEW",
                                          "brand": p.get("brand") or "ServisPlus"}}
            try:
                r = await asyncio.to_thread(lambda: requests.post(f"https://merchantapi.googleapis.com/products/v1/accounts/{c['merchant_id']}/productInputs:insert",
                                  headers={"Authorization": "Bearer " + c["access_token"], "Content-Type": "application/json"}, data=json.dumps(body), timeout=20))
                if r.status_code < 300:
                    ok += 1
                else:
                    errs.append(f"{p['id']}: {r.status_code} {r.text[:120]}")
            except Exception as e:
                errs.append(f"{p['id']}: {str(e)[:100]}")
        return {"ok": ok > 0 and not errs, "sent": ok, "errors": errs[:5],
                "note": "Merchant API OAuth jetonu ve veri kaynağı (dataSource) ayarı hesabınıza göre gerekebilir; hata alırsanız XML akışını (Merchant Center > Akışlar) kullanın."}

    # ------------------------------------------------------------ 404 / yönlendirme / SEO
    @api_router.post("/public/seo/hit-404")
    async def hit_404(p: Hit404In):
        d = await modules_doc()
        if not d["flags"]["log404"]:
            return {"ok": True}
        path = clean(p.path, 300).split("?")[0]
        if not path.startswith("/") or len(path) < 2:
            return {"ok": True}
        await db.sp_404.update_one({"path": path}, {"$inc": {"hits": 1}, "$set": {"last": now_iso(), "referrer": clean(p.referrer, 300)},
                                                   "$setOnInsert": {"id": uuid.uuid4().hex, "first": now_iso()}}, upsert=True)
        return {"ok": True}

    @api_router.get("/admin/404")
    async def list_404(_: dict = adm):
        return await db.sp_404.find({}, {"_id": 0}).sort("hits", -1).to_list(500)

    @api_router.delete("/admin/404/{rid}")
    async def del_404(rid: str, _: dict = adm):
        await db.sp_404.delete_one({"id": rid})
        return {"ok": True}

    def norm_src(s: str) -> str:
        s = re.sub(r"^https?://[^/]+", "", clean(s, 300))
        return s if s.startswith("/") else "/" + s

    @api_router.get("/admin/redirects")
    async def list_redirects(_: dict = adm):
        return await db.sp_redirects.find({}, {"_id": 0}).sort("created_at", -1).to_list(3000)

    @api_router.post("/admin/redirects")
    async def add_redirect(p: RedirectIn, _: dict = adm):
        src, tgt = norm_src(p.source), clean(p.target, 400)
        if not tgt or src == tgt:
            raise HTTPException(status_code=422, detail="Hedef adres geçersiz")
        if p.code not in (301, 302):
            raise HTTPException(status_code=422, detail="Kod 301 veya 302 olmalı")
        await db.sp_redirects.update_one({"source": src}, {"$set": {"target": tgt, "code": p.code, "active": p.active, "created_at": now_iso()},
                                                          "$setOnInsert": {"id": uuid.uuid4().hex}}, upsert=True)
        await db.sp_404.delete_one({"path": src})
        return await db.sp_redirects.find_one({"source": src}, {"_id": 0})

    @api_router.delete("/admin/redirects/{rid}")
    async def del_redirect(rid: str, _: dict = adm):
        await db.sp_redirects.delete_one({"id": rid})
        return {"ok": True}

    @api_router.get("/admin/redirects-htaccess")
    async def redirects_htaccess(_: dict = adm):
        rows = await db.sp_redirects.find({"active": True}, {"_id": 0}).to_list(3000)
        lines = ["# ServisPlus panelinden üretildi — gerçek HTTP yönlendirmesi için .htaccess dosyanıza ekleyin"]
        for r in rows:
            tgt = r["target"] if r["target"].startswith("http") else PUBLIC_SITE + r["target"]
            lines.append(f"Redirect {r['code']} {r['source']} {tgt}")
        return {"text": "\n".join(lines)}

    @api_router.get("/admin/seo")
    async def list_seo(_: dict = adm):
        return await db.sp_seo_rules.find({}, {"_id": 0}).sort("prefix", 1).to_list(500)

    @api_router.post("/admin/seo")
    async def add_seo(p: SeoRuleIn, _: dict = adm):
        pre = norm_src(p.prefix)
        doc = {"prefix": pre, "title": clean(p.title, 200), "description": clean(p.description, 400), "robots": clean(p.robots, 60),
               "canonical": clean(p.canonical, 300), "active": p.active, "updated_at": now_iso()}
        await db.sp_seo_rules.update_one({"prefix": pre}, {"$set": doc, "$setOnInsert": {"id": uuid.uuid4().hex}}, upsert=True)
        return await db.sp_seo_rules.find_one({"prefix": pre}, {"_id": 0})

    @api_router.delete("/admin/seo/{rid}")
    async def del_seo(rid: str, _: dict = adm):
        await db.sp_seo_rules.delete_one({"id": rid})
        return {"ok": True}

    @api_router.get("/admin/keywords")
    async def keywords(q: str, _: dict = adm):
        q = clean(q, 80)
        if len(q) < 2:
            return {"items": []}
        out, seen = [], set()
        for suffix in ["", " a", " b", " c", " d", " f", " k", " m", " s", " t", " fiyat", " servisi", " ankara"]:
            try:
                r = await asyncio.to_thread(lambda: requests.get("https://suggestqueries.google.com/complete/search", params={"client": "firefox", "hl": "tr", "gl": "tr", "q": q + suffix}, timeout=6))
                for it in r.json()[1]:
                    if it not in seen:
                        seen.add(it)
                        out.append(it)
            except Exception:
                continue
        if not out:
            raise HTTPException(status_code=502, detail="Google öneri servisine erişilemedi")
        return {"items": out[:80], "note": "Aylık arama hacmi için Google Ads Keyword Planner hesabı bağlanmalıdır; burada Google arama önerileri listelenir."}

    # ------------------------------------------------------------ Meta CAPI
    @api_router.post("/public/capi-track")
    async def capi_track(p: TrackIn, request: Request):
        d = await modules_doc()
        c = d["config"].get("fb_capi", {})
        if not (d["flags"]["fb_capi"] and c.get("pixel_id") and c.get("access_token")):
            return {"ok": True, "sent": False}
        sha = lambda x: hashlib.sha256(x.strip().lower().encode()).hexdigest() if x else None
        ph = re.sub(r"\D", "", p.phone or "")
        if len(ph) == 11 and ph.startswith("0"):
            ph = "9" + ph
        elif len(ph) == 10:
            ph = "90" + ph
        xf = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "")
        ud = {k: v for k, v in {"em": [sha(p.email)] if p.email else None, "ph": [sha(ph)] if ph else None, "client_ip_address": xf,
                                "client_user_agent": request.headers.get("user-agent", "")}.items() if v}
        ev = {"event_name": clean(p.event, 40) or "Lead", "event_time": int(time.time()), "action_source": "website", "event_source_url": clean(p.url, 300),
              "event_id": clean(p.event_id, 60) or uuid.uuid4().hex, "user_data": ud}
        if p.value:
            ev["custom_data"] = {"value": float(p.value), "currency": "TRY"}
        body = {"data": [ev]}
        if c.get("test_code"):
            body["test_event_code"] = c["test_code"]
        try:
            r = await asyncio.to_thread(lambda: requests.post(f"https://graph.facebook.com/v19.0/{c['pixel_id']}/events", params={"access_token": c["access_token"]}, json=body, timeout=8))
            return {"ok": r.ok, "sent": r.ok}
        except Exception as e:
            log.warning("capi: %s", e)
            return {"ok": False, "sent": False}

    # ------------------------------------------------------------ yönetici sipariş oluşturma (mağaza siparişlerine yazar)
    @api_router.post("/shop/orders-create")
    async def admin_order_create(p: AdminOrderIn, _: dict = adm):
        if not p.items:
            raise HTTPException(status_code=422, detail="En az bir ürün seçin")
        if not shopmod.valid_phone(p.phone):
            raise HTTPException(status_code=422, detail="Geçerli telefon girin")
        items, sub, done = [], 0.0, []
        for it in p.items:
            pr = await db.shop_products.find_one({"id": it.product_id}, {"_id": 0})
            if not pr:
                raise HTTPException(status_code=422, detail="Ürün bulunamadı")
            q = max(1, min(999, it.qty))
            r = await db.shop_products.update_one({"id": pr["id"], "$or": [{"track_stock": False}, {"stock": {"$gte": q}}]}, {"$inc": {"stock": -q, "sold": q}})
            if not r.modified_count:
                for d in done:
                    await db.shop_products.update_one({"id": d["product_id"], "track_stock": True}, {"$inc": {"stock": d["qty"], "sold": -d["qty"]}})
                raise HTTPException(status_code=409, detail=f"“{pr['name']}” için yeterli stok yok")
            line = round(float(pr.get("price", 0)) * q, 2)
            sub += line
            row = {"product_id": pr["id"], "name": pr["name"], "brand": pr.get("brand", ""), "model": pr.get("model", ""), "price": pr["price"], "qty": q,
                   "line_total": line, "image": (pr.get("images") or [""])[0]}
            items.append(row)
            done.append(row)
        cfg_ = await shop_cfg()
        ship = 0.0 if (cfg_["free_shipping_over"] and sub >= cfg_["free_shipping_over"]) else float(cfg_["shipping_fee"] or 0)
        status = p.status if p.status in shopmod.ORDER_STATUSES else "odeme_bekliyor"
        n = await db.shop_orders.count_documents({})
        while True:
            n += 1
            no = f"{cfg_['order_prefix'] or 'SP'}-{datetime.now(timezone.utc).strftime('%y%m')}-{n:04d}"
            if not await db.shop_orders.find_one({"order_no": no}, {"_id": 1}):
                break
        acc = await db.customer_accounts.find_one({"phone_key": shopmod.phone_key(p.phone)}, {"_id": 0, "id": 1})
        order = {"id": shopmod._id(), "order_no": no, "status": status,
                 "customer": {"name": clean(p.name, 120), "phone": clean(p.phone, 30), "email": clean(p.email, 120), "city": clean(p.city, 60),
                              "district": clean(p.district, 60), "address": clean(p.address, 400)},
                 "note": clean(p.note, 500), "items": items, "subtotal": round(sub, 2), "shipping": ship, "total": round(sub + ship, 2),
                 "account_id": (acc or {}).get("id", ""), "phone_key": shopmod.phone_key(p.phone), "payment": {}, "admin_note": "Panelden oluşturuldu",
                 "tracking_no": "", "carrier": "", "source": "panel", "history": [{"status": status, "at": now_iso()}], "created_at": now_iso(), "updated_at": now_iso()}
        await db.shop_orders.insert_one(dict(order))
        order.pop("_id", None)
        return order

    # ------------------------------------------------------------ site kataloğunu panele aktarma (ilk kurulum)
    @api_router.post("/shop/import-site-catalog")
    async def import_catalog(_: dict = adm):
        f = HERE / "seed_catalog.json"
        if not f.exists():
            raise HTTPException(status_code=404, detail="seed_catalog.json bulunamadı")
        data = json.loads(f.read_text(encoding="utf-8"))
        cats = {c["id"]: c["name"] for c in data.get("categories", [])}
        added = 0
        for i, p in enumerate(data.get("products", [])):
            if await db.shop_products.find_one({"id": p["id"]}, {"_id": 1}):
                continue
            await db.shop_products.insert_one({
                "id": p["id"], "slug": p["id"], "name": p["name"], "brand": "", "model": "", "category": cats.get(p.get("cat"), p.get("cat", "")),
                "price": float(p.get("price", 0)), "old_price": float(p.get("old", 0) or 0), "stock": 100, "track_stock": False, "short": "",
                "description": p.get("desc", ""), "specs": [], "images": [], "badge": p.get("badge", ""), "featured": False, "active": True, "sort": i + 1,
                "sku": p["id"], "icon": p.get("icon", "box"), "created_at": now_iso(), "updated_at": now_iso()})
            added += 1
        return {"ok": True, "added": added}

    # ------------------------------------------------------------ iyzico
    async def iyzico_call(path: str, body: dict) -> dict:
        c = await shopmod.iyzico_keys(db)
        if not c:
            raise HTTPException(status_code=400, detail="iyzico anahtarları girilmemiş")
        base = "https://sandbox-api.iyzipay.com" if str(c.get("sandbox", "1")) not in ("0", "false", "") else "https://api.iyzipay.com"
        raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        rnd = str(int(time.time() * 1000)) + str(random.randint(100000, 999999))
        sig = hmac.new(c["secret_key"].encode(), (rnd + path + raw).encode(), hashlib.sha256).hexdigest()
        auth = base64.b64encode(f"apiKey:{c['api_key']}&randomKey:{rnd}&signature:{sig}".encode()).decode()
        try:
            r = await asyncio.to_thread(lambda: requests.post(base + path, data=raw.encode("utf-8"), timeout=25,
                              headers={"Authorization": "IYZWSv2 " + auth, "x-iyzi-rnd": rnd, "Content-Type": "application/json", "Accept": "application/json"}))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"iyzico'ya bağlanılamadı: {str(e)[:120]}")
        try:
            return r.json()
        except Exception:
            raise HTTPException(status_code=502, detail="iyzico yanıtı okunamadı")

    async def call_iy(path: str, body: dict) -> dict:
        return await (shopmod.IYZICO.get("call") or iyzico_call)(path, body)      # testlerde taklit edilebilsin

    def site_origin(request: Request) -> str:
        """Ödeme dönüşü, siparişin verildiği sitenin kendi alan adına yapılır (platform adresine değil)."""
        host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or "").split(",")[0].strip()
        host = re.sub(r"[^A-Za-z0-9.:\-]", "", host)
        return f"https://{host}" if host else ""

    @api_router.post("/public/shop/pay/iyzico/init")
    async def iyzico_init(p: PayInit, request: Request):
        if not await shopmod.iyzico_keys(db):
            raise HTTPException(status_code=403, detail="Kartla ödeme şu an kapalı")
        o = await db.shop_orders.find_one({"order_no": clean(p.order_no, 30).upper()}, {"_id": 0})
        if not o or shopmod.phone_key(p.phone) != o.get("phone_key"):
            raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
        if (o.get("payment") or {}).get("method") != "kart":
            raise HTTPException(status_code=409, detail="Bu sipariş kartla ödeme için oluşturulmadı")
        if o["status"] != "odeme_bekliyor":
            raise HTTPException(status_code=409, detail="Bu sipariş için ödeme beklenmiyor")
        cu = o["customer"]
        fullname = cu["name"].split()
        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "85.34.78.112")
        basket = [{"id": ln["product_id"], "name": ln["name"][:60], "category1": "Mağaza", "itemType": "PHYSICAL", "price": f"{ln['line_total']:.2f}"} for ln in o["items"]]
        if o.get("shipping"):
            basket.append({"id": "kargo", "name": "Kargo", "category1": "Kargo", "itemType": "PHYSICAL", "price": f"{o['shipping']:.2f}"})
        if abs(sum(float(b["price"]) for b in basket) - float(o["total"])) > 0.01:
            raise HTTPException(status_code=409, detail="Sipariş tutarı doğrulanamadı; lütfen yeni sipariş verin")
        total = f"{o['total']:.2f}"
        origin = site_origin(request)
        if not origin:
            raise HTTPException(status_code=400, detail="Site adresi belirlenemedi")
        addr = {"contactName": cu["name"], "city": cu.get("city") or "Ankara", "country": "Turkey", "address": cu.get("address") or "Adres"}
        body = {"locale": "tr", "conversationId": o["order_no"], "price": total, "paidPrice": total, "currency": "TRY", "basketId": o["order_no"], "paymentGroup": "PRODUCT",
                "callbackUrl": f"{origin}/api/public/shop/pay/iyzico/callback", "enabledInstallments": [1, 2, 3, 6, 9],
                "buyer": {"id": o["id"][:20], "name": fullname[0] if fullname else "Müşteri", "surname": " ".join(fullname[1:]) or "-",
                          "gsmNumber": "+90" + shopmod.phone_key(cu["phone"]), "email": cu.get("email") or "", "identityNumber": "11111111111",
                          "registrationAddress": addr["address"], "ip": ip, "city": addr["city"], "country": "Turkey"},
                "shippingAddress": addr, "billingAddress": addr, "basketItems": basket}
        res = await call_iy("/payment/iyzipos/checkoutform/initialize/auth/ecom", body)
        if res.get("status") != "success":
            raise HTTPException(status_code=502, detail=res.get("errorMessage") or "iyzico ödeme formu açılamadı")
        await db.shop_orders.update_one({"id": o["id"]}, {"$set": {"iyzico_token": res.get("token")}})
        return {"ok": True, "url": res.get("paymentPageUrl"), "token": res.get("token")}

    @api_router.post("/public/shop/pay/iyzico/callback")
    async def iyzico_callback(request: Request):
        origin = site_origin(request)
        back = lambda q: RedirectResponse(f"{origin}/?{q}#magaza", status_code=303)      # noqa: E731
        form = await request.form()
        token = str(form.get("token") or "")
        o = await db.shop_orders.find_one({"iyzico_token": token}, {"_id": 0}) if token else None
        if not o:
            return back("odeme=hata")
        res = await call_iy("/payment/iyzipos/checkoutform/auth/ecom/detail", {"locale": "tr", "conversationId": o["order_no"], "token": token})
        ok = res.get("status") == "success" and res.get("paymentStatus") == "SUCCESS"
        if ok:
            try:
                paid = round(float(res.get("paidPrice") or 0), 2)
            except (TypeError, ValueError):
                paid = 0.0
            if abs(paid - float(o["total"])) > 0.01 or str(res.get("currency", "TRY")) != "TRY" or str(res.get("basketId", o["order_no"])) != o["order_no"]:
                await db.shop_orders.update_one({"id": o["id"]}, {"$set": {"flag": "odeme_tutar_uyusmazligi", "updated_at": now_iso(),
                    "payment": {**(o.get("payment") or {}), "status": "uyusmazlik", "provider": "iyzico", "payment_id": res.get("paymentId"), "paid": paid}}})
                try:
                    await shopmod.notify.notify_owner_t(db, f"DİKKAT: {o['order_no']} iyzico tutarı uyuşmuyor (sipariş {o['total']} / ödenen {paid}). Elle kontrol edin.", kind="shop_payment")
                except Exception:                      # noqa: BLE001
                    pass
                return back(f"odeme=kontrol&no={o['order_no']}")
            # tek seferlik geçiş: aynı geri dönüş iki kez gelse de sipariş bir kez onaylanır
            r = await db.shop_orders.update_one({"id": o["id"], "status": "odeme_bekliyor"}, {"$set": {"status": "onaylandi", "updated_at": now_iso(),
                "payment": {**(o.get("payment") or {}), "method": "kart", "status": "odendi", "provider": "iyzico", "payment_id": res.get("paymentId"), "amount": o["total"], "at": now_iso()}},
                "$push": {"history": {"status": "onaylandi", "at": now_iso(), "by": "iyzico"}}})
            if not r.modified_count and o["status"] == "iptal":
                # ödeme süresi dolup stok bırakılmışken para geldi: sipariş iptal kalmaz, elle ilgilenilsin
                await db.shop_orders.update_one({"id": o["id"]}, {"$set": {"flag": "iptal_siparise_odeme_geldi", "updated_at": now_iso()}})
                try:
                    await shopmod.notify.notify_owner_t(db, f"DİKKAT: {o['order_no']} iptal edilmişti ama kartla ödeme geldi. Müşteriyle görüşün veya iade edin.", kind="shop_payment")
                except Exception:                      # noqa: BLE001
                    pass
        return back(f"odeme={'ok' if ok else 'hata'}&no={o['order_no']}")

    @api_router.post("/admin/payments/iyzico/test")
    async def iyzico_test(_: dict = adm):
        res = await iyzico_call("/payment/bin/check", {"locale": "tr", "conversationId": "test", "binNumber": "554960"})
        return {"ok": res.get("status") == "success", "message": res.get("errorMessage") or "Bağlantı başarılı", "raw_status": res.get("status")}

    # ------------------------------------------------------------ pazaryerleri
    async def market_request(mid: str, method: str, url: str, **kw):
        c = await cfg(mid)
        h = kw.pop("headers", {})
        try:
            if mid == "trendyol":
                if not (c.get("seller_id") and c.get("api_key") and c.get("api_secret")):
                    raise HTTPException(status_code=400, detail="Trendyol bilgileri eksik")
                h.update({"Authorization": "Basic " + base64.b64encode(f"{c['api_key']}:{c['api_secret']}".encode()).decode(),
                          "User-Agent": f"{c['seller_id']} - SelfIntegration", "Content-Type": "application/json"})
            elif mid == "hepsiburada":
                if not (c.get("merchant_id") and c.get("service_key")):
                    raise HTTPException(status_code=400, detail="Hepsiburada bilgileri eksik")
                h.update({"Authorization": "Basic " + base64.b64encode(f"{c['merchant_id']}:{c['service_key']}".encode()).decode(),
                          "User-Agent": c.get("developer") or "servisplus_dev", "Content-Type": "application/json"})
            elif mid == "n11":
                if not (c.get("app_key") and c.get("app_secret")):
                    raise HTTPException(status_code=400, detail="N11 bilgileri eksik")
                h.update({"appkey": c["app_key"], "appsecret": c["app_secret"], "Content-Type": "application/json"})
            r = await asyncio.to_thread(lambda: requests.request(method, url, headers=h, timeout=25, **kw))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Bağlantı kurulamadı: {str(e)[:150]}")
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:300]}
        return r.status_code, data

    def market_urls(mid: str, c: dict) -> dict:
        if mid == "trendyol":
            b = f"https://apigw.trendyol.com/integration/order/sellers/{c.get('seller_id')}/orders"
            return {"orders": b + "?size=50&orderByField=PackageLastModifiedDate&orderByDirection=DESC",
                    "stock": f"https://apigw.trendyol.com/integration/inventory/sellers/{c.get('seller_id')}/products/price-and-inventory"}
        if mid == "hepsiburada":
            return {"orders": f"https://oms-external.hepsiburada.com/packages/merchantid/{c.get('merchant_id')}?limit=50&offset=0",
                    "stock": f"https://listing-external.hepsiburada.com/listings/merchantid/{c.get('merchant_id')}/inventory-uploads"}
        return {"orders": "https://api.n11.com/rest/delivery/v1/shipmentPackages?size=50", "stock": "https://api.n11.com/ms/product/tasks/price-stock-update"}

    def check_market(mid: str):
        if mid not in ("trendyol", "hepsiburada", "n11"):
            raise HTTPException(status_code=404, detail="Bilinmeyen pazaryeri")

    @api_router.post("/admin/market/{mid}/test")
    async def market_test(mid: str, _: dict = adm):
        check_market(mid)
        u = market_urls(mid, await cfg(mid))
        code, data = await market_request(mid, "GET", u["orders"])
        return {"ok": code < 300, "status": code, "message": "Bağlantı başarılı" if code < 300 else (str(data)[:200] or "Hata")}

    @api_router.post("/admin/market/{mid}/pull-orders")
    async def market_pull(mid: str, _: dict = adm):
        check_market(mid)
        u = market_urls(mid, await cfg(mid))
        code, data = await market_request(mid, "GET", u["orders"])
        if code >= 300:
            raise HTTPException(status_code=502, detail=f"{mid} yanıtı {code}: {str(data)[:200]}")
        rows = data.get("content") or data.get("items") or data.get("data") or data.get("shipmentPackages") or (data if isinstance(data, list) else [])
        n = 0
        for r in rows:
            key = str(r.get("orderNumber") or r.get("id") or r.get("packageNumber") or r.get("orderId") or uuid.uuid4().hex)
            doc = {"market": mid, "key": key, "raw": r, "pulled_at": now_iso(), "number": key,
                   "total": r.get("totalPrice") or r.get("totalAmount") or r.get("grossAmount") or 0,
                   "customer": (str(r.get("customerFirstName", "")) + " " + str(r.get("customerLastName", ""))).strip() or str(r.get("customerName") or ""),
                   "status": r.get("status") or r.get("packageStatus") or ""}
            await db.sp_market_orders.update_one({"market": mid, "key": key}, {"$set": doc}, upsert=True)
            n += 1
        return {"ok": True, "pulled": n}

    @api_router.get("/admin/market/orders")
    async def market_orders(_: dict = adm):
        return await db.sp_market_orders.find({}, {"_id": 0, "raw": 0}).sort("pulled_at", -1).to_list(500)

    @api_router.post("/admin/market/{mid}/push-stock")
    async def market_push(mid: str, _: dict = adm):
        check_market(mid)
        prods = await db.shop_products.find({"active": True, "sku": {"$nin": ["", None]}}, {"_id": 0}).to_list(1000)
        if not prods:
            raise HTTPException(status_code=422, detail="Ürünlerde SKU / barkod girilmemiş (Mağaza > Ürünler)")
        u = market_urls(mid, await cfg(mid))
        stock = lambda p: int(p.get("stock", 0)) if p.get("track_stock", True) else 999
        if mid == "trendyol":
            body = {"items": [{"barcode": p["sku"], "quantity": stock(p), "salePrice": float(p["price"]), "listPrice": float(p.get("old_price") or p["price"])} for p in prods]}
        elif mid == "hepsiburada":
            body = [{"merchantSku": p["sku"], "availableStock": stock(p), "price": float(p["price"])} for p in prods]
        else:
            body = {"payload": {"integrator": "ServisPlus", "skus": [{"stockCode": p["sku"], "quantity": stock(p), "listPrice": float(p.get("old_price") or p["price"]),
                                                                       "salePrice": float(p["price"]), "currencyType": "TL"} for p in prods]}}
        code, data = await market_request(mid, "POST", u["stock"], data=json.dumps(body))
        if code >= 300:
            raise HTTPException(status_code=502, detail=f"{mid} yanıtı {code}: {str(data)[:200]}")
        return {"ok": True, "sent": len(prods), "response": str(data)[:200]}

    # ------------------------------------------------------------ müşteri KVKK (verilerimi indir / hesabımı sil)
    async def cust_from_token(request: Request) -> dict:
        h = request.headers.get("authorization", "")
        tok = h[7:] if h.lower().startswith("bearer ") else ""
        try:
            pl = jwt.decode(tok, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except Exception:
            raise HTTPException(status_code=401, detail="Giriş yapmanız gerekiyor")
        acc = await db.customer_accounts.find_one({"id": pl.get("sub")}, {"_id": 0}) if pl.get("typ") == "customer" else None
        if not acc:
            raise HTTPException(status_code=401, detail="Hesap bulunamadı")
        return acc

    @api_router.get("/public/customer/export")
    async def cust_export(request: Request):
        acc = await cust_from_token(request)
        orders = await db.shop_orders.find({"$or": [{"account_id": acc["id"]}, {"phone_key": acc["phone_key"]}]}, {"_id": 0}).to_list(500)
        msgs = await db.contact_messages.find({"phone": acc["phone"]}, {"_id": 0, "ip": 0, "ua": 0}).to_list(500)
        acc.pop("password_hash", None)
        return {"hesap": acc, "siparisler": orders, "mesajlar": msgs}

    @api_router.post("/public/customer/delete")
    async def cust_delete(payload: dict, request: Request):
        acc = await cust_from_token(request)
        if not verify_password(str(payload.get("password", "")), acc["password_hash"]):
            raise HTTPException(status_code=401, detail="Şifre hatalı")
        await db.customer_accounts.delete_one({"id": acc["id"]})
        import notify as _n
        await _n.push_admins(db, "Müşteri hesabı silindi", f"{acc.get('name', '')} · {acc.get('phone', '')}", "/admin/customers")
        return {"ok": True}
