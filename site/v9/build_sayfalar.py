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

SEKT_AD={}
SLUG_ONCE={'kombi','klima','beyaz_esya','bilgisayar','elektrik','elektronik','guvenlik','tesisat'}
sys_path=__import__('sys').path;sys_path.insert(0,os.path.join(os.path.dirname(S),'panel'))
import sitegen as _g
SEKT=list(_g.SECTORS.items())
SEKT_AD.update({'sektor-%s.html'%k.replace('_','-'):a for k,a in SEKT})
def sektor_url(k): return '/sektor-%s.html'%k.replace('_','-')
ESLE={'Teknik servis':'kombi','Kuaför ve güzellik':'kuafor','E-ticaret':'eticaret','Oto servis':'oto_servis','Avukat ve danışmanlık':'avukat','Diş, estetik ve sağlık':'dis_klinigi','Veteriner':'veteriner','Restoran ve kafe':'lokanta','Emlak':'emlakci','Sürücü kursu':'surucu_kursu','Kurs ve eğitim':'etut_merkezi','Fitness ve pilates':'spor_salonu','Market ve bakkal':'market','Temizlik hizmetleri':'temizlik','Düğün ve organizasyon':'dugun_salonu'}
def sektor_chip(m):
    ad=m.group(1)
    if ad=='70 sektörün tamamı': return '<a class="hep" href="/tum-sektorler.html">%d sektörün tamamı</a>'%len(SEKT)
    if ad in ESLE: return '<a href="%s">%s</a>'%(sektor_url(ESLE[ad]),ad)
    if ad=='Paketleri ayrıntılı karşılaştırın': return '<a href="/fiyatlar.html">%s</a>'%ad
    if ad=='Otel ve pansiyon': return '<a href="/tum-sektorler.html">%s</a>'%ad
    return m.group(0)
for k_ in list(P):
    P[k_]=_re.sub(r'<a (?:class="hep" )?href="#">([^<]*)</a>',sektor_chip,P[k_])
    P[k_]=P[k_].replace('70 sektör','%d sektör'%len(SEKT)).replace('70 iş kolu','%d iş kolu'%len(SEKT))
    P[k_]=P[k_].replace('<b>Kodda doğrulanan</b>','<b>Hazır pazaryerleri</b>').replace('<b>Katalogda, bağlantısı hazırlanıyor</b>','<b>Bunlar da hazır</b>')
head_raw=src[:src.index('<script type="application/ld+json">')]
jsonld=src[src.index('<script type="application/ld+json">'):src.index('</script>',src.index('<script type="application/ld+json">'))+9]
mbar=src[src.index('<div class="mbar">'):src.index('<script src="/v9/v9.js"')]
foot=('<footer class="alt2"><div class="w"><div class="g">'
 '<div class="f1"><img src="/logo-renkli-s.png" alt="OnlineKaydet" width="140" height="28"><p>Web sitesi, e-ticaret, randevu ve iş takibi tek panelde.</p>'
 '<div class="sos"><a href="#" onclick="return false" aria-label="Instagram"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r="1" fill="currentColor" stroke="none"/></svg></a>'
 '<a href="#" onclick="return false" aria-label="X"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 4l16 16M20 4L4 20"/></svg></a>'
 '<a href="#" onclick="return false" aria-label="YouTube"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="2.5" y="5.5" width="19" height="13" rx="4"/><path d="M10 9.2v5.6l4.8-2.8z" fill="currentColor"/></svg></a></div></div>'
 '<div><b>Ürün</b><a href="/temalar.html">Temalar</a><a href="/e-ticaret.html">E-ticaret</a><a href="/web-sitesi.html">Web sitesi editörü</a><a href="/is-takibi.html">Randevu ve iş takibi</a><a href="/fiyatlar.html">Paketler</a></div>'
 '<div><b>Sektörler</b><a href="/sektor-kombi.html">Teknik servis</a><a href="/sektor-kuafor.html">Kuaför</a><a href="/sektor-eticaret.html">E-ticaret</a><a href="/tum-sektorler.html">Tüm sektörler</a></div>'
 '<div><b>Kaynak</b><a href="/blog.html">Blog</a><a href="/entegrasyonlar.html">Entegrasyonlar</a><a href="/bilgi-bankasi.html">Bilgi bankası</a><a href="/destek.html">Destek</a><a href="/uye-girisi">Üye girişi</a></div>'
 '<div><b>Şirket</b><a href="/hakkimizda.html">Hakkımızda</a><a href="/iletisim.html">İletişim</a><a href="/kvkk.html">KVKK</a><a href="/gizlilik.html">Gizlilik</a><a href="/cerez-politikasi.html">Çerez politikası</a><a href="/kullanim-kosullari.html">Kullanım koşulları</a><a href="/mesafeli-satis-iade.html">Mesafeli satış ve iade</a></div>'
 '</div><div class="alt"><span>© 2026 OnlineKaydet</span><span class="kart" aria-label="Kabul edilen kartlar">'
 '<svg viewBox="0 0 64 40" width="52" height="32" role="img" aria-label="Visa"><rect width="64" height="40" rx="6" fill="#fff" stroke="#cfd6df"/><text x="32" y="27" text-anchor="middle" font-family="Arial,sans-serif" font-weight="800" font-style="italic" font-size="19" fill="#1a3a8f">VISA</text></svg>'
 '<svg viewBox="0 0 64 40" width="52" height="32" role="img" aria-label="Mastercard"><rect width="64" height="40" rx="6" fill="#fff" stroke="#cfd6df"/><circle cx="26" cy="20" r="11" fill="#eb001b"/><circle cx="38" cy="20" r="11" fill="#f79e1b"/><path d="M32 11.2a11 11 0 0 1 0 17.6 11 11 0 0 1 0-17.6z" fill="#ff5f00"/></svg></span></div></div></footer>')
SEC={'temalar':'/temalar.html','eticaret':'/e-ticaret.html','editor':'/web-sitesi.html','yonetim':'/is-takibi.html','paketler':'/fiyatlar.html','sektorler':'/sektorler.html'}
NAV=[('Temalar','/temalar.html'),('E-ticaret','/e-ticaret.html'),('Web sitesi','/web-sitesi.html'),('İş takibi','/is-takibi.html'),('Paketler','/fiyatlar.html'),('Sektörler','/sektorler.html'),('Bilgi bankası','/bilgi-bankasi.html')]
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
SON_=''
TKB={'e-ticaret.html':('Mağazanız için teklif alın','Ürün, sipariş ve pazaryeri kurulumunu birlikte planlayalım.'),'web-sitesi.html':('Web siteniz için teklif alın','Temanızı birlikte seçelim, alan adı ve kurulum bizden.'),'is-takibi.html':('İş takibi için teklif alın','Randevu, kasa ve ekip düzeninizi işinize göre kuralım.'),'fiyatlar.html':('Paketiniz için teklif alın','İhtiyacınıza uygun paketi ve fiyatı birlikte belirleyelim.'),'temalar.html':('Seçtiğiniz tema için teklif alın','Temanızı kurup bilgilerinizi birlikte girelim.'),'sektorler.html':('İş kolunuz için teklif alın','Mesleğinize uygun temayı ve paneli birlikte hazırlayalım.')}
def page(slug,title,desc,body,ld=None,home=False,robots=None,extra_head='',extra_js='',ld_raw=None):
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
    if robots: h=re.sub(r'(<meta name="robots" content=")[^"]*',lambda m:m.group(1)+robots,h)
    if ld_raw is not None: lj=ld_raw
    cur='/' if home else '/'+slug
    body=body.replace('href="iletisim.html#form"','href="/iletisim.html#teklif"').replace('href="/iletisim.html#form"','href="/iletisim.html#teklif"')
    NOFORM='id="teklif"' not in body
    full=h+extra_head+lj+'\n</head><body>\n<a class="skip" href="#icerik">İçeriğe geç</a>'+hdr(cur)+'\n<main>'+body+'</main>\n'+foot+'\n'+mbar+'<script src="/v9/v9.js" defer></script><script src="/v9/v10.js" defer></script>'+('<script src="/v9/dunya.js" defer></script>' if home else '')+'<script src="/lead.js" defer></script>'+extra_js+'</body></html>'
    full=_re.sub(r'<a (class="btn[^"]*") href="#">([^<]*)</a>',lambda m:'<a %s href="%s">%s</a>'%(m.group(1),'/demo.html' if 'deneyin' in m.group(2).lower() or 'tema' in m.group(2).lower() else ('#teklif' if 'teklif' in m.group(2).lower() else '/iletisim.html'),m.group(2)),full)
    tk=TKB.get(slug)
    if not tk and slug.startswith('sektor-') and slug in SEKT_AD: tk=('%s için teklif alın'%SEKT_AD[slug],'Sektörünüze uygun temayı ve paneli birlikte hazırlayalım.')
    if tk and 'id="teklif"' in full:
        full=full.replace('<h2>Temanızı bugün seçin, mağazanızı bu hafta açın.</h2>','<h2>%s</h2><p class="lead">%s</p>'%(html.escape(tk[0]),html.escape(tk[1])),1).replace('<b style="font:700 24px/1 var(--fd);letter-spacing:-.02em">Teklif alın</b>','<b style="font:700 24px/1.15 var(--fd);letter-spacing:-.02em">%s</b>'%html.escape(tk[0]),1)
    if NOFORM: full=full.replace('href="#teklif"','href="/iletisim.html#teklif"')
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

def px(i,alt,w=900):
    return '<img src="https://images.pexels.com/photos/%s/pexels-photo-%s.jpeg?auto=compress&cs=tinysrgb&w=%d" alt="%s" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.closest(\'figure\').style.display=\'none\'">'%(i,i,w,html.escape(alt))
def fbant(et,h2,lead,items,cls='f3',link=None):
    fs=''.join('<figure><div class="fi">%s</div><figcaption>%s</figcaption></figure>'%(px(i,a),c) for i,a,c in items)
    ln='<a class="btn dolu kc" href="%s">%s</a>'%link if link else ''
    return '<section class="sec fbant"><div class="w"><div class="bs"><p class="et">%s</p><h2>%s</h2>%s</div><div class="fg2 %s">%s</div>%s</div></section>'%(et,h2,('<p class="lead">%s</p>'%lead) if lead else '',cls,fs,ln)
FOTO_ANA=fbant('Her iş koluna uyar','Kuaförden kafeye, oto servisten butiğe.','Sektörünüzü seçin, kelimeleri ve ekranları hazır gelsin.',[('33448218','Kuaför müşterinin saçını kesiyor','Kuaför'),('14656012','Çiçekçi','Çiçekçi'),('36643337','Barista latte art yapıyor','Kafe'),('3807811','Aracın altında çalışan usta','Oto servis'),('6667684','Gönderi için paketlenen kolilier'.replace('kolilier','koliler'),'Kargo ve paket'),('6539022','Butik','Butik')],'f6',('/sektorler.html','Tüm sektörleri görün'))
FOTO_ETC=fbant('Online satış','Telefondan sipariş, kapınıza kargo.','',[('6214382','Akıllı telefonla çevrimiçi alışveriş','Siparişler telefondan gelir'),('6667684','Paketleme ve teslimat','Paketle ve kargoya ver'),('6539022','Butik ürünü','Mağazanız sitenizin içinde')])
FOTO_WEB=fbant('Kendi sitenizi yönetin','Kahvenizi alın, sitenizi güncelleyin.','',[('36072623','Kahve ve dizüstü bilgisayarın bulunduğu çalışma alanı','Yazıyı siz değiştirirsiniz'),('6207729','Ellerde dizüstü bilgisayar','Resmi siz yüklersiniz')],'f2')
FOTO_IS=fbant('Günlük iş','Not defteri yerine tek ekran.','',[('7876381','Kalem tutan eller','Randevu ve notlar'),('8296969','Masada çalışan eller','Ekip ve evrak')],'f2')
FOTO_SEK=fbant('İş kolları','Hangi meslekteyseniz, tema hazır.','',[('33448218','Kuaför','Kuaför'),('3993310','Güzellik salonu iç mekân','Güzellik salonu'),('14656012','Çiçekçi','Çiçekçi'),('17247840','Kahve fincanları','Kafe'),('3807811','Oto servis','Oto servis'),('15372566','Restoran','Restoran'),('14554082','Fayans','Yapı malzemesi'),('3993449','Profesyonel kuaför','Güzellik')],'f4')
FOTO_ALT=fbant('Altyapı','Verileriniz Türkiye\'deki sunucularda.','Sitenizin ve panelinizin altyapısı Türkiye\'de çalışır.',[('1054397','Sunucu rafına takılı ethernet kabloları','Sunucular'),('2881232','Ethernet bağlantı noktalarına bağlı kablolar','Ağ bağlantısı')],'f2')
P['son']=_re.sub(r'<div class="alan"><label for="tf4">Sektörünüz</label><select id="tf4">.*?</select></div>','',P['son'],flags=_re.S)
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

DUNYA=('<section class="dnya" id="dunya-bolum"><div class="w"><div class="bs"><p class="et">Her yerden gelen iş</p><h2>Siteniz dünyaya açık, gelen iş tek panelde.</h2>'
 '<p class="lead">Siteden, pazaryerinden, telefonla ya da WhatsApp\'tan gelen sipariş ve randevu aynı listeye girer.</p></div>'
 '<div class="sh"><canvas id="dunya" role="img" aria-label="Dünyanın her yerinden gelen siparişler OnlineKaydet paneline akıyor"></canvas>'
 '<div class="dk" id="dunyakart"><div class="dh"><img src="/logo-renkli-s.png" alt="OnlineKaydet" width="140" height="28"><span class="mo2">Bugün</span></div>'
 '<ul><li><b>Yeni sipariş</b><span>Kendi sitem · 5.400 ₺</span></li><li><b>Randevu</b><span>Cuma 14:30 · Sitenizden</span></li><li><b>Pazaryeri</b><span>Trendyol siparişi</span></li><li><b>Telefon</b><span>Servis kaydı açıldı</span></li></ul></div></div>'
 '<ul class="kn2"><li>Web sitesi</li><li>Pazaryeri</li><li>Telefon</li><li>WhatsApp</li><li>Randevu</li></ul></div></section>')
home=duy+'' 
home_body=P['hero']+P['dort']+SERIT()+DUNYA+KAPI+FOTO_ANA+P['tema']+ETC_KISA+P['edt']+P['yon']+P['guv']+SON
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
 B('e','E-ticaret','Sitenizin içinde çalışan mağaza','Ürün, sipariş, kampanya ve pazaryeri satışı aynı panelden yürür.',('panel-d-urun','Ürün yönetimi ekranı'))+FOTO_ETC+P['etc']+SON)
page('web-sitesi.html','Kodsuz Web Sitesi Editörü | OnlineKaydet','Web sitenizin her bölümünü panelden düzenleyin: metin, yazı tipi, görsel, menü. Alan adı ve SSL dahil.',
 B('w','Web sitesi','Sitenizi kendiniz düzenleyin','Yazı, yazı tipi, resim ve menü panelden değişir. Alan adı bağlama ve SSL pakete dahil.',('panel-d-site','Web sitesi editörü ekranı'))+FOTO_WEB+P['edt']+P['guv']+SON)
page('is-takibi.html','Randevu, Muhasebe, Personel ve Evrak Takibi | OnlineKaydet','Randevu takvimi, kasa ve muhasebe, personel takibi, evrak takibi ve raporlar tek panelde.',
 B('i','İş takibi','Randevu, muhasebe, personel ve evrak takibi','Günlük işiniz tek ekranda: takvim, kasa, ekip ve raporlar.',('panel-k-takvim','Randevu takvimi ekranı'))+FOTO_IS+P['yon']+P['ent']+SON)
page('fiyatlar.html','Paketler ve Fiyatlar | OnlineKaydet','Web sitesi, mağaza ve iş takibi paketlerini ve içeriklerini karşılaştırın. E-ticaret modülü teklifle eklenir.',
 B('p','Paketler','Paketler ve içindekiler','Hangi pakette ne olduğu satır satır yazıyor. E-ticaret modülü teklifle eklenir.',('panel-k-kasa','Kasa ekranı'))+P['pak']+P['sss']+SON)
page('sektorler.html','Sektörlere Hazır Çözümler | OnlineKaydet','Teknik servis, kuaför, güzellik, oto servis ve diğer iş kolları için hazır tema ve panel.',
 B('s','Sektörler','Mesleğinize göre hazır','Teknik servisten kuaföre her iş kolunun kelimeleri ve ekranları hazır.',('tema-k6-butik-kuafor-d','Kuaför teması'))+FOTO_SEK+P['sek']+P['ent']+P['tema']+SON)
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
 B('h','Hakkımızda','İşinizi tek panelde toplayan yazılım','Ankara merkezli ekibimiz web sitesi, mağaza ve iş takibini birlikte sunar.')+hk+FOTO_ALT+P['guv']+SON)
ic=(sec_baslik('İletişim','Bize ulaşın','Aşağıdaki formu doldurun, sizi arayalım. Hemen konuşmak isterseniz arayın.')+'<div class="fg">'
 '<div class="fk"><span class="no">Telefon</span><h3>0544 444 40 04</h3><p>Satış ve kurulum için doğrudan arayın.</p><a href="tel:+905444444004">Hemen arayın</a></div>'
 '<div class="fk"><span class="no">WhatsApp</span><h3>Mesaj yazın</h3><p>Soru sorun, ekran görüntüsü gönderin.</p><a href="https://wa.me/905444444004">WhatsApp\'ta yazın</a></div>'
 '<div class="fk"><span class="no">Müşteri girişi</span><h3>Panele girin</h3><p>Mevcut müşteriler ve ustalar için.</p><a href="/uye-girisi">Giriş yapın</a></div>'
 '</div></div>')
page('iletisim.html','İletişim | OnlineKaydet','OnlineKaydet iletişim: telefon, WhatsApp ve teklif formu. Etimesgut, Ankara.',
 B('c','İletişim','Sizi arayalım','Formu doldurun, sektörünüzü not alalım, kurulum için sizi arayalım.')+'<section class="sec">'+ic+'</section>'+SON)


# ---- sektör sayfaları ve yasal sayfalar
import sektor_cok2 as _c2
DET={r[0]:r for r in _c2.R}
CTA=('<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Hemen deneyin</h2><p>Demo hesabını 7 gün ücretsiz kullanın ya da formu doldurun, sizi arayalım.</p>'
 '<p><a class="btn dolu" href="/demo.html">Ücretsiz deneyin</a> <a class="btn bos2" href="/iletisim.html#teklif">Teklif alın</a></p></div></div></section>')
GEN_OZ=[('Müşteri ve iş kaydı','Her müşteri ve iş tek kayıtta durur, geçmişi görürsünüz.'),('Randevu ve takvim','Randevuları takvimden yönetir, hatırlatma mesajı gönderirsiniz.'),('Kasa ve raporlar','Gelir, gider ve borç takibi panelde, raporlar tek ekranda.'),('Web siteniz','Sektörünüze hazır tema; yazı ve resimleri panelden değiştirirsiniz.')]
for k,ad in SEKT:
    if k in SLUG_ONCE: continue
    d=DET.get(k)
    uzun=d[1] if d else ad
    oz=d[6] if d else GEN_OZ
    ish=d[7] if d else []
    kart_=''.join('<div class="fk"><span class="no">%02d</span><h3>%s</h3><p>%s</p></div>'%(i+1,html.escape(a),html.escape(t)) for i,(a,t) in enumerate(oz))
    chips=('<p style="margin-top:22px"><b>Panelde hazır işlem türleri:</b> '+' · '.join(html.escape(x) for x in ish)+'</p>') if ish else ''
    body=B('s-'+k,uzun,'%s için web sitesi ve iş takibi'%uzun,'Sektörünüze hazır tema ve panel: kayıtlar, randevular, kasa ve web siteniz tek yerde.')+'<section class="sec"><div class="w"><div class="fg">'+kart_+'</div>'+chips+'</div></section>'+CTA+SON
    page('sektor-%s.html'%k.replace('_','-'),'%s İçin Web Sitesi ve İş Takip Programı | OnlineKaydet'%uzun,'%s için hazır web sitesi teması, randevu, kasa ve iş takibi. Ücretsiz deneyin.'%uzun,body)
lst=''.join('<a href="%s">%s</a>'%(sektor_url(k),html.escape(a)) for k,a in SEKT)
page('tum-sektorler.html','Tüm Sektörler (%d iş kolu) | OnlineKaydet'%len(SEKT),'OnlineKaydet’in hazır tema ve panel sunduğu %d iş kolunun tam listesi.'%len(SEKT),
 B('ts','Tüm sektörler','%d iş kolu için hazır'%len(SEKT),'Mesleğinizi seçin; temayı, kelimeleri ve ekranları görün.')+'<section class="sec"><div class="w"><div class="slst">'+lst+'</div></div></section>'+CTA+SON)
FIRMA='Moda Ekru E-Ticaret Hizmetleri Tekstil Sanayi ve Ticaret Ltd. Şti.'
def yasal(slug,ad,desc,icerik):
    page(slug,ad+' | OnlineKaydet',desc,B('y',ad,ad,desc)+'<section class="sec"><div class="w"><div class="yz">'+icerik+'</div></div></section>'+SON)
yasal('cerez-politikasi.html','Çerez Politikası','Sitede hangi çerezlerin kullanıldığını ve nasıl yönetebileceğinizi açıklıyoruz.',
 '<h2 style="margin-top:0">Çerez nedir?</h2><p>Çerezler, ziyaret ettiğiniz sitenin tarayıcınıza yerleştirdiği küçük metin dosyalarıdır.</p>'
 '<h2>Hangi çerezleri kullanıyoruz?</h2><p>Site yalnızca çalışması için gerekli çerezleri ve oturum bilgilerini kullanır (örneğin üye girişi ve form gönderimi). Reklam veya izleme amaçlı çerez kullanmıyoruz. İleride analitik bir araç eklenirse bu sayfa güncellenir ve onayınız istenir.</p>'
 '<h2>Çerezleri nasıl yönetirsiniz?</h2><p>Tarayıcı ayarlarınızdan çerezleri silebilir veya engelleyebilirsiniz. Gerekli çerezleri engellerseniz üye girişi gibi bazı bölümler çalışmayabilir.</p>'
 '<h2>İletişim</h2><p>%s, Etimesgut, Ankara. Telefon: <a href="tel:+905444444004">0544 444 40 04</a>. Kişisel verileriniz için <a href="/kvkk.html">KVKK aydınlatma metni</a>.</p>'%FIRMA)
yasal('kullanim-kosullari.html','Kullanım Koşulları','OnlineKaydet web sitesini ve panelini kullanırken geçerli olan koşullar.',
 '<h2 style="margin-top:0">Taraflar</h2><p>Bu koşullar, %s (“OnlineKaydet”) ile siteyi ve paneli kullanan kişi veya firma arasındadır.</p>'%FIRMA+
 '<h2>Hizmet</h2><p>OnlineKaydet; web sitesi, e-ticaret, randevu ve iş takibi için bir yazılım hizmetidir. Kapsam, seçtiğiniz pakete göre belirlenir ve <a href="/fiyatlar.html">paketler sayfasında</a> yazılıdır.</p>'
 '<h2>Hesap ve güvenlik</h2><p>Hesap bilgilerinizin gizliliğinden ve hesabınızda yapılan işlemlerden siz sorumlusunuz. Yetkisiz kullanımdan haberiniz olursa bize hemen bildirin.</p>'
 '<h2>İçerik</h2><p>Siteye ve panele yüklediğiniz yazı, görsel ve verilerin hukuka uygunluğu size aittir. Başkasının telif hakkını ihlal eden içerik yüklenemez.</p>'
 '<h2>Ücret ve iptal</h2><p>Ücretler paket sayfasında belirtilir. Aboneliği dilediğiniz zaman sonlandırabilirsiniz; ödenmiş dönem için koşullar <a href="/mesafeli-satis-iade.html">mesafeli satış ve iade</a> sayfasındadır.</p>'
 '<h2>Değişiklik</h2><p>Bu koşullar güncellenebilir; güncel hâli bu sayfada yayımlanır.</p><h2>İletişim</h2><p><a href="tel:+905444444004">0544 444 40 04</a> · <a href="/iletisim.html">İletişim formu</a></p>')
yasal('mesafeli-satis-iade.html','Mesafeli Satış ve İade Koşulları','Online satın alınan hizmetlerde cayma, iptal ve iade koşulları.',
 '<h2 style="margin-top:0">Satıcı</h2><p>%s, Etimesgut, Ankara. Telefon: <a href="tel:+905444444004">0544 444 40 04</a>.</p>'%FIRMA+
 '<h2>Hizmetin niteliği</h2><p>Sattığımız ürün, dijital bir yazılım hizmetidir (web sitesi, panel ve ilgili modüller). Hizmet, ödeme ve kurulumun ardından dijital ortamda sunulur; fiziksel teslimat yoktur.</p>'
 '<h2>Cayma hakkı</h2><p>6502 sayılı Tüketicinin Korunması Hakkında Kanun ve Mesafeli Sözleşmeler Yönetmeliği uyarınca, tüketici olarak 14 gün içinde cayma hakkınızı kullanabilirsiniz. Hizmetin ifasına, cayma süresi bitmeden sizin onayınızla başlanmışsa, yönetmelikte belirtilen hâllerde cayma hakkı kullanılamaz veya yalnızca kullanılmayan kısım için iade yapılır.</p>'
 '<h2>İade nasıl yapılır?</h2><p>İade talebinizi <a href="/iletisim.html">iletişim formundan</a> veya telefonla iletin. Onaylanan iade, ödemenizi yaptığınız yönteme geri yapılır.</p>'
 '<h2>Ücretsiz deneme</h2><p>Demo hesabı 7 gün ücretsizdir ve satın alma yükümlülüğü doğurmaz.</p>'
 '<h2>Uyuşmazlık</h2><p>Uyuşmazlıklarda Ticaret Bakanlığı’nca her yıl belirlenen parasal sınırlar dahilinde il ve ilçe tüketici hakem heyetleri ile tüketici mahkemeleri yetkilidir.</p>')


# ---- bilgi bankası
import bilgi_icerik as _bi
BK=_bi.A
kart_b=''.join('<a href="/bilgi-%s.html"><span>%s</span><h3>%s</h3><p>%s</p></a>'%(a['slug'],a['kat'],html.escape(a['ad']),html.escape(a['ozet'])) for a in BK)
page('bilgi-bankasi.html','Bilgi Bankası: Ürün Ekleme, Pazaryeri, Randevu, Kasa, İlan | OnlineKaydet','Panelin adım adım kullanım rehberi: ürün ekleme, pazaryerine gönderme, sipariş, randevu, müşteri, kasa, ekip, ilan ve web sitesi düzenleme.',
 B('b','Bilgi bankası','Paneli adım adım öğrenin','Her işlem için kısa, adım adım rehber. İstediğiniz konuyu seçin.')+'<section class="sec"><div class="w"><div class="bk">'+kart_b+'</div></div></section>'+CTA+SON)
for i,a in enumerate(BK):
    diger=''.join('<a href="/bilgi-%s.html">%s</a>'%(x['slug'],html.escape(x['ad'])) for x in BK if x is not a)
    ld='<script type="application/ld+json">'+__import__('json').dumps({'@context':'https://schema.org','@type':'HowTo','name':a['ad'],'description':a['ozet'],'inLanguage':'tr'},ensure_ascii=False)+'</script>'
    body=B('b-'+a['slug'],'<a href="/bilgi-bankasi.html">Bilgi bankası</a> / '+html.escape(a['kat']),a['ad'],a['ozet'])+'<section class="sec"><div class="w"><div class="yz">'+a['body']+'</div></div></section><section class="sec"><div class="w"><h2 style="margin-top:0">Diğer rehberler</h2><div class="bk2">'+diger+'</div></div></section>'+CTA+SON
    page('bilgi-%s.html'%a['slug'],a['ad']+' | Bilgi Bankası | OnlineKaydet',a['ozet'],body,ld_raw=ld)

# ---- eski sayfalar: içerik yeni kabuğa taşınır
import glob
ESKI_CSS={'mobil.css':'eski-mobil.css','yeni.css':'eski-yeni.css','ic1.css':'eski-ic1.css','ic2.css':'eski-ic2.css','sayfalar.css':'eski-sayfalar.css','sektor.css':'eski-sektor.css'}
for f in sorted(glob.glob(H+'/kaynak/eski/*.html')):
    nm=os.path.basename(f);o=open(f,encoding='utf-8').read()
    m=re.search(r'<main[^>]*>(.*)</main>',o,re.S)
    if not m: continue
    main=m.group(1)
    sp=re.search(r'<svg[^>]*(?:display:none|hidden|width="0")[^>]*>.*?</svg>',o,re.S)
    spr=sp.group(0) if sp and sp.group(0) not in main else ''
    t=re.search(r'<title>(.*?)</title>',o,re.S).group(1)
    dsc=(re.search(r'<meta name="description" content="([^"]*)"',o) or [0,''])[1]
    rb=(re.search(r'<meta name="robots" content="([^"]*)"',o) or [0,'index,follow'])[1]
    lds=''.join(re.findall(r'<script type="application/ld\+json">.*?</script>',o,re.S))
    css=''.join('<link rel="stylesheet" href="/v9/%s">'%ESKI_CSS[c] for c in re.findall(r'href="([^"]+\.css)"',o) if c in ESKI_CSS)
    main=main.replace('index.html#kayit','/iletisim.html#teklif')
    body=spr+'<div class="eski"><div id="icerik">'+main+'</div></div>'
    # <main> etiketi kabukta zaten var; içerik id'si çakışmasın
    body=body.replace('id="icerik"','',1) if False else body
    page(nm,html.unescape(t),html.unescape(dsc),body,robots=rb,extra_head=css,ld_raw=lds or None,extra_js='<script src="/site.js" defer></script>' if 'src="site.js"' in o else '')
