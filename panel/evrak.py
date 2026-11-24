"""Sahip paneli: firma evrakları (imzalı sözleşme, vergi levhası, imza sirküleri…) — yükleme, not, indirme, silme.
Dosyalar ana veritabanında (firm_docs) saklanır; yalnız platform sahibi erişir; indirme her zaman 'attachment' ve nosniff."""
import base64
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.responses import Response

import tenant

TURLER = {"imzali_sozlesme": "İmzalı sözleşme", "vergi_levhasi": "Vergi levhası", "imza_sirkuleri": "İmza sirküleri", "kimlik": "Kimlik / yetki belgesi",
          "ticaret_sicil": "Ticaret sicil / faaliyet belgesi", "fatura": "Fatura / ödeme dekontu", "diger": "Diğer evrak"}
MAKS = 6 * 1024 * 1024
MAKS_ADET = 80
TIPLER = {"pdf": ("application/pdf", b"%PDF"), "png": ("image/png", b"\x89PNG"), "jpg": ("image/jpeg", b"\xff\xd8\xff"), "jpeg": ("image/jpeg", b"\xff\xd8\xff"),
          "webp": ("image/webp", b"RIFF"), "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"PK"),
          "xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", b"PK")}


def _t(v, n=200):
    return " ".join(str(v or "").split())[:n]


def _now():
    return datetime.now(timezone(timedelta(hours=3))).replace(tzinfo=None).isoformat(timespec="seconds")


def register(api_router, db, deps):
    adm = deps["require_admin"]

    def owner():
        if tenant.current():
            raise HTTPException(403, "Yalnızca platform sahibi")

    def acik(d):
        return {k: d.get(k) for k in ("id", "firm_id", "tur", "ad", "not", "dosya", "tip", "boyut", "at", "by")} | {"tur_ad": TURLER.get(d.get("tur"), "Diğer evrak")}

    @api_router.get("/admin/firms/{fid}/evrak")
    async def evrak_liste(fid: str, _: dict = Depends(adm)):
        owner()
        rows = await db.main().firm_docs.find({"firm_id": fid}, {"_id": 0, "data": 0}).sort("at", -1).to_list(500)
        return {"items": [acik(r) for r in rows], "turler": TURLER, "maks_mb": MAKS // (1024 * 1024)}

    @api_router.post("/admin/firms/{fid}/evrak")
    async def evrak_yukle(fid: str, payload: dict, me: dict = Depends(adm)):
        owner()
        if not await db.main().firms.find_one({"id": fid}, {"_id": 1}):
            raise HTTPException(404, "Firma bulunamadı")
        if await db.main().firm_docs.count_documents({"firm_id": fid}) >= MAKS_ADET:
            raise HTTPException(409, "Bir firmaya en fazla %d evrak eklenebilir" % MAKS_ADET)
        dosya = _t(payload.get("dosya"), 120)
        uz = dosya.rsplit(".", 1)[-1].lower() if "." in dosya else ""
        if uz not in TIPLER:
            raise HTTPException(422, "Desteklenen türler: PDF, JPG, PNG, WEBP, DOCX, XLSX")
        raw = str(payload.get("data") or "")
        if "," in raw[:80]:
            raw = raw.split(",", 1)[1]
        try:
            b = base64.b64decode(raw, validate=False)
        except Exception:                                          # noqa: BLE001
            raise HTTPException(422, "Dosya okunamadı")
        if not b:
            raise HTTPException(422, "Dosya boş")
        if len(b) > MAKS:
            raise HTTPException(413, "Dosya en fazla %d MB olabilir" % (MAKS // (1024 * 1024)))
        mime, magic = TIPLER[uz]
        if not b.startswith(magic):
            raise HTTPException(422, "Dosya içeriği uzantısıyla uyuşmuyor")
        tur = payload.get("tur") if payload.get("tur") in TURLER else "diger"
        ad = _t(payload.get("ad"), 120) or TURLER[tur]
        d = {"id": uuid.uuid4().hex[:14], "firm_id": fid, "tur": tur, "ad": ad, "not": _t(payload.get("not"), 1000), "dosya": re.sub(r"[^\w.\- ]+", "_", dosya),
             "tip": mime, "boyut": len(b), "data": base64.b64encode(b).decode(), "at": _now(), "by": me.get("email", "")}
        await db.main().firm_docs.insert_one(dict(d))
        return acik(d)

    @api_router.put("/admin/evrak/{eid}")
    async def evrak_duzenle(eid: str, payload: dict, _: dict = Depends(adm)):
        owner()
        upd = {}
        if "not" in payload:
            upd["not"] = _t(payload.get("not"), 1000)
        if "ad" in payload and _t(payload.get("ad")):
            upd["ad"] = _t(payload.get("ad"), 120)
        if payload.get("tur") in TURLER:
            upd["tur"] = payload["tur"]
        if not upd:
            raise HTTPException(400, "Değişiklik yok")
        r = await db.main().firm_docs.update_one({"id": eid}, {"$set": upd})
        if not r.matched_count:
            raise HTTPException(404, "Evrak bulunamadı")
        return {"ok": True}

    @api_router.delete("/admin/evrak/{eid}")
    async def evrak_sil(eid: str, _: dict = Depends(adm)):
        owner()
        r = await db.main().firm_docs.delete_one({"id": eid})
        if not r.deleted_count:
            raise HTTPException(404, "Evrak bulunamadı")
        return {"ok": True}

    @api_router.get("/admin/evrak/{eid}/indir")
    async def evrak_indir(eid: str, _: dict = Depends(adm)):
        owner()
        d = await db.main().firm_docs.find_one({"id": eid}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Evrak bulunamadı")
        ad = re.sub(r"[^A-Za-z0-9._-]+", "_", d.get("dosya") or "evrak") or "evrak"
        return Response(base64.b64decode(d["data"]), media_type=d.get("tip") or "application/octet-stream",
                        headers={"Content-Disposition": 'attachment; filename="%s"' % ad, "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"})
