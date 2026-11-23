# -*- coding: utf-8 -*-
"""Siparişlerden toplu fatura taslağı: seçilen siparişler tek işlemle numaralı fatura kaydına çevrilir.

Her fatura satır bazında KDV'yi ayırır (KDV dahil satış fiyatından). Aynı sipariş ikinci kez faturalanmaz.
Hazırlanan faturalar tek dosyada (entegratörün toplu yükleme biçimi) indirilir; entegratör bağlıysa
`entegre` işaretiyle listelenir. Taslak faturalar iptal edilip siparişe bağlı kayıt serbest bırakılabilir.
"""
import csv
import io
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


def _n(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def hesapla(o):
    """Sipariş kalemlerinden KDV'li satırlar ve toplamlar. Fiyatlar KDV dahildir."""
    lines, matrah, kdv = [], 0.0, 0.0
    sub = sum(_n(i.get("price")) * _n(i.get("qty"), 1) - _n(i.get("discount")) for i in o.get("items") or []) or 0.0
    toplam = _n(o.get("total"))
    oran = (toplam / sub) if sub > 0 and toplam > 0 else 1.0       # sipariş indirimi/kargo kalemlere orantılı dağılır
    for i in o.get("items") or []:
        q = _n(i.get("qty"), 1)
        brut = round((_n(i.get("price")) * q - _n(i.get("discount"))) * oran, 2)
        v = _n(i.get("vat"), 20.0)
        net = round(brut / (1 + v / 100.0), 2)
        lines.append({"name": str(i.get("name") or "")[:120], "sku": str(i.get("sku") or "")[:60], "qty": q, "vat": v,
                      "matrah": net, "kdv": round(brut - net, 2), "total": brut})
        matrah += net
        kdv += brut - net
    if not lines and toplam:
        net = round(toplam / 1.2, 2)
        lines.append({"name": "Satış", "sku": "", "qty": 1, "vat": 20.0, "matrah": net, "kdv": round(toplam - net, 2), "total": toplam})
        matrah, kdv = net, toplam - net
    return lines, round(matrah, 2), round(kdv, 2), round(matrah + kdv, 2)


def register(api_router, db, deps):
    adm = deps["require_admin"]
    from fastapi import Depends

    async def sonraki_no():
        y = datetime.now(TR).year
        n = await db.yp_invoices.count_documents({"series_year": y}) + 1
        return y, "FTR%d%09d" % (y, n)

    @api_router.post("/yp/orders/fatura")
    async def toplu_fatura(payload: dict, _=Depends(adm)):
        """Seçili siparişler için fatura taslağı. İptal siparişler ve zaten faturalı olanlar atlanır."""
        ids = [str(i)[:24] for i in (payload.get("ids") or [])][:2000]
        if not ids:
            raise HTTPException(422, "Önce sipariş seçin")
        done, skip = [], []
        for oid in ids:
            o = await db.yp_orders.find_one({"id": oid}, {"_id": 0})
            if not o:
                continue
            if o.get("status") == "iptal":
                skip.append({"no": o.get("no", ""), "why": "iptal sipariş faturalanmaz"})
                continue
            if await db.yp_invoices.find_one({"order_id": oid, "state": {"$ne": "iptal"}}, {"_id": 1}):
                skip.append({"no": o.get("no", ""), "why": "bu siparişin faturası zaten var"})
                continue
            lines, matrah, kdv, toplam = hesapla(o)
            y, no = await sonraki_no()
            cu = o.get("customer") or {}
            inv = {"id": uuid.uuid4().hex[:12], "no": no, "series_year": y, "order_id": oid, "order_no": o.get("no", ""), "at": _now(),
                   "state": "taslak", "type": "earsiv", "buyer": {"name": cu.get("name", ""), "tckn": cu.get("tckn", ""), "phone": cu.get("phone", ""),
                   "email": cu.get("email", ""), "address": ", ".join(x for x in (cu.get("address"), cu.get("district"), cu.get("city")) if x)},
                   "lines": lines, "matrah": matrah, "kdv": kdv, "total": toplam, "channel": o.get("channel", "site")}
            await db.yp_invoices.insert_one(dict(inv))
            await db.yp_orders.update_one({"id": oid}, {"$set": {"invoice": {"no": no, "uuid": inv["id"], "state": "taslak"}}})
            done.append(no)
        return {"ok": True, "n": len(done), "nos": done[:50], "skipped": skip,
                "msg": "%d fatura taslağı hazırlandı%s" % (len(done), (", %d sipariş atlandı" % len(skip)) if skip else "")}

    @api_router.get("/yp/invoices")
    async def liste(state: str = "", q: str = "", _=Depends(adm)):
        flt = {"state": state} if state else {}
        rows = await db.yp_invoices.find(flt, {"_id": 0}).sort("at", -1).to_list(3000)
        if q:
            ql = q.lower()
            rows = [r for r in rows if ql in (r["no"] + r.get("order_no", "") + (r.get("buyer") or {}).get("name", "")).lower()]
        return {"rows": rows, "n": len(rows), "toplam": round(sum(r["total"] for r in rows if r["state"] != "iptal"), 2),
                "kdv": round(sum(r["kdv"] for r in rows if r["state"] != "iptal"), 2)}

    @api_router.post("/yp/invoices/durum")
    async def durum(payload: dict, _=Depends(adm)):
        """Toplu: hazir (kesildi/yüklendi olarak işaretle) ya da iptal."""
        ids = [str(i)[:24] for i in (payload.get("ids") or [])][:2000]
        to = str(payload.get("state") or "")
        if to not in ("hazir", "iptal") or not ids:
            raise HTTPException(422, "Fatura ve durum seçin")
        n = 0
        for iid in ids:
            inv = await db.yp_invoices.find_one({"id": iid}, {"_id": 0})
            if not inv or inv["state"] == "iptal" or inv["state"] == to:
                continue
            if inv["state"] == "hazir" and to == "iptal":
                continue                                           # kesilmiş fatura iptal edilemez, iade faturası gerekir
            await db.yp_invoices.update_one({"id": iid}, {"$set": {"state": to, "state_at": _now()}})
            await db.yp_orders.update_one({"id": inv["order_id"]}, {"$set": {"invoice": {"no": inv["no"] if to != "iptal" else "", "uuid": iid if to != "iptal" else "", "state": to if to != "iptal" else ""}}})
            n += 1
        return {"ok": True, "n": n, "msg": "%d fatura güncellendi" % n}

    @api_router.post("/yp/invoices/export")
    async def disa(payload: dict, _=Depends(adm)):
        ids = [str(i)[:24] for i in (payload.get("ids") or [])][:5000]
        rows = await db.yp_invoices.find({"id": {"$in": ids}, "state": {"$ne": "iptal"}}, {"_id": 0}).sort("at", 1).to_list(5000)
        if not rows:
            raise HTTPException(422, "Aktarılacak fatura yok")
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=";")
        w.writerow(["Fatura No", "Tarih", "Sipariş No", "Alıcı", "TCKN/VKN", "Adres", "Ürün", "Adet", "KDV %", "Matrah", "KDV", "Toplam"])
        for r in rows:
            b = r.get("buyer") or {}
            for ln in r["lines"]:
                w.writerow([r["no"], r["at"][:10], r.get("order_no", ""), b.get("name", ""), b.get("tckn", ""), b.get("address", ""), ln["name"],
                            ("%g" % ln["qty"]).replace(".", ","), ("%g" % ln["vat"]).replace(".", ","), ("%.2f" % ln["matrah"]).replace(".", ","),
                            ("%.2f" % ln["kdv"]).replace(".", ","), ("%.2f" % ln["total"]).replace(".", ",")])
        return {"ok": True, "n": len(rows), "name": "faturalar-%s.csv" % datetime.now(TR).strftime("%Y%m%d"), "csv": "﻿" + buf.getvalue()}
