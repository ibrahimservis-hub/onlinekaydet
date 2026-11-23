# E-ticaret kurulum listesi — eksikler ve iş akışı

Kaynak: kullanıcının gönderdiği 7 başlıklık kurulum listesi (Tema kurulumu, Ürün tanımlamaları, Temel ayarlar, Statik sayfalar, SEO, Meta Business, Google araçları). Kod tarandı (panel/*.py, storefront.py, shop.py, sp_ext.py, entegrasyon.py, notify.py) — 23.11.2026.

## Zaten var (dokunma)
Kategori ağacı, ürün girişi, varyant, marka tanımı, ilişkili ürünler, ödeme (havale/kapıda/kart, iyzico), kargo ayarları + 18 kargo entegrasyonu, sipariş ve üyelik (müşteri paneli), min. sipariş, slider/banner, ana sayfa/ürün/kategori sayfası, blog, SSS, sözleşmeler (shop_legal), hakkımızda/iletişim, kategori+ürün+ana sayfa SEO, sitemap, Merchant XML akışı, GA4/Ads/Pixel/GSC kimlik alanları, Google Ads offline dönüşüm yükleme (mkt.py).

## Eksikler

### 1. Ölçüm altyapısı (öncelik 1)
- `/public/site-modules` etiket döndürüyor ama firma sitesine GA4 / Ads / Pixel kodunu basan istemci kodu bulunamadı → önce bunu doğrula, yoksa yaz.
- Google Tag Manager kimliği (GTM-XXXX) alanı ve sitede yüklenmesi yok.
- dataLayer e-ticaret olayları yok: `view_item`, `view_item_list`, `add_to_cart`, `begin_checkout`, `add_payment_info`, `purchase` (storefront.py).
Akış: Panel > Bağlantı > Ölçüm'e GTM alanı → site-modules çıktısına `gtm` → firma sitesi `<head>`'ine GA4/GTM/Pixel/Ads betiği (çerez onayına bağlı) → storefront.py olay noktalarında `dataLayer.push` + `fbq('track')` + `gtag('event')` → sipariş tamamlanınca `purchase` (order_no ile tekilleştir) → test: GA4 DebugView / Tag Assistant.

### 2. Meta Business (öncelik 2)
- Dönüşümler API (CAPI) sunucu tarafı yok (token alanı var, graph.facebook.com çağrısı yok).
- Facebook/Instagram katalog ürün akışı yok (entegrasyon kaydı var, feed endpoint yok).
Akış: `/public/feeds/meta.xml` (Merchant akışından türet, `fb_product_category`, `availability`) → sipariş oluşunca arka planda CAPI `Purchase` (event_id = order_no, telefon/e-posta SHA-256) → tarayıcı Pixel ile aynı event_id (tekilleştirme) → panelde "Test olay kodu" alanı → Events Manager'da doğrula.

### 3. Ürün kurguları (öncelik 3)
- Özellik filtreleri: mağazada yalnız kategori/marka/fiyat/stok filtresi var. Ürün özelliklerinden (specs) filtre tanımı yok.
- Kişiselleştirme: ürüne müşterinin yazdığı not/isim/seçenek (ek ücretli) alanı yok.
- Tamamlayıcı ürünler: "ilişkili" var, sepette "bununla alınır" önerisi yok.
Akış: Panel > Ürünler > Filtreler (hangi özellik filtre olur, kategori bazlı) → pub_search'e `attr` süzgeci + yüzey sayımı → ürün editörüne "Kişiselleştirme" bölümü (alan türü, zorunlu, ek ücret, karakter sınırı) → sepet/sipariş satırına `custom` alanı, siparişte görünür → ürün editöründe "Tamamlayıcı ürünler" listesi → sepet çekmecesinde öneri.

### 4. Marka ve SEO (öncelik 4)
- Herkese açık marka sayfası yok (`/magaza/marka/{slug}`), marka SEO alanları yok.
- SEO şablonları yok: `{urun} | {kategori} | {firma}` gibi kurallarla boş title/description doldurma (mevcut toplu SEO yol bazlı).
Akış: brand koleksiyonuna slug/açıklama/görsel/SEO → marka sayfası (ürün ızgarası + filtre) → sitemap'e marka URL'leri → Panel > SEO > Şablonlar (ürün, kategori, marka, statik sayfa) → boş alanlarda şablon, dolu alana dokunma.

### 5. Müşteri e-postaları (öncelik 5)
- Siparişte yalnız işletmeye bildirim var; müşteriye sipariş onayı, kargoya verildi, teslim, iade e-postası ve şablon düzenleyici yok.
Akış: SMTP (var) → şablonlar (değişkenler: {ad}, {siparis_no}, {tutar}, {kargo_takip}) → olaylar: sipariş oluştu / ödendi / kargoda / teslim / iade → panelde önizleme ve test gönderimi → gönderim kaydı.

### Kısmen / doğrulanacak
- "Mağazalarımız" sayfası: şube verisi (profile.branches) var, ayrı sayfa olup olmadığı kontrol edilecek.
- Google İşletme Profili: yalnız yorum çekme var; profil yönetimi kapsam dışı.
- Performans ayarları (görsel sıkıştırma, önbellek) panelden ayarlanamıyor; kod tarafında var.
