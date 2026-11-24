# -*- coding: utf-8 -*-
"""Direksiyon: sürücü kursu. Koyu lacivert + kırmızı; yol şeridi, ehliyet sınıfı kartları, yatay kaydırmalı kurs yolu, soru çözme mini sınavı."""
import json
from common import *
IDX = 19
f = foto.F[IDX]
ph = lambda k, w=900: foto.url(f[k % len(f)], w)
SINIF = {'B': ('Otomobil', 'En çok seçilen sınıf. Teorik ve direksiyon eğitimi, ardından sınav.', 'Manuel veya otomatik'), 'A2': ('Motosiklet', 'Motosiklet için eğitim, pist ve yol uygulaması.', 'Kask ve ekipman kursta'), 'M': ('Moped', 'Düşük hızlı araç sınıfı. Kısa teorik ve uygulama.', 'Kısa eğitim'), 'C': ('Kamyon', 'Ticari araç sınıfı. Önceden B ehliyeti gerekir.', 'Yeterlilik şartı aranır')}
SORU = [('Kırmızı ışıkta duran sürücü ne zaman geçebilir?', ['Yeşil yandığında', 'Yol boşsa', 'Sarı yandığında'], 0), ('Şehir içinde tek yönlü yola ters girilir mi?', ['Gece girilir', 'Hayır, asla', 'Acil ise girilir'], 1), ('Emniyet kemeri kimler için zorunludur?', ['Yalnız sürücü', 'Ön koltuktakiler', 'Araçtaki herkes'], 2)]
STEP = [('Kayıt', 'Evrakları tamamla, sınıfını seç.'), ('Teorik', 'Trafik ve ilk yardım dersleri. Sınava hazırlık soruları.'), ('Direksiyon', 'Eğitmenle direksiyon dersleri, önce pist sonra yol.'), ('Sınav', 'Sınav günü yanında bir eğitmenin olur.'), ('Ehliyet', 'Başarılı olunca ehliyet çıkarılır.')]
CSS = '''
:root{--bg:#0f172a;--ink:#f1f5f9;--mut:#94a3b8;--ac:#ef4444;--ac2:#f1f5f9;--ln:rgba(241,245,249,.16);--hf:'Archivo',system-ui,sans-serif;--mono:'Inter',sans-serif;--bf:'Inter',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 17px/1.65 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:800;font-stretch:112%;letter-spacing:-.04em;line-height:.96;overflow-wrap:break-word;min-width:0}
.btn{border-radius:999px;font-family:var(--bf);font-weight:700;font-size:16px;text-transform:none;letter-spacing:0}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;align-items:center;gap:28px;padding:16px clamp(20px,4vw,56px);color:var(--ink);transition:background .3s}nav.top.solid{background:rgba(15,23,42,.94);backdrop-filter:blur(10px)}
.lg{font:800 24px var(--hf);letter-spacing:-.04em;text-decoration:none;margin-right:auto}.lg b{color:var(--ac)}
nav.top ul{display:flex;gap:28px;list-style:none;padding:0}nav.top li a{font:600 15px var(--bf);text-decoration:none;color:var(--mut)}nav.top li a:hover{color:#fff}nav.top .btn{background:var(--ac);color:#fff;padding:12px 24px}
.hero{min-height:100svh;position:relative;display:flex;align-items:flex-end;padding:0 clamp(20px,4vw,56px) 14vh;overflow:clip}.hero>img{position:absolute;inset:-6% 0;width:100%;height:112%;object-fit:cover;opacity:.55}.hero:after{content:'';position:absolute;inset:0;background:linear-gradient(0deg,var(--bg),rgba(15,23,42,.3) 60%,rgba(15,23,42,.7))}
.hero .c{position:relative;z-index:2;max-width:1200px}.hero h1{font-size:clamp(56px,10vw,180px)}.hero h1 em{font-style:normal;color:var(--ac)}.hero p{max-width:26em;margin:20px 0 28px;font-size:20px;color:#cbd5e1}.hero .bt{display:flex;gap:12px;flex-wrap:wrap}.hero .btn.p{background:var(--ac);color:#fff;padding:18px 34px}.hero .btn.g{border:2px solid var(--ink);color:var(--ink);background:transparent;padding:16px 30px}
.road{height:14px;background:linear-gradient(90deg,transparent 0,transparent 0),repeating-linear-gradient(90deg,#f1f5f9 0 60px,transparent 60px 120px) center/100% 4px no-repeat,#1e293b}
section.s{padding:min(14vh,130px) clamp(20px,4vw,56px) 4vh;max-width:1380px;margin:auto}
.hd h2{font-size:clamp(42px,6.6vw,108px);margin-bottom:5vh}.hd h2 em{font-style:normal;color:var(--ac)}
.sn{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.sn button{aspect-ratio:3/4;border:1px solid var(--ln);border-radius:24px;background:#162036;color:var(--ink);cursor:pointer;display:flex;flex-direction:column;justify-content:space-between;padding:22px;text-align:left;transition:transform .3s,background .3s,border-color .3s}.sn button:hover{transform:translateY(-6px);border-color:var(--ac)}.sn button[aria-pressed=true]{background:var(--ac);border-color:var(--ac)}
.sn b{font:800 clamp(80px,9vw,150px)/.8 var(--hf);letter-spacing:-.06em}.sn span{font:700 20px var(--hf)}
.dt{margin-top:16px;border:1px solid var(--ln);border-radius:24px;padding:clamp(24px,3.4vw,44px);display:grid;grid-template-columns:1fr 1fr;gap:30px;background:#162036}.dt h3{font-size:clamp(32px,4vw,56px)}.dt p{color:var(--mut);margin-top:12px;max-width:28em}.dt .kv{display:flex;flex-direction:column;gap:12px;justify-content:center}.dt .kv div{border-bottom:1px solid var(--ln);padding-bottom:12px}.dt .kv small{display:block;color:var(--mut);font-size:14px}.dt .kv b{font:700 22px var(--hf)}
.hz{height:100svh;overflow:hidden;position:relative}.hz .tr{display:flex;height:100%;width:max-content;align-items:center;padding:0 clamp(20px,4vw,56px);gap:20px}.hz .hl{width:min(80vw,640px);flex:none}.hz .hl h2{font-size:clamp(48px,7vw,120px)}.hz .hl h2 em{font-style:normal;color:var(--ac)}.hz .hl p{color:var(--mut);margin-top:14px}
.hz .st{flex:none;width:min(70vw,420px);height:62vh;border:1px solid var(--ln);border-radius:28px;padding:30px;background:#162036;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden}.hz .st b{font:800 clamp(100px,12vw,190px)/.8 var(--hf);color:rgba(239,68,68,.9);letter-spacing:-.06em}.hz .st h3{font-size:38px}.hz .st p{color:var(--mut);margin-top:8px}.hz .st:last-child{background:var(--ac)}.hz .st:last-child b{color:rgba(255,255,255,.9)}.hz .st:last-child p{color:#fff}
.qz{display:grid;grid-template-columns:1fr 1fr;gap:5vw;align-items:center;margin-top:6vh}.qz .im{aspect-ratio:4/3;border-radius:24px;overflow:hidden;position:relative}.qz img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.qb{border:1px solid var(--ln);border-radius:24px;padding:clamp(24px,3.4vw,44px);background:#162036}.qb .st2{font:600 14px var(--bf);color:var(--mut);margin-bottom:10px}.qb h3{font-size:clamp(26px,3vw,40px);margin-bottom:20px;letter-spacing:-.03em}.qb .op{display:grid;gap:8px}.qb .op button{text-align:left;min-height:54px;padding:0 20px;border:1px solid var(--ln);border-radius:14px;background:transparent;color:var(--ink);font:600 17px var(--bf);cursor:pointer;transition:all .2s}.qb .op button:hover{border-color:var(--ac)}.qb .op button.ok{background:#16a34a;border-color:#16a34a;color:#fff}.qb .op button.no{background:var(--ac);border-color:var(--ac);color:#fff}.qb .nx{margin-top:18px;background:#fff;color:var(--bg);border:0;padding:13px 26px;cursor:pointer}
.cl{background:var(--ac);color:#fff;padding:min(12vh,110px) clamp(20px,4vw,56px);margin-top:8vh}.cl>div{max-width:1380px;margin:auto;display:grid;grid-template-columns:1fr 1fr;gap:5vw;align-items:end}.cl h2{font-size:clamp(46px,7.4vw,120px)}.cl form{display:grid;gap:10px}.cl input,.cl select{min-height:56px;border:0;border-radius:14px;padding:0 18px;font:600 17px var(--bf);background:rgba(255,255,255,.2);color:#fff}.cl select option{color:#0f172a}.cl input::placeholder{color:#ffd0d0}.cl .btn{background:#fff;color:var(--ac);min-height:58px;border:0;cursor:pointer}.cl .ok{display:none;background:#fff;color:var(--ac);padding:14px 18px;border-radius:14px;font-weight:700}.cl .ok.on{display:block}
footer{padding:60px clamp(20px,4vw,56px) 30px;display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px;border-top:1px solid var(--ln)}footer b{font:800 28px var(--hf);letter-spacing:-.04em}footer b i{color:var(--ac);font-style:normal}footer a{display:block;color:var(--ink);text-decoration:none;padding:3px 0}footer a:hover{color:var(--ac)}footer p{color:var(--mut)}
@media(max-width:860px){
nav.top ul,nav.top>.btn{display:none}nav.top{padding:12px 16px}nav.top .hm{margin-left:auto;border-radius:50%}
.hero h1{font-size:clamp(52px,16vw,96px)}.sn{grid-template-columns:1fr 1fr}.dt,.qz,.cl>div,footer{grid-template-columns:1fr}
.hz{height:auto}.hz .tr{flex-direction:column;width:auto;height:auto;padding:0 20px;align-items:stretch}.hz .hl,.hz .st{width:100%}.hz .st{height:auto;min-height:220px;gap:20px}
.mb{left:12px;right:12px;bottom:12px;background:#1e293b;border:1px solid var(--ln);border-radius:999px;grid-template-columns:1fr 1fr 1.5fr;padding:5px;gap:4px}.mb a{min-height:50px;border-radius:999px;color:var(--ink);font:700 15px var(--bf);letter-spacing:0;text-transform:none}.mb a+a{border:0}.mb a.p{background:var(--ac);color:#fff}
.mm{background:var(--ac);color:#fff;inset:0;padding:90px 24px 110px;--ln:rgba(255,255,255,.3);--ac:#fff;--mut:#ffd0d0}.mm a{font:800 clamp(44px,14vw,72px)/1 var(--hf);letter-spacing:-.04em;color:#fff;border-bottom:1px solid var(--ln);padding:12px 0}.mm small{color:#ffd0d0;font:600 14px var(--bf);text-transform:none;letter-spacing:0}
footer{padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,rd=OK.reduce,mob=matchMedia('(max-width:860px)').matches;
 if(!rd){gsap.from('.hero h1',{y:60,opacity:0,duration:1.1,ease:'power4.out'});gsap.from('.hero .c>*:not(h1)',{y:30,opacity:0,stagger:.12,duration:.8,delay:.4});gsap.to('.hero>img',{yPercent:10,ease:'none',scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom top',scrub:true}});
  if(!mob){var tr=$('.hz .tr');gsap.to(tr,{x:function(){return -(tr.scrollWidth-innerWidth)},ease:'none',scrollTrigger:{trigger:'.hz',start:'top top',end:function(){return '+='+(tr.scrollWidth-innerWidth)},pin:true,scrub:.6,invalidateOnRefresh:true}})}
  gsap.utils.toArray('.hd h2,.sn button,.cl h2').forEach(function(e,i){gsap.from(e,{y:50,opacity:0,duration:.8,delay:(i%4)*.07,scrollTrigger:{trigger:e,start:'top 92%'}})})}
 function sh(k){var d=C.s[k];$$('.sn button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.k===k)});$('#t').textContent=k+' sınıfı · '+d[0];$('#d').textContent=d[1];$('#n').textContent=d[2]}
 $$('.sn button').forEach(function(b){b.onclick=function(){sh(b.dataset.k)}});sh('B');
 var qi=0,sc=0;function dq(){var q=C.q[qi],b=$('#qb');if(!q){b.innerHTML='<div class="st2">Bitti</div><h3>'+sc+' / '+C.q.length+' doğru</h3><button class="btn nx" id="rs" type="button">Tekrar dene</button>';$('#rs').onclick=function(){qi=0;sc=0;dq()};return}
  b.innerHTML='<div class="st2">Soru '+(qi+1)+' / '+C.q.length+'</div><h3>'+q[0]+'</h3><div class="op">'+q[1].map(function(o,i){return '<button type="button" data-i="'+i+'">'+o+'</button>'}).join('')+'</div>';
  $$('#qb .op button').forEach(function(x){x.onclick=function(){var ok=+x.dataset.i===q[2];if(ok)sc++;$$('#qb .op button').forEach(function(y){y.disabled=true;if(+y.dataset.i===q[2])y.classList.add('ok')});if(!ok)x.classList.add('no');var n=document.createElement('button');n.className='btn nx';n.type='button';n.textContent='Sonraki';n.onclick=function(){qi++;dq()};b.appendChild(n)}})}
 dq();
 $('#fm').onsubmit=function(e){e.preventDefault();var o=$('#fo');o.textContent='Teşekkürler '+$('#fn').value+'. '+$('#fk').value+' sınıfı için kayıt bilgilerini göndermek üzere seni arayacağız.';o.classList.add('on')};
});
'''
def render():
    sn = ''.join('<button type="button" data-k="%s" aria-pressed="false"><b>%s</b><span>%s</span></button>' % (k, k, v[0]) for k, v in SINIF.items())
    st = ''.join('<div class="st"><b>%d</b><div><h3>%s</h3><p>%s</p></div></div>' % (i + 1, a, b) for i, (a, b) in enumerate(STEP))
    opt = ''.join('<option>%s</option>' % k for k in SINIF)
    body = f'''<div id="pre" role="status"><div><b>DİREKSİYON</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">Direksiyon<b>.</b></a><ul><li><a href="#sinif">Sınıflar</a></li><li><a href="#yol">Kurs yolu</a></li><li><a href="#soru">Mini sınav</a></li></ul><a class="btn" href="#kayit">Kayıt ol</a></nav>
<main><header class="hero" id="hero"><img src="{ph(0, 1800)}" alt="Direksiyon başında ehliyet adayı" fetchpriority="high"><div class="c"><h1>Ehliyet <em>yolunda</em> yalnız değilsin.</h1><p>B, A2, M ve C sınıfı eğitim. Sabırlı eğitmen, güncel araç, sınav gününe kadar yanında.</p><div class="bt"><a class="btn p" href="#kayit">Kayıt ol</a><a class="btn g" href="#sinif">Sınıfını seç</a></div></div></header><div class="road"></div>
<section class="s" id="sinif"><div class="hd"><h2>Hangi <em>sınıf?</em></h2></div><div class="sn" role="group" aria-label="Sınıf">{sn}</div><div class="dt"><div><h3 id="t"></h3><p id="d"></p></div><div class="kv"><div><small>Not</small><b id="n"></b></div><div><small>Sınav</small><b>Teorik ve direksiyon</b></div></div></div></section>
<section class="hz" id="yol"><div class="tr"><div class="hl"><h2>Beş adımda <em>ehliyet</em></h2><p>Kaydırarak yolu izle.</p></div>{st}</div></section>
<section class="s" id="soru"><div class="hd"><h2>Mini <em>sınav</em></h2></div><div class="qz"><div class="im"><img src="{ph(1, 900)}" alt="Kurs aracı" loading="lazy"></div><div class="qb" id="qb"></div></div></section>
<section class="cl" id="kayit"><div><h2>Kayıt<br>ol.</h2><form id="fm"><input id="fn" required placeholder="Adınız" aria-label="Adınız" autocomplete="name"><select id="fk" aria-label="Sınıf">{opt}</select><button class="btn" type="submit">Beni arayın</button><p class="ok" id="fo" aria-live="polite"></p></form></div></section></main>
<footer><div><b>Direksiyon<i>.</i> Sürücü Kursu</b><p>Örnek Cad. Ankara</p></div><div><p>Sayfalar</p><a href="#sinif">Sınıflar</a><a href="#yol">Kurs yolu</a><a href="#soru">Mini sınav</a></div><div><p>İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div></footer>'''
    c = json.dumps(dict(s={k: list(v) for k, v in SINIF.items()}, q=SORU), ensure_ascii=False)
    return page('Direksiyon Sürücü Kursu', 'B, A2, M ve C sınıfı ehliyet eğitimi.', ['Archivo:wght@700;800', 'Inter:wght@400;600;700'], BASE_CSS + CSS, body, JS, c, dict(cta=['Kayıt ol', '#kayit'], addr='Örnek Cad. · Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/direksiyon', exist_ok=True); open(R + '/direksiyon/index.html', 'w', encoding='utf-8').write(render()); print('direksiyon ok')
