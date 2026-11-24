#!/usr/bin/env python3
"""Sektör blog yazıları + blog dizini. Çalıştır: python3 site/gen_blog_sektor.py
Kural: uydurma istatistik/yorum yok; genel, doğrulanabilir tavsiye; görünür telefon metni yok."""
import os, re
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
src = open('gen_seo_karsilastirma.py', encoding='utf-8').read()
exec(compile(src[:src.index('RIV = {')], 'gen_seo_pre', 'exec'))
ACT = '<a class="bt" href="/demo.html">7 gün ücretsiz deneyin</a><a class="bt l" href="tel:05444444004">Hemen arayın</a>'
def cta2(): return cta().replace('>0544 444 40 04</a>', '>Hemen arayın</a>')
P = lambda *x: ''.join('<p>%s</p>' % t for t in x)
L = lambda x: '<ul>%s</ul>' % ''.join('<li>%s</li>' % i for i in x)
def chk(x): return '<ul style="list-style:none;padding-left:0">%s</ul>' % ''.join('<li>&#9744; %s</li>' % i for i in x)
def govde(x): return P(*x) if isinstance(x, (list, tuple)) and x and isinstance(x[0], str) and not x[0].startswith('<ul') else x
OLD = [('blog-servis-fisi-nasil-hazirlanir', 'Servis fişi nasıl hazırlanır?', 'Servis'), ('blog-servis-kaydi-bilgileri', 'Servis kaydı açarken hangi bilgileri almalısınız?', 'Servis'),
       ('blog-servis-kaydi-nasil-tutulur', 'Servis kaydı nasıl tutulur: kâğıt, Excel ve program', 'Servis'), ('blog-servis-takip-programi-nedir', 'Servis takip programı nedir, nasıl seçilir?', 'Servis'),
       ('blog-teknik-servis-musteri-memnuniyeti', 'Teknik serviste müşteri memnuniyeti', 'Servis'), ('blog-randevu-hatirlatma-mesaji', 'Randevu hatırlatma mesajı nasıl yazılır?', 'Randevu'),
       ('blog-online-satisa-baslama-kontrol-listesi', 'Çevrimiçi satışa başlama kontrol listesi', 'E-ticaret')]
# slug, sektör sayfası, sektör adı, kategori, başlık, açıklama, giriş, bölümler, kontrol, sss
POSTS = [
('kuafor-randevu-duzeni', 'sektor-kuafor.html', 'Kuaför', 'Güzellik ve bakım', 'Kuaför ve berber salonunda randevu düzeni nasıl kurulur?',
 'Randevu defteri, WhatsApp ve telefon arasında kaybolan randevulara son. Kuaför ve berber salonu için randevu, hatırlatma ve boşluk yönetimi.',
 'Boş koltuk geliri kaybettirir; çifte rezervasyon ise müşteriyi. İkisini de önleyen şey, randevunun tek bir yerde durmasıdır.',
 [('Randevu tek yerde toplanmalı', ['Telefon, mesaj ve kapıdan gelen randevular farklı yerlere yazıldığında çakışma kaçınılmaz olur. Hangi kanaldan gelirse gelsin her randevuyu aynı takvime işleyin.', 'Takvimde her çalışan için ayrı sütun olması, kimin ne zaman boş olduğunu tek bakışta gösterir.']),
  ('Hizmet süresini baştan tanımlayın', ['Saç kesimi, boya ve fön aynı süreyi almaz. Her hizmete gerçekçi bir süre verirseniz takvim kendi kendine doğru dolar; müşteri beklemez, siz de geç kalmazsınız.', 'Birden fazla hizmet alan müşteri için süreleri toplayın ve tek randevu olarak kaydedin.']),
  ('Hatırlatma mesajı gelmeyenleri azaltır', ['Randevudan bir gün önce kısa bir hatırlatma gitmesi, unutulan randevuları azaltmanın en kolay yoludur. Mesaja iptal ya da erteleme için bir yol eklemek, boşalan saati başka müşteriye vermenizi sağlar.', 'Mesaj örnekleri için <a href="/blog-randevu-hatirlatma-mesaji.html">randevu hatırlatma mesajı</a> yazımıza bakabilirsiniz.']),
  ('Boşlukları görünür tutun', ['İki randevu arasında kalan kısa boşluklar çoğu zaman boşa gider. Takvimi haftalık görünümde izlemek, hangi saatlerin hep boş kaldığını fark etmenizi sağlar; bu saatlere özel bir hizmet ya da fiyat deneyebilirsiniz.']),
  ('Müşteri geçmişini kaydedin', ['Geçen sefer hangi boyanın, hangi oranda kullanıldığı müşteri kaydında durursa kim servis verirse versin sonuç aynı olur. Müşterinin doğum günü ve tercihleri gibi notlar da küçük ama etkili bir ilgi gösterir.'])],
 ['Her çalışan için ayrı takvim sütunu var.', 'Hizmetlerin süreleri tanımlı.', 'Randevu hatırlatma mesajı gidiyor.', 'İptal edilen saat hızla başka müşteriye veriliyor.', 'Müşteri geçmişi kayıtta duruyor.'],
 [('Online randevu için internet sitesi gerekir mi?', 'Siteniz varsa randevu formu doğrudan takvime düşer. OnlineKaydet’te hazır tema üzerinde randevu bölümü bulunur.'), ('Müşteri kendi randevusunu iptal edebilir mi?', 'Hatırlatma mesajına bir iptal bağlantısı eklenebilir; bu, salonun boşalan saati yeniden satmasını kolaylaştırır.'), ('Birden fazla çalışan için tek takvim yeterli mi?', 'Çalışan başına sütun ya da ayrı takvim kullanmak karışıklığı önler.')]),
('lokanta-qr-menu-siparis', 'sektor-lokanta.html', 'Lokanta ve kafe', 'Yeme içme', 'Lokanta ve kafede QR menü ve online sipariş nasıl kurulur?',
 'QR menü ve masadan ya da paket sipariş almak için nelere dikkat edilmeli? Lokanta ve kafe için adım adım kurulum rehberi.',
 'QR menü baskı masrafını ve menü güncelleme derdini ortadan kaldırır; asıl fayda, siparişin düzenli ve doğru gelmesidir.',
 [('Menüyü sadeleştirin', ['Telefon ekranında kısa kategoriler ve net ürün adları daha iyi çalışır. Her ürün için ad, kısa açıklama, fiyat ve mümkünse gerçek bir fotoğraf yeterlidir.', 'Tükenen ürünü menüden anında kapatabilmek, müşteriye olmayan ürün siparişi aldırmamanın en kolay yoludur.']),
  ('QR kodu doğru yere koyun', ['Her masaya masa numaralı bir kart koyarsanız sipariş hangi masadan geldiği bilinerek mutfağa ulaşır. Kapıda ve vitrinde ayrı bir QR ise paket sipariş için işe yarar.', 'Kartın okunaklı, parlamayan ve kolay temizlenir bir yüzeye basıldığından emin olun.']),
  ('Sipariş mutfağa nasıl ulaşıyor?', ['Siparişin kağıda tekrar yazılması hataya yol açar. Siparişin ekrana düşmesi ve durumunun (hazırlanıyor, hazır) takip edilmesi karışıklığı azaltır.', 'Yemek platformlarından gelen siparişler de aynı listeye düşerse tek ekrandan takip edersiniz.']),
  ('Paket sipariş ve teslimat', ['Paket servis yapıyorsanız teslimat alanını, asgari tutarı ve tahmini süreyi baştan yazın. Müşterinin aradığı ilk soru çoğu zaman “ne kadar sürer” olur.']),
  ('Menü fiyatı değişince ne olur?', ['Basılı menüyü yeniden basmak yerine fiyatı panelden bir kez değiştirirsiniz; QR menü ve site aynı anda güncellenir.'])],
 ['Menüde her ürünün adı ve fiyatı güncel.', 'Her masada numaralı QR kart var.', 'Tükenen ürün hızla kapatılabiliyor.', 'Sipariş mutfağa tek ekrandan düşüyor.', 'Paket sipariş için süre ve alan belli.'],
 [('QR menü için uygulama indirmek gerekir mi?', 'Hayır. Müşteri telefon kamerasıyla okutur ve menü tarayıcıda açılır.'), ('Yemek platformu siparişleri nasıl takip edilir?', 'OnlineKaydet’te Yemeksepeti, Trendyol Yemek, Getir Yemek ve Migros Yemek bağlantıları kurulduğunda siparişler aynı listeye düşer.'), ('Menüyü kendim güncelleyebilir miyim?', 'Evet. Ürün, fiyat ve fotoğraf panelden değiştirilir.')]),
('emlak-ilan-yonetimi', 'sektor-emlakci.html', 'Emlak', 'Emlak ve gayrimenkul', 'Emlakçı için ilan ve müşteri takibi: nereden başlamalı?',
 'Emlak ofisinde ilanları, portföyü ve müşteri taleplerini tek yerde tutmanın yolları. Eşleştirme, geri arama ve ilan vitrini.',
 'Emlak işi hatırlamakla yürür: kim hangi daireyi sormuştu, hangi mal sahibi fiyat düşürmeyi kabul etmişti. Kayıt bu yükü hafifletir.',
 [('Portföyü düzenli tutun', ['Her ilan için adres, metrekare, oda sayısı, fiyat, mal sahibi iletişimi ve fotoğraf aynı kayıtta durmalı. Güncel olmayan ilan hem zaman hem güven kaybettirir.', 'Satıldı ya da kiralandı olarak işaretlediğiniz ilanı vitrinden hemen kaldırın.']),
  ('Müşteri talebini kaydedin', ['Arayan müşterinin bütçesini, istediği semti ve oda sayısını yazarsanız yeni ilan geldiğinde kime haber vereceğinizi bilirsiniz.', 'Talebi hatırlamaya bırakmak, en iyi fırsatın yanlış müşteriye gitmesine yol açar.']),
  ('Geri aramayı unutmayın', ['Gösterim sonrası geri aramak satışın en sık atlanan adımıdır. Her görüşmeye bir sonraki adım ve tarih eklemek takibi kolaylaştırır.']),
  ('İlan vitrini ve internet sitesi', ['Kendi sitenizde ilan vitrini olması, ilan portallarına bağımlılığı azaltır ve müşteriyi doğrudan size getirir. Panelden eklediğiniz ilan sitenizde de görünürse aynı bilgiyi iki kez girmezsiniz.', 'Detay için <a href="/bilgi-ilan-ekleme.html">ilan ekleme</a> sayfamıza bakın.']),
  ('Kişisel veriyi koruyun', ['Mal sahibi ve müşteri bilgileri kişisel veridir. Kayıtlara yalnızca yetkili kişilerin erişmesi ve bilgilerin yalnızca iş için kullanılması gerekir; ayrıntı için mali ya da hukuki danışmanınıza başvurun.'])],
 ['Her ilanın bilgileri eksiksiz.', 'Satılan ilan vitrinden kaldırıldı.', 'Müşteri talepleri yazılı.', 'Her görüşmede sonraki adım belli.', 'Kayıtlara yetkisiz erişim yok.'],
 [('İlan portallarını bırakmam gerekir mi?', 'Hayır. Portallar ziyaretçi getirir; kendi siteniz ise müşteriyi doğrudan size bağlar. İkisini birlikte kullanabilirsiniz.'), ('Müşteri talepleriyle ilan eşleştirmesi elle mi yapılır?', 'Kayıtlı bütçe ve istekler üzerinden kendiniz eşleştirirsiniz; kayıt, kimi arayacağınızı hatırlatır.'), ('Fotoğrafları nereye yüklemeliyim?', 'İlanla birlikte panele yüklenir ve sitenizde gösterilir.')]),
('oto-servis-is-emri', 'sektor-oto-servis.html', 'Oto servis', 'Araç ve servis', 'Oto serviste iş emri nasıl düzenlenir?',
 'Araç girişinden teslimata iş emri, parça, işçilik ve müşteri onayı. Oto servis için düzenli kayıt rehberi.',
 'Araç servise girdiğinde aracın durumu, müşterinin talebi ve verilen fiyat yazılı değilse tartışma çıkar. İş emri bu tartışmayı baştan önler.',
 [('Araç teslim alırken', ['Plaka, marka, model, kilometre ve müşterinin şikâyetini yazın. Aracın mevcut hasar ve çizikleri varsa teslim alırken not edin; teslimde yaşanan anlaşmazlıkların çoğu buradan çıkar.']),
  ('İş emrinde neler olmalı?', [L(['Müşteri ve araç bilgisi', 'Bildirilen şikâyet', 'Yapılacak işlemler ve tahmini tutar', 'Kullanılan parça ve işçilik ayrı satırlarda', 'Tahmini teslim tarihi', 'Müşteri onayı ve imza'])]),
  ('Ek iş çıkarsa müşteriye sorun', ['İş sırasında yeni bir arıza bulunursa müşteriyi arayıp onay almadan ekleme yapmayın. Onayı iş emrine tarih ve saatle yazmak ileride yaşanacak itirazları azaltır.']),
  ('Parça ve stok takibi', ['Kullanılan parçaların iş emrine yazılması stoğu kendiliğinden azaltır. Sık kullanılan filtre, balata gibi parçaların asgari miktarını belirlerseniz bitmeden sipariş edersiniz.']),
  ('Araç geçmişi', ['Aynı plakaya daha önce yapılan işlerin görünmesi, müşteriye “geçen sefer şunu değiştirmiştik” diyebilmenizi sağlar ve bakım hatırlatması için zemin hazırlar.'])],
 ['Teslimde mevcut hasar yazıldı.', 'Şikâyet müşterinin sözleriyle kayıtlı.', 'Tahmini tutar müşteriye söylendi.', 'Ek işler onayla eklendi.', 'Teslim sonrası araç geçmişine işlendi.'],
 [('İş emri müşteriye imzalatılmalı mı?', 'İmza, anlaşılan işin ve tutarın yazılı kaydıdır; anlaşmazlıkları azaltır. Yasal gereklilikler için mali müşavirinize danışın.'), ('Bakım hatırlatması yapılabilir mi?', 'Araç geçmişi kayıtlıysa bir sonraki bakım için müşteriye hatırlatma gönderebilirsiniz.'), ('Parçalar stoğa nasıl yansır?', 'İş emrine yazılan parça stoktan düşer.')]),
('lastikci-saklama-ve-randevu', 'sektor-lastikci.html', 'Lastikçi', 'Araç ve servis', 'Lastikçide sezonluk lastik saklama ve randevu takibi',
 'Kış ve yaz lastiği değişim sezonunda yığılmayı azaltmak için saklama kaydı, randevu ve hatırlatma düzeni.',
 'Sezon değişiminde kapı önünde kuyruk oluşur. Önceden kayıt ve hatırlatma, bu yoğunluğu güne yaymanın en pratik yoludur.',
 [('Saklanan lastiği kayda geçirin', ['Plaka, lastik markası, ebadı ve raf numarasını kaydedin. Müşteri geldiğinde lastiğini dakikalar içinde bulmak hem zaman kazandırır hem güven verir.']),
  ('Sezondan önce hatırlatma gönderin', ['Mevsim değişiminden önce kayıtlı müşterilere kısa bir mesaj göndermek randevuyu erkene çeker. Mesajda randevu almanın yolunu belirtin.']),
  ('Randevuyu saat aralıklarına bölün', ['Her işin süresini belirleyip gün içine eşit dağıtırsanız yoğunluk tek bir saate yığılmaz. Randevusuz gelenler için ayrı bir pencere ayırabilirsiniz.']),
  ('Diş derinliği ve durum notu', ['Lastik teslim alırken görsel durumunu not edin. Değişim önerisini kayda dayandırırsanız müşteri kararını daha rahat verir.']),
  ('Tahsilat ve fiş', ['İşçilik, balans ve saklama ücretini ayrı satırlarda gösteren bir fiş, müşterinin ne için ödediğini net anlamasını sağlar.'])],
 ['Saklanan lastikler raf numarasıyla kayıtlı.', 'Sezondan önce hatırlatma gönderildi.', 'Randevu saatleri güne yayıldı.', 'Teslimde lastik durumu not edildi.', 'Fişte işlemler ayrı satırlarda.'],
 [('Saklama ücreti nasıl takip edilir?', 'Kayıt üzerinde saklama süresi ve ücret tutulabilir, süre dolunca müşteriye hatırlatma yapılabilir.'), ('Randevusuz müşteri ne olacak?', 'Gün içinde randevusuz gelenler için ayrı bir saat penceresi bırakılabilir.'), ('Müşteriye mesaj nasıl gider?', 'SMS ya da WhatsApp ile hatırlatma gönderilebilir.')]),
('temizlik-sirketi-is-planlama', 'sektor-temizlik.html', 'Temizlik', 'Ev ve yaşam hizmetleri', 'Temizlik şirketinde iş planlama ve ekip takibi',
 'Ev ve ofis temizliğinde randevu, ekip atama, abonelik ve tahsilat takibi nasıl düzenlenir?',
 'Temizlik işinde sorun genellikle iş yapmakta değil, işi doğru saate doğru ekibe vermektedir.',
 [('İş türüne göre süre tanımlayın', ['Standart ev temizliği, taşınma sonrası ve ofis temizliği aynı süreyi almaz. Her tür için metrekareye bağlı bir süre belirlerseniz ekip planı kendiliğinden oturur.']),
  ('Ekibi bölgeye göre atayın', ['Aynı gün içinde birbirine yakın adreslere aynı ekibi vermek yol süresini azaltır. Takvimde her ekibin gününü görmek çifte atamayı önler.']),
  ('Düzenli müşteriler için tekrar eden iş', ['Haftalık ya da iki haftalık müşterileri tekrar eden iş olarak tanımlayın. Her seferinde yeniden randevu girmek hem zaman alır hem unutulmaya açıktır.']),
  ('İş sonrası onay', ['İş bitince müşteriden kısa bir onay almak ve gerekirse fotoğraf not etmek, sonradan çıkabilecek itirazları azaltır.']),
  ('Tahsilat takibi', ['Kimin ödemesi alındı, kimin bekliyor sorusunun cevabı kayıtta olmalı. Aylık anlaşmalı müşterilerde vade tarihini yazın.'])],
 ['İş türlerinin süreleri tanımlı.', 'Ekipler bölgeye göre atanıyor.', 'Düzenli müşteriler tekrar eden iş.', 'İş sonrası onay alınıyor.', 'Tahsilat durumu kayıtta.'],
 [('Ekip takvimi nasıl tutulur?', 'Her ekip için ayrı takvim, çifte atamayı önler.'), ('Aylık sözleşmeli müşteri nasıl izlenir?', 'Tekrar eden iş ve vade tarihi ile.'), ('Müşteriye bilgilendirme gider mi?', 'Randevu ve ekip bilgisi mesajla iletilebilir.')]),
('hali-yikama-teslim-takibi', 'sektor-hali-yikama.html', 'Halı yıkama', 'Ev ve yaşam hizmetleri', 'Halı yıkamada teslim alma ve teslim etme takibi',
 'Halının evden alınmasından teslimine kadar etiket, durum ve tahsilat takibi. Karışıklığı önleyen düzen.',
 'Halı yıkamada en büyük risk karışıklıktır: yanlış eve giden halı güven kaybettirir. Etiket ve kayıt bu riski kapatır.',
 [('Her halıya numara verin', ['Teslim alınan her halıya numaralı bir etiket takın ve aynı numarayı kayda yazın. Müşteri adı, ölçü ve varsa özel durum (leke, yırtık) kayıtta olmalı.']),
  ('Ölçü ve fiyat', ['Fiyat metrekareye göre hesaplanıyorsa ölçüyü teslim alırken ölçüp kayda yazın. Hesap müşteriye gösterilirse itiraz azalır.']),
  ('Durum takibi', ['Alındı, yıkamada, kurutmada, hazır ve teslim edildi gibi birkaç durum yeterlidir. Müşteri “halım hazır mı” diye aradığında cevabı kayıttan saniyeler içinde verirsiniz.']),
  ('Hazır olunca haber verin', ['Halı hazır olduğunda müşteriye mesaj göndermek, teslim gününü netleştirir ve deponuzda bekleyen halı sayısını düşürür.']),
  ('Servis ve tahsilat', ['Evden alma ve teslim için adres, gün ve saat aralığını kaydedin. Tahsilat kapıda ya da sonradan olabilir; hangisi olduğunu kayda yazın.'])],
 ['Her halıda numaralı etiket var.', 'Ölçü ve fiyat müşteriye gösterildi.', 'Durum kayıtta güncel.', 'Hazır halı için mesaj gönderildi.', 'Tahsilat şekli kayıtlı.'],
 [('Etiket nasıl basılır?', 'OnlineKaydet’te etiket tasarımı ve QR etiket seçenekleri vardır.'), ('Müşteri halısının durumunu görebilir mi?', 'Durum kayıtta tutulur, müşteriye mesajla bildirilebilir.'), ('Servis günü nasıl planlanır?', 'Alma ve teslim işleri takvimde saat aralığıyla planlanır.')]),
('spor-salonu-uyelik-takibi', 'sektor-spor-salonu.html', 'Spor salonu', 'Spor ve sağlıklı yaşam', 'Spor salonunda üyelik ve yenileme takibi nasıl yapılır?',
 'Üyelik bitiş tarihi, ödeme ve yenileme hatırlatması: spor salonunda üyeyi kaybetmeden büyütmenin yolu.',
 'Salonlarda gelir, yeni üyeden çok yenileyen üyeden gelir. Bitiş tarihini kaçırmamak bu yüzden önemlidir.',
 [('Üyelik kaydında neler olmalı?', [L(['Ad, telefon', 'Üyelik türü ve süresi', 'Başlangıç ve bitiş tarihi', 'Ödeme durumu ve tutarı', 'Varsa dondurma kaydı'])]),
  ('Bitişten önce hatırlatın', ['Üyeliği bitmeden bir hafta önce kısa bir mesaj göndermek yenilemeyi kolaylaştırır. Mesajda yenileme için nasıl bir yol izleneceğini yazın.']),
  ('Dondurma ve uzatma', ['Üyelik dondurma taleplerini yazılı kayda geçirin ve bitiş tarihini buna göre kaydırın. Kural net değilse tartışma çıkar; kuralı salon girişinde ve sözleşmede açıkça belirtin.']),
  ('Ders ve randevu', ['Grup dersi ya da özel antrenör randevusu veriyorsanız kontenjan ve randevu takvimini ayrı tutun. Dolu dersin listesini görmek, bekleme listesi oluşturmanıza yardım eder.']),
  ('Tahsilat takibi', ['Taksitli ödemelerde vade günlerini kayıtta tutun; kimin ödemesinin geciktiğini her sabah tek listede görmek, geç tahsilatı azaltır.'])],
 ['Her üyenin bitiş tarihi kayıtlı.', 'Bitişten önce hatırlatma gidiyor.', 'Dondurma kuralı yazılı.', 'Ders kontenjanı takip ediliyor.', 'Geciken ödemeler listede görünüyor.'],
 [('Üyelik hatırlatması nasıl gider?', 'SMS ya da WhatsApp ile, bitişten önce.'), ('Taksit takibi yapılabilir mi?', 'Vade tarihleri kayıtta tutulur, geciken ödemeler listelenir.'), ('Ders randevusu alınabilir mi?', 'Takvim üzerinden randevu ve kontenjan takibi yapılır.')]),
('guzellik-merkezi-paket-seans', 'sektor-guzellik.html', 'Güzellik merkezi', 'Güzellik ve bakım', 'Güzellik merkezinde paket ve seans takibi',
 'Çok seanslı paket satan güzellik merkezlerinde kalan seans, randevu ve ödeme takibi nasıl yapılır?',
 'Paket satışı güvene dayanır. Müşteri kaç seansı kaldığını sorduğunda cevabı hemen verebilmek bu güveni pekiştirir.',
 [('Paketi seanslarıyla kaydedin', ['Paket adı, toplam seans, kullanılan seans ve kalan seans kayıtta açıkça görünmeli. Her gelişte bir seans düşmesi, elle sayma hatasını önler.']),
  ('Seanslar arası süreyi takvime işleyin', ['Bazı işlemler arasında belirli bir bekleme süresi gerekir. İşlem sonunda bir sonraki randevuyu hemen vermek hem müşteriyi hem sizi planlı tutar.']),
  ('Ödeme planı', ['Peşin ya da taksitli ödemeyi kayda yazın. Kalan tutarın ve vadenin görünmesi, tahsilatı unutmanızı önler.']),
  ('Onam ve notlar', ['Cilt tipi, alerji gibi önemli notlar ve müşteri onayı kayıtta durmalı. Sağlıkla ilgili hassas bilgiler için kişisel veri kurallarına uygun davranın.']),
  ('Hatırlatma ve ilgi', ['Seansı olan müşteriye bir gün önce mesaj gönderin. Paketi biten müşteriye yenileme önerisi yapmak için kayıt size zamanı gösterir.'])],
 ['Her paketin kalan seansı görünüyor.', 'Bir sonraki randevu seans sonunda veriliyor.', 'Ödeme planı kayıtlı.', 'Önemli notlar ve onam kayıtta.', 'Seans hatırlatması gidiyor.'],
 [('Kalan seans nasıl takip edilir?', 'Paket kaydında kullanılan ve kalan seans tutulur.'), ('Hassas bilgi saklamak güvenli mi?', 'Yalnızca gerekli bilgiyi ve yalnızca yetkili kişilerin erişebileceği şekilde saklayın.'), ('Müşteriye hatırlatma gider mi?', 'Evet, randevu öncesi mesaj gönderilebilir.')]),
('dis-klinigi-randevu-ve-hasta-kaydi', 'sektor-dis-klinigi.html', 'Diş kliniği', 'Sağlık', 'Diş kliniğinde randevu ve hasta kaydı düzeni',
 'Muayene randevusu, tedavi planı ve hatırlatma. Diş kliniğinde hasta kaydının düzenli tutulması için pratik öneriler.',
 'Kliniklerde boş kalan randevu koltuk süresi demektir. Hatırlatma ve düzenli kayıt, bu kaybı azaltmanın temel yoludur.',
 [('Randevu süresi işleme göre', ['Muayene, dolgu ve kanal tedavisi farklı süreler ister. İşlem türüne göre süre tanımlayıp takvimi buna göre kurmak gecikmeyi azaltır.']),
  ('Tedavi planı ve seanslar', ['Birden fazla seans gerektiren tedavilerde plan ve sıradaki randevu kayıtta durmalı. Hastaya bir sonraki adımı randevu çıkışında vermek takibi kolaylaştırır.']),
  ('Hatırlatma', ['Randevudan önce mesaj gönderilmesi boş kalan randevuları azaltır. İptal için bir yol bırakmak, boşalan saatin başka hastaya verilmesine imkân tanır.']),
  ('Ödeme ve tedavi geçmişi', ['Yapılan işlem ve alınan ödeme hasta kaydında görünmeli. Taksitli tedavilerde kalan tutarı kayıttan izlemek tahsilatı kolaylaştırır.']),
  ('Veri güvenliği', ['Sağlık verisi özel nitelikli kişisel veridir. Hasta kayıtlarına yetkisiz erişimi engelleyin ve saklama yükümlülükleri için ilgili mevzuata ve uzmanlara danışın.'])],
 ['İşlem süreleri tanımlı.', 'Tedavi planı kayıtta.', 'Randevu hatırlatması gidiyor.', 'Ödeme ve işlem geçmişi görünüyor.', 'Kayıtlara yalnızca yetkililer erişiyor.'],
 [('Hastaya hatırlatma nasıl gider?', 'SMS ya da WhatsApp ile randevu öncesi.'), ('Sağlık verisi nasıl korunmalı?', 'Erişim yetkilendirilmeli; mevzuat ve uzman görüşüne göre hareket edilmeli.'), ('Tedavi planı kayda yazılır mı?', 'Evet, plan ve seanslar hasta kaydında tutulur.')]),
('nakliyat-teklif-ve-is-takibi', 'sektor-nakliye.html', 'Nakliyat', 'Taşıma ve lojistik', 'Nakliyatta teklif, keşif ve iş günü takibi',
 'Evden eve nakliyatta keşif, teklif, ekip ve taşıma günü nasıl düzenlenir? Müşteriyle yazılı anlaşmanın önemi.',
 'Nakliyatta sorunların çoğu, neyin taşınacağının ve fiyatın baştan net yazılmamasından çıkar.',
 [('Keşif ve eşya listesi', ['Mümkünse yerinde ya da görüntülü keşif yapın ve taşınacak eşyaları listeleyin. Liste, fiyat teklifinin dayanağıdır ve taşıma gününde kontrol için kullanılır.']),
  ('Yazılı teklif', ['Fiyatın neleri içerdiğini yazın: paketleme, kat durumu, asansör, sigorta. Dahil olmayan şeyi baştan söylemek, taşıma günü tartışmayı önler.']),
  ('Ekip ve araç planı', ['Hangi gün hangi ekip ve aracın nerede olduğunu takvimde görün. Aynı gün birden fazla iş varsa süre tahminini gerçekçi tutun.']),
  ('Taşıma günü kontrol', ['Yüklemeden önce ve boşaltmadan sonra eşya listesini birlikte kontrol edin; hasar ya da eksik varsa o an not edin.']),
  ('Tahsilat', ['Kapora ve kalan tutarı kayıtta ayrı tutun. Teslimde kalan tutarı alınca kayda işleyin.'])],
 ['Keşif yapıldı, eşya listesi var.', 'Teklif yazılı ve kapsamı net.', 'Ekip ve araç takvimde.', 'Yükleme ve teslimde liste kontrol edildi.', 'Kapora ve kalan tutar kayıtlı.'],
 [('Teklif müşteriye nasıl gider?', 'Yazılı teklif PDF olarak iletilebilir.'), ('Birden fazla ekip nasıl yönetilir?', 'Her ekip için takvimde ayrı iş görünümü kullanılır.'), ('Kapora takibi yapılır mı?', 'Evet, kapora ve kalan tutar ayrı izlenir.')]),
('veteriner-hasta-ve-asi-takvimi', 'sektor-veteriner.html', 'Veteriner', 'Sağlık', 'Veteriner kliniğinde hasta kaydı ve aşı takvimi',
 'Evcil hayvan sahiplerine aşı ve kontrol hatırlatması gönderen düzenli bir veteriner kaydı nasıl kurulur?',
 'Aşı ve kontrol takvimi, veteriner kliniğinde düzenli müşteri getirir; unutan sahibini hatırlatmak hem hayvanın hem klinik için faydalıdır.',
 [('Hayvan ve sahip kaydı', ['Hayvanın adı, türü, ırkı, doğum tarihi ve sahibi aynı kayıtta durmalı. Bir sahibin birden fazla hayvanı olabilir; her biri ayrı kayıt olmalı.']),
  ('Aşı ve işlem geçmişi', ['Yapılan aşı, ilaç ve muayene tarihleri kayıtta görünür olursa bir sonraki tarihi doğru belirleyebilirsiniz.']),
  ('Hatırlatma gönderin', ['Bir sonraki aşı tarihinden önce sahibine mesaj göndermek, hem hayvanın korunmasını hem kliniğe geri dönüşü sağlar.']),
  ('Randevu ve acil durum', ['Rutin işler için randevu verin; acil gelenler için takvimde esneklik bırakın.']),
  ('Ödeme ve ürün satışı', ['Muayene, ilaç ve mama satışını aynı kayıttan yapmak kasayı sadeleştirir.'])],
 ['Her hayvan ayrı kayıtta.', 'Aşı ve işlem geçmişi görünüyor.', 'Bir sonraki aşı için hatırlatma gidiyor.', 'Acil için takvimde esneklik var.', 'Ödeme aynı kayıttan alınıyor.'],
 [('Aşı hatırlatması otomatik gider mi?', 'Bir sonraki tarih kayıtlıysa mesajla hatırlatma gönderilebilir.'), ('Bir sahibin birden fazla hayvanı olabilir mi?', 'Evet, her hayvan ayrı kayıt olarak tutulur.'), ('Mama ve ilaç satışı kaydedilir mi?', 'Evet, satışlar kasaya işlenir.')]),
('fotografci-cekim-ve-teslim-takibi', 'sektor-fotografci.html', 'Fotoğrafçı', 'Yaratıcı hizmetler', 'Fotoğrafçıda çekim planı, sözleşme ve teslim takibi',
 'Düğün, nişan ve stüdyo çekimlerinde tarih, paket, kapora ve albüm teslimini düzenleyen basit bir iş akışı.',
 'Fotoğrafçıda iş çekimle bitmez; seçim, rötuş ve teslim haftalar sürebilir. Bu süreci kayıtsız yürütmek karışıklık getirir.',
 [('Paketi ve kapsamı yazın', ['Kaç saat çekim, kaç kare, albüm ve teslim süresi gibi şartları yazılı paket olarak sunun. Müşteri neyi aldığını bilirse beklenti tutar.']),
  ('Tarih ve kapora', ['Çekim tarihini takvime işleyin ve kaporayı kayda yazın. Aynı gün için ikinci bir iş almamak, çifte rezervasyonu önler.']),
  ('İş akışı durumları', ['Çekildi, seçim bekliyor, rötuşta, baskıda, teslim edildi gibi durumlar iş yüküne bakışı kolaylaştırır.']),
  ('Teslim ve onay', ['Teslim tarihini baştan söyleyin ve gecikme olacaksa müşteriyi önceden bilgilendirin. Teslimde müşterinin onayını kayda alın.']),
  ('Portfolyo ve site', ['İyi bir çalışma örneği sitesi yeni müşteri getirir. Müşteri izniyle seçilmiş işleri sitede göstermek en etkili tanıtımdır.'])],
 ['Paket kapsamı yazılı.', 'Çekim tarihi takvimde, kapora kayıtlı.', 'İş durumu güncel.', 'Teslim tarihi müşteriye söylendi.', 'Portfolyoda yalnızca izinli işler var.'],
 [('Müşteri fotoğraflarını sitede göstermek serbest mi?', 'Müşterinin açık izni olmadan yayınlamayın.'), ('Kapora takibi nasıl yapılır?', 'Kayıtta kapora ve kalan tutar ayrı tutulur.'), ('Teslim durumu nasıl izlenir?', 'İş akışı durumlarıyla.')]),
('surucu-kursu-kursiyer-takibi', 'sektor-surucu-kursu.html', 'Sürücü kursu', 'Eğitim', 'Sürücü kursunda kursiyer, direksiyon ve ödeme takibi',
 'Direksiyon dersi randevusu, kursiyer evrakı ve taksit takibi: sürücü kursu için düzenli kayıt.',
 'Sürücü kursunda yoğunluk direksiyon takviminde yaşanır; kimin ne zaman ders aldığı net olmazsa randevular çakışır.',
 [('Kursiyer kaydı', ['Ad, telefon, sınıf ve evrak durumunu tek kayıtta tutun. Eksik evrak listesi kursiyeri aramanız gereken konuları net gösterir.']),
  ('Direksiyon takvimi', ['Her eğitmen ve araç için ayrı takvim tutun. Kursiyer ders sayısı ve kalan ders görünürse planlama kolaylaşır.']),
  ('Sınav takibi', ['Sınav tarihlerini ve sonucunu kayda yazın. Kalan hakkı görünen kursiyere zamanında hatırlatma yapabilirsiniz.']),
  ('Taksit ve tahsilat', ['Vade günleri kayıtta olursa geciken ödeme listesi her sabah elinizde olur.']),
  ('Hatırlatma', ['Ders ve sınav öncesi mesaj, gelmeyen kursiyer sayısını azaltır.'])],
 ['Evrak durumu kayıtta.', 'Eğitmen ve araç takvimi ayrı.', 'Sınav hakkı izleniyor.', 'Taksit vadeleri görünüyor.', 'Ders öncesi hatırlatma gidiyor.'],
 [('Eğitmen takvimi nasıl tutulur?', 'Her eğitmen ve araç için ayrı takvim.'), ('Taksit takibi yapılabilir mi?', 'Evet, vade günleriyle.'), ('Kursiyere mesaj gider mi?', 'Ders ve sınav öncesi mesaj gönderilebilir.')]),
('cicekci-online-siparis', 'sektor-cicekci.html', 'Çiçekçi', 'Perakende', 'Çiçekçide online sipariş ve teslimat günü yönetimi',
 'Sevgililer Günü ve Anneler Günü gibi yoğun günlerde teslimat saati, hediye notu ve stok yönetimi.',
 'Çiçekte zaman her şeydir: sipariş doğru gün ve saatte doğru adrese ulaşmazsa ürünün anlamı kalmaz.',
 [('Teslimat günü ve saati', ['Müşterinin gün ve saat aralığı seçebilmesi, hem müşteri beklentisini hem teslimat planınızı netleştirir. Yoğun günlerde bir günlük kapasiteyi sınırlamak kaliteyi korur.']),
  ('Hediye notu ve paketleme', ['Hediye notu ve özel paket seçeneği çiçekçide sık istenir. Sipariş ekranında not alanı olması, kartı elle yazma hatasını azaltır.']),
  ('Stok ve mevsim', ['Taze ürünün stoğu hızlı değişir. Bitmiş ürünü mağazadan kapatmak olmayan siparişi önler.']),
  ('Yoğun gün hazırlığı', ['Özel günlerden önce sık satılan ürünler için stok ve kurye planı yapın; sipariş kapanış saatini sitede açıkça yazın.']),
  ('Sepeti terk eden müşteri', ['Sepetini bırakan müşteriye kısa bir hatırlatma göndermek, özel gün yaklaşırken kaybolan satışları geri getirebilir.'])],
 ['Teslimat gün ve saati seçilebiliyor.', 'Hediye notu sipariş ekranında.', 'Biten ürün kapatılıyor.', 'Yoğun gün kapasitesi belirlendi.', 'Sepet hatırlatması açık.'],
 [('Teslimat saati seçtirilebilir mi?', 'OnlineKaydet mağazasında teslimat günü ve saat aralığı seçeneği vardır.'), ('Hediye notu eklenebilir mi?', 'Evet, hediye paketi ve not alanı bulunur.'), ('Sepet hatırlatması nasıl çalışır?', 'WhatsApp ya da SMS ile, isteğe bağlı kuponla.')]),
('giyim-magazasi-eticaret', 'sektor-tekstil.html', 'Giyim ve tekstil', 'Perakende', 'Giyim mağazası için e-ticaret: beden, stok ve iade',
 'Beden ve renk varyantı, stok takibi ve iade yönetimi: giyim mağazasının internette satışa başlama rehberi.',
 'Giyimde en sık iade sebebi bedendir. Net ölçü bilgisi ve doğru stok, hem iadeyi hem yanlış sipariş yükünü azaltır.',
 [('Varyantları doğru kurun', ['Renk ve beden kombinasyonlarını ayrı stokla tanımlayın. Müşteri seçtiği bedenin stokta olduğunu görmeli.']),
  ('Beden tablosu ve ölçü', ['Ürün sayfasında ölçü tablosu bulunması iade oranını düşürmenin en kolay yoludur. Manken ölçülerini ve ürün ölçülerini ayrı yazın.']),
  ('Fotoğraf', ['Aynı ürünün ön, arka ve detay fotoğrafı güveni artırır. Kendi çektiğiniz net fotoğraflar kullanın.']),
  ('İade ve değişim', ['İade koşullarını açıkça yazın ve yasal sürelere uyun. Hangi ürünün iade edilemeyeceğini (örneğin iç giyim) baştan belirtin.']),
  ('Kampanya ve sezon', ['Sezon sonu için X al Y öde, sepet indirimi ve kupon gibi araçlar kullanabilirsiniz. Her kampanyanın bitiş tarihini yazın.'])],
 ['Renk ve beden stokları ayrı.', 'Ölçü tablosu var.', 'Her üründe birden çok fotoğraf.', 'İade koşulları açık.', 'Kampanya bitiş tarihleri belli.'],
 [('Beden stoku nasıl takip edilir?', 'Her renk ve beden kombinasyonu ayrı stokla tanımlanır.'), ('Toplu ürün yüklenebilir mi?', 'Excel ya da XML ile toplu ürün aktarımı yapılabilir.'), ('Pazaryerine ürün gönderilir mi?', 'Pazaryeri bağlantısı panelden kurulur.')]),
('ozel-ders-ogrenci-ve-ders-takibi', 'sektor-ozel-ders.html', 'Özel ders ve kurs', 'Eğitim', 'Özel ders ve etüt merkezinde öğrenci ve ders takibi',
 'Ders programı, devamsızlık ve veli bilgilendirmesi: özel ders ve etüt merkezi için düzenli kayıt.',
 'Velinin sorduğu ilk şey öğrencisinin nasıl ilerlediği olur. Düzenli kayıt bu soruyu kolayca yanıtlar.',
 [('Öğrenci ve veli kaydı', ['Öğrenci bilgisi, sınıf, veli iletişimi ve alınan ders kayıtta durmalı. Reşit olmayan öğrencilerin verileri için özellikle dikkatli olun.']),
  ('Ders programı', ['Hangi öğretmen hangi gün hangi öğrenciyle çalışıyor sorusunun cevabı takvimde görünmeli. Telafi dersi için boş saatleri işaretleyin.']),
  ('Devam takibi', ['Gelen ve gelmeyen öğrenciyi kayda alın. Üst üste devamsızlıkta veliye haber vermek hem öğrenciyi hem düzeninizi korur.']),
  ('Veli bilgilendirmesi', ['Kısa dönemlik ilerleme notu velinin güvenini artırır. Mesaj kısa ve somut olmalı.']),
  ('Ödeme', ['Aylık ücret ve vadeyi kayda yazın; geciken ödeme listesini düzenli kontrol edin.'])],
 ['Öğrenci ve veli bilgisi kayıtta.', 'Ders programı takvimde.', 'Devamsızlık işleniyor.', 'Veliye düzenli bilgi gidiyor.', 'Aylık ödemeler izleniyor.'],
 [('Veliye mesaj gönderilebilir mi?', 'SMS ya da WhatsApp ile bilgilendirme yapılabilir.'), ('Öğrenci verisi nasıl korunur?', 'Yetkisiz erişimi engelleyin; çocukların verileri için ek özen gösterin.'), ('Telafi dersi nasıl planlanır?', 'Takvimde boş saat işaretlenerek.')]),
]
import html as _h
PAGES = []
def yaz(sl, sektor_sf, sektor, kat, title, desc, lead, bol, kontrol, sss):
    fn = 'blog-%s.html' % sl
    bolumler = [(t, govde(i if isinstance(i, str) else i)) for t, i in bol]
    govdeler = []
    for n, (t, i) in enumerate(bol):
        govdeler.append(sec(t, ''.join(x if x.startswith('<ul') else '<p>%s</p>' % x for x in i), tint=(n % 2 == 1)))
    links = [('/demo.html', '7 gün ücretsiz demo'), ('/' + sektor_sf, sektor + ' için OnlineKaydet'), ('/fiyatlar.html', 'Fiyatlar ve paketler'), ('/blog.html', 'Tüm blog yazıları')]
    body = STIL + ''.join(govdeler) + sec(sektor + ' için kontrol listesi', chk(kontrol)) + faq('Sık sorulan sorular', sss) \
        + sec('İlgili sayfalar', L(['<a href="%s">%s</a>' % l for l in links]), tint=True) + cta2()
    page(fn, title + ' | OnlineKaydet', desc, 'Blog', title, lead, body, acts=ACT, ld=faq_ld(sss)); PAGES.append(fn)
    h = open(fn, encoding='utf-8').read(); h = re.sub(r'<script type="application/ld\+json" data-zen>.*?</script>', '', h, flags=re.S)
    open(fn, 'w', encoding='utf-8').write(h)
for p in POSTS: yaz(*p)
# dizin
kats = {}
for sl, sf, sk, kat, t, d, *_ in POSTS: kats.setdefault(kat, []).append(('blog-%s.html' % sl, t, d))
for sl, t, k in OLD: kats.setdefault(k, []).append((sl + '.html', t, ''))
cards = ''
for kat, items in kats.items():
    cards += '<h2 style="margin:34px 0 12px;font-size:22px">%s</h2><div class="blg">%s</div>' % (kat, ''.join(
        '<a class="bl" href="/%s"><b>%s</b>%s<span class="go">Oku →</span></a>' % (f, t, '<p>%s</p>' % d if d else '') for f, t, d in items))
page('blog.html', 'Blog: küçük işletmeler için sektör rehberleri | OnlineKaydet',
     'Kuaför, lokanta, emlak, oto servis, güzellik, eğitim ve daha fazla sektör için randevu, kayıt, sipariş ve tahsilat rehberleri.', 'Blog',
     'Küçük işletmeler için rehberler', 'Randevu, kayıt, sipariş ve tahsilat üzerine kısa, uygulanabilir yazılar. Sektörünüzü seçin.',
     '<style>.blg{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;max-width:none!important;gap:20px}@media(max-width:900px){.blg{grid-template-columns:1fr!important}}</style><section><div class="w">%s</div></section>' % cards + cta2(), acts=ACT)
sm = open('sitemap.xml', encoding='utf-8').read(); add = ''
for fn in PAGES:
    u = 'https://onlinekaydet.com/' + fn
    if u not in sm: add += '<url><loc>%s</loc><lastmod>2026-11-24</lastmod></url>\n' % u
if add: open('sitemap.xml', 'w', encoding='utf-8').write(sm.replace('</urlset>', add + '</urlset>'))
print(len(PAGES), 'yazı')
