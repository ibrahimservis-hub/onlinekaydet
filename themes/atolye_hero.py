"""Atölye ana görseli: premium temaların (hrp) ilk ekranını yeniden kurar.
Tema renklerini (--bg, --ink, --ac, --fd) kullanır; açık temada kâğıt, koyu temada koyu zemin olur. Dört yön dört ayrı kompozisyon:
edit = sağda kemerli fotoğraf, lux = sağda çerçeveli dikdörtgen, cine = solda taşan fotoğraf (aynalı), neon = yuvarlak köşeli büyük fotoğraf.
Metinleri uydurmaz: başlık, açıklama, düğmeler ve etiketler temanın kendi ilk ekranından okunur. Aynı dosyaya ikinci kez uygulanmaz.
Çalıştır: python3 atolye_hero.py [html klasörü]   |   kod içinden: apply(html) -> (html, değişti_mi)"""
import os, re, sys

CSS = r"""/* atolye */
.p2{position:relative;background:var(--bg);color:var(--ink);overflow:hidden;--p2l:color-mix(in srgb,var(--ink) 16%,transparent);--p2m:color-mix(in srgb,var(--ink) 62%,transparent)}
.p2 .p2w{width:min(1320px,100% - 48px);margin:auto;display:grid;grid-template-columns:minmax(0,1.08fr) minmax(0,.92fr);min-height:min(100svh,900px);padding-top:96px}
.p2 .p2l{display:flex;flex-direction:column;justify-content:space-between;padding:44px 48px 36px 0;border-right:1px solid var(--p2l)}
.p2 .p2k{display:flex;align-items:center;gap:12px;font:600 .72rem/1 var(--fb);letter-spacing:.22em;text-transform:uppercase}
.p2 .p2k:before{content:"";width:28px;height:2px;background:var(--ac)}
.p2 h1{font-family:var(--fd);font-weight:var(--hw,700);font-size:clamp(2.6rem,5.5vw,5.4rem);line-height:.94;letter-spacing:-.045em;margin:30px 0 0;color:var(--ink);text-wrap:balance;animation:p2u .9s cubic-bezier(.2,.8,.2,1) both}
.p2 h1 em{font-style:italic;font-weight:400;color:var(--ac);font-family:Georgia,'Times New Roman',serif;letter-spacing:-.02em}
.p2 .p2lead{font:400 clamp(1.02rem,1.3vw,1.2rem)/1.62 var(--fb);max-width:42ch;margin:26px 0 0;color:var(--p2m);animation:p2u .9s .15s cubic-bezier(.2,.8,.2,1) both}
.p2 .p2c{display:flex;flex-wrap:wrap;gap:10px;margin-top:32px;animation:p2u .9s .25s cubic-bezier(.2,.8,.2,1) both}
@keyframes p2u{from{opacity:0;transform:translateY(26px)}}
.p2 .p2b{display:inline-flex;align-items:center;gap:14px;min-height:56px;padding:0 10px 0 26px;border-radius:99px;background:var(--ink);color:var(--bg);font:700 .95rem var(--fb);transition:gap .3s}
.p2 .p2b span{width:38px;height:38px;border-radius:50%;background:var(--ac);color:var(--on-ac,#fff);display:grid;place-items:center;transition:transform .35s}
.p2 .p2b:hover{gap:20px}.p2 .p2b:hover span{transform:rotate(-45deg)}
.p2 .p2o{display:inline-flex;align-items:center;gap:10px;min-height:56px;padding:0 24px;border-radius:99px;border:1px solid var(--p2l);font:600 .95rem var(--fb);color:var(--ink)}
.p2 .p2g{display:grid;grid-template-columns:repeat(4,1fr);margin-top:44px;border-top:1px solid var(--p2l)}
.p2 .p2g div{padding:16px 12px 0 0}.p2 .p2g b{display:block;font:700 .7rem var(--fb);letter-spacing:.16em;color:var(--ac);margin-bottom:9px}
.p2 .p2g strong{display:block;font:600 1.02rem/1.2 var(--fd);letter-spacing:-.02em}.p2 .p2g small{display:block;margin-top:4px;font-size:.8rem;color:var(--p2m)}
.p2 .p2r{position:relative;padding:44px 0 36px 48px;display:flex;flex-direction:column}
.p2 .p2ph{position:relative;flex:1;min-height:440px;overflow:hidden;border-radius:calc(var(--r,12px)*1.6) calc(var(--r,12px)*1.6) 240px calc(var(--r,12px)*1.6);clip-path:inset(0 0 100% 0);animation:p2r 1.2s cubic-bezier(.7,0,.2,1) .2s forwards}
@keyframes p2r{to{clip-path:inset(0)}}
.p2 .p2ph .ph{position:absolute;inset:0;transform:scale(1.14);animation:p2z 2s cubic-bezier(.2,.8,.2,1) .2s forwards}@keyframes p2z{to{transform:scale(1.02)}}
.p2 .p2ph:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 60%,rgba(0,0,0,.45))}
.p2 .p2tag{position:absolute;left:18px;bottom:16px;z-index:2;color:#fff;font:600 .78rem var(--fb)}
.p2 .p2rg{position:absolute;left:12px;top:92px;z-index:3;width:128px;height:128px;border-radius:50%;background:var(--ac);color:var(--on-ac,#fff);display:grid;place-items:center}
.p2 .p2rg svg{position:absolute;inset:0;animation:p2s 22s linear infinite}.p2 .p2rg i{font:700 1.5rem var(--fd);font-style:normal}
@keyframes p2s{to{transform:rotate(360deg)}}
.p2 .p2n{display:flex;justify-content:space-between;align-items:flex-end;margin-top:16px;font:500 .78rem var(--fb);color:var(--p2m)}.p2 .p2n b{font:700 1rem var(--fd);color:var(--ink)}
.p2 .p2ph0{background:var(--ac);color:var(--on-ac,#fff);display:flex;flex-direction:column;justify-content:flex-end;padding:30px;animation-name:p2r}
.p2 .p2ph0:before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(135deg,transparent 0 22px,rgba(255,255,255,.07) 22px 23px)}
.p2 .p2ph0:after{display:none}
.p2 .p2big{position:relative;font:var(--hw,700) clamp(2.8rem,6.4vw,6.2rem)/.9 var(--fd);letter-spacing:-.045em;overflow-wrap:anywhere;text-transform:none}
.p2 .p2big small{display:block;margin-top:18px;font:600 .74rem/1 var(--fb);letter-spacing:.2em;text-transform:uppercase;opacity:.8}
.p2 .p2ph0 .p2tag{display:none}
/* yönler */
.p2-lux h1{font-weight:300;letter-spacing:-.025em}.p2-lux .p2ph{border-radius:2px;outline:1px solid var(--ac);outline-offset:12px}.p2-lux .p2b,.p2-lux .p2o{border-radius:0;letter-spacing:.14em;text-transform:uppercase;font-size:.76rem}.p2-lux .p2b span{border-radius:0}.p2-lux .p2rg{border-radius:0;width:104px;height:104px;transform:rotate(0)}
.p2-neon .p2ph{border-radius:44px}.p2-neon .p2rg{left:auto;right:-6px}
.p2-cine .p2w{grid-template-columns:minmax(0,.95fr) minmax(0,1.05fr)}.p2-cine .p2l{order:2;padding:44px 0 36px 48px;border-right:0;border-left:1px solid var(--p2l)}.p2-cine .p2r{order:1;padding:0 0 36px;margin-left:calc(50% - 50vw)}
.p2-cine .p2ph{border-radius:0 0 0 0;margin-top:0}.p2-cine .p2rg{left:28px;top:auto;bottom:96px}.p2-cine .p2n{padding-left:calc(50vw - 50% )}
@media(max-width:900px){.p2 .p2w{grid-template-columns:1fr;padding-top:76px;width:calc(100% - 36px)}.p2 .p2l,.p2-cine .p2l{border:0;padding:20px 0 6px;order:1}.p2 .p2r,.p2-cine .p2r{padding:8px 0 26px;order:2;margin-left:0}
.p2 .p2ph{min-height:340px;border-radius:18px 18px 120px 18px}.p2-lux .p2ph{border-radius:2px}.p2-neon .p2ph{border-radius:30px}.p2-cine .p2ph{border-radius:18px}.p2 .p2rg,.p2-cine .p2rg,.p2-neon .p2rg{width:92px;height:92px;top:auto;left:auto;right:12px;bottom:66px}.p2-cine .p2n{padding-left:0}
.p2 .p2g{grid-template-columns:1fr 1fr;row-gap:12px}.p2 .p2c>*{flex:1 1 100%;justify-content:space-between}}
@media(prefers-reduced-motion:reduce){.p2 *{animation:none!important;clip-path:none!important}}
/* menü ilk ekranda tema renginde */
.p2on .pnv:not(.sc){color:var(--ink)}.p2on .pnv:not(.sc) .bgr{color:var(--ink)}.p2on .pnv-neon:not(.sc) .in{background:color-mix(in srgb,var(--bg) 70%,transparent);border-color:var(--p2l,#8884)}
"""

_TEL = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/></svg>'
_SEC = re.compile(r'<section class="hr hrp[^"]*" id="top2">.*?</section>', re.S)
_GUV = [('01', 'Ücretsiz', 'keşif ve ön bilgi'), ('02', 'Yazılı', 'fiyat, işten önce'), ('03', 'İmzalı', 'servis fişi, SMS ile'), ('04', 'Garantili', 'yapılan işe belge')]


def _dir(html):
    m = re.search(r'<body[^>]*class="[^"]*\bpm-(cine|edit|neon|lux)\b', html)
    return m.group(1) if m else 'edit'


def _stats(html):
    """Temanın kendi güven maddeleri (rakam kutuları) varsa onlar; yoksa ortak dört söz."""
    m = re.search(r'<section class="(?:pst|hr hrp he)[^"]*".*?</section>', html, re.S)
    if m:
        cells = re.findall(r'<div><b[^>]*>([^<]+)</b><small>([^<]+)</small></div>', m.group(0))
        if len(cells) == 4 and not any(re.search(r'\d', c[0]) for c in cells):
            return [('%02d' % (i + 1), a, b) for i, (a, b) in enumerate(cells)]
    return _GUV


def _photo(html, var):
    m = re.search(re.escape(var) + r':url\(data:image/([a-z+]+);base64,(/9j/)?', html)
    return bool(m and m.group(1) == 'jpeg' and m.group(2))


def _panel(html, var, label, city):
    """Gerçek fotoğraf varsa fotoğraf; yoksa tema renginde yazı paneli (boş gri kutu ya da çizim yerine). Fotoğraf inince otomatik fotoğrafa döner."""
    if _photo(html, var):
        return ('<div class="p2ph"><div class="ph" style="--bi:var(%s);--p:center;" role="img" aria-label="%s görseli"></div><span class="p2tag">Randevu ile hizmet</span></div>' % (var, label))
    return '<div class="p2ph p2ph0"><div class="p2big">%s<small>%s</small></div></div>' % (label, (city + ' · ') + 'Randevu ile hizmet' if city else 'Randevu ile hizmet')


def hero(html):
    m = _SEC.search(html)
    if not m:
        return html, False
    h = m.group(0)
    im = re.search(r'--bi:var\((--im\d?)\)', h)
    eb = re.search(r'class="(?:eyebrow|k)">([^<]+)<', h)
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    lead = re.search(r'<p class="lead"[^>]*>(.*?)</p>', h, re.S)
    cta = re.search(r'<a class="btn" href="#randevu">([^<]+?)\s*<svg', h)
    tel = re.search(r'href="tel:\+(\d+)"[^>]*>.*?</svg>\s*([^<]+)</a>', h, re.S)
    if not (im and eb and h1 and lead and cta and tel):
        return html, False
    parts = [x.strip() for x in eb.group(1).split('·')]
    label, city = parts[0], (parts[1] if len(parts) > 1 else '')
    ring_t = (label + ' · ' + (city + ' · ' if city else '') + 'RANDEVU İLE · ').upper()
    ring = ('<svg viewBox="0 0 128 128" aria-hidden="true"><defs><path id="p2c" d="M64,64 m-48,0 a48,48 0 1,1 96,0 a48,48 0 1,1 -96,0"/></defs>'
            '<text font-size="10.5" font-weight="700" letter-spacing="2.6" fill="currentColor"><textPath href="#p2c">%s</textPath></text></svg>' % ring_t)
    g = ''.join('<div><b>%s</b><strong>%s</strong><small>%s</small></div>' % t for t in _stats(html))
    d = _dir(html)
    sec = ('<section class="hr p2 p2-%s" id="top2"><div class="p2w"><div class="p2l"><div><div class="p2k">%s%s</div><h1>%s</h1><p class="p2lead">%s</p>'
           '<div class="p2c"><a class="p2b" href="#randevu">%s<span>→</span></a><a class="p2o" href="tel:+%s">%s %s</a></div></div><div class="p2g">%s</div></div>'
           '<div class="p2r">%s'
           '<div class="p2rg">%s<i>↓</i></div><div class="p2n"><span>%s<br><b>%s</b></span><span>Aşağı kaydırın</span></div></div></div></section>'
           % (d, label, (' · ' + city) if city else '', h1.group(1), lead.group(1), cta.group(1).strip(), tel.group(1), _TEL, tel.group(2).strip(), g,
              _panel(html, im.group(1), label, city), ring, label + ' hizmeti', (city + ' ve çevresi') if city else ''))
    html = html.replace(h, sec, 1)
    html = html.replace('</style>', CSS + '</style>', 1)
    html = re.sub(r'(<body[^>]*class=")', r'\1p2on ', html, count=1)
    return html, True


def apply(html):
    if 'class="hr p2 ' in html:
        return html, False
    return hero(html)


if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html')
    n = k = 0
    for f in sorted(os.listdir(d)):
        if not f.endswith('.html'):
            continue
        p = os.path.join(d, f)
        s = open(p, encoding='utf-8').read()
        s2, ch = apply(s)
        if ch:
            open(p, 'w', encoding='utf-8').write(s2); n += 1
        elif 'class="hr p2 ' not in s:
            k += 1
    print('değişen', n, 'atlanan', k)
