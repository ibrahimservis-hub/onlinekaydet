# -*- coding: utf-8 -*-
"""Bahar Çiçek: çiçekçi. Krem + gül pembesi, Fraunces, buket kurucu (boy, ekstra, kart notu, canlı toplam)."""
import json
from common import *
IDX = 14
f = foto.F[IDX]
ph = lambda k, w=900: foto.url(f[k % len(f)], w)
BOY = [('Küçük', 450, 'Masa için'), ('Orta', 750, 'Hediye için'), ('Büyük', 1200, 'Gösterişli')]
EKS = [('Vazo', 250), ('Çikolata', 180), ('Peluş ayı', 220)]
KOL = [('Lale', 1), ('Gül', 2), ('Şakayık', 3), ('Papatya', 4), ('Orkide', 5), ('Mevsim karışımı', 6)]
CSS = '''
:root{--bg:#fbf6f1;--ink:#2e2a24;--mut:#7d7468;--ac:#e0607e;--ac2:#7a1f3a;--ln:rgba(46,42,36,.16);--hf:'Fraunces',Georgia,serif;--mono:'Nunito',sans-serif;--bf:'Nunito',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 18px/1.65 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:400;font-variation-settings:'SOFT' 100,'WONK' 1;line-height:1;letter-spacing:-.02em;overflow-wrap:break-word;min-width:0}
.btn{border-radius:50px;font-family:var(--bf);font-weight:800;font-size:16px;text-transform:none;letter-spacing:0}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;align-items:center;gap:28px;padding:18px clamp(20px,4vw,56px);color:var(--ink);transition:background .3s}nav.top.solid{background:rgba(251,246,241,.94);backdrop-filter:blur(8px)}
.lg{font:italic 400 30px var(--hf);text-decoration:none;margin-right:auto;color:var(--ac2)}
nav.top ul{display:flex;gap:28px;list-style:none;padding:0}nav.top li a{font:700 15px var(--bf);text-decoration:none}nav.top li a:hover{color:var(--ac)}
nav.top .btn{background:var(--ac);color:#fff;padding:12px 24px}
.hero{min-height:100svh;display:grid;grid-template-columns:1fr 1fr;align-items:center;gap:3vw;padding:110px clamp(20px,4vw,56px) 60px;max-width:1500px;margin:auto}
.hero h1{font-size:clamp(54px,7.4vw,124px)}.hero h1 em{color:var(--ac);font-style:italic}.hero p{max-width:26em;color:var(--mut);margin:22px 0 30px;font-size:19px}.hero .bt{display:flex;gap:12px;flex-wrap:wrap}.hero .btn.p{background:var(--ac2);color:#fff;padding:18px 32px}.hero .btn.g{border:2px solid var(--ink);background:transparent;color:var(--ink);padding:16px 28px}
.hero .im{position:relative;aspect-ratio:4/5;max-height:80vh;justify-self:end;width:min(100%,560px)}.hero .im img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border-radius:300px 300px 28px 28px}.hero .im img+img{inset:auto auto -30px -50px;width:44%;height:44%;border-radius:50%;border:8px solid var(--bg);aspect-ratio:1}
section.s{padding:min(15vh,140px) clamp(20px,4vw,56px) 4vh;max-width:1380px;margin:auto}
.hd{text-align:center;margin-bottom:5vh}.hd h2{font-size:clamp(42px,6vw,96px)}.hd h2 em{color:var(--ac)}.hd p{color:var(--mut);margin-top:12px}
.ms{columns:3;column-gap:18px}.ms figure{margin:0 0 18px;break-inside:avoid;position:relative;overflow:hidden;border-radius:24px}.ms figure:nth-child(odd){aspect-ratio:3/4}.ms figure:nth-child(even){aspect-ratio:1/1}.ms img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .8s}.ms figure:hover img{transform:scale(1.05)}.ms figcaption{position:absolute;left:14px;bottom:14px;background:var(--bg);border-radius:30px;padding:6px 16px;font-weight:800;font-size:15px}
.bk{display:grid;grid-template-columns:1fr 1fr;gap:20px;background:#fff;border-radius:44px;padding:clamp(24px,4vw,56px);box-shadow:0 30px 70px -40px rgba(122,31,58,.35)}.bk .im{aspect-ratio:1/1;border-radius:32px;overflow:hidden;position:relative}.bk .im img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:opacity .4s}
.bk .fm{display:grid;gap:22px;align-content:start}.bk .lb{font:800 14px var(--bf);color:var(--mut);margin-bottom:10px}.bk .op{display:flex;gap:8px;flex-wrap:wrap}.bk .op button{min-height:52px;padding:0 22px;border:2px solid var(--ln);border-radius:30px;background:transparent;color:var(--ink);font:700 16px var(--bf);cursor:pointer;transition:all .2s}.bk .op button:hover{border-color:var(--ac)}.bk .op button[aria-pressed=true]{background:var(--ac);border-color:var(--ac);color:#fff}
.bk textarea{width:100%;min-height:90px;border:2px solid var(--ln);border-radius:20px;padding:14px 18px;font:600 16px var(--bf);background:var(--bg);color:var(--ink);resize:vertical}.bk .cd{background:var(--bg);border:2px dashed var(--ac);border-radius:20px;padding:16px 20px;font:italic 400 22px/1.3 var(--hf);color:var(--ac2);min-height:70px}
.bk .tot{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;border-top:2px solid var(--ln);padding-top:20px}.bk .tot b{font:400 46px var(--hf)}.bk .tot small{display:block;color:var(--mut);font-weight:700;font-size:14px}.bk .btn.p{background:var(--ac2);color:#fff;padding:17px 30px;border:0;cursor:pointer}.bk .ok{display:none;background:#fde6ec;border-radius:16px;padding:14px 18px;font-weight:700;color:var(--ac2)}.bk .ok.on{display:block}
.vs{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:8vh}.vs div{background:#fff;border-radius:28px;padding:30px}.vs h3{font-size:30px;margin:6px 0 8px;color:var(--ac2)}.vs p{color:var(--mut)}.vs i{font:italic 400 44px var(--hf);color:var(--ac)}
footer{background:var(--ac2);color:#fff;border-radius:50px 50px 0 0;padding:70px clamp(24px,5vw,80px) 36px;margin-top:10vh;text-align:center;overflow:clip}footer b{font:italic 400 clamp(60px,12vw,170px)/1 var(--hf);display:block;color:#ffd4df}footer .ln{display:flex;gap:28px;justify-content:center;flex-wrap:wrap;margin:26px 0}footer a{color:#fff;text-decoration:none;font-weight:700}footer a:hover{color:#ffd4df}footer p{color:#e8b4c4;font-size:15px}
@media(max-width:860px){
nav.top ul,nav.top>.btn{display:none}nav.top{padding:12px 16px}nav.top .hm{border-radius:50%;margin-left:auto}
.hero{grid-template-columns:1fr;padding-top:90px}.hero .im{order:-1;max-height:46vh;width:78%;justify-self:center;aspect-ratio:1/1}.hero .im img{border-radius:200px 200px 24px 24px}.hero .im img+img{inset:auto auto -16px -16px;width:38%;height:38%}
.ms{columns:2;column-gap:10px}.bk,.vs{grid-template-columns:1fr}.bk{padding:20px;border-radius:32px}.bk .im{max-height:300px;aspect-ratio:4/3}
.mb{left:12px;right:12px;bottom:12px;background:var(--ac2);border:0;border-radius:50px;grid-template-columns:1fr 1fr 1.5fr;padding:5px;gap:4px}.mb a{min-height:50px;border-radius:40px;color:#fff;font:800 15px var(--bf);letter-spacing:0;text-transform:none}.mb a.p{background:var(--ac)}
.mm{background:#fbe1e8;color:var(--ac2);inset:0;padding:90px 26px 110px;--ln:rgba(122,31,58,.2);--ac:#7a1f3a;--mut:#a55b73}.mm a{font:italic 400 clamp(46px,14vw,76px)/1.15 var(--hf);color:var(--ac2);border-bottom:0;padding:6px 0}.mm small{color:var(--mut);font:700 14px var(--bf);text-transform:none;letter-spacing:0}
footer{border-radius:34px 34px 0 0;padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce;
 if(!rd){gsap.from('.hero h1',{y:50,opacity:0,duration:1,ease:'power3.out'});gsap.from('.hero .tx>*:not(h1),.hero .bt',{y:24,opacity:0,stagger:.1,duration:.8,delay:.4});gsap.from('.hero .im img',{scale:.88,opacity:0,duration:1.2,stagger:.2,ease:'power3.out'});
  gsap.to('.hero .im',{yPercent:-6,ease:'none',scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom top',scrub:true}});
  gsap.utils.toArray('.ms figure,.vs div,.hd').forEach(function(e,i){gsap.from(e,{y:50,opacity:0,duration:.8,delay:(i%3)*.08,scrollTrigger:{trigger:e,start:'top 92%'}})})}
 var b=1,k=0,ex={};function up(){var t=C.b[b][1]+Object.keys(ex).reduce(function(s,i){return s+C.e[i][1]},0);$('#tt').textContent=money(t);var imgs=C.i;$('#bi').src=imgs[k];$('#cd').textContent=$('#nt').value?'“'+$('#nt').value+'”':'Kart notun burada görünür.'}
 function mk(id,arr,fn,sel){$(id).innerHTML=arr.map(function(x,i){return '<button type="button" data-i="'+i+'" aria-pressed="'+sel(i)+'">'+x[0]+(x[1]&&id!='#kl'?' · '+money(x[1]):'')+'</button>'}).join('');$$(id+' button').forEach(function(bt){bt.onclick=function(){fn(+bt.dataset.i,bt)}})}
 mk('#bo',C.b,function(i){b=i;$$('#bo button').forEach(function(x,j){x.setAttribute('aria-pressed',j===i)});up()},function(i){return i==1});
 mk('#kl',C.k,function(i){k=i;$$('#kl button').forEach(function(x,j){x.setAttribute('aria-pressed',j===i)});up()},function(i){return i==0});
 mk('#ek',C.e,function(i,bt){if(ex[i]){delete ex[i]}else{ex[i]=1}bt.setAttribute('aria-pressed',!!ex[i]);up()},function(){return false});
 $('#nt').oninput=up;up();
 $('#ad').onclick=function(){var o=$('#ok');o.textContent=C.b[b][0]+' '+C.k[k][0].toLowerCase()+' buketin siparişe eklendi. Toplam '+$('#tt').textContent+'. Aynı gün teslimat için 15:00\\'e kadar sipariş ver.';o.classList.add('on')};
});
'''
def render():
    ms = ''.join('<figure><img src="%s" alt="%s buketi" loading="lazy"><figcaption>%s</figcaption></figure>' % (ph(k, 700), n, n) for n, k in KOL)
    body = f'''<div id="pre" role="status"><div><b>BAHAR</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">Bahar Çiçek</a><ul><li><a href="#koleksiyon">Çiçekler</a></li><li><a href="#buket">Buketini kur</a></li><li><a href="#teslimat">Teslimat</a></li></ul><a class="btn" href="#buket">Sipariş ver</a></nav>
<main><header class="hero" id="hero"><div class="tx"><h1>Bugün <em>çiçek</em> gitsin.</h1><p>Sabah toplanan çiçeklerle günlük buket. Ankara içinde aynı gün teslimat, kart notun elle yazılır.</p><div class="bt"><a class="btn p" href="#buket">Buketini kur</a><a class="btn g" href="#koleksiyon">Çiçeklere bak</a></div></div><div class="im"><img src="{ph(0, 1000)}" alt="Taze çiçek buketi" fetchpriority="high"><img src="{ph(7, 500)}" alt="Çiçek detay" loading="lazy"></div></header>
<section class="s" id="koleksiyon"><div class="hd"><h2>Bu hafta <em>tezgâhta</em></h2><p>Mevsimine göre değişir. Stoktaki çiçeği telefonla sorabilirsin.</p></div><div class="ms">{ms}</div></section>
<section class="s" id="buket"><div class="hd"><h2>Buketini <em>kur</em></h2></div><div class="bk"><div class="im"><img id="bi" src="" alt="Seçtiğin buket"></div><div class="fm"><div><div class="lb">Boy</div><div class="op" id="bo"></div></div><div><div class="lb">Çiçek</div><div class="op" id="kl"></div></div><div><div class="lb">Ekstra</div><div class="op" id="ek"></div></div><div><div class="lb">Kart notu</div><textarea id="nt" maxlength="90" aria-label="Kart notu" placeholder="İyi ki varsın."></textarea><div class="cd" id="cd"></div></div><div class="tot"><div><small>Toplam</small><b id="tt">0 ₺</b></div><button class="btn p" id="ad" type="button">Siparişe ekle</button></div><p class="ok" id="ok" aria-live="polite"></p></div></div>
<div class="vs" id="teslimat"><div><i>1</i><h3>Aynı gün</h3><p>15:00'e kadar verilen sipariş akşam elinde.</p></div><div><i>2</i><h3>Elle yazılı not</h3><p>Kartı dükkânda biz yazarız, mesajını gizli tutarız.</p></div><div><i>3</i><h3>Taze garanti</h3><p>Üç gün içinde solarsa buketi yenileriz.</p></div></div></section></main>
<footer><b>Bahar</b><div class="ln"><a href="#koleksiyon">Çiçekler</a><a href="#buket">Buketini kur</a><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div><p>Örnek Sok. Ankara · Her gün 08:00 - 20:00</p></footer>'''
    c = json.dumps(dict(b=BOY, e=EKS, k=[[n, 0] for n, _ in KOL], i=[ph(k, 900) for _, k in KOL]), ensure_ascii=False)
    return page('Bahar Çiçek', 'Aynı gün çiçek teslimatı. Buketini kendin kur.', ['Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,400,100,1;1,9..144,400,100,1', 'Nunito:wght@400;600;700;800'], BASE_CSS + CSS, body, JS, c, dict(cta=['Sipariş ver', '#buket'], addr='Örnek Sok. · Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/bahar', exist_ok=True); open(R + '/bahar/index.html', 'w', encoding='utf-8').write(render()); print('bahar ok')
