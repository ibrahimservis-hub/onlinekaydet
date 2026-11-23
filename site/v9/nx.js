/* Yeni ana sayfa davranışları: menü, sekmeler, görünür olunca, kod akışı, sayaç */
(function(){
var RM=matchMedia('(prefers-reduced-motion:reduce)').matches,$=function(s,r){return (r||document).querySelector(s)},$$=function(s,r){return [].slice.call((r||document).querySelectorAll(s))};
// üst menü: kaydırınca daralır; hamburger tam ekran menü
var ust=$('#ust'),mm=$('#mmenu'),hm=$('.ust .hm');
addEventListener('scroll',function(){ust.classList.toggle('kc',scrollY>20)},{passive:true});
function kapat(){ust.classList.remove('ac');mm.classList.remove('ac');hm.setAttribute('aria-expanded','false');hm.setAttribute('aria-label','Menüyü aç');document.body.style.overflow=''}
hm.addEventListener('click',function(){var a=!mm.classList.contains('ac');if(!a)return kapat();ust.classList.add('ac');mm.classList.add('ac');hm.setAttribute('aria-expanded','true');hm.setAttribute('aria-label','Menüyü kapat');document.body.style.overflow='hidden'});
mm.addEventListener('click',function(e){if(e.target.closest('a'))kapat()});
addEventListener('keydown',function(e){if(e.key==='Escape'){kapat();$$('.ust details[open]').forEach(function(d){d.open=false})}});
document.addEventListener('click',function(e){$$('.ust details[open]').forEach(function(d){if(!d.contains(e.target))d.open=false})});
$$('.ust details').forEach(function(d){d.addEventListener('toggle',function(){if(d.open)$$('.ust details').forEach(function(o){if(o!==d)o.open=false})})});
// modül sekmeleri
var tb=$$('.mod .liste button'),kr=$$('.mod .kart'),sy=$('#msay');
function sec(i){tb.forEach(function(b,k){var on=k===i;b.classList.toggle('on',on);b.setAttribute('aria-selected',on?'true':'false');b.tabIndex=on?0:-1});kr.forEach(function(c,k){c.classList.toggle('on',k===i)});if(sy)sy.textContent=('0'+(i+1)).slice(-2)}
tb.forEach(function(b,i){b.addEventListener('click',function(){sec(i)});b.addEventListener('keydown',function(e){var n=e.key==='ArrowDown'||e.key==='ArrowRight'?1:e.key==='ArrowUp'||e.key==='ArrowLeft'?-1:0;if(n){e.preventDefault();var j=(i+n+tb.length)%tb.length;sec(j);tb[j].focus()}})});
if(tb.length)sec(0);
// görünür olunca
var io='IntersectionObserver' in window?new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('ac');io.unobserve(e.target);if(e.target.id==='kod')akis();if(e.target.classList.contains('say'))say(e.target)}})},{threshold:.2}):null;
$$('.gz').forEach(function(el){io&&!RM?io.observe(el):el.classList.add('ac')});
// kod akışı: satırlar sırayla çalışır, sonra baştan
var kod=$('#kod');
function akis(){var L=$$('#kod li');if(RM){L.forEach(function(l){l.classList.add('on')});return}var i=0;
 (function adim(){L.forEach(function(l,k){l.classList.toggle('on',k<i);l.classList.toggle('cur',k===i)});
  if(i<L.length){i++;setTimeout(adim,650)}else setTimeout(function(){i=0;adim()},2600)})()}
if(kod){if(io&&!RM)io.observe(kod);else akis()}
// sayaç
function say(box){$$('[data-say]',box).forEach(function(b){var n=+b.dataset.say;if(RM){b.textContent=n;return}var t0=null;(function f(t){if(!t0)t0=t;var p=Math.min(1,(t-t0)/1400);b.textContent=Math.round(n*(1-Math.pow(1-p,3)));if(p<1)requestAnimationFrame(f)})(performance.now())})}
var sb=$('.say');if(sb&&!(io&&!RM))say(sb);
})();
