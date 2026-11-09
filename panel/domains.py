# -*- coding: utf-8 -*-
"""Müşteri alan adı (domain) bağlama.

Akış: firma (veya sahip) alan adını yazar → panel DNS kayıtlarını gösterir → "Kontrol et" ile DNS doğrulanır →
istek o alan adından gelince firmanın verisi ve seçtiği tema siteyi açar. Sahip tarafında yalnız cPanel'de
"Takma alan adı (Alias)" eklenir; kalan her şey buradan yönetilir.

Eşleme dosyası (firm_domains.json) WSGI katmanı tarafından okunur; böylece statik/panel yolları uygulama
açılmadan doğru firmaya yönlendirilir.
"""
import html as _html
import json
import os
import re
import socket
import time
import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

import tenant

HERE = os.path.dirname(os.path.abspath(__file__))
MAP_FILE = os.path.join(HERE, "firm_domains.json")
PLATFORM_HOST = "onlinekaydet.com"
_DOM = re.compile(r"^(?=.{4,190}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}$")
_cache = {"t": 0, "m": {}}


def _now():
    return datetime.now(timezone.utc).isoformat()


def norm_domain(v: str) -> str:
    v = (v or "").strip().lower()
    v = re.sub(r"^[a-z]+://", "", v).split("/")[0].split("?")[0].split(":")[0].strip(".")
    if v.startswith("www."):
        v = v[4:]
    try:
        v = v.encode("idna").decode("ascii")
    except Exception:          # noqa: BLE001
        pass
    if not _DOM.match(v):
        raise HTTPException(422, "Geçerli bir alan adı yazın (örnek: firmaadi.com)")
    if v == PLATFORM_HOST or v.endswith("." + PLATFORM_HOST):
        raise HTTPException(422, "Bu alan adı platforma aittir")
    return v


def server_ips():
    try:
        return sorted(set(socket.gethostbyname_ex(PLATFORM_HOST)[2]))
    except Exception:          # noqa: BLE001
        return []


def dns_state(domain: str):
    """A kaydı sunucuya mı bakıyor? (alan adı ve www için)"""
    ips = set(server_ips())
    res = {"server_ips": sorted(ips)}
    for key, host in (("root", domain), ("www", "www." + domain)):
        try:
            got = set(socket.gethostbyname_ex(host)[2])
        except Exception:      # noqa: BLE001
            got = set()
        res[key] = {"host": host, "ips": sorted(got), "ok": bool(got & ips) if ips else False}
    return res


async def write_map(db):
    m = {}
    async for d in db.main().firm_domains.find({"status": {"$in": ["dns_ok", "yayinda"]}}, {"_id": 0}):
        m[d["domain"]] = {"fid": d["firm_id"], "db": d["db"]}
        m["www." + d["domain"]] = {"fid": d["firm_id"], "db": d["db"]}
    tmp = MAP_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(m, f)
    os.replace(tmp, MAP_FILE)
    _cache["t"] = 0


async def host_to_firm(db, host: str):
    """Ana veritabanından alan adı → firma (60 sn önbellekli)."""
    host = (host or "").lower().split(":")[0]
    if not host or host == PLATFORM_HOST or host.endswith("." + PLATFORM_HOST):
        return None
    if time.time() - _cache["t"] > 60:
        m = {}
        async for d in db.main().firm_domains.find({"status": {"$in": ["dns_ok", "yayinda"]}}, {"_id": 0}):
            m[d["domain"]] = d
            m["www." + d["domain"]] = d
        _cache["m"], _cache["t"] = m, time.time()
    return _cache["m"].get(host)


def portal_chip(url: str) -> str:
    """Tema sayfasına, müşteri portalına (servis takibi) giden küçük sabit bağlantı."""
    return ('<a href="%s" style="position:fixed;left:14px;bottom:14px;z-index:99998;background:#0a1f44;color:#fff;font:600 13px/1 system-ui,sans-serif;'
            'padding:11px 15px;border-radius:999px;text-decoration:none;box-shadow:0 6px 18px rgba(10,31,68,.35)">Servis takibi · Müşteri girişi</a>' % _html.escape(url, quote=True))


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]
    THEMES = deps.get("themes") or []

    def firm_admin(user):
        if not tenant.current():
            raise HTTPException(403, "Yalnızca firma hesabı")
        if user.get("role") != "admin":
            raise HTTPException(403, "Yalnızca firma yöneticisi")

    async def my_firm():
        d = tenant.current()
        f = await db.main().firms.find_one({"db": d}, {"_id": 0}) if d else None
        if not f:
            raise HTTPException(404, "Firma bulunamadı")
        return f

    def instructions(domain):
        ips = server_ips()
        ip = ips[0] if ips else "SUNUCU_IP"
        return {"server_ip": ip, "records": [
            {"type": "A", "host": "@", "value": ip, "note": "alan adının kendisi"},
            {"type": "A", "host": "www", "value": ip, "note": "www.%s" % domain}],
            "steps": [
                "Alan adını aldığınız firmanın (GoDaddy, Natro, Turhost, İsimtescil…) paneline girin; 'DNS Yönetimi' bölümünü açın.",
                "Var olan @ ve www A kayıtlarını silin, yukarıdaki iki A kaydını ekleyin (TTL 300 veya otomatik).",
                "Yayılması 5 dakika ile birkaç saat sürebilir. 'Kontrol et' düğmesi doğrulanınca site otomatik yayına alınır.",
                "SSL (https) sertifikası alan adı yönlenince kendiliğinden kurulur; ek işlem gerekmez."]}

    async def add_domain(f, domain, by):
        if await db.main().firm_domains.find_one({"domain": domain}, {"_id": 0}):
            ex = await db.main().firm_domains.find_one({"domain": domain, "firm_id": f["id"]}, {"_id": 0})
            if ex:
                return ex
            raise HTTPException(409, "Bu alan adı başka bir firmaya bağlı")
        n = await db.main().firm_domains.count_documents({"firm_id": f["id"]})
        if n >= 5:
            raise HTTPException(422, "Bir firmaya en fazla 5 alan adı bağlanabilir")
        doc = {"id": uuid.uuid4().hex[:12], "domain": domain, "firm_id": f["id"], "db": f["db"], "firm_name": f.get("name", ""),
               "status": "beklemede", "created_at": _now(), "created_by": by, "checked_at": "", "dns": {}}
        await db.main().firm_domains.insert_one(dict(doc))
        return doc

    async def check_domain(domain):
        d = await db.main().firm_domains.find_one({"domain": domain}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Alan adı kayıtlı değil")
        st = dns_state(domain)
        new = "yayinda" if (st["root"]["ok"]) else "beklemede"
        if d["status"] == "yayinda" and new == "beklemede":
            new = "yayinda"                       # bir kez yayına alınan alan adı geçici DNS hatasında kapanmaz
        await db.main().firm_domains.update_one({"domain": domain}, {"$set": {"status": new, "checked_at": _now(), "dns": st}})
        await write_map(db)
        return {**d, "status": new, "dns": st, "checked_at": _now()}

    def pub(d):
        return {k: d.get(k, "") for k in ("id", "domain", "status", "created_at", "checked_at", "dns", "firm_id", "firm_name")}

    # ------------------------------------------------------------ firma
    @api_router.get("/firm/domain")
    async def fd_get(user: dict = Depends(get_current_user)):
        firm_admin(user)
        f = await my_firm()
        rows = await db.main().firm_domains.find({"firm_id": f["id"]}, {"_id": 0}).to_list(10)
        return {"domains": [pub(r) for r in rows], "help": instructions(rows[0]["domain"] if rows else "alanadiniz.com")}

    @api_router.post("/firm/domain")
    async def fd_add(body: dict, user: dict = Depends(get_current_user)):
        firm_admin(user)
        f = await my_firm()
        d = await add_domain(f, norm_domain(body.get("domain")), "firma")
        return {"domain": pub(d), "help": instructions(d["domain"])}

    @api_router.post("/firm/domain/check")
    async def fd_check(body: dict, user: dict = Depends(get_current_user)):
        firm_admin(user)
        f = await my_firm()
        dom = norm_domain(body.get("domain"))
        if not await db.main().firm_domains.find_one({"domain": dom, "firm_id": f["id"]}, {"_id": 0}):
            raise HTTPException(404, "Alan adı bulunamadı")
        return pub(await check_domain(dom))

    @api_router.delete("/firm/domain/{domain}")
    async def fd_del(domain: str, user: dict = Depends(get_current_user)):
        firm_admin(user)
        f = await my_firm()
        await db.main().firm_domains.delete_one({"domain": norm_domain(domain), "firm_id": f["id"]})
        await write_map(db)
        return {"ok": True}

    # ------------------------------------------------------------ sahip
    @api_router.get("/admin/domains")
    async def ad_list(me: dict = Depends(require_admin)):
        if tenant.current():
            raise HTTPException(403, "Yalnızca platform sahibi")
        rows = await db.main().firm_domains.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
        return {"domains": [pub(r) for r in rows], "server_ips": server_ips()}

    @api_router.post("/admin/firms/{fid}/domains")
    async def ad_add(fid: str, body: dict, me: dict = Depends(require_admin)):
        if tenant.current():
            raise HTTPException(403, "Yalnızca platform sahibi")
        f = await db.main().firms.find_one({"id": fid}, {"_id": 0})
        if not f:
            raise HTTPException(404, "Firma bulunamadı")
        d = await add_domain(f, norm_domain(body.get("domain")), "sahip")
        return {"domain": pub(d), "help": instructions(d["domain"])}

    @api_router.post("/admin/domains/{domain}/check")
    async def ad_check(domain: str, me: dict = Depends(require_admin)):
        if tenant.current():
            raise HTTPException(403, "Yalnızca platform sahibi")
        return pub(await check_domain(norm_domain(domain)))

    @api_router.put("/admin/domains/{domain}/status")
    async def ad_status(domain: str, body: dict, me: dict = Depends(require_admin)):
        if tenant.current():
            raise HTTPException(403, "Yalnızca platform sahibi")
        st = body.get("status")
        if st not in ("beklemede", "yayinda", "kapali"):
            raise HTTPException(422, "Geçersiz durum")
        await db.main().firm_domains.update_one({"domain": norm_domain(domain)}, {"$set": {"status": st, "checked_at": _now()}})
        await write_map(db)
        return {"ok": True}

    @api_router.delete("/admin/domains/{domain}")
    async def ad_del(domain: str, me: dict = Depends(require_admin)):
        if tenant.current():
            raise HTTPException(403, "Yalnızca platform sahibi")
        await db.main().firm_domains.delete_one({"domain": norm_domain(domain)})
        await write_map(db)
        return {"ok": True}

    # ------------------------------------------------------------ yayın: alan adından gelen ziyaretçiye site
    @api_router.get("/public/hosted-site")
    async def hosted_site(request: Request):
        host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or "").split(":")[0].lower()
        if not tenant.current():
            return HTMLResponse("<!doctype html><meta charset=utf-8><title>Site bulunamadı</title><p style='font:16px system-ui;padding:40px'>Bu alan adı için yayınlanmış bir site yok.</p>", status_code=404)
        brand = await db.app_settings.find_one({"_id": "brand"}, {"_id": 0}) or {}
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        f = await db.main().firms.find_one({"db": tenant.current()}, {"_id": 0, "name": 1, "phone": 1}) or {}
        name = g.get("company_name") or f.get("name") or "Teknik Servis"
        tel = g.get("company_phone") or f.get("phone") or ""
        slug = brand.get("theme") or ""
        th = next((t for t in THEMES if t["slug"] == slug), None)
        path = os.path.join(HERE, "..", "themes", "html", slug + ".html") if th else ""
        if not (th and os.path.isfile(path)):
            e = _html.escape
            return HTMLResponse(
                "<!doctype html><html lang=tr><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>%s</title></head>"
                "<body style=\"margin:0;font:16px/1.6 system-ui,sans-serif;background:#0a1f44;color:#fff;display:grid;place-items:center;min-height:100vh;text-align:center\">"
                "<div style='padding:24px'><h1 style='margin:0 0 8px'>%s</h1><p style='opacity:.8'>Sitemiz çok yakında yayında.</p>%s</div></body></html>"
                % (e(name), e(name), ("<p><a style='color:#f6a35c;font-weight:700;font-size:20px;text-decoration:none' href='tel:%s'>%s</a></p>" % (e(re.sub(r"[^\d+]", "", tel)), e(tel))) if tel else ""))
        html = open(path, encoding="utf-8").read()
        html = html.replace("__API_URL__", "/api").replace("__PORTAL_URL__", "#")
        if th.get("name") and name:
            html = html.replace(th["name"], name)
        digits = "".join(ch for ch in tel if ch.isdigit())
        if len(digits) >= 10:
            dd = digits[-10:]
            html = html.replace("905320000000", "90" + dd).replace("0532 000 00 00", "0%s %s %s %s" % (dd[:3], dd[3:6], dd[6:8], dd[8:]))
        fd = await db.main().firms.find_one({"db": tenant.current()}, {"_id": 0, "id": 1, "modules": 1}) or {}
        if fd.get("id") and (fd.get("modules") is None or "portal" in (fd.get("modules") or [])):
            html = html.replace("</body>", portal_chip("/portal/%s~giris" % fd["id"]) + "</body>", 1) if "</body>" in html else html + portal_chip("/portal/%s~giris" % fd["id"])
        return HTMLResponse(html, headers={"Cache-Control": "no-cache"})

    # ------------------------------------------------------------ sahip: kurulum hazırlığı ve sistem durumu
    @api_router.get("/admin/readiness")
    async def readiness(me: dict = Depends(require_admin)):
        """Her firma için kurulum kontrol listesi: telefon, logo, tema, alan adı, SMS, kullanıcı, ilk iş."""
        if tenant.current():
            raise HTTPException(403, "Yalnızca platform sahibi")
        doms = {}
        async for d in db.main().firm_domains.find({}, {"_id": 0}):
            doms.setdefault(d["firm_id"], []).append(d)
        out = []
        for f in await db.main().firms.find({}, {"_id": 0}).sort("created_at", -1).to_list(300):
            fdb = db.firm(f["db"])
            try:
                g = await fdb.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
                lg = await fdb.app_settings.find_one({"_id": "firm_logo"}, {"_id": 0}) or {}
                br = await fdb.app_settings.find_one({"_id": "brand"}, {"_id": 0}) or {}
                ig = await fdb.app_settings.find_one({"_id": "integrations"}, {"_id": 0}) or {}
                users = await fdb.users.count_documents({})
                jobs = await fdb.jobs.count_documents({})
            except Exception:          # noqa: BLE001
                g = lg = br = ig = {}
                users = jobs = 0
            dl = doms.get(f["id"], [])
            items = [("Firma telefonu", bool(g.get("company_phone"))), ("Logo", bool(lg.get("data"))), ("Site teması seçildi", bool(br.get("theme"))),
                     ("Alan adı bağlandı", any(x["status"] == "yayinda" for x in dl)), ("SMS doğrulandı", bool(ig.get("sms_verified"))),
                     ("Personel eklendi", users > 1), ("İlk servis kaydı", jobs > 0)]
            out.append({"id": f["id"], "name": f.get("name", ""), "status": f.get("status", ""), "domains": [x["domain"] for x in dl],
                        "items": [{"k": k, "ok": ok} for k, ok in items], "done": sum(1 for _, ok in items if ok), "total": len(items)})
        return {"firms": out}

    @api_router.post("/admin/demo-cleanup")
    async def demo_cleanup(payload: dict, me: dict = Depends(require_admin)):
        """Süresi dolmuş demo firmaları (ve isteğe bağlı verilen firma kimliklerini) tüm verisiyle siler. Yalnızca platform sahibi."""
        if tenant.current():
            raise HTTPException(403, "Yalnızca platform sahibi")
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        ids = set(str(x) for x in (payload.get("ids") or []))
        removed = []
        for f in await db.main().firms.find({}, {"_id": 0}).to_list(5000):
            expired = f.get("demo") and (f.get("expires_at") or "9") < now and payload.get("expired", True)
            if f["id"] in ids or expired:
                try:
                    await db._client.drop_database(f["db"])
                except Exception:
                    pass
                await db.main().firm_logins.delete_many({"db": f["db"]})
                await db.main().firm_domains.delete_many({"firm_id": f["id"]})
                await db.main().firms.delete_one({"id": f["id"]})
                removed.append(f.get("name"))
        return {"ok": True, "removed": removed}

    @api_router.get("/admin/system")
    async def system_info(me: dict = Depends(require_admin)):
        if tenant.current():
            raise HTTPException(403, "Yalnızca platform sahibi")
        import platform
        import shutil
        info = {"python": platform.python_version(), "server_ips": server_ips()}
        try:
            u = shutil.disk_usage(HERE)
            info["disk"] = {"total_gb": round(u.total / 1e9, 1), "used_gb": round((u.total - u.free) / 1e9, 1)}
        except Exception:              # noqa: BLE001
            info["disk"] = None
        info["firms"] = await db.main().firms.count_documents({})
        info["domains"] = {"total": await db.main().firm_domains.count_documents({}), "live": await db.main().firm_domains.count_documents({"status": "yayinda"})}
        try:
            info["mongo_ms"] = None
            t0 = time.time()
            await db.main().command("ping")
            info["mongo_ms"] = round((time.time() - t0) * 1000)
        except Exception:              # noqa: BLE001
            pass
        try:
            ep = os.path.join(HERE, "startup-error.log")
            info["error_log"] = open(ep, encoding="utf-8", errors="ignore").read()[-1500:] if os.path.isfile(ep) else ""
        except Exception:              # noqa: BLE001
            info["error_log"] = ""
        info["themes"] = len(THEMES)
        return info
