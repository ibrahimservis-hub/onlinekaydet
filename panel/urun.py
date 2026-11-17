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
            "modanisa": ("Modanisa", 20.0), "temu": ("Temu", 10.0),
            # yemek platformları: komisyon firmaya göre değişir; entegrasyon ayarından girilir (boşsa 0)
            "yemeksepeti": ("Yemeksepeti", 0.0), "trendyol_yemek": ("Trendyol Yemek", 0.0),
            "getir_yemek": ("Getir Yemek", 0.0), "migros_yemek": ("Migros Yemek", 0.0)}
FOOD_CH = ("yemeksepeti", "trendyol_yemek", "getir_yemek", "migros_yemek")
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


FIYAT_MOD = {"ayni": "Sitedeki fiyatla", "oran": "Yüzde ekleyerek", "sabit": "Bu kanala özel fiyat"}


def kanal_fiyat(p, key):
    """(liste fiyatı, satış fiyatı) — kanal ayarına göre. Site her zaman ürünün kendi fiyatıdır."""
    price = _num(p.get("price"))
    sale = _num(p.get("sale_price")) or price
    c = (p.get("ch_price") or {}).get(key) or {}
    m = c.get("mod")
    if key == "site" or m not in ("oran", "sabit"):
        return price, sale
    if m == "oran":
        k = 1 + _num(c.get("oran")) / 100.0
        return round(price * k, 2), round(sale * k, 2)
    f = _num(c.get("fiyat")) or price
    return f, (_num(c.get("indirimli")) or f)


def channel_profit(p, chans=None):
    out = []
    for key in (chans or [k for k, v in (p.get("channels") or {}).items() if v]):
        name, comm = CHANNELS.get(key, (key, 0.0))
        cc = _num(((p.get("ch_price") or {}).get(key) or {}).get("komisyon")) or comm
        liste, sale = kanal_fiyat(p, key)
        r = profit(sale, p.get("cost"), p.get("vat", 20), cc, _num((p.get("ship") or {}).get("maliyet")))
        out.append(dict(r, channel=key, channel_name=name, commission_rate=cc, list_price=liste,
                        mod=((p.get("ch_price") or {}).get(key) or {}).get("mod") or "ayni"))
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
    vr, axes = [], []
    for a in (p.get("var_axes") or [])[:3]:
        if isinstance(a, dict) and _t(a.get("ad"), 30):
            vals = []
            for x in (a.get("degerler") or [])[:40]:
                x = _t(x, 40)
                if x and x not in vals:
                    vals.append(x)
            if vals and not any(z["ad"] == _t(a.get("ad"), 30) for z in axes):
                axes.append({"ad": _t(a.get("ad"), 30), "degerler": vals})
    seen_sku, seen_bc, seen_opt = set(), set(), set()
    for v in (p.get("variants") or [])[:200]:
        if not isinstance(v, dict):
            continue
        opts = {_t(a, 30): _t(b, 40) for a, b in list((v.get("opts") or {}).items())[:3] if _t(a, 30) and _t(b, 40)}
        if not opts:
            continue
        key = "|".join("%s=%s" % kv for kv in sorted(opts.items()))
        if key in seen_opt:
            raise HTTPException(422, "Aynı seçenek iki kez var: " + " / ".join(opts.values()))
        seen_opt.add(key)
        sku, bc = _t(v.get("sku"), 60), _t(v.get("barcode"), 40)
        for val, seen, ad in ((sku, seen_sku, "stok kodu"), (bc, seen_bc, "barkod")):
            if val:
                if val in seen:
                    raise HTTPException(422, "Seçeneklerde aynı %s birden fazla: %s" % (ad, val))
                seen.add(val)
        vp, vs = _num(v.get("price")), _num(v.get("sale_price"))
        if vs and vp and vs > vp:
            raise HTTPException(422, "Seçenek indirimli fiyatı, fiyatından yüksek olamaz")
        vr.append({"id": _t(v.get("id"), 20) or uuid.uuid4().hex[:8], "opts": opts, "sku": sku, "barcode": bc,
                   "stock": max(_int(v.get("stock")), 0), "price": vp or 0.0, "sale_price": vs or 0.0,
                   "image": _t(v.get("image"), 400), "active": v.get("active") is not False})
    if vr and not axes:                       # eksen verilmediyse seçeneklerden türet
        order = []
        for v in vr:
            for a, b in v["opts"].items():
                z = next((x for x in order if x["ad"] == a), None)
                if not z:
                    z = {"ad": a, "degerler": []}
                    order.append(z)
                if b not in z["degerler"]:
                    z["degerler"].append(b)
        axes = order[:3]
    imgs = [_t(u, 400) for u in (p.get("images") or [])[:20] if _t(u, 400)]
    specs = [{"k": _t(s.get("k"), 60), "v": _t(s.get("v"), 200)} for s in (p.get("specs") or [])[:40]
             if isinstance(s, dict) and _t(s.get("k"), 60)]
    chp = {}
    for k, c in (p.get("ch_price") or {}).items():
        if k in CHANNELS and k != "site" and isinstance(c, dict):
            m = c.get("mod") if c.get("mod") in FIYAT_MOD else "ayni"
            r = {"mod": m, "komisyon": min(max(_num(c.get("komisyon")), 0.0), 60.0)}
            if m == "oran":
                r["oran"] = min(max(_num(c.get("oran")), -50.0), 300.0)
            elif m == "sabit":
                r["fiyat"] = _num(c.get("fiyat"))
                r["indirimli"] = _num(c.get("indirimli"))
                if r["fiyat"] <= 0:
                    raise HTTPException(422, "%s için özel fiyat yazın" % CHANNELS[k][0])
                if r["indirimli"] and r["indirimli"] > r["fiyat"]:
                    raise HTTPException(422, "%s indirimli fiyatı, kanal fiyatından yüksek olamaz" % CHANNELS[k][0])
            chp[k] = r
    sh = p.get("ship") or {}
    en, boy, yuk = _num(sh.get("en")), _num(sh.get("boy")), _num(sh.get("yuk"))
    desi = _num(p.get("desi"))
    if not desi and en and boy and yuk:
        desi = round(max(en * boy * yuk / 3000.0, 1.0), 2)
    ship = {"en": en, "boy": boy, "yuk": yuk, "hs": _t(sh.get("hs"), 12), "gun": min(max(_int(sh.get("gun"), 2), 0), 60),
            "ucretsiz": bool(sh.get("ucretsiz")), "maliyet": _num(sh.get("maliyet"))}
    cats = []
    for c in (p.get("cats") or [])[:10]:
        c = _t(c, 80)
        if c and c not in cats:
            cats.append(c)
    main_cat = _t(p.get("cat"), 80) or (cats[0] if cats else "")
    if main_cat and main_cat not in cats:
        cats.insert(0, main_cat)
    so = p.get("seo") or {}
    canon = _t(so.get("canonical"), 300)
    if canon and not re.match(r"^(https?://|/)", canon):
        raise HTTPException(422, "Canonical adres http(s):// ya da / ile başlamalı")
    seo = {"title": _t(so.get("title"), 70), "desc": _t(so.get("desc"), 320), "keywords": _t(so.get("keywords"), 250),
           "canonical": canon, "noindex": bool(so.get("noindex")), "alt": _t(so.get("alt"), 125)}
    tags = []
    for x in (p.get("tags") or [])[:20]:
        x = _t(x, 30)
        if x and x not in tags:
            tags.append(x)
    vid = _t(p.get("video"), 300)
    if vid and not re.match(r"^https://(www\.)?(youtube\.com|youtu\.be|vimeo\.com)/", vid):
        raise HTTPException(422, "Video için YouTube veya Vimeo bağlantısı yapıştırın")
    out = {"name": name, "slug": slug(p.get("slug") or name), "sku": _t(p.get("sku"), 60),
           "barcode": _t(p.get("barcode"), 40), "gtin": _t(p.get("gtin"), 20),
           "cat": main_cat, "cats": cats, "brand": _t(p.get("brand"), 60), "model": _t(p.get("model"), 60),
           "tags": tags, "supplier": _t(p.get("supplier"), 80), "unit": _t(p.get("unit"), 15) or "Adet",
           "google_cat": _t(p.get("google_cat"), 160), "ch_price": chp, "ship": ship, "video": vid,
           "backorder": bool(p.get("backorder")), "featured": bool(p.get("featured")), "badge": _t(p.get("badge"), 24),
           "short": _t(p.get("short"), 240),
           "related": [_t(i, 24) for i in (p.get("related") or [])[:12] if _t(i, 24)],
           "desc": str(p.get("desc") or "")[:12000], "specs": specs,
           "cost": _num(p.get("cost")), "price": price, "sale_price": sale, "vat": vat,
           "stock": _int(p.get("stock")), "track_stock": False if p.get("track_stock") is False else True,
           "low_at": _int(p.get("low_at"), _int(old.get("low_at"), 5)),
           "variants": vr, "var_axes": axes if vr else [], "images": imgs,
           "weight": _num(p.get("weight")), "desi": desi,
           "warranty": _t(p.get("warranty"), 60), "min_qty": max(_int(p.get("min_qty"), 1), 1),
           "max_qty": _int(p.get("max_qty")), "channels": ch,
           "seo": seo,
           "status": "draft" if p.get("status") == "draft" else "live",
           "source": _t(p.get("source"), 400)}
    if vr:
        out["stock"] = sum(v["stock"] for v in vr if v["active"])
    return out


def view(p):
    sale = _num(p.get("sale_price")) or _num(p.get("price"))
    pr = profit(sale, p.get("cost"), p.get("vat", 20))
    d = _num(p.get("price")) - sale
    return dict(p, sale=sale, profit=pr, margin=pr["margin"],
                discount=round(d / _num(p["price"]) * 100) if d > 0 and _num(p.get("price")) else 0,
                low=bool(p.get("track_stock", True) and 0 < _int(p.get("stock")) <= _int(p.get("low_at"), 5)),
                out=bool(p.get("track_stock", True) and _int(p.get("stock")) <= 0),
                channels_on=[k for k, v in (p.get("channels") or {}).items() if v],
                variant_count=len(p.get("variants") or []))


async def _rozet(db, rows):
    """Listedeki ürünlere pazaryeri durumu ekler: markets=[{id,name,status,price,price_differs}] (yalnız açık pazaryerleri)."""
    try:
        import shop_channels as shch
        ids = [r["id"] for r in rows if any(k in shch.MARKETS for k in (r.get("channels_on") or []))]
        if not ids:
            return
        docs = {d["id"]: d async for d in db.shop_products.find({"id": {"$in": ids}}, {"_id": 0})}
        cms, bms = {}, {}
        for r in rows:
            d = docs.get(r["id"])
            if not d:
                continue
            out = []
            for mk in r.get("channels_on") or []:
                if mk not in shch.MARKETS:
                    continue
                if mk not in cms:
                    cms[mk] = {x["category_id"]: x async for x in db.market_catmap.find({"market": mk}, {"_id": 0})}
                    bm = await db.app_settings.find_one({"_id": "brandmap_" + mk}, {"_id": 0}) or {}
                    bms[mk] = {k.lower(): v for k, v in (bm.get("map") or {}).items()}
                st = shch.state(d, mk, cms[mk].get(d.get("category_id", "")), bms[mk])
                out.append({"id": mk, "name": CHANNELS.get(mk, (mk,))[0], "status": st["status"], "price": st["price"],
                            "price_differs": st["price_differs"], "error": st["error"], "issues": len(st["issues"])})
            r["markets"] = out
    except Exception:                                              # noqa: BLE001
        pass


async def _ayna(db, pid):
    try:
        import urun_ayna
        await urun_ayna.ayna(db, pid)
    except Exception:                                              # noqa: BLE001
        pass


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
        page = rows[offset:offset + limit]
        await _rozet(db, page)
        return {"rows": page, "total": len(rows), "counts": counts, "sum": tot,
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
            except Exception as e:                                 # noqa: BLE001
                code = getattr(e, "code", None) or getattr(getattr(e, "response", None), "status_code", None)
                raise HTTPException(502, "Sayfaya ulaşılamadı" + (" (%s)" % code if code else "")
                                    + ". Site otomatik okumayı engelliyor olabilir; “Sayfa kaynağını yapıştır” ile deneyin")
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
        await _ayna(db, o["id"])
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
        await _ayna(db, pid)
        return view(dict(p, **o))

    @api_router.delete("/yp/products/{pid}")
    async def delete(pid: str, _: dict = Depends(adm)):
        await one(pid)
        await db.yp_products.delete_one({"id": pid})
        await _ayna(db, pid)
        return {"ok": True}

    @api_router.post("/yp/products/bulk")
    async def bulk(payload: dict, _: dict = Depends(adm)):
        """Toplu işlem: fiyat/stok/kanal/durum. `op` ve `ids` zorunlu."""
        ids = [str(i) for i in (payload.get("ids") or [])][:5000]
        op = payload.get("op")
        if not ids or op not in ("price", "stock", "channel", "status", "delete", "cat",
                                 "brand", "sale", "vat", "low_at", "cost"):
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
                if p.get("variants"):
                    up["variants"] = [dict(v, price=round(_num(v.get("price")) * (1 + pct / 100.0), 2),
                                           sale_price=round(_num(v.get("sale_price")) * (1 + pct / 100.0), 2)) for v in p["variants"]]
            elif op == "stock":
                if p.get("variants"):                  # varyantlı ürün: her seçeneğe uygulanır, toplam varyantlardan türer
                    vs = [dict(v, stock=(max(_int(v.get("stock")) + _int(payload.get("add")), 0) if payload.get("add") is not None
                                         else max(_int(payload.get("set")), 0))) for v in p["variants"]]
                    up["variants"] = vs
                    up["stock"] = sum(v["stock"] for v in vs if v.get("active", True))
                else:
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
            elif op == "brand":
                up["brand"] = _t(payload.get("brand"), 60)
            elif op == "sale":
                pct = min(max(_num(payload.get("percent")), 0.0), 95.0)
                if pct:
                    up["sale_price"] = round(_num(p["price"]) * (1 - pct / 100.0), 2)
                else:
                    up["sale_price"] = 0.0
            elif op == "cost":
                pct = _num(payload.get("percent"))
                up["cost"] = round(_num(p.get("cost")) * (1 + pct / 100.0), 2)
            elif op == "vat":
                v = _int(payload.get("vat"), 20)
                up["vat"] = v if v in VATS else 20
            elif op == "low_at":
                up["low_at"] = max(_int(payload.get("low_at")), 0)
            if op == "delete":
                await db.yp_products.delete_one({"id": pid})
            else:
                up["updated_at"] = _now()
                await db.yp_products.update_one({"id": pid}, {"$set": up})
            await _ayna(db, pid)
            n += 1
        return {"ok": True, "n": n}

    @api_router.post("/yp/products/export")
    async def prod_export(payload: dict, _: dict = Depends(adm)):
        """Seçili ürünleri (seçim yoksa hepsini) Excel'in açabildiği CSV olarak ver."""
        ids = [_t(i, 24) for i in (payload.get("ids") or [])][:20000]
        q = {"id": {"$in": ids}} if ids else {}
        rows = [view(p) for p in await db.yp_products.find(q, {"_id": 0}).to_list(20000)]
        rows.sort(key=lambda r: r.get("name", "").lower())
        head = ["Ürün adı", "Stok kodu", "Barkod", "Kategori", "Marka", "Alış", "Satış", "İndirimli",
                "KDV", "Stok", "Az stok eşiği", "Kâr", "Kâr oranı %", "Durum", "Açık kanallar"]
        def cell(v):
            return '"%s"' % str(v if v is not None else "").replace('"', '""')
        lines = [";".join(head)]
        for r in rows:
            lines.append(";".join(cell(x) for x in [
                r.get("name"), r.get("sku"), r.get("barcode"), r.get("cat"), r.get("brand"),
                r.get("cost"), r.get("price"), r.get("sale_price") or "", r.get("vat"),
                r.get("stock"), r.get("low_at", 5), (r.get("profit") or {}).get("net"), r.get("margin"),
                "Yayında" if r.get("status") != "draft" else "Taslak",
                ", ".join(CHANNELS[k][0] for k in r.get("channels_on") or [] if k in CHANNELS)]))
        return {"ok": True, "n": len(rows), "name": "urunler-%s.csv" % _now()[:10],
                "csv": "\ufeff" + "\n".join(lines)}

    @api_router.post("/yp/products/{pid}/profit")
    async def profit_calc(pid: str, payload: dict, _: dict = Depends(adm)):
        """Kanal seçilince kâr yeniden hesaplanır."""
        p = await one(pid)
        chans = [c for c in (payload.get("channels") or []) if c in CHANNELS] or None
        return {"rows": channel_profit(dict(p, **{k: payload[k] for k in ("price", "sale_price", "cost", "vat") if k in payload}), chans)}
