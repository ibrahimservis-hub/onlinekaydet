"""Önce/sonra fotoğrafları müşteriye gösterme + yönetim onayı (GÜNCELLEME 171).

- Ustanın iş fotoğrafları (photos_before / photos_after) yalnızca İŞ TAMAMLANDIKTAN sonra ve yönetimin onay/gizleme penceresi
  (varsayılan 60 dk) geçtikten sonra, takip bağlantısı olan müşteriye görünür. Yönetim bir fotoğrafı "gizle" derse hiç görünmez;
  "Elle onay" modunda yalnızca yönetimin onayladıkları görünür.
- Müşteriye ASLA veritabanındaki adres verilmez (içinde oturum jetonu olabilir); görüntü sunucudan jetonsuz yeniden sunulur.
- Usta profil fotoğrafı yeni yüklendiğinde 'bekliyor' olur; yönetim onaylayana kadar müşteriye görünmez (eski fotoğraflar onaylı sayılır).
Yalnızca ekleme yapar; iş kaydına 'photo_review' alanı eklenir.
"""
import asyncio
import hashlib
import io
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import unquote

from fastapi import Depends, HTTPException
from fastapi.responses import Response

DONE = ("tamamlandi", "faturalandi")


def _now():
    return datetime.now(timezone.utc).isoformat()


def path_of(u: str) -> str:
    u = str(u or "")
    m = re.search(r"/api/files/([^?#]+)", u)
    if m:
        return unquote(m.group(1))
    if u.startswith(("http://", "https://", "data:")):
        return ""
    return u.lstrip("/")


def pkey(path: str) -> str:
    return hashlib.sha1(path.encode()).hexdigest()[:12]


def _parse(ts):
    try:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


import tenant


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]
    get_object = deps["get_object"]

    async def cfg():
        c = await db.app_settings.find_one({"_id": "foto"}, {"_id": 0}) or {}
        return {"manual": bool(c.get("manual", True)), "delay_min": max(0, min(1440, int(c.get("delay_min", 60) or 0)))}

    def state_of(job, path, c):
        """ok | hide | bekliyor (pencere/onay bekliyor) | gorunur (pencere bitti, otomatik görünür)"""
        rv = (job.get("photo_review") or {}).get(pkey(path))
        if rv == "hide":
            return "hide"
        if rv == "ok":
            return "ok"
        if c["manual"]:
            return "bekliyor"
        done_at = _parse(job.get("completed_at") or job.get("updated_at"))
        if job.get("status") in DONE and done_at and datetime.now(timezone.utc) >= done_at + timedelta(minutes=c["delay_min"]):
            return "gorunur"
        return "bekliyor"

    def photos(job):
        out = []
        for kind, key in (("before", "photos_before"), ("after", "photos_after")):
            for i, u in enumerate(job.get(key) or []):
                p = path_of(u)
                if p:
                    out.append({"kind": kind, "i": i, "path": p})
        return out

    # ------------------------------------------------------------------ müşteri (takip jetonu)
    @api_router.get("/public/track/{token}/fotolar")
    async def track_photos(token: str):
        if len(token) < 12:
            raise HTTPException(404, "Yok")
        job = await db.service_jobs.find_one({"track_token": token}, {"_id": 0, "photos_before": 1, "photos_after": 1, "photo_review": 1, "status": 1, "completed_at": 1, "updated_at": 1})
        if not job or job.get("status") not in DONE:
            return {"before": [], "after": []}
        c = await cfg()
        res = {"before": [], "after": []}
        for ph in photos(job):
            if state_of(job, ph["path"], c) in ("ok", "gorunur"):
                res[ph["kind"]].append(ph["i"])
        return res

    @api_router.get("/public/track/{token}/foto/{kind}/{i}")
    async def track_photo(token: str, kind: str, i: int, t: int = 0):
        if len(token) < 12 or kind not in ("before", "after") or i < 0 or i > 60:
            raise HTTPException(404, "Yok")
        job = await db.service_jobs.find_one({"track_token": token}, {"_id": 0, "photos_before": 1, "photos_after": 1, "photo_review": 1, "status": 1, "completed_at": 1, "updated_at": 1})
        if not job or job.get("status") not in DONE:
            raise HTTPException(404, "Yok")
        lst = job.get("photos_before" if kind == "before" else "photos_after") or []
        if i >= len(lst):
            raise HTTPException(404, "Yok")
        p = path_of(lst[i])
        if not p or state_of(job, p, await cfg()) not in ("ok", "gorunur"):
            raise HTTPException(404, "Yok")
        try:
            data, ct = await asyncio.to_thread(get_object, p)
        except Exception:
            raise HTTPException(404, "Yok")
        if t:
            try:
                from PIL import Image, ImageOps
                im = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
                im.thumbnail((420, 420))
                b = io.BytesIO()
                im.save(b, "JPEG", quality=72)
                data, ct = b.getvalue(), "image/jpeg"
            except Exception:
                pass
        return Response(content=data, media_type=ct or "image/jpeg", headers={"Cache-Control": "private, max-age=600"})

    # ------------------------------------------------------------------ yönetim
    @api_router.get("/foto/ayar")
    async def foto_ayar_get(_: dict = Depends(require_admin)):
        return await cfg()

    @api_router.put("/foto/ayar")
    async def foto_ayar_put(payload: dict, _: dict = Depends(require_admin)):
        upd = {}
        if "manual" in payload:
            upd["manual"] = bool(payload["manual"])
        if "delay_min" in payload:
            try:
                upd["delay_min"] = max(0, min(1440, int(payload["delay_min"])))
            except (TypeError, ValueError):
                raise HTTPException(422, "Süre sayı olmalı")
        if upd:
            await db.app_settings.update_one({"_id": "foto"}, {"$set": upd}, upsert=True)
        return await cfg()

    @api_router.get("/foto/job/{job_id}")
    async def foto_job(job_id: str, _: dict = Depends(require_admin)):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0, "photos_before": 1, "photos_after": 1, "photo_review": 1, "status": 1, "completed_at": 1, "updated_at": 1})
        if not job:
            raise HTTPException(404, "İş bulunamadı")
        c = await cfg()
        return {"manual": c["manual"], "delay_min": c["delay_min"], "done": job.get("status") in DONE,
                "items": [{**ph, "url": "/api/files/" + ph["path"], "state": state_of(job, ph["path"], c)} for ph in photos(job)]}

    @api_router.put("/foto/job/{job_id}")
    async def foto_job_set(job_id: str, payload: dict, _: dict = Depends(require_admin)):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0, "photos_before": 1, "photos_after": 1, "photo_review": 1})
        if not job:
            raise HTTPException(404, "İş bulunamadı")
        st = payload.get("state")
        if st not in ("ok", "hide", "reset"):
            raise HTTPException(422, "Geçersiz durum")
        allp = photos(job)
        if payload.get("kind") == "all":
            targets = [ph["path"] for ph in allp]
        else:
            targets = [ph["path"] for ph in allp if ph["kind"] == payload.get("kind") and ph["i"] == payload.get("i")]
        if not targets:
            raise HTTPException(404, "Fotoğraf bulunamadı")
        rev = dict(job.get("photo_review") or {})
        for p in targets:
            if st == "reset":
                rev.pop(pkey(p), None)
            else:
                rev[pkey(p)] = st
        await db.service_jobs.update_one({"id": job_id}, {"$set": {"photo_review": rev}})
        return {"ok": True}

    @api_router.get("/foto/bekleyen")
    async def foto_bekleyen(_: dict = Depends(require_admin)):
        c = await cfg()
        ust = await db.users.find({"role": "technician", "photo_status": "pending", "photo_path": {"$exists": True, "$ne": ""}},
                                  {"_id": 0, "id": 1, "name": 1, "photo_path": 1, "photo_at": 1}).to_list(200)
        since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        rows = await db.service_jobs.find({"status": {"$in": list(DONE)}, "completed_at": {"$gte": since}},
                                          {"_id": 0, "id": 1, "job_number": 1, "customer_name": 1, "assigned_technician_name": 1, "photos_before": 1,
                                           "photos_after": 1, "photo_review": 1, "completed_at": 1, "status": 1, "updated_at": 1}).to_list(5000)
        isler = []
        for j in rows:
            ph = photos(j)
            if not ph:
                continue
            pend = [p for p in ph if state_of(j, p["path"], c) == "bekliyor"]
            if pend:
                isler.append({"job_id": j["id"], "job_number": j.get("job_number", ""), "customer": j.get("customer_name", ""),
                              "tech": j.get("assigned_technician_name", ""), "count": len(pend), "completed_at": j.get("completed_at", "")})
        isler.sort(key=lambda x: x["completed_at"], reverse=True)
        must = await db.customer_accounts.find({"avatar": {"$exists": True, "$ne": ""}, "avatar_status": {"$ne": "ok"}},
                                               {"_id": 0, "id": 1, "name": 1, "phone": 1, "avatar": 1, "avatar_at": 1}).to_list(200)
        yor = await db.reviews.find({"status": "beklemede", "comment": {"$nin": ["", None]}},
                                    {"_id": 0, "id": 1, "name": 1, "rating": 1, "comment": 1, "job_number": 1, "created_at": 1, "brand": 1}).sort("created_at", -1).to_list(200)
        total = len(ust) + len(must) + len(yor) + len(isler)
        return {"manual": c["manual"], "delay_min": c["delay_min"], "ustalar": ust, "musteriler": must, "yorumlar": yor, "isler": isler[:100], "total": total}

    @api_router.get("/foto/sayi")
    async def foto_sayi(_: dict = Depends(require_admin)):
        """Menü rozeti için yalnızca onay bekleyen toplam sayı."""
        return {"n": (await foto_bekleyen(_))["total"]}

    @api_router.post("/foto/musteri/{acc_id}")
    async def foto_musteri(acc_id: str, payload: dict, _: dict = Depends(require_admin)):
        a = await db.customer_accounts.find_one({"id": acc_id}, {"_id": 0, "id": 1})
        if not a:
            raise HTTPException(404, "Hesap bulunamadı")
        st = payload.get("state")
        if st == "ok":
            await db.customer_accounts.update_one({"id": acc_id}, {"$set": {"avatar_status": "ok", "avatar_review_at": _now()}})
        elif st == "red":
            await db.customer_accounts.update_one({"id": acc_id}, {"$unset": {"avatar": "", "avatar_at": "", "avatar_consent_at": "", "avatar_status": ""}})
        else:
            raise HTTPException(422, "Geçersiz durum")
        return {"ok": True}

    @api_router.post("/foto/usta/{tech_id}")
    async def foto_usta(tech_id: str, payload: dict, _: dict = Depends(require_admin)):
        u = await db.users.find_one({"id": tech_id, "role": "technician"}, {"_id": 0, "id": 1})
        if not u:
            raise HTTPException(404, "Usta bulunamadı")
        st = payload.get("state")
        if st == "ok":
            await db.users.update_one({"id": tech_id}, {"$set": {"photo_status": "ok", "photo_review_at": _now()}})
        elif st == "red":
            await db.users.update_one({"id": tech_id}, {"$set": {"photo_status": "rejected", "photo_review_at": _now()}, "$unset": {"photo_path": "", "photo_at": ""}})
        else:
            raise HTTPException(422, "Geçersiz durum")
        return {"ok": True}

    @api_router.get("/foto/pdf/{job_id}")
    async def foto_pdf(job_id: str, user: dict = Depends(get_current_user)):
        """Servis fişi PDF'ine konacak küçük fotoğraflar. Yönetim: gizlenmemiş olanlar. Usta: yalnızca müşteriye zaten görünür (onaylı) olanlar."""
        role = user.get("role")
        if role not in ("admin", "technician"):
            raise HTTPException(403, "Yetkisiz")
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0, "photos_before": 1, "photos_after": 1, "photo_review": 1, "status": 1, "completed_at": 1, "updated_at": 1, "assigned_technician_id": 1})
        out = {"before": [], "after": []}
        if not job or (role == "technician" and job.get("assigned_technician_id") != user.get("id")):
            return out
        c = await cfg()
        for ph in photos(job):
            st = state_of(job, ph["path"], c)
            if st == "hide" or (role == "technician" and not tenant.current() and st not in ("ok", "gorunur")):   # firma kendi fotoğraflarının sahibi: yönetici onayı beklenmez
                continue
            out[ph["kind"]].append("/api/files/" + ph["path"])
        return out
