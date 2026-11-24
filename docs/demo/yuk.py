# -*- coding: utf-8 -*-
"""Yük Nakliyat: evden eve nakliyat. Lacivert + turuncu, Sora; kaydıkça dolan rota çizgisi, oda/kat/asansör ile fiyat tahmini."""
import json
from common import *
IDX = 5
f = foto.F[IDX]
ph = lambda k, w=900: foto.url(f[k % len(f)], w)
ODA = {'1+0': 4500, '1+1': 6000, '2+1': 8500, '3+1': 11500, '4+1': 15000}
STEP = [('Keşif', 'Ücretsiz keşif yapılır, eşya listesi çıkarılır.'), ('Paketleme', 'Eşyalar koli, battaniye ve streç ile korunur.'), ('Yükleme', 'Eğitimli ekip, asansör ve ip sistemiyle taşır.'), ('Teslimat', 'Eşyalar yeni evde yerleştirilir, mobilya kurulur.')]
CSS = '''
:root{--bg:#f5f3ee;--ink:#1b2a4a;--mut:#5d6881;--ac:#ff8a00;--ac2:#1b2a4a;--ln:rgba(27,42,74,.16);--hf:'Sora',system-ui,sans-serif;--mono:'Figtree',sans-serif;--bf:'Figtree',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:500 18px/1.6 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:800;letter-spacing:-.045em;line-height:.98;overflow-wrap:break-word;min-width:0}
.btn{border-radius:12px;font-family:var(--bf);font-weight:800;font-size:16px;text-transform:none;letter-spacing:0}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;align-items:center;gap:26px;padding:16px clamp(20px,4vw,56px);color:#fff;transition:background .3s}nav.top.solid{background:var(--ink)}
.lg{font:800 24px var(--hf);letter-spacing:-.05em;text-decoration:none;margin-right:auto}.lg b{color:var(--ac)}
nav.top ul{display:flex;gap:26px;list-style:none;padding:0}nav.top li a{font:700 15px var(--bf);text-decoration:none}nav.top li a:hover{color:var(--ac)}nav.top .btn{background:var(--ac);color:var(--ink);padding:12px 22px}
.hero{height:100svh;min-height:640px;position:relative;color:#fff;display:flex;align-items:center;padding:80px clamp(20px,4vw,56px) 0;overflow:clip;background:var(--ink)}.hero>img{position:absolute;inset:-6% 0 -6% auto;width:46%;height:112%;object-fit:cover;clip-path:polygon(14% 0,100% 0,100% 100%,0 100%)}.hero:after{content:'';position:absolute;left:0;bottom:0;width:100%;height:12px;background:repeating-linear-gradient(90deg,var(--ac) 0 40px,transparent 40px 80px)}
.hero .c{position:relative;z-index:2;max-width:56%}.hero h1{font-size:clamp(50px,7vw,124px)}.hero h1 em{font-style:normal;color:var(--ac)}.hero p{max-width:26em;margin:20px 0 28px;font-size:20px;color:#e3e8f4}.hero .bt{display:flex;gap:12px;flex-wrap:wrap}.hero .btn.p{background:var(--ac);color:var(--ink);padding:18px 32px}.hero .btn.g{border:2px solid #fff;color:#fff;background:transparent;padding:16px 28px}
section.s{padding:min(14vh,130px) clamp(20px,4vw,56px) 4vh;max-width:1380px;margin:auto}
.hd h2{font-size:clamp(42px,6.4vw,104px);margin-bottom:5vh}.hd h2 em{font-style:normal;color:var(--ac)}
.rt{position:relative;padding-left:90px}.rt .ln{position:absolute;left:34px;top:10px;bottom:10px;width:6px;background:var(--ln);border-radius:4px}.rt .ln i{display:block;width:100%;height:0;background:var(--ac);border-radius:4px}
.rt .tk{position:absolute;left:-76px;width:46px;height:46px;border-radius:50%;background:var(--ac);display:grid;place-items:center;top:0;z-index:2;font:800 18px var(--hf);color:var(--ink);box-shadow:0 0 0 8px var(--bg)}
.rt .st{position:relative;padding:0 0 clamp(40px,8vh,90px);display:grid;grid-template-columns:1fr 1fr;gap:30px;align-items:center;min-height:30vh}.rt .st:last-child{padding-bottom:0}.rt .st span{font:800 15px var(--bf);color:var(--ac);display:block;margin-bottom:6px}.rt .st h3{font-size:clamp(34px,4.4vw,66px)}.rt .st p{color:var(--mut);margin-top:10px;max-width:24em}.rt .st .im{aspect-ratio:16/10;border-radius:22px;overflow:hidden;position:relative}.rt .st img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .8s}.rt .st .im:hover img{transform:scale(1.04)}
.es{margin-top:10vh;background:var(--ink);color:#fff;border-radius:32px;display:grid;grid-template-columns:1.1fr .9fr}.es .fm{padding:clamp(26px,4vw,56px);display:grid;gap:24px}.es h3{font-size:clamp(34px,4vw,58px)}.es .lb{font:700 15px var(--bf);color:#a9b4cc;margin-bottom:10px}.es .op{display:flex;gap:8px;flex-wrap:wrap}.es .op button{min-height:48px;min-width:56px;padding:0 18px;border:2px solid rgba(255,255,255,.25);border-radius:12px;background:transparent;color:#fff;font:700 16px var(--bf);cursor:pointer;transition:all .2s}.es .op button:hover{border-color:var(--ac)}.es .op button[aria-pressed=true]{background:var(--ac);border-color:var(--ac);color:var(--ink)}
.es .rs{background:var(--ac);color:var(--ink);border-radius:0 32px 32px 0;padding:clamp(26px,4vw,56px);display:flex;flex-direction:column;justify-content:center;gap:10px}.es .rs b{font:800 clamp(52px,6vw,92px)/1 var(--hf);letter-spacing:-.05em}.es .rs small{font-weight:800}.es .rs p{font-weight:600}.es .rs .btn{background:var(--ink);color:#fff;padding:16px 26px;align-self:flex-start;margin-top:8px}
.cl{padding:min(12vh,110px) clamp(20px,4vw,56px)}.cl>div{max-width:1380px;margin:auto;display:grid;grid-template-columns:1fr 1fr;gap:5vw;align-items:end}.cl h2{font-size:clamp(46px,7vw,112px)}.cl form{display:grid;gap:10px}.cl input,.cl select{min-height:56px;border:2px solid var(--ink);background:transparent;border-radius:12px;padding:0 18px;font:600 17px var(--bf);color:var(--ink)}.cl .btn{background:var(--ink);color:#fff;min-height:58px;border:0;cursor:pointer}.cl .ok{display:none;background:var(--ac);padding:14px 18px;border-radius:12px;font-weight:800}.cl .ok.on{display:block}
footer{background:var(--ink);color:#fff;padding:70px clamp(20px,4vw,56px) 30px;display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px}footer b{font:800 28px var(--hf);letter-spacing:-.05em}footer b i{color:var(--ac);font-style:normal}footer a{display:block;color:#fff;text-decoration:none;padding:3px 0}footer a:hover{color:var(--ac)}footer p{color:#a9b4cc}
@media(max-width:860px){
nav.top ul,nav.top>.btn{display:none}nav.top{padding:12px 16px}nav.top .hm{margin-left:auto;border-radius:12px}
.hero{align-items:flex-end;padding-bottom:12vh}.hero>img{inset:-6% 0;width:100%;opacity:.4;clip-path:none}.hero .c{max-width:100%}.hero h1{font-size:clamp(48px,15vw,90px)}.rt{padding-left:60px}.rt .ln{left:20px}.rt .tk{left:-58px;width:40px;height:40px}.rt .st{grid-template-columns:1fr;gap:16px}.es,.cl>div,footer{grid-template-columns:1fr}.es .rs{border-radius:0 0 32px 32px}
.mb{left:0;right:0;bottom:0;background:var(--ink);border:0;border-top:3px solid var(--ac);border-radius:0;grid-template-columns:1fr 1fr 1.4fr;padding:0 0 max(0px,env(safe-area-inset-bottom))}.mb a{min-height:58px;border-radius:0;color:#fff;font:800 15px var(--bf);letter-spacing:0;text-transform:none}.mb a+a{border-left:1px solid rgba(255,255,255,.18)}.mb a.p{background:var(--ac);color:var(--ink)}
.mm{background:var(--ink);inset:0;padding:90px 24px 110px;--ln:rgba(255,255,255,.18);--ac:#ff8a00;--mut:#a9b4cc}.mm a{font:800 clamp(40px,13vw,66px)/1.1 var(--hf);letter-spacing:-.05em;color:#fff;border-bottom:1px solid var(--ln);padding:12px 0}.mm a:hover{color:var(--ac)}.mm small{color:var(--mut);font:700 14px var(--bf);text-transform:none;letter-spacing:0}
footer{padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce;
 if(!rd){gsap.from('.hero h1',{y:60,opacity:0,duration:1.1,ease:'power4.out'});gsap.from('.hero .c>*:not(h1)',{y:30,opacity:0,stagger:.12,duration:.8,delay:.4});gsap.to('.hero>img',{yPercent:10,ease:'none',scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom top',scrub:true}});
  gsap.to('.rt .ln i',{height:'100%',ease:'none',scrollTrigger:{trigger:'.rt',start:'top 60%',end:'bottom 70%',scrub:true}});
  gsap.utils.toArray('.rt .st').forEach(function(e,i){gsap.from(e.children,{y:50,opacity:0,duration:.9,stagger:.12,scrollTrigger:{trigger:e,start:'top 80%'}})});
  gsap.utils.toArray('.hd h2,.es,.cl h2').forEach(function(e){gsap.from(e,{y:50,opacity:0,duration:.8,scrollTrigger:{trigger:e,start:'top 90%'}})})}
 var o='2+1',k=3,a='Asansör var';function up(){var p=C.o[o]+Math.max(0,k-1)*(a=='Asansör var'?150:450)+(a=='Asansör var'?0:600);p=Math.round(p/50)*50;$('#pt').textContent=money(p)+' - '+money(Math.round(p*1.25/50)*50);$('#pn2').textContent=o+', '+k+'. kat, '+a.toLowerCase()}
 function mk(id,arr,def,cb){$(id).innerHTML=arr.map(function(x){return '<button type="button" aria-pressed="'+(String(x)==String(def))+'">'+x+'</button>'}).join('');$$(id+' button').forEach(function(b){b.onclick=function(){$$(id+' button').forEach(function(y){y.setAttribute('aria-pressed',y===b)});cb(b.textContent);up()}})}
 mk('#od',Object.keys(C.o),o,function(v){o=v});mk('#kt',[1,2,3,4,5,6],k,function(v){k=+v});mk('#as',['Asansör var','Asansör yok'],a,function(v){a=v});up();
 $('#fm').onsubmit=function(e){e.preventDefault();var o2=$('#fo');o2.textContent='Teşekkürler '+$('#fn').value+'. '+$('#fd').value+' için ücretsiz keşif randevusu ayarlayıp seni arayacağız.';o2.classList.add('on')};
});
'''
def render():
    st = ''.join('<div class="st"><div><span>Adım %d</span><h3>%s</h3><p>%s</p></div><div class="im"><img src="%s" alt="%s" loading="lazy"></div><i class="tk" style="top:0">%d</i></div>' % (i + 1, a, b, ph(i + 1, 900), a, i + 1) for i, (a, b) in enumerate(STEP))
    body = f'''<div id="pre" role="status"><div><b>YÜK</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">Yük<b>.</b></a><ul><li><a href="#surec">Süreç</a></li><li><a href="#fiyat">Fiyat tahmini</a></li><li><a href="#kesif">Keşif</a></li></ul><a class="btn" href="#kesif">Ücretsiz keşif</a></nav>
<main><header class="hero" id="hero"><img src="{ph(0, 1800)}" alt="Nakliye aracına eşya yüklenirken" fetchpriority="high"><div class="c"><h1>Eşyan <em>sağ salim</em> yeni evinde.</h1><p>Evden eve nakliyat. Ücretsiz keşif, sigortalı taşıma, mobilya söküm ve montaj dahil.</p><div class="bt"><a class="btn p" href="#fiyat">Fiyatı tahmin et</a><a class="btn g" href="#kesif">Ücretsiz keşif</a></div></div></header>
<section class="s" id="surec"><div class="hd"><h2>Dört adımda <em>taşınırsın</em></h2></div><div class="rt"><div class="ln"><i></i></div>{st}</div>
<div class="es" id="fiyat"><div class="fm"><h3>Fiyatı tahmin et</h3><div><div class="lb">Oda sayısı</div><div class="op" id="od"></div></div><div><div class="lb">Bulunduğun kat</div><div class="op" id="kt"></div></div><div><div class="lb">Asansör</div><div class="op" id="as"></div></div></div><div class="rs"><small>Tahmini aralık</small><b id="pt"></b><p id="pn2"></p><p>Kesin fiyat ücretsiz keşifle netleşir.</p><a class="btn" href="#kesif">Keşif iste</a></div></div></section>
<section class="cl" id="kesif"><div><h2>Keşif <br>randevusu.</h2><form id="fm"><input id="fn" required placeholder="Adınız" aria-label="Adınız" autocomplete="name"><input id="fd" type="date" required aria-label="Taşınma tarihi"><button class="btn" type="submit">Randevu iste</button><p class="ok" id="fo" aria-live="polite"></p></form></div></section></main>
<footer><div><b>Yük<i>.</i> Nakliyat</b><p>Evden eve nakliyat · Ankara</p></div><div><p>Sayfalar</p><a href="#surec">Süreç</a><a href="#fiyat">Fiyat tahmini</a><a href="#kesif">Keşif</a></div><div><p>İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div></footer>'''
    c = json.dumps(dict(o=ODA), ensure_ascii=False)
    return page('Yük Nakliyat', 'Evden eve nakliyat. Ücretsiz keşif, fiyat tahmini.', ['Sora:wght@600;700;800', 'Figtree:wght@500;600;700;800'], BASE_CSS + CSS, body, JS, c, dict(cta=['Ücretsiz keşif', '#kesif'], addr='Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/yuk', exist_ok=True); open(R + '/yuk/index.html', 'w', encoding='utf-8').write(render()); print('yuk ok')
