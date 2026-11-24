#!/usr/bin/env python3
"""Hız ve meta düzeltmeleri (idempotent): 4 CSS'i tek dosyada birleştirir, uzun başlıkları kısaltır, eksik description/canonical ekler."""
import re, glob, html, hashlib, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# 1) CSS birleştirme
parts = ['v9', 'v10', 'v11', 'v12']
css = '\n'.join(open('v9/%s.css' % p, encoding='utf-8').read() for p in parts)
open('v9/tum.css', 'w', encoding='utf-8').write(css)
ver = hashlib.md5(css.encode()).hexdigest()[:6]
LK = re.compile(r'<link rel="stylesheet" href="/v9/v9\.css[^>]*>\s*<link rel="stylesheet" href="/v9/v10\.css[^>]*>\s*<link rel="stylesheet" href="/v9/v11\.css[^>]*>\s*<link rel="stylesheet" href="/v9/v12\.css[^>]*>')
SM = open('sitemap.xml', encoding='utf-8').read()
nc = nt = nd = ncan = 0
for f in sorted(glob.glob('*.html')):
    t = open(f, encoding='utf-8').read(); o = t
    t, k = LK.subn('<link rel="stylesheet" href="/v9/tum.css?v=%s">' % ver, t); nc += k
    # 2) başlık
    m = re.search(r'<title>(.*?)</title>', t, re.S)
    if m:
        seg = m.group(1).split(' | ')
        ln = lambda s: len(html.unescape(' | '.join(s)))
        for drop in ('Bilgi Bankası', 'Hazır Tema', 'OnlineKaydet'):
            if ln(seg) > 65 and drop in seg[1:]: seg = [x for i, x in enumerate(seg) if i == 0 or x != drop]
        if ' | '.join(seg) != m.group(1):
            t = t.replace(m.group(0), '<title>%s</title>' % ' | '.join(seg), 1); nt += 1
    # 3) description / canonical
    noidx = re.search(r'<meta name="robots"[^>]*noindex', t)
    if '<meta name="description"' not in t and '</title>' in t:
        t = t.replace('</title>', '</title>\n<meta name="description" content="OnlineKaydet: web sitesi, e-ticaret, randevu ve iş takip programı. Ücretsiz deneyin.">', 1); nd += 1
    if 'rel="canonical"' not in t and not noidx and ('/' + f) in SM and '</title>' in t:
        t = t.replace('</title>', '</title>\n<link rel="canonical" href="https://onlinekaydet.com/%s">' % f, 1); ncan += 1
    if t != o: open(f, 'w', encoding='utf-8').write(t)
print('css', nc, 'baslik', nt, 'desc', nd, 'canonical', ncan)
