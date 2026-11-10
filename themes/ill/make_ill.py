#!/usr/bin/env python3
"""Yeni sektörler için özel çizim görseller (SVG -> JPG, 1600x1000). Fotoğraf değil, tutarlı bir düz-çizim dili.
Çalıştır: python3 make_ill.py  -> ../img/<anahtar>.jpg, <anahtar>2.jpg, <anahtar>3.jpg"""
import os, subprocess, random
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'img')
W, H = 1600, 1000

def svg(body, c1, c2, glow='#ffffff'):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>'
            f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>'
            f'<radialGradient id="gl" cx=".25" cy=".2" r=".8"><stop offset="0" stop-color="{glow}" stop-opacity=".28"/><stop offset="1" stop-color="{glow}" stop-opacity="0"/></radialGradient>'
            f'<filter id="sh" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="14"/></filter></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#gl)"/>{body}</svg>')

def shadow(cx, cy, rx, ry=26, o=.35):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#000" opacity="{o}" filter="url(#sh)"/>'

def floor(y, col, o=1):
    return f'<rect y="{y}" width="{W}" height="{H-y}" fill="{col}" opacity="{o}"/>'

def car(x, y, s, body, glass='#cfe6f2', dark='#16181d'):
    # yan görünüm otomobil; (x,y) tekerlek hizası tabanı
    return (f'<g transform="translate({x},{y}) scale({s})">{shadow(380,12,360,18,.45)}'
            f'<path d="M20 -80 C20 -120 60 -140 110 -150 L250 -205 C300 -225 420 -225 480 -190 L560 -140 C640 -128 720 -110 740 -80 L740 -40 L20 -40Z" fill="{body}"/>'
            f'<path d="M270 -195 C320 -212 410 -212 455 -185 L520 -140 L255 -140Z" fill="{glass}"/><path d="M360 -208 L372 -140" stroke="{body}" stroke-width="10"/>'
            f'<rect x="20" y="-62" width="720" height="10" fill="#000" opacity=".16"/>'
            f'<circle cx="170" cy="-38" r="62" fill="{dark}"/><circle cx="170" cy="-38" r="34" fill="#b9bfc8"/><circle cx="170" cy="-38" r="12" fill="{dark}"/>'
            f'<circle cx="590" cy="-38" r="62" fill="{dark}"/><circle cx="590" cy="-38" r="34" fill="#b9bfc8"/><circle cx="590" cy="-38" r="12" fill="{dark}"/>'
            f'<rect x="715" y="-100" width="30" height="22" rx="6" fill="#ffd36b"/><rect x="14" y="-98" width="22" height="20" rx="5" fill="#ff5a4d"/></g>')

def box(x, y, w, h, col, tape=True, sh=True):
    t = f'<rect x="{x+w/2-14}" y="{y}" width="28" height="{h}" fill="#000" opacity=".12"/><rect x="{x}" y="{y}" width="{w}" height="{h*.18}" fill="#000" opacity=".1"/>' if tape else ''
    return (shadow(x+w/2, y+h+6, w*.6, 10, .3) if sh else '') + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{col}"/>{t}'

def wheel(cx, cy, r, tire='#15171c', rim='#c5cbd4', spokes=5):
    sp = ''.join(f'<rect x="{cx-r*.07}" y="{cy-r*.62}" width="{r*.14}" height="{r*.62}" rx="{r*.05}" fill="{rim}" transform="rotate({i*360/spokes} {cx} {cy})"/>' for i in range(spokes))
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{tire}"/><circle cx="{cx}" cy="{cy}" r="{r*.72}" fill="#2a2e36"/><circle cx="{cx}" cy="{cy}" r="{r*.66}" fill="{rim}" opacity=".25"/>{sp}'
            f'<circle cx="{cx}" cy="{cy}" r="{r*.16}" fill="{rim}"/>')

def truck(x, y, s, cab, cargo, dark='#16181d'):
    return (f'<g transform="translate({x},{y}) scale({s})">{shadow(430,14,450,18,.45)}'
            f'<rect x="0" y="-330" width="620" height="260" rx="14" fill="{cargo}"/><rect x="0" y="-330" width="620" height="26" fill="#000" opacity=".12"/>'
            f'<path d="M640 -240 L760 -240 C790 -240 800 -222 812 -196 L850 -130 L850 -70 L640 -70Z" fill="{cab}"/><path d="M668 -222 L752 -222 L800 -150 L668 -150Z" fill="#cfe6f2"/>'
            f'<rect x="0" y="-74" width="850" height="22" fill="#000" opacity=".25"/>'
            f'<circle cx="150" cy="-44" r="52" fill="{dark}"/><circle cx="150" cy="-44" r="26" fill="#b9bfc8"/><circle cx="290" cy="-44" r="52" fill="{dark}"/><circle cx="290" cy="-44" r="26" fill="#b9bfc8"/>'
            f'<circle cx="730" cy="-44" r="52" fill="{dark}"/><circle cx="730" cy="-44" r="26" fill="#b9bfc8"/></g>')

def scissors(cx, cy, s, col='#d9dde3', handle='#e6a23c', rot=-25):
    return (f'<g transform="translate({cx},{cy}) rotate({rot}) scale({s})">'
            f'<path d="M-10 -20 L260 -300 L276 -286 L20 4Z" fill="{col}"/><path d="M10 -4 L-260 -300 L-276 -286 L-14 22Z" fill="{col}" opacity=".92"/>'
            f'<circle cx="0" cy="0" r="14" fill="#8b929c"/><ellipse cx="-70" cy="90" rx="62" ry="78" fill="none" stroke="{handle}" stroke-width="26"/>'
            f'<ellipse cx="70" cy="90" rx="62" ry="78" fill="none" stroke="{handle}" stroke-width="26"/></g>')

def mirror(x, y, w, h, frame='#caa469', glass='#e9eef2'):
    return (f'{shadow(x+w/2,y+h+10,w*.55,12,.3)}<rect x="{x-18}" y="{y-18}" width="{w+36}" height="{h+36}" rx="{w/2+18}" fill="{frame}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{w/2}" fill="{glass}"/><path d="M{x+w*.2} {y+h*.8} L{x+w*.55} {y+h*.15}" stroke="#fff" stroke-width="22" opacity=".55" stroke-linecap="round"/>')

def roll(x, y, w, r, col, dark):
    return (f'{shadow(x+w/2, y+r*2+8, w*.6, 12, .3)}<rect x="{x}" y="{y}" width="{w}" height="{r*2}" rx="{r}" fill="{col}"/>'
            f'<ellipse cx="{x+w}" cy="{y+r}" rx="{r*.45}" ry="{r}" fill="{dark}"/><ellipse cx="{x+w}" cy="{y+r}" rx="{r*.16}" ry="{r*.36}" fill="#e8dcc6"/>'
            + ''.join(f'<path d="M{x+i*w/7} {y+4} L{x+i*w/7+12} {y+r*2-4}" stroke="#fff" stroke-width="3" opacity=".12"/>' for i in range(1, 7)))

def bag(x, y, w, h, col, handle='#222'):
    return (f'{shadow(x+w/2,y+h+8,w*.6,12,.3)}<path d="M{x+w*.28} {y+h*.12} C{x+w*.28} {y-h*.1} {x+w*.72} {y-h*.1} {x+w*.72} {y+h*.12}" fill="none" stroke="{handle}" stroke-width="12" stroke-linecap="round"/>'
            f'<path d="M{x} {y+h*.1} L{x+w} {y+h*.1} L{x+w*.94} {y+h} L{x+w*.06} {y+h}Z" fill="{col}"/><rect x="{x}" y="{y+h*.1}" width="{w}" height="{h*.1}" fill="#000" opacity=".1"/>')

def spray(x, y, s, body, cap):
    return (f'<g transform="translate({x},{y}) scale({s})">{shadow(80,320,110,14,.3)}<rect x="10" y="90" width="140" height="230" rx="28" fill="{body}" opacity=".92"/>'
            f'<rect x="30" y="170" width="100" height="90" rx="8" fill="#fff" opacity=".85"/><rect x="45" y="190" width="70" height="10" rx="4" fill="{cap}"/><rect x="45" y="212" width="50" height="8" rx="4" fill="#9aa4ae"/>'
            f'<rect x="50" y="60" width="60" height="40" fill="{cap}"/><path d="M50 60 L50 30 L150 30 L150 52 L110 52 L110 60Z" fill="{cap}"/></g>')

def bubbles(seed, n, x0, x1, y0, y1, col='#fff'):
    r = random.Random(seed); out = ''
    for _ in range(n):
        x, y, rr = r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(10, 46)
        out += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr:.0f}" fill="{col}" opacity=".16"/><circle cx="{x-rr*.3:.0f}" cy="{y-rr*.3:.0f}" r="{rr*.22:.0f}" fill="#fff" opacity=".5"/>'
    return out

def leaf(x, y, s, rot, col):
    return f'<path transform="translate({x},{y}) rotate({rot}) scale({s})" d="M0 0 C60 -60 140 -50 190 0 C140 50 60 60 0 0Z" fill="{col}"/>'

def stones(x, y, col):
    return ''.join(f'{shadow(x+ox, y+oy+34, 90*k, 10, .3)}<ellipse cx="{x+ox}" cy="{y+oy}" rx="{90*k}" ry="{38*k}" fill="{col}"/><ellipse cx="{x+ox-10}" cy="{y+oy-8}" rx="{60*k}" ry="{18*k}" fill="#fff" opacity=".14"/>' for ox, oy, k in ((0, 0, 1.2), (20, -64, 1.0), (10, -118, .78)))

def cone(x, y, s):
    return (f'<g transform="translate({x},{y}) scale({s})">{shadow(70,0,95,10,.35)}<path d="M25 0 L115 0 L88 -190 L52 -190Z" fill="#ff7a1a"/><rect x="0" y="-8" width="140" height="18" rx="6" fill="#d95f0a"/>'
            f'<path d="M62 -120 L78 -120 L82 -90 L58 -90Z" fill="#fff"/><path d="M69 -170 L81 -170 L84 -140 L56 -140Z" fill="#fff"/></g>')

def phone(x, y, w, h, tiles):
    t = ''.join(f'<rect x="{x+22+(i%2)*(w/2-14)}" y="{y+90+(i//2)*(w/2+8)}" width="{w/2-30}" height="{w/2-14}" rx="12" fill="{c}"/>' for i, c in enumerate(tiles))
    return (f'{shadow(x+w/2,y+h+6,w*.55,12,.35)}<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="44" fill="#14161b"/><rect x="{x+10}" y="{y+10}" width="{w-20}" height="{h-20}" rx="36" fill="#f6f4ef"/>'
            f'<rect x="{x+22}" y="{y+34}" width="{w-44}" height="34" rx="17" fill="#e6e2d8"/>{t}')

def hanger(x, y, col):
    return f'<g transform="translate({x},{y})"><path d="M0 0 L0 -26 C0 -52 36 -52 36 -30" fill="none" stroke="#222" stroke-width="6" stroke-linecap="round"/><path d="M0 0 L-90 62 L90 62Z" fill="{col}" opacity=".95"/></g>'

def sewing(x, y, s, body):
    return (f'<g transform="translate({x},{y}) scale({s})">{shadow(250,300,300,16,.35)}<path d="M20 300 L20 240 L60 240 L60 120 C60 70 100 40 150 40 L440 40 L440 110 L330 110 L330 240 L480 240 L480 300Z" fill="{body}"/>'
            f'<rect x="330" y="110" width="26" height="130" fill="#b9bfc8"/><circle cx="130" cy="130" r="42" fill="#0000001a"/><circle cx="130" cy="130" r="26" fill="#d6dae0"/><rect x="40" y="280" width="450" height="20" fill="#000" opacity=".2"/></g>')

def sofa(x, y, w, col):
    return (f'{shadow(x+w/2,y+150,w*.55,12,.3)}<rect x="{x}" y="{y}" width="{w}" height="120" rx="26" fill="{col}"/><rect x="{x-24}" y="{y+40}" width="60" height="110" rx="22" fill="{col}"/><rect x="{x+w-36}" y="{y+40}" width="60" height="110" rx="22" fill="{col}"/>'
            f'<rect x="{x+30}" y="{y+30}" width="{w/2-40}" height="90" rx="16" fill="#fff" opacity=".14"/><rect x="{x+w/2+10}" y="{y+30}" width="{w/2-40}" height="90" rx="16" fill="#fff" opacity=".14"/>')

# ---- sahneler: (renk1, renk2, gövde)
def scenes():
    S = {}
    # OTO SERVİS
    S['oto_servis'] = [
        ('#1f2a37', '#3b4a5c', floor(760, '#10151c', .75) + '<rect x="120" y="170" width="14" height="590" fill="#6c7a8c"/><rect x="1466" y="170" width="14" height="590" fill="#6c7a8c"/><rect x="100" y="150" width="1400" height="26" rx="8" fill="#5b697a"/>' + ''.join(f'<rect x="{200+i*210}" y="215" width="130" height="14" rx="6" fill="#ffe08a" opacity=".85"/>' for i in range(6)) + car(330, 740, 1.35, '#e04b3a')),
        ('#27323f', '#44566b', floor(780, '#0f141b', .7) + wheel(800, 470, 330) + '<circle cx="800" cy="470" r="370" fill="none" stroke="#fff" stroke-width="3" opacity=".12"/>' + f'<rect x="1180" y="330" width="260" height="20" rx="10" fill="#e8b73c" transform="rotate(-24 1180 330)"/><circle cx="1196" cy="330" r="34" fill="none" stroke="#e8b73c" stroke-width="20"/>'),
        ('#2c3a4a', '#566a80', floor(800, '#0e1218', .6) + '<rect x="200" y="120" width="1200" height="520" rx="24" fill="#18202a"/>' + ''.join(f'<rect x="{240+i*290}" y="160" width="250" height="200" rx="14" fill="#223041"/><circle cx="{365+i*290}" cy="260" r="70" fill="none" stroke="#7fd1ae" stroke-width="12" stroke-dasharray="{200-i*40} 600"/>' for i in range(4)) + '<rect x="240" y="410" width="1120" height="190" rx="14" fill="#223041"/>' + ''.join(f'<rect x="{280+i*66}" y="{560-(40+((i*37)%110))}" width="40" height="{40+((i*37)%110)}" rx="6" fill="#e04b3a" opacity=".85"/>' for i in range(16))),
    ]
    S['oto_cekici'] = [
        ('#2b1f3a', '#e0763a', floor(790, '#15121c', .95) + '<rect y="905" width="1600" height="14" fill="#f2c23c" opacity=".8" />' + truck(220, 800, 1.3, '#f2b632', '#2f3945') + car(330, 520, .7, '#d9453a')),
        ('#1c2b3d', '#3d5876', floor(800, '#10141b', .95) + cone(260, 800, 2.2) + cone(1180, 800, 2.4) + '<rect x="140" y="860" width="1320" height="16" fill="#ff7a1a" opacity=".5"/>' + car(520, 720, .9, '#e8e8ea')),
        ('#14202e', '#5e3c2a', floor(780, '#0e1015', .95) + ''.join(f'<rect x="{80+i*260}" y="880" width="150" height="14" rx="7" fill="#f2c23c" opacity=".85"/>' for i in range(6)) + truck(420, 760, 1.5, '#e9573f', '#2f3945') + '<circle cx="1260" cy="260" r="110" fill="#ffd28a" opacity=".5"/>'),
    ]
    S['kuafor'] = [
        ('#3b2a2a', '#7a5a4a', floor(820, '#2a1d1d', .6) + mirror(180, 120, 520, 620) + mirror(900, 120, 520, 620) + f'<rect x="120" y="740" width="1400" height="40" rx="10" fill="#caa469"/>' + ''.join(f'<rect x="{200+i*120}" y="{660 if i%2 else 640}" width="46" height="{100 if i%2 else 120}" rx="10" fill="{c}"/>' for i, c in enumerate(('#e6b8a2', '#9db4a8', '#c97a6d', '#e8d4a8', '#8f6f61', '#d98c5f')))),
        ('#233036', '#4c6a68', scissors(800, 520, 1.5) + f'<rect x="1100" y="640" width="360" height="40" rx="8" fill="#1b2326"/>' + ''.join(f'<rect x="{1110+i*20}" y="{680}" width="8" height="{60+(i%3)*10}" fill="#1b2326"/>' for i in range(16))),
        ('#5a4036', '#c9a37a', floor(840, '#3a2a22', .7) + shadow(780, 760, 520, 22, .3) + '<path d="M300 380 C300 270 420 230 560 230 L880 230 C980 230 1040 300 1040 380 C1040 470 980 520 880 520 L560 520 C420 520 300 480 300 380Z" fill="#2a2e34"/><rect x="1020" y="300" width="150" height="160" rx="26" fill="#1d2025"/><rect x="560" y="500" width="150" height="250" rx="30" fill="#2a2e34" transform="rotate(-8 635 625)"/><circle cx="560" cy="380" r="86" fill="#caa469"/><circle cx="560" cy="380" r="48" fill="#2a2e34"/>' + ''.join(f'<rect x="{1190+i*18}" y="{320+i*4}" width="10" height="120" rx="5" fill="#caa469" opacity=".8"/>' for i in range(6))),
    ]
    S['nakliye'] = [
        ('#1f3a5c', '#e8a33c', floor(790, '#20252d', .95) + '<rect y="905" width="1600" height="12" fill="#fff" opacity=".35"/>' + truck(250, 800, 1.45, '#e8a33c', '#f4f1ea')),
        ('#2a3d52', '#6c8aa8', floor(800, '#2b2f36', .9) + box(240, 560, 300, 240, '#c99a5c') + box(540, 520, 340, 280, '#d6aa6c') + box(880, 580, 260, 220, '#b9894e') + box(300, 380, 220, 180, '#d6aa6c') + box(580, 280, 260, 240, '#c99a5c') + box(1180, 620, 220, 180, '#d6aa6c')),
        ('#3a2f2a', '#8a6a52', floor(790, '#241d19', .85) + sofa(360, 560, 560, '#6d8da6') + box(1020, 560, 280, 230, '#c99a5c') + box(1100, 400, 200, 160, '#d6aa6c') + '<rect x="1360" y="300" width="14" height="500" fill="#bda27c"/>'),
    ]
    S['tekstil'] = [
        ('#3a2c4a', '#b4658a', floor(800, '#2a2030', .8) + roll(200, 520, 560, 96, '#e0b84a', '#b8902a') + roll(260, 330, 520, 90, '#3f7d9a', '#2a5c75') + roll(840, 560, 520, 96, '#c0453a', '#8f2f27') + roll(900, 370, 480, 90, '#7a9a5a', '#58763c')),
        ('#2b3a45', '#8aa4b3', floor(800, '#1f2a33', .7) + sewing(380, 200, 2.0, '#e6e2d8') + '<path d="M1160 700 C1250 640 1340 660 1420 700" stroke="#e0b84a" stroke-width="8" fill="none"/>'),
        ('#2e2f3e', '#7d8fb0', '<rect x="200" y="200" width="1200" height="12" rx="6" fill="#d6dae0"/>' + ''.join(hanger(300 + i * 200, 200, c) for i, c in enumerate(('#c0453a', '#3f7d9a', '#e0b84a', '#7a9a5a', '#e8e2d4', '#8f6fb0', '#e07a5a'))) + floor(800, '#1d1f2c', .7)),
    ]
    S['eticaret'] = [
        ('#233a5c', '#f08a4b', floor(800, '#1b2433', .8) + bag(260, 380, 360, 420, '#f08a4b') + bag(640, 300, 320, 500, '#ffffff') + bag(1000, 420, 340, 380, '#2f6f73') + box(1260, 560, 220, 240, '#c99a5c')),
        ('#2a3550', '#6a82b0', phone(560, 100, 480, 800, ['#f08a4b', '#2f6f73', '#c0453a', '#e0b84a', '#7a9a5a', '#8f6fb0']) + bubbles(3, 8, 100, 1500, 100, 900, '#fff')),
        ('#3a3328', '#a89870', floor(790, '#2c261d', .9) + box(300, 520, 520, 270, '#c99a5c') + box(880, 440, 380, 350, '#d6aa6c') + '<rect x="300" y="520" width="520" height="30" fill="#000" opacity=".14"/><rect x="320" y="640" width="140" height="90" rx="6" fill="#fff"/><rect x="334" y="656" width="100" height="8" fill="#555"/><rect x="334" y="676" width="70" height="8" fill="#999"/>'),
    ]
    S['temizlik'] = [
        ('#1f5a6e', '#7fd0cc', bubbles(5, 22, 80, 1520, 80, 880, '#ffffff') + spray(560, 300, 2.4, '#4aa7c9', '#2f6f73') + floor(900, '#1a4a5a', .5)),
        ('#2a6b6a', '#a8dcc2', floor(800, '#1d4d4d', .6) + '<path d="M400 780 L470 460 L930 460 L1000 780Z" fill="#e8b73c"/><rect x="400" y="440" width="600" height="40" rx="12" fill="#c9951f"/><rect x="1020" y="140" width="22" height="650" rx="10" fill="#8b6a3a"/>' + ''.join(f'<rect x="{960+i*22}" y="{700}" width="14" height="110" rx="6" fill="#e8e2d4"/>' for i in range(8)) + bubbles(8, 12, 400, 1000, 380, 700, '#fff')),
        ('#31576b', '#a7c8d8', '<rect x="260" y="120" width="1080" height="700" rx="14" fill="#cfe6f2" opacity=".55"/><rect x="800" y="120" width="14" height="700" fill="#eaf3f8"/><rect x="260" y="470" width="1080" height="14" fill="#eaf3f8"/>' + ''.join(f'<path transform="translate({x},{y}) scale({s})" d="M0 -40 L10 -10 L40 0 L10 10 L0 40 L-10 10 L-40 0 L-10 -10Z" fill="#fff" opacity=".9"/>' for x, y, s in ((520, 300, 2.4), (1120, 640, 3), (980, 250, 1.6), (380, 640, 1.8)))),
    ]
    S['guzellik'] = [
        ('#4a3a3a', '#d9b8a0', floor(820, '#34282a', .6) + stones(700, 720, '#8a7a72') + leaf(840, 560, 2.2, -60, '#6d8f6a') + leaf(870, 600, 2.4, -20, '#7aa07a') + leaf(780, 640, 2, -120, '#58795a') + '<circle cx="1180" cy="300" r="140" fill="#f4d9c6" opacity=".7"/>'),
        ('#3d3140', '#c797a8', ''.join(f'<rect x="{360+i*130}" y="{240+(i%3)*40}" width="34" height="{360-(i%3)*40}" rx="14" fill="#d6b88a"/><ellipse cx="{377+i*130}" cy="{230+(i%3)*40}" rx="40" ry="70" fill="{c}"/>' for i, c in enumerate(('#2a2a2e', '#c97a8f', '#e8c4a8', '#8f6f61', '#2a2a2e', '#d98c8f', '#e8d4a8'))) + floor(820, '#2e2433', .6)),
        ('#2f3a38', '#a5c4b8', leaf(300, 700, 3, -70, '#5e8a6a') + leaf(500, 760, 2.6, -40, '#7aa88a') + leaf(1000, 740, 3, -140, '#4a7a5e') + leaf(1180, 700, 2.4, -110, '#7aa88a') + '<path d="M800 220 C940 220 1010 330 1010 460 C1010 620 900 700 800 700 C700 700 590 620 590 460 C590 330 660 220 800 220Z" fill="#f0d6c4" opacity=".92"/><path d="M700 430 Q740 410 770 430 M830 430 Q860 410 900 430" stroke="#6b4a40" stroke-width="10" fill="none" stroke-linecap="round"/><path d="M740 560 Q800 610 860 560" stroke="#c9707a" stroke-width="14" fill="none" stroke-linecap="round"/>'),
    ]
    return S

def render(name, idx, c1, c2, body):
    f = os.path.join(HERE, f'_{name}{idx}.svg'); open(f, 'w').write(svg(body, c1, c2))
    png = f.replace('.svg', '.png'); subprocess.run(['rsvg-convert', '-w', str(W), '-h', str(H), '-o', png, f], check=True)
    im = Image.open(png).convert('RGB')
    # hafif doku (düz vektör görünümünü kırar)
    import numpy as np
    a = np.asarray(im).astype('int16'); rng = np.random.default_rng(idx + len(name)); a += rng.integers(-5, 6, a.shape[:2])[..., None]
    Image.fromarray(a.clip(0, 255).astype('uint8')).resize((1280, 800)).save(os.path.join(OUT, f'{name}{"" if idx == 1 else idx}.jpg'), quality=82, optimize=True)
    os.remove(f); os.remove(png)

if __name__ == '__main__':
    for name, lst in scenes().items():
        for i, (c1, c2, body) in enumerate(lst, 1):
            render(name, i, c1, c2, body)
    print('tamam', sorted(f for f in os.listdir(OUT) if f.startswith(('oto', 'kuafor', 'nakliye', 'tekstil', 'eticaret', 'temizlik', 'guzellik'))))
