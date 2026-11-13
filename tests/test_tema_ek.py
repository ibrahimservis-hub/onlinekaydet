"""Hazır tema + bölüm kütüphanesi: temaya bölüm ekle, sırala, gizle, düzenle, kaldır."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-1200:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Ek Firma", "email": "ek@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "ek@x.com", "sifre12345")
    async def setup():
        f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
        await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": "p01-cine-kombi"}}, upsert=True)
        await s.db.main().firm_domains.insert_one({"id": "ek1", "domain": "ek-test.com", "firm_id": F, "db": f["db"], "status": "yayinda"})
    c.portal.call(setup)
    import domains; domains._cache["t"] = 0
    def get(p="/"): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers={"Host": "ek-test.com"})
    S = {}
    def ekle():
        assert c.post("/api/yp/tema-ek", headers=O).json()["pid"] == "tema-ek"
        assert all(p["id"] != "tema-ek" for p in c.get("/api/yp/pages", headers=O).json()["rows"]), "gizli kap sayfa listesinde görünmez"
        cards = c.get("/api/yp/blocks", headers=O).json()["rows"]
        bid = "sayilarla" if any(x["id"] == "sayilarla" for x in cards) else cards[0]["id"]
        r = c.post("/api/yp/pages/tema-ek/blocks", headers=O, json={"bid": bid}); assert r.status_code == 200, r.text
        S["iid"], S["name"] = r.json()["iid"], r.json()["name"]
        assert 'class="okek"' not in get().text, "boş eklenen bölüm sitede görünmez"
        assert any(b.get("ek") == S["iid"] for b in c.get("/api/site/blocks", headers=O).json()["blocks"]), "boşken de panel listesinde"
        assert c.put("/api/yp/pages/tema-ek/blocks/%s" % S["iid"], headers=O, json={"set": {"title": "Rakamlarla Biz", "items": "1500|Mutlu müşteri\n12|Yıl"}}).status_code == 200
        bl = c.get("/api/site/blocks", headers=O).json()["blocks"]
        ek = [b for b in bl if b.get("ek") == S["iid"]]; assert ek and ek[0]["name"].startswith("Ek · ") and not ek[0]["hidden"], bl[-3:]
        S["nm"] = ek[0]["name"]; S["names"] = [b["name"] for b in bl]
        h = get().text; assert 'class="okek"' in h and 'id="okek-css"' in h and h.index('class="okek"') < h.rindex("</footer>") if "</footer>" in h else True
        assert get("/__tema-ek").status_code == 404, "gizli kap ayrı sayfa olarak yayında değil"
    t("temaya kütüphaneden bölüm eklenir, sitede ve bölüm listesinde görünür", ekle)
    def sira_gizle():
        prof = c.get("/api/site/profile", headers=O).json()
        p = prof.get("profile") or prof
        order = [S["nm"]] + [n for n in S["names"] if n != S["nm"]]
        p = dict(p, layout={"order": order, "hidden": [S["names"][0] if S["names"][0] != S["nm"] else S["names"][1]]})
        assert c.put("/api/site/profile", headers=O, json=p).status_code == 200
        bl = c.get("/api/site/blocks", headers=O).json()["blocks"]; assert bl[0]["name"] == S["nm"], [b["name"] for b in bl][:3]
        p["layout"] = {"order": order, "hidden": [S["nm"]]}
        c.put("/api/site/profile", headers=O, json=p)
        assert 'class="okek"' not in get().text, "gizlenen ek bölüm yayında yok"
        p["layout"] = {"order": order, "hidden": []}; c.put("/api/site/profile", headers=O, json=p)
        assert 'class="okek"' in get().text
    t("eklenen bölüm tema bölümleriyle birlikte sıralanır ve gizlenir", sira_gizle)
    def duzen_sil():
        r = c.put("/api/yp/pages/tema-ek/blocks/%s" % S["iid"], headers=O, json={"set": {"items": "777|Özel Rakamım"}})
        assert r.status_code == 200 and "Özel Rakamım" in get().text
        assert c.put("/api/yp/pages/tema-ek", headers=O, json={"title": "x"}).status_code == 422
        assert c.delete("/api/yp/pages/tema-ek", headers=O).status_code == 422
        assert c.delete("/api/yp/pages/tema-ek/blocks/%s" % S["iid"], headers=O).json()["ok"]
        assert 'class="okek"' not in get().text and not any(b.get("ek") for b in c.get("/api/site/blocks", headers=O).json()["blocks"])
    t("eklenen bölüm düzenlenir ve kaldırılır; kap silinemez", duzen_sil)
print("ok", len(ok), "bad", len(bad))
for n, e in bad: print("FAIL", n, "\n", e)
