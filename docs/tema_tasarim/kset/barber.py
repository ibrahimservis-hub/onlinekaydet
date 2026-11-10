from ksh import page
FONTS = 'family=Anton&family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600'
CSS = """
:root{--bg:#0c0c0c;--ink:#f5f5f0;--mut:#9a9a92;--ac:#ffd60a;--line:rgba(255,255,255,.16);--sbg:#151515;--sink:#f5f5f0;--sac:#ffd60a;--sline:rgba(255,255,255,.22);--sfont:'Anton',sans-serif;--sbody:'Barlow',sans-serif;--sr:4px;--shw:400}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font:400 17px/1.55 'Barlow',sans-serif;overflow-x:hidden;padding-bottom:78px}
h1,h2,h3{font-family:'Anton',sans-serif;font-weight:400;text-transform:uppercase;letter-spacing:.01em;line-height:.95}
a{color:inherit;text-decoration:none}button{font:inherit;color:inherit;cursor:pointer;border:0;background:none}
.pp{background-size:cover;background-position:center;background-color:#222}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:54px;padding:0 30px;background:var(--ac);color:#0c0c0c;font:700 18px 'Barlow Condensed',sans-serif;letter-spacing:.08em;text-transform:uppercase;transition:.25s}.btn:hover{background:#fff}.btn.o{background:transparent;color:var(--ink);border:2px solid var(--ink)}.btn.o:hover{background:var(--ink);color:#0c0c0c}
.lab{font:600 15px 'Barlow Condensed',sans-serif;letter-spacing:.2em;text-transform:uppercase;color:var(--ac)}
.chip{display:inline-flex;align-items:center;min-height:44px;padding:0 18px;margin:0 6px 6px 0;border:2px solid var(--ink);font:700 17px 'Barlow Condensed',sans-serif;letter-spacing:.06em;transition:.2s}.chip:hover{background:var(--ac);color:#0c0c0c;border-color:var(--ac)}
#bar{position:sticky;top:0;z-index:60;display:flex;align-items:center;justify-content:space-between;padding:10px 18px;background:rgba(12,12,12,.92);backdrop-filter:blur(10px);border-bottom:2px solid var(--ac)}
#bar .lg{font:400 28px 'Anton';letter-spacing:.04em}#bar .lg b{color:var(--ac)}
#bg{min-height:44px;padding:0 14px;border:2px solid var(--ink);font:700 16px 'Barlow Condensed';letter-spacing:.1em;text-transform:uppercase}
#mn{position:fixed;inset:0;z-index:80;background:var(--ac);color:#0c0c0c;padding:80px 22px 30px;overflow:auto;transform:translateY(-100%);transition:transform .6s cubic-bezier(.7,0,.2,1)}#mn.on{transform:none}
#mn a.big{display:flex;align-items:baseline;gap:14px;font:400 clamp(44px,13vw,86px)/1.04 'Anton';text-transform:uppercase;border-bottom:2px solid #0c0c0c;padding:6px 0}#mn a.big small{font:600 16px 'Barlow Condensed';letter-spacing:.1em}
#mx{position:absolute;top:12px;right:18px;min-height:44px;padding:0 14px;border:2px solid #0c0c0c;font:700 16px 'Barlow Condensed';letter-spacing:.1em;text-transform:uppercase}
#mn .s{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}#mn .s a{border:2px solid #0c0c0c;min-height:44px;display:flex;align-items:center;padding:0 16px;font:700 16px 'Barlow Condensed';letter-spacing:.08em;text-transform:uppercase}
/* hero */
.hero{display:grid;border-bottom:2px solid var(--ac)}
.hero .tx{padding:34px 18px 26px}.hero h1{font-size:clamp(66px,22vw,190px);margin:14px 0 18px}.hero h1 span{display:block}.hero h1 .y{color:var(--ac)}.hero h1 .wl{display:block;height:.95em;position:relative;overflow:hidden}.hero h1 .w{position:absolute;left:0;top:100%;color:var(--ac);transition:top .6s cubic-bezier(.7,0,.2,1)}.hero h1 .w.on{top:0}.hero h1 .w.out{top:-100%}
.hero .ph{min-height:56vw;position:relative;filter:grayscale(1) contrast(1.1);background-position:center 25%}.hero .ph:after{content:"";position:absolute;inset:0;background:var(--ac);mix-blend-mode:multiply;opacity:.55}
.queue{margin-top:18px;border:2px solid var(--line);padding:14px 16px;display:flex;align-items:center;justify-content:space-between;gap:12px}.queue b{font:400 40px 'Anton';color:var(--ac);line-height:1}.queue small{font:600 14px 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase;color:var(--mut);display:block}
.open{display:inline-flex;align-items:center;gap:8px;font:600 15px 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}.open:before{content:"";width:9px;height:9px;background:#e0584a}.open.o:before{background:#5bd37a}
.mq{overflow:hidden;background:var(--ac);color:#0c0c0c;padding:10px 0}.mq div{display:flex;gap:30px;width:max-content;animation:mq 30s linear infinite;font:400 28px 'Anton';text-transform:uppercase}@keyframes mq{to{transform:translateX(-50%)}}
section{padding:64px 18px}section h2{font-size:clamp(52px,16vw,120px);margin:10px 0 18px}
/* servis akordeon */
.ac{border-top:2px solid var(--line);margin-top:20px}.ac details{border-bottom:2px solid var(--line)}
.ac summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:42px 1fr auto;gap:10px;align-items:center;min-height:72px}.ac summary::-webkit-details-marker{display:none}
.ac summary i{font:600 18px 'Barlow Condensed';color:var(--ac);font-style:normal}.ac summary b{font:400 clamp(26px,7vw,44px) 'Anton';text-transform:uppercase}.ac summary span{font:700 22px 'Barlow Condensed';color:var(--ac)}
.ac details[open] summary b{color:var(--ac)}.ac .bd{padding:0 0 22px 52px;display:grid;gap:12px;color:var(--mut);animation:fi .5s}@keyframes fi{from{opacity:0}to{opacity:1}}
/* stil seçici */
.pick{display:grid;gap:16px;margin-top:22px}.pick .ph{min-height:340px;position:relative;filter:grayscale(.2)}
.pick .tb{display:flex;gap:8px;flex-wrap:wrap}.pick .tb button{min-height:48px;padding:0 20px;border:2px solid var(--line);font:700 18px 'Barlow Condensed';letter-spacing:.08em;text-transform:uppercase}.pick .tb button.on{background:var(--ac);color:#0c0c0c;border-color:var(--ac)}
.pick .res{border:2px solid var(--line);padding:18px}.pick .res h3{font-size:44px;color:var(--ac)}.pick .res p{color:var(--mut);margin:8px 0 14px}.pick .st{display:flex;gap:22px;margin-bottom:14px;font:700 20px 'Barlow Condensed'}.pick .st small{display:block;font:500 13px 'Barlow Condensed';letter-spacing:.14em;color:var(--mut);text-transform:uppercase}
/* film şeridi */
.fs{display:flex;gap:10px;overflow-x:auto;scroll-snap-type:x mandatory;margin:20px -18px 0;padding:0 18px 14px;scrollbar-width:none}.fs::-webkit-scrollbar{display:none}
.fs .gi{flex:0 0 72%;max-width:340px;aspect-ratio:3/4;scroll-snap-align:center;position:relative;overflow:hidden;cursor:zoom-in;border:2px solid var(--line)}.fs .gi img{width:100%;height:100%;object-fit:cover;filter:grayscale(1);transition:filter .5s,transform 1.2s}.fs .gi:hover img{filter:none;transform:scale(1.05)}
/* kadro */
.ro{margin-top:20px;border-top:2px solid var(--line)}.ro .r{display:grid;gap:10px;padding:20px 0;border-bottom:2px solid var(--line)}.ro h3{font-size:clamp(48px,13vw,90px)}.ro small{font:600 15px 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase;color:var(--ac)}
.faq details{border-bottom:2px solid var(--line)}.faq summary{list-style:none;cursor:pointer;min-height:64px;display:flex;align-items:center;justify-content:space-between;font:600 22px 'Barlow Condensed';letter-spacing:.04em;text-transform:uppercase}.faq summary::-webkit-details-marker{display:none}.faq summary:after{content:"+";color:var(--ac);font-size:30px}.faq details[open] summary:after{content:"–"}.faq p{color:var(--mut);padding-bottom:16px}
footer{background:var(--ac);color:#0c0c0c;padding:50px 18px 100px}
footer .big{font:400 clamp(72px,26vw,300px)/.85 'Anton';text-transform:uppercase;margin-bottom:26px}
.fw{display:grid;gap:22px;font:600 17px 'Barlow Condensed';letter-spacing:.05em;text-transform:uppercase}footer h5{font:700 14px 'Barlow Condensed';letter-spacing:.2em;opacity:.7;margin-bottom:6px}footer a{display:flex;align-items:center;min-height:40px}
.fx{margin-top:26px;padding-top:14px;border-top:2px solid #0c0c0c;font:600 14px 'Barlow Condensed';letter-spacing:.08em;text-transform:uppercase;display:grid;gap:6px}
#dock{position:fixed;left:0;right:0;bottom:0;z-index:50;display:grid;grid-template-columns:auto 1fr;background:#0c0c0c;border-top:2px solid var(--ac);padding-bottom:env(safe-area-inset-bottom)}
#dock a{display:grid;place-items:center;min-height:62px;padding:0 24px;font:700 18px 'Barlow Condensed';letter-spacing:.1em;text-transform:uppercase}#dock .btn{min-height:62px;width:100%;font-size:22px}
@media(min-width:900px){
body{padding-bottom:0}#dock{display:none}
#bar{padding:12px 48px}#bar .lg{font-size:34px}.hero{grid-template-columns:1.1fr .9fr;min-height:calc(100svh - 64px)}.hero .tx{padding:60px 48px;align-self:center}.hero .ph{min-height:100%}
section{padding:100px 48px;max-width:1300px;margin:auto}.pick{grid-template-columns:1fr 1fr;align-items:stretch}.fs{margin:20px 0 0;padding:0 0 14px}.fs .gi{flex-basis:300px}
.ro .r{grid-template-columns:1.2fr 1fr auto;align-items:center}footer{padding:70px 48px 50px}.fw{grid-template-columns:repeat(4,1fr)}.fx{grid-auto-flow:column;justify-content:space-between}
}
"""
BODY = """
<header id="bar"><a class="lg" href="#">KESİM<b>.</b>HANE</a><div style="display:flex;gap:8px"><button class="btn" data-open style="min-height:44px;padding:0 16px;font-size:16px">Randevu</button><button id="bg">Menü</button></div></header>
<div id="mn"><button id="mx">Kapat</button><a class="big" href="#hizmet"><small>01</small>Hizmetler</a><a class="big" href="#stil"><small>02</small>Stilini seç</a><a class="big" href="#galeri"><small>03</small>Galeri</a><a class="big" href="#kadro"><small>04</small>Kadro</a><a class="big" href="#sss"><small>05</small>SSS</a><a class="big" href="#iletisim"><small>06</small>İletişim</a>
<div class="s"><a href="#">Instagram</a><a href="#">WhatsApp</a><a href="#">TikTok</a><a href="#">Google Haritalar</a></div></div>
<header class="hero"><div class="tx"><div class="lab">Beşiktaş · İstanbul · Barber ve saç</div><h1><span>Kes.</span><span class="y">Düzelt.</span><span class="wl"><i class="w on">Çık.</i><i class="w">Parla.</i><i class="w">Güven.</i></span></h1>
<div data-live="3"><div class="open" data-open-now style="margin-bottom:10px"><span></span></div><small data-live-t class="lab" style="display:block;margin-bottom:8px;color:var(--mut)">Bugün boş saatler</small></div>
<div class="queue"><div><small>Şu an koltukta · örnek</small><b id="qn">2</b> <span style="font:700 18px 'Barlow Condensed'">kişi bekliyor</span></div><div style="text-align:right"><small>Tahmini bekleme</small><b id="qm">25</b> <span style="font:700 18px 'Barlow Condensed'">dk</span></div></div>
<div style="display:flex;gap:10px;margin-top:20px;flex-wrap:wrap"><button class="btn" data-open>Randevu al</button><a class="btn o" href="#hizmet">Fiyatlar</a></div></div>
<div class="ph pp" data-p="19664876" data-w="1600"></div></header>
<div class="mq"><div>""" + 'FADE ✦ MAKAS ✦ USTURA ✦ SAKAL ✦ KLASİK ✦ ' * 6 + """</div></div>
<section id="hizmet"><div class="lab">Hizmetler</div><h2>Fiyat listesi.</h2><div class="ac">
<details open><summary><i>01</i><b>Saç kesimi</b><span>350 ₺</span></summary><div class="bd"><p>Makine veya makas, yıkama ve şekil. Yaklaşık 30 dk.</p><div><button class="btn sm" data-open data-s="Erkek kesim">Randevu al</button></div></div></details>
<details><summary><i>02</i><b>Sakal ve ustura</b><span>200 ₺</span></summary><div class="bd"><p>Şekil, ustura tıraşı, sıcak havlu. Yaklaşık 20 dk.</p><div><button class="btn" data-open data-s="Erkek kesim">Randevu al</button></div></div></details>
<details><summary><i>03</i><b>Kesim + sakal</b><span>500 ₺</span></summary><div class="bd"><p>İkisi bir arada, tek randevu. Yaklaşık 50 dk.</p><div><button class="btn" data-open data-s="Erkek kesim">Randevu al</button></div></div></details>
<details><summary><i>04</i><b>Kadın kesim ve fön</b><span>450 ₺</span></summary><div class="bd"><p>Saç tipine göre kesim, yıkama ve fön. 45–60 dk.</p><div><button class="btn" data-open data-s="Kesim ve fön">Randevu al</button></div></div></details>
<details><summary><i>05</i><b>Boya ve bakım</b><span>1.800 ₺</span></summary><div class="bd"><p>Renk danışmanlığı, boya, koruyucu bakım. 2 saat.</p><div><button class="btn" data-open data-s="Tek renk boya">Randevu al</button></div></div></details></div></section>
<section id="stil" style="border-top:2px solid var(--line)"><div class="lab">Stilini seç</div><h2>Hangisi sen?</h2>
<div class="pick"><div class="ph pp" id="pph" data-p="19664876"></div><div><div class="tb" id="ptb"><button class="on">Fade</button><button>Klasik</button><button>Uzun</button></div><div class="res"><h3 id="pn">Fade</h3><p id="pd">Yanlar kısa ve geçişli, üst orta boy. Her 3–4 haftada bir tazelenir.</p><div class="st"><div><small>Süre</small><span id="pt">35 dk</span></div><div><small>Fiyat</small><span id="pp">400 ₺</span></div></div><button class="btn" id="pb" data-open data-s="Erkek kesim">Bu stile randevu al</button></div></div></div></section>
<section id="galeri" data-gal style="border-top:2px solid var(--line)"><div class="lab">Galeri</div><h2>Kareler.</h2><div class="fs">""" + ''.join('<a href="#" class="gi" data-p="%s"><img data-i="%s" data-w="800" alt="Galeri" loading="lazy"></a>' % (i, i) for i in (19664876, 8867400, 6599030, 15659494, 7750144, 3993308, 8468134, 3356170)) + """</div></section>
<section id="kadro" style="border-top:2px solid var(--line)"><div class="lab">Kadro</div><h2>Koltuktakiler.</h2><div class="ro">
<div class="r"><div><h3>Murat</h3><small>Kesim · sakal · fade</small></div><p style="color:var(--mut)">Erkek kesimde 12 yıllık usta.</p><div data-slots="3" data-e="Murat" data-s="Erkek kesim"></div></div>
<div class="r"><div><h3>Elif</h3><small>Renk · bakım</small></div><p style="color:var(--mut)">Boya ve balyajda renk uzmanı.</p><div data-slots="3" data-e="Elif" data-s="Tek renk boya"></div></div>
<div class="r"><div><h3>Selin</h3><small>Kadın kesim · gelin</small></div><p style="color:var(--mut)">Fön ve gelin saçı.</p><div data-slots="3" data-e="Selin" data-s="Kesim ve fön"></div></div></div></section>
<section id="sss" class="faq" style="border-top:2px solid var(--line)"><div class="lab">SSS</div><h2>Sorular.</h2>
<details><summary>Randevusuz gelebilir miyim?</summary><p>Boş koltuk varsa evet; ama saatinizi ayırmak için randevu almanızı öneririz.</p></details><details><summary>Çocuk kesimi var mı?</summary><p>Var. Randevu notuna yaşı yazmanız yeterli.</p></details><details><summary>Ödeme nasıl?</summary><p>Nakit, kart veya havale. Tek fişle kapanır.</p></details></section>
<footer id="iletisim"><div class="big">Kesim.<br>Hane.</div><div class="fw"><div><h5>Adres</h5><a>Barbaros Blv. 8<br>Beşiktaş / İstanbul</a></div><div><h5>Saat</h5><a>Salı–Cumartesi<br>10:00–20:00</a></div><div><h5>Ara</h5><a href="tel:02120000000">0212 000 00 00</a><a href="#">WhatsApp</a></div><div><h5>Takip</h5><a href="#">Instagram</a><a href="#">TikTok</a></div></div><div class="fx"><span>© 2026 Kesimhane</span><span>KVKK · Gizlilik</span><a href="https://onlinekaydet.com">OnlineKaydet ile yayınlanır</a></div></footer>
<div id="dock"><a href="tel:02120000000">Ara</a><button class="btn" data-open>Randevu al</button></div>
"""
JS = """(function(){var $=function(s){return document.querySelector(s)};
var mn=$('#mn');function m(o){mn.classList.toggle('on',o);document.body.style.overflow=o?'hidden':''}$('#bg').onclick=function(){m(true)};$('#mx').onclick=function(){m(false)};mn.addEventListener('click',function(e){if(e.target.closest('a'))m(false)});OK.esc=function(){m(false)};
var w=[].slice.call(document.querySelectorAll('.hero h1 .w')),i=0;setInterval(function(){var o=w[i];o.classList.remove('on');o.classList.add('out');setTimeout(function(){o.classList.remove('out')},700);i=(i+1)%w.length;w[i].classList.add('on')},2600);
var S=[['Fade','Yanlar kısa ve geçişli, üst orta boy. Her 3–4 haftada bir tazelenir.','35 dk','400 ₺','19664876'],['Klasik','Yan ayrık, düzgün hat, makasla şekil. Her ofise yakışır.','30 dk','350 ₺','8867400'],['Uzun','Boyu korur, uçları ve şekli toplar. Sakalla bir arada çalışır.','45 dk','450 ₺','6599030']];
var b=[].slice.call(document.querySelectorAll('#ptb button'));b.forEach(function(x,k){x.onclick=function(){b.forEach(function(y){y.classList.toggle('on',y===x)});var s=S[k];$('#pn').textContent=s[0];$('#pd').textContent=s[1];$('#pt').textContent=s[2];$('#pp').textContent=s[3];$('#pph').style.backgroundImage='url(https://images.pexels.com/photos/'+s[4]+'/pexels-photo-'+s[4]+'.jpeg?auto=compress&cs=tinysrgb&w=1400)'}});
function q(){var d=OK.ist(),n=(d.getHours()+d.getDate())%4;$('#qn').textContent=n;$('#qm').textContent=n*12+5}q();OK.onRefresh=q})()"""
def build():
    return page('Kesimhane · Beşiktaş, İstanbul', '', CSS, BODY, JS, '#0c0c0c', FONTS)
