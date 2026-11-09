from rich import *
S=[]  # (fn,...)
def sol(fn,title,lede,pack,vis,strp,blocks,stp,qa,rel,fine=None,k='Çözümler',crumb=None):
    S.append(dict(fn=fn,title=title,lede=lede,pack=pack,vis=vis,strp=strp,blocks=blocks,stp=stp,qa=qa,rel=rel,fine=fine,crumb=crumb or title.replace('<em>','').replace('</em>','')))
# ---------- ÇEKİRDEK ----------
sol('cozum-servis-kaydi.html','Müşteriden fişe <em>tek kayıt</em>','Her iş için tek kayıt açın. Müşteri, cihaz, arıza, randevu ve usta aynı formda; süreç adımları, fotoğraf ve imza kuralları sizin ayarınızla çalışır.','Başlangıç pakette',
 mk_list('Servis kayıtları',[('SV-1043 · Ayşe Yılmaz','Kombi · Basınç düşüyor','Yolda','b'),('SV-1042 · Murat Şen','Klima · Soğutmuyor','Başladı','y'),('SV-1041 · Zeynep Aras','Çamaşır makinesi · Su almıyor','Tamamlandı','g'),('SV-1040 · Hasan Kaya','Kombi · Petek ısınmıyor','Yeni','')]),
 [('7','iş durumu'),('2','fiş boyutu'),('3','kayıt kuralı: fotoğraf, imza, form'),('8','sektöre hazır şablon')],
 [('Kayıt','Sahada kayıt değil, sistemde kayıt','Telefonda not alıp sonra deftere geçirmek bitiyor. Müşteri aradığında ya da formdan geldiğinde kayıt açılır; müşteri, cihaz ve arıza birlikte tutulur.',['Müşteri, cihaz, arıza ve randevu tek formda','Marka ve model kataloğundan seçim (kataloğu önceden siz hazırlarsınız)','Atölyeye alma ve “müşteri vazgeçti” durumları'],
   mk_kv('Yeni servis kaydı',[('Müşteri','Ayşe Yılmaz'),('Telefon','0532 *** ** 18'),('Cihaz','Kombi · Baymak'),('Arıza','Basınç düşüyor'),('Randevu','Yarın 11:00–13:00'),('Usta','Hasan')],'SV-1043')),
  ('Akış','Her işin hangi adımda olduğunu bilin','Yeni, Atandı, Yolda, Başladı, Tamamlandı, Faturalandı, İptal: işin konumu tek bakışta görünür. Gecikenleri siz aramadan fark edersiniz.',['Duruma göre akış ve renkli durum etiketleri','İşlem öncesi ve sonrası fotoğraf: zorunlu, isteğe bağlı ya da kapalı','Müşteri ve usta imzası ayrı ayrı açılır, kapatılır'],
   mk_toggles('Servis ayarları',[('Önce fotoğraf zorunlu',True),('Sonra fotoğraf zorunlu',True),('Müşteri imzası',True),('Usta imzası',False),('Parça ve işçilik formu',True),('Memnuniyet anketi',True)],'Ayarlar'),True),
  ('Sektör','Sektörünüze göre hazır gelir','Kombi, klima, beyaz eşya, elektronik, bilgisayar, tesisat, elektrik ve güvenlik için marka, model ve kontrol listesi hazır kurulur.',['Sektöre göre hazır kontrol listeleri','Parça, işçilik ve ödeme yöntemi girişi','Fişte KVKK aydınlatma metni otomatik'],
   mk_list('Kontrol listesi · Kombi',[('Su basıncı kontrolü','1,2 bar','Tamam','g'),('Baca gazı çıkışı','Gözle kontrol','Tamam','g'),('Genleşme tankı','Basınç testi','Bekliyor','y'),('Petek havası','Alındı','Tamam','g')]))],
 [('Kaydı açın','Müşteri, cihaz, arıza ve randevuyu girin.'),('Ustayı atayın','İş seçtiğiniz ustanın telefonuna düşer.'),('Usta işi yapsın','Fotoğraf, imza ve parça telefondan girilir.'),('Fiş hazır','İş bitince imzalı PDF fiş oluşur.')],
 [('Hangi bilgileri zorunlu yapabilirim?','Fotoğraf ve imza adımlarını Servis Ayarları’ndan zorunlu, isteğe bağlı ya da kapalı yaparsınız. Her firma kendi sürecini kurar.'),('Marka ve model listesi hazır mı?','Sektörünüze göre başlangıç şablonu kurulur. Listeyi siz düzenler, eksik markayı kendiniz eklersiniz.'),('Mevcut kayıtlarımı taşıyabilir miyim?','Evet. Müşteri ve cihaz kayıtlarınızı Excel’den biz aktarırız.')],
 [('usta-uygulamasi.html','Usta uygulaması','Sahada kayıt'),('cozum-pdf-servis-fisi.html','PDF servis fişi','İmzalı fiş'),('cozum-sms-bildirimleri.html','SMS bildirimleri','Müşteri bilgilensin')])
sol('cozum-sms-bildirimleri.html','Müşteri aramadan <em>bilgilensin</em>','Usta atandığında, yola çıktığında ve iş bittiğinde müşteriye otomatik mesaj gider. Metinleri siz yazarsınız, mesajlar kendi SMS hesabınızdan çıkar.','Profesyonel pakette',
 mk_chat('Müşteriye giden mesajlar',[('Usta atandı','Sayın Ayşe Yılmaz, ustamız Hasan 11:00–13:00 arasında gelecektir.',False),('Yola çıktı','Ustamız yola çıktı. Canlı takip: ok.link/xyz',False),('Tamamlandı','Servisiniz tamamlandı. İmzalı fişiniz ektedir.',True)]),
 [('4','hazır mesaj şablonu'),('5','SMS sağlayıcı seçeneği'),('1','kayıt: her mesaj saklanır'),('Hata','işi durdurmaz, kayda geçer')],
 [('Şablonlar','Mesajı siz yazın, değişkenler otomatik dolsun','Usta atandı, yolda, tamamlandı ve memnuniyet anketi için şablonlar hazır gelir. Müşteri adı, usta adı, saat gibi değişkenleri metne eklersiniz.',['Mesaj şablonları: usta atandı, yolda, tamamlandı, anket','Müşteri adı, usta, saat gibi değişkenler','Gönderilen her mesaj kayıt altında'],
   mk_kv('Mesaj şablonu · Usta atandı',[('Metin','Sayın {musteri}, ustamız {usta} {saat} arasında gelecektir.'),('Gönderim','Atama anında'),('Kanal','SMS'),('Durum','Açık')],'Şablon')),
  ('Sağlayıcı','Kendi SMS firmanızı bağlayın','İleti Merkezi, Verimor, Netgsm, Twilio ya da özel webhook. Bağlantı kurulurken bakiye sorgusuyla gerçekten test edilir.',['İleti Merkezi bağlantısı bakiye sorgusuyla test edilir','Hata olursa servis işlemi aksamaz, kayıt tutulur','WhatsApp iletilemezse SMS yedeği (ayardan açılır)'],
   mk_list('SMS sağlayıcı',[('İleti Merkezi','Bakiye sorgusu başarılı','Bağlı','g'),('Netgsm','Hesap bilgisi girilmedi','Kapalı',''),('Verimor','Hesap bilgisi girilmedi','Kapalı',''),('Özel webhook','İsteğe bağlı','Kapalı','')]),True)],
 [('Şablonu düzenleyin','Metni kendi dilinizle yazın.'),('Sağlayıcıyı bağlayın','SMS hesabınızı panele girin.'),('Adımı seçin','Hangi adımda mesaj gitsin, siz belirleyin.'),('Kaydı izleyin','Her mesajın durumu kayıtta görünür.')],
 [('Kendi SMS hesabım olmak zorunda mı?','Mesaj göndermek için bir SMS sağlayıcı hesabınız olmalı. Hesabınız yoksa kurulumda hangisini seçeceğinizi birlikte belirleriz.'),('SMS ücreti kime ait?','Mesajlar sizin sağlayıcı hesabınızdan gider, ücreti sağlayıcınıza ödersiniz.'),('Mesaj gitmezse iş durur mu?','Hayır. Gönderim hatası servis işlemini aksatmaz, hata kayda geçer.')],
 [('entegrasyon-sms.html','SMS entegrasyonları','Sağlayıcılar'),('cozum-servis-kaydi.html','Servis kaydı','Mesajı tetikleyen adımlar'),('cozum-bakim-garanti.html','Bakım ve garanti','Otomatik hatırlatma')])
sol('cozum-pdf-servis-fisi.html','İmzalı, logolu <em>servis fişi</em>','İş bittiğinde fiş otomatik hazırlanır. A4 ve 80 mm termal boyutu, logonuz, metinleriniz ve KVKK aydınlatma metniyle birlikte.','Başlangıç pakette',
 mk_receipt(['EGE KOMBİ SERVİS','Fiş no: SV-1043 · 12.11.2026','-',('Basınç sensörü','650 ₺'),('İşçilik','500 ₺'),'-',('TOPLAM','1.150 ₺'),('Ödeme','Kart'),'-','Müşteri imzası']),
 [('2','boyut: A4 ve 80 mm'),('1','dokunuşta müşteriye gönderim'),('KVKK','metni fişte otomatik'),('Logo','ve metinler size ait')],
 [('Tasarım','Fiş sizin firmanız gibi görünsün','Logo, firma bilgileri, alt metin ve garanti şartlarını düzenlersiniz. Aynı tasarım hem A4 hem 80 mm termal çıktıda kullanılır.',['A4 ve 80 mm PDF servis fişi','Logo, başlık ve alt metin düzenlenebilir','Fişte KVKK aydınlatma metni otomatik'],
   mk_toggles('Fiş tasarımı',[('Logo göster',True),('Garanti şartları',True),('KVKK aydınlatma metni',True),('Müşteri imza alanı',True),('Usta imza alanı',False)],'Düzenle')),
  ('Dağıtım','İş biter bitmez müşteride','Usta işi tamamlayınca fiş PDF olarak oluşur, müşteriye gönderilir. Kâğıda dökmek isterseniz termal yazıcıdan çıktı alırsınız.',['İşi tamamlayınca fiş otomatik hazırlanır','Müşteriye SMS ile bağlantı olarak gider','Parça, işçilik ve ödeme yöntemi fişte görünür'],
   mk_chat('Müşteriye giden',[('SMS','Servisiniz tamamlandı. İmzalı fişiniz ektedir.',True),('Müşteri','Fişi açtı',False)]),True)],
 [('İşi tamamlayın','Usta parça ve işçiliği girer.'),('İmza alın','Müşteri telefon ekranına imzalar.'),('Fiş oluşsun','PDF otomatik hazırlanır.'),('Gönderin','Müşteriye bağlantı gider.')],
 [('Fiş tasarımını ben değiştirebilir miyim?','Evet. Başlık, alt metin ve logoyu Servis Ayarları’ndan düzenlersiniz.'),('Termal yazıcıyla çalışır mı?','80 mm boyutlu PDF çıktı veriyoruz; 80 mm destekleyen yazıcıdan alabilirsiniz.'),('KVKK metnini kim yazıyor?','Fişte aydınlatma metni otomatik yer alır. Kendi firmanıza göre düzenleyebilirsiniz.')],
 [('blog-servis-fisi-nasil-hazirlanir.html','Servis fişi nasıl hazırlanır?','Rehber'),('servis-fisi-sablonu.html','Fiş önizleme aracı','Ücretsiz araç'),('cozum-servis-kaydi.html','Servis kaydı','Fişin kaynağı')])
sol('cozum-kasa-muhasebe.html','Kim ne kadar tahsil etti, <em>anında</em> görün','Tahsilat, gider ve cari takip servis kayıtlarına bağlı çalışır. Usta bazında kasa, nakit-kart-havale ayrımı ve ödeme bekleyen işler tek ekranda.','Profesyonel pakette',
 mk_kv('Bugünkü kasa',[('Hasan · nakit','2.350 ₺'),('Murat · kart','1.900 ₺'),('Selim · havale','1.150 ₺'),('Gider','–640 ₺'),('Ödeme bekleyen','3 iş')],'Örnek',('Net kasa','4.760 ₺')),
 [('3','ödeme yöntemi ayrımı'),('Usta','bazında kasa'),('Excel','dışa aktarma'),('Cari','hesap ve alacak')],
 [('Kasa','Ustaların topladığı parayı kayıtla eşleyin','Usta tahsilatı fişe işler, kasa takibinde görünür. Hangi ustanın hangi işte ne kadar tahsil ettiği açık olur.',['Usta bazında kasa ve tahsilat','Nakit, kart ve havale ayrımı','Ödeme bekleyen servislerin listesi'],
   mk_list('Tahsilat',[('SV-1043 · Hasan','1.150 ₺ · Kart','Tahsil edildi','g'),('SV-1042 · Murat','850 ₺ · Nakit','Tahsil edildi','g'),('SV-1039 · Selim','1.400 ₺','Bekliyor','y')])),
  ('Gider ve cari','Gelir kadar gideri de tutun','Gider kayıtlarını kategoriye göre girin, cari hesap ve alacakları servis kayıtlarına bağlı izleyin. Faturalanmamış tamamlanan işler ayrıca listelenir.',['Gider kayıtları ve kategoriler','Cari hesap ve alacak takibi','Kâr takibi ve Excel’e aktarma'],
   mk_bars('Gider dağılımı · Kasım',[('Yedek parça',72,'72%'),('Yakıt',16,'16%'),('Diğer',12,'12%')]),True)],
 [('Servis tahsilatı','Usta fişe tahsilatı işler.'),('Kasa görünümü','Yönetici ustaya göre toplamı görür.'),('Gider girişi','Gider kaydı kategoriyle tutulur.'),('Dışa aktarma','Muhasebeci için Excel çıktısı.')],
 [('Resmî muhasebe programının yerini tutar mı?','Hayır. Kasa ve cari takibi servis işinizi yönetmek içindir; resmî muhasebe için Excel çıktısını muhasebecinize verirsiniz.'),('Kart tahsilatı panelden mi alınıyor?','Kurumsal pakette müşteriye ödeme linki gider ve tahsilat otomatik işlenir. Diğer paketlerde usta ödeme yöntemini fişe işler.')],
 [('cozum-raporlar.html','Raporlar','Ciro ve performans'),('cozum-odeme-fatura.html','Ödeme ve e-arşiv fatura','Online tahsilat'),('entegrasyon-excel.html','Excel aktarımı','Veri taşıma')])
sol('cozum-raporlar.html','Kararlarınızı <em>rakamla</em> verin','Aylık ciro, usta bazında iş sayısı, açık ve geciken işler için hazır raporlar. Defter karıştırmadan, hangi ustanın ne kadar iş çıkardığını görün.','Profesyonel pakette',
 mk_bars('Usta performansı · Kasım',[('Hasan',88,'44 iş'),('Murat',70,'35 iş'),('Selim',56,'28 iş'),('Eda',40,'20 iş')]),
 [('4','hazır rapor grubu'),('Usta','bazında kırılım'),('Servis','türüne göre dağılım'),('Excel','dışa aktarma')],
 [('Ciro','Ay sonunu beklemeden ciroyu görün','Aylık ciro ve tahsilat özeti güncel kayıtlardan çıkar. Hangi hafta güçlü, hangisi zayıf; bir bakışta anlaşılır.',['Aylık ciro ve tahsilat özeti','Servis türüne göre dağılım','Tamamlanma süreleri'],
   mk_bars('Haftalık ciro',[('1. hafta',62,'12.4k ₺'),('2. hafta',78,'15.6k ₺'),('3. hafta',51,'10.2k ₺'),('4. hafta',90,'18.0k ₺')])),
  ('Operasyon','Açık ve geciken işleri kaçırmayın','Hangi iş kaç gündür açık, kim üzerinde, hangisi gecikti. Rapor ekranı sabah toplantısının gündemini kendisi çıkarır.',['Açık ve geciken işler','Usta bazında iş sayısı ve performans','Raporları dışa aktarma'],
   mk_list('Geciken işler',[('SV-1031 · Kombi','4 gündür açık · Selim','Gecikti','r'),('SV-1035 · Klima','2 gündür açık · Murat','Açık','y'),('SV-1038 · Beyaz eşya','1 gündür açık · Hasan','Açık','y')]),True)],
 [('Kayıt tutun','İşler sistemde olunca rapor kendiliğinden oluşur.'),('Raporu açın','Dönemi ve ustayı seçin.'),('İnceleyin','Gecikenlere ve yükü fazla ustaya bakın.'),('Aktarın','Excel’e aktarıp paylaşın.')],
 [('Raporlar anlık mı?','Raporlar servis kayıtlarından hesaplanır; kayıt güncellendikçe rakamlar güncellenir.'),('Raporu ustaya göstermek zorunda mıyım?','Hayır. Usta yalnızca kendine atanan işleri görür, raporlar yönetici yetkisindedir.')],
 [('cozum-kasa-muhasebe.html','Kasa ve muhasebe','Tahsilat'),('cozum-personel-takibi.html','Personel takibi','Ekip yönetimi'),('blog-usta-performans-takibi.html','Usta performansı nasıl ölçülür?','Rehber')])
sol('cozum-personel-takibi.html','Ekibiniz <em>düzenli</em> çalışsın','Usta ve personel için ayrı giriş, ayrı yetki. Usta yalnızca kendine atanan işi görür; yönetici günlük iş yükünü atama ekranında izler.','Başlangıç pakette',
 mk_list('Ekip · bugün',[('Hasan Kaya','3 iş · 1 yolda','Sahada','b'),('Murat Şen','2 iş','Sahada','b'),('Selim Acar','Atölyede','Atölye','y'),('Eda Tan','İzinli','İzinli','')]),
 [('2','rol: yönetici ve usta'),('1','telefon, 1 giriş'),('Günlük','iş yükü görünür'),('Ayrı','yetki ayarları')],
 [('Yetki','Herkes yalnızca işinin gördüğünü görsün','Usta kendi telefonundan giriş yapar, yalnızca kendine atanan işleri görür. Raporlar, kasa ve ayarlar yönetici yetkisindedir.',['Usta ekleme ve kullanıcı yönetimi','Yönetici ve usta için ayrı yetkiler','Usta kendi işlerini Aktif, Tamamlanan ve Atölye listelerinde görür'],
   mk_toggles('Usta yetkileri',[('Kendi işlerini görür',True),('Tüm işleri görür',False),('Kasa ve rapor',False),('Parça girişi',True),('Tahsilat girişi',True)],'Rol: Usta')),
  ('İş yükü','Atamadan önce kimin ne kadar yüklü olduğunu görün','Atama ekranı her ustanın günlük iş yükünü gösterir. Kurumsal pakette konum, uzmanlık ve iş yüküne göre usta önerisi de gelir.',['Atama ekranında ustanın günlük iş yükü','İş bitince fiş otomatik hazırlanır','Kurumsal pakette otomatik atama önerisi'],
   mk_bars('Bugünkü iş yükü',[('Hasan',75,'3 iş'),('Murat',50,'2 iş'),('Selim',25,'1 iş')]),True)],
 [('Usta ekleyin','Ad, telefon ve rol girin.'),('Yetkiyi seçin','Ne görebileceğini belirleyin.'),('İş atayın','Yükü görerek atama yapın.'),('Takip edin','Tamamlanan işleri izleyin.')],
 [('Usta uygulamayı indirecek mi?','Hayır. Usta telefonunun tarayıcısından girer, ana ekrana ekleyerek uygulama gibi kullanır.'),('Usta ayrılırsa verisi ne olur?','Kullanıcıyı kapatırsınız; geçmiş servis kayıtları firmanızda kalır.')],
 [('usta-uygulamasi.html','Usta uygulaması','Sahada çalışma'),('cozum-otomatik-atama.html','Otomatik atama','Kurumsal modül'),('cozum-raporlar.html','Raporlar','Performans')])
sol('cozum-musteri-portali.html','Müşteri servisini <em>kendisi takip etsin</em>','Müşteri telefon numarası ve SMS koduyla girer; servislerini, tutarlarını ve bekleyen tekliflerini görür. Siz “Ne zaman gelecek?” telefonlarından kurtulursunuz.','Kurumsal pakette',
 mk_list('Müşteri portalı · Ayşe Yılmaz',[('Kombi · Basınç düşüyor','Randevu: yarın 11:00–13:00','Yolda','b'),('Kombi bakımı','Tamamlandı · 1.150 ₺','Ödendi','g'),('Teklif TK-218','Basınç sensörü 1.150 ₺','Onay bekliyor','y')],'Müşteri'),
 [('SMS','kodu ile güvenli giriş'),('Canlı','servis durumu'),('Tek','dokunuşla servis talebi'),('Teklif','onay ve ödeme')],
 [('Takip','Servis durumunu müşteri izler','Randevu, usta yolda ve tamamlandı bilgileri portalda görünür. Müşteri servis takip bağlantısıyla aynı bilgiye ulaşır.',['Servis durumu ve randevu bilgisi','Servis takip bağlantısı','Yeni servis talebi oluşturma'],
   phone('Servislerim',[('Kombi · Basınç düşüyor','Yarın 11:00–13:00 · Usta Hasan','Canlı takip',False),('Teklif TK-218','1.150 ₺','Onayla',False)])),
  ('Karar','Teklifi onaylasın, ödemesini yapsın','Müşteri teklifi portaldan onaylar ya da reddeder, ödeme linkiyle borcunu kapatır. İş telefon trafiğine takılmaz.',['Teklif onayı ve ödeme','Karar tarihi ve saati kayıtta','Web sitenizdeki “Müşteri portalı” bağlantısıyla açılır'],
   mk_kv('Teklif TK-218',[('Basınç sensörü','650 ₺'),('İşçilik','500 ₺'),('Karar','Onay bekliyor')],'Müşteri',('Toplam','1.150 ₺')),True)],
 [('Müşteri girer','Telefon numarasını yazar.'),('SMS kodu','Kodu girerek doğrular.'),('Servislerini görür','Durum, tutar, teklif.'),('Talep açar','Yeni servis talebi oluşturur.')],
 [('Müşteri şifre mi hatırlayacak?','Hayır. Telefon numarası ve SMS koduyla giriş yapar.'),('Web sitem varsa bağlanır mı?','Evet. Tema menüsündeki “Müşteri portalı” bağlantısı firmanızın portal adresini açar.')],
 [('cozum-teklif-onay.html','Teklif ve onay','Müşteri kararı'),('cozum-web-sitesi.html','Web sitesi','Portal bağlantısı'),('cozum-sms-bildirimleri.html','SMS bildirimleri','Mesajlar')])
sol('cozum-web-sitesi.html','Hazır temalı <em>web siteniz</em>','30 hazır temadan birini seçin; randevu formu, SEO ayarları ve müşteri portalı bağlantısıyla yayına alın. Gelen talepler doğrudan servis panelinize düşer.','Tam Pakette',
 '<div class="mk"><div class="bar"><i></i><i></i><i></i><b>ege-kombi.com</b></div><img src="tema/1-kombi-k.webp" alt="Kombi temasından bir ekran" style="display:block;width:100%;height:auto"></div>',
 [('30','hazır tema'),('8','sektör'),('Form','talepler panele düşer'),('SEO','başlık ve açıklama ayarı')],
 [('Tema','Sektörünüze uygun temayı seçin','Her tema kendi rengi, köşesi ve yazı tipiyle gelir. Bölümleri panelden düzenler, fotoğraf ve yazıları istediğiniz zaman değiştirirsiniz.',['30 sektöre uygun, mobil uyumlu tema','Temayı istediğiniz zaman değiştirme; yazı ve fotoğraflar yeni temaya taşınır','Medya (fotoğraf) yöneticisi'],
   '<div class="mk"><div class="bar"><i></i><i></i><i></i><b>Tema seçimi</b></div><img src="tema/22-tesisat-sari-k.webp" alt="Tesisat teması" style="display:block;width:100%;height:auto"></div>',False,('temalar.html','Tüm temaları gör')),
  ('Talep','Siteden gelen her talep panelde','Randevu formundan gelen talepler servis panelinize kaydolur. Ziyaretçi takibi ve müşteri yorumu ayarları da panelden yönetilir.',['Randevu talebi formu: talepler panele düşer','SEO başlık ve açıklama ayarları','Ziyaretçi takibi ve müşteri yorumu ayarları'],
   mk_list('Gelen talepler',[('Ahmet Yıldız · Kombi','Web sitesi formu','Yeni','b'),('Fatma Kurt · Klima','Web sitesi formu','Yeni','b'),('Selma Er · Beyaz eşya','Canlı destek','Arandı','g')]),True)],
 [('Tema seçin','8 sektörden birini seçin.'),('Bilgileri girin','Firma adı, telefon, logo.'),('Yayına alın','Randevu formuyla birlikte.'),('Talepleri alın','Talepler panele düşer.')],
 [('Alan adımı kullanabilir miyim?','Evet. Kendi alan adınızı bağlarız; yoksa kurulumda birlikte ilerleriz.'),('Temayı sonradan değiştirebilir miyim?','Evet. Yazı ve fotoğraflarınız yeni temaya taşınır.')],
 [('temalar.html','Temalar','30 temayı inceleyin'),('cozum-musteri-portali.html','Müşteri portalı','Site bağlantısı'),('cozum-yedek-parca-magazasi.html','Yedek parça mağazası','Siteden satış')])
sol('cozum-yedek-parca-magazasi.html','Yedek parçayı <em>online satın</em>','Stoktaki yedek parçaları sitenizden satışa açın, servis kayıtlarında parça olarak kullanın. Stok azalınca uyarı gelir.','Tam Pakette',
 mk_list('Yedek parçalar',[('Basınç sensörü','Stok: 14 · 650 ₺','Satışta','g'),('Genleşme tankı','Stok: 3 · 480 ₺','Azalıyor','y'),('Fan motoru','Stok: 0 · 1.250 ₺','Tükendi','r')]),
 [('Stok','takibi ve uyarı'),('Online','sipariş alma'),('3','pazaryeri bağlantısı'),('Tek','ürün listesi')],
 [('Stok','Parça stoğu ve servis kaydı bir arada','Ustanız servis kaydında parçayı stoktan seçer, stok kendiliğinden düşer. Azalan ürün için uyarı alırsınız.',['Parça ve ürün listesi','Servis kaydında parçayı stoktan seçme','Azalan stok uyarısı'],
   mk_kv('Servis kaydı · Parça',[('Parça','Basınç sensörü'),('Stoktan','14 → 13'),('Fiyat','650 ₺')],'SV-1043')),
  ('Satış','Sitenizden ve pazaryerlerinden satın','Stoktaki parçaları web sitenizde sipariş alınır hale getirin. Trendyol, Hepsiburada ve N11 için tek ürün listesi kullanın; bağlantı panelde kurulum sihirbazıyla yapılır.',['Siteden online sipariş alma','Trendyol, Hepsiburada ve N11 ürün listesi','Pazaryeri bağlantısı zorunlu değildir'],
   mk_list('Pazaryeri bağlantıları',[('Trendyol','Ürün kartından yönetim','Hazır','g'),('Hepsiburada','Stok ve fiyat','Hazır','g'),('N11','Aynı ürün listesi','Hazır','g')]),True,('entegrasyon-pazaryeri.html','Pazaryeri bağlantıları'))],
 [('Ürünü ekleyin','Parça adı, stok ve fiyat.'),('Satışa açın','Sitede ve pazaryerinde.'),('Sipariş gelsin','Sipariş panele düşer.'),('Stok düşsün','Servis ve satıştan stok otomatik.')],
 [('Yedek parça satmak zorunda mıyım?','Hayır. Satış istemezseniz bu bölüm kapalı kalır, panelde görünmez.'),('Pazaryeri hesabını kim kuruyor?','Hesap bilgilerinizi siz girersiniz; bağlantı kurulum sihirbazıyla yapılır.')],
 [('entegrasyon-pazaryeri.html','Pazaryerleri','Bağlantılar'),('cozum-web-sitesi.html','Web sitesi','Sipariş sayfası'),('cozum-pazarlama.html','Pazarlama araçları','Müşteri çekin')])
# ---------- KURUMSAL / BÜYÜME ----------
sol('cozum-pazarlama.html','Yeni müşteri çekin, <em>eskisini geri kazanın</em>','Kampanya oluşturun, müşteri listesine toplu mesaj gönderin, büyüme önerilerini görün. Eski müşteriyi aramadan geri kazanın.','Tam Pakette',
 mk_list('Kampanyalar',[('Sonbahar bakım kampanyası','Kombi müşterilerine SMS','Aktif','g'),('Klima öncesi bakım','Hazırlanıyor','Taslak',''),('Eski müşteriyi geri kazan','12 aydır gelmeyenler','Önerilen','y')]),
 [('Toplu','mesaj gönderimi'),('Öneri','büyüme fırsatları'),('Geri','kazanma listesi'),('Tek','panelden yönetim')],
 [('Kampanya','Doğru müşteriye doğru mesaj','Kampanya oluşturur, müşteri listenizden hedef kitleyi seçer, toplu mesaj gönderirsiniz. Kayıtlar müşteri geçmişiyle birleşik olduğu için hedefleme kolaydır.',['Kampanya oluşturma','Müşteri listesine toplu mesaj','Büyüme önerileri ve fırsatlar'],
   mk_chat('Toplu mesaj',[('Taslak','Sonbahar bakımında bu hafta randevu alın, yer kalmadan ayırtın.',True)])),
  ('Geri kazanma','Uzun süredir gelmeyen müşteriyi hatırlayın','Eski müşteriyi geri kazanma aracıyla belirli süredir servis almamış müşteriler listelenir, tek seferde mesaj gider.',['Eski müşteriyi geri kazanma listesi','Servis geçmişine göre hedefleme','Mesajlar SMS sağlayıcınızdan gider'],
   mk_bars('Geri kazanma potansiyeli',[('6 ay+',45,'Liste'),('12 ay+',30,'Liste'),('24 ay+',15,'Liste')]),True)],
 [('Hedef seçin','Müşteri grubunu belirleyin.'),('Mesajı yazın','Şablon ya da kendi metniniz.'),('Gönderin','SMS sağlayıcınızdan çıkar.'),('Randevuyu alın','Talepler panele düşer.')],
 [('Toplu mesaj izinsiz olur mu?','Mesajları göndermeden önce müşteri izni ve ticari ileti mevzuatına uygunluk firmanızın sorumluluğundadır.'),('Mesaj ücreti nasıl?','Mesajlar sizin SMS sağlayıcı hesabınızdan gider.')],
 [('cozum-sms-bildirimleri.html','SMS bildirimleri','Mesaj altyapısı'),('cozum-web-sitesi.html','Web sitesi','Müşteri çekin'),('blog-teknik-servis-musteri-bulma.html','Müşteri bulma yolları','Rehber')])
sol('cozum-bakim-garanti.html','Yıllık bakım gelirini <em>kaçırmayın</em>','Her cihazın bakım tarihi ve garantisi takip edilir. Tarih yaklaşınca müşteri otomatik bilgilendirilir, tek dokunuşla servis talebi açar.','Kurumsal pakette',
 mk_list('Bakım takvimi',[('Ayşe Yılmaz · Kombi','Yıllık bakım','12 gün kaldı','y'),('Murat Şen · Klima','Sezon öncesi','3 gün kaldı','r'),('Zeynep Aras · Kombi','Yıllık bakım','Gecikti','r')]),
 [('Oto','SMS hatırlatma'),('Cihaz','bazında garanti'),('Geciken','bakım listesi'),('1','dokunuşla talep')],
 [('Takvim','Hangi cihazın bakımı ne zaman, bilin','Yıllık bakım hatırlatma listesi ve geciken bakımlar tek ekranda. Tarih gelen müşteriye otomatik SMS gider.',['Yıllık bakım hatırlatma listesi','Bakım zamanı gelen müşteriye SMS','Geciken bakım listesi'],
   mk_chat('Otomatik SMS',[('Hatırlatma','Yıllık kombi bakımınız yaklaşıyor. Randevu için: ok.link/b12',True)])),
  ('Garanti','Garanti bitişini cihaz kartında tutun','Her cihazın garanti bitiş tarihi, servis geçmişi ve garanti talepleri cihaz kartında toplanır.',['Cihaz bazında garanti bitiş tarihi','Cihaz kartı ve servis geçmişi','Garanti talepleri takibi'],
   mk_kv('Cihaz kartı · Kombi',[('Marka / model','Baymak Duotec'),('Garanti bitiş','14.03.2027'),('Son bakım','11.11.2025'),('Servis sayısı','3')],'Cihaz'),True,('garanti-hesaplama.html','Garanti bitiş hesaplama aracı'))],
 [('Cihazı kaydedin','Marka, model, garanti tarihi.'),('Takvim oluşsun','Bakım tarihi hesaplanır.'),('SMS gitsin','Müşteri hatırlatılır.'),('Talep gelsin','Müşteri randevu açar.')],
 [('Bakım aralığını ben mi belirliyorum?','Evet, cihaz türüne göre bakım periyodunu siz ayarlarsınız.'),('Garanti süresini otomatik hesaplar mı?','Garanti bitiş tarihini kaydedersiniz; ücretsiz garanti hesaplama aracımız tarihi bulmanıza yardım eder.')],
 [('cozum-sms-bildirimleri.html','SMS bildirimleri','Mesaj altyapısı'),('blog-garanti-kapsami-servis.html','Garanti kapsamında servis','Rehber'),('cozum-qr-etiket.html','QR etiket','Cihaz kartı')])
sol('cozum-teklif-onay.html','Fiyatı müşteri onaylasın, <em>iş durmasın</em>','Usta parça ve işçilikle teklif hazırlar, müşteri SMS bağlantısından onaylar ya da reddeder. Karar tarih ve saatle kayıtta saklanır.','Kurumsal pakette',
 mk_kv('Teklif TK-218',[('Basınç sensörü','650 ₺'),('İşçilik','500 ₺'),('Durum','Onay bekliyor'),('Müşteriye','SMS gitti')],'Örnek',('Toplam','1.150 ₺')),
 [('2','karar: onay ya da ret'),('SMS','ile onay bağlantısı'),('Saatli','karar kaydı'),('Anında','yöneticiye bildirim')],
 [('Teklif','Sahada hazırlayın, anında gönderin','Usta parça ve işçilik kalemlerini girer, teklif müşteriye bağlantı olarak gider. Kalem kalem görerek karar vermek müşteri için daha rahattır.',['Parça ve işçilikle teklif hazırlama','Müşteriye SMS ile onay linki','Onay ve ret kaydı (tarih, saat)'],
   phone('Teklif hazırla',[('Basınç sensörü','650 ₺','Kalem ekle',True),('İşçilik','500 ₺','Müşteriye gönder',False)])),
  ('Karar','Karar kayıtta, tartışma kapanır','Müşteri onayı ve ret kararı teklif kaydında kalır. Karar geldiğinde yöneticiye bildirim düşer; usta beklemeden işe devam eder.',['Karar bildirimi yöneticiye gider','Onaylanan teklif servis kaydına işlenir','Müşteri portalından da görülebilir'],
   mk_list('Teklif durumları',[('TK-218 · Ayşe Yılmaz','1.150 ₺','Onay bekliyor','y'),('TK-217 · Murat Şen','2.400 ₺','Onaylandı','g'),('TK-216 · Selim Acar','850 ₺','Reddedildi','r')]),True)],
 [('Teklifi hazırlayın','Parça ve işçilik ekleyin.'),('Gönderin','Müşteriye SMS ile gider.'),('Karar gelsin','Onay ya da ret kayda geçer.'),('İşe devam','Onaylanan işe başlanır.')],
 [('Müşteri onaylamazsa ne olur?','Ret kararı kayıtta saklanır, yöneticiye bildirim gider; işe devam edilmez.'),('Teklifi sonra değiştirebilir miyim?','Müşteriye gitmeden önce düzenlersiniz; gittikten sonra yeni teklif hazırlanır.')],
 [('cozum-musteri-portali.html','Müşteri portalı','Teklif ve ödeme'),('cozum-odeme-fatura.html','Ödeme ve e-arşiv','Tahsilat'),('cozum-servis-kaydi.html','Servis kaydı','Kaynak kayıt')])
sol('cozum-odeme-fatura.html','Tahsilatı linkle alın, <em>faturayı otomatik</em> kesin','Müşteriye ödeme linki gider, ödeme gelince servis kapanır ve e-arşiv fatura hazırlanır. Kapıda para takibi yapmanıza gerek kalmaz.','Kurumsal pakette',
 mk_kv('Ödeme linki',[('Servis','SV-1043'),('Tutar','1.150 ₺'),('Durum','Ödendi, kart'),('Fatura','E-arşiv fatura kesildi')],'Örnek'),
 [('Link','ile kartla tahsilat'),('Oto','tahsilat işleme'),('E-arşiv','fatura bağlantısı'),('iyzico','ödeme altyapısı')],
 [('Tahsilat','Linki gönder, parayı al','Müşteriye SMS ile ödeme linki gider. Ödeme geldiğinde servis kaydında tahsilat otomatik işlenir.',['SMS ile ödeme linki','Kredi kartı ile online tahsilat','Ödeme gelince servis kaydında tahsilat işlenir'],
   mk_chat('Ödeme linki',[('SMS','Servis tutarı 1.150 ₺. Güvenli ödeme için: ok.link/pay',True)])),
  ('Fatura','Faturanız hazır gelsin','E-arşiv fatura kendi entegratörünüzle bağlanır; ödeme gelince fatura hazırlığı başlar. Faturalanmamış tamamlanan işler kasada ayrıca listelenir.',['E-arşiv fatura bağlantısı (kendi entegratörünüzle)','Faturalanmamış işler listesi','iyzico bilgilerinizi panele girmeniz yeterli'],
   mk_list('Fatura durumu',[('SV-1043','1.150 ₺','Fatura kesildi','g'),('SV-1042','850 ₺','Bekliyor','y')]),True,('entegrasyon-odeme.html','Ödeme entegrasyonu'))],
 [('Linki gönderin','SMS ile müşteriye gider.'),('Müşteri ödesin','Kartla güvenli ödeme.'),('Kayıt kapansın','Tahsilat işlenir.'),('Fatura hazır','E-arşiv bağlantısı.')],
 [('Hangi ödeme sağlayıcı?','iyzico. Bilgilerinizi panele girersiniz; alan boşken ödeme düğmesi görünmez, doldurunca açılır.'),('Fatura entegratörüm nasıl bağlanır?','Kendi e-arşiv entegratörünüzle bağlanır; kurulumda birlikte yapılır.')],
 [('entegrasyon-odeme.html','Ödeme entegrasyonu','iyzico'),('cozum-kasa-muhasebe.html','Kasa ve muhasebe','Tahsilat takibi'),('cozum-teklif-onay.html','Teklif ve onay','Müşteri kararı')])
sol('cozum-canli-takip.html','Ustalarınız nerede, <em>görün</em>','Usta konumu yönetici ekranında görünür. Usta internetsiz yerde işlemini yapar; işlem sıraya alınır, bağlantı gelince gönderilir.','Kurumsal pakette',
 mk_list('Canlı usta konumu',[('Hasan Kaya','Çankaya · yolda','Yolda','b'),('Murat Şen','Keçiören · işte','Başladı','y'),('Selim Acar','Atölye','Atölye','')]),
 [('Canlı','konum görünümü'),('Çevrimdışı','işlem kuyruğu'),('Sıra','korunur, bağlantı gelince gider'),('Müşteri','“yoldayım” bağlantısı')],
 [('Konum','Hangi usta hangi işe daha yakın?','Usta konumu yönetici ekranında görünür. Acil bir iş geldiğinde en yakın ustaya yönlendirmek kolaylaşır.',['Usta canlı konumu yönetici ekranında','“Yoldayım” ile müşteriye takip bağlantısı','Kurumsal pakette otomatik atama önerisi'],
   mk_list('Yönetici haritası',[('Hasan Kaya','Mesafe: 2,4 km','Yakın','g'),('Murat Şen','Mesafe: 6,1 km','Orta','y')])),
  ('Çevrimdışı','Bodrumda da kayıt kaybolmasın','Usta internetsiz yerde fotoğraf, imza ve parça girer. İşlem sıraya alınır ve bağlantı gelince otomatik gönderilir.',['Usta uygulamasında çevrimdışı işlem kuyruğu','Bağlantı gelince otomatik gönderim','Servis kaydı sahada eksiksiz kalır'],
   phone('Çevrimdışı mod',[('3 işlem sırada','Bağlantı bekleniyor','Şimdi gönder',False)]),True)],
 [('Usta yola çıkar','Konum paylaşılır.'),('Yönetici görür','Harita ekranından izler.'),('İşi yapar','Bağlantı olmasa da.'),('Senkron','Bağlantı gelince gönderilir.')],
 [('Konum izleme ustaların gizliliğini ihlal eder mi?','Konum yalnızca çalışma sırasında, firma içi iş takibi için kullanılır. Ustalarınızı bilgilendirmeniz gerekir.'),('İnternet yoksa uygulama çalışır mı?','Usta işlemini yapar, işlem sıraya alınır ve bağlantı gelince gönderilir.')],
 [('usta-uygulamasi.html','Usta uygulaması','Sahada çalışma'),('cozum-otomatik-atama.html','Otomatik atama','Usta önerisi'),('cozum-personel-takibi.html','Personel takibi','Ekip')])
sol('cozum-bayi-b2b.html','Bayilerinizle <em>aynı panelden</em> çalışın','Bayi kendi servis taleplerini açar ve takip eder; siz bayi bazında rapor alırsınız. Telefon ve e-posta trafiği biter.','Kurumsal pakette',
 mk_list('Bayi talepleri',[('Yıldız Elektrik · SV-2104','Kombi · Yedek parça','Açık','y'),('Çınar Beyaz Eşya · SV-2101','Çamaşır makinesi','Tamamlandı','g'),('Doğa Klima · SV-2099','Klima montajı','Atandı','b')]),
 [('Bayi','kendi paneli'),('Bayi','bazında rapor'),('Tek','kayıt, iki taraf'),('Yetki','ayrımı')],
 [('Bayi paneli','Bayi kendi talebini kendisi açsın','Bayi hesabıyla giriş yapıp servis talebini kendi panelinden açar, durumunu izler. Sizin panelinizde tek kayıt olarak görünür.',['Bayi hesapları ve kendi paneli','Bayi bazında servis talebi','Bayi yalnızca kendi kayıtlarını görür'],
   mk_kv('Bayi paneli · Yıldız Elektrik',[('Açık talep','3'),('Tamamlanan','12'),('Bekleyen teklif','1')],'Bayi')),
  ('Rapor','Bayi bazında rapor alın','Hangi bayiden kaç iş geldi, hangisi tamamlandı, hangisi bekliyor; bayi bazında rapor ilişkiyi yönetmenizi kolaylaştırır.',['Bayi bazında rapor','Tamamlanma süreleri','Excel’e aktarma'],
   mk_bars('Bayi bazında iş',[('Yıldız',80,'24 iş'),('Çınar',56,'17 iş'),('Doğa',33,'10 iş')]),True)],
 [('Bayi ekleyin','Hesap ve yetki tanımlayın.'),('Bayi talep açsın','Kendi panelinden.'),('Siz yönetin','Ustayı atayın.'),('Rapor alın','Bayi bazında.')],
 [('Bayi benim müşterimi görür mü?','Hayır. Bayi yalnızca kendi açtığı kayıtları görür.'),('Bayi sayısı sınırlı mı?','Paket ve ihtiyaca göre kurulumda birlikte belirlenir.')],
 [('bayilik.html','İş ortaklığı','OnlineKaydet bayilik'),('cozum-raporlar.html','Raporlar','Raporlama'),('cozum-personel-takibi.html','Personel takibi','Ekip')])
sol('cozum-qr-etiket.html','Cihaza etiket, <em>telefona kayıt</em>','Cihaza yapıştırılan QR etiket okutulunca cihaz sayfası açılır. Arayan numara müşteri kartıyla eşleşir; telefonu açar açmaz müşteriyi tanırsınız.','Kurumsal pakette',
 mk_kv('Cihaz sayfası · QR',[('Cihaz','Baymak Duotec'),('Müşteri','Ayşe Yılmaz'),('Son servis','11.11.2025'),('Garanti','14.03.2027')],'Okutuldu'),
 [('QR','etiket yazdırma'),('Okut','geçmiş görsün'),('Arayan','numara eşleşir'),('Tek','dokunuş müşteri kartı')],
 [('QR','Etiketi okut, geçmişi gör','Cihaza yapıştırılan QR etiketi okutulunca cihazın servis geçmişi açılır. Usta, cihazın daha önce nasıl bir arıza yaşadığını daha sahaya girmeden bilir.',['QR cihaz etiketi yazdırma','Okutunca cihaz geçmişi','Cihaz kartında garanti ve bakım bilgisi'],
   mk_list('Cihaz geçmişi',[('11.11.2025','Yıllık bakım','Tamamlandı','g'),('02.03.2025','Basınç düşüyor','Tamamlandı','g'),('12.11.2024','Montaj','Tamamlandı','g')])),
  ('Arayan','Telefon çalar, müşteri kartı açılır','Arayan numara, kayıtlı müşteriyle eşleşir. Adı, cihazı ve açık işleri ilk saniyede önünüzdedir.',['Arayan numaradan müşteri kartı','Açık işler ve son servis tarihi','Yeni kayıt açma tek dokunuşta'],
   mk_kv('Gelen arama',[('Numara','0532 *** ** 18'),('Müşteri','Ayşe Yılmaz'),('Açık iş','SV-1043 · Yolda')],'Arıyor'),True)],
 [('Etiket yazdırın','Cihaza özel QR.'),('Cihaza yapıştırın','Kombinin üstüne.'),('Okutun','Geçmiş açılsın.'),('Arayanı tanıyın','Numara eşleşir.')],
 [('Etiket ücretli mi?','Etiket çıktısını panelden alırsınız; kendi yazıcınızı kullanırsınız.'),('Arayan numara özelliği için santral gerekir mi?','Arayan numara eşleşmesi için kurulumda telefon yönlendirmesini birlikte belirleriz.')],
 [('cozum-bakim-garanti.html','Bakım ve garanti','Cihaz kartı'),('cozum-servis-kaydi.html','Servis kaydı','Kayıt akışı'),('cozum-canli-takip.html','Canlı takip','Saha izleme')])
sol('cozum-otomatik-atama.html','İşi en uygun <em>usta alsın</em>','Konum, uzmanlık ve günlük iş yüküne göre usta önerilir. İsterseniz otomatik atanır; elle değiştirme her zaman açıktır.','Kurumsal pakette',
 mk_list('Usta önerisi · SV-1044',[('Hasan Kaya','2,4 km · kombi uzmanı · 3 iş','Önerilen','g'),('Murat Şen','6,1 km · klima uzmanı · 2 iş','Uygun','y'),('Selim Acar','Atölyede','Uygun değil','')]),
 [('3','kriter: konum, uzmanlık, yük'),('Oto','ya da öneri modu'),('Elle','değiştirme her zaman açık'),('Dengeli','günlük iş yükü')],
 [('Kurallar','Kuralı siz seçin, sistem uygulasın','Konuma göre en yakın, uzmanlığa göre en uygun, iş yüküne göre en az yüklü. Önerilen ustayı onaylarsınız ya da elle başka ustayı seçersiniz.',['En yakın usta önerisi','Uzmanlığa göre eşleştirme','Günlük iş yükü dengesi'],
   mk_toggles('Atama kuralları',[('Konuma göre',True),('Uzmanlığa göre',True),('İş yüküne göre',True),('Otomatik ata (öneri yerine)',False)],'Kurallar')),
  ('Kontrol','Elle değiştirmek her zaman mümkün','Otomatik atama yöneticinin yerini almaz; öneri sunar. Gerekirse kayda dönüp ustayı değiştirirsiniz.',['Elle değiştirme her zaman açık','Atama geçmişi kayıtta','Usta telefonuna anında düşer'],
   mk_list('Atama geçmişi',[('SV-1044','Hasan Kaya · otomatik','Atandı','g'),('SV-1043','Murat Şen · elle','Atandı','b')]),True)],
 [('Kuralı seçin','Konum, uzmanlık, yük.'),('Öneri gelsin','İş açılınca öneri çıkar.'),('Onaylayın','Ya da elle değiştirin.'),('Usta görsün','Telefona düşer.')],
 [('Otomatik atamada hata olursa?','Her zaman elle değiştirebilirsiniz. Öneri modu da seçilebilir.'),('Uzmanlık nasıl belirlenir?','Usta tanımında uzmanlık alanlarını siz seçersiniz.')],
 [('cozum-canli-takip.html','Canlı takip','Konum görünümü'),('cozum-personel-takibi.html','Personel takibi','Ekip yönetimi'),('cozum-servis-kaydi.html','Servis kaydı','İş akışı')])

def build_all():
    for d in S:
        title=d['title']
        plain=title.replace('<em>','').replace('</em>','')
        body=hero([('ozellikler.html','Ürün'),(None,d['crumb'])],title,d['lede'],d['vis'],[d['pack']]+(d['fine'] or []))
        body+=strip(d['strp'])
        for b in d['blocks']:
            k,h2,p,bul,vis=b[:5]; rev=b[5] if len(b)>5 else False; link=b[6] if len(b)>6 else None
            body+=split(k,h2,p,bul,vis,rev,link)
        body+=sec(head('Nasıl çalışır','Dört adımda işler','')+steps(d['stp']))
        body+=sec(head('Sık sorulanlar','Aklınıza takılanlar','')+faq(d['qa']))
        body+=sec(head('Birlikte kullanın','İlgili çözümler','')+related(d['rel']))
        body+=cta()
        page(d['fn'],plain,d['lede'][:155],body,faq_ld(d['qa']))
    return len(S)
