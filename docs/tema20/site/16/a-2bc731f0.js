var OK=(function(){var K='ok16_',L=localStorage,o={};
function g(k,d){try{return JSON.parse(L.getItem(K+k))||d}catch(e){return d}}function s(k,v){try{L.setItem(K+k,JSON.stringify(v))}catch(e){}}
function $(q,r){return (r||document).querySelector(q)}function $$(q,r){return [].slice.call((r||document).querySelectorAll(q))}
function esc(t){return String(t==null?'':t).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function num(t){var m=String(t).match(/\d[\d.]*/);return m?parseInt(m[0].replace(/\./g,''),10):0}
function tl(n){return n.toLocaleString('tr-TR')+' ₺'}
o.esc=esc;o.num=num;o.tl=tl;o.$=$;o.$$=$$;
o.cart=function(){return g('cart',[])};
o.badge=function(){var n=o.cart().reduce(function(a,x){return a+x.q},0);$$('#sbc').forEach(function(e){e.textContent=n})};
o.toast=function(m){var t=document.createElement('div');t.className='toast';t.textContent=m;document.body.appendChild(t);setTimeout(function(){t.classList.add('on')},10);setTimeout(function(){t.remove()},2400)};
o.add=function(it){var c=o.cart(),k=it.id+'|'+(it.opt||''),f=c.filter(function(x){return x.k==k})[0];if(f)f.q+=it.q||1;else{it.k=k;it.q=it.q||1;c.push(it)}s('cart',c);o.badge();o.toast(it.n+' sepete eklendi')};
o.addP=function(b){var d=b.closest('[data-id]');o.add({id:d.dataset.id,n:d.dataset.n,p:num(d.dataset.p),img:d.dataset.img,opt:b.dataset.opt||''})};
o.go=function(f,to){var d={};$$('input,select,textarea',f).forEach(function(i){d[i.placeholder||i.name]=i.value});try{sessionStorage.setItem(K+'pre',JSON.stringify(d))}catch(e){}location.href=to;return false};
o.pre=function(){try{return JSON.parse(sessionStorage.getItem(K+'pre'))||{}}catch(e){return{}}};
o.no=function(p){return p+Math.random().toString(36).slice(2,7).toUpperCase()};
o.save=function(k,v){var a=g(k,[]);a.unshift(v);s(k,a)};o.list=function(k){return g(k,[])};o.put=s;o.get=g;
o.fmtD=function(d){return d.toLocaleDateString('tr-TR',{day:'numeric',month:'long',weekday:'short'})};
/* genel form: kayıt oluşturur, takip no verir */
o.form=function(f){var pre=o.pre();$$('input,select,textarea',f).forEach(function(i){var v=pre[i.placeholder||i.name];if(v&&!i.value)i.value=v});
f.addEventListener('submit',function(e){e.preventDefault();var d={},ok=true;$$('[required]',f).forEach(function(i){if(!i.value.trim()){ok=false;i.classList.add('bad')}else i.classList.remove('bad')});if(!ok){o.toast('Zorunlu alanları doldurun');return}
$$('input,select,textarea',f).forEach(function(i){if(i.type!='file')d[i.getAttribute('data-l')||i.placeholder||i.name]=i.value});
var no=o.no(f.dataset.p||'TK');o.save('kayit',{no:no,tur:f.dataset.kind,baslik:f.dataset.title,veri:d,t:Date.now(),durum:0});
var m=$('.done',f.parentNode);f.hidden=true;m.hidden=false;$('.no',m).textContent=no;m.scrollIntoView({behavior:'smooth',block:'center'})})};
/* takip */
o.track=function(){var f=$('#tf'),r=$('#tr');f.addEventListener('submit',function(e){e.preventDefault();var q=$('input',f).value.trim().toUpperCase(),all=[].concat(o.list('kayit'),o.list('siparis'),o.list('randevu'));var h=all.filter(function(x){return x.no==q})[0];
if(!h){r.innerHTML='<div class="box"><b>Kayıt bulunamadı.</b><p>Numarayı SMS ve e-postadaki gibi yazın. Numara yoksa bizi arayın.</p></div>';return}
var st=h.adimlar||['Talep alındı','Planlandı','Yolda / hazırlanıyor','Tamamlandı'];var cur=Math.min(h.durum||0,st.length-1);
r.innerHTML='<div class="box"><b>'+esc(h.no)+'</b> · '+esc(h.baslik||h.tur||'')+'<ol class="tlx">'+st.map(function(x,i){return '<li class="'+(i<=cur?'on':'')+'">'+esc(x)+'</li>'}).join('')+'</ol></div>'})};
/* randevu sihirbazı */
o.wizard=function(D){var A=$('#app'),st={i:0,s:null,u:null,d:null,t:null},pre=o.pre(),days=[],now=new Date();now.setHours(0,0,0,0);
for(var k=0;days.length<10;k++){var d=new Date(now.getTime()+k*864e5);if(d.getDay()!=0||D.sunday)days.push(d)}
if(pre){D.services.forEach(function(x,i){var v=pre['Hizmet']||pre['Uygulama']||pre['Tedavi']||pre['Sınıf'];if(v&&x.n.toLowerCase().indexOf(v.toLowerCase())==0)st.s=i})}
var q=new URLSearchParams(location.search);if(q.get('s')!=null)st.s=+q.get('s');
var steps=['Hizmet'].concat(D.team?['Uzman']:[]).concat(['Gün','Saat','Bilgiler']);
function busy(d,t,u){var h=0,str=d.toDateString()+t+u;for(var i=0;i<str.length;i++)h=(h*31+str.charCodeAt(i))>>>0;var mine=o.list('randevu').some(function(x){return x.dk==d.toDateString()&&x.t==t&&(x.u==u||u=='Fark etmez')});return mine||h%5==0}
function slots(){var a=[],h=D.hours[0];while(h<D.hours[1]){a.push(('0'+Math.floor(h)).slice(-2)+':'+(h%1?'30':'00'));h+=D.step}return a}
function head(){return '<ol class="stp">'+steps.map(function(x,i){return '<li class="'+(i==st.i?'on':(i<st.i?'ok':''))+'">'+x+'</li>'}).join('')+'</ol>'}
function R(){var h=head(),n=steps[st.i],body='';
if(n=='Hizmet')body='<div class="opts">'+D.services.map(function(x,i){return '<button class="opt'+(st.s==i?' on':'')+'" data-v="'+i+'"><b>'+esc(x.n)+'</b><span>'+esc(x.d||'')+'</span><i>'+esc(x.p)+'</i></button>'}).join('')+'</div>';
if(n=='Uzman')body='<div class="opts">'+['Fark etmez'].concat(D.team).map(function(x){return '<button class="opt'+(st.u==x?' on':'')+'" data-v="'+esc(x)+'"><b>'+esc(x)+'</b></button>'}).join('')+'</div>';
if(n=='Gün')body='<div class="days">'+days.map(function(d,i){return '<button class="opt'+(st.d===i?' on':'')+'" data-v="'+i+'"><b>'+d.toLocaleDateString('tr-TR',{weekday:'short'})+'</b><span>'+d.getDate()+' '+d.toLocaleDateString('tr-TR',{month:'short'})+'</span></button>'}).join('')+'</div>';
if(n=='Saat'){var u=st.u||'Fark etmez';body='<div class="slots">'+slots().map(function(t){var b=busy(days[st.d],t,u);return '<button class="sl2'+(st.t==t?' on':'')+'" data-v="'+t+'"'+(b?' disabled':'')+'>'+t+'</button>'}).join('')+'</div><p class="hint">Dolu saatler pasif görünür.</p>'}
if(n=='Bilgiler'){var sv=D.services[st.s];body='<div class="sum"><b>'+esc(sv.n)+'</b><span>'+(st.u?esc(st.u)+' · ':'')+o.fmtD(days[st.d])+' · '+st.t+'</span><i>'+esc(sv.p)+'</i></div><form id="wf" class="ff"><label>Ad soyad<input required data-l="Ad soyad" placeholder="Ad soyad"></label><label>Telefon<input required data-l="Telefon" placeholder="05xx xxx xx xx" inputmode="tel"></label><label>Not<textarea data-l="Not" placeholder="İsterseniz not bırakın" rows="2"></textarea></label><button class="b p">Randevuyu onayla</button></form>'}
var nav=(st.i>0?'<button class="b o" id="bk">Geri</button>':'')+(n!='Bilgiler'?'<button class="b p" id="nx">Devam</button>':'');
A.innerHTML=h+'<div class="wbody">'+body+'</div><div class="wnav">'+nav+'</div>';
$$('.opt,.sl2',A).forEach(function(b){b.onclick=function(){var v=b.dataset.v;if(n=='Hizmet')st.s=+v;if(n=='Uzman')st.u=v;if(n=='Gün'){st.d=+v;st.t=null}if(n=='Saat')st.t=v;R()}});
if($('#bk'))$('#bk').onclick=function(){st.i--;R()};
if($('#nx'))$('#nx').onclick=function(){var ok=(n=='Hizmet'&&st.s!=null)||(n=='Uzman'&&st.u)||(n=='Gün'&&st.d!=null)||(n=='Saat'&&st.t);if(!ok){o.toast('Bir seçim yapın');return}st.i++;R()};
if($('#wf'))$('#wf').onsubmit=function(e){e.preventDefault();var f=e.target,ok=true;$$('[required]',f).forEach(function(i){if(!i.value.trim()){ok=false;i.classList.add('bad')}});if(!ok)return;
var sv=D.services[st.s],no=o.no('RN'),dd=days[st.d],rec={no:no,baslik:sv.n+' · '+o.fmtD(dd)+' '+st.t,tur:'randevu',u:st.u||'',t:st.t,dk:dd.toDateString(),ad:$('input',f).value,durum:0,adimlar:['Randevu alındı','SMS hatırlatma','Hizmet','Tamamlandı'],t0:Date.now()};o.save('randevu',rec);
var ics='BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nSUMMARY:'+sv.n+'\nDTSTART:'+dd.getFullYear()+('0'+(dd.getMonth()+1)).slice(-2)+('0'+dd.getDate()).slice(-2)+'T'+st.t.replace(':','')+'00\nEND:VEVENT\nEND:VCALENDAR';
A.innerHTML='<div class="box ok2"><h3>Randevunuz alındı</h3><p><b>'+esc(sv.n)+'</b><br>'+o.fmtD(dd)+' · '+st.t+(st.u?' · '+esc(st.u):'')+'</p><p>Randevu numaranız <b>'+no+'</b>. Hatırlatma SMS\'i gönderilir.</p><div class="row"><a class="b p" href="data:text/calendar;charset=utf-8,'+encodeURIComponent(ics)+'" download="randevu.ics">Takvime ekle</a><a class="b o" href="'+D.track+'">Randevuyu sorgula</a></div></div>'};
}R()};
/* ürün / ilan süzgeci */
o.filter=function(){var chips=$$('.fl [data-f]'),cards=$$('[data-cat]'),st={f:'',q:'',s:''};
function run(){cards.forEach(function(c){var ok=(!st.f||c.dataset.cat==st.f||(c.dataset.cat||'').split('|').indexOf(st.f)>-1)&&(!st.q||c.textContent.toLowerCase().indexOf(st.q)>-1);c.hidden=!ok});
var wrap=cards[0]&&cards[0].parentNode;if(wrap&&st.s){var arr=cards.slice().sort(function(a,b){return (st.s=='az'?1:-1)*(num(a.dataset.p)-num(b.dataset.p))});arr.forEach(function(c){wrap.appendChild(c)})}
var n=cards.filter(function(c){return!c.hidden}).length;var e=$('#cnt');if(e)e.textContent=n+' sonuç';var em=$('#empty');if(em)em.hidden=n>0}
chips.forEach(function(b){b.onclick=function(){st.f=b.dataset.f;chips.forEach(function(x){x.classList.toggle('on',x==b)});run()}});
var q=$('#fq');if(q)q.oninput=function(){st.q=q.value.toLowerCase();run()};var so=$('#fs');if(so)so.onchange=function(){st.s=so.value;run()};
$$('.fl select[data-key]').forEach(function(x){x.onchange=function(){run2()}});
function run2(){var sel=$$('.fl select[data-key]');cards.forEach(function(c){var ok=true;sel.forEach(function(x){if(x.value&&c.dataset[x.dataset.key]!=x.value)ok=false});c.hidden=!ok});var n=cards.filter(function(c){return!c.hidden}).length;var e=$('#cnt');if(e)e.textContent=n+' sonuç';var em=$('#empty');if(em)em.hidden=n>0}
var pr=o.pre();$$('.fl select[data-key]').forEach(function(x){var v=pr[x.dataset.pre];if(v)for(var i=0;i<x.options.length;i++)if(x.options[i].text.toLowerCase().indexOf(v.toLowerCase())==0)x.selectedIndex=i});run2()};
/* ürün sayfası */
o.product=function(){var b=$('#addc');b.onclick=function(){var d=$('#pd'),opt=$$('[data-opt]',d).map(function(x){return (x.dataset.opt)+': '+x.value}).filter(function(x){return x.split(': ')[1]}).join(' · ');var q=+($('#qty').value||1);o.add({id:d.dataset.id,n:d.dataset.n,p:num(d.dataset.p),img:d.dataset.img,opt:opt,q:q})};
var bn=$('#buyn');if(bn)bn.onclick=function(){b.onclick();location.href='odeme.html'};
$$('.vr button').forEach(function(x){x.onclick=function(){var g=x.parentNode;$$('button',g).forEach(function(y){y.classList.remove('on')});x.classList.add('on');g.dataset.val=x.dataset.v;var inp=$('input[type=hidden]',g);inp.value=x.dataset.v}})};
/* sepet */
o.cartPage=function(){var A=$('#app');function R(){var c=o.cart();if(!c.length){A.innerHTML='<div class="box"><b>Sepetiniz boş.</b><p>Ürünlere göz atıp sepete ekleyin.</p><a class="b p" href="'+A.dataset.shop+'">Alışverişe başla</a></div>';return}
var sub=c.reduce(function(a,x){return a+x.p*x.q},0),cp=sessionStorage.getItem(K+'cp'),ds=cp?Math.round(sub*.1):0;
A.innerHTML='<div class="two"><div class="ci-list">'+c.map(function(x,i){return '<div class="ci"><img src="'+esc(x.img)+'" alt=""><div><b>'+esc(x.n)+'</b>'+(x.opt?'<small>'+esc(x.opt)+'</small>':'')+'</div><div class="qt"><button data-a="-" data-i="'+i+'" aria-label="Azalt">−</button><span>'+x.q+'</span><button data-a="+" data-i="'+i+'" aria-label="Artır">+</button></div><b class="pp2">'+tl(x.p*x.q)+'</b><button class="rm" data-i="'+i+'" aria-label="Sil">✕</button></div>'}).join('')+'</div><aside class="sumbox"><h3>Özet</h3><p><span>Ara toplam</span><b>'+tl(sub)+'</b></p>'+(ds?'<p><span>Kupon (%10)</span><b>−'+tl(ds)+'</b></p>':'')+'<p class="tot"><span>Toplam</span><b>'+tl(sub-ds)+'</b></p><form id="cpn" class="cpn"><input placeholder="Kupon kodu" aria-label="Kupon kodu"><button class="b o s">Uygula</button></form><a class="b p" href="odeme.html">Ödemeye geç</a></aside></div>';
$$('.qt button',A).forEach(function(b){b.onclick=function(){var c=o.cart(),i=+b.dataset.i;c[i].q+=b.dataset.a=='+'?1:-1;if(c[i].q<1)c.splice(i,1);s('cart',c);o.badge();R()}});
$$('.rm',A).forEach(function(b){b.onclick=function(){var c=o.cart();c.splice(+b.dataset.i,1);s('cart',c);o.badge();R()}});
$('#cpn').onsubmit=function(e){e.preventDefault();var v=$('input',e.target).value.trim().toUpperCase();if(v=='HOSGELDIN'){sessionStorage.setItem(K+'cp','1');R();o.toast('Kupon uygulandı')}else o.toast('Kupon geçerli değil')}}R()};
/* ödeme */
o.checkout=function(){var A=$('#app'),c=o.cart();if(!c.length){A.innerHTML='<div class="box"><b>Sepetiniz boş.</b><a class="b p" href="'+A.dataset.shop+'">Alışverişe başla</a></div>';return}
var sub=c.reduce(function(a,x){return a+x.p*x.q},0),ds=sessionStorage.getItem(K+'cp')?Math.round(sub*.1):0;
A.innerHTML='<div class="two"><form id="ck" class="ff"><h3>İletişim</h3><label>Ad soyad<input required data-l="Ad soyad" placeholder="Ad soyad"></label><div class="row2"><label>Telefon<input required data-l="Telefon" inputmode="tel" placeholder="05xx xxx xx xx"></label><label>E-posta<input type="email" data-l="E-posta" placeholder="ornek@eposta.com"></label></div><h3>Teslimat</h3><div class="vr2"><label><input type="radio" name="tt" value="Adrese teslim" checked> Adrese teslim</label><label><input type="radio" name="tt" value="Gel al"> Mağazadan gel al</label></div><label>Adres<textarea required data-l="Adres" rows="2" placeholder="Mahalle, sokak, ilçe"></textarea></label><label>Sipariş notu<input data-l="Not" placeholder="İsterseniz not yazın"></label><h3>Ödeme</h3><div class="vr2"><label><input type="radio" name="od" value="Kartla ödeme" checked> Kartla ödeme (güvenli ödeme sayfası)</label><label><input type="radio" name="od" value="Kapıda ödeme"> Kapıda ödeme</label></div><label class="chk"><input type="checkbox" required> Mesafeli satış sözleşmesini ve iade koşullarını okudum.</label><button class="b p">Siparişi tamamla</button></form><aside class="sumbox"><h3>Siparişiniz</h3>'+c.map(function(x){return '<p><span>'+x.q+' × '+esc(x.n)+'</span><b>'+tl(x.p*x.q)+'</b></p>'}).join('')+(ds?'<p><span>Kupon</span><b>−'+tl(ds)+'</b></p>':'')+'<p class="tot"><span>Toplam</span><b>'+tl(sub-ds)+'</b></p></aside></div>';
$('#ck').onsubmit=function(e){e.preventDefault();var f=e.target,ok=true;$$('[required]',f).forEach(function(i){if(i.type=='checkbox'?!i.checked:!i.value.trim()){ok=false;i.classList.add('bad')}});if(!ok){o.toast('Zorunlu alanları doldurun');return}
var no=o.no('SP');o.save('siparis',{no:no,baslik:c.length+' ürün · '+tl(sub-ds),tur:'siparis',kalemler:c,toplam:sub-ds,ad:$('input',f).value,teslim:$('input[name=tt]:checked',f).value,odeme:$('input[name=od]:checked',f).value,t:Date.now(),durum:0,adimlar:['Sipariş alındı','Hazırlanıyor','Kargoda / yolda','Teslim edildi']});s('cart',[]);sessionStorage.removeItem(K+'cp');o.badge();
A.innerHTML='<div class="box ok2"><h3>Siparişiniz alındı</h3><p>Sipariş numaranız <b>'+no+'</b>. Durumu SMS ile bildiririz.</p><div class="row"><a class="b p" href="hesabim.html">Hesabım</a><a class="b o" href="'+A.dataset.track+'">Siparişi sorgula</a></div></div>'}};
/* hesabım */
o.account=function(){var A=$('#app'),u=g('user',null);
function login(){A.innerHTML='<form id="lg" class="ff box"><h3>Telefonla giriş</h3><label>Telefon<input required placeholder="05xx xxx xx xx" inputmode="tel"></label><label>SMS kodu<input required placeholder="Kod" inputmode="numeric"></label><p class="hint">Önizleme kodu: 1234</p><button class="b p">Giriş yap</button></form>';
$('#lg').onsubmit=function(e){e.preventDefault();var i=$$('input',e.target);if(i[1].value!='1234'){o.toast('Kod hatalı');return}s('user',{tel:i[0].value});u=g('user');R('sip')}}
function R(tab){var ord=o.list('siparis'),ap=o.list('randevu'),kt=o.list('kayit'),ad=g('adres',[]);
function row(x){return '<div class="row3"><b>'+esc(x.no)+'</b><span>'+esc(x.baslik||x.tur)+'</span><span>'+new Date(x.t||x.t0||Date.now()).toLocaleDateString('tr-TR')+'</span></div>'}
var tabs={sip:['Siparişlerim',ord.length?ord.map(row).join(''):'<p class="hint">Henüz sipariş yok.</p>'],ap:['Randevularım',ap.length?ap.map(row).join(''):'<p class="hint">Henüz randevu yok.</p>'],kt:['Taleplerim',kt.length?kt.map(row).join(''):'<p class="hint">Henüz talep yok.</p>'],ad:['Adreslerim',ad.map(function(a,i){return '<div class="row3"><span>'+esc(a)+'</span><button class="rm" data-i="'+i+'">Sil</button></div>'}).join('')+'<form id="af" class="cpn"><input placeholder="Yeni adres" aria-label="Yeni adres" required><button class="b o s">Ekle</button></form>']};
A.innerHTML='<div class="acc"><div class="atabs">'+Object.keys(tabs).map(function(k){return '<button class="'+(k==tab?'on':'')+'" data-t="'+k+'">'+tabs[k][0]+'</button>'}).join('')+'<button id="out">Çıkış</button></div><div class="abody">'+tabs[tab][1]+'</div></div>';
$$('.atabs [data-t]',A).forEach(function(b){b.onclick=function(){R(b.dataset.t)}});$('#out').onclick=function(){L.removeItem(K+'user');login()};
if($('#af'))$('#af').onsubmit=function(e){e.preventDefault();var a=g('adres',[]);a.push($('input',e.target).value);s('adres',a);R('ad')};
$$('.abody .rm').forEach(function(b){b.onclick=function(){var a=g('adres',[]);a.splice(+b.dataset.i,1);s('adres',a);R('ad')}})}
u?R('sip'):login()};
o.init=function(name,D){o.badge();if(name=='form')$$('form[data-kind]').forEach(o.form);if(name=='track')o.track();if(name=='wizard')o.wizard(D);if(name=='filter')o.filter();if(name=='product'){o.product()}if(name=='cart')o.cartPage();if(name=='checkout')o.checkout();if(name=='account')o.account();if(name=='bmi'){o.calc(D)}if(name=='form'&&D&&D.also)o[D.also]&&o[D.also]()};
o.calc=function(D){var f=$('#calc');f.onsubmit=function(e){e.preventDefault();var v=$$('input',f).map(function(i){return parseFloat(i.value.replace(',','.'))});var r=$('#calcr');
if(D.k=='bmi'){var b=v[1]/Math.pow(v[0]/100,2);r.innerHTML='<b>Vücut kitle indeksiniz '+b.toFixed(1).replace('.',',')+'</b><p>'+(b<18.5?'Zayıf aralığı':b<25?'Normal aralık':b<30?'Fazla kilolu aralığı':'Obezite aralığı')+'. Bu bir ön hesaptır; kişisel plan için ön görüşme alın.</p>'}
if(D.k=='kredi'){var P=v[0],n=v[1],i=(v[2]||3)/100,t=P*i*Math.pow(1+i,n)/(Math.pow(1+i,n)-1);r.innerHTML='<b>Aylık taksit: '+tl(Math.round(t))+'</b><p>Toplam geri ödeme '+tl(Math.round(t*n))+'. Faiz oranı aylık yüzde '+(v[2]||3)+' alınarak hesaplandı; bankanızın oranıyla değişir.</p>'}}};
document.addEventListener('DOMContentLoaded',function(){o.badge()});
return o})();
(function(){var R=matchMedia('(prefers-reduced-motion:reduce)').matches;
var h=document.querySelector('.top');addEventListener('scroll',function(){h.classList.toggle('sm',scrollY>40)},{passive:true});
document.querySelectorAll('.in').forEach(function(e){e.classList.add('go')});
if(R){document.querySelectorAll('video').forEach(function(v){v.pause()});return}
var io=new IntersectionObserver(function(es){es.forEach(function(x){if(!x.isIntersecting)return;var t=x.target;io.unobserve(t);t.classList.add('vis');
 if(t.dataset.n!==undefined){var raw=t.dataset.n,m=raw.match(/[\d.,]+/);if(!m)return;var n=parseFloat(m[0].replace(/\./g,'').replace(',','.')),dec=m[0].indexOf(',')>-1||/^\d\.\d$/.test(m[0]),k=0,st=performance.now();
  (function f(now){var p=Math.min(1,(now-st)/1400),v=n*(1-Math.pow(1-p,3));var s=dec?v.toFixed(1):Math.round(v).toLocaleString('tr-TR');t.textContent=raw.replace(m[0],s);if(p<1)requestAnimationFrame(f)})(st)}})},{threshold:.25});
document.querySelectorAll('.hd,.gl img,b[data-n]').forEach(function(e,i){e.classList.add('rv0');e.style.transitionDelay=(i%4)*70+'ms';io.observe(e)});
document.querySelectorAll('.sl1').forEach(function(s){var k=0;setInterval(function(){k=(k+1)%s.children.length;s.scrollTo({left:s.children[k].offsetLeft-s.offsetLeft,behavior:'smooth'})},4200)});
})();OK.init("x",null);