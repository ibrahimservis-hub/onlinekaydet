# -*- coding: utf-8 -*-
"""Bölüm motorunun uçları: katalog, rozetler, sektör paketleri ve sayfalar.

Sayfa = bölüm örneklerinden oluşan liste. Her örnek kendi ayarını (`set`) ve
telefon için ayrı ayarını (`set_m`) taşır. Katalog; sektöre, açık modüllere ve
sahibin izin verdiği listeye göre süzülür.
"""
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException

import blocks

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

RESERVED = {"api", "admin", "panel", "salon", "yonetim", "static", "uploads"}


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


def _t(v, n):
    return " ".join(str(v or "").split())[:n]


def slug(s, n=60):
    s = str(s or "").strip().lower()
    for a, b in (("ı", "i"), ("ğ", "g"), ("ü", "u"), ("ş", "s"), ("ö", "o"), ("ç", "c"), ("â", "a"), ("î", "i")):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return (s or "sayfa")[:n]


def register(api_router, db, deps):
    adm = deps["require_admin"]

    # ------------------------------------------------------------ paket durumu
    async def state():
        """Firmanın sektörü, açık modülleri ve sahibin izin verdiği bölümler."""
        d = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
        sec = d.get("sector")
        if not sec:
            s = await db.app_settings.find_one({"_id": "sector"}, {"_id": 0}) or {}
            sec = s.get("key") or ""
        pk = blocks.pack(sec) or {}
        mods = d.get("modules")
        if mods is None:
            mods = pk.get("modules") or []
        return {"sector": sec, "pack": pk, "modules": list(mods),
                "allow": d.get("allow"), "custom_badges": d.get("badges") or [],
                "sectors_allowed": d.get("sectors_allowed")}

    async def page_or_404(pid):
        p = await db.yp_pages.find_one({"id": pid}, {"_id": 0})
        if not p:
            raise HTTPException(404, "Sayfa bulunamadı")
        return p

    async def ensure_home():
        if not await db.yp_pages.count_documents({}):
            st = await state()
            ids = (st["pack"].get("blocks") or ["hero"])[:8]
            inst = [i for i in (blocks.new_instance(b) for b in ids) if i]
            await db.yp_pages.insert_one({"id": uuid.uuid4().hex[:12], "slug": "", "title": "Ana sayfa",
                                          "home": True, "status": "live", "order": 0,
                                          "menu": {"top": True, "footer": False, "mobile": True, "label": "Ana sayfa", "parent": ""},
                                          "blocks": inst, "created_at": _now(), "updated_at": _now()})

    # ------------------------------------------------------------ katalog
    @api_router.get("/yp/blocks")
    async def block_list(cat: str = "", q: str = "", all_: bool = False, _: dict = Depends(adm)):
        """Eklenebilir bölümler. Sektöre ve açık modüllere göre süzülür."""
        st = await state()
        rows = blocks.catalog("" if all_ else st["sector"], st["modules"], st["allow"])
        cnt = blocks.counts(rows)
        q = q.strip().lower()
        if q:
            rows = [r for r in rows if q in r["name"].lower() or q in r["desc"].lower()]
        if cat:
            rows = [r for r in rows if r["cat"] == cat]
        cats = [{"id": c, "name": n, "n": cnt.get(c, 0)} for c, n in blocks.CATS if cnt.get(c)]
        return {"rows": rows, "cats": cats, "total": sum(cnt.values()), "sector": st["sector"],
                "sector_name": (st["pack"] or {}).get("name", ""), "modules": st["modules"]}

    @api_router.get("/yp/blocks/{bid}")
    async def block_one(bid: str, _: dict = Depends(adm)):
        b = blocks.BY_ID.get(bid)
        if not b:
            raise HTTPException(404, "Bölüm bulunamadı")
        st = await state()
        return {"block": {k: b[k] for k in ("id", "cat", "name", "desc", "wire", "tags", "manage", "resp")},
                "fields": b["fields"], "defaults": blocks.defaults(bid),
                "badges": blocks.badge_list(st["custom_badges"]) if any(f["t"] == "rozet" for f in b["fields"]) else []}

    # ------------------------------------------------------------ rozetler
    @api_router.get("/yp/badges")
    async def badges_get(_: dict = Depends(adm)):
        st = await state()
        return {"rows": blocks.badge_list(st["custom_badges"]), "pos": blocks.BADGE_POS}

    @api_router.put("/yp/badges")
    async def badges_put(payload: dict, _: dict = Depends(adm)):
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise HTTPException(422, "Rozet listesi gerekli")
        custom = [r for r in rows if isinstance(r, dict) and r.get("custom")]
        await db.app_settings.update_one({"_id": "yp_pack"}, {"$set": {"badges": custom[:20]}}, upsert=True)
        st = await state()
        return {"rows": blocks.badge_list(st["custom_badges"])}

    # ------------------------------------------------------------ sektör paketleri
    @api_router.get("/yp/sectors")
    async def sectors(_: dict = Depends(adm)):
        st = await state()
        al = st["sectors_allowed"]
        rows = []
        for p in blocks.pack_list():
            rows.append(dict(p, locked=bool(al is not None and p["id"] not in al), on=p["id"] == st["sector"]))
        return {"rows": rows, "sector": st["sector"]}

    @api_router.post("/yp/sectors/{sid}")
    async def sector_apply(sid: str, _: dict = Depends(adm)):
        """Sektör paketini uygula: terimler, modüller ve hazır bölümler gelsin."""
        pk = blocks.pack(sid)
        if not pk:
            raise HTTPException(404, "Sektör bulunamadı")
        st = await state()
        if st["sectors_allowed"] is not None and sid not in st["sectors_allowed"]:
            raise HTTPException(403, "Bu sektör paketinizde yok")
        await db.app_settings.update_one({"_id": "yp_pack"},
                                         {"$set": {"sector": sid, "modules": list(pk["modules"]), "applied_at": _now()}}, upsert=True)
        return {"ok": True, "sector": sid, "terms": pk["terms"], "modules": pk["modules"],
                "integrations": pk["integrations"], "reports": pk["reports"], "flow": pk["flow"]}

    # ------------------------------------------------------------ sayfalar
    @api_router.get("/yp/pages")
    async def pages(_: dict = Depends(adm)):
        await ensure_home()
        rows = await db.yp_pages.find({}, {"_id": 0, "blocks": 0}).sort("order", 1).to_list(200)
        cnt = {p["id"]: len(p.get("blocks") or []) for p in await db.yp_pages.find({}, {"_id": 0, "id": 1, "blocks": 1}).to_list(200)}
        return {"rows": [dict(r, n=cnt.get(r["id"], 0)) for r in rows]}

    @api_router.post("/yp/pages")
    async def page_add(payload: dict, _: dict = Depends(adm)):
        await ensure_home()
        title = _t(payload.get("title"), 80) or "Yeni sayfa"
        sl = slug(payload.get("slug") or title)
        if sl in RESERVED or await db.yp_pages.find_one({"slug": sl}, {"_id": 1}):
            sl = sl + "-" + uuid.uuid4().hex[:4]
        src = payload.get("copy_of")
        inst = []
        if src:
            o = await page_or_404(src)
            for b in (o.get("blocks") or []):
                inst.append(dict(b, iid=uuid.uuid4().hex[:10]))
        elif payload.get("blocks"):
            inst = [i for i in (blocks.new_instance(b) for b in list(payload["blocks"])[:40]) if i]
        n = await db.yp_pages.count_documents({})
        doc = {"id": uuid.uuid4().hex[:12], "slug": sl, "title": title, "home": False,
               "status": "draft" if payload.get("draft") else "live", "order": n,
               "menu": {"top": bool(payload.get("menu", True)), "footer": bool(payload.get("footer")),
                        "mobile": False, "label": title, "parent": _t(payload.get("parent"), 40)},
               "blocks": inst, "created_at": _now(), "updated_at": _now()}
        await db.yp_pages.insert_one(dict(doc))
        doc.pop("blocks")
        return dict(doc, n=len(inst))

    @api_router.put("/yp/pages/{pid}")
    async def page_put(pid: str, payload: dict, _: dict = Depends(adm)):
        p = await page_or_404(pid)
        up = {"updated_at": _now()}
        if "title" in payload:
            up["title"] = _t(payload["title"], 80) or p["title"]
        if "slug" in payload and not p.get("home"):
            sl = slug(payload["slug"])
            if sl in RESERVED or await db.yp_pages.find_one({"slug": sl, "id": {"$ne": pid}}, {"_id": 1}):
                raise HTTPException(422, "Bu adres kullanılıyor")
            up["slug"] = sl
        if "status" in payload:
            up["status"] = "draft" if payload["status"] == "draft" else "live"
        if "menu" in payload and isinstance(payload["menu"], dict):
            m = payload["menu"]
            up["menu"] = {"top": bool(m.get("top")), "footer": bool(m.get("footer")), "mobile": bool(m.get("mobile")),
                          "label": _t(m.get("label"), 40) or p["title"], "parent": _t(m.get("parent"), 40)}
        await db.yp_pages.update_one({"id": pid}, {"$set": up})
        return dict(p, **up, blocks=None, n=len(p.get("blocks") or []))

    @api_router.delete("/yp/pages/{pid}")
    async def page_del(pid: str, _: dict = Depends(adm)):
        p = await page_or_404(pid)
        if p.get("home"):
            raise HTTPException(422, "Ana sayfa silinemez")
        await db.yp_pages.delete_one({"id": pid})
        return {"ok": True}

    @api_router.post("/yp/pages/order")
    async def pages_order(payload: dict, _: dict = Depends(adm)):
        ids = [str(i) for i in (payload.get("ids") or [])][:200]
        for i, pid in enumerate(ids):
            await db.yp_pages.update_one({"id": pid}, {"$set": {"order": i}})
        return {"ok": True}

    # ------------------------------------------------------------ sayfadaki bölümler
    @api_router.get("/yp/pages/{pid}/blocks")
    async def page_blocks(pid: str, _: dict = Depends(adm)):
        p = await page_or_404(pid)
        out = []
        for b in (p.get("blocks") or []):
            meta = blocks.BY_ID.get(b["bid"])
            if not meta:
                continue
            out.append(dict(b, name=meta["name"], desc=meta["desc"], cat=meta["cat"],
                            wire=meta["wire"], resp=meta["resp"], manage=meta["manage"]))
        return {"page": {k: p[k] for k in ("id", "slug", "title", "status", "home", "menu")}, "rows": out}

    @api_router.post("/yp/pages/{pid}/blocks")
    async def block_add(pid: str, payload: dict, _: dict = Depends(adm)):
        p = await page_or_404(pid)
        st = await state()
        bid = str(payload.get("bid") or "")
        meta = blocks.BY_ID.get(bid)
        if not meta:
            raise HTTPException(404, "Bölüm bulunamadı")
        if st["allow"] is not None and bid not in st["allow"]:
            raise HTTPException(403, "Bu bölüm paketinizde yok")
        if meta["needs"] and not set(meta["needs"]) <= set(st["modules"]):
            raise HTTPException(403, "Bu bölüm için %s modülü açık olmalı" % ", ".join(meta["needs"]))
        if meta["sectors"] != ["*"] and st["sector"] and st["sector"] not in meta["sectors"]:
            raise HTTPException(403, "Bu bölüm bu sektörde kullanılmıyor")
        rows = list(p.get("blocks") or [])
        if len(rows) >= 60:
            raise HTTPException(422, "Bir sayfada en çok 60 bölüm olabilir")
        inst = blocks.new_instance(bid)
        at = payload.get("at")
        if isinstance(at, int) and 0 <= at <= len(rows):
            rows.insert(at, inst)
        else:
            rows.append(inst)
        await db.yp_pages.update_one({"id": pid}, {"$set": {"blocks": rows, "updated_at": _now()}})
        return dict(inst, name=meta["name"], desc=meta["desc"], cat=meta["cat"], wire=meta["wire"],
                    resp=meta["resp"], manage=meta["manage"], at=rows.index(inst))

    @api_router.put("/yp/pages/{pid}/blocks/{iid}")
    async def block_set(pid: str, iid: str, payload: dict, _: dict = Depends(adm)):
        """Bölümün ayarları. `set` bilgisayar, `set_m` telefon için."""
        p = await page_or_404(pid)
        rows = list(p.get("blocks") or [])
        for i, b in enumerate(rows):
            if b["iid"] != iid:
                continue
            if "on" in payload:
                b["on"] = bool(payload["on"])
            if isinstance(payload.get("set"), dict):
                b["set"] = dict(b.get("set") or {}, **blocks.sanitize(b["bid"], payload["set"]))
            if isinstance(payload.get("set_m"), dict):
                b["set_m"] = dict(b.get("set_m") or {}, **blocks.sanitize(b["bid"], payload["set_m"], mobile=True))
            if isinstance(payload.get("badges"), list):
                ok = {x["id"] for x in blocks.badge_list((await state())["custom_badges"])}
                b["badges"] = [str(x)[:24] for x in payload["badges"][:12] if str(x) in ok]
            rows[i] = b
            await db.yp_pages.update_one({"id": pid}, {"$set": {"blocks": rows, "updated_at": _now()}})
            return b
        raise HTTPException(404, "Bölüm bu sayfada yok")

    @api_router.delete("/yp/pages/{pid}/blocks/{iid}")
    async def block_del(pid: str, iid: str, _: dict = Depends(adm)):
        p = await page_or_404(pid)
        rows = [b for b in (p.get("blocks") or []) if b["iid"] != iid]
        if len(rows) == len(p.get("blocks") or []):
            raise HTTPException(404, "Bölüm bu sayfada yok")
        await db.yp_pages.update_one({"id": pid}, {"$set": {"blocks": rows, "updated_at": _now()}})
        return {"ok": True}

    @api_router.post("/yp/pages/{pid}/blocks/order")
    async def block_order(pid: str, payload: dict, _: dict = Depends(adm)):
        p = await page_or_404(pid)
        rows = list(p.get("blocks") or [])
        ids = [str(i) for i in (payload.get("ids") or [])]
        idx = {b["iid"]: b for b in rows}
        new = [idx[i] for i in ids if i in idx]
        if len(new) != len(rows):
            new += [b for b in rows if b["iid"] not in set(ids)]
        await db.yp_pages.update_one({"id": pid}, {"$set": {"blocks": new, "updated_at": _now()}})
        return {"ok": True, "ids": [b["iid"] for b in new]}

    # ------------------------------------------------------------ menü (sayfalardan)
    @api_router.get("/yp/site/nav")
    async def nav(_: dict = Depends(adm)):
        await ensure_home()
        rows = await db.yp_pages.find({"status": "live"}, {"_id": 0, "blocks": 0}).sort("order", 1).to_list(200)
        out = {"top": [], "footer": [], "mobile": []}
        for r in rows:
            m = r.get("menu") or {}
            item = {"label": m.get("label") or r["title"], "href": "/" + (r["slug"] or ""), "parent": m.get("parent") or ""}
            for k in ("top", "footer", "mobile"):
                if m.get(k):
                    out[k].append(item)
        return out
