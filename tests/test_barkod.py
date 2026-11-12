"""Code 128 barkod: kodlama, sağlama ve fişe basılan barkodun doğruluğu."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import barkod
from siparis import fis_html, sevk_kodu

n = 0
def ok(c, m):
    global n
    assert c, m
    n += 1

# 1) desen tablosu eksiksiz
ok(len(barkod.P) == 107, "Code 128'de 107 desen olmalı: %d" % len(barkod.P))
ok(all(len(p) == 6 for p in barkod.P[:-1]) and len(barkod.P[-1]) == 7, "desen genişlikleri bozuk")

# 2) bilinen örnek: 123456 C kümesiyle, sağlama 44
ok(barkod.values("123456") == [105, 12, 34, 56, 44, 106], "123456 kodlaması: %s" % barkod.values("123456"))

# 3) harf içeren metin B kümesine düşer ve sağlama doğrudur
v = barkod.values("SP-2026-00412")
ok(v[0] == 104 and v[-1] == 106, "B kümesi başlangıç/dur simgesi")
chk = v[0] + sum(i * x for i, x in enumerate(v[1:-2], start=1))
ok(chk % 103 == v[-2], "sağlama hatalı: %d != %d" % (chk % 103, v[-2]))
ok(v[1] == ord("S") - 32, "B kümesinde değer = ASCII - 32")

# 4) tek haneli ve boş girdiler
ok(barkod.values("") == [], "boş metin barkod üretmemeli")
ok(barkod.svg("") == "", "boş metinde SVG boş dönmeli")
ok(barkod.values("12345")[0] == 104, "tek sayıda hane B kümesine düşer")

# 5) SVG çizimi: çubuk sayısı ve ölçü
s = barkod.svg("1234", height=50, module=2)
ok(s.startswith("<svg") and s.endswith("</svg>"), "geçerli SVG")
ok('height="64"' in s, "etiket için 14px pay eklenmeli: %s" % s[:120])
ok(s.count("<rect") > 10, "çubuklar çizilmeli")
ok('height="50"' in s, "çubuk yüksekliği")
ok("1234" in s, "barkod altına metin yazılmalı")
ok('<rect x="4.00"' in s, "sol kenar boşluğu bırakılmalı")

# 6) özel karakterler SVG'yi bozmamalı
ok("&amp;" in barkod.svg('A&B"'), "metin kaçışlanmalı")

# 7) fişte basılacak kod sırası: gönderi barkodu > takip no > sipariş no
O = {"no": "SP-2026-00412", "cargo": {}}
ok(sevk_kodu(O) == "SP-2026-00412", "barkod yoksa sipariş no basılır")
O["cargo"] = {"code": "7291043821"}
ok(sevk_kodu(O) == "7291043821", "takip no varsa o basılır")
O["cargo"]["barcode"] = "TY1234567890"
ok(sevk_kodu(O) == "TY1234567890", "pazaryeri gönderi barkodu önceliklidir")

# 8) kargo fişinde barkod ve pazaryeri sipariş numarası
o = {"no": "SP-2026-00412", "at": "2026-11-12T09:14", "market_no": "TY-998877",
     "channel": "trendyol", "channel_name": "Trendyol", "paid": True, "total": 1284.0,
     "customer": {"name": "Mehmet Yıldız", "phone": "05321112233", "address": "Moda Cad. 14", "city": "İstanbul"},
     "cargo": {"firm": "aras", "code": "7291043821", "barcode": "TY1234567890"},
     "items": [{"name": "Keten Gömlek", "sku": "GML-402", "barcode": "8680001112223", "qty": 2, "price": 899.0}],
     "subtotal": 1798.0, "ship_fee": 0, "free_ship": True, "camps": []}
h = fis_html([o], "kargo", "Demo Mağaza")
ok("Gönderi barkodu" in h, "barkodun ne olduğu yazmalı")
ok(h.count("<svg") == 2, "kargo fişinde sevk + pazaryeri barkodu: %d" % h.count("<svg"))
ok("TY-998877" in h and "Trendyol sipariş numarası" in h, "pazaryeri sipariş numarası basılmalı")
ok("0532 111 22 33" in h, "telefon okunur biçimde")

# 9) sipariş fişinde ürün barkodları
h2 = fis_html([o], "siparis", "Demo Mağaza")
ok(h2.count("<svg") == 2, "sipariş fişinde sevk + ürün barkodu: %d" % h2.count("<svg"))
ok("8680001112223" in h2, "ürünün kendi barkodu satırda basılmalı")
ok("Genel toplam" in h2 and "Gönderi barkodu" not in h2, "sipariş fişi kargo kutusu taşımaz")

# 10) barkodsuz ürün satırı barkod çizdirmez
o2 = dict(o, items=[{"name": "Çorap", "qty": 1, "price": 149.0}], cargo={}, market_no="")
ok(fis_html([o2], "siparis", "X").count("<svg") == 1, "barkodsuz üründe yalnız sipariş barkodu olur")

# ---------------------------------------------------------------- okuyucu benzetimi
# Çizilen SVG'yi geri çözüyoruz: bir tarayıcı barkodu nasıl okursa öyle — çubuk ve
# boşluk genişliklerini ölçüp desenle eşleştirerek. Böylece "çubuk çizildi" değil,
# "okunuyor" doğrulanmış oluyor.
import re as _re

def oku(svg_text):
    w = float(_re.search(r'viewBox="0 0 ([\d.]+)', svg_text).group(1))
    rects = [(float(a), float(b)) for a, b in _re.findall(r'<rect x="([\d.]+)" y="0" width="([\d.]+)"', svg_text)]
    assert rects, "çubuk yok"
    mod = min(b for _, b in rects)                       # en ince çubuk = 1 modül
    runs, x = [], rects[0][0]
    for rx, rw in rects:
        if rx > x + mod / 2:                             # araya giren boşluk
            runs.append(round((rx - x) / mod))
        runs.append(round(rw / mod))
        x = rx + rw
    vals, i = [], 0
    while i + 6 <= len(runs):
        pat = "".join(str(v) for v in runs[i:i + 6])
        if pat == "233111" and i + 7 <= len(runs):       # dur simgesi 7 çubuk
            vals.append(106); break
        vals.append(barkod.P.index(pat)); i += 6
    return vals

def metin(vals):
    assert vals[-1] == 106, "dur simgesi yok"
    chk = vals[0] + sum(i * v for i, v in enumerate(vals[1:-2], start=1))
    assert chk % 103 == vals[-2], "sağlama tutmuyor"
    if vals[0] == 105:
        return "".join("%02d" % v for v in vals[1:-2])
    return "".join(chr(v + 32) for v in vals[1:-2])

for t_ in ("TY1234567890", "SP-2026-00412", "8680001112223", "1234", "A&B"):
    ok(metin(oku(barkod.svg(t_))) == t_, "okuyucu '%s' barkodunu geri okuyamadı" % t_)

# fişteki barkodlar da okunabilir olmalı
h3 = fis_html([o], "kargo", "Demo")
svgs = _re.findall(r"<svg.*?</svg>", h3, _re.S)
ok(metin(oku(svgs[0])) == "TY1234567890", "kargo fişindeki sevk barkodu okunmalı")
ok(metin(oku(svgs[1])) == "TY-998877", "pazaryeri sipariş barkodu okunmalı")
svgs2 = _re.findall(r"<svg.*?</svg>", fis_html([o], "siparis", "Demo"), _re.S)
ok(metin(oku(svgs2[1])) == "8680001112223", "ürün barkodu okunmalı")

print("OK %d geçti (okuyucu benzetimi dâhil)" % n)
