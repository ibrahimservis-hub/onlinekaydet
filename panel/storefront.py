# -*- coding: utf-8 -*-
"""Yayındaki firma sitesinde gerçek mağaza (/magaza) ve müşteri paneli (/hesabim).

Sayfalar temadan bağımsızdır: sitenin kendi üst/alt bilgisi ve renkleriyle (compose_page) açılır, böylece firmanın logosu,
adı ve iletişim bilgileri otomatik görünür. Ürün, stok, ödeme yöntemi ve yasal metinler /api/public/shop/* ve
/api/public/customer/* uçlarından canlı gelir. Hiçbir yerde platform adı geçmez."""

CSS = r"""<style>
.okm{--c:var(--ac,var(--a,#0a1f44));--k:var(--ink,#0f172a);--m:var(--mut,#64748b);--l:var(--ln,#e2e8f0);--s:var(--sf,#f8fafc);--w:var(--fbg,#fff);--rr:var(--r,10px);font-family:var(--fb,inherit);color:var(--k);padding:clamp(96px,11vw,132px) 0 clamp(32px,4vw,56px)}
.okm *{box-sizing:border-box}.okm h1{font:800 clamp(1.5rem,3vw,2.2rem)/1.15 var(--fd,inherit);margin:0 0 6px}.okm .sub{color:var(--m);margin:0 0 18px}
.okm a{color:inherit}.okm .bt{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;padding:0 18px;border-radius:var(--rr);border:1px solid var(--c);background:var(--c);color:#fff;font:700 .92rem var(--fb,inherit);cursor:pointer;text-decoration:none}
.okm .bt.o{background:transparent;color:var(--k);border-color:var(--l)}.okm .bt:disabled{opacity:.55;cursor:not-allowed}.okm .bt.sm{min-height:36px;padding:0 12px;font-size:.84rem}.okm .bt.d{background:#b91c1c;border-color:#b91c1c}
.okm input,.okm select,.okm textarea{width:100%;min-height:44px;padding:9px 12px;border:1px solid var(--l);border-radius:var(--rr);background:var(--w);color:var(--k);font:500 .95rem var(--fb,inherit)}.okm label{display:block;font:700 .8rem var(--fb,inherit);margin-bottom:5px;color:var(--k)}
.okm .top{display:flex;gap:12px;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;margin-bottom:18px}.okm .acts{display:flex;gap:8px;flex-wrap:wrap}
.okm .lay{display:grid;grid-template-columns:240px 1fr;gap:24px;align-items:start}.okm .flt{border:1px solid var(--l);border-radius:var(--rr);padding:14px;background:var(--w);position:sticky;top:12px}.okm .flt h4{margin:14px 0 8px;font:800 .8rem var(--fb,inherit);text-transform:uppercase;letter-spacing:.05em;color:var(--m)}.okm .flt h4:first-child{margin-top:0}
.okm .fl{display:flex;flex-direction:column;gap:2px}.okm .fl button{background:none;border:0;text-align:left;padding:7px 8px;border-radius:8px;cursor:pointer;color:var(--k);font:600 .9rem var(--fb,inherit);display:flex;justify-content:space-between;gap:8px;min-height:36px}.okm .fl button.on{background:var(--c);color:#fff}.okm .fl small{opacity:.7}
.okm .two{display:grid;grid-template-columns:1fr 1fr;gap:8px}.okm .ck{display:flex;gap:8px;align-items:center;font:600 .88rem var(--fb,inherit);margin-top:8px}.okm .ck input{width:18px;min-height:18px;height:18px}
.okm .bar{display:grid;grid-template-columns:1fr 200px;gap:10px;margin-bottom:16px}.okm .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}
.okm .pc{border:1px solid var(--l);border-radius:calc(var(--rr)*1.2);background:var(--w);overflow:hidden;display:flex;flex-direction:column}.okm .pc .im{aspect-ratio:4/3;background:var(--s);display:block;cursor:pointer}.okm .pc .im img{width:100%;height:100%;object-fit:contain;display:block}
.okm .pc .in{padding:14px;display:flex;flex-direction:column;gap:6px;flex:1}.okm .pc h3{margin:0;font:700 .98rem/1.3 var(--fd,inherit);cursor:pointer}.okm .pc .br{font-size:.78rem;color:var(--m)}.okm .pc .pr{margin-top:auto;display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}.okm .pc .pr b{font:800 1.2rem var(--fd,inherit)}.okm .pc .pr s{color:var(--m);font-size:.86rem}
.okm .tag{display:inline-block;font:700 .72rem var(--fb,inherit);padding:3px 9px;border-radius:99px;background:var(--s);color:var(--m);width:max-content}.okm .tag.ok{background:#dcfce7;color:#166534}.okm .tag.wa{background:#fef3c7;color:#92400e}.okm .tag.er{background:#fee2e2;color:#991b1b}
.okm .pg{display:flex;gap:6px;justify-content:center;margin-top:20px;flex-wrap:wrap}.okm .empty{padding:50px 10px;text-align:center;color:var(--m)}.okm .msg{padding:12px 14px;border-radius:var(--rr);margin-bottom:14px;font-weight:600}.okm .msg.ok{background:#dcfce7;color:#166534}.okm .msg.er{background:#fee2e2;color:#991b1b}.okm .msg.wa{background:#fef3c7;color:#92400e}
.okm .ov{position:fixed;inset:0;z-index:9000;background:#0008;display:none;align-items:stretch;justify-content:flex-end}.okm .ov.on{display:flex}.okm .pn{background:var(--w);width:min(560px,100%);display:flex;flex-direction:column;max-height:100%}.okm .pn.c{margin:auto;border-radius:calc(var(--rr)*1.4);width:min(900px,96%);max-height:92vh;overflow:auto}
.okm .hd{display:flex;justify-content:space-between;align-items:center;padding:16px 18px;border-bottom:1px solid var(--l)}.okm .hd h3{margin:0;font:800 1.15rem var(--fd,inherit)}.okm .hd button{background:none;border:0;font-size:1.5rem;cursor:pointer;color:var(--k);min-width:44px;min-height:44px}
.okm .bd{padding:16px 18px;overflow:auto;flex:1}.okm .ft{padding:14px 18px calc(14px + env(safe-area-inset-bottom));border-top:1px solid var(--l);background:var(--s);display:grid;gap:10px}.okm .row{display:flex;justify-content:space-between;gap:10px;align-items:center}.okm .row.t{font:800 1.15rem var(--fd,inherit)}
.okm .it{display:grid;grid-template-columns:56px 1fr auto;gap:10px;align-items:center;padding:10px 0;border-bottom:1px solid var(--l)}.okm .it img{width:56px;height:56px;object-fit:contain;background:var(--s);border-radius:8px}.okm .qt{display:flex;gap:6px;align-items:center;margin-top:4px}.okm .qt button{width:32px;height:32px;border:1px solid var(--l);background:var(--w);border-radius:8px;cursor:pointer;color:var(--k)}
.okm .stp{display:flex;gap:6px;margin-bottom:14px}.okm .stp span{flex:1;text-align:center;padding:8px 4px;border-radius:99px;background:var(--s);font:700 .74rem var(--fb,inherit);color:var(--m)}.okm .stp span.on{background:var(--c);color:#fff}.okm .stp span.ok{background:#dcfce7;color:#166534}
.okm .opt{display:flex;gap:12px;align-items:flex-start;padding:14px;border:1.5px solid var(--l);border-radius:var(--rr);margin-bottom:10px;cursor:pointer;background:var(--w)}.okm .opt.on{border-color:var(--c);box-shadow:0 0 0 2px color-mix(in srgb,var(--c) 18%,transparent)}.okm .opt input{width:18px;min-height:18px;height:18px;margin-top:3px}.okm .opt small{display:block;color:var(--m);font-weight:500;margin-top:2px}
.okm .fld{margin-bottom:12px}.okm .iban{font:700 .95rem monospace;background:var(--s);padding:10px 12px;border-radius:8px;word-break:break-all;user-select:all;margin:6px 0}
.okm .gal{display:grid;grid-template-columns:1fr 1fr;gap:20px;padding:18px}.okm .gal .big{aspect-ratio:1/1;background:var(--s);border-radius:var(--rr);display:grid;place-items:center;overflow:hidden}.okm .gal .big img{max-width:100%;max-height:100%;object-fit:contain}.okm .th{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}.okm .th img{width:54px;height:54px;object-fit:cover;border:2px solid transparent;border-radius:8px;cursor:pointer}.okm .th img.on{border-color:var(--c)}
.okm .spec{width:100%;border-collapse:collapse;font-size:.9rem;margin-top:10px}.okm .spec td{padding:6px 4px;border-bottom:1px solid var(--l)}.okm .spec td:first-child{color:var(--m);width:40%}
.okm .tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px;border-bottom:1px solid var(--l)}.okm .tabs button{background:none;border:0;border-bottom:3px solid transparent;padding:10px 14px;font:700 .95rem var(--fb,inherit);cursor:pointer;color:var(--m);min-height:44px}.okm .tabs button.on{color:var(--k);border-color:var(--c)}
.okm .card{border:1px solid var(--l);border-radius:calc(var(--rr)*1.2);background:var(--w);padding:16px;margin-bottom:14px}.okm .auth{max-width:440px;margin:0 auto}.okm .flow{display:flex;gap:4px;margin:10px 0 4px}.okm .flow i{flex:1;height:6px;border-radius:6px;background:var(--l)}.okm .flow i.on{background:var(--c)}
body:has(.okm) .spx-fab{display:none}
@media(max-width:860px){.okm .lay{grid-template-columns:1fr}.okm .flt{position:static}.okm .gal{grid-template-columns:1fr}.okm .bar{grid-template-columns:1fr}}
</style>"""

COMMON = r"""
var $=function(s,r){return(r||document).querySelector(s)},A=function(s,r){return[].slice.call((r||document).querySelectorAll(s))};
var TL=function(n){return Number(n||0).toLocaleString('tr-TR',{minimumFractionDigits:0,maximumFractionDigits:2})+' ₺'};
var E=function(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})};
var TK='okc_token';function tok(){try{return localStorage.getItem(TK)||''}catch(e){return''}}function setTok(t){try{t?localStorage.setItem(TK,t):localStorage.removeItem(TK)}catch(e){}}
function api(m,p,b){var o={method:m,headers:{}};var t=tok();if(t)o.headers.Authorization='Bearer '+t;if(b!==undefined){o.headers['Content-Type']='application/json';o.body=JSON.stringify(b)}
 return fetch('/api'+p,o).then(function(r){return r.text().then(function(x){var j={};try{j=JSON.parse(x)}catch(e){}if(!r.ok){var d=j&&j.detail;var er=new Error(typeof d==='string'?d:(d&&d[0]&&d[0].msg)||'İşlem yapılamadı');er.status=r.status;throw er}return j})})}
function toast(m,bad){var d=document.createElement('div');d.textContent=m;d.style.cssText='position:fixed;left:50%;bottom:90px;transform:translateX(-50%);background:'+(bad?'#b91c1c':'#166534')+';color:#fff;padding:12px 18px;border-radius:10px;z-index:99999;font:600 .92rem system-ui;max-width:90%';document.body.appendChild(d);setTimeout(function(){d.remove()},3600)}
var ST={bekliyor:0,odeme_bekliyor:['wa','Ödeme bekleniyor'],odeme_bildirildi:['wa','Ödeme kontrol ediliyor'],onaylandi:['ok','Onaylandı'],hazirlaniyor:['ok','Hazırlanıyor'],kargoda:['ok','Kargoda'],teslim_edildi:['ok','Teslim edildi'],iptal:['er','İptal edildi']};
function tag(s){var m=ST[s]||['','' + s];return '<span class="tag '+m[0]+'">'+m[1]+'</span>'}
var PL={kart:'Kredi / banka kartı',havale:'Havale / EFT',kapida_nakit:'Kapıda nakit',kapida_kart:'Kapıda kartla'};
"""

SHOP_JS = r"""(function(){""" + COMMON + r"""
var KEY='okcart-live',C=[],INFO=null,F={q:'',category:'',brand:'',sort:'pop',min:'',max:'',in_stock:false,discount:false,page:1},STEP=1,ACC=null,PM='',BUSY=false;
try{C=JSON.parse(localStorage.getItem(KEY)||'[]')}catch(e){C=[]}
function save(){try{localStorage.setItem(KEY,JSON.stringify(C))}catch(e){}cnt()}
function cnt(){var n=C.reduce(function(a,x){return a+x.q},0);A('[data-cc]').forEach(function(e){e.textContent=n})}
function sub(){return C.reduce(function(a,x){return a+x.price*x.q},0)}
function ship(){var s=sub();return INFO&&INFO.free_shipping_over&&s>=INFO.free_shipping_over?0:(INFO?INFO.shipping_fee:0)}
function pmeth(){return INFO.payment_methods.filter(function(m){return m.id===PM})[0]}
function fee(){var m=pmeth();return m&&m.fee?m.fee:0}
function total(){return sub()+ship()+fee()}
var root=$('#okm-root');
root.innerHTML='<div class="w"><div id="okm-msg"></div><div class="top"><div><h1 id="okm-t">Mağaza</h1><p class="sub" id="okm-s"></p></div><div class="acts"><a class="bt o" href="/hesabim" id="okm-acc">Giriş yap / Hesabım</a><button class="bt" id="okm-cart" type="button"><span>Sepet · <span data-cc>0</span></span></button></div></div>'+
 '<div class="lay"><aside class="flt" id="okm-f"></aside><div><div class="bar"><input id="okm-q" type="search" placeholder="Ürün, marka veya stok kodu ara…" aria-label="Ürün ara"><select id="okm-so" aria-label="Sırala"><option value="pop">Önerilen sıra</option><option value="asc">Fiyat: düşükten yükseğe</option><option value="desc">Fiyat: yüksekten düşüğe</option><option value="new">En yeni</option><option value="name">Ada göre</option></select></div><div class="grid" id="okm-g"></div><div class="pg" id="okm-pg"></div></div></div></div>'+
 '<div class="ov" id="okm-pv"><div class="pn c" id="okm-pvb"></div></div><div class="ov" id="okm-cv"><div class="pn" id="okm-cb"></div></div>';
function msg(h,k){$('#okm-msg').innerHTML=h?'<div class="msg '+(k||'ok')+'">'+h+'</div>':''}
function load(){var q='q='+encodeURIComponent(F.q)+'&category='+encodeURIComponent(F.category)+'&brand='+encodeURIComponent(F.brand)+'&sort='+F.sort+'&min='+(F.min||0)+'&max='+(F.max||0)+'&in_stock='+F.in_stock+'&discount='+F.discount+'&page='+F.page+'&per=24';
 return api('GET','/public/shop/search?'+q).then(function(r){flt(r);grid(r)}).catch(function(e){$('#okm-g').innerHTML='<div class="empty">'+E(e.message)+'</div>'})}
function flt(r){var h='<h4>Kategori</h4><div class="fl"><button data-c="" class="'+(F.category?'':'on')+'">Tümü</button>'+r.categories.map(function(c){return '<button data-c="'+E(c.name)+'" class="'+(F.category===c.name?'on':'')+'">'+E(c.name)+' <small>'+c.count+'</small></button>'}).join('')+'</div>';
 if(r.brands.length)h+='<h4>Marka</h4><div class="fl"><button data-b="" class="'+(F.brand?'':'on')+'">Tümü</button>'+r.brands.map(function(c){return '<button data-b="'+E(c.slug)+'" class="'+(F.brand===c.slug?'on':'')+'">'+E(c.name)+' <small>'+c.count+'</small></button>'}).join('')+'</div>';
 h+='<h4>Fiyat (₺)</h4><div class="two"><input id="okm-pmin" type="number" min="0" placeholder="En az" value="'+E(F.min)+'"><input id="okm-pmax" type="number" min="0" placeholder="En çok" value="'+E(F.max)+'"></div><label class="ck"><input type="checkbox" id="okm-st"'+(F.in_stock?' checked':'')+'> Sadece stoktakiler</label><label class="ck"><input type="checkbox" id="okm-ds"'+(F.discount?' checked':'')+'> İndirimdekiler</label>';
 $('#okm-f').innerHTML=h}
function grid(r){var g=$('#okm-g');g.innerHTML=r.items.length?r.items.map(function(p){return '<article class="pc"><a class="im" data-v="'+E(p.slug)+'">'+(p.img?'<img loading="lazy" alt="'+E(p.name)+'" src="'+E(p.img)+'">':'<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.2" style="opacity:.25;margin:auto;display:block;position:relative;top:calc(50% - 24px)"><path d="M3 7l9-4 9 4v10l-9 4-9-4V7z"/><path d="M3 7l9 4 9-4M12 11v10"/></svg>')+'</a><div class="in">'+(p.badge?'<span class="tag wa">'+E(p.badge)+'</span>':'')+'<span class="br">'+E(p.brand)+'</span><h3 data-v="'+E(p.slug)+'">'+E(p.name)+'</h3><div class="pr"><b>'+TL(p.price)+'</b>'+(p.old_price>p.price?'<s>'+TL(p.old_price)+'</s>':'')+'</div>'+
  (p.in_stock?'<button class="bt" data-a="'+E(p.id)+'" type="button">Sepete ekle</button>':'<span class="tag er">Stokta yok</span>')+'</div></article>'}).join(''):'<div class="empty">Aramanıza uygun ürün bulunamadı.</div>';
 g.dataset.items=JSON.stringify(r.items.reduce(function(o,p){o[p.id]=p;return o},{}));
 var pages=Math.ceil(r.total/r.per);$('#okm-pg').innerHTML=pages>1?Array.apply(null,Array(pages)).map(function(_,i){return '<button class="bt sm '+(i+1===r.page?'':'o')+'" data-p="'+(i+1)+'">'+(i+1)+'</button>'}).join(''):''}
function add(p,q){var f=C.filter(function(x){return x.id===p.id})[0];if(f)f.q=Math.min(20,f.q+(q||1));else C.push({id:p.id,name:p.name,price:p.price,img:p.img||(p.images&&p.images[0])||'',q:q||1});save();toast('Sepete eklendi')}
function detail(slug){api('GET','/public/shop/products/'+encodeURIComponent(slug)).then(function(p){var im=p.images||[];
 $('#okm-pvb').innerHTML='<div class="hd"><h3>'+E(p.name)+'</h3><button data-x aria-label="Kapat">×</button></div><div class="gal"><div><div class="big" id="okm-big">'+(im[0]?'<img alt="'+E(p.name)+'" src="'+E(im[0])+'">':'')+'</div><div class="th">'+im.map(function(u,i){return '<img class="'+(i?'':'on')+'" data-im="'+E(u)+'" src="'+E(u)+'" alt="">'}).join('')+'</div></div><div>'+
  '<span class="br" style="color:var(--m)">'+E(p.brand)+(p.model?' · '+E(p.model):'')+'</span><div style="margin:8px 0"><b style="font:800 1.6rem var(--fd,inherit)">'+TL(p.price)+'</b> '+(p.old_price>p.price?'<s style="color:var(--m)">'+TL(p.old_price)+'</s>':'')+'</div>'+
  (p.in_stock?'<span class="tag ok">Stokta'+(p.stock_left?' · son '+p.stock_left+' adet':'')+'</span>':'<span class="tag er">Stokta yok</span>')+'<div style="margin:12px 0;line-height:1.6;white-space:pre-line">'+E(p.description||p.short||'')+'</div>'+
  (p.specs&&p.specs.length?'<table class="spec">'+p.specs.map(function(s){return '<tr><td>'+E(s.k)+'</td><td>'+E(s.v)+'</td></tr>'}).join('')+'</table>':'')+
  (p.in_stock?'<div style="margin-top:14px"><button class="bt" id="okm-pa" type="button">Sepete ekle</button></div>':'')+'</div></div>';
 $('#okm-pv').classList.add('on');var b=$('#okm-pa');if(b)b.onclick=function(){add({id:p.id,name:p.name,price:p.price,img:im[0]});$('#okm-pv').classList.remove('on')};
 A('[data-im]',$('#okm-pvb')).forEach(function(i){i.onclick=function(){$('#okm-big').innerHTML='<img src="'+E(i.dataset.im)+'" alt="">';A('[data-im]').forEach(function(x){x.classList.remove('on')});i.classList.add('on')}})}).catch(function(e){toast(e.message,1)})}
/* ---- sepet / ödeme ---- */
function openCart(){STEP=1;drawCart();$('#okm-cv').classList.add('on')}
function steps(){var n=['Sepet','Teslimat','Ödeme','Onay'];return '<div class="stp">'+n.map(function(x,i){return '<span class="'+(i+1===STEP?'on':(i+1<STEP?'ok':''))+'">'+(i+1)+' '+x+'</span>'}).join('')+'</div>'}
function drawCart(){var b=$('#okm-cb');
 var head='<div class="hd"><h3>'+(STEP===1?'Sepetim':'Sipariş')+'</h3><button data-cx aria-label="Kapat">×</button></div>';
 if(STEP===1){b.innerHTML=head+'<div class="bd">'+(C.length?C.map(function(x,j){return '<div class="it"><img src="'+E(x.img)+'" alt=""><div><b>'+E(x.name)+'</b><div class="qt"><button data-d="'+j+'" aria-label="Azalt">−</button><span>'+x.q+'</span><button data-u="'+j+'" aria-label="Artır">+</button><button data-r="'+j+'" style="width:auto;padding:0 10px">Kaldır</button></div></div><b>'+TL(x.price*x.q)+'</b></div>'}).join(''):'<div class="empty">Sepetiniz boş.</div>')+'</div>'+
   '<div class="ft"><div class="row"><span>Ara toplam</span><b>'+TL(sub())+'</b></div>'+(INFO.free_shipping_over?'<small style="color:var(--m)">'+TL(INFO.free_shipping_over)+' ve üzeri kargo ücretsiz</small>':'')+'<button class="bt" id="okm-go" '+(C.length?'':'disabled')+'>Devam et</button></div>'}
 if(STEP===2){if(!ACC){b.innerHTML=head+'<div class="bd">'+steps()+'<div class="msg wa">Sipariş vermek için giriş yapın veya üye olun. Sepetiniz korunur.</div><a class="bt" href="/hesabim?donus=magaza">Giriş yap / Üye ol</a></div><div class="ft"><button class="bt o" id="okm-bk">Sepete dön</button></div>';return}
  b.innerHTML=head+'<div class="bd">'+steps()+'<div class="fld"><label>Ad soyad *</label><input id="o_n" value="'+E(ACC.name)+'" autocomplete="name"></div><div class="two"><div class="fld"><label>Telefon *</label><input id="o_p" type="tel" value="'+E(ACC.phone)+'" autocomplete="tel"></div><div class="fld"><label>E-posta'+((INFO.payment_methods.some(function(m){return m.id==='kart'}))?' (kartla ödeme için gerekli)':'')+'</label><input id="o_e" type="email" value="'+E(ACC.email)+'" autocomplete="email"></div></div>'+
   '<div class="two"><div class="fld"><label>İl *</label><input id="o_c" value="'+E(ACC.city)+'" autocomplete="address-level1"></div><div class="fld"><label>İlçe *</label><input id="o_d" value="'+E(ACC.district)+'" autocomplete="address-level2"></div></div><div class="fld"><label>Açık adres *</label><textarea id="o_a" rows="3" autocomplete="street-address">'+E(ACC.address)+'</textarea></div><div class="fld"><label>Sipariş notu</label><input id="o_nt"></div></div>'+
   '<div class="ft"><div class="two"><button class="bt o" id="okm-bk">Geri</button><button class="bt" id="okm-go">Devam et</button></div></div>'}
 if(STEP===3){var ms=INFO.payment_methods;if(!PM||!pmeth())PM=ms[0]?ms[0].id:'';
  b.innerHTML=head+'<div class="bd">'+steps()+(ms.length?ms.map(function(m){return '<label class="opt '+(m.id===PM?'on':'')+'"><input type="radio" name="pm" value="'+m.id+'" '+(m.id===PM?'checked':'')+'><span><b>'+E(m.label)+'</b>'+(m.fee?' <em style="font-style:normal;color:var(--m)">+'+TL(m.fee)+'</em>':'')+'<small>'+E(m.desc||'')+'</small></span></label>'}).join(''):'<div class="msg er">Şu an ödeme alınamıyor. Lütfen firmayla iletişime geçin.</div>')+
   '<label class="ck"><input type="checkbox" id="o_ok"> <span>'+INFO.legal_docs.filter(function(d){return d.checkout}).map(function(d){return '<a href="/'+d.slug+'" target="_blank" rel="noopener"><u>'+E(d.title)+'</u></a>'}).join(' ve ')+' metinlerini okudum, kabul ediyorum.</span></label><div class="msg er" id="o_er" style="display:none;margin-top:10px"></div></div>'+
   '<div class="ft"><div class="row"><span>Ürünler</span><b>'+TL(sub())+'</b></div><div class="row"><span>Kargo</span><b>'+(ship()?TL(ship()):'Ücretsiz')+'</b></div>'+(fee()?'<div class="row"><span>Kapıda ödeme bedeli</span><b>'+TL(fee())+'</b></div>':'')+'<div class="row t"><span>Toplam</span><b id="o_t">'+TL(total())+'</b></div><div class="two"><button class="bt o" id="okm-bk">Geri</button><button class="bt" id="okm-go" '+(ms.length?'':'disabled')+'>Siparişi tamamla</button></div></div>'}}
function err(m){var e=$('#o_er');if(e){e.style.display='block';e.textContent=m}else toast(m,1)}
function order(){if(BUSY)return;if(!$('#o_ok').checked)return err('Sözleşme ve ön bilgilendirme metinlerini onaylayın.');if(!PM)return err('Ödeme yöntemi seçin.');
 var cu=ACC._f;BUSY=true;var bt=$('#okm-go');bt.disabled=true;bt.textContent='Gönderiliyor…';
 api('POST','/public/shop/orders',{customer:{name:cu.n,phone:cu.p,email:cu.e,city:cu.c,district:cu.d,address:cu.a+(cu.d||cu.c?' '+cu.d+'/'+cu.c:'')},items:C.map(function(x){return{product_id:x.id,qty:x.q}}),payment_method:PM,accept_terms:true,note:cu.nt}).then(function(r){
  C=[];save();BUSY=false;done(r)}).catch(function(e){BUSY=false;bt.disabled=false;bt.textContent='Siparişi tamamla';if(e.status===401){setTok('');ACC=null;STEP=2;drawCart();return}err(e.message)})}
function done(r){STEP=4;var b=$('#okm-cb'),h='<div class="hd"><h3>Siparişiniz alındı</h3><button data-cx aria-label="Kapat">×</button></div><div class="bd">'+steps()+'<div style="text-align:center"><div style="color:var(--m)">Sipariş numaranız</div><div style="font:800 1.5rem monospace;margin:6px 0">'+E(r.order_no)+'</div><b>Toplam '+TL(r.total)+'</b></div>';
 if(r.next==='iyzico'){h+='<p style="margin-top:14px">Güvenli ödeme sayfasına yönlendiriliyorsunuz…</p></div>';b.innerHTML=h;payCard(r.order_no,ACC._f.p);return}
 if(r.next==='havale'){h+='<div class="msg wa" style="margin-top:14px">Ödemeyi aşağıdaki hesaba yapın; açıklamaya sipariş numaranızı yazın. Ödemeniz kontrol edilince siparişiniz hazırlanır.</div>'+(r.bank_accounts||[]).map(function(a){return '<div class="card"><b>'+E(a.bank)+'</b><div>'+E(a.holder)+'</div><div class="iban">'+E(a.iban)+'</div></div>'}).join('')+'<div class="fld"><label>Ödemeyi yaptıysanız gönderen adı</label><input id="o_snd"></div><button class="bt" id="okm-pd">Ödemeyi yaptım</button>'}
 else h+='<div class="msg ok" style="margin-top:14px">Siparişiniz onaylandı. Ödemeyi teslimatta yapacaksınız'+(r.cod_fee?' (kapıda ödeme bedeli '+TL(r.cod_fee)+' dahildir)':'')+'.</div>';
 h+='<p style="margin-top:14px"><a class="bt o" href="/hesabim">Siparişlerim</a></p></div>';b.innerHTML=h;var pd=$('#okm-pd');if(pd)pd.onclick=function(){api('POST','/public/shop/orders/'+r.order_no+'/paid',{phone:ACC._f.p,sender:$('#o_snd').value}).then(function(){toast('Ödeme bildiriminiz alındı');pd.disabled=true}).catch(function(e){toast(e.message,1)})}}
function payCard(no,ph){api('POST','/public/shop/pay/iyzico/init',{order_no:no,phone:ph}).then(function(r){if(r.url)location.href=r.url;else throw new Error('Ödeme sayfası açılamadı')}).catch(function(e){$('#okm-cb').querySelector('.bd').insertAdjacentHTML('beforeend','<div class="msg er">'+E(e.message)+' Siparişlerim sayfasından ödemeyi tekrar deneyebilirsiniz.</div>')})}
function bind(){
 root.addEventListener('click',function(e){var t=e.target,x;
  if((x=t.closest('[data-c]'))&&x.closest('#okm-f')){F.category=x.dataset.c;F.page=1;return load()}
  if((x=t.closest('[data-b]'))&&x.closest('#okm-f')){F.brand=x.dataset.b;F.page=1;return load()}
  if(x=t.closest('[data-p]')){F.page=+x.dataset.p;window.scrollTo({top:0,behavior:'smooth'});return load()}
  if(x=t.closest('[data-v]'))return detail(x.dataset.v);
  if(x=t.closest('[data-a]')){var it=JSON.parse($('#okm-g').dataset.items)[x.dataset.a];return it&&add(it)}
  if(t.closest('#okm-cart'))return openCart();
  if(t.closest('[data-x]')||t===$('#okm-pv'))return $('#okm-pv').classList.remove('on');
  if(t.closest('[data-cx]')||t===$('#okm-cv'))return $('#okm-cv').classList.remove('on');
  if(x=t.closest('[data-d]')){var j=+x.dataset.d;C[j].q--;if(C[j].q<1)C.splice(j,1);save();return drawCart()}
  if(x=t.closest('[data-u]')){C[+x.dataset.u].q=Math.min(20,C[+x.dataset.u].q+1);save();return drawCart()}
  if(x=t.closest('[data-r]')){C.splice(+x.dataset.r,1);save();return drawCart()}
  if(t.closest('#okm-bk')){STEP--;return drawCart()}
  if(t.closest('#okm-go')){
   if(STEP===1){if(!C.length)return;STEP=2;return drawCart()}
   if(STEP===2){var v=function(i){return $(i).value.trim()};var f={n:v('#o_n'),p:v('#o_p'),e:v('#o_e'),c:v('#o_c'),d:v('#o_d'),a:v('#o_a'),nt:v('#o_nt')};
    if(f.n.length<3)return toast('Ad soyad yazın',1);if(f.p.replace(/\D/g,'').length<10)return toast('Geçerli telefon yazın',1);if(!f.c||!f.d)return toast('İl ve ilçe yazın',1);if(f.a.length<8)return toast('Açık adresinizi yazın',1);ACC._f=f;STEP=3;return drawCart()}
   if(STEP===3)return order()}
 });
 root.addEventListener('change',function(e){var t=e.target;if(t.name==='pm'){PM=t.value;var s=$('#o_ok');var ck=s&&s.checked;drawCart();if(ck)$('#o_ok').checked=true}});
 var qt;$('#okm-q').addEventListener('input',function(e){clearTimeout(qt);qt=setTimeout(function(){F.q=e.target.value.trim();F.page=1;load()},300)});$('#okm-so').addEventListener('change',function(e){F.sort=e.target.value;F.page=1;load()});
 $('#okm-f').addEventListener('change',function(e){var t=e.target;if(t.id==='okm-st')F.in_stock=t.checked;else if(t.id==='okm-ds')F.discount=t.checked;else if(t.id==='okm-pmin')F.min=t.value;else if(t.id==='okm-pmax')F.max=t.value;else return;F.page=1;load()});
}
function me(){if(!tok())return Promise.resolve();return api('GET','/public/customer/me').then(function(a){ACC=a;var l=$('#okm-acc');l.textContent='Hesabım · '+a.name.split(' ')[0]}).catch(function(){setTok('')})}
var qs=new URLSearchParams(location.search),od=qs.get('odeme');
api('GET','/public/shop/info').then(function(i){INFO=i;$('#okm-t').textContent=i.title||'Mağaza';$('#okm-s').textContent=i.subtitle||'';if(i.min_order)$('#okm-s').textContent+=(i.subtitle?' · ':'')+'Minimum sipariş '+TL(i.min_order);
 if(od==='ok'){C=[];save();msg('Ödemeniz alındı. Sipariş numaranız: <b>'+E(qs.get('no')||'')+'</b>. Siparişinizi <a href="/hesabim">hesabınızdan</a> takip edebilirsiniz.','ok')}
 else if(od==='kontrol')msg('Ödemeniz alındı ancak tutar kontrolü gerekiyor. Siparişiniz ('+E(qs.get('no')||'')+') firmamız tarafından kontrol edilecek, sizinle iletişime geçilecek.','wa');
 else if(od==='hata')msg('Ödeme tamamlanamadı. Siparişlerim sayfasından ödemeyi tekrar deneyebilirsiniz.','er');
 cnt();bind();return Promise.all([me(),load()])}).catch(function(e){root.innerHTML='<div class="w"><div class="empty">Mağaza şu an kapalı.</div></div>'});
})();"""

ACC_JS = r"""(function(){""" + COMMON + r"""
var root=$('#okm-root'),ACC=null,TAB='siparis',qs=new URLSearchParams(location.search),BACK=qs.get('donus');
function home(){root.innerHTML='<div class="w auth"><h1>Hesabım</h1><p class="sub">Siparişlerinizi görmek ve hızlı alışveriş için giriş yapın.</p><div class="tabs"><button class="on" data-m="g">Giriş</button><button data-m="u">Üye ol</button></div><div id="okm-fm"></div></div>';form('g');
 root.onclick=function(e){var b=e.target.closest('[data-m]');if(b){A('.tabs button').forEach(function(x){x.classList.remove('on')});b.classList.add('on');form(b.dataset.m)}}}
function form(m){var h='';
 if(m==='g')h='<div class="fld"><label>Telefon</label><input id="a_p" type="tel" autocomplete="tel"></div><div class="fld"><label>Şifre</label><input id="a_w" type="password" autocomplete="current-password"></div><div id="a_e"></div><button class="bt" id="a_go" style="width:100%">Giriş yap</button><p style="text-align:center;margin-top:12px"><a href="#" id="a_fg">Şifremi unuttum</a></p>';
 else h='<div class="fld"><label>Ad soyad *</label><input id="a_n" autocomplete="name"></div><div class="fld"><label>Telefon *</label><input id="a_p" type="tel" autocomplete="tel"></div><div class="fld"><label>E-posta</label><input id="a_m" type="email" autocomplete="email"></div><div class="fld"><label>Şifre (en az 6 karakter) *</label><input id="a_w" type="password" autocomplete="new-password"></div><div id="a_e"></div><button class="bt" id="a_go" style="width:100%">Üye ol</button><p style="color:var(--m);font-size:.82rem;margin-top:10px">Üye olarak <a href="/gizlilik-kvkk">gizlilik ve KVKK metnini</a> kabul etmiş olursunuz.</p>';
 $('#okm-fm').innerHTML=h;var go=$('#a_go');
 go.onclick=function(){go.disabled=true;var p=m==='g'?{phone:$('#a_p').value,password:$('#a_w').value}:{name:$('#a_n').value,phone:$('#a_p').value,email:$('#a_m').value,password:$('#a_w').value};
  api('POST','/public/customer/'+(m==='g'?'login':'register'),p).then(function(r){setTok(r.token);if(BACK==='magaza')location.href='/magaza';else boot()}).catch(function(e){go.disabled=false;$('#a_e').innerHTML='<div class="msg er">'+E(e.message)+'</div>'})};
 var fg=$('#a_fg');if(fg)fg.onclick=function(e){e.preventDefault();var ph=$('#a_p').value;if(!ph)return $('#a_e').innerHTML='<div class="msg wa">Önce telefon numaranızı yazın.</div>';api('POST','/public/customer/forgot',{phone:ph}).then(function(){$('#a_e').innerHTML='<div class="msg ok">Kayıtlı telefona şifre sıfırlama bilgisi gönderildi.</div>'}).catch(function(x){$('#a_e').innerHTML='<div class="msg er">'+E(x.message)+'</div>'})}}
function panel(){root.innerHTML='<div class="w"><div class="top"><div><h1>Merhaba, '+E(ACC.name.split(' ')[0])+'</h1><p class="sub">'+E(ACC.phone)+'</p></div><div class="acts"><a class="bt" href="/magaza">Alışverişe devam</a><button class="bt o" id="a_out">Çıkış yap</button></div></div><div id="okm-msg"></div><div class="tabs"><button data-t="siparis">Siparişlerim</button><button data-t="bilgi">Bilgilerim</button><button data-t="servis">Servis kayıtlarım</button><button data-t="gizli">Verilerim</button></div><div id="okm-tab"></div></div>';
 root.onclick=function(e){var b=e.target.closest('[data-t]');if(b){TAB=b.dataset.t;tab()}if(e.target.id==='a_out'){setTok('');location.href='/hesabim'}};tab();
 var od=qs.get('odeme');if(od==='ok')$('#okm-msg').innerHTML='<div class="msg ok">Ödemeniz alındı, teşekkürler.</div>'}
function tab(){A('.tabs button').forEach(function(b){b.classList.toggle('on',b.dataset.t===TAB)});var el=$('#okm-tab');el.innerHTML='<div class="empty">Yükleniyor…</div>';
 if(TAB==='siparis')api('GET','/public/customer/orders').then(function(rs){el.innerHTML=rs.length?rs.map(order).join(''):'<div class="empty">Henüz siparişiniz yok. <a href="/magaza">Mağazaya göz atın</a>.</div>';
  A('[data-pay]',el).forEach(function(b){b.onclick=function(){b.disabled=true;api('POST','/public/shop/pay/iyzico/init',{order_no:b.dataset.pay,phone:ACC.phone}).then(function(r){location.href=r.url}).catch(function(e){b.disabled=false;toast(e.message,1)})}})}).catch(function(e){el.innerHTML='<div class="msg er">'+E(e.message)+'</div>'});
 if(TAB==='bilgi'){el.innerHTML='<div class="card" style="max-width:560px"><div class="fld"><label>Ad soyad</label><input id="b_n" value="'+E(ACC.name)+'"></div><div class="fld"><label>E-posta</label><input id="b_e" value="'+E(ACC.email)+'"></div><div class="two"><div class="fld"><label>İl</label><input id="b_c" value="'+E(ACC.city)+'"></div><div class="fld"><label>İlçe</label><input id="b_d" value="'+E(ACC.district)+'"></div></div><div class="fld"><label>Teslimat adresi</label><textarea id="b_a" rows="3">'+E(ACC.address)+'</textarea></div><button class="bt" id="b_s">Kaydet</button></div>'+
  '<div class="card" style="max-width:560px"><b>Şifre değiştir</b><div class="two" style="margin-top:8px"><div class="fld"><label>Mevcut şifre</label><input id="b_o" type="password"></div><div class="fld"><label>Yeni şifre</label><input id="b_w" type="password"></div></div><button class="bt o" id="b_p">Şifreyi güncelle</button></div>';
  $('#b_s').onclick=function(){api('PUT','/public/customer/me',{name:$('#b_n').value,email:$('#b_e').value,city:$('#b_c').value,district:$('#b_d').value,address:$('#b_a').value}).then(function(a){ACC=a;toast('Bilgileriniz kaydedildi')}).catch(function(e){toast(e.message,1)})};
  $('#b_p').onclick=function(){api('PUT','/public/customer/me',{old_password:$('#b_o').value,new_password:$('#b_w').value}).then(function(){toast('Şifre güncellendi')}).catch(function(e){toast(e.message,1)})}}
 if(TAB==='servis')api('GET','/public/customer/jobs').then(function(js){el.innerHTML=js.length?js.map(function(j){return '<div class="card"><div class="row"><b>'+E(j.job_number||'Servis kaydı')+'</b><span class="tag">'+E(j.status)+'</span></div><div>'+E(j.device)+'</div><div style="color:var(--m)">'+E(j.fault||'')+'</div>'+(j.track_token?'<p><a href="/takip/'+E(j.track_token)+'">Servisi takip et</a></p>':'')+'</div>'}).join(''):'<div class="empty">Servis kaydınız yok.</div>'}).catch(function(){el.innerHTML='<div class="empty">Servis kayıtları şu an görüntülenemiyor.</div>'});
 if(TAB==='gizli'){el.innerHTML='<div class="card" style="max-width:560px"><b>Verilerimi indir</b><p style="color:var(--m)">Hesabınıza ve siparişlerinize ait verileri indirebilirsiniz.</p><button class="bt o" id="g_x">Verilerimi indir</button></div><div class="card" style="max-width:560px"><b>Hesabımı sil</b><p style="color:var(--m)">Hesabınız kalıcı olarak silinir. Yasal saklama yükümlülüğü olan sipariş kayıtları korunur.</p><div class="fld"><label>Şifreniz</label><input id="g_p" type="password"></div><button class="bt d" id="g_d">Hesabımı sil</button></div>';
  $('#g_x').onclick=function(){api('GET','/public/customer/export').then(function(j){var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(j,null,2)],{type:'application/json'}));a.download='verilerim.json';a.click()}).catch(function(e){toast(e.message,1)})};
  $('#g_d').onclick=function(){if(!confirm('Hesabınız kalıcı olarak silinecek. Emin misiniz?'))return;api('POST','/public/customer/delete',{password:$('#g_p').value}).then(function(){setTok('');location.href='/'}).catch(function(e){toast(e.message,1)})}}}
function order(o){var pay=o.payment||{},wait=o.status==='odeme_bekliyor';
 return '<div class="card"><div class="row"><b>'+E(o.order_no)+'</b>'+tag(o.status)+'</div><div style="color:var(--m);font-size:.88rem">'+E((o.created_at||'').slice(0,10))+' · '+E(pay.label||PL[pay.method]||'')+' · <b style="color:var(--k)">'+TL(o.total)+'</b></div>'+
  '<div class="flow">'+['onaylandi','hazirlaniyor','kargoda','teslim_edildi'].map(function(s,i){var idx=['onaylandi','hazirlaniyor','kargoda','teslim_edildi'].indexOf(o.status);return '<i class="'+(idx>=i?'on':'')+'"></i>'}).join('')+'</div><div style="font-size:.78rem;color:var(--m);display:flex;justify-content:space-between"><span>Onay</span><span>Hazırlık</span><span>Kargo</span><span>Teslim</span></div>'+
  '<div style="margin-top:8px">'+(o.items||[]).map(function(i){return '<div class="row"><span>'+i.qty+' × '+E(i.name)+'</span><span>'+TL(i.line_total)+'</span></div>'}).join('')+'</div>'+
  (o.tracking_no?'<p style="margin-top:8px">Kargo: <b>'+E(o.carrier||'')+' '+E(o.tracking_no)+'</b></p>':'')+
  (wait&&pay.method==='kart'?'<p style="margin-top:8px"><button class="bt" data-pay="'+E(o.order_no)+'">Ödemeyi tamamla</button></p>':'')+
  (wait&&pay.method==='havale'&&o.bank_accounts?'<div class="msg wa" style="margin-top:8px">Havale bekleniyor. Açıklamaya <b>'+E(o.order_no)+'</b> yazın.'+(o.bank_accounts||[]).map(function(a){return '<div class="iban">'+E(a.bank)+' · '+E(a.iban)+'</div>'}).join('')+'</div>':'')+'</div>'}
function boot(){if(!tok())return home();api('GET','/public/customer/me').then(function(a){ACC=a;panel()}).catch(function(){setTok('');home()})}
boot();
})();"""


def _wrap(js: str) -> str:
    return CSS + '<section class="okm"><div id="okm-root"><div class="w"><p style="color:var(--m)">Yükleniyor…</p></div></div></section><script>' + js + '</script>'


def shop_page() -> str:
    return _wrap(SHOP_JS)


def account_page() -> str:
    return _wrap(ACC_JS)
