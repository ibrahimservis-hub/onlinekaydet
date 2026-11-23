# -*- coding: utf-8 -*-
"""Pati Vet: veteriner kliniği. Sıcak turuncu, yuvarlak, samimi; hayvan türüne göre muayene seçici."""
import html as H, json
from common import *
IDX = 9
f = foto.F[IDX]
ph = lambda k, w=900: foto.url(f[k % len(f)], w)
PETS = {
 'Kedi': ('Kedi için ilk muayene', [('Genel muayene', 450), ('Karma aşı', 380), ('İç-dış parazit', 220)], 'Çoğu kedi evde sakin, klinikte stresli olur. Sessiz bekleme odamızı kedilere ayırdık.'),
 'Köpek': ('Köpek için yıllık bakım', [('Genel muayene', 450), ('Karma aşı + kuduz', 520), ('Kan tahlili paketi', 780)], 'Boyuna göre doz ve aşı takvimi çıkarılır, çip takılması aynı gün yapılır.'),
 'Kuş': ('Kuş için sağlık kontrolü', [('Genel muayene', 400), ('Dışkı analizi', 260), ('Tırnak ve gaga bakımı', 180)], 'Egzotik hayvanlar için ayrı muayene saati vardır, randevu şarttır.'),
 'Tavşan': ('Tavşan için kontrol', [('Genel muayene', 400), ('Diş kontrolü', 240), ('Parazit tedavisi', 200)], 'Tavşanlarda diş ve sindirim sorunları sık görülür, erken bakılması önemlidir.'),
}
SERV = [('Muayene', 0), ('Aşı takvimi', 1), ('Ameliyat', 2), ('Diş bakımı', 3), ('Tıraş ve bakım', 4), ('Acil', 5)]
TEAM = [('Dr. Elif Aksoy', 'Baş veteriner', 6), ('Dr. Kerem Yurt', 'Cerrahi', 7), ('Seda Ay', 'Hasta bakım', 8)]
CSS = '''
:root{--bg:#fff6ec;--ink:#2b1408;--mut:#7a5a45;--ac:#e8541c;--ac2:#8a2a08;--card:#fff;--ln:rgba(43,20,8,.14);--hf:'Fredoka',system-ui,sans-serif;--mono:'Nunito',sans-serif;--bf:'Nunito',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 18px/1.6 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:600;line-height:1.02;letter-spacing:-.01em;overflow-wrap:break-word;min-width:0}
.btn{border-radius:40px;font-family:var(--bf);text-transform:none;letter-spacing:0;font-size:16px;font-weight:800}
.btn.w{background:#fff;color:var(--ac2)}.btn.o{background:transparent;border:2px solid currentColor;color:inherit}
nav.top{position:fixed;inset:14px 14px auto 14px;z-index:50;display:flex;align-items:center;gap:18px;padding:10px 12px 10px 24px;border-radius:50px;color:#fff;transition:background .3s,color .3s,box-shadow .3s}
nav.top.solid{background:rgba(255,246,236,.92);color:var(--ink);box-shadow:0 10px 30px -18px rgba(43,20,8,.5);backdrop-filter:blur(10px)}
.lg{font:600 26px var(--hf);text-decoration:none;margin-right:auto}.lg b{color:#ffd9c2}nav.top.solid .lg b{color:var(--ac)}
nav.top ul{display:flex;gap:24px;list-style:none;padding:0}nav.top li a{font:800 15px var(--bf);text-decoration:none}nav.top li a:hover{text-decoration:underline;text-underline-offset:6px}
.hero{min-height:100svh;display:grid;grid-template-columns:1fr 1fr;align-items:center;gap:2vw;padding:130px clamp(24px,5vw,80px) 170px;background:linear-gradient(125deg,#5f1a04,#b8420c 55%,#ee6f1d);color:#fff;border-radius:0 0 56px 56px;position:relative}
.hero h1{font-size:clamp(46px,6.6vw,104px)}.hero h1 em{font-style:normal;color:#ffd0b0}.hero p{max-width:30em;margin:22px 0 30px;color:#ffe6d6;font-size:19px}.hero .bt{display:flex;gap:12px;flex-wrap:wrap}
.hp{position:relative;aspect-ratio:1/1.05;max-height:78vh;justify-self:end;width:min(100%,640px)}
.hp img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border-radius:46% 54% 42% 58%/52% 44% 56% 48%;animation:mo 12s ease-in-out infinite alternate;box-shadow:0 40px 80px -30px rgba(0,0,0,.6)}
@keyframes mo{to{border-radius:58% 42% 52% 48%/44% 56% 44% 56%}}
.hp .tag{position:absolute;background:#fff;color:var(--ink);border-radius:20px;padding:12px 16px;font:800 14px/1.2 var(--bf);box-shadow:0 14px 34px -14px rgba(0,0,0,.5)}.hp .t1{left:-6%;bottom:14%}.hp .t2{right:2%;top:6%}.hp .tag small{display:block;color:var(--mut);font-weight:600}
.strip{position:absolute;left:50%;bottom:34px;transform:translateX(-50%);display:flex;background:#fff;color:var(--ink);border-radius:50px;box-shadow:0 20px 50px -24px rgba(43,20,8,.6);width:min(940px,92vw)}
.strip div{flex:1;padding:18px 24px;font:800 16px/1.25 var(--bf)}.strip div+div{border-left:1px solid var(--ln)}.strip small{display:block;color:var(--mut);font-weight:600;font-size:14px}
section.s{padding:min(16vh,150px) clamp(20px,5vw,80px) 6vh;max-width:1380px;margin:auto}section.s:first-of-type{padding-top:min(14vh,120px)}
.hd{display:flex;justify-content:space-between;align-items:end;gap:20px;flex-wrap:wrap;margin-bottom:5vh}.hd h2{font-size:clamp(38px,5.4vw,78px)}.hd p{max-width:28em;color:var(--mut)}
.pk{display:grid;grid-template-columns:.9fr 1.1fr;gap:28px}.pt{display:flex;gap:10px;flex-wrap:wrap;grid-column:1/-1}
.pt button{min-height:56px;padding:0 28px;border-radius:40px;border:2px solid var(--ink);background:transparent;color:var(--ink);font:700 20px var(--hf);cursor:pointer;transition:transform .2s,background .2s}
.pt button:hover{transform:translateY(-2px)}.pt button[aria-pressed=true]{background:var(--ac);border-color:var(--ac);color:#fff}
.pc{background:var(--card);border-radius:32px;padding:34px;border:1px solid var(--ln)}.pc h3{font-size:34px}.pc p{color:var(--mut);margin-top:14px}
.pi{list-style:none;padding:0;margin:24px 0}.pi li{display:flex;justify-content:space-between;gap:12px;padding:15px 0;border-bottom:1px dashed var(--ln);font-weight:700}.pi li span{font-family:var(--hf);font-size:21px;color:var(--ac2)}
.pc .tot{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.pc .tot b{font:600 40px var(--hf)}.pc .tot small{display:block;color:var(--mut);font-weight:600;font-size:14px}
.ph{border-radius:32px;overflow:hidden;min-height:340px;position:relative}.ph img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.sv{display:flex;gap:18px;overflow-x:auto;scroll-snap-type:x mandatory;padding:0 clamp(20px,5vw,80px) 14px;margin:0 calc(-1*clamp(20px,5vw,80px));scrollbar-width:none}.sv::-webkit-scrollbar{display:none}
.sv a{flex:0 0 min(300px,72vw);scroll-snap-align:start;text-decoration:none;position:relative;border-radius:30px;overflow:hidden;aspect-ratio:3/4;color:#fff;transition:transform .3s}.sv a:hover{transform:translateY(-6px)}
.sv img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .6s}.sv a:hover img{transform:scale(1.05)}.sv a:after{content:'';position:absolute;inset:0;background:linear-gradient(transparent 45%,rgba(60,20,5,.82))}
.sv b{position:absolute;z-index:2;left:22px;bottom:20px;font:600 28px var(--hf)}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;counter-reset:s}.steps div{background:var(--card);border-radius:28px;padding:30px;border:1px solid var(--ln);position:relative;counter-increment:s}
.steps div:before{content:counter(s);display:grid;place-items:center;width:52px;height:52px;border-radius:50%;background:var(--ac);color:#fff;font:600 24px var(--hf);margin-bottom:18px}.steps h3{font-size:28px;margin-bottom:8px}.steps p{color:var(--mut)}
.tm{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.tm figure{margin:0}.tm .im{aspect-ratio:4/5;border-radius:30px;overflow:hidden;position:relative}.tm img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .6s}.tm figure:hover img{transform:scale(1.04)}
.tm figcaption{padding:14px 6px;font:600 24px var(--hf)}.tm figcaption small{display:block;font:600 16px var(--bf);color:var(--mut)}
.ap{display:grid;grid-template-columns:1fr 1fr;gap:28px;background:var(--ac2);color:#fff;border-radius:44px;padding:clamp(28px,5vw,64px);margin:6vh clamp(14px,3vw,40px)}
.ap h2{font-size:clamp(40px,5.6vw,80px)}.ap p{color:#ffd9c2;margin-top:16px;max-width:24em}
.fm{display:grid;gap:14px}.fm label{display:grid;gap:6px;font-weight:800;font-size:15px}.fm input,.fm select{min-height:54px;border-radius:18px;border:0;padding:0 18px;font:600 17px var(--bf);background:#fff;color:var(--ink)}
.fm .ok{display:none;background:#fff;color:var(--ink);border-radius:18px;padding:16px 18px;font-weight:800}.fm .ok.on{display:block}
footer{background:var(--ac);color:#fff;border-radius:56px 56px 0 0;padding:70px clamp(24px,5vw,80px) 30px;margin-top:6vh;display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px;overflow:clip}
footer b{font:600 26px var(--hf)}footer p{color:#ffe6d6;margin-top:8px}footer .cl a{color:#ffe6d6}footer .cr{color:#ffd0b0;border-color:rgba(255,255,255,.3)}
footer .big{grid-column:1/-1;font:600 clamp(70px,22vw,330px)/.8 var(--hf);letter-spacing:-.03em;color:#fff;opacity:.95;margin:20px 0 -.05em;white-space:nowrap;text-align:center}
.rv{will-change:transform}
@media(max-width:860px){
.hero{grid-template-columns:1fr;display:block;padding:100px 20px 40px;border-radius:0 0 36px 36px}.hp{margin:0 auto 24px;max-height:42vh;aspect-ratio:1/.8;width:100%}.hp .t1{left:2%;bottom:2%}.hp .t2{display:none}
.strip{position:static;transform:none;width:100%;margin-top:26px;flex-direction:column;border-radius:30px}.strip div+div{border-left:0;border-top:1px solid var(--ln)}.strip div{padding:11px 20px}section.s:first-of-type{padding-top:150px}
.pk,.steps,.tm,.ap,footer{grid-template-columns:1fr}.ph{min-height:240px}.pt button{min-height:50px;padding:0 20px;font-size:18px}
nav.top ul,nav.top>.btn{display:none}nav.top{padding:8px 8px 8px 20px;inset:10px 10px auto 10px}nav.top .hm{border-radius:50%;margin-left:auto}
.mb{left:12px;right:12px;bottom:12px;border:0;border-radius:40px;background:var(--ink);padding:5px;grid-template-columns:1fr 1fr 1.6fr;gap:4px}.mb a{min-height:50px;border-radius:30px;color:#fff;font:800 15px var(--bf);letter-spacing:0;text-transform:none}.mb a+a{border:0}.mb a.p{background:var(--ac)}
.mm{inset:auto 0 0 0;top:20vh;border-radius:36px 36px 0 0;background:var(--ac);color:#fff;padding:36px 26px 110px;transform:translateY(105%);gap:2px;justify-content:flex-start;--ln:rgba(255,255,255,.25);--ac:#fff;--mut:#ffd9c2}.mm a{font:600 40px/1.15 var(--hf);color:#fff;border-bottom:0;padding:8px 0}.mm small{color:#ffd9c2;font:700 14px var(--bf);text-transform:none;letter-spacing:0}
footer{border-radius:36px 36px 0 0;padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce;
 if(!rd){var tl=gsap.timeline({defaults:{ease:'back.out(1.5)'}});tl.from('.hero h1',{y:60,opacity:0,duration:.9}).from('.hero p,.hero .bt',{y:30,opacity:0,duration:.7,stagger:.12},'-=.5').from('.hp img',{scale:.8,opacity:0,duration:1.1,ease:'power3.out'},'-=1').from('.hp .tag',{scale:0,duration:.6,stagger:.15},'-=.4').from('.strip',{y:60,opacity:0,duration:.8,ease:'power3.out'},'-=.5');
  gsap.to('.hp img',{yPercent:6,ease:'none',scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom top',scrub:true}});
  gsap.utils.toArray('.steps div,.tm figure,.sv a').forEach(function(e,i){gsap.from(e,{y:50,opacity:0,duration:.8,delay:(i%3)*.08,ease:'back.out(1.3)',scrollTrigger:{trigger:e,start:'top 92%'}})});
  gsap.from('footer .big',{yPercent:40,opacity:0,duration:1.1,ease:'power3.out',scrollTrigger:{trigger:'footer',start:'top 80%'}})}
 var cur='Kedi';function show(k){cur=k;var d=C.pets[k];$('#pt').textContent=d[0];$('#pn2').textContent=d[2];var tot=0;$('#pl').innerHTML=d[1].map(function(x){tot+=x[1];return '<li>'+x[0]+'<span>'+money(x[1])+'</span></li>'}).join('');$('#ptot').textContent=money(tot);$$('.pt button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.k===k)})}
 $$('.pt button').forEach(function(b){b.onclick=function(){show(b.dataset.k)}});show('Kedi');
 $('#fm').onsubmit=function(e){e.preventDefault();var n=$('#fn').value||'Dostumuz';var o=$('#fo');o.textContent='Teşekkürler '+n+'. '+$('#fp').value+' için '+$('#fd').value+' randevu isteğiniz alındı. Sizi arayıp saati kesinleştireceğiz.';o.classList.add('on')};
});
'''
def render():
    pets = ''.join('<button type="button" data-k="%s" aria-pressed="false">%s</button>' % (k, k) for k in PETS)
    sv = ''.join('<a href="#randevu"><img src="%s" alt="%s" loading="lazy"><b>%s</b></a>' % (ph(k + 1, 700), n, n) for n, k in SERV)
    tm = ''.join('<figure><div class="im"><img src="%s" alt="%s" loading="lazy"></div><figcaption>%s<small>%s</small></figcaption></figure>' % (ph(k, 700), n, n, r) for n, r, k in TEAM)
    body = f'''<div id="pre" role="status"><div><b>PATİ VET</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">Pati<b>.</b>Vet</a><ul><li><a href="#muayene">Muayene</a></li><li><a href="#hizmet">Hizmetler</a></li><li><a href="#ekip">Ekip</a></li><li><a href="#randevu">Randevu</a></li></ul><a class="btn" href="#randevu">Randevu al</a></nav>
<main><header class="hero" id="hero"><div><h1>Her patinin <em>kendi doktoru</em> var.</h1><p>Kedi, köpek, kuş ve tavşanlar için kontrol, aşı ve cerrahi. Önce sizi dinler, sonra muayene ederiz.</p><div class="bt"><a class="btn w" href="#muayene">Neye ihtiyacın var?</a><a class="btn o" href="#randevu">Randevu al</a></div></div>
<div class="hp"><img src="{ph(0, 1100)}" alt="Veteriner hekim sevimli bir köpeği muayene ediyor" fetchpriority="high"><div class="tag t1">Acil durumda arayın<small>Telefonla yönlendiririz</small></div><div class="tag t2">Sessiz kedi odası<small>Köpeklerden ayrı</small></div></div>
<div class="strip"><div>Aşı ve kontrol<small>Takvim sizin yerinize tutulur</small></div><div>Yazılı fiyat<small>İşlemden önce söylenir</small></div><div>Taburcu notu<small>Evde bakım için yazılı</small></div></div></header>
<section class="s" id="muayene"><div class="hd"><h2 class="rv">Hangi dostumuz geldi?</h2><p>Türünü seç, ilk ziyarette neler yapıldığını ve örnek fiyatları gör.</p></div><div class="pk"><div class="pt" role="group" aria-label="Hayvan türü">{pets}</div>
<div class="pc"><h3 id="pt"></h3><p id="pn2"></p><ul class="pi" id="pl"></ul><div class="tot"><div><small>Örnek toplam</small><b id="ptot">0 ₺</b></div><a class="btn" href="#randevu">Bu paketle randevu al</a></div></div><div class="ph"><img src="{ph(1, 1000)}" alt="Klinikte bir kedi muayenesi" loading="lazy"></div></div></section>
<section class="s" id="hizmet"><div class="hd"><h2 class="rv">Neler yapıyoruz?</h2><p>Kaydırın, dokunun, randevuya geçin.</p></div><div class="sv">{sv}</div></section>
<section class="s"><div class="hd"><h2 class="rv">İlk ziyaret nasıl geçer?</h2></div><div class="steps"><div><h3>Tanışırız</h3><p>Adını, yaşını, huyunu ve şikâyetini sorarız. Aceleye getirmeyiz.</p></div><div><h3>Muayene ederiz</h3><p>Gerekirse tahlil ve görüntüleme önerir, fiyatı önceden söyleriz.</p></div><div><h3>Evde devam</h3><p>İlaç, beslenme ve kontrol tarihini yazılı veririz.</p></div></div></section>
<section class="s" id="ekip"><div class="hd"><h2 class="rv">Ekibimiz</h2><p>Her hasta için aynı hekim takip eder.</p></div><div class="tm">{tm}</div></section>
<section class="ap" id="randevu"><div><h2 class="rv">Randevu isteği bırakın.</h2><p>Formu doldurun, aynı gün içinde sizi arayıp saati netleştirelim.</p></div>
<form class="fm" id="fm"><label>Adınız<input id="fn" required autocomplete="name"></label><label>Hayvan türü<select id="fp"><option>Kedi</option><option>Köpek</option><option>Kuş</option><option>Tavşan</option></select></label><label>Tercih ettiğiniz gün<select id="fd"><option>bu hafta</option><option>hafta sonu</option><option>gelecek hafta</option></select></label><button class="btn w" type="submit">Randevu iste</button><p class="ok" id="fo" aria-live="polite"></p></form></section></main>
<footer><div><b>Pati Vet</b><p>Veteriner kliniği · Örnek Mah. Ankara</p></div><div class="cl"><p>Menü</p><a href="#muayene">Muayene</a><a href="#hizmet">Hizmetler</a><a href="#ekip">Ekip</a><a href="#randevu">Randevu</a></div><div class="cl"><p>İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div><div class="big" aria-hidden="true">PATİ VET</div><p class="cr">© Pati Vet · Örnek tasarım</p></footer>'''
    c = json.dumps(dict(pets={k: [v[0], v[1], v[2]] for k, v in PETS.items()}), ensure_ascii=False)
    return page('Pati Vet Veteriner Kliniği', 'Kedi, köpek, kuş ve tavşan için muayene, aşı ve cerrahi.', ['Fredoka:wght@500;600;700', 'Nunito:wght@400;600;700;800'], BASE_CSS + CSS, body, JS, c, dict(cta=['Randevu al', '#randevu'], addr='Örnek Mah. · Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/pati', exist_ok=True); open(R + '/pati/index.html', 'w', encoding='utf-8').write(render()); print('pati ok')
