# -*- coding: utf-8 -*-
"""Pırıl Temizlik: temizlik şirketi. Nane yeşili, yuvarlak balonlar; m² kaydırıcı + sıklık ile canlı fiyat, kontrol listesi."""
import json
from common import *
IDX = 4
f = foto.F[IDX]
ph = lambda k, w=800: foto.url(f[k % len(f)], w)
HIZ = {'Ev temizliği': 9, 'Ofis temizliği': 7, 'İnşaat sonrası': 14, 'Cam ve cephe': 11}
SIK = {'Tek seferlik': 1.0, 'Aylık': 0.9, 'Haftalık': 0.8}
CSS = '''
:root{--bg:#f3faf7;--ink:#0e3b43;--mut:#527077;--ac:#58c4a3;--ac2:#0e3b43;--ln:rgba(14,59,67,.14);--hf:'Nunito',system-ui,sans-serif;--mono:'Nunito',sans-serif;--bf:'Nunito',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:600 18px/1.6 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:900;letter-spacing:-.03em;line-height:1.02;overflow-wrap:break-word;min-width:0}
.btn{border-radius:60px;font-family:var(--bf);font-weight:900;font-size:17px;text-transform:none;letter-spacing:0}
nav.top{position:fixed;top:14px;left:14px;right:14px;z-index:50;display:flex;align-items:center;gap:22px;padding:10px 10px 10px 26px;border-radius:60px;background:rgba(255,255,255,.9);backdrop-filter:blur(12px);box-shadow:0 12px 36px -20px rgba(14,59,67,.5);color:var(--ink)}
.lg{font:900 25px var(--hf);letter-spacing:-.04em;text-decoration:none;margin-right:auto}.lg b{color:var(--ac)}
nav.top ul{display:flex;gap:24px;list-style:none;padding:0}nav.top li a{font:800 15px var(--bf);text-decoration:none}nav.top li a:hover{color:var(--ac)}nav.top .btn{background:var(--ink);color:#fff;padding:13px 24px}
.hero{min-height:100svh;display:grid;grid-template-columns:1fr 1fr;align-items:center;gap:3vw;padding:120px clamp(20px,4vw,56px) 60px;max-width:1500px;margin:auto}
.hero h1{font-size:clamp(52px,7.4vw,124px)}.hero h1 em{font-style:normal;color:var(--ac)}.hero p{max-width:26em;color:var(--mut);margin:20px 0 28px;font-size:19px}.hero .bt{display:flex;gap:10px;flex-wrap:wrap}.hero .btn.p{background:var(--ac);color:var(--ink);padding:18px 32px}.hero .btn.g{border:3px solid var(--ink);background:transparent;color:var(--ink);padding:15px 28px}
.bb{position:relative;aspect-ratio:1/1;max-height:78vh;justify-self:end;width:min(100%,600px)}.bb div{position:absolute;border-radius:50%;overflow:hidden}.bb img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.bb .a{inset:0 18% 22% 0;animation:fl 9s ease-in-out infinite}.bb .b{inset:46% 0 0 40%;border:10px solid var(--bg);animation:fl 7s ease-in-out infinite reverse}.bb .c{inset:2% 2% auto auto;width:30%;aspect-ratio:1;border:8px solid var(--bg);animation:fl 8s ease-in-out infinite}
@keyframes fl{50%{transform:translateY(-14px)}}
section.s{padding:min(14vh,130px) clamp(20px,4vw,56px) 4vh;max-width:1380px;margin:auto}
.hd{text-align:center;margin-bottom:5vh}.hd h2{font-size:clamp(40px,5.8vw,92px)}.hd h2 em{font-style:normal;color:var(--ac)}.hd p{color:var(--mut);margin-top:12px}
.cc{display:grid;grid-template-columns:1.1fr .9fr;gap:20px}.cc .fm{background:#fff;border-radius:40px;padding:clamp(24px,4vw,52px);display:grid;gap:26px}.cc .lb{font:900 15px var(--bf);color:var(--mut);margin-bottom:10px;display:flex;justify-content:space-between}.cc .lb b{color:var(--ink);font-size:20px}
.cc .op{display:flex;gap:8px;flex-wrap:wrap}.cc .op button{min-height:50px;padding:0 22px;border:3px solid var(--ln);border-radius:40px;background:transparent;color:var(--ink);font:800 16px var(--bf);cursor:pointer;transition:all .2s}.cc .op button:hover{border-color:var(--ac)}.cc .op button[aria-pressed=true]{background:var(--ink);border-color:var(--ink);color:#fff}
input[type=range]{width:100%;height:44px;accent-color:var(--ac);cursor:pointer}
.cc .rs{background:var(--ink);color:#fff;border-radius:40px;padding:clamp(24px,4vw,52px);display:flex;flex-direction:column;justify-content:center;gap:12px}.cc .rs small{color:#9fd9c9;font-weight:800}.cc .rs b{font:900 clamp(56px,7vw,100px)/1 var(--hf);color:var(--ac)}.cc .rs p{color:#bfe6da}.cc .rs .btn{background:var(--ac);color:var(--ink);padding:17px 28px;align-self:flex-start;margin-top:8px}
.ck{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:8vh;align-items:center}.ck .im{aspect-ratio:4/3;border-radius:40px;overflow:hidden;position:relative}.ck img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .8s}.ck .im:hover img{transform:scale(1.04)}
.ck ul{list-style:none;padding:0;display:grid;gap:10px}.ck li{background:#fff;border-radius:22px;padding:16px 22px;display:flex;align-items:center;gap:14px;font-weight:800;cursor:pointer;transition:background .2s}.ck li:before{content:'';width:26px;height:26px;border-radius:50%;border:3px solid var(--ac);flex:none;transition:background .2s}.ck li.on{background:#dff5ed;text-decoration:line-through;text-decoration-color:var(--ac)}.ck li.on:before{background:var(--ac)}
.cl{margin:8vh clamp(14px,3vw,40px) 0;background:var(--ac);border-radius:48px;padding:clamp(30px,5vw,70px);display:grid;grid-template-columns:1fr 1fr;gap:5vw;align-items:center}.cl h2{font-size:clamp(40px,5.6vw,90px)}.cl form{display:grid;gap:10px}.cl input,.cl select{min-height:56px;border:0;border-radius:40px;padding:0 24px;font:800 17px var(--bf);background:#fff;color:var(--ink)}.cl .btn{background:var(--ink);color:#fff;min-height:58px;border:0;cursor:pointer}.cl .ok{display:none;background:#fff;padding:14px 20px;border-radius:24px;font-weight:800}.cl .ok.on{display:block}
footer{background:var(--ink);color:#fff;border-radius:56px 56px 0 0;padding:70px clamp(24px,5vw,80px) 36px;margin-top:8vh;display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px}footer b{font:900 30px var(--hf);letter-spacing:-.04em;color:var(--ac)}footer a{display:block;color:#fff;text-decoration:none;padding:3px 0}footer a:hover{color:var(--ac)}footer p{color:#9fd9c9}
@media(max-width:860px){
nav.top ul,nav.top>.btn{display:none}nav.top{padding:8px 8px 8px 20px;top:10px;left:10px;right:10px}nav.top .hm{margin-left:auto;border-radius:50%}
.hero{grid-template-columns:1fr;padding-top:90px}.bb{order:-1;max-height:44vh;width:76%;justify-self:center}.cc,.ck,.cl,footer{grid-template-columns:1fr}
.mb{left:12px;right:12px;bottom:12px;background:var(--ink);border:0;border-radius:60px;grid-template-columns:1fr 1fr 1.5fr;padding:5px;gap:4px}.mb a{min-height:50px;border-radius:50px;color:#fff;font:900 15px var(--bf);letter-spacing:0;text-transform:none}.mb a+a{border:0}.mb a.p{background:var(--ac);color:var(--ink)}
.mm{background:var(--ac);color:var(--ink);inset:10px;border-radius:40px;padding:90px 24px 110px;--ln:rgba(14,59,67,.25);--ac:#0e3b43;--mut:#1e6a5d}.mm a{font:900 clamp(40px,13vw,66px)/1.1 var(--hf);letter-spacing:-.04em;color:var(--ink);border-bottom:0;padding:8px 0}.mm small{color:var(--ac2);font:800 14px var(--bf);text-transform:none;letter-spacing:0}
footer{border-radius:36px 36px 0 0;padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce;
 if(!rd){gsap.from('.hero .tx>*',{y:40,opacity:0,stagger:.1,duration:.9,ease:'back.out(1.4)'});gsap.from('.bb>div',{scale:.6,opacity:0,duration:1,stagger:.18,ease:'back.out(1.6)'});
  gsap.utils.toArray('.hd,.ck li,.cc>*,.cl').forEach(function(e,i){gsap.from(e,{y:46,opacity:0,duration:.8,delay:(i%3)*.07,scrollTrigger:{trigger:e,start:'top 92%'}})})}
 var h='Ev temizliği',s='Tek seferlik';function up(){var m=+$('#m').value;$('#mv').textContent=m+' m²';var p=Math.round(m*C.h[h]*C.s[s]/10)*10;$('#pt').textContent=money(p);$('#pn2').textContent=h+', '+s.toLowerCase()+', '+m+' m²'}
 function mk(id,obj,cb){$(id).innerHTML=Object.keys(obj).map(function(k,i){return '<button type="button" aria-pressed="'+(i==0)+'">'+k+'</button>'}).join('');$$(id+' button').forEach(function(b){b.onclick=function(){$$(id+' button').forEach(function(x){x.setAttribute('aria-pressed',x===b)});cb(b.textContent);up()}})}
 mk('#hz',C.h,function(v){h=v});mk('#sk',C.s,function(v){s=v});$('#m').oninput=up;up();
 $$('.ck li').forEach(function(l){l.onclick=function(){l.classList.toggle('on')}});
 $('#fm').onsubmit=function(e){e.preventDefault();var o=$('#fo');o.textContent='Teşekkürler '+$('#fn').value+'. '+$('#fk').value+' için teklifini hazırlayıp seni arayacağız.';o.classList.add('on')};
});
'''
def render():
    ck = ''.join('<li>%s</li>' % x for x in ['Mutfak tezgâh ve dolap içleri', 'Banyo derz ve armatür', 'Tüm zemin süpürme ve silme', 'Cam ve çerçeveler', 'Mobilya üstleri ve toz alma', 'Çöpler ve geri dönüşüm'])
    opt = ''.join('<option>%s</option>' % k for k in HIZ)
    body = f'''<div id="pre" role="status"><div><b>PIRIL</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">Pırıl<b>.</b></a><ul><li><a href="#hesap">Fiyat hesapla</a></li><li><a href="#liste">Neler yapılır</a></li><li><a href="#teklif">Teklif al</a></li></ul><a class="btn" href="#teklif">Teklif al</a></nav>
<main><header class="hero" id="hero"><div class="tx"><h1>Eviniz <em>pırıl pırıl</em> olsun.</h1><p>Ev, ofis ve inşaat sonrası temizlik. Sigortalı ekip, kendi malzememiz, işi kontrol listesiyle teslim ederiz.</p><div class="bt"><a class="btn p" href="#hesap">Fiyatı hesapla</a><a class="btn g" href="#teklif">Teklif al</a></div></div><div class="bb"><div class="a"><img src="{ph(0, 1000)}" alt="Temizlik görevlisi mutfağı siliyor" fetchpriority="high"></div><div class="b"><img src="{ph(1, 700)}" alt="Parlayan yüzey" loading="lazy"></div><div class="c"><img src="{ph(2, 400)}" alt="Temizlik malzemeleri" loading="lazy"></div></div></header>
<section class="s" id="hesap"><div class="hd"><h2>Kaç para <em>tutar?</em></h2><p>Metrekareyi ve sıklığı seç, tahmini tutarı gör.</p></div><div class="cc"><div class="fm"><div><div class="lb">Hizmet</div><div class="op" id="hz"></div></div><div><div class="lb">Alan <b id="mv"></b></div><input id="m" type="range" min="30" max="400" step="5" value="100" aria-label="Metrekare"></div><div><div class="lb">Sıklık</div><div class="op" id="sk"></div></div></div><div class="rs"><small>Tahmini tutar</small><b id="pt"></b><p id="pn2"></p><a class="btn" href="#teklif">Bu teklifi iste</a></div></div></section>
<section class="s" id="liste"><div class="hd"><h2>Her temizlikte <em>bunlar</em> var</h2><p>Bir maddeye dokun, tamamlandı say.</p></div><div class="ck"><div class="im"><img src="{ph(3, 1000)}" alt="Temiz salon" loading="lazy"></div><ul>{ck}</ul></div></section>
<section class="cl" id="teklif"><div><h2>Ücretsiz<br>teklif al.</h2></div><form id="fm"><input id="fn" required placeholder="Adınız" aria-label="Adınız" autocomplete="name"><select id="fk" aria-label="Hizmet">{opt}</select><button class="btn" type="submit">Teklif iste</button><p class="ok" id="fo" aria-live="polite"></p></form></section></main>
<footer><div><b>Pırıl Temizlik</b><p>Ev ve ofis temizliği · Ankara</p></div><div><p>Sayfalar</p><a href="#hesap">Fiyat hesapla</a><a href="#liste">Neler yapılır</a><a href="#teklif">Teklif al</a></div><div><p>İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div></footer>'''
    c = json.dumps(dict(h=HIZ, s=SIK), ensure_ascii=False)
    return page('Pırıl Temizlik', 'Ev, ofis ve inşaat sonrası temizlik. Fiyatı hemen hesapla.', ['Nunito:wght@600;700;800;900'], BASE_CSS + CSS, body, JS, c, dict(cta=['Teklif al', '#teklif'], addr='Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/piril', exist_ok=True); open(R + '/piril/index.html', 'w', encoding='utf-8').write(render()); print('piril ok')
