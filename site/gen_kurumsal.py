"""Çözümler, Neden OnlineKaydet ve Kariyer sayfalarını üretir; menü, alt bilgi, mobil menü, çerez bandı ve
kampanya titremesi düzeltmesini tüm sayfalara uygular. Tekrar çalıştırılabilir."""
import pathlib, re, html
from gen_mobil_menu import mm_html as _old_mm  # noqa: F401  (eski şablon; aşağıda yenisi kullanılır)

V = "20241124r"
T = pathlib.Path("hakkimizda.html").read_text(encoding="utf-8")
PRE, POST = T[:T.index("<main")], T[T.index("</main>"):]
j = T.index('id="teklif"'); k = T.rfind("<section", 0, j)
FORM = T[k:T.index("</section>", j) + 10]
FORM = FORM.replace("Numaranızı bırakın, sizi arayalım.", "Konuşalım, işinize göre kurulumu birlikte planlayalım.")


def e(s): return html.escape(s, quote=True)


def shell(fn, title, desc, crumb, main):
    pre = re.sub(r"<title>.*?</title>", "<title>%s</title>" % e(title), PRE, 1, flags=re.S)
    pre = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % e(desc), pre, 1)
    pre = re.sub(r'(<link rel="canonical" href=")[^"]*(">)', r"\g<1>https://onlinekaydet.com/%s\g<2>" % fn, pre, 1)
    pre = re.sub(r'(<meta property="og:url" content=")[^"]*(">)', r"\g<1>https://onlinekaydet.com/%s\g<2>" % fn, pre, 1)
    pre = re.sub(r'(<meta property="og:title" content=")[^"]*(">)', lambda m: m.group(1) + e(title) + m.group(2), pre, 1)
    pre = re.sub(r'(<meta property="og:description" content=")[^"]*(">)', lambda m: m.group(1) + e(desc) + m.group(2), pre, 1)
    pre = re.sub(r'"position": 2, "name": "[^"]*", "item": "[^"]*"', '"position": 2, "name": "%s", "item": "https://onlinekaydet.com/%s"' % (crumb, fn), pre, 1)
    out = pre + '<main class="kz" id="icerik">' + main + POST
    pathlib.Path(fn).write_text(out, encoding="utf-8")


def hero(h1, lead, crumb, extra=""):
    return ('<section class="kzhero"><div class="kzw"><p class="kzcr"><a href="/">Ana sayfa</a> / %s</p><h1>%s</h1><p class="kzl">%s</p>'
            '<div class="kzcta"><a class="kzbtn p" href="/demo.html">7 gün ücretsiz deneyin</a><a class="kzbtn" href="#teklif">Teklif alın</a></div>%s</div></section>') % (crumb, h1, lead, extra)


def fig(src, alt, w=1400, h=875, lazy=True):
    return '<figure class="kzfig"><img src="/v9/img/%s" width="%d" height="%d" alt="%s"%s></figure>' % (src, w, h, e(alt), ' loading="lazy"' if lazy else "")


# ------------------------------------------------------------------ ÇÖZÜMLER
GRUPLAR = [
    ("web", "Web sitesi", "Sitenizi sektörünüze hazır temayla yayına alın",
     "Metin, yazı tipi ve görselleri panelden kendiniz değiştirirsiniz. Her bölüm düzenlenebilir.", "panel-d-site.webp", "Web sitesi bölüm editörü ekranı", [
         ("Sektörüne hazır temalar", "Kuaförden teknik servise, lokantadan emlağa her iş kolu için hazır tema. Seçin, firma bilgileriniz otomatik dolsun.", "/temalar.html"),
         ("Bölüm editörü", "Sayfadaki her bölümün metni, görseli ve yazı tipi panelden düzenlenir. Kod bilmeniz gerekmez.", "/web-sitesi.html"),
         ("Alan adı bağlama", "Kendi alan adınızı siteye bağlayın; adım adım rehber panelde.", "/bilgi-alan-adi.html"),
         ("Arama motoru (SEO)", "Başlık, açıklama, site haritası ve 301 yönlendirmeleri panelden ayarlanır.", "/web-sitesi.html"),
         ("Çok dilli site", "Sitenizi birden fazla dilde yayınlayın.", "/web-sitesi.html"),
         ("Çerez bandı ve yasal metinler", "Çerez onay bandı, KVKK, mesafeli satış ve iade metinleri firma bilginizle otomatik dolar.", "/kvkk.html"),
     ]),
    ("eticaret", "E-ticaret", "Kendi mağazanızı kurun, siparişi doğrudan alın",
     "Ürün, stok, ödeme, kargo ve kampanya aynı panelde. Ek bir mağaza yazılımı gerekmez.", "panel-d-urun.webp", "Ürün listesi ve stok ekranı", [
         ("Ürün, varyant ve stok", "Renk ve beden seçenekleri, stok takibi, XML ile toplu ürün aktarımı.", "/bilgi-urun-ekleme.html"),
         ("Kategori ve Google ürün kategorisi", "Kategorileri birleştirin, sürükleyin. Google ürün kategorisi eşlenir; mağazaya ve ürün akışlarına otomatik gelir.", "/e-ticaret.html"),
         ("Ödeme yöntemleri", "Kredi kartı (iyzico), havale ve kapıda ödeme. Tutar her zaman sunucuda hesaplanır.", "/e-ticaret.html"),
         ("Teslimat günü, saat ve hediye paketi", "Müşteri teslimat gününü ve saat aralığını seçer, hediye paketi ve not ekler.", "/e-ticaret.html"),
         ("Hızlı öde", "Kayıtlı adres ve son ödeme yöntemiyle tek adımda sipariş. Kart bilginiz mağazada saklanmaz.", "/e-ticaret.html"),
         ("Sepet hatırlatma", "Sepetini bırakan müşteriye WhatsApp veya SMS ile hatırlatma gider; isterseniz kupon kodu eklenir.", "/e-ticaret.html"),
         ("Kampanya, kupon ve çarkıfelek", "Sepet indirimi, X al Y öde, kargo bedava, kupon kodu ve çarkıfelek. Birden fazla kampanya birlikte çalışır.", "/e-ticaret.html"),
         ("Bayi (B2B) fiyatı ve cari", "Bayilerinize özel fiyat ve vadeli cari hesap. Limit ve bakiye panelden izlenir.", "/e-ticaret.html"),
         ("Sipariş, kargo ve iade", "Siparişler listeye düşer; kargo takip numarası, etiket ve iade süreci panelde.", "/bilgi-siparis-ve-kargo.html"),
         ("Fiyat karşılaştırma ve reklam akışları", "Google Merchant, Akakçe, Cimri ve Meta için ürün akışları panelden açılır.", "/e-ticaret.html"),
     ]),
    ("baglanti", "Pazaryeri ve bağlantılar", "Satış kanallarınızı tek listede toplayın",
     "Pazaryeri, yemek platformu, kargo, SMS ve ödeme bağlantıları panelden kurulur.", "panel-d-pazaryeri.webp", "Pazaryeri bağlantıları ekranı", [
         ("Pazaryerleri", "Ürünlerinizi pazaryerlerine gönderin, gelen siparişleri tek listede görün.", "/bilgi-pazaryerine-gonderme.html"),
         ("Yemek platformları", "Yemeksepeti, Trendyol Yemek, Getir Yemek ve Migros Yemek siparişleri listeye kendiliğinden düşer.", "/bilgi-yemek-siparisleri.html"),
         ("SMS, WhatsApp ve e-posta", "Randevu, sipariş ve kargo bildirimleri müşteriye otomatik gider.", "/entegrasyonlar.html"),
         ("Bağlanabilen tüm entegrasyonlar", "97 entegrasyon, 8 grup. Bilgileri siz girersiniz; bağlantıyı panel kurar.", "/entegrasyonlar.html"),
         ("Açık API", "Kendi sisteminizle konuşması için API ve webhook bağlantıları.", "/acik-api-ve-entegrasyon.html"),
     ]),
    ("is", "Randevu ve iş takibi", "Randevudan tahsilata işi kaybetmeden yürütün",
     "Müşteri, takvim, usta ve tahsilat aynı kayıtta durur.", "panel-k-takvim.webp", "Randevu takvimi ekranı", [
         ("Randevu ve takvim", "Sitedeki randevu formu doğrudan takvime düşer; müşteriye hatırlatma gider.", "/bilgi-randevu-ve-takvim.html"),
         ("Servis kaydı ve usta takibi", "Hangi usta hangi işte, ne tahsil etti panelden görünür. Fiş ve belgeler hazır.", "/is-takibi.html"),
         ("Müşteri kayıtları", "Müşteriler randevu aldıkça kendiliğinden birikir; geçmiş işler tek kayıtta.", "/bilgi-musteri-yonetimi.html"),
         ("Ekip, maaş ve prim", "Prim tamamlanan işlerden kendiliğinden hesaplanır.", "/bilgi-personel-ve-prim.html"),
     ]),
    ("para", "Muhasebe ve stok", "Kasa, cari ve stok elinizin altında",
     "Her tahsilat kasaya yazılır; gün sonunda hesap kapanır.", "panel-k-kasa.webp", "Kasa ve gün sonu ekranı", [
         ("Kasa ve gün sonu", "Alınan her ödeme kasaya yazılır; gelir ve giderleri ayrıca girin.", "/bilgi-kasa-ve-muhasebe.html"),
         ("Cari hesap", "Müşteri ve bayi bakiyeleri, vadeler ve tahsilatlar.", "/muhasebe-ve-stok.html"),
         ("Stok, barkod ve etiket", "Barkod okutarak hızlı satış; kargo etiketi ve QR menü kartı tasarımı.", "/bilgi-etiket-tasarimi.html"),
         ("Toplu fatura", "Siparişleri seçin, faturayı toplu oluşturun, dosyayı entegratöre yükleyin.", "/bilgi-toplu-fatura.html"),
         ("Raporlar", "Satış, tahsilat ve ekip raporları; Excel'e aktarma.", "/muhasebe-ve-stok.html"),
     ]),
    ("sektor", "Sektöre özel çözümler", "Panel sektörünüzün kendi diliyle konuşur",
     "Kullandığınız terimler, listeler ve ekranlar sektörünüze göre gelir.", "panel-lokanta-siparis.webp", "Lokanta sipariş ekranı", [
         ("Lokanta ve kafe", "QR menü, masa ve paket siparişleri, yemek platformu bağlantıları.", "/bilgi-yemek-menusu.html"),
         ("Emlak, araç kiralama ve tur", "Panelden ilan ekleyin; ilan vitrini sitenizde görünür.", "/bilgi-ilan-ekleme.html"),
         ("Kuaför ve güzellik", "Randevu, personel primi ve müşteri geçmişi.", "/sektor-kuafor.html"),
         ("Teknik servis", "Marka, model ve arıza listeleri hazır gelir; servis fişi ve usta takibi.", "/sektor-kombi.html"),
         ("Tüm sektörler", "Sektörünüzü seçin, tema ve panel dili ona göre hazırlansın.", "/tum-sektorler.html"),
     ]),
]


def cozumler():
    chips = "".join('<a href="#%s">%s</a>' % (g[0], g[1]) for g in GRUPLAR)
    body = hero("İşinizin her yönü için hazır çözümler",
                "Web sitesi, e-ticaret, randevu, muhasebe ve bağlantılar tek panelde. Hangi alanda neler yaptığımızı aşağıdan inceleyin.", "Çözümler")
    body += '<nav class="kzchips" aria-label="Çözüm başlıkları"><div class="kzw">%s</div></nav>' % chips
    for i, (gid, ad, baslik, alt, img, imgalt, kartlar) in enumerate(GRUPLAR):
        cards = "".join('<a class="kzcard" href="%s"><b>%s</b><span>%s</span><em>Ayrıntı</em></a>' % (h, e(t), e(a)) for t, a, h in kartlar)
        body += ('<section class="kzgrp" id="%s"><div class="kzw"><div class="kzgh%s"><div><p class="kzet">%02d // %s</p><h2>%s</h2><p class="kzl">%s</p></div>%s</div>'
                 '<div class="kzcards">%s</div></div></section>') % (gid, " r" if i % 2 else "", i + 1, ad, baslik, alt, fig(img, imgalt), cards)
    body += '<section class="kzdark" style="margin-top:70px"><div class="kzw"><p class="kzet">Başlamak kolay</p><h2>Önce deneyin, sonra karar verin.</h2><p class="kzl">Demo hesabınız 7 gün ücretsiz. Kart bilgisi istenmez.</p><div class="kzcta"><a class="kzbtn p" href="/demo.html">7 gün ücretsiz deneyin</a><a class="kzbtn" href="/fiyatlar.html">Paketleri görün</a></div></div></section>'
    body += FORM
    shell("cozumler.html", "Çözümler: web sitesi, e-ticaret, randevu ve muhasebe | OnlineKaydet",
          "Web sitesi, e-ticaret, pazaryeri bağlantıları, randevu ve iş takibi, kasa ve stok. OnlineKaydet'in tüm çözümleri tek sayfada.", "Çözümler", body)


# ------------------------------------------------------------------ NEDEN
def neden():
    body = hero("Sitenizi, mağazanızı ve işinizi tek yerden yönetin",
                "Birden fazla programı birbirine bağlamakla uğraşmayın. OnlineKaydet küçük işletmenin ihtiyacı olan her şeyi tek panelde toplar, kurulumu birlikte yaparız.", "Neden OnlineKaydet")
    body += '<div class="kzw" style="padding-bottom:20px">%s</div>' % fig("nx/panel-radar.webp", "Panelde satış ve iş takibi özeti", 1600, 900, False)
    big = [
        ("Türkiye'deki sunucuda", "Sitenizin ve verilerinizin durduğu sunucu Türkiye'de. Tanıtım sayfalarımız önceden üretilmiş HTML olduğu için hızlı açılır, arama motorları kolay tarar."),
        ("Hızlı kurulum", "Demo hesabınız dakikalar içinde açılır. Sektörünüzü seçersiniz; tema, listeler ve ayarlar hazır gelir, kalanını birlikte tamamlarız."),
        ("Tek panel", "Web sitesi, e-ticaret, randevu, kasa ve stok aynı hesapta. Veriyi bir yerden öbürüne taşımazsınız."),
        ("Sektörünüzün diliyle", "78 sektör için ayrı terimler, listeler ve temalar. Kuaförde randevu, lokantada sipariş, serviste iş emri."),
        ("97 entegrasyon", "Pazaryeri, yemek platformu, kargo, SMS ve ödeme bağlantıları panelden kurulur."),
        ("Otomatik bildirim", "Randevu hatırlatma, sipariş ve kargo mesajı, terk edilen sepete WhatsApp hatırlatması kendiliğinden gider."),
    ]
    body += '<section><div class="kzw"><p class="kzet">01 // İddialı olduğumuz alanlar</p><h2>Küçük işletme için gerçekten işe yarayan altı şey.</h2><div class="kzbig" style="margin-top:36px">%s</div></div></section>' % "".join(
        '<div><span class="no">%02d //</span><h3>%s</h3><p>%s</p></div>' % (i + 1, e(t), e(a)) for i, (t, a) in enumerate(big))
    body += ('<section class="kzsoft"><div class="kzw"><div class="kzsplit"><div><p class="kzet">02 // Mağaza</p><h2>Siparişi alan, teslimatı planlayan mağaza.</h2>'
             '<p class="kzl">Kendi e-ticaret sitenizi kurun; ödeme, kargo ve kampanya hazır.</p><ul class="kzchk">'
             '<li>Teslimat günü ve saat aralığı seçimi, hediye paketi ve notu</li><li>Hızlı öde: kayıtlı adres ve son ödeme yöntemiyle tek adım</li>'
             '<li>Sepetini bırakan müşteriye WhatsApp veya SMS hatırlatması</li><li>Kategoriler Google ürün kategorisine otomatik eşlenir</li>'
             '<li>Kupon, çarkıfelek, X al Y öde ve bayi fiyatı</li></ul><div class="kzcta"><a class="kzbtn p" href="/e-ticaret.html">E-ticareti inceleyin</a></div></div>%s</div></div></section>') % fig("panel-d-kampanya.webp", "Kampanya listesi ekranı")
    body += ('<section><div class="kzw"><div class="kzsplit"><div class="kzfigx">%s</div><div><p class="kzet">03 // İş takibi</p><h2>Randevudan tahsilata tek kayıt.</h2>'
             '<p class="kzl">Müşteri, usta, takvim ve kasa birbirine bağlı çalışır.</p><ul class="kzchk"><li>Sitedeki randevu formu doğrudan takvime düşer</li>'
             '<li>Prim, tamamlanan işlerden kendiliğinden hesaplanır</li><li>Her tahsilat kasaya yazılır, gün sonunda hesap kapanır</li>'
             '<li>Müşterinin geçmişi tek kayıtta durur</li></ul><div class="kzcta"><a class="kzbtn p" href="/is-takibi.html">İş takibini inceleyin</a></div></div></div></div></section>') % fig("panel-k-takvim.webp", "Randevu takvimi ekranı")
    body += ('<section class="kzsoft"><div class="kzw"><p class="kzet">04 // Karşılaştırma</p><h2>Defter ve ayrı programlar yerine.</h2><div style="overflow:auto;margin-top:24px"><table class="kzcmp"><thead><tr><th></th><th>Defter, Excel, ayrı programlar</th><th>OnlineKaydet</th></tr></thead><tbody>'
             '<tr><td>Kayıt</td><td>Dağınık, kaybolabilir</td><td>Tek kayıtta müşteri, iş ve tahsilat</td></tr>'
             '<tr><td>Web sitesi</td><td>Ayrı firma, ayrı ücret</td><td>Panelle birlikte, hazır tema</td></tr>'
             '<tr><td>Sipariş ve randevu</td><td>Elle aktarılır</td><td>Siteden panele otomatik düşer</td></tr>'
             '<tr><td>Bildirim</td><td>Tek tek mesaj yazılır</td><td>SMS, WhatsApp ve e-posta otomatik</td></tr>'
             '<tr><td>Kurulum</td><td>Kendiniz öğrenirsiniz</td><td>Birlikte kurarız, demo 7 gün ücretsiz</td></tr>'
             '<tr><td>Veri</td><td>Farklı yerlerde</td><td>Türkiye\'deki sunucuda, sizin hesabınızda</td></tr></tbody></table></div></div></section>')
    body += ('<section class="kzdark"><div class="kzw"><p class="kzet">05 // Nasıl başlarsınız</p><h2>Üç adımda yayında.</h2><div class="kzsteps">'
             '<div><span>01 //</span><b>Demo hesabınızı açın</b><p>7 gün ücretsiz, kart bilgisi istenmez.</p></div>'
             '<div><span>02 //</span><b>Sektörünüzü ve temanızı seçin</b><p>Firma bilgileriniz ve listeleriniz hazır gelir.</p></div>'
             '<div><span>03 //</span><b>Yayına alın</b><p>İsterseniz kurulumu birlikte tamamlarız, paketinizi sonra seçersiniz.</p></div></div>'
             '<div class="kzcta"><a class="kzbtn p" href="/demo.html">7 gün ücretsiz deneyin</a><a class="kzbtn" href="/cozumler.html">Tüm çözümler</a></div></div></section>')
    body += FORM
    shell("neden-onlinekaydet.html", "Neden OnlineKaydet? Türkiye'deki sunucu, hızlı kurulum, tek panel",
          "Web sitesi, e-ticaret, randevu ve muhasebe tek panelde. Türkiye'deki sunucu, hızlı kurulum, 97 entegrasyon ve sektörünüzün diliyle çalışan panel.", "Neden OnlineKaydet", body)


# ------------------------------------------------------------------ KARİYER
def kariyer():
    body = hero("Bizimle çalışın", "Küçük işletmelerin işini kolaylaştıran bir ürün geliştiriyoruz. Açık pozisyonlara göz atın ya da genel başvuru yapın.", "Kariyer")
    body = body.replace('<a class="kzbtn p" href="/demo.html">7 gün ücretsiz deneyin</a><a class="kzbtn" href="#teklif">Teklif alın</a>',
                        '<a class="kzbtn p" href="#pozisyonlar">Açık pozisyonlar</a><a class="kzbtn" href="#genel" data-genel>Genel başvuru</a>')
    body += ('<section class="kzsoft"><div class="kzw"><p class="kzet">01 // Nasıl çalışıyoruz</p><h2>Küçük ekip, gerçek müşteri.</h2><div class="kzvals" style="margin-top:28px">'
             '<div><h3>Gerçek işletmeler için</h3><p>Yazdığımız her özellik bir kuaförün, servisin ya da mağazanın gün içinde kullandığı bir ekrandır.</p></div>'
             '<div><h3>Doğrudan sorumluluk</h3><p>Ekip küçük olduğu için yaptığınız iş ürüne ve müşteriye hızla yansır.</p></div>'
             '<div><h3>Başvurunuz okunur</h3><p>Her başvuru bir insan tarafından incelenir ve durumu hakkında size dönülür.</p></div></div></div></section>')
    body += ('<section id="pozisyonlar"><div class="kzw"><p class="kzet">02 // İş ilanları</p><h2>Açık pozisyonlar</h2><p class="kzl" style="margin-bottom:24px">Bir bölüm seçin, ayrıntıyı açın ve başvurun. Özgeçmişinizi PDF, DOC veya DOCX olarak ekleyebilirsiniz.</p>'
             '<div class="kzfl" id="kz-fl" role="group" aria-label="Bölüm filtresi"></div><div class="kzjobs" id="kz-jobs" aria-live="polite"><p class="kzl">Pozisyonlar yükleniyor…</p></div>'
             '<noscript><p class="kzl">Başvuru için JavaScript gerekir. Bize iletişim sayfasından ulaşabilirsiniz.</p></noscript></div></section>')
    body += ('<section class="kzdark" id="genel"><div class="kzw"><p class="kzet">03 // Aradığınız pozisyon yok mu?</p><h2>Genel başvuru yapın.</h2><p class="kzl">Alanınıza uygun bir ihtiyaç doğduğunda özgeçmişinize bakarız.</p>'
             '<div class="kzcta"><button type="button" class="kzbtn p" data-genel>Genel başvuru formu</button></div></div></section>')
    body += ('<dialog class="kzdlg" id="kz-dlg" aria-labelledby="kz-dt"><form class="kzfm" enctype="multipart/form-data" novalidate><h3 id="kz-dt">Başvuru formu</h3><p class="sub">Başvurduğunuz pozisyon: <b id="kz-ilan"></b></p>'
             '<p class="er" role="alert"></p><input type="hidden" name="ilan">'
             '<label>Ad soyad *<input type="text" name="name" autocomplete="name" required></label>'
             '<div class="two"><label>E-posta *<input type="email" name="email" autocomplete="email" required></label><label>Telefon *<input type="tel" name="phone" autocomplete="tel" required></label></div>'
             '<div class="two"><label>Şehir<input type="text" name="city" autocomplete="address-level2"></label><label>Portfolyo veya LinkedIn <small>(isteğe bağlı)</small><input type="url" name="link" placeholder="https://"></label></div>'
             '<label>Özgeçmiş <small>(PDF, DOC, DOCX, en fazla 5 MB)</small><input type="file" name="cv" accept=".pdf,.doc,.docx,application/pdf"></label>'
             '<label>Kısa not<textarea name="message" rows="3" maxlength="1500"></textarea></label>'
             '<div class="hp" aria-hidden="true"><label>Web sitesi<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>'
             '<label class="ck"><input type="checkbox" name="kvkk" value="1" required><span>Kişisel verilerimin başvuru sürecinde işlenmesine ilişkin <a href="/kvkk.html" target="_blank" rel="noopener">aydınlatma metnini</a> okudum.</span></label>'
             '<div class="ac2"><button type="button" class="kzbtn" data-kapat>Vazgeç</button><button type="submit" class="kzbtn p">Başvuruyu gönderin</button></div></form>'
             '<div class="kzok" hidden><b>Başvurunuz alındı</b><p>Teşekkür ederiz. Başvurunuzu inceleyip sizinle iletişime geçeceğiz.</p><button type="button" class="kzbtn p">Kapat</button></div></dialog>')
    body += '<script src="/v9/kariyer.js?v=%s" defer></script>' % V
    shell("kariyer.html", "Kariyer: açık pozisyonlar ve iş başvurusu | OnlineKaydet",
          "OnlineKaydet'te açık pozisyonlar: yazılım, destek, satış, pazarlama ve tasarım. Özgeçmişinizle online başvurun.", "Kariyer", body)


# ------------------------------------------------------------------ ORTAK YAMALAR
MM_NEW = lambda cls, id_: (
    '<div class="%s mm" id="%s"><!--mm-->'
    '<div class="mm-try v2"><span class="mm-rz"><b>7 GÜN</b><small>ÜCRETSİZ</small></span><p class="mm-t1">Satın almadan önce deneyin</p>'
    '<p class="mm-t2">Kart bilgisi istenmez. Üç adımda kendi sitenizi ve panelinizi görün.</p>'
    '<ul class="mm-ad"><li><i>1</i>Demo hesabınızı açın</li><li><i>2</i>Sektörünüzü ve temanızı seçin</li><li><i>3</i>Sipariş ve randevuları panelde izleyin</li></ul>'
    '<a class="mm-cta" href="/demo.html">7 gün ücretsiz deneyin <i>→</i></a><p class="mm-not">Beğenmezseniz hesabınız kendiliğinden durur.</p></div>'
    '<nav class="mm-l" aria-label="Mobil menü">'
    '<details><summary>Ürün</summary><div><a href="/web-sitesi.html">Web sitesi</a><a href="/e-ticaret.html">E-ticaret</a><a href="/is-takibi.html">Randevu ve iş takibi</a><a href="/muhasebe-ve-stok.html">Muhasebe ve stok</a><a href="/ozellikler.html">Tüm özellikler</a></div></details>'
    '<details><summary>Çözümler</summary><div><a href="/cozumler.html#web">Web sitesi</a><a href="/cozumler.html#eticaret">E-ticaret</a><a href="/cozumler.html#baglanti">Pazaryeri ve bağlantılar</a><a href="/cozumler.html#is">Randevu ve iş takibi</a><a href="/cozumler.html#para">Muhasebe ve stok</a><a class="mm-all" href="/cozumler.html">Tüm çözümler</a></div></details>'
    '<a href="/temalar.html">Temalar</a><a href="/sektorler.html">Sektörler</a><a href="/fiyatlar.html">Paketler ve fiyatlar</a>'
    '<details><summary>Kaynaklar</summary><div><a href="/bilgi-bankasi.html">Bilgi bankası</a><a href="/blog.html">Blog</a><a href="/entegrasyonlar.html">Entegrasyonlar</a><a href="/hesaplama-araclari.html">Hesaplama araçları</a><a href="/destek.html">Destek</a></div></details>'
    '<details><summary>Kurumsal</summary><div><a href="/neden-onlinekaydet.html">Neden OnlineKaydet</a><a href="/hakkimizda.html">Hakkımızda</a><a href="/kariyer.html">Kariyer</a><a href="/bayilik.html">Bayilik</a><a href="/iletisim.html">İletişim</a></div></details></nav>'
    '<div class="mm-bt"><div class="mm-c"><a href="tel:+905444444004">Hemen arayın</a><a class="wa" href="https://wa.me/905444444004">WhatsApp</a></div><a class="mm-in" href="/uye-girisi">Üye girişi</a></div>'
    '<!--/mm--></div>') % (cls, id_)
OLD = [(re.compile(r'<div class="nxm(?: mm)?" id="nxm">.*?(?:<!--/mm-->)?</div>(?=<!--/nxh-->)', re.S), "nxm", "nxm"),
       (re.compile(r'<div class="mmenu(?: mm)?" id="mmenu">.*?(?:<!--/mm-->)?</div>(?=\s*<main)', re.S), "mmenu", "mmenu")]
KURUMSAL_DD = ('<details><summary>Kurumsal</summary><div class="dd"><a href="/neden-onlinekaydet.html">Neden OnlineKaydet<small>İddialı olduğumuz alanlar</small></a><a href="/hakkimizda.html">Hakkımızda</a>'
               '<a href="/kariyer.html">Kariyer<small>Açık pozisyonlar</small></a><a href="/bayilik.html">Bayilik</a><a href="/iletisim.html">İletişim</a></div></details>')
FLICKER = '<style id="kz-fl">html:not([data-kok]) [data-kamp] [data-k]{visibility:hidden}</style><noscript><style>[data-kamp] [data-k]{visibility:visible!important}</style></noscript>'
HEADADD = '<link rel="stylesheet" href="/v9/kurumsal.css?v=%s">' % V


def yama(t):
    o = t
    for rx, cls, id_ in OLD:
        t = rx.sub(lambda m: MM_NEW(cls, id_), t, count=1)
    # masaüstü menü
    m = re.search(r'<nav aria-label="Ana menü">(.*?)</nav>', t, re.S)
    if m and "/cozumler.html" not in m.group(1):
        nav = m.group(1)
        nav = nav.replace('<a href="/temalar.html">Temalar</a>', '<a href="/cozumler.html">Çözümler</a><a href="/temalar.html">Temalar</a>', 1)
        nav = re.sub(r'<a href="/iletisim\.html">İletişim</a>\s*$', KURUMSAL_DD, nav.rstrip()) if nav.rstrip().endswith('<a href="/iletisim.html">İletişim</a>') else nav
        t = t.replace(m.group(0), '<nav aria-label="Ana menü">' + nav + '</nav>', 1)
    # alt bilgi
    fi = t.find("<footer")
    if fi > -1 and "/kariyer.html" not in t[fi:]:
        f = t[fi:]
        f = f.replace('<a href="/temalar.html">Temalar</a>', '<a href="/cozumler.html">Çözümler</a><a href="/temalar.html">Temalar</a>', 1)
        f = f.replace('<a href="/hakkimizda.html">Hakkımızda</a>', '<a href="/neden-onlinekaydet.html">Neden OnlineKaydet</a><a href="/hakkimizda.html">Hakkımızda</a><a href="/kariyer.html">Kariyer</a>', 1)
        f = f.replace('<a href="/cerez-politikasi.html">Çerez politikası</a>', '<a href="/cerez-politikasi.html">Çerez politikası</a><a href="#cerez" data-cerez-ac>Çerez tercihleri</a>', 1)
        t = t[:fi] + f
    # baş kısım
    if "kurumsal.css" not in t:
        t = t.replace("</head>", HEADADD + "</head>", 1)
    if "data-kamp" in t and 'id="kz-fl"' not in t:
        t = t.replace("</head>", FLICKER + "</head>", 1)
    t = re.sub(r'<link rel="stylesheet" href="/v9/mm\.css[^"]*">', '<link rel="stylesheet" href="/v9/mm.css?v=3">', t)
    # çerez betiği: izle.js'den önce
    if "/v9/cerez.js" not in t and "</body>" in t:
        if '<script src="/izle.js"' in t:
            t = t.replace('<script src="/izle.js"', '<script src="/v9/dunya-nokta.js?v=2" defer></script><script src="/v9/cerez.js?v=%s" defer></script><script src="/izle.js"' % V, 1)
        else:
            t = t.replace("</body>", '<script src="/v9/dunya-nokta.js?v=2" defer></script><script src="/v9/cerez.js?v=%s" defer></script></body>' % V, 1)
    return t


if __name__ == "__main__":
    cozumler(); neden(); kariyer()
    n = 0
    for f in pathlib.Path(".").glob("*.html"):
        a = f.read_text(encoding="utf-8")
        b = yama(a)
        if b != a:
            f.write_text(b, encoding="utf-8"); n += 1
    print(n, "sayfa güncellendi")
