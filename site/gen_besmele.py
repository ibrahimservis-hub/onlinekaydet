#!/usr/bin/env python3
"""Her sayfanın kaynak kodunun başına (doctype'tan hemen sonra) görünmeyen besmele ve bereket duası yorumu ekler. İdempotent; ziyaretçi görmez."""
import glob, re
YORUM = ('<!-- ﷽ Bismillâhirrahmânirrahîm. '
         'اللَّهُمَّ بَارِكْ لَنَا فِي رِزْقِنَا وَ اجْعَلْ هَذَا الْعَمَلَ خَالِصًا لِوَجْهِكَ الْكَرِيمِ. '
         'Allahümme bârik lenâ fî rızkınâ; bu işi hayırlı, bereketli ve helâl kazanç vesilesi eyle. Âmîn. -->')
n = 0
for f in glob.glob('*.html'):
    t = open(f, encoding='utf-8').read()
    t0 = re.sub(r'(<!doctype html>)\s*<!-- ﷽.*?-->', r'\1', t, count=1, flags=re.S | re.I)
    m = re.match(r'\s*<!doctype html>', t0, re.I)
    if not m: continue
    t1 = t0[:m.end()] + '\n' + YORUM + t0[m.end():]
    if t1 != t: open(f, 'w', encoding='utf-8').write(t1); n += 1
print(n, 'sayfa')
