"""Sektöre özel çalışan araçlar. Her araç: alanlar + calc (tarayıcıda çalışan JS) + sonucu ustaya gönderme.
Veri: hesaplar tarayıcıda yapılır; 'ustaya gönder' /api/public/contact ucuna gider (firmanın Mesajlar kutusu)."""
import json, os, html
HERE = os.path.dirname(os.path.abspath(__file__))
KB = json.load(open(os.path.join(HERE, '..', '..', 'panel', 'kb_codes.json'), encoding='utf-8'))


def N(k, l, v, mn=0, mx=100000, st='any', u=''): return dict(t='num', k=k, l=l, v=v, mn=mn, mx=mx, st=st, u=u)
def S(k, l, o, v=None): return dict(t='sel', k=k, l=l, o=o, v=v)
def G(k, l, o, v=None): return dict(t='seg', k=k, l=l, o=o, v=v or o[0][0])
def C(k, l, o): return dict(t='chk', k=k, l=l, o=o)
def D(k, l): return dict(t='date', k=k, l=l)
def T(k, l, ph=''): return dict(t='txt', k=k, l=l, ph=ph)
def R(k, l, mn, mx, v, st=1, u=''): return dict(t='rng', k=k, l=l, mn=mn, mx=mx, v=v, st=st, u=u)


def e(x): return html.escape(str(x), quote=True)


def field(f):
    k, l = f['k'], e(f['l'])
    t = f['t']
    if t == 'num':
        return f'<label>{l}<span class="u"><input data-k="{k}" type="number" inputmode="decimal" value="{f["v"]}" min="{f["mn"]}" max="{f["mx"]}" step="{f["st"]}">' + (f'<i>{e(f["u"])}</i>' if f['u'] else '') + '</span></label>'
    if t == 'rng':
        return f'<label>{l}<span class="rg"><input data-k="{k}" type="range" min="{f["mn"]}" max="{f["mx"]}" step="{f["st"]}" value="{f["v"]}"><output>{f["v"]}{e(f["u"])}</output></span></label>'
    if t == 'sel':
        if f['o'] and isinstance(f['o'][0], tuple) and isinstance(f['o'][0][1], list):
            opts = ''.join(f'<optgroup label="{e(g)}">' + ''.join(f'<option value="{e(v)}">{e(x)}</option>' for v, x in os_) + '</optgroup>' for g, os_ in f['o'])
        else:
            opts = ''.join(f'<option value="{e(v)}"{" selected" if v == f.get("v") else ""}>{e(x)}</option>' for v, x in f['o'])
        return f'<label>{l}<select data-k="{k}">{opts}</select></label>'
    if t == 'seg':
        return f'<div class="sgw"><span class="sgl">{l}</span><div class="sg">' + ''.join(
            f'<label><input type="radio" name="{{ID}}-{k}" data-k="{k}" value="{e(v)}"{" checked" if v == f["v"] else ""}><span>{e(x)}</span></label>' for v, x in f['o']) + '</div></div>'
    if t == 'chk':
        return f'<div class="sgw"><span class="sgl">{l}</span><div class="ck">' + ''.join(
            f'<label><input type="checkbox" data-k="{k}" value="{e(v)}"><span>{e(x)}</span></label>' for v, x in f['o']) + '</div></div>'
    if t == 'date':
        return f'<label>{l}<input data-k="{k}" type="date"></label>'
    if t == 'txt':
        return f'<label>{l}<input data-k="{k}" type="text" autocomplete="off" placeholder="{e(f.get("ph", ""))}"></label>'


def brands(dom):
    bs = sorted({r['b'] for r in KB if r['d'] == dom})
    return [(b, b.title() if len(b) > 3 else b.upper()) for b in bs]


def kb_json(dom):
    rows = [[r['b'].title() if len(r['b']) > 3 else r['b'].upper(), str(r['c']), r['t'], r['m'], r['f']] for r in KB if r['d'] == dom]
    return json.dumps(rows, ensure_ascii=False, separators=(',', ':'))


KODJS = r"""function(v,H){var c=(v.code||'').trim().toUpperCase().replace(/\s+/g,'');if(!c)return{head:'Hata kodunu yazın',lines:['Örnek: F28, E01, 5E. Ekrandaki ya da yanıp sönen kodu aynen girin.']};
var A=KB.filter(function(r){return(!v.brand||r[0]===v.brand)&&r[1].toUpperCase().replace(/\s+/g,'')===c});
if(!A.length)A=KB.filter(function(r){return(!v.brand||r[0]===v.brand)&&r[1].toUpperCase().replace(/\s+/g,'').indexOf(c)===0}).slice(0,4);
if(!A.length)return{tone:'warn',head:'Bu kod listemizde yok',lines:['Marka seçimini kaldırıp tekrar deneyin ya da kodu aşağıdan ustaya iletin.'],msg:'Hata kodu: '+H.e(c)+' ('+(v.brand||'marka seçilmedi')+')'};
var r=A[0];return{tone:'ok',big:H.e(r[1]),head:H.e(r[2]),lines:A.slice(0,3).map(function(x){return '<b>'+H.e(x[0])+' '+H.e(x[1])+':</b> '+H.e(x[3])+' <i>Ne yapılır:</i> '+H.e(x[4])}),note:'Genel bilgidir; marka ve modele göre değişebilir. Gaz, elektrik ve basınçlı sistemlere kendiniz müdahale etmeyin.',msg:'Hata kodu '+r[0]+' '+r[1]+' — '+r[2]}}"""


def bakim(ad, freqs, tips):
    return dict(id='bakim', ico='cal', title=ad, intro='Son bakım tarihini seçin; sonraki bakım gününü ve kalan süreyi hesaplayalım.',
                fields=[D('last', 'Son bakım ya da kurulum tarihi'), G('freq', 'Bakım sıklığı', freqs)],
                calc=r"""function(v,H){if(!v.last)return{head:'Tarihi seçin',lines:['Bilmiyorsanız cihazı aldığınız ya da kurdurduğunuz tarihi seçin.']};
var d=new Date(v.last),n=new Date();n.setHours(0,0,0,0);var m=parseInt(v.freq,10)||12,nx=new Date(d);nx.setMonth(nx.getMonth()+m);var g=Math.round((nx-n)/864e5);
var s=nx.toLocaleDateString('tr-TR',{day:'numeric',month:'long',year:'numeric'});var T=%s;
if(g<0)return{tone:'bad',big:Math.abs(g)+' gün gecikti',head:'Bakım zamanı geçmiş',lines:['Olması gereken tarih: '+s].concat(T),msg:'Bakım gecikmiş ('+Math.abs(g)+' gün). Son bakım: '+v.last};
if(g<=30)return{tone:'warn',big:g+' gün kaldı',head:'Bakım zamanı yaklaşıyor',lines:['Sonraki bakım: '+s].concat(T),msg:'Bakım yaklaşıyor ('+g+' gün). Son bakım: '+v.last};
return{tone:'ok',big:g+' gün',head:'Bakımınız güncel',lines:['Sonraki bakım: '+s],msg:'Bakım takibi: sonraki bakım '+s}}""" % json.dumps(tips, ensure_ascii=False))


def karar(ad, devs, intro):
    return dict(id='karar', ico='wr', title=ad, intro=intro,
                fields=[S('dev', 'Cihaz', devs), N('yas', 'Cihaz yaşı', 6, 0, 40, 1, 'yıl'), N('tamir', 'Tahmini onarım bedeli', 2500, 0, 500000, 50, '₺'), N('yeni', 'Aynı sınıf yeni cihaz fiyatı', 18000, 0, 5000000, 100, '₺')],
                calc=r"""function(v,H){var L={cm:12,bm:11,bd:14,fo:15,tv:9,ses:12,pc:5,ph:4};var o=L[v.dev]||10,r=v.yeni>0?v.tamir/v.yeni:0,y=v.yas/o,pct=Math.round(r*100);
var big=pct+'%',lines=['Onarım bedeli yeni cihazın %'+pct+"'i",'Ortalama ömrün %'+Math.min(100,Math.round(y*100))+"'i kullanılmış (yaklaşık ömür "+o+' yıl)'];
var t,h;if(r>=.5||(y>=.9&&r>=.3)){t='bad';h='Yeni cihaz daha mantıklı görünüyor'}else if(r>=.35||y>=.8){t='warn';h='Sınırda: ikinci bir teşhis alın'}else{t='ok';h='Onarım mantıklı'}
return{tone:t,big:big,head:h,lines:lines,note:'Kural: onarım bedeli yeni fiyatın yarısını aşıyorsa ya da cihaz ömrünün sonuna yaklaşmışsa yeni cihaz öne çıkar. Garanti kapsamı ve parça bulunabilirliği sonucu değiştirebilir.',msg:'Onarım/yeni karar aracı: yaş '+v.yas+', onarım '+v.tamir+' ₺, yeni '+v.yeni+' ₺ → '+h}}""")


def steps_tool(tid, ico, title, intro, label, opts, data):
    """Senaryo seç -> adım adım ilk müdahale. data: {anahtar: (başlık, ton, [adımlar], not)}"""
    js = 'function(v,H){var M=%s;var m=M[v.s];if(!m)return{head:"Seçim yapın"};return{tone:m[1],head:m[0],steps:m[2],note:m[3]||"",msg:"Durum: "+m[0]}}' % json.dumps({k: list(x) for k, x in data.items()}, ensure_ascii=False)
    return dict(id=tid, ico=ico, title=title, intro=intro, fields=[S('s', label, opts)], calc=js)


def checks_tool(tid, ico, title, intro, label, opts, weights, bands, fixes, bad=''):
    """Kontrol listesi -> puan. weights {anahtar: puan}; bands [(eşik, ton, başlık)]; fixes {anahtar: öneri}"""
    js = r"""function(v,H){var W=%s,F=%s,B=%s;var p=0,a=(v.c||[]);a.forEach(function(k){p+=W[k]||0});if(!a.length)return{head:'Size uyan maddeleri işaretleyin',lines:[]};
var b=B[0];for(var i=0;i<B.length;i++){if(p>=B[i][0])b=B[i]}
return{tone:b[1],big:p+' puan',head:b[2],lines:a.map(function(k){return F[k]}).filter(Boolean),note:%s,msg:'Kontrol listesi: '+a.length+' madde, '+p+' puan → '+b[2]}}""" % (
        json.dumps(weights, ensure_ascii=False), json.dumps(fixes, ensure_ascii=False), json.dumps([list(b) for b in bands], ensure_ascii=False), json.dumps(bad, ensure_ascii=False))
    return dict(id=tid, ico=ico, title=title, intro=intro, fields=[C('c', label, opts)], calc=js)


# ------------------------------------------------------------------------------------------- araç kataloğu
TOOLS = {}

# ---- KOMBİ
TOOLS['kombi.kod'] = dict(id='kod', ico='se', title='Kombi hata kodu çözücü', intro='Kombinin ekranında ya da ışıklarında görünen kodu yazın; anlamını ve ne yapılacağını görün.',
                          fields=[S('brand', 'Marka', [('', 'Tümü')] + brands('kombi')), T('code', 'Hata kodu', 'F28')], calc=KODJS, kb='kombi')
TOOLS['kombi.bakim'] = bakim('Yıllık kombi bakımı hatırlatıcı', [('12', 'Yılda bir'), ('6', '6 ayda bir')],
                             ['Bakımda yanma ayarı, eşanjör ve emniyet elemanları kontrol edilir.', 'Kış gelmeden bakım yaptırmak yoğun dönemde randevu bulmayı kolaylaştırır.'])
TOOLS['kombi.teshis'] = steps_tool('teshis', 'th', 'Kombi sorun sihirbazı', 'Belirtiyi seçin; güvenle yapabileceğiniz kontrolleri ve ustayı çağırma zamanını görün.', 'Belirti',
    [('basinc', 'Basınç düşüyor / çok yükseliyor'), ('sicak', 'Sıcak su gelmiyor ya da ılık'), ('petek', 'Petekler ısınmıyor'), ('ses', 'Kombiden gürültü geliyor'), ('hata', 'Ekranda hata kodu yanıp sönüyor'), ('koku', 'Gaz kokusu alıyorum')],
    {'basinc': ('Basınç sorunu', 'warn', ['Kombi kapalıyken manometreye bakın; soğukken ideal değer yaklaşık 1–1,5 bar.', 'Düşükse kullanım kılavuzundaki doldurma vanasıyla yavaşça tamamlayın, 1,5 barı geçirmeyin.', 'Sık sık düşüyorsa sistemde kaçak ya da genleşme tankı sorunu olabilir: usta çağırın.'], 'Basınç 3 barı aşıyorsa kombiyi kapatın ve servis çağırın.'),
     'sicak': ('Sıcak su sorunu', 'warn', ['Sıcak su ayarının ve şebeke su basıncının yeterli olduğunu kontrol edin.', 'Yalnızca sıcak su etkileniyorsa eşanjör kireçlenmesi ya da 3 yollu vana arızası olabilir.', 'Hata kodu varsa yukarıdaki hata kodu çözücüye girin.'], 'Kendiniz parça açmayın; yetkili/ehliyetli usta gerekir.'),
     'petek': ('Petekler ısınmıyor', 'warn', ['Petek vanalarının açık olduğunu kontrol edin.', 'Peteği elinizle tutun: üstü soğuk altı sıcaksa içinde hava vardır; petek peteğini hava tahliyesi ile boşaltın.', 'Hava aldıktan sonra basıncı tekrar kontrol edin.'], 'Hâlâ ısınmıyorsa sirkülasyon pompası ya da kirli tesisat olabilir.'),
     'ses': ('Kombi gürültüsü', 'warn', ['Kaynama/çıtırtı sesi kireç ya da düşük su akışına işaret eder.', 'Vınlama sirkülasyon pompasından gelebilir.', 'Ses artıyorsa cihazı kapatın.'], 'Ses sürekliyse bakım zamanı gelmiş demektir.'),
     'hata': ('Hata kodu yanıyor', 'warn', ['Kodu aynen not edin ve hata kodu çözücüye girin.', 'Cihazı bir kez kapatıp açarak sıfırlayın (kılavuzdaki reset yöntemiyle).', 'Kod geri gelirse ustaya iletin.'], 'Tekrar eden kodlar kendiliğinden geçmez.'),
     'koku': ('Gaz kokusu: ACİL', 'bad', ['Elektrik düğmesi, çakmak ya da telefonla uğraşmayın; açık alev yakmayın.', 'Pencereleri açın, doğalgaz vanasını kapatın.', 'Binadan çıkın ve ALO 187 doğalgaz acil hattını arayın.', 'Koku giderilip cihaz kontrol edilmeden kombiyi çalıştırmayın.'], 'Bu durumda önce 187, sonra servis.')})
TOOLS['kombi.kw'] = dict(id='kw', ico='fl', title='Kombi kapasitesi hesabı', intro='Evinizin büyüklüğüne ve yalıtımına göre yaklaşık kombi gücünü bulun.',
                         fields=[N('m2', 'Isıtılacak alan', 110, 20, 600, 5, 'm²'), G('yal', 'Yalıtım', [('iyi', 'İyi'), ('orta', 'Orta'), ('zayif', 'Zayıf')], 'orta'), G('tip', 'Bina', [('daire', 'Daire'), ('mustakil', 'Müstakil')])],
                         calc=r"""function(v,H){var w={iyi:65,orta:90,zayif:120}[v.yal]*(v.tip==='mustakil'?1.2:1),kw=v.m2*w/1000,S=[24,28,35,42,50],r=S[S.length-1];for(var i=0;i<S.length;i++){if(S[i]>=kw){r=S[i];break}}
return{tone:'ok',big:H.n(kw,1)+' kW',head:'Önerilen kombi: '+r+' kW',lines:['Yaklaşık '+H.n(r*860,0)+' kcal/saat','Anlık sıcak su verdiği için kombilerde 24 kW altı önerilmez; çok banyolu evlerde bir üst sınıf düşünülebilir.'],note:'Yaklaşık bir hesaptır; kesin seçim için yerinde keşif ve ısı kaybı hesabı gerekir.',msg:'Kombi kapasite: '+v.m2+' m², yalıtım '+v.yal+', '+v.tip+' → '+r+' kW'}}""")

# ---- KLİMA
TOOLS['klima.btu'] = dict(id='btu', ico='sn', title='BTU hesaplayıcı', intro='Oda ölçüsünü ve güneş durumunu girin; hangi kapasitede klima gerektiğini görün.',
                          fields=[N('m2', 'Oda alanı', 20, 5, 200, 1, 'm²'), N('h', 'Tavan yüksekliği', 2.6, 2, 6, .1, 'm'), G('sun', 'Güneş', [('az', 'Az'), ('orta', 'Orta'), ('cok', 'Çok')], 'orta'), R('kisi', 'Odada kalan kişi', 1, 8, 2), G('mut', 'Mutfak/cihaz ısısı', [('0', 'Yok'), ('1', 'Var')])],
                          calc=r"""function(v,H){var b=v.m2*{az:500,orta:600,cok:700}[v.sun]*(v.h/2.6)+Math.max(0,v.kisi-2)*600+(v.mut==='1'?4000:0),S=[9000,12000,18000,24000,30000,36000],r=S[S.length-1];for(var i=0;i<S.length;i++){if(S[i]>=b){r=S[i];break}}
return{tone:'ok',big:H.n(Math.round(b/100)*100)+' BTU',head:'Önerilen klima: '+H.n(r)+' BTU/saat',lines:['Yaklaşık '+H.n(r*0.000293,1)+' kW soğutma gücü','Hesap sonucundan hemen üstteki standart kapasite seçilir.'],note:'Yaklaşık hesaptır. Batı cephesi, çatı katı ve geniş camlı odalarda bir üst kapasiteyi değerlendirin.',msg:'BTU hesabı: '+v.m2+' m², tavan '+v.h+' m, güneş '+v.sun+', '+v.kisi+' kişi → '+r+' BTU'}}""")
TOOLS['klima.kod'] = dict(id='kod', ico='se', title='Klima hata kodu çözücü', intro='İç ünitedeki ışık ya da ekran kodunu yazın; anlamını ve ilk adımı görün.',
                          fields=[S('brand', 'Marka', [('', 'Tümü')] + brands('klima')), T('code', 'Hata kodu', 'E1')], calc=KODJS, kb='klima')
TOOLS['klima.bakim'] = bakim('Klima bakım ve filtre hatırlatıcı', [('12', 'Yılda bir'), ('6', '6 ayda bir')],
                             ['Filtreleri ayda bir yıkamak verimi korur.', 'Sezon başlamadan bakım, ilk sıcakta randevu sıkışıklığını önler.'])
TOOLS['klima.montaj'] = dict(id='montaj', ico='wr', title='Montaj ön keşif', intro='Montaj yerinizi anlatın; ustanın hazırlıklı gelmesi için gereken bilgiyi çıkaralım.',
                             fields=[G('tip', 'Sistem', [('split', 'Tek split'), ('multi', 'Multi (2 iç ünite)')]), N('boru', 'İç–dış ünite arası mesafe', 4, 1, 30, 1, 'm'), G('dis', 'Dış ünite yeri', [('balkon', 'Balkon / duvar'), ('cephe', 'Dış cephe'), ('teras', 'Teras / çatı')]), N('kat', 'Bulunduğunuz kat', 2, 0, 30, 1, '')],
                             calc=r"""function(v,H){var L=[],ek=Math.max(0,v.boru-3);L.push(v.tip==='multi'?'Tahmini iş süresi: 5–7 saat':'Tahmini iş süresi: 2–4 saat');L.push(ek>0?'Standart 3 m borunun üstünde yaklaşık '+ek+' m ek boru gerekir':'Standart boru boyu yeterli görünüyor');
if(v.dis==='cephe'&&v.kat>3)L.push('Dış cephede çalışma için iskele/halat ekipmanı gerekebilir; bina yönetimi izni sorulmalıdır');if(v.dis==='teras')L.push('Çatı/terasta taşıyıcı ayak ve su yalıtımı kontrol edilir');
L.push('Yanınızda hazır olsun: ayrı sigorta hattı (priz noktası), tahliye yeri, bina yönetimi onayı');return{tone:'ok',big:v.boru+' m',head:'Montaj ön bilgisi hazır',lines:L,note:'Kesin metraj ve tutar yerinde keşifle belirlenir.',msg:'Klima montaj keşfi: '+v.tip+', mesafe '+v.boru+' m, dış ünite '+v.dis+', kat '+v.kat}}""")
TOOLS['klima.tasarruf'] = dict(id='tasarruf', ico='bo', title='Klima elektrik gideri', intro='Günlük kullanımınıza göre aylık yaklaşık elektrik giderini görün.',
                               fields=[S('btu', 'Klima kapasitesi', [('9000', '9.000 BTU'), ('12000', '12.000 BTU'), ('18000', '18.000 BTU'), ('24000', '24.000 BTU')], '12000'), G('inv', 'Tip', [('1', 'Inverter'), ('0', 'Sabit hızlı')]), R('saat', 'Günlük kullanım', 1, 24, 8, 1, ' sa'), N('fiyat', 'kWh fiyatı (kendi tarifenizi yazın)', 3, 0.5, 20, 0.1, '₺')],
                               calc=r"""function(v,H){var base={9000:.75,12000:1,18000:1.5,24000:2}[v.btu],kw=base*(v.inv==='1'?.6:1),kwh=kw*v.saat*30,tl=kwh*v.fiyat;
return{tone:'ok',big:H.n(tl,0)+' ₺/ay',head:'Aylık yaklaşık '+H.n(kwh,0)+' kWh',lines:['Ortalama çekilen güç yaklaşık '+H.n(kw,2)+' kW','Inverter ile sabit hızlı arasındaki fark: aynı kullanımda yaklaşık %40'],note:'Değerler ortalamadır; yalıtım, dış sıcaklık ve ayar derecesi sonucu değiştirir.',msg:'Klima gider hesabı: '+v.btu+' BTU, '+(v.inv==='1'?'inverter':'sabit')+', '+v.saat+' sa/gün'}}""")

# ---- BEYAZ EŞYA
TOOLS['beyaz.karar'] = karar('Tamir mi, yeni cihaz mı?', [('cm', 'Çamaşır makinesi'), ('bm', 'Bulaşık makinesi'), ('bd', 'Buzdolabı'), ('fo', 'Fırın / ocak')], 'Yaşı, onarım bedelini ve yeni fiyatı girin; bütçenizi korumak için hangisinin mantıklı olduğunu görün.')
TOOLS['beyaz.belirti'] = dict(id='belirti', ico='wm', title='Arıza belirtisi rehberi', intro='Cihazınızın belirtisini seçin; olası nedenleri ve kendiniz güvenle deneyebileceğiniz adımları görün.',
    fields=[S('s', 'Belirti', [('Çamaşır makinesi', [('cm-su', 'Su almıyor'), ('cm-bos', 'Suyu boşaltmıyor'), ('cm-sik', 'Sıkma yapmıyor'), ('cm-ses', 'Titriyor / çok gürültülü')]),
                              ('Bulaşık makinesi', [('bm-tem', 'İyi yıkamıyor'), ('bm-bos', 'Dipte su kalıyor'), ('bm-kur', 'Kurutmuyor')]),
                              ('Buzdolabı', [('bd-sog', 'Yeterince soğutmuyor'), ('bd-buz', 'Buz tutuyor / su akıtıyor'), ('bd-ses', 'Sürekli çalışıyor / ses yapıyor')]),
                              ('Fırın / ocak', [('fo-isi', 'Fırın ısınmıyor'), ('fo-ocak', 'Ocak tutuşmuyor')])])],
    calc=r"""function(v,H){var M={'cm-su':['Su almıyor',['Su musluğu kapalı veya giriş filtresi tıkalı olabilir','Su giriş valfi arızası','Kapak kilidi tam kapanmıyor'],['Musluğun açık olduğunu görün','Fişi çekip hortum girişindeki ince filtreyi temizleyin','Kapağı sıkıca kapatıp tekrar deneyin']],
'cm-bos':['Suyu boşaltmıyor',['Pompa filtresinde yabancı cisim (para, çorap, tel)','Boşaltma hortumu kıvrık/tıkalı','Pompa arızası'],['Fişi çekin; pompa filtresini (alt ön kapak) altına havlu/tepsi koyarak temizleyin','Hortumun kıvrık olmadığını kontrol edin']],
'cm-sik':['Sıkma yapmıyor',['Dengesiz yük (cihaz kendini korur)','Kapak kilidi/sensör','Motor kömürü veya kart sorunu'],['Çamaşırları dağıtıp programı yeniden başlatın','Tek büyük parça yıkıyorsanız yanına birkaç parça ekleyin']],
'cm-ses':['Titreme / gürültü',['Nakliye cıvataları sökülmemiş','Ayaklar dengesiz','Rulman aşınması'],['Arkadaki nakliye cıvatalarının sökülü olduğuna bakın','Ayarlı ayakları sabitleyip su terazisiyle dengeleyin']],
'bm-tem':['İyi yıkamıyor',['Alt filtre ve püskürtme kolu delikleri tıkalı','Tuz/parlatıcı bitmiş','Yanlış yerleştirme veya deterjan'],['Filtreyi çıkarıp yıkayın','Püskürtme kolu deliklerini kürdanla açın','Tuz ve parlatıcı seviyesini kontrol edin']],
'bm-bos':['Dipte su kalıyor',['Filtre ve gider tıkalı','Gider hortumu kıvrık','Tahliye pompası'],['Filtreyi temizleyin','Lavabo sifonundaki hortum bağlantısını kontrol edin']],
'bm-kur':['Kurutmuyor',['Parlatıcı bitmiş','Rezistans arızası'],['Parlatıcı haznesini doldurun','Programın sonunda kapağı aralayın']],
'bd-sog':['Yeterince soğutmuyor',['Kapak contası kaçırıyor','Termostat ayarı/yanlış yerleştirme','Kompresör ya da soğutucu gaz sorunu'],['Termostat ayarını orta-yüksek konuma alın','Kapak contasını kağıt testiyle kontrol edin','Arka/ alt ızgarayı tozdan arındırın, duvardan 5 cm açın']],
'bd-buz':['Buz tutuyor / su akıtıyor',['Defrost tahliye deliği tıkalı','Kapak contası nem alıyor','Defrost rezistansı'],['Buzdolabını boşaltıp buzunu çözün, tahliye deliğini ılık suyla açın','Kapağın tam kapandığından emin olun']],
'bd-ses':['Sürekli çalışıyor / ses',['Kapak açık kalıyor ya da conta bozuk','Kondenser tozlu','Fan/kompresör'],['Kondenser tozunu temizleyin','Aşırı doluysa hava dolaşımı için boşaltın']],
'fo-isi':['Fırın ısınmıyor',['Rezistans','Termostat/ sıcaklık sensörü','Sigorta / besleme'],['Sigortayı kontrol edin','Farklı bir pişirme modunu deneyin (üst-alt)']],
'fo-ocak':['Ocak tutuşmuyor',['Ocak başlığı kirlenmiş','Ateşleme bujisi ıslak/kirli','Gaz girişi kapalı'],['Ocak başlığını söküp kurulayın','Gaz vanasının açık olduğunu kontrol edin. Gaz kokusu varsa ALO 187’yi arayıp binayı havalandırın.']]};
var m=M[v.s];if(!m)return{head:'Belirti seçin'};return{tone:'warn',head:m[0],lines:['<b>Olası nedenler:</b>'].concat(m[1]),steps:m[2],note:'Elektrikli cihazlarda fişi çekmeden iç parçaya dokunmayın. Gaz ve kart onarımları için usta çağırın.',msg:'Arıza belirtisi: '+m[0]}}""")
TOOLS['beyaz.parca'] = dict(id='parca', ico='bx', title='Yedek parça talebi hazırlayıcı', intro='Cihaz ve model bilgisini yazın; ustamız doğru parçayı eşleştirip size dönsün.',
    fields=[S('dev', 'Cihaz', [('Çamaşır makinesi', 'Çamaşır makinesi'), ('Bulaşık makinesi', 'Bulaşık makinesi'), ('Buzdolabı', 'Buzdolabı'), ('Fırın / ocak', 'Fırın / ocak'), ('Kurutma makinesi', 'Kurutma makinesi')]), T('marka', 'Marka', 'Arçelik'), T('model', 'Model / ürün kodu', 'Etiketteki kod'), T('parca', 'Aradığınız parça', 'Pompa, rezistans, conta…')],
    calc=r"""function(v,H){if(!v.model&&!v.parca)return{head:'Model ve parça bilgisini yazın',lines:['Model kodu cihazın kapak içi, arka panel ya da yan etiketinde yazar.']};
return{tone:'ok',big:H.e(v.dev),head:'Parça talebiniz hazır',lines:['Marka: '+H.e(v.marka||'-'),'Model: '+H.e(v.model||'-'),'Parça: '+H.e(v.parca||'-'),'Model kodunu etiketin fotoğrafıyla WhatsApp’tan da gönderebilirsiniz.'],msg:'Parça talebi — '+v.dev+' / '+v.marka+' / '+v.model+' / '+v.parca}}""")
TOOLS['beyaz.liste'] = checks_tool('liste', 'ok', 'Aylık cihaz bakım listesi', 'Yaptıklarınızı işaretleyin; cihazınızın ne kadar bakımlı olduğunu görün.', 'Bu ay yaptıklarınız',
    [('pompa', 'Çamaşır makinesi pompa filtresi temizlendi'), ('cekmece', 'Deterjan çekmecesi yıkandı'), ('conta', 'Kapak contası silinip kurulandı'), ('sicak', 'Boş makinede sıcak yıkama yapıldı'), ('hortum', 'Su hortumu ve bağlantılar kontrol edildi'), ('bulfiltre', 'Bulaşık makinesi filtresi temizlendi'), ('arka', 'Buzdolabı arka ızgarası tozdan temizlendi')],
    {'pompa': 15, 'cekmece': 10, 'conta': 10, 'sicak': 15, 'hortum': 15, 'bulfiltre': 20, 'arka': 15},
    [(0, 'bad', 'Bakım bekliyor'), (35, 'warn', 'Orta: bazı işler eksik'), (70, 'ok', 'Cihazlarınız bakımlı')],
    {'pompa': 'Pompa filtresi temizliği boşaltma arızalarının en yaygın önleyicisidir.', 'cekmece': 'Çekmece temizliği koku ve küf oluşumunu önler.', 'conta': 'Conta nemi kurulanınca küf ve kaçak riski azalır.', 'sicak': 'Ayda bir sıcak yıkama kireç ve deterjan birikimini azaltır.', 'hortum': 'Hortum bağlantılarını kontrol etmek su baskınını önler.', 'bulfiltre': 'Filtre temizliği yıkama performansını korur.', 'arka': 'Tozsuz kondenser buzdolabının daha az enerji harcamasını sağlar.'},
    'Listenin tamamı yapıldıysa bakım için usta çağırmanız şart değil; yıllık genel kontrol yine önerilir.')

# ---- ELEKTRONİK
TOOLS['tv.teshis'] = steps_tool('teshis', 'tv', 'Televizyon arıza sihirbazı', 'Ekranda ne görüyorsunuz? Seçin; olası arıza bölgesini ve ilk kontrolleri görün.', 'Belirti',
    [('acilmiyor', 'Hiç açılmıyor'), ('kirmizi', 'Kırmızı ışık yanıyor ama açılmıyor'), ('ses', 'Ses var, görüntü yok'), ('cizgi', 'Ekranda çizgi / bozulma'), ('yarim', 'Ekranın bir kısmı karanlık'), ('kapan', 'Kendiliğinden kapanıp açılıyor'), ('sesyok', 'Görüntü var, ses yok')],
    {'acilmiyor': ('Güç hattı sorunu', 'warn', ['Prizi ve uzatma kablosunu başka bir cihazla deneyin', 'Fişi 60 saniye çekip tekrar takın', 'Kumandanın pillerini değiştirin; panel düğmesiyle açmayı deneyin'], 'Hiçbir ışık yoksa genellikle güç kartı incelenir.'),
     'kirmizi': ('Bekleme (standby) modunda takılma', 'warn', ['Fişi çekip 1 dakika bekleyin', 'Kumanda yerine cihazın üzerindeki düğmeyi deneyin'], 'Kırmızı ışık varken açılmıyorsa güç kartı ya da anakart gerekir.'),
     'ses': ('Aydınlatma (backlight) arızası olabilir', 'warn', ['Ekrana el feneriyle yandan bakın; silik görüntü görüyorsanız backlight arızasıdır', 'Başka bir kaynak (HDMI) deneyin'], 'Arka ışık şeritlerinin değişimi genelde mümkündür.'),
     'cizgi': ('Panel veya T-con kartı', 'warn', ['Kabloyu/kaynağı değiştirin; menüde de çizgi varsa panel kaynaklıdır'], 'Dikey çizgiler çoğunlukla bağlantı ya da T-con kartıyla ilgilidir.'),
     'yarim': ('Backlight şeritlerinden biri', 'warn', ['Parlaklığı değiştirip bölgenin kaybolup kaybolmadığına bakın'], 'Şerit (LED bar) değişimi çözüm olabilir.'),
     'kapan': ('Isınma / güç kaynağı / yazılım', 'warn', ['Havalandırma boşluklarını açın', 'Uyku zamanlayıcıyı ve otomatik kapanmayı kapatın', 'Fabrika ayarlarını deneyin'], 'Isındıktan sonra tekrarlıyorsa güç kartındaki kapasitörler sorun olabilir.'),
     'sesyok': ('Ses ayarı ya da ses çıkışı', 'ok', ['Sessiz ve ses çıkışı (ARC/optik) ayarını kontrol edin', 'Harici kaynakta ses çıkışını TV hoparlörüne alın'], 'Hoparlör arızası ender; çoğunlukla ayar sorunudur.')})
TOOLS['tv.kod'] = dict(id='kod', ico='se', title='Televizyon hata ve LED kodu çözücü', intro='TV’nin kırmızı ışık sayısı ya da ekrandaki kodu yazın.',
                       fields=[S('brand', 'Marka', [('', 'Tümü')] + brands('televizyon')), T('code', 'Kod', '3')], calc=KODJS, kb='televizyon')
TOOLS['tv.karar'] = karar('Onarım değer hesabı', [('tv', 'Televizyon'), ('ses', 'Ses sistemi / soundbar'), ('ph', 'Telefon / tablet')], 'Cihazınızı onartmak mı, yenilemek mi? Üç sayıyı girin, mantıklı olanı görün.')
TOOLS['tv.teslim'] = dict(id='teslim', ico='dc', title='Cihaz teslim fişi önizleme', intro='Cihazı atölyeye bırakmadan önce teslim bilgilerini hazırlayın; fişi ustaya iletin.',
    fields=[S('dev', 'Cihaz', [('Televizyon', 'Televizyon'), ('Ses sistemi', 'Ses sistemi'), ('Projeksiyon', 'Projeksiyon'), ('Uydu alıcısı', 'Uydu alıcısı')]), T('marka', 'Marka / model', 'Samsung UE50…'), T('seri', 'Seri no (varsa)', ''), C('acc', 'Birlikte teslim edilenler', [('Güç kablosu', 'Güç kablosu'), ('Kumanda', 'Kumanda'), ('Ayak / duvar aparatı', 'Ayak / duvar aparatı'), ('Kutu', 'Kutu')]), T('ariza', 'Arıza', 'Ekran gelmiyor')],
    calc=r"""function(v,H){var a=(v.acc||[]).join(', ')||'Aksesuar yok';return{tone:'ok',big:H.e(v.dev),head:'Teslim fişi taslağı',lines:['Marka/model: '+H.e(v.marka||'-'),'Seri no: '+H.e(v.seri||'-'),'Aksesuar: '+H.e(a),'Arıza: '+H.e(v.ariza||'-'),'Teslim sırasında ekran ve gövdenin mevcut hali fotoğraflanır.'],msg:'Teslim fişi: '+v.dev+' / '+v.marka+' / '+v.seri+' / '+a+' / '+v.ariza}}""")

# ---- BİLGİSAYAR
TOOLS['pc.saglik'] = checks_tool('saglik', 'cp', 'Cihaz sağlık testi', 'Yaşadığınız belirtileri işaretleyin; cihazınızın ne kadar acil müdahale istediğini görün.', 'Belirtiler',
    [('yavas', 'Açılışı ve programlar çok yavaş'), ('fan', 'Fan sürekli yüksek sesle çalışıyor'), ('isinma', 'Cihaz aşırı ısınıyor'), ('pil', 'Pil hızlı bitiyor ya da şişmiş'), ('mavi', 'Mavi ekran / kendiliğinden yeniden başlıyor'), ('disk', 'Diskten tıkırtı / vurma sesi geliyor'), ('virus', 'Reklam, tuhaf pencere, bilinmeyen program var'), ('sarj', 'Şarj olmuyor ya da şarj girişi gevşek')],
    {'yavas': 10, 'fan': 10, 'isinma': 15, 'pil': 20, 'mavi': 25, 'disk': 40, 'virus': 15, 'sarj': 15},
    [(0, 'ok', 'Genel bakım yeterli olabilir'), (20, 'warn', 'Bakım ve yükseltme önerilir'), (40, 'bad', 'Yakın zamanda servis gerekli'), (60, 'bad', 'Acil: veri yedeği alın ve cihazı kullanmayı bırakın')],
    {'yavas': 'Yavaşlık için genellikle SSD ve RAM yükseltmesi ya da temiz kurulum yeterlidir.', 'fan': 'Toz ve kuruyan macun fan sesine yol açar: iç temizlik ve termal macun yenileme.', 'isinma': 'Isınma uzun vadede kart hasarına yol açabilir; en kısa sürede iç temizlik.', 'pil': 'Şişmiş pil güvenlik riskidir: cihazı şarja takmayın ve pili değiştirtin.', 'mavi': 'Mavi ekran sürücü, bellek ya da disk kaynaklı olabilir; teşhis gerekir.', 'disk': 'Tıkırtı sesi diskin ölmek üzere olduğu anlamına gelebilir: cihazı kapatın ve veri kurtarma için getirin.', 'virus': 'Zararlı yazılım temizliği ve güvenli yeniden kurulum.', 'sarj': 'Şarj girişi lehim hasarı sık görülen arızadır; zorlamayın.'},
    'Veriniz değerliyse ilk iş yedek almaktır.')
TOOLS['pc.veri'] = dict(id='veri', ico='dl', title='Veri kurtarma acil rehberi', intro='Verinizi kaybettiyseniz ilk dakikalar önemli. Durumu seçin, yapılacak ve yapılmayacakları görün.',
    fields=[S('ort', 'Ortam', [('hdd', 'Dizüstü / masaüstü HDD'), ('ssd', 'SSD / NVMe'), ('usb', 'USB bellek / SD kart'), ('tel', 'Telefon / tablet')]), S('dur', 'Ne oldu?', [('sil', 'Dosyaları yanlışlıkla sildim'), ('gor', 'Disk görünmüyor'), ('ses', 'Tıkırtı / vurma sesi geliyor'), ('su', 'Suya düştü / yandı'), ('for', 'Yanlışlıkla formatladım')])],
    calc=r"""function(v,H){var D={sil:['Silinen dosya: kurtarma şansı yüksek',['Cihazı kullanmayı bırakın; yeni veri yazmak eski veriyi ezer','Çöp kutusuna ve sürüm geçmişine bakın','Gerekirse cihazı olduğu gibi getirin'],'warn'],gor:['Disk görünmüyor',['Kabloyu ve portu değiştirin, tekrar deneyin','Disk bölümü bozulmuş ya da elektronik arıza olabilir','Disk yönetiminde “başlat/format” önerisini kabul etmeyin'],'warn'],ses:['Mekanik arıza şüphesi: ACİL',['Cihazı hemen kapatın; çalıştırmaya devam etmek yüzeye zarar verir','Kendiniz açmayın, dondurucuya koymayın','Temiz ortamda uzman müdahalesi gerekir'],'bad'],su:['Sıvı teması: ACİL',['Gücü hemen kesin, pili çıkarın; çalıştırmayı denemeyin','Pirinçle kurutma çözüm değildir','Kurumadan kart oksitlenir: en kısa sürede getirin'],'bad'],'for':['Formatlanmış: şansı olabilir',['Hiçbir şey yazmayın, yeni kurulum yapmayın','Cihazı olduğu gibi getirin'],'warn']};
var d=D[v.dur];var extra=v.ort==='ssd'?'SSD’lerde silinen veri TRIM nedeniyle hızla kaybolabilir; zaman kritiktir.':v.ort==='tel'?'Telefon şifresini ve hesap bilgilerini hazır bulundurun.':'';
return{tone:d[2],head:d[0],steps:d[1],note:extra,msg:'Veri kurtarma: ortam '+v.ort+', durum '+v.dur}}""")
TOOLS['pc.upgrade'] = dict(id='upgrade', ico='cp', title='Yükseltme önerisi', intro='Cihazınız yavaşladıysa hangi parçanın fark yaratacağını görün.',
    fields=[G('kul', 'Kullanım', [('ofis', 'Ofis / internet'), ('tasarim', 'Tasarım / video'), ('oyun', 'Oyun')]), S('ram', 'Bellek (RAM)', [('4', '4 GB'), ('8', '8 GB'), ('16', '16 GB'), ('32', '32 GB')], '8'), G('dep', 'Depolama', [('hdd', 'HDD'), ('ssd', 'SSD')]), N('yas', 'Cihaz yaşı', 5, 0, 20, 1, 'yıl')],
    calc=r"""function(v,H){var L=[],need={ofis:8,tasarim:16,oyun:16}[v.kul];if(v.dep==='hdd')L.push('<b>1. öncelik: SSD.</b> HDD’den SSD’ye geçmek açılış ve program hızında en büyük farkı yapar');
if(+v.ram<need)L.push('RAM’i '+need+' GB’a çıkarın (şu an '+v.ram+' GB)');else L.push('RAM yeterli görünüyor');if(v.yas>=7)L.push('Cihaz '+v.yas+' yaşında: pil ve termal macun yenileme de performansı geri getirir');if(v.kul==='oyun'||v.kul==='tasarim')L.push('Ekran kartı/işlemci sınırlıysa yükseltme sınırlı kalabilir; yerinde inceleme önerilir');
return{tone:'ok',big:v.dep==='hdd'?'SSD':(+v.ram<need?'RAM':'Bakım'),head:'Önerilen yükseltme sırası',lines:L,msg:'Yükseltme: '+v.kul+', '+v.ram+' GB, '+v.dep+', '+v.yas+' yaş'}}""")
TOOLS['pc.paket'] = dict(id='paket', ico='pr', title='Bakım paketi süre hesabı', intro='İstediğiniz işleri seçin; yaklaşık işlem süresini ve getirmeniz gerekenleri görün.',
    fields=[C('c', 'İşlemler', [('format', 'Format ve temiz kurulum'), ('temiz', 'İç temizlik + termal macun'), ('ssd', 'SSD takma ve veri taşıma'), ('ram', 'RAM yükseltme'), ('yedek', 'Yedekleme'), ('virus', 'Virüs / zararlı yazılım temizliği')])],
    calc=r"""function(v,H){var T={format:2,temiz:1.5,ssd:2,ram:.5,yedek:1.5,virus:2},a=v.c||[];if(!a.length)return{head:'İşlem seçin'};var s=0;a.forEach(function(k){s+=T[k]});if(a.length>2)s*=.8;
var g=s>6?'1–2 iş günü':(s>3?'Aynı gün (yarım gün)':'1–3 saat');return{tone:'ok',big:H.n(s,1)+' saat',head:'Tahmini işlem süresi: '+g,lines:['Şarj aletinizi ve cihaz şifrenizi getirin','Önemli verileriniz için yedek ortam (harici disk) gerekebilir','Yazılım lisanslarını/ürün anahtarlarını not edin'],note:'Süreler cihaza ve veri miktarına göre değişir.',msg:'Bakım paketi: '+a.join(', ')+' (~'+H.n(s,1)+' sa)'}}""")

# ---- TESİSAT
TOOLS['tes.kacak'] = dict(id='kacak', ico='dr', title='Su kaçağı testi', intro='Tüm muslukları ve su kullanan cihazları kapatın. Sayacı okuyun, 1 saat bekleyin, tekrar okuyun.',
    fields=[N('a', 'İlk okuma (m³)', 123.456, 0, 99999, .001, 'm³'), N('b', '1 saat sonraki okuma (m³)', 123.456, 0, 99999, .001, 'm³'), N('fiyat', 'Su birim fiyatı (kendi faturanızdan)', 40, 1, 500, .5, '₺/m³')],
    calc=r"""function(v,H){var d=v.b-v.a;if(d<0)return{head:'İkinci okuma ilkinden küçük olamaz'};if(d<0.0005)return{tone:'ok',big:'Kaçak yok',head:'Sayaç hareket etmemiş',lines:['Bir saatte tüketim görülmedi: bu testte kaçak belirtisi yok','Kaçak yalnızca kullanım anında oluşuyorsa (sifon, batarya) test yakalamayabilir'],msg:'Kaçak testi: hareket yok'};
var L=d*1000,gun=L*24,ay=gun*30/1000;return{tone:'bad',big:H.n(L,1)+' L/saat',head:'Sayaç hareket ediyor: kaçak şüphesi',lines:['Günde yaklaşık '+H.n(gun,0)+' litre','Ayda yaklaşık '+H.n(ay,1)+' m³ ≈ '+H.n(ay*v.fiyat,0)+' ₺ boşa gidiyor','Önce rezervuar (sifon) ve bataryalara bakın; bulamazsanız cihazlı kaçak tespiti gerekir'],note:'Sayacın yakınındaki ana vanayı kapatıp sayaç duruyorsa kaçak bina içindedir.',msg:'Su kaçağı testi: '+H.n(L,1)+' L/saat sayaç hareketi'}}""")
TOOLS['tes.damla'] = dict(id='damla', ico='dr', title='Damlayan musluk maliyeti', intro='Bir dakikadaki damla sayısını sayın; bir ayda ne kadar su ve para kaybettiğinizi görün.',
    fields=[R('dk', 'Dakikadaki damla sayısı', 5, 300, 40, 5, ''), N('fiyat', 'Su birim fiyatı', 40, 1, 500, .5, '₺/m³'), N('adet', 'Damlayan musluk sayısı', 1, 1, 20, 1, '')],
    calc=r"""function(v,H){var l=v.dk*0.05*60*24*30/1000*v.adet,tl=l/1000*v.fiyat;return{tone:l>100?'bad':'warn',big:H.n(l,0)+' L/ay',head:'Yaklaşık '+H.n(tl,1)+' ₺/ay boşa gidiyor',lines:['Yılda yaklaşık '+H.n(l*12/1000,2)+' m³ su','Çoğu zaman conta ya da kartuş değişimiyle çözülür'],note:'Hesapta bir damla ≈ 0,05 ml alınmıştır.',msg:'Damlayan musluk: '+v.dk+' damla/dk, '+v.adet+' adet → '+H.n(l,0)+' L/ay'}}""")
TOOLS['tes.acil'] = steps_tool('acil', 'ex', 'Acil durum ilk müdahale', 'Durumu seçin; usta gelene kadar zararı azaltacak adımları görün.', 'Durum',
    [('patlak', 'Boru patladı / su fışkırıyor'), ('tasma', 'Gider taşıyor'), ('tavan', 'Tavandan su damlıyor'), ('sicak', 'Sıcak su hiç gelmiyor'), ('koku', 'Kanalizasyon kokusu'), ('zayif', 'Musluklardan su zayıf akıyor')],
    {'patlak': ('Boru patlağı: ACİL', 'bad', ['Daire ya da bina ana su vanasını kapatın', 'Elektrik panosunu ıslak bölgeden önce kapatın', 'Eşyaları su yolundan çekin, kovalarla suyu toplayın', 'Fotoğraf çekip ustayı arayın'], 'Su elektrik tesisatına ulaşmışsa kimseyi o alana sokmayın.'),
     'tasma': ('Gider taşması', 'warn', ['Suyu kullanmayı bırakın, tıkanmış giderde su vermeyin', 'Bölgedeki giderlere kimyasal dökmeyin', 'Sıçrama olursa elektrik prizlerinden uzak durun'], 'Birden fazla gider birlikte taşıyorsa kolon hattı tıkalıdır: yönetimi ve ustayı arayın.'),
     'tavan': ('Tavandan sızıntı', 'bad', ['Altına kova koyun, tavanı iğneyle delerek suyu kontrollü boşaltın', 'Işık armatürü ıslaksa o hattın sigortasını kapatın', 'Üst kat komşuyu uyarın ve ana vanasını kapattırın'], 'Kaynak belirsizse kaçak tespit cihazı gerekir.'),
     'sicak': ('Sıcak su yok', 'warn', ['Kombi/şofben ve sıcak su vanasını kontrol edin', 'Hata kodu varsa not edin', 'Tek musluk etkilenmişse batarya kartuşu olabilir'], 'Isıtıcı çalışıyor ama sıcak gelmiyorsa tesisatta tıkanıklık aranır.'),
     'koku': ('Kokuyu kesme', 'ok', ['Sifon ve zemin giderine su dökün: kuruyan su sifonu koku yapar', 'Havalandırmayı açın', 'Koku sürerse kolon hattı kontrolü gerekir'], 'Sürekli kokuda hava sızdırmazlık ve havalandırma boruları incelenir.'),
     'zayif': ('Su basıncı düşük', 'warn', ['Batarya başlığındaki perlatörü sökün ve kirecinden arındırın', 'Ana vana tam açık mı kontrol edin', 'Tüm musluklarda zayıfsa şebeke ya da hidrofor sorunu olabilir'], 'Tek musluk etkileniyorsa başlık/kartuş değişimi yeterli olur.')})
TOOLS['tes.sure'] = dict(id='sure', ico='cl', title='İş süresi planlayıcı', intro='Yaptıracağınız işleri seçin; ustanın ne kadar süreceğini ve gün planını görün.',
    fields=[C('c', 'İşler', [('tik', 'Tıkalı gider açma'), ('batarya', 'Batarya / musluk değişimi'), ('rezer', 'Rezervuar / sifon onarımı'), ('kacak', 'Cihazlı kaçak tespiti'), ('petek', 'Petek temizliği (tek daire)'), ('wc', 'Klozet değişimi')])],
    calc=r"""function(v,H){var T={tik:[1,2],batarya:[1,2],rezer:[1,2],kacak:[2,4],petek:[4,8],wc:[2,4]},a=v.c||[];if(!a.length)return{head:'İş seçin'};var lo=0,hi=0;a.forEach(function(k){lo+=T[k][0];hi+=T[k][1]});
return{tone:'ok',big:lo+'–'+hi+' saat',head:hi>8?'Birden fazla güne yayılabilir':'Çoğunlukla tek ziyarette biter',lines:['Su kesintisi gerekebilir: yönetime önceden haber verin','Çalışma alanını boşaltın, ıslanabilecek eşyaları kaldırın'],note:'Süreler ortalamadır; tesisatın durumu ve parça temini değiştirir.',msg:'İş süresi planı: '+a.join(', ')+' ('+lo+'–'+hi+' sa)'}}""")

# ---- ELEKTRİK
TOOLS['elk.kesit'] = dict(id='kesit', ico='bo', title='Kablo kesiti hesabı', intro='Cihazın gücünü ve kablo boyunu girin; uygun bakır kablo kesitini ve sigortayı görün.',
    fields=[N('p', 'Cihaz gücü', 3.5, .1, 100, .1, 'kW'), G('faz', 'Şebeke', [('1', 'Tek faz (230 V)'), ('3', 'Üç faz (400 V)')]), N('l', 'Kablo uzunluğu', 25, 1, 500, 1, 'm')],
    calc=r"""function(v,H){var p=v.p*1000,ph=v.faz==='3',I=ph?p/(1.732*400*.9):p/(230*.95),rho=0.0175,dU=ph?400*.03:230*.03,S=ph?(1.732*rho*v.l*I*.9)/dU:(2*rho*v.l*I*.95)/dU;
var Z=[1.5,2.5,4,6,10,16,25,35,50,70],A=[15,21,28,36,50,68,89,111,134,171],r=Z[Z.length-1],ai=A[A.length-1];for(var i=0;i<Z.length;i++){if(Z[i]>=S&&A[i]>=I*1.15){r=Z[i];ai=A[i];break}}
var F=[10,16,20,25,32,40,50,63],f=F[F.length-1];for(var j=0;j<F.length;j++){if(F[j]>=I*1.05&&F[j]<=ai){f=F[j];break}}
return{tone:'ok',big:r+' mm²',head:'Önerilen bakır kablo: '+r+' mm²',lines:['Hesaplanan akım yaklaşık '+H.n(I,1)+' A','Gerilim düşümü %3 sınırına göre minimum kesit '+H.n(S,2)+' mm²','Önerilen otomat sigorta: '+f+' A (B tipi)'],note:'Ön bilgidir. Tesisat uygulaması ve topraklama için belgeli elektrik ustası ve proje gerekir.',msg:'Kablo kesiti: '+v.p+' kW, '+(ph?'3 faz':'1 faz')+', '+v.l+' m → '+r+' mm²'}}""")
TOOLS['elk.maliyet'] = dict(id='maliyet', ico='bo', title='Aylık elektrik gideri', intro='Cihaz sürelerini kaydırıcılarla ayarlayın; aylık yaklaşık tüketimi görün.',
    fields=[R('ut', 'Elektrikli soba / ısıtıcı (2000 W)', 0, 12, 0, 1, ' sa'), R('al', 'Klima (1000 W ortalama)', 0, 24, 4, 1, ' sa'), R('fi', 'Fırın (2200 W)', 0, 6, 1, 1, ' sa'), R('tv', 'TV + uydu (150 W)', 0, 24, 5, 1, ' sa'), R('pc', 'Bilgisayar (250 W)', 0, 24, 4, 1, ' sa'), R('su', 'Elektrikli su ısıtıcı (2000 W)', 0, 8, 1, 1, ' sa'), N('fiyat', 'kWh fiyatı (kendi faturanızdan)', 3, .5, 20, .1, '₺')],
    calc=r"""function(v,H){var d=(v.ut*2+v.al*1+v.fi*2.2+v.tv*.15+v.pc*.25+v.su*2)+1.2,ay=d*30,tl=ay*v.fiyat;return{tone:'ok',big:H.n(tl,0)+' ₺/ay',head:'Yaklaşık '+H.n(ay,0)+' kWh/ay',lines:['Günlük yaklaşık '+H.n(d,1)+' kWh (buzdolabı + aydınlatma tabanı dahil)','En büyük kalem: '+(v.ut*2>=v.al&&v.ut*2>=v.fi*2.2&&v.ut*2>=v.su*2?'ısıtıcı':(v.al>=v.fi*2.2&&v.al>=v.su*2?'klima':(v.su>=v.fi?'su ısıtıcı':'fırın')))],note:'Tahmini tüketimdir; faturanızdaki kademeli tarife ve vergiler sonucu değiştirir.',msg:'Elektrik gider hesabı: '+H.n(ay,0)+' kWh/ay ≈ '+H.n(tl,0)+' ₺'}}""")
TOOLS['elk.sigorta'] = dict(id='sigorta', ico='sh', title='Pano sigorta seçici', intro='Devre türünü seçin; genel kabul gören sigorta ve kablo değerlerini görün.',
    fields=[S('d', 'Devre', [('ayd', 'Aydınlatma'), ('priz', 'Genel priz'), ('ocak', 'Elektrikli fırın / ocak (7 kW’a kadar)'), ('klima', 'Klima (12.000–18.000 BTU)'), ('sofben', 'Elektrikli şofben / termosifon'), ('camasir', 'Çamaşır / bulaşık makinesi')])],
    calc=r"""function(v,H){var M={ayd:['B10 A','1,5 mm²','30 mA kaçak akım rölesi (grup)'],priz:['B16 A','2,5 mm²','30 mA kaçak akım rölesi'],ocak:['B32 A','6 mm²','Ayrı hat, 30 mA kaçak akım rölesi'],klima:['B16 A','2,5 mm²','Ayrı hat, kaçak akım rölesi'],sofben:['B20 A','4 mm²','Ayrı hat, 30 mA kaçak akım rölesi'],camasir:['B16 A','2,5 mm²','Ayrı hat, 30 mA kaçak akım rölesi']},m=M[v.d];
return{tone:'ok',big:m[0],head:'Önerilen sigorta ve kablo',lines:['Otomat sigorta: '+m[0],'Bakır kablo: '+m[1],'Koruma: '+m[2],'Topraklama hattı zorunludur'],note:'Genel kabul gören ön değerlerdir. Uygulama; kablo boyu, döşeme tipi ve mevzuata göre belgeli usta tarafından belirlenmelidir.',msg:'Sigorta seçimi: '+v.d+' → '+m[0]+' / '+m[1]}}""")
TOOLS['elk.acil'] = steps_tool('acil', 'ex', 'Elektrik acil durum rehberi', 'Durumu seçin; usta gelene kadar güvenliğiniz için yapılacakları görün.', 'Durum',
    [('carpma', 'Biri elektrik çarpıldı'), ('yangin', 'Pano/prizden duman ya da yanık kokusu'), ('atiyor', 'Sigorta sürekli atıyor'), ('kaçak', 'Kaçak akım rölesi atıyor'), ('oda', 'Yalnızca bir odada elektrik yok')],
    {'carpma': ('ACİL: 112’yi arayın', 'bad', ['Kişiye dokunmadan önce ana şalteri kapatın (ya da kuru tahta/plastikle ayırın)', '112’yi arayın', 'Bilinci yoksa solunum ve nabzı kontrol edin; gerekirse temel yaşam desteği uygulayın'], 'Güvenli olmadan kimseye çıplak elle dokunmayın.'),
     'yangin': ('Yangın riski: ACİL', 'bad', ['Ana şalteri kapatın', 'Elektrik yangınına suyla müdahale etmeyin; kuru toz tüple müdahale edin', 'Kontrol dışıysa binayı boşaltın ve 110’u arayın'], 'Şalteri kapatamıyorsanız kimseyi yaklaştırmayın.'),
     'atiyor': ('Sigorta atması', 'warn', ['Hangi cihaz çalışırken attığını not edin', 'Cihazı çıkarıp sigortayı bir kez kaldırın', 'Cihaz çıkınca atmıyorsa cihaz arızalıdır; atıyorsa hat aşırı yüklüdür'], 'Sürekli atmayı sigortayı büyütüp çözmeyin; kablo yanmasına neden olur.'),
     'kaçak': ('Kaçak akım', 'warn', ['Tüm sigortaları kapatın, röleyi kaldırın', 'Sigortaları tek tek açarak kaçak hattı bulun', 'Islak mekân (banyo, mutfak) ve şofben ilk bakılacak yerlerdir'], 'Kaçak akım rölesini devre dışı bırakmayın.'),
     'oda': ('Tek oda elektriksiz', 'ok', ['Odanın sigortasını kontrol edin', 'Prizlerden birinin fişi kısa devre yapmış olabilir', 'Sigorta sağlamsa klemens/bağlantı gevşemiştir'], 'Pano açmadan önce ana şalteri kapatın.')})

# ---- GÜVENLİK
TOOLS['gvn.depo'] = dict(id='depo', ico='ca', title='Kamera kayıt depolama hesabı', intro='Kamera sayısı ve çözünürlüğü girin; kaç TB diskin yeteceğini görün.',
    fields=[R('n', 'Kamera sayısı', 1, 32, 8, 1, ''), G('mp', 'Çözünürlük', [('2', '2 MP'), ('4', '4 MP'), ('8', '8 MP (4K)')], '4'), G('codec', 'Sıkıştırma', [('264', 'H.264'), ('265', 'H.265')], '265'), R('gun', 'Kayıt saklama süresi', 3, 90, 15, 1, ' gün'), G('mod', 'Kayıt tipi', [('s', 'Sürekli'), ('h', 'Hareketle')], 's')],
    calc=r"""function(v,H){var mb={2:2,4:4,8:8}[v.mp]*(v.codec==='265'?.55:1)*(v.mod==='h'?.4:1),tb=v.n*mb*10.8*v.gun/1000,D=[1,2,4,6,8,10,12,16,20],r=D[D.length-1];for(var i=0;i<D.length;i++){if(D[i]>=tb*1.1){r=D[i];break}}
return{tone:'ok',big:H.n(tb,1)+' TB',head:'Önerilen disk: '+r+' TB',lines:['Kamera başına yaklaşık '+H.n(mb,1)+' Mbps','Günlük toplam yaklaşık '+H.n(tb*1000/v.gun,0)+' GB','Hesaba %10 güvenlik payı eklenmiştir'],note:'Gerçek değer sahne hareketine ve kamera ayarlarına göre değişir.',msg:'Kamera depolama: '+v.n+' kamera, '+v.mp+' MP, '+v.codec+', '+v.gun+' gün → '+r+' TB'}}""")
TOOLS['gvn.kesif'] = dict(id='kesif', ico='sh', title='Güvenlik keşif sihirbazı', intro='Mekânınızı tarif edin; başlangıç için kaç kamera ve sensör gerektiğini görün.',
    fields=[S('yer', 'Mekân', [('daire', 'Daire'), ('villa', 'Villa / müstakil'), ('dukkan', 'Dükkân / ofis'), ('depo', 'Depo / fabrika')]), N('giris', 'Dış giriş kapısı sayısı', 1, 1, 10, 1, ''), N('pencere', 'Zemin / erişilebilir pencere', 4, 0, 40, 1, ''), N('alan', 'Kapalı alan', 120, 20, 5000, 10, 'm²'), G('bahce', 'Bahçe / dış alan', [('0', 'Yok'), ('1', 'Var')])],
    calc=r"""function(v,H){var cam=v.giris+(v.bahce==='1'?2:0)+(v.yer==='villa'?2:0)+(v.yer==='depo'?Math.ceil(v.alan/400):0)+(v.yer==='dukkan'?1:0),kon=v.giris+Math.ceil(v.pencere*.6),pir=Math.max(1,Math.ceil(v.alan/60)),dum=Math.max(1,Math.ceil(v.alan/80));
return{tone:'ok',big:cam+' kamera',head:'Başlangıç paketi önerisi',lines:[cam+' kamera ('+(v.bahce==='1'?'bahçe dahil':'iç/dış giriş ağırlıklı')+')','Manyetik kapı/pencere kontağı: '+kon+' adet','Hareket (PIR) dedektörü: '+pir+' adet','Duman dedektörü: '+dum+' adet','1 siren ve 1 kumanda paneli'],note:'Önerilen sayılar ön keşif içindir; mekânın krokisi ve kör noktalar yerinde incelenir.',msg:'Güvenlik keşfi: '+v.yer+', '+v.alan+' m², '+v.giris+' giriş → '+cam+' kamera, '+kon+' kontak, '+pir+' PIR'}}""")
TOOLS['gvn.risk'] = dict(id='risk', ico='lk', title='Güvenlik açığı kontrol listesi', intro='Doğru olanları işaretleyin; hangi önlemlerin eksik olduğunu görün.',
    fields=[C('c', 'Mevcut önlemler', [('kilit', 'Giriş kapısı çok noktalı kilitli'), ('pencere', 'Balkon / pencere kilitleri var'), ('isik', 'Dış aydınlatma hareket sensörlü'), ('kayit', 'Kayıt cihazı kilitli yerde ve yedekli'), ('alarm', 'Alarm düzenli test ediliyor'), ('anahtar', 'Yedek anahtar dışarıda saklanmıyor'), ('duman', 'Duman / gaz dedektörü var'), ('kamera', 'Girişi gören kamera var')])],
    calc=r"""function(v,H){var all={kilit:'Çok noktalı kilit ya da çelik kapı',pencere:'Pencere/balkon kilidi',isik:'Sensörlü dış aydınlatma',kayit:'Kayıt cihazını kilitli ve yedekli yere alma',alarm:'Alarmı aylık test etme',anahtar:'Yedek anahtarı dışarıdan kaldırma',duman:'Duman ve gaz dedektörü',kamera:'Girişi gören kamera'},have=v.c||[],miss=Object.keys(all).filter(function(k){return have.indexOf(k)<0}),p=Math.round(have.length/8*100);
var t=p>=75?'ok':(p>=40?'warn':'bad'),h=p>=75?'İyi durumdasınız':(p>=40?'Orta düzey güvenlik':'Ciddi eksikler var');return{tone:t,big:'%'+p,head:h,lines:miss.length?['<b>Eksikler:</b>'].concat(miss.map(function(k){return all[k]})):['Tüm temel önlemler tamam. Yıllık bakım yine önerilir.'],msg:'Güvenlik listesi: %'+p+' — eksikler: '+miss.join(', ')}}""")
TOOLS['gvn.bakim'] = dict(id='sozlesme', ico='sh', title='Bakım sözleşmesi seçici', intro='İhtiyacınıza uygun bakım planını görün. Fiyatı keşif sonrası yazılı bildiririz.',
    fields=[G('ziy', 'Yıllık ziyaret', [('1', '1 ziyaret'), ('2', '2 ziyaret'), ('4', '4 ziyaret')], '2'), G('uz', 'Uzaktan izleme desteği', [('0', 'Gerek yok'), ('1', 'Olsun')]), N('cihaz', 'Kamera + sensör sayısı', 10, 1, 200, 1, '')],
    calc=r"""function(v,H){var p=(v.ziy==='4'||v.uz==='1')?'Standart':'Temel';if(v.ziy==='4'&&v.uz==='1')p='Premium';var L=['Yıllık '+v.ziy+' periyodik bakım ziyareti','Kamera lens/ayar ve kayıt kontrolü ('+v.cihaz+' cihaz)'];if(v.uz==='1')L.push('Uzaktan sistem durumu izleme ve uyarı');if(p==='Premium')L.push('Arıza halinde öncelikli müdahale');
return{tone:'ok',big:p,head:p+' bakım planı',lines:L,note:'Kapsam örnektir; yazılı sözleşme keşif sonrası hazırlanır.',msg:'Bakım sözleşmesi: '+p+' ('+v.ziy+' ziyaret, uzaktan '+(v.uz==='1'?'var':'yok')+', '+v.cihaz+' cihaz)'}}""")
TOOLS['gvn.alarm'] = dict(id='alarm', ico='bt', title='Alarm bölge planlayıcı', intro='Korunacak bölgeleri seçin; hangi sensörlerin gerektiğini görün.',
    fields=[C('c', 'Korunacak bölgeler', [('kapi', 'Giriş kapısı'), ('balkon', 'Balkon / teras kapısı'), ('salon', 'Salon / geniş oda'), ('yatak', 'Yatak odası'), ('mutfak', 'Mutfak'), ('garaj', 'Garaj / depo')])],
    calc=r"""function(v,H){var M={kapi:'Giriş kapısı: manyetik kontak + sirenli panel',balkon:'Balkon: manyetik kontak + cam kırılma dedektörü',salon:'Salon: PIR hareket dedektörü',yatak:'Yatak odası: PIR (evcil hayvan filtreli) — gece modu için ayrı bölge',mutfak:'Mutfak: duman/gaz dedektörü (hırsızlık değil yangın koruması)',garaj:'Garaj/depo: kapı kontağı + PIR'},a=v.c||[];if(!a.length)return{head:'Bölge seçin'};
return{tone:'ok',big:a.length+' bölge',head:'Sensör planı',lines:a.map(function(k){return M[k]}).concat(['Merkez panel + siren + yedek akü','Telefon bildirimi için internet bağlantısı önerilir']),msg:'Alarm planı: '+a.join(', ')}}""")

# ---- ortak: sektör -> araç anahtarları (tema başına 2-3 tanesi seçilir)
SECTOR_TOOLS = {
    'kombi': ['kombi.kod', 'kombi.teshis', 'kombi.bakim', 'kombi.kw'],
    'klima': ['klima.btu', 'klima.kod', 'klima.bakim', 'klima.montaj', 'klima.tasarruf'],
    'beyaz_esya': ['beyaz.karar', 'beyaz.belirti', 'beyaz.parca', 'beyaz.liste'],
    'elektronik': ['tv.teshis', 'tv.kod', 'tv.karar', 'tv.teslim'],
    'bilgisayar': ['pc.saglik', 'pc.veri', 'pc.upgrade', 'pc.paket'],
    'tesisat': ['tes.kacak', 'tes.damla', 'tes.acil', 'tes.sure'],
    'elektrik': ['elk.kesit', 'elk.maliyet', 'elk.sigorta', 'elk.acil'],
    'guvenlik': ['gvn.depo', 'gvn.kesif', 'gvn.risk', 'gvn.bakim', 'gvn.alarm'],
}
SECTOR_KB = {'kombi': 'kombi', 'klima': 'klima', 'elektronik': 'televizyon'}


def render(key, uid, variant='a', kbvar='KB'):
    """Aracın HTML'i (sunucuda) + calc JS'i. uid: sayfadaki benzersiz kimlik."""
    t = TOOLS[key]
    ID = f'{uid}'
    fields = ''.join(field(f).replace('{ID}', ID) for f in t['fields'])
    html_ = (f'<article class="tl tl-{variant}" id="{ID}" data-tool="{t["id"]}" data-key="{key}">'
             f'<div class="tl-f"><div class="tl-h"><span class="tl-i">ICON_{t["ico"]}</span><div><h3>{e(t["title"])}</h3><p>{e(t["intro"])}</p></div></div>'
             f'<div class="fm tl-fields">{fields}</div></div>'
             f'<div class="tl-r"><div class="rs" aria-live="polite"></div>'
             f'<form class="tl-s fm" hidden><span class="sgl">Bu sonucu ustaya iletin</span><div class="g2"><label>Adınız<input name="n" autocomplete="name" required></label><label>Telefon<input name="p" type="tel" inputmode="tel" autocomplete="tel" placeholder="05xx xxx xx xx" required></label></div>'
             f'<input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true"><button class="btn" type="submit">Sonucu gönder</button><div class="msg" role="status"></div></form></div></article>')
    js = f'OKT.reg({json.dumps(key)},{t["calc"]});'
    return html_, js, t


RUNTIME = r"""(function(){
var API='__API_URL__',OKT=window.OKT={calc:{},kb:{}};
var H={e:function(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})},
n:function(x,d){return Number(x).toLocaleString('tr-TR',{minimumFractionDigits:d||0,maximumFractionDigits:d||0})}};
OKT.reg=function(k,f){OKT.calc[k]=f};
OKT.post=function(o){if(API.indexOf('__')===0){return new Promise(function(r){setTimeout(function(){r({preview:true})},500)})}
 return fetch(API+'/public/contact',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o)}).then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok)throw new Error(typeof j.detail==='string'?j.detail:'Gönderilemedi, lütfen telefonla arayın.');return j})})};
OKT.send=function(form,summary,dev){var f=form,n=f.elements.n?f.elements.n.value:f.elements.name.value,p=f.elements.p?f.elements.p.value:f.elements.phone.value,m=f.querySelector('.msg'),b=f.querySelector('button[type=submit]');
 if(f.elements.website&&f.elements.website.value)return;m.className='msg';m.textContent='';b.disabled=true;var old=b.textContent;b.textContent='Gönderiliyor…';
 var extra=f.elements.note?f.elements.note.value:'';
 OKT.post({name:n,phone:p,type:'servis_talebi',device_type:dev||'',message:(summary||'')+(extra?'\n'+extra:''),page:location.pathname,website:''}).then(function(r){m.className='msg ok';m.textContent=r.preview?'✓ Önizleme: bu sitede form henüz firmanıza bağlı değil.':'✓ Talebiniz alındı, sizi arayacağız.';b.textContent='Gönderildi'}).catch(function(x){m.className='msg er';m.textContent=x.message;b.disabled=false;b.textContent=old})};
function val(box){var v={};box.querySelectorAll('[data-k]').forEach(function(el){var k=el.dataset.k;if(el.type==='checkbox'){v[k]=v[k]||[];if(el.checked)v[k].push(el.value)}else if(el.type==='radio'){if(el.checked)v[k]=el.value}else if(el.type==='number'||el.type==='range'){v[k]=parseFloat(el.value)||0}else v[k]=el.value});return v}
function draw(box,r){var o=box.querySelector('.rs'),s=box.querySelector('.tl-s');if(!r){o.innerHTML='';s.hidden=true;return}
 var h='<div class="rs-in t-'+(r.tone||'ok')+'">';if(r.big)h+='<div class="rs-big">'+r.big+'</div>';h+='<h4>'+(r.head||'')+'</h4>';
 if(r.lines&&r.lines.length)h+='<ul>'+r.lines.map(function(x){return'<li>'+x+'</li>'}).join('')+'</ul>';
 if(r.steps&&r.steps.length)h+='<ol>'+r.steps.map(function(x){return'<li>'+x+'</li>'}).join('')+'</ol>';
 if(r.note)h+='<p class="rs-n">'+r.note+'</p>';h+='</div>';o.innerHTML=h;s.hidden=!r.msg;box._sum=r.msg||''}
function run(box){var f=OKT.calc[box.dataset.key],r;try{r=f(val(box),H)}catch(x){r={tone:'warn',head:'Değerleri kontrol edin'}}draw(box,r)}
function init(box){var out=box.querySelectorAll('.rg output');box.querySelectorAll('input[type=range]').forEach(function(i){i.addEventListener('input',function(){var o=i.parentNode.querySelector('output');o.textContent=i.value+(o.dataset.u||'')})});
 box.querySelectorAll('.rg output').forEach(function(o){var t=o.textContent,i=o.parentNode.querySelector('input');o.dataset.u=t.slice(String(i.value).length)});
 box.addEventListener('input',function(){run(box)});box.addEventListener('change',function(){run(box)});
 box.querySelector('.tl-s').addEventListener('submit',function(ev){ev.preventDefault();OKT.send(ev.target,'['+box.querySelector('h3').textContent+'] '+box._sum,box.dataset.dev||'')});run(box)}
document.addEventListener('DOMContentLoaded',function(){document.querySelectorAll('.tl[data-key]').forEach(init)});
})();"""

TOOL_CSS = """.tl{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:0;border:1px solid var(--ln);border-radius:var(--r);overflow:hidden;background:var(--bg);color:var(--ink)}
.tl-f{padding:clamp(22px,3vw,36px)}.tl-r{padding:clamp(22px,3vw,36px);background:var(--sf);border-left:1px solid var(--ln);display:flex;flex-direction:column;gap:18px;min-width:0}
.tl-h{display:flex;gap:14px;align-items:flex-start;margin-bottom:22px}.tl-h h3{font-size:clamp(1.15rem,2vw,1.45rem);margin-bottom:6px}.tl-h p{font-size:.92rem;color:var(--mut)}
.tl-i{flex:none;width:44px;height:44px;border-radius:calc(var(--r)*.7);background:var(--ac);color:var(--on-ac);display:grid;place-items:center}
.tl .u{display:flex;align-items:center;position:relative}.tl .u input{padding-right:54px}.tl .u i{position:absolute;right:14px;font:600 .85rem/1 var(--fb);color:var(--mut);font-style:normal;pointer-events:none}
.tl .rg{display:flex;align-items:center;gap:14px}.tl .rg input{padding:0;min-height:30px;border:0;background:none;accent-color:var(--ac);box-shadow:none!important}.tl .rg output{flex:none;min-width:56px;text-align:right;font:700 1rem/1 var(--fb);color:var(--ink)}
.tl .sgw{display:grid;gap:8px}.tl .sgl{font:600 .78rem/1.2 var(--fb);letter-spacing:.03em;color:var(--mut)}
.tl .sg label,.tl .ck label{position:relative}.tl .sg{display:flex;flex-wrap:wrap;gap:8px}.tl .sg label,.tl .ck label{display:block;cursor:pointer;color:var(--ink);font-size:.9rem;letter-spacing:0;font-weight:600}
.tl .sg input,.tl .ck input{position:absolute;width:1px!important;height:1px!important;padding:0!important;border:0!important;opacity:0;pointer-events:none}.tl .sg span{display:block;padding:12px 16px;border:1.5px solid var(--ln);border-radius:calc(var(--r)*.8);background:var(--bg);transition:.15s}
.tl .sg input:checked+span{background:var(--ac);color:var(--on-ac);border-color:var(--ac)}.tl .sg input:focus-visible+span,.tl .ck input:focus-visible+span{outline:2.5px solid var(--ac);outline-offset:2px}
.tl .ck{display:grid;gap:8px}.tl .ck span{display:flex;align-items:center;gap:12px;padding:13px 15px;border:1.5px solid var(--ln);border-radius:calc(var(--r)*.8);background:var(--bg);transition:.15s}
.tl .ck span:before{content:"";flex:none;width:20px;height:20px;border-radius:6px;border:1.5px solid var(--mut);background:var(--bg) center/14px no-repeat;transition:.15s}
.tl .ck input:checked+span{border-color:var(--ac);background:color-mix(in srgb,var(--ac) 9%,var(--bg))}.tl .ck input:checked+span:before{background-color:var(--ac);border-color:var(--ac);background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12.5l4.5 4.5L19 7.5'/%3E%3C/svg%3E")}
.tl .fm.tl-fields{gap:16px}.tl-fields .g2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.rs-in{display:grid;gap:12px;padding:22px;border-radius:calc(var(--r)*.8);background:var(--bg);border:1px solid var(--ln);border-left:4px solid var(--ac);animation:rise .4s both}
.rs-in.t-warn{border-left-color:#e0a100}.rs-in.t-bad{border-left-color:#d6392b}.rs-in.t-ok{border-left-color:#1d9a5b}
.rs-big{font:800 clamp(2rem,4.5vw,3rem)/1 var(--fd);letter-spacing:-.03em;color:var(--ink)}.rs-in h4{font:700 1.05rem/1.3 var(--fd)}
.rs-in ul,.rs-in ol{display:grid;gap:9px;padding-left:20px;font-size:.93rem;color:var(--ink)}.rs-in ol{counter-reset:s;list-style:none;padding-left:0}.rs-in ol li{counter-increment:s;display:flex;gap:12px}.rs-in ol li:before{content:counter(s);flex:none;width:26px;height:26px;border-radius:50%;background:var(--ac);color:var(--on-ac);display:grid;place-items:center;font:700 .8rem/1 var(--fb)}
.rs-in li i{display:block;font-style:normal;color:var(--mut);margin-top:3px}.rs-n{font-size:.82rem;color:var(--mut);padding-top:6px;border-top:1px dashed var(--ln)}
.tl-s{padding:18px;border:1px dashed var(--mut);border-radius:calc(var(--r)*.8);background:var(--bg)}.tl-s[hidden]{display:none}.tl-s .btn{width:100%}
@media(max-width:900px){.tl{grid-template-columns:1fr}.tl-r{border-left:0;border-top:1px solid var(--ln)}}
@media(max-width:480px){.tl-fields .g2,.tl-s .g2{grid-template-columns:1fr}}
/* araç varyantları */
.tl-b{background:var(--dk);color:#fff;border-color:#ffffff22;--ink:#fff;--mut:#ffffffa6;--ln:#ffffff2a;--bg:#ffffff0c;--sf:#00000030;--hc:#fff;--fbg:#ffffff10}
.tl-b .fm input,.tl-b .fm select,.tl-b .fm textarea{color:#fff;background:#ffffff10}.tl-b select option{color:#111}.tl-b .rs-in{background:#ffffff0d}
.tl-c{grid-template-columns:1fr;border:2px solid var(--ink);box-shadow:8px 8px 0 var(--ink)}.tl-c .tl-r{border-left:0;border-top:2px dashed var(--ink)}
.tl-c .tl-fields{grid-template-columns:1fr 1fr;display:grid}.tl-c .tl-fields>*{min-width:0}.tl-c .sgw{grid-column:1/-1}
@media(max-width:700px){.tl-c .tl-fields{grid-template-columns:1fr}}
.tl-d{border:0;background:transparent;gap:clamp(18px,3vw,36px)}.tl-d .tl-f,.tl-d .tl-r{border:1px solid var(--ln);border-radius:var(--r);background:var(--bg)}.tl-d .tl-r{background:var(--sf)}
"""
