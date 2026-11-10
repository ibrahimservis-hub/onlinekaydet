# -*- coding: utf-8 -*-
"""8 yeni sektör sayfası: sektor-kombi.html iskeleti + panel/sektor_ek.py verisi. Sayı/ödül/müşteri sayısı yazılmaz."""
import re,sys,html
sys.path.insert(0,'../../panel')
import sektor_ek as S
E=html.escape
T=open('sektor-kombi.html',encoding='utf-8').read()
a=T.index('<main id="icerik">')+len('<main id="icerik">'); b=T.index('</main>')
HEAD,TAIL=T[:a],T[b:]
ICON='<symbol id="i-isl" viewBox="0 0 120 120"><g stroke="#14161a" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"><path d="M14 44l8-28h76l8 28z" fill="#e9e4d8"/><path d="M14 44q0 12 11 12t11-12q0 12 12 12t12-12q0 12 12 12t12-12q0 12 11 12t11-12" fill="#fff"/><rect x="20" y="58" width="80" height="46" rx="3" fill="#fff"/><rect x="48" y="74" width="24" height="30" fill="#14161a"/></g></symbol>'
HEAD=HEAD.replace('<symbol id="i-kombi"',ICON+'<symbol id="i-kombi"',1)
PAGES=[('oto_servis','oto-servis','Oto servis','Oto servis için iş emri ve araç takip programı','Araç kabul, iş emri, parça ve bakım hatırlatma tek ekranda. Müşteri aracının durumunu telefonundan görür.','Araç teslim alırken fotoğraf, kilometre ve yakıt kaydı|İş emrinde yapılan işlemler ve parçalar|Bakım zamanı gelen müşteriye SMS','Plaka','34 ABC 123 · örnek','Periyodik bakım'),
('oto_cekici','oto-cekici','Oto çekici','Oto çekici ve yol yardım için çağrı takip programı','Çağrıyı kaydedin, en yakın sürücüye atayın, müşteri varış durumunu takip linkinden izlesin.','Konum ve varış adresi kaydı|Yüklemeden önce hasar fotoğrafı|Teslimde müşteri imzası','Araç','Otomobil · örnek','Araç çalışmıyor'),
('kuafor','kuafor','Kuaför ve berber','Kuaför ve berber için randevu defteri ve müşteri kartı','Randevular uzmana göre görünür, müşterinin geçmiş hizmetleri ve notları kartında durur.','Uzman bazlı randevu takvimi|Müşteri kartı ve hizmet geçmişi|Randevu hatırlatma SMS','Hizmet','Saç kesimi · örnek','Randevu'),
('nakliye','nakliye','Nakliye','Nakliye firmaları için keşif ve sevkiyat takip programı','Keşif, eşya listesi, ekip ve araç atamasını bir kayıtta toplayın; müşteri günü ve saati görür.','Keşifte eşya listesi ve fotoğraf|Ekip ve araç atama|Teslimde imzalı form','Adres','Kadıköy → Çankaya · örnek','Ev taşıma'),
('tekstil','tekstil','Tekstil','Tekstil ve konfeksiyon için sipariş ve üretim takip programı','Toptan siparişi, numuneyi ve üretim aşamasını kayıt altında tutun; ödeme ve sevkiyat bir arada.','Sipariş ve numune kaydı|Üretim aşaması takibi|Cari ve tahsilat görünümü','Sipariş','Toptan sipariş · örnek','Numune'),
('eticaret','e-ticaret','E-ticaret','E-ticaret mağazaları için sipariş, kargo ve iade takibi','Siparişler, kargo durumu, iade talepleri ve stok tek panelde; mağaza siteniz hazır temayla açılır.','Sipariş ve kargo durumu|İade ve değişim talepleri|Hazır mağaza teması','Sipariş','Sipariş · örnek','Kargo'),
('temizlik','temizlik','Temizlik','Temizlik firmaları için iş planı ve ekip takip programı','Alan, ekip ve saat bilgisi kayıtta; iş bitince önce/sonra fotoğraflarıyla müşteri onayı alınır.','Alan ve ekip planı|Önce / sonra fotoğraf|Müşteri onayı ve tahsilat','Alan','Daire · örnek','Ev temizliği'),
('guzellik','guzellik','Güzellik merkezi','Güzellik merkezleri için seans ve paket takip programı','Seans paketleri, randevular ve müşteri kartı tek yerde. Kalan seans müşteriye hatırlatılır.','Paket ve seans takibi|Müşteri kartı ve notlar|Randevu hatırlatma SMS','Paket','Seans paketi · örnek','Seans')]
ALLSEC=[('kombi','Kombi'),('klima','Klima'),('beyaz-esya','Beyaz eşya'),('elektronik','Elektronik'),('bilgisayar','Bilgisayar'),('tesisat','Tesisat'),('elektrik','Elektrik'),('guvenlik','Güvenlik')]+[(p[1],p[2]) for p in PAGES]
OPTS='<option>Seçiniz</option>'+''.join('<option>%s</option>'%E(n) for _,n in ALLSEC)+'<option>Diğer</option>'
def chips(xs): return '<div class="chp">'+''.join('<span>%s</span>'%E(x) for x in xs)+'</div>'
for key,slug,short,h1,lead,ticks,lab,val,fault in PAGES:
    d=S.NEW[key]; sv=d['site']['services']; fq=d['site']['faq']
    brands=[b for b in d['brands']]
    tm=d['terms']; terms=[(k,v) for k,v in tm.items() if k!=v][:6]
    title=h1[0].upper()+h1[1:]
    m='<div class="pgh sk"><div class="w"><div><nav class="crumb" aria-label="Sayfa yolu"><a href="index.html">Ana sayfa</a> / %s</nav><h1>%s</h1><p>%s</p><ul class="ticks">%s</ul><div class="ctas"><a class="pill" href="#kayit">Ücretsiz Dene</a><a class="pill gh" href="demo.html">Demoyu gör</a></div></div><div class="skv"><svg class="skic" aria-hidden="true"><use href="#i-isl"/></svg><div class="fis"><div class="top"><span>%s</span><span>%s</span></div><dl><dt>%s</dt><dd>%s</dd><dt>Konu</dt><dd>%s</dd></dl><div class="ln"><time>1</time><span>Kayıt açıldı</span></div><div class="ln"><time>2</time><span>Ekip atandı, müşteriye SMS gitti</span></div><div class="ln"><time>3</time><span>İşlem tamamlandı, imza alındı</span></div></div></div></div></div>'%(E(short),E(h1),E(lead),''.join('<li>%s</li>'%E(t) for t in ticks.split('|')),E(d['pdf_title'].title()),E(short)+' · örnek',E(lab),E(val),E(fault))
    m+='<section class="bnd pb"><div class="w"><div class="sh one"><h2>%s işletmesi için hazır gelenler</h2></div><div class="fgrid">%s</div></div></section>'%(E(short),''.join('<div><h3>%s</h3><p>%s</p></div>'%(E(t),E(x)) for t,x in sv[:3]))
    m+='<section class="bnd tint"><div class="w"><div class="sh one"><h2>%s için kurulu başlar</h2></div><div class="set sk2"><div><h3>Hizmet ve katalog</h3>%s<h3 style="margin-top:28px">Sık talepler</h3>%s</div><div><h3>Kontrol listesi</h3><ul class="ticks">%s</ul><p class="note2">Maddeleri panelden değiştirebilirsiniz.</p>%s</div></div></div></section>'%(E(short),chips([t for t,_ in sv]+brands[:4]),chips(d['faults'][:7]),''.join('<li>%s</li>'%E(c[0]) for c in d['checklist']),('<h3 style="margin-top:28px">Panelde sizin dilinizle</h3>'+chips(['%s → %s'%(k,v) for k,v in terms[:4]])) if terms else '')
    m+='<section class="ctab"><div class="w"><div class="cta2"><div><h2>%s için Profesyonel</h2><p>Otomatik SMS, kasa takibi ve raporlar dahil. Yeni müşteri için Tam Paket\'teki web sitesini de ekleyebilirsiniz.</p></div><a class="pill" href="fiyatlar.html">Paketleri incele</a></div></div></section>'%E(short)
    m+='<section id="sss" class="tint"><div class="w"><div class="sss"><h2>Sık sorulan sorular</h2><div>%s</div></div></div></section>'%''.join('<details%s><summary>%s</summary><p>%s</p></details>'%(' open' if i==0 else '',E(q),E(a)) for i,(q,a) in enumerate(fq))
    m+='<section class="bnd oth"><div class="w"><div class="sh one"><h2>Diğer sektörler</h2></div><div class="chp rel">%s<a href="sektorler.html">Tüm sektörler</a></div></div></section>'%''.join('<a href="sektor-%s.html">%s</a>'%(s,n) for s,n in ALLSEC if s!=slug)
    m+='<section id="kayit" class="dkk"><div class="w"><div class="fc"><div><h2>%s işletmenizi dijitale taşıyın</h2><p>Formu doldurun, uzmanımız sektörünüze göre kurulumu birlikte planlasın. İlk ay ücretsiz.</p><a class="big" href="tel:05444444004">0544 444 40 04</a></div> <div class="frm"><div><label for="f1">Ad soyad</label><input id="f1" autocomplete="name"></div><div><label for="f2">Telefon</label><input id="f2" type="tel" autocomplete="tel"></div><div><label for="f3">Firma adı</label><input id="f3" autocomplete="organization"></div><div><label for="f4">Sektör</label><select id="f4">%s</select></div><a class="bt" href="#">Beni arayın</a><small>Bilgileriniz yalnızca sizinle iletişim için kullanılır (KVKK).</small></div></div></div></section>'%(E(short),OPTS)
    p=HEAD.replace('Kombi Servisi Takip Programı | OnlineKaydet',E(title)+' | OnlineKaydet').replace('Kombi servisleri için servis kaydı, bakım hatırlatma, usta atama, imzalı servis fişi ve müşteriye SMS. Marka ve model listesi hazır.',E(lead))+m+TAIL
    open('sektor-%s.html'%slug,'w',encoding='utf-8').write(p)
# eski 8 sayfada 'Diğer sektörler' ve form listesi de 16'ya çıksın
for s,n in ALLSEC[:8]:
    f='sektor-%s.html'%s; h=open(f,encoding='utf-8').read()
    h=re.sub(r'<select id="f4">.*?</select>','<select id="f4">%s</select>'%OPTS,h,flags=re.S)
    extra=''.join('<a href="sektor-%s.html">%s</a>'%(x,y) for x,y in ALLSEC[8:])
    if 'sektor-oto-servis' not in h.split('Diğer sektörler')[-1]:
        h=h.replace('<a href="sektorler.html">Tüm sektörler</a>',extra+'<a href="sektorler.html">Tüm sektörler</a>',1)
    open(f,'w',encoding='utf-8').write(h)
print('ok')
