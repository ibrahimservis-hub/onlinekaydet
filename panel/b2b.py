# -*- coding: utf-8 -*-
"""B2B bayi: gruplar (iskonto, asgari sipariş), başvuru+onay, bayiye özel toptan fiyat, cari hesap (borç/alacak defteri).

Toptan fiyat YALNIZ burada tutulur (yp_b2b_prices) ve yalnız sipariş anında sunucuda çözülür: ürün belgesine, aynaya, pazaryeri
kuyruğuna ya da herkese açık ürün uçlarına yazılmaz; bu yüzden pazaryerlerine sızamaz. Bayi, mağaza müşteri hesabına bağlanır."""
import re
import time
import uuid
from datetime import datetime, timezone

import jwt
from fastapi import Depends, HTTPException, Request

DURUM = ("pending", "approved", "blocked")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _f(v, d=0.0):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return d


def _t(v, n):
    return " ".join(str(v or "").split())[:n]


# ---------------------------------------------------------------- sipariş kancaları (shop.py çağırır)
async def dealer_of(db, acc):
    """Onaylı bayi kaydı (yoksa None)."""
    if not acc:
        return None
    d = await db.yp_b2b_dealers.find_one({"account_id": acc["id"], "status": "approved"}, {"_id": 0})
    if not d:
        return None
    g = await db.yp_b2b_groups.find_one({"id": d.get("group_id")}, {"_id": 0}) or {}
    d["group"] = g
    return d


async def bakiye(db, dealer_id):
    b = 0.0
    for e in await db.yp_b2b_ledger.find({"dealer_id": dealer_id}, {"_id": 0, "tur": 1, "tutar": 1}).to_list(100000):
        b += e["tutar"] if e["tur"] == "borc" else -e["tutar"]
    return round(b, 2)


async def fiyat(db, dealer, p, v, unit):
    """Bayiye uygulanacak birim fiyat. Liste fiyatından büyük olamaz."""
    if not dealer:
        return unit
    g = dealer.get("group") or {}
    ov = await db.yp_b2b_prices.find_one({"group_id": g.get("id"), "product_id": p["id"]}, {"_id": 0})
    out = unit
    if ov and ov.get("price", 0) > 0:
        base = p.get("price") or 0
        out = ov["price"] * (unit / base) if (v and base > 0) else ov["price"]   # seçenekli üründe seçenek farkı orantılı korunur
    elif g.get("discount_pct", 0) > 0:
        out = unit * (1 - min(g["discount_pct"], 90) / 100.0)
    return round(min(out, unit), 2)


async def kontrol(db, dealer, subtotal, total, pm_id):
    if not dealer:
        return
    g = dealer.get("group") or {}
    if g.get("min_order", 0) and subtotal < g["min_order"]:
        raise HTTPException(422, "Bayi grubunuz için asgari sipariş tutarı %.2f TL" % g["min_order"])
    if pm_id == "cari":
        lim = dealer.get("credit_limit", 0) or 0
        if lim <= 0:
            raise HTTPException(422, "Cari (vadeli) alışveriş için limitiniz tanımlı değil; başka bir ödeme yöntemi seçin")
        b = await bakiye(db, dealer["id"])
        if b + total > lim + 0.001:
            raise HTTPException(422, "Cari limitinizi aşıyor (limit %.2f TL, güncel borç %.2f TL, kullanılabilir %.2f TL)" % (lim, b, max(0, lim - b)))


async def kaydet(db, dealer, order):
    """Sipariş oluştuktan sonra: cari ödemeli ise borç satırı yazar."""
    if not dealer:
        return
    await db.shop_orders.update_one({"id": order["id"]}, {"$set": {"dealer_id": dealer["id"]}})
    if order["payment"]["method"] == "cari":
        await db.yp_b2b_ledger.insert_one({"id": uuid.uuid4().hex[:12], "dealer_id": dealer["id"], "tur": "borc", "tutar": round(order["total"], 2),
                                           "aciklama": "Sipariş " + order["order_no"], "order_no": order["order_no"], "at": _now(), "by": "sistem"})


async def iade(db, order):
    """İptal/iade: cari ödemeli siparişin borcu tek seferlik alacak satırıyla kapatılır."""
    if (order.get("payment") or {}).get("method") != "cari" or not order.get("dealer_id"):
        return
    if await db.yp_b2b_ledger.find_one({"dealer_id": order["dealer_id"], "order_no": order["order_no"], "tur": "alacak"}, {"_id": 1}):
        return
    await db.yp_b2b_ledger.insert_one({"id": uuid.uuid4().hex[:12], "dealer_id": order["dealer_id"], "tur": "alacak", "tutar": round(order["total"], 2),
                                       "aciklama": "İptal/iade " + order["order_no"], "order_no": order["order_no"], "at": _now(), "by": "sistem"})


def register(api_router, db, deps):
    adm = Depends(deps["require_admin"])
    JWT_SECRET, JWT_ALGORITHM = deps["JWT_SECRET"], deps["JWT_ALGORITHM"]

    async def hesap(request: Request):
        h = request.headers.get("authorization", "")
        tok = h[7:] if h.lower().startswith("bearer ") else ""
        try:
            pl = jwt.decode(tok, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except Exception:                                                  # noqa: BLE001
            raise HTTPException(401, "Giriş yapmanız gerekiyor")
        acc = await db.customer_accounts.find_one({"id": pl.get("sub")}, {"_id": 0}) if pl.get("typ") == "customer" else None
        if not acc:
            raise HTTPException(401, "Giriş yapmanız gerekiyor")
        return acc

    # ------------------------------------------------------------------ gruplar
    @api_router.get("/yp/b2b/groups")
    async def groups(_: dict = adm):
        gs = await db.yp_b2b_groups.find({}, {"_id": 0}).sort("name", 1).to_list(500)
        for g in gs:
            g["dealers"] = await db.yp_b2b_dealers.count_documents({"group_id": g["id"]})
            g["prices"] = await db.yp_b2b_prices.count_documents({"group_id": g["id"]})
        return {"rows": gs}

    @api_router.post("/yp/b2b/groups")
    async def group_save(payload: dict, _: dict = adm):
        name = _t(payload.get("name"), 60)
        if len(name) < 2:
            raise HTTPException(422, "Grup adı yazın")
        d = _f(payload.get("discount_pct"))
        if d < 0 or d > 90:
            raise HTTPException(422, "İskonto % 0 ile 90 arasında olmalı")
        doc = {"name": name, "discount_pct": round(d, 2), "min_order": max(0.0, round(_f(payload.get("min_order")), 2)), "note": _t(payload.get("note"), 200)}
        gid = str(payload.get("id") or "")
        if gid:
            if not await db.yp_b2b_groups.find_one({"id": gid}, {"_id": 1}):
                raise HTTPException(404, "Grup bulunamadı")
            await db.yp_b2b_groups.update_one({"id": gid}, {"$set": doc})
        else:
            if await db.yp_b2b_groups.find_one({"name": name}, {"_id": 1}):
                raise HTTPException(409, "Bu adla bir grup var")
            gid = uuid.uuid4().hex[:10]
            await db.yp_b2b_groups.insert_one({"id": gid, **doc, "created_at": _now()})
        return {"ok": True, "id": gid}

    @api_router.delete("/yp/b2b/groups/{gid}")
    async def group_del(gid: str, _: dict = adm):
        if await db.yp_b2b_dealers.find_one({"group_id": gid}, {"_id": 1}):
            raise HTTPException(409, "Bu grupta bayi var; önce bayileri başka gruba taşıyın")
        await db.yp_b2b_groups.delete_one({"id": gid})
        await db.yp_b2b_prices.delete_many({"group_id": gid})
        return {"ok": True}

    # ------------------------------------------------------------------ bayiler
    @api_router.get("/yp/b2b/dealers")
    async def dealers(status: str = "", _: dict = adm):
        flt = {"status": status} if status in DURUM else {}
        rows = await db.yp_b2b_dealers.find(flt, {"_id": 0}).sort("created_at", -1).to_list(2000)
        gm = {g["id"]: g["name"] for g in await db.yp_b2b_groups.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(500)}
        for r in rows:
            r["group_name"] = gm.get(r.get("group_id"), "")
            r["bakiye"] = await bakiye(db, r["id"])
        cnt = {s: await db.yp_b2b_dealers.count_documents({"status": s}) for s in DURUM}
        return {"rows": rows, "counts": cnt}

    @api_router.post("/yp/b2b/dealers/{did}")
    async def dealer_set(did: str, payload: dict, _: dict = adm):
        d = await db.yp_b2b_dealers.find_one({"id": did}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Bayi bulunamadı")
        up = {}
        if "status" in payload:
            if payload["status"] not in DURUM:
                raise HTTPException(422, "Geçersiz durum")
            up["status"] = payload["status"]
        if "group_id" in payload:
            if payload["group_id"] and not await db.yp_b2b_groups.find_one({"id": payload["group_id"]}, {"_id": 1}):
                raise HTTPException(422, "Grup bulunamadı")
            up["group_id"] = payload["group_id"] or ""
        if "credit_limit" in payload:
            up["credit_limit"] = max(0.0, round(_f(payload["credit_limit"]), 2))
        if "note" in payload:
            up["admin_note"] = _t(payload["note"], 300)
        new = {**d, **up}
        if new["status"] == "approved" and not new.get("group_id"):
            raise HTTPException(422, "Onaylamak için bir bayi grubu seçin")
        up["updated_at"] = _now()
        await db.yp_b2b_dealers.update_one({"id": did}, {"$set": up})
        return {"ok": True}

    @api_router.get("/yp/b2b/dealers/{did}/ledger")
    async def ledger(did: str, _: dict = adm):
        rows = await db.yp_b2b_ledger.find({"dealer_id": did}, {"_id": 0}).sort("at", -1).to_list(2000)
        return {"rows": rows, "bakiye": await bakiye(db, did)}

    @api_router.post("/yp/b2b/dealers/{did}/ledger")
    async def ledger_add(did: str, payload: dict, user: dict = adm):
        if not await db.yp_b2b_dealers.find_one({"id": did}, {"_id": 1}):
            raise HTTPException(404, "Bayi bulunamadı")
        tur = payload.get("tur")
        if tur not in ("borc", "alacak"):
            raise HTTPException(422, "Tür borç ya da alacak olmalı")
        tutar = round(_f(payload.get("tutar")), 2)
        if tutar <= 0:
            raise HTTPException(422, "Tutar sıfırdan büyük olmalı")
        await db.yp_b2b_ledger.insert_one({"id": uuid.uuid4().hex[:12], "dealer_id": did, "tur": tur, "tutar": tutar,
                                           "aciklama": _t(payload.get("aciklama"), 200) or ("Tahsilat" if tur == "alacak" else "Borç kaydı"),
                                           "order_no": "", "at": _now(), "by": user.get("name", "")})
        return {"ok": True, "bakiye": await bakiye(db, did)}

    # ------------------------------------------------------------------ toptan fiyat listesi
    @api_router.get("/yp/b2b/prices")
    async def prices(group: str, q: str = "", page: int = 1, _: dict = adm):
        if not await db.yp_b2b_groups.find_one({"id": group}, {"_id": 1}):
            raise HTTPException(404, "Grup bulunamadı")
        flt = {}
        if q.strip():
            rx = {"$regex": re.escape(q.strip()), "$options": "i"}
            flt["$or"] = [{"name": rx}, {"sku": rx}, {"barcode": rx}]
        page = max(1, page)
        total = await db.yp_products.count_documents(flt)
        ps = await db.yp_products.find(flt, {"_id": 0, "id": 1, "name": 1, "sku": 1, "price": 1}).sort("name", 1).skip((page - 1) * 50).limit(50).to_list(50)
        ov = {o["product_id"]: o["price"] for o in await db.yp_b2b_prices.find({"group_id": group, "product_id": {"$in": [p["id"] for p in ps]}}, {"_id": 0}).to_list(100)}
        for p in ps:
            p["b2b_price"] = ov.get(p["id"], 0)
        return {"rows": ps, "total": total, "page": page}

    @api_router.put("/yp/b2b/prices")
    async def prices_set(payload: dict, _: dict = adm):
        gid = str(payload.get("group") or "")
        if not await db.yp_b2b_groups.find_one({"id": gid}, {"_id": 1}):
            raise HTTPException(404, "Grup bulunamadı")
        n = 0
        for it in (payload.get("items") or [])[:200]:
            pid = str(it.get("product_id") or "")
            p = await db.yp_products.find_one({"id": pid}, {"_id": 0, "price": 1})
            if not p:
                continue
            pr = round(_f(it.get("price")), 2)
            if pr <= 0:
                await db.yp_b2b_prices.delete_one({"group_id": gid, "product_id": pid})
            else:
                if pr > (p.get("price") or 0) > 0:
                    raise HTTPException(422, "Toptan fiyat liste fiyatından yüksek olamaz")
                await db.yp_b2b_prices.update_one({"group_id": gid, "product_id": pid}, {"$set": {"price": pr, "updated_at": _now()}}, upsert=True)
            n += 1
        return {"ok": True, "n": n}

    # ------------------------------------------------------------------ bayi (müşteri hesabıyla)
    async def durum(acc):
        d = await db.yp_b2b_dealers.find_one({"account_id": acc["id"]}, {"_id": 0})
        if not d:
            return {"status": "none"}
        g = await db.yp_b2b_groups.find_one({"id": d.get("group_id")}, {"_id": 0}) or {}
        out = {"status": d["status"], "company": d.get("company", ""), "address": d.get("address", "")}
        if d["status"] == "approved":
            b = await bakiye(db, d["id"])
            out.update({"group": g.get("name", ""), "discount_pct": g.get("discount_pct", 0), "min_order": g.get("min_order", 0),
                        "credit_limit": d.get("credit_limit", 0), "bakiye": b, "kullanilabilir": max(0, round((d.get("credit_limit", 0) or 0) - b, 2))})
        return out

    @api_router.get("/public/b2b/me")
    async def me(request: Request):
        return await durum(await hesap(request))

    @api_router.post("/public/b2b/apply")
    async def apply(payload: dict, request: Request):
        acc = await hesap(request)
        if await db.yp_b2b_dealers.find_one({"account_id": acc["id"]}, {"_id": 1}):
            raise HTTPException(409, "Başvurunuz zaten var")
        company, address = _t(payload.get("company"), 120), _t(payload.get("address"), 300)
        tax_no = re.sub(r"\D", "", str(payload.get("tax_no") or ""))
        if len(company) < 3:
            raise HTTPException(422, "Firma unvanı yazın")
        if len(tax_no) not in (10, 11):
            raise HTTPException(422, "Vergi no (10 hane) ya da TC kimlik no (11 hane) girin")
        if len(address) < 8:
            raise HTTPException(422, "Teslimat adresi yazın")
        await db.yp_b2b_dealers.insert_one({"id": uuid.uuid4().hex[:10], "account_id": acc["id"], "company": company, "tax_no": tax_no,
                                            "tax_office": _t(payload.get("tax_office"), 60), "contact": acc.get("name", ""), "phone": acc.get("phone", ""),
                                            "email": acc.get("email", ""), "address": address, "city": _t(payload.get("city"), 60), "status": "pending",
                                            "group_id": "", "credit_limit": 0.0, "admin_note": "", "created_at": _now(), "updated_at": _now()})
        return {"ok": True, "status": "pending"}

    @api_router.get("/public/b2b/products")
    async def pub_products(request: Request, q: str = "", page: int = 1):
        acc = await hesap(request)
        d = await dealer_of(db, acc)
        if not d:
            raise HTTPException(403, "Bayi hesabınız onaylı değil")
        flt = {"active": True}
        if q.strip():
            rx = {"$regex": re.escape(q.strip()), "$options": "i"}
            flt["$or"] = [{"name": rx}, {"sku": rx}, {"brand": rx}]
        page = max(1, page)
        total = await db.shop_products.count_documents(flt)
        ps = await db.shop_products.find(flt, {"_id": 0}).sort("name", 1).skip((page - 1) * 40).limit(40).to_list(40)
        rows = []
        for p in ps:
            vs = []
            for v in p.get("variants") or []:
                if v.get("active") is False:
                    continue
                vs.append({"id": v["id"], "label": v.get("label", ""), "sku": v.get("sku", ""), "stock": v.get("stock", 0), "list_price": v.get("price"),
                           "price": await fiyat(db, d, p, v, v.get("price") or p.get("price", 0))})
            rows.append({"id": p["id"], "slug": p.get("slug", ""), "name": p["name"], "brand": p.get("brand", ""), "sku": p.get("sku", ""), "img": (p.get("images") or [""])[0],
                         "stock": p.get("stock", 0), "track_stock": p.get("track_stock", True), "list_price": p.get("price", 0),
                         "price": await fiyat(db, d, p, None, p.get("price", 0)), "variants": vs})
        return {"rows": rows, "total": total, "page": page, "bayi": await durum(acc)}
