import re,glob,os,html
ROOT='..'
SKIP={'yeni-ana-sayfa.html','a-onizleme.html','index.html'}
pages=[os.path.basename(f) for f in sorted(glob.glob(ROOT+'/*.html')) if os.path.basename(f) not in SKIP and not os.path.basename(f).startswith('yon')]
names=set(pages)|{'index.html'}
NAV=[('ozellikler.html','Ürün'),('sektorler.html','Sektörler'),('temalar.html','Temalar'),('entegrasyonlar.html','Entegrasyonlar'),('fiyatlar.html','Fiyatlar'),('destek.html','Destek')]
SEC=[('sektor-kombi','Kombi'),('sektor-klima','Klima'),('sektor-beyaz-esya','Beyaz eşya'),('sektor-elektronik','Elektronik'),('sektor-bilgisayar','Bilgisayar'),('sektor-tesisat','Tesisat'),('sektor-elektrik','Elektrik'),('sektor-guvenlik','Güvenlik')]
ARW='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 8h12M9 3l5 5-5 5"/></svg>'
def header(cur,home=False):
    nav=''.join('<a href="%s"%s>%s</a>'%(h,' aria-current="page"' if h==cur or (cur.startswith('sektor-') and h=='sektorler.html') or (cur.startswith('blog') and h=='destek.html') else '',t) for h,t in NAV)
    mm=''.join('<a class="l" href="%s">%s%s</a>'%(h,t,ARW.replace('<svg','<svg width="20" height="20"')) for h,t in NAV)
    sub=''.join('<a href="%s.html">%s</a>'%(a,b) for a,b in SEC)
    return ('<a class="skip" href="#icerik">İçeriğe geç</a>'
    '<div class="o7-hd%s" id="o7hd"><div class="o7w"><a href="index.html" aria-label="OnlineKaydet ana sayfa"><img src="../logo-acik-s.png" alt="OnlineKaydet" width="154" height="30"></a>'
    '<nav class="o7-nav" aria-label="Ana menü">%s</nav><span class="o7-sp"></span><a class="gir" href="/giris">Giriş</a><a class="tel" href="tel:+905444444004">0544 444 40 04</a><a class="btn o sm" href="demo.html">Demo talep edin</a>'
    '<button class="o7-bg" type="button" aria-label="Menü" aria-expanded="false" aria-controls="o7mm"><svg class="m" viewBox="0 0 24 24"><path d="M3 8h18M3 16h18"/></svg><svg class="x" viewBox="0 0 24 24"><path d="M5 5l14 14M19 5L5 19"/></svg></button></div></div>'
    '<div class="o7-mm" id="o7mm">%s<div class="sub">%s</div><div class="cta"><a class="btn" href="demo.html">Demo talep edin</a><a class="btn o" href="/giris">Müşteri girişi</a></div><a class="tl" href="tel:+905444444004">0544 444 40 04</a></div>')%(' home' if home else '',nav,mm,sub)
FOOT='''<div class="o7-ft"><div class="o7w"><div class="gr5"><div><img src="../logo-acik-s.png" alt="OnlineKaydet" width="154" height="30"><p>Teknik servisler için servis kaydı, usta takibi, tahsilat ve web sitesi platformu.</p><a class="fph" href="tel:+905444444004">0544 444 40 04</a><a class="fwa" href="https://wa.me/905444444004" rel="noopener">WhatsApp ile yazın</a></div>
<div><h5>Ürün</h5><a href="ozellikler.html">Özellikler</a><a href="usta-uygulamasi.html">Usta uygulaması</a><a href="temalar.html">Temalar</a><a href="entegrasyonlar.html">Entegrasyonlar</a><a href="fiyatlar.html">Fiyatlar</a><a href="demo.html">Demo</a></div>
<div><h5>Sektörler</h5>%s</div>
<div><h5>Kaynaklar</h5><a href="blog.html">Blog</a><a href="destek.html">Destek</a><a href="komisyon-hesaplama.html">Komisyon hesaplama</a><a href="desi-hesaplama.html">Desi hesaplama</a><a href="hata-kodlari.html">Hata kodları</a></div>
<div><h5>OnlineKaydet</h5><a href="neden-onlinekaydet.html">Neden OnlineKaydet?</a><a href="hakkimizda.html">Hakkımızda</a><a href="bayilik.html">İş ortaklığı</a><a href="iletisim.html">İletişim</a><a href="/giris">Müşteri girişi</a></div></div>
<div class="cp"><span>© 2026 OnlineKaydet</span><a href="kvkk.html">KVKK</a><a href="gizlilik.html">Gizlilik</a><span class="sp"></span><span>onlinekaydet.com</span></div></div></div>'''%''.join('<a href="%s.html">%s</a>'%(a,b) for a,b in SEC)
VB='<div class="vb"><a class="p1" href="tel:+905444444004" aria-label="Ara">0544 444 40 04</a><a class="p2" href="https://wa.me/905444444004?text=Merhaba%2C%20OnlineKaydet%20hakk%C4%B1nda%20bilgi%20almak%20istiyorum." rel="noopener" target="_blank" aria-label="WhatsApp">WhatsApp</a></div>'
def fixrel(t):
    def f(m):
        a,q,u=m.group(1),m.group(2),m.group(3)
        if re.match(r'(https?:|/|#|mailto:|tel:|data:|javascript:|\.\./)',u) or u=='' : return m.group(0)
        base=u.split('#')[0].split('?')[0]
        if base in names: return m.group(0)
        return '%s=%s../%s%s'%(a,q,u,q)
    t=re.sub(r'\b(src|href|poster)=(["\'])([^"\']*)\2',lambda m:f(m).replace('=%s'%m.group(2),'=%s'%m.group(2),1) if False else f(m),t)
    return t
def cssname(s):
    ls=re.findall(r'<link rel="stylesheet" href="([^"]+)\.css"',s)
    return 'inner.%s.css'%'-'.join(ls)
def build(fn):
    s=open(ROOT+'/'+fn).read()
    title=re.search(r'<title>(.*?)</title>',s,re.S).group(1)
    desc=re.search(r'<meta name="description" content="([^"]*)"',s)
    desc=desc.group(1) if desc else ''
    ld=''.join(re.findall(r'<script type="application/ld\+json">.*?</script>',s,re.S))
    sprite=re.search(r'<svg[^>]*style="display:none"[^>]*>.*?</svg>',s,re.S) or re.search(r'<body[^>]*>\s*(<svg.*?</svg>)',s,re.S)
    sp=''
    if sprite:
        sp=sprite.group(0) if sprite.group(0).startswith('<svg') else sprite.group(1)
        for a,b in {'#0f1f46':'#14161a','#f27a1a':'#8a6d2f','#ffe4cb':'#e9e4d8','#f2760a':'#8a6d2f'}.items(): sp=sp.replace(a,b)
    mm=re.search(r'<main[^>]*>(.*)</main>',s,re.S)
    main=mm.group(1)
    main=re.sub(r'</?script[^>]*src=[^>]*></script>','',main)
    main=fixrel(main)
    inl=re.findall(r'<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>.*?</script>',s[s.find('</main>'):],re.S)
    cur=fn
    doc=('<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><meta name="theme-color" content="#0a0c0f">'
    '<link rel="icon" href="../favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="../favicon-32.png"><link rel="apple-touch-icon" href="../apple-touch-icon.png">'
    '<title>%s</title><meta name="description" content="%s">%s'
    '<link rel="stylesheet" href="shell.css"><link rel="stylesheet" href="%s">'
    '</head><body class="o7in">%s%s<main id="icerik">%s</main>%s%s'
    '<script>document.documentElement.classList.add("js")</script><script src="../site.js"></script><script src="../lead.js"></script><script src="ok7.js"></script>%s</body></html>')%(title,desc,ld,cssname(s),sp,header(cur),main,FOOT,VB,''.join(inl))
    open(fn,'w').write(doc)
for p in pages: build(p)
print(len(pages),'pages')
