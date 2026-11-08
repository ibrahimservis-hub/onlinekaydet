"""Ops3: müşteri memnuniyet raporu, usta borç vade takibi, günün iş haritası verisi. Hepsi OKUMA ağırlıklı, ek koleksiyon: tech_due."""
from datetime import datetime, timezone, timedelta

from fastapi import Depends, HTTPException

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                     # pragma: no cover
    TR = timezone(timedelta(hours=3))

CLOSED = ["tamamlandi", "faturalandi", "iptal"]


def _rating(j):
    r = j.get("customer_rating") or (j.get("survey") or {}).get("rating") or 0
    try:
        return int(r)
    except Exception:                                 # noqa: BLE001
        return 0


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    @api_router.get("/reports/satisfaction")
    async def satisfaction(days: int = 90, _: dict = Depends(require_admin)):
        days = max(1, min(int(days or 90), 730))
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        jobs = await db.service_jobs.find({"status": {"$in": ["tamamlandi", "faturalandi"]}, "completed_at": {"$gte": since}},
                                          {"_id": 0, "id": 1, "job_number": 1, "customer_name": 1, "customer_phone": 1, "assigned_technician_id": 1, "assigned_technician_name": 1,
                                           "device_brand_name": 1, "device_type": 1, "customer_rating": 1, "survey": 1, "completed_at": 1}).to_list(50000)
        dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        by_t, by_b, by_d, low = {}, {}, {}, []
        done, rated = len(jobs), 0
        for j in jobs:
            r = _rating(j)
            if not 1 <= r <= 5:
                continue
            rated += 1
            dist[r] += 1
            for store, key in ((by_t, j.get("assigned_technician_name") or "—"), (by_b, j.get("device_brand_name") or "—"), (by_d, j.get("device_type") or "—")):
                a = store.setdefault(key, [0, 0]); a[0] += r; a[1] += 1
            if r <= 2:
                low.append({"id": j["id"], "job_number": j.get("job_number", ""), "customer": j.get("customer_name", ""), "phone": j.get("customer_phone", ""),
                            "tech": j.get("assigned_technician_name", ""), "rating": r, "at": (j.get("completed_at") or "")[:10],
                            "comment": ((j.get("survey") or {}).get("comment") or "")[:200]})
        mk = lambda d: sorted([{"name": k, "avg": round(v[0] / v[1], 2), "n": v[1]} for k, v in d.items()], key=lambda x: (-x["avg"], -x["n"]))
        low.sort(key=lambda x: x["at"], reverse=True)
        return {"days": days, "done": done, "rated": rated, "avg": round(sum(k * v for k, v in dist.items()) / rated, 2) if rated else 0,
                "response_rate": round(100 * rated / done) if done else 0, "dist": dist, "techs": mk(by_t), "brands": mk(by_b), "devices": mk(by_d), "low": low[:50]}

    @api_router.get("/tech-due")
    async def tech_due(_: dict = Depends(require_admin)):
        res = await db.cash_transactions.aggregate([
            {"$match": {"type": {"$in": ["teknisyen_borc", "teknisyen_odeme"]}, "technician_id": {"$nin": ["", None]}}},
            {"$group": {"_id": {"t": "$technician_id", "y": "$type"}, "s": {"$sum": "$amount"}}}]).to_list(5000)
        bal = {}
        for r in res:
            k = r["_id"]["t"]
            bal[k] = bal.get(k, 0) + (r["s"] if r["_id"]["y"] == "teknisyen_borc" else -r["s"])
        dues = {d["technician_id"]: d async for d in db.tech_due.find({}, {"_id": 0})}
        users = {u["id"]: u async for u in db.users.find({"role": "technician"}, {"_id": 0, "id": 1, "name": 1, "phone": 1})}
        today = datetime.now(TR).strftime("%Y-%m-%d")
        out = []
        for tid, b in bal.items():
            if b <= 0.5 and tid not in dues:
                continue
            u = users.get(tid) or {}
            d = dues.get(tid) or {}
            due = d.get("due_date") or ""
            out.append({"technician_id": tid, "name": u.get("name", "—"), "phone": u.get("phone", ""), "balance": round(b, 2), "due_date": due, "note": d.get("note", ""),
                        "overdue": bool(due and due < today and b > 0.5), "days_left": (datetime.strptime(due, "%Y-%m-%d").date() - datetime.now(TR).date()).days if due else None})
        out.sort(key=lambda x: (not x["overdue"], x["due_date"] or "9999", -x["balance"]))
        return {"today": today, "items": out, "total": round(sum(x["balance"] for x in out if x["balance"] > 0), 2), "overdue_n": sum(1 for x in out if x["overdue"])}

    @api_router.put("/tech-due/{tid}")
    async def tech_due_set(tid: str, payload: dict, _: dict = Depends(require_admin)):
        due = (payload.get("due_date") or "").strip()
        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Tarih biçimi YYYY-AA-GG olmalı")
        await db.tech_due.update_one({"technician_id": tid}, {"$set": {"technician_id": tid, "due_date": due, "note": (payload.get("note") or "")[:300],
                                                                      "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
        return {"ok": True}

    @api_router.get("/ops/day-map")
    async def day_map(date: str = "", _: dict = Depends(require_admin)):
        day = date or datetime.now(TR).strftime("%Y-%m-%d")
        rows = await db.service_jobs.find({"status": {"$nin": CLOSED}, "scheduled_at": {"$regex": "^" + day}},
                                          {"_id": 0, "id": 1, "job_number": 1, "scheduled_at": 1, "customer_name": 1, "customer_address": 1, "customer_district": 1, "customer_city": 1,
                                           "assigned_technician_id": 1, "assigned_technician_name": 1, "device_type": 1, "device_brand_name": 1, "status": 1}).sort("scheduled_at", 1).to_list(500)
        return {"date": day, "items": rows}


async def ensure_indexes(db):
    await db.tech_due.create_index("technician_id", unique=True)
