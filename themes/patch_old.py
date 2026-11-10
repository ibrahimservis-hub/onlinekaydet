"""Eski (önceden üretilmiş) temalara yeni modülleri ekler: duyuru+geri sayım, hikâye, mega menü, fırsatlar, paketler, kayarak belirme.
Dosyayı yeniden üretmez (fotoğraflar ve yazı tipleri korunur); aynı dosyaya ikinci kez uygulanmaz. Çalıştır: python3 patch_old.py [html klasörü]"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from g3 import content, modules


class _X:
    def __init__(self, sector, nav):
        self.c = content.SEC[sector]; self.r = {'sector': sector, 'nav': nav}; self._css = {}
    def css(self, k, s): self._css.setdefault(k, s)


def patch(html, sector):
    if 'id="firsat"' in html or sector not in content.SEC:
        return html, False
    nav = 'rail' if 'class="nv nv8' in html else ('min' if 'class="nv nv4' in html else 'x')
    x = _X(sector, nav)
    ed = '<div class="ed"'
    mn = html.index('id="mn" class="hid" aria-hidden="true">')
    mn = html.index('>', mn) + 1
    hi = html.find('<div class="ed" data-nm="Ana görsel"')
    after_hero = html.find(ed, hi + 10) if hi >= 0 else -1
    bi = html.find('<div class="ed" data-nm="Randevu"')
    if after_hero < 0 or bi < 0:
        return html, False
    ins = [(bi, modules.deals(x) + modules.packages(x)), (after_hero, modules.stories(x))]
    top = modules.mega(x) if nav != 'x' else modules.announce(x) + modules.mega(x)
    ins.append((mn, top))
    for pos, frag in sorted(ins, key=lambda t: -t[0]):
        html = html[:pos] + frag + html[pos:]
    html = html.replace('<section class="sec', '<section class="rv sec')
    html = html.replace('<section class="rv sec deal"', '<section class="sec deal"').replace('<section class="rv sec pk"', '<section class="sec pk"')
    html = html.replace('</style>', modules.CSS + '</style>', 1)
    k = html.rindex('</script></body>')
    return html[:k] + modules.JS + html[k:], True


def run(d, meta):
    n = 0
    for f in sorted(os.listdir(d)):
        slug = f[:-5]
        if not f.endswith('.html') or re.match(r'n\d\d-', f) or slug not in meta:
            continue
        p = os.path.join(d, f)
        h = open(p, encoding='utf-8').read()
        new, ok = patch(h, meta[slug])
        if ok:
            open(p, 'w', encoding='utf-8').write(new); n += 1
    return n


if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'html')
    app = os.environ.get('OK_APP_DIR') or os.path.join(HERE, '..', 'panel')
    meta = {t['slug']: t['sector'] for t in json.load(open(os.path.join(app, 'themes.json'), encoding='utf-8'))}
    print(run(d, meta), 'eski tema güncellendi')
