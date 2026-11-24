# -*- coding: utf-8 -*-
"""Ortak parçalar: yükleme ekranı, Lenis + ScrollTrigger kurulumu, kaydırmayla video."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tema20'))
import foto
R = os.path.dirname(os.path.abspath(__file__))
def gf(*fams): return 'https://fonts.googleapis.com/css2?' + '&'.join('family=' + f.replace(' ', '+') for f in fams) + '&display=swap'
BASE_CSS = '''*{box-sizing:border-box;margin:0}html{overflow-x:clip}body{overflow-x:clip;-webkit-font-smoothing:antialiased}img,video{display:block;max-width:100%}a{color:inherit}
.lenis.lenis-smooth{scroll-behavior:auto!important}:focus-visible{outline:3px solid var(--ac);outline-offset:3px}
#pre{position:fixed;inset:0;z-index:100;display:grid;place-items:center;background:var(--bg);transition:opacity .6s,visibility .6s}#pre.off{opacity:0;visibility:hidden}
#pre b{display:block;font:400 clamp(44px,11vw,140px)/1 var(--hf);text-transform:uppercase;text-align:center}#pre i{display:block;text-align:center;font:600 14px var(--mono);font-style:normal;color:var(--mut);margin-top:10px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:48px;padding:0 22px;background:var(--ac);color:#fff;border:0;font:700 13px var(--mono);letter-spacing:.1em;text-transform:uppercase;text-decoration:none;cursor:pointer;transition:transform .15s,filter .15s}
.btn:hover{transform:translateY(-2px);filter:brightness(1.08)}.btn:active{transform:scale(.98)}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}'''
BOOT = '''
window.OK=(function(){var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
var $=function(s,r){return (r||document).querySelector(s)},$$=function(s,r){return [].slice.call((r||document).querySelectorAll(s))};
var money=function(n){return Math.round(n).toLocaleString('tr-TR')+' ₺'};
function start(cb){var n=0,pre=$('#pre'),num=$('#pn');function done(){pre.classList.add('off');setTimeout(function(){pre.remove()},800)}
 var iv=setInterval(function(){n=Math.min(100,n+Math.ceil(Math.random()*9));num.textContent=n;if(n>=100){clearInterval(iv);setTimeout(done,250)}},45);
 if(!(window.gsap&&window.ScrollTrigger&&window.Lenis)){pre.remove();return}
 gsap.registerPlugin(ScrollTrigger);
 if(!reduce){var lenis=new Lenis({lerp:.09,smoothWheel:true});lenis.on('scroll',ScrollTrigger.update);gsap.ticker.add(function(t){lenis.raf(t*1000)});gsap.ticker.lagSmoothing(0);window._lenis=lenis;
  $$('a[href^="#"]').forEach(function(a){a.addEventListener('click',function(e){var t=$(a.getAttribute('href'));if(t){e.preventDefault();lenis.scrollTo(t,{offset:0})}})})}
 var nav=$('nav.top');if(nav)ScrollTrigger.create({trigger:'#hero',start:'bottom 80px',end:'max',onToggle:function(t){nav.classList.toggle('solid',t.isActive)}});
 $$('.rv').forEach(function(h){if(!reduce)gsap.from(h,{y:60,opacity:0,duration:1,ease:'power3.out',scrollTrigger:{trigger:h,start:'top 88%'}})});
 cb();addEventListener('load',function(){ScrollTrigger.refresh()})}
/* video kaydırmayla: onP(progress) her güncellemede çağrılır */
function scrub(trigger,video,onP){var target=0,cur=0,dur=0;if(video){video.addEventListener('loadedmetadata',function(){dur=video.duration||0;video.pause()});if(video.readyState>0)dur=video.duration||0;video.addEventListener('error',function(){video.style.display='none'})}
 if(reduce){onP&&onP(0);return}
 ScrollTrigger.create({trigger:trigger,start:'top top',end:'bottom bottom',onUpdate:function(s){target=s.progress;onP&&onP(s.progress)}});
 gsap.ticker.add(function(){cur+=(target-cur)*.12;if(video&&dur&&Math.abs(video.currentTime-cur*dur)>.03){try{video.currentTime=cur*dur}catch(e){}}})}
return {reduce:reduce,$:$,$$:$$,money:money,start:start,scrub:scrub}})();
'''
MOB_CSS = """
.hm{display:none;width:48px;height:48px;border:1.5px solid currentColor;background:transparent;color:inherit;cursor:pointer;position:relative;margin-left:10px}
.hm i{position:absolute;left:12px;right:12px;height:2px;background:currentColor;transition:transform .3s,top .3s,opacity .3s}.hm i:nth-child(1){top:16px}.hm i:nth-child(2){top:23px}.hm i:nth-child(3){top:30px}
.hm[aria-expanded=true] i:nth-child(1){top:23px;transform:rotate(45deg)}.hm[aria-expanded=true] i:nth-child(2){opacity:0}.hm[aria-expanded=true] i:nth-child(3){top:23px;transform:rotate(-45deg)}
.mm{position:fixed;inset:0;z-index:70;background:var(--bg);color:var(--ink);display:flex;flex-direction:column;justify-content:center;gap:6px;padding:90px 28px 110px;transform:translateY(-100%);transition:transform .5s cubic-bezier(.7,0,.2,1);visibility:hidden}
.mm.on{transform:none;visibility:visible}.mm a{font:400 clamp(38px,11vw,64px)/1.1 var(--hf);text-transform:var(--mmt,none);text-decoration:none;padding:6px 0;border-bottom:1px solid var(--ln)}
.mm a:active{color:var(--ac)}.mm small{margin-top:18px;font:500 12px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--mut)}
.mb{display:none}
@media(max-width:860px){nav.top>.btn{display:none}.hm{display:inline-block;margin-left:auto}.cartbtn+.hm{margin-left:10px}body{padding-bottom:64px}nav.top{z-index:80!important}nav.top .lg{white-space:nowrap;min-width:0;font-size:clamp(15px,5vw,24px)!important;letter-spacing:.12em!important}body.mo nav.top,body.mo nav.top.solid{color:var(--ink)!important;background:transparent!important;border-color:transparent!important}body.mo nav.top .lg,body.mo nav.top .cr{color:var(--ink)!important}
.mb{display:grid;grid-template-columns:1fr 1fr 1.5fr;position:fixed;left:0;right:0;bottom:0;z-index:75;background:var(--bg);border-top:1px solid var(--ln);padding-bottom:env(safe-area-inset-bottom)}
.mb a{min-height:56px;display:grid;place-items:center;font:700 13px var(--mono);letter-spacing:.08em;text-transform:uppercase;text-decoration:none;color:var(--ink)}.mb a+a{border-left:1px solid var(--ln)}.mb a.p{background:var(--ac);color:#fff}}
footer .cl{display:grid;gap:6px}footer .cl a{color:var(--mut);font-size:14px;text-decoration:none}footer .cl a:hover{color:var(--ac)}footer .cr{grid-column:1/-1;font:500 12px var(--mono);color:var(--mut);border-top:1px solid var(--ln);padding-top:16px}
"""
MOB_JS = """
(function(){var $=function(s,r){return (r||document).querySelector(s)},$$=function(s,r){return [].slice.call((r||document).querySelectorAll(s))};var nav=$('nav.top');if(!nav)return;var ul=$('ul',nav);var items=ul?$$('a',ul):[];
 var btn=document.createElement('button');btn.className='hm';btn.type='button';btn.setAttribute('aria-label','Menüyü aç');btn.setAttribute('aria-expanded','false');btn.innerHTML='<i></i><i></i><i></i>';nav.appendChild(btn);
 var mm=document.createElement('div');mm.className='mm';mm.id='mm';mm.innerHTML=items.map(function(a){return '<a href="'+a.getAttribute('href')+'">'+a.textContent+'</a>'}).join('')+'<a href="'+MOB.cta[1]+'" style="color:var(--ac)">'+MOB.cta[0]+'</a><small>'+MOB.addr+'</small>';document.body.appendChild(mm);btn.setAttribute('aria-controls','mm');
 function set(on){btn.setAttribute('aria-expanded',on);btn.setAttribute('aria-label',on?'Menüyü kapat':'Menüyü aç');mm.classList.toggle('on',on);document.body.classList.toggle('mo',on);document.documentElement.style.overflow=on?'hidden':'';if(window._lenis){on?_lenis.stop():_lenis.start()}}
 btn.onclick=function(){set(btn.getAttribute('aria-expanded')!=='true')};$$('a',mm).forEach(function(a){a.onclick=function(){set(false)}});addEventListener('keydown',function(e){if(e.key==='Escape')set(false)});
 var bar=document.createElement('div');bar.className='mb';bar.innerHTML='<a href="tel:+905320000000">Ara</a><a href="https://wa.me/905320000000">WhatsApp</a><a class="p" href="'+MOB.cta[1]+'">'+MOB.cta[0]+'</a>';document.body.appendChild(bar);
})();
"""
def page(title, desc, fams, css, body, js, c='{}', mob=None):
    return ('<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><meta name="description" content="%s"><meta name="robots" content="noindex">'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="%s"><style>%s</style></head><body>%s'
            '<noscript><style>#pre{display:none}</style></noscript><script>const C=%s;</script><script src="../lib/gsap.min.js"></script><script src="../lib/ScrollTrigger.min.js"></script><script src="../lib/lenis.min.js"></script><script>window.MOB=%s;%s%s</script></body></html>') % (title, desc, gf(*fams), MOB_CSS + css, body, c, __import__('json').dumps(mob or {}, ensure_ascii=False), BOOT, js.replace('OK.start(function(){', 'OK.start(function(){' + MOB_JS, 1))
