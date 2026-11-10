"""Teknik olmayan sektörlerin tema içeriği (content.SEC biçimi). Metinler örnektir; firma panelinden kendi bilgileriyle değiştirilir.
Kural: kanıtlanamayan sayı, ödül, sertifika veya müşteri sayısı yazılmaz."""
import sys, os
sys.path.insert(0, os.environ.get('OK_APP_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'panel'))
import sektor_ek


def _svc(key, icons):
    return [(t, d, icons[i % len(icons)]) for i, (t, d) in enumerate(sektor_ek.NEW[key]['site']['services'])]


def _faq(key):
    return list(sektor_ek.NEW[key]['site']['faq']) + [('Randevu / sipariş nasıl veririm?', 'Sitedeki formdan ya da telefonla; talebiniz kayıt altına alınır ve size dönüş yapılır.'),
                                                    ('Ödeme nasıl yapılır?', 'Nakit, kart ya da havale; ödeme yöntemi ve tutar işlemden önce netleştirilir.')]


SEC = {
 'oto_servis': dict(label='Oto servis', ico='wr', img='oto_servis', cihaz=['Otomobil', 'Hafif ticari', 'SUV'], brands=['Renault', 'Fiat', 'Volkswagen', 'Ford', 'Toyota', 'Hyundai', 'Opel', 'Peugeot'],
   services=_svc('oto_servis', ['cal', 'wr', 'sp', 'bo', 'sn']), faq=_faq('oto_servis'),
   h=[('Aracınız yolda kalmadan bakıma alın', 'Periyodik bakım, fren ve lastik kontrolü tek randevuda; yapılan her işlem iş emrinde yazılı.'),
      ('Arızayı bulalım, gereksiz parça değiştirmeyelim', 'Bilgisayarlı teşhisle önce nedeni bulur, onarımdan önce fiyatı yazılı iletiriz.'),
      ('Bakım takvimi telefonunuzda', 'Bir sonraki bakım tarihini hesaplayın, randevunuzu şimdiden ayırın.'),
      ('Kış lastiği, akü, fren: hepsi aynı yerde', 'Sezon öncesi kontrolde araç gelmeden eksikleri size gösteririz.'),
      ('Aracınızı teslim alırken fotoğrafla kayıt', 'Teslimde hasar ve kilometre kayıt altına alınır; sürpriz yok.')],
   steps=[('Randevu', 'Aracınız ve talebiniz kayıt altına alınır.'), ('Muayene', 'Teşhis yapılır, işlem ve fiyat size iletilir.'), ('Onarım', 'Onayınızla işlem başlar, parçalar gösterilir.'), ('Teslim', 'İş emri ve fatura ile aracınızı teslim alırsınız.')],
   rev=[('Cem A.', 'Fiyatı onarımdan önce yazılı söylediler, sonradan eklenen bir şey çıkmadı.'), ('Derya K.', 'Eski parçaları gösterdiler, neyin değiştiğini anladım.'), ('Murat Ö.', 'Randevu saatinde aracım hazırdı, SMS ile haber verdiler.')],
   prob=['Periyodik bakım', 'Motor ışığı', 'Fren sesi', 'Akü', 'Lastik', 'Klima'], tag='araç bakım ve onarım'),
 'oto_cekici': dict(label='Oto çekici', ico='ar', img='oto_cekici', cihaz=['Otomobil', 'Hafif ticari', 'Motosiklet'], brands=['Otomobil', 'Hafif ticari', 'Motosiklet', 'Minibüs', 'Kamyonet'],
   services=_svc('oto_cekici', ['ar', 'wr', 'bx', 'bo', 'lk']), faq=_faq('oto_cekici'),
   h=[('Yolda kaldınız mı? Konumunuzu gönderin', 'En yakın ekibi yönlendirir, tahmini varış süresini baştan söyleriz.'),
      ('Kazadan sonra aracınız güvenle taşınsın', 'Yüklemeden önce fotoğraf, teslimde imzalı tutanak.'),
      ('Çekici ücretini önceden öğrenin', 'Mesafe ve araç tipine göre ön hesap yapın, net fiyatı telefonda alın.'),
      ('Şehirlerarası araç taşıma', 'Araç taşıyıcı ile uzun mesafe; teslim öncesi ve sonrası kayıt.'),
      ('Gece gündüz yol yardım', 'Akü, lastik ve yakıt desteği için tek arama.')],
   steps=[('Çağrı', 'Konumunuz ve aracınız alınır.'), ('Yönlendirme', 'En yakın ekip yola çıkar, varış süresi bildirilir.'), ('Yükleme', 'Fotoğraflı kayıtla araç yüklenir.'), ('Teslim', 'Adrese teslim, imzalı tutanak.')],
   rev=[('Serkan T.', 'Gece yarısı aradım, ekip kısa sürede geldi, fiyat baştan netti.'), ('Aylin B.', 'Aracı yüklemeden fotoğraf çektiler, teslimde sorun yaşamadım.'), ('Fatih E.', 'Telefonda söylenen fiyatla aynı ödedim.')],
   prob=['Araç çalışmıyor', 'Kaza', 'Lastik patlak', 'Akü bitti', 'Anahtar içeride', 'Şehirlerarası'], tag='çekici ve yol yardım'),
 'kuafor': dict(label='Kuaför', ico='cp', img='kuafor', cihaz=['Kadın', 'Erkek', 'Çocuk'], brands=['Saç kesimi', 'Boya', 'Röfle', 'Fön', 'Sakal', 'Bakım'],
   services=_svc('kuafor', ['cp', 'sp', 'pl', 'us', 'st']), faq=_faq('kuafor'),
   h=[('Randevunuzu şimdi ayırın, beklemeyin', 'Gün ve saati siz seçin; hatırlatma mesajı telefonunuza gelir.'),
      ('Saçınıza göre kesim, size göre bakım', 'İşleme başlamadan ne istediğinizi dinler, sonrası için bakım önerisi veririz.'),
      ('Boya ve röfle için doğru ton', 'Alerji sorusuyla başlar, saç yapınıza uygun ürünle çalışırız.'),
      ('Özel gününüz için gelin saçı', 'Deneme randevusuyla birlikte gün öncesinden planlanır.'),
      ('Erkek kuaförü ve sakal tasarımı', 'Kesim, ustura tıraşı ve bakım; beklemeden randevulu.')],
   steps=[('Randevu', 'Hizmet, gün ve saati seçersiniz.'), ('Hatırlatma', 'Randevudan önce SMS ile hatırlatırız.'), ('İşlem', 'Önce konuşur, sonra uygularız.'), ('Bakım önerisi', 'Evde bakım ve sonraki randevu planlanır.')],
   rev=[('Elif S.', 'Ne istediğimi dinlediler, fotoğrafı gösterince tam istediğim oldu.'), ('Burak Y.', 'Saatinde aldılar, beklemedim.'), ('Zehra M.', 'Boyadan önce alerji sordular, bakımı da anlattılar.')],
   prob=['Saç kesimi', 'Boya', 'Röfle', 'Fön', 'Sakal', 'Gelin saçı'], tag='saç ve bakım'),
 'nakliye': dict(label='Nakliyat', ico='bx', img='nakliye', cihaz=['1+1', '2+1', '3+1 ve üzeri', 'Ofis'], brands=['Evden eve', 'Ofis', 'Parça eşya', 'Depolama', 'Şehirlerarası'],
   services=_svc('nakliye', ['bx', 'ar', 'dn', 'dr', 'wr']), faq=_faq('nakliye'),
   h=[('Taşınma gününüz stressiz geçsin', 'Ücretsiz keşif, yazılı teklif ve paketlemeden yerleştirmeye tek ekip.'),
      ('Eşyalarınız sayımla teslim edilir', 'Yüklemede ve indirmede liste kontrolü; eksik ya da hasar kayıt altında.'),
      ('Evinize kaç kişi, hangi araç gerekir?', 'Eşya miktarınıza göre ön hesabı yapın, keşif randevusu alın.'),
      ('Asansörlü taşıma ile hızlı teslim', 'Yüksek katlarda dış cephe asansörüyle saatler değil dakikalar.'),
      ('Şehirlerarası taşıma, sigortalı', 'Mesafe ne olursa olsun yazılı sözleşme ve takip.')],
   steps=[('Keşif', 'Eşyalar görülür, liste çıkarılır.'), ('Teklif', 'Yazılı ve net fiyat sunulur.'), ('Taşıma', 'Paketleme, yükleme, taşıma ve montaj.'), ('Teslim', 'Sayım ve onayla teslim.')],
   rev=[('Gamze P.', 'Eşyalarımın tamamı sayımla teslim edildi, çizik bile yok.'), ('Hakan D.', 'Keşifte söylenen fiyat taşıma günü değişmedi.'), ('Neslihan A.', 'Mobilyaları söküp yeniden kurdular, aynı günde bitti.')],
   prob=['Evden eve', 'Ofis taşıma', 'Parça eşya', 'Asansörlü', 'Depolama', 'Şehirlerarası'], tag='evden eve ve ofis taşıma'),
 'tekstil': dict(label='Tekstil', ico='cp', img='tekstil', cihaz=['Hazır giyim', 'İş kıyafeti', 'Ev tekstili', 'Kumaş'], brands=['Tişört', 'Pantolon', 'Elbise', 'Ev tekstili', 'İş kıyafeti', 'Kumaş'],
   services=_svc('tekstil', ['cp', 'bx', 'pl', 'us', 'sp']), faq=_faq('tekstil'),
   h=[('Toptan hazır giyimde güvenilir üretici', 'Katalog, fiyat listesi ve numune talebi tek yerde; sevkiyat takipli.'),
      ('Modeliniz, kumaşınız, adediniz', 'Özel üretim ve fasonda numuneden sevkiyata kadar şeffaf süreç.'),
      ('İş kıyafetinde firma renginiz', 'Beden tablosu, baskı ve nakış dahil toplu üretim.'),
      ('Kumaş metrajınızı hesaplayın', 'Adet ve model başına metre girin, ihtiyacınızı ve teklif talebinizi iletin.'),
      ('Ev tekstilinde toptan fiyat', 'Nevresimden havluya; mağaza ve otel siparişlerine uygun adetler.')],
   steps=[('Talep', 'Model, adet ve termin bilgisi alınır.'), ('Numune', 'Numune hazırlanır, onayınıza sunulur.'), ('Üretim', 'Onaylı numuneye göre üretim ve kalite kontrol.'), ('Sevkiyat', 'Koli sayımı ve irsaliye ile sevk.')],
   rev=[('Mağaza sahibi, İzmir', 'Numune ile gelen ürün birebir çıktı, termin tuttu.'), ('Otel işletmecisi, Antalya', 'Havlu siparişimiz adet ve renk olarak eksiksiz geldi.'), ('Atölye yöneticisi, Bursa', 'Beden tablosunu baştan çıkardılar, iade çıkmadı.')],
   prob=['Toptan sipariş', 'Numune', 'Özel üretim', 'Baskı / nakış', 'İş kıyafeti', 'Kumaş'], tag='toptan ve özel üretim tekstil'),
 'eticaret': dict(label='Mağaza', ico='bx', img='eticaret', cihaz=['Giyim', 'Ayakkabı & çanta', 'Ev & yaşam', 'Kozmetik'], brands=['Giyim', 'Ayakkabı', 'Çanta', 'Kozmetik', 'Ev & Yaşam', 'Hediyelik'],
   services=_svc('eticaret', ['bx', 'ar', 'dr', 'us', 'cp']), faq=_faq('eticaret'),
   h=[('Sipariş verin, kapınıza gelsin', 'Stoktaki ürünler aynı gün ya da ertesi iş günü kargoda; takip kodu SMS ile gelir.'),
      ('Beğenmezseniz kolay iade', 'İade ve değişim talebini tek adımda açın, kargo kodunu size gönderelim.'),
      ('Toplu alımda özel fiyat', 'Adet ve kurumsal fatura için teklif isteyin; indirimi hemen hesaplayın.'),
      ('Hediye paketi ve notla', 'Sevdiğinize doğrudan gönderin; paket ve not seçeneği sipariş sırasında.'),
      ('Yeni gelenler ve indirimler', 'Stok anlık güncellenir; biten ürün satışta görünmez.')],
   steps=[('Sipariş', 'Ürünleri sepete ekler, bilgilerinizi girersiniz.'), ('Hazırlık', 'Siparişiniz kontrol edilir ve paketlenir.'), ('Kargo', 'Takip kodu SMS ile gelir.'), ('Teslim ve iade', 'Teslimden sonra yasal süre içinde iade hakkınız vardır.')],
   rev=[('Ece T.', 'Paket özenliydi, ürün fotoğraftaki gibi geldi.'), ('Onur Ç.', 'İade talebim bir günde sonuçlandı.'), ('Dilek R.', 'Kargo takip kodu hemen geldi, söylenen günde teslim aldım.')],
   prob=['Sipariş durumu', 'Kargo takibi', 'İade', 'Değişim', 'Toplu alım', 'Fatura'], tag='online mağaza'),
 'temizlik': dict(label='Temizlik', ico='sp', img='temizlik', cihaz=['Daire', 'Villa', 'Ofis', 'İnşaat sonrası'], brands=['Ev', 'Ofis', 'İnşaat sonrası', 'Halı', 'Koltuk', 'Cam'],
   services=_svc('temizlik', ['sp', 'cl', 'wr', 'bx', 'st']), faq=_faq('temizlik'),
   h=[('Eviniz pırıl pırıl, siz rahat', 'Oda sayınıza göre planlı temizlik; önce ve sonra fotoğrafla kayıt.'),
      ('Ofisiniz mesai başlamadan hazır', 'Haftalık ya da aylık abonelikle düzenli temizlik.'),
      ('İnşaat sonrası detaylı temizlik', 'Boya, alçı ve toz kalıntıları tek ziyarette.'),
      ('Halı ve koltuk adresten alınır', 'Yıkama, kurutma ve teslim; takip SMS ile.'),
      ('Ne kadar sürer, kaç kişi gelir?', 'Metrekarenizi girin, tahmini süreyi ve ekibi görün.')],
   steps=[('Talep', 'Alan ve temizlik türü alınır.'), ('Plan', 'Gün, ekip ve fiyat netleşir.'), ('Temizlik', 'Planlanan saatte ekip gelir.'), ('Kontrol', 'Birlikte kontrol edilir, eksik varsa tamamlanır.')],
   rev=[('Selma K.', 'Önce ve sonra fotoğraflarını gönderdiler, her yer yerli yerindeydi.'), ('Ofis yöneticisi', 'Mesai başlamadan bitirmişlerdi.'), ('Kadir B.', 'Halılar kokusuz ve temiz teslim edildi.')],
   prob=['Ev temizliği', 'Ofis', 'İnşaat sonrası', 'Halı', 'Koltuk', 'Cam'], tag='temizlik hizmetleri'),
 'guzellik': dict(label='Güzellik salonu', ico='sp', img='guzellik', cihaz=['Cilt', 'Epilasyon', 'El ayak', 'Kaş kirpik'], brands=['Cilt bakımı', 'Epilasyon', 'Manikür', 'Kaş', 'Masaj'],
   services=_svc('guzellik', ['sp', 'fl', 'st', 'pl', 'cl']), faq=_faq('guzellik'),
   h=[('Kendinize ayıracağınız saat burada', 'Cilt bakımından epilasyona, randevunuzu online ayırın.'),
      ('Cildinize göre bakım planı', 'Analizle başlar, size özel seans önerisi çıkarırız.'),
      ('Paket seanslarınız takipte', 'Kalan seans ve sonraki randevu tarihini kolayca görün.'),
      ('Hijyenik ve rahat ortam', 'Tek kullanımlık malzeme ve temiz kabinlerde uygulama.'),
      ('Özel gün öncesi bakım', 'Düğün ve davet öncesi seans planı.')],
   steps=[('Randevu', 'İşlem, gün ve saat seçilir.'), ('Karşılama', 'Hassasiyet ve beklentileriniz konuşulur.'), ('Uygulama', 'İşlem hijyenik ortamda uygulanır.'), ('Takip', 'Sonraki seans planlanır.')],
   rev=[('Merve G.', 'İlk seansta her adımı anlattılar, rahat hissettim.'), ('Seda U.', 'Paket seanslarım düzenli takip ediliyor.'), ('Pelin Ş.', 'Hijyene çok dikkat ediyorlar.')],
   prob=['Cilt bakımı', 'Epilasyon', 'Manikür', 'Kaş / kirpik', 'Masaj', 'Makyaj'], tag='güzellik ve bakım'),
}
PRODUCTS = {
 'eticaret': [('ÜR-1001', 'Deri omuz çantası', 'Atölye', 'Çanta', 1290, 2), ('ÜR-1002', 'Koşu ayakkabısı', 'Atölye', 'Ayakkabı', 1850, 2), ('ÜR-1003', 'Pamuklu basic tişört', 'Atölye', 'Giyim', 349, 2),
              ('ÜR-1004', 'Cam parfüm şişesi 50 ml', 'Atölye', 'Kozmetik', 780, 1), ('ÜR-1005', 'Telefon kılıfı', 'Atölye', 'Aksesuar', 220, 2), ('ÜR-1006', 'Seramik masa lambası', 'Atölye', 'Ev & Yaşam', 940, 2),
              ('ÜR-1007', 'Çelik kasa kol saati', 'Atölye', 'Saat', 2450, 1), ('ÜR-1008', 'Hediye seti', 'Atölye', 'Hediyelik', 690, 2), ('ÜR-1009', 'Sırt çantası', 'Atölye', 'Çanta', 990, 0), ('ÜR-1010', 'Keten gömlek', 'Atölye', 'Giyim', 620, 2)],
 'tekstil': [('TK-2001', "Penye tişört (12'li koli)", 'Atölye', 'Giyim', 1980, 2), ("TK-2002", "Kot pantolon (10'lu)", 'Atölye', 'Giyim', 3200, 2), ('TK-2003', 'İş ceketi (toptan)', 'Atölye', 'İş kıyafeti', 4100, 1),
             ('TK-2004', 'Havlu seti', 'Atölye', 'Ev tekstili', 760, 2), ("TK-2005", "Elbise (8'li)", 'Atölye', 'Giyim', 2750, 2), ('TK-2006', 'Kumaş topu 40 m', 'Atölye', 'Kumaş', 2200, 2)],
 'kuafor': [('KB-3001', 'Onarıcı saç maskesi', 'Atölye', 'Bakım', 420, 2), ('KB-3002', 'Şampuan 400 ml', 'Atölye', 'Bakım', 310, 2), ('KB-3003', 'Saç serumu', 'Atölye', 'Bakım', 380, 2), ('KB-3004', 'Sakal yağı', 'Atölye', 'Sakal', 260, 2),
            ('KB-3005', 'Şekillendirici wax', 'Atölye', 'Şekillendirme', 240, 1), ('KB-3006', 'Fön spreyi', 'Atölye', 'Şekillendirme', 290, 2)],
 'guzellik': [('GZ-4001', 'Nemlendirici krem', 'Atölye', 'Cilt bakımı', 540, 2), ('GZ-4002', 'Temizleme jeli', 'Atölye', 'Cilt bakımı', 330, 2), ('GZ-4003', 'Güneş kremi', 'Atölye', 'Cilt bakımı', 480, 2),
              ('GZ-4004', 'El kremi', 'Atölye', 'Bakım', 190, 2), ('GZ-4005', 'Tırnak bakım seti', 'Atölye', 'Bakım', 260, 1), ('GZ-4006', 'Masaj yağı', 'Atölye', 'Masaj', 350, 2)],
}
SHOP_SECTORS = ('eticaret', 'tekstil', 'kuafor', 'guzellik')

import sektor_cok as _cok
SEC.update(_cok.content_sec(_faq))
PRODUCTS.update(_cok.PRODUCTS)
SHOP_SECTORS = SHOP_SECTORS + tuple(_cok.theme_meta()['shop_on'])
