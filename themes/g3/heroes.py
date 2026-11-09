"""14 farklı ana görsel (hero) düzeni."""
from .base import ic
from .navs import TEL, TELRAW, ed

TRUST = ['Yazılı fiyat', 'Servis fişi', 'Garanti belgesi', 'SMS ile takip']


def cta(X, second='tel', cls=''):
    a = f'<a class="btn" href="#randevu">{X.r.get("cta", "Randevu al")} {ic("ar", 18)}</a>'
    if second == 'tel':
        b = f'<a class="btn o" href="tel:+{TELRAW}">{ic("tel", 18)} {TEL}</a>'
    elif second == 'wa':
        b = f'<a class="btn o" href="https://wa.me/{TELRAW}">{ic("wa", 18)} WhatsApp</a>'
    else:
        b = ''
    return f'<div class="cta {cls}">{a}{b}</div>'


def trust(items=None, cls=''):
    return f'<ul class="trust {cls}">' + ''.join(f'<li>{ic("ok", 16)}{t}</li>' for t in (items or TRUST[:3])) + '</ul>'


def h1(X):
    t = X.h[0]
    if X.r.get('em') and ' ' in t:
        a, b = t.rsplit(' ', 1)
        return f'{a} <em>{b}</em>'
    return t


BASE = """.hr{position:relative}.hr .trust{display:flex;flex-wrap:wrap;gap:10px 22px;list-style:none;font:600 .86rem/1 var(--fb)}.hr .trust li{display:flex;align-items:center;gap:7px}.hr .trust svg{color:var(--ac)}
.hr .cta{display:flex;flex-wrap:wrap;gap:12px}.hr h1 em{font-style:var(--emi,normal);color:var(--ac)}.hr .lead{margin:20px 0 30px}
@media(max-width:640px){.hr .cta .btn{flex:1 1 100%}}"""


def hero(X):
    k = X.r['hero']
    X.css('hero.base', BASE)
    return ed('Ana görsel', globals()['hero_' + k](X))


# ---------------------------------------------------------------- 1 split
def hero_split(X):
    X.css('hero.split', """.hr1{padding:clamp(40px,6vw,80px) 0 clamp(56px,8vw,112px)}.hr1 .g{display:grid;grid-template-columns:1.05fr .95fr;gap:clamp(32px,6vw,84px);align-items:center}.hr1 h1{margin:18px 0 0}.hr1 .trust{margin-top:34px}
.hr1 .im{position:relative;isolation:isolate}.hr1 .im .ph{aspect-ratio:4/5;max-height:600px;width:100%;border-radius:calc(var(--r)*1.8)}.hr1 .im:before{content:"";position:absolute;inset:20px -20px -20px 20px;border:1.5px solid var(--ac);border-radius:calc(var(--r)*1.8);z-index:-1}
.hr1 .fl{position:absolute;left:-26px;bottom:34px;background:var(--bg);color:var(--ink);padding:16px 20px;border-radius:var(--r);box-shadow:0 22px 50px -18px #0006;display:flex;gap:14px;align-items:center;max-width:260px}.hr1 .fl .ci{width:42px;height:42px;border-radius:50%;background:var(--ac);color:var(--on-ac);display:grid;place-items:center;flex:none}.hr1 .fl b{display:block;font:700 .95rem/1.2 var(--fd)}.hr1 .fl small{font-size:.76rem;color:var(--mut)}
@media(max-width:900px){.hr1 .g{grid-template-columns:1fr}.hr1 .im{order:-1}.hr1 .im .ph{aspect-ratio:16/11}.hr1 .fl{left:12px;bottom:-22px}.hr1 .im:before{inset:12px -10px -12px 10px}}""")
    return (f'<section class="hr hr1" id="top2"><div class="w g"><div class="rv"><span class="eyebrow">{X.c["label"]} servisi · {X.city}</span><h1>{h1(X)}</h1><p class="lead">{X.h[1]}</p>{cta(X)}{trust()}</div>'
            f'<div class="im rv rv2">{X.ph("im", "center")}<div class="fl"><span class="ci">{ic("sh", 20)}</span><div><b>Onayınız olmadan işlem yok</b><small>Fiyat yazılı bildirilir</small></div></div></div></div></section>')


# ---------------------------------------------------------------- 2 full-bleed + hızlı form
def hero_full(X):
    X.css('hero.full', """.hr2{color:#fff;overflow:hidden;--hc:#fff;--mut:#ffffffbb}.hr2 .bgp{position:absolute;inset:0}.hr2 .bgp .ph{position:absolute;inset:0}.hr2 .bgp:after{content:"";position:absolute;inset:0;background:linear-gradient(100deg,color-mix(in srgb,var(--dk) 94%,transparent) 8%,color-mix(in srgb,var(--dk) 72%,transparent) 52%,color-mix(in srgb,var(--dk) 30%,transparent))}
.hr2 .g{position:relative;display:grid;grid-template-columns:1.15fr .85fr;gap:clamp(30px,5vw,80px);align-items:center;padding:clamp(60px,9vw,130px) 0}.hr2 h1{margin-top:18px;color:#fff}.hr2 .eyebrow{color:#fff}.hr2 .lead{color:#ffffffc8}.hr2 .trust{margin-top:34px}.hr2 .btn.o{color:#fff}
.hr2 .qf{background:var(--bg);color:var(--ink);padding:clamp(22px,3vw,34px);border-radius:calc(var(--r)*1.4);box-shadow:0 40px 90px -30px #000a;--hc:var(--ink);--mut:#6b7280}.hr2 .qf h3{margin-bottom:4px;font-size:1.4rem}.hr2 .qf>p{color:var(--mut);font-size:.9rem;margin-bottom:6px}
@media(max-width:900px){.hr2 .g{grid-template-columns:1fr}.hr2 .bgp:after{background:linear-gradient(180deg,color-mix(in srgb,var(--dk) 80%,transparent),color-mix(in srgb,var(--dk) 92%,transparent))}}""")
    return (f'<section class="hr hr2" id="top2"><div class="bgp">{X.ph("im", "center 40%")}</div><div class="w g"><div class="rv"><span class="eyebrow">{X.c["label"]} · {X.city}</span><h1>{h1(X)}</h1><p class="lead">{X.h[1]}</p>{cta(X, "wa")}{trust()}</div>'
            f'<div class="rv rv2">{X.quickform("hq", "Hızlı randevu", "2 dakikada doldurun, sizi arayalım.")}</div></div></section>')


# ---------------------------------------------------------------- 3 editoryal
def hero_edit(X):
    X.css('hero.edit', """.hr3{padding:clamp(28px,4vw,52px) 0 clamp(56px,8vw,110px)}.hr3 .top{display:flex;justify-content:space-between;align-items:center;padding-bottom:18px;border-bottom:1.5px solid var(--ink);margin-bottom:clamp(24px,4vw,48px)}.hr3 .no{font:600 .78rem/1 var(--fb);letter-spacing:.14em;text-transform:uppercase}
.hr3 h1{font-size:clamp(2.6rem,9.2vw,8.2rem);line-height:.95;letter-spacing:-.045em;font-weight:var(--hw1,400);max-width:14ch}.hr3 .g3{display:grid;grid-template-columns:1fr 1.5fr 1fr;gap:clamp(20px,3vw,44px);align-items:end;margin-top:clamp(30px,5vw,64px)}.hr3 .g3 .ph{aspect-ratio:16/10;border-radius:calc(var(--r)*.8)}.hr3 .lead{margin:0 0 22px}
.hr3 .ls{display:grid;gap:0;border-top:1.5px solid var(--ink)}.hr3 .ls a{display:flex;justify-content:space-between;align-items:center;padding:16px 0;border-bottom:1px solid var(--ln);font:600 1rem/1 var(--fd);transition:.2s}.hr3 .ls a:hover{padding-left:10px;color:var(--ac)}
@media(max-width:900px){.hr3 .g3{grid-template-columns:1fr}.hr3 .g3 .ph{order:-1}}""")
    return (f'<section class="hr hr3" id="top2"><div class="w"><div class="top"><span class="eyebrow">{X.c["tag"]}</span><span class="no">{X.city} · Servis rehberi</span></div><h1 class="rv">{h1(X)}</h1>'
            f'<div class="g3"><div><p class="lead">{X.h[1]}</p>{trust(None)}</div><div class="rv rv2">{X.ph("im", "center")}</div><div class="ls"><a href="#randevu">{X.r.get("cta", "Randevu al")}{ic("ar", 18)}</a><a href="tel:+{TELRAW}">{TEL}{ic("tel", 18)}</a><a href="https://wa.me/{TELRAW}">WhatsApp{ic("wa", 18)}</a></div></div></div></section>')


# ---------------------------------------------------------------- 4 araç önde
def hero_tool(X):
    X.css('hero.tool', """.hr4{background:var(--sf);padding:clamp(36px,5vw,72px) 0 clamp(56px,8vw,100px)}.hr4 .g{display:grid;grid-template-columns:.85fr 1.15fr;gap:clamp(28px,5vw,70px);align-items:center}.hr4 h1{margin:18px 0 0;font-size:clamp(2rem,4.6vw,3.8rem)}.hr4 .trust{margin-top:30px}.hr4 .tl{box-shadow:0 40px 90px -40px #0005}
@media(max-width:1000px){.hr4 .g{grid-template-columns:1fr}}""")
    th, tj, _ = X.tool(0, 'a', in_hero=True)
    return (f'<section class="hr hr4" id="top2"><div class="w g"><div class="rv"><span class="eyebrow">{X.c["label"]} · ücretsiz araç</span><h1>{h1(X)}</h1><p class="lead">{X.h[1]}</p>{cta(X, "tel")}{trust()}</div><div class="rv rv2">{th}</div></div></section>')


# ---------------------------------------------------------------- 5 rakamlar
def hero_stats(X):
    X.css('hero.stats', """.hr5{padding:clamp(40px,6vw,84px) 0 0}.hr5 .g{display:grid;grid-template-columns:1.2fr .8fr;gap:clamp(28px,5vw,72px);align-items:end}.hr5 h1{margin:18px 0 0}.hr5 .st{display:grid;grid-template-columns:1fr 1fr;border:1.5px solid var(--ink);border-radius:var(--r);overflow:hidden}
.hr5 .st div{padding:clamp(18px,2.4vw,30px);border-right:1.5px solid var(--ink);border-bottom:1.5px solid var(--ink);display:grid;gap:8px}.hr5 .st div:nth-child(2n){border-right:0}.hr5 .st div:nth-child(n+3){border-bottom:0}.hr5 .st small{font:600 .72rem/1 var(--fb);letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}
.hr5 .st b{font:700 clamp(1.4rem,3vw,2.2rem)/1 var(--fd);letter-spacing:-.03em}.hr5 .st div.ac{background:var(--ac);color:var(--on-ac)}.hr5 .st div.ac small{color:inherit;opacity:.8}.hr5 .tk{margin-top:clamp(40px,6vw,80px);border-block:1.5px solid var(--ink);overflow:hidden}
.hr5 .tk div{display:flex;gap:46px;white-space:nowrap;padding:18px 0;animation:mq 34s linear infinite;width:max-content;font:700 1.1rem/1 var(--fd);letter-spacing:.06em;text-transform:uppercase}@keyframes mq{to{transform:translateX(-50%)}}.hr5 .tk span:after{content:"✦";margin-left:46px;color:var(--ac)}
@media(max-width:900px){.hr5 .g{grid-template-columns:1fr}}""")
    bs = ''.join(f'<span>{b}</span>' for b in X.c['brands']) * 2
    return (f'<section class="hr hr5" id="top2"><div class="w"><div class="g"><div class="rv"><span class="eyebrow">{X.c["label"]} · {X.city}</span><h1>{h1(X)}</h1><p class="lead">{X.h[1]}</p>{cta(X)}</div>'
            f'<div class="st rv rv2"><div><small>Teşhis</small><b>Yazılı</b></div><div class="ac"><small>Fiyat</small><b>Önceden</b></div><div><small>Takip</small><b>SMS ile</b></div><div><small>Garanti</small><b>Belgeli</b></div></div></div></div><div class="tk"><div>{bs}</div></div></section>')


# ---------------------------------------------------------------- 6 acil hat
def hero_sos(X):
    X.css('hero.sos', """.hr6{background:var(--dk);color:#fff;--hc:#fff;--mut:#ffffffb8;overflow:hidden}.hr6:before{content:"";display:block;height:14px;background:repeating-linear-gradient(135deg,var(--ac) 0 18px,#0c0c0c 18px 36px)}
.hr6 .g{display:grid;grid-template-columns:1.2fr .8fr;gap:clamp(24px,5vw,70px);align-items:center;padding:clamp(40px,6vw,84px) 0}.hr6 .tg{display:inline-flex;align-items:center;gap:10px;padding:9px 16px;border:1px solid #ffffff3a;border-radius:99px;font:600 .82rem/1 var(--fb);margin-bottom:22px}
.hr6 .num{display:block;font:800 clamp(2.6rem,9vw,7rem)/1 var(--fd);letter-spacing:-.04em;color:var(--ac);margin:6px 0 20px;white-space:nowrap}.hr6 h1{font-size:clamp(1.5rem,3vw,2.4rem);font-weight:600;letter-spacing:-.01em;color:#fff;max-width:20em}.hr6 .lead{margin:16px 0 28px}
.hr6 .btn.o{color:#fff}.hr6 .ph{aspect-ratio:1;border-radius:50%;max-width:440px;margin-left:auto;border:10px solid #ffffff12}.hr6 .eta{display:flex;gap:26px;margin-top:30px;flex-wrap:wrap;font:600 .86rem/1.2 var(--fb);color:#ffffffc0}.hr6 .eta span{display:flex;gap:9px;align-items:center}.hr6 .eta svg{color:var(--ac)}
@media(max-width:900px){.hr6 .g{grid-template-columns:1fr}.hr6 .ph{max-width:240px;margin:0}}""")
    return (f'<section class="hr hr6" id="top2"><div class="w g"><div class="rv"><span class="tg"><span class="pulse"></span>Şu an arama alıyoruz · 7/24 acil hat</span><a class="num" href="tel:+{TELRAW}">{TEL}</a><h1>{X.h[0]}</h1><p class="lead">{X.h[1]}</p>{cta(X, "wa")}'
            f'<div class="eta"><span>{ic("cl", 18)} Arayınca tahmini varış süresi söylenir</span><span>{ic("sh", 18)} Yazılı fiyat</span></div></div><div class="rv rv2">{X.ph("im", "center")}</div></div></section>')


# ---------------------------------------------------------------- 7 arama kutusu
def hero_search(X):
    X.css('hero.search', """.hr7{background:var(--sf);padding:clamp(48px,7vw,104px) 0 clamp(48px,6vw,84px);text-align:center}.hr7 h1{margin:18px auto 0;max-width:16em}.hr7 .lead{margin:18px auto 34px}
.hr7 .sb{display:flex;max-width:760px;margin:0 auto;background:var(--bg);border:2px solid var(--ink);border-radius:var(--r);overflow:hidden;box-shadow:6px 6px 0 var(--ink)}.hr7 .sb select{border:0;border-right:2px solid var(--ink);padding:0 38px 0 18px;font:700 .92rem/1 var(--fb);background:var(--sf);appearance:none;-webkit-appearance:none;min-width:150px;color:var(--ink);background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23333' stroke-width='3'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 14px center}
.hr7 .sb input{flex:1;border:0;padding:20px;font:500 1.05rem/1 var(--fb);min-width:0;background:transparent;color:var(--ink)}.hr7 .sb input:focus,.hr7 .sb select:focus{outline:0;background:color-mix(in srgb,var(--ac) 8%,var(--bg))}.hr7 .sb button{background:var(--ac);color:var(--on-ac);padding:0 30px;font:800 .95rem/1 var(--fb);letter-spacing:.04em;display:flex;align-items:center;gap:8px}
.hr7 .chips{justify-content:center;margin-top:24px}.hr7 .chips button{background:var(--bg)}.hr7 .trust{justify-content:center;margin-top:34px}
@media(max-width:640px){.hr7 .sb{flex-direction:column;box-shadow:4px 4px 0 var(--ink)}.hr7 .sb select{border-right:0;border-bottom:2px solid var(--ink);min-height:54px}.hr7 .sb button{min-height:56px;justify-content:center}}""")
    opts = ''.join(f'<option>{c}</option>' for c in X.c['cihaz'])
    chips = ''.join(f'<button type="button">{p}</button>' for p in X.c['prob'])
    X.js('SEARCH')
    return (f'<section class="hr hr7" id="top2"><div class="w"><span class="eyebrow">{X.c["label"]} · {X.c["tag"]}</span><h1 class="rv">{h1(X)}</h1><p class="lead rv rv2">{X.h[1]}</p>'
            f'<form class="sb rv rv3" id="hs" action="#randevu"><select aria-label="Cihaz">{opts}</select><input placeholder="Sorununuzu ya da model kodunu yazın…" aria-label="Sorun"><button type="submit">{ic("se", 18)} Başlat</button></form>'
            f'<div class="chips" id="hsc">{chips}</div>{trust(None)}</div></section>')


# ---------------------------------------------------------------- 8 çapraz blok
def hero_diag(X):
    X.css('hero.diag', """.hr8{position:relative;overflow:hidden;background:var(--dk);min-height:600px;display:flex;align-items:stretch}.hr8 .pho{position:absolute;inset:0 0 0 34%}.hr8 .pho .ph{position:absolute;inset:0}
.hr8 .bl{position:relative;z-index:2;width:66%;background:var(--ac);color:var(--on-ac);clip-path:polygon(0 0,100% 0,84% 100%,0 100%);display:flex;align-items:center;--hc:var(--on-ac);--mut:color-mix(in srgb,var(--on-ac) 80%,transparent)}
.hr8 .in{width:min(1200px,100% - 48px);margin-inline:auto;padding:clamp(48px,7vw,100px) clamp(60px,10vw,160px) clamp(48px,7vw,100px) 0}.hr8 .tx{max-width:560px}.hr8 h1{margin:16px 0 0;color:var(--on-ac)}.hr8 .eyebrow{color:var(--on-ac)}.hr8 .lead{color:color-mix(in srgb,var(--on-ac) 85%,transparent)}
.hr8 .btn{background:var(--on-ac);color:var(--ac);border-color:var(--on-ac)}.hr8 .btn.o{background:transparent;color:var(--on-ac)}.hr8 .trust svg{color:var(--on-ac)}
@media(max-width:900px){.hr8{flex-direction:column;min-height:0}.hr8 .pho{position:relative;inset:auto;height:240px;order:-1}.hr8 .bl{clip-path:none;width:100%}.hr8 .in{padding:36px 0 52px;width:min(100% - 36px,1200px)}}""")
    return (f'<section class="hr hr8" id="top2"><div class="pho">{X.ph("im", "center")}</div><div class="bl"><div class="in"><div class="tx rv"><span class="eyebrow">{X.c["label"]} · {X.city}</span><h1>{h1(X)}</h1><p class="lead">{X.h[1]}</p>{cta(X)}{trust(None)}</div></div></div></section>')


# ---------------------------------------------------------------- 9 dilimler
def hero_slices(X):
    X.css('hero.slices', """.hr9{position:relative;color:#fff;--hc:#fff;--mut:#ffffffc0;background:var(--dk)}.hr9 .sl{display:flex;height:min(86vh,700px);min-height:520px}.hr9 .s{flex:1;position:relative;overflow:hidden;transition:flex .6s cubic-bezier(.2,.7,.2,1);border-right:1px solid #ffffff22}.hr9 .s .ph{position:absolute;inset:0;transition:transform .8s}.hr9 .s:hover{flex:2.3}.hr9 .s:hover .ph{transform:scale(1.05)}
.hr9 .ov{position:absolute;inset:0;background:linear-gradient(180deg,color-mix(in srgb,var(--dk) 55%,transparent),color-mix(in srgb,var(--dk) 86%,transparent));pointer-events:none}.hr9 .tx{position:absolute;left:0;right:0;bottom:0;padding-bottom:clamp(36px,5vw,72px);z-index:3;pointer-events:none}.hr9 .tx>*{pointer-events:auto}.hr9 h1{max-width:14em;color:#fff;margin:16px 0 0}.hr9 .lead{margin:16px 0 26px;color:#ffffffd0;max-width:30em}.hr9 .btn.o{color:#fff}.hr9 .eyebrow{color:#fff}
.hr9 .lb{position:absolute;top:26px;left:20px;z-index:3;font:600 .72rem/1 var(--fb);letter-spacing:.16em;text-transform:uppercase;opacity:.85}
@media(max-width:800px){.hr9 .sl{height:auto;min-height:620px}.hr9 .s:not(:first-child){display:none}.hr9 .s{border:0}}""")
    pos = ['30% center', 'center', '70% center']
    sl = ''.join(f'<div class="s">{X.ph(v, p)}<span class="lb">0{i + 1}</span></div>' for i, (v, p) in enumerate(zip(['im', 'im2', 'im3'], pos)))
    return (f'<section class="hr hr9" id="top2"><div class="sl">{sl}</div><div class="ov"></div><div class="tx"><div class="w rv"><span class="eyebrow">{X.c["label"]} servisi · {X.city}</span><h1>{h1(X)}</h1><p class="lead">{X.h[1]}</p>{cta(X)}</div></div></section>')


# ---------------------------------------------------------------- 10 kemer
def hero_arch(X):
    X.css('hero.arch', """.hr10{padding:clamp(40px,6vw,84px) 0 clamp(56px,8vw,110px);text-align:center;background:linear-gradient(var(--sf),var(--bg))}.hr10 h1{margin:18px auto 0;max-width:15em}.hr10 .lead{margin:20px auto 30px}.hr10 .cta{justify-content:center}
.hr10 .g{display:grid;grid-template-columns:1fr minmax(260px,380px) 1fr;gap:clamp(20px,4vw,60px);align-items:end;margin-top:clamp(36px,5vw,64px);text-align:left}.hr10 .ph{aspect-ratio:3/4;border-radius:999px 999px calc(var(--r)*1.2) calc(var(--r)*1.2)}.hr10 .sd{display:grid;gap:22px;padding-bottom:30px}.hr10 .sd.r{text-align:right;justify-items:end}
.hr10 .sd b{display:block;font:700 1.15rem/1.2 var(--fd);margin-bottom:5px}.hr10 .sd span{color:var(--mut);font-size:.92rem}.hr10 .sd i{display:grid;place-items:center;width:46px;height:46px;border-radius:50%;border:1.5px solid var(--ac);color:var(--ac);margin-bottom:12px}
@media(max-width:900px){.hr10 .g{grid-template-columns:1fr;text-align:center}.hr10 .sd,.hr10 .sd.r{text-align:center;justify-items:center;padding:0}.hr10 .ph{max-width:300px;margin:0 auto;order:-1}}""")
    return (f'<section class="hr hr10" id="top2"><div class="w"><span class="eyebrow">{X.c["tag"]}</span><h1 class="rv">{h1(X)}</h1><p class="lead rv rv2">{X.h[1]}</p>{cta(X)}'
            f'<div class="g rv rv3"><div class="sd"><div><i>{ic("sh", 22)}</i><b>Yazılı fiyat</b><span>Onay vermeden işlem yapılmaz.</span></div><div><i>{ic("cl", 22)}</i><b>Randevulu servis</b><span>SMS ile hatırlatma ve takip.</span></div></div>'
            f'{X.ph("im", "center 30%")}<div class="sd r"><div><i>{ic("dc", 22)}</i><b>Servis fişi</b><span>İşlem sonrası imzalı kayıt.</span></div><div><i>{ic("st", 22)}</i><b>Garanti belgesi</b><span>Parça ve işçilik için yazılı.</span></div></div></div></div></section>')


# ---------------------------------------------------------------- 11 konsol
def hero_console(X):
    X.css('hero.console', """.hr11{background:var(--dk);color:#fff;--hc:#fff;--mut:#ffffffab;--ln:#ffffff26;background-image:linear-gradient(#ffffff0a 1px,transparent 1px),linear-gradient(90deg,#ffffff0a 1px,transparent 1px);background-size:44px 44px;padding:clamp(48px,7vw,104px) 0}
.hr11 .g{display:grid;grid-template-columns:1.1fr .9fr;gap:clamp(28px,5vw,80px);align-items:center}.hr11 .eyebrow{font-family:var(--fm,var(--fb));color:var(--ac)}.hr11 h1{margin:18px 0 0;color:#fff;font-size:clamp(2rem,4.8vw,4rem)}.hr11 .btn.o{color:#fff}
.hr11 .pn{background:#0b0e12;border:1px solid #ffffff2b;border-radius:var(--r);overflow:hidden;box-shadow:0 40px 90px -30px #000}.hr11 .pn .bar{display:flex;align-items:center;gap:7px;padding:13px 16px;border-bottom:1px solid #ffffff1c;background:#ffffff08;font:500 .76rem/1 var(--fm,var(--fb));color:#ffffff99}.hr11 .pn .bar i{width:10px;height:10px;border-radius:50%;background:#ffffff30}.hr11 .pn .bar span{margin-left:auto}
.hr11 .rw{display:flex;align-items:center;gap:16px;padding:17px 20px;border-bottom:1px solid #ffffff14;font:500 .9rem/1.2 var(--fb)}.hr11 .rw:last-of-type{border:0}.hr11 .rw em{margin-left:auto;font:500 .75rem/1 var(--fm,var(--fb));color:#ffffff77;font-style:normal}.hr11 .rw .d{flex:none;width:26px;height:26px;border-radius:50%;display:grid;place-items:center;border:1.5px solid #ffffff33;color:#ffffff55}
.hr11 .rw.ok .d{background:var(--ac);border-color:var(--ac);color:var(--on-ac)}.hr11 .rw.on .d{border-color:var(--ac);color:var(--ac);box-shadow:0 0 0 5px color-mix(in srgb,var(--ac) 22%,transparent)}.hr11 .rw.ok,.hr11 .rw.on{color:#fff}.hr11 .rw:not(.ok):not(.on){color:#ffffff66}.hr11 .ft0{padding:12px 20px;font:500 .72rem/1.3 var(--fm,var(--fb));color:#ffffff66;border-top:1px solid #ffffff14}
@media(max-width:900px){.hr11 .g{grid-template-columns:1fr}}""")
    rows = [('ok', 'Talep alındı', '09:12'), ('ok', 'Usta atandı', '09:20'), ('on', 'Yolda · randevu 10:30', '10:05'), ('', 'Teşhis ve yazılı fiyat', '—'), ('', 'Onarım ve teslim', '—')]
    rh = ''.join(f'<div class="rw {c}"><span class="d">{ic("ok", 14) if c == "ok" else ("●" if c == "on" else "")}</span>{t}<em>{m}</em></div>' for c, t, m in rows)
    return (f'<section class="hr hr11" id="top2"><div class="w g"><div class="rv"><span class="eyebrow">// servis kaydı · {X.c["label"].lower()}</span><h1>{h1(X)}</h1><p class="lead">{X.h[1]}</p>{cta(X)}</div>'
            f'<div class="pn rv rv2"><div class="bar"><i></i><i></i><i></i><span>kayit_2026-0482</span></div>{rh}<div class="ft0">Örnek kayıt ekranı · müşteriniz durumu SMS ile bu şekilde izler</div></div></div></section>')


# ---------------------------------------------------------------- 12 servis fişi
def hero_ticket(X):
    X.css('hero.ticket', """.hr12{padding:clamp(40px,6vw,84px) 0 clamp(56px,8vw,110px);background:var(--sf)}.hr12 .g{display:grid;grid-template-columns:1.1fr .9fr;gap:clamp(30px,6vw,90px);align-items:center}.hr12 h1{margin:18px 0 0}.hr12 .trust{margin-top:32px}
.hr12 .tk{position:relative;background:#fffdf5;color:#1c1b17;padding:34px 30px 38px;max-width:400px;margin:0 auto;transform:rotate(2deg);box-shadow:0 36px 70px -26px #0006;font:500 .86rem/1.5 var(--fm,ui-monospace,monospace);-webkit-mask:radial-gradient(circle 9px at 9px 100%,#0000 98%,#000) -9px 0/18px 100% repeat-x;mask:radial-gradient(circle 9px at 9px 100%,#0000 98%,#000) -9px 0/18px 100% repeat-x;mask-position:0 100%;-webkit-mask-position:0 100%;mask-size:18px 100%}
.hr12 .tk b{display:block;font:700 1.15rem/1 var(--fd);letter-spacing:.04em;text-transform:uppercase;margin-bottom:4px}.hr12 .tk hr{border:0;border-top:1.5px dashed #1c1b1766;margin:14px 0}.hr12 .tk .r{display:flex;justify-content:space-between;gap:16px}.hr12 .tk .r span:first-child{opacity:.6}.hr12 .bc{height:46px;background:repeating-linear-gradient(90deg,#1c1b17 0 2px,transparent 2px 5px,#1c1b17 5px 6px,transparent 6px 10px,#1c1b17 10px 13px,transparent 13px 16px);margin-top:6px}.hr12 .tk small{display:block;text-align:center;opacity:.55;margin-top:10px;font-size:.72rem}
.hr12 .st{display:inline-flex;align-items:center;gap:7px;padding:4px 10px;border-radius:99px;background:var(--ac);color:var(--on-ac);font-weight:700;font-size:.74rem}
@media(max-width:900px){.hr12 .g{grid-template-columns:1fr}.hr12 .tk{transform:none}}""")
    return (f'<section class="hr hr12" id="top2"><div class="w g"><div class="rv"><span class="eyebrow">{X.c["label"]} · {X.city}</span><h1>{h1(X)}</h1><p class="lead">{X.h[1]}</p>{cta(X)}{trust()}</div>'
            f'<div class="rv rv2"><div class="tk"><b>{X.nm}</b><div>Servis fişi</div><hr><div class="r"><span>İş no</span><span>2026-0482</span></div><div class="r"><span>Cihaz</span><span>{X.c["cihaz"][0]}</span></div><div class="r"><span>Belirti</span><span>{X.c["prob"][0]}</span></div><div class="r"><span>Randevu</span><span>Bugün 10:30</span></div><div class="r"><span>Durum</span><span class="st">● Yolda</span></div><hr><div class="r"><span>Fiyat</span><span>Teşhis sonrası yazılı</span></div><div class="bc"></div><small>Örnek fiş · müşteriye SMS ile gönderilir</small></div></div></div></section>')


# ---------------------------------------------------------------- 13 mozaik
def hero_mosaic(X):
    X.css('hero.mosaic', """.hr13{padding:clamp(28px,4vw,56px) 0 clamp(56px,8vw,100px)}.hr13 .g{display:grid;grid-template-columns:repeat(12,1fr);grid-template-rows:auto auto;gap:14px}.hr13 .tx{grid-column:1/7;grid-row:1/3;background:var(--dk);color:#fff;--hc:#fff;--mut:#ffffffbb;border-radius:calc(var(--r)*1.6);padding:clamp(28px,4vw,60px);display:flex;flex-direction:column;justify-content:center}
.hr13 .tx h1{margin:18px 0 0;font-size:clamp(2rem,4.2vw,3.6rem);color:#fff}.hr13 .tx .eyebrow{color:var(--ac)}.hr13 .tx .btn.o{color:#fff}.hr13 .a{grid-column:7/13;border-radius:calc(var(--r)*1.6);aspect-ratio:16/10}.hr13 .b,.hr13 .c{border-radius:calc(var(--r)*1.6);aspect-ratio:1}.hr13 .b{grid-column:7/10}.hr13 .c{grid-column:10/13;background:var(--ac);color:var(--on-ac);display:grid;align-content:center;justify-items:start;padding:22px;gap:6px;aspect-ratio:auto}
.hr13 .c b{font:700 clamp(1.4rem,3vw,2.4rem)/1 var(--fd);letter-spacing:-.03em}.hr13 .c small{font:600 .76rem/1.3 var(--fb);opacity:.85;letter-spacing:.06em;text-transform:uppercase}.hr13 .c svg{margin-bottom:10px}
@media(max-width:900px){.hr13 .g{grid-template-columns:1fr 1fr}.hr13 .tx{grid-column:1/3;grid-row:auto}.hr13 .a{grid-column:1/3}.hr13 .b{grid-column:1/2}.hr13 .c{grid-column:2/3}}""")
    return (f'<section class="hr hr13" id="top2"><div class="w"><div class="g"><div class="tx rv"><span class="eyebrow">{X.c["label"]} · {X.city}</span><h1>{h1(X)}</h1><p class="lead">{X.h[1]}</p>{cta(X)}</div>{X.ph("im", "center", "a rv rv2")}{X.ph("im2", "center", "b rv rv3")}'
            f'<div class="c rv rv3">{ic("sh", 28)}<b>Yazılı fiyat</b><small>Onayınız olmadan işlem yok</small></div></div></div></section>')


# ---------------------------------------------------------------- 14 tipografik
def hero_marquee(X):
    X.css('hero.marquee', """.hr14{padding:clamp(24px,4vw,48px) 0 clamp(56px,8vw,100px);overflow:hidden;text-align:center}.hr14 .mq{overflow:hidden;margin-bottom:clamp(20px,3vw,40px)}.hr14 .mq div{display:flex;gap:50px;width:max-content;animation:mq2 40s linear infinite;font:800 clamp(5rem,17vw,15rem)/.9 var(--fd);letter-spacing:-.05em;color:transparent;-webkit-text-stroke:2px var(--ink);text-transform:uppercase;white-space:nowrap}
@keyframes mq2{to{transform:translateX(-50%)}}.hr14 .mq span:nth-child(even){-webkit-text-stroke:0;color:var(--ac)}.hr14 h1{max-width:15em;margin:0 auto;font-size:clamp(1.9rem,4.4vw,3.6rem)}.hr14 .lead{margin:18px auto 28px}.hr14 .cta{justify-content:center}.hr14 .sp{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:clamp(36px,5vw,64px)}.hr14 .sp .ph{aspect-ratio:4/3;border-radius:calc(var(--r)*1.3)}.hr14 .sp .ph:nth-child(2){margin-top:34px}
@media(max-width:700px){.hr14 .sp{grid-template-columns:1fr 1fr}.hr14 .sp .ph:nth-child(3){display:none}.hr14 .sp .ph:nth-child(2){margin-top:20px}}""")
    wd = f'<span>{X.c["label"]}</span><span>servisi</span>' * 4
    return (f'<section class="hr hr14" id="top2"><div class="mq" aria-hidden="true"><div>{wd}</div></div><div class="w"><span class="eyebrow">{X.city} · {X.c["tag"]}</span><h1 style="margin-top:16px" class="rv">{h1(X)}</h1><p class="lead rv rv2">{X.h[1]}</p>{cta(X)}'
            f'<div class="sp rv rv3">{X.ph("im", "30% center")}{X.ph("im2", "center")}{X.ph("im3", "70% center")}</div></div></section>')
