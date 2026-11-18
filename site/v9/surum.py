# -*- coding: utf-8 -*-
"""Tüm sayfalarda CSS/JS bağlantılarına sürüm eki koyar (tarayıcı önbelleği eski stille kalmasın). Tekrar çalıştırılabilir."""
import re, glob, os, sys
V = sys.argv[1] if len(sys.argv) > 1 else '1119b'
S = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
pat = re.compile(r'((?:href|src)="/v9/(?:v9|v10|v11|v12|eski-[a-z0-9]+)\.(?:css|js))(?:\?v=[^"]*)?"')
n = 0
for f in glob.glob(S + '/*.html'):
    h = open(f, encoding='utf-8').read()
    g = pat.sub(lambda m: m.group(1) + '?v=' + V + '"', h)
    if g != h:
        open(f, 'w', encoding='utf-8').write(g); n += 1
print('sürüm eki:', n, 'sayfa')
