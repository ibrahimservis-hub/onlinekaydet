# -*- coding: utf-8 -*-
"""20 yeni tema şablon panosu (onay için): tel kafes çizimleri -> PNG."""
import html, json
# bölüm tipleri: hf=tam fotoğraf giriş, hs=yarım foto giriş, hq=giriş+teklif formu, hb=giriş+randevu kutusu, hp=ürün vitrinli giriş,
# c3=3 kart, c4=4 kart, sv=hizmet listesi+fiyat, pr=ürün ızgarası, cat=kategori kutuları, bk=randevu takvimi, qf=teklif formu, gl=galeri,
# tm=ekip, pk=paket/fiyat tablosu, st=adım adım, nm=rakamlar, rv=yorumlar, fq=sss, mp=harita+iletişim, ba=önce/sonra, mn=menü, il=ilan ızgarası,
# cl=hesaplayıcı/araç, bl=blog, cta=çağrı bandı, br=marka şeridi, tr=takip sorgu, kr=kurs takvimi
T = [
 # --- SERVİS / TEKLİF ---
 ("Isı Usta", "Kombi · Klima servisi", "servis", ["#0f2a3d", "#e8502b", "#f4efe8"], "Archivo / Inter",
  ["hq:Giriş + 'Arıza bildir' formu (marka, sorun, telefon)", "br:Servis verilen markalar", "sv:Hizmetler + başlangıç fiyatı", "cl:Kombi hata kodu sorgulama", "st:4 adımda servis", "nm:Yıl, servis sayısı, ilçe", "gl:Atölye ve saha fotoğrafları", "rv:Müşteri yorumları", "fq:Sık sorulanlar", "mp:Servis bölgeleri + harita"],
  ["Hizmetler", "Hizmet detayı (her hizmet)", "Hata kodları", "Servis takip", "Bölgeler", "İletişim"],
  ["Arıza/servis talebi → panele iş kaydı", "Servis takip no ile durum sorgulama", "Online randevu saati", "Yedek parça mini mağaza (sepet+ödeme)", "WhatsApp + ara butonu"],
  "kombi tamiri, teknisyen, kalorifer peteği, klima montajı"),
 ("Beyaz Servis", "Beyaz eşya servisi", "servis", ["#112b3c", "#1f9d8b", "#f2f6f5"], "Manrope / Manrope",
  ["hs:Yarım foto giriş + 'Hangi cihaz?' seçici", "c4:Cihaz kartları (çamaşır, bulaşık, buzdolabı, fırın)", "qf:Hızlı servis talebi", "st:Nasıl çalışıyoruz", "cl:Tamir mi yeni mi hesaplayıcı", "pk:Bakım paketleri", "rv:Yorumlar", "fq:SSS", "mp:İletişim"],
  ["Cihazlar", "Cihaz detay", "Bakım paketleri", "Servis takip", "İletişim"],
  ["Servis talebi → iş kaydı", "Servis takip", "Bakım paketi satın al (ödeme)", "Randevu saati"],
  "çamaşır makinesi tamiri, buzdolabı, teknisyen çanta"),
 ("Volt & Su", "Elektrik · Tesisat ustası", "servis", ["#1a1a1a", "#f5c518", "#f7f5ef"], "Barlow Condensed / Barlow",
  ["hq:Giriş + 'Acil usta çağır' büyük buton", "c3:Elektrik / Tesisat / Su kaçağı", "sv:Fiyat listesi (keşif ücreti dahil)", "ba:Önce / sonra işler", "nm:7/24, ortalama varış süresi", "rv:Yorumlar", "fq:SSS", "cta:Hemen ara bandı", "mp:Bölgeler"],
  ["Hizmetler", "Fiyatlar", "İşlerimiz", "İletişim"],
  ["Acil çağrı formu → iş kaydı", "Keşif randevusu", "Teklif iste (fotoğraf yükleyerek)", "Ara / WhatsApp"],
  "elektrikçi pano, tesisatçı boru, su kaçağı cihazı"),
 ("Motor Atölye", "Oto servis", "servis", ["#16181d", "#d7262f", "#efefef"], "Oswald / Inter",
  ["hf:Tam foto giriş + plaka ile randevu", "c4:Periyodik bakım, fren, motor, lastik", "pk:Bakım paketleri fiyatlı", "tr:Araç durumu sorgula (plaka)", "gl:Atölye", "br:Çalışılan markalar", "rv:Yorumlar", "mp:Adres + çalışma saati"],
  ["Hizmetler", "Bakım paketleri", "Araç takip", "Kampanyalar", "İletişim"],
  ["Plaka ile randevu", "Araç servis durumu sorgu", "Bakım paketi online öde", "Lastik/yedek parça mağazası"],
  "oto servis lift, mekanik, lastik değişimi"),
 ("Pırıl Temizlik", "Temizlik şirketi", "servis", ["#0e3b43", "#58c4a3", "#f3faf7"], "Nunito / Nunito",
  ["hq:Giriş + anlık fiyat hesaplayıcı (m², oda)", "c3:Ev / ofis / inşaat sonrası", "st:Rezervasyon adımları", "pk:Paketler", "nm:Rakamlar", "ba:Önce/sonra", "rv:Yorumlar", "fq:SSS", "mp:Hizmet bölgeleri"],
  ["Hizmetler", "Fiyat hesapla", "Kurumsal", "İletişim"],
  ["Fiyat hesapla → rezervasyon (tarih/saat)", "Online ödeme / kapora", "Düzenli temizlik aboneliği", "Teklif formu (kurumsal)"],
  "temizlik ekibi, ofis temizliği, mop, cam silme"),
 ("Yük Nakliyat", "Evden eve nakliyat", "servis", ["#1b2a4a", "#ff8a00", "#f5f3ee"], "Sora / Figtree",
  ["hq:Giriş + 'Nereden - nereye' teklif formu", "c4:Evden eve, ofis, eşya depolama, asansörlü", "st:Taşınma süreci", "cl:Ev büyüklüğü → tahmini fiyat", "gl:Araç filosu", "nm:Rakamlar", "rv:Yorumlar", "fq:SSS", "mp:İletişim"],
  ["Hizmetler", "Teklif al", "Depolama", "İletişim"],
  ["Teklif formu → panel teklif", "Teklif onay linki", "Taşınma takvimi", "Ara / WhatsApp"],
  "nakliye kamyonu, koli, asansörlü taşıma"),
 # --- RANDEVU ---
 ("Makas", "Kuaför · Berber", "randevu", ["#1c1917", "#c8a27a", "#f7f3ee"], "Fraunces / Inter",
  ["hb:Giriş + 'Hemen randevu' (hizmet, usta, saat)", "sv:Hizmet + fiyat + süre", "tm:Ustalar (randevu ustaya bağlı)", "gl:Lookbook galeri", "pk:Paketler (gelin, damat)", "rv:Yorumlar", "cta:Hediye çeki", "mp:Adres + saatler"],
  ["Hizmetler", "Ekip", "Galeri", "Randevu", "Ürünler", "İletişim"],
  ["Gerçek randevu takvimi (boş saatler)", "Usta seçimi", "SMS hatırlatma", "Bakım ürünleri mağazası", "Hediye çeki satışı"],
  "kuaför salonu, saç kesimi, berber, fön"),
 ("Lumi Estetik", "Güzellik · estetik merkezi", "randevu", ["#2d1f2b", "#d9a5a0", "#fbf6f4"], "Cormorant / Manrope",
  ["hs:Yarım foto giriş + randevu", "c3:Cilt bakımı, lazer, kalıcı makyaj", "sv:Uygulamalar fiyat/seans", "pk:Seans paketleri", "ba:Önce/sonra (izinli)", "tm:Uzmanlar", "fq:SSS", "mp:İletişim"],
  ["Uygulamalar", "Uygulama detayı", "Paketler", "Uzmanlar", "Randevu", "İletişim"],
  ["Randevu (uzman+uygulama)", "Seans paketi online satın al", "Ön danışma formu", "Kampanya kuponu"],
  "cilt bakımı, spa yüz bakımı, güzellik salonu"),
 ("Gülüş Diş", "Diş kliniği", "randevu", ["#0b2e4f", "#2fa4d9", "#f3f8fb"], "DM Serif / DM Sans",
  ["hs:Giriş + muayene randevusu", "c4:İmplant, ortodonti, beyazlatma, çocuk diş", "tm:Hekimler", "st:İlk muayene süreci", "nm:Rakamlar", "gl:Klinik", "fq:SSS", "bl:Ağız sağlığı yazıları", "mp:İletişim"],
  ["Tedaviler", "Tedavi detayı", "Hekimlerimiz", "Randevu", "Blog", "İletişim"],
  ["Hekime göre randevu", "Tedavi bilgi formu", "Hatırlatma SMS", "Blog yazıları"],
  "diş kliniği, diş hekimi, ünit, gülümseme"),
 ("Pati Vet", "Veteriner kliniği", "randevu", ["#173a2e", "#f08a4b", "#f7f4ec"], "Fredoka / Nunito",
  ["hb:Giriş + randevu (hayvan türü)", "c4:Muayene, aşı, kısırlaştırma, bakım", "cl:Aşı takvimi hesaplayıcı", "tm:Veterinerler", "pr:Mama & aksesuar mağazası", "gl:Klinik", "fq:SSS", "mp:Acil hat + harita"],
  ["Hizmetler", "Aşı takvimi", "Pet shop", "Randevu", "İletişim"],
  ["Randevu", "Aşı hatırlatma SMS", "Mama/aksesuar mağazası (sepet, kargo)", "Acil ara"],
  "veteriner köpek muayene, kedi, klinik"),
 ("Denge Diyet", "Diyetisyen", "randevu", ["#20372a", "#8bc34a", "#f8faf3"], "Lora / Inter",
  ["hs:Giriş + ücretsiz ön görüşme", "c3:Kilo yönetimi, sporcu, online diyet", "cl:Vücut kitle indeksi hesapla", "pk:Online program paketleri", "st:Süreç", "bl:Tarifler / yazılar", "fq:SSS", "mp:İletişim"],
  ["Programlar", "Paketler", "Tarifler", "Randevu", "İletişim"],
  ["Online / yüz yüze randevu", "Paket satın al (ödeme)", "Ön bilgi formu", "Blog"],
  "sağlıklı tabak, diyetisyen danışma, sebze"),
 ("İç Ses", "Psikolog · danışmanlık", "randevu", ["#2b2f3a", "#7c9cbf", "#f6f5f2"], "Newsreader / Inter",
  ["hs:Sakin giriş + ilk görüşme randevusu", "c3:Bireysel, çift, çocuk-ergen", "tm:Uzmanlar", "st:Görüşme nasıl ilerler", "pk:Seans ücretleri", "bl:Yazılar", "fq:SSS (gizlilik)", "mp:İletişim"],
  ["Hizmetler", "Uzmanlar", "Online görüşme", "Yazılar", "İletişim"],
  ["Randevu (online / yüz yüze)", "Seans ödemesi", "Gizli ön form", "Hatırlatma"],
  "sakin terapi odası, koltuk, danışmanlık"),
 ("Form Stüdyo", "Spor salonu · pilates", "randevu", ["#111111", "#c6ff3d", "#f4f4f1"], "Anton / Inter",
  ["hf:Tam foto giriş + ücretsiz deneme dersi", "kr:Haftalık ders programı (kontenjanlı)", "pk:Üyelik paketleri", "tm:Eğitmenler", "gl:Salon", "nm:Rakamlar", "fq:SSS", "mp:İletişim"],
  ["Dersler", "Program", "Üyelik", "Eğitmenler", "İletişim"],
  ["Derse kayıt (kontenjan)", "Üyelik satın al (ödeme)", "Deneme dersi formu", "Hatırlatma"],
  "pilates reformer, spor salonu, fitness"),
 # --- MAĞAZA ---
 ("Atlas Butik", "Giyim · butik e-ticaret", "magaza", ["#151515", "#b08d57", "#f6f4f0"], "Playfair / Inter",
  ["hp:Kampanya slaytı + yeni gelenler", "cat:Kategoriler (kadın, erkek, aksesuar)", "pr:Çok satanlar", "cta:Kampanya bandı + kupon", "pr:Yeni sezon", "c4:Kargo, iade, güvenli ödeme, taksit", "bl:Stil önerileri", "mp:İletişim"],
  ["Kategori listesi (filtre)", "Ürün detayı (beden, renk)", "Sepet", "Ödeme", "Hesabım / siparişlerim", "Sipariş takip", "Yasal sayfalar"],
  ["Gerçek sepet + ödeme", "Varyant (beden/renk) stok", "Kupon", "Sipariş takip", "Pazaryeri stok eşleme"],
  "butik giyim, askılık, moda ürün"),
 ("Bahar Çiçek", "Çiçekçi", "magaza", ["#2e2a24", "#e0607e", "#fbf6f1"], "Fraunces / Nunito",
  ["hp:Giriş + 'Bugün teslim' vitrin", "cat:Gül, orkide, buket, saksı, özel gün", "pr:Çok satanlar", "cl:Teslimat saati ve semt seç", "c3:Aynı gün teslim, not kartı, foto ile teslim", "rv:Yorumlar", "mp:İletişim"],
  ["Kategori", "Ürün detayı (not kartı)", "Sepet", "Ödeme", "Sipariş takip", "Kurumsal"],
  ["Sepet + ödeme", "Teslim tarihi/saati seçimi", "Kart notu", "Sipariş takip SMS"],
  "çiçek buketi, gül, orkide"),
 ("Fırın 1923", "Pastane · fırın", "magaza", ["#3a2418", "#d98e32", "#fbf5ec"], "DM Serif / Figtree",
  ["hp:Giriş + günün ürünleri", "cat:Pasta, kurabiye, börek, ekmek", "pr:Siparişe özel pastalar", "qf:Özel pasta sipariş formu (kişi, tarih, yazı)", "gl:Vitrin", "c3:Gel al / adrese teslim", "mp:Şubeler"],
  ["Ürünler", "Özel pasta", "Sepet", "Ödeme", "Şubeler"],
  ["Sepet + ödeme (gel-al / teslimat)", "Özel pasta talebi → teklif", "Teslim saati", "SMS bildirim"],
  "pasta, fırın, kurabiye, pastane vitrini"),
 ("Teknofix", "Telefon tamir + aksesuar", "magaza", ["#0d1117", "#3b82f6", "#f4f6fa"], "Space Grotesk / Inter",
  ["hq:Giriş + model seç → tamir fiyatı", "c4:Ekran, batarya, kamera, şarj soketi", "tr:Tamir durumu sorgula", "pr:Aksesuar mağazası", "st:Nasıl çalışır", "rv:Yorumlar", "fq:SSS", "mp:İletişim"],
  ["Tamir fiyatları", "Tamir takip", "Aksesuar mağazası", "Ürün detayı", "Sepet/ödeme", "İletişim"],
  ["Model → fiyat → tamir kaydı", "Tamir takip sorgu", "Aksesuar sepet+ödeme", "Kargo ile tamir formu"],
  "telefon tamiri, ekran değişimi, aksesuar"),
 # --- DİĞER ---
 ("Sofra", "Restoran · lokanta", "yemek", ["#231a14", "#c0392b", "#f7f1e8"], "Playfair / Inter",
  ["hf:Tam foto giriş + rezervasyon / paket sipariş", "mn:Menü (kategori sekmeli, fiyatlı, fotoğraflı)", "c3:Salon, paket, catering", "gl:Mekân ve yemek", "rv:Yorumlar", "cta:Grup / özel gün rezervasyonu", "mp:Adres + saatler"],
  ["Menü", "Paket sipariş", "Rezervasyon", "Galeri", "İletişim"],
  ["Online paket sipariş (sepet, ödeme)", "Masa rezervasyonu", "QR menü", "Yemek platformu sipariş aktarımı"],
  "restoran masa, kebap, meze, şef"),
 ("Anahtar Emlak", "Emlak ofisi", "proje", ["#14213d", "#2a9d8f", "#f5f5f2"], "Sora / Inter",
  ["hs:Giriş + ilan arama (satılık/kiralık, il/ilçe, oda)", "il:Öne çıkan ilanlar", "c3:Sat, kirala, değerleme", "cl:Kredi / kira hesaplayıcı", "tm:Danışmanlar", "nm:Rakamlar", "mp:Ofis"],
  ["İlanlar (filtre)", "İlan detayı (galeri, harita)", "Değerleme talebi", "Danışmanlar", "İletişim"],
  ["İlan listeleme ve filtre", "İlan için görüşme randevusu", "Değerleme talep formu", "WhatsApp ilan paylaş"],
  "modern daire salon, emlak, ev dış cephe"),
 ("Direksiyon", "Sürücü kursu", "kurs", ["#0f172a", "#ef4444", "#f6f7f9"], "Archivo / Inter",
  ["hs:Giriş + ön kayıt formu", "c4:B, A, A2, engelli sürücü", "pk:Kurs ücretleri + taksit", "kr:Dönem / sınav takvimi", "st:Ehliyet süreci", "gl:Araç filosu", "fq:SSS", "mp:İletişim"],
  ["Kurslar", "Ücretler", "Takvim", "Ön kayıt", "İletişim"],
  ["Ön kayıt → panel kayıt", "Taksitli ödeme linki", "Ders/sınav hatırlatma SMS", "Takvim"],
  "sürücü kursu aracı, direksiyon dersi"),
]

LBL = {"servis": "Servis · teklif", "randevu": "Randevu", "magaza": "E-ticaret", "yemek": "Restoran", "proje": "İlan", "kurs": "Kurs · kayıt"}


def wf(code, ac, sf):
    """Bölüm tipine göre küçük tel kafes çizimi (HTML)."""
    g = "#cfd3d8"; d = "#9aa0a8"
    box = lambda w, h, c=g, r=3, extra="": '<i style="display:block;width:%s;height:%dpx;background:%s;border-radius:%dpx;%s"></i>' % (w, h, c, r, extra)
    row = lambda *xs, gap=5: '<div style="display:flex;gap:%dpx">%s</div>' % (gap, "".join(xs))
    col = lambda *xs, gap=4, w="auto": '<div style="display:flex;flex-direction:column;gap:%dpx;flex:%s">%s</div>' % (gap, "1" if w == "auto" else "0 0 " + w, "".join(xs))
    foto = lambda h, w="100%": '<div style="width:%s;height:%dpx;border-radius:4px;background:linear-gradient(135deg,#8d939b,#b9bec4);position:relative"><span style="position:absolute;left:6px;bottom:4px;font:600 8px Inter;color:#fff;letter-spacing:.08em">FOTO</span></div>' % (w, h)
    btn = box("44px", 10, ac, 3)
    if code in ("hf", "hp"):
        return '<div style="position:relative">%s<div style="position:absolute;left:10px;bottom:10px;display:flex;flex-direction:column;gap:4px">%s%s%s</div></div>' % (foto(92), box("120px", 9, "#fff"), box("80px", 6, "#e6e6e6"), btn)
    if code in ("hs", "hb", "hq"):
        right = foto(84) if code == "hs" else '<div style="background:#fff;border:1px solid %s;border-radius:5px;padding:6px;display:flex;flex-direction:column;gap:4px">%s%s%s%s</div>' % (g, box("100%", 7), box("100%", 7), box("100%", 7), box("100%", 10, ac))
        return row(col(box("90%", 11, "#3b3f45"), box("70%", 11, "#3b3f45"), box("85%", 5), box("60%", 5), row(btn, box("44px", 10, "#fff", 3, "border:1px solid %s" % d)), gap=5), '<div style="flex:1">%s</div>' % right, gap=8)
    if code in ("c3", "c4"):
        n = 3 if code == "c3" else 4
        return row(*[col(foto(30), box("80%", 6, "#3b3f45"), box("95%", 4), box("60%", 4)) for _ in range(n)])
    if code in ("pr", "il"):
        return row(*[col(foto(40), box("85%", 5, "#3b3f45"), box("40%", 6, ac)) for _ in range(5)], gap=4)
    if code == "cat":
        return row(*[foto(34) for _ in range(5)], gap=4)
    if code in ("sv", "pk"):
        return row(*[col(box("70%", 6, "#3b3f45"), box("45%", 9, ac), box("90%", 4), box("80%", 4), box("100%", 8, "#fff", 3, "border:1px solid %s" % d), w="auto") for _ in range(3)], gap=6)
    if code in ("bk", "kr"):
        cells = "".join('<i style="width:18px;height:12px;border-radius:2px;background:%s"></i>' % (ac if i in (3, 9, 16) else g) for i in range(21))
        return '<div style="display:grid;grid-template-columns:repeat(7,18px);gap:3px">%s</div>' % cells
    if code in ("qf", "cl", "tr"):
        return '<div style="background:%s;border-radius:5px;padding:8px;display:flex;gap:5px;align-items:center">%s%s%s%s</div>' % (sf, box("70px", 12, "#fff"), box("70px", 12, "#fff"), box("70px", 12, "#fff"), box("60px", 12, ac))
    if code in ("gl", "ba"):
        return row(foto(44, "40%"), col(foto(20), foto(20)), col(foto(20), foto(20)), gap=4)
    if code == "tm":
        return row(*[col('<i style="display:block;width:32px;height:32px;border-radius:50%;background:#aab0b7"></i>', box("40px", 5, "#3b3f45")) for _ in range(4)], gap=10)
    if code in ("st",):
        return row(*[col('<b style="font:700 11px Inter;color:%s">%d</b>' % (ac, i + 1), box("80%", 5, "#3b3f45"), box("90%", 4)) for i in range(4)])
    if code == "nm":
        return row(*[col('<b style="font:800 14px Inter;color:#3b3f45">%s</b>' % v, box("60%", 4)) for v in ("12+", "4.8k", "38", "7/24")])
    if code == "rv":
        return row(*[col(box("40%", 5, ac), box("95%", 4), box("85%", 4), box("50%", 5, "#3b3f45"), w="auto") for _ in range(3)], gap=8)
    if code in ("fq",):
        return col(*[box("100%", 9, "#fff", 3, "border:1px solid %s" % g) for _ in range(3)], gap=3)
    if code == "mp":
        return row(col(box("70%", 6, "#3b3f45"), box("90%", 4), box("80%", 4), box("50px", 10, ac)), '<div style="flex:1.3;height:44px;border-radius:4px;background:repeating-linear-gradient(45deg,#dde1e5 0 6px,#e9ecef 6px 12px)"></div>', gap=8)
    if code == "mn":
        tabs = row(*[box("38px", 9, ac if i == 0 else g, 9) for i in range(5)], gap=4)
        return col(tabs, row(*[row(foto(24, "24px"), col(box("70%", 5, "#3b3f45"), box("40%", 4)), gap=4) for _ in range(3)], gap=8))
    if code in ("br",):
        return row(*[box("40px", 9, d) for _ in range(7)], gap=8)
    if code in ("bl",):
        return row(*[col(foto(28), box("85%", 5, "#3b3f45"), box("60%", 4)) for _ in range(3)])
    if code == "cta":
        return '<div style="background:%s;border-radius:5px;padding:9px;display:flex;justify-content:space-between;align-items:center">%s%s</div>' % (ac, box("150px", 8, "#fff"), box("54px", 12, "#fff"))
    return box("100%", 30)


def card(i, t):
    nm, sec, fam, pal, fn, secs, pages, works, foto = t
    dk, ac, sf = pal
    blocks = "".join('<div class="sec"><div class="lb"><b>%d</b>%s</div><div class="wf">%s</div></div>' % (k + 1, html.escape(s.split(":", 1)[1]), wf(s.split(":")[0], ac, sf)) for k, s in enumerate(secs))
    return '''<article class="card"><header style="background:%s"><div><span class="no">%02d</span><h2>%s</h2><p>%s</p></div><div class="chips"><span class="fam">%s</span>%s<span class="fn">%s</span></div></header>
<div class="body"><div class="site"><div class="nav"><b style="color:%s">%s</b><span></span><span></span><span></span><span></span><i style="background:%s"></i></div>%s<div class="ft" style="background:%s"></div></div>
<aside><h4>Sayfalar</h4><ul>%s</ul><h4>Çalışacak işlevler</h4><ul class="ok">%s</ul><h4>Fotoğraf konuları</h4><p class="ph">%s</p></aside></div></article>''' % (
        dk, i, html.escape(nm), html.escape(sec), LBL[fam], "".join('<i class="sw" style="background:%s"></i>' % c for c in pal), html.escape(fn),
        dk, html.escape(nm), ac, blocks, dk, "".join("<li>%s</li>" % html.escape(p) for p in pages), "".join("<li>%s</li>" % html.escape(w) for w in works), html.escape(foto))


CSS = """*{box-sizing:border-box;margin:0}body{font:14px/1.45 Inter,system-ui,sans-serif;background:#ecebe7;color:#1d1f23;padding:28px;width:1500px}
.top{display:flex;justify-content:space-between;align-items:end;margin-bottom:18px}.top h1{font:800 26px Inter}.top p{color:#555;max-width:760px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.card{background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 0 rgba(0,0,0,.06)}
.card header{color:#fff;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;gap:12px}
.card h2{font:700 19px Inter;display:inline}.card header p{opacity:.8;font-size:13px}.no{font:800 13px Inter;opacity:.55;margin-right:8px}
.chips{display:flex;gap:6px;align-items:center;flex-wrap:wrap;justify-content:flex-end}.sw{width:18px;height:18px;border-radius:50%;border:2px solid rgba(255,255,255,.7);display:inline-block}
.fam{background:rgba(255,255,255,.16);padding:3px 9px;border-radius:99px;font-size:12px;font-weight:600}.fn{font-size:11px;opacity:.75;margin-left:4px}
.body{display:grid;grid-template-columns:1.5fr 1fr;gap:16px;padding:16px}
.site{border:1px solid #e2e4e7;border-radius:10px;padding:10px;background:#fbfbfa;display:flex;flex-direction:column;gap:9px}
.nav{display:flex;align-items:center;gap:8px;padding-bottom:6px;border-bottom:1px solid #eceef0;font:800 12px Inter}.nav span{width:34px;height:5px;background:#d4d7db;border-radius:3px}.nav span:first-of-type{margin-left:auto}.nav i{width:52px;height:14px;border-radius:4px}
.sec{display:grid;grid-template-columns:150px 1fr;gap:10px;align-items:center}.lb{font-size:11.5px;line-height:1.3;color:#3d4148}.lb b{display:inline-block;width:17px;color:#888}
.ft{height:22px;border-radius:5px}
aside h4{font:700 12px Inter;text-transform:uppercase;letter-spacing:.06em;color:#777;margin:4px 0 6px}aside ul{padding-left:16px;margin-bottom:12px;font-size:13px}aside ul.ok li::marker{content:"✓  ";color:#1f9d55}
.ph{font-size:12.5px;color:#555;background:#f4f4f2;border-radius:8px;padding:8px}"""


def sayfa(title, sub, items, start):
    return '<!doctype html><html lang="tr"><meta charset="utf-8"><style>%s</style><body><div class="top"><div><h1>%s</h1><p>%s</p></div><b style="color:#888">onlinekaydet · yeni tema şablonları</b></div><div class="grid">%s</div></body></html>' % (
        CSS, html.escape(title), html.escape(sub), "".join(card(start + k + 1, t) for k, t in enumerate(items)))


if __name__ == "__main__":
    groups = [("Servis ve teklif temaları (1–6)", T[0:6]), ("Randevu temaları (7–13)", T[6:13]), ("E-ticaret temaları (14–17)", T[13:17]), ("Restoran, ilan ve kurs temaları (18–20)", T[17:20])]
    st = 0
    for k, (ti, it) in enumerate(groups):
        open("pano%d.html" % (k + 1), "w", encoding="utf-8").write(sayfa(ti, "Soldaki çizim ana sayfanın bölüm sırası, sağda sayfalar ve sitede gerçekten çalışacak işlevler. Fotoğraflar Pexels/Unsplash'ten ücretsiz ve gerçek olacak.", it, st))
        st += len(it)
    json.dump([dict(ad=t[0], sektor=t[1], aile=t[2], renk=t[3], font=t[4], bolum=t[5], sayfa=t[6], islev=t[7], foto=t[8]) for t in T], open("plan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
