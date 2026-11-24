"""Firma evrakları: yükleme, liste, indirme, not/ad düzenleme, silme, doğrulama, yetki."""
import sys, os, base64
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:500]))
PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
def b64(b): return "data:application/pdf;base64," + base64.b64encode(b).decode()
with TestClient(s.app) as c:
    r = c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}); A = {"Authorization": "Bearer " + r.json()["token"]}
    r = c.post("/api/admin/firms", json={"name": "Evrak Firma", "email": "ev@ornek.com", "password": "Sifre123!"}, headers=A); S["f"] = r.json()["id"]
    U = "/api/admin/firms/%s/evrak" % S["f"]
    def yukle():
        r = c.post(U, json={"tur": "imzali_sozlesme", "dosya": "sozlesme imzali.pdf", "data": b64(PDF), "not": "Müşteri imzaladı"}, headers=A); assert r.status_code == 200, r.text
        j = r.json(); S["e"] = j["id"]; assert j["tur_ad"] == "İmzalı sözleşme" and j["ad"] == "İmzalı sözleşme" and j["boyut"] == len(PDF) and "data" not in j
        r = c.post(U, json={"tur": "vergi_levhasi", "dosya": "levha.PNG", "data": "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\n0000").decode(), "ad": "Vergi levhası 2026"}, headers=A); assert r.status_code == 200, r.text
    t("evrak yüklenir", yukle)
    def liste():
        j = c.get(U, headers=A).json(); assert len(j["items"]) == 2 and all("data" not in x for x in j["items"]) and "imzali_sozlesme" in j["turler"]
    t("liste (veri dönmez)", liste)
    def indir():
        r = c.get("/api/admin/evrak/%s/indir" % S["e"], headers=A); assert r.status_code == 200 and r.content == PDF and r.headers["content-type"] == "application/pdf"
        assert "attachment" in r.headers["content-disposition"] and r.headers["x-content-type-options"] == "nosniff"
    t("indirme aynı baytlar", indir)
    def kotu():
        assert c.post(U, json={"dosya": "x.exe", "data": b64(PDF)}, headers=A).status_code == 422
        assert c.post(U, json={"dosya": "x.pdf", "data": b64(b"<html>hi</html>")}, headers=A).status_code == 422
        assert c.post(U, json={"dosya": "x.pdf", "data": ""}, headers=A).status_code == 422
        assert c.post(U, json={"dosya": "x.pdf", "data": b64(PDF + b"0" * (6 * 1024 * 1024))}, headers=A).status_code == 413
        assert c.post("/api/admin/firms/yok/evrak", json={"dosya": "x.pdf", "data": b64(PDF)}, headers=A).status_code == 404
    t("hatalı dosyalar reddedilir", kotu)
    def duzenle():
        assert c.put("/api/admin/evrak/%s" % S["e"], json={"not": "Asıl kargoda", "ad": "İmzalı sözleşme (kaşeli)", "tur": "diger"}, headers=A).status_code == 200
        x = [i for i in c.get(U, headers=A).json()["items"] if i["id"] == S["e"]][0]; assert x["not"] == "Asıl kargoda" and x["ad"] == "İmzalı sözleşme (kaşeli)" and x["tur"] == "diger"
        assert c.put("/api/admin/evrak/yok", json={"not": "x"}, headers=A).status_code == 404
    t("not ve ad düzenlenir", duzenle)
    def yetki():
        n = TestClient(s.app)
        for m, u in (("get", U), ("post", U), ("get", "/api/admin/evrak/%s/indir" % S["e"]), ("delete", "/api/admin/evrak/%s" % S["e"])):
            assert getattr(n, m)(u).status_code in (401, 403), (m, u)
    t("giriş yapılmadan erişilemez", yetki)
    def sil():
        assert c.delete("/api/admin/evrak/%s" % S["e"], headers=A).status_code == 200
        assert c.get("/api/admin/evrak/%s/indir" % S["e"], headers=A).status_code == 404 and len(c.get(U, headers=A).json()["items"]) == 1
    t("silme", sil)
print("OK %d geçti" % len(ok) if not bad else "FAIL", *bad, sep="\n")
