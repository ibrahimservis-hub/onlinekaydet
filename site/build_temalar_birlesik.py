# site/temalar-live.html: 420 yeni temayı ana galeriye (canlı önizleme küçük resimli) ve filtreye ekler, alttaki ayrı bölümü kaldırır.
import json, re, sys, html as H
sys.path.insert(0, 'panel')
import sektor
P = 'site/temalar-live.html'
s = open(P, encoding='utf-8').read()
th = json.load(open('panel/themes.json', encoding='utf-8'))
new = [t for t in th if re.match(r'n\d', t['slug'])]
assert len(new) == 420, len(new)
TECH = ['kombi', 'klima', 'beyaz_esya', 'elektronik', 'bilgisayar', 'tesisat', 'elektrik', 'guvenlik']
nm = lambda k: sektor.SECTORS[k]['name'].replace(' & ', ' ve ')
cnt = {}
for t in new: cnt[t['sector']] = cnt.get(t['sector'], 0) + 1
# 1) alttaki ayrı bölümü kaldır
y = s.find('id="yf"'); a = s.rfind('<section', 0, y); b = s.find('</section>', y) + len('</section>')
s = s[:a] + s[b:]
# 2) kartlar
def card(t):
    n = H.escape(t['name']); sn = nm(t['sector'])
    return ('<article class="tk" data-s="%s" data-p="%d" data-m="0" data-n="%s"><a class="tk-i" href="/tema-onizleme/%s.html" target="_blank" rel="noopener" aria-label="%s temasını yeni sekmede aç">%s<span class="tk-d tk-live"><iframe src="/tema-onizleme/%s.html" loading="lazy" tabindex="-1" scrolling="no" title="%s önizleme" data-live="1"></iframe></span><span class="tk-o">Temayı incele ↗</span></a><div class="tk-f"><div><b>%s</b><small>%s</small></div><a class="tk-b" href="index.html#kayit">Teklif alın</a></div></article>'
            % (t['sector'], 1 if t.get('premium') else 0, H.escape((t['name'] + ' ' + sn).lower()), t['slug'], n,
               '<span class="tk-bd">Premium</span>' if t.get('premium') else '', t['slug'], n, n, H.escape(sn)))
cards = ''.join(card(t) for t in sorted(new, key=lambda t: (nm(t['sector']), t['slug'])))
g = s.find('<div class="tk-gr">'); e = s.find('</article></div>', s.rfind('<article class="tk"')) 
e = s.find('</article>', s.rfind('<article class="tk"')) + len('</article>')
s = s[:e] + cards + s[e:]
# 3) kenar çubuğu
tot = 100 + 420; prem = 70 + sum(1 for t in new if t.get('premium')); std = tot - prem - 8
s = s.replace('<span>Tümü</span><em>100</em>', '<span>Tümü</span><em>%d</em>' % tot, 1)
s = s.replace('<span>Premium tema</span><em>70</em>', '<span>Premium tema</span><em>%d</em>' % prem, 1)
s = s.replace('<span>Standart tema</span><em>22</em>', '<span>Standart tema</span><em>%d</em>' % std, 1)
s = s.replace('<span>Tüm sektörler</span><em>100</em>', '<span>Tüm sektörler</span><em>%d</em>' % tot, 1)
add = ''.join('<label><input type="radio" name="tks" value="%s"><span>%s</span><em>%d</em></label>' % (k, H.escape(nm(k)), cnt[k]) for k in sorted(cnt, key=nm))
m = s.find('<span>Güvenlik</span><em>12</em></label>') + len('<span>Güvenlik</span><em>12</em></label>')
s = s[:m] + add + s[m:]
s = s.replace('<h3>Sektörler</h3>', '<h3>Sektörler (%d)</h3>' % (8 + len(cnt)), 1)
s = s.replace('<h2 class="r7-h2">100 tema, 8 sektör, 70 premium</h2>', '<h2 class="r7-h2">%d tema, %d sektör, %d premium</h2>' % (tot, 8 + len(cnt), prem), 1)
s = s.replace('Masaüstü ve mobil görünüm bir arada. Görsele tıklayın, tema yeni sekmede canlı açılsın.', 'Her kartta temanın canlı önizlemesi görünür. Tıklayın, tema yeni sekmede açılsın.', 1)
# 4) hero butonları
s = s.replace('<a class="btn" href="#temalar">Teknik servis temaları</a><a class="btn o" href="#yf">Diğer iş kolları (420 tema)</a>', '<a class="btn" href="#temalar">Temaları gör (%d)</a>' % tot, 1)
# 5) betik: üç kopya yerine tek, sayfalamalı
pat = re.compile(r"<script>\(function\(\)\{var q=document\.getElementById\('tkq'\).*?</script>", re.S)
assert len(pat.findall(s)) >= 1
s = pat.sub('', s)
js = r"""<script>(function(){var q=document.getElementById('tkq'),cs=[].slice.call(document.querySelectorAll('.tk')),no=document.getElementById('tkno'),sm=document.getElementById('tksum'),LIM=24,lim=LIM,bt=document.getElementById('tkmore');
function val(n){var e=document.querySelector('input[name='+n+']:checked');return e?e.value:''}
function ap(reset){if(reset)lim=LIM;var c=val('tkc'),s=val('tks'),t=(q.value||'').toLowerCase().trim(),k=0,sh=0;cs.forEach(function(e){var ok=(!s||e.dataset.s===s)&&(!t||e.dataset.n.indexOf(t)>=0)&&(c===''||(c==='p'&&e.dataset.p==='1')||(c==='m'&&e.dataset.m==='1')||(c==='s'&&e.dataset.p!=='1'&&e.dataset.m!=='1'));if(ok)k++;var vis=ok&&sh<lim;if(vis)sh++;e.hidden=!vis});no.style.display=k?'none':'block';sm.textContent=k+' tema listeleniyor';bt.hidden=k<=sh;bt.textContent='Daha fazla göster ('+(k-sh)+')';fit()}
function fit(){[].forEach.call(document.querySelectorAll('.tk-live'),function(b){var w=b.clientWidth;if(w){var f=b.firstChild;f.style.transform='scale('+(w/1280)+')'}})}
document.getElementById('tks').addEventListener('change',function(){ap(true)});q.addEventListener('input',function(){ap(true)});bt.addEventListener('click',function(){lim+=LIM;ap(false)});window.addEventListener('resize',fit);ap(true)})();</script>"""
s = s.replace('</main>', js + '</main>', 1)
s = s.replace('<div class="tk-no" id="tkno"', '<div class="tk-no" id="tkno"', 1)
no = s.find('id="tkno"'); ne = s.find('</div>', no) + 6
s = s[:ne] + '<button type="button" class="tk-more" id="tkmore" hidden>Daha fazla göster</button>' + s[ne:]
css = '.tk-live{aspect-ratio:8/5;background:#fff}.tk-live iframe{position:absolute;left:0;top:0;width:1280px;height:800px;border:0;transform-origin:0 0;pointer-events:none;background:#fff}.tk-more{display:block;margin:26px auto 0;background:#0a0c0f;color:#fff;border:0;border-radius:99px;padding:14px 26px;font:500 15px var(--f);cursor:pointer;min-height:48px}.tk-more[hidden]{display:none}#tks .tk-g:last-child{max-height:420px;overflow:auto}</style>'
s = s.replace('</style>', css, 1) if '.tk-live' not in s else s
open(P, 'w', encoding='utf-8').write(s)
print(len(s), s.count('class="tk"'), tot, prem, std)
