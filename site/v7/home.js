(function(){
var tabs=document.querySelectorAll('[role=tab]'),pans=document.querySelectorAll('.pkp');
function pick(n){tabs.forEach(function(t,i){t.setAttribute('aria-selected',i===n)});pans.forEach(function(p,i){p.hidden=i!==n;if(i===n){p.style.animation='none';p.offsetHeight;p.style.animation='fade .5s var(--ease) both'}})}
tabs.forEach(function(t,i){t.addEventListener('click',function(){pick(i)});t.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key==='ArrowLeft'){var n=(i+(e.key==='ArrowRight'?1:tabs.length-1))%tabs.length;pick(n);tabs[n].focus()}})});
pick(1);
var feed=document.getElementById('feed');
var E=[["12:41","<b>Kemal</b> yola çıktı, müşteriye takip bağlantısı gitti."],["12:46","Yeni talep: <b>Karşıyaka</b>, kombi arıza. <i>Kayıt açıldı.</i>"],["12:47","Otomatik atama: <b>Hasan</b> seçildi."],["12:58","<b>Emre</b> işe başladı, öncesi fotoğraf eklendi."],["13:09","<b>Selin</b> keşfi tamamladı, teklif hazır."],["13:15","Müşteri onayı geldi: <b>Bornova</b>, klima bakımı."],["13:22","<b>Hasan</b> kapattı. <i>1.350 ₺ tahsil edildi.</i>"],["13:30","Yıllık bakımı yaklaşan <b>9 müşteri</b> için hatırlatma gitti."]];
var i=0;
function add(){var d=document.createElement('div');d.className='ev';d.innerHTML='<time>'+E[i%E.length][0]+'</time><span>'+E[i%E.length][1]+'</span>';feed.insertBefore(d,feed.firstChild);while(feed.children.length>6)feed.removeChild(feed.lastChild);i++}
for(var j=0;j<4;j++)add();
if(!matchMedia('(prefers-reduced-motion:reduce)').matches){
 var run=false,ob=new IntersectionObserver(function(e){if(e[0].isIntersecting&&!run){run=true;setInterval(function(){add();if(i%3===0){var k=document.getElementById('k1');k.textContent=String(+k.textContent+1)}},2600)}},{threshold:.3});ob.observe(document.getElementById('con'));
}
})();
