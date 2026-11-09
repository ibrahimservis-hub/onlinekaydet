# -*- coding: utf-8 -*-
"""Firma sitesi düzenleyici: müşteri, seçtiği temanın metin, görsel, bağlantı ve alt bilgisini (footer) olduğu gibi düzenler;
yeni sayfa açar. Düzenlenmiş site, firmanın alan adından (hosted-site) yayınlanır.

Saklama: app_settings _id "site_custom" -> {"html": "<ana sayfa>", "pages": [{"slug","title","html"}], "updated_at"}
Ana sayfa özel HTML'i yoksa seçili temadan üretilir; "Sıfırla" özel HTML'i siler.
"""
import base64
import hashlib
import html as _html
import io
import os
import re
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

import shop as shopmod
import shop_legal
import storefront
import sitegen
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

    _raw_cache = {}

    def raw_theme(slug):
        if slug not in _raw_cache:
            p = os.path.join(HERE, "..", "themes", "html", slug + ".html")
            if not os.path.isfile(p):
                return None
            if len(_raw_cache) > 5:
                _raw_cache.clear()
            _raw_cache[slug] = open(p, encoding="utf-8").read()
        return _raw_cache[slug]

    async def build_ctx(inline=False):
        """Tema + firma profili bağlamı. Tema seçili değilse None."""
        brand = await db.app_settings.find_one({"_id": "brand"}, {"_id": 0}) or {}
        th = next((t for t in THEMES if t["slug"] == (brand.get("theme") or "")), None)
        if not th or raw_theme(th["slug"]) is None:
            return None
        name, tel, _f = await identity()
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        prof = await db.app_settings.find_one({"_id": "site_profile"}, {"_id": 0}) or {}
        sector = th.get("sector") or ""
        p = sitegen.effective(prof, sector)
        p["address"] = prof.get("address") or g.get("company_address") or ""
        imgs = {}
        keys = [x["k"] for x in (p.get("slides") or []) + (p.get("gallery") or [])] + [e["img"] for e in (p.get("extra_pages") or []) if e.get("img")]
        if inline and keys:
            async for r in db.site_images.find({"_id": {"$in": keys}}):
                imgs[r["_id"]] = "data:%s;base64,%s" % (r.get("mime") or "image/jpeg", base64.b64encode(bytes(r["data"])).decode())
        lg = (await db.app_settings.find_one({"_id": "firm_logo"}, {"_id": 0}) or {}).get("data") or ""
        logo = lg if inline else (("/api/public/site-logo?v=" + hashlib.sha1(lg.encode()).hexdigest()[:8]) if lg else "")
        feats = await db.app_settings.find_one({"_id": "site_features"}, {"_id": 0}) or {}
        legal = list(shop_legal.SLUGS) if feats.get("shop_enabled") else []
        return {"th": th, "name": name, "tel": tel, "p": p, "sector": sector, "logo": logo, "city": prof.get("city") or "", "legal": legal, "shop_on": bool(feats.get("shop_enabled")),
                "img": (lambda k: imgs.get(k, "")) if inline else (lambda k: "/api/public/site-img/" + k),
                "logo_abs": "/api/public/site-logo" if lg else ""}

    async def themed_home(ctx):
        return sitegen.apply_profile(raw_theme(ctx["th"]["slug"]), ctx["th"], ctx)

    async def theme_html():
        ctx = await build_ctx(inline=True)
        return await themed_home(ctx) if ctx else None

    _PUB = re.compile(r"/api/public/site-img/([a-f0-9]{16})")

    async def inline_imgs(h):
        """Düzenleyici için: herkese açık görsel adreslerini gömülü veriye çevirir."""
        keys = set(_PUB.findall(h))
        m = {}
        for k in keys:
            r = await db.site_images.find_one({"_id": k})
            if r:
                m[k] = "data:%s;base64,%s" % (r.get("mime") or "image/jpeg", base64.b64encode(bytes(r["data"])).decode())
        h = _PUB.sub(lambda x: m.get(x.group(1), x.group(0)), h)
        if "/api/public/site-logo" in h:
            lg = (await db.app_settings.find_one({"_id": "firm_logo"}, {"_id": 0}) or {}).get("data") or ""
            if lg:
                h = re.sub(r"/api/public/site-logo\?v=[a-f0-9]{8}", lambda x: lg, h)
        return h

    async def externalize_imgs(h):
        """Kaydederken: gömülü site görsellerini ve logoyu kısa adreslere çevirir (sayfa küçük kalır)."""
        def key_for(b64):
            try:
                return hashlib.sha1(base64.b64decode(b64)).hexdigest()[:16]
            except Exception:           # noqa: BLE001
                return ""
        found = {}
        for m in re.finditer(r"data:image/jpeg;base64,([A-Za-z0-9+/=]{2000,})", h):
            k = key_for(m.group(1))
            if k and k not in found:
                found[k] = bool(await db.site_images.find_one({"_id": k}, {"_id": 1}))
        h = re.sub(r"data:image/jpeg;base64,([A-Za-z0-9+/=]{2000,})", lambda m: ("/api/public/site-img/" + key_for(m.group(1))) if found.get(key_for(m.group(1))) else m.group(0), h)
        lg = (await db.app_settings.find_one({"_id": "firm_logo"}, {"_id": 0}) or {}).get("data") or ""
        if lg and lg in h:
            h = h.replace(lg, "/api/public/site-logo?v=" + hashlib.sha1(lg.encode()).hexdigest()[:8])
        return h

    async def doc():
        return await db.app_settings.find_one({"_id": "site_custom"}, {"_id": 0}) or {}

    # ---------------------------------------------------------------- düzenleyici API
    async def auto_list(d):
        ctx = await build_ctx()
        if not ctx:
            return []
        have = {p["slug"] for p in d.get("pages", [])}
        return [{"slug": x["slug"], "title": x["title"], "auto": True, "kind": x["kind"]} for x in sitegen.page_index(ctx) if x["slug"] not in have]

    @api_router.get("/site/edit")
    async def edit_get(page: str = "", _: dict = Depends(require_admin)):
        need_firm()
        d = await doc()
        pages = [{"slug": p["slug"], "title": p.get("title", p["slug"]), "kind": "saved"} for p in d.get("pages", [])] + await auto_list(d)
        if page:
            p = next((x for x in d.get("pages", []) if x["slug"] == page), None)
            if p:
                _c = await build_ctx(inline=True)
                _h = sitegen.rebase(p["html"], await themed_home(_c), _c, p.get("title") or page, page) if _c else p["html"]
                return {"html": await inline_imgs(_h), "custom": True, "pages": pages, "page": page, "title": p.get("title", page)}
            ctx = await build_ctx(inline=True)
            home = (await themed_home(ctx)) if ctx else (d.get("html") or "")
            r = sitegen.render_page(home, ctx, page) if ctx else None
            if not r:
                raise HTTPException(404, "Sayfa bulunamadı")
            return {"html": r[0], "custom": False, "pages": pages, "page": page, "title": r[1]}
        _cc = await build_ctx()
        if d.get("html") and not (_cc and d.get("home_theme") and d["home_theme"] != _cc["th"]["slug"]):
            return {"html": await inline_imgs(d["html"]), "custom": True, "pages": pages, "page": ""}
        h = await theme_html()
        if h is None:
            raise HTTPException(400, "Önce bir tema seçip kaydedin")
        return {"html": h, "custom": False, "pages": pages, "page": ""}

    @api_router.put("/site/edit")
    async def edit_put(payload: dict, _: dict = Depends(require_admin)):
        need_firm()
        h = await externalize_imgs(clean_html(payload.get("html")))
        if len(h) < 50 or len(h) > MAX_HTML:
            raise HTTPException(422, "Sayfa boyutu geçersiz (en fazla 6 MB)")
        page = str(payload.get("page") or "")
        d = await doc()
        if page:
            pages = d.get("pages", [])
            p = next((x for x in pages if x["slug"] == page), None)
            if not p:
                ctx = await build_ctx()
                au = next((x for x in sitegen.page_index(ctx) if x["slug"] == page), None) if ctx else None
                if not au:
                    raise HTTPException(404, "Sayfa bulunamadı")
                p = {"slug": page, "title": au["title"], "html": h}
                pages.append(p)
            p["html"] = h
            if payload.get("title"):
                p["title"] = str(payload["title"]).strip()[:80]
            await db.app_settings.update_one({"_id": "site_custom"}, {"$set": {"pages": pages, "updated_at": _now()}}, upsert=True)
        else:
            _cx2 = await build_ctx()
            await db.app_settings.update_one({"_id": "site_custom"}, {"$set": {"html": h, "updated_at": _now(), "home_theme": _cx2["th"]["slug"] if _cx2 else ""}}, upsert=True)
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
        home = await theme_html() or d.get("html") or ""
        _cx = await build_ctx()
        full = (sitegen.assemble(home, _cx, title, content) if (_cx and home) else None) or (compose_page(home, title, content) if home else None)
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

    # ---------------------------------------------------------------- firma profili (Sitem)
    def _t(v, n):
        return " ".join(str(v or "").split())[:n]

    sitegen_reserved = set(RESERVED) | {"hakkimizda", "hizmetlerimiz", "galeri", "nasil-calisiyoruz", "sss", "hizmet-bolgeleri", "iletisim"}

    async def san_profile(x):
        out = {"whatsapp": _t(x.get("whatsapp"), 20), "email": _t(x.get("email"), 80), "address": _t(x.get("address"), 200),
               "hours": _t(x.get("hours"), 120), "seo_title": _t(x.get("seo_title"), 70), "seo_desc": _t(x.get("seo_desc"), 300), "slogan": _t(x.get("slogan"), 110), "city": _t(x.get("city"), 40),
               "about": "\n".join(_t(l, 600) for l in str(x.get("about") or "").replace("\r", "").split("\n"))[:3000],
               "logo_only": bool(x.get("logo_only"))}
        out["services"] = [{"t": _t(s.get("t"), 60), "d": _t(s.get("d"), 400)} for s in (x.get("services") or [])[:12] if _t(s.get("t"), 60)]
        out["faq"] = [{"q": _t(f.get("q"), 140), "a": _t(f.get("a"), 600)} for f in (x.get("faq") or [])[:12] if _t(f.get("q"), 140)]
        rg = x.get("regions") or []
        if isinstance(rg, str):
            rg = re.split(r"[,\n]", rg)
        out["regions"] = [r for r in (_t(r, 40) for r in rg) if r][:12]
        soc = x.get("social") or {}
        out["social"] = {k: _t(soc.get(k), 200) for k in sitegen.LINK_ICON if _t(soc.get(k), 200)}
        lay = x.get("layout") or {}
        out["layout"] = {"order": [_t(n, 60) for n in (lay.get("order") or [])[:40] if _t(n, 60)], "hidden": [_t(n, 60) for n in (lay.get("hidden") or [])[:40] if _t(n, 60)]}
        ed = {}
        for th_, blks in (x.get("edits") or {}).items():
            if not isinstance(blks, dict) or len(ed) > 5:
                continue
            ed[_t(th_, 60)] = {_t(bn, 60): {str(int(i)): str(v)[:600] for i, v in list(tx.items())[:80] if str(i).isdigit()} for bn, tx in list(blks.items())[:40] if isinstance(tx, dict)}
        out["edits"] = ed
        out["hidden_pages"] = [_t(v, 60) for v in (x.get("hidden_pages") or [])[:60]]
        out["menu_off"] = [_t(v, 60) for v in (x.get("menu_off") or [])[:60]]
        ex, used = [], set()
        for e in (x.get("extra_pages") or [])[:20]:
            tt = _t(e.get("title"), 80)
            if not tt:
                continue
            sl = re.sub(r"[^a-z0-9-]", "", str(e.get("slug") or "").lower())[:40] or sitegen.slugify(tt)
            base, n = sl, 2
            while sl in sitegen_reserved or sl in used:
                sl, n = "%s-%d" % (base, n), n + 1
            used.add(sl)
            ex.append({"slug": sl, "title": tt, "body": "\n".join(_t(l, 800) for l in str(e.get("body") or "").replace("\r", "").split("\n"))[:6000], "img": str(e.get("img") or ""), "menu": bool(e.get("menu", True))})
        want = [str(s.get("k") or "") for s in (x.get("slides") or [])[:8]] + [str(g.get("k") or "") for g in (x.get("gallery") or [])[:16]] + [e["img"] for e in ex if e["img"]]
        have = set()
        async for r in db.site_images.find({"_id": {"$in": want}}, {"_id": 1}):
            have.add(r["_id"])
        out["slides"] = [{"k": s["k"], "t": _t(s.get("t"), 80), "d": _t(s.get("d"), 160)} for s in (x.get("slides") or [])[:8] if s.get("k") in have]
        out["gallery"] = [{"k": g["k"]} for g in (x.get("gallery") or [])[:16] if g.get("k") in have]
        for e in ex:
            if e["img"] not in have:
                e["img"] = ""
        out["extra_pages"] = ex
        return out

    @api_router.get("/site/profile")
    async def profile_get(_: dict = Depends(require_admin)):
        need_firm()
        prof = await db.app_settings.find_one({"_id": "site_profile"}, {"_id": 0}) or {}
        ctx = await build_ctx()
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        lg = (await db.app_settings.find_one({"_id": "firm_logo"}, {"_id": 0}) or {}).get("data") or ""
        d = await doc()
        sector = (ctx or {}).get("sector") or ""
        dflt = sitegen.DEFAULTS.get(sector) or {}
        keys = [x["k"] for x in (prof.get("slides") or []) + (prof.get("gallery") or [])] + [e["img"] for e in (prof.get("extra_pages") or []) if e.get("img")]
        imgs = {}
        async for r in db.site_images.find({"_id": {"$in": keys}}):
            imgs[r["_id"]] = "data:%s;base64,%s" % (r.get("mime") or "image/jpeg", base64.b64encode(bytes(r["data"])).decode())
        idx = sitegen.page_index(ctx, all_=True) if ctx else []
        return {"profile": prof, "imgs": imgs, "has_theme": bool(ctx), "sector": sector, "logo": lg, "custom_home": bool(d.get("html")),
                "name": (ctx or {}).get("name") or g.get("company_name") or "", "phone": g.get("company_phone") or "", "address": prof.get("address") or g.get("company_address") or "",
                "default_services": [{"t": a, "d": b} for a, b in dflt.get("services", [])], "default_faq": [{"q": a, "a": b} for a, b in dflt.get("faq", [])],
                "pages": [{"slug": x["slug"], "title": x["title"], "kind": x["kind"], "hidden": x["hidden"], "nav": x["nav"]} for x in idx],
                "custom_pages": [{"slug": p["slug"], "title": p.get("title", p["slug"])} for p in d.get("pages", [])]}

    @api_router.put("/site/profile")
    async def profile_put(payload: dict, _: dict = Depends(require_admin)):
        need_firm()
        prof = await san_profile(payload)
        await db.app_settings.update_one({"_id": "site_profile"}, {"$set": prof}, upsert=True)
        keep = [x["k"] for x in prof["slides"] + prof["gallery"]] + [e["img"] for e in prof["extra_pages"] if e["img"]]
        await db.site_images.delete_many({"_id": {"$nin": keep}})
        return {"ok": True}

    @api_router.post("/site/image")
    async def image_up(payload: dict, _: dict = Depends(require_admin)):
        need_firm()
        data = str(payload.get("data") or "")
        m = re.match(r"^data:image/(png|jpeg|webp|gif);base64,([A-Za-z0-9+/=]+)$", data)
        if not m or len(data) > 10_000_000:
            raise HTTPException(422, "Resim dosyası olmalı (JPG, PNG, WEBP) ve çok büyük olmamalı")
        try:
            from PIL import Image, ImageOps
            im = ImageOps.exif_transpose(Image.open(io.BytesIO(base64.b64decode(m.group(2)))))
            im = im.convert("RGB")
            side = 1920 if payload.get("kind") != "gallery" else 1280
            im.thumbnail((side, side))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
        except Exception:           # noqa: BLE001
            raise HTTPException(422, "Resim okunamadı")
        raw = buf.getvalue()
        k = hashlib.sha1(raw).hexdigest()[:16]
        await db.site_images.update_one({"_id": k}, {"$set": {"data": raw, "mime": "image/jpeg", "at": _now()}}, upsert=True)
        return {"ok": True, "k": k, "data": "data:image/jpeg;base64," + base64.b64encode(raw).decode()}

    @api_router.get("/public/site-img/{k}")
    async def image_pub(k: str):
        r = await db.site_images.find_one({"_id": k}) if re.fullmatch(r"[a-f0-9]{16}", k) else None
        if not r:
            raise HTTPException(404, "Yok")
        return Response(bytes(r["data"]), media_type=r.get("mime") or "image/jpeg", headers={"Cache-Control": "public, max-age=31536000, immutable"})

    @api_router.get("/public/site-logo")
    async def logo_pub():
        lg = (await db.app_settings.find_one({"_id": "firm_logo"}, {"_id": 0}) or {}).get("data") or ""
        m = re.match(r"^data:(image/[a-z+]+);base64,(.+)$", lg, re.S)
        if not m:
            raise HTTPException(404, "Yok")
        return Response(base64.b64decode(m.group(2)), media_type=m.group(1), headers={"Cache-Control": "public, max-age=86400", "Content-Security-Policy": "sandbox"})

    async def base_blocks(ctx, with_edits):
        p2 = dict(ctx["p"], layout={"_all": True})
        if not with_edits:
            p2["edits"] = {}
        h = sitegen.apply_profile(raw_theme(ctx["th"]["slug"]), ctx["th"], dict(ctx, p=p2))
        parts = sitegen.split_blocks(h)
        return {b[0]: b[1] for b in (parts[1] if parts else []) if b[0] not in sitegen.FIXED_TOP + sitegen.FIXED_BOTTOM}, [b[0] for b in (parts[1] if parts else []) if b[0] not in sitegen.FIXED_TOP + sitegen.FIXED_BOTTOM]

    @api_router.get("/site/blocks")
    async def blocks_get(_: dict = Depends(require_admin)):
        """Ana sayfadaki bölümler (sıra + gizli bilgisi). Her temada aynı yapı olduğu için tüm temalarda çalışır."""
        need_firm()
        ctx = await build_ctx()
        if not ctx:
            raise HTTPException(400, "Önce bir tema seçin")
        blocks, names = await base_blocks(ctx, True)
        lay = ctx["p"].get("layout") or {}
        order = [n for n in (lay.get("order") or []) if n in blocks] + [n for n in names if n not in (lay.get("order") or [])]
        from bs4 import BeautifulSoup
        out = []
        for n in order:
            soup = BeautifulSoup(blocks[n], "html.parser")
            hd = soup.find(["h1", "h2", "h3"])
            out.append({"name": n, "hidden": n in (lay.get("hidden") or []) or (sitegen.dflt_off(blocks[n]) and n not in (lay.get("order") or [])), "title": " ".join(hd.get_text().split())[:70] if hd else "", "n": len(sitegen.edit_nodes(soup))})
        return {"blocks": out}

    @api_router.get("/site/block-text")
    async def block_text(name: str, _: dict = Depends(require_admin)):
        need_firm()
        ctx = await build_ctx()
        if not ctx:
            raise HTTPException(400, "Önce bir tema seçin")
        cur, _n = await base_blocks(ctx, True)
        org, _n2 = await base_blocks(ctx, False)
        if name not in cur:
            raise HTTPException(404, "Bölüm yok")
        a, b = sitegen.block_texts(cur[name]), sitegen.block_texts(org[name])
        for x in a:
            x["orig"] = b[x["i"]]["text"] if x["i"] < len(b) else x["text"]
        return {"texts": a}

    @api_router.get("/site/preview")
    async def preview(path: str = "/", _: dict = Depends(require_admin)):
        """Panelde canlı önizleme: yayındakiyle aynı üretim, görseller gömülü."""
        need_firm()
        r = await render(path, inline=True)
        if not r:
            raise HTTPException(404, "Sayfa bulunamadı")
        return HTMLResponse(r[0], headers={"Cache-Control": "no-store"})

    # ---------------------------------------------------------------- yayın (domains.hosted_site çağırır)
    async def render(path, host="", inline=False):
        """(içerik, tür) ya da None. Özel (düzenleyici) sayfalar önce, sonra otomatik sayfalar."""
        d = await doc()
        p = (path or "/").split("?")[0].strip("/")
        if p.endswith(".html"):
            p = p[:-5]
        ctx = await build_ctx(inline=inline)
        if p == "robots.txt" and host:
            return "User-agent: *\nAllow: /\nSitemap: https://%s/sitemap.xml\n" % host, "text/plain"
        if p == "sitemap.xml" and host and ctx:
            return sitegen.sitemap(ctx, host, [x["slug"] for x in d.get("pages", []) if x["slug"] not in {i["slug"] for i in sitegen.page_index(ctx)}], str(d.get("updated_at") or "")), "application/xml"
        home = d.get("html")
        if home is not None and ctx and d.get("home_theme") and d["home_theme"] != ctx["th"]["slug"]:
            home = None  # tema değişti: eski temadan kalma ana sayfa kaydı kullanılmaz
        if home is None and ctx:
            home = await themed_home(ctx)
        if home is None:
            return None
        if p in ("", "index"):
            h = home
        elif p in ("magaza", "hesabim") and ctx and ctx.get("shop_on"):
            body = storefront.shop_page() if p == "magaza" else storefront.account_page()
            h = compose_page(await themed_home(ctx), ("Mağaza" if p == "magaza" else "Hesabım") + " · " + ctx["name"], body)
            if not h:
                return None
            h = h.replace("</head>", '<meta name="robots" content="noindex,follow"></head>', 1) if p == "hesabim" else h
        elif p in shop_legal.TITLES and ctx and ctx.get("legal"):
            sc = await db.app_settings.find_one({"_id": "shop_settings"}, {"_id": 0}) or {}
            cfg = {**shopmod.SHOP_DEFAULT, **sc}
            body = shop_legal.page(p, shopmod.merge_legal(cfg.get("legal")), cfg, cfg.get("legal_docs"), str(cfg.get("updated_at") or ""))
            h = compose_page(await themed_home(ctx), shop_legal.TITLES[p] + " · " + ctx["name"], body)
            if not h:
                return None
        else:
            pg = next((x for x in d.get("pages", []) if x["slug"] == p), None)
            if pg:
                h = pg["html"]
                if ctx and home:
                    h = sitegen.rebase(h, await themed_home(ctx), ctx, pg.get("title") or p, p)
            else:
                r = sitegen.render_page(home, ctx, p) if ctx else None
                if not r:
                    return None
                h = r[0]
        if ctx and "rel=\"canonical\"" not in h and "<title" in h:
            t = re.search(r"<title>(.*?)</title>", h, flags=re.S)
            tt = (t.group(1).split(" · ")[0] if t else "").strip()
            h = sitegen.seo_inject(h, sitegen.seo_block(ctx, tt, sitegen.seo_desc(ctx, tt), "" if p in ("", "index") else p, "home" if p in ("", "index") else "page"))
        if ctx and ctx.get("shop_on"):
            h = sitegen.account_icons(h)
        h = sitegen.credit(sitegen.seo_finish(h, host))
        if inline:
            h = await inline_imgs(h)
        return h, "text/html"

    async def serve(path: str, host: str = ""):
        r = await render(path, host)
        return r

    api_router.site_custom_serve = serve
