"""Kurumsal paket: bakım/garanti, teklif, bayi, QR, otomatik atama, canlı takip kapıları; yakında listesi."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:300]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
GATED = ["/api/maintenance/due", "/api/warranty-claims", "/api/quotes", "/api/dealers", "/api/qr/devices", "/api/autoassign/settings", "/api/admin/tech-locations"]
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    def a():
        r = c.get("/api/admin/packages", headers=A).json()
        k = r["packages"]["kurumsal"]; assert set(["bakim", "teklif", "bayi", "qr", "atama", "takip"]) <= set(k["modules"])
        assert set(r["soon"]) >= {"odeme", "efatura", "portal"} and not (set(r["soon"]) & set(r["modules"]))
    t("Kurumsal paket tanımlı; yakında modülleri atanabilir listede yok", a)
    def b():
        for k, n in (("tam", "Tam Firma"), ("kurumsal", "Kurumsal Firma")):
            r = c.post("/api/admin/firms", headers=A, json={"name": n, "email": f"{k}@k.com", "password": "sifre12345", "package": k}); assert r.status_code == 200, r.text
            S[k] = tok(c, f"{k}@k.com", "sifre12345")
        for u in GATED:
            r = c.get(u, headers=S["tam"]); assert r.status_code == 403 and "paketinizde yok" in r.text, (u, r.status_code)
    t("Tam Paket'te Kurumsal modüller kilitli (7 uç 403)", b)
    def d():
        for u in GATED:
            r = c.get(u, headers=S["kurumsal"]); assert r.status_code != 403, (u, r.status_code, r.text[:100])
    t("Kurumsal pakette aynı uçlar açık", d)
    def e():
        r = c.get("/api/firm/package", headers=S["tam"]).json(); assert "bakim" in r["locked"] and "odeme" in r["soon"]
        r = c.get("/api/firm/package", headers=S["kurumsal"]).json(); assert "bakim" not in r["locked"] and "teklif" not in r["locked"]
    t("firma paket bilgisinde kilitli ve yakında listeleri doğru", e)
    def f():
        assert c.get("/api/jobs", headers=S["tam"]).status_code == 200 and c.get("/api/cash", headers=S["tam"]).status_code != 403
    t("mevcut modüller etkilenmedi", f)
print(f"GEÇTİ {len(ok)}/{len(ok)+len(bad)}")
for a in bad: print("BAŞARISIZ", a)
