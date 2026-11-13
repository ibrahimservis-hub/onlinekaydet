"""Hazır tema: üst menü / mobil menü / mobil alt çubuk + tüm tema tasarımı."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-1500:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
THEMES = ["p01-cine-kombi", "k5-atolye-kuafor", "n13-lux-kuafor", "07-kombi-kizil"]
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Nav Firma", "email": "nv@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "nv@x.com", "sifre12345")
    async def setup():
        f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
        await s.db.main().firm_domains.insert_one({"id": "nv1", "domain": "nv-test.com", "firm_id": F, "db": f["db"], "status": "yayinda"})
        S["db"] = f["db"]
    S = {}; c.portal.call(setup)
    import domains; domains._cache["t"] = 0
    async def settheme(th): await s.db.firm(S["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": th}}, upsert=True)
    def get(p="/"): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers={"Host": "nv-test.com"})
    def ogren():
        for th in THEMES:
            c.portal.call(settheme, th)
            d = c.get("/api/site/nav-design", headers=O).json()
            assert d["has_theme"] and d["tema"]["bar"], (th, d["tema"])
            assert "drw" in d["tema"], th
    t("tema öğeleri (alt çubuk öğeleri, çekmece) okunur", ogren)
    def varsayilan():
        c.portal.call(settheme, "p01-cine-kombi")
        h = get().text
        assert "data-oknav" not in h and 'id="oktw"' not in h, "ayar yokken tema olduğu gibi"
    t("ayar yokken site değişmez", varsayilan)
    def tw():
        for th in THEMES:
            c.portal.call(settheme, th)
            r = c.put("/api/site/nav-design", headers=O, json={"tw": {"ac": "#c2185b", "dk": "#1a1a2e", "fd": "Playfair Display", "fb": "Inter", "kose": "keskin", "dugme": "hap", "x": "<script>"}})
            assert r.status_code == 200
            h = get().text
            assert 'id="oktw"' in h and "--ac:#c2185b!important" in h and "--on-ac:#ffffff" in h and "Playfair+Display" in h, th
            assert "<script>" not in h.split('id="oktw"')[1].split("</style>")[0]
        d = c.get("/api/site/nav-design", headers=O).json()["tw"]; assert d["ac"] == "#c2185b" and d["kose"] == "keskin"
        c.put("/api/site/nav-design", headers=O, json={"tw": {"ac": "javascript:1", "fd": "Comic Evil"}})
        assert 'id="oktw"' not in get().text, "geçersiz değerler elenir"
    t("tüm tema renk/yazı/köşe/düğme uygulanır, geçersiz elenir", tw)
    def nav():
        c.portal.call(settheme, "p01-cine-kombi")
        d = c.get("/api/site/nav-design", headers=O).json()
        items = d["tema"]["bar"]
        n = {"ust": {"bg": "#101820", "fg": "#ffffff", "sticky": "static"}, "drw": {"bg": "#202a30", "fg": "#f5f5f5", "boyut": 22},
             "bar": {"bg": "#101820", "fg": "#ffffff", "ac": "#ffb300", "edit": {str(items[0]["i"]): {"l": "Hemen Ara"}}, "extra": [{"l": "Konum", "h": "/iletisim", "ic": "konum"}]}}
        assert c.put("/api/site/nav-design", headers=O, json={"nav": n}).status_code == 200
        h = get().text
        assert 'data-oknav="ust"' in h and 'data-oknav="drw"' in h and 'data-oknav="bar"' in h
        assert "#101820" in h and "Hemen Ara" in h and "Konum" in h
        c.put("/api/site/nav-design", headers=O, json={"nav": {"bar": {"off": True}}})
        assert 'data-oknav="bar"' not in get().text
        c.put("/api/site/nav-design", headers=O, json={"nav": {}})
        assert "data-oknav" not in get().text
    t("üst menü / çekmece / alt çubuk tasarımı uygulanır ve sıfırlanır", nav)
    def profil_korur():
        c.put("/api/site/nav-design", headers=O, json={"tw": {"ac": "#c2185b"}, "nav": {"drw": {"bg": "#202a30"}}})
        p = c.get("/api/site/profile", headers=O).json()["profile"]
        assert c.put("/api/site/profile", headers=O, json=p).status_code == 200
        d = c.get("/api/site/nav-design", headers=O).json()
        assert d["tw"]["ac"] == "#c2185b" and d["nav"]["drw"]["bg"] == "#202a30"
    t("profil kaydı tasarım ayarlarını silmez", profil_korur)
    def alt_sayfa():
        c.portal.call(settheme, "p01-cine-kombi")
        c.put("/api/site/nav-design", headers=O, json={"tw": {"ac": "#c2185b"}, "nav": {}})
        r = get("/hakkimizda")
        print("alt sayfa", r.status_code, 'id="oktw"' in r.text)
    t("alt sayfa bilgisi", alt_sayfa)
print("OK", len(ok), "FAIL", len(bad))
for n, e in bad: print("---", n, e)
