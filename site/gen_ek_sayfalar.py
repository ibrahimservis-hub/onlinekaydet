#!/usr/bin/env python3
"""Ek sayfalar: entegrasyon grup sayfaları, sözlük, şablonlar. Çalıştır: python3 site/gen_ek_sayfalar.py
Kural: yalnız genel bilgi ve entegrasyonlar.html'deki listeler; özellik, fiyat, hacim iddiası uydurulmaz."""
import os, re, json, html
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
src = open('gen_seo_karsilastirma.py', encoding='utf-8').read()
pre = src[:src.index('RIV = {')]
exec(compile(pre, 'gen_seo_pre', 'exec'))
G = json.load(open(os.path.join(D, 'ent_gruplar.json'), encoding='utf-8'))
NEW = []
_page = page
ACT = '<a class="bt" href="/iletisim.html#teklif">Ücretsiz deneyin</a><a class="bt l" href="tel:05444444004">Hemen arayın</a>'
def page(*a, **k):
    k.setdefault('acts', ACT); return _page(*a, **k)
def reg(fn): NEW.append(fn); return fn
def um(s): return html.unescape(s)

# ---------- 1. Entegrasyon grup sayfaları ----------
GRUP = {
 'pos': dict(fn='sanal-pos-entegrasyonu.html', ad='Sanal POS entegrasyonu',
   ne='Sanal POS, web sitenizde ya da ödeme linkinde müşterinin kartını çekmeye yarayan altyapıdır. Para kartın bankasından size, ödeme kuruluşu üzerinden gelir.',
   adim=['Ödeme kuruluşunda hesabınızı açın; anahtar bilgilerini kendi panelinizden alırsınız.', 'OnlineKaydet panelinde Bağlantılar ekranından ilgili kartı açıp bilgileri girin.', 'Önce deneme (test) ortamıyla bir ödeme deneyin; sorun yoksa canlı ortama geçin.'],
   dikkat=['Gizli anahtarı kimseyle paylaşmayın; panelde yalnız son hanesi görünür.', 'Taksit ve iade seçenekleri ödeme kuruluşunuzla yaptığınız sözleşmeye bağlıdır.', 'Havale ve kapıda ödeme de aynı listede; müşteri ödeme ekranında bu seçenekleri görür.'],
   sss=[('Hangi sanal POS’u seçmeliyim?', 'Komisyon, taksit seçenekleri, para yatış süresi ve iade koşulları kuruluşa göre değişir; bunlar ödeme kuruluşunun sözleşmesinde yazar. Birden çok teklif alıp aynı kriterlerle karşılaştırın.'), ('Birden fazla ödeme yöntemi açabilir miyim?', 'Listedeki yöntemler ayrı ayrı bağlanır; kart, havale ve kapıda ödemeyi birlikte sunmak mümkündür.')]),
 'kargo': dict(fn='kargo-entegrasyonu.html', ad='Kargo entegrasyonu',
   ne='Kargo entegrasyonu, siparişten gönderi kaydı açmanızı, barkod almanızı ve takip numarasını müşteriye iletmenizi sağlar; kargo firmasının sitesine tek tek girmenize gerek kalmaz.',
   adim=['Kargo firmasıyla anlaşmanızın bilgilerini (müşteri kodu, kullanıcı adı, şifre ya da anahtar) hazırlayın.', 'Panelde Bağlantılar ekranından firmayı seçip bu bilgileri girin.', '“Test et” ile bağlantıyı deneyin; ardından bir siparişten gönderi oluşturun.'],
   dikkat=['Hangi bilgilerin gerektiği firmaya göre değişir; kargo firmanızın temsilcisinden anlaşma bilgilerinizi isteyin.', 'Birden çok firmayla çalışıyorsanız hepsini bağlayıp siparişe göre seçebilirsiniz.', 'Tek anlaşmayla birden çok kargoyu sunan aracı firmalar da listede.'],
   sss=[('Kargo anlaşmam yoksa kullanabilir miyim?', 'Entegrasyon sizin kargo anlaşmanızla çalışır. Anlaşmanız yoksa aracı firmalar listesine bakabilirsiniz; koşulları firmalarla görüşmeniz gerekir.'), ('Takip numarası müşteriye nasıl gider?', 'Gönderi oluşturulunca takip numarası siparişe işlenir; müşteriye mesajla iletilmesi mesaj bağlantılarınıza bağlıdır.')]),
 'efatura': dict(fn='e-fatura-e-arsiv-entegrasyonu.html', ad='E-fatura ve e-arşiv entegrasyonu',
   ne='E-fatura ve e-arşiv entegrasyonu, kestiğiniz satışların faturasını özel entegratör ya da GİB portalı üzerinden elektronik ortama aktarmak içindir.',
   adim=['Mali müşavirinizle hangi belge türünü (e-fatura, e-arşiv) kullanmanız gerektiğini netleştirin.', 'Entegratörünüzün size verdiği kullanıcı bilgilerini panelde Bağlantılar ekranına girin.', '“Test et” ile bağlantıyı deneyin ve ilk faturayı deneme olarak kesin.'],
   dikkat=['Resmi fatura yükümlülüğü ve belge türü mükellefiyetinize bağlıdır; bunu mali müşaviriniz belirler.', 'Bu sayfa vergi danışmanlığı değildir.', 'Listede özel entegratörler ve GİB e-Arşiv portalı birlikte yer alır.'],
   sss=[('E-fatura ile e-arşiv farkı nedir?', 'Kısaca: e-fatura e-fatura mükellefleri arasında, e-arşiv ise e-fatura mükellefi olmayan alıcılara kesilir. Hangisinin size uyduğunu mali müşaviriniz söyler.')]),
 'erp': dict(fn='muhasebe-erp-entegrasyonu.html', ad='Muhasebe ve ERP entegrasyonu',
   ne='Muhasebe ve ERP programlarıyla bağlantı, aynı veriyi iki yerde elle girmenizi azaltmak için vardır: cari, stok ve satış hareketleri tek yönde ya da iki yönde aktarılır.',
   adim=['Kullandığınız muhasebe programının bağlantı (API ya da servis) bilgilerini programın yöneticisinden alın.', 'Bu bilgileri panelde Bağlantılar ekranındaki ilgili karta girin.', '“Test et” ile deneyin; önce az sayıda kayıtla kontrol edin.'],
   dikkat=['Bağlantının hangi veriyi aktardığı programa göre değişir; kurulumdan önce kapsamı netleştirin.', 'Bazı programlarda API erişimi ayrıca açtırılır; program sağlayıcınıza sorun.', 'Listede 18 program var; listede olmayan programınız için bizimle iletişime geçin.'],
   sss=[('Muhasebe programımı değiştirmem gerekir mi?', 'Hayır. Bağlantı mevcut programınızla çalışır; amaç çift giriş yapmayı azaltmaktır.')]),
 'sms': dict(fn='sms-whatsapp-eposta-entegrasyonu.html', ad='SMS, WhatsApp ve e-posta entegrasyonu',
   ne='Mesaj bağlantıları, müşterinize randevu hatırlatması, servis durumu ya da kampanya metnini kendi SMS paketiniz, WhatsApp Business hesabınız ya da e-posta sunucunuz üzerinden göndermek içindir.',
   adim=['SMS sağlayıcınızdan API bilgilerini ve onaylı başlığınızı (gönderici adı) alın.', 'Panelde Bağlantılar ekranından sağlayıcıyı seçip bilgileri girin.', 'Kendi numaranıza deneme mesajı göndererek test edin.'],
   dikkat=['Ticari ileti göndermek için alıcının onayı (İYS ve KVKK kapsamı) gerekir; mesaj içeriğinden siz sorumlusunuz.', 'Gönderim ücretini SMS sağlayıcınız keser.', 'WhatsApp Business için Meta’nın kuralları geçerlidir.'],
   sss=[('Mesaj şablonlarını kendim yazabilir miyim?', 'Evet; servis durumu ve hatırlatma gibi mesaj şablonları panelden düzenlenir. Örnek metinler için şablonlar sayfasına bakın.')]),
 'pazaryeri': dict(fn='pazaryeri-entegrasyonu.html', ad='Pazaryeri ve yemek platformu entegrasyonu',
   ne='Pazaryeri bağlantısı, ürünlerinizi Trendyol, Hepsiburada gibi platformlara göndermenizi ve oradan gelen siparişleri tek listede görmenizi sağlar. Yemek platformları için siparişler aynı listeye düşer.',
   adim=['Pazaryerinde satıcı hesabınızı açın ve API bilgilerinizi kendi paneliniz üzerinden alın.', 'OnlineKaydet panelinde Bağlantılar ekranından ilgili platformu seçip bilgileri girin.', 'Önce tek bir ürünle deneyin, sonra toplu gönderime geçin.'],
   dikkat=['Pazaryerinin kategori, marka ve komisyon kuralları platforma aittir; ürün bilgilerinin platform şartlarına uygun olması gerekir.', 'Pazaryeri entegrasyonları e-ticaret kullanımı içindir; paket kapsamı için paketler sayfasına bakın.', 'Stok ve fiyat güncellemelerini kontrol ederek başlayın.'],
   sss=[('Aynı ürünü birden çok pazaryerinde satabilir miyim?', 'Evet, platformları ayrı ayrı bağlayabilirsiniz; her platformun kendi kuralları geçerlidir.')]),
 'olcum': dict(fn='olcum-reklam-entegrasyonu.html', ad='Ölçüm, reklam ve giriş bağlantıları',
   ne='Ölçüm ve reklam bağlantıları, sitenize gelen ziyaretçiyi ve reklamdan gelen talepleri görmek için; giriş bağlantıları ise müşterinin Google ya da Facebook hesabıyla üye olması içindir.',
   adim=['İlgili hizmette (örneğin Google Analytics) hesabınızı açıp kimlik numaranızı alın.', 'Panelde Bağlantılar ekranından kimliği girin.', 'Kaydettikten sonra sitenizde birkaç sayfa gezip ölçüm panelinde görünmesini kontrol edin.'],
   dikkat=['Ölçüm araçları ziyaretçi verisi topladığı için çerez izni ve aydınlatma metninizi güncel tutun.', 'Reklam dönüşümü için ilgili reklam hesabında dönüşüm tanımlamanız gerekir.'],
   sss=[('Hangi ölçüm aracını kullanmalıyım?', 'Ziyaretçi sayısı ve kaynak için Google Analytics, arama performansı için Search Console yeterli bir başlangıçtır; reklam veriyorsanız ilgili platformun pikselini ekleyin.')]),
 'diger': dict(fn='diger-entegrasyonlar.html', ad='Diğer entegrasyonlar',
   ne='Google İşletme Profili, UYAP, canlı destek, webhook ve toplantı bağlantıları gibi diğer bağlantılar bu grupta.',
   adim=['İlgili hizmetten gerekli kimlik ya da adresi alın.', 'Panelde Bağlantılar ekranından girin.', '“Test et” ile deneyin.'],
   dikkat=['Webhook ve API, kendi yazılımınızla bağlantı kurmak isteyenler içindir.', 'Her bağlantı için gerekli bilgiyi hizmet sağlayıcınızdan alın.'],
   sss=[('Listede olmayan bir hizmeti bağlayabilir miyim?', 'Webhook ve API ile kendi sisteminize bildirim gönderebilirsiniz. Başka bir hizmet için bize yazın.')]),
}
def grup_sayfa(k, g):
    ad_g, alt, items = G[k]
    liste = ''.join('<li><b>%s</b>: %s</li>' % (um(a), um(b)) for a, b in items)
    diger = ''.join('<a href="%s">%s</a>' % (v['fn'], v['ad']) for kk, v in GRUP.items() if kk != k)
    body = (STIL + sec('Nedir?', '<p>%s</p>' % g['ne'])
            + sec('Bağlanabilen servisler (%d)' % len(items), '<ul>%s</ul><p class="mini">Liste panelin Bağlantılar ekranıyla aynıdır. Tüm gruplar için <a href="entegrasyonlar.html">Entegrasyonlar</a> sayfasına bakın.</p>' % liste, tint=True)
            + sec('Panelden nasıl bağlanır?', '<ol style="max-width:760px;line-height:1.8;padding-left:20px">%s</ol>' % ''.join('<li>%s</li>' % x for x in g['adim']))
            + sec('Bilmeniz gerekenler', '<ul>%s</ul>' % ''.join('<li>%s</li>' % x for x in g['dikkat']), tint=True)
            + faq('Sık sorulan sorular', g['sss']) 
            + sec('Diğer entegrasyon grupları', '<p style="line-height:2.2">%s</p>' % ' · '.join(['<a href="%s">%s</a>' % (v['fn'], v['ad']) for kk, v in GRUP.items() if kk != k]))
            + cta())
    desc = '%s: %s bağlanabilir. %s Panelden nasıl bağlandığı ve dikkat edilecekler.' % (g['ad'], ', '.join(um(a) for a, b in items[:5]), g['ne'][:90])
    return page(g['fn'], '%s | OnlineKaydet' % g['ad'], desc[:300], '<a href="entegrasyonlar.html">Entegrasyonlar</a> / ' + g['ad'], g['ad'], '%d servisle bağlanır. Panelden nasıl bağlandığını ve nelere dikkat edeceğinizi anlatıyoruz.' % len(items), body, ld=faq_ld(g['sss']))

# ---------- 2. Sözlük ----------
TERIM = [
 ('Servis kaydı', 'Bir cihazın ya da işin servise alındığı andan teslimine kadar tutulan kayıt: müşteri, cihaz, arıza, yapılan işlem, tutar.'),
 ('Servis fişi', 'Cihazı teslim alırken müşteriye verilen, kaydın numarasını ve teslim bilgilerini taşıyan belge.'),
 ('Takip numarası', 'Her servis kaydına verilen benzersiz numara; müşteri durumunu bu numarayla sorar.'),
 ('Seri numarası', 'Üreticinin cihaza verdiği tekil numara. Garanti ve geçmiş sorgusunda kullanılır.'),
 ('Garanti belgesi', 'Yapılan işin ya da satılan ürünün hangi süreyle güvence altında olduğunu yazan belge.'),
 ('Fiyat teklifi', 'İş başlamadan önce müşteriye sunulan, kalemleri ve toplam tutarı gösteren yazılı fiyat.'),
 ('İş emri', 'Teknisyene verilen, yapılacak işin tanımı, adresi ve zamanını içeren görev kaydı.'),
 ('Cari hesap', 'Bir müşteri ya da tedarikçi ile aranızdaki borç ve alacak hareketlerinin tutulduğu hesap.'),
 ('Alacak takibi', 'Tahsil edilmemiş tutarların, vadesiyle birlikte izlenmesi.'),
 ('Tahsilat', 'Müşteriden para alma işlemi; nakit, kart ya da havale olabilir.'),
 ('Gün sonu', 'Günün sonunda kasadaki tahsilat ve giderlerin toplanıp kontrol edilmesi.'),
 ('Kasa', 'Nakit giriş ve çıkışlarının tutulduğu defter.'),
 ('Prim', 'Çalışana, yaptığı işe ya da satışa göre ödenen ek tutar.'),
 ('Avans', 'Maaştan önce çalışana yapılan ve sonra mahsup edilen ödeme.'),
 ('Randevu', 'Müşteri ile belirlenen tarih ve saatte yapılacak iş ya da görüşme.'),
 ('Bakım hatırlatma', 'Periyodik bakımı yaklaşan müşteriye önceden gönderilen bilgi mesajı.'),
 ('Sanal POS', 'İnternet üzerinden kartla tahsilat almayı sağlayan altyapı.'),
 ('3D Secure', 'Kartla ödemede müşterinin bankasından gelen ek doğrulama adımı (genelde SMS ile gelen kod).'),
 ('Taksit', 'Kartla yapılan ödemenin birden çok aya bölünmesi.'),
 ('Ödeme linki', 'Müşteriye gönderilen, tıklayınca kart ödemesi yapılan bağlantı.'),
 ('Havale / EFT', 'Banka hesabından hesaba para gönderme; müşteri açıklamaya sipariş numarasını yazar.'),
 ('Kapıda ödeme', 'Ürün ya da hizmet teslim edilirken tahsilat yapılması.'),
 ('e-Fatura', 'Elektronik ortamda düzenlenen ve iletilen fatura; yükümlülük mükellefiyete bağlıdır.'),
 ('e-Arşiv', 'E-fatura mükellefi olmayanlara kesilen, elektronik ortamda saklanan fatura.'),
 ('GİB', 'Gelir İdaresi Başkanlığı; e-belge portallarını işleten kurum.'),
 ('KVKK', 'Kişisel Verilerin Korunması Kanunu; müşteri ad, telefon ve adres gibi verilerin işlenme kurallarını belirler.'),
 ('İYS', 'İleti Yönetim Sistemi; ticari elektronik ileti onaylarının tutulduğu sistem.'),
 ('Pazaryeri', 'Birçok satıcının ürününü tek çatıda sattığı platform; Trendyol ve Hepsiburada gibi.'),
 ('API', 'İki yazılımın birbiriyle veri alıp verebilmesi için sunulan arayüz.'),
 ('Webhook', 'Bir olay olunca başka bir sisteme otomatik bildirim gönderen bağlantı.'),
 ('Alan adı', 'Sitenizin internetteki adresi; örneğin firmaadi.com.'),
 ('SEO', 'Sitenin arama sonuçlarında daha görünür olması için yapılan düzenlemeler.'),
 ('Barkod / QR etiket', 'Cihaz ya da ürüne yapıştırılan, okutulunca ilgili kaydı açan etiket.'),
 ('Cari bakiye', 'Bir müşteri ya da tedarikçiyle borç ve alacak farkı.'),
 ('Sektör terimi', 'Aynı işlemin sektöre göre farklı adı: servis formu, dava dosyası, muayene, iş emri gibi.'),
]
def sozluk():
    TERIM.sort(key=lambda x: x[0].lower().replace('ı', 'i'))
    li = ''.join('<div class="r" id="%s"><b>%s</b><span>%s</span></div>' % (re.sub(r'[^a-z0-9]+', '-', a.lower().translate(str.maketrans('çğıöşü', 'cgiosu'))).strip('-'), a, b) for a, b in TERIM)
    body = (STIL + '<section class="kk"><div class="w"><div class="kt">%s</div><p class="mini">Tanımlar genel bilgi niteliğindedir; vergi ve hukuk konularında mali müşaviriniz ya da avukatınıza danışın.</p></div></section>' % li + cta())
    ld = {"@context": "https://schema.org", "@type": "DefinedTermSet", "name": "Servis ve işletme sözlüğü", "hasDefinedTerm": [{"@type": "DefinedTerm", "name": a, "description": b} for a, b in TERIM]}
    return page('sozluk.html', 'Servis ve işletme sözlüğü: %d terim | OnlineKaydet' % len(TERIM), 'Servis kaydı, cari hesap, sanal POS, e-arşiv, KVKK, İYS gibi servis ve işletme terimlerinin kısa, açık tanımları.',
                'Sözlük', 'Servis ve işletme sözlüğü', 'Servis işinde ve küçük işletmede sık geçen %d terimin kısa tanımı.' % len(TERIM), body, ld=ld)

# ---------- 3. Şablonlar ----------
YAZ = ('<style>.sb{max-width:860px;border:1px solid #cfd3de;border-radius:10px;background:#fff;padding:28px}.sb h3{margin:0 0 14px;font:700 20px var(--fd,inherit)}'
       '.sb .sat{display:grid;grid-template-columns:200px 1fr;gap:12px;padding:10px 0;border-bottom:1px dashed #c5c9d6}.sb .sat span:last-child{min-height:22px}'
       '.sb pre{white-space:pre-wrap;font:15px/1.7 var(--fb,inherit);margin:0}.kopya{margin-top:14px}@media print{header,nav,footer,.pgh,.cta,.nxh,.nxf,.nxm,.mbar,.kk:not(.yz){display:none!important}.sb{border:0}}'
       '@media(max-width:700px){.sb .sat{grid-template-columns:1fr}}</style>')
def alanlar(ls): return '<div class="sb">%s</div>' % ''.join('<div class="sat"><b>%s</b><span></span></div>' % x for x in ls)
SAB = [
 dict(fn='servis-formu-sablonu.html', ad='Servis formu şablonu', ba='Servis formu şablonu: yazdırılabilir, boş form',
   desc='Yazdırıp doldurabileceğiniz boş servis formu şablonu: müşteri, cihaz, arıza, yapılan işlem, tutar ve imza alanları.',
   lead='Cihazı teslim alırken doldurulacak alanlar. Yazdırın ya da PDF olarak kaydedin.',
   govde=alanlar(['Form / takip no', 'Tarih', 'Müşteri adı soyadı', 'Telefon', 'Adres', 'Cihaz türü ve marka', 'Model ve seri no', 'Bildirilen arıza', 'Teslim alınan aksesuar', 'Yapılan işlem', 'Kullanılan parça', 'Toplam tutar', 'Tahmini teslim tarihi', 'Müşteri imzası', 'Teknisyen imzası']),
   not_='Önemli: Formun alt kısmına KVKK aydınlatma ve cihaz saklama süresi gibi kendi koşullarınızı ekleyin. Hukuki metin için avukatınıza danışın.',
   sss=[('Servis formunda mutlaka ne olmalı?', 'Müşteri bilgisi, cihaz ve seri numarası, bildirilen arıza, teslim alınan aksesuarlar, tarih ve iki tarafın imzası temel alanlardır.')]),
 dict(fn='fiyat-teklifi-sablonu.html', ad='Fiyat teklifi şablonu', ba='Fiyat teklifi şablonu: yazdırılabilir',
   desc='Yazdırılabilir boş fiyat teklifi şablonu: kalemler, birim fiyat, KDV, toplam, geçerlilik süresi ve onay alanı.',
   lead='İş başlamadan önce müşteriye verilecek teklifin alanları.',
   govde=alanlar(['Teklif no ve tarih', 'Müşteri adı / firma', 'İşin kısa tanımı', 'Kalem 1 (adet, birim fiyat)', 'Kalem 2 (adet, birim fiyat)', 'Kalem 3 (adet, birim fiyat)', 'Ara toplam', 'KDV', 'Genel toplam', 'Teklif geçerlilik süresi', 'Ödeme koşulu', 'Müşteri onayı (imza, tarih)']),
   not_='KDV oranını ve kalemleri kendi işinize göre doldurun; oranlar için mali müşavirinize danışın.',
   sss=[('Teklif ne kadar süre geçerli olmalı?', 'Süreyi siz belirlersiniz; parça fiyatları sık değişiyorsa kısa tutmak mantıklıdır. Teklifin üzerinde tarihi ve geçerlilik süresini açıkça yazın.')]),
 dict(fn='garanti-belgesi-sablonu.html', ad='Garanti belgesi şablonu', ba='Servis garanti belgesi şablonu: yazdırılabilir',
   desc='Yaptığınız işe ya da değiştirdiğiniz parçaya verilen garanti için yazdırılabilir boş belge şablonu.',
   lead='Yapılan işin hangi kapsamda ve süreyle güvence altında olduğunu yazılı verin.',
   govde=alanlar(['Belge no ve tarih', 'Müşteri adı', 'Cihaz ve seri no', 'Yapılan iş / değişen parça', 'Garanti başlangıç tarihi', 'Garanti süresi', 'Garanti kapsamı', 'Kapsam dışı durumlar', 'Firma yetkilisi imzası ve kaşe']),
   not_='Garanti koşulları sizin taahhüdünüzdür; yasal asgari süre ve haklar için avukatınıza ya da ilgili mevzuata bakın.',
   sss=[('Garanti belgesi şart mı?', 'Satılan ürünler için yasal yükümlülükler vardır; servis işinde verdiğiniz güvence ise yazılı olduğunda anlaşmazlığı azaltır. Ayrıntı için mevzuata ya da avukatınıza danışın.')]),
]
MESAJ = [
 ('Randevu hatırlatma', 'Merhaba {ad}, {tarih} saat {saat} için randevunuz var. Değişiklik için bu mesaja yanıt verebilirsiniz.'),
 ('Cihaz teslim alındı', 'Merhaba {ad}, cihazınız {takip_no} numarasıyla servisimize alındı. Durumunu bu numarayla sorabilirsiniz.'),
 ('Fiyat teklifi', 'Merhaba {ad}, {takip_no} numaralı servis için teklifimiz {tutar} TL. Onayınızı bekliyoruz.'),
 ('Cihaz hazır', 'Merhaba {ad}, {takip_no} numaralı cihazınız hazır. Teslim için bizi arayabilir ya da uğrayabilirsiniz.'),
 ('Bakım hatırlatma', 'Merhaba {ad}, cihazınızın periyodik bakım zamanı yaklaşıyor. Randevu için bize yazabilirsiniz.'),
 ('Ödeme hatırlatma', 'Merhaba {ad}, {tutar} TL tutarındaki ödemeniz için hatırlatma. Sorunuz varsa yanıtlayın.'),
 ('Memnuniyet', 'Merhaba {ad}, hizmetimizden memnun kaldınız mı? Görüşünüz bizim için değerli.'),
]
def sablon(s):
    body = (YAZ + STIL + '<section class="kk yz"><div class="w">%s<p class="mini">%s</p><p class="kopya"><a class="bt" href="#" onclick="window.print();return false">Yazdır</a></p></div></section>' % (s['govde'], s['not_'])
            + faq('Sık sorulan sorular', s['sss']) + cta('Bu formları panelden otomatik üretin', 'Servis formu, teklif ve makbuz panelde sektörünüzün kendi adıyla hazırlanır. 7 gün ücretsiz deneyin.'))
    return page(s['fn'], s['ba'] + ' | OnlineKaydet', s['desc'], '<a href="sablonlar.html">Şablonlar</a> / ' + s['ad'], s['ad'], s['lead'], body, ld=faq_ld(s['sss']))
def mesaj_sayfa():
    li = ''.join('<div class="r"><b>%s</b><span>%s</span></div>' % (a, html.escape(b)) for a, b in MESAJ)
    sss = [('{ad} gibi alanlar ne işe yarar?', 'Süslü parantezli alanlar, mesaj gönderilirken müşterinin kendi bilgisiyle değişen yer tutuculardır. Kendi mesajınıza göre düzenleyebilirsiniz.'),
           ('Toplu mesaj atabilir miyim?', 'Ticari amaçlı toplu ileti için alıcıların onayı gerekir (İYS ve KVKK). Servis durumu gibi bilgilendirme mesajları ayrı değerlendirilir; emin değilseniz uzmana danışın.')]
    body = (STIL + '<section class="kk"><div class="w"><div class="kt">%s</div><p class="mini">Metinleri kendi işinize göre değiştirin. Bu sayfa hukuki danışmanlık değildir.</p></div></section>' % li + faq('Sık sorulan sorular', sss) + cta())
    return page('musteri-mesaj-sablonlari.html', 'Müşteri mesaj şablonları: randevu, teslim, ödeme | OnlineKaydet', 'Randevu hatırlatma, cihaz teslim, fiyat teklifi, bakım ve ödeme hatırlatma mesajları için kopyalayıp kullanabileceğiniz örnek şablonlar.',
                '<a href="sablonlar.html">Şablonlar</a> / Mesaj şablonları', 'Müşteri mesaj şablonları', 'SMS ve WhatsApp için kısa, net %d örnek mesaj.' % len(MESAJ), body, ld=faq_ld(sss))
def hub():
    kart = [('servis-formu-sablonu.html', 'Servis formu', 'Cihaz teslim alırken doldurulan boş form.'), ('fiyat-teklifi-sablonu.html', 'Fiyat teklifi', 'Kalem, KDV ve toplamlı teklif formu.'),
            ('garanti-belgesi-sablonu.html', 'Garanti belgesi', 'Yapılan işe verilen yazılı güvence.'), ('musteri-mesaj-sablonlari.html', 'Mesaj şablonları', 'Randevu, teslim ve ödeme hatırlatma metinleri.')]
    li = ''.join('<div class="r"><b><a href="%s">%s</a></b><span>%s</span></div>' % k for k in kart)
    body = STIL + '<section class="kk"><div class="w"><div class="kt">%s</div><p class="mini">Hepsi örnektir; kendi işinize ve mevzuata göre uyarlayın. Panelde bu belgeler sektörünüzün adlarıyla hazır gelir.</p></div></section>' % li + cta()
    return page('sablonlar.html', 'Servis şablonları: form, teklif, garanti, mesaj | OnlineKaydet', 'Yazdırılabilir servis formu, fiyat teklifi, garanti belgesi ve müşteri mesaj şablonları.', 'Şablonlar', 'Servis şablonları', 'Servis işinde en çok gereken dört belge ve mesaj örneği.', body)

def sitemap():
    sm = open('sitemap.xml', encoding='utf-8').read(); add = ''
    for n in NEW:
        u = 'https://onlinekaydet.com/' + n
        if u not in sm: add += '<url><loc>%s</loc></url>\n' % u
    if add: open('sitemap.xml', 'w', encoding='utf-8').write(sm.replace('</urlset>', add + '</urlset>'))
_cta = cta
def cta(*a, **k):
    return _cta(*a, **k).replace('>0544 444 40 04</a>', '>Hemen arayın</a>')
if __name__ == '__main__':
    for k, g in GRUP.items(): reg(grup_sayfa(k, g))
    reg(sozluk()); reg(hub()); reg(mesaj_sayfa())
    for s in SAB: reg(sablon(s))
    sitemap(); print(len(NEW), 'sayfa')
