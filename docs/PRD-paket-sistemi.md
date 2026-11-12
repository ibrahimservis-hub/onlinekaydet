# OnlineKaydet — Sektörel Paket Sistemi (PRD v2)

> Sahibinin 2026-11-12 tarihli talimatlarının tamamı. **Bu belge yol haritasıdır, silinmez.**
> Hedef: **Ticimax / İdeaSoft / ikas / Qukasoft'tan daha iyi**, geliştirilebilir, son teknoloji.
> Rakip incelemesi: qukasoft.com (özellik listesi alındı), kobicms.com, ticimax, ideasoft, ikas.

---

## 0. TEMEL MANTIK — "BÖLÜM EKLE" MİMARİSİ
Bölüm, modül, ekran, rapor, entegrasyon, iş akışı, rozet, bildirim metni — hepsi **veri kaydı**, kod değil.
Yeni sektör açmak = var olan parçalardan paket derlemek. Amaç: sektör başına iş yükü ≈ 0.
Bu bölümler **500 temada farklı farklı** kullanılacak. (Tema çalışması şimdi yapılmayacak.)

---

## 1. TEMA BÖLÜM KÜTÜPHANESİ

### 1.1 Mevcut (104 bölüm + 12 serbest yapı taşı)
Tanıtım 10 · Hareketli 10 · Hizmet 10 · E-ticaret 16 · Güven 10 · Görsel 9 · Ekip 4 ·
Dönüşüm 9 · İçerik 9 · Bilgi 9 · Sektörel 8

### 1.2 EKLENECEK — E-ticaret ürün sıralama bölümleri (öncelik)
Her biri "ürün seç" ile **sistemdeki ürünlerden** beslenir, adet seçilir, site mantıklı dizer:
- İndirimli ürünler · Fırsat ürünleri (günün fırsatı) · Çok satanlar · Yeni gelenler
- Öne çıkanlar · Son görüntülenenler · Birlikte alınanlar · Tükenmek üzere
- Koleksiyon / kategori vitrini · Marka vitrini · Kampanyalı ürünler · Sepete hızlı ekle vitrini
- Kaydırmalı ürün şeridi (hareketli/hareketsiz) · Izgara vitrin (2/3/4/6 sütun)
- Büyük görsel + ürün karması (Lumora tarzı: büyük kart + küçük kartlar)
Her bölümde ayar: **adet, sıralama kuralı, sütun sayısı, hareket (açık/kapalı), metinler, "tümünü gör" hedefi**

### 1.3 EKLENECEK — Rozet sistemi
Ürün ve bölüm kartlarına: **İndirim %, Yeni, Çok satan, Son X adet, Kargo bedava, Hediyeli, Tükendi**
- Rozet **ekle / çıkar / yeni rozet tanımla**
- **Hareketli / hareketsiz** seçeneği, renk, konum (sol üst / sağ üst / alt şerit)

### 1.4 EKLENECEK — Hazır yapı bölümleri
- **Mobil bar** (hareketli / hareketsiz, 3–5 buton, ikon+metin, hedef seçimi)
- **Footer** (çok sütunlu, bülten, sosyal, ödeme logoları, yasal linkler)
- **Menü görünümü** (klasik, mega menü, **mobil menüde resimli kategori** — nevermore.com.tr örneği)
- **Logo bölümü** (konum, boyut, scroll'da küçülme)
- **Story alanı** (Instagram tarzı; neyin ekleneceği ayarlanabilir: ürün, kampanya, video, fotoğraf)
- **Ana sayfa slider** — hareketli görsel üzerine yazı (sadece bu tip)
- **Site içi arama ve filtre** (metinleri değiştirilebilir)
- **Sosyal medya bölümü**
- **Dil seçici** (kapatılabilir)
- **Çerez politikası bandı** (açınca siteye girenlere otomatik görünür)
- **QR menü** (lokanta; temaya eklenir/çıkarılır, pasife alınabilir)

### 1.5 Her bölüm için zorunlu ayarlar
- **Mobil ve web için ayrı tasarım alanı** (ayrı düzen, ayrı boyut, ayrı görünürlük)
- Metin · renk · yazı tipi · stil
- Hareket (animasyon) açık/kapalı
- Tıklama hedefi (sayfa, kategori, ürün, dış link, telefon, WhatsApp)

---

## 2. E-TİCARET MODÜLÜ

### 2.1 Otomatik açılma
E-ticaret sektörü/paketi aktif edilince **ürün ekleme bölümü e-ticaret moduna döner**;
stok kontrolü, pazaryeri, kargo, sanal POS, e-fatura, kampanya ve raporlar birlikte açılır.
Sahip panelden kapatınca müşteri panelinde **hiç görünmez**.

### 2.2 Ürün ekleme — en kolay akış
- Temel: başlık, kategori, marka, fiyat, indirimli fiyat, stok, KDV, barkod/stok kodu, görseller
- Gelişmiş: varyant (renk/beden/ölçü), ek görsel, açıklama, teknik özellikler, SEO alanları,
  desi/ağırlık/boyut, kargo kuralı, GTIN, menşei, garanti, min–maks alım limiti
- **Alış fiyatı + kârlılık hesabı** (kanal bazlı komisyon ve KDV düşülerek) → raporlara akar
- **Hızlı ürün ekleme:** link yapıştır → görsel, başlık, açıklama otomatik gelsin; kullanıcı yalnız
  fiyat ve stok girsin
- Toplu işlemler: Excel/XML ile yükleme, toplu fiyat/stok güncelleme, toplu pazaryeri işlemi

### 2.3 Ürünler ekranı
En önemli alanlar görünür (görsel, ad, stok kodu, stok, fiyat, kâr, kanal durumu),
**arama + filtre** (kategori, marka, stok durumu, kanal, kampanya, kârlılık), sıralama, toplu seçim.

### 2.4 Pazaryerleri (TR'nin tamamı)
Trendyol · Hepsiburada · N11 · Çiçeksepeti · Amazon TR · PttAVM · Pazarama · İdefix · Modanisa ·
LC Waikiki · Farmazon · Temu
- **Kategori eşleştirme**, **marka çekme/eşleştirme**, zorunlu özellik eşleştirme
- Ürün gönderme (toplu), fiyat/stok kuralı (komisyon + KDV + kâr marjı → kanal fiyatı)
- **Sipariş gelince diğer kanallarda stok düşümü** (hata payı sıfıra yakın olmalı — kritik)
- Buybox takibi ve otomatik fiyatlandırma
- Pazaryeri iade görüntüleme, pazaryeri e-Fatura/e-Arşiv gönderimi
- Akakçe / Cimri XML

### 2.5 Sipariş ve iade
Sipariş listesi ve durumları, kargo fişi/etiket, sipariş fişi, **gelişmiş iade/değişim yönetimi**,
aktif sepetleri görüntüleme, sepet hatırlatma, telefonla sipariş, sipariş risk kriterleri.

### 2.6 Kampanyalar (kritik — doğru çalışacak)
X al Y öde · X alana Y ürün Z indirimli · sepet toplamına indirim · ödeme tipine göre indirim ·
müşteri grubuna göre indirim · cihaza göre indirim · ilk siparişe özel · yeni üyeye özel ·
kupon · hediye çeki · tek sepette birden fazla kampanya · indirim sayacı · çarkıfelek

### 2.7 Üyelik ve müşteri adımları
E-ticaret, lokanta siparişi gibi **kullanıcı adımı gereken sektörlerde** site üyeliği:
kayıt/giriş, hesabım, siparişlerim, favoriler, adres defteri, iade talebi, puan/cüzdan.

---

## 3. ENTEGRASYONLAR (müşteri kendi kurar, sahip izin verir)

| Grup | Sağlayıcılar |
|---|---|
| **Sanal POS / banka** | iyzico, PayTR, Param, Paratika, Paynet, Moka, Lidio, Netahsilat, Stripe, Akbank, Garanti, İş, YapıKredi, Ziraat, VakıfBank, Halkbank, DenizBank, QNB Finansbank, TEB, Şekerbank, Kuveyt Türk, Albaraka, Türkiye Finans, Anadolubank · kapıda ödeme, havale/EFT, cari ödeme |
| **Kargo** | Yurtiçi, Aras, MNG, PTT, Sürat, Sendeo, hepsiJET, UPS, DHL, Geliver, Kargoist, Kargola, PTS, HTS, Pozitif, Basit Kargo |
| **e-Fatura / e-Arşiv** | Paraşüt, BirFatura, Bizim Hesap, Logo İşbaşı, GİB e-Arşiv, Uyumsoft |
| **ERP / muhasebe** | **Nebim**, Logo (Go/Tiger 3), Mikro, Netsis, Dia, Hitit, WebTicari, Evobulut, JBI, KolayBi, Flap ERP, ASB, Akınsoft, Sentez, Eta, Zirve, Luca, Canias |
| **SMS / mesaj** | NetGSM, İleti Merkezi, Kobikom, WhatsApp Business, SMTP e-posta |
| **Google** | İşletme Profili, Takvim, Analytics GA4, Search Console, Ads, Merchant |
| **Sosyal / reklam** | Meta Pixel, Facebook Catalog/Login, TikTok Pixel, Instagram, Google Login |
| **Diğer** | Canlı destek (Jivochat), webhook/API, Zoom/Meet |

**Sektöre göre otomatik açılma:** sektör seçilince o sektörün entegrasyonları kendiliğinden listelenir.
Sahip ekler/çıkarır. Müşteri panelinde **teknik terimsiz, adım adım sihirbaz** ile bağlanır.

---

## 4. BİLDİRİM, SMS VE DUYURU
- Yeni rezervasyon / sipariş / randevu / form geldiğinde **panel + telefon bildirimi**
- Bildirim metinleri **sektörel** (lokantada "yeni sipariş", kuaförde "yeni randevu")
- SMS'i açan müşteri: **hangi adımda, hangi metinle** gideceğini kendisi ayarlar
- Siteye girenlere **duyuru** gönderebilme (bant / açılır pencere)

---

## 5. SEKTÖREL İŞ AKIŞLARI (giriş + sonuçlandırma + PDF)
Her sektör kendi adımları, alanları ve çıktısıyla. Motor aynı, veri farklı.
Araştırma notları §11'de.

---

## 6. SEKTÖRE ÖZEL RAPORLAMA
Muhasebe · randevu · müşteri takibi · personel takibi · kasa · pazarlama · evrak takibi ·
e-ticaret (satış, kâr, kanal, iade, stok devir, sepet terki, kampanya etkisi) · galeri.
Sektör seçimi rapor setini belirler.

---

## 7. DESTEK TALEBİ
Müşteri panelinde talep açma, **ekran görüntüsü ekleme** (sürükle-bırak ve Ctrl+V), durum takibi.
Talepler sahibin yönetim paneline düşer.

---

## 8. PAKET YÖNETİMİ (sahip paneli)
Modül / ekran / rapor / entegrasyon / bölüm **aç–kapa, pakete ekle, müşteriye özel aç**.
Kapatılan şey müşteri panelinde görünmez. İzin verilen sektörler müşteriye kilitli/açık gösterilir.

---

## 9. SAHİP YÖNETİM PANELİ (onlinekaydet.com/yonetim)
Baştan düzenlenecek, kusursuz çalışacak; **onlinekaydet.com sitesi de buradan düzenlenecek.**

---

## 10. TASARIM KURALLARI
- Müşteri panelinde **yapay zekâ görünümlü renk ve font yok** (mor/indigo gradyan yok)
- OnlineKaydet/ServisPlus renkleri ve ikonları, gerçek fotoğraf, şablon görünümü yok
- Her bölüm mobil ve web ayrı ayrı düzenlenebilir

---

## 11. SEKTÖREL ARAŞTIRMA NOTLARI (internet taraması)

### Kombi / HVAC teknik servis — servis formu
Müşteri ve iş yeri · servis adresi · **marka, model, seri no, kurulum yeri** · sistem tipi
(kombi, kazan, split, VRF) · cihaz durumu · servis tarihi, **varış–ayrılış saati** · hizmet türü
(bakım/onarım/kurulum/arıza tespiti/acil) · **ekrandaki arıza kodu** · yapılan işlem · ölçümler
(bar, baca gazı) · değişen parça (stoktan düşer) · işçilik+parça ücreti · **1 yıl parça / 1 yıl işçilik
garantisi** · önce–sonra fotoğraf · **müşteri imzası** · PDF servis fişi · **bakım hatırlatması**.

### Avukat / hukuk bürosu
Dosya yönetimi (alan, karşı taraf, vekil) · **safahat (zaman çizelgesi)** · müvekkil ·
**duruşma/keşif takvimi + 90/60/30/14/7 gün uyarısı** · tebligat · süre hesaplama · vekâletname ·
evrak arşivi · harç/masraf · **tahsilat ve taksit** · kronometre, saatlik ücret, faturalandırılabilir süre ·
serbest meslek makbuzu · UYAP Avukat Portal'dan dosya/evrak çekme ve **fark takibi** · raporlar.

### Sürücü kursu (MTSK)
**Özel MTSK Modülü / MEBBİS uyumu** · kursiyer kaydı, **eksik evrak takibi** · ehliyet sınıfı ·
teorik ders ve **günlük yoklama** · **direksiyon ders programı** (usta öğretici + araç ataması) ·
direksiyon takip formu · **e-Sınav randevusu ve sonucu** (50 soru) · direksiyon sınavı ·
sertifika (e-Devlet) · araç ve güzergâh · toplu SMS · muhasebe ve personel.

### Veteriner kliniği
Hasta sahibi + **evcil hayvan profili** (tür, ırk, yaş, çip) · **anamnez → muayene → teşhis →
tedavi → reçete** · **aşı takvimi ve otomatik hatırlatma** · laboratuvar · ilaç stoğu
(**FEFO, SKT, minimum seviye**) · pansiyon · cari/taksit/kasa · WhatsApp · raporlar.

### Lokanta / kafe
**QR menü** (masa bazlı), menü ve fiyat kartı, rezervasyon, paket sipariş, adisyon,
kurye takibi, mutfak ekranı, kampanya/menü saatleri.

---

## 12. REFERANS: QUKASOFT ÖZELLİK LİSTESİ (mobil uygulama hariç — karşılanacak)
Ticket destek · B2C · **B2B toptan satış** · e-ihracat (çok dil, çok para birimi) · sınırsız ürün/kategori ·
kargo fişi ve sipariş fişi yazdırma · e-Fatura/e-Arşiv · blog · gelişmiş SEO · **gelişmiş raporlama** ·
canlı destek · SMS/e-posta/WhatsApp bildirim modülleri · WhatsApp sipariş · Facebook/Google ile giriş ·
Excel ve XML ile ürün yükleme, XML dışa aktarma · Google Merchant · Facebook Catalog · story modülü ·
Google Ads, Meta/TikTok Pixel, GA4, rich snippets, Facebook dönüşüm API · ürün kişiselleştirme ·
bölge bazlı teslimat · **fotoğraflı ürün yorumları** · toplu SMS/e-posta · yorum hatırlatma ·
**stoğa gelince haber ver** · ürün karşılaştırma · **fiyat düştü bildirimi** · toplu ürün/pazaryeri işlemleri ·
gelişmiş iade · aktif sepetler · telefonla sipariş · sipariş risk kriterleri · ürün sıralama · arama eşleştirme ·
breadcrumb · 404 yönetimi · 301 yönlendirme · link yönetimi · **gelişmiş blok yönetimi** · **tema editörü** ·
min/maks alım limiti · bakiye (cüzdan) modülü · teklif yönetimi · ürün toplama sihirbazı ·
dijital PIN kodu · **linkten ürün yükleme** · ödeme sayfasında SMS ve TC doğrulama · çarkıfelek ·
indirim kulakçığı · kampanya çanı · açılır ürün listesi · popup ürün vitrini · indirim sayacı ·
sosyal hit · ürün koleksiyonları · affiliate marketing · B2B.

---

## 13. TASARIM REFERANSLARI (sahibin gönderdiği)
- **Lumora** (ev dekorasyon e-ticaret): kategori ızgarası, "Great Deals", "Latest Line-up",
  büyük kart + küçük kart karması, sıcak nötr palet → **ürün vitrini bölümlerinin düzeni**
- **nevermore.com.tr**: mobil menüde resimli kategori, ana sayfa ürün yerleşimi
- Premium landing örnekleri (Ondera, Biomos, Metora, Aurora): büyük tipografi, tam genişlik görsel,
  kayan şerit, scroll animasyonu → **hareketli bölümler**
- Nooka panel şablonu: panel görsel seviyesi

---

## 14. YAPILACAKLAR SIRASI
1. **Bölüm motoru** — bölüm/rozet/ayar veri modeli, mobil+web ayrı tasarım alanı
2. **E-ticaret ürün vitrini bölümleri + rozetler + hazır yapı bölümleri** (mobil bar, footer, menü, logo, story, slider, arama, sosyal, çerez, QR menü, dil)
3. **E-ticaret modülü** — ürün ekleme (hızlı + gelişmiş), ürünler ekranı, stok, kâr
4. **Pazaryeri entegrasyonu** — kategori/marka eşleştirme, gönderim, stok senkronu
5. **Sipariş / iade / kampanya**
6. **Entegrasyon merkezi** — POS, kargo, e-fatura, ERP, SMS
7. **Bildirim + SMS + duyuru + üyelik**
8. **Sektörel iş akışları ve PDF** (kombi, avukat, veteriner, MTSK, lokanta)
9. **Sektörel raporlama**
10. **Destek talebi**
11. **Sahip paneli** — paket yönetimi + onlinekaydet.com düzenleme
