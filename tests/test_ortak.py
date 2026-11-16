"""Ortaklık: ortak kaydı, referans kodu, tıklama, komisyon yaşam döngüsü, ödeme, kendi siparişi/bayi siparişi hariç."""
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
    r = c.post("/api/admin/firms", headers=A, json={"name": "Ortak Firma", "email": "of@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "of@x.com", "sifre12345")
    c.put("/api/site/features", headers=O, json={"shop_enabled": True, "customer_portal_enabled": True})
    c.put("/api/shop/settings", headers=O, json={"shipping_fee": 50, "bank_accounts": [{"bank": "Ziraat", "holder": "M", "iban": "TR330006100519786457841326"}]})
    P = lambda path: "/api/public/" + path.replace("{F}", F + "~")
    body = lambda ph, qty, ref: {"customer": {"name": "Veli Müşteri", "phone": ph, "address": "Atatürk cad. 12 Ankara"}, "items": [{"product_id": S["P"], "qty": qty}], "accept_terms": True, "payment_method": "havale", "ref": ref}
    def acc(ph, n):
        rr = c.post(P("customer/{F}register"), json={"name": n, "phone": ph, "password": "parola1234"}); assert rr.status_code in (200, 201), rr.text
        return {"Authorization": "Bearer " + rr.json()["token"]}
    def a():
        r = c.post("/api/yp/products", headers=O, json={"name": "Lamba", "price": 500, "cost": 200, "sku": "LMB", "stock": 100}); assert r.status_code == 200, r.text
        S["P"] = r.json()["id"]
        assert c.post("/api/yp/ortak", headers=O, json={"name": "", "pct": 10}).status_code == 422
        assert c.post("/api/yp/ortak", headers=O, json={"name": "Ayşe Blog", "pct": 80}).status_code == 422, "oran sınırı"
        r = c.post("/api/yp/ortak", headers=O, json={"name": "Ayşe Blog", "phone": "0533 111 22 33", "pct": 10}); assert r.status_code == 200, r.text
        S["A"] = r.json()["id"]; S["code"] = r.json()["code"]; assert len(S["code"]) == 6
        assert c.post("/api/yp/ortak", headers=O, json={"name": "Başkası", "pct": 5, "code": S["code"].lower()}).status_code == 409, "kod benzersiz"
    t("ortak oluşur, kod benzersiz, oran sınırlı", a)
    def b():
        assert c.post(P("ortak/{F}click"), json={"code": "YOKTUR"}).json()["ok"] is False
        r1 = c.post(P("ortak/{F}click"), json={"code": S["code"]}).json(); assert r1["counted"] is True
        r2 = c.post(P("ortak/{F}click"), json={"code": S["code"]}).json(); assert r2["counted"] is False, "aynı ziyaretçi tekrar sayılmaz"
        row = [x for x in c.get("/api/yp/ortak", headers=O).json()["rows"] if x["id"] == S["A"]][0]; assert row["clicks"] == 1 and row["link"].endswith("ref=" + S["code"]), row
    t("tıklama sayılır, tekrarı sayılmaz", b)
    def d():
        H = acc("0532 000 11 22", "Veli")
        r = c.post(P("shop/{F}orders"), json=body("0532 000 11 22", 2, S["code"]), headers=H); assert r.status_code == 200, r.text
        S["no"] = r.json()["order_no"]; assert r.json()["subtotal"] == 1000
        r = c.post(P("shop/{F}orders"), json=body("0532 000 11 22", 1, "YANLIS"), headers=H); assert r.status_code == 200, "geçersiz kod siparişi bozmaz"
        cm = c.get("/api/yp/ortak/%s/komisyon" % S["A"], headers=O).json()["rows"]
        assert len(cm) == 1 and cm[0]["amount"] == 100 and cm[0]["status"] == "pending" and cm[0]["base"] == 1000, cm
    t("siparişte komisyon doğar (kargo hariç, bekliyor)", d)
    def e():
        H = acc("0533 111 22 33", "Ayşe Kendi")
        r = c.post(P("shop/{F}orders"), json=body("0533 111 22 33", 1, S["code"]), headers=H); assert r.status_code == 200, r.text
        assert len(c.get("/api/yp/ortak/%s/komisyon" % S["A"], headers=O).json()["rows"]) == 1, "kendi siparişine komisyon yok"
    t("ortağın kendi siparişine komisyon yazılmaz", e)
    def f():
        o = [x for x in c.get("/api/shop/orders", headers=O).json() if x["order_no"] == S["no"]][0]
        assert c.post("/api/yp/ortak/%s/odeme" % S["A"], headers=O, json={}).status_code == 422, "onaylı komisyon yokken ödeme olmaz"
        assert c.put("/api/shop/orders/" + o["id"], headers=O, json={"status": "teslim_edildi"}).status_code == 200
        L = c.get("/api/yp/ortak", headers=O).json(); row = [x for x in L["rows"] if x["id"] == S["A"]][0]
        assert row["approved"] == 100 and row["pending"] == 0, row
        p = c.post("/api/yp/ortak/%s/odeme" % S["A"], headers=O, json={"note": "Havale"}); assert p.status_code == 200 and p.json()["amount"] == 100, p.text
        assert c.post("/api/yp/ortak/%s/odeme" % S["A"], headers=O, json={}).status_code == 422, "çift ödeme olmaz"
        row = [x for x in c.get("/api/yp/ortak", headers=O).json()["rows"] if x["id"] == S["A"]][0]; assert row["paid"] == 100 and row["approved"] == 0, row
    t("teslimde onaylanır, ödeme kaydı tek sefer", f)
    def g():
        H = acc("0532 777 88 99", "Zeynep")
        r = c.post(P("shop/{F}orders"), json=body("0532 777 88 99", 1, S["code"]), headers=H); assert r.status_code == 200, r.text
        no = r.json()["order_no"]; o = [x for x in c.get("/api/shop/orders", headers=O).json() if x["order_no"] == no][0]
        assert c.put("/api/shop/orders/" + o["id"], headers=O, json={"status": "iptal"}).status_code == 200
        cm = c.get("/api/yp/ortak/%s/komisyon" % S["A"], headers=O).json()["rows"]
        assert [x for x in cm if x["order_no"] == no][0]["status"] == "cancelled", cm
        row = [x for x in c.get("/api/yp/ortak", headers=O).json()["rows"] if x["id"] == S["A"]][0]; assert row["pending"] == 0 and row["approved"] == 0
    t("iptal edilen siparişin komisyonu iptal olur", g)
    def h():
        assert c.post("/api/yp/ortak/" + S["A"], headers=O, json={"status": "passive"}).status_code == 200
        H = acc("0532 444 55 66", "Can")
        r = c.post(P("shop/{F}orders"), json=body("0532 444 55 66", 1, S["code"]), headers=H); assert r.status_code == 200
        assert len(c.get("/api/yp/ortak/%s/komisyon" % S["A"], headers=O).json()["rows"]) == 3 - 0 or True
        assert c.post(P("ortak/{F}click"), json={"code": S["code"]}).json()["ok"] is False, "pasif ortak tıklama almaz"
        n = len([x for x in c.get("/api/yp/ortak/%s/komisyon" % S["A"], headers=O).json()["rows"]]); assert n == 2, n
    t("pasif ortak komisyon ve tıklama almaz", h)
for n in ok: print("  ✓", n)
for n, e in bad: print("  ✗", n, e)
print("OK", len(ok), "FAIL", len(bad)); sys.exit(1 if bad else 0)
