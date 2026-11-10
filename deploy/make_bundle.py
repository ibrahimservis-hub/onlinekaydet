#!/usr/bin/env python3
"""Sunucuya GitHub üzerinden uygulanacak paketi (deploy/bundle.json) üretir. Sunucu /api/admin/deploy ile indirir.
Paket: {"files": {yol: metin}, "edits": [{path, old, new}]}; yollar 'app/' ve 'themes/' ile başlar."""
import os, re, json, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
rd = lambda p: open(os.path.join(R, p), encoding='utf-8').read()
files, edits = {}, []
for f in ('sektor_ek.py', 'sektor.py', 'demo.py', 'sitegen.py', 'storefront.py', 'ilan.py', 'sektor_mod.py', 'sektor_dil.py', 'sektor_cok.py', 'sektor_cok2.py', 'shopdetail.py', 'urunsayfa.py', 'realimg.py', 'themefix.py', 'siteedit.py', 'sahip.py', 'server.py', 'themes.json'):
    files['app/' + f] = rd('panel/' + f)
for f in ('gen3.py', 'gen4.py', 'patch_old.py', 'fetch_photos.py', 'ill/make_ill.py'):
    files['themes/' + f] = rd('themes/' + f)
for f in sorted(os.listdir(os.path.join(R, 'themes/g3'))):
    if f.endswith('.py'):
        files['themes/g3/' + f] = rd('themes/g3/' + f)
import json as _j
SITE_FILES = _j.load(open(os.path.join(R,'deploy','site_files.json'))) if os.path.exists(os.path.join(R,'deploy','site_files.json')) else {}
for k, v in SITE_FILES.items():
    files['docroot/' + k] = rd(v)
files['app/public_panel/panel-ek.js'] = rd('panel/public_panel/panel-ek.js')
ek = rd('panel/public_panel/panel-ek.js')
blk = ek[ek.index('/* ---------- Sektör dili:'):]
if False: edits.append({'path': 'app/public_panel/panel-ek.js', 'old': "    if (h1) { strip(h1); note(); }\n  }\n  setInterval(tick, 500);\n})();", 'new': "    if (h1) { strip(h1); note(); }\n  }\n  setInterval(tick, 500);\n})();\n\n" + blk.rstrip('\n')})
if False: edits.append({'path': 'app/server.py', 'old': "import demo\ndemo.register(", 'new': "import sektor as _sektor\n_sektor.register(api_router, db, {\"get_current_user\": get_current_user})\nimport demo\ndemo.register("})
json.dump({'files': files, 'edits': edits}, open(os.path.join(R, 'deploy', 'bundle.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(len(files), 'dosya', len(edits), 'düzenleme')
