/* Fiyatlar sayfası: ad, fiyat, açıklama ve maddeler yönetimde düzenlenen paketlerden gelir (sunucudan, anlık). */
(function(){
var cards=document.querySelectorAll('.pks .pk');if(!cards.length||!window.fetch)return;
function tl(n){return Math.round(n).toLocaleString('tr-TR')}
fetch((window.OK_API||'')+'/api/public/packages',{cache:'no-store'}).then(function(r){return r.ok?r.json():null}).then(function(j){
 if(!j||!j.packages||!j.packages.length)return;
 j.packages.forEach(function(p,i){var c=cards[i];if(!c)return;
  var h=c.querySelector('.ph h3');if(h&&p.name)h.textContent=p.name;
  var m=c.querySelector('.ph span');if(m&&p.modules)m.textContent=p.modules+' modül';
  var k=c.querySelector('.kim');if(k&&p.tagline)k.textContent=p.tagline;
  if(p.price>0){var b=c.querySelector('.fy b');if(b)b.textContent=tl(p.price);
   var y=c.querySelector('.yil');if(y&&p.yearly>0)y.textContent='Yıllık ödemede '+tl(p.yearly)+' ₺'}
  var ul=c.querySelector('ul');if(ul&&p.features&&p.features.length){ul.innerHTML='';p.features.forEach(function(f){var li=document.createElement('li');li.textContent=f;ul.appendChild(li)})}
 })}).catch(function(){})
})();
