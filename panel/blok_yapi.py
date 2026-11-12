# -*- coding: utf-8 -*-
"""Yapı, sektörel ve serbest bölümler — her bölümün kendi üreticisi.

Yapı bölümlerinin bir kısmı sayfa akışına girmez, sayfanın kabuğunu ayarlar
(menü görünümü, logo, alt bilgi). Bunlar KABUK defterine yazar; sayfa kabuğu
oradan okur. Böylece bölümü eklemek gerçekten bir şeyi değiştirir.

Serbest "HTML / kod" bölümü işletmenin kendi kodunu alır; betik ve olay
öznitelikleri temizlenir: panel hesabı ele geçse bile ziyaretçinin tarayıcısında
kod çalıştırılamasın.
"""
import html as _h
import re

from blokgen import E, v, lines, img_url, link, para, sec, _head, _cta, _cols, _grid, _n, _style, _card

KAYIT = {}
KABUK = {}


def kayit(bid):
    def sar(fn):
        KAYIT[bid] = fn
        return fn
    return sar


def kabuk(bid):
    def sar(fn):
        KABUK[bid] = fn
        return fn
    return sar


def _yok(b, dev):
    return sec(b, _head(b, dev, True), dev) if v(b, "title", dev, "") else ""


# ---------------------------------------------------------------- güvenli HTML
_IZIN = {"p", "br", "hr", "b", "strong", "i", "em", "u", "s", "small", "span", "div", "a", "ul", "ol", "li",
         "h2", "h3", "h4", "h5", "blockquote", "table", "thead", "tbody", "tr", "th", "td", "caption",
         "img", "figure", "figcaption", "iframe", "video", "source", "code", "pre"}
_OZ = {"href", "src", "alt", "title", "width", "height", "colspan", "rowspan", "target", "rel",
       "loading", "allowfullscreen", "controls", "poster", "type", "class"}
_IFRAME_OK = re.compile(r"^https://(www\.)?(youtube-nocookie\.com|youtube\.com|player\.vimeo\.com|google\.com/maps)/", re.I)


def guvenli_html(h):
    """İşletmenin yazdığı HTML'den betik ve olayları ayıklar."""
    h = str(h or "")
    h = re.sub(r"<\s*(script|style|object|embed|form|input|button|link|meta|base)\b.*?(</\s*\1\s*>|$)", "", h, flags=re.S | re.I)
    h = re.sub(r"<!--.*?-->", "", h, flags=re.S)

    def etiket(m):
        kapat, ad, geri = m.group(1), m.group(2).lower(), m.group(3)
        if ad not in _IZIN:
            return ""
        if kapat:
            return "</%s>" % ad
        oz = []
        for am in re.finditer(r'([A-Za-z_:][-\w:.]*)\s*=\s*("([^"]*)"|\'([^\']*)\'|([^\s"\'>]+))', geri or ""):
            k = am.group(1).lower()
            d = am.group(3) or am.group(4) or am.group(5) or ""
            if k.startswith("on") or k not in _OZ:
                continue
            if k in ("href", "src", "poster"):
                if re.match(r"\s*(javascript|data|vbscript)\s*:", d, re.I):
                    if ad in ("iframe", "img", "video", "source"):
                        return ""                  # kaynağı güvensizse etiket tamamen düşer
                    continue
                if ad == "iframe" and k == "src" and not _IFRAME_OK.match(d.strip()):
                    return ""
            oz.append('%s="%s"' % (k, _h.escape(d, quote=True)))
        if ad == "a" and any(x.startswith("target=") for x in oz) and not any(x.startswith("rel=") for x in oz):
            oz.append('rel="noopener"')
        if ad == "iframe":
            if not any(x.startswith("src=") for x in oz):
                return ""                          # kaynaksız gömme basılmaz
            if not any(x.startswith("title=") for x in oz):
                oz.append('title="Gömülü içerik"')
        return "<%s%s>" % (ad, (" " + " ".join(oz)) if oz else "")
    return re.sub(r"<\s*(/?)\s*([A-Za-z][\w:-]*)((?:[^<>\"']|\"[^\"]*\"|'[^']*')*)>", etiket, h)


# ---------------------------------------------------------------- yapı
@kayit("mobil_bar")
def mobil_bar(b, dev, d):
    """Mobil bar: telefonda altta sabit kısayollar. Bilgisayarda görünmez."""
    it = lines(v(b, "items", dev, ""), 2)
    if not it:
        it = [("Randevu", "/randevu"), ("Ara", "tel:" + str((d.get("iletisim") or {}).get("tel") or "")),
              ("Yol", "/iletisim")]
    n = _n(v(b, "count", dev, 4), 4)
    st = str(v(b, "style", dev, "düz"))
    ks = ""
    for x in it[:max(3, min(n, 5))]:
        to = link(x[1]) if len(x) > 1 else ""
        if not to:
            continue
        ks += '<a href="%s"><span>%s</span></a>' % (E(to), E(x[0]))
    if not ks:
        return ""
    return ('<nav class="bky-mb bky-mb-%s%s" aria-label="Hızlı erişim">%s</nav>%s') % (
        E(st), " bky-mb-giz" if v(b, "hide_scroll", dev, True) else "", ks,
        MB_JS if v(b, "hide_scroll", dev, True) else "")


@kayit("mobil_menu")
def mobil_menu(b, dev, d):
    """Mobil menü: telefonda açılan çekmece; kategoriler görselli olabilir."""
    kay = str(v(b, "source", dev, "ürün kategorileri"))
    if kay == "elle":
        it = [(x[0], link(x[1]) if len(x) > 1 else "", "") for x in lines(v(b, "items", dev, ""), 2)]
    else:
        it = [(k.get("ad") or "", "/magaza?kat=" + _h.escape(str(k.get("ad") or ""), quote=True).replace(" ", "+"), k.get("img") or "")
              for k in (d.get("kategoriler") or [])]
    if not it:
        return ""
    gor = v(b, "img", dev, True)
    bic = str(v(b, "look", dev, "liste"))
    sek = str(v(b, "shape", dev, "kare"))
    sut = _n(v(b, "cols_m", dev, 2), 2)
    ks = ""
    for ad, to, im in it[:40]:
        if not to:
            continue
        g = ('<img src="%s" alt="" loading="lazy">' % E(img_url(im))) if (gor and im) else ""
        ks += '<a href="%s">%s<span>%s</span></a>' % (E(to), g, E(ad))
    ara = ('<form class="bky-dr-ara" method="get" action="/magaza" role="search">'
           '<label class="bk-sr" for="dr-%s">Ara</label>'
           '<input id="dr-%s" name="q" type="search" placeholder="Ara"></form>') % (E(b["iid"]), E(b["iid"])) if v(b, "search", dev, True) else ""
    gir = '<a class="bky-dr-gir" href="/uye-girisi">Giriş / Hesabım</a>' if v(b, "login", dev, True) else ""
    return ('<div class="bky-dr bky-dr-%s%s" id="dr-%s" hidden role="dialog" aria-label="Menü">'
            '<div class="bky-dr-i" style="--c:%d">%s<div class="bky-dr-l bky-dr-%s">%s</div>%s'
            '<button class="bky-dr-x" type="button" aria-label="Menüyü kapat">×</button></div></div>%s') % (
        E(bic), " bky-dr-sag" if str(v(b, "side", dev, "sol")) == "sağ" else "", E(b["iid"]),
        max(1, min(sut, 3)), ara, E(sek), ks, gir, DR_JS)


@kayit("story")
def story(b, dev, d):
    """Story alanı: Instagram tarzı daireler, yatay kayar."""
    im = v(b, "items", dev, []) or []
    im = [x for x in im if x] if isinstance(im, list) else []
    if not im:
        im = [x.get("img") for x in (d.get("kategoriler") or []) if x.get("img")]
    if not im:
        return ""
    ks = "".join('<a class="bky-st%s" href="#"><img src="%s" alt="" loading="lazy"></a>' % (
        " bky-st-h" if v(b, "ring", dev, True) else "", E(img_url(k))) for k in im[:20])
    return sec(b, '<div class="bky-stl" role="region" aria-label="Öne çıkanlar" tabindex="0">%s</div>' % ks, dev)


@kayit("site_arama")
def site_arama(b, dev, d):
    """Site içi arama: kapsam, filtreler ve sıralama işletmenin yazdıklarından."""
    kap = str(v(b, "scope", dev, "hepsi"))
    yol = {"ürün": "/magaza", "hizmet": "/hizmetler", "yazı": "/blog"}.get(kap, "/ara")
    fl = ""
    for x in lines(v(b, "filters", dev, ""), 2)[:6]:
        sec_ = [y.strip() for y in str(x[1] or "").split(",") if y.strip()]
        if not sec_:
            continue
        fl += ('<label class="f2"><span>%s</span><select name="%s"><option value="">Hepsi</option>%s</select></label>') % (
            E(x[0]), E(re.sub(r"\W+", "_", x[0]).lower()[:20] or "f"),
            "".join('<option value="%s">%s</option>' % (E(y), E(y)) for y in sec_))
    sr = [y[0] for y in lines(v(b, "sort", dev, ""), 1)][:6]
    if sr:
        fl += ('<label class="f2"><span>Sıralama</span><select name="sira">%s</select></label>' %
               "".join('<option value="%s">%s</option>' % (E(y), E(y)) for y in sr))
    ph = v(b, "ph", dev, "") or "Ara"
    return sec(b, '<form class="bky-ara" method="get" action="%s" role="search">'
               '<label class="bk-sr" for="sa2-%s">%s</label>'
               '<input id="sa2-%s" name="q" type="search" placeholder="%s">%s'
               '<button class="bk-btn" type="submit">Ara</button></form>' % (
                   E(yol), E(b["iid"]), E(str(ph)), E(b["iid"]), E(str(ph)), fl), dev)


@kayit("sosyal")
def sosyal(b, dev, d):
    """Sosyal medya: hesaplar; ikon, kart ya da liste olarak."""
    it = [(x[0], link(x[1]) if len(x) > 1 else "") for x in lines(v(b, "items", dev, ""), 2)]
    if not it:
        it = [(k.capitalize(), link(str(u))) for k, u in (d.get("baglantilar") or {}).items()]
    it = [(a, u) for a, u in it if u]
    if not it:
        return ""
    st = str(v(b, "style", dev, "ikon"))
    ks = "".join('<a href="%s" target="_blank" rel="noopener"><span>%s</span></a>' % (E(u), E(a)) for a, u in it[:10])
    return sec(b, _head(b, dev, True) + '<div class="bky-sos bky-sos-%s">%s</div>' % (E(st), ks), dev)


@kayit("dil")
def dil(b, dev, d):
    """Dil seçici: seçilen dil adresin sonuna ?dil= olarak eklenir."""
    ds = [x.strip() for x in str(v(b, "langs", dev, "Türkçe, English") or "").replace("\n", ",").split(",") if x.strip()]
    if len(ds) < 2:
        return ""
    st = str(v(b, "style", dev, "kısaltma"))
    ks = ""
    for x in ds[:8]:
        kod = re.sub(r"\W", "", x)[:2].lower()
        et = x if st == "liste" else x[:2].upper()
        ks += '<a href="?dil=%s" hreflang="%s">%s</a>' % (E(kod), E(kod), E(et))
    return sec(b, '<nav class="bky-dil" aria-label="Dil seçimi">%s</nav>' % ks, dev)


@kayit("cerez")
def cerez_blok(b, dev, d):
    """Çerez bandı: site ayarlarındaki bantla aynı; sayfada bir kez çıkar."""
    try:
        import cerez as cz
    except Exception:                                              # noqa: BLE001
        return ""
    cfg = cz.temizle({"on": True, "text": v(b, "text", dev, "") or cz.VARSAYILAN["text"],
                      "accept": v(b, "accept", dev, "") or "Kabul et",
                      "reject": v(b, "reject", dev, ""),
                      "link": v(b, "link", dev, "") or "/cerez-politikasi",
                      "pos": v(b, "pos", dev, "alt")})
    return cz.band(cfg, (d.get("accent") or "#1155cc"))


@kayit("qr_menu")
def qr_menu(b, dev, d):
    """QR menü: masadaki kareyi okutan müşterinin gördüğü menü."""
    ur = d.get("menu") or d.get("hizmetler") or []
    it = lines(v(b, "items", dev, ""), 3)
    if str(v(b, "source", dev, "ürünler")) == "elle" or not ur:
        ur = [{"name": x[0], "price": re.sub(r"[^\d.,]", "", x[1] or "") or 0, "desc": x[2] if len(x) > 2 else ""} for x in it]
    if not ur:
        return _yok(b, dev)
    fi, fo = v(b, "price", dev, True), v(b, "photo", dev, True)
    ks = ""
    for x in ur[:120]:
        g = ('<img src="%s" alt="" loading="lazy">' % E(img_url((x.get("images") or [x.get("img")])[0]))) if (fo and (x.get("images") or x.get("img"))) else ""
        ks += '<li>%s<div><b>%s</b>%s</div>%s</li>' % (
            g, E(str(x.get("name") or "")),
            ("<p>%s</p>" % E(str(x.get("desc") or ""))) if x.get("desc") else "",
            ('<span class="bky-qf">%s ₺</span>' % para(x.get("price"))) if fi and x.get("price") else "")
    cag = '<a class="bk-btn bky-qc" href="#" data-cagir>Garson çağır</a>' if v(b, "call", dev, True) else ""
    yaz = '<button class="bk-btn bky-qy" type="button" onclick="print()">Yazdır</button>' if v(b, "print", dev, True) else ""
    not_ = v(b, "note", dev, "")
    return sec(b, _head(b, dev, True) + ('<p class="bky-qn">%s</p>' % E(str(not_)) if not_ else "")
               + '<ul class="bky-qr">%s</ul><div class="bk-c bky-qd">%s%s</div>' % (ks, cag, yaz), dev)


@kayit("footer")
def footer(b, dev, d):
    """Footer: çok sütunlu alt bilgi. Eklendiğinde sayfanın hazır alt bilgisi yerine geçer."""
    sut = {}
    for x in lines(v(b, "links", dev, ""), 3):
        sut.setdefault(x[0], []).append((x[1], link(x[2]) if len(x) > 2 else ""))
    ic = ""
    for bas, ln in list(sut.items())[:_n(v(b, "cols", dev, 3), 3)]:
        ic += '<div><h3>%s</h3><ul>%s</ul></div>' % (E(bas), "".join(
            '<li><a href="%s">%s</a></li>' % (E(u or "#"), E(a)) for a, u in ln[:10]))
    ek = ""
    if v(b, "bulten", dev, True):
        ek += ('<form class="bky-ft-b" method="post" action="/api/public/yp/bulten">'
               '<label class="bk-sr" for="fb-%s">E-posta</label>'
               '<input id="fb-%s" name="eposta" type="email" required placeholder="E-posta adresiniz">'
               '<button type="submit">Kaydol</button></form>') % (E(b["iid"]), E(b["iid"]))
    if v(b, "social", dev, True) and (d.get("baglantilar") or {}):
        ek += '<div class="bky-ft-s">%s</div>' % "".join(
            '<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(str(u)), E(k.capitalize()))
            for k, u in list((d.get("baglantilar") or {}).items())[:6] if link(str(u)))
    if not ic and not ek:
        return ""
    return ('<footer class="bk bky-ft" style="%s"><div class="bk-w"><div class="bky-ftg" style="--c:%d">%s%s</div>'
            '<div class="bky-ftc"><span>© %s %s</span>'
            '<a href="https://onlinekaydet.com" rel="noopener">OnlineKaydet ile yayınlanır</a></div></div></footer>') % (
        _style(b, dev), _n(v(b, "cols", dev, 3), 3), ic, ('<div class="bky-ft-e">%s</div>' % ek) if ek else "",
        E(str(d.get("yil") or "")), E(str(d.get("firma") or "")))


@kabuk("footer")
def _kb_footer(b, dev, d):
    return {"footer_var": True}


@kayit("menu_gorunum")
def menu_gorunum(b, dev, d):
    """Menü görünümü sayfanın kabuğunu ayarlar, akışta bir şey basmaz."""
    return ""


@kabuk("menu_gorunum")
def _kb_menu(b, dev, d):
    return {"menu_stil": str(v(b, "style", dev, "klasik")),
            "menu_yapis": bool(v(b, "sticky", dev, True)),
            "menu_kucul": bool(v(b, "shrink", dev, True)),
            "menu_ara": bool(v(b, "search", dev, False)),
            "menu_sepet": bool(v(b, "cart", dev, False))}


@kayit("logo_bolum")
def logo_bolum(b, dev, d):
    """Logo bölümü sayfanın kabuğunu ayarlar, akışta bir şey basmaz."""
    return ""


@kabuk("logo_bolum")
def _kb_logo(b, dev, d):
    return {"logo": v(b, "img", dev, "") or None,
            "logo_orta": str(v(b, "pos", dev, "sol")) == "orta",
            "logo_boy": _n(v(b, "size_m" if dev == "phone" else "size", dev, 40), 40),
            "logo_yalniz": bool(v(b, "only", dev, False))}


# ---------------------------------------------------------------- sektörel
@kayit("menu_karti")
def menu_karti(b, dev, d):
    """Menü / fiyat kartı: restoran ve kafe için kategorili liste."""
    hz = d.get("hizmetler") or []
    if not hz:
        return _yok(b, dev)
    gr = {}
    for x in hz:
        gr.setdefault(x.get("cat") or "Menü", []).append(x)
    ic = ""
    for k, vv in gr.items():
        ic += '<h3 class="bky-mk-b">%s</h3><ul class="bky-mk">%s</ul>' % (E(k), "".join(
            '<li><div><b>%s</b>%s</div>%s</li>' % (
                E(str(x.get("name") or "")), ("<p>%s</p>" % E(str(x.get("desc") or ""))) if x.get("desc") else "",
                ('<span>%s ₺</span>' % para(x["price"])) if x.get("price") else "") for x in vv))
    return sec(b, _head(b, dev, True) + ic, dev)


@kayit("rezervasyon")
def rezervasyon(b, dev, d):
    """Rezervasyon: kişi sayısı, tarih ve saat."""
    return sec(b, '<div class="bkd-fk">%s%s<form class="bkd-f" method="post" action="/api/public/yp/rezervasyon">'
               '<label class="f2"><span>Kişi<i aria-hidden="true"> *</i></span>'
               '<select name="kisi" required>%s</select></label>'
               '<label class="f2"><span>Tarih<i aria-hidden="true"> *</i></span><input name="tarih" type="date" required></label>'
               '<label class="f2"><span>Saat<i aria-hidden="true"> *</i></span><input name="saat" type="time" required></label>'
               '<label class="f2"><span>Adınız<i aria-hidden="true"> *</i></span><input name="ad" required maxlength="80"></label>'
               '<label class="f2"><span>Telefon<i aria-hidden="true"> *</i></span><input name="tel" type="tel" required maxlength="20"></label>'
               '<button class="bk-btn" type="submit">%s</button></form></div>' % (
                   "<h2>%s</h2>" % E(str(v(b, "title", dev, "") or "Rezervasyon")),
                   ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "",
                   "".join("<option>%d</option>" % i for i in range(1, 13)),
                   E(str(v(b, "cta", dev, "") or "Yer ayırt"))), dev)


@kayit("portfoy")
def portfoy(b, dev, d):
    """Portföy arama: emlak ilan filtresi."""
    tur = (d.get("portfoy_turleri") or ["Satılık", "Kiralık"])
    return sec(b, '<div class="bkd-fk">%s%s<form class="bkd-f" method="get" action="/portfoy" role="search">'
               '<label class="f2"><span>İşlem</span><select name="tur">%s</select></label>'
               '<label class="f2"><span>Oda</span><select name="oda"><option value="">Hepsi</option>'
               '<option>1+1</option><option>2+1</option><option>3+1</option><option>4+1</option></select></label>'
               '<label class="f2"><span>En fazla fiyat</span><input name="fiyat" type="number" min="0" step="1000"></label>'
               '<label class="f2"><span>Semt</span><input name="semt" maxlength="60"></label>'
               '<button class="bk-btn" type="submit">Ara</button></form></div>' % (
                   "<h2>%s</h2>" % E(str(v(b, "title", dev, "") or "Portföyde ara")),
                   ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "",
                   "".join("<option>%s</option>" % E(str(x)) for x in tur[:6])), dev)


@kayit("oda")
def oda(b, dev, d):
    """Oda ve müsaitlik: otel ve pansiyon; gecelik fiyat ve kapasite."""
    od = d.get("odalar") or []
    if not od:
        return _yok(b, dev)
    c, cm = _cols(b, dev, 3)
    ks = []
    for x in od[:_n(v(b, "count", dev, 6), 6)]:
        alt = []
        if x.get("kisi"):
            alt.append("%s kişilik" % E(str(x["kisi"])))
        if x.get("fiyat"):
            alt.append('<b>%s ₺</b> / gece' % para(x["fiyat"]))
        ks.append(_card((x.get("images") or [x.get("img")])[0] or "", x.get("ad") or "", x.get("desc") or "",
                        "/rezervasyon", ('<div class="bky-od">%s</div>' % " · ".join(alt)) if alt else ""))
    return sec(b, _head(b, dev, True) + _grid(ks, c, cm), dev)


@kayit("ders_program")
def ders_program(b, dev, d):
    """Ders programı: gün ve saate göre tablo."""
    pr = d.get("program") or []
    if not pr:
        return _yok(b, dev)
    sat = "".join('<tr><th scope="row">%s</th><td>%s</td><td>%s</td><td>%s</td></tr>' % (
        E(str(x.get("saat") or "")), E(str(x.get("gun") or "")), E(str(x.get("ders") or "")),
        E(str(x.get("egitmen") or ""))) for x in pr[:60])
    return sec(b, _head(b, dev) + '<div class="bke-tbl"><table><caption class="bk-sr">Ders programı</caption>'
               '<thead><tr><th scope="col">Saat</th><th scope="col">Gün</th><th scope="col">Ders</th>'
               '<th scope="col">Eğitmen</th></tr></thead><tbody>%s</tbody></table></div>' % sat, dev)


@kayit("marka_liste")
def marka_liste(b, dev, d):
    """Servis verdiğimiz markalar: oto ve teknik servis."""
    im = v(b, "imgs", dev, []) or []
    im = [x for x in im if x] if isinstance(im, list) else []
    ad = [x.get("ad") for x in (d.get("markalar") or [])]
    if not im and not ad:
        return _yok(b, dev)
    if im:
        ks = "".join('<img src="%s" alt="" loading="lazy">' % E(img_url(k)) for k in im[:40])
        ic = '<div class="bkh-lg">%s</div>' % ks
    else:
        ic = '<div class="bke-mkl">%s</div>' % "".join('<span class="bke-mk">%s</span>' % E(str(x)) for x in ad[:40])
    return sec(b, _head(b, dev, True) + ic, dev)


@kayit("calisma_alani")
def calisma_alani(b, dev, d):
    """Çalışma alanları: avukat ve danışmanlık; hizmetlerden kart dizisi."""
    hz = d.get("hizmetler") or []
    if not hz:
        return _yok(b, dev)
    c, cm = _cols(b, dev, 3)
    ks = [_card("", x.get("name") or "", x.get("desc") or "", "/iletisim") for x in hz[:_n(v(b, "count", dev, 6), 6)]]
    return sec(b, _head(b, dev, True) + _grid(ks, c, cm), dev)


@kayit("bilet")
def bilet(b, dev, d):
    """Bilet / kontenjan: etkinlik seçimi ve kişi sayısı; kalan yer yazar."""
    et = d.get("etkinlikler") or []
    sec_ = ""
    if et:
        sec_ = ('<label class="f2"><span>Etkinlik<i aria-hidden="true"> *</i></span><select name="etkinlik" required>%s</select></label>'
                % "".join('<option value="%s">%s%s</option>' % (
                    E(str(x.get("ad") or "")), E(str(x.get("ad") or "")),
                    (" · %s kişilik yer kaldı" % x["kalan"]) if x.get("kalan") is not None else "") for x in et[:40]))
    return sec(b, '<div class="bkd-fk">%s%s<form class="bkd-f" method="post" action="/api/public/yp/bilet">%s'
               '<label class="f2"><span>Kişi<i aria-hidden="true"> *</i></span>'
               '<input name="adet" type="number" min="1" max="20" value="1" required></label>'
               '<label class="f2"><span>Adınız<i aria-hidden="true"> *</i></span><input name="ad" required maxlength="80"></label>'
               '<label class="f2"><span>Telefon<i aria-hidden="true"> *</i></span><input name="tel" type="tel" required maxlength="20"></label>'
               '<button class="bk-btn" type="submit">%s</button></form></div>' % (
                   "<h2>%s</h2>" % E(str(v(b, "title", dev, "") or "Bilet al")),
                   ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "",
                   sec_, E(str(v(b, "cta", dev, "") or "Yerimi ayır"))), dev)


# ---------------------------------------------------------------- serbest
@kayit("s_baslik")
def s_baslik(b, dev, d):
    t = v(b, "text", dev, "")
    if not t:
        return ""
    boy = max(16, min(_n(v(b, "size", dev, 40), 40), 90))
    return sec(b, '<h2 class="bky-sb" style="font-size:%dpx">%s</h2>' % (boy, E(str(t))), dev)


@kayit("s_yazi")
def s_yazi(b, dev, d):
    t = v(b, "text", dev, "")
    if not t:
        return ""
    return sec(b, '<div class="bky-sy">%s</div>' % "".join("<p>%s</p>" % E(x[0]) for x in lines(t)), dev)


@kayit("s_resim")
def s_resim(b, dev, d):
    im = v(b, "img", dev, "")
    if not im:
        return ""
    cap = v(b, "cap", dev, "")
    return sec(b, '<figure class="bky-sr"><img src="%s" alt="%s" loading="lazy">%s</figure>' % (
        E(img_url(im)), E(str(cap or "")), ("<figcaption>%s</figcaption>" % E(str(cap))) if cap else ""), dev)


@kayit("s_resim_yazi")
def s_resim_yazi(b, dev, d):
    im, t = v(b, "img", dev, ""), v(b, "text", dev, "")
    if not (im or t):
        return ""
    return sec(b, '<div class="bkh-rz">%s<div>%s</div></div>' % (
        ('<img src="%s" alt="" loading="lazy">' % E(img_url(im))) if im else "",
        "".join("<p>%s</p>" % E(x[0]) for x in lines(t))), dev)


@kayit("s_2kolon")
def s_2kolon(b, dev, d):
    sol, sag = v(b, "left", dev, ""), v(b, "right", dev, "")
    if not (sol or sag):
        return ""
    def kol(x):
        return "<div>%s</div>" % "".join("<p>%s</p>" % E(y[0]) for y in lines(x))
    return sec(b, '<div class="bky-2k">%s%s</div>' % (kol(sol), kol(sag)), dev)


@kayit("s_3kolon")
def s_3kolon(b, dev, d):
    it = lines(v(b, "items", dev, ""), 2)
    if not it:
        return ""
    ks = ['<div class="bky-3k"><b>%s</b>%s</div>' % (E(x[0]), ("<p>%s</p>" % E(x[1])) if x[1] else "") for x in it[:6]]
    return sec(b, _grid(ks, min(len(ks), 3), "1"), dev)


@kayit("s_buton")
def s_buton(b, dev, d):
    t, to = v(b, "text", dev, ""), link(v(b, "to", dev, ""))
    if not t:
        return ""
    return sec(b, '<div class="bk-c"><a class="bk-btn" href="%s">%s</a></div>' % (E(to or "#"), E(str(t))), dev)


@kayit("s_ayirici")
def s_ayirici(b, dev, d):
    st = str(v(b, "style", dev, "çizgi"))
    if st == "boşluk":
        return '<div class="bky-ay-b" aria-hidden="true"></div>'
    return sec(b, '<hr class="bky-ay bky-ay-%s">' % ("nokta" if st == "nokta" else "cizgi"), dev)


@kayit("s_bosluk")
def s_bosluk(b, dev, d):
    h = max(0, min(_n(v(b, "h", dev, 48), 48), 240))
    return '<div style="height:%dpx" aria-hidden="true"></div>' % h


@kayit("s_video")
def s_video(b, dev, d):
    u = str(v(b, "video", dev, "") or "")
    m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([A-Za-z0-9_-]{6,20})", u)
    if m:
        return sec(b, '<div class="bk-vid"><iframe src="https://www.youtube-nocookie.com/embed/%s" '
                   'title="Video" loading="lazy" allowfullscreen></iframe></div>' % E(m.group(1)), dev)
    m = re.search(r"vimeo\.com/(\d+)", u)
    if m:
        return sec(b, '<div class="bk-vid"><iframe src="https://player.vimeo.com/video/%s" title="Video" '
                   'loading="lazy" allowfullscreen></iframe></div>' % E(m.group(1)), dev)
    return ""


@kayit("s_harita")
def s_harita(b, dev, d):
    ad = str(v(b, "adr", dev, "") or d.get("adres") or "")
    if not ad:
        return ""
    q = _h.escape(re.sub(r"\s+", "+", ad), quote=True)
    return sec(b, '<div class="bkd-hr"><iframe src="https://www.google.com/maps?q=%s&output=embed" '
               'title="Harita: %s" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>' % (q, E(ad)), dev)


@kayit("s_kod")
def s_kod(b, dev, d):
    """HTML / kod: işletmenin kendi kodu; betik ve olay öznitelikleri temizlenir."""
    h = guvenli_html(v(b, "html", dev, ""))
    if not h.strip():
        return ""
    return sec(b, '<div class="bky-kod">%s</div>' % h, dev)


# ---------------------------------------------------------------- betikler
MB_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
         "var y=0;addEventListener('scroll',function(){var n=scrollY;e.classList.toggle('giz',n>y&&n>160);y=n},{passive:true})})();</script>")

DR_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
         "function kapat(){e.hidden=true;document.removeEventListener('keydown',esc)}"
         "function esc(ev){if(ev.key==='Escape')kapat()}"
         "function ac(){e.hidden=false;document.addEventListener('keydown',esc);"
         "var b=e.querySelector('.bky-dr-x');if(b)b.focus()}"
         "document.addEventListener('click',function(ev){"
         "if(ev.target.closest('#bkmb')){ev.preventDefault();ac();return}"
         "if(ev.target===e||ev.target.classList.contains('bky-dr-x'))kapat()})})();</script>")

CSS = (
    ".bky-mb{position:fixed;left:0;right:0;bottom:0;z-index:2147481200;display:none;background:#fff;"
    "border-top:1px solid #e7e4dc;box-shadow:0 -2px 12px rgba(10,20,34,.08);transition:transform .25s}"
    ".bky-mb.giz{transform:translateY(100%)}"
    ".bky-mb a{flex:1;text-align:center;padding:10px 4px 12px;font-size:12px;color:#475467;text-decoration:none;min-height:52px;"
    "display:flex;align-items:center;justify-content:center}"
    ".bky-mb-yüzen{left:12px;right:12px;bottom:12px;border-radius:16px;border:1px solid #e7e4dc}"
    ".bky-mb-kavisli{border-radius:18px 18px 0 0}"
    "@media(max-width:820px){.bky-mb{display:flex}body{padding-bottom:64px}}"
    ".bky-dr{position:fixed;inset:0;background:rgba(8,14,24,.5);z-index:2147481800}"
    ".bky-dr[hidden]{display:none}"
    ".bky-dr-i{position:absolute;top:0;bottom:0;left:0;width:min(86vw,370px);background:#fff;padding:18px 16px;overflow:auto}"
    ".bky-dr-sag .bky-dr-i{left:auto;right:0}"
    ".bky-dr-x{position:absolute;top:10px;right:12px;border:0;background:none;font-size:25px;cursor:pointer;line-height:1;color:#667085}"
    ".bky-dr-ara input{width:100%;min-height:44px;border:1px solid #d7d3c8;border-radius:10px;padding:0 12px;font:16px inherit;margin-bottom:14px}"
    ".bky-dr-l{display:grid;gap:9px}"
    ".bky-dr-ızgara .bky-dr-l{grid-template-columns:repeat(var(--c,2),1fr)}"
    ".bky-dr-l a{display:flex;gap:11px;align-items:center;text-decoration:none;color:inherit;font-weight:600;font-size:15px}"
    ".bky-dr-ızgara .bky-dr-l a,.bky-dr-kart .bky-dr-l a{flex-direction:column;gap:6px;text-align:center;font-size:13.5px}"
    ".bky-dr-l img{width:46px;height:46px;object-fit:cover;border-radius:10px;flex:none}"
    ".bky-dr-ızgara .bky-dr-l img,.bky-dr-kart .bky-dr-l img{width:100%;height:auto;aspect-ratio:1/1}"
    ".bky-dr-yuvarlak img{border-radius:50%}.bky-dr-dikey img{aspect-ratio:3/4!important;border-radius:10px}"
    ".bky-dr-gir{display:block;margin-top:16px;padding-top:14px;border-top:1px solid #eee;font-weight:700;color:var(--ac);text-decoration:none}"
    ".bky-stl{display:flex;gap:13px;overflow-x:auto;padding:2px}"
    ".bky-st{flex:none;width:72px;height:72px;border-radius:50%;overflow:hidden;display:block;line-height:0}"
    ".bky-st-h{padding:2.5px;background:linear-gradient(45deg,var(--ac),var(--dk))}"
    ".bky-st img{width:100%;height:100%;object-fit:cover;border-radius:50%;border:2px solid #fff}"
    ".bky-ara{display:grid;grid-template-columns:1fr auto;gap:11px;max-width:860px;margin:0 auto}"
    ".bky-ara input[type=search]{min-height:48px;border:1px solid #d7d3c8;border-radius:10px;padding:0 14px;font:16px inherit}"
    ".bky-ara .f2{grid-column:span 1}"
    "@media(max-width:620px){.bky-ara{grid-template-columns:1fr}}"
    ".bky-sos{display:flex;gap:10px;flex-wrap:wrap;justify-content:center}"
    ".bky-sos a{border:1px solid #e7e4dc;border-radius:999px;padding:8px 16px;text-decoration:none;color:inherit;font-weight:600;font-size:14.5px;background:#fff}"
    ".bky-sos-kart a{border-radius:12px;padding:14px 20px}"
    ".bky-dil{display:flex;gap:7px;justify-content:center}"
    ".bky-dil a{border:1px solid #e7e4dc;border-radius:8px;padding:5px 11px;text-decoration:none;color:inherit;font-size:13.5px;font-weight:700;background:#fff}"
    ".bky-qn{text-align:center;opacity:.78;margin:-10px 0 18px}"
    ".bky-qr{list-style:none;margin:0;padding:0;display:grid;gap:1px;background:#e7e4dc;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);overflow:hidden}"
    ".bky-qr li{background:#fff;padding:12px 15px;display:flex;gap:13px;align-items:center}"
    ".bky-qr img{width:58px;height:58px;object-fit:cover;border-radius:9px;flex:none}"
    ".bky-qr b{font-size:16px}.bky-qr p{margin:2px 0 0;font-size:14px;opacity:.75}"
    ".bky-qf{margin-left:auto;font-weight:800;white-space:nowrap}"
    ".bky-qd{margin-top:18px;display:flex;gap:10px;justify-content:center}"
    "@media print{.bky-qd,.bk-top,.bky-mb{display:none!important}}"
    ".bky-ft{background:var(--bk-bg,var(--dk));color:var(--bk-fg,#cdd6e4);padding:40px 0 26px}"
    ".bky-ft a{color:#fff;text-decoration:none}.bky-ft a:hover{text-decoration:underline}"
    ".bky-ftg{display:grid;grid-template-columns:repeat(var(--c,3),1fr);gap:26px}"
    ".bky-ft h3{margin:0 0 10px;font-size:15px;color:#fff}"
    ".bky-ft ul{list-style:none;margin:0;padding:0;display:grid;gap:7px;font-size:14.5px}"
    ".bky-ft-b{display:flex;gap:8px;margin-bottom:12px}"
    ".bky-ft-b input{flex:1;min-height:42px;border:0;border-radius:9px;padding:0 12px;font:15px inherit}"
    ".bky-ft-b button{min-height:42px;padding:0 16px;border:0;border-radius:9px;background:var(--ac);color:#fff;font:700 14px inherit;cursor:pointer}"
    ".bky-ft-s{display:flex;gap:12px;flex-wrap:wrap;font-size:14px}"
    ".bky-ftc{display:flex;gap:14px;flex-wrap:wrap;margin-top:26px;padding-top:16px;border-top:1px solid rgba(255,255,255,.14);font-size:13.5px}"
    ".bky-ftc a{margin-left:auto}"
    "@media(max-width:780px){.bky-ftg{grid-template-columns:1fr 1fr}}"
    "@media(max-width:520px){.bky-ftg{grid-template-columns:1fr}}"
    ".bky-mk-b{margin:22px 0 8px;font-size:17px;color:var(--ac)}"
    ".bky-mk{list-style:none;margin:0;padding:0;display:grid;gap:1px;background:#e7e4dc;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);overflow:hidden}"
    ".bky-mk li{background:#fff;padding:12px 16px;display:flex;gap:14px;align-items:baseline}"
    ".bky-mk b{font-size:16px}.bky-mk p{margin:2px 0 0;font-size:14px;opacity:.75}"
    ".bky-mk span{margin-left:auto;font-weight:800;white-space:nowrap}"
    ".bky-od{font-size:14px;margin-top:6px}"
    ".bky-sb{margin:0;line-height:1.2;font-family:var(--bk-fh,inherit)}"
    ".bky-sy p:last-child{margin-bottom:0}"
    ".bky-sr{margin:0}.bky-sr img{width:100%;border-radius:var(--bk-r,12px);display:block}"
    ".bky-sr figcaption{margin-top:9px;font-size:14px;opacity:.72;text-align:center}"
    ".bky-2k{display:grid;grid-template-columns:1fr 1fr;gap:30px}"
    "@media(max-width:780px){.bky-2k{grid-template-columns:1fr;gap:14px}}"
    ".bky-3k{background:#fff;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);padding:17px 19px}"
    ".bky-3k b{display:block;font-size:16.5px;margin-bottom:5px}.bky-3k p{margin:0;opacity:.78;font-size:15px}"
    ".bky-ay{border:0;border-top:1px solid #e3e0d7;margin:0}"
    ".bky-ay-nokta{border-top-style:dotted;border-top-width:2px}"
    ".bky-ay-b{height:28px}"
    ".bky-kod{max-width:100%;overflow-x:auto}"
    ".bky-kod img,.bky-kod iframe{max-width:100%}"
)
