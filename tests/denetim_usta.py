"""Personel/usta tarafı (API): giriş, kendi işleri, durum ilerletme, tamamlama + kasa/stok/prim, konum, bakiye, teklif, randevu, yetki sınırları."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
import demo; demo.GUNLUK_LIMIT = 10 ** 6
ok = bad = 0
def t(n, c):
    global ok, bad
    ok += bool(c); bad += (not c); print(("  ✓ " if c else "  ✗ ") + n)
with TestClient(boot.server.app) as c:
    d = c.post("/api/public/demo", json={"name": "Usta Deneme", "phone": "05331112200", "sector": "kombi"}).json()
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
    lg = c.post("/api/auth/login", json={"email": d["tech_email"], "password": d["password"]}); t("usta demo şifresiyle girer (%s)" % lg.status_code, lg.status_code == 200)
    if lg.status_code != 200: print(d); raise SystemExit
    T = {"Authorization": "Bearer " + lg.json()["token"]}; me = lg.json()["user"]; t("usta rolü technician", me["role"] == "technician")
    jobs = c.get("/api/jobs", headers=T).json(); t("usta kendi işlerini görür (%d)" % len(jobs), isinstance(jobs, list) and all(j["assigned_technician_id"] == me["id"] for j in jobs))
    t("usta panoyu açar", c.get("/api/dashboard/tech", headers=T).status_code == 200)
    t("usta rozetleri", c.get("/api/tech/badges", headers=T).status_code == 200)
    t("usta ödeme bilgisi", c.get("/api/tech/pay-info", headers=T).status_code == 200)
    t("usta bakiyesi", c.get("/api/technicians/%s/balance" % me["id"], headers=T).status_code == 200)
    t("usta başka ustanın bakiyesini göremez", c.get("/api/technicians/baska/balance", headers=T).status_code == 403)
    t("usta konum bildirir", c.post("/api/tech/location", headers=T, json={"lat": 39.93, "lng": 32.85}).status_code == 200)
    tl = c.get("/api/admin/tech-locations", headers=A).json(); t("konum yönetici ekranında görünür", any(x["id"] == me["id"] and x.get("lat") for x in tl))
    # yeni iş (yönetici) → usta ilerletir
    q = c.post("/api/jobs/quick", headers=A, json={"customer_name": "Usta Test Müşteri", "customer_phone": "05324440011", "fault_description": "Su basıncı", "assigned_technician_id": me["id"]}); jid = q.json().get("id") or q.json()["job"]["id"]
    t("yeni iş ustanın listesinde", any(j["id"] == jid for j in c.get("/api/jobs", headers=T).json()))
    r0 = c.put("/api/jobs/" + jid, headers=T, json={"status": "basladi"}); t("fotoğrafsız başlatma engellenir (iş kuralı)", r0.status_code == 400)
    for st in ("yolda", "basladi"):
        if st == "basladi": c.put("/api/jobs/" + jid, headers=T, json={"photos_before": ["/api/files/x/onceki.jpg"]})
        r = c.put("/api/jobs/" + jid, headers=T, json={"status": st}); t("usta durumu '%s' yapar" % st, r.status_code == 200)
    sm0 = c.get("/api/cash/summary", headers=A).json(); mine0 = [x for x in sm0["technician_balances"] if x["id"] == me["id"]][0]
    part = c.post("/api/parts", headers=A, json={"name": "Usta Parçası", "price": 200, "cost": 100, "stock_qty": 4}).json()
    c.put("/api/jobs/" + jid, headers=T, json={"photos_after": ["/api/files/x/sonraki.jpg"]})
    r = c.put("/api/jobs/" + jid, headers=T, json={"status": "tamamlandi", "work_done": "Basınç ayarlandı", "parts_used": [{"part_id": part["id"], "name": "Usta Parçası", "qty": 1, "unit_price": 200}], "labor_fee": 300})
    t("usta işi tamamlar", r.status_code == 200 and r.json()["total_amount"] == 500)
    sm = c.get("/api/cash/summary", headers=A).json(); mine = [x for x in sm["technician_balances"] if x["id"] == me["id"]][0]
    t("kasa geliri, usta borcu ve primi yazıldı (borç+prim=500)", abs((mine["debt"] + mine["commission"]) - (mine0["debt"] + mine0["commission"]) - 500) < 0.01 and abs(sm["income"] - sm0["income"] - 500) < 0.01)
    t("stok 1 adet düştü", [p for p in c.get("/api/parts", headers=A).json() if p["id"] == part["id"]][0]["stock_qty"] == 3)
    bl = c.get("/api/technicians/%s/balance" % me["id"], headers=T).json(); t("usta bakiyesi şirkete borcu gösterir", bl["total_debt"] > 0 or bl["total_commission"] > 0)
    n = c.post("/api/tech/payment-notice", headers=T, json={"amount": 100, "note": "Havale yaptım"}); t("usta ödeme bildirir (%s)" % n.status_code, n.status_code == 200)
    # usta yetkileri
    t("usta müşteri silemez", c.delete("/api/customers/x", headers=T).status_code in (401, 403))
    t("usta kasa özetini göremez", c.get("/api/cash/summary", headers=T).status_code == 403)
    t("usta ekip ekleyemez", c.post("/api/technicians", headers=T, json={"email": "x@y.com", "password": "123456", "name": "x"}).status_code == 403)
    t("usta parça ekleyemez", c.post("/api/parts", headers=T, json={"name": "x"}).status_code == 403)
    t("usta ayarları değiştiremez", c.put("/api/settings", headers=T, json={"company_name": "Hacker"}).status_code == 403)
    t("usta iş silemez", c.delete("/api/jobs/" + jid, headers=T).status_code == 403)
    tq = c.post("/api/quotes", headers=T, json={"customer_name": "Teklif Müşteri", "customer_phone": "05320001122", "target_total": 1000, "labor_fee": 200, "parts": [{"name": "P", "weight": 1}]}); t("usta teklif hazırlar", tq.status_code == 200 and tq.json()["parts"][0]["amount"] == 800)
    ap = c.post("/api/appointments", headers=T, json={"title": "Keşif", "start_at": "2099-01-01T10:00", "technician_id": me["id"]}); t("usta randevu ekler", ap.status_code == 200)
    # başka firmanın verisi sızmaz
    d2 = c.post("/api/public/demo", json={"name": "Baska Firma", "phone": "05331112211", "sector": "klima"}).json()
    H2 = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": d2["email"], "password": d2["password"]}).json()["token"]}
    t("başka firma bu işi göremez", c.get("/api/jobs/" + jid, headers=H2).status_code == 404)
    t("başka firma ustayı listede görmez", not any(x["id"] == me["id"] for x in c.get("/api/technicians", headers=H2).json()))
    t("usta başka firmanın işine erişemez", c.get("/api/jobs", headers=T).status_code == 200 and not any(j["customer_name"] == "Baska" for j in c.get("/api/jobs", headers=T).json()))
print("OK", ok, "FAIL", bad)
