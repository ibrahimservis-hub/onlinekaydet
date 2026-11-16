"""B2B bayi: grup/iskonto, başvuru-onay, toptan fiyat (yalnız bayiye, pazaryerine sızmaz), asgari sipariş, cari limit, defter, iptalde iade."""
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
    r = c.post("/api/admin/firms", headers=A, json={"name": "Bayi Firma", "email": "bf@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "bf@x.com", "sifre12345")
    c.put("/api/site/features", headers=O, json={"shop_enabled": True, "customer_portal_enabled": True})
    c.put("/api/shop/settings", headers=O, json={"shipping_fee": 0, "bank_accounts": [{"bank": "Ziraat", "holder": "M", "iban": "TR330006100519786457841326"}]})
    P = lambda path: "/api/public/" + path.replace("{F}", F + "~")
    def a():
        for n, sku, pr in (("Tabak Seti", "TB", 1000), ("Bardak", "BR", 100)):
            r = c.post("/api/yp/products", headers=O, json={"name": n, "price": pr, "cost": pr / 2, "sku": sku, "stock": 50}); assert r.status_code == 200, r.text
            S[sku] = r.json()["id"]
        rr = c.post(P("customer/{F}register"), json={"name": "Ali Bayi", "phone": "0532 555 11 22", "password": "parola1234"}); assert rr.status_code in (200, 201), rr.text
        S["H"] = {"Authorization": "Bearer " + rr.json()["token"]}
        assert c.get(P("b2b/{F}me"), headers=S["H"]).json()["status"] == "none"
        assert c.get(P("b2b/{F}products"), headers=S["H"]).status_code == 403, "onaysız bayi toptan listeyi göremez"
        assert c.get(P("b2b/{F}me")).status_code == 401
    t("hesap açık, bayi değil: liste kapalı", a)
    def b():
        body = {"company": "Ali Hırdavat Ltd.", "tax_no": "1234567890", "address": "Sanayi sitesi 5. blok Ankara"}
        assert c.post(P("b2b/{F}apply"), json={**body, "tax_no": "123"}, headers=S["H"]).status_code == 422
        assert c.post(P("b2b/{F}apply"), json=body, headers=S["H"]).status_code == 200
        assert c.post(P("b2b/{F}apply"), json=body, headers=S["H"]).status_code == 409
        d = c.get("/api/yp/b2b/dealers", headers=O).json(); assert d["counts"]["pending"] == 1
        S["D"] = d["rows"][0]["id"]
        assert c.post("/api/yp/b2b/dealers/" + S["D"], headers=O, json={"status": "approved"}).status_code == 422, "grupsuz onay olmaz"
        g = c.post("/api/yp/b2b/groups", headers=O, json={"name": "Altın bayi", "discount_pct": 20, "min_order": 500}); assert g.status_code == 200, g.text
        S["G"] = g.json()["id"]
        assert c.post("/api/yp/b2b/groups", headers=O, json={"name": "X", "discount_pct": 95}).status_code == 422
        r = c.post("/api/yp/b2b/dealers/" + S["D"], headers=O, json={"status": "approved", "group_id": S["G"], "credit_limit": 3000}); assert r.status_code == 200, r.text
        me = c.get(P("b2b/{F}me"), headers=S["H"]).json()
        assert me["status"] == "approved" and me["discount_pct"] == 20 and me["kullanilabilir"] == 3000, me
    t("başvuru, doğrulamalar, grup, onay", b)
    def d():
        rows = {x["sku"]: x for x in c.get(P("b2b/{F}products"), headers=S["H"]).json()["rows"]}
        assert rows["TB"]["price"] == 800 and rows["TB"]["list_price"] == 1000 and rows["BR"]["price"] == 80, rows
        r = c.put("/api/yp/b2b/prices", headers=O, json={"group": S["G"], "items": [{"product_id": S["TB"], "price": 700}]}); assert r.status_code == 200, r.text
        assert c.put("/api/yp/b2b/prices", headers=O, json={"group": S["G"], "items": [{"product_id": S["TB"], "price": 1200}]}).status_code == 422
        rows = {x["sku"]: x for x in c.get(P("b2b/{F}products"), headers=S["H"]).json()["rows"]}
        assert rows["TB"]["price"] == 700 and rows["BR"]["price"] == 80, "ürüne özel fiyat iskontodan önce gelir"
        pl = c.get("/api/yp/b2b/prices?group=" + S["G"] + "&q=TB", headers=O).json(); assert pl["rows"][0]["b2b_price"] == 700
    t("fiyat çözümü: iskonto ve ürüne özel toptan fiyat", d)
    def e():
        pub = c.get(P("shop/{F}products")).json()
        row = [x for x in pub["products"] if x["id"] == S["TB"]][0]
        assert row["price"] == 1000, "herkese açık fiyat liste fiyatı kalır"
        sd = c.get("/api/shop/products", headers=O).json()
        sh = [x for x in (sd if isinstance(sd, list) else sd.get("items") or sd.get("rows") or sd.get("products")) if x["id"] == S["TB"]][0]
        assert sh["price"] == 1000 and "b2b" not in str(sh).lower(), "mağaza/pazaryeri belgesine toptan fiyat yazılmaz"
    t("toptan fiyat herkese açık ürün ve pazaryeri belgesine sızmaz", e)
    body = lambda items, pm: {"customer": {"name": "Ali Hırdavat", "phone": "0532 555 11 22", "address": "Sanayi sitesi 5. blok Ankara"}, "items": items, "accept_terms": True, "payment_method": pm}
    def f():
        r = c.post(P("shop/{F}orders"), json=body([{"product_id": S["BR"], "qty": 2}], "cari"), headers=S["H"]); assert r.status_code == 422 and "asgari" in r.text, r.text
        r = c.post(P("shop/{F}orders"), json=body([{"product_id": S["TB"], "qty": 2}], "cari"), headers=S["H"]); assert r.status_code == 200, r.text
        assert r.json()["subtotal"] == 1400.0 and r.json()["next"] == "cari", r.json(); S["no"] = r.json()["order_no"]
        me = c.get(P("b2b/{F}me"), headers=S["H"]).json(); assert me["bakiye"] == 1400 and me["kullanilabilir"] == 1600, me
        r = c.post(P("shop/{F}orders"), json=body([{"product_id": S["TB"], "qty": 2}], "cari"), headers=S["H"]); assert r.status_code == 200, r.text
        r = c.post(P("shop/{F}orders"), json=body([{"product_id": S["TB"], "qty": 1}], "cari"), headers=S["H"]); assert r.status_code == 422 and "limit" in r.text.lower(), r.text
        r = c.post(P("shop/{F}orders"), json=body([{"product_id": S["TB"], "qty": 1}], "havale"), headers=S["H"]); assert r.status_code == 200, "başka ödemede de bayi fiyatı"
        assert r.json()["subtotal"] == 700.0
    t("sipariş: asgari tutar, cari borç, limit aşımı, havale ile de bayi fiyatı", f)
    def g():
        L = c.get("/api/yp/b2b/dealers/%s/ledger" % S["D"], headers=O).json(); assert L["bakiye"] == 2800 and len(L["rows"]) == 2, L
        assert c.post("/api/yp/b2b/dealers/%s/ledger" % S["D"], headers=O, json={"tur": "alacak", "tutar": 1000, "aciklama": "Havale tahsilatı"}).json()["bakiye"] == 1800
        o = [x for x in c.get("/api/shop/orders", headers=O).json() if x["order_no"] == S["no"]][0]
        assert c.put("/api/shop/orders/" + o["id"], headers=O, json={"status": "iptal"}).status_code == 200
        assert c.get("/api/yp/b2b/dealers/%s/ledger" % S["D"], headers=O).json()["bakiye"] == 400, "iptalde borç kapanır"
        c.put("/api/shop/orders/" + o["id"], headers=O, json={"status": "iptal"})
        assert c.get("/api/yp/b2b/dealers/%s/ledger" % S["D"], headers=O).json()["bakiye"] == 400, "iade iki kez yazılmaz"
        assert c.post("/api/yp/b2b/dealers/" + S["D"], headers=O, json={"status": "blocked"}).status_code == 200
        r = c.post(P("shop/{F}orders"), json=body([{"product_id": S["TB"], "qty": 1}], "cari"), headers=S["H"]); assert r.status_code == 422, "engelli bayi cari kullanamaz"
        assert c.delete("/api/yp/b2b/groups/" + S["G"], headers=O).status_code == 409
    t("defter: tahsilat, iptalde tek sefer iade, engelli bayi, dolu grup silinmez", g)
print("OK", len(ok), "FAIL", len(bad))
for n in ok: print("  ✓", n)
for n, tb in bad: print("  ✗", n, "\n", tb)
