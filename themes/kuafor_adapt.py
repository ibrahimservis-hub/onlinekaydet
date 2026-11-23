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
    dict(n=5, slug="k5-atolye-kuafor", name="Atölye Saç", dark="#1a1310", accent="#c98a5a", soft="#241a15", radius=14),
    dict(n=6, slug="k6-butik-kuafor", name="Butik Saç", dark="#3a2328", accent="#b5476b", soft="#f4dfe0", radius=14),
    dict(n=7, slug="k7-kesimhane-kuafor", name="Kesimhane", dark="#0c0c0c", accent="#ffd60a", soft="#151515", radius=4),
    dict(n=8, slug="k8-sakin-kuafor", name="Sakin Saç", dark="#25382c", accent="#b9814f", soft="#f6f8f3", radius=99),
    dict(n=9, slug="k9-kagit-kuafor", name="Saç &amp; Kâğıt", dark="#161412", accent="#7a1f2b", soft="#f6f1e7", radius=0),
    dict(n=10, slug="k10-atolye-kuafor", name="Atölye Saç", dark="#1b1b1f", accent="#ff6b57", soft="#f4f1ea", radius=16),
]

VOID = {"br", "img", "input", "meta", "link", "hr", "source", "path", "circle", "rect", "line", "polyline", "ellipse", "use", "stop", "wbr"}
TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*)>")

ADDR = "Atatürk Cad. No:12"
CLEAN = {
    5: [(r"Atatürk Bulvarı, Çankaya / Ankara", ADDR), (r"Çankaya'da randevuyla", "randevuyla"), (r"Çankaya · Ankara · Kadın", "Kadın"), (r"document\.title=\(h==='home'\?'':TT\[h\]\+' · '\)\+'Atölye Saç';", ""),
        (r"scrollTo\(\{top:0,behavior:'instant'\}\);", "")],
    6: [(r"Moda Cd\. 12, Kadıköy(?: / İstanbul)?", ADDR), (r"Moda · Kadıköy, İstanbul", "Randevuyla çalışan butik salon")],
    7: [(r"Barbaros Blv\. 8<br>Beşiktaş / İstanbul", ADDR), (r"Beşiktaş · İstanbul · Barber ve saç", "Barber ve saç")],
    8: [(r"Cemal Gürsel Cd\. 21, Bahçelievler / İzmir", ADDR), (r"Bahçelievler · İzmir · Saç ve bakım", "Saç ve bakım")],
    9: [(r"Abdi İpekçi Cd\. 30(?:<br>|, )?Nişantaşı / İstanbul", ADDR), (r"Nişantaşı'nda randevuyla", "Randevuyla"), (r"Nişantaşı · İstanbul", "Randevuyla çalışır")],
    10: [(r"Atatürk Blv\. 40, Çankaya", ADDR), (r"Atatürk Blv\. 40<br>Çankaya / Ankara", ADDR), (r'<span class="tag">Çankaya · Ankara</span>', "")],
}

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
    if i in ("tab", "dock", "fab", "fb", "mbar"):
        return "Mobil bar"
    if i == "mn":
        return "Mobil menü"
    if "dl" in c or "an" in c:
        return "Duyuru çubuğu"
    if i.startswith("pg-"):
        return {"home": "Ana sayfa", "hizmetler": "Hizmetler", "galeri": "Galeri", "uzmanlar": "Ekip", "paketler": "Paketler", "hakkimizda": "Hakkımızda",
                "ipuclari": "İpuçları", "iletisim": "İletişim"}.get(i[3:])
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


def patch_booking(h, refresh="refreshAll"):
    """kuafor5'in satır içi randevu betiği (ksh çekirdeğinin eski hâli) gerçek API'ye bağlanır: aynı değişiklikler ksh.CORE'da yapıldı."""
    sys.path.insert(0, os.path.join(ROOT, "docs", "tema_tasarim", "kset"))
    import ksh
    core = ksh.CORE

    def rep(a, b):
        nonlocal h
        assert a in h, a[:60]
        h = h.replace(a, b, 1)
    rep("HRS=[10,11,12,13,14,15,16,17,18,19];", "HRS=[600,660,720,780,840,900,960,1020,1080,1140];")
    rep("function openDay(d){var g=d.getDay();return g>=2&&g<=6}", core[core.index("function p2("):core.index("function booked(")].strip())
    rep("function booked(d,e,h){var x=Math.sin((d.getFullYear()*10000+(d.getMonth()+1)*100+d.getDate())*13+h*7+e.charCodeAt(0)*31)*10000;return x-Math.floor(x)<.35}",
        "function booked(d,e,m){var h=m/60,x=Math.sin((d.getFullYear()*10000+(d.getMonth()+1)*100+d.getDate())*13+h*7+e.charCodeAt(0)*31)*10000;return x-Math.floor(x)<.35}")
    rep("function isFree(d,e,h){var n=ist();if(key(d)===key(n)&&h*60<n.getHours()*60+n.getMinutes()+60)return false;",
        "function isFree(d,e,h){if(LIVE){var t=L.slots[iso(d)];return!!t&&t.some(function(s){return s.m===h&&s.available})}var n=ist();if(key(d)===key(n)&&h<n.getHours()*60+n.getMinutes()+60)return false;")
    rep("function freeT(d,e){return HRS.filter(function(h){return isFree(d,e,h)})}\nfunction fmt(h){return(h<10?'0':'')+h+':00'}" if "function freeT(d,e){return HRS.filter(function(h){return isFree(d,e,h)})}\nfunction fmt" in h else
        "function freeT(d,e){return HRS.filter(function(h){return isFree(d,e,h)})} function fmt(h){return(h<10?'0':'')+h+':00'}",
        core[core.index("function hrs()"):core.index("while(o.length<7")].split("function days")[0].strip() if False else
        "function hrs(){if(!LIVE)return HRS;var u={};Object.keys(L.slots).forEach(function(k){L.slots[k].forEach(function(s){u[s.m]=1})});return Object.keys(u).map(Number).sort(function(a,b){return a-b})}\nfunction freeT(d,e){return hrs().filter(function(h){return isFree(d,e,h)})}\nfunction fmt(m){return p2(Math.floor(m/60))+':'+p2(m%60)}")
    rep("while(out.length<7&&k<30){", "while(out.length<7&&k<40){")
    rep("HRS.forEach(function(h){var b=document.createElement('button');b.dataset.v=fmt(h)", "hrs().forEach(function(h){var b=document.createElement('button');b.dataset.v=fmt(h)")
    rep("function openNow(){var d=new Date(", core[core.index("function openNow(){if(LIVE)"):core.index("var d=ist(),g=d.getDay()")].strip().replace("function openNow(){", "function openNow(){", 1) + "var d=new Date(")
    # gönderim
    i = h.index("$('#go').onclick=function(){")
    j = h.index("};", h.index("shs.classList.add('done')", i)) + 2
    new = core[core.index("function fin("):core.index("var cp0=")]
    new = new.replace("refresh()", refresh + "()")
    new += core[core.index("var cp0="):core.index("\n", core.index("var cp0="))]
    new = new.replace("$('#go').onclick=function(){err('');", "$('#go').onclick=function(){err('');") 
    h = h[:i] + new + h[j:]
    rep("function open(ds){", "function open(ds){err('');$('#go').disabled=!!(LIVE&&L.ready&&!L.enabled);if(LIVE&&L.ready&&!L.enabled){err('Online randevu şu an kapalı. Lütfen bizi arayın.')}")
    rep("setInterval(refreshAll,60000)", "setInterval(function(){load(false);refreshAll()},60000)")
    rep('<button class="btn go" id="go">', '<label data-mod="pazarlama" style="display:none">Kupon kodu (varsa)<input id="f-c" autocomplete="off" placeholder="KUPON"></label><div id="f-msg" role="alert" style="display:none;margin-top:12px;color:#e11d48;font-size:14px;font-weight:600"></div><button class="btn go" id="go">')
    return h


def build_theme(t):
    h = open(os.path.join(SRC, "kuafor%d.html" % t["n"]), encoding="utf-8").read()
    if t["n"] == 5:
        h = patch_booking(h)
        h = re.sub(r'href="#/([a-z]+)"', r'href="#pg-\1"', h)
        h = h.replace('href="#/"', 'href="#"')
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
            if t["n"] == 10:
                # bento ızgara: her karo kendi bölümü olur (panelde ayrı gizle / sırala / yazı düzenle); ızgara <body> üzerinde kurulur
                o = raw.index('<div class="bt">') + len('<div class="bt">')
                BT = {"hero": "Ana görsel", "live": "Boş saatler", "cd": "Geri sayım", "st": "Takvim özeti", "sv": "Hizmetler", "gal": "Galeri", "pk": "Paketler",
                      "ex": "Ekip", "ig": "Instagram", "gift": "Hediye çeki", "mp": "İletişim", "faq": "Sık sorulanlar"}
                for (a2, b2, tg, x) in children(raw, o, raw.rindex("</div></main>")):
                    k = re.search(r'class="t ([a-z]+)', x).group(1)
                    blocks.append([BT.get(k, "Bölüm"), raw[a2:b2]])
                continue
            if all(n is None for n in names):
                blocks.append(["Ana içerik", raw])
                continue
            for (a2, b2, tg, x), nm in zip(inner, names):
                sec = raw[a2:b2]
                if t["n"] == 6:
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
        elif prev and nm == "Hizmetler" and t["n"] == 10:
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
BRIDGE = BRIDGE + KX_CSS + "@media(max-width:900px){.spx-fab{bottom:92px!important}}.pg{display:block!important;scroll-margin-top:84px}@media(max-width:900px){nav>a[href^=\"/\"]:not([href*=\"#\"]):not([class]){display:none!important}}</style>"


NUL_JS = ("window.__NUL={addEventListener:function(){},removeEventListener:function(){},classList:{add:function(){},remove:function(){},toggle:function(){},contains:function(){return false}},"
          "style:{},dataset:{},firstChild:{},setAttribute:function(){},getAttribute:function(){return null},querySelector:function(){return null},querySelectorAll:function(){return[]},"
          "closest:function(){return null},focus:function(){},click:function(){},value:''};")


def finish(html, t):
    # müşteri bir bölümü gizleyince / sildiğinde betik "null" yüzünden durmasın: bulunamayan öğe için etkisiz bir yedek nesne döner
    html = html.replace("var $=function(s,r){return(r||document).querySelector(s)}", "var $=function(s,r){return(r||document).querySelector(s)||window.__NUL}")
    html = html.replace("var $=function(s){return document.querySelector(s)}", "var $=function(s){return document.querySelector(s)||window.__NUL}")
    html = html.replace("<script>", "<script>" + NUL_JS, 1) if "window.__NUL=" not in html else html
    if t["n"] == 10:               # bento: ızgara gövdede; bölüm sarmalayıcıları görünmez, karolar ızgaraya girer, diğer bölümler tam genişlik
        html = html.replace("</head>", "<style data-bt>body{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;max-width:1240px;margin:0 auto;padding:78px 12px 20px;align-content:start;overflow-x:hidden}"
                            "body>.ed{display:contents}body>.ed>:not(.t){grid-column:1/-1}footer{padding-left:0;padding-right:0;width:100%}"
                            "@media(min-width:900px){body{grid-template-columns:repeat(6,1fr);gap:12px;padding-top:92px}}</style></head>", 1)
    for rx, to in CLEAN.get(t["n"], []):
        html = re.sub(rx, lambda m, to=to: to, html)
    html = re.sub(r'<a[^>]*href="mailto:[^"]*\.example"[^>]*>[^<]*</a>', "", html)
    html = re.sub(r"<h2([^>]*)>@\w+</h2>", r"<h2\1>Bizi Instagram'da izleyin</h2>", html)
    html = re.sub(r"@(?:atolyesac|butiksac)\b", "Instagram", html)
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
