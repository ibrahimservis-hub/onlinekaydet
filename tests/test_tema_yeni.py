"""Yeni sektör temaları: sayfa hatasız açılır, her araç sonuç üretir, mağaza ürünlerinde görsel var, teknik servis dili kalmaz."""
import json, os, sys, glob
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
th = [t for t in json.load(open(os.path.join(ROOT, 'panel', 'themes.json'), encoding='utf-8')) if t['slug'].startswith('n') and t['slug'][1:3].isdigit()]
assert len(th) >= 48, len(th)
bad = []; seen_tools = set()
BANNED = ['Parça kodu', 'ustaya iletin', 'Usta atandı', 'garantili servis', 'yedek parça']
with sync_playwright() as p:
    b = p.chromium.launch()
    for t in th:
        f = os.path.join(ROOT, 'themes', 'html', t['slug'] + '.html'); html = open(f, encoding='utf-8').read()
        for w in BANNED:
            if w in html: bad.append((t['slug'], 'teknik dil: ' + w))
        pg = b.new_page(viewport={'width': 1280, 'height': 900}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('file://' + os.path.abspath(f)); pg.wait_for_timeout(300)
        if errs: bad.append((t['slug'], 'js hata: ' + errs[0][:100]))
        n = pg.evaluate("""()=>{var out=[];document.querySelectorAll('article.tl').forEach(function(a){var k=a.dataset.key;
            a.querySelectorAll('input[type=checkbox]').forEach(function(c,i){if(i<2){c.checked=true;c.dispatchEvent(new Event('change',{bubbles:true}))}});
            var d=a.querySelector('input[type=date]');if(d){d.value='2026-12-01';d.dispatchEvent(new Event('input',{bubbles:true}));d.dispatchEvent(new Event('change',{bubbles:true}))}
            var s=a.querySelector('select');if(s&&!s.value){s.selectedIndex=0}
            var r=a.querySelector('input[type=radio]');if(r){r.checked=true;r.dispatchEvent(new Event('change',{bubbles:true}))}
            if(s){s.dispatchEvent(new Event('change',{bubbles:true}))}
            var n=a.querySelector('input[type=number]');if(n){n.dispatchEvent(new Event('input',{bubbles:true}))}
            out.push([k,(a.querySelector('.rs')||{}).textContent.length])});return out}""")
        for k, ln in n:
            seen_tools.add(k)
            if ln < 5: bad.append((t['slug'], 'araç boş: ' + k))
        if t['sector'] in ('eticaret', 'tekstil', 'kuafor', 'guzellik'):
            pg.wait_for_timeout(200)
            c = pg.evaluate("document.querySelectorAll('#pg .pc svg.okpimg').length")
            if c < 4: bad.append((t['slug'], 'mağaza görseli yok: %d' % c))
        pg.close()
    b.close()
print('temalar', len(th), 'araçlar', len(seen_tools), sorted(seen_tools))
for x in bad[:30]: print('HATA', x)
sys.exit(1 if bad else 0)
