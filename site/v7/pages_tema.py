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
MAN=json.load(open('/home/claude/onlinekaydet/themes/g3/manifest.json',encoding='utf-8'))
SEC={'kombi':'Kombi','klima':'Klima','beyaz_esya':'Beyaz eşya','elektronik':'Elektronik','bilgisayar':'Bilgisayar','tesisat':'Tesisat','elektrik':'Elektrik','guvenlik':'Güvenlik'}
HD={'shop':'Online mağaza düzeni: parça kodu, uyumlu marka-model ve stok bilgisiyle ürün listesi, sepet ve sipariş formu.','tool':'Sayfa tepesinde sektöre özel hesaplayıcı: ziyaretçi ilk ekranda sonucunu görür.','full':'Tam genişlikte fotoğrafla açılan, güven veren sade düzen.','split':'Yazı ve fotoğraf yan yana; telefon ve randevu düğmesi hemen yanında.','stats':'Hizmet ve garanti bilgilerini rakam bloklarıyla öne çıkaran düzen.','sos':'Acil hat odaklı düzen: telefon numarası ve yanıt süresi ilk ekranda.','slices':'Fotoğrafı dilimleyen, hizmetleri yan yana gösteren dinamik düzen.','edit':'Editoryal, yazı ağırlıklı düzen; firmanın işine bakışını öne çıkarır.','mosaic':'Mozaik fotoğraf ızgarası ve hizmet kartlarıyla vitrin düzeni.','arch':'Kemer biçimli fotoğraf ve sakin, premium görünüm.','ticket':'Servis fişi görünümünde randevu ve takip hissi veren düzen.','marquee':'Büyük tipografi ve kayan hizmet bandıyla cesur düzen.','search':'Arama kutusuyla açılır: ziyaretçi marka, parça ya da arızayı yazarak başlar.','console':'Koyu konsol görünümünde durum paneli ve hızlı işlemler.','diag':'Çapraz bloklu, hareketli ve güçlü kontrastlı düzen.'}
ITEMS=[]
for m in MAN:
    st='magaza' in m['slug']
    ITEMS.append(dict(slug=m['slug'],sector='magaza' if st else m['sector'],sname='Online mağaza' if st else SEC[m['sector']],dark=m['pal'][3],acc=m['pal'][4],hero=m['hero'],layname=m['style'],firm=m['nm'],
        cname=(m['style'].split(' · ')[1].capitalize() if st else m['style'].split(' · ')[0]),tools=m['tools']))
N=len(ITEMS)
BASE='https://onlinekaydet.com/tema-onizleme/'
def tfile(sl): return 'tema-%s.html'%sl
def temalar():
    secs=[]
    for k,v in SEC.items(): secs.append((k,v))
    secs.append(('magaza','Online mağaza'))
    filt='<div class="r7-filter" id="tf"><button class="on" data-s="">Tümü (%d)</button>%%s</div>'%N%''.join('<button data-s="%s">%s (%d)</button>'%(k,v,sum(1 for i in ITEMS if i['sector']==k)) for k,v in secs)
    cards=''.join('<a class="r7-tc" data-s="%s" href="%s"><span class="im"><img src="tema/%s-k.webp" alt="%s teması: %s ekran görüntüsü" loading="lazy" width="640" height="400"></span><span class="in2"><span><b>%s · %s</b><small>%s düzeni</small></span><span class="sw2"><i style="background:%s"></i><i style="background:%s"></i></span></span></a>'%(i['sector'],tfile(i['slug']),i['slug'],i['sname'],i['firm'],i['sname'],i['cname'],i['layname'],i['dark'],i['acc']) for i in ITEMS)
    js='<script>(function(){var f=document.getElementById("tf");if(!f)return;f.addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;f.querySelectorAll("button").forEach(function(x){x.classList.toggle("on",x===b)});var s=b.getAttribute("data-s");document.querySelectorAll(".r7-tc").forEach(function(c){c.hidden=!!s&&c.getAttribute("data-s")!==s})})})();</script>'
    body=hero([(None,'Temalar')],'Servisinize uygun <em>hazır web sitesi</em>','Sekiz sektör ve online mağaza için hazırlanmış %d tema. '%N+' Birini seçin, firma bilgilerinizi girin; siteniz randevu formu ve müşteri portalı bağlantısıyla birlikte yayına girsin.',
      '<div class="mk"><div class="bar"><i></i><i></i><i></i><b>Sıcak Kombi · Bölge odaklı</b></div><img src="tema/07-kombi-kizil.webp" alt="Kombi teması" style="display:block;width:100%;height:auto"></div>',['Mobil uyumlu','Bölümleri panelden düzenleyin','İstediğiniz zaman tema değiştirin'],
      [('#temalar','Temaları gör',''),('index.html#kayit','Ücretsiz deneyin','o')])
    body+=strip([(str(N),'hazır tema'),('8','sektör + mağaza'),('10','farklı düzen'),('Her','tema mobil uyumlu')])
    body+=sec(head('Nasıl çalışır','Temayı seçin, gerisi panelden','')+cards_three(),)
    body+=sec(head('Tüm temalar','%d tema, 8 sektör ve online mağaza'%N,'Ekran görüntüsüne tıklayın, temanın ayrıntı sayfasını ve canlı önizlemesini görün.')+filt+'<div class="r7-tg" id="temalar">%s</div>'%cards,last=False,id='temalar')
    body+=sec(yeni_bolum(),last=False)
    body+=sec(head('Sektör bazında','Kendi sektörünüzden başlayın','')+'<div class="r7-sg">%s</div>'%''.join('<a href="%s"><b>%s</b><small>%d tema</small></a>'%(sf,v,sum(1 for i in ITEMS if i['sector']==k)) for (k,v),sf in zip(SEC.items(),['sektor-kombi.html','sektor-klima.html','sektor-beyaz-esya.html','sektor-elektronik.html','sektor-bilgisayar.html','sektor-tesisat.html','sektor-elektrik.html','sektor-guvenlik.html'])))
    body+=cta('Temanızı birlikte seçelim','Sektörünüzü söyleyin, size en uygun temaları birlikte belirleyelim. İlk ay ücretsiz.')
    page('temalar.html','Servis web sitesi temaları: %d hazır tema'%N,'Kombi, klima, beyaz eşya, elektronik, bilgisayar, tesisat, elektrik ve güvenlik servisleri için %d hazır web sitesi teması; yedek parça satan firmalar için online mağaza temaları.'%N,body+js)

def _nyeni():
    import sys; sys.path.insert(0,'/home/claude/onlinekaydet/panel')
    import sektor
    th=json.load(open('/home/claude/onlinekaydet/site/themes.json',encoding='utf-8'))
    skip={'kombi','klima','beyaz_esya','elektronik','bilgisayar','tesisat','elektrik','guvenlik'}
    ks=sorted({t['sector'] for t in th if t['sector'] not in skip},key=lambda k:sektor.SECTORS.get(k,{}).get('name',k))
    return {k:sektor.SECTORS.get(k,{}).get('name',k) for k in ks}
NYENI=_nyeni()
def yeni_bolum():
    th=[t for t in json.load(open('/home/claude/onlinekaydet/site/themes.json',encoding='utf-8')) if t['sector'] in NYENI]
    css=('<style>.r7-yn{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:22px}.r7-yn a{display:grid;gap:8px;border:1px solid rgba(128,128,128,.3);border-radius:16px;padding:16px;min-height:44px;transition:transform .2s,box-shadow .2s}'
         '.r7-yn a:hover{transform:translateY(-3px);box-shadow:0 14px 30px -20px #0006}.r7-yn .sw{display:flex;height:46px;border-radius:10px;overflow:hidden}.r7-yn .sw i{flex:1}.r7-yn .sw i+i{flex:.4}.r7-yn small{opacity:.7}'
         '.r7-yf{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}.r7-yf button{border:1px solid rgba(128,128,128,.4);background:none;color:inherit;border-radius:99px;padding:10px 16px;min-height:44px;cursor:pointer;font:inherit}.r7-yf button.on{background:currentColor}.r7-yf button.on span{color:#fff;mix-blend-mode:difference}'
         '@media(max-width:900px){.r7-yn{grid-template-columns:repeat(2,1fr)}}@media(max-width:520px){.r7-yn{grid-template-columns:1fr}}</style>')
    chips='<label for="ysel" style="display:block;font-weight:700;margin-bottom:8px">Sektörünüzü seçin</label><select id="ysel" style="min-height:48px;padding:0 14px;border-radius:12px;border:1px solid rgba(128,128,128,.4);background:transparent;color:inherit;font:inherit;max-width:100%"><option value="">Tümü ('+str(len(th))+')</option>'+''.join('<option value="%s">%s (%d)</option>'%(k,v,sum(1 for t in th if t['sector']==k)) for k,v in NYENI.items())+'</select>'
    cards=''.join('<a href="../tema-onizleme/%s.html" target="_blank" rel="noopener" data-y="%s"><span class="sw"><i style="background:%s"></i><i style="background:%s"></i></span><b>%s</b><small>%s teması%s</small></a>'%(t['slug'],t['sector'],t['dark'],t['accent'],t['name'],NYENI[t['sector']],' · Premium' if t.get('premium') else '') for t in th)
    js=('<script>(function(){var f=document.getElementById("ysel");if(!f)return;f.addEventListener("change",function(){var s=f.value;document.querySelectorAll("#yn a").forEach(function(a){a.style.display=(!s||a.getAttribute("data-y")===s)?"":"none"})})})();</script>')
    return css+head('Tüm sektörler','Kuaför, klinik, kurs, emlak, restoran, e-ticaret ve daha fazlası','Teknik servis dışındaki işletmeler için hazırlanan %d tema. Canlı önizlemeyi yeni sekmede açın; kampanya, hikâye ve paket bölümleri her temada hazır gelir.'%len(th))+'<div class="r7-yf" id="yf">%s</div><div class="r7-yn" id="yn">%s</div>'%(chips,cards)+js
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
          '%s. %s Sektöre özel araçlar: %s.'%(i['layname'],HD[i['hero']],', '.join(i['tools'])),'',['Örnek firma: %s'%i['firm'],'Mobil uyumlu','Panelden düzenlenir'],
          [('../tema-onizleme/%s.html'%i['slug'],'Canlı önizleme',''),('#paylas','İnternet bağlantısını al','o'),('index.html#kayit','Bu temayı seçin','o')])
        body+=sec('<style>.r7-share{border:1px solid rgba(128,128,128,.35);border-radius:18px;padding:clamp(20px,3vw,32px);max-width:860px;margin:0 auto}.r7-share p{margin:8px 0 18px;opacity:.75}.r7-share .row{display:flex;gap:10px;flex-wrap:wrap}.r7-share input{flex:1 1 280px;min-height:50px;padding:0 16px;border:1px solid rgba(128,128,128,.45);border-radius:12px;font:500 15px/1 inherit;background:transparent;color:inherit;min-width:0}.r7-share .btn{min-height:50px;display:inline-flex;align-items:center;justify-content:center;padding:0 22px}</style><div id="paylas" class="r7-share"><b>Bu temayı internette inceleyin</b><p>Bu bağlantıyı herkesle paylaşabilirsiniz; tıklayan kişi temayı gerçek site gibi açar, gezer ve telefondaki görünümünü görür.</p><div class="row"><input readonly value="%s%s.html" aria-label="Tema bağlantısı" onclick="this.select()"><button type="button" class="btn" data-copy="%s%s.html">Bağlantıyı kopyala</button><a class="btn o" href="../tema-onizleme/%s.html" target="_blank" rel="noopener">Yeni sekmede aç</a></div></div>'%(BASE,i['slug'],BASE,i['slug'],i['slug']))
        body+=sec(vis+'<div class="r7-sw"><i style="background:%s"></i><i style="background:%s"></i></div><p class="r7-note">Ekran görüntüleri örnek içeriklerle hazırlanmıştır; firma adı, telefon, logo ve fotoğraflar sizin bilgilerinizle değişir.</p>'%(i['dark'],i['acc']))
        body+=sec(head('Temayla gelenler','Siteniz yayına girdiğinde','')+cards([('cal','Randevu formu','Ziyaretçi randevu talebi bırakır; talep servis panelinize düşer.'),('phone','Mobil uyum','Telefonda alt çubuk ve menüyle rahat kullanım.'),('pen','Panelden düzenleme','Bölümleri, yazıları ve görselleri panelden değiştirirsiniz.'),('users','Müşteri portalı bağlantısı','Menüdeki bağlantı firmanızın müşteri portalını açar.'),('search','SEO ayarları','Başlık ve açıklama panelden girilir.'),('globe','Temayı değiştirin','İstediğiniz zaman başka temaya geçin; içerikler taşınır.')]))
        body+=sec(head('Diğer temalar','Aynı sektörden','')+'<div class="r7-tg">%s</div>'%''.join('<a class="r7-tc" href="%s"><span class="im"><img src="tema/%s-k.webp" alt="%s teması" loading="lazy" width="640" height="400"></span><span class="in2"><span><b>%s · %s</b><small>%s düzeni</small></span><span class="sw2"><i style="background:%s"></i><i style="background:%s"></i></span></span></a>'%(tfile(x['slug']),x['slug'],x['sname'],x['sname'],x['cname'],x['layname'],x['dark'],x['acc']) for x in same[:3]))
        body+=sec('<div class="r7-band"><div><h2>Bu temayı kullanmak ister misiniz?</h2><p>Sektörünüzü ve firma bilgilerinizi bırakın; temayı sizin için kuralım. İlk ay ücretsiz.</p></div><a class="btn" href="index.html#kayit">Ücretsiz deneyin</a></div>')
        body+=sec('<div style="display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap"><a class="r7-link" href="%s" style="margin:0">← %s · %s</a><a class="r7-link" href="temalar.html" style="margin:0">Tüm temalar</a><a class="r7-link" href="%s" style="margin:0">%s · %s →</a></div>'%(tfile(prev['slug']),prev['sname'],prev['cname'],tfile(nxt['slug']),nxt['sname'],nxt['cname']),last=True)
        body+='<script>document.addEventListener("click",function(e){var b=e.target.closest("[data-copy]");if(!b)return;var u=b.getAttribute("data-copy");var ok=function(){b.textContent="Kopyalandı ✓";setTimeout(function(){b.textContent="Bağlantıyı kopyala"},2200)};if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(u).then(ok,function(){b.previousElementSibling.select()})}else{b.previousElementSibling.select();document.execCommand("copy");ok()}})</script>'
        page(tfile(i['slug']),title,'%s servisleri için %s düzeninde hazır web sitesi teması. Randevu formu, mobil uyum ve panelden düzenleme.'%(i['sname'],i['layname']),body)
    return len(ITEMS)
