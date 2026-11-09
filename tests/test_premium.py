"""Premium temalar: 100 tema / 70 premium, 'Teklif alın', fiyat yok, mağaza varsayılan kapalı ve editörden açılır, iç sayfalar çalışır."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-700:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ali Veli", "phone": "05524165755", "sector": "Kombi"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    ADM = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    fid = [f for f in c.get("/api/admin/firms", headers=ADM).json().get("firms", []) if f.get("demo")][0]
    async def go():
        await s.db.main().firm_domains.insert_one({"id": "d8", "domain": "premium-site.com", "firm_id": fid["id"], "db": s.db.firm_db_name(fid["id"]), "status": "yayinda"})
    c.portal.call(go)
    import domains; domains._cache["t"] = 0
    def pub(p): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers={"Host": "premium-site.com"})
    def setth(slug):
        bd = c.get("/api/brand", headers=H).json(); th = next(x for x in bd["themes"] if x["slug"] == slug)
        r = c.put("/api/brand", headers=H, json={**bd["brand"], "theme": slug, "dark": th["dark"], "accent": th["accent"]}); assert r.status_code == 200, r.text
        domains._cache["t"] = 0
    def cnt():
        th = c.get("/api/brand", headers=H).json()["themes"]
        assert len(th) == 100 and sum(1 for x in th if x.get("premium")) == 70, (len(th), sum(1 for x in th if x.get("premium")))
    t("100 tema, 70'i premium", cnt)
    def home():
        setth("p01-cine-kombi")
        r = pub("/"); assert r.status_code == 200
        h = r.text
        assert "Teklif alın" in h and "Randevu al" not in h and "₺ …" not in h and "pgb" in h
        assert 'id="urunler"' not in h and "<button class=\"crt-fab\"" not in h, "mağaza varsayılan kapalı olmalı"
        assert "905524165755" in h and "905320000000" not in h
    t("premium tema: Teklif alın, mağaza kapalı, telefon yerleşir", home)
    def blocks():
        b = c.get("/api/site/blocks", headers=H).json()["blocks"]
        m = [x for x in b if x["name"] == "Ürünler"]; assert m and m[0]["hidden"], b
    t("editörde Ürünler bölümü gizli görünür", blocks)
    def openshop():
        d = c.get("/api/site/profile", headers=H).json()["profile"]
        b = c.get("/api/site/blocks", headers=H).json()["blocks"]
        d["layout"] = {"order": [x["name"] for x in b], "hidden": [x["name"] for x in b if x["name"] != "Ürünler" and x["hidden"]]}
        assert c.put("/api/site/profile", headers=H, json=d).status_code == 200
        domains._cache["t"] = 0
        h = pub("/").text; assert 'id="urunler"' in h and "Sepet" in h
        d["layout"]["hidden"].append("Ürünler"); assert c.put("/api/site/profile", headers=H, json=d).status_code == 200
        domains._cache["t"] = 0
        assert 'id="urunler"' not in pub("/").text
    t("mağaza editörden açılır ve kapanır", openshop)
    def allp():
        for sl in ["p02-edit-klima", "p03-neon-beyaz-esya", "p04-lux-elektronik", "1-kombi"]:
            setth(sl)
            for p in ["/", "/hakkimizda", "/iletisim"]:
                r = pub(p); assert r.status_code == 200 and "Teklif alın" in r.text and ("data-spx-auto" in r.text or "<html" in r.text), (sl, p)
            assert "Randevu al" not in pub("/").text, sl
    t("4 yön + yükseltilmiş eski tema: ana ve iç sayfalar çalışır", allp)
for n in ok: print("  ok", n)
for n, e in bad: print("FAIL", n, e)
print("OK %d/%d" % (len(ok), len(ok) + len(bad)))
