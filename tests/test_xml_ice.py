"""XML ürün aktarma: analiz, eşleşme önerisi, içe aktarma (ekle/güncelle/pasif), para birimi, güvenlik."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import xml_ice as xi
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-900:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
FEED = {"v": """<?xml version="1.0" encoding="UTF-8"?><Products>
<Product><ProductCode>A-1</ProductCode><Barcode>8690001</Barcode><ProductName>Kombi Eşanjör</ProductName><Price>1.234,50</Price><Stock>7</Stock><Category>Yedek Parça</Category><Brand>Baymak</Brand><Image1>https://x.test/1.jpg</Image1><Image2>https://x.test/2.jpg</Image2><Description>Orijinal</Description><Currency>TRY</Currency></Product>
<Product><ProductCode>A-2</ProductCode><ProductName>Fan Motoru</ProductName><Price>10.5</Price><Stock>0</Stock><Category>Yedek Parça</Category><Currency>USD</Currency></Product>
<Product><ProductCode>A-3</ProductCode><ProductName>Oda Termostatı</ProductName><Price>200</Price><Stock>3</Stock><Category>Termostat</Category></Product>
</Products>"""}
xi.fetch_bytes = lambda url, timeout=40: FEED["v"].encode("utf-8")
xi.assert_public_url = lambda u: None
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Xml Firma", "email": "xm@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    O = tok(c, "xm@x.com", "sifre12345")
    assert c.put("/api/site/features", headers=O, json={"shop_enabled": True}).status_code == 200
    S = {}
    def sayi():
        for a, b in (("1.234,50", 1234.5), ("1234.56", 1234.56), ("1,234.56", 1234.56), ("12,5", 12.5), ("%20", 20.0), ("1.234", 1234.0), ("", 0.0), ("10.5", 10.5)):
            assert xi.parse_number(a) == b, (a, xi.parse_number(a))
    t("sayı biçimleri: TR/EN ondalık ve binlik", sayi)
    def analiz():
        r = c.post("/api/yp/xml/analiz", headers=O, json={"url": "https://x.test/f.xml"}); assert r.status_code == 200, r.text
        j = r.json(); assert j["item_path"] == "Products/Product" and j["count"] == 3, j
        m = j["mapping"]; assert m["name"] == "ProductName" and m["sku"] == "ProductCode" and m["barcode"] == "Barcode" and m["price"] == "Price" and m["stock"] == "Stock", m
        assert "Image1" in m["images"] and "Image2" in m["images"], m; S["m"] = m
    t("analiz: ürün düğümü ve eşleşme otomatik bulunur", analiz)
    def kaydet():
        bad_ = c.post("/api/yp/xml", headers=O, json={"name": "X", "url": "ftp://x"}); assert bad_.status_code == 422
        assert c.post("/api/yp/xml", headers=O, json={"name": "X", "url": "https://x.test/f.xml", "mapping": {"name": "ProductName"}}).status_code == 422
        r = c.post("/api/yp/xml", headers=O, json={"name": "Tedarikçi A", "url": "https://x.test/f.xml", "mapping": S["m"], "markup_percent": 20, "round_to": 5, "usd_rate": 40, "new_active": True, "deactivate_missing": True, "hide_out_of_stock": True})
        assert r.status_code == 200, r.text; S["id"] = r.json()["id"]
    t("kaynak kaydı: doğrulamalar ve oluşturma", kaydet)
    def calistir():
        r = c.post("/api/yp/xml/%s/calistir" % S["id"], headers=O); assert r.status_code == 200, r.text
        j = r.json(); assert j["eklenen"] == 3 and j["guncellenen"] == 0, j
        ps = {p["sku"]: p for p in c.get("/api/shop/products", headers=O).json()}
        assert ps["A-1"]["price"] == 1485.0 and ps["A-1"]["stock"] == 7 and ps["A-1"]["active"] and len(ps["A-1"]["images"]) == 2, ps["A-1"]   # 1234.5*1.2=1481.4 -> 5'e yuvarlanır
        assert ps["A-2"]["price"] == 505.0 and ps["A-2"]["active"] is False, ps["A-2"]      # 10.5 USD*40=420*1.2=504 -> 505; stok yok -> pasif
        assert ps["A-3"]["price"] == 240.0
    t("içe aktarma: ekler, kâr + yuvarlama, USD kuru, stoksuz pasif", calistir)
    def guncelle():
        FEED["v"] = FEED["v"].replace("<Stock>7</Stock>", "<Stock>2</Stock>").replace("<Price>200</Price>", "<Price>300</Price>")
        j = c.post("/api/yp/xml/%s/calistir" % S["id"], headers=O).json(); assert j["eklenen"] == 0 and j["guncellenen"] == 3, j
        ps = {p["sku"]: p for p in c.get("/api/shop/products", headers=O).json()}
        assert ps["A-1"]["stock"] == 2 and ps["A-3"]["price"] == 360.0, ps["A-3"]
        assert len(c.get("/api/shop/products", headers=O).json()) == 3, "çift kayıt oluşmamalı"
    t("tekrar çalıştırma: aynı stok koduna güncelleme, çift kayıt yok", guncelle)
    def eksik():
        FEED["v"] = FEED["v"].replace("<Product><ProductCode>A-3</ProductCode>", "<Product x='1'><ProductCode>A-9</ProductCode>").replace("A-9</ProductCode><ProductName>Oda Termostatı", "A-9</ProductCode><ProductName>Yeni Ürün")
        j = c.post("/api/yp/xml/%s/calistir" % S["id"], headers=O).json(); assert j["eklenen"] == 1 and j["pasif_yapilan"] == 1, j
        ps = {p["sku"]: p for p in c.get("/api/shop/products", headers=O).json()}
        assert ps["A-3"]["active"] is False and ps["A-9"]["name"] == "Yeni Ürün"
    t("feedde olmayan ürün pasif, yeni ürün eklenir", eksik)
    def guvenlik():
        FEED["v"] = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "bomba">]><Products><Product><ProductCode>1</ProductCode><ProductName>&a;</ProductName><Price>1</Price></Product></Products>'
        r = c.post("/api/yp/xml/analiz", headers=O, json={"url": "https://x.test/f.xml"}); assert r.status_code == 422 and "DOCTYPE" in r.text, r.text
        FEED["v"] = "<a><b>"
        assert c.post("/api/yp/xml/analiz", headers=O, json={"url": "https://x.test/f.xml"}).status_code == 422
        from fastapi import HTTPException
        import importlib; real = importlib.reload(xi)
        for u in ("http://127.0.0.1/x.xml", "http://169.254.169.254/latest", "http://10.0.0.5/f.xml", "file:///etc/passwd", "http://localhost/f"):
            try: real.assert_public_url(u); assert False, u
            except HTTPException: pass
    t("güvenlik: DOCTYPE/ENTITY, bozuk XML, yerel/özel adres ve şema engeli", guvenlik)
    def liste_sil():
        l = c.get("/api/yp/xml", headers=O).json(); assert l["sources"][0]["product_count"] == 4 and l["sources"][0]["last_result"], l
        assert c.delete("/api/yp/xml/%s" % S["id"], headers=O).json()["ok"]
        assert len(c.get("/api/shop/products", headers=O).json()) == 4
    t("liste, son sonuç ve silme (ürünler kalır)", liste_sil)
print("GEÇTİ", len(ok)); [print("BAŞARISIZ", n, e) for n, e in bad]
sys.exit(1 if bad else 0)
