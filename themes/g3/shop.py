"""Online mağaza bölümü: ürün ızgarası (arama, kategori, marka, sıralama), sepet çekmecesi, sipariş formu.
Ürünler örnektir; fiyat ve stok firma panelinden girilir. Sipariş /api/public/contact'a 'siparis' tipiyle düşer."""
import json
from .base import ic
from .navs import TEL, TELRAW, ed

# (kod, ad, uyumlu, kategori, fiyat, stok: 2 var / 1 az / 0 yok)
PRODUCTS = {
 'kombi': [
  ('KP-1042', 'Eşanjör (ikincil) 12 plaka', 'Baymak, Demirdöküm, ECA', 'Eşanjör', 1450, 2), ('KP-2210', '3 yollu vana motoru', 'Vaillant, Bosch, Buderus', 'Vana', 890, 2),
  ('KP-3318', 'Genleşme tankı 8 lt', 'Tüm markalar (evrensel)', 'Tank', 640, 2), ('KP-4105', 'Sirkülasyon pompası 6 m', 'Baymak, Ariston, ECA', 'Pompa', 2150, 1),
  ('KP-5521', 'Ana kart (PCB)', 'Demirdöküm Nitromix', 'Elektronik', 3200, 1), ('KP-6034', 'Ateşleme elektrodu', 'Vaillant, Bosch', 'Elektronik', 210, 2),
  ('KP-7102', 'Fan motoru 230V', 'ECA Proteus, Baymak', 'Fan', 1380, 2), ('KP-8210', 'Basınç sensörü', 'Buderus, Viessmann', 'Sensör', 520, 2),
  ('KP-9004', 'Doldurma musluğu seti', 'Tüm markalar (evrensel)', 'Vana', 185, 2), ('KP-9140', 'Kombi sensör NTC 10K', 'Baymak, ECA, Bosch', 'Sensör', 140, 2),
  ('KP-9333', 'Gaz valfi', 'Vaillant, Ariston', 'Vana', 2740, 0), ('KP-9451', 'Conta ve o-ring seti', 'Tüm markalar (evrensel)', 'Sarf', 95, 2)],
 'klima': [
  ('KL-1101', 'Kapasitör 35 µF', 'Tüm split klimalar', 'Elektrik', 160, 2), ('KL-1204', 'İç ünite fan motoru', 'Arçelik, Vestel, Samsung', 'Motor', 980, 2),
  ('KL-1320', 'Dış ünite fan motoru', 'Daikin, LG, Mitsubishi', 'Motor', 1450, 1), ('KL-1411', 'Uzaktan kumanda (evrensel)', 'Tüm markalar', 'Aksesuar', 220, 2),
  ('KL-1510', 'Oda ısı sensörü', 'Airfel, Bosch, Vestel', 'Sensör', 120, 2), ('KL-1622', 'Kompresör rölesi', 'LG, Samsung', 'Elektrik', 240, 2),
  ('KL-1710', 'R32 gaz tüpü 1 kg', 'R32 kullanan modeller', 'Gaz', 780, 1), ('KL-1815', 'Bakır boru 1/4 - 3/8 çift (3 m)', 'Tüm markalar', 'Montaj', 960, 2),
  ('KL-1902', 'Dış ünite montaj konsolu', 'Tüm markalar', 'Montaj', 540, 2), ('KL-2003', 'Drenaj pompası', 'Salon tipi / duvar tipi', 'Pompa', 1260, 0),
  ('KL-2110', 'Ana kart (inverter)', 'Daikin, Mitsubishi', 'Elektronik', 3650, 1), ('KL-2204', 'Filtre seti (2 adet)', 'Arçelik, Vestel', 'Sarf', 150, 2)],
 'beyaz_esya': [
  ('BE-1010', 'Çamaşır mak. kayışı 1192 J5', 'Arçelik, Beko', 'Kayış', 130, 2), ('BE-1120', 'Kömür (fırça) çifti', 'Bosch, Siemens, Arçelik', 'Motor', 150, 2),
  ('BE-1245', 'Amortisör takımı (4 lü)', 'Arçelik, Vestel', 'Süspansiyon', 480, 2), ('BE-1332', 'Su giriş valfi çift yollu', 'Tüm markalar', 'Valf', 260, 2),
  ('BE-1410', 'Drenaj pompası', 'Bosch, Arçelik, Vestel', 'Pompa', 540, 1), ('BE-1520', 'Bulaşık mak. sirkülasyon motoru', 'Bosch, Beko', 'Motor', 1180, 1),
  ('BE-1604', 'Buzdolabı defrost rezistansı', 'Arçelik, Bosch', 'Rezistans', 360, 2), ('BE-1710', 'Buzdolabı kapı contası', 'Model seçimiyle', 'Conta', 420, 2),
  ('BE-1805', 'Termostat', 'Bulaşık / çamaşır mak.', 'Elektronik', 190, 2), ('BE-1912', 'Kapak kilidi (çamaşır)', 'Arçelik, Beko', 'Kilit', 210, 2),
  ('BE-2020', 'Elektronik kart', 'Arçelik 7112', 'Elektronik', 1450, 0), ('BE-2118', 'Kurutma mak. kondenser', 'Bosch, Beko', 'Kurutma', 860, 1)],
 'tesisat': [
  ('TS-1001', 'Rakor seti 1/2 (10 lu)', 'Tüm tesisat', 'Bağlantı', 120, 2), ('TS-1102', 'Fotoselli batarya', 'Evye / lavabo', 'Armatür', 1250, 2),
  ('TS-1210', 'Şamandıra mekanizması', 'Gizli / harici rezervuar', 'Rezervuar', 190, 2), ('TS-1305', 'Sifon bakır nikelajlı', 'Lavabo', 'Atık su', 150, 2),
  ('TS-1411', 'Su sayacı bağlantısı', 'DN15', 'Bağlantı', 210, 2), ('TS-1502', 'Pis su pompası', 'Bodrum / banyo', 'Pompa', 2750, 1),
  ('TS-1620', 'Hidrofor 1 HP', 'Müstakil / site', 'Pompa', 4950, 1), ('TS-1708', 'Basınç düşürücü', 'DN15 / DN20', 'Valf', 780, 2),
  ('TS-1812', 'PPR boru 20 mm (4 m)', 'Sıcak / soğuk su', 'Boru', 85, 2), ('TS-1910', 'Termostatik radyatör vanası', 'Petek', 'Valf', 340, 2),
  ('TS-2005', 'Kaçak tespit spreyi', 'Tüm tesisat', 'Sarf', 95, 0), ('TS-2102', 'Su filtresi 10"', 'Mutfak / ev girişi', 'Filtre', 320, 2)],
 'guvenlik': [
  ('GV-1001', '2 MP IP güvenlik kamerası', 'PoE, gece görüşlü', 'Kamera', 1450, 2), ('GV-1102', '4 MP dome kamera', 'PoE', 'Kamera', 1850, 2),
  ('GV-1205', '8 kanal NVR kayıt cihazı', '4 TB diske kadar', 'Kayıt', 4400, 1), ('GV-1310', '4 TB güvenlik diski', 'NVR / DVR', 'Depolama', 3250, 2),
  ('GV-1402', 'PoE switch 8 port', 'IP kameralar', 'Ağ', 1650, 2), ('GV-1520', 'Kablosuz alarm seti', 'Ev / işyeri', 'Alarm', 2950, 1),
  ('GV-1610', 'Hareket sensörü (PIR)', 'Alarm sistemleri', 'Sensör', 380, 2), ('GV-1704', 'Kapı manyetik kontağı', 'Alarm sistemleri', 'Sensör', 120, 2),
  ('GV-1812', 'Görüntülü diyafon seti', 'Daire / villa', 'Diyafon', 3900, 1), ('GV-1920', 'Cat6 kablo 100 m', 'Kamera bağlantısı', 'Kablo', 1250, 2),
  ('GV-2008', 'Sirenli flaşör', 'Alarm sistemleri', 'Alarm', 460, 0), ('GV-2110', '12V 2A adaptör', 'Analog kamera', 'Güç', 140, 2)],
 'elektrik': [
  ('EL-1001', 'Otomat sigorta 16A C', 'Tek faz', 'Sigorta', 85, 2), ('EL-1105', 'Kaçak akım rölesi 25A 30mA', 'Ev tipi', 'Koruma', 520, 2),
  ('EL-1210', 'NYM kablo 3x2,5 mm² (100 m)', 'Priz hattı', 'Kablo', 3450, 2), ('EL-1312', 'Topraklı priz (10 lu)', 'Beyaz seri', 'Anahtar-priz', 380, 2),
  ('EL-1410', 'Ledli panel armatür 60x60', '40 W günışığı', 'Aydınlatma', 560, 1), ('EL-1520', 'Duvar tipi sigorta kutusu 12 li', 'Ev tipi', 'Pano', 320, 2),
  ('EL-1604', 'Kontaktör 25A', 'Tek / üç faz', 'Pano', 460, 2), ('EL-1710', 'Zaman rölesi', 'Merdiven aydınlatma', 'Röle', 310, 2),
  ('EL-1802', 'Parafudr (gerilim koruma)', 'Pano girişi', 'Koruma', 980, 1), ('EL-1920', 'Kablo kanalı 25x16 (2 m)', 'Tüm tesisat', 'Aksesuar', 70, 2),
  ('EL-2001', 'Fotoselli sensör', 'Dış mekân', 'Sensör', 240, 0), ('EL-2108', 'Sayaç yanı pano seti', 'Dağıtım', 'Pano', 1850, 2)],
 'elektronik': [
  ('EK-1001', 'TV arka aydınlatma LED şerit', '40-43 inç', 'TV', 380, 2), ('EK-1102', 'TV güç kartı', 'Samsung, LG, Vestel', 'TV', 1250, 1),
  ('EK-1210', 'Ana kart (T-Con)', '43 inç 4K', 'TV', 960, 1), ('EK-1312', 'HDMI kablo 2.1 (2 m)', 'Tüm cihazlar', 'Kablo', 190, 2),
  ('EK-1405', 'Uzaktan kumanda', 'Samsung, LG', 'Aksesuar', 220, 2), ('EK-1510', 'Duvar askı aparatı', '32-65 inç', 'Aksesuar', 340, 2),
  ('EK-1620', 'Uydu alıcı LNB', 'Tek çıkışlı', 'Uydu', 260, 2), ('EK-1710', 'Hoparlör çifti 8 Ω', 'Soundbar / TV', 'Ses', 410, 1),
  ('EK-1802', 'Kondansatör seti', 'Güç kartı onarımı', 'Elektronik', 150, 2), ('EK-1910', 'Mikrofon / uzaktan kumanda pili', 'Genel', 'Sarf', 60, 2),
  ('EK-2005', 'Panel (ekran) 32 inç', 'Model seçimiyle', 'TV', 3250, 0), ('EK-2110', 'Anten kablosu 10 m', 'Tüm cihazlar', 'Kablo', 110, 2)],
}

SHOPCSS = """
.shp .bar{display:grid;grid-template-columns:1.4fr auto auto;gap:12px;margin:0 0 18px;align-items:center}.shp .bar input,.shp .bar select{width:100%;min-height:50px;padding:0 16px;background:var(--fbg);border:1px solid var(--ln);border-radius:var(--r);font:500 .96rem var(--fb);color:var(--ink)}
.shp .cat{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:26px}.shp .cat button{min-height:40px;padding:0 16px;border-radius:99px;border:1px solid var(--ln);background:transparent;color:var(--ink);font:600 .86rem var(--fb);cursor:pointer;transition:.2s}.shp .cat button.on,.shp .cat button:hover{background:var(--dk);color:#fff;border-color:var(--dk)}
.shp .pg{display:grid;gap:18px;grid-template-columns:repeat(4,1fr)}.shp .pc{background:var(--fbg);border:1px solid var(--ln);border-radius:calc(var(--r)*1.2);overflow:hidden;display:flex;flex-direction:column;transition:.25s}.shp .pc:hover{transform:translateY(-4px);box-shadow:0 22px 40px -22px #0006}
.shp .pc .im{position:relative;aspect-ratio:4/3}.shp .pc .pt{position:absolute;inset:0;display:grid;place-content:center;justify-items:center;gap:10px;background:linear-gradient(145deg,var(--sf),color-mix(in srgb,var(--ac) 14%,var(--sf)));color:var(--ac)}.shp .pc .pt small{font:700 .72rem var(--fb);letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}.shp .pc .cd1{position:absolute;left:10px;top:10px;background:var(--dk);color:#fff;font:700 .7rem/1 var(--fm);padding:6px 8px;border-radius:6px;letter-spacing:.04em}
.shp .pc .in{padding:16px;display:grid;gap:8px;flex:1;align-content:start}.shp .pc h3{font:700 1rem/1.25 var(--fd)}.shp .pc .uy{font-size:.8rem;color:var(--mut);line-height:1.4}.shp .pc .st{font:700 .74rem/1 var(--fb);display:flex;align-items:center;gap:6px}.shp .pc .st:before{content:"";width:8px;height:8px;border-radius:50%;background:#16a34a}.shp .pc .st.s1:before{background:#f59e0b}.shp .pc .st.s0:before{background:#dc2626}
.shp .pc .pr{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:auto;padding-top:10px}.shp .pc .pr b{font:800 1.22rem/1 var(--fd)}.shp .pc .add{min-height:42px;padding:0 14px;border-radius:var(--r);background:var(--ac);color:var(--on-ac);border:0;font:700 .84rem var(--fb);cursor:pointer;display:inline-flex;align-items:center;gap:6px}.shp .pc .add:disabled{background:var(--ln);color:var(--mut);cursor:not-allowed}
.shp .empty{padding:50px 10px;text-align:center;color:var(--mut)}
.shp.lst .pg{grid-template-columns:1fr}.shp.lst .pc{flex-direction:row}.shp.lst .pc .im{width:200px;aspect-ratio:auto;flex:none}.shp.lst .pc .in{grid-template-columns:1fr auto;align-items:center;gap:6px 20px}.shp.lst .pc .pr{flex-direction:column;align-items:flex-end;margin:0;padding:0}
.shp.mag .pg{grid-template-columns:repeat(3,1fr);gap:26px}.shp.mag .pc{border:0;background:transparent;border-radius:0}.shp.mag .pc .im{aspect-ratio:1/1;border-radius:calc(var(--r)*1.2);overflow:hidden}.shp.mag .pc .in{padding:14px 2px}
.crt-fab{position:fixed;right:18px;bottom:22px;z-index:75;min-height:56px;padding:0 20px;border-radius:99px;background:var(--dk);color:#fff;border:0;font:700 .92rem var(--fb);display:inline-flex;align-items:center;gap:10px;cursor:pointer;box-shadow:0 18px 40px -12px #0008}.crt-fab i{font-style:normal;background:var(--ac);color:var(--on-ac);min-width:24px;height:24px;border-radius:99px;display:grid;place-items:center;font-size:.78rem;padding:0 6px}
.crt{position:fixed;inset:0;z-index:90;visibility:hidden;pointer-events:none}.crt .bd{position:absolute;inset:0;background:#0007;opacity:0;transition:.3s}.crt .pn{position:absolute;right:0;top:0;bottom:0;width:min(440px,100%);background:var(--bg);color:var(--ink);transform:translateX(100%);transition:.35s;display:flex;flex-direction:column;box-shadow:-20px 0 60px -20px #0006}
body.copen .crt{visibility:visible;pointer-events:auto}body.copen .crt .bd{opacity:1}body.copen .crt .pn{transform:none}
.crt .hd{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid var(--ln)}.crt .hd h3{font:800 1.2rem var(--fd)}.crt .hd button{background:none;border:0;color:var(--ink);cursor:pointer;padding:8px}
.crt .ls{flex:1;overflow:auto;padding:8px 20px}.crt .it{display:grid;grid-template-columns:1fr auto;gap:4px 12px;padding:14px 0;border-bottom:1px solid var(--ln);align-items:center}.crt .it b{font:700 .94rem/1.3 var(--fb)}.crt .it small{color:var(--mut);font-size:.76rem}.crt .qt{display:flex;align-items:center;gap:6px;margin-top:6px}.crt .qt button{width:32px;height:32px;border-radius:8px;border:1px solid var(--ln);background:var(--fbg);color:var(--ink);cursor:pointer;font-size:1.05rem}.crt .it .tt{font:800 1rem var(--fd);text-align:right}
.crt .ft{padding:16px 20px calc(16px + env(safe-area-inset-bottom));border-top:1px solid var(--ln);display:grid;gap:10px;background:var(--sf)}.crt .sm{display:flex;justify-content:space-between;font:800 1.2rem var(--fd)}.crt form{display:grid;gap:8px}.crt input,.crt textarea{width:100%;min-height:46px;padding:10px 14px;background:var(--fbg);border:1px solid var(--ln);border-radius:var(--r);font:500 .94rem var(--fb);color:var(--ink)}.crt textarea{min-height:60px;resize:vertical}.crt .msg{font-size:.86rem}.crt .msg.er{color:#dc2626}.crt .msg.ok{color:#16a34a}.crt .nt{font-size:.76rem;color:var(--mut);line-height:1.45}
@media(max-width:1100px){.shp .pg{grid-template-columns:repeat(3,1fr)}}@media(max-width:800px){.shp .pg,.shp.mag .pg{grid-template-columns:repeat(2,1fr);gap:12px}.shp .bar{grid-template-columns:1fr 1fr}.shp .bar input{grid-column:1/-1}.shp.lst .pc{flex-direction:column}.shp.lst .pc .im{width:auto;aspect-ratio:4/3}.shp.lst .pc .in{grid-template-columns:1fr}.shp.lst .pc .pr{flex-direction:row;align-items:center}.shp .pc .in{padding:12px}.shp .pc h3{font-size:.92rem}.crt-fab{display:none}}
@media(max-width:420px){.shp .pg{grid-template-columns:1fr 1fr}.shp .pc .add span{display:none}}
"""

JS = r"""(function(){var D=window.__SHOP,C=[],q='',cat='',br='',so='',KEY='okcart-'+location.pathname;
try{C=JSON.parse(localStorage.getItem(KEY)||'[]')}catch(e){C=[]}
var $=function(s,r){return(r||document).querySelector(s)},A=function(s,r){return[].slice.call((r||document).querySelectorAll(s))},tl=function(n){return n.toLocaleString('tr-TR')+' ₺'};
function save(){try{localStorage.setItem(KEY,JSON.stringify(C))}catch(e){}}
function cnt(){return C.reduce(function(a,x){return a+x.q},0)}
function badge(){A('[data-ccount]').forEach(function(e){e.textContent=cnt()})}
function draw(){var g=$('#pg');if(!g)return;var L=D.filter(function(p){return(!cat||p[3]===cat)&&(!br||p[2].toLowerCase().indexOf(br.toLowerCase())>-1)&&(!q||(p[0]+' '+p[1]+' '+p[2]+' '+p[3]).toLowerCase().indexOf(q)>-1)});
 if(so==='a')L.sort(function(a,b){return a[4]-b[4]});if(so==='d')L.sort(function(a,b){return b[4]-a[4]});
 g.innerHTML=L.length?L.map(function(p){var i=D.indexOf(p),stt=p[5]==2?['Stokta','']:p[5]==1?['Son adetler','s1']:['Stokta yok','s0'];
  return '<article class="pc"><div class="im"><div class="pt" role="img" aria-label="'+p[1]+'">'+window.__SHOPIC+'<small>'+p[3]+'</small></div><span class="cd1">'+p[0]+'</span></div><div class="in"><h3>'+p[1]+'</h3><div class="uy">Uyumlu: '+p[2]+'</div><div class="st '+stt[1]+'">'+stt[0]+'</div><div class="pr"><b>'+tl(p[4])+'</b><button class="add" data-i="'+i+'"'+(p[5]?'':' disabled')+' aria-label="Sepete ekle">'+(p[5]?'+ <span>Sepete ekle</span>':'—')+'</button></div></div></article>'}).join(''):'<div class="empty">Aradığınız ürün bulunamadı. Parça kodunu veya cihaz modelini WhatsApp’tan yazın, bulalım.</div>';
 A('.add',g).forEach(function(b){b.addEventListener('click',function(){add(+b.dataset.i)})})}
function add(i){var p=D[i],f=C.filter(function(x){return x.k===p[0]})[0];if(f)f.q++;else C.push({k:p[0],n:p[1],p:p[4],q:1});save();cart();badge();document.body.classList.add('copen')}
function cart(){var l=$('#cl');if(!l)return;l.innerHTML=C.length?C.map(function(x,j){return '<div class="it"><div><b>'+x.n+'</b><small>'+x.k+' · '+tl(x.p)+'</small><div class="qt"><button data-d="'+j+'" aria-label="Azalt">−</button><span>'+x.q+'</span><button data-u="'+j+'" aria-label="Artır">+</button></div></div><div class="tt">'+tl(x.p*x.q)+'</div></div>'}).join(''):'<div class="empty" style="padding:40px 0;text-align:center;color:var(--mut)">Sepetiniz boş.</div>';
 A('[data-d]',l).forEach(function(b){b.onclick=function(){var j=+b.dataset.d;C[j].q--;if(C[j].q<1)C.splice(j,1);save();cart();badge()}});A('[data-u]',l).forEach(function(b){b.onclick=function(){C[+b.dataset.u].q++;save();cart();badge()}});
 var t=C.reduce(function(a,x){return a+x.p*x.q},0);$('#ct').textContent=tl(t);$('#cf').style.display=C.length?'':'none'}
document.addEventListener('DOMContentLoaded',function(){var s=$('#sq');if(!s)return;
 s.addEventListener('input',function(){q=s.value.trim().toLowerCase();draw()});$('#sb').addEventListener('change',function(e){br=e.target.value;draw()});$('#ss').addEventListener('change',function(e){so=e.target.value;draw()});
 A('.cat button').forEach(function(b){b.addEventListener('click',function(){A('.cat button').forEach(function(x){x.classList.remove('on')});b.classList.add('on');cat=b.dataset.c;draw()})});
 A('[data-cart]').forEach(function(b){b.addEventListener('click',function(e){e.preventDefault();document.body.classList.add('copen')})});A('[data-cclose]').forEach(function(b){b.addEventListener('click',function(){document.body.classList.remove('copen')})});
 var hs=document.getElementById('hsq');if(hs)hs.addEventListener('submit',function(e){e.preventDefault();s.value=hs.querySelector('input').value;q=s.value.trim().toLowerCase();draw();document.getElementById('urunler').scrollIntoView({behavior:'smooth'})});
 var f=$('#of');f.addEventListener('submit',function(ev){ev.preventDefault();var g=function(n){return f.elements[n].value.trim()};if(g('website'))return;if(!C.length)return;var m=f.querySelector('.msg'),b=f.querySelector('button[type=submit]'),old=b.textContent;b.disabled=true;b.textContent='Gönderiliyor…';m.className='msg';m.textContent='';
  var tot=C.reduce(function(a,x){return a+x.p*x.q},0),lines=C.map(function(x){return x.q+' x '+x.n+' ('+x.k+') = '+tl(x.p*x.q)}).join('\n');
  OKT.post({name:g('name'),phone:g('phone'),district:g('ilce'),type:'siparis',device_type:'Online mağaza',message:'SİPARİŞ\n'+lines+'\nToplam: '+tl(tot)+'\nAdres: '+g('adres')+(g('not')?'\nNot: '+g('not'):''),page:location.pathname,website:''}).then(function(r){m.className='msg ok';m.textContent=r.preview?'✓ Önizleme: bu sitede sipariş formu henüz firmanıza bağlı değil.':'✓ Siparişiniz alındı. Ödeme ve teslimat için sizi arayacağız.';C=[];save();cart();badge();b.textContent='Gönderildi';setTimeout(function(){b.disabled=false;b.textContent=old},4000)}).catch(function(x){m.className='msg er';m.textContent=x.message||'Gönderilemedi';b.disabled=false;b.textContent=old})});
 draw();cart();badge()})})();"""


def _brands(rows):
    seen = []
    for r in rows:
        for b in r[2].split(','):
            b = b.strip()
            if b and '(' not in b and b not in seen and b not in ('Tüm markalar', 'Model seçimiyle'):
                seen.append(b)
    return seen[:10]


def shop(X, v):
    rows = PRODUCTS[X.r['sector']]
    X.css('shop', SHOPCSS)
    X.js('SHOPJS')
    cats = []
    for r in rows:
        if r[3] not in cats:
            cats.append(r[3])
    brs = _brands(rows)
    cls = {'grid': '', 'list': ' lst', 'mag': ' mag'}[v]
    title = X.r.get('shopt', 'Ürünler')
    data = json.dumps([list(r) for r in rows], ensure_ascii=False)
    head = f'<div class="sh"><span class="eyebrow">Online mağaza</span><h2>{title}</h2><p>Parça kodu veya cihaz modelinizle arayın. Fiyat ve stok bilgisi anlıktır; siparişten sonra sizi arayıp teyit ederiz.</p></div>'
    bar = (f'<div class="bar"><input id="sq" type="search" placeholder="Parça kodu, ürün adı veya model ara…" aria-label="Ürün ara">'
           f'<select id="sb" aria-label="Marka"><option value="">Tüm markalar</option>' + ''.join(f'<option>{b}</option>' for b in brs) + '</select>'
           f'<select id="ss" aria-label="Sırala"><option value="">Önerilen sıra</option><option value="a">Fiyat: düşükten yükseğe</option><option value="d">Fiyat: yüksekten düşüğe</option></select></div>')
    catb = '<div class="cat"><button class="on" data-c="">Tümü</button>' + ''.join(f'<button data-c="{c}">{c}</button>' for c in cats) + '</div>'
    drawer = (f'<div class="crt" role="dialog" aria-label="Sepet"><div class="bd" data-cclose></div><div class="pn"><div class="hd"><h3>Sepetiniz</h3><button data-cclose aria-label="Kapat">{ic("x", 22)}</button></div>'
              f'<div class="ls" id="cl"></div><div class="ft" id="cf"><div class="sm"><span>Toplam</span><span id="ct">0 ₺</span></div>'
              f'<form id="of"><input name="name" placeholder="Ad soyad" required autocomplete="name"><input name="phone" type="tel" placeholder="Telefon" required autocomplete="tel"><input name="ilce" placeholder="İlçe" autocomplete="address-level2"><textarea name="adres" placeholder="Teslimat adresi" required></textarea><textarea name="not" placeholder="Cihaz marka / model (uyum kontrolü için)"></textarea>'
              f'<input name="website" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true"><button class="btn" type="submit">Siparişi gönder</button><div class="msg" role="status"></div><p class="nt">Ödeme: kapıda ödeme veya havale/EFT. Sipariş sonrası uyumluluk ve teslimat için sizi ararız.</p></form></div></div></div>')
    fab = f'<button class="crt-fab" data-cart aria-label="Sepeti aç">{ic("bx", 20)} Sepet <i data-ccount>0</i></button>'
    X.shop_data = data
    return (f'<section class="sec shp{cls}" id="urunler"><div class="w">{head}{bar}{catb}<div class="pg" id="pg"></div></div>'
            f'<script>window.__SHOP={data};window.__SHOPIC={json.dumps(ic(X.c["ico"], 54, 1.4))};</script></section>{drawer}{fab}')


def hero_shop(X):
    rows = PRODUCTS[X.r['sector']]
    cats = []
    for r in rows:
        if r[3] not in cats:
            cats.append(r[3])
    X.css('hero.shop', """.hrs{background:var(--sf);padding:clamp(36px,5vw,72px) 0}.hrs .g{display:grid;grid-template-columns:1.05fr .95fr;gap:clamp(24px,4vw,56px);align-items:center}.hrs h1{margin:14px 0 14px}.hrs .lead{max-width:520px;color:var(--mut)}
.hrs form{display:flex;gap:8px;margin:24px 0 14px;max-width:560px}.hrs form input{flex:1;min-height:56px;padding:0 18px;background:var(--fbg);border:1px solid var(--ln);border-radius:var(--r);font:500 1rem var(--fb);color:var(--ink);min-width:0}
.hrs .cc{display:flex;gap:8px;flex-wrap:wrap}.hrs .cc a{padding:8px 14px;border:1px solid var(--ln);border-radius:99px;font:600 .84rem var(--fb);background:var(--fbg)}.hrs .tr{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:26px;max-width:560px}.hrs .tr div{font:600 .84rem/1.35 var(--fb);display:flex;gap:8px;align-items:flex-start}
.hrs .im{position:relative;aspect-ratio:5/4;border-radius:calc(var(--r)*1.6);overflow:hidden}.hrs .im .ph{position:absolute;inset:0}.hrs .tag{position:absolute;left:16px;bottom:16px;right:16px;background:var(--bg);color:var(--ink);border-radius:calc(var(--r)*1.1);padding:14px 16px;display:flex;justify-content:space-between;gap:12px;align-items:center;font:700 .94rem var(--fb)}.hrs .tag small{display:block;color:var(--mut);font-weight:500;font-size:.78rem;margin-top:3px}
@media(max-width:900px){.hrs .g{grid-template-columns:1fr}.hrs .tr{grid-template-columns:1fr}.hrs form{flex-direction:column}}""")
    ch = ''.join(f'<a href="#urunler" onclick="document.querySelector(\'.cat [data-c=&quot;{c}&quot;]\').click()">{c}</a>' for c in cats[:6])
    return (f'<section class="hr hrs" id="top2"><div class="w g"><div class="rv"><span class="eyebrow">{X.c["label"]} yedek parça · {X.city}</span><h1>{X.h[0]}</h1>'
            f'<p class="lead">Parça kodu, marka ve model uyumunu görerek sipariş verin. Stokta olanlar aynı gün kargoya verilir; takılması için usta da gönderiyoruz.</p>'
            f'<form id="hsq"><input type="search" placeholder="Parça kodu veya model yazın (örn. {rows[0][0]})" aria-label="Ürün ara"><button class="btn" type="submit">Ürün ara</button></form><div class="cc">{ch}</div>'
            f'<div class="tr"><div>{ic("ok", 18)}Uyumlu marka ve model bilgisi her üründe</div><div>{ic("bx", 18)}Stoktaki ürün aynı gün kargoda</div><div>{ic("wr", 18)}İsterseniz usta takar, garanti verir</div></div></div>'
            f'<div class="rv rv2 im">{X.ph("im2", "center")}<div class="tag"><div>Parçayı bulamadınız mı?<small>Fotoğrafını WhatsApp’tan gönderin</small></div><a class="btn" href="https://wa.me/{TELRAW}">{ic("wa", 18)} Yazın</a></div></div></div></section>')
