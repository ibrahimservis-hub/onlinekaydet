"""Ortak temel: yazı tipleri, ikonlar, çekirdek CSS ve görünüm (skin) kuralları."""
import base64, os
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'fonts')
IMG = os.path.join(HERE, '..', 'img')

# anahtar -> (CSS ailesi, ağırlık aralığı, stil, yedek)
FAM = {
    'fraunces': ('Fraunces', '100 900', 'normal', 'Georgia,serif'),
    'playfair': ('Playfair Display', '400 900', 'normal', 'Georgia,serif'),
    'playfair-i': ('Playfair Display', '400 900', 'italic', 'Georgia,serif'),
    'newsreader': ('Newsreader', '200 800', 'normal', 'Georgia,serif'),
    'newsreader-i': ('Newsreader', '200 800', 'italic', 'Georgia,serif'),
    'bricolage': ('Bricolage Grotesque', '200 800', 'normal', 'system-ui,sans-serif'),
    'spacegrotesk': ('Space Grotesk', '300 700', 'normal', 'system-ui,sans-serif'),
    'sora': ('Sora', '100 800', 'normal', 'system-ui,sans-serif'),
    'outfit': ('Outfit', '100 900', 'normal', 'system-ui,sans-serif'),
    'manrope': ('Manrope', '200 800', 'normal', 'system-ui,sans-serif'),
    'figtree': ('Figtree', '300 900', 'normal', 'system-ui,sans-serif'),
    'instrument': ('Instrument Sans', '400 700', 'normal', 'system-ui,sans-serif'),
    'plex': ('IBM Plex Sans', '100 700', 'normal', 'system-ui,sans-serif'),
    'jbmono': ('JetBrains Mono', '100 800', 'normal', 'ui-monospace,monospace'),
    'intertight': ('Inter Tight', '100 900', 'normal', 'system-ui,sans-serif'),
    'dmserif': ('DM Serif Display', '400', 'normal', 'Georgia,serif'),
    'archivoblack': ('Archivo Black', '400', 'normal', 'Impact,sans-serif'),
    'barlow': ('Barlow Condensed', '700', 'normal', 'Arial Narrow,sans-serif'),
    'syne': ('Syne', '700', 'normal', 'system-ui,sans-serif'),
    'plexmono': ('IBM Plex Mono', '500', 'normal', 'ui-monospace,monospace'),
}
RANGE = {'latin': 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD',
         'latin-ext': 'U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF'}
_cache = {}


def face(key):
    """@font-face (latin + latin-ext, gömülü). Aile adı: 'F-<key>'."""
    if key in _cache:
        return _cache[key]
    fam, wt, st, _ = FAM[key]
    out = ''
    for sub in ('latin-ext', 'latin'):
        b = base64.b64encode(open(os.path.join(FONTS, f'{key}-{sub}.woff2'), 'rb').read()).decode()
        out += f"@font-face{{font-family:'F-{key}';font-style:{st};font-weight:{wt};font-display:swap;src:url(data:font/woff2;base64,{b}) format('woff2');unicode-range:{RANGE[sub]}}}"
    _cache[key] = out
    return out


def stack(key):
    return f"'F-{key}',{FAM[key][3]}"


def img64(name):
    return base64.b64encode(open(os.path.join(IMG, name + '.jpg'), 'rb').read()).decode()


# ---------------------------------------------------------------- ikonlar (çizgi, 24px, 1.75)
P = {
    'tel': '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
    'wa': '<path d="M4 20l1.3-4A8 8 0 1 1 8 18.7z"/><path d="M9 9.5c.3 2 2 3.800 4.500 4.500l1-1.200-1.800-.9-.7.700c-.8-.4-1.500-1.100-1.900-1.900l.7-.7-.9-1.800z"/>',
    'ok': '<path d="M5 12.500l4.500 4.500L19 7.500"/>',
    'cl': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'sh': '<path d="M12 3l8 3v6c0 5-3.500 8-8 9-4.500-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    'pin': '<path d="M12 21s7-6 7-11a7 7 0 0 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.500"/>',
    'st': '<path d="M12 3l2.700 5.600 6.100.9-4.400 4.300 1 6.100L12 17l-5.400 2.900 1-6.100L3.200 9.500l6.100-.9z"/>',
    'ar': '<path d="M5 12h14M13 6l6 6-6 6"/>',
    'al': '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    'pl': '<path d="M12 5v14M5 12h14"/>',
    'mn': '<path d="M4 7h16M4 12h16M4 17h16"/>',
    'x': '<path d="M6 6l12 12M18 6L6 18"/>',
    'cal': '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
    'se': '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.500-4.500"/>',
    'wr': '<path d="M14.500 6.500a4 4 0 0 0 5 5L10 21a2 2 0 0 1-3-3l9.500-9.500z" transform="rotate(0)"/><path d="M14 3l3 3"/>',
    'fl': '<path d="M12 3c1 3 5 5 5 10a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-6 1-9z"/>',
    'sn': '<path d="M12 3v18M4.500 7.500l15 9M19.500 7.500l-15 9M9 4.500l3 2 3-2M9 19.500l3-2 3 2"/>',
    'wm': '<rect x="4" y="3" width="16" height="18" rx="2"/><circle cx="12" cy="13" r="4.500"/><path d="M7.500 6.500h.01M10.500 6.500h3"/>',
    'tv': '<rect x="3" y="5" width="18" height="12" rx="2"/><path d="M8 21h8M12 17v4"/>',
    'lp': '<rect x="5" y="5" width="14" height="10" rx="1.500"/><path d="M3 19h18"/>',
    'dr': '<path d="M12 3s6 6.500 6 11a6 6 0 0 1-12 0c0-4.500 6-11 6-11z"/>',
    'bo': '<path d="M13 3L5 13h6l-1 8 8-10h-6z"/>',
    'ca': '<path d="M4 8h10a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2z"/><path d="M16 11l5-3v9l-5-3"/>',
    'th': '<path d="M10 14V5a2 2 0 0 1 4 0v9a4 4 0 1 1-4 0z"/>',
    'bt': '<path d="M3 9a9 9 0 0 1 18 0M6 12a6 6 0 0 1 12 0M9.500 15a3 3 0 0 1 5 0"/><circle cx="12" cy="18" r=".8"/>',
    'cp': '<rect x="7" y="7" width="10" height="10" rx="1.500"/><path d="M10 3v3M14 3v3M10 18v3M14 18v3M3 10h3M3 14h3M18 10h3M18 14h3"/>',
    'dl': '<path d="M12 4v11M7 11l5 5 5-5M5 20h14"/>',
    'pr': '<path d="M7 8V4h10v4M6 17H4v-7h16v7h-2M7 14h10v6H7z"/>',
    'bx': '<path d="M3 7l9-4 9 4-9 4zM3 7v10l9 4 9-4V7M12 11v10"/>',
    'lk': '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    'sp': '<path d="M12 3l1.800 4.700L18.500 9.500l-4.700 1.800L12 16l-1.800-4.700L5.500 9.500l4.700-1.800zM18 15l.8 2.200 2.200.8-2.200.8L18 21l-.8-2.200-2.200-.8 2.200-.8z"/>',
    'dn': '<path d="M6 9l6 6 6-6"/>',
    'ex': '<path d="M12 8v5M12 16.500h.01"/><circle cx="12" cy="12" r="9"/>',
    'us': '<circle cx="12" cy="8" r="4"/><path d="M4 20c1-4 4-6 8-6s7 2 8 6"/>',
    'ph': '<rect x="7" y="2.500" width="10" height="19" rx="2.500"/><path d="M11 18.500h2"/>',
    'dc': '<path d="M7 3h7l4 4v14H7zM14 3v4h4M10 12h5M10 16h5"/>',
}


def ic(n, s=20, sw=1.75):
    return f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{P[n]}</svg>'


def lum(h):
    return 0.299 * int(h[1:3], 16) + 0.587 * int(h[3:5], 16) + 0.114 * int(h[5:7], 16)


def mix(a, b, k):
    """a rengini b ile karıştır (k = a payı)."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(x * k + y * (1 - k)) for x, y in zip(ca, cb))


# ---------------------------------------------------------------- çekirdek CSS
CORE = """*{box-sizing:border-box;margin:0;padding:0}html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
html{overflow-x:clip}body{font:400 16px/1.6 var(--fb);color:var(--ink);background:var(--bg);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;overflow-x:clip}
a{color:inherit;text-decoration:none}img{max-width:100%}button{font:inherit;color:inherit;cursor:pointer;background:none;border:0}
.hid{position:absolute;opacity:0;pointer-events:none;width:0;height:0}
input[type=checkbox].hid,input[type=checkbox][class*=t-],.hid{width:0!important;height:0!important;left:0;top:0;margin:0;padding:0}
.w{width:min(1200px,100% - 48px);margin-inline:auto}.w.n{width:min(980px,100% - 48px)}
h1,h2,h3,h4{font-family:var(--fd);color:var(--hc,var(--ink));font-weight:var(--hw,700);letter-spacing:var(--ht,-.02em);line-height:1.08;text-wrap:balance}
h1{font-size:clamp(2.2rem,5.4vw,4.4rem)}h2{font-size:clamp(1.7rem,3.4vw,2.7rem)}h3{font-size:1.2rem;line-height:1.25}
p{text-wrap:pretty}
.eyebrow{font:600 .74rem/1 var(--fb);letter-spacing:.16em;text-transform:uppercase;color:var(--ac);display:inline-flex;align-items:center;gap:10px}
.eyebrow:before{content:"";width:22px;height:1.5px;background:currentColor}
.mut{color:var(--mut)}.lead{font-size:clamp(1rem,1.5vw,1.2rem);color:var(--mut);max-width:34em}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:9px;min-height:50px;padding:0 26px;font:700 .95rem/1 var(--fb);letter-spacing:.005em;background:var(--ac);color:var(--on-ac);border-radius:var(--r);border:1.5px solid var(--ac);transition:transform .18s,box-shadow .18s,background .18s,color .18s;white-space:nowrap}
.btn:hover{transform:translateY(-2px)}.btn:active{transform:none}
.btn.o{background:transparent;color:inherit;border-color:currentColor}.btn.d{background:var(--dk);border-color:var(--dk);color:#fff}.btn.l{background:#fff;border-color:#fff;color:var(--dk)}
.btn svg{flex:none}
.sec{padding:clamp(56px,8vw,112px) 0}.sec.alt{background:var(--sf)}.sec.dk{background:var(--dk);color:#fff;--hc:#fff;--mut:#ffffffb0;--ln:#ffffff26}
.sh{display:grid;gap:14px;margin-bottom:clamp(28px,4vw,52px)}.sh.c{text-align:center;justify-items:center}.sh p{color:var(--mut);max-width:40em}
.ph{position:relative;background:var(--bi) var(--p,center)/cover no-repeat var(--sf);overflow:hidden;filter:var(--phf,none)}
.ph:after{content:"";position:absolute;inset:0;background:var(--pho,transparent);mix-blend-mode:var(--phm,multiply);pointer-events:none}
.tag{display:inline-flex;align-items:center;gap:7px;padding:7px 13px;border:1px solid var(--ln);border-radius:99px;font:600 .8rem/1 var(--fb);background:var(--bg)}
.star{color:var(--ac)}
.pulse{width:9px;height:9px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 0 #22c55e88;animation:pl 2s infinite;display:inline-block}
@keyframes pl{70%{box-shadow:0 0 0 9px #22c55e00}100%{box-shadow:0 0 0 0 #22c55e00}}
@keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
.rv{animation:rise .7s cubic-bezier(.2,.7,.2,1) both}.rv2{animation-delay:.12s}.rv3{animation-delay:.24s}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}html{scroll-behavior:auto}}
:focus-visible{outline:2.5px solid var(--ac);outline-offset:3px}
/* üst şerit + menü çekmecesi */
.drw{position:fixed;inset:0;z-index:80;background:var(--dk);color:#fff;transform:translateX(102%);visibility:hidden;transition:transform .32s cubic-bezier(.2,.7,.2,1),visibility 0s .32s;overflow:auto;padding:20px 24px 120px;display:flex;flex-direction:column}
#mn:checked~.ed .drw{transform:none;visibility:visible;transition:transform .32s cubic-bezier(.2,.7,.2,1)}
.drw .dh{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}.drw .x{width:46px;height:46px;border:1.5px solid #ffffff44;border-radius:var(--r);display:grid;place-items:center;cursor:pointer}
.drw .dl a{display:flex;justify-content:space-between;align-items:center;padding:18px 2px;border-bottom:1px solid #ffffff1f;font:600 1.35rem/1.2 var(--fd)}
.drw .dl a small{font:500 .78rem/1 var(--fb);opacity:.5}
.drw .dc{display:grid;gap:10px;margin-top:26px}.drw .dn{margin-top:22px;font-size:.88rem;opacity:.7;line-height:1.9}
.drw.sheet{inset:0 0 0 auto;width:min(420px,92vw);box-shadow:-30px 0 80px #0006}
.bgr{display:none;width:46px;height:46px;border:1.5px solid var(--ln);border-radius:var(--r);place-items:center;cursor:pointer;margin-left:auto;color:inherit}
/* düzenleme kipi (panel) */
body.edit .ed{outline:2px dashed var(--ac);outline-offset:-2px;position:relative}
body.edit .ed:before{content:attr(data-nm) " · ✎ Düzenle";position:absolute;left:8px;top:8px;z-index:90;background:var(--ac);color:var(--on-ac);font:700 11px/1 sans-serif;padding:5px 9px;border-radius:20px}
/* formlar */
.fm{display:grid;gap:12px}.fm .g2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.fm label{display:grid;gap:6px;font:600 .78rem/1.2 var(--fb);letter-spacing:.03em;color:var(--mut)}
.fm input,.fm select,.fm textarea{width:100%;font:500 1rem/1.3 var(--fb);color:var(--ink);background:var(--fbg,#fff);border:1.5px solid var(--ln);border-radius:var(--fr,var(--r));padding:14px 15px;min-height:50px;transition:border-color .15s,box-shadow .15s;appearance:none;-webkit-appearance:none}
.fm select{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2.5'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 14px center;padding-right:38px}
.fm textarea{min-height:92px;resize:vertical}
.fm input:focus,.fm select:focus,.fm textarea:focus{outline:0;border-color:var(--ac);box-shadow:0 0 0 4px color-mix(in srgb,var(--ac) 18%,transparent)}
.fm .ok,.msg.ok{color:#0f8a4b}.msg{font:600 .92rem/1.4 var(--fb);min-height:1.4em}.msg.er{color:#c0341d}
.hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}
.chips{display:flex;flex-wrap:wrap;gap:8px}.chips button,.chips label{padding:10px 15px;border:1.5px solid var(--ln);border-radius:99px;font:600 .88rem/1 var(--fb);background:var(--bg);cursor:pointer;transition:.15s}
.chips button:hover{border-color:var(--ac)}.chips button.on{background:var(--ac);color:var(--on-ac);border-color:var(--ac)}
/* sık sorulanlar */
.faq details{border-bottom:1px solid var(--ln)}.faq summary{list-style:none;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:20px;padding:22px 0;font:600 1.08rem/1.3 var(--fd)}
.faq summary::-webkit-details-marker{display:none}.faq summary:after{content:"+";font:400 1.6rem/1 var(--fb);color:var(--ac);transition:transform .2s}.faq details[open] summary:after{transform:rotate(45deg)}
.faq details p{padding:0 0 22px;color:var(--mut);max-width:46em}
/* alt bilgi ortak */
.ft{background:var(--dk);color:#ffffffb8;font-size:.92rem}.ft b{color:#fff;display:block;margin-bottom:12px;font:700 .8rem/1 var(--fb);letter-spacing:.12em;text-transform:uppercase}
.ft a:hover{color:#fff}.ft .cp{border-top:1px solid #ffffff22;padding:20px 0;font-size:.82rem;opacity:.75}
@media(max-width:900px){.bgr{display:grid}.w{width:min(100% - 36px,1200px)}.fm .g2{grid-template-columns:1fr}}
"""

# ---------------------------------------------------------------- görünüm (skin) kuralları
BTN = {
    'solid': '',
    'pill': '.btn{border-radius:99px}',
    'sq': '.btn{border-radius:0;box-shadow:4px 4px 0 var(--ink)}.btn:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--ink)}.btn.o{box-shadow:none}.btn.l,.btn.d{box-shadow:4px 4px 0 var(--ac)}',
    'line': '.btn{border-radius:0;min-height:48px;letter-spacing:.08em;text-transform:uppercase;font-size:.8rem}',
    'soft': '.btn{border-radius:14px;box-shadow:0 10px 24px -10px color-mix(in srgb,var(--ac) 70%,transparent)}',
}
CARD = {
    'line': '.cd{border:1px solid var(--ln);border-radius:var(--r);background:var(--bg)}',
    'fill': '.cd{background:var(--sf);border-radius:var(--r)}',
    'lift': '.cd{background:#fff;border-radius:var(--r);box-shadow:0 1px 2px #0000000d,0 18px 40px -22px #0003}',
    'top': '.cd{border:1px solid var(--ln);border-top:3px solid var(--ac);border-radius:calc(var(--r)/2);background:var(--bg)}',
    'brut': '.cd{border:2px solid var(--ink);border-radius:var(--r);background:#fff;box-shadow:5px 5px 0 var(--ink)}',
    'dark': '.cd{background:#ffffff0d;border:1px solid #ffffff22;border-radius:var(--r);color:#fff}',
}
FIELD = {
    'box': '',
    'line': '.fm input,.fm select,.fm textarea{border:0;border-bottom:1.5px solid var(--ink);border-radius:0;background:transparent;padding-inline:2px}',
    'pill': '.fm input,.fm select{border-radius:99px;padding-inline:20px}.fm textarea{border-radius:22px}',
    'dark': '.fm input,.fm select,.fm textarea{background:#ffffff10;border-color:#ffffff30;color:#fff}.fm label{color:#ffffffa8}.fm select option{color:#111}',
}
HEAD = {
    'bold': '',
    'light': 'h1,h2,h3{--hw:400;--ht:-.03em}',
    'caps': 'h1,h2{text-transform:uppercase;--ht:.01em;--hw:800}h1{font-size:clamp(2rem,5vw,3.8rem)}',
    'tight': 'h1,h2,h3{--hw:800;--ht:-.045em}',
    'wide': 'h1,h2{--hw:600;--ht:.0em}',
}
