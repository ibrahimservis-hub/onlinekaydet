"""Saat teması (sıfırdan, kombi): src.html + gömülü yazı tipleri -> ../html/31-kombi-saat.html
Yazı tipleri: Antonio 700 ve Hanken Grotesk (OFL). Kaynak dosyalar fonts/ klasöründe."""
import base64, os
H = os.path.dirname(os.path.abspath(__file__))
def face(fam, fn, weight, rng):
    b = base64.b64encode(open(os.path.join(H, 'fonts', fn), 'rb').read()).decode()
    return f'@font-face{{font-family:"{fam}";src:url(data:font/woff2;base64,{b}) format("woff2");font-weight:{weight};font-display:swap;unicode-range:{rng}}}'
LAT = 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'
EXT = 'U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+1E00-1E9F,U+1EF2-1EFF,U+20A0-20AB,U+20AD-20C0,U+2C60-2C7F,U+A720-A7FF'
fonts = '\n'.join([
    face('Antonio', 'antonio-latin-ext-700-normal.woff2', 700, EXT), face('Antonio', 'antonio-latin-700-normal.woff2', 700, LAT),
    face('Hanken Grotesk', 'hanken-grotesk-latin-ext-wght-normal.woff2', '100 900', EXT), face('Hanken Grotesk', 'hanken-grotesk-latin-wght-normal.woff2', '100 900', LAT)])
src = open(os.path.join(H, 'src.html'), encoding='utf-8').read()
out = os.path.join(H, '..', 'html', '31-kombi-saat.html')
open(out, 'w', encoding='utf-8').write(src.replace('{{FONTS}}', fonts))
print(out, os.path.getsize(out))
