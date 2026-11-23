# -*- coding: utf-8 -*-
"""Sinematik demo siteler (GSAP + ScrollTrigger + Lenis). Çalıştır: python3 demo.py -> docs/demo/<slug>/index.html
Görseller Pexels (ücretsiz, ticari kullanım serbest) bağlantılarıdır; video kaydırmayla ilerler."""
import os, sys, json, html as H
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tema20'))
import foto
import common
R = os.path.dirname(os.path.abspath(__file__))

SITES = [
 dict(slug='makas', idx=6, name='MAKAS', sub='BERBER KULÜBÜ', title='Makas Berber Kulübü',
  bg='#0b0908', ink='#f4efe8', mut='#a89e92', ac='#e0572a', ac2='#8c1d18', paper='#f3eee4', hf='Anton', mono='Space Mono', bf='Manrope', dark=True,
  caps=[('HOŞ GELDİN.', 'Kapıdan içeri gir'), ('USTALIK.', 'Her kesim ölçülü'), ('FARKLI ÇIK.', 'Koltuğun hazır')],
  hero_cta='Koltuğunu ayır', mq=['Klasik kesim', 'Skin fade', 'Sakal şekli', 'Sıcak havlu', 'Randevusuz gelen de olur', 'Her gün 21.00’e kadar'],
  stmt='Kalabalık bir salon değil, iki ayakta bir sanat: usta, ayna ve koltuk.',
  svc_h=('SATIRI SEÇ.', 'DAMGALAYALIM.'), svc_p='Hizmete dokun, fişte damgalansın; sonra randevuya geç.', paper_t='FİYAT LİSTESİ', paper_s='berber',
  svc=[('Saç kesimi', 450, '30 dk'), ('Skin fade', 550, '40 dk'), ('Sakal düzeltme', 300, '20 dk'), ('Sıcak havlu tıraş', 350, '30 dk'), ('Saç + sakal', 700, '60 dk'), ('Kafa tıraşı', 350, '25 dk'), ('Çizgi / kontur', 200, '15 dk'), ('Çocuk kesimi', 300, '25 dk'), ('Tam bakım', 850, '75 dk')],
  team_h='USTALARLA TANIŞ.', team=[('Alper', 'Usta berber', 0), ('Cem', 'Fade uzmanı', 1), ('Murat', 'Kıdemli usta', 2)],
  gal_h='KANIT.', gal=[1, 3, 4, 5, 6, 7], book_h=('KOLTUĞUN', 'SENİ BEKLİYOR.'), book_p='İyi kesim tesadüf değildir.', unit='usta', fin=('BİR TÜRLÜ GİR.', 'BAŞKA TÜRLÜ ÇIK.'), fin_cta='Randevu al',
  nav=['Kulüp', 'Hizmetler', 'Ustalar', 'Galeri'], addr='Örnek Mah., Örnek Sk. · Ankara', hrs='Her gün 10.00 – 21.00', tl='₺'),
]

CSS = r'''
:root{--bg:%(bg)s;--ink:%(ink)s;--mut:%(mut)s;--ac:%(ac)s;--ac2:%(ac2)s;--paper:%(paper)s;--hf:'%(hf)s',Impact,sans-serif;--mono:'%(mono)s',monospace;--bf:'%(bf)s',system-ui,sans-serif;--ln:%(ln)s}
*{box-sizing:border-box;margin:0}html{overflow-x:clip}body{overflow-x:clip;background:var(--bg);color:var(--ink);font:400 17px/1.55 var(--bf);-webkit-font-smoothing:antialiased}
img,video{display:block;max-width:100%%}a{color:inherit}
.lenis.lenis-smooth{scroll-behavior:auto!important}
:focus-visible{outline:3px solid var(--ac);outline-offset:3px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
h1,h2,h3{font-family:var(--hf);font-weight:%(hw)s;text-transform:uppercase;line-height:.92;letter-spacing:-.01em;overflow-wrap:break-word;min-width:0}
.lb{font:600 12px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--mut)}
/* preloader */
#pre{position:fixed;inset:0;z-index:100;background:var(--bg);display:grid;place-items:center;transition:opacity .6s,visibility .6s}
#pre.off{opacity:0;visibility:hidden}
#pre b{font:400 clamp(48px,12vw,150px)/1 var(--hf);text-transform:uppercase}#pre i{font:600 14px var(--mono);font-style:normal;color:var(--mut);display:block;text-align:center;margin-top:10px}
/* nav */
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;justify-content:space-between;align-items:center;padding:20px clamp(18px,4vw,48px);mix-blend-mode:normal}
nav.top .lg{font:400 24px/1 var(--hf);text-transform:uppercase;text-decoration:none;color:#fff;text-shadow:0 1px 14px rgba(0,0,0,.45)}
nav.top .lg small{font:600 10px var(--mono);letter-spacing:.14em;margin-left:8px;opacity:.8}
nav.top ul{display:flex;gap:26px;list-style:none;padding:0}nav.top li a{font:600 12px var(--mono);letter-spacing:.1em;text-transform:uppercase;text-decoration:none;color:#fff;text-shadow:0 1px 12px rgba(0,0,0,.5)}
nav.top li a:hover{color:var(--ac)}
nav.top{transition:background .3s,backdrop-filter .3s}nav.top.solid{background:color-mix(in srgb,var(--bg) 88%%,transparent);backdrop-filter:blur(10px);padding-block:12px}nav.top.solid .lg,nav.top.solid li a{color:var(--ink);text-shadow:none}
.btn{display:inline-flex;align-items:center;gap:10px;min-height:48px;padding:0 22px;background:var(--ac);color:#fff;border:0;font:700 13px var(--mono);letter-spacing:.1em;text-transform:uppercase;text-decoration:none;cursor:pointer;transition:transform .15s,filter .15s}
.btn:hover{transform:translateY(-2px);filter:brightness(1.08)}.btn:active{transform:translateY(0) scale(.98)}
.btn.ghost{background:transparent;color:var(--ink);border:1.5px solid var(--ink)}
/* hero scrub */
#hero{position:relative;height:420vh}
.stage{position:sticky;top:0;height:100svh;overflow:hidden;background:#000}
.stage video,.stage .poster{position:absolute;inset:0;width:100%%;height:100%%;object-fit:cover}
.stage:after{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.45),rgba(0,0,0,.05) 35%%,rgba(0,0,0,.6));pointer-events:none}
.cap{position:absolute;left:clamp(18px,4vw,64px);bottom:14vh;z-index:3;color:#fff;opacity:0;transform:translateY(40px);max-width:min(72vw,1100px);transition:opacity .5s,transform .6s}
.cap.on{opacity:1;transform:none}
.cap h1,.cap h2{font-size:clamp(48px,10vw,160px);text-shadow:0 4px 40px rgba(0,0,0,.5)}
.cap p{font:600 13px var(--mono);letter-spacing:.14em;text-transform:uppercase;margin-top:16px;opacity:.9}
.stage .btn{position:absolute;right:clamp(18px,4vw,64px);bottom:14vh;z-index:3}
.prog{position:absolute;left:clamp(18px,4vw,64px);right:clamp(18px,4vw,64px);bottom:5vh;height:2px;background:rgba(255,255,255,.25);z-index:3}.prog i{display:block;height:100%%;width:0;background:var(--ac)}
.hint{position:absolute;left:50%%;bottom:5vh;transform:translateX(-50%%);z-index:3;font:600 11px var(--mono);letter-spacing:.2em;color:#fff;opacity:.8;margin-bottom:14px}
/* marquee */
.mq{overflow:hidden;border-block:1px solid var(--ln);padding:20px 0;background:var(--bg)}
.mq div{display:flex;width:max-content;gap:48px;animation:mq 30s linear infinite}
.mq span{font:400 clamp(26px,4vw,48px)/1 var(--hf);text-transform:uppercase;white-space:nowrap}.mq span:nth-child(even){color:var(--ac)}
@keyframes mq{to{transform:translateX(-50%%)}}
/* statement */
.st{padding:18vh clamp(18px,4vw,64px);max-width:1400px;margin:auto}
.st p{font:400 clamp(34px,6vw,86px)/1.02 var(--hf);text-transform:uppercase}
.st .w{opacity:.18;transition:opacity .2s}.st .w.on{opacity:1}
/* services receipt */
.sv{padding:12vh clamp(18px,4vw,64px);display:grid;grid-template-columns:minmax(0,1fr) minmax(0,520px);gap:clamp(24px,6vw,96px);align-items:start;max-width:1400px;margin:auto}
.sv .l{position:sticky;top:12vh}
.sv h2{font-size:clamp(40px,6.4vw,104px)}.sv h2 em{font-style:normal;color:var(--mut)}
.sv .l>p{margin-top:20px;color:var(--mut);max-width:34ch}
.sel{margin-top:36px;padding:22px 24px;border:1px solid var(--ln);background:color-mix(in srgb,var(--ink) 5%%,transparent)}
.sel b{display:block;font:600 14px var(--mono);text-transform:uppercase;min-height:20px;margin-top:6px}
.sel output{display:block;font:700 clamp(44px,6vw,76px)/1 var(--mono);margin-top:8px;font-variant-numeric:tabular-nums}
.sel .btn{margin-top:18px}
.paper{position:relative;background:var(--paper);color:#17130f;padding:34px 30px 54px;font-family:var(--mono);box-shadow:0 30px 70px -30px rgba(0,0,0,.6);-webkit-mask:conic-gradient(from -45deg at bottom,#0000,#000 1deg 89deg,#0000 90deg) 50%% 100%%/22px 100%%;mask:conic-gradient(from -45deg at bottom,#0000,#000 1deg 89deg,#0000 90deg) 50%% 100%%/22px 100%%;transform:rotate(1.2deg)}
.paper h3{font-size:clamp(34px,5vw,56px);text-align:center}.paper h3+i{display:block;text-align:center;font:italic 22px Georgia,serif;margin:-2px 0 22px}
.paper ul{list-style:none;padding:0}
.paper li button{all:unset;box-sizing:border-box;display:flex;justify-content:space-between;gap:12px;width:100%%;padding:10px 8px;font:600 14px var(--mono);text-transform:uppercase;cursor:pointer;position:relative;transition:background .15s,color .15s}
.paper li button:hover{background:#17130f;color:var(--paper)}
.paper li button:focus-visible{outline:3px solid var(--ac)}
.paper li button[aria-pressed=true]{text-decoration:line-through;text-decoration-thickness:2px;background:#17130f;color:var(--paper)}
.paper li button[aria-pressed=true]:after{content:'SEÇİLDİ';position:absolute;right:56px;top:50%%;transform:translateY(-50%%) rotate(-6deg);border:2px solid var(--ac);color:var(--ac);background:var(--paper);padding:1px 6px;font-size:10px;letter-spacing:.1em;text-decoration:none;animation:stamp .25s cubic-bezier(.2,1.6,.4,1)}
@keyframes stamp{from{transform:translateY(-50%%) rotate(-6deg) scale(2.2);opacity:0}}
.paper .tot{display:flex;justify-content:space-between;border-top:2px dashed #17130f;margin-top:16px;padding-top:14px;font:700 20px var(--mono)}
.bar{height:46px;margin:18px auto 0;width:70%%;background:repeating-linear-gradient(90deg,#17130f 0 2px,transparent 2px 5px,#17130f 5px 6px,transparent 6px 10px)}
.paper small{display:block;text-align:center;margin-top:8px;font:600 11px var(--mono);letter-spacing:.1em;color:#6b6258}
/* team 3d */
.tm{padding:12vh 0;text-align:center;overflow:hidden}
.tm h2{font-size:clamp(46px,9vw,140px);padding:0 18px}
.car{position:relative;height:min(74vh,640px);margin-top:4vh;perspective:1600px;touch-action:pan-y}
.cd{position:absolute;left:50%%;top:0;width:min(330px,70vw);height:100%%;margin-left:calc(min(330px,70vw)/-2);transition:transform .7s cubic-bezier(.2,.8,.2,1),opacity .7s,filter .7s;border-radius:22px;overflow:hidden;background:#111;box-shadow:0 30px 60px -20px rgba(0,0,0,.6);color:#fff;text-align:left}
.cd img{width:100%%;height:100%%;object-fit:cover;filter:grayscale(1) contrast(1.05)}
.cd .in{position:absolute;inset:auto 0 0 0;padding:22px;background:linear-gradient(transparent,rgba(0,0,0,.85))}
.cd .in b{font:400 clamp(40px,5vw,60px)/1 var(--hf);text-transform:uppercase;display:block}.cd .in span{font:600 11px var(--mono);letter-spacing:.14em;text-transform:uppercase;opacity:.85}
.cd .btn{margin-top:14px;width:100%%;justify-content:center;background:#f4f4f4;color:#111}
.cd[data-p='0']{transform:translateX(0) translateZ(0) rotateY(0)}
.cd[data-p='-1']{transform:translateX(-78%%) translateZ(-220px) rotateY(32deg);opacity:.55;filter:brightness(.6)}
.cd[data-p='1']{transform:translateX(78%%) translateZ(-220px) rotateY(-32deg);opacity:.55;filter:brightness(.6)}
.cd[data-p='h']{transform:translateZ(-400px);opacity:0;pointer-events:none}
.cn{display:flex;gap:10px;justify-content:center;margin-top:28px}.cn button{width:52px;height:52px;border:1.5px solid var(--ink);background:transparent;color:var(--ink);font-size:20px;cursor:pointer}.cn button:hover{background:var(--ink);color:var(--bg)}
/* gallery */
.gl{padding:12vh clamp(18px,4vw,64px);max-width:1500px;margin:auto}
.gl h2{font-size:clamp(46px,9vw,140px);margin-bottom:5vh}
.gg{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));grid-auto-rows:clamp(110px,16vw,230px);gap:14px}
.gg figure{overflow:hidden;border-radius:14px;background:#222;clip-path:inset(0 0 100%% 0)}
.gg figure.in{clip-path:inset(0)}
.gg img{width:100%%;height:100%%;object-fit:cover;transform:scale(1.15);transition:transform .9s}
.gg figure:hover img{transform:scale(1.04)}
.gg figure:nth-child(1){grid-column:span 2;grid-row:span 2}.gg figure:nth-child(2){grid-column:span 2}.gg figure:nth-child(3){grid-column:span 2;grid-row:span 2}.gg figure:nth-child(4){grid-column:span 2}.gg figure:nth-child(5){grid-column:span 3}.gg figure:nth-child(6){grid-column:span 3}
/* booking */
.bk{padding:14vh clamp(18px,4vw,64px);display:grid;grid-template-columns:minmax(0,1fr) minmax(0,560px);gap:clamp(24px,6vw,96px);max-width:1400px;margin:auto;align-items:start}
.bk h2{font-size:clamp(48px,8vw,120px)}.bk .l p{margin-top:18px;color:var(--mut)}
.note{margin-top:26px;padding:14px 16px;border:1px solid var(--ln);font:500 13px/1.5 var(--bf);color:var(--mut)}
.wz{border:1px solid var(--ln);background:color-mix(in srgb,var(--ink) 6%%,transparent);padding:22px;border-radius:14px}
.stp{display:flex;gap:6px;margin-bottom:20px}.stp i{flex:1;height:3px;background:var(--ln)}.stp i.on{background:var(--ac)}
.wz h3{font-size:30px;margin-bottom:14px}
.opts{display:grid;gap:8px}
.op{all:unset;box-sizing:border-box;display:flex;justify-content:space-between;gap:12px;padding:14px 16px;border:1px solid var(--ln);cursor:pointer;font:600 14px var(--mono);text-transform:uppercase;transition:background .15s,border-color .15s}
.op:hover{border-color:var(--ac)}.op[aria-pressed=true]{background:var(--ac);color:#fff;border-color:var(--ac)}.op:focus-visible{outline:3px solid var(--ac)}
.days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px}.days .op{flex-direction:column;align-items:center;padding:10px 0;gap:2px}.days .op b{font:700 20px var(--mono)}.days .op[disabled]{opacity:.3;cursor:not-allowed}
.hrs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin-top:14px}.hrs .op{justify-content:center;padding:12px 0}
.wz label{display:block;margin-top:12px;font:600 12px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--mut)}
.wz input{width:100%%;margin-top:6px;min-height:48px;padding:0 14px;background:transparent;border:1px solid var(--ln);color:var(--ink);font:500 16px var(--bf)}
.wz input:focus-visible{border-color:var(--ac)}
.act{display:flex;justify-content:space-between;margin-top:20px}
.act .back{background:none;border:0;color:var(--mut);font:600 12px var(--mono);letter-spacing:.1em;text-transform:uppercase;cursor:pointer;min-height:48px}
.sum{display:grid;gap:8px;font:600 14px var(--mono);text-transform:uppercase}.sum div{display:flex;justify-content:space-between;gap:10px;border-bottom:1px dashed var(--ln);padding-bottom:8px}
.ok{padding:14px;border:1px solid var(--ac);margin-top:14px;font-size:14px}
/* finale */
.fin{min-height:100svh;display:grid;place-items:center;text-align:center;padding:12vh 18px;position:relative;overflow:hidden;background:radial-gradient(60%% 50%% at 50%% 55%%,color-mix(in srgb,var(--ac2) 70%%,transparent),transparent 70%%),var(--bg)}
.fin h2{font-size:clamp(46px,11.5vw,190px);text-shadow:3px 3px 0 color-mix(in srgb,var(--ink) 25%%,transparent),6px 6px 0 color-mix(in srgb,var(--ac) 55%%,transparent)}
.fin h2 span{display:block;color:var(--ac)}.fin .btn{margin-top:5vh}
footer{padding:48px clamp(18px,4vw,64px) 34px;border-top:1px solid var(--ln);display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:24px}
footer b{font:400 34px/1 var(--hf);text-transform:uppercase}footer p{color:var(--mut);font-size:14px}footer .dm{grid-column:1/-1;font:500 12px var(--mono);color:var(--mut)}
@media(max-width:860px){.hint{display:none}nav.top ul{display:none}.sv,.bk{grid-template-columns:minmax(0,1fr)}.sv .l{position:static}.paper{transform:none}.gg{grid-template-columns:repeat(2,minmax(0,1fr))}.gg figure:nth-child(n){grid-column:span 1;grid-row:span 1}.gg figure:nth-child(1){grid-column:span 2}.cd[data-p='-1']{transform:translateX(-70%%) translateZ(-220px) rotateY(32deg)}.cd[data-p='1']{transform:translateX(70%%) translateZ(-220px) rotateY(-32deg)}.stage .btn{left:clamp(18px,4vw,64px);right:auto;bottom:calc(14vh - 70px)}.cap{bottom:24vh}.days .op b{font-size:16px}}

@media(max-width:860px){.mb{grid-template-columns:1fr 1.7fr;border-top:1px solid var(--ln)}.mb a:nth-child(2){display:none}.mb a{font:400 20px var(--hf);letter-spacing:.06em}.mb a.p{background:transparent;color:var(--ac);border-left:1px solid var(--ln)}
.mm{align-items:center;text-align:center}.mm a{border-bottom:0;font-family:var(--hf);text-transform:uppercase;font-size:clamp(46px,14vw,80px)}.mm small{text-align:center}}
@media(prefers-reduced-motion:reduce){.mq div{animation:none}.cap{opacity:1;transform:none;position:static;padding:90px 18px 20px}.cap:not(:first-of-type){display:none}.gg figure{clip-path:none}.gg img{transform:none}#hero{height:auto}.stage{height:70svh}.hint,.prog{display:none}}
'''

JS = r'''
(function(){
var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
var $=function(s,r){return (r||document).querySelector(s)},$$=function(s,r){return [].slice.call((r||document).querySelectorAll(s))};
var money=function(n){return n.toLocaleString('tr-TR')+' '+C.tl};
function ready(){gsap.registerPlugin(ScrollTrigger);
 if(!reduce){var lenis=new Lenis({lerp:.09,smoothWheel:true});lenis.on('scroll',ScrollTrigger.update);gsap.ticker.add(function(t){lenis.raf(t*1000)});gsap.ticker.lagSmoothing(0);window._lenis=lenis;
  $$('a[href^="#"]').forEach(function(a){a.addEventListener('click',function(e){var t=$(a.getAttribute('href'));if(t){e.preventDefault();lenis.scrollTo(t,{offset:0})}})})}
 ScrollTrigger.create({trigger:'#hero',start:'bottom 80px',end:'max',onToggle:function(t){$('nav.top').classList.toggle('solid',t.isActive||t.progress>=1)}});
 /* hero scrub */
 var v=$('#hv'),caps=$$('.cap'),pr=$('.prog i'),hint=$('.hint');
 if(!reduce){var target=0,cur=0,dur=0;
  v.addEventListener('loadedmetadata',function(){dur=v.duration||0;v.pause()});if(v.readyState>0){dur=v.duration||0}
  v.addEventListener('error',function(){v.style.display='none'});
  var prev=0;
  ScrollTrigger.create({trigger:'#hero',start:'top top',end:'bottom bottom',scrub:false,onUpdate:function(s){target=s.progress;pr.style.width=(s.progress*100)+'%';hint.style.opacity=s.progress>.04?0:.8;
    var n=Math.min(caps.length-1,Math.floor(s.progress*caps.length*0.999));caps.forEach(function(c,i){c.classList.toggle('on',i===n&&s.progress>0.01||(i===0&&s.progress<=.01))})}});
  gsap.ticker.add(function(){cur+=(target-cur)*.12;if(dur&&Math.abs(v.currentTime-cur*dur)>.03){try{v.currentTime=cur*dur}catch(e){}}});
  caps[0].classList.add('on')}
 /* statement words */
 var sp=$('.st p');var words=sp.textContent.trim().split(/\s+/);sp.setAttribute('aria-label',sp.textContent.trim());sp.innerHTML=words.map(function(w){return '<span class="w" aria-hidden="true">'+w+'</span>'}).join(' ');
 var ws=$$('.st .w');
 if(reduce){ws.forEach(function(w){w.classList.add('on')})}else{ScrollTrigger.create({trigger:'.st',start:'top 75%',end:'bottom 45%',onUpdate:function(s){var k=Math.round(s.progress*ws.length);ws.forEach(function(w,i){w.classList.toggle('on',i<k)})}})}
 /* headings reveal */
 if(!reduce){$$('.rv').forEach(function(h){gsap.from(h,{y:60,opacity:0,duration:1,ease:'power3.out',scrollTrigger:{trigger:h,start:'top 85%'}})})
  $$('.gg figure').forEach(function(f,i){ScrollTrigger.create({trigger:f,start:'top 88%',onEnter:function(){setTimeout(function(){f.classList.add('in')},i*90)}});f.style.transition='clip-path 1s cubic-bezier(.7,0,.2,1)'})}
 else{$$('.gg figure').forEach(function(f){f.classList.add('in')})}
 /* fiş */
 var sel={},tot=$('#tot'),out=$('#out'),nm=$('#nm'),shown=0;
 function upd(){var ks=Object.keys(sel),sum=0;ks.forEach(function(k){sum+=C.svc[k][1]});
  nm.textContent=ks.length?ks.map(function(k){return C.svc[k][0]}).join(' + '):'—';tot.textContent=money(sum);
  var o={v:shown};gsap.to(o,{v:sum,duration:.5,ease:'power2.out',onUpdate:function(){out.textContent=money(Math.round(o.v));shown=o.v}});
  if(window._wz)window._wz.sync(ks.map(function(k){return C.svc[k][0]}),sum)}
 $$('.paper li button').forEach(function(b){b.addEventListener('click',function(){var i=b.dataset.i,on=b.getAttribute('aria-pressed')==='true';b.setAttribute('aria-pressed',!on);if(on)delete sel[i];else sel[i]=1;upd()})});
 /* carousel */
 var cds=$$('.cd'),pos=1;
 function place(){cds.forEach(function(c,i){var d=i-pos;c.dataset.p=d===0?'0':(d===-1?'-1':(d===1?'1':'h'))})}
 place();$('#pv').onclick=function(){pos=Math.max(0,pos-1);place()};$('#nx').onclick=function(){pos=Math.min(cds.length-1,pos+1);place()};
 cds.forEach(function(c,i){c.addEventListener('click',function(e){if(i!==pos&&!e.target.closest('a,button')){pos=i;place()}})});
 var sx=null;var car=$('.car');car.addEventListener('pointerdown',function(e){sx=e.clientX});car.addEventListener('pointerup',function(e){if(sx===null)return;var d=e.clientX-sx;if(Math.abs(d)>50){pos=Math.max(0,Math.min(cds.length-1,pos+(d<0?1:-1)));place()}sx=null});
 car.setAttribute('tabindex','0');car.addEventListener('keydown',function(e){if(e.key==='ArrowRight'){$('#nx').click()}if(e.key==='ArrowLeft'){$('#pv').click()}});
 /* wizard */
 var W={step:0,svc:[],sum:0,who:null,day:null,hr:null};var wz=$('#wz');
 var days=[];var d0=new Date();var tn=['Paz','Pzt','Sal','Çar','Per','Cum','Cmt'];for(var i=0;i<14;i++){var d=new Date(d0.getFullYear(),d0.getMonth(),d0.getDate()+i+1);days.push(d)}
 var hrs=C.hours;
 function head(){return '<div class="stp">'+[0,1,2,3,4].map(function(i){return '<i class="'+(i<=W.step?'on':'')+'"></i>'}).join('')+'</div>'}
 function draw(){var h=head(),s=W.step;
  if(s===0){h+='<h3>1 · '+C.l1+'</h3><div class="opts">'+C.svc.map(function(x,i){var on=W.svc.indexOf(x[0])>-1;return '<button type="button" class="op" aria-pressed="'+on+'" data-s="'+i+'"><span>'+x[0]+'</span><span>'+money(x[1])+'</span></button>'}).join('')+'</div>'}
  if(s===1){h+='<h3>2 · '+C.l2+'</h3><div class="opts">'+C.team.map(function(x){return '<button type="button" class="op" aria-pressed="'+(W.who===x[0])+'" data-w="'+x[0]+'"><span>'+x[0]+'</span><span>'+x[1]+'</span></button>'}).join('')+'<button type="button" class="op" aria-pressed="'+(W.who==='Fark etmez')+'" data-w="Fark etmez"><span>Fark etmez</span><span>ilk boş</span></button></div>'}
  if(s===2){h+='<h3>3 · Gün ve saat</h3><div class="days">'+days.map(function(d,i){var off=d.getDay()===0&&C.sundayClosed;return '<button type="button" class="op" '+(off?'disabled':'')+' aria-pressed="'+(W.day===i)+'" data-d="'+i+'"><span>'+tn[d.getDay()]+'</span><b>'+d.getDate()+'</b></button>'}).join('')+'</div>'+(W.day===null?'<p class="lb" style="margin-top:14px">Önce bir gün seçin</p>':'<div class="hrs">'+hrs.map(function(t,i){var off=((W.day*7+i*3)%5===0);return '<button type="button" class="op" '+(off?'disabled':'')+' aria-pressed="'+(W.hr===t)+'" data-h="'+t+'">'+t+'</button>'}).join('')+'</div>')}
  if(s===3){h+='<h3>4 · Bilgileriniz</h3><label for="wn">Ad soyad</label><input id="wn" autocomplete="name"><label for="wp">Telefon</label><input id="wp" type="tel" autocomplete="tel" inputmode="tel">'}
  if(s===4){var d=days[W.day];h+='<h3>5 · Onay</h3><div class="sum"><div><span>İşlem</span><span>'+(W.svc.join(', ')||'—')+'</span></div><div><span>'+C.unit+'</span><span>'+W.who+'</span></div><div><span>Zaman</span><span>'+d.getDate()+'.'+(d.getMonth()+1)+' · '+W.hr+'</span></div><div><span>Toplam</span><span>'+money(W.sum)+'</span></div></div>'}
  var can=(s===0&&W.svc.length)||(s===1&&W.who)||(s===2&&W.day!==null&&W.hr)||(s===3)||(s===4);
  h+='<div class="act"><button type="button" class="back" '+(s?'':'style="visibility:hidden"')+' data-b="1">Geri</button>'+(s<4?'<button type="button" class="btn" data-n="1" '+(can?'':'disabled style="opacity:.4;cursor:not-allowed"')+'>Devam</button>':'<button type="button" class="btn" data-n="1">Randevuyu onayla</button>')+'</div>';
  wz.innerHTML=h;
  $$('[data-s]',wz).forEach(function(b){b.onclick=function(){var n=C.svc[b.dataset.s][0],i=W.svc.indexOf(n);if(i>-1)W.svc.splice(i,1);else W.svc.push(n);W.sum=0;W.svc.forEach(function(x){C.svc.forEach(function(y){if(y[0]===x)W.sum+=y[1]})});draw()}});
  $$('[data-w]',wz).forEach(function(b){b.onclick=function(){W.who=b.dataset.w;draw()}});
  $$('[data-d]',wz).forEach(function(b){b.onclick=function(){W.day=+b.dataset.d;W.hr=null;draw()}});
  $$('[data-h]',wz).forEach(function(b){b.onclick=function(){W.hr=b.dataset.h;draw()}});
  var bk=$('[data-b]',wz);if(bk)bk.onclick=function(){W.step--;draw()};
  var nx=$('[data-n]',wz);if(nx)nx.onclick=function(){if(nx.disabled)return;if(W.step<4){W.step++;draw()}else{wz.innerHTML=head()+'<h3>Teşekkürler</h3><p class="ok">Randevu talebiniz alındı. Size kısa süre içinde dönüş yapacağız.</p>'}}}
 window._wz={sync:function(a,sum){W.svc=a;W.sum=sum;if(W.step===0)draw()},pick:function(n){W.who=n}};
 draw();
 $$('[data-pick]').forEach(function(b){b.addEventListener('click',function(e){W.who=b.dataset.pick;if(W.step<1)W.step=Math.max(W.step,0);draw()})});
 var go=$('#goBook');if(go)go.addEventListener('click',function(){W.step=W.svc.length?1:0;draw()});
 if(!reduce){ScrollTrigger.refresh()}
}
var n=0,pre=$('#pre'),num=$('#pn');
function done(){pre.classList.add('off');setTimeout(function(){pre.remove()},800)}
var iv=setInterval(function(){n=Math.min(100,n+Math.ceil(Math.random()*9));num.textContent=n;if(n>=100){clearInterval(iv);setTimeout(done,250)}},45);
if(window.gsap&&window.ScrollTrigger&&window.Lenis){ready()}else{pre.remove()}
addEventListener('load',function(){if(window.ScrollTrigger)ScrollTrigger.refresh()});
})();
'''

def render(s):
    f = foto.F[s['idx']]
    ph = lambda k, w=900: foto.url(f[k % len(f)], w)
    vurl, poster = foto.video(s['idx'])
    ln = 'rgba(255,255,255,.16)' if s['dark'] else 'rgba(42,24,16,.18)'
    css = CSS % dict(bg=s['bg'], ink=s['ink'], mut=s['mut'], ac=s['ac'], ac2=s['ac2'], paper=s['paper'], hf=s['hf'], mono=s['mono'], bf=s['bf'], ln=ln, hw=400)
    fams = '&'.join('family=' + x.replace(' ', '+') for x in [s['hf'], s['mono'] + ':wght@500;600;700', s['bf'] + ':wght@400;500;700'])
    cap = ''.join('<div class="cap%s"><%s>%s</%s><p>%s</p></div>' % (' on' if i == 0 else '', 'h1' if i == 0 else 'h2', H.escape(c[0]), 'h1' if i == 0 else 'h2', H.escape(c[1])) for i, c in enumerate(s['caps']))
    mq = ''.join('<span>%s</span>' % H.escape(x) for x in s['mq'])
    tl = s['tl']
    lis = ''.join('<li><button type="button" aria-pressed="false" data-i="%d"><span>%s</span><span>%s %s</span></button></li>' % (i, H.escape(a), format(p, ',').replace(',', '.'), tl) for i, (a, p, _t) in enumerate(s['svc']))
    team = ''.join('<article class="cd" data-p="1"><img src="%s" alt="%s, %s" loading="lazy" width="660" height="880"><div class="in"><span>%s</span><b>%s</b><a class="btn" href="#randevu" data-pick="%s">%s ile randevu</a></div></article>' % (ph(t[2] + 2, 700), H.escape(t[0]), H.escape(t[1]), H.escape(t[1]), H.escape(t[0]), H.escape(t[0]), H.escape(t[0])) for t in s['team'])
    gal = ''.join('<figure><img src="%s" alt="%s galeri %d" loading="lazy"></figure>' % (ph(k, 900), H.escape(s['name'].title()), i + 1) for i, k in enumerate(s['gal']))
    nav = ''.join('<li><a href="#%s">%s</a></li>' % (a, H.escape(b)) for a, b in zip(['stm', 'fis', 'ekip', 'galeri'], s['nav']))
    cfg = dict(tl=tl, svc=s['svc'], team=s['team'], unit=s['unit'], l1='İşlem seçin' if s['slug'] != 'firin' else 'Ürün seçin', l2='Usta seçin' if s['slug'] != 'firin' else 'Teslim şekli',
               hours=['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00'] if s['slug'] != 'firin' else ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00'],
               sundayClosed=False)
    if s['slug'] == 'firin': cfg['team'] = [['Gel-al', 'dükkândan', 0], ['Adrese teslim', 'şehir içi', 1]]
    if s['slug'] == 'motor': cfg['hours'] = ['08:30', '09:30', '10:30', '11:30', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '', ''][:10]
    c = json.dumps(cfg, ensure_ascii=False)
    return '''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%(title)s</title>
<meta name="description" content="%(name)s için sinematik, kaydırmayla ilerleyen site. Hizmet fişi, ekip ve adım adım randevu penceresi."><meta name="robots" content="noindex">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?%(fams)s&display=swap">
<style>%(mcss)s</style><style>%(css)s</style></head><body>
<div id="pre" role="status"><div><b>%(name)s</b><i><span id="pn">0</span>%%</i></div></div>
<nav class="top"><a class="lg" href="#" aria-label="%(name)s ana sayfa">%(name)s<small>%(sub)s</small></a><ul>%(nav)s</ul><a class="btn" href="#randevu">Randevu</a></nav>
<main><section id="hero" aria-label="Açılış"><div class="stage"><img class="poster" src="%(poster)s" alt="" fetchpriority="high"><video id="hv" muted playsinline preload="auto" poster="%(poster)s" src="%(vurl)s" aria-hidden="true"></video>%(cap)s<a class="btn" href="#fis">%(hcta)s</a><div class="hint">KAYDIR</div><div class="prog"><i></i></div></div></section>
<div class="mq" aria-hidden="true"><div>%(mq)s%(mq)s</div></div>
<section class="st" id="stm"><p>%(stmt)s</p></section>
<section class="sv" id="fis"><div class="l"><h2 class="rv">%(h1)s <em>%(h2)s</em></h2><p>%(svcp)s</p><div class="sel" aria-live="polite"><span class="lb">Seçilen</span><b id="nm">—</b><output id="out">0 %(tl)s</output><a class="btn" href="#randevu" id="goBook">Randevuya geç</a></div></div>
<div class="paper" role="group" aria-label="%(pt)s"><h3>%(pt)s</h3><i>%(ps)s</i><ul>%(lis)s</ul><div class="tot"><span>TOPLAM</span><span id="tot">0 %(tl)s</span></div><div class="bar" aria-hidden="true"></div><small>@%(slug)s</small></div></section>
<section class="tm" id="ekip"><h2 class="rv">%(teamh)s</h2><div class="car" aria-label="Ekip: ok tuşlarıyla gezin">%(team)s</div><div class="cn"><button type="button" id="pv" aria-label="Önceki">←</button><button type="button" id="nx" aria-label="Sonraki">→</button></div></section>
<section class="gl" id="galeri"><h2 class="rv">%(galh)s</h2><div class="gg">%(gal)s</div></section>
<section class="bk" id="randevu"><div class="l"><h2 class="rv">%(bh1)s %(bh2)s</h2><p>%(bp)s</p></div><div class="wz" id="wz" aria-live="polite"></div></section>
<section class="fin"><div><h2 class="rv">%(f1)s <span>%(f2)s</span></h2><a class="btn" href="#randevu">%(fcta)s</a></div></section></main>
<footer><div><b>%(name)s</b><p>%(sub)s</p></div><div class="cl"><p class="lb">Menü</p><a href="#stm">Kulüp</a><a href="#fis">Hizmetler</a><a href="#ekip">Ustalar</a><a href="#galeri">Galeri</a></div><div class="cl"><p class="lb">İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a><p>%(addr)s</p></div><div><p class="lb">Saatler</p><p>%(hrs)s</p></div><p class="cr">© 2026 %(name)s</p></footer>
<noscript><style>#pre{display:none}.st .w{opacity:1}.gg figure{clip-path:none}.gg img{transform:none}</style></noscript>
<script>const C=%(c)s;</script><script src="../lib/gsap.min.js"></script><script src="../lib/ScrollTrigger.min.js"></script><script src="../lib/lenis.min.js"></script><script>%(js)s</script><script>window.MOB=%(mob)s;%(mjs)s</script></body></html>''' % dict(
        title=s['title'], name=s['name'], sub=s['sub'], fams=fams, css=css, nav=nav, poster=poster, vurl=vurl, cap=cap, hcta=H.escape(s['hero_cta']), mq=mq, stmt=H.escape(s['stmt']),
        h1=H.escape(s['svc_h'][0]), h2=H.escape(s['svc_h'][1]), svcp=H.escape(s['svc_p']), tl=tl, pt=s['paper_t'], ps=s['paper_s'], lis=lis, slug=s['slug'], teamh=s['team_h'], team=team, galh=s['gal_h'], gal=gal,
        bh1=H.escape(s['book_h'][0]), bh2=H.escape(s['book_h'][1]), bp=H.escape(s['book_p']), f1=H.escape(s['fin'][0]), f2=H.escape(s['fin'][1]), fcta=H.escape(s['fin_cta']), addr=s['addr'], hrs=s['hrs'], c=c, js=JS, mcss=common.MOB_CSS, mjs=common.MOB_JS, mob=json.dumps(dict(cta=[s['hero_cta'],'#randevu'], addr=s['addr']), ensure_ascii=False))

if __name__ == '__main__':
    for s in SITES:
        d = os.path.join(R, s['slug']); os.makedirs(d, exist_ok=True)
        open(d + '/index.html', 'w', encoding='utf-8').write(render(s))
    idx = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Demo siteler</title><body style="font:18px system-ui;background:#0b0908;color:#f4efe8;padding:8vw"><h1 style="font-size:40px">Demo siteler</h1><ul style="line-height:2.2">' + ''.join('<li><a style="color:#e0572a" href="%s/index.html">%s</a></li>' % (s['slug'], s['name'].title()) for s in SITES) + '</ul>'
    open(R + '/index.html', 'w', encoding='utf-8').write(idx)
    print('ok')
