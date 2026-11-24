# -*- coding: utf-8 -*-
"""Isı Usta: kombi/klima servisi. Lacivert + turuncu, bloklu, arıza seçici ve tahmini süre/fiyat, şerit bantlar."""
import json
from common import *
IDX = 0
f = foto.F[IDX]
ph = lambda k, w=900: foto.url(f[k % len(f)], w)
SORUN = {
 'Kombi çalışmıyor': ('Basınç, ateşleme veya pompa kontrolü', '60-90 dk', 650, 'Aynı gün'),
 'Radyatör ısınmıyor': ('Petek temizliği ve hava alma', '90-120 dk', 800, '24 saat içinde'),
 'Klima soğutmuyor': ('Gaz kontrolü ve filtre temizliği', '60 dk', 700, 'Aynı gün'),
 'Su damlatıyor': ('Conta ve bağlantı kontrolü', '45-60 dk', 550, 'Aynı gün'),
 'Yıllık bakım': ('Kombi tam bakım ve verim ölçümü', '60 dk', 900, 'Randevuyla'),
}
CSS = '''
:root{--bg:#f4efe8;--ink:#0f2a3d;--mut:#4d6272;--ac:#e8502b;--ac2:#0f2a3d;--ln:rgba(15,42,61,.2);--hf:'Archivo',system-ui,sans-serif;--mono:'Inter',sans-serif;--bf:'Inter',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 17px/1.6 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:900;letter-spacing:-.035em;line-height:.95;text-transform:uppercase;overflow-wrap:break-word;min-width:0}
.btn{border-radius:0;font-family:var(--bf);font-weight:800;font-size:15px;text-transform:none;letter-spacing:0}
.tape{height:14px;background:repeating-linear-gradient(-45deg,var(--ac) 0 18px,var(--ink) 18px 36px)}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;align-items:center;gap:28px;padding:16px clamp(20px,4vw,56px);background:var(--ink);color:#fff}
.lg{font:900 24px var(--hf);text-transform:uppercase;letter-spacing:-.03em;text-decoration:none;margin-right:auto}.lg b{color:var(--ac)}
nav.top ul{display:flex;gap:26px;list-style:none;padding:0}nav.top li a{font:700 14px var(--bf);text-decoration:none}nav.top li a:hover{color:var(--ac)}
nav.top .tel{background:var(--ac);color:#fff;padding:12px 22px;font-weight:800;text-decoration:none}
.hero{padding-top:70px;background:var(--ink);color:#fff;position:relative}
.hero .g{display:grid;grid-template-columns:1.05fr .95fr;min-height:calc(100svh - 84px)}
.hero .tx{padding:clamp(40px,7vh,90px) clamp(20px,4vw,56px);display:flex;flex-direction:column;justify-content:center}
.hero h1{font-size:clamp(54px,8.4vw,150px)}.hero h1 em{font-style:normal;color:var(--ac)}.hero p{max-width:25em;margin:24px 0 30px;color:#c9d6df;font-size:19px}
.hero .bt{display:flex;gap:12px;flex-wrap:wrap}.hero .btn.p{background:var(--ac);color:#fff;padding:18px 30px}.hero .btn.g2{border:2px solid #fff;color:#fff;background:transparent;padding:16px 28px}
.hero .im{position:relative;min-height:50vh;overflow:hidden}.hero .im img{position:absolute;inset:-4% 0;width:100%;height:108%;object-fit:cover}
.hero .badge{position:absolute;left:-36px;bottom:40px;z-index:3;background:var(--ac);color:#fff;padding:20px 26px;font:900 26px/1 var(--hf);text-transform:uppercase;transform:rotate(-3deg)}
section.s{padding:min(15vh,140px) clamp(20px,4vw,56px) 4vh;max-width:1400px;margin:auto}
.hd h2{font-size:clamp(46px,7.4vw,120px);margin-bottom:5vh}.hd h2 em{font-style:normal;color:var(--ac)}
.dg{display:grid;grid-template-columns:1fr 1.1fr;gap:0;border:3px solid var(--ink)}
.dg .ls{display:flex;flex-direction:column}.dg .ls button{text-align:left;min-height:72px;padding:0 24px;border:0;border-bottom:3px solid var(--ink);background:transparent;color:var(--ink);font:800 20px var(--bf);cursor:pointer;display:flex;justify-content:space-between;align-items:center;transition:background .2s,padding .25s}
.dg .ls button:last-child{border-bottom:0}.dg .ls button:hover{padding-left:34px}.dg .ls button:after{content:'→';font-weight:900}.dg .ls button[aria-pressed=true]{background:var(--ac);color:#fff}
.dg .rs{background:var(--ink);color:#fff;padding:clamp(26px,4vw,52px);display:flex;flex-direction:column;gap:18px}.dg .rs h3{font-size:clamp(34px,4vw,58px);color:var(--ac)}.dg .rs p{color:#c9d6df}
.dg .kv{display:grid;grid-template-columns:repeat(3,1fr);gap:2px;background:rgba(255,255,255,.2);margin-top:6px}.dg .kv div{background:var(--ink);padding:16px 14px}.dg .kv small{display:block;color:#9bb0bf;font-weight:600;font-size:13px}.dg .kv b{font:900 24px var(--hf)}
.dg .rs .btn{background:var(--ac);color:#fff;padding:16px 26px;align-self:flex-start;margin-top:8px}
.st{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border:3px solid var(--ink);counter-reset:s}.st div{padding:30px 24px;border-right:3px solid var(--ink);counter-increment:s}.st div:last-child{border-right:0}.st div:before{content:'0' counter(s);font:900 64px var(--hf);color:var(--ac);display:block;line-height:1;margin-bottom:12px}.st h3{font-size:26px;margin-bottom:8px}.st p{color:var(--mut)}
.br{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:6vh}.br .im{aspect-ratio:4/3;position:relative;overflow:hidden}.br img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .7s}.br .im:hover img{transform:scale(1.04)}
.cl{background:var(--ac);color:#fff;padding:min(12vh,110px) clamp(20px,4vw,56px)}.cl>div{max-width:1400px;margin:auto;display:grid;grid-template-columns:1fr 1fr;gap:5vw;align-items:end}.cl h2{font-size:clamp(46px,7.6vw,124px)}.cl form{display:grid;gap:10px}.cl input,.cl select{min-height:56px;border:3px solid var(--ink);background:#fff;padding:0 16px;font:600 17px var(--bf);color:var(--ink);border-radius:0}.cl .btn{background:var(--ink);color:#fff;min-height:58px;border:0;cursor:pointer}.cl .ok{display:none;background:var(--ink);padding:14px;font-weight:700}.cl .ok.on{display:block}
footer{background:var(--ink);color:#fff;padding:60px clamp(20px,4vw,56px) 30px;display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px}footer b{font:900 32px var(--hf);text-transform:uppercase}footer a{display:block;color:#fff;text-decoration:none;padding:3px 0}footer a:hover{color:var(--ac)}footer p{color:#9bb0bf}
@media(max-width:860px){
nav.top ul,nav.top>.tel{display:none}nav.top{padding:12px 16px}nav.top .hm{margin-left:auto;border-radius:0}
.hero .g{grid-template-columns:1fr;min-height:0}.hero .im{order:-1;min-height:34vh}.hero .badge{left:12px;bottom:12px;font-size:20px}.hero h1{font-size:clamp(48px,15vw,90px)}
.dg,.st,.br,.cl>div,footer{grid-template-columns:1fr}.st div{border-right:0;border-bottom:3px solid var(--ink)}.st div:last-child{border-bottom:0}.dg .kv{grid-template-columns:1fr}
.mb{left:0;right:0;bottom:0;background:var(--ink);border:0;border-top:4px solid var(--ac);border-radius:0;grid-template-columns:1fr 1fr;padding:0 0 max(0px,env(safe-area-inset-bottom))}.mb a{min-height:60px;border-radius:0;color:#fff;font:800 16px var(--bf);letter-spacing:0;text-transform:none}.mb a:nth-child(2){display:none}.mb a+a{border-left:1px solid rgba(255,255,255,.2)}.mb a.p{background:var(--ac)}
.mm{background:var(--ac);color:#fff;inset:0;padding:90px 20px 110px;--ln:rgba(255,255,255,.35);--ac:#0f2a3d;--mut:#ffe2d8}.mm a{font:900 clamp(46px,14vw,80px)/1 var(--hf);text-transform:uppercase;letter-spacing:-.03em;color:#fff;border-bottom:4px solid var(--ink);padding:10px 0}.mm small{color:#ffe2d8;font:700 14px var(--bf);text-transform:none;letter-spacing:0}
footer{padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce;
 if(!rd){gsap.from('.hero h1',{xPercent:-8,opacity:0,duration:1,ease:'power4.out'});gsap.from('.hero .tx>*:not(h1)',{y:30,opacity:0,stagger:.12,duration:.8,delay:.4});gsap.from('.badge',{scale:0,rotate:-20,duration:.7,delay:.9,ease:'back.out(2)'});
  gsap.to('.hero .im img',{yPercent:8,ease:'none',scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom top',scrub:true}});
  gsap.utils.toArray('.hd h2,.st div,.br .im').forEach(function(e,i){gsap.from(e,{y:50,opacity:0,duration:.8,delay:(i%4)*.07,scrollTrigger:{trigger:e,start:'top 92%'}})})}
 function sh(k){var d=C.s[k];$$('.ls button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.k===k)});$('#t').textContent=k;$('#d').textContent=d[0];$('#du').textContent=d[1];$('#pr').textContent=money(d[2])+'+';$('#wh').textContent=d[3]}
 $$('.ls button').forEach(function(b){b.onclick=function(){sh(b.dataset.k)}});sh('Kombi çalışmıyor');
 $('#fm').onsubmit=function(e){e.preventDefault();var o=$('#fo');o.textContent='Teşekkürler '+$('#fn').value+'. "'+$('#fs').value+'" için usta yönlendiriyoruz, kısa süre içinde arayacağız.';o.classList.add('on')};
});
'''
def render():
    ls = ''.join('<button type="button" data-k="%s" aria-pressed="false">%s</button>' % (k, k) for k in SORUN)
    opt = ''.join('<option>%s</option>' % k for k in SORUN)
    body = f'''<div id="pre" role="status"><div><b>ISI USTA</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">Isı<b>.</b>Usta</a><ul><li><a href="#ariza">Arıza</a></li><li><a href="#surec">Nasıl çalışır</a></li><li><a href="#cagri">Çağır</a></li></ul><a class="tel" href="tel:+905320000000">Hemen ara</a></nav>
<main><header class="hero" id="hero"><div class="g"><div class="tx"><h1>Kombin <em>yanmıyor</em> mu?</h1><p>Kombi, klima ve doğalgaz tesisatı için aynı gün servis. Önce arıza ve fiyat, sonra işçilik.</p><div class="bt"><a class="btn p" href="#ariza">Arızayı seç</a><a class="btn g2" href="tel:+905320000000">Hemen ara</a></div></div><div class="im"><img src="{ph(0, 1400)}" alt="Teknisyen kombi bakımı yapıyor" fetchpriority="high"><div class="badge">Aynı gün servis</div></div></div></header><div class="tape"></div>
<section class="s" id="ariza"><div class="hd"><h2>Sorun <em>ne?</em></h2></div><div class="dg"><div class="ls" role="group" aria-label="Arıza">{ls}</div><div class="rs"><h3 id="t"></h3><p id="d"></p><div class="kv"><div><small>Süre</small><b id="du"></b></div><div><small>Başlangıç fiyatı</small><b id="pr"></b></div><div><small>Gelme süresi</small><b id="wh"></b></div></div><a class="btn" href="#cagri">Usta çağır</a></div></div></section>
<section class="s" id="surec"><div class="hd"><h2>Dört adımda <em>servis</em></h2></div><div class="st"><div><h3>Ara</h3><p>Arızayı anlat, tahmini fiyatı söyleyelim.</p></div><div><h3>Randevu</h3><p>Sana uygun saatte usta yola çıkar.</p></div><div><h3>Tespit</h3><p>Usta bakar, yapılacak işi ve fiyatı yazar.</p></div><div><h3>Onayla</h3><p>Sen onaylarsan işe başlanır, garanti belgesi verilir.</p></div></div>
<div class="br"><div class="im"><img src="{ph(1, 800)}" alt="Klima bakımı" loading="lazy"></div><div class="im"><img src="{ph(2, 800)}" alt="Kombi parçası değişimi" loading="lazy"></div><div class="im"><img src="{ph(3, 800)}" alt="Tesisat kontrolü" loading="lazy"></div></div></section>
<section class="cl" id="cagri"><div><h2>Usta<br>çağır.</h2><form id="fm"><input id="fn" required placeholder="Adınız" aria-label="Adınız" autocomplete="name"><select id="fs" aria-label="Arıza">{opt}</select><button class="btn" type="submit">Beni arayın</button><p class="ok" id="fo" aria-live="polite"></p></form></div></section></main><div class="tape"></div>
<footer><div><b>Isı Usta</b><p>Kombi ve klima servisi · Ankara</p></div><div><p>Sayfalar</p><a href="#ariza">Arıza</a><a href="#surec">Nasıl çalışır</a><a href="#cagri">Çağır</a></div><div><p>İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div></footer>'''
    c = json.dumps(dict(s={k: list(v) for k, v in SORUN.items()}), ensure_ascii=False)
    return page('Isı Usta Kombi ve Klima Servisi', 'Kombi, klima ve tesisat servisi. Aynı gün usta.', ['Archivo:wght@700;800;900', 'Inter:wght@400;600;700;800'], BASE_CSS + CSS, body, JS, c, dict(cta=['Usta çağır', '#cagri'], addr='Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/isi', exist_ok=True); open(R + '/isi/index.html', 'w', encoding='utf-8').write(render()); print('isi ok')
