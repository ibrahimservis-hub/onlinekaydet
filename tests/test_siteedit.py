"""Site düzenleyici: tema HTML'i alınır, düzenlenip kaydedilir, yeni sayfa açılır, alan adından yayınlanır, sıfırlanır."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-400:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ali Veli", "phone": "05524165755", "sector": "Klima"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    def a():
        r = c.get("/api/site/edit", headers=H); assert r.status_code == 200, r.text
        d = r.json(); assert not d["custom"] and "<html" in d["html"].lower() and "__API_URL__" not in d["html"]; S["html"] = d["html"]
    t("tema HTML'i düzenlemeye açılır (demo sektör temasıyla)", a)
    def b():
        h = S["html"].replace("</body>", "<p id=x>Özel metin ABC</p></body>", 1).replace("<body", '<body contenteditable="true" data-spx-x="1"', 1)
        r = c.put("/api/site/edit", headers=H, json={"html": h}); assert r.status_code == 200, r.text
        d = c.get("/api/site/edit", headers=H).json(); assert d["custom"] and "Özel metin ABC" in d["html"] and "contenteditable" not in d["html"] and "data-spx" not in d["html"]
    t("düzenlenmiş site kaydedilir, düzenleyici izleri temizlenir", b)
    def p():
        r = c.post("/api/site/pages", headers=H, json={"title": "Hakkımızda Çalışma Saatleri", "content": "<section><h2>Alt başlık</h2><p>x</p></section>"}); assert r.status_code == 200, r.text
        S["slug"] = r.json()["slug"]; assert S["slug"] == "hakkimizda-calisma-saatleri", S["slug"]
        r = c.post("/api/site/pages", headers=H, json={"title": "Hakkımızda Çalışma Saatleri"}); assert r.json()["slug"].endswith("-2")
        assert c.post("/api/site/pages", headers=H, json={"title": "api"}).json()["slug"] != "api"
        d = c.get("/api/site/edit?page=" + S["slug"], headers=H).json(); assert "Hakkımızda Çalışma Saatleri" in d["html"] and len([p for p in d["pages"] if not p.get("auto")]) == 3
        h = d["html"].replace("Alt başlık", "ÇOK ÖZEL ALT BAŞLIK")
        assert c.put("/api/site/edit", headers=H, json={"page": S["slug"], "html": h}).status_code == 200
    t("yeni sayfa açılır (adres benzersiz, ayrılmış adlar yok), düzenlenir", p)
    def v():
        fid = [f for f in c.get("/api/admin/firms", headers={"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}).json().get("firms", []) if f.get("demo")][0]
        async def go():
            await s.db.main().firm_domains.insert_one({"id": "d1", "domain": "test-musteri.com", "firm_id": fid["id"], "db": s.db.firm_db_name(fid["id"]), "status": "yayinda"})
        c.portal.call(go)
        import domains; domains._cache["t"] = 0
        r = c.get("/api/public/hosted-site?p=%2F", headers={"Host": "test-musteri.com"}); assert r.status_code == 200 and "Özel metin ABC" in r.text, r.text[:200]
        r = c.get("/api/public/hosted-site?p=%2F" + S["slug"], headers={"Host": "test-musteri.com"}); assert "ÇOK ÖZEL ALT BAŞLIK" in r.text, r.text[:200]
    t("düzenlenmiş ana sayfa ve yeni sayfa alan adından yayınlanır", v)
    def r_():
        assert c.delete("/api/site/edit?page=" + S["slug"], headers=H).status_code == 200
        assert c.delete("/api/site/edit", headers=H).status_code == 200
        d = c.get("/api/site/edit", headers=H).json(); assert not d["custom"] and "Özel metin ABC" not in d["html"]
    t("sayfa silinir, ana sayfa temaya sıfırlanır", r_)
    def lg():
        assert c.put("/api/site/logo", headers=H, json={"data": "data:image/png;base64,iVBORw0KGgo="}).status_code == 200
        assert c.get("/api/site/logo", headers=H).json()["data"].startswith("data:image/png")
        assert c.put("/api/site/logo", headers=H, json={"data": "javascript:alert(1)"}).status_code == 422
        assert c.get("/api/firm/logo", headers=H).status_code in (200, 404)
    t("logo yüklenir, geçersiz dosya reddedilir", lg)
    def mt():
        S["slug"] = c.post("/api/site/pages", headers=H, json={"title": "Deneme Sayfa"}).json()["slug"]
        assert c.put("/api/site/pages/" + S["slug"], headers=H, json={"title": "Yeni Ad", "slug": "yeni-ad"}).json()["slug"] == "yeni-ad"
        assert c.put("/api/site/pages/yeni-ad", headers=H, json={"slug": "api"}).status_code == 422
    t("sayfa adı/adresi değişir, ayrılmış adres reddedilir", mt)
    def g():
        assert c.put("/api/site/edit", headers=H, json={"html": "x"}).status_code == 422
        assert c.get("/api/site/edit", headers={"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}).status_code == 403
    t("geçersiz boyut 422; platform sahibi bu uca giremez", g)
print(f"GEÇTİ {len(ok)}/{len(ok)+len(bad)}")
for x in bad: print("BAŞARISIZ", x)
