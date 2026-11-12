# -*- coding: utf-8 -*-
"""QR üreteci: dışarıdan kütüphane istemeden, baskıya uygun SVG.

Lokanta masasındaki kare, kahve lekesi ve loş ışık altında okunacak. Bu yüzden
kodu resim olarak değil SVG olarak basıyoruz (baskıda keskin kalır) ve hata
düzeltme düzeyini M tutuyoruz — kodun yaklaşık dörtte biri zarar görse bile
okunur.

Kapsam: bayt kipi (UTF-8), sürüm 1-10, düzey M. Bir menü bağlantısı için
fazlasıyla yeter; daha uzun metin istendiğinde hata verir, sessizce bozuk kod
üretmez.
"""

# --- GF(256) tabloları (QR'ın kullandığı 0x11D polinomu)
EXP = [0] * 512
LOG = [0] * 256
_x = 1
for _i in range(255):
    EXP[_i] = _x
    LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    EXP[_i] = EXP[_i - 255]


def _mul(a, b):
    return 0 if a == 0 or b == 0 else EXP[LOG[a] + LOG[b]]


def _rs_poly(n):
    p = [1]
    for i in range(n):
        q = [1, EXP[i]]
        r = [0] * (len(p) + 1)
        for a in range(len(p)):
            for b in range(2):
                r[a + b] ^= _mul(p[a], q[b])
        p = r
    return p


def _ecc(data, n):
    gen = _rs_poly(n)
    res = list(data) + [0] * n
    for i in range(len(data)):
        c = res[i]
        if c:
            for j in range(len(gen)):
                res[i + j] ^= _mul(gen[j], c)
    return res[len(data):]


# sürüm: (toplam veri baytı, blok başına ecc, g1 blok, g1 bayt, g2 blok, g2 bayt) — düzey M
VER = {1: (16, 10, 1, 16, 0, 0), 2: (28, 16, 1, 28, 0, 0), 3: (44, 26, 1, 44, 0, 0),
       4: (64, 18, 2, 32, 0, 0), 5: (86, 24, 2, 43, 0, 0), 6: (108, 16, 4, 27, 0, 0),
       7: (124, 18, 4, 31, 0, 0), 8: (154, 22, 2, 38, 2, 39), 9: (182, 22, 3, 36, 2, 37),
       10: (216, 26, 4, 43, 1, 44)}
ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
         7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]}
# düzey M için biçim bilgisi (maske 0-7), 15 bit
FORMAT_M = [0x5412, 0x5125, 0x5E7C, 0x5B4B, 0x45F9, 0x40CE, 0x4F97, 0x4AA0]


def _bits(data, ver):
    cap = VER[ver][0]
    say = 8 if ver < 10 else 16
    b = []
    b += [(4 >> i) & 1 for i in range(3, -1, -1)]                  # bayt kipi
    b += [(len(data) >> i) & 1 for i in range(say - 1, -1, -1)]
    for ch in data:
        b += [(ch >> i) & 1 for i in range(7, -1, -1)]
    b += [0] * min(4, cap * 8 - len(b))                            # bitiş
    b += [0] * ((8 - len(b) % 8) % 8)
    pad = [0xEC, 0x11]
    i = 0
    while len(b) < cap * 8:
        b += [(pad[i % 2] >> k) & 1 for k in range(7, -1, -1)]
        i += 1
    return [int("".join(str(x) for x in b[i:i + 8]), 2) for i in range(0, len(b), 8)]


def _interleave(bytes_, ver):
    _cap, ecn, g1, b1, g2, b2 = VER[ver]
    blocks, p = [], 0
    for _ in range(g1):
        blocks.append(bytes_[p:p + b1]); p += b1
    for _ in range(g2):
        blocks.append(bytes_[p:p + b2]); p += b2
    eccs = [_ecc(b, ecn) for b in blocks]
    out = []
    for i in range(max(len(b) for b in blocks)):
        for b in blocks:
            if i < len(b):
                out.append(b[i])
    for i in range(ecn):
        for e in eccs:
            out.append(e[i])
    return out


def _skeleton(ver):
    n = ver * 4 + 17
    m = [[None] * n for _ in range(n)]

    def kare(r, c):
        for i in range(-1, 8):
            for j in range(-1, 8):
                if 0 <= r + i < n and 0 <= c + j < n:
                    v = 0 <= i <= 6 and 0 <= j <= 6 and (i in (0, 6) or j in (0, 6)
                                                         or 2 <= i <= 4 and 2 <= j <= 4)
                    m[r + i][c + j] = 1 if v else 0
    kare(0, 0); kare(0, n - 7); kare(n - 7, 0)
    for i in range(8, n - 8):
        m[6][i] = m[i][6] = 1 - i % 2
    for a in ALIGN[ver]:
        for b in ALIGN[ver]:
            if (a < 8 and b < 8) or (a < 8 and b > n - 9) or (a > n - 9 and b < 8):
                continue
            for i in range(-2, 3):
                for j in range(-2, 3):
                    m[a + i][b + j] = 1 if (abs(i) == 2 or abs(j) == 2 or (i == 0 and j == 0)) else 0
    m[n - 8][8] = 1                                                # koyu modül
    for i in range(9):                                             # biçim alanı ayrılır
        if m[8][i] is None:
            m[8][i] = 0
        if m[i][8] is None:
            m[i][8] = 0
    for i in range(8):
        if m[8][n - 1 - i] is None:
            m[8][n - 1 - i] = 0
        if m[n - 1 - i][8] is None:
            m[n - 1 - i][8] = 0
    return m, n


def _reserved(ver, n):
    """Veri yazılamayacak hücreler."""
    r = [[False] * n for _ in range(n)]
    def blok(x0, y0, w, h):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if 0 <= x < n and 0 <= y < n:
                    r[y][x] = True
    blok(0, 0, 9, 9); blok(n - 8, 0, 8, 9); blok(0, n - 8, 9, 8)
    for i in range(n):
        r[6][i] = True
        r[i][6] = True
    for a in ALIGN[ver]:
        for b in ALIGN[ver]:
            if (a < 8 and b < 8) or (a < 8 and b > n - 9) or (a > n - 9 and b < 8):
                continue
            blok(b - 2, a - 2, 5, 5)
    return r


def _mask(i, r, c):
    return [(r + c) % 2 == 0, r % 2 == 0, c % 3 == 0, (r + c) % 3 == 0,
            (r // 2 + c // 3) % 2 == 0, (r * c) % 2 + (r * c) % 3 == 0,
            ((r * c) % 2 + (r * c) % 3) % 2 == 0, ((r + c) % 2 + (r * c) % 3) % 2 == 0][i]


def _ceza(m, n):
    p = 0
    for satir in list(m) + [list(x) for x in zip(*m)]:             # 1. kural
        say, onc = 1, satir[0]
        for v in satir[1:]:
            if v == onc:
                say += 1
            else:
                if say >= 5:
                    p += say - 2
                say, onc = 1, v
        if say >= 5:
            p += say - 2
    for r in range(n - 1):                                         # 2. kural
        for c in range(n - 1):
            if m[r][c] == m[r][c + 1] == m[r + 1][c] == m[r + 1][c + 1]:
                p += 3
    desen = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
    for satir in list(m) + [list(x) for x in zip(*m)]:             # 3. kural
        for i in range(n - 10):
            if satir[i:i + 11] == desen or satir[i:i + 11] == desen[::-1]:
                p += 40
    koyu = sum(sum(r) for r in m)
    p += abs(koyu * 100 // (n * n) - 50) // 5 * 10                 # 4. kural
    return p


def matrix(text, ver=0):
    """Metni QR hücre dizisine çevir (1 = koyu)."""
    data = str(text or "").encode("utf-8")
    if not data:
        return []
    if not ver:
        for v in range(1, 11):
            say = 8 if v < 10 else 16
            if 4 + say + len(data) * 8 <= VER[v][0] * 8:
                ver = v
                break
        if not ver:
            raise ValueError("Metin çok uzun: QR için en çok %d bayt" % VER[10][0])
    kod = _interleave(_bits(data, ver), ver)
    iskelet, n = _skeleton(ver)
    rez = _reserved(ver, n)
    bitler = [(b >> i) & 1 for b in kod for i in range(7, -1, -1)]
    enler = []
    for maske in range(8):
        m = [list(r) for r in iskelet]
        p, yon, c = 0, -1, n - 1
        r = n - 1
        while c > 0:
            if c == 6:
                c -= 1
            for _ in range(n):
                for dc in (0, 1):
                    x = c - dc
                    if not rez[r][x]:
                        bit = bitler[p] if p < len(bitler) else 0
                        p += 1
                        m[r][x] = bit ^ (1 if _mask(maske, r, x) else 0)
                r += yon
                if r < 0 or r >= n:
                    r = 0 if r < 0 else n - 1
                    yon = -yon
                    break
            c -= 2
        f = FORMAT_M[maske]
        for i in range(15):
            bit = (f >> i) & 1
            if i < 6:
                m[8][i] = bit
            elif i == 6:
                m[8][7] = bit
            elif i == 7:
                m[8][8] = bit
            elif i == 8:
                m[7][8] = bit
            else:
                m[14 - i][8] = bit
            if i < 8:
                m[n - 1 - i][8] = bit
            else:
                m[8][n - 15 + i] = bit
        m[n - 8][8] = 1
        enler.append((_ceza(m, n), m))
    return min(enler, key=lambda x: x[0])[1]


def svg(text, px=6, kenar=4, renk="#101828"):
    """QR'ı SVG olarak çiz. px: bir hücrenin kenarı, kenar: sessiz alan (hücre)."""
    m = matrix(text)
    if not m:
        return ""
    n = len(m)
    boy = (n + kenar * 2) * px
    yollar = []
    for r in range(n):
        c = 0
        while c < n:
            if m[r][c]:
                s = c
                while c + 1 < n and m[r][c + 1]:
                    c += 1
                yollar.append("M%d %dh%dv%dh-%dz" % ((s + kenar) * px, (r + kenar) * px,
                                                     (c - s + 1) * px, px, (c - s + 1) * px))
            c += 1
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
            'shape-rendering="crispEdges" role="img" aria-label="QR kod">'
            '<rect width="100%%" height="100%%" fill="#fff"/><path fill="%s" d="%s"/></svg>'
            % (boy, boy, boy, boy, renk, "".join(yollar)))
