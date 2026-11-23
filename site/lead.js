/* Satış sayfası talep formları: tüm formları /api/public/lead'e bağlar. */
(function(){
var API=(window.OK_API||'')+'/api/public/lead';
function utm(){try{var q=new URLSearchParams(location.search),o=JSON.parse(sessionStorage.getItem('ok_src')||'{}');['utm_source','utm_medium','utm_campaign','ref'].forEach(function(k){if(q.get(k))o[k]=q.get(k)});if(!o.ref&&document.referrer)try{o.ref=new URL(document.referrer).hostname}catch(e){}sessionStorage.setItem('ok_src',JSON.stringify(o));return o}catch(e){return{}}}
window.OKLead={send:function(p){p.src=Object.assign({page:location.pathname.split('/').pop()||'/'},utm());return fetch(API,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)}).then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok)throw new Error(j.detail||'Gönderilemedi, lütfen tekrar deneyin');return j})})}};
function val(box,label){var ls=box.querySelectorAll('label');for(var i=0;i<ls.length;i++){if(ls[i].textContent.trim().toLowerCase().indexOf(label)===0){var f=ls[i].parentNode.querySelector('input,select,textarea');return f?f.value.trim():''}}return''}
function wire(box){
 if(box.dataset.w)return;box.dataset.w=1;
 var hp=document.createElement('input');hp.name='website';hp.tabIndex=-1;hp.autocomplete='off';hp.setAttribute('aria-hidden','true');hp.style.cssText='position:absolute;left:-9999px;width:1px;height:1px;opacity:0';box.appendChild(hp);
 var msg=document.createElement('div');msg.setAttribute('role','status');msg.style.cssText='grid-column:1/-1;font-weight:600;font-size:14px;margin-top:8px;min-height:0';box.appendChild(msg);
 var btn=box.querySelector('a.bt,button.bt');if(!btn)return;btn.removeAttribute('href');btn.style.cursor='pointer';
 var form=box.dataset.form||(box.closest('section')&&box.closest('section').id)||(location.pathname.split('/').pop().replace('.html','')||'ana-sayfa');
 btn.addEventListener('click',function(e){e.preventDefault();if(btn.dataset.busy)return;
  var sec=val(box,'sektör'),d={name:val(box,'ad soyad'),phone:val(box,'telefon'),firm:val(box,'firma'),sector:sec==='Seçiniz'?'':sec,form:form,website:hp.value,extra:{}};
  var us=val(box,'ustanız');if(us)d.extra.usta=us;var ms=val(box,'mesajınız');if(ms)d.extra.mesaj=ms;var tu=val(box,'türü');if(tu)d.extra.tur=tu;if(window.OK_CTX)for(var k in window.OK_CTX)d.extra[k]=window.OK_CTX[k];
  var old=btn.textContent;btn.dataset.busy=1;btn.textContent='Gönderiliyor…';msg.style.color='';msg.textContent='';
  OKLead.send(d).then(function(){msg.style.color='#0f9d58';msg.textContent='✓ Talebiniz alındı. Sizi kısa süre içinde arayacağız.';btn.textContent='Gönderildi';
   try{(window.dataLayer=window.dataLayer||[]).push({event:'lead',form:form})}catch(e){}try{window.OKTrack&&OKTrack.event('form_submit')}catch(e){}
  }).catch(function(x){msg.style.color='#b42318';msg.textContent=x.message;btn.textContent=old;delete btn.dataset.busy})
 })}
function init(){utm();document.querySelectorAll('.cb .box,.frm').forEach(function(b){if(!b.closest('.dform'))wire(b)})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
