"""Bölüm kütüphanesi: hizmetler, süreç, yorumlar, markalar, form, önce/sonra, SSS, bölgeler, fiyat vb."""
from .base import ic
from .navs import TEL, TELRAW, ed
from .heroes import cta, trust

JS = {
 'QF': r"""document.addEventListener('DOMContentLoaded',function(){document.querySelectorAll('form.qf').forEach(function(f){
 f.querySelectorAll('[data-grp]').forEach(function(b){b.addEventListener('click',function(){var g=b.dataset.grp,multi=b.dataset.multi==='1';
  if(!multi){f.querySelectorAll('[data-grp="'+g+'"]').forEach(function(x){x.classList.remove('on')});b.classList.add('on')}else b.classList.toggle('on');
  var vals=[];f.querySelectorAll('[data-grp="'+g+'"].on').forEach(function(x){vals.push(x.textContent.trim())});if(f.elements[g])f.elements[g].value=vals.join(', ')})});
 var nx=f.querySelector('[data-next]');if(nx)nx.addEventListener('click',function(){var m=f.querySelector('.msg');if(!f.elements.sorun.value){m.className='msg er';m.textContent='Lütfen en az bir seçim yapın.';return}m.textContent='';f.classList.add('s2')});
 var bk=f.querySelector('[data-back]');if(bk)bk.addEventListener('click',function(){f.classList.remove('s2')});
 f.addEventListener('submit',function(ev){ev.preventDefault();var g=function(n){return f.elements[n]?f.elements[n].value:''};if(g('website'))return;
  var m=f.querySelector('.msg'),b=f.querySelector('button[type=submit]');m.className='msg';m.textContent='';b.disabled=true;var old=b.textContent;b.textContent='Gönderiliyor…';
  var p=[];[['cihaz','Cihaz'],['sorun','Sorun'],['zaman','Zaman'],['not','Not']].forEach(function(a){if(g(a[0]))p.push(a[1]+': '+g(a[0]))});
  OKT.post({name:g('name'),phone:g('phone'),district:g('ilce'),device_type:g('cihaz'),type:'servis_talebi',message:'Randevu talebi — '+p.join(' · '),page:location.pathname,website:''}).then(function(r){m.className='msg ok';m.textContent=r.preview?'✓ Önizleme: bu sitede form henüz firmanıza bağlı değil.':'✓ Talebiniz alındı. Sizi kısa süre içinde arayacağız.';b.textContent='Gönderildi'}).catch(function(x){m.className='msg er';m.textContent=x.message;b.disabled=false;b.textContent=old})})})});""",
 'SEARCH': r"""document.addEventListener('DOMContentLoaded',function(){var f=document.getElementById('hs');if(!f)return;var inp=f.querySelector('input'),sel=f.querySelector('select');
 document.querySelectorAll('#hsc button').forEach(function(b){b.addEventListener('click',function(){inp.value=b.textContent.trim();inp.focus()})});
 f.addEventListener('submit',function(e){e.preventDefault();var r=document.getElementById('randevu');if(r){var s=r.querySelector('[name=sorun]'),c=r.querySelector('[name=cihaz]');if(s&&inp.value){s.value=inp.value;if(s.dataset.grp===undefined&&r.querySelectorAll('[data-grp]').length)r.querySelectorAll('[data-grp="sorun"]').forEach(function(x){x.classList.toggle('on',x.textContent.trim()===inp.value)})}
  if(c){for(var i=0;i<c.options.length;i++){if(c.options[i].text===sel.value)c.selectedIndex=i}}r.scrollIntoView({behavior:'smooth'});var n=r.querySelector('[name=name]');if(n)setTimeout(function(){n.focus({preventScroll:true})},600)}})});""",
 'BA': r"""document.addEventListener('DOMContentLoaded',function(){document.querySelectorAll('.ba').forEach(function(b){var r=b.querySelector('input');var f=function(){b.style.setProperty('--x',r.value+'%')};r.addEventListener('input',f);f()})});""",
 'DRW': r"""document.addEventListener('DOMContentLoaded',function(){document.querySelectorAll('.drw a[href^="#"]').forEach(function(a){a.addEventListener('click',function(){var c=document.getElementById('mn');if(c)c.checked=false})});
 document.querySelectorAll('.mb7 .sh a').forEach(function(a){a.addEventListener('click',function(){var c=document.getElementById('msh');if(c)c.checked=false})})});""",
}


def sh(eb, title, sub='', c=False, cls=''):
    return f'<div class="sh{" c" if c else ""} {cls}"><span class="eyebrow">{eb}</span><h2>{title}</h2>' + (f'<p>{sub}</p>' if sub else '') + '</div>'


# ================================================================== HİZMETLER
def services(X, v):
    S = X.c['services']
    X.css('sv.base', ".cd{padding:clamp(22px,2.6vw,32px)}.sv-ic{width:50px;height:50px;border-radius:calc(var(--r)*.8);background:var(--ac);color:var(--on-ac);display:grid;place-items:center;flex:none}")
    head = sh('Hizmetlerimiz', X.r.get('svt', 'Neler yapıyoruz?'), 'Sorununuzu seçin; süre ve ücret aralığını önceden söyleriz.')
    if v == 'grid':
        X.css('sv.grid', ".sv1{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.sv1 .cd{display:grid;gap:14px;align-content:start;transition:.25s}.sv1 .cd:hover{transform:translateY(-4px)}.sv1 h3{font-size:1.18rem}.sv1 p{color:var(--mut);font-size:.93rem}.sv1 .ar{display:inline-flex;gap:6px;align-items:center;font:700 .84rem/1 var(--fb);color:var(--ac);margin-top:4px}@media(max-width:900px){.sv1{grid-template-columns:1fr 1fr}}@media(max-width:560px){.sv1{grid-template-columns:1fr}}")
        body = '<div class="sv1">' + ''.join(f'<article class="cd"><span class="sv-ic">{ic(i, 24)}</span><h3>{t}</h3><p>{d}</p><a class="ar" href="#randevu">Randevu al {ic("ar", 15)}</a></article>' for t, d, i in S) + '</div>'
    elif v == 'index':
        X.css('sv.index', ".sv2{border-top:1.5px solid var(--ink)}.sv2 a{display:grid;grid-template-columns:70px 1.1fr 1.4fr 40px;gap:20px;align-items:center;padding:clamp(20px,2.6vw,34px) 0;border-bottom:1px solid var(--ln);transition:.25s}.sv2 a:hover{padding-left:16px;background:var(--sf)}.sv2 .n{font:600 .85rem/1 var(--fm,var(--fb));color:var(--ac)}.sv2 h3{font-size:clamp(1.3rem,2.6vw,2rem);font-weight:var(--hw,700)}.sv2 p{color:var(--mut);font-size:.95rem}.sv2 svg{justify-self:end;color:var(--ac)}@media(max-width:800px){.sv2 a{grid-template-columns:44px 1fr 28px}.sv2 p{display:none}}")
        body = '<div class="sv2">' + ''.join(f'<a href="#randevu"><span class="n">0{i + 1}</span><h3>{t}</h3><p>{d}</p>{ic("ar", 22)}</a>' for i, (t, d, ico) in enumerate(S)) + '</div>'
    elif v == 'tiles':
        X.css('sv.tiles', ".sv3{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border:1px solid var(--ln);border-radius:var(--r);overflow:hidden}.sv3 article{padding:clamp(24px,3vw,40px);min-height:240px;display:flex;flex-direction:column;justify-content:space-between;gap:30px;transition:.3s;border-right:1px solid var(--ln);border-bottom:1px solid var(--ln)}.sv3 article:nth-child(3n){border-right:0}.sv3 article:nth-child(n+4){border-bottom:0}.sv3 article:hover{background:var(--ac);color:var(--on-ac)}.sv3 article:hover p{color:inherit;opacity:.85}.sv3 article:hover svg{color:inherit}.sv3 svg{color:var(--ac)}.sv3 h3{font-size:1.3rem;margin-bottom:8px}.sv3 p{color:var(--mut);font-size:.92rem}@media(max-width:900px){.sv3{grid-template-columns:1fr 1fr}.sv3 article:nth-child(3n){border-right:1px solid var(--ln)}.sv3 article:nth-child(2n){border-right:0}.sv3 article:nth-child(n+4){border-bottom:1px solid var(--ln)}.sv3 article:nth-child(n+5){border-bottom:0}}@media(max-width:560px){.sv3{grid-template-columns:1fr}.sv3 article{border-right:0!important;min-height:0}.sv3 article:last-child{border-bottom:0}}")
        body = '<div class="sv3">' + ''.join(f'<article>{ic(i, 38, 1.4)}<div><h3>{t}</h3><p>{d}</p></div></article>' for t, d, i in S) + '</div>'
    elif v == 'bento':
        X.css('sv.bento', ".sv4{display:grid;grid-template-columns:repeat(4,1fr);grid-auto-rows:minmax(190px,auto);gap:14px}.sv4 .big{grid-column:span 2;grid-row:span 2;position:relative;border-radius:calc(var(--r)*1.4);overflow:hidden;color:#fff;display:flex;align-items:flex-end}.sv4 .big .ph{position:absolute;inset:0}.sv4 .big:after{content:\"\";position:absolute;inset:0;background:linear-gradient(transparent 30%,color-mix(in srgb,var(--dk) 92%,transparent))}.sv4 .big div{position:relative;z-index:2;padding:clamp(22px,3vw,36px)}.sv4 .big h3{color:#fff;font-size:clamp(1.4rem,2.4vw,2rem);margin-bottom:8px}.sv4 .big p{color:#ffffffcc;font-size:.95rem}"
              ".sv4 article{border-radius:calc(var(--r)*1.4);padding:clamp(20px,2.4vw,30px);display:flex;flex-direction:column;justify-content:space-between;background:var(--sf);transition:.3s}.sv4 article:nth-of-type(2){background:var(--ac);color:var(--on-ac)}.sv4 article:nth-of-type(2) p{color:inherit;opacity:.85}.sv4 article:nth-of-type(4){background:var(--dk);color:#fff;--hc:#fff}.sv4 article:nth-of-type(4) p{color:#ffffffb0}.sv4 article:hover{transform:translateY(-4px)}.sv4 h3{font-size:1.12rem;margin:14px 0 6px}.sv4 p{color:var(--mut);font-size:.88rem}@media(max-width:900px){.sv4{grid-template-columns:1fr 1fr}.sv4 .big{grid-column:span 2;grid-row:span 1;min-height:280px}}@media(max-width:520px){.sv4{grid-template-columns:1fr}.sv4 .big{grid-column:auto}}")
        t0 = S[0]
        body = f'<div class="sv4"><div class="big">{X.ph("im2", "center")}<div><h3>{t0[0]}</h3><p>{t0[1]}</p><a class="btn" href="#randevu" style="margin-top:18px">Randevu al {ic("ar", 17)}</a></div></div>' + ''.join(f'<article>{ic(i, 28)}<div><h3>{t}</h3><p>{d}</p></div></article>' for t, d, i in S[1:5]) + '</div>'
    else:  # list2
        X.css('sv.list2', ".sv5{display:grid;grid-template-columns:.8fr 1.2fr;gap:clamp(30px,6vw,90px);align-items:start}.sv5 .l{position:sticky;top:110px}.sv5 .l .sh{margin-bottom:26px}.sv5 ul{list-style:none}.sv5 li{display:flex;gap:18px;padding:24px 0;border-bottom:1px solid var(--ln)}.sv5 li:first-child{padding-top:0}.sv5 li svg{color:var(--ac);flex:none;margin-top:3px}.sv5 h3{font-size:1.15rem;margin-bottom:5px}.sv5 p{color:var(--mut);font-size:.93rem}@media(max-width:900px){.sv5{grid-template-columns:1fr}.sv5 .l{position:static}}")
        return (f'<section class="sec" id="hizmet"><div class="w"><div class="sv5"><div class="l">{head}{cta(X, "tel")}</div><ul>' + ''.join(f'<li>{ic(i, 28, 1.5)}<div><h3>{t}</h3><p>{d}</p></div></li>' for t, d, i in S) + '</ul></div></div></section>')
    return f'<section class="sec" id="hizmet"><div class="w">{head}{body}</div></section>'


# ================================================================== SÜREÇ
def process(X, v):
    P = X.c['steps']
    head = sh('Nasıl çalışıyoruz', X.r.get('pt', 'Dört adımda, her adımda bilgi'), 'Her aşamada size SMS ile haber verilir; kayıtlarınız servis fişinde toplanır.')
    if v == 'line':
        X.css('pr.line', ".pr1{display:grid;grid-template-columns:repeat(4,1fr);gap:30px;position:relative}.pr1:before{content:\"\";position:absolute;left:5%;right:5%;top:27px;height:1.5px;background:var(--ln)}.pr1 div{position:relative}.pr1 .n{width:56px;height:56px;border-radius:50%;background:var(--bg);border:1.5px solid var(--ac);color:var(--ac);display:grid;place-items:center;font:700 1.15rem/1 var(--fd);margin-bottom:20px;position:relative}.pr1 div:first-child .n{background:var(--ac);color:var(--on-ac)}.pr1 h3{margin-bottom:8px}.pr1 p{color:var(--mut);font-size:.93rem}@media(max-width:800px){.pr1{grid-template-columns:1fr 1fr}.pr1:before{display:none}}@media(max-width:480px){.pr1{grid-template-columns:1fr}}")
        body = '<div class="pr1">' + ''.join(f'<div><span class="n">{i + 1}</span><h3>{t}</h3><p>{d}</p></div>' for i, (t, d) in enumerate(P)) + '</div>'
    elif v == 'vert':
        X.css('pr.vert', ".pr2{display:grid;grid-template-columns:.8fr 1.2fr;gap:clamp(30px,6vw,90px)}.pr2 .l{position:sticky;top:110px;align-self:start}.pr2 ol{list-style:none;border-left:1.5px solid var(--ln);margin-left:6px}.pr2 li{position:relative;padding:0 0 clamp(30px,4vw,56px) clamp(28px,4vw,56px)}.pr2 li:last-child{padding-bottom:0}.pr2 li:before{content:\"\";position:absolute;left:-7px;top:10px;width:13px;height:13px;border-radius:50%;background:var(--ac);box-shadow:0 0 0 5px var(--bg)}.pr2 .n{font:700 clamp(2.4rem,5vw,4rem)/1 var(--fd);letter-spacing:-.04em;color:transparent;-webkit-text-stroke:1.5px var(--ac);display:block;margin-bottom:6px}.pr2 h3{font-size:1.35rem;margin-bottom:6px}.pr2 p{color:var(--mut)}@media(max-width:900px){.pr2{grid-template-columns:1fr}.pr2 .l{position:static}}")
        return f'<section class="sec alt" id="surec"><div class="w"><div class="pr2"><div class="l">{head}</div><ol>' + ''.join(f'<li><span class="n">0{i + 1}</span><h3>{t}</h3><p>{d}</p></li>' for i, (t, d) in enumerate(P)) + '</ol></div></div></section>'
    elif v == 'big':
        X.css('pr.big', ".pr3{display:grid;grid-template-columns:repeat(4,1fr);border-top:1.5px solid var(--ink)}.pr3 div{padding:28px 24px 8px 0;border-right:1px solid var(--ln);margin-right:24px}.pr3 div:last-child{border:0;margin:0}.pr3 .n{font:800 clamp(4rem,8vw,7rem)/.9 var(--fd);letter-spacing:-.06em;color:var(--ac);display:block;margin-bottom:14px}.pr3 h3{margin-bottom:8px}.pr3 p{color:var(--mut);font-size:.93rem}@media(max-width:800px){.pr3{grid-template-columns:1fr 1fr;gap:10px}.pr3 div{border:0;margin:0;border-bottom:1px solid var(--ln);padding-bottom:22px}}@media(max-width:480px){.pr3{grid-template-columns:1fr}}")
        body = '<div class="pr3">' + ''.join(f'<div><span class="n">{i + 1}</span><h3>{t}</h3><p>{d}</p></div>' for i, (t, d) in enumerate(P)) + '</div>'
    else:
        X.css('pr.cards', ".pr4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.pr4 .cd{display:grid;gap:12px;align-content:start}.pr4 .n{width:42px;height:42px;border-radius:calc(var(--r)*.7);background:var(--dk);color:#fff;display:grid;place-items:center;font:700 1rem/1 var(--fd)}.pr4 p{color:var(--mut);font-size:.92rem}@media(max-width:900px){.pr4{grid-template-columns:1fr 1fr}}@media(max-width:480px){.pr4{grid-template-columns:1fr}}")
        body = '<div class="pr4">' + ''.join(f'<div class="cd"><span class="n">{i + 1}</span><h3>{t}</h3><p>{d}</p></div>' for i, (t, d) in enumerate(P)) + '</div>'
    return f'<section class="sec" id="surec"><div class="w">{head}{body}</div></section>'


# ================================================================== YORUMLAR
def proof(X, v):
    R = X.c['rev']
    note = '<p class="note">Örnek yorumlar — kendi müşterilerinizin yorumlarıyla değiştirin.</p>'
    X.css('pf.base', ".stars{display:flex;gap:2px;color:var(--ac)}.note{font-size:.8rem;color:var(--mut);margin-top:22px}")
    stars = f'<div class="stars">{ic("st", 17, 1.4) * 5}</div>'
    head = sh('Müşteri yorumları', X.r.get('rt', 'Müşterilerimiz ne diyor?'), '')
    if v == 'cards':
        X.css('pf.cards', ".pf1{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.pf1 .cd{display:grid;gap:16px;align-content:space-between}.pf1 p{font-size:1rem}.pf1 b{display:block;font:700 .92rem/1 var(--fd)}.pf1 small{color:var(--mut)}@media(max-width:800px){.pf1{grid-template-columns:1fr}}")
        body = '<div class="pf1">' + ''.join(f'<figure class="cd">{stars}<p>“{t}”</p><figcaption><b>{n}</b><small>Örnek yorum</small></figcaption></figure>' for n, t in R) + '</div>'
    elif v == 'quote':
        X.css('pf.quote', ".pf2{display:grid;grid-template-columns:1.5fr 1fr;gap:clamp(24px,5vw,70px);align-items:center}.pf2 .q{font:var(--qw,400) clamp(1.5rem,3.2vw,2.5rem)/1.2 var(--fd);letter-spacing:-.02em}.pf2 .q:before{content:\"“\";display:block;font-size:6rem;line-height:.6;color:var(--ac);margin-bottom:10px}.pf2 .who{margin-top:24px;display:flex;align-items:center;gap:14px}.pf2 .av{width:48px;height:48px;border-radius:50%;background:var(--ac);color:var(--on-ac);display:grid;place-items:center;font:700 1.1rem/1 var(--fd)}.pf2 .sd{display:grid;gap:16px}.pf2 .sd figure{padding:22px;border:1px solid var(--ln);border-radius:var(--r);background:var(--bg)}.pf2 .sd p{font-size:.95rem;margin:10px 0}.pf2 .sd b{font-size:.85rem}@media(max-width:900px){.pf2{grid-template-columns:1fr}}")
        body = (f'<div class="pf2"><figure><blockquote class="q">{R[0][1]}</blockquote><div class="who"><span class="av">{R[0][0][0]}</span><div><b>{R[0][0]}</b><br><small class="mut">Örnek yorum</small></div></div></figure><div class="sd">'
                + ''.join(f'<figure>{stars}<p>“{t}”</p><b>{n}</b></figure>' for n, t in R[1:]) + '</div></div>')
    else:
        X.css('pf.wall', ".pf3{columns:3;column-gap:18px}.pf3 figure{break-inside:avoid;margin-bottom:18px;padding:26px;border-radius:var(--r);background:var(--sf);display:grid;gap:14px}.pf3 figure:nth-child(2){background:var(--ac);color:var(--on-ac)}.pf3 figure:nth-child(2) .stars{color:inherit}.pf3 figure:nth-child(2) small{color:inherit;opacity:.8}.pf3 p{font-size:1.02rem}.pf3 small{color:var(--mut)}.pf3 .big{font:700 clamp(2.4rem,5vw,3.6rem)/1 var(--fd);letter-spacing:-.04em}@media(max-width:800px){.pf3{columns:1}}")
        body = ('<div class="pf3">' + ''.join(f'<figure>{stars}<p>“{t}”</p><div><b>{n}</b><br><small>Örnek yorum</small></div></figure>' for n, t in R)
                + f'<figure style="background:var(--dk);color:#fff;--hc:#fff"><span class="big">★ 5,0</span><p style="opacity:.8">Örnek puan alanı — gerçek yorum sayfanızdan doldurun.</p></figure></div>')
    return f'<section class="sec alt" id="yorum"><div class="w">{head}{body}{note}</div></section>'


# ================================================================== MARKALAR
def brands(X, v):
    B = X.c['brands']
    if v == 'wall':
        X.css('br.wall', ".br1 .g{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--ln);border-left:1px solid var(--ln)}.br1 .g span{display:grid;place-items:center;padding:30px 12px;border-right:1px solid var(--ln);border-bottom:1px solid var(--ln);font:700 clamp(1rem,1.8vw,1.4rem)/1 var(--fd);letter-spacing:.04em;text-transform:uppercase;color:var(--mut);transition:.2s}.br1 .g span:hover{color:var(--ink);background:var(--sf)}@media(max-width:700px){.br1 .g{grid-template-columns:1fr 1fr}}")
        return f'<section class="sec br1"><div class="w">{sh("Markalar", "Çalıştığımız markalar", "Aşağıdaki ve benzeri markaların servisini yapıyoruz. Marka adları ilgili firmalara aittir; Biz bağımsız bir servisiz.")}<div class="g">' + ''.join(f'<span>{b}</span>' for b in B) + '</div></div></section>'
    if v == 'pills':
        X.css('br.pills', ".br2{padding:clamp(34px,5vw,64px) 0;border-block:1px solid var(--ln)}.br2 .in{display:flex;align-items:center;gap:30px;flex-wrap:wrap}.br2 b{font:700 .8rem/1 var(--fb);letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}.br2 .chips span{padding:11px 18px;border:1px solid var(--ln);border-radius:99px;font:600 .9rem/1 var(--fb)}")
        return f'<section class="br2"><div class="w in"><b>Servis verdiğimiz markalar</b><div class="chips">' + ''.join(f'<span>{b}</span>' for b in B) + '</div></div></section>'
    X.css('br.tick', ".br3{border-block:1px solid var(--ln);overflow:hidden;padding:20px 0}.br3 div{display:flex;gap:52px;width:max-content;animation:mq 38s linear infinite;font:700 1.15rem/1 var(--fd);letter-spacing:.1em;text-transform:uppercase;color:var(--mut)}.br3 span:after{content:\"/\";margin-left:52px;color:var(--ac)}@keyframes mq{to{transform:translateX(-50%)}}")
    return '<section class="br3"><div>' + ''.join(f'<span>{b}</span>' for b in B * 2) + '</div></section>'


# ================================================================== FORM / RANDEVU
def _ilce_opts(X):
    return '<option value="">İlçe seçin</option>' + ''.join(f'<option>{i}</option>' for i in X.ilce)


def quickform(X, uid, title, sub, dark=False):
    X.js('QF')
    cih = ''.join(f'<option>{c}</option>' for c in X.c['cihaz'])
    return (f'<form class="qf fm" id="{uid}" novalidate><h3>{title}</h3><p>{sub}</p><label>Adınız soyadınız<input name="name" autocomplete="name" required></label>'
            f'<div class="g2"><label>Telefon<input name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="05xx xxx xx xx" required></label><label>İlçe<select name="ilce">{_ilce_opts(X)}</select></label></div>'
            f'<label>Cihaz<select name="cihaz">{cih}</select></label><label>Sorun (isteğe bağlı)<input name="sorun" placeholder="{X.c["prob"][0]}…"></label>'
            f'<input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true"><button class="btn" type="submit">{X.r.get("cta", "Randevu al")}</button><div class="msg" role="status"></div></form>')


def wizard(X, uid):
    X.js('QF')
    cih = ''.join(f'<option>{c}</option>' for c in X.c['cihaz'])
    chips = ''.join(f'<button type="button" data-grp="sorun" data-multi="1">{p}</button>' for p in X.c['prob'])
    zam = ''.join(f'<button type="button" data-grp="zaman">{z}</button>' for z in ['Bugün', 'Yarın', 'Bu hafta', 'Fark etmez'])
    X.css('form.wiz', ".wz .s1,.wz .s2c{display:grid;gap:16px}.wz .s2c{display:none}.wz.s2 .s1{display:none}.wz.s2 .s2c{display:grid}.wz .stp{display:flex;gap:8px;margin-bottom:6px}.wz .stp i{height:4px;flex:1;border-radius:4px;background:var(--ln)}.wz .stp i:first-child,.wz.s2 .stp i{background:var(--ac)}.wz .btns{display:flex;gap:10px}.wz .btns .btn{flex:1}")
    return (f'<form class="qf wz fm" id="{uid}" novalidate><div class="stp"><i></i><i></i></div><input type="hidden" name="sorun"><input type="hidden" name="zaman">'
            f'<div class="s1"><h3>Sorun nedir?</h3><p class="mut" style="font-size:.9rem">Birden fazla seçebilirsiniz.</p><div class="chips">{chips}</div><label>Cihaz<select name="cihaz">{cih}</select></label><label>Ek not (isteğe bağlı)<input name="not"></label><button type="button" class="btn" data-next>Devam {ic("ar", 17)}</button></div>'
            f'<div class="s2c"><h3>Size nasıl ulaşalım?</h3><label>Adınız soyadınız<input name="name" autocomplete="name" required></label><div class="g2"><label>Telefon<input name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="05xx xxx xx xx" required></label><label>İlçe<select name="ilce">{_ilce_opts(X)}</select></label></div>'
            f'<span class="sgl" style="font:600 .78rem/1 var(--fb);color:var(--mut)">Ne zaman uygun?</span><div class="chips">{zam}</div><input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true"><div class="btns"><button type="button" class="btn o" data-back>{ic("al", 17)} Geri</button><button class="btn" type="submit">Gönder</button></div></div><div class="msg" role="status"></div></form>')


def booking(X, v):
    head_title = X.r.get('bt', 'Randevunuzu şimdi alın')
    sub = 'Formu doldurun; ustamız aynı gün ya da ertesi gün sizi arasın.'
    if v == 'card':
        X.css('bk.card', ".bk1{display:grid;grid-template-columns:1fr 1fr;gap:clamp(28px,6vw,90px);align-items:center}.bk1 .f{padding:clamp(24px,3.4vw,40px);background:var(--bg);border-radius:calc(var(--r)*1.4);border:1px solid var(--ln);box-shadow:0 40px 80px -44px #0006}.bk1 .ls{display:grid;gap:18px;margin:28px 0}.bk1 .ls div{display:flex;gap:14px;align-items:flex-start}.bk1 .ls svg{color:var(--ac);flex:none;margin-top:3px}@media(max-width:900px){.bk1{grid-template-columns:1fr}}")
        return (f'<section class="sec alt" id="randevu"><div class="w bk1"><div>{sh("Randevu", head_title, sub)}<div class="ls"><div>{ic("cl", 22)}<span>Hafta içi 08:30–19:00, cumartesi 09:00–17:00. Acil çağrılar için 7/24 arayın.</span></div>'
                f'<div>{ic("dc", 22)}<span>İşlem sonunda imzalı servis fişi ve garanti belgesi verilir.</span></div><div>{ic("tel", 22)}<span>Dilerseniz doğrudan arayın: <a href="tel:+{TELRAW}"><b>{TEL}</b></a></span></div></div></div><div class="f">{quickform(X, "bkf", "Hızlı randevu", "2 dakikada doldurun, sizi arayalım.")}</div></div></section>')
    if v == 'split':
        X.css('bk.split', ".bk2{display:grid;grid-template-columns:.9fr 1.1fr;border-radius:calc(var(--r)*1.6);overflow:hidden;box-shadow:0 40px 90px -50px #0008}.bk2 .l{background:var(--dk);color:#fff;padding:clamp(28px,4vw,56px);display:flex;flex-direction:column;justify-content:space-between;gap:30px;--hc:#fff;--mut:#ffffffb0}.bk2 .l .num{font:700 clamp(1.6rem,3.4vw,2.6rem)/1 var(--fd);letter-spacing:-.03em;display:block;margin:8px 0}.bk2 .l ul{list-style:none;display:grid;gap:14px;font-size:.95rem;color:#ffffffc8}.bk2 .l li{display:flex;gap:12px}.bk2 .l li svg{color:var(--ac);flex:none}.bk2 .r{background:var(--bg);padding:clamp(28px,4vw,56px)}@media(max-width:900px){.bk2{grid-template-columns:1fr}}")
        return (f'<section class="sec" id="randevu"><div class="w"><div class="bk2"><div class="l"><div><span class="eyebrow" style="color:var(--ac)">Randevu</span><h2 style="margin-top:14px">{head_title}</h2><a class="num" href="tel:+{TELRAW}">{TEL}</a><p style="opacity:.8">{sub}</p></div>'
                f'<ul><li>{ic("cl", 20)}Hafta içi 08:30–19:00 · Cumartesi 09:00–17:00</li><li>{ic("pin", 20)}Atatürk Cad. No:12 / {X.city}</li><li>{ic("wa", 20)}WhatsApp: fotoğraf ve model bilgisi gönderin</li></ul></div><div class="r">{quickform(X, "bkf", "Hızlı randevu", "Adınızı ve telefonunuzu bırakın.")}</div></div></div></section>')
    if v == 'strip':
        X.css('bk.strip', ".bk3{background:var(--ac);color:var(--on-ac);--hc:var(--on-ac)}.bk3 h2{color:var(--on-ac);margin-bottom:26px;max-width:18em}.bk3 .qf{display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr auto;gap:12px;align-items:end;background:transparent}.bk3 .qf h3,.bk3 .qf>p{display:none}.bk3 .qf label{color:color-mix(in srgb,var(--on-ac) 82%,transparent)}.bk3 .qf .g2{display:contents}.bk3 .qf label{min-width:0}.bk3 .qf .hp{display:none}.bk3 .qf .btn{background:var(--dk);border-color:var(--dk);color:#fff}.bk3 .qf .msg{grid-column:1/-1;color:var(--on-ac)}.bk3 .qf .msg.ok{color:var(--on-ac)}.bk3 .qf>label:nth-of-type(3),.bk3 .qf>label:nth-of-type(4){display:grid}@media(max-width:1000px){.bk3 .qf{grid-template-columns:1fr 1fr}.bk3 .qf .btn{grid-column:1/-1}}@media(max-width:560px){.bk3 .qf{grid-template-columns:1fr}}")
        return f'<section class="sec bk3" id="randevu"><div class="w"><span class="eyebrow" style="color:var(--on-ac)">Randevu</span><h2 style="margin-top:14px">{head_title}</h2>{quickform(X, "bkf", "", "")}</div></section>'
    X.css('bk.wiz', ".bk4{max-width:720px;margin-inline:auto;background:var(--bg);border:1px solid var(--ln);border-radius:calc(var(--r)*1.6);padding:clamp(24px,4vw,48px);box-shadow:0 40px 80px -44px #0006}")
    return f'<section class="sec alt" id="randevu"><div class="w">{sh("Randevu", head_title, "Sorunu seçin, iletişim bilgilerinizi bırakın; biz sizi arayalım.", True)}<div class="bk4">{wizard(X, "bkf")}</div></div></section>'


# ================================================================== ÖNCE / SONRA
def before_after(X):
    X.js('BA')
    X.css('ba', ".ba-w{display:grid;grid-template-columns:.8fr 1.2fr;gap:clamp(28px,6vw,90px);align-items:center}.ba{position:relative;--x:50%;aspect-ratio:16/10;border-radius:calc(var(--r)*1.4);overflow:hidden;user-select:none}.ba .ph{position:absolute;inset:0}.ba .b{filter:grayscale(1) contrast(.9) brightness(.82) sepia(.35)}.ba .a{clip-path:inset(0 0 0 var(--x))}"
          ".ba .lb{position:absolute;top:16px;padding:7px 12px;border-radius:99px;background:#000a;color:#fff;font:700 .7rem/1 var(--fb);letter-spacing:.12em;z-index:3}.ba .lb.l{left:16px}.ba .lb.r{right:16px}.ba .ln{position:absolute;top:0;bottom:0;left:var(--x);width:3px;background:#fff;transform:translateX(-1.5px);z-index:2;pointer-events:none}.ba .ln:after{content:\"\";position:absolute;top:50%;left:50%;width:46px;height:46px;border-radius:50%;background:#fff;transform:translate(-50%,-50%);box-shadow:0 8px 24px #0006}"
          ".ba input{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:ew-resize;z-index:4;margin:0}@media(max-width:900px){.ba-w{grid-template-columns:1fr}}")
    return (f'<section class="sec" id="once-sonra"><div class="w ba-w"><div>{sh("Çalışmalarımız", "Yaptığımız işi gösteririz", "Servis kaydına eklenen önce / sonra fotoğraflarınızı burada gösterebilirsiniz. Çubuğu sürükleyin.")}<p class="note">Örnek görsel — kendi çalışma fotoğraflarınızı panelden yükleyin.</p></div>'
            f'<div class="ba">{X.ph("im3", "center", "b")}{X.ph("im3", "center", "a")}<span class="lb l">ÖNCE</span><span class="lb r">SONRA</span><div class="ln"></div><input type="range" min="2" max="98" value="50" aria-label="Önce sonra karşılaştırma"></div></div></section>')


# ================================================================== BÖLGELER
def areas(X):
    X.css('areas', ".ar-w{display:grid;grid-template-columns:.9fr 1.1fr;gap:clamp(28px,6vw,90px);align-items:center}.ar-g{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.ar-g a{display:flex;align-items:center;gap:12px;padding:16px 18px;border:1px solid var(--ln);border-radius:var(--r);background:var(--bg);font:600 .98rem/1 var(--fd);transition:.2s}.ar-g a:hover{border-color:var(--ac);transform:translateX(4px)}.ar-g svg{color:var(--ac)}@media(max-width:900px){.ar-w{grid-template-columns:1fr}}")
    return (f'<section class="sec alt" id="bolge"><div class="w ar-w"><div>{sh("Hizmet bölgeleri", f"{X.city} ve çevresinde yanınızdayız", "Listede ilçeniz yoksa arayın; çoğu zaman yakın bir ekibimiz vardır.")}{cta(X, "tel")}</div>'
            f'<div class="ar-g">' + ''.join(f'<a href="#randevu">{ic("pin", 18)}{i}</a>' for i in X.ilce) + '</div></div></section>')


# ================================================================== NEDEN BİZ
def why(X):
    X.css('why', ".wy{display:grid;grid-template-columns:1fr 1fr;gap:clamp(28px,6vw,90px);align-items:center}.wy .ph{aspect-ratio:4/5;border-radius:calc(var(--r)*1.6);max-height:560px;width:100%}.wy ul{list-style:none;display:grid;gap:26px;margin-top:30px}.wy li{display:flex;gap:18px}.wy li i{flex:none;width:48px;height:48px;border-radius:50%;border:1.5px solid var(--ac);color:var(--ac);display:grid;place-items:center}.wy h3{font-size:1.1rem;margin-bottom:4px}.wy p{color:var(--mut);font-size:.93rem}@media(max-width:900px){.wy{grid-template-columns:1fr}.wy .ph{aspect-ratio:16/10}}")
    R = [('sh', 'Yazılı fiyat', 'Teşhisten sonra, işe başlamadan fiyat yazılı iletilir.'), ('dc', 'Kayıtlı servis', 'Her işin numarası, servis fişi ve fotoğrafları kayıtlıdır.'), ('cl', 'Randevuya bağlı', 'Gün ve saat birlikte netleşir; SMS ile hatırlatma gelir.'), ('st', 'Garantili işçilik', 'Takılan parça ve işçilik için yazılı garanti.')]
    return (f'<section class="sec" id="neden"><div class="w wy">{X.ph("im3", "center", "rv")}<div>{sh("Neden biz", X.r.get("wt", "Farkımız düzen ve şeffaflık"), "")}<ul>' + ''.join(f'<li><i>{ic(a, 22)}</i><div><h3>{b}</h3><p>{c}</p></div></li>' for a, b, c in R) + '</ul></div></div></section>')


# ================================================================== FİYAT
def price(X, v):
    S = X.c['services']
    if v == 'table':
        X.css('pc.table', ".pc1 table{width:100%;border-collapse:collapse}.pc1 th{text-align:left;font:700 .74rem/1 var(--fb);letter-spacing:.14em;text-transform:uppercase;color:var(--mut);padding:14px 16px;border-bottom:1.5px solid var(--ink)}.pc1 td{padding:20px 16px;border-bottom:1px solid var(--ln);font-size:1rem}.pc1 td:first-child{font:700 1.1rem/1.2 var(--fd)}.pc1 td:last-child{text-align:right;font-weight:700;color:var(--ac)}.pc1 tr:hover td{background:var(--sf)}@media(max-width:600px){.pc1 td,.pc1 th{padding:14px 8px}.pc1 th:nth-child(2),.pc1 td:nth-child(2){display:none}}")
        rows = ''.join(f'<tr><td>{t}</td><td>{i + 1}–{i + 2} saat</td><td>₺ … – ₺ …</td></tr>' for i, (t, d, ic_) in enumerate(S[:5]))
        return f'<section class="sec pc1" id="fiyat"><div class="w">{sh("Fiyat listesi", "Şeffaf fiyat", "Örnek aralıklar; panelden kendi fiyatlarınızla değiştirin. Kesin fiyat teşhis sonrası yazılı bildirilir.")}<table><tr><th>İşlem</th><th>Süre</th><th>Ücret aralığı</th></tr>{rows}</table></div></section>'
    X.css('pc.paket', ".pc2{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;align-items:stretch}.pc2 .cd{display:grid;gap:18px;align-content:start}.pc2 .cd.hl{background:var(--dk);color:#fff;--hc:#fff;--mut:#ffffffb0;transform:translateY(-10px)}.pc2 .pr{font:800 2rem/1 var(--fd);letter-spacing:-.03em}.pc2 ul{list-style:none;display:grid;gap:11px;font-size:.93rem}.pc2 li{display:flex;gap:10px}.pc2 li svg{color:var(--ac);flex:none;margin-top:3px}.pc2 .tg2{font:700 .7rem/1 var(--fb);letter-spacing:.14em;text-transform:uppercase;color:var(--ac)}@media(max-width:900px){.pc2{grid-template-columns:1fr}.pc2 .cd.hl{transform:none}}")
    P = [('Temel', ['Teşhis ve yazılı rapor', 'Basit onarım ya da bakım', 'Servis fişi']), ('Standart', ['Temel pakettekilerin tümü', 'Parça değişimi (parça ayrı)', 'Yazılı garanti belgesi', 'SMS ile durum takibi']), ('Kapsamlı', ['Standart pakettekilerin tümü', 'Öncelikli randevu', 'Yıllık hatırlatma', 'Telefon desteği'])]
    return (f'<section class="sec alt" id="fiyat"><div class="w">{sh("Paketler", "Size uygun planı seçin", "Örnek paketler; kapsamı ve fiyatı panelden kendinize göre düzenleyin.", True)}<div class="pc2">'
            + ''.join(f'<div class="cd{" hl" if i == 1 else ""}"><span class="tg2">{n}</span><div class="pr">₺ …</div><ul>' + ''.join(f'<li>{ic("ok", 17)}{x}</li>' for x in l) + f'</ul><a class="btn{" " if i == 1 else " o"}" href="#randevu">Randevu al</a></div>' for i, (n, l) in enumerate(P)) + '</div></div></section>')


# ================================================================== SSS
def faq(X, v):
    F = X.c['faq']
    items = ''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in F)
    if v == 'side':
        X.css('faq.side', ".fq1{display:grid;grid-template-columns:.8fr 1.2fr;gap:clamp(28px,6vw,90px)}.fq1 .l{position:sticky;top:110px;align-self:start}@media(max-width:900px){.fq1{grid-template-columns:1fr}.fq1 .l{position:static}}")
        return f'<section class="sec" id="sss"><div class="w"><div class="fq1"><div class="l">{sh("Sık sorulanlar", "Aklınıza takılanlar", "Burada olmayan bir soru için bizi arayın.")}{cta(X, "wa")}</div><div class="faq">{items}</div></div></div></section>'
    return f'<section class="sec" id="sss"><div class="w n">{sh("Sık sorulanlar", "Aklınıza takılanlar", "", True)}<div class="faq">{items}</div></div></section>'


# ================================================================== CTA BANDI
def ctaband(X, v):
    if v == 'photo':
        X.css('cta.photo', ".cb1{position:relative;color:#fff;overflow:hidden;--hc:#fff;--mut:#ffffffbb;text-align:center;padding:clamp(70px,10vw,140px) 0}.cb1 .ph{position:absolute;inset:0}.cb1:before{content:\"\";position:absolute;inset:0;background:color-mix(in srgb,var(--dk) 82%,transparent);z-index:1}.cb1 .w{position:relative;z-index:2}.cb1 h2{max-width:16em;margin:0 auto 14px;color:#fff;font-size:clamp(2rem,5vw,3.8rem)}.cb1 .cta{justify-content:center;margin-top:26px}.cb1 .btn.o{color:#fff}")
        return f'<section class="cb1">{X.ph("im2", "center")}<div class="w"><span class="eyebrow" style="color:#fff">Bugün arayın</span><h2 style="margin-top:14px">{X.r.get("ct", "Sorununuzu birlikte çözelim")}</h2><p class="lead" style="margin-inline:auto">Telefonda anlatın ya da WhatsApp’tan fotoğraf gönderin.</p>{cta(X, "wa")}</div></section>'
    X.css('cta.big', ".cb2{background:var(--ac);color:var(--on-ac);padding:clamp(56px,8vw,110px) 0;--hc:var(--on-ac)}.cb2 .in{display:flex;justify-content:space-between;align-items:center;gap:30px;flex-wrap:wrap}.cb2 h2{font-size:clamp(2rem,5.4vw,4.4rem);max-width:12em;color:var(--on-ac)}.cb2 .num{font:800 clamp(1.8rem,4vw,3rem)/1 var(--fd);letter-spacing:-.03em;display:block;margin-bottom:16px;color:var(--on-ac)}.cb2 .btn{background:var(--on-ac);color:var(--ac);border-color:var(--on-ac)}.cb2 .btn.o{background:transparent;color:var(--on-ac)}")
    return f'<section class="cb2"><div class="w in"><h2>{X.r.get("ct", "Sorununuzu birlikte çözelim")}</h2><div><a class="num" href="tel:+{TELRAW}">{TEL}</a>{cta(X, "wa")}</div></div></section>'


# ================================================================== BİLGİ / HARİTA
def info(X):
    X.css('info', ".if{display:grid;grid-template-columns:1fr 1fr;gap:0;border:1px solid var(--ln);border-radius:calc(var(--r)*1.4);overflow:hidden}.if .l{padding:clamp(28px,4vw,52px);display:grid;gap:22px;align-content:center}.if .l div{display:flex;gap:16px}.if .l svg{color:var(--ac);flex:none;margin-top:2px}.if .l b{display:block;font:700 1rem/1.2 var(--fd);margin-bottom:3px}.if .l span{color:var(--mut);font-size:.93rem}"
          ".if .mp{position:relative;min-height:340px;background:linear-gradient(var(--ln) 1px,transparent 1px) 0 0/44px 44px,linear-gradient(90deg,var(--ln) 1px,transparent 1px) 0 0/44px 44px,var(--sf)}.if .mp:before{content:\"\";position:absolute;left:-10%;right:-10%;top:48%;height:22px;background:var(--bg);transform:rotate(-14deg);border-block:1px solid var(--ln)}.if .mp i{position:absolute;left:50%;top:44%;transform:translate(-50%,-100%);width:48px;height:48px;border-radius:50% 50% 50% 0;rotate:-45deg;background:var(--ac);display:grid;place-items:center;box-shadow:0 14px 30px -8px #0006}.if .mp i:after{content:\"\";width:16px;height:16px;border-radius:50%;background:var(--on-ac)}.if .mp small{position:absolute;left:14px;bottom:12px;font-size:.72rem;color:var(--mut)}@media(max-width:800px){.if{grid-template-columns:1fr}}")
    return (f'<section class="sec" id="adres"><div class="w">{sh("İletişim", "Bize ulaşın", "")}<div class="if"><div class="l"><div>{ic("pin", 22)}<p><b>Adres</b><span>Atatürk Cad. No:12, {X.city}</span></p></div><div>{ic("cl", 22)}<p><b>Çalışma saatleri</b><span>Hafta içi 08:30–19:00 · Cumartesi 09:00–17:00 · Acil 7/24</span></p></div>'
            f'<div>{ic("tel", 22)}<p><b>Telefon</b><span><a href="tel:+{TELRAW}">{TEL}</a></span></p></div><div>{ic("wa", 22)}<p><b>WhatsApp</b><span><a href="https://wa.me/{TELRAW}">Mesaj gönderin</a></span></p></div></div><div class="mp" role="img" aria-label="Harita alanı"><i></i><small>Harita alanı — panelden Google Haritalar bağlantısı ekleyin</small></div></div></div></section>')


# ================================================================== ARAÇ BÖLÜMÜ
def toolsec(X, idx, variant, alt=False):
    th, tj, t = X.tool(idx, variant)
    return (f'<section class="sec{" alt" if alt else ""}" id="arac{"" if idx == 0 else idx}"><div class="w">{sh("Ücretsiz araç", t["title"], "")}{th}</div></section>')
