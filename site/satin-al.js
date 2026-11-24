(function(){
"use strict";
var $=function(i){return document.getElementById(i)},API="/api/public/satin-al/";
var D=null,busy=false,q=new URLSearchParams(location.search);
function tl(n){n=Number(n)||0;return n.toLocaleString("tr-TR",{minimumFractionDigits:n%1?2:0,maximumFractionDigits:2})+" ₺"}
function hata(m){var e=$("err");e.textContent=m||"";e.classList.toggle("on",!!m)}
function js(u,o){return fetch(u,o).then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok){var d=j&&j.detail;throw new Error(typeof d==="string"?d:(Array.isArray(d)?"Formu kontrol edin":"İstek tamamlanamadı"))}return j})})}
function sure(){return document.querySelector('input[name=sure]:checked').value}
function paket(){var c=document.querySelector('input[name=paket]:checked');return c?c.value:""}
function yontem(){var c=document.querySelector('input[name=yontem]:checked');return c?c.value:""}
function bul(id){for(var i=0;i<D.paketler.length;i++)if(D.paketler[i].id===id)return D.paketler[i]}
function ozet(){
  var p=bul(paket());if(!p)return;var f=p[sure()];
  $("o1").textContent=p.name+" · "+({aylik:"aylık",yillik:"yıllık",iki_yil:"2 yıllık"}[sure()]);$("o2").textContent=tl(f.matrah);
  $("okd").textContent="KDV %"+f.kdv_oran;$("o3").textContent=tl(f.kdv);$("o4").textContent=tl(f.toplam);$("ob").textContent=tl(f.toplam);
  var hg=D.hediye&&D.hediye.gun?Math.round(D.hediye.gun/365):0,hi=$("hedi");if(hi){hi.textContent=hg?"+"+hg+" yıl hediye":"";hi.style.display=hg?"":"none"}
  $("o5").textContent=sure()==="yillik"?"Yıllık ödemede aylık "+tl(p.aylik.matrah)+" yerine "+tl(p.yillik.matrah/12)+"'ye denk gelir.":sure()==="iki_yil"?(hg?D.hediye.ad+" kampanyası: 2 yıl ödersiniz, "+(2+hg)+" yıl kullanırsınız. Aylık "+tl(f.matrah/(24+12*hg))+"'ye denk gelir.":"2 yıllık ödemede aylık "+tl(f.matrah/24)+"'ye denk gelir."):"";
  var a=p.aylik.matrah*12,y=p.yillik.matrah,k=a>0?Math.round((a-y)/p.aylik.matrah):0;
  $("hed").textContent=k>0?k+" ay hediye":"";$("hed").style.display=k>0?"":"none";
  var l=document.querySelectorAll("#pk label");for(var i=0;i<l.length;i++){var pp=bul(l[i].getAttribute("for").slice(3));l[i].querySelector("em").textContent=tl(pp[sure()].matrah)+(sure()==="yillik"?" /yıl":sure()==="iki_yil"?" /2 yıl":" /ay")}
}
function ciz(){
  var pk=$("pk");pk.textContent="";
  var on=bul(q.get("paket"))?q.get("paket"):(bul("profesyonel")?"profesyonel":D.paketler[0].id);
  D.paketler.forEach(function(p){
    var i=document.createElement("input");i.type="radio";i.name="paket";i.id="pk-"+p.id;i.value=p.id;i.checked=p.id===on;
    var l=document.createElement("label");l.setAttribute("for",i.id);
    var e=document.createElement("em"),b=document.createElement("b"),s=document.createElement("small");
    b.textContent=p.name;s.textContent=p.tagline||(p.modules?p.modules+" modül":"");l.appendChild(e);l.appendChild(b);l.appendChild(s);
    pk.appendChild(i);pk.appendChild(l);i.addEventListener("change",ozet)});
  var se=$("sektor");D.sektorler.forEach(function(s){var o=document.createElement("option");o.value=s.id;o.textContent=s.ad;se.appendChild(o)});
  if(q.get("sektor"))se.value=q.get("sektor");
  if(q.get("sure")==="aylik")$("su-a").checked=true;
  var Y=D.yontemler,yn=$("yn"),n=0;
  function sec(v,t,a,on){var l=document.createElement("label"),i=document.createElement("input");i.type="radio";i.name="yontem";i.value=v;i.checked=on;
    var d=document.createElement("div"),b=document.createElement("b"),s=document.createElement("small");b.textContent=t;s.textContent=a;d.appendChild(b);d.appendChild(s);l.appendChild(i);l.appendChild(d);yn.appendChild(l);i.addEventListener("change",yg);n++}
  if(Y.kart)sec("kart","Kredi / banka kartı","iyzico güvenli ödeme ekranı, taksit seçenekleri kart ekranında",true);
  if(Y.havale)sec("havale","Havale / EFT","Siparişten sonra IBAN gösterilir; ödemeniz onaylanınca paneliniz açılır",!Y.kart);
  if(!n){yn.innerHTML="";var d=document.createElement("div");d.className="pay";d.innerHTML="<b>Online ödeme şu an kapalı</b>Siparişi buradan veremiyoruz. Lütfen <a href=\"/iletisim.html\">bize yazın</a>, size ödeme bağlantısı iletelim.";yn.appendChild(d);$("go").disabled=$("go2").disabled=true}
  yg();$("yuk").hidden=true;$("ic").hidden=false;ozet();
}
function yg(){$("paykart").hidden=yontem()!=="kart"}
function dogru(){
  var bad=0,F=document.querySelectorAll("[data-f]");
  function at(n,ok){var d=document.querySelector('[data-f="'+n+'"]');d.classList.toggle("bad",!ok);if(!ok)bad++}
  var v=function(n){return(document.querySelector('[name="'+n+'"]').value||"").trim()};
  at("ad",v("ad").length>=3);at("firma",v("firma").length>=2);at("telefon",v("telefon").replace(/\D/g,"").length>=10);
  at("email",/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(v("email")));at("sektor",!!v("sektor"));at("vergi_dairesi",v("vergi_dairesi").length>=2);
  at("vergi_no",/^\d{10}$|^\d{11}$/.test(v("vergi_no")));at("il",v("il").length>=2);at("adres",v("adres").length>=8);at("kabul",$("kabul").checked);
  if(bad){var f=document.querySelector(".f.bad input,.f.bad select");if(f)f.focus()}
  return !bad;
}
function kilit(b){busy=b;$("go").disabled=$("go2").disabled=b;$("go").textContent=b?"Hazırlanıyor…":"Ödemeye geç"}
function gonder(e){
  e.preventDefault();if(busy)return;hata("");if(!dogru()){hata("Kırmızı işaretli alanları düzeltin.");return}
  var v=function(n){return(document.querySelector('[name="'+n+'"]').value||"").trim()};
  var g={ad:v("ad"),firma:v("firma"),email:v("email"),telefon:v("telefon"),vergi_no:v("vergi_no"),vergi_dairesi:v("vergi_dairesi"),adres:v("adres"),il:v("il"),sektor:v("sektor"),paket:paket(),sure:sure(),kabul:true};
  var ym=yontem();kilit(true);$("s3").className="on";
  js(API+"siparis",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(g)}).then(function(o){
    $("yen").classList.toggle("on",o.tur==="yenileme");
    try{sessionStorage.setItem("ok_sip",JSON.stringify({no:o.no,k:o.k}))}catch(_){}
    return js(API+"odeme",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({no:o.no,k:o.k,yontem:ym})}).then(function(r){
      var son="/satin-al-sonuc.html?no="+encodeURIComponent(o.no)+"&k="+encodeURIComponent(o.k);
      if(r.yontem==="havale")return havale(r,o,son);
      if(r.url){location.href=r.url;return}
      if(r.form){$("iyz").innerHTML=r.form;var S=$("iyz").querySelectorAll("script");S.forEach(function(s){var n=document.createElement("script");if(s.src)n.src=s.src;else n.text=s.text;s.parentNode.replaceChild(n,s)});$("iyz").scrollIntoView({behavior:"smooth"});kilit(false);return}
      throw new Error("Ödeme ekranı açılamadı")})
  }).catch(function(x){kilit(false);$("s3").className="";hata(x.message||"Bir sorun oluştu, lütfen tekrar deneyin.")});
}
function havale(r,o,son){
  var h=$("hv"),H=r.havale||{};h.textContent="";h.classList.add("on");
  var t=document.createElement("b");t.textContent="Havale / EFT bilgileri";h.appendChild(t);
  var dl=document.createElement("dl");function sat(a,b){var x=document.createElement("dt"),y=document.createElement("dd");x.textContent=a;y.textContent=b;dl.appendChild(x);dl.appendChild(y)}
  sat("Alıcı",H.unvan||"");if(H.banka)sat("Banka",H.banka);sat("IBAN",H.iban||"");sat("Tutar",tl(o.fiyat.toplam));sat("Açıklama",r.aciklama||o.no);h.appendChild(dl);
  var p=document.createElement("p");p.textContent="Açıklama alanına sipariş numaranızı yazın. Ödemeniz kontrol edilince paneliniz açılır ve giriş bilgileriniz e-postanıza gelir.";h.appendChild(p);
  var c=document.createElement("button");c.type="button";c.textContent="IBAN'ı kopyala";c.onclick=function(){try{navigator.clipboard.writeText(H.iban||"");c.textContent="Kopyalandı"}catch(_){}};h.appendChild(c);
  var a=document.createElement("a");a.href=son;a.textContent=" Sipariş durumunu gör";a.style.marginLeft="14px";h.appendChild(a);
  h.scrollIntoView({behavior:"smooth"});$("go").hidden=true;$("go2").hidden=true;kilit(false);$("go").disabled=true;
}
js(API+"paketler").then(function(d){if(!d.paketler||!d.paketler.length)throw new Error("Satışa açık paket yok");D=d;ciz()}).catch(function(x){$("yuk").innerHTML="";var s=document.createElement("span");s.textContent="Paketler şu an yüklenemedi. Lütfen sayfayı yenileyin ya da ";var a=document.createElement("a");a.href="/iletisim.html";a.textContent="bize yazın";$("yuk").appendChild(s);$("yuk").appendChild(a);$("yuk").append(".")});
document.querySelectorAll('input[name=sure]').forEach(function(i){i.addEventListener("change",ozet)});
$("sf").addEventListener("submit",gonder);
})();
