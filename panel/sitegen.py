# -*- coding: utf-8 -*-
"""Otomatik site üretici: seçilen temaya firma profilini (logo, telefon, WhatsApp, adres, slider, hizmetler, SSS, bölgeler...)
yerleştirir ve temanın üst/alt bilgisiyle çok sayfalı site üretir. Veritabanı bilmez; saf fonksiyonlardır.

Tema yapısı (38 temada aynı): <body><input id=mn> + <div class="ed" data-nm="Menü|Mobil menü|...|Alt bilgi|Mobil bar"> blokları + <script>.
"""
import html as _h
import re, json

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

import sektor_ek as _sek
for _k, _v in _sek.NEW.items():
    SECTORS[_k] = _v["name"].split(" &")[0]
    DEFAULTS[_k] = {"services": list(_v["site"]["services"]), "faq": list(_v["site"]["faq"])}

LINK_ICON = {"instagram": "Instagram", "facebook": "Facebook", "x": "X", "youtube": "YouTube", "tiktok": "TikTok", "linkedin": "LinkedIn"}


_SVG = {
 "instagram": '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.3" cy="6.7" r="1" fill="currentColor" stroke="none"/></svg>',
 "facebook": '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M13.5 21v-7.5H16l.5-3h-3V8.6c0-.9.3-1.5 1.6-1.5H16.6V4.4c-.3 0-1.2-.1-2.3-.1-2.3 0-3.8 1.4-3.8 3.9v2.3H8v3h2.5V21z"/></svg>',
 "x": '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M17.8 3h3l-6.6 7.5L22 21h-6.1l-4.8-6.3L5.6 21h-3l7-8L2 3h6.2l4.3 5.7zm-1 16.2h1.7L7.3 4.7H5.5z"/></svg>',
 "youtube": '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M21.6 7.2a2.5 2.5 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 0 0 2.4 7.2C2 8.8 2 12 2 12s0 3.2.4 4.8a2.5 2.5 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.5 2.5 0 0 0 1.8-1.8c.4-1.6.4-4.8.4-4.8s0-3.2-.4-4.8zM10 15V9l5.2 3z"/></svg>',
 "tiktok": '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M16.6 3c.3 2.4 1.7 3.9 4 4v3.1c-1.5.1-2.8-.4-4-1.200V15a6 6 0 1 1-6-6c.3 0 .6 0 .9.1v3.2a2.900 2.900 0 1 0 2 2.700V3z"/></svg>',
 "linkedin": '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M4.500 8.500h3.500V20H4.500zM6.300 3a2 2 0 1 1 0 4 2 2 0 0 1 0-4zM10 8.500h3.300v1.600c.5-.9 1.700-1.900 3.500-1.900 3.600 0 4.200 2.400 4.200 5.400V20h-3.500v-5.700c0-1.400 0-3.100-1.900-3.100s-2.200 1.500-2.200 3V20H10z"/></svg>',
 "whatsapp": '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.600 15L2 22l5.200-1.400A10 10 0 1 0 12 2zm5.200 14.200c-.2.6-1.300 1.200-1.800 1.200-.5.100-1 .2-3.300-.7-2.800-1.200-4.600-4-4.700-4.200-.1-.2-1.100-1.500-1.100-2.800s.7-2 1-2.300c.2-.3.500-.3.700-.3h.5c.2 0 .4 0 .6.500l.8 2c.1.200.1.300 0 .5l-.4.600c-.1.200-.3.300-.1.600.7 1.200 1.600 2.100 2.800 2.700.3.200.5.100.7-.1l.8-1c.2-.2.400-.2.600-.1l1.900.9c.2.100.4.200.5.300.1.200.1.800-.1 1.400z"/></svg>',
}


def social_urls(ctx):
    soc = ctx["p"].get("social") or {}
    out = []
    for k, lab in LINK_ICON.items():
        u = str(soc.get(k) or "").strip()
        if u:
            if not re.match(r"https?://", u):
                u = "https://" + u.lstrip("/@")
            out.append((k, lab, u))
    return out


def social_html(ctx):
    items = social_urls(ctx)
    if not items:
        return ""
    return '<div class="spx-soc">%s</div>' % "".join(
        '<a href="%s" target="_blank" rel="noopener" aria-label="%s" title="%s">%s</a>' % (E(u), lab, lab, _SVG[k]) for k, lab, u in items)


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


def page_index(ctx, all_=False):
    """Üretilen sayfa listesi: [{slug,title,kind,nav}]. all_=True ise gizlenenler de gelir (yönetim ekranı için; 'hidden' alanı ile)."""
    p = ctx["p"]
    off = set(p.get("menu_off") or [])
    hid = set(p.get("hidden_pages") or [])
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
    for i, x in enumerate(p.get("extra_pages") or []):
        if x.get("slug") and x["slug"] not in seen:
            seen.add(x["slug"])
            out.append({"slug": x["slug"], "title": x.get("title") or x["slug"], "kind": "custom", "idx": i, "nav": bool(x.get("menu", True))})
    for x in out:
        if x["slug"] in off and x["kind"] != "custom":
            x["nav"] = False
        x["hidden"] = x["slug"] in hid
    return out if all_ else [x for x in out if not x["hidden"]]


# ------------------------------------------------------------------ tema yapısı
_ED = re.compile(r'<div class="ed" data-nm="([^"]*)"[^>]*>')


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
.spx-off{display:none!important}
.spx-logo{height:42px;width:auto;max-width:200px;object-fit:contain;display:block}a.lg:has(.spx-logo){display:inline-flex!important;align-items:center;gap:10px}
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
.spx-ph .w.hi{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);gap:clamp(24px,4vw,64px);align-items:center}
.spx-hi{margin:0;border-radius:var(--r);overflow:hidden;aspect-ratio:4/3;background:var(--sf)}.spx-hi img{width:100%;height:100%;object-fit:cover;display:block}
.spx-ab{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);gap:clamp(22px,4vw,56px);align-items:start}.spx-ab figure{margin:0;display:grid;gap:14px}.spx-ab img{width:100%;border-radius:var(--r);display:block;aspect-ratio:4/3;object-fit:cover}
.spx-ki{padding:0;overflow:hidden}.spx-ki img{width:100%;aspect-ratio:16/10;object-fit:cover;display:block}.spx-ki b,.spx-ki span{padding-left:22px;padding-right:22px}.spx-ki b{margin-top:18px}.spx-ki span{padding-bottom:22px}
.spx-sv{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,.8fr);gap:clamp(22px,4vw,56px);align-items:start}.spx-sv img{width:100%;border-radius:var(--r);display:block;aspect-ratio:4/3;object-fit:cover;position:sticky;top:96px}
@media(max-width:800px){.spx-ph .w.hi,.spx-ab,.spx-sv{grid-template-columns:1fr}.spx-hi{order:-1;aspect-ratio:16/10}.spx-sv img{position:static}}
.spx-c{max-width:960px}.spx-c.wide{max-width:1180px}
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
.spx-fab{position:fixed;left:16px;bottom:16px;z-index:60;display:inline-flex;align-items:center;gap:8px;min-height:48px;padding:0 18px;border-radius:99px;background:var(--dk,#0a1f44);color:#fff;font:700 .92rem var(--fb,inherit);text-decoration:none;box-shadow:0 6px 20px #0003}
.spx-fl{display:flex;flex-wrap:wrap;gap:8px 18px;padding:18px 0;border-top:1px solid var(--ln);font-size:.92rem}
.spx-fl a{color:inherit;opacity:.85}
.spx-soc{display:flex;gap:6px;margin-left:auto}.spx-soc a{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:50%;border:1px solid var(--ln);opacity:.9}.spx-soc a:hover{opacity:1;border-color:var(--ac,currentColor)}
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
_ADDR = re.compile(r"(?:<br>)?Atatürk Cad\. No:12(?:(?:,| /| ·) (?!Hafta)[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)?(?: · )?")
_HOURS = re.compile(r"Hafta içi 08:30 ?[–-] ?19:00")


def _off(m):
    t = m.group(0).replace("905320000000", "")
    return t.replace('class="', 'class="spx-off ', 1) if 'class="' in t else t[:-1] + ' class="spx-off">'


def _sector_links(ctx):
    import sektor_mod
    return sektor_mod.site_links(ctx.get("sector") or "")


PAGE_MAP = {"hizmet": "hizmetlerimiz", "surec": "nasil-calisiyoruz", "neden": "hakkimizda", "yorum": "hakkimizda",
            "once-sonra": "galeri", "bolge": "hizmet-bolgeleri", "sss": "sss", "iletisim": "iletisim", "hakkimizda": "hakkimizda"}


_MENU_SKIP = {"soc", "s", "mi", "pgs-none"}


def _nav_anchors(soup):
    out = []
    for a in soup.find_all("a", href=True):
        cls = set(a.get("class") or [])
        if cls & {"lg", "btn"} or not " ".join(a.get_text().split()):
            continue
        if any(set(par.get("class") or []) & _MENU_SKIP for par in a.parents):
            continue
        out.append(a)
    return out


def menu_items(*htmls):
    """Menü bloklarındaki bağlantılar: [{h, l}] (aynı adres tek kez)."""
    from bs4 import BeautifulSoup
    seen, out = set(), []
    for h in htmls:
        for a in _nav_anchors(BeautifulSoup(h or "", "html.parser")):
            k = a["href"]
            if k not in seen:
                seen.add(k)
                out.append({"h": k, "l": " ".join(a.get_text().split())[:60]})
    return out


def apply_menu(h, menu):
    """Menü düzenlemesi: bağlantı adını değiştirir, gizler, ek bağlantı ekler. Düzenleme yoksa HTML'e dokunmaz."""
    if not menu or not (menu.get("edits") or menu.get("extra") or menu.get("order")):
        return h
    import copy
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(h, "html.parser")
    ed = menu.get("edits") or {}
    anchors = _nav_anchors(soup)
    for a in anchors:
        e = ed.get(a["href"])
        if not e:
            continue
        if e.get("off"):
            par = a.parent
            (par if par.name == "li" and len(par.find_all("a")) == 1 else a).decompose()
        elif e.get("l"):
            a.string = e["l"]
    left = [a for a in anchors if a.parent is not None and not ed.get(a["href"], {}).get("off")]
    if left and menu.get("extra"):
        last = left[-1]
        for x in menu["extra"]:
            n = copy.copy(last)
            for k in ("data-pg", "class", "id", "onclick"):
                n.attrs.pop(k, None)
            if "class" in last.attrs and "l" in (last.get("class") or []):
                n["class"] = ["l"]
            n["href"] = x["h"]
            n.string = x["l"]
            if x["h"].startswith("http"):
                n["target"], n["rel"] = "_blank", "noopener"
            host = last.parent if last.parent.name == "li" else last
            if host.name == "li":
                li = copy.copy(host)
                li.clear()
                li.append(n)
                host.insert_after(li)
                host = li
            else:
                host.insert_after(n)
            last = n
    order = [o for o in (menu.get("order") or []) if isinstance(o, str)]
    if order:
        hosts = []
        for a in _nav_anchors(soup):
            if a.get("href") in order and not a.get("data-yx"):
                hosts.append((order.index(a["href"]), a.parent if a.parent.name == "li" and len(a.parent.find_all("a")) == 1 else a))
        if len(hosts) > 1:
            slots = []
            for _, el in hosts:
                m = soup.new_tag("x-slot")
                el.replace_with(m)
                slots.append(m)
            for m, (_, el) in zip(slots, sorted(hosts, key=lambda t: t[0])):
                m.replace_with(el)
    return str(soup)


def link_pages(h, idx, base="/", suffix=""):
    """Menü/alt bilgideki '#hizmet' gibi sayfa içi bağlantılar, o içeriğin kendi sayfası varsa o sayfaya gider (ana sayfada aşağı kaymaz)."""
    have = {x["slug"] for x in idx}
    return re.sub(r'href="#([a-z-]+)"', lambda m: ('href="%s%s%s"' % (base, PAGE_MAP[m.group(1)], suffix)) if PAGE_MAP.get(m.group(1)) in have else m.group(0), h)


def _linked(h, base="/", suffix=""):
    return set(re.findall(r'href="%s([a-z0-9-]+)%s"' % (re.escape(base), re.escape(suffix)), h))


def apply_profile(raw, th, ctx):
    """Ham tema HTML'ine firma bilgilerini yerleştirir (ana sayfa). Boş bırakılan bilgi temadan da kalkar."""
    h = raw.replace("__API_URL__", "/api").replace("__PORTAL_URL__", "#")
    h = re.sub(r"©\s*\d{4}\s[^<]*?·\s*Bu site OnlineKaydet ile yayınlanır", '<a href="https://onlinekaydet.com" target="_blank" rel="noopener" style="color:inherit">Bu site OnlineKaydet ile yayınlanır</a>', h)
    name = ctx["name"]
    if th and th.get("name") and name:
        h = h.replace(th["name"], E(name))
    d = phone10(ctx["tel"])
    w = phone10(ctx["p"].get("whatsapp")) or d
    if w:
        h = h.replace("wa.me/905320000000", "wa.me/90" + w)
    else:
        h = re.sub(r'<a\b[^>]*wa\.me/905320000000[^>]*>', _off, h)
    if d:
        h = h.replace("905320000000", "90" + d).replace("0532 000 00 00", phone_fmt(d))
    else:
        h = re.sub(r'<a\b[^>]*tel:\+?905320000000[^>]*>', _off, h)
        h = re.sub(r"\s*[·•|-]?\s*0532 000 00 00", "", h)
    h = h.replace("<br>Vergi No: [firma bilgisi]", "").replace("Vergi No: [firma bilgisi]", "")
    hours = ctx["p"].get("hours") or ""
    _hv = (lambda m: E(hours)) if hours else (lambda m: "")
    h = re.sub(r"<div>Cumartesi 09:00 ?[–-] ?17:00</div>|<div>Acil: 7/24</div>", "", h)
    for rx in (r"Hafta içi 08:30 ?[–-] ?19:00, cumartesi 09:00 ?[–-] ?17:00\. Acil çağrılar için 7/24 arayın\.",
               r"Hafta içi 08:30 ?[–-] ?19:00 · Cumartesi 09:00 ?[–-] ?17:00",
               r"Pzt[–-]Cmt 08:30[–-]19:00(?: · Acil için 7/24 arayın)?",
               r"Hafta içi 08:30 ?[–-] ?19:00"):
        h = re.sub((r"(?: · )?" if not hours else "") + rx, _hv, h)
    h = h.replace("Şu an arama alıyoruz · 7/24 acil hat", "Şu an arama alıyoruz")
    adr = ctx["p"].get("address") or ""
    h = _ADDR.sub(lambda m: (E(adr) + (" · " if m.group(0).endswith(" · ") else "")) if adr else "", h)
    if ctx.get("logo"):
        img = '<img class="spx-logo" src="%s" alt="%s">' % (E(ctx["logo"]), E(name))
        h = re.sub(r'(<(?:a|div) class="lg[^"]*"[^>]*>)<span class="lm[^"]*">[^<]*</span>', lambda m: m.group(1) + img, h)
        if "spx-logo" not in h:
            h = re.sub(r'(<a class="lg[^"]*"[^>]*>)(<span class="ln">)', lambda m: m.group(1) + img + m.group(2), h)
        if "spx-logo" not in h:                                   # <a class="lg">Firma adı</a> biçimindeki temalar (Kuaför 5-10 vb.)
            def _lg(m):
                return m.group(1) + img + ("" if ctx["p"].get("logo_only") else '<span class="ln">' + m.group(2) + "</span>") + "</a>"
            h = re.sub(r'(<a class="lg[^"]*"[^>]*>)((?:(?!</a>).)*)</a>', _lg, h, count=1, flags=re.S)
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
        if b[0] in ("Menü", "Mobil menü", "Alt bilgi"):
            b[1] = link_pages(b[1], idx, ctx.get("page_base", "/"), ctx.get("page_suffix", ""))
    pb, ps = ctx.get("page_base", "/"), ctx.get("page_suffix", "")
    for b in blocks:
        if b[0] == "Menü":
            nv = "".join('<a href="%s%s%s">%s</a>' % (pb, x["slug"], ps, E(x["title"])) for x in navs[:2] if x["slug"] not in _linked(b[1], pb, ps))
            nv += "".join('<a href="%s%s%s">%s</a>' % (pb, h.lstrip("/"), ps, E(l)) for h, l in _sector_links(ctx) if h not in b[1])
            b[1] = b[1].replace("</nav>", nv + "</nav>", 1) if "</nav>" in b[1] else b[1]
        elif b[0] == "Mobil menü":
            nv = "".join('<a href="%s%s%s">%s</a>' % (pb, x["slug"], ps, E(x["title"])) for x in navs if x["slug"] not in _linked(b[1], pb, ps))
            nv += "".join('<a href="%s%s%s">%s</a>' % (pb, h.lstrip("/"), ps, E(l)) for h, l in _sector_links(ctx) if h not in b[1])
            i = b[1].find('class="dl">')
            if i > 0:
                j = b[1].find("</div>", i)
                b[1] = b[1][:j] + nv + b[1][j:]
        elif b[0] == "Alt bilgi":
            b[1] = footer_logo(b[1], ctx)
            b[1] = b[1].replace("</footer>", footer_links(ctx, idx) + "</footer>", 1)
    for b in blocks:
        if b[0] in ("Menü", "Mobil menü"):
            b[1] = apply_menu(b[1], ctx["p"].get("menu"))
    if ctx["p"].get("slides"):
        k = next((i for i, b in enumerate(blocks) if b[0] == "Ana görsel"), 2)
        blocks.insert(k, ["Slider", slider_html(ctx)])
    if ctx["p"].get("nav"):
        import navtasarim
        blocks = navtasarim.apply(blocks, ctx["p"]["nav"])
    ek = ctx.get("tema_ek") or []
    if ek:                                     # bölüm kütüphanesinden eklenenler: alt bilginin hemen önüne, sırası paneldeki sıradan gelir
        k = next((i for i, b in enumerate(blocks) if b[0] in FIXED_BOTTOM), len(blocks))
        blocks = blocks[:k] + [[n, x] for n, x in ek] + blocks[k:]
    blocks = apply_layout(blocks, ctx)
    out = join_blocks(pre, blocks, tail)
    if ek and 'class="okek' in out and 'id="okek-css"' not in out:
        out = out.replace("</head>", '<style id="okek-css">%s</style></head>' % ctx.get("tema_ek_css", ""), 1)
    imap = (ctx["p"].get("imgmap") or {}).get(ctx["th"]["slug"], {}) if ctx.get("th") else {}
    if imap:
        reg_ = ctx.setdefault("_oki", {})
        for pid, k in imap.items():
            u = ctx["img"](k)
            if u:
                reg_[str(pid)] = u
    if ctx.get("_oki"):
        out = _PXD.sub(lambda m: m.group(1) + "if(window.__OKI&&window.__OKI[i])return window.__OKI[i];" + m.group(2), out)
        out = out.replace("</body>", oki_script(ctx["_oki"]) + "</body>", 1) if "</body>" in out else out + oki_script(ctx["_oki"])
    out = yp_book(out, ctx["p"])
    out = apply_promo(out, ctx)
    out = out.replace("</head>", blockstyle_html(ctx) + "</head>", 1) if "</head>" in out else out
    if ctx["p"].get("tw") and "</head>" in out:
        import navtasarim
        out = out.replace("</head>", navtasarim.tw_html(ctx["p"]["tw"]) + "</head>", 1)
    out = out.replace("</head>", CSS + "</head>", 1)
    if ctx["p"].get("slides"):
        out = out.replace("</body>", SLIDER_JS + "</body>", 1) if "</body>" in out else out + SLIDER_JS
    desc = seo_desc(ctx)
    out = _set_desc(out, desc)
    t = ctx["name"] + ((" · " + (ctx["city"] + " " if ctx.get("city") else "") + ctx["p"]["noun"] + " Servisi") if ctx["p"].get("noun") else "")
    t = (ctx["p"].get("seo_title") or "").strip() or t
    out = re.sub(r"<title>.*?</title>", lambda m: "<title>%s</title>" % E(t), out, count=1, flags=re.S)
    return seo_inject(out, seo_block(ctx, "", desc, "", "home"))


FIXED_TOP = ("Menü", "Mobil menü")
FIXED_BOTTOM = ("Alt bilgi", "Mobil bar")
_ID = re.compile(r'\bid="([^"]+)"')


def middle_names(blocks):
    return [b[0] for b in blocks if b[0] not in FIXED_TOP + FIXED_BOTTOM]


def dflt_off(html):
    """Varsayılan kapalı bölüm (örn. premium temalardaki mağaza): müşteri 'Göster' deyip düzeni kaydedene dek yayında görünmez."""
    return 'data-dflt="off"' in html[:300]


SHOP_LINK = re.compile(r'<a\b[^>]*href="(?:#(?:urunler|firsat|sepet)|/magaza[^"]*|/hesabim[^"]*)"[^>]*>(?:(?!</a>).)*</a>', re.S)
STORY_SHOP = re.compile(r'<button class="st"[^>]*data-l="#(?:firsat|urunler|sepet)"[^>]*>.*?</button>', re.S)


SHOP_WORDS = re.compile(r"(?i)(?:sepet|kargo|iade|alışveriş|mağaza|sipariş|stoktaki|kapıda ödeme)")
SHOP_TEXT_BLOCKS = {"Hizmetler", "Nasıl çalışıyoruz", "Sık sorulanlar", "Araç", "İkinci araç", "Neden biz", "Teklif bandı", "Çağrı bandı", "Yorumlar"}


def shop_names(blocks, ctx):
    """E-ticaret kapalıyken yayından kalkacak bölümler: ürün/mağaza bölümü, ürün fırsatları ve onlara bağlanan duyuru."""
    if ctx.get("shop_on"):
        return set()
    gone = {b[0] for b in blocks if b[0] == "Ürünler"}
    for b in blocks:                                  # mağaza dilinde yazılmış (sepet, kargo, iade...) bölümler de kalkar
        if b[0] in SHOP_TEXT_BLOCKS and len(SHOP_WORDS.findall(re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", b[1], flags=re.S))) >= 2:
            gone.add(b[0])
    if any(b[0] == "Fırsatlar" and ("İndirimli ürünler" in b[1] or "Fırsat ürünleri" in b[1]) for b in blocks):
        gone |= {"Fırsatlar", "Duyuru çubuğu"}
    return gone


def strip_shop(b, ctx):
    """Kalan bölümlerde mağazaya/sepete/fırsat ürünlerine giden bağlantılar, hikâyeler ve menü paneli temizlenir."""
    h = b[1]
    h = STORY_SHOP.sub("", h)
    h = SHOP_LINK.sub("", h)
    h = re.sub(r'<div class="pr"><div><small>Güncel</small>.*?</div></div>', "", h, flags=re.S) if 'class="mega"' in h else h
    b[1] = h

_DMOD = re.compile(r'^<div class="ed"[^>]*\bdata-mod="([a-z,]+)"')


def mod_off(blocks, ctx):
    """Bölümün `data-mod="pazarlama"` gibi bir paket şartı varsa ve firmanın paketinde yoksa yayından kalkar (sahip ekranındaki paket belirler)."""
    mods = ctx.get("modules")
    if mods is None:
        return set()
    out = set()
    for b in blocks:
        m = _DMOD.match(b[1])
        if m and not all(x in mods for x in m.group(1).split(",")):
            out.add(b[0])
    return out


def strip_mod(b, ctx):
    """Bölümün içindeki `data-mod="..."` öğeleri (kupon alanı, mağaza düğmesi...) paket kapsamıyorsa kaldırılır."""
    mods = ctx.get("modules")
    if mods is None or ' data-mod="' not in b[1][40:]:
        return
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(b[1], "html.parser")
    for el in soup.select("[data-mod]"):
        if el.parent is not None and el.get("data-mod") and not all(x in mods for x in el["data-mod"].split(",")):
            el.decompose()
    b[1] = str(soup)


_PHONE_UA = re.compile(r"iphone|ipod|android.*mobile|windows phone|blackberry|bb10|iemobile|opera mini|mobile safari", re.I)
_TABLET_UA = re.compile(r"ipad|tablet|android(?!.*mobile)", re.I)


def is_phone(ua):
    """Tarayıcı imzasına göre telefon mu. Tablet telefon sayılmaz: bilgisayar görünümünü alır."""
    ua = ua or ""
    return bool(_PHONE_UA.search(ua)) and not _TABLET_UA.search(ua)


def phone_over(ctx):
    """Telefon görünümü için müşterinin ayrı düzenlemeleri. Bilgisayar görünümünde boş."""
    return (ctx["p"].get("phone") or {}) if ctx.get("dev") == "phone" else {}


def apply_layout(blocks, ctx):
    """Müşterinin bölüm sırası, gizlediği bölümler ve metin düzenlemeleri."""
    ph = phone_over(ctx)
    lay = ctx["p"].get("layout") or {}
    if ph.get("layout") and not lay.get("_all"):   # telefona ayrı sıra / gizleme (panel listelemesinde değil)
        lay = dict(lay, **{k: v for k, v in (ph["layout"] or {}).items() if k in ("order", "hidden")})
    order = [n for n in (lay.get("order") or []) if isinstance(n, str)]
    hidden = set(lay.get("hidden") or [])
    shop_on = bool(ctx.get("shop_on"))
    if not lay.get("_all"):
        hidden |= {b[0] for b in blocks if dflt_off(b[1]) and b[0] not in order and not (shop_on and b[0] == "Ürünler")}
    off = shop_names(blocks, ctx)
    hidden |= off
    hidden |= mod_off(blocks, ctx)
    if off:
        for b in blocks:
            if b[0] not in off:
                strip_shop(b, ctx)
    for b in blocks:
        if b[0] not in off and b[0] not in hidden:
            strip_mod(b, ctx)
    top = [b for b in blocks if b[0] in FIXED_TOP]
    bot = [b for b in blocks if b[0] in FIXED_BOTTOM]
    mid = [b for b in blocks if b[0] not in FIXED_TOP + FIXED_BOTTOM]
    edits = (ctx["p"].get("edits") or {}).get(ctx["th"]["slug"], {}) if ctx.get("th") else {}
    iedits = (ctx["p"].get("imgedits") or {}).get(ctx["th"]["slug"], {}) if ctx.get("th") else {}
    ped = (ph.get("edits") or {}).get(ctx["th"]["slug"], {}) if ctx.get("th") else {}
    if ped:                                    # telefona özel yazılar bilgisayardakilerin üzerine biner
        edits = dict(edits)
        for bn, tx in ped.items():
            edits[bn] = dict(edits.get(bn) or {}, **tx)
    pie = (ph.get("imgedits") or {}).get(ctx["th"]["slug"], {}) if ctx.get("th") else {}
    if pie:
        iedits = dict(iedits)
        for bn, tx in pie.items():
            iedits[bn] = dict(iedits.get(bn) or {}, **tx)
    for b in mid + [x for x in bot if x[0] == "Alt bilgi"]:
        if edits.get(b[0]):
            b[1] = edit_texts(b[1], edits[b[0]])
        if iedits.get(b[0]):
            b[1] = edit_imgs(b[1], iedits[b[0]], ctx["img"], ctx.setdefault("_oki", {}))
    pos = {n: i for i, n in enumerate(order)}
    mid = sorted(mid, key=lambda b: pos.get(b[0], 10_000))
    gone = [b for b in mid if b[0] in hidden]
    mid = [b for b in mid if b[0] not in hidden]
    if gone:
        ids = {i for b in gone for i in _ID.findall(b[1])}
        for t in top + bot:
            if t[0] in ("Menü", "Mobil menü", "Alt bilgi"):
                for i in ids:
                    t[1] = re.sub(r'<a [^>]*href="#%s"[^>]*>(?:(?!</a>).)*</a>' % re.escape(i), "", t[1])
                    t[1] = re.sub(r'<div><a [^>]*href="#%s"[^>]*>(?:(?!</a>).)*</a></div>' % re.escape(i), "", t[1])
    return top + mid + bot


def img_nodes(soup):
    """Temadaki değiştirilebilir resimler: <img data-i=ID> ve arka planı data-p=ID olan öğeler (belge sırasıyla)."""
    out = []
    for el in soup.find_all(True):
        if el.name == "img" and str(el.get("data-i") or "").isdigit():
            out.append(el)
        elif str(el.get("data-p") or "").isdigit():
            if any(c.name == "img" and c.get("data-i") == el.get("data-p") for c in el.find_all("img")):
                continue                            # <a data-p=X><img data-i=X>: tek resim sayılır (görünen <img>)
            out.append(el)
    return out


def block_images(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    return [{"i": i, "pid": str(el.get("data-i") or el.get("data-p")), "tag": el.name} for i, el in enumerate(img_nodes(soup))]


def edit_imgs(html, ed, url_of, reg=None):
    """ed: {sıra: yüklenen resim anahtarı}. Resim, lightbox ve tema betiği yeni adresi kullansın diye data-i/data-p 'u<anahtar>' olur."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    nodes = img_nodes(soup)
    done = False
    for k, v in ed.items():
        try:
            el = nodes[int(k)]
        except (ValueError, IndexError):
            continue
        url = url_of(str(v))
        if not url:
            continue
        uid = "u" + str(v)
        if el.name == "img" and el.get("data-i"):
            old_id = el.get("data-i")
            el["src"] = url
            el["data-i"] = uid
            par = el.parent
            while par is not None and par.name not in ("body", "[document]"):      # lightbox'ın okuduğu üst öğe
                if par.get("data-p") == old_id:
                    par["data-p"] = uid
                    break
                par = par.parent
        else:
            st = str(el.get("style") or "").strip().rstrip(";")
            el["style"] = (st + ";" if st else "") + 'background-image:url("%s")' % url.replace('"', "%22")
            el["data-p"] = uid
        if reg is not None:
            reg[uid] = url
        done = True
    return str(soup) if done else html


_PXID = re.compile(r"""data-[ip]="(\d{5,10})"|\[(\d{5,10}),\s*'|PX\((\d{5,10})""")


def theme_image_ids(raw):
    """Temanın kullandığı stok resim kimlikleri (görünen sırayla, tekrarsız): data-i/data-p, betik dizileri [id,'kategori'] ve PX(id)."""
    seen, out = set(), []
    for m in _PXID.finditer(raw or ""):
        v = next(g for g in m.groups() if g)
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def mark_edit(html):
    """Önizleme için: tıklanıp yerinde düzenlenebilen yazılara bölüm adı ve sıra numarası işaretler (data-yb, data-yi)."""
    parts = split_blocks(html)
    if not parts:
        return html
    from bs4 import BeautifulSoup
    pre, blocks, tail = parts
    for b in blocks:
        if b[0] in FIXED_TOP or b[0] == "Duyuru çubuğu":
            continue
        soup = BeautifulSoup(b[1], "html.parser")
        ns = edit_nodes(soup)
        done = False
        for i, el in enumerate(ns):
            if all(c.name in _INLINE for c in el.find_all(True)):
                el["data-yb"], el["data-yi"] = b[0], str(i)
                done = True
        if done:
            b[1] = str(soup)
    return join_blocks(pre, blocks, tail)

# Türkçe karakter (ğ ş ı İ ç ö ü) destekli Google yazı tipleri, gruplu
FONT_GRUP = [
    ("Sade (sans)", ["Inter", "Poppins", "Montserrat", "Raleway", "Nunito", "Work Sans", "Manrope", "Open Sans", "Roboto", "Lato", "Rubik",
                     "Mulish", "Outfit", "Plus Jakarta Sans", "DM Sans", "Figtree", "Sora", "Urbanist", "Lexend", "Barlow", "Josefin Sans",
                     "Quicksand", "Karla", "Source Sans 3", "Noto Sans", "Fira Sans", "Exo 2", "Archivo", "Space Grotesk", "Jost"]),
    ("Klasik (serif)", ["Playfair Display", "Lora", "Merriweather", "DM Serif Display", "Cormorant Garamond", "Roboto Slab", "Libre Baskerville",
                        "EB Garamond", "Crimson Pro", "Prata", "Bodoni Moda", "Fraunces", "Noto Serif", "Spectral", "Cinzel", "Marcellus"]),
    ("Güçlü başlık", ["Oswald", "Bebas Neue", "Anton", "Abril Fatface", "Alfa Slab One", "Archivo Black", "Teko", "Righteous", "Bricolage Grotesque"]),
    ("El yazısı", ["Dancing Script", "Pacifico", "Great Vibes", "Caveat", "Satisfy", "Sacramento", "Allura", "Kaushan Script"]),
]
FONTS = [f for _g, fs in FONT_GRUP for f in fs]


def font_link(fonts):
    """Seçilen yazı tiplerini Google Fonts'tan yükleyen <link> (yalnız izinli listeden)."""
    fs = [f for f in dict.fromkeys(fonts or []) if f in FONTS]
    if not fs:
        return ""
    return '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?%s&display=swap">' % "&".join(
        "family=" + f.replace(" ", "+") + (":wght@400;700" if f in _TEK_AGIRLIK_DEGIL else "") for f in fs)


# yalnız tek ağırlığı olan yazı tipleri için :wght istemek isteği bozar
_TEK = {"Bebas Neue", "Anton", "Abril Fatface", "Alfa Slab One", "Archivo Black", "Righteous", "Prata", "Pacifico", "Great Vibes", "Satisfy",
        "Sacramento", "Allura", "Kaushan Script", "Marcellus", "DM Serif Display"}
_TEK_AGIRLIK_DEGIL = set(FONTS) - _TEK
_HEADS = "h1,h2,h3,h4,summary,.eyebrow,figcaption b"
_BODY = "p,li,span,small,a,label,dd,dt,blockquote,button,input"


def blockstyle_html(ctx):
    """Bölüm başına yazı tipi / yazı rengi (müşterinin seçtiği). Yalnız izinli yazı tipleri ve #renk kabul edilir."""
    bs = ((ctx["p"].get("blockstyle") or {}).get(ctx["th"]["slug"], {})) if ctx.get("th") else {}
    css, used = [], []
    for name, st in bs.items():
        sel = '[data-nm="%s"]' % re.sub(r'["\\\[\]<>{}]', "", str(name))
        if st.get("h") in FONTS:
            used.append(st["h"])
            css.append("%s :is(%s){font-family:'%s',serif!important}" % (sel, _HEADS, st["h"]))
        if st.get("b") in FONTS:
            used.append(st["b"])
            css.append("%s :is(%s){font-family:'%s',sans-serif!important}" % (sel, _BODY, st["b"]))
        if re.fullmatch(r"#[0-9a-fA-F]{6}", st.get("c") or ""):
            css.append("%s :is(h1,h2,h3,h4,p,li,span,small,summary,blockquote,dd,dt):not(.btn){color:%s!important}" % (sel, st["c"]))
    if not css:
        return ""
    return font_link(used) + "<style>" + "".join(css) + "</style>"


_PROMO_END = re.compile(r"e=new Date\(n\);e\.setDate\(n\.getDate\(\)\+\(\(7-n\.getDay\(\)\)%7\)\);e\.setHours\(23,59,59,0\);if\(e<=n\)e\.setDate\(e\.getDate\(\)\+7\);var f=\$\('#lft'\);f\.textContent=2\+\(n\.getDate\(\)%4\);")
_PROMO_BAR = ('<div class="ypb" id="ypb"><span class="ypt">%s</span>%s%s</div>'
              '<style>.ypb{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;justify-content:center;padding:9px 16px;background:var(--ac,#1155cc);color:#fff;font:600 14px/1.3 var(--fb,system-ui,sans-serif);text-align:center}'
              '.ypb .ypc{display:flex;gap:8px}.ypb .ypc b{display:inline-block;min-width:34px;padding:3px 6px;background:rgba(0,0,0,.22);border-radius:6px;font-variant-numeric:tabular-nums}.ypb .ypc small{font-weight:500;margin-left:2px;opacity:.85}'
              '.ypb button{border:0;background:#fff;color:#111;font:700 13px inherit;padding:7px 14px;border-radius:99px;cursor:pointer}</style>')
_PROMO_JS = ("<script>(function(){var e=new Date('%s+03:00'),b=document.getElementById('ypb');if(!b||isNaN(e))return;function t(){var d=e-new Date();if(d<=0){b.style.display='none';return}"
             "var q=function(i,v){var x=document.getElementById(i);if(x)x.textContent=v};q('ypd',Math.floor(d/864e5));q('yph',Math.floor(d%%864e5/36e5));q('ypm',Math.floor(d%%36e5/6e4));q('yps',Math.floor(d%%6e4/1e3))}t();setInterval(t,1000)})()</script>")


def apply_promo(out, ctx):
    """Üstteki kampanya çubuğu/sayacı: yazı, bitiş tarihi, düğme; kapatılabilir. Ayar yoksa temanın kendi hâli kalır."""
    pr = ctx["p"].get("promo") or {}
    if not pr:
        return out
    txt, end, btn = E(pr.get("text") or ""), pr.get("end") or "", E(pr.get("btn") or "")
    has_theme = 'id="cd"' in out and 'id="an"' in out
    if pr.get("on") is False:
        return out.replace("</head>", "<style>#an,#ypb{display:none!important}</style></head>", 1) if has_theme else out
    if has_theme:
        if txt:
            out = re.sub(r'(<div class="an" id="an"><span>).*?(</span><div class="cd")', lambda m: m.group(1) + txt + m.group(2), out, count=1, flags=re.S)
        if btn:
            out = re.sub(r'(<button class="ab2"[^>]*>)[^<]*(</button>)', lambda m: m.group(1) + btn + m.group(2), out, count=1)
        if end:
            out = re.sub(r'<span class="lft">.*?</span>', "", out, count=1, flags=re.S)
            out = _PROMO_END.sub("e=new Date('%s+03:00');if(e<=n){var an=$('#an');if(an)an.style.display='none'}var f={};" % end, out, count=1)
        return out
    if not (txt or end):
        return out
    cd = ('<span class="ypc"><span><b id="ypd">0</b><small>gün</small></span><span><b id="yph">00</b><small>sa</small></span><span><b id="ypm">00</b><small>dk</small></span><span><b id="yps">00</b><small>sn</small></span></span>' if end else "")
    bt = ('<button type="button" data-open>%s</button>' % btn) if btn else ""
    bar = _PROMO_BAR % (txt, cd, bt) + (_PROMO_JS % end if end else "")
    return re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + bar, out, count=1) if "<body" in out else bar + out


BOOKTEXT = [
    ("title", "Başlık", r'(<div class="frm"><h3>)([^<]*)(</h3>)'),
    ("sub", "Alt yazı", r'(<div class="sub">)([^<]*)(</div>)'),
    ("h_service", "Hizmet başlığı", r'(<h4>)([^<]*)(</h4><div class="opts" id="o-s">)'),
    ("h_expert", "Uzman başlığı", r'(<h4>)([^<]*)(</h4><div class="opts" id="o-e">)'),
    ("h_day", "Gün başlığı", r'(<h4>)([^<]*)(</h4><div class="opts days" id="o-d">)'),
    ("h_time", "Saat başlığı", r'(<h4>)([^<]*?)( ?<span id="o-cnt")'),
    ("h_info", "Bilgiler başlığı", r'(<h4>)([^<]*)(</h4><div class="fld">)'),
    ("l_name", "Ad soyad etiketi", r'(<label>)([^<]*)(<input[^>]*id="f-n")'),
    ("ph_name", "Ad soyad örnek yazısı", r'(id="f-n"[^>]*placeholder=")([^"]*)(")'),
    ("l_phone", "Telefon etiketi", r'(<label>)([^<]*)(<input[^>]*id="f-p")'),
    ("ph_phone", "Telefon örnek yazısı", r'(id="f-p"[^>]*placeholder=")([^"]*)(")'),
    ("l_coupon", "Kupon etiketi", r'(<label[^>]*>)([^<]*)(<input[^>]*id="f-c")'),
    ("btn", "Kaydet düğmesi", r'(id="go">)([^<]*)(</button>)'),
    ("ok_title", "Onay başlığı", r'(<div class="ok"><div class="tick"><svg.*?</svg></div><h3>)([^<]*)(</h3>)'),
    ("ok_msg", "Onay mesajı (ad, hizmet ve saatten sonra gelir)", r"(\+t\.dataset\.v\+' )(randevunuz iletildi\.[^']*)(')"),
    ("ok_btn", "Onay düğmesi", r'(id="okx">)([^<]*)(</button>)'),
]


def booktext_fields(h):
    """Randevu formundaki düzenlenebilir yazılar ve temadaki varsayılanları [{k,label,def}]."""
    out = []
    for k, lab, rx in BOOKTEXT:
        m = re.search(rx, h, re.S)
        if m:
            out.append({"k": k, "label": lab, "def": m.group(2)})
    return out


def apply_booktext(h, p):
    bt = p.get("booktext") or {}
    for k, lab, rx in BOOKTEXT:
        v = (bt.get(k) or "").strip()
        if not v:
            continue
        if k == "ok_msg":
            v = v.replace("\\", "").replace("'", "\u2019").replace("<", "").replace("\n", " ")
        else:
            v = E(v)
        h = re.sub(rx, lambda m, v=v: m.group(1) + v + m.group(3), h, count=1, flags=re.S)
    if p.get("coupon_off"):
        h = re.sub(r'<label[^>]*>[^<]*<input[^>]*id="f-c"[^>]*>(?:</input>)?</label>', "", h, count=1)
    return h


YP_BOOK_JS = r"""window.YPD={};
window.YPS=function(j,dy){window.YPD[dy]=j;return(j.slots||[]).map(function(s){var q=s.time.split(':');return{m:+q[0]*60+ +q[1],available:!!s.available}})};
window.YPF=function(dy,e,h){var j=window.YPD[dy];if(!j||!j.slots)return false;var s=null;for(var i=0;i<j.slots.length;i++){var q=j.slots[i].time.split(':');if(+q[0]*60+ +q[1]===h){s=j.slots[i];break}}
if(!s||!s.n)return false;var sv=document.querySelector('#o-s .on'),dur=+(sv&&sv.dataset.d)||30;if(h+dur>j.end)return false;var I=window.YPI||{staff:[]},ids=[];
var one=null;(I.staff||[]).forEach(function(x){if(x.name&&e&&x.name.toLowerCase()===String(e).toLowerCase())one=x.id});
if(one)ids=[one];else ids=(I.staff||[]).map(function(x){return x.id});if(!ids.length)ids=[''];
ids=ids.filter(function(i){return(j.off||[]).indexOf(i)<0});
var free=ids.filter(function(i){return!(j.busy[i]||[]).some(function(b){return h<b[1]&&b[0]<h+dur})});
var lost=(j.anon||[]).filter(function(b){return h<b[1]&&b[0]<h+dur}).length;return free.length-lost>0};
window.YPB=function(c){window.YPI=c;var sig=JSON.stringify([c.services,c.staff]);if(window.YPSIG===sig)return;window.YPSIG=sig;
var os=document.getElementById('o-s'),oe=document.getElementById('o-e');
if(os&&c.services&&c.services.length){os.innerHTML='';c.services.forEach(function(s,i){var b=document.createElement('button');b.textContent=s.name;b.dataset.id=s.id;b.dataset.d=s.dur;if(i===0)b.className='on';os.appendChild(b)})}
if(oe){oe.innerHTML='';var f=document.createElement('button');f.textContent='Fark etmez';f.className='on';oe.appendChild(f);(c.staff||[]).forEach(function(x){var b=document.createElement('button');b.textContent=x.name;b.dataset.id=x.id;oe.appendChild(b)})}};
"""

_YP_PATCH = [
    ("fetch('/api/public/booking/config').then(function(r){return r.json()}).then(function(c){",
     "fetch('/api/public/yp/info').then(function(r){return r.json()}).then(function(c){window.YPB(c);"),
    ("fetch('/api/public/booking/slots?date='+dy)", "fetch('/api/public/yp/slots?date='+dy)"),
    ("L.slots[dy]=(j.slots||[]).map(function(s){var q=s.time.split(':');return{m:+q[0]*60+ +q[1],available:!!s.available}})", "L.slots[dy]=window.YPS(j,dy)"),
    ("function isFree(d,e,h){if(LIVE){var t=L.slots[iso(d)];return!!t&&t.some(function(s){return s.m===h&&s.available})}", "function isFree(d,e,h){if(LIVE){return window.YPF(iso(d),e,h)}"),
    ("if(id==='o-d'||id==='o-e')renderTimes()", "if(id!=='o-t')renderTimes()"),
    ("if(!pick('o-s',s)){var nb=document.createElement('button');nb.textContent=s;A('#o-s button').forEach(function(x){x.classList.remove('on')});nb.className='on';$('#o-s').appendChild(nb)}",
     "pick('o-s',s);if(!$('#o-s .on')){var f0=$('#o-s button');if(f0)f0.classList.add('on')}"),
    ("fetch('/api/public/booking',{method", "fetch('/api/public/yp/book',{method"),
    ("device_type:s?s.textContent:'',fault:note,coupon:cp?cp.value:''", "services:s&&s.dataset.id?[s.dataset.id]:[],staff_id:(ex&&ex.dataset.id)||'',note:note,coupon:cp?cp.value:''"),
    ("fin(n,s,d,t,x.j.message)", "L.at=0;load(true);fin(n,s,d,t,n.split(' ')[0]+', '+(s?s.textContent:'')+' için '+d.dataset.l+' ('+d.dataset.v+') saat '+t.dataset.v+' randevunuz iletildi. Salon onayladığında size mesaj gelecek.')"),
    ("<h3>Randevunuz alındı</h3>", "<h3>Randevunuz iletildi</h3>"),
]


def yp_book(h, p=None):
    """Kuaför temalarının randevu çekmecesini panelin ekip/hizmet/doluluk verisine bağlar (yalnız gömülü ortak randevu kodu varsa)."""
    if "window.__OKLIVE=true;" not in h or "function isFree(d,e,h){if(LIVE){var t=L.slots" not in h:
        return h
    for a, b in _YP_PATCH:
        h = h.replace(a, b)
    h = apply_booktext(h, p or {})
    h = h.replace("</head>", "<style>#sh .sheet.done .ok,#shs.done .ok{display:block!important}#sh .sheet.done .frm,#shs.done .frm{display:none!important}</style></head>", 1)
    return h.replace("window.__OKLIVE=true;", "window.__OKLIVE=true;" + YP_BOOK_JS, 1)


def oki_script(reg):
    import json as _j
    return "<script>window.__OKI=%s</script>" % _j.dumps(reg).replace("</", "<\\/")


_PXD = re.compile(r"(PX=function\(i,w\)\{)(return'https://images\.pexels\.com)")



_INLINE = {"em", "strong", "b", "i", "br", "span", "small", "mark", "u", "wbr"}
_EDITABLE = ["h1", "h2", "h3", "h4", "p", "summary", "li", "blockquote", "figcaption", "dt", "dd"]


def _is_edit(el):
    if el.name in _EDITABLE:
        return True
    cls = " ".join(el.get("class") or [])
    return (el.name == "a" and "btn" in cls) or "eyebrow" in cls or (el.name == "button" and "btn" in cls)


def edit_nodes(soup):
    """Düzenlenebilir metin öğeleri (içinde başka düzenlenebilir öğe olmayanlar)."""
    out = []
    for el in soup.find_all(True):
        if not _is_edit(el):
            continue
        if any(_is_edit(c) for c in el.find_all(True)):
            continue
        if not _own_text(el):
            continue
        out.append(el)
    return out


def _own_text(el):
    only_inline = all(c.name in _INLINE for c in el.find_all(True))
    t = el.get_text() if only_inline else "".join(str(x) for x in el.find_all(string=True, recursive=False))
    return " ".join(t.split())


def block_texts(html, edits=None):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    res = []
    for i, el in enumerate(edit_nodes(soup)):
        res.append({"i": i, "tag": el.name, "text": _own_text(el)})
    return res


def edit_texts(html, ed):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    nodes = edit_nodes(soup)
    for k, v in ed.items():
        try:
            el = nodes[int(k)]
        except (ValueError, IndexError):
            continue
        v = str(v)
        only_inline = all(c.name in _INLINE for c in el.find_all(True))
        if only_inline:
            el.clear()
            el.append(v)
        else:
            first = True
            for x in list(el.find_all(string=True, recursive=False)):
                if not str(x).strip():
                    continue
                if first:
                    x.replace_with(v)
                    first = False
                else:
                    x.extract()
            if first:
                el.insert(0, v)
    return str(soup)


def footer_logo(h, ctx):
    """Yüklenen logo alt bilgide de görünsün: temalardaki üç marka kalıbı (div.lg, b.fl, ilk sütunun <b> başlığı)."""
    if not ctx.get("logo") or "spx-logo" in h:
        return h
    name = ctx.get("name") or ""
    img = '<img class="spx-logo spx-flogo" src="%s" alt="%s">' % (E(ctx["logo"]), E(name))
    only = bool(ctx["p"].get("logo_only"))
    def put(m):
        return m.group(1) + img + ("" if only else '<span class="ln">' + m.group(2) + "</span>") + m.group(3)
    for rx in (r'(<div class="lg">)([^<]*)(</div>)', r'(<div class="fl">)([^<]*)(</div>)', r'(<b class="fl">)([^<]*)(</b>)', r'(<div class="w"><div class="g"><div><)(?:b>)([^<]*)(</b>)'):
        n = re.subn(rx, put if "<b>" not in rx else (lambda m: '<div class="w"><div class="g"><div>' + img + ("" if only else "<b>" + m.group(2) + "</b>")), h, count=1)
        if n[1]:
            return n[0]
    return h


def footer_links(ctx, idx):
    links = ['<a href="/%s">%s</a>' % (x["slug"], E(x["title"])) for x in idx if x["kind"] in ("about", "services", "gallery", "process", "faq", "regions", "contact", "custom")]
    legal = ['<a href="/%s">%s</a>' % (k, E(t)) for k, t in (ctx.get("legal") or [])]       # mağaza açıksa yasal metinler (mevzuat gereği her sayfadan erişilebilir)
    links += ['<a href="%s">%s</a>' % (h, E(l)) for h, l in _sector_links(ctx)]
    if ctx.get("shop_on"):
        links += ['<a href="/magaza">Mağaza</a>', '<a href="/hesabim">Hesabım / Giriş</a>']
    if not links and not legal and not social_urls(ctx):
        return ""
    fab = ('<a class="spx-fab" href="/magaza" aria-label="Mağaza"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
           '<path d="M6 7h12l1 13H5L6 7z"/><path d="M9 7a3 3 0 0 1 6 0"/></svg><span>Mağaza</span></a>') if ctx.get("shop_on") else ""
    return fab + '<div class="w spx-fl">%s%s</div>%s' % ("".join(links), social_html(ctx), ('<div class="w spx-fl spx-lg">%s</div>' % "".join(legal)) if legal else "")


_PH = "{{H}}"


def seo_block(ctx, title, desc, slug="", kind="home", extra_ld=None):
    """Temaya/sektöre özgü SEO: açıklama, canonical, Open Graph, JSON-LD. Alan adı {{H}} yer tutucusuyla gelir (seo_finish doldurur)."""
    p, name = ctx["p"], ctx["name"]
    url = _PH + "/" + slug if slug else _PH + "/"
    d = phone10(ctx["tel"])
    noun = p.get("noun") or "Teknik"
    city = (ctx.get("city") or p.get("city") or "").strip()
    biz = {"@context": "https://schema.org", "@type": "LocalBusiness", "name": name, "url": _PH + "/", "description": desc}
    if d:
        biz["telephone"] = "+90" + d
    if p.get("email"):
        biz["email"] = p["email"]
    if p.get("address"):
        biz["address"] = {"@type": "PostalAddress", "streetAddress": p["address"], "addressCountry": "TR"}
        if city:
            biz["address"]["addressLocality"] = city
    areas = list(p.get("regions") or []) or ([city] if city else [])
    if areas:
        biz["areaServed"] = [{"@type": "City" if a == city else "AdministrativeArea", "name": a} for a in areas[:12]]
    sa = [u for _k, _l, u in social_urls(ctx)]
    if sa:
        biz["sameAs"] = sa
    if p.get("hours"):
        biz["openingHours"] = p["hours"]
    if ctx.get("logo_abs"):
        biz["image"] = _PH + ctx["logo_abs"]
    biz["makesOffer"] = [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": sv["t"]}} for sv in (p.get("services") or [])[:8]]
    lds = [biz]
    if kind != "home":
        lds.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": name, "item": _PH + "/"},
            {"@type": "ListItem", "position": 2, "name": title, "item": url}]})
    if kind == "faq":
        lds.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in p.get("faq") or []]})
    if kind == "service":
        lds.append({"@context": "https://schema.org", "@type": "Service", "name": title, "description": desc,
                    "provider": {"@type": "LocalBusiness", "name": name, "url": _PH + "/"}, "areaServed": city or "TR"})
    for x in extra_ld or []:
        lds.append(x)
    ld = "".join('<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False).replace("</", "<\\/") for x in lds)
    t = "%s · %s" % (title, name) if title else name
    return ('<link rel="canonical" href="%s"><meta property="og:type" content="website"><meta property="og:locale" content="tr_TR">'
            '<meta property="og:site_name" content="%s"><meta property="og:title" content="%s"><meta property="og:description" content="%s">'
            '<meta property="og:url" content="%s"><meta name="twitter:card" content="summary"><meta name="robots" content="index,follow,max-image-preview:large">%s'
            % (url, E(name), E(t), E(desc[:300]), url, ld))


def seo_desc(ctx, title="", extra=""):
    p, name = ctx["p"], ctx["name"]
    city = (ctx.get("city") or p.get("city") or "").strip()
    noun = p.get("noun") or "Teknik"
    d = phone10(ctx["tel"])
    base = (p.get("seo_desc") or "").strip() if not title else ""
    if base:
        return base
    parts = []
    if title:
        parts.append("%s — %s" % (title, name))
    else:
        parts.append("%s — %s%s servisi." % (name, city + " " if city else "", noun.lower()))
    if extra:
        parts.append(extra)
    parts.append("Randevu ve bilgi için arayın" + (": " + phone_fmt(d) if d else "") + ".")
    return " ".join(parts)


ACCOUNT_BAR = (
    '<style>.spx-ab{display:inline-flex;gap:8px;align-items:center;margin-left:12px;flex:none;z-index:70}'
    '.spx-ab a{position:relative;width:44px;height:44px;display:inline-grid;place-items:center;border-radius:50%;border:1.5px solid currentColor;color:inherit;text-decoration:none;background:transparent}'
    '.spx-ab a:hover{opacity:.8}.spx-ab svg{width:20px;height:20px;pointer-events:none}'
    '.spx-ab i{position:absolute;top:-5px;right:-5px;min-width:18px;height:18px;padding:0 4px;border-radius:9px;background:var(--ac,#e11d48);color:#fff;font:700 11px/18px system-ui;text-align:center;font-style:normal}'
    '.spx-ab b{position:absolute;bottom:2px;right:2px;width:9px;height:9px;border-radius:50%;background:#22c55e;border:2px solid #fff}'
    '.spx-ab.fx{position:fixed;top:12px;right:12px;margin:0;background:var(--dk,#0a1f44);color:#fff;padding:6px 8px;border-radius:99px;box-shadow:0 6px 20px #0003}.spx-ab.fx a{border-color:#fff6}'
    '@media(max-width:560px){.spx-ab{gap:6px;margin-left:8px}.spx-ab a{width:40px;height:40px}}</style>'
    '<script>(function(){var n=0,li=0;try{n=JSON.parse(localStorage.getItem("okcart-live")||"[]").reduce(function(a,x){return a+(x.q||0)},0);li=localStorage.getItem("okc_token")?1:0}catch(e){}'
    'var d=document.createElement("div");d.className="spx-ab";'
    'd.innerHTML=\'<a href="/hesabim" aria-label="Hesabım / Giriş yap" title="Hesabım"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/></svg>\'+(li?"<b></b>":"")+\'</a>'
    '<a href="/magaza#sepet" aria-label="Sepetim" title="Sepetim"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 7h12l1 13H5L6 7z"/><path d="M9 7a3 3 0 0 1 6 0"/></svg>\'+(n?"<i>"+n+"</i>":"")+\'</a>\';'
    'var h=document.querySelector("body > header, header, .hd, #hd, nav.nv, .nav"),t=null;'
    'if(h&&h.offsetWidth>0){var c=[h].concat([].slice.call(h.querySelectorAll("div,nav")));for(var i=0;i<c.length;i++){var s=getComputedStyle(c[i]);if(s.display.indexOf("flex")>-1&&c[i].children.length>=2&&c[i].offsetWidth>=h.offsetWidth*.6){t=c[i];break}}}'
    'if(t){var l=t.lastElementChild;if(window.innerWidth<760&&l&&(l.tagName==="BUTTON"||/burger|bgr|hamb|menu|mn|tg/i.test(l.className+l.id))){t.insertBefore(d,l)}else{t.appendChild(d)}'
    'var fit=function(){if(t.scrollWidth<=t.clientWidth+1)return;var f=t.firstElementChild;if(f&&f!==d){f.style.minWidth="0";f.style.flexShrink="1";f.style.overflow="hidden";'
    '[].slice.call(f.querySelectorAll("span,b,strong,em,div,p")).forEach(function(e){if(!e.querySelector("img,svg")){e.style.minWidth="0";e.style.overflow="hidden";e.style.textOverflow="ellipsis";e.style.whiteSpace="nowrap"}})}'
    'if(t.scrollWidth>t.clientWidth+1){d.style.gap="4px";d.style.marginLeft="4px";[].slice.call(d.children).forEach(function(a){a.style.width=a.style.height="36px"})}};'
    'fit();addEventListener("resize",fit)}'
    'else{d.className+=" fx";document.body.appendChild(d)}})();</script>'
)


def account_icons(h: str) -> str:
    """Mağaza açıkken her sayfanın üst çubuğuna Hesabım (giriş/üye ol/siparişler) ve Sepet simgeleri; mobilde de görünür."""
    if not h or "spx-ab" in h or "</body>" not in h:
        return h
    return h.replace("</body>", ACCOUNT_BAR + "</body>", 1)


CREDIT_LINK = ('<a class="spx-credit" href="https://onlinekaydet.com" target="_blank" rel="noopener" '
               'style="color:inherit!important;text-decoration:underline!important;display:inline!important;visibility:visible!important;opacity:1!important;position:static!important">'
               'Bu site OnlineKaydet ile yayınlanır</a>')
_CREDIT_RX = re.compile(r"(?:<a\b[^>]*>\s*)?Bu site\s+OnlineKaydet\s+ile yay[ıi]nlan[ıi]r(?:\s*</a>)?", re.I)


_DEMO_MOD = {
    "ilanlar": [
        {"id": "d1", "slug": "d1", "kind": "satilik", "kind_label": "Satılık", "title": "Merkezde 3+1 güney cepheli daire", "price": 4250000, "rooms": "3+1", "m2": 135, "neighborhood": "Fatih Mah.", "district": "Merkez", "city": "", "img_count": 0},
        {"id": "d2", "slug": "d2", "kind": "kiralik", "kind_label": "Kiralık", "title": "Eşyalı 1+1 yeni bina", "price": 18500, "rooms": "1+1", "m2": 62, "neighborhood": "Yeni Mah.", "district": "Merkez", "city": "", "img_count": 0},
        {"id": "d3", "slug": "d3", "kind": "satilik", "kind_label": "Satılık", "title": "Yola cepheli 2+1 ofis katı", "price": 3100000, "rooms": "2+1", "m2": 98, "neighborhood": "Çarşı", "district": "Merkez", "city": "", "img_count": 0},
    ],
    "kurslar": [
        {"id": "d1", "title": "Temel eğitim programı", "price": 12500, "duration": "6 hafta", "schedule": "Hafta içi 18:00", "description": "Başlangıç seviyesi için birebir takipli program.", "has_img": False},
        {"id": "d2", "title": "Yoğun hafta sonu grubu", "price": 9800, "duration": "8 hafta", "schedule": "Cumartesi 10:00", "description": "Hafta içi vakti olmayanlar için küçük grup.", "has_img": False},
        {"id": "d3", "title": "Birebir özel ders", "price": 1500, "duration": "Saatlik", "schedule": "Randevuyla", "description": "Size uygun gün ve saatte.", "has_img": False},
    ],
    "rezervasyon": [
        {"id": "d1", "name": "Standart seçenek", "kind": "", "capacity": 4, "price": 2500, "description": "Tarihleri seçin, talebiniz size dönüşle onaylansın.", "has_img": False},
        {"id": "d2", "name": "Geniş seçenek", "kind": "", "capacity": 8, "price": 4200, "description": "Kalabalık grup için.", "has_img": False},
    ],
}


def _preview_module(h, ctx, page):
    """Önizlemede modül sayfaları örnek verilerle (gerçek sitede firmanın kendi kayıtları gösterilir)."""
    try:
        import sektor_mod, siteedit, ilan
        if ("/" + page) not in [x for x, _ in sektor_mod.site_links(ctx.get("sector") or "")]:
            return None
        items = _DEMO_MOD[page]
        if page == "ilanlar":
            body = ilan.list_body(items).replace('href="/ilan/', 'href="#" data-d="')
            title = "İlanlar"
        elif page == "kurslar":
            body, title = sektor_mod.kurslar_body(items), "Programlar"
        else:
            body, title = sektor_mod.rezervasyon_body(items), "Rezervasyon"
        return siteedit.compose_page(h, title + " · " + ctx["name"], body)
    except Exception:                                                     # noqa: BLE001
        return None


def preview_html(raw, th, slug, page=""):
    """Tema vitrini: örnek firma bilgisiyle ana sayfa ya da iç sayfa. Menü bağlantıları önizleme sayfalarına gider."""
    ctx = {"th": th, "name": th.get("name") or "Örnek Firma", "tel": "05320000000", "p": effective({}, th.get("sector") or ""), "sector": th.get("sector") or "",
           "logo": "", "city": "", "legal": [], "shop_on": True, "img": (lambda k: ""), "logo_abs": ""}
    ctx["p"]["address"] = ""
    h = apply_profile(raw, th, ctx)
    if page in ("ilanlar", "kurslar", "rezervasyon"):
        h = _preview_module(h, ctx, page)
        if not h:
            return None
    elif page.startswith("urun-"):
        import urunsayfa
        h = urunsayfa.page_html(h, ctx, slug, page)
        if not h:
            return None
    elif page:
        r = render_page(h, ctx, page)
        if not r:
            return None
        h = r[0]
    base = "/tema-onizleme/%s" % slug
    h = re.sub(r'<a\b[^>]*href="/(?:magaza|hesabim)[^"]*"[^>]*>(?:(?!</a>).)*</a>', "", h, flags=re.S)
    h = re.sub(r'href="/#([^"]*)"', lambda m: 'href="%s.html#%s"' % (base, m.group(1)), h)
    h = h.replace('href="/"', 'href="%s.html"' % base)
    h = re.sub(r'href="/([a-z0-9-]+)"', lambda m: 'href="%s/%s.html"' % (base, m.group(1)), h)
    return h


def credit(h: str) -> str:
    import themefix
    h = themefix.fix(h)
    """'OnlineKaydet ile yayınlanır' bağlantısı her sitede, her sayfada onlinekaydet.com'a gider; müşteri silemez ya da değiştiremez.
    Mevcut yazı (bağlantılı ya da düz) kanonik bağlantıyla değiştirilir; hiç yoksa sayfa sonuna eklenir."""
    if not h or "</body>" not in h:
        return h
    h = re.sub(r'<div class="spx-credit-w"[^>]*>.*?</div>', "", h, flags=re.S)
    h, n = _CREDIT_RX.subn(lambda m: CREDIT_LINK, h)
    if n == 0 or "spx-credit" not in h:
        h = h.replace("</body>", '<div class="spx-credit-w" style="text-align:center!important;padding:14px 12px!important;font-size:13px!important;color:inherit;display:block!important;visibility:visible!important;opacity:1!important">' + CREDIT_LINK + "</div></body>", 1)
    return h



def seo_finish(h, host):
    """{{H}} yer tutucusunu alan adıyla doldurur; alan adı yoksa (önizleme) o etiketleri atar."""
    if _PH not in h:
        return h
    if host:
        return h.replace(_PH, "https://" + host)
    h = re.sub(r'<link rel="canonical"[^>]*\{\{H\}\}[^>]*>|<meta property="og:url"[^>]*\{\{H\}\}[^>]*>|<script type="application/ld\+json">.*?</script>', "", h, flags=re.S)
    return h.replace(_PH, "")


def seo_inject(h, block):
    h = re.sub(r'<link rel="canonical"[^>]*>|<meta property="og:[^>]*>|<meta name="twitter:[^>]*>|<meta name="robots"[^>]*>|<script type="application/ld\+json">.*?</script>', "", h, flags=re.S)
    return h.replace("</head>", block + "</head>", 1)


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


def _imgs(ctx):
    try:
        import temafoto
        return temafoto.sector_imgs(ctx.get("sector"))
    except Exception:                                               # noqa: BLE001
        return []


def _page_body(ctx, pg, idx):
    p, name, noun = ctx["p"], ctx["name"], ctx["p"]["noun"]
    city = (ctx.get("city") or "").strip()
    k = pg["kind"]
    sv_links = {x["idx"]: x for x in idx if x["kind"] == "service"}
    if k == "about":
        txt = p.get("about") or ("%s, %s alanında hizmet veren bir servis firmasıdır. Arızayı önce yerinde tespit eder, yapılacak işlemi ve ücreti size anlatır, onayınızla başlarız.\n\n"
                                 "Aradığınızda bilgi verir, uygun saati birlikte belirleriz. Yaptığımız işlerin kaydı tutulur; sorunuz olursa bize her zaman ulaşabilirsiniz." % (name, noun.lower() + (" (" + city + ")" if city else "")))
        im = _imgs(ctx)
        if im:
            return "", '<div class="spx-ab"><div>%s</div><figure><img src="%s" alt="%s" loading="lazy"><img src="%s" alt="%s" loading="lazy"></figure></div>' % (paras(txt), E(im[1]), E(name), E(im[2]), E(name))
        return "", paras(txt)
    if k == "services":
        im = _imgs(ctx)
        cards = "".join('<a class="spx-k%s" href="/%s">%s<b>%s</b><span>%s</span></a>' % (" spx-ki" if im else "", sv_links[i]["slug"], ('<img src="%s" alt="" loading="lazy">' % E(im[i % 3])) if im else "", E(s["t"]), E(s.get("d") or "")) for i, s in enumerate(p["services"]) if i in sv_links)
        return "Hizmetlerimiz", '<div class="spx-g">%s</div>' % cards
    if k == "gallery":
        return "Çalışmalarımızdan", '<div class="spx-gal">%s</div>' % "".join('<img src="%s" alt="%s" loading="lazy">' % (E(ctx["img"](g["k"])), E(name)) for g in p["gallery"])
    if k == "custom":
        x = (p.get("extra_pages") or [])[pg["idx"]]
        im = ('<img src="%s" alt="%s" style="width:100%%;border-radius:var(--r);margin:0 0 20px;display:block">' % (E(ctx["img"](x["img"])), E(x.get("title") or "")) if x.get("img") else "")
        return "", im + paras(x.get("body") or "")
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
        im = _imgs(ctx)
        if im:
            body = '<div class="spx-sv"><div>%s</div><img src="%s" alt="%s" loading="lazy"></div>' % (body, E(im[pg["idx"] % 3]), E(s["t"]))
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
    out = assemble(home_html, ctx, pg["title"], content, pg["kind"], pg["slug"], sub if isinstance(sub, str) else "")
    return (out, pg["title"]) if out else None


def assemble(home_html, ctx, title, content, kind="page", slug="", extra=""):
    """Ana sayfanın menü + alt bilgi + mobil çubuğuyla, verilen içerikten sayfa kurar."""
    im = _imgs(ctx)
    hi = im[sum(map(ord, slug or title)) % 3] if im and kind in ("about", "services", "process", "faq", "regions", "region", "service", "contact", "gallery") else ""
    main = ('<div class="ed" data-nm="İçerik"><section class="spx-ph"><div class="w%s"><div><span class="eyebrow">%s</span><h1>%s</h1></div>%s</div></section>'
            '<section class="sec"><div class="w spx-c%s">%s%s</div></section></div>'
            % (" hi" if hi else "", E(ctx["name"]), E(title), ('<figure class="spx-hi"><img src="%s" alt="%s" loading="eager"></figure>' % (E(hi), E(title))) if hi else "",
               " wide" if kind in ("about", "services", "service") else "", content, _cta(ctx)))
    return assemble_mid(home_html, ctx, title, [["İçerik", main]], kind, slug, extra)


FIXED_NAMES = ("Menü", "Mobil menü", "Alt bilgi", "Mobil bar")


def assemble_mid(home_html, ctx, title, mids, kind="page", slug="", extra=""):
    """Güncel temanın başlık/menü/alt bilgisi + verilen orta bölümler. Tema değişince kayıtlı sayfalar da yeni temaya geçer."""
    parts = split_blocks(home_html)
    if not parts:
        return None
    pre, blocks, tail = parts
    keep = []
    for b in blocks:
        if b[0] in FIXED_NAMES:
            bb = link_pages(b[1], page_index(ctx))
            keep.append([b[0], re.sub(r'href="#([^"]*)"', lambda m: 'href="/%s"' % (("#" + m.group(1)) if m.group(1) not in ("", "top") else ""), bb)])
    out_blocks = [b for b in keep if b[0] in ("Menü", "Mobil menü")] + list(mids) + [b for b in keep if b[0] in ("Alt bilgi", "Mobil bar")]
    pre2 = _IMVAR.sub(lambda m: m.group(0).split(":")[0] + ":none", pre)
    out = join_blocks(pre2, out_blocks, tail)
    out = re.sub(r"<title>.*?</title>", "<title>%s · %s</title>" % (E(title), E(ctx["name"])), out, count=1, flags=re.S)
    desc = seo_desc(ctx, title, extra)
    out = _set_desc(out, desc)
    out = seo_inject(out, seo_block(ctx, title, desc, slug, {"faq": "faq", "service": "service"}.get(kind, "page")))
    return out.replace("</head>", CSS + "</head>", 1)


def rebase(saved_html, home_html, ctx, title, slug=""):
    """Kayıtlı (düzenleyiciden gelen) sayfanın içeriğini güncel tema kabuğuna oturtur. Ayrıştırılamazsa olduğu gibi döner."""
    sp = split_blocks(saved_html)
    if not sp or not home_html or not ctx:
        return saved_html
    mids = [b for b in sp[1] if b[0] not in FIXED_NAMES]
    if not mids:
        return saved_html
    return assemble_mid(home_html, ctx, title, mids, "page", slug) or saved_html


def sitemap(ctx, host, extra=(), lastmod=""):
    base = "https://" + host
    lm = ("<lastmod>%s</lastmod>" % E(lastmod[:10])) if lastmod else ""
    rows = [(base + "/", "1.0")]
    for x in page_index(ctx):
        rows.append((base + "/" + x["slug"], "0.8" if x["kind"] in ("about", "services", "contact", "faq") else "0.6"))
    rows += [(base + "/" + s_, "0.6") for s_ in extra]
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % "".join(
        "<url><loc>%s</loc>%s<priority>%s</priority></url>" % (E(u), lm, pr) for u, pr in rows)
