#!/usr/bin/env python3
"""30 tema (v3): her tema kendi düzeni, menüsü, mobil barı, yazı tipi ve sektör araçlarıyla üretilir.
Çalıştır: python3 gen3.py  →  html/<slug>.html, ../panel/themes.json, ../site/themes.json, g3/manifest.json
Yer tutucular: demo telefon 0532 000 00 00 / 905320000000, demo firma adı, __API_URL__ (panel yayınlarken doldurur)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from g3 import base, tools, navs, heroes, sections, content
from g3.recipes import R
from g3.base import ic, lum, mix, face, stack, img64

OUT = os.path.join(HERE, 'html')

TOOL_LABEL = {'kod': 'Hata kodu', 'btu': 'BTU hesapla', 'bakim': 'Bakım takvimi', 'teshis': 'Sorun sihirbazı', 'kw': 'Kapasite', 'montaj': 'Montaj keşfi', 'tasarruf': 'Gider hesabı',
              'karar': 'Tamir mi yeni mi', 'belirti': 'Arıza rehberi', 'parca': 'Parça talebi', 'liste': 'Bakım listesi', 'teslim': 'Teslim fişi', 'saglik': 'Sağlık testi',
              'veri': 'Veri kurtarma', 'upgrade': 'Yükseltme', 'paket': 'Süre hesabı', 'kacak': 'Kaçak testi', 'damla': 'Damla hesabı', 'acil': 'Acil rehber', 'sure': 'İş süresi',
              'kesit': 'Kablo kesiti', 'maliyet': 'Elektrik gideri', 'sigorta': 'Sigorta seçici', 'depo': 'Depolama', 'kesif': 'Keşif sihirbazı', 'risk': 'Güvenlik testi',
              'sozlesme': 'Bakım planı', 'alarm': 'Alarm planı'}


def on_color(h):
    def L(c):
        v = [int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        v = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in v]
        return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]
    la = L(h)
    cw = 1.05 / (la + .05)
    cb = (la + .05) / (L('#111111') + .05)
    return '#ffffff' if cw >= cb else '#111111'


class X:
    def __init__(self, r):
        self.r = r
        self.c = content.SEC[r['sector']]
        self.nm, self.city = r['nm'], r['city']
        self.ilce = content.CITY[self.city]
        self.h = self.c['h'][r['hidx']]
        self._css, self._js, self.bodycls = {}, [], []
        self.tools = r['tools']
        self.tool_js, self.kb = [], None
        self._used_tool_css = False
        self.links = []

    def css(self, k, s):
        self._css.setdefault(k, s)

    def js(self, name):
        if name not in self._js:
            self._js.append(name)

    def ph(self, var='im', pos='center', cls='', style=''):
        return f'<div class="ph {cls}" style="--bi:var(--{var});--p:{pos};{style}" role="img" aria-label="{self.c["label"]} servisi görseli"></div>'

    def quickform(self, uid, title, sub):
        return sections.quickform(self, uid, title, sub)

    def tool(self, idx, variant='a', in_hero=False):
        key = self.tools[idx]
        uid = f'tool{idx}'
        h, j, t = tools.render(key, uid, variant)
        h = h.replace('ICON_' + t['ico'], ic(t['ico'], 22))
        if t['id'] == 'kod' and not self.kb:
            self.kb = key.split('.')[0]
        self.tool_js.append(j)
        h = h.replace('<article class="tl', f'<article data-dev="{self.c["label"]}" class="tl', 1)
        self.X_toolcss()
        if in_hero:
            h = f'<div id="arac">{h}</div>'
        return h, j, t

    def X_toolcss(self):
        self.css('tools', tools.TOOL_CSS)


def build(r):
    x = X(r)
    pal = r['pal']
    bg, ink, sf, dk, ac = pal
    dark = r.get('dark', False)
    on_ac = on_color(ac)
    ln = mix(ink, bg, .16 if not dark else .2)
    mut = mix(ink, bg, .62 if not dark else .66)
    # bağlantılar
    order = r['order']
    labels = {'svc': ('Hizmetler', '#hizmet'), 'proc': ('Süreç', '#surec'), 'proof': ('Yorumlar', '#yorum'), 'areas': ('Bölgeler', '#bolge'), 'price': ('Fiyatlar', '#fiyat'), 'faq': ('SSS', '#sss'), 'why': ('Neden biz', '#neden'), 'ba': ('Çalışmalarımız', '#once-sonra')}
    toolkey = tools.TOOLS[r['tools'][0]]['id']
    x.links = [('Hizmetler', '#hizmet'), (TOOL_LABEL.get(toolkey, 'Araç'), '#arac')]
    for tkn in order:
        if tkn in labels and labels[tkn] not in x.links and len(x.links) < 4:
            x.links.append(labels[tkn])
    x.links.append(('Randevu', '#randevu'))
    # gövde
    parts = [navs.nav(x), navs.drawer(x), heroes.hero(x)]
    names = {'svc': 'Hizmetler', 'proc': 'Nasıl çalışıyoruz', 'proof': 'Yorumlar', 'brands': 'Markalar', 'ba': 'Önce / Sonra', 'areas': 'Hizmet bölgeleri', 'why': 'Neden biz', 'price': 'Fiyatlar', 'faq': 'Sık sorulanlar', 'cta': 'Çağrı bandı', 'book': 'Randevu', 'info': 'İletişim', 'tool0': 'Araç', 'tool1': 'İkinci araç'}
    for tkn in order:
        if tkn == 'svc': h = sections.services(x, r['svc'])
        elif tkn == 'proc': h = sections.process(x, r['proc'])
        elif tkn == 'proof': h = sections.proof(x, r['proof'])
        elif tkn == 'brands': h = sections.brands(x, r['br'])
        elif tkn == 'ba': h = sections.before_after(x)
        elif tkn == 'areas': h = sections.areas(x)
        elif tkn == 'why': h = sections.why(x)
        elif tkn == 'price': h = sections.price(x, r['price'])
        elif tkn == 'faq': h = sections.faq(x, r['faq'])
        elif tkn == 'cta': h = sections.ctaband(x, r['cta_v'])
        elif tkn == 'book': h = sections.booking(x, r['book'])
        elif tkn == 'info': h = sections.info(x)
        elif tkn == 'tool0': h = sections.toolsec(x, 0, r['tv0'])
        elif tkn == 'tool1': h = sections.toolsec(x, 1, r['tv1'], alt=True)
        else: continue
        parts.append(navs.ed(names[tkn], h))
    parts += [navs.footer(x), navs.mbar(x)]
    # paylaşılan JS adları
    x.js('DRW')
    # yazı tipleri
    fonts = {r['fd'], r['fb']}
    if r.get('fm'): fonts.add(r['fm'])
    if r.get('em') and r['fd'] in ('playfair', 'newsreader'): fonts.add(r['fd'] + '-i')
    faces = ''.join(face(k) for k in sorted(fonts))
    fm = stack(r['fm']) if r.get('fm') else "ui-monospace,'SF Mono',Consolas,monospace"
    phf = r['phf']; pho = r['pho']; phm = r['phm']
    if dark:
        phf = 'grayscale(.4) contrast(1.06) brightness(.88)'
    elif sum(map(ord, r['slug'])) % 3 == 0:
        pho = f'color-mix(in srgb,{ac} 16%,transparent)'
    root = (f":root{{--bg:{bg};--ink:{ink};--sf:{sf};--dk:{dk};--ac:{ac};--on-ac:{on_ac};--ln:{ln};--mut:{mut};--r:{r['r']}px;--fd:{stack(r['fd'])};--fb:{stack(r['fb'])};--fm:{fm};"
            f"--hw:{r['hw']};--ht:{r['ht']};--hc:var(--ink);--fbg:{'var(--sf)' if dark else '#fff'};--phf:{phf};--pho:{pho};--phm:{'soft-light' if dark else phm};--navc:{r['navc']};--emi:{'italic' if r.get('em') else 'normal'};"
            f"--im:url(data:image/jpeg;base64,{img64(x.c['img'])});--im2:url(data:image/jpeg;base64,{img64(x.c['img'] + '2')});--im3:url(data:image/jpeg;base64,{img64(x.c['img'] + '3')})}}")
    skin = base.BTN[r['btn']] + base.CARD[r['card']] + base.FIELD[r['field']] + base.HEAD[r['head']]
    if r['hero'] == 'edit':
        skin += f"h1{{--hw1:{r['hw']}}}"
    css = faces + root + base.CORE + skin + ''.join(x._css.values())
    js = tools.RUNTIME + (f"var KB={tools.kb_json(x.kb)};" if x.kb else '') + ''.join(x.tool_js) + ''.join(sections.JS[n] for n in x._js)
    body_cls = ' '.join(x.bodycls)
    desc = f'{x.nm} — {x.city} {x.c["tag"]}. Randevu, yazılı fiyat ve garantili servis.'
    html = (f'<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{x.nm} · {x.c["label"]} servisi · {x.city}</title>'
            f'<meta name="description" content="{desc}"><meta name="theme-color" content="{dk}"><style>{css}</style></head><body class="{body_cls}"><input type="checkbox" id="mn" class="hid" aria-hidden="true">'
            + ''.join(parts) + f'<script>{js}</script></body></html>')
    return html, x


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith('.html'):
            os.remove(os.path.join(OUT, f))
    themes, manifest = [], []
    for r in R:
        html, x = build(r)
        open(os.path.join(OUT, r['slug'] + '.html'), 'w', encoding='utf-8').write(html)
        themes.append(dict(slug=r['slug'], sector=r['sector'], dark=r['pal'][3], accent=r['pal'][4], soft=r['pal'][2], radius=r['r'], name=r['nm']))
        manifest.append(dict(slug=r['slug'], sector=r['sector'], nm=r['nm'], city=r['city'], style=r['style'], hero=r['hero'], nav=r['nav'], mbar=r['mbar'], ft=r['ft'],
                             tools=[tools.TOOLS[t]['title'] for t in r['tools']], pal=list(r['pal']), fd=r['fd'], fb=r['fb'], dark=bool(r.get('dark')),
                             kb=len(html) // 1024))
        print(f"{r['slug']:24s} {r['hero']:8s} {r['nav']:7s} {r['mbar']:7s} {len(html) // 1024:4d} KB  {r['style']}")
    for p in (os.path.join(HERE, '..', 'panel', 'themes.json'), os.path.join(HERE, '..', 'site', 'themes.json')):
        json.dump(themes, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(manifest, open(os.path.join(HERE, 'g3', 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
