# Müşteri paneli: kullanışlılık planı

Hedef: panel, işletme sahibinin telefonda ve masaüstünde az dokunuşla iş bitirebildiği, sade bir araç olsun. Bu plan Opus ile çizildi, uygulama Sonnet ile yapılacak. Madde sırası = uygulama sırası.

## Bugünkü durumdan gözlemler
- Menüde 50'den fazla sayfa var; mobilde "Diğer" altında uzun bir liste olarak açılıyor.
- Aynı iş birden çok yerde (Pazaryeri, Pazaryeri ürünleri, XML aktarım, Fiyat ve güvenlik, Depo ve sayım hep Satış altında).
- Açılışta ("Bugün") yeni bir hesap boş sayılarla karşılanıyor, ne yapılacağı söylenmiyor.
- Entegrasyonlar 58 kayıtlık düz liste idi (bu turda gruplandı).
- Sektöre özgü olmayan terimler vardı (bu turda düzeltildi).

## 1. Başlangıç rehberi (en yüksek etki)
- "Bugün" sayfasının üstüne sektör ve pakete göre 4-6 adımlık kurulum listesi: firma bilgisi, ilk ürün/hizmet, ödeme, site, ilk sipariş/randevu.
- Her adım tek düğme, tamamlananlar işaretli, hepsi bitince kendiliğinden gizlenir.
- Veri kaynağı: mevcut yp_pack ve firma verisi; yeni tablo gerekmez.

## 2. Sadeleşen menü
- Sol menü en çok 8 grup, her grubun içinde en çok 7 görünür sayfa (bugünkü LM=7 kuralı korunur).
- Seyrek kullanılan sayfalar ("Etiket tasarımı", "XML aktarım", "E-ihracat", "Ortaklar", "Bayiler") "Gelişmiş" başlığı altına taşınır; ana akışlar önde kalır.
- Menüde arama (Ctrl+K / mobilde arama simgesi): sayfa ve işlem adıyla doğrudan git.

## 3. Mobil önce
- Alt çubuk 5 hedef kalsın; "Diğer" tam ekran, aranabilir ve gruplu olsun (şimdiki 2 sütun kutucuk yapısı korunur, yazılar tam oturur: bu turda düzeltildi).
- Tablolar mobilde kart listesine dönüşsün (ürün, sipariş, müşteri, kasa).
- Sık işlemler için sabit "+" düğmesi: yeni sipariş/randevu/ürün/müşteri.

## 4. Tek tıkla işlemler
- Sipariş ve randevu kartında durum değiştirme, ödeme alma, SMS/WhatsApp gönderme doğrudan listeden.
- Toplu işlem çubuğu (seç, durum değiştir, etiketle, dışa aktar) ürün, sipariş ve müşteri listelerinde aynı davranışla.
- Geri al: silme ve durum değişiminde 8 saniyelik "Geri al" bildirimi.

## 5. Net boş ve hata durumları
- Her liste boşken ne yapılacağını söyleyen tek düğmeli boş ekran.
- Hata mesajları sebep + çözüm biçiminde (entegrasyonlarda zaten var; ürün içe aktarma, e-posta ve pazaryeri senkronunda ortak hale getir).

## 6. Tutarlılık
- Aynı iş için tek yer: Pazaryeri ürünleri ve XML aktarım "Ürünler" sayfasında sekme olsun; Fiyat ve güvenlik "Pazaryerleri" altına girsin.
- Tüm sayfalarda aynı başlık düzeni: başlık, tek cümle açıklama, birincil düğme sağda.
- Sektör terimleri `B.terms` ve `svKisi()` üzerinden; sabit "Usta", "Arıza" gibi metin kalmasın (denetim betiği: tests/denetim_panel_sektor.py).

## 7. Doğrulama
- Her madde sonrası: 78 sektör denetimi, 390 px ve 1280 px ekran görüntüsü, test_yp_eticaret_ui, test_marka_mail_ui, test_ana_panel_ui, test_menu_*.
- Başarı ölçüsü: yeni hesapta ilk ürün/hizmet ve ilk sipariş/randevu 5 dakika içinde, rehbersiz.
