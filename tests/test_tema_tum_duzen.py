"""Bütün hazır temalar: her bölümün yazısı düzenlenir, bölüm gizlenir/geri açılır, kütüphaneden bölüm eklenir/silinir."""
import sys, os, re, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; import kurumsal as K, domains
only = sys.argv[1:] 
bad = []; stat = {"tema": 0, "bolum": 0, "yazi": 0}
with TestClient(s.app) as c:
    def tok(e, p): return {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": e, "password": p}).json()["token"]}
    A = tok("admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Tum Duzen", "email": "td@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok("td@x.com", "sifre12345")
    async def setup():
        f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1}); S = s.db.firm(f["db"])
        await S.app_settings.update_one({"_id": "brand"}, {"$set": {"theme": K.THEMES[0]["slug"]}}, upsert=True)
        await s.db.main().firm_domains.insert_one({"id": "td1", "domain": "td-test.com", "firm_id": F, "db": f["db"], "status": "yayinda"})
        return f["db"]
    DB = c.portal.call(setup)
    async def tema(slug):
        S = s.db.firm(DB)
        await S.app_settings.update_one({"_id": "brand"}, {"$set": {"theme": slug}}, upsert=True)
        await S.app_settings.delete_one({"_id": "site_profile"}); await S.yp_pages.delete_many({"id": "tema-ek"})
    domains._cache["t"] = 0
    def get(): return c.get("/api/public/hosted-site?p=%2F", headers={"Host": "td-test.com"})
    c.post("/api/yp/tema-ek", headers=O)
    cards = c.get("/api/yp/blocks", headers=O).json()["rows"]
    for th in K.THEMES:
        sl = th["slug"]
        if only and not any(o in sl for o in only): continue
        def fail(m): bad.append((sl, m)); print("  ✗", sl, m[:200])
        try:
            c.portal.call(tema, sl); domains._cache["t"] = 0; c.post("/api/yp/tema-ek", headers=O)
            bl = c.get("/api/site/blocks", headers=O)
            if bl.status_code != 200: fail("blocks %s %s" % (bl.status_code, bl.text[:100])); continue
            bl = bl.json()["blocks"]
            if len(bl) < 3: fail("az bölüm %d" % len(bl)); continue
            h0 = get(); 
            if h0.status_code != 200: fail("site %s" % h0.status_code); continue
            # 1) her bölümde ilk yazıyı değiştir
            ed = {}; mk = {}
            for bi, b in enumerate(bl):
                r = c.get("/api/site/block-text", params={"name": b["name"]}, headers=O)
                if r.status_code != 200: fail("block-text %s %s" % (b["name"], r.status_code)); continue
                tx = r.json()["texts"]
                if not tx: continue
                x = tx[0]; m = "ZQ%dX%d" % (bi, len(sl)); ed.setdefault(b["name"], {})[str(x["i"])] = m; mk[b["name"]] = m
            pr = c.get("/api/site/profile", headers=O).json()["profile"]; pr["edits"] = {sl: ed}
            r = c.put("/api/site/profile", headers=O, json=pr)
            if r.status_code != 200: fail("profile put %s" % r.text[:100]); continue
            h = get().text
            miss = [n for n, m in mk.items() if m not in h and not next(b for b in bl if b["name"] == n)["hidden"]]
            if miss: fail("yazı sitede yok: %s" % miss[:4])
            stat["yazi"] += len(mk) - len(miss)
            # 2) gizle (ilk dışındaki görünür bölümler) ve geri aç
            vis = [b["name"] for b in bl if not b["hidden"] and b["name"] in mk]
            hide = vis[1:4]
            pr = c.get("/api/site/profile", headers=O).json()["profile"]; pr["layout"] = {"order": [], "hidden": hide}
            c.put("/api/site/profile", headers=O, json=pr); h = get().text
            still = [n for n in hide if mk[n] in h]
            if still: fail("gizlenen bölüm hâlâ sitede: %s" % still)
            pr["layout"] = {"order": [], "hidden": []}; c.put("/api/site/profile", headers=O, json=pr); h = get().text
            back = [n for n in hide if mk[n] not in h]
            if back: fail("geri açılan bölüm yok: %s" % back)
            # 3) sırayı tersine çevir
            names = [b["name"] for b in c.get("/api/site/blocks", headers=O).json()["blocks"]]
            pr["layout"] = {"order": names[::-1], "hidden": []}; r = c.put("/api/site/profile", headers=O, json=pr)
            nn = [b["name"] for b in c.get("/api/site/blocks", headers=O).json()["blocks"]]
            if nn != names[::-1]: fail("sıra değişmedi")
            pr["layout"] = {"order": [], "hidden": []}; c.put("/api/site/profile", headers=O, json=pr)
            # 4) kütüphaneden bölüm ekle, düzenle, sil
            r = c.post("/api/yp/pages/tema-ek/blocks", headers=O, json={"bid": cards[0]["id"]})
            if r.status_code != 200: fail("ek bölüm eklenemedi %s" % r.text[:100]); continue
            iid = r.json()["iid"]
            c.put("/api/yp/pages/tema-ek/blocks/%s" % iid, headers=O, json={"set": {"title": "EkBaslik%d" % len(sl)}})
            if not any(b.get("ek") == iid for b in c.get("/api/site/blocks", headers=O).json()["blocks"]): fail("ek bölüm listede yok")
            r = c.delete("/api/yp/pages/tema-ek/blocks/%s" % iid, headers=O)
            if r.status_code != 200 or any(b.get("ek") == iid for b in c.get("/api/site/blocks", headers=O).json()["blocks"]): fail("ek bölüm silinmedi %s" % r.status_code)
            stat["tema"] += 1; stat["bolum"] += len(bl)
        except Exception as e:
            import traceback; fail("istisna " + traceback.format_exc()[-300:])
print(stat, "HATA:", len(bad))
for b in bad: print(b)
