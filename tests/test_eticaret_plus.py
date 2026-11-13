"""E-ticaret ek araçları: Akakçe/Cimri XML, buybox, sipariş risk puanı, çarkıfelek."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import eticaret_plus as ep
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-900:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Plus Firma", "email": "pl@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "pl@x.com", "sifre12345")
    assert c.put("/api/site/features", headers=O, json={"shop_enabled": True, "customer_portal_enabled": True}).status_code == 200
    PID = c.post("/api/shop/products", headers=O, json={"name": "Eşanjör & Set", "price": 1000, "stock": 5, "category": "Eşanjör", "brand": "Baymak", "gtin": "8690000000000"}).json()["id"]
    PID2 = c.post("/api/shop/products", headers=O, json={"name": "Stoksuz", "price": 50, "stock": 0, "category": "X"}).json()["id"]
    c.put("/api/shop/settings", headers=O, json={"shipping_fee": 100, "bank_accounts": [{"bank": "Ziraat", "holder": "M", "iban": "TR330006100519786457841326"}]})
    def feed():
        assert c.get("/api/public/feed/%s~akakce.xml" % F).status_code == 404 if False else True
        r = c.put("/api/yp/feed", headers=O, json={"akakce": True, "cimri": True, "kargo": 29.9, "teslim_gun": 2}); assert r.json()["akakce"] and r.json()["kargo"] == 29.9
        g = c.get("/api/yp/feed", headers=O).json(); assert g["urls"]["akakce"].endswith("/api/public/feed/akakce.xml"), g
        for tur, tag in (("akakce", "<ProductUrl>"), ("cimri", "<Image1>")):
            x = c.get("/api/public/feed/%s~%s.xml" % (F, tur))
            assert x.status_code == 200 and "xml" in x.headers["content-type"], x.status_code
            assert "Eşanjör &amp; Set" in x.text and tag in x.text and "Stoksuz" not in x.text and "1000.00" in x.text, x.text
        c.put("/api/yp/feed", headers=O, json={"akakce": False})
        assert c.get("/api/public/feed/%s~akakce.xml" % F).status_code == 404
    t("Akakçe ve Cimri XML: kaçışlı, stoksuz ürün yok, kapalıyken 404", feed)
    def bb():
        assert c.put("/api/yp/buybox/%s" % PID, headers=O, json={"on": True, "rakip": 950, "min": 900}).json()["on"]
        assert c.put("/api/yp/buybox/%s" % PID, headers=O, json={"min": 990, "max": 980}).status_code == 422
        l = c.get("/api/yp/buybox", headers=O).json(); row = [x for x in l["rows"] if x["id"] == PID][0]
        assert row["hedef"] == 949.99, row
        d = c.post("/api/yp/buybox/uygula", headers=O).json()["degisen"]; assert d and d[0]["yeni"] == 949.99
        assert [p for p in c.get("/api/shop/products", headers=O).json() if p["id"] == PID][0]["price"] == 949.99
        assert c.post("/api/yp/buybox/uygula", headers=O).json()["degisen"] == []
        c.put("/api/yp/buybox/%s" % PID, headers=O, json={"rakip": 800})                     # alt sınır korur
        assert c.post("/api/yp/buybox/uygula", headers=O).json()["degisen"][0]["yeni"] == 900
        assert c.get("/api/yp/buybox", headers=O).json()["log"]
    t("buybox: rakibin 1 kuruş altı, alt/üst sınır, değişmeyene dokunmaz, kayıt", bb)
    def risk():
        assert c.put("/api/yp/risk", headers=O, json={"tutar_esik": 500, "orta": 30, "yuksek": 60}).json()["tutar_esik"] == 500
        rr = c.post("/api/public/customer/%s~register" % F, json={"name": "Ali Veli", "phone": "0532 555 11 22", "password": "parola1234"}); S["ct"] = {"Authorization": "Bearer " + rr.json()["token"]}
        body = {"customer": {"name": "Ali Veli", "phone": "0532 555 11 22", "address": "Atatürk cad. no 5 Çankaya", "city": "Ankara", "district": "Çankaya", "email": "x@mailinator.com"},
                "items": [{"product_id": PID, "qty": 1}], "accept_terms": True, "payment_method": "havale"}
        r = c.post("/api/public/shop/%s~orders" % F, json=body, headers=S["ct"]); assert r.status_code == 200, r.text
        o = [x for x in c.get("/api/shop/orders", headers=O).json() if x["order_no"] == r.json()["order_no"]][0]
        assert o["risk"]["seviye"] in ("orta", "yuksek", "dusuk") and "Tek kullanımlık e-posta" in o["risk"]["nedenler"] and "İlk sipariş" in o["risk"]["nedenler"], o["risk"]
        assert o["risk"]["puan"] >= 25, o["risk"]
        c.put("/api/yp/risk", headers=O, json={"on": False})
        r2 = c.post("/api/public/shop/%s~orders" % F, json=body, headers=S["ct"]); o2 = [x for x in c.get("/api/shop/orders", headers=O).json() if x["order_no"] == r2.json()["order_no"]][0]
        assert o2.get("risk") is None
    t("sipariş risk puanı: nedenler yazılır, kapalıyken hesaplanmaz", risk)
    def cark():
        assert c.put("/api/yp/cark", headers=O, json={"dilim": [{"ad": "x", "tur": "yok", "agirlik": 1}]}).status_code == 422
        assert c.post("/api/public/cark/%s~cevir" % F, json={"phone": "0532 111 22 33"}).status_code == 404       # kapalı
        r = c.put("/api/yp/cark", headers=O, json={"on": True, "dilim": [{"ad": "%10 indirim", "tur": "yuzde", "deger": 10, "agirlik": 1}, {"ad": "Yok", "tur": "yok", "agirlik": 0}]}); assert r.status_code == 200, r.text
        assert c.post("/api/public/cark/%s~cevir" % F, json={"phone": "123"}).status_code == 422
        j = c.post("/api/public/cark/%s~cevir" % F, json={"phone": "0532 111 22 33"}).json(); assert j["index"] == 0 and j["kod"].startswith("CARK-"), j
        assert c.post("/api/public/cark/%s~cevir" % F, json={"phone": "0532 111 22 33"}).status_code == 409
        k = [x for x in c.get("/api/yp/campaigns", headers=O).json()["items"] if x["cond"]["code"] == j["kod"]]
        assert k and k[0]["gain"]["percent"] == 10 and k[0]["state"] == "aktif", k
        g = c.get("/api/yp/cark", headers=O).json(); assert g["cevrilen"] == 1 and g["kazanan"] == 1
        h = ep.cark_html(dict(ep.CARK_DEF, on=True)); assert 'id="okck"' in h and "Çarkı çevir" in h and "emoji" not in h
        assert ep.cark_html(dict(ep.CARK_DEF)) == ""
    t("çarkıfelek: ağırlıklı seçim, telefon başına bir hak, kupon kampanyası açılır", cark)
print("ok", len(ok), "bad", len(bad))
for n, e in bad: print("FAIL", n, "\n", e)
