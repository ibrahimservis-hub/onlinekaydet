# -*- coding: utf-8 -*-
"""20 temanın çok sayfalı, çalışan sitesi -> site/NN/*.html  (örnek firma verisi; localStorage ile çalışan demo, panel API'sine bağlanacak)"""
import os, re, html, json
from pano import T, LBL
from foto import F, url
from icerik import C, SSS
import onizle as O
E_ = html.escape
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")
LIB = open(os.path.join(HERE, "lib.js"), encoding="utf-8").read()
PCSS = open(os.path.join(HERE, "pages.css"), encoding="utf-8").read()
FORMTO = {"servis": "talep.html", "randevu": "randevu.html", "yemek": "rezervasyon.html", "proje": "ilanlar.html", "kurs": "on-kayit.html"}
CTAP = dict(FORMTO, magaza="urunler.html")
STEPS = {"servis": ["Talebinizi bırakın", "15 dakika içinde arıyoruz", "Usta kapınızda", "Ödeme ve garanti belgesi"],
         "randevu": ["Hizmeti seçin", "Saati ayırın", "SMS hatırlatma", "Gelin, hazırız"],
         "kurs": ["Ön kayıt", "Evrak", "Teorik ve direksiyon", "Sınav"],
         "proje": ["İlanı seçin", "Görüşme ayarlayın", "Yerinde gezin", "Sözleşme"]}
VAR = {14: [("Beden", "S", ["XS", "S", "M", "L", "XL"]), ("Renk", "Ekru", ["Ekru", "Siyah", "Haki"])],
       16: [("Porsiyon", "6 kişilik", ["6 kişilik", "8 kişilik", "12 kişilik"])],
       17: [("Telefon modeli", "", ["iPhone 15", "iPhone 14", "Galaxy S24", "Galaxy A55", "Redmi Note 13"])]}


def num(t):
    m = re.search(r"\d[\d.]*", t or "")
    return int(m.group(0).replace(".", "")) if m else 0


def gen(i):
    n = i + 1
    t = T[i]; c = C[i]
    nm, sec, fam, pal, fn, secs, pages, works, _ = t
    P = F[i]
    ph = lambda k, w=900, h=None: url(P[k % len(P)], w, h)
    cards = c["cards"]; prods = c.get("products") or []; team = c.get("team") or []
    codes = [s.split(":")[0] for s in secs]
    has_pk = "pk" in codes; has_bl = "bl" in codes; has_gl = "gl" in codes; has_kr = "kr" in codes
    cta = O.CTA[fam]
    buy = bool(prods) or fam == "yemek" or has_pk
    pages_out = {}
    ctx = dict(sec=sec)

    def hero(title, sub="", crumbs=()):
        bc = '<div class="bc"><a href="index.html">Ana sayfa</a>' + "".join(" / " + (('<a href="%s">%s</a>' % (h, E_(l))) if h else E_(l)) for l, h in crumbs) + "</div>"
        return '<section class="ph"><div class="w">%s<h1>%s</h1>%s</div></section>' % (bc, E_(title), "<p>%s</p>" % E_(sub) if sub else "")

    def sec_(inner, cls=""):
        return '<section class="sec %s"><div class="w">%s</div></section>' % (cls, inner)

    def fld(label, kind="input", req=True, opts=None, typ=None):
        r = " required" if req else ""
        if kind == "select":
            return '<label>%s<select%s data-l="%s">%s</select></label>' % (E_(label), r, E_(label), "".join("<option>%s</option>" % E_(x) for x in [""] + opts)) if False else '<label>%s<select%s data-l="%s" placeholder="%s"><option value="">Seçin</option>%s</select></label>' % (E_(label), r, E_(label), E_(label), "".join("<option>%s</option>" % E_(x) for x in opts))
        if kind == "area":
            return '<label>%s<textarea%s data-l="%s" placeholder="%s" rows="3"></textarea></label>' % (E_(label), r, E_(label), E_(label))
        if kind == "file":
            return '<label>%s<input type="file" accept="image/*"></label>' % E_(label)
        return '<label>%s<input%s%s data-l="%s" placeholder="%s"></label>' % (E_(label), r, ' type="%s"' % typ if typ else "", E_(label), E_(label))

    def form(kind, title, fields, btn, ok="Talebiniz alındı.", pref="TK", extra=""):
        return ('<div class="two"><div><form class="ff box" data-kind="%s" data-title="%s" data-p="%s">%s<button class="b p">%s</button></form>'
                '<div class="done box ok2" hidden><h3>%s</h3><p>Takip numaranız: <b class="no"></b></p><p>Numarayı saklayın; durumu takip sayfasından sorgulayabilirsiniz.</p><div class="row"><a class="b p" href="%s">Durumu sorgula</a><a class="b o" href="index.html">Ana sayfa</a></div></div></div>%s</div>') % (
            kind, E_(title), pref, "".join(fields), E_(btn), E_(ok), TRACK, extra)

    side_contact = '<aside class="box"><h3>Bize ulaşın</h3><p>Hafta içi 08:30–19:00 · Cumartesi 09:00–17:00</p><div class="row"><a class="b p" href="tel:+905320000000">0532 000 00 00</a><a class="b o" href="#">WhatsApp</a></div></aside>'

    # ---------- gezinti ----------
    TRACK = "takip.html"
    L = {}
    detail = {}
    if fam in ("servis", "randevu", "kurs", "proje"):
        for k, x in enumerate(cards):
            detail[x[0]] = "hizmet-%d.html" % (k + 1)
    if fam == "servis":
        nav = [("Hizmetler", "hizmetler.html"), ("Servis talebi", "talep.html"), ("Randevu", "randevu.html"), ("Servis takip", "takip.html"), ("İletişim", "iletisim.html")]
        foot = ["Bölgeler"] + (["Paketler"] if has_pk else []) + (["Mağaza"] if prods else []) + (["Hesabım"] if buy else [])
        extra = {"Bölgeler": "bolgeler.html", "Paketler": "paketler.html", "Mağaza": "urunler.html", "Hesabım": "hesabim.html"}
    elif fam == "randevu":
        third = ("Ekip", "ekip.html") if team else (("Galeri", "galeri.html") if has_gl else ("Fiyatlar", "hizmetler.html"))
        fourth = ("Paketler", "paketler.html") if has_pk else (("Ürünler", "urunler.html") if prods else (("Yazılar", "yazilar.html") if has_bl else ("SSS", "iletisim.html")))
        nav = [("Hizmetler", "hizmetler.html"), ("Randevu", "randevu.html"), third, fourth, ("İletişim", "iletisim.html")]
        foot = (["Galeri"] if has_gl and third[0] != "Galeri" else []) + (["Yazılar"] if has_bl and fourth[0] != "Yazılar" else []) + (["Ürünler"] if prods and fourth[0] != "Ürünler" else []) + (["Paketler"] if has_pk and fourth[0] != "Paketler" else []) + (["Hesapla"] if n in (11,) else []) + (["Hesabım"] if buy else []) + (["Randevu sorgula"])
        extra = {"Galeri": "galeri.html", "Yazılar": "yazilar.html", "Ürünler": "urunler.html", "Paketler": "paketler.html", "Hesapla": "hesapla.html", "Hesabım": "hesabim.html", "Randevu sorgula": "takip.html"}
    elif fam == "magaza":
        sp = {16: ("Özel pasta", "ozel-pasta.html"), 17: ("Tamir", "tamir.html")}.get(n, ("Teslimat", "kargo-iade.html"))
        nav = [("Ürünler", "urunler.html"), ("Sipariş takip", "takip.html"), sp, ("Hesabım", "hesabim.html"), ("İletişim", "iletisim.html")]
        foot = ["Kargo ve iade"]
        extra = {"Kargo ve iade": "kargo-iade.html"}
        if n == 17:
            nav[1] = ("Tamir takip", "takip.html")
    elif fam == "yemek":
        nav = [("Menü", "menu.html"), ("Paket sipariş", "menu.html"), ("Rezervasyon", "rezervasyon.html"), ("Sipariş takip", "takip.html"), ("İletişim", "iletisim.html")]
        foot = ["Hesabım"]; extra = {"Hesabım": "hesabim.html"}
    elif fam == "proje":
        nav = [("İlanlar", "ilanlar.html"), ("Değerleme", "degerleme.html"), ("Danışmanlar", "danismanlar.html"), ("Randevu", "randevu.html"), ("İletişim", "iletisim.html")]
        foot = ["Kredi hesapla"]; extra = {"Kredi hesapla": "hesapla.html"}
    else:
        nav = [("Kurslar", "kurslar.html"), ("Ücretler", "ucretler.html"), ("Takvim", "takvim.html"), ("Ön kayıt", "on-kayit.html"), ("İletişim", "iletisim.html")]
        foot = ["Kayıt sorgula"]; extra = {"Kayıt sorgula": "takip.html"}
    L.update(dict(nav)); L.update({k: extra[k] for k in foot})
    for k_, v_ in detail.items():
        L[k_] = v_
    if fam == "magaza":
        for x in cards:
            L[x[0]] = "urunler.html"
    for b_ in c.get("brands", []):
        pass
    foot_labels = [l for l, _ in nav] + foot

    # ---------- sayfalar ----------
    # hizmetler / kurslar listesi
    def cardhtml(k, x, href):
        return '<a class="card" href="%s"><i class="no">%02d</i><img loading="lazy" src="%s" alt="%s"><div><h3>%s</h3><p>%s</p><div class="pr"><b>%s</b><span>%s →</span></div></div></a>' % (href, k + 1, ph(k + 1, 700, 480), E_(x[0]), E_(x[0]), E_(x[1]), E_(x[2] or "Teklif"), E_(cta))

    if detail:
        listname = {"servis": "Hizmetlerimiz", "randevu": "Hizmetlerimiz", "kurs": "Kurslarımız", "proje": "Hizmetlerimiz"}[fam]
        pages_out["hizmetler.html" if fam != "kurs" else "kurslar.html"] = (listname, hero(listname, "Fiyatlar başlangıç fiyatıdır; kesin tutar işe başlamadan söylenir." if any(x[2] for x in cards) else "", [(listname, None)]) +
            sec_('<div class="cards n3 k-%s">%s</div>' % (O.SK[n][2], "".join(cardhtml(k, x, "hizmet-%d.html" % (k + 1)) for k, x in enumerate(cards)))), "x", None)
        if fam == "kurs":
            L["Kurslar"] = "kurslar.html"
        steps = STEPS.get(fam, STEPS["servis"])
        act = {"servis": ("Servis talebi oluştur", "talep.html"), "randevu": ("Randevu al", "randevu.html"), "kurs": ("Ön kayıt yaptır", "on-kayit.html"), "proje": ("Randevu al", "randevu.html")}[fam]
        for k, x in enumerate(cards):
            relc = [cardhtml(j, y, "hizmet-%d.html" % (j + 1)) for j, y in enumerate(cards) if j != k][:3]
            body = ('<div class="det"><div><img class="big" src="%s" alt="%s"><h2 style="margin:28px 0 10px">%s nasıl ilerler?</h2><ol class="tlx on">%s</ol></div>'
                    '<aside class="box"><h3>%s</h3><p>%s</p><div class="pr0" style="font:700 30px var(--fh,serif)">%s</div><a class="b p" href="%s?s=%d">%s</a><a class="b o" style="margin-top:10px" href="tel:+905320000000">0532 000 00 00</a></aside></div>') % (
                ph(k + 1, 1100, 800), E_(x[0]), E_(x[0]), "".join("<li class='on'>%s</li>" % E_(s_) for s_ in steps), E_(x[0]), E_(x[1]), E_(x[2] or "Teklif alın"), act[1], k, E_(act[0]))
            pages_out["hizmet-%d.html" % (k + 1)] = (x[0], hero(x[0], x[1], [(listname, "hizmetler.html" if fam != "kurs" else "kurslar.html"), (x[0], None)]) + sec_(body) + sec_('<h2 style="margin-bottom:24px">Diğer hizmetler</h2><div class="cards n3 k-img">%s</div>' % "".join(relc), "sf"), "x", None)

    # servis: talep + bolgeler
    if fam == "servis":
        brands = c.get("brands")
        f0 = c.get("form") or ["Cihaz", "Arıza", "Telefon"]
        fl = [fld(f0[0], "select", True, brands) if brands and f0[0].startswith("Marka") else fld(f0[0])] + [fld(x) for x in f0[1:]] + [fld("Ad soyad"), fld("Adres / ilçe"), fld("Ayrıntı", "area", False), fld("Fotoğraf (isteğe bağlı)", "file")]
        pages_out["talep.html"] = ("Servis talebi", hero("Servis talebi", "Formu doldurun, ustamız sizi arasın.", [("Servis talebi", None)]) + sec_(form("talep", "Servis talebi", fl, c.get("fbtn", cta), "Talebiniz alındı", "TL", side_contact)), "form", None)
        pages_out["bolgeler.html"] = ("Servis bölgeleri", hero("Servis bölgeleri", "Hizmet verdiğimiz ilçeler.", [("Bölgeler", None)]) + sec_('<div class="chips">%s</div><p class="hint" style="margin-top:20px">Listede olmayan ilçe için arayın, yakın ekiple eşleştirelim.</p>' % "".join('<a href="talep.html">%s</a>' % x for x in ["Bornova", "Karşıyaka", "Bayraklı", "Buca", "Çiğli", "Konak", "Gaziemir", "Narlıdere", "Balçova", "Menemen", "Torbalı", "Urla"])), "x", None)
    # takip
    if fam in ("servis", "magaza", "yemek", "randevu") or n in (17,):
        tt = "Tamir takip" if n == 17 else ("Randevu sorgula" if fam == "randevu" else ("Sipariş takip" if fam in ("magaza", "yemek") else "Servis takip"))
        pages_out["takip.html"] = (tt, hero(tt, "Takip numaranızı yazın, durumu görün.", [(tt, None)]) + sec_('<div class="two"><div><form id="tf" class="ff box"><label>Takip numarası<input required placeholder="Örn. TLAB12C" autocomplete="off"></label><button class="b p">Sorgula</button></form><div id="tr" style="margin-top:18px"></div></div>' + side_contact + '</div>'), "track", None)
    if fam == "kurs":
        pages_out["takip.html"] = ("Kayıt sorgula", hero("Kayıt sorgula", "Ön kayıt numaranızla durumu görün.", [("Kayıt sorgula", None)]) + sec_('<div class="two"><div><form id="tf" class="ff box"><label>Kayıt numarası<input required placeholder="Örn. ONAB12C"></label><button class="b p">Sorgula</button></form><div id="tr" style="margin-top:18px"></div></div>' + side_contact + '</div>'), "track", None)

    # randevu sihirbazı
    wiz_team = team and fam in ("randevu", "proje")
    if fam in ("randevu", "servis", "proje"):
        svc = [dict(n=x[0], d=x[1], p=x[2] or "Teklif") for x in cards]
        tm = [x.split(" · ")[0] for x in team] if wiz_team else None
        if fam == "proje":
            svc = [dict(n=x[0] if False else y[0], d=y[1], p="Ücretsiz") for x, y in zip(cards, cards)][:3]
        D = dict(services=svc, team=tm, hours=[9, 19] if fam != "servis" else [8, 18], step=1 if fam != "randevu" else 0.5, track=("takip.html" if fam != "proje" else "index.html"), sunday=False)
        ttl = {"servis": "Servis randevusu", "randevu": "Randevu al", "proje": "Görüşme randevusu"}[fam]
        pages_out["randevu.html"] = (ttl, hero(ttl, "Hizmeti, günü ve saati seçin; onay SMS ile gelir.", [(ttl, None)]) + sec_('<div class="two"><div id="app" class="box"></div>' + side_contact + '</div>'), "wizard", D)
    if fam == "randevu" and team:
        pages_out["ekip.html"] = ("Ekip", hero("Ekibimiz", "Randevunuzu dilediğiniz uzmana alın.", [("Ekip", None)]) + sec_('<div class="tg">%s</div>' % "".join('<div><i>%s</i><h3>%s</h3><span>%s</span><a class="b o s" href="randevu.html">Randevu al</a></div>' % (E_("".join(w[0] for w in p.split(" · ")[0].replace("Dt. ", "").replace("Dr. ", "").split()[:2])), E_(p.split(" · ")[0]), E_(p.split(" · ")[1] if " · " in p else "")) for p in team)), "x", None)
    if fam == "proje":
        pages_out["danismanlar.html"] = ("Danışmanlar", hero("Danışmanlarımız", "", [("Danışmanlar", None)]) + sec_('<div class="tg">%s</div>' % "".join('<div><i>%s</i><h3>%s</h3><span>%s</span><a class="b o s" href="randevu.html">Görüşme al</a></div>' % (E_(p.split(" · ")[0][:2].upper()), E_(p.split(" · ")[0]), E_(p.split(" · ")[1] if " · " in p else "")) for p in team)), "x", None)
        pages_out["degerleme.html"] = ("Değerleme talebi", hero("Değerleme talebi", "Evinizin güncel değerini uzmanımız belirlesin.", [("Değerleme", None)]) + sec_(form("degerleme", "Değerleme talebi", [fld("Ad soyad"), fld("Telefon", typ="tel"), fld("İlçe / mahalle"), fld("Oda sayısı"), fld("Metrekare"), fld("Not", "area", False)], "Değerleme iste", "Talebiniz alındı", "DG", side_contact)), "form", None)
        li = c["listings"]
        def lst(k, x):
            kira = "/ay" in x[1]; ilce = x[0].split(" · ")[0]; oda = x[0].split(" · ")[1]
            return '<a class="ls" href="ilan-%d.html" data-cat="%s" data-ilce="%s" data-oda="%s" data-p="%s"><img loading="lazy" src="%s" alt="%s"><div><b>%s</b><h3>%s</h3></div></a>' % (k + 1, "Kiralık" if kira else "Satılık", E_(ilce), E_(oda), num(x[1]), ph(k + 1, 700, 520), E_(x[0]), E_(x[1]), E_(x[0]))
        ilces = sorted({x[0].split(" · ")[0] for x in li}); odas = sorted({x[0].split(" · ")[1] for x in li})
        sel = lambda key, pre, arr: '<select data-key="%s" data-pre="%s" aria-label="%s"><option value="">%s</option>%s</select>' % (key, pre, pre, pre, "".join("<option value='%s'>%s</option>" % (E_(a), E_(a)) for a in arr))
        pages_out["ilanlar.html"] = ("İlanlar", hero("İlanlar", "", [("İlanlar", None)]) + sec_('<div class="fl"><button data-f="" class="on">Tümü</button><button data-f="Satılık">Satılık</button><button data-f="Kiralık">Kiralık</button>%s%s<span class="sp" id="cnt"></span></div><div class="lsg">%s</div><p id="empty" hidden class="hint">Bu süzgece uyan ilan yok.</p>' % (sel("ilce", "İlçe", ilces), sel("oda", "Oda sayısı", odas), "".join(lst(k, x) for k, x in enumerate(li)))), "filter", None)
        for k, x in enumerate(li):
            ilce, oda, m2 = x[0].split(" · ")
            pages_out["ilan-%d.html" % (k + 1)] = (x[0], hero(x[0], x[1], [("İlanlar", "ilanlar.html"), (x[0], None)]) + sec_('<div class="det"><div><img class="big" src="%s" alt="%s"><div class="pd"><div class="gal th" style="grid-column:1/-1;margin-top:10px"><img src="%s" alt=""><img src="%s" alt=""></div></div></div><aside><ul class="box" style="list-style:none"><li><span>Konum</span><b>%s</b></li><li><span>Oda</span><b>%s</b></li><li><span>Alan</span><b>%s</b></li><li><span>Fiyat</span><b>%s</b></li></ul><a class="b p" style="width:100%%" href="randevu.html">Görüşme randevusu al</a><a class="b o" style="width:100%%;margin-top:10px" href="https://wa.me/?text=%s">WhatsApp ile paylaş</a></aside></div>' % (ph(k + 1, 1100, 800), E_(x[0]), ph(k + 2, 600, 450), ph(k + 3, 600, 450), E_(ilce), E_(oda), E_(m2), E_(x[1]), E_(x[0]))), "x", None)
        pages_out["hesapla.html"] = ("Kredi hesapla", hero("Kredi taksit hesabı", "Aylık faiz oranını bankanızın teklifine göre değiştirin.", [("Kredi hesapla", None)]) + sec_('<div class="two"><form id="calc" class="ff box">%s<button class="b p">Taksiti gör</button><div id="calcr" class="box" style="margin-top:6px"></div></form></div>' % "".join('<label>%s<input required inputmode="decimal" value="%s"></label>' % (a, b) for a, b in [("Kredi tutarı (₺)", "2000000"), ("Vade (ay)", "120"), ("Aylık faiz (%)", "3")])), "bmi", dict(k="kredi"))
    if n == 11:
        pages_out["hesapla.html"] = ("Vücut kitle indeksi", hero("Vücut kitle indeksi", "Boy ve kilonuzu yazın.", [("Hesapla", None)]) + sec_('<div class="two"><form id="calc" class="ff box">%s<button class="b p">Hesapla</button><div id="calcr" class="box" style="margin-top:6px"></div></form></div>' % "".join('<label>%s<input required inputmode="decimal" placeholder="%s"></label>' % (a, b) for a, b in [("Boy (cm)", "170"), ("Kilo (kg)", "70")])), "bmi", dict(k="bmi"))
    # paketler
    if has_pk or fam == "kurs" and False:
        pk = cards[:3]
        pages_out["paketler.html" if fam != "kurs" else "ucretler.html"] = ("Paketler", hero("Paketler" if fam != "kurs" else "Kurs ücretleri", "Size uygun olanı seçin.", [("Paketler", None)]) + sec_('<div class="pk">%s</div>' % "".join(
            '<div class="pkc%s" data-id="pk%d" data-n="%s" data-p="%s" data-img="%s">%s<h3>%s</h3><p>%s</p><b class="pp">%s</b><ul><li>Online ödeme</li><li>SMS hatırlatma</li><li>Ücretsiz iptal</li></ul>%s</div>' % (
                " on" if k == 1 else "", k + 1, E_(a), E_(p), ph(k + 1, 300, 300), '<span class="tag">En çok tercih edilen</span>' if k == 1 else "", E_(a), E_(d), E_(p or "Teklif"),
                ('<button class="b %s" onclick="OK.addP(this);location.href=\'sepet.html\'">Satın al</button>' % ("p" if k == 1 else "o")) if num(p) and fam != "kurs" else '<a class="b %s" href="%s">%s</a>' % ("p" if k == 1 else "o", CTAP[fam] if fam != "magaza" else "iletisim.html", "Ön kayıt" if fam == "kurs" else "Teklif iste")) for k, (a, d, p) in enumerate(pk))), "x", None)
    if fam == "kurs":
        pk = cards[:3]
        pages_out["ucretler.html"] = ("Kurs ücretleri", hero("Kurs ücretleri", "Taksit seçenekleri için ön kayıt sırasında bilgi verilir.", [("Ücretler", None)]) + sec_('<div class="pk">%s</div>' % "".join('<div class="pkc%s">%s<h3>%s</h3><p>%s</p><b class="pp">%s</b><a class="b %s" href="on-kayit.html">Ön kayıt yaptır</a></div>' % (" on" if k == 1 else "", '<span class="tag">En çok tercih edilen</span>' if k == 1 else "", E_(a), E_(d), E_(p or "Teklif"), "p" if k == 1 else "o") for k, (a, d, p) in enumerate(pk))), "x", None)
        rows = [("09:00", ["Teorik", "Direksiyon", "Teorik", "Direksiyon", "Teorik", "Direksiyon"]), ("14:00", ["Direksiyon", "Teorik", "Direksiyon", "Teorik", "Direksiyon", ""]), ("19:00", ["Teorik", "", "Teorik", "", "Teorik", ""])]
        days = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"]
        pages_out["takvim.html"] = ("Takvim", hero("Dönem takvimi", "Ders programı; kontenjanlı derslerde yer kalmadıysa sıraya yazılırsınız.", [("Takvim", None)]) + sec_('<div class="kr"><table><tr><th></th>%s</tr>%s</table></div>' % ("".join("<th>%s</th>" % d for d in days), "".join("<tr><td>%s</td>%s</tr>" % (h, "".join('<td>%s</td>' % ('<a class="sl" href="on-kayit.html">%s</a>' % x if x else "") for x in r)) for h, r in rows))), "x", None)
        f0 = c.get("form") or ["Sınıf", "Ad soyad", "Telefon"]
        pages_out["on-kayit.html"] = ("Ön kayıt", hero("Ön kayıt", "Formu doldurun, evrak listesini SMS ile gönderelim.", [("Ön kayıt", None)]) + sec_(form("onkayit", "Ön kayıt", [fld("Sınıf", "select", True, [x[0] for x in cards])] + [fld(x) for x in f0[1:]] + [fld("Doğum yılı", typ="number"), fld("Not", "area", False)], "Ön kayıt yaptır", "Ön kaydınız alındı", "ON", side_contact)), "form", None)
    # galeri / yazilar
    if has_gl and fam == "randevu":
        pages_out["galeri.html"] = ("Galeri", hero("Galeri", "", [("Galeri", None)]) + sec_('<div class="gl">%s</div>' % "".join('<img loading="lazy" src="%s" alt="">' % ph(k + 2, 800, 800) for k in range(5))), "x", None)
    if has_bl and fam == "randevu":
        pages_out["yazilar.html"] = ("Yazılar", hero("Yazılar", "", [("Yazılar", None)]) + sec_('<div class="cards n3">%s</div>' % "".join('<a class="card" href="iletisim.html"><img loading="lazy" src="%s" alt=""><div><h3>%s</h3><p>5 dk okuma</p></div></a>' % (ph(k + 4, 700, 480), E_(x)) for k, x in enumerate(["Başlarken bilmeniz gerekenler", "Sık yapılan 5 hata", "Uzmanından öneriler"]))), "x", None)

    # mağaza
    shop_items = []
    if prods or fam == "yemek":
        if fam == "yemek":
            k = 0
            for ci, (cn, its) in enumerate(c["menu"]):
                for nm_, pr_ in its:
                    shop_items.append(dict(id="m%d" % k, n=nm_, p=pr_, cat=cn, k=k)); k += 1
        else:
            cats = [x[0] for x in cards[:4]] if fam == "magaza" else ["Ürünler"]
            for k, (nm_, pr_) in enumerate(prods):
                shop_items.append(dict(id="p%d" % (k + 1), n=nm_, p=pr_, cat=cats[k % len(cats)], k=k))
    if prods and fam != "yemek":
        cats = sorted({x["cat"] for x in shop_items}, key=lambda z: [x["cat"] for x in shop_items].index(z))
        grid = "".join('<div class="pc" data-cat="%s" data-p="%s" data-id="%s" data-n="%s" data-img="%s"><a href="urun-%d.html"><img loading="lazy" src="%s" alt="%s"><h3>%s</h3></a><div><b>%s</b><button class="b p s" onclick="OK.addP(this)">Sepete ekle</button></div></div>' % (
            E_(x["cat"]), num(x["p"]), x["id"], E_(x["n"]), ph(x["k"] + 3, 300, 360), x["k"] + 1, ph(x["k"] + 3, 600, 720), E_(x["n"]), E_(x["n"]), E_(x["p"])) for x in shop_items)
        pages_out["urunler.html"] = ("Ürünler", hero("Ürünler", "", [("Ürünler", None)]) + sec_('<div class="fl"><button data-f="" class="on">Tümü</button>%s<input id="fq" placeholder="Ürün ara" aria-label="Ürün ara"><select id="fs" aria-label="Sırala"><option value="">Sırala</option><option value="az">Fiyat: düşükten yükseğe</option><option value="za">Fiyat: yüksekten düşüğe</option></select><span class="sp" id="cnt"></span></div><div class="prg">%s</div><p id="empty" hidden class="hint">Aramanıza uyan ürün yok.</p>' % ("".join('<button data-f="%s">%s</button>' % (E_(x), E_(x)) for x in cats if len(cats) > 1), grid)), "filter", None)
        for x in shop_items:
            k = x["k"]; vars_ = VAR.get(n, [])
            opts = "".join('<div class="opt-g">%s<div class="vr" data-val="%s"><input type="hidden" data-opt="%s" value="%s">%s</div></div>' % (E_(vn), E_(vd), E_(vn), E_(vd), "".join('<button type="button" data-v="%s" class="%s">%s</button>' % (E_(o_), "on" if o_ == vd else "", E_(o_)) for o_ in vo)) for vn, vd, vo in vars_)
            if n == 15:
                opts = '<label class="opt-g">Teslim tarihi<input type="date" data-opt="Teslim tarihi"></label><label class="opt-g">Saat aralığı<select data-opt="Saat"><option>09:00–12:00</option><option>12:00–16:00</option><option>16:00–20:00</option></select></label><label class="opt-g">Kart notu<textarea data-opt="Not" rows="2" placeholder="Karta yazılacak not"></textarea></label>'
            if n == 16:
                opts += '<label class="opt-g">Pasta üstü yazı<input data-opt="Yazı" placeholder="İsteğe bağlı"></label>'
            relh = "".join(['<div class="pc"><a href="urun-%d.html"><img loading="lazy" src="%s" alt=""><h3>%s</h3></a><div><b>%s</b></div></div>' % (y["k"] + 1, ph(y["k"] + 3, 500, 600), E_(y["n"]), E_(y["p"])) for y in shop_items if y["k"] != k][:4])
            pages_out["urun-%d.html" % (k + 1)] = (x["n"], hero(x["n"], "", [("Ürünler", "urunler.html"), (x["n"], None)]) + sec_('<div class="pd" id="pd" data-id="%s" data-n="%s" data-p="%s" data-img="%s"><div class="gal"><img src="%s" alt="%s"><div class="th"><img src="%s" alt=""><img src="%s" alt=""></div></div><div><h1>%s</h1><div class="pr0">%s</div>%s<div class="buy"><input id="qty" type="number" min="1" value="1" aria-label="Adet"><button id="addc" class="b p">Sepete ekle</button><button id="buyn" class="b o">Hemen al</button></div><p class="hint" style="margin-top:16px"><a href="kargo-iade.html" style="text-decoration:underline">Kargo ve iade koşulları</a></p></div></div>' % (
                x["id"], E_(x["n"]), num(x["p"]), ph(k + 3, 300, 360), ph(k + 3, 1000, 1250), E_(x["n"]), ph(k + 4, 600, 600), ph(k + 5, 600, 600), E_(x["n"]), E_(x["p"]), opts)) + sec_('<h2 style="margin-bottom:24px">Bunlara da bakın</h2><div class="prg">%s</div>' % relh, "sf"), "product", None)
        pol = [("Kargo", "Siparişler 1–3 iş günü içinde kargoya verilir; takip numarası SMS ile gönderilir."), ("İade", "Teslimden sonra 14 gün içinde ayıpsız ürünü iade edebilirsiniz."), ("Ödeme", "Kartla ödeme güvenli ödeme sayfasında alınır; kart bilgisi sitede saklanmaz.")]
        pages_out["kargo-iade.html"] = ("Kargo ve iade", hero("Kargo ve iade", "", [("Kargo ve iade", None)]) + sec_('<div class="nar">%s</div>' % "".join("<details open><summary>%s</summary><p>%s</p></details>" % (a, b) for a, b in pol)), "x", None)
        if n == 17:
            f0 = c["form"]
            pages_out["tamir.html"] = ("Tamir kaydı", hero("Tamir kaydı", "Marka, model ve arızayı yazın; fiyatı ve süreyi size bildirelim.", [("Tamir", None)]) + sec_(form("tamir", "Tamir kaydı", [fld(f0[0]), fld(f0[1]), fld(f0[2], "area"), fld("Ad soyad"), fld("Telefon", typ="tel")], "Tamir kaydı oluştur", "Tamir kaydınız açıldı", "TM", side_contact)), "form", None)
        if n == 16:
            f0 = c["form"]
            pages_out["ozel-pasta.html"] = ("Özel pasta", hero("Özel pasta siparişi", "Kişi sayısı, tarih ve yazıyı bildirin; fiyat teklifi gönderelim.", [("Özel pasta", None)]) + sec_(form("pasta", "Özel pasta", [fld(x) for x in f0] + [fld("Ad soyad"), fld("Telefon", typ="tel"), fld("Ayrıntı", "area", False)], "Özel pasta iste", "Talebiniz alındı", "PS", side_contact)), "form", None)
    if fam == "yemek":
        cats = [cn for cn, _ in c["menu"]]
        tabs = "".join('<button data-f="%s" class="%s">%s</button>' % (E_(cn), "on" if j == 0 else "", E_(cn)) for j, cn in enumerate(cats)) + '<button data-f="" >Tümü</button>'
        rows = "".join('<div class="mi" data-cat="%s" data-id="%s" data-n="%s" data-p="%s" data-img="%s"><img loading="lazy" src="%s" alt=""><div><h3>%s</h3></div><b>%s</b><button class="b p s" onclick="OK.addP(this)">Ekle</button></div>' % (E_(x["cat"]), x["id"], E_(x["n"]), num(x["p"]), ph(x["k"] + 1, 160, 160), ph(x["k"] + 1, 300, 300), E_(x["n"]), E_(x["p"])) for x in shop_items)
        pages_out["menu.html"] = ("Menü ve paket sipariş", hero("Menü", "Ürünleri sepete ekleyin; paket sipariş veya gel-al seçin.", [("Menü", None)]) + sec_('<div class="fl">%s<span class="sp" id="cnt"></span></div><div class="mp2" id="menug">%s</div><p style="margin-top:24px"><a class="b p" href="sepet.html">Sepete git</a></p>' % (tabs, rows)), "filter", None)
        pages_out["rezervasyon.html"] = ("Rezervasyon", hero("Masa rezervasyonu", "Tarih, saat ve kişi sayısını yazın; onayı SMS ile gönderelim.", [("Rezervasyon", None)]) + sec_(form("rezervasyon", "Masa rezervasyonu", [fld("Ad soyad"), fld("Telefon", typ="tel"), fld("Tarih", typ="date"), fld("Saat", "select", True, ["12:00", "13:00", "14:00", "19:00", "20:00", "21:00"]), fld("Kişi sayısı", typ="number"), fld("Not", "area", False)], "Rezervasyon yap", "Rezervasyon talebiniz alındı", "RZ", side_contact)), "form", None)
    if buy:
        shop_href = {"yemek": "menu.html", "magaza": "urunler.html"}.get(fam, "paketler.html" if has_pk else "urunler.html")
        pages_out["sepet.html"] = ("Sepet", hero("Sepet", "", [("Sepet", None)]) + sec_('<div id="app" data-shop="%s"></div>' % shop_href), "cart", None)
        pages_out["odeme.html"] = ("Ödeme", hero("Ödeme", "", [("Sepet", "sepet.html"), ("Ödeme", None)]) + sec_('<div id="app" data-shop="%s" data-track="takip.html"></div>' % shop_href), "checkout", None)
        pages_out["hesabim.html"] = ("Hesabım", hero("Hesabım", "Siparişlerinizi, randevularınızı ve adreslerinizi görün.", [("Hesabım", None)]) + sec_('<div id="app"></div>'), "account", None)
        if "takip.html" not in pages_out:
            pages_out["takip.html"] = ("Sipariş takip", hero("Sipariş takip", "Sipariş numaranızı yazın.", [("Takip", None)]) + sec_('<div class="two"><div><form id="tf" class="ff box"><label>Takip numarası<input required placeholder="Örn. SPAB12C"></label><button class="b p">Sorgula</button></form><div id="tr" style="margin-top:18px"></div></div>' + side_contact + '</div>'), "track", None)
    # iletişim
    pages_out["iletisim.html"] = ("İletişim", hero("İletişim", "", [("İletişim", None)]) + sec_('<div class="two"><div class="box"><ul class="ct"><li><b>Adres</b>Atatürk Cad., Bornova / İzmir</li><li><b>Telefon</b><a href="tel:+905320000000">0532 000 00 00</a></li><li><b>Çalışma saatleri</b>Hafta içi 08:30–19:00 · Cumartesi 09:00–17:00</li></ul></div>' +
        '<div><form class="ff box" data-kind="mesaj" data-title="İletişim mesajı" data-p="MS">%s%s%s<button class="b p">Mesaj gönder</button></form><div class="done box ok2" hidden><h3>Mesajınız alındı</h3><p>Referans: <b class="no"></b>. En kısa sürede dönüyoruz.</p></div></div></div>' % (fld("Ad soyad"), fld("Telefon", typ="tel"), fld("Mesajınız", "area"))) +
        sec_('<div class="nar"><h2 style="margin-bottom:20px">Sık sorulanlar</h2>%s</div>' % "".join("<details><summary>%s</summary><p>%s</p></details>" % (E_(q), E_(a)) for q, a in SSS.get(fam, SSS["servis"])), "sf"), "form", None)
    return t, c, nav, L, foot_labels, pages_out, buy


def build(i):
    t, c, nav, L, foot_labels, pages_out, buy = gen(i)
    n = i + 1; fam = t[2]
    d = os.path.join(OUT, "%02d" % n); os.makedirs(d, exist_ok=True)
    ext0 = dict(shop=buy and (fam == "magaza" or n in (7, 10)) or fam == "yemek", nav=nav, links=L, foot_labels=foot_labels, cta=CTAP[fam], form_to=FORMTO.get(fam, "urunler.html") if fam != "magaza" else {16: "ozel-pasta.html", 17: "tamir.html"}.get(n, "urunler.html"), back="../index.html", css=PCSS.replace("--FH", "'%s'" % O.FAMN.get(t[4].split("/")[0].strip(), t[4].split("/")[0].strip())).replace("--FB", "'%s'" % t[4].split("/")[1].strip()), lib=LIB.replace("__K__", "ok%02d_" % n))
    for fn_, (title, content, jsn, D) in dict(pages_out, **{"index.html": (None, None, "x", None)}).items():
        e = dict(ext0, js="OK.init(%s,%s);" % (json.dumps(jsn), json.dumps(D, ensure_ascii=False)))
        if content is not None:
            e["content"] = content; e["title"] = title
        if jsn == "x" and content is not None:
            pass
        open(os.path.join(d, fn_), "w", encoding="utf-8").write(O.page(i, t, c, e))
    return sorted(list(pages_out) + ["index.html"])


if __name__ == "__main__":
    import sys
    os.makedirs(OUT, exist_ok=True)
    only = [int(x) for x in sys.argv[1:]] or range(1, 21)
    allp = {}
    for n in only:
        allp[n] = build(n - 1)
        print(n, len(allp[n]), "sayfa")
