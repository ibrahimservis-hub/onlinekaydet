"""Kariyer: ilan listesi, başvuru + CV yükleme, yönetimde görünme, durum, CV indirme, silme."""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"; os.environ["KARIYER_DIR"] = tempfile.mkdtemp()
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:500]))
with TestClient(s.app) as c:
    r = c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}); A = {"Authorization": "Bearer " + r.json()["token"]}
    def liste():
        j = c.get("/api/public/kariyer").json()["ilanlar"]; assert len(j) >= 6 and all(i["active"] for i in j), j; S["i"] = j[0]["id"]
    t("herkese açık ilan listesi hazır pozisyonlarla gelir", liste)
    FORM = {"name": "Ayşe Yılmaz", "email": "ayse@ornek.com", "phone": "0532 555 11 22", "city": "Ankara", "message": "Merhaba", "kvkk": "1"}
    def basvur():
        r = c.post("/api/public/kariyer/basvuru", data={**FORM, "ilan": S["i"]}, files={"cv": ("cv.pdf", b"%PDF-1.4 test", "application/pdf")}); assert r.status_code == 200, r.text
    t("CV ile başvuru kabul edilir", basvur)
    def reddet():
        assert c.post("/api/public/kariyer/basvuru", data={**FORM, "kvkk": ""}).status_code == 422
        assert c.post("/api/public/kariyer/basvuru", data={**FORM, "email": "x"}).status_code == 422
        assert c.post("/api/public/kariyer/basvuru", data=FORM, files={"cv": ("a.exe", b"MZ", "application/octet-stream")}).status_code == 422
        assert c.post("/api/public/kariyer/basvuru", data={**FORM, "ilan": "yok"}).status_code == 422
        assert c.post("/api/public/kariyer/basvuru", data={**FORM, "website": "bot"}).status_code == 200
    t("onaysız, hatalı e-posta, yasak dosya türü ve olmayan ilan reddedilir; bot tuzağı sessiz", reddet)
    def yonet():
        j = c.get("/api/admin/kariyer", headers=A).json(); assert j["sayac"]["yeni"] == 1, j["sayac"]
        b = j["basvurular"][0]; assert b["ilan"] and b["cv"]["name"] == "cv.pdf" and b["name"] == "Ayşe Yılmaz", b; S["b"] = b["id"]
        c2 = TestClient(s.app); r0 = c2.get("/api/admin/kariyer"); assert r0.status_code in (401, 403), r0.status_code
        assert c.get(f"/api/admin/kariyer/basvuru/{S['b']}/cv", headers=A).content.startswith(b"%PDF")
        r1 = c2.get(f"/api/admin/kariyer/basvuru/{S['b']}/cv"); assert r1.status_code in (401, 403), r1.status_code
        assert c.put(f"/api/admin/kariyer/basvuru/{S['b']}", headers=A, json={"status": "gorusme", "note": "Aranacak"}).status_code == 200
        assert c.get("/api/admin/kariyer?durum=gorusme", headers=A).json()["basvurular"][0]["note"] == "Aranacak"
    t("yönetimde görünür, CV yalnız yönetime iner, durum ve not kaydedilir", yonet)
    def ilan():
        r = c.post("/api/admin/kariyer/ilan", headers=A, json={"title": "Test Uzmanı", "duties": "a\nb", "reqs": ["c"]}); assert r.status_code == 200, r.text
        iid = r.json()["id"]
        assert c.put(f"/api/admin/kariyer/ilan/{iid}", headers=A, json={"active": False}).status_code == 200
        assert "Test Uzmanı" not in [i["title"] for i in c.get("/api/public/kariyer").json()["ilanlar"]]
        assert c.delete(f"/api/admin/kariyer/ilan/{iid}", headers=A).status_code == 200
        assert c.delete(f"/api/admin/kariyer/basvuru/{S['b']}", headers=A).status_code == 200
        assert c.get(f"/api/admin/kariyer/basvuru/{S['b']}/cv", headers=A).status_code == 404
    t("ilan eklenir, kapatılınca listeden kalkar; başvuru silinince CV de gider", ilan)
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" FAIL", n, e)
sys.exit(1 if bad else 0)
