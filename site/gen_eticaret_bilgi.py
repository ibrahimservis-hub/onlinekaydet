#!/usr/bin/env python3
"""E-ticaret bilgi bankası: merkez sayfa + 7 rehber. Çalıştır: python3 site/gen_eticaret_bilgi.py
İçerik özgündür; yasal ve platform bilgileri genel düzeyde tutuldu, kesin şart ve oranlar için resmi kaynağa yönlendirilir."""
import os, re, json, html
import gen_seo_karsilastirma as G
page, faq, faq_ld, cta, sec, e = G.page, G.faq, G.faq_ld, G.cta, G.sec, G.e
TARIH = '24 Kasım 2026'
STIL = ('<style>.rh{padding:48px 0 12px}.rh figure{margin:0 auto 34px;max-width:980px}.rh figure img{width:100%;height:auto;border-radius:14px;display:block}'
 '.rh .art h2{font:700 28px/1.2 var(--fd,inherit);margin:40px 0 12px;letter-spacing:-.01em}.rh .art h3{font:700 20px/1.3 var(--fd,inherit);margin:24px 0 8px}'
 '.rh .art p,.rh .art li{line-height:1.75}.rh .toc{border:1px solid #d9dce6;border-radius:12px;padding:18px 22px;margin:0 0 30px;background:#fff}.rh .toc b{display:block;margin-bottom:8px}'
 '.rh .toc ol{margin:0;padding-left:20px;line-height:1.9}.rh .not{border-left:3px solid #e8456e;padding:4px 0 4px 16px;margin:22px 0;color:#3b4152}.rh .meta{font-size:14px;color:#6a7082;margin:-6px 0 22px}'
 '.rhub{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;max-width:1200px;margin:0 auto;padding:0 24px}.rhub a{display:block;text-decoration:none;color:inherit;border:1px solid #dde0ea;border-radius:14px;overflow:hidden;background:#fff;transition:transform .2s,box-shadow .2s}'
 '.rhub a:hover{transform:translateY(-3px);box-shadow:0 14px 30px -20px rgba(10,12,15,.45)}.rhub img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}.rhub div{padding:18px 20px 22px}.rhub h3{font:700 20px/1.25 var(--fd,inherit);margin:0 0 8px}.rhub p{margin:0;color:#4a5160;line-height:1.6;font-size:15.5px}'
 '@media(max-width:900px){.rhub{grid-template-columns:1fr 1fr}}@media(max-width:600px){.rhub{grid-template-columns:1fr}.rh .art h2{font-size:24px}}</style>')
IMG = lambda n: '/v9/img/nx/%s.webp' % n
A = {}   # slug -> dict
def L(href, t): return '<a href="%s">%s</a>' % (href, t)
SOURCES = {}
def art(slug, title, h1, desc, lead, img, alt, secs, faqs, kisa, kapak):
    A[slug] = dict(title=title, h1=h1, desc=desc, lead=lead, img=img, alt=alt, secs=secs, faqs=faqs, kisa=kisa, kapak=kapak)

# ---------------------------------------------------------------- 1
art('e-ticaret-nasil-yapilir', 'E-ticaret nasıl yapılır? Başlangıçtan satışa 9 adım | OnlineKaydet',
 'E-ticaret nasıl yapılır? Başlangıçtan ilk satışa 9 adım',
 'E-ticaret nasıl yapılır: ürün seçimi, işletme türü, site ya da pazaryeri, ödeme, kargo, yasal sayfalar ve ilk satış için sıralı 9 adım. Küçük işletmeler için rehber.',
 'İnternetten satışa başlamak için büyük bir sermayeye değil, doğru sıraya ihtiyaç var. Aşağıdaki dokuz adım, işe sıfırdan başlayan bir esnafın ilk siparişine kadar karşılaşacağı işleri sıraya koyuyor.',
 'ofis-gece', 'Akşam saatlerinde ofiste panel ekranları üzerinde çalışan ekip',
 [('Önce ne satacağınıza karar verin', '<p>Satacağınız ürünü ya da hizmeti üç soruyla sınayın: kimin için, hangi sorunu çözüyor, aynı şeyi satanlardan neden sizden alsınlar? Mevcut bir dükkânınız varsa en kolay başlangıç, zaten sattığınız ve müşterinizin sık sorduğu ürünlerdir. Elinizde stok olmayan bir ürüne sıfırdan girecekseniz küçük bir ürün grubuyla başlayıp satışa bakarak genişletin.</p>'),
  ('İşletme türünü ve vergi durumunu netleştirin', '<p>Düzenli satış yapıyorsanız şahıs işletmesi ya da şirket olarak vergi mükellefi olmanız gerekir. Pazaryerleri başvuruda genellikle vergi levhası ister. Hangi türün sizin için uygun olduğu ciro, ürün ve ortak sayısına göre değişir; karar vermeden önce mali müşavirinizle konuşun.</p><p class="not">Bu sayfa genel bilgi verir, vergi ya da hukuk danışmanlığı değildir. Güncel kurallar için Gelir İdaresi Başkanlığı ve Ticaret Bakanlığı kaynaklarına bakın.</p>'),
  ('Satış kanalınızı seçin', '<p>Üç ana yol var: kendi web siteniz, pazaryerleri ve sosyal medya. Kendi siteniz markanızı ve müşteri bilginizi size bırakır, ama ziyaretçiyi getirmek sizin işiniz. Pazaryerleri hazır ziyaretçi sunar, karşılığında komisyon alır ve fiyat rekabetini sertleştirir. Çoğu işletme ikisini birlikte yürütür. Ayrıntı için '+L('/internetten-satis-nasil-yapilir.html','internetten satış nasıl yapılır')+' rehberine bakın.</p>'),
  ('Ürün sayfalarını hazırlayın', '<p>İyi bir ürün sayfası dört şey taşır: net fotoğraf, ürünün ne olduğunu ve ölçüsünü anlatan açıklama, açık fiyat ve teslimat bilgisi. Her ürüne kendi adıyla ve markasıyla başlık yazın; aynı açıklamayı tüm ürünlere kopyalamayın. Arama motorları yinelenen metni değer vermez, müşteri de ayrım yapamaz.</p>'),
  ('Ödeme ve kargoyu bağlayın', '<p>Müşteri kartla ödeyebilmeli ve siparişi takip edebilmeli. Bunun için bir sanal POS ya da ödeme kuruluşu ile kargo firması anlaşması gerekir. Kargoda ürünün ağırlığı ve hacmi (desi) fiyatı belirler; maliyeti hesaplamak için '+L('/desi-hesaplama.html','desi hesaplama aracına')+' bakabilirsiniz.</p>'),
  ('Yasal sayfaları ekleyin', '<p>Online satışta müşteriyi bilgilendirmek zorundasınız. Pratikte şunlar sitede bulunur: mesafeli satış sözleşmesi, ön bilgilendirme formu, iade ve cayma koşulları, gizlilik ve çerez bilgisi, kişisel verilerin korunması aydınlatma metni. Tüketici mevzuatı, mesafeli satışlarda cayma hakkını genel kural olarak 14 gün olarak düzenler; istisnalı ürünler vardır. Metinlerinizi güncel kurallara göre hazırlayın.</p>'),
  ('Siteyi yayına almadan önce kontrol edin', '<ul><li>Telefonda ve bilgisayarda sipariş verip ödemeyi deneyin.</li><li>Fiyat, stok ve kargo ücretinin doğru göründüğüne bakın.</li><li>İletişim, iade ve sözleşme sayfalarının çalıştığını doğrulayın.</li><li>Sipariş e-postasının müşteriye ulaştığını görün.</li></ul>'),
  ('Ziyaretçi getirin', '<p>Site yayında olduğunda satış kendiliğinden başlamaz. İlk haftalarda en kolay üç yol: mevcut müşterilerinize haber vermek, Google işletme profilinizi ve sosyal medya hesaplarınızı siteye bağlamak, kısa bir reklam bütçesiyle hangi ürünün ilgi gördüğünü ölçmek. Uzun vadede ürün sayfalarının arama motorunda bulunması en ucuz ziyaretçi kaynağıdır.</p>'),
  ('Siparişi, stoğu ve parayı tek yerden izleyin', '<p>Sipariş sayısı arttığında Excel ve not defteri yetmez. Sipariş geldiğinde stoğun düşmesi, kargonun hazırlanması ve tahsilatın kasaya işlenmesi aynı yerde olursa hata azalır. OnlineKaydet panelinde site, mağaza, kasa ve rapor aynı veriye bakar; ayrıntı için '+L('/e-ticaret.html','e-ticaret sayfasına')+' göz atın.</p>')],
 [('E-ticaret yapmak için şirket kurmak şart mı?', 'Düzenli ve ticari nitelikte satış yapıyorsanız vergi mükellefiyeti gerekir; pazaryerleri de vergi levhası ister. Hangi türün uygun olduğunu mali müşavirinizle belirleyin.'),
  ('E-ticarete ne kadar bütçeyle başlanır?', 'Bütçe ürüne göre çok değişir. Sabit giderler genelde alan adı, site ya da panel aboneliği, ödeme ve kargo komisyonları ile reklamdır. Önce küçük bir ürün grubuyla başlayıp satış gördükçe büyümek riski azaltır.'),
  ('Kendi sitem mi, pazaryeri mi daha iyi?', 'İkisinin de yeri var. Pazaryeri hızlı ziyaretçi, kendi siteniz marka ve müşteri bilgisi sağlar. Birçok işletme ikisini birlikte kullanır.')],
 'Satış kanalı, ürün sayfası, ödeme, kargo ve yasal sayfalarla sıfırdan e-ticarete başlama adımları.', 'ofis-gece')

# ---------------------------------------------------------------- 2
art('e-ticaret-sitesi-kurmak', 'E-ticaret sitesi kurmak: seçenekler, adımlar ve kontrol listesi | OnlineKaydet',
 'E-ticaret sitesi kurmak: hangi yol size uygun, nasıl yapılır?',
 'E-ticaret sitesi kurmanın üç yolu (hazır altyapı, açık kaynak, özel yazılım), alan adı, tema, ödeme ve kargo adımları ve yayına almadan önce kontrol listesi.',
 'E-ticaret sitesi kurmanın üç yolu var ve her biri farklı bir işletmeye uyar. Önce yolu seçin, sonra aynı adımlardan geçin.',
 'editor-mock', 'Site editöründe tema bölümlerinin düzenlendiği panel ekranı',
 [('Üç yol: hazır altyapı, açık kaynak, özel yazılım', '<h3>Hazır e-ticaret altyapısı</h3><p>Aylık ya da yıllık abonelikle kullandığınız hazır panel. Tema seçer, ürün girer, ödeme ve kargoyu bağlarsınız. Güvenlik, güncelleme ve barındırma sağlayıcıdadır. Yazılım bilmeyen işletmeler için en kısa yoldur.</p><h3>Açık kaynak kurulum</h3><p>WooCommerce gibi sistemleri kendi barındırmanıza kurarsınız. Esneklik yüksektir, ama bakım, güvenlik ve güncelleme sizin sorumluluğunuzdadır; bir geliştiriciye ihtiyaç duyarsınız.</p><h3>Özel yazılım</h3><p>Her şeyi ihtiyacınıza göre yazdırırsınız. En esnek ve en pahalı yoldur; çok özel iş akışı olan büyük işletmelere uygundur.</p>'),
  ('Alan adı ve güvenli bağlantı', '<p>Markanıza yakın, kısa ve yazması kolay bir alan adı seçin. Site mutlaka güvenli bağlantı (https) ile açılmalı; ödeme alınan bir sitede bu zorunludur. Hazır altyapılarda genellikle sertifika hazır gelir, bu yüzden sizi ayrıca ilgilendirmez.</p>'),
  ('Tema seçimi', '<p>Tema, sitenin ilk izlenimidir. Sektörünüze uygun, telefonda rahat gezilen ve metin ile görseli sonradan değiştirmenize izin veren bir tema seçin. OnlineKaydet\'te '+L('/temalar.html','78 iş kolu için hazır temalar')+' bulunur; yazı, yazı tipi ve görselleri panelden kendiniz değiştirirsiniz.</p>'),
  ('Ürünleri girin', '<p>Her ürüne ayrı başlık, açıklama, fiyat, stok ve görsel girin. Varyantlı ürünlerde (beden, renk) her seçeneğin stoğunu ayrı tutun. Kategori yapısını müşterinizin ürünü nasıl aradığına göre kurun, sizin depo düzeninize göre değil.</p>'),
  ('Ödeme, kargo ve fatura', '<p>Müşteri için bir ödeme yöntemi (kart, havale), size için bir kargo anlaşması gerekir. Sipariş geldiğinde fatura ve kargo etiketi elle hazırlanıyorsa küçük hacimde sorun olmaz, ama hacim arttıkça bu adımların otomatik olması zaman kazandırır. Pazaryeri kullanıyorsanız siparişlerin '+L('/entegrasyonlar.html','tek listede')+' toplanması işinizi kolaylaştırır.</p>'),
  ('Yasal sayfalar', '<p>Mesafeli satış sözleşmesi, iade ve cayma bilgisi, gizlilik ve çerez metni ile kişisel verilerin korunması aydınlatma metni sitede bulunmalı. Metinlerin güncel mevzuata uygunluğunu bir uzmana kontrol ettirin.</p>'),
  ('Yayına almadan önce kontrol listesi', '<ul><li>Telefonda ve bilgisayarda tam bir sipariş deneyin.</li><li>Bütün sayfalarda başlık ve açıklama yazılı olsun (arama motoru için).</li><li>Sayfa hızını ölçün; büyük görselleri küçültün.</li><li>İletişim ve iade bilgileri açıkça görünsün.</li><li>Sipariş ve ödeme e-postaları müşteriye ulaşıyor mu bakın.</li></ul>')],
 [('E-ticaret sitesi kurmak ne kadar sürer?', 'Hazır altyapıda tema seçimi, ürün girişi ve ödeme-kargo bağlantısıyla birkaç gün içinde yayına alınabilir. Süreyi asıl belirleyen ürün sayısı ve görsellerin hazır olmasıdır.'),
  ('Kodlama bilmeden e-ticaret sitesi kurulur mu?', 'Evet. Hazır altyapılar tema, ürün yükleme, ödeme ve kargo adımlarını panelden, yazılım bilgisi olmadan yapmanıza izin verir.'),
  ('Kendi sitemin SEO\'su nasıl olur?', 'Her ürüne ve kategoriye özgün başlık ve açıklama yazın, sayfaları hızlı tutun ve işletme bilgilerinizi Google işletme profiliyle uyumlu girin.')],
 'Hazır altyapı, açık kaynak ve özel yazılım yollarının karşılaştırması; alan adı, tema, ürün, ödeme ve yasal sayfa adımları.', 'editor-mock')

# ---------------------------------------------------------------- 3
art('internetten-satis-nasil-yapilir', 'İnternetten satış nasıl yapılır? Kanallar, fiyat ve kargo | OnlineKaydet',
 'İnternetten satış nasıl yapılır? Kanallar, fiyatlama ve teslimat',
 'İnternetten satış yapmanın yolları: kendi site, pazaryeri ve sosyal medya. Fiyatı komisyon, kargo ve KDV ile hesaplama, stok takibi ve ilk siparişlerde dikkat edilecekler.',
 'İnternetten satış, ürünü doğru kanalda göstermek ve her satışın sonunda para kalacak şekilde fiyatlamaktır. Aşağıda üç kanalı ve fiyat hesabını sade bir dille anlatıyoruz.',
 'analiz-cam', 'Satış ve sipariş verilerinin cam bir yüzeyde analiz ekranı olarak görünümü',
 [('Üç satış kanalı', '<h3>Kendi web siteniz</h3><p>Marka, fiyat ve müşteri bilgisi sizde kalır. Komisyon yoktur, ama ziyaretçiyi siz getirirsiniz. Sürekli müşteriniz varsa ya da markanızı kurmak istiyorsanız vazgeçilmezdir.</p><h3>Pazaryerleri</h3><p>Trendyol, Hepsiburada ve N11 gibi platformlar hazır ziyaretçi sunar. Karşılığında kategoriye göre komisyon alır, kargo ve iade kurallarını belirler. Hızlı başlangıç için uygundur. Ayrıntı için '+L('/trendyolda-satis-yapmak.html','Trendyol\'da satış yapmak')+' rehberine bakın.</p><h3>Sosyal medya</h3><p>Instagram, Pinterest ve YouTube ürünü gösterir, müşteriyi siteye ya da mağazaya yönlendirir. Doğrudan satış her ürün için uygun değildir; ürünün görsel çekiciliği belirler. '+L('/pinterest-nedir.html','Pinterest nedir')+' yazısına göz atabilirsiniz.</p>'),
  ('Fiyatı nasıl hesaplarsınız?', '<p>Satış fiyatı şu kalemleri karşılamalı: ürün maliyeti, KDV, kargo, pazaryeri komisyonu, ödeme komisyonu, ambalaj ve iade payı. Hesabı bir kez yaptığınızda ürün başına net kâr görünür. Pazaryeri komisyonlarını hesaplamak için '+L('/komisyon-hesaplama.html','komisyon hesaplama')+', kargo için '+L('/desi-hesaplama.html','desi hesaplama')+' araçlarımızı kullanabilirsiniz.</p><p class="not">Komisyon oranları kategoriye ve zamana göre değişir; güncel oranı pazaryerinin satıcı panelinden doğrulayın.</p>'),
  ('Stok ve sipariş takibi', '<p>Aynı ürünü birden fazla kanalda satıyorsanız stok tek yerden yönetilmezse aynı ürünü iki kez satma riski doğar. Sipariş geldiğinde stoğun otomatik düşmesi ve tüm kanalların tek listede görünmesi bu riski azaltır.</p>'),
  ('Teslimat ve iade', '<p>Müşteri, ürünün ne zaman geleceğini bilmek ister. Sitenizde kargo süresi ve ücreti açık yazılı olsun. İade sürecini önceden belirleyin; cayma hakkı genel kural olarak mesafeli satışlarda geçerlidir ve kargo masrafı, ürünün durumu gibi ayrıntılar mevzuata göre değişir.</p>'),
  ('İlk siparişlerde dikkat edilecekler', '<ul><li>İlk 10 siparişi elle takip edin; hangi adımda zaman kaybettiğinizi görürsünüz.</li><li>Müşteriye sipariş alındı, kargoya verildi, teslim edildi mesajı gönderin.</li><li>Gelen soruları kaydedin; ürün sayfasını bu sorulara göre güncelleyin.</li><li>Fiyatı yalnızca rakibe bakarak değil, kendi maliyetinizle belirleyin.</li></ul>')],
 [('İnternetten satış yapmak için ne gerekir?', 'Bir satış kanalı (site, pazaryeri ya da ikisi), ürün fotoğrafı ve açıklaması, ödeme yöntemi, kargo anlaşması ve düzenli satış için vergi mükellefiyeti.'),
  ('Evden internetten satış yapılır mı?', 'Yapılır; ürününüzün saklanması, paketlenmesi ve kargoya verilmesi için bir düzen kurmanız yeterli. Düzenli ve ticari satışta vergi yükümlülüğünüzü mali müşavirinize danışın.'),
  ('Hangi ürünler internette iyi satılır?', 'Müşterinin fotoğrafla karar verebildiği, kargosu kolay ve iade riski düşük ürünler başlangıç için kolaydır. Mevcut müşterinizin sizden zaten sorduğu ürünlerle başlamak en güvenli yoldur.')],
 'Site, pazaryeri ve sosyal medya kanalları; komisyon, kargo ve KDV ile fiyatlama; stok ve iade.', 'analiz-cam')

# ---------------------------------------------------------------- 4
art('trendyolda-satis-yapmak', 'Trendyol\'da satış yapmak: başvuru, hazırlık ve entegrasyon | OnlineKaydet',
 'Trendyol\'da satış yapmak: başvuru adımları ve dikkat edilecekler',
 'Trendyol\'da satış yapmak için başvuru, hazırlık ve ürün girişi adımları. Komisyon ve kargo kalemleri, stok ve fiyat takibi, siparişleri tek panelde toplama.',
 'Trendyol, ürününüzü hazır bir müşteri kitlesine gösterir. Başvurudan ilk siparişe kadar hangi işlerin sizi beklediğini sıraya koyduk.',
 'panel-radar', 'Pazaryeri siparişlerinin tek listede toplandığı panel ekranı',
 [('Başvuru ve hazırlık', '<p>Satıcı başvurusu Trendyol\'un satıcı sayfasından yapılır. Başvuru formunda işletme türüne göre belgeler istenir; vergi levhası ve işletme bilgileri bunların başında gelir. Güncel belge listesi ve koşullar Trendyol\'un satıcı başvuru sayfasında yazılıdır, değişebildiği için başvurmadan önce oradan doğrulayın.</p>'),
  ('Ürün girişi', '<p>Ürünler marka, kategori ve özellik alanlarıyla girilir. Eksik ya da hatalı özellik, ürünün aramada çıkmasını zorlaştırır. Görseller platformun kurallarına uygun, net ve ürünü doğru gösteren fotoğraflar olmalıdır. Marka bilgisi gerektiren kategorilerde marka onayı süreci olabilir.</p>'),
  ('Maliyet kalemleri', '<p>Pazaryerinde net kâr, satış fiyatından şunlar düştükten sonra kalır: ürün maliyeti, platform komisyonu (kategoriye göre değişir), kargo, ambalaj, iade ve KDV. Hesabı yapmadan fiyat belirlemeyin. '+L('/komisyon-hesaplama.html','Komisyon hesaplama')+' aracıyla farklı oranları deneyebilirsiniz; gerçek oranı satıcı panelinizden doğrulayın.</p>'),
  ('Kargo ve sipariş süreci', '<p>Siparişi belirlenen süre içinde hazırlayıp kargoya vermek, satıcı performansınızı doğrudan etkiler. Kargo anlaşmanızı ve paketleme düzeninizi baştan kurun. Desi hesabını bilmek kargo maliyetini öngörmenizi sağlar: '+L('/desi-hesaplama.html','desi hesaplama')+'.</p>'),
  ('Stok ve fiyat takibi', '<p>Aynı ürünü hem kendi sitenizde hem pazaryerinde satıyorsanız stok tek havuzdan yönetilmelidir; aksi halde olmayan ürünü satmak iptal ve puan kaybına yol açar. OnlineKaydet\'te Trendyol, Hepsiburada ve N11 siparişleri aynı listeye düşer, stok tek havuzdan yönetilir; ayrıntı için '+L('/entegrasyonlar.html','entegrasyonlar')+' sayfasına bakın.</p>'),
  ('Pazaryerine bağımlı kalmamak', '<p>Pazaryeri müşteriyi platforma bağlar, siz müşterinin bilgisine sınırlı sahip olursunuz. Kendi sitenizi de açarak tekrar satış yapabileceğiniz bir müşteri tabanı oluşturabilirsiniz. İki kanalı birlikte yürütmek için '+L('/e-ticaret-sitesi-kurmak.html','e-ticaret sitesi kurmak')+' rehberine göz atın.</p>')],
 [('Trendyol\'da satış yapmak için şirket gerekir mi?', 'Başvuruda işletme türüne göre belgeler istenir ve vergi mükellefiyeti genellikle aranır. Hangi türün uygun olduğunu Trendyol\'un güncel koşullarından ve mali müşavirinizden öğrenin.'),
  ('Trendyol komisyonu ne kadar?', 'Komisyon kategoriye ve dönemsel kurallara göre değişir. Güncel oran için satıcı panelinizi kontrol edin; hesabınızı bu orana göre yapın.'),
  ('Trendyol siparişlerini kendi panelimde toplayabilir miyim?', 'OnlineKaydet\'te Trendyol, Hepsiburada ve N11 siparişleri aynı listede toplanır ve stok tek havuzdan yönetilir.')],
 'Satıcı başvurusu, ürün girişi, komisyon ve kargo kalemleri, stok takibi ve pazaryerine bağımlı kalmama.', 'panel-radar')

# ---------------------------------------------------------------- 5
art('pinterest-nedir', 'Pinterest nedir? İşletmeler için kullanımı ve satışa katkısı | OnlineKaydet',
 'Pinterest nedir, işletmeler için nasıl kullanılır?',
 'Pinterest nedir, pin ve pano ne demek? İş hesabı açma, ürün pinleri, web sitesini bağlama ve Pinterest ile siteye ziyaretçi çekme adımları.',
 'Pinterest, insanların görsel fikir aradığı ve beğendiklerini panolarda biriktirdiği bir platformdur. Sosyal ağlardan farkı, kişileri değil fikirleri takip etmeye dayanmasıdır; bu yüzden ürün keşfi için kullanılır.',
 'ekip-2', 'Çalışma masasında ürün fotoğrafları ve notlarla çalışan ekip',
 [('Pin, pano ve arama', '<p>Pin, bir görseldir ve bir web sayfasına bağlanır. Pano, pinleri konuya göre topladığınız koleksiyondur. Kullanıcılar bir fikir aradığında (örneğin "küçük balkon düzeni") sonuçlardan pin kaydeder; beğendiği pin onu pinin bağlı olduğu siteye götürür. Bu yüzden Pinterest bir arama motoru gibi de çalışır.</p>'),
  ('İşletmeler için ne işe yarar?', '<p>Görseli güçlü ürünler (ev, dekorasyon, moda, yemek, hediye, el işi) için ürün keşfini sağlar. Pin, siteye doğrudan bağlantı verdiği için ürün sayfalarına ziyaretçi getirir. Pinler uzun süre yeniden bulunabildiği için içerik bir kez hazırlanır, zamanla ziyaretçi getirmeye devam eder.</p>'),
  ('İş hesabı ve siteyi bağlama', '<p>Önce bir Pinterest iş hesabı açın. Profilinizde marka adı, kısa açıklama ve web sitesi adresi olsun. Pinterest, web sitenizin sahibi olduğunuzu doğrulamanızı ister; doğrulama sitenizde Pinterest\'in verdiği bir kodu kullanmayı gerektirir. Bu adımı sitenizi yöneten kişiye yaptırın.</p>'),
  ('İyi bir pin nasıl olur?', '<ul><li>Dikey ve net bir görsel kullanın.</li><li>Başlıkta ve açıklamada insanların aradığı kelimeleri yazın.</li><li>Pini ilgili ürün ya da yazı sayfasına bağlayın, ana sayfaya değil.</li><li>Her ürün için birkaç farklı görsel hazırlayın.</li></ul>'),
  ('Sonucu nasıl ölçersiniz?', '<p>Pinterest iş hesabı, pinlerin görüntülenme ve tıklanma sayılarını gösterir. Sitenizde ise hangi sayfalara ziyaretçi geldiğini analiz aracınızdan izleyin. Hangi pinler tıklanıyorsa o ürün ve tarz için içerik üretmeye devam edin.</p>'),
  ('Pinterest ile e-ticaret sitenizi birleştirin', '<p>Ürün sayfalarınızda düzgün görsel, başlık ve açıklama varsa Pinterest\'ten gelen ziyaretçi sipariş verebilir. '+L('/e-ticaret-sitesi-kurmak.html','E-ticaret sitesi kurmak')+' ve '+L('/internetten-satis-nasil-yapilir.html','internetten satış')+' rehberlerimiz bu hazırlığı anlatır.</p>')],
 [('Pinterest ücretsiz mi?', 'Hesap açmak ve pin paylaşmak ücretsizdir. Reklam vermek ücretlidir ve isteğe bağlıdır.'),
  ('Pinterest ile para kazanılır mı?', 'Doğrudan değil: Pinterest ziyaretçi getirir. Kazanç, getirdiği ziyaretçinin sitenizde ürün almasıyla oluşur.'),
  ('Hangi işletmeler için uygundur?', 'Ürünü fotoğrafla anlatılan işletmeler için: dekorasyon, moda, hediye, yemek, el işi, düğün ve benzerleri.')],
 'Pin ve pano nedir, iş hesabı nasıl açılır, ürün sayfalarına nasıl ziyaretçi getirilir.', 'ekip-2')

# ---------------------------------------------------------------- 6
art('online-is-fikirleri', 'Online iş fikirleri: evden başlanabilecek 10 fikir | OnlineKaydet',
 'Online iş fikirleri: evden başlanabilecek 10 fikir ve nelere dikkat etmeli',
 'Online iş fikirleri: e-ticaret, el işi ürün, dijital ürün, kurs, danışmanlık, yerel hizmet web sitesi ve daha fazlası. Her fikirde gereken yatırım ve riskler.',
 'Bu liste "hızlı zengin olma" vaadi içermez. Her fikirde neyin gerektiğini, neye dikkat edilmesi gerektiğini yazdık; seçmeden önce kendi becerinize ve zamanınıza uyup uymadığına bakın.',
 'ekip-3', 'Küçük bir ekip dizüstü bilgisayar başında iş planı üzerinde çalışıyor',
 [('1. Bildiğiniz bir ürünü internetten satmak', '<p>Mevcut dükkânınız ya da tedarikçiniz varsa en yakın fikir budur. Önce küçük bir ürün grubuyla başlayın; ayrıntıyı '+L('/e-ticaret-nasil-yapilir.html','e-ticaret nasıl yapılır')+' yazısında bulabilirsiniz.</p>'),
  ('2. El yapımı ve butik ürün', '<p>Takı, mum, seramik, tekstil, kişiye özel hediye. Fotoğrafı ve hikâyesi güçlü ürünler Instagram ve Pinterest ile iyi tanıtılır. Üretim kapasitenizi baştan hesaplayın; talep gelince yetişememek müşteriyi kaybettirir.</p>'),
  ('3. Dijital ürün ve şablon', '<p>E-kitap, şablon, tasarım dosyası gibi ürünlerde stok ve kargo yoktur. Karşılığında rekabet yüksektir, ürünün gerçekten fark yaratması gerekir.</p>'),
  ('4. Kurs ve eğitim', '<p>Bir alanda uzmansanız bunu kurs ya da birebir ders olarak satabilirsiniz. Güven burada her şeydir: referans ve örnek çalışma gösterin.</p>'),
  ('5. Danışmanlık ve uzman hizmeti', '<p>Muhasebe, tasarım, yazılım, çeviri, sağlıklı yaşam gibi alanlarda uzmanlığınızı randevulu hizmete çevirebilirsiniz. Müşterinin sizi bulabilmesi için bir web sitesi ve online randevu formu gerekir; '+L('/sektorler.html','sektörünüze uygun hazır siteleri')+' inceleyin.</p>'),
  ('6. Yerel hizmet işletmesi için web sitesi', '<p>Tesisat, kombi servisi, temizlik, nakliye gibi yerel hizmetlerde müşteri "yakınımdaki" diye arar. Sitesi ve randevu formu olan işletme bulunur. Bu işe başlamak isteyen ustalar için '+L('/web-sitesi.html','web sitesi ve iş takibi')+' bir arada çalışır.</p>'),
  ('7. İçerik üretimi (YouTube, blog, podcast)', '<p>Gelir gecikmeli gelir; önce izleyici ya da okuyucu kitlesi oluşturursunuz. Ayrıntı için '+L('/youtube-para-kazanma.html','YouTube\'da para kazanma')+' yazısına bakın.</p>'),
  ('8. Pazaryerinde satıcılık', '<p>Hazır ziyaretçi sunar, ama komisyon ve rekabet vardır. Fiyatı hesaplamadan girmeyin: '+L('/trendyolda-satis-yapmak.html','Trendyol\'da satış yapmak')+'.</p>'),
  ('9. Serbest çalışma (freelance)', '<p>Yazı, çeviri, grafik, ses, programlama gibi becerilerle projeye göre çalışırsınız. Başlangıçta portföy oluşturmak için küçük işler almak gerekir.</p>'),
  ('10. Abonelik ya da tekrarlayan hizmet', '<p>Bakım paketi, aylık kutu, düzenli temizlik gibi düzenli gelir doğuran işler müşteri takibini ve hatırlatmayı gerektirir; panelde müşteri kaydı ve hatırlatma varsa yönetmek kolaylaşır.</p>'),
  ('Seçerken kendinize sorun', '<ul><li>Bu işe haftada kaç saat ayırabilirim?</li><li>İlk üç ayda hiç gelir olmasa idare edebilir miyim?</li><li>Müşteriyi nereden bulacağım?</li><li>Vergi ve yasal yükümlülüklerim neler?</li></ul>')],
 [('Hangi online iş fikri en kolay?', 'Zaten bildiğiniz ürünü ya da hizmeti çevrimiçi sunmak en az öğrenme eğrisi isteyendir. Sıfırdan bir alana girmek zaman alır.'),
  ('Sermayesiz online iş olur mu?', 'Hizmet ve içerik fikirlerinde başlangıç parası düşüktür, ama zaman ve emek gerekir. Ürün satışında stok ve reklam bütçesi gerekir.'),
  ('Online işten ne kadar kazanılır?', 'Bu kişiye, alana ve emeğe göre çok değişir; belirli bir kazanç vaat edemeyiz. Düzenli gelir doğuran işlerde vergi yükümlülüğünüzü de unutmayın.')],
 'E-ticaret, el işi, dijital ürün, kurs, danışmanlık ve yerel hizmet gibi 10 fikir; seçerken sorulacak sorular.', 'ekip-3')

# ---------------------------------------------------------------- 7
art('youtube-para-kazanma', 'YouTube\'da para kazanma: şartlar, yollar ve işletmeler için kullanım | OnlineKaydet',
 'YouTube\'da para kazanma: şartlar, kazanç yolları ve işletmeler için kullanım',
 'YouTube\'da para kazanmanın şartları (abone ve izlenme saati), YouTube İş Ortağı Programı, reklam dışındaki kazanç yolları ve işletmenin YouTube\'dan siteye müşteri çekmesi.',
 'YouTube\'da para kazanmak için önce YouTube İş Ortağı Programı\'na kabul edilmeniz gerekir. Aşağıdaki şartlar YouTube\'un yardım sayfasından alınmıştır; Google şartları güncelleyebildiği için başvurmadan önce YouTube Studio\'daki güncel metni okuyun.',
 'cihaz-mock', 'Telefon ekranında bir içerik kanalının yönetim görünümü',
 [('Hangi şartlar aranıyor?', '<p>YouTube\'un yardım sayfasına göre reklam geliri için şunlar aranıyor: 1.000 abone ve ikisinden biri (son 365 günde uzun videolarda 4.000 geçerli izlenme saati ya da son 90 günde 10 milyon geçerli Shorts görüntülemesi). Kanal üyelikleri gibi bazı özellikler için daha düşük bir eşik var: 500 abone, son 90 günde 3 herkese açık yükleme ve ikisinden biri (365 günde 3.000 izlenme saati ya da 90 günde 3 milyon Shorts görüntülemesi).</p><p>Ayrıca 18 yaşında olmanız ya da ödemeleri yönetecek 18 yaşından büyük bir yasal vasiniz bulunması, program\'ın bulunduğu bir ülkede yaşamanız ve reklamverenlere uygun içerik kuralına uymanız gerekir.</p><p class="not">Google, YouTube İş Ortağı Programı şartlarında 1 Şubat 2027 tarihinden itibaren güncellemeler yapacağını duyurdu. Güncel eşikler için YouTube Studio\'daki metni kontrol edin.</p>'),
  ('Kazanç yolları', '<ul><li><b>Reklam geliri:</b> izleme sayfası ve Shorts akışı reklamlarından pay.</li><li><b>YouTube Premium geliri:</b> Premium abonelerin izlemesinden pay.</li><li><b>Kanal üyelikleri:</b> izleyicilerin aylık ödemesi.</li><li><b>Süper Chat, Süper Etiketler ve Süper Teşekkür:</b> izleyicilerin ödediği ek özellikler.</li><li><b>Alışveriş:</b> kendi ürünlerinizi kanalınızda gösterme.</li></ul><p>Her özelliğin kendi uygunluk koşulu vardır.</p>'),
  ('Reklam dışında kazanç', '<p>Birçok içerik üreticisi gelirinin asıl kaynağını YouTube dışında kurar: kendi ürününü satmak, hizmet vermek, kurs satmak ya da ürün tanıtımı yapmak. Küçük bir işletme için en gerçekçi yol, videolarla güven kazanıp müşteriyi siteye ya da mağazaya yönlendirmektir.</p>'),
  ('İşletmeler YouTube\'u nasıl kullanır?', '<ul><li>Ürünün nasıl kullanıldığını ya da servisin nasıl yapıldığını gösteren kısa videolar çekin.</li><li>Sık sorulan sorulara video ile cevap verin.</li><li>Açıklama kısmına ürün sayfanızın bağlantısını koyun.</li><li>Videoları sitenizdeki ilgili ürün ve hizmet sayfalarına gömün.</li></ul><p>Sitenizin hazır olması için '+L('/e-ticaret-sitesi-kurmak.html','e-ticaret sitesi kurmak')+' ya da '+L('/web-sitesi.html','web sitesi')+' sayfalarına bakın.</p>'),
  ('Vergi', '<p>YouTube\'dan elde edilen gelir vergiye tabi olabilir. Yerel vergi kurumunuza ya da mali müşavirinize danışın; YouTube da bu konuda yerel vergi kurumuna başvurmanızı önerir.</p>')],
 [('YouTube\'da para kazanmak için kaç abone gerekir?', 'Reklam geliri için YouTube\'un yardım sayfasında 1.000 abone ve belirli izlenme ölçütü yazıyor. Daha düşük eşikli özellikler için 500 abone isteniyor. Güncel şartları YouTube Studio\'dan doğrulayın.'),
  ('Kısa videolar (Shorts) ile kazanılır mı?', 'Shorts görüntülemeleri programa uygunlukta bir ölçüt olarak sayılır. Kazanç yöntemleri uygunluk şartlarına bağlıdır.'),
  ('Bir işletme için YouTube gerekli mi?', 'Zorunlu değil. Ürünü ya da hizmeti görsel olarak anlatmak daha kolaysa müşteri güveni kazanmak için güçlü bir kanaldır.')],
 'İş Ortağı Programı şartları, kazanç yolları ve işletmenin YouTube\'dan müşteri çekmesi.', 'cihaz-mock')

ORDER = ['e-ticaret-nasil-yapilir', 'e-ticaret-sitesi-kurmak', 'internetten-satis-nasil-yapilir', 'trendyolda-satis-yapmak', 'pinterest-nedir', 'online-is-fikirleri', 'youtube-para-kazanma']
def build_article(slug):
    a = A[slug]
    toc = '<div class="toc"><b>Bu yazıda</b><ol>%s</ol></div>' % ''.join('<li><a href="#b%d">%s</a></li>' % (i + 1, e(h)) for i, (h, _) in enumerate(a['secs']))
    body = ''.join('<h2 id="b%d">%s</h2>%s' % (i + 1, e(h), p) for i, (h, p) in enumerate(a['secs']))
    ilgili = [s for s in ORDER if s != slug][:3]
    rel = '<h2>İlgili rehberler</h2><ul>%s</ul>' % ''.join('<li><a href="/%s.html">%s</a></li>' % (s, e(A[s]['h1'])) for s in ilgili)
    main = ('%s<section class="rh"><div class="w"><figure><img src="%s" alt="%s" width="1600" height="900" loading="eager"></figure><article class="art"><p class="meta">Güncelleme: %s · OnlineKaydet</p>'
            '<p><b>%s</b></p>%s%s%s</article></div></section>' % (STIL, IMG(a['img']), e(a['alt']), TARIH, a['lead'], toc, body, rel))
    main += faq('Sık sorulan sorular', a['faqs']) + cta('Satışa başlamak için panelinizi açalım', 'Siteniz, mağazanız, siparişleriniz ve kasanız tek panelde. 7 gün ücretsiz deneyin.')
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": a['h1'], "description": a['desc'], "dateModified": "2026-11-24", "author": {"@type": "Organization", "name": "OnlineKaydet"},
           "publisher": {"@type": "Organization", "name": "OnlineKaydet"}, "mainEntityOfPage": "https://onlinekaydet.com/%s.html" % slug}, faq_ld(a['faqs'])]
    page(slug + '.html', a['title'], a['desc'], '<a href="e-ticaret-bilgi-bankasi.html">E-ticaret bilgi bankası</a> / %s' % e(a['h1']), e(a['h1']), e(a['lead']), main, ld=ld)
def build_hub():
    cards = ''.join('<a href="/%s.html"><img src="%s" alt="%s" width="800" height="450" loading="lazy"><div><h3>%s</h3><p>%s</p></div></a>' % (s, IMG(A[s]['kapak']), e(A[s]['alt']), e(A[s]['h1']), e(A[s]['kisa'])) for s in ORDER)
    body = STIL + '<section class="rh"><div class="rhub">%s</div></section>' % cards + sec('Blog ve servis rehberleri', '<p>Servis işletmeleri için yazılarımız <a href="/blog.html">blogda</a>. Pazaryeri komisyonu ve kargo maliyeti için <a href="/komisyon-hesaplama.html">komisyon hesaplama</a> ve <a href="/desi-hesaplama.html">desi hesaplama</a> araçlarını kullanabilirsiniz.</p>', tint=True) + cta('Satışa başlamak için panelinizi açalım', 'Siteniz, mağazanız, siparişleriniz ve kasanız tek panelde. 7 gün ücretsiz deneyin.')
    page('e-ticaret-bilgi-bankasi.html', 'E-ticaret bilgi bankası: e-ticaret nasıl yapılır, site kurmak, Trendyol, Pinterest | OnlineKaydet',
         'E-ticaret bilgi bankası: e-ticaret nasıl yapılır, e-ticaret sitesi kurmak, internetten satış, Trendyol\'da satış, Pinterest, online iş fikirleri ve YouTube\'da para kazanma rehberleri.',
         'E-ticaret bilgi bankası', 'E-ticaret bilgi bankası', 'İnternetten satışa başlayanlar ve satışını büyütenler için yedi rehber. Her yazı sade anlatılır, bağlantıları sitemizdeki araçlara gider.', body)
if __name__ == '__main__':
    build_hub()
    for s in ORDER: build_article(s)
    print(len(ORDER) + 1, 'sayfa')
