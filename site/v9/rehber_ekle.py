# -*- coding: utf-8 -*-
"""Bilgi bankasına yeni rehberler ekler (restoran menüsü, yemek siparişleri, etiket, entegrasyon, alan adı), tüm rehber
sayfalarının "Diğer rehberler" listesini, bilgi-bankasi.html kartlarını ve Destek merkezini (destek.html) yeniden kurar.
Çalıştır: python3 site/v9/rehber_ekle.py   (depo kökünden)"""
import re, os, json, html
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
def rd(n): return open(os.path.join(S, n), encoding="utf-8").read()
def wr(n, t):
    if n.startswith("bilgi-") and n != "bilgi-bankasi.html" and "aria-current" not in t:
        t = t.replace('<a href="/bilgi-bankasi.html">Bilgi bankası</a></nav>', '<a href="/bilgi-bankasi.html" aria-current="page">Bilgi bankası</a></nav>', 1)
    open(os.path.join(S, n), "w", encoding="utf-8").write(t)
E = html.escape

def steps(items):
    o = '<ol class="steps">'
    for it in items:
        b, t = it[0], it[1]
        f = ""
        if len(it) > 2:
            f = '<figure class="bf"><img src="/v9/img/bilgi/%s.webp" width="1000" height="601" alt="%s" loading="lazy"><figcaption>%s</figcaption></figure>' % (it[2], E(it[3]), E(it[3]))
        o += '<li><b>%s</b>%s%s</li>' % (b, t, f)
    return o + '</ol>'
def tip(t): return '<div class="ipuc"><b>İpucu:</b> %s</div>' % t

NEW = [
 dict(slug="bilgi-yemek-menusu", tag="Restoran", title="Restoran menüsü nasıl hazırlanır?",
  desc="Yemekleri ekleyin; menü bölümü, alerjen ve seçenek gruplarını girin. Menü sitenizde ve QR menüde görünür.",
  card="Yemek ekleyin, alerjen ve seçenek gruplarını girin; menü sitenizde ve QR menüde görünür.",
  body='<p>Restoran, kafe, lokanta ve pastane hesaplarında Ürünler ekranı “Menü” adını alır ve her yemeğin kartında “Yemek bilgileri” bölümü açılır. Mağaza hesaplarında bu bölüm ve restoran ekranları hiç görünmez.</p>'
   '<h2>Yemek ekleme</h2>' + steps([
    ("Soldaki menüden “Menü”yü açın", "“Yemek ekle” düğmesine basın.", "y_menu", "Menü ekranı: yemekler, fiyat, durum ve “Yemek ekle” düğmesi"),
    ("Ad, açıklama, fiyat ve fotoğrafı girin", "Yemeğin adı menüde ve platformlarda aynen görünür. Pazaryerinde zaten satılan bir yemeği eşleştirecekseniz adı aynı yazın."),
    ("“Yemek bilgileri”ni doldurun", "Menü bölümü (örn. Kebaplar, İçecekler), hazırlık süresi (dakika), porsiyon, kalori, acılık (Acı değil, Az acı, Orta, Çok acı) ve çıkarılabilir malzemeler. Vejetaryen ve Vegan kutularını uygunsa işaretleyin.", "y_yemekbilgi", "Ürün kartındaki “Yemek bilgileri” bölümü"),
    ("Alerjenleri işaretleyin", "Listeden yemekte bulunan alerjenleri seçin; menü dosyasına ve platform bilgisine yazılır."),
    ("Seçenek gruplarını ekleyin", "Örnek: “Yan ürün” grubu, en az 1 en çok 1 seçim; Pilav 0 ₺, Salata +15 ₺. Zorunlu bir grupta 0 ₺ olan en az bir seçenek bulunmalıdır; yoksa kayıt reddedilir ve nedeni yazılır."),
    ("Satış kanallarını seçip kaydedin", "“Platformlarda satışta” kutusu kapalıysa yemek platformlarda ve sitenizde görünmez; menüden kaldırmadan geçici olarak kapatmak için kullanılır.")]) +
   '<h2>Menü sitenizde nerede görünür?</h2><p>Satışta olan yemekler sitenizin menü kartlarında ve QR menüde, “Menü bölümü” başlıkları altında listelenir. Taslak durumundaki ve satışa kapattığınız yemekler görünmez. Fiyatı ya da fotoğrafı panelde değiştirdiğinizde site de güncellenir.</p>'
   + tip("QR menü kartını masalarınıza yerleştirmek için Etiket tasarımı ekranındaki “QR menü kartı” sekmesini kullanın.")),
 dict(slug="bilgi-menu-pazaryerine-gonderme", tag="Restoran", title="Menü Yemeksepeti, Trendyol, Getir ve Migros’a nasıl gönderilir?",
  desc="Menüyü pazaryerine gönderme ekranı: Trendyol Yemek’te fiyat ve satış durumu, diğer platformlar için menü dosyası.",
  card="Trendyol Yemek’e fiyat ve satış durumunu gönderin; diğer platformlar için menü dosyasını indirin.",
  body='<p>Yemek platformlarının her biri menü bilgisini farklı bir yoldan kabul eder. Panel, platformun izin verdiği yolu kullanır ve hangisinin ne yaptığını ekranda açıkça yazar. Ekran, “Menüyü pazaryerine gönder” adıyla Menü’nün yanındadır.</p>'
   '<h2>Trendyol Yemek</h2>' + steps([
    ("Entegrasyonlar ekranından Trendyol Yemek’i bağlayın", "Trendyol Yemek hesabınızdan aldığınız bilgileri ve mağaza numarasını girin; bağlantı denenir, başarılıysa “Bağlı” görünür."),
    ("“Menüyü pazaryerine gönder”i açın, Trendyol Yemek sekmesini seçin", "Tabloda her yemeğin panel fiyatı, platformdaki fiyatı, satış durumu ve durumu (Aynı, Farklı, Platformda yok) yan yana görünür.", "y_gonder", "Menüyü pazaryerine gönder ekranı: fark olanlar işaretlenir"),
    ("“Farkları gönder”e basın", "Yalnız fiyatı ya da satış durumu değişen yemekler gönderilir; aynı olanlara dokunulmaz.")]) +
   '<p>Trendyol’un servisi yeni yemek açmaz. Yemeği önce Trendyol Yemek satıcı panelinde açın; adı panelle aynıysa burada kendiliğinden eşleşir, değilse “Platformda yok” görünür.</p>'
   '<h2>Yemeksepeti, Getir Yemek ve Migros Yemek</h2><p>Bu platformlar menü servisini herkese açık yayımlamıyor. İlgili sekmede “Menü dosyasını indir (CSV)” düğmesi çıkar. Dosyada bölüm, ad, açıklama, fiyat, KDV, görsel, hazırlık süresi, alerjen, seçenek grupları ve satış durumu bulunur; dosyayı platformun satıcı panelinden yüklersiniz.</p>'
   + tip("Fiyatı panelde değiştirince hangi platformlarda fark oluştuğunu bu ekran gösterir; gönderim yapılmadan platformdaki fiyat değişmez.")),
 dict(slug="bilgi-yemek-siparisleri", tag="Restoran", title="Yemek siparişleri panele nasıl düşer?",
  desc="Yemeksepeti, Trendyol Yemek, Getir Yemek ve Migros Yemek bağlantısı; siparişler listeye kendiliğinden düşer ve uyarı verir.",
  card="Platformları bağlayın; siparişler kendiliğinden listeye düşer, yenisi gelince uyarı verir.",
  body='<p>Yemek platformlarından gelen siparişler, telefon ve site siparişleriyle aynı Siparişler listesinde toplanır. Siparişleri elle girmeniz ya da sayfayı yenilemeniz gerekmez.</p>'
   '<h2>Platformu bağlama</h2>' + steps([
    ("Entegrasyonlar ekranını açın", "“Yemek platformu” grubunda Yemeksepeti, Trendyol Yemek, Getir Yemek ve Migros Yemek kartları vardır.", "g_ent", "Entegrasyonlar ekranı: türler, durum ve arama"),
    ("Kartı açıp bilgileri girin", "Yemeksepeti için kendi belirlediğiniz bildirim anahtarını (Yemeksepeti’ne verdiğiniz bildirim adresinde kullanılır), durum bildirmek için erişim anahtarını ve isterseniz komisyon oranını girin. Diğer platformlarda platformun size verdiği erişim bilgileri istenir. Yemeksepeti, Getir ve Migros entegrasyon erişimini platformun kendisi verir."),
    ("Bağlantıyı deneyin", "Kayıt sırasında bağlantı denenir; çalışmıyorsa sebebi kartta yazılır, “Bağlı” yazısı yalnız deneme başarılıysa çıkar.")]) +
   '<h2>Siparişler nasıl gelir?</h2><ol class="steps"><li><b>Yemeksepeti</b>Platform her siparişi bildirim olarak gönderir; sipariş anında listenize düşer.</li><li><b>Trendyol, Getir ve Migros</b>Panel siparişleri bir iki dakikada bir platformdan çeker. Bağlantıyı açtığınız andan sonraki siparişler gelir; eski siparişler listeyi doldurmaz.</li><li><b>Siparişler ekranı açıkken</b>Liste yarım dakikada bir kendiliğinden kontrol edilir. Yeni sipariş gelince ekranda uyarı çıkar, kısa bir ses çalar ve liste yenilenir.<figure class="bf"><img src="/v9/img/bilgi/y_siparis.webp" width="1000" height="601" alt="Siparişler: platform siparişleri aynı listede" loading="lazy"><figcaption>Siparişler: telefon ve platform siparişleri aynı listede</figcaption></figure></li></ol>'
   + tip("Komisyon oranını girerseniz kâr hesabı platform komisyonunu da düşer.")),
 dict(slug="bilgi-etiket-tasarimi", tag="Mağaza ve restoran", title="Kargo etiketi, kargo şablonu ve QR menü kartı nasıl tasarlanır?",
  desc="Etiket tasarımı ekranında stil seçin, renk ve yazıları değiştirin, canlı önizlemeyi görüp yazdırın. Firma bilgisi ve logo otomatik gelir.",
  card="Stil seçin, renk ve yazıyı değiştirin, yandan canlı görün, yazdırın.",
  body='<p>“Etiket tasarımı” ekranı üç şey hazırlar: kargo etiketi, kargo şablonu (fiş) ve restoran hesaplarında QR menü kartı. Firma adınız, telefonunuz, adresiniz ve logonuz yönetici tarafından bir kez tanımlanır; tanımlanınca her etikete kendiliğinden gelir. QR menü kartı yalnız restoran, kafe, lokanta ve pastane hesaplarında görünür.</p>'
   '<h2>Tasarlama</h2>' + steps([
    ("Üstteki sekmelerden birini seçin", "Kargo etiketi, kargo şablonu ya da (restoran hesaplarında) QR menü kartı."),
    ("Bir stil seçin", "Stil küçük resimleri gerçek veriyle çizilmiş örneklerdir; seçtiğiniz stil yandaki canlı önizlemeye hemen yansır.", "e_etiket", "Etiket tasarımı: stil seçimi ve canlı önizleme"),
    ("Gösterilecek alanları işaretleyin", "Kargo etiketinde logo, telefon, adres, barkod, içerik-tutar-ödeme ve sipariş notu; kargo şablonunda logo, telefon, adres ve imza alanı; QR kartında logo, firma adı, masa numarası, bağlantı yazısı ve kesim çizgisi."),
    ("Yazıları, boyutu ve yazı tipini ayarlayın", "Alt yazı gibi kısa metinleri düzenleyin; QR kartında başlık, açıklama ve alt satır (örn. Wi-Fi şifresi) vardır. QR kartında masa sayısını da yazarsınız.", "e_qr", "Restoran QR menü kartı: masa numaralı kartlar"),
    ("Kaydedin ve yazdırın", "Kaydedilen tasarım bir dahaki sefere hazır gelir. Yazdırdığınızda gerçek siparişlerinizin ya da masalarınızın verisiyle çıkar.")]) +
   tip("Hangi sekmenin hangi ekranda kullanıldığını merak ediyorsanız: kargo etiketi sipariş kargoya verilirken, QR menü kartı masalara konmak üzere yazdırılır.")),
 dict(slug="bilgi-entegrasyon-baglama", tag="Ayarlar", title="Entegrasyon nasıl bağlanır?",
  desc="Pazaryeri, kargo, ödeme, e-fatura, SMS ve ölçüm araçlarını bağlama: anahtarı girin, bağlantıyı deneyin, durumu görün.",
  card="Anahtarınızı girin, bağlantıyı deneyin; durum ve hata sebebi ekranda görünür.",
  body='<p>Entegrasyonlar ekranı tüm bağlantıları tek yerde toplar. Anahtarlarınızı siz girersiniz; panel bağlantıyı denemeden “Bağlı” yazmaz, hata varsa sebebini gösterir.</p>'
   '<h2>Bağlama adımları</h2>' + steps([
    ("Entegrasyonlar ekranını açın", "Üstteki kartlar türlere ayrılır: ödeme, kargo, e-fatura, ERP, SMS, pazaryeri, yemek platformu, ölçüm ve diğer. Her kartta kaç tanesinin bağlı olduğu yazar.", "g_ent", "Entegrasyonlar ekranı"),
    ("Entegrasyonu bulun", "Arama kutusuna adını yazın (örn. iyzico, Aras, Paraşüt, Nebim) ya da türü seçin. “Bağlı”, “Hata”, “Bağlı değil” düğmeleriyle süzebilirsiniz."),
    ("Bilgileri girip kaydedin", "Her entegrasyonun kendi alanları vardır (anahtar, gizli anahtar, mağaza numarası gibi); gizli alanlar kayıttan sonra gösterilmez."),
    ("Bağlantıyı deneyin", "Kayıtta bağlantı denenir. “Bağlantıları dene” düğmesi hepsini yeniden dener. Çalışmayanın sebebi kartında yazar."),
    ("İşlem kaydına bakın", "“İşlem kaydı” hangi bağlantıda ne zaman ne olduğunu listeler.")]) +
   '<p>Her entegrasyonun neleri yaptığı ve desteklenenlerin tam listesi için <a href="/entegrasyonlar.html">Entegrasyonlar</a> sayfasına bakın.</p>'),
 dict(slug="bilgi-alan-adi", tag="Web sitesi", title="Kendi alan adınızı siteye nasıl bağlarsınız?",
  desc="Alan adını ekleyin, DNS kayıtlarını girin, Kontrol et deyin; site kendi adresinizde yayında olsun.",
  card="Alan adını ekleyin, DNS kaydını girin, kontrol edin; siteniz kendi adresinizde açılır.",
  body='<p>Sitenizi kendi alan adınızla (örn. firmaadi.com) yayınlamak için yalnız DNS kayıtlarını girersiniz; kalanı otomatik olur.</p>'
   '<h2>Bağlama adımları</h2>' + steps([
    ("Alan adı ekranını açın", "“Alan adı ekle” kutusuna adı yazın. www ya da http:// ile yazsanız da olur. En fazla 5 alan adı bağlanır.", "a_alan", "Alan adı ekranı ve DNS kayıtları"),
    ("DNS kayıtlarını girin", "Ekle’ye bastığınızda ekranda girmeniz gereken DNS kayıtları listelenir. Bunları alan adını aldığınız firmanın DNS ekranına girin."),
    ("Birkaç dakika bekleyip “Kontrol et”e basın", "Kayıtlar doğruysa durum “Yayında” olur. Henüz yönlenmiyorsa hangi adresin doğru, hangisinin eksik olduğu yazılır."),
    ("Siteyi açın", "Bağlanan alan adının yanındaki bağlantıdan siteyi görürsünüz; “Kaldır” ile bağlantıyı kaldırabilirsiniz.")]) +
   tip("DNS değişikliğinin yayılması bazen birkaç saat sürebilir. Kontrol et ilk seferde olumsuz dönerse bir süre sonra yeniden deneyin.")),
]
ORDER = [("Mağaza", ["bilgi-urun-ekleme", "bilgi-pazaryerine-gonderme", "bilgi-xml-ile-urun-aktarma", "bilgi-siparis-ve-kargo", "bilgi-etiket-tasarimi"]),
         ("Restoran", ["bilgi-yemek-menusu", "bilgi-menu-pazaryerine-gonderme", "bilgi-yemek-siparisleri"]),
         ("İş takibi", ["bilgi-randevu-ve-takvim", "bilgi-musteri-yonetimi", "bilgi-kasa-ve-muhasebe", "bilgi-personel-ve-prim"]),
         ("Web sitesi", ["bilgi-ilan-ekleme", "bilgi-web-sitesi-duzenleme", "bilgi-alan-adi"]),
         ("Ayarlar", ["bilgi-entegrasyon-baglama"]), ("Başlangıç", ["bilgi-baslangic"])]

# mevcut rehberlerin başlık/kart bilgisi: bilgi-bankasi.html kartlarından
bb = rd("bilgi-bankasi.html")
INFO = {}
for m in re.finditer(r'<a href="/(bilgi-[a-z-]+)\.html">(<div class="bkim">.*?</div>)?<span>([^<]*)</span><h3>([^<]*)</h3><p>([^<]*)</p></a>', bb):
    INFO[m.group(1)] = dict(slug=m.group(1), img=m.group(2) or "", tag=m.group(3), title=html.unescape(m.group(4)), card=html.unescape(m.group(5)))
CARDIMG = {"bilgi-yemek-menusu": "y_menu", "bilgi-menu-pazaryerine-gonderme": "y_gonder", "bilgi-yemek-siparisleri": "y_siparis", "bilgi-etiket-tasarimi": "e_etiket", "bilgi-entegrasyon-baglama": "g_ent", "bilgi-alan-adi": "a_alan"}
for g in NEW: INFO[g["slug"]] = dict(slug=g["slug"], img='<div class="bkim"><img src="/v9/img/bilgi/%s.webp" alt="" loading="lazy"></div>' % CARDIMG[g["slug"]], tag=g["tag"], title=g["title"], card=g["card"])
INFO["bilgi-menu-pazaryerine-gonderme"]["tag"] = "Restoran"
TAGFIX = {"bilgi-urun-ekleme": "Mağaza", "bilgi-pazaryerine-gonderme": "Mağaza", "bilgi-xml-ile-urun-aktarma": "Mağaza", "bilgi-siparis-ve-kargo": "Mağaza"}

def cards(ex=None):
    o = ""
    for _, sl in ORDER:
        for s in sl:
            if s not in INFO: continue
            i = INFO[s]
            o += '<a href="/%s.html">%s<span>%s</span><h3>%s</h3><p>%s</p></a>' % (s, i["img"], E(i["tag"]), E(i["title"]), E(i["card"]))
    return o
def others(self_slug):
    return '<div class="bk2">' + "".join('<a href="/%s.html">%s</a>' % (s, E(INFO[s]["title"])) for _, sl in ORDER for s in sl if s in INFO and s != self_slug) + '</div>'

def retitle(h, title, desc, slug, old):
    h = re.sub(r"<title>.*?</title>", "<title>%s | Bilgi Bankası | OnlineKaydet</title>" % E(title), h, 1, flags=re.S)
    h = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + E(desc, True), h, 1)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + E(title) + " | Bilgi Bankası | OnlineKaydet", h, 1)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + E(desc, True), h, 1)
    h = h.replace(old, slug)
    h = re.sub(r'("@type": "HowTo", "name": ")[^"]*(", "description": ")[^"]*', lambda m: m.group(1) + title.replace('"', '') + m.group(2) + desc.replace('"', ''), h, 1)
    return h

shell = rd("bilgi-pazaryerine-gonderme.html")
OLD = "bilgi-pazaryerine-gonderme"
def split_main(h):
    a = h.index('<section class="sec"><div class="w"><div class="yz">'); b = h.index('<section class="sec"><div class="w"><h2 style="margin-top:0">Diğer rehberler</h2>')
    return a, b
for g in NEW:
    h = retitle(shell, g["title"], g["desc"], g["slug"], OLD)
    # sayfa başlığı bloğu
    h = re.sub(r'<p class="kr">.*?</p><h1>.*?</h1><p class="lead">.*?</p>',
               '<p class="kr"><a href="/">Ana sayfa</a> / <a href="/bilgi-bankasi.html">Bilgi bankası</a> / %s</p><h1>%s</h1><p class="lead">%s</p>' % (E(g["tag"]), E(g["title"]), E(g["desc"])), h, 1, flags=re.S)
    a, b = split_main(h)
    h = h[:a] + '<section class="sec"><div class="w"><div class="yz">' + g["body"] + '</div></div></section>' + h[b:]
    h = re.sub(r'<div class="bk2">.*?</div>', lambda m: others(g["slug"]), h, 1, flags=re.S)
    wr(g["slug"] + ".html", h); print("yazıldı", g["slug"])
# eski rehberlerin "Diğer rehberler" listesi
for _, sl in ORDER:
    for s in sl:
        if s in [g["slug"] for g in NEW] or not os.path.exists(os.path.join(S, s + ".html")): continue
        h = rd(s + ".html")
        h2 = re.sub(r'<div class="bk2">.*?</div>', lambda m: others(s), h, 1, flags=re.S)
        if h2 != h: wr(s + ".html", h2)
# bilgi-bankasi kartları
h = re.sub(r'<div class="bk">.*?</div></div></section>', lambda m: '<div class="bk">' + cards() + '</div></div></section>', bb, 1, flags=re.S)
wr("bilgi-bankasi.html", h)

# Destek merkezi
dk = rd("destek.html"); shell2 = rd("bilgi-bankasi.html")
faq = [
 ("Kurulum için teknik bilgi gerekir mi?", "Hayır. Kurulumu biz yaparız; firma bilgilerinizi göndermeniz yeterli."),
 ("İlk ay gerçekten ücretsiz mi?", "Evet. Kurulum ve veri aktarımı da bu süreye dahil."),
 ("Ürünü nasıl eklerim, pazaryerine nasıl gönderirim?", "Ürünler ekranından tek tek ya da Excel ve XML ile eklersiniz; seçip “Pazaryerlerine gönder” dersiniz. Adım adım anlatım yukarıdaki rehberlerde."),
 ("Restoranım için menüyü Yemeksepeti, Trendyol, Getir ve Migros’a gönderebilir miyim?", "Trendyol Yemek’e fiyat ve satış durumu panelden gider; diğer platformlar için menü dosyasını indirip satıcı panelinden yüklersiniz. Siparişler dördünden de panele düşer."),
 ("Yemek siparişleri kendiliğinden geliyor mu?", "Evet. Platform bağlandıktan sonra siparişler listeye kendiliğinden düşer; Siparişler ekranı açıkken yeni sipariş uyarı ve sesle bildirilir."),
 ("E-ticaret ve restoran ekranları herkeste görünür mü?", "Hayır. Restoran ekranları yalnız restoran, kafe, lokanta ve pastane hesaplarında, mağaza ekranları e-ticaret yapan hesaplarda görünür."),
 ("Müşteriye SMS gidiyor mu?", "Randevu, usta yolda ve servis tamamlandı adımlarında otomatik SMS gider. Kendi SMS sağlayıcı hesabınızı bağlarsınız."),
 ("Mevcut kayıtlarımı taşıyabilir miyim?", "Excel veya defter kayıtlarınızı biz aktarırız."),
 ("Şifremi unuttum, ne yapmalıyım?", "Giriş ekranından şifre yenileyebilir ya da bizi arayabilirsiniz."),
 ("Fiş biçimini ve etiketleri değiştirebilir miyim?", "Evet. Fişi Servis Ayarları’ndan, kargo etiketini ve QR menü kartını Etiket tasarımı ekranından düzenlersiniz."),
]
main = ('<main><section class="pb" id="icerik"><div class="w"><div><p class="kr"><a href="/">Ana sayfa</a> / Destek</p><h1>Destek ve rehberler</h1>'
  '<p class="lead">Önce aşağıdaki adım adım rehberlere bakın; ürün eklemeden pazaryerine, restoran menüsünden etikete her işlem var. Bulamazsanız bize yazın ya da arayın.</p>'
  '<div class="cta"><a class="btn fil" href="tel:+905444444004">Hemen arayın</a><a class="btn bos" href="https://wa.me/905444444004" rel="noopener" target="_blank">WhatsApp’tan yazın</a><a class="btn duz" href="#sss">Sık sorulan sorular</a></div></div></div></section>'
  '<section class="sec"><div class="w"><form action="/ara.html" role="search" class="araf araf2"><input type="search" name="q" placeholder="Rehberlerde ara: ürün ekleme, Trendyol, menü, etiket…" aria-label="Destekte ara"><button class="btn dolu" type="submit">Ara</button></form>'
  '<div class="bk">' + cards() + '</div></div></section>'
  '<section class="sec sss" id="sss"><div class="w g"><div class="b1"><p class="et">Sık sorulanlar</p><h2>Sık sorulan sorular</h2></div><div class="lst">' +
  "".join('<div class="q%s"><h3>%s</h3><p>%s</p></div>' % (" ac" if i == 0 else "", E(q), E(a)) for i, (q, a) in enumerate(faq)) + '</div></div></section>'
  '<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Hâlâ takıldınız mı?</h2><p>Ekran görüntüsüyle birlikte WhatsApp’tan yazın ya da telefonla arayın; kurulum ve kullanım sorularına yardımcı oluruz.</p><p><a class="btn dolu" href="tel:+905444444004">Hemen arayın</a> <a class="btn bos2" href="/iletisim.html#teklif">Teklif alın</a></p></div></div></section>')
a = shell2.index("<main>"); b = shell2.index('<section class="son" id="teklif">')
h = shell2[:a] + main + shell2[b:]
h = re.sub(r"<title>.*?</title>", "<title>Destek ve Rehberler | OnlineKaydet</title>", h, 1, flags=re.S)
dsc = "Ürün ekleme, pazaryeri, restoran menüsü, yemek siparişleri, etiket, entegrasyon ve alan adı rehberleri; sık sorulan sorular ve iletişim."
h = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + dsc, h, 1)
h = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + dsc, h, 1)
h = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + "Destek ve Rehberler | OnlineKaydet", h, 1)
h = h.replace("bilgi-bankasi.html\">Bilgi bankası</a><a class=\"m\"", "bilgi-bankasi.html\">Bilgi bankası</a><a class=\"m\"")
h = h.replace('href="https://onlinekaydet.com/bilgi-bankasi.html"', 'href="https://onlinekaydet.com/destek.html"').replace('content="https://onlinekaydet.com/bilgi-bankasi.html"', 'content="https://onlinekaydet.com/destek.html"')
h = re.sub(r'<script type="application/ld\+json">.*?</script>', '', h, flags=re.S) if False else h
wr("destek.html", h)

# site içi arama
aj = os.path.join(S, "v9", "arama.json")
try:
    L = json.load(open(aj, encoding="utf-8"))
    have = {x["u"] for x in L}
    for g in NEW:
        u = "/%s.html" % g["slug"]
        if u not in have: L.append({"u": u, "t": g["title"], "d": g["desc"]})
    json.dump(L, open(aj, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
except Exception as e: print("arama.json", e)
sm = os.path.join(S, "sitemap.xml")
if os.path.exists(sm):
    t = open(sm, encoding="utf-8").read()
    for g in NEW:
        u = "https://onlinekaydet.com/%s.html" % g["slug"]
        if u not in t: t = t.replace("</urlset>", "<url><loc>%s</loc></url>\n</urlset>" % u)
    open(sm, "w", encoding="utf-8").write(t)
print("bitti")
