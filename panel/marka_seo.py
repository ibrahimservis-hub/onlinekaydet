# -*- coding: utf-8 -*-
"""Marka sayfaları (/magaza/marka/<adres>) ve SEO şablonları.

SEO şablonu: "{urun} | {kategori} | {firma}" gibi bir kalıp. Ürüne elle yazılmış başlık/açıklama varsa o kullanılır,
yoksa şablon, şablon da boşsa eski davranış (ad · firma) sürer. Değişkenler: {urun} {kategori} {marka} {model} {fiyat} {firma}.
Marka sayfasının içeriği (açıklama, logo, SEO) panelden düzenlenir; sayfa adresi markanın adından üretilir."""
import re
import time

from fastapi import Depends, HTTPException

TPL_KEYS = ("product_title", "product_desc", "category_title", "category_desc", "brand_title", "brand_desc")
TPL_DEFAULT = {
    "product_title": "{urun} | {kategori} | {firma}",
    "product_desc": "{urun} {marka} ürününü {firma} güvencesiyle inceleyin, fiyat ve stok bilgisini görün.",
    "category_title": "{kategori} Modelleri ve Fiyatları | {firma}",
    "category_desc": "{kategori} kategorisindeki ürünleri {firma} mağazasında inceleyin.",
    "brand_title": "{marka} Ürünleri | {firma}",
    "brand_desc": "{marka} markasının tüm ürünleri {firma} mağazasında. Güncel fiyat ve stok bilgisi.",
}
_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def slugify(s, n=70):
    s = str(s or "").translate(_TR).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:n]


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def tl(v):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return ""
    if n <= 0:
        return ""
    s = ("%.2f" % n).rstrip("0").rstrip(".")
    a, _, b = s.partition(".")
    a = "{:,}".format(int(a)).replace(",", ".")
    return a + ("," + b if b else "") + " TL"


def render(tpl, vars_, limit):
    """Şablondaki {değişken}leri doldurur. Değişken boşsa o parça ve yanındaki ayraç ('|', ' - ', ' · ') atılır:
    "{urun} | {kategori} | {firma}" + kategori boş → "Ürün | Firma"."""
    parts = re.split(r"(\s*\|\s*|\s+[-–—·]\s+)", str(tpl or ""))
    out, first = "", True
    for i in range(0, len(parts), 2):
        seg = parts[i]
        for k, v in vars_.items():
            seg = seg.replace("{" + k + "}", str(v or ""))
        seg = re.sub(r"\{[a-z_]+\}", "", seg)
        seg = re.sub(r"\s{2,}", " ", seg).strip(" ,:")
        if not seg:
            continue
        sep = parts[i - 1] if i > 0 else ""
        out += ("" if first else (sep if sep.strip() else " ")) + seg
        first = False
    return out[:limit].strip()


async def templates(db):
    d = await db.app_settings.find_one({"_id": "shop_seo_tpl"}, {"_id": 0}) or {}
    return {k: str(d.get(k, "") or "").strip()[:200] for k in TPL_KEYS}


async def firma_adi(db):
    g = await db.app_settings.find_one({"_id": "global"}, {"company_name": 1}) or {}
    n = (g.get("company_name") or "").strip()
    if n:
        return n
    s = await db.app_settings.find_one({"_id": "shop_settings"}, {"title": 1}) or {}
    return (s.get("title") or "").strip()


def urun_degiskenleri(p, firma):
    return {"urun": p.get("name", ""), "kategori": p.get("category", ""), "marka": p.get("brand", ""), "model": p.get("model", ""),
            "fiyat": tl(p.get("price")), "firma": firma}


def urun_seo(p, tpl, firma):
    """Elle yazılmış değer önce; yoksa şablon; yoksa boş (çağıran eski davranışa döner)."""
    v = urun_degiskenleri(p, firma)
    title = (p.get("seo_title") or "").strip() or (render(tpl["product_title"], v, 70) if tpl["product_title"] else "")
    desc = (p.get("seo_desc") or "").strip() or (render(tpl["product_desc"], v, 170) if tpl["product_desc"] else "")
    return title, desc


async def marka_listesi(db):
    """Aktif ürünlerden marka adı → {slug, name, count}; adres benzersizdir."""
    out, seen = {}, {}
    async for r in db.shop_products.find({"active": True}, {"_id": 0, "brand": 1}):
        b = (r.get("brand") or "").strip()
        if not b:
            continue
        s = slugify(b)
        if not s:
            continue
        if s in seen and seen[s] != b:
            s = s + "-" + str(len(out))
        seen.setdefault(s, b)
        o = out.setdefault(s, {"slug": s, "name": b, "count": 0})
        o["count"] += 1
    return out


async def marka_sayfasi(db, slug):
    """Herkese açık marka bilgisi (içerik + SEO). Bulunamazsa None."""
    m = (await marka_listesi(db)).get(slug)
    if not m:
        return None
    pg = await db.shop_brand_pages.find_one({"slug": slug}, {"_id": 0}) or {}
    if pg.get("hidden"):
        return None
    tpl, firma = await templates(db), await firma_adi(db)
    v = {"marka": m["name"], "firma": firma, "kategori": "", "urun": "", "model": "", "fiyat": ""}
    title = (pg.get("seo_title") or "").strip() or (render(tpl["brand_title"], v, 70) if tpl["brand_title"] else "")
    desc = (pg.get("seo_desc") or "").strip() or (render(tpl["brand_desc"], v, 170) if tpl["brand_desc"] else "")
    return {"slug": slug, "name": m["name"], "count": m["count"], "desc": pg.get("desc", ""), "logo": pg.get("logo", ""),
            "seo_title": title or (m["name"] + " Ürünleri · " + firma).strip(" ·"), "seo_desc": desc or (pg.get("desc", "")[:160]),
            "noindex": bool(pg.get("noindex"))}


def register(api_router, db, deps):
    adm = deps["require_admin"]

    @api_router.get("/shop/seo-templates")
    async def seo_get(_: dict = Depends(adm)):
        return {"values": await templates(db), "defaults": TPL_DEFAULT,
                "vars": ["urun", "kategori", "marka", "model", "fiyat", "firma"], "firma": await firma_adi(db)}

    @api_router.put("/shop/seo-templates")
    async def seo_put(payload: dict, _: dict = Depends(adm)):
        v = {}
        for k in TPL_KEYS:
            t = str((payload.get("values") or payload).get(k, "") or "").strip()[:200]
            bad = [x for x in re.findall(r"\{([^{}]*)\}", t) if x not in ("urun", "kategori", "marka", "model", "fiyat", "firma")]
            if bad:
                raise HTTPException(422, "Bilinmeyen değişken: {" + bad[0] + "}. Kullanılabilir: {urun} {kategori} {marka} {model} {fiyat} {firma}")
            v[k] = t
        await db.app_settings.update_one({"_id": "shop_seo_tpl"}, {"$set": {**v, "updated_at": _now()}}, upsert=True)
        return {"values": v}

    @api_router.get("/shop/brand-pages")
    async def bp_list(_: dict = Depends(adm)):
        brands = await marka_listesi(db)
        pages = {p["slug"]: p async for p in db.shop_brand_pages.find({}, {"_id": 0})}
        rows = []
        for s, m in sorted(brands.items(), key=lambda x: x[1]["name"].lower()):
            p = pages.get(s, {})
            rows.append({"slug": s, "name": m["name"], "count": m["count"], "desc": p.get("desc", ""), "logo": p.get("logo", ""),
                         "seo_title": p.get("seo_title", ""), "seo_desc": p.get("seo_desc", ""), "noindex": bool(p.get("noindex")),
                         "hidden": bool(p.get("hidden"))})
        return rows

    @api_router.put("/shop/brand-pages/{slug}")
    async def bp_put(slug: str, payload: dict, _: dict = Depends(adm)):
        if slug not in await marka_listesi(db):
            raise HTTPException(404, "Marka bulunamadı")
        doc = {"desc": str(payload.get("desc", "") or "").strip()[:3000], "logo": str(payload.get("logo", "") or "").strip()[:500],
               "seo_title": str(payload.get("seo_title", "") or "").strip()[:70], "seo_desc": str(payload.get("seo_desc", "") or "").strip()[:170],
               "noindex": bool(payload.get("noindex")), "hidden": bool(payload.get("hidden")), "updated_at": _now()}
        if doc["logo"] and not re.match(r"^(https://|/)", doc["logo"]):
            raise HTTPException(422, "Logo adresi https:// ile başlamalı")
        await db.shop_brand_pages.update_one({"slug": slug}, {"$set": {"slug": slug, **doc}}, upsert=True)
        return {"ok": True, **doc, "slug": slug}

    @api_router.get("/public/shop/brands")
    async def pub_brands():
        brands = await marka_listesi(db)
        pages = {p["slug"]: p async for p in db.shop_brand_pages.find({}, {"_id": 0})}
        return [{"slug": s, "name": m["name"], "count": m["count"], "logo": (pages.get(s) or {}).get("logo", "")}
                for s, m in sorted(brands.items(), key=lambda x: x[1]["name"].lower()) if not (pages.get(s) or {}).get("hidden")]

    @api_router.get("/public/shop/brands/{slug}")
    async def pub_brand(slug: str):
        r = await marka_sayfasi(db, slug)
        if not r:
            raise HTTPException(404, "Marka bulunamadı")
        return r
