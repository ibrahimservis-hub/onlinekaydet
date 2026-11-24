#!/usr/bin/env python3
"""77 sektör sayfasına, panelin kendi sektör verisinden (arızalar, kontrol listesi, terimler, belge başlığı) 3-4 ek SSS ekler. Tekrar çalıştırılabilir."""
import os, re, sys, json, glob, html
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
sys.path.insert(0, os.path.join(D, '..', 'panel'))
import sektor, sektor_ek
S = dict(sektor.SECTORS)
for k, v in sektor_ek.NEW.items():
    S.setdefault(k, {}); S[k] = {**S[k], **v}
e = lambda t: html.escape(t, quote=False)
def liste(x, n=8):
    x = [str(i) for i in x][:n]
    return x[0] if len(x) == 1 else ', '.join(x[:-1]) + ' ve ' + x[-1]
def sorular(v):
    ad = v['name']; q = []
    if v.get('faults'):
        q.append(('%s için kayıt açarken hangi arızalar hazır geliyor?' % ad, 'Panelde şu arıza seçenekleri hazır gelir: %s.' % liste(v['faults'])))
    if v.get('checklist'):
        q.append(('%s işinde teslim alırken hangi kontroller listelenir?' % ad, 'Kontrol listesinde şunlar yer alır: %s.' % liste([c[0] if isinstance(c, (list, tuple)) else c for c in v['checklist']])))
    t = v.get('terms')
    if t:
        ornek = ['%s ekranı “%s”' % (a, b) for a, b in list(t.items())[:3] if a != b]
        if ornek: q.append(('Panelde %s sektörünün kendi terimleri kullanılır mı?' % ad, 'Evet. Örneğin %s adıyla görünür.' % liste(ornek)))
    if v.get('pdf_title'):
        s = v.get('servis') or {}
        foto = {'zorunlu': 'zorunludur', 'istege_bagli': 'isteğe bağlıdır'}.get(s.get('foto_once'))
        cevap = 'Yazdırılan belgenin başlığı sektöre göre “%s” olarak basılır.' % v['pdf_title']
        if foto: cevap += ' Teslim alırken fotoğraf çekmek bu sektörde %s.' % foto
        q.append(('%s için yazdırılan belge nasıl adlandırılır?' % ad, cevap))
    return q
def isle(fn):
    key = os.path.basename(fn)[7:-5].replace('-', '_')
    v = S.get(key)
    if not v: return 0
    s = open(fn, encoding='utf-8').read()
    s = re.sub(r'<!--SSSEK-->.*?<!--/SSSEK-->', '', s, flags=re.S)
    s = re.sub(r'<script type="application/ld\+json" data-sssek>.*?</script>', '', s, flags=re.S)
    q = sorular(v)
    if not q or 'id="sss"' not in s: return 0
    i = s.index('id="sss"'); end = s.index('</section>', i)
    if '</details>' not in s[i:end]: return 0
    j = s.rindex('</details>', i, end) + len('</details>')
    ek = '<!--SSSEK-->' + ''.join('<details><summary>%s</summary><p>%s</p></details>' % (e(a), e(b)) for a, b in q) + '<!--/SSSEK-->'
    s = s[:j] + ek + s[j:]
    # JSON-LD FAQPage: mevcut soruların sonuna ekle (önceki ekleri temizle)
    def ld(m):
        d = json.loads(m.group(1))
        g = d['@graph'] if isinstance(d, dict) and '@graph' in d else [d] if isinstance(d, dict) else d
        for x in g:
            if x.get('@type') == 'FAQPage':
                ana = [m_ for m_ in x['mainEntity'] if not m_.get('_ek')]
                x['mainEntity'] = ana + [{'@type': 'Question', 'name': a, 'acceptedAnswer': {'@type': 'Answer', 'text': b}, '_ek': 1} for a, b in q]
        return m.group(0).split('>')[0] + '>' + json.dumps(d, ensure_ascii=False) + '</script>'
    s = re.sub(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', lambda m: ld(m) if 'FAQPage' in m.group(1) else m.group(0), s, flags=re.S)
    if 'FAQPage' not in s:
        a = s.index('id="sss"'); sec = s[a:s.index('</section>', a)]
        qa = re.findall(r'<summary>(.*?)</summary><p>(.*?)</p>', sec, re.S)
        if qa:
            f = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': html.unescape(x), 'acceptedAnswer': {'@type': 'Answer', 'text': html.unescape(re.sub(r'<[^>]+>', '', y))}} for x, y in qa]}
            s = s.replace('</head>', '<script type="application/ld+json" data-sssek>%s</script></head>' % json.dumps(f, ensure_ascii=False), 1)
    s = s.replace(', "_ek": 1', '').replace('"_ek": 1, ', '')
    open(fn, 'w', encoding='utf-8').write(s); return len(q)
if __name__ == '__main__':
    n = [isle(f) for f in sorted(glob.glob('sektor-*.html'))]
    print(sum(1 for x in n if x), 'sayfa,', sum(n), 'soru; atlanan:', sum(1 for x in n if not x))
