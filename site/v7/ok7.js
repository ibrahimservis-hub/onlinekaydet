(function(){
var d=document,h=d.getElementById('o7hd'),b=d.querySelector('.o7-bg'),root=d.documentElement;
if(b){b.addEventListener('click',function(){var o=root.classList.toggle('o7-open');b.setAttribute('aria-expanded',o)});
d.querySelectorAll('.o7-mm a').forEach(function(a){a.addEventListener('click',function(){root.classList.remove('o7-open');b.setAttribute('aria-expanded',false)})});
addEventListener('keydown',function(e){if(e.key==='Escape'){root.classList.remove('o7-open');b.setAttribute('aria-expanded',false)}});
addEventListener('resize',function(){if(innerWidth>1100)root.classList.remove('o7-open')})}
if(h){var f=function(){h.classList.toggle('sc',scrollY>40)};addEventListener('scroll',f,{passive:true});f()}
var io='IntersectionObserver' in window?new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{rootMargin:'0px 0px -8% 0px'}):null;
d.querySelectorAll('.rv,.pr').forEach(function(el){io?io.observe(el):el.classList.add('in')});
})();
(function(){document.querySelectorAll('.o7-dt').forEach(function(b){b.addEventListener('click',function(e){var d=b.parentNode,o=d.classList.contains('open');document.querySelectorAll('.o7-dd.open').forEach(function(x){x.classList.remove('open')});if(!o)d.classList.add('open');b.setAttribute('aria-expanded',!o);e.stopPropagation()})});document.addEventListener('click',function(){document.querySelectorAll('.o7-dd.open').forEach(function(x){x.classList.remove('open')})})})();
