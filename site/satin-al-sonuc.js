(function(){
"use strict";
var $=function(i){return document.getElementById(i)},q=new URLSearchParams(location.search),no=q.get("no")||"",k=q.get("k")||"";
if(!no||!k){try{var s=JSON.parse(sessionStorage.getItem("ok_sip")||"{}");no=no||s.no||"";k=k||s.k||""}catch(_){}}
var n=0,tm=null,tl=function(v){v=Number(v)||0;return v.toLocaleString("tr-TR",{minimumFractionDigits:v%1?2:0,maximumFractionDigits:2})+" ₺"};
function durumYaz(c,b,a){$("tk").className="tik "+c;$("bs").textContent=b;$("al").textContent=a}
function sat(a,b){var d=document.createElement("div"),x=document.createElement("span"),y=document.createElement("b");x.textContent=a;y.textContent=b;d.appendChild(x);d.appendChild(y);$("cp").appendChild(d)}
function dugme(t,h,i){var a=document.createElement("a");a.className="btn"+(i?" ikinci":"");a.href=h;a.textContent=t;$("ak").appendChild(a)}
function ozet(o){$("cp").hidden=false;$("cp").textContent="";sat("Sipariş no",o.no);sat("Paket",o.paket_ad+" · "+({aylik:"aylık",yillik:"yıllık",iki_yil:"2 yıllık"}[o.sure]||"")+(o.hediye_gun?" + "+Math.round(o.hediye_gun/365)+" yıl hediye":""));sat("Tutar (KDV dahil)",tl(o.toplam));if(o.fatura_no)sat("Fatura no",o.fatura_no);if(o.bitis)sat("Kullanım bitişi",o.bitis.slice(0,10).split("-").reverse().join("."))}
function adim(L){$("nx").hidden=false;$("nx").textContent="";L.forEach(function(t,i){var p=document.createElement("p"),b=document.createElement("b"),s=document.createElement("span");b.textContent=i+1;s.textContent=t;p.appendChild(b);p.appendChild(s);$("nx").appendChild(p)})}
function ciz(o){
  $("ak").textContent="";ozet(o);var d=o.durum;
  if(d==="tamamlandi"){
    durumYaz("y",o.tur==="yenileme"?"Hesabınız yenilendi":"Ödemeniz alındı, paneliniz hazır","Teşekkürler. "+(o.tur==="yenileme"?"Mevcut hesabınızın süresi uzatıldı.":"Giriş bilgileriniz "+o.email+" adresine gönderildi."));
    adim(o.tur==="yenileme"?["Mevcut şifrenizle panele girin; yeni süreniz tanımlandı.","Faturanız e-postanıza gönderildi, aşağıdan da indirebilirsiniz.","Şifrenizi unuttuysanız giriş ekranındaki bağlantıyı kullanın."]:["E-postanızdaki kullanıcı adı ve şifreyle panele girin.","Panelde sektörünüze göre hazır gelen ayarları gözden geçirin.","Faturanız e-postanıza gönderildi, aşağıdan da indirebilirsiniz."]);
    dugme("Panele giriş yap","/panel/");if(o.fatura_no)dugme("Faturayı indir","/api/public/satin-al/fatura/"+encodeURIComponent(o.no)+".pdf?k="+encodeURIComponent(k),1);return true}
  if(d==="havale_bekliyor"){durumYaz("b","Havale ödemeniz bekleniyor","Ödemeniz bize ulaşıp onaylanınca paneliniz açılır ve giriş bilgileriniz "+o.email+" adresine gelir. Açıklamaya "+o.no+" yazmayı unutmayın.");adim(["Havale/EFT ile tutarı gönderin.","Ödeme kontrol edilir; genelde iş saatlerinde aynı gün.","Giriş bilgileriniz ve faturanız e-postanıza gelir."]);return false}
  if(d==="isleniyor"||d==="odeme_bekliyor"&&n<6){durumYaz("b","Ödemeniz doğrulanıyor","Bu birkaç saniye sürer, sayfayı kapatmayın.");return false}
  if(d==="isleme_hatasi"){durumYaz("h","Ödemeniz alındı, kurulum tamamlanamadı","Endişelenmeyin, ödemeniz kaydedildi. Ekibimiz sipariş numaranızla kurulumu tamamlayacak ve size e-posta gönderecek.");dugme("Bize yazın","/iletisim.html");return true}
  if(d==="basarisiz"){durumYaz("h","Ödeme tamamlanamadı","Kartınızdan çekim yapılmadı. "+(o.hata||"Başka bir kartla tekrar deneyebilirsiniz."));dugme("Tekrar dene","/satin-al.html");return true}
  if(d==="iptal"){durumYaz("h","Sipariş iptal edildi","Yeni bir sipariş oluşturabilirsiniz.");dugme("Yeniden sipariş ver","/satin-al.html");return true}
  durumYaz("h","Ödeme tamamlanmadı","Ödeme ekranından ayrıldıysanız kart çekimi yapılmamıştır. İsterseniz yeniden deneyin.");dugme("Ödemeye dön","/satin-al.html");return true;
}
function sor(){
  fetch("/api/public/satin-al/durum?no="+encodeURIComponent(no)+"&k="+encodeURIComponent(k)).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(o){
    var son=ciz(o);n++;if(!son&&n<90)tm=setTimeout(sor,n<10?2000:6000)}).catch(function(){
    durumYaz("h","Sipariş bulunamadı","Bağlantı eksik ya da hatalı. E-postanızdaki sipariş bağlantısını kullanın ya da bize yazın.");$("ak").textContent="";dugme("Bize yazın","/iletisim.html")});
}
if(!no||!k){durumYaz("h","Sipariş bulunamadı","Sipariş bağlantısı eksik.");dugme("Fiyatlara dön","/fiyatlar.html")}else sor();
})();
