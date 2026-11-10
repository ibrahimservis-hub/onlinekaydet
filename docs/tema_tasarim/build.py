# -*- coding: utf-8 -*-
"""4 sektör için ana sayfa tasarım taslağı (kaydırma animasyonlu). Çıktı: out/<sektor>.html + PNG ekran görüntüleri."""
import os, base64, sys
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, '..', '..', 'themes')
OUT = os.path.join(H, 'out'); os.makedirs(OUT, exist_ok=True)

def font(name, fam, wt):
    p = os.path.join(T, 'fonts', name + '-latin.woff2'); p2 = os.path.join(T, 'fonts', name + '-latin-ext.woff2')
    out = ''
    for q, rng in ((p, 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122'), (p2, 'U+0100-02AF,U+1E00-1EFF,U+2020,U+20A0-20AB,U+20AD-20CF,U+2113,U+2C60-2C7F,U+A720-A7FF')):
        if os.path.exists(q):
            out += "@font-face{font-family:'%s';font-weight:%s;font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2');unicode-range:%s}" % (fam, wt, base64.b64encode(open(q, 'rb').read()).decode(), rng)
    return out

def img(n, w=1600):
    from PIL import Image; import io
    if not n: return ''
    p = os.path.join(T, 'img', n)
    if not os.path.exists(p): return ''
    i = Image.open(p).convert('RGB'); i.thumbnail((w, w)); b = io.BytesIO(); i.save(b, 'JPEG', quality=80)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()

BASE = """
*{box-sizing:border-box;margin:0}html{scroll-behavior:smooth}body{font:400 17px/1.6 var(--fb);background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:inherit;text-decoration:none}.w{max-width:1240px;margin:0 auto;padding:0 40px}
nav{position:fixed;inset:0 0 auto 0;z-index:30;display:flex;align-items:center;justify-content:space-between;padding:20px 40px;transition:background .3s,backdrop-filter .3s}
nav{color:var(--herocol)}nav.s{background:var(--navbg);backdrop-filter:blur(14px);color:var(--ink)}nav .lg{font:var(--lgw) 22px/1 var(--fh);letter-spacing:var(--lgls)}nav ul{display:flex;gap:34px;list-style:none;padding:0;font-size:14px;letter-spacing:.06em;text-transform:uppercase}
.btn{display:inline-flex;align-items:center;gap:10px;padding:16px 28px;background:var(--ac);color:var(--onac);font:600 14px var(--fb);letter-spacing:.08em;text-transform:uppercase;border-radius:var(--rad);border:0;cursor:pointer;transition:transform .25s}.btn:hover{transform:translateY(-2px)}
.btn.o{background:transparent;border:1px solid currentColor;color:inherit}
.hero{position:relative;min-height:100vh;display:flex;align-items:flex-end;overflow:hidden;color:var(--herocol)}
.hero .bg{position:absolute;inset:-10% 0;background-size:cover;background-position:center;transform:scale(1.08);will-change:transform}
.hero:after{content:"";position:absolute;inset:0;background:var(--shade)}
.hero .in{position:relative;z-index:2;padding:140px 40px 70px;width:100%;max-width:1240px;margin:0 auto;display:grid;grid-template-columns:1.5fr 1fr;gap:60px;align-items:end}
.eb{font:600 13px var(--fb);letter-spacing:.2em;text-transform:uppercase;color:var(--ac);display:flex;align-items:center;gap:14px}.hero .eb{color:#fff}.hero .eb:before{background:var(--ac);height:2px}.eb:before{content:"";width:38px;height:1px;background:currentColor}
h1{font:var(--h1w) clamp(48px,6.6vw,104px)/.98 var(--fh);letter-spacing:var(--h1ls);margin:22px 0 28px}h1 em{font-style:italic;color:var(--ac)}
.hero p.lead{font-size:20px;max-width:560px;opacity:.9;margin-bottom:34px}
.card{background:var(--cardbg);color:var(--cardink);padding:30px;border-radius:var(--rad2);box-shadow:0 30px 70px -20px rgba(0,0,0,.45)}
.card h3{font:var(--h2w) 26px/1.1 var(--fh);margin-bottom:6px}.card small{display:block;opacity:.65;margin-bottom:18px;font-size:14px}
.fld{display:grid;gap:12px}.fld label{display:grid;gap:5px;font:600 12px var(--fb);letter-spacing:.08em;text-transform:uppercase;opacity:.75}.fld .i{padding:14px 14px;background:var(--fbg);border:1px solid var(--fbd);border-radius:var(--rad);font:400 16px var(--fb);opacity:1;color:var(--cardink);letter-spacing:0;text-transform:none}.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tick{background:var(--ac);color:var(--onac);overflow:hidden;white-space:nowrap;padding:18px 0;font:var(--h1w) 28px/1 var(--fh);letter-spacing:.02em}.tick div{display:inline-block;animation:mq 40s linear infinite;padding-left:100%}.tick span{margin:0 28px}.tick i{font-style:normal;opacity:.6}
@keyframes mq{to{transform:translateX(-100%)}}
section{padding:130px 0}.h2{font:var(--h2w) clamp(38px,5vw,72px)/1 var(--fh);letter-spacing:var(--h2ls);max-width:900px;margin:18px 0 0}.sub{max-width:560px;opacity:.7;margin-top:22px;font-size:19px}
.svc{margin-top:70px;border-top:1px solid var(--line)}.svc a{display:grid;grid-template-columns:90px 1.1fr 1.4fr 160px 50px;gap:30px;align-items:center;padding:34px 0;border-bottom:1px solid var(--line);transition:padding .35s,background .35s}
.svc a:hover{padding-left:24px;background:var(--hov)}.svc .n{font:500 14px var(--fm);opacity:.5}.svc b{font:var(--h2w) 32px/1.1 var(--fh)}.svc span{opacity:.7;font-size:16px}.svc em{font-style:normal;font-weight:600;color:var(--ac)}.svc .ar{font-size:26px;text-align:right}
.split{display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}.ph{position:relative;aspect-ratio:4/5;border-radius:var(--rad2);overflow:hidden;background:#444}.ph div{position:absolute;inset:-8%;background-size:cover;background-position:center}
.ph.ph2{aspect-ratio:5/4}.tag{position:absolute;left:18px;bottom:18px;background:var(--cardbg);color:var(--cardink);padding:10px 16px;border-radius:99px;font:600 13px var(--fb)}
.steps{display:grid;grid-template-columns:repeat(var(--cols,5),1fr);gap:0;margin-top:70px;counter-reset:s;position:relative}.steps:before{content:"";position:absolute;left:0;right:0;top:27px;height:1px;background:var(--line)}
.st{position:relative;padding-right:26px}.st i{display:grid;place-items:center;width:54px;height:54px;border-radius:50%;background:var(--bg);border:1px solid var(--ac);color:var(--ac);font:600 16px var(--fm);font-style:normal;position:relative;z-index:1}
.st b{display:block;font:var(--h2w) 22px/1.2 var(--fh);margin:22px 0 8px}.st span{font-size:15px;opacity:.7;display:block}
.dark{background:var(--dk);color:var(--dkink)}.dark .sub{opacity:.75}
.big{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);margin-top:70px}.big div{background:var(--dk);padding:46px 34px}.big strong{display:block;font:var(--h1w) 64px/1 var(--fh);color:var(--ac)}.big span{opacity:.75;display:block;margin-top:10px}
.pk{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:70px}.pk .p{border:1px solid var(--line);padding:38px 32px;border-radius:var(--rad2);display:flex;flex-direction:column;gap:14px}.pk .p.f{background:var(--ink);color:var(--bg)}
.pk h4{font:var(--h2w) 26px/1 var(--fh)}.pk .pr{font:var(--h1w) 46px/1 var(--fh)}.pk ul{list-style:none;padding:0;display:grid;gap:10px;font-size:15px;opacity:.85}.pk li:before{content:"→ ";color:var(--ac)}
.faq{max-width:900px;margin-top:60px}.faq div{border-bottom:1px solid var(--line);padding:26px 0;display:flex;justify-content:space-between;gap:30px;font:var(--h2w) 24px/1.25 var(--fh)}.faq i{font-style:normal;color:var(--ac)}
.cta{text-align:center}.cta .h2{margin:20px auto 34px;max-width:1000px}
footer{background:var(--ft);color:var(--ftink);padding:80px 0 40px}footer .g{display:grid;grid-template-columns:1.6fr 1fr 1fr 1fr;gap:50px}footer h5{font:600 12px var(--fb);letter-spacing:.18em;text-transform:uppercase;opacity:.5;margin-bottom:16px}footer p,footer a{display:block;opacity:.8;font-size:15px;margin-bottom:8px}
.cr{border-top:1px solid rgba(255,255,255,.12);margin-top:50px;padding-top:24px;font-size:13px;opacity:.55;display:flex;justify-content:space-between}
.rv{opacity:0;transform:translateY(46px);transition:opacity .9s,transform .9s cubic-bezier(.2,.7,.2,1)}.rv.on{opacity:1;transform:none}
.mbar{display:none}
@media(max-width:900px){.w{padding:0 22px}nav ul{display:none}nav{padding:16px 22px}.hero .in{grid-template-columns:1fr;padding:120px 22px 60px;gap:36px}section{padding:80px 0}.svc a{grid-template-columns:44px 1fr 30px;gap:14px}.svc span,.svc em{display:none}.split,.pk,.big,footer .g{grid-template-columns:1fr;gap:34px}.steps{grid-template-columns:1fr;gap:30px}.steps:before{display:none}.mbar{display:flex;position:fixed;left:12px;right:12px;bottom:12px;z-index:40;gap:8px}.mbar a{flex:1;text-align:center;padding:15px;background:var(--ink);color:var(--bg);border-radius:var(--rad);font:600 14px var(--fb)}.mbar a.p{background:var(--ac);color:var(--onac)}}
"""
JS = """<script>(function(){var n=document.querySelector('nav');function s(){n.classList.toggle('s',scrollY>40);document.querySelectorAll('.hero .bg,.ph div').forEach(function(e){var r=e.parentNode.getBoundingClientRect(),k=(r.top+r.height/2-innerHeight/2)/innerHeight;e.style.transform='translateY('+(k*-60)+'px) scale(1.08)'})}
addEventListener('scroll',s,{passive:true});s();var io=new IntersectionObserver(function(a){a.forEach(function(x){if(x.isIntersecting){x.target.classList.add('on');io.unobserve(x.target)}})},{threshold:.12});document.querySelectorAll('.rv').forEach(function(e){io.observe(e)})})()</script>"""

LOAD = '''<script>(function(){var S=%r;function put(a){document.querySelectorAll('.pp').forEach(function(e){var u=a[Math.min(+e.dataset.i,a.length-1)];if(u){e.style.backgroundImage='url("'+u+'")';e.style.backgroundSize='cover';e.style.backgroundPosition='center';e.style.backgroundRepeat='no-repeat'}})}
if(S.charAt(0)==='/'){put([S+'1.jpg',S+'2.jpg',S+'3.jpg']);return}
fetch('/tema-onizleme/'+S+'.html').then(function(r){return r.text()}).then(function(t){var a=(t.match(/data:image\\/(?:jpeg|webp|png);base64,[A-Za-z0-9+\\/=]{20000,}/g)||[]);if(!a.length)a=(t.match(/\\/[A-Za-z0-9_\\/.~-]+\\.(?:jpg|jpeg|webp)/g)||[]);put(a.slice(0,3))}).catch(function(){})})()</script>'''

def page(c):
    fonts = ''.join(font(*f) for f in c['fonts'])
    svc = ''.join('<a href="#"><span class="n">%02d</span><b>%s</b><span>%s</span><em>%s</em><span class="ar">→</span></a>' % (i + 1, a, b, p) for i, (a, b, p) in enumerate(c['svc']))
    steps = ''.join('<div class="st rv" style="transition-delay:%dms"><i>%d</i><b>%s</b><span>%s</span></div>' % (i * 90, i + 1, a, b) for i, (a, b) in enumerate(c['steps']))
    form = ''.join(('<div class="g2">%s</div>' % ''.join('<label>%s<div class="i">%s</div></label>' % x for x in r)) if isinstance(r, list) else '<label>%s<div class="i">%s</div></label>' % r for r in c['form'])
    big = ''.join('<div><strong>%s</strong><span>%s</span></div>' % x for x in c['big'])
    pk = ''.join('<div class="p%s"><h4>%s</h4><div class="pr">%s</div><span style="opacity:.7">%s</span><ul>%s</ul><a class="btn%s" href="#">%s</a></div>' % (' f' if p[4] else '', p[0], p[1], p[2], ''.join('<li>%s</li>' % x for x in p[3]), '' if p[4] else ' o', c['cta']) for p in c['pk'])
    faq = ''.join('<div>%s<i>+</i></div>' % q for q in c['faq'])
    tick = ''.join('<span>%s</span><span><i>✦</i></span>' % t for t in c['tick'] * 2)
    ph = lambda n: '<div class="pp" data-i="%d" style="background:linear-gradient(160deg,#2a2f38,#12151a)"></div>' % n
    herobg = "background:linear-gradient(150deg,#2a2f38,#0d0f12 70%)"
    nav = ''.join('<li>%s</li>' % x for x in c['nav'])
    return """<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%(name)s</title><style>%(fonts)s:root{%(vars)s}%(base)s</style></head><body>
<nav><div class="lg">%(name)s</div><ul>%(nav)s</ul><a class="btn" href="#">%(cta)s</a></nav>
<header class="hero"><div class="bg pp" data-i="0" style="%(herobg)s"></div><div class="in"><div><div class="eb">%(eb)s</div><h1>%(h1)s</h1><p class="lead">%(lead)s</p><a class="btn" href="#">%(cta)s →</a> &nbsp; <a class="btn o" href="#">%(cta2)s</a></div>
<div class="card rv on"><h3>%(ft)s</h3><small>%(fs)s</small><div class="fld">%(form)s</div><a class="btn" style="margin-top:16px;width:100%%;justify-content:center" href="#">%(cta)s</a></div></div></header>
<div class="tick"><div>%(tick)s</div></div>
<section><div class="w"><div class="eb rv">%(s1e)s</div><h2 class="h2 rv">%(s1h)s</h2><p class="sub rv">%(s1s)s</p><div class="svc rv">%(svc)s</div></div></section>
<section class="dark"><div class="w split"><div class="ph rv">%(p2)s<span class="tag">%(tag2)s</span></div><div><div class="eb rv">%(s2e)s</div><h2 class="h2 rv">%(s2h)s</h2><p class="sub rv">%(s2s)s</p><div class="big rv" style="grid-template-columns:1fr;margin-top:40px">%(big)s</div></div></div></section>
<section><div class="w"><div class="eb rv">%(s3e)s</div><h2 class="h2 rv">%(s3h)s</h2><p class="sub rv">%(s3s)s</p><div class="steps" style="--cols:%(nst)d">%(steps)s</div></div></section>
<section class="dark"><div class="w"><div class="eb rv">%(s4e)s</div><h2 class="h2 rv">%(s4h)s</h2><div class="pk rv" style="--line:rgba(255,255,255,.18)">%(pk)s</div></div></section>
<section><div class="w split"><div><div class="eb rv">%(s5e)s</div><h2 class="h2 rv">%(s5h)s</h2><div class="faq rv">%(faq)s</div></div><div class="ph ph2 rv">%(p3)s<span class="tag">%(tag3)s</span></div></div></section>
<section class="dark cta"><div class="w"><div class="eb rv" style="justify-content:center">%(s6e)s</div><h2 class="h2 rv">%(s6h)s</h2><a class="btn rv" href="#">%(cta)s →</a></div></section>
<footer><div class="w"><div class="g"><div><div style="font:var(--h1w) 30px var(--fh);margin-bottom:14px">%(name)s</div><p>%(addr)s</p><p style="font:600 22px var(--fb);opacity:1">%(tel)s</p></div><div><h5>Sayfalar</h5>%(fl)s</div><div><h5>İletişim</h5><p>%(hrs)s</p></div><div><h5>Yasal</h5><a href="#">KVKK</a><a href="#">Gizlilik</a></div></div><div class="cr"><span>© 2026 %(name)s</span><span>OnlineKaydet ile yayınlanır</span></div></div></footer>
<div class="mbar"><a href="tel:">Ara</a><a class="p" href="#">%(cta)s</a></div>%(js)s</body></html>""" % dict(
        c, fonts=fonts, base=BASE, nav=nav, herobg=herobg, form=form, big=big, pk=pk, faq=faq, tick=tick, svc=svc, steps=steps, nst=len(c['steps']),
        p2=ph(1), p3=ph(2), fl=''.join('<a href="#">%s</a>' % x for x in c['nav']), js=JS + LOAD % c['src'])

KUAFOR = dict(
    name='Atölye Saç', src='n13-lux-kuafor', fonts=[('fraunces', 'Fraunces', '100 900'), ('manrope', 'Manrope', '200 800')],
    vars="--fh:'Fraunces',serif;--fb:'Manrope',sans-serif;--fm:'Manrope',sans-serif;--bg:#f4ede3;--ink:#1c1612;--ac:#b4572e;--onac:#fff;--navbg:rgba(244,237,227,.88);--lgw:600;--lgls:-.01em;--rad:2px;--rad2:4px;--h1w:500;--h1ls:-.03em;--h2w:500;--h2ls:-.02em;--herocol:#fff;--shade:linear-gradient(180deg,rgba(20,12,8,.35),rgba(20,12,8,.78));--cardbg:#f4ede3;--cardink:#1c1612;--fbg:#fff;--fbd:#d9ccb9;--line:rgba(28,22,18,.18);--hov:rgba(180,87,46,.07);--dk:#1c1612;--dkink:#f4ede3;--ft:#120d0a;--ftink:#f4ede3",
    nav=['Hizmetler', 'Uzmanlar', 'Süreç', 'Paketler', 'Sıkça sorulanlar'], cta='Randevu al', cta2='Hizmetleri gör',
    hero='kuafor.jpg', eb='Çankaya · Ankara · Randevulu salon', h1='Saçınıza <em>zaman</em> ayıran salon.', lead='Hizmeti seçin, uzmanınızı ve saatinizi belirleyin. Randevunuz alınır, bir gün önce hatırlatma mesajı gelir.',
    ft='Hızlı randevu', fs='Salonumuza uygun saatleri birkaç adımda ayırtın.',
    form=[('Ad soyad', 'Ayşe Yılmaz'), [('Telefon', '05xx xxx xx xx'), ('Uzman', 'Fark etmez ▾')], ('Hizmet', 'Kesim + fön ▾'), [('Tarih', '14 Kasım Cuma'), ('Saat', '14:30 ▾')]],
    tick=['Kesim', 'Boya', 'Balyaj', 'Keratin bakım', 'Gelin saçı', 'Erkek kesim', 'Sakal tıraşı'],
    s1e='Hizmetler', s1h='Ne yaptırmak istersiniz?', s1s='Süre ve fiyat aralığı önceden yazılı; randevuda sürpriz yok.',
    svc=[('Kesim ve fön', 'Saç tipine göre kesim, yıkama ve fön', '450 ₺ – 900 ₺'), ('Boya ve balyaj', 'Renk danışmanlığı, koruyucu bakım dahil', '1.800 ₺ – 4.500 ₺'), ('Keratin ve bakım', 'Kalıcı düzleştirme, yoğun onarım', '1.500 ₺ – 3.200 ₺'), ('Gelin saçı', 'Deneme randevusu ve düğün günü hizmeti', '3.500 ₺ – 6.000 ₺'), ('Erkek kesim ve sakal', 'Makine, makas ve ustura tıraşı', '350 ₺ – 600 ₺')],
    s2e='Uzmanlarımız', s2h='Her koltukta aynı özen.', s2s='Uzmanınızı kendiniz seçin; geçmiş işlemleriniz, kullanılan renk ve ürün notlarınız salonda kayıtlı kalır.',
    big=[('6', 'uzman, kendi uzmanlık alanıyla'), ('3 alan', 'saç, cilt ve tırnak bakımı'), ('Günlük', 'randevu defteri, hatırlatma mesajlı')],
    p2='kuafor2.jpg', tag2='Fotoğraf: salon çalışması', p3='kuafor3.jpg', tag3='Önce / sonra galerisi',
    s3e='Randevu süreci', s3h='Randevudan ödemeye, dört adım.', s3s='Bu adımların aynısı salonun yönetim panelinde de görünür; durum değiştikçe size mesaj gider.',
    steps=[('Randevu alındı', 'Formu doldurursunuz, kaydınız oluşur.'), ('Onaylandı', 'Uzmanınız ve saatiniz netleşir; hatırlatma gider.'), ('İşlemde', 'Koltuğunuz hazır, işlem başlar.'), ('Tamamlandı', 'Yapılan işlem ve ürünler kaydedilir.'), ('Ödendi', 'Nakit, kart ya da havale; fişiniz hazır.')],
    s4e='Paketler', s4h='Düzenli gelenlere özel paketler.',
    pk=[('Tek seans', '450 ₺', 'Tek seferlik hizmet', ['Uzman seçimi', 'Hatırlatma mesajı', 'İşlem notu'], 0), ('Aylık bakım', '1.600 ₺', '4 seans · her ay', ['Öncelikli saat', 'Ürün indirimi %10', 'Seans takibi'], 1), ('Gelin paketi', '5.500 ₺', 'Deneme + düğün günü', ['Deneme randevusu', 'Gün içi yerinde hizmet', 'Yazılı program'], 0)],
    s5e='Sıkça sorulanlar', s5h='Randevu öncesi merak edilenler.', faq=['Randevumu nasıl iptal ederim?', 'Rengi önceden danışabilir miyim?', 'Hangi ödeme yöntemleri geçerli?', 'Çocuk kesimi yapıyor musunuz?'],
    s6e='Randevu', s6h='Haftaya bir koltuk ayıralım mı?', addr='Atatürk Bulvarı No:112, Çankaya / Ankara', tel='0312 000 00 00', hrs='Salı–Cumartesi 10:00–20:00 · Pazar 11:00–17:00')

CEKICI = dict(
    name='HIZIR YOL YARDIM', src='n07-cine-oto-cekici', fonts=[('archivoblack', 'Archivo Black', '400'), ('barlow', 'Barlow', '300 700')],
    vars="--fh:'Archivo Black',sans-serif;--fb:'Barlow',sans-serif;--fm:'Barlow',sans-serif;--bg:#0f1215;--ink:#f3f1ea;--ac:#ffc21a;--onac:#111;--navbg:rgba(15,18,21,.9);--lgw:400;--lgls:.02em;--rad:0;--rad2:0;--h1w:400;--h1ls:-.02em;--h2w:400;--h2ls:-.01em;--herocol:#fff;--shade:linear-gradient(90deg,rgba(8,10,12,.92) 0%,rgba(8,10,12,.55) 60%,rgba(8,10,12,.3));--cardbg:#ffc21a;--cardink:#111;--fbg:#fff;--fbd:#111;--line:rgba(243,241,234,.2);--hov:rgba(255,194,26,.07);--dk:#181c20;--dkink:#f3f1ea;--ft:#07090b;--ftink:#f3f1ea",
    nav=['Hizmetler', 'Kapsama', 'Süreç', 'Fiyatlar', 'SSS'], cta='Çekici çağır', cta2='Fiyatları gör',
    hero='oto_cekici.jpg', eb='7/24 · Ankara ve çevre iller', h1='Yoldaysanız <em>arayın.</em>', lead='Konumunuzu bırakın, en yakın çekici yola çıksın. Fiyat çağrıda yazılı bildirilir; teslimde ödeme alınır.',
    ft='Hızlı çağrı', fs='Konumunuz ve aracınız yeterli; dönüş dakikalar içinde.',
    form=[('Konum', 'Eskişehir Yolu 12. km, Ankara'), [('Telefon', '05xx xxx xx xx'), ('Araç tipi', 'Otomobil ▾')], ('Sorun', 'Çalışmıyor · yolda kaldı ▾'), ('Gideceği yer', 'Çankaya, yetkili servis')],
    tick=['Kaza çekici', 'Arıza çekici', 'Yol yardım', 'Akü takviye', 'Lastik yardımı', 'Şehirlerarası taşıma'],
    s1e='Hizmetler', s1h='Aracınız nerede, ne oldu?', s1s='Kilometre ve araç tipine göre net fiyat; çağrıda yazılı verilir.',
    svc=[('Kaza çekici', 'Hasarlı araç, kasalı kamyon ile güvenli yükleme', 'Açılış 600 ₺ + km'), ('Arıza çekici', 'Çalışmayan araç, servise ya da eve taşıma', 'Açılış 500 ₺ + km'), ('Yol yardım', 'Akü takviye, lastik değişimi, yakıt', '300 ₺ – 500 ₺'), ('Şehirlerarası taşıma', 'Araç nakli, sigortalı taşıma', 'Km ücretiyle'), ('Ağır vasıta', 'Minibüs ve kamyon için vinçli çekici', 'Teklifle')],
    s2e='Filomuz', s2h='Kasalı, vinçli, her araca uygun.', s2s='Araç tipinize göre doğru çekici gönderilir; konumunuz canlı izlenir, şoförün arama numarası SMS ile size iletilir.',
    big=[('12', 'çekici ve kayar kasa aracı'), ('7/24', 'çağrı hattı ve sevk'), ('Sigortalı', 'her taşıma kayıtlı ve belgeli')],
    p2='oto_cekici2.jpg', tag2='Fotoğraf: yükleme anı', p3='oto_cekici3.jpg', tag3='Teslimde fotoğraflı tutanak',
    s3e='Çağrı süreci', s3h='Çağrıdan teslimata, beş adım.', s3s='Bu adımların aynısı yönetim panelinde de görünür; her adımda size SMS gider.',
    steps=[('Çağrı alındı', 'Konum ve araç bilgisi kayda geçer.'), ('Yola çıktı', 'Şoför atanır, tahmini varış bildirilir.'), ('Yükleme', 'Araç fotoğraflanır, tutanak imzalanır.'), ('Taşıma', 'Canlı konumla hedefe gidilir.'), ('Teslim', 'Ödeme alınır, belge verilir.')],
    s4e='Fiyatlar', s4h='Önceden bilirsiniz.',
    pk=[('Şehir içi', '500 ₺', 'Açılış + 20 km dahil', ['Fotoğraflı tutanak', 'SMS bildirimi', 'Sigortalı taşıma'], 0), ('Şehirlerarası', '18 ₺/km', 'Km başına', ['Sigortalı taşıma', 'Canlı konum', 'Yazılı sözleşme'], 1), ('Kurumsal', 'Teklif', 'Filolar için', ['Aylık fatura', 'Öncelikli sevk', 'Özel hat'], 0)],
    s5e='Sıkça sorulanlar', s5h='Yoldayken en çok sorulanlar.', faq=['Çekici ne kadar sürede gelir?', 'Fiyat nasıl hesaplanıyor?', 'Kaza tutanağında yardımcı olur musunuz?', 'Kart ile ödeme alıyor musunuz?'],
    s6e='Şimdi', s6h='Yolda kaldınız mı? Biz yoldayız.', addr='Eskişehir Yolu Sanayi Sitesi, Ankara', tel='0544 000 00 00', hrs='7 gün 24 saat açık')

AVUKAT = dict(
    name='Aksoy Hukuk', src='n91-lux-avukat', fonts=[('dmserif', 'DM Serif Display', '400'), ('figtree', 'Figtree', '300 800')],
    vars="--fh:'DM Serif Display',serif;--fb:'Figtree',sans-serif;--fm:'Figtree',sans-serif;--bg:#f6f2ea;--ink:#0f1d33;--ac:#a8803f;--onac:#fff;--navbg:rgba(246,242,234,.9);--lgw:400;--lgls:0;--rad:0;--rad2:0;--h1w:400;--h1ls:-.015em;--h2w:400;--h2ls:-.01em;--herocol:#fff;--shade:linear-gradient(180deg,rgba(10,18,34,.15),rgba(10,18,34,.78));--cardbg:#f6f2ea;--cardink:#0f1d33;--fbg:#fff;--fbd:#d8cdb6;--line:rgba(15,29,51,.18);--hov:rgba(168,128,63,.08);--dk:#0f1d33;--dkink:#f6f2ea;--ft:#08111f;--ftink:#f6f2ea",
    nav=['Çalışma alanları', 'Ekip', 'Süreç', 'Ücretlendirme', 'SSS'], cta='Görüşme planla', cta2='Alanlarımız',
    hero=None, eb='Ankara · Bireysel ve kurumsal hukuk', h1='Hakkınızı <em>doğru</em> anlatan avukat.', lead='İlk görüşmede durumunuzu dinler, izlenecek yolu ve tahmini süreyi yazılı olarak paylaşırız.',
    ft='Ön görüşme talebi', fs='Dosyanızı özetleyin; aynı gün sizi arayalım.',
    form=[('Ad soyad', 'Mehmet Demir'), [('Telefon', '05xx xxx xx xx'), ('Dosya türü', 'İş hukuku ▾')], ('Kısaca durumunuz', 'İşten çıkarıldım, tazminat…'), [('Tercih edilen gün', 'Perşembe'), ('Görüşme', 'Ofiste · Telefonda ▾')]],
    tick=['İş hukuku', 'Aile hukuku', 'Ceza hukuku', 'Ticaret hukuku', 'Gayrimenkul', 'İcra ve iflas'],
    s1e='Çalışma alanları', s1h='Hangi konuda destek arıyorsunuz?', s1s='Her dosya için baştan yazılı kapsam ve ücret planı sunulur.',
    svc=[('İş hukuku', 'İşe iade, kıdem ve ihbar tazminatı, mobbing', 'Ücret planı yazılı'), ('Aile hukuku', 'Boşanma, velayet, nafaka, mal paylaşımı', 'Ücret planı yazılı'), ('Ceza hukuku', 'Soruşturma ve kovuşturma aşamasında savunma', 'Dosyaya göre'), ('Ticaret hukuku', 'Sözleşmeler, şirket işlemleri, alacak tahsili', 'Aylık danışmanlık'), ('Gayrimenkul', 'Tapu, kira, kat mülkiyeti uyuşmazlıkları', 'Ücret planı yazılı')],
    s2e='Ekibimiz', s2h='Dosyanızı baştan sona aynı avukat yürütür.', s2s='Dosyanızın durumunu aradığınızda sizi bilgilendiren, duruşma öncesi hatırlatan bir yapı kurduk. Belgelerinizi güvenli şekilde yükler, ilerlemeyi takip edersiniz.',
    big=[('15 yıl', 'ortak çalışma deneyimi'), ('Yazılı', 'her dosya için kapsam ve ücret'), ('Gizli', 'avukat–müvekkil sırrı, güvenli belge alanı')],
    p2=None, tag2='Gerçek ofis fotoğrafı (Pexels) buraya gelir', p3=None, tag3='Gerçek ofis fotoğrafı (Pexels) buraya gelir',
    s3e='Dosya süreci', s3h='İlk görüşmeden karara, beş adım.', s3s='Bu adımların aynısı yönetim panelinde dosya durumu olarak görünür; her aşamada bilgilendirilirsiniz.',
    steps=[('Başvuru alındı', 'Talebiniz dosya olarak kaydedilir.'), ('Ön görüşme', 'Durum dinlenir, yol haritası çıkar.'), ('Vekalet ve belgeler', 'Sözleşme imzalanır, belgeler yüklenir.'), ('Dosya yürütme', 'Dilekçe, duruşma, hatırlatmalar.'), ('Sonuç ve kapanış', 'Karar bildirilir, hesap kapatılır.')],
    s4e='Ücretlendirme', s4h='Başlamadan bilirsiniz.',
    pk=[('Ön görüşme', '1.500 ₺', '45 dakika', ['Durum değerlendirmesi', 'Yazılı özet', 'Ücret planı'], 0), ('Dosya takibi', 'Plan', 'Konuya göre', ['Dilekçe ve duruşma', 'Duruşma hatırlatma', 'Belge alanı'], 1), ('Kurumsal danışmanlık', 'Aylık', 'Şirketler için', ['Sözleşme incelemesi', 'Öncelikli hat', 'Aylık rapor'], 0)],
    s5e='Sıkça sorulanlar', s5h='İlk görüşme öncesi merak edilenler.', faq=['İlk görüşme ücretli mi?', 'Dosyamın durumunu nereden takip ederim?', 'Belgelerim güvende mi?', 'Ücret nasıl belirleniyor?'],
    s6e='Görüşme', s6h='Önce dinleyelim, sonra planlayalım.', addr='Kızılay Mah. Atatürk Blv. No:24 Kat:6, Çankaya / Ankara', tel='0312 000 00 00', hrs='Hafta içi 09:30–18:30 · Cumartesi randevuyla')

ETICARET = dict(
    name='Moda Ekru', src='/tema-urun/giyim', fonts=[('bricolage', 'Bricolage Grotesque', '200 800'), ('manrope', 'Manrope', '200 800')],
    vars="--fh:'Bricolage Grotesque',sans-serif;--fb:'Manrope',sans-serif;--fm:'Manrope',sans-serif;--bg:#faf8f4;--ink:#161513;--ac:#c4492b;--onac:#fff;--navbg:rgba(250,248,244,.9);--lgw:700;--lgls:-.02em;--rad:999px;--rad2:20px;--h1w:700;--h1ls:-.04em;--h2w:600;--h2ls:-.03em;--herocol:#fff;--shade:linear-gradient(180deg,rgba(0,0,0,.1),rgba(0,0,0,.65));--cardbg:#fff;--cardink:#161513;--fbg:#faf8f4;--fbd:#e3ddd0;--line:rgba(22,21,19,.14);--hov:rgba(196,73,43,.06);--dk:#161513;--dkink:#faf8f4;--ft:#0d0c0b;--ftink:#faf8f4",
    nav=['Kadın', 'Erkek', 'Yeni gelenler', 'İndirim', 'Hesabım'], cta='Alışverişe başla', cta2='Yeni gelenler',
    hero='eticaret.jpg', eb='Yeni sezon · Ücretsiz kargo 1.500 ₺ üzeri', h1='Her gün <em>giyilen</em> parçalar.', lead='Doğal kumaşlar, net ölçü tablosu, 14 gün koşulsuz iade. Siparişiniz hazırlandığında kargo takip numarası mesajla gelir.',
    ft='Sepetiniz', fs='Üç ürün · ücretsiz kargoya 320 ₺ kaldı',
    form=[('Keten gömlek · M · Ekru', '1.290 ₺'), ('Pamuklu pantolon · 38 · Siyah', '1.490 ₺'), [('Kargo', 'Ücretsiz'), ('Ödeme', 'Kart · Havale ▾')], ('Toplam', '2.780 ₺')],
    tick=['Yeni sezon', 'Keten', 'Pamuk', 'Ücretsiz iade', 'Aynı gün kargo', 'Güvenli ödeme'],
    s1e='Koleksiyon', s1h='Kategoriye göre keşfedin.', s1s='Her ürün sayfasında beden tablosu, kumaş bilgisi ve stok durumu görünür.',
    svc=[('Gömlek ve bluz', 'Keten, pamuk, viskon; S–XXL', '590 ₺ – 1.490 ₺'), ('Pantolon ve etek', 'Yüksek bel, geniş paça, klasik kesim', '790 ₺ – 1.790 ₺'), ('Elbise', 'Günlük ve davet, ölçü tablosuyla', '990 ₺ – 2.490 ₺'), ('Dış giyim', 'Mevsimlik ceket, trençkot', '1.490 ₺ – 3.490 ₺'), ('Aksesuar', 'Eşarp, kemer, çanta', '190 ₺ – 890 ₺')],
    s2e='Alışveriş güvencesi', s2h='Almadan önce bilirsiniz.', s2s='Sipariş durumunuz ve kargonuz hesabınızdan izlenir; her adımda SMS ve e-posta ile haber verilir.',
    big=[('14 gün', 'koşulsuz iade'), ('Aynı gün', 'kargo, 15:00 öncesi siparişlerde'), ('3D Secure', 'güvenli kart ödemesi, havale seçeneği')],
    p2='eticaret2.jpg', tag2='Fotoğraf: yeni sezon', p3='eticaret3.jpg', tag3='Gerçek ürün fotoğrafları',
    s3e='Sipariş süreci', s3h='Sepetten kapıya, beş adım.', s3s='Bu adımların aynısı yönetim panelinde sipariş durumu olarak görünür.',
    steps=[('Sipariş alındı', 'Ödemeniz doğrulanır.'), ('Hazırlanıyor', 'Ürünler paketlenir, stoktan düşer.'), ('Kargoda', 'Takip numarası mesajla gelir.'), ('Teslim edildi', 'Paketiniz size ulaşır.'), ('İade / değişim', '14 gün içinde tek adımda.')],
    s4e='Kampanyalar', s4h='Sepete özel avantajlar.',
    pk=[('Hoş geldin', '%10', 'İlk siparişte', ['Kayıtta otomatik kupon', 'Tüm ürünlerde geçerli', 'Kargo ücretsiz'], 0), ('Sezon sonu', '%30', 'Seçili ürünlerde', ['Stok bitene kadar', 'Beden değişimi açık', 'Aynı gün kargo'], 1), ('Üçlü paket', '3 al 2 öde', 'Tişört ve gömlek', ['Sepete otomatik uygulanır', 'İade serbest', 'Hediye paketi'], 0)],
    s5e='Sıkça sorulanlar', s5h='Alışveriş öncesi merak edilenler.', faq=['Beden tablosunu nereden görürüm?', 'İade nasıl yapılır?', 'Kargo ne kadar sürede gelir?', 'Havale ile ödeme yapabilir miyim?'],
    s6e='Yeni sezon', s6h='Gardırobunuza yeni bir başlangıç.', addr='Etimesgut / Ankara · Moda Ekru Tekstil', tel='0544 000 00 00', hrs='Hafta içi 09:00–18:00 · Müşteri hattı')

if __name__ == '__main__':
    for k, c in (('kuafor', KUAFOR), ('cekici', CEKICI), ('avukat', AVUKAT), ('eticaret', ETICARET)):
        open(os.path.join(OUT, k + '.html'), 'w', encoding='utf-8').write(page(c)); print(k)
