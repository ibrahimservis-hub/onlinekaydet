#!/usr/bin/env python3
"""v9 ana sayfa mockup'ını (/tmp/v9/mockup.html) yayın sayfasına çevirir: WebP görseller, harici css/js, SEO başı, gerçek form."""
import re, os, json, shutil
from PIL import Image
R = '/home/claude/onlinekaydet'; SRC = '/tmp/v9'; OUT = R + '/site'
s = open(SRC + '/mockup.html', encoding='utf-8').read()
os.makedirs(OUT + '/v9/img', exist_ok=True); os.makedirs(OUT + '/v9/fonts', exist_ok=True)
# yazı tipleri
for f in os.listdir(R + '/themes/fonts'):
    if f.startswith(('bricolage', 'plex-', 'plexmono')):
        shutil.copyfile(R + '/themes/fonts/' + f, OUT + '/v9/fonts/' + f)
# css / js
css = re.search(r'<style>(.*?)</style>', s, re.S).group(1).replace('file:///home/claude/onlinekaydet/themes/fonts/', '/v9/fonts/')
css += '\n.q:not(.ac) p{display:none}.q h3{cursor:pointer}.q:focus-visible{outline:2px solid var(--cam);outline-offset:2px}.son form .alan{margin-top:12px}.son form .alan label{display:block;font-size:13px;color:var(--metin2)}.son form .alan input,.son form .alan select{width:100%;border:1px solid #b9beb6;height:46px;margin-top:5px;border-radius:6px;padding:0 14px;font:inherit;font-size:15px;background:#fff;color:var(--murekkep)}.son form button.bt{width:100%;margin-top:16px;background:var(--cam);border:1.5px solid var(--cam);color:#fff;height:52px;border-radius:2px;font:600 16px/1 var(--fb);cursor:pointer}.son form button.bt:disabled{opacity:.7}.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px 12px;z-index:99}'
open(OUT + '/v9/v9.css', 'w', encoding='utf-8').write(css)
js = re.search(r'<script>(.*?)</script>', s, re.S).group(1)
js = js.replace("d.querySelectorAll('.q').forEach(function(q){q.addEventListener('click',function(){q.classList.toggle('ac')})});",
 "d.querySelectorAll('.q').forEach(function(q){q.tabIndex=0;q.setAttribute('role','button');q.setAttribute('aria-expanded',q.classList.contains('ac'));function t(){q.classList.toggle('ac');q.setAttribute('aria-expanded',q.classList.contains('ac'))}q.addEventListener('click',t);q.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();t()}})});")
open(OUT + '/v9/v9.js', 'w', encoding='utf-8').write(js)
body = s[s.index('<body>') + 6:s.rindex('</body>')]
body = re.sub(r'<script>.*?</script>', '', body, flags=re.S)
body = body.replace('file:///home/claude/onlinekaydet/site/', '/')
# görseller -> webp
n = [0]
def img(m):
    tag = m.group(0); src = re.search(r'src="([^"]+)"', tag).group(1)
    if not re.match(r'(panel|tema)/', src): return tag
    p = SRC + '/' + src
    im = Image.open(p).convert('RGB'); w, h = im.size
    mx = 1400 if w > 1400 else w
    if mx != w: im = im.resize((mx, round(h * mx / w)), Image.LANCZOS); w, h = im.size
    dst = 'v9/img/' + src.replace('/', '-').rsplit('.', 1)[0] + '.webp'
    im.save(OUT + '/' + dst, 'WEBP', quality=80, method=6)
    n[0] += 1
    tag = tag.replace('src="%s"' % src, 'src="/%s"' % dst)
    tag = re.sub(r'\s(width|height|loading|decoding)="[^"]*"', '', tag)
    first = n[0] <= 3
    return tag.replace('<img', '<img width="%d" height="%d" %s' % (w, h, 'fetchpriority="high"' if first else 'loading="lazy" decoding="async"'), 1)
body = re.sub(r'<img[^>]*>', img, body)
body = body.replace('<img', '<img', 1)
# bağlantılar
body = body.replace('href="#dene"', 'href="/demo.html"').replace('class="logo" href="#"', 'class="logo" href="/"')
fl = {'Temalar': '/temalar.html', 'E-ticaret': '#eticaret', 'Web sitesi editörü': '#editor', 'Randevu': '#yonetim', 'Paketler': '#paketler', 'Teknik servis': '/sektor-kombi.html',
      'Kuaför ve güzellik': '/sektorler.html', 'Tüm sektörler': '/sektorler.html', 'Blog': '/blog.html', 'Entegrasyonlar': '/entegrasyonlar.html', 'Destek': '/destek.html',
      'Üye girişi': '/uye-girisi', 'Hakkımızda': '/hakkimizda.html', 'İletişim': '/iletisim.html', 'KVKK': '/kvkk.html', 'Gizlilik': '/kvkk.html'}
body = re.sub(r'<a>([^<]+)</a>', lambda m: '<a href="%s">%s</a>' % (fl[m.group(1)], m.group(1)) if m.group(1) in fl else m.group(0), body)
# gerçek form
form_old = re.search(r'<form>.*?</form>', body, re.S).group(0)
form_new = ('<div class="frm" id="teklif-form" style="grid-column:9/13;margin-top:32px;background:#fff;color:var(--murekkep);border-radius:12px;padding:26px"><b style="font:700 24px/1 var(--fd);letter-spacing:-.02em">Teklif alın</b>'
 '<div class="alan"><label for="tf1">Ad soyad</label><input id="tf1" autocomplete="name"></div><div class="alan"><label for="tf2">Telefon</label><input id="tf2" type="tel" autocomplete="tel"></div>'
 '<div class="alan"><label for="tf3">Firma adı</label><input id="tf3" autocomplete="organization"></div>'
 '<div class="alan"><label for="tf4">Sektörünüz</label><select id="tf4"><option>Seçiniz</option><option>Teknik servis</option><option>E-ticaret / mağaza</option><option>Kuaför ve güzellik</option><option>Sağlık ve klinik</option><option>Hukuk ve danışmanlık</option><option>Emlak</option><option>Eğitim</option><option>Diğer</option></select></div>'
 '<button class="bt" type="button">Teklif isteyin</button><small style="display:block;font-size:12px;color:var(--metin2);margin-top:10px">Bilgileriniz yalnız size dönüş yapmak için kullanılır. <a href="/kvkk.html" style="text-decoration:underline">KVKK</a></small></div>')
body = body.replace(form_old, form_new)
body = body.replace('<section class="son" id="teklif"><div class="w g">', '<section class="son" id="teklif"><div class="w g" data-form="teklif">', 1)
# SSS cevapları
ANS = {
 'Temayı seçtikten sonra değiştirebilir miyim?': 'Evet. Temayı panelden istediğiniz zaman değiştirebilirsiniz; metinleriniz, ürünleriniz ve sayfa içerikleriniz yeni temaya taşınır. Her bölümün metni, fontu ve görseli panelden düzenlenir.',
 'Kendi alan adımı bağlayabilir miyim?': 'Evet. Kendi alan adınızı panelden bağlarsınız; yönergeleri ve DNS adımlarını panel adım adım gösterir.',
 'Pazaryeri ve sanal POS hesaplarını kim bağlar?': 'Hesap bilgilerinizi siz girersiniz, kurulum sırasında yardımcı oluruz. Şu an Trendyol, Hepsiburada ve N11 bağlantıları doğrulanmıştır; diğer pazaryerleri hazırlanmaktadır.',
 'Sektörüm listede yoksa ne olur?': 'Bizimle iletişime geçin. 70 sektör diliyle çalışıyoruz; listede olmayan bir iş kolu için paneldeki terimleri ve ekranları sizinle birlikte uyarlarız.',
 'Eski kayıtlarımı ve ürün listemi taşıyabilir miyim?': 'Ürün listenizi toplu olarak aktarabilirsiniz. Müşteri ve servis kayıtlarınızın taşınması için kurulum görüşmesinde dosya biçiminizi birlikte değerlendiririz.',
 'Verilerim başka firmalarla karışır mı?': 'Hayır. Her firmanın verisi kendi veritabanında ayrı tutulur; başka bir firma sizin kayıtlarınızı göremez.',
 'Deneme süresi bitince ne olur?': 'Deneme süresi bitince bir paket seçersiniz; seçmezseniz hesabınız silinmez, yalnız işlem yapılması durur. Verileriniz size aittir.'}
for q, a in ANS.items():
    body = body.replace('<h3>%s</h3></div>' % q, '<h3>%s</h3><p>%s</p></div>' % (q, a))
open(SRC + '/_body.html', 'w', encoding='utf-8').write(body)
faq = re.findall(r'<div class="q[^"]*"><h3>(.*?)</h3><p>(.*?)</p></div>', body)
ld = [
 {"@context": "https://schema.org", "@type": "Organization", "name": "OnlineKaydet", "url": "https://onlinekaydet.com/", "logo": "https://onlinekaydet.com/logo-renkli-s.png",
  "legalName": "Moda Ekru E-Ticaret Hizmetleri Tekstil Sanayi ve Ticaret Ltd. Şti.", "telephone": "+905444444004", "address": {"@type": "PostalAddress", "addressLocality": "Etimesgut", "addressRegion": "Ankara", "addressCountry": "TR"}},
 {"@context": "https://schema.org", "@type": "WebSite", "name": "OnlineKaydet", "url": "https://onlinekaydet.com/", "inLanguage": "tr"},
 {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "OnlineKaydet", "applicationCategory": "BusinessApplication", "operatingSystem": "Web, Android", "url": "https://onlinekaydet.com/",
  "description": "Web sitesi, e-ticaret, randevu, muhasebe, personel ve iş takibini tek panelde toplayan sektörel işletme yazılımı.",
  "offers": {"@type": "AggregateOffer", "priceCurrency": "TRY", "lowPrice": "990", "highPrice": "5990", "offerCount": "4"}},
 {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": re.sub('<[^>]+>', '', q), "acceptedAnswer": {"@type": "Answer", "text": re.sub('<[^>]+>', '', a)}} for q, a in faq]}]
head = '''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Web Sitesi, E-Ticaret, Randevu ve İş Takip Programı | OnlineKaydet</title>
<meta name="description" content="Hazır tema seçin, mağazanızı açın; randevu, muhasebe, personel ve iş takibini tek panelde yönetin. 70 sektör, e-ticaret ve pazaryeri entegrasyonu. Teklif alın.">
<link rel="canonical" href="https://onlinekaydet.com/"><meta name="robots" content="index,follow,max-image-preview:large">
<meta name="theme-color" content="#0A6847">
<meta property="og:type" content="website"><meta property="og:locale" content="tr_TR"><meta property="og:site_name" content="OnlineKaydet"><meta property="og:url" content="https://onlinekaydet.com/">
<meta property="og:title" content="OnlineKaydet: web siteniz, mağazanız, randevunuz ve iş takibiniz tek yerde"><meta property="og:description" content="Hazır temalar, e-ticaret, randevu, muhasebe ve personel takibi tek panelde. 70 sektör için."><meta property="og:image" content="https://onlinekaydet.com/og-kart.png">
<meta name="twitter:card" content="summary_large_image">
<!-- Google Search Console doğrulaması: <meta name="google-site-verification" content="KOD"> (kod sahipten gelince buraya) -->
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" as="font" type="font/woff2" href="/v9/fonts/bricolage-latin.woff2" crossorigin><link rel="preload" as="font" type="font/woff2" href="/v9/fonts/plex-latin.woff2" crossorigin>
<link rel="stylesheet" href="/v9/v9.css">
<script type="application/ld+json">%s</script></head><body>
<a class="skip" href="#temalar">İçeriğe geç</a>''' % json.dumps(ld, ensure_ascii=False)
tail = '\n<script src="/v9/v9.js" defer></script><script src="/lead.js" defer></script></body></html>'
open(OUT + '/index.html', 'w', encoding='utf-8').write(head + body + tail)
print('görsel', n[0], 'boyut', sum(os.path.getsize(OUT + '/v9/img/' + f) for f in os.listdir(OUT + '/v9/img')) // 1024, 'KB')
