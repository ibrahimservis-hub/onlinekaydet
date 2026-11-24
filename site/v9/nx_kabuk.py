# -*- coding: utf-8 -*-
"""İç sayfalara yeni kabuk: üst menü (nxh), mobil menü (nxm), koyu footer (nxf), nx-ic.css/js.
Eski header/duyuru/footer kaldırılır. Tekrar çalıştırılabilir (işaretler arası değiştirilir).
Kullanım: python3 site/v9/nx_kabuk.py"""
import os, re, glob
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = '1123i'
ATLA = {'ana-sayfa-yeni.html', 'index.html', 'a-onizleme.html', 'ana-sayfa-astryx.html', 'yeni-ana-sayfa.html', 'temalar-live.html', 'tasarim-kuafor5.html', 'yon4.html', 'yon5.html', 'yon6.html', 'yon7.html'}
IC = {'tel': '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
      'form': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>'}
ic = lambda k: '<i><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></i>' % IC[k]
HDR = ('<!--nxh--><header class="nxh" id="nxh"><div class="w"><div class="bar">'
 '<a class="logo" href="/" aria-label="OnlineKaydet ana sayfa"><img src="/logo-acik-s.png" alt="OnlineKaydet" width="154" height="30"></a>'
 '<nav aria-label="Ana menü"><details><summary>Ürün</summary><div class="dd"><a href="/web-sitesi.html">Web sitesi<small>Tema ve bölüm editörü</small></a><a href="/e-ticaret.html">E-ticaret<small>Ürün, sipariş, pazaryeri</small></a><a href="/is-takibi.html">Randevu ve iş takibi<small>Takvim, servis, görev</small></a><a href="/muhasebe-ve-stok.html">Muhasebe ve stok<small>Kasa, cari, gün sonu</small></a><a href="/ozellikler.html">Tüm özellikler<small>Paket paket karşılaştırma</small></a></div></details>'
 '<a href="/temalar.html">Temalar</a><a href="/sektorler.html">Sektörler</a><a href="/fiyatlar.html">Paketler</a>'
 '<details><summary>Kaynaklar</summary><div class="dd"><a href="/bilgi-bankasi.html">Bilgi bankası<small>Adım adım kullanım</small></a><a href="/blog.html">Blog</a><a href="/entegrasyonlar.html">Entegrasyonlar</a><a href="/hesaplama-araclari.html">Hesaplama araçları</a><a href="/destek.html">Destek</a></div></details>'
 '<a href="/iletisim.html">İletişim</a></nav>'
 '<div class="sag"><a class="gir" href="/uye-girisi">Üye girişi</a><a class="nxbt p" href="/demo.html">Ücretsiz deneyin</a><button class="hm" type="button" aria-label="Menüyü aç" aria-expanded="false" aria-controls="nxm"><span></span></button></div>'
 '</div></div></header>'
 '<div class="nxm" id="nxm"><b>Ürün</b><a href="/web-sitesi.html">Web sitesi</a><a href="/e-ticaret.html">E-ticaret</a><a href="/is-takibi.html">Randevu ve iş takibi</a><a href="/muhasebe-ve-stok.html">Muhasebe ve stok</a><b>Keşfet</b><a href="/temalar.html">Temalar</a><a href="/sektorler.html">Sektörler</a><a href="/fiyatlar.html">Paketler</a><a href="/bilgi-bankasi.html">Bilgi bankası</a><a href="/blog.html">Blog</a><a href="/destek.html">Destek</a><a href="/hakkimizda.html">Hakkımızda</a><a href="/iletisim.html">İletişim</a><a href="/uye-girisi">Üye girişi</a><a class="nxbt p" href="/demo.html">Ücretsiz deneyin</a></div><!--/nxh-->')
FTR = ('<!--nxf--><footer class="nxf"><div class="w">'
 '<div class="ust2"><div><p class="mk"><b>//</b> kayıttan kazanca</p><h2>Birlikte işinizi <em>büyütelim.</em></h2></div>'
 '<div class="ok2"><svg viewBox="0 0 120 60" aria-hidden="true"><path d="M4 40 C30 10 70 6 104 24" fill="none" stroke="#e8456e" stroke-width="3" stroke-linecap="round"/><path d="M92 14 L106 25 L90 32" fill="none" stroke="#e8456e" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'
 '<div class="ilt"><a href="tel:+905444444004">' + ic('tel') + '<span>Bizi arayın</span></a><a href="/iletisim.html">' + ic('form') + '<span>İletişim formu</span></a></div></div></div>'
 '<div class="kol">'
 '<div><h3><span>01 //</span>Ürün</h3><a href="/temalar.html">Temalar</a><a href="/e-ticaret.html">E-ticaret</a><a href="/web-sitesi.html">Web sitesi editörü</a><a href="/is-takibi.html">Randevu ve iş takibi</a><a href="/muhasebe-ve-stok.html">Muhasebe ve stok</a><a href="/fiyatlar.html">Paketler</a></div>'
 '<div><h3><span>02 //</span>Sektörler</h3><a href="/sektor-kombi.html">Teknik servis</a><a href="/sektor-kuafor.html">Kuaför</a><a href="/sektor-eticaret.html">E-ticaret</a><a href="/tum-sektorler.html">Tüm sektörler</a></div>'
 '<div><h3><span>03 //</span>Kaynaklar</h3><a href="/blog.html">Blog</a><a href="/entegrasyonlar.html">Entegrasyonlar</a><a href="/bilgi-bankasi.html">Bilgi bankası</a><a href="/destek.html">Destek</a><a href="/hesaplama-araclari.html">Hesaplama araçları</a></div>'
 '<div><h3><span>04 //</span>E-ticaret bilgi bankası</h3><a href="/e-ticaret-bilgi-bankasi.html">Tüm rehberler</a><a href="/e-ticaret-nasil-yapilir.html">E-ticaret nasıl yapılır?</a><a href="/e-ticaret-sitesi-kurmak.html">E-ticaret sitesi kurmak</a><a href="/internetten-satis-nasil-yapilir.html">İnternetten satış</a><a href="/trendyolda-satis-yapmak.html">Trendyol\'da satış</a><a href="/pinterest-nedir.html">Pinterest nedir?</a><a href="/online-is-fikirleri.html">Online iş fikirleri</a><a href="/youtube-para-kazanma.html">YouTube para kazanma</a></div>'
 '<div><h3><span>05 //</span>Kurumsal</h3><a href="/hakkimizda.html">Hakkımızda</a><a href="/iletisim.html">İletişim</a><a href="/bayilik.html">Bayilik</a><a href="/altyapi-ve-teknoloji.html">Altyapı ve teknoloji</a><a href="/bilgi-ve-veri-guvenligi.html">Veri güvenliği</a><a href="/kvkk.html">KVKK ve gizlilik</a></div>'
 '</div><div class="fil" aria-hidden="true">onlinekaydet</div>'
 '<div class="nxalt"><span>© 2026 OnlineKaydet</span><span><a href="/gizlilik.html">Gizlilik</a> · <a href="/cerez-politikasi.html">Çerez politikası</a> · <a href="/kullanim-kosullari.html">Kullanım koşulları</a> · <a href="/mesafeli-satis-iade.html">Mesafeli satış ve iade</a></span><span class="imza">KAYDET · TAKİP ET · BÜYÜ //</span></div>'
 '</div></footer><!--/nxf-->')
FONTS = '<link rel="preload" as="font" type="font/woff2" href="/v9/fonts/jost-latin.woff2" crossorigin><link rel="preload" as="font" type="font/woff2" href="/v9/fonts/spacegrotesk-latin.woff2" crossorigin>'

def isle(s):
    s = re.sub(r'<!--nxh-->.*?<!--/nxh-->', '', s, flags=re.S)
    s = re.sub(r'<!--nxf-->.*?<!--/nxf-->', '', s, flags=re.S)
    s = re.sub(r'<div class="duy">.*?</div></div>', '', s, count=1, flags=re.S)
    s = re.sub(r'<header class="ust">.*?</header>', '', s, count=1, flags=re.S)
    s = re.sub(r'<footer class="alt2">.*?</footer>', '', s, count=1, flags=re.S)
    s = re.sub(r'<link rel="stylesheet" href="/v9/nx-ic\.css[^"]*">', '', s)
    s = re.sub(r'<script src="/v9/nx-ic\.js[^"]*" defer></script>', '', s)
    s = s.replace(FONTS, '')
    if '<body class="' in s and 'nxi' not in re.search(r'<body class="([^"]*)"', s).group(1):
        s = re.sub(r'<body class="', '<body class="nxi ', s, count=1)
    elif '<body>' in s:
        s = s.replace('<body>', '<body class="nxi">', 1)
    s = s.replace('</head>', FONTS + '<link rel="stylesheet" href="/v9/nx-ic.css?v=%s"></head>' % V, 1)
    m = re.search(r'<a class="skip"[^>]*>[^<]*</a>', s)
    if m:
        s = s[:m.end()] + HDR + s[m.end():]
    else:
        s = re.sub(r'(<body[^>]*>)', r'\1' + HDR.replace('\\', '\\\\'), s, count=1)
    s = s.replace('</main>', '</main>' + FTR, 1) if '</main>' in s else s.replace('</body>', FTR + '</body>', 1)
    s = s.replace('</body>', '<script src="/v9/nx-ic.js?v=%s" defer></script></body>' % V, 1)
    return s

# ---- iç sayfa görsel bantları (sayfa başlığının hemen altı)
G = {'blog.html': ('img', 'ekip-3', 'Ekip ekran başında yeni siteyi inceliyor'),
     'destek.html': ('img', 'ekip-1', 'Ekip ekrandaki akış şemasını gösteriyor'),
     'iletisim.html': ('img', 'ekip-2', 'İki kişi ekran başında iş akışını konuşuyor'),
     'bilgi-bankasi.html': ('img', 'analiz-cam', 'Ekip cam ekranda grafiği inceliyor'),
     'entegrasyonlar.html': ('vid', 'entegrasyon', 'Pazaryeri ve ERP bağlantısı'),
     'acik-api-ve-entegrasyon.html': ('vid', 'yazilim', 'Açık API ve özel yazılım'),
     'e-ticaret.html': ('img', 'akis-cekirdek', 'Siparişler ve belgeler tek merkezde birleşiyor'),
     'web-sitesi.html': ('vid', 'seo-goz', 'Google’da görünür olun'),
     'is-takibi.html': ('vid', 'otomasyon', 'Akıllı otomasyon'),
     'muhasebe-ve-stok.html': ('img', 'panel-radar', 'Panel ekranında performans görünümü'),
     'fiyatlar.html': ('img', 'ofis-gece', 'Ekip akşam ofiste panel ekranları üzerinde çalışıyor'),
     'bayilik.html': ('img', 'ekip-2', 'İki kişi ekran başında iş akışını konuşuyor'),
     'sektorler.html': ('img', 'ofis-gece', 'Ekip akşam ofiste çalışıyor'),
     'tum-sektorler.html': ('img', 'ofis-gece', 'Ekip akşam ofiste çalışıyor'),
     'ozellikler.html': ('img', 'panel-radar', 'Panel ekranında performans görünümü'),
     'altyapi-ve-teknoloji.html': ('vid', 'yazilim', 'Altyapı ve yazılım'),
     'bilgi-ve-veri-guvenligi.html': ('img', 'analiz-cam', 'Ekip veriyi inceliyor'),
     'hesap-guvenligi.html': ('img', 'analiz-cam', 'Ekip veriyi inceliyor'),
     'yedekleme-ve-denetim.html': ('img', 'panel-radar', 'Panel ekranı'),
     'ozel-tasarim.html': ('img', 'akis-cekirdek', 'Özel tasarım ve akış'),
     'hesaplama-araclari.html': ('img', 'analiz-cam', 'Ekip grafiği inceliyor'),
     'sikayet-ve-oneri.html': ('img', 'ekip-1', 'Ekip ekranı inceliyor')}

def bant(b):
    t, n, a = G[b]
    if t == 'img':
        x = '<img src="/v9/img/nx/%s.webp" width="1600" height="900" alt="%s" loading="lazy">' % (n, a)
    else:
        x = '<video muted loop playsinline autoplay preload="metadata" poster="/v9/img/nx/poster-%s.jpg" aria-label="%s"><source src="/v9/img/vid/nx-%s.mp4" type="video/mp4"></video>' % (n, a, n)
    return '<!--nxg--><div class="nxg">' + x + '</div><!--/nxg-->'

def gorsel(b, s):
    s = re.sub(r'<!--nxg-->.*?<!--/nxg-->', '', s, flags=re.S)
    if b not in G:
        return s
    i = s.find('<section class="pb"')
    if i < 0:
        i = s.find('<main>')
        if i < 0:
            return s
        j = s.find('</section>', i)
    else:
        j = s.find('</section>', i)
    if j < 0:
        return s
    j += len('</section>')
    return s[:j] + bant(b) + s[j:]

# ---- hakkımızda: şirket bilgileri yalnız burada
HAK = """<main><section class="pb" id="icerik"><div class="w"><div><p class="kr"><a href="/">Ana sayfa</a> / Hakkımızda</p><h1>İşinizi tek panelde toplayan yazılım</h1><p class="lead">Web sitesi, mağaza ve iş takibini birlikte sunuyoruz. Kayıttan kazanca, işletmenizin bütün akışı aynı yerde.</p><div class="cta"><a class="btn fil" href="/demo.html">Ücretsiz deneyin</a><a class="btn bos" href="#teklif">Teklif alın</a></div></div></div></section>
<div class="nxg"><img src="/v9/img/nx/ofis-gece.webp" width="1600" height="900" alt="Ekip akşam ofiste panel ekranları üzerinde çalışıyor"></div>
<section class="nxa"><div class="w2">
 <div class="nxa2"><div><p class="nxet">01 // Ne yapıyoruz</p><h2>Sitesi, mağazası ve defteri aynı yerde duran işletmeler.</h2><p>OnlineKaydet; web sitesi, e-ticaret, randevu ve iş takibini tek panelde toplar. Her firma sektörüne uygun hazır bir temayla başlar, metin ve görselleri panelden kendisi düzenler.</p>
  <p class="nxet" style="margin-top:34px">02 // Kimler için</p><p>Kendi ekibiyle çalışan küçük ve orta ölçekli işletmeler için: teknik servisler, kuaför ve güzellik salonları, oto servisler, mağazalar ve bayiler.</p></div>
  <img src="/v9/img/nx/ekip-2.webp" width="900" height="1125" alt="İki kişi ekran başında iş akışını konuşuyor" loading="lazy"></div>
</div></section>
<section class="nxk"><div class="w2 nxk2">
 <div><p class="nxet">03 // Nasıl çalışıyoruz</p><h2>İhtiyacı dinler, çözümü kurar, yolu birlikte çizeriz.</h2>
  <ol><li><span>01 //</span><b>İhtiyaç</b><p>Sektörünüzü, iş akışınızı ve kanallarınızı konuşuruz.</p></li><li><span>02 //</span><b>Çözüm</b><p>Tema, modül ve bağlantıları işinize göre açarız.</p></li><li><span>03 //</span><b>Yol haritası</b><p>Kurulum, veri aktarımı ve eğitim adım adım ilerler.</p></li></ol></div>
 <img src="/v9/img/nx/katman-yol.webp" width="1200" height="700" alt="İhtiyaç, çözüm ve yol haritası katmanları" loading="lazy">
</div></section>
<section class="nxa"><div class="w2">
 <div class="nxv"><div><video muted loop playsinline autoplay preload="metadata" poster="/v9/img/nx/poster-entegrasyon.jpg" aria-label="Pazaryeri ve ERP bağlantısı"><source src="/v9/img/vid/nx-entegrasyon.mp4" type="video/mp4"></video><b>Bağlantılar</b><span>Pazaryeri, fatura ve sipariş sistemleri tek panelde.</span></div>
  <div><video muted loop playsinline autoplay preload="metadata" poster="/v9/img/nx/poster-otomasyon.jpg" aria-label="Akıllı otomasyon"><source src="/v9/img/vid/nx-otomasyon.mp4" type="video/mp4"></video><b>Otomasyon</b><span>Hatırlatma, belge ve mesaj kendiliğinden yürür.</span></div></div>
</div></section>
<section class="nxa nxs"><div class="w2 nxsir">
 <div><p class="nxet">04 // Şirket</p><h2>Şirket bilgileri</h2></div>
 <dl><div><dt>Ünvan</dt><dd>Moda Ekru E-Ticaret Hizmetleri Tekstil Sanayi ve Ticaret Ltd. Şti.</dd></div><div><dt>Adres</dt><dd>Etimesgut, Ankara</dd></div><div><dt>Telefon</dt><dd><a href="tel:+905444444004">0544 444 40 04</a></dd></div><div><dt>Altyapı</dt><dd>Verileriniz Türkiye’deki sunucularda; her firmanın veritabanı ayrı.</dd></div></dl>
</div></section>
%SON%
</main>"""

def hakkimizda(s):
    i = s.index('<main>'); j = s.index('</main>') + len('</main>')
    m = s[i:j]
    k = m.find('<section class="son" id="teklif">')
    son = m[k:m.index('</section>', k) + 10] if k >= 0 else ''
    return s[:i] + HAK.replace('%SON%', son) + s[j:]

n = 0
for f in sorted(glob.glob(S + '/*.html')):
    b = os.path.basename(f)
    if b in ATLA:
        continue
    s = open(f, encoding='utf-8').read()
    if '<header class="ust">' not in s and 'class="nxh"' not in s:
        continue
    if b == 'hakkimizda.html' and 'class="nxsir"' not in s:
        s = hakkimizda(s)
    open(f, 'w', encoding='utf-8').write(gorsel(b, isle(s)))
    n += 1
print('kabuk uygulandı:', n, 'sayfa')
