"""Etiket tasarımı: kaydedilir, önizleme ve baskı aynı tasarımı kullanır, firma bilgisi/logo kendiliğinden gelir, ekran açılır."""
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
with TestClient(s.app) as c:
    d = c.post("/api/public/demo", json={"name": "Mehmet", "phone": "05321110099", "sector": "lokanta"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
    L = c.get("/api/yp/etiket", headers=H); t("etiket ayarları açılır", L.status_code == 200)
    j = L.json(); t("üç tür ve her birinde stiller", set(j["cfg"]) == {"fis", "etiket", "qr"} and len(j["stiller"]["etiket"]) == 5 and len(j["stiller"]["qr"]) == 5)
    r = c.put("/api/yp/etiket/qr", headers=H, json={"stil": "koyu", "renk": "#7c2d12", "boyut": "a4-6", "baslik": "Akşam menüsü", "masa": 4, "alt": "Wi-Fi: lezzet"}); t("QR tasarımı kaydedilir", r.status_code == 200 and r.json()["cfg"]["stil"] == "koyu")
    r = c.put("/api/yp/etiket/qr", headers=H, json={"renk": "kırmızı", "stil": "yok", "boyut": "z9"}); cfg = r.json()["cfg"]
    t("geçersiz renk/stil/boyut sessizce eskisine döner", cfg["renk"] == "#7c2d12" and cfg["stil"] == "koyu" and cfg["boyut"] == "a4-6")
    p = c.post("/api/yp/qr/yazdir", headers=H, json={}).json()
    t("QR baskısı kayıtlı tasarımı kullanır (4 masa, başlık, alt satır, koyu)", p["n"] == 4 and p["html"].count("<svg") == 4 and "Akşam menüsü" in p["html"] and "Wi-Fi: lezzet" in p["html"] and "var(--c)" in p["html"])
    pv = c.post("/api/yp/etiket/qr/onizleme", headers=H, json={"cfg": {"stil": "serit"}}).json()["html"]
    t("önizleme kaydetmeden taslağı gösterir ve yazdırmaz", "class='ust'" in pv and "window.print" not in pv)
    st = c.post("/api/yp/etiket/etiket/stiller", headers=H, json={}).json()["items"]
    t("her stilin küçük önizlemesi gelir", set(st) == {"klasik", "serit", "kalin", "minimal", "termal"} and all("Örnek Alıcı" in v for v in st.values()))
    r = c.put("/api/yp/etiket/etiket", headers=H, json={"stil": "serit", "boyut": "10x15", "logo": True, "alt": "Kırılacak eşya değildir"}); t("kargo etiketi kaydedilir", r.status_code == 200)
    r = c.put("/api/yp/etiket/fis", headers=H, json={"stil": "serit", "imza": False, "alt": "Teşekkürler"}); t("fiş tasarımı kaydedilir", r.status_code == 200)
    # sipariş oluştur, etiket ve fiş bas
    o = c.post("/api/yp/orders", headers=H, json={"customer": {"name": "Ece Tan", "phone": "05330001122", "address": "Kızılay", "city": "Ankara"}, "items": [{"name": "Köfte", "qty": 2, "price": 100}], "channel": "telefon"})
    t("sipariş açılır: %s" % o.text[:60], o.status_code in (200, 201))
    oid = o.json()["item"]["id"]
    e = c.post("/api/yp/orders/print", headers=H, json={"ids": [oid], "kind": "etiket"}); t("kargo etiketi baskısı", e.status_code == 200 and "Ece Tan" in e.json()["html"] and "100mm 150mm" in e.json()["html"])
    f = c.post("/api/yp/orders/print", headers=H, json={"ids": [oid], "kind": "kargo"}); fh = f.json()["html"]
    t("kargo şablonu: tasarım, alt yazı, imza kapalı", "Teşekkürler" in fh and "Teslim eden" not in fh and "--c:" in fh)
    f2 = c.post("/api/yp/orders/print", headers=H, json={"ids": [oid], "kind": "siparis"}); t("sipariş fişi de tasarımla", f2.status_code == 200 and "--c:" in f2.json()["html"])
    t("bilinmeyen tür 404", c.put("/api/yp/etiket/xx", headers=H, json={}).status_code == 404)
print("OK", ok, "FAIL", bad)
