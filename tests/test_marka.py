"""Marka: müşteri sayfaları (portal/ödeme/teklif) firmanın temasını kullanır; firmalar birbirini görmez."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:300]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
def path(u): return re.sub(r"^https?://[^/]+", "", u)
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    for k in ("x", "y"):
        r = c.post("/api/admin/firms", headers=A, json={"name": k.upper() + " Servis", "email": f"{k}@m.com", "password": "sifre12345", "package": "kurumsal"}); assert r.status_code == 200, r.text
        S[k] = tok(c, f"{k}@m.com", "sifre12345")
    def a():
        r = c.get("/api/brand", headers=S["x"]).json()
        assert r["brand"]["accent"] == "#f27a1a" and len(r["themes"]) == 30
        assert {"slug", "dark", "accent", "radius", "sector"} <= set(r["themes"][0])
    t("varsayılan marka + 30 tema listesi", a)
    def b():
        r = c.put("/api/brand", headers=S["x"], json={"theme": "08-kombi-kor", "dark": "#15171c", "accent": "#ffc400", "radius": 6}); assert r.status_code == 200, r.text
        assert c.get("/api/brand", headers=S["x"]).json()["brand"]["accent"] == "#ffc400"
    t("marka kaydedilir ve geri okunur", b)
    def d():
        for body in ({"dark": "kırmızı", "accent": "#fff"}, {"dark": "#000000", "accent": "#12345", "radius": 9}, {"theme": "yok-boyle", "dark": "#000000", "accent": "#ffffff"}, {"dark": "#000000", "accent": "#ffffff", "radius": "x"}):
            assert c.put("/api/brand", headers=S["x"], json=body).status_code == 422, body
        with TestClient(s.app) as c2: assert c2.put("/api/brand", json={"dark": "#000000", "accent": "#ffffff"}).status_code in (401, 403)
    t("geçersiz renk/tema/köşe 422, girişsiz 401", d)
    def e():
        lx = path(c.get("/api/portal-admin/link", headers=S["x"]).json()["url"]); ly = path(c.get("/api/portal-admin/link", headers=S["y"]).json()["url"])
        hx, hy = c.get(lx).text, c.get(ly).text
        assert "--or:#ffc400" in hx and "--hd:#15171c" in hx and "--rd:6px" in hx and "--on-or:#1b1b1b" in hx, hx[:900]
        assert "--or:#f27a1a" in hy and "#ffc400" not in hy
    t("portal sayfası firmanın rengiyle açılır; diğer firma etkilenmez (açık renkte koyu yazı)", e)
    def f():
        assert c.put("/api/brand", headers=S["y"], json={"theme": "", "dark": "#0b1420", "accent": "#14c27e", "radius": 14}).status_code == 200
        ly = path(c.get("/api/portal-admin/link", headers=S["y"]).json()["url"])
        h = c.get(ly).text; assert "--or:#14c27e" in h and "--on-or:#fff" in h
        assert "#ffc400" not in h
    t("ikinci firma kendi temasını alır", f)
    def g():
        lx = path(c.get("/api/portal-admin/link", headers=S["x"]).json()["url"])
        assert '<span id="fn">X Servis</span>' in c.get(lx).text and '<i id="mk">X</i>' in c.get(lx).text and "noindex" in c.get(lx).text
    t("marka işareti ve noindex duruyor", g)
    def h():
        r = c.get("/api/brand/site/07-kombi-kizil", headers=S["x"]); assert r.status_code == 200
        assert "__PORTAL_URL__" not in r.text and "/portal/" in r.text and r.text.count("~giris") >= 4
        assert c.get("/api/brand/site/..%2f..%2fetc", headers=S["x"]).status_code == 404
    t("tema sayfasında portal bağlantısı firmaya özel doldurulur", h)
print(f"GEÇTİ {len(ok)}/{len(ok)+len(bad)}")
for a in bad: print("BAŞARISIZ", a)
