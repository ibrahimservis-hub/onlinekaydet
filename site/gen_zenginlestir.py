#!/usr/bin/env python3
"""Kısa kalan sayfalara genel bilgi bölümleri ekler (<!--ZEN-->…<!--/ZEN--> arası; tekrar çalıştırılabilir). Ürün özelliği iddiası yok."""
import os, re, html, json
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
src = open('gen_seo_karsilastirma.py', encoding='utf-8').read()
exec(compile(src[:src.index('RIV = {')], 'gen_seo_pre', 'exec'))
L = lambda items: '<ul>%s</ul>' % ''.join('<li>%s</li>' % x for x in items)
O = lambda items: '<ol style="max-width:760px;line-height:1.8;padding-left:20px">%s</ol>' % ''.join('<li>%s</li>' % x for x in items)
def QA(items):
    return '<section class="kk"><div class="w"><h2>Sık sorulan sorular</h2><div class="sss">%s</div></div></section>' % ''.join('<details><summary>%s</summary><p>%s</p></details>' % (a, b) for a, b in items)
def ldq(items):
    return '<script type="application/ld+json" data-zen>%s</script>' % json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': a, 'acceptedAnswer': {'@type': 'Answer', 'text': b}} for a, b in items]}, ensure_ascii=False)
P = {}
P['blog-servis-kaydi-bilgileri.html'] = (
 sec('Telefonda hangi sırayla sormalı?', O(['Önce adı ve telefonu alın; görüşme kopsa bile geri arayabilirsiniz.', 'Adresi ve tarifini isteyin: bina, kat, kapı, yakın bir nokta.', 'Cihazın markasını ve modelini sorun; bilmiyorsa etiketin yerini tarif edin.', 'Arızayı müşterinin kendi cümleleriyle yazın; yorum katmayın.', 'Uygun gün ve saat aralığını netleştirin, müşteriye tekrar edin.'])) +
 sec('Her bilgi neden gerekli?', '<div class="kt">%s</div>' % ''.join('<div class="r"><b>%s</b><span>%s</span></div>' % x for x in [('Adres ve tarif', 'Usta yolda müşteriyi tekrar aramak zorunda kalmaz; gecikme azalır.'), ('Cihaz bilgisi', 'Doğru yedek parçayı yanına alır; ikinci ziyaret gerekmez.'), ('Arıza tarifi', 'Teşhis sahada hızlanır; müşteriyle ne konuşulduğu kayıtta kalır.'), ('Randevu aralığı', 'Gün planı yapılır, aynı bölgedeki işler birleştirilir.'), ('Atanan usta', 'Sorumlu belli olur; müşteri kiminle görüşeceğini bilir.')]), tint=True) +
 sec('Sık yapılan hatalar', L(['Telefon numarasını yalnız tek yere yazıp başka alana eklememek.', 'Adresi “merkez” ya da “yeni mahalle” gibi eksik yazmak.', 'Cihaz yaşını sormamak; garanti durumu belirsiz kalır.', 'Arıza alanına yalnızca “çalışmıyor” yazmak.', 'Randevuyu müşteriye yazılı ya da sözlü teyit etmemek.'])) +
 sec('Kayıt açıldıktan sonra', L(['Müşteriye randevu bilgisini mesajla iletin.', 'Atanan ustanın kayıttaki bilgiyi gördüğünden emin olun.', 'İş bitince yapılan işlemi, parçayı ve tutarı aynı kayda ekleyin.', 'Tahsilatı kayda bağlayın; sonradan “ödedim mi?” araması bitsin.']), tint=True),
 [('Müşteri bilgi vermek istemezse?', 'Zorunlu alanları kısa tutun: ad, telefon, adres ve arıza yeterlidir. Diğer bilgileri usta sahada tamamlayabilir.'), ('Kayıtta fotoğraf gerekir mi?', 'Cihazın durumunu göstermek için teslim alırken fotoğraf çekmek iyi bir uygulamadır; sektöre göre zorunluluk değişir.'), ('Aynı müşteri tekrar ararsa?', 'Telefon numarasıyla eski kayıt bulunur; önceki arıza ve işlem geçmişi yeni kaydı hızlandırır.')])
P['blog-servis-fisi-nasil-hazirlanir.html'] = (
 sec('Servis fişi ne işe yarar?', L(['Cihazın hangi durumda teslim alındığını gösterir.', 'Müşteriyle yapılan mutabakatı yazılı hâle getirir.', 'Garanti ve tahsilat sürecinin başlangıç belgesidir.', 'Aynı cihaz tekrar geldiğinde geçmişi bulmayı kolaylaştırır.'])) +
 sec('Fiş numarası nasıl verilmeli?', '<p>Numara her fişte benzersiz olmalı ve sıralı gitmelidir. Böylece müşteri durumu sorarken tek bir numara söyler, siz de kaydı saniyeler içinde bulursunuz. Yıl ve sıra numarasını birleştiren bir düzen, eski kayıtları karıştırmamak için işe yarar.</p>', tint=True) +
 sec('Fişte dikkat edilecekler', L(['Fiyatı “yaklaşık” yazıyorsanız bunu açıkça belirtin; kesin tutar işlem sonrası yazılır.', 'Müşterinin bıraktığı aksesuarları (şarj aleti, kutu, kablo) tek tek yazın.', 'Cihazın dış durumunu (çizik, kırık) kayda geçirin.', 'KVKK aydınlatma ve cihaz saklama süresi gibi koşulları kendi işinize göre ekleyin.', 'İmzayı hem teslim alırken hem teslim ederken alın.'])) +
 sec('Kâğıt fiş ile dijital fiş', '<div class="kt">%s</div>' % ''.join('<div class="r"><b>%s</b><span>%s</span></div>' % x for x in [('Okunaklılık', 'Dijital fişte el yazısı sorunu olmaz.'), ('Kayıp', 'Kâğıt kaybolabilir; dijital kayıt arama ile bulunur.'), ('Müşteriye gönderme', 'Dijital fiş PDF olarak iletilebilir.'), ('Hız', 'Kâğıt fiş hızlıdır ama arama ve raporlama zordur.')]), tint=True),
 [('Servis fişi yasal olarak zorunlu mu?', 'Fiş, ticari ilişkide kanıt niteliğindedir. Yasal yükümlülükler işinize göre değişir; ayrıntı için mali müşavirinize ya da mevzuata bakın.'), ('Fişi ne kadar saklamalıyım?', 'Saklama süresi mevzuata ve işinize bağlıdır; mali müşavirinize danışın. Dijital kayıtta saklama kolaylaşır.'), ('Müşteri imza atmak istemezse?', 'Teslim alma koşullarını açıklayın; imza olmadan işleme başlamamak sizi korur. Bu sizin işletme politikanızdır.')])
P['blog-servis-takip-programi-nedir.html'] = (
 sec('Kimler kullanır?', L(['Kombi, klima, beyaz eşya gibi teknik servisler.', 'Araç, telefon ve bilgisayar onarım atölyeleri.', 'Randevuyla çalışan kuaför, klinik ve güzellik merkezleri.', 'Montaj, tesisat ve elektrik ustaları.'])) +
 sec('Excel ve defterden farkı', '<div class="kt">%s</div>' % ''.join('<div class="r"><b>%s</b><span>%s</span></div>' % x for x in [('Arama', 'Müşteri geçmişi ad ya da telefonla saniyeler içinde bulunur.'), ('Çok kullanıcı', 'Birden çok kişi aynı anda çalışır; sürüm karışmaz.'), ('Yetki', 'Her çalışan yalnız kendi ekranını görür.'), ('Rapor', 'Tahsilat ve borç raporları otomatik oluşur.'), ('Mesaj', 'Müşteriye bilgilendirme mesajı gönderilebilir.')]), tint=True) +
 sec('Geçiş nasıl yapılır?', O(['Mevcut müşteri listenizi (ad, telefon, adres) tek bir dosyada toplayın.', 'Kullanacağınız kayıt alanlarını belirleyin: cihaz, arıza, işlem, tutar.', 'Birkaç gerçek işi yeni sistemde açıp deneyin.', 'Ekibe kısa bir eğitim verin; kimin hangi ekranı kullanacağını belirleyin.', 'Birkaç hafta paralel çalışın, sonra eski yöntemi bırakın.'])) +
 sec('Maliyet kalemleri', L(['Aylık ya da yıllık yazılım bedeli.', 'Kullanıcı ya da usta başına ek ücret olup olmadığı.', 'SMS ve mesaj gönderim ücretleri (sağlayıcıya göre).', 'Kurulum ve veri aktarımı için ek ücret.', 'Destek ve eğitim koşulları.']), tint=True) +
 sec('Sık yapılan hatalar', L(['Yalnızca fiyata bakıp ihtiyaç listesi çıkarmamak.', 'Denemeden satın almak.', 'Ekibin kullanımını hesaba katmamak.', 'Eski verileri aktarmayı planlamamak.'])),
 [('Küçük bir servis için gerekli mi?', 'Kayıt sayısı azken Excel yeterli olabilir; müşteri geçmişi ve tahsilat takibi zorlaşmaya başlayınca program işi kolaylaştırır.'), ('Verilerim güvende mi?', 'Her yazılım sağlayıcısına veri güvenliği, yedekleme ve KVKK konularını sorun; yanıtlar yazılı olsun.'), ('Denemek ücretsiz mi?', 'OnlineKaydet’te 7 gün ücretsiz denersiniz.')])
P['hesaplama-araclari.html'] = (
 sec('Hangi hesap ne için?', '<div class="kt">%s</div>' % ''.join('<div class="r"><b>%s</b><span>%s</span></div>' % x for x in [('KDV', 'Fiyatın KDV dahil ve hariç değerini görmek, teklif ve fatura hazırlamak için.'), ('Komisyon', 'Pazaryeri satışında komisyon düştükten sonra eline kalan tutarı görmek için.'), ('Desi', 'Kargo ücretini belirleyen desi değerini bulmak için.'), ('Kâr marjı', 'Maliyetine göre satış fiyatı belirlemek için.'), ('Vade', 'Vadeli satışta vade farkını ve ödeme tarihini görmek için.')])) +
 sec('Hesap yaparken dikkat', L(['KDV oranını ürün ya da hizmet türüne göre kendiniz seçin; oranlar için mali müşavirinize danışın.', 'Komisyon oranları pazaryeri ve kategoriye göre değişir; güncel oranı pazaryerinin kendi sayfasından kontrol edin.', 'Kargo desi hesabı firmaya göre farklılık gösterebilir.', 'Sonuçlar bilgilendirme amaçlıdır; resmi işlemlerde mali müşavirinizin onayını alın.']), tint=True),
 [('Hesaplamalarım kaydediliyor mu?', 'Araçlar kayıt istemez; sayfada yaptığınız hesap sunucuya gönderilmez.'), ('Oranları güncel tutuyor musunuz?', 'Oran ve faiz değerlerini hesaplayıcıya kendiniz girersiniz; böylece güncel oranı siz belirlersiniz.')])
P['web-sitesi.html'] = (
 sec('Yayına çıkmadan önce kontrol listesi', L(['Firma adı, adres ve çalışma saatleri doğru mu?', 'Her sayfanın başlığı ve kısa açıklaması yazıldı mı?', 'Fotoğraflar kendi işinize ait ve doğru boyutta mı?', 'Telefon düğmesi ve iletişim formu çalışıyor mu?', 'Telefonda menü ve alt çubuk düzgün görünüyor mu?', 'Alan adı bağlandı ve SSL etkin mi?'])) +
 sec('Arama motorları için ilk adımlar', L(['Her hizmete kendi sayfanızı yazın; tek sayfada hepsini toplamayın.', 'Başlıkta hizmeti ve bölgeyi belirtin.', 'Fotoğraflara açıklayıcı metin ekleyin.', 'Aynı metni birden çok sayfada tekrar etmeyin.', 'Siteyi Google Search Console’a ekleyin ve sitemap gönderin.']), tint=True) +
 sec('Site güncel kalsın', L(['Fiyat ve çalışma saati değiştiğinde sitede de değiştirin.', 'Yeni işlerinizin fotoğraflarını ekleyin.', 'Soru-cevap bölümünü müşterilerin gerçek sorularıyla güncelleyin.', 'Ayda bir telefonda siteyi gezip kontrol edin.'])),
 [('Siteyi kendim değiştirebilir miyim?', 'Evet. Metin, yazı tipi, görsel ve menü panelden değişir; teknik bilgi gerekmez.'), ('Kendi alan adımı bağlayabilir miyim?', 'Evet. Alan adı bağlama pakete dahildir; adım adım yönlendirme alırsınız.'), ('Temayı sonradan değiştirebilir miyim?', 'Evet. Tema değiştirirken içerikleriniz korunur; yeni temada bölümleri kontrol etmeniz yeterlidir.')])
P['ozellikler.html'] = (
 sec('Hangi özellik hangi sorunu çözer?', '<div class="kt">%s</div>' % ''.join('<div class="r"><b>%s</b><span>%s</span></div>' % x for x in [('Randevu ve takvim', 'Günün işleri dağınık not yerine tek takvimde toplanır.'), ('Kasa ve muhasebe', 'Tahsilat, gider ve alacaklar tek yerden izlenir.'), ('Personel takibi', 'Kim hangi işte, kim ne kadar yaptı görülür.'), ('Web sitesi editörü', 'Siteyi değiştirmek için yazılımcıya ihtiyaç kalmaz.'), ('E-ticaret', 'Ürün ve siparişler tek listede yönetilir.'), ('Pazaryeri', 'Birden çok platformda satış tek panelden izlenir.'), ('Bayi (B2B)', 'Bayiye özel fiyat ve cari hesap tutulur.'), ('Hazır temalar', 'Sektörünüze uygun hazır siteyle hızlı başlarsınız.')])) +
 sec('Kimler için uygun?', L(['Servis işi yapanlar: kayıt, usta ve tahsilat takibi isteyenler.', 'Randevuyla çalışan işletmeler.', 'Ürün satan ve pazaryerinde yer almak isteyenler.', 'Birden fazla çalışanı olan, işi tek ekrandan görmek isteyenler.']), tint=True) +
 sec('Başlarken', O(['Sektörünüzü seçin; panel kendi terimlerinizle açılır.', 'Ekibinizi ve ustalarınızı ekleyin.', 'Birkaç gerçek kayıt girin ve ekranları gezin.', 'Web sitesi ve mağaza gibi ek özellikleri paketinize göre açın.'])),
 [('Hangi özellik hangi pakette?', 'Paketlerin içeriği Paketler sayfasında satır satır yazar.'), ('Özellikleri tek tek açıp kapatabilir miyim?', 'Panelde ihtiyacınız olmayan ekranları kullanmayabilirsiniz; paket kapsamı için Paketler sayfasına bakın.')])
def isle(fn):
    s = open(fn, encoding='utf-8').read()
    s = re.sub(r'<!--ZEN-->.*?<!--/ZEN-->', '', s, flags=re.S)
    s = re.sub(r'<script type="application/ld\+json" data-zen>.*?</script>', '', s, flags=re.S)
    govde, qa = P[fn][0], P[fn][1]
    blok = '<!--ZEN-->' + STIL + govde + QA(qa) + '<!--/ZEN-->'
    if '<section id="kayit"' in s: i = s.index('<section id="kayit"')
    elif '\n</div></div></main>' in s: i = s.index('\n</div></div></main>')
    else: i = s.index('</main>')
    s = s[:i] + blok + s[i:]
    s = s.replace('</head>', ldq(qa) + '</head>', 1)
    open(fn, 'w', encoding='utf-8').write(s)
if __name__ == '__main__':
    for fn in P: isle(fn)
    print(len(P), 'sayfa')
