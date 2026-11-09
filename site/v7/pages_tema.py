import re,ast,json
from rich import *
HERE='/home/claude/onlinekaydet/themes/gen2.py'
src=open(HERE,encoding='utf-8').read()
def grab(name):
    i=src.index('\n'+name+' = {')+len(name)+4
    d=0
    for j in range(i,len(src)):
        if src[j]=='{': d+=1
        elif src[j]=='}':
            d-=1
            if d==0: break
    return ast.literal_eval(src[i:j+1])
L=grab('L'); LN=grab('NAMES')
TH=json.load(open('/home/claude/onlinekaydet/site/themes.json',encoding='utf-8'))
SEC={'kombi':'Kombi','klima':'Klima','beyaz_esya':'Beyaz eşya','elektronik':'Elektronik','bilgisayar':'Bilgisayar','tesisat':'Tesisat','elektrik':'Elektrik','guvenlik':'Güvenlik'}
DESC={1:'Hero, hizmet kartları ve hızlı randevu formu. İlk ziyaretçiyi hemen aramaya ya da randevuya yönlendiren, her sektöre uyan sade düzen.',
2:'Sayfa tepesinde tam genişlikte fotoğraf. Güven veren sahadan bir kare, üstünde telefon ve randevu düğmesi.',
3:'Yazı ağırlıklı, editoryal bir düzen. Firmanın hikâyesini ve işine bakışını öne çıkarır.',
4:'Marka ve model odaklı katalog görünümü. Teknik cihaz servisleri için uygun.',
5:'Acil hat odaklı düzen. Telefon numarası ve 7/24 vurgusu ilk ekranda; arıza anında aranan servisler için.',
6:'Hizmet ve fiyat listesi odaklı düzen. Ziyaretçi ne kadar ödeyeceğini baştan görür.',
7:'Önce ve sonra fotoğraflarıyla işin kalitesini gösteren düzen.',
8:'Garanti, belge ve güvence rozetleri öne çıkan düzen. Güven vermesi gereken işler için.',
9:'Hizmet verdiğiniz bölgelerin öne çıktığı, yerel aramalara uygun düzen.',
10:'Yedek parça vitrini olan düzen. Parça satışı yapan servisler için.'}
def info():
    s=open('/home/claude/onlinekaydet/site/temalar.html',encoding='utf-8').read()
    names={}
    for m in re.finditer(r'href="\.\./tema-onizleme/([^"]+)\.html"[^>]*>(.*?)</a>',s,re.S):
        b=re.search(r'<b>(.*?)</b>',m.group(2))
        names[m.group(1)]=b.group(1) if b else m.group(1)
    return names
NM=info()
SUF={'kizil':'Kızıl','kor':'Kor','cam':'Cam','buz':'Buz','poyraz':'Poyraz','okyanus':'Okyanus','kaymak':'Kaymak','pembe':'Pembe','gumus':'Gümüş','mor':'Mor','neon':'Gece','turuncu':'Turuncu','lacivert':'Lacivert','grafit':'Grafit','sari':'Sarı','su':'Su','bakir':'Bakır','volt':'Volt','kirmizi':'Kırmızı','petrol':'Petrol','zumrut':'Zümrüt','gece':'Gece','bordo':'Bordo'}
def cn(sl,lay):
    t=sl.split('-')[-1]
    return SUF.get(t) if re.match(r'\d\d-',sl) and t in SUF else LN[lay]
ITEMS=[]
for t in TH:
    sl=t['slug']
    if sl not in L: continue
    lay,font,firm=L[sl]
    ITEMS.append(dict(slug=sl,sector=t['sector'],sname=SEC[t['sector']],dark=t['dark'],acc=t['accent'],lay=lay,layname=LN[lay],firm=firm,cname=cn(sl,lay)))
def tfile(sl): return 'tema-%s.html'%sl
def temalar():
    secs=[]
    for k,v in SEC.items(): secs.append((k,v))
    filt='<div class="r7-filter" id="tf"><button class="on" data-s="">Tümü (30)</button>%s</div>'%''.join('<button data-s="%s">%s (%d)</button>'%(k,v,sum(1 for i in ITEMS if i['sector']==k)) for k,v in secs)
    cards=''.join('<a class="r7-tc" data-s="%s" href="%s"><span class="im"><img src="tema/%s-k.webp" alt="%s teması: %s ekran görüntüsü" loading="lazy" width="640" height="400"></span><span class="in2"><span><b>%s · %s</b><small>%s düzeni</small></span><span class="sw2"><i style="background:%s"></i><i style="background:%s"></i></span></span></a>'%(i['sector'],tfile(i['slug']),i['slug'],i['sname'],i['firm'],i['sname'],i['cname'],i['layname'],i['dark'],i['acc']) for i in ITEMS)
    js='<script>(function(){var f=document.getElementById("tf");if(!f)return;f.addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;f.querySelectorAll("button").forEach(function(x){x.classList.toggle("on",x===b)});var s=b.getAttribute("data-s");document.querySelectorAll(".r7-tc").forEach(function(c){c.hidden=!!s&&c.getAttribute("data-s")!==s})})})();</script>'
    body=hero([(None,'Temalar')],'Servisinize uygun <em>hazır web sitesi</em>','Sekiz sektör için hazırlanmış 30 tema. Birini seçin, firma bilgilerinizi girin; siteniz randevu formu ve müşteri portalı bağlantısıyla birlikte yayına girsin.',
      '<div class="mk"><div class="bar"><i></i><i></i><i></i><b>Sıcak Kombi · Bölge odaklı</b></div><img src="tema/07-kombi-kizil.webp" alt="Kombi teması" style="display:block;width:100%;height:auto"></div>',['Mobil uyumlu','Bölümleri panelden düzenleyin','İstediğiniz zaman tema değiştirin'],
      [('#temalar','Temaları gör',''),('index.html#kayit','Ücretsiz deneyin','o')])
    body+=strip([('30','hazır tema'),('8','sektör'),('10','farklı düzen'),('Her','tema mobil uyumlu')])
    body+=sec(head('Nasıl çalışır','Temayı seçin, gerisi panelden','')+cards_three(),)
    body+=sec(head('Tüm temalar','30 tema, 8 sektör','Ekran görüntüsüne tıklayın, temanın ayrıntı sayfasını ve canlı önizlemesini görün.')+filt+'<div class="r7-tg" id="temalar">%s</div>'%cards,last=False,id='temalar')
    body+=sec(head('Sektör bazında','Kendi sektörünüzden başlayın','')+'<div class="r7-sg">%s</div>'%''.join('<a href="%s"><b>%s</b><small>%d tema</small></a>'%(sf,v,sum(1 for i in ITEMS if i['sector']==k)) for (k,v),sf in zip(SEC.items(),['sektor-kombi.html','sektor-klima.html','sektor-beyaz-esya.html','sektor-elektronik.html','sektor-bilgisayar.html','sektor-tesisat.html','sektor-elektrik.html','sektor-guvenlik.html'])))
    body+=cta('Temanızı birlikte seçelim','Sektörünüzü söyleyin, size en uygun temaları birlikte belirleyelim. İlk ay ücretsiz.')
    page('temalar.html','Servis web sitesi temaları: 30 hazır tema','Kombi, klima, beyaz eşya, elektronik, bilgisayar, tesisat, elektrik ve güvenlik servisleri için 30 hazır web sitesi teması.',body+js)
def cards_three():
    return cards([('globe','Bir tıkla seçin','Sektörünüze uygun temayı seçin; firma adınız, telefonunuz ve logonuz yerleşir.'),('pen','Kendiniz düzenleyin','Menü, bölümler, görseller, yazılar, alt bilgi ve mobil menü panelden değişir.'),('bell','Formlar panele düşer','Randevu ve servis formundan gelen talepler doğrudan servis panelinize kaydolur.')])
def detail():
    for n,i in enumerate(ITEMS):
        prev=ITEMS[n-1]; nxt=ITEMS[(n+1)%len(ITEMS)]
        same=[x for x in ITEMS if x['sector']==i['sector'] and x['slug']!=i['slug']]
        title='%s teması · %s'%(i['sname'],i['cname'])
        vis=('<div class="r7-dev"><div class="big"><div class="bar"><i></i><i></i><i></i></div><img src="tema/%s.webp" alt="%s teması masaüstü görünümü" width="1000" height="1172"></div>'
             '<div class="mob"><img src="tema/%s-m.webp" alt="%s teması mobil görünümü" width="300" height="650"></div></div>')%(i['slug'],i['sname'],i['slug'],i['sname'])
        body=hero([('temalar.html','Temalar'),(None,'%s · %s'%(i['sname'],i['cname']))],'%s <em>%s</em>'%(i['sname'],i['cname']),
          '%s düzeni. %s'%(i['layname'],DESC[i['lay']]),'',['Örnek firma: %s'%i['firm'],'Mobil uyumlu','Panelden düzenlenir'],
          [('../tema-onizleme/%s.html'%i['slug'],'Canlı önizleme',''),('index.html#kayit','Bu temayı seçin','o')])
        body=body.replace('target','target')
        body+=sec(vis+'<div class="r7-sw"><i style="background:%s"></i><i style="background:%s"></i></div><p class="r7-note">Ekran görüntüleri örnek içeriklerle hazırlanmıştır; firma adı, telefon, logo ve fotoğraflar sizin bilgilerinizle değişir.</p>'%(i['dark'],i['acc']))
        body+=sec(head('Temayla gelenler','Siteniz yayına girdiğinde','')+cards([('cal','Randevu formu','Ziyaretçi randevu talebi bırakır; talep servis panelinize düşer.'),('phone','Mobil uyum','Telefonda alt çubuk ve menüyle rahat kullanım.'),('pen','Panelden düzenleme','Bölümleri, yazıları ve görselleri panelden değiştirirsiniz.'),('users','Müşteri portalı bağlantısı','Menüdeki bağlantı firmanızın müşteri portalını açar.'),('search','SEO ayarları','Başlık ve açıklama panelden girilir.'),('globe','Temayı değiştirin','İstediğiniz zaman başka temaya geçin; içerikler taşınır.')]))
        body+=sec(head('Diğer temalar','Aynı sektörden','')+'<div class="r7-tg">%s</div>'%''.join('<a class="r7-tc" href="%s"><span class="im"><img src="tema/%s-k.webp" alt="%s teması" loading="lazy" width="640" height="400"></span><span class="in2"><span><b>%s · %s</b><small>%s düzeni</small></span><span class="sw2"><i style="background:%s"></i><i style="background:%s"></i></span></span></a>'%(tfile(x['slug']),x['slug'],x['sname'],x['sname'],x['cname'],x['layname'],x['dark'],x['acc']) for x in same[:3]))
        body+=sec('<div class="r7-band"><div><h2>Bu temayı kullanmak ister misiniz?</h2><p>Sektörünüzü ve firma bilgilerinizi bırakın; temayı sizin için kuralım. İlk ay ücretsiz.</p></div><a class="btn" href="index.html#kayit">Ücretsiz deneyin</a></div>')
        body+=sec('<div style="display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap"><a class="r7-link" href="%s" style="margin:0">← %s · %s</a><a class="r7-link" href="temalar.html" style="margin:0">Tüm temalar</a><a class="r7-link" href="%s" style="margin:0">%s · %s →</a></div>'%(tfile(prev['slug']),prev['sname'],prev['cname'],tfile(nxt['slug']),nxt['sname'],nxt['cname']),last=True)
        page(tfile(i['slug']),title,'%s servisleri için %s düzeninde hazır web sitesi teması. Randevu formu, mobil uyum ve panelden düzenleme.'%(i['sname'],i['layname']),body)
    return len(ITEMS)
