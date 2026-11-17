# -*- coding: utf-8 -*-
"""Platform sahibi: onlinekaydet.com tanıtım sitesinin metin, görsel ve başlık düzenleyicisi.
Orijinal dosyalara dokunulmaz; değişen sayfa ayrı klasöre yazılır ve sunucu önce onu servis eder."""
import base64
import hashlib
import os
import re

from bs4 import BeautifulSoup
from fastapi import Depends, HTTPException

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def site_dir():
    for c in (os.environ.get("SITE_DIR"), os.path.join(ROOT, "onlinekaydet.com"), os.path.join(ROOT, "site")):
        if c and os.path.isdir(c):
            return c
    return os.path.join(ROOT, "site")


def ovr_dir():
    d = os.environ.get("ANASITE_DIR") or os.path.join(HERE, "anasite_ozel")
    os.makedirs(os.path.join(d, "img"), exist_ok=True)
    return d


NAME = re.compile(r"^[a-z0-9][a-z0-9\-_.]{0,80}\.html$")
TAGS = ("h1", "h2", "h3", "h4", "p", "li", "a", "button", "summary", "blockquote", "td", "th", "label", "figcaption", "dt", "dd")


def _read(name, ovr=True):
    if not NAME.match(name):
        raise HTTPException(400, "Geçersiz sayfa adı")
    for base in ((ovr_dir(),) if ovr else ()) + (site_dir(),):
        fp = os.path.join(base, name)
        if os.path.isfile(fp):
            return open(fp, encoding="utf-8").read(), base == ovr_dir()
    raise HTTPException(404, "Sayfa yok")


def _leaf_nodes(soup):
    out = []
    for el in soup.find_all(TAGS):
        if el.find_parent(["script", "style", "noscript"]):
            continue
        if any(getattr(c, "name", None) for c in el.children):
            continue
        t = el.get_text().strip()
        if t:
            out.append(el)
    return out


def items(html):
    soup = BeautifulSoup(html, "html.parser")
    res = []
    if soup.title:
        res.append({"k": "title", "tip": "baslik", "ad": "Sekme başlığı (title)", "v": soup.title.get_text().strip()})
    md = soup.find("meta", attrs={"name": "description"})
    if md:
        res.append({"k": "desc", "tip": "baslik", "ad": "Arama sonucu açıklaması", "v": md.get("content", "")})
    for i, el in enumerate(_leaf_nodes(soup)):
        res.append({"k": "t%d" % i, "tip": "metin", "ad": el.name, "v": el.get_text().strip()})
    for i, im in enumerate(soup.find_all("img")):
        s = im.get("src") or ""
        res.append({"k": "i%d" % i, "tip": "gorsel", "ad": im.get("alt") or "Görsel", "v": s if not s.startswith("data:") else "(gömülü görsel)", "gomulu": s.startswith("data:")})
    return res


def apply(html, edits):
    soup = BeautifulSoup(html, "html.parser")
    nodes = _leaf_nodes(soup)
    imgs = soup.find_all("img")
    for k, v in (edits or {}).items():
        if not isinstance(v, str) or len(v) > 4000:
            continue
        if k == "title" and soup.title:
            soup.title.string = v
        elif k == "desc":
            m = soup.find("meta", attrs={"name": "description"})
            if m:
                m["content"] = v
        elif re.fullmatch(r"t\d+", k) and int(k[1:]) < len(nodes):
            nodes[int(k[1:])].string = v
        elif re.fullmatch(r"i\d+", k) and int(k[1:]) < len(imgs):
            if re.match(r"^(/[\w\-./%]{1,200}|https://[^\s\"'<>]{4,300})$", v):
                imgs[int(k[1:])]["src"] = v
                for a in ("srcset", "data-src"):
                    if imgs[int(k[1:])].has_attr(a):
                        del imgs[int(k[1:])][a]
    return str(soup)


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    @api_router.get("/admin/anasite/sayfalar")
    async def sayfalar(_: dict = Depends(require_admin)):
        d, o = site_dir(), ovr_dir()
        out = []
        for f in sorted(os.listdir(d)):
            if f.endswith(".html") and NAME.match(f):
                t = ""
                try:
                    m = re.search(r"<title>(.*?)</title>", open(os.path.join(d, f), encoding="utf-8").read(6000), re.S)
                    t = m.group(1).strip() if m else ""
                except Exception:
                    pass
                out.append({"name": f, "title": t, "edited": os.path.isfile(os.path.join(o, f))})
        return {"pages": out}

    @api_router.get("/admin/anasite/sayfa")
    async def sayfa(name: str, _: dict = Depends(require_admin)):
        h, ed = _read(name)
        return {"name": name, "edited": ed, "items": items(h)}

    @api_router.put("/admin/anasite/sayfa")
    async def sayfa_kaydet(payload: dict, _: dict = Depends(require_admin)):
        name = str(payload.get("name") or "")
        h, _e = _read(name)
        out = apply(h, payload.get("edits") or {})
        with open(os.path.join(ovr_dir(), name), "w", encoding="utf-8") as f:
            f.write(out)
        return {"ok": True}

    @api_router.delete("/admin/anasite/sayfa")
    async def sayfa_sifirla(name: str, _: dict = Depends(require_admin)):
        _read(name, ovr=False)
        fp = os.path.join(ovr_dir(), name)
        if os.path.isfile(fp):
            os.remove(fp)
        return {"ok": True}

    @api_router.post("/admin/anasite/gorsel")
    async def gorsel(payload: dict, _: dict = Depends(require_admin)):
        m = re.match(r"^data:image/(png|jpeg|webp|gif|svg\+xml);base64,(.+)$", str(payload.get("data") or ""), re.S)
        if not m:
            raise HTTPException(400, "PNG, JPG, WEBP, GIF veya SVG yükleyin")
        raw = base64.b64decode(m.group(2))
        if len(raw) > 4_000_000:
            raise HTTPException(400, "Görsel 4 MB'ı geçmesin")
        ext = {"jpeg": "jpg", "svg+xml": "svg"}.get(m.group(1), m.group(1))
        fn = hashlib.sha1(raw).hexdigest()[:14] + "." + ext
        with open(os.path.join(ovr_dir(), "img", fn), "wb") as f:
            f.write(raw)
        return {"url": "/anasite-gorsel/" + fn}

    @api_router.get("/admin/temalar")
    async def temalar(_: dict = Depends(require_admin)):
        import json
        T = json.load(open(os.path.join(HERE, "themes.json"), encoding="utf-8"))
        return {"themes": [{"slug": t["slug"], "name": t.get("name") or t["slug"], "sector": t.get("sector") or "", "dark": bool(t.get("dark")), "premium": bool(t.get("premium"))} for t in T]}
