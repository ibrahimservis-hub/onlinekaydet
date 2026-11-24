# -*- coding: utf-8 -*-
"""Referanslar: ana sayfada kayan logo şeridi (platform düzeyi, ana veritabanı).

Logo dosyası base64 olarak kayıtta tutulur (en çok 300 KB; png, jpg, webp, svg, gif).
Genel uçlar yalnız yayındaki logoları listeler ve görseli önbellekli sunar."""
import base64
import re
import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from fastapi.responses import Response

IZIN = {"image/png", "image/jpeg", "image/webp", "image/svg+xml", "image/gif"}
MAX_BAYT = 300 * 1024
_DATA = re.compile(r"^data:([\w.+/-]+);base64,([A-Za-z0-9+/=\s]+)$")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _link(v):
    v = str(v or "").strip()[:200]
    return v if (not v or re.match(r"^https?://", v)) else ""


def _gorsel(v):
    m = _DATA.match(str(v or "").strip())
    if not m or m.group(1) not in IZIN:
        raise HTTPException(422, "Logo png, jpg, webp, svg ya da gif olmalı")
    try:
        ham = base64.b64decode(m.group(2), validate=False)
    except Exception:
        raise HTTPException(422, "Logo dosyası okunamadı")
    if not ham or len(ham) > MAX_BAYT:
        raise HTTPException(422, "Logo en çok 300 KB olabilir")
    if m.group(1) == "image/svg+xml" and re.search(rb"<script|onload\s*=|onerror\s*=|javascript:", ham, re.I):
        raise HTTPException(422, "Bu SVG dosyası güvenli değil")
    return m.group(1), base64.b64encode(ham).decode()


VARSAYILAN_BASLIK = "Bize güvenen markalar"


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    def main():
        return db.main()

    def need_main():
        from tenant import current
        if current():
            raise HTTPException(403, "Bu işlem yalnız ana yönetim içindir")

    async def baslik():
        d = await main().referans_ayar.find_one({"id": "ayar"}, {"_id": 0, "baslik": 1})
        return VARSAYILAN_BASLIK if d is None or "baslik" not in d else str(d["baslik"])

    @api_router.get("/public/referanslar")
    async def pub_list():
        rows = await main().referans_logo.find({"active": True}, {"_id": 0, "id": 1, "name": 1, "link": 1, "v": 1}).sort("order", 1).to_list(60)
        return {"baslik": await baslik(), "logolar": [{"id": r["id"], "name": r.get("name", ""), "link": r.get("link", ""), "src": "/api/public/referans/%s/logo?v=%s" % (r["id"], r.get("v", 1))} for r in rows]}

    @api_router.get("/public/referans/{rid}/logo")
    async def pub_logo(rid: str):
        r = await main().referans_logo.find_one({"id": rid, "active": True}, {"_id": 0, "mime": 1, "data": 1})
        if not r:
            raise HTTPException(404, "Logo yok")
        return Response(base64.b64decode(r["data"]), media_type=r["mime"], headers={
            "Cache-Control": "public, max-age=86400", "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox"})

    @api_router.get("/admin/referans")
    async def adm_list(_: dict = Depends(require_admin)):
        need_main()
        rows = await main().referans_logo.find({}, {"_id": 0, "data": 0}).sort("order", 1).to_list(200)
        for r in rows:
            r["src"] = "/api/public/referans/%s/logo?v=%s" % (r["id"], r.get("v", 1))
        return {"logolar": rows, "baslik": await baslik(), "varsayilan": VARSAYILAN_BASLIK}

    @api_router.put("/admin/referans-baslik")
    async def adm_baslik(payload: dict, _: dict = Depends(require_admin)):
        need_main()
        b = str(payload.get("baslik", "")).strip()[:80]
        await main().referans_ayar.update_one({"id": "ayar"}, {"$set": {"baslik": b}}, upsert=True)
        return {"ok": True, "baslik": b}

    @api_router.get("/admin/referans/{rid}/logo")
    async def adm_logo(rid: str, _: dict = Depends(require_admin)):
        need_main()
        r = await main().referans_logo.find_one({"id": rid}, {"_id": 0, "mime": 1, "data": 1})
        if not r:
            raise HTTPException(404, "Logo yok")
        return Response(base64.b64decode(r["data"]), media_type=r["mime"], headers={
            "X-Content-Type-Options": "nosniff", "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox"})

    @api_router.post("/admin/referans")
    async def adm_add(payload: dict, _: dict = Depends(require_admin)):
        need_main()
        ad = str(payload.get("name", "")).strip()[:80]
        if len(ad) < 2:
            raise HTTPException(422, "Marka adı gerekli")
        mime, data = _gorsel(payload.get("image"))
        n = await main().referans_logo.count_documents({})
        if n >= 60:
            raise HTTPException(422, "En çok 60 logo eklenebilir")
        d = {"id": str(uuid.uuid4()), "name": ad, "link": _link(payload.get("link")), "mime": mime, "data": data, "v": 1,
             "active": True, "order": n, "created_at": _now()}
        await main().referans_logo.insert_one(dict(d))
        return {"ok": True, "id": d["id"]}

    @api_router.put("/admin/referans/{rid}")
    async def adm_edit(rid: str, payload: dict, _: dict = Depends(require_admin)):
        need_main()
        cur = await main().referans_logo.find_one({"id": rid}, {"_id": 0, "v": 1})
        if not cur:
            raise HTTPException(404, "Logo bulunamadı")
        sets = {}
        if "name" in payload:
            ad = str(payload["name"]).strip()[:80]
            if len(ad) < 2:
                raise HTTPException(422, "Marka adı gerekli")
            sets["name"] = ad
        if "link" in payload:
            sets["link"] = _link(payload["link"])
        if "active" in payload:
            sets["active"] = bool(payload["active"])
        if "order" in payload:
            try:
                sets["order"] = int(payload["order"])
            except (TypeError, ValueError):
                pass
        if payload.get("image"):
            sets["mime"], sets["data"] = _gorsel(payload["image"])
            sets["v"] = int(cur.get("v", 1)) + 1
        if not sets:
            raise HTTPException(422, "Değişiklik yok")
        await main().referans_logo.update_one({"id": rid}, {"$set": sets})
        return {"ok": True}

    @api_router.post("/admin/referans/{rid}/tasi")
    async def adm_move(rid: str, payload: dict, _: dict = Depends(require_admin)):
        need_main()
        yon = -1 if payload.get("yon") == "yukari" else 1
        rows = await main().referans_logo.find({}, {"_id": 0, "id": 1}).sort("order", 1).to_list(200)
        ids = [r["id"] for r in rows]
        if rid not in ids:
            raise HTTPException(404, "Logo bulunamadı")
        i = ids.index(rid)
        j = i + yon
        if 0 <= j < len(ids):
            ids[i], ids[j] = ids[j], ids[i]
        for k, x in enumerate(ids):
            await main().referans_logo.update_one({"id": x}, {"$set": {"order": k}})
        return {"ok": True}

    @api_router.delete("/admin/referans/{rid}")
    async def adm_del(rid: str, _: dict = Depends(require_admin)):
        need_main()
        await main().referans_logo.delete_one({"id": rid})
        return {"ok": True}
