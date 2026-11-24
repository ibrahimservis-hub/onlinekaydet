/* Kariyer sayfası: açık pozisyonlar API'den gelir; başvuru formu CV ile birlikte gönderilir. */
(function(){
var API=(window.OK_API||'')+'/api/public/kariyer',box=document.getElementById('kz-jobs'),fl=document.getElementById('kz-fl'),dlg=document.getElementById('kz-dlg');
if(!box)return;
var ALL=[],cur='Tümü';
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
function liste(a){var u=el('ul');a.forEach(function(x){u.appendChild(el('li',0,x))});return u}
function ciz(){box.textContent='';var rows=ALL.filter(function(i){return cur==='Tümü'||i.dept===cur});
 if(!rows.length){box.appendChild(el('p','kzl','Bu bölümde şu an açık pozisyon yok. Genel başvuru yapabilirsiniz.'));return}
 rows.forEach(function(i){var d=el('details','kzjob'),s=el('summary'),l=el('div'),tg=el('div','tg');
  l.appendChild(el('h3',0,i.title));[i.dept,i.type,i.city].forEach(function(x){if(x)tg.appendChild(el('span',0,x))});l.appendChild(tg);
  s.appendChild(l);s.appendChild(el('span','ac','Ayrıntı'));d.appendChild(s);
  var b=el('div','kzjd');if(i.summary)b.appendChild(el('p',0,i.summary));
  if((i.duties||[]).length){var a=el('div');a.appendChild(el('h4',0,'Neler yapacaksınız'));a.appendChild(liste(i.duties));b.appendChild(a)}
  if((i.reqs||[]).length){var r=el('div');r.appendChild(el('h4',0,'Aradığımız nitelikler'));r.appendChild(liste(i.reqs));b.appendChild(r)}
  var bt=el('button','kzbtn p','Bu pozisyona başvurun');bt.type='button';bt.onclick=function(){ac(i)};b.appendChild(bt);d.appendChild(b);box.appendChild(d)})}
function filtre(){fl.textContent='';var ds=['Tümü'];ALL.forEach(function(i){if(i.dept&&ds.indexOf(i.dept)<0)ds.push(i.dept)});
 if(ds.length<3)return;ds.forEach(function(x){var b=el('button',0,x);b.type='button';b.setAttribute('aria-pressed',x===cur?'true':'false');b.onclick=function(){cur=x;filtre();ciz()};fl.appendChild(b)})}
function ac(i){var f=dlg.querySelector('form');f.reset();f.hidden=false;dlg.querySelector('.kzok').hidden=true;dlg.querySelector('.er').style.display='none';
 f.elements.ilan.value=i?i.id:'genel';dlg.querySelector('#kz-ilan').textContent=i?i.title:'Genel başvuru';
 if(dlg.showModal)dlg.showModal();else dlg.setAttribute('open','')}
document.querySelectorAll('[data-genel]').forEach(function(b){b.onclick=function(){ac(null)}});
dlg.querySelector('[data-kapat]').onclick=function(){dlg.close?dlg.close():dlg.removeAttribute('open')};
dlg.querySelector('.kzok button').onclick=function(){dlg.close?dlg.close():dlg.removeAttribute('open')};
var form=dlg.querySelector('form');
form.onsubmit=function(e){e.preventDefault();var er=dlg.querySelector('.er'),bt=form.querySelector('[type=submit]');er.style.display='none';
 var cv=form.elements.cv.files[0];if(cv&&cv.size>5*1024*1024){er.textContent='Özgeçmiş en fazla 5 MB olabilir.';er.style.display='block';return}
 if(!form.elements.kvkk.checked){er.textContent='Başvuru için aydınlatma metnini onaylayın.';er.style.display='block';return}
 bt.disabled=true;bt.textContent='Gönderiliyor…';
 fetch(API+'/basvuru',{method:'POST',body:new FormData(form)}).then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok)throw new Error(j.detail||'Gönderilemedi');return j})})
 .then(function(){form.hidden=true;dlg.querySelector('.kzok').hidden=false;try{window.OKTrack&&OKTrack.event('career_apply')}catch(x){}})
 .catch(function(x){er.textContent=x.message||'Gönderilemedi, tekrar deneyin.';er.style.display='block'})
 .then(function(){bt.disabled=false;bt.textContent='Başvuruyu gönderin'})};
fetch(API,{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(j){ALL=j.ilanlar||[];filtre();ciz()})
 .catch(function(){box.textContent='';box.appendChild(el('p','kzl','Pozisyonlar şu an yüklenemedi. Aşağıdaki genel başvuru formunu kullanabilirsiniz.'))});
})();
