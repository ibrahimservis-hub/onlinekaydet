"""Yeni modüller: her tema hatasız açılır; sayaç işler, hikâye açılır, mega menü görünür, yatay kaydırma yok."""
import glob, os, sys
from playwright.sync_api import sync_playwright
H = os.path.join(os.path.dirname(__file__), '..', 'themes', 'html')
files = sorted(glob.glob(H + '/' + os.environ.get('PAT', 'n*') + '.html'))
bad = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for f in files:
        nm = os.path.basename(f)
        for w, hgt in ((1280, 800), (360, 740)):
            pg = b.new_page(viewport={'width': w, 'height': hgt}); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.goto('file://' + os.path.abspath(f)); pg.wait_for_timeout(250)
            r = pg.evaluate("""()=>({fir:!!document.querySelector('#firsat'),pak:!!document.querySelector('#paket'),st:document.querySelectorAll('.stq .st').length,
              tm:(document.querySelector('.deal .tm')||{}).textContent||'',sx:document.documentElement.scrollWidth>innerWidth+1,mega:!!document.querySelector('.mega')})""")
            if errs or not (r['fir'] and r['pak'] and r['st'] >= 4 and r['tm']) or r['sx']:
                bad.append((nm, w, errs[:1], r))
            if w == 1280 and not bad or w == 1280:
                pg.evaluate("document.querySelector('.stq .st').click()"); pg.wait_for_timeout(120)
                if not pg.evaluate("document.querySelector('.stv').classList.contains('on')"): bad.append((nm, 'story'))
            if w == 1280 and r['mega']:
                ok = pg.evaluate("""()=>{var a=[].slice.call(document.querySelectorAll('.nv nav a,header nav a')).filter(a=>['#hizmet','#urunler'].includes(a.getAttribute('href')))[0];
                  if(!a||!a.offsetParent)return 'skip';a.dispatchEvent(new MouseEvent('mouseenter'));return document.querySelector('.mega').classList.contains('on')}""")
                if ok is False: bad.append((nm, 'mega'))
            pg.close()
    b.close()
print(len(files), 'tema,', len(bad), 'sorun')
for x in bad[:12]: print(x)
sys.exit(1 if bad else 0)
