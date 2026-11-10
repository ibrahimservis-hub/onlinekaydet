from ksh import page
FONTS = 'family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,500;1,6..96,400&family=Inter:wght@400;500;600'
CSS = """
:root{--bg:#f6f1e7;--ink:#161412;--mut:#6f675d;--ac:#7a1f2b;--line:#161412;--sbg:#f6f1e7;--sink:#161412;--sac:#7a1f2b;--sline:rgba(22,20,18,.3);--sfont:'Bodoni Moda',serif;--sbody:'Inter',sans-serif;--sr:0}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font:400 16px/1.65 'Inter',sans-serif;overflow-x:hidden}
h1,h2,h3{font-family:'Bodoni Moda',serif;font-weight:400;line-height:1}
a{color:inherit;text-decoration:none}button{font:inherit;color:inherit;cursor:pointer;border:0;background:none}
.pp{background-size:cover;background-position:center;background-color:#d9d0c0}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:52px;padding:0 28px;background:var(--ink);color:var(--bg);font-weight:500;letter-spacing:.08em;text-transform:uppercase;font-size:13px;transition:.3s}.btn:hover{background:var(--ac)}.btn.o{background:transparent;color:var(--ink);border:1.5px solid var(--ink)}.btn.o:hover{background:var(--ink);color:var(--bg)}
.k{font:600 11px 'Inter';letter-spacing:.24em;text-transform:uppercase;color:var(--ac)}
.chip{display:inline-flex;align-items:center;min-height:44px;padding:0 16px;margin:0 6px 6px 0;border:1px solid var(--ink);font-weight:500;font-size:14px;transition:.2s}.chip:hover{background:var(--ink);color:var(--bg)}
/* gazete başlığı */
.dl{display:flex;justify-content:space-between;gap:10px;font:500 11px 'Inter';letter-spacing:.16em;text-transform:uppercase;padding:10px 18px;border-bottom:1px solid var(--line)}
#mast{text-align:center;padding:18px 18px 12px;border-bottom:3px double var(--line)}
#mast .lg{font:400 clamp(44px,13vw,110px)/1 'Bodoni Moda';letter-spacing:-.02em;display:block}#mast .lg i{color:var(--ac)}
#lnk{display:none}
#bar{position:sticky;top:0;z-index:50;display:flex;align-items:center;justify-content:space-between;padding:8px 18px;background:var(--bg);border-bottom:1px solid var(--line)}
#bar a.s{font:italic 400 22px 'Bodoni Moda'}#bar .r{display:flex;gap:8px;align-items:center}#bar .btn{min-height:44px;padding:0 18px}
#bg{min-height:44px;padding:0 14px;border:1px solid var(--ink);font:600 12px 'Inter';letter-spacing:.14em;text-transform:uppercase}
#mn{position:fixed;inset:0;z-index:80;background:var(--bg);padding:80px 22px 30px;overflow:auto;opacity:0;visibility:hidden;transition:.45s}#mn.on{opacity:1;visibility:visible}
#mn a.l{display:flex;gap:14px;align-items:baseline;font:italic 400 clamp(40px,12vw,70px)/1.2 'Bodoni Moda';border-bottom:1px solid var(--line)}#mn a.l small{font:600 11px 'Inter';letter-spacing:.2em;font-style:normal;color:var(--ac)}
#mx{position:absolute;top:12px;right:18px;min-height:44px;padding:0 14px;border:1px solid var(--ink);font:600 12px 'Inter';letter-spacing:.14em;text-transform:uppercase}
#mn .s{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}#mn .s a{border:1px solid var(--ink);min-height:44px;display:flex;align-items:center;padding:0 16px;font-size:13px;letter-spacing:.06em;text-transform:uppercase}
/* hero */
.hero{display:grid;gap:22px;padding:30px 18px 40px;border-bottom:1px solid var(--line)}
.hero h1{font-size:clamp(54px,16vw,150px);letter-spacing:-.03em;margin:14px 0}.hero h1 em{color:var(--ac)}
.hero .im{aspect-ratio:4/5;position:relative;overflow:hidden}.hero .im .pp{position:absolute;inset:0;transform:scale(1.06);animation:z 9s ease-out forwards}@keyframes z{to{transform:none}}
.hero .im figcaption{display:none}
.hero .col{display:grid;gap:14px;align-content:start}.hero .lead{font-size:18px;max-width:440px}
.open{display:inline-flex;align-items:center;gap:8px;font:600 11px 'Inter';letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}.open:before{content:"";width:8px;height:8px;background:#c64b3e}.open.o:before{background:#3f9d5b}
.live{border:1px solid var(--line);padding:14px}.live small{display:block;font-size:13px;color:var(--mut);margin:4px 0 8px}
section{padding:64px 18px;border-bottom:1px solid var(--line)}section h2{font-size:clamp(44px,12vw,100px);letter-spacing:-.025em;margin:10px 0 16px}.lead{color:var(--mut);max-width:520px}
/* içindekiler: servis tablosu */
.tb{margin-top:24px;border-top:3px double var(--line)}.tb .r{display:grid;grid-template-columns:34px 1fr auto;gap:2px 12px;padding:18px 0;border-bottom:1px solid var(--line);align-items:baseline}
.tb .r i{font:italic 400 18px 'Bodoni Moda';color:var(--ac)}.tb .r h3{font-size:clamp(28px,7vw,44px)}.tb .r b{font:500 17px 'Inter'}.tb .r p{grid-column:2;color:var(--mut);font-size:14px}.tb .r button{grid-column:2;justify-self:start;min-height:44px;font:600 11px 'Inter';letter-spacing:.16em;text-transform:uppercase;text-decoration:underline;color:var(--ac);padding:0}
/* lookbook */
.lb2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:22px}.lb2 .gi{display:block;position:relative;overflow:hidden;cursor:zoom-in}.lb2 .gi:nth-child(odd){margin-top:0}.lb2 .gi:nth-child(even){margin-top:34px}.lb2 img{width:100%;display:block;transition:transform 1.2s}.lb2 .gi:hover img{transform:scale(1.04)}
.gf{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;margin-top:16px}.gf button{flex:0 0 auto;min-height:44px;padding:0 18px;border:1px solid var(--ink);font-weight:500;font-size:13px;letter-spacing:.1em;text-transform:uppercase}.gf button.on{background:var(--ink);color:var(--bg)}.lb2 .gi.h{display:none}
/* uzman notu */
.nt{display:grid;gap:14px;margin-top:22px}.nt article{border:1px solid var(--line);padding:22px}.nt article small{font:600 11px 'Inter';letter-spacing:.2em;text-transform:uppercase;color:var(--ac)}.nt h3{font-size:30px;margin:8px 0}.nt p{color:var(--mut)}
.ek{display:grid;gap:22px;margin-top:22px}.ek .m{display:grid;grid-template-columns:110px 1fr;gap:16px;border-top:1px solid var(--line);padding-top:16px}.ek .pp{aspect-ratio:3/4}.ek h3{font-size:32px}.ek small{font:600 11px 'Inter';letter-spacing:.16em;text-transform:uppercase;color:var(--ac)}
.nl{margin-top:20px;display:flex;gap:0;max-width:460px}.nl input{flex:1;min-height:52px;border:1px solid var(--ink);border-right:0;background:transparent;padding:0 14px;font:inherit;min-width:0}.nl button{min-height:52px;padding:0 20px;background:var(--ink);color:var(--bg);font-weight:600;font-size:13px;letter-spacing:.12em;text-transform:uppercase}
.faq details{border-bottom:1px solid var(--line)}.faq summary{list-style:none;cursor:pointer;min-height:64px;display:flex;align-items:center;justify-content:space-between;font:400 24px 'Bodoni Moda'}.faq summary::-webkit-details-marker{display:none}.faq summary:after{content:"+";font-size:26px;color:var(--ac)}.faq details[open] summary:after{content:"–"}.faq p{color:var(--mut);padding-bottom:16px}
footer{background:var(--ink);color:#d8d0c2;padding:56px 18px 40px}.fw{display:grid;gap:26px}footer b.fl{font:italic 400 clamp(46px,12vw,90px)/1 'Bodoni Moda';color:#fff;display:block}footer h5{font:600 11px 'Inter';letter-spacing:.22em;text-transform:uppercase;color:#e0a3ab;margin-bottom:8px}footer a{display:flex;align-items:center;min-height:38px}
.fx{margin-top:30px;padding-top:16px;border-top:1px solid rgba(255,255,255,.2);font-size:12px;letter-spacing:.06em;text-transform:uppercase;display:grid;gap:6px}
#fb{position:fixed;left:12px;right:12px;bottom:calc(env(safe-area-inset-bottom) + 12px);z-index:40}#fb .btn{width:100%;min-height:54px;box-shadow:0 14px 30px -12px rgba(0,0,0,.5)}body{padding-bottom:78px}
@media(min-width:900px){
body{padding-bottom:0}#fb{display:none}#bar{display:none}.dl,#mast{padding-left:48px;padding-right:48px}
#lnk{display:flex;justify-content:center;gap:34px;padding:12px 48px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:50;font:500 12px 'Inter';letter-spacing:.16em;text-transform:uppercase}#lnk a{display:flex;align-items:center;min-height:44px;border-bottom:1px solid transparent}#lnk a:hover{border-color:var(--ac);color:var(--ac)}#lnk .btn{min-height:44px}
.hero{grid-template-columns:1.4fr 1fr;padding:60px 48px;gap:50px;align-items:end}.hero .im{aspect-ratio:3/4}
section{padding:96px 48px;max-width:1300px;margin:auto}.tb .r{grid-template-columns:50px 1.2fr 2fr auto auto;align-items:center}.tb .r p{grid-column:auto}.tb .r button{grid-column:auto}
.lb2{grid-template-columns:repeat(4,1fr)}.nt{grid-template-columns:repeat(3,1fr)}.ek{grid-template-columns:repeat(3,1fr)}.ek .m{grid-template-columns:1fr}.ek .pp{aspect-ratio:4/5}
footer{padding:80px 48px 50px}.fw{grid-template-columns:2fr 1fr 1fr 1fr}.fx{grid-auto-flow:column;justify-content:space-between}
}
"""
BODY = """
<div class="dl"><span>Sayı 11 · Kasım</span><span>Nişantaşı · İstanbul</span></div>
<header id="mast"><a class="lg" href="#">Saç <i>&amp;</i> Kâğıt</a></header>
<nav id="lnk"><a href="#icindekiler">İçindekiler</a><a href="#lookbook">Lookbook</a><a href="#kadro">Kadro</a><a href="#notlar">Notlar</a><a href="#bulten">Bülten</a><a href="#iletisim">İletişim</a><button class="btn" data-open>Randevu al</button></nav>
<div id="bar"><a class="s" href="#">Saç &amp; Kâğıt</a><div class="r"><button class="btn" data-open>Randevu</button><button id="bg">Menü</button></div></div>
<div id="mn"><button id="mx">Kapat</button><a class="l" href="#icindekiler"><small>I</small>İçindekiler</a><a class="l" href="#lookbook"><small>II</small>Lookbook</a><a class="l" href="#kadro"><small>III</small>Kadro</a><a class="l" href="#notlar"><small>IV</small>Notlar</a><a class="l" href="#bulten"><small>V</small>Bülten</a><a class="l" href="#iletisim"><small>VI</small>İletişim</a><div class="s"><a href="#">Instagram</a><a href="#">Pinterest</a><a href="#">WhatsApp</a></div></div>
<header class="hero"><div class="col"><div class="k">Kapak · Kasım sayısı</div><h1>Saç, yazılmış bir <em>hikâye.</em></h1><p class="lead">Nişantaşı'nda randevuyla çalışan küçük bir atölye. Her müşteriye, düzenlenmiş bir sayfa kadar özen.</p>
<div class="live" data-live="3"><div class="open" data-open-now><span></span></div><small data-live-t>Bugün boş saatler</small></div>
<div style="display:flex;gap:10px;flex-wrap:wrap"><button class="btn" data-open>Randevu al</button><a class="btn o" href="#icindekiler">İçindekiler</a></div></div>
<figure class="im"><div class="pp" data-p="3993467" data-w="1600"></div></figure></header>
<section id="icindekiler"><div class="k">Bölüm I</div><h2>İçindekiler.</h2><p class="lead">Süre ve başlangıç fiyatı yanında yazılı; kesin tutar boy ve yoğunluğa göre söylenir.</p>
<div class="tb"><div class="r"><i>01</i><h3>Kesim ve fön</h3><b>450 ₺ · 60 dk</b><p>Saç tipine göre şekil; yıkama, kesim, fön.</p><button data-open data-s="Kesim ve fön">Randevu al</button></div>
<div class="r"><i>02</i><h3>Boya</h3><b>1.800 ₺ · 2 sa</b><p>Renk danışmanlığı ve koruyucu bakım dahil.</p><button data-open data-s="Tek renk boya">Randevu al</button></div>
<div class="r"><i>03</i><h3>Balyaj ve ombre</h3><b>3.200 ₺ · 3 sa</b><p>Kademeli açım, ton verme ve fön.</p><button data-open data-s="Balyaj ve ombre">Randevu al</button></div>
<div class="r"><i>04</i><h3>Keratin bakım</h3><b>1.500 ₺ · 90 dk</b><p>Kalıcı düzleştirme ve yoğun onarım.</p><button data-open data-s="Keratin bakım">Randevu al</button></div>
<div class="r"><i>05</i><h3>Gelin saçı</h3><b>3.500 ₺ · 2–3 sa</b><p>Deneme randevusu ve düğün günü.</p><button data-open data-s="Gelin saçı">Randevu al</button></div>
<div class="r"><i>06</i><h3>Erkek kesim</h3><b>350 ₺ · 30 dk</b><p>Makine veya makas, yıkama dahil.</p><button data-open data-s="Erkek kesim">Randevu al</button></div></div></section>
<section id="lookbook" data-gal><div class="k">Bölüm II</div><h2>Lookbook.</h2><div class="gf"><button class="on" data-f="all">Tümü</button><button data-f="kesim">Kesim</button><button data-f="renk">Renk</button><button data-f="salon">Salon</button></div>
<div class="lb2">""" + ''.join('<a href="#" class="gi" data-p="%s" data-c="%s"><img data-i="%s" data-w="700" alt="Lookbook" loading="lazy"></a>' % (i, c, i) for i, c in [(29096366, 'kesim'), (7195812, 'salon'), (18367697, 'renk'), (8468143, 'salon'), (3993320, 'kesim'), (10028673, 'renk'), (29189945, 'kesim'), (7750144, 'salon')]) + """</div></section>
<section id="kadro"><div class="k">Bölüm III</div><h2>Kadro.</h2><div class="ek">
<div class="m"><div class="pp" data-p="3993462" data-w="500"></div><div><small>Renk</small><h3>Elif</h3><p style="color:var(--mut);margin:4px 0 8px">Boya ve balyajda 9 yıl.</p><div data-slots="3" data-e="Elif" data-s="Tek renk boya"></div></div></div>
<div class="m"><div class="pp" data-p="6599030" data-w="500"></div><div><small>Kesim</small><h3>Murat</h3><p style="color:var(--mut);margin:4px 0 8px">Kadın ve erkek kesim.</p><div data-slots="3" data-e="Murat" data-s="Erkek kesim"></div></div></div>
<div class="m"><div class="pp" data-p="23349912" data-w="500"></div><div><small>Bakım</small><h3>Selin</h3><p style="color:var(--mut);margin:4px 0 8px">Keratin, onarım, gelin.</p><div data-slots="3" data-e="Selin" data-s="Keratin bakım"></div></div></div></div></section>
<section id="notlar"><div class="k">Bölüm IV</div><h2>Atölyeden notlar.</h2><div class="nt">
<article><small>Bakım · 3 dk</small><h3>Boyalı saç nasıl bakılır?</h3><p>İlk 48 saat yıkamayın; renk koruyucu şampuan ve haftada bir maske kullanın.</p></article>
<article><small>Keratin · 2 dk</small><h3>İlk 72 saat</h3><p>Saçı toplamayın, tokayla sıkmayın, yıkamayın; tuzlu su ve havuzdan uzak durun.</p></article>
<article><small>Kesim · 2 dk</small><h3>Ne sıklıkla kesim?</h3><p>Kısa saçta 4–6 hafta, uzun saçta uçlar için 8–10 hafta idealdir.</p></article></div></section>
<section id="bulten"><div class="k">Bölüm V</div><h2>Bültene yazılın.</h2><p class="lead">Ayda bir e-posta: yeni boş saatler, kampanyalar ve bakım notu.</p><div class="nl" id="nl"><input type="email" placeholder="E-posta adresiniz" aria-label="E-posta"><button id="nb">Katıl</button></div><p id="nk" style="display:none;margin-top:12px;color:var(--ac)">Teşekkürler, kaydınız alındı.</p></section>
<section class="faq"><div class="k">Sık sorulanlar</div><h2>Sorular.</h2><details><summary>Randevu iptali?</summary><p>Hatırlatma mesajındaki bağlantıdan ya da arayarak, bir gün öncesine kadar ücretsiz.</p></details><details><summary>Fiyatlar kesin mi?</summary><p>Başlangıç fiyatıdır; kesin tutar işlemden önce söylenir.</p></details><details><summary>Ödeme yöntemleri?</summary><p>Nakit, kart ve havale.</p></details></section>
<footer id="iletisim"><div class="fw"><div><b class="fl">Saç &amp; Kâğıt</b><p style="max-width:320px;margin-top:10px">Nişantaşı'nda randevuyla çalışan küçük bir saç atölyesi.</p></div><div><h5>Adres</h5><a>Abdi İpekçi Cd. 30<br>Nişantaşı / İstanbul</a><a href="tel:02120000000">0212 000 00 00</a></div><div><h5>Saatler</h5><a>Salı–Cumartesi<br>10:00–20:00</a></div><div><h5>Takip</h5><a href="#">Instagram</a><a href="#">Pinterest</a><a href="#">WhatsApp</a></div></div><div class="fx"><span>© 2026 Saç &amp; Kâğıt</span><span>KVKK · Gizlilik · Çerez</span><a href="https://onlinekaydet.com">OnlineKaydet ile yayınlanır</a></div></footer>
<div id="fb"><button class="btn" data-open>Randevu al</button></div>
"""
JS = """(function(){var $=function(s){return document.querySelector(s)};var mn=$('#mn');function m(o){mn.classList.toggle('on',o);document.body.style.overflow=o?'hidden':''}$('#bg').onclick=function(){m(true)};$('#mx').onclick=function(){m(false)};mn.addEventListener('click',function(e){if(e.target.closest('a'))m(false)});OK.esc=function(){m(false)};$('#nb').onclick=function(){$('#nl').style.display='none';$('#nk').style.display='block'}})()"""
def build():
    return page('Saç & Kâğıt · Nişantaşı, İstanbul', '', CSS, BODY, JS, '#f6f1e7', FONTS)
