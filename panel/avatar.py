"""Profil fotoğrafları (GÜNCELLEME 170).

- Müşteri hesabı kendi fotoğrafını (isteğe bağlı, açık rızayla) yükler/kaldırır: /public/customer/avatar
  Yönetim ve YALNIZCA ilgili işe atanmış usta görür: /avatar/job/{job_id}
- Usta fotoğrafı (users.photo_path, /api/tech/photo ile yüklenir) takip bağlantısı olan müşteriye görünür:
  /public/track/{token}/usta-foto  (jeton bilen kişi görür; tahmin edilemez)
Yalnızca ekleme yapar; mevcut koleksiyon şemaları değişmez (customer_accounts.avatar* alanları eklenir).
"""
import asyncio
import base64
import io
from datetime import datetime, timezone

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.responses import Response


def _now():
    return datetime.now(timezone.utc).isoformat()


def _digits(s):
    return "".join(ch for ch in (s or "") if ch.isdigit())


def _pk(s):
    d = _digits(s)
    return d[-10:] if len(d) >= 10 else d


def square_jpeg(raw: bytes, size: int = 256) -> bytes:
    from PIL import Image, ImageOps
    im = Image.open(io.BytesIO(raw))
    im = ImageOps.exif_transpose(im).convert("RGB")
    w, h = im.size
    m = min(w, h)
    im = im.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m)).resize((size, size))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True)
    return buf.getvalue()


def register(api_router, db, deps):
    get_current_user = deps["get_current_user"]
    get_object = deps["get_object"]
    JWT_SECRET, JWT_ALGORITHM = deps["JWT_SECRET"], deps["JWT_ALGORITHM"]

    async def cust_acc(request: Request) -> dict:
        h = request.headers.get("authorization", "")
        tok = h[7:] if h.lower().startswith("bearer ") else ""
        try:
            pl = jwt.decode(tok, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except Exception:
            raise HTTPException(401, "Giriş yapmanız gerekiyor")
        acc = await db.customer_accounts.find_one({"id": pl.get("sub")}, {"_id": 0}) if pl.get("typ") == "customer" else None
        if not acc:
            raise HTTPException(401, "Hesap bulunamadı")
        return acc

    # ------------------------------------------------------------------ müşteri fotoğrafı
    @api_router.post("/public/customer/avatar")
    async def cust_avatar_set(payload: dict, request: Request):
        acc = await cust_acc(request)
        if payload.get("consent") is not True:
            raise HTTPException(422, "Fotoğraf yüklemek için açık rıza onayı gerekir")
        s = str(payload.get("image") or "")
        if not s.startswith("data:image/") or "," not in s or len(s) > 4_500_000:
            raise HTTPException(422, "Geçersiz veya çok büyük fotoğraf (en çok ~3 MB)")
        try:
            raw = base64.b64decode(s.split(",", 1)[1], validate=False)
            jpg = await asyncio.to_thread(square_jpeg, raw)
        except Exception:
            raise HTTPException(422, "Bu dosya fotoğraf olarak açılamadı")
        url = "data:image/jpeg;base64," + base64.b64encode(jpg).decode()
        await db.customer_accounts.update_one({"id": acc["id"]}, {"$set": {"avatar": url, "avatar_at": _now(), "avatar_consent_at": _now(), "avatar_status": "pending"}})
        return {"ok": True, "avatar": url, "avatar_status": "pending"}

    @api_router.delete("/public/customer/avatar")
    async def cust_avatar_del(request: Request):
        acc = await cust_acc(request)
        await db.customer_accounts.update_one({"id": acc["id"]}, {"$unset": {"avatar": "", "avatar_at": "", "avatar_consent_at": "", "avatar_status": ""}})
        return {"ok": True}

    async def cust_avatar_by_customer(customer_id: str):
        c = await db.customers.find_one({"id": customer_id}, {"_id": 0, "phone": 1, "name": 1})
        k = _pk((c or {}).get("phone"))
        if len(k) < 10:
            return None
        a = await db.customer_accounts.find_one({"phone_key": k, "avatar": {"$exists": True}, "avatar_status": "ok"}, {"_id": 0, "avatar": 1, "avatar_consent_at": 1})
        return a.get("avatar") if a and a.get("avatar_consent_at") else None

    async def tech_photo_bytes(uid: str, public: bool = False):
        u = await db.users.find_one({"id": uid}, {"_id": 0, "photo_path": 1, "photo_status": 1}) if uid else None
        p = (u or {}).get("photo_path")
        if public and (u or {}).get("photo_status") in ("pending", "rejected"):
            return None          # yönetim onayı olmadan müşteriye gösterilmez
        if not p:
            return None
        try:
            data, _ct = await asyncio.to_thread(get_object, p)
            return data
        except Exception:
            return None

    # ------------------------------------------------------------------ yönetim / usta görünümü
    @api_router.get("/avatar/job/{job_id}")
    async def avatar_job(job_id: str, user: dict = Depends(get_current_user)):
        role = user.get("role")
        if role not in ("admin", "technician"):
            raise HTTPException(403, "Yetkisiz")
        j = await db.service_jobs.find_one({"id": job_id}, {"_id": 0, "customer_id": 1, "customer_name": 1, "assigned_technician_id": 1, "assigned_technician_name": 1})
        if not j:
            raise HTTPException(404, "İş bulunamadı")
        if role == "technician" and j.get("assigned_technician_id") != user.get("id"):
            raise HTTPException(403, "Bu iş size atanmamış")
        out = {"customer": await cust_avatar_by_customer(j.get("customer_id")), "customer_name": j.get("customer_name", ""), "tech": None,
               "tech_name": j.get("assigned_technician_name", "")}
        if role == "admin":
            b = await tech_photo_bytes(j.get("assigned_technician_id"))
            if b:
                out["tech"] = "data:image/jpeg;base64," + base64.b64encode(b).decode()
        return out

    # ------------------------------------------------------------------ müşteriye: ustanın fotoğrafı (takip jetonu ile)
    @api_router.get("/public/track/{token}/usta-foto")
    async def track_tech_photo(token: str):
        if len(token) < 12:
            raise HTTPException(404, "Yok")
        j = await db.service_jobs.find_one({"track_token": token}, {"_id": 0, "assigned_technician_id": 1})
        b = await tech_photo_bytes((j or {}).get("assigned_technician_id"), public=True)
        if not b:
            raise HTTPException(404, "Fotoğraf yok")
        mt = "image/png" if b[:4] == b"\x89PNG" else ("image/webp" if b[8:12] == b"WEBP" else "image/jpeg")
        return Response(content=b, media_type=mt, headers={"Cache-Control": "private, max-age=600"})
