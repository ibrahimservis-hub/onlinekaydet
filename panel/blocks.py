"""Bölüm motoru: tema bölümleri, rozetler ve sektör paketleri birer veri kaydıdır.

Yeni sektör açmak = var olan bölümlerden paket derlemek. Kod yazılmaz.
Her bölüm; alanları (fields), düzen seçenekleri, rozetleri, hareketi ve
**bilgisayar/telefon için ayrı** ayarlarıyla birlikte tanımlanır.
"""
import re
import uuid

# ---------------------------------------------------------------- alan tipleri
# text  tek satır · area çok satır · sel seçim · num sayı · sw aç/kapa
# color renk · font yazı tipi · img tek görsel · imgs çoklu görsel
# urun  ürün seçici · link hedef seçici · rozet rozet listesi · slider kaydırıcı
TYPES = ("text", "area", "sel", "num", "sw", "color", "font", "img", "imgs", "urun", "link", "rozet", "slider")


def F(key, label, typ="text", **kw):
    """Tek bir düzenlenebilir alan."""
    f = {"k": key, "l": label, "t": typ}
    f.update(kw)
    return f


# Sık kullanılan alan öbekleri -------------------------------------------------
def TEXTS(title="Başlık", sub="Alt yazı", cta=True):
    out = [F("title", title), F("sub", sub, "area")]
    if cta:
        out += [F("cta", "Düğme yazısı"), F("cta_to", "Düğme nereye gitsin", "link")]
    return out


LAYOUT = [F("count", "Kaç tane gösterilsin", "sel", opt=[4, 6, 8, 12, 16, 24], d=8),
          F("cols", "Sütun (bilgisayar)", "sel", opt=[2, 3, 4, 6], d=4),
          F("cols_m", "Sütun (telefon)", "sel", opt=["1", "2", "kaydırmalı"], d="2", m=True)]

MOTION = [F("anim_in", "Kaydırınca belirsin", "sw", d=True),
          F("anim_hover", "Üstüne gelince büyüsün", "sw", d=True),
          F("anim_auto", "Kendiliğinden kaysın", "sw", d=False)]

STYLE = [F("font_h", "Başlık yazı tipi", "font"), F("font_b", "Metin yazı tipi", "font"),
         F("color", "Yazı rengi", "color"), F("bg", "Arka plan", "color"),
         F("radius", "Köşe yuvarlaklığı", "slider", min=0, max=24, d=12),
         F("pad", "Bölüm boşluğu", "slider", min=0, max=120, d=56, m=True)]

PRODUCTS = [F("rule", "Ürünler nasıl seçilsin", "sel", d="manuel",
              opt=["manuel", "indirim", "coksatan", "yeni", "stok_az", "kampanyali", "rastgele"]),
            F("items", "Ürünler", "urun"),
            F("cat", "Kategori (kuralla seçerken)", "sel"),
            F("badges", "Rozetler", "rozet"),
            F("all_text", "“Tümünü gör” yazısı"), F("all_to", "“Tümünü gör” hedefi", "link")]

# ---------------------------------------------------------------- rozetler
BADGES = [
    {"id": "indirim", "name": "İndirim %", "color": "#be123c", "pos": "tl", "motion": True, "auto": "discount"},
    {"id": "yeni", "name": "Yeni", "color": "#0b7a4b", "pos": "tr", "motion": False, "auto": "new_30d"},
    {"id": "coksatan", "name": "Çok satan", "color": "#b4600a", "pos": "tl", "motion": False, "auto": "bestseller"},
    {"id": "son_adet", "name": "Son {n} adet", "color": "#1c1a17", "pos": "bar", "motion": True, "auto": "low_stock"},
    {"id": "kargo", "name": "Kargo bedava", "color": "#1155cc", "pos": "bar", "motion": False, "auto": "free_ship"},
    {"id": "hediyeli", "name": "Hediyeli", "color": "#7a1fa2", "pos": "tr", "motion": False, "auto": ""},
    {"id": "tukendi", "name": "Tükendi", "color": "#6b7385", "pos": "tl", "motion": False, "auto": "out_of_stock"},
    {"id": "firsat", "name": "Fırsat", "color": "#e11d48", "pos": "tl", "motion": True, "auto": "deal"},
]
BADGE_POS = {"tl": "sol üst", "tr": "sağ üst", "bl": "sol alt", "br": "sağ alt", "bar": "alt şerit"}

# ---------------------------------------------------------------- kategoriler
CATS = [("tanitim", "Tanıtım"), ("hareketli", "Hareketli"), ("hizmet", "Hizmet"), ("eticaret", "E-ticaret"),
        ("guven", "Güven"), ("gorsel", "Görsel"), ("ekip", "Ekip"), ("donusum", "Dönüşüm"),
        ("icerik", "İçerik"), ("bilgi", "Bilgi"), ("yapi", "Yapı"), ("sektorel", "Sektörel"), ("serbest", "Serbest")]
CAT_NAMES = dict(CATS)

# rozet etiketleri: urun=panelden ürünle dolar, panel=panel verisinden dolar,
# hareket=animasyonlu, hazir=yapı bölümü, sektorel=sektöre özel
_B = []


def B(bid, cat, name, desc, wire, fields, tags=(), sectors=("*",), manage="", needs=(), resp=True):
    """Bir bölüm tanımı. resp=True → bilgisayar ve telefon için ayrı ayar tutulur."""
    _B.append({"id": bid, "cat": cat, "name": name, "desc": desc, "wire": wire,
               "fields": list(fields), "tags": list(tags), "sectors": list(sectors),
               "manage": manage, "needs": list(needs), "resp": resp})


# ---- Tanıtım -----------------------------------------------------------------
B("hero", "tanitim", "Ana görsel", "Başlık, alt yazı ve çağrı düğmesi", "hero",
  TEXTS() + [F("img", "Arka plan görseli", "img"), F("align", "Hizalama", "sel", opt=["sol", "orta", "sağ"], d="sol", m=True)] + STYLE)
B("hero_video", "tanitim", "Ana görsel + video", "Arkada otomatik oynayan video", "video",
  TEXTS() + [F("video", "Video bağlantısı"), F("poster", "Kapak görseli", "img"), F("mute", "Sessiz başlasın", "sw", d=True)] + STYLE,
  tags=["hareket"])
B("hero_slider", "tanitim", "Ana sayfa slider", "Hareketli görsel üzerine yazı", "full",
  [F("slides", "Slaytlar (görsel + başlık + yazı + düğme)", "imgs"),
   F("speed", "Geçiş süresi (sn)", "num", d=5), F("effect", "Geçiş biçimi", "sel", opt=["kayma", "solma", "yakınlaşma"], d="kayma"),
   F("dots", "Nokta göstergesi", "sw", d=True), F("arrows", "Ok düğmeleri", "sw", d=True),
   F("h_m", "Telefonda yükseklik", "slider", min=240, max=680, d=420, m=True)] + STYLE,
  tags=["hareket"])
B("hero_split", "tanitim", "Bölünmüş kapak", "Solda yazı, sağda büyük görsel", "split", TEXTS() + [F("img", "Görsel", "img")] + STYLE)
B("hero_search", "tanitim", "Arama kutulu kapak", "Ürün / ilan / hizmet araması", "form",
  TEXTS(cta=False) + [F("ph", "Arama kutusu yazısı"), F("scope", "Nerede arasın", "sel", opt=["ürün", "hizmet", "ilan", "yazı"])] + STYLE)
B("hakkimizda", "tanitim", "Hakkımızda", "Hikâye, fotoğraf + yazı", "split", TEXTS() + [F("img", "Fotoğraf", "img")] + STYLE)
B("sayilarla", "tanitim", "Sayılarla biz", "Yıl, müşteri, iş sayısı", "stat",
  [F("items", "Sayılar (rakam + açıklama)", "area"), F("count_anim", "Rakamlar sayarak gelsin", "sw", d=True)] + STYLE, tags=["hareket"])
B("duyuru_bar", "tanitim", "Duyuru çubuğu", "Üstte kampanya ve geri sayım", "band",
  [F("text", "Duyuru yazısı"), F("end", "Geri sayım bitişi"), F("cta", "Düğme yazısı"),
   F("cta_to", "Hedef", "link"), F("closable", "Ziyaretçi kapatabilsin", "sw", d=True)] + STYLE, manage="Pazarlama › Duyuru")
B("deger", "tanitim", "Değer önerisi", "3 kısa fayda, ikonlu", "g3", [F("items", "Faydalar", "area")] + STYLE)
B("video_tanitim", "tanitim", "Karşılama videosu", "Kısa tanıtım filmi", "video", TEXTS(cta=False) + [F("video", "Video bağlantısı")] + STYLE)

# ---- Hareketli ---------------------------------------------------------------
for _i, (_id, _n, _d, _w) in enumerate([
        ("kayan_yazi", "Kayan yazı şeridi", "Sonsuz kayan duyuru / marka", "band"),
        ("daktilo", "Daktilo başlık", "Harf harf yazılan başlık", "hero"),
        ("sayac_anim", "Sayaç animasyonu", "Rakamlar sıfırdan sayar", "stat"),
        ("scroll_in", "Kaydırınca beliren", "Bölümler yumuşak girer", "rows"),
        ("sticky", "Yapışkan bölüm", "Kaydırırken sabit kalır", "split"),
        ("parallax", "Parallax arka plan", "Görsel farklı hızda kayar", "full"),
        ("logo_akis", "Kayan logo şeridi", "Markalar sonsuz akar", "logos"),
        ("kart_deste", "Kart destesi", "Üst üste gelen kartlar", "g3"),
        ("once_sonra", "Öncesi – Sonrası", "Sürüklenen karşılaştırma", "ba"),
        ("ilerleme", "Sayfa ilerleme çubuğu", "Üstte okuma göstergesi", "band")]):
    B(_id, "hareketli", _n, _d, _w,
      TEXTS(cta=False) + [F("speed", "Hız", "slider", min=1, max=10, d=5),
                          F("on_m", "Telefonda da çalışsın", "sw", d=True, m=True)] + STYLE, tags=["hareket"])

# ---- Hizmet ------------------------------------------------------------------
B("hizmet_liste", "hizmet", "Hizmet ve fiyat listesi", "Panelinizdeki hizmetlerden", "rows",
  TEXTS(cta=False) + [F("show_price", "Fiyatları göster", "sw", d=True), F("show_dur", "Süreleri göster", "sw", d=True),
                      F("group", "Kategoriye göre ayır", "sw", d=False)] + STYLE, tags=["panel"], manage="Ayarlar › Hizmetler")
B("hizmet_kart", "hizmet", "Hizmet kartları", "Resimli kart dizisi", "g3", TEXTS(cta=False) + LAYOUT + STYLE, tags=["panel"], manage="Ayarlar › Hizmetler")
B("hizmet_sekme", "hizmet", "Sekmeli hizmetler", "Kategoriye göre ayrılmış", "faq", TEXTS(cta=False) + STYLE, tags=["panel"], manage="Ayarlar › Hizmetler")
B("paketler", "hizmet", "Paketler", "Çoklu seans, indirimli paket", "g3", TEXTS(cta=False) + LAYOUT + STYLE, tags=["panel"], manage="Pazarlama › Paketler")
B("fiyat_tablo", "hizmet", "Fiyat tablosu", "Karşılaştırmalı paketler", "g3", TEXTS(cta=False) + STYLE, tags=["panel"], manage="Ayarlar › Hizmetler")
B("surec", "hizmet", "Süreç adımları", "1-2-3 nasıl çalışır", "stat", TEXTS(cta=False) + [F("items", "Adımlar", "area")] + STYLE)
B("hesaplayici", "hizmet", "Fiyat hesaplayıcı", "Seçime göre tahmini tutar", "form", TEXTS(cta=False) + [F("items", "Seçenekler ve katsayılar", "area")] + STYLE, tags=["hareket"])
B("teklif", "hizmet", "Teklif formu", "Serbest teklif talebi", "form", TEXTS() + STYLE, tags=["panel"], manage="Gelen kutusu")
B("hediye_ceki", "hizmet", "Hediye çeki", "Online hediye kartı satışı", "split", TEXTS() + STYLE, tags=["panel"], manage="Pazarlama › Hediye çekleri")
B("karsilastirma", "hizmet", "Karşılaştırma tablosu", "Biz / diğerleri", "g3", TEXTS(cta=False) + [F("items", "Satırlar", "area")] + STYLE)

# ---- E-ticaret: ürün vitrinleri ---------------------------------------------
_SHOP = ("eticaret", "market", "tekstil", "lokanta", "eczane", "petshop", "yedek_parca")
for _id, _n, _d, _w, _rule, _tg in [
        ("v_indirim", "İndirimli ürünler", "İndirim oranı en yüksek olanlar", "g3", "indirim", ["urun"]),
        ("v_firsat", "Fırsat ürünleri", "Günün fırsatı · sayaçlı", "g3", "kampanyali", ["urun", "hareket"]),
        ("v_coksatan", "Çok satanlar", "Satış adedine göre otomatik", "g3", "coksatan", ["urun"]),
        ("v_yeni", "Yeni gelenler", "Son eklenen ürünler", "g3", "yeni", ["urun"]),
        ("v_secili", "Öne çıkanlar", "Elle seçtiğiniz ürünler", "g3", "manuel", ["urun"]),
        ("v_kampanya", "Kampanyalı ürünler", "X al Y öde, sepet indirimi", "g3", "kampanyali", ["urun"]),
        ("v_tukeniyor", "Tükenmek üzere", "Son birkaç adet kalanlar", "g3", "stok_az", ["urun", "hareket"]),
        ("v_birlikte", "Birlikte alınanlar", "Sepet ortalamasını yükseltir", "g3", "manuel", ["urun"]),
        ("v_son_bakilan", "Son görüntülenenler", "Ziyaretçiye özel", "g3", "manuel", ["urun", "hareket"]),
        ("v_serit", "Kaydırmalı ürün şeridi", "Yatay kayan, otomatik", "band", "manuel", ["urun", "hareket"]),
        ("v_buyuk_kart", "Büyük kart + küçük kartlar", "Bir büyük, yanında küçükler", "hero", "manuel", ["urun"]),
        ("v_izgara", "Izgara vitrin", "2 / 3 / 4 / 6 sütun", "g6", "manuel", ["urun"]),
        ("v_hizli_sepet", "Sepete hızlı ekle", "Karttan çıkmadan", "g3", "manuel", ["urun"])]:
    B(_id, "eticaret", _n, _d, _w,
      TEXTS(cta=False) + [dict(PRODUCTS[0], d=_rule)] + PRODUCTS[1:] + LAYOUT + MOTION + STYLE,
      tags=_tg, sectors=list(_SHOP), manage="Ürünler", needs=["shop"])
B("v_kategori", "eticaret", "Kategori vitrini", "Koleksiyon kapakları", "g6",
  TEXTS(cta=False) + [F("items", "Kategoriler", "sel"), F("img_mode", "Görsel biçimi", "sel", opt=["kare", "dikey", "geniş"], d="kare")] + LAYOUT + STYLE,
  tags=["urun"], sectors=list(_SHOP), manage="Ürünler › Kategoriler", needs=["shop"])
B("v_marka", "eticaret", "Marka vitrini", "Sattığınız markalar", "logos",
  TEXTS(cta=False) + [F("items", "Markalar", "sel")] + STYLE, tags=["urun"], sectors=list(_SHOP), manage="Ürünler › Markalar", needs=["shop"])
B("v_stok_haber", "eticaret", "Stoğa gelince haber ver", "Tükenen üründe kayıt", "form",
  TEXTS() + STYLE, tags=["urun"], sectors=list(_SHOP), manage="Müşteriler", needs=["shop"])
B("guvence", "eticaret", "Güvence şeridi", "Kargo, iade, güvenli ödeme", "logos",
  [F("items", "Maddeler (ikon + yazı)", "area")] + STYLE, sectors=list(_SHOP), needs=["shop"])
B("odeme_logo", "eticaret", "Ödeme yöntemleri", "Kabul edilen kartlar", "logos", [F("auto", "Bağlı POS'tan otomatik", "sw", d=True)] + STYLE,
  tags=["panel"], sectors=list(_SHOP), manage="Entegrasyonlar › Sanal POS", needs=["shop"])
B("taksit", "eticaret", "Taksit tablosu", "Banka ve taksit seçenekleri", "rows", [F("auto", "Bağlı POS'tan otomatik", "sw", d=True)] + STYLE,
  tags=["panel"], sectors=list(_SHOP), manage="Entegrasyonlar › Sanal POS", needs=["shop"])
B("siparis_takip", "eticaret", "Sipariş takip", "Kodla kargo sorgulama", "form", TEXTS() + STYLE,
  tags=["panel"], sectors=list(_SHOP), manage="Siparişler", needs=["shop"])
B("uyelik", "eticaret", "Üyelik ve favoriler", "Giriş, kayıt, favori listesi", "form",
  [F("fav", "Favoriler açık", "sw", d=True), F("wallet", "Cüzdan / puan", "sw", d=False),
   F("social", "Google / Facebook ile giriş", "sw", d=True)] + STYLE,
  tags=["panel"], sectors=list(_SHOP) + ["lokanta", "otel", "kurs"], manage="Müşteriler › Üyeler", needs=["uyelik"])
B("sepet_hatirlat", "eticaret", "Sepet hatırlatma", "Çıkışta açılan pencere", "cta", TEXTS() + STYLE,
  tags=["hareket", "panel"], sectors=list(_SHOP), manage="Pazarlama", needs=["shop"])

# ---- Güven -------------------------------------------------------------------
B("yorumlar", "guven", "Müşteri yorumları", "Kart veya kayan şerit", "quote",
  TEXTS(cta=False) + [F("min_star", "En az kaç yıldız", "sel", opt=[3, 4, 5], d=4), F("style", "Biçim", "sel", opt=["kart", "kayan şerit", "tek büyük"], d="kart")] + LAYOUT + STYLE,
  tags=["panel"], manage="Yorumlar")
B("google_yorum", "guven", "Google yorumları", "Google puanınız ve yorumlar", "quote",
  TEXTS(cta=False) + [F("show_score", "Puanı başlıkta göster", "sw", d=True)] + LAYOUT + STYLE, tags=["panel"], manage="Yorumlar › Google")
B("video_yorum", "guven", "Video yorum", "Müşteri videoları", "video", TEXTS(cta=False) + STYLE, tags=["panel"], manage="Yorumlar")
B("yildiz_ozet", "guven", "Yıldız özeti", "Ortalama puan ve dağılım", "stat", TEXTS(cta=False) + STYLE, tags=["panel"], manage="Yorumlar")
B("markalar", "guven", "Kullandığımız markalar", "Logo şeridi", "logos", TEXTS(cta=False) + [F("imgs", "Logolar", "imgs")] + STYLE)
B("sertifika", "guven", "Sertifikalar", "Belge ve eğitim rozetleri", "g5", TEXTS(cta=False) + [F("imgs", "Belgeler", "imgs")] + STYLE, manage="Web Sitem › Belgeler")
B("basinda", "guven", "Basında biz", "Haber ve röportajlar", "rows", TEXTS(cta=False) + [F("items", "Bağlantılar", "area")] + STYLE)
B("guven_rozet", "guven", "Güvence rozetleri", "SSL, iade, KVKK", "logos", [F("items", "Rozetler", "area")] + STYLE)
B("referans", "guven", "Referans müşteriler", "Çalıştığınız firmalar", "logos", TEXTS(cta=False) + [F("imgs", "Logolar", "imgs")] + STYLE)

# ---- Görsel ------------------------------------------------------------------
B("galeri", "gorsel", "Galeri", "Izgara, büyütmeli", "g6", TEXTS(cta=False) + [F("imgs", "Fotoğraflar", "imgs"), F("light", "Tıklayınca büyüsün", "sw", d=True)] + LAYOUT + STYLE,
  tags=["panel"], manage="Web Sitem › Fotoğraflar")
B("galeri_kayan", "gorsel", "Kayan galeri", "Yatay fotoğraf şeridi", "band", TEXTS(cta=False) + [F("imgs", "Fotoğraflar", "imgs")] + MOTION + STYLE, tags=["hareket", "panel"], manage="Web Sitem › Fotoğraflar")
B("masonry", "gorsel", "Masonry galeri", "Farklı boylarda yerleşim", "g6", TEXTS(cta=False) + [F("imgs", "Fotoğraflar", "imgs")] + LAYOUT + STYLE, tags=["panel"], manage="Web Sitem › Fotoğraflar")
B("instagram", "gorsel", "Instagram akışı", "Son gönderileriniz", "g6", TEXTS(cta=False) + [F("count", "Kaç gönderi", "sel", opt=[4, 6, 8, 12], d=6)] + STYLE,
  tags=["panel"], manage="Ayarlar › Bağlantılar", needs=["instagram"])
B("video_galeri", "gorsel", "Video galeri", "Birden çok video", "g3", TEXTS(cta=False) + [F("items", "Video bağlantıları", "area")] + LAYOUT + STYLE)
B("gorsel_360", "gorsel", "360° görsel", "Çevrilebilir ürün / mekân", "video", TEXTS(cta=False) + [F("imgs", "Kareler", "imgs")] + STYLE, tags=["hareket"])
B("tam_gorsel", "gorsel", "Tam genişlik görsel", "Sayfayı bölen büyük kare", "full", [F("img", "Görsel", "img"), F("img_m", "Telefon görseli", "img", m=True)] + TEXTS(cta=False) + STYLE)
B("resim_yazi", "gorsel", "Resim + yazı", "Yan yana anlatım", "split", TEXTS() + [F("img", "Görsel", "img"), F("side", "Görsel tarafı", "sel", opt=["sol", "sağ"], d="sol")] + STYLE)

# ---- Ekip --------------------------------------------------------------------
B("ekip", "ekip", "Ekip kartları", "Panelinizdeki ekipten", "g3", TEXTS(cta=False) + LAYOUT + STYLE, tags=["panel"], manage="Ekip")
B("uzman", "ekip", "Uzman tanıtımı", "Tek kişi, uzun tanıtım", "split", TEXTS() + [F("img", "Fotoğraf", "img")] + STYLE, tags=["panel"], manage="Ekip")
B("kariyer", "ekip", "Eleman arıyoruz", "Kariyer çağrısı + başvuru", "cta", TEXTS() + STYLE, tags=["panel"], manage="Gelen kutusu › Başvurular")

# ---- Dönüşüm -----------------------------------------------------------------
B("cta_serit", "donusum", "Çağrı şeridi", "Dikkat çeken bant ve düğme", "cta", TEXTS() + STYLE)
B("randevu_form", "donusum", "Gömülü randevu formu", "Sayfanın içinde takvim", "form", TEXTS() + STYLE, tags=["panel"], manage="Randevu ayarları")
B("iletisim_form", "donusum", "İletişim formu", "Mesaj kutusu, panele düşer", "form", TEXTS() + [F("fields", "Alanlar", "area")] + STYLE, tags=["panel"], manage="Gelen kutusu")
B("geri_arama", "donusum", "Geri arama talebi", "Numaranı bırak, arayalım", "form", TEXTS() + STYLE, tags=["panel"], manage="Gelen kutusu")
B("whatsapp", "donusum", "WhatsApp butonu", "Köşede sabit düğme", "band",
  [F("num", "Numara"), F("msg", "Hazır mesaj"), F("pos", "Konum", "sel", opt=["sağ alt", "sol alt"], d="sağ alt"), F("on_m", "Telefonda göster", "sw", d=True, m=True)] + STYLE,
  tags=["panel"], manage="Ayarlar › İletişim")
B("bulten", "donusum", "Bülten / SMS kaydı", "Kampanyalardan haberdar et", "form", TEXTS() + [F("kvkk", "KVKK onay kutusu", "sw", d=True)] + STYLE,
  tags=["panel"], manage="Pazarlama › Bülten")
B("popup", "donusum", "Açılır pencere / duyuru", "Siteye girene mesaj", "cta",
  TEXTS() + [F("when", "Ne zaman çıksın", "sel", opt=["hemen", "5 sn sonra", "sayfa yarısında", "çıkarken"], d="5 sn sonra"),
             F("once", "Ziyaretçiye bir kez", "sw", d=True), F("img", "Görsel", "img")] + STYLE,
  tags=["hareket", "panel"], manage="Pazarlama › Duyuru")
B("gerisayim", "donusum", "Geri sayım", "Kampanya bitimine kalan", "band", TEXTS() + [F("end", "Bitiş tarihi")] + STYLE, tags=["hareket"])

# ---- İçerik ------------------------------------------------------------------
B("blog", "icerik", "Blog / yazılar", "Son yazılar", "g3", TEXTS(cta=False) + LAYOUT + STYLE, tags=["panel"], manage="Web Sitem › Blog")
B("sss", "icerik", "Sık sorulan sorular", "Açılır kapanır liste", "faq", TEXTS(cta=False) + [F("items", "Soru ve cevaplar", "area"), F("search", "Arama kutusu", "sw", d=False)] + STYLE,
  tags=["panel"], manage="Web Sitem › SSS")
B("zaman", "icerik", "Zaman çizelgesi", "Tarih tarih hikâye", "rows", TEXTS(cta=False) + [F("items", "Maddeler", "area")] + MOTION + STYLE, tags=["hareket"])
B("sekme", "icerik", "Sekmeli içerik", "Başlıklara ayrılmış", "faq", TEXTS(cta=False) + [F("items", "Sekmeler", "area")] + STYLE)
B("alinti", "icerik", "Alıntı / söz", "Büyük puntolu cümle", "quote", [F("text", "Söz", "area"), F("who", "Kim söyledi")] + STYLE)
B("dosya", "icerik", "İndirilebilir dosya", "Katalog, fiyat listesi PDF", "rows", TEXTS(cta=False) + [F("items", "Dosyalar", "imgs")] + STYLE,
  tags=["panel"], manage="Web Sitem › Dosyalar")
B("rehber", "icerik", "Adım adım rehber", "Numaralı anlatım", "rows", TEXTS(cta=False) + [F("items", "Adımlar", "area")] + STYLE)
B("vaka", "icerik", "Vaka çalışması", "Önce-sonra iş anlatımı", "split", TEXTS() + [F("img", "Görsel", "img")] + STYLE)

# ---- Bilgi -------------------------------------------------------------------
B("harita", "bilgi", "Harita ve yol tarifi", "Google Haritalar + adres", "map", TEXTS(cta=False) + [F("zoom", "Yakınlık", "slider", min=10, max=18, d=15)] + STYLE,
  tags=["panel"], manage="Ayarlar › Adres")
B("saatler", "bilgi", "Çalışma saatleri", "Gün gün açık/kapalı", "rows", TEXTS(cta=False) + [F("now", "“Şu an açık” rozetini göster", "sw", d=True)] + STYLE,
  tags=["panel"], manage="Ayarlar › Saatler")
B("subeler", "bilgi", "Şubeler", "Birden çok adres", "g3", TEXTS(cta=False) + LAYOUT + STYLE, tags=["panel"], manage="Ayarlar › Şubeler")
B("bolgeler", "bilgi", "Hizmet bölgeleri", "Mahalle ve semt listesi (SEO)", "rows", TEXTS(cta=False) + [F("items", "Bölgeler", "area")] + STYLE,
  tags=["panel"], manage="Ayarlar › Bölgeler")
B("iletisim_bilgi", "bilgi", "İletişim bilgileri", "Telefon, e-posta, sosyal", "rows", TEXTS(cta=False) + STYLE, tags=["panel"], manage="Ayarlar › İletişim")
B("kvkk", "bilgi", "KVKK ve politikalar", "Aydınlatma, çerez", "rows", TEXTS(cta=False) + STYLE, tags=["panel"], manage="Ayarlar › Yasal")
B("iade_kosul", "bilgi", "İade ve kargo koşulları", "Mesafeli satış metinleri", "rows", TEXTS(cta=False) + STYLE,
  tags=["panel"], sectors=list(_SHOP), manage="Ayarlar › Yasal", needs=["shop"])

# ---- Yapı (hazır bölümler) ---------------------------------------------------
B("mobil_bar", "yapi", "Mobil bar", "Telefonda altta sabit düğmeler", "band",
  [F("items", "Düğmeler (ikon + yazı + hedef)", "area"), F("count", "Kaç düğme", "sel", opt=[3, 4, 5], d=4),
   F("motion", "Hareketli olsun", "sw", d=False), F("hide_scroll", "Aşağı kaydırınca gizlensin", "sw", d=True),
   F("style", "Biçim", "sel", opt=["düz", "yüzen", "kavisli"], d="düz")] + STYLE, tags=["hazir"], resp=True)
B("mobil_menu", "yapi", "Mobil menü (kategori görselli)",
  "Telefonda açılan çekmece: kategoriler görselle, iç içe açılır",
  "drawer",
  [F("source", "Kategoriler nereden", "sel", opt=["ürün kategorileri", "elle"], d="ürün kategorileri"),
   F("items", "Elle menü (başlık | görsel | hedef)", "area",
     hint="Her satıra bir kategori. Alt kategori için başına boşluk koyun."),
   F("look", "Görünüm", "sel", opt=["liste", "ızgara", "kart"], d="liste", m=True),
   F("cols_m", "Telefonda sütun", "sel", opt=[1, 2, 3], d=2, m=True),
   F("img", "Görselleri göster", "sw", d=True),
   F("shape", "Görsel biçimi", "sel", opt=["kare", "yuvarlak", "dikey"], d="kare"),
   F("side", "Hangi yandan açılsın", "sel", opt=["sol", "sağ"], d="sol", m=True),
   F("search", "Üstte arama kutusu", "sw", d=True),
   F("login", "Altta giriş / hesap", "sw", d=True),
   F("social", "Altta sosyal medya", "sw", d=False),
   F("motion", "Açılırken kaysın", "sw", d=True)] + STYLE,
  tags=["hazir", "hareket"], manage="Ürünler", resp=True)
B("footer", "yapi", "Footer", "Çok sütunlu alt bilgi", "rows",
  [F("cols", "Sütun sayısı", "sel", opt=[2, 3, 4], d=4), F("logo", "Logo göster", "sw", d=True),
   F("bulten", "Bülten kutusu", "sw", d=True), F("social", "Sosyal medya", "sw", d=True),
   F("odeme", "Ödeme logoları", "sw", d=False), F("links", "Bağlantılar", "area")] + STYLE, tags=["hazir"])
B("menu_gorunum", "yapi", "Menü görünümü", "Klasik, mega menü, resimli mobil menü", "rows",
  [F("style", "Biçim", "sel", opt=["klasik", "mega menü", "ortalı", "yan çekmece"], d="klasik"),
   F("mobile_img", "Mobil menüde kategori resmi", "sw", d=True, m=True),
   F("sticky", "Kaydırınca üstte kalsın", "sw", d=True), F("shrink", "Kaydırınca küçülsün", "sw", d=True),
   F("search", "Arama kutusu", "sw", d=False), F("cart", "Sepet ve hesap ikonu", "sw", d=False)] + STYLE, tags=["hazir"])
B("logo_bolum", "yapi", "Logo bölümü", "Konum, boyut, davranış", "logos",
  [F("img", "Logo", "img"), F("pos", "Konum", "sel", opt=["sol", "orta"], d="sol"),
   F("size", "Boyut", "slider", min=24, max=96, d=40), F("size_m", "Telefonda boyut", "slider", min=20, max=72, d=32, m=True),
   F("only", "Yalnız logo (yazı olmasın)", "sw", d=False)] + STYLE, tags=["hazir"])
B("story", "yapi", "Story alanı", "Instagram tarzı daireler", "g5",
  [F("source", "Neler görünsün", "sel", opt=["ürün", "kampanya", "video", "fotoğraf", "karışık"], d="karışık"),
   F("items", "İçerikler", "imgs"), F("ring", "Renkli halka", "sw", d=True), F("auto", "Kendiliğinden ilerlesin", "sw", d=True)] + STYLE,
  tags=["hazir", "hareket"])
B("site_arama", "yapi", "Site içi arama ve filtre", "Arama, filtre ve sıralama", "form",
  [F("ph", "Arama kutusu yazısı"), F("scope", "Nerede arasın", "sel", opt=["ürün", "hizmet", "yazı", "hepsi"], d="hepsi"),
   F("filters", "Filtreler", "area"), F("sort", "Sıralama seçenekleri", "area"), F("empty", "Sonuç yok yazısı")] + STYLE, tags=["hazir"])
B("sosyal", "yapi", "Sosyal medya", "Hesaplar ve akış", "logos",
  [F("items", "Hesaplar", "area"), F("style", "Biçim", "sel", opt=["ikon", "kart", "akış"], d="ikon")] + STYLE, tags=["hazir"])
B("dil", "yapi", "Dil seçici", "Çoklu dil", "band",
  [F("langs", "Diller", "area", d="Türkçe, English"), F("style", "Biçim", "sel", opt=["bayrak", "kısaltma", "liste"], d="kısaltma"),
   F("auto", "Ziyaretçinin diline göre açılsın", "sw", d=True)] + STYLE, tags=["hazir"])
B("cerez", "yapi", "Çerez politikası bandı", "Tek tuşla aktif", "band",
  [F("text", "Metin", "area"), F("accept", "Kabul yazısı", "text", d="Kabul et"), F("reject", "Reddet yazısı"),
   F("link", "Politika sayfası", "link"), F("pos", "Konum", "sel", opt=["alt", "üst", "ortada pencere"], d="alt")] + STYLE,
  tags=["hazir", "panel"], manage="Ayarlar › Yasal")
B("qr_menu", "yapi", "QR menü", "Masadaki kareyi okutan müşteri menüyü telefonunda görür", "g3",
  [F("title", "Menü başlığı", "text", d="Menü"),
   F("note", "Masadaki yazı", "area", hint="Kareyi kamerayla okutun"),
   F("source", "Menü içeriği", "sel", opt=["ürünler", "elle"], d="ürünler"),
   F("items", "Elle menü (bölüm | ürün | fiyat)", "area"),
   F("tables", "Masa sayısı", "num", d=12), F("order", "Masadan sipariş alınsın", "sw", d=False),
   F("call", "Garson çağır düğmesi", "sw", d=True), F("langs", "Menü dilleri", "area"),
   F("photo", "Ürün görselleri", "sw", d=True), F("price", "Fiyatları göster", "sw", d=True),
   F("allergen", "Alerjen / içerik notu", "sw", d=False),
   F("print", "Masa karekodlarını yazdır", "sw", d=True)] + STYLE,
  tags=["hazir", "sektorel", "panel"], sectors=["lokanta", "kafe", "otel", "pastane"], manage="QR menü", needs=["qr"])

# ---- Sektörel ----------------------------------------------------------------
B("menu_karti", "sektorel", "Menü / fiyat kartı", "Restoran ve kafe", "rows", TEXTS(cta=False) + STYLE,
  tags=["sektorel", "panel"], sectors=["lokanta", "kafe", "pastane"], manage="Ayarlar › Hizmetler")
B("rezervasyon", "sektorel", "Rezervasyon", "Masa ve saat seçimi", "form", TEXTS() + STYLE,
  tags=["sektorel", "panel"], sectors=["lokanta", "kafe", "otel"], manage="Randevu ayarları")
B("portfoy", "sektorel", "Portföy arama", "Emlak ilan filtresi", "form", TEXTS(cta=False) + STYLE,
  tags=["sektorel", "panel"], sectors=["emlak"], manage="Ürünler › Portföy")
B("oda", "sektorel", "Oda ve müsaitlik", "Otel ve pansiyon", "g3", TEXTS(cta=False) + LAYOUT + STYLE,
  tags=["sektorel", "panel"], sectors=["otel"], manage="Ürünler › Odalar")
B("ders_program", "sektorel", "Ders programı", "Fitness, kurs, dans", "rows", TEXTS(cta=False) + STYLE,
  tags=["sektorel", "panel"], sectors=["fitness", "kurs", "surucu"], manage="Takvim › Programlar")
B("marka_liste", "sektorel", "Servis verdiğimiz markalar", "Oto ve teknik servis", "logos", TEXTS(cta=False) + [F("imgs", "Marka logoları", "imgs")] + STYLE,
  tags=["sektorel", "panel"], sectors=["oto", "teknik", "yedek_parca"], manage="Ayarlar › Markalar")
B("calisma_alani", "sektorel", "Çalışma alanları", "Avukat ve danışmanlık", "g3", TEXTS(cta=False) + LAYOUT + STYLE,
  tags=["sektorel", "panel"], sectors=["avukat", "danisman", "mali"], manage="Ayarlar › Hizmetler")
B("bilet", "sektorel", "Bilet / kontenjan", "Etkinlik ve organizasyon", "form", TEXTS() + STYLE,
  tags=["sektorel", "panel"], sectors=["organizasyon", "kurs"], manage="Takvim › Etkinlikler")

# ---- Serbest yapı taşları ----------------------------------------------------
for _id, _n, _d, _w, _f in [
        ("s_baslik", "Başlık", "Tek satır başlık", "hero", [F("text", "Yazı"), F("size", "Boyut", "slider", min=16, max=96, d=40)]),
        ("s_yazi", "Yazı", "Serbest metin", "rows", [F("text", "Yazı", "area")]),
        ("s_resim", "Resim", "Tek görsel", "full", [F("img", "Görsel", "img"), F("cap", "Alt yazı")]),
        ("s_resim_yazi", "Resim + yazı", "Yan yana", "split", [F("img", "Görsel", "img"), F("text", "Yazı", "area")]),
        ("s_2kolon", "2 kolon", "İki sütun", "g2", [F("left", "Sol", "area"), F("right", "Sağ", "area")]),
        ("s_3kolon", "3 kolon", "Üç sütun", "g3", [F("items", "Sütunlar", "area")]),
        ("s_buton", "Buton", "Tek düğme", "cta", [F("text", "Yazı"), F("to", "Hedef", "link")]),
        ("s_ayirici", "Ayırıcı", "İnce çizgi", "band", [F("style", "Biçim", "sel", opt=["çizgi", "nokta", "boşluk"], d="çizgi")]),
        ("s_bosluk", "Boşluk", "Dikey boşluk", "band", [F("h", "Yükseklik", "slider", min=8, max=160, d=48)]),
        ("s_video", "Video", "Gömülü video", "video", [F("video", "Bağlantı")]),
        ("s_harita", "Harita", "Gömülü harita", "map", [F("adr", "Adres")]),
        ("s_kod", "HTML / kod", "Kendi kodunuz", "rows", [F("html", "Kod", "area")])]:
    B(_id, "serbest", _n, _d, _w, _f + STYLE, tags=["hazir"])

BLOCKS = _B
BY_ID = {b["id"]: b for b in BLOCKS}


# ---------------------------------------------------------------- sektör paketleri
def S(sid, name, terms, blocks, modules, integrations, reports, flow="randevu", themes=0):
    return {"id": sid, "name": name, "terms": terms, "blocks": list(blocks), "modules": list(modules),
            "integrations": list(integrations), "reports": list(reports), "flow": flow, "themes": themes}


_BASE_BLOCKS = ["hero", "hizmet_liste", "galeri", "ekip", "yorumlar", "sss", "harita", "saatler", "iletisim_form",
                "mobil_bar", "footer", "menu_gorunum", "logo_bolum", "kvkk", "cerez"]
_BASE_INT = ["google_isletme", "netgsm", "iletimerkezi", "verimor", "mutlucell", "masgsm", "whatsapp",
             "smtp", "gtm", "ga4", "search_console", "google_ads", "meta_pixel", "canli_destek", "havale", "kapida"]
_BASE_REP = ["ciro", "musteri", "personel", "kasa"]
_SHOP_BLOCKS = ["v_indirim", "v_coksatan", "v_yeni", "v_kategori", "v_marka", "v_serit", "v_buyuk_kart",
                "guvence", "odeme_logo", "taksit", "siparis_takip", "uyelik", "sepet_hatirlat", "story",
                "site_arama", "iade_kosul"]
_SHOP_MOD = ["shop", "stok", "siparis", "iade", "kampanya", "pazaryeri", "kargo", "efatura", "uyelik"]
_SHOP_INT = ["iyzico", "paytr", "param", "sipay", "craftgate", "banka_pos",
             "trendyol", "hepsiburada", "n11", "ciceksepeti", "amazon_tr", "pttavm", "pazarama",
             "idefix", "modanisa", "temu",
             "yurtici", "aras", "mng", "ptt", "surat", "ups", "sendeo", "hepsijet", "kolaygelsin",
             "parasut", "birfatura", "uyumsoft", "izibiz", "nes", "edm", "qnb_efinans", "gib_earsiv",
             "nebim", "logo", "mikro", "netsis", "dia", "akinsoft",
             "tiktok_pixel", "google_merchant", "facebook_catalog"]
_SHOP_REP = ["satis", "kar", "kanal", "iade_rapor", "stok_devir", "sepet_terk", "kampanya_etki"]

SECTOR_PACKS = {
    "kuafor": S("kuafor", "Kuaför ve güzellik", {"kisi": "Uzman", "kisiler": "Uzmanlar", "yer": "Koltuk", "is": "Randevu"},
                _BASE_BLOCKS + ["once_sonra", "paketler", "hediye_ceki", "google_yorum", "instagram"],
                ["randevu", "musteri", "kasa", "personel", "pazarlama"], _BASE_INT, _BASE_REP + ["doluluk"], "randevu", 12),
    "eticaret": S("eticaret", "E-ticaret", {"kisi": "Personel", "kisiler": "Personel", "yer": "Depo", "is": "Sipariş"},
                  _BASE_BLOCKS + _SHOP_BLOCKS, _SHOP_MOD + ["musteri", "kasa", "pazarlama"],
                  _SHOP_INT + _BASE_INT, _SHOP_REP + _BASE_REP, "siparis", 26),
    "teknik": S("teknik", "Teknik servis", {"kisi": "Usta", "kisiler": "Ustalar", "yer": "Servis", "is": "Servis kaydı"},
                _BASE_BLOCKS + ["marka_liste", "surec", "bolgeler", "geri_arama"],
                ["servis", "musteri", "kasa", "personel", "stok", "evrak"], _BASE_INT, _BASE_REP + ["servis_rapor", "garanti"], "servis", 11),
    "oto": S("oto", "Oto servis", {"kisi": "Usta", "kisiler": "Ustalar", "yer": "Lift", "is": "İş emri"},
             _BASE_BLOCKS + ["marka_liste", "surec", "once_sonra"], ["servis", "musteri", "kasa", "personel", "stok"],
             _BASE_INT, _BASE_REP + ["servis_rapor"], "servis", 10),
    "avukat": S("avukat", "Avukat ve danışmanlık", {"kisi": "Avukat", "kisiler": "Avukatlar", "yer": "Görüşme", "is": "Dosya"},
                _BASE_BLOCKS + ["calisma_alani", "blog", "basinda", "zaman"],
                ["dosya", "evrak", "durusma", "musteri", "kasa", "tahsilat"], _BASE_INT + ["uyap"],
                _BASE_REP + ["dosya_rapor", "tahsilat_rapor", "sure"], "dosya", 8),
    "veteriner": S("veteriner", "Veteriner", {"kisi": "Veteriner", "kisiler": "Veterinerler", "yer": "Oda", "is": "Muayene"},
                   _BASE_BLOCKS + ["once_sonra", "paketler", "blog"],
                   ["randevu", "hasta", "asi", "recete", "stok", "musteri", "kasa"], _BASE_INT,
                   _BASE_REP + ["hasta_rapor", "asi_rapor"], "muayene", 8),
    "lokanta": S("lokanta", "Restoran ve kafe", {"kisi": "Garson", "kisiler": "Personel", "yer": "Masa", "is": "Sipariş"},
                 _BASE_BLOCKS + ["qr_menu", "menu_karti", "rezervasyon", "instagram", "story", "dil"],
                 ["qr", "menu", "rezervasyon", "siparis", "kasa", "personel"], _BASE_INT + ["iyzico", "paytr", "yemeksepeti", "trendyol_yemek", "getir_yemek", "migros_yemek"],
                 _BASE_REP + ["masa_rapor", "menu_rapor"], "siparis", 10),
    "otel": S("otel", "Otel ve pansiyon", {"kisi": "Personel", "kisiler": "Personel", "yer": "Oda", "is": "Rezervasyon"},
              _BASE_BLOCKS + ["oda", "rezervasyon", "galeri_kayan", "dil", "uyelik"],
              ["rezervasyon", "oda", "musteri", "kasa", "personel"], _BASE_INT + ["iyzico", "paytr"],
              _BASE_REP + ["doluluk", "oda_rapor"], "rezervasyon", 9),
    "emlak": S("emlak", "Emlak", {"kisi": "Danışman", "kisiler": "Danışmanlar", "yer": "Portföy", "is": "İlan"},
               _BASE_BLOCKS + ["portfoy", "hero_search", "site_arama", "vaka"],
               ["ilan", "portfoy", "musteri", "kasa", "personel"], _BASE_INT, _BASE_REP + ["ilan_rapor"], "ilan", 8),
    "surucu": S("surucu", "Sürücü kursu", {"kisi": "Usta öğretici", "kisiler": "Usta öğreticiler", "yer": "Araç", "is": "Kursiyer"},
                _BASE_BLOCKS + ["ders_program", "surec", "sss"],
                ["kursiyer", "ders", "sinav", "evrak", "musteri", "kasa", "personel"], _BASE_INT + ["mebbis"],
                _BASE_REP + ["kursiyer_rapor", "sinav_rapor"], "kursiyer", 7),
    "kurs": S("kurs", "Kurs ve eğitim", {"kisi": "Eğitmen", "kisiler": "Eğitmenler", "yer": "Sınıf", "is": "Kayıt"},
              _BASE_BLOCKS + ["ders_program", "bilet", "blog", "uyelik"],
              ["kurs", "ogrenci", "yoklama", "musteri", "kasa", "personel"], _BASE_INT, _BASE_REP + ["ogrenci_rapor"], "kayit", 7),
    "fitness": S("fitness", "Fitness ve pilates", {"kisi": "Eğitmen", "kisiler": "Eğitmenler", "yer": "Salon", "is": "Ders"},
                 _BASE_BLOCKS + ["ders_program", "paketler", "once_sonra", "uyelik"],
                 ["randevu", "uyelik", "paket", "musteri", "kasa", "personel"], _BASE_INT, _BASE_REP + ["uyelik_rapor"], "randevu", 8),
    "saglik": S("saglik", "Diş, estetik ve sağlık", {"kisi": "Hekim", "kisiler": "Hekimler", "yer": "Oda", "is": "Randevu"},
                _BASE_BLOCKS + ["once_sonra", "surec", "sertifika", "blog"],
                ["randevu", "hasta", "tedavi", "musteri", "kasa", "personel"], _BASE_INT,
                _BASE_REP + ["hasta_rapor", "tedavi_rapor"], "muayene", 9),
    "market": S("market", "Market ve bakkal", {"kisi": "Personel", "kisiler": "Personel", "yer": "Kasa", "is": "Sipariş"},
                _BASE_BLOCKS + _SHOP_BLOCKS, _SHOP_MOD + ["musteri", "kasa"], _SHOP_INT + _BASE_INT, _SHOP_REP + _BASE_REP, "siparis", 10),
    "temizlik": S("temizlik", "Temizlik hizmetleri", {"kisi": "Ekip", "kisiler": "Ekipler", "yer": "Araç", "is": "İş"},
                  _BASE_BLOCKS + ["bolgeler", "surec", "hesaplayici"], ["randevu", "musteri", "kasa", "personel"],
                  _BASE_INT, _BASE_REP, "randevu", 7),
    "organizasyon": S("organizasyon", "Düğün ve organizasyon", {"kisi": "Danışman", "kisiler": "Danışmanlar", "yer": "Salon", "is": "Etkinlik"},
                      _BASE_BLOCKS + ["bilet", "galeri_kayan", "paketler", "vaka"],
                      ["etkinlik", "rezervasyon", "musteri", "kasa", "personel"], _BASE_INT, _BASE_REP + ["etkinlik_rapor"], "etkinlik", 8),
}


# ---------------------------------------------------------------- yardımcılar
def catalog(sector="", modules=(), allow=None):
    """Sektöre ve açık modüllere göre bölüm listesi. allow=None → hepsi."""
    mods = set(modules or ())
    out = []
    for b in BLOCKS:
        if allow is not None and b["id"] not in allow:
            continue
        if b["sectors"] != ["*"] and sector and sector not in b["sectors"] and not ("shop" in mods and ("shop" in (b["needs"] or []) or b["cat"] == "eticaret")):
            continue
        if b["needs"] and not set(b["needs"]) <= mods:
            continue
        out.append({k: b[k] for k in ("id", "cat", "name", "desc", "wire", "tags", "manage", "resp")})
    return out


def counts(rows):
    c = {}
    for r in rows:
        c[r["cat"]] = c.get(r["cat"], 0) + 1
    return c


def fields_of(bid):
    b = BY_ID.get(bid)
    return list(b["fields"]) if b else []


def defaults(bid):
    """Bölüm eklenince kullanılacak başlangıç ayarları."""
    out = {}
    for f in fields_of(bid):
        if "d" in f:
            out[f["k"]] = f["d"]
    return out


_SAFE = re.compile(r"[^0-9a-zA-Z_\-]")


def new_instance(bid):
    """Sayfaya eklenen bölümün kaydı: kendi kimliği, ayarları ve mobil ayarları."""
    if bid not in BY_ID:
        return None
    return {"iid": uuid.uuid4().hex[:10], "bid": bid, "on": True,
            "set": defaults(bid), "set_m": {}, "badges": []}


def sanitize(bid, data, mobile=False):
    """Gelen ayarları alan tanımına göre süz; tanımsız alan kaydedilmez."""
    out = {}
    for f in fields_of(bid):
        if mobile and not f.get("m") and f["t"] not in ("sel", "sw", "slider", "num"):
            continue                                   # telefona ayrı tutulmayan alan set_m'ye yazılmaz
        k = f["k"]
        if k not in data:
            continue
        v = data[k]
        t = f["t"]
        if t == "sw":
            out[k] = bool(v)
        elif t in ("num", "slider"):
            try:
                n = float(v)
            except (TypeError, ValueError):
                continue
            if "min" in f:
                n = max(n, f["min"])
            if "max" in f:
                n = min(n, f["max"])
            out[k] = int(n) if n == int(n) else n
        elif t == "sel":
            opt = [str(o) for o in (f.get("opt") or [])]
            if not opt or str(v) in opt:
                out[k] = str(v)[:120]
        elif t == "color":
            if re.fullmatch(r"#[0-9a-fA-F]{6}", str(v)):
                out[k] = str(v)
        elif t in ("imgs", "urun", "rozet"):
            if isinstance(v, list):
                out[k] = [str(x)[:300] for x in v[:60]]
        elif t == "area":
            out[k] = str(v)[:4000]
        else:
            out[k] = str(v)[:300]
    return out


def badge_list(custom=()):
    rows = [dict(b, custom=False) for b in BADGES]
    for c in (custom or [])[:20]:
        if isinstance(c, dict) and c.get("name"):
            rows.append({"id": _SAFE.sub("", str(c.get("id") or ""))[:24] or uuid.uuid4().hex[:8],
                         "name": str(c["name"])[:40],
                         "color": c.get("color") if re.fullmatch(r"#[0-9a-fA-F]{6}", str(c.get("color") or "")) else "#1c1a17",
                         "pos": c.get("pos") if c.get("pos") in BADGE_POS else "tl",
                         "motion": bool(c.get("motion")), "auto": "", "custom": True})
    return rows


def pack(sector):
    return SECTOR_PACKS.get(sector)


def pack_list():
    return [{"id": p["id"], "name": p["name"], "terms": p["terms"], "themes": p["themes"],
             "blocks": len(p["blocks"]), "modules": len(p["modules"]),
             "integrations": len(p["integrations"]), "reports": len(p["reports"]), "flow": p["flow"]}
            for p in SECTOR_PACKS.values()]


# ---------------------------------------------------------------- e-ticaret açık mı (tek yerden)
SHOP_MOD, SHOP_INT, SHOP_REP, SHOP_BLOCKS = _SHOP_MOD, _SHOP_INT, _SHOP_REP, _SHOP_BLOCKS


async def firma_modulleri(db):
    """(modüller, sektör, e-ticaret açık mı). Modüller: sahibin seçimi ya da sektör paketi.
    E-ticaret açıksa (paket 'shop' içeriyor ya da sahip firmaya 'E-ticaret' modülünü açtı)
    ürün, sipariş, kampanya, iade, pazaryeri, kargo, e-fatura ve üyelik birlikte gelir."""
    d = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
    sec = d.get("sector")
    if not sec:
        s = await db.app_settings.find_one({"_id": "sector"}, {"_id": 0}) or {}
        sec = s.get("key") or ""
    mods = d.get("modules")
    if mods is None:
        mods = list((pack(sec) or {}).get("modules") or [])
    acik = "shop" in mods
    if not acik:
        try:
            import tenant
            f = await db.main().firms.find_one({"db": tenant.current()}, {"_id": 0, "modules": 1}) if tenant.current() else None
            acik = "eticaret" in ((f or {}).get("modules") or [])
        except Exception:                                          # noqa: BLE001
            acik = False
    if acik:
        mods = list(dict.fromkeys(list(mods) + _SHOP_MOD))
    return list(mods), sec, acik
