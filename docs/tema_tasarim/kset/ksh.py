"""Kuaför tasarım seti ortak parçaları: randevu sayfası (otomatik tarih/saat), lightbox, 'şu an açık', canlı boş saat.
Tasarımlar bunları yalnızca davranış için paylaşır; düzen, menü, modül ve görünüm her dosyada ayrıdır."""
import json
PX = "https://images.pexels.com/photos/{0}/pexels-photo-{0}.jpeg?auto=compress&cs=tinysrgb&w={1}"
EXPERTS = ['Elif', 'Murat', 'Selin']
SERVICES = ['Kesim ve fön', 'Tek renk boya', 'Balyaj ve ombre', 'Keratin bakım', 'Gelin saçı', 'Erkek kesim']

SHEET_CSS = """
#sh{position:fixed;inset:0;z-index:300;background:rgba(10,6,4,.55);backdrop-filter:blur(4px);opacity:0;visibility:hidden;transition:.4s}
#sh.on{opacity:1;visibility:visible}
#sh .sheet{position:absolute;left:0;right:0;bottom:0;max-height:92svh;overflow:auto;background:var(--sbg);color:var(--sink);border-radius:26px 26px 0 0;padding:10px 22px calc(env(safe-area-inset-bottom) + 22px);transform:translateY(100%);transition:transform .6s cubic-bezier(.2,.8,.2,1);font-family:var(--sbody,inherit)}
#sh.on .sheet{transform:none}
#sh .grab{width:44px;height:4px;border-radius:4px;background:var(--sline);margin:0 auto 14px}
#sh h3{font:var(--shw,400) 32px/1.1 var(--sfont);margin-bottom:4px}#sh .sub{opacity:.65;font-size:14px}
#sh h4{font:600 12px var(--sbody,sans-serif);letter-spacing:.14em;text-transform:uppercase;color:var(--sac);margin:18px 0 9px}
#sh .opts{display:flex;gap:8px;flex-wrap:wrap}
#sh .opts button{min-height:44px;padding:0 16px;border-radius:var(--sr,99px);border:1.5px solid var(--sline);font-weight:500;background:transparent;color:inherit;cursor:pointer;font-size:15px;transition:.2s}
#sh .opts button.on{background:var(--sink);color:var(--sbg);border-color:var(--sink)}
#sh .opts button:disabled{opacity:.3;text-decoration:line-through;cursor:not-allowed}
#sh .days button{display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1.15;min-width:62px;padding:6px 10px;border-radius:16px}#sh .days small{font-size:11px;opacity:.7}
#sh .fld{display:grid;gap:12px}#sh label{font-size:13px;font-weight:600;opacity:.8;display:grid;gap:6px}
#sh input{min-height:50px;border-radius:14px;border:1.5px solid var(--sline);padding:0 14px;background:transparent;color:inherit;font-size:16px;width:100%}
#sh input:focus{outline:2px solid var(--sac)}
#sh .go{width:100%;margin-top:20px;min-height:54px;border-radius:var(--sr,99px);background:var(--sac);color:#fff;font-weight:600;font-size:16px;border:0;cursor:pointer}
#sh .ok{display:none;text-align:center;padding:30px 0 10px}.sheet.done .ok{display:block}.sheet.done .frm{display:none}
#sh .tick{width:72px;height:72px;border-radius:50%;background:var(--sac);margin:0 auto 18px;display:grid;place-items:center}
#sh .tick svg{width:34px;stroke:#fff;fill:none;stroke-width:3;stroke-dasharray:40;stroke-dashoffset:40}.sheet.done .tick svg{animation:dr .8s .2s forwards}
@keyframes dr{to{stroke-dashoffset:0}}
#sh .ok p{opacity:.7;margin:8px auto 18px;max-width:300px}
#sh .ok button{min-height:48px;padding:0 26px;border-radius:var(--sr,99px);border:1.5px solid var(--sline);background:transparent;color:inherit;cursor:pointer;font-weight:600}
@media(min-width:900px){#sh .sheet{left:50%;right:auto;width:560px;margin-left:-280px;bottom:50%;transform:translateY(55%);border-radius:26px;opacity:0;transition:transform .6s cubic-bezier(.2,.8,.2,1),opacity .4s}#sh.on .sheet{transform:translateY(50%);opacity:1}}
#lb{position:fixed;inset:0;z-index:400;background:rgba(10,6,4,.95);display:none;align-items:center;justify-content:center}
#lb.on{display:flex}
#lb img{max-width:94vw;max-height:80svh;border-radius:12px;object-fit:contain;transition:opacity .3s}
#lb button{position:absolute;width:48px;height:48px;border-radius:50%;background:rgba(255,255,255,.14);color:#fff;font-size:22px;border:0;cursor:pointer}
#lb .x{top:14px;right:14px}#lb .p{left:10px;top:50%}#lb .n{right:10px;top:50%}
#lb .ct{position:absolute;bottom:22px;left:0;right:0;text-align:center;font-size:14px;color:#cbbfb3}
.rv{opacity:0;transform:translateY(16px);transition:opacity 1s ease,transform 1s ease}.rv.v{opacity:1;transform:none}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.rv{opacity:1;transform:none}}
"""


def sheet_html(svcs=SERVICES, exps=EXPERTS):
    s = ''.join('<button>%s</button>' % x for x in svcs)
    e = '<button class="on">Fark etmez</button>' + ''.join('<button>%s</button>' % x for x in exps)
    return ('<div id="sh" aria-hidden="true"><div class="sheet" id="shs"><div class="grab"></div><div class="frm"><h3>Randevu al</h3>'
            '<div class="sub">Salon panelindeki kayıtla aynı alanlar.</div><h4>Hizmet</h4><div class="opts" id="o-s">%s</div><h4>Uzman</h4><div class="opts" id="o-e">%s</div>'
            '<h4>Gün</h4><div class="opts days" id="o-d"></div><h4>Saat <span id="o-cnt" style="text-transform:none;letter-spacing:0;font-weight:500;opacity:.7"></span></h4><div class="opts" id="o-t"></div>'
            '<h4>Bilgileriniz</h4><div class="fld"><label>Ad soyad<input id="f-n" autocomplete="name" placeholder="Ayşe Yılmaz"></label><label>Telefon<input id="f-p" type="tel" autocomplete="tel" placeholder="05xx xxx xx xx"></label></div>'
            '<label data-mod="pazarlama" style="display:none">Kupon kodu (varsa)<input id="f-c" autocomplete="off" placeholder="KUPON"></label><div id="f-msg" role="alert" style="display:none;margin-top:12px;color:#e11d48;font-size:14px;font-weight:600"></div><button class="go" id="go">Randevuyu kaydet</button></div>'
            '<div class="ok"><div class="tick"><svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></div><h3>Randevunuz alındı</h3><p id="okp"></p><button id="okx">Tamam</button></div></div></div>'
            '<div id="lb"><button class="x" aria-label="Kapat">×</button><button class="p" aria-label="Önceki">‹</button><img alt="Salon fotoğrafı"><button class="n" aria-label="Sonraki">›</button><div class="ct"></div></div>') % (s, e)


CORE = r"""
(function(){
var $=function(s,r){return(r||document).querySelector(s)},A=function(s,r){return[].slice.call((r||document).querySelectorAll(s))};
var PX=function(i,w){return'https://images.pexels.com/photos/'+i+'/pexels-photo-'+i+'.jpeg?auto=compress&cs=tinysrgb&w='+(w||1400)};
function paint(){A('[data-p]').forEach(function(e){if(!e.style.backgroundImage)e.style.backgroundImage='url("'+PX(e.dataset.p,+e.dataset.w||1400)+'")'});A('img[data-i]').forEach(function(e){if(!e.src)e.src=PX(e.dataset.i,+e.dataset.w||800)})}paint();
var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.add('v');io.unobserve(en.target)}})},{threshold:.12});
A('.rv').forEach(function(e){io.observe(e)});
var EXP=__EXP__,HRS=[600,660,720,780,840,900,960,1020,1080,1140],DN=['Paz','Pzt','Sal','Çar','Per','Cum','Cmt'],DL=['Pazar','Pazartesi','Salı','Çarşamba','Perşembe','Cuma','Cumartesi'],MO=['Oca','Şub','Mar','Nis','May','Haz','Tem','Ağu','Eyl','Eki','Kas','Ara'];
function ist(){return new Date(new Date().toLocaleString('en-US',{timeZone:'Europe/Istanbul'}))}
function key(d){return d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate()}
function p2(n){return(n<10?'0':'')+n}
function iso(d){return d.getFullYear()+'-'+p2(d.getMonth()+1)+'-'+p2(d.getDate())}
var LIVE=!!window.__OKLIVE,L={ready:false,enabled:true,days:[],slots:{},at:0,notice:''};
function openDay(d){if(LIVE)return L.days.indexOf(iso(d))>=0;var g=d.getDay();return g>=2&&g<=6}
function booked(d,e,m){var h=m/60,x=Math.sin((d.getFullYear()*10000+(d.getMonth()+1)*100+d.getDate())*13+h*7+e.charCodeAt(0)*31)*10000;return x-Math.floor(x)<.35}
function isFree(d,e,h){if(LIVE){var t=L.slots[iso(d)];return!!t&&t.some(function(s){return s.m===h&&s.available})}var n=ist();if(key(d)===key(n)&&h<n.getHours()*60+n.getMinutes()+60)return false;if(e==='Fark etmez')return EXP.some(function(x){return!booked(d,x,h)});return!booked(d,e,h)}
function hrs(){if(!LIVE)return HRS;var u={};Object.keys(L.slots).forEach(function(k){L.slots[k].forEach(function(s){u[s.m]=1})});return Object.keys(u).map(Number).sort(function(a,b){return a-b})}
function freeT(d,e){return hrs().filter(function(h){return isFree(d,e,h)})}
function fmt(m){return p2(Math.floor(m/60))+':'+p2(m%60)}
function days(){var n=ist(),o=[],k=0;while(o.length<7&&k<40){var d=new Date(n.getFullYear(),n.getMonth(),n.getDate()+k);k++;if(openDay(d)&&freeT(d,'Fark etmez').length)o.push(d)}return o}
function nextSlots(e,c){var o=[];days().forEach(function(d){freeT(d,e).forEach(function(h){if(o.length<c)o.push({d:d,h:h})})});return o}
function dayLab(d){var n=ist(),t=new Date(n.getFullYear(),n.getMonth(),n.getDate()+1);return key(d)===key(n)?'Bugün':key(d)===key(t)?'Yarın':DL[d.getDay()]}
window.OK={days:days,nextSlots:nextSlots,dayLab:dayLab,fmt:fmt,key:key,freeT:freeT,ist:ist,MO:MO,DN:DN};
function curE(){var b=$('#o-e .on');return b?b.textContent.trim():'Fark etmez'}
function renderDays(sel){var od=$('#o-d');od.innerHTML='';days().forEach(function(d){var b=document.createElement('button');b._d=d;b.dataset.k=key(d);b.dataset.v=d.getDate()+' '+MO[d.getMonth()];b.dataset.l=dayLab(d);b.innerHTML='<small>'+(dayLab(d)==='Bugün'?'Bugün':DN[d.getDay()])+'</small><b>'+d.getDate()+'</b><small>'+MO[d.getMonth()]+'</small>';od.appendChild(b)});var f=sel&&$('[data-k="'+sel+'"]',od);(f||od.firstChild).classList.add('on')}
function renderTimes(want){var d=$('#o-d .on')._d,e=curE(),ot=$('#o-t'),pv=want||($('#o-t .on')&&$('#o-t .on').dataset.v);ot.innerHTML='';var fr=freeT(d,e);hrs().forEach(function(h){var b=document.createElement('button');b.dataset.v=fmt(h);b.textContent=fmt(h);if(fr.indexOf(h)<0)b.disabled=true;ot.appendChild(b)});var f=pv&&$('[data-v="'+pv+'"]:not(:disabled)',ot),g=f||$('button:not(:disabled)',ot);if(g)g.classList.add('on');$('#o-cnt').textContent='· '+fr.length+' boş saat'}
['o-s','o-e','o-d','o-t'].forEach(function(id){$('#'+id).addEventListener('click',function(ev){var b=ev.target.closest('button');if(!b||b.disabled)return;A('button',this).forEach(function(x){x.classList.remove('on')});b.classList.add('on');if(id==='o-d'||id==='o-e')renderTimes()})});
function pick(id,val){var g=A('#'+id+' button');var f=g.filter(function(b){return(b.dataset.v||b.textContent.replace(/\s+/g,' ').trim())===val})[0];if(f)g.forEach(function(b){b.classList.toggle('on',b===f)});return!!f}
var sh=$('#sh'),shs=$('#shs');
function open(ds){err('');$('#go').disabled=!!(LIVE&&L.ready&&!L.enabled);if(LIVE&&L.ready&&!L.enabled){err('Online randevu şu an kapalı. Lütfen bizi arayın.')}shs.classList.remove('done');var s=ds.s||'Kesim ve fön';if(!pick('o-s',s)){var nb=document.createElement('button');nb.textContent=s;A('#o-s button').forEach(function(x){x.classList.remove('on')});nb.className='on';$('#o-s').appendChild(nb)}
pick('o-e',ds.e||'Fark etmez');renderDays(ds.d);renderTimes(ds.t);sh.classList.add('on');sh.setAttribute('aria-hidden','false');document.body.style.overflow='hidden'}
window.OK.open=open;
function close(){sh.classList.remove('on');sh.setAttribute('aria-hidden','true');document.body.style.overflow=''}
document.addEventListener('click',function(e){var o=e.target.closest('[data-open]');if(o){e.preventDefault();if(window.OK.beforeOpen)window.OK.beforeOpen();open(o.dataset)}});
sh.addEventListener('click',function(e){if(e.target===sh)close()});$('#okx').onclick=close;
function fin(n,s,d,t,msg){$('#okp').textContent=msg||(n.split(' ')[0]+', '+(s?s.textContent:'')+' için '+(d?d.dataset.l+' ('+d.dataset.v+')':'')+' saat '+t.dataset.v+' randevunuz salonun paneline düştü. Onaylanınca size mesaj gelecek.');shs.classList.add('done');refresh()}
function err(m){var e=$('#f-msg');if(e){e.textContent=m;e.style.display=m?'block':'none'}}
$('#go').onclick=function(){err('');var n=$('#f-n').value.trim(),s=$('#o-s .on'),d=$('#o-d .on'),t=$('#o-t .on'),ph=$('#f-p').value;if(!t){err('Lütfen gün ve saat seçin.');return}
if(!LIVE){fin(n||'Ayşe',s,d,t);return}
if(n.length<2){err('Lütfen adınızı yazın.');return}
if(ph.replace(/\D/g,'').length<10){err('Lütfen geçerli bir telefon numarası girin.');return}
var ex=$('#o-e .on'),cp=$('#f-c'),btn=$('#go'),note='Hizmet: '+(s?s.textContent:'')+(ex&&ex.textContent.trim()!=='Fark etmez'?' · Uzman: '+ex.textContent.trim():'');
btn.disabled=true;
fetch('/api/public/booking',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n,phone:ph,date:iso(d._d),time:t.dataset.v,device_type:s?s.textContent:'',fault:note,coupon:cp?cp.value:''})}).then(function(r){return r.json().then(function(j){return{ok:r.ok,j:j}})}).then(function(x){btn.disabled=false;if(!x.ok){err(x.j.detail||'Randevu kaydedilemedi, lütfen tekrar deneyin.');if(x.j.detail&&/dolu/.test(x.j.detail)){L.at=0;load(true)}return}fin(n,s,d,t,x.j.message)}).catch(function(){btn.disabled=false;err('Bağlantı kurulamadı, lütfen tekrar deneyin.')})};
function load(force){if(!LIVE)return;var now=Date.now();if(!force&&now-L.at<300000)return;L.at=now;fetch('/api/public/booking/config').then(function(r){return r.json()}).then(function(c){L.enabled=!!c.enabled;L.notice=c.notice||'';L.days=c.days||[];var ds=L.days.slice(0,8),left=ds.length;if(!left){L.ready=true;refresh();return}ds.forEach(function(dy){fetch('/api/public/booking/slots?date='+dy).then(function(r){return r.json()}).then(function(j){L.slots[dy]=(j.slots||[]).map(function(s){var q=s.time.split(':');return{m:+q[0]*60+ +q[1],available:!!s.available}})}).catch(function(){}).then(function(){if(--left===0){L.ready=true;refresh()}})})}).catch(function(){L.ready=true;refresh()})}
load(true);
var cp0=$('#f-c');if(cp0&&LIVE&&document.querySelector('[data-camp]')){cp0.parentNode.style.display='grid';cp0.addEventListener('blur',function(){var v=cp0.value.trim();if(!v)return;fetch('/api/public/coupon/'+encodeURIComponent(v)).then(function(r){return r.json()}).then(function(j){err(j.valid?'':(j.message||'Kupon geçersiz'));if(!j.valid)cp0.value=''})})}

/* canlı: [data-live] içindeki .chip'ler, [data-slots] uzman saatleri, [data-open-now] açık/kapalı */
function renderLive(){A('[data-live]').forEach(function(box){var ns=nextSlots('Fark etmez',+box.dataset.live||3);if(!ns.length)return;var first=ns[0].d,t=$('[data-live-t]',box);if(t)t.textContent=dayLab(first)==='Bugün'?'Bugün boş saatler':'En yakın boş saatler · '+dayLab(first);A('.chip',box).forEach(function(c){c.remove()});ns.forEach(function(x){var c=document.createElement('button');c.className='chip';c.dataset.open='';c.dataset.t=fmt(x.h);c.dataset.d=key(x.d);c.textContent=(dayLab(x.d)===dayLab(first)?'':dayLab(x.d).slice(0,3)+' ')+fmt(x.h);box.appendChild(c)})})}
function renderExp(){A('[data-slots]').forEach(function(w){var e=w.dataset.e,sv=w.dataset.s||'Kesim ve fön';w.innerHTML='';nextSlots(e,+w.dataset.slots||3).forEach(function(x){var c=document.createElement('button');c.className='chip';c.dataset.open='';c.dataset.s=sv;c.dataset.e=e;c.dataset.t=fmt(x.h);c.dataset.d=key(x.d);c.textContent=(dayLab(x.d)==='Bugün'?'':dayLab(x.d).slice(0,3)+' ')+fmt(x.h);w.appendChild(c)})})}
function openNow(){if(LIVE){var td=ist(),fr=L.ready&&freeT(td,'Fark etmez').length,t=!L.ready?'':!L.enabled?'Online randevu şu an kapalı':fr?'Bugün boş saat var':L.days.indexOf(iso(td))>=0?'Bugün için saatler doldu':'Bugün kapalı · en yakın boş gün aşağıda';A('[data-open-now]').forEach(function(e){e.classList.toggle('o',!!fr);e.classList.toggle('c',!fr);var s=$('span',e)||e;if(t)s.textContent=t});return}var d=ist(),g=d.getDay(),m=d.getHours()*60+d.getMinutes(),op=g>=2&&g<=6&&m>=600&&m<1200,t=op?"Şu an açık · 20:00'ye kadar":"Şu an kapalı · Salı–Cumartesi 10:00'da açılır";A('[data-open-now]').forEach(function(e){e.classList.toggle('c',!op);e.classList.toggle('o',op);var s=$('span',e)||e;s.textContent=t})}
function refresh(){renderLive();renderExp();openNow();if(window.OK.onRefresh)window.OK.onRefresh()}window.OK.refresh=refresh;refresh();setInterval(function(){load(false);refresh()},60000);document.addEventListener('visibilitychange',function(){if(!document.hidden)refresh()});
/* lightbox: .gi öğeleri, data-p kimliği */
var lb=$('#lb'),lim=$('img',lb),vis=[],li=0;
function show(i){li=(i+vis.length)%vis.length;lim.style.opacity=0;setTimeout(function(){lim.src=PX(vis[li].dataset.p,1600);lim.style.opacity=1},120);$('.ct',lb).textContent=(li+1)+' / '+vis.length}
document.addEventListener('click',function(e){var a=e.target.closest('.gi');if(!a)return;e.preventDefault();var c=a.closest('[data-gal]')||document;vis=A('.gi',c).filter(function(x){return x.offsetParent!==null&&!x.classList.contains('h')});show(vis.indexOf(a));lb.classList.add('on');document.body.style.overflow='hidden'});
function lbx(){lb.classList.remove('on');document.body.style.overflow=''}
$('.x',lb).onclick=lbx;$('.p',lb).onclick=function(){show(li-1)};$('.n',lb).onclick=function(){show(li+1)};lb.addEventListener('click',function(e){if(e.target===lb)lbx()});
var x0=0;lb.addEventListener('touchstart',function(e){x0=e.touches[0].clientX},{passive:true});lb.addEventListener('touchend',function(e){var d=e.changedTouches[0].clientX-x0;if(Math.abs(d)>50)show(li+(d<0?1:-1))});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){close();lbx();if(window.OK.esc)window.OK.esc()}if(lb.classList.contains('on')){if(e.key==='ArrowRight')show(li+1);if(e.key==='ArrowLeft')show(li-1)}});
/* galeri filtresi: [data-f] düğmeleri, .gi[data-c] */
A('[data-f]').forEach(function(b){b.addEventListener('click',function(){var c=b.closest('[data-gal]')||document,f=b.dataset.f;A('[data-f]',c).forEach(function(x){x.classList.toggle('on',x===b)});A('.gi',c).forEach(function(a){a.classList.toggle('h',f!=='all'&&a.dataset.c!==f)})})});
})();
"""


def core_js():
    return CORE.replace('__EXP__', json.dumps(EXPERTS, ensure_ascii=False))


def page(title, head_extra, css, body, js_extra='', theme='#111', fonts=''):
    return ('<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<meta name="theme-color" content="%s"><title>%s</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?%s&display=swap" rel="stylesheet">%s<style>%s%s</style></head><body>%s%s<script>%s</script><script>%s</script></body></html>'
            % (theme, title, fonts, head_extra, css, SHEET_CSS, body, sheet_html(), core_js(), js_extra))
