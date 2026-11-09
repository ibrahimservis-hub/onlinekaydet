"""Menü, mobil menü çekmecesi, 14 farklı mobil bar ve 4 alt bilgi düzeni."""
from .base import ic

TEL = '0532 000 00 00'
TELRAW = '905320000000'


def ed(nm, h):
    return f'<div class="ed" data-nm="{nm}">{h}</div>'


def logo(X, cls=''):
    r = X.r
    mk = r.get('logo', 'sq')
    ini = X.nm[0]
    if mk == 'tx':
        m = ''
    else:
        m = f'<span class="lm lm-{mk}">{ini}</span>'
    return f'<a class="lg {cls}" href="#top">{m}<span class="ln">{X.nm}</span></a>'


def links_html(X, tag='a'):
    return ''.join(f'<a href="{h}">{l}</a>' for l, h in X.links)


# ================================================================== MENÜLER
NAVCSS = {
 'base': """.lg{display:inline-flex;align-items:center;gap:11px;font:700 1.15rem/1 var(--fd);letter-spacing:var(--lgt,-.02em);color:inherit;white-space:nowrap}
.lm{flex:none;width:38px;height:38px;display:grid;place-items:center;font:800 1.1rem/1 var(--fd);background:var(--ac);color:var(--on-ac);border-radius:calc(var(--r)*.7)}
.lm-ci{border-radius:50%}.lm-ol{background:transparent;color:var(--ac);border:2px solid var(--ac)}.lm-bar{border-radius:0;background:transparent;color:var(--ac);border-left:4px solid var(--ac);width:auto;padding-left:10px;font-size:1.5rem}
.lm-dm{transform:rotate(45deg);border-radius:6px}.lm-dm{font-size:0}.lm-dm:after{content:"";}
.nv{z-index:60}.nv nav{display:flex;gap:clamp(16px,2.2vw,32px);font:600 .93rem/1 var(--fb)}.nv nav a{position:relative;padding:6px 0;opacity:.82;transition:.15s}.nv nav a:hover{opacity:1;color:var(--ac)}
@media(max-width:900px){.nv nav,.nv .nv-cta,.nv .nv-tel{display:none!important}}""",
 'classic': """.nv1{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--ln)}.nv1 .w{display:flex;align-items:center;gap:32px;height:76px}.nv1 nav{margin-left:auto}.nv1 .btn{min-height:44px;padding:0 20px}""",
 'center': """.nv2{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--ln)}.nv2 .w{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;height:84px}.nv2 nav.l{justify-content:flex-start}.nv2 nav.r{justify-content:flex-end;align-items:center}.nv2 .lg{font-size:1.5rem;justify-self:center}
.nv2 .btn{min-height:42px;padding:0 18px;font-size:.85rem}@media(max-width:900px){.nv2 .w{display:flex;height:70px}.nv2 .lg{margin-right:auto;font-size:1.2rem}}""",
 'pill': """.nv3{position:sticky;top:12px;margin:12px auto 0;width:min(1120px,100% - 24px);z-index:60}.nv3 .in{display:flex;align-items:center;gap:20px;height:64px;padding:0 10px 0 22px;border-radius:99px;background:color-mix(in srgb,var(--bg) 86%,transparent);backdrop-filter:blur(14px);border:1px solid var(--ln);box-shadow:0 12px 34px -16px #0005}
.nv3 nav{margin-left:auto}.nv3 .btn{min-height:46px;border-radius:99px}.nv3 .bgr{border-radius:50%;width:46px;height:46px}""",
 'min': """.nv4{position:absolute;top:0;left:0;right:0;z-index:60;color:var(--navc,inherit)}.nv4 .w{display:flex;align-items:center;justify-content:space-between;height:88px}.nv4 .nv-tel{font:600 .95rem/1 var(--fb);margin-left:auto;margin-right:18px;display:flex;align-items:center;gap:9px}
.nv4 .bgr{display:grid!important;margin-left:0;background:var(--bg);color:var(--ink);border-color:transparent}""",
 'two': """.nv5 .st{background:var(--dk);color:#ffffffbf;font-size:.8rem}.nv5 .st .w{display:flex;justify-content:space-between;gap:16px;padding:9px 0}.nv5 .st a{color:#fff;font-weight:600}.nv5 .mn{position:sticky;top:0;background:var(--bg);border-bottom:3px solid var(--ac);z-index:60}
.nv5 .mn .w{display:flex;align-items:center;gap:30px;height:74px}.nv5 nav{margin-left:auto;text-transform:uppercase;letter-spacing:.07em;font-size:.76rem}.nv5 nav a:after{content:"";position:absolute;left:0;right:100%;bottom:-6px;height:2px;background:var(--ac);transition:right .2s}.nv5 nav a:hover:after{right:0}
@media(max-width:900px){.nv5 .st{display:none}.nv5 .mn .w{height:66px}}""",
 'idx': """.nv6{position:sticky;top:0;background:var(--dk);color:#fff;border-bottom:1px solid #ffffff22}.nv6 .w{display:flex;align-items:center;gap:28px;height:70px}.nv6 nav{margin-left:auto;font-family:var(--fm,var(--fb));gap:26px}.nv6 nav a{font-size:.8rem;letter-spacing:.04em}
.nv6 nav a:before{content:attr(data-i);color:var(--ac);margin-right:7px;font-size:.7rem}.nv6 .bgr{color:#fff;border-color:#ffffff44}.nv6 .btn{min-height:40px;padding:0 16px;font-size:.8rem}""",
 'box': """.nv7{padding:16px 0 0;position:sticky;top:0;z-index:60;background:linear-gradient(var(--bg) 70%,transparent)}.nv7 .in{display:flex;align-items:center;gap:26px;border:1.5px solid var(--ink);border-radius:var(--r);height:68px;padding:0 12px 0 22px;background:var(--bg)}.nv7 nav{margin-left:auto}.nv7 .btn{min-height:46px;padding:0 20px}""",
 'rail': """@media(min-width:1000px){body.rail{padding-left:92px}.nv8{position:fixed;left:0;top:0;bottom:0;width:92px;z-index:70;background:var(--dk);color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:space-between;padding:22px 0}
.nv8 .lg .ln{display:none}.nv8 .bgr{display:grid;margin:0;border-color:#ffffff44;color:#fff}.nv8 .vt{writing-mode:vertical-rl;transform:rotate(180deg);font:700 .85rem/1 var(--fb);letter-spacing:.2em;text-transform:uppercase;display:flex;align-items:center;gap:12px;color:#fff}.nv8 .vt:before{content:"";width:8px;height:8px;border-radius:50%;background:var(--ac)}
.nv8 .tl2{writing-mode:vertical-rl;transform:rotate(180deg);font:600 .8rem/1 var(--fb);letter-spacing:.12em;opacity:.7}.nv8 nav{display:none}}
@media(max-width:999px){.nv8{position:sticky;top:0;background:var(--dk);color:#fff;z-index:60}.nv8 .vt,.nv8 .tl2{display:none}.nv8 .in{display:flex;align-items:center;height:66px;padding:0 18px}.nv8 .bgr{color:#fff;border-color:#ffffff44}}""",
}


def nav(X):
    k = X.r['nav']
    X.css('nav.base', NAVCSS['base'])
    cta = f'<a class="btn nv-cta" href="#randevu">{X.r.get("cta", "Randevu al")}</a>'
    burger = '<label class="bgr" for="mn" aria-label="Menü">' + ic('mn', 22) + '</label>'
    L = links_html(X)
    if k == 'classic':
        X.css('nav.classic', NAVCSS['classic'])
        return ed('Menü', f'<header class="nv nv1" id="top"><div class="w">{logo(X)}<nav>{L}</nav>{cta}{burger}</div></header>')
    if k == 'center':
        X.css('nav.center', NAVCSS['center'])
        a, b = X.links[:2], X.links[2:4]
        return ed('Menü', f'<header class="nv nv2" id="top"><div class="w"><nav class="l">' + ''.join(f'<a href="{h}">{l}</a>' for l, h in a) + f'</nav>{logo(X)}<nav class="r">' + ''.join(f'<a href="{h}">{l}</a>' for l, h in b) + f'{cta}</nav>{burger}</div></header>')
    if k == 'pill':
        X.css('nav.pill', NAVCSS['pill'])
        return ed('Menü', f'<header class="nv nv3" id="top"><div class="in">{logo(X)}<nav>{L}</nav>{cta}{burger}</div></header>')
    if k == 'min':
        X.css('nav.min', NAVCSS['min'])
        return ed('Menü', f'<header class="nv nv4" id="top"><div class="w">{logo(X)}<a class="nv-tel" href="tel:+{TELRAW}">{ic("tel", 18)} {TEL}</a>{burger}</div></header>')
    if k == 'two':
        X.css('nav.two', NAVCSS['two'])
        return ed('Menü', f'<header class="nv nv5" id="top"><div class="st"><div class="w"><span>{ic("cl", 14)} Pzt–Cmt 08:30–19:00 · Acil için 7/24 arayın</span><span>{X.city} · <a href="tel:+{TELRAW}">{TEL}</a></span></div></div><div class="mn"><div class="w">{logo(X)}<nav>{L}</nav>{cta}{burger}</div></div></header>')
    if k == 'idx':
        X.css('nav.idx', NAVCSS['idx'])
        L2 = ''.join(f'<a href="{h}" data-i="0{i + 1}">{l}</a>' for i, (l, h) in enumerate(X.links))
        return ed('Menü', f'<header class="nv nv6" id="top"><div class="w">{logo(X)}<nav>{L2}</nav>{cta}{burger}</div></header>')
    if k == 'box':
        X.css('nav.box', NAVCSS['box'])
        return ed('Menü', f'<header class="nv nv7" id="top"><div class="w"><div class="in">{logo(X)}<nav>{L}</nav>{cta}{burger}</div></div></header>')
    if k == 'rail':
        X.css('nav.rail', NAVCSS['rail'])
        X.bodycls.append('rail')
        return ed('Menü', f'<header class="nv nv8" id="top"><div class="in">{logo(X)}<span class="vt">Randevu · {TEL}</span>{burger}<span class="tl2">{X.city}</span></div></header>')


# ================================================================== MOBİL MENÜ
def drawer(X):
    X.css('drawer.js', '')
    sheet = X.r.get('drw') == 'sheet'
    sv = ''.join(f'<span class="tag" style="border-color:#ffffff44;background:transparent;color:#fff">{s[0]}</span>' for s in X.c['services'][:5])
    items = ''.join(f'<a href="{h}">{l}<small>0{i + 1}</small></a>' for i, (l, h) in enumerate(X.links))
    return ed('Mobil menü', f'<div class="drw{" sheet" if sheet else ""}"><div class="dh">{logo(X)}<label class="x" for="mn" aria-label="Kapat">{ic("x", 20)}</label></div><div class="dl">{items}</div>'
              f'<div style="margin-top:24px"><div class="eyebrow" style="color:#fff;opacity:.6;margin-bottom:12px">Hizmetlerimiz</div><div class="chips" style="gap:8px">{sv}</div></div>'
              f'<div class="dc"><a class="btn" href="tel:+{TELRAW}">{ic("tel", 18)} {TEL} · Ara</a><a class="btn o" style="color:#fff" href="https://wa.me/{TELRAW}">{ic("wa", 18)} WhatsApp ile yaz</a></div>'
              f'<div class="dn">{ic("cl", 15)} Hafta içi 08:30 – 19:00 · Cumartesi 09:00 – 17:00<br>{ic("pin", 15)} Atatürk Cad. No:12 / {X.city}</div></div>')


# ================================================================== MOBİL BARLAR (14 çeşit)
def _mb(cls, pad, css):
    return f'.{cls}{{display:none}}@media(max-width:900px){{.{cls}{{display:flex}}body{{padding-bottom:{pad}px}}{css}}}'


MB = {
 'dock': (lambda X: f'<nav class="mb mb1" aria-label="Hızlı iletişim"><a href="tel:+{TELRAW}">{ic("tel", 21)}<span>Ara</span></a><a href="https://wa.me/{TELRAW}">{ic("wa", 21)}<span>WhatsApp</span></a><a class="hl" href="#randevu">{ic("cal", 21)}<span>Randevu</span></a><a href="#iletisim">{ic("pin", 21)}<span>Konum</span></a></nav>',
          _mb('mb1', 96, ".mb1{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));z-index:70;display:grid;grid-template-columns:repeat(4,1fr);gap:4px;background:color-mix(in srgb,var(--dk) 90%,transparent);backdrop-filter:blur(16px);border-radius:24px;padding:7px;box-shadow:0 22px 44px -14px #0008;color:#fff}.mb1 a{display:flex;flex-direction:column;align-items:center;gap:4px;padding:9px 0 8px;border-radius:18px;font:600 .68rem/1 var(--fb)}.mb1 a.hl{background:var(--ac);color:var(--on-ac)}")),
 'fab': (lambda X: f'<nav class="mb mb2" aria-label="Hızlı iletişim"><a href="#hizmet">{ic("mn", 21)}<span>Hizmetler</span></a><a href="https://wa.me/{TELRAW}">{ic("wa", 21)}<span>WhatsApp</span></a><a class="fab" href="tel:+{TELRAW}" aria-label="Ara">{ic("tel", 28)}</a><a href="#randevu">{ic("cal", 21)}<span>Randevu</span></a><a href="#iletisim">{ic("pin", 21)}<span>Konum</span></a></nav>',
         _mb('mb2', 78, ".mb2{position:fixed;left:0;right:0;bottom:0;z-index:70;display:grid;grid-template-columns:1fr 1fr 78px 1fr 1fr;align-items:end;background:var(--bg);border-top:1px solid var(--ln);padding:8px 4px calc(8px + env(safe-area-inset-bottom));box-shadow:0 -10px 30px -18px #0004}.mb2 a{display:flex;flex-direction:column;align-items:center;gap:4px;font:600 .66rem/1 var(--fb);color:var(--mut);padding:6px 0}.mb2 a.fab{width:64px;height:64px;margin:-34px auto 0;border-radius:50%;background:var(--ac);color:var(--on-ac);justify-content:center;border:5px solid var(--bg);box-shadow:0 10px 24px -6px color-mix(in srgb,var(--ac) 80%,transparent)}")),
 'one': (lambda X: f'<div class="mb mb3"><a class="go" href="tel:+{TELRAW}"><span class="pulse"></span><b>Hemen ara</b><em>{TEL}</em></a><a class="wa" href="https://wa.me/{TELRAW}" aria-label="WhatsApp">{ic("wa", 24)}</a></div>',
         _mb('mb3', 90, ".mb3{position:fixed;left:10px;right:10px;bottom:calc(10px + env(safe-area-inset-bottom));z-index:70;gap:8px}.mb3 .go{flex:1;display:flex;align-items:center;gap:10px;height:58px;padding:0 20px;background:var(--ac);color:var(--on-ac);border-radius:var(--r);font:700 1rem/1 var(--fb);box-shadow:0 14px 30px -10px color-mix(in srgb,var(--ac) 80%,transparent)}.mb3 .go em{margin-left:auto;font-style:normal;font-weight:600;font-size:.88rem;opacity:.85}.mb3 .wa{width:58px;height:58px;display:grid;place-items:center;border-radius:var(--r);background:#1fa855;color:#fff;box-shadow:0 14px 30px -10px #1fa85599}")),
 'split': (lambda X: f'<div class="mb mb4"><a class="a" href="tel:+{TELRAW}">{ic("tel", 20)} Ara</a><a class="b" href="https://wa.me/{TELRAW}">{ic("wa", 20)} WhatsApp</a></div>',
           _mb('mb4', 60, ".mb4{position:fixed;left:0;right:0;bottom:0;z-index:70}.mb4 a{flex:1;display:flex;align-items:center;justify-content:center;gap:9px;height:60px;padding-bottom:env(safe-area-inset-bottom);font:700 .98rem/1 var(--fb);letter-spacing:.02em}.mb4 .a{background:var(--dk);color:#fff}.mb4 .b{background:#1fa855;color:#fff}")),
 'side': (lambda X: f'<div class="mb mb5"><a class="rz" href="#randevu">Randevu</a><div class="st"><a class="w1" href="https://wa.me/{TELRAW}" aria-label="WhatsApp">{ic("wa", 24)}</a><a class="w2" href="tel:+{TELRAW}" aria-label="Ara">{ic("tel", 24)}</a></div></div>',
          _mb('mb5', 0, ".mb5{position:fixed;inset:auto 0 0 0;z-index:70;pointer-events:none;justify-content:space-between;align-items:flex-end;padding:0 14px calc(18px + env(safe-area-inset-bottom))}.mb5>*{pointer-events:auto}.mb5 .st{display:grid;gap:12px}.mb5 .st a{width:58px;height:58px;border-radius:50%;display:grid;place-items:center;color:#fff;box-shadow:0 14px 30px -8px #0007}.mb5 .w1{background:#1fa855}.mb5 .w2{background:var(--ac);color:var(--on-ac)!important}.mb5 .rz{writing-mode:vertical-rl;transform:rotate(180deg);background:var(--dk);color:#fff;padding:18px 12px;border-radius:12px 0 0 12px;font:700 .8rem/1 var(--fb);letter-spacing:.18em;text-transform:uppercase;margin-left:-14px;margin-bottom:6px}")),
 'status': (lambda X: f'<div class="mb mb6"><span class="pulse"></span><div><b>Şu an hizmetteyiz</b><small>Pzt–Cmt 08:30–19:00</small></div><a href="tel:+{TELRAW}" aria-label="Ara">{ic("tel", 22)}</a></div>',
            _mb('mb6', 72, ".mb6{position:fixed;left:0;right:0;bottom:0;z-index:70;align-items:center;gap:12px;background:var(--dk);color:#fff;padding:10px 14px calc(10px + env(safe-area-inset-bottom)) 18px}.mb6 div{display:grid;gap:3px;flex:1}.mb6 b{font:700 .95rem/1 var(--fb)}.mb6 small{font-size:.74rem;opacity:.65}.mb6 a{width:52px;height:52px;border-radius:50%;background:var(--ac);color:var(--on-ac);display:grid;place-items:center}")),
 'sheet': (lambda X: f'<div class="mb mb7"><input type="checkbox" id="msh" class="hid"><div class="sh"><a href="tel:+{TELRAW}">{ic("tel", 22)}<div><b>Hemen ara</b><small>{TEL}</small></div>{ic("ar", 18)}</a><a href="https://wa.me/{TELRAW}">{ic("wa", 22)}<div><b>WhatsApp’tan yazın</b><small>Fotoğraf ve model bilgisi gönderin</small></div>{ic("ar", 18)}</a><a href="#randevu">{ic("cal", 22)}<div><b>Randevu formu</b><small>Sizi biz arayalım</small></div>{ic("ar", 18)}</a><a href="#iletisim">{ic("pin", 22)}<div><b>Adres ve saatler</b><small>Atatürk Cad. No:12 / {X.city}</small></div>{ic("ar", 18)}</a></div><label for="msh" class="hd"><i></i><span>Hızlı iletişim</span>{ic("dn", 16)}</label></div>',
           _mb('mb7', 60, ".mb7{position:fixed;left:0;right:0;bottom:0;z-index:70;flex-direction:column;background:var(--bg);border-radius:22px 22px 0 0;box-shadow:0 -16px 50px -14px #0006}.mb7 .hd{display:flex;align-items:center;justify-content:center;gap:10px;height:60px;padding-bottom:env(safe-area-inset-bottom);font:700 .92rem/1 var(--fb);cursor:pointer;position:relative}.mb7 .hd i{position:absolute;top:8px;left:50%;width:42px;height:4px;border-radius:4px;background:var(--ln);transform:translateX(-50%)}.mb7 .hd svg{transition:.25s;transform:rotate(180deg)}#msh:checked~.hd svg{transform:none}.mb7 .sh{display:none;padding:18px 16px 4px;gap:6px}#msh:checked~.sh{display:grid}.mb7 .sh a{display:flex;align-items:center;gap:14px;padding:14px 12px;border-radius:14px;background:var(--sf)}.mb7 .sh a>div{flex:1}.mb7 .sh b{display:block;font:700 .95rem/1.2 var(--fb)}.mb7 .sh small{color:var(--mut);font-size:.78rem}.mb7 .sh svg:first-child{color:var(--ac)}.mb7 .sh svg:last-child{color:var(--mut)}")),
 'tabs': (lambda X: f'<nav class="mb mb8" aria-label="Hızlı iletişim"><a class="on" href="#top">{ic("st", 20)}<span>Ana</span></a><a href="#hizmet">{ic("mn", 20)}<span>Hizmet</span></a><a href="#arac">{ic("se", 20)}<span>Araç</span></a><a href="tel:+{TELRAW}">{ic("tel", 20)}<span>Ara</span></a></nav>',
          _mb('mb8', 68, ".mb8{position:fixed;left:0;right:0;bottom:0;z-index:70;display:grid;grid-template-columns:repeat(4,1fr);background:var(--bg);border-top:1px solid var(--ln);padding-bottom:env(safe-area-inset-bottom)}.mb8 a{position:relative;display:flex;flex-direction:column;align-items:center;gap:5px;padding:11px 0 10px;font:600 .68rem/1 var(--fb);color:var(--mut)}.mb8 a.on{color:var(--ac)}.mb8 a.on:before{content:\"\";position:absolute;top:-1px;left:25%;right:25%;height:3px;background:var(--ac);border-radius:0 0 4px 4px}")),
 'bubble': (lambda X: f'<div class="mb mb9"><a class="c" href="tel:+{TELRAW}" aria-label="Ara">{ic("tel", 24)}</a><a class="w" href="https://wa.me/{TELRAW}">{ic("wa", 22)}<span>Yazın, hemen dönelim</span></a></div>',
            _mb('mb9', 0, ".mb9{position:fixed;left:0;right:0;bottom:0;z-index:70;justify-content:space-between;align-items:center;padding:0 14px calc(16px + env(safe-area-inset-bottom));pointer-events:none}.mb9>*{pointer-events:auto;box-shadow:0 14px 30px -8px #0007}.mb9 .c{width:58px;height:58px;border-radius:50%;background:var(--dk);color:#fff;display:grid;place-items:center}.mb9 .w{display:flex;align-items:center;gap:10px;height:58px;padding:0 22px 0 18px;border-radius:99px;background:#1fa855;color:#fff;font:700 .92rem/1 var(--fb)}")),
 'offer': (lambda X: f'<div class="mb mb10"><div><b>Yazılı fiyat</b><small>Onayınız olmadan işlem yok</small></div><a class="bt" href="#randevu">Randevu al</a><a class="tl" href="tel:+{TELRAW}" aria-label="Ara">{ic("tel", 20)}</a></div>',
           _mb('mb10', 76, ".mb10{position:fixed;left:0;right:0;bottom:0;z-index:70;align-items:center;gap:10px;background:var(--bg);border-top:2px solid var(--ac);padding:10px 12px calc(10px + env(safe-area-inset-bottom)) 16px}.mb10 div{flex:1;display:grid;gap:2px;min-width:0}.mb10 b{font:700 .95rem/1.1 var(--fd)}.mb10 small{font-size:.72rem;color:var(--mut)}.mb10 .bt{height:48px;padding:0 20px;display:flex;align-items:center;background:var(--ac);color:var(--on-ac);border-radius:var(--r);font:700 .88rem/1 var(--fb)}.mb10 .tl{width:48px;height:48px;border-radius:var(--r);border:1.5px solid var(--ink);display:grid;place-items:center}")),
 'pill': (lambda X: f'<div class="mb mb11"><a class="n" href="tel:+{TELRAW}">{ic("tel", 22)}<b>{TEL}</b></a><a class="w" href="https://wa.me/{TELRAW}" aria-label="WhatsApp">{ic("wa", 22)}</a></div>',
          _mb('mb11', 92, ".mb11{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(16px + env(safe-area-inset-bottom));width:min(92%,400px);z-index:70;background:var(--dk);color:#fff;border-radius:99px;padding:6px;align-items:center;box-shadow:0 18px 40px -10px #0009}.mb11 .n{flex:1;display:flex;align-items:center;gap:12px;padding:0 16px;height:52px}.mb11 .n b{font:700 1.08rem/1 var(--fd);letter-spacing:.01em}.mb11 .n svg{color:var(--ac)}.mb11 .w{width:52px;height:52px;border-radius:50%;background:#1fa855;display:grid;place-items:center}")),
 'seg': (lambda X: f'<div class="mb mb12"><a href="tel:+{TELRAW}">{ic("tel", 18)} Ara</a><a href="https://wa.me/{TELRAW}">{ic("wa", 18)} Yaz</a><a class="on" href="#randevu">{ic("cal", 18)} Randevu</a></div>',
         _mb('mb12', 82, ".mb12{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));z-index:70;background:var(--bg);border:1.5px solid var(--ink);border-radius:var(--r);overflow:hidden;box-shadow:4px 4px 0 var(--ink)}.mb12 a{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;height:54px;font:700 .86rem/1 var(--fb);border-right:1.5px solid var(--ink)}.mb12 a:last-child{border:0}.mb12 a.on{background:var(--ac);color:var(--on-ac);flex:1.3}")),
 'asym': (lambda X: f'<div class="mb mb13"><a class="big" href="tel:+{TELRAW}">{ic("tel", 24)}<div><small>Hemen arayın</small><b>{TEL}</b></div></a><a class="ic" href="https://wa.me/{TELRAW}" aria-label="WhatsApp">{ic("wa", 22)}</a><a class="ic" href="#iletisim" aria-label="Konum">{ic("pin", 22)}</a></div>',
          _mb('mb13', 72, ".mb13{position:fixed;left:0;right:0;bottom:0;z-index:70;height:72px;padding-bottom:env(safe-area-inset-bottom);box-sizing:content-box}.mb13 .big{flex:2.2;display:flex;align-items:center;gap:14px;padding:0 20px;background:var(--ac);color:var(--on-ac)}.mb13 .big small{display:block;font:600 .68rem/1 var(--fb);letter-spacing:.1em;text-transform:uppercase;opacity:.75;margin-bottom:5px}.mb13 .big b{font:700 1.1rem/1 var(--fd)}.mb13 .ic{flex:.7;display:grid;place-items:center;background:var(--dk);color:#fff}.mb13 .ic+.ic{border-left:1px solid #ffffff22}")),
 'menu': (lambda X: f'<div class="mb mb14"><label for="mn" class="m">{ic("mn", 22)}<span>Menü</span></label><a class="c" href="tel:+{TELRAW}">{ic("tel", 20)} Hemen ara</a><a class="w" href="https://wa.me/{TELRAW}" aria-label="WhatsApp">{ic("wa", 24)}</a></div>',
           _mb('mb14', 76, ".mb14{position:fixed;left:0;right:0;bottom:0;z-index:70;align-items:center;gap:8px;background:var(--bg);border-top:1px solid var(--ln);padding:9px 10px calc(9px + env(safe-area-inset-bottom))}.mb14 .m{display:flex;flex-direction:column;align-items:center;gap:3px;width:56px;font:600 .66rem/1 var(--fb);cursor:pointer}.mb14 .c{flex:1;display:flex;align-items:center;justify-content:center;gap:9px;height:52px;border-radius:99px;background:var(--ac);color:var(--on-ac);font:700 .95rem/1 var(--fb)}.mb14 .w{width:52px;height:52px;border-radius:50%;background:#1fa855;color:#fff;display:grid;place-items:center}")),
 'cart': (lambda X: f'<nav class="mb mb15" aria-label="Mağaza"><a href="#urunler">{ic("mn", 21)}<span>Ürünler</span></a><a href="tel:+{TELRAW}">{ic("tel", 21)}<span>Ara</span></a><a href="https://wa.me/{TELRAW}">{ic("wa", 21)}<span>Parça sor</span></a><a class="ct" href="#" data-cart>{ic("bx", 21)}<span>Sepet</span><i data-ccount>0</i></a></nav>',
          _mb('mb15', 68, ".mb15{position:fixed;left:0;right:0;bottom:0;z-index:70;display:grid;grid-template-columns:repeat(4,1fr);background:var(--bg);border-top:1px solid var(--ln);padding-bottom:env(safe-area-inset-bottom)}.mb15 a{position:relative;display:flex;flex-direction:column;align-items:center;gap:5px;padding:11px 0 10px;font:600 .68rem/1 var(--fb);color:var(--ink)}.mb15 .ct{background:var(--ac);color:var(--on-ac)}.mb15 .ct i{position:absolute;top:6px;right:calc(50% - 26px);font-style:normal;background:var(--dk);color:#fff;min-width:18px;height:18px;border-radius:99px;display:grid;place-items:center;font-size:.64rem;padding:0 4px}")),
}


def mbar(X):
    f, css = MB[X.r['mbar']]
    X.css('mbar.' + X.r['mbar'], css)
    return ed('Mobil bar', f(X))


# ================================================================== ALT BİLGİ
FTCSS = {
 'cols': ".ft1{padding:clamp(44px,6vw,80px) 0 0}.ft1 .g{display:grid;grid-template-columns:1.5fr 1fr 1fr 1fr;gap:40px;padding-bottom:44px}.ft1 .lg{color:#fff;margin-bottom:16px}.ft1 p{max-width:26em;line-height:1.7}.ft1 .c div{margin-bottom:8px}@media(max-width:800px){.ft1 .g{grid-template-columns:1fr 1fr}}@media(max-width:520px){.ft1 .g{grid-template-columns:1fr}}",
 'min': ".ft2{padding:36px 0;background:var(--sf);color:var(--ink)}.ft2 .row{display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap}.ft2 .ls{display:flex;gap:22px;flex-wrap:wrap;font-weight:600;font-size:.9rem}.ft2 .cp{opacity:.65;font-size:.8rem;margin-top:22px;padding-top:18px;border-top:1px solid var(--ln)}.ft2 .lg{color:var(--ink)}",
 'big': ".ft3{overflow:hidden;padding-top:clamp(44px,6vw,80px)}.ft3 .g{display:grid;grid-template-columns:repeat(3,1fr);gap:36px;padding-bottom:30px}.ft3 .wm{font:800 clamp(3.5rem,16vw,13rem)/.8 var(--fd);letter-spacing:-.05em;color:transparent;-webkit-text-stroke:1.5px #ffffff30;white-space:nowrap;margin:20px 0 -.12em;user-select:none}@media(max-width:700px){.ft3 .g{grid-template-columns:1fr}}",
 'cen': ".ft4{padding:clamp(44px,6vw,80px) 0 0;text-align:center}.ft4 .lg{color:#fff;font-size:1.6rem;margin-bottom:18px}.ft4 .tel{display:block;font:700 clamp(1.8rem,5vw,3rem)/1 var(--fd);color:#fff;margin:6px 0 24px}.ft4 .ls{display:flex;justify-content:center;gap:10px 26px;flex-wrap:wrap;margin-bottom:30px}.ft4 .ad{opacity:.7;margin-bottom:30px}",
}


def footer(X):
    k = X.r['ft']
    X.css('ft.' + k, FTCSS[k])
    sv = ''.join(f'<div>{s[0]}</div>' for s in X.c['services'][:4])
    cp = f'<div class="cp"><div class="w">© 2026 {X.nm} · Bu site OnlineKaydet ile yayınlanır</div></div>'
    lk = ''.join(f'<div><a href="{h}">{l}</a></div>' for l, h in X.links)
    hrs = '<div>Hafta içi 08:30 – 19:00</div><div>Cumartesi 09:00 – 17:00</div><div>Acil: 7/24</div>'
    if k == 'cols':
        return ed('Alt bilgi', f'<footer class="ft ft1" id="iletisim"><div class="w g"><div><div class="lg">{X.nm}</div><p>{X.c["label"]} alanında {X.city} ve çevresinde randevulu, kayıtlı ve garantili hizmet.<br>Atatürk Cad. No:12, {X.city}<br>Vergi No: [firma bilgisi]</p></div><div class="c"><b>Hizmetler</b>{sv}</div><div class="c"><b>Bağlantılar</b>{lk}</div><div class="c"><b>Çalışma saatleri</b>{hrs}<div style="margin-top:12px"><a href="tel:+{TELRAW}">{TEL}</a></div></div></div>{cp}</footer>')
    if k == 'min':
        return ed('Alt bilgi', f'<footer class="ft ft2" id="iletisim"><div class="w"><div class="row">{logo(X)}<div class="ls">{"".join(f"<a href={chr(34)}{h}{chr(34)}>{l}</a>" for l, h in X.links)}</div><a class="btn" href="tel:+{TELRAW}">{ic("tel", 18)} {TEL}</a></div><div class="cp">© 2026 {X.nm} · Atatürk Cad. No:12, {X.city} · Bu site OnlineKaydet ile yayınlanır</div></div></footer>')
    if k == 'big':
        return ed('Alt bilgi', f'<footer class="ft ft3" id="iletisim"><div class="w"><div class="g"><div><b>{X.nm}</b>Atatürk Cad. No:12<br>{X.city}<br><a href="tel:+{TELRAW}">{TEL}</a></div><div><b>Hizmetler</b>{sv}</div><div><b>Saatler</b>{hrs}</div></div><div class="wm" aria-hidden="true">{X.nm.split()[0]}</div></div>{cp}</footer>')
    return ed('Alt bilgi', f'<footer class="ft ft4" id="iletisim"><div class="w"><div class="lg">{X.nm}</div><a class="tel" href="tel:+{TELRAW}">{TEL}</a><div class="ls">{"".join(f"<a href={chr(34)}{h}{chr(34)}>{l}</a>" for l, h in X.links)}</div><div class="ad">Atatürk Cad. No:12 · {X.city} · Hafta içi 08:30–19:00</div></div>{cp}</footer>')
