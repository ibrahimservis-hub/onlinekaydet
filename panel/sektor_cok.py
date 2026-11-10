# -*- coding: utf-8 -*-
"""Yeni sektör kataloğu (1. grup). Sade bir tanımdan; panel (sektor_ek.NEW), tema içeriği (content.SEC),
tema adları ve araçlar üretilir. Kural: kanıtlanamayan sayı, ödül, sertifika, müşteri sayısı ve tıbbi/hukuki
sonuç vaadi yazılmaz. Metinler örnektir; firma panelinden kendi bilgileriyle değiştirilir.

Arketipler (panel dili): randevu | kurs | ilan | menu | cekim"""

ARCHE_TERMS = {
    "randevu": {"Servis Kayıtları": "Randevu Defteri", "Randevular": "Online Randevular", "Garanti Talepleri": "Memnuniyet Talepleri", "Teknisyenler": "Uzmanlar",
                "Ustalar": "Uzmanlar", "Yedek Parça": "Ürün ve Sarf Stoku", "Atölye (Cihaz Teslim)": "Oda / Kabin Takibi", "Günün İş Haritası": "Günün Randevuları",
                "Fiyat Teklifleri": "Paket Teklifleri", "Usta Puanlama": "Uzman Puanlama", "Usta İş Geçmişi": "Uzman Randevu Geçmişi", "Ustadan Para Aldım": "Uzmandan Tahsilat",
                "Ustaların Borç Durumu": "Uzman Hesapları", "Geciken Usta Borçları": "Geciken Uzman Hesapları"},
    "kurs": {"Servis Kayıtları": "Kursiyer Kayıtları", "Randevular": "Ders Programı", "Garanti Talepleri": "Şikâyet ve Talepler", "Teknisyenler": "Eğitmenler",
             "Ustalar": "Eğitmenler", "Yedek Parça": "Eğitim Malzemeleri", "Atölye (Cihaz Teslim)": "Sınıf / Araç Takibi", "Günün İş Haritası": "Günün Dersleri",
             "Fiyat Teklifleri": "Kurs Teklifleri", "Usta Puanlama": "Eğitmen Puanlama", "Usta İş Geçmişi": "Eğitmen Ders Geçmişi", "Ustadan Para Aldım": "Eğitmenden Tahsilat",
             "Ustaların Borç Durumu": "Eğitmen Hesapları", "Geciken Usta Borçları": "Geciken Eğitmen Hesapları"},
    "ilan": {"Servis Kayıtları": "Müşteri Talepleri", "Randevular": "Yer Gösterme Randevuları", "Garanti Talepleri": "Takip Notları", "Teknisyenler": "Danışmanlar",
             "Ustalar": "Danışmanlar", "Yedek Parça": "Tanıtım Malzemeleri", "Atölye (Cihaz Teslim)": "Portföy Takibi", "Günün İş Haritası": "Günün Gösterimleri",
             "Fiyat Teklifleri": "Teklifler", "Usta Puanlama": "Danışman Puanlama", "Usta İş Geçmişi": "Danışman Geçmişi", "Ustadan Para Aldım": "Danışmandan Tahsilat",
             "Ustaların Borç Durumu": "Danışman Hesapları", "Geciken Usta Borçları": "Geciken Danışman Hesapları"},
    "menu": {"Servis Kayıtları": "Siparişler", "Randevular": "Masa Rezervasyonları", "Garanti Talepleri": "Müşteri Geri Bildirimi", "Teknisyenler": "Ekip",
             "Ustalar": "Ekip", "Yedek Parça": "Mutfak Stoku", "Atölye (Cihaz Teslim)": "Masa Takibi", "Günün İş Haritası": "Bugünkü Rezervasyonlar",
             "Fiyat Teklifleri": "Grup ve Etkinlik Teklifleri", "Usta Puanlama": "Ekip Puanlama", "Usta İş Geçmişi": "Ekip Vardiya Geçmişi", "Ustadan Para Aldım": "Ekipten Tahsilat",
             "Ustaların Borç Durumu": "Ekip Hesapları", "Geciken Usta Borçları": "Geciken Ekip Hesapları"},
    "cekim": {"Servis Kayıtları": "Çekim Kayıtları", "Randevular": "Çekim Takvimi", "Garanti Talepleri": "Revize Talepleri", "Teknisyenler": "Fotoğrafçılar",
              "Ustalar": "Fotoğrafçılar", "Yedek Parça": "Ekipman Stoku", "Atölye (Cihaz Teslim)": "Teslim Edilecek Albümler", "Günün İş Haritası": "Günün Çekimleri",
              "Fiyat Teklifleri": "Paket Teklifleri", "Usta Puanlama": "Ekip Puanlama", "Usta İş Geçmişi": "Çekim Geçmişi", "Ustadan Para Aldım": "Ekipten Tahsilat",
              "Ustaların Borç Durumu": "Ekip Hesapları", "Geciken Usta Borçları": "Geciken Ekip Hesapları"},
}
ARCHE_TERMS["servis"] = {}
ARCHE_DIRS = {"randevu": ["lux", "edit", "lux", "cine", "edit", "lux"], "kurs": ["edit", "neon", "edit", "cine", "neon", "edit"], "ilan": ["lux", "cine", "edit", "lux", "cine", "edit"],
              "menu": ["cine", "lux", "neon", "edit", "cine", "lux"], "cekim": ["cine", "lux", "cine", "edit", "lux", "neon"], "servis": ["edit", "neon", "cine", "edit", "neon", "cine"]}
NAME_SUF = [["Merkezi", "Stüdyo", "Plus", "Atölye", "Evi", "Butik"]]

# key: ad, arche, shop, ico, tip, tag, hizmetler(4-5), sss(2), talepler(6), baslik(3), adimlar(4), isim(6)
S = {
 "surucu_kursu": dict(name="Sürücü Kursu", arche="kurs", shop=False, ico="ar", tag="sürücü kursu",
   svc=[("Direksiyon dersi", "Sınıf ve araç eğitimi ders programına göre planlanır; ders saatiniz kayıt altında tutulur."), ("Teorik ders ve deneme sınavı", "Ders ve deneme sınavı takviminden size uygun grubu seçersiniz."),
        ("Sınav randevusu takibi", "Sınav tarihlerini ve eksik evrakınızı tek yerden görürsünüz."), ("Evrak ve ödeme planı", "Kayıt evrakları ve taksit takvimi açıkça yazılı verilir.")],
   faq=[("Kayıt için hangi belgeler gerekli?", "Güncel evrak listesi kurs kaydında yazılı verilir; yönetmelik değişebileceğinden önce arayıp teyit edin."), ("Direksiyon dersi nasıl planlanıyor?", "Müsait gün ve saatinize göre ders planı çıkarılır, değişiklik için bilgi vermeniz yeterlidir.")],
   prob=["Yeni kayıt", "Sertifika sınıfı", "Direksiyon dersi", "Sınav tarihi", "Ödeme planı", "Evrak"],
   h=["Ehliyet yolculuğunuzu planlı başlatın", "Ders ve sınav takviminiz tek ekranda", "Evrak ve ödeme planı açık yazılı"],
   steps=[("Ön kayıt", "Bilgileriniz ve sınıfınız alınır."), ("Evrak", "Gerekli evrak listesi iletilir."), ("Ders planı", "Teorik ve direksiyon dersi planlanır."), ("Sınav", "Sınav randevusu takip edilir.")],
   names=["Yol Arkadaşı Sürücü Kursu", "Yeşil Işık Kursu", "Güvenli Direksiyon", "Kavşak Sürücü Kursu", "Anadolu Sürücü Kursu", "Hız Sınırı Kursu"]),
 "src_kursu": dict(name="SRC & Mesleki Yeterlilik Kursu", arche="kurs", shop=False, ico="cl", tag="mesleki belge kursu",
   svc=[("SRC belge kursları", "Hangi SRC belgesi için başvuru yapacağınızı birlikte netleştirir, kayıt işlemlerinizi yürütürüz."), ("Mesleki yeterlilik hazırlık", "Sınava hazırlık dersleri ve deneme takvimi."),
        ("Evrak takibi", "Eksik evrakınız ve son tarihler size bildirilir."), ("Grup ve kurumsal eğitim", "Firmalar için toplu kayıt ve ders planı.")],
   faq=[("Hangi belgeye ihtiyacım olduğunu nasıl öğrenirim?", "Çalışma türünüzü söyleyin, gerekli belgeyi ve güncel şartları birlikte kontrol edelim."), ("Sınav tarihlerini siz mi takip ediyorsunuz?", "Sınav takvimini bildirir, randevu sürecinde size yardımcı oluruz.")],
   prob=["Belge türü", "Yeni kayıt", "Evrak", "Sınav tarihi", "Yenileme", "Kurumsal eğitim"],
   h=["Mesleki belgenizi planlı alın", "Evrak ve sınav takvimi takipte", "Firmanız için toplu kayıt"],
   steps=[("Görüşme", "Çalışma türünüz ve belgeniz netleşir."), ("Kayıt", "Evraklar toplanır."), ("Eğitim", "Ders programı belirlenir."), ("Sınav", "Takvim ve randevu takip edilir.")],
   names=["Yetkin Mesleki Eğitim", "Doğru Belge Kursu", "Profesyonel Sürücü Merkezi", "Yol ve İş Eğitim", "Atlas SRC Kursu", "Net Yeterlilik Merkezi"]),
 "psikolog": dict(name="Psikolog & Psikoterapist", arche="randevu", shop=False, ico="us", tag="psikolojik danışmanlık",
   svc=[("Bireysel görüşme", "İlk görüşmede beklentileriniz konuşulur, görüşme sıklığı birlikte planlanır."), ("Çift ve aile görüşmeleri", "İlişki ve aile içi iletişim konularında planlı seanslar."),
        ("Çocuk ve ergen görüşmeleri", "Aileyle yapılan ön görüşmeden sonra yaşa uygun seans planlanır."), ("Online görüşme", "Uygun olduğunuzda görüntülü seans seçeneği.")],
   faq=[("İlk görüşmede ne olur?", "Birbirimizi tanır, beklentilerinizi konuşur ve çalışma çerçevesini birlikte belirleriz."), ("Görüşmeler gizli mi?", "Görüşme bilgileriniz meslek etiği ve yasal çerçevede gizli tutulur.")],
   prob=["İlk görüşme", "Bireysel", "Çift / aile", "Çocuk / ergen", "Online seans", "Randevu değişikliği"],
   h=["İlk adımı küçük tutun: bir görüşme ayırın", "Randevunuz sizin saatinize göre", "Gizli, sakin ve planlı süreç"],
   steps=[("Randevu", "Uygun gün ve saat seçilir."), ("İlk görüşme", "Beklentileriniz konuşulur."), ("Plan", "Görüşme sıklığı belirlenir."), ("Takip", "Sonraki randevular hatırlatılır.")],
   names=["Sakin Psikolojik Danışmanlık", "Yeni Bir Sayfa Terapi", "Denge Danışmanlık", "Pusula Psikoloji", "Açıklık Terapi Merkezi", "Bağ Danışmanlık"]),
 "diyetisyen": dict(name="Diyetisyen", arche="randevu", shop=False, ico="fl", tag="beslenme danışmanlığı",
   svc=[("Beslenme danışmanlığı", "Alışkanlıklarınıza ve yaşam tarzınıza göre planlanır; kişiye özel plan randevuda konuşulur."), ("Düzenli takip", "Ölçü ve plan takibi randevu kartınızda görünür."),
        ("Online danışmanlık", "Uygun olduğunuzda görüntülü görüşme."), ("Grup ve kurumsal programlar", "Şirket ve topluluklar için bilgilendirme seansları.")],
   faq=[("İlk randevuya ne getirmeliyim?", "Varsa güncel tahlilleriniz ve kullandığınız ilaçların listesi yararlı olur; bilgi randevu mesajında iletilir."), ("Programı kim hazırlıyor?", "Plan, görüşmenizdeki bilgilere göre diyetisyen tarafından hazırlanır.")],
   prob=["İlk randevu", "Takip", "Online görüşme", "Kurumsal program", "Randevu değişikliği", "Paket"],
   h=["Size uygun beslenme düzeni için randevu alın", "Takip randevularınız hatırlatılır", "Online da görüşebiliriz"],
   steps=[("Randevu", "Gün ve saat seçilir."), ("Görüşme", "Alışkanlıklarınız konuşulur."), ("Plan", "Size uygun plan hazırlanır."), ("Takip", "Sonraki randevu planlanır.")],
   names=["Dengeli Beslenme", "Taze Plan Diyet", "Sağlıklı Sofra", "Mevsim Beslenme", "Doğru Tabak", "Yeşil Tabak Danışmanlık"]),
 "fizyoterapi": dict(name="Fizyoterapi & Masaj", arche="randevu", shop=False, ico="pl", tag="fizyoterapi",
   svc=[("Fizyoterapi seansları", "Değerlendirmeden sonra seans planı çıkarılır; doktor önerisi varsa getirmeniz istenir."), ("Egzersiz programı", "Evde yapabileceğiniz egzersizler gösterilir."),
        ("Masaj ve rahatlama", "Seans süreleri ve türleri randevuda seçilir."), ("Paket seans takibi", "Kalan seans sayınız kartınızda görünür.")],
   faq=[("Doktor yönlendirmesi gerekli mi?", "Duruma göre değişir; randevuda sorularınızı yanıtlarız."), ("Kaç seans gerekir?", "Değerlendirmeden sonra planlanır, kesin sayı kişiye göre değişir.")],
   prob=["İlk değerlendirme", "Seans randevusu", "Paket", "Egzersiz", "Masaj", "Değişiklik"],
   h=["Randevunuzu ayırın, seanslarınızı takip edelim", "Kalan seanslarınız kartınızda", "Evde yapabileceğiniz egzersizler"],
   steps=[("Randevu", "Gün ve saat seçilir."), ("Değerlendirme", "Şikâyetiniz dinlenir."), ("Plan", "Seans planı çıkarılır."), ("Takip", "Her seans kaydedilir.")],
   names=["Hareket Fizyoterapi", "Omurga Merkezi", "Yeniden Hareket", "Denge Fizyo", "Rahat Adım", "Kıvrak Fizyoterapi"]),
 "dis_klinigi": dict(name="Diş Kliniği", arche="randevu", shop=False, ico="cp", tag="ağız ve diş sağlığı",
   svc=[("Muayene ve kontrol", "Düzenli kontrol randevusu; tedavi planı muayeneden sonra anlatılır."), ("Tedavi planlama", "Yapılacak işlemler ve randevu sayısı önceden bildirilir."),
        ("Estetik uygulamalar", "Beklentiler muayenede konuşulur."), ("Çocuk diş hekimliği", "Çocuklar için sakin, kısa randevular.")],
   faq=[("İlk muayenede ne yapılır?", "Ağız içi muayene yapılır; ihtiyaç halinde film istenir ve plan anlatılır."), ("Tedavi ücreti önceden belli mi?", "Muayeneden sonra planlanan işlemlerin fiyatı yazılı bildirilir.")],
   prob=["Muayene", "Ağrı", "Tedavi", "Estetik", "Çocuk randevusu", "Kontrol"],
   h=["Kontrol randevunuzu şimdi ayırın", "Tedavi planı ve fiyat yazılı", "Çocuklar için sakin randevular"],
   steps=[("Randevu", "Uygun saat seçilir."), ("Muayene", "Ağız içi muayene yapılır."), ("Plan", "Tedavi planı ve fiyat anlatılır."), ("Takip", "Kontrol randevusu verilir.")],
   names=["Beyaz Gülüş Diş", "Işıl Ağız Diş Sağlığı", "Dört Mevsim Diş", "Parlak Diş Kliniği", "Güler Yüz Diş", "Sağlam Diş Polikliniği"]),
 "veteriner": dict(name="Veteriner", arche="randevu", shop=True, ico="sp", tag="veteriner hekimlik",
   svc=[("Muayene ve aşı takibi", "Aşı takvimi hatırlatma mesajıyla takip edilir."), ("Kısırlaştırma ve ameliyat", "İşlem öncesi hazırlık bilgisi randevuda verilir."), ("Hasta kabul ve yatış", "Kabul ve taburculuk bilgisi yazılı."),
        ("Mama ve ürün satışı", "Online mağazamızdan sipariş verebilirsiniz.")],
   faq=[("Acil durumda ne yapmalıyım?", "Hemen arayın; ilk yönlendirme telefonda yapılır."), ("Aşı takvimini siz mi takip ediyorsunuz?", "Evet, tarih yaklaştığında hatırlatma mesajı göndeririz.")],
   prob=["Muayene", "Aşı", "Kısırlaştırma", "Acil", "Mama / ürün", "Kontrol"],
   h=["Dostunuzun aşı takvimi bizde", "Randevu ve acil iletişim tek yerde", "Mama ve ürünleri online sipariş edin"],
   steps=[("Randevu", "Hayvanın türü ve şikâyet alınır."), ("Muayene", "Muayene ve öneri."), ("Tedavi", "Plan anlatılır, onayınızla başlar."), ("Takip", "Kontrol ve aşı hatırlatması.")],
   names=["Pati Veteriner Kliniği", "Dost Hayvan Hastanesi", "Tüylü Dostlar Veteriner", "Minik Pati Klinik", "Vefa Veteriner", "Can Dostum Veteriner"]),
 "avukat": dict(name="Avukat & Hukuk Bürosu", arche="randevu", shop=False, ico="sh", tag="hukuki danışmanlık",
   svc=[("Hukuki danışma görüşmesi", "Konunuz görüşmede dinlenir; sonuç vaadi verilmez, süreç ve belgeler anlatılır."), ("Dava ve takip", "Süreç boyunca bilgilendirilirsiniz."),
        ("Sözleşme hazırlığı ve inceleme", "Kiralama, iş ve ticari sözleşmeler."), ("Kurumsal danışmanlık", "Firmalar için sürekli hukuki destek.")],
   faq=[("İlk görüşme ücretli mi?", "Ücret bilgisi randevu öncesinde yazılı iletilir."), ("Belgelerimi önceden gönderebilir miyim?", "Evet, randevu sonrası güvenli kanalla iletebilirsiniz.")],
   prob=["Danışma", "Aile hukuku", "İş hukuku", "Ticari", "Sözleşme", "Randevu değişikliği"],
   h=["Hukuki sorununuzu randevuyla netleştirin", "Süreç boyunca bilgilendirilirsiniz", "Ücret baştan yazılı"],
   steps=[("Randevu", "Konu ve belgeler önceden alınır."), ("Görüşme", "Durumunuz değerlendirilir."), ("Plan", "Süreç ve ücret açıklanır."), ("Takip", "Gelişmeler bildirilir.")],
   names=["Adalet Hukuk Bürosu", "Hakkaniyet Hukuk", "Dayanak Hukuk", "Mizan Hukuk Bürosu", "Kanun ve Düzen Hukuk", "Savunma Hukuk"]),
 "muhasebe": dict(name="Mali Müşavir & Muhasebe", arche="randevu", shop=False, ico="ca", tag="muhasebe ve mali danışmanlık",
   svc=[("Defter ve beyanname", "Aylık ve yıllık beyanname takvimi hatırlatılır."), ("Şirket ve şahıs kuruluşu", "Süreç, belgeler ve ücret baştan yazılı."), ("Bordro ve SGK işlemleri", "Personel işlemleri tek yerden."),
        ("Mali danışmanlık", "Vergi planlaması ve raporlama.")],
   faq=[("Beyanname tarihlerini kim takip ediyor?", "Takvimi biz takip eder, yaklaşan tarihleri bildiririz."), ("Belgeleri nasıl teslim ederim?", "Online yükleyebilir ya da ofise getirebilirsiniz.")],
   prob=["Şirket kuruluşu", "Beyanname", "Bordro", "Danışmanlık", "Belge teslimi", "Ücret"],
   h=["Beyanname tarihleri bizde", "Şirket kuruluşunda belgeler baştan yazılı", "Belgelerinizi online teslim edin"],
   steps=[("Görüşme", "İhtiyacınız ve firmanız anlatılır."), ("Teklif", "Kapsam ve ücret yazılı."), ("Belge akışı", "Aylık belge teslimi düzenlenir."), ("Takip", "Beyanname ve ödemeler hatırlatılır.")],
   names=["Denge Mali Müşavirlik", "Artı Muhasebe", "Berrak Mali Danışman", "Düzen Muhasebe", "Net Defter", "Güven SMMM"]),
 "spor_salonu": dict(name="Spor Salonu & Pilates", arche="randevu", shop=False, ico="bt", tag="spor ve fitness",
   svc=[("Üyelik paketleri", "Aylık, 3 aylık ve yıllık paketler; kullanım koşulları baştan yazılı."), ("Grup dersleri", "Ders programını online görün, yer ayırın."), ("Birebir antrenman", "Hedefinize göre program hazırlanır."),
        ("Deneme seansı", "Üye olmadan önce salonu tanıyın.")],
   faq=[("Üyeliğimi dondurabilir miyim?", "Dondurma koşulları üyelik sözleşmesinde yazılıdır, kayıtta anlatılır."), ("Deneme seansı alabilir miyim?", "Randevu formundan gün ve saat seçebilirsiniz.")],
   prob=["Üyelik", "Grup dersi", "Birebir antrenman", "Deneme seansı", "Dondurma", "Ödeme"],
   h=["Deneme seansınızı ayırın", "Ders programı ve yer ayırtma online", "Üyelik koşulları baştan yazılı"],
   steps=[("Tanışma", "Hedefiniz konuşulur."), ("Paket", "Size uygun paket seçilir."), ("Program", "Ders ve antrenman planı."), ("Takip", "Gelişiminiz kaydedilir.")],
   names=["Güç Spor Merkezi", "Nefes Pilates Stüdyosu", "Form Fitness", "Hareket Spor Salonu", "Denge Pilates", "Tempo Spor Kulübü"]),
 "lokanta": dict(name="Lokanta & Kafe", arche="menu", shop=False, ico="fl", tag="yeme içme",
   svc=[("Masa rezervasyonu", "Kişi sayısı ve saatinizi seçin, onay mesajı alın."), ("Menü ve günün yemekleri", "Güncel menü ve fiyatlar sitede."), ("Grup ve özel gün yemekleri", "Doğum günü ve iş yemekleri için ayrı düzen."),
        ("Paket servis ve sipariş", "Telefonla ya da formdan sipariş alınır.")],
   faq=[("Rezervasyon nasıl yapılıyor?", "Sitedeki formu doldurun ya da arayın; onay mesajı gönderilir."), ("Alerjim varsa?", "Rezervasyon notuna yazın; mutfak ekibine iletilir.")],
   prob=["Masa", "Grup yemeği", "Doğum günü", "Paket sipariş", "Menü", "Alerji bilgisi"],
   h=["Masanızı şimdi ayırın", "Günün menüsü sitede", "Grup ve özel günler için ayrı düzen"],
   steps=[("Rezervasyon", "Gün, saat ve kişi sayısı."), ("Onay", "Mesajla onay alırsınız."), ("Karşılama", "Masanız hazır beklenir."), ("Geri bildirim", "Görüşünüzü paylaşırsınız.")],
   names=["Sofra Lokanta", "Közde Mutfak", "Mevsim Kafe", "Tuzlu Tatlı Mutfak", "Köşe Kafe", "Bahçe Lokantası"]),
 "fotografci": dict(name="Fotoğrafçı & Video Prodüksiyon", arche="cekim", shop=False, ico="lp", tag="fotoğraf ve video çekimi",
   svc=[("Düğün ve nişan çekimi", "Tarih ve mekân görüşmesi, paket ve teslim süresi baştan yazılı."), ("Portre ve aile çekimi", "Stüdyoda ya da dışarıda."), ("Ürün ve kurumsal çekim", "E-ticaret ve kurumsal görseller."),
        ("Video ve tanıtım filmi", "Senaryo, çekim ve kurgu aşamaları anlatılır.")],
   faq=[("Teslim süresi nedir?", "Paket ve çekim türüne göre değişir; sözleşmede tarih yazılıdır."), ("Fotoğrafları nasıl alıyorum?", "Online galeri bağlantısıyla teslim edilir.")],
   prob=["Düğün", "Portre", "Ürün çekimi", "Kurumsal", "Video", "Tarih sorgulama"],
   h=["Çekim tarihinizi ayırın", "Paket ve teslim süresi yazılı", "Online galeri ile teslim"],
   steps=[("Görüşme", "Beklentiler ve tarih."), ("Paket", "Kapsam ve fiyat yazılı."), ("Çekim", "Planlanan gün çekim yapılır."), ("Teslim", "Seçilen kareler galeriye yüklenir.")],
   names=["Kare Fotoğraf Stüdyosu", "Işık Atölyesi", "Anı Fotoğrafçılık", "Poz Prodüksiyon", "Obje Stüdyo", "Çerçeve Film"]),
 "emlakci": dict(name="Emlakçı & Gayrimenkul", arche="ilan", shop=False, ico="pin", tag="gayrimenkul danışmanlığı",
   svc=[("Satılık ve kiralık portföy", "Güncel ilanlar sitede; fotoğraf, konum ve fiyat bilgisiyle."), ("Değerleme görüşmesi", "Mülkünüz için bölge ve özelliklere göre görüşme."), ("Yer gösterme randevusu", "Uygun gün ve saatte ilanı yerinde görün."),
        ("Tapu ve kiralama sürecinde destek", "Gerekli belge ve adımlar yazılı anlatılır.")],
   faq=[("İlanı yerinde görebilir miyim?", "Randevu formundan gün ve saat seçin; danışman sizi karşılar."), ("Mülkümü satmak için ne yapmalıyım?", "Değerleme görüşmesi için randevu alın; belgeler ve süreç anlatılır.")],
   prob=["Satılık arıyorum", "Kiralık arıyorum", "Mülkümü satmak istiyorum", "Mülkümü kiralamak istiyorum", "Yer gösterme", "Değerleme"],
   h=["Aradığınız evi birlikte bulalım", "Yer gösterme randevusu tek formda", "Mülkünüz için değerleme görüşmesi"],
   steps=[("Talep", "Bütçe, bölge ve beklenti alınır."), ("Seçenekler", "Uygun ilanlar paylaşılır."), ("Yer gösterme", "Randevu ayarlanır."), ("Süreç", "Teklif ve belge adımları anlatılır.")],
   names=["Yuva Gayrimenkul", "Anahtar Emlak", "Kapı Emlak", "Çatı Gayrimenkul", "Şehir Emlak", "Bahçeli Emlak"]),
 "oto_yikama": dict(name="Oto Yıkama & Detay", arche="randevu", shop=False, ico="dr", tag="oto yıkama ve detaylı temizlik",
   svc=[("İç ve dış yıkama", "Aracınıza göre seçilen paketle yıkama."), ("Detaylı iç temizlik", "Koltuk, döşeme ve iç aksam derinlemesine temizlenir."), ("Pasta cila ve koruma", "Boya durumu görülerek uygun uygulama anlatılır."),
        ("Randevulu hizmet", "Müsait saat seçin, bekleme olmasın.")],
   faq=[("Randevusuz gelebilir miyim?", "Yoğunluğa göre; randevuyla beklemezsiniz."), ("İşlem ne kadar sürer?", "Paket ve araç durumuna göre; randevuda tahmini süre söylenir.")],
   prob=["İç dış yıkama", "Detay", "Pasta cila", "Seramik / koruma", "Filo aracı", "Randevu"],
   h=["Aracınız için saat ayırın, beklemeyin", "Paket ve fiyat baştan yazılı", "İşlem öncesi sonrası fotoğraf"],
   steps=[("Randevu", "Paket ve saat seçilir."), ("Teslim", "Araç durumu kayıt altına alınır."), ("Uygulama", "İşlem yapılır."), ("Teslim", "Birlikte kontrol edilir.")],
   names=["Pırıl Oto Yıkama", "Parlak Oto Detay", "Işıltı Oto", "Köpük Oto Yıkama", "Cilalı Oto", "Tertemiz Oto"]),
 "telefon_tamir": dict(name="Telefon & Tablet Tamiri", arche="randevu", shop=True, ico="ph", tag="telefon ve tablet tamiri",
   svc=[("Ekran ve batarya değişimi", "Fiyat ve süre cihazı görüldükten sonra yazılı söylenir."), ("Su teması ve kart arızaları", "Önce teşhis, sonra onayınızla işlem."), ("Yazılım ve veri aktarımı", "Verileriniz için işlem öncesi bilgi verilir."),
        ("Aksesuar ve kılıf", "Online mağazadan sipariş verin.")],
   faq=[("Tamir ne kadar sürer?", "Arızaya göre değişir; teşhis sonrası süre bildirilir."), ("Verilerim silinir mi?", "İşlem öncesi yedek alma önerilir ve işlem bilgisi verilir.")],
   prob=["Ekran kırık", "Batarya", "Şarj olmuyor", "Su teması", "Yazılım", "Aksesuar"],
   h=["Cihazınızı bırakın, durum SMS ile gelsin", "Fiyat işlemden önce yazılı", "Aksesuarlar online mağazada"],
   steps=[("Kayıt", "Cihaz ve arıza alınır."), ("Teşhis", "Fiyat ve süre bildirilir."), ("Onarım", "Onayınızla işlem."), ("Teslim", "SMS ile haber, test sonrası teslim.")],
   names=["Hızlı Telefon Servisi", "Mobil Onarım", "Ekran Tamir Merkezi", "Dokunmatik Servis", "Akıllı Servis", "Şarj Telefon Tamiri"]),
}
PRODUCTS = {
 "veteriner": [("VT-5001", "Kedi maması 2 kg", "Pati", "Mama", 520, 2), ("VT-5002", "Köpek maması 3 kg", "Pati", "Mama", 690, 2), ("VT-5003", "Tasma seti", "Pati", "Aksesuar", 240, 2), ("VT-5004", "Bakım şampuanı", "Pati", "Bakım", 190, 2)],
 "telefon_tamir": [("TT-6001", "Şeffaf telefon kılıfı", "Servis", "Kılıf", 180, 2), ("TT-6002", "Temperli cam", "Servis", "Koruyucu", 120, 2), ("TT-6003", "Hızlı şarj kablosu", "Servis", "Şarj", 260, 2), ("TT-6004", "Taşınabilir şarj cihazı", "Servis", "Şarj", 650, 1)],
}
HEAD_SUB = {"servis": "Talebinizi yazın, randevu veya keşif için size dönüş yapalım.", "randevu": "Randevunuzu online ayırın; hatırlatma mesajı telefonunuza gelir.", "kurs": "Kaydınızı ve ders planınızı online başlatın.", "ilan": "Talebinizi iletin, danışman sizi arasın.",
            "menu": "Rezervasyon ve sipariş bilgilerinizi bırakın, onay mesajı gelsin.", "cekim": "Tarih ve ihtiyacınızı yazın, paket ve fiyatla dönüş yapalım."}
CIT = ["Ankara", "İstanbul", "İzmir", "Bursa", "Antalya", "Konya"]
SEC_COLORS = None


def panel_new():
    """sektor_ek.NEW biçimi."""
    out = {}
    for k, s in S.items():
        out[k] = {"name": s["name"], "type": "hizmet", "brands": {t: [] for t in s["prob"][:5]}, "faults": list(s["prob"]),
                  "checklist": [("Müşteri bilgileri doğrulandı", True), ("Hizmet kapsamı ve ücret bildirildi", True), ("Sonraki adım / randevu planlandı", False)],
                  "servis": {"foto_once": "istege_bagli", "foto_sonra": "istege_bagli"}, "pdf_title": "HİZMET FORMU",
                  "terms": dict(ARCHE_TERMS[s["arche"]]), "site": {"services": list(s["svc"]), "faq": list(s["faq"])}}
    return out


def content_sec(faq_fn):
    """content.SEC biçimi (tema içeriği)."""
    out = {}
    for k, s in S.items():
        sub = HEAD_SUB[s["arche"]]
        h = [(t, sub) for t in s["h"]] + [("Sorularınız mı var? Bize yazın", "Formdan ulaşın, size en kısa sürede dönüş yapalım."), ("Bilgileriniz kayıt altında", "Talebiniz kaydedilir, onay ve hatırlatma mesajı gönderilir.")]
        out[k] = dict(label=s["name"].split(" &")[0], ico=s["ico"], img=k, cihaz=s["prob"][:4], brands=s["prob"][:6],
                      services=[(t, d, ["cal", "us", "cl", "pl", "st"][i % 5]) for i, (t, d) in enumerate(s["svc"])], faq=faq_fn(k),
                      h=h, steps=list(s["steps"]), rev=[("Örnek müşteri", "Randevu süreci ve bilgilendirme çok net, tekrar tercih ederim."), ("Örnek müşteri", "Hatırlatma mesajı sayesinde randevumu kaçırmadım."),
                                                      ("Örnek müşteri", "Fiyat ve kapsam baştan yazılıydı.")], prob=list(s["prob"]), tag=s["tag"])
    return out


def theme_meta():
    return dict(
        names={k: list(s["names"]) for k, s in S.items()}, dirs={k: ARCHE_DIRS[s["arche"]] for k, s in S.items()},
        shop_on={k for k, s in S.items() if s["shop"]}, tools_by={k: ["gen.hazirlik", "gen.soru"] for k in S},
        sector_words={s["name"].lower().split(" &")[0]: k for k, s in S.items()})


import sektor_cok2 as _c2
S.update(_c2.to_spec())
PRODUCTS.update(_c2.PRODUCTS)
