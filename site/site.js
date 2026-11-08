/* Ortak küçük davranışlar: üst bar gölgesi, telefon doğrulama (lead.js'ten önce çalışır) */
(function(){
var h=document.querySelector('header');
if(h){var f=function(){h.classList.toggle('sc',window.scrollY>8)};addEventListener('scroll',f,{passive:true});f()}
function digits(v){return (v||'').replace(/\D/g,'')}
document.addEventListener('click',function(e){
 var b=e.target.closest&&e.target.closest('.frm a.bt,.frm button.bt');if(!b)return;
 var box=b.closest('.frm');var tel=box.querySelector('input[type=tel]');if(!tel)return;
 var d=digits(tel.value),ok=d.length>=10&&d.length<=13;
 var nm=box.querySelector('input[autocomplete=name]');
 var msg=box.querySelector('[data-v]');
 if(!msg){msg=document.createElement('div');msg.setAttribute('data-v','');msg.setAttribute('role','alert');msg.style.cssText='grid-column:1/-1;font-weight:700;font-size:14px;color:#b42318';box.insertBefore(msg,b)}
 if(!ok||(nm&&!nm.value.trim())){
  e.preventDefault();e.stopImmediatePropagation();
  msg.textContent=(nm&&!nm.value.trim())?'Lütfen adınızı yazın.':'Lütfen geçerli bir telefon numarası yazın (ör. 0544 444 40 04).';
  tel.setAttribute('aria-invalid',!ok);(nm&&!nm.value.trim()?nm:tel).focus();
 }else{msg.textContent='';tel.removeAttribute('aria-invalid')}
},true);
})();
