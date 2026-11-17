# -*- coding: utf-8 -*-
"""Sektör x arama niyeti sayfaları. Veri: panel/sitegen.SECTORS + panel/sektor_cok2.R. Sayı/ödül/müşteri uydurulmaz."""
import html, json, os
E_=html.escape
TIP={'servis':'servis','randevu':'randevu','kurs':'kurs','menu':'menu','ilan':'ilan','cekim':'cekim','urun':'urun'}
MAN={**{k:'servis' for k in 'kombi klima beyaz_esya bilgisayar elektrik elektronik guvenlik tesisat oto_servis oto_cekici temizlik telefon_tamir oto_yikama'.split()},
 **{k:'randevu' for k in 'kuafor guzellik psikolog diyetisyen fizyoterapi dis_klinigi veteriner spor_salonu'.split()},
 'surucu_kursu':'kurs','src_kursu':'kurs','emlakci':'ilan','avukat':'ilan','muhasebe':'ilan','nakliye':'ilan','lokanta':'menu','fotografci':'cekim','tekstil':'urun','eticaret':'urun'}
PROG={'servis':'Servis Takip Programı','randevu':'Randevu Programı','kurs':'Kayıt ve Ders Takip Programı','ilan':'Müşteri ve İş Takip Programı','menu':'Sipariş ve Rezervasyon Programı','cekim':'Rezervasyon ve Müşteri Takip Programı','urun':'Stok ve Sipariş Takip Programı'}
URL={'servis':'servis-takip-programi','randevu':'randevu-programi','kurs':'kayit-takip-programi','ilan':'musteri-takip-programi','menu':'siparis-rezervasyon-programi','cekim':'rezervasyon-programi','urun':'stok-siparis-programi'}
KAYIT={'servis':['Müşteri adı ve telefonu','Cihaz / ürün ve arıza bilgisi','Durum (bekliyor, işlemde, tamamlandı)','Kullanılan parça ve ücret','Tahsilat ve borç'],
 'randevu':['Müşteri adı ve telefonu','Randevu günü ve saati','Yapılacak işlem','Ücret ve ödeme','Önceki randevular'],
 'kurs':['Öğrenci / kursiyer bilgisi','Kayıt ve ders programı','Devam durumu','Ödeme planı ve taksit','Veli veya iletişim notu'],
 'ilan':['Müşteri / dosya bilgisi','Talep ve işlem türü','Görüşme ve not geçmişi','Hatırlatma ve takvim','Tahsilat ve borç'],
 'menu':['Masa veya sipariş bilgisi','Rezervasyon günü ve saati','Özel istek notu','Ödeme','Müşteri geçmişi'],
 'cekim':['Müşteri bilgisi','Çekim / rezervasyon tarihi','Seçilen paket','Ödeme ve kapora','Teslim notu'],
 'urun':['Ürün, SKU ve barkod','Stok adedi ve uyarı','Sipariş ve kargo durumu','Fiyat, KDV ve kâr','Müşteri kaydı']}
SSS={'servis':[('%s için servis kaydı nasıl tutulur?','Her müşteri ve cihaz tek kayıtta açılır; arıza, durum, parça ve ücret bu kayda yazılır. Geçmiş kayıtlara telefon ya da isimle ulaşırsınız.'),('Müşteriye bilgi mesajı gönderilebilir mi?','Evet, panelden müşteriye durum ve randevu mesajı gönderilir. SMS için bağlantı kurulumu gerekir.')],
 'randevu':[('%s için randevu nasıl yönetilir?','Randevular takvimde gün ve saate göre görünür; müşteri kaydıyla bağlıdır. Hatırlatma mesajı gönderebilirsiniz.'),('Müşteri web sitesinden randevu alabilir mi?','Web sitenizdeki formdan gelen talepler panele düşer; siz onaylayıp takvime işlersiniz.')],
 'kurs':[('%s için kayıt ve ders takibi nasıl yapılır?','Kursiyer kaydı, ders programı, devam ve ödeme planı tek kayıtta tutulur.'),('Taksit ve ödeme takibi var mı?','Evet, kasa bölümünde tahsilat ve borç takibi yapılır.')],
 'ilan':[('%s için müşteri takibi nasıl yapılır?','Her müşteri veya dosya tek kayıtta durur; görüşme notları, hatırlatma ve tahsilat bu kayda bağlanır.'),('Gelen talepler nereye düşer?','Web sitenizdeki form panele düşer, kayda çevirip takip edebilirsiniz.')],
 'menu':[('%s için rezervasyon ve sipariş nasıl alınır?','Formdan gelen talepler panele düşer; onay mesajı gönderir, takvime işlersiniz.'),('Özel istekler kaydedilir mi?','Evet, not alanına yazılan istekler kayıtta durur.')],
 'cekim':[('%s için rezervasyon nasıl takip edilir?','Tarih, paket ve ödeme tek kayıtta tutulur; takvimde görürsünüz.'),('Kapora takibi yapılır mı?','Kasa bölümünde tahsilat ve kalan tutar takip edilir.')],
 'urun':[('%s için stok ve sipariş nasıl takip edilir?','Ürün, stok ve sipariş panelde tek yerde durur; stok azalınca uyarı alırsınız.'),('Pazaryerine ürün gönderilebilir mi?','Panelde pazaryeri bağlantı kartları var; kullanım rehberi Bilgi Bankası’nda.')]}


import glob, sys
_P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','panel')
sys.path.insert(0,_P)
import sektor_kayit as _sk, sektor_dil as _sd, sektor as _sc
IMG=os.path.join(os.path.dirname(os.path.abspath(__file__)),'img')
SITE_URL='https://onlinekaydet.com'
SERVIS_ADIM=['Yeni iş','Teknisyen atandı','Yolda','İşlemde','Tamamlandı']
def tek(x): return x.split('/')[0]
def cog(x): return x.split('/')[-1]
def veri(k,ad,tip):
    t=_sk.template(k);r=_sd.ROWS.get(k)
    d={}
    if t:
        d.update(noun=t['noun'],plural=t['plural'],staff=t['staff_l'],steps=[x['l'] for x in t['steps']],side=[x['l'] for x in t.get('side',[])],
          fields=[f['l'] for _,fs in t['sections'] for f in fs if f['l'] not in ('Telefon',)],items=[i['l'] for i in t['items']],
          chk_t=t['check'][0],chk=[c[1] for c in t['check'][1]],comm=t.get('comm'),pay=t.get('pay'),hesap=[h[1] for h in t.get('hesap',[])])
    else:
        sc=_sc.SECTORS.get(k,{})
        d.update(noun='Servis kaydı',plural='Servis kayıtları',staff='Teknisyen',steps=SERVIS_ADIM,side=['İptal'],fields=['Müşteri','Adres','Cihaz','Arıza','Randevu','Teknisyen'],
          items=['Yedek parça','İşçilik'],chk_t='Servis kontrol listesi',chk=[c[0] for c in sc.get('checklist',[])],comm=None,pay=True,hesap=['İşçilik','Yedek parça'],
          sorunlar=list(sc.get('faults',[])))
    if r:
        d.update(kisi=tek(r['kisi']) if False else tek(r['cihaz']) if False else None)
    d['kisi_l']=(tek(r['cihaz']) if r and tip in('randevu','ilan','kurs') and r['cihaz'] and 'Müşteri' not in r['cihaz'] and k in('dis_klinigi','psikolog','diyetisyen','fizyoterapi','veteriner','aile_danisman','avukat','estetik_merkezi','spor_salonu','surucu_kursu','src_kursu') else 'Müşteri')
    d['gun']=r['gun'] if r else 'Günün işleri'
    d['yer']=r['yer'] if r else 'İş takibi'
    d['stok']=r['stok'] if r else 'Stok'
    d['teklif']=r['teklif'] if r else 'Teklifler'
    d['is']=cog(r['is']) if r else d['plural']
    d['is1']=tek(r['is']) if r else d['noun']
    d['staff_p']=tek(r['kisi']) if r else d['staff']
    return d
def gorsel(k):
    s=k.replace('_','-');d=sorted(glob.glob(IMG+'/tema-*-%s-d.webp'%s));m=sorted(glob.glob(IMG+'/tema-*-%s-m.webp'%s))
    return [os.path.basename(x)[:-5] for x in d[:1]],[os.path.basename(x)[:-5] for x in m[:1]]
def li(l): return ''.join('<li>%s</li>'%E_(x) for x in l)
def satir(no,et,h,p,mad,img,alt,ters=False,neden=None):
    return ('<section class="sec sxrow"><div class="w"><div class="sxr%s"><div class="sxt"><span class="sxn">%02d</span><p class="et">%s</p><h2>%s</h2><p>%s</p>%s</div>'
      '<figure class="sxf"><img src="%s" alt="%s" loading="lazy"><figcaption>%s</figcaption></figure></div></div></section>')%(' ters' if ters else '',no,E_(et),E_(h),E_(p),'<ul class="sxl">%s</ul>'%li(mad) if mad else '',img,E_(alt),E_(alt))
def adim(steps,side):
    s=''.join('<li><b>%d</b><span>%s</span></li>'%(i+1,E_(x)) for i,x in enumerate(steps))
    y=('<p class="sxy">Yan durumlar: %s</p>'%E_(' · '.join(side))) if side else ''
    return '<ol class="sxs">%s</ol>%s'%(s,y)
def seridi(l):
    return '<div class="sxst">%s</div>'%''.join('<div><b>%s</b><span>%s</span></div>'%(E_(a),E_(b)) for a,b in l)
def sss_html(q): return ''.join('<details class="sssd"><summary>%s</summary><p>%s</p></details>'%(E_(x),E_(y)) for x,y in q)
def faq(q): return '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':x,'acceptedAnswer':{'@type':'Answer','text':y}} for x,y in q]},ensure_ascii=False)+'</script>'
def demo(v,ad):
    st=''.join('<li><button type="button" data-i="%d"%s>%s</button></li>'%(i,' class="on"' if i==0 else '',E_(x)) for i,x in enumerate(v['steps']))
    fl=''.join('<label><span>%s</span><input type="text" disabled placeholder="—"></label>'%E_(x) for x in v['fields'][:8])
    ck=''.join('<label class="sxck"><input type="checkbox"><span>%s</span></label>'%E_(x) for x in v['chk'])
    return ('<div class="sxdemo" data-n="%d"><div class="sxd-h"><b>%s formu</b><span>Durum: <em class="sxd-d">%s</em></span></div><div class="sxd-bar"><i></i></div>'
      '<ol class="sxd-st">%s</ol><div class="sxd-g">%s</div><div class="sxd-c"><b>%s</b><div>%s</div><small class="sxd-s">0 / %d tamam</small></div>'
      '<div class="sxd-f"><button type="button" class="btn bos2" data-a="p">Geri</button><button type="button" class="btn dolu" data-a="n">Sonraki adım</button></div>'
      '<small class="sxd-n">Önizleme: alanlar panelle aynıdır, bilgileri gerçek panelde siz girersiniz.</small></div>')%(len(v['steps']),E_(v['noun']),E_(v['steps'][0]),st,fl,E_(v['chk_t']),ck,len(v['chk']))
def kars(ad,nl):
    R=[('Kayıt','Defter, Excel ve mesajlara dağılır','Her %s tek kayıtta'%nl),('Müşteri geçmişi','Aramak zaman alır','İsim ya da telefonla anında'),('Evrak takibi','Akılda ya da kağıtta','Her kayıtta işaretli liste'),('Hatırlatma','Elle aranır','Panelden mesaj gönderilir'),('Ödeme ve borç','Ayrı defterde','Kayda bağlı, kasada toplanır'),('Ekip','Telefonla yönlendirilir','İş kişiye atanır, görünür')]
    return '<div class="sxtb"><table><thead><tr><th></th><th>Defter / Excel / mesajlar</th><th>OnlineKaydet</th></tr></thead><tbody>%s</tbody></table></div>'%''.join('<tr><th>%s</th><td>%s</td><td>%s</td></tr>'%(E_(a),E_(x),E_(y)) for a,x,y in R)
def bc(ad,ana,ad2,slug,SITE_):
    return '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Ana sayfa','item':SITE_+'/'},{'@type':'ListItem','position':2,'name':ad,'item':SITE_+ana},{'@type':'ListItem','position':3,'name':ad2,'item':SITE_+'/'+slug}]},ensure_ascii=False)+'</script>'
def sw(ad2,desc,slug,SITE_):
    return '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@type':'SoftwareApplication','name':'OnlineKaydet — '+ad2,'applicationCategory':'BusinessApplication','operatingSystem':'Web','description':desc,'url':SITE_+'/'+slug,'inLanguage':'tr','offers':{'@type':'Offer','price':'0','priceCurrency':'TRY','description':'7 gün ücretsiz deneme'}},ensure_ascii=False)+'</script>'
def bolum(cls,h,ic): return '<section class="sec %s"><div class="w"><h2>%s</h2>%s</div></section>'%(cls,E_(h),ic)

def uret(page,B,SON,CTA,SEKT,DET,sektor_url,SLUG_ONCE,BASE,SITE):
    out=[]
    ad_of={k:(DET[k][1] if k in DET else a) for k,a in SEKT}
    for k,a in SEKT:
        ad=ad_of[k];tip=MAN.get(k) or (DET[k][2] if k in DET else 'servis')
        if tip not in PROG: tip='servis'
        s=k.replace('_','-');pu=PROG[tip];tipu=URL[tip]
        v=veri(k,ad,tip);oz=DET[k][6] if k in DET else [];ish=DET[k][7] if k in DET else []
        dsk,mob=gorsel(k)
        sl={'prog':'%s-%s.html'%(s,tipu),'muh':'%s-muhasebe-programi.html'%s,'web':'%s-web-sitesi.html'%s}
        diger=''.join('<a href="/%s">%s %s</a>'%(sl[x],E_(ad),n) for x,n in (('prog',pu),('muh','Muhasebe ve Kasa'),('web','Web Sitesi')))
        ben=[(k2,a2) for k2,a2 in SEKT if k2!=k and (MAN.get(k2) or (DET[k2][2] if k2 in DET else 'servis'))==tip][:8]
        benz=''.join('<a href="/%s-%s.html">%s</a>'%(k2.replace('_','-'),URL[tip],E_(ad_of[k2])) for k2,_ in ben)
        ana='<p class="sxln"><a href="%s">%s ana sayfası</a> · <a href="/tum-sektorler.html">Tüm sektörler</a> · <a href="/bilgi-bankasi.html">Bilgi bankası</a></p>'%(sektor_url(k),E_(ad))
        son=bolum('','%s için diğer sayfalar'%ad,'<div class="slst">%s</div>%s'%(diger,ana))+(bolum('','Benzer iş kolları','<div class="slst">%s</div>'%benz) if benz else '')+CTA+SON
        noun=v['noun'];nl=noun.lower();pl=v['plural'].lower();staff=v['staff'].lower()
        stats=[(str(len(v['steps'])),'adımda %s ilerler'%nl),(str(len(v['fields'])),'kayıt alanı'),(str(len(v['chk'])),'%s maddesi'%v['chk_t'].lower() if len(v['chk_t'])<22 else 'kontrol maddesi'),(str(len(set(v['items']+v['hesap']))),'hesap kalemi')]
        # ---------- 1) PROGRAM
        rows=''
        rows+=satir(1,'Müşteri kaydı','%s kartı ve geçmişi'%v['kisi_l'],'Her %s tek kartta durur; aynı kişinin tüm %s birlikte görünür.'%(v['kisi_l'].lower(),pl),
          ['Telefon, iletişim ve notlar','Geçmiş %s ve ödemeler'%pl,'Aradığınızı isim ya da telefonla bulursunuz'],'/v9/img/bilgi/m_liste.webp','%s müşteri listesi ekranı'%ad)
        rows+=satir(2,'Randevu ve takvim',v['gun']+' takvimde','Gün ve saat takvimde görünür; %s ve %s ayrı takip edilir.'%(staff,v['yer'].lower()),
          ['Günlük ve haftalık takvim','Müşteriye hatırlatma mesajı','%s: %s'%('Yan durumlar',' · '.join(v['side'])) if v['side'] else 'Ertelenen işler takvimde güncellenir'],'/v9/img/panel-k-takvim.webp','%s için randevu takvimi')
        rows=rows.replace('%s için randevu takvimi','%s randevu takvimi'%ad)
        rows+=satir(3,'Evrak ve belge takibi',v['chk_t']+' her kayıtta','Her %s için gerekli evrak ve kontroller işaretlenir; eksik olan görünür kalır.'%nl,v['chk'][:6],'/v9/img/panel-d-siparis.webp','%s kayıt listesi ekranı'%ad,True)
        rows+=satir(4,'Kasa ve muhasebe','Tahsilat, gider ve borç','Ödemeler ilgili kayda bağlanır; günün sonunda kasa kendiliğinden tutar.',
          (['Hesap kalemleri: '+', '.join(v['hesap'])] if v['hesap'] else [])+['Gider kayıtları ve müşteri borcu','Gün, hafta ve ay raporları']+(['Kayıt, ödeme alındıktan sonra kapatılır'] if v['pay'] else []),'/v9/img/panel-k-kasa.webp','%s kasa ve tahsilat ekranı'%ad)
        rows+=satir(5,'Personel ve prim',v['staff_p']+' ve ekip','Ekibinizi ekler, işleri kişiye atar, kimin ne yaptığını görürsünüz.',
          ['Ekip üyesi ekleme ve yetki','%s bazında iş dağılımı'%v['staff'],'Prim ve hakediş takibi' if v['comm'] else 'Kişi bazlı iş ve performans görünümü'],'/v9/img/panel-d-ekip.webp','%s ekip ve personel ekranı'%ad,True)
        rows+=satir(6,'Ürün ve e-ticaret','Ürün satışı ve sipariş','İsterseniz ürün de satarsınız: stok, sipariş ve kargo aynı panelde.',
          ['%s takibi'%v['stok'],'Sipariş ve kargo durumları','Pazaryeri bağlantı kartları (Trendyol, Hepsiburada ve diğerleri)'],'/v9/img/panel-d-urun.webp','%s ürün ve stok ekranı'%ad)
        rows+=satir(7,'Raporlar','Tek ekranda sonuçlar','Ne kadar iş yaptığınızı, ne kadar kazandığınızı ve neyin beklediğini raporlardan görürsünüz.',
          ['Gelir ve gider özeti','Tamamlanan ve bekleyen işler','Ekip bazında özet'],'/v9/img/panel-d-rapor.webp','%s rapor ekranı'%ad,True)
        pq=[('%s için %s nasıl takip edilir?'%(ad,v['is1'].lower()),'Her kayıt şu adımlardan geçer: %s. Hangi adımda olduğu listede görünür.'%', '.join(v['steps'])),
            ('Evrak ve belge takibi var mı?','Evet. Her kayıtta "%s" listesi bulunur: %s.'%(v['chk_t'],'; '.join(v['chk'][:4]))),
            ('Müşteriye bilgi mesajı gönderilebilir mi?','Evet, panelden randevu ve durum mesajı gönderilir. SMS için bağlantı kurulumu gerekir.'),
            ('Çalışanlarımı ekleyebilir miyim?','Evet. Ekip bölümünden %s ekler, işleri onlara atarsınız.'%staff),
            ('Ödeme ve borç takibi nasıl yapılır?','Kasa bölümünde her tahsilat ilgili kayda bağlanır; kalan tutar ve borç ayrı görünür.'),
            ('Denemek ücretli mi?','Hayır, demo hesabı 7 gün ücretsiz kullanılır.')]
        body=(B('p-'+k,'<a href="%s">%s</a>'%(sektor_url(k),E_(ad)),'%s %s'%(ad,pu),'%s için kayıt, evrak, randevu, kasa, ekip ve web sitesi tek panelde. 7 gün ücretsiz deneyin.'%ad)
          +'<section class="sec"><div class="w">'+seridi(stats)+'</div></section>'
          +bolum('sxfl','Bir %s böyle ilerler'%nl,adim(v['steps'],v['side']))
          +bolum('sxdm','%s formunu deneyin'%v['noun'],demo(v,ad))
          +'<section class="sec"><div class="w"><div class="sxcols"><div class="sxcard"><h3>Kayıtta tuttuğunuz bilgiler</h3><ul class="sxl">%s</ul></div><div class="sxcard"><h3>%s</h3><ul class="sxl">%s</ul></div><div class="sxcard"><h3>Kayda eklenen kalemler</h3><ul class="sxl">%s</ul></div></div></div></section>'%(li(v['fields']),E_(v['chk_t']),li(v['chk']),li(list(dict.fromkeys(v['items']+v['hesap']))))
          +(bolum('','Sık görülen işler',('<div class="sxchips">%s</div>'%''.join('<span>%s</span>'%E_(x) for x in (v.get('sorunlar') or ish)))) if (v.get('sorunlar') or ish) else '')
          +rows
          +bolum('','%s: defter mi, panel mi?'%ad,kars(ad,nl))
          +(bolum('','Hazır web sitesi teması','<div class="sxtema"><figure><img src="/v9/img/%s.webp" alt="%s web sitesi teması masaüstü görünümü" loading="lazy"></figure>%s</div><p><a class="btn bos2" href="/%s">%s web sitesi sayfası</a></p>'%(dsk[0],E_(ad),('<figure class="m"><img src="/v9/img/%s.webp" alt="%s web sitesi teması mobil görünümü" loading="lazy"></figure>'%(mob[0],E_(ad))) if mob else '',sl['web'],E_(ad))) if dsk else '')
          +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>%s</div></div></section>'%sss_html(pq)+son)
        page(sl['prog'],'%s %s | OnlineKaydet'%(ad,pu),'%s için %s: %s adımlı kayıt, evrak takibi, randevu, kasa, ekip ve web sitesi. 7 gün ücretsiz.'%(ad,pu.lower(),len(v['steps'])),body,ld_raw=faq(pq)+bc(ad,sektor_url(k),pu,sl['prog'],SITE_URL)+sw(ad+' '+pu,'%s için %s'%(ad,pu.lower()),sl['prog'],SITE_URL),extra_js='<script src="/v9/sx.js" defer></script>');out.append(sl['prog'])
        # ---------- 2) MUHASEBE / KASA
        r2=satir(1,'Kasa','Her tahsilat kayda bağlı','Ödeme alındığında ilgili %s açılır, tutar ve ödeme şekli girilir; kasa kendiliğinden güncellenir.'%nl,
          ['Nakit, kart ve havale girişi','Kalan tutar ve borç görünür']+(['Kayıt, ödeme alındıktan sonra kapatılır'] if v['pay'] else []),'/v9/img/panel-k-kasa.webp','%s kasa ekranı'%ad)
        r2+=satir(2,'Gelir ve gider','Giderleri de girin','Kira, malzeme, maaş gibi giderleri kaydedin; kâr ve zarar tek yerde görünsün.',
          ['Gider kalemleri ve tarihleri','Gün, hafta ve ay özeti','Kasa girdi ekranı'],'/v9/img/bilgi/k_girdi.webp','%s gelir gider girişi'%ad,True)
        r2+=satir(3,'Hesap kalemleri','%s hesabı nasıl oluşur'%ad,'Her kaydın tutarı şu kalemlerden oluşur: %s.'%(', '.join(v['hesap'] or v['items'])),
          v['hesap'] or v['items'],'/v9/img/panel-d-siparis.webp','%s kayıt hesabı')
        r2=r2.replace('%s kayıt hesabı','%s kayıt hesabı'%ad)
        r2+=satir(4,'Personel ve prim','Ekip hakedişi',('%s için prim ve hakediş takibi yapılır.'%v['staff_p']) if v['comm'] else 'Kim hangi işi yaptı, ekip bazında görünür.',
          ['Kişi bazlı iş listesi','Tamamlanan işler','Prim ve hakediş takibi' if v['comm'] else 'Görev dağılımı'],'/v9/img/panel-d-ekip.webp','%s personel ekranı'%ad,True)
        r2+=satir(5,'Raporlar','Sonuç tek ekranda','Gelir, gider, borç ve bekleyen işleri raporlardan izlersiniz.',['Gelir gider özeti','Müşteri borçları','Dönemsel karşılaştırma'],'/v9/img/panel-d-rapor.webp','%s rapor ekranı'%ad)
        mq=[('%s için gelir gider takibi nasıl yapılır?'%ad,'Kasa bölümünde her tahsilat, gider ve borç kaydedilir; gün, hafta ve ay bazlı raporlar panelde görünür.'),
            ('Resmi muhasebe ve e-fatura yerine geçer mi?','Hayır. Panel günlük kasa ve borç takibi içindir; resmi muhasebe ve e-fatura işlemleri için mali müşavirinizle çalışmaya devam edersiniz.'),
            ('Müşteri borcunu nasıl izlerim?','Her kaydın ödenen ve kalan tutarı görünür; borçlu müşteriler listelenir.'),
            ('Personel primi hesaplanır mı?','Ekip bölümünde prim ve hakediş takibi yapılır.' if v['comm'] else 'Ekip bölümünde kimin hangi işi yaptığını görürsünüz.'),
            ('Deneme var mı?','Demo hesabı 7 gün ücretsiz kullanılır.')]
        body=(B('m-'+k,'<a href="%s">%s</a>'%(sektor_url(k),E_(ad)),'%s Muhasebe ve Kasa Programı'%ad,'%s için gelir, gider, borç, tahsilat ve ekip hakedişi tek ekranda.'%ad)
          +'<section class="sec"><div class="w">'+seridi([(str(len(v['hesap'] or v['items'])),'hesap kalemi'),('3','ödeme şekli'),('1','kasa, tüm kayıtlar'),(str(len(v['steps'])),'adım, ödeme dahil')])+'</div></section>'
          +bolum('sxfl','Ödeme %s içinde nerede?'%nl,adim(v['steps'],v['side']))+r2
          +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>%s</div></div></section>'%sss_html(mq)+son)
        page(sl['muh'],'%s Muhasebe ve Kasa Programı | OnlineKaydet'%ad,'%s için gelir gider, borç, tahsilat ve ekip hakedişi takibi. Kasa ve raporlar panelde. 7 gün ücretsiz.'%ad,body,ld_raw=faq(mq)+bc(ad,sektor_url(k),'Muhasebe ve Kasa',sl['muh'],SITE_URL)+sw(ad+' Muhasebe ve Kasa Programı','%s için kasa ve borç takibi'%ad,sl['muh'],SITE_URL));out.append(sl['muh'])
        # ---------- 3) WEB
        r3=satir(1,'Hazır tema','%s için hazır tasarım'%ad,'Sektörünüze uygun tema seçilir; hizmetler, iletişim ve harita bölümleri hazır gelir.',['Masaüstü ve telefonda düzgün görünür','Hizmet, SSS ve iletişim bölümleri','Her bölüm düzenlenebilir'],'/v9/img/panel-d-site.webp','%s site düzenleme ekranı'%ad)
        r3+=satir(2,'Panelden düzenleme','Yazı ve resimler sizin','Yazıyı, görseli ve iletişim bilgisini panelden değiştirirsiniz; yayın anında güncellenir.',['Metin ve font değişikliği','Resim yükleme ve değiştirme','Bölüm ekleme ve kaldırma'],'/v9/img/bilgi/w_site.webp','%s site yönetim ekranı'%ad,True)
        r3+=satir(3,'Form ve talepler','Gelen talep panele düşer','Sitedeki formdan gelen müşteri bilgisi panele düşer; %s olarak kayda çevirir, takvime işlersiniz.'%nl,[ 'Form talepleri panelde listelenir','Müşteri kartına çevirme','Randevu ve takvime işleme'],'/v9/img/bilgi/m_liste.webp','%s müşteri talepleri'%ad)
        r3+=satir(4,'Ürün satışı','İsterseniz online satış','Ürünlerinizi sitede satar, siparişleri panelden yönetirsiniz.',['Ürün ve stok yönetimi','Sipariş ve kargo takibi','Pazaryeri bağlantı kartları'],'/v9/img/panel-d-urun.webp','%s ürün ekranı'%ad,True)
        wq=[('%s için web sitesi nasıl kurulur?'%ad,'Sektörünüze hazır temayı seçersiniz; yazı, resim ve iletişim bilgilerini panelden girersiniz. Alan adı ve kurulum desteği verilir.'),
            ('Sitedeki yazı ve resimleri ben değiştirebilir miyim?','Evet, her bölümün yazısı ve görseli panelden değiştirilir.'),
            ('Sitedeki formdan gelen talepler nereye düşer?','Panele düşer; müşteri kaydına çevirip takip edersiniz.'),
            ('Online ürün satabilir miyim?','Evet, ürün, stok ve sipariş yönetimi panelde var.'),
            ('Deneme var mı?','Demo hesabı 7 gün ücretsiz kullanılır.')]
        body=(B('w-'+k,'<a href="%s">%s</a>'%(sektor_url(k),E_(ad)),'%s Web Sitesi'%ad,'%s için hazır tema, panelden düzenleme ve form talepleri panele düşer.'%ad)
          +(bolum('','%s teması önizleme'%ad,'<div class="sxtema"><figure><img src="/v9/img/%s.webp" alt="%s web sitesi teması masaüstü görünümü" loading="lazy"></figure>%s</div>'%(dsk[0],E_(ad),('<figure class="m"><img src="/v9/img/%s.webp" alt="%s web sitesi teması mobil görünümü" loading="lazy"></figure>'%(mob[0],E_(ad))) if mob else '')) if dsk else '')
          +r3
          +(bolum('','Sitenizde yer alacak bölümler','<div class="fg">%s</div>'%''.join('<div class="fk"><span class="no">%02d</span><h3>%s</h3><p>%s</p></div>'%(i+1,E_(x),E_(y)) for i,(x,y) in enumerate(oz))) if oz else '')
          +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>%s</div></div></section>'%sss_html(wq)+son)
        page(sl['web'],'%s Web Sitesi | Hazır Tema | OnlineKaydet'%ad,'%s için hazır web sitesi teması. Yazı ve resimleri panelden değiştirin, form talepleri panele düşsün.'%ad,body,ld_raw=faq(wq)+bc(ad,sektor_url(k),'Web Sitesi',sl['web'],SITE_URL)+sw(ad+' Web Sitesi','%s için hazır web sitesi'%ad,sl['web'],SITE_URL));out.append(sl['web'])
    # ---------- ulusal niyet sayfaları
    ACIK={'servis':'Teknik servis, oto servis, temizlik ve benzeri saha işleri için','randevu':'Randevu ile çalışan salon, klinik ve danışmanlık işleri için','kurs':'Kurs ve eğitim işletmeleri için','ilan':'Dosya, müşteri ve iş takibi gereken hizmet işleri için','menu':'Sipariş ve rezervasyon alan işletmeler için','cekim':'Çekim ve rezervasyon alan işletmeler için','urun':'Ürün satan işletmeler için'}
    for tp in PROG:
        ks=[(k,ad_of[k]) for k,_ in SEKT if (MAN.get(k) or (DET[k][2] if k in DET else 'servis'))==tp]
        if not ks: continue
        slug=URL[tp]+'.html'
        ref=[v for v in (veri(ks[0][0],ks[0][1],tp),)][0]
        lst=''.join('<a href="/%s-%s.html">%s</a>'%(k.replace('_','-'),URL[tp],E_(a)) for k,a in ks)
        hq=[('%s nedir?'%PROG[tp],'İşinize ait müşteri, iş, evrak ve ödeme bilgilerini tek panelde tutan programdır. OnlineKaydet’te aynı panelde randevu, kasa, ekip ve web sitesi de vardır.'),
            ('Hangi iş kolları için hazır?','%d iş kolu için hazır: %s.'%(len(ks),', '.join(a for _,a in ks[:10])+(' ve diğerleri' if len(ks)>10 else ''))),
            ('Denemek ücretli mi?','Hayır, demo hesabı 7 gün ücretsiz kullanılır.')]
        body=(B('h-'+tp,'<a href="/tum-sektorler.html">Sektörler</a>',PROG[tp],'%s. İş koluna göre hazır kayıt adımları, evrak listesi, kasa ve web sitesi.'%ACIK[tp])
          +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">%s ne işe yarar?</h2><p>%s tek panelde şunları tutarsınız: müşteri kartı ve geçmişi, işin adımları, evrak ve kontrol listesi, tahsilat ve borç, ekip ve prim, ürün satışı ve hazır web siteniz.</p><ul class="sxl">%s</ul></div></div></section>'%(E_(PROG[tp]),ACIK[tp],li(['Örnek adımlar: '+', '.join(ref['steps']),'Örnek evrak listesi: '+', '.join(ref['chk'][:3]),'Kasa, rapor ve ekip aynı panelde']))
          +bolum('','%s: iş kolunuzu seçin'%PROG[tp],'<div class="slst">%s</div>'%lst)
          +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>%s</div></div></section>'%sss_html(hq)+CTA+SON)
        page(slug,'%s | İş Koluna Hazır Panel | OnlineKaydet'%PROG[tp],'%s. %d iş kolu için hazır kayıt adımları, evrak takibi, kasa ve web sitesi. 7 gün ücretsiz.'%(ACIK[tp],len(ks)),body,ld_raw=faq(hq));out.append(slug)
    return out
