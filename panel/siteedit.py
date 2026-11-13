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
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

import shop as shopmod
import shop_legal
import cerez as cerez_mod
import dil as dil_mod
import uyelik as dil_mod_uyelik
import duyuru as duyuru_mod
import eticaret_plus as ep_mod
import blokgen
import blok_eticaret
import blok_tanitim
import blok_hareket
import blok_donusum
import blok_yapi
import blocks as blok_tanim

blokgen.kayit_al(blok_eticaret.KAYIT, blok_eticaret.CSS)
blokgen.kayit_al(blok_tanitim.KAYIT, blok_tanitim.CSS)
blokgen.kayit_al(blok_hareket.KAYIT, blok_hareket.CSS)
blokgen.kayit_al(blok_donusum.KAYIT, blok_donusum.CSS)
blokgen.kayit_al(blok_yapi.KAYIT, blok_yapi.CSS, blok_yapi.KABUK)
import storefront
import ilan
import sektor_mod
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


TEMA_EK = "tema-ek"


def tema_ek_ad(b):
    """Ek bölümün tema listesindeki adı (sıra/gizleme bu adla tutulur)."""
    return ("Ek · %s · %s" % (str(b.get("name") or "Bölüm")[:40], str(b.get("iid") or "")[:4]))[:60]


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



def _tema_renkleri(raw):
    """Temanın kendi :root renkleri (panelde 'temanın rengi' göstermek ve sıfırlamak için)."""
    out = {}
    m = re.search(r":root\s*\{([^}]*)\}", raw or "")
    if m:
        for k, v in re.findall(r"--(ac|dk|bg|ink|sf)\s*:\s*(#[0-9a-fA-F]{6})\b", m.group(1)):
            out[k] = v.lower()
    return out


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

    async def build_ctx(inline=False, dev=""):
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
        keys = [x["k"] for x in (p.get("slides") or []) + (p.get("gallery") or [])] + [e["img"] for e in (p.get("extra_pages") or []) if e.get("img")] + [v for blks in (p.get("imgedits") or {}).values() for tx in blks.values() for v in tx.values()] + [v for mp in (p.get("imgmap") or {}).values() for v in mp.values()]
        if inline and keys:
            async for r in db.site_images.find({"_id": {"$in": keys}}):
                imgs[r["_id"]] = "data:%s;base64,%s" % (r.get("mime") or "image/jpeg", base64.b64encode(bytes(r["data"])).decode())
        lg = (await db.app_settings.find_one({"_id": "firm_logo"}, {"_id": 0}) or {}).get("data") or ""
        logo = lg if inline else (("/api/public/site-logo?v=" + hashlib.sha1(lg.encode()).hexdigest()[:8]) if lg else "")
        feats = await db.app_settings.find_one({"_id": "site_features"}, {"_id": 0}) or {}
        fm = await db.app_settings.find_one({"_id": "firm"}, {"_id": 0, "modules": 1}) or {}
        mods = fm.get("modules")                       # None: paket sınırı yok (eski/tek firma) -> hepsi açık
        mods = None if mods is None else list(mods)
        shop_ok = bool(feats.get("shop_enabled")) and (mods is None or "magaza" in mods)   # paket Mağaza'yı içermiyorsa tema bölümü de yayında olmaz
        cz = dict(cerez_mod.VARSAYILAN, **((await db.app_settings.find_one({"_id": "cerez"}, {"_id": 0})) or {}))
        if shop_ok:
            legal = list(shop_legal.SLUGS)
        elif cz.get("on"):                      # çerez bandı açıkken politika ve aydınlatma metni her sitede açılır
            legal = [x for x in shop_legal.SLUGS if x[0] in ("cerez-politikasi", "gizlilik-kvkk")]
        else:
            legal = []
        ctx = {"modules": mods, "cerez": cz, "th": th, "brand": brand, "name": name, "tel": tel, "p": p, "sector": sector, "logo": logo, "city": prof.get("city") or "", "legal": legal, "shop_on": shop_ok, "dev": dev,
                "img": (lambda k: imgs.get(k, "")) if inline else (lambda k: "/api/public/site-img/" + k),
                "logo_abs": "/api/public/site-logo" if lg else ""}
        await tema_ek_yukle(ctx, dev)
        return ctx

    async def tema_ek_yukle(ctx, dev=""):
        """Hazır temaya bölüm kütüphanesinden eklenen bölümler (yp_pages 'tema-ek')."""
        try:
            pg = await db.yp_pages.find_one({"id": TEMA_EK}, {"_id": 0, "blocks": 1})
        except Exception:                                          # noqa: BLE001
            pg = None
        rows = []
        for b in (pg or {}).get("blocks") or []:
            t = blok_tanim.BY_ID.get(b.get("bid"))
            if t and b.get("on", True):
                rows.append(dict(b, wire=t["wire"], name=t["name"]))
        if not rows:
            return
        try:
            veri = await blok_veri(rows, ctx)
        except Exception:                                          # noqa: BLE001
            veri = {}
        th = ctx.get("th") or {}
        dk = th.get("dark") or (ctx.get("brand") or {}).get("dark") or "#0a1f44"
        ac = th.get("accent") or (ctx.get("brand") or {}).get("accent") or "#f27a1a"
        out = []
        for b in rows:
            h = blokgen.tema_bolum(b, "phone" if dev == "phone" else "", veri.get(b["iid"]) or veri.get(b.get("bid")) or {}, dk, ac)
            n = tema_ek_ad(b)                                      # boşken de listede durur ki panelden doldurulabilsin; sitede boş görünür
            out.append([n, '<div class="ed" data-nm="%s">%s</div>' % (_html.escape(n), h)])
        ctx["tema_ek"] = out
        ctx["tema_ek_iid"] = {tema_ek_ad(b): b["iid"] for b in rows}
        ctx["tema_ek_css"] = blokgen.tema_css()

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
        ie = {}
        for th_, blks in (x.get("imgedits") or {}).items():
            if not isinstance(blks, dict) or len(ie) > 5:
                continue
            ie[_t(th_, 60)] = {_t(bn, 60): {str(int(i)): str(v) for i, v in list(tx.items())[:80] if str(i).isdigit() and re.fullmatch(r"[a-f0-9]{16}", str(v))} for bn, tx in list(blks.items())[:40] if isinstance(tx, dict)}
        out["imgedits"] = ie
        pz = x.get("phone") or {}
        if isinstance(pz, dict):
            pl = pz.get("layout") or {}
            ph_out = {}
            if isinstance(pl, dict) and (pl.get("order") or pl.get("hidden")):
                ph_out["layout"] = {"order": [_t(n, 60) for n in (pl.get("order") or [])[:40] if _t(n, 60)],
                                    "hidden": [_t(n, 60) for n in (pl.get("hidden") or [])[:40] if _t(n, 60)]}
            pe = {}
            for th_, blks in (pz.get("edits") or {}).items():
                if not isinstance(blks, dict) or len(pe) > 5:
                    continue
                pe[_t(th_, 60)] = {_t(bn, 60): {str(int(i)): str(v)[:600] for i, v in list(tx.items())[:80] if str(i).isdigit()} for bn, tx in list(blks.items())[:40] if isinstance(tx, dict)}
            if pe:
                ph_out["edits"] = pe
            pi = {}
            for th_, blks in (pz.get("imgedits") or {}).items():
                if not isinstance(blks, dict) or len(pi) > 5:
                    continue
                pi[_t(th_, 60)] = {_t(bn, 60): {str(int(i)): str(v) for i, v in list(tx.items())[:80] if str(i).isdigit() and re.fullmatch(r"[a-f0-9]{16}", str(v))} for bn, tx in list(blks.items())[:40] if isinstance(tx, dict)}
            if pi:
                ph_out["imgedits"] = pi
            ui = pz.get("ui") or {}
            if isinstance(ui, dict) and ui:
                ph_out["ui"] = {_t(k, 40): (v if isinstance(v, (bool, int)) else _t(v, 120)) for k, v in list(ui.items())[:60] if _t(k, 40)}
            out["phone"] = ph_out
        else:
            out["phone"] = {}
        im = {}
        for th_, mp in (x.get("imgmap") or {}).items():
            if isinstance(mp, dict) and len(im) <= 5:
                im[_t(th_, 60)] = {str(p): str(v) for p, v in list(mp.items())[:200] if str(p).isdigit() and re.fullmatch(r"[a-f0-9]{16}", str(v))}
        out["imgmap"] = im
        out["hidden_pages"] = [_t(v, 60) for v in (x.get("hidden_pages") or [])[:60]]
        mn = x.get("menu") or {}
        ed = {}
        for k, v in list((mn.get("edits") or {}).items())[:80]:
            k = str(k)[:300]
            if isinstance(v, dict) and (v.get("off") or _t(v.get("l"), 40)):
                ed[k] = {"l": _t(v.get("l"), 40), "off": bool(v.get("off"))}
        ex_ = []
        for v in (mn.get("extra") or [])[:10]:
            hh, ll = str((v or {}).get("h") or "").strip()[:300], _t((v or {}).get("l"), 40)
            if ll and re.match(r"^(#[\w-]*|/[^\s]*|https?://[^\s]+|tel:[+\d\s]+|mailto:[^\s]+)$", hh):
                ex_.append({"h": hh, "l": ll})
        out["menu"] = {"edits": ed, "extra": ex_, "order": [str(o)[:300] for o in (mn.get("order") or [])[:80] if isinstance(o, str)]}
        bs = {}
        for th_, mp in (x.get("blockstyle") or {}).items():
            if not isinstance(mp, dict) or len(bs) > 5:
                continue
            row = {}
            for bn, st in list(mp.items())[:40]:
                if not isinstance(st, dict):
                    continue
                v = {}
                if st.get("h") in sitegen.FONTS:
                    v["h"] = st["h"]
                if st.get("b") in sitegen.FONTS:
                    v["b"] = st["b"]
                if re.fullmatch(r"#[0-9a-fA-F]{6}", str(st.get("c") or "")):
                    v["c"] = st["c"]
                if v:
                    row[_t(bn, 60)] = v
            bs[_t(th_, 60)] = row
        out["blockstyle"] = bs
        bk = {str(k): _t(v, 200 if k == "ok_msg" else 120) for k, v in (x.get("booktext") or {}).items() if k in {r[0] for r in sitegen.BOOKTEXT} and _t(v, 200)}
        out["booktext"] = bk
        out["coupon_off"] = bool(x.get("coupon_off"))
        pm = x.get("promo") or {}
        out["promo"] = {}
        if isinstance(pm, dict) and pm:
            out["promo"] = {"on": False if pm.get("on") is False else True, "text": _t(pm.get("text"), 120),
                            "end": str(pm.get("end") or "") if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", str(pm.get("end") or "")) else "", "btn": _t(pm.get("btn"), 30)}
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
        want = [v for mp in im.values() for v in mp.values()] + [v for blks in ie.values() for tx in blks.values() for v in tx.values()] + [str(s.get("k") or "") for s in (x.get("slides") or [])[:8]] + [str(g.get("k") or "") for g in (x.get("gallery") or [])[:16]] + [e["img"] for e in ex if e["img"]]
        have = set()
        async for r in db.site_images.find({"_id": {"$in": want}}, {"_id": 1}):
            have.add(r["_id"])
        for mp in im.values():
            for p_ in list(mp):
                if mp[p_] not in have:
                    del mp[p_]
        for blks in ie.values():
            for bn in list(blks):
                blks[bn] = {i: v for i, v in blks[bn].items() if v in have}
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
        try:
            pd = bool(ctx) and 'id="cd"' in raw_theme(ctx["th"]["slug"])
        except Exception:                                          # noqa: BLE001
            pd = False
        return {"promo_default": pd, "profile": prof, "imgs": imgs, "has_theme": bool(ctx), "sector": sector, "logo": lg, "custom_home": bool(d.get("html")),
                "name": (ctx or {}).get("name") or g.get("company_name") or "", "phone": g.get("company_phone") or "", "address": prof.get("address") or g.get("company_address") or "",
                "default_services": [{"t": a, "d": b} for a, b in dflt.get("services", [])], "default_faq": [{"q": a, "a": b} for a, b in dflt.get("faq", [])],
                "pages": [{"slug": x["slug"], "title": x["title"], "kind": x["kind"], "hidden": x["hidden"], "nav": x["nav"]} for x in idx],
                "custom_pages": [{"slug": p["slug"], "title": p.get("title", p["slug"])} for p in d.get("pages", [])]}

    @api_router.put("/site/profile")
    async def profile_put(payload: dict, _: dict = Depends(require_admin)):
        need_firm()
        if "imgedits" not in payload or "imgmap" not in payload or "menu" not in payload or "blockstyle" not in payload or "promo" not in payload or "booktext" not in payload or "phone" not in payload:          # eski panel bu alanları bilmez: mevcut resim/menü değişikliklerini silmesin
            old_ = (await db.app_settings.find_one({"_id": "site_profile"}, {"_id": 0})) or {}
            payload = dict(payload, imgedits=payload.get("imgedits", old_.get("imgedits") or {}), imgmap=payload.get("imgmap", old_.get("imgmap") or {}), menu=payload.get("menu", old_.get("menu") or {}), blockstyle=payload.get("blockstyle", old_.get("blockstyle") or {}), promo=payload.get("promo", old_.get("promo") or {}), booktext=payload.get("booktext", old_.get("booktext") or {}), coupon_off=payload.get("coupon_off", old_.get("coupon_off") or False), phone=payload.get("phone", old_.get("phone") or {}))
        prof = await san_profile(payload)
        await db.app_settings.update_one({"_id": "site_profile"}, {"$set": prof}, upsert=True)
        keep = [x["k"] for x in prof["slides"] + prof["gallery"]] + [e["img"] for e in prof["extra_pages"] if e["img"]] + [v for blks in prof["imgedits"].values() for tx in blks.values() for v in tx.values()] + [v for mp in prof["imgmap"].values() for v in mp.values()]
        await db.site_images.delete_many({"_id": {"$nin": keep}})
        return {"ok": True}

    @api_router.get("/site/nav-design")
    async def nav_design_get(_: dict = Depends(require_admin)):
        """Üst menü, mobil menü, mobil alt çubuk ve tüm tema tasarım ayarları + temadaki gerçek öğeler (düğme, bağlantı...)."""
        import navtasarim
        need_firm()
        prof = await db.app_settings.find_one({"_id": "site_profile"}, {"_id": 0}) or {}
        ctx = await build_ctx()
        og = {"cta": None, "bar": [], "drw": {"chips": False, "cta": False}}
        if ctx:
            ctx2 = dict(ctx, p=dict(ctx["p"], nav={}, tw={}, layout={"_all": True}))
            parts = sitegen.split_blocks(sitegen.apply_profile(raw_theme(ctx["th"]["slug"]), ctx["th"], ctx2))
            bl = {b[0]: b[1] for b in (parts[1] if parts else [])}
            og = navtasarim.ogrenme(bl.get("Menü", ""), bl.get("Mobil menü", ""), bl.get("Mobil bar", ""))
        return {"nav": navtasarim.clean(prof.get("nav") or {}), "tw": navtasarim.tw_clean(prof.get("tw") or {}), "tema": og,
                "has_theme": bool(ctx), "fonts": sitegen.FONTS, "icons": navtasarim.ICON_AD,
                "tema_renk": _tema_renkleri(raw_theme(ctx["th"]["slug"])) if ctx else {}}

    @api_router.put("/site/nav-design")
    async def nav_design_put(payload: dict, _: dict = Depends(require_admin)):
        import navtasarim
        need_firm()
        up = {}
        if "nav" in payload:
            up["nav"] = navtasarim.clean(payload.get("nav"))
        if "tw" in payload:
            up["tw"] = navtasarim.tw_clean(payload.get("tw"))
        if up:
            await db.app_settings.update_one({"_id": "site_profile"}, {"$set": up}, upsert=True)
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

    async def base_blocks(ctx, with_edits, footer=False):
        # ctx içindeki "dev" telefon ise sitegen telefon katmanını kendiliğinden uygular
        p2 = dict(ctx["p"], layout={"_all": True})
        if not with_edits:
            p2["edits"] = {}
        p2["imgedits"] = {}                 # resim sırası her zaman özgün temaya göre sayılır
        h = sitegen.apply_profile(raw_theme(ctx["th"]["slug"]), ctx["th"], dict(ctx, p=p2))
        parts = sitegen.split_blocks(h)
        return ({b[0]: b[1] for b in (parts[1] if parts else []) if b[0] not in sitegen.FIXED_TOP + sitegen.FIXED_BOTTOM or (footer and b[0] == "Alt bilgi")},
                [b[0] for b in (parts[1] if parts else []) if b[0] not in sitegen.FIXED_TOP + sitegen.FIXED_BOTTOM])

    @api_router.get("/site/blocks")
    async def blocks_get(dev: str = "", _: dict = Depends(require_admin)):
        """Ana sayfadaki bölümler (sıra + gizli bilgisi). dev=phone ise telefona özel sıra/gizleme döner."""
        need_firm()
        ctx = await build_ctx(dev="phone" if dev == "phone" else "")
        if not ctx:
            raise HTTPException(400, "Önce bir tema seçin")
        blocks, names = await base_blocks(ctx, True)
        org_, _nn = await base_blocks(ctx, False)
        lay = ctx["p"].get("layout") or {}
        ph = (ctx["p"].get("phone") or {}) if ctx.get("dev") == "phone" else {}
        ayri = bool(ph.get("layout"))                      # telefon sırası bilgisayardan ayrı mı
        if ayri:
            lay = dict(lay, **{k: v for k, v in (ph["layout"] or {}).items() if k in ("order", "hidden")})
        ped = ((ph.get("edits") or {}).get(ctx["th"]["slug"], {}) or {}) if ph else {}
        pie = ((ph.get("imgedits") or {}).get(ctx["th"]["slug"], {}) or {}) if ph else {}
        order = [n for n in (lay.get("order") or []) if n in blocks] + [n for n in names if n not in (lay.get("order") or [])]
        from bs4 import BeautifulSoup
        out = []
        for n in order:
            soup = BeautifulSoup(blocks[n], "html.parser")
            hd = soup.find(["h1", "h2", "h3"])
            out.append({"name": n, "hidden": n in (lay.get("hidden") or []) or (sitegen.dflt_off(blocks[n]) and n not in (lay.get("order") or [])), "title": " ".join(hd.get_text().split())[:70] if hd else "", "n": len(sitegen.edit_nodes(soup)), "ni": len(sitegen.block_images(org_[n])) if n in org_ else 0,
                        "own": bool(ped.get(n)) or bool(pie.get(n)), "ek": (ctx.get("tema_ek_iid") or {}).get(n, "")})     # telefona özel yazı/resim var mı
        for x in out:
            if x["ek"] and not x["title"]:
                x["title"] = x["name"].split(" · ")[1] if x["name"].count(" · ") >= 2 else x["name"]
        return {"blocks": out, "dev": ctx.get("dev") or "web", "own_order": ayri}


    @api_router.get("/site/block-text")
    async def block_text(name: str, dev: str = "", _: dict = Depends(require_admin)):
        need_firm()
        ctx = await build_ctx(dev="phone" if dev == "phone" else "")
        if not ctx:
            raise HTTPException(400, "Önce bir tema seçin")
        cur, _n = await base_blocks(ctx, True, True)
        org, _n2 = await base_blocks(ctx, False, True)
        if name not in cur:
            raise HTTPException(404, "Bölüm yok")
        a, b = sitegen.block_texts(cur[name]), sitegen.block_texts(org[name])
        for x in a:
            x["orig"] = b[x["i"]]["text"] if x["i"] < len(b) else x["text"]
        if ctx.get("dev") == "phone":                     # telefonda: bilgisayardaki hâli ve hangisi telefona özel
            wctx = await build_ctx()
            wcur, _n3 = await base_blocks(wctx, True, True)
            w = sitegen.block_texts(wcur[name]) if name in wcur else []
            own = ((((ctx["p"].get("phone") or {}).get("edits") or {}).get(ctx["th"]["slug"], {}) or {}).get(name) or {})
            for x in a:
                x["web"] = w[x["i"]]["text"] if x["i"] < len(w) else x["orig"]
                x["own"] = str(x["i"]) in own
        return {"texts": a, "dev": ctx.get("dev") or "web"}

    @api_router.get("/site/booktext")
    async def booktext_get(_: dict = Depends(require_admin)):
        """Randevu formundaki yazılar (temadaki varsayılanlarıyla)."""
        need_firm()
        ctx = await build_ctx()
        if not ctx:
            raise HTTPException(400, "Önce bir tema seçin")
        h = raw_theme(ctx["th"]["slug"])
        f = sitegen.booktext_fields(h) if "function isFree(d,e,h){if(LIVE){var t=L.slots" in h else []
        cur = ctx["p"].get("booktext") or {}
        return {"fields": [dict(x, val=cur.get(x["k"], "")) for x in f], "coupon_off": bool(ctx["p"].get("coupon_off"))}

    @api_router.get("/site/menu")
    async def menu_get(_: dict = Depends(require_admin)):
        """Sitenin menüsündeki bağlantılar (temadan gelenler) ve kayıtlı düzenlemeler."""
        need_firm()
        ctx = await build_ctx()
        if not ctx:
            raise HTTPException(400, "Önce bir tema seçin")
        p2 = dict(ctx["p"], layout={"_all": True}, menu={})
        parts = sitegen.split_blocks(sitegen.apply_profile(raw_theme(ctx["th"]["slug"]), ctx["th"], dict(ctx, p=p2)))
        bl = {b[0]: b[1] for b in (parts[1] if parts else [])}
        items = sitegen.menu_items(bl.get("Menü"), bl.get("Mobil menü"))
        m = ctx["p"].get("menu") or {}
        od = [o for o in (m.get("order") or [])]
        items.sort(key=lambda x: od.index(x["h"]) if x["h"] in od else 10_000)
        return {"items": items, "edits": m.get("edits") or {}, "extra": m.get("extra") or [], "order": od}

    @api_router.get("/site/theme-images")
    async def theme_images(_: dict = Depends(require_admin)):
        """Temanın kullandığı bütün stok resimler (galeri, ekip, kapak...) ve varsa değiştirilmiş hâlleri."""
        need_firm()
        ctx = await build_ctx()
        if not ctx:
            raise HTTPException(400, "Önce bir tema seçin")
        cur = (ctx["p"].get("imgmap") or {}).get(ctx["th"]["slug"], {}) or {}
        return {"images": [{"pid": p, "thumb": "https://images.pexels.com/photos/%s/pexels-photo-%s.jpeg?auto=compress&cs=tinysrgb&w=400" % (p, p), "k": cur.get(p, "")} for p in sitegen.theme_image_ids(raw_theme(ctx["th"]["slug"]))]}

    @api_router.get("/site/block-images")
    async def block_images(name: str, _: dict = Depends(require_admin)):
        """Bölümdeki değiştirilebilir resimler: özgün stok resim + (varsa) yüklenen resim."""
        need_firm()
        ctx = await build_ctx()
        if not ctx:
            raise HTTPException(400, "Önce bir tema seçin")
        org, _n = await base_blocks(ctx, False, True)
        if name not in org:
            raise HTTPException(404, "Bölüm yok")
        cur = ((ctx["p"].get("imgedits") or {}).get(ctx["th"]["slug"], {}) or {}).get(name, {})
        return {"images": [dict(x, thumb="https://images.pexels.com/photos/%s/pexels-photo-%s.jpeg?auto=compress&cs=tinysrgb&w=400" % (x["pid"], x["pid"]), k=cur.get(str(x["i"]), "")) for x in sitegen.block_images(org[name])]}

    @api_router.get("/site/preview")
    async def preview(path: str = "/", dev: str = "", _: dict = Depends(require_admin)):
        """Panelde canlı önizleme: yayındakiyle aynı üretim, görseller gömülü. dev=phone ise telefon görünümü."""
        need_firm()
        r = await render(path, inline=True, dev="phone" if dev == "phone" else "")
        if not r:
            raise HTTPException(404, "Sayfa bulunamadı")
        html = r[0]
        if (path or "/").split("?")[0].strip("/") in ("", "index") and isinstance(html, str) and not (await doc()).get("html"):
            try:
                html = sitegen.mark_edit(html)
            except Exception:                                      # noqa: BLE001
                pass
        return HTMLResponse(html, headers={"Cache-Control": "no-store"})

    # ---------------------------------------------------------------- yayın (domains.hosted_site çağırır)
    async def blok_veri(rows, ctx):
        """Bölümlerin beslendiği listeler: ürünler, hizmetler, ekip, yorumlar, adres."""
        gerek = {(blok_tanim.BY_ID.get(b.get("bid")) or {}).get("manage") or "" for b in rows}
        kimlik = {b.get("bid") for b in rows}
        out, kasa = {}, {}
        if "Ürünler" in gerek or "Ürünler › Kategoriler" in gerek or "Ürünler › Markalar" in gerek:
            pr = await db.yp_products.find({"status": {"$ne": "draft"}},
                                           {"_id": 0, "id": 1, "name": 1, "slug": 1, "cat": 1, "brand": 1,
                                            "price": 1, "sale_price": 1, "stock": 1, "low_at": 1,
                                            "track_stock": 1, "images": 1, "channels": 1,
                                            "status": 1, "created_at": 1}).limit(200).to_list(200)
            kasa["urun"] = [(x.get("name") or "", ("%s ₺" % blokgen.para(x.get("price"))) if x.get("price") else "",
                             "/magaza/urun/" + str(x.get("slug") or x.get("id") or ""), (x.get("images") or [None])[0] or "") for x in pr[:24]]
            kasa["urunler"] = pr
            sat = {}
            if "v_coksatan" in kimlik or "v_hizli_sepet" in kimlik:
                try:
                    async for o in db.yp_orders.find({"state": {"$nin": ["iptal"]}}, {"_id": 0, "items": 1}).limit(600):
                        for it in (o.get("items") or []):
                            k = str(it.get("pid") or it.get("id") or "")
                            if k:
                                sat[k] = sat.get(k, 0) + int(it.get("qty") or 1)
                except Exception:                                  # noqa: BLE001
                    sat = {}
            kasa["satis"] = sat
            kt, mk = {}, {}
            for x in pr:
                c = (x.get("cat") or "").strip()
                if c:
                    e = kt.setdefault(c, {"ad": c, "n": 0, "img": ""})
                    e["n"] += 1
                    if not e["img"]:
                        e["img"] = (x.get("images") or [None])[0] or ""
                mm = (x.get("brand") or "").strip()
                if mm:
                    mk[mm] = mk.get(mm, 0) + 1
            kasa["kategoriler"] = sorted(kt.values(), key=lambda e: -e["n"])
            kasa["markalar"] = [{"ad": a, "n": n} for a, n in sorted(mk.items(), key=lambda e: -e[1])]
            try:
                st_ = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0, "badges": 1}) or {}
                kasa["rozetler"] = blok_tanim.badge_list(st_.get("badges") or [])
            except Exception:                                      # noqa: BLE001
                kasa["rozetler"] = []
        if "Ayarlar › Hizmetler" in gerek:
            sv = await db.yp_services.find({"active": {"$ne": False}},
                                           {"_id": 0, "name": 1, "price": 1, "dur": 1, "cat": 1, "desc": 1, "img": 1}).limit(60).to_list(60)
            kasa["hizmet"] = [(x.get("name") or "", ("%s ₺" % blokgen.para(x.get("price"))) if x.get("price") else "") for x in sv]
            kasa["hizmetler"] = sv
        if "Ekip" in gerek:
            st = await db.yp_staff.find({"active": {"$ne": False}},
                                        {"_id": 0, "name": 1, "title": 1, "img": 1}).sort("order", 1).limit(24).to_list(24)
            kasa["ekip"] = [(x.get("name") or "", x.get("title") or "", "", "") for x in st]
            kasa["ekip_k"] = [{"ad": x.get("name") or "", "unvan": x.get("title") or "", "img": x.get("img") or ""} for x in st]
        if "Pazarlama › Paketler" in gerek:
            try:
                pk = await db.yp_camps.find({"type": "paket"}, {"_id": 0}).limit(12).to_list(12)
            except Exception:                                      # noqa: BLE001
                pk = []
            kasa["paketler"] = [{"ad": x.get("name") or "", "fiyat": x.get("price") or 0,
                                 "aciklama": x.get("desc") or "", "kazanc": x.get("save") or 0} for x in pk]
        if "Pazarlama › Hediye çekleri" in gerek:
            try:
                ck = await db.yp_camps.find({"type": "kupon"}, {"_id": 0, "amount": 1}).limit(8).to_list(8)
            except Exception:                                      # noqa: BLE001
                ck = []
            kasa["cekler"] = [{"tutar": x.get("amount") or 0} for x in ck if x.get("amount")]
        if "Pazarlama › Duyuru" in gerek:
            dy = await db.yp_duyuru.find_one({"on": True}, {"_id": 0, "text": 1}) or {}
            kasa["duyuru"] = dy.get("text") or ""
        if "Yorumlar" in gerek or "Yorumlar › Google" in gerek:
            yo = await db.yp_content.find({"type": "yorum", "onay": True},
                                          {"_id": 0, "text": 1, "ad": 1, "name": 1, "puan": 1, "star": 1, "video": 1}).limit(40).to_list(40)
            kasa["yorum"] = [(x.get("text") or "", x.get("ad") or x.get("name") or "") for x in yo]
            kasa["yorumlar"] = [{"yazi": x.get("text") or "", "ad": x.get("ad") or x.get("name") or "",
                                 "puan": x.get("puan") or x.get("star") or 5} for x in yo if x.get("text")]
            kasa["video_yorum"] = [{"url": x.get("video"), "ad": x.get("ad") or x.get("name") or ""} for x in yo if x.get("video")]
            try:
                g = await db.app_settings.find_one({"_id": "google"}, {"_id": 0}) or {}
            except Exception:                                      # noqa: BLE001
                g = {}
            kasa["google"] = {"puan": g.get("rating"), "adet": g.get("count"),
                              "yorumlar": [{"yazi": x.get("text") or "", "ad": x.get("author") or "",
                                            "puan": x.get("rating") or 5} for x in (g.get("reviews") or [])[:12]]}
        if "Web Sitem › Fotoğraflar" in gerek:
            kasa["fotograflar"] = [x.get("k") for x in ((ctx.get("p") or {}).get("gallery") or []) if x.get("k")]
        if "Web Sitem › Belgeler" in gerek:
            kasa["belgeler"] = [x.get("k") for x in ((ctx.get("p") or {}).get("docs") or []) if x.get("k")]
        if "Ayarlar › Bağlantılar" in gerek:
            kasa["baglantilar"] = (ctx.get("p") or {}).get("social") or {}
        adres = ((ctx.get("p") or {}).get("address") or ctx.get("city") or "")
        prof = ctx.get("p") or {}
        if "Web Sitem › Blog" in gerek:
            try:
                yz = await db.yp_content.find({"type": "yazi", "onay": {"$ne": False}},
                                              {"_id": 0, "baslik": 1, "ozet": 1, "slug": 1, "img": 1, "tarih": 1}).limit(12).to_list(12)
            except Exception:                                      # noqa: BLE001
                yz = []
            kasa["yazilar"] = yz
        if "Web Sitem › SSS" in gerek:
            try:
                sq = await db.yp_content.find({"type": "sss"}, {"_id": 0, "soru": 1, "cevap": 1}).limit(40).to_list(40)
            except Exception:                                      # noqa: BLE001
                sq = []
            kasa["sss"] = sq
        if "Web Sitem › Dosyalar" in gerek:
            kasa["dosyalar"] = [x for x in (prof.get("files") or []) if isinstance(x, dict)]
        if "Ayarlar › Saatler" in gerek:
            sa = prof.get("hours") or []
            kasa["saatler"] = sa
            try:
                simdi = datetime.now(timezone.utc) + timedelta(hours=3)
                kasa["bugun"] = simdi.weekday()
                g = sa[simdi.weekday()] if len(sa) > simdi.weekday() else {}
                if g and not g.get("kapali") and g.get("ac") and g.get("kapa"):
                    hhmm = simdi.strftime("%H:%M")
                    kasa["acik_mi"] = str(g["ac"]) <= hhmm <= str(g["kapa"])
                else:
                    kasa["acik_mi"] = False
            except Exception:                                      # noqa: BLE001
                kasa["bugun"], kasa["acik_mi"] = None, None
        if "Ayarlar › Şubeler" in gerek:
            kasa["subeler"] = [x for x in (prof.get("branches") or []) if isinstance(x, dict)]
        if "Ayarlar › Bölgeler" in gerek:
            kasa["bolgeler"] = [str(x) for x in (prof.get("areas") or []) if str(x).strip()]
        if "Ayarlar › İletişim" in gerek:
            kasa["iletisim"] = {"tel": ctx.get("tel") or "", "eposta": prof.get("email") or "",
                                "adres": adres, "whatsapp": prof.get("whatsapp") or ""}
            kasa["baglantilar"] = prof.get("social") or {}
        if "Ayarlar › Yasal" in gerek:
            kasa["yasal"] = list(ctx.get("legal") or [])
        if "Ürünler › Odalar" in gerek:
            try:
                kasa["odalar"] = await db.yp_products.find({"cat": {"$regex": "oda", "$options": "i"}},
                                                           {"_id": 0, "name": 1, "price": 1, "images": 1, "desc": 1}).limit(12).to_list(12)
            except Exception:                                      # noqa: BLE001
                kasa["odalar"] = []
            kasa["odalar"] = [{"ad": x.get("name") or "", "fiyat": x.get("price") or 0,
                               "desc": x.get("desc") or "", "images": x.get("images") or []} for x in kasa["odalar"]]
        if "Takvim › Programlar" in gerek:
            try:
                kasa["program"] = await db.yp_content.find({"type": "program"}, {"_id": 0}).limit(60).to_list(60)
            except Exception:                                      # noqa: BLE001
                kasa["program"] = []
        if "Takvim › Etkinlikler" in gerek:
            try:
                kasa["etkinlikler"] = await db.yp_content.find({"type": "etkinlik"}, {"_id": 0}).limit(40).to_list(40)
            except Exception:                                      # noqa: BLE001
                kasa["etkinlikler"] = []
        for b in rows:
            mg = (blok_tanim.BY_ID.get(b.get("bid")) or {}).get("manage") or ""
            w = b.get("wire")
            d = {}
            if mg == "Ürünler" and kasa.get("urun"):
                d["cards"] = kasa["urun"]
            elif mg == "Ayarlar › Hizmetler" and kasa.get("hizmet"):
                d["rows" if w in ("rows", "faq") else "cards"] = kasa["hizmet"] if w in ("rows", "faq") else [(a, b2, "", "") for a, b2 in kasa["hizmet"]]
            elif mg == "Ekip" and kasa.get("ekip"):
                d["cards"] = kasa["ekip"]
                d["ekip"] = kasa.get("ekip_k") or []
            elif mg == "Yorumlar" and kasa.get("yorum"):
                d["quotes"] = kasa["yorum"]
            if w == "map":
                d["address"] = adres
            if mg == "Ayarlar › Hizmetler":
                d["hizmetler"] = kasa.get("hizmetler") or []
            if mg == "Pazarlama › Paketler":
                d["paketler"] = kasa.get("paketler") or []
            if mg == "Pazarlama › Hediye çekleri":
                d["cekler"] = kasa.get("cekler") or []
            if mg == "Pazarlama › Duyuru":
                d["duyuru"] = kasa.get("duyuru") or ""
            if mg.startswith("Yorumlar"):
                d["yorumlar"] = kasa.get("yorumlar") or []
                d["video_yorum"] = kasa.get("video_yorum") or []
                d["google"] = kasa.get("google") or {}
            if mg == "Web Sitem › Fotoğraflar":
                d["fotograflar"] = kasa.get("fotograflar") or []
            if mg == "Web Sitem › Belgeler":
                d["belgeler"] = kasa.get("belgeler") or []
            if mg == "Ayarlar › Bağlantılar":
                d["baglantilar"] = kasa.get("baglantilar") or {}
            if mg == "Web Sitem › Blog":
                d["yazilar"] = kasa.get("yazilar") or []
            if mg == "Web Sitem › SSS":
                d["sss"] = kasa.get("sss") or []
            if mg == "Web Sitem › Dosyalar":
                d["dosyalar"] = kasa.get("dosyalar") or []
            if mg == "Ayarlar › Adres":
                d["adres"] = adres
            if mg == "Ayarlar › Saatler":
                d["saatler"] = kasa.get("saatler") or []
                d["bugun"] = kasa.get("bugun")
                d["acik_mi"] = kasa.get("acik_mi")
            if mg == "Ayarlar › Şubeler":
                d["subeler"] = kasa.get("subeler") or []
            if mg == "Ayarlar › Bölgeler":
                d["bolgeler"] = kasa.get("bolgeler") or []
            if mg == "Ayarlar › İletişim":
                d["iletisim"] = kasa.get("iletisim") or {}
                d["baglantilar"] = kasa.get("baglantilar") or {}
            if mg == "Ayarlar › Yasal":
                d["yasal"] = kasa.get("yasal") or []
            if mg == "Ürünler › Odalar":
                d["odalar"] = kasa.get("odalar") or []
            if mg == "Takvim › Programlar":
                d["program"] = kasa.get("program") or []
            if mg == "Takvim › Etkinlikler":
                d["etkinlikler"] = kasa.get("etkinlikler") or []
            if mg == "QR menü":
                d["menu"] = kasa.get("urunler") or kasa.get("hizmetler") or []
            if mg == "Ürünler › Portföy":
                d["portfoy_turleri"] = kasa.get("portfoy_turleri") or []
            if mg == "Ayarlar › Markalar":
                d["markalar"] = kasa.get("markalar") or []
            d.setdefault("adres", adres)
            d.setdefault("accent", (ctx.get("brand") or {}).get("accent") or "#1155cc")
            d.setdefault("yil", datetime.now(timezone.utc).year)
            d.setdefault("firma", ctx.get("name") or "")
            d.setdefault("baglantilar", kasa.get("baglantilar") or (ctx.get("p") or {}).get("social") or {})
            d.setdefault("iletisim", kasa.get("iletisim") or {"tel": ctx.get("tel") or "", "adres": adres})
            d.setdefault("kategoriler", kasa.get("kategoriler") or [])
            if mg == "Randevu ayarları":
                d["hizmetler"] = kasa.get("hizmetler") or []
                d["ekip"] = kasa.get("ekip_k") or []
            if mg.startswith("Ürünler"):
                d["urunler"] = kasa.get("urunler") or []
                d["satis"] = kasa.get("satis") or {}
                d["kategoriler"] = kasa.get("kategoriler") or []
                d["markalar"] = kasa.get("markalar") or []
                d["rozetler"] = kasa.get("rozetler") or []
            out[b["iid"]] = d
        return out

    try:
        import blocks_api as _ba
        _ba.VERI, _ba.CTX = blok_veri, build_ctx
    except Exception:                                              # noqa: BLE001
        pass

    async def blok_motor_acik():
        """Bölüm motoru yalnız işletme açıkça açtığında devreye girer.
        Kapalıyken mevcut tema sitesi olduğu gibi yayında kalır."""
        try:
            st = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0, "site_engine": 1})
        except Exception:                                          # noqa: BLE001
            return False
        return (st or {}).get("site_engine") == "blok"

    async def blok_sayfa(p, ctx, dev):
        """Panelde kurulmuş bölüm sayfası varsa onu üretir, yoksa None."""
        if not await blok_motor_acik():
            return None
        try:
            doc_ = await db.yp_pages.find_one({"home": True, "status": "live"}, {"_id": 0}) if p in ("", "index") \
                else await db.yp_pages.find_one({"slug": p, "status": "live"}, {"_id": 0})
        except Exception:                                          # noqa: BLE001
            return None
        if not doc_ or not doc_.get("blocks"):
            return None
        rows = []
        for b in doc_["blocks"]:
            t = blok_tanim.BY_ID.get(b.get("bid"))
            if t:
                rows.append(dict(b, wire=t["wire"], name=t["name"]))
        if not rows:
            return None
        mn = await db.yp_pages.find({"status": "live", "menu.top": True}, {"_id": 0, "slug": 1, "title": 1, "home": 1, "menu": 1}).sort("order", 1).limit(8).to_list(8)
        menu = [{"slug": x.get("slug") or "", "home": x.get("home"), "title": (x.get("menu") or {}).get("label") or x.get("title") or ""} for x in mn]
        c2 = dict(ctx, menu_pages=menu, yil=datetime.now(timezone.utc).year)
        return blokgen.page_html(doc_, rows, c2, await blok_veri(rows, ctx), dev)

    async def render_raw(path, host="", inline=False, dev=""):
        """(içerik, tür) ya da None. Özel (düzenleyici) sayfalar önce, sonra otomatik sayfalar."""
        d = await doc()
        p = (path or "/").split("?")[0].strip("/")
        if p.endswith(".html"):
            p = p[:-5]
        ctx = await build_ctx(inline=inline, dev=dev)
        if p == "robots.txt" and host:
            return "User-agent: *\nAllow: /\nSitemap: https://%s/sitemap.xml\n" % host, "text/plain"
        if p == "sitemap.xml" and host and ctx:
            return sitegen.sitemap(ctx, host, [x["slug"] for x in d.get("pages", []) if x["slug"] not in {i["slug"] for i in sitegen.page_index(ctx)}], str(d.get("updated_at") or "")), "application/xml"
        bs = await blok_sayfa(p, ctx, dev) if ctx else None
        if bs:                                                     # panelde kurulmuş bölüm sayfası temanın önüne geçer
            return bs, "text/html"
        home = d.get("html")
        if home is not None and ctx and d.get("home_theme") and d["home_theme"] != ctx["th"]["slug"]:
            home = None  # tema değişti: eski temadan kalma ana sayfa kaydı kullanılmaz
        if home is None and ctx:
            home = await themed_home(ctx)
        if home is None:
            return None
        if p in ("", "index"):
            h = home
        elif (p in ("magaza", "hesabim") or re.fullmatch(r"magaza/urun/[^/]{1,120}", p)) and ctx and (ctx.get("shop_on") or (p == "hesabim" and ((await db.app_settings.find_one({"_id": "yp_uyelik"}, {"_id": 0, "on": 1})) or {}).get("on"))):
            body = storefront.shop_page() if p.startswith("magaza") else storefront.account_page(bool(ctx.get("shop_on")))
            ttl = "Mağaza" if p == "magaza" else "Hesabım"
            if p.startswith("magaza/urun/"):
                try:
                    from urllib.parse import unquote
                    pr = await db.shop_products.find_one({"$or": [{"slug": unquote(p[12:])}, {"id": unquote(p[12:])}], "active": True}, {"_id": 0, "name": 1})
                except Exception:                                             # noqa: BLE001
                    pr = None
                if not pr:
                    return None
                ttl = pr["name"]
            h = compose_page(await themed_home(ctx), ttl + " · " + ctx["name"], body)
            if not h:
                return None
            h = h.replace("</head>", '<meta name="robots" content="noindex,follow"></head>', 1) if p == "hesabim" else h
        elif p in ("kurslar", "rezervasyon") and ctx and (("/" + p) in [h for h, _ in sektor_mod.site_links(ctx.get("sector") or "")] or await getattr(db, "programs" if p == "kurslar" else "resources").count_documents({}) > 0):
            items = await sektor_mod.public_items(db, "programs" if p == "kurslar" else "resources")
            body = sektor_mod.kurslar_body(items) if p == "kurslar" else sektor_mod.rezervasyon_body(items)
            h = compose_page(await themed_home(ctx), ("Programlar" if p == "kurslar" else "Rezervasyon") + " · " + ctx["name"], body)
            if not h:
                return None
        elif (p == "ilanlar" or p.startswith("ilan/")) and ctx and (ctx.get("sector") in sektor_mod.SECTOR_MODULES["ilan"] or await db.listings.count_documents({}) > 0):
            if p == "ilanlar":
                rows = await db.listings.find({"status": {"$in": ["yayinda", "satildi"]}}, {"_id": 0, "images": 0}).sort([("featured", -1), ("created_at", -1)]).to_list(300)
                for r in rows:
                    r["img_count"] = len((await db.listings.find_one({"id": r["id"]}, {"_id": 0, "images": 1}) or {}).get("images") or [])
                items = [ilan.public_item(r) for r in rows]
                kind = ""
                body, ttl = ilan.list_body(items, kind), "İlanlar"
            else:
                slug = p[5:]
                dd = await db.listings.find_one({"slug": slug, "status": {"$in": ["yayinda", "satildi"]}}, {"_id": 0})
                if not dd:
                    return None
                body, ttl = ilan.detail_body(dd, sitegen.phone10(ctx.get("tel")), sitegen.phone10((ctx.get("p") or {}).get("whatsapp"))), dd["title"]
            h = compose_page(await themed_home(ctx), ttl + " · " + ctx["name"], body)
            if not h:
                return None
        elif ctx and p in {k for k, _ in (ctx.get("legal") or [])}:
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
        if ctx and not ctx.get("shop_on"):
            h = sitegen.SHOP_LINK.sub("", sitegen.STORY_SHOP.sub("", h))
        if ctx and ctx.get("shop_on"):
            h = sitegen.account_icons(h)
        h = sitegen.credit(sitegen.seo_finish(h, host))
        h = cerez_mod.ekle(h, ctx.get("cerez") if ctx else None, ((ctx or {}).get("th") or {}).get("accent") or "#1155cc")
        if inline:
            h = await inline_imgs(h)
        return h, "text/html"

    async def render(path, host="", inline=False, dev=""):
        inline_ = inline
        """Çok dilli site: /en/... adresi çözülür, sayfa ziyaretçinin diline çevrilir, dil seçici eklenir."""
        lang, p2, cfg = await dil_mod.parse_path(db, path)
        r = await render_raw(p2 if lang else path, host, inline, dev)
        if lang and r and str(r[1]).startswith("text/html"):
            rest = (p2 or "/").split("?")[0].strip("/")
            r = (dil_mod.apply_page(r[0], cfg, lang, rest, await dil_mod.tablo(db, lang) if lang != cfg["ana"] else {}), r[1])
        if r and not inline_ and str(r[1]).startswith("text/html") and "</body>" in r[0] and "okuye" not in r[0]:
            try:
                uy = await db.app_settings.find_one({"_id": "yp_uyelik"}, {"_id": 0, "on": 1})
            except Exception:                                      # noqa: BLE001
                uy = None
            if (uy or {}).get("on"):
                btn = dil_mod_uyelik.buton(("/" + lang) if lang and lang != cfg["ana"] and cfg.get("adresli") else "")
                r = (r[0].replace("</body>", btn + "</body>", 1), r[1])
        if r and not inline_ and str(r[1]).startswith("text/html") and "</body>" in r[0] and 'id="okdy' not in r[0]:
            try:
                bas, son = duyuru_mod.render_html(await duyuru_mod.get_cfg(db))
            except Exception:                                      # noqa: BLE001
                bas, son = "", ""
            if bas or son:
                h = r[0]
                if bas:
                    h = re.sub(r"(<body\b[^>]*>)", lambda m: m.group(1) + bas, h, 1)
                r = (h.replace("</body>", son + "</body>", 1) if son else h, r[1])
        if r and not inline_ and str(r[1]).startswith("text/html") and "</body>" in r[0] and 'id="okpv' not in r[0]:
            try:
                import popvitrin as _pv
                pc = await _pv.get_cfg(db)
                pv = ""
                if pc.get("on"):
                    ft = await db.app_settings.find_one({"_id": "site_features"}, {"_id": 0, "shop_enabled": 1}) or {}
                    if ft.get("shop_enabled"):
                        pv = _pv.render_html(pc, await _pv.urunler(db, pc), (p2 if lang else path) or "/")
            except Exception:                                      # noqa: BLE001
                pv = ""
            if pv:
                r = (r[0].replace("</body>", pv + "</body>", 1), r[1])
        if r and not inline_ and str(r[1]).startswith("text/html") and "</body>" in r[0] and 'id="okck"' not in r[0]:
            try:
                ck = ep_mod.cark_html(await ep_mod._cfg(db, "yp_cark", ep_mod.CARK_DEF))
            except Exception:                                      # noqa: BLE001
                ck = ""
            if ck:
                r = (r[0].replace("</body>", ck + "</body>", 1), r[1])
        return r

    api_router.site_render_raw = render_raw

    async def serve(path: str, host: str = "", ua: str = ""):
        r = await render(path, host, dev="phone" if sitegen.is_phone(ua) else "")
        return r

    api_router.site_custom_serve = serve

    async def not_found(host: str = "", ua: str = ""):
        """Temanın üst ve alt bilgisiyle 'sayfa bulunamadı' sayfası; site yoksa None."""
        ctx = await build_ctx(dev="phone" if sitegen.is_phone(ua) else "")
        if not ctx:
            return None
        home = await themed_home(ctx)
        if not home:
            return None
        body = ('<section style="max-width:640px;margin:0 auto;padding:72px 20px;text-align:center">'
                '<p style="font-size:64px;font-weight:800;margin:0;line-height:1;opacity:.25">404</p>'
                '<h1 style="margin:12px 0 8px">Aradığınız sayfa bulunamadı</h1>'
                '<p style="line-height:1.6;opacity:.8">Adres değişmiş ya da sayfa kaldırılmış olabilir.</p>'
                '<p style="margin-top:24px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap">'
                '<a href="/" style="display:inline-block;min-height:44px;line-height:44px;padding:0 22px;border-radius:10px;background:#0a1f44;color:#fff;text-decoration:none;font-weight:700">Ana sayfaya dön</a>'
                + ('<a href="/magaza" style="display:inline-block;min-height:44px;line-height:44px;padding:0 22px;border-radius:10px;border:1px solid currentColor;text-decoration:none;font-weight:700">Mağazaya git</a>' if ctx.get("shop_on") else "")
                + '</p></section>')
        h = compose_page(home, "Sayfa bulunamadı · " + ctx["name"], body)
        if not h:
            return None
        return h.replace("</head>", '<meta name="robots" content="noindex"></head>', 1)

    api_router.site_not_found = not_found
