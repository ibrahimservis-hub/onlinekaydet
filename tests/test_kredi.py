"""'OnlineKaydet ile yayınlanır' bağlantısı tüm temalarda, her koşulda onlinekaydet.com'a gider."""
import sys, os, glob, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import sitegen
ok = bad = 0
fails = []
def chk(name, h):
    global ok, bad
    out = sitegen.credit(h)
    n = len(re.findall(r'class="spx-credit"', out))
    good = n == 1 and 'href="https://onlinekaydet.com"' in out and out.count("Bu site OnlineKaydet ile yayınlanır") == 1
    if good: ok += 1
    else: bad += 1; fails.append((name, n))
for f in glob.glob(os.path.join(os.path.dirname(__file__), "..", "themes", "html", "*.html")):
    h = open(f, encoding="utf-8").read()
    chk(os.path.basename(f), h)                                                   # tema dosyası
    chk(os.path.basename(f) + " (yazı silinmiş)", _ := re.sub(r"Bu site OnlineKaydet ile yayınlanır", "", h))   # müşteri metni sildi
    chk(os.path.basename(f) + " (başka yazı)", h.replace("Bu site OnlineKaydet ile yayınlanır", "Bu site Firmam tarafından yapıldı"))
    chk(os.path.basename(f) + " (bağlantı bozuk)", h.replace("Bu site OnlineKaydet ile yayınlanır", '<a href="https://baska.com">Bu site OnlineKaydet ile yayınlanır</a>'))
once = sitegen.credit(sitegen.credit("<html><body><footer>x</footer></body></html>"))
assert once.count('class="spx-credit"') == 1, "iki kez çalışınca çoğalmamalı"
print("OK", ok, "FAIL", bad); [print(" ", x) for x in fails[:8]]
sys.exit(1 if bad else 0)
