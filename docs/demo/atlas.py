# -*- coding: utf-8 -*-
"""Atlas Butik: giyim butiği. Siyah + altın, serif; yatay lookbook, ürün seçici (beden/renk) ve sepet sayacı."""
import json
from common import *
IDX = 13
f = foto.F[IDX]
ph = lambda k, w=900: foto.url(f[k % len(f)], w)
URUN = [('Keten gömlek', 1850, ['Ekru', 'Zeytin', 'Siyah'], 1), ('Yün palto', 6900, ['Gri', 'Camel'], 2), ('Triko kazak', 2400, ['Krem', 'Lacivert', 'Bordo'], 3), ('Deri ceket', 8900, ['Siyah', 'Kahve'], 4), ('İpek bluz', 2750, ['Fildişi', 'Pudra'], 5), ('Pamuklu pantolon', 2100, ['Bej', 'Siyah'], 6)]
BED = ['XS', 'S', 'M', 'L', 'XL']
CSS = '''
:root{--bg:#f6f4f0;--ink:#151515;--mut:#6f6a60;--ac:#b08d57;--ac2:#151515;--ln:rgba(21,21,21,.18);--hf:'Playfair Display',Georgia,serif;--mono:'Inter',sans-serif;--bf:'Inter',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 16px/1.65 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:400;letter-spacing:-.02em;line-height:1;overflow-wrap:break-word;min-width:0}
.btn{border-radius:0;font-family:var(--bf);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:600}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;padding:20px clamp(20px,4vw,56px);color:#fff;transition:background .3s,color .3s}nav.top.solid{background:var(--bg);color:var(--ink);border-bottom:1px solid var(--ln)}
nav.top ul{display:flex;gap:28px;list-style:none;padding:0}nav.top li a{font:500 12px var(--bf);text-transform:uppercase;letter-spacing:.16em;text-decoration:none}
.lg{font:400 30px var(--hf);letter-spacing:.2em;text-transform:uppercase;text-decoration:none}.cr{justify-self:end;font:500 12px var(--bf);text-transform:uppercase;letter-spacing:.16em;display:flex;gap:10px;align-items:center}.cr b{background:var(--ac);color:#fff;border-radius:50%;width:24px;height:24px;display:grid;place-items:center;font-size:12px}
.hero{height:100svh;min-height:620px;position:relative;color:#fff;display:flex;align-items:flex-end;padding:0 clamp(20px,4vw,56px) 9vh;overflow:clip}.hero>img{position:absolute;inset:-6% 0;width:100%;height:112%;object-fit:cover}.hero:after{content:'';position:absolute;inset:0;background:linear-gradient(0deg,rgba(21,21,21,.75),rgba(21,21,21,.1) 55%,rgba(21,21,21,.35))}
.hero .c{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:end;gap:30px;width:100%;flex-wrap:wrap}.hero h1{font-size:clamp(54px,9vw,150px);font-style:italic;max-width:9em}.hero p{max-width:20em;margin-bottom:20px}.hero .btn{display:inline-block;background:#fff;color:var(--ink);padding:17px 34px}
section.s{padding:min(15vh,140px) clamp(20px,4vw,56px) 4vh;max-width:1500px;margin:auto}
.hd{display:flex;justify-content:space-between;align-items:end;gap:20px;flex-wrap:wrap;margin-bottom:5vh;border-bottom:1px solid var(--ink);padding-bottom:20px}.hd h2{font-size:clamp(40px,5.6vw,88px)}.hd small{font:500 12px var(--bf);text-transform:uppercase;letter-spacing:.16em;color:var(--mut)}
.lb{height:100svh;position:relative;overflow:hidden}.lb .tr{display:flex;height:100%;width:max-content}.lb .pn{width:min(78vw,900px);height:100%;position:relative;flex:none;border-right:1px solid var(--bg)}.lb .pn img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.lb .pn span{position:absolute;left:24px;bottom:24px;color:#fff;font:italic 400 clamp(34px,4vw,60px) var(--hf);z-index:2;text-shadow:0 2px 20px rgba(0,0,0,.4)}
.lb .intro{width:min(46vw,560px);flex:none;background:var(--ink);color:#fff;padding:clamp(30px,4vw,60px);display:flex;flex-direction:column;justify-content:flex-end}.lb .intro h2{font-size:clamp(46px,6vw,96px);font-style:italic}.lb .intro p{color:#bdb6a6;margin-top:16px}
.gr{display:grid;grid-template-columns:repeat(3,1fr);gap:40px 22px}.gr article{cursor:pointer}.gr .im{aspect-ratio:3/4;position:relative;overflow:hidden;background:#e8e3da}.gr img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .8s}.gr article:hover img{transform:scale(1.04)}
.gr h3{font-size:24px;margin-top:14px}.gr p{display:flex;justify-content:space-between;color:var(--mut);margin-top:4px}.gr article[aria-selected=true] h3{text-decoration:underline;text-decoration-color:var(--ac);text-underline-offset:6px}
.sel{position:sticky;bottom:18px;z-index:20;background:var(--ink);color:#fff;display:grid;grid-template-columns:1fr auto auto auto;gap:24px;align-items:center;padding:18px 26px;margin-top:6vh}.sel b{font:italic 400 28px var(--hf)}.sel small{display:block;color:#bdb6a6;font-size:13px}
.sel .op{display:flex;gap:6px;flex-wrap:wrap}.sel .op button{min-width:44px;min-height:44px;padding:0 12px;border:1px solid rgba(255,255,255,.35);background:transparent;color:#fff;font:600 13px var(--bf);cursor:pointer;transition:all .2s}.sel .op button:hover{border-color:var(--ac)}.sel .op button[aria-pressed=true]{background:var(--ac);border-color:var(--ac)}
.sel .btn{background:#fff;color:var(--ink);min-height:48px;padding:0 26px;border:0;cursor:pointer}.sel .btn.ad{background:var(--ac);color:#fff}
.nw{display:grid;grid-template-columns:1fr 1fr;min-height:70vh}.nw .im{position:relative;overflow:hidden}.nw img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.nw .tx{background:var(--ac);color:#fff;padding:clamp(30px,6vw,90px);display:flex;flex-direction:column;justify-content:center;gap:20px}.nw h2{font-size:clamp(42px,5.4vw,84px);font-style:italic}.nw form{display:flex;gap:0;max-width:30em}.nw input{flex:1;min-height:54px;border:0;border-bottom:1px solid #fff;background:transparent;color:#fff;font:500 16px var(--bf);min-width:0}.nw input::placeholder{color:#f0e3cb}.nw .btn{background:var(--ink);color:#fff;border:0;padding:0 24px;cursor:pointer}.nw .ok{display:none}.nw .ok.on{display:block}
footer{background:var(--ink);color:#fff;padding:70px clamp(20px,4vw,56px) 30px;text-align:center}footer b{font:400 clamp(40px,8vw,110px) var(--hf);letter-spacing:.2em;text-transform:uppercase;display:block}footer .ln{display:flex;gap:30px;justify-content:center;flex-wrap:wrap;margin:30px 0}footer a{color:#fff;text-decoration:none;font:500 12px var(--bf);text-transform:uppercase;letter-spacing:.16em}footer a:hover{color:var(--ac)}footer p{color:#bdb6a6;font-size:14px}
@media(max-width:860px){
nav.top{grid-template-columns:auto 1fr auto;padding:12px 16px}nav.top ul{display:none}nav.top .lg{font-size:24px}nav.top .hm{border-radius:0}.cr{order:2;justify-self:end;margin-right:10px}
.lb{height:auto}.lb .tr{flex-direction:column;width:auto;height:auto}.lb .pn,.lb .intro{width:100%;height:60vh;border:0}.lb .intro{height:auto;padding:60px 22px}
.gr{grid-template-columns:1fr 1fr;gap:26px 12px}.sel{grid-template-columns:1fr 1fr;bottom:76px;padding:14px}.sel>div:first-child{grid-column:1/-1}.sel .op{grid-column:1/-1}.nw{grid-template-columns:1fr}.nw .im{min-height:40vh}
.mb{left:0;right:0;bottom:0;background:var(--bg);border:0;border-top:1px solid var(--ink);border-radius:0;grid-template-columns:1fr 1fr 1.3fr;padding:0 0 max(0px,env(safe-area-inset-bottom))}.mb a{min-height:58px;border-radius:0;color:var(--ink);font:500 11px var(--bf);letter-spacing:.16em;text-transform:uppercase}.mb a+a{border-left:1px solid var(--ln)}.mb a.p{background:var(--ink);color:#fff}
.mm{background:var(--bg);color:var(--ink);inset:0;padding:100px 28px 110px;--ln:rgba(21,21,21,.18);--ac:#b08d57;--mut:#6f6a60}.mm a{font:italic 400 clamp(44px,14vw,76px)/1.15 var(--hf);color:var(--ink);border-bottom:1px solid var(--ln);padding:8px 0}.mm small{color:var(--mut);font:500 11px var(--bf);letter-spacing:.2em}
footer{padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce,mob=matchMedia('(max-width:860px)').matches;
 if(!rd){gsap.from('.hero h1',{y:60,opacity:0,duration:1.2,ease:'power3.out'});gsap.from('.hero .c>*:not(h1)',{opacity:0,y:20,duration:.8,delay:.6});gsap.to('.hero>img',{yPercent:10,ease:'none',scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom top',scrub:true}});
  if(!mob){var tr=$('.lb .tr');gsap.to(tr,{x:function(){return -(tr.scrollWidth-innerWidth)},ease:'none',scrollTrigger:{trigger:'.lb',start:'top top',end:function(){return '+='+(tr.scrollWidth-innerWidth)},pin:true,scrub:.6,invalidateOnRefresh:true}})}
  gsap.utils.toArray('.gr article').forEach(function(e,i){gsap.from(e,{y:60,opacity:0,duration:.9,delay:(i%3)*.1,scrollTrigger:{trigger:e,start:'top 92%'}})})}
 var cur=0,col=0,sz='M',n=0;function pick(i){cur=i;col=0;$$('.gr article').forEach(function(a,j){a.setAttribute('aria-selected',j===i)});var u=C.u[i];$('#sn').textContent=u[0];$('#sp').textContent=money(u[1]);$('#sc').innerHTML=u[2].map(function(c,j){return '<button type="button" aria-pressed="'+(j==0)+'" data-j="'+j+'">'+c+'</button>'}).join('');$$('#sc button').forEach(function(b){b.onclick=function(){col=+b.dataset.j;$$('#sc button').forEach(function(x){x.setAttribute('aria-pressed',x===b)})}})}
 $$('.gr article').forEach(function(a,i){a.onclick=function(){pick(i)}});pick(0);
 $$('#sz button').forEach(function(b){b.onclick=function(){sz=b.textContent;$$('#sz button').forEach(function(x){x.setAttribute('aria-pressed',x===b)})}});
 $('#ad').onclick=function(){n++;$('#cn').textContent=n;this.textContent='Sepete eklendi ('+C.u[cur][2][col]+', '+sz+')';var t=this;setTimeout(function(){t.textContent='Sepete ekle'},1600)};
 $('#fm').onsubmit=function(e){e.preventDefault();var o=$('#fo');o.textContent='Teşekkürler, yeni koleksiyonu ilk sen göreceksin.';o.classList.add('on')};
});
'''
def render():
    gr = ''.join('<article aria-selected="false"><div class="im"><img src="%s" alt="%s" loading="lazy"></div><h3>%s</h3><p><span>%s renk</span><b>%s</b></p></article>' % (ph(k + 6, 700), n, n, len(c), '{:,}'.format(p).replace(',', '.') + ' ₺') for n, p, c, k in URUN)
    sz = ''.join('<button type="button" aria-pressed="%s">%s</button>' % ('true' if s == 'M' else 'false', s) for s in BED)
    body = f'''<div id="pre" role="status"><div><b>ATLAS</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><ul><li><a href="#koleksiyon">Koleksiyon</a></li><li><a href="#lookbook">Lookbook</a></li></ul><a class="lg" href="#">Atlas</a><div class="cr">Sepet <b id="cn">0</b></div></nav>
<main><header class="hero" id="hero"><img src="{ph(0, 1800)}" alt="Butik koleksiyonundan bir kombin" fetchpriority="high"><div class="c"><h1>Kış koleksiyonu geldi.</h1><div><p>Doğal kumaş, sade kesim. Ankara'daki butiğimizde deneyin, istediğiniz yere gönderelim.</p><a class="btn" href="#koleksiyon">Koleksiyonu gör</a></div></div></header>
<section class="lb" id="lookbook"><div class="tr"><div class="intro"><h2>Lookbook</h2><p>Bu sezonun üç kombini. Kaydırın.</p></div><div class="pn"><img src="{ph(1, 1400)}" alt="Palto ile kombin" loading="lazy"><span>Şehir</span></div><div class="pn"><img src="{ph(2, 1400)}" alt="Keten gömlekle kombin" loading="lazy"><span>Hafta sonu</span></div><div class="pn"><img src="{ph(3, 1400)}" alt="Akşam kombini" loading="lazy"><span>Akşam</span></div></div></section>
<section class="s" id="koleksiyon"><div class="hd"><h2>Koleksiyon</h2><small>Ürüne dokun, beden ve rengi seç</small></div><div class="gr">{gr}</div>
<div class="sel"><div><b id="sn"></b><small id="sp"></small></div><div class="op" id="sc" aria-label="Renk"></div><div class="op" id="sz" aria-label="Beden">{sz}</div><button class="btn ad" id="ad" type="button">Sepete ekle</button></div></section>
<section class="nw"><div class="im"><img src="{ph(4, 1200)}" alt="Butik içi" loading="lazy"></div><div class="tx"><h2>Yeni gelenleri ilk sen gör.</h2><form id="fm"><input type="email" required placeholder="E-posta" aria-label="E-posta"><button class="btn" type="submit">Katıl</button></form><p class="ok" id="fo" aria-live="polite"></p></div></section></main>
<footer><b>Atlas</b><div class="ln"><a href="#koleksiyon">Koleksiyon</a><a href="#lookbook">Lookbook</a><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div><p>Örnek Cad. Ankara · Pzt-Cmt 10:00 - 20:00</p></footer>'''
    c = json.dumps(dict(u=[[n, p, c_] for n, p, c_, k in URUN]), ensure_ascii=False)
    return page('Atlas Butik', 'Doğal kumaş, sade kesim. Ankara butik giyim.', ['Playfair+Display:ital,wght@0,400;1,400', 'Inter:wght@400;500;600'], BASE_CSS + CSS, body, JS, c, dict(cta=['Koleksiyon', '#koleksiyon'], addr='Örnek Cad. · Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/atlas', exist_ok=True); open(R + '/atlas/index.html', 'w', encoding='utf-8').write(render()); print('atlas ok')
