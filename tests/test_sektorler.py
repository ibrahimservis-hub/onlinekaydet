"""Teknik olmayan sektörler: her sektörde demo açılır, örnek veri sektör diliyle gelir, panel terimleri uç noktadan okunur."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import sektor, sektor_ek, sektor_dil, demo
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-400:]))
KEYS = list(sektor_ek.NEW)
with TestClient(s.app) as c:
    def a():
        assert len(sektor.SECTORS) >= 16 and all(k in sektor.SECTORS for k in KEYS)
        for k, v in sektor_ek.NEW.items():
            assert (v["terms"].get("Servis Kayıtları") or not v["terms"]) and v["site"]["services"] and v["site"]["faq"] and v["checklist"] and v["faults"], k
    t("16 sektör: her yeni sektörde terim, site metni, kontrol listesi, talep listesi var", a)
    def b():
        for i, k in enumerate(KEYS):
            demo._RATE.clear(); r = c.post("/api/public/demo", json={"name": "Deneme Kisi", "phone": "0552416%04d" % (6000 + i), "sector": k}); assert r.status_code == 200, (k, r.text)
            d = r.json()
            tok = c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]
            H = {"Authorization": "Bearer " + tok}
            jobs = c.get("/api/jobs", headers=H).json(); assert len(jobs) == 7, (k, len(jobs))
            meta = sektor_ek.DEMO_META[k]
            assert jobs[0]["device_model"] == meta[0], (k, jobs[0]["device_model"])
            assert any(j["work_done"] == meta[1] for j in jobs), k
            tr = c.get("/api/sector-terms", headers=H).json()
            assert tr["key"] == k and tr["terms"].get("Servis Kayıtları", "Servis Kayıtları") == (sektor_dil.labels(k) or sektor_ek.NEW[k]["terms"]).get("Servis Kayıtları", "Servis Kayıtları") and tr["lex"].get("kisi"), (k, tr)
    t("her yeni sektörde demo açılır; örnek veri ve panel terimleri sektör dilinde", b)
    def e():
        demo._RATE.clear(); r = c.post("/api/public/demo", json={"name": "Berber Ali", "phone": "05524167001", "sector": "Berber"}); assert r.status_code == 200, r.text
        tok = c.post("/api/auth/login", json={"email": r.json()["email"], "password": r.json()["password"]}).json()["token"]
        assert c.get("/api/sector-terms", headers={"Authorization": "Bearer " + tok}).json()["key"] == "kuafor"
    t("formda 'Berber' yazınca kuaför sektörü seçilir", e)
    def f():
        demo._RATE.clear(); r = c.post("/api/public/demo", json={"name": "Teknik Usta", "phone": "05524167002", "sector": "Kombi"}); assert r.status_code == 200
        tok = c.post("/api/auth/login", json={"email": r.json()["email"], "password": r.json()["password"]}).json()["token"]
        assert c.get("/api/sector-terms", headers={"Authorization": "Bearer " + tok}).json()["terms"] == {}
    t("teknik sektörde terim değişmez", f)
    def g():
        demo._RATE.clear(); r = c.post("/api/public/demo", json={"name": "Magaza Sahibi", "phone": "05524168001", "sector": "E-ticaret"}); assert r.status_code == 200, r.text
        d = r.json(); H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
        it = c.get("/api/shop/products", headers=H); assert it.status_code == 200, it.text
        L = it.json(); L = L.get("items", L) if isinstance(L, dict) else L; assert len(L) == 8, len(L)
    t("e-ticaret demosunda 8 örnek ürün gelir", g)
print("GEÇTİ", len(ok)); [print("  ✓", x) for x in ok]
for n, e in bad: print("HATA:", n, e)
sys.exit(1 if bad else 0)
