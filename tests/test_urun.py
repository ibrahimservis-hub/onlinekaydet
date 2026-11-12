"""E-ticaret ürün modülü: hızlı ekleme (link ayrıştırma), kârlılık, varyant, filtre ve toplu işlem."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import urun
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-700:]))

PAGE = '''<html><head><title>Keten Gömlek · Oversize | Nevermore</title>
<meta property="og:image" content="//cdn.x.com/a.jpg">
<meta property="og:description" content="Yumuşak dokulu keten gömlek">
<script type="application/ld+json">{"@type":"Product","name":"Keten Gömlek Oversize","sku":"KG-38",
"brand":{"name":"Nevermore"},"image":["https://cdn.x.com/b.jpg","/rel.jpg"],
"additionalProperty":[{"name":"Kumaş","value":"%100 keten"}],"offers":{"price":"899.00"}}</script>
</head><body><img src="/c.png"></body></html>'''

with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    def a():
        r = urun.profit(1200, 700, 20, 18)
        assert r["base"] == 1000.0 and r["vat"] == 200.0 and r["commission"] == 216.0
        assert r["net"] == 84.0 and r["margin"] == 7.0, r
        assert urun.profit(629, 420, 20, 18)["net"] < 0, "zararına satış görülmeli"
        assert urun.profit(0, 100)["margin"] == 0.0
        assert urun.profit("1.299,90", "800", 10, 0)["base"] == 1181.73
    t("kârlılık: KDV matrahı, kanal komisyonu, zararına satış ve Türkçe sayı biçimi", a)
    def b():
        d = urun.parse_product(PAGE, "https://shop.example.com/urun/1")
        assert d["name"] == "Keten Gömlek Oversize" and d["brand"] == "Nevermore" and d["sku"] == "KG-38"
        assert d["price"] == 899.0 and d["desc"].startswith("Yumuşak")
        assert d["images"][0] == "https://cdn.x.com/b.jpg", "JSON-LD görseli önce gelmeli"
        assert "https://shop.example.com/rel.jpg" in d["images"], "göreli adres tam adrese çevrilmeli"
        assert "https://cdn.x.com/a.jpg" in d["images"], "// ile başlayan adres düzeltilmeli"
        assert d["specs"] == [{"k": "Kumaş", "v": "%100 keten"}]
        assert set(d["found"]) >= {"name", "brand", "sku", "images", "specs"}
        d2 = urun.parse_product('<html><head><title>Sade Sayfa</title></head></html>')
        assert d2["name"] == "Sade Sayfa" and d2["images"] == []
    t("hızlı ekleme: JSON-LD + OpenGraph'tan ad, marka, stok kodu, görsel ve özellik çıkarma", b)
    def d():
        r = c.post("/api/yp/products/parse", headers=H, json={"html": PAGE, "url": "https://shop.example.com/urun/1"})
        assert r.status_code == 200 and r.json()["name"] == "Keten Gömlek Oversize"
        assert c.post("/api/yp/products/parse", headers=H, json={"url": "merhaba"}).status_code == 422
        assert c.post("/api/yp/products/parse", headers=H, json={"html": "<html></html>"}).status_code == 422
    t("parse ucu: geçersiz bağlantı ve boş sayfa anlaşılır hata veriyor", d)
    def e():
        p = {"name": "Keten Gömlek Oversize", "sku": "KG-38", "brand": "Nevermore", "cat": "Gömlek",
             "cost": 420, "price": 899, "sale_price": 629, "vat": 20, "stock": 24,
             "images": ["https://cdn.x.com/b.jpg"], "channels": {"trendyol": True, "yok": True},
             "specs": [{"k": "Kumaş", "v": "%100 keten"}]}
        r = c.post("/api/yp/products", headers=H, json=p); assert r.status_code == 200, r.text
        v = r.json(); S["p1"] = v["id"]
        assert v["slug"] == "keten-gomlek-oversize" and v["discount"] == 30
        assert v["channels"]["site"] is True and "yok" not in v["channels"], "tanınmayan kanal atılmalı"
        assert v["margin"] == urun.profit(629, 420, 20, 0)["margin"]
        assert c.post("/api/yp/products", headers=H, json=dict(p, sku="X")).status_code == 200
        assert c.post("/api/yp/products", headers=H, json=dict(p, sku="KG-38")).status_code == 422, "aynı stok kodu"
        assert c.post("/api/yp/products", headers=H, json={"name": "", "price": 10}).status_code == 422
        assert c.post("/api/yp/products", headers=H, json={"name": "A", "price": 0}).status_code == 422
        assert c.post("/api/yp/products", headers=H, json={"name": "A", "price": 100, "sale_price": 200}).status_code == 422
    t("ürün ekleme: doğrulama, indirim oranı, kanal süzme, stok kodu tekilliği", e)
    def f():
        r = c.put("/api/yp/products/" + S["p1"], headers=H, json={"variants": [
            {"opts": {"Beden": "38", "Renk": "Bej"}, "stock": 5, "sku": "KG-38-BEJ"},
            {"opts": {"Beden": "40", "Renk": "Bej"}, "stock": 7},
            {"opts": {}, "stock": 99}]}).json()
        assert len(r["variants"]) == 2 and r["stock"] == 12, "stok varyantlardan toplanmalı"
        assert r["variants"][0]["id"] and r["variants"][0]["sku"] == "KG-38-BEJ"
    t("varyant: seçeneksiz satır atılıyor, stok varyantlardan toplanıyor", f)
    def g():
        r = c.post("/api/yp/products/%s/profit" % S["p1"], headers=H,
                   json={"channels": ["site", "trendyol", "hepsiburada"]}).json()["rows"]
        assert [x["channel"] for x in r] == ["site", "trendyol", "hepsiburada"]
        assert r[0]["net"] > r[1]["net"] > 0 or r[1]["net"] < r[0]["net"], "komisyon kârı düşürmeli"
        assert r[1]["commission_rate"] == 18.0 and r[1]["commission"] == round(629 * 0.18, 2)
        one = c.get("/api/yp/products/" + S["p1"], headers=H).json()
        assert one["channel_profit"] and one["profit"]["base"] > 0
    t("kanal bazlı kâr: komisyon oranları uygulanıyor", g)
    def h():
        for i, (n, st, pr, cost, cat) in enumerate([("Yün Kazak", 8, 1249, 700, "Kazak"), ("Deri Çanta", 3, 2199, 1500, "Çanta"),
                                                     ("Spor Ayakkabı", 0, 1899, 1400, "Ayakkabı"), ("Tişört", 142, 449, 180, "Tişört")]):
            c.post("/api/yp/products", headers=H, json={"name": n, "price": pr, "cost": cost, "stock": st, "cat": cat, "sku": "S%d" % i})
        r = c.get("/api/yp/products", headers=H).json()
        assert r["total"] == 6 and r["sum"]["n"] == 6
        assert r["counts"]["tukendi"] == 1 and r["counts"]["az_stok"] >= 1
        assert c.get("/api/yp/products", headers=H, params={"q": "kg-38"}).json()["total"] == 1, "stok koduyla arama"
        assert c.get("/api/yp/products", headers=H, params={"q": "nevermore"}).json()["total"] == 2, "markayla arama"
        assert c.get("/api/yp/products", headers=H, params={"cat": "Çanta"}).json()["total"] == 1
        assert c.get("/api/yp/products", headers=H, params={"seg": "tukendi"}).json()["rows"][0]["name"] == "Spor Ayakkabı"
        assert c.get("/api/yp/products", headers=H, params={"channel": "trendyol"}).json()["total"] == 2
        names = [x["name"] for x in c.get("/api/yp/products", headers=H, params={"sort": "fiyat"}).json()["rows"]]
        assert names[0] == "Tişört", names
        fl = c.get("/api/yp/products/filters", headers=H).json()
        assert {"name": "Gömlek", "n": 2} in fl["cats"] and {"name": "Nevermore", "n": 2} in fl["brands"]
    t("ürün listesi: arama, kategori/kanal/bölüm süzgeci, sıralama, filtre kaynakları", h)
    def i():
        ids = [x["id"] for x in c.get("/api/yp/products", headers=H, params={"cat": "Gömlek"}).json()["rows"]]
        assert c.post("/api/yp/products/bulk", headers=H, json={"op": "price", "ids": ids, "percent": 10}).json()["n"] == 2
        p = c.get("/api/yp/products/" + S["p1"], headers=H).json()
        assert p["price"] == 988.9 and p["sale_price"] == 691.9, p["price"]
        assert c.post("/api/yp/products/bulk", headers=H, json={"op": "channel", "ids": ids, "channel": "n11", "on": True}).json()["n"] == 2
        assert c.get("/api/yp/products", headers=H, params={"channel": "n11"}).json()["total"] == 2
        assert c.post("/api/yp/products/bulk", headers=H, json={"op": "stock", "ids": ids, "add": -100}).json()["n"] == 2
        assert c.get("/api/yp/products/" + S["p1"], headers=H).json()["stock"] == 0, "stok eksiye düşmemeli"
        assert c.post("/api/yp/products/bulk", headers=H, json={"op": "price", "ids": ids}).status_code == 422
        assert c.post("/api/yp/products/bulk", headers=H, json={"op": "yok", "ids": ids}).status_code == 422
    t("toplu işlem: yüzdeyle fiyat, kanal açma, stok ekleme (eksiye düşmez), hatalı istek reddi", i)
print("OK" if not bad else "FAIL", len(ok), "geçti")
for n, e in bad: print("✗", n, "\n", e)
sys.exit(1 if bad else 0)
