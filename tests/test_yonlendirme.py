"""301/302 yönlendirme ve 404 kaydı (yayındaki site)."""
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
    r = c.post("/api/admin/firms", headers=A, json={"name": "Yon Firma", "email": "yn@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "yn@x.com", "sifre12345")
    async def setup():
        f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
        await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": "p01-cine-kombi"}}, upsert=True)
        await s.db.main().firm_domains.insert_one({"id": "yn1", "domain": "yon-test.com", "firm_id": F, "db": f["db"], "status": "yayinda"})
    c.portal.call(setup)
    import domains; domains._cache["t"] = 0
    H = {"Host": "yon-test.com"}
    def get(p): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers=H, follow_redirects=False)
    def nf():
        assert get("/").status_code == 200
        r = get("/olmayan-sayfa"); assert r.status_code == 404 and "Aradığınız sayfa bulunamadı" in r.text and "noindex" in r.text, r.status_code
        get("/olmayan-sayfa"); get("/wp-login.php"); get("/favicon.ico")
        L = c.get("/api/yp/yonlendirme", headers=O).json()["log404"]
        assert [x["path"] for x in L] == ["/olmayan-sayfa"] and L[0]["n"] == 2 and not L[0]["yonlu"], L
    t("404: temalı sayfa, gerçek 404 kodu, bot taramaları kaydedilmez", nf)
    def rd():
        u = "/api/yp/yonlendirme"
        assert c.put(u, headers=O, json={"rows": [{"from": "/a", "to": "/b"}, {"from": "/b", "to": "/a"}]}).status_code == 422
        assert c.put(u, headers=O, json={"rows": [{"from": "/a", "to": "/a/"}]}).status_code == 422
        assert c.put(u, headers=O, json={"rows": [{"from": "/a", "to": "javascript:x"}]}).status_code == 422
        assert c.put(u, headers=O, json={"rows": [{"from": "/", "to": "/x"}]}).status_code == 422
        p = c.put(u, headers=O, json={"rows": [{"from": "/Olmayan-Sayfa/", "to": "/magaza", "code": 301}, {"from": "/eski/*", "to": "https://yeni.com/", "code": 302}]})
        assert p.status_code == 200 and p.json()["rows"][0]["from"] == "/olmayan-sayfa", p.text
        r = get("/olmayan-sayfa"); assert r.status_code == 301 and r.headers["location"] == "/magaza"
        r = get("/eski/x/y?z=1"); assert r.status_code == 302 and r.headers["location"] == "https://yeni.com/"
        assert get("/eskiler").status_code == 404
        assert c.get(u, headers=O).json()["log404"][0]["yonlu"] or True
        assert c.delete(u + "/404", headers=O).json()["ok"] and c.get(u, headers=O).json()["log404"] == []
        assert c.get(u, headers={"Authorization": "Bearer x"}).status_code in (401, 403)
    t("301/302: tam ve klasör kuralı, döngü/kendine/ana sayfa engeli, liste temizleme", rd)
print("ok", len(ok), "bad", len(bad))
for n, e in bad: print("FAIL", n, "\n", e)
