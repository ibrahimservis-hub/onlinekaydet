# -*- coding: utf-8 -*-
"""Tanıtım, hizmet ve ekip bölümleri — her bölümün kendi üreticisi."""
import html as _h
import re

from blokgen import E, v, lines, img_url, link, para, sec, _head, _cta, _cols, _grid, _n, _card, _style

KAYIT = {}


def kayit(bid):
    def sar(fn):
        KAYIT[bid] = fn
        return fn
    return sar


def _yok(b, dev):
    return sec(b, _head(b, dev, True), dev) if v(b, "title", dev, "") else ""


def _video_goml(u, baslik, sessiz=True):
    u = str(u or "").strip()
    m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([A-Za-z0-9_-]{6,20})", u)
    if m:
        return ('<div class="bk-vid"><iframe src="https://www.youtube-nocookie.com/embed/%s?rel=0" '
                'title="%s" loading="lazy" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div>') % (E(m.group(1)), E(baslik))
    m = re.search(r"vimeo\.com/(\d+)", u)
    if m:
        return '<div class="bk-vid"><iframe src="https://player.vimeo.com/video/%s" title="%s" loading="lazy" allowfullscreen></iframe></div>' % (E(m.group(1)), E(baslik))
    if re.fullmatch(r"https://[^\s\"'<>]+\.(mp4|webm)", u):
        return ('<video class="bkt-vd" src="%s" playsinline %s loop autoplay preload="metadata" aria-label="%s"></video>'
                % (E(u), "muted" if sessiz else "controls", E(baslik)))
    return ""


# ---------------------------------------------------------------- tanıtım
@kayit("hero")
def hero(b, dev, d):
    """Ana görsel: başlık, alt yazı, çağrı düğmesi; arkada görsel varsa karartılır."""
    t, s, im = v(b, "title", dev, ""), v(b, "sub", dev, ""), v(b, "img", dev, "")
    if not (t or s):
        return ""
    al = {"orta": "c", "sağ": "r"}.get(str(v(b, "align", dev, "sol")), "l")
    st = _style(b, dev)
    if im:
        st += ";background-image:linear-gradient(rgba(10,20,34,.55),rgba(10,20,34,.55)),url('%s')" % E(img_url(im))
    return ('<section class="bk bkt-hero%s" style="%s"><div class="bk-w bkt-a-%s">'
            '<h1>%s</h1>%s%s</div></section>') % (
        " bkt-ov" if im else "", st, al, E(str(t)),
        ("<p>%s</p>" % E(str(s))) if s else "", _cta(b, dev))


@kayit("hero_video")
def hero_video(b, dev, d):
    """Ana görsel + video: arkada sessiz dönen video, üstünde yazı.
    Telefonda video yerine kapak görseli kullanılır: mobil veriyi yakmamak için."""
    t, s = v(b, "title", dev, ""), v(b, "sub", dev, "")
    poster = v(b, "poster", dev, "")
    if not (t or s):
        return ""
    if dev == "phone" or not v(b, "video", dev, ""):
        arka = ("linear-gradient(rgba(10,20,34,.55),rgba(10,20,34,.55)),url('%s')" % E(img_url(poster))) if poster else ""
        st = _style(b, dev) + (";background-image:%s" % arka if arka else "")
        return ('<section class="bk bkt-hero%s" style="%s"><div class="bk-w bkt-a-c"><h1>%s</h1>%s%s</div></section>') % (
            " bkt-ov" if arka else "", st, E(str(t)), ("<p>%s</p>" % E(str(s))) if s else "", _cta(b, dev))
    vd = _video_goml(v(b, "video", dev, ""), str(t or "Tanıtım"), bool(v(b, "mute", dev, True)))
    return ('<section class="bk bkt-hero bkt-vhero" style="%s"><div class="bkt-vbg" aria-hidden="true">%s</div>'
            '<div class="bk-w bkt-a-c"><h1>%s</h1>%s%s</div></section>') % (
        _style(b, dev), vd, E(str(t)), ("<p>%s</p>" % E(str(s))) if s else "", _cta(b, dev))


@kayit("hero_slider")
def hero_slider(b, dev, d):
    """Ana sayfa slider: ok ve noktalarla gezilir, klavyeyle de çalışır."""
    sl = v(b, "slides", dev, []) or []
    sl = [x for x in sl if x] if isinstance(sl, list) else []
    if not sl:
        return ""
    yuk = _n(v(b, "h_m", dev, 420), 420) if dev == "phone" else 0
    ef = str(v(b, "effect", dev, "kayma"))
    hiz = max(2, min(_n(v(b, "speed", dev, 5), 5), 20))
    lis = "".join('<li%s><img src="%s" alt="" loading="%s"></li>' % (
        ' class="ac"' if i == 0 else "", E(img_url(k)), "eager" if i == 0 else "lazy") for i, k in enumerate(sl[:12]))
    nok = ""
    if v(b, "dots", dev, True) and len(sl) > 1:
        nok = '<div class="bkt-nk">%s</div>' % "".join(
            '<button type="button" data-g="%d" aria-label="%d. görsel"%s></button>' % (i, i + 1, ' class="ac"' if i == 0 else "")
            for i in range(min(len(sl), 12)))
    ok = ('<button class="bkt-ok bkt-sol" type="button" aria-label="Önceki">‹</button>'
          '<button class="bkt-ok bkt-sag" type="button" aria-label="Sonraki">›</button>') if v(b, "arrows", dev, True) and len(sl) > 1 else ""
    return sec(b, '<div class="bkt-sl bkt-%s" data-hiz="%d"%s role="region" aria-label="Görsel dizisi">'
               '<ul>%s</ul>%s%s</div>%s' % (
                   E(ef), hiz, (' style="--h:%dpx"' % yuk) if yuk else "", lis, ok, nok, SLIDER_JS), dev)


@kayit("hero_split")
def hero_split(b, dev, d):
    """Bölünmüş kapak: solda yazı, sağda büyük görsel."""
    t, s, im = v(b, "title", dev, ""), v(b, "sub", dev, ""), v(b, "img", dev, "")
    if not (t or s):
        return ""
    sag = ('<img src="%s" alt="" loading="lazy">' % E(img_url(im))) if im else ""
    return sec(b, '<div class="bkt-split"><div><h1>%s</h1>%s%s</div>%s</div>' % (
        E(str(t)), ("<p>%s</p>" % E(str(s))) if s else "", _cta(b, dev), sag), dev)


@kayit("hero_search")
def hero_search(b, dev, d):
    """Arama kutulu kapak: aramanın nereye gideceği kapsam ayarından gelir."""
    t, s = v(b, "title", dev, ""), v(b, "sub", dev, "")
    if not t:
        return ""
    kap = str(v(b, "scope", dev, "ürün"))
    yol = {"ürün": "/magaza", "hizmet": "/hizmetler", "ilan": "/ilanlar", "yazı": "/blog"}.get(kap, "/ara")
    ph = v(b, "ph", dev, "") or ("%s ara" % kap.capitalize())
    return sec(b, '<div class="bk-c bkt-ara"><h1>%s</h1>%s'
               '<form class="bk-form" method="get" action="%s" role="search">'
               '<label class="bk-sr" for="ar-%s">%s</label>'
               '<input id="ar-%s" name="q" type="search" placeholder="%s"><button type="submit">Ara</button>'
               '</form></div>' % (
                   E(str(t)), ("<p>%s</p>" % E(str(s))) if s else "", E(yol),
                   E(b["iid"]), E(str(ph)), E(b["iid"]), E(str(ph))), dev)


@kayit("hakkimizda")
def hakkimizda(b, dev, d):
    """Hakkımızda: fotoğraf ve hikâye yan yana."""
    t, s, im = v(b, "title", dev, ""), v(b, "sub", dev, ""), v(b, "img", dev, "")
    if not (t or s):
        return ""
    gor = ('<img src="%s" alt="" loading="lazy">' % E(img_url(im))) if im else ""
    pr = "".join("<p>%s</p>" % E(x[0]) for x in lines(s)) if s else ""
    return sec(b, '<div class="bkt-split bkt-ters">%s<div><h2>%s</h2>%s%s</div></div>' % (
        gor, E(str(t)), pr, _cta(b, dev)), dev)


@kayit("sayilarla")
def sayilarla(b, dev, d):
    """Sayılarla biz: rakamlar görününce sayar."""
    it = lines(v(b, "items", dev, ""), 2)
    if not it:
        return ""
    anim = v(b, "count_anim", dev, True)
    ks = []
    for x in it[:8]:
        sayi = x[0]
        m = re.match(r"^([\d.,]+)(.*)$", sayi.strip())
        if anim and m:
            ham = m.group(1).replace(".", "").replace(",", ".")
            ks.append('<div class="bkt-sy"><b data-hedef="%s" data-son="%s">%s</b><span>%s</span></div>' % (
                E(ham), E(m.group(2)), E(sayi), E(x[1])))
        else:
            ks.append('<div class="bkt-sy"><b>%s</b><span>%s</span></div>' % (E(sayi), E(x[1])))
    return sec(b, _head(b, dev, True) + _grid(ks, min(len(ks), 4), "2") + (SAY_JS if anim else ""), dev)


@kayit("duyuru_bar")
def duyuru_bar(b, dev, d):
    """Duyuru çubuğu: sayfanın en üstünde, kapatılabilir, geri sayımlı."""
    t = v(b, "text", dev, "") or (d.get("duyuru") or "")
    if not t:
        return ""
    bit = str(v(b, "end", dev, "") or "")
    sy = ('<span class="bkt-dsy" data-bit="%s"></span>' % E(bit)) if bit else ""
    kap = ('<button class="bkt-dx" type="button" aria-label="Duyuruyu kapat">×</button>') if v(b, "closable", dev, True) else ""
    return ('<div class="bkt-duyuru" id="d-%s" style="%s" role="region" aria-label="Duyuru">'
            '<div class="bk-w"><span>%s</span>%s%s%s</div></div>%s') % (
        E(b["iid"]), _style(b, dev), E(str(t)), sy, _cta(b, dev, "bk-btn bk-sm"), kap, DUYURU_JS)


@kayit("deger")
def deger(b, dev, d):
    """Değer önerisi: kısa faydalar, her biri bir kutu."""
    it = lines(v(b, "items", dev, ""), 2)
    if not it:
        return ""
    ks = ['<div class="bkt-dg"><b>%s</b>%s</div>' % (E(x[0]), ("<p>%s</p>" % E(x[1])) if x[1] else "") for x in it[:6]]
    return sec(b, _head(b, dev, True) + _grid(ks, min(len(ks), 3), "1"), dev)


@kayit("video_tanitim")
def video_tanitim(b, dev, d):
    """Karşılama videosu: kısa tanıtım filmi."""
    vd = _video_goml(v(b, "video", dev, ""), str(v(b, "title", dev, "") or "Tanıtım videosu"))
    if not vd:
        return _yok(b, dev)
    return sec(b, _head(b, dev, True) + vd, dev)


# ---------------------------------------------------------------- hizmet
@kayit("hizmet_liste")
def hizmet_liste(b, dev, d):
    """Hizmet ve fiyat listesi: fiyat ve süre ayrı ayrı açılıp kapanır."""
    hz = d.get("hizmetler") or []
    if not hz:
        return _yok(b, dev)
    fi, su = v(b, "show_price", dev, True), v(b, "show_dur", dev, True)
    grup = v(b, "group", dev, False)
    def sat(x):
        sag = []
        if su and x.get("dur"):
            sag.append('<span class="bkt-sure">%d dk</span>' % int(x["dur"]))
        if fi and x.get("price"):
            sag.append('<span class="bkt-fiyat">%s ₺</span>' % para(x["price"]))
        return "<li><b>%s</b>%s</li>" % (E(str(x.get("name") or "")), "".join(sag))
    if grup:
        gr = {}
        for x in hz:
            gr.setdefault(x.get("cat") or "Hizmetler", []).append(x)
        ic = "".join('<h3 class="bkt-gb">%s</h3><ul class="bkt-hz">%s</ul>' % (E(k), "".join(sat(x) for x in vv))
                     for k, vv in gr.items())
    else:
        ic = '<ul class="bkt-hz">%s</ul>' % "".join(sat(x) for x in hz)
    return sec(b, _head(b, dev) + ic, dev)


@kayit("hizmet_kart")
def hizmet_kart(b, dev, d):
    """Hizmet kartları: resimli kart dizisi, fiyatıyla."""
    hz = d.get("hizmetler") or []
    if not hz:
        return _yok(b, dev)
    n = _n(v(b, "count", dev, 8), 8)
    c, cm = _cols(b, dev, 3)
    ks = []
    for x in hz[:n]:
        alt = '<span class="bkt-fiyat">%s ₺</span>' % para(x["price"]) if x.get("price") else ""
        ks.append(_card(x.get("img") or "", x.get("name") or "", x.get("desc") or "", "/randevu", alt))
    return sec(b, _head(b, dev, True) + _grid(ks, c, cm), dev)


@kayit("hizmet_sekme")
def hizmet_sekme(b, dev, d):
    """Sekmeli hizmetler: kategoriye göre ayrılmış, açılır kapanır."""
    hz = d.get("hizmetler") or []
    if not hz:
        return _yok(b, dev)
    gr = {}
    for x in hz:
        gr.setdefault(x.get("cat") or "Hizmetler", []).append(x)
    ic = ""
    for i, (k, vv) in enumerate(gr.items()):
        sat = "".join('<li><b>%s</b>%s</li>' % (
            E(str(x.get("name") or "")), ('<span class="bkt-fiyat">%s ₺</span>' % para(x["price"])) if x.get("price") else "") for x in vv)
        ic += '<details%s><summary>%s</summary><ul class="bkt-hz">%s</ul></details>' % (" open" if not i else "", E(k), sat)
    return sec(b, _head(b, dev) + '<div class="bk-faq">%s</div>' % ic, dev)


@kayit("paketler")
def paketler(b, dev, d):
    """Paketler: çoklu seans, indirimli paket; kazanç tutarı yazılır."""
    pk = d.get("paketler") or []
    if not pk:
        return _yok(b, dev)
    c, cm = _cols(b, dev, 3)
    ks = []
    for p in pk[:_n(v(b, "count", dev, 8), 8)]:
        kaz = p.get("kazanc")
        alt = ('<div class="bkt-kaz">%s ₺ kazanç</div>' % para(kaz)) if kaz else ""
        ks.append('<div class="bkt-pk"><h3>%s</h3><div class="bkt-pf">%s ₺</div>%s%s'
                  '<a class="bk-btn" href="/randevu">Satın al</a></div>' % (
                      E(str(p.get("ad") or "")), para(p.get("fiyat")),
                      ('<p>%s</p>' % E(str(p.get("aciklama") or ""))) if p.get("aciklama") else "", alt))
    return sec(b, _head(b, dev, True) + _grid(ks, c, cm), dev)


@kayit("fiyat_tablo")
def fiyat_tablo(b, dev, d):
    """Fiyat tablosu: hizmetler tablo olarak, sütunlarda süre ve fiyat."""
    hz = d.get("hizmetler") or []
    if not hz:
        return _yok(b, dev)
    sat = "".join('<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>' % (
        E(str(x.get("name") or "")), ("%d dk" % int(x["dur"])) if x.get("dur") else "—",
        ("%s ₺" % para(x["price"])) if x.get("price") else "—") for x in hz[:40])
    return sec(b, _head(b, dev) + '<div class="bke-tbl"><table><caption class="bk-sr">Hizmet fiyatları</caption>'
               '<thead><tr><th scope="col">Hizmet</th><th scope="col">Süre</th><th scope="col">Fiyat</th></tr></thead>'
               '<tbody>%s</tbody></table></div>' % sat, dev)


@kayit("surec")
def surec(b, dev, d):
    """Süreç adımları: 1-2-3 nasıl çalışır, numaralı."""
    it = lines(v(b, "items", dev, ""), 2)
    if not it:
        return _yok(b, dev)
    ks = ['<li class="bkt-ad"><span class="bkt-no">%d</span><div><b>%s</b>%s</div></li>' % (
        i + 1, E(x[0]), ("<p>%s</p>" % E(x[1])) if x[1] else "") for i, x in enumerate(it[:6])]
    return sec(b, _head(b, dev, True) + '<ol class="bkt-surec">%s</ol>' % "".join(ks), dev)


@kayit("hesaplayici")
def hesaplayici(b, dev, d):
    """Fiyat hesaplayıcı: seçeneklerin tutarı toplanır, tahmini tutar yazar."""
    it = lines(v(b, "items", dev, ""), 2)
    if not it:
        return _yok(b, dev)
    sec_ = "".join('<label class="bkt-hs"><input type="checkbox" data-tutar="%s"> <span>%s</span>'
                   '<b>%s ₺</b></label>' % (E(re.sub(r"[^\d.]", "", x[1]) or "0"), E(x[0]), E(x[1])) for x in it[:12])
    return sec(b, _head(b, dev) + '<div class="bkt-hesap">%s'
               '<div class="bkt-top2">Tahmini tutar: <b data-top>0 ₺</b></div>'
               '<p class="bk-sr" aria-live="polite" data-oku></p></div>%s' % (sec_, HESAP_JS), dev)


@kayit("teklif")
def teklif(b, dev, d):
    """Teklif formu: ad, telefon ve mesaj; gelen kutusuna düşer."""
    return sec(b, '<div class="bkt-form-k">%s%s'
               '<form class="bkt-tk" method="post" action="/api/public/yp/teklif">'
               '<label class="f2"><span>Adınız</span><input name="ad" required maxlength="80"></label>'
               '<label class="f2"><span>Telefon</span><input name="tel" type="tel" required maxlength="20"></label>'
               '<label class="f2 bkt-tam"><span>Ne yaptırmak istiyorsunuz?</span>'
               '<textarea name="mesaj" rows="4" maxlength="2000" required></textarea></label>'
               '<button class="bk-btn" type="submit">%s</button></form></div>' % (
                   "<h2>%s</h2>" % E(str(v(b, "title", dev, "") or "Teklif alın")),
                   ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "",
                   E(str(v(b, "cta", dev, "") or "Teklif iste"))), dev)


@kayit("hediye_ceki")
def hediye_ceki(b, dev, d):
    """Hediye çeki: tutarlar işletmenin tanımladığı çeklerden."""
    ck = d.get("cekler") or []
    t = v(b, "title", dev, "") or "Hediye çeki"
    tut = ""
    if ck:
        tut = '<div class="bkt-cek">%s</div>' % "".join(
            '<a class="bkt-cekb" href="/hediye-ceki?t=%s">%s ₺</a>' % (E(str(x.get("tutar") or "")), para(x.get("tutar"))) for x in ck[:8])
    return sec(b, '<div class="bkt-split"><div><h2>%s</h2>%s%s%s</div>'
               '<div class="bkt-cekg" aria-hidden="true"><span>HEDİYE</span></div></div>' % (
                   E(str(t)), ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "",
                   tut, _cta(b, dev)), dev)


@kayit("karsilastirma")
def karsilastirma(b, dev, d):
    """Karşılaştırma tablosu: biz / diğerleri, var-yok işaretli."""
    it = lines(v(b, "items", dev, ""), 3)
    if not it:
        return _yok(b, dev)
    def im(x):
        x = (x or "").strip().lower()
        if x in ("var", "evet", "+", "✓"):
            return '<span class="bkt-var" title="var">✓</span><span class="bk-sr">var</span>'
        if x in ("yok", "hayır", "-", "✗"):
            return '<span class="bkt-yok" title="yok">✗</span><span class="bk-sr">yok</span>'
        return E(x)
    sat = "".join('<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>' % (E(x[0]), im(x[1]), im(x[2])) for x in it[:14])
    return sec(b, _head(b, dev, True) + '<div class="bke-tbl"><table><caption class="bk-sr">Karşılaştırma</caption>'
               '<thead><tr><td></td><th scope="col">Biz</th><th scope="col">Diğerleri</th></tr></thead>'
               '<tbody>%s</tbody></table></div>' % sat, dev)


# ---------------------------------------------------------------- ekip
@kayit("ekip")
def ekip(b, dev, d):
    """Ekip kartları: panelinizdeki ekipten, adı ve unvanıyla."""
    ek = d.get("ekip") or []
    if not ek:
        return _yok(b, dev)
    c, cm = _cols(b, dev, 4)
    n = _n(v(b, "count", dev, 8), 8)
    ks = []
    for x in ek[:n]:
        bas = "".join(p[0] for p in str(x.get("ad") or "").split()[:2]).upper()
        gor = ('<img src="%s" alt="%s" loading="lazy">' % (E(img_url(x.get("img"))), E(str(x.get("ad") or "")))
               ) if x.get("img") else '<span class="bkt-bh" aria-hidden="true">%s</span>' % E(bas)
        ks.append('<div class="bkt-ek">%s<b>%s</b>%s</div>' % (
            gor, E(str(x.get("ad") or "")),
            ("<span>%s</span>" % E(str(x.get("unvan") or ""))) if x.get("unvan") else ""))
    return sec(b, _head(b, dev, True) + _grid(ks, c, cm), dev)


@kayit("uzman")
def uzman(b, dev, d):
    """Uzman tanıtımı: tek kişi, uzun tanıtım yazısı."""
    t, s, im = v(b, "title", dev, ""), v(b, "sub", dev, ""), v(b, "img", dev, "")
    if not (t or s):
        return ""
    gor = ('<img src="%s" alt="%s" loading="lazy">' % (E(img_url(im)), E(str(t or "")))) if im else ""
    pr = "".join("<p>%s</p>" % E(x[0]) for x in lines(s)) if s else ""
    return sec(b, '<div class="bkt-split bkt-ters">%s<div><h2>%s</h2>%s%s</div></div>' % (gor, E(str(t)), pr, _cta(b, dev)), dev)


@kayit("kariyer")
def kariyer(b, dev, d):
    """Eleman arıyoruz: açık ilan varsa listelenir, yoksa genel başvuru."""
    il = d.get("ilanlar") or []
    t = v(b, "title", dev, "") or "Ekibimize katılın"
    lst = ""
    if il:
        lst = '<ul class="bkt-ilan">%s</ul>' % "".join(
            "<li><b>%s</b>%s</li>" % (E(str(x.get("ad") or "")), ("<span>%s</span>" % E(str(x.get("yer") or ""))) if x.get("yer") else "")
            for x in il[:8])
    return sec(b, '<div class="bk-c"><h2>%s</h2>%s%s%s</div>' % (
        E(str(t)), ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "",
        lst, _cta(b, dev) or '<a class="bk-btn" href="/kariyer">Başvur</a>'), dev)


# ---------------------------------------------------------------- betikler
SLIDER_JS = ("<script>(function(){var w=document.currentScript.previousElementSibling;if(!w)return;"
             "var u=w.querySelector('ul'),l=[].slice.call(u.children),n=[].slice.call(w.querySelectorAll('.bkt-nk button'));"
             "if(l.length<2)return;var i=0,az=matchMedia('(prefers-reduced-motion:reduce)').matches,tm;"
             "function g(k){l[i].classList.remove('ac');if(n[i])n[i].classList.remove('ac');"
             "i=(k+l.length)%l.length;l[i].classList.add('ac');if(n[i])n[i].classList.add('ac')}"
             "function don(){if(az)return;clearTimeout(tm);tm=setTimeout(function(){g(i+1);don()},(+w.dataset.hiz||5)*1000)}"
             "w.addEventListener('click',function(e){var t=e.target;"
             "if(t.classList.contains('bkt-sag'))g(i+1);else if(t.classList.contains('bkt-sol'))g(i-1);"
             "else if(t.dataset.g!==undefined)g(+t.dataset.g);else return;don()});"
             "w.addEventListener('keydown',function(e){if(e.key==='ArrowRight'){g(i+1);don()}else if(e.key==='ArrowLeft'){g(i-1);don()}});"
             "w.addEventListener('mouseenter',function(){clearTimeout(tm)});w.addEventListener('mouseleave',don);don()})();</script>")

SAY_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
          "var ns=[].slice.call(e.querySelectorAll('[data-hedef]'));if(!ns.length)return;"
          "if(matchMedia('(prefers-reduced-motion:reduce)').matches)return;"
          "function say(b){var h=parseFloat(b.dataset.hedef);if(isNaN(h))return;var t0=null,sr=900;"
          "function a(t){if(!t0)t0=t;var p=Math.min((t-t0)/sr,1);"
          "b.textContent=(h%1?(h*p).toFixed(1):Math.round(h*p)).toLocaleString('tr-TR')+(b.dataset.son||'');"
          "if(p<1)requestAnimationFrame(a)}b.textContent='0'+(b.dataset.son||'');requestAnimationFrame(a)}"
          "if(!window.IntersectionObserver){ns.forEach(say);return}"
          "var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){say(x.target);io.unobserve(x.target)}})},{threshold:.4});"
          "ns.forEach(function(b){io.observe(b)})})();</script>")

DUYURU_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
             "var k='ok_duy_'+e.id;try{if(localStorage.getItem(k)==='1'){e.remove();return}}catch(x){}"
             "var x2=e.querySelector('.bkt-dx');if(x2)x2.addEventListener('click',function(){e.remove();"
             "try{localStorage.setItem(k,'1')}catch(y){}});"
             "var s=e.querySelector('.bkt-dsy');if(!s)return;var h=new Date(s.dataset.bit).getTime();if(isNaN(h))return;"
             "function p(n){return(n<10?'0':'')+n}function t(){var f=h-Date.now();if(f<0){s.textContent='';return}"
             "var g=Math.floor(f/86400000),sa=Math.floor(f/3600000)%24,d=Math.floor(f/60000)%60,sn=Math.floor(f/1000)%60;"
             "s.textContent=(g?g+' gün ':'')+p(sa)+':'+p(d)+':'+p(sn);setTimeout(t,1000)}t()})();</script>")

HESAP_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
            "var t=e.querySelector('[data-top]'),o=e.querySelector('[data-oku]');"
            "e.addEventListener('change',function(){var s=0;"
            "[].forEach.call(e.querySelectorAll('input[type=checkbox]'),function(c){if(c.checked)s+=parseFloat(c.dataset.tutar)||0});"
            "var m=s.toLocaleString('tr-TR')+' \\u20ba';t.textContent=m;if(o)o.textContent='Tahmini tutar '+m})})();</script>")

CSS = (
    ".bkt-hero{padding:clamp(40px,7vw,96px) 0}"
    ".bkt-hero h1{font-size:clamp(30px,5.4vw,54px);line-height:1.12;margin:0 0 14px;font-family:var(--bk-fh,inherit)}"
    ".bkt-hero p{font-size:clamp(16px,2vw,20px);max-width:60ch;opacity:.9;margin:0 0 18px}"
    ".bkt-hero.bkt-ov{background-size:cover;background-position:center;color:#fff}"
    ".bkt-a-c{text-align:center}.bkt-a-c p{margin-left:auto;margin-right:auto}"
    ".bkt-a-r{text-align:right}.bkt-a-r p{margin-left:auto}"
    ".bkt-vhero{position:relative;overflow:hidden;color:#fff}"
    ".bkt-vbg{position:absolute;inset:0;z-index:0}.bkt-vbg:after{content:'';position:absolute;inset:0;background:rgba(10,20,34,.55)}"
    ".bkt-vbg .bk-vid{padding-top:0;height:100%;border-radius:0}.bkt-vd{width:100%;height:100%;object-fit:cover}"
    ".bkt-vhero .bk-w{position:relative;z-index:1}"
    ".bkt-split{display:grid;grid-template-columns:1fr 1fr;gap:34px;align-items:center}"
    ".bkt-split img{width:100%;border-radius:var(--bk-r,12px);object-fit:cover}"
    ".bkt-split h1,.bkt-split h2{font-size:clamp(24px,3.4vw,38px);margin:0 0 12px}"
    "@media(max-width:780px){.bkt-split{grid-template-columns:1fr;gap:20px}.bkt-ters>div{order:-1}}"
    ".bkt-ara h1{margin-bottom:10px}.bkt-ara .bk-form{margin-top:18px}"
    ".bkt-sl{position:relative;border-radius:var(--bk-r,12px);overflow:hidden}"
    ".bkt-sl ul{list-style:none;margin:0;padding:0;position:relative;height:var(--h,clamp(260px,42vw,520px))}"
    ".bkt-sl li{position:absolute;inset:0;opacity:0;transition:opacity .5s}"
    ".bkt-sl li.ac{opacity:1}.bkt-sl img{width:100%;height:100%;object-fit:cover;display:block}"
    ".bkt-kayma li{transform:translateX(16px)}.bkt-kayma li.ac{transform:none;transition:opacity .5s,transform .5s}"
    ".bkt-yakınlaşma li.ac img{animation:bkt-zoom 7s ease-out both}"
    "@keyframes bkt-zoom{from{transform:scale(1)}to{transform:scale(1.07)}}"
    ".bkt-ok{position:absolute;top:50%;transform:translateY(-50%);width:44px;height:44px;border-radius:50%;"
    "border:0;background:rgba(255,255,255,.88);font-size:26px;line-height:1;cursor:pointer;color:#17202c}"
    ".bkt-sol{left:12px}.bkt-sag{right:12px}"
    ".bkt-nk{position:absolute;left:0;right:0;bottom:12px;display:flex;gap:7px;justify-content:center}"
    ".bkt-nk button{width:9px;height:9px;padding:0;border-radius:50%;border:0;background:rgba(255,255,255,.55);cursor:pointer}"
    ".bkt-nk button.ac{background:#fff;width:22px;border-radius:5px}"
    ".bkt-duyuru{background:var(--bk-bg,var(--dk));color:var(--bk-fg,#fff);font-size:14.5px;position:relative}"
    ".bkt-duyuru .bk-w{display:flex;gap:12px;align-items:center;justify-content:center;flex-wrap:wrap;padding-top:9px;padding-bottom:9px}"
    ".bkt-dsy{font-variant-numeric:tabular-nums;font-weight:800;background:rgba(255,255,255,.16);padding:2px 9px;border-radius:7px}"
    ".bkt-dx{position:absolute;right:10px;top:50%;transform:translateY(-50%);border:0;background:none;color:inherit;font-size:21px;cursor:pointer;line-height:1;opacity:.7}"
    ".bkt-dg{background:#fff;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);padding:18px 19px}"
    ".bkt-dg b{display:block;font-size:17px;margin-bottom:5px}.bkt-dg p{margin:0;font-size:15px;opacity:.78}"
    ".bkt-sy{text-align:center}"
    ".bkt-sy b{display:block;font-size:clamp(28px,4.6vw,46px);font-weight:800;color:var(--ac);line-height:1.1;font-variant-numeric:tabular-nums;font-family:var(--bk-fh,inherit)}"
    ".bkt-sy span{font-size:15px;opacity:.78}"
    ".bkt-hz{list-style:none;margin:0 0 14px;padding:0;display:grid;gap:1px;background:#e7e4dc;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);overflow:hidden}"
    ".bkt-hz li{background:#fff;padding:13px 16px;display:flex;gap:12px;align-items:baseline}"
    ".bkt-hz b{font-weight:600}.bkt-sure{margin-left:auto;opacity:.65;font-size:14px}"
    ".bkt-fiyat{font-weight:800;color:var(--dk);margin-left:14px}"
    ".bkt-hz .bkt-sure+.bkt-fiyat{margin-left:0}"
    ".bkt-gb{margin:18px 0 8px;font-size:16px;opacity:.8}"
    ".bkt-pk{background:#fff;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);padding:20px;text-align:center;display:flex;flex-direction:column;gap:8px}"
    ".bkt-pk h3{margin:0;font-size:18px}.bkt-pf{font-size:28px;font-weight:800;color:var(--dk)}"
    ".bkt-pk p{margin:0;font-size:14.5px;opacity:.78}.bkt-pk .bk-btn{margin-top:auto}"
    ".bkt-kaz{font-size:13.5px;font-weight:700;color:var(--ok,#16794a)}"
    ".bkt-surec{list-style:none;margin:0;padding:0;display:grid;gap:14px;counter-reset:s}"
    ".bkt-ad{display:flex;gap:14px;align-items:flex-start}"
    ".bkt-no{flex:none;width:34px;height:34px;border-radius:50%;background:var(--ac);color:#fff;display:grid;place-items:center;font-weight:800}"
    ".bkt-ad b{display:block;font-size:16.5px}.bkt-ad p{margin:3px 0 0;font-size:15px;opacity:.78}"
    ".bkt-hesap{max-width:560px;margin:0 auto;display:grid;gap:9px}"
    ".bkt-hs{display:flex;gap:11px;align-items:center;background:#fff;border:1px solid #e7e4dc;border-radius:10px;padding:12px 14px;cursor:pointer}"
    ".bkt-hs span{flex:1}.bkt-hs b{font-weight:700}"
    ".bkt-top2{text-align:right;font-size:18px;padding-top:6px}"
    ".bkt-form-k{max-width:620px;margin:0 auto}"
    ".bkt-tk{display:grid;grid-template-columns:1fr 1fr;gap:13px;margin-top:16px}"
    ".bkt-tk .bkt-tam{grid-column:1/-1}.bkt-tk button{grid-column:1/-1;justify-self:start}"
    ".f2{display:grid;gap:5px;font-size:13.5px;font-weight:600}"
    ".f2 input,.f2 textarea{border:1px solid #d7d3c8;border-radius:10px;padding:11px 13px;font:16px inherit;min-height:46px;background:#fff}"
    "@media(max-width:620px){.bkt-tk{grid-template-columns:1fr}}"
    ".bkt-cek{display:flex;gap:9px;flex-wrap:wrap;margin:0 0 16px}"
    ".bkt-cekb{border:1.5px solid var(--ac);color:var(--ac);border-radius:10px;padding:9px 16px;text-decoration:none;font-weight:700}"
    ".bkt-cekg{background:linear-gradient(135deg,var(--dk),var(--ac));border-radius:var(--bk-r,12px);"
    "aspect-ratio:8/5;display:grid;place-items:center;color:#fff;font-weight:800;letter-spacing:.2em;font-size:21px}"
    ".bkt-var{color:#16794a;font-weight:800}.bkt-yok{color:#b42318;font-weight:800}"
    ".bkt-ek{text-align:center}"
    ".bkt-ek img,.bkt-bh{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:var(--bk-r,12px);display:grid;place-items:center;background:#ece9e1}"
    ".bkt-bh{font-size:30px;font-weight:800;color:#9aa1ad}"
    ".bkt-ek b{display:block;margin-top:9px;font-size:16px}.bkt-ek span{font-size:14px;opacity:.72}"
    ".bkt-ilan{list-style:none;padding:0;margin:0 0 16px;display:grid;gap:8px;max-width:520px;margin-inline:auto}"
    ".bkt-ilan li{background:#fff;border:1px solid #e7e4dc;border-radius:10px;padding:11px 15px;display:flex;gap:12px}"
    ".bkt-ilan span{margin-left:auto;opacity:.7;font-size:14px}"
)
