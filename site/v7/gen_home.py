import re,sys
sys.path.insert(0,'.')
src=open('../yon7.html').read()
css=re.search(r'<style>(.*)</style>',src,re.S).group(1)
css=re.sub(r'@font-face\{[^}]*\}\n?','',css)
# kabuk tarafından sağlanan parçaları at
css=re.sub(r'/\* header \*/.*?/\* hero \*/','/* hero */',css,flags=re.S)
css=re.sub(r'footer\{[^}]*\}\nfooter \.wrap[^\n]*\n','',css)
css=css.replace('.hd nav,.hd .tel{display:none}','')
css=re.sub(r':root\{[^}]*\}\n\*\{[^}]*\}\nhtml\{[^}]*\}\nbody\{[^}]*\}\na\{[^}]*\}\n:focus-visible\{[^}]*\}\n','',css)
css=css.replace('.wrap{max-width:1240px;margin:0 auto;padding:0 40px}','.wrap{max-width:1240px;margin:0 auto;padding:0 40px}')
css=css.replace('em{font:italic 400 1.08em var(--s);letter-spacing:0}\n','')
css=re.sub(r'\.btn\{[^\n]*\n\.btn:hover[^\n]*\n\.btn\.o[^\n]*\n\.btn\.ink[^\n]*\n\.btn svg[^\n]*\n','',css)
css=css.replace('.js .rv{opacity:0;transform:translateY(22px);transition:opacity .9s var(--ease),transform .9s var(--ease)}\n.js .rv.in{opacity:1;transform:none}\n','')
css=css.replace('.hero h1{font:300 clamp(50px,7.4vw,112px)/1.0 var(--f)','.hero h1{font:300 clamp(42px,6.3vw,96px)/1.02 var(--f)')
open('home.base.css','w').write(css)
body=src[src.index('<main>'):src.index('</main>')+7]
body=body.replace('<h1><span class="l"><span>Servis operasyonunuzun</span></span><span class="l"><span><em>tek</em> merkezi.</span></span></h1>','<h1><span class="l"><span>Teknik servisler için</span></span><span class="l"><span><em>servis takip</em> programı</span></span></h1>')
assert 'Teknik servisler için' in body
# paketler: sadeleştir
a=body.index('<section id="paketler">');b=body.index('<section id="yolharitasi">')
old=body[a:b]
det=old[old.index('<div class="pkt rv"'):]
det=det.replace('</div></section>\n','',1) if det.rstrip().endswith('</section>') else det
det=re.sub(r'</div></section>\s*$','',det.strip())
cards=[('Başlangıç','990','Tek başına çalışan usta ve küçük ekipler için.',['Servis kaydı ve cihaz kataloğu','Usta uygulaması: Atandı, Yolda, Başladı, Bitti','İmzalı PDF servis fişi'],'Servisin çekirdeği.',False),
('Profesyonel','1.990','Müşteri iletişimini ve tahsilatı düzene sokmak isteyenler için.',['Başlangıç’taki her şey','Otomatik SMS ve şablonlar','Kasa, gider ve cari hesap','Raporlar ve memnuniyet anketi'],'',True),
('Tam Paket','3.490','Web sitesi ve online parça satışıyla büyümek isteyenler için.',['Profesyonel’deki her şey','Temalı web sitesi ve SEO','Yedek parça mağazası','Pazarlama araçları'],'',False),
('Kurumsal','5.990','Bakım, garanti ve bayi ağıyla çalışan büyük servisler için.',['Tam Paket’teki her şey','Periyodik bakım ve garanti takibi','Teklif, onay ve ödeme linki','E-arşiv fatura, müşteri portalı'],'',False)]
cd=''
for n,p,t,bl,_,hot in cards:
    cd+='<div class="pc%s">%s<h3>%s</h3><div class="price">%s ₺<small>/ ay + KDV</small></div><p>%s</p><ul>%s</ul><a class="btn %s" href="demo.html">Ücretsiz deneyin</a></div>'%(' hot' if hot else '','<span class="tag">En çok tercih edilen</span>' if hot else '',n,p,t,''.join('<li>%s</li>'%x for x in bl),'' if hot else 'o')
new=('<section id="paketler"><div class="wrap">\n<div class="kick rv">Paketler</div>\n<h2 class="rv">Dört paket, <em>açık</em> fiyat.</h2>\n<p class="lead rv">İlk ay ücretsiz, kart bilgisi istenmez. Fiyatlar aylık, KDV hariçtir. Yıllık ödemede 2 ay hediye.</p>\n'
 '<div class="pcs rv">'+cd+'</div>\n'
 '<details class="pkdet rv"><summary><span>Paket ayrıntıları ve tüm özellikler tablosu</span><i></i></summary><div class="pkin">'+det+'</div></details>\n</div></section>\n\n')
# det kapanışı: eski bölümden gelen son </div> sayısını koru
body=body[:a]+new+body[b:]
# yol haritası bölümünü kaldır (önerilen, doğrulanmamış)
a=body.index('<section id="yolharitasi">');b=body.index('<div class="dk" id="guvenlik">')
body=body[:a]+body[b:]
# yeni bölümler: sektörlerden sonra
extra='''
<section id="usta"><div class="wrap">
<div class="kick rv">Usta uygulaması</div>
<h2 class="rv">Saha ekibiniz telefonundan <em>çalışır.</em></h2>
<div class="two rv"><p class="l">Uygulama mağazası gerekmez. Usta, tarayıcıdan kendi kullanıcı adıyla girer ve yalnızca kendine atanan işleri görür.</p>
<dl class="dl"><div><dt>İş akışı</dt><dd><span>Atandı</span><span>Yolda</span><span>Başladı</span><span>Bitti</span></dd></div><div><dt>Sahada</dt><dd><span>Fotoğraf</span><span>Kontrol listesi</span><span>Parça ve işçilik</span><span>Müşteri imzası</span></dd></div><div><dt>Müşteriye</dt><dd><span>Takip bağlantısı</span><span>İmzalı fiş</span><span>SMS bildirimi</span></dd></div></dl></div>
<a class="lnk rv" href="usta-uygulamasi.html">Usta uygulamasını inceleyin <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 8h12M9 3l5 5-5 5"/></svg></a>
</div></section>

<section id="web"><div class="wrap">
<div class="kick rv">Web sitesi ve entegrasyonlar</div>
<h2 class="rv">Siteniz hazır, <em>sisteminiz</em> bağlı.</h2>
<div class="two rv"><p class="l">30 hazır tema, sekiz sektör. Randevu formu doğrudan servis kaydına düşer.</p>
<dl class="dl"><div><dt>Temalar</dt><dd><span>Kombi</span><span>Klima</span><span>Beyaz eşya</span><span>Elektronik</span><span>Bilgisayar</span><span>Tesisat</span><span>Elektrik</span><span>Güvenlik</span></dd></div><div><dt>Mesajlaşma</dt><dd><span>Netgsm</span><span>Verimor</span><span>İleti Merkezi</span><span>Twilio</span></dd></div><div><dt>Satış ve ödeme</dt><dd><span>Trendyol</span><span>Hepsiburada</span><span>N11</span><span>iyzico</span></dd></div><div><dt>Diğer</dt><dd><span>Google Search Console</span><span>Excel ile içe aktarma</span></dd></div></dl></div>
<div class="lk rv"><a class="lnk" href="temalar.html">Temaları görün <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 8h12M9 3l5 5-5 5"/></svg></a><a class="lnk" href="entegrasyonlar.html">Entegrasyonlar <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 8h12M9 3l5 5-5 5"/></svg></a></div>
</div></section>

<section id="kaynaklar"><div class="wrap">
<div class="kick rv">Kaynaklar</div>
<h2 class="rv">Ücretsiz <em>rehberler</em> ve araçlar.</h2>
<div class="sx rv">
<a href="hata-kodlari.html"><span class="n">01</span><h3>Hata kodları</h3><p>Marka ve model bazında arıza kodları</p><svg viewBox="0 0 22 22" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M3 11h16M12 4l7 7-7 7"/></svg></a>
<a href="komisyon-hesaplama.html"><span class="n">02</span><h3>Komisyon hesaplama</h3><p>Usta ve prim hesabı</p><svg viewBox="0 0 22 22" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M3 11h16M12 4l7 7-7 7"/></svg></a>
<a href="desi-hesaplama.html"><span class="n">03</span><h3>Desi hesaplama</h3><p>Kargo desisi ve ücret</p><svg viewBox="0 0 22 22" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M3 11h16M12 4l7 7-7 7"/></svg></a>
<a href="blog.html"><span class="n">04</span><h3>Blog</h3><p>Servis yönetimi üzerine yazılar</p><svg viewBox="0 0 22 22" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M3 11h16M12 4l7 7-7 7"/></svg></a>
</div></div></section>

<section id="sss"><div class="wrap">
<div class="kick rv">Sık sorulan sorular</div>
<h2 class="rv">Aklınızdakiler.</h2>
<div class="faq rv">
<details><summary>Fiyatlara KDV dahil mi?</summary><p>Hayır, gösterilen fiyatlara KDV eklenir.</p></details>
<details><summary>Deneme süresinde neler var?</summary><p>Seçtiğiniz paketin tüm özellikleri ilk ay açıktır. Kart bilgisi istenmez.</p></details>
<details><summary>Usta sayısı sınırını aşarsam ne olur?</summary><p>Üst pakete geçersiniz ya da ek kullanıcı alırsınız.</p></details>
<details><summary>Yıllık ödemede indirim var mı?</summary><p>Yıllık ödemede 2 ay hediye edilir.</p></details>
<details><summary>Fatura kesiyor musunuz?</summary><p>Evet, her ödeme için e-fatura düzenlenir.</p></details>
</div></div></section>
'''
i=body.index('<section>\n<div class="wrap">\n<div class="kick rv">Geçiş')if '<section>\n<div class="wrap">\n<div class="kick rv">Geçiş' in body else body.index('<section><div class="wrap">\n<div class="kick rv">Geçiş')
body=body[:i]+extra+'\n'+body[i:]
# CTA -> form ile
a=body.index('<div class="cta">');b=body.index('</main>')
cta='''<div class="cta" id="kayit"><div class="wrap cg2">
<div><h2 class="rv">Önce <em>konuşalım.</em></h2><p class="cl rv">Formu doldurun, uzmanımız sektörünüze göre kurulumu birlikte planlasın. İlk ay ücretsiz.</p><a class="tel rv" href="tel:+905444444004">0544 444 40 04</a></div>
<div class="frm rv"><div><label for="f1">Ad soyad</label><input id="f1" autocomplete="name"></div><div><label for="f2">Telefon</label><input id="f2" type="tel" autocomplete="tel" inputmode="tel"></div><div><label for="f3">Firma adı</label><input id="f3" autocomplete="organization"></div><div><label for="f4">Sektör</label><select id="f4"><option>Seçiniz</option><option>Kombi</option><option>Klima</option><option>Beyaz eşya</option><option>Elektronik</option><option>Bilgisayar</option><option>Tesisat</option><option>Elektrik</option><option>Güvenlik</option></select></div><a class="bt" href="#">Beni arayın</a><small>Bilgileriniz yalnızca sizinle iletişim için kullanılır (KVKK).</small></div>
</div></div>
'''
body=body[:a]+cta+body[b:]
import gen7
doc=('<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><meta name="theme-color" content="#0a0c0f">'
'<link rel="icon" href="../favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="../favicon-32.png"><link rel="apple-touch-icon" href="../apple-touch-icon.png">'
'<title>Servis Takip Programı | OnlineKaydet</title><meta name="description" content="Teknik servisler için servis takip programı: servis kaydı, usta takibi, tahsilat ve hazır web sitesi. İlk ay ücretsiz.">'
'<link rel="stylesheet" href="shell.css"><link rel="stylesheet" href="home.css"></head><body>'+gen7.header('index.html',True)+body+gen7.FOOT+gen7.VB+
'<script>document.documentElement.classList.add("js")</script><script src="../site.js"></script><script src="../lead.js"></script><script src="ok7.js"></script><script src="home.js"></script></body></html>')
# gövde içindeki sıfırlama: çift id
open('index.html','w').write(doc)
# home.js
js=src[src.index("var tabs=document"):src.index("</script>\n</body>")]
js=js.replace('})();\n','',1) if False else js
open('home.js','w').write('(function(){\n'+js)
print('ok',len(doc))
