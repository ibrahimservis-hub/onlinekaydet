# OnlineKaydet panel araştırması (10 Kasım 2026)

Amaç: panelin tüm sektörlere hitap eden, güncel teknolojide ve entegrasyonları eksiksiz bir yapıya gelmesi için rakip ve pazar taraması.
Kaynaklar: ikas, IdeaSoft, Ticimax, T-Soft karşılaştırma yazıları; BirFatura, Zunapro, Kobitime entegrasyon rehberleri; RandevuNet, Piyzi, Salon Randevu; Fieldcode, Housecall Pro, Simpro (saha servisi). Kodda "var/yok" sütunu yalnızca dosya adı taramasıdır, her satır tek tek doğrulanmadı.

## 1. Rakiplerin ortak çekirdeği
| Alan | Pazarda standart | Bizde (kod taraması) |
|---|---|---|
| Tek panel, sade yönetim | ikas'ın ana satış argümanı | panel var, sadeleştirme bekliyor |
| Pazaryeri entegrasyonu | Trendyol, Hepsiburada, n11, Çiçeksepeti, Amazon TR, Pazarama, PttAVM, Temu; çift yönlü stok/fiyat/sipariş | Trendyol, Hepsiburada, n11 kodlarda var; diğerleri yok |
| e-Fatura / e-Arşiv / e-İrsaliye | Sipariş anında otomatik fatura, entegratör (BirFatura, Logo, Mikro, Uyumsoft, Foriba, Paraşüt) | e-fatura izleri var; entegratör bağlantısı belirsiz; Paraşüt yok |
| Ödeme | iyzico, PayTR, Param, Papara | iyzico var; PayTR yalnızca sahip ekranında |
| Kargo | Yurtiçi, Aras, MNG, PTT, Sürat, HepsiJet, Trendyol Express, DHL, UPS; etiket tek tıkla, takip no pazaryerine | finance_plus içinde kargo izi var; canlı API bağlantısı doğrulanmalı |
| Muhasebe | Paraşüt, Logo, Mikro, Luca | yok |
| Yapay zeka | Panel destek asistanı, ürün içerik üretimi, yönetim için MCP sunucusu (IdeaSoft) | ai.py var; MCP yok |
| Mobil yönetim uygulaması | IdeaSoft, Ticimax | ServisPlus Usta uygulaması ayrı; yönetim uygulaması yok |
| Çoklu mağaza stok | tek ekranda | pazar yeri merkezi var |

## 2. Randevu / hizmet sektörleri (kuaför, klinik, kurs, spor)
Pazarın standardı: online randevu sayfası (kendi alan adıyla), SMS + WhatsApp hatırlatma (no-show %80'e kadar azalıyor iddiası, kaynak: Piyzi), personel takvimi ve izin, paket/seans takibi, adisyon ve günlük kasa, müşteri 360, doğum günü mesajı, Google yorum isteği otomasyonu, borç takibi, prim hesabı, sesli arama hatırlatması.
Bizde: randevu, bildirim, müşteri 360, paket/seans (fieldops, growth) var. Eksik veya doğrulanacak: Google yorum otomasyonu, prim, adisyon/günlük kasa ekranı, WhatsApp Business API (resmi), çevrimiçi ön ödeme/kapora, tekrar eden randevu.

## 3. Saha servisi (bizim çıkış noktamız)
2026 beklentisi (Fieldcode, Simpro): otomatik planlama ve atama, rota optimizasyonu, SLA'ya duyarlı planlama, teknisyen mobil uygulaması ve yönlendirmeli iş akışı, müşteri portalı ile self servis randevu, yapay zeka ile talep ön değerlendirme, sesli yapay zeka karşılama.
Bizde: teknisyen uygulaması ve servis akışı var; rota optimizasyonu, SLA ve yapay zeka ön değerlendirme doğrulanmalı.

## 4. Sektöre özel modüller (hitap alanını genişletir)
- Emlak: ilan modülü, harita, portföy paylaşımı (Sahibinden/Hepsiemlak XML dışa aktarma).
- Araç kiralama, transfer, tur: rezervasyon takvimi ve uygunluk, depozito.
- Restoran/pastane: menü, masa rezervasyonu, paket servis, QR menü.
- Eğitim kurumları, sürücü kursu: öğrenci kaydı, ders programı, taksit/ödeme takvimi, devamsızlık SMS.
- Sağlık (klinik, diş, veteriner): hasta dosyası, reçete, aşı/randevu hatırlatma, KVKK onamları.

## 5. Önerilen sıra
1. **Güven ve yasal temel:** e-Fatura/e-Arşiv entegratör bağlantısı (BirFatura ve Paraşüt), KVKK onam akışları, kargo API'leri (Yurtiçi, Aras, MNG, PTT).
2. **Satış kanalları:** Çiçeksepeti, Amazon TR, Pazarama, PttAVM; çift yönlü stok.
3. **İletişim:** WhatsApp Business resmi API, Google yorum otomasyonu, kapora/ön ödeme (iyzico, PayTR).
4. **Zeka:** panel destek asistanı, ürün içerik üretimi, yönetim için MCP, randevu ve talep için yapay zeka karşılama.
5. **Sektör paketleri:** ilan (emlak), rezervasyon (kiralama, restoran), öğrenci/taksit (kurs), hasta dosyası (klinik).
6. **Mobil yönetim uygulaması** (sahip için sipariş, randevu ve ciro özeti).

## 6. Açık sorular (karar sizde)
- Hangi entegratörle başlayalım (BirFatura, Paraşüt veya Logo)? Her biri için ayrı sözleşme ve API anahtarı gerekir.
- WhatsApp Business API resmi sağlayıcı ücretlidir; paket fiyatına dahil edilecek mi?
- Hangi sektör paketini önce satışa çıkaralım?

Not: Rakiplerin kendi pazarlama sayfalarındaki oranlar (örneğin no-show düşüşü) doğrulanmış sonuç değildir.
