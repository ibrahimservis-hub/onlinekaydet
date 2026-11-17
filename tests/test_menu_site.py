"""Restoran Menü ekranındaki yemekler sitede (menü kartı / QR menü) görünür; pasif ve taslak olanlar görünmez; e-ticarette menü bölümü beslenmez."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
import demo
demo.GUNLUK_LIMIT = 10 ** 6
s = boot.server; ok = bad = 0
def t(n, c):
    global ok, bad
    ok += bool(c); bad += (not c); print(("  ✓ " if c else "  ✗ ") + n)
def yemek(ad, fiyat, bolum, **k):
    d = {"name": ad, "price": fiyat, "vat": 10, "channels": {"site": True}, "food": {"bolum": bolum, "aktif": k.pop("aktif", True)}}; d.update(k); return d
with TestClient(s.app) as c:
    d = c.post("/api/public/demo", json={"name": "Mehmet", "phone": "05321110055", "sector": "lokanta"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
    for x in (yemek("Zeytinyağlı Yaprak Sarma", 120, "Mezeler", short="Taze asma yaprağıyla"), yemek("Pasif Yemek Zz", 99, "Mezeler", aktif=False), yemek("Taslak Yemek Zz", 99, "Mezeler", status="draft")):
        r = c.post("/api/yp/products", headers=H, json=x); assert r.status_code in (200, 201), r.text
    home = c.post("/api/yp/tema-ek", headers=H).json()["pid"]
    for bid in ("menu_karti", "qr_menu"):
        r = c.post("/api/yp/pages/%s/blocks" % home, headers=H, json={"bid": bid}); assert r.status_code == 200, r.text
    pv = ""
    for path in ("/", "/menu", "/menu.html"):
        pv += c.get("/api/site/preview?path=" + path, headers=H).text
    t("yemek sitede görünür (menü kartı ya da QR menü)", "Zeytinyağlı Yaprak Sarma" in pv)
    t("kategori başlığı (menü bölümü) görünür", "Mezeler" in pv)
    t("pasif ve taslak yemek görünmez", "Pasif Yemek Zz" not in pv and "Taslak Yemek Zz" not in pv)
print("OK", ok, "FAIL", bad)
