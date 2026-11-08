"""Google Search Console otomatik yönetimi.

- Panelden tek tıkla "Google ile bağlan" (OAuth) — yenileme anahtarı kendiliğinden kaydedilir.
- Site (mülk) otomatik bulunur, sitemap adresleri otomatik tespit edilir, Google'a gönderilir (Sitemaps API).
- Sitemap'teki sayfalar sırayla URL Inspection API ile denetlenir (günlük kota dahilinde), dizin raporu çıkar.
- Arama performansı (tıklama/gösterim) mevcut mkt_site.gsc_sync ile çekilir.
- Zamanlayıcı (governance.HOOKS) + cPanel cron için gizli anahtarlı adres: /api/public/gsc/cron?k=...
- Hata olursa yöneticiye bildirim gider (aynı hata günde bir kez).

Not: Google'ın "Indexing API"si yalnızca iş ilanı/canlı yayın sayfaları içindir; sıradan sayfalar için
Google'ın resmî yolu sitemap gönderimi + URL denetimidir. Burada yapılan da budur.
"""
import asyncio
import html as _html
import logging
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode, urlparse

import jwt
import requests
from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

import governance
import mkt
import notify

log = logging.getLogger("gsc_auto")
SCOPE = "https://www.googleapis.com/auth/webmasters"
API = "https://searchconsole.googleapis.com"
DEFAULTS = {"auto": True, "interval_h": 24, "sitemaps": [], "inspect_per_run": 40, "analytics": True, "cron_key": "",
            "last_run": "", "last_result": {}, "last_error": "", "last_error_day": ""}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _day():
    return datetime.now(timezone.utc).date().isoformat()


def _get(url, timeout=25):
    return requests.get(url, headers={"User-Agent": "ServisPlusBot/1.0"}, timeout=timeout)


def collect_urls(sitemap_urls, limit=5000):
    """Sitemap (ve sitemap index) içindeki sayfa adreslerini toplar."""
    seen, urls, queue, checked = set(), [], list(sitemap_urls), []
    while queue and len(checked) < 40:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        try:
            r = _get(sm)
        except Exception as e:                          # noqa: BLE001
            checked.append({"url": sm, "ok": False, "error": str(e)[:120], "count": 0})
            continue
        if r.status_code != 200 or "<" not in r.text[:200]:
            checked.append({"url": sm, "ok": False, "error": f"HTTP {r.status_code}", "count": 0})
            continue
        locs = [_html.unescape(x) for x in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", r.text)]
        if "<sitemapindex" in r.text[:2000].lower():
            queue += locs
            checked.append({"url": sm, "ok": True, "index": True, "count": len(locs)})
        else:
            urls += locs
            checked.append({"url": sm, "ok": True, "count": len(locs)})
        if len(urls) >= limit:
            break
    return list(dict.fromkeys(urls))[:limit], checked


def discover_sitemaps(site_url):
    out = []
    try:
        r = _get(site_url.rstrip("/") + "/robots.txt", timeout=15)
        if r.status_code == 200:
            out += re.findall(r"(?im)^\s*sitemap:\s*(\S+)", r.text)
    except Exception:                                   # noqa: BLE001
        pass
    for p in ("/sitemap.xml", "/sitemap_index.xml"):
        u = site_url.rstrip("/") + p
        if u not in out:
            try:
                if _get(u, timeout=15).status_code == 200:
                    out.append(u)
            except Exception:                           # noqa: BLE001
                pass
    return list(dict.fromkeys(out))


def register(api_router, db, deps):
    PANEL_URL = os.environ.get("PANEL_PUBLIC_URL", "https://bayi.servisplus.net.tr")
    require_admin = deps["require_admin"]
    JWT_SECRET = deps["JWT_SECRET"]
    adm = Depends(require_admin)

    async def get_conf():
        d = await db.app_settings.find_one({"_id": "gsc_auto"}, {"_id": 0}) or {}
        c = {**DEFAULTS, **d}
        if not c["cron_key"]:
            c["cron_key"] = secrets.token_urlsafe(16)
            await db.app_settings.update_one({"_id": "gsc_auto"}, {"$set": {"cron_key": c["cron_key"]}}, upsert=True)
        return c

    async def save(upd):
        await db.app_settings.update_one({"_id": "gsc_auto"}, {"$set": upd}, upsert=True)

    async def google():
        cfg = await mkt.get_cfg(db)
        return cfg, cfg["google"]

    def hdr(tok):
        return {"Authorization": "Bearer " + tok}

    def pick_property(sites, site_url):
        host = urlparse(site_url).netloc.replace("www.", "")
        cands = [f"sc-domain:{host}", site_url.rstrip("/") + "/", f"https://www.{host}/", f"http://{host}/"]
        have = {s["siteUrl"]: s.get("permissionLevel", "") for s in sites}
        for c in cands:
            if c in have and have[c] != "siteUnverifiedUser":
                return c
        return ""

    # ------------------------------------------------------------ durum
    @api_router.get("/admin/gsc/status")
    async def status(_: dict = adm):
        c = await get_conf()
        cfg, g = await google()
        total = await db.page_index.count_documents({})
        ok = await db.page_index.count_documents({"verdict": "PASS"})
        return {
            "has_client": bool(g.get("client_id") and g.get("client_secret")),
            "client_id": g.get("client_id") or "",
            "connected": bool(g.get("gsc_refresh_token")),
            "property": g.get("gsc_site") or "",
            "site_url": cfg["site_url"],
            "config": {k: c[k] for k in ("auto", "interval_h", "sitemaps", "inspect_per_run", "analytics")},
            "last_run": c["last_run"], "last_result": c["last_result"], "last_error": c["last_error"],
            "cron_url": f"{PANEL_URL}/api/public/gsc/cron?k={c['cron_key']}",
            "redirect_uri": f"{PANEL_URL}/api/public/gsc/oauth/callback",
            "inspected": total, "indexed": ok,
        }

    @api_router.put("/admin/gsc/config")
    async def put_config(payload: dict, _: dict = adm):
        upd = {}
        if "auto" in payload:
            upd["auto"] = bool(payload["auto"])
        if "analytics" in payload:
            upd["analytics"] = bool(payload["analytics"])
        if "interval_h" in payload:
            upd["interval_h"] = max(6, min(168, int(payload["interval_h"] or 24)))
        if "inspect_per_run" in payload:
            upd["inspect_per_run"] = max(0, min(200, int(payload["inspect_per_run"] or 0)))
        if "sitemaps" in payload:
            upd["sitemaps"] = [str(u).strip() for u in (payload["sitemaps"] or []) if re.match(r"^https?://", str(u).strip())][:20]
        if upd:
            await save(upd)
        if payload.get("property") is not None:
            await db.app_settings.update_one({"_id": "mkt"}, {"$set": {"google.gsc_site": str(payload["property"]).strip()}}, upsert=True)
        return await status(_)

    # ------------------------------------------------------------ OAuth bağlantısı
    @api_router.put("/admin/gsc/client")
    async def put_client(payload: dict, _: dict = adm):
        upd = {}
        cid, cs = str(payload.get("client_id") or "").strip(), str(payload.get("client_secret") or "").strip()
        if cid:
            upd["google.client_id"] = cid
        if cs and not cs.startswith("*"):
            upd["google.client_secret"] = cs
        if upd:
            await db.app_settings.update_one({"_id": "mkt"}, {"$set": upd}, upsert=True)
        return {"ok": True}

    @api_router.get("/admin/gsc/oauth-url")
    async def oauth_url(_: dict = adm):
        cfg, g = await google()
        if not (g.get("client_id") and g.get("client_secret")):
            raise HTTPException(400, "Önce Google istemci kimliği ve gizli anahtarını kaydedin.")
        state = jwt.encode({"t": "gsc", "exp": int(time.time()) + 900}, JWT_SECRET, algorithm="HS256")
        q = urlencode({"client_id": g["client_id"], "redirect_uri": f"{PANEL_URL}/api/public/gsc/oauth/callback", "response_type": "code",
                       "scope": SCOPE, "access_type": "offline", "prompt": "consent", "state": state})
        return {"url": "https://accounts.google.com/o/oauth2/v2/auth?" + q}

    @api_router.get("/public/gsc/oauth/callback")
    async def oauth_cb(request: Request):
        code, state = request.query_params.get("code", ""), request.query_params.get("state", "")
        err = request.query_params.get("error", "")

        def page(msg, ok):
            col = "#15803d" if ok else "#b91c1c"
            return HTMLResponse("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
                                f"<body style='font-family:system-ui;text-align:center;padding:60px 20px'><h2 style='color:{col}'>{_html.escape(msg)}</h2>"
                                "<p>Bu pencereyi kapatıp panele dönebilirsiniz.</p>"
                                "<script>try{window.opener&&window.opener.postMessage('gsc-connected','*')}catch(e){}</script></body>")
        if err or not code:
            return page("Bağlantı iptal edildi: " + (err or "kod gelmedi"), False)
        try:
            jwt.decode(state, JWT_SECRET, algorithms=["HS256"])
        except Exception:                               # noqa: BLE001
            return page("Oturum süresi doldu, panelden yeniden deneyin.", False)
        cfg, g = await google()
        try:
            r = await asyncio.to_thread(mkt._http, "POST", "https://oauth2.googleapis.com/token", None, None,
                                        {"code": code, "client_id": g["client_id"], "client_secret": g["client_secret"],
                                         "redirect_uri": f"{PANEL_URL}/api/public/gsc/oauth/callback", "grant_type": "authorization_code"})
        except Exception as e:                          # noqa: BLE001
            return page("Google jeton hatası: " + str(e)[:160], False)
        rt = r.get("refresh_token")
        if not rt:
            return page("Google yenileme anahtarı vermedi. Google hesabı izinlerinden uygulamayı kaldırıp tekrar deneyin.", False)
        await db.app_settings.update_one({"_id": "mkt"}, {"$set": {"google.gsc_refresh_token": rt}}, upsert=True)
        return page("Google Search Console bağlandı ✓", True)

    @api_router.post("/admin/gsc/disconnect")
    async def disconnect(_: dict = adm):
        await db.app_settings.update_one({"_id": "mkt"}, {"$set": {"google.gsc_refresh_token": ""}}, upsert=True)
        return {"ok": True}

    # ------------------------------------------------------------ Google çağrıları
    async def api_call(method, path, **kw):
        cfg, g = await google()
        tok = await asyncio.to_thread(mkt.g_token, g, "gsc")
        return await asyncio.to_thread(lambda: requests.request(method, API + path, headers=hdr(tok), timeout=40, **kw))

    def need_ok(r):
        if r.status_code >= 400:
            hint = " (Bağlantıyı yenileyin: izin kapsamı eksik olabilir.)" if r.status_code in (401, 403) else ""
            raise HTTPException(502, f"Search Console {r.status_code}: {r.text[:200]}{hint}")

    @api_router.get("/admin/gsc/sites")
    async def sites(_: dict = adm):
        cfg, g = await google()
        try:
            r = await api_call("GET", "/webmasters/v3/sites")
        except Exception as e:                          # noqa: BLE001
            raise HTTPException(502, str(e)[:250])
        need_ok(r)
        lst = r.json().get("siteEntry", [])
        auto = pick_property(lst, cfg["site_url"])
        if auto and not g.get("gsc_site"):
            await db.app_settings.update_one({"_id": "mkt"}, {"$set": {"google.gsc_site": auto}}, upsert=True)
        return {"sites": lst, "auto": auto, "selected": g.get("gsc_site") or auto}

    @api_router.get("/admin/gsc/sitemaps")
    async def sitemaps(_: dict = adm):
        cfg, g = await google()
        site = g.get("gsc_site") or cfg["site_url"] + "/"
        try:
            r = await api_call("GET", f"/webmasters/v3/sites/{quote(site, safe='')}/sitemaps")
        except Exception as e:                          # noqa: BLE001
            raise HTTPException(502, str(e)[:250])
        need_ok(r)
        out = []
        for s in r.json().get("sitemap", []):
            out.append({"path": s.get("path"), "last_submitted": s.get("lastSubmitted", ""), "last_downloaded": s.get("lastDownloaded", ""),
                        "pending": s.get("isPending", False), "errors": int(s.get("errors", 0) or 0), "warnings": int(s.get("warnings", 0) or 0),
                        "contents": [{"type": c.get("type"), "submitted": int(c.get("submitted", 0) or 0), "indexed": int(c.get("indexed", 0) or 0)} for c in s.get("contents", [])]})
        return out

    @api_router.delete("/admin/gsc/sitemaps")
    async def sitemap_delete(path: str, _: dict = adm):
        cfg, g = await google()
        site = g.get("gsc_site") or cfg["site_url"] + "/"
        r = await api_call("DELETE", f"/webmasters/v3/sites/{quote(site, safe='')}/sitemaps/{quote(path, safe='')}")
        need_ok(r)
        return {"ok": True}

    # ------------------------------------------------------------ işler
    async def job_sitemaps(cfg, g, conf, rep):
        sms = conf["sitemaps"] or await asyncio.to_thread(discover_sitemaps, cfg["site_url"])
        if not sms:
            rep["sitemaps"] = {"error": "Sitemap bulunamadı (robots.txt / sitemap.xml)."}
            return []
        site = g.get("gsc_site") or cfg["site_url"] + "/"
        sent, errs = [], []
        for sm in sms:
            r = await api_call("PUT", f"/webmasters/v3/sites/{quote(site, safe='')}/sitemaps/{quote(sm, safe='')}")
            if r.status_code in (200, 204):
                sent.append(sm)
            else:
                errs.append(f"{sm}: {r.status_code} {r.text[:120]}")
        rep["sitemaps"] = {"submitted": sent, "errors": errs}
        if errs and not sent:
            raise RuntimeError("Sitemap gönderilemedi: " + errs[0])
        return sms

    async def job_inspect(cfg, g, conf, rep, sms):
        n = int(conf["inspect_per_run"])
        if n <= 0:
            return
        urls, checked = await asyncio.to_thread(collect_urls, sms or [cfg["site_url"] + "/sitemap.xml"])
        rep["sitemap_files"] = checked
        rep["sitemap_urls"] = len(urls)
        if not urls:
            return
        site = g.get("gsc_site") or cfg["site_url"] + "/"
        host = urlparse(cfg["site_url"]).netloc.replace("www.", "")
        known = {d["path"]: d.get("at", "") async for d in db.page_index.find({}, {"_id": 0, "path": 1, "at": 1})}

        def path_of(u):
            p = urlparse(u)
            return (p.path or "/") + (("?" + p.query) if p.query else "")
        todo = [u for u in urls if urlparse(u).netloc.replace("www.", "") == host]
        todo.sort(key=lambda u: known.get(path_of(u), ""))       # hiç denetlenmemişler önce, sonra en eskiler
        done = bad = 0
        tok = await asyncio.to_thread(mkt.g_token, g, "gsc")
        for u in todo[:n]:
            try:
                r = await asyncio.to_thread(lambda: requests.post(API + "/v1/urlInspection/index:inspect", headers=hdr(tok), timeout=40,
                                                                json={"inspectionUrl": u, "siteUrl": site}))
            except Exception:                           # noqa: BLE001
                bad += 1
                continue
            if r.status_code == 429:
                rep["quota"] = "Günlük denetim kotası doldu, yarın devam eder."
                break
            if r.status_code >= 400:
                bad += 1
                if r.status_code in (401, 403):
                    raise RuntimeError(f"URL denetimi reddedildi ({r.status_code}): {r.text[:160]}")
                continue
            ir = (r.json().get("inspectionResult") or {}).get("indexStatusResult") or {}
            doc = {"path": path_of(u), "url": u, "verdict": ir.get("verdict", ""), "state": ir.get("coverageState", ""),
                   "robots": ir.get("robotsTxtState", ""), "indexing": ir.get("indexingState", ""), "last_crawl": ir.get("lastCrawlTime", ""),
                   "canonical": ir.get("googleCanonical", ""), "user_canonical": ir.get("userCanonical", ""), "at": _now()}
            await db.page_index.update_one({"path": doc["path"]}, {"$set": doc}, upsert=True)
            done += 1
            await asyncio.sleep(0.15)
        rep["inspected"] = done
        rep["inspect_failed"] = bad

    async def run(parts=("sitemap", "inspect", "analytics")):
        cfg, g = await google()
        conf = await get_conf()
        rep = {"at": _now()}
        if not g.get("gsc_refresh_token"):
            raise RuntimeError("Google hesabı bağlı değil.")
        if not g.get("gsc_site"):
            r = await api_call("GET", "/webmasters/v3/sites")
            if r.status_code == 200:
                auto = pick_property(r.json().get("siteEntry", []), cfg["site_url"])
                if auto:
                    await db.app_settings.update_one({"_id": "mkt"}, {"$set": {"google.gsc_site": auto}}, upsert=True)
                    cfg, g = await google()
        sms = []
        if "sitemap" in parts:
            sms = await job_sitemaps(cfg, g, conf, rep)
        if "inspect" in parts:
            await job_inspect(cfg, g, conf, rep, sms or conf["sitemaps"])
        if "analytics" in parts and conf["analytics"]:
            try:
                import mkt_site
                rep["analytics_rows"] = await mkt_site.gsc_sync(db, 28)
            except Exception as e:                      # noqa: BLE001
                rep["analytics_error"] = str(e)[:200]
        await save({"last_run": rep["at"], "last_result": rep, "last_error": ""})
        return rep

    async def run_safe(parts):
        try:
            return await run(parts)
        except Exception as e:                          # noqa: BLE001
            msg = str(e)[:300]
            c = await get_conf()
            await save({"last_run": _now(), "last_error": msg})
            if c.get("last_error_day") != _day():
                await save({"last_error_day": _day()})
                try:
                    await notify.notify_owner(db, "Google Search Console otomasyonu hata verdi: " + msg, kind="gsc_error")
                except Exception:                       # noqa: BLE001
                    pass
            raise

    @api_router.post("/admin/gsc/run")
    async def run_now(payload: dict, _: dict = adm):
        parts = [p for p in (payload.get("parts") or ["sitemap", "inspect", "analytics"]) if p in ("sitemap", "inspect", "analytics")]
        try:
            return await run_safe(tuple(parts))
        except Exception as e:                          # noqa: BLE001
            raise HTTPException(502, str(e)[:300])

    @api_router.get("/public/gsc/cron")
    async def cron(k: str = ""):
        c = await get_conf()
        if not secrets.compare_digest(k or "x", c["cron_key"]):
            raise HTTPException(403, "Yetkisiz")
        try:
            rep = await run_safe(("sitemap", "inspect", "analytics"))
            return {"ok": True, "submitted": (rep.get("sitemaps") or {}).get("submitted"), "inspected": rep.get("inspected", 0)}
        except Exception as e:                          # noqa: BLE001
            return {"ok": False, "error": str(e)[:200]}

    @api_router.get("/admin/gsc/index-report")
    async def index_report(_: dict = adm):
        rows = await db.page_index.find({}, {"_id": 0}).to_list(20000)
        states = {}
        for r in rows:
            k = r.get("state") or "Bilinmiyor"
            states[k] = states.get(k, 0) + 1
        bad = [r for r in rows if r.get("verdict") != "PASS"]
        bad.sort(key=lambda r: r.get("at", ""), reverse=True)
        return {"total": len(rows), "indexed": sum(1 for r in rows if r.get("verdict") == "PASS"),
                "states": sorted(([k, v] for k, v in states.items()), key=lambda x: -x[1]),
                "problems": [{"path": r["path"], "state": r.get("state", ""), "verdict": r.get("verdict", ""),
                              "last_crawl": r.get("last_crawl", ""), "at": r.get("at", "")} for r in bad[:100]]}

    @api_router.post("/admin/gsc/inspect-url")
    async def inspect_url(payload: dict, _: dict = adm):
        cfg, g = await google()
        path = str(payload.get("path") or "/")
        u = path if path.startswith("http") else cfg["site_url"] + (path if path.startswith("/") else "/" + path)
        site = g.get("gsc_site") or cfg["site_url"] + "/"
        r = await api_call("POST", "/v1/urlInspection/index:inspect", json={"inspectionUrl": u, "siteUrl": site})
        need_ok(r)
        ir = (r.json().get("inspectionResult") or {}).get("indexStatusResult") or {}
        doc = {"path": urlparse(u).path or "/", "url": u, "verdict": ir.get("verdict", ""), "state": ir.get("coverageState", ""),
               "robots": ir.get("robotsTxtState", ""), "indexing": ir.get("indexingState", ""), "last_crawl": ir.get("lastCrawlTime", ""),
               "canonical": ir.get("googleCanonical", ""), "at": _now()}
        await db.page_index.update_one({"path": doc["path"]}, {"$set": doc}, upsert=True)
        return doc

    # ------------------------------------------------------------ zamanlayıcı
    async def hook(_db):
        try:
            c = await get_conf()
            if not c["auto"]:
                return
            cfg, g = await google()
            if not g.get("gsc_refresh_token"):
                return
            last = c.get("last_run") or ""
            if last and datetime.fromisoformat(last) > datetime.now(timezone.utc) - timedelta(hours=int(c["interval_h"])):
                return
            await save({"last_run": _now()})              # çifte çalışmayı önle
            await run_safe(("sitemap", "inspect", "analytics"))
        except Exception as e:                          # noqa: BLE001
            log.warning("gsc auto: %s", e)

    governance.HOOKS.append(hook)
