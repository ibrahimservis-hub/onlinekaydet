#!/usr/bin/env python3
"""Satın al ve hukuki sayfalara, sayfadaki metinle uyumlu 'Kısaca' ve SSS bölümleri ekler (<!--HZ-->). Yeni hukuki hüküm eklemez."""
import os, re, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
exec(compile(open('gen_bilgi_zen.py',encoding='utf-8').read().split('P = {')[0],'x','exec'))
P = {
'satin-al.html': ([('Ödemeden sonra ne olur?','Ödemeden hemen sonra paneliniz açılır ve giriş bilgileriniz e-postanıza gelir.'),('Kart bilgilerim güvende mi?','Kart bilgileri iyzico’nun güvenli ekranında girilir; kart numaranız sunucumuza uğramaz.'),('Taksit yapabilir miyim?','Tüm banka ve kredi kartları geçerlidir; taksit seçenekleri kart ekranında görünür.'),('Faturamı nasıl alırım?','Faturanız e-postanıza gönderilir. Fatura için vergi dairesi, vergi ya da TC kimlik no ve adres bilgisi istenir.'),('Önce denemek istersem?','Satın almadan önce ücretsiz demo hesabı açabilirsiniz; demo 7 gün açık kalır.'),('Zaten hesabım var, ne olur?','Aynı e-posta ile kayıtlı hesap varsa yeni hesap açılmaz; mevcut hesabınızın süresi uzatılır ve paketiniz güncellenir.')],None),
'gizlilik.html': ([('Hangi bilgileri topluyorsunuz?','Formlara yazdığınız ad soyad, telefon, firma ve sektör bilgisi. Başvurunuzla ilgisi olmayan veri istenmez.'),('Bilgilerim satılır mı?','Hayır; bilgiler yalnızca sizinle iletişim kurmak ve talebinizi yanıtlamak için kullanılır, üçüncü kişilere satılmaz.'),('Haklarım nelerdir?','Ayrıntı için KVKK Aydınlatma Metni sayfasına bakın.')],'Bu sayfa, sitede hangi bilgilerin neden toplandığını sade bir dille özetler. Ayrıntılı hukuki metin için KVKK Aydınlatma Metni’ne bakın.'),
'kvkk.html': ([('Verilerim ne için kullanılır?','Talebinize dönüş yapmak, demo veya kurulum sürecini yürütmek, teklif ve hizmet bilgisi sunmak için.'),('Verilerim kimlerle paylaşılır?','Yalnızca hizmetin yürütülmesi için gerekli iş ortaklarıyla (barındırma, SMS gibi) ve yasal zorunluluk halinde yetkili kurumlarla.'),('Verilerimin silinmesini isteyebilir miyim?','KVKK madde 11 kapsamında silinmesini veya yok edilmesini isteme hakkınız vardır. Başvuru için sitedeki iletişim formunu kullanabilirsiniz.')],'Bu sayfa 6698 sayılı Kanun’un 10. maddesi uyarınca hazırlanmış aydınlatma metnidir. Aşağıdaki sorular metnin kısa özetidir; metnin yerine geçmez.'),
'cerez-politikasi.html': ([('Reklam çerezi kullanıyor musunuz?','Hayır. Site yalnızca çalışması için gerekli çerezleri ve oturum bilgilerini kullanır.'),('Çerezleri engellersem ne olur?','Gerekli çerezleri engellerseniz üye girişi gibi bazı bölümler çalışmayabilir.'),('Çerezleri nasıl silerim?','Tarayıcı ayarlarınızdan çerezleri silebilir veya engelleyebilirsiniz.')],None),
'kullanim-kosullari.html': ([('Hesabımdan kim sorumlu?','Hesap bilgilerinizin gizliliğinden ve hesabınızda yapılan işlemlerden siz sorumlusunuz. Yetkisiz kullanımı hemen bildirin.'),('Yüklediğim içerikten kim sorumlu?','Yüklediğiniz yazı, görsel ve verilerin hukuka uygunluğu size aittir; başkasının telif hakkını ihlal eden içerik yüklenemez.'),('Aboneliği sonlandırabilir miyim?','Aboneliği dilediğiniz zaman sonlandırabilirsiniz; ödenmiş dönem koşulları mesafeli satış ve iade sayfasındadır.')],None),
'mesafeli-satis-iade.html': ([('Cayma hakkım kaç gün?','Tüketici olarak 14 gün içinde cayma hakkınızı kullanabilirsiniz; yönetmelikte belirtilen hâllerde istisnalar vardır.'),('İade nasıl yapılır?','İade talebinizi iletişim formundan ya da telefonla iletin. Onaylanan iade, ödemenizi yaptığınız yönteme geri yapılır.'),('Ücretsiz deneme bir yükümlülük doğurur mu?','Hayır; demo hesabı 7 gün ücretsizdir ve satın alma yükümlülüğü doğurmaz.')],None),
}
def blok(q, ozet):
    h = '<!--HZ-->' + STIL
    if ozet: h += sec('Kısaca', '<p>%s</p>' % ozet)
    return h + QA(q) + '<!--/HZ-->'
for fn, (q, ozet) in P.items():
    t = open(fn, encoding='utf-8').read()
    t = re.sub(r'<!--HZ-->.*?<!--/HZ-->', '', t, flags=re.S)
    t = re.sub(r'<script type="application/ld\+json" data-hz>.*?</script>', '', t, flags=re.S)
    if '<section id="kayit"' in t: i = t.index('<section id="kayit"')
    elif '</main>' in t: i = t.index('</main>')
    else: i = t.index('<p class="footm"')
    t = t[:i] + blok(q, ozet) + t[i:]
    t = t.replace('</head>', ldq(q).replace('data-bz', 'data-hz') + '</head>', 1)
    open(fn, 'w', encoding='utf-8').write(t)
print(len(P))
