from rich import *
A=[]
def art(fn,title,cat,desc,read,secs,rel,cta_txt=None):
    A.append(dict(fn=fn,title=title,cat=cat,desc=desc,read=read,secs=secs,rel=rel))
def L(*x): return ('ul',list(x))
def O(*x): return ('ol',list(x))
def N(t): return ('note',t)
art('blog-teknik-servis-nasil-acilir.html','Teknik servis nasıl açılır?','Başlangıç','Teknik servis açmadan önce karar verilecek konular: sektör, mevzuat, ekipman, fiyat ve kayıt düzeni.','6 dk',[
 ('Önce sektörü ve çalışma biçimini seçin',['Kombi, klima, beyaz eşya, elektronik, bilgisayar, tesisat, elektrik ya da güvenlik; her sektörün parça stoğu, ekipmanı ve müşteri beklentisi farklıdır. Tek bir sektörde uzmanlaşmak, ilk yıl için çoğu zaman daha sağlıklıdır.','İkinci karar çalışma biçimi: yalnızca sahada hizmet mi vereceksiniz, yoksa cihazı atölyeye de alacak mısınız? Atölye, ek mekân ve parça stoğu demektir; saha ise yol ve zaman maliyeti.']),
 ('Hukuki ve mali hazırlık',['Faaliyete başlamak için vergi mükellefiyeti ve esnaf ya da ticaret odası kaydı gerekir. Bazı markaların yetkili servisi olmak ayrıca başvuru ve belge ister. Güncel şartları mali müşavirinize ve ilgili meslek odasına danışın.',N('Mevzuat sık değişir. Bu yazı genel bilgilendirmedir; kesin gereklilikler için resmî kaynaklara ve danışmanınıza başvurun.')]),
 ('Ekipman ve parça stoğu',['Başlangıçta her parçayı stoklamaya çalışmayın. En sık arızalanan parçaları belirleyin; geri kalanı sipariş üzerine temin edin. Stok takibi baştan yapılmazsa hangi parçanın nerede olduğu kısa sürede karışır.',L('Temel el aletleri ve ölçüm cihazları','Sık kullanılan sarf ve yedek parçalar','Araç ve yakıt planı','Güvenilir bir parça tedarikçisi')]),
 ('Fiyatlandırma',['Fiyat listesini baştan hazırlayın: kalem başına işçilik, çıkış ücreti ve parça payı. Fiyatı müşteriye iş başlamadan söylemek hem güveni hem tahsilatı kolaylaştırır.','Ayrıntılı rehber için fiyat listesi yazımıza bakın.']),
 ('İlk günden kayıt düzeni kurun',['Büyük hata, ilk haftalarda kaydı “sonra yazarım” diye ertelemektir. Her iş için müşteri, cihaz, arıza, yapılan işlem, parça ve tahsilatı aynı yerde tutun. Defter ve Excel küçük hacimde yeter; usta sayısı arttığında program gerekir.',L('Müşteri ve cihaz bilgisi','Arıza ve yapılan işlem','Parça ve işçilik','Fotoğraf ve imza','Tahsilat')]),
 ('Müşteri bulma',['İlk müşteriler çoğunlukla çevre, mahalle grupları ve internet aramalarından gelir. Ayrıntılar için müşteri bulma yazımıza bakın.'])],
 [('blog-servis-fiyat-listesi-hazirlama.html','Servis fiyat listesi nasıl hazırlanır?','Fiyat'),('blog-teknik-servis-musteri-bulma.html','Teknik servis müşteri bulma yolları','Müşteri'),('cozum-servis-kaydi.html','Servis kaydı','Ürün')])
art('blog-servis-takip-programi-nasil-secilir.html','Servis takip programı nasıl seçilir?','Seçim rehberi','Servis takip programı seçerken sorulacak sorular: usta uygulaması, fiş, SMS, rapor, veri ve maliyet.','6 dk',[
 ('Önce ihtiyacınızı yazın',['Program seçmeden önce günlük işinizin nerede aksadığını yazın: telefon trafiği mi, ustaya iş atama mı, tahsilat takibi mi, müşteriye bilgi vermek mi? Aksayan yer, ilk bakacağınız özelliktir.']),
 ('Mutlaka sorulacak sekiz soru',[O('Usta telefonundan çalışıyor mu, indirme gerekiyor mu?','Fotoğraf ve imza adımları firmanıza göre ayarlanabiliyor mu?','Servis fişi tasarımı ve KVKK metni düzenlenebiliyor mu?','SMS kendi sağlayıcı hesabınızla mı gidiyor?','Usta bazında kasa ve rapor var mı?','Verilerinizi Excel’e alabiliyor musunuz?','Sektörünüze hazır şablon sunuluyor mu?','Mevcut kayıtlarınız aktarılıyor mu?')]),
 ('Fiyatı doğru karşılaştırın',['Aylık ücret tek başına yanıltıcıdır. Usta sayısı, SMS maliyeti, web sitesi ve kurulum desteği paketlerde farklı yerlerde olabilir. Paket içeriğini tablo halinde isteyin ve KDV’nin dahil olup olmadığına bakın.']),
 ('Deneme süresini kullanın',['İyi bir program size denetmekten çekinmez. Gerçek bir iş açın, ustanızı bağlayın, fişi basın, müşteriye mesaj gönderin. Bir gün içinde sürtünmeleri görürsünüz.']),
 ('Çıkış yolunu öğrenin',['Bir gün başka araca geçmek isterseniz verilerinizi alabilecek misiniz? Dışa aktarma imkânı, programın size ne kadar güvendiğinin göstergesidir.',N('Seçerken yalnızca özellik listesine değil, ekibin telefonda ne kadar yardımcı olduğuna da bakın.')])],
 [('blog-servis-takip-programi-nedir.html','Servis takip programı nedir?','Temel'),('karsilastirma.html','Defter ve Excel ile fark','Karşılaştırma'),('paketler-ozellikler.html','Paket paket ayrıntı','Paketler')])
art('blog-teknik-servis-musteri-bulma.html','Teknik servis müşteri bulma yolları','Büyüme','Yerel aramalardan referansa, web sitesinden bakım hatırlatmaya: teknik servislerin müşteri bulma yolları.','7 dk',[
 ('Yerel aramada görünün',['Müşteri arıza anında “kombi servisi” ya da “klima bakımı” diye arar. Harita kaydınızı doldurun, çalışma saatlerinizi ve telefonunuzu güncel tutun, hizmet verdiğiniz bölgeleri yazın. Fotoğraf ve müşteri yorumu güven verir.']),
 ('Web sitesi ve randevu formu',['Basit ama düzgün bir site, telefon açmaya çekinenleri forma yönlendirir. Sitede telefon, hizmet bölgesi, fiyat yaklaşımı ve randevu formu yeterlidir. Formdan gelen talebin kaybolmaması önemlidir.',L('Net telefon numarası ve tıklanabilir arama düğmesi','Hizmet verilen bölgeler','Marka listesi','Randevu formu')]),
 ('Mevcut müşteriyi geri kazanın',['Yeni müşteri bulmak, mevcut müşteriyi tutmaktan pahalıdır. Yıllık bakım gelen müşteriyi zamanında hatırlatmak hem gelir hem sadakat getirir. Bakım tarihlerini bir yerde tutmak yeter.']),
 ('Referans ve çevre',['Memnun müşteri en ucuz reklamdır. İş bitince fişi düzgün vermek, bir sonraki arızada sizi aramasının en güçlü nedenidir. Müşteriden yorum istemeyi iş akışının parçası yapın.']),
 ('Ölçün',['Hangi kanaldan kaç talep geldiğini kaydetmezseniz bütçeyi nereye harcayacağınızı bilemezsiniz. Her talebe kaynak bilgisi ekleyin.',N('Toplu SMS ya da arama yapmadan önce müşteri izni ve ticari ileti mevzuatına uyumu kontrol edin.')])],
 [('cozum-web-sitesi.html','Web sitesi','Ürün'),('cozum-pazarlama.html','Pazarlama araçları','Ürün'),('temalar.html','Temalar','38 hazır tema')])
art('blog-garanti-kapsami-servis.html','Garanti kapsamında servis nasıl yürür?','Süreç','Garanti kapsamındaki arızalarda kayıt, belge ve müşteri iletişimi nasıl yönetilir.','5 dk',[
 ('Garanti süresi ve başlangıç',['Garanti süresi, kural olarak ürünün tüketiciye teslim tarihinden başlar. Servis kaydında satış ya da teslim tarihini mutlaka tutun; garanti içinde mi dışında mı olduğunu bu tarih belirler.',N('Garanti süresi ve şartları üründen ürüne değişir. Güncel mevzuat ve üretici belgesini esas alın.')]),
 ('Garanti kaydında neler olmalı',[L('Satış ya da teslim tarihi ve fatura bilgisi','Cihaz marka, model ve seri numarası','Arıza tanımı ve fotoğraf','Yapılan işlem ve değişen parça','Müşteri imzası')]),
 ('Garanti dışı durumlar',['Kullanıcı hatası, yetkisiz müdahale ya da sürenin dolması gibi durumlarda müşteriyi sebebiyle birlikte bilgilendirin ve yazılı teklif sunun. Bilgilendirme ve onay kaydı, sonradan çıkabilecek tartışmaları önler.']),
 ('Bakımı garanti sürecine bağlayın',['Garanti biterken müşteriye yıllık bakım önermek doğal bir fırsattır. Bitiş tarihini cihaz kartında tutarsanız hatırlatmayı zamanında yaparsınız. Ücretsiz garanti bitiş hesaplama aracımız tarihi bulmanızı kolaylaştırır.'])],
 [('garanti-hesaplama.html','Garanti bitiş hesaplama','Araç'),('cozum-bakim-garanti.html','Bakım ve garanti','Ürün'),('cozum-teklif-onay.html','Teklif ve onay','Ürün')])
art('blog-servis-fiyat-listesi-hazirlama.html','Servis fiyat listesi nasıl hazırlanır?','Fiyat','Teknik servis için işçilik, çıkış ücreti ve parça payını içeren fiyat listesi hazırlama rehberi.','5 dk',[
 ('Neden baştan fiyat listesi?',['Fiyatı iş başlamadan söylemek müşteriyi rahatlatır. Telefonda “ne kadar tutar?” sorusuna net aralık verebildiğinizde randevuya dönüşme ihtimali artar.']),
 ('Üç kalemle başlayın',[O('Çıkış (kurulum) ücreti: adres başına yol ve zaman maliyeti','İşçilik: işlem türüne göre sabit ya da aralıklı','Parça: maliyet üzerine makul pay')]),
 ('Maliyetinizi bilin',['Fiyat, maliyetin üstünde olmalı; ama maliyeti bilmeden bunu bilemezsiniz. Yakıt, araç, sigorta, sarf malzeme ve zaman dahil edilmelidir. Aylık gider kaydı tutmak bu hesabı kolaylaştırır.']),
 ('Teklifi yazılı verin',['Parça gerektiren işlerde tutarı müşteri onayıyla netleştirin. Yazılı teklif ve onay kaydı iki tarafı da korur.',N('Fiyat listesi tek seferlik değildir; parça maliyeti değiştikçe güncelleyin.')]),
 ('Fiyatı sayfada gösterin',['Web sitenizde fiyat yaklaşımını yazmak, yalnızca ciddi talepleri çeker. Net fiyat yazmak istemiyorsanız “işçilik ... ₺’den başlar” gibi bir ifade kullanın.'])],
 [('cozum-teklif-onay.html','Teklif ve onay','Ürün'),('cozum-kasa-muhasebe.html','Kasa ve muhasebe','Ürün'),('blog-teknik-servis-nasil-acilir.html','Teknik servis nasıl açılır?','Başlangıç')])
art('blog-usta-performans-takibi.html','Usta performansı nasıl ölçülür?','Yönetim','Usta bazında iş sayısı, tamamlanma süresi ve tahsilat ile performans ölçümü ve adil değerlendirme.','5 dk',[
 ('Neyi ölçmeli?',['Yalnızca iş sayısına bakmak yanıltır. Hızlı ama özensiz çalışan usta çok iş çıkarır, geri dönüşü yüksek olur. Birkaç göstergeyi birlikte okuyun.',L('Tamamlanan iş sayısı','Ortalama tamamlanma süresi','Geri dönen (tekrar arızalanan) iş','Tahsilat tutarı','Müşteri memnuniyeti')]),
 ('Kayıt yoksa ölçüm yok',['Bu göstergeler ancak her iş sistemde kayıtlıysa güvenilir çıkar. İşe başlama ve bitirme adımları, fotoğraf ve imza zorunlu olduğunda veri düzgün birikir.']),
 ('Adil kıyaslama',['Zor ve kolay işleri aynı kefeye koymayın. Sektör ve iş türüne göre kıyaslayın; yeni başlayan ustayı deneyimli ustayla aynı hedefe bağlamayın.']),
 ('Geri bildirim döngüsü',['Rakamı ay sonunda bir kez söylemek yetmez. Haftalık kısa bir değerlendirmeyle güçlü ve zayıf yönleri konuşun. Anketle müşteri geri bildirimini rakamlara ekleyin.',N('Konum ya da performans takibi yapıyorsanız ekibinizi bu konuda açıkça bilgilendirin.')])],
 [('cozum-raporlar.html','Raporlar','Ürün'),('cozum-personel-takibi.html','Personel takibi','Ürün'),('cozum-canli-takip.html','Canlı takip','Ürün')])
def render(secs):
    out='';toc=[]
    for n,(h,parts) in enumerate(secs):
        out+='<h2 id="b%d">%s</h2>'%(n,E(h));toc.append((n,h))
        for p in parts:
            if isinstance(p,tuple):
                if p[0]=='ul': out+='<ul>%s</ul>'%''.join('<li>%s</li>'%E(x) for x in p[1])
                elif p[0]=='ol': out+='<ol>%s</ol>'%''.join('<li>%s</li>'%E(x) for x in p[1])
                else: out+='<div class="note">%s</div>'%E(p[1])
            else: out+='<p>%s</p>'%E(p)
    return out,toc
def build_all():
    for a in A:
        body_html,toc=render(a['secs'])
        t='<div class="r7-toc"><b>Bu yazıda</b>%s</div>'%''.join('<a href="#b%d">%s</a>'%(n,E(h)) for n,h in toc)
        body=hero([('bilgi-bankasi.html','Bilgi bankası'),(None,a['cat'])],a['title'],a['desc'],'',['%s okuma'%a['read'],a['cat']],[('index.html#kayit','Ücretsiz deneyin',''),('bilgi-bankasi.html','Tüm yazılar','o')])
        body+=sec('<div class="r7-art">%s%s</div>'%(t,body_html))
        body+=band('Servis kaydını kâğıttan çıkarın','İlk ay ücretsiz. Kurulumu birlikte yapalım.')
        body+=sec(head('Devamını okuyun','İlgili sayfalar','')+related([(h,t,s) for h,t,s in a['rel']]),last=False)
        body+=cta()
        ld='<script type="application/ld+json">%s</script>'%json.dumps({"@context":"https://schema.org","@type":"Article","headline":a['title'],"description":a['desc'],"inLanguage":"tr","publisher":{"@type":"Organization","name":"OnlineKaydet"}},ensure_ascii=False)
        page(a['fn'],a['title'],a['desc'],body,ld)
    return len(A)
HUB=[(a['fn'],a['title'],(a['cat'],a['desc'])) for a in A]
