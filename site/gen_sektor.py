import re,json,sys
sys.path.insert(0,'/home/claude/onlinekaydet/panel')
import sektor as S
T=open('sektor-kombi.tpl').read()
CHIPS_OLD='<div class="chips"><span>Baymak</span><span>Vaillant</span><span>Demirdöküm</span><span>Bosch</span><span>ECA</span><span>Buderus</span><span>Ariston</span><span>Viessmann</span></div>'
CK_OLD=re.search(r'<div class="ck">.*?</div></div></div></div></section>',T,re.S).group(0)
FAQ_OLD=re.search(r'<div class="faq">.*?</div></div></div></section>',T,re.S).group(0)
PB_OLD=re.search(r'<div class="pb">.*?</div></div></div></section>',T,re.S).group(0)
ck_item=lambda t,k:f'<div><i data-i="check"></i>{t}<small>{k}</small></div>'
D={
'klima':dict(file='sektor-klima',name='Klima',h1='Klima servisi için <em>servis takip programı</em>',tag='Klima servisleri için',
 lead='Montaj, bakım ve arıza kayıtları, usta atama ve imzalı servis fişi. Marka listesi ve kontrol listesi hazır gelir.',
 hl=['Daikin, Mitsubishi Electric, Samsung, LG, Arçelik marka kataloğu','Montaj ve bakım için hazır kontrol listeleri','Müşteriye otomatik SMS ve takip linki'],
 mock=('Klima','Daikin','Split inverter 12.000 BTU','Soğutmuyor, gaz eksik'),
 prob=[('Mevsim başında yığılan işler','Yaz öncesi gelen çağrılar telefonda ve kağıtta dağılıyor, sıra karışıyor.','Randevu ve usta atama tek ekranda, günlük plan hazır'),('Montaj ve arıza karışıyor','Aynı ustaya iki ayrı iş bildirimi yanlış zamanda gidiyor.','Her kayıtta iş türü, adres ve randevu saati ayrı görünür'),('Servis fişi sonradan yazılıyor','Yapılan işlem ve değişen parça akılda kalmıyor, müşteri fiyatı sorguluyor.','Parça, işçilik ve fotoğraf kayıtta, imzalı PDF fiş hazır')],
 ready='Klima servisi için kurulu başlar',steps='Klima arızasından <em>servis fişine</em>',pkg='Klima servisleri için <em>Profesyonel</em>',
 faq=[('Klima için hangi markalar hazır geliyor?','Daikin, Mitsubishi Electric, Samsung, LG, Arçelik, Vestel, Bosch ve Airfel başlangıç listesinde gelir. Eksikleri panelden siz eklersiniz.'),('Montaj ve bakım işini ayrı takip edebilir miyim?','Evet. Her kayıtta iş türü ve arıza girilir, kontrol listeleri iş türüne göre kullanılır.'),('Ustalarım kendi telefonundan çalışabilir mi?','Evet. Her usta kendi kullanıcı adıyla girer, yalnızca kendine atanan işleri görür.'),('Servis fişinde kendi logomu kullanabilir miyim?','Evet. Fiş tasarımını, imza alanını ve metinleri Servis Ayarları\'ndan düzenlersiniz.')],
 meta='Klima servisleri için servis kaydı, usta atama, imzalı servis fişi ve müşteriye otomatik SMS. Marka listesi ve kontrol listesi hazır.'),
'beyaz-esya':dict(file='sektor-beyaz-esya',key='beyaz_esya',name='Beyaz Eşya',h1='Beyaz eşya servisi için <em>servis takip programı</em>',tag='Beyaz eşya servisleri için',
 lead='Çamaşır, bulaşık makinesi ve buzdolabı onarımlarını tek kayıtta tutun. Usta atama, imzalı fiş ve müşteriye SMS hazır.',
 hl=['Arçelik, Beko, Bosch, Siemens, Samsung, LG marka kataloğu','Arıza, parça ve işçilik kayıtta, fiş otomatik','Müşteriye otomatik SMS ve takip linki'],
 mock=('Çamaşır makinesi','Arçelik','8 kg çamaşır makinesi','Su boşaltmıyor'),
 prob=[('Parça ikinci ziyareti doğuruyor','Arıza telefonda eksik anlatılıyor, usta parçasız gidiyor.','Arıza ve cihaz kayıtta, usta işe hazır gider'),('Müşteri iş durumunu soruyor','Her gün gelen "usta ne zaman gelecek" aramaları işi bölüyor.','Müşteriye takip linki ve randevu SMS\'i otomatik gider'),('Fiş ve ücret kayıtsız','Yapılan işlem elle yazılıyor, sonradan fark çıkıyor.','Parça ve işçilik kayıtta, imzalı PDF fiş hazır')],
 ready='Beyaz eşya servisi için kurulu başlar',steps='Beyaz eşya arızasından <em>servis fişine</em>',pkg='Beyaz eşya servisleri için <em>Profesyonel</em>',
 faq=[('Hangi markalar hazır geliyor?','Arçelik, Beko, Bosch, Siemens, Samsung, LG, Vestel, Profilo ve Altus başlangıç listesinde gelir. Eksikleri panelden siz eklersiniz.'),('Her cihaz türü için ayrı kayıt tutabilir miyim?','Evet. Cihaz türü, marka ve model her kayıtta seçilir; eksik marka ve modelleri katalogdan eklersiniz.'),('Ustalarım kendi telefonundan çalışabilir mi?','Evet. Her usta kendi kullanıcı adıyla girer, yalnızca kendine atanan işleri görür.'),('Servis fişinde kendi logomu kullanabilir miyim?','Evet. Fiş tasarımını, imza alanını ve metinleri Servis Ayarları\'ndan düzenlersiniz.')],
 meta='Beyaz eşya servisleri için servis kaydı, usta atama, imzalı servis fişi ve müşteriye SMS. Arçelik, Beko, Bosch marka listesi hazır.'),
'elektronik':dict(file='sektor-elektronik',name='Elektronik & TV',h1='Elektronik servisi için <em>servis takip programı</em>',tag='Elektronik ve TV servisleri için',
 lead='TV ve elektronik cihaz onarımlarında cihaz teslimi, arıza, parça ve fiyat kaydı tek yerde. İmzalı fiş ve müşteriye SMS hazır.',
 hl=['Samsung, LG, Sony, Philips, Vestel marka kataloğu','Cihaz dış durum fotoğrafı ve aksesuar teslim listesi','Müşteriye otomatik SMS ve takip linki'],
 mock=('TV','Samsung','55 inç LED TV','Görüntü yok, ses var'),
 prob=[('Cihaz teslimi kayıtsız kalıyor','Hangi cihaz hangi aksesuarla geldi, nasıl bir durumdaydı belli olmuyor.','Dış durum fotoğrafı ve aksesuar listesi kayda girer'),('Onarım durumu sorulup duruluyor','Müşteri cihazının ne aşamada olduğunu telefonla soruyor.','Takip linki ve durum SMS\'i müşteriye otomatik gider'),('Fiyat ve fiş tartışması','Parça ve işçilik yazılı değilse müşteri fiyatı sorguluyor.','Parça, işçilik ve fotoğraf kayıtta, imzalı PDF fiş hazır')],
 ready='Elektronik servisi için kurulu başlar',steps='Cihaz tesliminden <em>servis fişine</em>',pkg='Elektronik servisleri için <em>Profesyonel</em>',
 faq=[('Hangi markalar hazır geliyor?','Samsung, LG, Sony, Philips, Vestel, Arçelik, TCL ve Hisense başlangıç listesinde gelir. Eksikleri panelden siz eklersiniz.'),('Cihaz teslimini fotoğrafla kaydedebilir miyim?','Evet. Kayıtta işlem öncesi ve sonrası fotoğrafı zorunlu, isteğe bağlı ya da kapalı yapabilirsiniz.'),('Ustalarım kendi telefonundan çalışabilir mi?','Evet. Her usta kendi kullanıcı adıyla girer, yalnızca kendine atanan işleri görür.'),('Servis fişinde kendi logomu kullanabilir miyim?','Evet. Fiş tasarımını, imza alanını ve metinleri Servis Ayarları\'ndan düzenlersiniz.')],
 meta='Elektronik ve TV servisleri için servis kaydı, cihaz teslim fotoğrafı, imzalı fiş ve müşteriye SMS. Marka listesi hazır.'),
'bilgisayar':dict(file='sektor-bilgisayar',name='Bilgisayar & Telefon',h1='Bilgisayar ve telefon servisi için <em>takip programı</em>',tag='Bilgisayar ve telefon servisleri için',
 lead='Bilgisayar, telefon ve tablet onarımlarında cihaz teslimi, yedek bilgisi, arıza ve fiyat teklifi tek kayıtta. İmzalı fiş ve SMS hazır.',
 hl=['Apple, Samsung, Lenovo, HP, Dell, Asus marka kataloğu','Şifre/yedek bilgisi ve aksesuar teslim listesi','Müşteriye otomatik SMS ve takip linki'],
 mock=('Telefon','Samsung','Galaxy A54','Ekran kırık, şarj almıyor'),
 prob=[('Teslim alınan cihaz belgesiz','Çizik, şifre ve aksesuar bilgisi yazılmayınca teslimde tartışma çıkıyor.','Dış durum fotoğrafı ve teslim listesi kayda girer'),('Fiyat teklifi dağınık','Onarım fiyatı mesajlarda kalıyor, kim ne onayladı belli değil.','Parça ve işçilik kayıtta, imzalı fiş hazır'),('Müşteri sürekli arıyor','"Cihazım hazır mı" aramaları işi bölüyor.','Takip linki ve durum SMS\'i müşteriye otomatik gider')],
 ready='Bilgisayar ve telefon servisi için kurulu başlar',steps='Cihaz tesliminden <em>servis fişine</em>',pkg='Bilgisayar ve telefon servisleri için <em>Profesyonel</em>',
 faq=[('Hangi markalar hazır geliyor?','Apple, Samsung, Lenovo, HP, Dell, Asus, Huawei ve Xiaomi başlangıç listesinde gelir. Eksikleri panelden siz eklersiniz.'),('Müşteri verisi için şifre/yedek bilgisi alabilir miyim?','Kontrol listesinde "şifre/yedek bilgisi alındı" maddesi hazır gelir; maddeleri Servis Ayarları\'ndan değiştirebilirsiniz.'),('Ustalarım kendi telefonundan çalışabilir mi?','Evet. Her usta kendi kullanıcı adıyla girer, yalnızca kendine atanan işleri görür.'),('Servis fişinde kendi logomu kullanabilir miyim?','Evet. Fiş tasarımını, imza alanını ve metinleri Servis Ayarları\'ndan düzenlersiniz.')],
 meta='Bilgisayar ve telefon servisleri için servis kaydı, cihaz teslim listesi, imzalı fiş ve müşteriye SMS. Marka listesi hazır.'),
'tesisat':dict(file='sektor-tesisat',name='Tesisat & Su',h1='Tesisat servisi için <em>servis takip programı</em>',tag='Tesisat servisleri için',
 lead='Su kaçağı, tıkanıklık ve armatür işlerinde çağrı kaydı, usta atama ve imzalı servis fişi tek yerde. Müşteriye SMS ve takip linki gider.',
 hl=['Sık arıza listesi ve tesisat kontrol listesi hazır','Usta yola çıkınca müşteriye takip linki','Parça, işçilik ve fotoğraflı imzalı fiş'],
 mock=('Tesisat','Genel','Mutfak armatürü','Kaçak var, tıkanıklık'),
 prob=[('Acil çağrılar kaçıyor','Telefonla gelen acil işler not edilmeyince ustaya geç ulaşıyor.','Çağrı anında kayıt açılır, usta telefonundan görür'),('Usta nerede belli değil','Müşteri ustanın ne zaman geleceğini defalarca soruyor.','Usta "yoldayım" der, müşteriye takip linki SMS ile gider'),('İş sonrası belge yok','Yapılan iş ve ücret yazılı olmayınca sonradan tartışılıyor.','Parça, işçilik ve fotoğraf kayıtta, imzalı PDF fiş hazır')],
 ready='Tesisat servisi için kurulu başlar',steps='Çağrıdan <em>servis fişine</em>',pkg='Tesisat servisleri için <em>Profesyonel</em>',chips_label='faults',
 faq=[('Tesisat için kontrol listesi hazır geliyor mu?','Evet. Ana vana kapatıldı, kaçak/sızdırmazlık testi ve çalışma alanı temizliği gibi maddeler hazır gelir; Servis Ayarları\'ndan değiştirebilirsiniz.'),('Sık arızalar hazır geliyor mu?','Kayıt formunda sektöre göre sık arıza listesi hazır gelir; kendi arızalarınızı da ekleyebilirsiniz.'),('Ustalarım kendi telefonundan çalışabilir mi?','Evet. Her usta kendi kullanıcı adıyla girer, yalnızca kendine atanan işleri görür.'),('Servis fişinde kendi logomu kullanabilir miyim?','Evet. Fiş tasarımını, imza alanını ve metinleri Servis Ayarları\'ndan düzenlersiniz.')],
 meta='Tesisat ve su servisleri için çağrı kaydı, usta atama, imzalı servis fişi ve müşteriye SMS takip linki.'),
'elektrik':dict(file='sektor-elektrik',name='Elektrik',h1='Elektrik servisi için <em>servis takip programı</em>',tag='Elektrik servisleri için',
 lead='Arıza, pano ve aydınlatma işlerinde çağrı kaydı, usta atama ve imzalı servis fişi tek yerde. Güvenlik kontrol listesi hazır gelir.',
 hl=['Enerji kesildi ve topraklama gibi kontrol maddeleri hazır','Usta yola çıkınca müşteriye takip linki','Parça, işçilik ve fotoğraflı imzalı fiş'],
 mock=('Elektrik','Genel','Pano ve sigorta','Sigorta atıyor'),
 prob=[('Güvenlik adımı atlanıyor','Enerji kesme ve test adımları akılda kalıyor, kayıt olmuyor.','Kontrol listesi her işte hazır, tamamlanan maddeler kayıtta'),('İş yükü ustalar arasında dağılmıyor','Çağrılar tek kişide yığılıyor, diğeri boş kalıyor.','Usta atama ve günlük plan tek ekranda'),('Yapılan iş belgesiz','Değişen malzeme ve işçilik yazılı değilse müşteri sorguluyor.','Parça, işçilik ve fotoğraf kayıtta, imzalı PDF fiş hazır')],
 ready='Elektrik servisi için kurulu başlar',steps='Arıza çağrısından <em>servis fişine</em>',pkg='Elektrik servisleri için <em>Profesyonel</em>',chips_label='faults',
 faq=[('Elektrik için kontrol listesi hazır geliyor mu?','Evet. Enerji kesildi teyidi, topraklama kontrolü ve işlem sonrası test maddeleri hazır gelir. Bunlar genel iyi uygulama maddeleridir, mevzuat yerine geçmez.'),('Kayıt formunda sık arızalar hazır mı?','Sektöre göre sık arıza listesi hazır gelir; kendi arızalarınızı da ekleyebilirsiniz.'),('Ustalarım kendi telefonundan çalışabilir mi?','Evet. Her usta kendi kullanıcı adıyla girer, yalnızca kendine atanan işleri görür.'),('Servis fişinde kendi logomu kullanabilir miyim?','Evet. Fiş tasarımını, imza alanını ve metinleri Servis Ayarları\'ndan düzenlersiniz.')],
 meta='Elektrik servisleri için çağrı kaydı, usta atama, kontrol listesi, imzalı servis fişi ve müşteriye SMS.'),
'guvenlik':dict(file='sektor-guvenlik',name='Güvenlik & Kamera',h1='Güvenlik ve kamera servisi için <em>takip programı</em>',tag='Güvenlik ve kamera servisleri için',
 lead='Kamera, alarm ve geçiş sistemleri için kurulum ve bakım kayıtlarını tek yerde tutun. Usta atama, imzalı fiş ve müşteriye SMS hazır.',
 hl=['Hikvision, Dahua, Uniview, Ajax, Hilook marka kataloğu','Görüş açısı ve kayıt cihazı kontrol listeleri','Müşteriye otomatik SMS ve takip linki'],
 mock=('Güvenlik','Hikvision','8 kameralı kayıt seti','Kayıt almıyor, uzaktan erişim yok'),
 prob=[('Kurulum bilgisi dağınık','Hangi sitede hangi cihaz ve disk var, bir yerde toplu görünmüyor.','Cihaz, marka ve model müşteri kaydında tutulur'),('Bakım ziyaretleri unutuluyor','Periyodik kontrol tarihleri defterde kalıyor.','Her servis kaydı müşteri geçmişinde, tekrar işlemler kolay'),('Teslim belgesiz','Yapılan kurulum ve test sonrası müşteriden onay alınmıyor.','Test maddeleri ve imzalı PDF fiş kayıtta')],
 ready='Güvenlik servisi için kurulu başlar',steps='Kurulumdan <em>servis fişine</em>',pkg='Güvenlik servisleri için <em>Profesyonel</em>',
 faq=[('Hangi markalar hazır geliyor?','Hikvision, Dahua, Uniview, Ajax ve Hilook başlangıç listesinde gelir. Eksikleri panelden siz eklersiniz.'),('Kamera için kontrol listesi hazır geliyor mu?','Evet. Kamera görüş açısı, kayıt cihazı/disk ve uzaktan erişim testi gibi maddeler hazır gelir.'),('Ustalarım kendi telefonundan çalışabilir mi?','Evet. Her usta kendi kullanıcı adıyla girer, yalnızca kendine atanan işleri görür.'),('Servis fişinde kendi logomu kullanabilir miyim?','Evet. Fiş tasarımını, imza alanını ve metinleri Servis Ayarları\'ndan düzenlersiniz.')],
 meta='Güvenlik ve kamera sistemleri için kurulum/bakım kaydı, usta atama, imzalı servis fişi ve müşteriye SMS. Hikvision, Dahua marka listesi hazır.')}
LINKS=[('Kombi','sektor-kombi.html'),('Klima','sektor-klima.html'),('Beyaz Eşya','sektor-beyaz-esya.html'),('Elektronik & TV','sektor-elektronik.html'),('Bilgisayar & Telefon','sektor-bilgisayar.html'),('Tesisat','sektor-tesisat.html'),('Elektrik','sektor-elektrik.html'),('Güvenlik & Kamera','sektor-guvenlik.html'),('Tüm sektörler','sektorler.html')]
def rel(cur): return '<div class="rel">'+''.join(f'<a href="{h}">{n}</a>' for n,h in LINKS if h!=cur+'.html')+'</div>'
def seo(d,url,faq):
    ld={"@context":"https://schema.org","@graph":[{"@type":"SoftwareApplication","name":"OnlineKaydet — "+d['name']+" servisleri için servis takip programı","applicationCategory":"BusinessApplication","operatingSystem":"Web, Android","description":d['meta'],"url":url,"publisher":{"@type":"Organization","name":"OnlineKaydet","url":"https://onlinekaydet.com"}},{"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}]}
    return (f'<meta name="description" content="{d["meta"]}"><link rel="canonical" href="{url}"><meta property="og:title" content="{d["name"]} servisi programı — OnlineKaydet"><meta property="og:description" content="{d["meta"]}"><meta property="og:type" content="website"><meta property="og:url" content="{url}">'
            '<script type="application/ld+json">'+json.dumps(ld,ensure_ascii=False)+'</script>')

FIS={'kombi':("Kombi","Ayşe Y. · Bornova","Baymak Duo-Tec 24","Isıtmıyor, E01 hatası","Hasan Y.","Parça değişti, fotoğraf eklendi","1.250"),
'klima':("Klima","Mehmet K. · Karşıyaka","Daikin 12.000 BTU","Soğutmuyor, gaz kaçağı şüphesi","Emre T.","Gaz dolumu yapıldı, test edildi","1.800"),
'beyaz-esya':("Beyaz eşya","Selin D. · Bayraklı","Arçelik çamaşır makinesi","Su boşaltmıyor","Murat Ş.","Pompa değişti, fotoğraf eklendi","950"),
'elektronik':("Elektronik","Can A. · Buca","Samsung 55\" televizyon","Görüntü yok, ses var","Okan B.","Arka ışık şeridi değişti","2.100"),
'bilgisayar':("Bilgisayar","Deniz Ö. · Konak","Dizüstü bilgisayar","Açılmıyor, şarj olmuyor","Burak Y.","Şarj soketi değişti, test edildi","1.100"),
'tesisat':("Tesisat","Ali R. · Çiğli","Banyo gideri","Su gitmiyor, tıkanıklık","Kemal S.","Tıkanıklık açıldı, kamera ile kontrol","700"),
'elektrik':("Elektrik","Zeynep A. · Bornova","Daire sigorta panosu","Sürekli sigorta atıyor","Ferhat K.","Kaçak akım rölesi değişti, ölçüm yapıldı","1.400"),
'guvenlik':("Güvenlik","Orhan T. · Karşıyaka","Hikvision 8 kameralı set","Kayıt almıyor, uzaktan erişim yok","Serkan D.","Disk değişti, uzaktan erişim test edildi","2.300")}
CH=[('Kombi','sektor-kombi'),('Klima','sektor-klima'),('Beyaz eşya','sektor-beyaz-esya'),('Elektronik','sektor-elektronik'),('Bilgisayar','sektor-bilgisayar'),('Tesisat','sektor-tesisat'),('Elektrik','sektor-elektrik'),('Güvenlik','sektor-guvenlik')]
def hero(d,k):
    f=d['file']; x=FIS[k]; T_=["09:12","10:05","10:48","11:02"]; L=["Kayıt açıldı","Usta yolda, müşteriye SMS gitti",x[5],"İmzalı fiş SMS ile gönderildi"]
    chips=''.join(f'<a href="{h}.html"'+(' class="on"' if h==f else '')+f'>{n}</a>' for n,h in CH)
    tl=''.join(f'<div><span class="t">{t}</span><span class="d{" o" if i==3 else ""}"></span><b>{L[i]}</b></div>' for i,t in enumerate(T_))
    fis=f'<div class="top"><span class="no">İŞ EMRİ #2417</span><span class="sec">{x[0]} · örnek kayıt</span></div><dl><dt>Müşteri</dt><dd>{x[1]}</dd><dt>Cihaz</dt><dd>{x[2]}</dd><dt>Arıza</dt><dd>{x[3]}</dd><dt>Usta</dt><dd>{x[4]}</dd></dl><div class="tl">{tl}</div><div class="ftr"><span class="tot">TOPLAM {x[6]} ₺</span><span class="stamp">TAHSİL EDİLDİ</span></div>'
    h1=d['h1'].replace('<em>','<u>').replace('</em>','</u>')
    return (f'<div class="nh"><div class="w"><div class="ng"><div><span class="eb">{d["tag"]}</span><h1>{h1}</h1><p class="lead">{d["lead"]}</p>'
            f'<div class="chips">{chips}</div><div class="nhc"><a class="bt o lg" href="#kayit">Ücretsiz Dene</a><a class="tel" href="tel:05444444004"><i data-i="phone"></i>0544 444 40 04</a></div><div class="note">Fiş örnek bir kayıttır.</div></div>'
            f'<div><div class="nfs">{fis}</div></div></div></div></div>')
def build(k,d):
    s=T; key=d.get('key',k); sec=S.SECTORS[key]; name=d['name']
    R=lambda a,b: s.replace(a,b,1) if a in s else (_ for _ in ()).throw(SystemExit('YOK: '+a[:50]))
    s=R('<title>Kombi servisi programı — OnlineKaydet</title>',f'<title>{name} servisi programı — OnlineKaydet</title>')
    s=R('</a><span>›</span>Kombi</div>',f'</a><span>›</span>{name}</div>')
    s=R('<b>Kombi</b>Kombi servisleri için',f'<b>{name.split(" ")[0]}</b>{d["tag"]}')
    s=R('Kombi servisi için <em>servis takip programı</em>',d['h1'])
    s=R('Bakım hatırlatma, arıza kaydı, usta atama, yedek parça ve imzalı servis fişi. Marka ve model listesi, kontrol listesi hazır gelir.',d['lead'])
    for old,new in zip(['Baymak, Vaillant, Demirdöküm, Bosch, ECA marka ve model kataloğu','Yıllık bakım ve arıza için hazır kontrol listeleri','Müşteriye otomatik SMS ve takip linki'],d['hl']): s=R(old,new)
    t,m,mo,ar=d['mock']
    s=R('<label>Cihaz türü</label><div class="f">Kombi</div>',f'<label>Cihaz türü</label><div class="f">{t}</div>')
    s=R('<div class="f">Vaillant</div>',f'<div class="f">{m}</div>'); s=R('<div class="f">ecoTEC plus 24/28</div>',f'<div class="f">{mo}</div>'); s=R('<div class="f">Isıtmıyor, F28 hatası</div>',f'<div class="f">{ar}</div>')
    s=R('Kombi servislerinin <em>en sık yaşadığı üç sorun</em>',f'{name} servislerinin <em>en sık yaşadığı üç sorun</em>')
    oldp=[('Bakım zamanı kaçıyor','Yıllık bakım tarihleri defterde kalıyor, müşteri başka servise gidiyor.','Bakım hatırlatma: müşteriye zamanı gelince otomatik SMS'),('Usta eksik parçayla gidiyor','Arıza bilgisi telefonda anlatılınca yanlış parça, ikinci ziyaret çıkıyor.','Arıza ve model kayıtta, usta işe hazır gider'),('Garanti ve ücret tartışması','Cihaz yaşı ve garanti durumu belli değil, fiş elle yazılıyor.','Garanti süresi kayıtta, imzalı PDF fiş hazır')]
    for (a,b,c),(x,y,z) in zip(oldp,d['prob']): s=R(a,x); s=R(b,y); s=R(c,z)
    s=R('Kombi servisi için kurulu başlar',d['ready'])
    if d.get('chips_label')=='faults':
        s=R('<span class="eb">Hazır gelenler</span>','<span class="eb">Sık arızalar hazır</span>')
        s=R(CHIPS_OLD,'<div class="chips">'+''.join(f'<span>{x}</span>' for x in sec['faults'])+'</div>')
    else:
        s=R(CHIPS_OLD,'<div class="chips">'+''.join(f'<span>{x}</span>' for x in sec['brands'])+'</div>')
    cks=[(t,'Zorunlu' if z else 'Kontrol') for t,z in sec['checklist']][:5]
    s=R(CK_OLD,'<div class="ck">'+''.join(ck_item(t,k2) for t,k2 in cks)+'</div></div></div></div></section>')
    s=R('Kombi arızasından <em>servis fişine</em>',d['steps'])
    s=R('Müşteri, marka ve model seçilerek kayıt açılır. Arıza ve randevu saati girilir.','Müşteri ve cihaz seçilerek kayıt açılır. Arıza ve randevu saati girilir.')
    s=R('Kombi servisleri için <em>Profesyonel</em>',d['pkg'])
    f='<div class="faq">'+''.join(f'<div class="q{" o" if i==0 else ""}"><b>{q}</b><p>{a}</p></div>' for i,(q,a) in enumerate(d['faq']))+'</div></div></section>'
    s=R(FAQ_OLD,f)
    s=re.sub(r'<div class="rel">.*?</div>',rel(d['file']),s,count=1,flags=re.S)
    s=R('<h2>Kombi servisinizi dijitale taşıyın</h2>',f'<h2>{name} servisinizi dijitale taşıyın</h2>')
    s=s.replace('<option>Kombi</option>','<option>Kombi</option>',1)
    opt=name.split(' ')[0]; opt={'Beyaz':'Beyaz eşya','Elektronik':'Elektronik','Bilgisayar':'Bilgisayar','Güvenlik':'Güvenlik'}.get(opt,opt)
    fi=s.index('<div class="frm">'); s=s[:fi]+s[fi:].replace(f'<option>{opt}</option>',f'<option selected>{opt}</option>',1)
    s=s.replace('<a class="bt lg" href="#">Canlı Demoyu Gör</a>','<a class="bt lg" href="demo.html">Canlı Demoyu Gör</a>').replace('<a class="bt o lg" href="#">Paketleri İncele</a>','<a class="bt o lg" href="fiyatlar.html">Paketleri İncele</a>')
    url='https://onlinekaydet.com/'+d['file']+'.html'
    s=s.replace('</title>','</title>'+seo(d,url,d['faq']),1)
    s=re.sub(r'<div class="ih">.*?</div></div></div></div></div>\n',lambda m:hero(d,k)+'\n',s,count=1,flags=re.S)
    open(d['file']+'.html','w').write(s)
for k,d in D.items(): build(k,d)
print('ok',len(D))
# kombi: şablonun kendisi, yalnızca üst bölüm yenilenir
_k=dict(file='sektor-kombi',tag='Kombi servisleri için',h1='Kombi servisi için <em>servis takip programı</em>',lead='Bakım hatırlatma, arıza kaydı, usta atama, yedek parça ve imzalı servis fişi. Marka ve model listesi, kontrol listesi hazır gelir.')
_s=re.sub(r'<div class="ih">.*?</div></div></div></div></div>\n',lambda m:hero(_k,'kombi')+'\n',T,count=1,flags=re.S)
open('sektor-kombi.html','w').write(_s)
