# -*- coding: utf-8 -*-
"""Denge Diyet: diyetisyen. Koyu yeşil + limon, Lora; solda yapışkan başlık sütunu, sağda haftalık örnek menü sekmeleri ve paket seçici."""
import json
from common import *
IDX = 10
f = foto.F[IDX]
ph = lambda k, w=800: foto.url(f[k % len(f)], w)
GUN = {'Pazartesi': [('Kahvaltı', 'Yulaf, yoğurt, mevsim meyvesi', 1), ('Öğle', 'Mercimek çorbası, bulgur pilavı, cacık', 2), ('Akşam', 'Fırında tavuk, közlenmiş sebze', 3)],
       'Salı': [('Kahvaltı', 'Haşlanmış yumurta, tam buğday ekmeği, domates', 4), ('Öğle', 'Nohutlu salata, ayran', 5), ('Akşam', 'Zeytinyağlı barbunya, yoğurt', 6)],
       'Çarşamba': [('Kahvaltı', 'Peynirli omlet, yeşillik', 2), ('Öğle', 'Izgara balık, roka salatası', 3), ('Akşam', 'Sebzeli makarna, cacık', 1)],
       'Perşembe': [('Kahvaltı', 'Chia pudingi, muz', 6), ('Öğle', 'Etli kuru fasulye, pilav', 4), ('Akşam', 'Mantar sote, yoğurt', 5)],
       'Cuma': [('Kahvaltı', 'Tam buğday tost, avokado', 3), ('Öğle', 'Tavuklu salata', 1), ('Akşam', 'Fırın sebze, ızgara köfte', 2)]}
PAK = [('Tek görüşme', 900, 'Tanışma, ölçüm ve ilk program.'), ('1 aylık takip', 2400, 'Haftalık görüşme, menü güncelleme, mesajla destek.'), ('3 aylık takip', 6000, 'Aylığa göre daha uygun. Tarif kitapçığı dahil.')]
CSS = '''
:root{--bg:#f8faf3;--ink:#20372a;--mut:#5f7367;--ac:#8bc34a;--ac2:#20372a;--ln:rgba(32,55,42,.16);--hf:'Lora',Georgia,serif;--mono:'Inter',sans-serif;--bf:'Inter',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 17px/1.7 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:500;letter-spacing:-.02em;line-height:1.05;overflow-wrap:break-word;min-width:0}
.btn{border-radius:8px;font-family:var(--bf);font-weight:600;font-size:16px;text-transform:none;letter-spacing:0}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;align-items:center;gap:28px;padding:18px clamp(20px,4vw,56px);color:var(--ink);transition:background .3s,box-shadow .3s}nav.top.solid{background:rgba(248,250,243,.95);box-shadow:0 1px 0 var(--ln)}
.lg{font:italic 500 28px var(--hf);text-decoration:none;margin-right:auto}.lg b{color:#5d8f1f}
nav.top ul{display:flex;gap:28px;list-style:none;padding:0}nav.top li a{font:500 15px var(--bf);text-decoration:none}nav.top li a:hover{text-decoration:underline;text-underline-offset:6px;text-decoration-color:var(--ac)}nav.top .btn{background:var(--ink);color:#fff;padding:12px 22px}
.hero{padding:130px clamp(20px,4vw,56px) 40px;max-width:1500px;margin:auto;display:grid;grid-template-columns:repeat(12,1fr);gap:20px;align-items:end;min-height:100svh}
.hero h1{grid-column:1/9;font-size:clamp(52px,7.6vw,128px);font-weight:400}.hero h1 em{color:#5d8f1f}.hero .tx{grid-column:9/13;padding-bottom:12px}.hero .tx p{color:var(--mut);margin-bottom:20px}.hero .btn.p{background:var(--ac);color:var(--ink);padding:16px 28px;display:inline-block;font-weight:700}
.hero .wide{grid-column:1/-1;aspect-ratio:21/8;border-radius:16px;overflow:hidden;position:relative}.hero .wide img{position:absolute;inset:-8% 0;width:100%;height:116%;object-fit:cover}
section.s{padding:min(14vh,130px) clamp(20px,4vw,56px) 4vh;max-width:1380px;margin:auto}
.mn{display:grid;grid-template-columns:.7fr 1.3fr;gap:5vw;align-items:start}.mn .stk{position:sticky;top:110px}.mn h2{font-size:clamp(40px,5vw,78px);font-weight:400}.mn h2 em{color:#5d8f1f}.mn .stk p{color:var(--mut);margin:16px 0 26px}
.mn .tb{display:flex;flex-direction:column;gap:2px;border-top:1px solid var(--ln)}.mn .tb button{text-align:left;min-height:56px;border:0;border-bottom:1px solid var(--ln);background:transparent;color:var(--ink);font:italic 500 24px var(--hf);cursor:pointer;display:flex;justify-content:space-between;align-items:center;transition:padding .25s,color .2s}.mn .tb button:hover{padding-left:10px}.mn .tb button[aria-pressed=true]{color:#5d8f1f;padding-left:14px}.mn .tb button[aria-pressed=true]:after{content:'●';font-size:12px}
.ml{display:grid;gap:16px}.ml article{display:grid;grid-template-columns:200px 1fr;gap:20px;align-items:center;background:#fff;border-radius:16px;padding:14px;border:1px solid var(--ln)}.ml .im{aspect-ratio:1/1;border-radius:12px;overflow:hidden;position:relative}.ml img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .8s}.ml article:hover img{transform:scale(1.05)}
.ml small{font:600 14px var(--bf);color:#5d8f1f}.ml h3{font-size:30px;margin-top:4px}
.pk{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:6vh}.pk label{cursor:pointer}.pk input{position:absolute;opacity:0}.pk .c{display:block;border:2px solid var(--ln);border-radius:18px;padding:28px;height:100%;background:#fff;transition:all .25s}.pk input:focus-visible+.c{outline:3px solid var(--ac)}.pk input:checked+.c{border-color:var(--ink);background:var(--ink);color:#fff;transform:translateY(-4px)}.pk .c h3{font-size:28px}.pk .c b{display:block;font:500 46px var(--hf);margin:14px 0 6px;color:#5d8f1f}.pk input:checked+.c b{color:var(--ac)}.pk .c p{opacity:.8}
.cl{background:var(--ac);padding:min(12vh,110px) clamp(20px,4vw,56px);margin-top:8vh}.cl>div{max-width:1380px;margin:auto;display:grid;grid-template-columns:1fr 1fr;gap:5vw;align-items:end}.cl h2{font-size:clamp(42px,6vw,96px);font-weight:400}.cl form{display:grid;gap:10px}.cl input[type=text],.cl input[type=email]{min-height:56px;border:0;border-bottom:2px solid var(--ink);background:transparent;padding:0;font:500 18px var(--bf);color:var(--ink);border-radius:0}.cl .btn{background:var(--ink);color:#fff;min-height:58px;border:0;cursor:pointer}.cl .ok{display:none;background:#fff;padding:14px 18px;border-radius:8px;font-weight:600}.cl .ok.on{display:block}
footer{background:var(--ink);color:#fff;padding:70px clamp(20px,4vw,56px) 30px;display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px}footer b{font:italic 500 30px var(--hf);color:var(--ac)}footer a{display:block;color:#fff;text-decoration:none;padding:3px 0}footer a:hover{color:var(--ac)}footer p{color:#a9bdae}
@media(max-width:860px){
nav.top ul,nav.top>.btn{display:none}nav.top{padding:12px 16px}nav.top .hm{margin-left:auto;border-radius:8px}
.hero{padding-top:90px;min-height:0;display:block}.hero h1{font-size:clamp(46px,14vw,84px)}.hero .tx{padding:18px 0 26px}.hero .wide{aspect-ratio:4/3}
.mn,.pk,.cl>div,footer{grid-template-columns:1fr}.mn .stk{position:static}.mn .tb{flex-direction:row;flex-wrap:wrap;border:0;gap:6px}.mn .tb button{width:auto;min-height:46px;border:1px solid var(--ln);border-radius:30px;padding:0 18px;font-size:19px}.mn .tb button[aria-pressed=true]{background:var(--ink);color:#fff;padding-left:18px}.mn .tb button[aria-pressed=true]:after{content:none}.ml article{grid-template-columns:96px 1fr;gap:14px}.ml h3{font-size:22px}
.mb{left:0;right:0;bottom:0;background:var(--bg);border:0;border-top:1px solid var(--ln);border-radius:0;grid-template-columns:1fr 1fr 1.4fr;padding:0 0 max(0px,env(safe-area-inset-bottom))}.mb a{min-height:58px;border-radius:0;color:var(--ink);font:600 15px var(--bf);letter-spacing:0;text-transform:none}.mb a+a{border-left:1px solid var(--ln)}.mb a.p{background:var(--ac);color:var(--ink)}
.mm{background:var(--bg);color:var(--ink);inset:0;padding:96px 24px 110px;--ln:rgba(32,55,42,.16);--ac:#5d8f1f;--mut:#5f7367}.mm a{font:italic 500 clamp(42px,13vw,68px)/1.15 var(--hf);color:var(--ink);border-bottom:1px solid var(--ln);padding:10px 0}.mm small{color:var(--mut);font:600 14px var(--bf);text-transform:none;letter-spacing:0}
footer{padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce;
 if(!rd){gsap.from('.hero h1',{y:50,opacity:0,duration:1.1,ease:'power3.out'});gsap.from('.hero .tx,.hero .wide',{y:40,opacity:0,duration:1,delay:.3,stagger:.15,ease:'power3.out'});gsap.to('.hero .wide img',{yPercent:8,ease:'none',scrollTrigger:{trigger:'.hero .wide',start:'top bottom',end:'bottom top',scrub:true}});
  gsap.utils.toArray('.pk label,.stk').forEach(function(e,i){gsap.from(e,{y:46,opacity:0,duration:.8,delay:(i%3)*.08,scrollTrigger:{trigger:e,start:'top 92%'}})})}
 function sh(k){$$('.tb button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.k===k)});$('#ml').innerHTML=C.g[k].map(function(x){return '<article><div class="im"><img src="'+x[3]+'" alt="'+x[0]+'" loading="lazy"></div><div><small>'+x[0]+'</small><h3>'+x[1]+'</h3></div></article>'}).join('');if(!rd)gsap.from('#ml article',{y:30,opacity:0,stagger:.08,duration:.5})}
 $$('.tb button').forEach(function(b){b.onclick=function(){sh(b.dataset.k)}});sh('Pazartesi');
 $('#fm').onsubmit=function(e){e.preventDefault();var p=document.querySelector('.pk input:checked').dataset.n,o=$('#fo');o.textContent='Teşekkürler '+$('#fn').value+'. "'+p+'" için ilk görüşme randevunu ayarlamak üzere seni arayacağız.';o.classList.add('on')};
});
'''
def render():
    tb = ''.join('<button type="button" data-k="%s" aria-pressed="false">%s</button>' % (k, k) for k in GUN)
    pk = ''.join('<label><input type="radio" name="p" data-n="%s"%s><span class="c"><h3>%s</h3><b>%s</b><p>%s</p></span></label>' % (n, ' checked' if i == 1 else '', n, '{:,}'.format(p).replace(',', '.') + ' ₺', d) for i, (n, p, d) in enumerate(PAK))
    body = f'''<div id="pre" role="status"><div><b>DENGE</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">Denge<b>.</b></a><ul><li><a href="#menu">Örnek menü</a></li><li><a href="#paket">Paketler</a></li><li><a href="#randevu">Randevu</a></li></ul><a class="btn" href="#randevu">Randevu al</a></nav>
<main><header class="hero" id="hero"><h1>Yemeği <em>bırakmadan</em> dengeye gel.</h1><div class="tx"><p>Kişiye özel beslenme programı. Yasak listesi yok, yaşam tarzına uyan haftalık menü var.</p><a class="btn p" href="#randevu">İlk görüşmeyi ayarla</a></div><div class="wide"><img src="{ph(0, 1800)}" alt="Taze sebze ve sağlıklı tabak" fetchpriority="high"></div></header>
<section class="s" id="menu"><div class="mn"><div class="stk"><h2>Örnek <em>haftalık</em> menü</h2><p>Gerçek program kişiye göre hazırlanır. Burada bir fikir verir.</p><div class="tb" role="group" aria-label="Gün">{tb}</div></div><div class="ml" id="ml"></div></div></section>
<section class="s" id="paket"><div class="mn"><div class="stk"><h2>Sana uygun <em>paket</em></h2><p>Birini seç, randevu formunda hazır gelsin.</p></div><div></div></div><div class="pk">{pk}</div></section>
<section class="cl" id="randevu"><div><h2>İlk görüşme<br>ücretsiz.</h2><form id="fm"><input type="text" id="fn" required placeholder="Adınız" aria-label="Adınız" autocomplete="name"><input type="email" required placeholder="E-posta" aria-label="E-posta"><button class="btn" type="submit">Randevu iste</button><p class="ok" id="fo" aria-live="polite"></p></form></div></section></main>
<footer><div><b>Denge Diyet</b><p>Diyetisyen · Örnek Cad. Ankara</p></div><div><p>Sayfalar</p><a href="#menu">Örnek menü</a><a href="#paket">Paketler</a><a href="#randevu">Randevu</a></div><div><p>İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div></footer>'''
    g = {k: [[a, b, c_, ph(c_, 400)] for a, b, c_ in v] for k, v in GUN.items()}
    c = json.dumps(dict(g=g), ensure_ascii=False)
    return page('Denge Diyet', 'Kişiye özel beslenme programı. İlk görüşme ücretsiz.', ['Lora:ital,wght@0,400;0,500;1,500', 'Inter:wght@400;500;600;700'], BASE_CSS + CSS, body, JS, c, dict(cta=['Randevu al', '#randevu'], addr='Örnek Cad. · Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/denge', exist_ok=True); open(R + '/denge/index.html', 'w', encoding='utf-8').write(render()); print('denge ok')
