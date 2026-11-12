"""QR üreteci doğrulaması.

Dış kütüphane çalıştırmadan doğruluyoruz; üç bağımsız kontrol:

1. Yapı: bulucu kareler, zamanlama çizgileri, hizalama desenleri, koyu modül.
2. Hata düzeltme: üretilen kod sözcüğü, üreteç kökleri α^0..α^(n-1) için sıfır
   veriyor mu? Reed-Solomon'un tanımı budur; tutuyorsa ECC baytları doğrudur.
3. Geri okuma: maskeyi kaldırıp blokları ayırıyor, veri baytlarını okuyup metni
   geri çıkarıyoruz. Yerleşim, maske, serpiştirme ve bit paketleme yanlışsa
   metin geri gelmez.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import qr

n_ok = 0
def ok(c, m):
    global n_ok
    assert c, m
    n_ok += 1

# ---- 1. yapı
for metin in ("https://onlinekaydet.com/menu/demo", "A"):
    m = qr.matrix(metin)
    n = len(m)
    ok(n == len(m[0]) and (n - 17) % 4 == 0, "kare ve geçerli sürüm olmalı: %d" % n)
    for r0, c0 in ((0, 0), (0, n - 7), (n - 7, 0)):
        halka = [m[r0 + i][c0 + j] for i in range(7) for j in range(7)]
        ok(sum(halka) == 33, "bulucu kare 33 koyu hücre taşır")
        ok(m[r0 + 3][c0 + 3] == 1 and m[r0 + 1][c0 + 1] == 0, "bulucu kare ortası dolu, ikinci halka boş")
    ok(all(m[6][i] == 1 - i % 2 for i in range(8, n - 8)), "yatay zamanlama çizgisi şaşmamalı")
    ok(all(m[i][6] == 1 - i % 2 for i in range(8, n - 8)), "dikey zamanlama çizgisi şaşmamalı")
    ok(m[n - 8][8] == 1, "koyu modül yerinde olmalı")

# ---- 2. Reed-Solomon: kod sözcüğü üreteç köklerinde sıfırlanmalı
def deger(poli, x):
    y = 0
    for c in poli:
        y = qr._mul(y, x) ^ c
    return y

for veri, ecn in (([32, 91, 11, 120, 209, 114, 220, 77, 67, 64, 236, 17, 236, 17, 236, 17], 10),
                  (list(range(1, 45)), 26)):
    tam = list(veri) + qr._ecc(veri, ecn)
    kokler = [deger(tam, qr.EXP[i]) for i in range(ecn)]
    ok(not any(kokler), "ECC hatalı: kökler sıfırlanmadı %s" % kokler[:4])
ok(len(qr._ecc([1, 2, 3], 10)) == 10, "istenen kadar ECC baytı üretilmeli")

# ---- 3. geri okuma (kendi çözücümüz)
def coz(m):
    n = len(m)
    ver = (n - 17) // 4
    # biçim bilgisinden maskeyi oku
    biz = 0
    for i in range(15):
        if i < 6:
            b = m[8][i]
        elif i == 6:
            b = m[8][7]
        elif i == 7:
            b = m[8][8]
        elif i == 8:
            b = m[7][8]
        else:
            b = m[14 - i][8]
        biz |= b << i
    maske = qr.FORMAT_M.index(biz)                                 # tabloda yoksa hata verir
    rez = qr._reserved(ver, n)
    bitler, yon, c, r = [], -1, n - 1, n - 1
    while c > 0:
        if c == 6:
            c -= 1
        for _ in range(n):
            for dc in (0, 1):
                x = c - dc
                if not rez[r][x]:
                    bitler.append(m[r][x] ^ (1 if qr._mask(maske, r, x) else 0))
            r += yon
            if r < 0 or r >= n:
                r = 0 if r < 0 else n - 1
                yon = -yon
                break
        c -= 2
    kod = [int("".join(str(b) for b in bitler[i:i + 8]), 2) for i in range(0, len(bitler) // 8 * 8, 8)]
    # serpiştirmeyi geri al
    _cap, ecn, g1, b1, g2, b2 = qr.VER[ver]
    boy = [b1] * g1 + [b2] * g2
    bloklar = [[] for _ in boy]
    i = 0
    for k in range(max(boy)):
        for b in range(len(boy)):
            if k < boy[b]:
                bloklar[b].append(kod[i]); i += 1
    veri = [x for b in bloklar for x in b]
    bb = "".join(bin(x)[2:].zfill(8) for x in veri)
    kip = int(bb[:4], 2)
    say = 8 if ver < 10 else 16
    uz = int(bb[4:4 + say], 2)
    gov = bb[4 + say:4 + say + uz * 8]
    return kip, bytes(int(gov[i:i + 8], 2) for i in range(0, len(gov), 8)).decode("utf-8")

for metin in ("https://onlinekaydet.com/menu/demo", "MERHABA", "A",
              "https://onlinekaydet.com/menu/guzellik-salonu-sisli-istanbul-2026",
              "Ürün: Çay 25 TL", "x" * 100):
    kip, geri = coz(qr.matrix(metin))
    ok(kip == 4, "bayt kipi kullanılmalı")
    ok(geri == metin, "geri okunamadı: %r → %r" % (metin, geri))

# ---- sürüm seçimi ve sınırlar
ok(len(qr.matrix("A")) == 21, "kısa metin sürüm 1 olmalı")
ok(len(qr.matrix("x" * 200)) == 57, "uzun metin sürüm 10'a çıkmalı: %d" % len(qr.matrix("x" * 200)))
try:
    qr.matrix("x" * 400)
    ok(False, "kapasite aşımında hata verilmeli")
except ValueError as e:
    ok("çok uzun" in str(e), "anlaşılır hata: %s" % e)
ok(qr.matrix("") == [] and qr.svg("") == "", "boş metin kod üretmemeli")

# ---- SVG
s = qr.svg("https://onlinekaydet.com/menu/demo", px=6)
ok(s.startswith("<svg") and 'shape-rendering="crispEdges"' in s, "baskıda keskin SVG")
ok('width="%d"' % ((29 + 8) * 6) in s, "sessiz alan payıyla ölçü: %s" % s[:90])
ok(s.count("<path") == 1 and "#fff" in s, "tek yol ve beyaz zemin")

# ---- QR menü ucu (panel tarafı)
import os as _os
_os.environ["BACKGROUND_JOBS"] = "0"
sys.path.insert(0, _os.path.dirname(__file__))
import boot  # noqa: E402
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient  # noqa: E402
with TestClient(boot.server.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Lokanta"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login",
                                             json={"email": j["email"], "password": j["password"]}).json()["token"]}
    r = c.get("/api/yp/qr", headers=H).json()
    ok(r["tables"] == 12 and len(r["items"]) == 12, "varsayılan 12 masa")
    ok(r["items"][0]["url"].startswith("https://") and "masa=1" in r["items"][0]["url"],
       "her masa kendi bağlantısına gider: %s" % r["items"][0]["url"])
    c.put("/api/yp/qr", headers=H, json={"tables": 3, "title": "Kahvaltı menüsü", "note": "Afiyet olsun"})
    r2 = c.get("/api/yp/qr", headers=H).json()
    ok(r2["tables"] == 3 and r2["title"] == "Kahvaltı menüsü", r2)
    ok(c.put("/api/yp/qr", headers=H, json={"tables": 9999}).status_code == 200
       and c.get("/api/yp/qr", headers=H).json()["tables"] == 200, "masa sayısı sınırlanmalı")
    c.put("/api/yp/qr", headers=H, json={"tables": 3, "title": "Kahvaltı menüsü"})
    p = c.post("/api/yp/qr/yazdir", headers=H, json={}).json()
    ok(p["n"] == 3 and p["html"].count("<svg") == 3, "her masa için bir kare: %s" % p["n"])
    ok("Masa 3" in p["html"] and "Kahvaltı menüsü" in p["html"], "kartta masa numarası ve başlık")
    ok("window.print" in p["html"], "yazdırmaya hazır")
    tek = c.post("/api/yp/qr/yazdir", headers=H, json={"tables": [2]}).json()
    ok(tek["n"] == 1 and "Masa 2" in tek["html"], "seçili masa basılabilmeli")
    # kartın içindeki kare gerçekten o masanın bağlantısını taşıyor mu?
    import re as _re
    sv = _re.search(r"<svg.*?</svg>", tek["html"], _re.S).group(0)
    yollar = _re.findall(r'd="([^"]+)"', sv)[0]
    ok(len(yollar) > 200, "kare çizilmiş olmalı")

print("OK %d geçti (yapı + Reed-Solomon + geri okuma + QR menü ucu)" % n_ok)
