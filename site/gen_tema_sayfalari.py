#!/usr/bin/env python3
"""20 sektör temasının tanıtım sayfaları (tema-<ad>.html). Veri: docs/tema20/pano.py (temanın gerçek bölüm, sayfa ve panel bağlantı listesi).
Önizlemedeki örnek rakamlar ve fiyatlar kullanılmaz."""
import os, re, sys, html
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
src = open('gen_seo_karsilastirma.py', encoding='utf-8').read()
exec(compile(src[:src.index('RIV = {')], 'gen_seo_pre', 'exec'))
sys.path.insert(0, os.path.join(D, '..', 'docs', 'tema20'))
from pano import T
_page = page
ACT = '<a class="bt" href="/iletisim.html#teklif">Ücretsiz deneyin</a><a class="bt l" href="tel:05444444004">Hemen arayın</a>'
def page(*a, **k):
    k.setdefault('acts', ACT); return _page(*a, **k)
_cta = cta
def cta(*a, **k): return _cta(*a, **k).replace('>0544 444 40 04</a>', '>Hemen arayın</a>')
TR = str.maketrans('çğıöşüÇĞİÖŞÜ&', 'cgiosuCGIOSU-')
def slug(n): return re.sub(r'[^a-z0-9]+', '-', n.translate(TR).lower()).strip('-')
SEC = {'hq': 'Giriş bölümü ve talep formu', 'br': 'Çalışılan markalar', 'sv': 'Hizmetler', 'cl': 'Hesaplama / sorgulama aracı', 'st': 'Adım adım süreç', 'nm': 'Rakamlar bölümü', 'gl': 'Fotoğraf galerisi',
       'rv': 'Müşteri yorumları', 'fq': 'Sık sorulanlar', 'mp': 'Bölgeler ve harita', 'tm': 'Ekip', 'pr': 'Paketler', 'ct': 'İletişim', 'ab': 'Hakkımızda', 'ln': 'Ürün / liste'}
TIP = {'servis': ('servis ve teklif', 'Arıza ya da iş talebi alan, teklif veren ve işi takip numarasıyla yürüten işler için hazırlandı. Müşteri formdan talebini gönderir; talep panelde iş kaydı olarak açılır.'),
       'randevu': ('randevu', 'Müşterinin gün ve saat seçerek randevu aldığı işler için hazırlandı. Randevu panelde takvime düşer; uzman ve hizmet seçimi forma dahildir.'),
       'magaza': ('e-ticaret', 'Ürün satan ya da sipariş alan işler için hazırlandı. Sepet, ödeme ve sipariş takibi temanın sayfalarında yer alır.'),
       'yemek': ('restoran', 'Menü gösteren ve masa rezervasyonu alan işletmeler için hazırlandı.'),
       'proje': ('ilan', 'Portföy ya da ilan listesi gösteren işler için hazırlandı; ilgilenen kişi ilan üzerinden iletişime geçer.'),
       'kurs': ('kurs ve kayıt', 'Ön kayıt alan, program ve eğitmen tanıtan kurslar için hazırlandı.')}
FOOT = {'servis': 'Kayıt, usta ve tahsilat panelde servis işinin kendi terimleriyle tutulur.', 'randevu': 'Randevular, uzmanlar ve müşteri geçmişi panelde tek yerden yönetilir.', 'magaza': 'Ürün, sipariş ve kargo panelden yönetilir.',
        'yemek': 'Menü ve rezervasyonlar panelden düzenlenir.', 'proje': 'İlanlar ve başvurular panelden yönetilir.', 'kurs': 'Ön kayıtlar ve dersler panelden yönetilir.'}
def renk(h): return '<span style="display:inline-block;width:18px;height:18px;border-radius:4px;background:%s;border:1px solid #cfd3de;vertical-align:-3px;margin-right:6px"></span>%s' % (h, h)
def uret(n, t):
    ad, sek, tip, pal, font, bol, sayf, pan, kel = t[:9]
    ad = html.unescape(ad); fn = 'tema-%s.html' % slug(ad)
    tn, tx = TIP[tip]
    bolum = [(SEC.get(b.split(':')[0], b.split(':')[0]), b.split(':', 1)[1]) for b in bol]
    body = (STIL
        + sec('Bu tema kimin için?', '<p><b>%s</b>, %s sektörü için hazırlanmış %s temasıdır. %s</p><p>Önizlemeyi gezerek ana sayfayı ve alt sayfaları canlı görebilirsiniz.</p><p><a class="bt" href="/tema-onizleme/yeni/%02d/index.html">Önizlemeyi aç</a></p>' % (ad, sek, tn, tx, n))
        + sec('Ana sayfadaki bölümler', '<div class="kt">%s</div><p class="mini">Her bölümün metni, görseli ve yazı tipi panelden düzenlenir.</p>' % ''.join('<div class="r"><b>%s</b><span>%s</span></div>' % (a, html.escape(b)) for a, b in bolum), tint=True)
        + sec('Temadaki sayfalar', '<ul>%s</ul><p class="mini">Ana sayfaya ek olarak bu sayfalar temayla birlikte gelir.</p>' % ''.join('<li>%s</li>' % x for x in sayf))
        + sec('Panelle bağlantılar', '<ul>%s</ul><p>%s</p>' % (''.join('<li>%s</li>' % x for x in pan), FOOT[tip]), tint=True)
        + sec('Renk ve yazı tipleri', '<p>%s</p><p>Yazı tipi: <b>%s</b></p><p class="mini">Renkleri ve yazı tipini panelden kendi markanıza göre değiştirebilirsiniz.</p>' % (' &nbsp; '.join(renk(c) for c in pal), html.escape(font)))
        + sec('Sitede işlenen konular', '<p>%s.</p><p class="mini">Başlıklar ve metinler bu konulara göre hazırlanır; kendi hizmetlerinize göre değiştirebilirsiniz.</p>' % html.escape(kel).replace(', ', '; ').replace(';', ','), tint=True)
        + sec('Aynı türdeki diğer temalar', '<p style="line-height:2.2">%s</p><p><a href="yeni-temalar.html">Tüm yeni sektör temaları</a> · <a href="temalar.html">Temalar</a></p>' % ' · '.join('<a href="tema-%s.html">%s</a>' % (slug(html.unescape(x[0])), html.unescape(x[0])) for x in T if x[2] == tip and x[0] != t[0]) or 'Bu türde tek tema var.')
        + faq('Sık sorulan sorular', SSS(ad, sek)) + cta('%s temasını deneyin' % ad, 'Temayı seçin, metin ve fotoğrafları kendi işinize göre değiştirin. 7 gün ücretsiz.'))
    return fn, ad, sek, body
def SSS(ad, sek):
    return [('%s temasını kendi markama göre düzenleyebilir miyim?' % ad, 'Evet. Ana sayfadaki her bölümün metnini, görselini ve yazı tipini panelden değiştirirsiniz; renkleri markanıza uyarlarsınız.'),
            ('Tema mobilde de çalışır mı?', 'Evet. Tema telefonda alt çubuk, tam ekran menü ve ayrı bir alt bilgi düzeniyle gelir.'),
            ('%s için başka tema seçebilir miyim?' % sek, 'Evet. Tüm temalar Temalar sayfasında listelenir; sitenizi kaydedip istediğiniz zaman tema değiştirebilirsiniz.'),
            ('Önizlemedeki fotoğraf ve yazılar benim sitemde de olacak mı?', 'Önizleme örnek içerikle hazırlanır. Kendi sitenizde bu alanları kendi metin ve fotoğraflarınızla doldurursunuz.')]
def sitemap(NEW):
    sm = open('sitemap.xml', encoding='utf-8').read(); add = ''
    for n in NEW:
        u = 'https://onlinekaydet.com/' + n
        if u not in sm: add += '<url><loc>%s</loc></url>\n' % u
    if add: open('sitemap.xml', 'w', encoding='utf-8').write(sm.replace('</urlset>', add + '</urlset>'))
if __name__ == '__main__':
    NEW = []; liste = []
    for n, t in enumerate(T, 1):
        fn, ad, sek, body = uret(n, t)
        qa = SSS(ad, sek)
        page(fn, '%s teması: %s sitesi | OnlineKaydet' % (ad, sek), '%s teması, %s için hazır çok sayfalı site: bölümleri, sayfaları, panel bağlantıları ve renkleri. Önizlemeyi açın, 7 gün ücretsiz deneyin.' % (ad, sek),
             '<a href="temalar.html">Temalar</a> / %s' % ad, '%s teması: %s sitesi' % (ad, sek), '%s için hazır, her bölümü düzenlenebilir site teması.' % sek, body, ld=faq_ld(qa))
        NEW.append(fn); liste.append((fn, ad, sek))
    sitemap(NEW); print(len(NEW), 'sayfa')
    import json; json.dump(liste, open('/tmp/tema_liste.json', 'w', encoding='utf-8'), ensure_ascii=False)
