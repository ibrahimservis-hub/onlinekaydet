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

def uret(page,B,SON,CTA,SEKT,DET,sektor_url,SLUG_ONCE,BASE,SITE):
    out=[]
    ad_of={k:(DET[k][1] if k in DET else a) for k,a in SEKT}
    for k,a in SEKT:
        ad=ad_of[k];tip=MAN.get(k) or (DET[k][2] if k in DET else 'servis')
        if tip not in PROG: tip='servis'
        s=k.replace('_','-');pu=PROG[tip];tipu=URL[tip]
        oz=DET[k][6] if k in DET else []
        ish=DET[k][7] if k in DET else []
        sl={'prog':'%s-%s.html'%(s,tipu),'muh':'%s-muhasebe-programi.html'%s,'web':'%s-web-sitesi.html'%s}
        diger=''.join('<a href="/%s">%s %s</a>'%(sl[x],E_(ad),n) for x,n in (('prog',pu),('muh','Muhasebe ve Kasa'),('web','Web Sitesi')))
        # benzer sektörler (aynı tip)
        ben=[(k2,a2) for k2,a2 in SEKT if k2!=k and (MAN.get(k2) or (DET[k2][2] if k2 in DET else 'servis'))==tip][:8]
        benz=''.join('<a href="/%s-%s.html">%s</a>'%(k2.replace('_','-'),URL[tip],E_(ad_of[k2])) for k2,_ in ben)
        ana='<p><a href="%s">%s ana sayfası</a> · <a href="/tum-sektorler.html">Tüm sektörler</a> · <a href="/bilgi-bankasi.html">Bilgi bankası</a></p>'%(sektor_url(k),E_(ad))
        def faq(q):
            return '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':x,'acceptedAnswer':{'@type':'Answer','text':y}} for x,y in q]},ensure_ascii=False)+'</script>'
        def kart(l): return ''.join('<div class="fk"><span class="no">%02d</span><h3>%s</h3><p>%s</p></div>'%(i+1,E_(x),E_(y)) for i,(x,y) in enumerate(l))
        def sss_html(q): return ''.join('<details class="sssd"><summary>%s</summary><p>%s</p></details>'%(E_(x),E_(y)) for x,y in q)
        tq=[(SSS[tip][0][0]%ad,SSS[tip][0][1]),SSS[tip][1]]
        # 1) program
        liste=''.join('<li>%s</li>'%E_(x) for x in KAYIT[tip])
        isl=('<p style="margin-top:18px"><b>%s için panelde hazır işlem türleri:</b> %s</p>'%(E_(ad),' · '.join(E_(x) for x in ish))) if ish else ''
        body=(B('p-'+k,'<a href="%s">%s</a>'%(sektor_url(k),E_(ad)),'%s %s'%(ad,pu),'%s için kayıtları, takvimi ve kasayı tek panelde tutun. 7 gün ücretsiz deneyin.'%ad)
         +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">%s %s ne işe yarar?</h2><p>Kayıtlar defterde, telefonda ve mesajlarda dağılınca iş takibi zorlaşır. OnlineKaydet’te %s işiniz için müşteri, iş ve ödeme bilgileri tek panelde durur. Aşağıdaki bilgileri her kayıtta tutarsınız:</p><ul>%s</ul>%s</div></div></section>'%(E_(ad),E_(pu.lower()),E_(ad.lower()),liste,isl)
         +('<section class="sec"><div class="w"><h2>Öne çıkan özellikler</h2><div class="fg">%s</div></div></section>'%kart(oz) if oz else '')
         +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>%s%s</div></div></section>'%(sss_html(tq),'')
         +'<section class="sec"><div class="w"><h2>%s için diğer sayfalar</h2><div class="slst">%s</div>%s</div></section>'%(E_(ad),diger,ana)
         +(('<section class="sec"><div class="w"><h2>Benzer iş kolları</h2><div class="slst">%s</div></div></section>'%benz) if benz else '')+CTA+SON)
        page(sl['prog'],'%s %s | OnlineKaydet'%(ad,pu),'%s için %s: kayıt, takvim, kasa ve web sitesi tek panelde. 7 gün ücretsiz deneyin.'%(ad,pu.lower()),body,ld_raw=faq(tq));out.append(sl['prog'])
        # 2) muhasebe/kasa
        mq=[('%s için gelir gider takibi nasıl yapılır?'%ad,'Kasa bölümünde her tahsilat, gider ve borç kaydedilir; gün, hafta ve ay bazlı raporlar panelde görünür.'),('Resmi muhasebe ve e-fatura yerine geçer mi?','Hayır. Panel günlük kasa ve borç takibi içindir; resmi muhasebe ve e-fatura işlemleri için mali müşavirinizle çalışmaya devam edersiniz.')]
        body=(B('m-'+k,'<a href="%s">%s</a>'%(sektor_url(k),E_(ad)),'%s Muhasebe ve Kasa Programı'%ad,'%s için gelir, gider, borç ve tahsilatı tek ekranda takip edin.'%ad)
         +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">%s için kasa ve borç takibi</h2><p>%s işinde tahsilat bir yerde, gider başka yerde kalınca günün sonunda hesap tutmaz. Kasa bölümünde şunları tutarsınız:</p><ul><li>Gelir ve tahsilat (nakit, kart, havale)</li><li>Gider kayıtları</li><li>Müşteri borcu ve kalan tutar</li><li>Gün, hafta ve ay raporları</li></ul><p>Her tahsilat, ilgili müşteri ve iş kaydına bağlanır; müşteri sayfasından geçmiş ödemeleri görürsünüz.</p></div></div></section>'%(E_(ad),E_(ad))
         +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>%s</div></div></section>'%sss_html(mq)
         +'<section class="sec"><div class="w"><h2>%s için diğer sayfalar</h2><div class="slst">%s</div>%s</div></section>'%(E_(ad),diger,ana)+CTA+SON)
        page(sl['muh'],'%s Muhasebe ve Kasa Programı | OnlineKaydet'%ad,'%s için gelir gider, borç ve tahsilat takibi. Kasa ve raporlar panelde. 7 gün ücretsiz deneyin.'%ad,body,ld_raw=faq(mq));out.append(sl['muh'])
        # 3) web sitesi
        wq=[('%s için web sitesi nasıl kurulur?'%ad,'Sektörünüze hazır temayı seçersiniz; yazı, resim ve iletişim bilgilerini panelden girersiniz. Alan adı ve kurulum desteği verilir.'),('Sitedeki yazı ve resimleri ben değiştirebilir miyim?','Evet, her bölümün yazısı ve görseli panelden değiştirilir.')]
        body=(B('w-'+k,'<a href="%s">%s</a>'%(sektor_url(k),E_(ad)),'%s Web Sitesi'%ad,'%s için hazır tema, panelden düzenleme ve form talepleri panele düşer.'%ad)
         +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">%s için hazır web sitesi</h2><p>Sıfırdan tasarım beklemeden, %s işine uygun hazır temayla yayına çıkarsınız. Sitedeki formdan gelen talepler panelinize düşer; müşteri kaydına çevirip takip edersiniz.</p></div></div></section>'%(E_(ad),E_(ad.lower()))
         +('<section class="sec"><div class="w"><h2>Sitenizde yer alacak bölümler</h2><div class="fg">%s</div></div></section>'%kart(oz) if oz else '')
         +'<section class="sec"><div class="w"><div class="yz"><h2 style="margin-top:0">Sık sorulan sorular</h2>%s</div></div></section>'%sss_html(wq)
         +'<section class="sec"><div class="w"><h2>%s için diğer sayfalar</h2><div class="slst">%s</div>%s</div></section>'%(E_(ad),diger,ana)+CTA+SON)
        page(sl['web'],'%s Web Sitesi | Hazır Tema | OnlineKaydet'%ad,'%s için hazır web sitesi teması. Yazı ve resimleri panelden değiştirin, form talepleri panele düşsün.'%ad,body,ld_raw=faq(wq));out.append(sl['web'])
    return out
