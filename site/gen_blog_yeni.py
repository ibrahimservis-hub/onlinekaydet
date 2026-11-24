#!/usr/bin/env python3
"""4 yeni blog/rehber sayfası. Çalıştır: python3 site/gen_blog_yeni.py  (sonra python3 site/v9/nx_kabuk.py).
Kural: uydurma istatistik/yorum yok; genel ve doğrulanabilir bilgi; görünür telefon metni yok."""
import os, re
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
src = open('gen_seo_karsilastirma.py', encoding='utf-8').read()
exec(compile(src[:src.index('RIV = {')], 'gen_seo_pre', 'exec'))
ACT = '<a class="bt" href="/demo.html">Ücretsiz deneyin</a><a class="bt l" href="tel:05444444004">Hemen arayın</a>'
def cta2(): return cta().replace('>0544 444 40 04</a>', '>Hemen arayın</a>')
P = lambda *x: ''.join('<p>%s</p>' % t for t in x)
L = lambda x: '<ul>%s</ul>' % ''.join('<li>%s</li>' % i for i in x)
def chk(x): return '<ul style="list-style:none;padding-left:0">%s</ul>' % ''.join('<li>&#9744; %s</li>' % i for i in x)
def ilgili(links): return sec('İlgili sayfalar', L(['<a href="%s">%s</a>' % l for l in links]), tint=True)
for f in ('fiyatlar.html', 'demo.html', 'bilgi-randevu-ve-takvim.html', 'bilgi-musteri-yonetimi.html', 'bilgi-baslangic.html', 'bilgi-siparis-ve-kargo.html', 'bilgi-urun-ekleme.html', 'sektor-eticaret.html', 'sektor-kombi.html', 'sektor-beyaz-esya.html', 'sektor-klima.html', 'sektor-kuafor.html', 'sektor-dis-klinigi.html', 'blog-servis-kaydi-bilgileri.html', 'blog-servis-takip-programi-nedir.html'):
    assert os.path.exists(f), f
PAGES = []
EK = {
'blog-servis-kaydi-nasil-tutulur.html': [('Sık yapılan hatalar', L(['Kaydı işten sonraya bırakmak; akşam hatırlanan bilgi eksik ve yanlış olur.', 'Aynı müşteriyi farklı yazımlarla (ad, soyad sırası, telefon biçimi) tekrar tekrar girmek.', 'Yapılan işlemi “bakım yapıldı” gibi tek kelimeyle geçmek; ileride neyin değiştiği anlaşılmaz.', 'Parça ve işçilik ücretini kayıttan ayrı bir yere not etmek; tahsilat ile iş eşleşmez.', 'Yedek almamak. Defter ya da bilgisayar kaybolduğunda bütün geçmiş gider.']) + P('Hangi yöntemi seçerseniz seçin, kaydı işi yaptığınız anda ve her seferinde aynı düzende tutmak, yöntemin kendisinden daha belirleyicidir. Düzenli tutulan bir defter, dağınık bir programdan daha işe yarar.'))],
'blog-teknik-servis-musteri-memnuniyeti.html': [('Küçük işletmede neyi önceliklendirmeli?', P('Hepsini aynı anda uygulamaya çalışmak yerine tek bir sorunla başlayın. Müşterilerin en çok neyden yakındığını düşünün: geç gelme mi, fiyat belirsizliği mi, iş sonrası ilgisizlik mi? İlk iki haftayı bu soruna ayırın, sonra bir sonraki adıma geçin.', 'Ekibiniz varsa konuyu birlikte konuşun. Sahadaki usta, müşterinin gerçekte ne dediğini en iyi bilen kişidir. Ustaya “müşteri şikâyetini ilk sen duyuyorsun, bunu bana nasıl iletirsin?” diye sormak, çoğu zaman en değerli geri bildirimi getirir. Bu notları bir yere yazmak da ayrı bir alışkanlıktır; defter, tablo ya da bir program olabilir.'))],
'blog-randevu-hatirlatma-mesaji.html': [('Mesaj yazarken kaçınılacaklar', L(['Uzun ve resmî cümleler; mesaj okunmadan geçilir.', 'Birden fazla işlem isteyen mesaj (onayla, iptal et, adres gönder aynı anda).', 'Tehdit ya da ceza tonu; müşteriyi uzaklaştırır.', 'Müşterinin adını yanlış yazmak ya da şablondaki köşeli parantezleri doldurmayı unutmak.', 'Gece geç saatte göndermek. Makul bir saat seçin.']) + P('Mesajın tonu işletmenize uygun olmalı. Kuaför samimi, klinik daha ölçülü yazabilir. Önemli olan müşterinin tek bakışta tarihi, saati ve ne yapması gerektiğini anlamasıdır.'))],
'blog-online-satisa-baslama-kontrol-listesi.html': [('Sık yapılan hatalar', L(['Maliyeti kargo ve komisyon olmadan hesaplamak.', 'Stokta olmayan ürünü satışta bırakmak; müşteriye iptal bildirmek güveni zedeler.', 'İade ve teslim koşullarını yazmadan satışa çıkmak.', 'Fotoğrafı telefonla karanlıkta çekmek ya da başka sitelerden almak.', 'Telefondan görünümü hiç denememek; birçok müşteri alışverişi telefonla yapar.']) + P('Bu hataların çoğu, ilk siparişi uçtan uca kendiniz vererek önceden yakalanır. Bir arkadaşınıza ya da yakınınıza siteyi telefonundan denetmek de işe yarar. Bulduğunuz her eksik, gerçek bir müşterinin yaşayacağı sorundur.'))],
}
def yaz(fn, title, desc, crumb, h1, lead, bolumler, kontrol_baslik, kontrol, soru, links):
    bolumler = list(bolumler) + EK.get(fn, [])
    body = STIL + ''.join(sec(t, i, tint=(n % 2 == 1)) for n, (t, i) in enumerate(bolumler)) \
        + sec(kontrol_baslik, chk(kontrol)) + faq('Sık sorulan sorular', soru) + ilgili(links) + cta2()
    page(fn, title, desc, crumb, h1, lead, body, acts=ACT, ld=faq_ld(soru)); PAGES.append(fn)
    h = open(fn, encoding='utf-8').read(); h = re.sub(r'<script type="application/ld\+json" data-zen>.*?</script>', '', h, flags=re.S); open(fn, 'w', encoding='utf-8').write(h)

# 1 ---------------------------------------------------------------
yaz('blog-servis-kaydi-nasil-tutulur.html',
 'Servis kaydı nasıl tutulur? Kâğıt, Excel ve program karşılaştırması',
 'Servis kaydı kâğıt defterle, Excel ile ya da programla nasıl tutulur? Üç yöntemin güçlü ve zayıf yanları, hangi durumda hangisi uygun, geçiş için kontrol listesi.',
 'Servis kaydı nasıl tutulur', 'Servis kaydı nasıl tutulur: kâğıt, Excel ve program karşılaştırması',
 'Üç yöntemin de işe yaradığı bir nokta var. Sorun, iş büyüdüğünde hangisinin sizi yavaşlatmaya başladığını görmekte.',
 [('Önce kayıt neden tutulur?', P('Servis kaydı, bir işin başladığı andan müşteriye teslim edilene kadar ne olduğunun yazılı izidir. Tutulmadığında üç şey kaybolur: müşteriye ne söz verildiği, hangi parçanın takıldığı ve paranın ne kadarının alındığı. Aynı müşteri bir ay sonra tekrar aradığında “geçen sefer ne yapmıştık?” sorusunun cevabı kayıttadır.',
   'Yöntem ne olursa olsun, iyi bir kaydın bilgileri aynıdır: müşteri adı ve telefonu, adres, cihaz ya da iş türü, bildirilen arıza, yapılan işlem, kullanılan parça, işi yapan kişi, tarih ve tahsilat durumu. Hangi bilgileri alacağınızı <a href="/blog-servis-kaydi-bilgileri.html">servis kaydı bilgileri rehberimizde</a> ayrıca yazdık.')),
  ('Kâğıt defter ve fiş', P('Kâğıt, kurulum ve öğrenme gerektirmeyen yöntemdir. Tek kişilik ve günde birkaç iş yapan bir işletme için çoğu zaman yeterlidir. Fiş ya da form müşteriye imzalı verildiğinde elle tutulur bir belge de olur.') +
   '<p><b>Güçlü yanı:</b> sıfır maliyet, hemen başlanır, elektrik ya da internet gerekmez.</p><p><b>Zayıf yanı:</b> aramak zordur. “Geçen yıl Ahmet Bey’in kombisine ne yapmıştık?” sorusu için sayfa sayfa karıştırmak gerekir. Defter kaybolur, ıslanır, el yazısı okunmaz. Birden fazla usta varsa kayıt dağılır, kimin hangi işte olduğunu görmek için herkesin defterine bakmanız gerekir.'),
  ('Excel ve tablo dosyaları', P('Excel, kâğıdın bir adım ötesidir. Arama, filtreleme ve toplam alma imkânı verir; birkaç yüz kayda kadar rahat yürür. Birçok işletme ilk dijital kaydını burada tutar.') +
   '<p><b>Güçlü yanı:</b> herkes bilir, ek ücret yoktur, istediğiniz sütunu eklersiniz.</p><p><b>Zayıf yanı:</b> aynı dosyayı iki kişi aynı anda düzenlediğinde sürümler çakışır. Sütun düzeni zamanla bozulur, telefon numaraları farklı biçimlerde girilir ve arama güvenilmez hâle gelir. Müşteriye otomatik mesaj göndermez, ustaya iş atamaz, tahsilatı ve borcu cari olarak takip etmez. Dosya bir kişinin bilgisayarında duruyorsa o kişi yokken kimse göremez.'),
  ('Servis takip programı', P('Program, kaydı bir kez girip her yerde kullanmanızı sağlar: aynı kayıttan servis fişi çıkar, usta iş listesini görür, tahsilat kasaya işler, müşteri geçmişi telefon numarasıyla bulunur. Bulut tabanlı olanlarda ofiste de sahada da aynı veriye ulaşılır.',
   'Karşılığında bir ücret ve kısa bir alışma süresi vardır. Seçerken neye bakacağınızı <a href="/blog-servis-takip-programi-nedir.html">servis takip programı nedir</a> yazımızda anlattık. OnlineKaydet’in kayıt, usta, kasa ve randevu tarafını <a href="/demo.html">demo hesabıyla</a> 7 gün ücretsiz deneyebilirsiniz; paketler <a href="/fiyatlar.html">fiyatlar sayfasında</a> açık yazılıdır.')),
  ('Hangi durumda hangisi?', kt([('Tek kişi, az iş', 'Kâğıt ya da basit bir Excel yeterli olur'),
   ('Müşteri geçmişi sık aranıyor', 'Excel’i geçip programa bakma zamanı'),
   ('Birden fazla usta var', 'Ortak ve eş zamanlı çalışan bir program gerekir'),
   ('Müşteriye hatırlatma, tahsilat takibi istiyorsunuz', 'Program; Excel bu işleri kendiliğinden yapmaz')], head=['Durum', 'Uygun yöntem']) +
   P('Bu bir kural değil, genel bir yönlendirmedir. İşinizin hızı ve ekibinizin büyüklüğü belirleyicidir.')),
  ('Yöntem değiştirirken', P('Kâğıttan ya da Excel’den programa geçerken eski kayıtların hepsini taşımak şart değil. Çoğu işletme için en az sancılı yol, belirli bir tarihten itibaren yeni kayıtları programa girmek ve eski kayıtları arşiv olarak saklamaktır. Müşteri listesi gibi sık aranan veriyi önce taşırsınız, geri kalanı zamanla.',
   'Geçişte ekibin alışması için ilk hafta iki yöntemi birlikte yürütmek makul olur. Kişisel veri içeren müşteri kayıtlarını, hangi yöntemi kullanırsanız kullanın, yetkisiz kişilerin erişemeyeceği bir yerde saklamak KVKK açısından da gereklidir.')) ],
 'Servis kaydı kontrol listesi',
 ['Her kayıtta müşteri adı, telefon ve adres var.', 'Bildirilen arıza ile yapılan işlem ayrı yazılıyor.', 'Kullanılan parçalar ve fiyatları kayıtta görünüyor.', 'Kaydı işi yapan kişinin adı ve tarihi var.', 'Tahsilat durumu (alındı, kısmi, borç) açık.', 'Müşteri geçmişini telefon numarasıyla bulabiliyorsunuz.', 'Kayıtların yedeği ya da ikinci bir kopyası var.', 'Müşteri bilgilerine yalnız yetkili kişiler erişiyor.'],
 [('Servis kaydı tutmak zorunlu mu?', 'Faturalı satış ve garanti kapsamındaki işlerde belge düzeni yasal yükümlülüklerle bağlantılıdır. Kendi işletmeniz için hangi kayıtların zorunlu olduğunu mali müşavirinize ya da ilgili mevzuata göre netleştirmeniz gerekir.'),
  ('Excel ile servis takibi yeterli olur mu?', 'Az sayıda kayıt ve tek kullanıcıda yeterli olabilir. Birden fazla usta, sık müşteri geçmişi araması ve tahsilat takibi başladığında Excel zorlaşır.'),
  ('Programa geçince eski kayıtlarım kaybolur mu?', 'Hayır. Eski defter ve dosyalarınızı arşiv olarak saklayabilir, yeni kayıtları programa girebilirsiniz. Sık aranan müşteri listesini ayrıca taşımak iyi bir başlangıçtır.'),
  ('Servis kaydı programını denemeden almalı mıyım?', 'Denemeden almamanızı öneririz. OnlineKaydet’te 7 gün ücretsiz deneme var; gerçek birkaç kaydı girerek işinize uyup uymadığını görebilirsiniz.')],
 [('/fiyatlar.html', 'Fiyatlar ve paketler'), ('/demo.html', 'Ücretsiz demo'), ('/bilgi-musteri-yonetimi.html', 'Bilgi bankası: Müşteri yönetimi'), ('/bilgi-baslangic.html', 'Bilgi bankası: Başlangıç'), ('/sektor-kombi.html', 'Kombi servisi için yazılım'), ('/sektor-beyaz-esya.html', 'Beyaz eşya servisi için yazılım')])

# 2 ---------------------------------------------------------------
yaz('blog-teknik-servis-musteri-memnuniyeti.html',
 'Teknik serviste müşteri memnuniyeti nasıl artırılır? 8 uygulanabilir adım',
 'Teknik serviste müşteri memnuniyetini artırmanın pratik yolları: net randevu, dürüst bilgilendirme, düzenli kayıt, teslim sonrası takip. Kontrol listesiyle.',
 'Teknik servis müşteri memnuniyeti', 'Teknik serviste müşteri memnuniyeti nasıl artırılır?',
 'Memnuniyet büyük jestlerden çok küçük sözlerin tutulmasından gelir. Servis işinde bu sözler çoğunlukla zaman, fiyat ve bilgi ile ilgilidir.',
 [('Memnuniyet nereden doğar?', P('Teknik servis çağıran müşteri çoğu zaman bir sorunla karşılaşmıştır: kombi çalışmıyor, makine su akıtıyor, bilgisayar açılmıyor. Müşteri, işin kusursuz olmasını kadar belirsizlikten kurtulmayı da bekler. “Ne zaman gelecek, ne kadar tutar, ne yapılacak?” sorularının cevabını bilmek, gerginliği büyük ölçüde azaltır.',
   'Bu yüzden memnuniyetin temel taşları üç tanedir: zamanında gelmek, işi anlaşıldığı gibi yapmak ve süreç boyunca bilgi vermek. Aşağıdaki adımlar bu üçünü destekler.')),
  ('1. Randevuda net saat aralığı verin', P('“Bugün uğrarız” demek, müşteriyi gün boyu bekletir. Mümkünse bir saat aralığı verin ve gecikme olacaksa önceden haber verin. Gecikme anlaşılır bir sebep ve kısa bir mesajla bildirildiğinde çoğu müşteri için sorun olmaktan çıkar. Randevu düzeni için <a href="/bilgi-randevu-ve-takvim.html">randevu ve takvim rehberine</a> bakabilirsiniz.')),
  ('2. İşe başlamadan önce fiyat çerçevesini söyleyin', P('Fiyat sürprizi, memnuniyetsizliğin en bilinen kaynağıdır. Kesin fiyat arızayı görmeden verilemese bile iş gücü, parça ve yol ücretinin nasıl hesaplandığını baştan söylemek güven verir. Beklenenden pahalı bir parça çıkarsa işlemden önce müşteriye sorun; onay alınmamış bir ek ücret ilişkiyi bozar.')),
  ('3. Yapılan işi yazılı bırakın', P('Servis fişi ya da form, müşteriye ne yapıldığını gösterir ve olası bir anlaşmazlıkta iki tarafı da korur. Fişte bulunması gerekenleri <a href="/blog-servis-fisi-nasil-hazirlanir.html">servis fişi rehberinde</a> listeledik. Değiştirilen parçayı müşteriye göstermek ve eski parçayı istenirse vermek de şeffaflık sağlar.')),
  ('4. Müşteri geçmişini bilin', P('Aynı müşteri tekrar aradığında geçmiş kaydı hazırsa “bu cihazı en son şu tarihte şu nedenle onarmıştık” diyebilirsiniz. Bu, müşteriye değer verildiği hissini kolayca verir. Kayıtlarınız defterde dağınıksa bu bilgiye ulaşmak zordur; <a href="/bilgi-musteri-yonetimi.html">müşteri yönetimi</a> bunun için vardır.')),
  ('5. Teslimden sonra kısa bir takip yapın', P('İşten birkaç gün sonra “her şey yolunda mı?” diye sormak, küçük bir sorunu büyümeden yakalamanızı sağlar. Bu kısa mesaj, işi yarım bırakmadığınızı da gösterir. Sorun varsa hemen dönüş yapın ve şikâyeti bir kayıt olarak not edin.')),
  ('6. Şikâyeti bir veri olarak görün', P('Tekrarlayan şikâyetler genelde aynı yerden çıkar: geç gelme, anlatılmayan ek ücret, eksik temizlik. Şikâyetleri not edip ayda bir ekiple konuşmak, kişilerden çok süreçteki aksaklığı bulmanızı sağlar. Ekibin sorumluluk alanını netleştirmek için <a href="/bilgi-personel-ve-prim.html">personel ve prim</a> düzeni de yardımcı olur.'))],
 'Müşteri memnuniyeti kontrol listesi',
 ['Randevuda saat aralığı verildi.', 'Gecikme olursa müşteriye önceden haber verildi.', 'Fiyat hesabı iş başlamadan açıklandı.', 'Ek parça ya da ek ücret için onay alındı.', 'Yapılan işlem servis fişine yazıldı.', 'Müşteriye değiştirilen parça gösterildi.', 'Teslimden birkaç gün sonra takip mesajı gönderildi.', 'Gelen şikâyet kayda alındı ve ekiple konuşuldu.'],
 [('Müşteri memnuniyetini ölçmek için ne yapabilirim?', 'En basit yol, işten sonra müşteriye kısa bir soru sormaktır: iş beklentiyi karşıladı mı, bir eksik var mı? Gelen cevapları not edip tekrarlayan konulara bakın.'),
  ('Geç kalacağım zaman ne yapmalıyım?', 'Mümkün olan en erken anda haber verin, yeni bir saat aralığı söyleyin ve kısa bir özür ekleyin. Haber vermemek, gecikmenin kendisinden daha çok güveni zedeler.'),
  ('Haksız şikâyetle karşılaşırsam?', 'Yazılı servis kaydı ve imzalı fiş burada önemlidir. Sakin kalın, kayıtlara göre ne yapıldığını anlatın ve çözüm önerin.'),
  ('Program kullanmak memnuniyeti artırır mı?', 'Tek başına artırmaz, ama randevu, müşteri geçmişi ve hatırlatma gibi işleri düzenli tuttuğu için yukarıdaki adımları uygulamayı kolaylaştırır.')],
 [('/fiyatlar.html', 'Fiyatlar ve paketler'), ('/demo.html', 'Ücretsiz demo'), ('/bilgi-randevu-ve-takvim.html', 'Bilgi bankası: Randevu ve takvim'), ('/bilgi-musteri-yonetimi.html', 'Bilgi bankası: Müşteri yönetimi'), ('/sektor-klima.html', 'Klima servisi için yazılım'), ('/sektor-kombi.html', 'Kombi servisi için yazılım')])

# 3 ---------------------------------------------------------------
yaz('blog-randevu-hatirlatma-mesaji.html',
 'Randevu hatırlatma mesajı nasıl yazılır? Örnek şablonlarla no-show azaltma',
 'Randevu hatırlatma mesajında neler yazılmalı, ne zaman gönderilmeli? Gelmeyen müşteriyi (no-show) azaltmak için hazır mesaj şablonları ve kontrol listesi.',
 'Randevu hatırlatma mesajı', 'Randevu hatırlatma mesajı nasıl yazılır: no-show azaltma rehberi',
 'Randevuya gelmeyen müşteri hem boş saat hem kayıp gelir demektir. İyi yazılmış kısa bir hatırlatma bunun önüne geçmeye yardım eder.',
 [('No-show nedir, neden olur?', P('No-show, randevu alıp haber vermeden gelmeyen müşteri anlamına gelir. Kuaför, klinik, oto servis ve teknik servis gibi saat bazlı çalışan işlerde boş kalan saat başka müşteriye verilemez. Sebepler çoğunlukla basittir: unutmak, tarihi karıştırmak, plan değişince iptal etmeyi akıl edememek ya da iptal etmenin kolay olmaması.',
   'Bu nedenlerin çoğu bilgi eksikliğidir ve bir hatırlatmayla giderilebilir. Hatırlatma mesajı bir baskı değil, müşteriye yapılmış bir hizmettir.')),
  ('İyi bir hatırlatma mesajında ne olur?', L(['<b>Kim yazıyor:</b> işletme adı mesajın başında.', '<b>Ne zaman:</b> tarih ve saat, gün adıyla birlikte.', '<b>Nerede:</b> adres ya da servis geliyorsa ziyaret saati aralığı.', '<b>Ne yapması gerekiyor:</b> onay, iptal ya da erteleme için kolay bir yol.', '<b>Kısa olmalı:</b> tek ekranda okunacak uzunlukta.']) +
   P('Kişisel veri açısından mesajda gereğinden fazla bilgi (hastalık adı, tutar gibi) vermeyin. Müşteriye ticari ileti göndermek için gereken izinler konusunda <a href="/kvkk.html">KVKK ve gizlilik</a> sayfamıza ve güncel mevzuata bakın.')),
  ('Ne zaman gönderilmeli?', P('Tek bir doğru zaman yoktur, ama genel yaklaşım iki aşamalıdır: randevudan bir ya da iki gün önce ilk hatırlatma, randevu günü sabahı ya da birkaç saat öncesinde ikinci kısa mesaj. Uzun süre önceden alınan randevularda ilk hatırlatma daha erken olabilir. İşinize göre deneyip hangi zamanın daha çok geri dönüş aldığını kendi kayıtlarınızdan görebilirsiniz.')),
  ('Hazır mesaj şablonları', '<p><b>Standart hatırlatma</b></p><blockquote>Merhaba [Ad], [İşletme adı] olarak [gün] günü saat [saat] için randevunuzu hatırlatırız. Gelemeyecekseniz lütfen bize haber verin, saatinizi değiştirelim.</blockquote>'
   '<p><b>Servis ziyareti için</b></p><blockquote>Merhaba [Ad], [gün] günü [saat aralığı] arasında ustamız size uğrayacak. Adreste olamayacaksanız lütfen önceden bildirin.</blockquote>'
   '<p><b>Onay isteyen</b></p><blockquote>Merhaba [Ad], [gün] [saat] randevunuz için geliyor musunuz? Onaylamak ya da değiştirmek için bu mesaja cevap verebilirsiniz.</blockquote>'
   '<p><b>Randevudan sonra teşekkür</b></p><blockquote>Merhaba [Ad], bugün bize geldiğiniz için teşekkür ederiz. Aklınıza takılan bir şey olursa yazabilirsiniz.</blockquote>'
   '<p>Köşeli parantezleri kendi bilgilerinizle değiştirin. Şablonları programda kaydedip tek tıkla göndermek zaman kazandırır.</p>'),
  ('Mesajdan fazlası: iptali kolaylaştırın', P('Hatırlatmanın amacı yalnız gelmeyi sağlamak değil, gelemeyecek müşterinin vaktinde haber vermesini sağlamaktır. İptal edilen saati başka biri kullanabilir. İptal için tek bir yol (cevap yazmak, link ya da arama) belirleyin ve mesajda belirtin. İptal eden müşteriyi cezalandırmayın; bir sonraki sefer yine sizi seçmesi daha değerlidir.')),
  ('Hatırlatmayı elle mi, otomatik mi yapmalı?', P('Birkaç randevuyu elle aramak mümkündür. Günde onlarca randevu varsa bu iş zaman alır ve bazı günler unutulur. OnlineKaydet’te randevu takvimi ve mesaj şablonları aynı panelde durur; hangi özelliklerin hangi pakette olduğu <a href="/fiyatlar.html">fiyatlar sayfasında</a> yazılıdır, kurulumu <a href="/demo.html">ücretsiz demoyla</a> görebilirsiniz. Randevu düzeni için <a href="/bilgi-randevu-ve-takvim.html">randevu ve takvim</a> rehberine de bakın.'))],
 'Hatırlatma mesajı kontrol listesi',
 ['İşletme adı mesajın başında yazıyor.', 'Tarih, saat ve gün adı açık.', 'Adres ya da ziyaret aralığı belirtilmiş.', 'İptal ya da erteleme için tek ve kolay bir yol var.', 'Mesaj tek ekranda okunacak kadar kısa.', 'Gereksiz kişisel bilgi yok.', 'İki aşamalı hatırlatma (önceki gün ve gün içi) planlandı.', 'İptal edilen saat hızla başka müşteriye açılıyor.'],
 [('Hatırlatma mesajı SMS mi, WhatsApp mı olmalı?', 'Müşterinizin en rahat kullandığı kanal uygundur. Hangi kanalda geri dönüş aldığınızı birkaç hafta izleyip karar verebilirsiniz. Kanal ne olursa olsun müşterinin izni ve güncel mevzuat önemlidir.'),
  ('Mesajı kaç kez göndermeliyim?', 'Çoğu işletme için iki mesaj yeterlidir: bir ya da iki gün önce ve gün içinde. Fazla mesaj rahatsız edebilir.'),
  ('No-show tamamen biter mi?', 'Bitmez, ama hatırlatma ve kolay iptal yolu genelde azaltmaya yardım eder. Kesin bir oran vaat edemeyiz; sonucu kendi kayıtlarınızdan görürsünüz.'),
  ('Gelmeyen müşteriden ücret alınabilir mi?', 'Bu, işletmenin politikasına ve müşteriyle baştan yapılan anlaşmaya bağlıdır. Uygulamadan önce koşulları müşteriye açıkça bildirmek ve gerekirse hukuki danışmanlık almak doğru olur.')],
 [('/fiyatlar.html', 'Fiyatlar ve paketler'), ('/demo.html', 'Ücretsiz demo'), ('/bilgi-randevu-ve-takvim.html', 'Bilgi bankası: Randevu ve takvim'), ('/sektor-kuafor.html', 'Kuaför için yazılım'), ('/sektor-dis-klinigi.html', 'Diş kliniği için yazılım'), ('/sektor-klima.html', 'Klima servisi için yazılım')])

# 4 ---------------------------------------------------------------
yaz('blog-online-satisa-baslama-kontrol-listesi.html',
 'Küçük işletme için çevrimiçi satışa başlama kontrol listesi',
 'Küçük işletme internetten satışa nasıl başlar? Ürün, fiyat, ödeme, kargo, yasal bilgiler ve site için adım adım kontrol listesi.',
 'Çevrimiçi satışa başlama', 'Küçük işletme için çevrimiçi satışa başlama kontrol listesi',
 'İnternetten satış tek bir karar değil, birkaç küçük hazırlığın toplamıdır. Sırayla ilerlerseniz çoğu kolayca çözülür.',
 [('Başlamadan önce üç soru', P('Önce neyi, kime, nasıl satacağınızı yazın. Bunlar netse sonraki adımlar kolaylaşır. <b>Neyi:</b> tüm ürünleri mi, yoksa en iyi satan birkaç ürünü mü ile başlayacaksınız? <b>Kime:</b> yalnız çevrenize mi, yoksa Türkiye geneline mi? <b>Nasıl:</b> kendi sitenizden mi, pazaryerinden mi, ikisinden mi?',
   'Pek çok küçük işletme küçük başlayıp ürün sayısını sonradan artırır. İlk haftada yüzlerce ürün yüklemek şart değildir.')),
  ('Ürün bilgisi ve fotoğraf', P('Her ürün için net bir ad, açıklama, fiyat, stok bilgisi ve kendi çektiğiniz temiz fotoğraflar gerekir. Müşteri ürünü elle tutamadığı için fotoğraf ve açıklama satışı belirler. Boyut, malzeme, kullanım gibi sorulacak bilgileri açıklamaya yazın. Ürünleri panele nasıl ekleyeceğinizi <a href="/bilgi-urun-ekleme.html">ürün ekleme rehberinde</a> adım adım anlattık.')),
  ('Fiyat ve maliyet', P('Fiyatı belirlerken ürün maliyetinin yanında kargo, ambalaj, ödeme komisyonu, varsa pazaryeri komisyonu ve iade payını hesaba katın. Bunları hesaba katmadan konan fiyat, satış arttıkça zarar yaratabilir. Aylık sabit giderlerinizi de (yazılım, depolama) bir tabloda toplayın.')),
  ('Satış kanalı: kendi site ve pazaryeri', P('Kendi siteniz markanızı ve müşteri verinizi size bırakır, ama ziyaretçiyi sizin getirmeniz gerekir. Pazaryerinde hazır bir ziyaretçi kitlesi vardır, ancak komisyon ödenir ve kurallar pazaryerine aittir. Birçok işletme ikisini birlikte yürütür. OnlineKaydet’te e-ticaret ve pazaryeri bağlantıları ile hangi paketlerde bulunduğu <a href="/fiyatlar.html">fiyatlar sayfasında</a> yazılıdır; sektör örneği için <a href="/sektor-eticaret.html">e-ticaret sektör sayfasına</a> bakın.')),
  ('Ödeme ve kargo', P('Müşteriye kredi kartı ve havale gibi tanıdık ödeme yolları sunun. Ödeme altyapısı için yetkili bir ödeme kuruluşu kullanın; kart bilgisini kendiniz saklamayın. Kargo tarafında hangi firmayla çalışacağınızı, gönderim süresini ve ücreti baştan belirleyin. Sipariş ve kargo takibini <a href="/bilgi-siparis-ve-kargo.html">sipariş ve kargo rehberinde</a> anlattık.')),
  ('Yasal bilgiler', P('Çevrimiçi satışta müşteriye gösterilmesi gereken bazı belgeler vardır: mesafeli satış sözleşmesi, iade ve cayma koşulları, gizlilik ve KVKK aydınlatma metni, işletmenin ünvan ve iletişim bilgileri. Gerekli metinlerin kapsamı işinize göre değişir; mali müşavirinize ya da hukuk danışmanınıza kontrol ettirin. Bu yazı hukuki tavsiye değildir.')),
  ('İlk satıştan sonra', P('İlk siparişlerde süreci baştan sona kendiniz izleyin: sipariş nasıl geldi, paketleme ne kadar sürdü, müşteri ürünü nasıl aldı? Aksayan yeri not edip düzeltin. Ardından ürün sayısını, fotoğrafları ve açıklamaları aşama aşama geliştirin. Kurulumdan önce <a href="/demo.html">ücretsiz demoyu</a> deneyip paneli tanımanız mantıklı bir ilk adımdır.'))],
 'Çevrimiçi satışa başlama kontrol listesi',
 ['Neyi, kime, hangi kanaldan satacağım yazılı.', 'İlk ürünler için ad, açıklama ve stok hazır.', 'Kendi çektiğim net fotoğraflar var.', 'Fiyatta kargo, komisyon ve iade payı hesaplandı.', 'Ödeme yöntemleri belirlendi.', 'Kargo firması, süre ve ücret belli.', 'Mesafeli satış, iade ve gizlilik metinleri hazır.', 'İlk siparişi uçtan uca denedim.'],
 [('Çevrimiçi satış için şirket kurmam gerekir mi?', 'Bu, satışınızın niteliğine ve hacmine göre değişir. Vergi ve şirket yapısı için mali müşavirinize danışın; bu sayfa hukuki ya da mali tavsiye değildir.'),
  ('Önce kendi site mi, pazaryeri mi?', 'İkisinin de artısı ve eksisi var. Pazaryeri hazır ziyaretçi, kendi site marka ve müşteri verisi sağlar. Birçok işletme ikisini birlikte kullanır.'),
  ('Kaç ürünle başlamalıyım?', 'Kesin bir sayı yok. Fotoğraf ve açıklaması hazır, stoku belli birkaç ürünle başlayıp sonradan artırabilirsiniz.'),
  ('Kurulum için teknik bilgi gerekir mi?', 'Hazır tema ve panelle teknik bilgi olmadan ürün ekleyip satışa başlanabilir. OnlineKaydet’i 7 gün ücretsiz deneyerek kendiniz görebilirsiniz.')],
 [('/fiyatlar.html', 'Fiyatlar ve paketler'), ('/demo.html', 'Ücretsiz demo'), ('/bilgi-urun-ekleme.html', 'Bilgi bankası: Ürün ekleme'), ('/bilgi-siparis-ve-kargo.html', 'Bilgi bankası: Sipariş ve kargo'), ('/sektor-eticaret.html', 'E-ticaret için yazılım')])

# sitemap
sm = open('sitemap.xml', encoding='utf-8').read(); add = ''
for fn in PAGES:
    u = 'https://onlinekaydet.com/' + fn
    if u not in sm: add += '<url><loc>%s</loc><lastmod>2026-11-24</lastmod></url>\n' % u
if add: open('sitemap.xml', 'w', encoding='utf-8').write(sm.replace('</urlset>', add + '</urlset>'))
print(len(PAGES), 'sayfa')
