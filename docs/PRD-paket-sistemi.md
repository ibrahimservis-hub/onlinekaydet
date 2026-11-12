# OnlineKaydet — Sektörel Paket Sistemi (PRD)

> Sahibinin 2026-11-12 tarihli talimatı. Bu belge yol haritasıdır, silinmez.
> Hedef: **Ticimax / İdeaSoft / ikas'tan daha iyi**, geliştirilebilir, son teknoloji bir sistem.

## 0. Temel mantık
Her şey **"bölüm ekle"** mantığıyla kurulur: bölüm, modül, ekran, rapor, entegrasyon ve iş akışı
birer **veri kaydıdır** (kod değil). Yeni sektör açmak = var olan parçalardan paket derlemek.
Amaç: farklı sektörlerde iş yükünü sıfıra yaklaştırmak.

## 1. Sektörel entegrasyonlar (otomatik)
- Sektör seçilince o sektörün entegrasyonları **kendiliğinden açılır**.
- Sahip (yönetim paneli) istediğini **ekler / çıkarır**.
- Açılan entegrasyon müşteri panelinde **en basit, anlaşılır** biçimde görünür (teknik terim yok,
  adım adım sihirbaz, "bağlandı / bağlanmadı" net durum).

## 2. E-ticaret paketi (tek tuşla açılır)
Paket açılınca otomatik gelir:
- Stok kontrolü ve stok senkronu
- TR pazaryerlerinin tamamı: Trendyol, Hepsiburada, N11, Çiçeksepeti, Amazon TR, PttAvm, Pazarama
- Kategori eşleştirme ekranı, ürün gönderme (toplu), fiyat/stok kuralları
- Sipariş geldiğinde **diğer pazaryerlerine otomatik stok düşümü**
- Sipariş ve **iade/değişim** ekranı
- Pazaryerlerine uygun **muhasebe ekranı** (komisyon, kesinti, hakediş, e-Fatura/e-Arşiv)
- Kargo entegrasyonları, etiket, takip
- Sanal POS / taksit / 3D Secure
- Temalar ve modüller
**Sahip, bu paketi kendi panelinden kapatabilir; kapatınca müşteri panelinde hiç görünmez.**

## 3. Destek talebi ekranı (müşteri panelinde)
- Müşteri talep açar, **ekran görüntüsü ekleyebilir**, durum takibi yapar.
- Talepler sahibin yönetim paneline düşer.

## 4. Sektöre özel raporlama
Seçilen sektöre göre rapor seti değişir: muhasebe, randevu, müşteri takibi, personel takibi,
kasa, pazarlama, evrak takibi, e-ticaret, galeri vb.
Sektörler: teknik servis, e-ticaret, kuaför/güzellik, sürücü kursu, eğitim, market, lokanta,
otel, avukat, emlak, oto servis, veteriner, sağlık, spor, organizasyon …

## 5. Sektörel iş akışları ve ekranlar (EN ÖNEMLİ)
Her sektörün **giriş adımları, sonuçlandırma adımları ve PDF çıktıları** farklıdır.
- **Kombi/teknik servis:** marka–model seçimi, arıza, servis formu, müşteri imzası, PDF servis fişi,
  bakım hatırlatması, yedek parça, garanti takibi.
- **Avukat:** dosya/evrak takibi, duruşma takvimi, süreç metinleri, vekâlet, masraf, tahsilat.
- Diğer sektörler kendi akışıyla.
> Önce **internet ortamında sektör bazında derinlemesine araştırma** yapılacak, sonra tasarlanacak.
Sahip isterse ek bölüm/adım ekleyebilir.

## 6. Paket paket satış
Sahibin panelinde modül/ekran/rapor/entegrasyon **ekleme–çıkarma çok kolay** olacak
(aç/kapa, pakete ekle, müşteriye özel aç).

## 7. Bölüm kütüphanesi
- 104 hazır bölüm + 12 serbest yapı taşı (bugünkü durum), sürekli genişletilecek.
- **En son çıkan temalar** internetten taranıp bölümler güncellenecek.
- Bu bölümler **500 temada farklı farklı** kullanılacak. (Tema çalışması şimdi yapılmayacak.)

## 8. Sahip yönetim paneli (onlinekaydet.com/yonetim)
- Baştan düzenlenecek, kusursuz çalışacak.
- **onlinekaydet.com sitesi de buradan düzenlenebilecek.**
- Gereken yeni özellikler eklenebilir.

## 9. Tasarım kuralı
- Müşteri panelinde **yapay zekâ görünümlü renk ve fontlar kullanılmayacak**.
- OnlineKaydet/ServisPlus renkleri ve ikonları; gerçek fotoğraf; şablon görünümü yok.

## 10. Kalite çıtası
Ticimax, İdeaSoft, ikas ve benzeri firmalardan **daha iyi** olacak. Her adım gerçekten çalışacak.

---

## 11. Sektörel araştırma notları (2026-11-12, internet taraması)

### Kombi / HVAC teknik servis — servis formu alanları
Müşteri ve iş yeri bilgileri · servis adresi · **marka, model, seri no, kurulum yeri** ·
sistem tipi (kombi, split, VRF, kazan…) · cihazın genel durumu · servis tarihi, **varış ve ayrılış saati** ·
hizmet türü (bakım / onarım / kurulum / arıza tespiti / acil) · arıza başlangıcı ·
**ekrandaki arıza kodu** · yapılan işlemler · ölçümler (basınç/bar, baca gazı) · değişen parça ·
işçilik + parça ücreti · **garanti (1 yıl parça / 1 yıl işçilik)** · önce–sonra fotoğraf ·
**müşteri imzası** · PDF servis fişi · **periyodik bakım hatırlatması**.
Not: parça uyumluluğu tam model kodundan doğrulanır; MYK/MEB ustalık belgesi müşteriye gösterilir.

### Avukat / hukuk bürosu
Dosya yönetimi (hukuk alanına göre kategori, karşı taraf, vekil) · **dosya bazlı zaman çizelgesi (safahat)** ·
müvekkil takibi (bireysel/kurumsal) · **duruşma ve keşif takvimi + artan uyarılar (90/60/30/14/7 gün)** ·
tebligat durumu · **süre hesaplama** · vekâletname takibi · evrak yönetimi ve arşiv ·
harç/masraf girişi · **tahsilat ve taksit planı** · kronometreyle çalışma süresi, saatlik ücret,
faturalandırılabilir süre · serbest meslek makbuzu · UYAP Avukat Portal'dan dosya/evrak/safahat
çekme ve **fark takibi** · raporlar (dosya, müvekkil, finans).

### Sürücü kursu (MTSK)
**Özel MTSK Modülü / MEBBİS uyumu** · kursiyer kaydı ve **eksik evrak takibi** (belgeler taranıp
il/ilçe MEM onayına gider) · ehliyet sınıfı · teorik ders ve **günlük yoklama** (grup bazlı) ·
**direksiyon ders programı** (usta öğretici ve araç ataması, dönem, hafta içi/sonu grubu) ·
direksiyon takip formu · **e-Sınav randevusu ve sonucu** (50 soru: trafik 23, ilk yardım 12,
araç tekniği 9, trafik adabı 6) · direksiyon sınavı · sertifika (e-Devlet) · fatura modüle işlenir ·
araç ve güzergâh kayıtları · toplu SMS · muhasebe ve personel.

### Veteriner kliniği
Hasta sahibi + **evcil hayvan profili** (tür, ırk, yaş, cinsiyet, fotoğraf, çip no) ·
**anamnez → muayene → teşhis → tedavi → reçete** akışı · **aşı takvimi ve otomatik hatırlatma** ·
laboratuvar tahlil ve ödeme takibi · ilaç stoğu (**FEFO, son kullanma, minimum seviye uyarısı**) ·
pansiyon/bakım ayrı hizmet tipi · cari hesap, taksit, kasa · tek tıkla WhatsApp · tür/yaş/cinsiyet raporları.
