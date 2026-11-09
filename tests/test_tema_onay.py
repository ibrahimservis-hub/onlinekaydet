"""Premium temalar: platform sahibi onaylamadan firma göremez ve seçemez."""
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
    r = c.post("/api/admin/firms", headers=A, json={"name": "Tema Firma", "email": "tf@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "tf@x.com", "sifre12345")
    def th(h): return c.get("/api/brand", headers=h).json()
    prem = next(x["slug"] for x in th(A)["themes"] if x.get("premium")); free = next(x["slug"] for x in th(A)["themes"] if not x.get("premium"))
    def hidden():
        j = th(O); assert j["premium_ok"] is False and not any(x.get("premium") for x in j["themes"]), "onaysız firma premium temayı görmemeli"
        assert any(not x.get("premium") for x in j["themes"])
    t("onaysız firma premium temaları listede görmez", hidden)
    def blocked():
        r = c.put("/api/brand", headers=O, json={"theme": prem}); assert r.status_code == 403, r.text
        r = c.put("/api/brand", headers=O, json={"theme": free}); assert r.status_code == 200, r.text
    t("onaysız firma premium temayı seçemez, ücretsiz seçebilir", blocked)
    def approved():
        assert c.put(f"/api/admin/firms/{F}", headers=A, json={"premium_themes": True}).status_code == 200
        j = th(O); assert j["premium_ok"] and any(x.get("premium") for x in j["themes"])
        assert c.put("/api/brand", headers=O, json={"theme": prem}).status_code == 200
    t("sahip onaylayınca premium görünür ve seçilir", approved)
    def revoke():
        assert c.put(f"/api/admin/firms/{F}", headers=A, json={"premium_themes": False}).status_code == 200
        j = th(O); assert [x["slug"] for x in j["themes"] if x.get("premium")] == [prem], "seçili tema korunur, diğer premium gizlenir"
    t("onay kaldırılınca mevcut tema kalır, diğer premium gizlenir", revoke)
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" FAIL", n, e)
sys.exit(1 if bad else 0)
