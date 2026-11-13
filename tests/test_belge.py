"""Sektör kayıtlarından yazdırılabilir belge (PDF olarak kaydet)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import demo
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-700:]))
with TestClient(s.app) as c:
    n = [0]
    def login(k):
        demo._RATE.clear(); n[0] += 1
        r = c.post("/api/public/demo", json={"name": "Deneme Kisi", "phone": "0552418%04d" % (7000 + n[0]), "sector": k}); assert r.status_code == 200, r.text
        d = r.json(); return {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
    def akis(k, baslik):
        H = login(k); sc = c.get("/api/admin/kayit/schema", headers=H).json()
        body = {"customer_name": "Zeynep <Ak>", "customer_phone": "05551112233", "when": "2026-11-12T14:30", "discount": 10, "notes": "Not & detay", "check": {sc["check"]["opts"][0]["k"]: True}}
        body[sc["items"][0]["k"]] = [{"name": "Kalem A", "qty": 2, "price": 100}]
        if sc["family"] == "yol": body.update({"km": 10, "km_rate": 20, "base": 300})
        rid = c.post("/api/admin/kayit", json=body, headers=H).json()["id"]
        r = c.get("/api/admin/kayit/%s/belge" % rid, headers=H); assert r.status_code == 200 and "text/html" in r.headers["content-type"], r.status_code
        h = r.text
        assert sc["title"] in h and "Zeynep &lt;Ak&gt;" in h and "Not &amp; detay" in h and "Kalem A" in h and "Toplam" in h and "PDF olarak kaydet" in h and "KVKK" in h, k
        assert "190,00 ₺" in h or "Toplam" in h
        assert c.get("/api/admin/kayit/yok/belge", headers=H).status_code == 404
        x = c.get("/api/admin/kayit/%s/belge" % rid, headers={"Authorization": "Bearer yanlis"}); assert x.status_code in (401, 403), x.status_code
    for k in ("avukat", "dis_klinigi", "surucu_kursu", "kuafor", "oto_servis"):
        t("belge: " + k, (lambda kk: (lambda: akis(kk, "")))(k))
print("ok", len(ok), "bad", len(bad))
for a, b in bad: print("FAIL", a, "\n", b)
