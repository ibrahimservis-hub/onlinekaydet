/* Çerez onay bandı: tercih yalnızca bu tarayıcıda (localStorage) saklanır. Onaydan önce ölçüm ve reklam etiketi yüklenmez. */
(function(){
var K='ok_cerez',AY=12,kutu=null;
function oku(){try{var c=JSON.parse(localStorage.getItem(K)||'null');if(c&&Date.now()-c.t<AY*2592e6)return c}catch(e){}return null}
function yaz(o){o.t=Date.now();try{localStorage.setItem(K,JSON.stringify(o))}catch(e){}
 try{document.dispatchEvent(new CustomEvent('ok-cerez',{detail:o}))}catch(e){}}
window.okCerez={izin:function(k){var c=oku();return !!(c&&c[k])},ac:function(){goster(true)}};
function kapat(){if(kutu){kutu.remove();kutu=null}document.documentElement.removeAttribute('data-cerez')}
function sec(o){yaz(o);kapat()}
function goster(zorla){
 if(kutu)return;if(!zorla&&oku())return;var c=oku()||{};
 kutu=document.createElement('div');kutu.className='ckb';kutu.setAttribute('role','dialog');kutu.setAttribute('aria-label','Çerez tercihleri');kutu.setAttribute('aria-live','polite');
 kutu.innerHTML='<div class="ckb-i"><div class="ckb-t"><b>Çerez tercihleriniz</b><p>Sitenin çalışması için zorunlu çerezleri kullanırız. İzin verirseniz ziyaretleri anonim olarak ölçer ve reklam etiketlerini yükleriz. Tercihinizi dilediğiniz zaman değiştirebilirsiniz. <a href="/cerez-politikasi.html">Çerez politikası</a></p></div>'
 +'<div class="ckb-p" hidden><label><input type="checkbox" checked disabled> Zorunlu <small>Oturum ve güvenlik; kapatılamaz</small></label><label><input type="checkbox" id="ck-o"> İstatistik <small>Anonim ziyaret ölçümü</small></label><label><input type="checkbox" id="ck-p"> Pazarlama <small>Reklam ve dönüşüm etiketleri</small></label></div>'
 +'<div class="ckb-b"><button type="button" class="ckb-k" data-ck="hepsi">Kabul et</button><button type="button" class="ckb-r" data-ck="red">Yalnız zorunlu</button><button type="button" class="ckb-s" data-ck="tercih" aria-expanded="false">Tercihleri seç</button></div></div>';
 document.body.appendChild(kutu);document.documentElement.setAttribute('data-cerez','1');
 kutu.querySelector('#ck-o').checked=!!c.olcum;kutu.querySelector('#ck-p').checked=!!c.pazarlama;
 kutu.addEventListener('click',function(e){var b=e.target.closest('[data-ck]');if(!b)return;var a=b.dataset.ck;
  if(a==='hepsi')sec({olcum:true,pazarlama:true});
  else if(a==='red')sec({olcum:false,pazarlama:false});
  else if(a==='tercih'){var p=kutu.querySelector('.ckb-p');if(p.hidden){p.hidden=false;b.textContent='Seçimi kaydet';b.setAttribute('aria-expanded','true');b.classList.add('ckb-k')}else sec({olcum:kutu.querySelector('#ck-o').checked,pazarlama:kutu.querySelector('#ck-p').checked})}});
}
function basla(){goster(false)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',basla);else basla();
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('[data-cerez-ac]');if(a){e.preventDefault();goster(true)}});
})();
