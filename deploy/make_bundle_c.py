#!/usr/bin/env python3
"""20 sinematik panel teması paketi: deploy/bundle_c.json (themes/html/c*.html + app/themes.json). Sunucu /api/admin/deploy ile uygular, restart:true."""
import os, json, glob
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
files = {}
for f in sorted(glob.glob(R + '/themes/html/c[0-9][0-9]-*.html')):
    files['themes/html/' + os.path.basename(f)] = open(f, encoding='utf-8').read()
files['app/themes.json'] = open(R + '/panel/themes.json', encoding='utf-8').read()
files['app/temafoto.py'] = open(R + '/panel/temafoto.py', encoding='utf-8').read()
json.dump({'files': files, 'edits': []}, open(R + '/deploy/bundle_c.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(len(files), os.path.getsize(R + '/deploy/bundle_c.json') // 1024, 'KB')
