# -*- coding: utf-8 -*-
"""Dönüşüm, içerik ve bilgi bölümleri — her bölümün kendi üreticisi.

Form bölümlerinde ortak kural: her alanın görünür etiketi var, zorunlu alanlar işaretli,
KVKK onayı istendiğinde gönderim ona bağlı. Yasal metinler ve adres işletmenin kendi
ayarlarından gelir; uydurulmaz.
"""
import html as _h
import re

from blokgen import E, v, lines, img_url, link, para, sec, _head, _cta, _cols, _grid, _n, _style, _card

KAYIT = {}
GUNLER = ("Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar")


def kayit(bid):
    def sar(fn):
        KAYIT[bid] = fn
        return fn
    return sar


def _yok(b, dev):
    return sec(b, _head(b, dev, True), dev) if v(b, "title", dev, "") else ""


def _alan(ad, et, tip="text", zorunlu=True, iid="", satir=False, ek=""):
    kid = "f-%s-%s" % (iid, ad)
    if satir:
        gir = '<textarea id="%s" name="%s" rows="4" maxlength="2000"%s></textarea>' % (E(kid), E(ad), " required" if zorunlu else "")
    else:
        gir = '<input id="%s" name="%s" type="%s" maxlength="120"%s%s>' % (
            E(kid), E(ad), E(tip), " required" if zorunlu else "", ek)
    return '<label class="f2"><span>%s%s</span>%s</label>' % (
        E(et), '<i aria-hidden="true"> *</i>' if zorunlu else "", gir)


def _kvkk(b, dev, iid):
    if not v(b, "kvkk", dev, True):
        return ""
    return ('<label class="bkd-kv"><input type="checkbox" name="kvkk" value="1" required id="k-%s">'
            '<span><a href="/gizlilik-kvkk" target="_blank" rel="noopener">Aydınlatma metnini</a> '
            "okudum, iletişim kurulmasına izin veriyorum.</span></label>") % E(iid)


def _form(b, dev, alanlar, eylem, buton, kvkk_html="", basla=""):
    return ('<div class="bkd-fk">%s%s<form class="bkd-f" method="post" action="%s">%s%s'
            '<button class="bk-btn" type="submit">%s</button></form>%s</div>') % (
        ("<h2>%s</h2>" % E(str(v(b, "title", dev, "")))) if v(b, "title", dev, "") else "",
        ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "",
        E(eylem), "".join(alanlar), kvkk_html, E(buton), basla)


# ---------------------------------------------------------------- dönüşüm
@kayit("cta_serit")
def cta_serit(b, dev, d):
    """Çağrı şeridi: dikkat çeken bant, tek düğme."""
    t, s = v(b, "title", dev, ""), v(b, "sub", dev, "")
    if not (t or s):
        return ""
    return sec(b, '<div class="bkd-cta">%s%s%s</div>' % (
        ("<h2>%s</h2>" % E(str(t))) if t else "",
        ("<p>%s</p>" % E(str(s))) if s else "", _cta(b, dev)), dev)


@kayit("randevu_form")
def randevu_form(b, dev, d):
    """Gömülü randevu formu: hizmet ve kişi listesi panelden gelir."""
    hz = d.get("hizmetler") or []
    ek = d.get("ekip") or []
    sec_hz = ""
    if hz:
        sec_hz = ('<label class="f2"><span>Hizmet<i aria-hidden="true"> *</i></span>'
                  '<select name="hizmet" required>%s</select></label>') % "".join(
            '<option value="%s">%s%s</option>' % (E(str(x.get("name") or "")), E(str(x.get("name") or "")),
                                                  (" · %s ₺" % para(x["price"])) if x.get("price") else "") for x in hz[:60])
    sec_ek = ""
    if ek:
        sec_ek = ('<label class="f2"><span>Kiminle</span><select name="kisi">'
                  '<option value="">Fark etmez</option>%s</select></label>') % "".join(
            '<option value="%s">%s</option>' % (E(str(x.get("ad") or "")), E(str(x.get("ad") or ""))) for x in ek[:40])
    al = [sec_hz, sec_ek,
          _alan("tarih", "Tarih", "date", True, b["iid"]),
          _alan("ad", "Adınız", "text", True, b["iid"]),
          _alan("tel", "Telefon", "tel", True, b["iid"])]
    return sec(b, _form(b, dev, [x for x in al if x], "/api/public/yp/randevu",
                        str(v(b, "cta", dev, "") or "Randevu al")), dev)


@kayit("iletisim_form")
def iletisim_form(b, dev, d):
    """İletişim formu: ek alanlar işletmenin yazdığı satırlardan kurulur."""
    al = [_alan("ad", "Adınız", "text", True, b["iid"]),
          _alan("tel", "Telefon", "tel", True, b["iid"]),
          _alan("eposta", "E-posta", "email", False, b["iid"])]
    for x in lines(v(b, "fields", dev, ""), 1)[:6]:
        al.append(_alan("ek_" + re.sub(r"\W+", "_", x[0]).strip("_").lower()[:20] or "ek", x[0], "text", False, b["iid"]))
    al.append(_alan("mesaj", "Mesajınız", "text", True, b["iid"], satir=True))
    return sec(b, _form(b, dev, al, "/api/public/yp/iletisim",
                        str(v(b, "cta", dev, "") or "Gönder"), _kvkk(b, dev, b["iid"])), dev)


@kayit("geri_arama")
def geri_arama(b, dev, d):
    """Geri arama talebi: yalnız ad ve numara; kısa tutulur, dönüşüm düşmesin."""
    al = [_alan("ad", "Adınız", "text", True, b["iid"]),
          _alan("tel", "Telefon", "tel", True, b["iid"])]
    return sec(b, _form(b, dev, al, "/api/public/yp/geri-arama",
                        str(v(b, "cta", dev, "") or "Beni arayın"), _kvkk(b, dev, b["iid"])), dev)


@kayit("whatsapp")
def whatsapp(b, dev, d):
    """WhatsApp butonu: köşede sabit durur, numara ayarlardan gelir."""
    num = re.sub(r"\D", "", str(v(b, "num", dev, "") or (d.get("iletisim") or {}).get("whatsapp") or ""))
    if not num:
        return ""
    msg = str(v(b, "msg", dev, "") or "")
    sag = str(v(b, "pos", dev, "sağ alt")) != "sol alt"
    return ('<a class="bkd-wa%s" href="https://wa.me/%s%s" target="_blank" rel="noopener" '
            'aria-label="WhatsApp ile yazın">'
            '<svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
            '<path d="M12 2a10 10 0 00-8.6 15l-1.3 4.7 4.8-1.3A10 10 0 1012 2zm0 2a8 8 0 110 16 8 8 0 01-4.1-1.1l-.3-.2-2.4.6.6-2.3-.2-.3A8 8 0 0112 4zm-3 4c-.2 0-.5.1-.7.4-.3.3-.9.9-.9 2.1s.9 2.4 1 2.6c.1.2 1.7 2.8 4.3 3.8 2.1.8 2.6.7 3 .6.5 0 1.5-.6 1.7-1.2.2-.6.2-1.1.1-1.2 0-.1-.2-.2-.5-.3l-1.6-.8c-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1-.2-.1-1-.4-1.9-1.2-.7-.6-1.2-1.4-1.3-1.6-.1-.2 0-.4.1-.5l.4-.5.3-.5v-.5l-.7-1.7c-.2-.4-.4-.4-.5-.4h-.5z"/></svg>'
            "</a>") % (" bkd-wa-sol" if not sag else "", E(num), ("?text=" + _h.escape(msg, quote=True).replace(" ", "%20")) if msg else "")


@kayit("bulten")
def bulten(b, dev, d):
    """Bülten kaydı: KVKK onayı açıkken gönderim ona bağlanır."""
    al = [_alan("eposta", "E-posta adresiniz", "email", True, b["iid"])]
    return sec(b, _form(b, dev, al, "/api/public/yp/bulten",
                        str(v(b, "cta", dev, "") or "Kaydol"), _kvkk(b, dev, b["iid"])), dev)


@kayit("popup")
def popup(b, dev, d):
    """Açılır pencere: ne zaman açılacağı seçilir, bir kez gösterilebilir."""
    t = v(b, "title", dev, "") or (d.get("duyuru") or "")
    if not t:
        return ""
    ne = {"hemen": "0", "5 sn sonra": "5000", "sayfa yarısında": "yari", "çıkarken": "cikis"}.get(
        str(v(b, "when", dev, "5 sn sonra")), "5000")
    im = v(b, "img", dev, "")
    return ('<div class="bkd-pop" id="p-%s" hidden role="dialog" aria-modal="true" aria-label="%s" '
            'data-ne="%s" data-bir="%s"><div class="bkd-pop-i">%s'
            '<h2>%s</h2>%s%s<button class="bkd-pop-x" type="button" aria-label="Kapat">×</button>'
            "</div></div>%s") % (
        E(b["iid"]), E(str(t)), E(ne), "1" if v(b, "once", dev, True) else "",
        ('<img src="%s" alt="" loading="lazy">' % E(img_url(im))) if im else "",
        E(str(t)), ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "",
        _cta(b, dev), POP_JS)


@kayit("gerisayim")
def gerisayim(b, dev, d):
    """Geri sayım: kampanya bitimine kalan süre; süre dolunca bölüm kendini gizler."""
    bit = str(v(b, "end", dev, "") or "")
    t = v(b, "title", dev, "")
    if not bit or not t:
        return ""
    return sec(b, '<div class="bkd-gs" data-bit="%s"><div><h2>%s</h2>%s</div>'
               '<div class="bkd-gsk" role="timer" aria-live="off">'
               '<span data-s="g">00</span><i>gün</i><span data-s="s">00</span><i>saat</i>'
               '<span data-s="d">00</span><i>dk</i><span data-s="sn">00</span><i>sn</i></div>%s</div>%s' % (
                   E(bit), E(str(t)), ("<p>%s</p>" % E(str(v(b, "sub", dev, "")))) if v(b, "sub", dev, "") else "",
                   _cta(b, dev), GS_JS), dev)


# ---------------------------------------------------------------- içerik
@kayit("blog")
def blog(b, dev, d):
    """Blog: son yazılar, tarihi ve özetiyle."""
    yz = d.get("yazilar") or []
    if not yz:
        return _yok(b, dev)
    c, cm = _cols(b, dev, 3)
    ks = []
    for x in yz[:_n(v(b, "count", dev, 6), 6)]:
        alt = ('<time datetime="%s">%s</time>' % (E(str(x.get("tarih") or "")), E(str(x.get("tarih_tr") or x.get("tarih") or "")))) if x.get("tarih") else ""
        ks.append(_card(x.get("img") or "", x.get("baslik") or "", x.get("ozet") or "",
                        link("/blog/" + str(x.get("slug") or "")) or "", alt))
    return sec(b, _head(b, dev, True) + _grid(ks, c, cm), dev)


@kayit("sss")
def sss(b, dev, d):
    """Sık sorulan sorular: açılır kapanır; istenirse içinde arama kutusu."""
    it = lines(v(b, "items", dev, ""), 2) or [(x.get("soru") or "", x.get("cevap") or "") for x in (d.get("sss") or [])]
    if not it:
        return _yok(b, dev)
    ks = "".join('<details data-ara="%s"><summary>%s</summary><div>%s</div></details>' % (
        _h.escape((str(x[0]) + " " + str(x[1])).lower(), quote=True), E(str(x[0])), E(str(x[1]))) for x in it[:40])
    ara = ""
    if v(b, "search", dev, False):
        ara = ('<label class="bk-sr" for="sa-%s">Soru ara</label>'
               '<input class="bkd-ara" id="sa-%s" type="search" placeholder="Soru ara">%s') % (
            E(b["iid"]), E(b["iid"]), SSS_JS)
    return sec(b, _head(b, dev) + '<div class="bkd-sss">%s<div class="bk-faq">%s</div></div>' % (ara, ks), dev)


@kayit("zaman")
def zaman(b, dev, d):
    """Zaman çizelgesi: tarih ve olay, çizgi üzerinde."""
    it = lines(v(b, "items", dev, ""), 3)
    if not it:
        return _yok(b, dev)
    ks = "".join('<li><span class="bkd-zt">%s</span><div><b>%s</b>%s</div></li>' % (
        E(x[0]), E(x[1]), ("<p>%s</p>" % E(x[2])) if len(x) > 2 and x[2] else "") for x in it[:20])
    return sec(b, _head(b, dev, True) + '<ol class="bkd-zaman">%s</ol>' % ks, dev)


@kayit("sekme")
def sekme(b, dev, d):
    """Sekmeli içerik: başlıklara ayrılmış; ilki açık gelir."""
    it = lines(v(b, "items", dev, ""), 2)
    if not it:
        return _yok(b, dev)
    ks = "".join('<details%s><summary>%s</summary><div>%s</div></details>' % (
        " open" if not i else "", E(x[0]), E(x[1])) for i, x in enumerate(it[:20]))
    return sec(b, _head(b, dev) + '<div class="bk-faq">%s</div>' % ks, dev)


@kayit("alinti")
def alinti(b, dev, d):
    """Alıntı: büyük puntolu cümle ve kaynağı."""
    t = v(b, "text", dev, "")
    if not t:
        return ""
    kim = v(b, "who", dev, "")
    return sec(b, '<figure class="bkd-al"><blockquote>%s</blockquote>%s</figure>' % (
        E(str(t)), ("<figcaption>%s</figcaption>" % E(str(kim))) if kim else ""), dev)


@kayit("dosya")
def dosya(b, dev, d):
    """İndirilebilir dosya: ad, tür ve boyutuyla; yeni sekmede açılır."""
    ds = d.get("dosyalar") or []
    it = v(b, "items", dev, []) or []
    if not ds and isinstance(it, list) and it:
        ds = [{"ad": "Dosya %d" % (i + 1), "url": x} for i, x in enumerate(it) if x]
    if not ds:
        return _yok(b, dev)
    ks = ""
    for x in ds[:20]:
        u = link(x.get("url") or "") or img_url(x.get("k") or "")
        if not u:
            continue
        tur = str(x.get("tur") or (u.rsplit(".", 1)[-1][:5] if "." in u else "")).upper()
        ks += ('<li><a href="%s" target="_blank" rel="noopener" download><b>%s</b>'
               '<span>%s%s</span></a></li>') % (
            E(u), E(str(x.get("ad") or "Dosya")), E(tur), (" · %s" % E(str(x.get("boyut")))) if x.get("boyut") else "")
    if not ks:
        return _yok(b, dev)
    return sec(b, _head(b, dev) + '<ul class="bkd-dosya">%s</ul>' % ks, dev)


@kayit("rehber")
def rehber(b, dev, d):
    """Adım adım rehber: numaralı anlatım."""
    it = lines(v(b, "items", dev, ""), 2)
    if not it:
        return _yok(b, dev)
    ks = "".join('<li><b>%s</b>%s</li>' % (E(x[0]), ("<p>%s</p>" % E(x[1])) if x[1] else "") for x in it[:20])
    return sec(b, _head(b, dev) + '<ol class="bkd-rehber">%s</ol>' % ks, dev)


@kayit("vaka")
def vaka(b, dev, d):
    """Vaka çalışması: sorun, yapılan, sonuç; fotoğrafla yan yana."""
    t, s, im = v(b, "title", dev, ""), v(b, "sub", dev, ""), v(b, "img", dev, "")
    if not (t or s):
        return ""
    sat = lines(s, 2)
    ic = "".join('<div class="bkd-vk-s"><b>%s</b>%s</div>' % (
        E(x[0]), ("<p>%s</p>" % E(x[1])) if len(x) > 1 and x[1] else "") for x in sat) if sat else ""
    gor = ('<img src="%s" alt="" loading="lazy">' % E(img_url(im))) if im else ""
    return sec(b, '<div class="bkd-vk">%s<div><h2>%s</h2>%s%s</div></div>' % (gor, E(str(t)), ic, _cta(b, dev)), dev)


# ---------------------------------------------------------------- bilgi
@kayit("harita")
def harita(b, dev, d):
    """Harita ve yol tarifi: adres ayarlardan gelir, yol tarifi bağlantısıyla."""
    ad = str(d.get("adres") or d.get("address") or "")
    if not ad:
        return ""
    z = max(1, min(_n(v(b, "zoom", dev, 15), 15), 20))
    q = _h.escape(re.sub(r"\s+", "+", ad), quote=True)
    return sec(b, _head(b, dev) + (
        '<div class="bkd-hr"><iframe src="https://www.google.com/maps?q=%s&z=%d&output=embed" '
        'title="Harita: %s" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>'
        '<p class="bkd-adr">%s · <a href="https://www.google.com/maps/dir/?api=1&destination=%s" '
        'target="_blank" rel="noopener">Yol tarifi al</a></p>') % (q, z, E(ad), E(ad), q), dev)


@kayit("saatler")
def saatler(b, dev, d):
    """Çalışma saatleri: bugünün satırı işaretlenir, açık/kapalı durumu yazılır."""
    st = d.get("saatler") or []
    if not st:
        return _yok(b, dev)
    bugun = d.get("bugun")
    ks = ""
    for i, x in enumerate(st[:7]):
        ad = str(x.get("gun") or (GUNLER[i] if i < 7 else ""))
        kapali = x.get("kapali") or not (x.get("ac") and x.get("kapa"))
        deg = "Kapalı" if kapali else "%s – %s" % (x.get("ac"), x.get("kapa"))
        bu = bugun is not None and i == bugun
        ks += '<li%s><b>%s%s</b><span%s>%s</span></li>' % (
            ' class="bkd-bugun"' if bu else "", E(ad),
            '<i class="bkd-bg">bugün</i>' if bu else "",
            ' class="bkd-kap"' if kapali else "", E(deg))
    simdi = ""
    if v(b, "now", dev, True) and d.get("acik_mi") is not None:
        simdi = '<p class="bkd-simdi %s">%s</p>' % (
            "bkd-ac" if d["acik_mi"] else "bkd-kp", "Şu anda açığız" if d["acik_mi"] else "Şu anda kapalıyız")
    return sec(b, _head(b, dev) + simdi + '<ul class="bkd-saat">%s</ul>' % ks, dev)


@kayit("subeler")
def subeler(b, dev, d):
    """Şubeler: her şube adresi, telefonu ve yol tarifiyle."""
    sb = d.get("subeler") or []
    if not sb:
        return _yok(b, dev)
    c, cm = _cols(b, dev, 3)
    ks = []
    for x in sb[:_n(v(b, "count", dev, 6), 6)]:
        ad = str(x.get("adres") or "")
        tel = re.sub(r"[^\d+]", "", str(x.get("tel") or ""))
        alt = []
        if x.get("tel"):
            alt.append('<a href="tel:%s">%s</a>' % (E(tel), E(str(x.get("tel")))))
        if ad:
            alt.append('<a href="https://www.google.com/maps/dir/?api=1&destination=%s" target="_blank" rel="noopener">Yol tarifi</a>'
                       % _h.escape(re.sub(r"\s+", "+", ad), quote=True))
        ks.append('<div class="bkd-sb"><h3>%s</h3>%s<div class="bkd-sb-l">%s</div></div>' % (
            E(str(x.get("ad") or "")), ("<p>%s</p>" % E(ad)) if ad else "", " · ".join(alt)))
    return sec(b, _head(b, dev, True) + _grid(ks, c, cm), dev)


@kayit("bolgeler")
def bolgeler(b, dev, d):
    """Hizmet bölgeleri: mahalle ve semt listesi; arama için okunur metin."""
    it = [x[0] for x in lines(v(b, "items", dev, ""), 1)] or list(d.get("bolgeler") or [])
    if not it:
        return _yok(b, dev)
    ks = "".join("<li>%s</li>" % E(str(x)) for x in it[:200])
    return sec(b, _head(b, dev) + '<ul class="bkd-bolge">%s</ul>' % ks, dev)


@kayit("iletisim_bilgi")
def iletisim_bilgi(b, dev, d):
    """İletişim bilgileri: telefon, e-posta, adres ve sosyal hesaplar."""
    il = d.get("iletisim") or {}
    sos = d.get("baglantilar") or {}
    sat = []
    if il.get("tel"):
        sat.append(('Telefon', '<a href="tel:%s">%s</a>' % (E(re.sub(r"[^\d+]", "", str(il["tel"]))), E(str(il["tel"])))))
    if il.get("eposta"):
        sat.append(("E-posta", '<a href="mailto:%s">%s</a>' % (E(str(il["eposta"])), E(str(il["eposta"])))))
    if il.get("adres"):
        sat.append(("Adres", E(str(il["adres"]))))
    for ad, u in list(sos.items())[:6]:
        if link(str(u)):
            sat.append((str(ad).capitalize(), '<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(str(u)), E(str(ad).capitalize()))))
    if not sat:
        return _yok(b, dev)
    ks = "".join("<li><b>%s</b><span>%s</span></li>" % (E(a), c) for a, c in sat)
    return sec(b, _head(b, dev) + '<ul class="bkd-ilt">%s</ul>' % ks, dev)


@kayit("kvkk")
def kvkk(b, dev, d):
    """KVKK ve politikalar: yalnız gerçekten var olan metinlere bağlantı verir."""
    return _yasal(b, dev, d, ("gizlilik-kvkk", "cerez-politikasi", "kullanim-kosullari"),
                  "Aydınlatma metni, çerez politikası ve kullanım koşulları")


@kayit("iade_kosul")
def iade_kosul(b, dev, d):
    """İade ve kargo koşulları: mesafeli satış metinlerine bağlantı."""
    return _yasal(b, dev, d, ("iade-kosullari", "mesafeli-satis", "teslimat-kargo"),
                  "İade, mesafeli satış ve teslimat koşulları")


def _yasal(b, dev, d, slugs, alt):
    var = {k: a for k, a in (d.get("yasal") or [])}
    sat = [(k, var[k]) for k in slugs if k in var]
    if not sat:
        return ""
    ks = "".join('<li><a href="/%s">%s</a></li>' % (E(k), E(a)) for k, a in sat)
    bas = _head(b, dev) or ('<div class="bk-h"><h2>%s</h2><p>%s</p></div>' % (
        E(str(v(b, "title", dev, "") or "Yasal metinler")), E(alt)))
    return sec(b, bas + '<ul class="bkd-yasal">%s</ul>' % ks, dev)


# ---------------------------------------------------------------- betikler
POP_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
          "var k='ok_pop_'+e.id,bir=e.dataset.bir==='1';"
          "try{if(bir&&localStorage.getItem(k)==='1')return}catch(x){}"
          "var g=false;function ac(){if(g)return;g=true;e.hidden=false;"
          "var b=e.querySelector('.bkd-pop-x');if(b)b.focus();"
          "try{if(bir)localStorage.setItem(k,'1')}catch(y){}}"
          "function kapat(){e.hidden=true;document.removeEventListener('keydown',esc)}"
          "function esc(ev){if(ev.key==='Escape')kapat()}"
          "e.addEventListener('click',function(ev){if(ev.target===e||ev.target.classList.contains('bkd-pop-x'))kapat()});"
          "document.addEventListener('keydown',esc);"
          "var n=e.dataset.ne;"
          "if(n==='cikis')document.addEventListener('mouseout',function(ev){if(!ev.relatedTarget&&ev.clientY<10)ac()});"
          "else if(n==='yari')addEventListener('scroll',function(){var h=document.documentElement;"
          "if(h.scrollTop>(h.scrollHeight-h.clientHeight)/2)ac()},{passive:true});"
          "else setTimeout(ac,parseInt(n,10)||0)})();</script>")

GS_JS = ("<script>(function(){var e=document.currentScript.previousElementSibling;if(!e)return;"
         "var w=e.querySelector('.bkd-gs')||e;var h=new Date(w.dataset.bit).getTime();if(isNaN(h))return;"
         "function p(n){return(n<10?'0':'')+n}function t(){var f=h-Date.now();"
         "if(f<=0){var s=e.closest('section');if(s)s.hidden=true;return}"
         "var g=Math.floor(f/86400000),sa=Math.floor(f/3600000)%24,d=Math.floor(f/60000)%60,sn=Math.floor(f/1000)%60;"
         "w.querySelector('[data-s=g]').textContent=p(g);w.querySelector('[data-s=s]').textContent=p(sa);"
         "w.querySelector('[data-s=d]').textContent=p(d);w.querySelector('[data-s=sn]').textContent=p(sn);"
         "setTimeout(t,1000)}t()})();</script>")

SSS_JS = ("<script>(function(){var i=document.currentScript.previousElementSibling;if(!i)return;"
          "var w=i.parentNode;i.addEventListener('input',function(){var q=i.value.trim().toLowerCase();"
          "[].forEach.call(w.querySelectorAll('details'),function(dd){"
          "dd.hidden=!!q&&(dd.dataset.ara||'').indexOf(q)<0})})})();</script>")

CSS = (
    ".bkd-cta{text-align:center;max-width:720px;margin:0 auto}"
    ".bkd-cta h2{font-size:clamp(23px,3.4vw,34px);margin:0 0 10px}"
    ".bkd-fk{max-width:620px;margin:0 auto}"
    ".bkd-f{display:grid;grid-template-columns:1fr 1fr;gap:13px;margin-top:16px}"
    ".bkd-f label.f2:last-of-type,.bkd-f textarea,.bkd-kv{grid-column:1/-1}"
    ".bkd-f button{grid-column:1/-1;justify-self:start}"
    ".bkd-f select{border:1px solid #d7d3c8;border-radius:10px;padding:11px 13px;font:16px inherit;min-height:46px;background:#fff}"
    ".bkd-f .f2 i{color:#b42318;font-style:normal}"
    ".bkd-kv{display:flex;gap:9px;align-items:flex-start;font-size:13.5px;line-height:1.5}"
    "@media(max-width:620px){.bkd-f{grid-template-columns:1fr}}"
    ".bkd-wa{position:fixed;right:18px;bottom:18px;z-index:2147481500;width:54px;height:54px;border-radius:50%;"
    "background:#25d366;color:#fff;display:grid;place-items:center;box-shadow:0 6px 18px rgba(8,14,24,.26)}"
    ".bkd-wa-sol{right:auto;left:18px}"
    ".bkd-pop{position:fixed;inset:0;background:rgba(8,14,24,.55);z-index:2147482200;display:grid;place-items:center;padding:20px}"
    ".bkd-pop[hidden]{display:none}"
    ".bkd-pop-i{position:relative;background:#fff;border-radius:16px;max-width:430px;overflow:hidden;text-align:center;padding-bottom:24px}"
    ".bkd-pop-i img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;margin-bottom:16px}"
    ".bkd-pop-i h2{margin:0 16px 8px;font-size:21px}.bkd-pop-i p{margin:0 20px 14px;opacity:.8}"
    ".bkd-pop-x{position:absolute;top:6px;right:12px;border:0;background:rgba(255,255,255,.85);border-radius:50%;"
    "width:32px;height:32px;font-size:22px;cursor:pointer;line-height:1;color:#475467}"
    ".bkd-gs{display:flex;gap:20px;align-items:center;justify-content:space-between;flex-wrap:wrap}"
    ".bkd-gs h2{margin:0 0 4px;font-size:clamp(20px,2.8vw,28px)}.bkd-gs p{margin:0;opacity:.8}"
    ".bkd-gsk{display:flex;gap:6px;align-items:baseline;font-variant-numeric:tabular-nums}"
    ".bkd-gsk span{background:var(--dk);color:#fff;border-radius:9px;padding:8px 11px;font-weight:800;font-size:21px}"
    ".bkd-gsk i{font-style:normal;opacity:.6;font-size:12.5px;margin-right:5px}"
    ".bkd-sss .bkd-ara{width:100%;min-height:46px;border:1px solid #d7d3c8;border-radius:10px;padding:0 13px;font:16px inherit;margin-bottom:12px}"
    ".bkd-zaman{list-style:none;margin:0;padding:0 0 0 26px;position:relative}"
    ".bkd-zaman:before{content:'';position:absolute;left:7px;top:6px;bottom:6px;width:2px;background:#e3e0d7}"
    ".bkd-zaman li{position:relative;padding:0 0 20px}"
    ".bkd-zaman li:before{content:'';position:absolute;left:-23px;top:7px;width:10px;height:10px;border-radius:50%;background:var(--ac)}"
    ".bkd-zt{display:block;font-size:13px;font-weight:700;color:var(--ac);letter-spacing:.03em}"
    ".bkd-zaman b{font-size:16.5px}.bkd-zaman p{margin:3px 0 0;opacity:.78;font-size:15px}"
    ".bkd-al{margin:0;max-width:760px;margin-inline:auto;text-align:center}"
    ".bkd-al blockquote{margin:0;font-size:clamp(20px,3vw,28px);line-height:1.5;font-family:var(--bk-fh,inherit)}"
    ".bkd-al figcaption{margin-top:12px;font-size:15px;opacity:.7;font-weight:600}"
    ".bkd-dosya{list-style:none;margin:0;padding:0;display:grid;gap:9px}"
    ".bkd-dosya a{display:flex;gap:12px;align-items:baseline;background:#fff;border:1px solid #e7e4dc;"
    "border-radius:var(--bk-r,12px);padding:13px 16px;text-decoration:none;color:inherit}"
    ".bkd-dosya a:hover{border-color:var(--ac)}.bkd-dosya span{margin-left:auto;font-size:13px;opacity:.65}"
    ".bkd-rehber{margin:0;padding-left:22px;display:grid;gap:12px}"
    ".bkd-rehber b{font-size:16.5px}.bkd-rehber p{margin:3px 0 0;opacity:.78;font-size:15px}"
    ".bkd-vk{display:grid;grid-template-columns:1fr 1fr;gap:34px;align-items:center}"
    ".bkd-vk img{width:100%;border-radius:var(--bk-r,12px);object-fit:cover}"
    ".bkd-vk-s{margin-bottom:12px}.bkd-vk-s b{display:block;font-size:15px;color:var(--ac)}"
    ".bkd-vk-s p{margin:2px 0 0}"
    "@media(max-width:780px){.bkd-vk{grid-template-columns:1fr;gap:20px}}"
    ".bkd-hr{position:relative;padding-top:42%;border-radius:var(--bk-r,12px);overflow:hidden;background:#eceae4}"
    ".bkd-hr iframe{position:absolute;inset:0;width:100%;height:100%;border:0}"
    ".bkd-adr{margin:12px 0 0;font-size:15px}"
    ".bkd-saat{list-style:none;margin:0;padding:0;display:grid;gap:1px;background:#e7e4dc;border:1px solid #e7e4dc;"
    "border-radius:var(--bk-r,12px);overflow:hidden;max-width:460px}"
    ".bkd-saat li{background:#fff;padding:11px 16px;display:flex;gap:12px}"
    ".bkd-saat li span{margin-left:auto;font-variant-numeric:tabular-nums}"
    ".bkd-bugun{background:#faf7ef!important;font-weight:700}"
    ".bkd-bg{font-style:normal;font-size:11px;font-weight:700;background:var(--ac);color:#fff;border-radius:999px;padding:1px 7px;margin-left:7px}"
    ".bkd-kap{opacity:.6}"
    ".bkd-simdi{margin:0 0 12px;font-weight:700}"
    ".bkd-ac{color:#16794a}.bkd-kp{color:#b42318}"
    ".bkd-sb{background:#fff;border:1px solid #e7e4dc;border-radius:var(--bk-r,12px);padding:17px 19px}"
    ".bkd-sb h3{margin:0 0 6px;font-size:17px}.bkd-sb p{margin:0 0 9px;font-size:15px;opacity:.8}"
    ".bkd-sb-l{font-size:14px}"
    ".bkd-bolge{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:8px}"
    ".bkd-bolge li{background:#fff;border:1px solid #e7e4dc;border-radius:999px;padding:6px 14px;font-size:14px}"
    ".bkd-ilt{list-style:none;margin:0;padding:0;display:grid;gap:1px;background:#e7e4dc;border:1px solid #e7e4dc;"
    "border-radius:var(--bk-r,12px);overflow:hidden;max-width:520px}"
    ".bkd-ilt li{background:#fff;padding:12px 16px;display:flex;gap:14px}"
    ".bkd-ilt span{margin-left:auto}"
    ".bkd-yasal{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:10px}"
    ".bkd-yasal a{background:#fff;border:1px solid #e7e4dc;border-radius:999px;padding:8px 16px;text-decoration:none;color:inherit;font-size:14.5px}"
    ".bkd-yasal a:hover{border-color:var(--ac)}"
)
