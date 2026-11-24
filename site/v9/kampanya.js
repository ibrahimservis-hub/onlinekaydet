(function(){
var els=document.querySelectorAll('[data-kamp]');if(!els.length)return;
var off=0,end=0,tm=0,tries=0;
function set(k,v){document.querySelectorAll('[data-k="'+k+'"]').forEach(function(e){if(v!=null&&v!=='')e.textContent=v})}
function p2(n){return n<10?'0'+n:''+n}
function tick(){document.documentElement.toggleAttribute('data-kend',!!end);var left=end?end-(Date.now()+off):0;
 var strip=document.querySelectorAll('[data-kc]'),box=document.querySelectorAll('[data-kt]');
 if(!end){strip.forEach(function(e){e.textContent=''});box.forEach(function(e){e.hidden=true});return}
 if(left<=0){clearInterval(tm);setTimeout(load,1500);return}
 var s=Math.floor(left/1e3),d=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60),c=s%60;
 strip.forEach(function(e){e.textContent=(d?d+' gün ':'')+p2(h)+':'+p2(m)+':'+p2(c)});
 box.forEach(function(e){e.hidden=false;var v=[d,h,m,c];e.querySelectorAll('b').forEach(function(b,i){b.textContent=i?p2(v[i]):v[i]})})}
function load(){fetch('/api/public/campaign',{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(c){
 tries=0;off=c.now_ms-Date.now();end=c.end_ms||0;
 ['strip','l1','l2','em','lead','bt','bb','bs','cta'].forEach(function(k){set(k,c[{bt:'badge_top',bb:'badge_big',bs:'badge_sub'}[k]||k])});
 if(c.accent)document.documentElement.style.setProperty('--ka',c.accent);
 document.querySelectorAll('.kst2').forEach(function(s){var x;try{x=sessionStorage.getItem('kst-x')}catch(e){}if(x===String(c.id)){s.remove();return}s.querySelectorAll('a').forEach(function(a){a.href=c.always?'/demo.html':'/fiyatlar.html#paketler'});var b=s.querySelector('button');if(b)b.onclick=function(){try{sessionStorage.setItem('kst-x',String(c.id))}catch(e){}s.remove()}});
 clearInterval(tm);tick();if(end)tm=setInterval(tick,1000)}).catch(function(){if(++tries<4)setTimeout(load,5000*tries)})}
function hh(){var u=document.getElementById('ust'),k=document.querySelector('.kh');if(u&&k)k.style.setProperty('--hh',u.offsetHeight+'px')}hh();addEventListener('resize',hh);
load();
document.addEventListener('visibilitychange',function(){if(!document.hidden&&end&&end-(Date.now()+off)<=0)load()});
})();
