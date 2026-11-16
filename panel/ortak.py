# -*- coding: utf-8 -*-
"""Ortaklık (affiliate): ortak kaydı, referans kodu/linki, tıklama sayacı, sipariş komisyonu (bekliyor → onaylı → ödendi), ödeme kaydı.

Komisyon YALNIZ sepet tutarı (kargo hariç) üzerinden, sipariş anındaki ortak oranıyla hesaplanır. Bayi (B2B/cari) siparişlerinde komisyon doğmaz;
toptan fiyat ortağa, tıklama kaydına ya da herkese açık uçlara hiçbir yerde yazılmaz. Durum sipariş durumundan türetilir:
teslim_edildi → onaylı, iptal → iptal; ödenmiş komisyon sonradan değişmez."""
import hashlib
import secrets
import time
import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request

AL = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
BEKLEME = 6 * 3600                                  # aynı ziyaretçinin aynı kodu yeniden tıklaması sayılmaz


def _now():
    return datetime.now(timezone.utc).isoformat()


def _t(v, n):
    return " ".join(str(v or "").split())[:n]


def _f(v, d=0.0):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return d


def _code(v):
    return "".join(ch for ch in str(v or "").upper() if ch.isalnum())[:16]


def _pk(v):
    d = "".join(ch for ch in str(v or "") if ch.isdigit())
    return d[-10:]


# ---------------------------------------------------------------- sipariş kancası (shop.py çağırır)
async def kaydet(db, order, ref, dealer=None):
    """Siparişe komisyon yazar (yoksa sessizce çıkar). Siparişi hiçbir koşulda bozmaz."""
    try:
        code = _code(ref)
        if not code or dealer or order.get("payment", {}).get("method") == "cari":
            return None
        a = await db.yp_affiliates.find_one({"code": code, "status": "active"}, {"_id": 0})
        if not a:
            return None
        if a.get("phone_key") and a["phone_key"] == order.get("phone_key"):
            return None                              # kendi siparişine komisyon yok
        base = round(float(order.get("subtotal") or 0), 2)
        amt = round(base * float(a.get("pct") or 0) / 100, 2)
        if amt <= 0:
            return None
        c = {"id": uuid.uuid4().hex[:12], "aff_id": a["id"], "code": code, "order_id": order["id"], "order_no": order.get("order_no", ""),
             "base": base, "pct": a["pct"], "amount": amt, "status": "pending", "created_at": _now(), "updated_at": _now()}
        if await db.yp_aff_comm.find_one({"order_id": order["id"]}, {"_id": 1}):
            return None
        await db.yp_aff_comm.insert_one(dict(c))
        return c
    except Exception:                                   # noqa: BLE001
        return None


async def senkron(db, aff_id=None):
    """Bekleyen/onaylı komisyonların durumunu sipariş durumuna eşitler."""
    q = {"status": {"$in": ["pending", "approved"]}}
    if aff_id:
        q["aff_id"] = aff_id
    rows = await db.yp_aff_comm.find(q, {"_id": 0}).to_list(5000)
    if not rows:
        return
    od = {o["id"]: o["status"] for o in await db.shop_orders.find({"id": {"$in": [r["order_id"] for r in rows]}}, {"_id": 0, "id": 1, "status": 1}).to_list(5000)}
    for r in rows:
        st = od.get(r["order_id"])
        new = "cancelled" if (st in ("iptal", None)) else ("approved" if st == "teslim_edildi" else "pending")
        if new != r["status"]:
            await db.yp_aff_comm.update_one({"id": r["id"], "status": r["status"]}, {"$set": {"status": new, "updated_at": _now()}})


def register(api_router, db, deps):
    adm = Depends(deps["require_admin"])

    def vid(request: Request):
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
        return hashlib.sha256((ip + "|" + request.headers.get("user-agent", "")[:80]).encode()).hexdigest()[:20]

    async def yeni_kod():
        for _ in range(20):
            c = "".join(secrets.choice(AL) for _ in range(6))
            if not await db.yp_affiliates.find_one({"code": c}, {"_id": 1}):
                return c
        raise HTTPException(500, "Kod üretilemedi")

    async def ozet(a):
        cm = await db.yp_aff_comm.find({"aff_id": a["id"]}, {"_id": 0}).to_list(5000)
        s = lambda st: round(sum(x["amount"] for x in cm if x["status"] == st), 2)
        a = dict(a)
        a.update({"orders": len([x for x in cm if x["status"] != "cancelled"]), "pending": s("pending"), "approved": s("approved"), "paid": s("paid"),
                  "link": "/magaza?ref=" + a["code"]})
        return a

    # ------------------------------------------------------------------ herkese açık: tıklama
    @api_router.post("/public/ortak/click")
    async def click(payload: dict, request: Request):
        code = _code(payload.get("code"))
        a = await db.yp_affiliates.find_one({"code": code, "status": "active"}, {"_id": 0, "id": 1})
        if not a:
            return {"ok": False}
        v = vid(request)
        since = time.time() - BEKLEME
        if await db.yp_aff_clicks.find_one({"aff_id": a["id"], "v": v, "ts": {"$gt": since}}, {"_id": 1}):
            return {"ok": True, "counted": False}
        await db.yp_aff_clicks.insert_one({"aff_id": a["id"], "v": v, "ts": time.time(), "at": _now()})
        return {"ok": True, "counted": True}

    # ------------------------------------------------------------------ panel
    @api_router.get("/yp/ortak")
    async def liste(_: dict = adm):
        await senkron(db)
        rows = []
        for a in await db.yp_affiliates.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000):
            r = await ozet(a)
            r["clicks"] = await db.yp_aff_clicks.count_documents({"aff_id": a["id"]})
            rows.append(r)
        tot = {k: round(sum(r[k] for r in rows), 2) for k in ("pending", "approved", "paid")}
        return {"rows": rows, "total": tot}

    def temiz(p, yeni):
        name = _t(p.get("name"), 120)
        if yeni and len(name) < 2:
            raise HTTPException(422, "Ortak adı gerekli")
        pct = _f(p.get("pct"), -1)
        if (yeni or "pct" in p) and not (0 < pct <= 50):
            raise HTTPException(422, "Komisyon oranı %0 ile %50 arasında olmalı")
        out = {"name": name, "phone": _t(p.get("phone"), 30), "email": _t(p.get("email"), 120).lower(), "note": _t(p.get("note"), 300),
               "iban": _t(p.get("iban"), 40)}
        out["phone_key"] = _pk(out["phone"])
        if "pct" in p or yeni:
            out["pct"] = round(pct, 2)
        return out

    @api_router.post("/yp/ortak")
    async def olustur(p: dict, _: dict = adm):
        d = temiz(p, True)
        code = _code(p.get("code")) or await yeni_kod()
        if len(code) < 4:
            raise HTTPException(422, "Kod en az 4 harf/rakam olmalı")
        if await db.yp_affiliates.find_one({"code": code}, {"_id": 1}):
            raise HTTPException(409, "Bu kod başka bir ortakta kullanılıyor")
        d.update({"id": uuid.uuid4().hex[:12], "code": code, "status": "active", "created_at": _now()})
        await db.yp_affiliates.insert_one(dict(d))
        d.pop("_id", None)
        return d

    @api_router.post("/yp/ortak/{aid}")
    async def guncelle(aid: str, p: dict, _: dict = adm):
        if not await db.yp_affiliates.find_one({"id": aid}, {"_id": 1}):
            raise HTTPException(404, "Ortak bulunamadı")
        d = temiz({k: v for k, v in p.items() if k in ("name", "phone", "email", "note", "iban", "pct")}, False)
        d = {k: v for k, v in d.items() if (k in p or k == "phone_key")}
        if "name" in p and len(d.get("name", "")) < 2:
            raise HTTPException(422, "Ortak adı gerekli")
        if p.get("status") in ("active", "passive"):
            d["status"] = p["status"]
        await db.yp_affiliates.update_one({"id": aid}, {"$set": d})
        return {"ok": True}

    @api_router.get("/yp/ortak/{aid}/komisyon")
    async def komisyon(aid: str, _: dict = adm):
        await senkron(db, aid)
        rows = await db.yp_aff_comm.find({"aff_id": aid}, {"_id": 0}).sort("created_at", -1).to_list(2000)
        pays = await db.yp_aff_pay.find({"aff_id": aid}, {"_id": 0}).sort("at", -1).to_list(200)
        return {"rows": rows, "payouts": pays}

    @api_router.post("/yp/ortak/{aid}/odeme")
    async def odeme(aid: str, p: dict, _: dict = adm):
        a = await db.yp_affiliates.find_one({"id": aid}, {"_id": 0})
        if not a:
            raise HTTPException(404, "Ortak bulunamadı")
        await senkron(db, aid)
        rows = await db.yp_aff_comm.find({"aff_id": aid, "status": "approved"}, {"_id": 0}).to_list(5000)
        ids, total = [], 0.0
        for r in rows:                                  # her komisyon tek seferde ödenir (koşullu güncelleme)
            u = await db.yp_aff_comm.update_one({"id": r["id"], "status": "approved"}, {"$set": {"status": "paid", "paid_at": _now()}})
            if u.modified_count:
                ids.append(r["id"]); total += r["amount"]
        if not ids:
            raise HTTPException(422, "Ödenecek onaylı komisyon yok")
        po = {"id": uuid.uuid4().hex[:12], "aff_id": aid, "amount": round(total, 2), "count": len(ids), "note": _t(p.get("note"), 200), "at": _now(), "comm_ids": ids}
        await db.yp_aff_pay.insert_one(dict(po))
        po.pop("_id", None)
        return po
