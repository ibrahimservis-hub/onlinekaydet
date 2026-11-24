#!/usr/bin/env python3
"""<img> etiketlerine eksik width/height ekler (gerçek dosya boyutundan), ilk görsel hariç loading=lazy ekler. İdempotent."""
import re, os, glob
from PIL import Image
os.chdir(os.path.dirname(os.path.abspath(__file__)))
cache = {}
def dim(src):
    p = src.split('?')[0].split('#')[0]
    if not p.startswith('/'): return None
    if p in cache: return cache[p]
    try:
        with Image.open('.' + p) as im: cache[p] = im.size
    except Exception: cache[p] = None
    return cache[p]
n = 0
for f in glob.glob('*.html'):
    t = open(f, encoding='utf-8').read(); o = t; cnt = [0]
    def fix(m):
        tag = m.group(0); cnt[0] += 1
        s = re.search(r'\ssrc="([^"]+)"', tag)
        if s and not re.search(r'\swidth=', tag) and not re.search(r'\sheight=', tag):
            d = dim(s.group(1))
            if d: tag = tag[:-1].rstrip('/').rstrip() + ' width="%d" height="%d">' % d
        if cnt[0] > 1 and 'loading=' not in tag:
            tag = tag[:-1].rstrip('/').rstrip() + ' loading="lazy">'
        return tag
    t = re.sub(r'<img\b[^>]*>', fix, t)
    if t != o: open(f, 'w', encoding='utf-8').write(t); n += 1
print(n, 'sayfa')
