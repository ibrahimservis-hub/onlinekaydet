# OnlineKaydet ana sayfa v9 — tasarım şeması

Durum: **onay bekliyor**. Kod yazılmadı; `site/` ve `panel/` dosyalarına dokunulmadı. Bu belge `ana-sayfa-v8-tasarim.md` şemasını günceller; burada değişmediği söylenen her şey için v8 geçerlidir. Araştırma: `ana-sayfa-v9-arastirma.md`.

Onay görselleri (`/tmp/v9/`):

| Dosya | İçerik |
|---|---|
| `mockup.html` | Mockup kaynağı (üretici `build.py`; parçalar `v9.body.html`, `v9.css`, `v9.js`) |
| `ilk-ekran-masaustu.png` | 1440×900 ilk ekran |
| `ilk-ekran-mobil.png` | 390×844 ilk ekran (2x) |
| `masaustu.png` | 1440 px tam sayfa (18.481 px) |
| `mobil.png` | 390 px tam sayfa (1x, 25.000 px civarı) |
| `tema-vitrini.png` | Tema vitrini bölümü |
| `parca-01…07.png` | Masaüstü, 2.800 px'lik parçalar |
| `parca-08…24.png` | Mobil, 1.500 px'lik parçalar (2x, okunaklı) |

v8'e gelen geri bildirim ve v9'daki karşılığı:

| Geri bildirim | v9 |
|---|---|
| Telefon çok büyüktü; düğme olsun | Numara hiçbir yerde iri değil. "Hemen arayın" düğmesi ilk ekranda, son çağrıda ve mobil alt çubukta. Numara yalnız son çağrıda 14 px |
| E-ticaret ilk ekranda olmalı | İlk ekranın sağ yarısı mağaza teması + sipariş paneli + mobil mağaza. Üstte e-ticaret duyuru şeridi, H1'de "mağazanız" vurgulu |
| Hazır temalar ve web sitesi öne çıkmalı | Tema vitrini ilk ekrandan sonraki ilk büyük bölüm: 20 gerçek tema, sektör filtresi, masaüstü + mobil. Editör ayrı bölüm |
| "Çok basit, site değil" | Koyu sahne ve açık kâğıt bölümleri dönüşümlü; 50'den fazla gerçek ekran görüntüsü; yapışkan menülü e-ticaret anlatımı; kaydırınca açılan bölümler ve sayaçlar |

## 1. Yön: "Çam vitrin"

v8'in yazı tipleri ve çam yeşili **korundu**; yüzey dili **değişti**. Gerekçe araştırmadan:

- Rakiplerin tamamı mavi-mor ve kampanya diliyle konuşuyor. Yeşil ve mürekkep bizi o kalabalıktan ayırıyor, logonun mavi-turuncusuyla da çakışmıyor. Yön değiştirmek için neden çıkmadı.
- v8'in "basit" görünmesinin nedeni renk değil yüzeydi: tek beyaz zemin, ince çizgi, az görsel. Premium sayılan sayfaların ortak yanı ürünün gerçek görüntüsünü sahneye koymaları. v9 bunu yapıyor: koyu çam bir "sahne" üstünde cihaz çerçeveleri, aralarda açık kâğıt bölümler.
- E-ticaret için ikinci bir işaret rengi eklendi (kiremit). Yalnız mağazayla ilgili yerlerde: e-ticaret etiketi, ek modül bandı, sipariş bildirimi. Sayfanın geri kalanı yeşil ve mürekkep.

"Yapay zekâ görünümü" denetimi: mor ya da mavi yok; renk gradyanı yok (ilk ekrandaki ızgara çizgileri 1 px düz çizgidir); blob, parıltı, cam efekti, neon yok; emoji ve süs ikonu yok (sayfada ikon kullanılmıyor); stok fotoğraf yok; bölümler sola yaslı, hiçbiri ortalı değil; tema ızgarası 6+6, 4+4+4 dönüşümlü; yönetim bölümü beş farklı genişlikte kutu.

## 2. Renk token'ları

| Token | Değer | Kullanım | v8'e göre |
|---|---|---|---|
| `--kagit` | `#FBFAF6` | ana zemin (sıcak beyaz) | yeni (`#FFFFFF` idi) |
| `--beyaz` | `#FFFFFF` | kart, çerçeve içi, e-ticaret bölümü zemini | – |
| `--zemin` | `#F0EEE6` | paketler ve alt bilgi zemini | ısıtıldı |
| `--murekkep` | `#0D1512` | başlık, metin, dolu düğme | aynı |
| `--metin2` | `#4A5550` | ikincil metin | aynı |
| `--cizgi` | `#D9D7CC` | ince ayırıcı | ısıtıldı |
| `--cam` | `#0A6847` | açık zeminde vurgu: etiket, bağlantı çizgisi, matris işareti | aynı |
| `--cam-koyu` | `#0B2B21` | öne çıkan paket, e-ticaret tema kutusu, evrak kutusu | aynı |
| `--sahne` | `#061A14` | üst çubuk, ilk ekran, editör bölümü, son çağrı | **yeni** |
| `--cizgi-k` | `#234A3C` | koyu zeminde çizgi | yeni |
| `--filiz` | `#A8E0BF` | koyu zeminde vurgu ve ana düğme (üstünde `--sahne` yazı, yaklaşık 12:1) | **yeni** |
| `--acik-k` | `#C4D6CC` | koyu zeminde ikincil metin | yeni |
| `--kiremit` | `#B8431A` | e-ticaret işareti (beyaz üstünde yaklaşık 5,5:1) | **yeni** |
| `--kiremit-acik` | `#F8E6DD` | e-ticaret bantları | yeni |
| `--cam-acik` | `#E0EDE5` | matriste Tam Paket sütunu | aynı |

Logo olduğu gibi kullanılır: koyu zeminde `logo-acik-s.png`, açık zeminde `logo-renkli-s.png`.

## 3. Yazı tipleri

Değişmedi: **Bricolage Grotesque** (başlık, rakam, fiyat; 700), **IBM Plex Sans** (metin), **IBM Plex Mono** (etiket, rozet, çerçeve başlığı). Üçü de depoda (`themes/fonts/`), kendi sunucumuzdan verilir.

Ölçek (masaüstü / mobil): H1 62 / 36 · H2 54 / 36 · son çağrı 60 / 38 · sahne başlığı 34 / 28 · kart başlığı 28 / 24 · fiyat 52 / 44 · rakam 42 / 34 · metin 17 / 16 · küçük 14 · etiket 12. Telefon numarası için ölçek yok.

## 4. Izgara, çerçeve ve köşe

- Kapsayıcı 1280 px içerik, yan boşluk 48 px (mobil 20). 12 sütun, 24 px oluk. Kırılım 760 px.
- Köşe yarıçapı: düğme 6, kart ve çerçeve 10–12, telefon çerçevesi 16–26 (v8'de her şey 2 px idi; cihaz çerçeveleri için yükseltildi).
- **Tarayıcı çerçevesi**: 30 px başlık şeridi, üç nokta, Plex Mono etiket ("Tema önizleme · Nokta Butik", "Panel › Satış › Siparişler"). Uydurma alan adı yazılmaz.
- **Telefon çerçevesi**: 6 px mürekkep kenar.
- Gölge yalnız çerçevelerde.
- Dikey ritim: bölümler arası 128 px (mobil 80), bantların iç boşluğu 112 px (mobil 72).

## 5. Bölüm akışı

| # | Bölüm | Zemin | İçerik | Neden burada |
|---|---|---|---|---|
| 0 | Duyuru şeridi | filiz | "E-ticaret modülü: ürün, sipariş, kampanya, pazaryeri ve iade tek panelde" + bağlantı | E-ticaret, sayfanın ilk satırı |
| 1 | Üst çubuk (yapışkan) | sahne | logo · Temalar, E-ticaret, Web sitesi, İş takibi, Paketler, Sektörler · Üye girişi (`/uye-girisi`) · "Teklif alın" · "Ücretsiz deneyin" | Telefon yok. `/yonetim` hiçbir yerde yok |
| 2 | İlk ekran | sahne | Sol: H1, tek paragraf, üç düğme. Sağ: mağaza teması (tarayıcı), sipariş paneli (tarayıcı), mobil mağaza (telefon), iki bildirim kartı. Altta beş rakam | Reklamdan gelen kişi tek bakışta "site + mağaza + panel" görür |
| 3 | Dört iş | beyaz | Web sitesi · **E-ticaret** (kiremit zeminli, daha geniş) · Randevu · İş takibi; her biri ilgili bölüme iner | Önermenin dört parçası, gezinme haritası |
| 4 | Tema vitrini | kâğıt | Başlık; öne çıkan e-ticaret teması kutusu; yapışkan filtre; 20 tema kartı; "78 iş kolu" kutusu | Sahibin ikinci önceliği; rakiplerde yok |
| 5 | E-ticaret | beyaz | Solda yapışkan sekiz başlıklı menü; sağda sahneler; sonda ek modül bandı | En uzun bölüm; mağaza iddiasının kanıtı |
| 6 | Web sitesi editörü | sahne | Sol: üç adım. Sağ: editör ekranı, üstünde üç işaret etiketi | "Her bölüm düzenlenebilir" sözünün gösterimi |
| 7 | İş takibi ve yönetim | kâğıt | Beş kutu: Randevu ve takvim, Muhasebe ve kasa, Personel takibi, **Evrak takibi**, Raporlar | Rakiplerde olmayan kısım |
| 8 | Paketler | zemin | Aylık/yıllık anahtarı; dört kart; e-ticaret ek modül bandı; 28 satırlık matris (başlığı yapışkan) | Ne olduğunu gördükten sonra fiyat |
| 9 | Sektörler | kâğıt | 16 sektör paketi düğme olarak + "70 sektörün tamamı" | "Bana uyar mı"; sektör sayfalarına iç bağlantı |
| 10 | Entegrasyonlar | kâğıt | Sekiz grup, sayaçlı rakamlar | "Hesaplarımla çalışır mı" |
| 11 | Güven | kâğıt | Dört satır + şirket kimliği. Yorum, logo, puan yok | Uydurma içerik konmaz |
| 12 | SSS | kâğıt | Sekiz soru; ilki "E-ticaret hangi pakette?" | FAQPage şeması |
| 13 | Son çağrı | sahne | Başlık, "Ücretsiz deneyin", "Hemen arayın", üç alanlı teklif formu | Sayfa iki düğmeyle biter |
| 14 | Alt bilgi | zemin | Beş sütun | – |
| — | Mobil alt çubuk (sabit) | sahne | "Hemen arayın" · "Teklif alın" · "Ücretsiz deneyin" | Üç eylem her an ekranda |

v8'den çıkarılanlar: telefon bandı, 176 px'lik son çağrı numarası, altı satırlık iş akışı listesi (içeriği e-ticaret ve yönetim bölümlerine dağıldı), saha uygulaması bandı (gerçek ekran görüntüsü ve fotoğraf gelene kadar; sektör sayfalarında yer alır).

### 5.1 İlk ekran
- H1: **"Web siteniz, mağazanız, randevunuz ve iş takibiniz tek yerde."** "mağazanız" filiz renginde.
- Paragraf: "Hazır temayı seçin, ürünlerinizi ekleyin, siparişi ve randevuyu aynı panelden yönetin. Kasa, personel ve raporlar da orada."
- Düğmeler: "Ücretsiz deneyin" (dolu, filiz) · "Teklif alın" (çerçeveli) · "Hemen arayın" (altı çizili metin, `tel:`).
- Kompozisyon: arkada mağaza teması (Nokta Butik), önde sol altta Siparişler ekranı (11 sipariş, ciro, net kâr, kanal sütunu), sağda mobil mağaza. İki bildirim kartı ("Yeni sipariş · SP-2026-00010 · 5.400 ₺", "Kargoda · Aras Kargo") Siparişler ekranındaki gerçek satırlardan yazıldı; yayında panelden gelen son siparişle değil, sabit örnekle gösterilir.
- Rakam bandı: 78 iş kolu için tema · 126 düzenlenebilir site bölümü · 7 kampanya türü · 94 entegrasyon sağlayıcısı · 17 hazır rapor. Hepsi koddan sayılmıştır (v8 §6).
- Mobil: duyuru tek satır, etiket satırı ve "Hemen arayın" gizlenir (alt çubukta var); kompozisyon ilk ekranın alt yarısına girer.

### 5.2 Tema vitrini
- Kaynak: `themes/html/<slug>.html` dosyalarından 1280×800 (masaüstü) ve 390×760 (mobil, 2x) ekran görüntüsü (`/tmp/v9/temashot9.py`). Tema adı `site/themes.json` içindeki `name`.
- Seçim kuralı: yalnız görselleri eksiksiz temalar. 84 aday gözle denetlendi, 20'si kondu:
  - **E-ticaret ve mağaza (6)**: `n32-edit-eticaret`, `n31-neon-eticaret`, `n36-lux-eticaret`, `31-magaza-kombi`, `37-magaza-elektronik`, `36-magaza-elektrik`
  - **Teknik servis (6)**: `1-kombi`, `10-klima-buz`, `13-beyaz-kaymak`, `22-tesisat-sari`, `25-elektrik-volt`, `19-bilgisayar-lacivert`
  - **Kuaför ve güzellik (4)**: `k7-kesimhane-kuafor`, `k6-butik-kuafor`, `k5-atolye-kuafor`, `k8-sakin-kuafor`
  - **Oto ve nakliye (4)**: `n04-edit-oto-servis`, `n02-cine-oto-servis`, `n08-neon-oto-cekici`, `n19-edit-nakliye`
- Öne çıkan kutu: koyu çam zemin; solda e-ticaret temalarının beş özelliği ve iki bağlantı; sağda temanın **tam sayfa** görüntüsü tarayıcı çerçevesinde 26 saniyede kendi kendine aşağı kayar, önünde mobil görünüm.
- Filtre: Tümü (20) · E-ticaret ve mağaza (6) · Teknik servis (6) · Kuaför ve güzellik (4) · Oto ve nakliye (4). Kaydırınca üstte yapışır. Mobilde yatay kaydırılır.
- Kart: tarayıcı çerçevesinde masaüstü, sağ altta taşan telefon. Üzerine gelince çerçeve 6 px, telefon 12 px yükselir, "Canlı önizleme" etiketi belirir. Altında tema adı, tür, (mağazaysa) "Mağaza" etiketi, "Bu temayı dene".
- "Bu temayı dene" → deneme kaydı, tema seçili (`/demo?tema=<slug>`; adres kodlamada kesinleşir). "Canlı önizleme" → `/tema-onizleme/<slug>.html`.
- Mobilde ilk 8 kart, altında "12 tema daha gösterin".
- Yayında: sektör sayfasında (`?s=`) ilgili küme önce gelir.

### 5.3 E-ticaret bölümü
Masaüstünde sol sütun yapışkan menü; kaydırdıkça etkin başlık kiremit çizgiyle işaretlenir. Mobilde aynı menü üstte yapışan yatay şerit olur.

| # | Başlık | Ekran görüntüsü | Kodda dayanak |
|---|---|---|---|
| 01 | Ürün ve stok | Satış › Ürünler | `urun.py` (`yp/products`, toplu işlem, Excel), `pazaryeri.py` (`yp/stock/take`, `stock/log`) |
| 02 | Sipariş ve kargo | Satış › Siparişler | `siparis.py`: durum akışı, kargo firmaları, toplu işlem, yazdırma |
| 03 | Kampanya ve kupon | Satış › Kampanyalar | `kampanya.py`: 7 tür, `campaigns/try` |
| 04 | Pazaryerleri | Satış › Pazaryerleri | `pazaryeri.py`, `markets_hub.py`; Akakçe ve Cimri beslemesi `eticaret_plus.py` |
| 05 | Ortaklık | Satış › Ortaklar | `ortak.py` |
| 06 | İade | Satış › İadeler | `siparis.py` (`yp/returns`) |
| 07 | Bayi (B2B) | yok (liste boş göründüğü için konmadı) | `b2b.py`: grup iskontosu, başvuru, fiyat listesi, cari |
| 08 | Sepet ve ödeme | yok (ürün fotoğrafı gerekli) | `storefront.py`, `urunsayfa.py`, `eticaret_plus.py` (terk edilen sepet) |

Pazaryeri iddiası iki satırda verilir: **Kodda doğrulanan**: Trendyol, Hepsiburada, N11. **Katalogda, bağlantısı hazırlanıyor**: Çiçeksepeti, Amazon TR, PttAVM, Pazarama, İdefix, Modanisa, Temu.

Ekran görüntüleri yerelde açılan bir e-ticaret deneme hesabından alındı; 12 ürün, 11 sipariş, 5 kampanya, 2 ortak, 1 iade girildi (`/tmp/v9/panelshot9.py`). Ürün ve müşteri adları örnektir.

### 5.4 Web sitesi editörü
Üç adım: (1) Temayı seçin, (2) Bölüme tıklayın, değiştirin: metin, yazı tipi, görsel, sıra; 126 bölümlük kütüphane, (3) Önizleyin ve yayınlayın. Sağda `Web Sitem › Bölümler` ekranı; üstünde üç etiket ekranın ilgili yerini gösterir: "Bölümü aç, kapat, sırala", "Yazı · yazı tipi · görsel", "Bilgisayar ve telefon önizleme". Yayında bu alan üç adımda değişen üç ekran görüntüsü olabilir (çapraz geçiş); video gerekmez.

### 5.5 İş takibi ve yönetim
Beş kutu, her birinde paket rozeti:
- **Randevu ve takvim** (Tam Paket) — Takvim ekranı
- **Muhasebe ve kasa** (Profesyonel) — Kasa ekranı
- **Personel takibi** (Başlangıç) — Ekip ekranı: prim, maaş, avans, ödenecek
- **Evrak takibi** — koyu kutu, beş satır: yazdırılabilir imzalı belge ve PDF fiş (Başlangıç) · dava dosyası, kursiyer evrakı, muayene kaydı (Başlangıç) · teklif ve müşteri onayı (Kurumsal) · e-arşiv fatura bağlantısı (Kurumsal) · **evrak arşivi: dosya yükleme, son tarih uyarısı (Yakında)**
- **Raporlar** (Profesyonel) — Raporlar ekranı

Takvim ve kasa görüntüleri v8'de kurulan kuaför deneme hesabından, ekip ve rapor görüntüleri e-ticaret hesabından.

### 5.6 Hareket
Kütüphane yok; CSS ve `IntersectionObserver`. Toplam JS 2 KB civarı.

| Hareket | Nerede | Nasıl |
|---|---|---|
| İlk ekran girişi | kompozisyonun beş parçası | 26 px aşağıdan, 140 ms arayla, 0,8 sn |
| Kademeli belirme | kartlar, sahneler, kutular | 22 px yukarı + opaklık, 0,6 sn; aynı satırdakiler 70 ms arayla |
| Sayaç | ilk ekran rakamları, entegrasyon rakamları | görününce 0'dan değere, 0,9 sn |
| Çerçeve içi kayma | öne çıkan tema | tam sayfa görüntü 26 sn'de aşağı, sonra geri |
| Yapışkan öğeler | üst çubuk, tema filtresi, e-ticaret menüsü, matris başlığı | `position: sticky` |
| Etkin başlık | e-ticaret menüsü | görünen sahneye göre |
| Üzerine gelme | tema kartı, düğmeler | 2–12 px yükselme |
| Filtre | tema kartları | anında gizle/göster |

`prefers-reduced-motion: reduce` açıkken animasyon ve geçişlerin tamamı kapalı, öğeler görünür, sayaç son değeri gösterir. JS yoksa da her şey görünür (gizleme `.js` sınıfına bağlı).

## 6. Paket ve özellik matrisi

Kaynak `panel/firms.py` `DEFAULT_PACKAGES`; her paket bir öncekini içerir. Fiyatlar **yer tutucu** (990 / 1.990 / 3.490 / 5.990 ₺). v8'e göre fark: satırlar sahibin istediği başlıklarla yeniden gruplandı; muhasebe, personel takibi ve evrak takibi ayrı gruplar oldu.

| Grup | Satır | Baş. | Pro. | Tam | Kur. | Kod |
|---|---|:-:|:-:|:-:|:-:|---|
| İş takibi | İş ve servis kayıtları | ● | ● | ● | ● | `servis` |
| | Sektörel iş akışı (servis formu, dava dosyası, muayene, iş emri, kursiyer) | ● | ● | ● | ● | `isakis.py` `FLOWS` |
| **Personel takibi** | Ekip, yetki ve iş yükü | ● | ● | ● | ● | `personel` |
| | Prim, maaş, avans ve ödenecek tutar | – | ● | ● | ● | Ekip ekranı; kasaya bağlı (bkz. açık soru 3) |
| | Otomatik atama ve canlı saha takibi | – | – | – | ● | `atama`, `takip` |
| **Muhasebe** | Kasa: tahsilat, gider, gün sonu | – | ● | ● | ● | `muhasebe` |
| | Cari ve alacak takibi | – | ● | ● | ● | `muhasebe` |
| | Raporlar (17 hazır rapor) | – | ● | ● | ● | `rapor` |
| | SMS ve mesaj şablonları | – | ● | ● | ● | `sms` |
| **Evrak takibi** | Yazdırılabilir, imzalı belge | ● | ● | ● | ● | `isakis.py` `belge_html` |
| | Dosya ve evrak durumu alanları | ● | ● | ● | ● | `isakis.py` (dava dosyası, kursiyer) |
| | Teklif ve müşteri onayı | – | – | – | ● | `teklif` |
| | E-arşiv fatura bağlantısı | – | – | – | ● | `efatura` |
| | Evrak arşivi (dosya yükleme, sözleşme saklama, son tarih uyarısı) | Yakında | Yakında | Yakında | Yakında | **kodda yok** |
| Web sitesi | Web sitesi ve hazır temalar | – | – | ● | ● | `site` |
| | Online randevu | – | – | ● | ● | `randevu` |
| | Pazarlama | – | – | ● | ● | `pazarlama` |
| Satış | Yedek parça mağazası | – | – | ● | ● | `magaza` |
| | E-ticaret: ürün, varyant, stok | Ek | Ek | Ek | Ek | `eticaret` |
| | E-ticaret: sipariş, kargo, iade | Ek | Ek | Ek | Ek | `eticaret` |
| | E-ticaret: kampanya ve kupon | Ek | Ek | Ek | Ek | `eticaret` |
| | E-ticaret: pazaryerleri | Ek | Ek | Ek | Ek | `eticaret` |
| | E-ticaret: ortaklık | Ek | Ek | Ek | Ek | `eticaret` |
| | Bayi (B2B) | – | – | – | ● | `bayi` |
| Kurumsal | Ödeme linki | – | – | – | ● | `odeme` |
| | Müşteri portalı | – | – | – | ● | `portal` |
| | Bakım hatırlatma ve garanti | – | – | – | ● | `bakim` |
| | QR cihaz etiketi ve arayan numara tanıma | – | – | – | ● | `qr`, `arayan` |
| | Modül sayısı | 2 | 5 | 9 | 19 | |

Sunum: dört kart (kime göre, modül sayısı, fiyat, 4–6 maddelik özet, düğme); Tam Paket koyu ve 14 px yüksek. Altında kiremit çerçeveli "Ek modül: E-ticaret" bandı. Matris başlığı kaydırırken yapışır; Tam Paket sütunu açık yeşil. Mobilde dört dar sütun, açıklamalar gizli.

**Evrak takibi notu.** Kodda "evrak takibi" adında bir modül yoktur. Var olanlar matrise ayrı satır olarak yazıldı; genel evrak arşivi "Yakında" olarak işaretlendi ve mockup'ta da öyle görünüyor. Eski paneldeki sektör kontrol listeleri (sözleşme imzalandı, vekâletname alındı, gerekli evraklar tamam) yeni panele taşınmadığı için matrise konmadı.

## 7. Görsel listesi

v9 mockup'ında fotoğraf yeri **yoktur**; "FOTO" dolgusu kalmadı. Görsellerin tamamı gerçek ekran görüntüsü: 20 tema × 2 (masaüstü, mobil), 1 tam sayfa tema, 11 panel ekranı.

Dikkat edilecekler:
1. Teknik servis ve yedek parça temalarının içindeki fotoğraflar (usta kareleri) v8'de "üretilmiş görünümlü" olarak not edilmişti. Tema ekran görüntüsü olarak vitrinde görünüyorlar. Sahibin gerçek fotoğraf paketi gelince temalar güncellenir, vitrin yeniden çekilir.
2. E-ticaret temalarının ilk ekranındaki çanta ve koli görselleri çizimdir (temanın kendi içeriği).
3. Mağaza vitrini ve ürün sayfası ilk ekranda gösterilemedi: örnek ürünlerin fotoğrafı yok. 8–12 gerçek ürün fotoğrafı gelirse ilk ekran kompozisyonuna ürün sayfası ve sepet eklenir.
4. `k7-kesimhane-kuafor` temasının mobil üst çubuğunda "MENÜ" düğmesi 390 px'te kenara taşıyor (temanın kendi sorunu; vitrin için ayrıca düzeltilmeli).
5. Sektör sayfaları (`?s=`) için fotoğraf ihtiyacı v8 §8'deki gibi sürüyor (F5).

Yayında bütün görüntüler aynı betiklerle 1x ve 2x WebP olarak yeniden alınır.

## 8. SEO planı güncellemesi

v8 §9 geçerlidir; değişenler:

- **`<title>`**: `OnlineKaydet: Web Sitesi, E-Ticaret, Randevu ve İş Takip Programı` (64 karakter; 60'ı aşıyor, kısaltmak için "ve İş Takip" → "İş Takibi").
- **`meta description`**: `Hazır temayla web sitenizi ve mağazanızı açın; sipariş, randevu, kasa ve personel tek panelde. 78 iş kolu için tema. Ücretsiz deneyin.`
- **H1**: Web siteniz, mağazanız, randevunuz ve iş takibiniz tek yerde.
- **H2**: Temanızı seçin. Yarın yayında olun. · Mağazanız sitenizin içinde. Hepsi tek stoktan. · Sitenizin her bölümü sizin elinizde. · Mağazanın arkasındaki iş de aynı panelde. · Dört paket. Ne aldığınız satır satır belli. · Panel sizin işinizin diliyle konuşur. · Zaten kullandığınız hesaplara bağlanır. · Kime emanet ettiğinizi bilin. · Karar vermeden önce · Temanızı bugün seçin, mağazanızı bu hafta açın.
- **H3**: dört iş, tema adları, sekiz e-ticaret başlığı, beş yönetim kutusu, paket adları, SSS soruları.
- Yeni hedef sözcükler: "hazır web sitesi teması", "e-ticaret sitesi kurma", "e-ticaret paketi", "pazaryeri entegrasyonu", "randevu programı", "iş takip programı". H1 altı paragrafta ve bölüm girişlerinde doğal geçer.
- **Tema görselleri**: `alt` = "{Tema adı} teması, masaüstü görünüm". Görsel sayısı arttığı için ilk ekran dışındaki hepsi `loading="lazy" decoding="async"`, `width` ve `height` yazılı. Vitrin kartı görüntüsü en çok 45 KB (640 px WebP), mobil görüntü en çok 25 KB.
- **LCP**: öğe yine H1 metni. İlk ekrandaki üç görsel `fetchpriority="high"` değil, yalnız mağaza teması görüntüsü öncelikli; diğer ikisi normal.
- **JSON-LD**: `SoftwareApplication.offers` dört paket (fiyat panelden). E-ticaret eki fiyatı belli olunca beşinci `Offer`. `ItemList` (tema vitrini) eklenebilir: her öğe tema adı + önizleme adresi. `aggregateRating` ve `review` yine yok.
- **İç bağlantı**: tema kartları `/tema-onizleme/<slug>.html`; filtre sekmeleri ilgili `/temalar-<kume>` sayfasına da bağlanır (sayfalar varsa); e-ticaret başlıkları `cozum-*` sayfalarına; sektör düğmeleri `/sektor-<ad>.html`.
- **Olaylar** (v8 listesine ek): `tema_filtre` (küme), `tema_onizle` (slug), `tema_dene` (slug), `eticaret_baslik` (başlık), `teklif_form_gonder`. `tel_tikla` konumları: ilk ekran, son çağrı, mobil çubuk.
- Yapışkan öğeler ve belirme hareketleri CLS üretmez (yalnız `transform` ve `opacity`).

## 9. Sahibin sağlaması gerekenler

1. Paket fiyatları ve e-ticaret ek modülünün fiyatı.
2. Mağaza vitrini için 8–12 gerçek ürün fotoğrafı (kendi ürünleri ya da lisanslı).
3. Teknik servis temaları için gerçek fotoğraf paketi (daha önce göndereceğini söylediği).
4. Gerçek müşteri yorumu, logo, müşteri sayısı (varsa, yazılı onaylı). Yoksa güven bölümü bugünkü hâliyle kalır.
5. "Ücretsiz deneyin" koşulu: süre, kart istenip istenmediği.
6. Google kimlikleri (v8 §9), çalışma saatleri, destek e-postası.

## 10. Açık sorular

1. **E-ticaret hangi pakette, kaç lira?** Kodda hiçbir pakette değil; mockup "ek modül" diyor. Duyuru şeridi ve ilk ekran e-ticareti bu kadar öne çıkarırken fiyatının belli olması gerekir.
2. **Tema sayısı.** `themes.json` 526 tema, 78 iş kolu diyor; denetlenenlerin çoğunda görsel boş. Mockup "526" yazmıyor, "78 iş kolu için hazır tema" yazıyor. Bu ifade de eksik temalar tamamlanana kadar fazla mı? Seçenek: "20 hazır tema, yenileri ekleniyor".
3. **Prim, maaş, avans** hangi pakette? Ekip ekranında herkese görünüyor, hesap kasaya bağlı. Matriste Profesyonel yazıldı.
4. **Evrak arşivi** (dosya yükleme, son tarih uyarısı) yapılacak mı? "Yakında" olarak sitede görünmesi isteniyor mu, yoksa yazılana kadar satır kaldırılsın mı?
5. **Bayi (B2B)**: paket modülü olarak Kurumsal'da, ama panelde mağaza açılınca Bayiler ekranı geliyor. Sitede Kurumsal mı yazsın, e-ticaret ekinin parçası mı?
6. **Kiremit** e-ticaret rengi onaylanıyor mu, yoksa yalnız yeşil mi kalsın?
7. **Saha uygulaması bölümü** v9'da yok. Teknik servis sektör sayfalarında mı kalsın, ana sayfaya da dönsün mü?
8. "Bu temayı dene" nereye gitsin: doğrudan deneme kaydı mı, önce canlı önizleme mi?
