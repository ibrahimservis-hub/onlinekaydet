# -*- coding: utf-8 -*-
"""Mağaza ürünlerinde varyantlı (renk/beden) stok düşümü ve iadesi. Varyant yoksa eski davranış."""


async def al(db, pid, qty, vid="", track=True):
    """Koşullu düş (yarışta eksiye düşmesin). True: düşüldü."""
    if not track:
        r = await db.shop_products.update_one({"id": pid}, {"$inc": {"sold": qty}})
        return bool(r.matched_count)
    if vid:
        r = await db.shop_products.update_one(
            {"id": pid, "variants": {"$elemMatch": {"id": vid, "stock": {"$gte": qty}}}},
            {"$inc": {"variants.$.stock": -qty, "stock": -qty, "sold": qty}})
    else:
        r = await db.shop_products.update_one({"id": pid, "stock": {"$gte": qty}}, {"$inc": {"stock": -qty, "sold": qty}})
    return bool(r.modified_count)


async def ver(db, pid, qty, vid=""):
    """İptal/iade: stoğu geri ekle."""
    if vid:
        await db.shop_products.update_one({"id": pid, "track_stock": True, "variants.id": vid},
                                          {"$inc": {"variants.$.stock": qty, "stock": qty, "sold": -qty}})
    else:
        await db.shop_products.update_one({"id": pid, "track_stock": True}, {"$inc": {"stock": qty, "sold": -qty}})


def sec(p, vid):
    """Ürün belgesinden seçeneği bul (yoksa None). Varyantlı üründe seçenek zorunludur."""
    return next((v for v in (p.get("variants") or []) if v.get("id") == vid), None) if vid else None
