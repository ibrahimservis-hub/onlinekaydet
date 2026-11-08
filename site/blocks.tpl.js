(function(){
var TH=/*THEMES*/[];
var SEC={kombi:["Kombi","kombi servisi","{c}'de kombi arızası mı?","Aynı gün yanınızda.","Bakım, arıza ve parça değişimi. Randevunuzu online alın, ustamız yola çıkınca SMS gelsin."],
klima:["Klima","klima servisi","{c}'de klima mı bozuldu?","Yazdan önce hazır olsun.","Montaj, bakım ve gaz dolumu. Randevunuzu online alın, servis durumunu telefondan izleyin."],
beyaz_esya:["Beyaz eşya","beyaz eşya servisi","{c}'de makineniz mi durdu?","Aynı gün evinizdeyiz.","Çamaşır, bulaşık ve buzdolabı onarımı. Randevu alın, ustanız yola çıkınca haber verelim."],
elektronik:["Elektronik","elektronik servisi","{c}'de TV ve cihaz onarımı","Yetkili titizliğiyle.","Arıza kaydınızı açın, onarım sürecini ve fiyat teklifini telefondan takip edin."],
bilgisayar:["Bilgisayar","bilgisayar servisi","{c}'de bilgisayar ve telefon onarımı","Cihazınız emin ellerde.","Arıza kaydı, fiyat teklifi ve teslim bildirimi tek yerde. Onarım durumunu canlı izleyin."],
tesisat:["Tesisat","tesisat servisi","{c}'de su kaçağı ve tesisat","Hemen yola çıkıyoruz.","Kaçak tespiti, tıkanıklık ve armatür değişimi. Ustanın nerede olduğunu canlı görün."],
elektrik:["Elektrik","elektrik servisi","{c}'de elektrik arızası","Güvenle çözüyoruz.","Arıza, pano ve aydınlatma işleri. Randevu alın, iş bitince imzalı fiş SMS ile gelsin."],
guvenlik:["Güvenlik","güvenlik sistemleri","{c}'de kamera ve alarm sistemi","Evinizi biz izleyelim.","Kamera, alarm ve geçiş sistemleri için kurulum ve bakım. Servis kaydınızı online izleyin."]};
var $=function(i){return document.getElementById(i)};
function slug(s){return s.toLowerCase().replace(/ğ/g,'g').replace(/ü/g,'u').replace(/ş/g,'s').replace(/ı/g,'i').replace(/ö/g,'o').replace(/ç/g,'c').replace(/[^a-z0-9]+/g,'').slice(0,28)}
function tl(n){return Math.round(n).toLocaleString('tr-TR')+' ₺'}
function toForm(extra,firm,sector){window.OK_CTX=extra||{};var f=document.querySelector('#kayit .frm');if(f){var ins=f.querySelectorAll('input');if(firm&&ins[2])ins[2].value=firm;var s=f.querySelector('select');if(s&&sector){for(var i=0;i<s.options.length;i++)if(s.options[i].text===sector)s.selectedIndex=i}}
 var k=$('kayit');if(k)k.scrollIntoView({behavior:'smooth',block:'start'});var n=f&&f.querySelector('input');if(n)setTimeout(function(){n.focus({preventScroll:true})},600)}
/* 1 önizleme */
if($('pvx')){var cur='kombi',ti=0,order=Object.keys(SEC);
 function secs(){$('pvs').innerHTML=order.map(function(k){return '<button type="button" data-k="'+k+'" class="'+(k===cur?'on':'')+'">'+SEC[k][0]+'</button>'}).join('')}
 function sws(){var L=TH.filter(function(t){return t.sector===cur});$('pvt').innerHTML=L.map(function(t,i){return '<button type="button" aria-label="Tema '+(i+1)+'" data-i="'+i+'" class="'+(i===ti?'on':'')+'" style="background:'+t.accent+'"></button>'}).join('')}
 function draw(){var L=TH.filter(function(t){return t.sector===cur}),t=L[ti]||L[0],c=SEC[cur],name=($('pvn').value||'Firma adınız').trim(),city=($('pvc').value||'Şehriniz').trim(),x=$('pvx');
  x.style.setProperty('--d',t.dark);x.style.setProperty('--a',t.accent);x.style.setProperty('--s',t.soft);
  var dark=parseInt(t.soft.slice(1,3),16)<90;x.style.setProperty('--s',dark?t.dark:t.soft);
  $('pv1').textContent=name;$('pv2').textContent=city+' '+c[1];$('pv3').innerHTML='';var a=document.createElement('span');a.textContent=c[2].replace('{c}',city)+' ';var e=document.createElement('em');e.textContent=c[3];$('pv3').appendChild(a);$('pv3').appendChild(e);
  $('pv3').style.color=dark?'#fff':t.dark;$('pv4').textContent=c[4];$('pv4').style.color=dark?'#c9d4ee':'#5d6985';x.querySelector('.hr').style.background='transparent';
  $('pvu').textContent=(slug(name)||'firmaniz')+'.com';}
 $('pvs').onclick=function(e){var b=e.target.closest('button');if(!b)return;cur=b.dataset.k;ti=0;secs();sws();draw()};
 $('pvt').onclick=function(e){var b=e.target.closest('button');if(!b)return;ti=+b.dataset.i;sws();draw()};
 $('pvn').oninput=draw;$('pvc').oninput=draw;
 $('pvg').onclick=function(){var L=TH.filter(function(t){return t.sector===cur}),t=L[ti]||L[0];toForm({tema:t.slug,onizleme:'evet'},$('pvn').value.trim(),SEC[cur][0])};
 secs();sws();draw()}
/* 2 hesap */
if($('c1')){function calc(){var a=+$('c1').value,o=+$('c2').value/100,u=+$('c3').value,t=+$('c4').value/100;
  $('c1v').textContent=a;$('c2v').textContent='%'+Math.round(o*100);$('c3v').textContent=tl(u);$('c4v').textContent='%'+Math.round(t*100);
  var kacan=a*o,kal=a-kacan,tahsil=kal*u*t,kayip=kacan*u+tahsil;
  $('cr').innerHTML=Math.round(kayip).toLocaleString('tr-TR')+'<span> ₺</span>';$('cy').textContent='Yılda yaklaşık '+tl(kayip*12);$('ck').textContent=Math.round(kacan)+' servis ('+tl(kacan*u)+')';$('ct').textContent=tl(tahsil)}
 ['c1','c2','c3','c4'].forEach(function(i){$(i).oninput=calc});calc();
 $('cg').onclick=function(){toForm({hesap_kayip_aylik:Math.round((+$('c1').value*(+$('c2').value/100))*+$('c3').value+((+$('c1').value)*(1-(+$('c2').value/100)))*+$('c3').value*(+$('c4').value/100)),arama:+$('c1').value},'','')}}
/* 3 sihirbaz */
if($('wq')){var Q=[["Ekibinizde kaç usta çalışıyor?",["Tek başıma çalışıyorum","2–5 usta","6 ve üzeri"]],["Kendi web sitenizden online satış veya hazır site istiyor musunuz?",["Hayır, yalnızca servis takibi","Evet, site ve online satış istiyorum"]],["Müşteriden online ödeme, e-arşiv fatura veya bayi/portal gerekiyor mu?",["Şimdilik gerekmiyor","Evet, gerekiyor"]]];
 var PK={baslangic:["Başlangıç","990",["Servis kaydı ve cihaz kataloğu","Personel ve usta uygulaması","PDF servis fişi"]],profesyonel:["Profesyonel","1.990",["Başlangıçtaki her şey","Otomatik SMS ve mesaj şablonları","Muhasebe ve kasa takibi","Raporlar"]],tam:["Tam Paket","3.490",["Profesyonel'deki her şey","Yedek parça mağazası","Temalı web sitesi ve SEO","Pazarlama ve kampanya araçları"]],kurumsal:["Kurumsal","5.990",["Tam Paket'teki her şey","Periyodik bakım hatırlatma ve garanti takibi","Teklif ve müşteri onayı","Ödeme linki ve e-arşiv fatura","Müşteri portalı, canlı usta takibi","Bayi (B2B) ve QR cihaz etiketi"]]};
 var A=[],step=0;
 function pick(){var e=A[0]||0,s=A[1]||0,k=A[2]||0;return(k===1||e===2)?'kurumsal':(s===1)?'tam':(e===1)?'profesyonel':'baslangic'}
 function show(r,final){var p=PK[r];$('wn').textContent=p[0];$('wp').innerHTML=p[1]+' ₺<small> /ay + KDV</small>';$('wl').innerHTML=p[2].map(function(x){return '<li>'+x+'</li>'}).join('');$('we').textContent=final?'SİZE UYGUN PAKET':'ŞU ANKİ ÖNERİ'}
 function draw(){var done=step>=Q.length;[].forEach.call($('wsp').children,function(i,n){i.className=n<=Math.min(step,2)&&!(done&&false)?'on':''});
  if(done){$('wq').textContent='Cevaplarınıza göre önerimiz yandaki paket.';$('wo').innerHTML='';}else{$('wq').textContent=Q[step][0];$('wo').innerHTML=Q[step][1].map(function(o,i){return '<button type="button" class="op'+(A[step]===i?' on':'')+'" data-i="'+i+'"><i></i>'+o+'</button>'}).join('')}
  $('wb').hidden=step===0;show(pick(),done)}
 $('wo').onclick=function(e){var b=e.target.closest('button');if(!b)return;A[step]=+b.dataset.i;step++;draw()};
 $('wb').onclick=function(){if(step>0){step--;A.length=step;draw()}};
 $('wg').onclick=function(){var r=pick();toForm({paket:r,sihirbaz:'evet'},'','')};
 draw()}
})();
