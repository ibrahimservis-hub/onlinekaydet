# OnlineKaydet ana sayfa v8 — tasarım şeması

Durum: **onay bekliyor**. Kod yazılmadı, site ve panel dosyalarına dokunulmadı.
Onay görselleri: `/tmp/v8/masaustu.png` (1440 px, tam sayfa), `/tmp/v8/mobil.png` (390 px, tam sayfa), `/tmp/v8/mobil-ilk-ekran.png` (sabit arama çubuğuyla ilk ekran). Mockup kaynağı: `/tmp/v8/mockup.html` (üretici: `/tmp/v8/build.py`).

## 1. Yön: "Mürekkep ve çam"

Açık zemin, mürekkep siyahı yazı, tek vurgu rengi olarak çam yeşili. Kart ızgarası yerine ince çizgili satırlar ve tablolar; her bölüm sola yaslı başlıkla açılır, içerik sütunu bölümden bölüme yer değiştirir. Kanıt olarak çizim değil panelin kendi ekran görüntüleri kullanılır.

Bilerek tekrarlanmayanlar:

| Önceki | Neydi | v8'de |
|---|---|---|
| yon7 / v7 | koyu grafit + şampanya, Instrument + Geist | açık zemin, yeşil, Bricolage + Plex |
| yon5 | krem + turuncu + lacivert, Red Hat | krem ve turuncu yok |
| yon6 | sarı, Antonio + Hanken | sarı yok |
| ilk site, panel | mavi (#2f6bdc, #1650b0) + turuncu | mavi yalnız panel ekran görüntülerinin içinde kalır |

"Yapay zekâ görünümü" denetimi: mor ya da mavi gradyan yok, gradyan hiç yok; ortalanmış bölüm yok; tekrarlayan üçlü kart ızgarası yok; blob, parıltı, cam efekti yok; emoji ya da süs ikonu yok (sayfada ikon kullanılmıyor); köşe yarıçapı 2 px; gölge yalnız hero'daki ekran görüntüsünde.

## 2. Renk token'ları

| Token | Değer | Kullanım |
|---|---|---|
| `--kagit` | `#FFFFFF` | ana zemin |
| `--zemin` | `#F2F4F0` | paketler bölümü ve alt bilgi zemini |
| `--murekkep` | `#0D1512` | başlık, metin, kalın çizgi, dolu düğme |
| `--metin2` | `#4B5651` | ikincil metin (beyaz üstünde yaklaşık 7:1) |
| `--cizgi` | `#D3D9D3` | ince ayırıcı |
| `--cam` | `#0A6847` | **tek vurgu**: ana düğme, H1 vurgusu, matris işareti, bağlantı alt çizgisi (beyaz üstünde yaklaşık 6,5:1) |
| `--cam-koyu` | `#0B2B21` | telefon bandı, saha uygulaması bölümü, öne çıkan paket (yüzey rengi, vurgu değil) |
| `--cam-acik` | `#E2EEE7` | matriste Tam Paket sütunu, Başlangıç etiketi |
| `--dolgu` | `#D6DBD6` | yalnız mockup'taki FOTO yer tutucuları |

Logo (mavi + turuncu bulut) olduğu gibi kullanılır; sayfada başka mavi ya da turuncu yoktur.

## 3. Yazı tipleri (Google Fonts, ücretsiz, Türkçe destekli)

| Rol | Yazı tipi | Ağırlık | Not |
|---|---|---|---|
| Başlık, telefon, fiyat | **Bricolage Grotesque** (değişken, 200–800) | 700, telefon 800 | harf aralığı −0,03 em, telefon −0,05 em, rakamlar `tabular-nums` |
| Metin | **IBM Plex Sans** (değişken, 100–700) | 400 / 500 / 600 | 17 px, satır 1,55 |
| Etiket, paket rozeti, not | **IBM Plex Mono** | 500 | 11–13 px |

İki dosya da depoda var (`themes/fonts/bricolage-*.woff2`, `plex-*.woff2`, `plexmono-*.woff2`), kendi sunucumuzdan verilir; Google'a istek gitmez. ğ, ş, ı, İ, ç, ö, ü mockup'ta denetlendi. Yedek öneri (sahip Bricolage'ı sevmezse): Archivo (genişlik eksenli) + Hanken Grotesk; ikisi de `site/fonts/` içinde.

Ölçek (masaüstü / mobil): telefon 148 / 51 · H1 86 / 46 · H2 56 / 38 · akış başlığı 44 / 34 · H3 28 · fiyat 54 / 46 · metin 17 / 16 · küçük 14 · etiket 12.

## 4. Izgara ve boşluk

- Kapsayıcı en çok 1280 px içerik, yan boşluk 48 px (mobil 20 px).
- 12 sütun, 24 px oluk. Başlık bloğu çoğunlukla 1–5 ya da 1–7. sütun; içerik 6–12 ya da 7–12. sütun. Paketler ve akış tam genişlik.
- Dikey ritim: bölümler arası 128 px (mobil 80), koyu ve gri bantların iç boşluğu 104 px (mobil 64).
- Çizgi dili: bölüm ve tablo üstü 1,5 px mürekkep, satır arası 1 px `--cizgi`.
- Düğme 52 px yükseklik, 2 px köşe. Mobilde dokunma hedefi en az 48 px.
- Kırılım: 700 px altı tek sütun. 700–1100 arası ara düzen kodlama aşamasında çıkarılacak (mockup'ta yok).

## 5. Bölüm akışı ve gerekçesi

| # | Bölüm | Yerleşim | Neden burada |
|---|---|---|---|
| 0 | Üst çubuk | logo · menü · "Üye girişi" (`/uye-girisi`, küçük ve gri) · telefon 24 px · "Ücretsiz deneyin" | Telefon çubukta da en iri öğe. `/yonetim` hiçbir yerde yok. |
| 1 | Hero | sol 7 sütun H1 + tek paragraf + 2 düğme; sağ 5 sütun dikey fotoğraf, üstüne taşan telefon ekran görüntüsü | Reklamdan gelen kişi ilk ekranda ürünün ne olduğunu ve kime olduğunu okur. |
| 2 | Telefon bandı | tam genişlik koyu yeşil, `0544 444 40 04` 148 px | Sayfanın en büyük öğesi. Tamamı `tel:` bağlantısı. |
| 3 | Sayılar | 6 rakam, ilki büyük ve yeşil | Koddan sayılmış gerçek rakamlar; iddianın hemen kanıtı. |
| 4 | Panel ekranları | büyük "Bugün" ekranı + üstüne binen telefon + altında Takvim ve Entegrasyonlar | "Çizim değil" kanıtı. Özellik listesinden önce gelir ki liste inandırıcı olsun. |
| 5 | İş akışı | 6 satır: Kaydet, Yürüt, Tahsil et, Hatırlat, Sat, Ölç; her özelliğin yanında açıldığı ilk paketin rozeti | Tüm özellikler menü sırasıyla değil işin sırasıyla; rozetler paket tablosuna hazırlar. |
| 6 | Paketler | aylık/yıllık anahtarı, 4 paket tek çerçevede (Tam Paket koyu), altında 20 satırlık matris | Ziyaretçi neyin ne olduğunu öğrendikten sonra fiyatı görür. |
| 7 | Sektör seçici | sol: başlık + arama + "aynı ekran, üç sektör" örneği; sağ: 16 sektör paketi, her birinin terimleriyle | Fiyat sonrası "bana uyar mı" sorusu. Sektör sayfalarına iç bağlantı merkezi. |
| 8 | Temalar | 1 büyük + 3 küçük gerçek tema ekranı, altında site editörü ekranı | Web sitesi Tam Paket'in satış gerekçesi. |
| 9 | Saha uygulaması | koyu bant: sol özellik listesi, sağ telefon + saha fotoğrafı | Teknik servis ve saha ekipleri için ayrı karar nedeni. |
| 10 | Entegrasyonlar | sol başlık + Siparişler ekranı; sağ 8 grup, adlar düz metin | "Mevcut hesaplarımla çalışır mı" itirazı. |
| 11 | Güven | 6 satır + şirket kimliği + (onay gelirse) müşteri yorumu | Satın almadan önceki son itirazlar. |
| 12 | SSS | 8 soru, ilki açık | FAQPage şeması bu metinden üretilir. |
| 13 | Son çağrı | telefon 176 px yeşil + 3 alanlı form | Sayfa telefonla başlar, telefonla biter. |
| 14 | Alt bilgi | 5 sütun; e-posta ve adres küçük | Diğer iletişim öğeleri yalnız burada. |
| — | Mobil sabit çubuk | altta koyu yeşil: numara + "Hemen arayın" | Mobilde numara her an ekranda. |

Mobil farklar: menü çekmeceye girer; matris dört dar sütun (Baş., Pro., Tam, Kur.) ve açıklamasız; akış listeleri tek sütun; paketler alt alta.

Hareket (kodlamada): yalnız ekran görüntülerinde kaydırınca 12 px yukarı belirme ve sekme değişiminde çapraz geçiş. `prefers-reduced-motion` açıkken kapalı. Sayaç animasyonu, paralaks, kayan logo şeridi yok.

### Sektöre özel açılış
Mevcut plan korunur: `/sektor-<ad>.html` ayrı URL (sitemap'te 78 sayfa var) ve ana sayfada `?s=<ad>`. `?s=` verilince değişenler: H1 ve paragraf, hero fotoğrafı, panel ekran görüntüleri (o sektörün deneme hesabından), sektör terimleri, akış satırlarındaki örnek sözcükler, tema vitrini, SSS'nin ilk iki sorusu. Paket matrisi ve telefon değişmez. `?s=` sayfasının canonical'ı ilgili `/sektor-<ad>.html` adresidir.

## 6. Özellik envanteri (koddan)

| Ölçü | Sayı | Kaynak |
|---|---|---|
| Paket | 4 (Başlangıç, Profesyonel, Tam Paket, Kurumsal) | `panel/firms.py` `DEFAULT_PACKAGES` |
| Paket modülü | 19 (`ALL_MODS`) + 1 ek (`eticaret`) = 20 tanımlı | `panel/firms.py` `MODULES` |
| "Yakında" modül | 0 (`SOON = {}`) | `panel/firms.py` |
| Müşteri paneli ekranı | 18 temel + 9 satış ekranı = 27; 11 üst menü grubu | `panel/yp_ui.html` `BASE_NAV`, `buildNav`, `NAVG` |
| Sahip paneli | 5 grup, 13 ekran (sitede gösterilmez) | `panel/sahip/src.html` `GR` |
| Sektör dili | 70 sektör, 16 sektör paketi | `panel/sektor_dil.py` `ROWS`, `panel/blocks.py` `SECTOR_PACKS` |
| Tema | 526 tema, 78 iş kolu (496'sı "premium" işaretli) | `site/themes.json` |
| Site bölümü | 126 bölüm, 13 kategori, 8 rozet | `panel/blocks.py` |
| Entegrasyon | 94 sağlayıcı, 8 grup: POS 14, kargo 17, e-fatura 10, ERP 18, SMS 8, pazaryeri 11, ölçüm 11, diğer 5 | `panel/entegrasyon.py` `CATALOG` |
| Pazaryeri | katalogda 11; ürün kanalı 10; API modülü 6; "doğrulandı" işaretli 3 (Trendyol, Hepsiburada, N11) | `entegrasyon.py`, `urun.py` `CHANNELS`, `markets_hub.py` |
| Hazır rapor | 17 rapor, 6 grup | `panel/yprapor.py` |
| Sektörel iş akışı | 5 (servis formu, dava dosyası, muayene, iş emri, kursiyer) | `panel/isakis.py` `FLOWS` |
| Kampanya türü | 7 | `panel/kampanya.py` `TYPES` |
| Sektör modülü | 4 (ilan, kurs, rezervasyon, klinik) | `panel/sektor_mod.py` |
| Bayi (B2B) | grup iskontosu, başvuru ve onay, bayiye özel fiyat, cari | `panel/b2b.py` |
| Ortaklık | referans linki, tıklama sayacı, sipariş komisyonu, ödeme kaydı | `panel/ortak.py` |

Müşteri paneli ekranları: Bugün, Takvim, Randevular, Müşteriler, Üyelik, Kasa, Ekip, Raporlar, Web Sitem, Diller, Duyuru, Yönlendirmeler, İş kayıtları, İçerikler, Bildirimler, Entegrasyonlar, Ayarlar, Destek. Satış açılınca: Ürünler, Siparişler, Kampanyalar, Fiyat ve güvenlik, Popup vitrin, Bayiler, Ortaklar, İadeler, Pazaryerleri.

## 7. Paket ve özellik matrisi

Kaynak `DEFAULT_PACKAGES`; her paket bir öncekinin tamamını içerir. Fiyatlar **yer tutucudur** (bugünkü sitedeki rakamlar), sahip panelden düzenler.

| Modül (anahtar) | Başlangıç | Profesyonel | Tam Paket | Kurumsal |
|---|:-:|:-:|:-:|:-:|
| Yer tutucu fiyat, ₺/ay + KDV | 990 | 1.990 | 3.490 | 5.990 |
| Yer tutucu yıllık (10 ay) | 9.900 | 19.900 | 34.900 | 59.900 |
| **Çekirdek** | | | | |
| İş / servis kayıtları (`servis`) | ● | ● | ● | ● |
| Ekip, usta, personel (`personel`) | ● | ● | ● | ● |
| **Yönetim** | | | | |
| Muhasebe ve kasa (`muhasebe`) | – | ● | ● | ● |
| Raporlar (`rapor`) | – | ● | ● | ● |
| SMS ve mesaj şablonları (`sms`) | – | ● | ● | ● |
| **Büyüme** | | | | |
| Web sitesi (`site`) | – | – | ● | ● |
| Online randevu (`randevu`) | – | – | ● | ● |
| Yedek parça mağazası (`magaza`) | – | – | ● | ● |
| Pazarlama (`pazarlama`) | – | – | ● | ● |
| **Kurumsal** | | | | |
| Bakım hatırlatma ve garanti (`bakim`) | – | – | – | ● |
| Teklif ve onay (`teklif`) | – | – | – | ● |
| Ödeme linki (`odeme`) | – | – | – | ● |
| E-arşiv fatura bağlantısı (`efatura`) | – | – | – | ● |
| Müşteri portalı (`portal`) | – | – | – | ● |
| Canlı saha takibi (`takip`) | – | – | – | ● |
| Otomatik atama (`atama`) | – | – | – | ● |
| QR cihaz etiketi (`qr`) | – | – | – | ● |
| Arayan numara tanıma (`arayan`) | – | – | – | ● |
| Bayi B2B (`bayi`) | – | – | – | ● |
| **Ek modül** | | | | |
| E-ticaret (`eticaret`) | Ek | Ek | Ek | Ek |
| Modül sayısı | 2 | 5 | 9 | 19 |

Dikkat edilecek üç nokta:
1. `eticaret` modülü `ALL_MODS` içinde değil; Kurumsal dahil hiçbir varsayılan pakette yok. Mockup'ta "Ek" olarak gösterildi.
2. `randevu` Tam Paket'te var ama bugünkü `fiyatlar.html` tablosunda satırı yok; v8'de eklendi.
3. Paket tanımları teknik servis diliyle yazılmış (servis, usta). Yeni paneldeki sektör paketleri (`SECTOR_PACKS`) ayrı bir modül kümesi kullanıyor (randevu, kasa, dosya, hasta, kursiyer...). Kuaför ya da avukat için "Başlangıç" tam olarak neyi açar, kodda tanımlı değil.

Her pakette olanlar (matris altı not): firmaya özel veritabanı, SSL, rol ve yetki, KVKK metni, sektör şablonu, destek talebi, paket yükseltme.

## 8. Fotoğraf ve görsel listesi

Depodaki görseller incelendi; **kullanılabilir gerçek fotoğraf bulunamadı**:
- `themes/img/` teknik sektör fotoğrafları (kombi, klima, beyaz eşya...) aynı kişiyi her karede gösteren, üretilmiş görünümlü kareler; kaynak kimliği yok.
- `themes/img/` kuaför, e-ticaret, nakliye, oto, temizlik, tekstil, güzellik dosyaları vektör çizim. `themes/fetch_photos.py` içindeki Pexels listesi hiç çalıştırılmamış görünüyor.
- `site/hero-gorsel.webp` ve `assets/giris-gorsel.webp` üretilmiş görsel.
- Bu ortamda Pexels ve Unsplash'e erişim kapalı (403), o yüzden fotoğraf indirilemedi.

Bu nedenle mockup'ta 4 yerde "FOTO" etiketli nötr dolgu var. Gerekenler:

| # | Yer | Ne olacak | Oran / boyut | Arama terimi (Pexels, Unsplash) |
|---|---|---|---|---|
| F1 | Hero | Gerçek bir iş yerinde tezgâh başında tabletten ya da telefondan kayıt alan işletme sahibi; gün ışığı, kameraya poz yok | dikey 4:5, 1040×1300 | "small business owner tablet counter", "workshop owner phone", "barber shop reception" |
| F2 | Saha uygulaması | Müşterinin evinde telefonu uzatıp imza alan usta ya da telefona bakan teknisyen | dikey 3:4, 840×1120 | "technician smartphone customer home", "repairman signing phone" |
| F3 | Saha uygulaması telefonu | Saha uygulamasının gerçek ekran görüntüsü (iş listesi) | 390×844 | fotoğraf değil; ekrandan alınır |
| F4 | Güven | Ankara ofisi ya da ekip | yatay 4:3, 620×460 | **sahip sağlar**; stok kullanılmaz, yoksa blok fotoğrafsız çıkar |
| F5 | `?s=` sayfaları | Her sektör paketi için 1 hero fotoğrafı (16 adet) | dikey 4:5 | `fetch_photos.py` içindeki Pexels kimlikleri aday (kuaför 13138585, oto servis 8985615, lokanta 4916299, diş 3845737...), gözle onaylanmalı |

Kural: Pexels ya da Unsplash lisanslı, kaynak adresi `docs/` altında listelenir; üretilmiş görsel ve vektör çizim kullanılmaz. Tüm fotoğraflar tek tonda, hafif soğuk renk düzeltmesiyle verilir.

Mockup'taki ekran görüntüleri gerçektir: panel testlerdeki düzenle yerelde açıldı, bir kuaför deneme hesabına 9 örnek randevu girildi (`/tmp/v8/panelshot.py`), temalar `themes/html/` dosyalarından çekildi (`/tmp/v8/temashot.py`). Yayında aynı yöntemle 1440 ve 390 genişlikte, WebP olarak yeniden alınır.

## 9. SEO ve Google planı

### Başlık ve açıklama şablonları
| Sayfa | `<title>` (60 karakter altı) | `meta description` (150 karakter civarı) |
|---|---|---|
| Ana sayfa | `OnlineKaydet: Randevu, Servis Takip ve İşletme Programı` | `Randevu, iş kaydı, kasa, web sitesi ve e-ticaret tek panelde. 70 sektöre özel iş takip programı. İlk ay ücretsiz. 0544 444 40 04` |
| Sektör | `{Sektör} Programı: Randevu, Kayıt, Kasa \| OnlineKaydet` | `{Sektör} için {iş terimi} takibi, {kişi terimi} yönetimi, kasa ve hazır web sitesi. İlk ay ücretsiz.` |
| Paketler | `Paketler ve Fiyatlar \| OnlineKaydet` | `Dört paket, 19 modül. Hangi özellik hangi pakette, satır satır.` |
| Tema | `{Sektör} Web Sitesi Temaları \| OnlineKaydet` | `{n} hazır {sektör} teması. Metni, görseli ve yazı tipini panelden düzenleyin.` |

"İlk ay ücretsiz" ifadesi bugünkü sitede var; geçerliliği sahibe soruldu (bkz. §11).

### Başlık yapısı (ana sayfa)
- **H1** (tek): Randevu, iş kaydı, kasa ve web siteniz tek panelde.
- **H2**: Panelin kendisi. Çizim değil. · Bir iş gününde panelin yaptıkları · Dört paket. Ne aldığınız satır satır belli. · Panel sizin işinizin diliyle konuşur · 526 tema. Hepsini panelden siz düzenlersiniz. · İş sahada biter, fiş kendiliğinden çıkar. · Zaten kullandığınız hesaplara bağlanır · Kime emanet ettiğinizi bilin · Sık sorulanlar · (son çağrı)
- **H3**: akış adımları (6), paket adları (4), entegrasyon grupları (8), SSS soruları (8), "Site editörü panelin içinde".
- Telefon numarası başlık etiketi değildir; `<a href="tel:+905444444004">`.
- Arama niyetini taşıyan sözcükler (servis takip programı, randevu programı, işletme yönetim programı) H1 altındaki paragrafta ve H2 altı metinlerde doğal biçimde geçer.

### JSON-LD (tek `@graph`)
- `Organization`: ad, url, logo, `telephone: +90 544 444 40 04`, adres (Etimesgut, Ankara), `sameAs` (sahip verecek).
- `WebSite`: ad, url.
- `SoftwareApplication`: `applicationCategory: BusinessApplication`, `operatingSystem: Web`, `offers` olarak 4 `Offer` (ad, `price`, `priceCurrency: TRY`, `url`). Fiyatlar panelden geldiği için şema da aynı kaynaktan üretilir; fiyat gizlenirse `Offer` çıkarılır.
- `FAQPage`: sayfada görünen 8 soru ve cevap, birebir aynı metin.
- `BreadcrumbList`: sektör, paket ve tema sayfalarında.
- `aggregateRating` ve `review` **konmaz**; gerçek, doğrulanabilir yorum olmadan Google yönergelerine aykırıdır.

### Sosyal kartlar
`og:type=website`, `og:title`, `og:description`, `og:url`, `og:image` (1200×630, yeni yön: beyaz zemin, H1 ve telefon; bugünkü mavi `og-kart.png` değişir), `og:locale=tr_TR`, `og:site_name`. `twitter:card=summary_large_image`, `twitter:title`, `twitter:description`, `twitter:image`.

### sitemap.xml ve robots.txt
- Bugün 137 adres var. Eklenecek: yeni ana sayfa `lastmod`; varsa yeni `/paketler` adresi. `?s=` adresleri sitemap'e **girmez**.
- `/uye-girisi` sitemap'e girmez, `noindex` alır. `/yonetim` robots.txt'ye **yazılmaz** (yazmak adresi ifşa eder); sayfanın kendisi `noindex` başlığı döndürür ve hiçbir yerden bağlantı almaz.
- robots.txt'deki mevcut `Disallow` satırları kalır; `/uye-girisi` eklenmez (noindex'in görülebilmesi için taranabilir kalmalı).
- `lastmod` gerçek değişiklik tarihidir; her derlemede bugünün tarihi basılmaz.

### Canonical, dil, iç bağlantı
- Her sayfada mutlak `rel=canonical`. Ana sayfa `https://onlinekaydet.com/`; `?s=kombi` → `/sektor-kombi.html`; `utm_` gibi parametreler ana adrese.
- Tek dil: `<html lang="tr">`, hreflang yok.
- İç bağlantı: ana sayfadaki 16 sektör satırı ilgili sektör sayfasına, "70 sektörün tamamı" `/sektorler.html`'e gider. Her sektör sayfası ana sayfaya, paketlere, kendi tema listesine ve aynı aileden 3 sektöre bağlanır. Akış satırları `cozum-*` sayfalarına, entegrasyon grupları `/entegrasyonlar.html`'e bağlanır. Bağlantı metni "tıklayın" değil, hedefin adıdır.

### Core Web Vitals
- **LCP** öğesi H1 metnidir (görsel değil). Hero fotoğrafı `fetchpriority="high"`, `<picture>` ile AVIF + WebP, 520 / 1040 genişlik, en çok 90 KB.
- Tüm `<img>` için `width` ve `height` yazılır (CLS 0). İlk ekran dışındaki her görsel `loading="lazy" decoding="async"`.
- Ekran görüntüleri WebP, 1x ve 2x `srcset`; büyük ekran görüntüsü en çok 120 KB.
- Yazı tipleri kendi sunucudan, yalnız `latin` + `latin-ext` alt kümeleri, `font-display: swap`; Bricolage ve Plex Sans `preload`. Yedek yazı tipine `size-adjust` verilir ki yüklenince satırlar kaymasın.
- Kritik CSS satır içi, toplam CSS 30 KB altı; JS yalnız paket anahtarı, SSS, sektör araması ve form için, `defer`, 15 KB altı. Üçüncü taraf betik (GTM) etkileşimden ya da çerez onayından sonra yüklenir.
- Hedef: mobilde LCP 2,0 sn altı, CLS 0,05 altı, INP 200 ms altı.

### Google araçları için sahibin vereceği bilgiler
Hiçbiri uydurulmadı; alanlar boş bırakılır.
- Search Console doğrulama: `<meta name="google-site-verification" content="…">` değeri ya da DNS TXT kaydı.
- Google Tag Manager kapsayıcı kimliği (`GTM-…`) **ya da** doğrudan GA4 ölçüm kimliği (`G-…`). İkisi birden kurulmaz.
- Google Ads dönüşüm kimliği ve etiketi (`AW-…/…`): telefon tıklaması ve form gönderimi için.
- Ölçülecek olaylar: `tel_tikla` (konum: üst, bant, son, mobil çubuk), `deneme_form_gonder`, `paket_sec` (paket adı), `sektor_sec`, `yillik_aylik_degistir`.
- Çerez onay bandı metni ve KVKK onayı: ölçüm çerezleri onaydan sonra çalışır (Consent Mode v2).

## 10. Sahibin sağlaması gerekenler

1. Paket fiyatları ve yıllık indirim kuralı (yer tutucu: 990 / 1.990 / 3.490 / 5.990 ₺, yıllıkta 2 ay hediye).
2. Fotoğraflar: F4 (ofis ya da ekip); F1, F2 ve F5 için ya kendi fotoğraf paketi ya da seçilecek Pexels karelerine onay.
3. Gerçek müşteri yorumu (ad, işletme, yazılı onay). Yoksa blok yayınlanmaz.
4. Google kimlikleri: Search Console doğrulaması, GTM ya da GA4, Ads dönüşüm.
5. Çalışma saatleri (telefon bandının altına yazılabilir), destek e-postası, sosyal medya adresleri.
6. Deneme koşulu: süre ve "kart istenmez" ifadesinin doğruluğu.

## 11. Açık sorular

1. **E-ticaret hangi pakette?** Kodda hiçbir pakette değil. Ek modül mü (ayrı fiyat), Kurumsal'a dahil mi, ayrı bir beşinci paket mi?
2. **Teknik servis dışı sektörlerde paketler neyi açar?** Paket modülleri servis diliyle tanımlı. Kuaför için Başlangıç = randevu + ekip mi? Ana sayfa matrisinin sektöre göre satır değiştirmesi isteniyor mu?
3. **Pazaryeri iddiası**: katalogda 11 ad var, kodda "doğrulandı" işaretli olan 3 (Trendyol, Hepsiburada, N11). Ana sayfada 11'i de yazılsın mı, yoksa çalışanlar ve "hazırlanıyor" ayrı mı gösterilsin? Aynı soru 94 entegrasyon için de geçerli.
4. **"526 tema"**: bunların 496'sı premium işaretli (onaylanana kadar firmaya görünmüyor) ve denenen 8 temadan 4'ünde fotoğraf yerinde gri kutu var. Ana sayfada 526 mı, onaylı tema sayısı mı yazılsın?
5. **Öne çıkan paket** Tam Paket seçildi (web sitesi dahil olduğu için). Profesyonel mi olsun?
6. **"İlk ay ücretsiz. Kart bilgisi istenmez."** hâlâ geçerli mi?
7. **Yeşil yön** onaylanıyor mu? Logo mavi ve turuncu; sayfa yeşil. Uyum kabul mü, yoksa logonun tek renkli (mürekkep) sürümü mü kullanılsın?
8. Saha uygulaması bölümü teknik servis dışı sektörlerde (kuaför, klinik) gizlensin mi?
