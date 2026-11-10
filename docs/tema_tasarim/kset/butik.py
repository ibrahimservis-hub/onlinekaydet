from ksh import page
FONTS = 'family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400;1,500&family=DM+Sans:wght@400;500;600'
CSS = """
:root{--bg:#fbf1ee;--ink:#3a2328;--mut:#8a6b70;--ac:#b5476b;--soft:#f4dfe0;--line:rgba(58,35,40,.16);--sbg:#fbf1ee;--sink:#3a2328;--sac:#b5476b;--sline:rgba(58,35,40,.22);--sfont:'Cormorant Garamond',serif;--sbody:'DM Sans',sans-serif;--sr:14px;--side:0px}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font:400 16px/1.65 'DM Sans',sans-serif;overflow-x:hidden;padding-bottom:84px}
h1,h2,h3,h4{font-family:'Cormorant Garamond',serif;font-weight:400;line-height:1.02;letter-spacing:-.01em}
a{color:inherit;text-decoration:none}button{font:inherit;color:inherit;cursor:pointer;border:0;background:none}
.pp{background-size:cover;background-position:center;background-color:#e8cfd0}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:52px;padding:0 28px;border-radius:14px;background:var(--ac);color:#fff;font-weight:600;transition:.3s;box-shadow:0 14px 28px -14px rgba(181,71,107,.7)}
.btn:hover{transform:translateY(-2px)}.btn.o{background:transparent;color:var(--ink);border:1.5px solid var(--line);box-shadow:none}
.eb{font:italic 500 20px 'Cormorant Garamond',serif;color:var(--ac)}
.chip{display:inline-flex;align-items:center;min-height:44px;padding:0 18px;margin:0 6px 6px 0;border-radius:14px;background:#fff;border:1px solid var(--line);font-weight:500;transition:.3s}.chip:hover{background:var(--ink);color:#fff}
/* yan menü / mobil üst çubuk */
#side{display:none}
#top{position:sticky;top:0;z-index:40;display:flex;align-items:center;justify-content:space-between;padding:10px 20px;background:rgba(251,241,238,.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
#top .lg{font:italic 500 26px 'Cormorant Garamond',serif}#top .btn{min-height:44px;padding:0 18px;font-size:14px}
#tab{position:fixed;left:10px;right:10px;bottom:calc(env(safe-area-inset-bottom) + 10px);z-index:50;display:grid;grid-template-columns:repeat(5,1fr);background:#fff;border-radius:22px;border:1px solid var(--line);box-shadow:0 18px 40px -18px rgba(58,35,40,.5);padding:6px}
#tab a{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;min-height:56px;border-radius:16px;font-size:11px;font-weight:600;color:var(--mut)}
#tab a.on{background:var(--soft);color:var(--ac)}#tab svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
main{max-width:1080px;margin:auto}
section{padding:70px 22px}
section h2{font-size:clamp(40px,11vw,68px);margin:6px 0 12px}.lead{color:var(--mut);max-width:480px}
/* hero */
.hero{padding:30px 22px 40px;display:grid;gap:28px}
.hero h1{font-size:clamp(50px,15vw,100px);margin:10px 0 16px}.hero h1 em{color:var(--ac)}
.arch{position:relative;border-radius:999px 999px 24px 24px;overflow:hidden;aspect-ratio:3/4;max-width:420px;width:100%;margin:0 auto;box-shadow:0 40px 60px -30px rgba(58,35,40,.55)}
.arch .pp{position:absolute;inset:0;transform:scale(1.08);animation:z 9s ease-out forwards}@keyframes z{to{transform:none}}
.ring{position:absolute;right:-6px;top:-6px;width:96px;height:96px;border:1.5px dashed var(--ac);border-radius:50%;animation:sp 28s linear infinite;opacity:.55}@keyframes sp{to{transform:rotate(360deg)}}
.livebox{margin-top:22px;background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px}
.livebox small{display:block;font-size:13px;color:var(--mut);margin-bottom:8px}
.open{display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--mut);margin-bottom:10px}.open:before{content:"";width:8px;height:8px;border-radius:50%;background:#e0786a}.open.o:before{background:#4cae6a}
/* menü kartı (fiyat) */
.menu{background:#fff;border-radius:28px;padding:26px 22px;border:1px solid var(--line);margin-top:26px}
.menu h3{font:italic 500 30px 'Cormorant Garamond',serif;color:var(--ac);margin:20px 0 6px}.menu h3:first-child{margin-top:0}
.mi{display:flex;align-items:baseline;gap:8px;padding:9px 0;min-height:44px}
.mi b{font-weight:500}.mi i{flex:1;border-bottom:1.5px dotted rgba(58,35,40,.3);transform:translateY(-4px)}.mi span{font-weight:600;color:var(--ac);white-space:nowrap}
.mi button{font-size:13px;font-weight:600;color:var(--ac);min-height:44px;padding:0 6px;text-decoration:underline}
.mi small{display:block;color:var(--mut);font-size:13px;font-weight:400}
/* galeri masonry */
.gf{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;margin:20px 0}.gf button{flex:0 0 auto;min-height:44px;padding:0 20px;border-radius:99px;border:1px solid var(--line);background:#fff;font-weight:500}.gf button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.gg{columns:2;column-gap:10px}.gg .gi{display:block;break-inside:avoid;margin-bottom:10px;border-radius:20px;overflow:hidden;cursor:zoom-in}.gg .gi.h{display:none}.gg img{width:100%;display:block;transition:transform 1.2s}.gg .gi:hover img{transform:scale(1.05)}
/* ekip */
.tm{display:flex;gap:14px;overflow-x:auto;scroll-snap-type:x mandatory;margin:24px -22px 0;padding:4px 22px 18px;scrollbar-width:none}.tm::-webkit-scrollbar{display:none}
.mem{flex:0 0 76%;max-width:300px;scroll-snap-align:center;background:#fff;border-radius:28px 28px 20px 20px;overflow:hidden;border:1px solid var(--line)}
.mem .pp{height:300px;border-radius:999px 999px 0 0;margin:10px 10px 0}.mem .bd{padding:16px 18px 20px}.mem h3{font-size:30px}.mem small{color:var(--mut)}
/* paketler */
.pk{display:grid;gap:14px;margin-top:24px}.pc{background:#fff;border-radius:26px;padding:26px;border:1px solid var(--line)}.pc.f{background:var(--ink);color:#fff}
.pc h3{font-size:32px}.pc .pr{font:italic 400 44px 'Cormorant Garamond',serif;color:var(--ac);margin:8px 0}.pc.f .pr{color:#f2b6c6}.pc ul{list-style:none;display:grid;gap:8px;margin:12px 0 20px;font-size:15px}.pc li:before{content:"✿ ";color:var(--ac)}
.words{display:grid;gap:12px;margin-top:22px}.words div{background:var(--soft);border-radius:22px;padding:22px}.words h3{font-size:28px;margin-bottom:6px}
.ig{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:20px}.ig .pp{aspect-ratio:1;border-radius:16px}
.ct{display:grid;gap:12px;margin-top:20px}.ct div{background:#fff;border:1px solid var(--line);border-radius:22px;padding:22px}.ct h3{font-size:26px;margin-bottom:6px}
footer{background:var(--ink);color:#e5d3d3;padding:56px 22px 110px;margin-top:20px}
.fw{max-width:1080px;margin:auto;display:grid;gap:28px}footer b.fl{font:italic 500 34px 'Cormorant Garamond',serif;color:#fff;display:block}
footer h5{font:600 12px 'DM Sans';letter-spacing:.16em;text-transform:uppercase;color:#f2b6c6;margin-bottom:8px}footer a{display:flex;align-items:center;min-height:36px}
.soc{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.soc a{border:1px solid rgba(255,255,255,.3);border-radius:12px;padding:0 16px;min-height:44px}
.fx{max-width:1080px;margin:36px auto 0;padding-top:18px;border-top:1px solid rgba(255,255,255,.15);font-size:13px;display:grid;gap:6px}
@media(min-width:900px){
body{padding-bottom:0;padding-left:270px}
#top,#tab{display:none}
#side{display:flex;flex-direction:column;position:fixed;left:0;top:0;bottom:0;width:270px;padding:36px 28px;border-right:1px solid var(--line);background:var(--bg);z-index:40}
#side .lg{font:italic 500 36px 'Cormorant Garamond',serif;margin-bottom:28px}
#side nav{display:flex;flex-direction:column;gap:2px;flex:1}#side nav a{display:flex;align-items:center;min-height:44px;font-size:16px;color:var(--mut);border-left:2px solid transparent;padding-left:14px;transition:.3s}#side nav a:hover,#side nav a.on{color:var(--ink);border-color:var(--ac)}
#side .btn{width:100%}#side .soc a{border-color:var(--line);min-height:44px}
.hero{grid-template-columns:1.1fr .9fr;align-items:center;padding:70px 40px}section{padding:90px 40px}
.menu{display:grid;grid-template-columns:1fr 1fr;gap:0 50px}.menu h3{grid-column:span 1}
.gg{columns:3}.tm{margin:24px 0 0;padding:4px 0 18px;overflow:visible;display:grid;grid-template-columns:repeat(3,1fr)}.mem{max-width:none}
.pk{grid-template-columns:repeat(3,1fr)}.words{grid-template-columns:repeat(3,1fr)}.ig{grid-template-columns:repeat(6,1fr)}.ct{grid-template-columns:repeat(3,1fr)}
.fw{grid-template-columns:1.4fr 1fr 1fr}footer{padding-bottom:40px}.fx{grid-auto-flow:column;justify-content:space-between}
}
"""
SOC = '<a href="#">Instagram</a><a href="#">WhatsApp</a><a href="#">Facebook</a><a href="#">TikTok</a>'
IC = lambda p: '<svg viewBox="0 0 24 24">%s</svg>' % p
BODY = """
<aside id="side"><a class="lg" href="#ana">Butik Saç</a><nav id="sn"><a href="#ana" class="on">Ana sayfa</a><a href="#hizmet">Hizmetler</a><a href="#galeri">Galeri</a><a href="#ekip">Ekip</a><a href="#paket">Paketler</a><a href="#iletisim">İletişim</a></nav>
<div class="open" data-open-now><span></span></div><button class="btn" data-open>Randevu al</button><div class="soc" style="margin-top:14px">""" + SOC + """</div></aside>
<header id="top"><a class="lg" href="#ana">Butik Saç</a><button class="btn" data-open>Randevu al</button></header>
<main>
<section class="hero" id="ana"><div><div class="eb">Moda · Kadıköy, İstanbul</div><h1>Saçınıza bir <em>butik</em> dokunuş.</h1><p class="lead">Küçük, randevulu ve sakin bir salon. Kesim, renk ve bakım; her biri size ayrılmış zamanla.</p>
<div class="livebox" data-live="3"><div class="open" data-open-now><span></span></div><small data-live-t>Bugün boş saatler</small></div></div>
<div class="arch rv"><div class="pp" data-p="29096366"></div><i class="ring"></i></div></section>
<section id="hizmet"><div class="eb rv">Hizmetler</div><h2 class="rv">Menü kartı.</h2><p class="lead rv">Fiyatlar başlangıçtır; boy ve yoğunluğa göre kesin tutar randevuda söylenir.</p>
<div class="menu rv"><div><h3>Kesim</h3><div class="mi"><div><b>Kesim ve fön</b><small>45–60 dk</small></div><i></i><span>450 ₺</span><button data-open data-s="Kesim ve fön">Seç</button></div><div class="mi"><div><b>Ucu alma</b><small>30 dk</small></div><i></i><span>300 ₺</span><button data-open data-s="Kesim ve fön">Seç</button></div><div class="mi"><div><b>Erkek kesim</b><small>30 dk</small></div><i></i><span>350 ₺</span><button data-open data-s="Erkek kesim">Seç</button></div>
<h3>Renk</h3><div class="mi"><div><b>Tek renk boya</b><small>2 saat</small></div><i></i><span>1.800 ₺</span><button data-open data-s="Tek renk boya">Seç</button></div><div class="mi"><div><b>Balyaj ve ombre</b><small>3 saat</small></div><i></i><span>3.200 ₺</span><button data-open data-s="Balyaj ve ombre">Seç</button></div></div>
<div><h3>Bakım</h3><div class="mi"><div><b>Keratin bakım</b><small>90 dk</small></div><i></i><span>1.500 ₺</span><button data-open data-s="Keratin bakım">Seç</button></div><div class="mi"><div><b>Onarıcı maske</b><small>30 dk</small></div><i></i><span>400 ₺</span><button data-open data-s="Keratin bakım">Seç</button></div>
<h3>Gelin</h3><div class="mi"><div><b>Deneme randevusu</b><small>90 dk</small></div><i></i><span>1.200 ₺</span><button data-open data-s="Gelin saçı">Seç</button></div><div class="mi"><div><b>Düğün günü saç</b><small>2–3 saat</small></div><i></i><span>3.500 ₺</span><button data-open data-s="Gelin saçı">Seç</button></div></div></div></section>
<section id="galeri" data-gal><div class="eb rv">Galeri</div><h2 class="rv">Koltuktan kareler.</h2>
<div class="gf"><button class="on" data-f="all">Tümü</button><button data-f="kesim">Kesim</button><button data-f="renk">Renk</button><button data-f="salon">Salon</button></div>
<div class="gg">""" + ''.join('<a href="#" class="gi" data-p="%s" data-c="%s"><img data-i="%s" data-w="700" alt="Butik Saç galeri" loading="lazy"></a>' % (i, c, i) for i, c in [(3993320, 'kesim'), (8468143, 'salon'), (18367697, 'renk'), (7750144, 'salon'), (29189945, 'kesim'), (10028673, 'renk'), (3993467, 'kesim'), (7195812, 'salon'), (20092122, 'renk')]) + """</div></section>
<section id="ekip"><div class="eb rv">Ekip</div><h2 class="rv">Üç uzman, üç alan.</h2>
<div class="tm"><div class="mem"><div class="pp" data-p="3993462"></div><div class="bd"><h3>Elif</h3><small>Renk uzmanı</small><div style="margin-top:10px" data-slots="3" data-e="Elif" data-s="Tek renk boya"></div></div></div>
<div class="mem"><div class="pp" data-p="6599030"></div><div class="bd"><h3>Murat</h3><small>Kesim uzmanı</small><div style="margin-top:10px" data-slots="3" data-e="Murat" data-s="Erkek kesim"></div></div></div>
<div class="mem"><div class="pp" data-p="23349912"></div><div class="bd"><h3>Selin</h3><small>Bakım ve gelin</small><div style="margin-top:10px" data-slots="3" data-e="Selin" data-s="Keratin bakım"></div></div></div></div></section>
<section id="paket"><div class="eb rv">Paketler</div><h2 class="rv">Düzenli gelenlere.</h2>
<div class="pk"><div class="pc"><h3>5 kesim</h3><div class="pr">2.000 ₺</div><ul><li>5 kesim ve fön</li><li>Bakım maskesi hediye</li></ul><button class="btn" data-open data-s="Kesim ve fön">Paketi al</button></div><div class="pc f"><h3>Aylık bakım</h3><div class="pr">1.600 ₺</div><ul><li>Ayda bir bakım ve fön</li><li>Öncelikli randevu</li></ul><button class="btn" data-open data-s="Keratin bakım">Üye ol</button></div><div class="pc"><h3>Gelin paketi</h3><div class="pr">7.500 ₺</div><ul><li>Deneme + düğün günü</li><li>Yakınlarınıza 2 fön</li></ul><button class="btn" data-open data-s="Gelin saçı">Randevu al</button></div></div>
<h2 style="margin-top:56px" class="rv">Salon sözleri.</h2><div class="words"><div><h3>Acele yok</h3><p>Her randevuya süre ayrılır; önce dinleriz.</p></div><div><h3>Önce konuşma</h3><p>Rengi ve boyu birlikte seçeriz.</p></div><div><h3>Yazılı bakım notu</h3><p>Evde nasıl bakacağınız elinize verilir.</p></div></div>
<div class="eb rv" style="margin-top:56px">Instagram · @butiksac</div><div class="ig">""" + ''.join('<div class="pp" data-p="%s" data-w="400"></div>' % i for i in (20092122, 8468134, 29189945, 3356174, 15659494, 7879790)) + """</div></section>
<section id="iletisim"><div class="eb rv">İletişim</div><h2 class="rv">Bize uğrayın.</h2>
<div class="ct"><div><h3>Adres</h3><p>Moda Cd. 12, Kadıköy / İstanbul</p><p style="margin-top:6px"><a href="tel:02160000000"><b>0216 000 00 00</b></a></p></div><div><h3>Saatler</h3><p>Salı–Cumartesi 10:00–20:00<br>Pazar–Pazartesi kapalı</p></div><div><h3>Yazın</h3><button class="btn" data-open>Randevu al</button></div></div></section>
</main>
<nav id="tab"><a href="#ana" class="on">""" + IC('<path d="M4 11l8-7 8 7v9H4z"/>') + """Ana</a><a href="#hizmet">""" + IC('<path d="M6 3v18M6 3c3 0 5 2 5 5M18 3v8c0 2-1 3-3 3h0v7"/>') + """Menü</a><a href="#galeri">""" + IC('<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="2"/><path d="M4 18l6-5 4 3 3-2 4 4"/>') + """Galeri</a><a href="#ekip">""" + IC('<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3 3-5 6-5s6 2 6 5M16 5a3 3 0 0 1 0 6M18 15c2 0 3 2 3 4"/>') + """Ekip</a><a href="tel:02160000000">""" + IC('<path d="M5 4h4l2 5-2 1c1 2 3 4 5 5l1-2 5 2v4c0 1-1 2-2 2C10 21 3 14 3 6c0-1 1-2 2-2z"/>') + """Ara</a></nav>
<footer><div class="fw"><div><b class="fl">Butik Saç</b><p style="max-width:300px">Küçük, randevulu, sakin bir salon.</p><div class="soc">""" + SOC + """</div></div><div><h5>Sayfalar</h5><a href="#hizmet">Hizmetler</a><a href="#galeri">Galeri</a><a href="#ekip">Ekip</a><a href="#paket">Paketler</a></div><div><h5>Adres</h5><a>Moda Cd. 12, Kadıköy</a><a href="tel:02160000000">0216 000 00 00</a><a>Salı–Cumartesi 10:00–20:00</a></div></div><div class="fx"><span>© 2026 Butik Saç</span><span>KVKK · Gizlilik · Çerez</span><a href="https://onlinekaydet.com">OnlineKaydet ile yayınlanır</a></div></footer>
"""
JS = """(function(){var L=[].slice.call(document.querySelectorAll('#sn a,#tab a[href^="#"]')),S=['ana','hizmet','galeri','ekip','paket','iletisim'];
function on(){var y=scrollY+200,c='ana';S.forEach(function(s){var e=document.getElementById(s);if(e&&e.offsetTop<=y)c=s});L.forEach(function(a){a.classList.toggle('on',a.getAttribute('href')==='#'+c)})}addEventListener('scroll',on,{passive:true});on()})()"""
def build():
    return page('Butik Saç · Kadıköy, İstanbul', '', CSS, BODY, JS, '#fbf1ee', FONTS)
