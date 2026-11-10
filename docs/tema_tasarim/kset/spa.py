from ksh import page
FONTS = 'family=Cormorant:ital,wght@0,400;0,500;1,400&family=Jost:wght@400;500;600'
CSS = """
:root{--bg:#eef2ea;--ink:#25382c;--mut:#667a6c;--ac:#b9814f;--sage:#d7e1d3;--line:rgba(37,56,44,.18);--sbg:#f6f8f3;--sink:#25382c;--sac:#b9814f;--sline:rgba(37,56,44,.25);--sfont:'Cormorant',serif;--sbody:'Jost',sans-serif;--sr:99px}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font:400 16px/1.7 'Jost',sans-serif;overflow-x:hidden}
h1,h2,h3{font-family:'Cormorant',serif;font-weight:400;line-height:1.05}
a{color:inherit;text-decoration:none}button{font:inherit;color:inherit;cursor:pointer;border:0;background:none}
.pp{background-size:cover;background-position:center;background-color:#c9d5c4}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:52px;padding:0 30px;border-radius:99px;background:var(--ink);color:#fff;font-weight:500;letter-spacing:.04em;transition:.4s}.btn:hover{background:var(--ac)}.btn.l{background:#fff;color:var(--ink)}.btn.l:hover{background:var(--ac);color:#fff}
.btn.o{background:transparent;border:1.5px solid var(--ink);color:var(--ink)}.btn.o:hover{background:var(--ink);color:#fff}
.eb{font:500 13px 'Jost';letter-spacing:.28em;text-transform:uppercase;color:var(--ac)}
.chip{display:inline-flex;align-items:center;min-height:44px;padding:0 18px;margin:0 6px 6px 0;border-radius:99px;background:rgba(255,255,255,.7);border:1px solid var(--line);font-weight:500;transition:.3s}.chip:hover{background:var(--ink);color:#fff}
/* ortalı logo menü */
#nv{position:absolute;top:0;left:0;right:0;z-index:50;display:grid;grid-template-columns:44px 1fr auto;gap:6px;align-items:center;padding:14px 20px;color:#fff}
#nv .lg{font:italic 400 26px 'Cormorant';text-align:center;letter-spacing:.02em;white-space:nowrap}
#nv ul{display:none;list-style:none;gap:26px;font-size:14px;letter-spacing:.1em;text-transform:uppercase}
#nv .r{display:flex;justify-content:flex-end;gap:8px;align-items:center}
#nv .btn{min-height:44px;padding:0 16px;background:#fff;color:var(--ink);font-size:14px;white-space:nowrap}
#bg{width:44px;height:44px;border-radius:50%;border:1px solid rgba(255,255,255,.6);color:#fff;display:grid;place-items:center;justify-self:start}#bg i,#bg i:before,#bg i:after{display:block;width:16px;height:1.5px;background:#fff;position:relative;content:""}#bg i:before{position:absolute;top:-5px}#bg i:after{position:absolute;top:5px}
#mn{position:fixed;inset:0;z-index:90;background:var(--ink);color:#f1efe6;padding:90px 28px 30px;overflow:auto;opacity:0;visibility:hidden;transition:.5s;text-align:center}#mn.on{opacity:1;visibility:visible}
#mn a.l{display:block;font:italic 400 clamp(38px,11vw,64px)/1.25 'Cormorant'}#mn .s{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:26px}#mn .s a{border:1px solid rgba(255,255,255,.35);border-radius:99px;min-height:44px;display:flex;align-items:center;padding:0 18px;font-size:14px}
#mx{position:absolute;top:14px;left:20px;width:44px;height:44px;border-radius:50%;border:1px solid rgba(255,255,255,.5);color:#fff;font-size:24px}
/* hero */
.hero{position:relative;min-height:100svh;display:flex;align-items:flex-end;border-radius:0 0 40px 40px;overflow:hidden}
.hero .pp{position:absolute;inset:0;background-position:center 30%;transform:scale(1.06);animation:z 10s ease-out forwards}@keyframes z{to{transform:none}}
.hero:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,30,22,.45),rgba(20,30,22,.1) 35%,rgba(20,30,22,.78))}
.hc{position:relative;z-index:2;width:100%;padding:0 20px 28px;color:#fff;max-width:1100px;margin:auto}.hc h1{font-size:clamp(50px,14vw,110px);font-weight:400;margin:12px 0 16px}.hc h1 em{display:block}
.eb.w{color:#e9cfae}
.book{background:rgba(255,255,255,.96);color:var(--ink);border-radius:26px;padding:18px;display:grid;gap:12px;margin-top:20px;box-shadow:0 30px 60px -30px #000}
.book small{font-size:13px;color:var(--mut)}.book .open{display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--mut)}.book .open:before{content:"";width:8px;height:8px;border-radius:50%;background:#d9776b}.book .open.o:before{background:#4cae6a}
.book select{min-height:50px;border-radius:14px;border:1px solid var(--line);padding:0 14px;background:#fff;font:inherit;color:var(--ink);width:100%}
section{padding:80px 22px;max-width:1100px;margin:auto}section h2{font-size:clamp(40px,11vw,72px);margin:10px 0 12px}.lead{color:var(--mut);max-width:520px}
.c{text-align:center}.c .lead{margin:0 auto}
/* ritüel satırları */
.rt{display:grid;gap:34px;margin-top:34px}.rt .it{display:grid;gap:16px}.rt .ph{aspect-ratio:4/3;border-radius:200px 200px 24px 24px;overflow:hidden;position:relative}.rt .ph .pp{position:absolute;inset:0;transition:transform 1.4s}.rt .it:hover .pp{transform:scale(1.05)}
.rt h3{font-size:38px}.rt .pr{font:500 15px 'Jost';color:var(--ac);letter-spacing:.06em}.rt p{color:var(--mut)}
/* ritüel seçici (3 adım) */
.wz{background:#fff;border-radius:30px;padding:24px 20px;margin-top:26px;border:1px solid var(--line)}
.wz .st{display:flex;gap:6px;margin-bottom:16px}.wz .st i{flex:1;height:3px;border-radius:3px;background:var(--sage);transition:.4s}.wz .st i.on{background:var(--ac)}
.wz h3{font-size:34px;margin-bottom:12px}.wz .op{display:grid;gap:8px}.wz .op button{min-height:54px;border-radius:16px;border:1px solid var(--line);text-align:left;padding:0 18px;font-weight:500;background:var(--bg);transition:.3s}.wz .op button:hover{background:var(--ink);color:#fff}
.wz .rs{display:none}.wz .rs h3{color:var(--ac)}
/* galeri slayt */
.sl{position:relative;margin-top:26px;border-radius:30px;overflow:hidden;aspect-ratio:4/5;max-height:560px;background:#c9d5c4}
.sl .gi{position:absolute;inset:0;opacity:0;transition:opacity 1.2s;cursor:zoom-in}.sl .gi.cur{opacity:1}.sl .gi img{width:100%;height:100%;object-fit:cover}
.sl .dt{position:absolute;bottom:14px;left:0;right:0;display:flex;justify-content:center;gap:8px;z-index:3}.sl .dt button{width:10px;height:10px;border-radius:50%;background:rgba(255,255,255,.5);min-height:0}.sl .dt button.on{background:#fff;width:26px;border-radius:6px}
.tp{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}.tp .gi{aspect-ratio:1;border-radius:20px;overflow:hidden;cursor:zoom-in}.tp img{width:100%;height:100%;object-fit:cover;transition:transform 1s}.tp .gi:hover img{transform:scale(1.06)}
/* ekip */
.tm{display:grid;gap:14px;margin-top:26px}.tm .m{display:grid;grid-template-columns:96px 1fr;gap:16px;align-items:center;background:#fff;border-radius:26px;padding:14px;border:1px solid var(--line)}.tm .pp{width:96px;height:96px;border-radius:50%}.tm h3{font-size:30px}.tm small{color:var(--mut)}
/* hediye çeki */
.gift{background:var(--ink);color:#f1efe6;border-radius:34px;padding:30px 24px;margin-top:20px;display:grid;gap:18px}.gift h2{color:#fff}.gift .lead{color:#c7d3c9}
.amts{display:flex;gap:8px;flex-wrap:wrap}.amts button{min-height:44px;padding:0 20px;border-radius:99px;border:1px solid rgba(255,255,255,.4);font-weight:500}.amts button.on{background:#fff;color:var(--ink)}
.faq details{border-bottom:1px solid var(--line)}.faq summary{list-style:none;cursor:pointer;min-height:64px;display:flex;align-items:center;justify-content:space-between;font:400 24px 'Cormorant'}.faq summary::-webkit-details-marker{display:none}.faq summary:after{content:"+";color:var(--ac);font-size:28px}.faq details[open] summary:after{content:"–"}.faq p{color:var(--mut);padding-bottom:16px}
.mp{margin-top:22px;border-radius:30px;min-height:260px;position:relative;overflow:hidden;background:#dfe7da}.mp svg{position:absolute;inset:0;width:100%;height:100%}.mp b{position:absolute;left:50%;top:46%;transform:translate(-50%,-100%);background:var(--ink);color:#fff;padding:10px 18px;border-radius:99px;font-weight:500;white-space:nowrap}
footer{background:var(--ink);color:#d3ddd5;text-align:center;padding:60px 22px 40px;border-radius:40px 40px 0 0;margin-top:40px}
footer .fl{font:italic 400 44px 'Cormorant';color:#fff}footer nav{display:flex;flex-wrap:wrap;justify-content:center;gap:2px 20px;margin:18px 0}footer nav a{display:flex;align-items:center;min-height:44px}
footer .s{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}footer .s a{border:1px solid rgba(255,255,255,.3);border-radius:99px;min-height:44px;display:flex;align-items:center;padding:0 18px;font-size:14px}
footer small{display:block;margin-top:26px;font-size:13px}footer small a{text-decoration:underline}
@media(min-width:900px){
#nv{padding:22px 48px;grid-template-columns:1fr auto 1fr}#nv ul{display:flex}#bg{display:none}#nv .lg{font-size:38px}
.hc{padding:0 48px 60px}.hero{align-items:flex-end}.book{grid-template-columns:1fr auto;align-items:center;max-width:820px;border-radius:99px;padding:14px 14px 14px 30px}
section{padding:110px 48px}.rt .it{grid-template-columns:1fr 1fr;align-items:center;gap:60px}.rt .it:nth-child(even) .ph{order:2}.rt .ph{aspect-ratio:1}
.sl{aspect-ratio:16/9;max-height:600px}.tm{grid-template-columns:repeat(3,1fr)}.gift{grid-template-columns:1.2fr 1fr;align-items:center;padding:60px}
}
"""
BODY = """
<nav id="nv"><button id="bg" aria-label="Menü"><i></i></button><ul id="ul-l" style="justify-content:flex-start"><li><a href="#ritueller">Ritüeller</a></li><li><a href="#galeri">Galeri</a></li><li><a href="#ekip">Ekip</a></li></ul>
<a class="lg" href="#" style="grid-column:2">Sakin Saç</a><div class="r"><ul style="margin-right:16px"><li><a href="#hediye">Hediye çeki</a></li><li><a href="#iletisim">İletişim</a></li></ul><button class="btn" data-open>Randevu al</button></div></nav>
<div id="mn"><button id="mx" aria-label="Kapat">×</button><a class="l" href="#ritueller">Ritüeller</a><a class="l" href="#sec">Sana göre</a><a class="l" href="#galeri">Galeri</a><a class="l" href="#ekip">Ekip</a><a class="l" href="#hediye">Hediye çeki</a><a class="l" href="#iletisim">İletişim</a>
<div class="s"><a href="#">Instagram</a><a href="#">WhatsApp</a><a href="#">Pinterest</a><a href="#">Google Haritalar</a></div></div>
<header class="hero"><div class="pp" data-p="20046793" data-w="1800"></div><div class="hc"><div class="eb w">Bahçelievler · İzmir · Saç ve bakım</div><h1>Saçınıza <em>sakin bir mola.</em></h1>
<div class="book"><div data-live="3"><div class="open" data-open-now><span></span></div><small data-live-t style="display:block;margin:2px 0 8px">Bugün boş saatler</small></div><button class="btn" data-open>Randevu al</button></div></div></header>
<section id="ritueller" class="c"><div class="eb">Ritüeller</div><h2>Üç sakin bakım.</h2><p class="lead">Her ritüel, size ayrılmış bir koltukta ve acele edilmeden uygulanır.</p>
<div class="rt" style="text-align:left"><div class="it"><div class="ph"><div class="pp" data-p="10028673"></div></div><div><h3>Renk ritüeli</h3><div class="pr">2 SAAT · 1.800 ₺'DEN</div><p style="margin:10px 0 16px">Renk danışmanlığı, boya ve koruyucu bakım; fön dahil.</p><button class="btn o" data-open data-s="Tek renk boya">Randevu al</button></div></div>
<div class="it"><div class="ph"><div class="pp" data-p="23349912"></div></div><div><h3>Bakım ritüeli</h3><div class="pr">90 DK · 1.500 ₺'DEN</div><p style="margin:10px 0 16px">Keratin ya da yoğun onarım; saçınızın ihtiyacına göre seçilir.</p><button class="btn o" data-open data-s="Keratin bakım">Randevu al</button></div></div>
<div class="it"><div class="ph"><div class="pp" data-p="3993462"></div></div><div><h3>Kesim ve fön</h3><div class="pr">60 DK · 450 ₺'DEN</div><p style="margin:10px 0 16px">Saç tipinize göre şekil; yıkama, kesim ve fön.</p><button class="btn o" data-open data-s="Kesim ve fön">Randevu al</button></div></div></div></section>
<section id="sec" style="padding-top:20px"><div class="eb">Sana göre</div><h2>Ritüelini bulalım.</h2>
<div class="wz" id="wz"><div class="st"><i class="on"></i><i></i><i></i></div><div class="q"><h3 id="wq">Saçınız nasıl?</h3><div class="op" id="wo"><button>Boyalı ve yıpranmış</button><button>Doğal ama sönük</button><button>Uzun ve bakımsız</button></div></div><div class="rs"><h3 id="wr"></h3><p id="wt" style="color:var(--mut);margin:6px 0 16px"></p><button class="btn" id="wb" data-open>Bu ritüele randevu al</button> <button class="btn o" id="wa" style="margin-top:8px">Baştan başla</button></div></div></section>
<section id="galeri" data-gal><div class="eb">Galeri</div><h2>Salondan kareler.</h2>
<div class="sl" id="sl">""" + ''.join('<a href="#" class="gi%s" data-p="%s"><img data-i="%s" data-w="1400" alt="Salon"></a>' % (' cur' if k == 0 else '', i, i) for k, i in enumerate((3993320, 7195812, 29189945, 10028673))) + """<div class="dt" id="dt"></div></div>
<div class="tp">""" + ''.join('<a href="#" class="gi" data-p="%s"><img data-i="%s" data-w="500" alt="Salon" loading="lazy"></a>' % (i, i) for i in (8468143, 7750144, 20092122, 8468134, 3356174, 18367697)) + """</div></section>
<section id="ekip"><div class="eb">Ekip</div><h2>Size eşlik edenler.</h2><div class="tm">
<div class="m"><div class="pp" data-p="3993467" data-w="300"></div><div><h3>Elif</h3><small>Renk ritüeli</small><div style="margin-top:6px" data-slots="2" data-e="Elif" data-s="Tek renk boya"></div></div></div>
<div class="m"><div class="pp" data-p="29096366" data-w="300"></div><div><h3>Selin</h3><small>Bakım ritüeli</small><div style="margin-top:6px" data-slots="2" data-e="Selin" data-s="Keratin bakım"></div></div></div>
<div class="m"><div class="pp" data-p="6599030" data-w="300"></div><div><h3>Murat</h3><small>Kesim ve şekil</small><div style="margin-top:6px" data-slots="2" data-e="Murat" data-s="Erkek kesim"></div></div></div></div></section>
<section id="hediye"><div class="gift"><div><div class="eb" style="color:#e9cfae">Hediye çeki</div><h2>Bir mola hediye edin.</h2><p class="lead">Seçtiğiniz tutarda çek, kodla salonda kullanılır.</p></div>
<div><div class="amts" id="am"><button>500 ₺</button><button class="on">1.000 ₺</button><button>2.000 ₺</button></div><p id="gt" style="margin:16px 0;font:italic 400 30px 'Cormorant'">1.000 ₺ değerinde bir mola · Kod <b id="gc">SKN-4F7Q</b></p><button class="btn l" id="gb">Çeki oluştur</button></div></div></section>
<section class="faq"><div class="eb">Sık sorulanlar</div><h2>Merak edilenler.</h2><details><summary>Randevuyu nasıl iptal ederim?</summary><p>Hatırlatma mesajındaki bağlantıdan ya da arayarak, bir gün öncesine kadar ücretsiz.</p></details><details><summary>Fiyatlar kesin mi?</summary><p>Başlangıç fiyatıdır; boy ve yoğunluğa göre kesin tutar işlemden önce söylenir.</p></details><details><summary>İkram var mı?</summary><p>Evet, bitki çayı ve kahve.</p></details></section>
<section id="iletisim" class="c"><div class="eb">İletişim</div><h2>Sizi bekliyoruz.</h2><p class="lead">Cemal Gürsel Cd. 21, Bahçelievler / İzmir<br>0232 000 00 00 · Salı–Cumartesi 10:00–20:00</p><div class="mp"><svg viewBox="0 0 600 300" preserveAspectRatio="xMidYMid slice"><rect width="600" height="300" fill="#dfe7da"/><g stroke="#fff" stroke-width="14" fill="none"><path d="M-10 90 L610 150"/><path d="M200 -10 L260 310"/><path d="M-10 230 L610 200" stroke-width="9"/></g><g fill="#cbd8c6"><rect x="40" y="110" width="110" height="60" rx="14"/><rect x="290" y="40" width="90" height="70" rx="14"/><rect x="450" y="190" width="100" height="70" rx="14"/></g></svg><b>Sakin Saç</b></div></section>
<footer><div class="fl">Sakin Saç</div><nav><a href="#ritueller">Ritüeller</a><a href="#galeri">Galeri</a><a href="#ekip">Ekip</a><a href="#hediye">Hediye çeki</a><a href="#iletisim">İletişim</a></nav><div class="s"><a href="#">Instagram</a><a href="#">WhatsApp</a><a href="#">Pinterest</a></div><small>© 2026 Sakin Saç · KVKK · Gizlilik · <a href="https://onlinekaydet.com">OnlineKaydet ile yayınlanır</a></small></footer>
"""
JS = """(function(){var $=function(s){return document.querySelector(s)},A=function(s){return[].slice.call(document.querySelectorAll(s))};
var mn=$('#mn');function m(o){mn.classList.toggle('on',o);document.body.style.overflow=o?'hidden':''}$('#bg').onclick=function(){m(true)};$('#mx').onclick=function(){m(false)};mn.addEventListener('click',function(e){if(e.target.closest('a'))m(false)});OK.esc=function(){m(false)};
var sl=A('#sl .gi'),dt=$('#dt'),k=0,tm;sl.forEach(function(x,i){var b=document.createElement('button');b.onclick=function(e){e.stopPropagation();go(i)};dt.appendChild(b)});
function go(i){k=i;sl.forEach(function(x,j){x.classList.toggle('cur',j===i)});A('#dt button').forEach(function(b,j){b.classList.toggle('on',j===i)});clearInterval(tm);tm=setInterval(function(){go((k+1)%sl.length)},4500)}go(0);
var Q=[['Saçınız nasıl?',['Boyalı ve yıpranmış','Doğal ama sönük','Uzun ve bakımsız']],['Ne istersiniz?',['Rengi tazelemek','Işıltı ve yumuşaklık','Şekil ve toparlama']]],R={'0':['Bakım ritüeli','Yıpranmış saçlar için yoğun onarım ve nem dengesi. Keratin ya da onarıcı maske uzmanla seçilir.','Keratin bakım'],'1':['Renk ritüeli','Yeni bir ton ya da canlı bir yenileme; koruyucu bakım ve fön dahil.','Tek renk boya'],'2':['Kesim ve fön','Uçları toplayan, saç tipinize uygun bir şekil ve fön.','Kesim ve fön']};
var st=0,a1=0;function ren(){A('#wz .st i').forEach(function(x,i){x.classList.toggle('on',i<=st)});if(st<2){$('#wz .q').style.display='block';$('#wz .rs').style.display='none';$('#wq').textContent=Q[st][0];$('#wo').innerHTML=Q[st][1].map(function(x){return'<button>'+x+'</button>'}).join('')}}
$('#wo').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;var i=A('#wo button').indexOf(b);if(st===0){a1=i;st=1;ren()}else{st=2;var r=R[a1===0&&i===0?'1':a1===0?'0':i===2?'2':a1===2?'2':i===0?'1':'0'];A('#wz .st i').forEach(function(x){x.classList.add('on')});$('#wz .q').style.display='none';$('#wz .rs').style.display='block';$('#wr').textContent=r[0];$('#wt').textContent=r[1];$('#wb').dataset.s=r[2]}});
$('#wa').onclick=function(){st=0;ren()};ren();
var am=A('#am button');am.forEach(function(b){b.onclick=function(){am.forEach(function(x){x.classList.toggle('on',x===b)});$('#gt').firstChild.textContent=b.textContent+' değerinde bir mola · Kod '}});$('#gb').onclick=function(){$('#gc').textContent='SKN-'+Math.random().toString(36).slice(2,6).toUpperCase()};
})()"""
def build():
    return page('Sakin Saç · Bahçelievler, İzmir', '', CSS, BODY, JS, '#25382c', FONTS)
