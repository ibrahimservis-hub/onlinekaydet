"""Demo firma -> gerçek müşteri: paket düşer, süre/ad/giriş güncellenir, demo işareti kalkar (temizlik silmez), örnek veri temizlenir."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server
with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    d = c.post("/api/public/demo", json={"name": "Ahmet Usta", "phone": "05329990011", "sector": "kuafor"}).json()
    fid = [f for f in c.get("/api/admin/firms", headers=A).json()["firms"] if f.get("demo")][0]["id"]
    ft = c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]; H = {"Authorization": "Bearer " + ft}
    sayi = lambda h=None: len(c.get("/api/yp/customers", headers=h or H).json()["rows"])
    assert sayi() == 5
    # 1) paket düşür, süre, ad, giriş
    r = c.put("/api/admin/firms/" + fid, headers=A, json={"package": "baslangic", "usage_days": 30, "name": "Ahmet Kuaför", "email": "ahmet@kuafor.com", "password": "Yeni12345"}); assert r.status_code == 200, r.text
    r = c.post("/api/admin/firms/%s/demo-donustur" % fid, headers=A, json={"temizle": False}); assert r.status_code == 200, r.text
    f = [x for x in c.get("/api/admin/firms", headers=A).json()["firms"] if x["id"] == fid][0]
    assert not f.get("demo") and f["package"] == "baslangic" and f["name"] == "Ahmet Kuaför", f
    assert c.post("/api/admin/firms/%s/demo-donustur" % fid, headers=A, json={}).status_code == 409
    # 2) demo temizliği artık bu firmayı silmemeli (süresi dolmuş sayılsa bile)
    r = c.post("/api/admin/demo-cleanup", headers=A, json={}); assert "Ahmet Kuaför" not in r.json()["removed"], r.json()
    # 3) yeni giriş çalışıyor, eski demo şifresi geçersiz, veriler yerinde
    assert c.post("/api/auth/login", json={"email": "ahmet@kuafor.com", "password": "Yeni12345"}).status_code == 200
    assert c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).status_code in (401, 400, 403)
    H2 = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "ahmet@kuafor.com", "password": "Yeni12345"}).json()["token"]}
    assert sayi(H2) == 5
    # 4) ikinci demo: örnek veriyi temizleyerek çevir
    d2 = c.post("/api/public/demo", json={"name": "Veli", "phone": "05329990022", "sector": "kuafor"}, headers={"X-Forwarded-For": "9.9.9.9"}).json()
    fid2 = [x for x in c.get("/api/admin/firms", headers=A).json()["firms"] if x.get("demo")][0]["id"]
    r = c.post("/api/admin/firms/%s/demo-donustur" % fid2, headers=A, json={"temizle": True}).json(); assert r["silinen"]["customers"] == 5 and r["silinen"]["users"] == 2, r
    T2 = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": d2["email"], "password": d2["password"]}).json()["token"]}
    assert sayi(T2) == 0
    assert c.post("/api/auth/login", json={"email": d2["tech_email"], "password": d2["password"]}).status_code in (401, 400, 403, 404)
print("GEÇTİ")
