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
 'bilgisayar': [
  ('BG-1001', 'SSD 512 GB NVMe', 'Tüm modern dizüstü ve masaüstüler', 'Depolama', 1450, 2), ('BG-1102', 'SSD 1 TB SATA 2.5"', 'Eski dizüstü ve masaüstüler', 'Depolama', 1790, 2),
  ('BG-1210', 'DDR4 8 GB 3200 MHz RAM', 'Masaüstü', 'Bellek', 780, 2), ('BG-1215', 'DDR4 SODIMM 16 GB RAM', 'Dizüstü', 'Bellek', 1380, 1),
  ('BG-1320', 'Dizüstü batarya (model seçimiyle)', 'Asus, Lenovo, HP, Monster', 'Batarya', 1150, 2), ('BG-1410', 'Şarj adaptörü 65 W', 'Dizüstü (uç seçimiyle)', 'Adaptör', 520, 2),
  ('BG-1505', 'Dizüstü ekran 15.6" FHD', 'Model seçimiyle', 'Ekran', 2450, 1), ('BG-1602', 'Klavye (Türkçe Q)', 'Model seçimiyle', 'Klavye', 480, 2),
  ('BG-1710', 'Termal macun (4 g)', 'Tüm işlemciler', 'Sarf', 140, 2), ('BG-1820', 'Soğutucu fan', 'Dizüstü / kasa', 'Soğutma', 260, 2),
  ('BG-1905', 'Güç kaynağı 550 W', 'Masaüstü', 'Güç', 1280, 0), ('BG-2010', 'USB-C hub 7 in 1', 'Tüm cihazlar', 'Aksesuar', 640, 2)],
 'elektronik': [
  ('EK-1001', 'TV arka aydınlatma LED şerit', '40-43 inç', 'TV', 380, 2), ('EK-1102', 'TV güç kartı', 'Samsung, LG, Vestel', 'TV', 1250, 1),
  ('EK-1210', 'Ana kart (T-Con)', '43 inç 4K', 'TV', 960, 1), ('EK-1312', 'HDMI kablo 2.1 (2 m)', 'Tüm cihazlar', 'Kablo', 190, 2),
  ('EK-1405', 'Uzaktan kumanda', 'Samsung, LG', 'Aksesuar', 220, 2), ('EK-1510', 'Duvar askı aparatı', '32-65 inç', 'Aksesuar', 340, 2),
  ('EK-1620', 'Uydu alıcı LNB', 'Tek çıkışlı', 'Uydu', 260, 2), ('EK-1710', 'Hoparlör çifti 8 Ω', 'Soundbar / TV', 'Ses', 410, 1),
  ('EK-1802', 'Kondansatör seti', 'Güç kartı onarımı', 'Elektronik', 150, 2), ('EK-1910', 'Mikrofon / uzaktan kumanda pili', 'Genel', 'Sarf', 60, 2),
  ('EK-2005', 'Panel (ekran) 32 inç', 'Model seçimiyle', 'TV', 3250, 0), ('EK-2110', 'Anten kablosu 10 m', 'Tüm cihazlar', 'Kablo', 110, 2)],
}

CFG = {'kargo': 89, 'kargo_esik': 1500, 'montaj': 350, 'kesif': 250, 'kapida_ucret': 25, 'iban': 'TR00 0000 0000 0000 0000 0000 00', 'hesap': 'Firma unvanı', 'adres': '',
       'odeme': {'kapida_nakit': True, 'kapida_kart': True, 'kart': True, 'havale': True}}
SHOPCSS = """
.shp .bar{display:grid;grid-template-columns:1.4fr auto auto;gap:12px;margin:0 0 18px;align-items:center}.shp .bar input,.shp .bar select{width:100%;min-height:50px;padding:0 16px;background:var(--fbg);border:1px solid var(--ln);border-radius:var(--r);font:500 .96rem var(--fb);color:var(--ink)}
.shp .cat{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:26px}.shp .cat button{min-height:40px;padding:0 16px;border-radius:99px;border:1px solid var(--ln);background:transparent;color:var(--ink);font:600 .86rem var(--fb);cursor:pointer;transition:.2s}.shp .cat button.on,.shp .cat button:hover{background:var(--dk);color:#fff;border-color:var(--dk)}
.shp .pg{display:grid;gap:18px;grid-template-columns:repeat(4,1fr)}.shp .pc{background:var(--fbg);border:1px solid var(--ln);border-radius:calc(var(--r)*1.2);overflow:hidden;display:flex;flex-direction:column;transition:.25s}.shp .pc:hover{transform:translateY(-4px);box-shadow:0 22px 40px -22px #0006}
.shp .pc .im{position:relative;aspect-ratio:4/3}.shp .pc .pt{position:absolute;inset:0;display:grid;place-content:center;justify-items:center;gap:10px;background:linear-gradient(145deg,var(--sf),color-mix(in srgb,var(--ac) 14%,var(--sf)));color:var(--ac)}.shp .pc .pt small{font:700 .72rem var(--fb);letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}.shp .pc .pt .okpimg{width:100%;height:100%}.shp .pc .cd1{position:absolute;left:10px;top:10px;background:var(--dk);color:#fff;font:700 .7rem/1 var(--fm);padding:6px 8px;border-radius:6px;letter-spacing:.04em}
.shp .pc .in{padding:16px;display:grid;gap:8px;flex:1;align-content:start}.shp .pc h3{font:700 1rem/1.25 var(--fd)}.shp .pc .uy{font-size:.8rem;color:var(--mut);line-height:1.4}.shp .pc .st{font:700 .74rem/1 var(--fb);display:flex;align-items:center;gap:6px}.shp .pc .st:before{content:"";width:8px;height:8px;border-radius:50%;background:#16a34a}.shp .pc .st.s1:before{background:#f59e0b}.shp .pc .st.s0:before{background:#dc2626}
.shp .pc .pr{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:auto;padding-top:10px}.shp .pc .pr b{font:800 1.22rem/1 var(--fd)}.shp .pc .add{min-height:42px;padding:0 14px;border-radius:var(--r);background:var(--ac);color:var(--on-ac);border:0;font:700 .84rem var(--fb);cursor:pointer;display:inline-flex;align-items:center;gap:6px}.shp .pc .add:disabled{background:var(--ln);color:var(--mut);cursor:not-allowed}
.shp .empty{padding:50px 10px;text-align:center;color:var(--mut)}
.shp.lst .pg{grid-template-columns:1fr}.shp.lst .pc{flex-direction:row}.shp.lst .pc .im{width:200px;aspect-ratio:auto;flex:none}.shp.lst .pc .in{grid-template-columns:1fr auto;align-items:center;gap:6px 20px}.shp.lst .pc .pr{flex-direction:column;align-items:flex-end;margin:0;padding:0}
.shp.mag .pg{grid-template-columns:repeat(3,1fr);gap:26px}.shp.mag .pc{border:0;background:transparent;border-radius:0}.shp.mag .pc .im{aspect-ratio:1/1;border-radius:calc(var(--r)*1.2);overflow:hidden}.shp.mag .pc .in{padding:14px 2px}
.crt-fab{position:fixed;right:18px;bottom:22px;z-index:75;min-height:56px;padding:0 20px;border-radius:99px;background:var(--dk);color:#fff;border:0;font:700 .92rem var(--fb);display:inline-flex;align-items:center;gap:10px;cursor:pointer;box-shadow:0 18px 40px -12px #0008}.crt-fab i{font-style:normal;background:var(--ac);color:var(--on-ac);min-width:24px;height:24px;border-radius:99px;display:grid;place-items:center;font-size:.78rem;padding:0 6px}
.crt{position:fixed;inset:0;z-index:90;visibility:hidden;pointer-events:none}.crt .bd{position:absolute;inset:0;background:#0007;opacity:0;transition:.3s}.crt .pn{position:absolute;right:0;top:0;bottom:0;width:min(520px,100%);background:var(--bg);color:var(--ink);transform:translateX(100%);transition:.35s;display:flex;flex-direction:column;box-shadow:-20px 0 60px -20px #0006}
body.copen .crt{visibility:visible;pointer-events:auto}body.copen .crt .bd{opacity:1}body.copen .crt .pn{transform:none}
.crt .hd{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid var(--ln)}.crt .hd h3{font:800 1.2rem var(--fd)}.crt .hd button{background:none;border:0;color:var(--ink);cursor:pointer;padding:8px}
.crt .ls{flex:1;overflow:auto;padding:8px 20px}.crt .it{display:grid;grid-template-columns:1fr auto;gap:4px 12px;padding:14px 0;border-bottom:1px solid var(--ln);align-items:center}.crt .it b{font:700 .94rem/1.3 var(--fb)}.crt .it small{color:var(--mut);font-size:.76rem}.crt .qt{display:flex;align-items:center;gap:6px;margin-top:6px}.crt .qt button{width:32px;height:32px;border-radius:8px;border:1px solid var(--ln);background:var(--fbg);color:var(--ink);cursor:pointer;font-size:1.05rem}.crt .it .tt{font:800 1rem var(--fd);text-align:right}
.crt .cfo{padding:16px 20px calc(16px + env(safe-area-inset-bottom));border-top:1px solid var(--ln);display:grid;gap:10px;background:var(--sf)}.crt .sm{display:flex;justify-content:space-between;font:800 1.2rem var(--fd)}.crt form{display:grid;gap:8px}.crt input,.crt textarea{width:100%;min-height:46px;padding:10px 14px;background:var(--fbg);border:1px solid var(--ln);border-radius:var(--r);font:500 .94rem var(--fb);color:var(--ink)}.crt textarea{min-height:60px;resize:vertical}.crt .msg{font-size:.86rem}.crt .msg.er{color:#dc2626}.crt .msg.ok{color:#16a34a}.crt .nt{font-size:.76rem;color:var(--mut);line-height:1.45}
.crt .stp{display:flex;gap:4px;padding:12px 20px;border-bottom:1px solid var(--ln);overflow:auto}.crt .stp span{flex:1;min-width:max-content;font:700 .72rem var(--fb);text-align:center;padding:8px 6px;border-radius:99px;color:var(--mut);background:var(--sf);white-space:nowrap}.crt .stp span.on{background:var(--dk);color:#fff}.crt .stp span.ok{background:color-mix(in srgb,var(--ac) 18%,var(--sf));color:var(--ink)}
.crt .pane{display:none}.crt .pane.on{display:block}.crt .fld{display:grid;gap:6px;margin-bottom:12px}.crt .fld label{font:700 .8rem var(--fb)}.crt .two{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.crt .opt{display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:start;padding:14px;border:1.5px solid var(--ln);border-radius:var(--r);margin-bottom:10px;cursor:pointer;background:var(--fbg);position:relative}.crt .opt input{width:18px;height:18px;min-height:0;margin-top:2px;accent-color:var(--ac)}.crt .opt b{font:700 .94rem/1.3 var(--fb);display:block}.crt .opt small{display:block;color:var(--mut);font-size:.78rem;line-height:1.4;margin-top:3px}.crt .opt em{font:800 .9rem var(--fd);font-style:normal;white-space:nowrap}.crt .opt.on{border-color:var(--ac);box-shadow:0 0 0 3px color-mix(in srgb,var(--ac) 18%,transparent)}
.crt .sub{display:none;margin:-4px 0 12px;padding:14px;background:var(--sf);border-radius:var(--r)}.crt .sub.on{display:block}.crt .sum2{display:grid;gap:6px;font-size:.9rem;padding:14px;background:var(--sf);border-radius:var(--r);margin-bottom:12px}.crt .sum2 div{display:flex;justify-content:space-between;gap:12px}.crt .sum2 .t{font:800 1.1rem var(--fd);border-top:1px solid var(--ln);padding-top:8px;margin-top:4px}
.crt .nv{display:flex;gap:8px}.crt .nv .btn{flex:1;min-height:48px}.crt .nv .o{flex:0 0 auto}.crt .ck2{display:flex;gap:10px;align-items:flex-start;font-size:.82rem;line-height:1.45;margin:6px 0 12px}.crt .ck2 input{width:18px;height:18px;min-height:0;flex:none;margin-top:2px}
.crt .done{text-align:center;padding:10px 0}.crt .done .no{font:800 1.5rem var(--fm);letter-spacing:.04em;background:var(--sf);display:inline-block;padding:10px 18px;border-radius:var(--r);margin:10px 0}.crt .tl2{text-align:left;margin:18px 0;display:grid;gap:0}.crt .tl2 div{position:relative;padding:0 0 16px 28px;font-size:.88rem}.crt .tl2 div:before{content:"";position:absolute;left:5px;top:5px;width:10px;height:10px;border-radius:50%;background:var(--ln)}.crt .tl2 div.f:before{background:var(--ac)}.crt .tl2 div:after{content:"";position:absolute;left:9px;top:16px;bottom:-5px;width:2px;background:var(--ln)}.crt .tl2 div:last-child:after{display:none}.crt .tl2 small{display:block;color:var(--mut)}
.crt .iban{font:700 .95rem var(--fm);background:var(--sf);padding:12px;border-radius:var(--r);word-break:break-all;margin:8px 0;user-select:all}
@media(max-width:1100px){.shp .pg{grid-template-columns:repeat(3,1fr)}}@media(max-width:800px){.shp .pg,.shp.mag .pg{grid-template-columns:repeat(2,1fr);gap:12px}.shp .bar{grid-template-columns:1fr 1fr}.shp .bar input{grid-column:1/-1}.shp.lst .pc{flex-direction:column}.shp.lst .pc .im{width:auto;aspect-ratio:4/3}.shp.lst .pc .in{grid-template-columns:1fr}.shp.lst .pc .pr{flex-direction:row;align-items:center}.shp .pc .in{padding:12px}.shp .pc h3{font-size:.92rem}.crt-fab{display:none}}
@media(max-width:420px){.shp .pg{grid-template-columns:1fr 1fr}.shp .pc .add span{display:none}}
"""

JS = r"""(function(){function okPimg(n,c){var s=String(n||'')+' '+String(c||''),l=s.toLowerCase().replace(/İ/g,'i'),h=0,i;for(i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))%360;
var P=[['#f6e3d3','#e8935a'],['#dcebf2','#4f8fb0'],['#e6efdc','#6f9a58'],['#efe0ec','#a8639a'],['#f4ecd0','#c9a227'],['#dfe3ee','#5b6fb0'],['#f3dcdc','#c0504a'],['#d9efe9','#3f9a86']][h%8],a=P[0],b=P[1],g='',k=function(r){return r.test(l)};
if(k(/çanta|canta|cüzdan|valiz|sırt/))g='<path d="M62 78 C62 52 138 52 138 78" fill="none" stroke="'+b+'" stroke-width="7" stroke-linecap="round"/><path d="M44 78 H156 L146 158 H54Z" fill="'+b+'"/><rect x="44" y="78" width="112" height="12" fill="#000" opacity=".12"/>';
else if(k(/ayakkab|bot|sneaker|terlik|sandalet|çizme/))g='<path d="M40 128 C40 100 58 96 74 92 L92 70 L112 78 C120 98 150 108 164 118 L164 142 H40Z" fill="'+b+'"/><rect x="40" y="138" width="124" height="14" rx="7" fill="#fff" opacity=".85"/><path d="M96 84 l10 12 M108 90 l10 12" stroke="#fff" stroke-width="4" stroke-linecap="round"/>';
else if(k(/tişört|tisort|gömlek|elbise|pantolon|ceket|mont|kazak|giyim|t-shirt|etek|şort|hırka|sweat/))g='<path d="M70 52 L100 62 L130 52 L170 78 L152 102 L138 94 V158 H62 V94 L48 102 L30 78Z" fill="'+b+'"/><path d="M84 52 Q100 72 116 52" fill="'+a+'" opacity=".9"/>';
else if(k(/şişe|sise|parfüm|parfum|krem|şampuan|sampuan|serum|kozmetik|losyon|sprey|yağ|yag|sabun|deterjan/))g='<rect x="86" y="46" width="28" height="22" rx="4" fill="#3a3f48"/><rect x="92" y="34" width="16" height="14" rx="3" fill="#3a3f48"/><rect x="62" y="68" width="76" height="92" rx="16" fill="'+b+'"/><rect x="72" y="96" width="56" height="36" rx="6" fill="#fff" opacity=".88"/><rect x="80" y="106" width="40" height="5" rx="2" fill="'+b+'"/><rect x="80" y="118" width="26" height="4" rx="2" fill="#aaa"/>';
else if(k(/telefon|kılıf|kilif|şarj|sarj|kulaklık|kulaklik|kablo|powerbank|akıllı|tablet|bilgisayar/))g='<rect x="66" y="36" width="68" height="128" rx="14" fill="#262a32"/><rect x="72" y="46" width="56" height="102" rx="8" fill="'+b+'"/><circle cx="100" cy="156" r="4" fill="#666"/><rect x="82" y="58" width="36" height="8" rx="4" fill="#fff" opacity=".5"/><rect x="82" y="74" width="26" height="6" rx="3" fill="#fff" opacity=".4"/>';
else if(k(/lamba|aydınlat|avize|mum|vazo|saksı|ev |yaşam|dekor|yastık|battaniye|halı/))g='<path d="M70 120 L130 120 L142 66 H58Z" fill="'+b+'"/><rect x="96" y="120" width="8" height="34" fill="#3a3f48"/><rect x="74" y="152" width="52" height="8" rx="4" fill="#3a3f48"/><circle cx="100" cy="92" r="12" fill="#fff" opacity=".45"/>';
else if(k(/saat|takı|taki|kolye|yüzük|bilezik|gözlük/))g='<rect x="82" y="30" width="36" height="30" fill="#3a3f48"/><rect x="82" y="140" width="36" height="30" fill="#3a3f48"/><circle cx="100" cy="100" r="42" fill="'+b+'"/><circle cx="100" cy="100" r="33" fill="#fff"/><path d="M100 100 V78 M100 100 L116 108" stroke="#3a3f48" stroke-width="5" stroke-linecap="round"/>';
else if(k(/hediye|paket|set/))g='<rect x="48" y="82" width="104" height="76" rx="6" fill="'+b+'"/><rect x="44" y="68" width="112" height="20" rx="5" fill="'+b+'"/><rect x="92" y="68" width="16" height="90" fill="#fff" opacity=".85"/><path d="M100 68 C80 40 62 56 80 66 M100 68 C120 40 138 56 120 66" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round"/>';
else g='<path d="M44 74 L100 50 L156 74 V140 L100 164 L44 140Z" fill="'+b+'"/><path d="M44 74 L100 98 L156 74 M100 98 V164" fill="none" stroke="#000" stroke-opacity=".18" stroke-width="3"/><rect x="62" y="108" width="30" height="20" rx="3" fill="#fff" opacity=".8" transform="rotate(14 77 118)"/>';
return '<svg class="okpimg" viewBox="0 0 200 200" preserveAspectRatio="xMidYMid slice" style="width:100%;height:100%;display:block" role="img" aria-label="'+String(n||'Ürün').replace(/"/g,'')+'"><rect width="200" height="200" fill="'+a+'"/><ellipse cx="100" cy="164" rx="52" ry="9" fill="#000" opacity=".12"/>'+g+'</svg>'}
var D=window.__SHOP,CF=window.__SHOPCFG||{},C=[],q='',cat='',br='',so='',STEP=1,KEY='okcart-'+location.pathname;
try{C=JSON.parse(localStorage.getItem(KEY)||'[]')}catch(e){C=[]}
var $=function(s,r){return(r||document).querySelector(s)},A=function(s,r){return[].slice.call((r||document).querySelectorAll(s))},tl=function(n){return n.toLocaleString('tr-TR')+' ₺'},V=function(id){var e=document.getElementById(id);return e?e.value.trim():''},R=function(n){var e=document.querySelector('input[name='+n+']:checked');return e?e.value:''};
function save(){try{localStorage.setItem(KEY,JSON.stringify(C))}catch(e){}}
function cnt(){return C.reduce(function(a,x){return a+x.q},0)}
function sub(){return C.reduce(function(a,x){return a+x.p*x.q},0)}
function badge(){A('[data-ccount]').forEach(function(e){e.textContent=cnt()})}
function kargo(){return R('o_tes')==='elden'?0:(sub()>=CF.kargo_esik?0:CF.kargo)}
function srv(){var s=R('o_srv');return s==='takim'?CF.montaj:s==='kesif'?CF.kesif:0}
function pay(){return R('o_pay')}
function fee(){return pay()==='kapida_nakit'||pay()==='kapida_kart'?CF.kapida_ucret:0}
function total(){return sub()+kargo()+srv()+fee()}
function draw(){var g=$('#pg');if(!g)return;var L=D.filter(function(p){return(!cat||p[3]===cat)&&(!br||p[2].toLowerCase().indexOf(br.toLowerCase())>-1)&&(!q||(p[0]+' '+p[1]+' '+p[2]+' '+p[3]).toLowerCase().indexOf(q)>-1)});
 if(so==='a')L.sort(function(a,b){return a[4]-b[4]});if(so==='d')L.sort(function(a,b){return b[4]-a[4]});
 g.innerHTML=L.length?L.map(function(p){var i=D.indexOf(p),stt=p[5]==2?['Stokta','']:p[5]==1?['Son adetler','s1']:['Stokta yok','s0'];
  return '<article class="pc"><div class="im"><div class="pt" role="img" aria-label="'+p[1]+'">'+okPimg(p[1],p[3])+'</div><span class="cd1">'+p[0]+'</span></div><div class="in"><h3>'+p[1]+'</h3><div class="uy">Uyumlu: '+p[2]+'</div><div class="st '+stt[1]+'">'+stt[0]+'</div><div class="pr"><b>'+tl(p[4])+'</b><button class="add" data-i="'+i+'"'+(p[5]?'':' disabled')+' aria-label="Sepete ekle">'+(p[5]?'+ <span>Sepete ekle</span>':'—')+'</button></div></div></article>'}).join(''):'<div class="empty">Aradığınız ürün bulunamadı. Parça kodunu veya cihaz modelini WhatsApp’tan yazın, bulalım.</div>';
 A('.add',g).forEach(function(b){b.addEventListener('click',function(){add(+b.dataset.i)})})}
function add(i){var p=D[i],f=C.filter(function(x){return x.k===p[0]})[0];if(f)f.q++;else C.push({k:p[0],n:p[1],p:p[4],q:1});save();STEP=1;go(1);badge();document.body.classList.add('copen')}
function cart(){var l=$('#cl');if(!l)return;l.innerHTML=C.length?C.map(function(x,j){return '<div class="it"><div><b>'+x.n+'</b><small>'+x.k+' · '+tl(x.p)+'</small><div class="qt"><button data-d="'+j+'" aria-label="Azalt">−</button><span>'+x.q+'</span><button data-u="'+j+'" aria-label="Artır">+</button></div></div><div class="tt">'+tl(x.p*x.q)+'</div></div>'}).join('')+(sub()<CF.kargo_esik?'<p class="nt" style="padding:14px 0">'+tl(CF.kargo_esik-sub())+' daha ekleyin, kargo ücretsiz olsun.</p>':'<p class="nt" style="padding:14px 0">✓ Kargo ücretsiz.</p>'):'<div class="empty" style="padding:40px 0;text-align:center;color:var(--mut)">Sepetiniz boş.</div>';
 A('[data-d]',l).forEach(function(b){b.onclick=function(){var j=+b.dataset.d;C[j].q--;if(C[j].q<1)C.splice(j,1);save();cart();badge();tot()}});A('[data-u]',l).forEach(function(b){b.onclick=function(){C[+b.dataset.u].q++;save();cart();badge();tot()}});tot()}
function tot(){var e=$('#ct');if(e)e.textContent=tl(STEP===1?sub():total());var n=$('#nx');if(n&&STEP===1)n.disabled=!C.length}
function payopts(){var o=CF.odeme||{},L=[];
 if(o.kapida_nakit)L.push(['kapida_nakit','Kapıda nakit ödeme','Ürün elinize geçerken kuryeye nakit ödersiniz.',CF.kapida_ucret?'+'+tl(CF.kapida_ucret):'']);
 if(o.kapida_kart)L.push(['kapida_kart','Kapıda kredi kartı ile ödeme','Kurye taşınabilir POS cihazıyla gelir; kartınızı kuryeye uzatırsınız.',CF.kapida_ucret?'+'+tl(CF.kapida_ucret):'']);
 if(o.kart)L.push(['kart','Kredi / banka kartı (güvenli ödeme bağlantısı)','Siparişiniz onaylanınca telefonunuza güvenli ödeme bağlantısı gönderilir; 3D Secure ile ödersiniz. Kart bilgisi bu sayfada girilmez.','']);
 if(o.havale)L.push(['havale','Havale / EFT','Sipariş numarasını açıklamaya yazarak ödersiniz. Ödeme hesabımıza geçince ürün kargolanır.','']);
 $('#o_pay').innerHTML=L.map(function(x,i){return '<label class="opt'+(i?'':' on')+'"><input type="radio" name="o_pay" value="'+x[0]+'"'+(i?'':' checked')+'><span><b>'+x[1]+'</b><small>'+x[2]+'</small></span><em>'+x[3]+'</em></label>'}).join('')}
function sum(){var tes=R('o_tes')==='elden'?'Mağazadan teslim':'Kargo',sr={yok:'Sadece parça',takim:'Usta taksın',kesif:'Önce keşif'}[R('o_srv')],py=$('input[name=o_pay]:checked');py=py?py.parentNode.querySelector('b').textContent:'';
 $('#o_sum').innerHTML=C.map(function(x){return '<div><span>'+x.q+' × '+x.n+'</span><span>'+tl(x.p*x.q)+'</span></div>'}).join('')+'<div><span>Ürünler</span><span>'+tl(sub())+'</span></div><div><span>'+tes+'</span><span>'+(kargo()?tl(kargo()):'Ücretsiz')+'</span></div><div><span>Servis: '+sr+'</span><span>'+(srv()?tl(srv()):'—')+'</span></div>'+(fee()?'<div><span>Kapıda ödeme bedeli</span><span>'+tl(fee())+'</span></div>':'')+'<div class="t"><span>Genel toplam</span><span>'+tl(total())+'</span></div><div><span>Ödeme</span><span style="text-align:right">'+py+'</span></div><div><span>Teslimat</span><span style="text-align:right">'+V('o_name')+', '+V('o_ilce')+'/'+V('o_il')+'</span></div>'+(R('o_srv')!=='yok'?'<div><span>Randevu</span><span style="text-align:right">'+V('o_gun')+' · '+V('o_saat')+'</span></div>':'')}
function go(n){STEP=n;A('.crt .pane').forEach(function(p){p.classList.remove('on')});var cl=$('#cl');cl.style.display=n===1?'':'none';if(n>1&&n<6)$('#p'+n).classList.add('on');if(n===6)$('#p6').classList.add('on');
 A('#stp span').forEach(function(s,i){s.className=i+1===n?'on':(i+1<n?'ok':'')});$('#stp').style.display=n===6?'none':'';$('#cf').style.display=n===6?'none':'';
 $('#nb').style.display=n>1?'':'none';$('#nx').textContent=n===5?'Siparişi tamamla':'Devam et';$('#ch').textContent=n===1?'Sepetiniz':n===6?'Siparişiniz alındı':'Sipariş';if(n===1)cart();if(n===5)sum();tot();var pn=$('.crt .pn .ls:not([style*=none])');if(pn)pn.scrollTop=0}
function err(m){var e=$('#o_msg');if(STEP===5){e.className='msg er';e.textContent=m}else toast(m)}
function toast(m){var d=document.createElement('div');d.textContent=m;d.style.cssText='position:fixed;left:50%;bottom:90px;transform:translateX(-50%);background:#b91c1c;color:#fff;padding:12px 18px;border-radius:10px;z-index:99;font:600 .88rem sans-serif;max-width:90%';document.body.appendChild(d);setTimeout(function(){d.remove()},3200)}
function valid(n){if(n===2){if(V('o_name').length<3)return 'Ad soyad yazın.';if(V('o_phone').replace(/\D/g,'').length<10)return 'Geçerli bir telefon numarası yazın.';if(!V('o_il')||!V('o_ilce'))return 'İl ve ilçe yazın.';if(R('o_tes')==='kargo'&&V('o_adres').length<10)return 'Teslimat adresini yazın.'}
 if(n===3&&R('o_srv')!=='yok'){if(!V('o_cihaz'))return 'Cihaz marka ve modelini yazın.';if(!V('o_gun'))return 'Randevu gününü seçin.'}
 if(n===4&&!pay())return 'Ödeme yöntemi seçin.';if(n===5&&!$('#o_ok').checked)return 'Sipariş koşullarını onaylayın.';return ''}
function finish(){var b=$('#nx'),old=b.textContent;b.disabled=true;b.textContent='Gönderiliyor…';var no='SP-'+new Date().toISOString().slice(2,10).replace(/-/g,'')+'-'+Math.random().toString(36).slice(2,6).toUpperCase();
 var py=$('input[name=o_pay]:checked').parentNode.querySelector('b').textContent,lines=C.map(function(x){return x.q+' x '+x.n+' ('+x.k+') = '+tl(x.p*x.q)}).join('\n');
 var msg='SİPARİŞ '+no+'\n'+lines+'\nÜrünler: '+tl(sub())+'\nKargo: '+(kargo()?tl(kargo()):'Ücretsiz')+' ('+(R('o_tes')==='elden'?'Mağazadan teslim':'Kargo')+')\nServis: '+({yok:'Sadece parça',takim:'Usta taksın',kesif:'Önce keşif'}[R('o_srv')])+(srv()?' '+tl(srv()):'')+(R('o_srv')!=='yok'?'\nRandevu: '+V('o_gun')+' '+V('o_saat')+'\nCihaz: '+V('o_cihaz')+'\nArıza/Not: '+V('o_not'):'')+'\nÖdeme: '+py+(fee()?' (+'+tl(fee())+')':'')+'\nGENEL TOPLAM: '+tl(total())+'\nAdres: '+V('o_adres')+' '+V('o_ilce')+'/'+V('o_il')+'\nE-posta: '+V('o_mail');
 OKT.post({name:V('o_name'),phone:V('o_phone'),district:V('o_ilce'),type:'siparis',device_type:'Online mağaza',message:msg,page:location.pathname,website:V('o_hp')}).then(function(r){var p=pay(),tt=total(),hv=p==='havale'?'<p style="margin-top:12px">Havale / EFT bilgisi:</p><div class="iban">'+CF.iban+'<br><small>'+CF.hesap+'</small></div><p class="nt">Açıklamaya sipariş numaranızı yazın: <b>'+no+'</b></p>':p==='kart'?'<p class="nt" style="margin-top:12px">Siparişiniz teyit edilince <b>'+V('o_phone')+'</b> numarasına güvenli ödeme bağlantısı göndereceğiz.</p>':'<p class="nt" style="margin-top:12px">Ödemeyi ürün teslim edilirken ('+(p==='kapida_nakit'?'nakit':'kartla')+') yapacaksınız.</p>';
  $('#p6').innerHTML='<div class="done"><div style="font-size:.9rem;color:var(--mut)">Sipariş numaranız</div><div class="no">'+no+'</div><div class="sm" style="justify-content:center;gap:10px">Toplam '+tl(tt)+'</div>'+(r.preview?'<p class="nt" style="margin-top:10px">Önizleme: bu sitede form henüz firmanıza bağlı değil; gerçek sitede sipariş firmanın paneline düşer.</p>':'')+hv+'<div class="tl2"><div class="f">Sipariş alındı<small>Şimdi</small></div><div>Teyit araması<small>Stok, uyumluluk ve ödeme için sizi arayacağız</small></div><div>'+(R('o_srv')==='yok'?'Hazırlık ve kargo':'Hazırlık')+'<small>'+(p==='havale'?'Ödeme hesaba geçince':'Teyitten sonra')+'</small></div>'+(R('o_srv')==='yok'?'':'<div>Usta randevusu<small>'+V('o_gun')+' · '+V('o_saat')+'</small></div>')+'<div>Teslim / montaj tamam<small>Servis fişi ve garanti belgesi verilir</small></div></div><button class="btn" data-cclose type="button" style="width:100%">Alışverişe dön</button></div>';
  C=[];save();badge();go(6)}).catch(function(x){b.disabled=false;b.textContent=old;err(x.message||'Gönderilemedi, tekrar deneyin.')})}
document.addEventListener('DOMContentLoaded',function(){var s=$('#sq');if(!s)return;
 s.addEventListener('input',function(){q=s.value.trim().toLowerCase();draw()});$('#sb').addEventListener('change',function(e){br=e.target.value;draw()});$('#ss').addEventListener('change',function(e){so=e.target.value;draw()});
 A('.cat button').forEach(function(b){b.addEventListener('click',function(){A('.cat button').forEach(function(x){x.classList.remove('on')});b.classList.add('on');cat=b.dataset.c;draw()})});
 A('[data-cart]').forEach(function(b){b.addEventListener('click',function(e){e.preventDefault();if(STEP===6)go(1);document.body.classList.add('copen')})});document.addEventListener('click',function(e){if(e.target.closest('[data-cclose]'))document.body.classList.remove('copen')});
 var hs=document.getElementById('hsq');if(hs)hs.addEventListener('submit',function(e){e.preventDefault();s.value=hs.querySelector('input').value;q=s.value.trim().toLowerCase();draw();document.getElementById('urunler').scrollIntoView({behavior:'smooth'})});
 payopts();$('#o_kargo').textContent=CF.kargo?tl(CF.kargo)+' ('+tl(CF.kargo_esik)+' üzeri ücretsiz)':'Ücretsiz';$('#o_mont').textContent='+'+tl(CF.montaj);$('#o_kes').textContent='+'+tl(CF.kesif);if(CF.adres)$('#o_adr').textContent=CF.adres;
 document.addEventListener('change',function(e){var t=e.target;if(t.type==='radio'){A('input[name='+t.name+']').forEach(function(r){r.closest('.opt').classList.toggle('on',r.checked)});if(t.name==='o_srv')$('#o_sub').classList.toggle('on',t.value!=='yok')}if(t.closest&&t.closest('.crt'))tot()});
 $('#nx').addEventListener('click',function(){if(STEP===1){if(C.length)go(2);return}var m=valid(STEP);if(m){err(m);return}if(STEP===5){finish();return}go(STEP+1)});$('#nb').addEventListener('click',function(){if(STEP>1)go(STEP-1)});
 draw();go(1);badge()})})();"""


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
    drawer = (f'<div class="crt" role="dialog" aria-label="Sepet ve sipariş"><div class="bd" data-cclose></div><div class="pn"><div class="hd"><h3 id="ch">Sepetiniz</h3><button data-cclose aria-label="Kapat">{ic("x", 22)}</button></div>'
              '<div class="stp" id="stp"><span class="on">1 Sepet</span><span>2 Bilgiler</span><span>3 Servis</span><span>4 Ödeme</span><span>5 Onay</span></div>'
              '<div class="ls" id="cl"></div>'
              '<div class="ls pane" id="p2"><div class="fld"><label>Ad soyad *</label><input id="o_name" autocomplete="name"></div><div class="two"><div class="fld"><label>Telefon *</label><input id="o_phone" type="tel" autocomplete="tel"></div><div class="fld"><label>E-posta</label><input id="o_mail" type="email" autocomplete="email"></div></div>'
              '<div class="two"><div class="fld"><label>İl *</label><input id="o_il" autocomplete="address-level1"></div><div class="fld"><label>İlçe *</label><input id="o_ilce" autocomplete="address-level2"></div></div><div class="fld"><label>Açık adres *</label><textarea id="o_adres" autocomplete="street-address"></textarea></div>'
              '<div class="fld"><label>Teslimat yöntemi</label><label class="opt on"><input type="radio" name="o_tes" value="kargo" checked><span><b>Kargo ile adrese teslim</b><small>Stoktaki ürünler aynı gün kargoya verilir.</small></span><em id="o_kargo">—</em></label><label class="opt"><input type="radio" name="o_tes" value="elden"><span><b>Mağazadan teslim al</b><small id="o_adr">Adres bilgisi firma tarafından eklenir.</small></span><em>Ücretsiz</em></label></div></div>'
              '<div class="ls pane" id="p3"><p class="nt" style="margin-bottom:12px">Parçayı kendiniz mi takacaksınız, yoksa usta mı gelsin? Siz karar verin; fiyat önceden yazılı bildirilir.</p>'
              '<label class="opt on"><input type="radio" name="o_srv" value="yok" checked><span><b>Sadece parça gönderin</b><small>Montajı kendim yapacağım / ustam var.</small></span><em>0 ₺</em></label>'
              '<label class="opt"><input type="radio" name="o_srv" value="takim"><span><b>Parça ustamız tarafından takılsın</b><small>Randevu gününde usta parçayı takar, çalıştığını gösterir. Takılan parçaya garanti verilir.</small></span><em id="o_mont">—</em></label>'
              '<label class="opt"><input type="radio" name="o_srv" value="kesif"><span><b>Önce usta arızayı görsün</b><small>Parçanın doğru olduğundan emin değilim; keşif sonrası onayımla parça takılsın.</small></span><em id="o_kes">—</em></label>'
              '<div class="sub" id="o_sub"><div class="two"><div class="fld"><label>Cihaz marka / model *</label><input id="o_cihaz" placeholder="örn. Baymak Duotec 24"></div><div class="fld"><label>Randevu günü *</label><input id="o_gun" type="date"></div></div><div class="fld"><label>Saat aralığı</label><select id="o_saat"><option>09:00 – 12:00</option><option>12:00 – 15:00</option><option>15:00 – 18:00</option></select></div><div class="fld"><label>Arıza / not</label><textarea id="o_not" placeholder="Cihazın belirtisini kısaca yazın"></textarea></div></div></div>'
              '<div class="ls pane" id="p4"><p class="nt" style="margin-bottom:12px">Ödeme yöntemini seçin. Hiçbir yöntemde kart bilginiz bu sayfaya yazılmaz.</p><div id="o_pay"></div></div>'
              '<div class="ls pane" id="p5"><div class="sum2" id="o_sum"></div><label class="ck2"><input type="checkbox" id="o_ok"><span>Ön bilgilendirme koşullarını, mesafeli satış sözleşmesini ve KVKK aydınlatma metnini okudum, onaylıyorum.</span></label><input id="o_hp" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true"><div class="msg" id="o_msg" role="status"></div></div>'
              '<div class="ls pane" id="p6"></div>'
              '<div class="cfo" id="cf"><div class="sm"><span>Toplam</span><span id="ct">0 ₺</span></div><div class="nv"><button class="btn o" id="nb" type="button" style="display:none">Geri</button><button class="btn" id="nx" type="button">Devam et</button></div><p class="nt">Kapıda ödeme, kredi kartı ve havale/EFT seçenekleri bir sonraki adımlardadır.</p></div></div></div>')
    fab = f'<button class="crt-fab" data-cart aria-label="Sepeti aç">{ic("bx", 20)} Sepet <i data-ccount>0</i></button>'
    X.shop_data = data
    return (f'<section class="sec shp{cls}" id="urunler"><div class="w">{head}{bar}{catb}<div class="pg" id="pg"></div></div>'
            f'<script>window.__SHOPCFG={json.dumps(X.r.get("shopcfg", CFG), ensure_ascii=False)};window.__SHOP={data};window.__SHOPIC={json.dumps(ic(X.c["ico"], 54, 1.4))};</script></section>{drawer}{fab}')


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
