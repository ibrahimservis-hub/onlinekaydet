# -*- coding: utf-8 -*-
"""Anahtar Emlak: krem + limon editoryal, devasa tipografi, kemer maskeli foto, filtre çipleri, ilan tablosu."""
import json
from common import *
IDX = 18
f = foto.F[IDX]
ph = lambda k, w=900: foto.url(f[k % len(f)], w)
ILAN = [
 ('Çankaya, 3+1 daire', 'Satılık', 'Daire', 6850000, '145 m²', '4. kat', '2018', 1),
 ('Yenimahalle, 2+1 daire', 'Kiralık', 'Daire', 28000, '95 m²', '2. kat', '2020', 2),
 ('Gölbaşı, müstakil villa', 'Satılık', 'Villa', 14900000, '320 m²', '3 katlı', '2016', 3),
 ('Etimesgut, 1+1 daire', 'Kiralık', 'Daire', 17500, '55 m²', '5. kat', '2022', 4),
 ('Keçiören, dükkân', 'Satılık', 'Ticari', 4200000, '70 m²', 'Zemin', '2012', 5),
 ('Bilkent, 4+1 daire', 'Kiralık', 'Daire', 62000, '210 m²', '8. kat', '2019', 6),
]
CSS = '''
:root{--bg:#f3efe3;--ink:#16180f;--mut:#6b6a58;--ac:#c6f03a;--ac2:#2f3a12;--ln:rgba(22,24,15,.2);--hf:'Sora',system-ui,sans-serif;--mono:'Inter',sans-serif;--bf:'Inter',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 17px/1.6 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:700;letter-spacing:-.045em;line-height:.92;overflow-wrap:break-word;min-width:0}
.btn{border-radius:0;font-family:var(--bf);text-transform:none;letter-spacing:0;font-weight:700;font-size:16px}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;align-items:center;gap:30px;padding:18px clamp(20px,4vw,56px);background:var(--bg);border-bottom:1px solid var(--ln)}
.lg{font:800 22px var(--hf);letter-spacing:-.05em;text-decoration:none;margin-right:auto}.lg i{display:inline-block;width:12px;height:12px;background:var(--ac);border:2px solid var(--ink);border-radius:50%;margin-right:8px}
nav.top ul{display:flex;gap:30px;list-style:none;padding:0}nav.top li a{font:600 15px var(--bf);text-decoration:none;background:linear-gradient(var(--ink),var(--ink)) 0 100%/0 2px no-repeat;transition:background-size .3s}nav.top li a:hover{background-size:100% 2px}
nav.top .btn{background:var(--ac);color:var(--ink);padding:11px 20px;border:2px solid var(--ink)}
.hero{padding:120px clamp(20px,4vw,56px) 0;display:grid;grid-template-columns:1.25fr .75fr;gap:3vw;min-height:100svh;align-items:end;overflow:clip}
.hero h1{font-size:clamp(60px,10.5vw,190px);grid-column:1/-1;margin-bottom:-.1em;position:relative;z-index:2}.hero h1 em{font-style:normal;background:var(--ac);padding:0 .08em}
.hero .tx{align-self:center;padding-bottom:40px}.hero .tx p{max-width:27em;font-size:20px}.hero .tx .bt{display:flex;gap:12px;margin-top:26px;flex-wrap:wrap}
.hero .btn.p{background:var(--ink);color:var(--ac)}.hero .btn.g{border:2px solid var(--ink);background:transparent;color:var(--ink)}
.arch{width:min(100%,520px);aspect-ratio:3/3.7;border-radius:999px 999px 0 0;overflow:hidden;justify-self:end;position:relative}.arch img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.tick{background:var(--ink);color:var(--ac);overflow:hidden;white-space:nowrap;padding:16px 0;font:700 22px var(--hf);letter-spacing:-.02em}.tick div{display:inline-block;animation:tk 30s linear infinite}.tick span{margin:0 28px}
@keyframes tk{to{transform:translateX(-50%)}}
section.s{padding:min(15vh,140px) clamp(20px,4vw,56px) 4vh;max-width:1500px;margin:auto}
.hd h2{font-size:clamp(46px,8vw,128px);margin-bottom:5vh}.hd h2 span{color:var(--mut)}
.ch{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:28px}.ch button{min-height:48px;padding:0 24px;border:2px solid var(--ink);background:transparent;font:700 16px var(--bf);cursor:pointer;border-radius:0;transition:background .2s}
.ch button:hover{background:var(--ac)}.ch button[aria-pressed=true]{background:var(--ink);color:var(--ac)}
.ls{border-top:2px solid var(--ink)}
.row{display:grid;grid-template-columns:150px 1.6fr 1fr .8fr .8fr 1fr;gap:20px;align-items:center;padding:16px 0;border-bottom:1px solid var(--ln);cursor:pointer;transition:background .25s,padding .25s;text-decoration:none;color:inherit}
.row:hover,.row[aria-selected=true]{background:var(--ac);padding-left:14px;padding-right:14px}.row .th{aspect-ratio:4/3;overflow:hidden;position:relative}.row .th img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.row b{font:700 22px/1.1 var(--hf);letter-spacing:-.03em}.row small{display:block;color:var(--mut);font:600 14px var(--bf);margin-top:4px}.row .pr{font:700 22px var(--hf);text-align:right}.row[hidden]{display:none}
.fe{display:grid;grid-template-columns:1.1fr .9fr;gap:4vw;margin-top:8vh;align-items:start}.fe .im{aspect-ratio:5/4;position:relative;overflow:hidden}.fe .im img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .8s}.fe .im:hover img{transform:scale(1.03)}
.fe h3{font-size:clamp(34px,4.4vw,64px)}.sp{width:100%;border-collapse:collapse;margin:24px 0}.sp td{padding:14px 0;border-bottom:1px solid var(--ink);font-weight:600}.sp td:last-child{text-align:right;font:700 20px var(--hf)}
.num{background:var(--ac);padding:min(14vh,120px) clamp(20px,4vw,56px)}.num div{max-width:1500px;margin:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:30px}.num b{font:800 clamp(56px,9vw,150px)/.9 var(--hf);letter-spacing:-.06em;display:block}.num p{font-weight:700;max-width:14em}
.fm{display:grid;grid-template-columns:1fr 1fr;gap:5vw;align-items:end}.fm h2{font-size:clamp(46px,8vw,128px)}.fm form{display:grid;gap:12px}.fm label{display:grid;gap:6px;font:700 15px var(--bf)}.fm input,.fm select{min-height:54px;border:2px solid var(--ink);background:transparent;padding:0 16px;font:600 17px var(--bf);border-radius:0;color:var(--ink)}
.fm .btn{background:var(--ink);color:var(--ac);min-height:56px;border:0;cursor:pointer}.fm .ok{display:none;background:var(--ac);padding:14px 16px;font-weight:700}.fm .ok.on{display:block}
footer{background:var(--ink);color:var(--bg);padding:70px clamp(20px,4vw,56px) 28px;overflow:clip}footer .t{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px}footer b{font:800 28px var(--hf);letter-spacing:-.04em;color:var(--ac)}
footer a{display:block;color:var(--bg);text-decoration:none;padding:3px 0}footer a:hover{color:var(--ac)}footer p{color:#a9a891}
footer .big{font:800 clamp(80px,26vw,420px)/.78 var(--hf);letter-spacing:-.07em;color:var(--ac);margin:50px 0 0;white-space:nowrap}
@media(max-width:860px){
.hero{grid-template-columns:1fr;padding-top:92px}.hero h1{font-size:clamp(54px,17vw,110px)}.arch{justify-self:center;width:84%}
nav.top ul,nav.top>.btn{display:none}nav.top{padding:12px 16px}nav.top .hm{margin-left:auto;border-radius:0}
.row{grid-template-columns:96px 1fr;gap:12px}.row>:nth-child(n+3){display:none}.row .pr{display:block!important;grid-column:2;text-align:left;font-size:19px}
.fe,.fm,.num div,footer .t{grid-template-columns:1fr}section.s{padding-top:80px}
.mb{left:0;right:0;bottom:0;background:var(--ink);border:0;border-radius:0;grid-template-columns:1fr 1fr 1.5fr;padding:8px 8px max(8px,env(safe-area-inset-bottom))}.mb a{color:var(--bg);border-radius:0;min-height:48px;font:700 15px var(--bf);text-transform:none;letter-spacing:0}.mb a.p{background:var(--ac);color:var(--ink)}
.mm{background:var(--ac);color:var(--ink);inset:0;padding:90px 20px 100px;--ln:rgba(22,24,15,.3);--ac:#16180f;--mut:#2f3a12}.mm a{font:800 clamp(46px,15vw,80px)/.95 var(--hf);letter-spacing:-.05em;color:var(--ink);border-bottom:2px solid var(--ink);padding:10px 0}.mm small{color:var(--ac2);font:700 14px var(--bf);text-transform:none;letter-spacing:0}
footer{padding-bottom:100px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce;
 if(!rd){gsap.from('.hero h1',{yPercent:30,opacity:0,duration:1,ease:'power4.out'});gsap.from('.arch',{clipPath:'inset(100% 0 0 0)',duration:1.3,ease:'power4.out',delay:.2});gsap.from('.hero .tx>*',{y:30,opacity:0,stagger:.1,duration:.8,delay:.5});
  gsap.to('.arch img',{yPercent:8,scale:1.1,ease:'none',scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom top',scrub:true}});
  $$('.num b').forEach(function(e){var v=+e.dataset.v,o={n:0};ScrollTrigger.create({trigger:e,start:'top 85%',once:true,onEnter:function(){gsap.to(o,{n:v,duration:1.6,ease:'power2.out',onUpdate:function(){e.textContent=Math.round(o.n)+(e.dataset.s||'')}})}})});
  gsap.from('footer .big',{yPercent:50,duration:1.2,ease:'power4.out',scrollTrigger:{trigger:'footer',start:'top 85%'}})}
 var rows=$$('.row'),sel=0;function pick(i){sel=i;var d=C.l[i];rows.forEach(function(r,j){r.setAttribute('aria-selected',j===i)});$('#fi').src=d[8];$('#ft').textContent=d[0];$('#fs').innerHTML=[['Tür',d[2]],['Alan',d[4]],['Kat',d[5]],['Yapım yılı',d[6]],[d[1]=='Kiralık'?'Aylık kira':'Fiyat',money(d[3])]].map(function(x){return '<tr><td>'+x[0]+'</td><td>'+x[1]+'</td></tr>'}).join('')}
 rows.forEach(function(r,i){r.onclick=function(e){e.preventDefault();pick(i)}});
 $$('.ch button').forEach(function(b){b.onclick=function(){$$('.ch button').forEach(function(x){x.setAttribute('aria-pressed',x===b)});var k=b.dataset.k;rows.forEach(function(r){var d=C.l[+r.dataset.i];r.hidden=!(k=='Hepsi'||d[1]==k||d[2]==k)});var v=rows.filter(function(r){return !r.hidden})[0];if(v)pick(+v.dataset.i)}});
 pick(0);
 $('#fm').onsubmit=function(e){e.preventDefault();var o=$('#fo');o.textContent='Teşekkürler '+$('#fn').value+'. '+$('#fk').value+' için talebiniz alındı, size ulaşacağız.';o.classList.add('on')};
});
'''
def render():
    chips = ''.join('<button type="button" data-k="%s" aria-pressed="%s">%s</button>' % (k, 'true' if k == 'Hepsi' else 'false', k) for k in ['Hepsi', 'Satılık', 'Kiralık', 'Daire', 'Villa', 'Ticari'])
    rows = ''.join('<a class="row" href="#ilan" data-i="%d"><div class="th"><img src="%s" alt="%s" loading="lazy"></div><div><b>%s</b><small>%s · %s</small></div><div>%s</div><div>%s</div><div>%s</div><div class="pr">%s</div></a>' % (i, ph(l[7], 500), l[0], l[0], l[1], l[2], l[4], l[5], l[6], money_py(l[3], l[1])) for i, l in enumerate(ILAN))
    tick = ''.join('<span>Satılık</span><span>Kiralık</span><span>Değerleme</span><span>Tapu işlemleri</span>' for _ in range(6))
    body = f'''<div id="pre" role="status"><div><b>ANAHTAR</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#"><i></i>Anahtar</a><ul><li><a href="#ilanlar">İlanlar</a></li><li><a href="#rakam">Rakamlar</a></li><li><a href="#iletisim">İletişim</a></li></ul><a class="btn" href="#iletisim">Değerleme iste</a></nav>
<main><header class="hero" id="hero"><h1>Evin <em>anahtarı</em> bizde.</h1><div class="tx"><p>Ankara'da satılık ve kiralık daire, villa ve işyeri. Her ilan yerinde görülür, tapusu kontrol edilir.</p><div class="bt"><a class="btn p" href="#ilanlar">İlanlara bak</a><a class="btn g" href="#iletisim">Evimi değerle</a></div></div><div class="arch"><img src="{ph(0, 1100)}" alt="Modern bir evin cephesi" fetchpriority="high"></div></header>
<div class="tick" aria-hidden="true"><div>{tick}</div></div>
<section class="s" id="ilanlar"><div class="hd"><h2>Açık <span>ilanlar</span></h2></div><div class="ch" role="group" aria-label="Filtre">{chips}</div><div class="ls">{rows}</div>
<div class="fe" id="ilan"><div class="im"><img id="fi" src="" alt="Seçili ilan"></div><div><h3 id="ft"></h3><table class="sp"><tbody id="fs"></tbody></table><a class="btn p" style="background:var(--ink);color:var(--ac);display:inline-block;padding:14px 26px" href="#iletisim">Bu ilanı gör</a></div></div></section>
<section class="num" id="rakam"><div><p><b data-v="14" data-s=" yıl">0</b>Aynı mahallelerde çalışıyoruz.</p><p><b data-v="2" data-s=" gün">0</b>İlan fotoğrafı ve ekspertizi hazır olur.</p><p><b data-v="1" data-s=" kişi">0</b>Dosyanızı baştan sona tek danışman izler.</p></div></section>
<section class="s" id="iletisim"><div class="fm"><h2>Eviniz kaç para eder?</h2><form id="fm"><label>Adınız<input id="fn" required autocomplete="name"></label><label>Konu<select id="fk"><option>Değerleme</option><option>Satış</option><option>Kiralama</option></select></label><button class="btn" type="submit">Talep bırak</button><p class="ok" id="fo" aria-live="polite"></p></form></div></section></main>
<footer><div class="t"><div><b>Anahtar Emlak</b><p>Örnek Mah. Ankara</p></div><div><p>Sayfalar</p><a href="#ilanlar">İlanlar</a><a href="#rakam">Rakamlar</a><a href="#iletisim">İletişim</a></div><div><p>İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div></div><div class="big" aria-hidden="true">ANAHTAR</div></footer>'''
    L = [list(l[:7]) + [l[7]] + [ph(l[7], 1000)] for l in ILAN]
    c = json.dumps(dict(l=[[a, b, c_, d, e, g, h, i, j] for a, b, c_, d, e, g, h, i, j in L]), ensure_ascii=False)
    return page('Anahtar Emlak', 'Ankara satılık ve kiralık daire, villa, işyeri.', ['Sora:wght@600;700;800', 'Inter:wght@400;600;700'], BASE_CSS + CSS, body, JS, c, dict(cta=['Değerleme iste', '#iletisim'], addr='Örnek Mah. · Ankara'))
def money_py(v, t):
    s = '{:,}'.format(v).replace(',', '.') + ' ₺'
    return s + (' / ay' if t == 'Kiralık' else '')
if __name__ == '__main__':
    import os
    os.makedirs(R + '/emlak', exist_ok=True); open(R + '/emlak/index.html', 'w', encoding='utf-8').write(render()); print('emlak ok')
