# -*- coding: utf-8 -*-
"""Siteye giren herkese duyuru: üstte bant ya da bir kez açılan pencere. Sekmesi panelde Bildirimler yanında."""
import html as _h
import re
import zlib

from fastapi import Depends

DEF = {"on": False, "tur": "bant", "text": "", "link": "", "link_text": "Ayrıntılar", "renk": "#f27a1a", "kapatilir": True}


async def get_cfg(db):
    d = await db.app_settings.find_one({"_id": "yp_duyuru"}, {"_id": 0}) or {}
    return dict(DEF, **{k: v for k, v in d.items() if k in DEF})


def render_html(c):
    """Sayfaya eklenecek parça: (gövde başı, gövde sonu). Boş duyuru yoksa ("", "")."""
    if not (c["on"] and c["text"].strip()):
        return "", ""
    key = "okdy" + str(zlib.crc32((c["text"] + c["tur"]).encode()))
    t, lk = _h.escape(c["text"]), (_h.escape(c["link"]) if re.match(r"^(/|https?://|tel:)", c["link"] or "") else "")
    a = ('<a href="%s">%s</a>' % (lk, _h.escape(c["link_text"] or "Ayrıntılar"))) if lk else ""
    col = c["renk"] if re.match(r"^#[0-9a-fA-F]{6}$", c["renk"] or "") else "#f27a1a"
    js = "<script>(function(){var k='%s',e=document.getElementById(k);if(!e)return;try{if(sessionStorage.getItem(k)){e.remove();return}}catch(x){}var c=e.querySelector('[data-k]');if(c)c.onclick=function(){e.remove();try{sessionStorage.setItem(k,1)}catch(x){}}})()</script>" % key
    x = '<button data-k aria-label="Kapat" style="background:none;border:0;color:inherit;font-size:22px;cursor:pointer;min-width:44px;min-height:44px">×</button>' if c["kapatilir"] else ""
    if c["tur"] == "popup":
        css = ("<style>#%s{position:fixed;inset:0;z-index:9600;background:#0008;display:grid;place-items:center;padding:18px}#%s .b{background:#fff;color:#0a1f44;max-width:420px;width:100%%;border-radius:16px;padding:26px;"
               "font:16px/1.5 system-ui,sans-serif;position:relative;border-top:6px solid %s}#%s .b a{display:inline-block;margin-top:14px;background:%s;color:#fff;padding:11px 18px;border-radius:10px;text-decoration:none;font-weight:700}"
               "#%s [data-k]{position:absolute;right:4px;top:2px;color:#0a1f44}</style>") % (key, key, col, key, col, key)
        return "", css + '<div id="%s" role="dialog" aria-modal="true"><div class="b">%s<div>%s</div>%s</div></div>' % (key, x, t, a) + js
    css = ("<style>#%s{display:flex;align-items:center;justify-content:center;gap:12px;background:%s;color:#fff;padding:4px 8px 4px 16px;font:600 14px/1.4 system-ui,sans-serif;text-align:center;position:relative;z-index:9300}"
           "#%s a{color:#fff;text-decoration:underline}</style>") % (key, col, key)
    return css + '<div id="%s" role="region" aria-label="Duyuru"><span>%s %s</span>%s</div>' % (key, t, a, x), js


def register(api_router, db, deps):
    adm = deps["require_admin"]

    @api_router.get("/yp/duyuru")
    async def duyuru_get(_: dict = Depends(adm)):
        return await get_cfg(db)

    @api_router.put("/yp/duyuru")
    async def duyuru_put(payload: dict, _: dict = Depends(adm)):
        c = await get_cfg(db)
        for k in ("on", "kapatilir"):
            if k in payload:
                c[k] = bool(payload[k])
        if payload.get("tur") in ("bant", "popup"):
            c["tur"] = payload["tur"]
        for k, n in (("text", 200), ("link", 300), ("link_text", 40)):
            if k in payload:
                c[k] = str(payload[k]).strip()[:n]
        if re.match(r"^#[0-9a-fA-F]{6}$", str(payload.get("renk") or "")):
            c["renk"] = payload["renk"]
        await db.app_settings.update_one({"_id": "yp_duyuru"}, {"$set": c}, upsert=True)
        return c
