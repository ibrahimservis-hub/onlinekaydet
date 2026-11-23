# -*- coding: utf-8 -*-
"""Sektör simgeli, iki renkli yazılı logolar -> logo/NN.svg (açık zemin), logo/NN-beyaz.svg (koyu zemin). Yazı yola çevrilir."""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from pano import T
from logo_ikon import IK
FD = "/tmp/fz/node_modules/@fontsource/poppins/files/poppins-%s-800-normal.woff"
FN = [TTFont(FD % "latin"), TTFont(FD % "latin-ext")]
SPLIT = {"Teknofix": ("Tekno", "fix"), "Volt & Su": ("Volt &", "Su")}
NOSP = {"Teknofix"}

def dark(h, f=.72):
    r, g, b = [int(h[i:i+2], 16) for i in (1, 3, 5)]
    if (.299*r + .587*g + .114*b) / 255 < .55: return h
    return "#%02x%02x%02x" % (int(r*f), int(g*f), int(b*f))

def glyph(ch):
    for f in FN:
        cm = f.getBestCmap()
        if ord(ch) in cm: return f, cm[ord(ch)]
    return FN[0], ".notdef"

def text_path(txt, size, x0):
    s = size / 1000.0; x = x0; d = []
    for ch in txt:
        f, g = glyph(ch); gs = f.getGlyphSet(); upm = f["head"].unitsPerEm; k = size / upm
        pen = SVGPathPen(gs); tp = TransformPen(pen, (k, 0, 0, -k, x, 0)); gs[g].draw(tp)
        d.append(pen.getCommands()); x += gs[g].width * k
    return " ".join(d), x

def make(k, t, white):
    nm = t[0]; dk, ac = t[3][0], t[3][1]
    a, b = SPLIT.get(nm) or ((nm.rsplit(" ", 1) + [""])[:2] if " " in nm else (nm, ""))
    if not b: a, b = "", nm
    ink = "#ffffff" if white else dk
    if not white: ac = dark(ac)
    d1, x1 = text_path(a + (" " if a and b and nm not in NOSP else ""), 40, 80)
    d2, x2 = text_path(b, 40, x1)
    W = x2 + 6; H = 72
    mark = ('<g transform="translate(10 2) scale(1.9)" fill="none" stroke="%s" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">%s</g>'
            '<path d="M6 57Q36 76 70 50" fill="none" stroke="%s" stroke-width="5.5" stroke-linecap="round"/>') % (ink, IK[k], ac)
    word = '<g transform="translate(0 50)"><path d="%s" fill="%s"/><path d="%s" fill="%s"/></g>' % (d1, ink, d2, ac)
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %d" height="%d" role="img" aria-label="%s">%s%s</svg>' % (W, H, H, nm, mark, word)

if __name__ == "__main__":
    os.makedirs("logo", exist_ok=True)
    for k, t in enumerate(T, 1):
        open("logo/%02d.svg" % k, "w").write(make(k, t, False))
        open("logo/%02d-beyaz.svg" % k, "w").write(make(k, t, True))
    print("ok")
