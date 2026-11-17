/* Site içi arama: /v9/arama.json dizinini tarayıcıda tarar. Türkçe harf farkı gözetmez (ğ=g, ı=i ...). */
(function(){var d=document,IDX=null,YUK=null;
function nz(s){return String(s||'').replace(/İ/g,'i').replace(/I/g,'ı').toLowerCase().replace(/ı/g,'i').replace(/ç/g,'c').replace(/ğ/g,'g').replace(/ö/g,'o').replace(/ş/g,'s').replace(/ü/g,'u')}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function yukle(){if(YUK)return YUK;YUK=fetch('/v9/arama.json').then(function(r){return r.json()}).then(function(a){a.forEach(function(x){x.nt=nz(x.t);x.nd=nz(x.d);x.nh=nz(x.h.join(' | '));x.nx=nz(x.x);x.nk=nz(x.k)});IDX=a;return a}).catch(function(){IDX=[];return []});return YUK}
function ara(q){var T=nz(q).split(/\s+/).filter(function(x){return x.length>1});if(!T.length||!IDX)return[];
 var R=[];IDX.forEach(function(x){var s=0,ok=0;T.forEach(function(w){var p=0;if(x.nt.indexOf(w)>-1)p+=12;if(x.nk.indexOf(w)>-1)p+=7;if(x.nh.indexOf(w)>-1)p+=6;if(x.nd.indexOf(w)>-1)p+=4;if(x.nx.indexOf(w)>-1)p+=1+Math.min(3,(x.nx.split(w).length-1)*.3);if(p){ok++;s+=p}});
  if(!ok)return;if(ok===T.length)s+=15;var ph=T.join(' ');if(T.length>1&&x.nt.indexOf(ph)>-1)s+=20;if(/^\/bilgi-/.test(x.u))s+=2;R.push({x:x,s:s,all:ok===T.length})});
 R.sort(function(a,b){return b.s-a.s});var tam=R.filter(function(r){return r.all});return tam.length?tam:R}
function parca(x,q){var T=nz(q).split(/\s+/).filter(function(w){return w.length>1});var i=-1;for(var k=0;k<T.length&&i<0;k++)i=x.nx.indexOf(T[k]);var m=x.x;if(i<0)return esc(x.d||m.slice(0,150));var a=Math.max(0,i-60),z=Math.min(m.length,i+120);var t=(a?'…':'')+m.slice(a,z)+(z<m.length?'…':'');t=esc(t);
 T.forEach(function(w){var nt=nz(t),o='',p=0,j;while((j=nt.indexOf(w,p))>-1){o+=t.slice(p,j)+'<mark>'+t.slice(j,j+w.length)+'</mark>';p=j+w.length}t=o+t.slice(p)});return t}
function kart(r,q){var x=r.x;return '<a class="arasn-k" href="'+esc(x.u)+'"><b>'+esc(x.t)+'</b><span class="aru">'+esc(x.u)+'</span><p>'+parca(x,q)+'</p></a>'}
function ciz(kap,q,max,tum){var h='';if(!q||nz(q).trim().length<2){kap.innerHTML='';return}
 var R=ara(q);if(!R.length){kap.innerHTML='<p class="arayok">“'+esc(q)+'” için sonuç bulunamadı. Farklı bir sözcük deneyin ya da <a href="/iletisim.html">bize yazın</a>.</p>';return}
 R.slice(0,max).forEach(function(r){h+=kart(r,q)});if(tum&&R.length>max)h+='<a class="arahep" href="/ara.html?q='+encodeURIComponent(q)+'">Tüm '+R.length+' sonucu gör</a>';
 kap.innerHTML=(tum?'':'')+h}
var ov=d.getElementById('arap');
function ac(){if(!ov)return;ov.hidden=false;d.body.classList.add('kilit');var g=d.getElementById('arag');yukle().then(function(){var v=g.value;if(v)ciz(d.getElementById('arasn'),v,6,true)});setTimeout(function(){g.focus()},30);var sk=d.getElementById('arasik');if(sk&&!sk.children.length){['Ürün ekleme','Pazaryerine gönderme','Randevu','Kasa','Sipariş','İlan','Fiyatlar'].forEach(function(t){var a=d.createElement('a');a.href='#';a.textContent=t;a.addEventListener('click',function(e){e.preventDefault();g.value=t;g.dispatchEvent(new Event('input'))});sk.appendChild(a)})}}
function kapat(){if(!ov)return;ov.hidden=true;d.body.classList.remove('kilit')}
d.addEventListener('click',function(e){if(e.target.closest('[data-ara]')){e.preventDefault();ac()}else if(e.target.closest('[data-arakapat]')||e.target===ov)kapat()});
d.addEventListener('keydown',function(e){if(e.key==='Escape'&&ov&&!ov.hidden)kapat();if((e.key==='/'||(e.key==='k'&&(e.ctrlKey||e.metaKey)))&&!/INPUT|TEXTAREA|SELECT/.test((d.activeElement||{}).tagName)){e.preventDefault();ac()}});
var g=d.getElementById('arag');if(g){g.addEventListener('input',function(){yukle().then(function(){ciz(d.getElementById('arasn'),g.value,6,true)})})}
// tam sayfa
var sy=d.getElementById('arasy'),so=d.getElementById('arasonuc');
if(sy&&so){var q=new URLSearchParams(location.search).get('q')||'';sy.value=q;yukle().then(function(){ciz(so,q,40,false);var f=function(){ciz(so,sy.value,40,false);try{history.replaceState(null,'','?q='+encodeURIComponent(sy.value))}catch(e){}};sy.addEventListener('input',f)});
 var sk2=d.getElementById('arasik2');if(sk2)sk2.addEventListener('click',function(e){var a=e.target.closest('a');if(!a)return;e.preventDefault();sy.value=a.textContent;sy.dispatchEvent(new Event('input'))})}
})();
