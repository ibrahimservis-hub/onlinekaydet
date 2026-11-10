# -*- coding: utf-8 -*-
"""61 yeni sektör için sayfa: sektor-kombi.html iskeleti + panel/sektor_ek.py verisi (sayı/ödül/müşteri sayısı yazılmaz)."""
import re, sys, html, json
sys.path.insert(0, '../../panel')
import sektor_ek as S
import sektor_cok as C
E = html.escape
T = open('sektor-kombi.html', encoding='utf-8').read()
a = T.index('<main id="icerik">') + len('<main id="icerik">'); b = T.index('</main>')
HEAD0, TAIL = T[:a], T[b:]
OLD = open('gen_sektor_ek.py', encoding='utf-8').read()
ICON = re.search(r"ICON='(.*?)'\nHEAD=", OLD, re.S).group(1)
HEAD0 = HEAD0.replace('<symbol id="i-kombi"', ICON + '<symbol id="i-kombi"', 1)
ARCH = {"randevu": "online randevu ve müşteri takip programı", "kurs": "kayıt, ders programı ve ödeme takip programı",
        "ilan": "ilan, talep ve yer gösterme takip programı", "menu": "sipariş, rezervasyon ve müşteri takip programı",
        "cekim": "çekim planı ve müşteri takip programı", "servis": "iş planı ve müşteri takip programı"}
KEYS = list(C.S.keys())
ALL16 = [('kombi', 'Kombi'), ('klima', 'Klima'), ('beyaz-esya', 'Beyaz eşya'), ('elektronik', 'Elektronik'), ('bilgisayar', 'Bilgisayar'), ('tesisat', 'Tesisat'), ('elektrik', 'Elektrik'), ('guvenlik', 'Güvenlik'),
         ('oto-servis', 'Oto servis'), ('oto-cekici', 'Oto çekici'), ('kuafor', 'Kuaför ve berber'), ('nakliye', 'Nakliye'), ('tekstil', 'Tekstil'), ('e-ticaret', 'E-ticaret'), ('temizlik', 'Temizlik'), ('guzellik', 'Güzellik merkezi')]
NEWS = [(k.replace('_', '-'), S.NEW[k]['name']) for k in KEYS]
ALLSEC = ALL16 + NEWS
OPTS = '<option>Seçiniz</option>' + ''.join('<option>%s</option>' % E(n) for _, n in sorted(ALLSEC, key=lambda x: x[1])) + '<option>Diğer</option>'


def chips(xs):
    return '<div class="chp">' + ''.join('<span>%s</span>' % E(x) for x in xs) + '</div>'


def build(key, idx):
    d = S.NEW[key]; spec = C.S[key]
    slug = key.replace('_', '-'); short = d['name']
    sv = d['site']['services']; fq = d['site']['faq']
    brands = list(d['brands'])
    terms = [(k, v) for k, v in d['terms'].items() if k != v][:6]
    h1 = '%s için %s' % (short, ARCH.get(spec.get('arche'), ARCH['servis']))
    lead = '%s işletmeniz için %s. Kayıt, müşteri kartı ve hatırlatma tek panelde; sitenizi hazır temayla yayınlayın.' % (short, spec.get('tag', 'iş takibi'))
    ticks = [t for t, _ in sv[:3]]
    lab, val, fault = 'Müşteri', 'Örnek kayıt', (d['faults'][0] if d['faults'] else 'Görüşme')
    rel = [(s, n) for s, n in ALLSEC if s != slug]
    off = (idx * 7) % len(rel)
    rel = (rel[off:] + rel[:off])[:12]
    m = ('<div class="pgh sk"><div class="w"><div><nav class="crumb" aria-label="Sayfa yolu"><a href="index.html">Ana sayfa</a> / <a href="sektorler.html">Sektörler</a> / %s</nav><h1>%s</h1><p>%s</p><ul class="ticks">%s</ul>'
         '<div class="ctas"><a class="pill" href="#kayit">Ücretsiz Dene</a><a class="pill gh" href="demo.html">Demoyu gör</a></div></div>'
         '<div class="skv"><svg class="skic" aria-hidden="true"><use href="#i-isl"/></svg><div class="fis"><div class="top"><span>%s</span><span>%s</span></div><dl><dt>%s</dt><dd>%s</dd><dt>Konu</dt><dd>%s</dd></dl>'
         '<div class="ln"><time>1</time><span>Kayıt açıldı</span></div><div class="ln"><time>2</time><span>Ekip atandı, müşteriye SMS gitti</span></div><div class="ln"><time>3</time><span>İşlem tamamlandı</span></div></div></div></div></div>'
         % (E(short), E(h1), E(lead), ''.join('<li>%s</li>' % E(t) for t in ticks), E(d['pdf_title'].title()), E(short) + ' · örnek', E(lab), E(val), E(fault)))
    m += '<section class="bnd pb"><div class="w"><div class="sh one"><h2>%s işletmesi için hazır gelenler</h2></div><div class="fgrid">%s</div></div></section>' % (E(short), ''.join('<div><h3>%s</h3><p>%s</p></div>' % (E(t), E(x)) for t, x in sv[:3]))
    m += ('<section class="bnd tint"><div class="w"><div class="sh one"><h2>%s için kurulu başlar</h2></div><div class="set sk2"><div><h3>Hizmet ve katalog</h3>%s<h3 style="margin-top:28px">Sık talepler</h3>%s</div>'
          '<div><h3>Kontrol listesi</h3><ul class="ticks">%s</ul><p class="note2">Maddeleri panelden değiştirebilirsiniz.</p>%s</div></div></div></section>'
          % (E(short), chips([t for t, _ in sv] + brands[:4]), chips(d['faults'][:7]), ''.join('<li>%s</li>' % E(c[0]) for c in d['checklist']),
             ('<h3 style="margin-top:28px">Panelde sizin dilinizle</h3>' + chips(['%s → %s' % (k, v) for k, v in terms[:4]])) if terms else ''))
    m += ('<section class="ctab"><div class="w"><div class="cta2"><div><h2>%s için Profesyonel</h2><p>Otomatik SMS, kasa takibi ve raporlar dahil. Yeni müşteri için Tam Paket\'teki web sitesini de ekleyebilirsiniz.</p></div>'
          '<a class="pill" href="fiyatlar.html">Paketleri incele</a></div></div></section>' % E(short))
    m += '<section id="sss" class="tint"><div class="w"><div class="sss"><h2>Sık sorulan sorular</h2><div>%s</div></div></div></section>' % ''.join('<details%s><summary>%s</summary><p>%s</p></details>' % (' open' if i == 0 else '', E(q), E(a)) for i, (q, a) in enumerate(fq))
    m += '<section class="bnd oth"><div class="w"><div class="sh one"><h2>Diğer sektörler</h2></div><div class="chp rel">%s<a href="sektorler.html">Tüm sektörler</a></div></div></section>' % ''.join('<a href="sektor-%s.html">%s</a>' % (s, E(n)) for s, n in rel)
    m += ('<section id="kayit" class="dkk"><div class="w"><div class="fc"><div><h2>%s işletmenizi dijitale taşıyın</h2><p>Formu doldurun, uzmanımız sektörünüze göre kurulumu birlikte planlasın. İlk ay ücretsiz.</p><a class="big" href="tel:05444444004">0544 444 40 04</a></div> '
          '<div class="frm"><div><label for="f1">Ad soyad</label><input id="f1" autocomplete="name"></div><div><label for="f2">Telefon</label><input id="f2" type="tel" autocomplete="tel"></div><div><label for="f3">Firma adı</label><input id="f3" autocomplete="organization"></div>'
          '<div><label for="f4">Sektör</label><select id="f4">%s</select></div><a class="bt" href="#">Beni arayın</a><small>Bilgileriniz yalnızca sizinle iletişim için kullanılır (KVKK).</small></div></div></div></section>' % (E(short), OPTS))
    title = h1[0].upper() + h1[1:]
    head = HEAD0.replace('sektor-kombi.html', 'sektor-%s.html' % slug)
    head = head.replace('Kombi Servisi Takip Programı | OnlineKaydet', E(title) + ' | OnlineKaydet')
    head = head.replace('Kombi servisleri için servis kaydı, bakım hatırlatma, usta atama, imzalı servis fişi ve müşteriye SMS. Marka ve model listesi hazır.', E(lead))
    head = head.replace('OnlineKaydet — Kombi servisleri için servis takip programı', 'OnlineKaydet — %s için takip programı' % E(short))
    head = head.replace('Kombi servisleri için servis kaydı, bakım hat', E(lead)[:0] + 'Kayıt, müşteri kartı ve hat')
    head = head.replace('<a href="sektor-%s.html" aria-current="page"><b>Kombi</b></a>' % slug, '<a href="sektor-kombi.html"><b>Kombi</b></a>')
    head = head.replace('aria-current="page"', '')
    def _ld(mm):
        g = json.loads(mm.group(1))
        for it in g.get("@graph", []):
            if it.get("@type") == "FAQPage":
                it["mainEntity"] = [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}} for q, ans in fq]
            elif it.get("@type") == "SoftwareApplication":
                it["name"] = "OnlineKaydet — %s için takip programı" % short
                it["description"] = lead
                it["url"] = "https://onlinekaydet.com/sektor-%s.html" % slug
        return '<script type="application/ld+json">' + json.dumps(g, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    head, nfaq = re.subn(r'<script type="application/ld\+json">(.*?)</script>', _ld, head, count=1, flags=re.S)
    assert nfaq == 1, key
    page = head + m + TAIL
    open('sektor-%s.html' % slug, 'w', encoding='utf-8').write(page)
    return slug, short


out = [build(k, i) for i, k in enumerate(KEYS)]
# sektorler.html: tüm yeni sektörler için ek bölüm (yeniden çalıştırınca tekrarlanmaz)
f = 'sektorler.html'; h = open(f, encoding='utf-8').read()
h = re.sub(r'<section class="sekw" id="digerleri">.*?</section>', '', h, flags=re.S)
sec = ('<section class="sekw" id="digerleri"><div class="w"><div class="sh one"><h2>Diğer sektörler</h2><p>Randevu, kurs, ilan, rezervasyon ve çekim gibi iş akışları için hazır kurulum.</p></div><div class="chp rel">%s</div></div></section>'
       % ''.join('<a href="sektor-%s.html">%s</a>' % (s, E(n)) for s, n in out))
h = h.replace('</main>', sec + '</main>', 1)
open(f, 'w', encoding='utf-8').write(h)
json.dump([s for s, _ in out], open('/tmp/yeni_sektor_slugs.json', 'w'))
print('ok', len(out))

# gen_sektor_ek ile üretilen 8 sayfada da yapılandırılmış veri (SSS) kombi sayfasından kalmıştı: sayfadaki görünür SSS'ye eşitle
for s_, n_ in ALL16[8:]:
    f = 'sektor-%s.html' % s_
    h = open(f, encoding='utf-8').read()
    fqs = re.findall(r'<details[^>]*><summary>(.*?)</summary><p>(.*?)</p></details>', h, re.S)
    if not fqs:
        continue
    def _fix(mm, fqs=fqs, n_=n_, s_=s_):
        g = json.loads(mm.group(1))
        for it in g.get("@graph", []):
            if it.get("@type") == "FAQPage":
                it["mainEntity"] = [{"@type": "Question", "name": html.unescape(q), "acceptedAnswer": {"@type": "Answer", "text": html.unescape(a)}} for q, a in fqs]
            elif it.get("@type") == "SoftwareApplication":
                it["name"] = "OnlineKaydet — %s için takip programı" % n_
                it["url"] = "https://onlinekaydet.com/sektor-%s.html" % s_
        return '<script type="application/ld+json">' + json.dumps(g, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    h2 = re.sub(r'<script type="application/ld\+json">(.*?)</script>', _fix, h, count=1, flags=re.S)
    open(f, 'w', encoding='utf-8').write(h2)
print('ek sayfalar düzeltildi')
