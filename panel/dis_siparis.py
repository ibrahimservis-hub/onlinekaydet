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
            await kasaya_isle(db, cur["id"])
        return False
    items = []
    for ln in n["lines"]:
        pid, cost, vat = "", 0, 20.0
        if ln.get("barcode"):
            p = await db.yp_products.find_one({"$or": [{"barcode": ln["barcode"]}, {"sku": ln["barcode"]}]}, {"_id": 0, "id": 1, "cost": 1, "vat": 1})
            pid = (p or {}).get("id", "")
            try:                                           # kâr hesabı için ürün kartındaki alış maliyeti ve KDV oranı
                cost = float((p or {}).get("cost") or 0)
                vat = float((p or {}).get("vat") or 20.0)
            except (TypeError, ValueError):
                cost, vat = 0, 20.0
        items.append({"product": pid, "name": ln["name"], "sku": ln["barcode"], "qty": ln["quantity"], "price": ln["price"], "discount": 0, "cost": cost, "vat": vat})
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
    await kasaya_isle(db, o["id"])
    return True


KASA_YONT = {"nakit": "Nakit", "kart": "Kart", "havale": "Havale", "kapida_nakit": "Nakit", "kapida_kart": "Kart"}


async def kasaya_isle(db, oid):
    """Teslim edilen siparişin tahsilatı kasaya, komisyon ve kargo gideri çıkış olarak işlenir. Aynı sipariş bir kez."""
    o = await db.yp_orders.find_one({"id": oid}, {"_id": 0})
    if not o or o.get("status") != "teslim":
        return False
    if await db.yp_cash.find_one({"ref": oid, "kind": "siparis"}, {"_id": 1}):
        return False
    try:
        tot = float(o.get("total") or 0)
    except (TypeError, ValueError):
        tot = 0
    if tot <= 0:
        return False
    at = _now()[:16]
    mt = KASA_YONT.get(o.get("payment"), "Havale")
    no = o.get("no", "")
    rows = [{"type": "in", "amount": round(tot, 2), "method": mt, "desc": "Sipariş %s tahsilat" % no}]
    try:
        kom = round(tot * float(o.get("comm") or 0) / 100.0, 2)
    except (TypeError, ValueError):
        kom = 0
    if kom > 0:
        rows.append({"type": "out", "amount": kom, "method": "Havale", "desc": "Sipariş %s pazaryeri komisyonu" % no})
    try:
        kg = round(float(o.get("ship_cost") or 0), 2)
    except (TypeError, ValueError):
        kg = 0
    if kg > 0:
        rows.append({"type": "out", "amount": kg, "method": "Havale", "desc": "Sipariş %s kargo gideri" % no})
    for r in rows:
        await db.yp_cash.insert_one({"id": uuid.uuid4().hex[:12], "at": at, "kind": "siparis", "ref": oid, "ref_no": no, "staff_id": "", "by": "sistem", **r})
    return True
