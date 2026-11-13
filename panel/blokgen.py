# -*- coding: utf-8 -*-
"""Bölüm sayfalarını HTML'e çevirir.

Paneldeki "Bölüm ekle" ekranında kurulan sayfalar (yp_pages) burada siteye basılır.
Her bölümün 19 yerleşim türünden biri vardır; yerleşim türü başına bir üretici yazılır,
içerik bölümün kendi alanlarından (set) gelir. Telefonda set_m değerleri set'in üzerine biner,
dokunulmayan ayar bilgisayardakini miras alır.

Ürün, hizmet, ekip ve yorum gibi listeler işletmenin kendi kayıtlarından beslenir;
kayıt yoksa bölüm sessizce boş çıkar, asla "örnek içerik" basılmaz.
"""
import html as _h
import json
import re

E = _h.escape


# ---------------------------------------------------------------- değerler
def v(b, k, dev="", d=None):
    """Bölümün bir ayarı. Telefonda set_m varsa o, yoksa set, yoksa verilen varsayılan."""
    if dev == "phone":
        sm = b.get("set_m") or {}
        if k in sm:
            return sm[k]
    s = b.get("set") or {}
    return s[k] if k in s else d


def lines(s, parts=1):
    """Çok satırlı alanı satırlara böler. Satır içi parçalar | ile ayrılır."""
    out = []
    for ln in str(s or "").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        p = [x.strip() for x in ln.split("|")]
        while len(p) < parts:
            p.append("")
        out.append(p)
    return out


def img_url(k):
    k = str(k or "").strip()
    if not k:
        return ""
    if k.startswith("http") or k.startswith("/"):
        return k
    return "/api/public/site-img/" + k


def _n(x, d=0):
    try:
        return int(x)
    except (TypeError, ValueError):
        return d


def para(x):
    """1234.5 -> 1.234,50"""
    try:
        f = float(x)
    except (TypeError, ValueError):
        return ""
    t = "%0.2f" % f
    tam, kus = t.split(".")
    neg = tam.startswith("-")
    tam = tam.lstrip("-")
    g = ""
    while len(tam) > 3:
        g = "." + tam[-3:] + g
        tam = tam[:-3]
    return ("-" if neg else "") + tam + g + ("," + kus if kus != "00" else "")


def tel_goster(t):
    """5331112233 -> 0533 111 22 33"""
    d = re.sub(r"\D", "", str(t or ""))
    if d.startswith("90") and len(d) == 12:
        d = "0" + d[2:]
    if len(d) == 10:
        d = "0" + d
    if len(d) == 11 and d.startswith("0"):
        return "%s %s %s %s" % (d[:4], d[4:7], d[7:9], d[9:])
    return str(t or "").strip()


def link(t):
    """Düğme hedefi: yalnız kendi sitemiz ya da https, telefon ve e-posta."""
    t = str(t or "").strip()
    if not t:
        return ""
    if re.fullmatch(r"(/[A-Za-z0-9\-/_?=&.%#]{0,180}|https://[^\s\"'<>]{3,200}|tel:[+0-9 ]{3,24}|mailto:[^\s\"'<>]{3,120}|#[A-Za-z0-9\-_]{1,60})", t):
        return t
    return ""


# ---------------------------------------------------------------- ortak parçalar
def _style(b, dev):
    """Bölümün kendi rengi, boşluğu, köşesi ve yazı tipi."""
    st = []
    bg, col = v(b, "bg", dev), v(b, "color", dev)
    if bg:
        st.append("--bk-bg:%s" % E(str(bg)))
    if col:
        st.append("--bk-fg:%s" % E(str(col)))
    st.append("--bk-pad:%dpx" % max(0, min(_n(v(b, "pad", dev, 56), 56), 160)))
    st.append("--bk-r:%dpx" % max(0, min(_n(v(b, "radius", dev, 12), 12), 40)))
    for k, var in (("font_h", "--bk-fh"), ("font_b", "--bk-fb")):
        f = v(b, k, dev)
        if f:
            st.append("%s:'%s'" % (var, E(str(f).replace("'", ""))))
    return ";".join(st)


def _cols(b, dev, d=3):
    c = _n(v(b, "cols", dev, d), d)
    cm = str(v(b, "cols_m", dev, "2"))
    return max(1, min(c, 6)), cm


def _head(b, dev, orta=False):
    t, s = v(b, "title", dev, ""), v(b, "sub", dev, "")
    if not t and not s:
        return ""
    return '<div class="bk-h%s">%s%s</div>' % (
        " bk-c" if orta else "",
        ("<h2>%s</h2>" % E(str(t))) if t else "",
        ("<p>%s</p>" % E(str(s))) if s else "")


def _cta(b, dev, cls="bk-btn"):
    t, to = v(b, "cta", dev, ""), link(v(b, "cta_to", dev, ""))
    if not t:
        return ""
    return '<a class="%s" href="%s">%s</a>' % (cls, E(to or "#"), E(str(t)))


def sec(b, inner, dev, extra=""):
    if not inner:
        return ""
    return '<section class="bk bkw-%s%s" style="%s"><div class="bk-w">%s</div></section>' % (
        E(b["wire"]), (" " + extra) if extra else "", _style(b, dev), inner)


def _grid(items, c, cm, cls="bk-g"):
    return '<div class="%s" style="--c:%d;--cm:%s">%s</div>' % (
        cls, c, ("auto" if cm == "kaydırmalı" else E(cm)), "".join(items))


def _card(img, t, s, to="", ek=""):
    h = ""
    if img:
        h += '<img src="%s" alt="%s" loading="lazy">' % (E(img_url(img)), E(str(t or "")))
    h += '<div class="bk-cb">'
    if t:
        h += "<h3>%s</h3>" % E(str(t))
    if s:
        h += "<p>%s</p>" % E(str(s))
    h += ek + "</div>"
    if to:
        return '<a class="bk-card" href="%s">%s</a>' % (E(to), h)
    return '<div class="bk-card">%s</div>' % h


# ---------------------------------------------------------------- yerleşimler
def w_hero(b, dev, d):
    im = v(b, "img", dev, "")
    al = str(v(b, "align", dev, "sol"))
    t, s = v(b, "title", dev, ""), v(b, "sub", dev, "")
    if not (t or s or im):
        return ""
    inner = '<div class="bk-hero bk-a-%s">%s%s%s</div>' % (
        {"orta": "c", "sağ": "r"}.get(al, "l"),
        ("<h1>%s</h1>" % E(str(t))) if t else "",
        ("<p>%s</p>" % E(str(s))) if s else "",
        _cta(b, dev))
    st = _style(b, dev)
    if im:
        st += ";background-image:linear-gradient(rgba(10,20,34,.52),rgba(10,20,34,.52)),url('%s')" % E(img_url(im))
    return ('<section class="bk bkw-hero%s" style="%s"><div class="bk-w">%s</div></section>'
            % (" bk-ov" if im else "", st, inner))


def w_split(b, dev, d):
    im = v(b, "img", dev, "")
    t, s = v(b, "title", dev, ""), v(b, "sub", dev, "")
    if not (t or s or im):
        return ""
    sol = '<div class="bk-sx">%s%s%s</div>' % (
        ("<h2>%s</h2>" % E(str(t))) if t else "",
        ("<p>%s</p>" % E(str(s))) if s else "", _cta(b, dev))
    sag = ('<img src="%s" alt="" loading="lazy">' % E(img_url(im))) if im else ""
    return sec(b, '<div class="bk-split">%s%s</div>' % (sol, sag), dev)


def w_g3(b, dev, d):
    c, cm = _cols(b, dev, 3)
    it = d.get("cards") or [(x[0], x[1], x[2] if len(x) > 2 else "", "") for x in lines(v(b, "items", dev, ""), 3)]
    if not it and not v(b, "title", dev, ""):
        return ""
    ks = [_card(x[3] if len(x) > 3 else "", x[0], x[1], link(x[2]) if len(x) > 2 else "") for x in it]
    return sec(b, _head(b, dev, True) + (_grid(ks, c, cm) if ks else ""), dev)


def w_g6(b, dev, d):
    c, cm = _cols(b, dev, 4)
    it = d.get("cards") or [(x[0], x[1], x[2], "") for x in lines(v(b, "items", dev, ""), 3)]
    if not it and not v(b, "title", dev, ""):
        return ""
    ks = [_card(x[3] if len(x) > 3 else "", x[0], x[1], link(x[2]) if len(x) > 2 else "") for x in it]
    alt = ""
    at, ato = v(b, "all_text", dev, ""), link(v(b, "all_to", dev, ""))
    if at:
        alt = '<div class="bk-c" style="margin-top:18px"><a class="bk-btn" href="%s">%s</a></div>' % (E(ato or "#"), E(str(at)))
    return sec(b, _head(b, dev, True) + (_grid(ks, c, cm) if ks else "") + alt, dev)


def w_g5(b, dev, d):
    ims = v(b, "imgs", dev, []) or []
    if not isinstance(ims, list) or not ims:
        return sec(b, _head(b, dev, True), dev) if v(b, "title", dev, "") else ""
    ks = ['<div class="bk-lg"><img src="%s" alt="" loading="lazy"></div>' % E(img_url(k)) for k in ims[:30]]
    return sec(b, _head(b, dev, True) + _grid(ks, 5, "3"), dev)


def w_g2(b, dev, d):
    sol, sag = v(b, "left", dev, ""), v(b, "right", dev, "")
    if not (sol or sag):
        return ""
    def blok(x):
        return "".join("<p>%s</p>" % E(p[0]) for p in lines(x))
    return sec(b, '<div class="bk-2">%s%s</div>' % ("<div>%s</div>" % blok(sol), "<div>%s</div>" % blok(sag)), dev)


def w_rows(b, dev, d):
    it = d.get("rows") or lines(v(b, "items", dev, ""), 2)
    if not it and not v(b, "title", dev, ""):
        return ""
    ks = "".join('<li><b>%s</b>%s</li>' % (E(x[0]), ("<span>%s</span>" % E(x[1])) if len(x) > 1 and x[1] else "") for x in it)
    return sec(b, _head(b, dev) + ('<ul class="bk-rows">%s</ul>' % ks if ks else ""), dev)


def w_stat(b, dev, d):
    it = lines(v(b, "items", dev, ""), 2)
    if not it:
        return ""
    ks = ['<div class="bk-st"><b>%s</b><span>%s</span></div>' % (E(x[0]), E(x[1])) for x in it[:8]]
    return sec(b, _head(b, dev, True) + _grid(ks, min(len(ks), 4), "2"), dev)


def w_quote(b, dev, d):
    it = d.get("quotes") or lines(v(b, "items", dev, ""), 2)
    if not it:
        return sec(b, _head(b, dev, True), dev) if v(b, "title", dev, "") else ""
    c, cm = _cols(b, dev, 3)
    ks = ['<figure class="bk-q"><blockquote>%s</blockquote>%s</figure>' % (
        E(x[0]), ("<figcaption>%s</figcaption>" % E(x[1])) if len(x) > 1 and x[1] else "") for x in it]
    return sec(b, _head(b, dev, True) + _grid(ks, c, cm), dev)


def w_faq(b, dev, d):
    it = d.get("rows") or lines(v(b, "items", dev, ""), 2)
    if not it:
        return sec(b, _head(b, dev), dev) if v(b, "title", dev, "") else ""
    ks = "".join('<details><summary>%s</summary><div>%s</div></details>' % (E(x[0]), E(x[1])) for x in it)
    return sec(b, _head(b, dev) + ('<div class="bk-faq">%s</div>' % ks), dev)


def w_logos(b, dev, d):
    ims = v(b, "imgs", dev, []) or []
    if not isinstance(ims, list) or not ims:
        return ""
    ks = "".join('<img src="%s" alt="" loading="lazy">' % E(img_url(k)) for k in ims[:40])
    return sec(b, _head(b, dev, True) + ('<div class="bk-logos">%s</div>' % ks), dev)


def w_band(b, dev, d):
    t = v(b, "text", dev, "") or v(b, "title", dev, "")
    if not t:
        return ""
    return sec(b, '<div class="bk-band"><span>%s</span>%s</div>' % (E(str(t)), _cta(b, dev, "bk-btn bk-sm")), dev)


def w_cta(b, dev, d):
    t, s = v(b, "title", dev, ""), v(b, "sub", dev, "")
    if not (t or s):
        return ""
    return sec(b, '<div class="bk-c">%s%s%s</div>' % (
        ("<h2>%s</h2>" % E(str(t))) if t else "",
        ("<p>%s</p>" % E(str(s))) if s else "", _cta(b, dev)), dev)


def w_full(b, dev, d):
    sl = v(b, "slides", dev, []) or []
    if not isinstance(sl, list) or not sl:
        im = v(b, "img", dev, "")
        if not im:
            return ""
        sl = [im]
    ks = "".join('<li><img src="%s" alt="" loading="lazy"></li>' % E(img_url(k)) for k in sl[:12])
    return sec(b, _head(b, dev, True) + ('<ul class="bk-slide">%s</ul>' % ks), dev)


def w_video(b, dev, d):
    u = str(v(b, "video", dev, "") or "").strip()
    emb = ""
    m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/))([A-Za-z0-9_-]{6,20})", u)
    if m:
        emb = '<div class="bk-vid"><iframe src="https://www.youtube-nocookie.com/embed/%s" title="%s" loading="lazy" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div>' % (
            E(m.group(1)), E(str(v(b, "title", dev, "") or "Tanıtım videosu")))
    elif re.search(r"vimeo\.com/(\d+)", u):
        emb = '<div class="bk-vid"><iframe src="https://player.vimeo.com/video/%s" title="Video" loading="lazy" allowfullscreen></iframe></div>' % E(re.search(r"vimeo\.com/(\d+)", u).group(1))
    if not emb and not v(b, "title", dev, ""):
        return ""
    return sec(b, _head(b, dev, True) + emb + ('<div class="bk-c">%s</div>' % _cta(b, dev) if v(b, "cta", dev, "") else ""), dev)


def w_map(b, dev, d):
    ad = d.get("address") or ""
    if not ad:
        return ""
    z = max(1, min(_n(v(b, "zoom", dev, 15), 15), 20))
    src = "https://www.google.com/maps?q=%s&z=%d&output=embed" % (_h.escape(re.sub(r"\s+", "+", ad), quote=True), z)
    return sec(b, _head(b, dev) + '<div class="bk-map"><iframe src="%s" title="Harita: %s" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>' % (E(src), E(ad)), dev)


def w_form(b, dev, d):
    t, s = v(b, "title", dev, ""), v(b, "sub", dev, "")
    ph = v(b, "ph", dev, "") or "Aramak istediğinizi yazın"
    if not (t or s):
        return ""
    return sec(b, '<div class="bk-c">%s%s<form class="bk-form" action="/ara" method="get" role="search">'
                  '<label class="bk-sr" for="bkq-%s">%s</label>'
                  '<input id="bkq-%s" name="q" type="search" placeholder="%s"><button type="submit">Ara</button></form></div>' % (
                      ("<h2>%s</h2>" % E(str(t))) if t else "",
                      ("<p>%s</p>" % E(str(s))) if s else "",
                      E(b["iid"]), E(str(ph)), E(b["iid"]), E(str(ph))), dev)


def w_ba(b, dev, d):
    ims = v(b, "imgs", dev, []) or []
    if not isinstance(ims, list) or len(ims) < 2:
        return ""
    return sec(b, _head(b, dev, True) + '<div class="bk-ba"><figure><img src="%s" alt="Önce" loading="lazy"><figcaption>Önce</figcaption></figure>'
                  '<figure><img src="%s" alt="Sonra" loading="lazy"><figcaption>Sonra</figcaption></figure></div>' % (
                      E(img_url(ims[0])), E(img_url(ims[1]))), dev)


def w_drawer(b, dev, d):
    return ""                     # telefon menüsü sayfa akışına girmez, kabukta çizilir


WIRES = {"hero": w_hero, "split": w_split, "g3": w_g3, "g6": w_g6, "g5": w_g5, "g2": w_g2,
         "rows": w_rows, "stat": w_stat, "quote": w_quote, "faq": w_faq, "logos": w_logos,
         "band": w_band, "cta": w_cta, "full": w_full, "video": w_video, "map": w_map,
         "form": w_form, "ba": w_ba, "drawer": w_drawer}


OZEL = {}                 # bölüm kimliğine göre kendi üreticisi; blok_*.py dosyaları doldurur
EK_CSS = []               # kategori dosyalarının kendi stilleri
KABUK = {}                # sayfanın kabuğunu ayarlayan bölümler (menü, logo, alt bilgi)


def kayit_al(d, css="", kabuk=None):
    """Bir kategorinin kendi üreticilerini, stillerini ve kabuk katkılarını devreye alır."""
    OZEL.update(d)
    if css and css not in EK_CSS:
        EK_CSS.append(css)
    if kabuk:
        KABUK.update(kabuk)


def kabuk_ayar(rows, dev, data):
    """Kabuğu ayarlayan bölümlerin katkıları."""
    out = {}
    for b in rows:
        fn = KABUK.get(b.get("bid"))
        if not fn or not b.get("on", True):
            continue
        try:
            out.update({k: x for k, x in (fn(b, dev, (data or {}).get(b["iid"]) or {}) or {}).items() if x is not None})
        except Exception:                                          # noqa: BLE001
            continue
    return out


def block_html(b, dev="", data=None):
    """Bir bölümün HTML'i. Önce bölümün kendi üreticisi, yoksa yerleşim kalıbı."""
    if not b.get("on", True):
        return ""
    if dev == "phone" and v(b, "on_m", dev, True) is False:
        return ""
    fn = OZEL.get(b.get("bid")) or WIRES.get(b.get("wire"))
    if not fn:
        return ""
    try:
        return fn(b, dev, data or {})
    except Exception:                                          # noqa: BLE001
        return ""                                              # tek bölüm sayfayı düşürmez


# ---------------------------------------------------------------- sayfa kabuğu
CSS = (
    "*{box-sizing:border-box}"
    "body{margin:0;font:17px/1.7 var(--fb,system-ui),system-ui,-apple-system,'Segoe UI',sans-serif;color:#1c2430;background:#fff}"
    "img{max-width:100%;height:auto}"
    "a{color:var(--ac)}"
    ".bk-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}"
    # kabuk
    ".bk-top{background:var(--dk);color:#fff;position:sticky;top:0;z-index:40}"
    ".bk-top-duz{position:static}"
    ".bk-top-orta .bk-brand{margin:0 auto}"
    ".bk-top .bk-w{display:flex;align-items:center;gap:16px;min-height:66px}"
    ".bk-top a{color:#fff;text-decoration:none}"
    ".bk-brand{font-weight:800;font-size:19px;letter-spacing:-.2px;margin-right:auto}"
    ".bk-brand img{height:38px;width:auto;max-width:190px;object-fit:contain;display:block}"
    ".bk-nav{display:flex;gap:18px;font-weight:600;font-size:15px}"
    ".bk-tel{background:var(--ac);padding:10px 17px;border-radius:999px;font-weight:700;font-size:15px;white-space:nowrap}"
    ".bk-mb{display:none;background:none;border:0;color:#fff;padding:8px;cursor:pointer}"
    ".bk-mb svg{display:block}"
    "@media(max-width:820px){.bk-nav{display:none}.bk-mb{display:block;order:3}"
    ".bk-top.op .bk-nav{display:flex;position:absolute;left:0;right:0;top:100%;background:var(--dk);flex-direction:column;padding:12px 22px 18px;gap:2px}"
    ".bk-top.op .bk-nav a{padding:11px 0;border-bottom:1px solid rgba(255,255,255,.12)}}"
    # bölüm
    ".bk{padding:var(--bk-pad,56px) 0;background:var(--bk-bg,transparent);color:var(--bk-fg,inherit)}"
    ".bk-w{max-width:1120px;margin:0 auto;padding:0 22px}"
    ".bk h1,.bk h2,.bk h3{font-family:var(--bk-fh,var(--fh,inherit));line-height:1.18;margin:0 0 12px;color:inherit}"
    ".bk p{font-family:var(--bk-fb,var(--fb,inherit));margin:0 0 14px}"
    ".bk-h{margin:0 0 26px;max-width:62ch}.bk-h.bk-c{margin-left:auto;margin-right:auto;text-align:center}"
    ".bk-h h2{font-size:clamp(24px,3.4vw,34px)}.bk-h p{opacity:.82;margin:0}"
    ".bk-c{text-align:center}"
    ".bk-btn{display:inline-block;margin-top:6px;background:var(--ac);color:#fff;text-decoration:none;font-weight:700;padding:13px 24px;border-radius:var(--bk-r,12px);min-height:46px;line-height:20px}"
    ".bk-btn:hover{filter:brightness(1.07)}.bk-btn.bk-sm{padding:8px 16px;min-height:38px;font-size:14px;margin:0}"
    # yerleşimler
    ".bk-hero{padding:18px 0}.bk-hero h1{font-size:clamp(30px,5.4vw,52px);margin:0 0 14px}"
    ".bk-hero p{font-size:clamp(16px,2vw,20px);max-width:60ch;opacity:.9}"
    ".bk-hero.bk-a-c{text-align:center}.bk-hero.bk-a-c p{margin-left:auto;margin-right:auto}"
    ".bk-hero.bk-a-r{text-align:right}.bk-hero.bk-a-r p{margin-left:auto}"
    ".bk.bkw-hero.bk-ov{background-size:cover;background-position:center;color:#fff;padding:clamp(56px,9vw,120px) 0}"
    ".bk-split{display:grid;grid-template-columns:1fr 1fr;gap:34px;align-items:center}"
    ".bk-split img{border-radius:var(--bk-r,12px);width:100%;object-fit:cover}"
    ".bk-split h2{font-size:clamp(23px,3.2vw,32px)}"
    "@media(max-width:780px){.bk-split{grid-template-columns:1fr;gap:22px}}"
    ".bk-g{display:grid;grid-template-columns:repeat(var(--c,3),1fr);gap:18px}"
    "@media(max-width:860px){.bk-g{grid-template-columns:repeat(2,1fr)}}"
    "@media(max-width:560px){.bk-g{grid-template-columns:repeat(var(--cm,2),1fr)}"
    ".bk-g[style*='--cm:auto']{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch}"
    ".bk-g[style*='--cm:auto']>*{flex:0 0 78%;scroll-snap-align:start}}"
    ".bk-card{display:block;background:#fff;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);overflow:hidden;text-decoration:none;color:inherit}"
    "a.bk-card:hover{border-color:var(--ac);box-shadow:0 4px 16px rgba(10,20,34,.09)}"
    ".bk-card img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block}"
    ".bk-cb{padding:14px 15px}.bk-cb h3{font-size:17px;margin:0 0 5px}.bk-cb p{font-size:15px;opacity:.8;margin:0}"
    ".bk-lg{display:grid;place-items:center;padding:12px;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);background:#fff}"
    ".bk-lg img{max-height:54px;object-fit:contain}"
    ".bk-2{display:grid;grid-template-columns:1fr 1fr;gap:30px}@media(max-width:780px){.bk-2{grid-template-columns:1fr;gap:16px}}"
    ".bk-rows{list-style:none;margin:0;padding:0;display:grid;gap:1px;background:#e7e4dc;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);overflow:hidden}"
    ".bk-rows li{background:#fff;padding:13px 16px;display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}"
    ".bk-rows b{font-weight:650}.bk-rows span{margin-left:auto;opacity:.75;font-size:15px}"
    ".bk-st{text-align:center}.bk-st b{display:block;font-size:clamp(28px,4.6vw,44px);font-weight:800;color:var(--ac);line-height:1.1;font-family:var(--bk-fh,inherit)}"
    ".bk-st span{font-size:15px;opacity:.78}"
    ".bk-q{margin:0;background:#fff;border:1px solid #e7e4dc;border-left:3px solid var(--ac);border-radius:var(--bk-r,12px);padding:18px 20px}"
    ".bk-q blockquote{margin:0 0 10px;font-size:16px;line-height:1.65}"
    ".bk-q figcaption{font-size:14px;opacity:.72;font-weight:600}"
    ".bk-faq{border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);overflow:hidden}"
    ".bk-faq details{border-bottom:1px solid #e7e4dc}.bk-faq details:last-child{border-bottom:0}"
    ".bk-faq summary{cursor:pointer;padding:15px 18px;font-weight:650;list-style:none}"
    ".bk-faq summary::-webkit-details-marker{display:none}"
    ".bk-faq summary:after{content:'+';float:right;font-weight:700;opacity:.5}"
    ".bk-faq details[open] summary:after{content:'–'}"
    ".bk-faq details>div{padding:0 18px 16px;opacity:.85}"
    ".bk-logos{display:flex;flex-wrap:wrap;gap:26px;align-items:center;justify-content:center}"
    ".bk-logos img{height:40px;width:auto;object-fit:contain;opacity:.78}"
    ".bk-band{display:flex;align-items:center;justify-content:center;gap:16px;flex-wrap:wrap;text-align:center;font-weight:600}"
    ".bk-slide{list-style:none;margin:0;padding:0;display:flex;gap:12px;overflow-x:auto;scroll-snap-type:x mandatory}"
    ".bk-slide li{flex:0 0 100%;scroll-snap-align:center}"
    ".bk-slide img{width:100%;aspect-ratio:16/7;object-fit:cover;border-radius:var(--bk-r,12px)}"
    ".bk-vid,.bk-map{position:relative;padding-top:56.25%;border-radius:var(--bk-r,12px);overflow:hidden;background:#eceae4}"
    ".bk-map{padding-top:42%}"
    ".bk-vid iframe,.bk-map iframe{position:absolute;inset:0;width:100%;height:100%;border:0}"
    ".bk-form{display:flex;gap:8px;max-width:520px;margin:0 auto;flex-wrap:wrap}"
    ".bk-form input{flex:1;min-width:190px;min-height:48px;border:1px solid #d7d3c8;border-radius:var(--bk-r,12px);padding:0 14px;font:16px inherit}"
    ".bk-form button{min-height:48px;padding:0 22px;border:0;border-radius:var(--bk-r,12px);background:var(--ac);color:#fff;font:700 16px inherit;cursor:pointer}"
    ".bk-ba{display:grid;grid-template-columns:1fr 1fr;gap:14px}"
    ".bk-ba figure{margin:0}.bk-ba img{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:var(--bk-r,12px)}"
    ".bk-ba figcaption{text-align:center;font-size:14px;font-weight:650;opacity:.75;margin-top:6px}"
    # alt bilgi
    ".bk-foot{background:var(--dk);color:#cdd6e4;padding:34px 0;font-size:15px}"
    ".bk-foot a{color:#fff}.bk-foot .bk-w{display:flex;gap:16px;flex-wrap:wrap;align-items:center}"
    ".bk-cr{margin-left:auto;font-size:13.5px;opacity:.85}"
    "@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important;scroll-behavior:auto!important}}"
)

NAVJS = ("<script>(function(){var b=document.getElementById('bkmb');if(!b)return;"
         "b.addEventListener('click',function(){var t=b.closest('.bk-top'),a=t.classList.toggle('op');"
         "b.setAttribute('aria-expanded',a?'true':'false')})})();</script>")


def page_html(page, rows, ctx, data=None, dev=""):
    """Bölümlerden tam sayfa üretir."""
    data = data or {}
    kb = kabuk_ayar(rows, dev, data)
    brand = ctx.get("brand") or {}
    dk = brand.get("dark") or "#0a1f44"
    ac = brand.get("accent") or "#f27a1a"
    ad = ctx.get("name") or ""
    tel = ctx.get("tel") or ""
    telh = re.sub(r"[^\d+]", "", tel)
    logo = kb.get("logo") or ctx.get("logo") or ""
    govde = "".join(block_html(b, dev, data.get(b["iid"]) or data.get(b.get("bid")) or {}) for b in rows)
    try:                                   # bölümlerde seçilen yazı tipleri gerçekten yüklensin
        import sitegen as _sg
        govde = _sg.font_link([str(v(b, k, dev) or "") for b in rows for k in ("font_h", "font_b")]) + govde
    except Exception:                                              # noqa: BLE001
        pass
    menu = "".join('<a href="%s">%s</a>' % (E(link(p.get("slug_url") or ("/" if p.get("home") else "/" + str(p.get("slug") or ""))) or "/"), E(str(p.get("title") or "")))
                   for p in (ctx.get("menu_pages") or [])[:7])
    bas = "%s · %s" % (page.get("title") or "", ad) if page.get("title") and not page.get("home") else ad
    aciklama = str(page.get("desc") or ctx.get("desc") or "")[:300]
    return (
        '<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>%(t)s</title>%(d)s"
        "<style>:root{--dk:%(dk)s;--ac:%(ac)s}%(css)s%(ekcss)s</style></head><body>"
        '<header class="bk-top%(topc)s"><div class="bk-w">'
        '<a class="bk-brand" href="/">%(logo)s</a>'
        '<nav class="bk-nav" aria-label="Ana menü">%(menu)s</nav>'
        '<button class="bk-mb" id="bkmb" type="button" aria-label="Menü" aria-expanded="false">'
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
        '<path d="M4 7h16M4 12h16M4 17h16"/></svg></button>'
        "%(tel)s</div></header><main>%(body)s</main>%(foot)s%(js)s</body></html>"
    ) % {
        "t": E(bas), "dk": E(dk), "ac": E(ac), "css": CSS, "ekcss": "".join(EK_CSS), "menu": menu,
        "d": ('<meta name="description" content="%s">' % E(aciklama)) if aciklama else "",
        "topc": ("" if kb.get("menu_yapis", True) else " bk-top-duz") + (" bk-top-orta" if kb.get("logo_orta") else ""),
        "foot": "" if kb.get("footer_var") else (
            '<footer class="bk-foot"><div class="bk-w"><span>&copy; %s %s</span>%s'
            '<span class="bk-cr"><a href="https://onlinekaydet.com" rel="noopener">OnlineKaydet ile yayınlanır</a></span>'
            "</div></footer>") % (E(str(ctx.get("yil") or "")), E(ad),
                                  ('<span><a href="tel:%s">%s</a></span>' % (E(telh), E(tel_goster(tel)))) if tel else ""),
        "logo": ('<img src="%s" alt="%s"%s>' % (E(img_url(logo)), E(ad),
                                                (' style="height:%dpx"' % int(kb["logo_boy"])) if kb.get("logo_boy") else "")) if logo else E(ad),
        "tel": ('<a class="bk-tel" href="tel:%s">%s</a>' % (E(telh), E(tel_goster(tel)))) if tel else "",
        "ad": E(ad), "body": govde, "js": NAVJS,
    }


def tema_css():
    """Tema içine eklenen bölümler için CSS: sayfa kabuğu (body, üst menü, alt bilgi) kuralları olmadan."""
    i = CSS.index(".bk{padding")
    j = CSS.index(".bk-foot{")
    k = CSS.index("@media(prefers-reduced-motion")
    return ".okek{display:block}.okek img{max-width:100%;height:auto}.okek .bk-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}" \
        + CSS[i:j] + CSS[k:] + "".join(EK_CSS)


def tema_bolum(b, dev="", data=None, dk="#0a1f44", ac="#f27a1a"):
    """Tek bölümü tema içine girecek biçimde sarar; boşsa ''."""
    h = block_html(b, dev, data)
    if not h:
        return ""
    return '<div class="okek" style="--dk:%s;--ac:%s">%s</div>' % (E(dk), E(ac), h)
