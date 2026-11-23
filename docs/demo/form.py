# -*- coding: utf-8 -*-
"""Form Stüdyo: spor salonu. Koyu yeşil + limon, dar devasa başlık, tam ekran foto, haftalık ders programı sekmeleri, program akordeonu."""
import json
from common import *
IDX = 12
f = foto.F[IDX]
ph = lambda k, w=1000: foto.url(f[k % len(f)], w)
GUN = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt']
DERS = {
 'Pzt': [('07:00', 'Kuvvet temelleri', 'Elif K.', 12), ('12:30', 'Öğle HIIT', 'Mert A.', 15), ('19:00', 'Güç ve kondisyon', 'Mert A.', 10)],
 'Sal': [('07:30', 'Mobilite', 'Selin D.', 14), ('18:30', 'Boks tekniği', 'Can Y.', 12), ('20:00', 'Kuvvet temelleri', 'Elif K.', 12)],
 'Çar': [('07:00', 'Öğle öncesi HIIT', 'Mert A.', 15), ('19:00', 'Pilates mat', 'Selin D.', 14)],
 'Per': [('07:30', 'Güç ve kondisyon', 'Mert A.', 10), ('18:30', 'Boks tekniği', 'Can Y.', 12), ('20:00', 'Mobilite', 'Selin D.', 14)],
 'Cum': [('07:00', 'Kuvvet temelleri', 'Elif K.', 12), ('18:00', 'HIIT', 'Mert A.', 15)],
 'Cmt': [('10:00', 'Takım antrenmanı', 'Tüm ekip', 20), ('11:30', 'Mobilite', 'Selin D.', 14)],
}
PROG = [('Başlangıç', '8 hafta, haftada 3 gün', 'Tüm hareketlerin tekniği ölçüyle öğretilir. İlk gün vücut ölçümü ve hedef konuşması yapılır.'),
        ('Güç', '12 hafta, haftada 4 gün', 'Squat, deadlift ve bench üzerine ilerleyen yük tablosu. Her ay test günü vardır.'),
        ('Yağ yakımı', '10 hafta, haftada 4 gün', 'Güç antrenmanı ve kardiyoyu bir arada planlar; beslenme notları yazılı verilir.'),
        ('Birebir', 'Esnek takvim', 'Tek antrenörle, kendi hedefine göre kişisel program. Ölçüm her 4 haftada tekrarlanır.')]
CSS = '''
:root{--bg:#0b1f17;--ink:#eaf5e4;--mut:#8fae9d;--ac:#c8ff2e;--ac2:#14392a;--ln:rgba(234,245,228,.18);--hf:'Anton',Impact,sans-serif;--mono:'Inter',sans-serif;--bf:'Inter',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 17px/1.6 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:400;text-transform:uppercase;line-height:.88;letter-spacing:.005em;overflow-wrap:break-word;min-width:0}
.btn{border-radius:4px;font-family:var(--bf);text-transform:uppercase;letter-spacing:.06em;font-size:14px;font-weight:800}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;align-items:center;gap:30px;padding:20px clamp(20px,4vw,56px);color:var(--ink);transition:background .3s}nav.top.solid{background:rgba(11,31,23,.94);backdrop-filter:blur(10px)}
.lg{font:400 28px var(--hf);letter-spacing:.04em;text-transform:uppercase;text-decoration:none;margin-right:auto}.lg b{color:var(--ac)}
nav.top ul{display:flex;gap:28px;list-style:none;padding:0}nav.top li a{font:700 13px var(--bf);text-transform:uppercase;letter-spacing:.1em;text-decoration:none}nav.top li a:hover{color:var(--ac)}
nav.top .btn{background:var(--ac);color:#0b1f17;padding:12px 22px}
.hero{height:100svh;min-height:640px;position:relative;display:flex;align-items:flex-end;padding:0 clamp(20px,4vw,56px) 7vh;overflow:clip}
.hero>img{position:absolute;inset:-6% 0;width:100%;height:112%;object-fit:cover;filter:saturate(.8) contrast(1.05)}.hero:after{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(11,31,23,.5),rgba(11,31,23,.15) 35%,rgba(11,31,23,.92))}
.hero .c{position:relative;z-index:2;width:100%}.hero h1{font-size:clamp(76px,17vw,300px);color:var(--ink)}.hero h1 em{font-style:normal;color:var(--ac)}
.hero .r{display:flex;justify-content:space-between;align-items:end;gap:30px;margin-top:22px;flex-wrap:wrap}.hero p{max-width:26em;font-size:19px}.hero .bt{display:flex;gap:10px;flex-wrap:wrap}
.hero .btn.p{background:var(--ac);color:#0b1f17}.hero .btn.g{border:2px solid var(--ink);background:transparent;color:var(--ink)}
.mq{border-block:1px solid var(--ln);overflow:hidden;white-space:nowrap;padding:18px 0;font:400 44px var(--hf);text-transform:uppercase;color:var(--ac)}.mq div{display:inline-block;animation:mq 26s linear infinite}.mq span{margin:0 26px}.mq i{color:var(--ink);font-style:normal}
@keyframes mq{to{transform:translateX(-50%)}}
section.s{padding:min(16vh,150px) clamp(20px,4vw,56px) 4vh;max-width:1500px;margin:auto}
.hd h2{font-size:clamp(56px,10vw,170px);margin-bottom:5vh}.hd h2 em{font-style:normal;color:var(--ac)}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:26px}.tabs button{min-width:78px;min-height:56px;border:2px solid var(--ln);background:transparent;color:var(--ink);font:400 24px var(--hf);text-transform:uppercase;cursor:pointer;border-radius:4px;transition:border-color .2s,background .2s}
.tabs button:hover{border-color:var(--ac)}.tabs button[aria-pressed=true]{background:var(--ac);border-color:var(--ac);color:#0b1f17}
.cl{display:grid;border-top:1px solid var(--ln)}.cl .it{display:grid;grid-template-columns:130px 1fr 220px 150px;gap:18px;align-items:center;padding:22px 0;border-bottom:1px solid var(--ln)}
.cl time{font:400 44px var(--hf);color:var(--ac)}.cl b{font:400 clamp(28px,3.6vw,50px)/1 var(--hf);text-transform:uppercase}.cl small{color:var(--mut);font-size:15px}
.cl .bk{justify-self:end;min-height:48px;padding:0 22px;background:transparent;border:2px solid var(--ac);color:var(--ac);font:800 13px var(--bf);letter-spacing:.08em;text-transform:uppercase;cursor:pointer;border-radius:4px;transition:background .2s,color .2s}.cl .bk:hover,.cl .bk.on{background:var(--ac);color:#0b1f17}
.pg{display:grid;grid-template-columns:.9fr 1.1fr;gap:5vw;align-items:start}.pg .im{aspect-ratio:4/5;position:relative;overflow:hidden;border-radius:6px;position:sticky;top:90px}.pg .im img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .8s}.pg .im:hover img{transform:scale(1.03)}
.ac details{border-top:1px solid var(--ln);padding:6px 0}.ac details:last-child{border-bottom:1px solid var(--ln)}.ac summary{list-style:none;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:14px;min-height:76px;font:400 clamp(34px,4.6vw,66px)/1 var(--hf);text-transform:uppercase}
.ac summary::-webkit-details-marker{display:none}.ac summary:after{content:'+';color:var(--ac);font-size:50px;transition:transform .3s}.ac details[open] summary:after{transform:rotate(45deg)}.ac summary small{display:block;font:700 14px var(--bf);color:var(--mut);letter-spacing:.06em;margin-top:4px}
.ac p{color:var(--mut);max-width:32em;padding:0 0 22px}
.pr{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.pr div{border:1px solid var(--ln);border-radius:8px;padding:30px;display:flex;flex-direction:column;gap:10px}.pr div.hi{background:var(--ac);color:#0b1f17;border-color:var(--ac)}.pr h3{font-size:44px}.pr b{font:400 64px var(--hf)}.pr p{opacity:.8}
.cta{background:var(--ac);color:#0b1f17;padding:min(14vh,120px) clamp(20px,4vw,56px);overflow:clip}.cta h2{font-size:clamp(70px,15vw,260px)}.cta form{display:flex;gap:10px;margin-top:30px;flex-wrap:wrap}.cta input{flex:1 1 260px;min-height:58px;background:transparent;border:2px solid #0b1f17;color:#0b1f17;padding:0 18px;font:600 17px var(--bf);border-radius:4px}.cta input::placeholder{color:#2b4a38}
.cta .btn{background:#0b1f17;color:var(--ac);min-height:58px;padding:0 30px;border:0;cursor:pointer}.cta .ok{display:none;margin-top:14px;font-weight:800}.cta .ok.on{display:block}
footer{padding:60px clamp(20px,4vw,56px) 28px;display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px;border-top:1px solid var(--ln)}footer b{font:400 34px var(--hf);text-transform:uppercase;color:var(--ac)}footer a{display:block;color:var(--ink);text-decoration:none;padding:3px 0}footer a:hover{color:var(--ac)}footer p{color:var(--mut)}
@media(max-width:860px){
nav.top ul,nav.top>.btn{display:none}nav.top{padding:12px 16px}nav.top .hm{margin-left:auto;border-radius:4px}
.hero h1{font-size:clamp(70px,24vw,150px)}.hero .r{margin-bottom:70px}
.cl .it{grid-template-columns:90px 1fr;gap:6px 12px;padding:16px 0}.cl time{font-size:34px}.cl .it>:nth-child(3){grid-column:2}.cl .bk{grid-column:2;justify-self:start;margin-top:6px}
.pg,.pr,footer{grid-template-columns:1fr}.pg .im{position:relative;top:0;aspect-ratio:1/1}
.mb{left:0;right:0;bottom:0;background:var(--bg);border:0;border-top:1px solid var(--ln);border-radius:0;grid-template-columns:1fr 1fr 1.4fr;padding:0 0 max(0px,env(safe-area-inset-bottom))}.mb a{min-height:58px;border-radius:0;color:var(--ink);font:800 13px var(--bf);letter-spacing:.08em;text-transform:uppercase}.mb a+a{border-left:1px solid var(--ln)}.mb a.p{background:var(--ac);color:#0b1f17}
.mm{background:var(--bg);inset:0;padding:96px 20px 110px;--ln:rgba(234,245,228,.18);--ac:#c8ff2e;--mut:#8fae9d}.mm a{font:400 clamp(60px,20vw,110px)/.95 var(--hf);text-transform:uppercase;color:var(--ink);border-bottom:1px solid var(--ln);padding:8px 0}.mm a:hover{color:var(--ac)}.mm small{color:var(--mut);font:700 13px var(--bf);letter-spacing:.1em}
footer{padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,rd=OK.reduce;
 if(!rd){gsap.from('.hero h1',{yPercent:40,opacity:0,duration:1.1,ease:'power4.out'});gsap.from('.hero .r>*',{y:30,opacity:0,stagger:.15,duration:.8,delay:.5});
  gsap.to('.hero>img',{yPercent:10,ease:'none',scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom top',scrub:true}});
  gsap.utils.toArray('.hd h2,.cta h2').forEach(function(e){gsap.from(e,{x:-60,opacity:0,duration:.9,ease:'power3.out',scrollTrigger:{trigger:e,start:'top 88%'}})});
  gsap.utils.toArray('.pr div').forEach(function(e,i){gsap.from(e,{y:50,opacity:0,duration:.7,delay:i*.1,scrollTrigger:{trigger:e,start:'top 92%'}})})}
 function show(g){$$('.tabs button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.g===g)});$('#cl').innerHTML=C.d[g].map(function(x){return '<div class="it"><time>'+x[0]+'</time><div><b>'+x[1]+'</b></div><small>'+x[2]+' · '+x[3]+' kişilik</small><button class="bk" type="button">Yer ayır</button></div>'}).join('');$$('.bk').forEach(function(b){b.onclick=function(){b.classList.toggle('on');b.textContent=b.classList.contains('on')?'Yer ayrıldı':'Yer ayır'}})}
 $$('.tabs button').forEach(function(b){b.onclick=function(){show(b.dataset.g)}});show('Pzt');
 $('#fm').onsubmit=function(e){e.preventDefault();var o=$('#fo');o.textContent='Teşekkürler. '+$('#fe').value+' adresine deneme dersi bilgisini gönderdik.';o.classList.add('on')};
});
'''
def render():
    tabs = ''.join('<button type="button" data-g="%s" aria-pressed="false">%s</button>' % (g, g) for g in GUN)
    prog = ''.join('<details%s><summary><span>%s<small>%s</small></span></summary><p>%s</p></details>' % (' open' if i == 0 else '', a, b, c_) for i, (a, b, c_) in enumerate(PROG))
    mq = ''.join('<span>Kuvvet</span><i>/</i><span>Kondisyon</span><i>/</i><span>Mobilite</span><i>/</i>' for _ in range(8))
    body = f'''<div id="pre" role="status"><div><b>FORM</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">Form<b>.</b></a><ul><li><a href="#program">Ders programı</a></li><li><a href="#paket">Programlar</a></li><li><a href="#fiyat">Üyelik</a></li></ul><a class="btn" href="#deneme">Ücretsiz deneme</a></nav>
<main><header class="hero" id="hero"><img src="{ph(0, 1800)}" alt="Salonda ağırlık çalışan sporcu" fetchpriority="high"><div class="c"><h1>Gücünü <em>kur.</em></h1><div class="r"><p>Küçük gruplarla, antrenörün sana bakarak çalıştığı bir salon. İlk ders ücretsiz.</p><div class="bt"><a class="btn p" href="#deneme">Ücretsiz dene</a><a class="btn g" href="#program">Ders programı</a></div></div></div></header>
<div class="mq" aria-hidden="true"><div>{mq}</div></div>
<section class="s" id="program"><div class="hd"><h2>Bu hafta <em>derste</em></h2></div><div class="tabs" role="group" aria-label="Gün">{tabs}</div><div class="cl" id="cl"></div></section>
<section class="s" id="paket"><div class="pg"><div class="im"><img src="{ph(1, 1000)}" alt="Antrenör sporcuya teknik gösteriyor" loading="lazy"></div><div class="ac"><div class="hd"><h2>Hedefe <em>göre</em> program</h2></div>{prog}</div></div></section>
<section class="s" id="fiyat"><div class="hd"><h2>Üyelik</h2></div><div class="pr"><div><h3>Aylık</h3><b>1.800 ₺</b><p>Tüm dersler, sınırsız giriş. İstediğin ay bırakabilirsin.</p></div><div class="hi"><h3>3 aylık</h3><b>4.500 ₺</b><p>Aylığa göre daha ucuz. Başlangıç ölçümü dahil.</p></div><div><h3>Birebir</h3><b>900 ₺</b><p>Ders başına, tek antrenörle. 10'lu pakette indirim vardır.</p></div></div></section>
<section class="cta" id="deneme"><h2>İlk ders<br>bizden.</h2><form id="fm"><input id="fe" type="email" required placeholder="E-posta adresin" aria-label="E-posta"><button class="btn" type="submit">Gönder</button></form><p class="ok" id="fo" aria-live="polite"></p></section></main>
<footer><div><b>Form Stüdyo</b><p>Örnek Cad. Ankara · 06:00 - 23:00</p></div><div><p>Sayfalar</p><a href="#program">Ders programı</a><a href="#paket">Programlar</a><a href="#fiyat">Üyelik</a></div><div><p>İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div></footer>'''
    c = json.dumps(dict(d={g: DERS[g] for g in GUN}), ensure_ascii=False)
    return page('Form Stüdyo Spor Salonu', 'Küçük gruplu ders, birebir antrenman. İlk ders ücretsiz.', ['Anton', 'Inter:wght@400;600;700;800'], BASE_CSS + CSS, body, JS, c, dict(cta=['Ücretsiz dene', '#deneme'], addr='Örnek Cad. · Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/form', exist_ok=True); open(R + '/form/index.html', 'w', encoding='utf-8').write(render()); print('form ok')
