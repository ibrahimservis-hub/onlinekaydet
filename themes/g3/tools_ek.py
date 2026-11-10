"""Teknik olmayan sektörlerin çalışan araçları (tools.TOOLS biçimi). Hesaplar tarayıcıda yapılır; sonuç 'bize iletin' formuyla firmaya gider.
Sayılar yaklaşık ön tahmindir ve araçta öyle belirtilir; kesin değer yerinde / telefonla netleşir."""
from .tools import N, S, G, C, D, T, R, bakim, steps_tool, checks_tool

TOOLS = {}

# ---- OTO SERVİS
TOOLS['oto.bakim'] = bakim('Araç bakım hatırlatıcı', [('12', 'Yılda bir'), ('6', '6 ayda bir')],
                           ['Yağ ve filtre, fren, lastik ve sıvı seviyeleri kontrol edilir.', 'Üreticinin bakım çizelgesi ve kilometre esastır; kullanım kılavuzuna bakın.'])
TOOLS['oto.kontrol'] = checks_tool('kontrol', 'th', 'Aracım servise ne kadar acil?', 'Fark ettiğiniz belirtileri işaretleyin; aciliyet düzeyini ve ilk adımı görün.', 'Belirtiler',
    [('isik', 'Motor arıza ışığı yanıyor'), ('fren', 'Fren sesi ya da pedal boşluğu var'), ('duman', 'Egzozdan renkli duman çıkıyor'), ('yag', 'Yağ ışığı yandı ya da yağ sızıntısı var'), ('isi', 'Motor ısı göstergesi yükseliyor'),
     ('ses', 'Motordan ya da alttan vuruntu sesi geliyor'), ('akü', 'Marş yavaş basıyor'), ('lastik', 'Lastikte aşınma ya da yan şişme var')],
    {'isik': 2, 'fren': 5, 'duman': 3, 'yag': 5, 'isi': 5, 'ses': 3, 'akü': 2, 'lastik': 3},
    [(0, 'ok', 'Acil bir belirti işaretlenmedi'), (2, 'warn', 'Yakın zamanda servise götürün'), (5, 'bad', 'Aracı kullanmadan servise danışın')],
    {'isik': 'Arıza ışığı bilgisayarlı teşhisle okunur.', 'fren': 'Fren belirtisinde aracı mümkünse kullanmayın; balata ve hidrolik kontrol edilmeli.', 'duman': 'Duman rengi arızanın yerini gösterir; teşhis gerekir.',
     'yag': 'Yağ ışığı yanıyorsa motoru çalıştırmayın; seviyeyi kontrol edin.', 'isi': 'Isı yükseliyorsa durun, motoru kapatın, soğumadan kapak açmayın.', 'ses': 'Vuruntu için alt takım ve motor kontrolü gerekir.',
     'akü': 'Akü ve şarj sistemi test edilmeli.', 'lastik': 'Yan şişme ya da aşırı aşınmada lastik değişmeli.'},
    'Bu liste ön fikir verir; kesin teşhis aracın muayenesiyle yapılır.')

# ---- OTO ÇEKİCİ
TOOLS['cek.varis'] = dict(id='varis', ico='ar', title='Tahmini varış ve bilgi hazırlığı', intro='Konumunuz ile aracın durduğu yer arasındaki mesafeyi girin; tahmini varış süresini ve aramadan önce hazırlayacağınız bilgileri görün.',
    fields=[N('km', 'Ekibin size yaklaşık uzaklığı', 12, 1, 400, 1, 'km'), G('yer', 'Aracın durduğu yer', [('sehir', 'Şehir içi'), ('yol', 'Şehirlerarası yol'), ('otopark', 'Otopark / bodrum')]), G('arac', 'Araç', [('oto', 'Otomobil'), ('tic', 'Hafif ticari'), ('mot', 'Motosiklet')])],
    calc=r"""function(v,H){var sp={sehir:35,yol:70,otopark:30}[v.yer],dk=Math.round(v.km/sp*60+5),L=['Tahmini varış: yaklaşık '+dk+' dakika (trafik ve yoğunluğa göre değişir)','Aramadan önce hazırlayın: tam konum (paylaşım), plaka, araç türü, aracın durumu (tekerlekler dönüyor mu, hasar var mı)'];
if(v.yer==='yol')L.push('Şerit dışına çıkın, dörtlüleri yakın, reflektörü araç arkasına koyun ve yolun dışında bekleyin');if(v.yer==='otopark')L.push('Bodrum katta çıkış yüksekliği ve rampa bilgisini söyleyin; ekip uygun araçla gelsin');if(v.arac==='mot')L.push('Motosiklet için uygun yükleme ekipmanı hazırlanır');
return{tone:'ok',big:dk+' dk',head:'Ön bilgi hazır',lines:L,note:'Süre ön tahmindir; net varış süresi ve fiyat telefonda söylenir.',msg:'Çekici talebi: '+v.km+' km, '+v.yer+', '+v.arac+' → tahmini '+dk+' dk'}}""")
TOOLS['cek.acil'] = steps_tool('acil', 'al', 'Yolda kaldım, ne yapmalıyım?', 'Durumu seçin; güvenliğiniz için ilk adımları görün.', 'Durum',
    [('kaza', 'Kaza oldu'), ('ariza', 'Araç yolda durdu'), ('lastik', 'Lastik patladı'), ('yakit', 'Yakıt bitti'), ('kilit', 'Anahtar içeride kaldı')],
    {'kaza': ('Kaza sonrası adımlar', 'bad', ['Önce yaralı olup olmadığına bakın; yaralı varsa 112\'yi arayın.', 'Dörtlüleri yakın, mümkünse araçları güvenli yere çekin, reflektör koyun.', 'Fotoğraf çekin, tutanak için 155 / jandarma süreçlerini izleyin.', 'Çekici için konumunuzu bize gönderin.'], 'Hasarlı aracı çalıştırmayın.'),
     'ariza': ('Araç yolda durdu', 'warn', ['Dörtlüleri yakın, aracı yolun dışına almaya çalışın.', 'Reflektörü aracın arkasına 30–50 m koyun.', 'Aracın içinde değil, korkuluğun arkasında bekleyin.', 'Konumunuzu paylaşın.'], ''),
     'lastik': ('Lastik patladı', 'warn', ['Direksiyonu sıkı tutun, frene ani basmayın, yavaşlayın.', 'Güvenli yerde durun; yedek lastik ve kriko varsa güvenli zeminde değiştirin.', 'Yan şişmiş ya da yırtılmış lastikle yola devam etmeyin.'], 'Emin değilseniz yol yardım isteyin.'),
     'yakit': ('Yakıt bitti', 'ok', ['Aracı güvenli yere çekin, dörtlüleri yakın.', 'Yakın istasyona yürüyerek gidecekseniz araç kilitli kalsın ve değerli eşya görünmesin.', 'İsterseniz yakıt desteği için bize konum gönderin.'], ''),
     'kilit': ('Anahtar içeride', 'ok', ['Çocuk ya da hayvan içerideyse hemen 112\'yi arayın.', 'Aksi halde araca zarar vermeden açmak için bize ulaşın; açma işlemi ehliyet ve ruhsat kontrolüyle yapılır.'], '')})

# ---- KUAFÖR
TOOLS['kuf.sure'] = dict(id='sure', ico='cal', title='Randevu süresi hesaplayıcı', intro='İstediğiniz işlemleri işaretleyin; ne kadar süreceğini ve randevuya ne zaman gelmeniz gerektiğini görün.',
    fields=[C('c', 'İşlemler', [('kesim', 'Saç kesimi'), ('fon', 'Fön'), ('boya', 'Boya'), ('rofle', 'Röfle / balyaj'), ('sakal', 'Sakal tasarımı'), ('bakim', 'Bakım maskesi')])],
    calc=r"""function(v,H){var M={kesim:45,fon:30,boya:90,rofle:150,sakal:30,bakim:30},a=v.c||[];if(!a.length)return{head:'Yapılacak işlemleri işaretleyin',lines:[]};var t=0;a.forEach(function(k){t+=M[k]||0});
var s=Math.floor(t/60),d=t%60;return{tone:'ok',big:(s?s+' sa ':'')+(d?d+' dk':''),head:'Tahmini randevu süresi',lines:['Saç uzunluğu ve yoğunluğuna göre değişir.','Boya ve röfle için bekleme süresi dahildir.'],note:'Ön tahmindir; uzman kesin süreyi randevuda söyler.',msg:'Randevu hesabı: '+a.join(', ')+' → yaklaşık '+t+' dk'}}""")
TOOLS['kuf.rehber'] = steps_tool('rehber', 'sp', 'Saç bakım rehberi', 'Sorununuzu seçin; evde yapabileceklerinizi ve uzmana ne zaman gelmeniz gerektiğini görün.', 'Sorun',
    [('kuru', 'Saçım kuru ve elektriklenme yapıyor'), ('yagli', 'Saçım çabuk yağlanıyor'), ('boyali', 'Boyalı saçım matlaştı'), ('dokulme', 'Normalden fazla dökülme var'), ('sakal', 'Sakalım batıyor / kaşınıyor')],
    {'kuru': ('Kuru saç', 'ok', ['Sıcak su yerine ılık su kullanın.', 'Haftada 1–2 kez nemlendirici maske uygulayın.', 'Isıtıcılardan önce ısı koruyucu kullanın.'], 'Uçlar çok kırıksa kesim ve bakım için randevu alın.'),
     'yagli': ('Yağlanma', 'ok', ['Şampuanı kafa derisine, bakımı yalnızca uçlara uygulayın.', 'Çok sık ya da çok sıcak yıkamayın.', 'Fırçayı ve yastık kılıfını düzenli temizleyin.'], 'Kaşıntı ve pullanma varsa uzmana danışın.'),
     'boyali': ('Boyalı saç bakımı', 'ok', ['Boya sonrası ilk 48 saat yıkamayın.', 'Renk koruyucu şampuan kullanın.', 'Dip boya için 4–6 haftalık aralık yaygındır; saç yapısına göre değişir.'], 'Renk tonu için randevuda fotoğraf getirin.'),
     'dokulme': ('Saç dökülmesi', 'warn', ['Günlük birkaç tel dökülme normaldir.', 'Aniden artan ya da bölgesel dökülmede bir doktora danışın.'], 'Bu bir tıbbi değerlendirme değildir.'),
     'sakal': ('Sakal bakımı', 'ok', ['Sıcak havluyla cildi yumuşatın, tıraşı kıl yönünde yapın.', 'Sakal yağı ve düzenli şekil vermek batmayı azaltır.', 'Tahriş sürerse tıraşı bırakıp randevu alın.'], '')})

# ---- NAKLİYE
TOOLS['nak.hacim'] = dict(id='hacim', ico='bx', title='Taşıma ön hesabı', intro='Ev büyüklüğünü ve adres bilgilerini girin; yaklaşık ekip ve araç ihtiyacını görün, keşif randevusu alın.',
    fields=[S('oda', 'Ev büyüklüğü', [('1', '1+0 / 1+1'), ('2', '2+1'), ('3', '3+1'), ('4', '4+1 ve üzeri'), ('o', 'Ofis')], '2'), N('kat', 'Çıkış kat sayısı', 3, 0, 30, 1, ''), G('asan', 'Asansör', [('var', 'Var'), ('yok', 'Yok')]), N('km', 'Mesafe', 15, 1, 1500, 1, 'km')],
    calc=r"""function(v,H){var B={1:[2,'Panelvan / küçük kamyonet',3],2:[3,'Kamyonet / orta kamyon',4],3:[4,'Orta kamyon',6],4:[5,'Büyük kamyon',8],o:[4,'Orta / büyük kamyon',7]}[v.oda],ek=0;if(v.asan==='yok'&&v.kat>2)ek=Math.min(3,Math.round((v.kat-2)/2));
var h=B[2]+ek+(v.km>100?3:0);var L=['Ekip: yaklaşık '+B[0]+' kişi','Araç: '+B[1],'Yükleme + taşıma + indirme: yaklaşık '+h+' saat'];if(v.asan==='yok'&&v.kat>2)L.push('Asansör yok ve kat yüksek: dış cephe asansörü değerlendirilebilir');if(v.km>100)L.push('Şehirlerarası taşımada sigorta ve takip bilgisi sözleşmeye yazılır');
return{tone:'ok',big:B[0]+' kişi',head:'Ön hesap hazır',lines:L,note:'Gerçek ihtiyaç eşya miktarına göre değişir; ücretsiz keşifle netleşir.',msg:'Taşıma ön hesabı: '+v.oda+', '+v.kat+'. kat, asansör '+v.asan+', '+v.km+' km → '+B[0]+' kişi, '+B[1]}}""")
TOOLS['nak.liste'] = checks_tool('liste', 'cl', 'Taşınma hazırlık listesi', 'Yaptıklarınızı işaretleyin; eksik kalanları görün.', 'Tamamlananlar',
    [('keşif', 'Keşif randevusu aldım'), ('ayıkla', 'Kullanmadığım eşyaları ayıkladım'), ('kolı', 'Kırılacak eşyaları ayırdım'), ('belge', 'Önemli evrakı ayrı çantaya koydum'), ('asansör', 'Bina yönetiminden asansör ve park izni aldım'), ('beyaz', 'Beyaz eşyaları boşalttım ve ayırdım'), ('yeni', 'Yeni adreste kat/asansör bilgisini öğrendim')],
    {'keşif': 3, 'ayıkla': 2, 'kolı': 2, 'belge': 3, 'asansör': 3, 'beyaz': 2, 'yeni': 2},
    [(0, 'bad', 'Hazırlığa yeni başladınız'), (6, 'warn', 'İyi gidiyorsunuz'), (12, 'ok', 'Taşınmaya hazırsınız')],
    {'keşif': '', 'ayıkla': '', 'kolı': '', 'belge': '', 'asansör': '', 'beyaz': '', 'yeni': ''}, 'Maddelerin çoğu taşıma gününü sorunsuz geçirmeniz içindir.')

# ---- TEKSTİL
TOOLS['tek.metraj'] = dict(id='metraj', ico='cp', title='Kumaş metrajı hesaplayıcı', intro='Ürün türünü ve adedi seçin; yaklaşık kumaş ihtiyacını ve fire payını görün.',
    fields=[S('t', 'Ürün', [('tisort', 'Tişört'), ('gomlek', 'Gömlek'), ('pantolon', 'Pantolon'), ('elbise', 'Elbise'), ('ceket', 'Ceket / mont'), ('nevresim', 'Nevresim takımı')], 'tisort'), N('adet', 'Adet', 500, 1, 100000, 10, 'adet'), R('fire', 'Fire payı', 3, 15, 8, 1, '%')],
    calc=r"""function(v,H){var M={tisort:1.1,gomlek:1.5,pantolon:1.6,elbise:2.1,ceket:2.4,nevresim:5},m=M[v.t],top=v.adet*m*(1+v.fire/100),rol=Math.ceil(top/40);
return{tone:'ok',big:H.n(Math.ceil(top))+' m',head:'Yaklaşık kumaş ihtiyacı',lines:['Parça başına yaklaşık '+m+' m (150 cm en baz alındı)','Fire dahil: '+H.n(Math.ceil(top))+' m ≈ '+rol+' top (40 m\'lik)'],note:'Model, beden dağılımı, kumaş eni ve kesim planına göre değişir; kesin metraj numuneyle belirlenir.',msg:'Kumaş metrajı: '+v.adet+' '+v.t+', fire %'+v.fire+' → '+Math.ceil(top)+' m'}}""")
TOOLS['tek.surec'] = steps_tool('surec', 'bx', 'Numuneden sevkiyata süreç', 'Sipariş tipinizi seçin; adımları ve sizden beklenenleri görün.', 'Sipariş türü',
    [('toptan', 'Hazır model toptan alım'), ('ozel', 'Kendi modelim için özel üretim'), ('baski', 'Baskı / nakışlı ürün'), ('isk', 'İş kıyafeti')],
    {'toptan': ('Toptan alım', 'ok', ['Katalogdan model ve beden dağılımını seçin.', 'Fiyat listesi ve minimum adet teyit edilir.', 'Ödeme sonrası sevk planlanır, koli ve irsaliye ile gönderilir.'], 'Stokta yoksa termin teklifte yazılır.'),
     'ozel': ('Özel üretim', 'ok', ['Teknik föy / örnek ürün ve adedi iletin.', 'Numune hazırlanır, onayınız alınır.', 'Onaylı numuneye göre seri üretim ve kalite kontrol yapılır.', 'Sevkiyat ve fatura.'], 'Numune onayından sonra model değişikliği süreyi uzatır.'),
     'baski': ('Baskı / nakış', 'ok', ['Logoyu vektör (AI, PDF, SVG) ya da yüksek çözünürlükte gönderin.', 'Konum ve ölçü için taslak onaylanır.', 'Önce örnek baskı, sonra seri uygulama.'], 'Düşük çözünürlüklü görsel baskı kalitesini düşürür.'),
     'isk': ('İş kıyafeti', 'ok', ['Kıyafet türü, renk ve adet belirlenir.', 'Beden tablosu çıkarılır (çalışan sayısına göre).', 'Numune → onay → toplu üretim → sevkiyat.'], 'Beden listesini baştan netleştirmek iadeyi azaltır.')})

# ---- E-TİCARET
TOOLS['eti.kargo'] = dict(id='kargo', ico='bx', title='Ücretsiz kargoya ne kadar kaldı?', intro='Sepet tutarınızı yazın; ücretsiz kargo eşiğine ne kadar kaldığını görün.',
    fields=[N('sepet', 'Sepet tutarınız', 520, 0, 100000, 10, '₺'), N('esik', 'Ücretsiz kargo eşiği (mağaza belirler)', 750, 0, 100000, 10, '₺')],
    calc=r"""function(v,H){var k=v.esik-v.sepet;if(k<=0)return{tone:'ok',big:'Ücretsiz',head:'Kargo ücretsiz',lines:['Sepet tutarınız eşiği geçti.'],msg:'Sepet '+v.sepet+' ₺ — kargo ücretsiz'};
return{tone:'warn',big:H.n(k,0)+' ₺',head:'Ücretsiz kargo için kalan tutar',lines:['Sepetinize '+H.n(k,0)+' ₺ daha ürün eklerseniz kargo ücretsiz olur.'],note:'Eşik tutarı mağaza ayarlarından değiştirilir.',msg:'Sepet '+v.sepet+' ₺, eşik '+v.esik+' ₺, kalan '+k+' ₺'}}""")
TOOLS['eti.iade'] = steps_tool('iade', 'dr', 'İade ve değişim rehberi', 'Durumunuzu seçin; adımları görün.', 'Durum',
    [('iade', 'Ürünü iade etmek istiyorum'), ('degis', 'Beden / renk değiştirmek istiyorum'), ('hasar', 'Ürün hasarlı ya da yanlış geldi'), ('kargo', 'Siparişim henüz gelmedi')],
    {'iade': ('İade', 'ok', ['Ürünün kullanılmamış, etiketli ve ambalajında olması gerekir (hijyenik ürünlerde istisnalar vardır).', 'Siparişiniz teslim edildikten sonra yasal süre içinde iade talebi açın.', 'Size iade kargo kodu iletilir; ürün onaylandıktan sonra ödeme iade edilir.'], 'Cayma süresi ve istisnalar için sözleşme koşullarına bakın.'),
     'degis': ('Değişim', 'ok', ['Değişim talebinde yeni beden / renk belirtin.', 'Stok varsa ürün kargolanır; yoksa iade seçeneği sunulur.'], ''),
     'hasar': ('Hasarlı / yanlış ürün', 'warn', ['Paketi açarken fotoğraf çekin, kargo fişini saklayın.', 'Hemen bize iletin; ürünü ücretsiz değiştirir ya da ödemeyi iade ederiz.'], 'Kargo teslimatında hasar varsa tutanak tutturun.'),
     'kargo': ('Kargo gecikmesi', 'warn', ['SMS ile gelen takip koduyla kargo firmasından durumu sorgulayın.', 'Takip kodu gelmediyse sipariş numaranızla bize yazın.', 'Beklenen süre geçtiyse kargoyu araştırır, çözüm sunarız.'], '')})

# ---- TEMİZLİK
TOOLS['tem.sure'] = dict(id='sure', ico='cal', title='Temizlik süresi ve ekip hesabı', intro='Alanı ve temizlik türünü girin; tahmini süre ve ekip büyüklüğünü görün.',
    fields=[N('m2', 'Alan', 110, 10, 3000, 5, 'm²'), G('tur', 'Tür', [('ev', 'Ev'), ('ofis', 'Ofis'), ('insaat', 'İnşaat sonrası')]), G('kir', 'Kirlilik', [('az', 'Düzenli'), ('orta', 'Orta'), ('cok', 'Yoğun')], 'orta')],
    calc=r"""function(v,H){var r={ev:25,ofis:35,insaat:15}[v.tur]*{az:1.2,orta:1,cok:.7}[v.kir],kisi=v.m2>200?4:v.m2>100?3:2,saat=v.m2/(r*kisi);
return{tone:'ok',big:H.n(saat,1)+' saat',head:'Tahmini süre: '+kisi+' kişilik ekiple',lines:['Alan: '+v.m2+' m²','Kirlilik ve eşya yoğunluğu süreyi değiştirir.'],note:'Ön tahmindir; fotoğraf ya da keşifle netleşir.',msg:'Temizlik hesabı: '+v.m2+' m² '+v.tur+', '+v.kir+' → '+H.n(saat,1)+' sa, '+kisi+' kişi'}}""")
TOOLS['tem.liste'] = checks_tool('liste', 'cl', 'Temizlik öncesi hazırlık', 'Yaptıklarınızı işaretleyin; ekibin işini kolaylaştırın.', 'Hazırlıklar',
    [('deger', 'Değerli eşyaları kaldırdım'), ('kirilir', 'Kırılacak eşyaları topladım'), ('ev', 'Evcil hayvan varsa haber verdim'), ('su', 'Su ve elektrik açık olacak'), ('anahtar', 'Giriş ve park bilgisini ilettim'), ('ozel', 'Özel istekleri (alerji, ürün) yazdım')],
    {'deger': 2, 'kirilir': 2, 'ev': 1, 'su': 2, 'anahtar': 2, 'ozel': 2},
    [(0, 'bad', 'Hazırlığa başlayın'), (4, 'warn', 'Neredeyse hazır'), (9, 'ok', 'Hazırsınız')], {'deger': '', 'kirilir': '', 'ev': '', 'su': '', 'anahtar': '', 'ozel': ''}, 'Bu hazırlıklar işin daha hızlı ve sorunsuz bitmesini sağlar.')

# ---- GÜZELLİK
TOOLS['guz.paket'] = dict(id='paket', ico='cal', title='Seans paketi takibi', intro='Seans sayısını, aralığı ve başlangıç tarihini girin; tüm seans tarihlerini ve bitişi görün.',
    fields=[N('n', 'Paket seans sayısı', 6, 1, 30, 1, 'seans'), N('ara', 'Seanslar arası', 4, 1, 12, 1, 'hafta'), D('d0', 'İlk seans tarihi')],
    calc=r"""function(v,H){if(!v.d0)return{head:'İlk seans tarihini seçin',lines:[]};var d=new Date(v.d0),L=[],n=Math.min(30,v.n|0);for(var i=0;i<n;i++){var x=new Date(d);x.setDate(x.getDate()+i*7*v.ara);L.push((i+1)+'. seans: '+x.toLocaleDateString('tr-TR',{day:'numeric',month:'long',weekday:'short'}))}
return{tone:'ok',big:n+' seans',head:'Paket planı',lines:L.slice(0,8).concat(n>8?['…']:[]),note:'Tarihler öneridir; randevu müsaitliğe göre netleşir. Seans aralığı işleme göre uzman tarafından belirlenir.',msg:'Seans planı: '+n+' seans, '+v.ara+' haftada bir, başlangıç '+v.d0}}""")
TOOLS['guz.cilt'] = steps_tool('cilt', 'sp', 'Cilt bakım rehberi', 'Cilt tipinizi seçin; günlük bakımı görün.', 'Cilt tipi',
    [('kuru', 'Kuru'), ('yagli', 'Yağlı / karma'), ('hassas', 'Hassas'), ('lekeli', 'Leke ya da sivilce eğilimli')],
    {'kuru': ('Kuru cilt', 'ok', ['Hafif temizleyici ve nemlendirici kullanın.', 'Sıcak su yerine ılık su tercih edin.', 'Gün içinde güneş koruyucu kullanın.'], 'Pullanma ve kızarıklık sürerse uzmana danışın.'),
     'yagli': ('Yağlı / karma cilt', 'ok', ['Sabah ve akşam nazik temizleyici kullanın.', 'Hafif, yağsız nemlendirici seçin.', 'Cildi sık sık sürtmeyin.'], ''),
     'hassas': ('Hassas cilt', 'warn', ['Kokusuz ve az içerikli ürünler seçin.', 'Yeni ürünü önce küçük bir alanda deneyin.', 'Kızarıklık ve yanma olursa ürünü bırakın.'], 'Belirgin reaksiyonda doktora başvurun.'),
     'lekeli': ('Leke / sivilce eğilimi', 'warn', ['Güneş koruyucu lekeler için temel adımdır.', 'Sivilceleri sıkmayın.', 'Uzman analizi ile bakım planı yapılması önerilir.'], 'Bu bilgi tıbbi tavsiye değildir.')})
