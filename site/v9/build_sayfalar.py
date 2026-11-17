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
APP_STORE_URL='';PLAY_URL=''   # mobil uygulama yayınlanınca buraya bağlantıyı yazın
def _rozet(ad,alt,url,svg):
    ic='<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>'%svg
    ic_=('<a class="rz" href="%s" rel="noopener" target="_blank">%s<span><small>%s</small><b>%s</b></span></a>'%(url,ic,alt,ad)) if url else ('<span class="rz yak" aria-label="%s, yakında">%s<span><small>Yakında</small><b>%s</b></span></span>'%(ad,ic,ad))
    return ic_
STORE=('<div class="mag"><span class="mgb">Mobil uygulama</span>'
 +_rozet('App Store','İndirin',APP_STORE_URL,'<rect x="6" y="2.5" width="12" height="19" rx="3"/><path d="M10.5 18.5h3"/>')
 +_rozet('Google Play','Edinin',PLAY_URL,'<rect x="6" y="2.5" width="12" height="19" rx="3"/><path d="M10.5 18.5h3"/>')+'</div>')
foot=('<footer class="alt2"><div class="w"><div class="g">'
 '<div class="f1"><img src="/logo-renkli-s.png" alt="OnlineKaydet" width="140" height="28"><p>Web sitesi, e-ticaret, randevu ve iş takibi tek panelde.</p>'
 '<div class="sos"><a href="#" onclick="return false" aria-label="Instagram" style="color:#E4405F"><svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M7.0301.084c-1.2768.0602-2.1487.264-2.911.5634-.7888.3075-1.4575.72-2.1228 1.3877-.6652.6677-1.075 1.3368-1.3802 2.127-.2954.7638-.4956 1.6365-.552 2.914-.0564 1.2775-.0689 1.6882-.0626 4.947.0062 3.2586.0206 3.6671.0825 4.9473.061 1.2765.264 2.1482.5635 2.9107.308.7889.72 1.4573 1.388 2.1228.6679.6655 1.3365 1.0743 2.1285 1.38.7632.295 1.6361.4961 2.9134.552 1.2773.056 1.6884.069 4.9462.0627 3.2578-.0062 3.668-.0207 4.9478-.0814 1.28-.0607 2.147-.2652 2.9098-.5633.7889-.3086 1.4578-.72 2.1228-1.3881.665-.6682 1.0745-1.3378 1.3795-2.1284.2957-.7632.4966-1.636.552-2.9124.056-1.2809.0692-1.6898.063-4.948-.0063-3.2583-.021-3.6668-.0817-4.9465-.0607-1.2797-.264-2.1487-.5633-2.9117-.3084-.7889-.72-1.4568-1.3876-2.1228C21.2982 1.33 20.628.9208 19.8378.6165 19.074.321 18.2017.1197 16.9244.0645 15.6471.0093 15.236-.005 11.977.0014 8.718.0076 8.31.0215 7.0301.0839m.1402 21.6932c-1.17-.0509-1.8053-.2453-2.2287-.408-.5606-.216-.96-.4771-1.3819-.895-.422-.4178-.6811-.8186-.9-1.378-.1644-.4234-.3624-1.058-.4171-2.228-.0595-1.2645-.072-1.6442-.079-4.848-.007-3.2037.0053-3.583.0607-4.848.05-1.169.2456-1.805.408-2.2282.216-.5613.4762-.96.895-1.3816.4188-.4217.8184-.6814 1.3783-.9003.423-.1651 1.0575-.3614 2.227-.4171 1.2655-.06 1.6447-.072 4.848-.079 3.2033-.007 3.5835.005 4.8495.0608 1.169.0508 1.8053.2445 2.228.408.5608.216.96.4754 1.3816.895.4217.4194.6816.8176.9005 1.3787.1653.4217.3617 1.056.4169 2.2263.0602 1.2655.0739 1.645.0796 4.848.0058 3.203-.0055 3.5834-.061 4.848-.051 1.17-.245 1.8055-.408 2.2294-.216.5604-.4763.96-.8954 1.3814-.419.4215-.8181.6811-1.3783.9-.4224.1649-1.0577.3617-2.2262.4174-1.2656.0595-1.6448.072-4.8493.079-3.2045.007-3.5825-.006-4.848-.0608M16.953 5.5864A1.44 1.44 0 1 0 18.39 4.144a1.44 1.44 0 0 0-1.437 1.4424M5.8385 12.012c.0067 3.4032 2.7706 6.1557 6.173 6.1493 3.4026-.0065 6.157-2.7701 6.1506-6.1733-.0065-3.4032-2.771-6.1565-6.174-6.1498-3.403.0067-6.156 2.771-6.1496 6.1738M8 12.0077a4 4 0 1 1 4.008 3.9921A3.9996 3.9996 0 0 1 8 12.0077"/></svg></a><a href="#" onclick="return false" aria-label="X" style="color:#2b3340"><svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/></svg></a><a href="#" onclick="return false" aria-label="YouTube" style="color:#FF0000"><svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg></a></div></div>'
 '<div><b>Ürün</b><a href="/temalar.html">Temalar</a><a href="/e-ticaret.html">E-ticaret</a><a href="/web-sitesi.html">Web sitesi editörü</a><a href="/is-takibi.html">Randevu ve iş takibi</a><a href="/muhasebe-ve-stok.html">Muhasebe ve stok</a><a href="/fiyatlar.html">Paketler</a></div>'
 '<div><b>Sektörler</b><a href="/sektor-kombi.html">Teknik servis</a><a href="/sektor-kuafor.html">Kuaför</a><a href="/sektor-eticaret.html">E-ticaret</a><a href="/tum-sektorler.html">Tüm sektörler</a></div>'
 '<div><b>Kaynak</b><a href="/blog.html">Blog</a><a href="/entegrasyonlar.html">Entegrasyonlar</a><a href="/bilgi-bankasi.html">Bilgi bankası</a><a href="/destek.html">Destek</a><a href="/hesaplama-araclari.html">Hesaplama araçları</a><a href="/uye-girisi">Üye girişi</a></div>'
 '<div><b>Şirket</b><a href="/hakkimizda.html">Hakkımızda</a><a href="/iletisim.html">İletişim</a><a href="/bayilik.html">Bayilik</a><a href="/ozel-tasarim.html">Özel tasarım</a><a href="/sikayet-ve-oneri.html">Şikayet ve öneri</a></div>'
 '<div><b>Teknoloji ve güvenlik</b><a href="/altyapi-ve-teknoloji.html">Altyapı ve teknoloji</a><a href="/bilgi-ve-veri-guvenligi.html">Bilgi ve veri güvenliği</a><a href="/hesap-guvenligi.html">Hesap güvenliği</a><a href="/yedekleme-ve-denetim.html">Yedekleme ve denetim kaydı</a></div>'
 '</div>'+STORE+'<div class="yas"><a href="/kvkk.html">KVKK aydınlatma metni</a><a href="/gizlilik.html">Gizlilik</a><a href="/cerez-politikasi.html">Çerez politikası</a><a href="/kullanim-kosullari.html">Kullanım koşulları</a><a href="/mesafeli-satis-iade.html">Mesafeli satış ve iade</a></div><div class="alt"><span>© 2026 OnlineKaydet</span><span class="kart" aria-label="Kabul edilen kartlar">'
 '<svg viewBox="0 0 64 40" width="52" height="32" role="img" aria-label="Visa"><rect width="64" height="40" rx="6" fill="#fff" stroke="#cfd6df"/><text x="32" y="27" text-anchor="middle" font-family="Arial,sans-serif" font-weight="800" font-style="italic" font-size="19" fill="#1a3a8f">VISA</text></svg>'
 '<svg viewBox="0 0 64 40" width="52" height="32" role="img" aria-label="Mastercard"><rect width="64" height="40" rx="6" fill="#fff" stroke="#cfd6df"/><circle cx="26" cy="20" r="11" fill="#eb001b"/><circle cx="38" cy="20" r="11" fill="#f79e1b"/><path d="M32 11.2a11 11 0 0 1 0 17.6 11 11 0 0 1 0-17.6z" fill="#ff5f00"/></svg></span></div></div></footer>')
SEC={'temalar':'/temalar.html','eticaret':'/e-ticaret.html','editor':'/web-sitesi.html','yonetim':'/is-takibi.html','paketler':'/fiyatlar.html','sektorler':'/sektorler.html'}
NAV=[('Temalar','/temalar.html'),('E-ticaret','/e-ticaret.html'),('Web sitesi','/web-sitesi.html'),('İş takibi','/is-takibi.html'),('Paketler','/fiyatlar.html'),('Sektörler','/sektorler.html'),('Bilgi bankası','/bilgi-bankasi.html')]
def hdr(cur):
    a=lambda t,u,c='':'<a %shref="%s"%s>%s</a>'%(c,u,' aria-current="page"' if u==cur else '',t)
    nav=''.join(a(t,u) for t,u in NAV)
    def _g(ad,L,acik=False):
        return '<details class="mg"%s><summary>%s</summary>%s</details>'%(' open' if acik else '',ad,''.join('<a class="m" href="%s"%s>%s</a>'%(u,' aria-current="page"' if u==cur else '',x) for x,u in L))
    dr=(_g('Ürün',[('Temalar','/temalar.html'),('E-ticaret','/e-ticaret.html'),('Web sitesi','/web-sitesi.html'),('İş takibi','/is-takibi.html'),('Özellikler','/ozellikler.html'),('Muhasebe ve stok','/muhasebe-ve-stok.html')],True)
       +_g('Sektörler',[('Tüm sektörler','/tum-sektorler.html'),('Servis takip programı','/servis-takip-programi.html'),('Randevu programı','/randevu-programi.html'),('Stok ve sipariş programı','/stok-siparis-programi.html')])
       +_g('Öğrenin',[('Bilgi bankası','/bilgi-bankasi.html'),('Blog','/blog.html'),('Entegrasyonlar','/entegrasyonlar.html'),('Hesaplama araçları','/hesaplama-araclari.html'),('Sitede ara','/ara.html')])
       +_g('Fiyat ve destek',[('Paketler','/fiyatlar.html'),('Destek','/destek.html'),('İletişim','/iletisim.html'),('Bayilik','/bayilik.html')]))
    return ('<header class="ust"><div class="w"><a class="logo" href="/"><img src="/logo-acik-s.png" alt="OnlineKaydet" width="160" height="32"></a>'
     '<nav class="nav" aria-label="Ana menü">%s</nav><button class="arab" type="button" data-ara aria-label="Sitede ara"><svg viewBox=\"0 0 24 24\" width=\"20\" height=\"20\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" aria-hidden=\"true\"><circle cx=\"11\" cy=\"11\" r=\"6.5\"/><path d=\"M16 16l4.5 4.5\"/></svg></button><a class="gir" href="/uye-girisi">Üye girişi</a>'
     '<a class="btn bos kc" href="#teklif">Teklif alın</a><a class="btn fil kc" href="/demo.html">Ücretsiz deneyin</a>'
     '<button class="mnu" type="button" aria-label="Menüyü aç" aria-expanded="false" aria-controls="cekmece"><i></i><i></i><i></i></button></div>'
     '<div class="cek" id="cekmece">%s<div class="bt2"><a class="btn fil" href="/demo.html">Ücretsiz deneyin</a><a class="btn bos" href="#teklif">Teklif alın</a><a class="btn bos" href="tel:+905444444004">Hemen arayın</a><a class="btn bos" href="/uye-girisi">Üye girişi</a></div></div></header>')%(nav,dr)
ARAMA_OV=('<div class="arap" id="arap" hidden role="dialog" aria-modal="true" aria-label="Sitede ara"><div class="arak"><form action="/ara.html" role="search" class="araf"><input type="search" name="q" id="arag" placeholder="Ne arıyorsunuz? Örn. ürün ekleme, randevu, Trendyol" autocomplete="off" aria-label="Ara"><button class="btn dolu kc" type="submit">Ara</button><button class="arak2" type="button" data-arakapat aria-label="Kapat">×</button></form><div class="arasik" id="arasik"></div><div class="arasn" id="arasn" aria-live="polite"></div></div></div>')
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
    full=h+extra_head+lj+'\n</head><body>\n<a class="skip" href="#icerik">İçeriğe geç</a>'+hdr(cur)+'\n<main>'+body+'</main>\n'+foot+'\n'+ARAMA_OV+mbar+'<script src="/v9/arama.js" defer></script><script src="/v9/v9.js" defer></script><script src="/v9/v10.js" defer></script>'+('<script src="/v9/dunya.js" defer></script>' if home else '')+'<script src="/lead.js" defer></script><script src="/izle.js" defer></script>'+extra_js+'</body></html>'
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
 B('o','Özellikler','Tek panel, bütün işler','Web sitesi, mağaza ve iş takibi aynı panelde çalışır.',('panel-d-ekip','Ekip ve yetki ekranı'))+'<section class="sec">'+ozel+'</section>'+'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Yeni: muhasebe, stok ve satış araçları</h2><p>Çek-senet takibi, barkodlu hızlı satış, depo ve son kullanma takibi, mali müşavir erişimi, e-ihracat proforma ve açık API. <a href="/muhasebe-ve-stok.html">Hepsini görün</a> · <a href="/hesaplama-araclari.html">Hesaplama araçları</a></p></div></div></section>'+P['dort']+SON)
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
import seo_uret as _seo
def _seo_link(k,ad,d):
    t=_seo.MAN.get(k) or (d[2] if d else 'servis')
    if t not in _seo.PROG: t='servis'
    s=k.replace('_','-')
    L=[('/%s-%s.html'%(s,_seo.URL[t]),'%s %s'%(ad,_seo.PROG[t])),('/%s-muhasebe-programi.html'%s,'%s Muhasebe ve Kasa Programı'%ad),('/%s-web-sitesi.html'%s,'%s Web Sitesi'%ad)]
    return '<section class="sec"><div class="w"><h2>%s için detaylı sayfalar</h2><div class="slst">%s</div></div></section>'%(html.escape(ad),''.join('<a href="%s">%s</a>'%(u,html.escape(x)) for u,x in L))
for k,ad in SEKT:
    if k in SLUG_ONCE: continue
    d=DET.get(k)
    uzun=d[1] if d else ad
    oz=d[6] if d else GEN_OZ
    ish=d[7] if d else []
    kart_=''.join('<div class="fk"><span class="no">%02d</span><h3>%s</h3><p>%s</p></div>'%(i+1,html.escape(a),html.escape(t)) for i,(a,t) in enumerate(oz))
    chips=('<p style="margin-top:22px"><b>Panelde hazır işlem türleri:</b> '+' · '.join(html.escape(x) for x in ish)+'</p>') if ish else ''
    body=B('s-'+k,uzun,'%s için web sitesi ve iş takibi'%uzun,'Sektörünüze hazır tema ve panel: kayıtlar, randevular, kasa ve web siteniz tek yerde.')+'<section class="sec"><div class="w"><div class="fg">'+kart_+'</div>'+chips+'</div></section>'+_seo_link(k,uzun,d)+CTA+SON
    page('sektor-%s.html'%k.replace('_','-'),'%s İçin Web Sitesi ve İş Takip Programı | OnlineKaydet'%uzun,'%s için hazır web sitesi teması, randevu, kasa ve iş takibi. Ücretsiz deneyin.'%uzun,body)
lst=''.join('<a href="%s">%s</a>'%(sektor_url(k),html.escape(a)) for k,a in SEKT)
page('tum-sektorler.html','Tüm Sektörler (%d iş kolu) | OnlineKaydet'%len(SEKT),'OnlineKaydet’in hazır tema ve panel sunduğu %d iş kolunun tam listesi.'%len(SEKT),
 B('ts','Tüm sektörler','%d iş kolu için hazır'%len(SEKT),'Mesleğinizi seçin; temayı, kelimeleri ve ekranları görün.')+'<section class="sec"><div class="w"><div class="slst">'+lst+'</div></div></section>'+'<section class="sec"><div class="w"><h2>Program türüne göre</h2><div class="slst"><a href="/servis-takip-programi.html">Servis takip programı</a><a href="/randevu-programi.html">Randevu programı</a><a href="/kayit-takip-programi.html">Kayıt ve ders takip programı</a><a href="/musteri-takip-programi.html">Müşteri ve iş takip programı</a><a href="/siparis-rezervasyon-programi.html">Sipariş ve rezervasyon programı</a><a href="/rezervasyon-programi.html">Rezervasyon programı</a><a href="/stok-siparis-programi.html">Stok ve sipariş programı</a></div></div></section>'+CTA+SON)
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


SEO_SAYFA=_seo.uret(page,B,SON,CTA,SEKT,DET,sektor_url,SLUG_ONCE,BASE,S)
# ---- altyapı, güvenlik ve özel tasarım sayfaları (yalnız footer bağlantılı)
def kart(l): return ''.join('<div class="fk"><span class="no">%02d</span><h3>%s</h3><p>%s</p></div>'%(i+1,html.escape(a),html.escape(b)) for i,(a,b) in enumerate(l))
def ul(l): return '<ul class="sxl">%s</ul>'%''.join('<li>%s</li>'%html.escape(x) for x in l)
def ssd(q): return ''.join('<details class="sssd"><summary>%s</summary><p>%s</p></details>'%(html.escape(a),html.escape(b)) for a,b in q)
def ldq(q):
    import json as j
    return '<script type="application/ld+json">'+j.dumps({'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':a,'acceptedAnswer':{'@type':'Answer','text':b}} for a,b in q]},ensure_ascii=False)+'</script>'
GNOT='<p class="sxy" style="margin-top:18px">Bu sayfa teknik bir özettir; hukuki taahhüt değildir. Panelin gerçek ayarlarına dayanır. ISO gibi bir sertifika iddiamız yoktur. Soru için <a href="/iletisim.html">bize yazın</a>.</p>'
Q1=[('Panel hangi teknolojiyle çalışıyor?','Sunucu tarafı Python ve FastAPI ile yazıldı, veriler MongoDB’de tutulur. Panel tarayıcıdan açılır, kurulum gerekmez.'),('Tanıtım sitesi nasıl üretiliyor?','Sayfalar önceden üretilen HTML dosyalarıdır; bu yüzden hızlı açılır ve arama motorları kolay tarar.')]
page('altyapi-ve-teknoloji.html','Altyapı ve Teknoloji | OnlineKaydet','OnlineKaydet’in kullandığı yazılım dilleri, veritabanı, entegrasyonlar ve çalışma şekli.',
 B('at','<a href="/hakkimizda.html">Şirket</a> / Teknoloji','Altyapı ve teknoloji','Panelin ve sitenin hangi teknolojiyle çalıştığını açıkça yazıyoruz.')
 +'<section class="sec"><div class="w"><div class="fg">'+kart([('Sunucu yazılımı','Python ve FastAPI ile yazılmış arka uç. İstekler REST arayüzünden geçer.'),('Veritabanı','Kayıtlar MongoDB’de tutulur. Toplu veri ve dosya içe aktarma desteklenir.'),('Arayüz','Panel ve site tarayıcıda çalışır. Telefon, tablet ve bilgisayarda aynı hesapla açılır.'),('Tanıtım sitesi','Önceden üretilen HTML sayfalar. JavaScript yalnızca arama, menü ve formlar için kullanılır.'),('Entegrasyonlar','SMS sağlayıcıları, pazaryerleri, kargo ve ödeme kuruluşları için bağlantı kartları. Hangilerinin hazır olduğu Entegrasyonlar sayfasında.'),('Raporlar ve belgeler','PDF belge, Excel dışa aktarma ve barkod/QR üretimi panelde yerleşiktir.')])+'</div>'+ul(['Dil ve çatı: Python, FastAPI','Veritabanı: MongoDB','Kimlik: bcrypt ile şifre, JWT oturum','Hata izleme: Sentry uyumlu','Bildirim: SMS ve e-posta sağlayıcı bağlantıları'])+GNOT+'</div></section>'
 +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>'+ssd(Q1)+'</div></div></section>'+CTA+SON,ld_raw=ldq(Q1))
Q2=[('Şifreler nasıl saklanıyor?','Şifreler bcrypt ile özetlenerek saklanır; düz metin olarak tutulmaz.'),('Veriler yedekleniyor mu?','Panelde elle ve otomatik yedek alma bulunur; sıkıştırılmış dosya olarak saklanır. Ayrıntı Yedekleme ve denetim kaydı sayfasında.'),('Güvenlik sertifikanız var mı?','Hayır, ISO gibi bir sertifika iddiamız yok. Panelde bulunan koruma özelliklerini yazıyoruz.')]
page('bilgi-ve-veri-guvenligi.html','Bilgi ve Veri Güvenliği | OnlineKaydet','OnlineKaydet’te şifre, oturum, yetki, yedekleme ve kişisel veri güvenliği için uygulanan önlemler.',
 B('bg','<a href="/hakkimizda.html">Şirket</a> / Güvenlik','Bilgi ve veri güvenliği','Hangi önlemlerin panelde gerçekten bulunduğunu sade bir dille anlatıyoruz.')
 +'<section class="sec"><div class="w"><div class="fg">'+kart([('Şifre koruması','Şifreler bcrypt ile özetlenir. Panel şifrenizi düz metin olarak görmez.'),('Oturum','Girişten sonra imzalı oturum anahtarı (JWT) kullanılır.'),('Yetki ve roller','Yönetici rolleri ayrıdır; her rol yalnızca kendi bölümlerine girer.'),('Giriş koruma','Kısa sürede çok sayıda hatalı denemede hesap geçici kilitlenir.'),('İki adımlı doğrulama','Yönetici hesapları için TOTP tabanlı iki adımlı doğrulama açılabilir.'),('Denetim kaydı','Önemli işlemlerin kim tarafından yapıldığı kayıt altında tutulur.'),('Çöp kutusu','Silinen kayıtlar hemen yok olmaz, çöp kutusundan geri alınabilir.'),('Çerez ve KVKK','Çerez onay bandı, ölçüm betiklerini ziyaretçi onayına bağlar. Aydınlatma metni KVKK sayfasında.'.replace('<a>','').replace('</a>',''))])+'</div>'+GNOT+'</div></section>'
 +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>'+ssd(Q2)+'<p><a href="/hesap-guvenligi.html">Hesap güvenliği</a> · <a href="/yedekleme-ve-denetim.html">Yedekleme ve denetim kaydı</a> · <a href="/kvkk.html">KVKK</a></p></div></div></section>'+CTA+SON,ld_raw=ldq(Q2))
Q3=[('Hatalı şifre girersem ne olur?','Kısa sürede art arda hatalı deneme olursa hesap bir süre kilitlenir. Süre ve deneme sayısı panelde tanımlıdır.'),('Başka cihazdan giriş yapılırsa haber verilir mi?','Yeni cihaz ve yeni IP girişleri için güvenlik uyarısı oluşur; gece saatlerinde giriş de uyarı üretir.')]
page('hesap-guvenligi.html','Hesap Güvenliği | OnlineKaydet','Giriş koruma, yeni cihaz uyarısı, kilitleme ve iki adımlı doğrulama.',
 B('hg','<a href="/hakkimizda.html">Şirket</a> / Güvenlik','Hesap güvenliği','Hesabınızı korumak için panelde bulunan önlemler.')
 +'<section class="sec"><div class="w"><div class="fg">'+kart([('Hatalı deneme kilidi','15 dakika içinde 5 hatalı denemeden sonra hesap 15 dakika kilitlenir (varsayılan ayar).'),('Yeni cihaz kontrolü','Teknisyen yeni cihazdan girerken kayıtlı telefon doğrulanır; yönetici isterse yeni cihazı onaya bağlar.'),('Yeni IP ve gece girişi uyarısı','Alışılmadık IP ya da gece girişinde yöneticiye uyarı düşer.'),('İki adımlı doğrulama','Doğrulama uygulamasından 6 haneli kod istenir; yedek kodlar verilir.')])+'</div>'+ul(['Giriş kayıtlarında cihaz ve IP bilgisi görünür','Şifre değişikliği denetim kaydına işlenir'])+GNOT+'</div></section>'
 +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>'+ssd(Q3)+'</div></div></section>'+CTA+SON,ld_raw=ldq(Q3))
Q4=[('Yedekler nerede tutulur?','Yedekler sunucuda sıkıştırılmış dosya olarak saklanır. Geri yükleme yapılırken önce mevcut verinin ayrıca yedeği alınır.'),('Yanlışlıkla sildim, geri gelir mi?','Çöp kutusundaki kayıtlar geri alınabilir.')]
page('yedekleme-ve-denetim.html','Yedekleme ve Denetim Kaydı | OnlineKaydet','Otomatik yedek, çöp kutusu, denetim kaydı ve sistem sağlığı izleme.',
 B('yd','<a href="/hakkimizda.html">Şirket</a> / Güvenlik','Yedekleme ve denetim kaydı','Verinizin korunması ve yapılan işlemlerin izlenmesi.')
 +'<section class="sec"><div class="w"><div class="fg">'+kart([('Elle ve otomatik yedek','Yönetici yedek alabilir; otomatik yedek zamanlayıcı da çalışır.'),('Çöp kutusu','Silinen kayıtlar geri alınabilir şekilde bekler.'),('Denetim kaydı','Kim hangi işlemi yaptı, hangi saatte: kayıt altında tutulur.'),('Sağlık ve hata izleme','Sistem sağlığı ve hatalar izlenir; sorunlar yöneticiye görünür.')])+'</div>'+GNOT+'</div></section>'
 +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>'+ssd(Q4)+'</div></div></section>'+CTA+SON,ld_raw=ldq(Q4))
Q5=[('Özel tasarım ne demek?','Hazır temayı alıp markanıza göre renk, yazı tipi, düzen ve bölümleri değiştirmek ya da sıfırdan sayfa tasarlamak.'),('Tasarımı sonra ben değiştirebilir miyim?','Evet, her bölümün yazısı, yazı tipi ve görseli panelden değiştirilir.'),('Ücret nasıl belirlenir?','Kapsam netleşince ücret yazılı olarak bildirilir; talep bırakmak bağlayıcı değildir.')]
page('ozel-tasarim.html','Özel Tasarım Web Sitesi | OnlineKaydet','Markanıza özel web sitesi tasarımı: önce görsel taslak, onaydan sonra yapım. Her bölüm panelden düzenlenir.',
 B('ot','<a href="/hakkimizda.html">Şirket</a> / Özel tasarım','Markanıza özel tasarım','Hazır tema yetmiyorsa sitenizi işinize ve markanıza göre birlikte tasarlayalım.')
 +'<section class="sec"><div class="w"><h2>Nasıl ilerler?</h2>'+'<ol class="sxs">'+''.join('<li><b>%d</b><span>%s</span><small>%s</small></li>'%(i+1,a,b) for i,(a,b) in enumerate([('Görüşme','İşinizi, hedefinizi ve beğendiğiniz siteleri dinleriz.'),('Taslak görsel','Yapmadan önce tasarımı görsel olarak size göndeririz.'),('Onay','Beğendiğiniz ya da değişmesini istediğiniz yeri yazarsınız.'),('Yapım','Onaylanan tasarım siteye dönüştürülür; bölümler panelden düzenlenir.'),('Yayın','Alan adı ve yayın kurulumu yapılır.')]))+'</ol></div></section>'
 +'<section class="sec"><div class="w"><div class="fg">'+kart([('Marka uyumu','Logo, renk ve yazı tipi markanıza göre belirlenir.'),('Gerçek fotoğraf','Telifli ve gerçek fotoğraflar kullanılır; çizim ya da yapay görsel kullanılmaz.'),('Her bölüm düzenlenebilir','Yazı, yazı tipi ve görseller panelden değişir; her seferinde bize yazmanız gerekmez.'),('Panel ile bağlantı','Formdan gelen talepler müşteri kaydına döner; randevu ve kasa aynı panelde.')])+'</div></div></section>'
 +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>'+ssd(Q5)+'</div></div></section>'+CTA+SON,ld_raw=ldq(Q5))

# ---- muhasebe, stok ve satış özellik sayfaları
import ozellik_sayfalar as _oz
OZ_SAYFA=_oz.uret(page,B,SON,CTA)
# ---- bilgi bankası
import bilgi_icerik as _bi
BK=_bi.A
KAPAK={'xml-ile-urun-aktarma':'bilgi/x_analiz','urun-ekleme':'bilgi/u_liste','pazaryerine-gonderme':'bilgi/pz_sayfa','siparis-ve-kargo':'panel-d-siparis','randevu-ve-takvim':'panel-k-takvim','musteri-yonetimi':'bilgi/m_liste','kasa-ve-muhasebe':'panel-k-kasa','personel-ve-prim':'panel-d-ekip','web-sitesi-duzenleme':'bilgi/w_site'}
kart_b=''.join('<a href="/bilgi-%s.html">%s<span>%s</span><h3>%s</h3><p>%s</p></a>'%(a['slug'],('<div class="bkim"><img src="/v9/img/%s.webp" alt="" loading="lazy"></div>'%KAPAK[a['slug']]) if a['slug'] in KAPAK else '',a['kat'],html.escape(a['ad']),html.escape(a['ozet'])) for a in BK)
page('bilgi-bankasi.html','Bilgi Bankası: Ürün Ekleme, Pazaryeri, Randevu, Kasa, İlan | OnlineKaydet','Panelin adım adım kullanım rehberi: ürün ekleme, pazaryerine gönderme, sipariş, randevu, müşteri, kasa, ekip, ilan ve web sitesi düzenleme.',
 B('b','Bilgi bankası','Paneli adım adım öğrenin','Her işlem için kısa, adım adım rehber. İstediğiniz konuyu seçin.')+'<section class="sec"><div class="w"><form action="/ara.html" role="search" class="araf araf2"><input type="search" name="q" placeholder="Rehberlerde ara: ürün ekleme, Trendyol, randevu…" aria-label="Bilgi bankasında ara"><button class="btn dolu" type="submit">Ara</button></form><div class="bk">'+kart_b+'</div></div></section>'+CTA+SON)
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

# ---- site içi arama
SIK=['Ürün ekleme','Pazaryerine gönderme','Randevu','Kasa','Sipariş','İlan ekleme','Fiyatlar','Demo','Temalar','Entegrasyonlar','KVKK']
page('ara.html','Sitede Ara | OnlineKaydet','OnlineKaydet sitesinde ve bilgi bankasında arama.',
 '<section class="sec" id="icerik"><div class="w"><p class="et">Arama</p><h1 style="font-size:clamp(30px,5vw,54px);margin:6px 0 18px">Sitede ara</h1>'
 '<form action="/ara.html" role="search" class="araf araf2"><input type="search" name="q" id="arasy" placeholder="Ne arıyorsunuz? Örn. ürün ekleme, randevu, Trendyol" autocomplete="off" aria-label="Ara"><button class="btn dolu" type="submit">Ara</button></form>'
 '<div class="arasik" id="arasik2">'+''.join('<a href="/ara.html?q=%s">%s</a>'%(html.escape(x),x) for x in SIK)+'</div><div id="arasonuc" class="arasonuc" aria-live="polite"></div></div></section>',robots='noindex,follow')
import json as _j
DISLA=set(SEO_SAYFA)|{'a-onizleme.html','ana-sayfa-astryx.html','yeni-ana-sayfa.html','temalar-live.html','404.html','ara.html'}
def metin(h):
    m=_re.search(r'<main[^>]*>(.*)</main>',h,_re.S);t=m.group(1) if m else h
    t=_re.sub(r'<(script|style|svg)[^>]*>.*?</\1>','',t,flags=_re.S)
    t=_re.sub(r'<section class="son".*?</section>','',t,flags=_re.S)
    t=_re.sub(r'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Hemen deneyin</h2>.*?</section>','',t,flags=_re.S)
    hs=[_re.sub(r'<[^>]+>','',x).strip() for x in _re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>',t,_re.S)]
    t=_re.sub(r'<[^>]+>',' ',t);t=html.unescape(_re.sub(r'\s+',' ',t)).strip()
    return hs,t
KW={'bilgi-xml-ile-urun-aktarma.html':'xml feed besleme tedarikçi dropshipping toplu ürün aktarma otomatik stok fiyat güncelleme akakçe cimri','bilgi-urun-ekleme.html':'ürün yükle ürün kaydet stok barkod sku kategori excel toplu yükleme','bilgi-pazaryerine-gonderme.html':'trendyol hepsiburada n11 çiçeksepeti amazon pttavm pazarama idefix modanisa temu pazaryeri entegrasyon','bilgi-randevu-ve-takvim.html':'randevu al takvim hatırlatma sms uzman hizmet','bilgi-kasa-ve-muhasebe.html':'kasa gelir gider muhasebe ödeme tahsilat rapor','bilgi-ilan-ekleme.html':'ilan emlak satılık kiralık araç kiralama tur transfer','bilgi-personel-ve-prim.html':'personel çalışan maaş prim avans','bilgi-web-sitesi-duzenleme.html':'web sitesi düzenle tema yazı resim menü alan adı ssl'}
idx=[]
for f in sorted(glob.glob(S+'/*.html')):
    n=os.path.basename(f)
    if n in DISLA: continue
    h=open(f,encoding='utf-8').read()
    if 'noindex' in (_re.search(r'<meta name="robots" content="([^"]*)"',h) or [0,''])[1]: continue
    t=html.unescape((_re.search(r'<title>(.*?)</title>',h,_re.S) or [0,n])[1]).replace(' | OnlineKaydet','')
    d=html.unescape((_re.search(r'<meta name="description" content="([^"]*)"',h) or [0,''])[1])
    hs,tx=metin(h)
    idx.append({'u':'/' if n=='index.html' else '/'+n,'t':t,'d':d,'h':hs[:14],'x':tx[:2600],'k':KW.get(n,'')})
open(H+'/arama.json','w',encoding='utf-8').write(_j.dumps(idx,ensure_ascii=False,separators=(',',':')))
print('arama dizini',len(idx),'sayfa',os.path.getsize(H+'/arama.json')//1024,'KB')

# ---- sitemap: SEO sayfaları
_sm=open(S+'/sitemap.xml',encoding='utf-8').read()
_ek=''.join('<url><loc>%s/%s</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>\n'%(BASE,n) for n in SEO_SAYFA if '/'+n not in _sm)
if _ek: open(S+'/sitemap.xml','w',encoding='utf-8').write(_sm.replace('</urlset>',_ek+'</urlset>'))
print('seo sayfa',len(SEO_SAYFA))
_sm=open(S+'/sitemap.xml',encoding='utf-8').read()
_ek=''.join('<url><loc>%s/%s</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'%(BASE,n) for n in OZ_SAYFA if '/'+n not in _sm)
if _ek: open(S+'/sitemap.xml','w',encoding='utf-8').write(_sm.replace('</urlset>',_ek+'</urlset>'))

_sm=open(S+'/sitemap.xml',encoding='utf-8').read()
_ek=''.join('<url><loc>%s/bilgi-%s.html</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>\n'%(BASE,a['slug']) for a in BK if '/bilgi-%s.html'%a['slug'] not in _sm)
if _ek: open(S+'/sitemap.xml','w',encoding='utf-8').write(_sm.replace('</urlset>',_ek+'</urlset>'))
