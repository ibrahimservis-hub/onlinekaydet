# Ana sayfayi sadelestirir (idempotent): tekrar eden bolum, sayi seridi, SSS + API ornegi.
import re,glob
FAQ=[("Ücretsiz deneyebilir miyim?","Evet. Demo hesabını 7 gün ücretsiz deneyebilirsiniz. Deneme bitince bir paket seçersiniz; seçmezseniz hesabınız silinmez, yalnız işlem yapılması durur."),
("Temayı seçtikten sonra değiştirebilir miyim?","Evet. Temayı panelden istediğiniz zaman değiştirebilirsiniz; metinleriniz, ürünleriniz ve sayfa içerikleriniz yeni temaya taşınır."),
("Kendi alan adımı bağlayabilir miyim?","Evet. Alan adınızı panelden bağlarsınız; DNS adımlarını panel adım adım gösterir."),
("Verilerim başka firmalarla karışır mı?","Hayır. Her firmanın verisi kendi veritabanında ayrı tutulur; başka bir firma sizin kayıtlarınızı göremez."),
("Sektörüm listede yoksa ne olur?","Bizimle iletişime geçin. Listede olmayan bir iş kolu için paneldeki terimleri ve ekranları sizinle birlikte uyarlarız.")]
faq=''.join('<details class="sssd"><summary>%s</summary><p>%s</p></details>'%f for f in FAQ)
BLOK=('<!--SADE--><section class="sec sade"><div class="w"><div class="sg">'
'<div><h2>Açık API</h2><p>Ürün, fiyat ve stoğunuzu kendi yazılımınızdan okuyup güncelleyin. Sipariş ve müşteri verisi API’de yoktur.</p>'
'<pre class="kod">GET /urunler?q=süt&amp;adet=50\nPUT /urunler/869111\n{"fiyat": 31.5, "stok": 12}\nX-API-Key: ok_…</pre><a class="lnk" href="/acik-api-ve-entegrasyon.html">API sayfasına bakın</a></div>'
'<div><h2>Sık sorulan sorular</h2>'+faq+'<a class="lnk" href="/fiyatlar.html">Tüm sorular ve paketler</a></div></div></div></section><!--/SADE-->')
for f in ['index.html','v9/kaynak/index-v9.html']:
    s=open(f,encoding='utf-8').read()
    s=re.sub(r'<section class="dort">.*?</section>','',s,count=1,flags=re.S)
    s=re.sub(r'<div><b data-say="7">7</b><span>kampanya ve kupon türü</span></div>\s*','',s)
    s=re.sub(r'<div><b data-say="17">17</b><span>hazır rapor</span></div>\s*','',s)
    s=re.sub(r'<!--SADE-->.*?<!--/SADE-->','',s,flags=re.S)
    s=s.replace('<section class="son"',BLOK+'<section class="son"',1)
    open(f,'w',encoding='utf-8').write(s)
n=0
for f in glob.glob('*.html')+glob.glob('v9/kaynak/*.html')+glob.glob('v9/kaynak/eski/*.html'):
    s=open(f,encoding='utf-8').read()
    def fix(m): return m.group(0).replace('<a href="/web-sitesi.html">Web sitesi</a>','').replace('<a href="/is-takibi.html">İş takibi</a>','')
    t=re.sub(r'<nav class="nav" aria-label="Ana menü">.*?</nav>',fix,s,count=1,flags=re.S)
    if t!=s: open(f,'w',encoding='utf-8').write(t); n+=1
print(n)
