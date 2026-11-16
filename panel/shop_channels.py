# -*- coding: utf-8 -*-
"""Mağaza kanalları: TEK ürün kaydı (stok, kategori, marka, barkod) site mağazasını ve pazaryerlerini besler.

İlke: ürün ve stok bir kez tutulur (shop_products). Site, Trendyol, Hepsiburada, N11 ... bu kaydın "kanal" görünümleridir.
- Kategori: iç kategori ağacı (shop_categories) tek kaynaktır; her pazaryeri kategorisi bu ağaca eşlenir (market_catmap).
  Eşleme yoksa ürün o pazaryerine gönderilemez ("hazır değil" + eksik alan listesi).
- Stok: tek havuz. Kanal stoğu = havuz - kanal güvenlik payı. Siparişten/panelden/pazaryeri siparişinden stok değişince
  etkilenen ürünler kuyruğa (shop_sync_queue) alınır, her açık pazaryerine aynı değer gönderilir.
- Fiyat: varsayılan site fiyatıyla aynı; kanala özel fiyat girilirse ekranda "farklı" diye işaretlenir.
"""
import re
import uuid
from datetime import datetime, timezone

MARKETS = {
    "trendyol": {"name": "Trendyol", "live": True},
    "hepsiburada": {"name": "Hepsiburada", "live": True},
    "n11": {"name": "N11", "live": True},
    "ciceksepeti": {"name": "Çiçeksepeti", "live": True},
    "pazarama": {"name": "Pazarama", "live": True},
    "pttavm": {"name": "PttAVM", "live": True},
}
KDV_RATES = (0, 1, 10, 20)

# Her pazaryerinin ürün açarken zorunlu tuttuğu alanlar. (alan, etiket)
REQUIRED = {
    "trendyol": [("barcode", "Barkod"), ("sku", "Stok kodu"), ("name", "Ürün adı"), ("brand", "Marka"), ("category_map", "Trendyol kategori eşlemesi"),
                 ("brand_map", "Trendyol marka kodu"), ("images", "En az 1 görsel"), ("description", "Açıklama"), ("price", "Fiyat"), ("kdv", "KDV oranı"),
                 ("desi", "Desi"), ("attrs", "Kategorinin zorunlu özellikleri")],
    "hepsiburada": [("barcode", "Barkod"), ("sku", "Stok kodu (merchantSku)"), ("name", "Ürün adı"), ("brand", "Marka"), ("category_map", "Hepsiburada kategori eşlemesi"),
                    ("images", "En az 1 görsel"), ("description", "Açıklama"), ("price", "Fiyat"), ("kdv", "KDV oranı"), ("desi", "Desi"), ("attrs", "Kategorinin zorunlu özellikleri")],
    "n11": [("barcode", "Barkod"), ("sku", "Stok kodu"), ("name", "Ürün adı"), ("brand", "Marka"), ("category_map", "N11 kategori eşlemesi"),
            ("images", "En az 1 görsel"), ("description", "Açıklama"), ("price", "Fiyat"), ("kdv", "KDV oranı"), ("delivery_days", "Hazırlık süresi (gün)"),
            ("attrs", "Kategorinin zorunlu özellikleri")],
}
_BASIC = [("barcode", "Barkod"), ("sku", "Stok kodu"), ("name", "Ürün adı"), ("brand", "Marka"), ("category_map", "{m} kategori eşlemesi"),
          ("images", "En az 1 görsel"), ("description", "Açıklama"), ("price", "Fiyat"), ("kdv", "KDV oranı")]
for _mk, _nm in (("ciceksepeti", "Çiçeksepeti"), ("pazarama", "Pazarama"), ("pttavm", "PttAVM")):
    REQUIRED[_mk] = [(a, b.replace("{m}", _nm)) for a, b in _BASIC] + [("attrs", "Kategorinin zorunlu özellikleri")]
TITLE_MAX = {"trendyol": 100, "hepsiburada": 200, "n11": 255, "ciceksepeti": 150, "pazarama": 200, "pttavm": 200}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def gtin_valid(code: str) -> bool:
    """GTIN-8/12/13/14 sağlama basamağı (EAN/UPC)."""
    c = re.sub(r"\D", "", code or "")
    if len(c) not in (8, 12, 13, 14) or c != (code or "").strip():
        return False
    digits = [int(x) for x in c]
    chk = digits.pop()
    s = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(digits)))
    return (10 - s % 10) % 10 == chk


def clean_channels(raw, cur=None) -> dict:
    """Ürünün kanal ayarı: {market: {enabled, price (boş=site fiyatı), buffer}}; 'site' her zaman vardır."""
    cur = cur or {}
    out = {"site": {"enabled": bool((raw or {}).get("site", cur.get("site", {})).get("enabled", True))}}
    for mk in MARKETS:
        r = (raw or {}).get(mk) if isinstance((raw or {}).get(mk), dict) else None
        c = cur.get(mk) or {}
        if r is None and not c:
            continue
        base = {**c, **(r or {})}
        try:
            price = round(float(base.get("price") or 0), 2)
        except (TypeError, ValueError):
            price = 0.0
        try:
            buf = max(0, int(float(base.get("buffer") or 0)))
        except (TypeError, ValueError):
            buf = 0
        out[mk] = {"enabled": bool(base.get("enabled")), "price": max(0.0, price), "buffer": buf}
    return out


def channel_price(p: dict, mk: str) -> float:
    ch = (p.get("channels") or {}).get(mk) or {}
    return float(ch.get("price") or 0) or float(p.get("price") or 0)


def channel_stock(p: dict, mk: str) -> int:
    """Kanala bildirilecek stok. Takipsiz ürün pazaryerine hiç gönderilmez (0 = satışa kapalı)."""
    if not p.get("track_stock", True):
        return 0
    ch = (p.get("channels") or {}).get(mk) or {}
    if ch.get("enabled") is False or p.get("active") is False:      # kanal ya da ürün kapalı: pazaryerinde satışa kapat
        return 0
    return max(0, int(p.get("stock") or 0) - int(ch.get("buffer") or 0))


def issues(p: dict, mk: str, catmap: dict = None, brandmap: dict = None, settings: dict = None) -> list:
    """Ürünün bu pazaryerine gönderilebilmesi için eksikleri döndürür: [{'field','msg'}]. Boş liste = hazır."""
    out = []
    if mk not in REQUIRED:
        return [{"field": "market", "msg": "Bu pazaryeri henüz desteklenmiyor"}]
    cm = catmap or {}
    sc = settings or {}
    for f, lbl in REQUIRED[mk]:
        bad = False
        if f == "barcode":
            bad = not gtin_valid(p.get("barcode") or "")
            if bad and p.get("barcode"):
                out.append({"field": f, "msg": "Barkod geçersiz (GTIN sağlama basamağı tutmuyor)"})
                continue
        elif f == "category_map":
            bad = not cm.get("ext_id")
        elif f == "brand_map":
            bad = not (brandmap or {}).get((p.get("brand") or "").strip().lower())
        elif f == "images":
            bad = not [x for x in (p.get("images") or []) if str(x).startswith(("http://", "https://", "/"))]
        elif f == "description":
            bad = len(re.sub(r"<[^>]+>", "", p.get("description") or p.get("short") or "").strip()) < 30
        elif f == "price":
            bad = channel_price(p, mk) <= 0
        elif f == "kdv":
            bad = p.get("kdv") not in KDV_RATES
        elif f == "desi":
            bad = not float(p.get("desi") or 0) > 0
        elif f == "delivery_days":
            bad = int(p.get("delivery_days") or 0) <= 0
        elif f == "attrs":
            need = [a for a in (cm.get("required_attrs") or []) if a.get("required", True) is not False]
            have = dict(cm.get("attrs") or {})
            have.update((p.get("market_attrs") or {}).get(mk) or {})
            miss = [a.get("name") or str(a.get("id")) for a in need if str(a.get("id")) not in {str(k) for k, v in have.items() if v}]
            if miss:
                out.append({"field": f, "msg": "Zorunlu özellik eksik: " + ", ".join(miss[:6])})
            continue
        else:
            bad = not str(p.get(f) or "").strip()
        if bad:
            out.append({"field": f, "msg": lbl + " eksik"})
    if p.get("track_stock", True) is False:
        out.append({"field": "track_stock", "msg": "Stok takibi kapalı; pazaryerine stok bildirilemez"})
    if len(p.get("name") or "") > TITLE_MAX.get(mk, 255):
        out.append({"field": "name", "msg": "Ürün adı %d karakteri aşıyor" % TITLE_MAX[mk]})
    if mk == "trendyol" and float((p.get("old_price") or 0)) and float(p["old_price"]) < channel_price(p, mk):
        out.append({"field": "old_price", "msg": "Liste fiyatı satış fiyatından düşük olamaz"})
    return out


def state(p: dict, mk: str, catmap: dict = None, brandmap: dict = None) -> dict:
    """Ekranda gösterilen kanal durumu."""
    ch = (p.get("channels") or {}).get(mk) or {}
    sync = (p.get("market_sync") or {}).get(mk) or {}
    iss = issues(p, mk, catmap, brandmap) if ch.get("enabled") else []
    if not ch.get("enabled"):
        st = "kapali"
    elif iss:
        st = "eksik"
    elif sync.get("error"):
        st = "hata"
    elif sync.get("listed"):
        st = "yayinda"
    else:
        st = "hazir"
    price = channel_price(p, mk)
    return {"status": st, "issues": iss, "stock": channel_stock(p, mk), "price": price, "price_differs": abs(price - float(p.get("price") or 0)) > 0.005,
            "buffer": int(ch.get("buffer") or 0), "last_sync": sync.get("at", ""), "error": sync.get("error", ""), "listed": bool(sync.get("listed"))}


def new_job(market: str, product_id: str, kind: str) -> dict:
    return {"id": str(uuid.uuid4()), "market": market, "product_id": product_id, "kind": kind, "status": "bekliyor", "attempts": 0, "error": "", "created_at": _now()}
