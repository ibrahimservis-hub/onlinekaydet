"""Sahip ekranı: firma oturumu ile firma verisine müdahale, satış hattı, kurulum adımları, toplu işlemler."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: import traceback; bad.append((n, traceback.format_exc()[-700:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    def mk(name, email):
        r = c.post("/api/admin/firms", headers=A, json={"name": name, "email": email, "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text; return r.json()["id"]
    F1 = mk("Sahip Test Bir", "sa1@x.com"); F2 = mk("Sahip Test Iki", "sa2@x.com")
    def sess():
        r = c.post(f"/api/admin/firms/{F1}/session", headers=A); assert r.status_code == 200, r.text
        S["H"] = {"Authorization": "Bearer " + r.json()["token"]}
    t("firma oturumu alınır", sess)
    def firm_only():
        r = c.post(f"/api/admin/firms/{F1}/session", headers=tok(c, "sa1@x.com", "sifre12345")); assert r.status_code in (401, 403), r.status_code
    t("firma kendi adına sahip oturumu alamaz", firm_only)
    def prod():
        r = c.post("/api/shop/products", headers=S["H"], json={"name": "Sensör", "price": 100, "stock": 5, "sku": "SN-1"}); assert r.status_code == 200, r.text; S["pid"] = r.json()["id"]
        r = c.put(f"/api/shop/products/{S['pid']}", headers=S["H"], json={"stock": 9, "price": 150}); assert r.status_code == 200, r.text
        L = c.get("/api/shop/products", headers=S["H"]).json(); p = next(x for x in L if x["id"] == S["pid"]); assert p["stock"] == 9 and p["price"] == 150 and p["name"] == "Sensör"
    t("firma ürünü sahip oturumuyla eklenir ve stok/fiyat değişir", prod)
    def other_isolated():
        r = c.post(f"/api/admin/firms/{F2}/session", headers=A); H2 = {"Authorization": "Bearer " + r.json()["token"]}
        assert not [x for x in c.get("/api/shop/products", headers=H2).json() if x["id"] == S["pid"]]
    t("firmalar birbirinin verisini görmez", other_isolated)
    def cust_cash():
        r = c.post("/api/customers", headers=S["H"], json={"name": "Ali", "phone": "05321112233"}); assert r.status_code == 200, r.text
        r = c.post("/api/cash/transactions", headers=S["H"], json={"type": "gelir", "amount": 500, "description": "Test"}); assert r.status_code == 200, r.text
        assert c.get("/api/finance/overview", headers=S["H"]).json()["revenue"] >= 500
    t("müşteri ve kasa kaydı", cust_cash)
    def note():
        r = c.post(f"/api/admin/firms/{F1}/note", headers=A, json={"action": "Ürün", "detail": "stok 9"}); assert r.status_code == 200
        rows = c.get(f"/api/admin/firms/{F1}/audit", headers=A).json()["rows"]; assert any("SAHİP İŞLEMİ" in x["action"] for x in rows), rows[:3]
    t("sahip işlemi günlüğe yazılır", note)
    def pipe():
        r = c.post("/api/admin/pipeline", headers=A, json={"name": "Yıldız Kombi", "city": "Ankara", "note": "WhatsApp'tan geldi"}); assert r.status_code == 200, r.text; cid = r.json()["id"]
        assert c.put(f"/api/admin/pipeline/{cid}", headers=A, json={"stage": "demo", "add_note": "Demo yapıldı"}).json()["stage"] == "demo"
        d = c.get("/api/admin/pipeline", headers=A).json(); cd = next(x for x in d["cards"] if x["id"] == cid); assert cd["stage"] == "demo" and len(cd["notes"]) == 2 and d["active"]
        assert c.put(f"/api/admin/pipeline/{cid}", headers=A, json={"stage": "x"}).status_code == 400
        assert c.delete(f"/api/admin/pipeline/{cid}", headers=A).status_code == 200
        assert c.post("/api/admin/pipeline", headers=A, json={"name": ""}).status_code == 400
    t("satış hattı kartı", pipe)
    def onb():
        d = c.get("/api/admin/onboarding", headers=A).json(); f = next(x for x in d["firms"] if x["id"] == F1); assert f["total"] == 10 and not [i for i in f["items"] if i["k"] == "egitim"][0]["ok"]
        assert c.put(f"/api/admin/onboarding/{F1}", headers=A, json={"key": "egitim", "ok": True}).status_code == 200
        c.put(f"/api/admin/onboarding/{F1}", headers=A, json={"note": "Logo yarın"})
        f = next(x for x in c.get("/api/admin/onboarding", headers=A).json()["firms"] if x["id"] == F1); assert [i for i in f["items"] if i["k"] == "egitim"][0]["ok"] and f["note"] == "Logo yarın"
        assert c.put(f"/api/admin/onboarding/{F1}", headers=A, json={"key": "tel", "ok": True}).status_code == 400
    t("kurulum adımları", onb)
    def bulk():
        r = c.post("/api/admin/bulk", headers=A, json={"ids": [F1, F2], "action": "extend", "value": 30}); assert r.json()["updated"] == 2, r.text
        r = c.post("/api/admin/bulk", headers=A, json={"ids": [F1, F2], "action": "module_off", "value": "pazarlama"}); assert r.json()["updated"] == 2
        fl = {x["id"]: x for x in c.get("/api/admin/firms", headers=A).json()["firms"]}; assert "pazarlama" not in fl[F1]["modules"] and "servis" in fl[F1]["modules"] and fl[F1]["expires_at"]
        assert c.post("/api/admin/bulk", headers=A, json={"ids": [F1], "action": "module_on", "value": "nope"}).status_code == 400
        assert c.post("/api/admin/bulk", headers=A, json={"ids": [], "action": "extend", "value": 5}).status_code == 400
        assert c.post("/api/admin/bulk", headers=A, json={"ids": [F1], "action": "package", "value": "baslangic"}).json()["updated"] == 1
        assert c.post("/api/admin/bulk", headers=tok(c, "sa1@x.com", "sifre12345"), json={"ids": [F1], "action": "extend", "value": 5}).status_code in (401, 403)
    t("toplu işlemler", bulk)
    def roles():
        r = c.get("/api/governance/roles", headers=S["H"]); assert r.status_code == 200
    t("firma yetki rolleri okunur", roles)
print("OK" if not bad else "FAIL", len(ok), "geçti"); [print("✗", n, "\n", m) for n, m in bad]
