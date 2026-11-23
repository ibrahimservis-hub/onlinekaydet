# -*- coding: utf-8 -*-
"""Lumi Estetik: cilt bakım kliniği. Kırmızı zemin, fotoğrafın arkasında dev yazı, cilt tipi testi, ürün üçlüsü."""
import json
from common import *
IDX = 7
f = foto.F[IDX]
ph = lambda k, w=900: foto.url(f[k % len(f)], w)
Q = [('Cildin gün sonunda nasıl hissettiriyor?', [('Parlak ve yağlı', 'y'), ('Gergin ve kuru', 'k'), ('Bazı bölgelerde yağlı', 'k2'), ('Rahat, dengeli', 'd')]),
     ('En çok neyi düzeltmek istiyorsun?', [('Sivilce ve lekeler', 'y'), ('Kuruluk ve çizgiler', 'k'), ('Gözenekler', 'k2'), ('Işıltı', 'd')])]
SONUC = {'y': ('Yağlı ve karma eğilim', 'Haftada bir derin temizlik, hafif nem bakımı.', 1450), 'k': ('Kuru ve hassas', 'Nem ve bariyer odaklı hydrafacial serisi.', 1700), 'k2': ('Karma cilt', 'T bölgesine temizlik, yanaklara nem. Karma bakım.', 1550), 'd': ('Dengeli cilt', 'Işıltı bakımı ve ayda bir koruyucu seans.', 1300)}
CSS = '''
:root{--bg:#c4161c;--ink:#fff3ee;--mut:#ffc9bd;--ac:#fff3ee;--ac2:#5a0508;--ln:rgba(255,243,238,.3);--hf:'Cormorant',Georgia,serif;--mono:'Manrope',sans-serif;--bf:'Manrope',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 17px/1.65 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:500;line-height:.95;letter-spacing:-.015em;overflow-wrap:break-word;min-width:0}
.btn{border-radius:0;font-family:var(--bf);text-transform:none;letter-spacing:.02em;font-size:16px;font-weight:700}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;align-items:center;padding:20px clamp(20px,4vw,56px);gap:30px;color:var(--ink);transition:background .3s}nav.top.solid{background:var(--bg)}
.lg{font:600 32px var(--hf);font-style:italic;text-decoration:none;margin-right:auto}
nav.top ul{display:flex;gap:30px;list-style:none;padding:0}nav.top li a{font:600 15px var(--bf);text-decoration:none;opacity:.9}nav.top li a:hover{opacity:1;text-decoration:underline;text-underline-offset:6px}
nav.top .btn{border:1px solid var(--ink);padding:11px 22px;background:transparent;color:var(--ink)}nav.top .btn:hover{background:var(--ink);color:var(--bg)}nav.top.solid .btn{color:var(--ink)}
.hero{min-height:100svh;position:relative;display:grid;place-items:center;overflow:clip;padding:100px 20px 60px}
.hero .w{position:absolute;left:50%;top:48%;transform:translate(-50%,-50%);font:600 clamp(200px,40vw,700px)/.7 var(--hf);font-style:italic;color:#e0242b;letter-spacing:-.04em;white-space:nowrap;user-select:none;pointer-events:none}
.hero .ph{position:relative;z-index:2;width:min(34vw,460px);aspect-ratio:3/4;border-radius:240px 240px 0 0;overflow:hidden}.hero .ph img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.hero h1{position:absolute;z-index:3;left:clamp(20px,4vw,56px);bottom:9vh;font-size:clamp(52px,7vw,120px);max-width:8em}.hero h1 em{color:#fff;font-style:italic}
.hero .rt{position:absolute;z-index:3;right:clamp(20px,4vw,56px);bottom:9vh;max-width:21em}.hero .rt p{margin-bottom:18px}.hero .btn{display:inline-block;background:var(--ink);color:var(--bg);padding:15px 28px}
section.s{padding:min(16vh,150px) clamp(20px,4vw,56px) 4vh;max-width:1400px;margin:auto}
.hd{margin-bottom:5vh}.hd h2{font-size:clamp(46px,7.6vw,120px)}.hd h2 i{color:#fff}.hd p{max-width:27em;color:var(--mut);margin-top:18px}
.qz{display:grid;grid-template-columns:1fr 1fr;gap:5vw;align-items:center}.qz .im{aspect-ratio:4/5;position:relative;overflow:hidden;border-radius:200px 200px 0 0}.qz .im img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .8s}.qz .im:hover img{transform:scale(1.03)}
.qb{border:1px solid var(--ln);padding:clamp(24px,3.4vw,46px)}.qb .st{font:700 14px var(--bf);color:var(--mut);margin-bottom:12px}.qb h3{font-size:clamp(30px,3.4vw,48px);margin-bottom:22px}
.qb .op{display:grid;gap:10px}.qb .op button{text-align:left;min-height:56px;padding:0 20px;border:1px solid var(--ln);background:transparent;color:var(--ink);font:600 17px var(--bf);cursor:pointer;transition:background .2s,color .2s,border-color .2s}.qb .op button:hover{background:var(--ink);color:var(--bg)}
.qb .res h3{font-size:clamp(38px,4.4vw,64px)}.qb .res b{display:block;font:500 46px var(--hf);margin:16px 0}.qb .rs{background:none;border:0;color:var(--mut);text-decoration:underline;cursor:pointer;font:600 15px var(--bf);margin-left:14px}
.pb{height:3px;background:var(--ln);margin-bottom:22px}.pb i{display:block;height:100%;background:var(--ink);width:0;transition:width .4s}
.tr{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}.tr article{display:grid;gap:14px}.tr .im{aspect-ratio:4/5;position:relative;overflow:hidden}.tr img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .8s}.tr article:hover img{transform:scale(1.04)}
.tr article:nth-child(2){margin-top:60px}.tr h3{font-size:34px}.tr p{color:var(--mut)}.tr .pr{display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--ln);padding-top:12px;font-weight:700}.tr .pr span{font:500 30px var(--hf)}
.sp{display:grid;grid-template-columns:1.2fr .8fr;gap:5vw;align-items:end;margin:6vh 0}.sp .im{aspect-ratio:16/10;position:relative;overflow:hidden}.sp img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.sp blockquote{font:500 clamp(30px,3.6vw,52px)/1.08 var(--hf);font-style:italic}.sp cite{display:block;font:600 15px var(--bf);font-style:normal;color:var(--mut);margin-top:16px}
.ap{background:var(--ink);color:var(--bg);padding:min(14vh,120px) clamp(20px,4vw,56px)}.ap>div{max-width:1400px;margin:auto;display:grid;grid-template-columns:1fr 1fr;gap:5vw;align-items:end}.ap h2{font-size:clamp(46px,7.6vw,120px)}.ap form{display:grid;gap:12px}.ap input,.ap select{min-height:54px;border:0;border-bottom:1px solid var(--bg);background:transparent;padding:0;font:600 17px var(--bf);color:var(--bg);border-radius:0}.ap label{font:700 14px var(--bf)}.ap .btn{background:var(--bg);color:var(--ink);min-height:56px;border:0;cursor:pointer}.ap .ok{display:none;font-weight:700}.ap .ok.on{display:block}
footer{padding:80px clamp(20px,4vw,56px) 30px;overflow:clip}footer .t{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px}footer b{font:600 32px var(--hf);font-style:italic}footer a{display:block;color:var(--ink);text-decoration:none;padding:3px 0}footer a:hover{text-decoration:underline}footer p{color:var(--mut)}
footer .big{font:600 clamp(120px,34vw,560px)/.7 var(--hf);font-style:italic;color:#e0242b;margin:40px 0 0;text-align:center;letter-spacing:-.04em}
@media(max-width:860px){
nav.top ul,nav.top>.btn{display:none}nav.top{padding:12px 16px}nav.top .hm{margin-left:auto;border-radius:50%}
.hero{padding:100px 20px 160px;align-content:center}.hero .ph{width:72vw}.hero .w{top:42%;font-size:62vw}.hero h1{position:relative;left:auto;bottom:auto;grid-area:2;margin-top:24px;font-size:clamp(46px,14vw,80px)}.hero .rt{position:relative;right:auto;bottom:auto;grid-area:3;margin-top:16px}
.qz,.tr,.sp,.ap>div,footer .t{grid-template-columns:1fr}.tr article:nth-child(2){margin-top:0}.qz .im{max-height:420px;width:80%;margin:auto}
.mb{left:14px;right:14px;bottom:14px;background:var(--ink);color:var(--bg);border:0;border-radius:0;grid-template-columns:1fr 1fr 1.4fr;padding:0}.mb a{color:var(--bg);min-height:54px;border-radius:0;font:700 15px var(--bf);letter-spacing:.02em;text-transform:none}.mb a+a{border-left:1px solid rgba(90,5,8,.25)}.mb a.p{background:var(--ac2);color:var(--ink)}
.mm{background:var(--ink);color:var(--bg);inset:0;padding:100px 28px 110px;--ln:rgba(90,5,8,.25);--ac:#5a0508;--mut:#8c2a2f}.mm a{font:500 clamp(48px,15vw,84px)/1 var(--hf);font-style:italic;color:var(--bg);border-bottom:0;padding:8px 0}.mm small{color:#8c2a2f;font:700 14px var(--bf);text-transform:none;letter-spacing:0}
footer{padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce;
 if(!rd){var tl=gsap.timeline();tl.from('.hero .w',{scale:.85,opacity:0,duration:1.4,ease:'power3.out'}).from('.hero .ph',{clipPath:'inset(100% 0 0 0)',duration:1.2,ease:'power4.out'},'-=1').from('.hero h1,.hero .rt',{y:40,opacity:0,stagger:.15,duration:.8},'-=.5');
  gsap.to('.hero .w',{yPercent:-12,ease:'none',scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom top',scrub:true}});gsap.to('.hero .ph',{yPercent:8,ease:'none',scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom top',scrub:true}});
  gsap.utils.toArray('.tr article').forEach(function(e,i){gsap.from(e,{y:70,opacity:0,duration:.9,delay:i*.1,ease:'power3.out',scrollTrigger:{trigger:e,start:'top 92%'}})});
  gsap.from('footer .big',{yPercent:30,opacity:0,duration:1.2,scrollTrigger:{trigger:'footer',start:'top 85%'}})}
 var qi=0,sc={};function draw(){var b=$('#qb');if(qi>=C.q.length){var m=Object.keys(sc).sort(function(a,c){return sc[c]-sc[a]})[0]||'d',r=C.r[m];b.innerHTML='<div class="pb"><i style="width:100%"></i></div><div class="res"><div class="st">Sonucun</div><h3>'+r[0]+'</h3><p>'+r[1]+'</p><b>'+money(r[2])+'</b><a class="btn" style="display:inline-block;background:var(--ink);color:var(--bg);padding:14px 26px" href="#randevu">Bu bakım için randevu al</a><button class="rs" type="button" id="rs">Testi tekrarla</button></div>';$('#rs').onclick=function(){qi=0;sc={};draw()};return}
  var q=C.q[qi];b.innerHTML='<div class="pb"><i style="width:'+(qi/C.q.length*100)+'%"></i></div><div class="st">Soru '+(qi+1)+' / '+C.q.length+'</div><h3>'+q[0]+'</h3><div class="op">'+q[1].map(function(o,i){return '<button type="button" data-k="'+o[1]+'">'+o[0]+'</button>'}).join('')+'</div>';$$('#qb .op button').forEach(function(x){x.onclick=function(){sc[x.dataset.k]=(sc[x.dataset.k]||0)+1;qi++;draw()}})}
 draw();
 $('#fm').onsubmit=function(e){e.preventDefault();var o=$('#fo');o.textContent='Teşekkürler '+$('#fn').value+'. '+$('#fk').value+' için randevu isteğin alındı.';o.classList.add('on')};
});
'''
def render():
    tr = ''.join('<article><div class="im"><img src="%s" alt="%s" loading="lazy"></div><h3>%s</h3><p>%s</p><div class="pr">%s<span>%s</span></div></article>' % (ph(k, 700), n, n, d, a, p) for n, d, a, p, k in [
        ('Hydrafacial', 'Temizler, nemlendirir, aynı seansta ışıltı verir.', '45 dk', '1.700 ₺', 1), ('Leke bakımı', 'Güneş ve sivilce lekeleri için serili seanslar.', '60 dk', '1.450 ₺', 2), ('Kaş ve kirpik', 'Şekillendirme ve lifting. Tek seansta sonuç.', '40 dk', '900 ₺', 3)])
    body = f'''<div id="pre" role="status"><div><b>LUMI</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">Lumi</a><ul><li><a href="#test">Cilt testi</a></li><li><a href="#bakim">Bakımlar</a></li><li><a href="#randevu">Randevu</a></li></ul><a class="btn" href="#randevu">Randevu al</a></nav>
<main><header class="hero" id="hero"><div class="w" aria-hidden="true">Lumi</div><div class="ph"><img src="{ph(0, 1000)}" alt="Cilt bakımı yaptıran kadın" fetchpriority="high"></div><h1>Cildin için <em>doğru</em> bakım.</h1><div class="rt"><p>Uzman estetisyen önce cildine bakar, sonra ne gerektiğini söyler. Gereksiz seans önermeyiz.</p><a class="btn" href="#test">Cilt tipini bul</a></div></header>
<section class="s" id="test"><div class="qz"><div class="im"><img src="{ph(4, 900)}" alt="Cilt analizi yapan estetisyen" loading="lazy"></div><div><div class="hd"><h2>İki soruda <i>cilt tipin</i></h2></div><div class="qb" id="qb"></div></div></div></section>
<section class="s" id="bakim"><div class="hd"><h2>Öne çıkan <i>bakımlar</i></h2><p>Fiyatlar tek seans içindir. Seri alırsan indirim yapılır.</p></div><div class="tr">{tr}</div>
<div class="sp"><div class="im"><img src="{ph(5, 1200)}" alt="Klinikte bakım odası" loading="lazy"></div><div><blockquote>Önce cildi dinlemek, sonra dokunmak gerekir.</blockquote><cite>Uzm. Estetisyen Ayşe Demir</cite></div></div></section>
<section class="ap" id="randevu"><div><h2>Randevunu<br>ayır.</h2><form id="fm"><label>Adın<input id="fn" required autocomplete="name"></label><label>Bakım<select id="fk"><option>Hydrafacial</option><option>Leke bakımı</option><option>Kaş ve kirpik</option><option>Cilt analizi</option></select></label><button class="btn" type="submit">Randevu iste</button><p class="ok" id="fo" aria-live="polite"></p></form></div></section></main>
<footer><div class="t"><div><b>Lumi Estetik</b><p>Örnek Sok. Ankara · 10:00 - 20:00</p></div><div><p>Sayfalar</p><a href="#test">Cilt testi</a><a href="#bakim">Bakımlar</a><a href="#randevu">Randevu</a></div><div><p>İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div></div><div class="big" aria-hidden="true">Lumi</div></footer>'''
    c = json.dumps(dict(q=[[a, b] for a, b in Q], r=SONUC), ensure_ascii=False)
    return page('Lumi Estetik', 'Cilt analizi, hydrafacial ve leke bakımı.', ['Cormorant:ital,wght@0,500;0,600;1,500;1,600', 'Manrope:wght@400;600;700'], BASE_CSS + CSS, body, JS, c, dict(cta=['Randevu al', '#randevu'], addr='Örnek Sok. · Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/lumi', exist_ok=True); open(R + '/lumi/index.html', 'w', encoding='utf-8').write(render()); print('lumi ok')
