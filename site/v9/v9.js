(function(){var d=document,h=d.documentElement;h.classList.add('js');
var az=matchMedia('(prefers-reduced-motion:reduce)').matches;
// kademeli belirme: aynı kapsayıcıdaki kardeşler 70 ms arayla
var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){x.target.classList.add('in');io.unobserve(x.target)}})},{rootMargin:'0px 0px 15% 0px',threshold:0});
d.querySelectorAll('.gor').forEach(function(el){var k=[].indexOf.call(el.parentNode.children,el)%4;el.style.setProperty('--g',(k*70)+'ms');io.observe(el)});
// sayaçlar
var so=new IntersectionObserver(function(es){es.forEach(function(x){if(!x.isIntersecting)return;so.unobserve(x.target);var el=x.target,n=+el.dataset.say;if(az){return}
 var t0=performance.now();(function f(t){var p=Math.min((t-t0)/900,1);el.textContent=Math.round(n*(1-Math.pow(1-p,3)));if(p<1)requestAnimationFrame(f)})(t0)})},{threshold:.6});
d.querySelectorAll('[data-say]').forEach(function(el){so.observe(el)});
// tema filtresi
d.querySelectorAll('.flt button').forEach(function(b){b.addEventListener('click',function(){d.querySelectorAll('.flt button').forEach(function(x){x.classList.toggle('on',x===b)});
 var f=b.dataset.f;d.querySelector('.tkg').classList.add('acik');d.querySelectorAll('.tkg .tk[data-k]').forEach(function(c){c.hidden=!(f==='tum'||c.dataset.k===f);c.classList.add('in')})})});
// "6 mağaza temasının hepsi": filtreyi açar, listeye iner (başka sayfadaysa temalar sayfasında açılır)
function tf(f){var b=d.querySelector('.flt button[data-f="'+f+'"]');if(!b)return false;b.click();var t=d.querySelector('.flt');if(t)t.scrollIntoView({behavior:az?'auto':'smooth',block:'start'});return true}
d.querySelectorAll('a[data-f]').forEach(function(a){a.addEventListener('click',function(e){if(tf(a.dataset.f))e.preventDefault()})});
if(/^#(eticaret|teknik|kuafor|oto)$/.test(location.hash))setTimeout(function(){tf(location.hash.slice(1))},300);
// e-ticaret: kaydırdıkça yapışkan menüde etkin başlık
var nav=d.querySelectorAll('.enav a');var eo=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){nav.forEach(function(a){var on=a.getAttribute('href')==='#'+x.target.id;a.classList.toggle('on',on);if(on&&innerWidth<761)a.parentNode.scrollLeft=a.offsetLeft-20})}})},{rootMargin:'-35% 0px -55% 0px'});
d.querySelectorAll('.sah').forEach(function(s){eo.observe(s)});
var dh=d.querySelector('.daha');if(dh)dh.addEventListener('click',function(){d.querySelector('.tkg').classList.add('acik')});
// SSS
d.querySelectorAll('.q').forEach(function(q){q.tabIndex=0;q.setAttribute('role','button');q.setAttribute('aria-expanded',q.classList.contains('ac'));function t(){q.classList.toggle('ac');q.setAttribute('aria-expanded',q.classList.contains('ac'))}q.addEventListener('click',t);q.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();t()}})});
})();
