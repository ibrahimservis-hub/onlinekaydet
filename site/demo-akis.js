/* Canlı demo formu: sektör seç, (SMS açıksa) telefon kodunu doğrula, örnek verili demo hesabını aç. */
(function(){
var box=document.querySelector('.dform .frm');if(!box)return;
var btn0=box.querySelector('a.bt'),btn=btn0.cloneNode(true);btn0.parentNode.replaceChild(btn,btn0);var $=function(i){return document.getElementById(i)};
var msg=document.createElement('div');msg.setAttribute('role','status');msg.style.cssText='grid-column:1/-1;font-weight:600;font-size:14px;margin-top:8px';box.appendChild(msg);
var hp=document.createElement('input');hp.name='website';hp.tabIndex=-1;hp.autocomplete='off';hp.setAttribute('aria-hidden','true');hp.style.cssText='position:absolute;left:-9999px;width:1px;height:1px;opacity:0';box.appendChild(hp);
var sel=document.createElement('div');sel.innerHTML='<label for="d4">Sektör</label><select id="d4"><option value="">Seçiniz</option></select>';box.insertBefore(sel,btn);
var kod=document.createElement('div');kod.hidden=true;kod.innerHTML='<label for="d5">SMS doğrulama kodu</label><input id="d5" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="6 haneli kod">';box.insertBefore(kod,btn);
var need=false,sent=false;
function api(path,opt){return fetch('/api/public/'+path,opt).then(function(r){return r.json().catch(function(){return {}}).then(function(j){if(!r.ok)throw new Error(typeof j.detail==='string'?j.detail:'İşlem yapılamadı, lütfen tekrar deneyin.');return j})})}
function post(path,b){b.website=hp.value;return api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)})}
api('demo/ayar').then(function(a){need=!!a.kod;var s=$('d4');(a.sektorler||[]).forEach(function(x){var o=document.createElement('option');o.value=x.k;o.textContent=x.ad;s.appendChild(o)})}).catch(function(){});
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function done(d){
 fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:d.email,password:d.password})}).then(function(r){return r.json()}).catch(function(){return {}}).then(function(l){
  var tok=l&&l.token,pn=d.panel||'/salon',f=document.querySelector('.dform');
  var url=location.origin+pn;
  function row(t,v){return '<div class="dsat"><b>'+t+'</b><div class="dsv"><code>'+esc(v)+'</code><button type="button" class="dkop" data-v="'+esc(v)+'">Kopyala</button></div></div>'}
  f.innerHTML='<h2>Demo hesabınız hazır</h2><p>'+d.days+' gün boyunca açık. Örnek müşteri, usta ve kayıtlar yüklendi.</p><div class="dcred">'+row('Panel adresi',url)+row('Kullanıcı adı',d.email)+row('Şifre',d.password)+row('Usta uygulaması kullanıcı adı (aynı şifre)',d.tech_email)+'</div><button type="button" class="dkop dhep" data-v="Panel: '+esc(url)+'\nKullanıcı adı: '+esc(d.email)+'\nŞifre: '+esc(d.password)+'\nUsta kullanıcı adı: '+esc(d.tech_email)+'">Tüm bilgileri kopyala</button><p style="margin:12px 0 0;font-size:13px">Demoda tüm özellikler açıktır. Demo verilerinizi isterseniz koruyabilirsiniz.</p><a class="bt" id="dgopanel" href="'+pn+'">Panele gir</a>';
  f.addEventListener('click',function(ev){var k=ev.target.closest&&ev.target.closest('.dkop');if(!k)return;var v=k.getAttribute('data-v'),old=k.textContent;
   function ok(){k.textContent='Kopyalandı';k.classList.add('ok');setTimeout(function(){k.textContent=old;k.classList.remove('ok')},1600)}
   function fb(){var t=document.createElement('textarea');t.value=v;t.style.cssText='position:fixed;left:-9999px';document.body.appendChild(t);t.select();try{document.execCommand('copy');ok()}catch(e){}document.body.removeChild(t)}
   if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(v).then(ok,fb);else fb()});
  try{window.OKTrack&&OKTrack.event('form_submit')}catch(e){}
  if(tok)$('dgopanel').addEventListener('click',function(ev){ev.preventDefault();try{localStorage.setItem('token',tok);localStorage.removeItem('spx_firm');if(pn==='/salon')localStorage.setItem('ypt',tok)}catch(x){}location.href=pn+(pn==='/salon'?'#bugun':'')})
 })}
btn.removeAttribute('href');btn.style.cursor='pointer';
btn.addEventListener('click',function(e){e.preventDefault();if(btn.dataset.busy)return;
 var n=$('d1').value.trim(),p=$('d2').value.trim(),s=$('d4').value;
 msg.style.color='#b42318';
 if(n.length<2){msg.textContent='Lütfen adınızı yazın.';return}
 if(p.replace(/\D/g,'').length<10){msg.textContent='Telefon numarasını 05xx xxx xx xx biçiminde yazın.';return}
 if(!s){msg.textContent='Lütfen sektörünüzü seçin.';return}
 var old=btn.textContent;btn.dataset.busy=1;msg.textContent='';
 function fin(){delete btn.dataset.busy}
 if(need&&!sent){btn.textContent='Kod gönderiliyor…';
  post('demo/kod',{phone:p}).then(function(){sent=true;kod.hidden=false;$('d5').focus();msg.style.color='#0f9d58';msg.textContent='Telefonunuza 6 haneli kod gönderdik. Kodu girip demoyu açın.';btn.textContent='Kodu doğrula ve demoyu aç';fin()}).catch(function(x){msg.textContent=x.message;btn.textContent=old;fin()});return}
 btn.textContent='Hesabınız açılıyor…';msg.style.color='#1a4fb8';msg.textContent='Lütfen bekleyin, demo hesabınız açılıyor. Bu işlem birkaç saniye sürer, sayfayı kapatmayın.';
 post('demo',{name:n,phone:p,sector:s,firm:$('d3').value.trim(),code:need?$('d5').value.trim():''}).then(done).catch(function(x){msg.textContent=x.message;btn.textContent=need?'Kodu doğrula ve demoyu aç':old;fin()})
})})();
