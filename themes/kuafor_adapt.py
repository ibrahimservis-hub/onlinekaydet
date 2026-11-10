# -*- coding: utf-8 -*-
"""Kuaför tasarım taslaklarını (docs/tema_tasarim/out/kuaforN.html) panelle çalışan temaya çevirir.

- üst düzey bölümler `<div class="ed" data-nm=...>` bloklarına sarılır (panelde göster/gizle, sırala, metin düzenle)
- telefon / çalışma saati / marka adı panelin yer tutucularına çevrilir (firma bilgisi otomatik yerleşir)
- randevu çekmecesi gerçek API'ye bağlanır (window.__OKLIVE) ve yalnız firmanın açtığı günler/saatler görünür
- paket şartı olan bölümler `data-mod="..."` taşır; firmanın paketinde yoksa yayından kalkar (sitegen.mod_off / strip_mod)
Çıktı: themes/html/<slug>.html, panel/themes.json ve site/themes.json kayıtları.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "docs", "tema_tasarim", "out")
OUT = os.path.join(HERE, "html")

# slug, kaynak no, kayıtlı ad (HTML'de geçtiği biçimiyle), tema bilgileri
THEMES = [
    dict(n=6, slug="k6-butik-kuafor", name="Butik Saç", dark="#3a2328", accent="#b5476b", soft="#f4dfe0", radius=14),
    dict(n=7, slug="k7-kesimhane-kuafor", name="Kesimhane", dark="#0c0c0c", accent="#ffd60a", soft="#151515", radius=4),
    dict(n=8, slug="k8-sakin-kuafor", name="Sakin Saç", dark="#25382c", accent="#b9814f", soft="#f6f8f3", radius=99),
    dict(n=9, slug="k9-kagit-kuafor", name="Saç &amp; Kâğıt", dark="#161412", accent="#7a1f2b", soft="#f6f1e7", radius=0),
    dict(n=10, slug="k10-atolye-kuafor", name="Atölye Saç", dark="#1b1b1f", accent="#ff6b57", soft="#f4f1ea", radius=16),
]

VOID = {"br", "img", "input", "meta", "link", "hr", "source", "path", "circle", "rect", "line", "polyline", "ellipse", "use", "stop", "wbr"}
TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*)>")

NAMES = {"ana": "Ana görsel", "hizmet": "Hizmetler", "stil": "Stil seçici", "galeri": "Galeri", "ekip": "Ekip", "kadro": "Ekip", "paket": "Paketler",
         "iletisim": "İletişim", "sss": "Sık sorulanlar", "ritueller": "Hizmetler", "sec": "Ritüel sihirbazı", "hediye": "Hediye kartı",
         "icindekiler": "Hizmetler", "lookbook": "Galeri", "notlar": "Notlar", "bulten": "Bülten"}


def children(h, a, b):
    """h[a:b] içindeki ilk düzey öğeler: [(başlangıç, bitiş, etiket, öznitelik)]."""
    out, d, i, cur = [], 0, a, None
    while True:
        m = TAG.search(h, i, b)
        if not m:
            break
        close, tag, at = m.group(1), m.group(2).lower(), m.group(3)
        i = m.end()
        if tag in ("script", "style") and not close:
            e = h.find("</%s>" % tag, i)
            i = e + len(tag) + 3
            if d == 0:
                out.append((m.start(), i, tag, at))
            continue
        if tag in VOID or at.rstrip().endswith("/"):
            if d == 0:
                out.append((m.start(), m.end(), tag, at))
            continue
        if close:
            d -= 1
            if d == 0:
                s = cur
                out.append((s[0], m.end(), s[1], s[2]))
        else:
            if d == 0:
                cur = (m.start(), tag, at)
            d += 1
    return out


def attr(at, k):
    m = re.search(r'\b%s="([^"]*)"' % k, at)
    return m.group(1) if m else ""


def classify(tag, at, first_hero):
    i, c = attr(at, "id"), attr(at, "class").split()
    if tag in ("script", "style"):
        return None
    if i in ("sh", "lb"):
        return "Mobil bar"
    if i in ("tab", "dock", "fab", "fb"):
        return "Mobil bar"
    if i == "mn":
        return "Mobil menü"
    if "dl" in c:
        return "Duyuru çubuğu"
    if tag == "footer":
        return "Alt bilgi"
    if tag in ("aside", "nav") or i in ("top", "bar", "mast", "lnk", "nv"):
        return "Menü"
    if tag == "header" and "hero" in c:
        return "Ana görsel"
    if "mq" in c:
        return "Kayan şerit"
    if tag == "section":
        if i in NAMES:
            return NAMES[i]
        if "faq" in c:
            return "Sık sorulanlar"
        return None
    return None


def build_theme(t):
    h = open(os.path.join(SRC, "kuafor%d.html" % t["n"]), encoding="utf-8").read()
    bs = h.index("<body")
    be = h.index(">", bs) + 1
    ee = h.rindex("</body>")
    head, body = h[:be], h[be:ee]
    kids = children(body, 0, len(body))
    blocks, seen = [], {}
    tail_scripts = []
    for (a, b, tag, at) in kids:
        raw = body[a:b]
        if tag == "script":
            tail_scripts.append(raw)
            continue
        if tag == "style":
            head = head.replace("</head>", raw + "</head>")
            continue
        if tag == "main":
            inner = children(raw, raw.index(">") + 1, raw.rindex("</main>"))
            names = [classify(tg, x, False) or ("Ana görsel" if "hero" in attr(x, "class") else None) for (_, _, tg, x) in inner]
            if all(n is None for n in names) or t["n"] == 10:
                blocks.append(["Ana içerik", raw])
                continue
            for (a2, b2, tg, x), nm in zip(inner, names):
                sec = raw[a2:b2]
                sec = re.sub(r"^<(\w+)", r'<\1 data-mx', sec, count=1)
                blocks.append([nm or "Bölüm", sec])
            continue
        nm = classify(tag, at, False)
        if nm is None:
            h2 = re.search(r"<h2[^>]*>(.*?)</h2>", raw, re.S)
            nm = re.sub(r"<[^>]+>", "", h2.group(1)).strip(" .") if h2 else "Bölüm"
        blocks.append([nm, raw])
    # aynı adlı bölümleri ve art arda gelen sabit parçaları birleştir
    merged = []
    for nm, raw in blocks:
        prev = next((m for m in merged if m[0] == nm), None)
        if prev and nm in ("Menü", "Mobil bar", "Mobil menü", "Duyuru çubuğu", "Alt bilgi"):
            prev[1] += raw
        else:
            merged.append([nm, raw])
    # sabitler kendi yerlerinde: Menü/Mobil menü/Duyuru başta, Alt bilgi/Mobil bar sonda
    top = [b for b in merged if b[0] in ("Duyuru çubuğu", "Menü", "Mobil menü")]
    bot_ft = [b for b in merged if b[0] == "Alt bilgi"]
    bot_mb = [b for b in merged if b[0] == "Mobil bar"]
    mid = [b for b in merged if b[0] not in ("Duyuru çubuğu", "Menü", "Mobil menü", "Alt bilgi", "Mobil bar")]
    ordered = [b for b in top if b[0] == "Duyuru çubuğu"] + [b for b in top if b[0] == "Menü"] + [b for b in top if b[0] == "Mobil menü"] + mid + bot_ft + bot_mb
    if t["n"] != 10:
        k = next((i for i, b in enumerate(ordered) if b[0] == "Alt bilgi"), len(ordered))
        ordered[k:k] = [["Ürünler", SHOP], ["Kampanyalar", CAMP]]
    else:
        raw = next(b for b in ordered if b[0] == "Ana içerik")
        raw[1] = raw[1].replace("</main>", "</main>", 1)
        k = next(i for i, b in enumerate(ordered) if b[0] == "Alt bilgi")
        ordered[k:k] = [["Ürünler", SHOP], ["Kampanyalar", CAMP]]
    used = {}
    out = []
    for nm, raw in ordered:
        used[nm] = used.get(nm, 0) + 1
        label = nm if used[nm] == 1 else "%s %d" % (nm, used[nm])
        ex = {"Ürünler": ' data-dflt="off" data-mod="magaza"', "Kampanyalar": ' data-mod="pazarlama"'}.get(nm, "")
        out.append('<div class="ed" data-nm="%s"%s>%s</div>' % (label, ex, raw))
    tail_scripts += [SHOP_JS, CAMP_JS]
    html = head + "".join(out) + "".join(tail_scripts) + "</body>" + h[ee + len("</body>"):]
    return finish(html, t)


CAMP = """<section class="sec kx" id="kampanya" data-camp><div class="w"><span class="eyebrow">Kampanyalar</span><h2>Kupon kodunuz mu var?</h2><p>Salonun güncel kampanya kodunu buraya yazın, indiriminizi hemen görün. Randevu alırken aynı kodu girebilirsiniz.</p><form class="kf" id="kupf" novalidate><input id="kupc" name="kupon" autocomplete="off" placeholder="KUPON KODU" aria-label="Kupon kodu"><button class="btn" type="submit">Kodu kontrol et</button></form><div class="kmsg" id="kupm" role="status"></div></div></section>"""
CAMP_JS = """<script>(function(){var f=document.getElementById('kupf');if(!f)return;f.addEventListener('submit',function(e){e.preventDefault();var v=document.getElementById('kupc').value.trim(),m=document.getElementById('kupm');if(!v){m.textContent='Lütfen kodu yazın.';return}m.textContent='Kontrol ediliyor…';fetch('/api/public/coupon/'+encodeURIComponent(v)).then(function(r){return r.json()}).then(function(j){if(!j.valid){m.textContent=j.message||'Bu kupon geçerli değil.';return}var d=j.type==='percent'||j.type==='pct'||j.type==='yuzde'?('%'+j.value+' indirim'):(j.value+' ₺ indirim');m.textContent='Kod geçerli: '+d+(j.min_total?' ('+j.min_total+' ₺ ve üzeri)':'')+'. Randevu alırken aynı kodu girin.'}).catch(function(){m.textContent='Şu an kontrol edilemedi.'})})})()</script>"""
SHOP = """<section class="sec kx" id="urunler"><div class="w"><span class="eyebrow">Online mağaza</span><h2>Ürünler</h2><p>Bakım ve şekillendirme ürünlerimizi buradan sipariş edebilirsiniz.</p><div class="kpg" id="kpg" aria-live="polite"></div><p style="margin-top:22px"><a class="btn" href="/magaza">Tüm ürünleri gör</a></p></div></section>"""
SHOP_JS = """<script>(function(){var g=document.getElementById('kpg');if(!g)return;fetch('/api/public/shop/products').then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(j){var ps=(j.products||[]).slice(0,6);if(!ps.length){g.parentNode.parentNode.style.display='none';return}var esc=function(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})};g.innerHTML=ps.map(function(p){var im=(p.images||[])[0];return'<a class="kp" href="/magaza/urun/'+encodeURIComponent(p.slug||p.id)+'">'+(im?'<img loading="lazy" alt="'+esc(p.name)+'" src="'+esc(im)+'">':'<span class="kpn"></span>')+'<b>'+esc(p.name)+'</b><span>'+Number(p.price||0).toLocaleString('tr-TR')+' ₺</span></a>'}).join('')}).catch(function(){var s=g.closest('section');if(s)s.style.display='none'})})()</script>"""
KX_CSS = """.kx{background:var(--bg);color:var(--ink)}.kx h2{font:500 clamp(28px,4vw,44px)/1.1 var(--sfont);margin:12px 0}.kx p{max-width:560px;opacity:.8;line-height:1.6}
.kf{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px;max-width:520px}.kf input{flex:1;min-width:180px;min-height:50px;padding:0 16px;border:1.5px solid var(--line);border-radius:var(--sr);background:transparent;color:inherit;font:600 15px var(--sbody);letter-spacing:.08em;text-transform:uppercase}
.kmsg{margin-top:14px;font-weight:600;min-height:24px}.kpg{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px;margin-top:22px}
.kp{display:grid;gap:6px;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:var(--sr);padding:10px}.kp img,.kpn{width:100%;aspect-ratio:1;object-fit:cover;border-radius:calc(var(--sr)*.7);background:var(--line)}.kp span{opacity:.75}"""

BRIDGE = """<style data-kbridge>
:root{--ln:var(--line,rgba(0,0,0,.14));--sf:var(--soft,var(--sbg,#f5f5f5));--r:var(--sr,12px);--fd:var(--sfont,inherit);--fb:var(--sbody,inherit);--hw:500;--ht:0;--dk:var(--ink);--fbg:var(--bg);--on-ac:#fff}
[data-mx]{max-width:1080px;margin-left:auto;margin-right:auto}
.w{max-width:1100px;margin:0 auto;padding:0 20px}.sec{padding:clamp(40px,7vw,84px) 0}
.eyebrow{font:600 12px/1 var(--fb);letter-spacing:.14em;text-transform:uppercase;color:var(--ac)}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:0 26px;border-radius:var(--r);background:var(--ac);color:#fff;font:600 15px var(--fb);text-decoration:none;border:0}
.btn.o{background:transparent;color:inherit;border:1.5px solid var(--ln)}
.spx-c{max-width:760px;line-height:1.7}.spx-c h2,.spx-c h3{font-family:var(--fd)}
.spx-fl{display:flex;flex-wrap:wrap;gap:14px;justify-content:center;padding:18px 20px;font-size:14px}.spx-fl a{color:inherit;opacity:.8}
"""
BRIDGE = BRIDGE + KX_CSS + "@media(max-width:900px){.spx-fab{bottom:92px!important}}</style>"


def finish(html, t):
    # telefon, saat, marka: panelin yer tutucuları
    html = re.sub(r"tel:\+?\d{10,12}", "tel:+905320000000", html)
    html = re.sub(r"0[2-3]\d{2} 000 00 00", "0532 000 00 00", html)
    html = html.replace("Salı–Cumartesi 10:00–20:00", "Hafta içi 08:30 – 19:00")
    html = html.replace("Salı–Cumartesi", "Hafta içi 08:30 – 19:00", 0)
    # kaynak taslağındaki sahte sosyal hesap yazıları panelin gerçek bağlantılarına bırakılır
    html = re.sub(r"Instagram · @\w+", "", html)
    # gerçek randevu
    html = html.replace("<script>", "<script>window.__OKLIVE=true;", 1) if "__OKLIVE=true" not in html else html
    html = html.replace("</head>", BRIDGE + "</head>", 1)
    html = re.sub(r"<title>.*?</title>", "<title>%s</title>" % t["name"], html, count=1, flags=re.S)
    if "data-mod=" not in html:
        pass
    return html


def register(items):
    for rel in (os.path.join(ROOT, "panel", "themes.json"), os.path.join(ROOT, "site", "themes.json")):
        if not os.path.isfile(rel):
            continue
        d = json.load(open(rel, encoding="utf-8"))
        d = [x for x in d if x["slug"] not in {i["slug"] for i in items}]
        for i in items:
            d.append(dict(slug=i["slug"], sector="kuafor", dark=i["dark"], accent=i["accent"], soft=i["soft"], radius=i["radius"], name=i["name"], premium=True))
        json.dump(d, open(rel, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    only = {int(x) for x in sys.argv[1:]}
    done = []
    for t in THEMES:
        if only and t["n"] not in only:
            continue
        html = build_theme(t)
        open(os.path.join(OUT, t["slug"] + ".html"), "w", encoding="utf-8").write(html)
        done.append(t)
        print(t["slug"], len(html), html.count('class="ed"'))
    register(done)
