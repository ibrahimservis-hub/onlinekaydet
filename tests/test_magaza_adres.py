"""Ürün formu (slug kontrolü, çoklu kategori) ve müşteri adres defteri."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:500]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Adres Firma", "email": "ad@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "ad@x.com", "sifre12345")
    c.put("/api/site/features", headers=O, json={"shop_enabled": True, "customer_portal_enabled": True})
    r = c.post("/api/shop/products", headers=O, json={"name": "Kombi Pompa", "price": 900, "stock": 3, "category": "Pompa"}); assert r.status_code == 200, r.text
    P1 = r.json()
    def slug():
        r = c.get("/api/shop/slug-check?slug=Kombi Pompa", headers=O).json(); assert r["free"] is False and r["suggest"] != r["slug"], r
        r = c.get("/api/shop/slug-check?slug=Kombi Pompa&id=" + P1["id"], headers=O).json(); assert r["free"] is True, r
        r = c.get("/api/shop/slug-check?slug=Yeni Urun", headers=O).json(); assert r["free"] is True, r
    t("slug kontrolü: dolu/boş/kendi ürünü", slug)
    def multi():
        a = c.post("/api/shop/categories", headers=O, json={"name": "Yedek Parça"}); b = c.post("/api/shop/categories", headers=O, json={"name": "Pompalar"})
        assert a.status_code == 200 and b.status_code == 200, (a.text, b.text)
        ids = [a.json()["id"], b.json()["id"]]
        r = c.put("/api/shop/products/" + P1["id"], headers=O, json={"category_ids": ids}); assert r.status_code == 200, r.text
        assert r.json()["category_ids"] == ids and r.json()["category"] == "Yedek Parça", r.json()
    t("çoklu kategori: ilk kategori ana kategori olur", multi)
    def addr():
        rr = c.post(f"/api/public/customer/{F}~register", json={"name": "Ali Veli", "phone": "0532 555 11 22", "password": "parola1234"}); assert rr.status_code in (200, 201), rr.text
        H = {"Authorization": "Bearer " + rr.json()["token"]}; U = f"/api/public/customer/{F}~addresses"
        body = {"title": "Ev", "name": "Ali Veli", "phone": "0532 555 11 22", "city": "Ankara", "district": "Çankaya", "address": "Atatürk cad. no 5"}
        r = c.post(U, headers=H, json=body); assert r.status_code == 200 and len(r.json()) == 1 and r.json()[0]["default"], r.text
        r = c.post(U, headers=H, json={**body, "title": "İş", "default": True}); l = r.json(); assert len(l) == 2 and [x["default"] for x in l] == [False, True], l
        r = c.post(U, headers=H, json={**body, "address": "kısa"}); assert r.status_code == 422, r.text
        aid = l[0]["id"]
        r = c.put(U + "/" + aid, headers=H, json={"title": "Ev 2"}); assert r.status_code == 200 and r.json()[0]["title"] == "Ev 2", r.text
        r = c.delete(U + "/" + l[1]["id"], headers=H); l = r.json(); assert len(l) == 1 and l[0]["default"], l
        assert c.get(U).status_code == 401
    t("müşteri adres defteri: ekle/varsayılan/düzenle/sil/doğrulama", addr)
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" FAIL", n, e)
sys.exit(1 if bad else 0)
