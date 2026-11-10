# -*- coding: utf-8 -*-
"""Tema vitrini: mağaza ürünleri için kendi adresi olan ürün sayfası (/tema-onizleme/<tema>/urun-<kod>.html).
Ürün verisi temanın gömülü mağaza listesinden (window.__SHOP) okunur; sayfa temanın menü/alt bilgisiyle kurulur."""
import json, re
from html import escape as E

VAR = [
    (r"tişört|tisort|gömlek|elbise|pantolon|ceket|mont|kazak|giyim|etek|şort|hırka|sweat", [("Beden", ["S", "M", "L", "XL"]), ("Renk", ["Siyah", "Beyaz", "Lacivert"])]),
    (r"ayakkab|bot|sneaker|terlik|sandalet|çizme", [("Numara", ["39", "40", "41", "42", "43", "44"])]),
    (r"çanta|canta|cüzdan|valiz|sırt|saat|takı|gözlük", [("Renk", ["Siyah", "Kahverengi", "Lacivert"])]),
]
DESC = {
    "giyim": "Günlük kullanıma uygun, rahat kesimli ürün. Beden ve renk seçeneğini seçip sepete ekleyin.",
    "ayakkab": "Gün boyu rahat kullanım için tasarlanmış ürün. Numarayı seçip sepete ekleyin; uymazsa değişim yapılır.",
    "çanta": "Günlük kullanıma uygun, düzenli iç hacimli ürün. Renk seçeneğini seçip sepete ekleyin.",
}
CSS = """<style id="okurun">
.okp.ok_p{--c:var(--ac,#0a1f44);padding:0 0 clamp(28px,4vw,56px);color:var(--ink);font-family:var(--fb,inherit)}
.okp *{box-sizing:border-box}.okp .ok_bc{font:600 .82rem var(--fb,inherit);color:var(--mut);display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}.okp .ok_bc a{color:inherit;text-decoration:none}.okp .ok_bc a:hover{color:var(--c)}
.okp .ok_top{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:clamp(20px,4vw,48px);align-items:start}
.okp .ok_gl{display:grid;grid-template-columns:72px 1fr;gap:12px}.okp .ok_tl{display:flex;flex-direction:column;gap:8px}.okp .ok_tl button{padding:0;border:2px solid var(--ln);border-radius:10px;overflow:hidden;background:var(--sf);cursor:pointer;aspect-ratio:1/1}.okp .ok_tl button.on{border-color:var(--c)}.okp .ok_tl svg,.okp .ok_mn svg{width:100%;height:100%;display:block}
.okp .ok_mn{aspect-ratio:1/1;border-radius:calc(var(--r,12px)*1.3);overflow:hidden;background:var(--sf);border:1px solid var(--ln)}
.okp .ok_cd{font:700 .74rem var(--fb,inherit);letter-spacing:.12em;text-transform:uppercase;color:var(--mut)}.okp h1{font:800 clamp(1.4rem,2.6vw,2rem)/1.2 var(--fd,inherit);margin:6px 0 10px}
.okp .ok_st{font:700 .84rem/1 var(--fb,inherit);display:inline-flex;align-items:center;gap:7px}.okp .ok_st:before{content:"";width:9px;height:9px;border-radius:50%;background:#16a34a}.okp .ok_st.s1:before{background:#f59e0b}.okp .ok_st.s0:before{background:#dc2626}
.okp .ok_pr{font:800 clamp(1.8rem,3.2vw,2.4rem) var(--fd,inherit);margin:14px 0 4px}.okp .ok_pn{font-size:.82rem;color:var(--mut)}
.okp .ok_vg{margin:18px 0 0;display:grid;gap:14px}.okp .ok_vg b{display:block;font:700 .84rem var(--fb,inherit);margin-bottom:8px}.okp .ok_vo{display:flex;gap:8px;flex-wrap:wrap}.okp .ok_vo button{min-width:46px;min-height:44px;padding:0 14px;border:1.5px solid var(--ln);border-radius:10px;background:var(--fbg,#fff);color:var(--ink);font:700 .9rem var(--fb,inherit);cursor:pointer}.okp .ok_vo button.on{border-color:var(--c);box-shadow:0 0 0 3px color-mix(in srgb,var(--c) 18%,transparent)}
.okp .ok_by{display:flex;gap:10px;margin-top:20px;flex-wrap:wrap}.okp .ok_qt{display:flex;align-items:center;border:1.5px solid var(--ln);border-radius:var(--r,10px);background:var(--fbg,#fff)}.okp .ok_qt button{width:46px;height:52px;border:0;background:none;color:var(--ink);font-size:1.25rem;cursor:pointer}.okp .ok_qt span{min-width:30px;text-align:center;font-weight:700}
.okp .ok_b1,.okp .ok_b2{min-height:54px;padding:0 22px;border-radius:var(--r,10px);font:700 1rem var(--fb,inherit);cursor:pointer;flex:1;min-width:150px}.okp .ok_b1{background:var(--c);color:var(--on-ac,#fff);border:0}.okp .ok_b2{background:transparent;color:var(--ink);border:1.5px solid var(--ink)}.okp button:disabled{opacity:.5;cursor:not-allowed}
.okp .ok_bx{margin-top:18px;border:1px solid var(--ln);border-radius:var(--r,10px);background:var(--sf);padding:14px 16px;display:grid;gap:9px;font-size:.88rem}.okp .ok_bx div{display:flex;gap:10px;align-items:flex-start}.okp .ok_bx i{font-style:normal;font-weight:800;color:var(--c);flex:none}
.okp .ok_tb{margin-top:38px;border-bottom:1px solid var(--ln);display:flex;gap:4px;flex-wrap:wrap}.okp .ok_tb button{background:none;border:0;border-bottom:3px solid transparent;padding:12px 16px;min-height:46px;font:700 .95rem var(--fb,inherit);color:var(--mut);cursor:pointer}.okp .ok_tb button.on{color:var(--ink);border-color:var(--c)}
.okp .ok_tp{display:none;padding:22px 0;line-height:1.7;max-width:820px}.okp .ok_tp.on{display:block}.okp .ok_sp{width:100%;border-collapse:collapse}.okp .ok_sp td{padding:11px 6px;border-bottom:1px solid var(--ln);font-size:.92rem}.okp .ok_sp td:first-child{color:var(--mut);width:38%}
.okp .ok_rh{font:800 1.25rem var(--fd,inherit);margin:44px 0 16px}.okp .ok_rg{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.okp .ok_rc{display:block;text-decoration:none;color:inherit;border:1px solid var(--ln);border-radius:calc(var(--r,12px)*1.2);overflow:hidden;background:var(--fbg,#fff);transition:.2s}.okp .ok_rc:hover{transform:translateY(-3px);box-shadow:0 18px 34px -20px #0006}.okp .ok_rc .ok_im{aspect-ratio:4/3}.okp .ok_rc .ok_im svg{width:100%;height:100%;display:block}.okp .ok_rc h3{font:700 .92rem/1.3 var(--fb,inherit);margin:0;padding:12px 12px 4px}.okp .ok_rc b{display:block;padding:0 12px 14px;font:800 1.05rem var(--fd,inherit)}
.okp .ok_ty{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);z-index:9000;background:var(--dk,#111);color:#fff;border-radius:14px;padding:14px 18px;display:none;gap:16px;align-items:center;box-shadow:0 24px 50px -16px #000a;max-width:94%}.okp .ok_ty.on{display:flex}.okp .ok_ty a{background:var(--c);color:var(--on-ac,#fff);text-decoration:none;padding:10px 16px;border-radius:10px;font-weight:700;white-space:nowrap}
@media(max-width:860px){.okp .ok_top{grid-template-columns:1fr}.okp .ok_gl{grid-template-columns:1fr}.okp .ok_tl{flex-direction:row;order:2}.okp .ok_tl button{width:64px}.okp .ok_rg{grid-template-columns:repeat(2,1fr)}}
.okp .ok_mn{position:relative}.okp .ok_ic{position:absolute;right:12px;top:12px;display:grid;gap:8px;z-index:2}.okp .ok_ic button{width:44px;height:44px;border-radius:50%;border:0;background:#fff!important;color:#111!important;box-shadow:0 6px 16px -6px #0006;cursor:pointer;font-size:1.15rem}.okp .ok_ic button.on{color:#e11d48!important}
.okp .ok_rt{display:flex;gap:14px;flex-wrap:wrap;font:600 .86rem var(--fb,inherit);color:var(--mut);margin:2px 0 10px}.okp .ok_rt a{color:var(--c);text-decoration:none}
.okp .ok_sw{width:42px;height:42px;min-width:42px;padding:0!important;border-radius:50%!important}.okp .ok_sw.on{outline:2px solid var(--c);outline-offset:2px}
.okp .ok_sl{margin-top:16px;border:1px solid var(--ln);border-radius:var(--r,10px);padding:14px 16px;display:flex;gap:14px;align-items:center;justify-content:space-between;flex-wrap:wrap}.okp .ok_sl b{display:block;font-size:.95rem}.okp .ok_sl small{color:var(--mut)}.okp .ok_sl a{color:var(--c);font-weight:700;text-decoration:none;font-size:.88rem}
.okp .ok_ft{margin:14px 0 0;padding:0;list-style:none;display:grid;gap:7px;font-size:.9rem}.okp .ok_ft li:before{content:"•";color:var(--c);font-weight:900;margin-right:8px}
.okp .ok_em{padding:26px;border:1px dashed var(--ln);border-radius:var(--r,10px);text-align:center;color:var(--mut)}.okp .ok_em b{display:block;color:var(--ink);margin-bottom:6px}
.okp .ok_fm{display:grid;gap:10px;max-width:520px;margin-top:14px}.okp .ok_fm textarea{width:100%;min-height:90px;padding:12px;border:1px solid var(--ln);border-radius:var(--r,10px);background:var(--fbg,#fff);color:var(--ink);font:500 .95rem var(--fb,inherit)}.okp .ok_fm button{min-height:48px;border:0;border-radius:var(--r,10px);background:var(--c);color:var(--on-ac,#fff);font:700 .95rem var(--fb,inherit);cursor:pointer}
.okp .ok_sb{display:none}
@media(max-width:860px){.okp{padding-bottom:96px}.okp .ok_sb{position:fixed;left:0;right:0;bottom:0;z-index:8000;background:var(--bg,#fff);color:var(--ink);border-top:1px solid var(--ln);padding:10px 14px calc(10px + env(safe-area-inset-bottom));display:flex;gap:12px;align-items:center;box-shadow:0 -10px 30px -16px #0008}.okp .ok_sb div{font:800 1.2rem var(--fd,inherit);flex:none}.okp .ok_sb small{display:block;font:600 .72rem var(--fb,inherit);color:var(--mut)}.okp .ok_sb button{flex:1;min-height:50px;border:0;border-radius:var(--r,10px);background:var(--c);color:var(--on-ac,#fff);font:700 1rem var(--fb,inherit)}.okp .ok_ty{bottom:84px}}
</style>"""


def _slug(s):
    import sitegen
    return sitegen.slugify(s, 40)


def _data(home):
    m = re.search(r"window\.__SHOP=(\[.*?\]);\s*\n?", home, re.S)
    c = re.search(r"window\.__SHOPCFG=(\{.*?\});", home, re.S)
    if not m:
        return None, {}
    try:
        return json.loads(m.group(1)), (json.loads(c.group(1)) if c else {})
    except ValueError:
        return None, {}


def _pimg_js(home):
    a = home.find("function okPimg(")
    b = home.find("var D=window.__SHOP", a)
    return home[a:b] if a >= 0 and b > a else ""


SW = {"Siyah": "#15171c", "Beyaz": "#f5f5f5", "Lacivert": "#1b2a5a", "Kahverengi": "#6b4423"}


def _vb(t, o, k):
    on = " on" if k == 0 else ""
    if t == "Renk" and o in SW:
        return '<button type="button" class="ok_sw%s" data-v="%s" title="%s" aria-label="%s" style="background:%s;border:1.5px solid var(--ln)"></button>' % (on, E(o), E(o), E(o), SW[o])
    return '<button type="button" data-v="%s"%s>%s</button>' % (E(o), ' class="on"' if k == 0 else "", E(o))


def tl(n):
    return "{:,.0f}".format(n).replace(",", ".") + " ₺"


def render(home, ctx, theme_slug, page):
    """page = 'urun-<kod>' -> (html, başlık) ya da None."""
    import sitegen
    D, CF = _data(home)
    pj = _pimg_js(home)
    if not D or not pj:
        return None
    key = page[5:]
    i = next((n for n, p in enumerate(D) if _slug(p[0]) == key), -1)
    if i < 0:
        return None
    p = D[i]
    code, name, brand, cat, price, stock = p
    low = (name + " " + cat).lower().replace("İ", "i")
    var = next((v for rx, v in VAR if re.search(rx, low)), [])
    desc = next((v for k, v in DESC.items() if k in low), "Seçtiğiniz ürünün bilgileri aşağıdadır. Sorularınız için bize yazabilirsiniz.")
    base = "/" + "urun-"
    stt = ["Stokta yok", "s0"] if not stock else (["Son adetler", "s1"] if stock == 1 else ["Stokta", ""])
    rel = [x for x in D if x[0] != code and x[3] == cat][:4] or [x for x in D if x[0] != code][:4]
    wa = sitegen.phone10(ctx.get("tel"))
    esik = CF.get("kargo_esik") or 0
    home_href = "/tema-onizleme/%s.html" % theme_slug
    vh = "".join('<div><b>%s: <span data-vl="%s"></span></b><div class="ok_vo" data-vg="%s">%s</div></div>' % (
        E(t), E(t), E(t), "".join(_vb(t, o, k) for k, o in enumerate(opts))) for t, opts in var)
    specs = [("Ürün kodu", code), ("Kategori", cat), ("Marka / seri", brand), ("Stok durumu", stt[0])] + [(t, ", ".join(o)) for t, o in var] + [("Kargo", "%s ve üzeri siparişlerde ücretsiz" % tl(esik) if esik else "Hızlı kargo")]
    rows = "".join("<tr><td>%s</td><td>%s</td></tr>" % (E(a), E(b)) for a, b in specs)
    relh = "".join('<a class="ok_rc" href="/%s%s"><div class="ok_im" data-r="%d"></div><h3>%s</h3><b>%s</b></a>' % ("urun-", _slug(x[0]), D.index(x), E(x[1]), tl(x[4])) for x in rel)
    buy = ('<div class="ok_by"><div class="ok_qt"><button type="button" data-m aria-label="Azalt">−</button><span id="ok_q">1</span><button type="button" data-p aria-label="Artır">+</button></div>'
           '<button type="button" class="ok_b1" data-add>Sepete ekle</button><button type="button" class="ok_b2" data-now>Hemen al</button></div>') if stock else \
        '<p class="ok_pn" style="margin-top:18px">Bu ürün şu an stokta yok. Haber vermemizi isterseniz bize yazın.</p>'
    info = ('<div class="ok_bx"><div><i>✓</i><span>%s</span></div><div><i>✓</i><span>Tahmini teslimat: <b id="ok_dt">1-3 iş günü</b></span></div><div><i>✓</i><span>Kapıda ödeme, kart veya havale/EFT ile ödeme</span></div></div>'
            % (("%s ve üzeri siparişlerde ücretsiz kargo" % tl(esik)) if esik else "Hızlı kargo"))
    ask = ('<p>Ürünle ilgili sorunuz mu var? <a href="https://wa.me/90%s" style="color:var(--c);font-weight:700">WhatsApp’tan yazın</a>, hızlıca dönelim.</p>' % wa) if wa else "<p>Ürünle ilgili sorularınız için bize ulaşın.</p>"
    seller = ('<div class="ok_sl"><div><small>Satıcı</small><b>%s</b></div>%s</div>' % (E(ctx.get("name") or ""), ('<a href="https://wa.me/90%s">Satıcıya yaz</a>' % wa) if wa else ""))
    feats = "".join("<li>%s</li>" % E(x) for x in (["Marka / seri: " + brand, "Kategori: " + cat] + ["%s seçeneği mevcut" % t for t, o in var] + ["Ürün kodu: " + code]))
    reviews = ('<div class="ok_em"><b>Bu ürün için henüz değerlendirme yok</b>Ürünü aldıysanız deneyiminizi bize yazın.</div>')
    qa = ('<div class="ok_em"><b>Henüz soru sorulmamış</b>Aklınızdaki soruyu yazın, satıcı size dönsün.</div>'
          '<form class="ok_fm" data-qa><textarea name="q" placeholder="Ürünle ilgili sorunuz" required></textarea><button type="submit">Soruyu gönder</button></form>')
    cartkey = "okcart-" + home_href
    main = ('<div class="ed" data-nm="İçerik"><section class="sec"><div class="w okp ok_p" data-cartkey="%s" data-home="%s" data-wa="%s">'
            '<nav class="ok_bc" aria-label="Sayfa yolu"><a href="/">Ana sayfa</a><span>›</span><a href="/#urunler">Mağaza</a><span>›</span><span>%s</span><span>›</span><b>%s</b></nav>'
            '<div class="ok_top"><div class="ok_gl"><div class="ok_tl" id="ok_tl"></div><div class="ok_mn" id="ok_mn" role="img" aria-label="%s"><div class="ok_ic"><button type="button" id="ok_fv" aria-label="Favorilere ekle" title="Favorilere ekle">♡</button><button type="button" id="ok_sh" aria-label="Paylaş" title="Paylaş">⇪</button></div><div id="ok_mi" style="width:100%%;height:100%%"></div></div></div>'
            '<div><div class="ok_cd">%s · %s</div><h1>%s</h1><div class="ok_rt"><a href="#ok_tabs" data-go="2">Değerlendirmeler</a><a href="#ok_tabs" data-go="3">Soru &amp; cevap</a><span class="ok_st %s">%s</span></div><div class="ok_pr">%s</div><div class="ok_pn">KDV dahil</div>'
            '<div class="ok_vg">%s</div>%s%s<ul class="ok_ft">%s</ul>%s</div></div>'
            '<div class="ok_tb" id="ok_tabs" role="tablist"><button class="on" data-t="0">Ürün bilgileri</button><button data-t="1">Özellikler</button><button data-t="2">Değerlendirmeler</button><button data-t="3">Soru &amp; cevap</button><button data-t="4">Teslimat ve iade</button></div>'
            '<div class="ok_tp on" data-tp="0"><p>%s</p></div><div class="ok_tp" data-tp="1"><table class="ok_sp">%s</table></div>'
            '<div class="ok_tp" data-tp="2">%s</div><div class="ok_tp" data-tp="3">%s</div><div class="ok_tp" data-tp="4"><p>Siparişiniz onaylandıktan sonra kargoya verilir; teslimat süresi genellikle 1-3 iş günüdür. %s</p><p>Teslimde ürünü kontrol edin; sorun varsa bize yazın, değişim ya da iade için yardımcı oluruz.</p></div>'
            ''
            '<h2 class="ok_rh">Benzer ürünler</h2><div class="ok_rg">%s</div><div id="ok_rv"></div>'
            '<div class="ok_sb"><div><small>Fiyat</small>%s</div><button type="button" data-add2>Sepete ekle</button></div><div class="ok_ty" id="ok_ty"><span>Ürün sepete eklendi</span><a href="%s?sepet=1">Sepete git</a></div></div></section></div>'
            % (E(cartkey), E(home_href), E(wa or ""), E(cat), E(name), E(name), E(cat), E(code), E(name), stt[1], stt[0], tl(price), vh, buy, info, feats, "",
               E(desc), rows, reviews, qa, (("%s ve üzeri siparişlerde kargo ücretsizdir." % tl(esik)) if esik else ""), relh, tl(price) if stock else "", home_href))
    js = ('<script>(function(){' + pj + 'var D=' + json.dumps(D, ensure_ascii=False) + ',I=' + str(i) + ',P=D[I],Q=1,SEL={},$=function(s,r){return(r||document).querySelector(s)},A=function(s,r){return[].slice.call((r||document).querySelectorAll(s))};'
          'var W=$(".okp"),KEY=W.dataset.cartkey,VB=["0 0 200 200","24 24 152 152","46 46 108 108","0 40 200 120"];'
          'function pic(vb){var s=okPimg(P[1],P[3]);return s.replace(/viewBox="[^"]*"/,\'viewBox="\'+vb+\'"\')}'
          'function show(n){$("#ok_mi").innerHTML=pic(VB[n]);A("#ok_tl button").forEach(function(b,k){b.classList.toggle("on",k===n)})}'
          '$("#ok_tl").innerHTML=VB.map(function(v,k){return \'<button type="button" data-k="\'+k+\'" aria-label="Görsel \'+(k+1)+\'">\'+pic(v)+"</button>"}).join("");A("#ok_tl button").forEach(function(b){b.onclick=function(){show(+b.dataset.k)}});show(0);'
          'A("[data-r]").forEach(function(e){var x=D[+e.dataset.r];e.innerHTML=okPimg(x[1],x[3])});'
          'A("[data-vg]").forEach(function(g){var t=g.dataset.vg;var f=$("button",g);SEL[t]=f.dataset.v;$(\'[data-vl="\'+t+\'"]\').textContent=SEL[t];A("button",g).forEach(function(b){b.onclick=function(){A("button",g).forEach(function(x){x.classList.remove("on")});b.classList.add("on");SEL[t]=b.dataset.v;$(\'[data-vl="\'+t+\'"]\').textContent=SEL[t]}})});'
          'A("[data-t]").forEach(function(b){b.onclick=function(){A("[data-t]").forEach(function(x){x.classList.toggle("on",x===b)});A("[data-tp]").forEach(function(x){x.classList.toggle("on",x.dataset.tp===b.dataset.t)})}});'
          'var q=$("#ok_q");$("[data-m]")&&($("[data-m]").onclick=function(){Q=Math.max(1,Q-1);q.textContent=Q});$("[data-p]")&&($("[data-p]").onclick=function(){Q=Math.min(20,Q+1);q.textContent=Q});'
          'function add(){var v=Object.keys(SEL).map(function(k){return SEL[k]}).join(" / "),k=P[0]+(v?"|"+v:""),n=P[1]+(v?" ("+v+")":""),C=[];try{C=JSON.parse(localStorage.getItem(KEY)||"[]")}catch(e){}var f=C.filter(function(x){return x.k===k})[0];if(f)f.q+=Q;else C.push({k:k,n:n,p:P[4],q:Q});try{localStorage.setItem(KEY,JSON.stringify(C))}catch(e){}}'
          '$("[data-add]")&&($("[data-add]").onclick=function(){add();var t=$("#ok_ty");t.classList.add("on");clearTimeout(window.__t);window.__t=setTimeout(function(){t.classList.remove("on")},5000)});'
          '$("[data-now]")&&($("[data-now]").onclick=function(){add();location.href=W.dataset.home+"?sepet=1"});'
          'A("[data-go]").forEach(function(a){a.onclick=function(){var b=$(\'[data-t="\'+a.dataset.go+\'"]\');b&&b.click()}});'
          'var d=new Date(),n=0,e1,e2,M=["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"];function wd(k){var x=new Date(),c=0;while(c<k){x.setDate(x.getDate()+1);if(x.getDay()%6)c++}return x}e1=wd(1);e2=wd(3);var dt=$("#ok_dt");dt&&(dt.textContent=e1.getDate()+" "+M[e1.getMonth()]+" – "+e2.getDate()+" "+M[e2.getMonth()]);'
          'var FK="okfav-"+KEY,fv=$("#ok_fv"),FV=[];try{FV=JSON.parse(localStorage.getItem(FK)||"[]")}catch(e){}function fp(){var o=FV.indexOf(P[0])>-1;fv.classList.toggle("on",o);fv.textContent=o?"♥":"♡"}fv.onclick=function(){var j=FV.indexOf(P[0]);j>-1?FV.splice(j,1):FV.push(P[0]);try{localStorage.setItem(FK,JSON.stringify(FV))}catch(e){}fp()};fp();'
          '$("#ok_sh").onclick=function(){var u=location.href;if(navigator.share){navigator.share({title:P[1],url:u}).catch(function(){})}else if(navigator.clipboard){navigator.clipboard.writeText(u);this.textContent="✓";var s=this;setTimeout(function(){s.textContent="⇪"},1500)}};'
          'var s2=$("[data-add2]");s2&&(s2.onclick=function(){$("[data-add]").click()});'
          'var RK="okrecent-"+KEY,R=[];try{R=JSON.parse(localStorage.getItem(RK)||"[]")}catch(e){}var rv=R.filter(function(c){return c!==P[0]}).map(function(c){return D.filter(function(x){return x[0]===c})[0]}).filter(Boolean).slice(0,4);'
          'if(rv.length){$("#ok_rv").innerHTML=\'<h2 class="ok_rh">Son gezdikleriniz</h2><div class="ok_rg">\'+rv.map(function(x){return \'<a class="ok_rc" href="/urun-\'+String(x[0]).toLowerCase().replace(/ü/g,"u").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"")+\'"><div class="ok_im">\'+okPimg(x[1],x[3])+\'</div><h3>\'+x[1]+\'</h3><b>\'+x[4].toLocaleString("tr-TR")+" ₺</b></a>"}).join("")+"</div>";A("#ok_rv a").forEach(function(a){a.href=location.pathname.replace(/\\/[^\\/]*$/,"")+a.getAttribute("href").replace("/urun-","/urun-")+".html"})}'
          'R=[P[0]].concat(R.filter(function(c){return c!==P[0]})).slice(0,8);try{localStorage.setItem(RK,JSON.stringify(R))}catch(e){}'
          'var fm=$("[data-qa]");fm&&(fm.onsubmit=function(ev){ev.preventDefault();var t=fm.q.value.trim();if(!t)return;var wa=W.dataset.wa;if(wa){window.open("https://wa.me/90"+wa+"?text="+encodeURIComponent("Ürün sorusu ("+P[1]+" / "+P[0]+"): "+t),"_blank")}fm.innerHTML="<p>Sorunuz iletildi, teşekkürler.</p>"})})();</script>')
    return main + CSS + js


def page_html(home, ctx, theme_slug, page):
    import sitegen
    r = render(home, ctx, theme_slug, page)
    if not r:
        return None
    m = re.search(r'aria-label="([^"]+)" role="img"|<h1>(.*?)</h1>', r)
    title = re.search(r"<h1>(.*?)</h1>", r)
    title = title.group(1) if title else "Ürün"
    out = sitegen.assemble_mid(home, ctx, title, [["İçerik", r]], "page", page, "")
    return out
