# -*- coding: utf-8 -*-
"""Sofra: bistro. Bordo zemin, serif, masa rezervasyon aracı, menü sekmeleri."""
import json
from common import *
IDX = 17
f = foto.F[IDX]
ph = lambda k, w=900: foto.url(f[k % len(f)], w)
MENU = {
 'Başlangıç': [('Közlenmiş patlıcan', 'Yoğurt, nar ekşisi, ceviz', 280), ('Deniz börülcesi', 'Zeytinyağı, limon', 240), ('Günün çorbası', 'Ekmek ile', 190)],
 'Ana yemek': [('Dana yanak', 'Kök sebze püresi, kırmızı şarap sosu', 720), ('Levrek', 'Kereviz, roka, limonlu tereyağı', 640), ('Kuzu pirzola', 'Közlenmiş sebze, nane yağı', 780)],
 'Tatlı': [('Fırın sütlaç', 'Tarçın, fındık', 210), ('Çikolatalı sufle', 'Vanilyalı dondurma', 260), ('Mevsim meyvesi', 'Ballı yoğurt ile', 220)],
}
SAAT = ['18:00', '18:30', '19:00', '19:30', '20:00', '20:30', '21:00', '21:30']
CSS = '''
:root{--bg:#3b0f1a;--ink:#f6ead8;--mut:#c9a99a;--ac:#e9c489;--ac2:#2a0810;--ln:rgba(246,234,216,.22);--hf:'Playfair Display',Georgia,serif;--mono:'Inter',sans-serif;--bf:'Inter',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 17px/1.7 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:500;line-height:1.02;letter-spacing:-.01em;overflow-wrap:break-word;min-width:0}
.btn{border-radius:0;font-family:var(--bf);text-transform:uppercase;letter-spacing:.14em;font-size:13px;font-weight:600}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;align-items:center;gap:36px;padding:22px clamp(20px,4vw,56px);color:var(--ink);transition:background .3s}nav.top.solid{background:rgba(42,8,16,.95);backdrop-filter:blur(8px)}
.lg{font:500 30px var(--hf);font-style:italic;text-decoration:none;margin-right:auto}
nav.top ul{display:flex;gap:34px;list-style:none;padding:0}nav.top li a{font:500 12px var(--bf);text-transform:uppercase;letter-spacing:.16em;text-decoration:none}nav.top li a:hover{color:var(--ac)}
nav.top .btn{border:1px solid var(--ac);color:var(--ac);background:transparent;padding:12px 24px}nav.top .btn:hover{background:var(--ac);color:var(--ac2)}
.hero{min-height:100svh;display:grid;grid-template-columns:1fr 1fr;position:relative}
.hero .tx{display:flex;flex-direction:column;justify-content:center;padding:130px clamp(24px,5vw,80px) 80px}.hero .tx small{font:500 12px var(--bf);text-transform:uppercase;letter-spacing:.2em;color:var(--ac);margin-bottom:26px}
.hero h1{font-size:clamp(58px,7.6vw,128px);font-weight:400}.hero h1 em{color:var(--ac)}.hero p{max-width:26em;color:var(--mut);margin:26px 0 34px;font-size:18px}
.hero .bt{display:flex;gap:14px;flex-wrap:wrap}.hero .btn.p{background:var(--ac);color:var(--ac2);padding:17px 32px}.hero .btn.g{border:1px solid var(--ln);color:var(--ink);background:transparent}
.hero .im{position:relative;min-height:60vh;overflow:hidden}.hero .im img{position:absolute;inset:-5% 0;width:100%;height:110%;object-fit:cover}.hero .im:before{content:'';position:absolute;inset:0;z-index:1;background:linear-gradient(90deg,var(--bg),transparent 25%)}
.hero .sl{position:absolute;z-index:2;bottom:36px;right:36px;border:1px solid var(--ac);padding:12px 18px;background:rgba(42,8,16,.78);font:500 12px var(--bf);text-transform:uppercase;letter-spacing:.14em;color:var(--ac)}
section.s{padding:min(16vh,150px) clamp(24px,5vw,80px) 4vh;max-width:1360px;margin:auto}
.hd{text-align:center;margin-bottom:6vh}.hd small{font:500 12px var(--bf);text-transform:uppercase;letter-spacing:.2em;color:var(--ac);display:block;margin-bottom:16px}.hd h2{font-size:clamp(44px,6vw,96px);font-weight:400}.hd h2 em{color:var(--ac)}
.rz{display:grid;grid-template-columns:1fr 1fr;border:1px solid var(--ln)}.rz .im{position:relative;min-height:440px;overflow:hidden}.rz .im img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .8s}.rz .im:hover img{transform:scale(1.03)}
.rz .fm{padding:clamp(26px,4vw,56px);display:grid;gap:22px;align-content:center}.fm h3{font-size:clamp(32px,3.6vw,50px)}.fm .lb{font:500 12px var(--bf);text-transform:uppercase;letter-spacing:.16em;color:var(--mut);margin-bottom:10px}
.cnt{display:flex;align-items:center;gap:20px}.cnt button{width:52px;height:52px;border:1px solid var(--ac);background:transparent;color:var(--ac);font:400 28px var(--hf);cursor:pointer;transition:background .2s,color .2s}.cnt button:hover{background:var(--ac);color:var(--ac2)}.cnt b{font:500 54px var(--hf);min-width:1.4em;text-align:center}
.sat{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.sat button{min-height:50px;border:1px solid var(--ln);background:transparent;color:var(--ink);font:500 16px var(--bf);cursor:pointer;transition:all .2s}.sat button:hover{border-color:var(--ac)}.sat button[aria-pressed=true]{background:var(--ac);color:var(--ac2);border-color:var(--ac)}
.fm input[type=date],.fm input[type=text]{min-height:52px;border:0;border-bottom:1px solid var(--ln);background:transparent;color:var(--ink);font:500 18px var(--bf);width:100%;padding:0;color-scheme:dark;border-radius:0}.fm input:focus-visible{border-color:var(--ac);outline:0}
.fm .btn.p{background:var(--ac);color:var(--ac2);min-height:58px;border:0;cursor:pointer}.fm .ok{display:none;border:1px solid var(--ac);padding:16px;color:var(--ac)}.fm .ok.on{display:block}
.mn{display:grid;grid-template-columns:.8fr 1.2fr;gap:6vw;align-items:start}.mn .tb{display:flex;flex-direction:column;gap:4px;position:sticky;top:110px}.mn .tb button{text-align:left;background:none;border:0;color:var(--mut);font:400 clamp(34px,4.4vw,64px)/1.15 var(--hf);cursor:pointer;padding:6px 0;font-style:italic;transition:color .2s,transform .3s}.mn .tb button:hover{color:var(--ink)}.mn .tb button[aria-pressed=true]{color:var(--ac);transform:translateX(18px)}
.dl{list-style:none;padding:0}.dl li{display:grid;grid-template-columns:1fr auto;gap:4px 24px;padding:22px 0;border-bottom:1px solid var(--ln)}.dl li:first-child{border-top:1px solid var(--ln)}.dl b{font:500 28px var(--hf)}.dl i{color:var(--mut);font-style:normal;grid-column:1}.dl span{font:500 28px var(--hf);color:var(--ac);grid-row:1/3;grid-column:2;align-self:center}
.st{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:8vh 0}.st figure{margin:0;aspect-ratio:3/4;position:relative;overflow:hidden}.st figure:nth-child(2){margin-top:50px}.st img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .8s}.st figure:hover img{transform:scale(1.04)}
.vs{text-align:center;padding:min(12vh,110px) 20px}.vs p{font:400 clamp(30px,4.2vw,64px)/1.1 var(--hf);font-style:italic;max-width:18em;margin:0 auto}.vs small{display:block;margin-top:24px;font:500 12px var(--bf);text-transform:uppercase;letter-spacing:.2em;color:var(--ac)}
footer{background:var(--ac2);padding:80px clamp(24px,5vw,80px) 36px;text-align:center}footer b{font:500 clamp(54px,9vw,130px)/1 var(--hf);font-style:italic;display:block;color:var(--ac)}footer .ln{display:flex;gap:30px;justify-content:center;flex-wrap:wrap;margin:34px 0}footer a{color:var(--ink);text-decoration:none;font:500 12px var(--bf);text-transform:uppercase;letter-spacing:.16em}footer a:hover{color:var(--ac)}footer p{color:var(--mut);font-size:15px}
@media(max-width:860px){
nav.top ul,nav.top>.btn{display:none}nav.top{padding:12px 16px}nav.top .hm{margin-left:auto;border-radius:0}
.hero{grid-template-columns:1fr}.hero .im{order:-1;min-height:48vh}.hero .im:before{background:linear-gradient(0deg,var(--bg),transparent 30%)}.hero .tx{padding:30px 22px 110px}.hero .sl{display:none}
.rz,.mn,.st{grid-template-columns:1fr}.rz .im{min-height:240px}.mn .tb{position:static;flex-direction:row;flex-wrap:wrap;gap:4px 18px}.mn .tb button{font-size:34px}.mn .tb button[aria-pressed=true]{transform:none}.st figure:nth-child(2){margin-top:0}.sat{grid-template-columns:repeat(3,1fr)}
.mb{left:0;right:0;bottom:0;background:var(--ac2);border:0;border-top:1px solid var(--ln);border-radius:0;grid-template-columns:1fr 1fr 1.5fr;padding:0 0 max(0px,env(safe-area-inset-bottom))}.mb a{min-height:60px;border-radius:0;color:var(--ink);font:500 12px var(--bf);letter-spacing:.16em;text-transform:uppercase}.mb a+a{border-left:1px solid var(--ln)}.mb a.p{background:var(--ac);color:var(--ac2)}
.mm{background:var(--ac2);inset:0;padding:100px 28px 110px;text-align:center;align-items:center;justify-content:center;--ln:rgba(246,234,216,.22);--ac:#e9c489;--mut:#c9a99a}.mm a{font:400 clamp(44px,14vw,76px)/1.2 var(--hf);font-style:italic;color:var(--ink);border-bottom:0;padding:6px 0}.mm a:hover{color:var(--ac)}.mm small{color:var(--mut);font:500 12px var(--bf);letter-spacing:.2em}
footer{padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce;
 if(!rd){var tl=gsap.timeline({defaults:{ease:'power3.out'}});tl.from('.hero .tx>*',{y:40,opacity:0,stagger:.12,duration:1}).from('.hero .im img',{scale:1.15,duration:2},0);
  gsap.to('.hero .im img',{yPercent:8,ease:'none',scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom top',scrub:true}});
  gsap.utils.toArray('.hd,.st figure,.vs p').forEach(function(e,i){gsap.from(e,{y:50,opacity:0,duration:1,ease:'power3.out',scrollTrigger:{trigger:e,start:'top 90%'}})})}
 var g=2;function sg(n){g=Math.max(1,Math.min(12,n));$('#gn').textContent=g}
 $('#gm').onclick=function(){sg(g-1)};$('#gp').onclick=function(){sg(g+1)};sg(2);
 var t='19:30';$$('.sat button').forEach(function(b){b.onclick=function(){t=b.textContent;$$('.sat button').forEach(function(x){x.setAttribute('aria-pressed',x===b)})}});
 var d=new Date();d.setDate(d.getDate()+1);var ds=d.toISOString().slice(0,10);$('#rd').value=ds;$('#rd').min=new Date().toISOString().slice(0,10);
 $('#rf').onsubmit=function(e){e.preventDefault();var o=$('#ro'),dt=new Date($('#rd').value+'T12:00:00').toLocaleDateString('tr-TR',{day:'numeric',month:'long',weekday:'long'});o.textContent=$('#rn').value+', '+dt+' saat '+t+' için '+g+' kişilik masa isteğin alındı. Onay için seni arayacağız.';o.classList.add('on')};
 var cur;function sm(k){cur=k;$$('.tb button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.k===k)});$('#dl').innerHTML=C.m[k].map(function(x){return '<li><b>'+x[0]+'</b><i>'+x[1]+'</i><span>'+money(x[2])+'</span></li>'}).join('')}
 $$('.tb button').forEach(function(b){b.onclick=function(){sm(b.dataset.k)}});sm('Başlangıç');
});
'''
def render():
    tb = ''.join('<button type="button" data-k="%s" aria-pressed="false">%s</button>' % (k, k) for k in MENU)
    sat = ''.join('<button type="button" aria-pressed="%s">%s</button>' % ('true' if s == '19:30' else 'false', s) for s in SAAT)
    body = f'''<div id="pre" role="status"><div><b>SOFRA</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">Sofra</a><ul><li><a href="#rezervasyon">Rezervasyon</a></li><li><a href="#menu">Menü</a></li><li><a href="#iletisim">Adres</a></li></ul><a class="btn" href="#rezervasyon">Masa ayır</a></nav>
<main><header class="hero" id="hero"><div class="tx"><small>Bistro · Ankara</small><h1>Masa <em>kurulu</em>, sofra sıcak.</h1><p>Mevsiminde sebze, günlük balık, yavaş pişen et. Her gün akşam yemeği, hafta sonu öğle de açığız.</p><div class="bt"><a class="btn p" href="#rezervasyon">Masa ayır</a><a class="btn g" href="#menu">Menüye bak</a></div></div><div class="im"><img src="{ph(0, 1400)}" alt="Bistroda servise hazır tabak" fetchpriority="high"><div class="sl">Her gün 18:00 - 23:00</div></div></header>
<section class="s" id="rezervasyon"><div class="hd"><small>Rezervasyon</small><h2>Masanı <em>şimdi</em> ayır</h2></div><div class="rz"><div class="im"><img src="{ph(1, 1000)}" alt="Akşam yemeğine hazırlanmış masa" loading="lazy"></div><form class="fm" id="rf"><h3>Kaç kişi, ne zaman?</h3><div><div class="lb">Kişi sayısı</div><div class="cnt"><button type="button" id="gm" aria-label="Azalt">−</button><b id="gn">2</b><button type="button" id="gp" aria-label="Artır">+</button></div></div><div><div class="lb">Tarih</div><input id="rd" type="date" required></div><div><div class="lb">Saat</div><div class="sat">{sat}</div></div><div><div class="lb">Adın</div><input id="rn" type="text" required autocomplete="name"></div><button class="btn p" type="submit">Masa iste</button><p class="ok" id="ro" aria-live="polite"></p></form></div></section>
<section class="s" id="menu"><div class="hd"><small>Menü</small><h2>Mutfaktan <em>seçmeler</em></h2></div><div class="mn"><div class="tb" role="group" aria-label="Menü bölümü">{tb}</div><ul class="dl" id="dl"></ul></div>
<div class="st"><figure><img src="{ph(2, 800)}" alt="Ana yemek tabağı" loading="lazy"></figure><figure><img src="{ph(3, 800)}" alt="Şef tabak hazırlıyor" loading="lazy"></figure><figure><img src="{ph(4, 800)}" alt="Tatlı tabağı" loading="lazy"></figure></div></section>
<section class="vs"><p>Yavaş pişen yemek, acelesiz sofra.</p><small>Şef Murat Kaya</small></section></main>
<footer id="iletisim"><b>Sofra</b><div class="ln"><a href="#rezervasyon">Rezervasyon</a><a href="#menu">Menü</a><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div><p>Örnek Sok. Ankara · Her gün 18:00 - 23:00</p></footer>'''
    c = json.dumps(dict(m={k: v for k, v in MENU.items()}), ensure_ascii=False)
    return page('Sofra Bistro', 'Ankara bistro. Masa rezervasyonu ve menü.', ['Playfair+Display:ital,wght@0,400;0,500;1,400;1,500', 'Inter:wght@400;500;600'], BASE_CSS + CSS, body, JS, c, dict(cta=['Masa ayır', '#rezervasyon'], addr='Örnek Sok. · Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/sofra', exist_ok=True); open(R + '/sofra/index.html', 'w', encoding='utf-8').write(render()); print('sofra ok')
