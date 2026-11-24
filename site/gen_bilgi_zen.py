#!/usr/bin/env python3
"""Bilgi bankası ve birkaç sayfaya hazırlık, sık sorunlar ve SSS bölümleri ekler (<!--BZ-->…<!--/BZ-->). Genel bilgi; sayfadaki adımlarla uyumlu."""
import os, re, json
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
src = open('gen_seo_karsilastirma.py', encoding='utf-8').read()
exec(compile(src[:src.index('RIV = {')], 'gen_seo_pre', 'exec'))
L = lambda x: '<ul>%s</ul>' % ''.join('<li>%s</li>' % i for i in x)
def QA(items):
    return '<section class="kk"><div class="w"><h2>Sık sorulan sorular</h2><div class="sss">%s</div></div></section>' % ''.join('<details><summary>%s</summary><p>%s</p></details>' % (a, b) for a, b in items)
def ldq(items):
    return '<script type="application/ld+json" data-bz>%s</script>' % json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': a, 'acceptedAnswer': {'@type': 'Answer', 'text': b}} for a, b in items]}, ensure_ascii=False)
# (hazırlık, sorunlar, SSS)
P = {
'bilgi-alan-adi.html': (['Alan adını aldığınız firmanın panel girişi ve şifresi.', 'Mevcut sitenizin ya da e-posta hizmetinizin aynı alan adını kullanıp kullanmadığı bilgisi.', 'Bağlamak istediğiniz adresin yazımı (örneğin firmaadi.com).'],
  ['DNS kaydını yanlış satıra ya da yanlış türde girmek.', 'Eski kaydı silmeden yenisini eklemek; çakışma olur.', 'Değişiklik yayılmadan hemen “Kontrol et”e basmak.', 'E-posta kayıtlarını (MX) yanlışlıkla silmek; e-posta çalışmaz.'],
  [('DNS nedir?', 'DNS, alan adının hangi sunucuya gideceğini belirleyen kayıtlar listesidir. Alan adını aldığınız firmanın ekranından düzenlenir.'), ('Birden fazla alan adı bağlayabilir miyim?', 'Evet; sayfada belirtildiği üzere en fazla 5 alan adı bağlanır.'), ('E-postalarım bozulur mu?', 'Yalnızca siteyle ilgili kayıtları değiştirirseniz bozulmaz. E-posta (MX) kayıtlarına dokunmayın.')]),
'bilgi-baslangic.html': (['Firmanızın adı, telefonu ve adresi.', 'Sunmak istediğiniz hizmet ya da ürünlerin listesi.', 'Kullanacağınız fotoğraflar (kendi işinize ait).', 'Alan adınız varsa giriş bilgileri.'],
  ['Temayı seçip metinleri değiştirmeden yayına almak.', 'Fotoğrafları çok büyük boyutta yüklemek.', 'Telefonda görünümü kontrol etmemek.', 'Ekibin kullanıcılarını ve yetkilerini eklemeyi unutmak.'],
  [('Demo gerçek veriye dönüşür mü?', 'Demo, deneme içindir. Gerçek kullanıma başlarken kendi firma bilgilerinizi ve kayıtlarınızı girersiniz.'), ('Kart bilgisi gerekir mi?', 'Demo hesabı açarken kart bilgisi istenmez; demo 7 gün açık kalır.')]),
'bilgi-entegrasyon-baglama.html': (['İlgili hizmetten (iyzico, kargo, pazaryeri vb.) alınmış anahtar ya da kullanıcı bilgileri.', 'Test ortamı varsa test anahtarları.', 'Hangi bağlantının hangi işe yarayacağının kısa notu.'],
  ['Anahtarı eksik ya da başında sonunda boşlukla yapıştırmak.', 'Canlı anahtarı test ortamına girmek ya da tersini yapmak.', 'Bağlantı hata verirken test edilmeden kullanmaya devam etmek.', 'Gizli anahtarı başkalarıyla paylaşmak.'],
  [('“Bağlı” yazmadan kullanabilir miyim?', 'Panel bağlantıyı denemeden “Bağlı” yazmaz. Hata varsa kartta sebebi görünür; önce onu giderin.'), ('Gizli anahtar neden görünmüyor?', 'Güvenlik için gizli alanlar kayıttan sonra gösterilmez; yalnız son haneler görünür.')]),
'bilgi-ilan-ekleme.html': (['İlanın başlığı, türü ve kategorisi.', 'Fiyat, il, ilçe ve mahalle bilgisi.', 'En fazla 8 resim; her biri yaklaşık 600 KB’ı geçmeyecek şekilde hazır.', 'Açıklama metni (en fazla 5000 karakter).'],
  ['Başlığı çok kısa (5 karakterden az) yazmak.', 'Resimleri büyük boyutta yüklemeye çalışmak.', 'Açıklamayı başka sitelerden aynen kopyalamak; arama motorlarında zayıf kalır.', 'Satıldı ya da kiralandı durumundaki ilanı güncellememek.'],
  [('Kaç resim ekleyebilirim?', 'Bir ilana en fazla 8 resim eklenir.'), ('İlanlar Google’da görünür mü?', 'Her ilanın kendi sayfası vardır ve arama motorları bu sayfaları görebilir; başlık ve açıklamayı özgün yazmak sıralamaya yardım eder.')]),
'bilgi-kasa-ve-muhasebe.html': (['Gelir ve gider kalemlerinizin kısa listesi (kira, malzeme, maaş vb.).', 'Hangi ödeme yöntemlerini kullandığınız: nakit, kart, havale.', 'Gün sonunda kasa sayımını kimin yapacağı.'],
  ['Gideri girmeyip yalnız geliri takip etmek; kâr yanıltıcı görünür.', 'Elle kayıt girerken tarihi yanlış seçmek.', 'Aynı ödemeyi hem randevudan hem elle girmek; çift kayıt olur.', 'Gün sonunda gerçek kasa ile kayıtlı kasayı karşılaştırmamak.'],
  [('Randevudan alınan ödeme otomatik yazılır mı?', 'Evet; sayfada belirtildiği gibi randevudan alınan her ödeme kasaya yazılır.'), ('Resmi muhasebe yerine geçer mi?', 'Kasa ekranı işletme içi takip içindir. Resmi defter ve beyanlar için mali müşavirinize danışın.')]),
'bilgi-musteri-yonetimi.html': (['Mevcut müşteri listeniz (ad, telefon).', 'Hangi bilgilerin zorunlu olacağına dair kısa karar.', 'Müşteri notlarında nelerin yazılacağı (alışkanlık, tercih, alerji gibi iş için gerekenler).'],
  ['Aynı müşteriyi farklı yazımlarla birden çok kez kaydetmek.', 'Telefon numarasını biçimsiz girmek; arama zorlaşır.', 'Gereksiz kişisel bilgi toplamak; KVKK açısından risklidir.', 'Müşteri notlarına gereksiz yorum yazmak.'],
  [('Müşteri geçmişini nasıl bulurum?', 'Müşteriyi ad ya da telefonla arayıp açarsınız; önceki işlemleri ve notları görürsünüz.'), ('Müşteri bilgileri KVKK’ya uygun mu?', 'Veriyi yalnız iş için gerekli kadar toplayın ve KVKK aydınlatma metninizi güncel tutun; hukuki ayrıntı için uzmana danışın.')]),
'bilgi-personel-ve-prim.html': (['Her çalışanın adı, unvanı, maaşı ve prim oranı.', 'Primin hangi işlerden hesaplanacağı kararı.', 'Avans ve ödeme tarihleriniz.'],
  ['Prim oranını yanlış girip sonradan düzeltmemek.', 'Avansı kasaya işlemeden vermek.', 'Dönem seçimini (bu ay / geçen ay) karıştırmak.', 'Kişi eklemeden randevu açmaya çalışmak.'],
  [('Prim nasıl hesaplanır?', 'Sayfada anlatıldığı gibi prim, tamamlanan randevulardan kendiliğinden hesaplanır.'), ('Ödenecek tutar nasıl bulunur?', 'Ödenecek tutar maaş ve primin toplamından dönem içinde yapılan ödemelerin (avans, maaş, prim) düşülmesiyle bulunur.')]),
'bilgi-randevu-ve-takvim.html': (['Sunduğunuz hizmetlerin adı, süresi ve fiyatı.', 'Çalışanların ya da uzmanların listesi.', 'Çalışma saatleriniz ve hatırlatma mesajı tercihiniz.'],
  ['Hizmet süresini gerçekçi girmemek; takvim sıkışır.', 'Aynı uzmana aynı saatte iki randevu vermek.', 'Siteden gelen talebi onaylamadan bırakmak.', 'İşlem bitince ödemeyi kayda almamak.'],
  [('Siteden gelen talepler nerede görünür?', 'Talepler takvimde “talep” olarak belirir; onaylayıp tarih ve saati netleştirirsiniz.'), ('Müşteriye hatırlatma gider mi?', 'Mesaj ayarınız açıksa randevu oluşunca hatırlatma gider.')]),
'bilgi-ve-veri-guvenligi.html': (['Yönetici hesapları için güçlü bir şifre.', 'Hangi çalışanın hangi ekranı göreceğine dair rol listesi.', 'İki adımlı doğrulama için bir doğrulama uygulaması.'],
  ['Aynı şifreyi başka yerlerde de kullanmak.', 'Ortak hesapla çalışmak; kimin ne yaptığı belli olmaz.', 'Ayrılan çalışanın hesabını kapatmamak.', 'Şifreleri e-postayla paylaşmak.'],
  [('İki adımlı doğrulamayı açmalı mıyım?', 'Yönetici hesapları için açmanızı öneririz; sayfada belirtildiği gibi TOTP tabanlı doğrulama açılabilir.'), ('Silinen kayıt geri gelir mi?', 'Silinen kayıtlar çöp kutusuna gider ve oradan geri alınabilir.')]),
'bilgi-web-sitesi-duzenleme.html': (['Firma bilgileri, hizmet metinleri ve fotoğraflar.', 'Menüde yer alacak sayfaların listesi.', 'Her sayfa için kısa başlık ve açıklama metni.'],
  ['Tema metinlerini hiç değiştirmeden yayına almak.', 'Her sayfaya aynı başlığı yazmak.', 'Fotoğrafları sıkıştırmadan yüklemek.', 'Telefonda görünümü kontrol etmemek.'],
  [('Kod bilmem gerekir mi?', 'Hayır; metin, resim ve menü panelden değişir.'), ('Yaptığım değişiklik hemen yayınlanır mı?', 'Kaydedip yayınladığınızda değişiklik sitenizde görünür.')]),
'bilgi-siparis-ve-kargo.html': (['Kargo firmasıyla anlaşma bilgileriniz.', 'Ürünlerin ağırlık ve ölçüleri.', 'Etiket ve kargo şablonu tercihleriniz.'],
  ['Adres alanı eksik siparişi kargoya vermek.', 'Ölçüleri yanlış girip desi farkıyla karşılaşmak.', 'Takip numarasını sipariş kaydına işlememek.', 'İade gönderisini ayrı takip etmemek.'],
  [('Takip numarası müşteriye gider mi?', 'Takip numarası siparişe işlenir; müşteriye iletilmesi mesaj ayarlarınıza bağlıdır.'), ('Birden çok siparişi toplu işleyebilir miyim?', 'Bu sayfadaki adımlar toplu işlemleri anlatır; ayrıntı için sayfadaki adımları izleyin.')]),
'bilgi-yemek-siparisleri.html': (['Yemek platformu hesabı ve bağlantı bilgileri.', 'Menünüzdeki ürünlerin güncel fiyatları.', 'Siparişleri kimin karşılayacağı bilgisi.'],
  ['Menüde olmayan ürünü açık bırakmak.', 'Fiyatı platformlarda farklı güncellemek.', 'Sipariş bildirimini kaçırmak.', 'Hazırlık süresini gerçekçi belirtmemek.'],
  [('Siparişler tek listede görünür mü?', 'Bağlanan platformlardan gelen siparişler aynı listede toplanır.'), ('Menüyü platformlara nasıl gönderirim?', 'Menü ve platform adımları için “menüyü pazaryerine gönderme” rehberine bakın.')]),
'bilgi-menu-pazaryerine-gonderme.html': (['Menüdeki ürünlerin adı, açıklaması, fiyatı ve fotoğrafı.', 'Platformda onaylı işletme hesabı.', 'Platformun kategori kuralları.'],
  ['Fotoğrafsız ürün göndermek.', 'Kategori eşleştirmesini yapmamak.', 'Fiyatı platform komisyonunu düşünmeden belirlemek.', 'Tükenen ürünü menüden çıkarmamak.'],
  [('Hangi platformlara gönderilir?', 'Entegrasyonlar sayfasındaki yemek platformları listesine bakın.'), ('Önce birkaç ürünle deneyebilir miyim?', 'Evet; önce az sayıda ürünle denemek hata riskini azaltır.')]),
}
IL = (['Formu doldurmadan önce hangi sektörde çalıştığınızı ve kaç çalışanınız olduğunu düşünün.', 'Şu an kullandığınız yöntemi (defter, Excel, başka program) not edin.', 'Aklınızdaki üç temel soruyu yazın.'],
  ['Telefon numarasını yanlış yazmak; size ulaşamayız.', 'Sektör alanını boş bırakmak; kurulumu planlamak güçleşir.'],
  [('Formu doldurunca ne olur?', 'Sayfada belirtildiği gibi sizi arayıp kurulumu planlarız.'), ('WhatsApp ile yazabilir miyim?', 'Evet; soru sorabilir, ekran görüntüsü gönderebilirsiniz.')])
DM = (['Demo hesabınız için ad, telefon ve firma adı yeterlidir.', 'Birkaç gerçek işi demoda deneyin: kayıt aç, usta ata, fiş gönder.', 'Ekipten bir kişiyi daha deneme için dahil edin.'],
  ['Demoyu açıp hiç gezmemek.', 'Yalnız yönetim panelini denemek, usta uygulamasını atlamak.'],
  [('Demo ne kadar süre açık kalır?', 'Demo hesabı 7 gün açık kalır.'), ('Kart bilgisi gerekir mi?', 'Kayıt ve kart bilgisi gerekmez.')])
P['iletisim.html'] = IL; P['demo.html'] = DM
def blok(h, s, q):
    return ('<!--BZ-->' + STIL + sec('Başlamadan önce', L(h)) + sec('Sık yapılan hatalar', L(s), tint=True) + QA(q) + '<!--/BZ-->')
def isle(fn):
    t = open(fn, encoding='utf-8').read()
    t = re.sub(r'<!--BZ-->.*?<!--/BZ-->', '', t, flags=re.S)
    t = re.sub(r'<script type="application/ld\+json" data-bz>.*?</script>', '', t, flags=re.S)
    h, s, q = P[fn]
    if 'Diğer rehberler' in t: i = t.rindex('<section', 0, t.index('Diğer rehberler'))
    elif '<section id="kayit"' in t: i = t.index('<section id="kayit"')
    else: i = t.index('</main>')
    t = t[:i] + blok(h, s, q) + t[i:]
    t = t.replace('</head>', ldq(q) + '</head>', 1)
    open(fn, 'w', encoding='utf-8').write(t)
if __name__ == '__main__':
    for fn in P: isle(fn)
    print(len(P), 'sayfa')
