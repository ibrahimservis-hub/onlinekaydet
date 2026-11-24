(function(){var b=document.querySelector('[data-ref]');if(!b)return;
function yap(l){var T=b.querySelector('.rft');T.textContent='';var n=l.length,rep=n<8?Math.ceil(8/n):1,set=[];for(var r=0;r<rep;r++)set=set.concat(l);
 function kart(x,gizli){var e=document.createElement(x.link?'a':'span');e.className='rfk';e.setAttribute('role','listitem');if(x.link){e.href=x.link;e.rel='noopener nofollow';e.target='_blank'}if(gizli)e.setAttribute('aria-hidden','true'),e.tabIndex=-1;
  var i=document.createElement('img');i.src=x.src;i.alt=gizli?'':x.name;i.loading='lazy';i.decoding='async';i.height=40;e.appendChild(i);return e}
 var a=document.createElement('div');a.className='rfg';set.forEach(function(x){a.appendChild(kart(x,false))});
 var c=a.cloneNode(false);c.setAttribute('aria-hidden','true');set.forEach(function(x){c.appendChild(kart(x,true))});
 T.appendChild(a);T.appendChild(c);T.style.setProperty('--rfs',Math.max(24,set.length*4.2)+'s');b.hidden=false}
fetch('/api/public/referanslar',{cache:'no-cache'}).then(function(r){return r.ok?r.json():null}).then(function(j){if(j&&j.logolar&&j.logolar.length)yap(j.logolar)}).catch(function(){})})();
