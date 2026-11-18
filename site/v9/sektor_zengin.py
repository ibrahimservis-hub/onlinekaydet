# -*- coding: utf-8 -*-
"""Sektör sayfalarını (sektor-*.html) zenginleştirir: neler değişir, işinizi nasıl geliştirir, kayıt akışı, sık sorulanlar,
benzer sektörler + başlık/açıklama/JSON-LD/arama dizini/sitemap. Tekrar çalıştırılabilir (<!--ZENGIN--> işaretli blok yenilenir)."""
import os, re, sys, json, html, glob
E = html.escape
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(S, '..', 'panel'))
import seo_uret as su, sektor_cok2 as c2, sitegen as g
from sektor_metin import M
BASE = 'https://onlinekaydet.com'
DET = {r[0]: r for r in c2.R}
SEKT = list(g.SECTORS.items())
AD = {k: (DET[k][1] if k in DET else a) for k, a in SEKT}
TIP = {}
for k, a in SEKT:
    t = su.MAN.get(k) or (DET[k][2] if k in DET else 'servis')
    TIP[k] = t if t in su.PROG else 'servis'
ONCE = {'kombi', 'klima', 'beyaz_esya', 'bilgisayar', 'elektrik', 'elektronik', 'guvenlik', 'tesisat'}


def lo(x): return x.replace('I', 'ı').replace('İ', 'i').lower()


def buyuk(x): return x[:1].upper() + x[1:]


def kartlar(tip, ad, v):
    n, nl, kisi, staff, gun = v['noun'], lo(v['noun']), lo(v['kisi_l']), lo(v['staff']), v['gun']
    yer = lo(v['yer'])
    if tip == 'randevu':
        return [('Boş saatleri görün', 'Takvim %s ve saate göre dolu ve boş yerleri gösterir; %s sabah tek ekrandan okunur.' % (staff, lo(gun))),
                ('Gelmeyen randevuyu azaltın', 'Randevudan önce müşteriye hatırlatma mesajı gider (mesaj ayarı açıksa). Gelmeyenler “Gelmedi” diye işaretlenir, raporlarda görünür.'),
                ('Müşteri geri gelsin', 'Her %s kartında geçmiş işlemler ve notlar durur; uzun süredir uğramayanı bulup arayabilirsiniz. Raporda yeni ve geri gelen müşteri sayısı ayrı yazar.' % kisi),
                ('Gece de randevu alın', 'Sitenizdeki randevu formu panele düşer; siz sabah onaylar ya da saati değiştirirsiniz.'),
                ('Kasa kendiliğinden tutulsun', '“Tamamla ve ödeme al” dediğinizde tutar ilgili randevuya bağlanır ve kasaya yazılır.'),
                ('Ekibin hakedişi net olsun', 'Prim, tamamlanan randevulardan hesaplanır; kişi bazında yapılan iş, ciro ve ödenecek tutar tabloda görünür.')]
    if tip == 'servis':
        return [('Her iş tek kayıtta', '%s açıldığında müşteri, adres, sorun ve durum aynı kartta durur; telefonla sorulan şeyi dosya aramadan bulursunuz.' % n),
                ('Müşteri sormadan bilsin', 'Durum değiştikçe müşteriye bilgi mesajı gönderilir (SMS bağlantısı kurulduktan sonra).'),
                ('Tekrar eden sorunu yakalayın', 'Aynı müşterinin ya da aynı cihazın geçmiş kayıtları birlikte görünür; ikinci kez gelen sorun hemen fark edilir.'),
                ('%s işi dengeli dağıtın' % buyuk(staff), 'İşi kişiye atar, kimin ne kadar işi olduğunu %s ekranından görürsünüz.' % lo(gun)),
                ('Parça ve işçilik kasada', 'Kullanılan parça ve işçilik kayda yazılır, tahsilat ve kalan borç kasada toplanır.'),
                ('Sitenizden iş gelsin', 'Sitenizdeki talep formu panele düşer; müşteri aradığında kaydını açık bulursunuz.')]
    if tip == 'kurs':
        return [('Kayıt tek dosyada', 'Kursiyerin bilgisi, evrakı, programı ve ödemesi aynı kayıttadır; eksik evrak işaretli listede görünür.'),
                ('Ödeme ve taksit görünür', 'Ödeme planı kayda yazılır, tahsilat kasaya geçer; kimin kaç taksidi kaldığı listeden okunur.'),
                ('Devam ve program', 'Ders programı takvimde görünür; devamsızlık kayda işlenir.'),
                ('Veliye ve öğrenciye haber', 'Duyuru ve hatırlatma mesajı panelden gönderilir (SMS bağlantısı kurulduktan sonra).'),
                ('Ön kayıt web sitesinden', 'Sitedeki kayıt formu doğrudan panele düşer; arayıp kayda çevirirsiniz.'),
                ('Eğitmen ve ekip', 'Eğitmen bazında program ve iş dağılımı görünür; hakediş kayıtta tutulur.')]
    if tip == 'menu':
        return [('Tek listede siparişler', 'Siteden, telefondan ve bağlı platformlardan gelen siparişler aynı listede toplanır; yeni gelen hemen görünür.'),
                ('Hazırlık ve teslim planı', '%s ekranı hazırlanacak ve teslim edilecekleri tarih saat sırasıyla gösterir.' % buyuk(lo(gun))),
                ('Rezervasyon ve özel istek', 'Gelen talepler panele düşer; onay mesajı gönderir, özel isteği kayda not düşersiniz.'),
                ('Ürün ve menü bir kez', 'Ürünü ya da menüyü bir kez girersiniz; site ve bağlı kanallar aynı kayıttan beslenir.'),
                ('Kasa ve tahsilat', 'Ödeme siparişe bağlanır; kapora ve kalan tutar kayıtta ayrı görünür.'),
                ('Müşteri geçmişi', 'Müşterinin önceki siparişleri kartında durur; tekrar siparişi hızlı açarsınız.')]
    if tip == 'cekim':
        return [('Her iş bir dosya', '%s açıldığında müşteri, tarih, teklif ve notlar aynı kayıtta durur.' % n),
                ('Teklif ve onay', 'Teklifi ve onay adımını kayıtta izlersiniz; hangi işin hangi aşamada olduğu listeden okunur.'),
                ('Kapora ve ödeme', 'Kapora ve kalan tutar kayda yazılır; tahsilat kasaya geçer.'),
                ('Takvimde çakışma görün', 'İş ve teslim günleri takvimde görünür; aynı güne iki iş yazmadan önce görürsünüz.'),
                ('Çalışmalarınız sitede', 'Galeri ve örnek işleri sitenize panelden eklersiniz; müşteri formu panele düşer.'),
                ('Ekip ve görev', 'İşi kişiye atar, kim ne yapıyor görürsünüz.')]
    if tip == 'urun':
        return [('Ürün bir kez girilir', 'Ürün kartı site ve bağlı pazaryerlerinde aynı kayıttan kullanılır; fiyat ve stok her yerde aynı kalır.'),
                ('Stok uyarısı', 'Stok azaldığında uyarı alırsınız; satılan ürünün stoku sipariş kaydolunca düşer.'),
                ('Sipariş ve kargo', 'Sipariş durumları ve kargo kodu tek listede ilerler; iptal ve iadede stok geri döner.'),
                ('Pazaryeri kanalları', 'Trendyol, Hepsiburada gibi pazaryeri kartlarından bağlantı kurulur; kanal fiyatı ve net kâr ürün kartında görünür.'),
                ('Mağaza sitenizde', 'Sitenin içinde mağaza açılır; sepet, ödeme ve sipariş aynı panele gelir.'),
                ('Kâr ve rapor', 'Ciro, net kâr ve sepet ortalaması sipariş listesinin üstünde durur.')]
    # ilan (müşteri / dosya / talep)
    return [('Her müşteri bir dosya', '%s açıldığında müşteri, talep, görüşme notları ve evrak aynı kayıtta durur.' % n),
            ('Hatırlatma ve takvim', 'Görüşme, teslim ve randevu günleri takvime yazılır; hatırlatma tarihi gelince görünür.'),
            ('Teklif ve onay', 'Teklif ve onay adımları kayıtta ilerler; bekleyen işler ayrı süzülür.'),
            ('Tahsilat ve borç', 'Ödeme dosyaya bağlanır; alınan, kalan ve geciken tutarlar kasada görünür.'),
            ('Sitenizden talep alın', 'Sitedeki form panele düşer; ilan ya da hizmet sayfalarınız arama motorlarında yer alır.'),
            ('Ekip ve görev', 'Dosyayı kişiye atar, kimin ne yaptığını görürsünüz.')]


def tablo(tip, ad, v):
    nl = lo(v['noun']); kisi = lo(v['kisi_l']); staff = lo(v['staff']); gun = lo(v['gun'])
    R = [('%s kaydı' % v['noun'], 'Defter, Excel ve mesajlara dağılır', 'Her %s tek kayıtta, adım adım ilerler' % nl),
         ('%s geçmişi' % buyuk(kisi), 'Aramak zaman alır', 'İsim ya da telefonla anında açılır'),
         (buyuk(lo(v['chk_t'])), 'Akılda ya da kağıtta', 'Her kayıtta işaretli madde listesi'),
         ('Hatırlatma', 'Elle aranır', 'Panelden mesaj gönderilir'),
         ('Ödeme ve borç', 'Ayrı defterde', 'Kayda bağlı, kasada toplanır'),
         (buyuk(staff), 'Telefonla yönlendirilir', 'İş kişiye atanır, %s ekranında görünür' % gun),
         ('Web siteniz', 'Ayrı bir ajansa bağlı', 'Hazır tema, yazı ve resimleri panelden değiştirirsiniz')]
    return '<div class="sxtb"><table><thead><tr><th></th><th>Şimdi</th><th>OnlineKaydet ile</th></tr></thead><tbody>%s</tbody></table></div>' % ''.join(
        '<tr><th>%s</th><td>%s</td><td>%s</td></tr>' % (E(a), E(b), E(x)) for a, b, x in R)


def sss(k, ad, tip, v):
    nl = lo(v['noun']); steps = v['steps']; pain, gain, tipm = M[k]
    q = [('%s için hangi kayıtlar tutulur?' % ad, 'Her %s tek kayıtta açılır; alanlar: %s. Geçmiş kayıtlara isim ya da telefonla ulaşırsınız.' % (nl, ', '.join(lo(x) for x in v['fields'][:6]))),
         ('%s ne zaman ilerler, hangi adımlar var?' % buyuk(nl), 'Her %s şu adımlardan geçer: %s. Hangi adımda olduğu listede görünür.' % (nl, ', '.join(steps))),
         ('%s işinde en çok hangi sorun yaşanır, panel nasıl çözer?' % ad, pain + ' ' + gain),
         ('Evrak ya da kontrol listesi var mı?', '“%s” her kayıtta bulunur: %s.' % (v['chk_t'], '; '.join(v['chk'][:4]))),
         ('Müşteriye mesaj gönderebilir miyim?', 'Evet. Panelden randevu ve durum mesajı gönderilir; SMS için sağlayıcı bağlantısı kurmanız gerekir.'),
         ('%s için web sitesi de var mı?' % ad, 'Evet. Sektörünüze uygun hazır temalardan birini seçersiniz; yazı, yazı tipi ve resimleri panelden değiştirirsiniz. Sitedeki form talepleri panele düşer.'),
         ('Denemek ücretli mi?', 'Hayır. Demo hesabı 7 gün ücretsiz kullanılır, kart bilgisi istenmez.')]
    return q


def tema_gorsel(k):
    """Yalnız gerçek fotoğraflı (n serisi) tema önizlemesi; fotoğrafı olmayan sektörde bölüm gösterilmez."""
    if not os.path.exists(os.path.join(S, '..', 'themes', 'img', k + '.jpg')):
        return None
    s = k.replace('_', '-')
    d = sorted(glob.glob(S + '/v9/img/tema-n*-%s-d.webp' % s), key=lambda x: int(re.search(r'tema-n(\d+)-', x).group(1)))
    return (os.path.basename(d[0]), None) if d else None


def blok(k, once):
    ad = AD[k]; tip = TIP[k]; v = su.veri(k, ad, tip); pain, gain, tipm = M[k]; nl = lo(v['noun'])
    cards = kartlar(tip, ad, v)
    b = ['<!--ZENGIN-->']
    b.append('<section class="sec" id="neler-degisir"><div class="w"><p class="et">%s işinde</p><h2>%s işinde neler değişir?</h2><p class="lead">%s</p>%s</div></section>' % (E(ad), E(ad), E(pain + ' ' + gain), tablo(tip, ad, v)))
    b.append('<section class="sec" id="isinizi-gelistirin"><div class="w"><h2>%s işinizi nasıl geliştirir?</h2><div class="fg">%s</div><p class="sxy"><b>İpucu:</b> %s</p></div></section>' % (
        E(ad), ''.join('<div class="fk"><span class="no">%02d</span><h3>%s</h3><p>%s</p></div>' % (i + 1, E(a), E(t)) for i, (a, t) in enumerate(cards)), E(tipm)))
    b.append('<section class="sec" id="kayit-akisi"><div class="w"><h2>Bir %s panelde nasıl ilerler?</h2>%s<p style="margin-top:18px"><b>%s:</b> %s.</p></div></section>' % (
        E(nl), su.adim(v['steps'], v['side']), E(v['chk_t']), E('; '.join(v['chk'][:6]))))
    tg = tema_gorsel(k)
    if tg:
        b.append('<section class="sec" id="sektor-tema"><div class="w"><h2>%s için hazır web sitesi teması</h2><p class="lead">Temayı seçer, yazı ve resimleri panelden değiştirirsiniz. Sitedeki formlar panele düşer.</p>'
                 '<a href="/temalar.html"><img src="/v9/img/%s" alt="%s için hazır web sitesi teması" width="1280" height="800" loading="lazy" style="width:100%%;height:auto;border-radius:14px;border:1px solid var(--ln,#e3e7ef)"></a>'
                 '<p style="margin-top:14px"><a class="btn bos2" href="/temalar.html">Tüm temaları görün</a></p></div></section>' % (E(ad), tg[0][:-5] + '.webp', E(ad)))
    if not once:
        q = sss(k, ad, tip, v)
        b.append('<section class="sec" id="sss"><div class="w"><h2>%s için sık sorulan sorular</h2>%s</div></section>' % (E(ad), su.sss_html(q)))
    ben = [(k2, AD[k2]) for k2, _ in SEKT if k2 != k and TIP[k2] == tip][:8]
    if ben:
        b.append('<section class="sec"><div class="w"><h2>Benzer iş kolları</h2><div class="slst">%s<a href="/tum-sektorler.html">Tüm sektörler</a></div></div></section>' % ''.join(
            '<a href="/sektor-%s.html">%s</a>' % (k2.replace('_', '-'), E(a2)) for k2, a2 in ben))
    b.append('<!--/ZENGIN-->')
    return ''.join(b), v, (None if once else sss(k, ad, tip, v))


def meta(h, title, desc, extra_ld=''):
    h = re.sub(r'<title>.*?</title>', lambda m: '<title>%s</title>' % E(title), h, count=1, flags=re.S)
    h = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + E(desc, quote=True), h, count=1)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + E(title, quote=True), h, count=1)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + E(desc, quote=True), h, count=1)
    if '<meta name="twitter:title"' not in h:
        h = h.replace('<meta name="twitter:card" content="summary_large_image">', '<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="%s"><meta name="twitter:description" content="%s">' % (E(title, quote=True), E(desc, quote=True)), 1)
    else:
        h = re.sub(r'(<meta name="twitter:title" content=")[^"]*', lambda m: m.group(1) + E(title, quote=True), h, count=1)
        h = re.sub(r'(<meta name="twitter:description" content=")[^"]*', lambda m: m.group(1) + E(desc, quote=True), h, count=1)
    h = re.sub(r'<script type="application/ld\+json" data-z="1">.*?</script>', '', h, flags=re.S)
    if extra_ld:
        h = h.replace('</head>', extra_ld + '\n</head>', 1)
    return h


def ld(obj): return '<script type="application/ld+json" data-z="1">%s</script>' % json.dumps(obj, ensure_ascii=False)


def run():
    arama = json.load(open(S + '/v9/arama.json', encoding='utf-8'))
    amap = {e['u']: e for e in arama}
    sm = open(S + '/sitemap.xml', encoding='utf-8').read()
    n = 0
    for k, _ in SEKT:
        fn = 'sektor-%s.html' % k.replace('_', '-'); p = os.path.join(S, fn)
        if not os.path.exists(p):
            continue
        h = open(p, encoding='utf-8').read()
        once = k in ONCE
        h = re.sub(r'<!--ZENGIN-->.*?<!--/ZENGIN-->', '', h, flags=re.S)
        bl, v, q = blok(k, once)
        ad = AD[k]; tip = TIP[k]; prog = su.PROG[tip]; steps = v['steps']
        if '<h2>Sık sorulan sorular</h2>' in h and once:
            i = h.index('<h2>Sık sorulan sorular</h2>'); j = h.rfind('<section', 0, i)
        elif ' için detaylı sayfalar</h2>' in h:
            i = h.index(' için detaylı sayfalar</h2>'); j = h.rfind('<section', 0, i)
        else:
            j = h.index('<section class="son" id="teklif">')
        h = h[:j] + bl + h[j:]
        if not once:
            title = '%s İçin Web Sitesi ve %s | OnlineKaydet' % (ad, prog)
            if len(title) > 68: title = '%s İçin Web Sitesi ve %s' % (ad, prog)
            if len(title) > 68: title = '%s Web Sitesi ve %s | OnlineKaydet' % (ad, prog)
            desc = '%s için %s ve hazır web sitesi: her %s “%s” adımından “%s” adımına kadar izlenir; takvim, kasa ve raporlar panelde. 7 gün ücretsiz deneyin.' % (ad, lo(prog), lo(v['noun']), steps[0], steps[-1])
            if len(desc) > 165: desc = '%s için %s ve hazır web sitesi: %s kaydı, takvim, kasa ve raporlar tek panelde. 7 gün ücretsiz deneyin.' % (ad, lo(prog), lo(v['noun']))
            h = re.sub(r'(<p class="lead">)Sektörünüze hazır tema ve panel: kayıtlar, randevular, kasa ve web siteniz tek yerde\.', lambda m: m.group(1) + E('%s için hazır tema ve panel: %s kaydı, takvim, kasa ve web siteniz tek yerde.' % (ad, lo(v['noun']))), h, count=1)
            lds = ld({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': x, 'acceptedAnswer': {'@type': 'Answer', 'text': y}} for x, y in q]})
        else:
            title = None; desc = None; lds = ''
        sw = ld({'@context': 'https://schema.org', '@type': 'SoftwareApplication', 'name': 'OnlineKaydet — %s' % ad, 'applicationCategory': 'BusinessApplication', 'operatingSystem': 'Web',
                 'description': '%s için %s, web sitesi, kasa ve raporlar.' % (ad, lo(prog)), 'url': '%s/%s' % (BASE, fn), 'inLanguage': 'tr',
                 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'TRY', 'description': '7 gün ücretsiz deneme'}})
        if title:
            h = meta(h, title, desc, lds + sw)
        else:
            h = re.sub(r'<script type="application/ld\+json" data-z="1">.*?</script>', '', h, flags=re.S)
            h = h.replace('</head>', sw + '\n</head>', 1)
        open(p, 'w', encoding='utf-8').write(h)
        # arama dizini
        text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h[h.index('<main'):h.index('</main>')])).strip()
        hs = [re.sub(r'<[^>]+>', '', m.group(2)).strip() for m in re.finditer(r'<(h1|h2|h3)[^>]*>(.*?)</\1>', h[h.index('<main'):h.index('</main>')], re.S)]
        e = amap.get('/' + fn)
        if e is not None:
            if title: e['t'] = title.split(' | ')[0]; e['d'] = desc
            e['h'] = hs[:14]; e['x'] = text[:1800]
        sm = re.sub(r'(<loc>%s/%s</loc><lastmod>)[^<]*' % (re.escape(BASE), re.escape(fn)), lambda m: m.group(1) + '2026-11-19', sm)
        n += 1
    json.dump(arama, open(S + '/v9/arama.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    open(S + '/sitemap.xml', 'w', encoding='utf-8').write(sm)
    print('güncellendi', n)


if __name__ == '__main__':
    run()
