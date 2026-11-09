# -*- coding: utf-8 -*-
"""Firma sitesi düzenleyici: müşteri, seçtiği temanın metin, görsel, bağlantı ve alt bilgisini (footer) olduğu gibi düzenler;
yeni sayfa açar. Düzenlenmiş site, firmanın alan adından (hosted-site) yayınlanır.

Saklama: app_settings _id "site_custom" -> {"html": "<ana sayfa>", "pages": [{"slug","title","html"}], "updated_at"}
Ana sayfa özel HTML'i yoksa seçili temadan üretilir; "Sıfırla" özel HTML'i siler.
"""
import html as _html
import os
import re
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

import tenant

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_HTML = 6_000_000
RESERVED = {"api", "admin", "tech", "giris", "login", "panel", "uye-girisi", "portal", "takip", "static", "uploads", "fonts", "brand", "index", "sitemap", "robots"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def clean_html(h: str) -> str:
    """Düzenleyiciden gelen izleri temizler."""
    h = str(h or "")
    h = re.sub(r"<(style|script)[^>]*data-spx-ed[^>]*>.*?</\1>", "", h, flags=re.S | re.I)
    h = re.sub(r"\scontenteditable(=\"[^\"]*\"|='[^']*'|=[^\s>]*)?", "", h, flags=re.I)
    h = re.sub(r"\sdata-spx-[a-z-]+(=\"[^\"]*\")?", "", h, flags=re.I)
    return h


def page_template(title: str, name: str, tel: str, dark: str, accent: str) -> str:
    e = _html.escape
    telhref = re.sub(r"[^\d+]", "", tel or "")
    return (
        '<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>%(t)s · %(n)s</title><style>*{box-sizing:border-box}body{margin:0;font:17px/1.7 system-ui,-apple-system,'Segoe UI',sans-serif;color:#1c2430;background:#fff}"
        "header{background:%(d)s;color:#fff}.w{max-width:1000px;margin:0 auto;padding:0 22px}.hd{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:68px}"
        ".hd a{color:#fff;text-decoration:none;font-weight:700}.hd .tel{background:%(a)s;padding:10px 16px;border-radius:999px;font-size:15px}"
        "main{padding:54px 0 70px}h1{font-size:clamp(30px,5vw,46px);line-height:1.15;margin:0 0 18px;color:%(d)s}h2{margin:34px 0 10px;color:%(d)s}p{margin:0 0 16px}"
        "footer{background:%(d)s;color:#cdd6e4;padding:30px 0;font-size:15px}footer a{color:#fff}</style></head><body>"
        '<header><div class="w hd"><a href="/">%(n)s</a><a class="tel" href="tel:%(th)s">%(tel)s</a></div></header>'
        '<main><div class="w"><h1>%(t)s</h1><p>Bu metni tıklayıp yazarak düzenleyin. Başlık, paragraf, resim ve bağlantıları değiştirebilirsiniz.</p>'
        "<h2>Alt başlık</h2><p>Hizmetleriniz, çalışma saatleriniz veya hakkınızda bilgiyi buraya yazın.</p></div></main>"
        '<footer><div class="w">© %(n)s · <a href="/">Ana sayfa</a></div></footer></body></html>'
    ) % {"t": e(title), "n": e(name), "d": dark or "#0a1f44", "a": accent or "#f27a1a", "th": e(telhref), "tel": e(tel or "")}


def compose_page(home: str, title: str, content: str):
    """Ana sayfanın <head>, üst bilgi, alt bilgi ve betikleriyle yeni sayfa kurar (tema görünümü korunur). Başarısızsa None."""
    try:
        hm = re.search(r"<head[^>]*>(.*?)</head>", home, re.S | re.I)
        bm = re.search(r"<body[^>]*>", home, re.I)
        if not (hm and bm):
            return None
        head = re.sub(r"<title>.*?</title>", "", hm.group(1), flags=re.S | re.I)
        head = re.sub(r"<meta[^>]+name=[\"']description[\"'][^>]*>", "", head, flags=re.I)
        hd = re.search(r"<header\b.*?</header>", home, re.S | re.I)
        ft = re.findall(r"<footer\b.*?</footer>", home, re.S | re.I)
        if not hd and not ft:
            return None
        scripts = "".join(re.findall(r"<script\b(?![^>]*\bsrc=[\"']?https?://(?:www\.)?(?:googletagmanager|google-analytics))[^>]*>.*?</script>", home[bm.end():], re.S | re.I))
        return ("<!DOCTYPE html><html lang=\"tr\"><head>%s<title>%s</title></head>%s%s<main>%s</main>%s%s</body></html>"
                % (head, _html.escape(title), bm.group(0), hd.group(0) if hd else "", content, ft[-1] if ft else "", scripts))
    except Exception:
        return None


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    THEMES = deps.get("themes") or []
    portal_chip = deps.get("portal_chip")

    def need_firm():
        if not tenant.current():
            raise HTTPException(403, "Yalnızca firma hesabı")

    async def identity():
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        f = await db.main().firms.find_one({"db": tenant.current()}, {"_id": 0, "id": 1, "name": 1, "phone": 1, "modules": 1}) or {}
        return (g.get("company_name") or f.get("name") or "Teknik Servis"), (g.get("company_phone") or f.get("phone") or ""), f

    async def theme_html():
        brand = await db.app_settings.find_one({"_id": "brand"}, {"_id": 0}) or {}
        name, tel, _ = await identity()
        slug = brand.get("theme") or ""
        th = next((t for t in THEMES if t["slug"] == slug), None)
        if not th:
            return None
        p = os.path.join(HERE, "..", "themes", "html", slug + ".html")
        if not os.path.isfile(p):
            return None
        h = open(p, encoding="utf-8").read().replace("__API_URL__", "/api").replace("__PORTAL_URL__", "#")
        if th.get("name") and name:
            h = h.replace(th["name"], name)
        d = "".join(ch for ch in (tel or "") if ch.isdigit())
        if len(d) >= 10:
            d = d[-10:]
            h = h.replace("905320000000", "90" + d).replace("0532 000 00 00", "0%s %s %s %s" % (d[:3], d[3:6], d[6:8], d[8:]))
        return h

    async def doc():
        return await db.app_settings.find_one({"_id": "site_custom"}, {"_id": 0}) or {}

    # ---------------------------------------------------------------- düzenleyici API
    @api_router.get("/site/edit")
    async def edit_get(page: str = "", _: dict = Depends(require_admin)):
        need_firm()
        d = await doc()
        pages = [{"slug": p["slug"], "title": p.get("title", p["slug"])} for p in d.get("pages", [])]
        if page:
            p = next((x for x in d.get("pages", []) if x["slug"] == page), None)
            if not p:
                raise HTTPException(404, "Sayfa bulunamadı")
            return {"html": p["html"], "custom": True, "pages": pages, "page": page, "title": p.get("title", page)}
        if d.get("html"):
            return {"html": d["html"], "custom": True, "pages": pages, "page": ""}
        h = await theme_html()
        if h is None:
            raise HTTPException(400, "Önce bir tema seçip kaydedin")
        return {"html": h, "custom": False, "pages": pages, "page": ""}

    @api_router.put("/site/edit")
    async def edit_put(payload: dict, _: dict = Depends(require_admin)):
        need_firm()
        h = clean_html(payload.get("html"))
        if len(h) < 50 or len(h) > MAX_HTML:
            raise HTTPException(422, "Sayfa boyutu geçersiz (en fazla 6 MB)")
        page = str(payload.get("page") or "")
        d = await doc()
        if page:
            pages = d.get("pages", [])
            p = next((x for x in pages if x["slug"] == page), None)
            if not p:
                raise HTTPException(404, "Sayfa bulunamadı")
            p["html"] = h
            if payload.get("title"):
                p["title"] = str(payload["title"]).strip()[:80]
            await db.app_settings.update_one({"_id": "site_custom"}, {"$set": {"pages": pages, "updated_at": _now()}}, upsert=True)
        else:
            await db.app_settings.update_one({"_id": "site_custom"}, {"$set": {"html": h, "updated_at": _now()}}, upsert=True)
        return {"ok": True}

    @api_router.delete("/site/edit")
    async def edit_reset(page: str = "", _: dict = Depends(require_admin)):
        need_firm()
        d = await doc()
        if page:
            await db.app_settings.update_one({"_id": "site_custom"}, {"$set": {"pages": [p for p in d.get("pages", []) if p["slug"] != page]}}, upsert=True)
        else:
            await db.app_settings.update_one({"_id": "site_custom"}, {"$unset": {"html": ""}}, upsert=True)
        return {"ok": True}

    @api_router.post("/site/pages")
    async def page_new(payload: dict, _: dict = Depends(require_admin)):
        need_firm()
        title = " ".join(str(payload.get("title") or "").split())[:80]
        if len(title) < 2:
            raise HTTPException(422, "Sayfa başlığı yazın")
        tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
        slug = re.sub(r"[^a-z0-9]+", "-", title.translate(tr).lower()).strip("-")[:40] or "sayfa"
        d = await doc()
        pages = d.get("pages", [])
        if len(pages) >= 30:
            raise HTTPException(422, "En fazla 30 sayfa açılabilir")
        base, n = slug, 2
        while slug in RESERVED or any(p["slug"] == slug for p in pages):
            slug, n = "%s-%d" % (base, n), n + 1
        brand = await db.app_settings.find_one({"_id": "brand"}, {"_id": 0}) or {}
        name, tel, _f = await identity()
        content = clean_html(payload.get("content") or "") or ('<section style="max-width:960px;margin:0 auto;padding:56px 22px"><h1>%s</h1><p>Bu metni düzenleyin.</p></section>' % _html.escape(title))
        home = d.get("html") or await theme_html() or ""
        full = compose_page(home, title, content) if home else None
        pages.append({"slug": slug, "title": title, "html": full or page_template(title, name, tel, brand.get("dark"), brand.get("accent"))})
        await db.app_settings.update_one({"_id": "site_custom"}, {"$set": {"pages": pages, "updated_at": _now()}}, upsert=True)
        return {"ok": True, "slug": slug, "title": title}

    @api_router.put("/site/logo")
    async def logo_put(payload: dict, _: dict = Depends(require_admin)):
        need_firm()
        data = str(payload.get("data") or "")
        if data and not re.match(r"^data:image/(png|jpeg|webp|gif|svg\+xml);base64,[A-Za-z0-9+/=]+$", data):
            raise HTTPException(422, "Logo bir resim dosyası olmalı (PNG, JPG, WEBP, SVG)")
        if len(data) > 1_500_000:
            raise HTTPException(422, "Logo çok büyük (en fazla ~1 MB)")
        await db.app_settings.update_one({"_id": "firm_logo"}, {"$set": {"data": data}}, upsert=True)
        await db.app_settings.update_one({"_id": "global"}, {"$set": {"has_logo": bool(data)}}, upsert=True)
        return {"ok": True}

    @api_router.get("/site/logo")
    async def logo_get(_: dict = Depends(require_admin)):
        need_firm()
        d = await db.app_settings.find_one({"_id": "firm_logo"}, {"_id": 0}) or {}
        return {"data": d.get("data") or ""}

    @api_router.put("/site/pages/{slug}")
    async def page_meta(slug: str, payload: dict, _: dict = Depends(require_admin)):
        need_firm()
        d = await doc()
        pages = d.get("pages", [])
        p = next((x for x in pages if x["slug"] == slug), None)
        if not p:
            raise HTTPException(404, "Sayfa bulunamadı")
        if payload.get("title"):
            p["title"] = " ".join(str(payload["title"]).split())[:80]
        ns = str(payload.get("slug") or "").strip().lower()
        if ns and ns != slug:
            if not re.fullmatch(r"[a-z0-9-]{1,40}", ns) or ns in RESERVED or any(x["slug"] == ns for x in pages):
                raise HTTPException(422, "Bu adres kullanılamaz (a-z, 0-9 ve tire; başka sayfada kullanılmamış olmalı)")
            p["slug"] = ns
        await db.app_settings.update_one({"_id": "site_custom"}, {"$set": {"pages": pages, "updated_at": _now()}}, upsert=True)
        return {"ok": True, "slug": p["slug"], "title": p["title"]}

    # ---------------------------------------------------------------- yayın (domains.hosted_site çağırır)
    async def serve(path: str):
        """Firma bağlamı kurulmuşken, istenen yol için düzenlenmiş HTML (yoksa None)."""
        d = await doc()
        if not d:
            return None
        p = (path or "/").split("?")[0].strip("/")
        if p.endswith(".html"):
            p = p[:-5]
        h = None
        if p in ("", "index"):
            h = d.get("html")
            if h is None:
                return None
        else:
            pg = next((x for x in d.get("pages", []) if x["slug"] == p), None)
            if not pg:
                return None
            h = pg["html"]
        _n, _t, f = await identity()
        if portal_chip and f.get("id") and (f.get("modules") is None or "portal" in (f.get("modules") or [])):
            chip = portal_chip("/portal/%s~giris" % f["id"])
            h = h.replace("</body>", chip + "</body>", 1) if "</body>" in h else h + chip
        return h

    api_router.site_custom_serve = serve
