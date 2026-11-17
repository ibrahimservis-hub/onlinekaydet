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
        if el.find_parent(["script", "style", "noscript"]) or el.find_parent(class_="duy"):
            continue
        if any(getattr(c, "name", None) for c in el.children):
            continue
        t = el.get_text().strip()
        if t:
            out.append(el)
    return out


_LINK_OK = re.compile(r"^(/[\w\-./%?=&#]{0,200}|#[\w-]{1,60}|https://[^\s\"'<>]{4,300}|tel:[+\d]{5,20}|mailto:[^\s\"'<>]{3,120})$")


def _serit_parts(d):
    sp = d.find("span")
    b = sp.find("b") if sp else None
    a = d.find("a")
    t = ""
    if sp:
        t = "".join(str(c) for c in sp.children if not (getattr(c, "name", None) == "b")).strip()
        t = BeautifulSoup(t, "html.parser").get_text().strip()
    return sp, b, a, t


def _serit_items(soup):
    """Sayfanın üstündeki duyuru şeridi (.duy): açık/kapalı, kalın başlık, yazı, bağlantı yazısı ve adresi."""
    d = soup.find(class_="duy")
    if not d:
        return []
    sp, b, a, t = _serit_parts(d)
    return [
        {"k": "duy_on", "tip": "serit", "ad": "Şerit görünsün mü", "v": "0" if d.has_attr("hidden") else "1", "sec": True},
        {"k": "duy_b", "tip": "serit", "ad": "Kalın başlık", "v": b.get_text().strip() if b else ""},
        {"k": "duy_t", "tip": "serit", "ad": "Yazı", "v": t},
        {"k": "duy_lt", "tip": "serit", "ad": "Bağlantı yazısı", "v": a.get_text().strip() if a else ""},
        {"k": "duy_lu", "tip": "serit", "ad": "Bağlantı adresi (/sayfa, #bolum, https://…, tel:…)", "v": (a.get("href") or "") if a else ""},
    ]


def _serit_apply(soup, edits):
    d = soup.find(class_="duy")
    if not d or not any(k.startswith("duy_") for k in edits):
        return
    sp, b, a, t = _serit_parts(d)
    nb = edits.get("duy_b", b.get_text().strip() if b else "")
    nt = edits.get("duy_t", t)
    if sp is not None and ("duy_b" in edits or "duy_t" in edits):
        sp.clear()
        if nb.strip():
            nb_tag = soup.new_tag("b")
            nb_tag.string = nb.strip()
            sp.append(nb_tag)
            sp.append(" ")
        sp.append(nt.strip())
    if a is not None:
        if "duy_lt" in edits:
            a.string = edits["duy_lt"].strip()
        if "duy_lu" in edits and _LINK_OK.match(edits["duy_lu"].strip()):
            a["href"] = edits["duy_lu"].strip()
    if "duy_on" in edits:
        if edits["duy_on"] == "0":
            d["hidden"] = ""
            d["style"] = "display:none"
        else:
            if d.has_attr("hidden"):
                del d["hidden"]
            if d.has_attr("style"):
                del d["style"]


def items(html):
    soup = BeautifulSoup(html, "html.parser")
    res = []
    if soup.title:
        res.append({"k": "title", "tip": "baslik", "ad": "Sekme başlığı (title)", "v": soup.title.get_text().strip()})
    md = soup.find("meta", attrs={"name": "description"})
    if md:
        res.append({"k": "desc", "tip": "baslik", "ad": "Arama sonucu açıklaması", "v": md.get("content", "")})
    res.extend(_serit_items(soup))
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
    _serit_apply(soup, {k: v for k, v in (edits or {}).items() if isinstance(v, str) and len(v) <= 400 and k.startswith("duy_")})
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
