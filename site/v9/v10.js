(function(){var d=document,b=d.body,u=d.querySelector('.ust');if(!u)return;
var az=matchMedia('(prefers-reduced-motion:reduce)').matches;
var bt=u.querySelector('.mnu'),ck=u.querySelector('.cek');
function ac(x){if(x&&ck)ck.style.top=Math.max(u.getBoundingClientRect().bottom,0)+'px';u.classList.toggle('acik',x);b.classList.toggle('kilit',x);if(bt){bt.setAttribute('aria-expanded',x);bt.setAttribute('aria-label',x?'Menüyü kapat':'Menüyü aç')}}
if(bt){bt.addEventListener('click',function(){ac(!u.classList.contains('acik'))});
 d.addEventListener('keydown',function(e){if(e.key==='Escape'&&u.classList.contains('acik')){ac(false);bt.focus()}});
 ck.addEventListener('click',function(e){if(e.target.closest('a'))ac(false)});
 matchMedia('(min-width:861px)').addEventListener('change',function(m){if(m.matches)ac(false)})}
// ilerleme çubuğu ve başlık gölgesi
var pr=d.createElement('div');pr.className='ilr';b.appendChild(pr);
var tk=0;function sc(){tk=0;var y=scrollY,h=d.documentElement.scrollHeight-innerHeight;pr.style.transform='scaleX('+(h>0?y/h:0)+')';u.classList.toggle('kay',y>8);
 if(!az)d.querySelectorAll('[data-px]').forEach(function(e){var r=e.getBoundingClientRect();if(r.bottom<0||r.top>innerHeight)return;e.style.transform='translate3d(0,'+((r.top-innerHeight/2)*(+e.dataset.px)).toFixed(1)+'px,0)'})}
addEventListener('scroll',function(){if(!tk)tk=requestAnimationFrame(sc)},{passive:true});sc();
// eğim: ince işaretçi cihazlarda
if(!az&&matchMedia('(hover:hover)').matches)d.querySelectorAll('[data-tilt]').forEach(function(e){
 e.addEventListener('mousemove',function(v){var r=e.getBoundingClientRect(),x=(v.clientX-r.left)/r.width-.5,y=(v.clientY-r.top)/r.height-.5;e.style.transform='perspective(900px) rotateY('+(x*6).toFixed(2)+'deg) rotateX('+(-y*5).toFixed(2)+'deg)'});
 e.addEventListener('mouseleave',function(){e.style.transform=''})});
// kapı kartları belirme
var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){x.target.classList.add('in');io.unobserve(x.target)}})},{threshold:.15});
d.querySelectorAll('.kp,.fk').forEach(function(e,i){e.style.setProperty('--g',(i%3*90)+'ms');if(e.classList.contains('fk'))e.classList.add('gor');io.observe(e)});
d.querySelectorAll('.sec .b1,.sec h2').forEach(function(e){io.observe(e)});
})();
