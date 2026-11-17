"""tum-sektorler.html: 78 iş kolunu kategorilere ayırıp kart olarak listeler (sektor-*.html dosyalarından)."""
import re, os, glob, html
R = os.path.join(os.path.dirname(__file__), "..")
E = html.escape
CAT = [("Teknik servis ve tamir", "Servis kaydı, usta atama, imzalı fiş ve müşteriye SMS.",
        "kombi klima beyaz-esya bilgisayar elektrik elektronik guvenlik tesisat telefon-tamir yazici-servis asansor jenerator su-aritma cilingir ayakkabi-tamir kuyumcu-saat cam-dograma tadilat".split()),
       ("Oto ve ulaşım", "Randevu, iş emri, araç ve sefer takibi.", "oto-servis oto-cekici oto-yikama oto-kaplama lastikci nakliye kurye transfer arac-kiralama".split()),
       ("Güzellik ve bakım", "Randevu, personel takvimi ve paket satışı.", "kuafor guzellik tirnak-studyo estetik-merkezi spa-hamam dovme-studyo evcil-hayvan".split()),
       ("Sağlık ve danışmanlık", "Randevu, hasta ya da danışan kaydı, hatırlatma.", "psikolog diyetisyen fizyoterapi dis-klinigi veteriner aile-danisman avukat muhasebe mimar tercume emlakci optik".split()),
       ("Eğitim ve kurs", "Kayıt, ders programı ve ödeme takibi.", "surucu-kursu src-kursu etut-merkezi dil-okulu muzik-kursu anaokulu ozel-ders bilgisayar-kursu spor-salonu yoga-dans yuzme-kursu".split()),
       ("Yeme-içme ve satış", "Menü ya da ürün, sipariş ve pazaryeri bağlantısı.", "lokanta pastane catering market eticaret tekstil cicekci mobilya matbaa terzi".split()),
       ("Temizlik, bakım ve organizasyon", "Çağrı kaydı, ekip planı ve teklif.", "temizlik hali-yikama kuru-temizleme bocek-ilaclama havuz-bakim peyzaj gunes-enerjisi fotografci dj-muzik dugun-salonu tur-organizasyon".split())]
nm = {}
for f in glob.glob(os.path.join(R, "sektor-*.html")):
    k = os.path.basename(f)[7:-5]; s = open(f, encoding="utf-8").read()
    t = re.sub("<[^>]+>", "", re.search(r"<h1>(.*?)</h1>", s, re.S).group(1))
    t = re.sub(r" (için|servisi için|servisleri için).*$", "", t); t = re.sub(r" servisi$", "", t) if k in ("kombi", "klima", "beyaz-esya", "elektrik", "elektronik", "tesisat", "su-aritma") else t
    t = html.unescape(t).replace("Bilgisayar ve telefon servisi", "Bilgisayar servisi").replace("Güvenlik ve kamera servisi", "Güvenlik ve kamera")
    nm[k] = re.sub(r"\s*(için|takip programı)$", "", re.sub(r" için .*$", "", t)).strip()
used = [k for c in CAT for k in c[2]]
missing = set(nm) - set(used); extra = set(used) - set(nm)
assert not missing and not extra, (missing, extra)
o = ['<!--SLB--><style>.sl2{padding:8px 0 40px}.sl2 .ar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:0 0 26px}.sl2 input{font:inherit;padding:12px 16px;min-height:46px;border:1px solid #d5dbe4;border-radius:12px;min-width:min(100%%,320px);flex:1;max-width:460px}.sl2 .sy{color:#5b6677;font-size:14px}'
     '.sl2 .kt{margin:0 0 34px}.sl2 .kt h2{font-size:22px;margin:0 0 4px}.sl2 .kt>p{margin:0 0 14px;color:#5b6677;font-size:15px}.sl2 .kl{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}'
     '.sl2 .kk{border:1px solid #e1e6ee;border-radius:14px;padding:16px;background:#fff;display:flex;flex-direction:column;gap:10px}.sl2 .kk strong{font-size:16px}.sl2 .kk div{display:flex;flex-wrap:wrap;gap:8px 14px;font-size:14px}.sl2 .kk a{color:#26407a;text-decoration:underline;text-underline-offset:3px;min-height:24px}'
     '@media(max-width:560px){.sl2 .kl{grid-template-columns:1fr}}</style><section class="sl2" id="liste"><div class="w"><div class="ar"><input id="slq" type="search" placeholder="Meslek ara: kuaför, kombi, avukat…" aria-label="Meslek ara"><span class="sy" id="sls">%d iş kolu</span></div>' % len(nm)]
for ad, ac, ks in CAT:
    o.append('<div class="kt"><h2>%s</h2><p>%s</p><div class="kl">' % (E(ad), E(ac)))
    for k in ks:
        web = os.path.exists(os.path.join(R, k + "-web-sitesi.html"))
        o.append('<div class="kk" data-n="%s"><strong>%s</strong><div><a href="/sektor-%s.html">Neler var</a>%s</div></div>' % (E(nm[k].replace('İ','i').lower()), E(nm[k]), k, ('<a href="/%s-web-sitesi.html">Web sitesi</a>' % k) if web else ""))
    o.append('</div></div>')
o.append("</div></section><script>(function(){var q=document.getElementById('slq'),s=document.getElementById('sls');if(!q)return;var tr=function(x){return x.toLocaleLowerCase('tr')};q.addEventListener('input',function(){var v=tr(q.value.trim()),n=0;document.querySelectorAll('#liste .kk').forEach(function(e){var g=!v||tr(e.getAttribute('data-n')).indexOf(v)>-1;e.style.display=g?'':'none';if(g)n++});document.querySelectorAll('#liste .kt').forEach(function(t){t.style.display=t.querySelector('.kk:not([style*=none])')?'':'none'});s.textContent=n+' iş kolu'})})();</script><!--/SLB-->")
blok = "".join(o)
p = os.path.join(R, "tum-sektorler.html"); s = open(p, encoding="utf-8").read()
if "<!--SLB-->" in s:
    s = re.sub(r"<!--SLB-->.*?<!--/SLB-->", lambda m: blok, s, flags=re.S)
else:
    i = s.find('<section class="sec"><div class="w"><div class="slst">'); j = s.find("</section>", i) + 10
    assert i > 0
    s = s[:i] + blok + s[j:]
open(p, "w", encoding="utf-8").write(s); print("ok", len(nm))
