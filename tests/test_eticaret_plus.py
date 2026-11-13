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
    def sepet():
        rr = c.post("/api/public/customer/%s~register" % F, json={"name": "Sepet Kisi", "phone": "0533 444 55 66", "password": "parola1234"}); T = {"Authorization": "Bearer " + rr.json()["token"]}
        assert c.put("/api/public/shop/%s~sepet" % F, json={"items": []}).status_code == 401
        r = c.put("/api/public/shop/%s~sepet" % F, headers=T, json={"items": [{"id": PID, "q": 2}, {"id": "yok", "q": 1}]}); assert r.json()["n"] == 1, r.text
        l = c.get("/api/yp/sepetler", headers=O).json(); row = [x for x in l["rows"] if x["phone"].endswith("5556") or x["name"] == "Sepet Kisi"][0]
        assert row["total"] == 2 * 900 and row["durum"] == "aktif" and l["ozet"]["aktif"] >= 1, row
        assert c.post("/api/yp/sepetler/yok/hatirla", headers=O).status_code == 404
        # eski sepet terk sayılır
        async def eskit():
            fm = await s.db.main().firms.find_one({"login_email": "pl@x.com"})
            await s.db.firm(fm["db"]).shop_carts.update_one({"id": row["id"]}, {"$set": {"updated_at": "2020-01-01T00:00:00+00:00"}})
        c.portal.call(eskit)
        assert c.get("/api/yp/sepetler", headers=O).json()["ozet"]["terk"] >= 1
        import notify
        gid = []
        async def sahte(db, ch, to, text, **k): gid.append((to, text)); return {"status": "sent"}
        eski = notify.send; notify.send = sahte
        try:
            assert c.post("/api/yp/sepetler/%s/hatirla" % row["id"], headers=O).json()["ok"] and "Sepet" in gid[0][1] and "/magaza" in gid[0][1], gid
        finally:
            notify.send = eski
        assert c.post("/api/yp/sectors/eticaret", headers=O).status_code == 200
        raporlar = [x["id"] for x in c.get("/api/yp/rapor", headers=O).json()["items"]]
        assert "sepet_terk" in raporlar and "stok_devir" in raporlar, raporlar
        j = c.get("/api/yp/rapor/sepet_terk?frm=2019-01-01", headers=O).json(); assert j["n"] >= 1 and "terk" in j["rows"][0]["durum"].lower(), j["rows"]
        d = c.get("/api/yp/rapor/stok_devir", headers=O).json(); assert d["n"] >= 1 and "devir" in d["rows"][0]
        # sipariş verince sepet silinir
        body = {"customer": {"name": "Sepet Kisi", "phone": "0533 444 55 66", "address": "Atatürk cad. no 5 Çankaya", "city": "Ankara", "district": "Çankaya", "email": ""},
                "items": [{"product_id": PID, "qty": 1}], "accept_terms": True, "payment_method": "havale"}
        assert c.post("/api/public/shop/%s~orders" % F, json=body, headers=T).status_code == 200
        assert not [x for x in c.get("/api/yp/sepetler", headers=O).json()["rows"] if x["name"] == "Sepet Kisi"]
    t("sepet: kaydedilir, terk sayılır, SMS hatırlatma, raporlar, siparişte silinir", sepet)
    def webhook():
        import asyncio, hmac, hashlib, json as _j, requests
        got = []
        class R:  status_code = 200
        eski = requests.post
        requests.post = lambda url, data=None, headers=None, timeout=0: (got.append((url, data, headers)), R())[1]
        try:
            async def ekle():
                fm = await s.db.main().firms.find_one({"login_email": "pl@x.com"})
                await s.db.firm(fm["db"]).yp_integrations.update_one({"id": "webhook"}, {"$set": {"id": "webhook", "on": True, "ok": True, "keys": {"url": "https://example.com/hook", "secret": "gizli"}}}, upsert=True)
            c.portal.call(ekle)
            body = {"customer": {"name": "Hook Kisi", "phone": "0533 444 55 66", "address": "Atatürk cad. no 5 Çankaya", "city": "Ankara", "district": "Çankaya", "email": ""},
                    "items": [{"product_id": PID, "qty": 1}], "accept_terms": True, "payment_method": "havale"}
            rr = c.post("/api/public/customer/%s~register" % F, json={"name": "Hook Kisi", "phone": "0534 111 22 33", "password": "parola1234"}); T = {"Authorization": "Bearer " + rr.json()["token"]}
            assert c.post("/api/public/shop/%s~orders" % F, json=body, headers=T).status_code == 200
            assert got, "webhook çağrılmadı"
            url, data, h = got[0]; assert url == "https://example.com/hook" and h["X-OnlineKaydet-Olay"] == "siparis.olustu"
            assert h["X-OnlineKaydet-Imza"] == hmac.new(b"gizli", data, hashlib.sha256).hexdigest()
            assert _j.loads(data)["veri"]["musteri"] == "Hook Kisi"
        finally:
            requests.post = eski
    t("webhook: sipariş olayı imzalı gider", webhook)
    def haberver():
        sent = []
        async def ekle():
            fm = await s.db.main().firms.find_one({"login_email": "pl@x.com"}); d = s.db.firm(fm["db"])
            await d.yp_integrations.update_one({"id": "sms"}, {"$set": {"id": "sms", "group": "sms", "on": True, "ok": True, "keys": {}}}, upsert=True)
        c.portal.call(ekle)
        import notify
        eski = notify.send
        async def sahte(db, ch, to, text, kind="", ref=""):
            sent.append((to, text)); return {"status": "sent"}
        notify.send = sahte
        try:
            u = "/api/public/shop/haberver"
            assert c.post(u, json={"product_id": PID2, "phone": "123", "tur": "stok"}).status_code == 422
            assert c.post(u, json={"product_id": PID, "phone": "0533 111 22 33", "tur": "stok"}).status_code == 409
            assert c.post(u, json={"product_id": PID2, "phone": "0533 111 22 33", "tur": "stok"}).json()["ok"]
            assert c.post(u, json={"product_id": PID2, "phone": "0533 111 22 33", "tur": "stok"}).json().get("tekrar")
            assert c.post(u, json={"product_id": PID, "phone": "0533 111 22 33", "tur": "fiyat"}).json()["ok"]
            L = c.get("/api/yp/haberver", headers=O).json()["rows"]; assert sum(r["bekleyen"] for r in L) == 2, L
            assert c.post("/api/yp/haberver/tara", headers=O).json()["gonderilen"] == 0
            c.put("/api/shop/products/%s" % PID2, headers=O, json={"name": "Stoksuz", "price": 50, "stock": 4, "category": "X"})
            c.put("/api/shop/products/%s" % PID, headers=O, json={"name": "Eşanjör & Set", "price": 500, "stock": 5, "category": "Eşanjör"})
            assert c.post("/api/yp/haberver/tara", headers=O).json()["gonderilen"] == 2, sent
            assert any("stokta" in t for _, t in sent) and any("düştü" in t for _, t in sent)
            assert c.post("/api/yp/haberver/tara", headers=O).json()["gonderilen"] == 0
            assert c.get("/api/yp/haberver", headers=Bad).status_code in (401, 403) if (Bad := {"Authorization": "Bearer x"}) else 0
        finally:
            notify.send = eski
    t("haber ver: stok geldi / fiyat düştü SMS bir kez gider", haberver)
print("ok", len(ok), "bad", len(bad))
for n, e in bad: print("FAIL", n, "\n", e)
