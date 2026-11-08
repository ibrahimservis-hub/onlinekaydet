#!/usr/bin/env python3
"""Statik yayın (bake): panelde YAYINLANMIŞ site içeriğini sunucu tarafında HTML dosyalarına işler.

Neden? Site Stüdyosu içeriği normalde ziyaretçinin tarayıcısında JavaScript ile uygulanır (hızlı ve güvenli ama
Google bazı değişiklikleri geç görebilir). Bu araç aynı değişiklikleri HTML dosyalarının içine yazar; böylece başlık,
metin, meta açıklama, menü ve yeni sayfalar arama motoruna ilk istekte hazır gelir.

Kullanım (kendi bilgisayarınızda veya site sunucusunda):
    python bake.py --site /var/www/servisplus --api https://bayi.servisplus.net.tr/api
    python bake.py --site ./site --api http://localhost:8001/api --paths /,/servis/kombi/ --dry-run
    python bake.py --site ./site --restore          # her şeyi özgün haline döndürür

Güvenlik: değiştirilen her dosyanın özgün hali ilk seferde <site>/.sp-bake-orig/ altına kopyalanır; her çalıştırma
özgün dosyadan başlar (tekrar çalıştırmak güvenlidir). Sitenin kodunu kendiniz güncelleyecekseniz önce --restore çalıştırın.
"""
import argparse
import hashlib
import html as htmlmod
import json
import os
import re
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, Tag

ORIG_DIR = ".sp-bake-orig"
MANIFEST = ".sp-bake.json"
OLD_PHONE = re.compile(r"^(\(?0?544\)?[\s.-]*)?444[\s.-]*4[\s.-]*004$")
THEME_VARS = {"primary": "--sp-blue", "primary_dark": "--sp-blue-dark", "navy": "--sp-navy", "muted": "--sp-muted",
              "border": "--sp-border", "bg": "--sp-bg", "card": "--sp-card", "brand": "--sp-brand-color"}
FOOTER_VARS = {"bg": "--sp-footer-bg", "text": "--sp-footer-text", "title": "--sp-footer-title"}
HERO_CSS = (".spc-hero{position:relative;overflow:hidden;width:100%;border-radius:inherit;background:#0b1f3a}.spc-slide{position:absolute;inset:0;opacity:0;transition:opacity .7s ease;display:flex;align-items:flex-end}.spc-slide.on{opacity:1;z-index:1}.spc-slide img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.spc-ov{position:absolute;inset:0}.spc-txt{position:relative;z-index:2;color:#fff;padding:32px 40px;max-width:760px}.spc-txt h1,.spc-txt h2{margin:0 0 10px;font-size:clamp(24px,4vw,40px);line-height:1.15;color:#fff}.spc-txt p{margin:0 0 16px;font-size:clamp(14px,1.8vw,18px);color:#eaf2ff}.spc-btn{display:inline-block;background:var(--sp-blue,#1155cc);color:#fff;padding:12px 22px;border-radius:10px;font-weight:700;text-decoration:none}.spc-nav{position:absolute;top:50%;transform:translateY(-50%);z-index:3;background:rgba(255,255,255,.85);border:0;width:38px;height:38px;border-radius:50%;font-size:20px;cursor:pointer}.spc-dots{position:absolute;left:0;right:0;bottom:10px;z-index:3;display:flex;gap:8px;justify-content:center}.spc-dots i{width:9px;height:9px;border-radius:50%;background:rgba(255,255,255,.55);cursor:pointer}.spc-dots i.on{background:#fff}"
            "@media(max-width:767px){.spc-txt{padding:18px 18px 34px}.spc-nav{width:30px;height:30px}}")


# ------------------------------------------------------------------ yardımcılar
def norm_path(p: str) -> str:
    p = (p or "/").split("?")[0].split("#")[0]
    if not p.startswith("/"):
        p = "/" + p
    if not p.endswith("/") and "." not in p.rsplit("/", 1)[-1]:
        p += "/"
    return p.replace("/index.html", "/")


def ops_for(state: dict, path: str):
    out = []
    for o in state.get("ops", []):
        sc, op = o.get("scope", "page"), o.get("path", "/")
        if sc == "global" or (sc == "page" and norm_path(op) == norm_path(path)) or (sc == "prefix" and norm_path(path).startswith(norm_path(op))):
            out.append(o)
    return out


def media_abs(u: str, api: str) -> str:
    if u and u.startswith("/api/public/media/"):
        return api.rstrip("/").removesuffix("/api") + u
    return u


def clean_css(css: str) -> str:
    parts = []
    for d in (css or "").split(";"):
        d = d.strip()
        if d:
            parts.append(re.sub(r"\s*!important\s*$", "", d) + " !important")
    return ";".join(parts)


def media_wrap(dev: Optional[str]):
    return ("@media (max-width:767px){", "}") if dev == "mobile" else ("@media (min-width:768px){", "}") if dev == "desktop" else ("", "")


def build_css(state: dict, ops: list, home: bool) -> str:
    th, ft = state.get("theme") or {}, state.get("footer") or {}
    out, vs = [], []
    vs += [f"{v}:{th[k]} !important" for k, v in THEME_VARS.items() if th.get(k)]
    vs += [f"{v}:{ft[k]} !important" for k, v in FOOTER_VARS.items() if ft.get(k)]
    if vs:
        out.append(":root{" + ";".join(vs) + "}")
    if th.get("font"):
        out.append("body,body *{font-family:" + th["font"] + " !important}")
    if th.get("radius") not in (None, ""):
        out.append(".sp-card-grid>*,.sp-hero-banner,.sp-region-card,.sp-service-card,.sp-benefit,.sp-step{border-radius:" + str(int(th["radius"])) + "px !important}")
    for o in ops:
        a, b = media_wrap(o.get("device"))
        sel = f'[data-spc-k~="{o["id"]}"]' if o.get("id") else o.get("selector")
        if o.get("type") == "hide" and sel:
            out.append(a + sel + "{display:none !important}" + b)
        if o.get("type") == "style" and sel and o.get("css"):
            out.append(a + sel + "{" + clean_css(o["css"]) + "}" + b)
    if (state.get("custom") or {}).get("css"):
        out.append(state["custom"]["css"])
    if state.get("hero", {}).get("enabled") and home:
        out.append(HERO_CSS)
    return "\n".join(out)


def sel1(soup, selector):
    try:
        return soup.select_one(selector)
    except Exception:
        return None


def frag(soup, html: str):
    return BeautifulSoup(html, "html.parser")


def set_inner(soup, el: Tag, html: str):
    el.clear()
    for c in list(BeautifulSoup(html, "html.parser").contents):
        el.append(c.extract())


def set_attr(el: Tag, name: str, val: str):
    el[name] = val
    if name == "src":
        el.attrs.pop("srcset", None)
        if el.parent is not None and el.parent.name == "picture":
            for s in el.parent.find_all("source"):
                s["srcset"] = val


def meta_tag(soup, name: str, val: str, prop=False):
    if val in (None, ""):
        return
    m = soup.find("meta", attrs={("property" if prop else "name"): name})
    if not m:
        m = soup.new_tag("meta")
        m["property" if prop else "name"] = name
        (soup.head or soup).append(m)
    m["content"] = val


def hero_html(h: dict, api: str) -> str:
    slides = [h["slides"][0]] if h.get("mode") == "single" else h["slides"]
    H = int(h.get("height") or 440)
    ov = h.get("overlay", 0.35)
    q = lambda s: htmlmod.escape(str(s or ""), quote=True)
    out = '<div class="spc-hero" style="height:%dpx;max-height:%dpx">' % (H, H)
    for i, s in enumerate(slides):
        tag = "h1" if i == 0 else "h2"
        img = ""
        if s.get("image"):
            img = '<img src="%s" alt="%s"%s>' % (q(media_abs(s["image"], api)), q(s.get("alt") or s.get("title")), ' fetchpriority="high"' if i == 0 else ' loading="lazy"')
        title = "<%s>%s</%s>" % (tag, s["title"], tag) if s.get("title") else ""
        text = "<p>%s</p>" % s["text"] if s.get("text") else ""
        cta = '<a class="spc-btn" href="%s">%s</a>' % (q(s["cta_url"]), s["cta_text"]) if s.get("cta_text") and s.get("cta_url") else ""
        out += ('<div class="spc-slide%s">%s<div class="spc-ov" style="background:linear-gradient(180deg,rgba(0,0,0,0) 20%%,rgba(7,20,45,%s) 100%%)"></div>'
                '<div class="spc-txt">%s%s%s</div></div>') % (" on" if i == 0 else "", img, ov, title, text, cta)
    if len(slides) > 1:
        out += ('<button class="spc-nav" data-d="-1" style="left:12px" aria-label="Önceki">‹</button><button class="spc-nav" data-d="1" style="right:12px" aria-label="Sonraki">›</button>'
                '<div class="spc-dots">' + "".join('<i data-i="%d"%s></i>' % (i, ' class="on"' if i == 0 else "") for i in range(len(slides))) + "</div>")
    return out + "</div>"


# ------------------------------------------------------------------ bir sayfaya içerik işleme
def bake_html(html: str, state: dict, path: str, api: str, active_banner: Optional[dict] = None) -> str:
    soup = BeautifulSoup(html, "html.parser")
    ops = ops_for(state, path)
    home = norm_path(path) == "/"
    # 1) hide/style hedeflerini özgün DOM'da işaretle
    for o in ops:
        if o.get("type") in ("hide", "style") and o.get("id") and o.get("selector"):
            el = sel1(soup, o["selector"])
            if el is not None:
                cur = (el.get("data-spc-k") or "").split()
                if o["id"] not in cur:
                    cur.append(o["id"])
                    el["data-spc-k"] = " ".join(cur)
    css = build_css(state, ops, home)
    if css and soup.head is not None:
        st = soup.new_tag("style", id="sp-cms-css")
        st.string = css
        soup.head.append(st)
    # 2) metin / öznitelik / sıralama / ekleme
    for o in ops:
        if o.get("type") == "text" and o.get("selector") and "data-spc-add" not in o["selector"]:
            el = sel1(soup, o["selector"])
            if el is not None:
                set_inner(soup, el, o.get("value", ""))
    for o in ops:
        if o.get("type") == "attr" and o.get("selector") and o.get("name") and "data-spc-add" not in o["selector"]:
            el = sel1(soup, o["selector"])
            if el is not None:
                v = o.get("value", "")
                set_attr(el, o["name"], media_abs(v, api) if o["name"] in ("src", "href") else v)
    for o in ops:
        if o.get("type") == "order" and o.get("parent"):
            parent = sel1(soup, o["parent"])
            if parent is not None:
                kids = [c for c in parent.children if isinstance(c, Tag)]
                perm = o.get("perm") or []
                if len(perm) == len(kids) and all(isinstance(i, int) and 0 <= i < len(kids) for i in perm):
                    for k in kids:
                        k.extract()
                    for i in perm:
                        parent.append(kids[i])
    for o in ops:
        if o.get("type") == "add" and o.get("anchor") and o.get("html"):
            a = sel1(soup, o["anchor"])
            if a is None:
                continue
            node = next((c for c in BeautifulSoup(o["html"], "html.parser").contents if isinstance(c, Tag)), None)
            if node is None:
                continue
            node["data-spc-add"] = o.get("id", "")
            w = o.get("where", "after")
            if w == "before":
                a.insert_before(node)
            elif w == "append":
                a.append(node)
            elif w == "prepend":
                a.insert(0, node)
            else:
                a.insert_after(node)
    for o in ops:
        if "data-spc-add" in (o.get("selector") or "") and o.get("type") in ("text", "attr"):
            el = sel1(soup, o["selector"])
            if el is not None:
                set_inner(soup, el, o.get("value", "")) if o["type"] == "text" else set_attr(el, o.get("name", ""), o.get("value", ""))
    # 3) meta
    for o in ops:
        if o.get("type") == "meta":
            if o.get("title"):
                if soup.title:
                    soup.title.string = o["title"]
                meta_tag(soup, "og:title", o["title"], True)
            meta_tag(soup, "description", o.get("description"))
            meta_tag(soup, "og:description", o.get("description"), True)
            meta_tag(soup, "og:image", media_abs(o.get("og_image"), api), True)
            if o.get("noindex"):
                meta_tag(soup, "robots", "noindex, nofollow")
    # 4) global
    g = state.get("global") or {}
    if g.get("logo_url"):
        for i in soup.select('.sph-logo-img, .sph-logo img, img[src*="/images/logo"]'):
            set_attr(i, "src", media_abs(g["logo_url"], api))
    if g.get("favicon_url"):
        l = soup.find("link", rel=lambda r: r and "icon" in (r if isinstance(r, list) else [r]))
        if l:
            l["href"] = media_abs(g["favicon_url"], api)
    tel = re.sub(r"[^\d+]", "", g.get("phone") or "")
    disp = g.get("phone_display") or g.get("phone")
    if tel:
        for a in soup.select('a[href^="tel:"]'):
            a["href"] = "tel:" + tel
    if disp:
        for el in soup.find_all(["a", "span", "p", "strong", "b", "small", "li", "div"]):
            if len([c for c in el.children if isinstance(c, Tag)]) > 2:
                continue
            t = re.sub(r"\s+", " ", el.get_text()).strip()
            if len(t) < 22 and OLD_PHONE.match(t):
                set_inner(soup, el, htmlmod.escape(disp))
    if g.get("email"):
        for a in soup.select('a[href^="mailto:"]'):
            a["href"] = "mailto:" + g["email"]
            if "@" in a.get_text():
                pre = re.match(r"^[^\w]*", a.get_text()).group(0)
                set_inner(soup, a, htmlmod.escape(pre + g["email"]))
    if g.get("whatsapp"):
        for a in soup.select('a[href*="wa.me"], a[href*="whatsapp.com"]'):
            a["href"] = "https://wa.me/" + re.sub(r"\D", "", g["whatsapp"])
    for k, v in (g.get("social") or {}).items():
        if v:
            for a in soup.select(f'a[href*="{k}"]'):
                if a.find_parent(["footer", "header"]):
                    a["href"] = v
    # 5) menü / footer bağlantıları
    apply_nav(soup, state.get("nav"))
    # 6) footer metinleri, banner, hero, özel kod
    f = state.get("footer") or {}
    foot = soup.find("footer")
    if foot is not None:
        if f.get("copyright"):
            for el in foot.find_all(["p", "div", "span", "small"]):
                if not [c for c in el.children if isinstance(c, Tag)] and re.search(r"©|telif|tüm hakları", el.get_text(), re.I):
                    set_inner(soup, el, f["copyright"])
                    break
        if f.get("note"):
            p = soup.new_tag("p")
            p["data-spc-note"] = "1"
            p["style"] = "margin:12px 0 0;opacity:.85;font-size:13px"
            set_inner(soup, p, f["note"])
            foot.append(p)
    b = active_banner
    if b and b.get("text") and soup.body is not None:
        d = soup.new_tag("div", id="spc-banner")
        d["style"] = f"background:{b.get('bg') or '#b91c1c'};color:{b.get('color') or '#fff'};text-align:center;padding:9px 14px;font:600 14px/1.4 Inter,Arial,sans-serif;position:relative;z-index:2147483001"
        inner = f'<a href="{htmlmod.escape(b["link"], quote=True)}" style="color:inherit;text-decoration:underline">{b["text"]}</a>' if b.get("link") else b["text"]
        set_inner(soup, d, inner)
        soup.body.insert(0, d)
    h = state.get("hero") or {}
    if home and h.get("enabled") and h.get("slides"):
        host = soup.select_one(".sp-hero-banner")
        if host is not None:
            set_inner(soup, host, hero_html(h, api))
    c = state.get("custom") or {}
    if c.get("head_html") and soup.body is not None:
        d = soup.new_tag("div", id="spc-head")
        d["style"] = "display:none"
        set_inner(soup, d, c["head_html"])
        soup.body.append(d)
    if c.get("body_end_html") and soup.body is not None:
        d = soup.new_tag("div", id="spc-end")
        set_inner(soup, d, c["body_end_html"])
        soup.body.append(d)
    return soup.decode(formatter=None)


def apply_nav(soup, nav: Optional[dict]):
    if not nav or not nav.get("enabled"):
        return
    q = lambda s: htmlmod.escape(str(s or ""), quote=True)
    hn = soup.select_one("nav.sph-nav")
    if hn is not None and nav.get("header"):
        hn.clear()
        for l in nav["header"]:
            hn.append(BeautifulSoup(f'<a href="{q(l.get("href"))}">{htmlmod.escape(str(l.get("label", "")))}</a>', "html.parser"))
    foot = soup.find("footer")
    if foot is not None and nav.get("footer"):
        cols = [c for c in foot.select(".bg2f-col") if c.find("h4") and c.find("ul")]
        for col, spec in zip(cols, nav["footer"]):
            col.find("h4").string = spec.get("title", "")
            ul = col.find("ul")
            ul.clear()
            for l in spec.get("links", []):
                ext = (l.get("href") or "").startswith("http")
                ul.append(BeautifulSoup(f'<li><a href="{q(l.get("href"))}"' + (' rel="noopener" target="_blank"' if ext else "") + f'>{htmlmod.escape(str(l.get("label", "")))}</a></li>', "html.parser"))


# ------------------------------------------------------------------ yeni sayfalar
def render_blocks(blocks: list, api: str) -> str:
    q = lambda s: htmlmod.escape(str(s or ""), quote=True)
    out, faq = [], []
    for b in blocks:
        t = b.get("type")
        if t == "heading":
            lv = 2 if int(b.get("level") or 2) < 3 else 3
            out.append(f'<h{lv} class="section-title">{b.get("text", "")}</h{lv}>')
        elif t == "paragraph":
            out.append(f'<p>{b.get("text", "")}</p>')
        elif t == "image" and b.get("src"):
            out.append(f'<p><img src="{q(media_abs(b["src"], api))}" alt="{q(b.get("alt"))}" loading="lazy" style="max-width:100%;height:auto;border-radius:12px"></p>')
        elif t == "button" and b.get("text"):
            out.append(f'<p><a class="btn" href="{q(b.get("href") or "#")}">{b["text"]}</a></p>')
        elif t == "list":
            out.append("<ul>" + "".join(f"<li>{i}</li>" for i in (b.get("items") or [])) + "</ul>")
        elif t == "faq":
            for it in b.get("items") or []:
                out.append(f'<details class="faq-item"><summary><b>{it.get("q", "")}</b></summary><p>{it.get("a", "")}</p></details>')
                faq.append(it)
        elif t == "html":
            out.append(b.get("html", ""))
    body = "\n".join(out)
    ld = ""
    if faq:
        ld = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": re.sub("<[^>]+>", "", i.get("q", "")), "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", i.get("a", ""))}} for i in faq]}, ensure_ascii=False) + "</script>"
    return body + ld


def build_page(shell_html: str, page: dict, state: dict, api: str) -> str:
    """Var olan sade bir sayfayı (kabuk) alıp header/footer'ı koruyarak içeriği değiştirir."""
    soup = BeautifulSoup(shell_html, "html.parser")
    site = (state.get("site_url") or "").rstrip("/")
    title = page.get("title") or page["slug"]
    if soup.title:
        soup.title.string = title
    meta_tag(soup, "description", page.get("description"))
    meta_tag(soup, "og:title", title, True)
    meta_tag(soup, "og:description", page.get("description"), True)
    meta_tag(soup, "og:image", media_abs(page.get("og_image"), api), True)
    meta_tag(soup, "robots", "noindex, nofollow" if page.get("noindex") else "index, follow")
    can = soup.find("link", rel="canonical")
    if can is None and soup.head is not None:
        can = soup.new_tag("link", rel="canonical")
        soup.head.append(can)
    if can is not None:
        can["href"] = f"{site}/{page['slug']}/"
    # eski sayfanın JSON-LD / breadcrumb blokları sızmasın
    for s in soup.find_all("script", attrs={"type": "application/ld+json"}):
        s.decompose()
    main = soup.find("main")
    if main is None:
        raise RuntimeError("Kabuk sayfada <main> yok")
    main.clear()
    h1 = f'<h1 style="margin:24px 0 8px">{htmlmod.escape(title)}</h1>'
    inner = BeautifulSoup(f'<div class="container"><section>{h1}{render_blocks(page.get("blocks", []), api)}</section></div>', "html.parser")
    for c in list(inner.contents):
        main.append(c.extract())
    return soup.decode(formatter=None)


# ------------------------------------------------------------------ site genelinde
def has_global(state: dict) -> bool:
    return bool(state.get("theme") or any((state.get("global") or {}).values()) or any((state.get("footer") or {}).values())
                or (state.get("banner") or {}).get("enabled") or (state.get("nav") or {}).get("enabled")
                or any((state.get("custom") or {}).values()) or any(o.get("scope") == "global" for o in state.get("ops", [])))


def page_files(site: Path):
    for root, dirs, files in os.walk(site):
        dirs[:] = [d for d in dirs if d not in (ORIG_DIR, "node_modules", ".git")]
        if "index.html" in files:
            yield Path(root) / "index.html"


def url_of(site: Path, f: Path) -> str:
    rel = f.relative_to(site).parent.as_posix()
    return "/" if rel == "." else f"/{rel}/"


def _bake_one(args):
    site, rel, state, api, banner = args
    f = Path(site) / rel
    orig = Path(site) / ORIG_DIR / rel
    src = orig if orig.exists() else f
    html = src.read_text(encoding="utf-8")
    path = url_of(Path(site), f)
    new = bake_html(html, state, path, api, banner)
    return rel, html, new


def restore(site: Path) -> int:
    od = site / ORIG_DIR
    n = 0
    if od.exists():
        for f in od.rglob("*"):
            if f.is_file():
                dest = site / f.relative_to(od)
                shutil.copy2(f, dest)
                n += 1
    m = site / MANIFEST
    if m.exists():
        info = json.loads(m.read_text())
        for rel in info.get("new_pages", []):
            p = site / rel
            if p.exists():
                p.unlink()
                try:
                    p.parent.rmdir()
                except OSError:
                    pass
        m.unlink()
    if od.exists():
        shutil.rmtree(od)
    return n


def bake_site(site: Path, state: dict, api: str, paths=None, workers: int = 1, dry: bool = False, banner=None) -> dict:
    site = Path(site)
    result = {"baked": 0, "new_pages": [], "skipped": 0, "errors": []}
    b = state.get("banner") or {}
    if banner is None:
        # tarih aralığı olan şerit statik yazılmaz (süresi dolunca eski HTML'de kalırdı); tarayıcı tarafı yönetir
        banner = b if b.get("enabled") and not b.get("start_at") and not b.get("end_at") else None
    targets = []
    allp = list(page_files(site))
    if paths:
        want = {norm_path(p) for p in paths}
        targets = [f for f in allp if url_of(site, f) in want]
    elif has_global(state):
        targets = allp
    else:
        for f in allp:
            if ops_for(state, url_of(site, f)):
                targets.append(f)
    # önceki bake'te işlenmiş ama artık içeriği kalmamış sayfalar özgün hale dönsün
    manifest = {}
    mf = site / MANIFEST
    if mf.exists():
        manifest = json.loads(mf.read_text())
    prev = set(manifest.get("baked", []))
    cur_rel = {f.relative_to(site).as_posix() for f in targets}
    for rel in prev - cur_rel:
        o = site / ORIG_DIR / rel
        if o.exists() and not dry:
            shutil.copy2(o, site / rel)
            o.unlink()
    jobs = [(str(site), f.relative_to(site).as_posix(), state, api, banner) for f in targets]
    done = []
    results = ProcessPoolExecutor(workers).map(_bake_one, jobs, chunksize=8) if workers > 1 and len(jobs) > 16 else map(_bake_one, jobs)
    try:
        for rel, old, new in results:
            if new == old and not (site / ORIG_DIR / rel).exists():
                result["skipped"] += 1
                continue
            if not dry:
                o = site / ORIG_DIR / rel
                if not o.exists():
                    o.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(site / rel, o)
                (site / rel).write_text(new, encoding="utf-8")
            done.append(rel)
            result["baked"] += 1
    except Exception as e:                          # noqa: BLE001
        result["errors"].append(str(e)[:200])
    # yeni sayfalar
    new_pages = []
    pubs = [p for p in state.get("pages", []) if p.get("status", "published") == "published"]
    shell = None
    for pth in (site / ORIG_DIR / "hakkimizda/index.html", site / "hakkimizda/index.html", site / ORIG_DIR / "iletisim/index.html", site / "iletisim/index.html"):
        if pth.exists():
            shell = pth.read_text(encoding="utf-8")
            break
    for p in pubs:
        if shell is None:
            result["errors"].append("Sayfa şablonu (hakkimizda/index.html) bulunamadı")
            break
        rel = f"{p['slug']}/index.html"
        try:
            html = build_page(shell, p, state, api)
            html = bake_html(html, {**state, "ops": [], "hero": {}}, "/" + p["slug"] + "/", api, banner)   # tema/global/menü/footer de uygulansın
        except Exception as e:                      # noqa: BLE001
            result["errors"].append(f"{p['slug']}: {e}")
            continue
        if not dry:
            dest = site / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html, encoding="utf-8")
        new_pages.append(rel)
    for rel in set(manifest.get("new_pages", [])) - set(new_pages):    # yayından kalkan sayfalar
        p = site / rel
        if p.exists() and not dry:
            p.unlink()
            try:
                p.parent.rmdir()
            except OSError:
                pass
    result["new_pages"] = new_pages
    update_sitemap(site, state, pubs, dry)
    if not dry:
        mf.write_text(json.dumps({"baked": sorted(set(done) | (prev & cur_rel)), "new_pages": new_pages, "version": state.get("_version", 0)}, ensure_ascii=False))
    return result


def update_sitemap(site: Path, state: dict, pubs: list, dry: bool):
    sm = site / "sitemap.xml"
    if not sm.exists() or dry:
        return
    orig = site / ORIG_DIR / "sitemap.xml"
    if not orig.exists():
        orig.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sm, orig)
    txt = orig.read_text(encoding="utf-8")
    if pubs and "</urlset>" in txt:
        base = (state.get("site_url") or "").rstrip("/")
        add = "".join(f"<url><loc>{base}/{p['slug']}/</loc></url>" for p in pubs if not p.get("noindex"))
        txt = txt.replace("</urlset>", add + "</urlset>")
    sm.write_text(txt, encoding="utf-8")


def fetch_state(api: str) -> dict:
    import requests
    r = requests.get(api.rstrip("/") + "/public/site-bake", timeout=30)
    r.raise_for_status()
    j = r.json()
    j["state"]["_version"] = j.get("version", 0)
    return j["state"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="ServisPlus statik yayın aracı")
    ap.add_argument("--site", required=True, help="Sitenin HTML klasörü")
    ap.add_argument("--api", help="Panel API adresi, örn. https://bayi.servisplus.net.tr/api")
    ap.add_argument("--paths", help="Yalnızca bu sayfalar (virgülle), örn. /,/servis/kombi/")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--restore", action="store_true", help="Tüm değişiklikleri özgün hale döndür")
    a = ap.parse_args(argv)
    site = Path(a.site)
    if a.restore:
        print(f"{restore(site)} dosya özgün haline döndürüldü")
        return 0
    if not a.api:
        ap.error("--api gerekli")
    state = fetch_state(a.api)
    res = bake_site(site, state, a.api, [p for p in (a.paths or "").split(",") if p] or None, a.workers, a.dry_run)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
