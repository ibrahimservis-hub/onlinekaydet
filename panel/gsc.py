# -*- coding: utf-8 -*-
"""Google Search Console bağlantısı (yalnız platform sahibi): organik aramada hangi kelimelerle çıkıldığını gösterir.

Kimlik doğrulama: Google hizmet hesabı (service account) JSON anahtarı. Hesabın e-postası Search Console'da
mülke 'Kullanıcı' olarak eklenir; anahtar yalnız sunucuda saklanır, panele geri gönderilmez.
"""
import json
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import jwt
import requests
from fastapi import Depends, HTTPException

import tenant

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/webmasters/v3/sites/%s/searchAnalytics/query"
_TOK = {"t": "", "exp": 0, "key": ""}
_CACHE = {}


def _token(sa):
    if _TOK["t"] and _TOK["exp"] > time.time() + 60 and _TOK["key"] == sa.get("client_email"):
        return _TOK["t"]
    now = int(time.time())
    assertion = jwt.encode({"iss": sa["client_email"], "scope": SCOPE, "aud": TOKEN_URL, "iat": now, "exp": now + 3000},
                           sa["private_key"], algorithm="RS256")
    r = requests.post(TOKEN_URL, data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion}, timeout=20)
    if r.status_code != 200:
        raise HTTPException(502, "Google kimlik doğrulaması başarısız: " + (r.json().get("error_description") if r.headers.get("content-type", "").startswith("application/json") else str(r.status_code)))
    j = r.json()
    _TOK.update(t=j["access_token"], exp=time.time() + int(j.get("expires_in", 3000)), key=sa.get("client_email"))
    return _TOK["t"]


def _query(site, sa, body):
    r = requests.post(API % quote(site, safe=""), headers={"Authorization": "Bearer " + _token(sa)}, json=body, timeout=30)
    if r.status_code == 403:
        raise HTTPException(403, "Hizmet hesabının (%s) bu mülke erişimi yok. Search Console > Ayarlar > Kullanıcılar ve izinler bölümünden bu e-postayı ekleyin." % sa.get("client_email"))
    if r.status_code == 404:
        raise HTTPException(404, "Mülk bulunamadı. Adres Search Console'daki ile birebir aynı olmalı (örn. sc-domain:onlinekaydet.com veya https://onlinekaydet.com/).")
    if r.status_code != 200:
        raise HTTPException(502, "Search Console yanıtı: %s" % r.status_code)
    return r.json().get("rows") or []


def _rows(rows, key=True):
    return [{"name": (r.get("keys") or [""])[0], "clicks": int(r.get("clicks", 0)), "impressions": int(r.get("impressions", 0)),
             "ctr": round(r.get("ctr", 0) * 100, 1), "position": round(r.get("position", 0), 1)} for r in rows]


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    def owner():
        if tenant.current():
            raise HTTPException(403, "Bu işlem yalnız platform sahibi içindir")

    async def cfg():
        d = await db.app_settings.find_one({"_id": "gsc"}, {"_id": 0}) or {}
        return d

    @api_router.get("/admin/gsc/ayar")
    async def gsc_ayar(_: dict = Depends(require_admin)):
        owner()
        d = await cfg()
        sa = d.get("sa") or {}
        return {"configured": bool(sa.get("client_email") and d.get("site")), "site": d.get("site", ""), "client_email": sa.get("client_email", "")}

    @api_router.post("/admin/gsc/ayar")
    async def gsc_kaydet(payload: dict, _: dict = Depends(require_admin)):
        owner()
        site = str(payload.get("site") or "").strip()[:200]
        if not re.fullmatch(r"(sc-domain:[a-z0-9.-]+|https?://[^\s]+)", site):
            raise HTTPException(422, "Mülk adresi: sc-domain:onlinekaydet.com ya da https://onlinekaydet.com/ biçiminde olmalı")
        raw = payload.get("sa_json")
        old = (await cfg()).get("sa") or {}
        if raw:
            try:
                sa = json.loads(raw) if isinstance(raw, str) else raw
            except ValueError:
                raise HTTPException(422, "Anahtar dosyası geçerli bir JSON değil")
            if not (sa.get("client_email") and "BEGIN PRIVATE KEY" in str(sa.get("private_key") or "")):
                raise HTTPException(422, "Bu bir hizmet hesabı anahtarı değil (client_email ve private_key gerekli)")
            sa = {"client_email": str(sa["client_email"]), "private_key": str(sa["private_key"])}
        elif old:
            sa = old
        else:
            raise HTTPException(422, "Hizmet hesabı JSON anahtarı gerekli")
        await db.app_settings.update_one({"_id": "gsc"}, {"$set": {"site": site, "sa": sa}}, upsert=True)
        _CACHE.clear()
        _TOK.update(t="", exp=0, key="")
        return {"ok": True, "client_email": sa["client_email"]}

    @api_router.delete("/admin/gsc/ayar")
    async def gsc_sil(_: dict = Depends(require_admin)):
        owner()
        await db.app_settings.delete_one({"_id": "gsc"})
        _CACHE.clear()
        return {"ok": True}

    @api_router.get("/analytics/gsc")
    async def gsc_veri(days: int = 28, _: dict = Depends(require_admin)):
        owner()
        d = await cfg()
        sa, site = d.get("sa") or {}, d.get("site")
        if not (sa.get("client_email") and site):
            return {"configured": False}
        days = max(7, min(int(days), 90))
        ck = (site, days)
        hit = _CACHE.get(ck)
        if hit and hit[0] > time.time():
            return hit[1]
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=days - 1)
        base = {"startDate": start.isoformat(), "endDate": end.isoformat(), "dataState": "all", "type": "web"}
        import asyncio
        loop = asyncio.get_event_loop()
        q = await loop.run_in_executor(None, lambda: _query(site, sa, {**base, "dimensions": ["query"], "rowLimit": 30}))
        pg = await loop.run_in_executor(None, lambda: _query(site, sa, {**base, "dimensions": ["page"], "rowLimit": 15}))
        dy = await loop.run_in_executor(None, lambda: _query(site, sa, {**base, "dimensions": ["date"], "rowLimit": 100}))
        clicks = sum(r.get("clicks", 0) for r in dy)
        imp = sum(r.get("impressions", 0) for r in dy)
        pos = (sum(r.get("position", 0) * r.get("impressions", 0) for r in dy) / imp) if imp else 0
        out = {"configured": True, "site": site, "days": days,
               "kpi": {"clicks": int(clicks), "impressions": int(imp), "ctr": round(clicks * 100 / imp, 1) if imp else 0, "position": round(pos, 1)},
               "queries": _rows(q), "pages": _rows(pg),
               "daily": [{"label": (r["keys"][0] or "")[5:].replace("-", "."), "clicks": int(r.get("clicks", 0)), "impressions": int(r.get("impressions", 0))} for r in sorted(dy, key=lambda r: r["keys"][0])]}
        _CACHE[ck] = (time.time() + 600, out)
        return out
