import os, html
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html')
os.makedirs(OUT, exist_ok=True)

ICONS = {
 'flame':'<path d="M12 3c1 4 5 5 5 10a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-5 1-9z"/>',
 'snow':'<path d="M12 2v20M4 6l16 12M20 6L4 18"/>',
 'wash':'<rect x="4" y="3" width="16" height="18" rx="2"/><circle cx="12" cy="13" r="4"/><path d="M7 7h2"/>',
 'tv':'<rect x="3" y="5" width="18" height="12" rx="2"/><path d="M8 21h8M12 17v4"/>',
 'phone':'<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>',
 'drop':'<path d="M12 3c4 5 6 8 6 11a6 6 0 0 1-12 0c0-3 2-6 6-11z"/>',
 'bolt':'<path d="M13 2L5 14h6l-1 8 8-12h-6z"/>',
 'cam':'<rect x="2" y="7" width="14" height="10" rx="2"/><path d="M16 11l6-3v8l-6-3"/>',
 'wrench':'<path d="M14 6a4 4 0 0 0 5 5l-9 9a2.5 2.5 0 0 1-4-4l9-9a4 4 0 0 0-1-1z"/>',
 'shield':'<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5L16 9.5"/>',
 'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 'pin':'<path d="M12 21s7-6 7-11a7 7 0 0 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
 'star':'<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
 'check':'<path d="M5 12.5l4.5 4.5L19 7.5"/>',
 'phoneh':'<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
}
def ic(n, s=22):
    return f'<svg class="i" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[n]}</svg>'

SECT = {
 'kombi':dict(ad='Kombi & Isıtma', ico='flame', folder='kombi', hero=['Kombiniz soğuk mu?','Kış gelmeden bakımını yaptırın'], sub='Yetkili servis tecrübesiyle arıza, bakım ve petek temizliği.',
   svc=[('Yıllık bakım','Gaz, basınç ve baca gazı ölçümü','flame'),('Arıza onarım','Hata kodu okuma, ilk ziyarette çözüm','wrench'),('Petek temizliği','Makineli temizlik, basınç testi','drop'),('Montaj','Yeni cihaz kurulumu ve ilk çalıştırma','check')],
   stats=[('12 yıl','sektör tecrübesi'),('18.400','tamamlanan servis'),('%97','ilk ziyarette çözüm'),('4,9/5','müşteri puanı')], brands='BAYMAK · DEMİRDÖKÜM · VAILLANT · BOSCH · ECA'),
 'klima':dict(ad='Klima & Soğutma', ico='snow', folder='klima', hero=['Yaz bastırmadan klimanız hazır olsun','Montaj, bakım, gaz dolumu'], sub='Aynı hafta içinde keşif, temiz montaj ve yazılı garanti.',
   svc=[('Klima montajı','Duvar tipi, salon ve VRF sistemler','snow'),('Periyodik bakım','Filtre, evaporatör, drenaj temizliği','drop'),('Gaz dolumu','Kaçak testi ve basınç ayarı','wrench'),('Arıza onarım','Kart, fan ve kompresör kontrolü','bolt')],
   stats=[('9 yıl','deneyim'),('6.200','montaj'),('24 saat','ortalama dönüş'),('2 yıl','işçilik garantisi')], brands='DAIKIN · MITSUBISHI · ARÇELİK · VESTEL · SAMSUNG'),
 'beyaz':dict(ad='Beyaz Eşya', ico='wash', folder='beyaz-esya', hero=['Çamaşır makineniz mi durdu?','Aynı gün evinizdeyiz'], sub='Buzdolabı, çamaşır, bulaşık makinesi ve fırın onarımı. Parça garantili.',
   svc=[('Buzdolabı','Soğutma, kompresör, termostat','snow'),('Çamaşır makinesi','Pompa, rulman, kart onarımı','wash'),('Bulaşık makinesi','Su alma, ısıtıcı, kilit','drop'),('Fırın & ocak','Rezistans, gaz valfi, sıcaklık sensörü','flame')],
   stats=[('15 yıl','tecrübe'),('31.000','onarım'),('%92','yerinde çözüm'),('6 ay','parça garantisi')], brands='ARÇELİK · BEKO · BOSCH · SAMSUNG · LG'),
 'elektronik':dict(ad='Elektronik & TV', ico='tv', folder='elektronik', hero=['TV ve elektronik cihaz onarımı','Arızayı bulmadan ücret almayız'], sub='Panel, güç kartı ve anakart seviyesinde onarım; yazılı teşhis raporu.',
   svc=[('TV onarımı','Ekran, backlight, güç kartı','tv'),('Ses sistemleri','Amfi, hoparlör, bağlantı sorunları','bolt'),('Anakart tamiri','Lehim ve mikroskop altında onarım','wrench'),('Uydu & anten','Montaj ve sinyal ayarı','cam')],
   stats=[('11 yıl','atölye deneyimi'),('9.800','onarılan cihaz'),('48 saat','ortalama süre'),('3 ay','onarım garantisi')], brands='SAMSUNG · LG · SONY · VESTEL · PHILIPS'),
 'bilgisayar':dict(ad='Bilgisayar & Telefon', ico='phone', folder='bilgisayar-telefon', hero=['Telefon ve bilgisayar tamiri','Çoğu onarım bekleme süresinde'], sub='Ekran, batarya, şarj soketi ve yazılım sorunları. Veriniz güvende.',
   svc=[('Ekran değişimi','Orijinal ve muadil seçenekli','phone'),('Batarya','Kapasite testi ve değişim','bolt'),('Laptop bakımı','Termal macun, fan, SSD yükseltme','wrench'),('Veri kurtarma','Silinen veya bozuk disk','shield')],
   stats=[('8 yıl','deneyim'),('14.000','tamir'),('45 dk','ekran değişimi'),('6 ay','garanti')], brands='APPLE · SAMSUNG · XIAOMI · LENOVO · HP'),
 'tesisat':dict(ad='Tesisat & Su', ico='drop', folder='tesisat', hero=['Su kaçağı mı var?','Hemen geliyoruz'], sub='Kırmadan kaçak tespiti, gider açma ve tesisat yenileme. 7/24 acil hat.',
   svc=[('Su kaçağı tespiti','Cihazla, kırmadan','drop'),('Gider açma','Makineli, kameralı kontrol','wrench'),('Banyo & mutfak','Batarya, rezervuar, sifon','check'),('Tesisat yenileme','Boru değişimi, kolektör','flame')],
   stats=[('7/24','acil hat'),('30 dk','ortalama varış'),('16 yıl','deneyim'),('%98','memnuniyet')], brands='VİTRA · ECA · HANSGROHE · GROHE · E.C.A.'),
 'elektrik':dict(ad='Elektrik', ico='bolt', folder='elektrik', hero=['Elektrik arızasında güvenli çözüm','Sigorta, pano, aydınlatma'], sub='Belgeli elektrik ustası; her işte topraklama ve yazılı fatura.',
   svc=[('Arıza bulma','Kısa devre, kaçak akım','bolt'),('Pano yenileme','Sigorta ve şalter değişimi','wrench'),('Aydınlatma','Spot, avize, led montajı','star'),('Topraklama','Ölçüm ve belgelendirme','shield')],
   stats=[('14 yıl','tecrübe'),('7.500','tamamlanan iş'),('1 saat','ortalama varış'),('1 yıl','işçilik garantisi')], brands='SCHNEIDER · LEGRAND · VIKO · ABB · SIEMENS'),
 'guvenlik':dict(ad='Güvenlik & Kamera', ico='cam', folder='guvenlik', hero=['Evinizi ve iş yerinizi 7/24 izleyin','Kamera, alarm, diyafon'], sub='Ücretsiz keşif, projelendirme ve telefondan canlı izleme.',
   svc=[('Kamera sistemi','IP ve analog, gece görüşlü','cam'),('Alarm','Kablosuz sensör ve siren','shield'),('Diyafon','Görüntülü, akıllı geçiş','phone'),('Uzaktan izleme','Mobil uygulama kurulumu','pin')],
   stats=[('10 yıl','deneyim'),('2.300','kurulum'),('Ücretsiz','keşif'),('2 yıl','garanti')], brands='HIKVISION · DAHUA · UNIVIEW · PARADOX · JABLOTRON'),
}
ORDER = ['kombi','klima','beyaz','elektronik','bilgisayar','tesisat','elektrik','guvenlik']

# 24 palettes: (isim, firma, koyu, vurgu, yumuşak, font, radius)
FONTS = {
 'sans':"Inter,'Segoe UI',system-ui,sans-serif",
 'serif':"Georgia,'Times New Roman',serif",
 'round':"'Trebuchet MS','Segoe UI',sans-serif",
 'cond':"'Arial Narrow','Roboto Condensed',Arial,sans-serif",
 'hum':"'Gill Sans','Calibri','Segoe UI',sans-serif",
}
P = [
 ('Kızıl','Anadolu Kombi','#3a1410','#d9482b','#fdeee9','sans',6),('Kor','Isı Atölyesi','#1d2430','#e8a317','#fdf6e3','cond',2),('Çam','Yeşil Isı Servis','#0f2e24','#2f9e6b','#e8f6ee','hum',10),
 ('Buz','Kutup Klima','#082a3d','#12a4d6','#e5f6fc','sans',8),('Poyraz','Poyraz Soğutma','#1b2a49','#4a7bd8','#eaf0fc','round',14),('Okyanus','Mavi Hat Klima','#052f3b','#0fb5ae','#e3f7f6','cond',4),
 ('Kaymak','Ev Servisi','#4a3626','#c47a3a','#fbf1e6','serif',4),('Pembe','Beyaz Diyar','#3d1d34','#d6457f','#fdeaf3','round',16),('Gümüş','Usta Beyaz Eşya','#262a31','#6b7a90','#eef1f5','sans',2),
 ('Mor','Sinyal Elektronik','#1c1233','#8a5cf6','#f0eafe','sans',10),('Neon','Devre Atölyesi','#07111f','#22d3a0','#e3fbf3','cond',2),('Turuncu','Ekran Doktoru','#2b1708','#f2751a','#fff0e2','round',12),
 ('Lacivert','Hızlı Tamir','#0b1e44','#2b6cf0','#e8f0ff','sans',8),('Cam','Telefon Hastanesi','#10243a','#22b8e8','#e5f7fd','hum',18),('Grafit','Servis Noktası','#202124','#e5483c','#fdecea','cond',2),
 ('Sarı','Acil Tesisat','#17181c','#ffc400','#fff8dc','cond',2),('Su','Damla Tesisat','#0a2c4a','#1c93e3','#e6f3fd','round',16),('Bakır','Bakır Boru','#33201a','#b8673a','#faeee6','serif',3),
 ('Volt','Volt Elektrik','#10131c','#ffd21e','#fffbe0','sans',4),('Kırmızı','Güç Elektrik','#2a0e12','#e23b4a','#fdecee','cond',3),('Petrol','Kablo & Pano','#10292b','#188f9a','#e4f5f6','hum',8),
 ('Zümrüt','Kalkan Güvenlik','#08231b','#14b87a','#e2f8ef','sans',6),('Gece','Göz Güvenlik','#0a0f1c','#3ba0ff','#e5f1ff','cond',2),('Bordo','Sentinel Alarm','#2b0f1c','#c43a62','#fbe9ef','serif',4),
]
# 24 tema: sektör = ORDER[i//3], yerleşim = (i*5+i//3) % 6 -> sektör içi farklı
LAYOUTS = ['split','cover','collage','editorial','diag','tiles']

def img(sector, n, cls='', alt=''):
    folder = SECT[sector]['folder']
    return (f'<div class="im {cls}" data-s="{sector}"><img loading="lazy" src="../photos/{folder}/{n}.jpg" alt="{alt}" '
            f'onerror="this.parentNode.classList.add(\'nf\');this.remove()"><span class="ph">{ic(SECT[sector]["ico"],54)}</span></div>')

def page(i):
    sec = ORDER[i//3]; S = SECT[sec]; pal = P[i]; lay = LAYOUTS[(i*5 + i//3) % 6]
    nm, firma, dark, acc, soft, fk, rad = pal
    num = 7 + i
    slug = f'{num:02d}-{sec}-' + nm.lower().translate(str.maketrans('ıçğöşü','icgosu'))
    h1a, h1b = S['hero']
    svc = ''.join(f'<div class="sc"><div class="sci">{ic(c)}</div><b>{a}</b><span>{b}</span></div>' for a,b,c in S['svc'])
    stats = ''.join(f'<div><b>{a}</b><span>{b}</span></div>' for a,b in S['stats'])
    gal = ''.join(img(sec, n, 'g') for n in (3,4,5,6))
    rev = ''.join(f'<div class="rv"><span class="st">★★★★★</span><p>{t}</p><small>{n} · {w}</small></div>' for t,n,w in [
        ('Aradığım gün geldiler, işi bitirip ortalığı temiz bıraktılar. Fiyatı baştan söylediler, sürpriz çıkmadı.','Ayşe K.','Google yorumu'),
        ('Telefondan randevu aldım, usta saatinde geldi. Yapılan işlemi fotoğraflayıp gönderdiler.','Mehmet D.','Google yorumu'),
        ('Daha önce iki yerden bakılmış, sorunu burada ilk ziyarette çözdüler.','Selin T.','Google yorumu')])
    steps = ''.join(f'<div><i>{k}</i><b>{a}</b><span>{b}</span></div>' for k,(a,b) in enumerate([
        ('Arayın veya formu doldurun','Sorunu kısaca anlatın'),('Randevu ve fiyat aralığı','Saat ve tahmini ücreti önceden bilirsiniz'),('Usta adresinize gelir','İşlem öncesi onayınız alınır'),('Yazılı fiş ve garanti','İşlem kaydı telefonunuza gelir')],1))
    form = f'''<div class="form"><h3>Hızlı randevu</h3><small>2 dakikada doldurun, sizi arayalım.</small>
<div class="f">Adınız soyadınız</div><div class="r2"><div class="f">Telefon</div><div class="f">İlçe</div></div><div class="f">Sorun nedir? (isteğe bağlı)</div><a class="btn">Randevu talep et</a></div>'''
    cta_btns = f'<a class="btn">Randevu al</a><a class="btn gh">{ic("phoneh",18)} 0532 000 00 00</a>'
    chips = ''.join(f'<span>{ic("check",16)}{t}</span>' for t in ['Ücretsiz keşif','Yazılı garanti','Aynı gün servis'])
    if lay=='split':
        hero = f'<section class="hero split"><div class="w"><div><h1>{h1a}<br><em>{h1b}</em></h1><p>{S["sub"]}</p><div class="bt">{cta_btns}</div><div class="ck">{chips}</div></div>{form}</div></section>'
    elif lay=='cover':
        hero = f'<section class="hero cover">{img(sec,1,"bg")}<div class="w"><div><h1>{h1a}<br><em>{h1b}</em></h1><p>{S["sub"]}</p><div class="bt">{cta_btns}</div></div></div></section><div class="chipband"><div class="w">{chips}</div></div>'
    elif lay=='collage':
        hero = f'<section class="hero collage"><div class="w"><div><h1>{h1a}<br><em>{h1b}</em></h1><p>{S["sub"]}</p><div class="bt">{cta_btns}</div><div class="ck">{chips}</div></div><div class="cg">{img(sec,1,"c1")}{img(sec,2,"c2")}{img(sec,7,"c3")}<div class="badge2"><b>4,9/5</b><span>312 Google yorumu</span></div></div></div></section>'
    elif lay=='editorial':
        hero = f'<section class="hero editorial"><div class="w">{img(sec,1,"tall")}<div><small class="kick">{S["ad"]} · {firma}</small><h1>{h1a} <em>{h1b}</em></h1><p>{S["sub"]}</p><div class="bt">{cta_btns}</div><div class="ck">{chips}</div></div></div></section>'
    elif lay=='diag':
        hero = f'<section class="hero diag"><div class="w"><div class="tx"><h1>{h1a}<br><em>{h1b}</em></h1><p>{S["sub"]}</p><div class="bt">{cta_btns}</div></div></div>{img(sec,1,"dg")}</section>'
    else:
        tiles = ''.join(f'<a class="tl">{ic(c,26)}<b>{a}</b><span>{b}</span></a>' for a,b,c in S['svc'])
        hero = f'<section class="hero tiles">{img(sec,1,"bn")}<div class="w"><h1>{h1a} <em>{h1b}</em></h1><p>{S["sub"]}</p></div></section><div class="w pick"><b>Sorununuzu seçin</b><div class="tg">{tiles}</div></div>'
    about = f'<section class="sec ab"><div class="w">{img(sec,2,"abi")}<div><h2>{firma} hakkında</h2><p>Mahallenizdeki işletme olarak her işlemi önce fiyat aralığı ve süreyle size anlatıyor, onayınızı alıp başlıyoruz. İşlem sonunda parça ve işçilik ayrı ayrı yazılı fiş olarak teslim edilir.</p><ul>{"".join(f"<li>{ic("check",18)}{t}</li>" for t in ["Kimlikli, üniformalı usta","Orijinal veya muadil parça seçeneği","Yaptığımız her işe yazılı garanti"])}</ul><a class="btn">Bizi tanıyın</a></div></div></section>'
    team = ''.join(f'<div class="tm">{img(sec,n,"p")}<b>{a}</b><span>{b}</span></div>' for n,a,b in [(8,'Hasan Yıldız','Kurucu usta'),(9,'Emre Kaya','Saha teknisyeni'),(10,'Zeynep Aydın','Müşteri hizmetleri')])
    css = f'''
:root{{--d:{dark};--a:{acc};--s:{soft};--r:{rad}px;--f:{FONTS[fk]}}}
*{{box-sizing:border-box}}body{{margin:0;font-family:var(--f);color:#26303b;font-size:15px;line-height:1.55;padding-bottom:0}}
h1,h2,h3,p{{margin:0}}a{{color:inherit;text-decoration:none}}.w{{max-width:1200px;margin:0 auto;padding:0 40px}}
.i{{flex:none}}
.im{{position:relative;overflow:hidden;border-radius:var(--r);background:linear-gradient(135deg,var(--d),color-mix(in srgb,var(--d) 70%,var(--a)))}}
.im img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.im .ph{{position:absolute;inset:0;display:none;place-items:center;color:#ffffff40}}.im.nf .ph{{display:grid}}
.top{{background:var(--d);color:#ffffffbb;font-size:12.5px;padding:7px 0}}.top .w{{display:flex;justify-content:space-between}}
.nav{{background:#fff;border-bottom:1px solid #eceef2;position:sticky;top:0;z-index:20}}.nav .w{{display:flex;align-items:center;gap:30px;height:70px}}
.lg{{font-weight:800;font-size:21px;color:var(--d);display:flex;align-items:center;gap:9px}}.lg .lm{{width:34px;height:34px;border-radius:var(--r);background:var(--a);color:#fff;display:grid;place-items:center}}
.nav nav{{display:flex;gap:24px;font-weight:600;font-size:14px;margin-left:auto}}.nav .cta{{background:var(--a);color:#fff;padding:11px 20px;border-radius:var(--r);font-weight:700;font-size:14px}}
.burger{{display:none}}#mn{{display:none}}
.btn{{display:inline-flex;align-items:center;gap:8px;background:var(--a);color:#fff;padding:13px 24px;border-radius:var(--r);font-weight:700;font-size:15px}}.btn.gh{{background:transparent;border:2px solid currentColor;margin-left:10px}}
.hero h1{{font-size:46px;letter-spacing:-1px;line-height:1.08}}.hero h1 em{{font-style:normal;color:var(--a)}}.hero p{{font-size:17px;margin:16px 0 26px;max-width:520px}}.bt{{display:flex;flex-wrap:wrap;gap:10px 0}}
.ck{{display:flex;gap:22px;margin-top:26px;font-size:13.5px;flex-wrap:wrap}}.ck span{{display:flex;gap:6px;align-items:center}}.ck .i{{color:var(--a)}}
.form{{background:#fff;color:#26303b;border-radius:var(--r);padding:26px;box-shadow:0 18px 44px #0004}}.form h3{{font-size:20px;color:var(--d)}}.form small{{color:#788}}.f{{border:1px solid #d8dde4;border-radius:var(--r);padding:11px 12px;color:#8a94a2;margin-top:10px;font-size:14px}}.r2{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}.form .btn{{width:100%;justify-content:center;margin-top:14px}}
.hero.split{{background:linear-gradient(105deg,var(--d) 0 60%,color-mix(in srgb,var(--d) 78%,var(--a)));color:#fff;padding:64px 0}}.hero.split .w{{display:grid;grid-template-columns:1.2fr 1fr;gap:56px;align-items:center}}
.hero.cover{{position:relative;color:#fff;padding:120px 0 110px}}.hero.cover .bg{{position:absolute;inset:0;border-radius:0}}.hero.cover .bg::after{{content:"";position:absolute;inset:0;background:linear-gradient(90deg,var(--d) 0,#0000 85%);opacity:.9}}.hero.cover .w{{position:relative;z-index:2}}
.chipband{{background:var(--a);color:#fff}}.chipband .w{{display:flex;gap:34px;padding:14px 40px;font-weight:600;font-size:14px}}.chipband span{{display:flex;gap:7px;align-items:center}}
.hero.collage{{background:var(--s);padding:60px 0}}.hero.collage .w{{display:grid;grid-template-columns:1fr 1fr;gap:50px;align-items:center}}.hero.collage h1{{color:var(--d)}}.hero.collage .btn.gh{{color:var(--d)}}
.cg{{position:relative;height:430px}}.cg .c1{{position:absolute;left:0;top:0;width:62%;height:78%}}.cg .c2{{position:absolute;right:0;top:12%;width:42%;height:48%;border:6px solid var(--s)}}.cg .c3{{position:absolute;right:6%;bottom:0;width:46%;height:38%;border:6px solid var(--s)}}
.badge2{{position:absolute;left:4%;bottom:6%;background:#fff;border-radius:var(--r);padding:12px 16px;box-shadow:0 10px 30px #0002}}.badge2 b{{display:block;font-size:24px;color:var(--d)}}.badge2 span{{font-size:12px;color:#788}}
.hero.editorial{{background:#fff;padding:64px 0}}.hero.editorial .w{{display:grid;grid-template-columns:.9fr 1.1fr;gap:60px;align-items:center}}.tall{{height:500px}}.kick{{text-transform:uppercase;letter-spacing:2px;color:var(--a);font-weight:700;font-size:12px}}.hero.editorial h1{{font-size:50px;margin:12px 0 0;color:var(--d)}}.hero.editorial .btn.gh{{color:var(--d)}}
.hero.diag{{position:relative;background:var(--d);color:#fff;padding:90px 0 100px;overflow:hidden}}.hero.diag .tx{{position:relative;z-index:2;max-width:560px}}.hero.diag .dg{{position:absolute;right:0;top:0;bottom:0;width:48%;border-radius:0;clip-path:polygon(22% 0,100% 0,100% 100%,0 100%)}}
.hero.tiles{{position:relative;color:#fff;padding:72px 0 120px}}.hero.tiles .bn{{position:absolute;inset:0;border-radius:0}}.hero.tiles .bn::after{{content:"";position:absolute;inset:0;background:color-mix(in srgb,var(--d) 78%,transparent)}}.hero.tiles .w{{position:relative;z-index:2}}.hero.tiles h1{{max-width:720px}}
.pick{{position:relative;z-index:3;margin-top:-70px;background:#fff;border-radius:var(--r);box-shadow:0 16px 44px #0002;padding:22px 26px 26px!important;max-width:1120px}}.pick>b{{font-size:15px;color:var(--d)}}.tg{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:12px}}.tl{{border:1px solid #e5e8ee;border-radius:var(--r);padding:16px;display:block}}.tl .i{{color:var(--a)}}.tl b{{display:block;margin-top:8px;color:var(--d)}}.tl span{{font-size:12.5px;color:#788}}
.sec{{padding:64px 0}}.sec h2{{font-size:30px;color:var(--d);margin-bottom:6px}}.sub{{color:#788;margin-bottom:28px}}
.sg{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}.sc{{border:1px solid #e5e8ee;border-radius:var(--r);padding:22px}}.sci{{width:46px;height:46px;border-radius:var(--r);background:var(--s);color:var(--a);display:grid;place-items:center;margin-bottom:12px}}.sc b{{display:block;color:var(--d);margin-bottom:4px}}.sc span{{font-size:13.5px;color:#6b7280}}
.stats{{background:var(--d);color:#fff;padding:38px 0}}.stats .w{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;text-align:center}}.stats b{{display:block;font-size:30px;color:var(--a)}}.stats span{{font-size:13px;color:#ffffffaa}}
.brands{{padding:26px 0;background:#f6f7f9;text-align:center;color:#8a93a5;font-weight:800;letter-spacing:1px;font-size:14px}}
.ab .w{{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:center}}.abi{{height:380px}}.ab p{{margin:10px 0 16px;color:#556}}.ab ul{{list-style:none;padding:0;margin:0 0 20px}}.ab li{{display:flex;gap:8px;align-items:center;margin:7px 0}}.ab li .i{{color:var(--a)}}
.gal{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.g{{height:210px}}
.how{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}}.how>div{{border-top:3px solid var(--a);padding-top:14px}}.how i{{font-style:normal;font-weight:800;color:var(--a);font-size:22px;display:block}}.how b{{display:block;color:var(--d)}}.how span{{font-size:13.5px;color:#6b7280}}
.tms{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}}.tm{{text-align:center}}.tm .p{{height:260px;margin-bottom:10px}}.tm b{{display:block;color:var(--d)}}.tm span{{color:#788;font-size:13px}}
.rvs{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}.rv{{border:1px solid #e5e8ee;border-radius:var(--r);padding:20px;font-size:14px}}.rv .st{{color:var(--a);letter-spacing:2px}}.rv p{{margin:8px 0}}.rv small{{color:#788}}
.band{{background:var(--a);color:#fff;padding:40px 0}}.band .w{{display:flex;justify-content:space-between;align-items:center;gap:20px}}.band h2{{font-size:26px}}.band .btn{{background:#fff;color:var(--d)}}
.ft{{background:var(--d);color:#ffffffaa;padding:44px 0 0;font-size:13.5px}}.ft .w{{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:30px}}.ft b{{display:block;color:#fff;margin-bottom:8px}}.ft div div{{margin:4px 0}}.ft .lb{{border-top:1px solid #ffffff22;margin-top:30px;padding:16px 40px;text-align:center;font-size:12px}}
.mbar{{display:none}}
@media(max-width:700px){{
.w{{padding:0 18px!important}}.top,.nav nav,.nav .cta{{display:none}}
.burger{{display:block;margin-left:auto;font-size:26px;cursor:pointer;color:var(--d)}}
.hero h1,.hero.editorial h1{{font-size:31px}}.hero.split .w,.hero.collage .w,.hero.editorial .w,.ab .w{{grid-template-columns:1fr!important;gap:26px!important}}
.hero.cover{{padding:60px 0}}.chipband .w{{flex-direction:column;gap:6px;padding:14px 18px!important}}.cg{{height:340px}}.tall{{height:260px}}.abi{{height:240px}}
.hero.diag{{padding:50px 0 0}}.hero.diag .dg{{position:relative;width:100%;height:220px;clip-path:none;margin-top:30px}}
.hero.tiles{{padding:44px 0 90px}}.tg,.sg,.how,.rvs,.tms,.stats .w{{grid-template-columns:1fr 1fr}}.tms,.rvs{{grid-template-columns:1fr}}.gal{{grid-template-columns:1fr 1fr}}.g{{height:140px}}
.ft .w{{grid-template-columns:1fr 1fr}}.band .w{{flex-direction:column;text-align:center}}
.btn.gh{{margin-left:0}}
.mbar{{display:grid;grid-template-columns:1fr 1fr 1.3fr;position:fixed;left:0;right:0;bottom:0;z-index:30;background:#fff;border-top:1px solid #e5e8ee;padding:8px;gap:8px}}
.mbar a{{display:flex;justify-content:center;align-items:center;gap:6px;padding:11px 6px;border-radius:var(--r);font-weight:700;font-size:13.5px;background:var(--s);color:var(--d)}}.mbar a:last-child{{background:var(--a);color:#fff}}
body{{padding-bottom:64px}}}}'''
    foot = f'''<footer class="ft"><div class="w"><div><b>{firma}</b>Atatürk Cad. No:12<br>Vergi No: 123 456 7890</div><div><b>Hizmetler</b>{"".join(f"<div>{a}</div>" for a,_,_ in S["svc"])}</div><div><b>Kurumsal</b><div>Hakkımızda</div><div>Hizmet bölgeleri</div><div>Sık sorulan sorular</div><div>İletişim</div><div><a href="__PORTAL_URL__">Müşteri portalı</a></div></div><div><b>Çalışma saatleri</b><div>Hafta içi 08:30 – 19:00</div><div>Cumartesi 09:00 – 16:00</div><div>0532 000 00 00</div></div></div><div class="lb">© 2026 {firma} · KVKK · Çerez politikası · Mesafeli satış</div></footer>'''

    v = lambda k,m: (i*k + i//3) % m
    svc_v, gal_v, rev_v, how_v, st_v, nav_v = v(3,4), v(5,3), v(7,2), v(11,2), v(13,3), v(2,3)
    SV = {
     0: f'<div class="sg">{svc}</div>',
     1: '<div class="sl">' + ''.join(f'<div class="sr"><div class="sci">{ic(c)}</div><div><b>{a_}</b><span>{b_}</span></div><em>Fiyat al →</em></div>' for a_,b_,c in S['svc']) + '</div>',
     2: '<div class="sn">' + ''.join(f'<div>{img(sec, 11+k, "sni")}<i>0{k+1}</i><b>{a_}</b><span>{b_}</span></div>' for k,(a_,b_,c) in enumerate(S['svc'])) + '</div>',
     3: '<div class="sd">' + ''.join(f'<div>{ic(c,30)}<b>{a_}</b><span>{b_}</span></div>' for a_,b_,c in S['svc']) + '</div>',
    }
    GAL = {
     0: f'<div class="gal">{gal}</div>',
     1: '<div class="gal mas">' + img(sec,3,'g big') + img(sec,4,'g') + img(sec,5,'g') + img(sec,6,'g') + img(sec,7,'g') + '</div>',
     2: '<div class="gal strip">' + img(sec,3,'g') + img(sec,4,'g') + img(sec,5,'g') + '</div>',
    }
    REV = {
     0: f'<div class="rvs">{rev}</div>',
     1: f'<div class="rq"><div class="big">“Aradığım gün geldiler, işi bitirip ortalığı temiz bıraktılar. Fiyatı baştan söylediler, sürpriz çıkmadı.”</div><div class="who"><span class="st">★★★★★</span> Ayşe K. · Google yorumu · 4,9/5 (312 yorum)</div></div>',
    }
    HOW = {
     0: f'<div class="how">{steps}</div>',
     1: '<div class="tl2">' + ''.join(f'<div><i>{k}</i><div><b>{a_}</b><span>{b_}</span></div></div>' for k,(a_,b_) in enumerate([('Arayın veya formu doldurun','Sorunu kısaca anlatın'),('Randevu ve fiyat aralığı','Saat ve tahmini ücreti önceden bilirsiniz'),('Usta adresinize gelir','İşlem öncesi onayınız alınır'),('Yazılı fiş ve garanti','İşlem kaydı telefonunuza gelir')],1)) + '</div>',
    }
    stats_sec = f'<section class="stats"><div class="w">{stats}</div></section>'
    SECS = {
     'svc': ('Hizmetler', f'<section class="sec"><div class="w"><h2>Hizmetlerimiz</h2><div class="sub">Sorununuzu seçin, süre ve ücret aralığını görün.</div>{SV[svc_v]}</div></section>'),
     'stats': ('İstatistikler', stats_sec),
     'brands': ('Markalar', f'<div class="brands">{S["brands"]}</div>'),
     'about': ('Hakkımızda', about),
     'gal': ('Galeri', f'<section class="sec"><div class="w"><h2>İşlerimizden</h2><div class="sub">Gerçek müşteri işleri.</div>{GAL[gal_v]}</div></section>'),
     'how': ('Nasıl çalışıyoruz', f'<section class="sec" style="background:#f6f7f9"><div class="w"><h2>Nasıl çalışıyoruz?</h2><div class="sub">Her aşamada ne olacağını bilirsiniz.</div>{HOW[how_v]}</div></section>'),
     'team': ('Ekip', f'<section class="sec"><div class="w"><h2>Ekibimiz</h2><div class="sub">Sizinle ilgilenecek kişiler.</div><div class="tms">{team}</div></div></section>'),
     'rev': ('Yorumlar', f'<section class="sec" style="background:var(--s)"><div class="w"><h2>Müşterilerimiz ne diyor?</h2><div class="sub">Google yorumlarından · 4,9 / 5</div>{REV[rev_v]}</div></section>'),
     'band': ('Çağrı bandı', '<section class="band"><div class="w"><h2>Sorununuzu bugün çözelim</h2><a class="btn">Randevu al</a></div></section>'),
    }
    ORDERS = [
     ['svc','stats','brands','about','gal','how','team','rev','band'],
     ['about','svc','gal','stats','rev','how','band'],
     ['svc','how','about','rev','stats','gal','band'],
     ['brands','svc','gal','about','team','how','rev','band'],
     ['stats','about','svc','rev','gal','how','band'],
     ['svc','gal','rev','about','how','stats','team','band'],
    ]
    order = ORDERS[(i*7 + i//3*2) % 6]
    mid = ''.join(f'<div class="ed" data-nm="{SECS[k][0]}">{SECS[k][1]}</div>' for k in order)
    navcls = ['','dk','ct'][nav_v]
    drwhtml = f'''<div class="drw ed" data-nm="Mobil menü"><div class="dh"><a class="lg"><span class="lm">{ic(S["ico"],20)}</span>{firma}</a><label for="mn" class="cl">✕</label></div>
<div class="dl">{"".join(f'<a><span class="di">{ic(c,20)}</span><b>{t}</b><em>›</em></a>' for t,c in [("Hizmetlerimiz","wrench"),("Markalar","star"),("Hizmet bölgeleri","pin"),("Hakkımızda","shield"),("Sık sorulan sorular","check"),("İletişim","phoneh")])}<a href="__PORTAL_URL__"><span class="di">{ic("check",20)}</span><b>Müşteri portalı</b><em>›</em></a></div>
<div class="dq"><b>Hizmetlerimiz</b>{"".join(f'<span>{a_}</span>' for a_,_,_ in S["svc"])}</div>
<div class="dc"><a class="btn">{ic("phoneh",18)} Hemen ara</a><a class="btn wa">WhatsApp</a></div>
<a class="btn dr">Randevu al</a>
<div class="dn"><div>{ic("clock",16)} Hafta içi 08:30 – 19:00 · Cmt 09:00 – 16:00</div><div>{ic("pin",16)} Atatürk Cad. No:12</div></div></div>
'''
    body = f"""<input type="checkbox" id="mn"><div class="top ed" data-nm="Üst şerit"><div class="w"><span>Pzt–Cmt 08:30–19:00 · Acil için 7/24 arayın</span><span>info@firma.com · 0532 000 00 00</span></div></div>
<header class="nav {navcls} ed" data-nm="Menü"><div class="w"><a class="lg"><span class="lm">{ic(S["ico"],20)}</span>{firma}</a><nav><a>Hizmetler</a><a>Markalar</a><a>Hizmet bölgeleri</a><a>Hakkımızda</a><a>İletişim</a><a class="pt" href="__PORTAL_URL__">Müşteri portalı</a></nav><a class="cta">Randevu al</a><label for="mn" class="burger">☰</label></div></header>
{drwhtml}
<div class="ed" data-nm="Ana görsel">{hero}</div>
{mid}
<div class="ed" data-nm="Portal şeridi"><section class="pband"><div class="w"><div><b>Servisinizi takip edin, ödemenizi online yapın</b><span>Telefon numaranızla giriş yapın; servis durumunuzu, teklifinizi ve ödemenizi görün.</span></div><a class="btn" href="__PORTAL_URL__">Müşteri portalına gir</a></div></section></div>
<div class="ed" data-nm="Alt bilgi">{foot}</div>
<div class="mbar ed" data-nm="Mobil çubuk"><a>{ic("phoneh",18)} Ara</a><a>WhatsApp</a><a>Randevu al</a></div>"""
    css += """

.drw{display:none}
.nav nav a.pt{color:var(--a)}.pband{background:var(--s);padding:34px 0;border-top:1px solid #0000000f}.pband .w{display:flex;align-items:center;justify-content:space-between;gap:24px}.pband b{display:block;font-size:20px;color:var(--d)}.pband span{color:#667;font-size:14.5px}.ft a{color:inherit}
@media(max-width:700px){.pband .w{flex-direction:column;align-items:flex-start}.pband .btn{width:100%;justify-content:center}.nav nav a.pt{display:none}}
@media(max-width:700px){#mn:checked~.drw{display:flex}#mn:checked~.drw~*{}
.drw{position:fixed;inset:0;z-index:60;background:var(--d);color:#fff;flex-direction:column;padding:18px 20px 24px;overflow:auto}
.drw .dh{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}.drw .lg{color:#fff}.drw .cl{width:40px;height:40px;border-radius:50%;background:#ffffff1f;display:grid;place-items:center;font-size:18px;cursor:pointer}
.drw .dl a{display:flex;align-items:center;gap:14px;padding:14px 4px;border-bottom:1px solid #ffffff1c;font-size:18px;font-weight:600}.drw .dl .di{width:38px;height:38px;border-radius:var(--r);background:#ffffff14;color:var(--a);display:grid;place-items:center}.drw .dl b{flex:1;font-weight:600}.drw .dl em{font-style:normal;opacity:.5;font-size:22px}
.drw .dq{margin:18px 0 6px}.drw .dq b{display:block;font-size:11px;letter-spacing:1px;text-transform:uppercase;opacity:.6;margin-bottom:8px}.drw .dq span{display:inline-block;border:1px solid #ffffff33;border-radius:30px;padding:6px 12px;font-size:13px;margin:0 6px 6px 0}
.drw .dc{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}.drw .dc .btn{justify-content:center;background:#ffffff1a}.drw .dc .wa{background:#25d366}
.drw .dr{justify-content:center;margin-top:10px;padding:16px}.drw .dn{margin-top:auto;padding-top:20px;font-size:12.5px;opacity:.75}.drw .dn div{display:flex;gap:8px;align-items:center;margin:5px 0}
.nav.dk{background:var(--d);border-color:#ffffff22}.nav.dk .lg,.nav.dk nav,.nav.dk .burger{color:#fff}
.nav.ct .w{flex-direction:column;height:auto;padding:14px 0;gap:10px}.nav.ct nav{margin:0}.nav.ct .cta{display:none}
.sl{display:grid;gap:10px}.sr{display:flex;align-items:center;gap:16px;border:1px solid #e5e8ee;border-radius:var(--r);padding:16px 20px}.sr .sci{margin:0}.sr div b{display:block;color:var(--d)}.sr div span{font-size:13.5px;color:#6b7280}.sr em{margin-left:auto;font-style:normal;font-weight:700;color:var(--a);white-space:nowrap}
.sn{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}.sni{height:170px;margin-bottom:10px}.sn i{font-style:normal;color:var(--a);font-weight:800}.sn b{display:block;color:var(--d)}.sn span{font-size:13.5px;color:#6b7280}
.sd{display:grid;grid-template-columns:repeat(4,1fr);gap:0;background:var(--d);border-radius:var(--r);overflow:hidden}.sd>div{padding:28px 24px;color:#fff;border-right:1px solid #ffffff1f}.sd .i{color:var(--a)}.sd b{display:block;margin:10px 0 4px}.sd span{font-size:13.5px;color:#ffffffaa}
.gal.mas{grid-template-columns:2fr 1fr 1fr;grid-auto-rows:150px}.gal.mas .g{height:auto}.gal.mas .big{grid-row:span 2}
.gal.strip{grid-template-columns:repeat(3,1fr)}.gal.strip .g{height:300px}
.rq{text-align:center;max-width:820px;margin:0 auto}.rq .big{font-size:26px;line-height:1.4;color:var(--d);font-weight:600}.rq .who{margin-top:16px;color:#788}.rq .st{color:var(--a)}
.tl2{max-width:700px;border-left:3px solid var(--a);padding-left:26px}.tl2>div{display:flex;gap:16px;margin-bottom:22px;position:relative}.tl2>div>i{font-style:normal;background:var(--a);color:#fff;width:34px;height:34px;border-radius:50%;display:grid;place-items:center;font-weight:800;margin-left:-45px;flex:none}.tl2 b{display:block;color:var(--d)}.tl2 span{color:#6b7280;font-size:14px}
@media(max-width:700px){.sn,.sd{grid-template-columns:1fr 1fr}.gal.mas{grid-template-columns:1fr 1fr;grid-auto-rows:120px}.gal.strip{grid-template-columns:1fr}.gal.strip .g{height:160px}.rq .big{font-size:19px}.sr em{display:none}}
body.edit .ed{outline:2px dashed var(--a);outline-offset:-2px;position:relative}
body.edit .ed::before{content:attr(data-nm) " · ✎ Düzenle";position:absolute;left:8px;top:8px;z-index:50;background:var(--a);color:#fff;font:700 11px/1 sans-serif;padding:5px 9px;border-radius:20px}
body.edit .mbar.ed{position:fixed}
"""
    script = "<script>if(/edit=1/.test(location.search))document.body.classList.add('edit');if(/menu=1/.test(location.search)){document.getElementById('mn').checked=true}</script>"
    body += script
    doc = f'<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{firma}</title><style>{css}</style></head><body>{body}</body></html>'
    open(f'{OUT}/{slug}.html','w').write(doc)
    return slug, sec, lay, firma

if __name__=='__main__':
    for i in range(24): print(page(i))
