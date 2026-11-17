# -*- coding: utf-8 -*-
"""Muhasebe, stok ve satış özellik sayfaları + hesaplama araçları + şikayet/öneri formu.
İçerik panelde gerçekten bulunan özelliklere dayanır; bulunmayanlar 'Henüz yok' bölümünde açıkça yazılır."""
import html, json


def uret(page, B, SON, CTA):
    e = html.escape

    def kart(l):
        return ''.join('<div class="fk"><span class="no">%02d</span><h3>%s</h3><p>%s</p></div>' % (i + 1, e(a), e(b)) for i, (a, b) in enumerate(l))

    def ul(l):
        return '<ul class="sxl">%s</ul>' % ''.join('<li>%s</li>' % e(x) for x in l)

    def ssd(q):
        return ''.join('<details class="sssd"><summary>%s</summary><p>%s</p></details>' % (e(a), e(b)) for a, b in q)

    def ldq(q):
        return '<script type="application/ld+json">' + json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': a, 'acceptedAnswer': {'@type': 'Answer', 'text': b}} for a, b in q]}, ensure_ascii=False) + '</script>'

    ILG = [('Muhasebe ve stok özellikleri', '/muhasebe-ve-stok.html'), ('Çek ve senet takibi', '/cek-senet-takip-programi.html'),
           ('Barkodlu hızlı satış', '/barkodlu-hizli-satis-programi.html'), ('Depo, lot ve son kullanma takibi', '/stok-sayim-lot-skt-takibi.html'),
           ('Mali müşavir paneli', '/mali-musavir-paneli.html'), ('E-ihracat ve proforma', '/e-ihracat-proforma.html'),
           ('Açık API', '/acik-api-ve-entegrasyon.html'), ('Hesaplama araçları', '/hesaplama-araclari.html')]
    uretilen = []

    def ozellik(slug, title, desc, kick, h1, lead, kartlar, maddeler, sss, ek=''):
        diger = '<p class="sxy" style="margin-top:18px">İlgili sayfalar: ' + ' · '.join('<a href="%s">%s</a>' % (u, a) for a, u in ILG if u != '/' + slug) + '</p>'
        page(slug, title, desc,
             B(slug[:3], '<a href="/muhasebe-ve-stok.html">Muhasebe ve stok</a> / ' + kick, h1, lead)
             + '<section class="sec"><div class="w"><div class="fg">' + kart(kartlar) + '</div>' + ul(maddeler) + ek + diger + '</div></section>'
             + '<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>' + ssd(sss) + '</div></div></section>' + CTA + SON,
             ld_raw=ldq(sss))
        uretilen.append(slug)

    # ---------------------------------------------------------------- çek-senet
    ozellik('cek-senet-takip-programi.html', 'Çek ve Senet Takip Programı | OnlineKaydet',
            'Alacak ve borç çek-senetlerini vade tarihine göre izleyin; tahsil edince kasaya otomatik işleyin. Vadesi geçenler ve yaklaşanlar tek ekranda.',
            'Çek ve senet', 'Çek ve senet takibi', 'Elinizdeki çekleri ve verdiğiniz senetleri vade sırasıyla görün, tahsil edildiğinde kasaya tek tıkla işleyin.',
            [('Alacak ve borç ayrımı', 'Müşteriden aldığınız ve sizin verdiğiniz çek-senetler ayrı izlenir. Portföydeki alacak ve ödenecek borç toplamı üstte görünür.'),
             ('Vade uyarısı', 'Vadesi 7 gün içinde olanlar ve vadesi geçenler sayı ve tutar olarak öne çıkar; geciken satır kırmızı görünür.'),
             ('Tek tıkla tahsilat', 'Tahsil ya da ödendi dediğinizde seçtiğiniz kasa veya banka hesabına gelir/gider hareketi kendiliğinden yazılır.'),
             ('Karşılıksız ve iade', 'Karşılıksız çıkan çek ayrı durumla işaretlenir, tahsilat sayılmaz.'),
             ('Kayıt koruması', 'Kasaya işlenmiş kayıt değiştirilemez ve silinemez; bu yüzden kasa ile portföy tutarsız kalmaz.'),
             ('Banka ekstresi', 'İnternet bankacılığından indirdiğiniz CSV ekstre içe aktarılır; aynı hareket ikinci kez eklenmez.')],
            ['Tutar ve vade tarihi zorunludur; eksik kayıt alınmaz', 'Çek/senet numarası, banka ve not alanı vardır', 'Hareketler Kasa raporlarında görünür'],
            [('Çekin tahsilini kasaya otomatik yazıyor mu?', 'Evet. Tahsil edildi dediğinizde seçtiğiniz hesaba gelir olarak işlenir. Borç çeki için ödendi dediğinizde gider olarak işlenir.'),
             ('Bankadan çek bilgisi çekiyor mu?', 'Hayır. Çek ve senetleri elle girersiniz; banka bağlantısı yoktur. Banka hareketleri için ekstre dosyası yüklenir.'),
             ('Karşılıksız çeki geri alabilir miyim?', 'Karşılıksız ve iade durumları bilgi amaçlıdır; kasaya hareket yazmaz. Tahsil edilmiş kayıt ise değiştirilemez.')])

    # ---------------------------------------------------------------- hızlı satış
    ozellik('barkodlu-hizli-satis-programi.html', 'Barkodlu Hızlı Satış Programı | OnlineKaydet',
            'Barkodu okutun, sepeti kapatın: stok düşer, tahsilat kasaya yazılır. Mağaza, market ve tezgâh satışı için hızlı satış ekranı.',
            'Hızlı satış', 'Barkodlu hızlı satış', 'Tezgâh ve mağaza satışı için tek alanlı ekran: barkodu okutun, Enter’a basın, satışı tamamlayın.',
            [('Barkod okutma', 'El tipi barkod okuyucu klavye gibi çalışır; barkodu okutup Enter’a basmanız yeterli. Barkod, stok kodu ya da ürün adıyla bulunur.'),
             ('Stok kontrolü', 'Sepete eklerken stok yoksa uyarılır; satış tamamlanırken stok koşullu düşer. Yetersiz stokta satış yapılmaz, düşen kalemler geri alınır.'),
             ('İndirim ve ödeme türü', 'Nakit, kart ve havale seçilir; sepete tutar olarak indirim girilebilir.'),
             ('Kasaya otomatik yazılır', 'Satış, seçtiğiniz hesaba gelir olarak işlenir; her satışa fiş numarası verilir.'),
             ('Günlük toplam', 'Bugünkü satış toplamı ve son satışlar ekranın üstünde görünür.'),
             ('Pazaryeri ile aynı stok', 'Hızlı satışla düşen stok, bağlı pazaryeri ve mağazaya da yansır.')],
            ['Aynı ürün tekrar okutulunca adet artar', 'Adet sepet içinden değiştirilebilir', 'Fiyat, ürün kartındaki güncel (indirimli ise indirimli) fiyattır'],
            [('Fiş yazıcı ya da yazarkasa var mı?', 'Hayır. Satış panelde fiş numarasıyla kayıt altına alınır; yazarkasa ya da mali cihaz bağlantısı yoktur. Resmî belge gerekiyorsa mevcut yazarkasanız veya e-fatura entegratörünüz kullanılır.'),
             ('İnternet olmadan çalışır mı?', 'Hayır, şu an çevrimdışı satış yok. İnternet gerekir.'),
             ('Hangi barkod okuyucu uyar?', 'USB ya da Bluetooth ile klavye gibi çalışan her okuyucu. Ayrıca sürücü kurmanız gerekmez.')])

    # ---------------------------------------------------------------- depo / lot / skt
    ozellik('stok-sayim-lot-skt-takibi.html', 'Stok Sayım, Lot ve Son Kullanma Tarihi Takibi | OnlineKaydet',
            'Çoklu depo, lot numarası, son kullanma tarihi uyarısı, stok sayımı ve toplu fiyat güncelleme. Geri alınabilir fiyat değişikliği.',
            'Depo ve sayım', 'Depo, lot ve son kullanma takibi', 'Gıda, kozmetik, ilaç dışı sağlık ürünleri ve her türlü stoklu satış için lot, SKT ve sayım araçları.',
            [('Çoklu depo', 'Ana depo, şube, araç gibi istediğiniz kadar depo tanımlayın. Lotları depolar arasında taşıyın.'),
             ('Lot ve SKT', 'Mal kabulde lot numarası ve son kullanma tarihi girin. Ürün stoğu otomatik artar.'),
             ('SKT uyarısı', '60 gün içinde dolacak ve geçmiş lotlar kalan gün sayısıyla listelenir. Fire ya da imha için tek tıkla düşülür.'),
             ('Stok sayımı', 'Barkod ve sayılan adedi yazın ya da CSV yükleyin. Önce fark raporu çıkar; onaylayınca stok düzelir ve kayıt altına alınır.'),
             ('Toplu fiyat güncelleme', 'Kategori ya da markaya göre yüzde, sabit tutar veya yeni fiyat uygulayın. Önce önizleme görürsünüz.'),
             ('Geri alma', 'Toplu fiyat değişikliği tek tıkla eski fiyatlara döndürülür.')],
            ['Fiyat yuvarlama: tam TL, 5’e, ,90 ve ,99 seçenekleri', 'Stok hareketleri kayıt altındadır (kaynak: lot girişi, sayım, fire)', 'Depo içinde stok varken depo silinemez'],
            [('Satışta SKT’ye göre otomatik lot seçiliyor mu?', 'Hayır. Lotlar ve SKT takip edilir, uyarı verilir; satışta FEFO/FIFO ile otomatik lot seçimi yoktur.'),
             ('Sayımda stok doğrudan değişir mi?', 'Önce farkları görürsünüz. Yalnız “Sayımı uygula” dediğinizde stok sayılan adede eşitlenir ve hareket kaydı yazılır.'),
             ('Toplu fiyat yanlış giderse?', 'İşlemden hemen sonra çıkan Geri al düğmesiyle tüm ürünler önceki fiyatına döner.')])

    # ---------------------------------------------------------------- mali müşavir
    ozellik('mali-musavir-paneli.html', 'Mali Müşavir Paneli ve Muhasebe Aktarımı | OnlineKaydet',
            'Mali müşavirinize şifresiz, süreli ve salt okunur bağlantı verin; ay özetini görsün, hareketleri Excel’e uygun CSV olarak indirsin.',
            'Mali müşavir', 'Mali müşavir erişimi', 'Müşavirinize hesap açmadan, yalnız okunur ve süreli bir bağlantı verin.',
            [('Süreli bağlantı', '1 ile 365 gün arasında geçerlilik seçersiniz. Süre dolunca bağlantı kapanır.'),
             ('Salt okunur', 'Müşavir yalnız gelir-gider özetini görür ve dosya indirir; hiçbir kaydı değiştiremez.'),
             ('Ay özeti', 'Aylık gelir, gider, net sonuç ve kategori dökümü tek sayfada.'),
             ('Excel’e uygun CSV', 'Tarih, tür, kategori, açıklama ve tutar sütunlarıyla, noktalı virgül ayraçlı dosya. Excel’de doğrudan açılır.'),
             ('Anında iptal', 'Bağlantıyı panelden iptal ettiğiniz an kapanır; son giriş zamanı görünür.'),
             ('Arama motoruna kapalı', 'Sayfa dizine alınmaz; bağlantı yalnız size ve gönderdiğiniz kişiye aittir.')],
            ['Bağlantı yalnız oluşturulurken görünür; kaybederseniz yenisini üretirsiniz', 'Bağlantı kimlik doğrulama gerektirmez; paylaşırken dikkatli olun'],
            [('Muhasebe programına doğrudan aktarıyor mu?', 'Hayır. CSV dosyası verilir; müşaviriniz kendi programına bu dosyadan aktarır. Logo, Mikro ya da Paraşüt’e doğrudan bağlantı bu özelliğin parçası değildir.'),
             ('Fatura keser mi?', 'Resmî e-fatura/e-arşiv kesimi için özel entegratör hesabı gerekir. Panel, Paraşüt, Uyumsoft gibi sağlayıcılara bağlantı kartları sunar.'),
             ('Müşavir ne görür?', 'Seçilen aydaki gelir ve gider hareketleri. Servis tahakkuku gibi gerçek para girişi olmayan kayıtlar dahil edilmez.')])

    # ---------------------------------------------------------------- e-ihracat
    ozellik('e-ihracat-proforma.html', 'E-İhracat ve Proforma Fatura | OnlineKaydet',
            'Yurt dışı satış için proforma fatura, GTİP ve menşei bilgisi, teslim şekli ve TCMB kuruyla döviz karşılığı.',
            'E-ihracat', 'E-ihracat ve proforma fatura', 'Yurt dışı alıcıya döviz cinsinden proforma gönderin; GTİP, menşei ve teslim şekli belgede görünsün.',
            [('Döviz cinsinden fiyat', 'TL fiyatlar güncel TCMB satış kuruyla USD, EUR ya da GBP’ye çevrilir. İsterseniz kuru elle yazarsınız.'),
             ('GTİP ve menşei', 'Ürün başına gümrük tarife kodu, menşei ülke ve ağırlık kaydedilir; proformada yazar.'),
             ('Teslim şekli', 'EXW, FCA, FOB, CIF, DAP veya DDP seçilir.'),
             ('Firma ve banka bilgisi', 'Unvan, vergi no, IBAN ve SWIFT belgeye otomatik girer.'),
             ('Ülke listesi ve asgari sipariş', 'Satış yaptığınız ülkeleri ve asgari sipariş tutarını tanımlarsınız.'),
             ('Yazdırılabilir belge', 'Proforma tek sayfa olarak açılır; yazdırın ya da PDF kaydedin.')],
            ['Proforma, resmî ihracat faturası yerine geçmez', 'Gümrük beyannamesi ve e-ihracat resmî belgeleri bu özelliğe dahil değildir'],
            [('Gümrük işlemlerini yapıyor mu?', 'Hayır. Yalnız proforma ve ürün bazlı GTİP/menşei kaydı vardır. Beyanname ve resmî belgeler gümrük müşavirinizle yapılır.'),
             ('Yabancı dilde site olur mu?', 'Evet, panelde çoklu dil desteği vardır. Hangi dillerin açık olduğunu Diller sayfasından yönetirsiniz.'),
             ('Kur nereden geliyor?', 'T.C. Merkez Bankası günlük kur dosyasından alınır; ulaşılamazsa son kaydedilen değer gösterilir.')])

    # ---------------------------------------------------------------- açık API
    ozellik('acik-api-ve-entegrasyon.html', 'Açık API ve Entegrasyon | OnlineKaydet',
            'Kendi yazılımınızı panele bağlayın: API anahtarıyla ürün, fiyat ve stok okuyun, güncelleyin. Okuma ve yazma yetkili ayrı anahtarlar.',
            'Açık API', 'Açık API', 'ERP, muhasebe ya da kendi yazdığınız araçla ürün, fiyat ve stok verisini alın ve güncelleyin.',
            [('Anahtar bazlı erişim', 'Her yazılım için ayrı anahtar üretirsiniz. Anahtar yalnız oluşturulurken görünür.'),
             ('Okuma ve yazma yetkisi', 'Varsayılan anahtar yalnız okur. Yazma yetkisi bilerek açılır ve yalnız fiyat ile stok günceller.'),
             ('Ürün listesi', 'Sayfalı liste, arama, barkod ya da stok koduyla tek ürün.'),
             ('Hız sınırı', 'Anahtar başına dakikada 120 istek; aşılırsa istek reddedilir.'),
             ('Anında iptal', 'İptal edilen anahtar bir sonraki istekte reddedilir.'),
             ('Stok senkronu', 'API ile yapılan değişiklik mağaza ve bağlı pazaryerlerine de yansır.')],
            ['Anahtarlar sunucuda düz metin olarak saklanmaz', 'İstek başlığı: X-API-Key', 'Sipariş ve müşteri verisi API’de yoktur; yalnız ürün, fiyat, stok'],
            [('Sipariş verisini API ile alabilir miyim?', 'Şu an hayır. API yalnız ürün, fiyat ve stok içindir.'),
             ('Webhook var mı?', 'Hayır, şu an yok.'),
             ('Dokümantasyon nerede?', 'Panelde API anahtarları sayfasında adresler ve örnek istekler görünür.')],
            ek='<div class="yz" style="margin-top:20px"><h2 style="margin-top:0">Örnek istek</h2><pre style="white-space:pre-wrap;font-size:13px;background:#f6f8fb;padding:14px;border-radius:8px">GET /urunler?q=süt&amp;adet=50\nPUT /urunler/869111   {"fiyat": 31.5, "stok": 12}\nX-API-Key: ok_…</pre><p class="sxy">Tam adres, panelde API anahtarları sayfasında firmanıza özel olarak gösterilir.</p></div>')

    # ---------------------------------------------------------------- merkez sayfa
    HIC = ['e-İrsaliye, e-SMM ve e-Müstahsil makbuzu: şu an yok', 'E-imza (nitelikli elektronik imza): yok; teklif onayı bağlantıyla alınır', 'Çevrimdışı (internetsiz) satış: yok',
           'Yazarkasa ve POS cihazı bağlantısı: yok', 'Lot/SKT’ye göre otomatik lot seçimi (FEFO): yok', 'Banka hesabına doğrudan bağlantı (otomatik ekstre): yok, ekstre CSV ile yüklenir']
    Q0 = [('e-Fatura ve e-Arşiv kesiyor musunuz?', 'Panel kendisi fatura kesmez. Paraşüt, Uyumsoft, Foriba gibi özel entegratör hesabınız varsa bağlantı kartından bağlarsınız; resmî fatura entegratörde kesilir.'),
          ('Bu özellikler her pakette var mı?', 'Hangi modülün hangi pakette olduğu Fiyatlar sayfasında. Emin olmak için bize yazın.'),
          ('Listede olmayan bir özellik gerekiyor.', 'Yukarıdaki “Henüz yok” listesini açıkça yazdık. Gerçekten gerekiyorsa bize iletin; öncelik belirlerken talepleri dikkate alıyoruz.')]
    page('muhasebe-ve-stok.html', 'Muhasebe, Stok ve Satış Özellikleri | OnlineKaydet',
         'Çek-senet takibi, banka ekstresi, mali müşavir erişimi, barkodlu hızlı satış, depo ve lot takibi, stok sayımı, e-ihracat proforma ve açık API.',
         B('ms', 'Özellikler', 'Muhasebe, stok ve satış', 'Kasa, stok ve satış işlerini aynı panelde yönetin. Aşağıdakilerin hepsi panelde çalışır; olmayanları da açıkça yazdık.')
         + '<section class="sec"><div class="w"><div class="fg">' + ''.join('<div class="fk"><span class="no">%02d</span><h3><a href="%s">%s</a></h3><p>%s</p></div>' % (i + 1, u, e(a), e(b)) for i, (a, u, b) in enumerate([
             ('Çek ve senet takibi', '/cek-senet-takip-programi.html', 'Alacak ve borç vadelerini izleyin; tahsil edince kasaya işleyin.'),
             ('Banka ekstresi ve döviz kuru', '/cek-senet-takip-programi.html', 'CSV ekstre içe aktarma ve günlük TCMB kuru.'),
             ('Barkodlu hızlı satış', '/barkodlu-hizli-satis-programi.html', 'Okut, sepeti kapat; stok düşer, kasa güncellenir.'),
             ('Depo, lot ve SKT', '/stok-sayim-lot-skt-takibi.html', 'Çoklu depo, son kullanma uyarısı, sayım ve toplu fiyat.'),
             ('Mali müşavir paneli', '/mali-musavir-paneli.html', 'Süreli, salt okunur bağlantı ve CSV.'),
             ('E-ihracat proforma', '/e-ihracat-proforma.html', 'Döviz cinsinden proforma, GTİP ve menşei.'),
             ('Açık API', '/acik-api-ve-entegrasyon.html', 'Ürün, fiyat ve stoğu kendi yazılımınızdan yönetin.'),
             ('Şikayet ve öneri formu', '/sikayet-ve-oneri.html', 'Müşteri geri bildirimleri panelde toplanır.')])) + '</div>'
         + '<div class="yz" style="margin-top:22px"><h2 style="margin-top:0">Henüz bulunmayanlar</h2><p>Eksiğimizi saklamıyoruz:</p>' + ul(HIC) + '</div>'
         + '<p class="sxy" style="margin-top:18px">Ücretsiz <a href="/hesaplama-araclari.html">hesaplama araçları</a>: KDV, kâr marjı, vade farkı, taksit, pazaryeri net kazanç, desi ve daha fazlası.</p></div></section>'
         + '<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>' + ssd(Q0) + '</div></div></section>' + CTA + SON, ld_raw=ldq(Q0))
    uretilen.append('muhasebe-ve-stok.html')

    # ---------------------------------------------------------------- hesaplama araçları
    CALC = r'''
<style>.hsp{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}.hsk{background:#fff;border:1px solid #e3e8ef;border-radius:14px;padding:20px}.hsk h3{margin:0 0 4px;font-size:18px}.hsk p.a{margin:0 0 12px;color:#5b6675;font-size:13.5px}.hsk label{display:block;font-size:13px;font-weight:600;margin:10px 0 4px}.hsk input,.hsk select{width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #cfd6df;border-radius:8px;font:inherit;min-height:44px;background:#fff}.hsk .s{margin-top:14px;padding:12px;border-radius:10px;background:#f2f6ff;font-weight:600;min-height:24px;line-height:1.6}</style>
<div class="hsp" id="hesaplar"></div>
<script>
(function(){
function n(v){v=String(v==null?'':v).trim().replace(/\s/g,'');if(v.indexOf(',')>-1)v=v.replace(/\./g,'').replace(',','.');var x=parseFloat(v);return isFinite(x)?x:NaN}
function t(x,d){return isFinite(x)?x.toLocaleString('tr-TR',{minimumFractionDigits:d==null?2:d,maximumFractionDigits:d==null?2:d}):'—'}
var T=[
{ad:'KDV hesaplama',a:'KDV hariç ya da dahil tutardan diğerini bulun.',f:[['tutar','Tutar (₺)'],['oran','KDV oranı (%)','20'],['mod','Hesap','sel','hariç → KDV dahil|dahil → KDV hariç']],
 h:function(v){var k=v.oran/100;if(v.mod==='0'){var kd=v.tutar*k;return 'KDV: '+t(kd)+' ₺ · Toplam: '+t(v.tutar+kd)+' ₺'}var h=v.tutar/(1+k);return 'KDV hariç: '+t(h)+' ₺ · KDV: '+t(v.tutar-h)+' ₺'}},
{ad:'Kâr marjı',a:'Maliyet ve satış fiyatından marj ve kâr oranını bulun.',f:[['maliyet','Maliyet (₺)'],['satis','Satış fiyatı (₺)']],
 h:function(v){var k=v.satis-v.maliyet;return 'Kâr: '+t(k)+' ₺ · Marj: %'+t(k/v.satis*100)+' · Maliyet üzerine kâr: %'+t(k/v.maliyet*100)}},
{ad:'Hedef marjla satış fiyatı',a:'İstediğiniz kâr marjı için satış fiyatını bulun.',f:[['maliyet','Maliyet (₺)'],['marj','Hedef marj (%)','30']],
 h:function(v){if(v.marj>=100)return 'Marj 100’den küçük olmalı';var s=v.maliyet/(1-v.marj/100);return 'Satış fiyatı: '+t(s)+' ₺ · Kâr: '+t(s-v.maliyet)+' ₺'}},
{ad:'İndirim hesaplama',a:'İndirimli fiyatı ve tasarrufu görün.',f:[['fiyat','Liste fiyatı (₺)'],['ind','İndirim (%)','10']],
 h:function(v){var y=v.fiyat*(1-v.ind/100);return 'İndirimli fiyat: '+t(y)+' ₺ · Tasarruf: '+t(v.fiyat-y)+' ₺'}},
{ad:'Yüzde değişim',a:'Eski ve yeni değerden artış ya da azalış oranı.',f:[['eski','Eski değer'],['yeni','Yeni değer']],
 h:function(v){var d=(v.yeni-v.eski)/v.eski*100;return (d>=0?'Artış: %':'Azalış: %')+t(Math.abs(d))+' · Fark: '+t(v.yeni-v.eski)}},
{ad:'Vade farkı',a:'Gecikme ya da vadeli satış için basit vade farkı.',f:[['tutar','Tutar (₺)'],['faiz','Aylık faiz (%)','3'],['gun','Gün sayısı','30']],
 h:function(v){var f=v.tutar*v.faiz/100/30*v.gun;return 'Vade farkı: '+t(f)+' ₺ · Toplam: '+t(v.tutar+f)+' ₺'}},
{ad:'Kredi / taksit',a:'Eşit taksitli (anüite) ödeme planı.',f:[['tutar','Tutar (₺)'],['faiz','Aylık faiz (%)','3'],['ay','Vade (ay)','12']],
 h:function(v){var r=v.faiz/100,m=v.ay,p=r===0?v.tutar/m:v.tutar*r/(1-Math.pow(1+r,-m));return 'Aylık taksit: '+t(p)+' ₺ · Toplam geri ödeme: '+t(p*m)+' ₺ · Faiz: '+t(p*m-v.tutar)+' ₺'}},
{ad:'Pazaryeri net kazanç',a:'Komisyon ve kargo düştükten sonra kalan kâr.',f:[['satis','Satış fiyatı (₺)'],['kom','Komisyon (%)','15'],['kargo','Kargo (₺)','0'],['maliyet','Ürün maliyeti (₺)']],
 h:function(v){var k=v.satis*v.kom/100,net=v.satis-k-v.kargo-v.maliyet;return 'Komisyon: '+t(k)+' ₺ · Net kâr: '+t(net)+' ₺ · Kâr oranı: %'+t(net/v.satis*100)}},
{ad:'Desi hesaplama',a:'Kargo ücreti desiye ya da kiloya göre, hangisi büyükse ondan hesaplanır.',f:[['en','En (cm)'],['boy','Boy (cm)'],['yuk','Yükseklik (cm)'],['kg','Gerçek ağırlık (kg)','1']],
 h:function(v){var d=v.en*v.boy*v.yuk/3000;return 'Desi: '+t(d)+' · Ücrete esas: '+t(Math.max(d,v.kg))+(d>=v.kg?' (desi)':' (kg)')}},
{ad:'Başa baş noktası',a:'Zarar etmemek için kaç adet satmalısınız?',f:[['sabit','Sabit gider (₺)'],['fiyat','Birim satış fiyatı (₺)'],['maliyet','Birim maliyet (₺)']],
 h:function(v){var b=v.fiyat-v.maliyet;if(b<=0)return 'Satış fiyatı maliyetten büyük olmalı';var a=Math.ceil(v.sabit/b);return 'Başa baş: '+t(a,0)+' adet · Ciro: '+t(a*v.fiyat)+' ₺'}},
{ad:'Birim fiyat karşılaştırma',a:'İki paketten hangisi daha ucuz? (kg ya da litre başına)',f:[['f1','1. ürün fiyatı (₺)'],['m1','1. ürün miktarı'],['f2','2. ürün fiyatı (₺)'],['m2','2. ürün miktarı']],
 h:function(v){var a=v.f1/v.m1,b=v.f2/v.m2;return '1. ürün: '+t(a)+' ₺/birim · 2. ürün: '+t(b)+' ₺/birim · '+(a===b?'Aynı':(a<b?'1. ürün':'2. ürün')+' daha ucuz')}}
];
var K=document.getElementById('hesaplar');
T.forEach(function(c,i){var d=document.createElement('div');d.className='hsk';var h='<h3>'+c.ad+'</h3><p class="a">'+c.a+'</p>';
 c.f.forEach(function(f){var id='h'+i+f[0];h+='<label for="'+id+'">'+f[1]+'</label>'+(f[2]==='sel'?'<select id="'+id+'">'+f[3].split('|').map(function(o,j){return '<option value="'+j+'">'+o+'</option>'}).join('')+'</select>':'<input id="'+id+'" inputmode="decimal" autocomplete="off" value="'+(f[2]||'')+'">')});
 h+='<div class="s" role="status" aria-live="polite"></div>';d.innerHTML=h;K.appendChild(d);
 var s=d.querySelector('.s');function run(){var v={},ok=true;c.f.forEach(function(f){var e=document.getElementById('h'+i+f[0]);var x=f[2]==='sel'?e.value:n(e.value);if(f[2]!=='sel'&&!isFinite(x)){ok=false}v[f[0]]=x});
  if(!ok){s.textContent='Değerleri girin';return}try{s.textContent=c.h(v)}catch(e){s.textContent='Hesaplanamadı'}}
 d.addEventListener('input',run);d.addEventListener('change',run);run()});
})();
</script>'''
    page('hesaplama-araclari.html', 'Ücretsiz Hesaplama Araçları: KDV, Kâr Marjı, Vade Farkı, Desi | OnlineKaydet',
         'KDV, kâr marjı, indirim, vade farkı, taksit, pazaryeri net kazanç, desi ve başa baş noktası hesaplama araçları. Ücretsiz, kayıt gerektirmez.',
         B('ha', 'Araçlar', 'Hesaplama araçları', 'Ticarette en çok gereken hesaplar. Kayıt yok, veriniz sunucuya gitmez.')
         + '<section class="sec"><div class="w">' + CALC + '<p class="sxy" style="margin-top:18px">Sonuçlar bilgilendirme amaçlıdır; vergi ve mali işlemlerde mali müşavirinize danışın. KDV oranları ve faiz değerlerini kendiniz girersiniz. <a href="/muhasebe-ve-stok.html">Muhasebe ve stok özellikleri</a></p></div></section>' + CTA + SON)
    uretilen.append('hesaplama-araclari.html')

    # ---------------------------------------------------------------- şikayet / öneri
    FORM = ('<section class="sec"><div class="w"><div class="fg"><div class="fk"><span class="no">Neden?</span><h3>Sesiniz bize ulaşsın</h3><p>Yaşadığınız sorunu, önerinizi ya da teşekkürünüzü yazın. Mesajınız kayda geçer; telefon numaranızı yalnız size dönmek için kullanırız.</p></div>'
            '<div class="frm" id="geri-form" style="background:#fff;border:1px solid #e3e8ef;border-radius:12px;padding:22px"><b style="font-size:22px">Şikayet ve öneri formu</b>'
            '<div class="alan"><label for="gb1">Ad soyad</label><input id="gb1" autocomplete="name"></div>'
            '<div class="alan"><label for="gb2">Telefon</label><input id="gb2" type="tel" autocomplete="tel"></div>'
            '<div class="alan"><label for="gb3">Türü</label><select id="gb3"><option>Şikayet</option><option>Öneri</option><option>Teşekkür</option></select></div>'
            '<div class="alan"><label for="gb4">Mesajınız</label><textarea id="gb4" rows="5" maxlength="900" style="width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #cfd6df;border-radius:8px;font:inherit"></textarea></div>'
            '<button class="bt" type="button">Gönder</button><small style="display:block;font-size:12px;color:#5b6675;margin-top:10px">Bilgileriniz yalnız dönüş için kullanılır. <a href="/kvkk.html" style="text-decoration:underline">KVKK</a></small></div></div></div></section>')
    page('sikayet-ve-oneri.html', 'Şikayet ve Öneri Formu | OnlineKaydet', 'OnlineKaydet hakkındaki şikayet, öneri ve teşekkürlerinizi bu formla iletin.',
         B('sk', '<a href="/iletisim.html">İletişim</a> / Geri bildirim', 'Şikayet ve öneri', 'Memnun kalmadığınız ya da geliştirmemizi istediğiniz bir şey mi var? Yazın.') + FORM + SON)
    uretilen.append('sikayet-ve-oneri.html')
    return uretilen
