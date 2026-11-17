"""Anında demo: forma ad/telefon/sektör -> örnek verili firma açılır, giriş çalışır, usta işlerini görür, kötüye kullanım sınırlı."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e:
        import traceback; bad.append((n, traceback.format_exc()[-300:]))
with TestClient(s.app) as c:
    def a():
        r = c.post("/api/public/demo", json={"name": "Ibrahim Kargi", "phone": "05524165710", "sector": "Kombi"}); assert r.status_code == 200, r.text
        S.update(r.json()); assert S["email"].endswith("@demo.onlinekaydet.com") and len(S["password"]) == 8
    t("demo açılır, giriş bilgisi döner", a)
    def b():
        r = c.post("/api/auth/login", json={"email": S["email"], "password": S["password"]}); assert r.status_code == 200, r.text
        H = {"Authorization": "Bearer " + r.json()["token"]}; S["H"] = H
        jobs = c.get("/api/jobs", headers=H).json(); assert len(jobs) == 7, len(jobs)
        assert {j["status"] for j in jobs} >= {"yeni", "atandi", "yolda", "basladi", "tamamlandi"}
        assert len(c.get("/api/customers", headers=H).json()) == 5 and len(c.get("/api/technicians", headers=H).json()) == 2
        assert c.get("/api/dashboard/admin", headers=H).json()["total_revenue"] > 0
        pk = c.get("/api/firm/package", headers=H).json(); assert pk["package"] == "kurumsal" and pk["locked"] == ["eticaret"]
    t("yönetici girişi: 7 servis kaydı, 5 müşteri, 2 usta, tam paket", b)
    def d():
        r = c.post("/api/auth/login", json={"email": S["tech_email"], "password": S["password"]}); assert r.status_code == 200, r.text
        U = {"Authorization": "Bearer " + r.json()["token"]}; mine = c.get("/api/jobs", headers=U).json(); assert mine and all(j["assigned_technician_id"] for j in mine)
        j = [x for x in mine if x["status"] == "atandi"][0]
        assert c.put("/api/jobs/" + j["id"], headers=U, json={"status": "yolda"}).status_code == 200
    t("usta girişi: kendi işlerini görür ve ilerletir", d)
    def e():
        assert c.post("/api/public/demo", json={"name": "A", "phone": "05524165710", "sector": "Kombi"}).status_code == 422
        assert c.post("/api/public/demo", json={"name": "Ali Veli", "phone": "123", "sector": "Kombi"}).status_code == 422
        assert c.post("/api/public/demo", json={"name": "Ali Veli", "phone": "05524165711", "sector": "uzay"}).status_code == 422
        assert c.post("/api/public/demo", json={"name": "Bot", "phone": "05524165712", "sector": "Kombi", "website": "x"}).json() == {"ok": True}
    t("geçersiz ad/telefon/sektör 422, bot tuzağı sessiz", e)
    def f():
        r = c.post("/api/public/demo", json={"name": "Ibrahim Kargi", "phone": "05524165710", "sector": "Klima"}); assert r.status_code == 200
        r = c.post("/api/public/demo", json={"name": "Ibrahim Kargi", "phone": "05524165710", "sector": "Klima"}); assert r.status_code == 429, r.status_code
    t("aynı telefonla günde en fazla 2 demo", f)
    def g():
        A = c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]
        L = c.get("/api/admin/leads", headers={"Authorization": "Bearer " + A}).json()
        assert any(x.get("form") == "demo-hesabi" for x in L["leads"]), L
        subs = c.get("/api/admin/subscriptions?days=30", headers={"Authorization": "Bearer " + A}); assert subs.status_code == 200
    t("talep, satış listesine 'demo' olarak düşer", g)
    def h():
        A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
        r = c.post("/api/admin/demo-cleanup", headers=A, json={"expired": True}); assert r.status_code == 200 and r.json()["removed"] == [], r.text
        FL = c.get("/api/admin/firms", headers=A).json(); FL = FL.get("firms", FL); fid = [x for x in FL if x.get("demo")][0]["id"]
        r = c.post("/api/admin/demo-cleanup", headers=A, json={"ids": [fid], "expired": False}); assert len(r.json()["removed"]) == 1, r.text
        FL = c.get("/api/admin/firms", headers=A).json(); FL = FL.get("firms", FL); assert fid not in [x["id"] for x in FL]
        assert c.post("/api/admin/demo-cleanup", headers=S["H"], json={}).status_code == 403
    t("demo temizliği: süresi dolmayan kalır, seçilen silinir, firma yöneticisi yapamaz", h)
    def m():
        r = c.get("/api/shop/settings", headers=S["H"]); assert r.status_code == 200, r.text
        r = c.put("/api/shop/settings", headers=S["H"], json={"shipping_fee": 49.9, "free_shipping_over": 1500, "bank_accounts": [{"bank": "Ziraat", "holder": "Test", "iban": "tr12 0001 0000 0000 0000 0000 01"}]}); assert r.status_code == 200, r.text
        j = r.json(); assert j["shipping_fee"] == 49.9 and j["bank_accounts"][0]["iban"].startswith("TR12")
    t("mağaza ayarları kaydedilir", m)
    def r():
        c.post("/api/public/demo", json={"name": "Zeynep Kaya", "phone": "05524165720", "sector": "Kombi"})
        async def go():
            await s.db.main().firms.update_many({"demo": True}, {"$set": {"name": "Eski Ad Servis (Demo)"}})
            await s.demo.rename_old_demos(s.db)
            return sorted([f["name"] async for f in s.db.main().firms.find({"demo": True})])
        names = c.portal.call(go); assert names and all(n.startswith("Demo ") for n in names) and len(set(names)) == len(names), names
    t("eski demo adları 'Demo N'e çevrilir", r)
print(f"GEÇTİ {len(ok)}/{len(ok)+len(bad)}")
for x in bad: print("BAŞARISIZ", x)
