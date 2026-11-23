# site/NN/*.html içindeki ortak <style> ve <script> bloklarını dış dosyaya taşır (boyutu küçültür)
import re, glob, os, hashlib, collections
R = os.path.dirname(os.path.abspath(__file__)) + '/site'
SM = re.compile(r'<style>(.*?)</style>', re.S)
JM = re.compile(r'<script>(.*?)</script>', re.S)
for d in sorted(glob.glob(R + '/[0-9][0-9]')):
    fs = sorted(glob.glob(d + '/*.html'))
    if not fs: continue
    docs = {f: open(f, encoding='utf-8').read() for f in fs}
    for rx, ext, mk in ((SM, 'css', lambda n: '<link rel="stylesheet" href="%s">' % n), (JM, 'js', lambda n: '<script src="%s"></script>' % n)):
        cnt = collections.Counter()
        for t in docs.values():
            for b in set(rx.findall(t)):
                if len(b) > 3000: cnt[b] += 1
        for b, n in cnt.items():
            if n < 2: continue
            h = hashlib.md5(b.encode()).hexdigest()[:8]
            name = 'a-%s.%s' % (h, ext)
            open(d + '/' + name, 'w', encoding='utf-8').write(b)
            for f in docs:
                docs[f] = docs[f].replace(rx.pattern.replace('(.*?)', '') and ('<style>' if ext == 'css' else '<script>') + b + ('</style>' if ext == 'css' else '</script>'), mk(name))
    for f, t in docs.items(): open(f, 'w', encoding='utf-8').write(t)
print('ok')
