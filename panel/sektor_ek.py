# -*- coding: utf-8 -*-
"""Teknik olmayan sektörler: oto servis, çekici, kuaför, nakliye, tekstil, e-ticaret, temizlik, güzellik.

Her sektörde: katalog (marka/hizmet), sık talepler, kontrol listesi, belge başlığı, SİTE metinleri (hizmet + SSS) ve
firma panelinde görünen TERİMLER (terms). Panel menüsündeki "Servis Kayıtları", "Teknisyenler" gibi teknik servis
dili, sektörün kendi diliyle değişir (oto servis: "İş Emirleri / Ustalar", kuaför: "Randevu Defteri / Uzmanlar" ...).
Kural: kanıtlanamayan sayı, ödül, sertifika veya müşteri sayısı yazılmaz."""

# Panelde yeniden adlandırılan varsayılan etiketler (teknik servis dili). Anahtar: varsayılan metin.
BASE_TERMS = ["Servis Kayıtları", "Randevular", "Fiyat Teklifleri", "Garanti Talepleri", "Teknisyenler", "Ustalar",
              "Yedek Parça", "Atölye (Cihaz Teslim)", "Günün İş Haritası", "Müşteri 360", "Usta Puanlama", "Usta İş Geçmişi",
              "Ustadan Para Aldım", "Ustaların Borç Durumu", "Geciken Usta Borçları", "Bayilik Başvuruları"]

NEW = {
    "oto_servis": {
        "name": "Oto Servis & Bakım", "type": "araç",
        "brands": {"Renault": ["Clio", "Megane"], "Fiat": ["Egea", "Doblo"], "Volkswagen": ["Golf", "Passat"], "Ford": ["Focus", "Transit"],
                   "Toyota": ["Corolla"], "Hyundai": ["i20", "Tucson"], "Opel": ["Astra"], "Peugeot": ["301"], "Dacia": ["Duster"]},
        "faults": ["Periyodik bakım", "Motor ışığı yanıyor", "Fren sesi / balata", "Yağ ve filtre değişimi", "Akü / marş sorunu", "Lastik ve rot-balans", "Klima bakımı", "Egzoz / duman"],
        "checklist": [("Araç teslim alırken dış hasar fotoğrafı", True), ("Kilometre ve yakıt seviyesi kaydı", True), ("Yağ, antifriz, fren hidroliği seviyeleri", False), ("Lastik basınçları", False), ("Yol denemesi", True)],
        "servis": {"foto_once": "zorunlu", "foto_sonra": "istege_bagli"}, "pdf_title": "İŞ EMRİ",
        "terms": {"Servis Kayıtları": "İş Emirleri", "Randevular": "Bakım Randevuları", "Garanti Talepleri": "Garanti ve Geri Çağırma", "Teknisyenler": "Ustalar",
                  "Yedek Parça": "Parça Stoku", "Atölye (Cihaz Teslim)": "Araç Teslim Alma", "Günün İş Haritası": "Bugünkü İş Emirleri", "Fiyat Teklifleri": "Onarım Teklifleri"},
        "site": {"services": [("Periyodik bakım", "Yağ, filtre, fren ve sıvı kontrollerini üreticinin bakım çizelgesine göre yaparız; yapılan her işlemi iş emrinde gösteririz."),
                              ("Mekanik onarım", "Motor, şanzıman, fren ve süspansiyon arızalarını bilgisayarlı teşhisle tespit eder, fiyatı onarımdan önce söyleriz."),
                              ("Lastik ve rot-balans", "Lastik değişimi, balans ve rot ayarını aynı gün yaparız."),
                              ("Akü ve elektrik", "Akü, marş, alternatör ve aydınlatma sorunlarını yerinde test ederiz."),
                              ("Klima bakım ve gaz dolumu", "Araç kliması için filtre değişimi, kaçak kontrolü ve gaz dolumu yapılır.")],
                 "faq": [("Aracımı bıraktıktan sonra ne zaman haber alırım?", "Muayene sonrası yapılacak işlem ve fiyat telefonunuza iletilir, onayınız olmadan işlem başlamaz."),
                         ("Bakım ne sıklıkla yapılmalı?", "Genellikle yılda bir ya da üreticinin belirttiği kilometrede; aracınızın kullanım kılavuzu esastır."),
                         ("Parçalar orijinal mi?", "Orijinal, muadil ya da yan sanayi seçenekleri fiyatlarıyla sunulur; seçimi siz yaparsınız.")]},
    },
    "oto_cekici": {
        "name": "Oto Çekici & Yol Yardım", "type": "araç",
        "brands": {"Otomobil": [], "Hafif ticari": [], "Motosiklet": [], "Minibüs": [], "Kamyonet": []},
        "faults": ["Kaza sonrası çekim", "Araç çalışmıyor", "Lastik patlak", "Akü bitti", "Yakıt bitti", "Kapı kilidi / anahtar", "Şehirlerarası taşıma", "Park yeri çıkarma"],
        "checklist": [("Araç hasar fotoğrafları (yüklemeden önce)", True), ("Konum ve varış adresi onayı", True), ("Teslimde müşteri imzası", True), ("Ücret ve ödeme yöntemi bilgisi", False)],
        "servis": {"foto_once": "zorunlu", "foto_sonra": "zorunlu"}, "pdf_title": "ÇEKİCİ HİZMET FORMU",
        "terms": {"Servis Kayıtları": "Çekici Çağrıları", "Randevular": "Rezervasyonlar", "Garanti Talepleri": "Hasar Bildirimleri", "Teknisyenler": "Sürücüler",
                  "Ustalar": "Sürücüler", "Yedek Parça": "Ekipman Stoku", "Atölye (Cihaz Teslim)": "Araç Teslim", "Günün İş Haritası": "Çağrı Haritası", "Fiyat Teklifleri": "Mesafe Teklifleri",
                  "Usta Puanlama": "Sürücü Puanlama", "Usta İş Geçmişi": "Sürücü Sefer Geçmişi", "Ustadan Para Aldım": "Sürücüden Tahsilat"},
        "site": {"services": [("Acil yol yardım", "Aracınız yolda kaldığında konumunuzu paylaşın, en yakın ekibi yönlendirelim."),
                              ("Kaza sonrası çekim", "Hasarlı aracı güvenle yükler, anlaşmalı servise ya da istediğiniz adrese bırakırız."),
                              ("Şehirlerarası araç taşıma", "Araç taşıyıcı ile uzun mesafe taşıma; teslim öncesi fotoğraflı tutanak."),
                              ("Akü takviyesi ve lastik yardımı", "Yolda akü takviyesi, yedek lastik takma ve yakıt desteği."),
                              ("Kilitli araç açma", "Anahtar içeride kaldığında araca zarar vermeden açmaya çalışırız.")],
                 "faq": [("Ne kadar sürede gelirsiniz?", "Konumunuza ve yoğunluğa göre değişir; çağrıda tahmini varış süresini söyleriz."),
                         ("Ücret nasıl belirleniyor?", "Mesafe ve araç tipine göre; yola çıkmadan önce telefonda net fiyat veririz."),
                         ("Sigorta çekicisi mi, özel mi?", "Her ikisi için de hizmet veririz; sigorta yol yardım hakkınızı poliçeden kontrol edin.")]},
    },
    "kuafor": {
        "name": "Kuaför & Berber", "type": "hizmet",
        "brands": {"Saç kesimi": [], "Boya ve röfle": [], "Fön ve şekillendirme": [], "Sakal ve bakım": [], "Cilt bakımı": [], "Gelin saçı": []},
        "faults": ["Saç kesimi", "Boya", "Röfle / balyaj", "Fön", "Sakal tıraşı", "Keratin bakımı", "Gelin saçı", "Çocuk tıraşı"],
        "checklist": [("Alerji / hassasiyet sorusu soruldu", True), ("İşlem öncesi fotoğraf (isteğe bağlı)", False), ("Ürün ve boya bilgisi karta işlendi", False), ("Bir sonraki randevu önerildi", False)],
        "servis": {"foto_once": "istege_bagli", "foto_sonra": "istege_bagli"}, "pdf_title": "HİZMET FİŞİ",
        "terms": {"Servis Kayıtları": "Randevu Defteri", "Randevular": "Online Randevular", "Garanti Talepleri": "Memnuniyet Talepleri", "Teknisyenler": "Uzmanlar",
                  "Ustalar": "Uzmanlar", "Yedek Parça": "Ürün ve Sarf Stoku", "Atölye (Cihaz Teslim)": "Koltuk / Kabin Takibi", "Günün İş Haritası": "Günün Randevuları",
                  "Fiyat Teklifleri": "Paket Teklifleri", "Usta Puanlama": "Uzman Puanlama", "Usta İş Geçmişi": "Uzman Randevu Geçmişi", "Ustadan Para Aldım": "Uzmandan Tahsilat",
                  "Ustaların Borç Durumu": "Uzman Hesapları", "Geciken Usta Borçları": "Geciken Uzman Hesapları"},
        "site": {"services": [("Saç kesimi", "Yüz şeklinize ve saç yapınıza göre kesim; öncesinde ne istediğinizi dinler, sonrasında bakım önerisi veririz."),
                              ("Boya ve röfle", "Alerji sorusuyla başlar, saç yapınıza uygun ürünle çalışırız."),
                              ("Fön ve şekillendirme", "Günlük, özel gün ve davet öncesi şekillendirme."),
                              ("Sakal ve bakım", "Sakal tasarımı, ustura tıraşı ve cilt bakımı."),
                              ("Gelin saçı ve özel gün", "Deneme randevusuyla birlikte gün öncesi planlanır.")],
                 "faq": [("Randevusuz gelebilir miyim?", "Boş koltuk varsa alırız; beklememek için online randevu almanızı öneririz."),
                         ("Randevumu nasıl iptal ederim?", "Hatırlatma mesajındaki bağlantıdan ya da telefonla iptal edebilir veya saatini değiştirebilirsiniz."),
                         ("Kendi ürünümü getirebilir miyim?", "Evet; saç yapınıza uygunluğunu randevuda birlikte kontrol ederiz.")]},
    },
    "nakliye": {
        "name": "Nakliye & Taşımacılık", "type": "taşıma",
        "brands": {"Evden eve": [], "Ofis taşıma": [], "Parça eşya": [], "Asansörlü taşıma": [], "Depolama": [], "Şehirlerarası": []},
        "faults": ["Evden eve nakliyat", "Ofis taşıma", "Parça eşya", "Asansörlü taşıma", "Eşya depolama", "Paketleme hizmeti", "Şehirlerarası nakliyat", "Piyano / özel eşya"],
        "checklist": [("Keşif yapıldı, eşya listesi çıkarıldı", True), ("Kırılacak eşya paketlendi ve işaretlendi", True), ("Çıkış ve varış adresinde asansör / kat bilgisi", False), ("Teslimde eşya sayımı ve müşteri onayı", True)],
        "servis": {"foto_once": "istege_bagli", "foto_sonra": "zorunlu"}, "pdf_title": "TAŞIMA FORMU",
        "terms": {"Servis Kayıtları": "Taşıma İşleri", "Randevular": "Keşif ve Taşıma Günleri", "Garanti Talepleri": "Hasar ve Tazmin Talepleri", "Teknisyenler": "Ekip ve Şoförler",
                  "Ustalar": "Ekip", "Yedek Parça": "Ambalaj ve Malzeme", "Atölye (Cihaz Teslim)": "Depo Teslim", "Günün İş Haritası": "Günün Sefer Haritası", "Fiyat Teklifleri": "Keşif ve Teklifler",
                  "Usta Puanlama": "Ekip Puanlama", "Usta İş Geçmişi": "Ekip Sefer Geçmişi", "Ustadan Para Aldım": "Ekipten Tahsilat"},
        "site": {"services": [("Evden eve nakliyat", "Keşifle başlar, eşyalar paketlenir, sigortalı taşınır ve yerine yerleştirilir."),
                              ("Ofis ve işyeri taşıma", "Hafta sonu ya da mesai dışı planlı taşıma; dosya ve bilgisayarlar sayımla teslim edilir."),
                              ("Asansörlü taşıma", "Yüksek katlarda dış cephe asansörüyle hızlı ve güvenli taşıma."),
                              ("Eşya depolama", "Kısa ve uzun süreli, sigortalı ve temiz depolarda saklama."),
                              ("Paketleme ve montaj", "Mobilya söküm-montaj ve özel paketleme hizmeti.")],
                 "faq": [("Fiyatı nasıl öğrenebilirim?", "Ücretsiz keşifte eşyaları görür, yazılı teklif veririz; teklif dışında ek ücret istenmez."),
                         ("Eşyalarım sigortalı mı?", "Taşıma sırasında oluşabilecek hasar için sigorta kapsamı sözleşmede yazılıdır."),
                         ("Taşıma günü ne kadar sürer?", "Evin büyüklüğüne ve mesafeye göre değişir; keşifte tahmini süreyi söyleriz.")]},
    },
    "tekstil": {
        "name": "Tekstil & Konfeksiyon", "type": "ürün",
        "brands": {"Tişört": [], "Pantolon": [], "Elbise": [], "Ev tekstili": [], "İş kıyafeti": [], "Kumaş (metre)": []},
        "faults": ["Toptan sipariş", "Numune talebi", "Özel üretim", "Baskı / nakış", "İş kıyafeti", "Kumaş satın alma", "Fason üretim", "Ürün iadesi"],
        "checklist": [("Numune onayı alındı", True), ("Beden ve adet tablosu doğrulandı", True), ("Kalite kontrol (dikiş, ütü, etiket)", True), ("Koli ve sevk irsaliyesi", False)],
        "servis": {"foto_once": "istege_bagli", "foto_sonra": "zorunlu"}, "pdf_title": "SİPARİŞ FORMU",
        "terms": {"Servis Kayıtları": "Siparişler", "Randevular": "Numune ve Görüşmeler", "Garanti Talepleri": "İade ve Reklamasyon", "Teknisyenler": "Üretim Ekibi",
                  "Ustalar": "Üretim Ekibi", "Yedek Parça": "Hammadde ve Stok", "Atölye (Cihaz Teslim)": "Üretim Takibi", "Günün İş Haritası": "Bugünkü Sevkiyatlar", "Fiyat Teklifleri": "Numune ve Teklifler",
                  "Usta Puanlama": "Ekip Performansı", "Usta İş Geçmişi": "Ekip Üretim Geçmişi", "Ustadan Para Aldım": "Ekipten Tahsilat", "Bayilik Başvuruları": "Toptan Müşteri Başvuruları"},
        "site": {"services": [("Toptan hazır giyim", "Minimum adet ve fiyat listesiyle bayi ve mağazalara toptan satış."),
                              ("Özel üretim ve fason", "Model, kumaş ve adedinize göre numune çıkarır, onayınızdan sonra üretiriz."),
                              ("Baskı ve nakış", "Logo ve desenlerinizi tişört, şapka ve iş kıyafetine uygularız."),
                              ("İş kıyafeti ve üniforma", "Firma renklerinizde, beden tablosuyla toplu üretim."),
                              ("Ev tekstili", "Nevresim, havlu ve perde için toptan ve özel ölçü seçenekleri.")],
                 "faq": [("Minimum sipariş adedi nedir?", "Ürüne göre değişir; model sayfasında ve fiyat listesinde yazar."),
                         ("Numune alabilir miyim?", "Evet; numune ücreti ve süresi teklifte belirtilir, siparişe dönüşürse düşülebilir."),
                         ("Teslim süresi ne kadar?", "Stoktaki ürünler hemen, üretim siparişleri onaydan sonra belirtilen sürede sevk edilir.")]},
    },
    "eticaret": {
        "name": "E-Ticaret & Mağaza", "type": "ürün",
        "brands": {"Giyim": [], "Ayakkabı & Çanta": [], "Ev & Yaşam": [], "Kozmetik": [], "Elektronik Aksesuar": [], "Hediyelik": []},
        "faults": ["Sipariş durumu", "Kargo takibi", "İade talebi", "Değişim talebi", "Ürün bilgisi", "Toplu alım", "Faturalama", "Stok sorusu"],
        "checklist": [("Ürün stok ve fiyat doğrulandı", True), ("Kargo etiketi ve paketleme", True), ("İade ürünü kontrol edildi", False), ("Müşteriye bilgilendirme gönderildi", False)],
        "servis": {"foto_once": "istege_bagli", "foto_sonra": "istege_bagli"}, "pdf_title": "SİPARİŞ FİŞİ",
        "terms": {"Servis Kayıtları": "Siparişler", "Randevular": "Müşteri Görüşmeleri", "Garanti Talepleri": "İade ve Değişim", "Teknisyenler": "Ekip",
                  "Ustalar": "Ekip", "Yedek Parça": "Ürün Stoğu", "Atölye (Cihaz Teslim)": "Depo ve Paketleme", "Günün İş Haritası": "Bugünkü Kargolar", "Fiyat Teklifleri": "Toplu Alım Teklifleri",
                  "Usta Puanlama": "Ekip Performansı", "Usta İş Geçmişi": "Ekip Geçmişi", "Ustadan Para Aldım": "Ekipten Tahsilat", "Bayilik Başvuruları": "Bayi Başvuruları"},
        "site": {"services": [("Online sipariş", "Ürünleri sepete ekleyin, kapıda ya da kartla ödeyin; sipariş durumunu SMS ile takip edin."),
                              ("Hızlı kargo", "Hafta içi verilen siparişler aynı gün ya da ertesi iş günü kargoya verilir."),
                              ("Kolay iade ve değişim", "Ürünü teslim aldıktan sonra yasal süre içinde iade veya değişim talebi oluşturun."),
                              ("Toplu alım ve kurumsal satış", "Adet ve kurumsal fatura için özel fiyat teklifi alın."),
                              ("Hediye paketi", "Siparişte not ve hediye paketi seçeneği.")],
                 "faq": [("Siparişim ne zaman kargoya verilir?", "Stoktaki ürünler aynı gün ya da ertesi iş günü kargoya verilir; takip kodu SMS ile gelir."),
                         ("İade nasıl yapılır?", "Siparişim sayfasından iade talebi açarsınız; kargo kodu size iletilir."),
                         ("Hangi ödeme yöntemleri var?", "Kredi kartı, havale/EFT ve seçili ürünlerde kapıda ödeme.")]},
    },
    "temizlik": {
        "name": "Temizlik & Bakım", "type": "hizmet",
        "brands": {"Ev temizliği": [], "Ofis temizliği": [], "İnşaat sonrası": [], "Halı yıkama": [], "Koltuk yıkama": [], "Cam silme": []},
        "faults": ["Ev temizliği", "Ofis temizliği", "İnşaat sonrası temizlik", "Halı yıkama", "Koltuk yıkama", "Cam silme", "Taşınma sonrası", "Düzenli abonelik"],
        "checklist": [("Alan ve oda sayısı teyit edildi", True), ("Önce / sonra fotoğraf", True), ("Müşteri kontrol onayı", True), ("Malzeme ve ekipman sayımı", False)],
        "servis": {"foto_once": "zorunlu", "foto_sonra": "zorunlu"}, "pdf_title": "HİZMET FORMU",
        "terms": {"Servis Kayıtları": "Temizlik İşleri", "Randevular": "Planlı Temizlikler", "Garanti Talepleri": "Memnuniyet / Tekrar Talepleri", "Teknisyenler": "Temizlik Ekibi",
                  "Ustalar": "Ekip", "Yedek Parça": "Malzeme Stoku", "Atölye (Cihaz Teslim)": "Halı / Koltuk Teslim", "Günün İş Haritası": "Günün Adresleri", "Fiyat Teklifleri": "Keşif ve Teklifler"},
        "site": {"services": [("Ev temizliği", "Oda sayınıza göre planlanır; malzeme dahil ya da sizin ürünlerinizle."),
                              ("Ofis ve işyeri", "Mesai dışı, düzenli abonelik seçenekli temizlik."),
                              ("İnşaat sonrası temizlik", "Boya, alçı ve toz kalıntılarını detaylıca temizleriz."),
                              ("Halı ve koltuk yıkama", "Adresten alım, yıkama, kurutma ve teslim."),
                              ("Cam silme", "Dış cephe ve yüksek cam temizliği, güvenlik ekipmanlı.")],
                 "faq": [("Malzeme dahil mi?", "Teklifte yazar; isterseniz kendi ürünlerinizle de çalışırız."),
                         ("Fiyat nasıl belirleniyor?", "Metrekare ve temizlik türüne göre; keşif ya da fotoğraf üzerinden net fiyat veririz."),
                         ("Düzenli hizmet alabilir miyim?", "Haftalık ya da aylık abonelik planı oluşturabiliriz.")]},
    },
    "guzellik": {
        "name": "Güzellik & Estetik Salonu", "type": "hizmet",
        "brands": {"Cilt bakımı": [], "Lazer epilasyon": [], "Manikür / pedikür": [], "Kaş ve kirpik": [], "Masaj": [], "Makyaj": []},
        "faults": ["Cilt bakımı", "Lazer epilasyon", "Manikür", "Pedikür", "Kaş tasarımı", "Kirpik", "Masaj", "Makyaj"],
        "checklist": [("Onam / hassasiyet formu", True), ("İşlem öncesi fotoğraf", False), ("Kullanılan ürün karta işlendi", False), ("Sonraki seans planlandı", False)],
        "servis": {"foto_once": "istege_bagli", "foto_sonra": "istege_bagli"}, "pdf_title": "SEANS FİŞİ",
        "terms": {"Servis Kayıtları": "Seans Defteri", "Randevular": "Online Randevular", "Garanti Talepleri": "Memnuniyet Talepleri", "Teknisyenler": "Uzmanlar",
                  "Ustalar": "Uzmanlar", "Yedek Parça": "Ürün ve Sarf Stoku", "Atölye (Cihaz Teslim)": "Kabin Takibi", "Günün İş Haritası": "Günün Seansları", "Fiyat Teklifleri": "Paket Teklifleri",
                  "Usta Puanlama": "Uzman Puanlama", "Usta İş Geçmişi": "Uzman Seans Geçmişi", "Ustadan Para Aldım": "Uzmandan Tahsilat"},
        "site": {"services": [("Cilt bakımı", "Cilt analizinden sonra size uygun bakım planı çıkarırız."),
                              ("Lazer epilasyon", "Seans planı ve paket seçenekleri randevuda anlatılır."),
                              ("Manikür ve pedikür", "Hijyenik ekipmanla, tek kullanımlık malzemeyle."),
                              ("Kaş ve kirpik", "Yüz hatlarınıza uygun kaş tasarımı, kirpik uygulamaları."),
                              ("Masaj ve rahatlama", "Seans süreleri ve türleri randevuda seçilir.")],
                 "faq": [("İlk seans öncesi ne yapmalıyım?", "Randevu mesajında işleme özel hazırlık bilgisi iletilir."),
                         ("Paket alırsam seanslarımı nasıl takip ederim?", "Kalan seans sayınız kartınızda ve randevu mesajlarında görünür."),
                         ("Hassasiyetim varsa?", "İşlemden önce mutlaka söyleyin; formu birlikte doldururuz.")]},
    },
}

# Giriş formunda sektör seçimi için (yazılış -> anahtar)
SECTOR_WORDS = {"oto servis": "oto_servis", "oto tamir": "oto_servis", "oto çekici": "oto_cekici", "çekici": "oto_cekici", "yol yardım": "oto_cekici",
                "kuaför": "kuafor", "berber": "kuafor", "nakliye": "nakliye", "nakliyat": "nakliye", "tekstil": "tekstil", "konfeksiyon": "tekstil",
                "e-ticaret": "eticaret", "eticaret": "eticaret", "mağaza": "eticaret", "temizlik": "temizlik", "güzellik": "guzellik", "estetik": "guzellik"}

# Örnek veri (demo firma): sektör -> (müşteri tipi, talepler)
DEMO_FAULTS = {k: v["faults"][:4] for k, v in NEW.items()}


def terms_for(key, base_sectors=None):
    s = NEW.get(key)
    return dict(s["terms"]) if s else {}


# Demo örnek kaydında kullanılan sektör dili: (model/ürün, yapılan iş, parça/malzeme adı)
DEMO_META = {
    "oto_servis": ("Renault Clio 1.5 dCi", "Periyodik bakım yapıldı, yağ ve filtreler değiştirildi.", "Yağ filtresi seti"),
    "oto_cekici": ("Fiat Egea", "Araç yüklendi ve anlaşmalı servise teslim edildi.", "Akü takviye hizmeti"),
    "kuafor": ("Saç kesimi + fön", "İşlem tamamlandı, bakım önerisi verildi.", "Bakım ürünü"),
    "nakliye": ("3+1 ev, 3. kat", "Eşyalar paketlendi, taşındı ve yerleştirildi.", "Koli ve ambalaj"),
    "tekstil": ("Tişört, 200 adet", "Üretim tamamlandı, kalite kontrolden geçti, sevk edildi.", "Kumaş ve aksesuar"),
    "eticaret": ("Sipariş #1042", "Sipariş hazırlandı ve kargoya verildi.", "Ürün"),
    "temizlik": ("3+1 daire", "Temizlik tamamlandı, müşteri kontrolü yapıldı.", "Temizlik malzemesi"),
    "guzellik": ("Cilt bakımı seansı", "Seans tamamlandı, sonraki randevu planlandı.", "Seans ürünü"),
}


# Demo mağaza ürünleri (e-ticaret ve tekstil): (ad, marka, kategori, fiyat, eski fiyat, stok). Fotoğraf yoksa vitrinde ürüne özel çizim görünür.
DEMO_URUN = {
    "eticaret": [("Deri omuz çantası", "Atölye", "Çanta", 1290, 1590, 14), ("Koşu ayakkabısı", "Atölye", "Ayakkabı", 1850, 0, 22), ("Pamuklu basic tişört", "Atölye", "Giyim", 349, 429, 60),
                 ("Cam parfüm şişesi 50 ml", "Atölye", "Kozmetik", 780, 0, 18), ("Telefon kılıfı", "Atölye", "Aksesuar", 220, 0, 90), ("Seramik masa lambası", "Atölye", "Ev & Yaşam", 940, 1100, 9),
                 ("Çelik kasa kol saati", "Atölye", "Saat", 2450, 0, 7), ("Hediye seti", "Atölye", "Hediyelik", 690, 0, 25)],
    "tekstil": [("Penye tişört (12'li koli)", "Atölye", "Giyim", 1980, 2300, 40), ("Kot pantolon (10'lu)", "Atölye", "Giyim", 3200, 0, 25), ("İş ceketi (toptan)", "Atölye", "İş kıyafeti", 4100, 0, 15),
                ("Havlu seti", "Atölye", "Ev tekstili", 760, 890, 30), ("Elbise (8'li)", "Atölye", "Giyim", 2750, 0, 18), ("Kumaş topu 40 m", "Atölye", "Kumaş", 2200, 0, 12)],
}
