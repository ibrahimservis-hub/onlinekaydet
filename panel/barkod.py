# -*- coding: utf-8 -*-
"""Code 128 barkod üretici: dışarıdan kütüphane istemeden, yazdırmaya uygun SVG.

Pazaryeri siparişlerinde kargo barkodu fişin üzerinde okunabilir olmalı; depodaki
el terminali ekrandan değil kâğıttan okur. Bu yüzden barkodu resim olarak değil,
baskıda keskin çıkan SVG çubuk olarak çiziyoruz.

Kodlama: yalnız rakamdan oluşan ve çift haneli metinler C kümesiyle (iki hane bir
simge) daha dar basılır; diğerleri B kümesiyle. Sağlama (checksum) Code 128
kuralına göre hesaplanır, aksi hâlde okuyucu barkodu reddeder.
"""

# 0-102 simge, 103-105 başlangıç, 106 dur. Her desen: çubuk/boşluk genişlikleri.
P = ("212222 222122 222221 121223 121322 131222 122213 122312 132212 221213 "
     "221312 231212 112232 122132 122231 113222 123122 123221 223211 221132 "
     "221231 213212 223112 312131 311222 321122 321221 312212 322112 322211 "
     "212123 212321 232121 111323 131123 131321 112313 132113 132311 211313 "
     "231113 231311 112133 112331 132131 113123 113321 133121 313121 211331 "
     "231131 213113 213311 213131 311123 311321 331121 312113 312311 332111 "
     "314111 221411 431111 111224 111422 121124 121421 141122 141221 112214 "
     "112412 122114 122411 142112 142211 241211 221114 413111 241112 134111 "
     "111242 121142 121241 114212 124112 124211 411212 421112 421211 212141 "
     "214121 412121 111143 111341 131141 114113 114311 411113 411311 113141 "
     "114131 311141 411131 211412 211214 211232 2331112").split()
START_B, START_C, STOP = 104, 105, 106


def values(text):
    """Metni Code 128 simge değerlerine çevir (başlangıç ve sağlama dâhil)."""
    t = "".join(ch for ch in str(text or "") if 32 <= ord(ch) <= 126)
    if not t:
        return []
    if t.isdigit() and len(t) % 2 == 0 and len(t) >= 4:
        vals = [START_C] + [int(t[i:i + 2]) for i in range(0, len(t), 2)]
    else:
        vals = [START_B] + [ord(ch) - 32 for ch in t]
    chk = vals[0]
    for i, v in enumerate(vals[1:], start=1):
        chk += i * v
    return vals + [chk % 103, STOP]


def svg(text, height=44, module=1.7, label=True, pad=4):
    """Barkodu SVG olarak çiz. module: en ince çubuğun genişliği (px)."""
    vals = values(text)
    if not vals:
        return ""
    bars, x = [], pad
    for v in vals:
        bar = True
        for w in P[v]:
            w = int(w) * module
            if bar:
                bars.append('<rect x="%.2f" y="0" width="%.2f" height="%d"/>' % (x, w, height))
            x += w
            bar = not bar
    w_all = x + pad
    h_all = height + (14 if label else 0)
    txt = ('<text x="%.2f" y="%d" text-anchor="middle" font-family="ui-monospace,Menlo,monospace" '
           'font-size="11" letter-spacing="1.5">%s</text>' % (w_all / 2, height + 11, _e(text))) if label else ""
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%.0f" height="%d" viewBox="0 0 %.2f %d" '
            'role="img" aria-label="%s"><rect width="100%%" height="100%%" fill="#fff"/>'
            '<g fill="#000">%s</g>%s</svg>'
            % (w_all, h_all, w_all, h_all, _e(text), "".join(bars), txt))


def _e(v):
    return str(v or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
