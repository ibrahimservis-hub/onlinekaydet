# -*- coding: utf-8 -*-
"""Motor Atölye: oto servis. Endüstriyel, plaka odaklı; yatay kaydırmalı paketler, araç durumu çizelgesi, imleçle açılan usta listesi."""
import html as H, json
from common import *
IDX = 3
f = foto.F[IDX]
ph = lambda k, w=900: foto.url(f[k % len(f)], w)
VURL, POSTER = foto.video(IDX)
PK = [
 ('TEMEL BAKIM', 1800, ['Motor yağı değişimi', 'Yağ filtresi', 'Hava filtresi kontrolü', 'Sıvı seviyeleri', '20 noktalı kontrol']),
 ('FREN PAKETİ', 2400, ['Ön balata değişimi', 'Disk ölçümü', 'Fren hidroliği kontrolü', 'Yol denemesi']),
 ('KIŞ HAZIRLIĞI', 1500, ['Akü testi', 'Antifriz ölçümü', 'Silecek ve cam suyu', 'Lastik basıncı ve diş derinliği']),
 ('KAPSAMLI KONTROL', 1200, ['Bilgisayarlı arıza taraması', 'Süspansiyon ve alt takım', 'Egzoz ve sızıntı kontrolü', 'Yazılı rapor']),
]
STAGES = ['Kabul', 'Teşhis', 'Onay', 'İşlem', 'Teslim']
TEAM = [('SERKAN', 'Motor ustası', 0), ('VOLKAN', 'Elektrik ve elektronik', 1), ('EMRE', 'Fren ve süspansiyon', 2), ('BURAK', 'Lastik ve rot balans', 3)]
CSS = '''
:root{--bg:#101215;--ink:#eceff2;--mut:#98a1ab;--ac:#e4262f;--ln:rgba(255,255,255,.14);--hf:'Oswald',Impact,sans-serif;--mono:'IBM Plex Mono',monospace;--bf:'Inter',system-ui,sans-serif}
body{background:var(--bg);color:var(--ink);font:400 17px/1.55 var(--bf)}
h1,h2,h3{font-family:var(--hf);font-weight:700;text-transform:uppercase;line-height:.95;overflow-wrap:break-word;min-width:0}
.lb{font:600 12px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--mut)}
nav.top{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;justify-content:space-between;align-items:center;padding:18px clamp(18px,4vw,48px);transition:background .3s,backdrop-filter .3s}
nav.top.solid{background:rgba(16,18,21,.88);backdrop-filter:blur(10px);padding-block:12px}
.lg{font:700 24px/1 var(--hf);text-transform:uppercase;text-decoration:none;color:#fff}.lg b{color:var(--ac)}
nav.top ul{display:flex;gap:26px;list-style:none;padding:0}nav.top li a{font:600 12px var(--mono);letter-spacing:.1em;text-transform:uppercase;text-decoration:none;color:#fff}nav.top li a:hover{color:var(--ac)}
#hero{position:relative;height:380vh}.stage{position:sticky;top:0;height:100svh;overflow:hidden;background:#000}
.stage video,.stage .poster{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.stage:after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.75),rgba(0,0,0,.1) 60%),linear-gradient(0deg,rgba(0,0,0,.7),transparent 40%);pointer-events:none}
.hud{position:absolute;z-index:3;inset:0;padding:clamp(80px,12vh,120px) clamp(18px,4vw,64px) 6vh;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,380px);gap:24px;align-items:end}
.cp{position:relative;min-height:46vh}.cap{position:absolute;left:0;bottom:0;opacity:0;transform:translateY(30px);transition:opacity .5s,transform .6s}.cap.on{opacity:1;transform:none}
.cap h1,.cap h2{font-size:clamp(46px,9vw,150px)}.cap p{font:600 13px var(--mono);letter-spacing:.14em;text-transform:uppercase;margin-top:14px;color:#d6dae0}
.plate{background:rgba(16,18,21,.82);backdrop-filter:blur(8px);border:1px solid var(--ln);padding:22px}
.plate label{display:block;margin-bottom:10px}.plate input{width:100%;min-height:58px;background:#f4d03f;color:#111;border:0;border-left:34px solid #1e4aa8;font:700 28px var(--mono);letter-spacing:.12em;text-transform:uppercase;padding:0 12px}
.plate .btn{width:100%;margin-top:12px}
.gauge{position:absolute;z-index:3;top:clamp(80px,12vh,110px);right:clamp(18px,4vw,64px);width:150px;text-align:center}
.gauge svg{width:150px;height:96px}.gauge output{display:block;font:700 28px var(--mono);margin-top:-6px;font-variant-numeric:tabular-nums}.gauge span{font:600 10px var(--mono);letter-spacing:.14em;color:var(--mut)}
.prog{position:absolute;z-index:3;left:clamp(18px,4vw,64px);right:clamp(18px,4vw,64px);bottom:3vh;height:2px;background:rgba(255,255,255,.2)}.prog i{display:block;height:100%;width:0;background:var(--ac)}
/* bant */
.tape{background:var(--ac);color:#fff;overflow:hidden;padding:14px 0;transform:rotate(-1.2deg);margin:-14px -20px 0;position:relative;z-index:4}
.tape div{display:flex;width:max-content;gap:40px;animation:tp 26s linear infinite}.tape span{font:700 24px/1 var(--hf);text-transform:uppercase;white-space:nowrap}
@keyframes tp{to{transform:translateX(-50%)}}
/* paketler yatay */
.pk{position:relative;padding-top:12vh}.pk>h2{font-size:clamp(46px,8vw,120px);padding:0 clamp(18px,4vw,64px)}.pk>p{padding:14px clamp(18px,4vw,64px) 0;color:var(--mut);max-width:60ch}
.pin{overflow:hidden;margin-top:5vh}.trk{display:flex;gap:22px;padding:0 clamp(18px,4vw,64px) 12vh;width:max-content}
.cd{width:min(420px,82vw);flex:none;background:#171a1f;border:1px solid var(--ln);padding:26px;display:flex;flex-direction:column;gap:14px;transition:border-color .2s,transform .2s}
.cd:hover{border-color:var(--ac);transform:translateY(-4px)}.cd h3{font-size:36px}.cd .pr{font:700 44px/1 var(--mono);font-variant-numeric:tabular-nums}.cd ul{list-style:none;padding:0;display:grid;gap:8px;color:#cfd4da;font-size:15px}
.cd li{display:flex;gap:10px}.cd li:before{content:'';flex:none;width:14px;height:14px;margin-top:4px;border:2px solid var(--ac);background:linear-gradient(var(--ac),var(--ac)) center/6px 6px no-repeat}
.cd button{margin-top:auto}.cd[aria-pressed=true]{border-color:var(--ac);background:#2a1215}
.cd button[aria-pressed=true]{background:#fff;color:#111}
.bar{position:sticky;bottom:0;z-index:20;display:flex;justify-content:space-between;align-items:center;gap:14px;padding:14px clamp(18px,4vw,64px);background:#f0f1f3;color:#111;transform:translateY(100%);transition:transform .35s}.bar.on{transform:none}
.bar b{font:700 22px var(--mono)}.bar span{font:600 12px var(--mono);text-transform:uppercase}
/* durum */
.du{padding:14vh clamp(18px,4vw,64px);max-width:1300px;margin:auto}.du h2{font-size:clamp(46px,8vw,120px)}
.qr{display:flex;gap:10px;margin-top:5vh;flex-wrap:wrap}.qr input{flex:1;min-width:220px;min-height:56px;background:#f4d03f;color:#111;border:0;border-left:30px solid #1e4aa8;font:700 24px var(--mono);letter-spacing:.12em;text-transform:uppercase;padding:0 12px}
.st{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));margin-top:7vh;position:relative}
.st:before,.st i.fl{content:'';position:absolute;top:19px;left:10%;height:3px;background:var(--ln);right:10%}.st i.fl{background:var(--ac);right:auto;width:0}
.sp{position:relative;text-align:center;z-index:1}.sp b{display:grid;place-items:center;width:40px;height:40px;margin:0 auto 10px;border-radius:50%;background:var(--bg);border:3px solid var(--ln);font:700 14px var(--mono);transition:border-color .3s,background .3s}
.sp.on b{border-color:var(--ac);background:var(--ac);color:#fff}.sp span{font:600 12px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--mut)}.sp.on span{color:var(--ink)}
.res{margin-top:5vh;padding:20px 22px;border:1px solid var(--ln);display:none;gap:6px}.res.on{display:grid}.res b{font:700 22px var(--hf);text-transform:uppercase}
/* ekip */
.tm{padding:12vh clamp(18px,4vw,64px);max-width:1300px;margin:auto}.tm h2{font-size:clamp(46px,8vw,120px);margin-bottom:5vh}
.tr{display:flex;justify-content:space-between;align-items:baseline;gap:16px;padding:22px 0;border-top:1px solid var(--ln);cursor:pointer;transition:padding .25s,color .2s}.tr:last-of-type{border-bottom:1px solid var(--ln)}
.tr b{font:700 clamp(40px,7vw,96px)/1 var(--hf);text-transform:uppercase}.tr span{font:600 13px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--mut)}
.tr:hover{padding-left:24px;color:var(--ac)}
.pv{position:fixed;z-index:60;width:260px;aspect-ratio:3/4;pointer-events:none;border-radius:6px;overflow:hidden;opacity:0;transform:translate(-50%,-50%) scale(.85);transition:opacity .2s,transform .2s;box-shadow:0 20px 50px rgba(0,0,0,.6)}
.pv.on{opacity:1;transform:translate(-50%,-50%) scale(1)}.pv img{width:100%;height:100%;object-fit:cover}
/* şerit galeri */
.gl{padding:6vh 0 12vh;overflow:hidden}.gl h2{font-size:clamp(46px,8vw,120px);padding:0 clamp(18px,4vw,64px);margin-bottom:5vh}
.rw{display:flex;gap:14px;width:max-content;margin-bottom:14px}.rw img{height:clamp(160px,24vw,320px);width:auto;aspect-ratio:4/3;object-fit:cover;border-radius:4px}
/* randevu */
.rd{padding:12vh clamp(18px,4vw,64px);display:grid;grid-template-columns:minmax(0,1fr) minmax(0,600px);gap:clamp(24px,6vw,96px);max-width:1400px;margin:auto;align-items:start}
.rd h2{font-size:clamp(46px,8vw,120px)}.rd .l p{margin-top:18px;color:var(--mut)}
form.fm{display:grid;gap:14px;border:1px solid var(--ln);padding:24px;background:#15181c}
.fm label{display:grid;gap:6px;font:600 12px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--mut)}
.fm input,.fm select{min-height:50px;padding:0 14px;background:transparent;border:1px solid var(--ln);color:var(--ink);font:500 16px var(--bf)}.fm select option{color:#111}
.fm input:focus-visible,.fm select:focus-visible{border-color:var(--ac)}
.chk{display:flex;flex-wrap:wrap;gap:8px}.chk button{all:unset;box-sizing:border-box;padding:10px 14px;border:1px solid var(--ln);font:600 12px var(--mono);text-transform:uppercase;cursor:pointer}.chk button[aria-pressed=true]{background:var(--ac);border-color:var(--ac);color:#fff}.chk button:focus-visible{outline:3px solid var(--ac)}
.ok{display:none;padding:16px;border:1px solid var(--ac)}.ok.on{display:block}
.fin{min-height:90svh;display:grid;place-items:center;text-align:center;padding:12vh 18px;background:radial-gradient(55% 45% at 50% 60%,#4a0c11,transparent 70%)}
.fin h2{font-size:clamp(46px,11vw,180px);-webkit-text-stroke:2px var(--ink);color:transparent}.fin h2 span{display:block;-webkit-text-stroke:0;color:var(--ac)}.fin .btn{margin-top:5vh}
footer{padding:44px clamp(18px,4vw,64px) 32px;border-top:1px solid var(--ln);display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:24px}footer b{font:700 32px/1 var(--hf);text-transform:uppercase}footer p{color:var(--mut);font-size:14px}
@media(max-width:860px){nav.top ul{display:none}.hud{grid-template-columns:minmax(0,1fr)}.cp{min-height:30vh}.gauge{display:none}.plate{padding:14px}.plate input{min-height:50px;font-size:22px}.rd{grid-template-columns:minmax(0,1fr)}.trk{overflow:visible}.pin{overflow-x:auto}.st .sp span{font-size:10px}.tr:hover{padding-left:0}}

@media(max-width:860px){.mb{grid-template-columns:1fr 1fr 1.6fr;background:#0a0b0d;border-top:3px solid var(--ac)}.mb a{font-family:var(--hf);font-size:15px;letter-spacing:.04em;min-height:60px}.mb a.p{background:#f4d03f;color:#111}
.mm{justify-content:flex-start;padding-top:110px;counter-reset:n}.mm a{font:700 clamp(34px,9vw,52px)/1 var(--hf);text-transform:uppercase;display:flex;gap:16px;align-items:baseline;counter-increment:n}.mm a:before{content:'0' counter(n);font:600 13px var(--mono);color:var(--ac)}}
footer{background:#0a0b0d}
@media(prefers-reduced-motion:reduce){.cap{opacity:1;transform:none;position:static}.cp{min-height:0}#hero{height:auto}.stage{height:auto;min-height:80svh}.pin{overflow-x:auto}}
'''
JS = '''
OK.start(function(){var $=OK.$,$$=OK.$$,money=OK.money,rd=OK.reduce;
 var caps=$$('.cap'),pr=$('.prog i'),needle=$('#nd'),rpm=$('#rpm'),v=$('#hv');
 OK.scrub('#hero',v,function(p){pr.style.width=(p*100)+'%';var n=Math.min(caps.length-1,Math.floor(p*caps.length*.999));caps.forEach(function(c,i){c.classList.toggle('on',i===n)});
  var val=Math.round(800+p*6400);rpm.textContent=val.toLocaleString('tr-TR');needle.setAttribute('transform','rotate('+(-90+p*180)+' 75 80)')});
 caps[0].classList.add('on');
 /* yatay paketler */
 var trk=$('.trk'),pin=$('.pin');
 if(!rd&&matchMedia('(min-width:861px)').matches){var dist=function(){return trk.scrollWidth-innerWidth+0};
  gsap.to(trk,{x:function(){return -dist()},ease:'none',scrollTrigger:{trigger:pin,start:'top 12%',end:function(){return '+='+dist()},pin:true,scrub:1,invalidateOnRefresh:true}})}
 var sel={};var bar=$('.bar');
 function upd(){var ks=Object.keys(sel),sum=0;ks.forEach(function(k){sum+=C.pk[k][1]});$('#bn').textContent=ks.length?ks.map(function(k){return C.pk[k][0]}).join(' + '):'';var o={v:+$('#bt').dataset.v||0};gsap.to(o,{v:sum,duration:.4,onUpdate:function(){$('#bt').textContent=money(o.v);$('#bt').dataset.v=o.v}});bar.classList.toggle('on',ks.length>0);
  $$('.chk button').forEach(function(b){b.setAttribute('aria-pressed',!!sel[b.dataset.k])})}
 $$('.cd button').forEach(function(b){b.addEventListener('click',function(){var k=b.dataset.k;if(sel[k])delete sel[k];else sel[k]=1;b.setAttribute('aria-pressed',!!sel[k]);b.closest('.cd').setAttribute('aria-pressed',!!sel[k]);b.textContent=sel[k]?'Seçildi':'Paketi seç';upd()})});
 $$('.chk button').forEach(function(b){b.addEventListener('click',function(e){e.preventDefault();var k=b.dataset.k;if(sel[k])delete sel[k];else sel[k]=1;var cb=$('.cd button[data-k="'+k+'"]');cb.setAttribute('aria-pressed',!!sel[k]);cb.closest('.cd').setAttribute('aria-pressed',!!sel[k]);cb.textContent=sel[k]?'Seçildi':'Paketi seç';upd()})});
 /* plaka */
 function fmt(s){return s.toUpperCase().replace(/[^0-9A-Z ]/g,'').slice(0,12)}
 $$('input.pl').forEach(function(i){i.addEventListener('input',function(){i.value=fmt(i.value)})});
 $('#hp').addEventListener('click',function(){var v=$('#hpi').value.trim();$('#dpi').value=v;$('#rpl').value=v;if(window._lenis)_lenis.scrollTo('#durum');else location.hash='#durum';setTimeout(sorgu,900)});
 function sorgu(){var v=$('#dpi').value.trim();var res=$('.res');if(!v){$('#dpi').focus();return}
  var d=2+(v.length%2);var fl=$('.st i.fl');$$('.sp').forEach(function(s,i){s.classList.toggle('on',i<=d)});gsap.to(fl,{width:(d/4*80)+'%',duration:1,ease:'power2.out'});
  res.classList.add('on');$('#rs1').textContent=v+' · '+['Teşhis tamamlandı, onay bekleniyor','Parçalar sipariş edildi, işlem başlıyor','İşlem sürüyor, teslim bugün'][d-2+0>2?2:d-2];$('#rs2').textContent='Güncel adım: '+C.st[d]}
 $('#dq').addEventListener('click',sorgu);$('#dpi').addEventListener('keydown',function(e){if(e.key==='Enter')sorgu()});
 /* ekip önizleme */
 var pv=$('.pv'),pi=$('.pv img');$$('.tr').forEach(function(r){r.addEventListener('mouseenter',function(){pi.src=r.dataset.img;pv.classList.add('on')});r.addEventListener('mouseleave',function(){pv.classList.remove('on')});r.addEventListener('mousemove',function(e){pv.style.left=(e.clientX+150)+'px';pv.style.top=e.clientY+'px'})});
 /* şerit galeri */
 if(!rd)$$('.rw').forEach(function(r,i){gsap.fromTo(r,{x:i%2?'-30%':'0%'},{x:i%2?'0%':'-30%',ease:'none',scrollTrigger:{trigger:'.gl',start:'top bottom',end:'bottom top',scrub:1}})});
 /* form */
 $('.fm').addEventListener('submit',function(e){e.preventDefault();$('.ok').classList.add('on');$('.ok').textContent='Randevu talebiniz alındı. Plaka '+($('#rpl').value||'-')+' için size dönüş yapacağız.'});
});
'''
def render():
    pk = ''.join('<article class="cd"><h3>%s</h3><div class="pr">%s ₺</div><ul>%s</ul><button class="btn" type="button" data-k="%d" aria-pressed="false">Paketi seç</button></article>' % (a, format(p, ',').replace(',', '.'), ''.join('<li>%s</li>' % H.escape(x) for x in l), i) for i, (a, p, l) in enumerate(PK))
    tm = ''.join('<div class="tr" data-img="%s" tabindex="0"><b>%s</b><span>%s</span></div>' % (ph(t[2] + 2, 520), t[0], H.escape(t[1])) for t in TEAM)
    rows = ''.join('<div class="rw">%s</div>' % ''.join('<img src="%s" alt="Atölye çalışması" loading="lazy">' % ph(k + r * 2, 700) for k in (0, 1, 2, 3, 4, 5) for _ in (0,)) for r in (0, 1, 2))
    chk = ''.join('<button type="button" data-k="%d" aria-pressed="false">%s</button>' % (i, a) for i, (a, _p, _l) in enumerate(PK))
    mq = ''.join('<span>%s</span>' % x for x in ['Periyodik bakım', 'Fren', 'Motor', 'Lastik', 'Akü', 'Klima', 'Yazılı teklif', 'Sürpriz fatura yok'] * 2)
    steps = ''.join('<div class="sp%s"><b>%d</b><span>%s</span></div>' % (' on' if i == 0 else '', i + 1, s) for i, s in enumerate(STAGES))
    body = '''<div id="pre" role="status"><div><b>MOTOR ATÖLYE</b><i><span id="pn">0</span>%%</i></div></div>
<nav class="top"><a class="lg" href="#">MOTOR<b>.</b>ATÖLYE</a><ul><li><a href="#paketler">Paketler</a></li><li><a href="#durum">Araç durumu</a></li><li><a href="#ekip">Ustalar</a></li><li><a href="#randevu">Randevu</a></li></ul><a class="btn" href="#randevu">Randevu al</a></nav>
<main><section id="hero" aria-label="Açılış"><div class="stage"><img class="poster" src="%(poster)s" alt="" fetchpriority="high"><video id="hv" muted playsinline preload="auto" poster="%(poster)s" src="%(v)s" aria-hidden="true"></video>
<div class="gauge" aria-hidden="true"><svg viewBox="0 0 150 96"><path d="M15 80 A60 60 0 0 1 135 80" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="6"/><path d="M105 28 A60 60 0 0 1 135 80" fill="none" stroke="#e4262f" stroke-width="6"/><g id="nd" transform="rotate(-90 75 80)"><path d="M75 80 L75 28" stroke="#fff" stroke-width="3" stroke-linecap="round"/></g><circle cx="75" cy="80" r="6" fill="#fff"/></svg><output id="rpm">800</output><span>DEVİR / DAK</span></div>
<div class="hud"><div class="cp"><div class="cap"><h1>ARAÇ GİRER.</h1><p>Plaka okunur, kayıt açılır</p></div><div class="cap"><h2>USTA BAKAR.</h2><p>Her adım yazılı ve fotoğraflı</p></div><div class="cap"><h2>SORUNSUZ ÇIKAR.</h2><p>Teslim saati baştan bellidir</p></div></div>
<div class="plate"><label class="lb" for="hpi">Plakanızı yazın</label><input id="hpi" class="pl" value="06 ABC 123" autocomplete="off" maxlength="12"><button class="btn" id="hp" type="button">Aracımın durumuna bak</button></div></div><div class="prog"><i></i></div></div></section>
<div class="tape" aria-hidden="true"><div>%(mq)s</div></div>
<section class="pk" id="paketler"><h2 class="rv">PAKETİ SEÇ.</h2><p>Kaç liraya, neye bakılacak, baştan yazılı. Paketlere dokunarak birden fazlasını birleştirebilirsin.</p><div class="pin"><div class="trk">%(pk)s</div></div></section>
<div class="bar" aria-live="polite"><div><span>Seçilen</span><br><span id="bn" style="color:#555"></span></div><b id="bt" data-v="0">0 ₺</b><a class="btn" href="#randevu">Randevuya geç</a></div>
<section class="du" id="durum"><h2 class="rv">ARACIN NEREDE?</h2><div class="qr"><input id="dpi" class="pl" value="" placeholder="PLAKA" aria-label="Plaka" maxlength="12"><button class="btn" id="dq" type="button">Durumu göster</button></div><div class="st"><i class="fl"></i>%(steps)s</div><div class="res" aria-live="polite"><b id="rs1"></b><span id="rs2"></span></div></section>
<section class="tm" id="ekip"><h2 class="rv">USTALAR.</h2>%(tm)s</section><div class="pv" aria-hidden="true"><img alt=""></div>
<section class="gl" aria-label="Atölyeden kareler"><h2 class="rv">ATÖLYE.</h2>%(rows)s</section>
<section class="rd" id="randevu"><div class="l"><h2 class="rv">ARACINI GETİR.</h2><p>Gün ve saati sen seç, gerisi bizde.</p></div><form class="fm"><label>Plaka<input id="rpl" class="pl" required maxlength="12" autocomplete="off"></label><label>Marka ve model<select><option>Seçiniz</option><option>Renault Clio</option><option>Fiat Egea</option><option>Volkswagen Golf</option><option>Toyota Corolla</option><option>Diğer</option></select></label><div><span class="lb">Paketler</span><div class="chk" style="margin-top:8px">%(chk)s</div></div><label>Tarih<input type="date" required></label><label>Telefon<input type="tel" required inputmode="tel" autocomplete="tel"></label><button class="btn" type="submit">Randevu talep et</button><p class="ok" role="status"></p></form></section>
<section class="fin"><div><h2 class="rv">ARAÇ GİRER. <span>GÜVENLE ÇIKAR.</span></h2><a class="btn" href="#randevu">Randevu al</a></div></section></main>
<footer><div><b>MOTOR ATÖLYE</b><p>Oto servis</p></div><div class="cl"><p class="lb">Menü</p><a href="#paketler">Paketler</a><a href="#durum">Araç durumu</a><a href="#ekip">Ustalar</a><a href="#randevu">Randevu</a></div><div class="cl"><p class="lb">İletişim</p><a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a><p>Örnek Sanayi Sitesi · Ankara</p></div><div><p class="lb">Saatler</p><p>Hafta içi 08.30 – 18.30</p><p>Cumartesi 09.00 – 15.00</p></div><p class="cr">© 2026 Motor Atölye</p></footer>''' % dict(poster=POSTER, v=VURL, mq=mq, pk=pk, steps=steps, tm=tm, rows=rows, chk=chk)
    c = json.dumps(dict(pk=[[a, p] for a, p, _ in PK], st=STAGES), ensure_ascii=False)
    return page('Motor Atölye Oto Servis', 'Plakayla randevu, bakım paketleri ve araç durumu takibi.', ['Oswald:wght@500;700', 'IBM Plex Mono:wght@500;600;700', 'Inter:wght@400;500;700'], BASE_CSS + CSS, body, JS, c, dict(cta=['Randevu al','#randevu'], addr='Örnek Sanayi Sitesi · Ankara'))
if __name__ == '__main__':
    import os
    os.makedirs(R + '/motor', exist_ok=True); open(R + '/motor/index.html', 'w', encoding='utf-8').write(render()); print('motor ok')
