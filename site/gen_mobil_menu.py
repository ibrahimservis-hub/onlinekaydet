"""Mobil menüyü yeniler: ana sayfa (#mmenu) ve iç sayfalar (#nxm). Tekrar çalıştırılabilir (<!--mm--> işareti)."""
import pathlib,re
def mm_html(cls,id_):
    return ('<div class="%s mm" id="%s"><!--mm-->'
     '<div class="mm-try"><span class="mm-rz"><b>7 GÜN</b><small>ÜCRETSİZ</small></span><p class="mm-t1">Satın almadan önce deneyin</p><p class="mm-t2">Kart bilgisi istenmez. Sitenizi, siparişlerinizi ve randevularınızı hemen kurun.</p><a class="mm-cta" href="/demo.html">Ücretsiz deneyin <i>→</i></a></div>'
     '<nav class="mm-l" aria-label="Mobil menü"><details><summary>Ürün</summary><div><a href="/web-sitesi.html">Web sitesi</a><a href="/e-ticaret.html">E-ticaret</a><a href="/is-takibi.html">Randevu ve iş takibi</a><a href="/muhasebe-ve-stok.html">Muhasebe ve stok</a><a href="/ozellikler.html">Tüm özellikler</a></div></details>'
     '<a href="/temalar.html">Temalar</a><a href="/sektorler.html">Sektörler</a><a href="/fiyatlar.html">Paketler ve fiyatlar</a><a href="/iletisim.html">İletişim</a></nav>'
     '<div class="mm-s"><a href="/bilgi-bankasi.html">Bilgi bankası</a><a href="/blog.html">Blog</a><a href="/destek.html">Destek</a><a href="/hakkimizda.html">Hakkımızda</a></div>'
     '<div class="mm-bt"><div class="mm-c"><a href="tel:+905444444004">Hemen arayın</a><a class="wa" href="https://wa.me/905444444004">WhatsApp</a></div><a class="mm-in" href="/uye-girisi">Üye girişi</a></div>'
     '<!--/mm--></div>') % (cls,id_)
OLD=[(re.compile(r'<div class="nxm(?: mm)?" id="nxm">.*?(?:<!--/mm-->)?</div>(?=<!--/nxh-->)',re.S),'nxm','nxm'),
     (re.compile(r'<div class="mmenu(?: mm)?" id="mmenu">.*?(?:<!--/mm-->)?</div>(?=\s*<main)',re.S),'mmenu','mmenu')]
CSS='<link rel="stylesheet" href="/v9/mm.css?v=2">'
if __name__=='__main__':
    n=0
    for f in pathlib.Path('.').glob('*.html'):
        t=f.read_text(encoding='utf-8');o=t
        for rx,cls,id_ in OLD:
            t=rx.sub(lambda m:mm_html(cls,id_),t,count=1)
        if t!=o:
            t=re.sub(r'<link rel="stylesheet" href="/v9/mm\.css[^"]*">','',t)
            t=t.replace('</head>',CSS+'</head>',1);f.write_text(t,encoding='utf-8');n+=1
    print(n,'sayfa')
