"""İleri düzey muhasebe: hesaplar (kasa/banka/pos), virman, kasa sayımı, personel, sabit giderler,
genel bakış (K/Z, nakit akışı) ve gelişmiş raporlar."""
import uuid
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Depends, HTTPException

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:
    TR = timezone(timedelta(hours=3))

EXPENSE_CATS = ["Maaş", "Avans", "Prim", "SGK / Vergi", "Kira", "Elektrik / Su / Doğalgaz", "İnternet / Telefon",
                "Yakıt", "Araç Bakım", "Malzeme / Parça Alımı", "Reklam (Google Ads vb.)", "Yemek", "Ofis Gideri",
                "Muhasebe / Danışmanlık", "Kargo / Nakliye", "Diğer"]
INCOME_CATS = ["Servis Geliri", "Parça Satışı", "Usta Tahsilatı", "Bayi Geliri", "Diğer Gelir"]
STAFF_KINDS = {"maas": "Maaş", "avans": "Avans", "prim": "Prim", "sgk": "SGK / Vergi", "yemek": "Yemek", "diger": "Diğer"}
PAY_METHODS = ["nakit", "kart", "havale", "cek"]


def _id():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc).isoformat()


def _day(s):
    return (s or "")[:10]


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    # ------------------------------------------------------------ yardımcılar
    async def default_account_id():
        a = await db.accounts.find_one({"is_default": True}, {"_id": 0})
        if a:
            return a["id"]
        if await db.accounts.count_documents({}) == 0:
            for name, typ, dflt in (("Nakit Kasa", "kasa", True), ("Banka Hesabı", "banka", False)):
                await db.accounts.insert_one({"id": _id(), "name": name, "type": typ, "opening_balance": 0.0,
                                              "is_default": dflt, "is_active": True, "note": "", "created_at": _now()})
            a = await db.accounts.find_one({"is_default": True}, {"_id": 0})
            return a["id"]
        a = await db.accounts.find_one({}, {"_id": 0})
        return a["id"]

    def deltas(tx, dflt):
        """Bir hareketin hesaplara gerçek para etkisi: {account_id: +/-tutar}. Servis tahakkukları (gelir/prim/borç) nakit değildir."""
        t, amt = tx.get("type"), float(tx.get("amount", 0) or 0)
        acc = tx.get("account_id") or dflt
        if t == "gelir" and not tx.get("job_id"):
            return {acc: amt}
        if t == "teknisyen_odeme":
            return {acc: amt}
        if t == "gider":
            return {acc: -amt}
        if t == "virman":
            return {tx.get("from_account_id") or dflt: -amt, tx.get("to_account_id") or dflt: amt}
        return {}

    async def balances(date_to: Optional[str] = None):
        dflt = await default_account_id()
        accs = await db.accounts.find({}, {"_id": 0}).sort("created_at", 1).to_list(200)
        q = {}
        if date_to:
            q["date"] = {"$lt": (datetime.fromisoformat(date_to) + timedelta(days=1)).date().isoformat()}
        txs = await db.cash_transactions.find(q, {"_id": 0}).to_list(200000)
        tot_in, tot_out = defaultdict(float), defaultdict(float)
        for tx in txs:
            for a, d in deltas(tx, dflt).items():
                (tot_in if d > 0 else tot_out)[a] += abs(d)
        out = []
        for a in accs:
            a["total_in"] = round(tot_in[a["id"]], 2)
            a["total_out"] = round(tot_out[a["id"]], 2)
            a["balance"] = round(float(a.get("opening_balance", 0)) + tot_in[a["id"]] - tot_out[a["id"]], 2)
            out.append(a)
        return out

    # ------------------------------------------------------------ hesaplar
    @api_router.get("/finance/accounts")
    async def list_accounts(_: dict = Depends(require_admin)):
        return await balances()

    @api_router.post("/finance/accounts")
    async def create_account(payload: dict, _: dict = Depends(require_admin)):
        name = (payload.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Hesap adı zorunlu")
        await default_account_id()
        doc = {"id": _id(), "name": name, "type": payload.get("type", "kasa"), "opening_balance": float(payload.get("opening_balance", 0) or 0),
               "is_default": False, "is_active": True, "note": payload.get("note", ""), "created_at": _now()}
        await db.accounts.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.put("/finance/accounts/{aid}")
    async def update_account(aid: str, payload: dict, _: dict = Depends(require_admin)):
        upd = {k: payload[k] for k in ("name", "type", "opening_balance", "note", "is_active") if k in payload}
        if "opening_balance" in upd:
            upd["opening_balance"] = float(upd["opening_balance"] or 0)
        if payload.get("is_default"):
            await db.accounts.update_many({}, {"$set": {"is_default": False}})
            upd["is_default"] = True
        r = await db.accounts.update_one({"id": aid}, {"$set": upd})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Hesap bulunamadı")
        return {"ok": True}

    @api_router.delete("/finance/accounts/{aid}")
    async def delete_account(aid: str, _: dict = Depends(require_admin)):
        a = await db.accounts.find_one({"id": aid}, {"_id": 0})
        if not a:
            raise HTTPException(status_code=404, detail="Hesap bulunamadı")
        if a.get("is_default"):
            raise HTTPException(status_code=400, detail="Varsayılan hesap silinemez")
        used = await db.cash_transactions.count_documents({"$or": [{"account_id": aid}, {"from_account_id": aid}, {"to_account_id": aid}]})
        if used:
            raise HTTPException(status_code=409, detail=f"Bu hesapta {used} hareket var; silmek yerine pasifleştirin")
        await db.accounts.delete_one({"id": aid})
        return {"ok": True}

    @api_router.post("/finance/transfer")
    async def transfer(payload: dict, user: dict = Depends(require_admin)):
        amt = float(payload.get("amount", 0) or 0)
        fa, ta = payload.get("from_account_id"), payload.get("to_account_id")
        if amt <= 0 or not fa or not ta or fa == ta:
            raise HTTPException(status_code=400, detail="Geçerli tutar ve farklı iki hesap seçin")
        doc = {"id": _id(), "type": "virman", "amount": amt, "from_account_id": fa, "to_account_id": ta,
               "description": payload.get("description") or "Hesaplar arası virman", "date": payload.get("date") or _now(),
               "category": "Virman", "created_by": user["id"]}
        await db.cash_transactions.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.get("/finance/accounts/{aid}/statement")
    async def statement(aid: str, date_from: Optional[str] = None, date_to: Optional[str] = None, _: dict = Depends(require_admin)):
        dflt = await default_account_id()
        a = await db.accounts.find_one({"id": aid}, {"_id": 0})
        if not a:
            raise HTTPException(status_code=404, detail="Hesap bulunamadı")
        txs = await db.cash_transactions.find({}, {"_id": 0}).sort("date", 1).to_list(200000)
        bal = float(a.get("opening_balance", 0))
        opening, rows = None, []
        for tx in txs:
            d = deltas(tx, dflt).get(aid)
            if d is None:
                continue
            day = _day(tx.get("date"))
            if date_from and day < date_from:
                bal += d
                continue
            if date_to and day > date_to:
                continue
            if opening is None:
                opening = bal
            bal += d
            rows.append({**tx, "delta": round(d, 2), "balance": round(bal, 2)})
        return {"account": a, "opening": round(opening if opening is not None else bal, 2), "closing": round(bal, 2), "rows": rows[::-1]}

    # ------------------------------------------------------------ kasa sayımı
    @api_router.post("/finance/cash-counts")
    async def add_count(payload: dict, user: dict = Depends(require_admin)):
        aid = payload.get("account_id")
        accs = {a["id"]: a for a in await balances()}
        if aid not in accs:
            raise HTTPException(status_code=404, detail="Hesap bulunamadı")
        counted = float(payload.get("counted", 0) or 0)
        expected = accs[aid]["balance"]
        diff = round(counted - expected, 2)
        doc = {"id": _id(), "account_id": aid, "account_name": accs[aid]["name"], "expected": expected, "counted": counted,
               "diff": diff, "note": payload.get("note", ""), "date": payload.get("date") or _now(), "by": user["name"], "adjusted": False}
        if payload.get("adjust") and diff != 0:
            await db.cash_transactions.insert_one({
                "id": _id(), "type": "gelir" if diff > 0 else "gider", "amount": abs(diff), "account_id": aid,
                "category": "Kasa Farkı", "description": f"Kasa sayım farkı ({accs[aid]['name']})", "date": doc["date"], "created_by": user["id"]})
            doc["adjusted"] = True
        await db.cash_counts.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.get("/finance/cash-counts")
    async def list_counts(_: dict = Depends(require_admin)):
        return await db.cash_counts.find({}, {"_id": 0}).sort("date", -1).to_list(500)

    @api_router.delete("/finance/cash-counts/{cid}")
    async def delete_count(cid: str, _: dict = Depends(require_admin)):
        await db.cash_counts.delete_one({"id": cid})
        return {"ok": True}

    # ------------------------------------------------------------ kategoriler
    @api_router.get("/finance/categories")
    async def categories(_: dict = Depends(require_admin)):
        s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        c = s.get("finance_categories") or {}
        return {"income": c.get("income") or INCOME_CATS, "expense": c.get("expense") or EXPENSE_CATS,
                "payment_methods": PAY_METHODS, "staff_kinds": STAFF_KINDS}

    @api_router.put("/finance/categories")
    async def put_categories(payload: dict, _: dict = Depends(require_admin)):
        c = {"income": [str(x)[:60] for x in payload.get("income", [])][:60], "expense": [str(x)[:60] for x in payload.get("expense", [])][:80]}
        await db.app_settings.update_one({"_id": "global"}, {"$set": {"finance_categories": c}}, upsert=True)
        return c

    # ------------------------------------------------------------ personel
    @api_router.get("/finance/staff")
    async def list_staff(_: dict = Depends(require_admin)):
        staff = await db.staff.find({}, {"_id": 0}).sort("name", 1).to_list(500)
        month = datetime.now(TR).strftime("%Y-%m")
        year = month[:4]
        txs = await db.cash_transactions.find({"staff_id": {"$nin": [None, ""]}}, {"_id": 0}).to_list(50000)
        for s in staff:
            mine = [t for t in txs if t.get("staff_id") == s["id"]]
            s["paid_this_month"] = round(sum(t["amount"] for t in mine if _day(t.get("period") or t.get("date"))[:7] == month), 2)
            s["paid_year"] = round(sum(t["amount"] for t in mine if _day(t.get("date"))[:4] == year), 2)
            s["advance_total"] = round(sum(t["amount"] for t in mine if t.get("category") == "Avans"), 2)
            s["salary_paid_this_month"] = any(t.get("category") == "Maaş" and (t.get("period") or _day(t.get("date"))[:7]) == month for t in mine)
        return staff

    @api_router.post("/finance/staff")
    async def create_staff(payload: dict, _: dict = Depends(require_admin)):
        name = (payload.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Ad zorunlu")
        doc = {"id": _id(), "name": name, "title": payload.get("title", ""), "phone": payload.get("phone", ""),
               "salary": float(payload.get("salary", 0) or 0), "start_date": payload.get("start_date", ""), "iban": payload.get("iban", ""),
               "note": payload.get("note", ""), "is_active": True, "created_at": _now()}
        await db.staff.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.put("/finance/staff/{sid}")
    async def update_staff(sid: str, payload: dict, _: dict = Depends(require_admin)):
        upd = {k: payload[k] for k in ("name", "title", "phone", "salary", "start_date", "iban", "note", "is_active") if k in payload}
        if "salary" in upd:
            upd["salary"] = float(upd["salary"] or 0)
        r = await db.staff.update_one({"id": sid}, {"$set": upd})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Personel bulunamadı")
        return {"ok": True}

    @api_router.delete("/finance/staff/{sid}")
    async def delete_staff(sid: str, _: dict = Depends(require_admin)):
        n = await db.cash_transactions.count_documents({"staff_id": sid})
        if n:
            await db.staff.update_one({"id": sid}, {"$set": {"is_active": False}})
            return {"ok": True, "deactivated": True, "detail": f"{n} ödeme kaydı olduğu için pasifleştirildi"}
        await db.staff.delete_one({"id": sid})
        return {"ok": True}

    @api_router.get("/finance/staff/{sid}/payments")
    async def staff_payments(sid: str, _: dict = Depends(require_admin)):
        return await db.cash_transactions.find({"staff_id": sid}, {"_id": 0}).sort("date", -1).to_list(1000)

    @api_router.post("/finance/staff/{sid}/pay")
    async def staff_pay(sid: str, payload: dict, user: dict = Depends(require_admin)):
        s = await db.staff.find_one({"id": sid}, {"_id": 0})
        if not s:
            raise HTTPException(status_code=404, detail="Personel bulunamadı")
        kind = payload.get("kind", "maas")
        amt = float(payload.get("amount", s.get("salary", 0)) or 0)
        if amt <= 0:
            raise HTTPException(status_code=400, detail="Tutar sıfırdan büyük olmalı")
        month = payload.get("month") or datetime.now(TR).strftime("%Y-%m")
        cat = STAFF_KINDS.get(kind, "Diğer")
        doc = {"id": _id(), "type": "gider", "amount": amt, "category": cat, "staff_id": sid, "period": month,
               "account_id": payload.get("account_id") or await default_account_id(), "payment_method": payload.get("payment_method", "nakit"),
               "description": payload.get("description") or f"{s['name']} — {cat} ({month})", "party": s["name"],
               "date": payload.get("date") or _now(), "created_by": user["id"]}
        await db.cash_transactions.insert_one(doc)
        doc.pop("_id", None)
        return doc

    # ------------------------------------------------------------ sabit giderler
    @api_router.get("/finance/recurring")
    async def list_recurring(_: dict = Depends(require_admin)):
        return await db.recurring_expenses.find({}, {"_id": 0}).sort("title", 1).to_list(300)

    @api_router.post("/finance/recurring")
    async def create_recurring(payload: dict, _: dict = Depends(require_admin)):
        if not (payload.get("title") or "").strip() or float(payload.get("amount", 0) or 0) <= 0:
            raise HTTPException(status_code=400, detail="Başlık ve tutar zorunlu")
        doc = {"id": _id(), "title": payload["title"].strip(), "amount": float(payload["amount"]), "category": payload.get("category", "Diğer"),
               "account_id": payload.get("account_id", ""), "payment_method": payload.get("payment_method", "havale"),
               "day_of_month": max(1, min(28, int(payload.get("day_of_month", 1) or 1))), "is_active": True, "last_run": "", "created_at": _now()}
        await db.recurring_expenses.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.put("/finance/recurring/{rid}")
    async def update_recurring(rid: str, payload: dict, _: dict = Depends(require_admin)):
        upd = {k: payload[k] for k in ("title", "amount", "category", "account_id", "payment_method", "day_of_month", "is_active") if k in payload}
        r = await db.recurring_expenses.update_one({"id": rid}, {"$set": upd})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
        return {"ok": True}

    @api_router.delete("/finance/recurring/{rid}")
    async def delete_recurring(rid: str, _: dict = Depends(require_admin)):
        await db.recurring_expenses.delete_one({"id": rid})
        return {"ok": True}

    @api_router.post("/finance/recurring/run")
    async def run_recurring(user: dict = Depends(require_admin)):
        now = datetime.now(TR)
        month = now.strftime("%Y-%m")
        n = 0
        for r in await db.recurring_expenses.find({"is_active": True}, {"_id": 0}).to_list(500):
            if r.get("last_run") == month or r["day_of_month"] > now.day:
                continue
            await db.cash_transactions.insert_one({
                "id": _id(), "type": "gider", "amount": r["amount"], "category": r["category"], "account_id": r.get("account_id") or await default_account_id(),
                "payment_method": r.get("payment_method", ""), "description": f"{r['title']} (sabit gider {month})", "recurring_id": r["id"],
                "date": f"{month}-{r['day_of_month']:02d}T09:00:00+03:00", "created_by": user["id"]})
            await db.recurring_expenses.update_one({"id": r["id"]}, {"$set": {"last_run": month}})
            n += 1
        return {"ok": True, "created": n}

    # ------------------------------------------------------------ genel bakış
    @api_router.get("/finance/overview")
    async def overview(date_from: Optional[str] = None, date_to: Optional[str] = None, _: dict = Depends(require_admin)):
        now = datetime.now(TR)
        if not date_from:
            date_from = now.replace(day=1).strftime("%Y-%m-%d")
        if not date_to:
            date_to = now.strftime("%Y-%m-%d")
        dflt = await default_account_id()
        txs = await db.cash_transactions.find({}, {"_id": 0}).to_list(200000)
        inr = [t for t in txs if date_from <= _day(t.get("date")) <= date_to]
        job_rev = sum(t["amount"] for t in inr if t["type"] == "gelir" and t.get("job_id"))
        other_inc = sum(t["amount"] for t in inr if t["type"] == "gelir" and not t.get("job_id"))
        tech_share = sum(t["amount"] for t in inr if t["type"] == "teknisyen_prim")
        expenses = [t for t in inr if t["type"] == "gider"]
        exp_total = sum(t["amount"] for t in expenses)
        by_cat = defaultdict(float)
        for t in expenses:
            by_cat[t.get("category") or "Kategorisiz"] += t["amount"]
        inc_cat = defaultdict(float)
        for t in inr:
            if t["type"] == "gelir":
                inc_cat[t.get("category") or ("Servis Geliri" if t.get("job_id") else "Kategorisiz")] += t["amount"]
        revenue = job_rev + other_inc
        gross = revenue - tech_share
        net = gross - exp_total
        collected = sum(t["amount"] for t in inr if t["type"] == "teknisyen_odeme") + other_inc
        staff_cost = sum(t["amount"] for t in expenses if t.get("staff_id"))
        borc = sum(t["amount"] for t in txs if t["type"] == "teknisyen_borc")
        odeme = sum(t["amount"] for t in txs if t["type"] == "teknisyen_odeme")
        # günlük nakit akışı (gerçek para)
        daily = defaultdict(lambda: [0.0, 0.0])
        for t in inr:
            for a, d in deltas(t, dflt).items():
                if t["type"] == "virman":
                    continue
                daily[_day(t["date"])][0 if d > 0 else 1] += abs(d)
        d0 = datetime.fromisoformat(date_from)
        d1 = datetime.fromisoformat(date_to)
        cashflow, cur = [], d0
        while cur <= d1 and len(cashflow) < 400:
            k = cur.strftime("%Y-%m-%d")
            cashflow.append({"date": k, "in": round(daily[k][0], 2), "out": round(daily[k][1], 2)})
            cur += timedelta(days=1)
        # 12 aylık seri
        monthly = defaultdict(lambda: {"revenue": 0.0, "expense": 0.0, "tech": 0.0})
        for t in txs:
            m = _day(t.get("date"))[:7]
            if t["type"] == "gelir":
                monthly[m]["revenue"] += t["amount"]
            elif t["type"] == "gider":
                monthly[m]["expense"] += t["amount"]
            elif t["type"] == "teknisyen_prim":
                monthly[m]["tech"] += t["amount"]
        series = []
        for i in range(11, -1, -1):
            y, mo = now.year, now.month - i
            while mo <= 0:
                mo += 12
                y -= 1
            k = f"{y}-{mo:02d}"
            v = monthly[k]
            series.append({"month": k, "revenue": round(v["revenue"], 2), "expense": round(v["expense"], 2),
                           "net": round(v["revenue"] - v["tech"] - v["expense"], 2)})
        accs = await balances()
        top = sorted(expenses, key=lambda t: -t["amount"])[:8]
        return {
            "range": {"from": date_from, "to": date_to},
            "revenue": round(revenue, 2), "job_revenue": round(job_rev, 2), "other_income": round(other_inc, 2),
            "tech_share": round(tech_share, 2), "gross_profit": round(gross, 2), "expenses": round(exp_total, 2),
            "net_profit": round(net, 2), "margin_pct": round(net / revenue * 100, 1) if revenue else 0,
            "collected_cash": round(collected, 2), "staff_cost": round(staff_cost, 2),
            "technician_receivable": round(borc - odeme, 2),
            "accounts": accs, "total_cash": round(sum(a["balance"] for a in accs if a.get("is_active", True)), 2),
            "expense_by_category": sorted([{"name": k, "amount": round(v, 2)} for k, v in by_cat.items()], key=lambda x: -x["amount"]),
            "income_by_category": sorted([{"name": k, "amount": round(v, 2)} for k, v in inc_cat.items()], key=lambda x: -x["amount"]),
            "cashflow": cashflow, "monthly": series,
            "top_expenses": [{"date": t["date"], "amount": t["amount"], "description": t.get("description", ""), "category": t.get("category", "")} for t in top],
        }

    # ------------------------------------------------------------ gelişmiş raporlar
    @api_router.get("/reports/advanced")
    async def reports_advanced(date_from: Optional[str] = None, date_to: Optional[str] = None, _: dict = Depends(require_admin)):
        now = datetime.now(TR)
        if not date_to:
            date_to = now.strftime("%Y-%m-%d")
        if not date_from:
            date_from = (now - timedelta(days=29)).strftime("%Y-%m-%d")
        d0, d1 = datetime.fromisoformat(date_from), datetime.fromisoformat(date_to)
        span = (d1 - d0).days + 1
        p_to = (d0 - timedelta(days=1)).strftime("%Y-%m-%d")
        p_from = (d0 - timedelta(days=span)).strftime("%Y-%m-%d")
        jobs_all = await db.service_jobs.find({}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(100000)
        custs = {c["id"]: c for c in await db.customers.find({}, {"_id": 0}).to_list(100000)}
        DONE = ("tamamlandi", "faturalandi")

        def in_range(j, a, b):
            return a <= _day(j.get("created_at")) <= b

        def done_in(j, a, b):
            return j.get("status") in DONE and a <= _day(j.get("completed_at") or j.get("updated_at")) <= b

        created = [j for j in jobs_all if in_range(j, date_from, date_to)]
        done = [j for j in jobs_all if done_in(j, date_from, date_to)]
        p_created = [j for j in jobs_all if in_range(j, p_from, p_to)]
        p_done = [j for j in jobs_all if done_in(j, p_from, p_to)]

        def rev(js):
            return round(sum(float(j.get("total_amount", 0) or 0) for j in js), 2)

        def kpis(cr, dn):
            hrs = []
            for j in dn:
                try:
                    if j.get("created_at") and j.get("completed_at"):
                        hrs.append((datetime.fromisoformat(j["completed_at"]) - datetime.fromisoformat(j["created_at"])).total_seconds() / 3600)
                except Exception:
                    pass
            canc = len([j for j in cr if j.get("status") == "iptal"])
            rated = [j["customer_rating"] for j in dn if j.get("customer_rating")]
            return {"created": len(cr), "completed": len(dn), "revenue": rev(dn), "avg_ticket": round(rev(dn) / len(dn), 2) if dn else 0,
                    "cancel_rate": round(canc / len(cr) * 100, 1) if cr else 0, "avg_hours": round(sum(hrs) / len(hrs), 1) if hrs else 0,
                    "repeat": len([j for j in cr if j.get("original_job_id")]), "rating": round(sum(rated) / len(rated), 2) if rated else 0,
                    "parts_revenue": round(sum(float(j.get("parts_total", 0) or 0) for j in dn), 2),
                    "labor_revenue": round(sum(float(j.get("labor_fee", 0) or 0) for j in dn), 2),
                    "completion_rate": round(len(dn) / len(cr) * 100, 1) if cr else 0}

        def group(js, keyf, with_rev=True):
            g = defaultdict(lambda: {"jobs": 0, "done": 0, "revenue": 0.0})
            for j in js:
                k = keyf(j) or "Belirtilmemiş"
                g[k]["jobs"] += 1
                if j.get("status") in DONE:
                    g[k]["done"] += 1
                    g[k]["revenue"] += float(j.get("total_amount", 0) or 0)
            return sorted([{"name": k, "jobs": v["jobs"], "done": v["done"], "revenue": round(v["revenue"], 2),
                            "avg": round(v["revenue"] / v["done"], 2) if v["done"] else 0} for k, v in g.items()], key=lambda x: (-x["revenue"], -x["jobs"]))

        # günlük seri
        series, cur = [], d0
        cr_by, dn_by = Counter(_day(j.get("created_at")) for j in created), defaultdict(float)
        dn_cnt = Counter()
        for j in done:
            k = _day(j.get("completed_at") or j.get("updated_at"))
            dn_by[k] += float(j.get("total_amount", 0) or 0)
            dn_cnt[k] += 1
        while cur <= d1 and len(series) < 400:
            k = cur.strftime("%Y-%m-%d")
            series.append({"date": k, "created": cr_by[k], "completed": dn_cnt[k], "revenue": round(dn_by[k], 2)})
            cur += timedelta(days=1)
        # hafta günü x saat yoğunluğu
        heat = [[0] * 24 for _ in range(7)]
        for j in created:
            try:
                dt = datetime.fromisoformat(j["created_at"]).astimezone(TR)
                heat[dt.weekday()][dt.hour] += 1
            except Exception:
                pass
        # parçalar / müşteriler
        parts = defaultdict(lambda: {"qty": 0.0, "amount": 0.0})
        for j in done:
            for p in j.get("parts_used") or []:
                parts[p.get("name", "?")]["qty"] += float(p.get("qty", 0) or 0)
                parts[p.get("name", "?")]["amount"] += float(p.get("total", 0) or 0)
        cust_cnt = Counter(j.get("customer_id") for j in jobs_all if j.get("customer_id"))
        cust_rev = defaultdict(float)
        for j in done:
            cust_rev[j.get("customer_id")] += float(j.get("total_amount", 0) or 0)
        top_cust = [{"name": custs.get(k, {}).get("name", "?"), "phone": custs.get(k, {}).get("phone", ""), "jobs": cust_cnt[k], "revenue": round(v, 2)}
                    for k, v in sorted(cust_rev.items(), key=lambda x: -x[1])[:10] if k]
        repeat_cust = len([k for k in {j.get("customer_id") for j in created} if k and cust_cnt[k] > 1])
        # tekrar arıza oranı (aynı müşteri 30 gün içinde yeniden)
        funnel = {
            "messages": await db.contact_messages.count_documents({"created_at": {"$gte": date_from, "$lt": (d1 + timedelta(days=1)).strftime("%Y-%m-%d")}}),
            "jobs": len(created), "completed": len([j for j in created if j.get("status") in DONE]),
        }
        return {
            "range": {"from": date_from, "to": date_to, "prev_from": p_from, "prev_to": p_to},
            "kpis": kpis(created, done), "prev_kpis": kpis(p_created, p_done),
            "series": series,
            "by_technician": group(created, lambda j: j.get("assigned_technician_name")),
            "by_channel": group(created, lambda j: j.get("source_channel")),
            "by_brand": group(created, lambda j: j.get("device_brand_name")),
            "by_device": group(created, lambda j: j.get("device_type")),
            "by_city": group(created, lambda j: (custs.get(j.get("customer_id"), {}).get("city") or "").title()),
            "by_status": group(created, lambda j: j.get("status")),
            "heatmap": heat,
            "top_parts": sorted([{"name": k, "qty": v["qty"], "amount": round(v["amount"], 2)} for k, v in parts.items()], key=lambda x: -x["amount"])[:10],
            "top_customers": top_cust, "repeat_customers": repeat_cust, "funnel": funnel,
        }


async def ensure_indexes(db):
    await db.accounts.create_index("id", unique=True)
    await db.staff.create_index("id", unique=True)
