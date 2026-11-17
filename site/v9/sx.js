(function(){document.querySelectorAll('.sxdemo').forEach(function(d){var n=+d.dataset.n,i=0,bs=d.querySelectorAll('.sxd-st button'),bar=d.querySelector('.sxd-bar i'),dd=d.querySelector('.sxd-d'),cks=d.querySelectorAll('.sxck input'),s=d.querySelector('.sxd-s');
function set(k){i=Math.max(0,Math.min(n-1,k));bs.forEach(function(b,j){b.className=j<i?'ok':j==i?'on':''});bar.style.width=((i+1)/n*100)+'%';dd.textContent=bs[i].textContent}
function cnt(){var c=0;cks.forEach(function(x){if(x.checked)c++});s.textContent=c+' / '+cks.length+' tamam'}
bs.forEach(function(b,j){b.addEventListener('click',function(){set(j)})});
d.querySelector('[data-a=n]').addEventListener('click',function(){set(i+1)});d.querySelector('[data-a=p]').addEventListener('click',function(){set(i-1)});
cks.forEach(function(x){x.addEventListener('change',cnt)});set(0);cnt()})})();
