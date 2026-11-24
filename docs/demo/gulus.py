# -*- coding: utf-8 -*-
"""Gülüş Diş: diş kliniği. Açık mavi, DM Serif, yumuşak bento kartlar, tedavi adım izleyici, sabit randevu şeridi."""
import json
from common import *
IDX = 8
f = foto.F[IDX]
ph = lambda k, w=900: foto.url(f[k % len(f)], w)
TED = {
 'Check-up': ('Ağız muayenesi, panoramik film ve plak kontrolü.', [('Muayene', '20 dk'), ('Panoramik film', '5 dk'), ('Tedavi planı', '15 dk')], 'Ücretsiz ilk muayene'),
 'Diş beyazlatma': ('Ofis tipi beyazlatma, tek seansta.', [('Ölçü ve renk tespiti', '15 dk'), ('Jel uygulama', '45 dk'), ('Koruma ve bakım notu', '10 dk')], '1 seans'),
 'İmplant': ('Eksik diş için kalıcı çözüm.', [('3 boyutlu tomografi', '15 dk'), ('Implant yerleştirme', '60 dk'), ('İyileşme kontrolü', '3 ay sonra'), ('Üst yapı', '2 seans')], '4-6 ay'),
 'Ortodonti': ('Şeffaf plak ve tel tedavisi.', [('Ölçü ve plan', '30 dk'), ('Plak teslimi', '20 dk'), ('Aylık kontrol', '15 dk')], '8-18 ay'),
 'Çocuk diş': ('Korkutmadan, oyunla tanışarak.', [('Tanışma', '10 dk'), ('Muayene', '15 dk'), ('Flor uygulaması', '10 dk')], 'Randevu şart'),
}
CSS = '''
:root{--bg:#f3f8fb;--ink:#0b2e4f;--mut:#566f86;--ac:#2fa4d9;--ac2:#0b2e4f;--ln:rgba(11,46,79,.14);--hf:'DM Serif Display',Georgia,serif;--mono:'DM Sans',sans-serif;--bf:'DM Sans',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 18px/1.65 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:400;line-height:1;letter-spacing:-.01em;overflow-wrap:break-word;min-width:0}
.btn{border-radius:16px;font-family:var(--bf);font-weight:700;font-size:16px;text-transform:none;letter-spacing:0}
nav.top{position:fixed;top:16px;left:50%;transform:translateX(-50%);z-index:50;width:min(1180px,calc(100% - 32px));display:flex;align-items:center;gap:24px;padding:10px 12px 10px 26px;background:rgba(255,255,255,.88);backdrop-filter:blur(14px);border-radius:22px;box-shadow:0 10px 40px -20px rgba(11,46,79,.5)}
.lg{font:400 26px var(--hf);text-decoration:none;margin-right:auto;color:var(--ink)}.lg b{color:var(--ac)}
nav.top ul{display:flex;gap:26px;list-style:none;padding:0}nav.top li a{font:600 15px var(--bf);text-decoration:none;color:var(--ink)}nav.top li a:hover{color:var(--ac)}
nav.top .btn{background:var(--ink);color:#fff;padding:13px 22px}
.hero{padding:130px clamp(20px,4vw,56px) 40px;max-width:1500px;margin:auto}
.hero .g{display:grid;grid-template-columns:repeat(12,1fr);grid-template-rows:auto auto;gap:16px}
.hero .t{grid-column:1/8;background:#fff;border-radius:36px;padding:clamp(28px,4vw,64px);display:flex;flex-direction:column;justify-content:center}
.hero h1{font-size:clamp(52px,6.8vw,112px)}.hero h1 em{font-style:italic;color:var(--ac)}.hero p{color:var(--mut);max-width:28em;margin:20px 0 28px}.hero .bt{display:flex;gap:10px;flex-wrap:wrap}.hero .btn.p{background:var(--ac);color:#fff;padding:18px 30px}.hero .btn.g2{background:var(--bg);color:var(--ink);padding:18px 28px}
.hero .i1{grid-column:8/13;grid-row:1/3;border-radius:36px;overflow:hidden;position:relative;min-height:540px}.hero .i1 img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.hero .k{grid-column:1/4;background:var(--ink);color:#fff;border-radius:28px;padding:26px}.hero .k b{font:400 52px var(--hf);display:block;line-height:1}.hero .k span{color:#a9c4d8}
.hero .k2{grid-column:4/8;background:var(--ac);color:#fff;border-radius:28px;padding:26px;display:flex;align-items:center;gap:16px;font:600 19px/1.3 var(--bf)}
section.s{padding:min(15vh,140px) clamp(20px,4vw,56px) 4vh;max-width:1380px;margin:auto}
.hd h2{font-size:clamp(42px,5.8vw,92px);margin-bottom:5vh}.hd h2 em{font-style:italic;color:var(--ac)}
.tm{display:grid;grid-template-columns:.8fr 1.2fr;gap:20px}.tm .ls{background:#fff;border-radius:32px;padding:14px;display:flex;flex-direction:column;gap:4px}.tm .ls button{text-align:left;min-height:64px;padding:0 24px;border:0;border-radius:20px;background:transparent;color:var(--ink);font:600 19px var(--bf);cursor:pointer;transition:background .2s}.tm .ls button:hover{background:var(--bg)}.tm .ls button[aria-pressed=true]{background:var(--ac);color:#fff}
.tm .dt{background:#fff;border-radius:32px;padding:clamp(26px,4vw,52px)}.tm .dt h3{font-size:clamp(34px,4vw,56px)}.tm .dt p{color:var(--mut);margin:12px 0 26px}.tm .dt .su{display:inline-block;background:var(--bg);border-radius:30px;padding:8px 18px;font-weight:700;font-size:15px;margin-bottom:22px}
.tm ol{list-style:none;padding:0;margin:0;position:relative}.tm ol:before{content:'';position:absolute;left:19px;top:20px;bottom:20px;width:2px;background:var(--ln)}.tm li{display:flex;align-items:center;gap:18px;padding:12px 0;position:relative;font-weight:600}.tm li i{width:40px;height:40px;border-radius:50%;background:var(--ac);color:#fff;display:grid;place-items:center;font:400 18px var(--hf);font-style:normal;flex:none;z-index:1}.tm li small{margin-left:auto;color:var(--mut);font-weight:600}
.bn{display:grid;grid-template-columns:repeat(12,1fr);gap:16px;margin-top:6vh}.bn .a{grid-column:span 5;aspect-ratio:5/4;border-radius:32px;overflow:hidden;position:relative}.bn .b{grid-column:span 7;background:var(--ink);color:#fff;border-radius:32px;padding:clamp(26px,4vw,52px);display:flex;flex-direction:column;justify-content:center;gap:14px}.bn .b h3{font-size:clamp(34px,4vw,56px)}.bn .b p{color:#a9c4d8}
.bn img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .8s}.bn .a:hover img{transform:scale(1.04)}.bn .c{grid-column:span 4;background:#fff;border-radius:28px;padding:28px}.bn .c h3{font-size:30px;margin-bottom:8px}.bn .c p{color:var(--mut)}
.ap{margin:8vh clamp(14px,3vw,40px) 0;background:var(--ink);color:#fff;border-radius:44px;padding:clamp(30px,5vw,70px);display:grid;grid-template-columns:1fr 1fr;gap:5vw;align-items:center}.ap h2{font-size:clamp(42px,5.8vw,92px)}.ap h2 em{font-style:italic;color:var(--ac)}.ap form{display:grid;gap:12px}.ap input,.ap select{min-height:56px;border:0;border-radius:16px;padding:0 18px;font:500 17px var(--bf);background:rgba(255,255,255,.1);color:#fff}.ap select option{color:#0b2e4f}.ap input::placeholder{color:#a9c4d8}
.ap .btn{background:var(--ac);color:#fff;min-height:58px;border:0;cursor:pointer}.ap .ok{display:none;background:var(--ac);padding:14px 18px;border-radius:16px;font-weight:600}.ap .ok.on{display:block}
footer{padding:70px clamp(20px,4vw,56px) 36px;max-width:1380px;margin:auto;display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px}footer b{font:400 30px var(--hf)}footer a{display:block;color:var(--ink);text-decoration:none;padding:3px 0}footer a:hover{color:var(--ac)}footer p{color:var(--mut)}
@media(max-width:860px){
nav.top ul,nav.top>.btn{display:none}nav.top{padding:8px 8px 8px 20px;top:10px;width:calc(100% - 20px)}nav.top .hm{border-radius:14px;margin-left:auto}
.hero{padding-top:90px}.hero .g,.tm,.bn,.ap,footer{grid-template-columns:1fr}.hero .g>*{grid-column:1!important;grid-row:auto!important}.hero .i1{min-height:300px;order:-1}.bn>*{grid-column:1!important}
.mb{left:12px;right:12px;bottom:12px;background:#fff;border:0;border-radius:22px;box-shadow:0 14px 40px -12px rgba(11,46,79,.55);grid-template-columns:1fr 1fr 1.5fr;padding:6px;gap:6px}.mb a{min-height:50px;border-radius:16px;color:var(--ink);font:700 15px var(--bf);letter-spacing:0;text-transform:none}.mb a.p{background:var(--ac);color:#fff}
.mm{background:var(--bg);color:var(--ink);inset:10px;border-radius:30px;padding:90px 24px 110px;--ln:rgba(11,46,79,.14);--ac:#2fa4d9;--mut:#566f86}.mm a{font:400 clamp(40px,12vw,64px)/1.15 var(--hf);color:var(--ink);border-bottom:0;padding:8px 0}.mm small{color:var(--mut);font:600 14px var(--bf);text-transform:none;letter-spacing:0}
footer{padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,rd=OK.reduce;
 if(!rd){gsap.from('.hero .g>*',{y:50,opacity:0,scale:.97,duration:.9,stagger:.1,ease:'power3.out'});
  gsap.utils.toArray('.hd h2,.bn>*,.ap').forEach(function(e,i){gsap.from(e,{y:50,opacity:0,duration:.8,delay:(i%3)*.08,scrollTrigger:{trigger:e,start:'top 92%'}})})}
 function sh(k){var d=C.t[k];$$('.ls button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.k===k)});$('#t').textContent=k;$('#d').textContent=d[0];$('#su').textContent='Toplam süre: '+d[2];$('#st').innerHTML=d[1].map(function(x,i){return '<li><i>'+(i+1)+'</i>'+x[0]+'<small>'+x[1]+'</small></li>'}).join('')}
 $$('.ls button').forEach(function(b){b.onclick=function(){sh(b.dataset.k)}});sh('Check-up');
 $('#fm').onsubmit=function(e){e.preventDefault();var o=$('#fo');o.textContent='Teşekkürler '+$('#fn').value+'. '+$('#fk').value+' için randevu isteğin alındı, kısa sürede arayacağız.';o.classList.add('on')};
});
'''
def render():
    ls = ''.join('<button type="button" data-k="%s" aria-pressed="false">%s</button>' % (k, k) for k in TED)
    opt = ''.join('<option>%s</option>' % k for k in TED)
    body = f'''<div id="pre" role="status"><div><b>GÜLÜŞ</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">Gülüş<b>.</b></a><ul><li><a href="#tedavi">Tedaviler</a></li><li><a href="#klinik">Klinik</a></li><li><a href="#randevu">Randevu</a></li></ul><a class="btn" href="#randevu">Randevu al</a></nav>
<main><header class="hero" id="hero"><div class="g"><div class="t"><h1>Korkmadan <em>gülümse.</em></h1><p>Ağrısız anlatan, acele etmeyen bir diş kliniği. İlk muayene ücretsiz, fiyatı tedaviden önce yazılı veririz.</p><div class="bt"><a class="btn p" href="#randevu">Randevu al</a><a class="btn g2" href="#tedavi">Tedavileri gör</a></div></div><div class="i1"><img src="{ph(0, 1200)}" alt="Hasta ile konuşan diş hekimi" fetchpriority="high"></div><div class="k"><b>Ücretsiz</b><span>ilk muayene</span></div><div class="k2">Acil diş ağrısında aynı gün muayene.</div></div></header>
<section class="s" id="tedavi"><div class="hd"><h2>Neye ihtiyacın <em>var?</em></h2></div><div class="tm"><div class="ls" role="group" aria-label="Tedavi">{ls}</div><div class="dt"><h3 id="t"></h3><p id="d"></p><span class="su" id="su"></span><ol id="st"></ol></div></div></section>
<section class="s" id="klinik"><div class="hd"><h2>Kliniğimiz <em>böyle</em></h2></div><div class="bn"><div class="a"><img src="{ph(1, 900)}" alt="Tedavi odası" loading="lazy"></div><div class="b"><h3>Her hastaya tek hekim.</h3><p>Muayeneyi yapan hekim tedaviyi de yapar. Kontrole geldiğinde seni tanıyan yüz karşılar.</p></div><div class="c"><h3>Steril</h3><p>Aletler tek kullanımlık paketlerde açılır.</p></div><div class="c"><h3>Yazılı plan</h3><p>Ne yapılacağı, kaç seans sürdüğü ve fiyatı elinde olur.</p></div><div class="a" style="grid-column:span 4"><img src="{ph(2, 800)}" alt="Bekleme salonu" loading="lazy"></div></div></section>
<section class="ap" id="randevu"><div><h2>Randevu <em>iste</em></h2></div><form id="fm"><input id="fn" required placeholder="Adınız" aria-label="Adınız" autocomplete="name"><select id="fk" aria-label="Tedavi">{opt}</select><button class="btn" type="submit">Randevu iste</button><p class="ok" id="fo" aria-live="polite"></p></form></section></main>
<footer><div><b>Gülüş Diş Kliniği</b><p>Örnek Cad. Ankara · Hafta içi 09:00 - 19:00</p></div><div><p>Sayfalar</p><a href="#tedavi">Tedaviler</a><a href="#klinik">Klinik</a><a href="#randevu">Randevu</a></div><div><p>İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div></footer>'''
    c = json.dumps(dict(t={k: [v[0], v[1], v[2]] for k, v in TED.items()}), ensure_ascii=False)
    return page('Gülüş Diş Kliniği', 'Ağrısız diş tedavisi. İlk muayene ücretsiz.', ['DM+Serif+Display:ital@0;1', 'DM+Sans:wght@400;500;600;700'], BASE_CSS + CSS, body, JS, c, dict(cta=['Randevu al', '#randevu'], addr='Örnek Cad. · Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/gulus', exist_ok=True); open(R + '/gulus/index.html', 'w', encoding='utf-8').write(render()); print('gulus ok')
