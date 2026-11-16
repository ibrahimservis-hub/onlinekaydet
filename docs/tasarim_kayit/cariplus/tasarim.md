# OnlineKaydet panel tasarımı — "CariPlus yönü"

Kapsam: müşteri (firma) paneli `panel/yp_ui.html` ve sahip paneli `panel/sahip/src.html` (→ `index.html`).
Eski panel (`panel/public_panel/`, ServisPlus tabanlı ekranlar) kapsam dışıdır; dokunulmaz.
Bu klasördeki dosyalar yalnızca tasarımdır; uygulama dosyalarında değişiklik yapılmamıştır.

| Dosya | İçerik |
|---|---|
| `tokens.css` | `:root` belirteçleri + ortak bileşen sınıfları (yapıştırılabilir) |
| `mockup-musteri.html` | Müşteri paneli: Genel Bakış + Satış › Ürünler (soldaki menüden geçilir, `#satis`) |
| `mockup-sahip.html` | Sahip paneli: Genel Bakış + Firmalar (`#firmalar`) |
| `shot-*-1440.png`, `shot-*-390.png` | Genel Bakış ekran görüntüleri |
| `shot-musteri-urunler-*.png`, `shot-sahip-firmalar-*.png` | Liste ekranı görüntüleri |

Referans: `../referans-cariplus-panel.jpg`. Referanstan alınan: yerleşim iskeleti (dar ikonlu menü, sekme şeridi, tek renkli özet kartı + beyaz metrikler, iki sütun vade listesi, sütun grafik, üst çubukta arama/firma/avatar). Alınmayan: kırmızı renk.

## 1. Mevcut durum ve değişen

| | Şimdi | Yeni |
|---|---|---|
| Menü | 216 px (müşteri) / 236 px (sahip) koyu lacivert, tek sütun uzun liste (müşteride 20+ satır, ekrana sığmıyor) | 84 px beyaz, ikon üstte + 10,5 px etiket; en fazla 9–11 modül. Alt ekranlar sekme şeridine taşınır |
| Üst çubuk | Yok; firma adı menünün dibinde | 52 px beyaz çubuk: arama, yardım, bildirim, firma adı + paket, avatar |
| Sekme | Yok (sahipte yalnız bazı sayfalarda `.tabs`) | Her modülde 42 px sekme şeridi |
| Zemin | Müşteri: sıcak bej `#f5f4ef`; sahip: `#f6f7f9` | İkisinde aynı nötr `#f4f5f7` |
| Köşe | Müşteri 8–14 px, hap biçimli rozet/çip; sahip 3–4 px | Denetimler 6 px, kart 8 px, rozet 4 px. Hap biçimi yok |
| Vurgu | Müşteri mavi; sahip mavi + turuncu birincil düğme | Tek vurgu: `#1650b0`. Turuncu yalnızca logoda ve bildirim noktasında |
| Genel bakış | Dört eşit rakam kutusu + boş listeler | Renkli ana özet + metrik şeridi + iki vade listesi + nakit akışı grafiği |
| Grafik | `.gr2b .bar` gradyanlı sütun | Düz renk çift sütun, gradyan yok |

## 2. Renk belirteçleri

Tüm adlar `--ds-` ile başlar; mevcut `--ink`, `--blue`, `--ok`, `--nv`, `--bl` vb. ile çakışmaz, geçiş sırasında yan yana durabilir.

Nötr ölçek (hafif soğuk, düşük doygunluk):

| Belirteç | Değer | Kullanım |
|---|---|---|
| `--ds-n-0` | `#ffffff` | Kart, menü, üst çubuk yüzeyi |
| `--ds-n-25` | `#fafbfc` | Tablo başlığı, satır üzerine gelme, modal altlığı |
| `--ds-n-50` | `#f4f5f7` | Sayfa zemini |
| `--ds-n-100` | `#eceef1` | Yumuşak ayırıcı (satır arası) |
| `--ds-n-200` | `#e1e4e9` | Standart 1 px çizgi |
| `--ds-n-300` | `#cdd2da` | Form/düğme kenarı, grafikte ikinci seri |
| `--ds-n-400` | `#9aa2b0` | Pasif ikon |
| `--ds-n-500` | `#6a7281` | Üçüncül metin (tarih, açıklama) |
| `--ds-n-600` | `#4a5160` | İkincil metin |
| `--ds-n-700` | `#333945` | — |
| `--ds-n-800` | `#1f242e` | Avatar, sayaç, bildirim kutusu zemini |
| `--ds-n-900` | `#141820` | Ana metin |

Anlam katmanı: `--ds-bg`, `--ds-surface`, `--ds-surface-2`, `--ds-line`, `--ds-line-soft`, `--ds-line-strong`, `--ds-text`, `--ds-text-2`, `--ds-text-3` (hepsi yukarıdaki ölçeğe bağlı).

Vurgu ve marka:

| Belirteç | Değer | Not |
|---|---|---|
| `--ds-ac` | `#1650b0` | Tek vurgu. Birincil düğme, etkin menü/sekme, bağlantı, grafikte ana seri. Beyaz üstünde karşıtlık ≈ 7:1 |
| `--ds-ac-hover` | `#11428f` | Üzerine gelme |
| `--ds-ac-tint` | `#edf2fb` | Etkin menü zemini, odak halkası |
| `--ds-ac-line` | `#c7d6f0` | Bilgi rozeti kenarı |
| `--ds-brand-navy` | `#0c2550` | Logodaki lacivert; sahip panelinde ana özet kartı zemini |
| `--ds-brand-orange` | `#f27a1a` | Yalnızca logo ve okunmamış bildirim noktası. Düğme, başlık, rozet rengi olarak kullanılmaz |
| `--ds-hero` | müşteri: `--ds-ac`, sahip: `--ds-brand-navy` | Ana özet kartı zemini; `body.ds-sahip` ile değişir |

Durum renkleri (metin / zemin / kenar):

| Durum | Metin | Zemin | Kenar |
|---|---|---|---|
| Başarı | `--ds-ok #17734a` | `--ds-ok-bg #e8f4ed` | `--ds-ok-line #bfdfcc` |
| Uyarı | `--ds-warn #8f5606` | `--ds-warn-bg #fbf1dc` | `--ds-warn-line #ecd5a2` |
| Hata | `--ds-err #b3261e` | `--ds-err-bg #fbeae8` | `--ds-err-line #f0c4bf` |
| Bilgi | `--ds-info #1650b0` | `--ds-info-bg #edf2fb` | `--ds-info-line #c7d6f0` |

Kural: durum rengi yalnızca anlam taşıyan yerde (rozet, tutar, değişim oku). Süs olarak renkli kenarlı kart, renkli ikon kutusu yok.

## 3. Yazı

Yazı tipi: **Inter** korunur (iki panelde de `font-family` zaten Inter ile başlıyor; Türkçe karakterleri tam). Yığın: `Inter,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif`.
Dikkat: paneller Inter'i şu an **yüklemiyor**, yalnızca adını yazıyor; Inter kurulu olmayan Windows'ta Segoe UI görünür. Tutarlılık isteniyorsa `Inter-roman.var.woff2` dosyası (latin-ext alt kümesi, yaklaşık 100 KB) panelle birlikte sunulup `@font-face{font-family:Inter;src:url(/salon/inter.woff2) format("woff2");font-weight:100 900;font-display:swap}` eklenmeli. Dış CDN kullanılmaz.

| Belirteç | Boyut | Ağırlık | Kullanım |
|---|---|---|---|
| `--ds-fs-28` | 28 px | 650 | Ana özet kartındaki tutar |
| `--ds-fs-20` | 20 px | 650 | Metrik değeri |
| `--ds-fs-16` | 16 px | 600 | Sayfa başlığı (`h1`) |
| `--ds-fs-14` | 14 px | 600 | Kart ve modal başlığı; mobilde gövde |
| `--ds-fs-13` | 13 px | 400/500 | Gövde, tablo, düğme (600) |
| `--ds-fs-12` | 12 px | 400/600 | Alt açıklama, alan etiketi, küçük düğme |
| `--ds-fs-11` | 11 px | 600 | Rozet, tablo başlığı, değişim satırı |
| — | 10,5 px | 500 | Menü etiketi, grafik eksen yazısı |

- Bütün para, adet, tarih ve yüzde alanlarında `font-variant-numeric:tabular-nums` (`.ds-num` ya da bileşenin kendi kuralı).
- Tablo başlıkları BÜYÜK HARF değil; cümle düzeni, 11 px 600.
- Para biçimi: `28.460,50 ₺` (mevcut `tl()` işleviyle aynı sıra; her zaman iki ondalık). Tarih: `3 Eki 2026`. Yüzde: `%12,5`.
- Harf aralığı yalnız büyük rakamlarda −0,015/−0,02 em.

## 4. Aralık, köşe, çizgi, gölge

- Aralık: `--ds-s-1…8` = 4, 8, 12, 16, 20, 24, 32 px. Sayfa iç boşluğu 16/24 px; kartlar arası 16 px; kart iç boşluğu 16 px yatay.
- Köşe: `--ds-r-sm` 4 px (rozet, küçük görsel), `--ds-r` 6 px (düğme, alan), `--ds-r-lg` 8 px (kart, modal). Daha büyük köşe yok; yalnız avatar ve sayaç yuvarlak.
- Çizgi: her yerde 1 px. Kart kenarı `--ds-line`, satır arası `--ds-line-soft`, denetim kenarı `--ds-line-strong`.
- Gölge: kartlarda **yok**. Yalnız açılır katman (`--ds-shadow-pop`) ve modal (`--ds-shadow-modal`).
- Denetim yüksekliği 34 px (`--ds-ctl-h`), küçük 28 px. Mobilde alt çubuk öğesi en az 44 px.
- Geçiş efekti yok sayılır; istenirse yalnız renk/kenar için 120 ms.

## 5. Bileşenler

### Dikey menü — `.ds-rail`
- 84 px, beyaz, sağında 1 px çizgi, `position:sticky`, tam yükseklik. Üstte 52 px kutuda yalnız logo simgesi (bulut + belge; `assets/ok-logo-renkli.png` dosyasının sol 544 px'lik kısmı).
- Öğe `.ds-rail-item`: 20 px çizgi ikon, altında 10,5 px etiket, ortalı. Varsayılan `--ds-text-3`; üzerine gelince `--ds-text`.
- Etkin `.on`: zemin `--ds-ac-tint`, yazı/ikon `--ds-ac`, solda 2 px vurgu çubuğu.
- Grup: başlık yazısı yok; gruplar arasında `.ds-rail-sep` (1 px çizgi). Ayarlar/Destek (sahipte Ayarlar/Çıkış) `.ds-rail-nav.end` ile dibe yaslanır.
- Sayaç `.ds-rail-count`: koyu nötr küçük sayı (bekleyen sipariş, açık talep).

### Üst çubuk — `.ds-top`
52 px, beyaz, altında 1 px çizgi. Soldan: arama (`.ds-search`, 320 px, `Ctrl K` ipucu) · boşluk · yardım · bildirim (okunmamışta turuncu nokta) · dikey çizgi · firma adı + alt satırda paket (`.ds-firm`) · 30 px avatar (`.ds-avatar`, baş harfler, koyu nötr).

### Sekme şeridi — `.ds-tabs`
42 px, beyaz. Sekme `.ds-tab`: 15 px ikon + 13 px etiket + isteğe bağlı sayı. Etkin: koyu metin, 600, altında 2 px vurgu çizgisi, ikon vurgu renginde. Taşarsa yatay kayar (kaydırma çubuğu gizli).

### Kartlar
- **Ana özet `.ds-hero`**: ekranda tek tane. Düz renk zemin (gradyan yok), beyaz yazı: etiket satırı, 28 px tutar, açıklama, ince çizgi altında 2–3 kırılım (`.ds-hero-split`). 300 px sabit genişlik.
- **Metrik şeridi `.ds-metrics` / `.ds-metric`**: dört ayrı kart değil, **tek çerçeve içinde dikey çizgiyle bölünmüş** dört hücre. Hücre: başlık (12/600), dönem (11), değişim satırı (`.ds-delta.up/.down/.warn`, ok ikonu + yüzde + "geçen aya göre"), altta 20 px değer.
- **Liste kartı `.ds-card` + `.ds-list` / `.ds-row`**: başlık + sağda "Tümünü gör" bağlantısı, altında özet satırı ("Önümüzdeki 30 gün · Toplam …"). Satır 36 px: rozet (74 px sütun) · tarih · ad (taşarsa üç nokta) · tutar sağda. Tahsilat `.in` yeşil, ödeme `.out` kırmızı, metin durumu `.txt` nötr.
- **Genel kart `.ds-card`**: beyaz, 1 px çizgi, 8 px köşe, gölgesiz. `.ds-card-hd`, `.ds-card-sub`, `.ds-card-bd`.

### Tablo — `.ds-table`
Kart içinde; üstte `.ds-toolbar` (arama, seçim kutuları, sağda `.ds-seg` süzgeç), altta `.ds-tfoot` (kayıt sayısı, toplamlar, `.ds-pager`). Başlık 34 px `--ds-n-25` zemin; satır 46 px; sayısal sütunlar sağa yaslı ve tabular. İlk hücre `.ds-cell`: 32 px görsel (`.ds-thumb`, ürün fotoğrafı varsa `<img class="ds-thumb">`) ya da baş harf kutusu (`.ds-mono`) + iki satır metin. Satır işlemleri: küçük ikon düğmeler (`.ds-btn.sm.ghost.icon`). Stok uyarısı: `.ds-low` (10'un altı), `.ds-zero`.

### Rozet — `.ds-badge`
20 px, 4 px köşe, 11 px 600, açık zemin + 1 px kenar. Türler: varsayılan (nötr), `.ok`, `.warn`, `.err`, `.info`. Önünde nokta yok, hap biçimi yok.

### Düğme — `.ds-btn`
| Tür | Sınıf | Görünüm |
|---|---|---|
| Birincil | `.ds-btn.primary` | Vurgu zemin, beyaz yazı. Ekranda bir tane |
| İkincil | `.ds-btn` | Beyaz zemin, `--ds-line-strong` kenar |
| Tehlike | `.ds-btn.danger` (onay modalinde `.danger.solid`) | Kırmızı yazı + açık kırmızı kenar; dolu hâli yalnız son onayda |
| Sessiz | `.ds-btn.ghost` | Kenarsız; satır içi ikon işlemleri |
| Küçük / ikon | `.sm`, `.icon` | 28 px; kare |
| Bağlantı | `.ds-link` | 12 px 600 vurgu rengi |

### Form alanı — `.ds-field`
`<label class="ds-field"><span>Etiket</span><input class="ds-input"><small>Yardım</small></label>`. 34 px, 6 px köşe; odakta vurgu kenar + 3 px açık halka. Hata: `.ds-field.err`. Seçim: `.ds-select` (kendi ok işareti). İki sütun: `.ds-grid2`. Bölümlü seçim: `.ds-seg`.

### Modal — `.ds-overlay` + `.ds-modal`
Koyu nötr %45 perde (bulanıklık yok). 520 px (`.wide` 760 px), 8 px köşe. Başlık (14/600, altı çizgili), gövde 16 px, altlık `--ds-n-25` zeminde sağa yaslı düğmeler (ikincil solda, birincil sağda). Mobilde alttan açılan tam genişlik sayfa.

### Boş durum — `.ds-empty`
Sola yaslı, ortalanmaz: 18 px nötr ikon + kalın tek satır başlık + tek cümle açıklama + bir `.ds-link` eylem. Çizim/illüstrasyon yok. Örnek: "Bugün sırada randevu yok. — Takvimden yeni randevu ekleyebilirsiniz. — Randevu ekle".

### Uyarı satırı ve bildirim
`.ds-note` (`.warn/.err/.ok`): açık zemin + 1 px kenar. `.ds-toast`: sağ altta koyu nötr kutu, hata için kırmızı.

### Grafik — `.ds-chart`
- Sütun grafik, HTML/CSS ile (kütüphane gerekmez): `.ds-chart-col` içinde iki `<i>`; yükseklik yüzde olarak verilir.
- İki seri: ana seri `--ds-ac`, ikinci seri `--ds-n-300`. Gerçekleşmemiş (beklenen) günler aynı renk %35 saydam (`.est`). Kırmızı/yeşil sütun yok; anlam, üstteki "Giriş / Çıkış / Net" rakam satırında.
- Yatay kılavuz çizgileri `--ds-line-soft`, taban çizgisi `--ds-line-strong`; eksen yazısı 10,5 px tabular ("10 B" = bin).
- Sütun üstü köşe 1 px, gradyan ve gölge yok. Gösterge (`.ds-legend`) 8 px kare.
- Aylık görünümde `.ds-chart.wide` (daha kalın sütun).

## 6. İki panelde ortak olanlar ve farklar

Ortak: bütün belirteçler, yazı ölçeği, menü/üst çubuk/sekme iskeleti, kart, tablo, rozet, düğme, form, modal, grafik.

| | Müşteri paneli (`body.ds.ds-musteri`) | Sahip paneli (`body.ds.ds-sahip`) |
|---|---|---|
| Ana özet zemini | `--ds-ac` (mavi) | `--ds-brand-navy` (lacivert) — iki panel bir bakışta ayrılır |
| Ana özet içeriği | Bugünkü kasa; nakit / banka / POS | Aylık yinelenen gelir; yıllık / aylık planlar |
| Metrikler | Dönem tahsilatı, dönem ödemesi, vadesi geçmiş alacak, bu ay sipariş | Aktif firma, bu ay tahsilat, süresi yaklaşan, açık talep |
| Listeler | Vadesi yaklaşan tahsilatlar / ödemeler (tutar renkli) | Süresi yaklaşan abonelikler (tutar nötr) / bekleyen kurulum ve talepler (sağda durum metni) |
| Grafik | Günlük nakit akışı, 30 gün | Aylık tahsilat, 12 ay (`.wide`) |
| Menü | Modüle göre değişir (`buildNav`); 9–11 öğe | Sabit 5 öğe + Ayarlar, Çıkış |
| Üst çubuk sağı | Firma adı + paket | "OnlineKaydet Yönetim" + rol |
| Mobil alt çubuk | Genel, Takvim, Satış, Kasa, Diğer | Genel, Satış, Firmalar, Finans, Diğer |
| Terimler | Sektöre göre (kuaförde "uzman", serviste "teknisyen"); maketteki örnek yedek parça + servis firması | Sabit |

### Menü → sekme dağılımı (öneri)

Müşteri paneli (`BASE_NAV` + `buildNav` rotaları):

| Menü öğesi | Sekmeler (rota) |
|---|---|
| Genel Bakış | Genel Bakış (`bugun`), Bildirimler (`bildirim`), Duyurular (`duyuru`) |
| Takvim | Takvim (`takvim`), Randevular (`randevu`), İş kayıtları (`is`) |
| Müşteriler | Müşteriler (`musteri`), Üyelik (`uyelik`) |
| Satış | Ürünler (`urun`), Siparişler (`siparis`), Kampanyalar (`kampanya`), İadeler (`iade`), Pazaryerleri (`pazaryeri`), Fiyat ve güvenlik (`eplus`) |
| Kasa | `kasa` |
| Ekip | `ekip` |
| Raporlar | `rapor` |
| Web Sitem | Site (`site`), İçerikler (`icerik`), Popup vitrin (`popvitrin`), Diller (`dil`), Yönlendirmeler (`yonlendir`) |
| Bağlantılar | `entegrasyon` |
| Ayarlar / Destek (dipte) | `ayar` / `destek` |

Modülü kapalı olan rota sekmede görünmez; grubun hiç sekmesi kalmazsa menü öğesi de gizlenir.

Sahip paneli (`NAV` dizisindeki `g` grupları zaten bu yapıda):

| Menü öğesi | Sekmeler |
|---|---|
| Genel Bakış | `genel` |
| Satış | Satış Hattı, Yeni Kurulum, Talepler |
| Firmalar | Firmalar, Kurulum Adımları, Toplu İşlemler, Yetki ve Roller |
| Finans | Abonelik ve Tahsilat, Paketler ve Fiyatlar |
| Sistem | Alan Adları, Kurulum Hazırlığı, Sistem Durumu |

## 7. Mevcut sınıf → yeni stil eşlemesi

### `panel/yp_ui.html` (müşteri)

| Mevcut | Yeni | Not |
|---|---|---|
| `:root{--ink,--blue,--paper,--line,--mut,--r…}` | `--ds-*` | Eskiler geçiş bitene kadar kalabilir. `--paper` (bej) → `--ds-bg`; `--r:10px` → `--ds-r-lg` (8) |
| `body` | `body.ds.ds-musteri` | 14 → 13 px gövde |
| `.app` (216 px + 1fr) | `.ds-app` (84 px + 1fr) | `<main>` bir `.ds-body` içine alınır: üst çubuk + sekme + `.ds-page` |
| `.rail`, `.rail .logo`, `.rail a`, `.rail a.on` | `.ds-rail`, `.ds-rail-logo`, `.ds-rail-item`, `.on` | Koyu zemin kalkar; logo `/salon/logo.png` (beyaz yazılı) yerine renkli simge |
| `.rail a .bd` (sarı hap) | `.ds-rail-count` | |
| `.rail .firm`, `#fn`, `#fu`, `#out` | `.ds-top` içindeki `.ds-firm` + `.ds-avatar` | Çıkış: avatar menüsüne |
| `.mhd` (mobil koyu başlık) | `.ds-top` + `.ds-top-logo` | |
| `.mbar`, `.mbar a.on` | `.ds-mbar` | Ortadaki yuvarlak gölgeli `+` (`.mbar a.plus`) kalkar; "Yeni kayıt" sayfa başındaki birincil düğmedir |
| `.top`, `.top h1` (25 px), `.top p` | `.ds-bar`, `h1` 16 px, `.ds-muted` | |
| `.btn`, `.btn.p`, `.btn.s`, `.btn.d` | `.ds-btn`, `.primary`, `.sm`, `.danger` | 40 → 34 px, 8 → 6 px köşe |
| `.lnk`, `.card .hd a` | `.ds-link` | |
| `.card`, `.card .hd`, `.card h2`, `.pad` | `.ds-card`, `.ds-card-hd`, `h2`, `.ds-card-bd` | |
| `.figs`, `.fig` | `.ds-metrics`, `.ds-metric` (+ `-lbl`, `-sub`, `-val`, `.ds-delta`) | Solda ayrıca `.ds-hero`; ikisi `.ds-summary` içinde |
| `.cols` (1fr + 340 px) | `.ds-cols2` (eşit iki sütun) | |
| `.row`, `.row .t`, `.row .m` | `.ds-row`, `.ds-row-name`, `.ds-row-date`, `.ds-row-amt` | |
| `.tag`, `.tag.w/.g/.b/.y/.r` | `.ds-badge`, (yok)/`.ok`/`.info`/`.warn`/`.err` | `:before` noktası ve 20 px yuvarlak kalkar |
| `.av` | `.ds-avatar` (kişi) / `.ds-mono` (kare) | Renkli avatar zeminleri → nötr |
| `.bar`, `.bar i`, `.stokbar` | Tabloda rakam + `.ds-low/.ds-zero`; doluluk için 4 px yükseklik, 2 px köşe, `--ds-ac` | |
| `table`, `th`, `td`, `td.r`, `.tw` | `.ds-table`, `.r`, `.num`, `.ds-tablewrap` | Öğe seçicileri yerine sınıf; `th` zemini `#faf9f6` → `--ds-n-25` |
| `.fbar` | `.ds-toolbar` (+ `.ds-search`, `.ds-select`) | |
| `.chips`, `.chip`, `.chip.on` | Süzgeçte `.ds-seg`; çoklu seçimde 6 px köşeli çip (`.ds-badge` ölçüsünde, `.on` = vurgu kenar + tint) | Hap biçimi kalkar |
| `.seg`, `.seg button.on` | `.ds-seg` | Etkin: koyu dolgu yerine beyaz yüzey |
| `.sumline` | `.ds-tfoot` | |
| `.stt` | `.ds-metrics` (küçük) ya da `.ds-tfoot` | |
| `.pimg` | `.ds-thumb` | Gerçek ürün fotoğrafı `<img>` ile |
| `label.f` | `.ds-field` + `.ds-input/.ds-select/.ds-textarea` | 40 → 34 px, 15 → 13 px |
| `.g2`, `.g3` | `.ds-grid2` (üçlü için aynı kalıp) | |
| `.sw2` (anahtar) | Aynı yapı; açık renk `--ds-ac`, kapalı `--ds-n-300` | |
| `#ov`, `.md`, `.md.wide`, `.mh`, `.mb`, `.mf` | `.ds-overlay`, `.ds-modal`, `.wide`, `.ds-modal-hd`, `.ds-modal-bd`, `.ds-modal-ft` | 14 → 8 px köşe; gölge hafifler |
| `.empty` | `.ds-empty` | Ortalı → sola yaslı, eylem bağlantılı |
| `.note`, `.errbox`, `.okbox`, `.hlp` | `.ds-note` (+ `.err`, `.ok`), `.ds-muted` | |
| `#toast`, `#toast.bad` | `.ds-toast`, `.err` | Alt orta → sağ alt (mobilde alt çubuğun üstü) |
| `.gr2b`, `.gr2b .bar` | `.ds-chart`, `.ds-chart-col i` | `linear-gradient` kaldırılır |
| `.rpl .ri.on`, `.ictab`, `.stabs` | `.ds-tabs` / `.ds-tab.on` kalıbı | İç sekmelerde de aynı alt çizgi |
| `.cal`, `.ev.*` | Yapı aynı; renkler `--ds-*-bg` + sol 3 px `--ds-*`; köşe 4 px | |
| `svg.i` + `<symbol id="home">…` | `.ds-ico` + `#i-home…` | Çizgi kalınlığı 1,75 → 1,5. Mevcut semboller korunur; eklenenler: `search, down, right, up, dn, export, edit, dots, box, building, card, pulse, funnel, globe, out, clock, check, shield` (maketteki `<defs>`) |

### `panel/sahip/src.html` (sahip) — düzenlenecek dosya `src.html`, sonra `python3 build.py`

| Mevcut | Yeni | Not |
|---|---|---|
| `:root{--nv,--bl,--or,--bg,--ink,--ln,--mu,--ok,--er,--wa,--r}` | `--ds-*` | `--or` düğme rengi olarak kullanılmaz |
| `body` | `body.ds.ds-sahip` | |
| `.app` (236 px) / `.side` / `.main` | `.ds-app` / `.ds-rail` / `.ds-body` > `.ds-page` | `shell()` işlevi üst çubuk + sekme şeridini de üretmeli |
| `.brand`, `.brand small` ("Sahip Paneli") | `.ds-rail-logo`; rol yazısı `.ds-firm small` | `build.py` içindeki `LOGO_D` (açık logo) yerine renkli simge gömülür |
| `.g` (grup başlığı) | `.ds-rail-sep`; grup adı menü öğesinin kendisi olur | `NAV` içindeki `["g","Satış"]` satırları menü öğesine, altındakiler sekmeye dönüşür |
| `.n`, `.n.on`, `.n b`, `.n b.hot` | `.ds-rail-item`, `.on`, `.ds-rail-count` | Turuncu sol çizgi → vurgu rengi |
| `.usr` | `.ds-firm` + `.ds-avatar` (üst çubuk) | |
| `.hd`, `.hd h1`, `.hd .r` | `.ds-bar`, `h1`, sağdaki düğmeler | |
| `.bt`, `.bt.b`, `.bt.o`, `.bt.r`, `.bt.sm` | `.ds-btn`, `.primary`, `.primary`, `.danger`, `.sm` | Turuncu `.bt.o` da birincil maviye iner |
| `.cd`, `.cd>h3`, `.cd>.sub`, `.cd>.bd` | `.ds-card`, `.ds-card-hd h2`, `.ds-card-sub`, `.ds-card-bd` | |
| `.kp`, `.kp>div` (altı eşit kutu) | `.ds-summary` = `.ds-hero` + `.ds-metrics` (dört hücre) | Altı rakamdan biri ana özete, dördü şeride; kalan biri grafiğin özet satırına |
| `.pl`, `.pl.ok/.er/.wa/.bl/.gy` | `.ds-badge`, `.ok/.err/.warn/.info`/(yok) | |
| `table`, `th` (büyük harf), `td`, `tr.cl` | `.ds-table` | `text-transform:uppercase` kalkar |
| `.tabs`, `.tabs a.on` | `.ds-tabs`, `.ds-tab.on` | |
| `.tb` | `.ds-toolbar` | |
| `.fd`, `.in`, `.in.xs`, `.row2`, `.row3` | `.ds-field`, `.ds-input`, (genişlik satır içi), `.ds-grid2` | |
| `.g2` (1fr + 340 px) | `.ds-cols2` | |
| `.tg`, `.tg.on` | Aynı yapı; açık renk `--ds-ac` | Yeşil → vurgu |
| `.chip`, `.chip.on` | 6 px köşeli çip; `.on` = `--ds-ac-tint` + vurgu kenar | Lacivert dolgu kalkar |
| `.note`, `.note.er`, `.note.ok`, `.ownb` | `.ds-note`, `.err`, `.ok`, `.warn` | |
| `.dt` | Aynı yapı; çizgi `--ds-line-soft` | |
| `.bars`, `.bars i` | Aynı yapı; 6 px yükseklik, `--ds-ac`; ya da `.ds-chart.wide` | |
| `.mdl`, `.mb`, `.mb>h3`, `.mc`, `.mf` | `.ds-overlay`, `.ds-modal`, `.ds-modal-hd`, `.ds-modal-bd`, `.ds-modal-ft` | |
| `.kb`, `.kc`, `.kd` (satış hattı) | Sütun zemini `--ds-n-100`; kart `.ds-card` + 6 px köşe; sol renkli çizgi kalkar, aşama `.ds-badge` ile | |
| `.pg` | 4 px yükseklik, `--ds-ac` | |
| `.td`, `.td b` | `.ds-row` + `.ds-rail-count` benzeri nötr sayaç | Turuncu sayaç kalkar |
| `.nm`, `.nm .lo` | `.ds-cell`, `.ds-mono` | |
| `.toast`, `.toast.er` | `.ds-toast`, `.err` | |
| `.mu`, `.sm` | `.ds-muted`, `font-size:var(--ds-fs-12)` | |
| `i[data-i]` + `icons.js` (`stroke-width:2`) | `.ds-ico` ölçüleri; `stroke-width:1.5` | İkon yolları aynı kalabilir |
| `.lgw`, `.lgc` (giriş ekranı) | Kapsam dışı; dokunulmaz | |

## 8. Duyarlı davranış

| Genişlik | Davranış |
|---|---|
| ≥ 1181 px | Ana özet 300 px + metrik şeridi yan yana; listeler iki sütun |
| ≤ 1180 px | Ana özet üstte tam genişlik, metrik şeridi altında |
| ≤ 900 px | Listeler tek sütun; üst çubukta firma adı gizlenir |
| ≤ 720 px | Menü gizlenir → `.ds-mbar` (5 öğe, alta sabit). Üst çubuk: logo simgesi + arama + bildirim + avatar. Metrikler 2×2. Liste satırı iki satıra iner (ad + tutar / rozet + tarih). Tabloda `.opt` sütunları ve seçim kutusu gizlenir, ürün adı iki satıra kadar kırılır. Gövde 14 px. Modal alttan açılır |

Makette 1440 ve 390 px genişlikte yatay taşma olmadığı Playwright ile ölçüldü (`scrollWidth − innerWidth = 0`).

## 9. Yapılmayacaklar

Gradyan (düğme, kart, grafik dahil), cam/bulanıklık, parlak leke, emoji, 8 px'ten büyük köşe, kart gölgesi, hap rozet, renkli ikon kutuları, ortalanmış boş durum çizimleri, birbirinin aynısı kart ızgarası, ikinci bir vurgu rengi, büyük harfli tablo başlığı.

## 10. Açık noktalar (karar bekleyen)

1. Kullanıcı onayı: uygulamaya geçmeden önce ekran görüntüleri onaylatılacak.
2. Referans notunda logo "takvim + onay simgesi" diye geçiyor; depodaki dosya (`assets/ok-logo-renkli.png`) bulut + belge simgesi. Maket depodaki logoyu kullanıyor.
3. Ana özet kartındaki "POS bekleyen", metriklerdeki "Vadesi geçmiş alacak" ve vade listeleri için uçların hazır olup olmadığı denetlenmeli (`finance.py`, `finance_plus.py`); veri yoksa hücre gizlenmeli, sıfırla doldurulmamalı.
4. Maketteki bütün rakamlar ve firma adları örnektir.
