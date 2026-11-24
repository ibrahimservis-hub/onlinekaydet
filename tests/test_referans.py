"""Referanslar: logo ekleme, genel liste, görsel sunumu, düzenleme, sıra, kapatma, silme, güvenlik."""
import sys, os, base64
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:500]))
PNG = "data:image/png;base64," + base64.b64encode(bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63f8ffff3f0005fe02fea7d6054d0000000049454e44ae426082")).decode()
with TestClient(s.app) as c:
    r = c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}); A = {"Authorization": "Bearer " + r.json()["token"]}
    t("boş liste", lambda: (lambda j: None if j == [] else (_ for _ in ()).throw(AssertionError(j)))(c.get("/api/public/referanslar").json()["logolar"]))
    def ekle():
        r = c.post("/api/admin/referans", json={"name": "Örnek A.Ş.", "link": "https://ornek.com", "image": PNG}, headers=A); assert r.status_code == 200, r.text; S["a"] = r.json()["id"]
        r = c.post("/api/admin/referans", json={"name": "İkinci Marka", "image": PNG}, headers=A); assert r.status_code == 200; S["b"] = r.json()["id"]
    t("iki logo eklenir", ekle)
    def liste():
        j = c.get("/api/public/referanslar").json()["logolar"]; assert [x["name"] for x in j] == ["Örnek A.Ş.", "İkinci Marka"], j; assert "data" not in j[0] and j[0]["src"].startswith("/api/public/referans/")
        g = c.get(j[0]["src"]); assert g.status_code == 200 and g.headers["content-type"] == "image/png" and g.content[:4] == b"\x89PNG", g.status_code
        assert "max-age" in g.headers["cache-control"] and g.headers["x-content-type-options"] == "nosniff"
    t("genel liste ve görsel", liste)
    def kotu():
        assert c.post("/api/admin/referans", json={"name": "x", "image": PNG}, headers=A).status_code == 422
        assert c.post("/api/admin/referans", json={"name": "Marka", "image": "data:text/html;base64,PGI+"}, headers=A).status_code == 422
        svg = "data:image/svg+xml;base64," + base64.b64encode(b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>").decode()
        assert c.post("/api/admin/referans", json={"name": "Marka", "image": svg}, headers=A).status_code == 422
        big = "data:image/png;base64," + base64.b64encode(b"0" * 310000).decode()
        assert c.post("/api/admin/referans", json={"name": "Marka", "image": big}, headers=A).status_code == 422
        assert TestClient(s.app).post("/api/admin/referans", json={"name": "Marka", "image": PNG}).status_code in (401, 403)
    t("geçersiz dosya, küçük ad, büyük dosya ve yetkisiz reddedilir", kotu)
    def sirala():
        assert c.post("/api/admin/referans/%s/tasi" % S["b"], json={"yon": "yukari"}, headers=A).status_code == 200
        assert [x["name"] for x in c.get("/api/public/referanslar").json()["logolar"]] == ["İkinci Marka", "Örnek A.Ş."]
    t("sıra değişir", sirala)
    def duzenle():
        assert c.put("/api/admin/referans/" + S["a"], json={"name": "Yeni Ad", "active": False}, headers=A).status_code == 200
        assert [x["name"] for x in c.get("/api/public/referanslar").json()["logolar"]] == ["İkinci Marka"]
        assert c.get("/api/public/referans/%s/logo" % S["a"]).status_code == 404
        j = c.get("/api/admin/referans", headers=A).json()["logolar"]; assert len(j) == 2 and all("data" not in x for x in j)
        assert c.put("/api/admin/referans/" + S["a"], json={"image": PNG}, headers=A).status_code == 200
        assert c.get("/api/admin/referans", headers=A).json()["logolar"][1]["v"] == 2
    t("kapatma, düzenleme, görsel yenileme", duzenle)
    def sil():
        assert c.delete("/api/admin/referans/" + S["a"], headers=A).status_code == 200
        assert len(c.get("/api/admin/referans", headers=A).json()["logolar"]) == 1
    t("silme", sil)
print("GEÇTİ", len(ok), "KALDI", len(bad))
for b in bad: print(" -", b)
sys.exit(1 if bad else 0)
