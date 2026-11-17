# -*- coding: utf-8 -*-
"""Pazaryeri ve yemek platformlarından çekilen siparişi müşteri panelinin Siparişler listesine (yp_orders) yazar.

Stok burada düşülmez: markets_hub.apply_market_order zaten tek havuzdan bir kez düşer.
Aynı sipariş ikinci kez gelirse yeni kayıt açılmaz, yalnızca durumu güncellenir.
"""
import uuid
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

ON = {"yemeksepeti": "YS", "trendyol_yemek": "TYY", "getir_yemek": "GY", "migros_yemek": "MY", "trendyol": "TY", "hepsiburada": "HB",
      "n11": "N11", "ciceksepeti": "CS", "pazarama": "PZ", "pttavm": "PTT", "site": "SP"}
DURUM = {"onaylandi": "onaylandi", "hazirlaniyor": "hazirlaniyor", "kargoda": "kargoda", "teslim_edildi": "teslim", "iptal": "iptal"}


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


async def yaz(db, mk, n, mapped, comm=None):
    """n: markets_hub.normalize çıktısı. Döner: True = yeni kayıt açıldı."""
    st = DURUM.get(mapped, "yeni")
    cur = await db.yp_orders.find_one({"channel": mk, "market_no": n["key"]}, {"_id": 0, "id": 1, "status": 1})
    if cur:
        if cur.get("status") != st:
            await db.yp_orders.update_one({"id": cur["id"]}, {"$set": {"status": st}, "$push": {"timeline": {"at": _now(), "by": mk, "state": st, "note": "platformdan güncellendi"}}})
        return False
    items = []
    for ln in n["lines"]:
        pid = ""
        if ln.get("barcode"):
            p = await db.yp_products.find_one({"$or": [{"barcode": ln["barcode"]}, {"sku": ln["barcode"]}]}, {"_id": 0, "id": 1})
            pid = (p or {}).get("id", "")
        items.append({"product": pid, "name": ln["name"], "sku": ln["barcode"], "qty": ln["quantity"], "price": ln["price"], "discount": 0, "cost": 0, "vat": 20.0})
    cu = n["customer"]
    cnt = await db.yp_orders.count_documents({})
    at = (n["created"].astimezone(TR).replace(tzinfo=None).isoformat(timespec="seconds") if n.get("created") else _now())
    o = {"id": uuid.uuid4().hex[:12], "no": ("%s-%s" % (ON.get(mk, mk[:3].upper()), n["key"]))[:30], "channel": mk, "at": at, "seq": cnt + 1, "status": st,
         "customer": {"name": cu.get("name") or "Platform müşterisi", "phone": "".join(c for c in cu.get("phone", "") if c.isdigit())[-11:], "email": cu.get("email", ""),
                      "city": cu.get("city", ""), "district": cu.get("district", ""), "address": cu.get("address", ""), "group": "", "tckn": "", "note": ""},
         "items": items, "subtotal": n["total"], "discount": 0, "camps": [], "coupon": "", "ship_fee": 0, "ship_cost": 0, "free_ship": False, "gifts": [],
         "total": n["total"], "payment": "pazaryeri", "paid": True, "market_no": n["key"],
         "cargo": {"firm": "", "code": "", "barcode": "", "label": ""}, "invoice": {"no": "", "uuid": "", "state": ""}, "note": "",
         "external": True, "timeline": [{"at": _now(), "by": mk, "state": st, "note": "platformdan alındı"}]}
    if comm is not None:
        o["comm"] = comm
    await db.yp_orders.insert_one(o)
    return True
