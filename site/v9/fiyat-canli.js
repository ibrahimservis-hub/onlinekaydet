(function(){var cards=document.querySelectorAll('.pks .pk');if(!cards.length)return;
function f(n){n=Math.round(n*100)/100;return n.toLocaleString('tr-TR',{minimumFractionDigits:n%1?2:0,maximumFractionDigits:2})}
fetch('/api/public/satin-al/paketler',{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(d){
 var map={};d.paketler.forEach(function(p){map[p.name]=p});
 cards.forEach(function(c){var h=c.querySelector('h3'),p=h&&map[h.textContent.trim()];if(!p)return;
  var fy=c.querySelector('.fy'),yl=c.querySelector('.yil');
  if(fy){fy.querySelector('b').textContent=f(p.yillik.toplam);fy.querySelector('span').textContent='₺ / yıl · KDV dahil'}
  if(yl){yl.textContent='Aylık '+f(p.yillik.toplam/12)+' ₺\'ye denk gelir. 2 yıllık alımda '+f(p.iki_yil.toplam)+' ₺'+(d.hediye?' ve +1 yıl hediye.':'.')}
  if(!c.querySelector('a.al')){var a=document.createElement('a');a.className='al';a.href='/satin-al.html?paket='+encodeURIComponent(p.id);a.textContent='Satın alın';c.appendChild(a)}
  c.classList.add('canli')});
 document.documentElement.setAttribute('data-fiyat','1')}).catch(function(){
 cards.forEach(function(c){var fy=c.querySelector('.fy'),yl=c.querySelector('.yil');if(fy)fy.innerHTML='<b style="font-size:22px">Güncel fiyat</b><span>için paketlere bakın</span>';if(yl)yl.textContent='En az 1 yıllık paket, KDV dahil.'})})
})();
