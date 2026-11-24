# -*- coding: utf-8 -*-
"""İç Ses: psikolog. Sakin gri-mavi, Newsreader serif, bol boşluk; nefes egzersizi, görüşme türü seçici, SSS."""
import json
from common import *
IDX = 11
f = foto.F[IDX]
ph = lambda k, w=900: foto.url(f[k % len(f)], w)
TUR = {'Bireysel': ('50 dk', 'Yüz yüze veya çevrimiçi. Seni rahatsız eden konuyu, kendi hızında konuşursun.', 1800),
       'Çift': ('75 dk', 'İletişim ve yakınlık üzerine ortak çalışma. İki taraf da aynı odadadır.', 2600),
       'Ergen': ('50 dk', '13-18 yaş için. İlk görüşmede aile ile kısa bir bilgi alma yapılır.', 1800)}
SSS = [('İlk seans nasıl geçer?', 'Tanışırız, seni buraya getireni dinleriz. Sonrasında nasıl devam edeceğimizi birlikte konuşuruz.'), ('Çevrimiçi olur mu?', 'Evet. Güvenli bir görüntülü görüşme bağlantısı gönderilir, tek şart sessiz bir oda.'), ('Gizlilik nasıl sağlanır?', 'Seanslarda konuşulanlar yasa gereği gizli tutulur. Kayıtlar yalnızca bende saklanır.'), ('Kaç seans gerekir?', 'Konuya göre değişir. İlk görüşmeden sonra tahmini bir süre birlikte belirlenir.')]
CSS = '''
:root{--bg:#f6f5f2;--ink:#2b2f3a;--mut:#6a7080;--ac:#7c9cbf;--ac2:#2b2f3a;--ln:rgba(43,47,58,.14);--hf:'Newsreader',Georgia,serif;--mono:'Inter',sans-serif;--bf:'Inter',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 18px/1.8 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:400;letter-spacing:-.015em;line-height:1.1;overflow-wrap:break-word;min-width:0}
.btn{border-radius:40px;font-family:var(--bf);font-weight:500;font-size:16px;text-transform:none;letter-spacing:0}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;align-items:center;gap:30px;padding:22px clamp(20px,4vw,56px);color:var(--ink);transition:background .4s}nav.top.solid{background:rgba(246,245,242,.94);backdrop-filter:blur(8px)}
.lg{font:italic 400 28px var(--hf);text-decoration:none;margin-right:auto}
nav.top ul{display:flex;gap:32px;list-style:none;padding:0}nav.top li a{font:400 15px var(--bf);text-decoration:none;color:var(--mut)}nav.top li a:hover{color:var(--ink)}nav.top .btn{border:1px solid var(--ink);padding:11px 24px;background:transparent;color:var(--ink)}nav.top .btn:hover{background:var(--ink);color:#fff}
.hero{min-height:100svh;display:grid;grid-template-columns:1.2fr .8fr;align-items:center;gap:6vw;padding:120px clamp(24px,6vw,100px) 80px;max-width:1500px;margin:auto}
.hero h1{font-size:clamp(46px,6.4vw,104px);font-weight:300}.hero h1 em{font-style:italic;color:#5a7ea5}.hero p{max-width:26em;color:var(--mut);margin:26px 0 34px;font-size:19px}.hero .btn.p{background:var(--ink);color:#fff;padding:17px 34px;display:inline-block}
.hero .im{aspect-ratio:3/4;border-radius:200px 200px 16px 16px;overflow:hidden;position:relative;max-height:74vh;justify-self:end;width:min(100%,460px)}.hero .im img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
section.s{padding:min(16vh,150px) clamp(24px,6vw,100px) 4vh;max-width:1280px;margin:auto}
.hd{margin-bottom:6vh}.hd h2{font-size:clamp(38px,5vw,76px);font-weight:300}.hd h2 em{font-style:italic;color:#5a7ea5}.hd p{color:var(--mut);max-width:30em;margin-top:14px}
.br{display:grid;grid-template-columns:1fr 1fr;gap:6vw;align-items:center;background:#e9eef4;border-radius:32px;padding:clamp(28px,5vw,80px)}.br .rg{position:relative;width:min(100%,380px);aspect-ratio:1;margin:auto;display:grid;place-items:center}
.br .rg i{position:absolute;inset:0;border-radius:50%;background:radial-gradient(circle,#b8cde3,#7c9cbf);opacity:.6;transform:scale(.55);transition:transform 4s cubic-bezier(.45,0,.55,1)}.br .rg.in i{transform:scale(1)}.br .rg.hold i{transition:none}.br .rg.out i{transform:scale(.55)}
.br .rg span{position:relative;font:italic 400 38px var(--hf);color:var(--ink)}.br h3{font-size:clamp(30px,3.4vw,48px)}.br p{color:var(--mut);margin:14px 0 24px}.br .btn{background:var(--ink);color:#fff;border:0;padding:15px 30px;cursor:pointer}
.tr{display:grid;grid-template-columns:.9fr 1.1fr;gap:6vw;align-items:start}.tr .tb{display:flex;flex-direction:column;border-top:1px solid var(--ln)}.tr .tb button{text-align:left;min-height:76px;border:0;border-bottom:1px solid var(--ln);background:transparent;color:var(--mut);font:300 clamp(30px,3.4vw,48px) var(--hf);cursor:pointer;transition:color .3s,padding .3s}.tr .tb button:hover{color:var(--ink)}.tr .tb button[aria-pressed=true]{color:var(--ink);font-style:italic;padding-left:16px}
.tr .dt h3{font-size:clamp(30px,3.4vw,46px)}.tr .dt .kv{display:flex;gap:30px;margin:20px 0;padding:18px 0;border-block:1px solid var(--ln)}.tr .dt small{display:block;color:var(--mut);font-size:14px}.tr .dt b{font:400 32px var(--hf)}.tr .dt p{color:var(--mut)}.tr .dt .btn{display:inline-block;margin-top:22px;background:var(--ink);color:#fff;padding:15px 30px}
.fq details{border-bottom:1px solid var(--ln)}.fq details:first-child{border-top:1px solid var(--ln)}.fq summary{list-style:none;cursor:pointer;min-height:80px;display:flex;justify-content:space-between;align-items:center;font:300 clamp(26px,3vw,40px) var(--hf);gap:16px}.fq summary::-webkit-details-marker{display:none}.fq summary:after{content:'+';font-size:34px;color:var(--ac);transition:transform .3s}.fq details[open] summary:after{transform:rotate(45deg)}.fq p{color:var(--mut);padding:0 0 28px;max-width:40em}
.wd{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:8vh}.wd .im{aspect-ratio:4/3;position:relative;overflow:hidden;border-radius:16px}.wd img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform 1s}.wd .im:hover img{transform:scale(1.03)}
.cl{background:var(--ink);color:#fff;padding:min(14vh,130px) clamp(24px,6vw,100px);margin-top:10vh}.cl>div{max-width:1280px;margin:auto;display:grid;grid-template-columns:1fr 1fr;gap:6vw;align-items:end}.cl h2{font-size:clamp(40px,5.6vw,90px);font-weight:300}.cl h2 em{font-style:italic;color:#b8cde3}.cl form{display:grid;gap:14px}.cl input{min-height:56px;border:0;border-bottom:1px solid rgba(255,255,255,.4);background:transparent;padding:0;font:400 18px var(--bf);color:#fff;border-radius:0}.cl input::placeholder{color:#9aa3b5}.cl .btn{background:#fff;color:var(--ink);min-height:58px;border:0;cursor:pointer;margin-top:6px}.cl .ok{display:none;color:#b8cde3}.cl .ok.on{display:block}
footer{background:var(--ink);color:#fff;padding:0 clamp(24px,6vw,100px) 40px;display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px;border-top:1px solid rgba(255,255,255,.14);padding-top:50px}footer b{font:italic 400 28px var(--hf)}footer a{display:block;color:#fff;text-decoration:none;padding:3px 0}footer a:hover{color:#b8cde3}footer p{color:#9aa3b5;font-size:15px}
@media(max-width:860px){
nav.top ul,nav.top>.btn{display:none}nav.top{padding:14px 16px}nav.top .hm{margin-left:auto;border-radius:50%}
.hero{grid-template-columns:1fr;padding-top:96px;gap:30px}.hero .im{order:-1;width:70%;justify-self:center;max-height:44vh}.br,.tr,.wd,.cl>div,footer{grid-template-columns:1fr}
.mb{left:12px;right:12px;bottom:12px;background:#fff;border:1px solid var(--ln);border-radius:40px;box-shadow:0 14px 40px -16px rgba(43,47,58,.5);grid-template-columns:1fr 1fr 1.5fr;padding:5px;gap:4px}.mb a{min-height:50px;border-radius:30px;color:var(--ink);font:500 15px var(--bf);letter-spacing:0;text-transform:none}.mb a+a{border:0}.mb a.p{background:var(--ink);color:#fff}
.mm{background:#e9eef4;color:var(--ink);inset:0;padding:100px 28px 110px;--ln:rgba(43,47,58,.14);--ac:#5a7ea5;--mut:#6a7080}.mm a{font:italic 300 clamp(40px,13vw,66px)/1.2 var(--hf);color:var(--ink);border-bottom:0;padding:8px 0}.mm small{color:var(--mut);font:400 14px var(--bf);text-transform:none;letter-spacing:0}
footer{padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce;
 if(!rd){gsap.from('.hero h1',{opacity:0,y:30,duration:1.6,ease:'power2.out'});gsap.from('.hero p,.hero .btn',{opacity:0,y:20,duration:1.2,delay:.5,stagger:.15});gsap.from('.hero .im',{opacity:0,duration:1.8,ease:'power2.out'});
  gsap.utils.toArray('.hd,.br,.tr,.wd .im,.fq').forEach(function(e){gsap.from(e,{opacity:0,y:40,duration:1.2,ease:'power2.out',scrollTrigger:{trigger:e,start:'top 88%'}})})}
 var rg=$('#rg'),lb=$('#rl'),btn=$('#rb'),on=false,tm=[];function clr(){tm.forEach(clearTimeout);tm=[]}
 function cyc(){if(!on)return;rg.className='rg in';lb.textContent='Nefes al';tm.push(setTimeout(function(){if(!on)return;rg.className='rg in hold';lb.textContent='Tut';tm.push(setTimeout(function(){if(!on)return;rg.className='rg out';lb.textContent='Ver';tm.push(setTimeout(cyc,4000))},4000))},4000))}
 btn.onclick=function(){on=!on;clr();if(on){btn.textContent='Durdur';cyc()}else{btn.textContent='Başla';rg.className='rg';lb.textContent='Hazır'}};
 if(rd){rg.style.setProperty('--x',1)}
 function sh(k){var d=C.t[k];$$('.tb button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.k===k)});$('#tt').textContent=k+' görüşme';$('#td').textContent=d[1];$('#tu').textContent=d[0];$('#tp').textContent=money(d[2])}
 $$('.tb button').forEach(function(b){b.onclick=function(){sh(b.dataset.k)}});sh('Bireysel');
 $('#fm').onsubmit=function(e){e.preventDefault();var o=$('#fo');o.textContent='Teşekkürler '+$('#fn').value+'. İlk görüşme için sana dönüş yapacağım.';o.classList.add('on')};
});
'''
def render():
    tb = ''.join('<button type="button" data-k="%s" aria-pressed="false">%s</button>' % (k, k) for k in TUR)
    fq = ''.join('<details><summary>%s</summary><p>%s</p></details>' % (a, b) for a, b in SSS)
    body = f'''<div id="pre" role="status"><div><b>İÇ SES</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">İç Ses</a><ul><li><a href="#nefes">Nefes</a></li><li><a href="#gorusme">Görüşmeler</a></li><li><a href="#sss">Sorular</a></li></ul><a class="btn" href="#randevu">İlk görüşme</a></nav>
<main><header class="hero" id="hero"><div><h1>Anlatmak için <em>acele etme.</em></h1><p>Klinik psikolog eşliğinde, yargılanmadan konuşabileceğin sakin bir alan. Yüz yüze ve çevrimiçi görüşme.</p><a class="btn p" href="#randevu">İlk görüşmeyi ayarla</a></div><div class="im"><img src="{ph(0, 1000)}" alt="Sakin bir görüşme odası" fetchpriority="high"></div></header>
<section class="s" id="nefes"><div class="hd"><h2>Bir dakika <em>dur.</em></h2><p>Dört saniye al, dört tut, dört ver. Dilediğin kadar sürdür.</p></div><div class="br"><div class="rg" id="rg"><i></i><span id="rl">Hazır</span></div><div><h3>Nefes egzersizi</h3><p>Görüşmelerde de kullandığımız basit bir yavaşlama yöntemidir. Tıbbi bir tedavi yerine geçmez.</p><button class="btn" id="rb" type="button">Başla</button></div></div></section>
<section class="s" id="gorusme"><div class="hd"><h2>Görüşme <em>türleri</em></h2></div><div class="tr"><div class="tb" role="group" aria-label="Tür">{tb}</div><div class="dt"><h3 id="tt"></h3><div class="kv"><div><small>Süre</small><b id="tu"></b></div><div><small>Ücret</small><b id="tp"></b></div></div><p id="td"></p><a class="btn" href="#randevu">Randevu iste</a></div></div>
<div class="wd"><div class="im"><img src="{ph(1, 900)}" alt="Görüşme koltuğu" loading="lazy"></div><div class="im"><img src="{ph(2, 900)}" alt="Bekleme alanı" loading="lazy"></div></div></section>
<section class="s" id="sss"><div class="hd"><h2>Sık sorulan <em>sorular</em></h2></div><div class="fq">{fq}</div></section>
<section class="cl" id="randevu"><div><h2>İlk adımı <em>birlikte</em> atalım.</h2><form id="fm"><input id="fn" required placeholder="Adınız" aria-label="Adınız" autocomplete="name"><input type="email" required placeholder="E-posta" aria-label="E-posta"><button class="btn" type="submit">Görüşme iste</button><p class="ok" id="fo" aria-live="polite"></p></form></div></section></main>
<footer><div><b>İç Ses</b><p>Klinik psikolog · Örnek Sok. Ankara</p></div><div><p>Sayfalar</p><a href="#nefes">Nefes</a><a href="#gorusme">Görüşmeler</a><a href="#sss">Sorular</a></div><div><p>İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div></footer>'''
    c = json.dumps(dict(t={k: list(v) for k, v in TUR.items()}), ensure_ascii=False)
    return page('İç Ses Psikolojik Danışmanlık', 'Klinik psikolog. Yüz yüze ve çevrimiçi görüşme.', ['Newsreader:ital,wght@0,300;0,400;1,300;1,400', 'Inter:wght@400;500'], BASE_CSS + CSS, body, JS, c, dict(cta=['İlk görüşme', '#randevu'], addr='Örnek Sok. · Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/ses', exist_ok=True); open(R + '/ses/index.html', 'w', encoding='utf-8').write(render()); print('ses ok')
