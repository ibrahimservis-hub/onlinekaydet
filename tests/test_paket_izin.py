"""Sahip paneli: firma bazlı paket izinleri (sektör/modül/rapor/entegrasyon/bölüm)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-900:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Izin Firma", "email": "iz@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "iz@x.com", "sifre12345")
    c.post("/api/yp/sectors/eticaret", headers=O)
    def izin():
        g = c.get("/api/admin/firms/%s/yp-izin" % F, headers=A).json()
        assert g["katalog"]["reports"] and g["katalog"]["integrations"] and g["katalog"]["blocks"] and g["izin"]["reports_allowed"] is None
        tum = c.get("/api/yp/rapor", headers=O).json()["items"]; assert len(tum) > 2
        keep = [tum[0]["id"]]
        p = c.put("/api/admin/firms/%s/yp-izin" % F, headers=A, json={"reports_allowed": keep + ["yok_boyle_rapor"], "integrations_allowed": ["sms_netgsm"] if False else []}); assert p.status_code == 200, p.text
        assert p.json()["izin"]["reports_allowed"] == keep
        assert [x["id"] for x in c.get("/api/yp/rapor", headers=O).json()["items"]] == keep
        assert c.get("/api/yp/rapor/%s" % tum[1]["id"], headers=O).status_code == 403
        assert c.get("/api/yp/integrations", headers=O).json()["items"] == []
        assert c.put("/api/admin/firms/%s/yp-izin" % F, headers=A, json={"reports_allowed": None, "integrations_allowed": None}).status_code == 200
        assert len(c.get("/api/yp/rapor", headers=O).json()["items"]) == len(tum)
        assert c.put("/api/admin/firms/%s/yp-izin" % F, headers=A, json={"reports_allowed": "x"}).status_code == 422
        assert c.put("/api/admin/firms/%s/yp-izin" % F, headers=O, json={"reports_allowed": []}).status_code in (401, 403)
    t("sahip: firma bazlı rapor/entegrasyon izni, sıfırlama, doğrulama, yetki", izin)
print("ok", len(ok), "bad", len(bad))
for n, e in bad: print("FAIL", n, "\n", e)
