#!/usr/bin/env python3
"""Satış sitesi: ek sayfaları üretir, üst menü ve alt bilgiyi tüm sayfalarda günceller.
Çalıştır: python3 site/gen_sayfalar.py   (site/ klasöründen veya dışından)"""
import os, re, json, html, shutil
D = os.path.dirname(os.path.abspath(__file__))
os.chdir(D)
BASE = open('bayilik.html', encoding='utf-8').read()
HEAD_TOP = BASE[:BASE.index('<title>')]
CSS_LINKS = ''.join(re.findall(r'<link rel="stylesheet" href="[^"]+">', BASE)) + '<link rel="stylesheet" href="sayfalar.css">'
PRE = BASE[BASE.index('</head>'):BASE.index('<main id="icerik">')]   # </head><body>..svg..header
POST = BASE[BASE.index('</main>') + len('</main>'):]
TEL = '0544 444 40 04'

NAV = ('<nav class="m" aria-label="Ana menü"><a href="ozellikler.html">Ürün</a><a href="sektorler.html">Sektörler</a>'
       '<a href="temalar.html">Temalar</a><a href="entegrasyonlar.html">Entegrasyonlar</a><a href="fiyatlar.html">Fiyatlar</a>'
       '<a href="destek.html">Destek</a></nav>')
FOOT_GRID = ('<footer><div class="w"><div class="g g5"><div><img src="logo-acik-s.png" alt="OnlineKaydet" height="34">'
 '<p>Teknik servisler için servis kaydı, usta takibi, tahsilat ve web sitesi platformu.</p>'
 '<a class="fp" href="tel:05444444004">0544 444 40 04</a></div>'
 '<div><h5>Ürün</h5><a href="ozellikler.html">Özellikler</a><a href="usta-uygulamasi.html">Usta uygulaması</a><a href="temalar.html">Temalar</a><a href="entegrasyonlar.html">Entegrasyonlar</a><a href="fiyatlar.html">Fiyatlar</a><a href="demo.html">Demo</a></div>'
 '<div><h5>Sektörler</h5><a href="sektor-kombi.html">Kombi</a><a href="sektor-klima.html">Klima</a><a href="sektor-beyaz-esya.html">Beyaz eşya</a><a href="sektor-elektronik.html">Elektronik</a><a href="sektor-bilgisayar.html">Bilgisayar</a><a href="sektor-tesisat.html">Tesisat</a><a href="sektor-elektrik.html">Elektrik</a><a href="sektor-guvenlik.html">Güvenlik</a></div>'
 '<div><h5>Kaynaklar</h5><a href="blog.html">Blog</a><a href="destek.html">Destek</a><a href="komisyon-hesaplama.html">Komisyon hesaplama</a><a href="desi-hesaplama.html">Desi hesaplama</a><a href="hata-kodlari.html">Hata kodları</a></div>'
 '<div><h5>OnlineKaydet</h5><a href="neden-onlinekaydet.html">Neden OnlineKaydet?</a><a href="bayilik.html">İş ortaklığı</a><a href="iletisim.html">İletişim</a><a href="https://wa.me/905444444004" rel="noopener">WhatsApp</a><a href="/giris">Müşteri girişi</a></div></div>'
 '<div class="cp"><span>© 2026 OnlineKaydet</span><span>onlinekaydet.com</span></div></div></footer>')

def e(s): return html.escape(s, quote=True)

def page(fn, title, desc, crumb, h1, lead, body, acts=None, ld=None, extra_head=''):
    acts = acts or '<a class="bt" href="iletisim.html#form">Ücretsiz deneyin</a><a class="bt l" href="tel:05444444004">%s</a>' % TEL
    url = 'https://onlinekaydet.com/' + fn
    head = (HEAD_TOP + '<title>%s</title>\n<meta name="description" content="%s">\n<link rel="canonical" href="%s">\n'
            '<meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:type" content="website">'
            '<meta property="og:url" content="%s"><meta property="og:image" content="https://onlinekaydet.com/og-kart.png"><meta name="twitter:card" content="summary_large_image">\n'
            % (e(title), e(desc), url, e(title), e(desc), url))
    head = re.sub(r'<script type="application/ld\+json">.*?</script>', '', head, flags=re.S)
    if ld: head += '<script type="application/ld+json">%s</script>' % json.dumps(ld, ensure_ascii=False)
    head += CSS_LINKS + extra_head
    hero = ('<main id="icerik">\n<div class="pgh"><div class="w"><div><nav class="crumb" aria-label="Sayfa yolu"><a href="index.html">Ana sayfa</a> / %s</nav>'
            '<h1>%s</h1><p>%s</p><div class="acts">%s</div></div></div></div>\n' % (crumb, h1, lead, acts))
    out = head + PRE + hero + body + '\n</main>' + POST
    out = apply_chrome(out)
    open(fn, 'w', encoding='utf-8').write(out)
    return fn

def apply_chrome(h):
    h = re.sub(r'<nav class="m" aria-label="Ana menü">.*?</nav>', NAV, h, flags=re.S)
    h = re.sub(r'<footer>.*?</footer>', FOOT_GRID, h, flags=re.S)
    return h

ICO = {
 'tel': '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
 'chat': '<path d="M4 5h16v11H9l-5 4z"/>',
 'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 'sms': '<rect x="3" y="5" width="18" height="12" rx="2"/><path d="M7 21l3-4M8 10h8M8 13h5"/>',
 'cart': '<path d="M3 4h3l2 11h10l2-8H7"/><circle cx="10" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/>',
 'card': '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18M7 15h4"/>',
 'cam': '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
 'pen': '<path d="M4 20l1-5L16 4l4 4L9 19z"/><path d="M14 6l4 4"/>',
 'user': '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
 'doc': '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h7"/>',
 'map': '<path d="M12 21s7-6 7-11a7 7 0 0 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
 'bell': '<path d="M6 17V11a6 6 0 0 1 12 0v6l2 2H4z"/><path d="M10 21h4"/>',
 'web': '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M7 6.5h.01M10 6.5h.01"/>',
 'bolt': '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
 'shield': '<path d="M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
 'box': '<path d="M3 8l9-5 9 5v8l-9 5-9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
 'chart': '<path d="M4 20V4M4 20h16M8 16v-5M13 16V8M18 16v-8"/>',
}
def ic(name, col='b'):
    return '<i class="ib %s"><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></i>' % (col, ICO[name])

def card(icon, col, h, p):
    return '<div>%s<h3>%s</h3><p>%s</p></div>' % (ic(icon, col), h, p)

FORM = ('<div class="frm"><div><label for="f1">Ad soyad</label><input id="f1" autocomplete="name"></div>'
 '<div><label for="f2">Telefon</label><input id="f2" type="tel" autocomplete="tel"></div>'
 '<div><label for="f3">Firma adı</label><input id="f3" autocomplete="organization"></div>'
 '<div><label for="f4">Sektör</label><select id="f4"><option>Seçiniz</option><option>Kombi</option><option>Klima</option><option>Beyaz eşya</option><option>Elektronik</option><option>Bilgisayar</option><option>Tesisat</option><option>Elektrik</option><option>Güvenlik</option></select></div>'
 '<a class="bt" href="#">Beni arayın</a><small>Bilgileriniz yalnızca sizinle iletişim için kullanılır (KVKK).</small></div>')

def cta(title='Servis işinizi bu hafta düzene sokalım', text='Formu doldurun, sektörünüze göre kurulumu birlikte planlayalım. 7 gün ücretsiz.', sid='kayit'):
    return ('<section id="'+sid+'" class="dkk"><div class="w"><div class="fc"><div><h2>%s</h2><p>%s</p><a class="big" href="tel:05444444004">%s</a></div>%s</div></div></section>'
            % (title, text, TEL, FORM))

def faq(title, items, sid='sss'):
    d = ''.join('<details%s><summary>%s</summary><p>%s</p></details>' % (' open' if i == 0 else '', q, a) for i, (q, a) in enumerate(items))
    return '<section id="%s"><div class="w"><div class="sss"><h2>%s</h2><div>%s</div></div></div></section>' % (sid, title, d)

def faq_ld(items):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}

def sec(title, inner, tint=False, sid=''):
    return '<section%s%s><div class="w"><div class="sh one"><h2>%s</h2></div>%s</div></section>' % (
        ' class="tint"' if tint else '', ' id="%s"' % sid if sid else '', title, inner)

# ---------------- 1. İLETİŞİM ----------------
def p_iletisim():
    body = ('<section><div class="w"><div class="ctg">'
      '<a class="cc" href="tel:05444444004">%s<b>Telefon</b><span class="cbig">%s</span><p>Satış ve kurulum için doğrudan arayın.</p></a>'
      '<a class="cc" href="https://wa.me/905444444004?text=Merhaba%%2C%%20OnlineKaydet%%20hakk%%C4%%B1nda%%20bilgi%%20almak%%20istiyorum." rel="noopener" target="_blank">%s<b>WhatsApp</b><span class="cbig">Mesaj yazın</span><p>Soru sorun, ekran görüntüsü gönderin.</p></a>'
      '<a class="cc" href="/giris">%s<b>Müşteri girişi</b><span class="cbig">Panele gir</span><p>Mevcut müşteriler ve ustalar için.</p></a>'
      '</div></div></section>' % (ic('tel', 'o'), TEL, ic('chat', 'g'), ic('user', 'b')))
    body += cta('Sizi arayalım', 'Formu doldurun, sektörünüzü not alalım ve kurulum için sizi arayalım. 7 gün ücretsiz, kurulum ve veri aktarımı dahil.', 'form')
    return page('iletisim.html', 'İletişim | OnlineKaydet', 'OnlineKaydet ile iletişime geçin: telefon 0544 444 40 04, WhatsApp veya form. Servis takip programı için kurulum ve demo talebi.',
        'İletişim', 'Bizimle iletişime geçin', 'Telefonla arayın, WhatsApp\'tan yazın ya da formu doldurun; sektörünüze göre kurulumu birlikte planlayalım.',
        body, acts='<a class="bt" href="tel:05444444004">%s</a><a class="bt l" href="#form">Formu doldur</a>' % TEL)

# ---------------- 2. TEMALAR ----------------
SEKTOR_AD = {'kombi': 'Kombi', 'klima': 'Klima', 'beyaz_esya': 'Beyaz eşya', 'elektronik': 'Elektronik', 'bilgisayar': 'Bilgisayar', 'tesisat': 'Tesisat', 'elektrik': 'Elektrik', 'guvenlik': 'Güvenlik',
             'oto_servis': 'Oto servis', 'oto_cekici': 'Oto çekici', 'kuafor': 'Kuaför', 'nakliye': 'Nakliye', 'tekstil': 'Tekstil', 'eticaret': 'E-ticaret', 'temizlik': 'Temizlik', 'guzellik': 'Güzellik merkezi'}
def p_temalar():
    os.makedirs('tema-onizleme', exist_ok=True)
    src = os.path.join(os.path.dirname(D), 'themes', 'html')
    for f in os.listdir(src):
        if f.endswith('.html'):
            shutil.copy(os.path.join(src, f), os.path.join('tema-onizleme', f))
    th = json.load(open('themes.json', encoding='utf-8'))
    secs = {}
    for m in th:
        secs.setdefault(m['sector'], []).append(m)
    chips = '<button type="button" class="chip on" data-s="">Tümü <small>%d</small></button>' % len(th)
    inner = ''
    for sk, nm in SEKTOR_AD.items():
        L = secs.get(sk)
        if not L:
            continue
        chips += '<button type="button" class="chip" data-s="%s">%s <small>%d</small></button>' % (sk, nm, len(L))
        cards = ''.join('<a class="tm" href="tema-onizleme/%s.html" target="_blank" rel="noopener"><span class="sw"><i style="background:%s"></i><i style="background:%s"></i></span><b>%s</b><small>%s teması%s</small><span class="go">Önizle →</span></a>'
                        % (t['slug'], t.get('dark', '#0f1f46'), t.get('accent', '#f27a1a'), e(t.get('name') or nm), nm, ' · Premium' if t.get('premium') else '') for t in L)
        inner += '<div class="tgrp" data-s="%s"><h3 class="tg">%s</h3><div class="tmg">%s</div></div>' % (sk, nm, cards)
    feat = ('<section><div class="w"><div class="three">%s%s%s</div></div></section>' % (
        '<div>%s<b>Bir tıkla seçin</b><p>Sektörünüze uygun temayı seçin, firma adınız, telefonunuz ve logonuz otomatik yerleşir.</p></div>' % ic('web', 'b'),
        '<div>%s<b>Kendiniz düzenleyin</b><p>Menü, bölümler, kampanya ve fırsat alanları, görseller, yazılar ve mobil menü panelden değişir.</p></div>' % ic('pen', 'o'),
        '<div>%s<b>Formlar panele düşer</b><p>Randevu, teklif ve sipariş formlarından gelen talepler doğrudan panelinize kaydolur.</p></div>' % ic('bell', 'g')))
    css = ('<style>.chips{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 18px}.chip{border:1px solid var(--l);background:#fff;border-radius:99px;padding:10px 16px;font:600 14px/1 inherit;cursor:pointer;min-height:44px}'
           '.chip small{opacity:.6;margin-left:4px}.chip.on{background:var(--n);color:#fff;border-color:var(--n)}@media(max-width:900px){.tmg{grid-template-columns:repeat(2,1fr)}}@media(max-width:520px){.tmg{grid-template-columns:1fr}}</style>')
    js = ('<script>(function(){var c=document.querySelectorAll(".chip"),g=document.querySelectorAll(".tgrp");c.forEach(function(b){b.addEventListener("click",function(){c.forEach(function(x){x.classList.remove("on")});b.classList.add("on");'
          'var s=b.getAttribute("data-s");g.forEach(function(d){d.style.display=(!s||d.getAttribute("data-s")===s)?"":"none"})})});var h=location.hash.slice(1);if(h){c.forEach(function(b){if(b.getAttribute("data-s")===h)b.click()})}})();</script>')
    body = (feat + css + '<section class="tint"><div class="w"><div class="sh one"><h2>%d hazır tema, %d sektör</h2></div><div class="chips">%s</div>%s'
            '<p class="note2">Önizlemelerdeki görseller ve kampanya örnekleri örnektir; yayına almadan önce kendi fotoğraflarınızı, fiyat ve kampanyalarınızı girersiniz.</p></div></section>' % (len(th), len(secs), chips, inner) + js + cta())
    return page('temalar.html', 'Hazır Web Sitesi Temaları | Servis, Oto, Kuaför, Nakliye, E-ticaret | OnlineKaydet',
        'Teknik servis, oto servis, çekici, kuaför, nakliye, tekstil, e-ticaret, temizlik ve güzellik merkezi için hazır web sitesi temaları. Önizleyin, seçin, panelden düzenleyin.',
        'Temalar', 'İşinize uygun hazır web sitesi', 'Sektörünüze göre hazırlanmış %d tema. Seçin, firma bilgilerinizi girin, siteniz randevu veya sipariş formuyla birlikte yayına girsin.' % len(th), body)

# ---------------- 3. ENTEGRASYONLAR ----------------
def p_entegrasyon():
    body = sec('Müşteriye giden mesajlar', '<div class="fgrid">%s%s%s</div>' % (
        card('sms', 'o', 'SMS sağlayıcınızı bağlayın', 'Netgsm, Verimor ve İleti Merkezi hesabınızı panele girin; mesajlar kendi hesabınızdan gider. Twilio ve özel webhook ile de çalışır.'),
        card('bell', 'b', 'Hangi adımda mesaj gitsin', 'Randevu, usta yolda, servis tamamlandı gibi adımları siz seçersiniz. Mesaj metinlerini düzenleyebilirsiniz.'),
        card('chat', 'g', 'Yedek kanal', 'WhatsApp iletilemezse mesaj SMS ile gider (ayarı panelden açıp kapatırsınız).')), tint=True)
    body += sec('Yedek parça satışı', '<div class="fgrid">%s%s%s</div><p class="note2">Pazaryeri bağlantısı panelde kurulum sihirbazıyla yapılır; hesap bilgilerinizi siz girersiniz.</p>' % (
        card('cart', 'o', 'Trendyol', 'Yedek parça ürünlerinizi tek panelden yönetin.'),
        card('cart', 'b', 'Hepsiburada', 'Stok ve fiyat bilgisi ürün kartından yönetilir.'),
        card('cart', 'g', 'N11', 'Aynı ürün listesini N11\'de de kullanın.')))
    body += sec('Ödeme', '<div class="fgrid">%s%s</div>' % (
        card('card', 'p', 'iyzico ile kart ödemesi', 'Web sitenizden kartla ödeme almak için iyzico bilgilerinizi panele girin. Alan boşken ödeme düğmesi görünmez, doldurunca açılır.'),
        card('doc', 'o', 'Servis fişinde tahsilat', 'Usta tahsilat tutarını fişe işler; kasa takibinde görünür.')), tint=True)
    body += sec('Bilgi akışı', '<div class="fgrid">%s%s%s</div>' % (
        card('web', 'b', 'Web sitesi formları', 'Randevu, servis formu ve canlı destek mesajları firmanın kendi panelinde toplanır.'),
        card('chart', 'g', 'Google Search Console', 'Sitenizin arama performansı panelde izlenir.'),
        card('box', 'o', 'Excel aktarımı', 'Mevcut müşteri ve cihaz kayıtlarınızı biz aktarırız.')))
    items = [('Kendi SMS hesabım olmak zorunda mı?', 'Mesaj göndermek için bir SMS sağlayıcı hesabınız olmalı. Hesabınız yoksa kurulum sırasında hangisini seçeceğinizi birlikte belirleriz.'),
             ('Pazaryeri bağlantısı zorunlu mu?', 'Hayır. Yedek parça satmak istemiyorsanız bu bölüm kapalı kalır, panelde görünmez.')]
    body += faq('Entegrasyon hakkında sık sorulanlar', items) + cta()
    return page('entegrasyonlar.html', 'Entegrasyonlar: SMS, Pazaryeri, Ödeme | OnlineKaydet', 'OnlineKaydet servis programı SMS sağlayıcılar (Netgsm, Verimor, İleti Merkezi), Trendyol, Hepsiburada, N11 ve iyzico ile çalışır.',
        'Entegrasyonlar', 'SMS, pazaryeri ve ödeme bağlantıları', 'Müşterinize SMS gönderin, yedek parçayı pazaryerlerinde satın, web sitenizden kartla ödeme alın. Hepsi panelden ayarlanır.', body, ld=faq_ld(items))

# ---------------- 4. USTA UYGULAMASI ----------------
def p_usta():
    body = sec('Usta sahada ne yapar', '<div class="fgrid">%s%s%s%s%s%s</div>' % (
        card('user', 'b', 'Kendi işlerini görür', 'Usta telefonundan girer, kendisine atanan işleri sırayla görür.'),
        card('map', 'o', 'Adrese gider', 'Müşterinin adresi ve telefonu iş kartında; tek dokunuşla arar veya yol tarifi açar.'),
        card('cam', 'g', 'Önce ve sonra fotoğraf', 'Fotoğraf adımını siz açıp kapatırsınız; açıksa usta işe başlarken ve bitirirken çeker.'),
        card('pen', 'p', 'İmza', 'Müşteri imzayı telefon ekranına atar. İmza adımı da ayarlardan açılıp kapanır.'),
        card('doc', 'o', 'Servis fişi', 'İş bitince fiş PDF olarak hazırlanır, müşteriye gönderilir.'),
        card('bell', 'b', 'Müşteriye haber', 'Usta yolda ve servis tamamlandı adımlarında müşteriye otomatik SMS gider.')), tint=True)
    body += ('<section><div class="w"><div class="us"><div><h2>Yöneticide ne değişir</h2><ol class="seq">'
      '<li><i></i><time>1</time><div><b>Kaydı siz açarsınız</b><p>Müşteri, cihaz marka ve modeli, arıza ve randevu bilgisi girilir.</p></div></li>'
      '<li><i></i><time>2</time><div><b>Ustayı atarsınız</b><p>İş seçtiğiniz ustanın telefonuna düşer.</p></div></li>'
      '<li><i></i><time>3</time><div><b>Süreci izlersiniz</b><p>Usta işe başladı, tamamladı, tahsilat yaptı; hepsi panelde görünür.</p></div></li></ol></div>'
      '<div class="fis"><div class="top"><span>Servis kaydı</span><span>Örnek</span></div><dl><dt>Müşteri</dt><dd>Ad, adres, telefon</dd><dt>Cihaz</dt><dd>Marka ve model</dd><dt>Atanan usta</dt><dd>Panelden seçilir</dd><dt>Durum</dt><dd>Yolda / Tamamlandı</dd></dl><div class="ftr"><span>Fiş formatı düzenlenebilir</span></div></div></div></div></section>')
    items = [('Uygulamayı indirmem gerekiyor mu?', 'Usta, panele telefonunun tarayıcısından giriş yapar. Ana ekrana ekleyerek uygulama gibi kullanabilir.'),
             ('Adımları değiştirebilir miyim?', 'Evet. Servis Ayarları bölümünden fotoğraf ve imza adımlarını açıp kapatır, fiş biçimini düzenlersiniz.')]
    body += faq('Usta uygulaması hakkında sık sorulanlar', items) + cta()
    return page('usta-uygulamasi.html', 'Usta Uygulaması | Servis Takip | OnlineKaydet', 'Ustanız işlerini telefondan görsün, fotoğraf çeksin, müşteriye imza attırsın, servis fişi otomatik oluşsun. OnlineKaydet usta ekranı.',
        'Usta uygulaması', 'Ustanız sahada, kayıt anında panelde', 'İşi usta telefonundan görür, fotoğraf çeker, müşteriye imza attırır. Siz ofisten aynı kaydı izlersiniz.', body, ld=faq_ld(items))

# ---------------- 5. NEDEN ----------------
def p_neden():
    body = sec('Defter, Excel ve mesaj grupları yerine', '<div class="fgrid">%s%s%s%s%s%s</div>' % (
        card('doc', 'o', 'Kayıt kaybolmaz', 'Her iş müşteri, cihaz, usta ve tahsilatıyla tek kayıtta durur.'),
        card('user', 'b', 'Usta takibi', 'Hangi usta hangi işte, kim ne tahsil etti panelden görünür.'),
        card('bell', 'g', 'Müşteri haberdar', 'Randevu ve tamamlanma mesajları kendiliğinden gider.'),
        card('web', 'p', 'Site ve panel bir arada', 'Sitedeki randevu formu doğrudan servis paneline kayıt düşer.'),
        card('box', 'o', 'Sektöre göre kurulum', 'Marka, model ve arıza listeleri sektörünüze göre hazır gelir.'),
        card('shield', 'b', 'Verileriniz sizin', 'Her firmanın kaydı kendi veritabanında tutulur.'), ), tint=True)
    body += ('<section><div class="w"><div class="sh one"><h2>Nasıl başlarsınız</h2></div><ol class="seq steps">'
      '<li><i></i><time>1</time><div><b>Arayın ya da form doldurun</b><p>Sektörünüzü ve usta sayınızı öğreniriz.</p></div></li>'
      '<li><i></i><time>2</time><div><b>Kurulumu biz yaparız</b><p>Firma bilgileriniz, marka ve modeller, tema ve fiş biçimi hazırlanır.</p></div></li>'
      '<li><i></i><time>3</time><div><b>Ustalarınız çalışmaya başlar</b><p>7 gün ücretsiz; sonrasında paketinizi seçersiniz.</p></div></li></ol></div></section>')
    body += cta()
    return page('neden-onlinekaydet.html', 'Neden OnlineKaydet? | Servis Takip Programı', 'Servis kaydı, usta takibi, SMS ve web sitesi tek yerde. OnlineKaydet teknik servisler için hazırlandı; kurulumu biz yaparız, 7 gün ücretsiz.',
        'Neden OnlineKaydet?', 'Servis işi için yapılmış bir program', 'Genel amaçlı bir yazılımı servise uydurmak yerine, servis kaydı ve usta takibi için baştan yazıldı.', body)

# ---------------- 6. BLOG ----------------
POSTS = [
 ('servis-takip-programi-nedir', 'Servis takip programı nedir, ne işe yarar?', 'Servis takip programının ne yaptığını, kimlerin kullandığını ve seçerken nelere bakılacağını anlatıyoruz.',
  '<p>Servis takip programı, teknik servisin işlerini tek yerde tutan yazılımdır. Müşteri aradığında açılan kayıt, ustaya atanan iş, yapılan işlem, alınan para ve gönderilen servis fişi aynı ekranda toplanır.</p>'
  '<h2>Hangi sorunu çözer?</h2><p>Defter ve Excel ile çalışan servislerde üç şey sık kaybolur: müşterinin adresi ve cihazı, ustanın yaptığı işlemin ayrıntısı, tahsil edilen tutar. Program bu üçünü her işe bağlı tutar. Aynı müşteri tekrar aradığında geçmiş kaydı hemen görünür.</p>'
  '<h2>Seçerken nelere bakılır?</h2><ul><li>Usta telefonundan kullanabiliyor mu?</li><li>Müşteriye otomatik mesaj gidiyor mu?</li><li>Servis fişi kendi firma bilginizle çıkıyor mu?</li><li>Eski kayıtlarınızı aktarabiliyor musunuz?</li><li>Kurulumu kim yapıyor?</li></ul>'
  '<p>OnlineKaydet bu soruların hepsine evet cevabı verecek şekilde hazırlandı; ayrıntılar için <a href="ozellikler.html">özellikler sayfasına</a> bakabilirsiniz.</p>'),
 ('servis-fisi-nasil-hazirlanir', 'Servis fişinde bulunması gereken bilgiler', 'Müşteriye verdiğiniz servis fişinde hangi bilgiler yer almalı? Kontrol listesi.',
  '<p>Servis fişi, yapılan işin müşteriyle yazılı mutabakatıdır. Sonradan çıkabilecek "bunu yapmadınız" ya da "bu kadar tutmazdı" tartışmalarında elinizdeki tek belge odur.</p>'
  '<h2>Fişte olması gerekenler</h2><ul><li>Firma adı, telefonu ve adresi</li><li>Fiş numarası ve tarih</li><li>Müşterinin adı, adresi ve telefonu</li><li>Cihazın markası, modeli ve varsa seri numarası</li><li>Bildirilen arıza ve yapılan işlem</li><li>Değiştirilen parçalar ve tutarları</li><li>İşçilik ve toplam tutar, ödeme şekli</li><li>Müşteri imzası</li></ul>'
  '<h2>Kâğıt yerine dijital fiş</h2><p>Fiş telefonda doldurulursa okunaklı olur, kaybolmaz ve müşteriye PDF olarak gönderilebilir. OnlineKaydet\'te fişin biçimini ve adımlarını Servis Ayarları bölümünden değiştirebilirsiniz.</p>'),
 ('servis-kaydi-bilgileri', 'Servis kaydı açarken hangi bilgileri almalısınız?', 'Telefon açıldığında müşteriden istenecek bilgilerin kısa listesi.',
  '<p>İyi bir servis kaydı, ustanın sahada ikinci kez aramasına gerek bırakmaz. Telefonda şu bilgileri almak yeterli olur:</p>'
  '<ul><li><b>Müşteri:</b> ad soyad, telefon, tam adres ve tarif</li><li><b>Cihaz:</b> marka, model ve kaç yaşında olduğu</li><li><b>Arıza:</b> müşterinin kendi cümleleriyle, varsa hata kodu</li><li><b>Randevu:</b> gün ve saat aralığı</li><li><b>Atanan usta:</b> kim gidecek</li></ul>'
  '<p>Kombi gibi hata kodu veren cihazlarda kodu baştan yazmak ustanın yanına doğru parçayı almasını sağlar; örnekler için <a href="hata-kodlari.html">hata kodları sayfasına</a> bakın.</p>'
  '<p>OnlineKaydet\'te marka ve modeller önceden eklediğiniz katalogdan seçilir, böylece aynı cihaz farklı yazımlarla kaydedilmez.</p>'),
]
def p_blog():
    cards = ''.join('<a class="bl" href="blog-%s.html"><b>%s</b><p>%s</p><span class="go">Oku →</span></a>' % (s, t, d) for s, t, d, _ in POSTS)
    body = '<section><div class="w"><div class="blg">%s</div></div></section>' % cards + cta()
    page('blog.html', 'Blog | Servis Takip ve Teknik Servis Yönetimi | OnlineKaydet', 'Teknik servisler için servis kaydı, servis fişi ve usta takibi üzerine kısa rehberler.', 'Blog', 'Teknik servisler için rehberler', 'Servis kaydı, servis fişi ve usta takibi üzerine kısa, uygulanabilir yazılar.', body)
    for s, t, d, c in POSTS:
        art = '<section><div class="w"><article class="art">%s<p class="note2">Bir sorunuz mu var? <a href="iletisim.html">Bize yazın</a> ya da %s numarasını arayın.</p></article></div></section>' % (c, TEL) + cta()
        page('blog-%s.html' % s, t + ' | OnlineKaydet', d, '<a href="blog.html">Blog</a> / ' + t, t, d, art,
             ld={"@context": "https://schema.org", "@type": "Article", "headline": t, "description": d, "author": {"@type": "Organization", "name": "OnlineKaydet"}, "publisher": {"@type": "Organization", "name": "OnlineKaydet"}, "mainEntityOfPage": "https://onlinekaydet.com/blog-%s.html" % s})
    return 'blog'

# ---------------- 7. DESTEK ----------------
def p_destek():
    items = [
     ('Kurulum için teknik bilgi gerekir mi?', 'Hayır. Kurulumu biz yaparız; firma bilgilerinizi göndermeniz yeterli.'),
     ('Ustalar uygulamayı nasıl kullanır?', 'Usta telefonundan giriş yapar, kendi işlerini görür, fotoğraf çeker ve fişi müşteriye imzalatır.'),
     ('İlk ay gerçekten ücretsiz mi?', 'Evet. Kurulum ve veri aktarımı da bu süreye dahil.'),
     ('Müşteriye SMS gidiyor mu?', 'Randevu, usta yolda ve servis tamamlandı adımlarında otomatik SMS gider. Kendi SMS sağlayıcı hesabınızı bağlarsınız.'),
     ('Web sitesi dahil mi?', 'Hazır temalardan birini seçersiniz. Randevu formu doğrudan servis panelinize kayıt düşer.'),
     ('Mevcut kayıtlarımı taşıyabilir miyim?', 'Excel veya defter kayıtlarınızı biz aktarırız.'),
     ('Şifremi unuttum, ne yapmalıyım?', 'Giriş ekranından şifre yenileyebilir ya da bizi arayabilirsiniz.'),
     ('Fiş biçimini değiştirebilir miyim?', 'Evet. Servis menüsündeki Servis Ayarları bölümünden fişi ve kayıt adımlarını düzenlersiniz.')]
    body = ('<section><div class="w"><div class="ctg">'
      '<a class="cc" href="tel:05444444004">%s<b>Telefonla destek</b><span class="cbig">%s</span><p>Kurulum ve kullanım soruları için.</p></a>'
      '<a class="cc" href="https://wa.me/905444444004" rel="noopener" target="_blank">%s<b>WhatsApp</b><span class="cbig">Yazın</span><p>Ekran görüntüsüyle sorun anlatın.</p></a>'
      '<a class="cc" href="hata-kodlari.html">%s<b>Hata kodları</b><span class="cbig">Kod sözlüğü</span><p>Cihaz hata kodlarının anlamları.</p></a></div></div></section>' % (ic('tel', 'o'), TEL, ic('chat', 'g'), ic('shield', 'b')))
    body += faq('Sık sorulan sorular', items)
    return page('destek.html', 'Destek ve Sık Sorulan Sorular | OnlineKaydet', 'OnlineKaydet kurulum, usta uygulaması, SMS ve fatura konusunda sık sorulan sorular ve destek hattı.',
        'Destek', 'Destek ve sık sorulan sorular', 'Aradığınız cevap burada yoksa telefonla ya da WhatsApp\'tan yazın.', body, ld=faq_ld(items))

# ---------------- 8. HESAPLAMA ----------------
CALC_JS_KOM = ('<script>(function(){function g(i){return parseFloat(String(document.getElementById(i).value).replace(",","."))||0}'
 'function f(n){return n.toLocaleString("tr-TR",{minimumFractionDigits:2,maximumFractionDigits:2})+" ₺"}'
 'function h(){var s=g("k_s"),a=g("k_a"),k=g("k_k"),c=g("k_c"),h=g("k_h"),x=g("k_x");var com=s*k/100,kdv=com*0.20,net=s-com-kdv-c-h-x;'
 'document.getElementById("o_com").textContent=f(com);document.getElementById("o_kdv").textContent=f(kdv);document.getElementById("o_net").textContent=f(net);'
 'document.getElementById("o_marj").textContent=a>0?"%"+(net/a*100).toFixed(1).replace(".",","):"-";document.getElementById("o_kar").textContent=f(net-a);}'
 '["k_s","k_a","k_k","k_c","k_h","k_x"].forEach(function(i){document.getElementById(i).addEventListener("input",h)});h()})()</script>')
def p_komisyon():
    body = ('<section><div class="w"><div class="calc"><div class="cin">'
      '<div><label for="k_s">Satış fiyatı (₺)</label><input id="k_s" inputmode="decimal" value="1000"></div>'
      '<div><label for="k_a">Alış (parça) maliyeti (₺)</label><input id="k_a" inputmode="decimal" value="600"></div>'
      '<div><label for="k_k">Pazaryeri komisyonu (%)</label><input id="k_k" inputmode="decimal" value="15"></div>'
      '<div><label for="k_c">Kargo (₺)</label><input id="k_c" inputmode="decimal" value="60"></div>'
      '<div><label for="k_h">Hizmet bedeli (₺)</label><input id="k_h" inputmode="decimal" value="0"></div>'
      '<div><label for="k_x">Diğer gider (₺)</label><input id="k_x" inputmode="decimal" value="0"></div></div>'
      '<dl class="cout"><dt>Komisyon tutarı</dt><dd id="o_com">-</dd><dt>Komisyon KDV\'si (%20)</dt><dd id="o_kdv">-</dd><dt>Net kalan</dt><dd id="o_net">-</dd><dt>Kâr</dt><dd id="o_kar">-</dd><dt>Kâr marjı (alışa göre)</dt><dd id="o_marj">-</dd></dl></div>'
      '<p class="note2">Komisyon oranını pazaryerindeki kategori oranınıza göre kendiniz girin; oranlar kategoriye göre değişir ve burada sabit değer verilmez. Komisyon KDV\'si %20 alınmıştır, farklıysa net tutarı buna göre değerlendirin.</p></div></section>' + cta() + CALC_JS_KOM)
    return page('komisyon-hesaplama.html', 'Pazaryeri Komisyon Hesaplama | Yedek Parça Kâr Hesabı', 'Trendyol, Hepsiburada, N11 için komisyon, kargo ve maliyeti girin; net kalan tutarı ve kâr marjını görün.',
        'Komisyon hesaplama', 'Pazaryeri komisyon ve kâr hesaplama', 'Yedek parça satarken komisyon, kargo ve alış maliyeti düştükten sonra elinize ne kaldığını hesaplayın.', body,
        acts='<a class="bt" href="entegrasyonlar.html">Pazaryeri bağlantıları</a>')

CALC_JS_DESI = ('<script>(function(){function g(i){return parseFloat(String(document.getElementById(i).value).replace(",","."))||0}'
 'function h(){var d=g("d_e")*g("d_b")*g("d_y")/3000,k=g("d_k"),n=Math.max(d,k);'
 'document.getElementById("o_d").textContent=d.toFixed(2).replace(".",",");document.getElementById("o_n").textContent=n.toFixed(2).replace(".",",")+(d>k?" (desi)":" (kg)")}'
 '["d_e","d_b","d_y","d_k"].forEach(function(i){document.getElementById(i).addEventListener("input",h)});h()})()</script>')
def p_desi():
    body = ('<section><div class="w"><div class="calc"><div class="cin">'
      '<div><label for="d_e">En (cm)</label><input id="d_e" inputmode="decimal" value="30"></div>'
      '<div><label for="d_b">Boy (cm)</label><input id="d_b" inputmode="decimal" value="40"></div>'
      '<div><label for="d_y">Yükseklik (cm)</label><input id="d_y" inputmode="decimal" value="20"></div>'
      '<div><label for="d_k">Gerçek ağırlık (kg)</label><input id="d_k" inputmode="decimal" value="5"></div></div>'
      '<dl class="cout"><dt>Hacimsel ağırlık (desi)</dt><dd id="o_d">-</dd><dt>Ücrete esas değer</dt><dd id="o_n">-</dd></dl></div>'
      '<p class="note2">Desi = en × boy × yükseklik ÷ 3000. Kargo firması desi ile gerçek ağırlıktan büyük olanı esas alır. Bazı firmalar farklı bölen kullanabilir; sözleşmenizi kontrol edin.</p></div></section>' + cta() + CALC_JS_DESI)
    return page('desi-hesaplama.html', 'Desi Hesaplama Aracı | Kargo Ağırlığı', 'En, boy ve yüksekliği girin; desi ve ücrete esas kargo ağırlığını hesaplayın.',
        'Desi hesaplama', 'Desi hesaplama aracı', 'Yedek parça gönderirken paketin desisini ve kargonun ücrete esas alacağı değeri hesaplayın.', body,
        acts='<a class="bt" href="komisyon-hesaplama.html">Komisyon hesapla</a>')

PAGES = [p_iletisim, p_temalar, p_entegrasyon, p_usta, p_neden, p_blog, p_destek, p_komisyon, p_desi]
NEW = ['iletisim', 'tema-onizleme', 'entegrasyonlar', 'usta-uygulamasi', 'neden-onlinekaydet', 'blog', 'destek', 'komisyon-hesaplama', 'desi-hesaplama'] + ['blog-' + p[0] for p in POSTS]

def update_all():
    for f in os.listdir('.'):
        if f.endswith('.html'):
            s = open(f, encoding='utf-8').read()
            n = apply_chrome(s)
            if n != s:
                open(f, 'w', encoding='utf-8').write(n)

def sitemap():
    sm = open('sitemap.xml', encoding='utf-8').read()
    add = ''
    for n in NEW:
        u = 'https://onlinekaydet.com/%s.html' % n
        if u not in sm:
            add += '<url><loc>%s</loc></url>\n' % u
    if add:
        sm = sm.replace('</urlset>', add + '</urlset>')
        open('sitemap.xml', 'w', encoding='utf-8').write(sm)

if __name__ == '__main__':
    for p in PAGES: p()
    update_all(); sitemap()
    print('ok', len(NEW), 'sayfa')
