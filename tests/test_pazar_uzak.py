"""Pazaryerinden kategori ve marka kodlarını çekme (Trendyol).""" 
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
import shop_sync, markets_hub, firms, tenant
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: import traceback; bad.append((n, traceback.format_exc()[-700:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
def ean(base12):
    d = [int(x) for x in base12]; s_ = sum(v * (3 if i % 2 else 1) for i, v in enumerate(d)); return base12 + str((10 - s_ % 10) % 10)
RESP = {"orders": {}}
CALLS = []
async def fake_http(method, url, headers, body=None):
    CALLS.append((method, url, headers, body))
    if "connect/token" in url: return 200, {"access_token": "TOK1", "expires_in": 3600}
    if "stock" in url.lower() or "price-and-inventory" in url or "inventory-uploads" in url: return 200, {"ok": True}
    for k, v in sorted(RESP["orders"].items(), key=lambda kv: -len(kv[0])):
        if k in url: return 200, v
    return 200, {}
shop_sync.HTTP["fn"] = fake_http
NOW_MS = lambda d=0: int((time.time() + d) * 1000)
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Pazar Firma", "email": "pz@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "pz@x.com", "sifre12345")
    c.put("/api/site/features", headers=O, json={"shop_enabled": True})
    def setcfg():
        async def go():
            f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1}); S["db"] = f["db"]
            await s.db.firm(f["db"]).app_settings.update_one({"_id": "sp_modules"}, {"$set": {"config": {
                "trendyol": {"seller_id": "123", "api_key": "k", "api_secret": "s"},
                "pazarama": {"client_id": "cid", "client_secret": "sec"},
                "ciceksepeti": {"api_key": "ck"}}}}, upsert=True)
        c.portal.call(go)
    setcfg()

    TREE = {"categories": [{"id": 1, "name": "Giyim", "subCategories": [{"id": 2, "name": "Gömlek", "subCategories": []}, {"id": 3, "name": "Pantolon", "subCategories": [{"id": 4, "name": "Kot Pantolon", "subCategories": []}]}]}, {"id": 9, "name": "Ev", "subCategories": [{"id": 10, "name": "Kombi", "subCategories": []}]}]}
    async def fh(method, url, headers, body=None):
        CALLS.append(url)
        if url.endswith("/product-categories"): return 200, TREE
        if "brands/by-name" in url: return 200, [{"id": 77, "name": "Demirdöküm"}, {"id": 78, "name": "Demir Kombi"}]
        return 200, {}
    shop_sync.HTTP["fn"] = fh
    def kat():
        r = c.get("/api/shop/channels/trendyol/remote-categories?q=kot", headers=O); assert r.status_code == 200, r.text
        j = r.json(); assert [x["id"] for x in j["categories"]] == ["4"] and j["categories"][0]["path"] == "Giyim > Pantolon > Kot Pantolon", j
        assert len(c.get("/api/shop/channels/trendyol/remote-categories", headers=O).json()["categories"]) == 3
        n = len(CALLS); c.get("/api/shop/channels/trendyol/remote-categories?q=gom", headers=O); assert len(CALLS) == n, "ağaç önbellekten gelmeli"
    t("Trendyol kategori ağacından arama (yaprak, yol, önbellek)", kat)
    def mar():
        r = c.get("/api/shop/channels/trendyol/remote-brands?name=demir", headers=O); assert r.status_code == 200, r.text
        assert [b["id"] for b in r.json()["brands"]] == ["77", "78"]
        assert c.get("/api/shop/channels/trendyol/remote-brands?name=d", headers=O).status_code == 422
    t("Trendyol marka koduna ada göre arama", mar)
    def diger():
        assert c.get("/api/shop/channels/pazarama/remote-categories?q=a", headers=O).status_code == 501
        assert c.get("/api/shop/channels/pazarama/remote-brands?name=abc", headers=O).status_code == 501
    t("diğer pazaryerlerinde dürüst mesaj", diger)
print("OK", len(ok), "FAIL", len(bad))
for n, e in bad: print(n, e)
