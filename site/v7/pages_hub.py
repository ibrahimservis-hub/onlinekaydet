from rich import *
from pages_cozum import S
def hub_ozellikler():
    core=[('file','Servis kayıtları','Müşteri, cihaz, arıza, randevu ve usta tek formda.','cozum-servis-kaydi.html'),
    ('wrench','Usta uygulaması','Atama, yola çıkış, fotoğraf, imza ve parça telefondan.','usta-uygulamasi.html'),
    ('chat','SMS bildirimleri','Atama, yola çıkış ve bitiş mesajları otomatik gider.','cozum-sms-bildirimleri.html'),
    ('receipt','PDF servis fişi','İmzalı, logolu fiş. A4 ve 80 mm.','cozum-pdf-servis-fisi.html'),
    ('wallet','Kasa ve muhasebe','Tahsilat, gider ve cari takibi usta bazında.','cozum-kasa-muhasebe.html'),
    ('chart','Raporlar','Ciro, usta performansı ve açık işler.','cozum-raporlar.html'),
    ('users','Personel takibi','Rol, yetki ve günlük iş yükü.','cozum-personel-takibi.html'),
    ('globe','Web sitesi ve temalar','38 hazır tema, randevu formu ve SEO.','cozum-web-sitesi.html'),
    ('bag','Yedek parça mağazası','Parçalarınızı sitede ve pazaryerinde satın.','cozum-yedek-parca-magazasi.html')]
    corp=[('bell','Bakım ve garanti','Yıllık bakım hatırlatma, garanti takibi.','cozum-bakim-garanti.html'),
    ('check','Teklif ve onay','Müşteri teklifi linkten onaylar.','cozum-teklif-onay.html'),
    ('card','Ödeme ve e-arşiv fatura','Ödeme linki, otomatik tahsilat.','cozum-odeme-fatura.html'),
    ('users','Müşteri portalı','Müşteri kendi servisini izler.','cozum-musteri-portali.html'),
    ('map','Canlı usta takibi','Konum ve çevrimdışı işlem kuyruğu.','cozum-canli-takip.html'),
    ('link','Bayi (B2B) modülü','Bayi kendi talebini açar ve izler.','cozum-bayi-b2b.html'),
    ('search','QR etiket ve arayan numara','Cihaz geçmişi ve müşteri kartı.','cozum-qr-etiket.html'),
    ('star','Otomatik usta atama','Konum, uzmanlık ve yüke göre öneri.','cozum-otomatik-atama.html'),
    ('tag','Pazarlama araçları','Kampanya, toplu mesaj, geri kazanma.','cozum-pazarlama.html')]
    body=hero([(None,'Ürün')],'Servis işiniz için <em>her şey</em> bir arada','Kayıttan tahsilata, ustadan müşteriye, web sitesinden raporlara. Her modülü ayrı ayrı inceleyin; her biri sektörünüzün işleyişine göre kurulur.',
      mk_list('Bugün · servis panosu',[('SV-1043 · Ayşe Yılmaz','Kombi · Basınç düşüyor','Yolda','b'),('SV-1042 · Murat Şen','Klima · Soğutmuyor','Başladı','y'),('SV-1041 · Zeynep Aras','Çamaşır makinesi','Tamamlandı','g')],'Panel'),['İlk ay ücretsiz','Kart bilgisi istenmez'],
      [('index.html#kayit','Ücretsiz deneyin',''),('paketler-ozellikler.html','Paket paket ayrıntı','o')])
    body+=strip([('18','modül'),('4','paket'),('8','sektör'),('38','hazır web teması')])
    body+=sec(head('Çekirdek modüller','Her serviste ihtiyaç duyulan dokuz modül','Başlangıç, Profesyonel ve Tam Paket içinde gelen, günlük işi yürüten modüller.')+cards(core))
    body+=sec(head('Kurumsal modüller','Büyüyen servisler için dokuz modül','Bakım gelirini yönetmek, müşteriye self-servis sunmak, bayiyle çalışmak isteyen servisler için.')+cards(corp),id='kurumsal')
    body+=split('Esneklik','Süreci siz tasarlarsınız','Her firmanın çalışma şekli farklı. Fotoğraf, imza ve form alanlarını kendi sürecinize göre açıp kapatırsınız; servis fişinin tasarımı ve metinleri size ait.',['Fotoğraf: zorunlu, isteğe bağlı ya da kapalı','Müşteri imzası ve usta imzası ayrı ayrı','Servis fişi tasarımı ve metinleri'],
      mk_toggles('Servis ayarları',[('Fotoğraf zorunlu',True),('Müşteri imzası',True),('Usta imzası',False),('Parça ve işçilik formu',True),('Memnuniyet anketi',True)],'Ayarlar'))
    body+=band('Kombi servisiyseniz','Ücretsiz hata kodları rehberinde markanızı seçin, arızanın anlamını ve ilk kontrol adımlarını görün.',('hata-kodlari.html','Hata kodları rehberi'))
    body+=sec(head('Hangi pakette ne var','Paketler ve modüller','Hangi modülün hangi pakette olduğunu paket sayfasında görün.')+'<a class="btn ink" href="paketler-ozellikler.html">Paket paket ayrıntı</a>')
    body+=cta('Özellikleri canlı görmek ister misiniz?','Formu doldurun, uzmanımız sektörünüze göre kurulumu birlikte planlasın. İlk ay ücretsiz.')
    page('ozellikler.html','Özellikler: servis takip programının tüm modülleri','Servis kaydı, usta uygulaması, SMS, fiş, kasa, rapor, web sitesi ve kurumsal modüller. Teknik servisler için hepsi bir arada.',body)
def usta():
    body=hero([('ozellikler.html','Ürün'),(None,'Usta uygulaması')],'Ustanız sahada, kayıt <em>anında panelde</em>','İşi usta telefonundan görür, fotoğraf çeker, müşteriye imza attırır. Siz ofisten aynı kaydı izlersiniz. İndirme yok, tarayıcıdan girer.',
      phone('Bugünkü işlerim',[('Ayşe Yılmaz · Kombi','Basınç düşüyor · 11:00–13:00','Yola çık',False),('Murat Şen · Klima','Soğutmuyor · 14:00–16:00','Servise başla',True)]),['Başlangıç pakette','Telefon tarayıcısından çalışır'])
    body+=strip([('3','liste: aktif, tamamlanan, atölye'),('2','imza: müşteri ve usta'),('SMS','yolda ve tamamlandı'),('0','indirme: ana ekrana ekleyin')])
    body+=split('Sahada','Usta ne görür, ne yapar','Usta telefonundan girer ve yalnızca kendisine atanan işleri sırayla görür. Adres ve telefon iş kartında; tek dokunuşla arar ya da yol tarifi açar.',['Aktif, Tamamlanan ve Atölye listeleri','“Yola Çık” ve “Servise Başla” adımları','Telefondan fotoğraf, imza ve parça girişi','İş bitince fiş otomatik hazırlanır'],
      phone('Servis kaydı',[('SV-1043 · Kombi','Müşteri: Ayşe Yılmaz','Fotoğraf çek',True),('Parça: Basınç sensörü','650 ₺ · İşçilik 500 ₺','İmza al',False)]))
    body+=split('Yönetici','Siz ofiste her şeyi görürsünüz','Usta işe başladı, tamamladı, tahsilat yaptı; hepsi panelde anında görünür. “Yoldayım” adımında müşteriye otomatik SMS ve takip linki gider.',['Atama ekranında ustanın günlük iş yükü','“Yoldayım” ile müşteriye SMS ve takip linki','Kurumsal pakette canlı konum ve çevrimdışı işlem kuyruğu'],
      mk_list('Yönetici ekranı',[('Hasan Kaya','SV-1043 · Yolda','Yolda','b'),('Murat Şen','SV-1042 · Başladı','Başladı','y'),('Selim Acar','Atölye','Atölye','')]),True,('cozum-canli-takip.html','Canlı usta takibi'))
    body+=sec(head('Nasıl çalışır','Yöneticide üç adım','')+steps([('Kaydı siz açarsınız','Müşteri, cihaz marka ve modeli, arıza ve randevu bilgisi girilir.'),('Ustayı atarsınız','İş seçtiğiniz ustanın telefonuna düşer.'),('Süreci izlersiniz','Usta işe başladı, tamamladı, tahsilat yaptı; panelde görünür.')]))
    qa=[('Uygulamayı indirmem gerekiyor mu?','Usta, panele telefonunun tarayıcısından giriş yapar. Ana ekrana ekleyerek uygulama gibi kullanabilir.'),('Adımları değiştirebilir miyim?','Evet. Servis Ayarları bölümünden fotoğraf ve imza adımlarını açıp kapatır, fiş biçimini düzenlersiniz.'),('İnternet yoksa ne olur?','Kurumsal pakette çevrimdışı işlem kuyruğu vardır; bağlantı gelince işlemler gönderilir.')]
    body+=sec(head('Sık sorulanlar','Usta uygulaması hakkında','')+faq(qa))
    body+=sec(head('Birlikte kullanın','İlgili çözümler','')+related([('cozum-servis-kaydi.html','Servis kaydı','Kayıt akışı'),('cozum-personel-takibi.html','Personel takibi','Rol ve yetki'),('cozum-pdf-servis-fisi.html','PDF servis fişi','İmzalı fiş')]))
    body+=cta()
    page('usta-uygulamasi.html','Usta uygulaması','Ustanız sahada işi telefonundan görür, fotoğraf çeker, imza alır; siz ofisten izlersiniz.',body,faq_ld(qa))
ENT=[]
def ent(fn,title,lede,vis,strp,blocks,qa,rel):
    ENT.append((fn,title,lede,vis,strp,blocks,qa,rel))
def hub_ent():
    body=hero([(None,'Entegrasyonlar')],'SMS, pazaryeri ve ödeme <em>bağlantıları</em>','Müşterinize SMS gönderin, yedek parçayı pazaryerlerinde satın, web sitenizden kartla ödeme alın. Hepsi panelden, kendi hesabınızla ayarlanır.',
      mk_list('Bağlantılar',[('İleti Merkezi','Bakiye sorgusu başarılı','Bağlı','g'),('Trendyol','Ürün kartından yönetim','Hazır','g'),('iyzico','Kart ödemesi','Bağlı','g'),('Search Console','Arama performansı','Bağlı','g')],'Panel'),['Hesap bilgilerini siz girersiniz','Kurulumda birlikte yaparız'])
    body+=strip([('5','SMS sağlayıcı seçeneği'),('3','pazaryeri'),('1','ödeme sistemi: iyzico'),('Excel','kayıt aktarımı')])
    body+=sec(head('Bağlantı grupları','Servis işinizin dışarıyla konuştuğu yerler','')+cards([
      ('chat','SMS ve WhatsApp','Netgsm, Verimor, İleti Merkezi, Twilio ve özel webhook. WhatsApp iletilemezse SMS yedeği.','entegrasyon-sms.html'),
      ('cart','Pazaryerleri','Trendyol, Hepsiburada ve N11’de yedek parça satışı.','entegrasyon-pazaryeri.html'),
      ('card','Ödeme (iyzico)','Web sitenizden ve ödeme linkiyle kartla tahsilat.','entegrasyon-odeme.html'),
      ('search','Google ve form akışı','Search Console, randevu formları, canlı destek.','entegrasyon-google.html'),
      ('upload','Excel aktarımı','Mevcut müşteri ve cihaz kayıtlarınızı biz taşırız.','entegrasyon-excel.html'),
      ('receipt','E-arşiv fatura','Kendi entegratörünüzle bağlanır (Kurumsal paket).','cozum-odeme-fatura.html')]))
    qa=[('Kendi SMS hesabım olmak zorunda mı?','Mesaj göndermek için bir SMS sağlayıcı hesabınız olmalı. Hesabınız yoksa kurulum sırasında hangisini seçeceğinizi birlikte belirleriz.'),('Pazaryeri bağlantısı zorunlu mu?','Hayır. Yedek parça satmak istemiyorsanız bu bölüm kapalı kalır, panelde görünmez.'),('Bağlantıları kim kuruyor?','Hesap bilgilerinizi siz girersiniz; kurulumda gerekirse birlikte yaparız.')]
    body+=sec(head('Sık sorulanlar','Entegrasyon hakkında','')+faq(qa))
    body+=cta('Servis işinizi bu hafta düzene sokalım')
    page('entegrasyonlar.html','Entegrasyonlar: SMS, pazaryeri, ödeme','SMS sağlayıcıları, pazaryerleri, iyzico ödeme ve Google bağlantıları. Servis panelinizden ayarlanır.',body,faq_ld(qa))
def sub_ent():
    for fn,title,lede,vis,strp,blocks,qa,rel in ENT:
        plain=title.replace('<em>','').replace('</em>','')
        body=hero([('entegrasyonlar.html','Entegrasyonlar'),(None,plain.split(':')[0][:30])],title,lede,vis,['Hesap bilgilerini siz girersiniz'])
        body+=strip(strp)
        for b in blocks: body+=split(*b)
        body+=sec(head('Sık sorulanlar','Aklınıza takılanlar','')+faq(qa))
        body+=sec(head('Birlikte kullanın','İlgili sayfalar','')+related(rel))
        body+=cta()
        page(fn,plain,lede[:155],body,faq_ld(qa))
ent('entegrasyon-sms.html','Mesajlar <em>kendi hesabınızdan</em> gitsin','Netgsm, Verimor, İleti Merkezi ve Twilio hesabınızı panele girin; ya da kendi webhook’unuzu bağlayın. Randevu, usta yolda, servis tamamlandı gibi adımlarda mesaj gider.',
 mk_list('SMS sağlayıcı',[('İleti Merkezi','Bakiye sorgusu başarılı','Bağlı','g'),('Netgsm','Hesap bilgisi bekleniyor','Hazır',''),('Verimor','Hesap bilgisi bekleniyor','Hazır',''),('Twilio','İsteğe bağlı','Hazır','')]),
 [('5','bağlantı seçeneği'),('4','hazır şablon'),('Yedek','WhatsApp → SMS'),('Kayıt','her mesaj saklanır')],
 [('Bağlantı','Sağlayıcınızı bağlayın','Hesap bilgilerinizi panele girin; mesajlar sizin hesabınızdan gider. İleti Merkezi bağlantısı bakiye sorgusuyla gerçekten test edilir.',['Netgsm, Verimor, İleti Merkezi, Twilio, özel webhook','Bağlantı testi bakiye sorgusuyla yapılır','Mesaj ücreti sağlayıcınıza ait'],mk_kv('Bağlantı testi',[('Sağlayıcı','İleti Merkezi'),('Bakiye','Sorgulandı'),('Durum','Bağlı')],'Test')),
  ('Adımlar','Hangi adımda mesaj gitsin, siz seçin','Randevu, usta yolda, servis tamamlandı gibi adımları siz seçersiniz. Metinleri düzenler, değişkenlerle kişiselleştirirsiniz.',['Adım bazında açma ve kapama','Müşteri adı, usta, saat değişkenleri','WhatsApp iletilemezse SMS yedeği (ayardan açılır)'],mk_toggles('Mesaj adımları',[('Usta atandı',True),('Yola çıktı',True),('Tamamlandı',True),('Memnuniyet anketi',True)],'Ayarlar'),True)],
 [('Hangi sağlayıcıyı seçmeliyim?','Mevcut hesabınız varsa onu bağlayın. Yoksa kurulum sırasında birlikte karar veririz.'),('Mesaj hatalarında ne olur?','Gönderim hatası servis işlemini aksatmaz; hata kayıt altına alınır.')],
 [('cozum-sms-bildirimleri.html','SMS bildirimleri','Mesaj akışı'),('entegrasyonlar.html','Tüm entegrasyonlar','Genel bakış'),('cozum-pazarlama.html','Pazarlama araçları','Toplu mesaj')])
ent('entegrasyon-pazaryeri.html','Yedek parçayı <em>pazaryerlerinde</em> satın','Trendyol, Hepsiburada ve N11 için ürün listenizi tek panelden yönetin. Stok ve fiyat ürün kartından yönetilir.',
 mk_list('Pazaryeri bağlantıları',[('Trendyol','Yedek parça ürünleri','Hazır','g'),('Hepsiburada','Stok ve fiyat','Hazır','g'),('N11','Aynı ürün listesi','Hazır','g')]),
 [('3','pazaryeri'),('Tek','ürün listesi'),('Sihirbaz','ile kurulum'),('Stok','servis kaydıyla ortak')],
 [('Ürünler','Bir kez girin, her yerde kullanın','Ürün listeniz tek; Trendyol, Hepsiburada ve N11 için ayrı ayrı girmeniz gerekmez. Stok servis kaydıyla ortak çalışır.',['Trendyol: ürünleri tek panelden yönetin','Hepsiburada: stok ve fiyat ürün kartından','N11: aynı ürün listesi'],mk_kv('Ürün kartı',[('Ürün','Basınç sensörü'),('Stok','14'),('Fiyat','650 ₺'),('Pazaryerleri','Trendyol · Hepsiburada · N11')],'Ürün')),
  ('Kurulum','Kurulum sihirbazıyla birkaç dakikada','Pazaryeri bağlantısı panelde kurulum sihirbazıyla yapılır; hesap bilgilerinizi siz girersiniz. Satmak istemiyorsanız bölüm kapalı kalır.',['Kurulum sihirbazı','Hesap bilgilerini siz girersiniz','Zorunlu değil, istemezseniz görünmez'],mk_toggles('Pazaryeri bağlantısı',[('Trendyol',True),('Hepsiburada',True),('N11',False)],'Ayarlar'),True)],
 [('Pazaryeri komisyonunu hesaplayabilir miyim?','Evet, ücretsiz komisyon hesaplama aracımızı kullanabilirsiniz.'),('Siparişler nereye düşer?','Pazaryeri siparişlerini pazaryeri panelinizden yönetirsiniz; ürün ve stok bilgisi tek listeden gelir.')],
 [('komisyon-hesaplama.html','Komisyon hesaplama','Ücretsiz araç'),('cozum-yedek-parca-magazasi.html','Yedek parça mağazası','Stok ve satış'),('entegrasyonlar.html','Tüm entegrasyonlar','Genel bakış')])
ent('entegrasyon-odeme.html','Siteden ve linkle <em>kartla ödeme</em>','iyzico bilgilerinizi panele girin; web sitenizde ve müşteriye gönderdiğiniz ödeme linkinde kartla tahsilat açılır. Alan boşken ödeme düğmesi görünmez.',
 mk_kv('Ödeme linki',[('Servis','SV-1043'),('Tutar','1.150 ₺'),('Yöntem','Kart · iyzico'),('Durum','Ödendi')],'Örnek'),
 [('iyzico','ödeme altyapısı'),('Link','ile tahsilat'),('Oto','tahsilat kaydı'),('Kasa','takibinde görünür')],
 [('Kurulum','Bilgilerinizi girin, düğme açılsın','iyzico hesabınızın bilgilerini panele girersiniz. Alan boşken ödeme düğmesi sitede görünmez, doldurunca açılır.',['iyzico bilgilerini panelden girin','Alan boşsa ödeme düğmesi gizli','Kendi hesabınıza tahsil edersiniz'],mk_toggles('Ödeme ayarları',[('iyzico ile kart ödemesi',True),('Ödeme linki (SMS)',True)],'Ayarlar')),
  ('Tahsilat','Servis tahsilatı kasada görünür','Usta tahsilat tutarını fişe işler; kasa takibinde görünür. Kurumsal pakette ödeme gelince servis kaydı kapanır, e-arşiv fatura hazırlanır.',['Servis fişinde tahsilat','Kasa takibinde usta bazında görünür','Kurumsal pakette ödeme linki ve e-arşiv'],mk_list('Tahsilat',[('SV-1043','1.150 ₺ · Kart','Ödendi','g'),('SV-1042','850 ₺ · Nakit','Tahsil edildi','g')]),True)],
 [('iyzico hesabım yoksa?','Önce iyzico’dan işletme hesabı açmanız gerekir; kurulumda yönlendiririz.'),('Komisyonu kim ödüyor?','Ödeme sağlayıcı komisyonu iyzico ile aranızdaki sözleşmeye bağlıdır.')],
 [('cozum-odeme-fatura.html','Ödeme ve e-arşiv fatura','Kurumsal modül'),('cozum-kasa-muhasebe.html','Kasa ve muhasebe','Tahsilat'),('entegrasyonlar.html','Tüm entegrasyonlar','Genel bakış')])
ent('entegrasyon-google.html','Talepler <em>tek panelde</em> toplansın','Web sitenizin randevu ve servis formları, canlı destek mesajları firmanızın panelinde birleşir. Search Console ile sitenizin arama performansını panelden izlersiniz.',
 mk_list('Gelen talepler',[('Ahmet Yıldız · Kombi','Web sitesi formu','Yeni','b'),('Selma Er · Beyaz eşya','Canlı destek','Arandı','g'),('Fatma Kurt · Klima','Web sitesi formu','Yeni','b')]),
 [('3','kaynak: form, canlı destek, telefon'),('GSC','arama performansı'),('Tek','panel'),('KVKK','metni formda')],
 [('Form akışı','Her talep kaybolmadan size ulaşsın','Randevu, servis formu ve canlı destek mesajları firmanın kendi panelinde toplanır. Bir talep iki yerde kaybolmaz.',['Web sitesi formları panele düşer','Canlı destek mesajları panelde','Form altında KVKK bilgilendirmesi'],mk_kv('Randevu talebi',[('Ad','Ahmet Yıldız'),('Telefon','0532 *** ** 40'),('Sorun','Kombi çalışmıyor'),('Kaynak','Web sitesi')],'Yeni')),
  ('Google','Arama performansını panelden izleyin','Google Search Console bağlantısıyla sitenizin hangi aramalarda göründüğünü panelden takip edersiniz.',['Search Console bağlantısı','Arama performansı panelde','SEO başlık ve açıklama ayarları'],mk_bars('Arama performansı',[('Kombi servisi',70,'Liste'),('Kombi arıza',50,'Liste'),('Servis ücreti',30,'Liste')]),True)],
 [('Search Console nasıl bağlanır?','Kurulumda site sahipliğini birlikte doğrularız.'),('Canlı destek zorunlu mu?','Hayır, istediğinizde açıp kapatırsınız.')],
 [('cozum-web-sitesi.html','Web sitesi','Randevu formu'),('temalar.html','Temalar','38 hazır tema'),('entegrasyonlar.html','Tüm entegrasyonlar','Genel bakış')])
ent('entegrasyon-excel.html','Mevcut kayıtlarınızı <em>biz taşırız</em>','Defter, Excel ya da başka programdaki müşteri ve cihaz kayıtlarınızı sizin için panele aktarıyoruz. İlk günden geçmişinizle başlarsınız.',
 mk_list('Aktarım',[('Müşteriler','Excel dosyanızdan','Aktarıldı','g'),('Cihazlar','Marka ve model eşleşti','Aktarıldı','g'),('Servis geçmişi','İsteğe bağlı','Planlandı','y')]),
 [('Excel','dosyasından'),('Biz','yaparız'),('Cihaz','bazında eşleşme'),('İlk gün','geçmişle başlayın')],
 [('Aktarım','Sıfırdan başlamayın','Müşteri ve cihaz kayıtlarınızı Excel dosyası olarak gönderin; biz sütunları eşleştirip panele aktaralım. Eksik ve tekrar eden kayıtları birlikte temizleriz.',['Müşteri ve cihaz kayıtları aktarımı','Sütun eşleştirme ve temizlik','Dışa aktarma: raporlar Excel’e iner'],mk_kv('Aktarım özeti',[('Kaynak','Excel dosyası'),('Eşleşen sütun','Ad, telefon, adres, cihaz'),('Durum','Hazır')],'Aktarım')),
  ('Dışa aktarma','Verileriniz size ait','Raporları ve kasa kayıtlarını Excel’e aktarabilirsiniz. Muhasebeciye vermek ya da başka araçta kullanmak serbesttir.',['Raporlar Excel’e aktarılır','Kasa ve cari kayıtlar dışa aktarılır','Verileriniz firmanıza ait'],mk_toggles('Dışa aktarma',[('Rapor',True),('Kasa',True),('Müşteri listesi',True)],'Aktar'),True)],
 [('Dosyam düzensizse?','Sorun değil; eşleştirme ve temizliği birlikte yaparız.'),('Aktarım nasıl yapılıyor?','Dosyanızı gönderirsiniz, sütunları birlikte eşleştirir ve aktarımı kurulum sürecinde biz yaparız; ayrıntıyı görüşmede netleştiririz.')],
 [('baslangic-rehberi.html','Başlangıç rehberi','İlk gün'),('karsilastirma.html','Defter ve Excel ile fark','Karşılaştırma'),('entegrasyonlar.html','Tüm entegrasyonlar','Genel bakış')])
