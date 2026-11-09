#!/usr/bin/env python3
"""Satış sitesi tema vitrini (site/v7/temalar.html): Ticimax tarzı — sol filtre, masaüstü + mobil görünüm, tıklayınca temayı yeni sekmede açar, fiyat yok ('Teklif alın')."""
import json, os, re, html
H = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(H, '..', 'panel', 'themes.json'), encoding='utf-8'))
M = {m['slug']: m for m in json.load(open(os.path.join(H, 'g3', 'manifest.json'), encoding='utf-8'))}
SEC = [('kombi', 'Kombi'), ('klima', 'Klima'), ('beyaz_esya', 'Beyaz eşya'), ('elektronik', 'Elektronik'), ('bilgisayar', 'Bilgisayar'), ('tesisat', 'Tesisat'), ('elektrik', 'Elektrik'), ('guvenlik', 'Güvenlik')]
SN = dict(SEC)
def card(t):
    m = M[t['slug']]; s = t['slug']; mag = 'magaza' in s; pr = bool(t.get('premium'))
    badge = '<span class="tk-bd">Premium</span>' if pr else ('<span class="tk-bd m">Online mağaza</span>' if mag else '')
    stil = m['style'].replace('Premium · ', '')
    return (f'<article class="tk" data-s="{t["sector"]}" data-p="{int(pr)}" data-m="{int(mag)}" data-n="{html.escape((m["nm"] + " " + SN[t["sector"]] + " " + stil).lower())}">'
            f'<a class="tk-i" href="/tema-onizleme/{s}.html" target="_blank" rel="noopener" aria-label="{html.escape(m["nm"])} temasını yeni sekmede aç">{badge}'
            f'<span class="tk-d"><img src="tema/{s}-k.webp" alt="{html.escape(m["nm"])} masaüstü görünümü" loading="lazy" width="640" height="400"></span>'
            f'<span class="tk-p"><img src="tema/{s}-i.webp" alt="{html.escape(m["nm"])} mobil görünümü" loading="lazy" width="404" height="838"></span><span class="tk-o">Temayı incele ↗</span></a>'
            f'<div class="tk-f"><div><b>{html.escape(m["nm"])}</b><small>{SN[t["sector"]]} · {html.escape(stil)}</small></div><a class="tk-b" href="index.html#kayit">Teklif alın</a></div></article>')
order = sorted(T, key=lambda t: (not t.get('premium'), 'magaza' in t['slug'], t['slug']))
n_all, n_pr = len(T), sum(1 for t in T if t.get('premium')); n_mg = sum(1 for t in T if 'magaza' in t['slug']); n_st = n_all - n_pr
cnt = {k: sum(1 for t in T if t['sector'] == k) for k, _ in SEC}
side = ('<aside class="tk-s" id="tks"><div class="tk-g"><h3>Ara</h3><input type="search" id="tkq" placeholder="Tema veya sektör ara…" aria-label="Tema ara"></div>'
        '<div class="tk-g"><h3>Kategori</h3>'
        f'<label><input type="radio" name="tkc" value="" checked><span>Tümü</span><em>{n_all}</em></label>'
        f'<label><input type="radio" name="tkc" value="p"><span>Premium tema</span><em>{n_pr}</em></label>'
        f'<label><input type="radio" name="tkc" value="s"><span>Standart tema</span><em>{n_st - n_mg}</em></label>'
        f'<label><input type="radio" name="tkc" value="m"><span>Online mağaza</span><em>{n_mg}</em></label></div>'
        '<div class="tk-g"><h3>Sektörler</h3><label><input type="radio" name="tks" value="" checked><span>Tüm sektörler</span><em>' + str(n_all) + '</em></label>'
        + ''.join(f'<label><input type="radio" name="tks" value="{k}"><span>{v}</span><em>{cnt[k]}</em></label>' for k, v in SEC) + '</div></aside>')
CSS = """<style>.tk-w{display:grid;grid-template-columns:260px minmax(0,1fr);gap:34px;align-items:start}.tk-s{position:sticky;top:96px;border:1px solid #cfc9ba;background:#fbf9f4;padding:8px 22px 18px}.tk-g{padding:14px 0;border-bottom:1px solid #e3ddcf}.tk-g:last-child{border:0}.tk-g h3{font:500 17px var(--f);margin:0 0 10px}
.tk-g label{display:flex;align-items:center;gap:10px;padding:7px 0;cursor:pointer;font-size:15.5px}.tk-g label span{flex:1}.tk-g label em{font-style:normal;color:var(--mut);font-size:13px}.tk-g input[type=radio]{appearance:none;width:18px;height:18px;border:1.5px solid #9a9486;border-radius:50%;margin:0;flex:none;display:grid;place-items:center;background:#fff}.tk-g input[type=radio]:checked{border-color:var(--chd);background:radial-gradient(var(--chd) 45%,#fff 48%)}
.tk-g input[type=search]{width:100%;min-height:46px;border:1px solid #cfc9ba;background:#fff;padding:8px 12px;font:400 15px var(--f);border-radius:0}.tk-g input:focus-visible{outline:2px solid var(--ch)}
.tk-gr{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:26px}.tk{background:#fbf9f4;border:1px solid #d6d0c2;transition:transform .35s var(--ease),box-shadow .35s var(--ease)}.tk:hover{transform:translateY(-5px);box-shadow:0 30px 56px -28px rgba(20,22,26,.45)}.tk[hidden]{display:none}
.tk-i{position:relative;display:block;aspect-ratio:8/5.6;overflow:hidden;background:linear-gradient(135deg,#e9e4d8,#d9d2c1)}.tk-d{position:absolute;left:5%;top:6%;width:84%;border-radius:8px;overflow:hidden;box-shadow:0 18px 40px -16px rgba(0,0,0,.5);border:1px solid #0002}.tk-d img{display:block;width:100%;height:auto;transition:transform .8s var(--ease)}
.tk-p{position:absolute;right:4%;bottom:-14%;width:23%;transition:transform .5s var(--ease);filter:drop-shadow(0 18px 22px rgba(0,0,0,.42))}.tk-p img{display:block;width:100%;height:auto}
.tk:hover .tk-p{transform:translateY(-14px)}.tk:hover .tk-d img{transform:scale(1.03)}
.tk-bd{position:absolute;left:12px;top:12px;z-index:3;background:#0a0c0f;color:var(--ch);font:600 11.5px var(--f);letter-spacing:.1em;text-transform:uppercase;padding:6px 11px;border-radius:99px}.tk-bd.m{color:#fff;background:#1f6f54}
.tk-o{position:absolute;inset:0;z-index:2;display:grid;place-items:center;background:rgba(10,12,15,.55);color:#fff;font:500 17px var(--f);opacity:0;transition:opacity .3s}.tk-i:hover .tk-o,.tk-i:focus-visible .tk-o{opacity:1}
.tk-f{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:16px 18px 18px;border-top:1px solid #d6d0c2}.tk-f b{display:block;font-weight:500;font-size:18px}.tk-f small{display:block;color:var(--mut);font-size:13.5px;margin-top:2px}.tk-f a.tk-b{flex:none;background:#0a0c0f;color:#fff !important;white-space:nowrap;padding:11px 16px;border-radius:99px;font:500 14px var(--f);transition:background .25s,transform .25s}.tk-f a.tk-b:hover{background:#2a2e35;transform:translateY(-2px)}
.tk-no{display:none;padding:40px;text-align:center;color:var(--mut);border:1px dashed #cfc9ba}.tk-sum{margin:0 0 16px;color:var(--mut);font-size:15px}
@media(max-width:1100px){.tk-gr{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:860px){.tk-w{grid-template-columns:minmax(0,1fr)}.tk-s{position:static;display:grid;grid-template-columns:1fr 1fr;gap:0 18px;padding:8px 16px 14px}.tk-s .tk-g:first-child{grid-column:1/-1}.tk-g{border-bottom:0}}
@media(max-width:560px){.tk-gr{grid-template-columns:minmax(0,1fr)}.tk-s{grid-template-columns:minmax(0,1fr)}.tk-f{flex-wrap:wrap}}
@media(prefers-reduced-motion:reduce){.tk,.tk-p,.tk-d img{transition:none}}</style>"""
JS = """<script>(function(){var q=document.getElementById('tkq'),cs=[].slice.call(document.querySelectorAll('.tk')),no=document.getElementById('tkno'),sm=document.getElementById('tksum');function val(n){var e=document.querySelector('input[name='+n+']:checked');return e?e.value:''}
function ap(){var c=val('tkc'),s=val('tks'),t=(q.value||'').toLowerCase().trim(),k=0;cs.forEach(function(e){var ok=(!s||e.dataset.s===s)&&(!t||e.dataset.n.indexOf(t)>=0)&&(c===''||(c==='p'&&e.dataset.p==='1')||(c==='m'&&e.dataset.m==='1')||(c==='s'&&e.dataset.p!=='1'&&e.dataset.m!=='1'));e.hidden=!ok;if(ok)k++});no.style.display=k?'none':'block';sm.textContent=k+' tema listeleniyor'}
document.getElementById('tks').addEventListener('change',ap);q.addEventListener('input',ap);ap()})();</script>"""
sec = ('<section class="r7-sec" id="temalar"><div class="o7w"><div class="r7-head"><span class="r7-k">Tüm temalar</span><h2 class="r7-h2">' + f'{n_all} tema, 8 sektör, {n_pr} premium' + '</h2>'
       '<p class="r7-p">Masaüstü ve mobil görünüm bir arada. Görsele tıklayın, tema yeni sekmede canlı açılsın. Fiyat için "Teklif alın" deyin.</p></div>'
       '<div class="tk-w">' + side + '<div><p class="tk-sum" id="tksum" aria-live="polite"></p><div class="tk-gr">' + ''.join(card(t) for t in order) + '</div><div class="tk-no" id="tkno">Aramanıza uygun tema bulunamadı.</div></div></div></div></section>' + CSS + JS)
p = os.path.join(H, '..', 'site', 'v7', 'temalar.html')
s = open(p, encoding='utf-8').read()
a = s.find('<section class="r7-sec" id="temalar">'); b = s.find('</section>', a) + len('</section>')
assert a > 0 and b > a
s = s[:a] + sec + s[b:]
s = re.sub(r'<script>\(function\(\)\{var f=document\.getElementById\("tf"\).*?</script>', '', s, flags=re.S)
s = s.replace('38 hazır tema', f'{n_all} hazır tema').replace('Servis web sitesi temaları: 38', f'Servis web sitesi temaları: {n_all}').replace('Sekiz sektör ve online mağaza için hazırlanmış 38 tema', f'Sekiz sektör ve online mağaza için hazırlanmış {n_all} tema ({n_pr} premium)')
s = s.replace('<div class="it"><b>38</b><span>hazır tema</span></div>', f'<div class="it"><b>{n_all}</b><span>hazır tema</span></div>').replace('<div class="it"><b>10</b><span>farklı düzen</span></div>', f'<div class="it"><b>{n_pr}</b><span>premium tema</span></div>')
s = re.sub(r'\b38 hazır', f'{n_all} hazır', s)
open(p, 'w', encoding='utf-8').write(s); print(n_all, n_pr, len(s))
