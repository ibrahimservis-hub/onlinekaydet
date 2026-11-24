# -*- coding: utf-8 -*-
"""Beyaz Servis: beyaz eşya servisi. Açık, ortalı; cihaz kutuları, sık görülen sorun listesi, marka şeridi yok."""
import json
from common import *
IDX = 1
f = foto.F[IDX]
ph = lambda k, w=800: foto.url(f[k % len(f)], w)
CIH = {
 'Çamaşır makinesi': (1, [('Su almıyor', 'Musluk, filtre ve su giriş valfi kontrol edilir.'), ('Sıkma yapmıyor', 'Kayış, pompa ve yük dengesi bakılır.'), ('Su boşaltmıyor', 'Pompa filtresi ve tahliye hortumu temizlenir.')]),
 'Bulaşık makinesi': (2, [('Yıkamıyor', 'Püskürtme kolları ve pompa kontrol edilir.'), ('Su tahliye etmiyor', 'Filtre ve tahliye pompası bakılır.'), ('Kapı kapanmıyor', 'Kilit ve menteşe değişimi.')]),
 'Buzdolabı': (3, [('Soğutmuyor', 'Gaz, kompresör ve fan motoru kontrol edilir.'), ('Su akıtıyor', 'Defrost tahliye kanalı temizlenir.'), ('Çok ses yapıyor', 'Fan ve kompresör titreşimi bakılır.')]),
 'Fırın': (4, [('Isıtmıyor', 'Rezistans ve termostat kontrol edilir.'), ('Kapak yanıyor', 'Sızdırmazlık ve fan kontrolü.'), ('Ekran çalışmıyor', 'Kart ve bağlantı bakılır.')]),
 'Kurutma makinesi': (5, [('Kurutmuyor', 'Rezistans ve hava kanalı temizlenir.'), ('Çok ses yapıyor', 'Rulman ve kayış kontrolü.'), ('Durmadan çalışıyor', 'Nem sensörü bakılır.')]),
 'Ankastre set': (6, [('Ocak tutuşmuyor', 'Ateşleme ve gaz valfi kontrolü.'), ('Davlumbaz çekmiyor', 'Motor ve filtre bakımı.'), ('Set kurulumu', 'Yerinde montaj ve bağlantı.')]),
}
CSS = '''
:root{--bg:#f2f6f5;--ink:#112b3c;--mut:#5a7080;--ac:#1f9d8b;--ac2:#0d5c52;--ln:rgba(17,43,60,.14);--hf:'Manrope',system-ui,sans-serif;--mono:'Manrope',sans-serif;--bf:'Manrope',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:500 17px/1.6 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:800;letter-spacing:-.04em;line-height:1.02;overflow-wrap:break-word;min-width:0}
.btn{border-radius:14px;font-family:var(--bf);font-weight:800;font-size:16px;text-transform:none;letter-spacing:0}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;align-items:center;gap:26px;padding:16px clamp(20px,4vw,56px);background:rgba(242,246,245,.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--ln);color:var(--ink)}
.lg{font:800 24px var(--hf);letter-spacing:-.04em;text-decoration:none;margin-right:auto}.lg b{color:var(--ac)}
nav.top ul{display:flex;gap:26px;list-style:none;padding:0}nav.top li a{font:700 15px var(--bf);text-decoration:none}nav.top li a:hover{color:var(--ac)}nav.top .btn{background:var(--ac);color:#fff;padding:12px 22px}
.hero{padding:140px clamp(20px,4vw,56px) 50px;text-align:center;max-width:1100px;margin:auto}
.hero h1{font-size:clamp(46px,7vw,112px)}.hero h1 em{font-style:normal;color:var(--ac)}.hero p{max-width:32em;margin:20px auto 34px;color:var(--mut);font-size:19px}
.hero .sr{display:flex;gap:8px;background:#fff;border-radius:22px;padding:8px;box-shadow:0 20px 50px -26px rgba(17,43,60,.5);max-width:640px;margin:auto}.hero .sr input{flex:1;min-height:56px;border:0;padding:0 18px;font:600 18px var(--bf);background:transparent;color:var(--ink);min-width:0}.hero .sr .btn{background:var(--ac);color:#fff;padding:0 28px;border:0;cursor:pointer}
.hero .ch{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-top:18px}.hero .ch a{background:#fff;border-radius:30px;padding:9px 18px;font-weight:700;font-size:15px;text-decoration:none;border:1px solid var(--ln);transition:all .2s}.hero .ch a:hover{background:var(--ac);color:#fff;border-color:var(--ac)}
.ph{max-width:1380px;margin:0 auto;padding:0 clamp(20px,4vw,56px)}.ph .im{aspect-ratio:21/9;border-radius:32px;overflow:hidden;position:relative}.ph img{position:absolute;inset:-6% 0;width:100%;height:112%;object-fit:cover}
section.s{padding:min(14vh,130px) clamp(20px,4vw,56px) 4vh;max-width:1380px;margin:auto}
.hd{text-align:center;margin-bottom:5vh}.hd h2{font-size:clamp(38px,5.4vw,84px)}.hd h2 em{font-style:normal;color:var(--ac)}.hd p{color:var(--mut);margin-top:12px}
.cg{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.cg button{position:relative;aspect-ratio:4/3;border:3px solid transparent;border-radius:26px;overflow:hidden;cursor:pointer;padding:0;background:#dfe9e7;transition:border-color .2s,transform .3s;text-align:left}.cg button:hover{transform:translateY(-3px)}.cg button[aria-pressed=true]{border-color:var(--ac)}
.cg img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.cg button:after{content:'';position:absolute;inset:0;background:linear-gradient(transparent 45%,rgba(10,30,40,.78))}.cg b{position:absolute;z-index:2;left:20px;bottom:16px;color:#fff;font:800 24px var(--hf);letter-spacing:-.03em}
.pb{margin-top:20px;background:#fff;border-radius:30px;padding:clamp(22px,3.4vw,44px);display:grid;grid-template-columns:.8fr 1.2fr;gap:30px}.pb h3{font-size:clamp(30px,3.6vw,50px)}.pb>div:first-child p{color:var(--mut);margin:12px 0 22px}.pb .btn{background:var(--ac);color:#fff;padding:16px 26px;display:inline-block}
.pb details{border-bottom:1px solid var(--ln);padding:4px 0}.pb details:first-child{border-top:1px solid var(--ln)}.pb summary{list-style:none;cursor:pointer;min-height:64px;display:flex;align-items:center;justify-content:space-between;font:800 20px var(--hf);letter-spacing:-.02em}.pb summary::-webkit-details-marker{display:none}.pb summary:after{content:'+';color:var(--ac);font-size:30px;transition:transform .3s}.pb details[open] summary:after{transform:rotate(45deg)}.pb details p{color:var(--mut);padding:0 0 18px}
.sg{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.sg div{background:#fff;border-radius:24px;padding:26px}.sg b{font:800 42px var(--hf);color:var(--ac);display:block;line-height:1}.sg h3{font-size:22px;margin:10px 0 6px}.sg p{color:var(--mut);font-size:16px}
.cl{margin:8vh clamp(14px,3vw,40px) 0;background:var(--ink);color:#fff;border-radius:40px;padding:clamp(30px,5vw,70px);display:grid;grid-template-columns:1fr 1fr;gap:5vw;align-items:center}.cl h2{font-size:clamp(38px,5vw,78px)}.cl form{display:grid;gap:10px}.cl input,.cl select{min-height:56px;border:0;border-radius:14px;padding:0 18px;font:600 17px var(--bf);background:rgba(255,255,255,.1);color:#fff}.cl select option{color:#112b3c}.cl input::placeholder{color:#9fb4c2}.cl .btn{background:var(--ac);color:#fff;min-height:58px;border:0;cursor:pointer}.cl .ok{display:none;background:var(--ac);padding:14px 18px;border-radius:14px;font-weight:700}.cl .ok.on{display:block}
footer{max-width:1380px;margin:auto;padding:70px clamp(20px,4vw,56px) 36px;display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px}footer b{font:800 26px var(--hf);letter-spacing:-.04em}footer a{display:block;color:var(--ink);text-decoration:none;padding:3px 0}footer a:hover{color:var(--ac)}footer p{color:var(--mut)}
@media(max-width:860px){
nav.top ul,nav.top>.btn{display:none}nav.top{padding:12px 16px}nav.top .hm{border-radius:14px;margin-left:auto}
.hero{padding-top:100px}.hero .sr{flex-direction:column}.hero .sr input{min-height:52px}.hero .sr .btn{min-height:52px}.ph .im{aspect-ratio:16/10;border-radius:22px}
.cg{grid-template-columns:1fr 1fr;gap:10px}.pb,.cl,footer{grid-template-columns:1fr}.sg{grid-template-columns:1fr 1fr}
.mb{left:12px;right:12px;bottom:12px;background:#fff;border:1px solid var(--ln);border-radius:20px;box-shadow:0 16px 40px -14px rgba(17,43,60,.5);grid-template-columns:1fr 1fr 1.5fr;padding:6px;gap:6px}.mb a{min-height:50px;border-radius:14px;color:var(--ink);font:800 15px var(--bf);letter-spacing:0;text-transform:none}.mb a+a{border:0}.mb a.p{background:var(--ac);color:#fff}
.mm{background:var(--ac);color:#fff;inset:0;padding:90px 24px 110px;--ln:rgba(255,255,255,.3);--ac:#fff;--mut:#d6f2ed}.mm a{font:800 clamp(38px,12vw,60px)/1.1 var(--hf);letter-spacing:-.04em;color:#fff;border-bottom:1px solid var(--ln);padding:12px 0}.mm small{color:#d6f2ed;font:700 14px var(--bf);text-transform:none;letter-spacing:0}
footer{padding-bottom:110px}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,rd=OK.reduce,keys=Object.keys(C.c);
 if(!rd){gsap.from('.hero>*',{y:40,opacity:0,stagger:.1,duration:.9,ease:'power3.out'});gsap.to('.ph img',{yPercent:8,ease:'none',scrollTrigger:{trigger:'.ph',start:'top bottom',end:'bottom top',scrub:true}});
  gsap.utils.toArray('.hd,.cg button,.sg div,.cl').forEach(function(e,i){gsap.from(e,{y:46,opacity:0,duration:.8,delay:(i%3)*.07,scrollTrigger:{trigger:e,start:'top 92%'}})})}
 function sh(k){$$('.cg button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.k===k)});$('#t').textContent=k;$('#ls').innerHTML=C.c[k].map(function(x,i){return '<details'+(i==0?' open':'')+'><summary>'+x[0]+'</summary><p>'+x[1]+'</p></details>'}).join('')}
 $$('.cg button').forEach(function(b){b.onclick=function(){sh(b.dataset.k)}});sh(keys[0]);
 $('#sf').onsubmit=function(e){e.preventDefault();var q=$('#sq').value.toLowerCase(),hit=keys.filter(function(k){return q.indexOf(k.split(' ')[0].toLowerCase().slice(0,5))>-1})[0];if(hit){sh(hit);document.getElementById('cihaz').scrollIntoView({behavior:rd?'auto':'smooth'})}else{document.getElementById('cihaz').scrollIntoView()}};
 $('#fm').onsubmit=function(e){e.preventDefault();var o=$('#fo');o.textContent='Teşekkürler '+$('#fn').value+'. '+$('#fk').value+' için servis kaydın alındı, seni arayacağız.';o.classList.add('on')};
});
'''
def render():
    cg = ''.join('<button type="button" data-k="%s" aria-pressed="false"><img src="%s" alt="%s" loading="lazy"><b>%s</b></button>' % (k, ph(v[0], 700), k, k) for k, v in CIH.items())
    opt = ''.join('<option>%s</option>' % k for k in CIH)
    chips = ''.join('<a href="#cihaz">%s</a>' % k for k in ['Su almıyor', 'Soğutmuyor', 'Isıtmıyor', 'Ses yapıyor'])
    body = f'''<div id="pre" role="status"><div><b>BEYAZ SERVİS</b><i><span id="pn">0</span>%</i></div></div>
<nav class="top"><a class="lg" href="#">Beyaz<b>.</b>Servis</a><ul><li><a href="#cihaz">Cihazlar</a></li><li><a href="#surec">Süreç</a></li><li><a href="#servis">Servis çağır</a></li></ul><a class="btn" href="#servis">Servis çağır</a></nav>
<main><header class="hero" id="hero"><h1>Cihazın bozulduysa <em>biz buradayız.</em></h1><p>Çamaşır, bulaşık, buzdolabı, fırın. Aynı gün servis, yazılı fiyat, 6 ay parça garantisi.</p><form class="sr" id="sf"><input id="sq" placeholder="Hangi cihaz bozuldu?" aria-label="Cihaz"><button class="btn" type="submit">Sorunu bul</button></form><div class="ch">{chips}</div></header>
<div class="ph"><div class="im"><img src="{ph(0, 1600)}" alt="Teknisyen beyaz eşya onarıyor" fetchpriority="high"></div></div>
<section class="s" id="cihaz"><div class="hd"><h2>Hangi cihaz <em>bozuk?</em></h2><p>Cihazı seç, sık görülen sorunlara bak.</p></div><div class="cg">{cg}</div><div class="pb"><div><h3 id="t"></h3><p>Sorunun listede yoksa ara, ustamız telefonda yönlendirsin.</p><a class="btn" href="#servis">Servis çağır</a></div><div id="ls"></div></div></section>
<section class="s" id="surec"><div class="hd"><h2>Servis <em>nasıl işler?</em></h2></div><div class="sg"><div><b>1</b><h3>Ara</h3><p>Cihaz ve sorunu anlat.</p></div><div><b>2</b><h3>Randevu</h3><p>Aynı gün veya sana uygun saat.</p></div><div><b>3</b><h3>Tespit</h3><p>Fiyat yazılı söylenir.</p></div><div><b>4</b><h3>Onarım</h3><p>Onayınla yapılır, garanti verilir.</p></div></div></section>
<section class="cl" id="servis"><div><h2>Servis kaydı oluştur.</h2></div><form id="fm"><input id="fn" required placeholder="Adınız" aria-label="Adınız" autocomplete="name"><select id="fk" aria-label="Cihaz">{opt}</select><button class="btn" type="submit">Beni arayın</button><p class="ok" id="fo" aria-live="polite"></p></form></section></main>
<footer><div><b>Beyaz Servis</b><p>Beyaz eşya servisi · Ankara</p></div><div><p>Sayfalar</p><a href="#cihaz">Cihazlar</a><a href="#surec">Süreç</a><a href="#servis">Servis çağır</a></div><div><p>İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a></div></footer>'''
    c = json.dumps(dict(c={k: v[1] for k, v in CIH.items()}), ensure_ascii=False)
    return page('Beyaz Servis', 'Beyaz eşya servisi. Aynı gün, garantili.', ['Manrope:wght@500;600;700;800'], BASE_CSS + CSS, body, JS, c, dict(cta=['Servis çağır', '#servis'], addr='Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/beyaz', exist_ok=True); open(R + '/beyaz/index.html', 'w', encoding='utf-8').write(render()); print('beyaz ok')
