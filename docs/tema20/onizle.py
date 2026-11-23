# -*- coding: utf-8 -*-
"""20 temanın fotoğraflı ana sayfa önizlemesi -> onizleme/NN.html + onizleme/index.html"""
import os, html, re
from pano import T, LBL
from foto import F, url, video
from icerik import C, SSS
from logo_ikon import IK
import logo_uret
E_ = html.escape
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "onizleme"); os.makedirs(OUT, exist_ok=True)
GF = {"Archivo": "Archivo:wght@500;700;800", "Inter": "Inter:wght@400;500;600;700", "Manrope": "Manrope:wght@400;600;700;800", "Barlow Condensed": "Barlow+Condensed:wght@600;700",
      "Barlow": "Barlow:wght@400;500;600", "Oswald": "Oswald:wght@500;600", "Nunito": "Nunito:wght@400;600;800", "Sora": "Sora:wght@500;600;700", "Figtree": "Figtree:wght@400;500;700",
      "Fraunces": "Fraunces:opsz,wght@9..144,500;9..144,700", "Cormorant": "Cormorant+Garamond:wght@500;600", "DM Serif": "DM+Serif+Display", "DM Sans": "DM+Sans:wght@400;500;700",
      "Fredoka": "Fredoka:wght@500;600", "Lora": "Lora:wght@500;600", "Newsreader": "Newsreader:opsz,wght@6..72,500", "Anton": "Anton", "Playfair": "Playfair+Display:wght@600;700",
      "Space Grotesk": "Space+Grotesk:wght@500;700"}
FAMN = {"Cormorant": "Cormorant Garamond", "DM Serif": "DM Serif Display", "Playfair": "Playfair Display"}
RAD = [10, 14, 4, 6, 18, 10, 2, 22, 14, 18, 16, 12, 4, 0, 20, 12, 10, 4, 8, 6]
CTA = {"servis": "Servis iste", "randevu": "Randevu al", "magaza": "Alışverişe başla", "yemek": "Rezervasyon", "proje": "İlanlara bak", "kurs": "Ön kayıt"}


# hero, nav, cards, head, foot, mode
SK = {1: ("poster", "classic", "rows", "num", "cols", "light"), 2: ("split", "pill", "nums", "left", "light", "tint"),
      3: ("giant", "overlay", "tiles", "split", "big", "dark"), 4: ("overlay", "overlay", "rows", "num", "cols", "dark"),
      5: ("arch", "centered", "img", "center", "light", "tint"), 6: ("tall", "classic", "tiles", "split", "cols", "light"),
      7: ("frame", "centered", "rows", "center", "big", "dark"), 8: ("arch", "pill", "img", "left", "light", "light"),
      9: ("frame", "classic", "img", "num", "light", "tint"), 10: ("bento", "pill", "tiles", "left", "big", "tint"),
      11: ("tall", "centered", "nums", "center", "light", "light"), 12: ("split", "centered", "rows", "left", "light", "light"),
      13: ("giant", "overlay", "tiles", "num", "big", "dark"), 14: ("bento", "centered", "img", "center", "cols", "light"),
      15: ("arch", "pill", "tiles", "center", "light", "tint"), 16: ("tall", "classic", "img", "left", "big", "tint"),
      17: ("frame", "pill", "nums", "split", "cols", "dark"), 18: ("overlay", "centered", "rows", "center", "big", "dark"),
      19: ("poster", "classic", "img", "split", "cols", "light"), 20: ("poster", "pill", "nums", "num", "big", "tint")}


def _rgb(h): return [int(h[k:k + 2], 16) for k in (1, 3, 5)]
def _hex(r): return "#%02x%02x%02x" % tuple(max(0, min(255, int(v))) for v in r)
def mix(a, b, t): return _hex([x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))])
def lum(h): r, g, b = _rgb(h); return (.299 * r + .587 * g + .114 * b) / 255


def page(i, t, c):
    nm, sec, fam, pal, fn, secs, pages, works, _ = t
    dk, ac, sf = pal
    fh, fb = [x.strip() for x in fn.split("/")]
    P = F[i]
    ph = lambda k, w=1200, h=None: url(P[k % len(P)], w, h)
    cta = CTA[fam]
    vsrc, vpos = video(i)
    vid = lambda cls='': '<video class="bgv %s" autoplay muted loop playsinline preload="metadata" poster="%s"><source src="%s" type="video/mp4"></video>' % (cls, vpos, vsrc)
    phone = "0532 000 00 00"
    _w = [x for x in re.split(r"[\s&]+", nm) if x and x[0].isalpha()]
    _ini = (_w[0][0] + _w[1][0]) if len(_w) > 1 else nm[:2]
    _shape = ["", "r", "h", "d"][(i + 1) % 4]
    logo = lambda w=False: logo_uret.make(i + 1, t, w).replace('height="72"', 'class="lgo"')
    fonts = "&".join("family=" + GF[f] for f in dict.fromkeys([fh, fb]) if f in GF)
    S = SK[i + 1]
    out = []

    def btn(t_, cls="p"):
        return '<a class="b %s" href="#iletisim">%s</a>' % (cls, E_(t_))

    def form(fields, b, dark=False):
        return '<form class="fm%s" onsubmit="event.preventDefault();this.querySelector(\'.ok\').hidden=false">%s<button class="b p">%s</button><p class="ok" hidden>Talebiniz alındı, 15 dakika içinde dönüyoruz.</p></form>' % (
            " dk" if dark else "", "".join('<label><span>%s</span><input placeholder="%s"></label>' % (E_(f), E_(f)) for f in fields), E_(b))

    def head(eyebrow, h2, p=""):
        return '<div class="hd %s"><h2>%s</h2>%s</div>' % (S[3], E_(h2), '<p>%s</p>' % E_(p) if p else "")

    def hero_html():
        f = c.get("form"); k = S[0]
        h1 = "<h1>%s</h1>" % E_(c["h1"]); sub = '<p class="lead">%s</p>' % E_(c["sub"])
        acts = '<div class="row">%s%s</div>' % (btn(cta), '<a class="b o" href="tel:+905320000000">%s</a>' % phone)
        fb = c.get("fbtn", cta)
        if k == "split":
            return '<section class="h h-split"><div class="w g2"><div class="htx in">%s%s%s</div><div class="hpic">%s%s</div></div></section>' % (h1, sub, acts, vid(), '<div class="fcard">%s</div>' % form(f, fb) if f else "")
        if k == "giant":
            return '<section class="h h-giant">%s<div class="shade b"></div><div class="w in">%s%s%s</div></section>' % (vid(), h1, sub, form(f, fb, True) if f else acts)
        if k == "arch":
            return '<section class="h h-arch"><div class="w g2"><div class="htx in">%s%s%s</div><div class="arch">%s</div></div></section>' % (h1, sub, form(f, fb) if f else acts, vid())
        if k == "bento":
            return '<section class="h h-bento"><div class="w bg"><div class="t1">%s<div class="shade b"></div><div class="tx in">%s%s%s</div></div><div class="t2"><img src="%s" alt=""></div><div class="t3"><img src="%s" alt=""></div><a class="t4" href="#iletisim"><b>%s</b><span>→</span></a></div></section>' % (vid(), h1, sub, acts, ph(1, 700, 700), ph(2, 700, 500), E_(cta))
        if k == "frame":
            return '<section class="h h-frame"><div class="w in ct">%s%s%s</div><div class="w"><div class="frm">%s</div>%s</div></section>' % (h1, sub, "" if f else acts, vid(), '<div class="fcard">%s</div>' % form(f, fb) if f else "")
        if k == "tall":
            return '<section class="h h-tall"><div class="w tl"><div class="tv">%s</div><div class="htx in">%s%s%s</div></div></section>' % (vid(), h1, sub, form(f, fb) if f else acts)
        if k == "poster":
            return '<section class="h h-poster"><div class="pt"><div class="pi in">%s%s%s</div></div><div class="pv">%s</div></section>' % (h1, sub, form(f, fb) if f else acts, vid())
        return '<section class="h h-over">%s<div class="shade"></div><div class="w in"><div class="oc">%s%s%s</div></div></section>' % (vid(), h1, sub, form(f, fb) if f else acts)

    for s in secs:
        code, label = s.split(":", 1)
        if code in ("hf", "hs", "hq", "hb", "hp"):
            out.append(hero_html())
        elif code == "__hf":
            f = c.get("form")
            out.append('<section class="hf">%s<div class="shade"></div><div class="w in"><span class="ey l">%s</span><h1>%s</h1><p class="lead">%s</p>%s</div></section>' % (
                vid(), E_(sec), E_(c["h1"]), E_(c["sub"]), form(f, c.get("fbtn", cta), True) if f else '<div class="row">%s%s</div>' % (btn(cta), btn("Menüyü gör" if fam == "yemek" else "Paketler", "o l"))))
        elif code in ("hs", "hq", "hb"):
            f = c.get("form")
            right = '<div class="hpic">%s<span class="live">● Canlı görüntü</span><div class="fcard">%s</div></div>' % (vid(), form(f, c.get("fbtn", cta))) if f else '<div class="hpic">%s</div>' % vid()
            out.append('<section class="hs"><div class="w g2"><div class="htx in"><span class="ey">%s</span><h1>%s</h1><p class="lead">%s</p><div class="row">%s%s</div><div class="trust"><b>★ 4.9</b> Google puanı · <b>Aynı gün</b> dönüş</div></div>%s</div></section>' % (
                E_(sec), E_(c["h1"]), E_(c["sub"]), btn(cta), '<a class="b o" href="tel:+905320000000">%s</a>' % phone, right))
        elif code == "hp":
            out.append('<section class="hp"><div class="w hpg"><a class="big">%s<div class="shade b"></div><div class="bt in"><span class="ey l">Yeni sezon</span><h1>%s</h1><p>%s</p><span class="b p">%s</span></div></a><a class="sm" style="background-image:linear-gradient(0deg,rgba(0,0,0,.55),transparent 70%%),url(%s)"><b>Çok satanlar</b><span>Keşfet →</span></a><a class="sm" style="background-image:linear-gradient(0deg,rgba(0,0,0,.55),transparent 70%%),url(%s)"><b>Kampanya</b><span>%%20 indirim →</span></a></div></section>' % (
                vid(), E_(c["h1"]), E_(c["sub"]), cta, ph(1, 700), ph(2, 700)))
        elif code == "br":
            bb = "".join("<b>%s</b>" % E_(b) for b in c.get("brands", []))
            out.append('<section class="br"><div class="w"><span>%s</span><div class="mq"><div class="mqi">%s%s</div></div></div></section>' % ("Servis verdiğimiz markalar" if fam == "servis" else "Çalıştığımız markalar", bb, bb))
        elif code in ("c3", "c4", "sv"):
            cards = c["cards"][:6 if code == "sv" else (3 if code == "c3" else 4)]
            out.append('<section class="sec"><div class="w">%s<div class="cards n%d k-%s">%s</div></div></section>' % (head(label.split("(")[0].strip().split(" + ")[0], {"servis": "Ne yapıyoruz?", "randevu": "Hizmetlerimiz", "kurs": "Kurslarımız"}.get(fam, "Hizmetler"), "Fiyatlar başlangıç fiyatıdır; kesin tutarı işe başlamadan söyleriz." if any(x[2] for x in cards) else ""), min(len(cards), 3 if len(cards) in (3, 6) else 4), S[2],
                "".join('<a class="card" href="#iletisim"><i class="no">%02d</i><img loading="lazy" src="%s" alt="%s"><div><h3>%s</h3><p>%s</p><div class="pr"><b>%s</b><span>%s →</span></div></div></a>' % (k + 1, ph(k + 1, 700, 480), E_(a), E_(a), E_(d), E_(p), cta) for k, (a, d, p) in enumerate(cards))))
        elif code == "pk":
            cards = c["cards"][:3]
            out.append('<section class="sec sf"><div class="w">%s<div class="pk">%s</div></div></section>' % (head("Paketler", "Size uygun paketi seçin"), "".join('<div class="pkc%s">%s<h3>%s</h3><p>%s</p><b class="pp">%s</b><ul><li>Online ödeme</li><li>SMS hatırlatma</li><li>Ücretsiz iptal</li></ul><a class="b %s" href="#iletisim">Satın al</a></div>' % (
                " on" if k == 1 else "", '<span class="tag">En çok tercih edilen</span>' if k == 1 else "", E_(a), E_(d), E_(p or "Teklif"), "p" if k == 1 else "o") for k, (a, d, p) in enumerate(cards))))
        elif code in ("cl", "qf", "tr"):
            tl = c.get("tool") or ("Hızlı talep", c.get("form", ["Ad soyad", "Telefon", "Not"]), c.get("fbtn", cta))
            if code == "qf" and c.get("form"):
                tl = ("Özel sipariş" if fam == "magaza" else "Hızlı talep", c["form"], c.get("fbtn", cta))
            out.append('<section class="tool"><div class="w"><div class="tb"><div><span class="ey l">%s</span><h2>%s</h2></div>%s</div></div></section>' % ("Online araç" if code == "cl" else ("Takip" if code == "tr" else "Hızlı talep"), E_(tl[0]), form(tl[1], tl[2], True)))
        elif code == "st":
            st = {"servis": ["Talebinizi bırakın", "15 dk içinde arıyoruz", "Usta kapınızda", "Ödeme ve garanti belgesi"], "randevu": ["Hizmeti seçin", "Saati ayırın", "SMS hatırlatma", "Gelin, hazırız"], "kurs": ["Ön kayıt", "Sağlık raporu ve evrak", "Teorik + direksiyon", "Sınav ve ehliyet"]}.get(fam, ["Seçin", "Onaylayın", "Takip edin", "Teslim"])
            out.append('<section class="sec"><div class="w">%s<ol class="st">%s</ol></div></section>' % (head("Süreç", "Nasıl çalışıyoruz?"), "".join("<li><b>%d</b><h3>%s</h3></li>" % (k + 1, E_(x)) for k, x in enumerate(st))))
        elif code == "nm":
            out.append('<section class="nm">%s<div class="shade"></div><div class="w">%s</div></section>' % (vid("dim"), "".join("<div class=\"rv1\"><b data-n=\"%s\">%s</b><span>%s</span></div>" % (E_(a), E_(a), E_(b)) for a, b in c.get("stats", [("12+", "yıl"), ("4.8", "puan"), ("3.000+", "müşteri"), ("7/24", "destek")]))))
        elif code in ("gl", "ba"):
            if code == "ba":
                out.append('<section class="sec"><div class="w">%s<div class="ba"><figure><img loading="lazy" src="%s" alt=""><figcaption>Önce</figcaption></figure><figure><img loading="lazy" src="%s" alt=""><figcaption>Sonra</figcaption></figure></div></div></section>' % (head("İşlerimiz", "Önce ve sonra"), ph(5, 900, 640), ph(6, 900, 640)))
            else:
                out.append('<section class="sec"><div class="w">%s<div class="gl">%s</div></div></section>' % (head("Galeri", "Bizden kareler"), "".join('<img src="%s" alt="">' % ph(k + 2, 800, 800) for k in range(5))))
        elif code == "tm":
            out.append('<section class="sec sf"><div class="w">%s<div class="tm">%s</div></div></section>' % (head("Ekip", "Uzmanlarımız", "Randevunuzu dilediğiniz uzmana alabilirsiniz."), "".join('<div><i>%s</i><h3>%s</h3><span>%s</span><a href="#iletisim">Randevu al →</a></div>' % (E_("".join(w[0] for w in p.split(" · ")[0].replace("Dt. ", "").replace("Dr. ", "").split()[:2])), E_(p.split(" · ")[0]), E_(p.split(" · ")[1] if " · " in p else "")) for p in c.get("team", ["Usta 1 · kesim", "Usta 2 · renk"]))))
        elif code == "rv":
            out.append('<section class="sec"><div class="w">%s<div class="rv sl1">%s</div><p class="note">Örnek yorumlar · firmanın kendi Google yorumları burada gösterilir.</p></div></section>' % (head("Yorumlar", "Müşterilerimiz ne diyor?"), "".join('<blockquote><span class="stars">★★★★★</span><p>%s</p><cite>%s</cite></blockquote>' % (E_(a), E_(b)) for a, b in [("Söylenen saatte geldiler, fiyatı başta söylediler. Çok memnun kaldık.", "A. K. · Google"), ("Randevu almak çok kolaydı, hatırlatma mesajı da geldi.", "S. T. · Google"), ("Temiz ve özenli iş. Tekrar tercih ederim.", "M. D. · Google")])))
        elif code == "fq":
            out.append('<section class="sec sf"><div class="w nar">%s%s</div></section>' % (head("SSS", "Sık sorulan sorular"), "".join("<details><summary>%s</summary><p>%s</p></details>" % (E_(q), E_(a)) for q, a in SSS.get(fam, SSS["servis"]))))
        elif code == "mp":
            out.append('<section class="sec" id="iletisim"><div class="w g2 mp"><div>%s<ul class="ct"><li><b>Adres</b>Atatürk Cad. No:12, Bornova / İzmir</li><li><b>Telefon</b><a href="tel:+905320000000">%s</a></li><li><b>Çalışma saatleri</b>Hafta içi 08:30–19:00 · Cumartesi 09:00–17:00</li></ul><div class="row">%s<a class="b o" href="#">WhatsApp</a></div></div><div class="map"><span>📍</span><b>%s</b><small>Harita · Google Maps</small></div></div></section>' % (
                head("İletişim", "Bize ulaşın"), phone, btn(cta), E_(nm)))
        elif code == "pr":
            prods = c.get("products") or [("Ürün", "250 ₺")] * 5
            out.append('<section class="sec"><div class="w">%s<div class="prg">%s</div></div></section>' % (head("Mağaza", "Çok satanlar" if fam == "magaza" else "Online mağaza", "Sepete ekleyin, kapınıza gelsin."), "".join(
                '<div class="pc"><img loading="lazy" src="%s" alt="%s"><h3>%s</h3><div><b>%s</b><button class="b p s" onclick="var x=document.getElementById(\'sbc\');x.textContent=+x.textContent+1">Sepete ekle</button></div></div>' % (ph(k + 3, 600, 720), E_(a), E_(a), E_(p)) for k, (a, p) in enumerate(prods))))
        elif code == "cat":
            out.append('<section class="sec"><div class="w">%s<div class="cat">%s</div></div></section>' % (head("Kategoriler", "Ne arıyorsunuz?"), "".join('<a style="background-image:linear-gradient(0deg,rgba(0,0,0,.55),transparent 60%%),url(%s)"><b>%s</b></a>' % (ph(k + 1, 600, 700), E_(a)) for k, (a, _, _) in enumerate(c["cards"][:5]))))
        elif code == "mn":
            tabs = c["menu"]
            out.append('<section class="sec sf" id="menu"><div class="w">%s<div class="mt">%s</div>%s</div></section>' % (head("Menü", "Menümüz", "Fiyatlar KDV dahildir. Paket siparişte aynı fiyat."), "".join('<button class="%s" onclick="document.querySelectorAll(\'.mp2\').forEach(function(x,j){x.hidden=j!=%d});document.querySelectorAll(\'.mt button\').forEach(function(x,j){x.className=j==%d?\'on\':\'\'})">%s</button>' % ("on" if k == 0 else "", k, k, E_(a)) for k, (a, _) in enumerate(tabs)),
                "".join('<div class="mp2"%s>%s</div>' % ("" if k == 0 else " hidden", "".join('<div class="mi"><img loading="lazy" src="%s" alt=""><div><h3>%s</h3><small>Günlük taze</small></div><b>%s</b><button class="b p s">Ekle</button></div>' % (ph(k * 3 + j, 300, 300), E_(n), E_(p)) for j, (n, p) in enumerate(items))) for k, (_, items) in enumerate(tabs))))
        elif code == "il":
            out.append('<section class="sec"><div class="w">%s<div class="prg">%s</div></div></section>' % (head("İlanlar", "Öne çıkan ilanlar"), "".join('<div class="pc il"><img loading="lazy" src="%s" alt=""><h3>%s</h3><div><b>%s</b><a class="b o s" href="#iletisim">Görüşme</a></div></div>' % (ph(k + 1, 700, 520), E_(a), E_(p)) for k, (a, p) in enumerate(c["listings"]))))
        elif code == "kr":
            days = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"]
            rows = [("09:00", ["Reformer", "", "Reformer", "", "Reformer", "Mat"]), ("12:30", ["Mat", "Fonksiyonel", "", "Fonksiyonel", "Mat", ""]), ("18:30", ["Reformer", "Reformer", "Fonksiyonel", "Reformer", "", "Reformer"]), ("20:00", ["Fonksiyonel", "Mat", "Reformer", "Mat", "Reformer", ""])] if fam != "kurs" else [("09:00", ["Teorik", "Direksiyon", "Teorik", "Direksiyon", "Teorik", "Direksiyon"]), ("14:00", ["Direksiyon", "Teorik", "Direksiyon", "Teorik", "Direksiyon", ""]), ("19:00", ["Teorik", "", "Teorik", "", "Teorik", ""])]
            out.append('<section class="sec sf"><div class="w">%s<div class="kr"><table><tr><th></th>%s</tr>%s</table></div></div></section>' % (head("Program", "Haftalık ders programı" if fam != "kurs" else "Dönem programı", "Kontenjanlı ders: dolu olanlara sıra kaydı yapılır."), "".join("<th>%s</th>" % d for d in days), "".join("<tr><td>%s</td>%s</tr>" % (h, "".join('<td>%s</td>' % ('<button class="sl">%s<small>%d yer</small></button>' % (x, (len(x) + j) % 5 + 1) if x else "") for j, x in enumerate(r))) for h, r in rows)))
        elif code == "bl":
            out.append('<section class="sec"><div class="w">%s<div class="cards n3">%s</div></div></section>' % (head("Blog", "Yazılar"), "".join('<a class="card" href="#"><img loading="lazy" src="%s" alt=""><div><h3>%s</h3><p>5 dk okuma</p></div></a>' % (ph(k + 4, 700, 480), E_(x)) for k, x in enumerate(["Başlarken bilmeniz gerekenler", "Sık yapılan 5 hata", "Uzmanından öneriler"]))))
        elif code == "cta":
            out.append('<section class="cta"><div class="w"><h2>%s</h2>%s</div></section>' % (E_({"servis": "Acil mi? Hemen arayın, ustamız yola çıksın.", "randevu": "Sevdiklerinize hediye çeki verin.", "magaza": "İlk siparişe %10 indirim: HOSGELDIN", "yemek": "15 kişi ve üzeri grup rezervasyonu için arayın."}.get(fam, "Bize hemen ulaşın.")), '<a class="b l" href="tel:+905320000000">%s</a>' % phone))
    if c.get("perks") and fam == "magaza":
        out.insert(3, '<section class="perk"><div class="w">%s</div></section>' % "".join("<div><b>%s</b><span>%s</span></div>" % (E_(a), E_(b)) for a, b in c["perks"]))

    navs = [p for p in pages if not p.startswith(("Sepet", "Ödeme", "Hesabım", "Yasal", "Ürün detay", "Hizmet detay", "Cihaz detay", "Uygulama detay", "Tedavi detay", "İlan detay"))][:5]
    shop = fam == "magaza" or any("mağaza" in w.lower() or "sepet" in w.lower() for w in works)
    items = [x[0] for x in c.get("cards", [])][:6]
    mega = '<div class="mega"><div class="w mg"><div><b>%s</b>%s</div><div><b>Hızlı erişim</b>%s</div><a class="mgp" style="background-image:linear-gradient(0deg,rgba(0,0,0,.6),transparent 60%%),url(%s)"><span>Kampanya</span><b>%s</b></a></div></div>' % (
        E_(navs[0].split(" (")[0]), "".join('<a href="#">%s</a>' % E_(x) for x in items), "".join('<a href="#">%s</a>' % E_(p.split(" (")[0]) for p in navs[1:]), ph(3, 600, 400), E_({"servis": "Kış öncesi bakımda %15 indirim", "randevu": "İlk randevuya özel %10", "magaza": "Sezon sonu indirimi", "yemek": "Hafta içi öğle menüsü"}.get(fam, "Bu ay ücretsiz danışmanlık")))
    drawer = '<div class="drw" id="drw"><div class="dh"><b>%s</b><button onclick="document.body.classList.remove(\'mo\')" aria-label="Kapat">✕</button></div>%s<a class="b p" href="#iletisim" onclick="document.body.classList.remove(\'mo\')">%s</a><a class="tl" href="tel:+905320000000">%s</a></div>' % (
        logo(True), "".join('<a href="#" onclick="document.body.classList.remove(\'mo\')">%s<span>›</span></a>' % E_(p.split(" (")[0]) for p in navs + ([] if any(x.startswith("İletişim") for x in navs) else ["İletişim"])), cta, phone)
    hdr = drawer + '<header class="top nv-' + S[1] + '"><div class="w"><button class="bur" onclick="document.body.classList.add(\'mo\')" aria-label="Menü"><i></i><i></i><i></i></button><a class="lg" href="#" aria-label="%s">%s</a><nav><span class="hasm">%s ▾%s</span>%s</nav><div class="hr">%s<a class="b p s" href="#iletisim">%s</a></div></div></header>' % (
        E_(nm), logo(S[5] == "dark" or S[1] == "overlay"), E_(navs[0].split(" (")[0]), mega, "".join('<a href="#">%s</a>' % E_(p.split(" (")[0]) for p in navs[1:]), '<a class="cart" href="#" aria-label="Sepet">Sepet <b id="sbc">0</b></a>' if shop else '<a class="tel" href="tel:+905320000000">%s</a>' % phone, cta)
    ftr = '<footer><div class="w fg"><div><b class="lg">%s</b><p>%s · %s</p></div><div><b>Sayfalar</b>%s</div><div><b>Kurumsal</b><a>Hakkımızda</a><a>KVKK</a><a>Çerez politikası</a>%s</div><div><b>İletişim</b><a>%s</a><a>Bornova / İzmir</a></div></div><div class="w cp">© 2026 %s · onlinekaydet ile yapıldı</div></footer>' % (
        logo(S[4] != "light"), E_(sec), E_(LBL[fam]), "".join("<a>%s</a>" % E_(p.split(" (")[0]) for p in pages[:6]), "<a>Mesafeli satış sözleşmesi</a><a>İade koşulları</a>" if shop else "", phone, E_(nm))
    ftr = ftr.replace("<footer>", '<footer class="f-%s">' % S[4], 1)
    if S[4] == "big":
        ftr = ftr.replace('<div class="w cp">', '<div class="w fgiant" aria-hidden="true">%s</div><div class="w cp">' % E_(nm), 1)
    ink_on_ac = "#111111" if lum(ac) > .6 else "#ffffff"
    if S[5] == "dark":
        bgc = mix(dk, "#000000", .55); cardc = mix(dk, "#ffffff", .07); sfc = mix(dk, "#000000", .3)
        modecss = ":root{--bg:%s;--card:%s;--sf:%s;--ink:#f2f3f5;--mut:#a9afb8;--ln:rgba(255,255,255,.14);}" % (bgc, cardc, sfc)
    else:
        modecss = ":root{--bg:%s;--card:#fff;--ink:#16181c}" % ("#ffffff" if S[5] == "light" else sf)
    modecss += ":root{--onac:%s}" % ink_on_ac
    mbar = '<div class="mb"><a href="tel:+905320000000">Ara</a><a href="#">WhatsApp</a><a class="p" href="#iletisim">%s</a></div>' % cta
    fhf, fbf = FAMN.get(fh, fh), FAMN.get(fb, fb)
    css = CSS.replace("--DK", dk).replace("--AC", ac).replace("--SF", sf).replace("--FH", "'%s'" % fhf).replace("--FB", "'%s'" % fbf).replace("--RR", "%dpx" % RAD[i])
    upper = "text-transform:uppercase;letter-spacing:.01em;" if fh in ("Oswald", "Anton", "Barlow Condensed") else ""
    return '<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s · %s</title><link rel="preconnect" href="https://fonts.gstatic.com"><link href="https://fonts.googleapis.com/css2?%s&display=swap" rel="stylesheet"><style>%s h1,h2{%s}</style></head><body data-mode="%s">%s<main>%s</main>%s%s<a class="back" href="index.html">← Tüm temalar</a><script>%s</script></body></html>' % (
        E_(nm), E_(sec), fonts, css + modecss + SKINCSS.replace("--FH", "'%s'" % fhf).replace("--FB", "'%s'" % fbf), upper, S[5], hdr, "".join(out), ftr, mbar, JS)


SKINCSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "skin.css.txt")).read()

CSS = """:root{--dk:--DK;--ac:--AC;--sf:--SF;--r:--RR;--ink:#16181c;--mut:#5d636c;--ln:rgba(0,0,0,.1)}
*{box-sizing:border-box;margin:0;padding:0}html{scroll-behavior:smooth}body{font:16px/1.6 --FB,system-ui,sans-serif;color:var(--ink);background:#fff;overflow-x:hidden;padding-bottom:0}
img{display:block;max-width:100%}a{color:inherit;text-decoration:none}.w{max-width:1200px;margin:0 auto;padding:0 20px}
h1,h2,h3{font-family:--FH,serif;line-height:1.1;color:var(--dk)}h1{font-size:clamp(34px,5vw,58px);font-weight:700}h2{font-size:clamp(26px,3.4vw,40px)}h3{font-size:19px;line-height:1.25}
.ey{display:inline-block;font-weight:700;font-size:13px;color:var(--ac);margin-bottom:12px}.ey.l{color:#fff;background:var(--ac);padding:4px 10px;border-radius:99px}
.lead{font-size:18px;color:var(--mut);margin:18px 0 26px;max-width:560px}.row{display:flex;gap:12px;flex-wrap:wrap}
.b{display:inline-flex;align-items:center;justify-content:center;min-height:50px;padding:0 24px;border-radius:var(--r);font-weight:700;font-size:15px;border:0;cursor:pointer;font-family:inherit;transition:transform .15s,box-shadow .15s}
.b:hover{transform:translateY(-2px);box-shadow:0 8px 20px -10px rgba(0,0,0,.4)}.b.p{background:var(--ac);color:#fff}.b.o{border:1.5px solid var(--ln);background:#fff;color:var(--ink)}.b.l{background:#fff;color:var(--dk)}.b.o.l{background:transparent;color:#fff;border-color:rgba(255,255,255,.6)}.b.s{min-height:40px;padding:0 16px;font-size:14px}
.top{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.94);backdrop-filter:blur(10px);border-bottom:1px solid var(--ln)}.top>.w{display:flex;align-items:center;gap:26px;height:72px}
.lg{font:700 22px --FH,serif;color:var(--dk)}.top nav{display:flex;align-items:center;gap:22px;font-weight:600;font-size:15px;color:#3b3f45}.top nav a:hover{color:var(--ac)}.hr{margin-left:auto;display:flex;align-items:center;gap:16px}.tel{font-weight:700;color:var(--dk)}
.cart{font-weight:700}.cart b{background:var(--ac);color:#fff;border-radius:99px;padding:1px 8px;font-size:13px;margin-left:4px}
.hf{min-height:600px;display:flex;align-items:center;background-size:cover;background-position:center;color:#fff;padding:80px 0}.hf h1{color:#fff;max-width:760px}.hf .lead{color:rgba(255,255,255,.88)}
.hs{background:var(--sf);padding:56px 0 64px}.g2{display:grid;grid-template-columns:1.05fr 1fr;gap:48px;align-items:center}.hpic{position:relative}.hpic img{width:100%;aspect-ratio:5/5.4;min-height:0;object-fit:cover;border-radius:calc(var(--r)*1.6)}
.fcard{position:absolute;left:-40px;right:30px;bottom:-30px;background:#fff;border-radius:var(--r);padding:18px;box-shadow:0 24px 50px -20px rgba(0,0,0,.35)}.trust{margin-top:22px;color:var(--mut);font-size:14px}.trust b{color:var(--dk)}
.fm{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;align-items:end}.fm label span{display:block;font-size:12px;font-weight:700;color:var(--mut);margin-bottom:4px}
.fm input{width:100%;min-height:48px;border:1.5px solid var(--ln);border-radius:calc(var(--r)*.7);padding:0 14px;font:inherit;font-size:15px;background:#fff}.fm .ok{grid-column:1/-1;color:#15803d;font-weight:700}
.fm.dk{max-width:900px;margin-top:26px}.fm.dk label span{color:rgba(255,255,255,.8)}.fm.dk input{border-color:transparent}
.hp{padding:20px 0}.hpg{display:grid;grid-template-columns:2fr 1fr;grid-template-rows:1fr 1fr;gap:14px;height:560px}.hpg a{background-size:cover;background-position:center;border-radius:var(--r);color:#fff;padding:28px;display:flex;flex-direction:column;justify-content:flex-end}
.hpg .big{grid-row:span 2}.hpg h1{color:#fff;font-size:clamp(30px,4vw,48px);max-width:560px}.hpg p{max-width:480px;margin:12px 0 20px;opacity:.9}.hpg .big .b{align-self:flex-start}.hpg .sm b{font:700 24px --FH}.hpg .sm span{opacity:.9}
.br{border-block:1px solid var(--ln);padding:22px 0}.br .w{display:flex;align-items:center;gap:34px;flex-wrap:wrap}.br span{font-size:13px;color:var(--mut);font-weight:700}.br b{font-size:19px;color:#9097a0;letter-spacing:.02em}
.sec{padding:84px 0}.sf{background:var(--sf)}.hd{max-width:640px;margin-bottom:38px}.hd p{color:var(--mut);margin-top:12px}.nar{max-width:820px}
.cards{display:grid;gap:22px}.cards.n3{grid-template-columns:repeat(3,1fr)}.cards.n4{grid-template-columns:repeat(4,1fr)}
.card{background:#fff;border:1px solid var(--ln);border-radius:var(--r);overflow:hidden;transition:transform .2s,box-shadow .2s}.card:hover{transform:translateY(-3px);box-shadow:0 18px 40px -22px rgba(0,0,0,.35)}
.card img{width:100%;aspect-ratio:3/2;object-fit:cover}.card>div{padding:18px 20px 20px}.card p{color:var(--mut);font-size:15px;margin:6px 0 14px}.pr{display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--ln);padding-top:12px}.pr b{color:var(--dk);font-size:17px}.pr span{color:var(--ac);font-weight:700;font-size:14px}
.pk{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.pkc{background:#fff;border-radius:var(--r);padding:28px;border:1px solid var(--ln);position:relative}.pkc.on{border:2px solid var(--ac);transform:scale(1.03)}
.pkc p{color:var(--mut);font-size:15px}.pp{display:block;font:700 32px --FH;color:var(--dk);margin:16px 0}.pkc ul{list-style:none;margin-bottom:22px;font-size:15px}.pkc li{padding:6px 0;border-bottom:1px dashed var(--ln)}.pkc li::before{content:"✓ ";color:var(--ac);font-weight:700}.pkc .b{width:100%}
.tag{position:absolute;top:-13px;left:24px;background:var(--ac);color:#fff;font-size:12px;font-weight:700;padding:3px 12px;border-radius:99px}
.tool{background:var(--dk);color:#fff;padding:56px 0}.tool h2{color:#fff}.tb{display:grid;grid-template-columns:1fr 2fr;gap:30px;align-items:end}.tb .fm.dk{margin:0}
.st{list-style:none;display:grid;grid-template-columns:repeat(4,1fr);gap:22px;counter-reset:a}.st li{border-top:3px solid var(--ac);padding-top:16px}.st b{font:700 40px --FH;color:var(--ac)}
.nm{background:var(--dk);color:#fff;padding:50px 0}.nm .w{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}.nm b{display:block;font:700 clamp(30px,4vw,46px) --FH;color:#fff}.nm span{opacity:.75}
.gl{display:grid;grid-template-columns:2fr 1fr 1fr;grid-template-rows:220px 220px;gap:12px}.gl img{width:100%;height:100%;object-fit:cover;border-radius:var(--r)}.gl img:first-child{grid-row:span 2}
.ba{display:grid;grid-template-columns:1fr 1fr;gap:16px}.ba figure{position:relative}.ba img{border-radius:var(--r);width:100%;aspect-ratio:4/3;object-fit:cover}.ba figcaption{position:absolute;left:14px;top:14px;background:#fff;font-weight:700;padding:4px 12px;border-radius:99px;font-size:14px}
.tm{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}.tm>div{background:#fff;border-radius:var(--r);padding:26px;text-align:center;border:1px solid var(--ln)}.tm i{display:grid;place-items:center;width:84px;height:84px;margin:0 auto 14px;border-radius:50%;background:var(--ac);color:#fff;font:700 26px --FH;font-style:normal}.tm span{display:block;color:var(--mut);font-size:14px;margin:4px 0 12px}.tm a{color:var(--ac);font-weight:700;font-size:14px}
.rv{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.rv blockquote{border:1px solid var(--ln);border-radius:var(--r);padding:24px}.stars{color:#f5a524;letter-spacing:2px}.rv p{margin:10px 0 14px}.rv cite{font-style:normal;font-weight:700;color:var(--mut);font-size:14px}.note{font-size:13px;color:var(--mut);margin-top:16px}
details{background:#fff;border-radius:var(--r);margin-bottom:10px;border:1px solid var(--ln)}summary{padding:18px 22px;font-weight:700;cursor:pointer;list-style:none;display:flex;justify-content:space-between}summary::after{content:"+";color:var(--ac);font-size:22px;line-height:1}details[open] summary::after{content:"–"}details p{padding:0 22px 18px;color:var(--mut)}
.ct{list-style:none;margin:0 0 24px}.ct li{padding:12px 0;border-bottom:1px solid var(--ln)}.ct b{display:block;font-size:13px;color:var(--mut)}
.map{min-height:340px;border-radius:var(--r);background:linear-gradient(var(--sf),var(--sf)),#eee;background-image:linear-gradient(rgba(0,0,0,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.05) 1px,transparent 1px);background-size:32px 32px;background-color:var(--sf);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px}.map span{font-size:40px}.map small{color:var(--mut)}
.prg{display:grid;grid-template-columns:repeat(5,1fr);gap:18px}.pc img{width:100%;aspect-ratio:5/6;object-fit:cover;border-radius:var(--r)}.pc.il img{aspect-ratio:4/3}.pc h3{font-size:16px;margin:12px 0 8px;font-family:--FB}.pc>div{display:flex;justify-content:space-between;align-items:center;gap:8px}.pc>div b{color:var(--dk);font-size:17px}
.cat{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}.cat a{aspect-ratio:4/5;border-radius:var(--r);background-size:cover;background-position:center;display:flex;align-items:flex-end;padding:18px;color:#fff;transition:transform .2s}.cat a:hover{transform:translateY(-3px)}.cat b{font:700 22px --FH}
.perk{border-bottom:1px solid var(--ln);padding:24px 0}.perk .w{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.perk b{display:block;color:var(--dk)}.perk span{color:var(--mut);font-size:14px}
.mt{display:flex;gap:8px;margin-bottom:22px;flex-wrap:wrap}.mt button{min-height:44px;padding:0 20px;border-radius:99px;border:1.5px solid var(--ln);background:#fff;font:700 15px inherit;cursor:pointer}.mt button.on{background:var(--dk);color:#fff;border-color:var(--dk)}
.mp2{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.mi{display:grid;grid-template-columns:72px 1fr auto;gap:12px;align-items:center;background:#fff;border-radius:var(--r);padding:12px;border:1px solid var(--ln)}.mi img{width:72px;height:72px;object-fit:cover;border-radius:calc(var(--r)*.7)}.mi small{color:var(--mut)}.mi b{color:var(--dk)}.mi .b{grid-column:3}
.kr{overflow-x:auto}.kr table{width:100%;border-collapse:separate;border-spacing:6px;min-width:680px}.kr th{font-size:14px;color:var(--mut);text-align:left;padding:4px}.kr td:first-child{font-weight:700}.sl{width:100%;min-height:52px;border:0;border-radius:calc(var(--r)*.7);background:#fff;font:700 14px inherit;cursor:pointer;border-left:4px solid var(--ac);text-align:left;padding:6px 10px}.sl small{display:block;color:var(--mut);font-weight:500;font-size:12px}
.cta{background:var(--ac);color:#fff;padding:44px 0}.cta .w{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}.cta h2{color:#fff;font-size:clamp(22px,3vw,32px)}
footer{background:var(--dk);color:rgba(255,255,255,.78);padding:60px 0 0;font-size:15px}.fg{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:30px}footer .lg{color:#fff}footer b{display:block;color:#fff;margin-bottom:12px}footer a{display:block;padding:3px 0;cursor:pointer}footer a:hover{color:#fff}.cp{border-top:1px solid rgba(255,255,255,.12);margin-top:44px;padding:20px;font-size:13px;opacity:.7}
.mb{display:none}.back{position:fixed;right:14px;bottom:14px;z-index:50;background:#111;color:#fff;font:600 13px system-ui;padding:10px 14px;border-radius:99px;box-shadow:0 8px 24px -8px #000}
@media(max-width:900px){.top nav,.tel{display:none}.g2,.tb{grid-template-columns:1fr}.cards.n3,.cards.n4,.pk,.rv,.tm,.st,.nm .w,.perk .w,.mp2{grid-template-columns:1fr 1fr}.prg,.cat{grid-template-columns:repeat(2,1fr)}.fg{grid-template-columns:1fr 1fr}
.fcard{position:static;margin-top:-60px;margin-inline:12px}.hpg{grid-template-columns:1fr;grid-template-rows:420px 180px 180px;height:auto}.hpg .big{grid-row:auto}.gl{grid-template-columns:1fr 1fr;grid-template-rows:200px 140px 140px}.gl img:first-child{grid-column:span 2;grid-row:auto}.pkc.on{transform:none}}
@media(max-width:600px){.hpic img{aspect-ratio:4/3}.sec{padding:58px 0}.cards.n3,.cards.n4,.pk,.rv,.st,.mp2,.ba{grid-template-columns:1fr}.hf{min-height:540px}.top>.w{height:62px;gap:12px}.hr .b{display:none}
.mb{display:grid;grid-template-columns:1fr 1fr 1.4fr;position:sticky;bottom:0;z-index:30;background:#fff;border-top:1px solid var(--ln)}.mb a{min-height:56px;display:grid;place-items:center;font-weight:700;font-size:15px}.mb a.p{background:var(--ac);color:#fff}.back{bottom:70px}}
.bgv{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.75),rgba(0,0,0,.2))}.shade.b{background:linear-gradient(0deg,rgba(0,0,0,.7),transparent 65%)}
.hf{position:relative;overflow:hidden}.hf .w{position:relative;z-index:1;width:100%}
.hpic{position:relative;aspect-ratio:5/5.4;border-radius:calc(var(--r)*1.6);overflow:visible}.hpic .bgv{border-radius:calc(var(--r)*1.6)}.live{position:absolute;left:16px;top:16px;background:rgba(0,0,0,.55);color:#fff;font-size:12px;font-weight:700;padding:5px 10px;border-radius:99px;backdrop-filter:blur(4px)}
.hpg .big{position:relative;overflow:hidden}.hpg .big .bt{position:relative;z-index:1;display:flex;flex-direction:column}
.in>*{opacity:0;transform:translateY(22px);transition:opacity .8s cubic-bezier(.2,.7,.2,1),transform .8s cubic-bezier(.2,.7,.2,1)}.in.go>*{opacity:1;transform:none}.in.go>*:nth-child(2){transition-delay:.12s}.in.go>*:nth-child(3){transition-delay:.24s}.in.go>*:nth-child(4){transition-delay:.36s}.in.go>*:nth-child(5){transition-delay:.48s}
.rv0{opacity:0;transform:translateY(26px);transition:opacity .7s ease,transform .7s cubic-bezier(.2,.7,.2,1)}.rv0.vis{opacity:1;transform:none}
.card img,.pc img,.cat a,.gl img{transition:transform .6s cubic-bezier(.2,.7,.2,1)}.card{overflow:hidden}.card:hover img,.pc:hover img{transform:scale(1.06)}.pc{overflow:hidden}.pc img{will-change:transform}
.mq{overflow:hidden;flex:1;mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent)}.mqi{display:flex;gap:46px;width:max-content;animation:mq 26s linear infinite}.mq:hover .mqi{animation-play-state:paused}@keyframes mq{to{transform:translateX(-50%)}}
.nm{position:relative;overflow:hidden}.nm .w{position:relative;z-index:1}.nm .shade{background:rgba(0,0,0,.62)}.bgv.dim{filter:saturate(.8)}
.top{transition:box-shadow .3s,background .3s}.top.sm{box-shadow:0 8px 30px -18px rgba(0,0,0,.4)}.top>.w{transition:height .3s}.top.sm>.w{height:60px}
.hasm{position:relative;cursor:pointer;padding:24px 0}.mega{position:fixed;left:0;right:0;top:72px;background:#fff;border-top:1px solid var(--ln);box-shadow:0 30px 50px -30px rgba(0,0,0,.35);opacity:0;visibility:hidden;transform:translateY(-8px);transition:all .25s}.top.sm .mega{top:60px}
.hasm:hover .mega{opacity:1;visibility:visible;transform:none}.mg{display:grid;grid-template-columns:1fr 1fr 1.2fr;gap:30px;padding:28px 20px}.mg b{display:block;color:var(--dk);margin-bottom:10px;font-size:14px}.mg a{display:block;padding:6px 0;color:#3b3f45;font-weight:500}.mg a:hover{color:var(--ac);padding-left:4px}.mg .mgp{padding:18px;border-radius:var(--r);background-size:cover;background-position:center;min-height:170px;color:#fff;padding:18px;display:flex!important;flex-direction:column;justify-content:flex-end}.mgp span{font-size:12px;opacity:.85}.mgp b{color:#fff;font:700 20px --FH;margin:0}
.bur{display:none;flex-direction:column;gap:5px;background:none;border:0;padding:10px;cursor:pointer}.bur i{display:block;width:22px;height:2px;background:var(--dk);border-radius:2px}
.drw{position:fixed;inset:0;z-index:60;background:var(--dk);color:#fff;padding:20px;transform:translateX(-100%);transition:transform .4s cubic-bezier(.2,.7,.2,1);display:flex;flex-direction:column;gap:2px}.mo .drw{transform:none}
.dh{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;font:700 22px --FH}.dh button{background:rgba(255,255,255,.1);border:0;color:#fff;width:44px;height:44px;border-radius:50%;font-size:18px}
.drw>a:not(.b){display:flex;justify-content:space-between;padding:15px 4px;border-bottom:1px solid rgba(255,255,255,.12);font-size:19px;font-weight:600}.drw .b{margin-top:22px}.drw .tl{text-align:center;padding:14px;color:var(--ac);font-weight:700}
.sl1{overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none}.sl1::-webkit-scrollbar{display:none}.sl1>*{scroll-snap-align:start}
@media(max-width:900px){.bur{display:flex}.hpic{aspect-ratio:4/3}.rv.sl1{display:flex}.rv.sl1>*{min-width:85%}}
@media(max-width:900px){.hpic{aspect-ratio:auto;display:flex;flex-direction:column;overflow:visible}.hpic .bgv{position:static;height:auto;aspect-ratio:16/10;border-radius:calc(var(--r)*1.4)}.hpic .fcard{position:static;margin:12px 0 0;box-shadow:0 14px 30px -18px rgba(0,0,0,.3);border:1px solid var(--ln)}.hpic img{aspect-ratio:16/10}.hs{padding:36px 0 44px}.hf{padding:56px 0}}
@media(max-width:600px){h1{font-size:30px}h2{font-size:24px}.lead{font-size:16px;margin:12px 0 20px}.b{min-height:44px;padding:0 18px;font-size:14px}.b.s{min-height:38px}.top>.w{height:52px}.top.sm>.w{height:48px}.lg{font-size:19px}.cart{font-size:14px}.bur{padding:8px}.bur i{width:20px}
.drw{padding:14px 16px}.dh{font-size:18px;margin-bottom:8px}.dh button{width:38px;height:38px;font-size:15px}.drw>a:not(.b){padding:12px 2px;font-size:16px}.drw .b{margin-top:16px;min-height:44px}.drw .tl{padding:10px;font-size:15px;border:0}
.mb{grid-template-columns:1fr 1fr 1.3fr}.mb a{min-height:46px;font-size:14px}.back{bottom:58px;padding:7px 11px;font-size:12px}.fm{grid-template-columns:1fr}.fm input{min-height:44px}.sec{padding:48px 0}.hd{margin-bottom:26px}}
.lm{display:inline-flex;align-items:center;gap:10px;font:700 21px/1 --FH,serif;color:var(--dk);white-space:nowrap}.lm i{display:grid;place-items:center;width:42px;height:42px;background:var(--ac);color:#fff;font:700 15px/1 --FH,serif;font-style:normal;letter-spacing:.02em;border-radius:50%}.lm i.r{border-radius:10px}.lm i.h{border-radius:4px 16px 4px 16px}.lgo{height:40px;width:auto;display:block}footer .lgo{height:44px;margin-bottom:12px}.dh .lgo{height:34px}@media(max-width:600px){.lgo{height:30px}.dh .lgo{height:28px}}.lm i.d{border-radius:50% 50% 50% 4px}
footer .lm,.drw .lm{color:#fff}footer .lm i,.drw .lm i{box-shadow:0 0 0 2px rgba(255,255,255,.25)}
@media(max-width:600px){.lm{font-size:17px;gap:8px}.lm i{width:32px;height:32px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}.in>*,.rv0{opacity:1;transform:none}}"""


JS = r"""(function(){var R=matchMedia('(prefers-reduced-motion:reduce)').matches;
var h=document.querySelector('.top');addEventListener('scroll',function(){h.classList.toggle('sm',scrollY>40)},{passive:true});
document.querySelectorAll('.in').forEach(function(e){e.classList.add('go')});
if(R){document.querySelectorAll('video').forEach(function(v){v.pause()});return}
var io=new IntersectionObserver(function(es){es.forEach(function(x){if(!x.isIntersecting)return;var t=x.target;io.unobserve(t);t.classList.add('vis');
 if(t.dataset.n!==undefined){var raw=t.dataset.n,m=raw.match(/[\d.,]+/);if(!m)return;var n=parseFloat(m[0].replace(/\./g,'').replace(',','.')),dec=m[0].indexOf(',')>-1||/^\d\.\d$/.test(m[0]),k=0,st=performance.now();
  (function f(now){var p=Math.min(1,(now-st)/1400),v=n*(1-Math.pow(1-p,3));var s=dec?v.toFixed(1):Math.round(v).toLocaleString('tr-TR');t.textContent=raw.replace(m[0],s);if(p<1)requestAnimationFrame(f)})(st)}})},{threshold:.25});
document.querySelectorAll('.hd,.gl img,b[data-n]').forEach(function(e,i){e.classList.add('rv0');e.style.transitionDelay=(i%4)*70+'ms';io.observe(e)});
document.querySelectorAll('.sl1').forEach(function(s){var k=0;setInterval(function(){k=(k+1)%s.children.length;s.scrollTo({left:s.children[k].offsetLeft-s.offsetLeft,behavior:'smooth'})},4200)});
})();"""

INDEX = """<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>20 yeni tema · önizleme</title>
<style>*{box-sizing:border-box;margin:0}body{font:15px/1.5 system-ui,sans-serif;background:#f1f0ec;color:#17191d;padding:28px 18px}h1{font-size:28px;max-width:1200px;margin:0 auto 6px}p.s{max-width:1200px;margin:0 auto 24px;color:#666}
h2{max-width:1200px;margin:28px auto 12px;font-size:18px}.g{max-width:1200px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px}
a.t{display:block;background:#fff;border-radius:14px;overflow:hidden;text-decoration:none;color:inherit;transition:transform .2s}a.t:hover{transform:translateY(-3px)}a.t img{width:100%;aspect-ratio:16/10;object-fit:cover}a.t div{padding:12px 14px}a.t b{display:block;font-size:16px}a.t span{color:#666;font-size:13px}.sw{display:flex;gap:4px;margin-top:6px}.sw i{width:16px;height:16px;border-radius:50%}</style></head><body>
<h1>20 yeni tema · fotoğraflı önizleme</h1><p class="s">Her kartı açınca temanın ana sayfası görünür. Fotoğraflar Pexels'ten (ücretsiz, ticari kullanım serbest). Yazılar ve fiyatlar örnektir, firma panelden değiştirir.</p>%s</body></html>"""

if __name__ == "__main__":
    groups = [("Servis ve teklif", range(0, 6)), ("Randevu", range(6, 13)), ("E-ticaret", range(13, 17)), ("Restoran, emlak, kurs", range(17, 20))]
    for i, t in enumerate(T):
        open(os.path.join(OUT, "%02d.html" % (i + 1)), "w", encoding="utf-8").write(page(i, t, C[i]))
    body = "".join('<h2>%s</h2><div class="g">%s</div>' % (g, "".join('<a class="t" href="%02d.html"><img loading="lazy" src="%s" alt=""><div><b>%02d · %s</b><span>%s</span><div class="sw">%s</div></div></a>' % (
        i + 1, url(F[i][0], 640, 400), i + 1, E_(T[i][0]), E_(T[i][1]), "".join('<i style="background:%s"></i>' % x for x in T[i][3])) for i in r)) for g, r in groups)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(INDEX.replace("%s", body))
    print("ok")
