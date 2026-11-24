# -*- coding: utf-8 -*-
"""gen_ek_sayfalar.py için zengin metinler (genel bilgi; ürün özelliği iddiası yok)."""
EK = {
'pos': dict(
 neden=['Müşteri kartla ödemek ister; siz de her ödemede banka havalesi ya da nakit beklemek zorunda kalmazsınız.',
        'Web sitenizden ya da gönderdiğiniz ödeme bağlantısından, mesai saati dışında da tahsilat alabilirsiniz.',
        'Ödeme sipariş kaydına bağlanır; hangi siparişin ödendiğini ayrı ayrı aramazsınız.'],
 hazirlik=['Şirket ya da şahıs bilgileriniz, vergi levhası ve IBAN gibi belgeler: ödeme kuruluşu başvuruda ister.', 'Kuruluşun test (deneme) anahtarları: ilk denemeyi gerçek kartla yapmayın.', 'Hangi taksit seçeneklerini sunacağınıza karar verin.', 'İade ve iptal sürecini ödeme kuruluşunun şartlarından okuyun.'],
 hata=['Test anahtarıyla canlıya geçmek ya da canlı anahtarı test ortamına girmek.', 'Gizli anahtarı e-postayla ya da mesajla göndermek.', 'Tutar ve para birimi kontrolü yapmadan ilk gerçek ödemeyi almak.', 'Komisyonu hesaba katmadan fiyat belirlemek.'],
 olcut=['Komisyon oranı ve taksitlerde ek ücret.', 'Paranın hesabınıza yatış süresi.', 'İade ve iptal koşulları.', 'Başvuru ve onay süresi.', 'Destek kanalı ve ulaşılabilirlik.'],
 sss=[('Test ortamı ile canlı ortam farkı nedir?', 'Test ortamında gerçek para çekilmez; ödeme akışını denemek içindir. Canlı ortamda gerçek kartlardan tahsilat yapılır. Panelde ortam seçimi bu yüzden ayrıdır.'),
      ('3D Secure zorunlu mu?', 'Kartlı internet ödemelerinde bankanın ek doğrulaması yaygındır. Uygulaması bankaya ve ödeme kuruluşuna bağlıdır.'),
      ('Havale seçeneğini de gösterebilir miyim?', 'Evet. Havale / EFT ve kapıda ödeme listede ayrı seçenekler olarak yer alır.')]),
'kargo': dict(
 neden=['Gönderi için her seferinde kargo firmasının sitesine girip bilgi yeniden yazmazsınız.', 'Barkod ve takip numarası sipariş kaydında durur.', 'Birden çok firmayla çalışıyorsanız tek ekrandan yönetirsiniz.'],
 hazirlik=['Kargo firmasıyla yapılmış bir anlaşma ya da müşteri hesabı.', 'Firmanın size verdiği kullanıcı adı, şifre ya da anahtar bilgisi.', 'Gönderici adresi ve iletişim bilginiz.', 'Ürünlerin ağırlık ve desi bilgisi.'],
 hata=['Anlaşma bilgisinde eski şifreyi kullanmak.', 'Adres ve telefon alanlarını eksik bırakıp gönderi oluşturmak.', 'Desi hesabını yanlış yapıp fiyat farkıyla karşılaşmak.', 'Test etmeden toplu gönderi başlatmak.'],
 olcut=['Fiyat ve desi hesabı.', 'Teslimat süresi ve kapsama alanı.', 'Kapıda ödeme ve iade gönderisi desteği.', 'Hasar ve kayıp durumunda süreç.', 'Müşteri hizmetlerine ulaşılabilirlik.'],
 sss=[('Desi nedir, nasıl hesaplanır?', 'Desi, ürünün hacmine göre hesaplanan kargo birimidir. Hesaplama için sitemizdeki desi hesaplama aracını kullanabilirsiniz.'),
      ('Kapıda ödemeli gönderi yapabilir miyim?', 'Kapıda ödeme seçeneği sipariş tarafında ayrı bir ödeme yöntemidir; kargo firmanızın bu hizmeti sunup sunmadığını anlaşmanızdan kontrol edin.'),
      ('Birden çok kargo firması bağlayabilir miyim?', 'Evet. Listedeki firmaları ayrı ayrı bağlar, gönderiye göre seçersiniz.')]),
'efatura': dict(
 neden=['Satış kaydı ile fatura ayrı yerlerde tutulmaz; çift giriş azalır.', 'Faturalar elektronik ortamda düzenlenir ve saklanır.', 'Mali müşavirinizle aynı verilere dayanarak çalışırsınız.'],
 hazirlik=['Mükellefiyet durumunuzu (e-fatura mı, e-arşiv mi) mali müşavirinizle netleştirin.', 'Seçtiğiniz entegratörden alınan kullanıcı bilgileri.', 'Fatura serisi ve numara düzeni.', 'KDV oranları ve istisna kodları için muhasebecinizin yönlendirmesi.'],
 hata=['Yanlış belge türüyle fatura kesmek.', 'Test faturasını canlı numarayla karıştırmak.', 'Müşteri vergi numarası ve unvanını eksik girmek.', 'İptal ve iade faturası sürecini bilmemek.'],
 olcut=['Entegratörün aylık ve kontör ücreti.', 'Destek ve kullanım kolaylığı.', 'Muhasebe programınızla uyum.', 'Arşiv saklama hizmeti.'],
 sss=[('Fatura kesmek için entegratör şart mı?', 'Mükellefiyetinize göre değişir. GİB e-Arşiv portalı gibi seçenekler de vardır; hangisinin size uyduğunu mali müşaviriniz söyler.'),
      ('Kestiğim faturayı müşteriye nasıl gönderirim?', 'Belge entegratör üzerinden iletilir; e-posta ile gönderim ayarları entegratörünüze bağlıdır.')]),
'erp': dict(
 neden=['Cari ve stok bilgisini iki programda elle girmezsiniz.', 'Muhasebecinizin kullandığı programla veri akışı olur.', 'Satış ve tahsilat hareketleri tek yerden izlenir.'],
 hazirlik=['Programınızın sürümü ve bağlantı yöntemi (API, servis, web servis).', 'Program sağlayıcınızdan bağlantı bilgilerini isteyin.', 'Hangi verilerin aktarılacağını yazılı karara bağlayın: cari, stok, satış.', 'Aktarımdan önce yedek alın.'],
 hata=['Her iki yönde aktarım isterken hangi tarafın esas olduğunu belirlememek.', 'Stok kodlarını iki tarafta farklı tutmak.', 'Test etmeden tüm cariyi aktarmak.', 'API erişiminin programda ayrıca açılması gerektiğini unutmak.'],
 olcut=['Programın bağlantı desteği.', 'Aktarılan veri kapsamı.', 'Destek ve sürüm güncellemeleri.', 'Lisans maliyeti.'],
 sss=[('Hangi veriler aktarılır?', 'Kapsam programa ve bağlantı türüne göre değişir. Kurulumdan önce hangi verinin hangi yönde aktarılacağını netleştirin.'),
      ('Listede olmayan programım için ne yapabilirim?', 'Webhook ve API ile veri paylaşımı mümkündür; ayrıntı için bize ulaşın.')]),
'sms': dict(
 neden=['Randevu ve teslim bilgisi müşteriye zamanında ulaşır; unutulan randevular azalır.', 'Mesajlar kendi gönderici adınızla gider.', 'E-posta ile belge ve bilgilendirme gönderebilirsiniz.'],
 hazirlik=['SMS sağlayıcısında hesap ve yeterli kontör.', 'Onaylı gönderici adı (başlık) için sağlayıcının istediği belgeler.', 'WhatsApp Business hesabı kullanacaksanız Meta onay süreci.', 'Müşteriden alınmış iletişim izni (İYS ve KVKK).'],
 hata=['Onay almadan tanıtım mesajı göndermek.', 'Mesajda yer tutucuyu doldurmadan göndermek.', 'Kontör bitince gönderimin durduğunu fark etmemek.', 'Uzun mesajla birden çok SMS ücreti ödemek.'],
 olcut=['Birim SMS fiyatı ve kontör süresi.', 'Başlık onay süresi.', 'Teslim raporu ve destek.', 'WhatsApp için şablon onay süreci.'],
 sss=[('Mesaj başına ücret öder miyim?', 'Gönderim ücreti SMS sağlayıcınızdan kesilir; fiyatı sağlayıcı belirler.'),
      ('Müşteriye hangi mesajlar gider?', 'Randevu hatırlatma, cihaz teslim, teklif ve ödeme hatırlatma gibi mesajlar için örnek metinleri mesaj şablonları sayfamızda bulabilirsiniz.')]),
'pazaryeri': dict(
 neden=['Ürünü her pazaryerine ayrı ayrı girmezsiniz.', 'Siparişler tek listede toplanır.', 'Stok ve fiyat tek yerden yönetilir.'],
 hazirlik=['Pazaryerinde onaylı satıcı hesabı.', 'API bilgilerinizi pazaryeri satıcı panelinden alın.', 'Ürün başlığı, marka, kategori ve görselleri pazaryeri kurallarına uygun hazırlayın.', 'Komisyon ve kargo koşullarını gözden geçirin.'],
 hata=['Kategori ve marka eşleştirmesini yapmadan ürün göndermek.', 'Stok güncellemesini kontrol etmeyip tükenmiş ürünü satışta bırakmak.', 'Fiyatı komisyonsuz belirlemek.', 'Yemek platformu siparişlerinde hazırlık süresini unutmak.'],
 olcut=['Komisyon oranı ve kategori bazlı farklar.', 'Ödeme ve vade süresi.', 'Kargo anlaşma koşulları.', 'Satıcı destek kalitesi.'],
 sss=[('Her pazaryeri için ayrı fiyat girebilir miyim?', 'Pazaryerlerinin kuralları ve komisyonları farklıdır; platforma özel fiyat belirlemek yaygın bir yöntemdir.'),
      ('Yemek platformları ile pazaryerleri aynı mıdır?', 'Hayır. Pazaryerleri ürün satışı, yemek platformları ise hazır yemek siparişi içindir; ikisinin siparişleri de aynı listede görülür.')]),
'olcum': dict(
 neden=['Ziyaretçi sayısı, kaynağı ve dönüşümü görürsünüz.', 'Reklamdan kaç talep geldiğini ölçersiniz.', 'Müşteri tek tıkla Google ya da Facebook hesabıyla üye olabilir.'],
 hazirlik=['İlgili hizmette hesap ve kimlik (ölçüm kimliği, piksel kimliği).', 'Çerez izni ve aydınlatma metniniz.', 'Ölçmek istediğiniz hedef: form gönderimi, arama, satın alma.'],
 hata=['Aynı ölçüm kodunu iki kez eklemek.', 'Çerez izni almadan ölçüm kodunu çalıştırmak.', 'Dönüşümü tanımlamadan reklam bütçesi harcamak.', 'Verileri yorumlamadan karar almak.'],
 olcut=['Ölçmek istediğiniz hedefe uyum.', 'Gizlilik ve KVKK uyumu.', 'Raporların anlaşılır olması.'],
 sss=[('Hangi araç neyi ölçer?', 'Analytics ziyaretçi davranışını, Search Console aramadaki görünürlüğü, reklam pikselleri ise reklamdan gelen dönüşümü ölçer.'),
      ('Takvim bağlantısı ne işe yarar?', 'Google Takvim bağlantısı randevuları takvimle ilişkilendirmek içindir.')]),
'diger': dict(
 neden=['İşletme profilinizi ve toplantı bağlantılarınızı tek yerden yönetirsiniz.', 'Webhook ile kendi yazılımınıza anlık bildirim gönderebilirsiniz.', 'Canlı destek ile sitede ziyaretçiyle yazışırsınız.'],
 hazirlik=['İlgili hizmetten kimlik, adres ya da anahtar.', 'Webhook için bildirimi alacak adres.', 'Kullanım amacınızı netleştirin.'],
 hata=['Webhook adresini herkese açık paylaşmak.', 'Gerekli izinleri vermeden bağlantıyı test etmek.'],
 olcut=['İhtiyacınıza uyum.', 'Güvenlik ve yetki kapsamı.'],
 sss=[('UYAP bağlantısı kimler içindir?', 'Dava ve dosya takibi yapan meslekler (avukat, hukuk bürosu) için düşünülmüş bir bağlantıdır.')]),
}
TERIM_EK = [
 ('Teknisyen', 'Sahada ya da atölyede işi yapan kişi; sektöre göre usta, personel ya da uzman olarak da adlandırılır.'),
 ('Atölye teslimi', 'Cihazın servise getirilerek teslim bırakılması; saha servisinden (müşteride yapılan iş) ayrılır.'),
 ('Saha servisi', 'İşin müşterinin bulunduğu yerde, teknisyenin gidip yapması.'),
 ('Yedek parça', 'Arızalı parçanın yerine takılan parça; stok takibi ve maliyet hesabı için kayıt altına alınır.'),
 ('Stok sayımı', 'Raftaki gerçek miktarın kayıttaki miktarla karşılaştırılması.'),
 ('Maliyet', 'Bir işin ya da ürünün size kaça mal olduğu; parça, işçilik ve diğer giderlerin toplamı.'),
 ('Kâr marjı', 'Satış fiyatı ile maliyet arasındaki farkın satış fiyatına oranı.'),
 ('Komisyon', 'Pazaryeri ya da ödeme kuruluşunun satıştan aldığı pay.'),
 ('Desi', 'Kargoda ürünün hacmine göre hesaplanan birim; ağırlık ile hacimsel ağırlığın büyüğü esas alınır.'),
 ('Vade', 'Bir ödemenin yapılması gereken son tarih.'),
 ('Tahsilat makbuzu', 'Alınan paranın karşılığında verilen belge.'),
 ('İade', 'Satılan ürünün ya da yapılan işin bedelinin müşteriye geri verilmesi.'),
 ('Yetki ve rol', 'Çalışanın panelde hangi ekranları görüp neyi değiştirebileceğini belirleyen ayar.'),
 ('Yedekleme', 'Verinin bir kopyasının ayrı bir yerde saklanması; arıza ya da yanlışlıkla silinmeye karşı.'),
 ('Müşteri portalı', 'Müşterinin kendi kayıtlarını ve durumunu görebildiği giriş alanı.'),
]
KARISTIRILAN = [
 ('e-Fatura mı e-Arşiv mi?', 'İkisi de elektronik faturadır. Alıcınız e-fatura mükellefiyse e-fatura, değilse e-arşiv düzenlenir. Hangisinin size uyduğunu mali müşaviriniz belirler.'),
 ('Teklif mi sipariş mi?', 'Teklif, müşterinin henüz onaylamadığı fiyattır. Müşteri onaylayınca iş ya da sipariş oluşur.'),
 ('Tahsilat mı fatura mı?', 'Tahsilat parayı almaktır; fatura satışın belgesidir. Para önce alınabilir, fatura sonra kesilebilir; iki kayıt ayrı tutulur.'),
 ('Servis fişi mi garanti belgesi mi?', 'Servis fişi cihazın teslim alındığını gösterir. Garanti belgesi yapılan işe verdiğiniz güvenceyi yazar.'),
 ('Cari hesap mı kasa mı?', 'Cari hesap kişi bazlı borç ve alacaktır; kasa ise işletmedeki nakit hareketidir.'),
 ('Sanal POS mu ödeme linki mi?', 'Sanal POS altyapıdır; ödeme linki ise o altyapıyla oluşturulan, müşteriye gönderilen bir bağlantıdır.'),
]
SABLON_EK = {
 'servis-formu-sablonu.html': dict(
  nasil=['Cihazı alır almaz, müşteri yanındayken formu doldurun.', 'Bildirilen arızayı müşterinin kendi sözleriyle yazın; teknik yorumu ayrı alana bırakın.', 'Teslim aldığınız aksesuarları (şarj aleti, kutu, kablo) tek tek yazın.', 'Seri numarasını okuyup doğrulayın; yanlış yazılan seri garanti sorgusunu bozar.', 'İki nüsha basın: biri müşteride, biri sizde kalsın.'],
  hata=['Arıza alanına yalnızca “bozuk” yazmak.', 'Cihazın dış durumunu (çizik, kırık) kayda geçirmemek.', 'Müşteri imzası almadan işleme başlamak.', 'Takip numarasını müşteriye söylememek.'],
  sakla='Servis formlarını teslimden sonra da belli bir süre saklayın; ne kadar süre saklanacağı için mevzuata ve mali müşavirinize bakın.'),
 'fiyat-teklifi-sablonu.html': dict(
  nasil=['İşin kapsamını açık yazın: ne yapılacak, ne yapılmayacak.', 'Parça ve işçiliği ayrı kalemlerde gösterin.', 'KDV’yi ayrı satırda yazın; KDV dahil mi hariç mi olduğunu belirtin.', 'Teklifin geçerlilik süresini ve ödeme koşulunu yazın.', 'Müşteri onayını imza ve tarihle alın.'],
  hata=['Parça fiyatı sık değişirken uzun geçerlilik vermek.', 'Ek işi yazmadan sonradan fiyat artırmak.', 'KDV durumunu belirtmemek.', 'Onay almadan işe başlamak.'],
  sakla='Onaylanan teklifler iş kaydıyla birlikte saklanır; anlaşmazlıkta işin kapsamını gösterir.'),
 'garanti-belgesi-sablonu.html': dict(
  nasil=['Garantinin neyi kapsadığını açık yazın: işçilik, değişen parça, ikisi birden.', 'Başlangıç tarihini ve süreyi gün ya da ay olarak belirtin.', 'Kapsam dışı durumları (yanlış kullanım, darbe, sıvı teması gibi) yazın.', 'Belgeyi imzalayıp kaşeleyin ve bir nüshasını müşteriye verin.'],
  hata=['Süreyi belirtmeden “garantilidir” yazmak.', 'Kapsam dışı durumları hiç yazmamak.', 'Değişen parçanın seri numarasını kayda geçirmemek.', 'Belgeyi müşteriye vermeyip sadece sözlü söylemek.'],
  sakla='Verdiğiniz garanti belgelerinin bir kopyasını iş kaydıyla birlikte saklayın; sonradan gelen taleplerde ilk bakacağınız belge budur.'),
}

SABLON_NEDEN = {
 'servis-formu-sablonu.html': ['Cihazın hangi durumda teslim alındığını kanıtlar; sonradan “çizikti” gibi tartışmaları önler.', 'Müşteriye takip numarası vermenizi sağlar; müşteri durumu sormak için bu numarayı kullanır.', 'İş geçmişi olur: aynı cihaz tekrar geldiğinde önceki arızaya bakarsınız.', 'Tahsilat ve garanti süreçlerinin başlangıç belgesidir.'],
 'fiyat-teklifi-sablonu.html': ['Müşteri ne ödeyeceğini işten önce bilir; fiyat itirazı azalır.', 'İşin kapsamı yazılıdır; ek iş istenirse yeni teklif çıkarırsınız.', 'Onaylı teklif, işin başlaması için net bir dayanak olur.', 'Teklif geçmişi, hangi işlerin onaylanıp hangilerinin geri çevrildiğini görmenizi sağlar.'],
 'garanti-belgesi-sablonu.html': ['Müşteri, yapılan işin ne kadar süre güvence altında olduğunu bilir.', 'Aynı arızayla geri gelen müşteride, garanti kapsamında olup olmadığını hızlı karara bağlarsınız.', 'Değişen parçanın seri numarasıyla izlenebilirlik sağlar.', 'Güvenilir firma izlenimi verir.'],
}
SABLON_SSS_EK = {
 'servis-formu-sablonu.html': [('Formu dijital ortamda da tutabilir miyim?', 'Evet. Kağıt form küçük işler için yeterlidir; kayıt sayısı arttıkça servis kayıtlarını bir programda tutmak arama ve raporlamada zaman kazandırır.'), ('Müşteri formu okumadan imzalarsa ne olur?', 'İmza, formdaki bilgileri kabul ettiğini gösterir. Yine de formu müşteriye göstermek ve önemli noktaları sözlü belirtmek iyi bir uygulamadır.')],
 'fiyat-teklifi-sablonu.html': [('Teklifte parça ve işçilik ayrı mı yazılmalı?', 'Ayrı yazmak şeffaftır ve müşterinin neye ödeme yaptığını gösterir; zorunlu değildir, tercih meselesidir.'), ('Teklif verdikten sonra fiyat değişirse?', 'Teklifin geçerlilik süresi içinde fiyat sabit kalmalıdır; süre dolduysa yeni teklif hazırlayın.')],
 'garanti-belgesi-sablonu.html': [('Garanti süresini kim belirler?', 'Satılan ürünlerde yasal asgari süreler vardır; verdiğiniz servis güvencesinin süresini ise siz belirlersiniz. Ayrıntı için mevzuata bakın.'), ('Garanti kapsamı dışındaki işler nasıl yazılır?', 'Yanlış kullanım, darbe, sıvı teması ve yetkisiz müdahale gibi durumları açık ve kısa cümlelerle yazın.')],
}
MESAJ_ILKE = ['Kısa tutun: tek mesajda tek bilgi verin.', 'Müşteriyi adıyla karşılayın.', 'Takip numarasını ve tarihi mesaja yazın; müşteri kendisi arayıp sormak zorunda kalmasın.', 'Fiyat ve onay isteyen mesajlarda tutarı açık yazın.', 'Gece geç saatlerde mesaj göndermekten kaçının.', 'Müşterinin yanıt verebileceği bir yol bırakın.']
MESAJ_ZAMAN = [('Cihaz teslim alındığında', 'Cihaz teslim alındı mesajı: müşteri takip numarasını yanında taşır.'), ('Teklif hazır olduğunda', 'Fiyat teklifi mesajı: onay beklendiğini belirtir.'), ('İş bittiğinde', 'Cihaz hazır mesajı: teslim için müşteriyi çağırır.'), ('Randevudan önce', 'Randevu hatırlatma mesajı: unutulan randevuları azaltır.'), ('Ödeme gecikince', 'Ödeme hatırlatma mesajı: nazik ve kısa tutulur.'), ('Bakım zamanı yaklaşınca', 'Bakım hatırlatma mesajı: müşteriyi geri çağırır.'), ('İşten sonra', 'Memnuniyet mesajı: görüş ister.')]
HUB_SSS = [('Bu şablonları kullanmak ücretsiz mi?', 'Evet; yazdırıp kullanabilirsiniz. Kendi koşullarınızı ve unvanınızı eklemeyi unutmayın.'), ('Şablonlar hukuken yeterli mi?', 'Şablonlar örnektir. Sözleşme, garanti ve KVKK metinleri için avukatınıza ya da mali müşavirinize danışın.'), ('Panelde bu belgeler hazır mı geliyor?', 'Panelde servis formu, teklif ve makbuz sektörünüzün kendi adlarıyla düzenlenir ve yazdırılır.')]
