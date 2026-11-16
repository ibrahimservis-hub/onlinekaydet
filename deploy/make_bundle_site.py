#!/usr/bin/env python3
"""Yeni ana sayfa (v9) paketi: deploy/bundle_site.json. Sunucu /api/admin/deploy ile uygular (docroot/ altına yazar; görseller base64)."""
import os, json, base64
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')); S = R + '/site'
files = {}
def txt(rel): files['docroot/' + rel] = open(S + '/' + rel, encoding='utf-8').read()
def bin_(rel): files['docroot/' + rel] = {'b64': base64.b64encode(open(S + '/' + rel, 'rb').read()).decode()}
for rel in ('index.html', 'temalar.html', 'e-ticaret.html', 'web-sitesi.html', 'is-takibi.html', 'fiyatlar.html', 'sektorler.html', 'sss.html', 'ozellikler.html', 'hakkimizda.html', 'iletisim.html', 'v9/v9.css', 'v9/v10.css', 'v9/v9.js', 'v9/v10.js', 'lead.js', 'sitemap.xml', 'robots.txt'): txt(rel)
for d, ext in (('v9/img', '.webp'), ('v9/fonts', '.woff2')):
    for f in sorted(os.listdir(S + '/' + d)):
        if f.endswith(ext): bin_(d + '/' + f)
for rel in ('logo-acik-s.png', 'logo-renkli-s.png', 'og-kart.png'): bin_(rel)
json.dump({'files': files, 'edits': []}, open(R + '/deploy/bundle_site.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(len(files), 'dosya', os.path.getsize(R + '/deploy/bundle_site.json') // 1024, 'KB')
