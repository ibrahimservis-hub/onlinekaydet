"""B2B vitrin: onaylı bayi vitrinde kendi fiyatını görür."""
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
    F = r.json()["id"]; O = tok(c, "bf@x.com", "sifre12345")
    c.put("/api/site/features", headers=O, json={"shop_enabled": True, "customer_portal_enabled": True})
    c.put("/api/shop/settings", headers=O, json={"shipping_fee": 0, "bank_accounts": [{"bank": "Ziraat", "holder": "M", "iban": "TR330006100519786457841326"}]})
    P = lambda path: "/api/public/" + path.replace("{F}", F + "~")
    def a():
        for n, sku, pr in (("Tabak Seti", "TB", 1000), ("Bardak", "BR", 100)):
            r = c.post("/api/yp/products", headers=O, json={"name": n, "price": pr, "cost": pr / 2, "sku": sku, "stock": 50, "category": "Mutfak"}); assert r.status_code == 200, r.text
            S[sku] = r.json()["id"]
        rr = c.post(P("customer/{F}register"), json={"name": "Ali Bayi", "phone": "0532 555 11 22", "password": "parola1234"}); S["H"] = {"Authorization": "Bearer " + rr.json()["token"]}
        c.post(P("b2b/{F}apply"), json={"company": "Ali Hırdavat Ltd.", "tax_no": "1234567890", "address": "Sanayi sitesi 5. blok Ankara"}, headers=S["H"])
        S["D"] = c.get("/api/yp/b2b/dealers", headers=O).json()["rows"][0]["id"]
        S["G"] = c.post("/api/yp/b2b/groups", headers=O, json={"name": "Altın", "discount_pct": 20, "min_order": 500}).json()["id"]
    t("kurulum", a)
    def b():
        items = lambda r: {x["id"]: x for x in r.json()["items"]}
        # başvuru bekliyor: fiyat liste fiyatı
        assert items(c.get(P("shop/{F}search"), headers=S["H"]))[S["TB"]]["price"] == 1000
        assert c.post("/api/yp/b2b/dealers/" + S["D"], headers=O, json={"status": "approved", "group_id": S["G"], "credit_limit": 3000}).status_code == 200
        anon = items(c.get(P("shop/{F}search"))); assert anon[S["TB"]]["price"] == 1000 and "bayi" not in anon[S["TB"]], "anonim ziyaretçi liste fiyatı görür"
        dl = items(c.get(P("shop/{F}search"), headers=S["H"]))
        assert dl[S["TB"]]["price"] == 800 and dl[S["TB"]]["old_price"] == 1000 and dl[S["TB"]]["bayi"] is True and dl[S["BR"]]["price"] == 80, dl
        p = c.get(P("shop/{F}products/") .replace("~", "~") + S["TB"], headers=S["H"]).json(); assert p["price"] == 800 and p["old_price"] == 1000, p
        assert c.get(P("shop/{F}products/") + S["TB"]).json()["price"] == 1000
        rel = c.get(P("shop/{F}related/") + S["TB"], headers=S["H"]).json(); allr = rel["similar"] + rel["same_brand"] + rel["picked"]
        assert all(x["price"] == 80 for x in allr if x["id"] == S["BR"]), rel
        assert c.get(P("shop/{F}related/") + S["TB"]).json()["similar"][0]["price"] == 100
    t("bayi girişinde vitrin bayi fiyatını gösterir, anonim ve onaysız göstermez", b)
    def d():
        q = c.post(P("b2b/{F}quote"), headers=S["H"], json={"items": [{"id": S["TB"], "v": "", "q": 1}, {"id": S["BR"], "v": "", "q": 2}, {"id": "yok", "q": 1}]}).json()["items"]
        assert {x["id"]: x["price"] for x in q} == {S["TB"]: 800, S["BR"]: 80} and len(q) == 2, q
        assert c.post(P("b2b/{F}quote"), json={"items": []}).status_code == 401
    t("sepet fiyat sorgusu", d)
for n in ok: print("  ✓", n)
for n, e in bad: print("  ✗", n, e)
print("OK", len(ok), "FAIL", len(bad)); sys.exit(1 if bad else 0)
