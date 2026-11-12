# -*- coding: utf-8 -*-
"""E-ticaret ürün modülü: ürün kaydı, varyant, stok, kârlılık ve hızlı ekleme.

Kârlılık: satış fiyatı KDV dâhil tutulur. Matrah = satış / (1 + KDV).
Kanal komisyonu brüt satış üzerinden alınır. Kâr = matrah − alış − komisyon.
Hızlı ekleme: verilen sayfanın JSON-LD ve OpenGraph etiketlerinden ad, açıklama,
görsel, marka, stok kodu ve fiyat çıkarılır; kullanıcı yalnız fiyat ve stoğu onaylar.
"""
import html as _html
import json
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

# Pazaryeri komisyonları (kategori bazlı ince ayar panelden yapılır)
CHANNELS = {"site": ("Kendi sitem", 0.0), "trendyol": ("Trendyol", 18.0), "hepsiburada": ("Hepsiburada", 14.0),
            "n11": ("N11", 13.0), "ciceksepeti": ("Çiçeksepeti", 15.0), "amazon_tr": ("Amazon TR", 15.0),
            "pttavm": ("PttAVM", 10.0), "pazarama": ("Pazarama", 12.0), "idefix": ("İdefix", 15.0),
            "modanisa": ("Modanisa", 20.0), "temu": ("Temu", 10.0)}
VATS = (0, 1, 10, 20)
SORTS = {"yeni": [("created_at", -1)], "ad": [("name", 1)], "fiyat": [("price", 1)], "fiyat_d": [("price", -1)],
         "stok": [("stock", 1)], "stok_d": [("stock", -1)], "kar": [("_margin", -1)]}


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


def _t(v, n):
    return " ".join(str(v or "").split())[:n]


def _num(v, d=0.0):
    try:
        return round(float(str(v).replace(" ", "").replace("₺", "").replace(".", "").replace(",", ".")
                          if isinstance(v, str) and "," in str(v) else str(v).replace(" ", "").replace("₺", "")), 2)
    except (TypeError, ValueError):
        return d


def _int(v, d=0):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return d


def slug(s, n=70):
    s = str(s or "").strip().lower()
    for a, b in (("ı", "i"), ("ğ", "g"), ("ü", "u"), ("ş", "s"), ("ö", "o"), ("ç", "c")):
        s = s.replace(a, b)
    return (re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "urun")[:n]


# ---------------------------------------------------------------- kârlılık
def profit(price, cost, vat=20.0, commission=0.0, ship=0.0):
    """KDV dâhil satış fiyatından net kâr. Döndürülen tutarlar ₺, oran %."""
    price, cost = _num(price), _num(cost)
    base = round(price / (1 + (_num(vat) / 100.0)), 2) if price else 0.0
    comm = round(price * (_num(commission) / 100.0), 2)
    net = round(base - cost - comm - _num(ship), 2)
    return {"price": price, "base": base, "vat": round(price - base, 2), "cost": cost,
            "commission": comm, "ship": _num(ship), "net": net,
            "margin": round(net / price * 100, 1) if price else 0.0}


def channel_profit(p, chans=None):
    out = []
    sale = _num(p.get("sale_price")) or _num(p.get("price"))
    for key in (chans or [k for k, v in (p.get("channels") or {}).items() if v]):
        name, comm = CHANNELS.get(key, (key, 0.0))
        r = profit(sale, p.get("cost"), p.get("vat", 20), comm)
        out.append(dict(r, channel=key, channel_name=name, commission_rate=comm))
    return out


# ---------------------------------------------------------------- hızlı ekleme
_IMG = re.compile(r'<meta[^>]+(?:property|name)=["\']og:image(?::url)?["\'][^>]+content=["\']([^"\']+)', re.I)
_IMG2 = re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image', re.I)
_META = re.compile(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]+content=["\']([^"\']*)', re.I)
_META2 = re.compile(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']%s["\']', re.I)
_LD = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


def _meta(h, key):
    for rx in (_META, _META2):
        m = rx.replace if False else re.compile(rx.pattern % re.escape(key), re.I)
        g = m.search(h)
        if g and g.group(1).strip():
            return _html.unescape(g.group(1).strip())
    return ""


def _abs(u, base):
    if not u:
        return ""
    if u.startswith("//"):
        return "https:" + u
    if u.startswith(("http://", "https://")):
        return u
    if base and u.startswith("/"):
        m = re.match(r"(https?://[^/]+)", base)
        return (m.group(1) + u) if m else u
    return u


def _ld_products(h):
    out = []
    for raw in _LD.findall(h):
        try:
            data = json.loads(raw.strip())
        except Exception:                                          # noqa: BLE001
            continue
        for d in (data if isinstance(data, list) else [data]):
            if not isinstance(d, dict):
                continue
            for d2 in ([d] + (d.get("@graph") if isinstance(d.get("@graph"), list) else [])):
                if isinstance(d2, dict) and "product" in str(d2.get("@type", "")).lower():
                    out.append(d2)
    return out


def parse_product(h, base=""):
    """Sayfa kaynağından ürün bilgisi çıkar. Fiyat ve stok kullanıcıya bırakılır."""
    h = h or ""
    out = {"name": "", "desc": "", "brand": "", "sku": "", "gtin": "", "price": 0.0, "images": [], "specs": [],
           "source": base, "found": []}
    for d in _ld_products(h):
        out["name"] = out["name"] or _t(d.get("name"), 200)
        out["desc"] = out["desc"] or _t(d.get("description"), 4000)
        br = d.get("brand")
        out["brand"] = out["brand"] or _t(br.get("name") if isinstance(br, dict) else br, 60)
        out["sku"] = out["sku"] or _t(d.get("sku") or d.get("mpn"), 60)
        out["gtin"] = out["gtin"] or _t(d.get("gtin13") or d.get("gtin") or d.get("gtin12"), 20)
        img = d.get("image")
        for u in (img if isinstance(img, list) else [img]):
            if isinstance(u, dict):
                u = u.get("url")
            if u and _abs(u, base) not in out["images"]:
                out["images"].append(_abs(u, base))
        off = d.get("offers")
        off = off[0] if isinstance(off, list) and off else off
        if isinstance(off, dict) and not out["price"]:
            out["price"] = _num(off.get("price"))
        for pr in (d.get("additionalProperty") or [])[:30]:
            if isinstance(pr, dict) and pr.get("name"):
                out["specs"].append({"k": _t(pr["name"], 60), "v": _t(pr.get("value"), 120)})
    out["name"] = out["name"] or _meta(h, "og:title") or _t((_TITLE.search(h) or [None, ""])[1] if _TITLE.search(h) else "", 200)
    out["desc"] = out["desc"] or _meta(h, "og:description") or _meta(h, "description")
    out["brand"] = out["brand"] or _meta(h, "product:brand") or _meta(h, "og:site_name")
    if not out["price"]:
        out["price"] = _num(_meta(h, "product:price:amount") or _meta(h, "og:price:amount"))
    for rx in (_IMG, _IMG2):
        for u in rx.findall(h):
            u = _abs(_html.unescape(u), base)
            if u and u not in out["images"]:
                out["images"].append(u)
    if not out["images"]:
        for u in re.findall(r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)', h, re.I)[:12]:
            u = _abs(_html.unescape(u), base)
            if u not in out["images"]:
                out["images"].append(u)
    out["name"] = re.sub(r"\s*[|·–-]\s*[^|·–-]{0,40}$", "", out["name"]) if len(out["name"]) > 40 else out["name"]
    out["images"] = out["images"][:12]
    out["found"] = [k for k in ("name", "desc", "brand", "sku", "images", "specs") if out.get(k)]
    return out


# ---------------------------------------------------------------- kayıt
def clean(p, old=None):
    old = old or {}
    name = _t(p.get("name"), 200)
    if not name:
        raise HTTPException(422, "Ürün adı yazın")
    price = _num(p.get("price"))
    if price <= 0:
        raise HTTPException(422, "Satış fiyatı yazın")
    sale = _num(p.get("sale_price"))
    if sale and sale > price:
        raise HTTPException(422, "İndirimli fiyat, satış fiyatından yüksek olamaz")
    vat = _int(p.get("vat"), 20)
    if vat not in VATS:
        vat = 20
    ch = {}
    for k, v in (p.get("channels") or {}).items():
        if k in CHANNELS:
            ch[k] = bool(v)
    ch.setdefault("site", True)
    vr = []
    for v in (p.get("variants") or [])[:200]:
        if not isinstance(v, dict):
            continue
        opts = {_t(a, 30): _t(b, 40) for a, b in list((v.get("opts") or {}).items())[:4] if _t(a, 30)}
        if not opts:
            continue
        vr.append({"id": _t(v.get("id"), 20) or uuid.uuid4().hex[:8], "opts": opts,
                   "sku": _t(v.get("sku"), 60), "barcode": _t(v.get("barcode"), 40),
                   "stock": _int(v.get("stock")), "price": _num(v.get("price")) or 0.0})
    imgs = [_t(u, 400) for u in (p.get("images") or [])[:20] if _t(u, 400)]
    specs = [{"k": _t(s.get("k"), 60), "v": _t(s.get("v"), 200)} for s in (p.get("specs") or [])[:40]
             if isinstance(s, dict) and _t(s.get("k"), 60)]
    out = {"name": name, "slug": slug(p.get("slug") or name), "sku": _t(p.get("sku"), 60),
           "barcode": _t(p.get("barcode"), 40), "gtin": _t(p.get("gtin"), 20),
           "cat": _t(p.get("cat"), 80), "brand": _t(p.get("brand"), 60),
           "desc": str(p.get("desc") or "")[:12000], "specs": specs,
           "cost": _num(p.get("cost")), "price": price, "sale_price": sale, "vat": vat,
           "stock": _int(p.get("stock")), "track_stock": False if p.get("track_stock") is False else True,
           "low_at": _int(p.get("low_at"), _int(old.get("low_at"), 5)),
           "variants": vr, "images": imgs,
           "weight": _num(p.get("weight")), "desi": _num(p.get("desi")),
           "warranty": _t(p.get("warranty"), 60), "min_qty": max(_int(p.get("min_qty"), 1), 1),
           "max_qty": _int(p.get("max_qty")), "channels": ch,
           "seo": {"title": _t((p.get("seo") or {}).get("title"), 70), "desc": _t((p.get("seo") or {}).get("desc"), 300)},
           "status": "draft" if p.get("status") == "draft" else "live",
           "source": _t(p.get("source"), 400)}
    if vr:
        out["stock"] = sum(v["stock"] for v in vr)
    return out


def view(p):
    sale = _num(p.get("sale_price")) or _num(p.get("price"))
    pr = profit(sale, p.get("cost"), p.get("vat", 20))
    d = _num(p.get("price")) - sale
    return dict(p, sale=sale, profit=pr, margin=pr["margin"],
                discount=round(d / _num(p["price"]) * 100) if d > 0 and _num(p.get("price")) else 0,
                low=bool(p.get("track_stock", True) and 0 < _int(p.get("stock")) <= _int(p.get("low_at"), 5)),
                out=bool(p.get("track_stock", True) and _int(p.get("stock")) <= 0),
                channels_on=[k for k, v in (p.get("channels") or {}).items() if v])


def register(api_router, db, deps):
    adm = deps["require_admin"]
    fetch = deps.get("fetch_url")                                  # canlıda dış sayfayı çeken yardımcı

    async def one(pid):
        p = await db.yp_products.find_one({"id": pid}, {"_id": 0})
        if not p:
            raise HTTPException(404, "Ürün bulunamadı")
        return p

    @api_router.get("/yp/products")
    async def products(q: str = "", cat: str = "", brand: str = "", channel: str = "", seg: str = "",
                       sort: str = "yeni", offset: int = 0, limit: int = 50, _: dict = Depends(adm)):
        rows = [view(p) for p in await db.yp_products.find({}, {"_id": 0}).to_list(20000)]
        q = q.strip().lower()
        if q:
            rows = [r for r in rows if q in r["name"].lower() or q in (r.get("sku") or "").lower()
                    or q in (r.get("barcode") or "").lower() or q in (r.get("brand") or "").lower()]
        if cat:
            rows = [r for r in rows if r.get("cat") == cat]
        if brand:
            rows = [r for r in rows if r.get("brand") == brand]
        if channel:
            rows = [r for r in rows if (r.get("channels") or {}).get(channel)]
        segs = {"yayinda": lambda r: r["status"] == "live", "taslak": lambda r: r["status"] == "draft",
                "az_stok": lambda r: r["low"], "tukendi": lambda r: r["out"],
                "indirimli": lambda r: r["discount"] > 0,
                "kanalsiz": lambda r: len(r["channels_on"]) <= 1,
                "kar_dusuk": lambda r: r["margin"] < 10}
        counts = {k: sum(1 for r in rows if f(r)) for k, f in segs.items()}
        counts["hepsi"] = len(rows)
        if seg in segs:
            rows = [r for r in rows if segs[seg](r)]
        key = {"yeni": lambda r: r.get("created_at", ""), "ad": lambda r: r["name"].lower(),
               "fiyat": lambda r: r["sale"], "stok": lambda r: _int(r.get("stock")),
               "kar": lambda r: r["margin"]}.get(sort.rstrip("_d"), lambda r: r.get("created_at", ""))
        rows.sort(key=key, reverse=sort in ("yeni", "fiyat_d", "stok_d", "kar"))
        offset, limit = max(offset, 0), min(max(limit, 1), 200)
        tot = {"n": len(rows), "stock_value": round(sum(_num(r.get("cost")) * _int(r.get("stock")) for r in rows), 2),
               "margin": round(sum(r["margin"] for r in rows) / len(rows), 1) if rows else 0.0}
        return {"rows": rows[offset:offset + limit], "total": len(rows), "counts": counts, "sum": tot,
                "channels": [{"id": k, "name": v[0], "commission": v[1]} for k, v in CHANNELS.items()]}

    @api_router.get("/yp/products/filters")
    async def filters(_: dict = Depends(adm)):
        rows = await db.yp_products.find({}, {"_id": 0, "cat": 1, "brand": 1}).to_list(20000)
        cats, brands = {}, {}
        for r in rows:
            if r.get("cat"):
                cats[r["cat"]] = cats.get(r["cat"], 0) + 1
            if r.get("brand"):
                brands[r["brand"]] = brands.get(r["brand"], 0) + 1
        return {"cats": sorted(({"name": k, "n": v} for k, v in cats.items()), key=lambda x: -x["n"]),
                "brands": sorted(({"name": k, "n": v} for k, v in brands.items()), key=lambda x: -x["n"]),
                "vats": list(VATS), "sorts": list(SORTS)}

    @api_router.post("/yp/products/parse")
    async def parse(payload: dict, _: dict = Depends(adm)):
        """Hızlı ekleme: bağlantıdan ad, açıklama, görsel ve özellikleri çek."""
        url = _t(payload.get("url"), 500)
        raw = payload.get("html")
        if not raw:
            if not re.match(r"https?://", url):
                raise HTTPException(422, "Geçerli bir bağlantı yapıştırın")
            if not fetch:
                raise HTTPException(503, "Bağlantıdan çekme şu an kapalı")
            try:
                raw = await fetch(url)
            except Exception:                                      # noqa: BLE001
                raise HTTPException(502, "Sayfaya ulaşılamadı; bilgileri elle girebilirsiniz")
        d = parse_product(raw, url)
        if not d["name"]:
            raise HTTPException(422, "Sayfada ürün bilgisi bulunamadı; elle girebilirsiniz")
        return d

    @api_router.post("/yp/products")
    async def add(payload: dict, user: dict = Depends(adm)):
        o = clean(payload)
        if o["sku"] and await db.yp_products.find_one({"sku": o["sku"]}, {"_id": 1}):
            raise HTTPException(422, "Bu stok kodu başka üründe kullanılıyor")
        o.update({"id": uuid.uuid4().hex[:12], "low_at": _int(payload.get("low_at"), 5),
                  "created_at": _now(), "updated_at": _now(), "by": user.get("name", "")})
        await db.yp_products.insert_one(dict(o))
        return view(o)

    @api_router.get("/yp/products/{pid}")
    async def get_one(pid: str, _: dict = Depends(adm)):
        p = await one(pid)
        return dict(view(p), channel_profit=channel_profit(p))

    @api_router.put("/yp/products/{pid}")
    async def put(pid: str, payload: dict, _: dict = Depends(adm)):
        p = await one(pid)
        o = clean(dict(p, **payload), p)
        if o["sku"] and await db.yp_products.find_one({"sku": o["sku"], "id": {"$ne": pid}}, {"_id": 1}):
            raise HTTPException(422, "Bu stok kodu başka üründe kullanılıyor")
        o["updated_at"] = _now()
        if "low_at" in payload:
            o["low_at"] = _int(payload["low_at"], 5)
        await db.yp_products.update_one({"id": pid}, {"$set": o})
        return view(dict(p, **o))

    @api_router.delete("/yp/products/{pid}")
    async def delete(pid: str, _: dict = Depends(adm)):
        await one(pid)
        await db.yp_products.delete_one({"id": pid})
        return {"ok": True}

    @api_router.post("/yp/products/bulk")
    async def bulk(payload: dict, _: dict = Depends(adm)):
        """Toplu işlem: fiyat/stok/kanal/durum. `op` ve `ids` zorunlu."""
        ids = [str(i) for i in (payload.get("ids") or [])][:5000]
        op = payload.get("op")
        if not ids or op not in ("price", "stock", "channel", "status", "delete", "cat"):
            raise HTTPException(422, "Yapılacak işlemi ve ürünleri seçin")
        n = 0
        for pid in ids:
            p = await db.yp_products.find_one({"id": pid}, {"_id": 0})
            if not p:
                continue
            up = {}
            if op == "price":
                pct = _num(payload.get("percent"))
                if not pct:
                    raise HTTPException(422, "Yüzde yazın")
                up["price"] = round(_num(p["price"]) * (1 + pct / 100.0), 2)
                if _num(p.get("sale_price")):
                    up["sale_price"] = round(_num(p["sale_price"]) * (1 + pct / 100.0), 2)
            elif op == "stock":
                up["stock"] = max(_int(p.get("stock")) + _int(payload.get("add")), 0) if payload.get("add") is not None else _int(payload.get("set"))
            elif op == "channel":
                k = payload.get("channel")
                if k not in CHANNELS:
                    raise HTTPException(422, "Kanal seçin")
                up["channels"] = dict(p.get("channels") or {}, **{k: bool(payload.get("on", True))})
            elif op == "status":
                up["status"] = "draft" if payload.get("status") == "draft" else "live"
            elif op == "cat":
                up["cat"] = _t(payload.get("cat"), 80)
            if op == "delete":
                await db.yp_products.delete_one({"id": pid})
            else:
                up["updated_at"] = _now()
                await db.yp_products.update_one({"id": pid}, {"$set": up})
            n += 1
        return {"ok": True, "n": n}

    @api_router.post("/yp/products/{pid}/profit")
    async def profit_calc(pid: str, payload: dict, _: dict = Depends(adm)):
        """Kanal seçilince kâr yeniden hesaplanır."""
        p = await one(pid)
        chans = [c for c in (payload.get("channels") or []) if c in CHANNELS] or None
        return {"rows": channel_profit(dict(p, **{k: payload[k] for k in ("price", "sale_price", "cost", "vat") if k in payload}), chans)}
