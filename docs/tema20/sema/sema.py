# -*- coding: utf-8 -*-
import html
E_ = html.escape
CSS = """*{box-sizing:border-box;margin:0}body{font:14px/1.4 Inter,system-ui,sans-serif;background:#efede8;color:#17191d;padding:30px;width:1600px}
h1{font:800 30px Inter}.sub{color:#555;margin:6px 0 22px;font-size:15px;max-width:1100px}
.box{background:#fff;border-radius:16px;padding:22px;margin-bottom:20px}.box h2{font:800 20px Inter;margin-bottom:4px}.box>p{color:#666;margin-bottom:16px}
.fam{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.tree{border:1px solid #e4e4e0;border-radius:12px;padding:14px;background:#fbfbf9}.tree h3{font:800 16px Inter;display:flex;gap:8px;align-items:center;margin-bottom:10px}.tree h3 i{width:12px;height:12px;border-radius:50%;display:inline-block}
.n{display:block;border-radius:8px;padding:6px 10px;margin:4px 0;font-weight:600;font-size:13px;border:1.5px solid #d9dad6;background:#fff}
.n.r{background:#17191d;color:#fff;border-color:#17191d}.n.k{border-color:var(--c);background:color-mix(in srgb,var(--c) 10%,#fff)}.n.f{border-style:dashed;border-color:var(--c);color:var(--c)}
.l1{margin-left:16px;border-left:2px solid #d9dad6;padding-left:10px}.l2{margin-left:14px;border-left:2px dashed #d9dad6;padding-left:10px}
.n small{display:block;font-weight:500;color:#777;font-size:11.5px}.n.r small{color:#bbb}
.flow{display:flex;align-items:stretch;gap:0;margin:8px 0 4px;flex-wrap:nowrap}.st{flex:1;background:#fff;border:1.5px solid var(--c);border-radius:10px;padding:10px;font-size:12.5px;position:relative}.st b{display:block;color:var(--c);font-size:11px;margin-bottom:2px}
.ar{align-self:center;padding:0 6px;color:#999;font-weight:800}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:20px}.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.mm{border:1px solid #ddd;border-radius:12px;overflow:hidden}.mm .bar{background:#fff;display:flex;gap:18px;align-items:center;padding:12px 16px;border-bottom:1px solid #eee;font-weight:700;font-size:13px}.mm .bar span.on{color:#e8502b;border-bottom:2px solid #e8502b}
.mm .bar em{margin-left:auto;background:#e8502b;color:#fff;font-style:normal;padding:6px 12px;border-radius:8px}
.mm .drop{display:grid;grid-template-columns:1fr 1fr 1fr 1.2fr;gap:14px;padding:16px;background:#fff}.mm .drop div b{display:block;margin-bottom:6px;font-size:13px}.mm .drop div span{display:block;color:#555;font-size:12.5px;padding:3px 0}
.ph{background:linear-gradient(135deg,#8d939b,#c4c8cd);border-radius:8px;min-height:120px;color:#fff;font-weight:700;display:flex;align-items:flex-end;padding:10px;font-size:12px}
.mob{width:230px;border:8px solid #17191d;border-radius:28px;overflow:hidden;background:#fff;height:440px;display:flex;flex-direction:column}.mob .t{padding:10px 12px;display:flex;justify-content:space-between;font-weight:800;border-bottom:1px solid #eee}.mob .d{background:#17191d;color:#fff;flex:1;padding:14px}.mob .d span{display:block;padding:8px 0;border-bottom:1px solid #333;font-weight:600}.mob .d span small{float:right;color:#888}
.mob .bb{display:grid;grid-template-columns:1fr 1fr 1.4fr;font-size:12px;font-weight:700;text-align:center}.mob .bb span{padding:12px 0;border-top:1px solid #eee}.mob .bb span:last-child{background:#e8502b;color:#fff}
.mv{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.mv div{border:1px solid #e4e4e0;border-radius:10px;padding:12px;background:#fbfbf9}.mv b{display:block;margin-bottom:4px}.mv span{color:#666;font-size:12.5px}
table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:8px 10px;border-bottom:1px solid #eee;text-align:left;vertical-align:top}th{color:#777;font-size:12px}
.pill{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:99px;background:#e7f6ec;color:#167a3a}.pill.y{background:#fff4dc;color:#8a5a00}
.leg{display:flex;gap:16px;font-size:12px;color:#555;margin-bottom:12px}.leg span{display:flex;gap:6px;align-items:center}.leg i{width:14px;height:14px;border-radius:4px;border:1.5px solid #999;display:inline-block}"""

def tree(title, col, rows):
    def node(x):
        cls, t, s = x[0], x[1], (x[2] if len(x) > 2 else "")
        return '<span class="n %s">%s%s</span>' % (cls, E_(t), "<small>%s</small>" % E_(s) if s else "")
    out = []
    for r in rows:
        if not isinstance(r[0], tuple):
            out.append(node(r))
        else:
            head, kids = r
            out.append(node(head) + '<div class="l1">%s</div>' % "".join(node(k) if not isinstance(k[0], tuple) else node(k[0]) + '<div class="l2">%s</div>' % "".join(node(z) for z in k[1]) for k in kids))
    return '<div class="tree" style="--c:%s"><h3><i style="background:%s"></i>%s</h3>%s</div>' % (col, col, E_(title), "".join(out))

def flow(col, steps):
    return '<div class="flow" style="--c:%s">%s</div>' % (col, '<span class="ar">→</span>'.join('<div class="st"><b>%s</b>%s</div>' % (E_(a), E_(b)) for a, b in steps))

FAM = [
 tree("Servis · teklif (kombi, beyaz eşya, usta, oto, temizlik, nakliyat)", "#e8502b", [
  ("r", "Ana sayfa", "slayt giriş + arıza formu"),
  (("k", "Hizmetler", "liste, kategori filtresi"), [("", "Kombi bakımı", "her hizmetin kendi sayfası"), ("", "Kombi arıza onarımı"), ("", "Petek temizliği"), ("", "Klima montajı · bakımı"), ("f", "+ panelden eklenen her hizmet")]),
  (("k", "Bölgeler", "SEO: ilçe sayfaları"), [("", "Bornova kombi servisi"), ("f", "+ her ilçe otomatik sayfa")]),
  ("k", "Arıza bildir", "3 adımlı form → takip no"), ("k", "Servis takip", "takip no + telefon"), ("", "Hata kodları · araçlar"),
  ("f", "Yedek parça mağazası (modül açıksa)", "sepet + ödeme"), ("", "Hakkımızda · Blog · SSS · İletişim"), ("", "Yasal sayfalar (KVKK, çerez…)")]),
 tree("Randevu (kuaför, güzellik, diş, veteriner, diyet, psikolog, spor)", "#b5476b", [
  ("r", "Ana sayfa", "slayt + hızlı randevu kutusu"),
  (("k", "Hizmetler", "fiyat + süre listesi"), [("", "Hizmet detay", "öncesi/sonrası, fiyat, süre"), ("f", "+ panelden eklenen her hizmet")]),
  (("k", "Ekibimiz"), [("", "Uzman detay", "o uzmana randevu, çalıştığı günler")]),
  ("k", "Randevu al", "4 adımlı sihirbaz (aşağıda)"), ("k", "Randevularım", "SMS kodu ile giriş, iptal/değiştir"),
  ("k", "Paketler · hediye çeki", "online satın alma"), ("", "Fiyat listesi · Galeri · Blog"), ("f", "Ürün mağazası (modül açıksa)"), ("", "Hakkımızda · SSS · İletişim · Yasal")]),
 tree("E-ticaret (butik, çiçekçi, pastane, telefon aksesuar)", "#1f6feb", [
  ("r", "Ana sayfa", "kampanya slaytı, vitrinler"),
  (("k", "Kategori", "filtre: fiyat, beden, renk · sıralama"), [(("", "Ürün detay", "galeri, varyant, stok, yorumlar"), [("", "Sepet çekmecesi", "sağdan açılır")])]),
  ("k", "Sepet", "kupon, kargo hesabı"), ("k", "Ödeme", "3 adım: adres → kargo → ödeme"), ("k", "Sipariş onay", "e-posta + SMS"),
  (("k", "Hesabım"), [("", "Siparişlerim · takip · iade"), ("", "Adreslerim · favorilerim"), ("", "Giriş / kayıt / şifre")]),
  ("", "Arama (canlı öneri)"), ("", "Kampanyalar · Blog · İletişim"), ("", "Mesafeli satış, iade, KVKK")]),
 tree("Restoran · kafe · pastane siparişi", "#c0392b", [
  ("r", "Ana sayfa", "video/slayt + rezervasyon"),
  (("k", "Menü", "kategori sekmeleri, fotoğraflı"), [("", "Yemek detay", "porsiyon, ekstra seçenek")]),
  ("k", "Paket sipariş", "sepet → adres → ödeme"), ("k", "Rezervasyon", "kişi, gün, saat, not"), ("", "QR menü (masaya özel)"),
  ("", "Galeri · Hakkımızda · İletişim")]),
 tree("Emlak · ilan", "#2a9d8f", [
  ("r", "Ana sayfa", "ilan arama kutusu"),
  (("k", "İlanlar", "filtre + harita görünümü"), [("", "İlan detay", "foto galeri, özellikler, konum, görüşme randevusu")]),
  (("k", "Danışmanlar"), [("", "Danışman detay", "ilanları + randevu")]),
  ("k", "Evimi değerle", "talep formu"), ("", "Kredi hesapla · Blog · İletişim")]),
 tree("Kurs · eğitim (sürücü kursu, dil, müzik…)", "#ef4444", [
  ("r", "Ana sayfa", "dönem başlıyor sayacı"),
  (("k", "Kurslar"), [("", "Kurs detay", "ücret, süre, taksit, program")]),
  ("k", "Ön kayıt", "adım adım, evrak listesi"), ("k", "Ders / sınav takvimi"), ("", "Eğitmenler · Ücretler · SSS · İletişim")]),
]

MOTION = [("Giriş slaytı", "2–4 fotoğraf, yumuşak geçiş, oklar ve noktalar; telefonda kaydırma (Swiper)"), ("Başlık girişi", "Sayfa açılınca başlık ve butonlar bir kez belirir (GSAP)"),
          ("Sayaç", "Rakamlar ekrana gelince 0'dan sayar: 9.600 servis, 14 yıl"), ("Kayan marka şeridi", "Vaillant, Bosch… sürekli akan şerit, üzerine gelince durur"),
          ("Kart hareketi", "Üzerine gelince kart 3px yükselir, fotoğraf içeride hafif büyür"), ("Bölüm girişleri", "Kaydırdıkça 1–2 vurgu bölümü belirir; her kartta değil (göz yormaz)"),
          ("Önce / sonra", "Ortadaki tutamağı sürükleyince iki fotoğraf karşılaştırılır"), ("Galeri", "Tıklayınca tam ekran, kaydırarak geçiş"),
          ("Yorum slaytı", "Google yorumları otomatik döner"), ("Sepet çekmecesi", "Ürün eklenince sağdan kayarak açılır, sayaç zıplar"),
          ("Menü", "Masaüstünde açılır mega menü, telefonda tam ekran kayan menü"), ("Hareket azaltma", "Telefonda 'hareketi azalt' açıksa tüm animasyon kapanır")]

SRC = [("Swiper", "Slayt, galeri, yorum kaydırıcı", "MIT", "github.com/nolimits4web/swiper"), ("GSAP + ScrollTrigger", "Giriş ve kaydırma animasyonları, sayaç", "Ücretsiz, ticari kullanım serbest", "gsap.com"),
       ("Shopery HTML", "E-ticaret sayfa yapısı referansı: hesabım, sipariş geçmişi, favoriler, ödeme", "MIT", "github.com/templatecookie/shopery-html"),
       ("Open Salon", "Personel sütunlu gün takvimi, randevu fikirleri", "MIT", "github.com/clawnify/open-salon"),
       ("Kendi panelimiz", "Randevu boş saatleri, sepet, sipariş, hesabım, SMS: mevcut API'ye bağlanır", "—", "onlinekaydet panel")]

def page1():
    return '''<h1>Yeni temalar · site şeması</h1><p class="sub">Her tema çok sayfalı olacak. Panelde eklenen her hizmet, ürün, uzman ve ilan kendi sayfasını kendiliğinden alır. Koyu kutular ana sayfa, renkli kutular çalışan işlev sayfaları, kesikli kutular modül açıksa görünen sayfalar.</p>
<div class="box"><h2>1 · Sektör ailelerine göre sayfa ağacı</h2><p>20 tema bu 6 aileden birine bağlı; aynı ailedeki temalar aynı sayfaları ve işlevleri kullanır, tasarımları farklıdır.</p>
<div class="leg"><span><i style="background:#17191d;border-color:#17191d"></i>Ana sayfa</span><span><i style="border-color:#e8502b"></i>Çalışan işlev sayfası</span><span><i style="border-style:dashed;border-color:#e8502b"></i>Modül açıksa / otomatik çoğalan</span><span><i></i>Bilgi sayfası</span></div>
<div class="fam">%s</div></div>''' % "".join(FAM)

def page2():
    mm = '''<div class="mm"><div class="bar"><b style="font-size:16px">Isı Usta</b><span class="on">Hizmetler ▾</span><span>Bölgeler ▾</span><span>Servis takip</span><span>Hata kodları</span><span>Blog</span><span>İletişim</span><span style="margin-left:auto">0532 000 00 00</span><em>Arıza bildir</em></div>
<div class="drop"><div><b>Kombi</b><span>Kombi bakımı</span><span>Arıza onarımı</span><span>Kombi değişimi</span><span>Petek temizliği</span></div><div><b>Klima</b><span>Klima montajı</span><span>Klima bakımı</span><span>Gaz dolumu</span></div><div><b>Hızlı</b><span>Fiyat listesi</span><span>Servis takip</span><span>Hata kodu sorgula</span></div><div class="ph">Kampanya görseli · "Kış öncesi bakım %15"</div></div></div>'''
    mob = '''<div style="display:flex;gap:18px"><div class="mob"><div class="t">Isı Usta <span>✕</span></div><div class="d"><span>Hizmetler <small>›</small></span><span>Bölgeler <small>›</small></span><span>Servis takip</span><span>Hata kodları</span><span>Blog</span><span>İletişim</span><span style="border:0;color:#e8502b">0532 000 00 00</span></div><div class="bb"><span>Ara</span><span>WhatsApp</span><span>Arıza bildir</span></div></div>
<div class="mob"><div class="t">Atlas Butik <span>🛍 2</span></div><div class="d" style="background:#fff;color:#17191d"><span style="border-color:#eee">Keten gömlek · M <small>890 ₺</small></span><span style="border-color:#eee">Trençkot · S <small>2.490 ₺</small></span><span style="border-color:#eee">Kargo <small>Ücretsiz</small></span><span style="border:0;font-size:16px">Toplam <small style="color:#17191d;font-weight:800">3.380 ₺</small></span><span style="background:#17191d;color:#fff;text-align:center;border-radius:8px;margin-top:10px">Ödemeye geç</span></div></div></div>'''
    rdv = flow("#b5476b", [("1 · Hizmet", "Saç kesimi · 45 dk · 450 ₺"), ("2 · Uzman", "Elif, Murat ya da 'fark etmez'"), ("3 · Gün ve saat", "Yalnız boş saatler, gerçek takvimden"), ("4 · Bilgiler", "Ad, telefon → SMS kodu ile onay"), ("Onay", "SMS + takvime ekle; panelde randevu düşer")])
    sep = flow("#1f6feb", [("Ürün", "Beden/renk seç, stok kontrolü"), ("Sepet çekmecesi", "Sağdan açılır, kupon"), ("Adres", "Üyeli ya da misafir"), ("Kargo", "Ücret otomatik"), ("Ödeme", "Kart, 3D, taksit"), ("Onay", "Panelde sipariş, stok düşer, SMS")])
    srv = flow("#e8502b", [("1 · Cihaz", "Kombi / klima, marka"), ("2 · Sorun", "Hata kodu, foto yükle"), ("3 · Adres ve saat", "Uygun gün aralığı"), ("Takip no", "Panelde iş kaydı, ustaya atanır"), ("Takip", "Müşteri durumu telefondan izler")])
    return '''<div class="box"><h2>2 · Menü</h2><p>Masaüstünde açılır mega menü (hizmetler gruplu, yanında kampanya görseli). Telefonda tam ekran kayan menü ve altta sabit Ara · WhatsApp · ana işlem çubuğu. Kaydırınca üst menü küçülür ve sabit kalır.</p>%s<div style="margin-top:18px">%s</div></div>
<div class="box"><h2>3 · Çalışan akışlar (panele bağlı)</h2><p>Bu akışlar sahte değil; panelin randevu, sipariş ve iş kaydı sistemine bağlanacak.</p>
<p style="font-weight:800;margin:10px 0 0">Randevu sihirbazı</p>%s<p style="font-weight:800;margin:14px 0 0">Sepet ve ödeme</p>%s<p style="font-weight:800;margin:14px 0 0">Servis / arıza talebi</p>%s</div>
<div class="g2"><div class="box"><h2>4 · Hareketler</h2><p>Siteler canlı görünecek ama göz yormayacak.</p><div class="mv" style="grid-template-columns:1fr 1fr">%s</div></div>
<div class="box"><h2>5 · Açık kaynaktan kullanacaklarımız</h2><p>Lisansı ticari kullanıma uygun olanlar.</p><table><tr><th>Kaynak</th><th>Ne için</th><th>Lisans</th></tr>%s</table>
<h2 style="margin-top:20px">6 · Her temada</h2><p style="color:#444;margin-top:6px;line-height:1.7">• Her bölüm, yazı, fotoğraf, yazı tipi panelden düzenlenir<br>• Bölümler gizlenir, sıralanır, kütüphaneden eklenir<br>• Gerçek ücretsiz fotoğraflar (Pexels), sektörüne özel<br>• Telefon ve bilgisayarda test, her buton ve form denenir<br>• SEO: her hizmet ve ilçe ayrı sayfa, site haritası otomatik<br>• Yasal sayfalar modüle göre otomatik</p></div></div>''' % (
        mm, mob, rdv, sep, srv, "".join("<div><b>%s</b><span>%s</span></div>" % (E_(a), E_(b)) for a, b in MOTION),
        "".join('<tr><td><b>%s</b><br><small style="color:#888">%s</small></td><td>%s</td><td><span class="pill%s">%s</span></td></tr>' % (E_(a), E_(d), E_(b), "" if c != "—" else " y", E_(c if c != "—" else "bizde var")) for a, b, c, d in SRC))

for k, body in ((1, page1()), (2, page2())):
    open("sema%d.html" % k, "w", encoding="utf-8").write('<!doctype html><html lang="tr"><meta charset="utf-8"><style>%s</style><body>%s</body></html>' % (CSS, body))
