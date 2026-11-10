#!/usr/bin/env python3
"""Teknik olmayan sektörler için tema üretici (oto servis, çekici, kuaför, nakliye, tekstil, e-ticaret, temizlik, güzellik).
gen3'ün bileşenlerini kullanır; yalnızca yeni sektörlerin temalarını yazar, mevcutlara dokunmaz.
Çalıştır: python3 gen4.py  ->  html/<slug>.html + ../panel/themes.json ve ../site/themes.json (yeni girişler eklenir, tekrar çalıştırınca çoğalmaz)."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import gen3
from g3 import content, content_ek, tools, tools_ek, shop, recipes_p
from g3.recipes import mk

content.SEC.update(content_ek.SEC)
tools.TOOLS.update(tools_ek.TOOLS)
shop.PRODUCTS.update(content_ek.PRODUCTS)
gen3.TOOL_LABEL.update({'bakim': 'Bakım takvimi', 'kontrol': 'Acil mi?', 'varis': 'Varış süresi', 'acil': 'Yolda kaldım', 'sure': 'Süre hesabı', 'rehber': 'Bakım rehberi', 'hacim': 'Taşıma hesabı',
                        'liste': 'Hazırlık listesi', 'metraj': 'Kumaş metrajı', 'surec': 'Sipariş süreci', 'kargo': 'Kargo eşiği', 'iade': 'İade rehberi', 'paket': 'Seans takibi', 'cilt': 'Cilt rehberi'})

NEW = list(content_ek.SEC)
TOOLS_BY = {'oto_servis': ['oto.bakim', 'oto.kontrol'], 'oto_cekici': ['cek.varis', 'cek.acil'], 'kuafor': ['kuf.sure', 'kuf.rehber'], 'nakliye': ['nak.hacim', 'nak.liste'],
            'tekstil': ['tek.metraj', 'tek.surec'], 'eticaret': ['eti.kargo', 'eti.iade'], 'temizlik': ['tem.sure', 'tem.liste'], 'guzellik': ['guz.paket', 'guz.cilt']}
DIRS = {'oto_servis': ['neon', 'cine', 'neon', 'edit', 'cine', 'neon'], 'oto_cekici': ['cine', 'neon', 'cine', 'neon', 'edit', 'cine'], 'kuafor': ['lux', 'edit', 'lux', 'cine', 'edit', 'lux'],
        'nakliye': ['edit', 'cine', 'edit', 'neon', 'cine', 'edit'], 'tekstil': ['edit', 'lux', 'edit', 'cine', 'lux', 'neon'], 'eticaret': ['neon', 'edit', 'cine', 'edit', 'neon', 'lux'],
        'temizlik': ['edit', 'neon', 'edit', 'cine', 'neon', 'edit'], 'guzellik': ['lux', 'edit', 'lux', 'edit', 'cine', 'lux']}
NAMES = {
 'oto_servis': ['Usta Oto Servis', 'Dört Mevsim Oto', 'Motor Atölyesi', 'Yeşil Vites Oto', 'Hızlı Bakım Oto', 'Güven Oto Servis'],
 'oto_cekici': ['Yol Arkadaşı Çekici', 'Akın Oto Çekici', 'Gece Gündüz Çekici', 'Hızır Yol Yardım', 'Kuzey Çekici', 'Anadolu Oto Kurtarma'],
 'kuafor': ['Makas Kuaför', 'Ayna Kuaför', 'Tarak Berber', 'Lale Kuaför', 'Zarif Saç Tasarım', 'Usta Berber'],
 'nakliye': ['Güvenli Nakliyat', 'Anadolu Evden Eve', 'Hızlı Taşıma', 'Koli Nakliyat', 'Yuva Taşıma', 'Kolay Nakliyat'],
 'tekstil': ['İplik Tekstil', 'Dokuma Atölyesi', 'Mavi Konfeksiyon', 'Kumaş Dünyası', 'Ege Tekstil', 'Terzi Fabrika'],
 'eticaret': ['Sepet Mağaza', 'Nokta Butik', 'Dükkan Online', 'Bahar Butik', 'Köşe Mağaza', 'Pazar Yeri Butik'],
 'temizlik': ['Pırıl Temizlik', 'Berrak Temizlik', 'Tertemiz Hizmet', 'Işıltı Temizlik', 'Düzen Temizlik', 'Özen Temizlik'],
 'guzellik': ['Nilüfer Güzellik', 'Işıl Güzellik Salonu', 'Rüya Bakım Merkezi', 'Ten Estetik Salonu', 'Çiçek Güzellik', 'Sevgi Bakım'],
}
SHOP_ON = set(content_ek.SHOP_SECTORS)
PLAIN = {'eticaret', 'tekstil', 'kuafor', 'guzellik'}   # parça mağazası dili yok

# Genel bileşenlerdeki teknik servis dilini sektöre çevirir (sırayla uygulanır)
VOCAB_ALL = [('Bu sonucu ustaya iletin', 'Bu sonucu bize iletin'), (' servisi ·', ' ·'), ('Randevu, yazılı fiyat ve garantili servis.', 'Randevu ve yazılı bilgilendirme.'),
             ('randevulu, kayıtlı ve garantili hizmet', 'randevulu ve kayıtlı hizmet'), ('Randevulu servis', 'Randevulu hizmet'), ('Servis rehberi', 'Rehber'), ('Servis verdiğimiz markalar', 'Çalıştığımız alanlar'),
             ('Kayıtlı servis', 'Kayıtlı hizmet'), ('Garantili işçilik', 'Yazılı işçilik bilgisi'), ('Yazılı garanti', 'Yazılı teklif'), ('Servis fişi', 'İşlem kaydı'), ('Usta atandı', 'Ekip atandı'),
             ('İşlem sonunda imzalı servis fişi ve garanti belgesi verilir.', 'İşlem sonunda kayıt ve bilgilendirme verilir.'), ('Parça kodu veya cihaz modelinizle arayın. Fiyat ve stok bilgisi anlıktır; siparişten sonra sizi arayıp teyit ederiz.', 'Ürün adı ya da koduyla arayın. Fiyat ve stok bilgisi anlıktır; siparişten sonra sizi arayıp teyit ederiz.'),
             ('Parça kodu, ürün adı veya model ara…', 'Ürün adı ya da kod ara…'), ('Sadece parça', 'Standart teslimat'), ('Servis kaydına eklenen önce / sonra fotoğrafla', 'Önce / sonra fotoğrafla')]
VOCAB = {
 'oto_servis': [('Teşhis ve onarım', 'Muayene ve onarım')],
 'oto_cekici': [('Randevu', 'Çağrı'), ('Randevu al', 'Çağır'), ('Teklif alın', 'Hemen ara')],
 'kuafor': [('Teklif alın', 'Randevu al')],
 'nakliye': [('Randevu al', 'Keşif iste'), ('Randevu', 'Keşif')],
 'tekstil': [('Randevu al', 'Teklif iste'), ('Randevu', 'Teklif')],
 'eticaret': [('Randevu al', 'Sipariş ver'), ('Randevu', 'Sipariş'), ('Teklif alın', 'Alışverişe başla')],
 'temizlik': [('Randevu al', 'Keşif iste'), ('Randevu', 'Keşif')],
 'guzellik': [('Teklif alın', 'Randevu al')],
}


def recipes():
    out = []
    n = 0
    for sec in NEW:
        cnt = {}
        for i, dr in enumerate(DIRS[sec]):
            d = recipes_p.D[dr]; k = cnt.get(dr, 0); cnt[dr] = k + 1
            bg = d['bgs'][(k + n) % len(d['bgs'])]; ac = d['acs'][(n * 3 + k) % len(d['acs'])]; ink = d['ink']
            if d['dark']:
                pal = (bg, ink, recipes_p._mix(bg, '#ffffff', .07), recipes_p._mix(bg, '#000000', .35), ac)
            else:
                pal = (bg, ink, recipes_p._mix(bg, '#000000', .06), recipes_p._mix(ink, bg, .1), ac)
            fd = d['fd'][(k + i) % len(d['fd'])]; fb = d['fb'][(k * 2 + i) % len(d['fb'])]
            tl = TOOLS_BY[sec]
            order = list(recipes_p.ORDERS[(k + i) % 4])
            if dr == 'cine':
                order = [t for t in order if t != 'pmq']
            order = [t for t in order if t not in ('ba', 'brands', 'areas', 'price') or t == 'areas']
            if sec not in SHOP_ON:
                order = [t for t in order if t != 'shop']
            if 'tool1' not in order and 'tool0' in order:
                order.insert(order.index('tool0') + 2 if len(order) > order.index('tool0') + 2 else len(order), 'tool1')
            slug = f'n{n * 6 + i + 1:02d}-{dr}-{sec.replace("_", "-")}'
            out.append(mk(slug=slug, sector=sec, nm=NAMES[sec][i], city=recipes_p.CITIES[(n * 2 + i * 3) % 10], pal=pal, fd=fd, fb=fb, r=d['r'], btn=d['btn'], card=d['card'], field=d['field'],
                          logo=['sq', 'ci', 'ol', 'bar', 'tx'][(k + i) % 5] if dr != 'lux' else 'tx', em=(fd in ('playfair', 'newsreader') and dr in ('edit', 'lux')),
                          nav='premium', dir=dr, hero='p_' + dr, mbar=recipes_p.MBAR[(i + n) % 8], ft=recipes_p.FT[(k + i) % 4], hidx=(i + n) % 5, tools=tl, tv0='abcd'[(i + n) % 4], tv1='abcd'[(i + 1) % 4],
                          svc=recipes_p.SVC[dr][k % 3], proc=['line', 'cards', 'big', 'vert'][(i + k) % 4], proof=['cards', 'quote', 'wall'][(i + 2 * k) % 3], br=['wall', 'pills', 'ticker'][i % 3],
                          faq=['side', 'stack'][i % 2], book=['split', 'card', 'wizard', 'strip'][(i + k) % 4], order=order, hw=d['hw'], ht=d['ht'], dark=d['dark'], premium=True,
                          cta='Teklif alın', imv=['im', 'im2', 'im3'][(i + n) % 3], shopplain=sec in PLAIN, shopt='Ürünler',
                          head='tight' if dr in ('cine', 'neon') else ('light' if dr in ('edit', 'lux') else 'bold'), style=f'Premium · {d["lbl"]} · {sec.replace("_", " ")}'))
        n += 1
    return out


def main():
    os.makedirs(gen3.OUT, exist_ok=True)
    R = recipes(); themes = []
    for r in R:
        html, x = gen3.build(r)
        for a, b in VOCAB_ALL + VOCAB.get(r['sector'], []):
            html = html.replace(a, b)
        open(os.path.join(gen3.OUT, r['slug'] + '.html'), 'w', encoding='utf-8').write(html)
        themes.append(dict(slug=r['slug'], sector=r['sector'], dark=r['pal'][3], accent=r['pal'][4], soft=r['pal'][2], radius=r['r'], name=r['nm'], premium=True))
        print(f"{r['slug']:28s} {len(html) // 1024:5d} KB  {r['style']}")
    for p in (os.path.join(HERE, '..', 'panel', 'themes.json'), os.path.join(HERE, '..', 'site', 'themes.json')):
        cur = [t for t in json.load(open(p, encoding='utf-8')) if t['sector'] not in NEW]
        json.dump(cur + themes, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    print(len(themes), 'tema yazıldı')


if __name__ == '__main__':
    main()
