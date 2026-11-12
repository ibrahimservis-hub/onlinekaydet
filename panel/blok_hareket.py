# -*- coding: utf-8 -*-
"""Hareketli, güven ve görsel bölümleri — her bölümün kendi üreticisi.

Hareketli bölümlerin tamamı "hareketi azalt" ayarına uyar: işletim sisteminde bu ayar
açıksa animasyon çalışmaz, içerik olduğu gibi görünür. Telefonda kapatma anahtarı
(on_m) ayrıca her birinde vardır.
"""
import html as _h
import re

from blokgen import E, v, lines, img_url, link, para, sec, _head, _cta, _cols, _grid, _n, _style

KAYIT = {}


def kayit(bid):
    def sar(fn):
        KAYIT[bid] = fn
        return fn
    return sar


def _yok(b, dev):
    return sec(b, _head(b, dev, True), dev) if v(b, "title", dev, "") else ""


def _hiz(b, dev, d=5, en_az=2, en_cok=40):
    """Kaydırıcıdaki hız: büyük değer daha hızlı. Saniyeye çevrilir."""
    h = max(1, min(_n(v(b, "speed", dev, d), d), 10))
    return round(en_cok - (h - 1) * (en_cok - en_az) / 9.0, 1)


def _gorseller(b, dev, d, anahtar="imgs"):
    im = v(b, anahtar, dev, []) or []
    if isinstance(im, list) and im:
        return [x for x in im if x]
    return [x for x in (d.get("fotograflar") or []) if x]


# ---------------------------------------------------------------- hareketli
@kayit("kayan_yazi")
def kayan_yazi(b, dev, d):
    """Kayan yazı şeridi: sonsuz döner, fareyle durur, hareket azaltmada durur."""
    t = v(b, "title", dev, "") or v(b, "text", dev, "")
    if not t:
        return ""
    par = [x[0] for x in lines(v(b, "sub", dev, ""))] or [str(t)]
    bir = "".join('<span>%s</span><i aria-hidden="true">•</i>' % E(x) for x in par)
    return ('<section class="bk bkh-kayan" style="%s;--sure:%ss" aria-label="%s">'
            '<div class="bkh-ks"><div class="bkh-kp">%s</div><div class="bkh-kp" aria-hidden="true">%s</div></div>'
            "</section>") % (_style(b, dev), _hiz(b, dev, 5, 8, 60), E(str(t)), bir, bir)


@kayit("daktilo")
def daktilo(b, dev, d):
    """Daktilo başlık: harf harf yazılır. Hareket azaltmada tam başlık görünür."""
    t = v(b, "title", dev, "")
    if not t:
        return ""
    sat = [x[0] for x in lines(v(b, "sub", dev, ""))]
    return sec(b, '<div class="bkh-dk"><h2><span data-yaz="%s">%s</span><i class="bkh-im" aria-hidden="true"></i></h2>%s</div>%s' % (
        _h.escape("|".join(sat) if sat else str(t), quote=True), E(str(t)),
        "".join("<p>%s</p>" % E(x) for x in sat[:1]), DAKTILO_JS), dev)


@kayit("sayac_anim")
def sayac_anim(b, dev, d):
    """Sayaç animasyonu: rakamlar görününce sıfırdan sayar."""
    it = lines(v(b, "sub", dev, ""), 2) or lines(v(b, "items", dev, ""), 2)
    if not it:
        return _yok(b, dev)
    ks = []
    for x in it[:8]:
        m = re.match(r"^([\d.,]+)(.*)$", x[0].strip())
        ham = m.group(1).replace(".", "").replace(",", ".") if m else ""
        ks.append('<div class="bkh-sy"><b%s>%s</b><span>%s</span></div>' % (
            (' data-hedef="%s" data-son="%s"' % (E(ham), E(m.group(2)))) if ham else "", E(x[0]), E(x[1])))
    return sec(b, _head(b, dev, True) + _grid(ks, min(len(ks), 4), "2") + SAYAC_JS, dev)


@kayit("scroll_in")
def scroll_in(b, dev, d):
    """Kaydırınca beliren: maddeler sırayla yumuşak girer."""
    it = lines(v(b, "sub", dev, ""), 2)
    if not it:
        return _yok(b, dev)
    ks = "".join('<li class="bkh-gir" style="--g:%dms"><b>%s</b>%s</li>' % (
        i * 90, E(x[0]), ("<span>%s</span>" % E(x[1])) if x[1] else "") for i, x in enumerate(it[:10]))
    return sec(b, _head(b, dev) + '<ul class="bkh-liste">%s</ul>%s' % (ks, GIR_JS), dev)


@kayit("sticky")
def sticky(b, dev, d):
    """Yapışkan bölüm: solda yazı sabit kalır, sağdaki içerik kayar.
    Telefonda yapışkanlık kapanır: küçük ekranda ekranın yarısını kaplardı."""
    t, s = v(b, "title", dev, ""), v(b, "sub", dev, "")
    if not (t or s):
        return ""
    sag = "".join('<div class="bkh-yp-k"><b>%s</b>%s</div>' % (
        E(x[0]), ("<p>%s</p>" % E(x[1])) if len(x) > 1 and x[1] else "") for x in lines(s, 2)[:8])
    return sec(b, '<div class="bkh-yp"><div class="bkh-yp-s"><h2>%s</h2>%s</div><div>%s</div></div>' % (
        E(str(t)), _cta(b, dev), sag), dev)


@kayit("parallax")
def parallax(b, dev, d):
    """Parallax arka plan: görsel sayfadan yavaş kayar.
    Telefonda sabit arka plan kullanılır: mobil tarayıcılarda parallax takılır."""
    im = v(b, "img", dev, "") or (_gorseller(b, dev, d) or [""])[0]
    t, s = v(b, "title", dev, ""), v(b, "sub", dev, "")
    if not im and not t:
        return ""
    st = _style(b, dev)
    if im:
        st += ";background-image:linear-gradient(rgba(10,20,34,.5),rgba(10,20,34,.5)),url('%s')" % E(img_url(im))
    return ('<section class="bk bkh-par%s" style="%s"><div class="bk-w bk-c">%s%s%s</div></section>') % (
        " bkh-sbt" if dev == "phone" else "", st,
        ("<h2>%s</h2>" % E(str(t))) if t else "",
        ("<p>%s</p>" % E(str(s))) if s else "", _cta(b, dev))


@kayit("logo_akis")
def logo_akis(b, dev, d):
    """Kayan logo şeridi: markalar sonsuz akar, fareyle durur."""
    im = _gorseller(b, dev, d)
    if not im:
        return _yok(b, dev)
    bir = "".join('<img src="%s" alt="" loading="lazy">' % E(img_url(k)) for k in im[:30])
    return sec(b, _head(b, dev, True) + '<div class="bkh-ls" style="--sure:%ss">'
               '<div class="bkh-lp">%s</div><div class="bkh-lp" aria-hidden="true">%s</div></div>' % (
                   _hiz(b, dev, 5, 10, 60), bir, bir), dev)


@kayit("kart_deste")
def kart_deste(b, dev, d):
    """Kart destesi: kartlar kaydırdıkça üst üste yapışır."""
    it = lines(v(b, "sub", dev, ""), 2)
    if not it:
        return _yok(b, dev)
    ks = "".join('<div class="bkh-dst" style="--i:%d"><b>%s</b>%s</div>' % (
        i, E(x[0]), ("<p>%s</p>" % E(x[1])) if x[1] else "") for i, x in enumerate(it[:6]))
    return sec(b, _head(b, dev, True) + '<div class="bkh-dstl">%s</div>' % ks, dev)


@kayit("once_sonra")
def once_sonra(b, dev, d):
    """Öncesi–Sonrası: sürgüyle iki fotoğraf karşılaştırılır, klavyeyle de çalışır."""
    im = _gorseller(b, dev, d)
    if len(im) < 2:
        return _yok(b, dev)
    return sec(b, _head(b, dev, True) + (
        '<div class="bkh-os"><img class="bkh-os-a" src="%s" alt="Öncesi" loading="lazy">'
        '<div class="bkh-os-b"><img src="%s" alt="Sonrası" loading="lazy"></div>'
        '<input type="range" min="0" max="100" value="50" aria-label="Öncesi ve sonrası karşılaştırma sürgüsü">'
        '<span class="bkh-os-c" aria-hidden="true"></span></div>%s') % (
            E(img_url(im[0])), E(img_url(im[1])), OS_JS), dev)


@kayit("ilerleme")
def ilerleme(b, dev, d):
    """Sayfa ilerleme çubuğu: en üstte, okunan oranı gösterir."""
    return ('<div class="bkh-ilr" id="il-%s" role="progressbar" aria-label="Sayfa ilerlemesi" '
            'aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><i></i></div>%s') % (E(b["iid"]), ILERLEME_JS)


# ---------------------------------------------------------------- güven
def _yildiz(n):
    n = max(0, min(int(round(float(n or 0))), 5))
    return '<span class="bkh-yd" aria-hidden="true">%s</span><span class="bk-sr">5 üzerinden %d</span>' % ("★" * n + "☆" * (5 - n), n)


@kayit("yorumlar")
def yorumlar(b, dev, d):
    """Müşteri yorumları: puan eşiğinin altındakiler gösterilmez, üç ayrı düzen."""
    yo = [x for x in (d.get("yorumlar") or []) if int(x.get("puan") or 5) >= _n(v(b, "min_star", dev, 4), 4)]
    if not yo:
        return _yok(b, dev)
    n = _n(v(b, "count", dev, 8), 8)
    yo = yo[:n]
    st = str(v(b, "style", dev, "kart"))
    def kart(x):
        return ('<figure class="bkh-yr">%s<blockquote>%s</blockquote>'
                '<figcaption>%s</figcaption></figure>') % (
            _yildiz(x.get("puan")), E(str(x.get("yazi") or "")), E(str(x.get("ad") or "")))
    if st == "tek büyük":
        ic = '<div class="bkh-tek">%s</div>' % kart(yo[0])
    elif st == "kayan şerit":
        ic = '<div class="bkh-yrs" role="region" aria-label="Yorumlar" tabindex="0">%s</div>' % "".join(kart(x) for x in yo)
    else:
        c, cm = _cols(b, dev, 3)
        ic = _grid([kart(x) for x in yo], c, cm)
    return sec(b, _head(b, dev, True) + ic, dev)


@kayit("google_yorum")
def google_yorum(b, dev, d):
    """Google yorumları: puan ortalaması ve yorum sayısı Google'dan gelir."""
    g = d.get("google") or {}
    yo = g.get("yorumlar") or []
    if not yo and not g.get("puan"):
        return _yok(b, dev)
    ozet = ""
    if v(b, "show_score", dev, True) and g.get("puan"):
        ozet = ('<div class="bkh-gz"><b>%s</b>%s<span>%d değerlendirme</span></div>' % (
            E(str(g.get("puan"))), _yildiz(g.get("puan")), int(g.get("adet") or 0)))
    c, cm = _cols(b, dev, 3)
    ks = ['<figure class="bkh-yr">%s<blockquote>%s</blockquote><figcaption>%s</figcaption></figure>' % (
        _yildiz(x.get("puan")), E(str(x.get("yazi") or "")), E(str(x.get("ad") or ""))) for x in yo[:_n(v(b, "count", dev, 8), 8)]]
    return sec(b, _head(b, dev, True) + ozet + (_grid(ks, c, cm) if ks else ""), dev)


@kayit("video_yorum")
def video_yorum(b, dev, d):
    """Video yorum: müşteri videoları yan yana."""
    vd = [x for x in (d.get("video_yorum") or []) if x.get("url")]
    if not vd:
        return _yok(b, dev)
    ks = []
    for x in vd[:6]:
        m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([A-Za-z0-9_-]{6,20})", str(x.get("url")))
        if not m:
            continue
        ks.append('<figure class="bkh-vy"><div class="bk-vid"><iframe src="https://www.youtube-nocookie.com/embed/%s" '
                  'title="%s" loading="lazy" allowfullscreen></iframe></div><figcaption>%s</figcaption></figure>' % (
                      E(m.group(1)), E(str(x.get("ad") or "Müşteri yorumu")), E(str(x.get("ad") or ""))))
    if not ks:
        return _yok(b, dev)
    return sec(b, _head(b, dev, True) + _grid(ks, min(len(ks), 3), "1"), dev)


@kayit("yildiz_ozet")
def yildiz_ozet(b, dev, d):
    """Yıldız özeti: ortalama puan ve yıldız dağılımı çubuklarla."""
    yo = d.get("yorumlar") or []
    if not yo:
        return _yok(b, dev)
    pu = [int(x.get("puan") or 5) for x in yo]
    ort = sum(pu) / float(len(pu))
    dag = {k: pu.count(k) for k in range(5, 0, -1)}
    en = max(dag.values()) or 1
    cub = "".join('<div class="bkh-dg"><span>%d</span><i><b style="width:%d%%"></b></i><span>%d</span></div>' % (
        k, int(dag[k] * 100 / en), dag[k]) for k in range(5, 0, -1))
    return sec(b, _head(b, dev, True) + (
        '<div class="bkh-oz"><div class="bkh-ozp"><b>%s</b>%s<span>%d değerlendirme</span></div>'
        '<div class="bkh-dgl">%s</div></div>') % (
            ("%.1f" % ort).replace(".", ","), _yildiz(round(ort)), len(pu), cub), dev)


@kayit("markalar")
def markalar(b, dev, d):
    """Kullandığımız markalar: logo şeridi."""
    return _logo_sabit(b, dev, d, "Markalar")


@kayit("referans")
def referans(b, dev, d):
    """Referans müşteriler: çalıştığınız firmaların logoları."""
    return _logo_sabit(b, dev, d, "Referanslar")


def _logo_sabit(b, dev, d, et):
    im = v(b, "imgs", dev, []) or []
    im = [x for x in im if x] if isinstance(im, list) else []
    if not im:
        return _yok(b, dev)
    ks = "".join('<img src="%s" alt="" loading="lazy">' % E(img_url(k)) for k in im[:40])
    return sec(b, _head(b, dev, True) + '<div class="bkh-lg" role="list" aria-label="%s">%s</div>' % (E(et), ks), dev)


@kayit("sertifika")
def sertifika(b, dev, d):
    """Sertifikalar: belgeler büyütülebilir kutularda."""
    im = v(b, "imgs", dev, []) or []
    im = [x for x in im if x] if isinstance(im, list) else (d.get("belgeler") or [])
    if not im:
        return _yok(b, dev)
    ks = ['<a class="bkh-srt" href="%s" target="_blank" rel="noopener">'
          '<img src="%s" alt="Belge %d" loading="lazy"></a>' % (E(img_url(k)), E(img_url(k)), i + 1)
          for i, k in enumerate(im[:20])]
    return sec(b, _head(b, dev, True) + _grid(ks, 5, "3"), dev)


@kayit("basinda")
def basinda(b, dev, d):
    """Basında biz: haber başlığı, yayın adı ve bağlantısı."""
    it = lines(v(b, "items", dev, ""), 3)
    if not it:
        return _yok(b, dev)
    ks = ""
    for x in it[:12]:
        to = link(x[2]) if len(x) > 2 else ""
        ic = '<b>%s</b><span>%s</span>' % (E(x[0]), E(x[1]))
        ks += ('<li>%s</li>' % (('<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(to), ic)) if to else ic))
    return sec(b, _head(b, dev) + '<ul class="bkh-bs">%s</ul>' % ks, dev)


@kayit("guven_rozet")
def guven_rozet(b, dev, d):
    """Güvence rozetleri: SSL, iade, KVKK gibi kısa güven sözleri."""
    it = lines(v(b, "items", dev, ""), 2)
    if not it:
        return ""
    ks = "".join('<div class="bkh-gr"><b>%s</b>%s</div>' % (
        E(x[0]), ("<span>%s</span>" % E(x[1])) if x[1] else "") for x in it[:6])
    return sec(b, '<div class="bkh-grl">%s</div>' % ks, dev)


# ---------------------------------------------------------------- görsel
@kayit("galeri")
def galeri(b, dev, d):
    """Galeri: ızgara, tıklayınca büyütür (klavyeyle kapatılabilir)."""
    im = _gorseller(b, dev, d)
    if not im:
        return _yok(b, dev)
    n = _n(v(b, "count", dev, 8), 8)
    c, cm = _cols(b, dev, 4)
    buy = v(b, "light", dev, True)
    ks = []
    for i, k in enumerate(im[:n]):
        g = '<img src="%s" alt="Fotoğraf %d" loading="lazy">' % (E(img_url(k)), i + 1)
        ks.append(('<button class="bkh-gl" type="button" data-buyut="%s" aria-label="%d. fotoğrafı büyüt">%s</button>'
                   % (E(img_url(k)), i + 1, g)) if buy else '<div class="bkh-gl">%s</div>' % g)
    return sec(b, _head(b, dev, True) + _grid(ks, c, cm) + (BUYUT_JS if buy else ""), dev)


@kayit("galeri_kayan")
def galeri_kayan(b, dev, d):
    """Kayan galeri: yatay fotoğraf şeridi, parmakla sürüklenir."""
    im = _gorseller(b, dev, d)
    if not im:
        return _yok(b, dev)
    ks = "".join('<img src="%s" alt="Fotoğraf %d" loading="lazy">' % (E(img_url(k)), i + 1) for i, k in enumerate(im[:30]))
    oto = ' data-oto="1"' if v(b, "anim_auto", dev, False) else ""
    return sec(b, _head(b, dev, True) + '<div class="bkh-gks"%s role="region" aria-label="Fotoğraf şeridi" tabindex="0">%s</div>%s' % (
        oto, ks, KAY_JS if oto else ""), dev)


@kayit("masonry")
def masonry(b, dev, d):
    """Masonry galeri: fotoğraflar kendi oranında, farklı boylarda yerleşir."""
    im = _gorseller(b, dev, d)
    if not im:
        return _yok(b, dev)
    n = _n(v(b, "count", dev, 12), 12)
    c, cm = _cols(b, dev, 4)
    ks = "".join('<img src="%s" alt="Fotoğraf %d" loading="lazy">' % (E(img_url(k)), i + 1) for i, k in enumerate(im[:n]))
    return sec(b, _head(b, dev, True) + '<div class="bkh-ms" style="--c:%d;--cm:%s">%s</div>' % (
        c, E("1" if cm == "kaydırmalı" else cm), ks), dev)


@kayit("instagram")
def instagram(b, dev, d):
    """Instagram akışı: hesap bağlıysa son gönderiler, değilse hesaba bağlantı."""
    gs = d.get("instagram") or []
    hesap = str((d.get("baglantilar") or {}).get("instagram") or "")
    if not gs:
        if not hesap:
            return ""
        return sec(b, _head(b, dev, True) + '<div class="bk-c"><a class="bk-btn" href="%s" target="_blank" rel="noopener">'
                   "Instagram'da takip edin</a></div>" % E(hesap), dev)
    n = _n(v(b, "count", dev, 8), 8)
    ks = ['<a class="bkh-ig" href="%s" target="_blank" rel="noopener">'
          '<img src="%s" alt="Instagram gönderisi" loading="lazy"></a>' % (E(link(x.get("url")) or hesap or "#"), E(img_url(x.get("img"))))
          for x in gs[:n]]
    return sec(b, _head(b, dev, True) + _grid(ks, 4, "2"), dev)


@kayit("video_galeri")
def video_galeri(b, dev, d):
    """Video galeri: birden çok video, her biri kendi başlığıyla."""
    it = lines(v(b, "items", dev, ""), 2)
    if not it:
        return _yok(b, dev)
    c, cm = _cols(b, dev, 3)
    ks = []
    for x in it[:_n(v(b, "count", dev, 8), 8)]:
        m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([A-Za-z0-9_-]{6,20})", x[1] or x[0])
        if not m:
            continue
        ks.append('<figure class="bkh-vg"><div class="bk-vid"><iframe src="https://www.youtube-nocookie.com/embed/%s" '
                  'title="%s" loading="lazy" allowfullscreen></iframe></div>%s</figure>' % (
                      E(m.group(1)), E(x[0] or "Video"), ("<figcaption>%s</figcaption>" % E(x[0])) if x[0] else ""))
    if not ks:
        return _yok(b, dev)
    return sec(b, _head(b, dev, True) + _grid(ks, c, cm), dev)


@kayit("gorsel_360")
def gorsel_360(b, dev, d):
    """360° görsel: sürükledikçe kareler değişir."""
    im = _gorseller(b, dev, d)
    if len(im) < 4:
        return _yok(b, dev)
    ks = "".join('<img src="%s" alt="%s" loading="%s"%s>' % (
        E(img_url(k)), "360 derece görünüm" if not i else "", "eager" if not i else "lazy",
        "" if not i else ' hidden') for i, k in enumerate(im[:36]))
    return sec(b, _head(b, dev, True) + '<div class="bkh-360" role="img" aria-label="360 derece görünüm, sürükleyerek çevirin" tabindex="0">%s'
               '<span class="bkh-360i" aria-hidden="true">↔ çevirmek için sürükleyin</span></div>%s' % (ks, D360_JS), dev)


@kayit("tam_gorsel")
def tam_gorsel(b, dev, d):
    """Tam genişlik görsel: sayfayı bölen büyük kare. Telefon için ayrı görsel verilebilir."""
    im = v(b, "img_m", dev, "") if dev == "phone" and v(b, "img_m", dev, "") else v(b, "img", dev, "")
    if not im:
        return ""
    t, s = v(b, "title", dev, ""), v(b, "sub", dev, "")
    yaz = ""
    if t or s:
        yaz = '<div class="bkh-tgy"><div class="bk-w">%s%s</div></div>' % (
            ("<h2>%s</h2>" % E(str(t))) if t else "", ("<p>%s</p>" % E(str(s))) if s else "")
    return ('<section class="bk bkh-tg" style="%s"><img src="%s" alt="%s" loading="lazy">%s</section>') % (
        _style(b, dev), E(img_url(im)), E(str(t or "")), yaz)


@kayit("resim_yazi")
def resim_yazi(b, dev, d):
    """Resim + yazı: resmin hangi yanda duracağı seçilir."""
    t, s, im = v(b, "title", dev, ""), v(b, "sub", dev, ""), v(b, "img", dev, "")
    if not (t or s):
        return ""
    gor = ('<img src="%s" alt="" loading="lazy">' % E(img_url(im))) if im else ""
    yazi = '<div><h2>%s</h2>%s%s</div>' % (
        E(str(t)), "".join("<p>%s</p>" % E(x[0]) for x in lines(s)), _cta(b, dev))
    sag = str(v(b, "side", dev, "sol")) == "sağ"
    return sec(b, '<div class="bkh-rz%s">%s%s</div>' % (" bkh-rz-s" if sag else "", gor, yazi), dev)


# ---------------------------------------------------------------- betikler
_AZ = "if(matchMedia('(prefers-reduced-motion:reduce)').matches)return;"

DAKTILO_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
              "var s=e.querySelector('[data-yaz]');if(!s)return;" + _AZ +
              "var l=(s.dataset.yaz||'').split('|').filter(Boolean);if(!l.length)return;"
              "var i=0,j=0,sil=false;s.textContent='';"
              "function a(){var m=l[i];s.textContent=m.slice(0,j);"
              "if(!sil&&j<m.length){j++;setTimeout(a,55)}else if(!sil){sil=true;setTimeout(a,1400)}"
              "else if(j>0){j--;setTimeout(a,28)}else{sil=false;i=(i+1)%l.length;setTimeout(a,220)}}a()})();</script>")

SAYAC_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;" + _AZ +
            "var ns=[].slice.call(e.querySelectorAll('[data-hedef]'));if(!ns.length)return;"
            "function say(b){var h=parseFloat(b.dataset.hedef);if(isNaN(h))return;var t0=null;"
            "function a(t){if(!t0)t0=t;var p=Math.min((t-t0)/900,1);"
            "b.textContent=(h%1?(h*p).toFixed(1):Math.round(h*p)).toLocaleString('tr-TR')+(b.dataset.son||'');"
            "if(p<1)requestAnimationFrame(a)}b.textContent='0'+(b.dataset.son||'');requestAnimationFrame(a)}"
            "if(!window.IntersectionObserver){ns.forEach(say);return}"
            "var io=new IntersectionObserver(function(x){x.forEach(function(y){if(y.isIntersecting){say(y.target);io.unobserve(y.target)}})},{threshold:.4});"
            "ns.forEach(function(b){io.observe(b)})})();</script>")

GIR_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
          "var ns=[].slice.call(e.querySelectorAll('.bkh-gir'));"
          "if(matchMedia('(prefers-reduced-motion:reduce)').matches||!window.IntersectionObserver){"
          "ns.forEach(function(n){n.classList.add('ac')});return}"
          "var io=new IntersectionObserver(function(x){x.forEach(function(y){if(y.isIntersecting){"
          "y.target.classList.add('ac');io.unobserve(y.target)}})},{threshold:.2});"
          "ns.forEach(function(n){io.observe(n)})})();</script>")

OS_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
         "var r=e.querySelector('input'),b=e.querySelector('.bkh-os-b'),c=e.querySelector('.bkh-os-c');"
         "function u(){var p=+r.value;b.style.width=p+'%';c.style.left=p+'%'}"
         "r.addEventListener('input',u);u()})();</script>")

ILERLEME_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
               "var i=e.querySelector('i');function u(){var h=document.documentElement;"
               "var m=h.scrollHeight-h.clientHeight;var p=m>0?Math.round(h.scrollTop/m*100):0;"
               "i.style.width=p+'%';e.setAttribute('aria-valuenow',p)}"
               "addEventListener('scroll',u,{passive:true});u()})();</script>")

KAY_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;" + _AZ +
          "var p=false;e.addEventListener('mouseenter',function(){p=true});e.addEventListener('mouseleave',function(){p=false});"
          "e.addEventListener('focusin',function(){p=true});"
          "setInterval(function(){if(p)return;if(e.scrollLeft+e.clientWidth>=e.scrollWidth-1)e.scrollLeft=0;else e.scrollLeft+=1},30)})();</script>")

BUYUT_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
            "var o=null;function kapat(){if(o){o.remove();o=null;document.removeEventListener('keydown',esc)}}"
            "function esc(ev){if(ev.key==='Escape')kapat()}"
            "e.addEventListener('click',function(ev){var b=ev.target.closest('[data-buyut]');if(!b)return;"
            "kapat();o=document.createElement('div');o.className='bkh-buyut';o.setAttribute('role','dialog');"
            "o.setAttribute('aria-label','Büyütülmüş fotoğraf');o.innerHTML='<img src=\"'+b.dataset.buyut+'\" alt=\"\">"
            "<button type=\"button\" aria-label=\"Kapat\">\\u00d7</button>';"
            "document.body.appendChild(o);o.querySelector('button').focus();"
            "o.addEventListener('click',kapat);document.addEventListener('keydown',esc)})})();</script>")

D360_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
           "var im=[].slice.call(e.querySelectorAll('img'));if(im.length<2)return;var i=0,x0=null;"
           "function g(k){im[i].hidden=true;i=(k+im.length)%im.length;im[i].hidden=false}"
           "function s(x){if(x0===null){x0=x;return}var dx=x-x0;if(Math.abs(dx)>14){g(i+(dx>0?1:-1));x0=x}}"
           "e.addEventListener('pointerdown',function(ev){x0=ev.clientX});"
           "e.addEventListener('pointermove',function(ev){if(x0!==null&&ev.buttons)s(ev.clientX)});"
           "addEventListener('pointerup',function(){x0=null});"
           "e.addEventListener('keydown',function(ev){if(ev.key==='ArrowRight')g(i+1);else if(ev.key==='ArrowLeft')g(i-1)})})();</script>")

CSS = (
    ".bkh-kayan{overflow:hidden;background:var(--bk-bg,var(--dk));color:var(--bk-fg,#fff);padding:12px 0}"
    ".bkh-ks{display:flex;width:max-content}"
    ".bkh-kp{display:flex;gap:18px;align-items:center;padding-right:18px;white-space:nowrap;"
    "animation:bkh-kay var(--sure,30s) linear infinite;font-weight:700}"
    ".bkh-kp i{opacity:.5;font-style:normal}"
    "@keyframes bkh-kay{from{transform:translateX(0)}to{transform:translateX(-100%)}}"
    ".bkh-kayan:hover .bkh-kp{animation-play-state:paused}"
    ".bkh-dk h2{font-size:clamp(24px,4vw,40px);margin:0 0 10px}"
    ".bkh-im{display:inline-block;width:2px;height:1em;background:currentColor;vertical-align:-2px;margin-left:3px;animation:bkh-yp 1s step-end infinite}"
    "@keyframes bkh-yp{50%{opacity:0}}"
    ".bkh-sy{text-align:center}.bkh-sy b{display:block;font-size:clamp(28px,4.6vw,46px);font-weight:800;color:var(--ac);font-variant-numeric:tabular-nums}"
    ".bkh-sy span{font-size:15px;opacity:.78}"
    ".bkh-liste{list-style:none;margin:0;padding:0;display:grid;gap:11px}"
    ".bkh-liste li{background:#fff;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);padding:14px 17px;display:flex;gap:14px;align-items:baseline}"
    ".bkh-liste span{margin-left:auto;opacity:.75;font-size:15px}"
    ".bkh-gir{opacity:0;transform:translateY(14px);transition:opacity .5s var(--g,0ms),transform .5s var(--g,0ms)}"
    ".bkh-gir.ac{opacity:1;transform:none}"
    ".bkh-yp{display:grid;grid-template-columns:minmax(220px,1fr) 1.4fr;gap:30px;align-items:start}"
    ".bkh-yp-s{position:sticky;top:90px}"
    ".bkh-yp-k{background:#fff;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);padding:18px 20px;margin-bottom:14px}"
    ".bkh-yp-k b{display:block;font-size:17px;margin-bottom:4px}.bkh-yp-k p{margin:0;opacity:.78;font-size:15px}"
    "@media(max-width:820px){.bkh-yp{grid-template-columns:1fr}.bkh-yp-s{position:static}}"
    ".bkh-par{background-size:cover;background-position:center;background-attachment:fixed;color:#fff;padding:clamp(60px,10vw,130px) 0}"
    ".bkh-par.bkh-sbt{background-attachment:scroll}"
    ".bkh-par h2{font-size:clamp(24px,4vw,40px);margin:0 0 10px}"
    "@media(hover:none){.bkh-par{background-attachment:scroll}}"
    ".bkh-ls{overflow:hidden;display:flex;width:100%}"
    ".bkh-lp{display:flex;gap:40px;align-items:center;padding-right:40px;animation:bkh-kay var(--sure,30s) linear infinite}"
    ".bkh-lp img{height:38px;width:auto;object-fit:contain;opacity:.75;max-width:none}"
    ".bkh-ls:hover .bkh-lp{animation-play-state:paused}"
    ".bkh-dstl{display:grid;gap:14px}"
    ".bkh-dst{position:sticky;top:calc(90px + var(--i) * 12px);background:#fff;border:1px solid #e7e4dc;"
    "border-radius:var(--bk-r,12px);padding:22px 24px;box-shadow:0 -2px 14px rgba(10,20,34,.05)}"
    ".bkh-dst b{display:block;font-size:19px;margin-bottom:6px}.bkh-dst p{margin:0;opacity:.8}"
    "@media(max-width:700px){.bkh-dst{position:static}}"
    ".bkh-os{position:relative;overflow:hidden;border-radius:var(--bk-r,12px);line-height:0}"
    ".bkh-os img{width:100%;display:block}"
    ".bkh-os-b{position:absolute;inset:0;width:50%;overflow:hidden}"
    ".bkh-os-b img{width:100vw;max-width:none;height:100%;object-fit:cover}"
    ".bkh-os input{position:absolute;inset:auto 0 14px;width:calc(100% - 28px);margin:0 14px;z-index:2}"
    ".bkh-os-c{position:absolute;top:0;bottom:0;width:2px;background:#fff;left:50%;pointer-events:none}"
    ".bkh-ilr{position:fixed;top:0;left:0;right:0;height:3px;background:transparent;z-index:2147481000}"
    ".bkh-ilr i{display:block;height:100%;width:0;background:var(--ac);transition:width .1s linear}"
    ".bkh-yd{color:#e8a33d;letter-spacing:1px}"
    ".bkh-yr{margin:0;background:#fff;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);padding:18px 20px}"
    ".bkh-yr blockquote{margin:9px 0 10px;font-size:16px;line-height:1.65}"
    ".bkh-yr figcaption{font-size:14px;opacity:.72;font-weight:600}"
    ".bkh-yrs{display:flex;gap:14px;overflow-x:auto;scroll-snap-type:x mandatory}"
    ".bkh-yrs>.bkh-yr{flex:0 0 min(340px,82%);scroll-snap-align:start}"
    ".bkh-tek{max-width:660px;margin:0 auto;text-align:center}"
    ".bkh-tek blockquote{font-size:19px}"
    ".bkh-gz,.bkh-ozp{text-align:center;margin:0 0 20px}"
    ".bkh-gz b,.bkh-ozp b{display:block;font-size:40px;font-weight:800;color:var(--ac);line-height:1}"
    ".bkh-gz span,.bkh-ozp span{display:block;font-size:14px;opacity:.7;margin-top:4px}"
    ".bkh-oz{display:grid;grid-template-columns:200px 1fr;gap:26px;align-items:center;max-width:640px;margin:0 auto}"
    ".bkh-dgl{display:grid;gap:6px}"
    ".bkh-dg{display:grid;grid-template-columns:14px 1fr 34px;gap:9px;align-items:center;font-size:13.5px}"
    ".bkh-dg i{display:block;height:8px;background:#ece9e1;border-radius:4px;overflow:hidden}"
    ".bkh-dg b{display:block;height:100%;background:var(--ac)}"
    "@media(max-width:620px){.bkh-oz{grid-template-columns:1fr}}"
    ".bkh-lg{display:flex;flex-wrap:wrap;gap:26px;align-items:center;justify-content:center}"
    ".bkh-lg img{height:40px;width:auto;object-fit:contain;opacity:.78}"
    ".bkh-srt{display:grid;place-items:center;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);padding:10px;background:#fff}"
    ".bkh-srt img{max-height:90px;width:auto;object-fit:contain}"
    ".bkh-bs{list-style:none;margin:0;padding:0;display:grid;gap:1px;background:#e7e4dc;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);overflow:hidden}"
    ".bkh-bs li{background:#fff}.bkh-bs li>*,.bkh-bs li a{display:flex;gap:14px;padding:13px 16px;text-decoration:none;color:inherit;align-items:baseline}"
    ".bkh-bs span{margin-left:auto;opacity:.65;font-size:14px}"
    ".bkh-grl{display:flex;flex-wrap:wrap;gap:20px;justify-content:center;text-align:center}"
    ".bkh-gr{flex:1 1 170px}.bkh-gr b{display:block;font-size:15.5px}.bkh-gr span{font-size:13.5px;opacity:.75}"
    ".bkh-gl{padding:0;border:0;background:none;cursor:zoom-in;display:block;line-height:0;border-radius:var(--bk-r,12px);overflow:hidden}"
    ".bkh-gl img{width:100%;aspect-ratio:1/1;object-fit:cover;display:block}"
    ".bkh-buyut{position:fixed;inset:0;background:rgba(8,14,24,.88);z-index:2147482500;display:grid;place-items:center;padding:24px;cursor:zoom-out}"
    ".bkh-buyut img{max-width:100%;max-height:90vh;object-fit:contain;border-radius:8px}"
    ".bkh-buyut button{position:absolute;top:14px;right:18px;border:0;background:none;color:#fff;font-size:30px;cursor:pointer;line-height:1}"
    ".bkh-gks{display:flex;gap:12px;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:6px}"
    ".bkh-gks img{flex:0 0 min(320px,76%);aspect-ratio:4/3;object-fit:cover;border-radius:var(--bk-r,12px);scroll-snap-align:start}"
    ".bkh-ms{column-count:var(--c,4);column-gap:12px}"
    ".bkh-ms img{width:100%;display:block;margin:0 0 12px;border-radius:var(--bk-r,12px);break-inside:avoid}"
    "@media(max-width:860px){.bkh-ms{column-count:2}}"
    "@media(max-width:560px){.bkh-ms{column-count:var(--cm,1)}}"
    ".bkh-ig{display:block;line-height:0;border-radius:var(--bk-r,12px);overflow:hidden}"
    ".bkh-ig img{width:100%;aspect-ratio:1/1;object-fit:cover}"
    ".bkh-vg,.bkh-vy{margin:0}.bkh-vg figcaption,.bkh-vy figcaption{font-size:14.5px;margin-top:8px;font-weight:600}"
    ".bkh-360{position:relative;cursor:ew-resize;border-radius:var(--bk-r,12px);overflow:hidden;line-height:0;touch-action:pan-y}"
    ".bkh-360 img{width:100%;display:block}"
    ".bkh-360i{position:absolute;left:50%;bottom:12px;transform:translateX(-50%);background:rgba(8,14,24,.6);"
    "color:#fff;font-size:12.5px;padding:5px 12px;border-radius:999px;line-height:1.4}"
    ".bkh-tg{padding:0;position:relative;line-height:0}"
    ".bkh-tg img{width:100%;max-height:70vh;object-fit:cover;display:block}"
    ".bkh-tgy{position:absolute;inset:auto 0 0 0;padding:40px 0 24px;line-height:1.5;color:#fff;"
    "background:linear-gradient(transparent,rgba(8,14,24,.75))}"
    ".bkh-tgy h2{margin:0 0 6px;font-size:clamp(22px,3.4vw,34px)}.bkh-tgy p{margin:0;opacity:.9}"
    ".bkh-rz{display:grid;grid-template-columns:1fr 1fr;gap:34px;align-items:center}"
    ".bkh-rz img{width:100%;border-radius:var(--bk-r,12px);object-fit:cover}"
    ".bkh-rz h2{font-size:clamp(23px,3.2vw,32px);margin:0 0 12px}"
    ".bkh-rz-s img{order:2}"
    "@media(max-width:780px){.bkh-rz{grid-template-columns:1fr;gap:20px}.bkh-rz-s img{order:0}}"
    "@media(prefers-reduced-motion:reduce){.bkh-kp,.bkh-lp{animation:none}.bkh-gir{opacity:1;transform:none}"
    ".bkh-im{animation:none}}"
)
