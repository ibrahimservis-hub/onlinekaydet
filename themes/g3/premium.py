"""Premium tema katmanı: 4 yön (cine / edit / neon / lux), premium menü, hareket (CSS+JS), sayaç ve kayan bant bölümleri.
Fiyat yazılmaz; her yerde 'Teklif alın'. Mağaza bölümü varsayılan kapalıdır (data-dflt="off"), müşteri editörden 'Göster' ile açar."""
from .base import ic
from .navs import TEL, TELRAW, ed, logo, links_html

DIRS = ('cine', 'edit', 'neon', 'lux')


def _h1(X, em=True):
    t = X.h[0]
    if em and ' ' in t:
        a, b = t.rsplit(' ', 1)
        return f'{a} <em>{b}</em>'
    return t


def _btns(X, second='tel'):
    a = f'<a class="btn" href="#randevu">{X.r.get("cta", "Teklif alın")} {ic("ar", 18)}</a>'
    b = f'<a class="btn o" href="tel:+{TELRAW}">{ic("tel", 18)} {TEL}</a>' if second == 'tel' else f'<a class="btn o" href="https://wa.me/{TELRAW}">{ic("wa", 18)} WhatsApp</a>'
    return f'<div class="cta">{a}{b}</div>'


def _cnt(to, sf='', d=0):
    if isinstance(to, str):
        return f'<b>{to}</b>'
    return f'<b class="cnt" data-to="{to}" data-sf="{sf}" data-d="{d}">{_fmt(to, sf, d)}</b>'


def _fmt(to, sf, d):
    s = f'{to:,.{d}f}'.replace(',', '.') if d == 0 else f'{to:.{d}f}'.replace('.', ',')
    return s + sf


# Kanıtlanamayan sayı yazılmaz: güven maddeleri söz verilen hizmetlerdir (sayaç yok).
STATS = [('Ücretsiz', '', 0, 'Keşif ve ön bilgi'), ('Yazılı', '', 0, 'Fiyat, işe başlamadan önce'), ('İmzalı', '', 0, 'Servis fişi, SMS ile'), ('Garantili', '', 0, 'Yapılan işe belge')]


def _imv(X):
    return X.r.get('imv', 'im')


# ------------------------------------------------------------------ MENÜ
NAVCSS = """.pnv{position:absolute;top:0;left:0;right:0;z-index:50;color:#fff;transition:background .3s,backdrop-filter .3s}.pnv .in{display:flex;align-items:center;gap:30px;width:min(1240px,100% - 48px);margin-inline:auto;padding:22px 0}
.pnv nav{display:flex;gap:30px;margin-left:auto;font:600 .88rem/1 var(--fb)}.pnv nav a{opacity:.82;position:relative;padding:6px 0}.pnv nav a:after{content:"";position:absolute;left:0;bottom:0;height:1.5px;width:0;background:var(--ac);transition:width .3s}.pnv nav a:hover{opacity:1}.pnv nav a:hover:after{width:100%}
.pnv .bgr{display:none;margin-left:auto;color:#fff}.pnv .nv-cta{min-height:44px;padding:0 22px;font-size:.88rem}.pnv.sc{position:fixed;background:color-mix(in srgb,var(--dk) 82%,transparent);backdrop-filter:blur(16px) saturate(1.3)}.pnv.sc .in{padding:13px 0}
.pnv-edit{color:var(--ink);position:sticky}.pnv-edit .bgr{color:var(--ink)}.pnv-edit.sc{background:color-mix(in srgb,var(--bg) 86%,transparent)}.pnv-edit nav{margin-left:auto}
.pnv-neon{top:16px;position:fixed;left:0;right:0;padding:0 16px}.pnv-neon .in{width:min(960px,100%);padding:10px 12px 10px 24px;border-radius:99px;background:#ffffff12;border:1px solid #ffffff26;backdrop-filter:blur(16px)}.pnv-neon.sc{background:transparent;backdrop-filter:none}.pnv-neon.sc .in{background:color-mix(in srgb,var(--dk) 78%,transparent)}
.pnv-lux nav{letter-spacing:.16em;text-transform:uppercase;font-size:.72rem}.pnv-lux .nv-cta{border-radius:0!important;background:transparent;color:var(--ac);border:1px solid var(--ac);box-shadow:none;letter-spacing:.16em;text-transform:uppercase;font-size:.72rem}
@media(max-width:900px){.pnv nav,.pnv .nv-cta{display:none}.pnv .bgr{display:flex}}"""


def nav(X):
    k = X.r['dir']
    from .navs import NAVCSS as _NB
    X.css('nav.base', _NB['base'])
    X.css('pn', NAVCSS)
    burger = '<label class="bgr" for="mn" aria-label="Menü">' + ic('mn', 22) + '</label>'
    cta = f'<a class="btn nv-cta" href="#randevu">{X.r.get("cta", "Teklif alın")}</a>'
    return ed('Menü', f'<header class="pnv pnv-{k}" id="top"><div class="in">{logo(X)}<nav>{links_html(X)}</nav>{cta}{burger}</div></header>')


# ------------------------------------------------------------------ ANA GÖRSEL
HBASE = """.hrp{position:relative;overflow:hidden}.hrp .cta{display:flex;flex-wrap:wrap;gap:12px}.hrp em{font-style:var(--emi,normal)}.hrp .lead{margin:22px 0 34px;max-width:46ch}
.hrp .ph{animation:kb 26s ease-in-out infinite alternate}@keyframes kb{from{transform:scale(1.04)}to{transform:scale(1.14) translate(-1.2%,1%)}}
.hrp .cnt{font-variant-numeric:tabular-nums}.hrp .glass{background:#ffffff14;border:1px solid #ffffff2e;backdrop-filter:blur(18px)}
.mqb{overflow:hidden;white-space:nowrap}.mqb .mqt{display:inline-flex;gap:0;animation:mq 38s linear infinite}.mqb span{padding:0 28px}@keyframes mq{to{transform:translateX(-50%)}}
@media(max-width:640px){.hrp .cta .btn{flex:1 1 100%}}@media(prefers-reduced-motion:reduce){.hrp .ph,.mqb .mqt{animation:none}}"""


def _mq(X):
    w = [X.c['label'].upper(), 'RANDEVU İLE HİZMET', 'ŞEFFAF FİYAT', 'YAZILI GARANTİ', 'ÜCRETSİZ KEŞİF', X.city.upper() + ' VE ÇEVRESİ']
    s = ''.join(f'<span>{t}</span><span>✦</span>' for t in w)
    return f'<div class="mqb" aria-hidden="true"><div class="mqt">{s}{s}</div></div>'


def hero_cine(X):
    X.css('hr.base', HBASE)
    X.css('hr.cine', """.hc{color:#fff;--hc:#fff;min-height:min(100svh,880px);display:flex;flex-direction:column;background:var(--dk)}.hc .bgp{position:absolute;inset:0}.hc .bgp .ph{position:absolute;inset:0;filter:brightness(.6) saturate(1.1)}
.hc .bgp:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,color-mix(in srgb,var(--dk) 92%,transparent) 0,color-mix(in srgb,var(--dk) 40%,transparent) 58%,transparent),linear-gradient(0deg,var(--dk) 0,transparent 38%)}
.hc .g{position:relative;flex:1;display:grid;grid-template-columns:1.2fr .8fr;gap:40px;align-items:center;padding:150px 0 70px}.hc h1{font-size:clamp(2.7rem,7.2vw,6.6rem);line-height:.95;letter-spacing:-.04em;color:#fff;margin-top:20px}
.hc h1 em{color:transparent;-webkit-text-stroke:2px #fff}.hc .eyebrow{color:#fff}.hc .lead{color:#ffffffcc}.hc .btn.o{color:#fff;border-color:#ffffff66}
.hc .pcd{padding:28px;border-radius:26px;max-width:340px;justify-self:end;width:100%}.hc .pcd small{opacity:.7;font:600 .72rem/1 var(--fb);letter-spacing:.14em;text-transform:uppercase}.hc .pcd h3{color:#fff;font-size:1.6rem;margin:10px 0 16px}
.hc .pcd div{display:flex;justify-content:space-between;padding:12px 0;border-top:1px solid #ffffff26;font-size:.92rem}.hc .pcd i{font-style:normal;color:var(--ac);font-weight:700}
.hc .mqb{position:relative;border-top:1px solid #ffffff26;padding:20px 0;font:700 clamp(1.1rem,2.4vw,1.9rem)/1 var(--fd);opacity:.55;letter-spacing:-.01em}
@media(max-width:900px){.hc .g{grid-template-columns:1fr;padding:120px 0 40px}.hc .pcd{justify-self:stretch;max-width:none}}""")
    card = ('<aside class="pcd glass rv rv2"><small>Hizmet güvencesi</small><h3>Randevu ile yerinde hizmet</h3><div><span>Keşif</span><i>Ücretsiz</i></div>'
            '<div><span>Fiyat</span><i>Yazılı</i></div><div><span>Yapılan iş</span><i>Garantili</i></div></aside>')
    return (f'<section class="hr hrp hc" id="top2"><div class="bgp">{X.ph(_imv(X), "center 40%")}</div><div class="w g"><div class="rv"><span class="eyebrow">{X.c["label"]} · {X.city}</span><h1>{_h1(X)}</h1>'
            f'<p class="lead">{X.h[1]}</p>{_btns(X)}</div>{card}</div>{_mq(X)}</section>')


def hero_edit(X):
    X.css('hr.base', HBASE)
    X.css('hr.edit', """.he{padding:clamp(24px,4vw,56px) 0 0}.he .g{display:grid;grid-template-columns:1.1fr .9fr;gap:clamp(30px,5vw,80px);align-items:center;padding-bottom:clamp(40px,6vw,80px)}
.he h1{font-size:clamp(2.6rem,6.6vw,6rem);line-height:.98;letter-spacing:-.035em;font-weight:var(--hw,400);margin-top:20px}.he h1 em{color:var(--ac)}
.he .vis{position:relative;height:clamp(380px,46vw,600px)}.he .vis .a{position:absolute;right:0;top:0;width:76%;height:88%;border-radius:999px 999px 24px 24px;box-shadow:0 44px 90px -30px #0006}.he .vis .b{position:absolute;left:0;bottom:0;width:44%;height:46%;border-radius:22px;border:8px solid var(--bg);box-shadow:0 30px 60px -20px #0005;transform:rotate(-4deg);z-index:2}
.he .vis .st{position:absolute;right:-6px;bottom:16px;background:var(--ac);color:var(--on-ac);padding:18px 22px;border-radius:20px;transform:rotate(3deg);z-index:3;font:600 2.2rem/1 var(--fd)}.he .vis .st small{display:block;font:600 .68rem/1 var(--fb);letter-spacing:.1em;text-transform:uppercase;margin-top:6px}
.he .vis .ph{width:100%;height:100%}.he .stt{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--ln)}.he .stt div{padding:22px 0 26px;border-right:1px solid var(--ln);padding-left:clamp(14px,2.4vw,32px)}.he .stt div:first-child{padding-left:0}.he .stt div:last-child{border:0}
.he .stt b{display:block;font:500 clamp(1.6rem,3vw,2.4rem)/1 var(--fd)}.he .stt small{color:var(--mut);font-size:.8rem;letter-spacing:.04em}
@media(max-width:900px){.he .g{grid-template-columns:1fr}.he .vis{height:420px;order:-1}.he .stt{grid-template-columns:1fr 1fr}.he .stt div:nth-child(2){border:0}}""")
    st = ''.join(f'<div>{_cnt(a, b, d)}<small>{t}</small></div>' for a, b, d, t in STATS)
    return (f'<section class="hr hrp he" id="top2"><div class="w"><div class="g"><div class="rv"><span class="eyebrow">{X.c["label"]} · {X.city}</span><h1>{_h1(X)}</h1><p class="lead">{X.h[1]}</p>{_btns(X)}</div>'
            f'<div class="vis rv rv2"><div class="a">{X.ph(_imv(X), "center")}</div><div class="b">{X.ph("im2", "center")}</div><div class="st">Yerinde<small>Keşif ve hizmet</small></div></div></div><div class="stt">{st}</div></div></section>')


def hero_neon(X):
    X.css('hr.base', HBASE)
    X.css('hr.neon', """.hn{color:#fff;--hc:#fff;background:var(--dk);padding:150px 0 70px}.hn .blob{position:absolute;border-radius:50%;filter:blur(90px);opacity:.55;animation:bl 16s ease-in-out infinite alternate}
.hn .b1{width:520px;height:420px;left:-80px;top:-60px;background:var(--ac)}.hn .b2{width:460px;height:380px;right:-60px;top:80px;background:color-mix(in srgb,var(--ac) 40%,#19e6c8)}.hn .b3{width:420px;height:300px;left:40%;bottom:-120px;background:#7c4dff;opacity:.35}@keyframes bl{to{transform:translate(40px,-30px) scale(1.12)}}
.hn .tx{position:relative;text-align:center;max-width:900px;margin:0 auto}.hn h1{font-size:clamp(2.4rem,6vw,5.2rem);line-height:1.04;letter-spacing:-.04em;color:#fff}.hn h1 em{background:linear-gradient(90deg,#fff,var(--ac));-webkit-background-clip:text;background-clip:text;color:transparent}
.hn .lead{margin:22px auto 32px;color:#ffffffb8}.hn .cta{justify-content:center}.hn .btn.o{color:#fff;border-color:#ffffff40}.hn .eyebrow{color:#ffffffcc}
.hn .bn{position:relative;display:grid;grid-template-columns:1.3fr .7fr .7fr;grid-template-rows:auto auto;gap:14px;margin-top:64px}.hn .bn>div{border-radius:26px;padding:24px;position:relative;overflow:hidden;--mx:50%;--my:50%}.hn .bn>div:after{content:"";position:absolute;inset:0;background:radial-gradient(260px circle at var(--mx) var(--my),#ffffff22,transparent 60%);opacity:0;transition:.3s;pointer-events:none}.hn .bn>div:hover:after{opacity:1}
.hn .bn .pic{grid-row:span 2;min-height:300px;padding:0}.hn .bn .pic .ph{position:absolute;inset:0}.hn .bn .pic span{position:absolute;left:22px;bottom:20px;font:700 1.1rem/1.2 var(--fd);z-index:2;text-shadow:0 2px 14px #000a}.hn .bn .pic:before{content:"";position:absolute;inset:0;z-index:1;background:linear-gradient(0deg,#000a,transparent 55%)}
.hn .bn small{color:#ffffffa6;font-size:.82rem}.hn .bn strong{display:block;font:700 2.4rem/1.1 var(--fd);margin-top:6px;letter-spacing:-.03em}.hn .bars{grid-column:span 2;display:flex;align-items:flex-end;gap:10px;min-height:130px}.hn .bars i{flex:1;border-radius:8px;background:linear-gradient(0deg,var(--ac),#19e6c8);transform-origin:bottom;animation:grow 1.4s cubic-bezier(.2,.7,.2,1) both}
@keyframes grow{from{transform:scaleY(.1)}}@media(max-width:900px){.hn{padding-top:120px}.hn .bn{grid-template-columns:1fr 1fr}.hn .bn .pic{grid-column:span 2;grid-row:auto;min-height:220px}.hn .bars{grid-column:span 2}}""")
    bars = ''.join(f'<i style="height:{h}%;animation-delay:{i * .08:.2f}s"></i>' for i, h in enumerate((38, 52, 46, 68, 60, 82, 76, 100)))
    return (f'<section class="hr hrp hn" id="top2"><i class="blob b1"></i><i class="blob b2"></i><i class="blob b3"></i><div class="w"><div class="tx rv"><span class="eyebrow">{X.c["label"]} · {X.city}</span><h1 style="margin-top:20px">{_h1(X)}</h1><p class="lead">{X.h[1]}</p>{_btns(X)}</div>'
            f'<div class="bn rv rv2"><div class="pic glass">{X.ph(_imv(X), "center")}<span>{X.c["tag"]}</span></div><div class="glass"><small>Hizmet güvencesi</small><strong>Yazılı fiyat</strong></div><div class="glass"><small>Keşif</small><strong>Ücretsiz</strong></div>'
            f'<div class="glass bars" aria-label="Aylık performans">{bars}</div></div></div></section>')


def hero_lux(X):
    X.css('hr.base', HBASE)
    X.css('hr.lux', """.hl{background:var(--dk);color:#efe7d6;--hc:#efe7d6;min-height:min(100svh,860px);display:flex;align-items:center}.hl .im{overflow:hidden;position:absolute;right:0;top:0;bottom:0;width:min(52%,720px)}.hl .im .ph{position:absolute;inset:0;filter:grayscale(.45) contrast(1.1) brightness(.72)}
.hl .im:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,var(--dk),transparent 65%)}.hl .g{position:relative;padding:140px 0 90px}.hl .k{font:600 .72rem/1 var(--fb);letter-spacing:.3em;text-transform:uppercase;color:var(--ac)}
.hl h1{font-weight:300;font-size:clamp(2.6rem,6.4vw,5.8rem);line-height:1.02;letter-spacing:-.02em;color:#efe7d6;max-width:12ch;margin-top:22px}.hl h1 em{color:var(--ac)}.hl .ln{width:0;height:1px;background:var(--ac);margin:34px 0 0;animation:ln 1.2s .5s ease forwards}@keyframes ln{to{width:96px}}
.hl .lead{color:#b9b09c}.hl .btn{border-radius:0;letter-spacing:.16em;text-transform:uppercase;font-size:.74rem}.hl .btn.o{color:var(--ac);border-color:var(--ac)}.hl .vt{position:absolute;right:28px;top:50%;transform:rotate(90deg);transform-origin:right top;font:600 .66rem/1 var(--fb);letter-spacing:.4em;text-transform:uppercase;color:var(--ac);z-index:2}
@media(max-width:900px){.hl .im{width:100%;opacity:.35}.hl .im:after{background:linear-gradient(0deg,var(--dk),transparent)}.hl .vt{display:none}}""")
    return (f'<section class="hr hrp hl" id="top2"><div class="im">{X.ph(_imv(X), "center")}</div><div class="w g"><div class="rv"><div class="k">{X.c["label"]} · {X.city} · Randevu ile yerinde hizmet</div><h1>{_h1(X)}</h1><div class="ln"></div>'
            f'<p class="lead" style="margin-top:26px">{X.h[1]}</p>{_btns(X)}</div></div><div class="vt">Kaydırın ↓</div></section>')


HERO = {'cine': hero_cine, 'edit': hero_edit, 'neon': hero_neon, 'lux': hero_lux}


# ------------------------------------------------------------------ BÖLÜMLER
def stats(X):
    X.css('pm.stats', """.pst{padding:clamp(44px,6vw,80px) 0}.pst .g{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-block:1px solid var(--ln)}.pst .g div{padding:34px 24px;border-right:1px solid var(--ln)}.pst .g div:last-child{border:0}
.pst b{display:block;font:var(--hw,700) clamp(2rem,4.2vw,3.4rem)/1 var(--fd);letter-spacing:-.03em;color:var(--ac);font-variant-numeric:tabular-nums}.pst small{display:block;margin-top:10px;color:var(--mut)}@media(max-width:800px){.pst .g{grid-template-columns:1fr 1fr}.pst .g div:nth-child(2){border-right:0}.pst .g div:nth-child(-n+2){border-bottom:1px solid var(--ln)}}""")
    s = ''.join(f'<div>{_cnt(a, b, d)}<small>{t}</small></div>' for a, b, d, t in STATS)
    return f'<section class="pst"><div class="w"><div class="g">{s}</div></div></section>'


def marquee(X):
    X.css('pm.mq', """.pmq{padding:26px 0;border-block:1px solid var(--ln);font:var(--hw,700) clamp(1.4rem,3.4vw,2.6rem)/1 var(--fd);letter-spacing:-.02em;color:var(--ink)}.pmq .mqb span:nth-child(even){color:var(--ac)}""")
    X.css('hr.base', HBASE)
    return f'<section class="pmq">{_mq(X)}</section>'


def quote_cta(X):
    X.css('pm.qc', """.pqc{padding:clamp(56px,8vw,110px) 0}.pqc .bx{border-radius:calc(var(--r)*2);padding:clamp(34px,6vw,80px);background:var(--dk);color:#fff;position:relative;overflow:hidden;display:grid;grid-template-columns:1.3fr .7fr;gap:30px;align-items:center}
.pqc .bx:before{content:"";position:absolute;right:-120px;top:-120px;width:420px;height:420px;border-radius:50%;background:var(--ac);opacity:.35;filter:blur(70px)}.pqc h2{color:#fff;font-size:clamp(1.9rem,4vw,3.4rem);position:relative}.pqc p{color:#ffffffbb;margin-top:14px;position:relative}.pqc .cta{display:flex;gap:12px;flex-wrap:wrap;justify-content:flex-end;position:relative}.pqc .btn.o{color:#fff;border-color:#ffffff55}
@media(max-width:800px){.pqc .bx{grid-template-columns:1fr}.pqc .cta{justify-content:flex-start}}""")
    return (f'<section class="pqc" id="teklif"><div class="w"><div class="bx"><div><h2>Projeniz için ücretsiz keşif ve yazılı teklif alın</h2><p>Sahada ölçüm yapar, kalem kalem teklifi yazılı olarak bırakırız. Onayınız olmadan işlem başlamaz.</p></div>'
            f'<div class="cta"><a class="btn" href="#randevu">Teklif alın {ic("ar", 18)}</a><a class="btn o" href="tel:+{TELRAW}">{ic("tel", 18)} {TEL}</a></div></div></div></section>')


# ------------------------------------------------------------------ HAREKET KATMANI
MOTION_CSS = """html.pmj .pmr{opacity:0;transform:translateY(28px);transition:opacity .8s cubic-bezier(.2,.7,.2,1),transform .8s cubic-bezier(.2,.7,.2,1);transition-delay:var(--d,0s)}html.pmj .pmr.pmi{opacity:1;transform:none}
.pgb{position:fixed;left:0;top:0;height:3px;width:100%;transform:scaleX(0);transform-origin:left;background:var(--ac);z-index:99;pointer-events:none}
.pm .btn{position:relative;overflow:hidden;transition:transform .25s,box-shadow .25s,background .25s}.pm .btn:not(.o):after{content:"";position:absolute;top:0;bottom:0;width:40%;left:-60%;background:linear-gradient(100deg,transparent,#ffffff55,transparent);transform:skewX(-20deg);animation:shn 4.5s ease-in-out infinite}@keyframes shn{0%,60%{left:-60%}100%{left:130%}}
.hrp .ph{translate:0 var(--py,0px)}.he .vis .b{animation:fl 7s ease-in-out infinite}.he .vis .st{animation:fl 5s ease-in-out -2s infinite}.hc .pcd{animation:fl 8s ease-in-out infinite}.hn .bn .glass{animation:fl 9s ease-in-out infinite}.hn .bn .glass:nth-child(2){animation-delay:-3s}.hn .bn .glass:nth-child(3){animation-delay:-6s}
@keyframes fl{50%{translate:0 -10px}}.pm .ed section h2{background:linear-gradient(currentColor,currentColor) 0 100%/0 2px no-repeat;transition:background-size 1s .3s}.pm .ed .pmi h2,.pm .ed h2.pmi{background-size:60px 2px;padding-bottom:10px}.pm .btn:hover{transform:translateY(-3px)}.pm .btn:active{transform:translateY(0) scale(.98)}
.pm a:focus-visible,.pm button:focus-visible,.pm input:focus-visible,.pm select:focus-visible{outline:2px solid var(--ac);outline-offset:3px}
.pm .ed:not(:first-child) article,.pm .ed:not(:first-child) li{transition:transform .35s cubic-bezier(.2,.7,.2,1),box-shadow .35s}.pm .ed:not(:first-child) article:hover{transform:translateY(-5px);box-shadow:0 26px 50px -26px #0006}
.pm .ed:not(:first-child) .ph{transition:transform .8s cubic-bezier(.2,.7,.2,1)}.pm .ed:not(:first-child):hover .ph{transform:scale(1.03)}
@media(prefers-reduced-motion:reduce){.pm .btn:after,.hrp *{animation:none!important}html.pmj .pmr{opacity:1;transform:none;transition:none}.pm *{scroll-behavior:auto!important}}"""

MOTION_JS = r"""(function(){var d=document.documentElement,rm=matchMedia('(prefers-reduced-motion:reduce)').matches,ifr=false;try{ifr=window.top!==window}catch(e){ifr=true}
var h=document.querySelector('.pnv');function pnap(){if(!h)return;var a=document.querySelector('.ann'),t=a&&a.offsetParent!==null?a.offsetHeight:0,nf=h.classList.contains('pnv-neon');h.style.top=(h.classList.contains('sc')&&!nf)?'':((nf?16:0)+(scrollY<t?t-scrollY:0)*(nf?1:(h.classList.contains('sc')?0:1)))+'px'}document.addEventListener('click',function(){setTimeout(pnap,60)});addEventListener('resize',pnap);function sc(){var y=scrollY;var hr=document.querySelector('.hrp');if(hr&&y<1200&&!rm)hr.style.setProperty('--py',(y*.12)+'px');if(h)h.classList.toggle('sc',y>40);pnap();var b=document.querySelector('.pgb');if(b){var m=document.documentElement.scrollHeight-innerHeight;b.style.transform='scaleX('+(m>0?y/m:0)+')'}}
var pb=document.createElement('i');pb.className='pgb';document.body.appendChild(pb);addEventListener('scroll',sc,{passive:true});sc();
function cnt(e){var t=parseFloat(e.dataset.to),f=parseInt(e.dataset.d||0),s=e.dataset.sf||'',t0=performance.now(),D=1400;function fm(v){var x=f?v.toFixed(f).replace('.',','):Math.round(v).toLocaleString('tr-TR');return x+s}
function st(n){var p=Math.min(1,(n-t0)/D),v=t*(1-Math.pow(1-p,3));e.textContent=fm(v);if(p<1)requestAnimationFrame(st)}requestAnimationFrame(st)}
var cs=[].slice.call(document.querySelectorAll('.cnt'));
if(!rm&&!ifr){var h1=document.querySelector('.hrp h1');if(h1&&!h1.querySelector('*:not(em)')){var n=0;(function w(nd){[].slice.call(nd.childNodes).forEach(function(c){if(c.nodeType===3){var f=document.createDocumentFragment();c.textContent.split(/(\s+)/).forEach(function(t){if(!t)return;if(/^\s+$/.test(t)){f.appendChild(document.createTextNode(t))}else{var s=document.createElement('span');s.className='wd';s.style.setProperty('--i',n++);s.textContent=t;f.appendChild(s)}});nd.replaceChild(f,c)}else if(c.nodeType===1)w(c)})})(h1);d.classList.add('pmw')}
var px=[].slice.call(document.querySelectorAll('.hc .bgp,.hl .im,.he .vis .a'));if(px.length){addEventListener('scroll',function(){var y=scrollY;if(y<1200)px.forEach(function(e){e.style.transform='translate3d(0,'+(y*.12)+'px,0)'})},{passive:true})}
[].slice.call(document.querySelectorAll('.hrp .btn')).forEach(function(b){b.addEventListener('pointermove',function(ev){var r=b.getBoundingClientRect();b.style.translate=((ev.clientX-r.left-r.width/2)*.12)+'px '+((ev.clientY-r.top-r.height/2)*.2)+'px'});b.addEventListener('pointerleave',function(){b.style.translate=''})})}
if(rm||!('IntersectionObserver' in window)){return}
var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){x.target.classList.add('pmi');io.unobserve(x.target)}})},{threshold:.12,rootMargin:'0px 0px -6% 0px'});
var co=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){cnt(x.target);co.unobserve(x.target)}})},{threshold:.6});cs.forEach(function(e){co.observe(e)});
if(ifr)return;d.classList.add('pmj');
[].slice.call(document.querySelectorAll('.ed:not(:first-child):not([data-nm="Alt bilgi"]):not([data-nm="Mobil bar"]) section .w > *, .ed:not(:first-child) section > .w > * > *')).forEach(function(e,i){if(e.closest('.hrp'))return;e.classList.add('pmr');e.style.setProperty('--d',((i%4)*.08)+'s');io.observe(e)});
[].slice.call(document.querySelectorAll('.hn .bn>div')).forEach(function(e){e.addEventListener('pointermove',function(ev){var r=e.getBoundingClientRect();e.style.setProperty('--mx',(ev.clientX-r.left)+'px');e.style.setProperty('--my',(ev.clientY-r.top)+'px')})});
setTimeout(function(){[].slice.call(document.querySelectorAll('.pmr:not(.pmi)')).forEach(function(e){var r=e.getBoundingClientRect();if(r.top<innerHeight&&r.bottom>0)e.classList.add('pmi')})},1800)})();"""
