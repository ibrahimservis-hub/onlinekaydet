# -*- coding: utf-8 -*-
"""Otomatik site üretici: seçilen temaya firma profilini (logo, telefon, WhatsApp, adres, slider, hizmetler, SSS, bölgeler...)
yerleştirir ve temanın üst/alt bilgisiyle çok sayfalı site üretir. Veritabanı bilmez; saf fonksiyonlardır.

Tema yapısı (38 temada aynı): <body><input id=mn> + <div class="ed" data-nm="Menü|Mobil menü|...|Alt bilgi|Mobil bar"> blokları + <script>.
"""
import html as _h
import re

_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
E = _h.escape

SECTORS = {
    "kombi": "Kombi", "klima": "Klima", "beyaz_esya": "Beyaz eşya", "bilgisayar": "Bilgisayar",
    "elektrik": "Elektrik", "elektronik": "Elektronik", "guvenlik": "Güvenlik sistemi", "tesisat": "Tesisat",
}

DEFAULTS = {
    "kombi": {
        "services": [("Yıllık kombi bakımı", "Kombinizin yanma ve emniyet kontrollerini yapar, filtre ve eşanjörü temizler, ölçüm sonuçlarını size anlatırız."),
                     ("Kombi arıza tespiti ve onarım", "Ekrandaki hata kodunu okur, arızayı yerinde bulur, değişecek parça varsa fiyatını önceden söyleriz."),
                     ("Petek temizliği", "Isınmayan veya geç ısınan petekleri cihazla temizler, sistem dengesini ayarlarız."),
                     ("Kombi montajı ve yer değişimi", "Yeni kombinizi kurar, baca ve gaz bağlantılarını kurallara uygun yapar, çalıştırıp teslim ederiz."),
                     ("Su basıncı ve kaçak kontrolü", "Basınç düşmesi, su kaçağı ve genleşme tankı sorunlarını bulur ve giderir.")],
        "faq": [("Kombi bakımı yılda kaç kez yapılmalı?", "Yılda bir kez, kış başlamadan önce yaptırmanızı öneririz."),
                ("Hata kodu veren kombi ne zaman gelmeli?", "Kodu söylemeniz yeterli; telefonla ön bilgi verir, uygun saat için randevu oluştururuz."),
                ("Fiyatı önceden öğrenebilir miyim?", "Arıza tespitinden sonra yapılacak işlemi ve ücreti size söyler, onayınızı alırız.")],
    },
    "klima": {
        "services": [("Klima montajı", "Duvara uygun yer seçer, bakır tesisatı ve drenajı düzgün çeker, vakumlayıp çalıştırarak teslim ederiz."),
                     ("Klima bakımı ve temizliği", "İç ve dış ünite temizliği, filtre ve gaz basıncı kontrolü yapılır."),
                     ("Klima arıza onarımı", "Soğutmama, su damlatma, ses ve açılmama sorunlarını yerinde tespit edip onarırız."),
                     ("Gaz dolumu", "Gaz kaçağını bulur, onarır ve cihaza uygun gazı ölçülü şekilde doldururuz."),
                     ("Söküm ve yer değişimi", "Klimanızı söker, yeni yerine monte eder ve çalıştırırız.")],
        "faq": [("Klima bakımı ne zaman yapılmalı?", "Sezon başlamadan önce yılda bir kez yaptırmanızı öneririz."),
                ("Montaj ne kadar sürer?", "Standart bir montaj çoğunlukla birkaç saat içinde tamamlanır; tesisat uzunluğuna göre değişir."),
                ("Fiyatı önceden öğrenebilir miyim?", "Keşif sonrası yapılacak işlemi ve ücreti önceden söyleriz.")],
    },
    "beyaz_esya": {
        "services": [("Çamaşır makinesi tamiri", "Su almama, sıkma ve ses sorunlarını yerinde tespit edip onarırız."),
                     ("Bulaşık makinesi tamiri", "Yıkamama, su boşaltmama ve kapı sorunlarında hızlı servis veririz."),
                     ("Buzdolabı tamiri", "Soğutmama, buzlanma ve ses sorunlarının nedenini bulur ve gideririz."),
                     ("Kurutma makinesi ve fırın servisi", "Isınmama ve program hatalarını kontrol eder, gerekirse parça değişimi yaparız."),
                     ("Yedek parça temini", "Cihazınıza uygun yedek parçayı temin eder ve takarız.")],
        "faq": [("Tamir mi yeni cihaz mı almalıyım?", "Arıza tespitinde tamirin değip değmeyeceğini açıkça söyleriz."),
                ("Servis ücreti nasıl belirleniyor?", "Arıza tespitinden sonra parça ve işçilik için net fiyat veririz."),
                ("Her marka için servis veriyor musunuz?", "Yaygın tüm markalar için hizmet veriyoruz; cihaz modelinizi telefonda söylemeniz yeterli.")],
    },
    "bilgisayar": {
        "services": [("Bilgisayar ve laptop tamiri", "Açılmama, yavaşlık, ekran ve klavye sorunlarını inceler ve onarırız."),
                     ("Format ve program kurulumu", "Verilerinizi yedekleyerek temiz kurulum yapar, gerekli programları yükleriz."),
                     ("Virüs ve yavaşlık temizliği", "Zararlı yazılımları temizler, bilgisayarınızı eski hızına yaklaştırırız."),
                     ("Veri kurtarma", "Silinen veya erişilemeyen dosyalarınızı kurtarmayı deneriz."),
                     ("Ağ ve modem kurulumu", "Ev ve ofis internet ağınızı kurar, çekim sorunlarını gideririz.")],
        "faq": [("Verilerim silinir mi?", "İşleme başlamadan önce yedek alınır; sizin onayınız olmadan veriye dokunulmaz."),
                ("Onarım ne kadar sürer?", "Basit işlemler aynı gün biter; parça gerektiren işlerde süreyi önceden söyleriz."),
                ("Fiyatı önceden öğrenebilir miyim?", "İnceleme sonrası yapılacak işlemi ve ücreti yazılı olarak bildiririz.")],
    },
    "elektrik": {
        "services": [("Elektrik arıza onarımı", "Sigorta atması, kaçak akım ve priz sorunlarını yerinde bulur ve gideririz."),
                     ("Pano ve sigorta düzenleme", "Eski panoları yeniler, topraklama ve kaçak akım rölesi bağlarız."),
                     ("Aydınlatma montajı", "Avize, spot ve dış aydınlatmayı projeye uygun şekilde kurarız."),
                     ("Priz ve anahtar değişimi", "Yıpranmış priz ve anahtarları güvenli şekilde yeniler."),
                     ("Kablo ve tesisat yenileme", "Ev ve iş yeri tesisatını yenilemek için keşif yapar, fiyat veririz.")],
        "faq": [("Sigorta sürekli atıyor, ne yapmalıyım?", "Cihazları fişten çekip bizi arayın; nedenini yerinde tespit ederiz."),
                ("Acil arızaya geliyor musunuz?", "Çalışma saatlerimiz içinde en kısa sürede ekip yönlendiririz."),
                ("Fiyatı önceden öğrenebilir miyim?", "Keşif sonrası yapılacak işin fiyatını önceden söyleriz.")],
    },
    "elektronik": {
        "services": [("Televizyon tamiri", "Görüntü, ses ve açılmama sorunlarını inceler ve onarırız."),
                     ("Anakart ve kart tamiri", "Elektronik kartlarda arıza tespiti yapar ve parça düzeyinde onarırız."),
                     ("Küçük ev aleti tamiri", "Süpürge, ütü, mikser gibi cihazların arızalarını gideririz."),
                     ("Ses sistemi ve uydu kurulumu", "Ses sistemlerini ve uydu çanağını kurar, ayarlarını yaparız."),
                     ("Yedek parça temini", "Cihazınıza uygun elektronik parçayı temin eder ve takarız.")],
        "faq": [("Tamir edilemeyen cihaz oluyor mu?", "Tamiri değmeyen cihazları baştan açıkça söyler, gereksiz ücret almayız."),
                ("Arıza tespiti ücretli mi?", "İnceleme sonrası ücret konusunda önceden bilgi veririz."),
                ("Onarım süresi nedir?", "Basit arızalar aynı gün biter; parça bekleyen işlerde süreyi bildiririz.")],
    },
    "guvenlik": {
        "services": [("Güvenlik kamerası kurulumu", "Evinize veya iş yerinize uygun kamera sistemini keşif yaparak kurarız."),
                     ("Alarm sistemi kurulumu", "Hırsız ve yangın alarmı sistemlerini kurar, telefonunuza bağlarız."),
                     ("Kamera ve kayıt cihazı bakımı", "Mevcut sisteminizin görüntü ve kayıt sorunlarını giderir, bakımını yaparız."),
                     ("Kartlı geçiş ve diyafon", "Kapı kontrol, kartlı geçiş ve diyafon sistemleri kurarız."),
                     ("Uzaktan izleme ayarı", "Kameralarınızı telefonunuzdan izleyecek şekilde ayarlarız.")],
        "faq": [("Kamera görüntüleri ne kadar saklanır?", "Kayıt süresi disk kapasitesine ve kamera sayısına göre değişir; kurulumda hesaplayıp söyleriz."),
                ("Keşif ücretli mi?", "Keşif ve fiyat bilgisi için bizi arayın; ayrıntıyı telefonda söyleyelim."),
                ("Mevcut sistemime ekleme yapılır mı?", "Uyumlu olduğu sürece mevcut sisteme kamera ve cihaz ekleyebiliriz.")],
    },
    "tesisat": {
        "services": [("Su kaçağı tespiti", "Duvar ve zemin içindeki kaçakları cihazla bulur, kırmadan müdahale etmeye çalışırız."),
                     ("Tıkanıklık açma", "Lavabo, klozet ve gider tıkanıklıklarını makineyle açarız."),
                     ("Musluk ve batarya değişimi", "Damlatan veya bozulan armatürleri yeniler."),
                     ("Petek ve kombi tesisatı", "Isıtma tesisatını yeniler, petek ve boru değişimi yaparız."),
                     ("Banyo ve mutfak tesisatı", "Yenileme sırasında su ve gider hatlarını düzenleriz.")],
        "faq": [("Su kaçağını duvarı kırmadan bulabilir misiniz?", "Cihazla yerini belirleriz; kırma gerekiyorsa en küçük alanda çalışırız."),
                ("Acil tıkanıklığa gelir misiniz?", "Çalışma saatlerimiz içinde en kısa sürede ekip yönlendiririz."),
                ("Fiyatı önceden öğrenebilir miyim?", "Yerinde inceleme sonrası işin ücretini önceden söyleriz.")],
    },
}

LINK_ICON = {"instagram": "Instagram", "facebook": "Facebook", "x": "X", "youtube": "YouTube", "tiktok": "TikTok", "linkedin": "LinkedIn"}


def slugify(s, n=40):
    s = re.sub(r"[^a-z0-9]+", "-", str(s or "").translate(_TR).lower()).strip("-")
    return (s[:n].strip("-")) or "sayfa"


def digits(s):
    return "".join(c for c in str(s or "") if c.isdigit())


def phone10(s):
    d = digits(s)
    return d[-10:] if len(d) >= 10 else ""


def phone_fmt(d10):
    return "0%s %s %s %s" % (d10[:3], d10[3:6], d10[6:8], d10[8:])


def paras(s):
    parts = [p.strip() for p in re.split(r"\n\s*\n|\r\n\s*\r\n", str(s or "")) if p.strip()]
    if len(parts) <= 1:
        parts = [p.strip() for p in str(s or "").split("\n") if p.strip()]
    return "".join("<p>%s</p>" % E(p) for p in parts)


def effective(profile, sector):
    """Profilde boş bırakılan yerleri sektör varsayılanlarıyla doldurur."""
    p = dict(profile or {})
    d = DEFAULTS.get(sector) or DEFAULTS["tesisat"]
    sv = [s for s in (p.get("services") or []) if (s.get("t") or "").strip()]
    p["services"] = sv or [{"t": a, "d": b} for a, b in d["services"]]
    fq = [f for f in (p.get("faq") or []) if (f.get("q") or "").strip()]
    p["faq"] = fq or [{"q": a, "a": b} for a, b in d["faq"]]
    p["regions"] = [r.strip() for r in (p.get("regions") or []) if str(r).strip()][:12]
    p["noun"] = SECTORS.get(sector, "Teknik")
    return p


def page_index(ctx):
    """Üretilen sayfa listesi: [{slug,title,kind,nav}]"""
    p = ctx["p"]
    out = [{"slug": "hakkimizda", "title": "Hakkımızda", "kind": "about", "nav": True},
           {"slug": "hizmetlerimiz", "title": "Hizmetlerimiz", "kind": "services", "nav": True}]
    if p.get("gallery"):
        out.append({"slug": "galeri", "title": "Galeri", "kind": "gallery", "nav": True})
    out.append({"slug": "nasil-calisiyoruz", "title": "Nasıl Çalışıyoruz", "kind": "process", "nav": False})
    out.append({"slug": "sss", "title": "Sık Sorulan Sorular", "kind": "faq", "nav": True})
    if p["regions"]:
        out.append({"slug": "hizmet-bolgeleri", "title": "Hizmet Bölgeleri", "kind": "regions", "nav": False})
    out.append({"slug": "iletisim", "title": "İletişim", "kind": "contact", "nav": True})
    seen = {x["slug"] for x in out}
    for i, s in enumerate(p["services"]):
        sl = "hizmet-" + slugify(s["t"], 34)
        while sl in seen:
            sl += "-%d" % (i + 2)
        seen.add(sl)
        out.append({"slug": sl, "title": s["t"], "kind": "service", "idx": i, "nav": False})
    for i, r in enumerate(p["regions"]):
        sl = "bolge-" + slugify(r, 30)
        while sl in seen:
            sl += "-%d" % (i + 2)
        seen.add(sl)
        out.append({"slug": sl, "title": "%s %s Servisi" % (r, ctx["p"]["noun"]), "kind": "region", "idx": i, "nav": False})
    return out


# ------------------------------------------------------------------ tema yapısı
_ED = re.compile(r'<div class="ed" data-nm="([^"]*)">')


def split_blocks(h):
    ms = list(_ED.finditer(h))
    if len(ms) < 3:
        return None
    pre = h[:ms[0].start()]
    blocks = []
    end = len(h)
    for i, m in enumerate(ms):
        if i + 1 < len(ms):
            end = ms[i + 1].start()
        else:
            s = h.find("<script", m.end())
            end = s if s > 0 else (h.rfind("</body>") if h.rfind("</body>") > 0 else len(h))
        blocks.append([m.group(1), h[m.start():end]])
    return pre, blocks, h[end:]


def join_blocks(pre, blocks, tail):
    return pre + "".join(b[1] for b in blocks) + tail


CSS = """<style data-spx-auto>
.spx-logo{height:42px;width:auto;max-width:200px;object-fit:contain;display:block}
.spx-sl{position:relative;overflow:hidden;background:var(--dk,#111)}
.spx-sl-t{position:relative;aspect-ratio:16/6;min-height:240px;max-height:620px}
.spx-s{position:absolute;inset:0;opacity:0;transition:opacity .7s ease;pointer-events:none}
.spx-s.on{opacity:1;pointer-events:auto}
.spx-s img{width:100%;height:100%;object-fit:cover;display:block}
.spx-s figcaption{position:absolute;inset:auto 0 0 0;padding:clamp(18px,4vw,46px) clamp(18px,5vw,64px) clamp(34px,5vw,56px);color:#fff;background:linear-gradient(to top,rgba(0,0,0,.66),rgba(0,0,0,0))}
.spx-s figcaption b{display:block;font:var(--hw,700) clamp(22px,4vw,42px)/1.1 var(--fd,inherit);letter-spacing:var(--ht,0)}
.spx-s figcaption span{display:block;margin-top:8px;max-width:640px;font-size:clamp(14px,1.6vw,18px);opacity:.92}
.spx-sl-d{position:absolute;left:0;right:0;bottom:14px;display:flex;justify-content:center;gap:8px;z-index:2}
.spx-sl-d button{width:11px;height:11px;border-radius:50%;border:0;padding:0;background:#fff;opacity:.45;cursor:pointer}
.spx-sl-d button.on{background:var(--ac);opacity:1;transform:scale(1.25)}
.spx-sl-a{position:absolute;top:50%;transform:translateY(-50%);width:46px;height:46px;border-radius:50%;border:0;background:rgba(0,0,0,.42);color:#fff;display:grid;place-items:center;cursor:pointer;z-index:2}
.spx-sl-a.p{left:12px}.spx-sl-a.n{right:12px}
@media(max-width:700px){.spx-sl-t{aspect-ratio:4/3}.spx-sl-a{width:40px;height:40px}}
.spx-ph{background:var(--sf);border-bottom:1px solid var(--ln);padding:clamp(44px,7vw,92px) 0 clamp(28px,4vw,52px)}
.spx-ph h1{margin:10px 0 0;font-family:var(--fd);font-weight:var(--hw);letter-spacing:var(--ht);font-size:clamp(30px,5vw,54px);line-height:1.1;color:var(--hc,var(--ink))}
.spx-ph p{margin:14px 0 0;max-width:660px;color:var(--mut);font-size:1.05rem}
.spx-c{max-width:960px}
.spx-c p{margin:0 0 16px;line-height:1.75;font-size:1.05rem}
.spx-c h2{font-family:var(--fd);font-weight:var(--hw);letter-spacing:var(--ht);font-size:clamp(22px,3vw,30px);margin:34px 0 12px}
.spx-g{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px}
.spx-k{display:block;background:var(--fbg,var(--sf));border:1px solid var(--ln);border-radius:var(--r);padding:22px;color:inherit;text-decoration:none;transition:transform .18s,border-color .18s}
.spx-k:hover{transform:translateY(-3px);border-color:var(--ac)}
.spx-k b{display:block;font-family:var(--fd);font-weight:var(--hw);font-size:1.15rem;margin-bottom:8px}
.spx-k span{display:block;color:var(--mut);line-height:1.6;font-size:.97rem}
.spx-gal{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.spx-gal img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:var(--r);display:block}
.spx-q{border:1px solid var(--ln);border-radius:var(--r);background:var(--fbg,var(--sf));margin:0 0 10px}
.spx-q summary{cursor:pointer;padding:18px 20px;font-weight:700;list-style:none}
.spx-q summary::-webkit-details-marker{display:none}
.spx-q summary:after{content:"+";float:right;font-size:1.3rem;line-height:1;color:var(--ac)}
.spx-q[open] summary:after{content:"–"}
.spx-q div{padding:0 20px 18px;color:var(--mut);line-height:1.7}
.spx-ct{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:28px;align-items:start}
@media(max-width:800px){.spx-ct{grid-template-columns:1fr}}
.spx-ct dl{margin:0}.spx-ct dt{font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin-top:18px}
.spx-ct dd{margin:4px 0 0;font-size:1.1rem}.spx-ct dd a{color:inherit}
.spx-ct iframe{width:100%;height:340px;border:0;border-radius:var(--r);background:var(--sf)}
.spx-cta{margin-top:40px;padding:clamp(24px,4vw,40px);background:var(--dk);color:#fff;border-radius:var(--r);display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:18px}
.spx-cta b{font-family:var(--fd);font-weight:var(--hw);font-size:clamp(20px,3vw,28px)}
.spx-cta .row{display:flex;flex-wrap:wrap;gap:10px}
.spx-cta .btn.o{background:transparent;color:#fff;border-color:#ffffff88}
.spx-fl{display:flex;flex-wrap:wrap;gap:8px 18px;padding:18px 0;border-top:1px solid var(--ln);font-size:.92rem}
.spx-fl a{color:inherit;opacity:.85}
.spx-rl{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.spx-rl a{border:1px solid var(--ln);border-radius:999px;padding:8px 16px;color:inherit;text-decoration:none;font-size:.95rem}
.spx-rl a:hover{border-color:var(--ac);color:var(--ac)}
</style>"""

SLIDER_JS = ("<script data-spx-auto>(function(){var r=document.querySelector('.spx-sl');if(!r)return;var s=r.querySelectorAll('.spx-s'),d=r.querySelectorAll('.spx-sl-d button'),i=0,t;"
             "function g(n){i=(n+s.length)%s.length;for(var k=0;k<s.length;k++){s[k].classList.toggle('on',k==i);if(d[k])d[k].classList.toggle('on',k==i)}}"
             "function a(){clearInterval(t);if(s.length>1)t=setInterval(function(){g(i+1)},5200)}"
             "var p=r.querySelector('.p'),n=r.querySelector('.n');if(p)p.onclick=function(){g(i-1);a()};if(n)n.onclick=function(){g(i+1);a()};"
             "for(var k=0;k<d.length;k++)(function(k){d[k].onclick=function(){g(k);a()}})(k);g(0);a()})()</script>")

_CH_L = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>'
_CH_R = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>'


def slider_html(ctx):
    sl = ctx["p"].get("slides") or []
    if not sl:
        return ""
    figs = []
    for i, s in enumerate(sl):
        cap = ""
        if (s.get("t") or s.get("d")):
            cap = "<figcaption>%s%s</figcaption>" % (("<b>%s</b>" % E(s.get("t"))) if s.get("t") else "", ("<span>%s</span>" % E(s.get("d"))) if s.get("d") else "")
        figs.append('<figure class="spx-s%s" style="margin:0"><img src="%s" alt="%s"%s>%s</figure>' % (" on" if i == 0 else "", E(ctx["img"](s["k"])), E(s.get("t") or ctx["name"]), "" if i == 0 else ' loading="lazy"', cap))
    nav = ""
    if len(sl) > 1:
        nav = ('<button class="spx-sl-a p" aria-label="Önceki">%s</button><button class="spx-sl-a n" aria-label="Sonraki">%s</button><div class="spx-sl-d">%s</div>'
               % (_CH_L, _CH_R, "".join('<button aria-label="Slayt %d"></button>' % (i + 1) for i in range(len(sl)))))
    return '<div class="ed" data-nm="Slider"><section class="spx-sl" aria-label="Öne çıkanlar"><div class="spx-sl-t">%s</div>%s</section></div>' % ("".join(figs), nav)


# ------------------------------------------------------------------ ana sayfa
_ADDR = re.compile(r"Atatürk Cad\. No:12(?:(?:,| /| ·) (?!Hafta)[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)?")
_HOURS = re.compile(r"Hafta içi 08:30 ?[–-] ?19:00")


def apply_profile(raw, th, ctx):
    """Ham tema HTML'ine firma bilgilerini yerleştirir (ana sayfa)."""
    h = raw.replace("__API_URL__", "/api").replace("__PORTAL_URL__", "#")
    name = ctx["name"]
    if th and th.get("name") and name:
        h = h.replace(th["name"], E(name))
    d = phone10(ctx["tel"])
    w = phone10(ctx["p"].get("whatsapp")) or d
    if w:
        h = h.replace("wa.me/905320000000", "wa.me/90" + w)
    if d:
        h = h.replace("905320000000", "90" + d).replace("0532 000 00 00", phone_fmt(d))
    if ctx["p"].get("address"):
        h = _ADDR.sub(lambda m: E(ctx["p"]["address"]), h)
    if ctx["p"].get("hours"):
        h = _HOURS.sub(lambda m: E(ctx["p"]["hours"]), h)
    if ctx.get("logo"):
        img = '<img class="spx-logo" src="%s" alt="%s">' % (E(ctx["logo"]), E(name))
        h = re.sub(r'(<(?:a|div) class="lg[^"]*"[^>]*>)<span class="lm[^"]*">[^<]*</span>', lambda m: m.group(1) + img, h)
        if "spx-logo" not in h:
            h = re.sub(r'(<a class="lg[^"]*"[^>]*>)(<span class="ln">)', lambda m: m.group(1) + img + m.group(2), h)
        if ctx["p"].get("logo_only"):
            h = re.sub(r'(<img class="spx-logo"[^>]*>)<span class="ln">[^<]*</span>', r"\1", h)
    if ctx["p"].get("slogan"):
        h = re.sub(r"(<section class=\"hr[^>]*>.*?<h1[^>]*>).*?(</h1>)", lambda m: m.group(1) + E(ctx["p"]["slogan"]) + m.group(2), h, count=1, flags=re.S)
    parts = split_blocks(h)
    if not parts:
        return h
    pre, blocks, tail = parts
    idx = page_index(ctx)
    navs = [x for x in idx if x["nav"]]
    for b in blocks:
        if b[0] == "Menü":
            nv = "".join('<a href="/%s">%s</a>' % (x["slug"], E(x["title"])) for x in navs[:1])
            b[1] = b[1].replace("</nav>", nv + "</nav>", 1) if "</nav>" in b[1] else b[1]
        elif b[0] == "Mobil menü":
            nv = "".join('<a href="/%s">%s</a>' % (x["slug"], E(x["title"])) for x in navs)
            i = b[1].find('class="dl">')
            if i > 0:
                j = b[1].find("</div>", i)
                b[1] = b[1][:j] + nv + b[1][j:]
        elif b[0] == "Alt bilgi":
            b[1] = b[1].replace("</footer>", footer_links(ctx, idx) + "</footer>", 1)
    if ctx["p"].get("slides"):
        k = next((i for i, b in enumerate(blocks) if b[0] == "Ana görsel"), 2)
        blocks.insert(k, ["Slider", slider_html(ctx)])
    out = join_blocks(pre, blocks, tail)
    out = out.replace("</head>", CSS + "</head>", 1)
    if ctx["p"].get("slides"):
        out = out.replace("</body>", SLIDER_JS + "</body>", 1) if "</body>" in out else out + SLIDER_JS
    if ctx.get("seo_desc"):
        out = _set_desc(out, ctx["seo_desc"])
    return out


def footer_links(ctx, idx):
    links = ['<a href="/%s">%s</a>' % (x["slug"], E(x["title"])) for x in idx if x["kind"] in ("about", "services", "gallery", "process", "faq", "regions", "contact")]
    soc = ctx["p"].get("social") or {}
    for k, lab in LINK_ICON.items():
        u = str(soc.get(k) or "").strip()
        if u:
            if not re.match(r"https?://", u):
                u = "https://" + u.lstrip("/@")
            links.append('<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(u), lab))
    if not links:
        return ""
    return '<div class="w spx-fl">%s</div>' % "".join(links)


def _set_desc(h, desc):
    h = re.sub(r'<meta name="description"[^>]*>', "", h, count=1)
    return h.replace("</title>", '</title><meta name="description" content="%s">' % E(desc[:300]), 1)


# ------------------------------------------------------------------ iç sayfalar
def _cta(ctx):
    d = phone10(ctx["tel"])
    w = phone10(ctx["p"].get("whatsapp")) or d
    btn = []
    if d:
        btn.append('<a class="btn" href="tel:+90%s">Hemen arayın · %s</a>' % (d, phone_fmt(d)))
    if w:
        btn.append('<a class="btn o" href="https://wa.me/90%s" target="_blank" rel="noopener">WhatsApp</a>' % w)
    btn.append('<a class="btn o" href="/#randevu">Randevu al</a>')
    return '<div class="spx-cta"><b>Bize ulaşın, size dönelim</b><div class="row">%s</div></div>' % "".join(btn)


def _page_body(ctx, pg, idx):
    p, name, noun = ctx["p"], ctx["name"], ctx["p"]["noun"]
    city = (ctx.get("city") or "").strip()
    k = pg["kind"]
    sv_links = {x["idx"]: x for x in idx if x["kind"] == "service"}
    if k == "about":
        txt = p.get("about") or ("%s, %s alanında hizmet veren bir servis firmasıdır. Arızayı önce yerinde tespit eder, yapılacak işlemi ve ücreti size anlatır, onayınızla başlarız.\n\n"
                                 "Aradığınızda bilgi verir, uygun saati birlikte belirleriz. Yaptığımız işlerin kaydı tutulur; sorunuz olursa bize her zaman ulaşabilirsiniz." % (name, noun.lower() + (" (" + city + ")" if city else "")))
        return "", paras(txt)
    if k == "services":
        cards = "".join('<a class="spx-k" href="/%s"><b>%s</b><span>%s</span></a>' % (sv_links[i]["slug"], E(s["t"]), E(s.get("d") or "")) for i, s in enumerate(p["services"]) if i in sv_links)
        return "Hizmetlerimiz", '<div class="spx-g">%s</div>' % cards
    if k == "gallery":
        return "Çalışmalarımızdan", '<div class="spx-gal">%s</div>' % "".join('<img src="%s" alt="%s" loading="lazy">' % (E(ctx["img"](g["k"])), E(name)) for g in p["gallery"])
    if k == "process":
        steps = [("Bizi arayın", "Telefon veya WhatsApp'tan sorununuzu anlatın."), ("Randevu verelim", "Size uygun günü ve saati birlikte belirleriz."),
                 ("Tespit ve fiyat", "Sorunu yerinde bulur, yapılacak işi ve ücreti onayınıza sunarız."), ("İşlem ve teslim", "Onayınızla işi yapar, çalıştığını birlikte kontrol ederiz.")]
        return "", '<div class="spx-g">%s</div>' % "".join('<div class="spx-k"><b>%d. %s</b><span>%s</span></div>' % (i + 1, E(a), E(b)) for i, (a, b) in enumerate(steps))
    if k == "faq":
        return "", "".join('<details class="spx-q"><summary>%s</summary><div>%s</div></details>' % (E(f["q"]), E(f.get("a") or "")) for f in p["faq"])
    if k == "regions":
        rl = {x["idx"]: x for x in idx if x["kind"] == "region"}
        return "", "<p>%s hizmet verdiğimiz bölgeler:</p><div class=\"spx-rl\">%s</div>" % (E(name), "".join('<a href="/%s">%s</a>' % (rl[i]["slug"], E(r)) for i, r in enumerate(p["regions"]) if i in rl))
    if k == "contact":
        d = phone10(ctx["tel"])
        w = phone10(p.get("whatsapp"))
        rows = ""
        if d:
            rows += '<dt>Telefon</dt><dd><a href="tel:+90%s">%s</a></dd>' % (d, phone_fmt(d))
        if w:
            rows += '<dt>WhatsApp</dt><dd><a href="https://wa.me/90%s" target="_blank" rel="noopener">%s</a></dd>' % (w, phone_fmt(w))
        if p.get("email"):
            rows += '<dt>E-posta</dt><dd><a href="mailto:%s">%s</a></dd>' % (E(p["email"]), E(p["email"]))
        if p.get("address"):
            rows += "<dt>Adres</dt><dd>%s</dd>" % E(p["address"])
        if p.get("hours"):
            rows += "<dt>Çalışma saatleri</dt><dd>%s</dd>" % E(p["hours"])
        mp = ""
        if p.get("address"):
            from urllib.parse import quote
            mp = '<iframe loading="lazy" title="Harita" src="https://maps.google.com/maps?q=%s&output=embed"></iframe>' % quote(p["address"])
        return "", '<div class="spx-ct"><dl>%s</dl><div>%s</div></div>' % (rows, mp)
    if k == "service":
        s = p["services"][pg["idx"]]
        others = "".join('<a href="/%s">%s</a>' % (x["slug"], E(x["title"])) for x in idx if x["kind"] == "service" and x["idx"] != pg["idx"])
        body = paras(s.get("d") or "") or ""
        body += paras("%s olarak %s için arayabilir veya WhatsApp'tan yazabilirsiniz. Önce sorunu dinler, gerekiyorsa yerinde inceler, yapılacak işlemi ve ücreti onayınızla başlamadan söyleriz." % (name, s["t"].lower()))
        if city:
            body += paras("%s ve çevresinde hizmet veriyoruz." % city)
        return "", body + ('<h2>Diğer hizmetlerimiz</h2><div class="spx-rl">%s</div>' % others if others else "")
    if k == "region":
        r = p["regions"][pg["idx"]]
        others = "".join('<a href="/%s">%s</a>' % (x["slug"], E(p["regions"][x["idx"]])) for x in idx if x["kind"] == "region" and x["idx"] != pg["idx"])
        body = paras("%s olarak %s bölgesinde %s hizmeti veriyoruz. Aradığınızda sorunu dinler, uygun saati birlikte belirleriz." % (name, r, noun.lower()))
        body += "<h2>%s içinde yaptığımız işler</h2><div class=\"spx-rl\">%s</div>" % (E(r), "".join('<a href="/%s">%s</a>' % (sv_links[i]["slug"], E(s["t"])) for i, s in enumerate(p["services"]) if i in sv_links))
        return "", body + ('<h2>Diğer bölgeler</h2><div class="spx-rl">%s</div>' % others if others else "")
    return "", ""


_IMVAR = re.compile(r"--im\d?:url\(data:[^)]*\)")


def render_page(home_html, ctx, slug):
    """Üretilen iç sayfa: (html, title) ya da None."""
    idx = page_index(ctx)
    pg = next((x for x in idx if x["slug"] == slug), None)
    if not pg:
        return None
    sub, content = _page_body(ctx, pg, idx)
    out = assemble(home_html, ctx, pg["title"], content)
    return (out, pg["title"]) if out else None


def assemble(home_html, ctx, title, content):
    """Ana sayfanın menü + alt bilgi + mobil çubuğuyla, verilen içerikten sayfa kurar."""
    parts = split_blocks(home_html)
    if not parts:
        return None
    pre, blocks, tail = parts
    keep = []
    for b in blocks:
        if b[0] in ("Menü", "Mobil menü", "Alt bilgi", "Mobil bar"):
            keep.append([b[0], re.sub(r'href="#([^"]*)"', lambda m: 'href="/%s"' % (("#" + m.group(1)) if m.group(1) not in ("", "top") else ""), b[1])])
    main = ('<div class="ed" data-nm="İçerik"><section class="spx-ph"><div class="w"><span class="eyebrow">%s</span><h1>%s</h1></div></section>'
            '<section class="sec"><div class="w spx-c">%s%s</div></section></div>' % (E(ctx["name"]), E(title), content, _cta(ctx)))
    out_blocks = [b for b in keep if b[0] in ("Menü", "Mobil menü")] + [["İçerik", main]] + [b for b in keep if b[0] in ("Alt bilgi", "Mobil bar")]
    pre2 = _IMVAR.sub(lambda m: m.group(0).split(":")[0] + ":none", pre)
    out = join_blocks(pre2, out_blocks, tail)
    out = re.sub(r"<title>.*?</title>", "<title>%s · %s</title>" % (E(title), E(ctx["name"])), out, count=1, flags=re.S)
    out = _set_desc(out, "%s — %s. %s" % (title, ctx["name"], ("Tel: " + phone_fmt(phone10(ctx["tel"]))) if phone10(ctx["tel"]) else ""))
    return out.replace("</head>", CSS + "</head>", 1)


def sitemap(ctx, host, extra=()):
    base = "https://" + host
    urls = [base + "/"] + [base + "/" + x["slug"] for x in page_index(ctx)] + [base + "/" + s for s in extra]
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % "".join("<url><loc>%s</loc></url>" % E(u) for u in urls)
