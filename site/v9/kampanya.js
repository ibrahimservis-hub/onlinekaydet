(function(){
var els=document.querySelectorAll('[data-kamp]');if(!els.length)return;
var off=0,end=0,tm=0,tries=0;
function set(k,v){document.querySelectorAll('[data-k="'+k+'"]').forEach(function(e){if(v!=null&&v!=='')e.textContent=v})}
var KEYS=['strip','l1','l2','em','lead','bt','bb','bs','cta'],MAP={bt:'badge_top',bb:'badge_big',bs:'badge_sub'};
function ready(){document.documentElement.setAttribute('data-kok','1')}
function paint(c){KEYS.forEach(function(k){set(k,c[MAP[k]||k])});if(c.accent)document.documentElement.style.setProperty('--ka',c.accent)}
try{var cc=JSON.parse(localStorage.getItem('kamp-c')||'null');if(cc&&cc.strip&&!cc.always){end=cc.end_ms||0;off=0;paint(cc);build(cc);ready();document.documentElement.setAttribute('data-kon','1');tick();if(end)tm=setInterval(tick,1000)}}catch(e){}
setTimeout(ready,1200);
var st=document.createElement('style');st.id='kb-css';st.textContent='.kst.kb,.kst2.kb{display:block;background:linear-gradient(90deg,var(--ka,#2f6fe0) 0%,#0b1220 58%,#000 100%);color:#fff;border:0;padding:0;position:relative;z-index:51}\n.kb .kb-in{display:flex!important;max-width:1240px;margin:0 auto;padding:9px 46px 9px 18px;min-height:64px;box-sizing:border-box;display:flex;align-items:center;justify-content:space-between;gap:14px;color:#fff;text-decoration:none}\n.kb .kb-x{display:flex;flex-direction:column;gap:5px;min-width:0;font:500 12.5px/1.25 var(--fb,system-ui);text-align:left}\n.kb .kb-x b{font:700 12.5px/1.2 var(--fb,system-ui);background:none;border:0;padding:0;color:#fff}\n.kb .kb-x span{font-weight:500;color:#fff}\n.kb .kb-t{flex:none;display:flex;gap:16px;align-items:flex-end}\n.kb .kb-t[hidden]{display:none}\n.kb .kb-t div{display:flex;flex-direction:column;align-items:center;gap:1px;min-width:34px}\n.kb .kb-t b{font:700 22px/1 var(--fb,system-ui);font-variant-numeric:tabular-nums;color:#fff;background:none;border:0;padding:0;letter-spacing:-.01em}\n.kb .kb-t small{font:500 10px/1.1 var(--fb,system-ui);text-transform:uppercase;letter-spacing:.02em;color:#fff;opacity:.92}\n.kb .kb-in:focus-visible{outline:2px solid #fff;outline-offset:-4px}\n.kst2.kb button{position:absolute;right:8px;top:8px;translate:none;width:28px;height:28px;background:transparent;color:#ffffffb3}\n@media(min-width:900px){.kb .kb-in{justify-content:center;gap:44px;min-height:72px}.kb .kb-x{flex-direction:row;align-items:baseline;gap:12px;font-size:16px}.kb .kb-x b{font-size:18px}.kb .kb-t b{font-size:26px}.kb .kb-t small{font-size:11px}.kb .kb-t{gap:20px}.kb .kb-t div{min-width:44px}}\n@media(max-width:390px){.kb .kb-in{padding-left:12px;gap:8px}.kb .kb-t{gap:10px}.kb .kb-t div{min-width:30px}.kb .kb-t b{font-size:19px}.kb .kb-x,.kb .kb-x b{font-size:12px}}\n@media(prefers-reduced-motion:no-preference){.kb .kb-t b{transition:opacity .15s}}\n';document.head.appendChild(st);
function build(c){if(!c||c.always)return;var pp=String(c.strip||'').split(/:\s+/),a=pp.length>1?pp.shift():'',b=pp.join(': ')||String(c.strip||'');
 document.querySelectorAll('.kst,.kst2').forEach(function(s){var in2=s.classList.contains('kst2')?s.querySelector('.in'):s;if(!in2)return;
  var h=document.createElement('a');h.className='kb-in';h.href='/fiyatlar.html#paketler';
  var x=document.createElement('span');x.className='kb-x';if(a){var b1=document.createElement('b');b1.textContent=a;x.appendChild(b1)}var s2=document.createElement('span');s2.textContent=b;x.appendChild(s2);h.appendChild(x);
  var t=document.createElement('span');t.className='kb-t';t.setAttribute('data-kt','');t.hidden=!end;['gün','saat','dakika','saniye'].forEach(function(l){var d=document.createElement('div'),n=document.createElement('b'),m=document.createElement('small');n.textContent='0';m.textContent=l;d.appendChild(n);d.appendChild(m);t.appendChild(d)});h.appendChild(t);
  while(in2.firstChild)in2.removeChild(in2.firstChild);in2.appendChild(h);s.classList.add('kb');if(in2!==s){in2.style.cssText='padding:0;min-height:0;display:block;max-width:none'}
  var bt=s.querySelector('button');if(bt&&s.classList.contains('kst2')&&bt.parentNode!==s)s.appendChild(bt)})}
function p2(n){return n<10?'0'+n:''+n}
function tick(){document.documentElement.toggleAttribute('data-kend',!!end);var left=end?end-(Date.now()+off):0;
 var strip=document.querySelectorAll('[data-kc]'),box=document.querySelectorAll('[data-kt]');
 if(!end){strip.forEach(function(e){e.textContent=''});box.forEach(function(e){e.hidden=true});return}
 if(left<=0){clearInterval(tm);setTimeout(load,1500);return}
 var s=Math.floor(left/1e3),d=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60),c=s%60;
 strip.forEach(function(e){e.textContent=(d?d+' gün ':'')+p2(h)+':'+p2(m)+':'+p2(c)});
 box.forEach(function(e){e.hidden=false;var v=[d,h,m,c];e.querySelectorAll('b').forEach(function(b,i){b.textContent=i?p2(v[i]):v[i]})})}
function load(){fetch('/api/public/campaign',{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(c){
 tries=0;off=c.now_ms-Date.now();end=c.end_ms||0;try{localStorage.setItem('kamp-c',JSON.stringify(c))}catch(e){}
 paint(c);build(c);ready();
 if(c.always){document.documentElement.removeAttribute('data-kon');document.querySelectorAll('.kst,.kst2').forEach(function(s){s.remove()})}else document.documentElement.setAttribute('data-kon','1');
 document.querySelectorAll('.kst2').forEach(function(s){var x;try{x=sessionStorage.getItem('kst-x')}catch(e){}if(x===String(c.id)){s.remove();return}s.querySelectorAll('a').forEach(function(a){a.href=c.always?'/demo.html':'/fiyatlar.html#paketler'});var b=s.querySelector('button');if(b)b.onclick=function(){try{sessionStorage.setItem('kst-x',String(c.id))}catch(e){}s.remove()}});
 clearInterval(tm);tick();if(end)tm=setInterval(tick,1000)}).catch(function(){if(++tries<4)setTimeout(load,5000*tries);else ready()})}
function hh(){var u=document.getElementById('ust'),k=document.querySelector('.kh');if(u&&k)k.style.setProperty('--hh',u.getBoundingClientRect().height+'px')}hh();addEventListener('resize',hh);addEventListener('load',hh);if(window.ResizeObserver){var u0=document.getElementById('ust');if(u0)new ResizeObserver(hh).observe(u0)}if(document.fonts&&document.fonts.ready)document.fonts.ready.then(hh);
load();
document.addEventListener('visibilitychange',function(){if(!document.hidden&&end&&end-(Date.now()+off)<=0)load()});
})();
