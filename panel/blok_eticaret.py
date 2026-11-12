# -*- coding: utf-8 -*-
"""E-ticaret bölümleri — her bölümün kendi üreticisi.

Bu bölümlerin alanları birbirine benzer ama davranışları ayrıdır: indirimli ürünler
indirim oranına göre sıralanır ve yüzde rozeti taşır, fırsat ürünleri sayaç gösterir,
tükenmek üzere olanlar kalan adedi yazar, son görüntülenenler ziyaretçinin kendi
tarayıcısından okunur. Bu yüzden ortak bir kalıba sıkıştırılmazlar.
"""
import html as _h
import json
import re

from blokgen import E, v, lines, img_url, link, para, sec, _head, _cta, _cols, _grid, _n

KAYIT = {}


def kayit(bid):
    def sar(fn):
        KAYIT[bid] = fn
        return fn
    return sar


# ---------------------------------------------------------------- ürün seçimi
def _sat(p):
    """Satış fiyatı."""
    s = float(p.get("sale_price") or 0)
    return s if s else float(p.get("price") or 0)


def _indirim(p):
    t = float(p.get("price") or 0)
    s = _sat(p)
    return round((t - s) / t * 100) if t and s < t else 0


def _stok(p):
    try:
        return int(p.get("stock") or 0)
    except (TypeError, ValueError):
        return 0


def _var(p):
    """Sitede gösterilecek mi."""
    if p.get("status") == "draft":
        return False
    ch = p.get("channels") or {}
    return ch.get("site", True) is not False


def sec_urun(b, dev, d, kural=None):
    """Bölümün kuralına göre ürünleri seçer. Her bölüm kendi varsayılan kuralını verir."""
    ur = [p for p in (d.get("urunler") or []) if _var(p)]
    kat = str(v(b, "cat", dev, "") or "").strip()
    if kat:
        ur = [p for p in ur if (p.get("cat") or "") == kat]
    k = str(v(b, "rule", dev, kural or "yeni") or kural or "yeni")
    satis = d.get("satis") or {}
    if k == "manuel":
        se = v(b, "items", dev, []) or []
        se = se if isinstance(se, list) else []
        sira = {str(x): i for i, x in enumerate(se)}
        ur = [p for p in ur if str(p.get("id") or p.get("slug")) in sira]
        ur.sort(key=lambda p: sira.get(str(p.get("id") or p.get("slug")), 999))
    elif k == "indirim":
        ur = [p for p in ur if _indirim(p) > 0]
        ur.sort(key=_indirim, reverse=True)
    elif k == "coksatan":
        ur.sort(key=lambda p: satis.get(str(p.get("id")), 0), reverse=True)
        ur = [p for p in ur if satis.get(str(p.get("id")), 0) > 0] or ur
    elif k == "yeni":
        ur.sort(key=lambda p: str(p.get("created_at") or ""), reverse=True)
    elif k == "stok_az":
        ur = [p for p in ur if p.get("track_stock", True) and 0 < _stok(p) <= max(_n(p.get("low_at"), 5), 1)]
        ur.sort(key=_stok)
    elif k == "kampanyali":
        ur = [p for p in ur if p.get("camp") or _indirim(p) > 0]
    elif k == "rastgele":
        ur = sorted(ur, key=lambda p: str(p.get("id") or ""))
    n = _n(v(b, "count", dev, 8), 8)
    return ur[:max(1, min(n, 48))]


def urun_yolu(p):
    return "/magaza/urun/" + str(p.get("slug") or p.get("id") or "")


def rozet_html(b, dev, d, p, ek=""):
    """Bölümün seçtiği rozetler + bölüme özel etiket."""
    se = v(b, "badges", dev, []) or []
    se = se if isinstance(se, list) else []
    tan = {x["id"]: x for x in (d.get("rozetler") or [])}
    out = []
    if ek:
        out.append('<span class="bke-rz bke-oz">%s</span>' % E(ek))
    for rid in se[:4]:
        r = tan.get(rid)
        if not r:
            continue
        gor = True
        if rid == "indirim":
            gor = _indirim(p) > 0
        elif rid == "yeni":
            gor = True
        elif rid in ("son_adet", "tukendi"):
            gor = 0 < _stok(p) <= 5 if rid == "son_adet" else _stok(p) <= 0
        if gor:
            out.append('<span class="bke-rz" style="background:%s">%s</span>' % (E(str(r.get("color") or "#1155cc")), E(str(r.get("name") or ""))))
    return ('<span class="bke-rzl">%s</span>' % "".join(out)) if out else ""


def urun_kart(b, dev, d, p, ek_rozet="", alt="", buyuk=False):
    """Ürün kartı. Alt satır ve rozet bölüme göre değişir."""
    im = (p.get("images") or [None])[0]
    t, s = float(p.get("price") or 0), _sat(p)
    fiyat = '<span class="bke-f">%s ₺</span>' % para(s)
    if s < t:
        fiyat = '<span class="bke-es">%s ₺</span>%s' % (para(t), fiyat)
    hover = " bke-hv" if v(b, "anim_hover", dev, True) else ""
    return ('<a class="bke-k%s%s" href="%s">%s%s<div class="bke-g"><h3>%s</h3><div class="bke-ff">%s</div>%s</div></a>') % (
        " bke-buyuk" if buyuk else "", hover, E(urun_yolu(p)),
        ('<img src="%s" alt="%s" loading="lazy">' % (E(img_url(im)), E(str(p.get("name") or "")))) if im else '<span class="bke-bos" aria-hidden="true"></span>',
        rozet_html(b, dev, d, p, ek_rozet),
        E(str(p.get("name") or "")), fiyat,
        ('<div class="bke-alt">%s</div>' % alt) if alt else "")


def hepsi_btn(b, dev):
    t, to = v(b, "all_text", dev, ""), link(v(b, "all_to", dev, ""))
    if not t:
        return ""
    return '<div class="bk-c" style="margin-top:20px"><a class="bk-btn" href="%s">%s</a></div>' % (E(to or "/magaza"), E(str(t)))


def izgara(b, dev, kartlar):
    c, cm = _cols(b, dev, 4)
    sinif = "bk-g bke-g" + (" bke-in" if v(b, "anim_in", dev, False) else "")
    return _grid(kartlar, c, cm, sinif)


def bos(b, dev):
    """Ürün yoksa: başlık varsa yalnız başlık, yoksa hiç."""
    return sec(b, _head(b, dev, True), dev) if v(b, "title", dev, "") else ""


# ---------------------------------------------------------------- bölümler
@kayit("v_indirim")
def v_indirim(b, dev, d):
    """İndirimli ürünler: indirim oranına göre sıralı, her kartta yüzde rozeti."""
    ur = sec_urun(b, dev, d, "indirim")
    if not ur:
        return bos(b, dev)
    ks = [urun_kart(b, dev, d, p, ek_rozet="%%%d" % _indirim(p) if _indirim(p) else "") for p in ur]
    return sec(b, _head(b, dev, True) + izgara(b, dev, ks) + hepsi_btn(b, dev), dev)


@kayit("v_firsat")
def v_firsat(b, dev, d):
    """Fırsat ürünleri: bitiş saatine kadar geri sayan sayaç."""
    ur = sec_urun(b, dev, d, "indirim")
    if not ur:
        return bos(b, dev)
    bit = str(v(b, "end", dev, "") or "")
    sayac = ""
    if bit:
        sayac = ('<div class="bke-sayac" data-bit="%s" role="timer" aria-live="off">'
                 '<span data-s="g">00</span><i>g</i><span data-s="s">00</span><i>s</i>'
                 '<span data-s="d">00</span><i>d</i><span data-s="sn">00</span></div>%s') % (E(bit), SAYAC_JS)
    ks = [urun_kart(b, dev, d, p, ek_rozet="FIRSAT") for p in ur]
    return sec(b, _head(b, dev, True) + sayac + izgara(b, dev, ks) + hepsi_btn(b, dev), dev)


@kayit("v_coksatan")
def v_coksatan(b, dev, d):
    """Çok satanlar: satış adedine göre sıralı, kartta sıra numarası.

    Henüz satış kaydı yoksa sıra numarası basılmaz: 1. sırada diye gösterilen ürün
    gerçekte en çok satan olmayabilir. O durumda ürünler yeniden eskiye listelenir.
    """
    ur = sec_urun(b, dev, d, "coksatan")
    if not ur:
        return bos(b, dev)
    satis = d.get("satis") or {}
    varsa = any(satis.get(str(p.get("id")), 0) > 0 for p in ur)
    ks = [urun_kart(b, dev, d, p, ek_rozet=("%d." % (i + 1)) if varsa and satis.get(str(p.get("id")), 0) > 0 else "")
          for i, p in enumerate(ur)]
    return sec(b, _head(b, dev, True) + izgara(b, dev, ks) + hepsi_btn(b, dev), dev)


@kayit("v_yeni")
def v_yeni(b, dev, d):
    """Yeni gelenler: en son eklenenler, YENİ rozeti."""
    ur = sec_urun(b, dev, d, "yeni")
    if not ur:
        return bos(b, dev)
    ks = [urun_kart(b, dev, d, p, ek_rozet="YENİ") for p in ur]
    return sec(b, _head(b, dev, True) + izgara(b, dev, ks) + hepsi_btn(b, dev), dev)


@kayit("v_secili")
def v_secili(b, dev, d):
    """Öne çıkanlar: işletmenin elle seçtiği ürünler, seçtiği sırayla."""
    ur = sec_urun(b, dev, d, "manuel")
    if not ur:
        return bos(b, dev)
    ks = [urun_kart(b, dev, d, p) for p in ur]
    return sec(b, _head(b, dev, True) + izgara(b, dev, ks) + hepsi_btn(b, dev), dev)


@kayit("v_kampanya")
def v_kampanya(b, dev, d):
    """Kampanyalı ürünler: kartın altında kampanyanın adı yazar."""
    ur = sec_urun(b, dev, d, "kampanyali")
    if not ur:
        return bos(b, dev)
    ks = [urun_kart(b, dev, d, p, ek_rozet="KAMPANYA",
                    alt=E(str(p.get("camp") or "")) if p.get("camp") else "") for p in ur]
    return sec(b, _head(b, dev, True) + izgara(b, dev, ks) + hepsi_btn(b, dev), dev)


@kayit("v_tukeniyor")
def v_tukeniyor(b, dev, d):
    """Tükenmek üzere: kalan adet yazılır, azalan sırada."""
    ur = sec_urun(b, dev, d, "stok_az")
    if not ur:
        return bos(b, dev)
    ks = [urun_kart(b, dev, d, p, ek_rozet="SON %d" % _stok(p),
                    alt="Son %d adet" % _stok(p)) for p in ur]
    return sec(b, _head(b, dev, True) + izgara(b, dev, ks) + hepsi_btn(b, dev), dev)


@kayit("v_birlikte")
def v_birlikte(b, dev, d):
    """Birlikte alınanlar: ürünler + arasında artı işareti, toplam fiyat."""
    ur = sec_urun(b, dev, d, "manuel")[:4]
    if len(ur) < 2:
        return bos(b, dev)
    ara = '<span class="bke-arti" aria-hidden="true">+</span>'
    ks = ara.join(urun_kart(b, dev, d, p) for p in ur)
    top = sum(_sat(p) for p in ur)
    return sec(b, _head(b, dev, True) + '<div class="bke-birlikte">%s</div>'
               '<div class="bk-c bke-top">Birlikte: <b>%s ₺</b></div>' % (ks, para(top)) + hepsi_btn(b, dev), dev)


@kayit("v_son_bakilan")
def v_son_bakilan(b, dev, d):
    """Son görüntülenenler: ziyaretçinin kendi tarayıcısından okunur, sunucuda tutulmaz."""
    if not v(b, "title", dev, ""):
        return ""
    return sec(b, _head(b, dev, True) + '<div class="bk-g bke-g" id="bke-son" style="--c:%d;--cm:%s" hidden></div>%s' % (
        _cols(b, dev, 4)[0], E(_cols(b, dev, 4)[1]), SON_JS), dev)


@kayit("v_serit")
def v_serit(b, dev, d):
    """Kaydırmalı ürün şeridi: yatay kayar, dokunarak sürüklenir."""
    ur = sec_urun(b, dev, d, "yeni")
    if not ur:
        return bos(b, dev)
    ks = "".join(urun_kart(b, dev, d, p) for p in ur)
    oto = ' data-oto="1"' if v(b, "anim_auto", dev, False) else ""
    return sec(b, _head(b, dev) + '<div class="bke-serit"%s role="region" aria-label="Ürün şeridi" tabindex="0">%s</div>%s' % (
        oto, ks, SERIT_JS if oto else "") + hepsi_btn(b, dev), dev)


@kayit("v_buyuk_kart")
def v_buyuk_kart(b, dev, d):
    """Bir büyük kart, yanında küçükler."""
    ur = sec_urun(b, dev, d, "indirim")
    if not ur:
        return bos(b, dev)
    bas, kalan = ur[0], ur[1:5]
    sag = "".join(urun_kart(b, dev, d, p) for p in kalan)
    return sec(b, _head(b, dev) + '<div class="bke-buyuk-d">%s<div class="bke-kucuk">%s</div></div>' % (
        urun_kart(b, dev, d, bas, buyuk=True), sag) + hepsi_btn(b, dev), dev)


@kayit("v_izgara")
def v_izgara(b, dev, d):
    """Izgara vitrin: sade, sütun sayısı işletmenin seçtiği kadar."""
    ur = sec_urun(b, dev, d, "yeni")
    if not ur:
        return bos(b, dev)
    ks = [urun_kart(b, dev, d, p) for p in ur]
    return sec(b, _head(b, dev, True) + izgara(b, dev, ks) + hepsi_btn(b, dev), dev)


@kayit("v_hizli_sepet")
def v_hizli_sepet(b, dev, d):
    """Sepete hızlı ekle: karttan çıkmadan sepete ekleme düğmesi."""
    ur = sec_urun(b, dev, d, "coksatan")
    if not ur:
        return bos(b, dev)
    ks = []
    for p in ur:
        tuk = p.get("track_stock", True) and _stok(p) <= 0
        dg = ('<button class="bke-sep" type="button" data-urun="%s"%s>%s</button>' % (
            E(str(p.get("id") or p.get("slug") or "")), " disabled" if tuk else "",
            "Tükendi" if tuk else "Sepete ekle"))
        ks.append(urun_kart(b, dev, d, p, alt=dg))
    return sec(b, _head(b, dev, True) + izgara(b, dev, ks) + SEPET_JS + hepsi_btn(b, dev), dev)


@kayit("v_kategori")
def v_kategori(b, dev, d):
    """Kategori vitrini: koleksiyon kapakları, kapak görseli kategorinin ilk ürününden."""
    kts = d.get("kategoriler") or []
    if not kts:
        return bos(b, dev)
    n = _n(v(b, "count", dev, 8), 8)
    c, cm = _cols(b, dev, 4)
    mod = str(v(b, "img_mode", dev, "ürün görseli"))
    ks = []
    for k in kts[:n]:
        im = k.get("img") if mod != "renk" else ""
        ic = ('<img src="%s" alt="%s" loading="lazy">' % (E(img_url(im)), E(str(k.get("ad") or "")))) if im else '<span class="bke-bos" aria-hidden="true"></span>'
        ks.append('<a class="bke-kat" href="/magaza?kat=%s">%s<span class="bke-kat-ad">%s<i>%d ürün</i></span></a>' % (
            _h.escape(str(k.get("ad") or ""), quote=True).replace(" ", "+"), ic,
            E(str(k.get("ad") or "")), int(k.get("n") or 0)))
    return sec(b, _head(b, dev, True) + _grid(ks, c, cm) + hepsi_btn(b, dev), dev)


@kayit("v_marka")
def v_marka(b, dev, d):
    """Marka vitrini: sattığınız markalar, ürünü olanlar."""
    mk = d.get("markalar") or []
    if not mk:
        return bos(b, dev)
    ks = "".join('<a class="bke-mk" href="/magaza?marka=%s">%s</a>' % (
        _h.escape(str(m.get("ad") or ""), quote=True).replace(" ", "+"), E(str(m.get("ad") or ""))) for m in mk[:40])
    return sec(b, _head(b, dev, True) + '<div class="bke-mkl">%s</div>' % ks, dev)


@kayit("v_stok_haber")
def v_stok_haber(b, dev, d):
    """Stoğa gelince haber ver: tükenen üründe e-posta kaydı."""
    t = v(b, "title", dev, "") or "Stoğa gelince haber verelim"
    return sec(b, '<div class="bk-c">%s%s'
               '<form class="bk-form" method="post" action="/api/public/yp/stok-haber">'
               '<label class="bk-sr" for="sh-%s">E-posta adresiniz</label>'
               '<input id="sh-%s" name="email" type="email" required placeholder="E-posta adresiniz">'
               '<button type="submit">%s</button></form></div>' % (
                   "<h2>%s</h2>" % E(str(t)),
                   ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "",
                   E(b["iid"]), E(b["iid"]), E(str(v(b, "cta", dev, "") or "Haber ver"))), dev)


@kayit("guvence")
def guvence(b, dev, d):
    """Güvence şeridi: kargo, iade, güvenli ödeme sözleri."""
    it = lines(v(b, "items", dev, ""), 2)
    if not it:
        return ""
    ks = "".join('<div class="bke-gv"><b>%s</b>%s</div>' % (
        E(x[0]), ("<span>%s</span>" % E(x[1])) if x[1] else "") for x in it[:6])
    return sec(b, '<div class="bke-gvl">%s</div>' % ks, dev)


@kayit("odeme_logo")
def odeme_logo(b, dev, d):
    """Ödeme yöntemleri: bağlı sanal POS'tan gelen kart markaları."""
    ms = d.get("kartlar") or []
    if not ms:
        return ""
    ks = "".join('<span class="bke-kart">%s</span>' % E(str(m)) for m in ms[:10])
    return sec(b, '<div class="bke-gvl bke-odm">%s</div>' % ks, dev)


@kayit("taksit")
def taksit(b, dev, d):
    """Taksit tablosu: banka ve taksit seçenekleri."""
    tk = d.get("taksit") or []
    if not tk:
        return ""
    bas = "".join("<th>%s</th>" % E(str(x)) for x in (tk[0].get("ay") or []))
    sat = ""
    for r in tk[:12]:
        sat += "<tr><th scope=\"row\">%s</th>%s</tr>" % (
            E(str(r.get("banka") or "")), "".join("<td>%s ₺</td>" % para(x) for x in (r.get("tutar") or [])))
    return sec(b, _head(b, dev) + '<div class="bke-tbl"><table><caption class="bk-sr">Taksit seçenekleri</caption>'
               '<thead><tr><th scope="col">Banka</th>%s</tr></thead><tbody>%s</tbody></table></div>' % (bas, sat), dev)


@kayit("siparis_takip")
def siparis_takip(b, dev, d):
    """Sipariş takip: sipariş kodu ile kargo sorgulama."""
    return sec(b, '<div class="bk-c">%s%s'
               '<form class="bk-form" method="get" action="/siparis-takip">'
               '<label class="bk-sr" for="st-%s">Sipariş kodu</label>'
               '<input id="st-%s" name="kod" required placeholder="Sipariş kodunuz" autocomplete="off">'
               '<button type="submit">%s</button></form></div>' % (
                   "<h2>%s</h2>" % E(str(v(b, "title", dev, "") or "Siparişinizi takip edin")),
                   ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "",
                   E(b["iid"]), E(b["iid"]), E(str(v(b, "cta", dev, "") or "Sorgula"))), dev)


@kayit("uyelik")
def uyelik(b, dev, d):
    """Üyelik ve favoriler: giriş, kayıt ve açık olan ek özellikler."""
    ek = []
    if v(b, "fav", dev, True):
        ek.append("Favori listesi")
    if v(b, "wallet", dev, False):
        ek.append("Cüzdan ve puan")
    if v(b, "social", dev, False):
        ek.append("Google ile giriş")
    lst = ('<ul class="bke-uy">%s</ul>' % "".join("<li>%s</li>" % E(x) for x in ek)) if ek else ""
    return sec(b, '<div class="bk-c"><h2>%s</h2>%s%s'
               '<p><a class="bk-btn" href="/uye-girisi">Giriş yap</a> '
               '<a class="bk-btn bke-ikinci" href="/uye-kayit">Üye ol</a></p></div>' % (
                   E(str(v(b, "title", dev, "") or "Üye girişi")),
                   ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "", lst), dev)


@kayit("sepet_hatirlat")
def sepet_hatirlat(b, dev, d):
    """Sepet hatırlatma: sayfadan ayrılırken bir kez açılan pencere."""
    t = v(b, "title", dev, "")
    if not t:
        return ""
    return ('<div class="bke-hat" id="bke-hat" hidden role="dialog" aria-label="Sepetiniz">'
            '<div class="bke-hat-i"><h2>%s</h2>%s%s'
            '<button class="bke-hat-x" type="button" aria-label="Kapat">×</button></div></div>%s') % (
        E(str(t)), ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "",
        _cta(b, dev), HAT_JS)


# ---------------------------------------------------------------- küçük betikler
SAYAC_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
            "var s=new Date(e.getAttribute('data-bit')).getTime();if(isNaN(s))return;"
            "function p(n){return (n<10?'0':'')+n}"
            "function t(){var f=s-Date.now();if(f<0)f=0;"
            "var g=Math.floor(f/86400000),sa=Math.floor(f/3600000)%24,d=Math.floor(f/60000)%60,sn=Math.floor(f/1000)%60;"
            "e.querySelector('[data-s=g]').textContent=p(g);e.querySelector('[data-s=s]').textContent=p(sa);"
            "e.querySelector('[data-s=d]').textContent=p(d);e.querySelector('[data-s=sn]').textContent=p(sn);"
            "if(f>0)setTimeout(t,1000)}t()})();</script>")

SERIT_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
            "if(matchMedia('(prefers-reduced-motion:reduce)').matches)return;var d=1,p=false;"
            "e.addEventListener('mouseenter',function(){p=true});e.addEventListener('mouseleave',function(){p=false});"
            "e.addEventListener('focusin',function(){p=true});"
            "setInterval(function(){if(p)return;if(e.scrollLeft+e.clientWidth>=e.scrollWidth-1)e.scrollLeft=0;else e.scrollLeft+=d},30)})();</script>")

SON_JS = ("<script>(function(){var e=document.getElementById('bke-son');if(!e)return;"
          "var l=[];try{l=JSON.parse(localStorage.getItem('ok_son')||'[]')}catch(x){}"
          "if(!l.length)return;e.hidden=false;"
          "e.innerHTML=l.slice(0,8).map(function(p){return '<a class=\"bke-k\" href=\"'+p.u+'\">'"
          "+(p.i?'<img src=\"'+p.i+'\" alt=\"\" loading=\"lazy\">':'<span class=\"bke-bos\"></span>')"
          "+'<div class=\"bke-g\"><h3></h3><div class=\"bke-ff\"><span class=\"bke-f\"></span></div></div></a>'}).join('');"
          "Array.prototype.forEach.call(e.querySelectorAll('a'),function(a,i){a.querySelector('h3').textContent=l[i].a;"
          "a.querySelector('.bke-f').textContent=l[i].f})})();</script>")

SEPET_JS = ("<script>(function(){document.addEventListener('click',function(ev){"
            "var b=ev.target.closest('.bke-sep');if(!b)return;ev.preventDefault();"
            "if(b.disabled)return;var o=b.textContent;b.disabled=true;b.textContent='Eklendi';"
            "try{var c=JSON.parse(localStorage.getItem('ok_sepet')||'[]');c.push({u:b.dataset.urun,n:1});"
            "localStorage.setItem('ok_sepet',JSON.stringify(c))}catch(x){}"
            "setTimeout(function(){b.disabled=false;b.textContent=o},1800)})})();</script>")

HAT_JS = ("<script>(function(){var e=document.getElementById('bke-hat');if(!e)return;var g=false;"
          "function ac(){if(g)return;var c=[];try{c=JSON.parse(localStorage.getItem('ok_sepet')||'[]')}catch(x){}"
          "if(!c.length)return;g=true;e.hidden=false}"
          "document.addEventListener('mouseout',function(ev){if(!ev.relatedTarget&&ev.clientY<10)ac()});"
          "e.addEventListener('click',function(ev){if(ev.target===e||ev.target.classList.contains('bke-hat-x'))e.hidden=true})})();</script>")

CSS = (
    ".bke-g{align-items:stretch}"
    ".bke-k{position:relative;display:flex;flex-direction:column;background:#fff;border:1px solid #e7e4dc;"
    "border-radius:var(--bk-r,12px);overflow:hidden;text-decoration:none;color:inherit}"
    ".bke-k img,.bke-k .bke-bos{width:100%;aspect-ratio:1/1;object-fit:cover;display:block;background:#f1efe9}"
    ".bke-hv{transition:border-color .16s,box-shadow .16s,transform .16s}"
    ".bke-hv:hover{border-color:var(--ac);box-shadow:0 6px 20px rgba(10,20,34,.10);transform:translateY(-2px)}"
    ".bke-g2{padding:12px 13px;display:flex;flex-direction:column;gap:5px;flex:1}"
    ".bke-k .bke-g{padding:12px 13px;display:flex;flex-direction:column;gap:5px;flex:1}"
    ".bke-k h3{font-size:15px;margin:0;line-height:1.35;font-weight:600}"
    ".bke-ff{margin-top:auto;display:flex;gap:7px;align-items:baseline;flex-wrap:wrap}"
    ".bke-f{font-weight:800;font-size:17px;color:var(--dk)}"
    ".bke-es{text-decoration:line-through;opacity:.5;font-size:14px}"
    ".bke-alt{margin-top:7px}"
    ".bke-rzl{position:absolute;top:9px;left:9px;display:flex;flex-direction:column;gap:4px;align-items:flex-start;z-index:1}"
    ".bke-rz{background:#1155cc;color:#fff;font-size:11.5px;font-weight:800;padding:3px 8px;border-radius:999px;line-height:1.35}"
    ".bke-rz.bke-oz{background:var(--ac)}"
    ".bke-sep{width:100%;min-height:40px;border:1px solid var(--ac);background:#fff;color:var(--ac);"
    "border-radius:9px;font:700 14px inherit;cursor:pointer}"
    ".bke-sep:hover:not(:disabled){background:var(--ac);color:#fff}.bke-sep:disabled{opacity:.6;cursor:default}"
    ".bke-sayac{display:flex;gap:6px;align-items:baseline;justify-content:center;margin:0 0 20px;font-variant-numeric:tabular-nums}"
    ".bke-sayac span{background:var(--dk);color:#fff;border-radius:8px;padding:7px 10px;font-weight:800;font-size:19px}"
    ".bke-sayac i{font-style:normal;opacity:.6;font-size:13px;margin-right:3px}"
    ".bke-serit{display:flex;gap:14px;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:6px}"
    ".bke-serit>.bke-k{flex:0 0 220px;scroll-snap-align:start}"
    ".bke-serit:focus-visible{outline:2px solid var(--ac);outline-offset:3px}"
    ".bke-buyuk-d{display:grid;grid-template-columns:1.4fr 1fr;gap:16px}"
    ".bke-buyuk-d .bke-kucuk{display:grid;grid-template-columns:1fr 1fr;gap:14px}"
    ".bke-buyuk img,.bke-buyuk .bke-bos{aspect-ratio:4/3}"
    ".bke-buyuk h3{font-size:20px}"
    "@media(max-width:780px){.bke-buyuk-d{grid-template-columns:1fr}}"
    ".bke-birlikte{display:flex;gap:10px;align-items:center;justify-content:center;flex-wrap:wrap}"
    ".bke-birlikte>.bke-k{flex:0 1 200px}"
    ".bke-arti{font-size:22px;font-weight:700;opacity:.4}"
    ".bke-top{margin-top:16px;font-size:18px}"
    ".bke-kat{position:relative;display:block;border-radius:var(--bk-r,12px);overflow:hidden;text-decoration:none;color:#fff}"
    ".bke-kat img,.bke-kat .bke-bos{width:100%;aspect-ratio:3/2;object-fit:cover;display:block;background:#cfcabd}"
    ".bke-kat-ad{position:absolute;inset:auto 0 0 0;padding:26px 14px 12px;font-weight:700;"
    "background:linear-gradient(transparent,rgba(8,14,24,.72))}"
    ".bke-kat-ad i{display:block;font-style:normal;font-weight:500;font-size:13px;opacity:.85}"
    ".bke-mkl{display:flex;flex-wrap:wrap;gap:9px;justify-content:center}"
    ".bke-mk{border:1px solid #e7e4dc;border-radius:999px;padding:8px 16px;text-decoration:none;color:inherit;font-weight:600;font-size:15px;background:#fff}"
    ".bke-mk:hover{border-color:var(--ac)}"
    ".bke-gvl{display:flex;flex-wrap:wrap;gap:18px;justify-content:center;text-align:center}"
    ".bke-gv{flex:1 1 180px}.bke-gv b{display:block;font-size:15.5px}.bke-gv span{font-size:13.5px;opacity:.75}"
    ".bke-odm .bke-kart{border:1px solid #e7e4dc;border-radius:8px;padding:7px 14px;font-weight:700;font-size:13.5px;background:#fff}"
    ".bke-tbl{overflow-x:auto}.bke-tbl table{border-collapse:collapse;width:100%;font-size:15px;background:#fff}"
    ".bke-tbl th,.bke-tbl td{border:1px solid #e7e4dc;padding:9px 12px;text-align:right}"
    ".bke-tbl thead th,.bke-tbl tbody th{text-align:left;background:#faf9f6}"
    ".bke-uy{list-style:none;padding:0;margin:0 0 14px;display:flex;gap:16px;justify-content:center;flex-wrap:wrap;font-size:15px;opacity:.85}"
    ".bke-uy li:before{content:'✓';color:var(--ac);font-weight:800;margin-right:6px}"
    ".bke-ikinci{background:transparent;color:var(--ac);border:1.5px solid var(--ac)}"
    ".bke-hat{position:fixed;inset:0;background:rgba(8,14,24,.5);z-index:2147482000;display:grid;place-items:center;padding:20px}"
    ".bke-hat-i{position:relative;background:#fff;border-radius:16px;padding:26px 28px;max-width:420px;text-align:center}"
    ".bke-hat-x{position:absolute;top:8px;right:12px;border:0;background:none;font-size:24px;cursor:pointer;line-height:1;color:#667085}"
    "@media(prefers-reduced-motion:reduce){.bke-hv:hover{transform:none}}"
)
