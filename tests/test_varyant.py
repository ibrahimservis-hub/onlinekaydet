"""Varyant (renk/beden): kayıt ve tekillik, panel siparişinde seçenekten stok düşümü/iade, mağaza vitrini ve siparişi, pazaryeri siparişi."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad, S = [], [], {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-1100:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Varyant Firma", "email": "vf@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "vf@x.com", "sifre12345")
    c.put("/api/site/features", headers=O, json={"shop_enabled": True, "customer_portal_enabled": True})
    c.put("/api/shop/settings", headers=O, json={"shipping_fee": 0, "bank_accounts": [{"bank": "Ziraat", "holder": "M", "iban": "TR330006100519786457841326"}]})
    G = lambda pid: (lambda r: r.get("item") or r)(c.get("/api/yp/products/" + pid, headers=O).json())
    def shopdoc(pid): return c.get("/api/public/shop/%s~products" % F)
    def a():
        r = c.post("/api/yp/products", headers=O, json={"name": "Keten Gömlek", "price": 900, "cost": 400, "sku": "KG", "variants": [
            {"opts": {"Renk": "Beyaz", "Beden": "M"}, "stock": 5, "sku": "KG-B-M", "barcode": "8690000000014"},
            {"opts": {"Renk": "Beyaz", "Beden": "L"}, "stock": 2, "sku": "KG-B-L", "price": 950},
            {"opts": {"Renk": "Mavi", "Beden": "M"}, "stock": 0, "sku": "KG-M-M", "sale_price": 800, "price": 900}]})
        assert r.status_code == 200, r.text
        p = r.json(); S["p"] = p["id"]; S["v"] = {v["sku"]: v["id"] for v in p["variants"]}
        assert p["stock"] == 7 and [a["ad"] for a in p["var_axes"]] == ["Renk", "Beden"], p
        assert set(p["var_axes"][0]["degerler"]) == {"Beyaz", "Mavi"}
        bad1 = c.post("/api/yp/products", headers=O, json={"name": "X", "price": 10, "variants": [{"opts": {"Beden": "M"}, "sku": "A"}, {"opts": {"Beden": "L"}, "sku": "A"}]})
        assert bad1.status_code == 422, "aynı stok kodu iki seçenekte olamaz"
        bad2 = c.post("/api/yp/products", headers=O, json={"name": "X", "price": 10, "variants": [{"opts": {"Beden": "M"}}, {"opts": {"Beden": "M"}}]})
        assert bad2.status_code == 422, "aynı seçenek iki kez olamaz"
    t("varyantlı ürün: eksenler, toplam stok, tekillik", a)
    def b():
        d = c.get("/api/yp/products?q=KG", headers=O).json()["rows"][0]
        assert d["variant_count"] == 3
        sd = c.get("/api/shop/products", headers=O).json()
        row = [x for x in (sd if isinstance(sd, list) else sd.get("items") or sd.get("rows") or []) if x["id"] == S["p"]][0]
        assert len(row["variants"]) == 3 and {v["sku"] for v in row["variants"]} == set(S["v"])
        pr = {v["sku"]: v for v in row["variants"]}
        assert pr["KG-B-L"]["price"] == 950 and pr["KG-M-M"]["price"] == 800 and pr["KG-M-M"]["old_price"] == 900 and pr["KG-B-M"]["price"] == 900
    t("mağaza aynası: seçenek fiyatları (özel fiyat, indirim)", b)
    def d():
        o = lambda items, **k: c.post("/api/yp/orders", headers=O, json=dict({"channel": "telefon", "customer": {"name": "Ali", "phone": "0532 111 22 33"}, "items": items}, **k))
        it = lambda sku, q: {"product": S["p"], "name": "Keten Gömlek", "price": 900, "qty": q, "variant_id": S["v"][sku], "variant": sku}
        assert o([{"product": S["p"], "name": "Keten Gömlek", "price": 900, "qty": 1}]).status_code == 409, "seçenek seçilmeden sipariş olmaz"
        r = o([it("KG-B-M", 2)]); assert r.status_code == 200, r.text
        p = G(S["p"]); v = {x["sku"]: x for x in p["variants"]}
        assert v["KG-B-M"]["stock"] == 3 and p["stock"] == 5, (v["KG-B-M"]["stock"], p["stock"])
        r2 = o([it("KG-B-M", 1), it("KG-B-L", 9)]); assert r2.status_code == 409, "yetersiz stok"
        p = G(S["p"]); assert {x["sku"]: x["stock"] for x in p["variants"]}["KG-B-M"] == 3 and p["stock"] == 5, "başarısız siparişte stok geri alınmalı"
        S["o"] = r.json()["item"]["id"]
        r3 = c.post("/api/yp/orders/%s/status" % S["o"], headers=O, json={"status": "iptal"})
        if r3.status_code >= 400: r3 = c.put("/api/yp/orders/%s" % S["o"], headers=O, json={"status": "iptal"})
        assert r3.status_code == 200, r3.text
        p = G(S["p"]); assert {x["sku"]: x["stock"] for x in p["variants"]}["KG-B-M"] == 5 and p["stock"] == 7, "iptalde seçeneğe iade"
    t("panel siparişi: seçenekten düşer, yetersizde hiç düşmez, iptalde döner", d)
    def e():
        rr = c.post(f"/api/public/customer/{F}~register", json={"name": "Ali Veli", "phone": "0532 555 11 22", "password": "parola1234"}); assert rr.status_code in (200, 201), rr.text
        H = {"Authorization": "Bearer " + rr.json()["token"]}
        body = lambda items: {"customer": {"name": "Ali Veli", "phone": "0532 555 11 22", "address": "Atatürk cad. no 5 Çankaya", "city": "Ankara", "district": "Çankaya"},
                              "items": items, "accept_terms": True, "payment_method": "havale"}
        P = f"/api/public/shop/{F}~orders"
        assert c.post(P, json=body([{"product_id": S["p"], "qty": 1}]), headers=H).status_code == 422, "seçenek seçilmeli"
        assert c.post(P, json=body([{"product_id": S["p"], "qty": 1, "variant_id": S["v"]["KG-M-M"]}]), headers=H).status_code == 422, "stoksuz seçenek"
        r = c.post(P, json=body([{"product_id": S["p"], "qty": 2, "variant_id": S["v"]["KG-B-L"]}]), headers=H); assert r.status_code == 200, r.text
        assert r.json()["subtotal"] == 1900.0, r.json()
        S["no"] = r.json()["order_no"]
        p = G(S["p"]); assert {x["sku"]: x["stock"] for x in p["variants"]}["KG-B-L"] == 0 and p["stock"] == 5, "mağaza siparişi panele geri yazılmalı"
        o = [x for x in c.get("/api/shop/orders", headers=O).json() if x["order_no"] == S["no"]][0]
        assert o["items"][0]["variant"] == "Beyaz / L" and o["items"][0]["variant_id"] == S["v"]["KG-B-L"], o["items"][0]
        assert c.put("/api/shop/orders/" + o["id"], headers=O, json={"status": "iptal"}).status_code == 200
        p = G(S["p"]); assert {x["sku"]: x["stock"] for x in p["variants"]}["KG-B-L"] == 2 and p["stock"] == 7, "mağaza iptali seçeneğe geri verir"
    t("mağaza siparişi: seçenek zorunlu, fiyat seçenekten, panele stok yazımı, iptalde iade", e)
    def f():
        import asyncio, shop_sync
        async def run():
            fdb = (await s.db.main().firms.find_one({"_id": F}) or await s.db.main().firms.find_one({"id": F}))["db"]
            d = s.db.firm(fdb)
            await shop_sync.apply_market_order(d, "trendyol", "K1", {"status": "Created", "lines": [{"barcode": "8690000000014", "quantity": 3}]})
        try:
            c.portal.call(run)
        except Exception:
            import traceback; print(traceback.format_exc()[-400:]); raise
        p = G(S["p"]); assert {x["sku"]: x["stock"] for x in p["variants"]}["KG-B-M"] == 2, [x["stock"] for x in p["variants"]]
    t("pazaryeri siparişi: varyant barkoduyla doğru seçenekten düşer", f)
for n in ok: print("  ✓", n)
for n, x in bad: print("  ✗", n, "\n", x)
print("OK %d FAIL %d" % (len(ok), len(bad)))
