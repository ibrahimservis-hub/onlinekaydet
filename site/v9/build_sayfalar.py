#!/usr/bin/env python3
"""Çok sayfalı site üretici. Kaynak: kaynak/index-v9.html (tek sayfa sürümü)."""
import re, os, html
H=os.path.dirname(os.path.abspath(__file__)); S=os.path.dirname(H)
src=open(H+'/kaynak/index-v9.html',encoding='utf-8').read()
BASE='https://onlinekaydet.com'
# --- parçalar
marks=['<section class="hero"','<section class="dort"','<section class="sec tema"','<section class="sec etc"','<section class="edt"','<section class="sec yon"','<section class="pak"','<section class="sec sek"','<section class="sec ent"','<section class="sec guv"','<section class="sec sss"','<section class="son"','<footer>']
pos=[src.index(m) for m in marks]+[src.index('<div class="mbar">')]
P={}
KEYS=['hero','dort','tema','etc','edt','yon','pak','sek','ent','guv','sss','son','footer']
for i,k in enumerate(KEYS): P[k]=src[pos[i]:pos[i+1]]

# --- metin düzeltmeleri (daha sade, konuşur gibi)
METIN=[
('Web siteniz, <em>mağazanız</em>, randevunuz ve <span>iş takibiniz</span> tek yerde.','Sitenizi açın, <em>siparişi</em> alın, <span>işi buradan</span> takip edin.'),
('Hazır temayı seçin, ürünlerinizi ekleyin, siparişi ve randevuyu aynı panelden yönetin. Kasa, personel ve raporlar da orada.','Sektörünüze uygun hazır temayı seçin, ürünlerinizi girin. Sipariş, randevu, kasa ve personel aynı ekranda.'),
('Hazır tema, alan adı bağlama ve SSL web sitesi paketine dahildir.','Hazır tema, alan adı bağlama ve SSL web sitesi paketinin içindedir.'),
('Temanızı seçin. Yarın yayında olun.','Tema seçin, yarın sitenizi yayınlayın.'),
('Aşağıdakiler çizim değil, temaların kendi ekran görüntüleri: masaüstü ve telefon yan yana. Her temada metni, yazı tipini ve görseli panelden siz değiştirirsiniz.','Aşağıdakiler çizim değil, gerçek tema ekran görüntüleri: bilgisayar ve telefon yan yana. Yazıyı, yazı tipini ve resmi panelden kendiniz değiştirirsiniz.'),
('Mağazanız sitenizin içinde. Hepsi tek stoktan.','Mağaza sitenizin içinde, stok tek yerde.'),
('Sitenizden, pazaryerinden, telefondan ya da tezgâhtan gelen sipariş aynı listeye düşer. Aşağıdaki ekranlar panelin kendisidir.','Siteden, pazaryerinden, telefonla ya da tezgâhta gelen sipariş aynı listeye girer. Aşağıdaki ekranlar panelin kendisi.'),
('Sitenizin her bölümü sizin elinizde.','Siteyi değiştirmek için kimseye ihtiyacınız yok.'),
('Mağazanın arkasındaki iş de aynı panelde.','Mağazanın arkasındaki iş de aynı yerde yürür.'),
('Randevu, kasa, personel ve evrak ayrı programlara dağılmaz. Panel, seçtiğiniz sektörün terimleriyle açılır: kuaförde uzman ve randevu, serviste usta ve servis kaydı.','Randevu, kasa, personel ve evrak ayrı programlara dağılmaz. Panel mesleğinizin diliyle açılır: kuaförde uzman ve randevu, serviste usta ve servis kaydı.'),
('Dört paket. Ne aldığınız satır satır belli.','Dört paket; içinde ne var, satır satır yazıyor.'),
('Panel sizin işinizin diliyle konuşur.','Panelde sizin mesleğinizin kelimeleri geçer.'),
('Zaten kullandığınız hesaplara bağlanır.','Kullandığınız hesaplarla birlikte çalışır.'),
('Kime emanet ettiğinizi bilin.','Verileriniz kimde duruyor, açıkça yazıyoruz.'),
('Karar vermeden önce','Sık sorulanlar'),
('Temanızı bugün seçin, mağazanızı bu hafta açın.','Numaranızı bırakın, sizi arayalım.'),
]
for k in list(P):
    for a,c in METIN: P[k]=P[k].replace(a,c)
import re as _re
P['guv']=_re.sub(r'<div class="yorum">.*?</div>','',P['guv'],flags=_re.S)

head_raw=src[:src.index('<script type="application/ld+json">')]
jsonld=src[src.index('<script type="application/ld+json">'):src.index('</script>',src.index('<script type="application/ld+json">'))+9]
mbar=src[src.index('<div class="mbar">'):src.index('<script src="/v9/v9.js"')]
foot=P['footer']
SEC={'temalar':'/temalar.html','eticaret':'/e-ticaret.html','editor':'/web-sitesi.html','yonetim':'/is-takibi.html','paketler':'/fiyatlar.html','sektorler':'/sektorler.html'}
NAV=[('Temalar','/temalar.html'),('E-ticaret','/e-ticaret.html'),('Web sitesi','/web-sitesi.html'),('İş takibi','/is-takibi.html'),('Paketler','/fiyatlar.html'),('Sektörler','/sektorler.html')]
def hdr(cur):
    a=lambda t,u,c='':'<a %shref="%s"%s>%s</a>'%(c,u,' aria-current="page"' if u==cur else '',t)
    nav=''.join(a(t,u) for t,u in NAV)
    dr=''.join('<a class="m" style="--i:%d" href="%s"%s>%s</a>'%(i,u,' aria-current="page"' if u==cur else '',t) for i,(t,u) in enumerate(NAV+[('Özellikler','/ozellikler.html'),('İletişim','/iletisim.html')]))
    return ('<header class="ust"><div class="w"><a class="logo" href="/"><img src="/logo-acik-s.png" alt="OnlineKaydet" width="160" height="32"></a>'
     '<nav class="nav" aria-label="Ana menü">%s</nav><a class="gir" href="/uye-girisi">Üye girişi</a>'
     '<a class="btn bos kc" href="#teklif">Teklif alın</a><a class="btn fil kc" href="/demo.html">Ücretsiz deneyin</a>'
     '<button class="mnu" type="button" aria-label="Menüyü aç" aria-expanded="false" aria-controls="cekmece"><i></i><i></i></button></div>'
     '<div class="cek" id="cekmece">%s<div class="bt2"><a class="btn fil" href="/demo.html">Ücretsiz deneyin</a><a class="btn bos" href="#teklif">Teklif alın</a><a class="btn bos" href="tel:+905444444004">Hemen arayın</a><a class="btn bos" href="/uye-girisi">Üye girişi</a></div></div></header>')%(nav,dr)
def img(n,w,h,alt,eager=False):
    return '<img src="/v9/img/%s.webp" width="%d" height="%d" alt="%s"%s>'%(n,w,h,html.escape(alt),'' if eager else ' loading="lazy"')
def banner(slug,ad,h1,lead,gorsel=None,chip=None):
    yan=''
    if gorsel:
        n,alt=gorsel
        yan='<div class="yan" data-tilt><div class="tar"><div class="tb"><i></i><i></i><i></i></div>%s</div>%s</div>'%(img(n,1400,875,alt,True),'<div class="cip2"><b>%s</b>%s</div>'%chip if chip else '')
    return ('<section class="pb" id="icerik"><div class="w"><div><p class="kr"><a href="/">Ana sayfa</a> / %s</p><h1>%s</h1><p class="lead">%s</p>'
     '<div class="cta"><a class="btn fil" href="/demo.html">Ücretsiz deneyin</a><a class="btn bos" href="#teklif">Teklif alın</a><a class="btn duz" href="tel:+905444444004">Hemen arayın</a></div></div>%s</div></section>')%(ad,h1,lead,yan)
def page(slug,title,desc,body,ld=None,home=False):
    url=BASE+('/' if home else '/'+slug)
    h=head_raw.replace('content="#0A6847"','content="#3034FF"')
    h=re.sub(r'<title>.*?</title>','<title>%s</title>'%html.escape(title),h,flags=re.S)
    h=re.sub(r'(<meta name="description" content=")[^"]*','\\g<1>'+html.escape(desc,quote=True),h)
    h=re.sub(r'(<link rel="canonical" href=")[^"]*','\\g<1>'+url,h)
    h=re.sub(r'(<meta property="og:url" content=")[^"]*','\\g<1>'+url,h)
    h=re.sub(r'(<meta property="og:title" content=")[^"]*','\\g<1>'+html.escape(title,quote=True),h)
    h=re.sub(r'(<meta property="og:description" content=")[^"]*','\\g<1>'+html.escape(desc,quote=True),h)
    h=h.replace('<link rel="stylesheet" href="/v9/v9.css">','<link rel="stylesheet" href="/v9/v9.css"><link rel="stylesheet" href="/v9/v10.css"><link rel="stylesheet" href="/v9/v11.css">')
    import json as _j
    _all=_j.loads(jsonld[jsonld.index('>')+1:-9])
    if home: lj='<script type="application/ld+json">'+_j.dumps(_all[:3],ensure_ascii=False)+'</script>'
    elif slug=='sss.html': lj='<script type="application/ld+json">'+_j.dumps([x for x in _all if x['@type']=='FAQPage'],ensure_ascii=False)+'</script>'
    else:
        lj='<script type="application/ld+json">'+__import__('json').dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Ana sayfa","item":BASE+"/"},{"@type":"ListItem","position":2,"name":title.split(' | ')[0],"item":url}]},ensure_ascii=False)+'</script>'
    cur='/' if home else '/'+slug
    full=h+lj+'\n</head><body>\n<a class="skip" href="#icerik">İçeriğe geç</a>'+hdr(cur)+'\n<main>'+body+'</main>\n'+foot+'\n'+mbar+'<script src="/v9/v9.js" defer></script><script src="/v9/v10.js" defer></script><script src="/lead.js" defer></script></body></html>'
    for k,v in SEC.items():
        if 'id="%s"'%k not in full: full=full.replace('href="#%s"'%k,'href="%s"'%v)
    if 'id="e-urun"' not in full: full=full.replace('href="#e-','href="/e-ticaret.html#e-')
    full=full.replace('<div class="duy">','<div class="duy">')  # duyuru çubuğu ana sayfada
    open(S+'/'+('index.html' if home else slug),'w',encoding='utf-8').write(full)
    print('yazıldı',slug if not home else 'index.html',len(full)//1024,'KB')
# duyuru çubuğu yalnız ana sayfada (src içinde başlıkla birlikte); iç sayfalarda yok
duy=src[src.index('<div class="duy">'):src.index('</div></div>',src.index('<div class="duy">'))+12]
def karti(no,ad,tx,u,im,alt,cls=''):
    return '<a class="kp %s" href="%s"><div class="im">%s</div><div class="ic"><span class="no">%s</span><h3>%s</h3><p>%s</p><span class="ok">İncele</span></div></a>'%(cls,u,img(im[0],im[1],im[2],alt),no,ad,tx)
KAPI=('<section class="kpl" id="kapilar"><div class="w"><div class="bs"><p class="et">Siteyi gezin</p><h2>Her konu kendi sayfasında, ayrıntısıyla.</h2></div><div class="kg">'
 +karti('01','Hazır temalar','Sektörünüze göre hazır gelen web sitesi temaları.','/temalar.html',('tema-1-kombi-d',1280,800),'Hazır tema örneği','gen')
 +karti('02','E-ticaret','Ürün, sipariş, kampanya, pazaryeri ve iade tek panelde.','/e-ticaret.html',('panel-d-urun',1400,875),'E-ticaret ürün ekranı')
 +karti('03','Web sitesi','Metni, görseli ve bölümleri panelden değiştirin.','/web-sitesi.html',('panel-d-site',1400,875),'Web sitesi editörü')
 +karti('04','Randevu ve iş takibi','Takvim, kasa, muhasebe, personel ve evrak takibi.','/is-takibi.html',('panel-k-takvim',1400,875),'Randevu takvimi')
 +karti('05','Paketler','Paketleri ve içeriklerini yan yana karşılaştırın.','/fiyatlar.html',('panel-k-kasa',1400,875),'Kasa ekranı')
 +'</div></div></section>')
SERIT=lambda: '<div class="ser" aria-hidden="true"><div>'+''.join('<span>%s</span>'%x for x in 2*['Kombi servisi','Klima','Kuaför','Güzellik salonu','Beyaz eşya','Oto servis','Elektrik','Tesisat','Bilgisayar','Güvenlik kamerası','Nakliyat','E-ticaret'])+'</div></div>'

def kart(no,ad,tx,u='',yk=False):
    return '<div class="fk"><span class="no">%s</span><h3>%s%s</h3><p>%s</p>%s</div>'%(no,ad,'<span class="yk">Yakında</span>' if yk else '',tx,('<a href="%s">Ayrıntılar</a>'%u) if u else '')
def sec_baslik(et,h2,lead=''):
    return '<div class="w"><div class="bs" style="max-width:720px;margin-bottom:36px"><p class="et">%s</p><h2>%s</h2>%s</div>'%(et,h2,('<p class="lead" style="margin-top:14px">%s</p>'%lead) if lead else '')
SON=P['son']
# ---- ana sayfa
ETC_KISA=('<section class="sec etc" id="eticaret"><div class="w"><div class="g bas"><div class="b1"><p class="et kir">E-ticaret</p><h2>Mağazanız sitenizin içinde. Hepsi tek stoktan.</h2></div>'
 '<p class="lead b2">Sitenizden, pazaryerinden, telefondan ya da tezgâhtan gelen sipariş aynı listeye düşer.</p></div><div class="fg" style="margin-top:40px">'
 +kart('01','Ürün ve stok','Varyantlı ürünler, toplu içe aktarma, tek stok.','/e-ticaret.html#e-urun')
 +kart('02','Sipariş ve kargo','Siparişten kargoya tek akış.','/e-ticaret.html#e-siparis')
 +kart('03','Kampanya ve kupon','Yedi kampanya ve kupon türü.','/e-ticaret.html#e-kampanya')
 +kart('04','Pazaryerleri','Trendyol, Hepsiburada ve N11 hazır.','/e-ticaret.html#e-pazaryeri')
 +kart('05','Bayi (B2B)','Bayiye özel fiyat ve cari hesap.','/e-ticaret.html#e-bayi')
 +kart('06','Sepet ve ödeme','Kapıda ödeme, havale ve cari seçenekleri.','/e-ticaret.html#e-sepet')
 +'</div><p class="ka"><a class="btn dolu" href="/e-ticaret.html">Tüm e-ticaret özellikleri</a></p></div></section>')
home=duy+'' 
home_body=P['hero']+P['dort']+SERIT()+KAPI+P['tema']+ETC_KISA+P['edt']+P['yon']+P['guv']+SON
body=home_body
page('index.html','Web Sitesi, E-Ticaret, Randevu ve İş Takip Programı | OnlineKaydet','Hazır tema seçin, mağazanızı açın; randevu, muhasebe, personel ve iş takibini tek panelde yönetin. 70 sektör, e-ticaret ve pazaryeri entegrasyonu. Teklif alın.',body,home=True)
# duyuru çubuğunu ana sayfaya ekle
t=open(S+'/index.html',encoding='utf-8').read().replace('<a class="skip" href="#icerik">İçeriğe geç</a>','<a class="skip" href="#temalar">İçeriğe geç</a>'+duy,1)
t=t.replace('<main>','<main id="icerik">',1); open(S+'/index.html','w',encoding='utf-8').write(t)
# ---- iç sayfalar
B=banner
page('temalar.html','Hazır Web Sitesi Temaları | OnlineKaydet','Sektörünüze göre hazır web sitesi temaları. Seçin, metin ve görselleri panelden düzenleyin, alan adınızı bağlayın.',
 B('t','Temalar','Mesleğinize uygun hazır temalar','Birini seçin; yazıları ve resimleri panelden değiştirin. Menü, mobil alt çubuk ve alt bilgi hazır gelir.',('tema-1-kombi-d','Kombi servisi teması'))+P['tema']+P['sek']+SON)
page('e-ticaret.html','E-Ticaret Modülü: Ürün, Sipariş, Pazaryeri, B2B | OnlineKaydet','Ürün ve stok, sipariş ve kargo, kampanya, pazaryeri, iade, ortaklık ve bayi (B2B) tek panelde. Sitenizin içinde çalışan mağaza.',
 B('e','E-ticaret','Sitenizin içinde çalışan mağaza','Ürün, sipariş, kampanya ve pazaryeri satışı aynı panelden yürür.',('panel-d-urun','Ürün yönetimi ekranı'))+P['etc']+SON)
page('web-sitesi.html','Kodsuz Web Sitesi Editörü | OnlineKaydet','Web sitenizin her bölümünü panelden düzenleyin: metin, yazı tipi, görsel, menü. Alan adı ve SSL dahil.',
 B('w','Web sitesi','Sitenizi kendiniz düzenleyin','Yazı, yazı tipi, resim ve menü panelden değişir. Alan adı bağlama ve SSL pakete dahil.',('panel-d-site','Web sitesi editörü ekranı'))+P['edt']+P['guv']+SON)
page('is-takibi.html','Randevu, Muhasebe, Personel ve Evrak Takibi | OnlineKaydet','Randevu takvimi, kasa ve muhasebe, personel takibi, evrak takibi ve raporlar tek panelde.',
 B('i','İş takibi','Randevu, muhasebe, personel ve evrak takibi','Günlük işiniz tek ekranda: takvim, kasa, ekip ve raporlar.',('panel-k-takvim','Randevu takvimi ekranı'))+P['yon']+P['ent']+SON)
page('fiyatlar.html','Paketler ve Fiyatlar | OnlineKaydet','Web sitesi, mağaza ve iş takibi paketlerini ve içeriklerini karşılaştırın. E-ticaret modülü teklifle eklenir.',
 B('p','Paketler','Paketler ve içindekiler','Hangi pakette ne olduğu satır satır yazıyor. E-ticaret modülü teklifle eklenir.',('panel-k-kasa','Kasa ekranı'))+P['pak']+P['sss']+SON)
page('sektorler.html','Sektörlere Hazır Çözümler | OnlineKaydet','Teknik servis, kuaför, güzellik, oto servis ve diğer iş kolları için hazır tema ve panel.',
 B('s','Sektörler','Mesleğinize göre hazır','Teknik servisten kuaföre her iş kolunun kelimeleri ve ekranları hazır.',('tema-k6-butik-kuafor-d','Kuaför teması'))+P['sek']+P['ent']+P['tema']+SON)
page('sss.html','Sık Sorulan Sorular | OnlineKaydet','Deneme, veri taşıma, pazaryeri, paketler ve kurulum hakkında sık sorulan sorular.',
 B('sss','Sık sorulan sorular','Sık sorulanlar','Kurulum, paketler, pazaryeri ve veri taşıma hakkında kısa cevaplar.')+P['sss']+SON)
ozel=(sec_baslik('Özellikler','Panelde neler var?','Aşağıdaki başlıkların her biri kendi sayfasında anlatılır.')+'<div class="fg">'
 +kart('01','Randevu ve takvim','Günlük işleri takvimde toplayın.','/is-takibi.html')
 +kart('02','Kasa ve muhasebe','Tahsilat, gider ve raporlar.','/is-takibi.html')
 +kart('03','Personel takibi','Ekip, yetki ve iş dağılımı.','/is-takibi.html')
 +kart('04','Evrak takibi','Belgeleri müşteri ve işe bağlayın.','/is-takibi.html',True)
 +kart('05','Web sitesi editörü','Her bölüm panelden düzenlenir.','/web-sitesi.html')
 +kart('06','E-ticaret','Ürün, sipariş, kampanya, iade.','/e-ticaret.html')
 +kart('07','Pazaryeri','Trendyol, Hepsiburada ve N11.','/e-ticaret.html#e-pazaryeri')
 +kart('08','Bayi (B2B)','Bayiye özel fiyat ve cari hesap.','/e-ticaret.html#e-bayi')
 +kart('09','Hazır temalar','Sektörünüze göre başlayın.','/temalar.html')
 +'</div></div>')
page('ozellikler.html','Özellikler | Panelin Tüm Modülleri | OnlineKaydet','Randevu, kasa, muhasebe, personel, evrak, web sitesi editörü, e-ticaret, pazaryeri ve B2B modülleri.',
 B('o','Özellikler','Tek panel, bütün işler','Web sitesi, mağaza ve iş takibi aynı panelde çalışır.',('panel-d-ekip','Ekip ve yetki ekranı'))+'<section class="sec">'+ozel+'</section>'+P['dort']+SON)
hk=('<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Ne yapıyoruz?</h2><p>OnlineKaydet; web sitesi, e-ticaret, randevu ve iş takibini tek panelde toplar. Her firma sektörüne uygun hazır bir temayla başlar, metin ve görselleri panelden kendisi düzenler.</p>'
 '<h2>Kimler için?</h2><p>Kendi ekibiyle çalışan küçük ve orta ölçekli işletmeler için: teknik servisler, kuaför ve güzellik salonları, oto servisler, mağazalar ve bayiler.</p>'
 '<h2>Şirket</h2><p><b>Moda Ekru E-Ticaret Hizmetleri Tekstil Sanayi ve Ticaret Ltd. Şti.</b><br>Etimesgut, Ankara<br>Telefon: <a href="tel:+905444444004">0544 444 40 04</a></p></div></div></section>')
page('hakkimizda.html','Hakkımızda | OnlineKaydet','OnlineKaydet; web sitesi, e-ticaret, randevu ve iş takibini tek panelde toplayan, Ankara merkezli bir yazılımdır.',
 B('h','Hakkımızda','İşinizi tek panelde toplayan yazılım','Ankara merkezli ekibimiz web sitesi, mağaza ve iş takibini birlikte sunar.')+hk+P['guv']+SON)
ic=(sec_baslik('İletişim','Bize ulaşın','Aşağıdaki formu doldurun, sizi arayalım. Hemen konuşmak isterseniz arayın.')+'<div class="fg">'
 '<div class="fk"><span class="no">Telefon</span><h3>0544 444 40 04</h3><p>Satış ve kurulum için doğrudan arayın.</p><a href="tel:+905444444004">Hemen arayın</a></div>'
 '<div class="fk"><span class="no">WhatsApp</span><h3>Mesaj yazın</h3><p>Soru sorun, ekran görüntüsü gönderin.</p><a href="https://wa.me/905444444004">WhatsApp\'ta yazın</a></div>'
 '<div class="fk"><span class="no">Müşteri girişi</span><h3>Panele girin</h3><p>Mevcut müşteriler ve ustalar için.</p><a href="/uye-girisi">Giriş yapın</a></div>'
 '</div></div>')
page('iletisim.html','İletişim | OnlineKaydet','OnlineKaydet iletişim: telefon, WhatsApp ve teklif formu. Etimesgut, Ankara.',
 B('c','İletişim','Sizi arayalım','Formu doldurun, sektörünüzü not alalım, kurulum için sizi arayalım.')+'<section class="sec">'+ic+'</section>'+SON)
