/* İç sayfalar: yeni üst menü ve tam ekran mobil menü */
(function(){var h=document.getElementById('nxh'),m=document.getElementById('nxm');if(!h||!m)return;var b=h.querySelector('.hm');
addEventListener('scroll',function(){h.classList.toggle('kc',scrollY>20)},{passive:true});
function kapat(){h.classList.remove('ac');m.classList.remove('ac');b.setAttribute('aria-expanded','false');b.setAttribute('aria-label','Menüyü aç');document.body.style.overflow=''}
b.addEventListener('click',function(){if(m.classList.contains('ac'))return kapat();h.classList.add('ac');m.classList.add('ac');b.setAttribute('aria-expanded','true');b.setAttribute('aria-label','Menüyü kapat');document.body.style.overflow='hidden'});
m.addEventListener('click',function(e){if(e.target.closest('a'))kapat()});
var D=[].slice.call(h.querySelectorAll('details'));
addEventListener('keydown',function(e){if(e.key==='Escape'){kapat();D.forEach(function(d){d.open=false})}});
document.addEventListener('click',function(e){D.forEach(function(d){if(!d.contains(e.target))d.open=false})});
D.forEach(function(d){d.addEventListener('toggle',function(){if(d.open)D.forEach(function(o){if(o!==d)o.open=false})})});
var v=[].slice.call(document.querySelectorAll('.nxg video'));if(v.length&&'IntersectionObserver' in window&&!matchMedia('(prefers-reduced-motion:reduce)').matches){var io=new IntersectionObserver(function(es){es.forEach(function(e){e.isIntersecting?e.target.play().catch(function(){}):e.target.pause()})},{threshold:.3});v.forEach(function(x){io.observe(x)})}
})();
