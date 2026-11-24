#!/usr/bin/env python3
"""Rakip karşılaştırma + niyet sayfaları. Çalıştır: python3 site/gen_seo_karsilastirma.py
Kurallar: rakip hakkında yalnız kendi herkese açık sayfasında yazanlar; bizim için yalnız fiyatlar.html'deki gerçek bilgiler. Arama hacmi iddiası yok."""
import os, re
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gen_sayfalar.py'), encoding='utf-8').read()
import html, json
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
TEL = '0544 444 40 04'
def e(s): return html.escape(s, quote=True)
exec(compile(_src[_src.index('ICO = {'):re.search(r'# -+ 1\. ', _src).start()], 'gen_head', 'exec'))
SHELL = open('blog-servis-takip-programi-nedir.html', encoding='utf-8').read()
A0 = '</svg><div class="eski"><div id="icerik">\n'; A1 = '\n</div></div></main>'
def page(fn, title, desc, crumb, h1, lead, body, acts=None, ld=None):
    acts = acts or '<a class="bt" href="/iletisim.html#teklif">Ücretsiz deneyin</a><a class="bt l" href="tel:05444444004">%s</a>' % TEL
    url = 'https://onlinekaydet.com/' + fn
    h = SHELL
    h = re.sub(r'<title>.*?</title>', '<title>%s</title>' % e(title), h, count=1, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % e(desc), h, count=1)
    h = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="%s">' % url, h, count=1)
    h = re.sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="%s">' % e(title), h, count=1)
    h = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="%s">' % e(desc), h, count=1)
    h = re.sub(r'<meta property="og:url" content="[^"]*">', '<meta property="og:url" content="%s">' % url, h, count=1)
    h = re.sub(r'<script type="application/ld\+json">.*?</script>', '', h, flags=re.S)
    if ld: h = h.replace('</head>', '<script type="application/ld+json">%s</script></head>' % json.dumps(ld, ensure_ascii=False), 1)
    i = h.index(A0) + len(A0); j = h.index(A1)
    hero = ('<div class="pgh"><div class="w"><div><nav class="crumb" aria-label="Sayfa yolu"><a href="index.html">Ana sayfa</a> / %s</nav>'
            '<h1>%s</h1><p>%s</p><div class="acts">%s</div></div></div></div>\n' % (crumb, h1, lead, acts))
    open(fn, 'w', encoding='utf-8').write(h[:i] + hero + body + h[j:])
    return fn
STIL = ('<style>.kk{padding:56px 0}.kk.t{background:#f3f4f8}.kk h2{font:700 30px/1.15 var(--fd,inherit);margin:0 0 22px;letter-spacing:-.02em}'
 '.kt{border:1px solid #d9dce6;border-radius:12px;background:#fff;overflow:hidden;max-width:980px}.kt .r{display:grid;grid-template-columns:230px 1fr;gap:20px;padding:14px 20px;border-top:1px solid #e6e8ef}'
 '.kt .r:first-child{border-top:0}.kt .r b{font-weight:600}.kt .r span{color:#3b4152;line-height:1.55}.kt.p .r{grid-template-columns:150px 150px 1fr}.kt .h{background:#0a0c0f;color:#fff;font-weight:600}.kt .h span{color:#fff}'
 '.kk p.mini{font-size:14px;color:#5b6173;max-width:760px;margin-top:18px}.kk p{max-width:720px;line-height:1.7}.kk ul{max-width:760px;line-height:1.8;padding-left:20px}'
 '@media(max-width:700px){.kk{padding:36px 0}.kk h2{font-size:24px}.kt .r,.kt.p .r{grid-template-columns:1fr;gap:4px}}</style>')
def kt(rows, head=None, cls=''):
    h = '<div class="r h">%s</div>' % ''.join('<span>%s</span>' % x for x in head) if head else ''
    return '<div class="kt %s">%s%s</div>' % (cls, h, ''.join('<div class="r">%s</div>' % ''.join('<%s>%s</%s>' % (('b' if i == 0 else 'span'), c, ('b' if i == 0 else 'span')) for i, c in enumerate(r)) for r in rows))
def sec(title, inner, tint=False, sid=''):
    return '<section class="kk%s"%s><div class="w"><h2>%s</h2>%s</div></section>' % (' t' if tint else '', ' id="%s"' % sid if sid else '', title, inner)
TARIH = '24 Kasım 2026'
NOT = ('<p class="mini">Karşılaştırdığımız ürünün bilgileri, ürünün kendi herkese açık sayfasından %s tarihinde alındı. Özellikler ve fiyatlar değişebilir; '
       'güncel durum için ürünün kendi sitesine bakın. Fiyatını bu sayfada yazmıyoruz.</p>' % TARIH)
OURS = [('Servis ve iş kayıtları', 'Sektörün kendi adıyla (servis formu, dava dosyası, muayene, iş emri); yazdırılabilir imzalı belge'),
        ('Ekip ve usta takibi', 'Ekip, yetki, iş yükü; prim, maaş, avans hesabı'),
        ('Kasa ve muhasebe', 'Tahsilat, gider, gün sonu, cari ve alacak takibi, 17 hazır rapor'),
        ('Müşteriye mesaj', 'SMS ve mesaj şablonları, bakım hatırlatma, QR etiket'),
        ('Web sitesi', 'Hazır tema, her bölümü düzenlenen site editörü, SEO başlıkları, kendi alan adınız'),
        ('Online randevu ve mağaza', 'Siteden randevu, yedek parça mağazası; Kurumsal pakette e-ticaret ve pazaryerleri'),
        ('Fiyat', 'Aylık 990 ₺ + KDV\'den başlar; yıllık ödemede 2 ay bizden. 7 gün ücretsiz')]
RIV = {
 'takip-online': dict(ad='Takip Online', url='takiponline.com', ne='bulut tabanlı teknik servis yazılımı',
   bilgi=[('Servis kaydı', 'Müşteri, cihaz, marka, servis türü ve teslim bilgileriyle kasiyer ekranından kayıt açılır'),
          ('Geçmiş', 'Takip no veya seri no ile eski servis kayıtları açılır'),
          ('Saha', 'Android uygulamasında servis fişi Bluetooth yazıcıya basılır'),
          ('Evrak', 'Teklif, form ve servis evrakları arşivlenir'),
          ('Ek modül', 'Asansör modülü sayfasında belirtiliyor')],
   fark='Takip Online\'ın sayfası servis kaydı, saha uygulaması ve evrak arşivine odaklanıyor. Web sitesi ve online mağaza tarafı o sayfada öne çıkmıyor; sitesini ayrı bir yerden yaptıranlar için bu bir artı olabilir.',
   uygun='Servisiniz için en önemli şey sahadaki teknisyenin Android uygulamasından Bluetooth yazıcıya fiş basması ise Takip Online\'ı da deneyin; bu özelliğin bizde olup olmadığını satış görüşmesinde net soruyoruz ve size açıkça söylüyoruz.'),
 'evo-bulut': dict(ad='Evo Bulut', url='evobulut.com', ne='bulut ve mobil çalışan teknik servis programı',
   bilgi=[('Süreç', 'Arıza kaydından teknisyene, yedek parçadan teslim ve faturaya servis süreci'),
          ('Müşteri bilgilendirme', 'Servis kaydına özel takip bağlantısı SMS, WhatsApp, e-posta veya QR ile paylaşılır'),
          ('Fatura', 'E-Fatura bağlantısı sayfada belirtiliyor'),
          ('Saha', 'Teknisyen sahadan mobil çalışır')],
   fark='Evo Bulut müşteriye özel online servis sorgulama bağlantısını öne çıkarıyor. OnlineKaydet\'in farkı servis takibinin yanında web sitesi, online randevu ve mağazanın aynı panelde olması.',
   uygun='Müşterinizin cihazını bağlantıyla kendi kendine sorgulaması sizin için ilk sıradaysa Evo Bulut\'un bu özelliğini mutlaka inceleyin.'),
 'pazarus': dict(ad='Pazarus', url='pazarus.io', ne='bulut tabanlı teknik servis takip programı',
   bilgi=[('Kapsam', 'Servis fişinden müşteri takibine, teklif onayı, tutanak ve e-faturaya kadar tek panel'),
          ('Kurulum', 'Bulut tabanlı; kurulum gerektirmediği belirtiliyor')],
   fark='Pazarus servis, teklif onayı ve e-fatura akışını tek panelde topluyor. OnlineKaydet bu akışa ek olarak müşterinin sizi bulacağı web sitesini ve randevu sayfasını da panelden yönetmenizi sağlıyor.',
   uygun='Teklif onayı ve tutanak sizin için günlük iş akışının merkezindeyse Pazarus\'un bu bölümünü kendi işinizle karşılaştırın.'),
 'opwire': dict(ad='Opwire', url='opwire.app', ne='teknik servis programı',
   bilgi=[('İş takibi', 'İş emri, teslimat, bakım, tamir ve değişim süreçleri online takip edilir'),
          ('Mobil', 'Mobil uygulamayla sahadan anlık veri aktarımı')],
   fark='Opwire iş emri ve saha verisine odaklanıyor. OnlineKaydet\'te ek olarak kasa, prim ve maaş hesabı, 17 hazır rapor ve web sitesi aynı pakette.',
   uygun='Sahadan anlık veri girişi ve iş emri akışı tek önceliğinizse Opwire\'ın mobil uygulamasını da deneyin.'),
 'wolvox': dict(ad='Wolvox Servis (Akınsoft)', url='akinsoft.com.tr', ne='Akınsoft\'un Wolvox ürün ailesindeki servis yönetimi programı',
   bilgi=[('Kapsam', 'Servis yönetimi modülü; marka ve ürün takibi sayfada özellik olarak sayılıyor'),
          ('Aile', 'Sayfada Reporter (Android ve iOS) gibi ilgili programlar da listeleniyor')],
   fark='Wolvox ticari yazılım ailesinin bir parçası olduğu için ön muhasebe ve stok programlarıyla birlikte düşünülüyor. OnlineKaydet bulutta çalışır, kurulum istemez ve servis işinin yanında web sitenizi de içerir.',
   uygun='Zaten Wolvox ile stok ve muhasebe yürütüyorsanız servis modülünü aynı ailede tutmak sizin için sade olabilir. Önce bu kararı verin, sonra bizimle karşılaştırın.'),
 'mikro': dict(ad='Mikro Fly Tamir / Teknik Servis', url='mikro.com.tr', ne='Mikro Fly\'ın sektörel çözümlerinden tamir ve teknik servis yönetimi modülü',
   bilgi=[('Kapsam', 'Servis noktalarının tüm aşamalarda yönetimi sayfada anlatılıyor'),
          ('Aile', 'Mikro Fly sektörel çözümlerinden biri')],
   fark='Mikro Fly, Mikro\'nun ticari yazılım çatısı altında bir modül. OnlineKaydet yalnız servis ve esnaf işine odaklı, aylık paketle başlıyor ve web sitesini de içeriyor.',
   uygun='Mikro ile muhasebe ve ticari işlemlerinizi yürütüyorsanız modülü aynı yerde tutmak mantıklı olabilir.'),
}
def tablo(r):
    return ('<h2>%s sayfasında yazanlar</h2>%s<h2 style="margin-top:44px">OnlineKaydet\'te olanlar</h2>%s%s'
            % (r['ad'], kt(r['bilgi']), kt(OURS), NOT))
def rakip(slug, r):
    fn = '%s-alternatifi.html' % slug
    soru = [('%s yerine OnlineKaydet kullanılır mı?' % r['ad'], 'Evet. Servis kaydı, usta takibi, kasa ve raporlar OnlineKaydet\'te de var. Geçerken kayıtlarınızı Excel\'den aktarmanıza yardım ediyoruz; önce ücretsiz 7 günde kendi işinizle deneyin.'),
            ('OnlineKaydet\'in %s\'dan farkı ne?' % r['ad'], r['fark']),
            ('Fiyatı ne kadar?', 'OnlineKaydet 990 ₺ + KDV\'den (aylık) başlar; yıllık ödemede iki ay bizden. Paketlerin satır satır içeriği fiyatlar sayfasında.'),
            ('Hangi durumda %s daha uygun olabilir?' % r['ad'], r['uygun'])]
    body = (STIL + '<section class="kk"><div class="w">%s</div></section>' % tablo(r)
            + sec('Fark ne?', '<p>%s</p>' % r['fark'], tint=True)
            + sec('%s mı, OnlineKaydet mi?' % r['ad'], '<p>%s</p>' % r['uygun'])
            + faq('Sık sorulan sorular', soru) + cta())
    page(fn, '%s alternatifi: OnlineKaydet ile karşılaştırma' % r['ad'],
         '%s (%s) ile OnlineKaydet\'i karşılaştırın: ürünün kendi sayfasında yazanlar, OnlineKaydet\'te olanlar ve hangi durumda hangisi uygun. Fiyat 990 ₺ + KDV\'den, 7 gün ücretsiz.' % (r['ad'], r['ne']),
         '<a href="servis-takip-programi-karsilastirma.html">Servis takip programı karşılaştırma</a> / %s' % r['ad'],
         '%s alternatifi: OnlineKaydet ile karşılaştırma' % r['ad'],
         '%s ile OnlineKaydet\'in neyi nasıl yaptığını, ürünlerin kendi anlattıklarına göre yan yana koyduk.' % r['ad'],
         body, ld=faq_ld(soru))
    return fn
def hub():
    li = ''.join('<a class="cc" href="%s-alternatifi.html"><b>%s</b><p>%s</p></a>' % (s, r['ad'], r['ne'][0].upper() + r['ne'][1:]) for s, r in RIV.items())
    kont = [('Usta telefonundan kullanabiliyor mu?', 'Sahadaki teknisyen işi nereden açacak?'),
            ('Müşteriye mesaj ya da takip bağlantısı gidiyor mu?', 'Müşteri aramadan durumu öğrenebilmeli.'),
            ('Servis fişi kendi firma bilginizle çıkıyor mu?', 'Yazdırılabilir, imzalı belge.'),
            ('Kasa ve alacak aynı yerde mi?', 'Tahsilat, gider ve cari bir arada olmalı.'),
            ('Web sitenizi de yönetiyor mu?', 'Yeni müşteri bulmak için site ve randevu.'),
            ('Eski kayıtlarınızı aktarıyor mu?', 'Excel ya da defterden geçiş.'),
            ('Kurulum ve fiyat net mi?', 'Aylık paket, gizli modül ücreti var mı?'),
            ('Deneme süresi var mı?', 'Kendi işinizle önce deneyin.')]
    kl = ''.join('<li><b>%s</b> %s</li>' % (a, b) for a, b in kont)
    soru = [('Servis takip programı seçerken nelere bakılır?', 'Usta telefonundan kullanım, müşteriye mesaj, servis fişi, kasa ve alacak takibi, eski kayıtların aktarımı, kurulum ve net fiyat. Sekiz maddelik listeyi bu sayfada bulabilirsiniz.'),
            ('En iyi servis takip programı hangisi?', 'Tek bir en iyisi yok; işinize göre değişir. Her ürünün kendi sitesinde yazanları ve OnlineKaydet\'te olanları yan yana koyduk. Hepsini ücretsiz ya da denemeyle kendi işinizle deneyin.')]
    body = (STIL + '<section class="kk"><div class="w"><div class="ctg">%s</div></div></section>' % li
            + sec('Karşılaştırırken sorulacak 8 soru', '<ul>%s</ul>' % kl, tint=True)
            + faq('Sık sorulan sorular', soru) + cta())
    page('servis-takip-programi-karsilastirma.html', 'Servis takip programı karşılaştırma: Takip Online, Evo Bulut, Pazarus ve diğerleri',
         'Servis takip programlarını karşılaştırın: Takip Online, Evo Bulut, Pazarus, Opwire, Wolvox Servis, Mikro Fly ve OnlineKaydet. Seçerken sorulacak 8 soru.',
         'Servis takip programı karşılaştırma', 'Servis takip programı karşılaştırma',
         'Piyasadaki başlıca teknik servis programlarını, kendi sayfalarında yazdıklarına göre ayrı ayrı karşılaştırdık.', body, ld=faq_ld(soru))
def fiyat():
    soru = [('Servis takip programı fiyatları ne kadar?', 'OnlineKaydet\'te dört paket var: Başlangıç 990 ₺, Profesyonel 1.990 ₺, Tam Paket 3.490 ₺, Kurumsal 5.990 ₺ (aylık, + KDV). Yıllık ödemede iki ay bizden.'),
            ('Ek modül ücreti var mı?', 'Hayır. Kurumsal pakette e-ticaret dahil tüm özellikler açıktır; ek ücret ya da ek modül yok.'),
            ('Başlangıç paketinde neler var?', 'İş ve servis kayıtları, ekip ve yetki, sektörel iş akışı ve yazdırılabilir imzalı belge.')]
    pk = [('Başlangıç', '990 ₺', 'İş ve servis kayıtları, ekip ve yetki, sektörel iş akışı, yazdırılabilir imzalı belge'),
          ('Profesyonel', '1.990 ₺', 'Başlangıç\'taki her şey; muhasebe ve kasa, 17 hazır rapor, SMS ve mesaj şablonları, prim, maaş, avans'),
          ('Tam Paket', '3.490 ₺', 'Profesyonel\'deki her şey; web sitesi ve hazır temalar, site editörü, SEO, alan adı, online randevu, yedek parça mağazası'),
          ('Kurumsal', '5.990 ₺', 'Tam Paket\'teki her şey; bayi ve müşteri portalı, teklif, ödeme linki, e-arşiv, bakım hatırlatma, canlı saha takibi, e-ticaret')]
    t = kt([(a, b + ' / ay + KDV', c) for a, b, c in pk], head=('Paket', 'Fiyat', 'İçerik'), cls='p')
    body = (STIL + '<section class="kk"><div class="w">%s'
            '<p class="mini">Yıllık ödemede iki ay bizden. Güncel ve tam liste: <a href="fiyatlar.html">Paketler</a>.</p></div></section>' % t
            + sec('Fiyat karşılaştırırken', '<p>Fiyatı yalnız aylık tutara göre değil, içine neyin girdiğine göre karşılaştırın: ek modül ücreti, kullanıcı sayısı sınırı, SMS ve web sitesi dahil mi. Bizde kullanıcıya göre ek ücret yazmıyoruz; paketler içeriğiyle satır satır fiyatlar sayfasında.</p>', tint=True)
            + faq('Sık sorulan sorular', soru) + cta())
    page('servis-takip-programi-fiyatlari.html', 'Servis takip programı fiyatları | OnlineKaydet 990 ₺ + KDV\'den',
         'Servis takip programı fiyatları: OnlineKaydet Başlangıç 990 ₺, Profesyonel 1.990 ₺, Tam Paket 3.490 ₺, Kurumsal 5.990 ₺ (aylık + KDV). Pakette neler var, satır satır.',
         'Servis takip programı fiyatları', 'Servis takip programı fiyatları', 'Dört paket, içinde ne olduğu açık yazıyor. Yıllık ödemede iki ay bizden.', body, ld=faq_ld(soru))
def ucretsiz():
    soru = [('Ücretsiz servis takip programı var mı?', 'OnlineKaydet\'te 7 gün ücretsiz denersiniz; sonrasında paket fiyatı geçerlidir. Tamamen ücretsiz programlar genelde kayıt ya da modül sayısını sınırlar.'),
            ('Excel ile servis takibi yeterli mi?', 'Az kayıtta yeterli olabilir. Kayıt, usta ve tahsilat arttıkça müşteri geçmişini aramak, kimin ne kadar borçlu olduğunu bulmak ve ustaya iş atamak Excel\'de zorlaşır.'),
            ('Crack\'li ya da kaynağı belirsiz programlar güvenli mi?', 'Değil. Müşteri kayıtlarınız ve telefon numaraları KVKK kapsamındadır; kaynağı belirsiz bir yazılıma vermek hem veri hem hukuk riski taşır.')]
    body = (STIL + sec('Ücretsiz seçeneklerin sınırı', '<ul><li><b>Excel ve defter:</b> maliyeti yok, ama müşteri geçmişi ve alacak aramakla kaybolur.</li><li><b>Sınırlı ücretsiz sürüm:</b> kayıt, kullanıcı ya da modül sayısını kısıtlayabilir; kısıtı önceden okuyun.</li><li><b>Kaynağı belirsiz program:</b> müşteri verinizi riske atar, KVKK sorumluluğu size kalır.</li><li><b>Deneme süreli ürün:</b> kendi işinizle denemek en güvenlisi; OnlineKaydet\'te 7 gün ücretsiz.</li></ul>')
            + sec('OnlineKaydet\'te 7 gün ücretsiz', '<p style="max-width:720px;line-height:1.7">Kayıt açın, ustalarınızı ekleyin, birkaç gerçek servis kaydı girin. Beğenmezseniz devam etmenize gerek yok. Beğenirseniz Başlangıç paketi 990 ₺ + KDV\'den başlar. Paket içerikleri <a href="fiyatlar.html">fiyatlar sayfasında</a>.</p>', tint=True)
            + faq('Sık sorulan sorular', soru) + cta())
    page('ucretsiz-servis-takip-programi.html', 'Ücretsiz servis takip programı: seçenekler ve sınırları',
         'Ücretsiz servis takip programı arıyorsanız: Excel, sınırlı ücretsiz sürümler ve deneme süreli ürünlerin farkı. OnlineKaydet\'te 7 gün ücretsiz.',
         'Ücretsiz servis takip programı', 'Ücretsiz servis takip programı: neye dikkat etmeli?', 'Ücretsiz seçenekler neyi karşılıyor, nerede sınırlanıyor, ve 7 gün ücretsiz denemek ne demek.', body, ld=faq_ld(soru))
if __name__ == '__main__':
    out = [rakip(s, r) for s, r in RIV.items()] + [hub(), fiyat(), ucretsiz()]
    for n in ('servis-takip-programi-karsilastirma.html', 'servis-takip-programi-fiyatlari.html', 'ucretsiz-servis-takip-programi.html'): pass
    print(len(out) + 0, 'sayfa')
