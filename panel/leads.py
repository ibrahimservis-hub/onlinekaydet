"""Satış sayfalarından gelen talepler (platform düzeyi, ana veritabanı)."""
import re, time, uuid
from datetime import datetime, timezone
from fastapi import HTTPException, Request, Depends

_RATE: dict = {}
STATUSES = ("yeni", "arandi", "demo", "kazanildi", "olumsuz")


def _digits(s):
    return re.sub(r"\D", "", str(s or ""))


def _norm_phone(s):
    d = _digits(s)
    if d.startswith("90") and len(d) == 12:
        d = d[2:]
    if d.startswith("0"):
        d = d[1:]
    return d if len(d) == 10 and d.startswith("5") else ""


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    def main():
        return db.main()

    def need_main():
        from tenant import current
        if current():
            raise HTTPException(403, "Bu işlem yalnız ana yönetim içindir")

    @api_router.post("/public/lead")
    async def lead(payload: dict, request: Request):
        # bot tuzağı: görünmeyen alan doluysa sessizce başarılı say
        if str(payload.get("website") or "").strip():
            return {"ok": True}
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
        now = time.time()
        hist = [t for t in _RATE.get(ip, []) if now - t < 3600]
        if len(hist) >= 6:
            raise HTTPException(429, "Çok fazla deneme, biraz sonra tekrar deneyin")
        name = " ".join(str(payload.get("name") or "").split())[:80]
        phone = _norm_phone(payload.get("phone"))
        if len(name) < 2:
            raise HTTPException(422, "Lütfen adınızı yazın")
        if not phone:
            raise HTTPException(422, "Telefon numarası geçersiz (05xx xxx xx xx)")
        hist.append(now)
        _RATE[ip] = hist
        since = datetime.fromtimestamp(now - 600, timezone.utc).isoformat()
        dup = await main().leads.find_one({"phone": phone, "created_at": {"$gte": since}})
        if dup:
            return {"ok": True, "id": dup["id"]}
        src = payload.get("src") if isinstance(payload.get("src"), dict) else {}
        extra = payload.get("extra") if isinstance(payload.get("extra"), dict) else {}
        doc = {
            "id": str(uuid.uuid4()), "name": name, "phone": phone,
            "firm": str(payload.get("firm") or "")[:100], "sector": str(payload.get("sector") or "")[:40],
            "city": str(payload.get("city") or "")[:60], "form": str(payload.get("form") or "")[:40],
            "src": {k: str(src.get(k) or "")[:120] for k in ("utm_source", "utm_medium", "utm_campaign", "ref", "page")},
            "extra": {str(k)[:30]: (v if isinstance(v, (int, float, bool)) else str(v)[:(1000 if k == "mesaj" else 120)]) for k, v in list(extra.items())[:12]},
            "status": "yeni", "note": "", "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await main().leads.insert_one(doc)
        return {"ok": True, "id": doc["id"]}

    @api_router.get("/admin/leads")
    async def leads_list(status: str = "", _: dict = Depends(require_admin)):
        need_main()
        q = {"status": status} if status in STATUSES else {}
        items = await main().leads.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
        counts = {s: await main().leads.count_documents({"status": s}) for s in STATUSES}
        return {"leads": items, "counts": counts}

    @api_router.put("/admin/leads/{lead_id}")
    async def leads_update(lead_id: str, payload: dict, _: dict = Depends(require_admin)):
        need_main()
        sets = {}
        if "status" in payload:
            if payload["status"] not in STATUSES:
                raise HTTPException(422, "Durum geçersiz")
            sets["status"] = payload["status"]
        if "note" in payload:
            sets["note"] = str(payload["note"])[:500]
        if not sets:
            raise HTTPException(422, "Değişiklik yok")
        r = await main().leads.update_one({"id": lead_id}, {"$set": sets})
        if not r.matched_count:
            raise HTTPException(404, "Talep bulunamadı")
        return {"ok": True}
