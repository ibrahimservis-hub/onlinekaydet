"""Site Stüdyosu: servisplus.net.tr içeriğini panelden yönetme (CMS) + medya kütüphanesi.

Mimari: Panelde taslak (draft) düzenlenir -> "Yayınla" ile canlı sürüme alınır ->
site, herkese açık /api/public/site-content ucundan canlı sürümü okuyup sayfaya uygular
(servisplus-automation.js içindeki CMS uygulayıcı). Her yayın bir sürüm olarak saklanır (geri alınabilir).
"""
import io
import re
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, UploadFile, File, Request, Response

MAX_UPLOAD = 8 * 1024 * 1024
ALLOWED_IMG = {"image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml", "image/x-icon", "image/avif"}

DEFAULT_STATE = {
    "site_url": "https://servisplus.net.tr",
    "theme": {},            # {"primary": "#1155cc", ...}
    "global": {},           # {"phone":..., "phone_display":..., "email":..., "whatsapp":..., "address":..., "logo_url":..., "favicon_url":...}
    "footer": {},           # {"bg":..., "text":..., "title":..., "copyright":..., "note":...}
    "hero": {"enabled": False, "mode": "single", "slides": [], "autoplay": True, "interval": 5, "height": 440, "overlay": 0.35},
    "ops": [],
    "custom": {"css": "", "head_html": "", "body_end_html": ""},
    "banner": {"enabled": False, "text": "", "link": "", "bg": "#b91c1c", "color": "#ffffff", "start_at": "", "end_at": ""},   # üst duyuru şeridi (isteğe bağlı tarih aralığı)
    "nav": {"enabled": False, "header": [], "footer": []},   # üst menü: [{label, href}]; footer: [{title, links:[{label, href}]}]
    "pages": [],            # yeni sayfalar: [{id, slug, title, description, og_image, noindex, status, blocks:[{type, ...}]}]
}

THEME_VARS = {
    "primary": "--sp-blue", "primary_dark": "--sp-blue-dark", "navy": "--sp-navy", "muted": "--sp-muted",
    "border": "--sp-border", "bg": "--sp-bg", "card": "--sp-card", "brand": "--sp-brand-color",
}
FOOTER_VARS = {"bg": "--sp-footer-bg", "text": "--sp-footer-text", "title": "--sp-footer-title"}


RESERVED_SLUGS = {"api", "static", "images", "admin", "servis", "il", "blog", "hakkimizda", "iletisim", "kvkk"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _id():
    return str(uuid.uuid4())


def _clean_state(st: dict) -> dict:
    out = {k: (v.copy() if isinstance(v, dict) else list(v) if isinstance(v, list) else v) for k, v in DEFAULT_STATE.items()}
    for k in DEFAULT_STATE:
        if k in st and st[k] is not None:
            if isinstance(DEFAULT_STATE[k], dict) and isinstance(st[k], dict):
                out[k] = {**DEFAULT_STATE[k], **st[k]} if k in ("hero", "custom", "banner", "nav") else dict(st[k])
            elif isinstance(DEFAULT_STATE[k], list) and isinstance(st[k], list):
                out[k] = st[k]
            elif isinstance(DEFAULT_STATE[k], str):
                out[k] = str(st[k])
    ops = []
    for o in out["ops"]:
        if isinstance(o, dict) and o.get("type"):
            o["id"] = o.get("id") or _id()
            o["scope"] = o.get("scope") or "page"
            ops.append(o)
    out["ops"] = ops
    pages, seen = [], set()
    for p in out["pages"]:
        if not isinstance(p, dict):
            continue
        slug = re.sub(r"[^a-z0-9\-/]", "", (p.get("slug") or "").lower().replace(" ", "-").strip("/"))
        if not slug or slug in seen or slug.split("/")[0] in RESERVED_SLUGS:
            continue
        seen.add(slug)
        p["slug"], p["id"] = slug, p.get("id") or _id()
        p["status"] = p.get("status") if p.get("status") in ("published", "draft") else "published"
        p["blocks"] = [b for b in (p.get("blocks") or []) if isinstance(b, dict) and b.get("type")]
        pages.append(p)
    out["pages"] = pages
    return out


def _scope_match(scope: str, path: str, op_path: str) -> bool:
    if scope == "global":
        return True
    if scope == "page":
        return _norm_path(op_path) == _norm_path(path)
    if scope == "prefix":
        return _norm_path(path).startswith(_norm_path(op_path))
    return False


def _norm_path(p: str) -> str:
    p = (p or "/").split("?")[0].split("#")[0]
    if not p.startswith("/"):
        p = "/" + p
    if not p.endswith("/") and "." not in p.rsplit("/", 1)[-1]:
        p += "/"
    return p.replace("/index.html", "/")


def banner_active(b: dict, now: Optional[str] = None) -> bool:
    if not b or not b.get("enabled"):
        return False
    now = now or _now()
    if b.get("start_at") and now < b["start_at"]:
        return False
    if b.get("end_at") and now > b["end_at"]:
        return False
    return True


def public_view(live: dict, path: str) -> dict:
    st = live["state"]
    ops = [o for o in st["ops"] if _scope_match(o.get("scope", "page"), path, o.get("path", "/"))]
    home = _norm_path(path) == "/"
    return {
        "version": live.get("version", 0), "theme": st["theme"], "global": st["global"], "footer": st["footer"],
        "hero": st["hero"] if home and st["hero"].get("enabled") else None,
        "ops": ops, "custom": st["custom"], "banner": st["banner"] if banner_active(st["banner"]) else None,
        "nav": st["nav"] if st["nav"].get("enabled") else None,
    }


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    async def get_live():
        d = await db.site_content.find_one({"_id": "live"}, {"_id": 0})
        if not d:
            d = {"version": 0, "state": _clean_state({}), "updated_at": _now()}
        return d

    async def get_draft():
        d = await db.site_content.find_one({"_id": "draft"}, {"_id": 0})
        if d:
            return d
        live = await get_live()
        return {"state": live["state"], "base_version": live.get("version", 0), "updated_at": _now(), "dirty": False}

    # ----------------------------------------------------------------- PUBLIC
    @api_router.get("/public/site-content")
    async def public_site_content(request: Request, response: Response, path: str = "/"):
        live = await get_live()
        etag = f'W/"{live.get("version", 0)}-{hashlib.md5(path.encode()).hexdigest()[:6]}"'
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers={"ETag": etag, "Cache-Control": "public, max-age=60"})
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=60"
        return public_view(live, path)

    @api_router.get("/public/media/{mid}")
    async def public_media(mid: str, thumb: int = 0):
        m = await db.media.find_one({"id": mid.split(".")[0]}, {"_id": 0})
        if not m:
            raise HTTPException(status_code=404, detail="Dosya yok")
        data = m["thumb"] if thumb and m.get("thumb") else m["data"]
        ctype = "image/webp" if thumb and m.get("thumb") else m["content_type"]
        return Response(content=bytes(data), media_type=ctype, headers={"Cache-Control": "public, max-age=31536000, immutable", "Access-Control-Allow-Origin": "*"})

    # ----------------------------------------------------------------- ADMIN: taslak / yayın
    @api_router.get("/studio/state")
    async def studio_state(_: dict = Depends(require_admin)):
        live = await get_live()
        draft = await get_draft()
        return {"live_version": live.get("version", 0), "draft": draft["state"], "dirty": draft.get("dirty", False),
                "base_version": draft.get("base_version", 0), "updated_at": draft.get("updated_at"), "published_at": live.get("updated_at"),
                "scheduled_at": draft.get("scheduled_at", ""), "updated_by": draft.get("updated_by", "")}

    @api_router.put("/studio/draft")
    async def studio_put_draft(payload: dict, user: dict = Depends(require_admin)):
        st = _clean_state(payload.get("state") or {})
        live = await get_live()
        cur = await db.site_content.find_one({"_id": "draft"}, {"_id": 0, "updated_at": 1, "updated_by": 1})
        # çift düzenleme koruması: istemcinin gördüğü sürüm başkası tarafından değiştirildiyse uyar
        seen = payload.get("seen_updated_at")
        if cur and seen is not None and not payload.get("force") and cur.get("updated_at") != seen and cur.get("updated_by") != user["name"]:
            raise HTTPException(status_code=409, detail=f"Taslak, siz düzenlerken {cur.get('updated_by', 'başka bir yönetici')} tarafından değiştirildi. Sayfayı yenileyin.")
        now = _now()
        await db.site_content.update_one({"_id": "draft"}, {"$set": {
            "state": st, "dirty": True, "base_version": live.get("version", 0), "updated_at": now, "updated_by": user["name"]}}, upsert=True)
        return {"ok": True, "ops": len(st["ops"]), "updated_at": now}

    @api_router.put("/studio/schedule")
    async def studio_schedule(payload: dict, user: dict = Depends(require_admin)):
        at = (payload.get("at") or "").strip()
        if at:
            try:
                datetime.fromisoformat(at.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Geçersiz tarih")
        await db.site_content.update_one({"_id": "draft"}, {"$set": {"scheduled_at": at, "scheduled_by": user["name"]}}, upsert=True)
        return {"ok": True, "scheduled_at": at}

    @api_router.get("/public/site-bake")
    async def public_site_bake():
        """Statik yayın aracı (bake) için: yayındaki tüm içerik tek yanıtta."""
        live = await get_live()
        return {"version": live.get("version", 0), "state": live["state"]}

    async def do_publish(label: str, who: str):
        draft = await get_draft()
        live = await get_live()
        ver = int(live.get("version", 0)) + 1
        st = _clean_state(draft["state"])
        await db.site_content.update_one({"_id": "live"}, {"$set": {"state": st, "version": ver, "updated_at": _now(), "updated_by": who}}, upsert=True)
        await db.site_content.update_one({"_id": "draft"}, {"$set": {"dirty": False, "base_version": ver, "scheduled_at": ""}}, upsert=True)
        await db.site_versions.insert_one({"id": _id(), "version": ver, "label": label, "state": st,
                                           "created_at": _now(), "created_by": who, "ops": len(st["ops"])})
        old = await db.site_versions.find({}, {"_id": 1}).sort("version", -1).to_list(500)
        for o in old[40:]:
            await db.site_versions.delete_one({"_id": o["_id"]})
        return {"ok": True, "version": ver}

    @api_router.post("/studio/publish")
    async def studio_publish(payload: dict, user: dict = Depends(require_admin)):
        return await do_publish((payload or {}).get("label", ""), user["name"])

    async def scheduled_hook(_db):
        d = await db.site_content.find_one({"_id": "draft"}, {"_id": 0, "scheduled_at": 1, "scheduled_by": 1, "dirty": 1})
        if d and d.get("scheduled_at") and d.get("dirty"):
            try:
                due = datetime.fromisoformat(d["scheduled_at"].replace("Z", "+00:00"))
                if due.tzinfo is None:
                    due = due.replace(tzinfo=timezone.utc)
            except ValueError:
                return
            if due <= datetime.now(timezone.utc):
                await do_publish("Zamanlanmış yayın", (d.get("scheduled_by") or "zamanlayıcı") + " (zamanlanmış)")

    import governance
    governance.HOOKS.append(scheduled_hook)
    api_router.scheduled_publish_hook = scheduled_hook

    @api_router.post("/studio/discard")
    async def studio_discard(_: dict = Depends(require_admin)):
        live = await get_live()
        await db.site_content.update_one({"_id": "draft"}, {"$set": {"state": live["state"], "dirty": False, "base_version": live.get("version", 0), "updated_at": _now()}}, upsert=True)
        return {"ok": True}

    @api_router.get("/studio/versions")
    async def studio_versions(_: dict = Depends(require_admin)):
        return await db.site_versions.find({}, {"_id": 0, "state": 0}).sort("version", -1).to_list(60)

    @api_router.post("/studio/versions/{vid}/restore")
    async def studio_restore(vid: str, _: dict = Depends(require_admin)):
        v = await db.site_versions.find_one({"id": vid}, {"_id": 0})
        if not v:
            raise HTTPException(status_code=404, detail="Sürüm bulunamadı")
        live = await get_live()
        await db.site_content.update_one({"_id": "draft"}, {"$set": {"state": v["state"], "dirty": True, "base_version": live.get("version", 0), "updated_at": _now()}}, upsert=True)
        return {"ok": True}

    # ----------------------------------------------------------------- ADMIN: medya
    @api_router.post("/media")
    async def media_upload(request: Request, file: UploadFile = File(...), user: dict = Depends(require_admin)):
        raw = await file.read()
        if len(raw) > MAX_UPLOAD:
            raise HTTPException(status_code=413, detail="Dosya en fazla 8 MB olabilir")
        ctype = (file.content_type or "").lower()
        if ctype not in ALLOWED_IMG:
            raise HTTPException(status_code=400, detail="Yalnızca görsel dosyaları yüklenebilir")
        data, thumb, w, h = raw, None, 0, 0
        if ctype not in ("image/svg+xml", "image/gif", "image/x-icon"):
            try:
                from PIL import Image
                im = Image.open(io.BytesIO(raw))
                im.load()
                w, h = im.size
                if max(w, h) > 2400:
                    im.thumbnail((2400, 2400))
                    w, h = im.size
                buf = io.BytesIO()
                has_alpha = im.mode in ("RGBA", "LA", "P")
                im.convert("RGBA" if has_alpha else "RGB").save(buf, "WEBP", quality=86, method=4)
                if buf.tell() < len(raw) or max(w, h) > 2400:
                    data, ctype = buf.getvalue(), "image/webp"
                t = im.copy()
                t.thumbnail((360, 360))
                tb = io.BytesIO()
                t.convert("RGBA" if has_alpha else "RGB").save(tb, "WEBP", quality=70)
                thumb = tb.getvalue()
            except Exception:
                data = raw
        mid = _id()
        base = request.headers.get("x-public-base") or ""
        name = re.sub(r"[^\w.\- ]", "", file.filename or "gorsel")[:80]
        await db.media.insert_one({"id": mid, "name": name, "content_type": ctype, "size": len(data), "w": w, "h": h,
                                   "data": data, "thumb": thumb, "created_at": _now(), "created_by": user["name"]})
        return {"id": mid, "name": name, "size": len(data), "w": w, "h": h, "path": f"/api/public/media/{mid}"}

    @api_router.get("/media")
    async def media_list(_: dict = Depends(require_admin)):
        items = await db.media.find({}, {"_id": 0, "data": 0, "thumb": 0}).sort("created_at", -1).to_list(1000)
        for i in items:
            i["path"] = f"/api/public/media/{i['id']}"
        return items

    @api_router.put("/media/{mid}")
    async def media_rename(mid: str, payload: dict, _: dict = Depends(require_admin)):
        r = await db.media.update_one({"id": mid}, {"$set": {"name": str(payload.get("name", ""))[:80]}})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        return {"ok": True}

    @api_router.delete("/media/{mid}")
    async def media_delete(mid: str, _: dict = Depends(require_admin)):
        await db.media.delete_one({"id": mid})
        return {"ok": True}


async def ensure_indexes(db):
    await db.media.create_index("id", unique=True)
    await db.site_versions.create_index([("version", -1)])
