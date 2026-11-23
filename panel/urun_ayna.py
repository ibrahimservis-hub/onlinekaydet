# -*- coding: utf-8 -*-
"""Panel ürünü (yp_products) ↔ mağaza/pazaryeri ürünü (shop_products) köprüsü.

Tek kaynak paneldeki üründür. Panelde kaydedilen ürün aynı kimlikle mağazaya yazılır; böylece
/magaza, ürün sayfası, arama ve pazaryeri gönderimi (shop_sync) aynı ürünü görür.
Mağazada ya da pazaryerinde satış olunca düşen stok panele geri yazılır (geri()).
"""
import re

import urun

_TAG = re.compile(r"<[^>]+>")


def _kisa(p):
    s = (p.get("short") or (p.get("seo") or {}).get("desc") or "").strip()
    if not s:
        s = " ".join(_TAG.sub(" ", p.get("desc") or "").split())[:200]
    return s[:240]


def belge(p):
    """yp ürününden mağaza belgesi (yalnız $set edilecek alanlar)."""
    price = urun._num(p.get("price"))
    sale = urun._num(p.get("sale_price"))
    on_sale = 0 < sale < price
    seo = p.get("seo") or {}
    ship = p.get("ship") or {}
    kanallar = {"site": {"enabled": bool((p.get("channels") or {}).get("site", True))}}
    for k, on in (p.get("channels") or {}).items():
        if k == "site" or k not in urun.CHANNELS:
            continue
        _liste, satis = urun.kanal_fiyat(p, k)
        kanallar[k] = {"enabled": bool(on), "price": satis if satis != (sale if on_sale else price) else 0.0, "buffer": 0}
    canli = p.get("status") != "draft" and kanallar["site"]["enabled"]
    taban = sale if on_sale else price
    varyant = []
    for v in (p.get("variants") or []):
        vp, vs = urun._num(v.get("price")), urun._num(v.get("sale_price"))
        if vp or vs:
            liste = vp or price
            etkin = vs if (vs and vs < liste) else liste
        else:
            liste, etkin = price, taban
        varyant.append({"id": v["id"], "opts": dict(v.get("opts") or {}), "label": " / ".join((v.get("opts") or {}).values()),
                        "sku": v.get("sku") or "", "barcode": v.get("barcode") or "", "stock": urun._int(v.get("stock")),
                        "price": etkin, "old_price": liste if etkin < liste else 0.0,
                        "image": v.get("image") or "", "active": v.get("active", True)})
    return {
        "variants": varyant, "var_axes": list(p.get("var_axes") or []),
        "name": p["name"], "slug": p.get("slug") or p["id"], "brand": p.get("brand") or "", "model": p.get("model") or "",
        "category": p.get("cat") or "", "categories": p.get("cats") or ([p["cat"]] if p.get("cat") else []),
        "price": sale if on_sale else price, "old_price": price if on_sale else 0.0,
        "stock": urun._int(p.get("stock")), "track_stock": p.get("track_stock", True) and not p.get("backorder"),
        "short": _kisa(p), "description": p.get("desc") or "",
        "specs": [{"k": x.get("k"), "v": x.get("v")} for x in (p.get("specs") or [])],
        "images": list(p.get("images") or []), "sku": p.get("sku") or "", "barcode": p.get("barcode") or "",
        "gtin": p.get("gtin") or "", "badge": p.get("badge") or "", "featured": bool(p.get("featured")),
        "active": canli, "kdv": urun._int(p.get("vat"), 20), "cost": urun._num(p.get("cost")),
        "desi": urun._num(p.get("desi")), "weight": urun._num(p.get("weight")),
        "delivery_days": urun._int(ship.get("gun"), 2), "free_ship": bool(ship.get("ucretsiz")),
        "warranty_months": 0, "unit": p.get("unit") or "Adet", "supplier": p.get("supplier") or "",
        "tags": list(p.get("tags") or []), "seo_title": seo.get("title") or "", "seo_desc": (seo.get("desc") or "")[:170],
        "seo_keywords": seo.get("keywords") or "", "canonical": seo.get("canonical") or "", "noindex": bool(seo.get("noindex")),
        "img_alt": seo.get("alt") or "", "video": p.get("video") or "", "related": list(p.get("related") or []),
        "min_qty": urun._int(p.get("min_qty"), 1), "max_qty": urun._int(p.get("max_qty")),
        "channels": kanallar, "src": {"panel": True}, "updated_at": p.get("updated_at") or urun._now(),
    }


async def ayna(db, pid):
    """Panel ürününü mağazaya yaz (yoksa oluşturur, silinmişse mağazadan da kaldırır)."""
    p = await db.yp_products.find_one({"id": pid}, {"_id": 0})
    if not p:
        await db.shop_products.delete_one({"id": pid, "src.panel": True})
        return
    doc = belge(p)
    ids = [i for i in (p.get("cat_ids") or []) if i]
    if ids:
        doc["category_id"], doc["category_ids"] = ids[0], ids
    await db.shop_products.update_one({"id": pid}, {"$set": doc,
                                                   "$setOnInsert": {"id": pid, "sold": 0, "sort": 100, "created_at": p.get("created_at") or urun._now()}},
                                      upsert=True)
    try:
        import shop
        await shop.stock_changed(db, [pid])                   # açık pazaryerlerine stok/fiyat güncellemesi kuyruğa
    except Exception:                                          # noqa: BLE001
        pass


async def ayna_hepsi(db):
    n = 0
    async for p in db.yp_products.find({}, {"_id": 0, "id": 1}):
        await ayna(db, p["id"])
        n += 1
    return n


async def geri(db, ids):
    """Mağaza/pazaryeri satışında düşen (ya da iadede artan) stoğu panel ürününe yaz."""
    for pid in set(ids or []):
        d = await db.shop_products.find_one({"id": pid, "src.panel": True}, {"_id": 0, "stock": 1, "variants": 1})
        if d is not None:
            up = {"stock": urun._int(d.get("stock")), "updated_at": urun._now()}
            if d.get("variants"):                  # varyantlı ürün: her seçeneğin stoğunu panele yaz, toplamı yeniden hesapla
                yp = await db.yp_products.find_one({"id": pid}, {"_id": 0, "variants": 1})
                st = {v["id"]: urun._int(v.get("stock")) for v in d["variants"]}
                vs = [dict(v, stock=st.get(v["id"], urun._int(v.get("stock")))) for v in (yp or {}).get("variants", [])]
                if vs:
                    up["variants"] = vs
                    up["stock"] = sum(v["stock"] for v in vs if v.get("active", True))
            await db.yp_products.update_one({"id": pid}, {"$set": up})
