# -*- coding: utf-8 -*-
"""Fırın 1923: pastane. Açık, sıcak; kart halinde başlayıp ekranı kaplayan video, filtreli ürünler + sepet çekmecesi, yazılı pasta tasarımcısı, yatay vitrin."""
import html as H, json
from common import *
IDX = 15
f = foto.F[IDX]
ph = lambda k, w=800: foto.url(f[k % len(f)], w)
VURL, POSTER = foto.video(IDX)
CATS = ['Hepsi', 'Ekmek', 'Börek', 'Tatlı', 'Pasta']
PROD = [  # ad, kategori, fiyat, foto no
 ('Köy ekmeği', 'Ekmek', 60, 0), ('Simit (6’lı)', 'Ekmek', 90, 1), ('Su böreği (dilim)', 'Börek', 120, 2), ('Peynirli poğaça (4’lü)', 'Börek', 110, 3),
 ('Tereyağlı kurabiye (500 g)', 'Tatlı', 320, 4), ('Profiterol (porsiyon)', 'Tatlı', 150, 5), ('Baklava (kutu)', 'Tatlı', 480, 6), ('Cheesecake (dilim)', 'Tatlı', 140, 7),
 ('Doğum günü pastası (8 kişilik)', 'Pasta', 1450, 8), ('Meyveli tart (6 kişilik)', 'Pasta', 780, 9),
]
CSS = '''
:root{--bg:#f6efe4;--ink:#2a1810;--mut:#6b5648;--ac:#b9611a;--ac2:#3a2418;--card:#fffaf1;--ln:rgba(42,24,16,.16);--hf:'DM Serif Display',Georgia,serif;--mono:'DM Mono',monospace;--bf:'Figtree',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 17px/1.55 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:400;line-height:1;letter-spacing:-.01em;overflow-wrap:break-word;min-width:0}
.lb{font:500 12px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--mut)}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;justify-content:space-between;align-items:center;padding:18px clamp(18px,4vw,48px);transition:background .3s,backdrop-filter .3s,color .3s;color:var(--ink)}
nav.top.ond{color:#fff}
nav.top.solid{background:rgba(246,239,228,.9);backdrop-filter:blur(10px);padding-block:12px;color:var(--ink)}
.lg{font:400 28px/1 var(--hf);text-decoration:none}nav.top ul{display:flex;gap:26px;list-style:none;padding:0}nav.top li a{font:500 13px var(--mono);letter-spacing:.08em;text-transform:uppercase;text-decoration:none}nav.top li a:hover{color:var(--ac)}
.cartbtn{position:relative;min-height:46px;padding:0 18px;border:1.5px solid currentColor;background:transparent;color:inherit;font:500 13px var(--mono);letter-spacing:.08em;text-transform:uppercase;cursor:pointer}
.cartbtn b{display:inline-grid;place-items:center;min-width:22px;height:22px;margin-left:8px;border-radius:11px;background:var(--ac);color:#fff;font-size:12px}
/* hero: kart büyür */
#hero{position:relative;height:340vh}.stage{position:sticky;top:0;height:100svh;overflow:hidden;background:var(--bg);display:grid;place-items:center}
.win{position:absolute;inset:0;margin:auto;width:46vw;height:56vh;border-radius:28px;overflow:hidden;background:#000;will-change:width,height,border-radius}
.win video,.win .poster{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.win:after{content:'';position:absolute;inset:0;background:rgba(30,15,5,.28)}
.tt{position:absolute;z-index:3;inset:0;display:grid;place-items:center;text-align:center;pointer-events:none;padding:0 18px;color:#fff;mix-blend-mode:difference}
.tt h1{font-size:clamp(46px,10.5vw,170px)}.tt p{font:500 13px var(--mono);letter-spacing:.14em;text-transform:uppercase;margin-top:18px}
.cap{position:absolute;z-index:4;left:0;right:0;bottom:12vh;text-align:center;color:#fff;opacity:0;transform:translateY(24px);transition:opacity .5s,transform .6s;padding:0 18px}.cap.on{opacity:1;transform:none}
.cap h2{font-size:clamp(40px,8vw,120px);text-shadow:0 4px 40px rgba(0,0,0,.45)}.cap p{font:500 13px var(--mono);letter-spacing:.14em;text-transform:uppercase;margin-top:12px}
.sc{position:absolute;z-index:3;left:50%;bottom:4vh;transform:translateX(-50%);font:500 11px var(--mono);letter-spacing:.2em;color:var(--mut)}
/* menü */
.mn{padding:14vh clamp(18px,4vw,64px) 8vh;max-width:1400px;margin:auto}.mn>h2{font-size:clamp(44px,8vw,120px)}.mn>p{color:var(--mut);margin-top:12px}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:5vh 0 24px}.chips button{min-height:46px;padding:0 20px;border-radius:30px;border:1.5px solid var(--ink);background:transparent;color:var(--ink);font:500 13px var(--mono);letter-spacing:.06em;text-transform:uppercase;cursor:pointer;transition:background .15s,color .15s}
.chips button[aria-pressed=true]{background:var(--ink);color:var(--bg)}.chips button:hover{background:var(--ac2);color:var(--bg)}
.gr{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:20px}
.pc{background:var(--card);border-radius:18px;overflow:hidden;border:1px solid var(--ln);display:flex;flex-direction:column;transition:transform .25s,box-shadow .25s}.pc:hover{transform:translateY(-4px);box-shadow:0 18px 40px -22px rgba(58,36,24,.5)}
.pc.hide{display:none}.pc .im{aspect-ratio:4/3;overflow:hidden;background:#e7dccb}.pc img{width:100%;height:100%;object-fit:cover;transition:transform .8s}.pc:hover img{transform:scale(1.05)}
.pc .tx{padding:16px 18px 18px;display:grid;gap:6px;flex:1}.pc h3{font-size:24px}.pc .pr{font:500 16px var(--mono)}
.pc .ad{margin-top:auto;min-height:46px;border:0;border-radius:30px;background:var(--ink);color:var(--bg);font:500 13px var(--mono);letter-spacing:.06em;text-transform:uppercase;cursor:pointer;transition:background .15s,transform .15s}.pc .ad:hover{background:var(--ac)}.pc .ad:active{transform:scale(.97)}
/* çekmece */
.dr{position:fixed;z-index:90;top:0;right:0;bottom:0;width:min(440px,100%);background:var(--card);box-shadow:-20px 0 60px rgba(0,0,0,.25);transform:translateX(105%);transition:transform .45s cubic-bezier(.2,.8,.2,1);display:flex;flex-direction:column;padding:22px}
.dr.on{transform:none}.dr header{display:flex;justify-content:space-between;align-items:center}.dr h3{font-size:34px}.dr .x{width:46px;height:46px;border:1.5px solid var(--ink);background:transparent;font-size:20px;cursor:pointer;border-radius:50%}
.dr ul{list-style:none;padding:0;margin:16px 0;overflow:auto;flex:1;display:grid;gap:10px;align-content:start}.dr li{display:grid;grid-template-columns:1fr auto;gap:6px 10px;padding:12px 0;border-bottom:1px solid var(--ln)}
.dr li b{font:500 14px var(--mono)}.dr .q{display:flex;gap:6px;align-items:center}.dr .q button{width:34px;height:34px;border-radius:50%;border:1.5px solid var(--ink);background:transparent;cursor:pointer;font-size:16px}
.dr .em{color:var(--mut)}.tg{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}.tg button{min-height:46px;border:1.5px solid var(--ink);background:transparent;font:500 13px var(--mono);text-transform:uppercase;cursor:pointer}.tg button[aria-pressed=true]{background:var(--ink);color:var(--bg)}
.dr .tot{display:flex;justify-content:space-between;font:500 22px var(--mono);margin-bottom:14px}.dr .btn{width:100%}.ov{position:fixed;inset:0;z-index:80;background:rgba(30,15,5,.45);opacity:0;pointer-events:none;transition:opacity .3s}.ov.on{opacity:1;pointer-events:auto}
.dr .ok{display:none;padding:14px;border:1px solid var(--ac);margin-top:12px}.dr .ok.on{display:block}
/* pasta tasarla */
.ck{background:var(--ac2);color:#f6efe4;padding:14vh clamp(18px,4vw,64px)}.ckw{max-width:1300px;margin:auto;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:clamp(24px,6vw,90px);align-items:center}
.ck h2{font-size:clamp(44px,7vw,104px)}.ck p.s{color:#d9c7b3;margin-top:14px;max-width:44ch}
.ctl{display:grid;gap:18px;margin-top:34px}.ctl .lb{color:#d9c7b3;display:block;margin-bottom:8px}.opts{display:flex;gap:8px;flex-wrap:wrap}.opts button{min-height:46px;padding:0 18px;border-radius:30px;border:1.5px solid #f6efe4;background:transparent;color:#f6efe4;font:500 13px var(--mono);cursor:pointer}.opts button[aria-pressed=true]{background:#f6efe4;color:var(--ac2)}
.ctl input{width:100%;min-height:52px;padding:0 16px;background:rgba(255,255,255,.08);border:1.5px solid rgba(255,255,255,.4);border-radius:12px;color:#fff;font:400 18px var(--bf)}
.pr2{font:500 clamp(34px,5vw,56px)/1 var(--mono)}.pre{position:relative;border-radius:24px;overflow:hidden;aspect-ratio:1;background:#24140b}.pre img{width:100%;height:100%;object-fit:cover;transition:transform .6s}
.rib{position:absolute;left:8%;right:8%;bottom:14%;padding:12px 18px;background:rgba(255,250,241,.94);color:var(--ink);text-align:center;font:400 clamp(24px,3.4vw,44px)/1.1 var(--hf);border-radius:6px;transform:rotate(-3deg);min-height:1.4em;overflow-wrap:anywhere;box-shadow:0 10px 30px rgba(0,0,0,.35)}
.rib:empty:before{content:'Yazınız burada görünür';color:#a8957f;font-size:.6em}
.ck .btn{margin-top:6px}.ck .ok{display:none;margin-top:12px;padding:14px;border:1px solid #f6efe4}.ck .ok.on{display:block}
/* vitrin */
.vt{padding:12vh 0}.vt h2{font-size:clamp(44px,8vw,120px);padding:0 clamp(18px,4vw,64px)}.vh{display:flex;gap:16px;overflow-x:auto;scroll-snap-type:x mandatory;padding:5vh clamp(18px,4vw,64px) 14px;scrollbar-width:thin}
.vh figure{flex:none;width:min(420px,78vw);aspect-ratio:3/4;border-radius:22px;overflow:hidden;scroll-snap-align:center;background:#e7dccb;min-width:0}.vh img{width:100%;height:100%;object-fit:cover}
.vn{display:flex;gap:10px;padding:0 clamp(18px,4vw,64px)}.vn button{width:52px;height:52px;border-radius:50%;border:1.5px solid var(--ink);background:transparent;color:var(--ink);font-size:20px;cursor:pointer}.vn button:hover{background:var(--ink);color:var(--bg)}
/* şube */
.sb{padding:6vh clamp(18px,4vw,64px) 12vh;max-width:1400px;margin:auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px}
.sb div{background:var(--card);border:1px solid var(--ln);border-radius:18px;padding:24px}.sb h3{font-size:30px;margin-bottom:8px}.sb p{color:var(--mut)}
.fin{min-height:80svh;display:grid;place-items:center;text-align:center;padding:12vh 18px;background:radial-gradient(60% 50% at 50% 55%,rgba(217,142,50,.35),transparent 70%)}
.fin h2{font-size:clamp(44px,11vw,180px)}.fin h2 span{display:block;color:var(--ac);font-style:italic}.fin .btn{margin-top:5vh}
footer{padding:44px clamp(18px,4vw,64px) 32px;border-top:1px solid var(--ln);display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:24px}footer b{font:400 34px/1 var(--hf)}footer p{color:var(--mut);font-size:14px}
@media(max-width:860px){nav.top ul{display:none}.win{width:78vw;height:50vh}.ckw{grid-template-columns:minmax(0,1fr)}}
@media(prefers-reduced-motion:reduce){#hero{height:auto}.stage{height:80svh}.win{width:100%;height:100%;border-radius:0}.cap{opacity:1;transform:none}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce;
 var win=$('.win'),tt=$('.tt'),cap=$('.cap'),sc=$('.sc');
 var wv=matchMedia('(max-width:860px)').matches?78:46,hv=matchMedia('(max-width:860px)').matches?50:56;
 OK.scrub('#hero',$('#hv'),function(p){var e=Math.min(1,p/.45);e=e*e*(3-2*e);win.style.width=(wv+(100-wv)*e)+'vw';win.style.height=(hv+(100-hv)*e)+'vh';win.style.borderRadius=(28*(1-e))+'px';
  tt.style.opacity=Math.max(0,1-p*4);sc.style.opacity=p>.03?0:1;cap.classList.toggle('on',p>.55);$('nav.top').classList.toggle('ond',p>.4)});
 /* filtre */
 $$('.chips button').forEach(function(b){b.addEventListener('click',function(){$$('.chips button').forEach(function(x){x.setAttribute('aria-pressed',x===b)});$$('.pc').forEach(function(c){c.classList.toggle('hide',b.dataset.c!=='Hepsi'&&c.dataset.c!==b.dataset.c)});ScrollTrigger.refresh()})});
 /* sepet */
 var cart={},mode='Gel-al';var dr=$('.dr'),ov=$('.ov');
 function open(on){dr.classList.toggle('on',on);ov.classList.toggle('on',on)}
 function draw(){var ks=Object.keys(cart),n=0,sum=0;var ul=$('.dr ul');ul.innerHTML=ks.length?ks.map(function(k){var p=C.p[k],q=cart[k];n+=q;sum+=p[2]*q;return '<li><span>'+p[0]+'</span><b>'+money(p[2]*q)+'</b><div class="q"><button type="button" data-m="'+k+'" aria-label="Azalt">−</button><span>'+q+'</span><button type="button" data-a="'+k+'" aria-label="Artır">+</button></div></li>'}).join(''):'<li class="em">Sepetiniz boş.</li>';
  $('.cartbtn b').textContent=n;$('.dr .tot b').textContent=money(sum);gsap.fromTo('.cartbtn b',{scale:1.5},{scale:1,duration:.4,ease:'back.out(3)'});
  $$('[data-a]',ul).forEach(function(b){b.onclick=function(){cart[b.dataset.a]++;draw()}});$$('[data-m]',ul).forEach(function(b){b.onclick=function(){var k=b.dataset.m;if(--cart[k]<=0)delete cart[k];draw()}})}
 $$('.ad').forEach(function(b){b.addEventListener('click',function(){var k=b.dataset.k;cart[k]=(cart[k]||0)+1;draw();b.textContent='Eklendi';setTimeout(function(){b.textContent='Sepete ekle'},900)})});
 $('.cartbtn').onclick=function(){open(true)};$('.x').onclick=function(){open(false)};ov.onclick=function(){open(false)};addEventListener('keydown',function(e){if(e.key==='Escape')open(false)});
 $$('.tg button').forEach(function(b){b.onclick=function(){$$('.tg button').forEach(function(x){x.setAttribute('aria-pressed',x===b)});mode=b.dataset.t}});
 $('#ord').onclick=function(){if(!Object.keys(cart).length)return;var o=$('.dr .ok');o.textContent='Siparişiniz alındı ('+mode.toLowerCase()+'). Hazır olunca size haber vereceğiz.';o.classList.add('on')};
 draw();
 /* pasta */
 var sz=8,fl='Çikolata',base=1200;var pre=$('.rib');
 var price={4:.7,8:1,12:1.45,20:2.2},fp={'Çikolata':0,'Vanilya':0,'Frambuaz':150,'Fıstık':250};
 function calc(){var v=Math.round((base*price[sz]+fp[fl])/10)*10;$('#cp').textContent=money(v)}
 $$('[data-sz]').forEach(function(b){b.onclick=function(){sz=+b.dataset.sz;$$('[data-sz]').forEach(function(x){x.setAttribute('aria-pressed',x===b)});calc()}});
 $$('[data-fl]').forEach(function(b){b.onclick=function(){fl=b.dataset.fl;$$('[data-fl]').forEach(function(x){x.setAttribute('aria-pressed',x===b)});calc()}});
 $('#tx').addEventListener('input',function(e){pre.textContent=e.target.value.slice(0,36)});calc();
 $('#qt').onclick=function(){var o=$('.ck .ok');o.textContent=sz+' kişilik '+fl.toLowerCase()+' pasta için talebiniz alındı'+($('#tx').value?' ("'+$('#tx').value+'")':'')+'. Teklifi birkaç saat içinde ileteceğiz.';o.classList.add('on')};
 /* vitrin */
 var vh=$('.vh');$('#vp').onclick=function(){vh.scrollBy({left:-vh.clientWidth*.6,behavior:'smooth'})};$('#vx').onclick=function(){vh.scrollBy({left:vh.clientWidth*.6,behavior:'smooth'})};
});
'''
def render():
    cards = ''.join('<article class="pc" data-c="%s"><div class="im"><img src="%s" alt="%s" loading="lazy"></div><div class="tx"><h3>%s</h3><span class="pr">%s ₺</span><button class="ad" type="button" data-k="%d">Sepete ekle</button></div></article>' % (c, ph(k, 700), H.escape(a), H.escape(a), format(p, ',').replace(',', '.'), i) for i, (a, c, p, k) in enumerate(PROD))
    chips = ''.join('<button type="button" data-c="%s" aria-pressed="%s">%s</button>' % (c, 'true' if i == 0 else 'false', c) for i, c in enumerate(CATS))
    vit = ''.join('<figure><img src="%s" alt="Vitrinden bir kare" loading="lazy"></figure>' % ph(k, 700) for k in (1, 3, 5, 7, 9, 2, 4))
    body = '''<div id="pre" role="status"><div><b>Fırın 1923</b><i><span id="pn">0</span>%%</i></div></div>
<nav class="top"><a class="lg" href="#">Fırın 1923</a><ul><li><a href="#menu">Ürünler</a></li><li><a href="#pasta">Özel pasta</a></li><li><a href="#vitrin">Vitrin</a></li><li><a href="#sube">Şubeler</a></li></ul><button class="cartbtn" type="button" aria-label="Sepeti aç">Sepet<b>0</b></button></nav>
<main><section id="hero" aria-label="Açılış"><div class="stage"><div class="tt"><div><h1>Sabah fırından.</h1><p>Kapı açılmadan hamur hazır</p></div></div><div class="win"><img class="poster" src="%(poster)s" alt="" fetchpriority="high"><video id="hv" muted playsinline preload="auto" poster="%(poster)s" src="%(v)s" aria-hidden="true"></video></div><div class="cap"><h2>Elle şekil, sıcak teslim.</h2><p>Gel-al ya da kapına gelsin</p></div><div class="sc">KAYDIR</div></div></section>
<section class="mn" id="menu"><h2 class="rv">Bugün neler var?</h2><p>Sıcak çıkanlar, günlük tazeler ve siparişe özel pastalar.</p><div class="chips" role="group" aria-label="Kategori">%(chips)s</div><div class="gr">%(cards)s</div></section>
<section class="ck" id="pasta"><div class="ckw"><div><h2 class="rv">Pastanı tasarla.</h2><p class="s">Boyutu ve aromayı seç, üzerine yazılacak cümleyi gir; pasta bir önizlemede şekillensin.</p><div class="ctl"><div><span class="lb">Kişi sayısı</span><div class="opts"><button type="button" data-sz="4" aria-pressed="false">4</button><button type="button" data-sz="8" aria-pressed="true">8</button><button type="button" data-sz="12" aria-pressed="false">12</button><button type="button" data-sz="20" aria-pressed="false">20</button></div></div><div><span class="lb">Aroma</span><div class="opts"><button type="button" data-fl="Çikolata" aria-pressed="true">Çikolata</button><button type="button" data-fl="Vanilya" aria-pressed="false">Vanilya</button><button type="button" data-fl="Frambuaz" aria-pressed="false">Frambuaz</button><button type="button" data-fl="Fıstık" aria-pressed="false">Fıstık</button></div></div><div><label class="lb" for="tx">Pastanın üzerine yazı</label><input id="tx" maxlength="36" placeholder="İyi ki doğdun Defne"></div><div class="pr2" id="cp">0 ₺</div><button class="btn" id="qt" type="button" style="background:#f6efe4;color:#3a2418">Teklif iste</button><p class="ok" role="status"></p></div></div>
<div class="pre"><img src="%(cake)s" alt="Pasta önizlemesi"><div class="rib" aria-live="polite"></div></div></div></section>
<section class="vt" id="vitrin"><h2 class="rv">Vitrinden.</h2><div class="vh" tabindex="0" aria-label="Vitrin fotoğrafları">%(vit)s</div><div class="vn"><button type="button" id="vp" aria-label="Önceki">←</button><button type="button" id="vx" aria-label="Sonraki">→</button></div></section>
<section class="sb" id="sube"><div><h3>Merkez şube</h3><p>Örnek Cd., Örnek Mah. · Ankara</p><p>Her gün 07.00 – 22.00</p></div><div><h3>Gel-al</h3><p>Siparişin hazır olunca haber veririz; tezgâhtan teslim alırsın.</p></div><div><h3>Adrese teslim</h3><p>Şehir içi, 30 – 60 dakikada sıcak teslim.</p></div></section>
<section class="fin"><div><h2 class="rv">Sıcak gelir. <span>Tatlı gider.</span></h2><a class="btn" href="#menu">Sipariş ver</a></div></section></main>
<footer><div><b>Fırın 1923</b><p>Pastane · Fırın</p></div><div class="cl"><p class="lb">Menü</p><a href="#menu">Ürünler</a><a href="#pasta">Özel pasta</a><a href="#vitrin">Vitrin</a><a href="#sube">Şubeler</a></div><div class="cl"><p class="lb">İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a><p>Örnek Cd., Örnek Mah. · Ankara</p></div><div><p class="lb">Saatler</p><p>Her gün 07.00 – 22.00</p></div><p class="cr">© 2026 Fırın 1923</p></footer>
<div class="ov"></div><aside class="dr" aria-label="Sepet"><header><h3>Sepetiniz</h3><button class="x" type="button" aria-label="Kapat">×</button></header><ul></ul><div class="tg" role="group" aria-label="Teslim"><button type="button" data-t="Gel-al" aria-pressed="true">Gel-al</button><button type="button" data-t="Adrese teslim" aria-pressed="false">Adrese teslim</button></div><div class="tot"><span>Toplam</span><b>0 ₺</b></div><button class="btn" id="ord" type="button">Siparişi tamamla</button><p class="ok" role="status"></p></aside>''' % dict(poster=POSTER, v=VURL, chips=chips, cards=cards, vit=vit, cake=ph(8, 1000))
    c = json.dumps(dict(p=[[a, c, p] for a, c, p, _ in PROD]), ensure_ascii=False)
    return page('Fırın 1923 Pastane', 'Günlük fırın ürünleri, sepet ve özel pasta siparişi.', ['DM Serif Display', 'DM Mono:wght@400;500', 'Figtree:wght@400;500;700'], BASE_CSS + CSS, body, JS, c, dict(cta=['Sipariş ver','#menu'], addr='Örnek Cd., Örnek Mah. · Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/firin', exist_ok=True); open(R + '/firin/index.html', 'w', encoding='utf-8').write(render()); print('firin ok')
