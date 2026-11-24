#!/usr/bin/env python3
"""Sektör, bilgi rehberi ve entegrasyon sayfaları arasına 'İlgili sayfalar' bölümü ekler (<!--IB-->…<!--/IB-->).
İdempotent: her çalıştırmada eski bölüm silinip yeniden yazılır. Yalnız var olan dosyalara bağlanır. Çalıştır: python3 site/gen_ic_baglanti.py"""
import os, re, glob, zlib
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
src = open('gen_seo_karsilastirma.py', encoding='utf-8').read()
exec(compile(src[:src.index('RIV = {')], 'gen_seo_pre', 'exec'))   # STIL, sec, kt
IBCSS = ('<style>.ibg{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;max-width:1100px}'
         '.ibg a{display:block;border:1px solid #d9dce6;border-radius:10px;background:#fff;padding:14px 16px;line-height:1.45;font-weight:600;text-decoration:none;color:inherit}'
         '.ibg a:hover{border-color:#0a0c0f}.ibg a small{display:block;font-weight:400;color:#5b6173;margin-top:3px;font-size:13px}'
         '.ibh{margin:26px 0 12px;font-size:16px;font-weight:700}</style>')
ok = lambda fn: os.path.exists(fn)

# Entegrasyon grup sayfaları: dosya -> (metin son eki, kısa açıklama)
ENT = {
 'sanal-pos-entegrasyonu.html': ('kartla tahsilat ve sanal POS entegrasyonu', 'iyzico gibi ödeme altyapılarını bağlayın'),
 'kargo-entegrasyonu.html': ('kargo entegrasyonu ve takip', 'gönderi ve takip numarası süreci'),
 'e-fatura-e-arsiv-entegrasyonu.html': ('e-fatura ve e-arşiv entegrasyonu', 'faturayı panelden kesin'),
 'muhasebe-erp-entegrasyonu.html': ('muhasebe ve ERP programı entegrasyonu', 'kayıtları muhasebe programına aktarın'),
 'pazaryeri-entegrasyonu.html': ('pazaryeri entegrasyonu', 'ürün ve siparişleri tek yerden yönetin'),
 'sms-whatsapp-eposta-entegrasyonu.html': ('SMS, WhatsApp ve e-posta bildirimleri', 'müşteriye otomatik mesaj'),
 'olcum-reklam-entegrasyonu.html': ('ölçüm ve reklam entegrasyonu', 'reklam ve ziyaretçi takibi'),
}
# Rehberler: dosya -> (sektör sayfasındaki ek: "{Sektör} için …", bilgi sayfasındaki bağlantı metni)
BIL = {
 'bilgi-randevu-ve-takvim.html': ('randevu ve takvim rehberi', 'Randevu nasıl verilir ve takvim nasıl yönetilir?'),
 'bilgi-musteri-yonetimi.html': ('müşteri kayıtlarını düzenli tutma rehberi', 'Müşteri kayıtları nasıl tutulur ve aranır?'),
 'bilgi-kasa-ve-muhasebe.html': ('kasa, tahsilat ve gider takibi rehberi', 'Kasa, tahsilat ve gider takibi nasıl yapılır?'),
 'bilgi-personel-ve-prim.html': ('ekip, maaş ve prim hesabı rehberi', 'Ekip, maaş ve prim hesabı nasıl yapılır?'),
 'bilgi-web-sitesi-duzenleme.html': ('web sitesini düzenleme rehberi', 'Web sitenizin metin, resim ve menüsü nasıl düzenlenir?'),
 'bilgi-alan-adi.html': ('kendi alan adını bağlama rehberi', 'Kendi alan adınızı siteye nasıl bağlarsınız?'),
 'bilgi-entegrasyon-baglama.html': ('entegrasyon bağlama rehberi', 'Ödeme, kargo, SMS ve diğer entegrasyonlar nasıl bağlanır?'),
 'bilgi-siparis-ve-kargo.html': ('sipariş ve kargo takibi rehberi', 'Sipariş ve kargo takibi nasıl yürütülür?'),
 'bilgi-urun-ekleme.html': ('ürün ekleme rehberi', 'Panele ürün nasıl eklenir?'),
 'bilgi-pazaryerine-gonderme.html': ('ürünleri pazaryerine gönderme rehberi', 'Ürünler pazaryerine nasıl gönderilir?'),
 'bilgi-xml-ile-urun-aktarma.html': ('XML ile tedarikçi ürünü aktarma rehberi', 'XML ile tedarikçi ürünleri nasıl aktarılır?'),
 'bilgi-toplu-fatura.html': ('toplu fatura hazırlama rehberi', 'Siparişlere toplu fatura nasıl hazırlanır?'),
 'bilgi-etiket-tasarimi.html': ('kargo etiketi ve QR kart tasarlama rehberi', 'Kargo etiketi ve QR menü kartı nasıl tasarlanır?'),
 'bilgi-yemek-menusu.html': ('menü hazırlama rehberi', 'Restoran menüsü nasıl hazırlanır?'),
 'bilgi-menu-pazaryerine-gonderme.html': ('menüyü yemek platformlarına gönderme rehberi', 'Menü yemek platformlarına nasıl gönderilir?'),
 'bilgi-yemek-siparisleri.html': ('yemek siparişlerini panelde toplama rehberi', 'Yemek siparişleri panele nasıl düşer?'),
 'bilgi-ilan-ekleme.html': ('ilan ekleme rehberi', 'Panelden ilan nasıl eklenir?'),
 'bilgi-baslangic.html': ('ilk gün kurulum rehberi', 'İlk gün: hesabı açıp yayına almak'),
 'bilgi-sifirdan-baslangic.html': ('sıfırdan başlangıç rehberi', 'Hiç bilmeden başlayın: ilk gününüzü adım adım yönetin'),
 'bilgi-ve-veri-guvenligi.html': ('veri güvenliği ve yetkilendirme rehberi', 'Verileriniz ve ekip yetkileri nasıl güvende tutulur?'),
}
# Sektör grupları: (sektör slug kümesi, rehberler, entegrasyonlar)
RANDEVU = 'aile-danisman avukat dis-klinigi diyetisyen dovme-studyo estetik-merkezi fizyoterapi guzellik kuafor psikolog spa-hamam tirnak-studyo veteriner optik fotografci yoga-dans spor-salonu yuzme-kursu evcil-hayvan mimar tercume'.split()
EGITIM = 'anaokulu bilgisayar-kursu dil-okulu etut-merkezi muzik-kursu ozel-ders src-kursu surucu-kursu'.split()
ETKINLIK = 'dj-muzik dugun-salonu tur-organizasyon arac-kiralama transfer'.split()
SERVIS = ('kombi klima beyaz-esya elektronik bilgisayar telefon-tamir yazici-servis asansor jenerator oto-servis oto-yikama oto-kaplama lastikci '
          'cilingir tesisat elektrik tadilat cam-dograma bocek-ilaclama su-aritma havuz-bakim peyzaj gunes-enerjisi guvenlik temizlik hali-yikama '
          'kuru-temizleme terzi ayakkabi-tamir kuyumcu-saat mobilya oto-cekici nakliye kurye matbaa').split()
SATIS = 'eticaret market tekstil cicekci'.split()
YEMEK = 'lokanta catering pastane'.split()
G = {}
for s in RANDEVU: G[s] = (['randevu-ve-takvim', 'musteri-yonetimi', 'kasa-ve-muhasebe', 'web-sitesi-duzenleme'], ['sms-whatsapp-eposta-entegrasyonu', 'sanal-pos-entegrasyonu', 'e-fatura-e-arsiv-entegrasyonu'])
for s in EGITIM: G[s] = (['randevu-ve-takvim', 'musteri-yonetimi', 'personel-ve-prim', 'kasa-ve-muhasebe'], ['sms-whatsapp-eposta-entegrasyonu', 'sanal-pos-entegrasyonu', 'e-fatura-e-arsiv-entegrasyonu'])
for s in ETKINLIK: G[s] = (['randevu-ve-takvim', 'musteri-yonetimi', 'kasa-ve-muhasebe', 'alan-adi'], ['sanal-pos-entegrasyonu', 'sms-whatsapp-eposta-entegrasyonu', 'e-fatura-e-arsiv-entegrasyonu'])
for s in SERVIS: G[s] = (['musteri-yonetimi', 'personel-ve-prim', 'kasa-ve-muhasebe', 'etiket-tasarimi'], ['sms-whatsapp-eposta-entegrasyonu', 'e-fatura-e-arsiv-entegrasyonu', 'muhasebe-erp-entegrasyonu'])
for s in SATIS: G[s] = (['urun-ekleme', 'siparis-ve-kargo', 'pazaryerine-gonderme', 'toplu-fatura'], ['pazaryeri-entegrasyonu', 'kargo-entegrasyonu', 'sanal-pos-entegrasyonu', 'e-fatura-e-arsiv-entegrasyonu'])
for s in YEMEK: G[s] = (['yemek-menusu', 'yemek-siparisleri', 'menu-pazaryerine-gonderme', 'kasa-ve-muhasebe'], ['pazaryeri-entegrasyonu', 'sanal-pos-entegrasyonu', 'sms-whatsapp-eposta-entegrasyonu'])
G['emlakci'] = (['ilan-ekleme', 'musteri-yonetimi', 'web-sitesi-duzenleme', 'alan-adi'], ['sms-whatsapp-eposta-entegrasyonu', 'olcum-reklam-entegrasyonu', 'e-fatura-e-arsiv-entegrasyonu'])
G['muhasebe'] = (['kasa-ve-muhasebe', 'toplu-fatura', 'musteri-yonetimi', 've-veri-guvenligi'], ['e-fatura-e-arsiv-entegrasyonu', 'muhasebe-erp-entegrasyonu', 'sanal-pos-entegrasyonu'])
DEF = (['musteri-yonetimi', 'kasa-ve-muhasebe', 'randevu-ve-takvim', 'web-sitesi-duzenleme'], ['sms-whatsapp-eposta-entegrasyonu', 'e-fatura-e-arsiv-entegrasyonu', 'sanal-pos-entegrasyonu'])

def ad(slug):
    t = open('sektor-%s.html' % slug, encoding='utf-8').read()
    m = re.search(r'<h1[^>]*>(.*?) için web sitesi', t, re.S) or re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else slug
SEK = sorted(f[7:-5] for f in glob.glob('sektor-*.html'))
AD = {s: ad(s) for s in SEK}
# bilgi sayfası -> ilişkili sektörler (üretilen kümelerden), diğer rehberler, entegrasyonlar
def sektorler_icin(bk):
    r = [s for s in SEK if bk in G.get(s, DEF)[0]]
    return r
REL = {  # bilgi sayfası -> ilgili diğer rehberler
 'randevu-ve-takvim': ['musteri-yonetimi', 'kasa-ve-muhasebe', 'personel-ve-prim', 'web-sitesi-duzenleme'],
 'musteri-yonetimi': ['randevu-ve-takvim', 'kasa-ve-muhasebe', 've-veri-guvenligi', 'toplu-fatura'],
 'kasa-ve-muhasebe': ['personel-ve-prim', 'toplu-fatura', 'musteri-yonetimi', 'randevu-ve-takvim'],
 'personel-ve-prim': ['kasa-ve-muhasebe', 'randevu-ve-takvim', 've-veri-guvenligi', 'musteri-yonetimi'],
 'web-sitesi-duzenleme': ['alan-adi', 'baslangic', 'randevu-ve-takvim', 'ilan-ekleme'],
 'alan-adi': ['web-sitesi-duzenleme', 'baslangic', 'entegrasyon-baglama', 've-veri-guvenligi'],
 'entegrasyon-baglama': ['pazaryerine-gonderme', 'siparis-ve-kargo', 'toplu-fatura', 'yemek-siparisleri'],
 'siparis-ve-kargo': ['urun-ekleme', 'pazaryerine-gonderme', 'toplu-fatura', 'etiket-tasarimi'],
 'urun-ekleme': ['xml-ile-urun-aktarma', 'pazaryerine-gonderme', 'siparis-ve-kargo', 'etiket-tasarimi'],
 'pazaryerine-gonderme': ['urun-ekleme', 'xml-ile-urun-aktarma', 'siparis-ve-kargo', 'entegrasyon-baglama'],
 'xml-ile-urun-aktarma': ['urun-ekleme', 'pazaryerine-gonderme', 'siparis-ve-kargo', 'toplu-fatura'],
 'toplu-fatura': ['siparis-ve-kargo', 'kasa-ve-muhasebe', 'urun-ekleme', 'entegrasyon-baglama'],
 'etiket-tasarimi': ['siparis-ve-kargo', 'yemek-menusu', 'urun-ekleme', 'musteri-yonetimi'],
 'yemek-menusu': ['menu-pazaryerine-gonderme', 'yemek-siparisleri', 'etiket-tasarimi', 'kasa-ve-muhasebe'],
 'menu-pazaryerine-gonderme': ['yemek-menusu', 'yemek-siparisleri', 'entegrasyon-baglama', 'kasa-ve-muhasebe'],
 'yemek-siparisleri': ['yemek-menusu', 'menu-pazaryerine-gonderme', 'entegrasyon-baglama', 'kasa-ve-muhasebe'],
 'ilan-ekleme': ['web-sitesi-duzenleme', 'musteri-yonetimi', 'alan-adi', 'baslangic'],
 'baslangic': ['sifirdan-baslangic', 'web-sitesi-duzenleme', 'musteri-yonetimi', 'randevu-ve-takvim'],
 'sifirdan-baslangic': ['baslangic', 'web-sitesi-duzenleme', 'urun-ekleme', 'randevu-ve-takvim'],
 've-veri-guvenligi': ['personel-ve-prim', 'musteri-yonetimi', 'alan-adi', 'kasa-ve-muhasebe'],
}
BENT = {  # bilgi sayfası -> entegrasyon grup sayfaları
 'randevu-ve-takvim': ['sms-whatsapp-eposta-entegrasyonu'], 'musteri-yonetimi': ['sms-whatsapp-eposta-entegrasyonu'],
 'kasa-ve-muhasebe': ['muhasebe-erp-entegrasyonu', 'sanal-pos-entegrasyonu', 'e-fatura-e-arsiv-entegrasyonu'],
 'personel-ve-prim': ['muhasebe-erp-entegrasyonu'], 'web-sitesi-duzenleme': ['olcum-reklam-entegrasyonu'],
 'alan-adi': ['olcum-reklam-entegrasyonu'], 'entegrasyon-baglama': ['sanal-pos-entegrasyonu', 'kargo-entegrasyonu', 'e-fatura-e-arsiv-entegrasyonu', 'muhasebe-erp-entegrasyonu'],
 'siparis-ve-kargo': ['kargo-entegrasyonu', 'pazaryeri-entegrasyonu'], 'urun-ekleme': ['pazaryeri-entegrasyonu'],
 'pazaryerine-gonderme': ['pazaryeri-entegrasyonu', 'kargo-entegrasyonu'], 'xml-ile-urun-aktarma': ['pazaryeri-entegrasyonu'],
 'toplu-fatura': ['e-fatura-e-arsiv-entegrasyonu', 'muhasebe-erp-entegrasyonu', 'kargo-entegrasyonu'],
 'etiket-tasarimi': ['kargo-entegrasyonu'], 'yemek-menusu': ['pazaryeri-entegrasyonu'],
 'menu-pazaryerine-gonderme': ['pazaryeri-entegrasyonu'], 'yemek-siparisleri': ['pazaryeri-entegrasyonu', 'sanal-pos-entegrasyonu'],
 'ilan-ekleme': ['olcum-reklam-entegrasyonu'], 'baslangic': ['entegrasyonlar'], 'sifirdan-baslangic': ['entegrasyonlar'],
 've-veri-guvenligi': ['entegrasyonlar'],
}
BK = lambda k: 'bilgi-%s.html' % k
def cik(grup):  # [(href, metin, açıklama)] -> html
    return '<div class="ibg">%s</div>' % ''.join('<a href="/%s">%s%s</a>' % (h, t, '<small>%s</small>' % d if d else '') for h, t, d in grup)
def blok(fn, gruplar):
    ic = ''
    for bas, grup in gruplar:
        if not grup: continue
        ic += ('<p class="ibh">%s</p>' % bas if bas else '') + cik(grup)
    return '<!--IB-->' + STIL + IBCSS + sec('İlgili sayfalar', ic, tint=True) + '<!--/IB-->'
def yerlestir(fn, b):
    t = open(fn, encoding='utf-8').read()
    t = re.sub(r'<!--IB-->.*?<!--/IB-->', '', t, flags=re.S)
    m = re.search(r'<section[^>]*\bid="kayit"', t)
    if not m: m = re.search(r'<section[^>]*>(?:(?!<section).)*?<h2[^>]*>Diğer rehberler</h2>', t, re.S)
    if not m: m = re.search(r'<section class="son" id="teklif"', t)
    pos = m.start() if m else t.index('</main>')
    n = t[:pos] + b + t[pos:]
    return n
def yaz(fn, b):
    old = open(fn, encoding='utf-8').read()
    n = yerlestir(fn, b)
    if n != old:
        open(fn, 'w', encoding='utf-8').write(n); return 1
    return 0
def var(h): return ok(h.split('#')[0])
degisen = 0
# 1) sektör sayfaları
for i, s in enumerate(SEK):
    fn = 'sektor-%s.html' % s; a = AD[s]
    bl, en = G.get(s, DEF)
    bl = [k for k in bl]
    # rotasyonla bir ek rehber: sektörler arası çeşitlilik
    ekler = [k for k in ['web-sitesi-duzenleme', 'alan-adi', 'baslangic', 've-veri-guvenligi', 'entegrasyon-baglama'] if k not in bl]
    if len(bl) < 4: bl.append(ekler[zlib.crc32(s.encode()) % len(ekler)])
    rehber = [(BK(k), '%s için %s' % (a, BIL[BK(k)][0]), '') for k in bl[:4] if var(BK(k))]
    ent = [(f, '%s için %s' % (a, ENT[f][0]), ENT[f][1].capitalize()) for f in en if var(f)]
    ek = []
    if var('%s-muhasebe-programi.html' % s) and s != 'muhasebe': ek.append(('%s-muhasebe-programi.html' % s, '%s muhasebe programı' % a, 'Cari, kasa ve alacak takibi'))
    if var('entegrasyonlar.html'): ek.append(('entegrasyonlar.html', 'Tüm entegrasyonlar', 'Bağlanabilen ödeme, kargo, fatura ve mesaj hizmetleri'))
    if var('bilgi-bankasi.html'): ek.append(('bilgi-bankasi.html', 'Bilgi bankası', 'Adım adım kullanım rehberleri'))
    gr = [('Kullanım rehberleri', rehber), ('Entegrasyonlar', ent), ('Daha fazlası', [x for x in ek if x[0] != fn])]
    degisen += yaz(fn, blok(fn, gr))
# 2) bilgi sayfaları
for bf in sorted(glob.glob('bilgi-*.html')):
    k = bf[6:-5]
    if k == 'bankasi' or k not in REL: continue
    rel = [(BK(r), BIL[BK(r)][1], '') for r in REL[k] if BK(r) != bf and var(BK(r))]
    sk = sektorler_icin(k)
    # kararlı ama sayfaya göre değişen 4 sektör
    sk = sorted(sk, key=lambda s: zlib.crc32((k + s).encode()))[:4]
    sek = [('sektor-%s.html' % s, '%s için iş takip ve kayıt programı' % AD[s], '') for s in sk if var('sektor-%s.html' % s)]
    ent = []
    for f in BENT.get(k, []):
        if f == 'entegrasyonlar.html': ent.append((f, 'Tüm entegrasyonlar', 'Bağlanabilen ödeme, kargo, fatura ve mesaj hizmetleri'))
        elif var(f) and f in ENT: ent.append((f, ENT[f][0][0].upper() + ENT[f][0][1:], ENT[f][1].capitalize()))
    ent = [x for x in ent if x[0] != bf]
    gr = [('Birlikte okunacak rehberler', rel), ('Bu rehberin işine yarayan sektörler', sek), ('İlgili entegrasyonlar', ent)]
    degisen += yaz(bf, blok(bf, gr))
# 3) entegrasyon grup sayfalarına da sektör/rehber ilgili bölümü
ENT_REH = {
 'sanal-pos-entegrasyonu.html': ['kasa-ve-muhasebe', 'entegrasyon-baglama', 'yemek-siparisleri'], 'kargo-entegrasyonu.html': ['siparis-ve-kargo', 'etiket-tasarimi', 'toplu-fatura'],
 'e-fatura-e-arsiv-entegrasyonu.html': ['toplu-fatura', 'kasa-ve-muhasebe', 'entegrasyon-baglama'], 'muhasebe-erp-entegrasyonu.html': ['kasa-ve-muhasebe', 'toplu-fatura', 'entegrasyon-baglama'],
 'pazaryeri-entegrasyonu.html': ['pazaryerine-gonderme', 'urun-ekleme', 'xml-ile-urun-aktarma', 'menu-pazaryerine-gonderme'],
 'sms-whatsapp-eposta-entegrasyonu.html': ['randevu-ve-takvim', 'musteri-yonetimi', 'entegrasyon-baglama'], 'olcum-reklam-entegrasyonu.html': ['web-sitesi-duzenleme', 'alan-adi', 'entegrasyon-baglama'],
}
ENT_SEK = {'sanal-pos-entegrasyonu.html': ['dis-klinigi', 'kuafor', 'eticaret', 'spor-salonu'], 'kargo-entegrasyonu.html': ['eticaret', 'market', 'tekstil', 'cicekci'],
 'e-fatura-e-arsiv-entegrasyonu.html': ['muhasebe', 'oto-servis', 'eticaret', 'kombi'], 'muhasebe-erp-entegrasyonu.html': ['muhasebe', 'eticaret', 'market', 'oto-servis'],
 'pazaryeri-entegrasyonu.html': ['eticaret', 'market', 'lokanta', 'pastane'], 'sms-whatsapp-eposta-entegrasyonu.html': ['dis-klinigi', 'kuafor', 'klima', 'veteriner'],
 'olcum-reklam-entegrasyonu.html': ['emlakci', 'avukat', 'surucu-kursu', 'tadilat']}
for f in ENT:
    if not ok(f): continue
    rel = [(BK(r), BIL[BK(r)][1], '') for r in ENT_REH[f] if var(BK(r))]
    sek = [('sektor-%s.html' % s, '%s için web sitesi ve iş takibi' % AD[s], '') for s in ENT_SEK[f] if s in AD]
    diger = [(g, ENT[g][0][0].upper() + ENT[g][0][1:], '') for g in ENT if g != f and var(g)][:3]
    degisen += yaz(f, blok(f, [('İlgili kullanım rehberleri', rel), ('Bu entegrasyonu kullanan sektörler', sek), ('Diğer entegrasyonlar', diger)]))
print('değişen sayfa:', degisen)
# kırık link taraması
kirik = []
for f in glob.glob('*.html'):
    t = open(f, encoding='utf-8').read()
    for b in re.findall(r'<!--IB-->.*?<!--/IB-->', t, flags=re.S):
        for h in re.findall(r'href="(/[^"#?]*)', b):
            if h != '/' and not ok(h[1:]): kirik.append((f, h))
        if re.search(r'\+?90\s?5\d\d|0\s?5\d\d\s?\d{3}', b): kirik.append((f, 'TELEFON'))
        if 'href="/%s"' % f in b: kirik.append((f, 'KENDİNE LİNK'))
print('IB bölümlerinde sorun:', len(kirik), kirik[:5])
