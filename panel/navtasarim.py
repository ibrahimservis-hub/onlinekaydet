"""Hazır temanın üst menüsü, mobil menüsü ve mobil alt çubuğu için tasarım katmanı.
Tema dosyalarına dokunmaz: seçilen renk, boyut, düğme ve sıra ayarlarını tema HTML'ine uygular."""
import copy
import re

from bs4 import BeautifulSoup, NavigableString

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
HREF = re.compile(r"^(#[\w-]{0,60}|/[\w\-./?=&%#]{0,200}|tel:\+?[\d ]{5,20}|mailto:[^\s<>\"']{3,80}|https?://[^\s<>\"']{4,300})$")

# 24x24, çizgi stili temadaki simgelerle aynı
ICONS = {
    "telefon": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
    "whatsapp": '<path d="M4 20l1.3-4A8 8 0 1 1 8 18.7z"/><path d="M9 9.5c.3 2 2 3.8 4.5 4.5l1-1.2-1.8-.9-.7.7c-.8-.4-1.5-1.1-1.9-1.9l.7-.7-.9-1.8z"/>',
    "randevu": '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
    "konum": '<path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "magaza": '<path d="M4 9l1-4h14l1 4M4 9v10h16V9M4 9h16"/><path d="M9 19v-5h6v5"/>',
    "instagram": '<rect x="4" y="4" width="16" height="16" rx="5"/><circle cx="12" cy="12" r="3.5"/><path d="M17 7h.01"/>',
    "bilgi": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
}
ICON_AD = {"telefon": "Telefon", "whatsapp": "WhatsApp", "randevu": "Randevu", "konum": "Konum", "mail": "E-posta",
           "magaza": "Mağaza", "instagram": "Instagram", "bilgi": "Bilgi", "menu": "Menü"}


def _renk(v):
    v = str(v or "").strip()
    return v.lower() if HEX.match(v) else ""


def _yazi(v, n):
    return re.sub(r"\s+", " ", str(v or "")).strip()[:n]


def _href(v):
    v = str(v or "").strip()
    return v if HREF.match(v) else ""


def _sayi(v, lo, hi):
    try:
        n = int(float(v))
    except (TypeError, ValueError):
        return 0
    return 0 if n <= 0 else max(lo, min(hi, n))


def clean(x):
    """Panelden gelen ayarı güvenli, sınırlı bir biçime indirir."""
    x = x if isinstance(x, dict) else {}
    u, d, b = (x.get("ust") or {}), (x.get("drw") or {}), (x.get("bar") or {})
    out = {
        "ust": {"sticky": u.get("sticky") if u.get("sticky") in ("sticky", "static") else "",
                "bg": _renk(u.get("bg")), "fg": _renk(u.get("fg")), "cta_bg": _renk(u.get("cta_bg")),
                "cta_off": bool(u.get("cta_off")), "cta_text": _yazi(u.get("cta_text"), 28), "cta_link": _href(u.get("cta_link")),
                "logo_boy": _sayi(u.get("logo_boy"), 20, 120), "golge": bool(u.get("golge")), "cizgi": bool(u.get("cizgi"))},
        "drw": {"bg": _renk(d.get("bg")), "fg": _renk(d.get("fg")), "boyut": _sayi(d.get("boyut"), 14, 40),
                "chips_off": bool(d.get("chips_off")), "cta_off": bool(d.get("cta_off"))},
    }
    edit = {}
    for k, v in (b.get("edit") or {}).items():
        if not str(k).isdigit() or int(k) > 30 or not isinstance(v, dict):
            continue
        e = {"off": bool(v.get("off")), "l": _yazi(v.get("l"), 18), "h": _href(v.get("h"))}
        if e["off"] or e["l"] or e["h"]:
            edit[str(int(k))] = e
    extra = []
    for e in (b.get("extra") or [])[:3]:
        if isinstance(e, dict) and _yazi(e.get("l"), 18) and _href(e.get("h")):
            extra.append({"l": _yazi(e.get("l"), 18), "h": _href(e.get("h")), "ic": e.get("ic") if e.get("ic") in ICONS else "bilgi"})
    order = []
    for i in (b.get("order") or [])[:30]:
        if isinstance(i, (int, float, str)) and str(i).isdigit() and int(i) not in order and int(i) <= 30:
            order.append(int(i))
    out["bar"] = {"off": bool(b.get("off")), "bg": _renk(b.get("bg")), "fg": _renk(b.get("fg")), "ac": _renk(b.get("ac")),
                  "labels_off": bool(b.get("labels_off")), "edit": edit, "extra": extra, "order": order}
    return out


def bos(nav):
    """Hiçbir ayar yapılmamış mı?"""
    if not nav:
        return True
    n = clean(nav)
    return not any(any(bool(v) for v in n[k].values()) for k in n)


def _kontrast(hx):
    r, g, b = int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16)
    return "#111111" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#ffffff"


def _kok(block_html):
    soup = BeautifulSoup(block_html, "html.parser")
    ed = soup.find(class_="ed")
    root = next((c for c in (ed.children if ed else soup.children) if getattr(c, "name", None)), None)
    return soup, ed, root


def _etiket_koy(a, text):
    """Bağlantının yazısını değiştirir; simge ve yapıyı korur."""
    span = [s for s in a.find_all("span") if not s.find("svg")]
    if span:
        span[-1].string = text
        return
    nodes = [n for n in a.find_all(string=True, recursive=True) if isinstance(n, NavigableString) and n.strip()]
    if nodes:
        nodes[0].replace_with(text)
        for n in nodes[1:]:
            n.replace_with("")
    else:
        a.append(NavigableString(text))


def _etiket_oku(a):
    span = [s for s in a.find_all("span") if not s.find("svg") and s.get_text(strip=True)]
    return (span[-1].get_text(strip=True) if span else a.get_text(" ", strip=True))[:30]


def _bar_ogeleri(root):
    return [a for a in root.find_all("a")]


def _ust_cta(root):
    """Üst menüdeki çağrı düğmesi: menü listesinin dışındaki düğme biçimli bağlantı."""
    for a in root.find_all("a"):
        if a.find_parent("nav") is not None or a.find_parent(class_="lg") is not None:
            continue
        cl = " ".join(a.get("class") or [])
        if a.get("class") and a.get("class")[0] in ("lg",):
            continue
        if re.search(r"btn|cta", cl):
            return a
    return None


def ogrenme(menu_html, drw_html, bar_html):
    """Panelde gösterilecek mevcut öğeler (tema orijinali)."""
    out = {"cta": None, "bar": [], "drw": {"chips": False, "cta": False}}
    if menu_html:
        _s, _e, root = _kok(menu_html)
        a = _ust_cta(root) if root else None
        if a:
            out["cta"] = {"l": _etiket_oku(a), "h": a.get("href") or ""}
    if drw_html:
        _s, _e, root = _kok(drw_html)
        if root:
            out["drw"] = {"chips": root.find(class_="chips") is not None, "cta": root.find(class_="dc") is not None}
    if bar_html:
        _s, _e, root = _kok(bar_html)
        if root:
            for i, a in enumerate(_bar_ogeleri(root)):
                out["bar"].append({"i": i, "l": _etiket_oku(a), "h": a.get("href") or "", "fab": "fab" in (a.get("class") or [])})
    return out


def _stil(css, root, ed):
    st = BeautifulSoup("<style>%s</style>" % css, "html.parser").style
    (ed or root.parent).append(st)


def _ust(html, c):
    soup, ed, root = _kok(html)
    if not root:
        return html
    root["data-oknav"] = "ust"
    css = []
    if c["sticky"] == "sticky":
        css.append('[data-oknav="ust"]{position:sticky!important;top:0!important;z-index:60!important}')
    elif c["sticky"] == "static":
        css.append('[data-oknav="ust"]{position:relative!important;top:auto!important}')
    if c["bg"]:
        css.append('[data-oknav="ust"]{background:%s!important;backdrop-filter:none!important}' % c["bg"])
    if c["fg"]:
        css.append('[data-oknav="ust"],[data-oknav="ust"] a:not([data-oknav-cta]),[data-oknav="ust"] .ln,[data-oknav="ust"] label{color:%s!important}' % c["fg"])
    if c["logo_boy"]:
        css.append('[data-oknav="ust"] img{height:%dpx!important;width:auto!important;max-height:none!important}' % c["logo_boy"])
    if c["golge"]:
        css.append('[data-oknav="ust"]{box-shadow:0 6px 24px rgba(0,0,0,.18)!important}')
    if c["cizgi"]:
        css.append('[data-oknav="ust"]{border-bottom:1px solid rgba(128,128,128,.35)!important}')
    cta = _ust_cta(root)
    if cta is not None:
        if c["cta_off"]:
            cta.decompose()
        else:
            cta["data-oknav-cta"] = "1"
            if c["cta_text"]:
                _etiket_koy(cta, c["cta_text"])
            if c["cta_link"]:
                cta["href"] = c["cta_link"]
            if c["cta_bg"]:
                css.append('[data-oknav-cta]{background:%s!important;border-color:%s!important;color:%s!important}' % (c["cta_bg"], c["cta_bg"], _kontrast(c["cta_bg"])))
    if css:
        _stil("".join(css), root, ed)
    return str(soup)


def _drw(html, c):
    soup, ed, root = _kok(html)
    if not root:
        return html
    root["data-oknav"] = "drw"
    css = []
    if c["bg"]:
        css.append('[data-oknav="drw"]{background:%s!important}' % c["bg"])
    if c["fg"]:
        css.append('[data-oknav="drw"],[data-oknav="drw"] a:not(.btn),[data-oknav="drw"] .ln,[data-oknav="drw"] .lg,[data-oknav="drw"] .x,[data-oknav="drw"] .dl a small{color:%s!important}' % c["fg"])
    if c["boyut"]:
        css.append('[data-oknav="drw"] .dl a{font-size:%dpx!important;line-height:1.25!important}' % c["boyut"])
    if c["chips_off"]:
        ch = root.find(class_="chips")
        if ch is not None:
            (ch.parent if ch.parent is not root else ch).decompose()
    if c["cta_off"]:
        dc = root.find(class_="dc")
        if dc is not None:
            dc.decompose()
    if css:
        _stil("".join(css), root, ed)
    return str(soup)


def _bar(html, c):
    """None dönerse çubuk tamamen kaldırılır."""
    if c["off"]:
        return None
    soup, ed, root = _kok(html)
    if not root:
        return html
    root["data-oknav"] = "bar"
    css = []
    ogeler = _bar_ogeleri(root)
    n = len(ogeler)
    proto = next((a for a in ogeler if "fab" not in (a.get("class") or [])), ogeler[0] if ogeler else None)
    for k, e in c["edit"].items():
        i = int(k)
        if i >= n:
            continue
        a = ogeler[i]
        if e["off"]:
            a["data-oknav-off"] = "1"
            continue
        if e["l"]:
            _etiket_koy(a, e["l"])
        if e["h"]:
            a["href"] = e["h"]
    yeni = []
    if proto is not None:
        for e in c["extra"]:
            a = copy.copy(proto)
            for k in ("data-oknav-off", "id", "onclick", "data-pg"):
                a.attrs.pop(k, None)
            cl = [x for x in (a.get("class") or []) if x not in ("fab", "on", "act")]
            if cl:
                a["class"] = cl
            elif "class" in a.attrs:
                del a["class"]
            a["href"] = e["h"]
            if e["h"].startswith("http"):
                a["target"], a["rel"] = "_blank", "noopener"
            sv = a.find("svg")
            if sv is not None:
                sv.clear()
                for part in BeautifulSoup(ICONS[e["ic"]], "html.parser").contents:
                    sv.append(copy.copy(part))
            _etiket_koy(a, e["l"])
            yeni.append(a)
    tum = ogeler + yeni
    host = ogeler[0].parent if ogeler else None
    sira = [i for i in c["order"] if i < len(tum)] + [i for i in range(len(tum)) if i not in c["order"]]
    if host is not None and all(a.parent is host for a in ogeler):
        for a in tum:
            if a.parent is not None:
                a.extract()
        for i in sira:
            host.append(tum[i])
    elif yeni and ogeler:
        ogeler[-1].insert_after(*yeni)
    for a in list(root.find_all("a")):
        if a.get("data-oknav-off"):
            a.decompose()
    if c["extra"] or c["order"] or any(e["off"] for e in c["edit"].values()):
        kal = [a for a in root.find_all("a") if a.parent is host] if host is not None else []
        if kal:                                    # temada sabit sütun sayısı varsa yeni düğme alt satıra düşmesin
            css.append('[data-oknav="bar"]{grid-template-columns:%s!important}' % " ".join(
                "minmax(56px,auto)" if "fab" in (a.get("class") or []) else "minmax(0,1fr)" for a in kal))
    if c["bg"]:
        css.append('[data-oknav="bar"]{background:%s!important}' % c["bg"])
    if c["fg"]:
        css.append('[data-oknav="bar"] a:not(.fab){color:%s!important}' % c["fg"])
    if c["ac"]:
        css.append('[data-oknav="bar"] a.fab,[data-oknav="bar"] .fab{background:%s!important;color:%s!important}' % (c["ac"], _kontrast(c["ac"])))
    if c["labels_off"]:
        css.append('[data-oknav="bar"] a span{display:none!important}')
    if css:
        _stil("".join(css), root, ed)
    return str(soup)


def apply(blocks, nav):
    """blocks: [[ad, html], ...]. Ayar yoksa listeye hiç dokunmaz."""
    if bos(nav):
        return blocks
    n = clean(nav)
    out = []
    for b in blocks:
        ad, h = b[0], b[1]
        try:
            if ad == "Menü" and any(n["ust"].values()):
                h = _ust(h, n["ust"])
            elif ad == "Mobil menü" and any(n["drw"].values()):
                h = _drw(h, n["drw"])
            elif ad == "Mobil bar" and any(bool(v) for v in n["bar"].values()):
                h = _bar(h, n["bar"])
                if h is None:
                    continue
        except Exception:                                          # noqa: BLE001
            pass                                                   # tasarım katmanı siteyi asla düşürmez
        out.append([ad, h] + list(b[2:]))
    return out


# ---------------------------------------------------------------- tüm tema (renk, yazı tipi, köşe, düğme)
TW_RENK = ("ac", "dk", "bg", "ink", "sf")
TW_KOSE = {"keskin": 0, "yumusak": 10, "yuvarlak": 18}
TW_DUGME = {"keskin": "0", "orta": "10px", "hap": "999px"}


def _fontlar():
    import sitegen
    return sitegen.FONTS


def tw_clean(x):
    x = x if isinstance(x, dict) else {}
    f = _fontlar()
    out = {k: _renk(x.get(k)) for k in TW_RENK}
    out["fd"] = x.get("fd") if x.get("fd") in f else ""
    out["fb"] = x.get("fb") if x.get("fb") in f else ""
    out["kose"] = x.get("kose") if x.get("kose") in TW_KOSE else ""
    out["dugme"] = x.get("dugme") if x.get("dugme") in TW_DUGME else ""
    out["yazi"] = _sayi(x.get("yazi"), 90, 125)          # genel yazı boyutu, % olarak
    return out


def tw_bos(tw):
    return not tw or not any(tw_clean(tw).values())


def tw_html(tw):
    """<head> sonuna konacak tek bir <style> (+ yazı tipi bağlantısı). Ayar yoksa boş döner."""
    if tw_bos(tw):
        return ""
    t = tw_clean(tw)
    v = []
    for k in TW_RENK:
        if t[k]:
            v.append("--%s:%s!important" % (k, t[k]))
    if t["ac"]:
        v.append("--on-ac:%s!important" % _kontrast(t["ac"]))
    if t["kose"]:
        v.append("--r:%dpx!important" % TW_KOSE[t["kose"]])
    used = []
    if t["fd"]:
        v.append("--fd:'%s',serif!important" % t["fd"])
        used.append(t["fd"])
    if t["fb"]:
        v.append("--fb:'%s',sans-serif!important" % t["fb"])
        used.append(t["fb"])
    css = []
    if v:
        css.append(":root{%s}" % ";".join(v))
    if t["fb"]:
        css.append("body{font-family:var(--fb)!important}")
    if t["fd"]:
        css.append("h1,h2,h3,h4{font-family:var(--fd)!important}")
    if t["bg"]:
        css.append("body{background:var(--bg)!important}")
    if t["ink"]:
        css.append("body{color:var(--ink)!important}")
    if t["dugme"]:
        css.append(".btn,button.btn,a.btn,.cta,.bk,.b1,.b2{border-radius:%s!important}" % TW_DUGME[t["dugme"]])
    if t["yazi"]:
        css.append("html{font-size:%d%%!important}" % t["yazi"])
    import sitegen
    link = sitegen.font_link(used)
    return link + '<style id="oktw">' + "".join(css) + "</style>"
