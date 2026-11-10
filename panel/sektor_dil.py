"""Sektör dili: her sektör için panelde görünen teknik servis kelimelerinin (usta, teknisyen, cihaz, arıza, servis kaydı, yedek parça,
garanti ...) o işe uygun karşılıkları. Menü etiketleri (terms) ve kelime düzeyi sözlük (lex) buradan üretilir.
Teknik servis sektörleri (kombi, klima, ...) değişmez: orada bu kelimeler zaten doğrudur."""

# alan sırası: kisi (tekil/çoğul), is (tekil/çoğul: panelde 'servis kaydı'), cihaz (tekil/çoğul), sorun (tekil),
#              garanti (tekil), stok, yer, gun, teklif
F = ("kisi", "is", "cihaz", "sorun", "garanti", "stok", "yer", "gun", "teklif")


def _r(kisi, is_, cihaz, sorun, garanti, stok, yer, gun, teklif):
    return dict(zip(F, (kisi, is_, cihaz, sorun, garanti, stok, yer, gun, teklif)))


ROWS = {
    # --- güzellik / bakım
    "kuafor": _r("Uzman/Uzmanlar", "Randevu/Randevu Defteri", "Hizmet/Hizmetler", "Şikâyet", "Memnuniyet", "Ürün ve Sarf Stoku", "Koltuk Takibi", "Günün Randevuları", "Paket Teklifleri"),
    "guzellik": _r("Uzman/Uzmanlar", "Seans/Seans Defteri", "Uygulama/Uygulamalar", "Şikâyet", "Memnuniyet", "Ürün ve Sarf Stoku", "Kabin Takibi", "Günün Seansları", "Paket Teklifleri"),
    "tirnak_studyo": _r("Uzman/Uzmanlar", "Randevu/Randevu Defteri", "Uygulama/Uygulamalar", "Şikâyet", "Memnuniyet", "Ürün ve Sarf Stoku", "Masa Takibi", "Günün Randevuları", "Paket Teklifleri"),
    "estetik_merkezi": _r("Uzman/Uzmanlar", "Randevu/Randevu Defteri", "Hasta/Hastalar", "Şikâyet", "Memnuniyet", "Ürün ve Sarf Stoku", "Oda Takibi", "Günün Randevuları", "Tedavi Paketleri"),
    "spa_hamam": _r("Terapist/Terapistler", "Randevu/Randevu Defteri", "Hizmet/Hizmetler", "Şikâyet", "Memnuniyet", "Ürün ve Sarf Stoku", "Kabin Takibi", "Günün Randevuları", "Paket Teklifleri"),
    "dovme_studyo": _r("Sanatçı/Sanatçılar", "Randevu/Randevu Defteri", "Tasarım/Tasarımlar", "Şikâyet", "Memnuniyet", "Ürün ve Sarf Stoku", "Koltuk Takibi", "Günün Randevuları", "Çalışma Teklifleri"),
    "evcil_hayvan": _r("Bakım Uzmanı/Bakım Uzmanları", "Randevu/Randevu Defteri", "Hayvan/Hayvanlar", "Şikâyet", "Memnuniyet", "Ürün ve Sarf Stoku", "Pansiyon Takibi", "Günün Randevuları", "Paket Teklifleri"),
    # --- sağlık / danışmanlık
    "dis_klinigi": _r("Hekim/Hekimler", "Randevu/Randevu Defteri", "Hasta/Hastalar", "Şikâyet", "Memnuniyet", "Sarf Malzeme Stoku", "Oda Takibi", "Günün Randevuları", "Tedavi Planları"),
    "psikolog": _r("Terapist/Terapistler", "Seans/Seans Defteri", "Danışan/Danışanlar", "Konu", "Memnuniyet", "Sarf Malzeme Stoku", "Oda Takibi", "Günün Seansları", "Seans Paketleri"),
    "diyetisyen": _r("Diyetisyen/Diyetisyenler", "Randevu/Randevu Defteri", "Danışan/Danışanlar", "Konu", "Memnuniyet", "Ürün Stoku", "Görüşme Takibi", "Günün Randevuları", "Program Paketleri"),
    "fizyoterapi": _r("Fizyoterapist/Fizyoterapistler", "Seans/Seans Defteri", "Hasta/Hastalar", "Şikâyet", "Memnuniyet", "Sarf Malzeme Stoku", "Kabin Takibi", "Günün Seansları", "Tedavi Paketleri"),
    "veteriner": _r("Veteriner Hekim/Veteriner Hekimler", "Randevu/Randevu Defteri", "Hasta/Hastalar", "Şikâyet", "Memnuniyet", "İlaç ve Mama Stoku", "Muayene Odası Takibi", "Günün Randevuları", "Tedavi Teklifleri"),
    "aile_danisman": _r("Danışman/Danışmanlar", "Seans/Seans Defteri", "Danışan/Danışanlar", "Konu", "Memnuniyet", "Materyal Stoku", "Oda Takibi", "Günün Seansları", "Seans Paketleri"),
    "optik": _r("Optisyen/Optisyenler", "Randevu/Randevu Defteri", "Müşteri/Müşteriler", "Şikâyet", "Garanti", "Gözlük ve Lens Stoku", "Atölye Takibi", "Günün Randevuları", "Teklifler"),
    # --- hukuk / finans / çeviri
    "avukat": _r("Avukat/Avukatlar", "Dosya/Dosyalar", "Müvekkil/Müvekkiller", "Konu", "Memnuniyet", "Kırtasiye Stoku", "Görüşme Takibi", "Günün Görüşmeleri", "Ücret Teklifleri"),
    "muhasebe": _r("Müşavir/Müşavirler", "Dosya/Dosyalar", "Mükellef/Mükellefler", "Konu", "Memnuniyet", "Kırtasiye Stoku", "Görüşme Takibi", "Günün Görüşmeleri", "Hizmet Teklifleri"),
    "tercume": _r("Tercüman/Tercümanlar", "Çeviri Kaydı/Çeviri Kayıtları", "Belge/Belgeler", "Konu", "Revizyon", "Kırtasiye Stoku", "Teslim Takibi", "Bugünkü Teslimler", "Çeviri Teklifleri"),
    # --- eğitim
    "surucu_kursu": _r("Eğitmen/Eğitmenler", "Kursiyer Kaydı/Kursiyer Kayıtları", "Kursiyer/Kursiyerler", "Konu", "Memnuniyet", "Direksiyon Araç Stoku", "Sınıf ve Araç Takibi", "Günün Dersleri", "Kurs Teklifleri"),
    "src_kursu": _r("Eğitmen/Eğitmenler", "Kursiyer Kaydı/Kursiyer Kayıtları", "Kursiyer/Kursiyerler", "Konu", "Memnuniyet", "Eğitim Materyali Stoku", "Sınıf Takibi", "Günün Dersleri", "Kurs Teklifleri"),
    "etut_merkezi": _r("Eğitmen/Eğitmenler", "Öğrenci Kaydı/Öğrenci Kayıtları", "Öğrenci/Öğrenciler", "Konu", "Memnuniyet", "Kitap ve Materyal Stoku", "Sınıf Takibi", "Günün Dersleri", "Kayıt Teklifleri"),
    "dil_okulu": _r("Eğitmen/Eğitmenler", "Öğrenci Kaydı/Öğrenci Kayıtları", "Öğrenci/Öğrenciler", "Konu", "Memnuniyet", "Kitap ve Materyal Stoku", "Sınıf Takibi", "Günün Dersleri", "Kayıt Teklifleri"),
    "muzik_kursu": _r("Eğitmen/Eğitmenler", "Öğrenci Kaydı/Öğrenci Kayıtları", "Öğrenci/Öğrenciler", "Konu", "Memnuniyet", "Enstrüman ve Materyal Stoku", "Stüdyo Takibi", "Günün Dersleri", "Kayıt Teklifleri"),
    "anaokulu": _r("Öğretmen/Öğretmenler", "Çocuk Kaydı/Çocuk Kayıtları", "Çocuk/Çocuklar", "Konu", "Memnuniyet", "Materyal Stoku", "Sınıf Takibi", "Günün Programı", "Kayıt Teklifleri"),
    "ozel_ders": _r("Eğitmen/Eğitmenler", "Öğrenci Kaydı/Öğrenci Kayıtları", "Öğrenci/Öğrenciler", "Konu", "Memnuniyet", "Materyal Stoku", "Ders Takibi", "Günün Dersleri", "Ders Paketleri"),
    "bilgisayar_kursu": _r("Eğitmen/Eğitmenler", "Kursiyer Kaydı/Kursiyer Kayıtları", "Kursiyer/Kursiyerler", "Konu", "Memnuniyet", "Ekipman Stoku", "Sınıf Takibi", "Günün Dersleri", "Kurs Teklifleri"),
    "yuzme_kursu": _r("Eğitmen/Eğitmenler", "Kursiyer Kaydı/Kursiyer Kayıtları", "Kursiyer/Kursiyerler", "Konu", "Memnuniyet", "Ekipman Stoku", "Havuz Takibi", "Günün Dersleri", "Kurs Teklifleri"),
    "spor_salonu": _r("Antrenör/Antrenörler", "Üye Kaydı/Üye Kayıtları", "Üye/Üyeler", "Konu", "Memnuniyet", "Ekipman ve Ürün Stoku", "Salon Takibi", "Günün Dersleri", "Üyelik Teklifleri"),
    "yoga_dans": _r("Eğitmen/Eğitmenler", "Üye Kaydı/Üye Kayıtları", "Üye/Üyeler", "Konu", "Memnuniyet", "Ekipman Stoku", "Stüdyo Takibi", "Günün Dersleri", "Üyelik Teklifleri"),
    # --- satış / üretim
    "eticaret": _r("Çalışan/Çalışanlar", "Sipariş/Siparişler", "Ürün/Ürünler", "Şikâyet", "İade ve Değişim", "Ürün Stoğu", "Depo ve Paketleme", "Bugünkü Kargolar", "Toplu Alım Teklifleri"),
    "tekstil": _r("Üretim Personeli/Üretim Ekibi", "Sipariş/Siparişler", "Ürün/Ürünler", "Şikâyet", "İade ve Reklamasyon", "Hammadde ve Stok", "Üretim Takibi", "Bugünkü Sevkiyatlar", "Numune ve Teklifler"),
    "market": _r("Personel/Personel", "Sipariş/Siparişler", "Ürün/Ürünler", "Şikâyet", "İade ve Değişim", "Raf ve Depo Stoku", "Hazırlama Takibi", "Bugünkü Teslimatlar", "Toplu Alım Teklifleri"),
    "cicekci": _r("Personel/Personel", "Sipariş/Siparişler", "Ürün/Ürünler", "Şikâyet", "İade ve Değişim", "Çiçek ve Malzeme Stoku", "Hazırlama Takibi", "Bugünkü Teslimatlar", "Organizasyon Teklifleri"),
    "pastane": _r("Personel/Personel", "Sipariş/Siparişler", "Ürün/Ürünler", "Şikâyet", "İade ve Değişim", "Hammadde Stoku", "Fırın ve Üretim Takibi", "Bugünkü Siparişler", "Özel Sipariş Teklifleri"),
    "kuyumcu_saat": _r("Usta/Ustalar", "Tamir Kaydı/Tamir Kayıtları", "Saat ve Takı/Saat ve Takılar", "Sorun", "Garanti", "Parça ve Malzeme Stoku", "Tezgâh Takibi", "Bugünkü Teslimler", "Tamir Teklifleri"),
    "matbaa": _r("Operatör/Operatörler", "İş Emri/İş Emirleri", "Baskı İşi/Baskı İşleri", "Sorun", "Reklamasyon", "Kâğıt ve Mürekkep Stoku", "Üretim Takibi", "Bugünkü Teslimler", "Baskı Teklifleri"),
    "terzi": _r("Terzi/Terziler", "Sipariş/Siparişler", "Kıyafet/Kıyafetler", "Sorun", "Düzeltme", "Kumaş ve Malzeme Stoku", "Prova Takibi", "Bugünkü Provalar", "Dikim Teklifleri"),
    "mimar": _r("Mimar/Mimarlar", "Proje Kaydı/Proje Kayıtları", "Proje/Projeler", "Konu", "Revizyon", "Malzeme Numune Stoku", "Proje Takibi", "Günün Görüşmeleri", "Proje Teklifleri"),
    "mobilya": _r("Usta/Ustalar", "İş Emri/İş Emirleri", "Mobilya/Mobilyalar", "Sorun", "Garanti", "Malzeme Stoku", "Atölye Takibi", "Günün İş Haritası", "Fiyat Teklifleri"),
    # --- yemek / etkinlik
    "lokanta": _r("Personel/Personel", "Sipariş/Siparişler", "Masa/Masalar", "Şikâyet", "Geri Bildirim", "Mutfak Stoku", "Masa Takibi", "Bugünkü Rezervasyonlar", "Grup ve Etkinlik Teklifleri"),
    "catering": _r("Personel/Personel", "Sipariş/Siparişler", "Menü/Menüler", "Şikâyet", "Geri Bildirim", "Mutfak ve Malzeme Stoku", "Organizasyon Takibi", "Bugünkü Organizasyonlar", "Organizasyon Teklifleri"),
    "dugun_salonu": _r("Personel/Personel", "Rezervasyon/Rezervasyonlar", "Salon/Salonlar", "Konu", "Geri Bildirim", "Ekipman ve Malzeme Stoku", "Salon Takibi", "Bugünkü Organizasyonlar", "Organizasyon Teklifleri"),
    "dj_muzik": _r("Teknisyen/Teknisyenler", "Etkinlik Kaydı/Etkinlik Kayıtları", "Ekipman/Ekipmanlar", "Sorun", "Geri Bildirim", "Ekipman Stoku", "Depo Takibi", "Bugünkü Etkinlikler", "Etkinlik Teklifleri"),
    "fotografci": _r("Fotoğrafçı/Fotoğrafçılar", "Çekim Kaydı/Çekim Kayıtları", "Çekim/Çekimler", "Konu", "Revizyon", "Ekipman ve Albüm Stoku", "Stüdyo Takibi", "Bugünkü Çekimler", "Çekim Teklifleri"),
    "tur_organizasyon": _r("Rehber/Rehberler", "Rezervasyon/Rezervasyonlar", "Tur/Turlar", "Konu", "Geri Bildirim", "Ekipman Stoku", "Program Takibi", "Bugünkü Turlar", "Tur Teklifleri"),
    # --- araç / taşıma
    "oto_servis": _r("Usta/Ustalar", "İş Emri/İş Emirleri", "Araç/Araçlar", "Arıza", "Garanti", "Yedek Parça", "Servis Takibi", "Günün İş Haritası", "Fiyat Teklifleri"),
    "oto_cekici": _r("Sürücü/Sürücüler", "Çağrı/Çekici Çağrıları", "Araç/Araçlar", "Arıza", "Memnuniyet", "Ekipman Stoku", "Araç Takibi", "Günün Çağrıları", "Fiyat Teklifleri"),
    "oto_yikama": _r("Uzman/Uzmanlar", "Randevu/Randevu Defteri", "Araç/Araçlar", "Şikâyet", "Memnuniyet", "Ürün ve Sarf Stoku", "Yıkama Alanı Takibi", "Günün Randevuları", "Paket Teklifleri"),
    "oto_kaplama": _r("Uygulayıcı/Uygulayıcılar", "Randevu/Randevu Defteri", "Araç/Araçlar", "Şikâyet", "Garanti", "Kaplama Malzemesi Stoku", "Atölye Takibi", "Günün Randevuları", "Paket Teklifleri"),
    "lastikci": _r("Usta/Ustalar", "İş Emri/İş Emirleri", "Araç/Araçlar", "Sorun", "Garanti", "Lastik ve Jant Stoku", "Atölye Takibi", "Günün İş Haritası", "Fiyat Teklifleri"),
    "arac_kiralama": _r("Danışman/Danışmanlar", "Kiralama/Kiralamalar", "Araç/Araçlar", "Konu", "Memnuniyet", "Araç ve Aksesuar Stoku", "Filo Takibi", "Bugünkü Teslimler", "Kiralama Teklifleri"),
    "transfer": _r("Şoför/Şoförler", "Transfer/Transferler", "Araç/Araçlar", "Konu", "Memnuniyet", "Araç Stoku", "Araç Takibi", "Bugünkü Transferler", "Transfer Teklifleri"),
    "nakliye": _r("Ekip Üyesi/Ekip", "Taşıma İşi/Taşıma İşleri", "Eşya/Eşyalar", "Sorun", "Hasar Talebi", "Malzeme Stoku", "Araç Takibi", "Günün Taşımaları", "Taşıma Teklifleri"),
    "kurye": _r("Kurye/Kuryeler", "Teslimat/Teslimatlar", "Paket/Paketler", "Konu", "Memnuniyet", "Ekipman Stoku", "Dağıtım Takibi", "Bugünkü Teslimatlar", "Teslimat Teklifleri"),
    "emlakci": _r("Danışman/Danışmanlar", "Müşteri Talebi/Müşteri Talepleri", "İlan/İlanlar", "Konu", "Takip Notu", "Tanıtım Malzemeleri", "Portföy Takibi", "Günün Gösterimleri", "Teklifler"),
    # --- ev / saha hizmetleri (usta kavramı doğru kalan işler)
    "temizlik": _r("Temizlik Personeli/Ekip", "Temizlik İşi/Temizlik İşleri", "Adres/Adresler", "Şikâyet", "Memnuniyet", "Malzeme Stoku", "Ekip Takibi", "Günün Temizlikleri", "Fiyat Teklifleri"),
    "hali_yikama": _r("Personel/Personel", "Yıkama İşi/Yıkama İşleri", "Halı/Halılar", "Şikâyet", "Memnuniyet", "Kimyasal ve Malzeme Stoku", "Yıkama ve Kurutma Takibi", "Bugünkü Teslimler", "Fiyat Teklifleri"),
    "kuru_temizleme": _r("Personel/Personel", "Sipariş/Siparişler", "Kıyafet/Kıyafetler", "Şikâyet", "Memnuniyet", "Kimyasal ve Malzeme Stoku", "Üretim Takibi", "Bugünkü Teslimler", "Fiyat Teklifleri"),
    "ayakkabi_tamir": _r("Usta/Ustalar", "Tamir Kaydı/Tamir Kayıtları", "Ayakkabı/Ayakkabılar", "Sorun", "Garanti", "Malzeme Stoku", "Tezgâh Takibi", "Bugünkü Teslimler", "Tamir Teklifleri"),
    "telefon_tamir": _r("Teknisyen/Teknisyenler", "Tamir Kaydı/Tamir Kayıtları", "Cihaz/Cihazlar", "Arıza", "Garanti", "Yedek Parça", "Tezgâh Takibi", "Bugünkü Teslimler", "Fiyat Teklifleri"),
    "peyzaj": _r("Usta/Ustalar", "İş Emri/İş Emirleri", "Proje/Projeler", "Sorun", "Garanti", "Bitki ve Malzeme Stoku", "Saha Takibi", "Günün İş Haritası", "Keşif ve Teklifler"),
    "bocek_ilaclama": _r("Uygulayıcı/Uygulayıcılar", "İlaçlama İşi/İlaçlama İşleri", "Adres/Adresler", "Sorun", "Garanti", "İlaç ve Ekipman Stoku", "Saha Takibi", "Günün İş Haritası", "Keşif ve Teklifler"),
    "tadilat": _r("Usta/Ustalar", "İş Emri/İş Emirleri", "Proje/Projeler", "Sorun", "Garanti", "Malzeme Stoku", "Şantiye Takibi", "Günün İş Haritası", "Keşif ve Teklifler"),
    "cilingir": _r("Çilingir/Çilingirler", "Çağrı/Çağrılar", "Kilit/Kilitler", "Sorun", "Garanti", "Kilit ve Anahtar Stoku", "Araç ve Ekip Takibi", "Günün Çağrıları", "Fiyat Teklifleri"),
    "cam_dograma": _r("Usta/Ustalar", "İş Emri/İş Emirleri", "Ürün/Ürünler", "Sorun", "Garanti", "Profil ve Cam Stoku", "Atölye Takibi", "Günün İş Haritası", "Keşif ve Teklifler"),
    "asansor": _r("Teknisyen/Teknisyenler", "Servis Kaydı/Servis Kayıtları", "Asansör/Asansörler", "Arıza", "Garanti", "Yedek Parça", "Bakım Takibi", "Günün İş Haritası", "Bakım Teklifleri"),
    "su_aritma": _r("Teknisyen/Teknisyenler", "Servis Kaydı/Servis Kayıtları", "Cihaz/Cihazlar", "Arıza", "Garanti", "Filtre ve Yedek Parça", "Servis Takibi", "Günün İş Haritası", "Fiyat Teklifleri"),
    "gunes_enerjisi": _r("Montaj Ekibi/Montaj Ekibi", "İş Emri/İş Emirleri", "Sistem/Sistemler", "Arıza", "Garanti", "Panel ve Ekipman Stoku", "Saha Takibi", "Günün İş Haritası", "Keşif ve Teklifler"),
    "havuz_bakim": _r("Bakım Teknisyeni/Bakım Ekibi", "Bakım Kaydı/Bakım Kayıtları", "Havuz/Havuzlar", "Sorun", "Garanti", "Kimyasal ve Ekipman Stoku", "Saha Takibi", "Günün İş Haritası", "Bakım Teklifleri"),
    "jenerator": _r("Teknisyen/Teknisyenler", "Servis Kaydı/Servis Kayıtları", "Jeneratör/Jeneratörler", "Arıza", "Garanti", "Yedek Parça", "Servis Takibi", "Günün İş Haritası", "Fiyat Teklifleri"),
    "yazici_servis": _r("Teknisyen/Teknisyenler", "Servis Kaydı/Servis Kayıtları", "Cihaz/Cihazlar", "Arıza", "Garanti", "Yedek Parça ve Toner Stoku", "Servis Takibi", "Günün İş Haritası", "Fiyat Teklifleri"),
}
# teknik servis sektörleri: kelimeler olduğu gibi kalır
SADE = ("kombi", "klima", "beyaz_esya", "elektronik", "bilgisayar", "tesisat", "elektrik", "guvenlik")


def _sp(x):
    a, _, b = x.partition("/")
    return a, (b or a)


RDV = {"eticaret": "Müşteri Görüşmeleri", "tekstil": "Numune ve Görüşmeler", "market": "Teslimat Saatleri", "lokanta": "Masa Rezervasyonları", "catering": "Tadım ve Görüşmeler", "dugun_salonu": "Salon Gezme Randevuları",
       "pastane": "Teslim Randevuları", "cicekci": "Teslim Randevuları", "kurye": "Alım Randevuları", "nakliye": "Keşif Randevuları", "emlakci": "Yer Gösterme Randevuları", "arac_kiralama": "Teslim Randevuları",
       "transfer": "Transfer Randevuları", "tur_organizasyon": "Görüşme Randevuları", "mimar": "Görüşme Randevuları", "matbaa": "Baskı Görüşmeleri", "dj_muzik": "Görüşme Randevuları", "fotografci": "Çekim Randevuları"}
GAR = {"İade ve Değişim": "İade ve Değişim", "İade ve Reklamasyon": "İade ve Reklamasyon", "Hasar Talebi": "Hasar Talepleri", "Geri Bildirim": "Geri Bildirimler", "Takip Notu": "Takip Notları"}


def labels(key):
    """Menü etiketi eşlemesi (eski 'terms' biçimi): özgün başlık -> sektöre uygun başlık."""
    r = ROWS.get(key)
    if not r:
        return {}
    ks, kp = _sp(r["kisi"])
    isg, ipl = _sp(r["is"])
    ab = _abl(ks)
    t = {
        "Servis Kayıtları": ipl, "Randevular": RDV.get(key, "Online Randevular"), "Garanti Talepleri": GAR.get(r["garanti"], r["garanti"] + " Talepleri"),
        "Teknisyenler": kp, "Ustalar": kp, "Yedek Parça": r["stok"], "Atölye (Cihaz Teslim)": r["yer"], "Günün İş Haritası": r["gun"], "Fiyat Teklifleri": r["teklif"],
        "Usta Puanlama": ks + " Puanlama", "Usta İş Geçmişi": ks + " Geçmişi", "Ustadan Para Aldım": ks + ab + " Tahsilat",
        "Ustaların Borç Durumu": ks + " Hesapları", "Geciken Usta Borçları": "Geciken " + ks + " Hesapları",
    }
    return t


_VOW = "aeıioöuü"
_BACK = "aıou"


def _last_vowel(w):
    for c in reversed(w.lower()):
        if c in _VOW:
            return c
    return "e"


def _abl(w):
    """'Uzmanlar' -> 'dan/den' eki (Uzmanlardan -> 'Uzmanlar' + 'dan'); yalnızca ek döndürür (ünlü uyumu + sert ünsüz)."""
    lw = w.lower().rstrip()
    v = _last_vowel(lw)
    if lw[-1] in _VOW:
        return "nd" + ("a" if v in _BACK else "e") + "n"
    hard = lw[-1] in "çfhkpsşt"
    return ("t" if hard else "d") + ("a" if v in _BACK else "e") + "n"


def lex(key):
    """Kelime düzeyi sözlük: panel metinlerindeki usta/cihaz/arıza... kelimelerinin karşılıkları. SADE sektörlerde boş."""
    r = ROWS.get(key)
    if not r:
        return {}
    ks, kp = _sp(r["kisi"])
    isg, ipl = _sp(r["is"])
    cs, cp = _sp(r["cihaz"])
    return {"kisi": [ks, kp], "is": [isg, ipl], "cihaz": [cs, cp], "sorun": r["sorun"], "stok": r["stok"]}
