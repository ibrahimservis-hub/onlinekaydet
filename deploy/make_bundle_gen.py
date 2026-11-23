#!/usr/bin/env python3
"""Tema uretici + gercek foto + app dosyalari paketi: deploy/bundle_gen.json (docroot/themes/app)."""
import os, json, base64, glob
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
files = {}
t = lambda k, p: files.__setitem__(k, open(os.path.join(R, p), encoding='utf-8').read())
for f in ('demo.py', 'server.py', 'siparis.py', 'sitegen.py', 'yp_ui.html', 'sahip/index.html', 'kategori.py', 'shop.py', 'shop_sync.py', 'storefront.py', 'urun.py', 'urun_ayna.py'):
    t('app/' + f, 'panel/' + f)
for f in ('gen4.py', 'fetch_photos.py', 'ill/make_ill.py'):
    t('themes/' + f, 'themes/' + f)
for f in sorted(glob.glob(R + '/themes/g3/*.py')) + [R + '/themes/g3/demo_marks.json']:
    t('themes/g3/' + os.path.basename(f), 'themes/g3/' + os.path.basename(f))
files['themes/img/real.txt'] = 'real'
for f in sorted(glob.glob(R + '/themes/img/*.jpg')):
    files['themes/img/' + os.path.basename(f)] = {'b64': base64.b64encode(open(f, 'rb').read()).decode()}
json.dump({'files': files, 'edits': []}, open(R + '/deploy/bundle_gen.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(len(files), os.path.getsize(R + '/deploy/bundle_gen.json') // 1024, 'KB')
