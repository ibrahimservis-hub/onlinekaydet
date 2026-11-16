"""Toplu işlemler: pazaryerlerine gönder (açar, eksikleri raporlar), satışa kapat (kanallar kapanır, listelenen pazaryerine stok 0 kuyruğa girer), tekrar aç."""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-900:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ali", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    P = lambda **k: c.post("/api/yp/products", headers=H, json=dict({"price": 500, "cost": 200, "stock": 8}, **k)).json()["id"]
    a1 = P(name="Pompa A", sku="TA1", barcode="8690000000014", brand="Vaillant", cat="Pompa")
    a2 = P(name="Pompa B", sku="TA2")
    ids = [a1, a2]
    G = lambda pid: (lambda r: r.get("item") or r)(c.get("/api/yp/products/" + pid, headers=H).json())
    def shopdoc(pid):
        async def f(): return await s.db.firm(FIRM).shop_products.find_one({"id": pid}, {"_id": 0})
        return c.portal.call(f)
    async def firm():
        f = await s.db.main().firms.find_one({"login_email": j["email"]}, {"_id": 0, "db": 1}); return f["db"]
    FIRM = c.portal.call(firm)
    def a():
        r = c.post("/api/yp/products/bulk-market", headers=H, json={"ids": ids, "op": "send", "markets": ["trendyol", "n11"]})
        assert r.status_code == 200, r.text
        m = {x["market"]: x for x in r.json()["markets"]}
        assert set(m) == {"trendyol", "n11"} and m["trendyol"]["enabled"] == 2
        assert m["trendyol"]["blocked_n"] >= 1 and m["trendyol"]["blocked"][0]["issues"], m["trendyol"]
        assert G(a1)["channels"]["trendyol"] is True and G(a2)["channels"]["n11"] is True
        d = shopdoc(a1); assert d["channels"]["trendyol"]["enabled"] is True
    t("gönder: pazaryeri açılır, eksikler ürün ürün raporlanır", a)
    def b():
        assert c.post("/api/yp/products/bulk-market", headers=H, json={"ids": ids, "op": "send", "markets": []}).status_code == 422
        assert c.post("/api/yp/products/bulk-market", headers=H, json={"ids": [], "op": "send", "markets": ["n11"]}).status_code == 422
        assert c.post("/api/yp/products/bulk-market", headers=H, json={"ids": ids, "op": "x"}).status_code == 422
    t("gönder: eksik istek reddedilir", b)
    def rz():
        r = c.get("/api/yp/products?limit=50", headers=H).json()
        row = [x for x in r["rows"] if x["id"] == a1][0]
        m = {x["id"]: x for x in row["markets"]}
        assert "trendyol" in m and m["trendyol"]["status"] in ("eksik", "hazir", "hata"), m
        assert "name" in m["trendyol"] and "price_differs" in m["trendyol"]
    t("liste: açık pazaryerleri durum rozetiyle gelir", rz)
    def d():
        async def mark():
            await s.db.firm(FIRM).shop_products.update_one({"id": a1}, {"$set": {"market_sync.trendyol.listed": True}})
        c.portal.call(mark)
        r = c.post("/api/yp/products/bulk-market", headers=H, json={"ids": ids, "op": "close"}).json()
        assert r["ok"] and r["n"] == 2 and r["queued"] >= 1, r
        g = G(a1); assert not any(g["channels"].values()), g["channels"]
        d1 = shopdoc(a1); assert d1["active"] is False and d1["channels"]["trendyol"]["enabled"] is False
        import shop_channels as ch
        assert ch.channel_stock(d1, "trendyol") == 0, "kapalı ürün pazaryerine stok 0 bildirmeli"
    t("satışa kapat: tüm kanallar kapanır, listelenen pazaryerine stok 0", d)
    def e():
        r = c.post("/api/yp/products/bulk-market", headers=H, json={"ids": ids, "op": "open"}).json()
        assert r["ok"]
        g = G(a1); assert g["channels"]["site"] is True and g["status"] == "live"
        assert shopdoc(a1)["active"] is True
    t("sitede yeniden aç", e)
with TestClient(s.app) as _: pass
for n in ok: print("  ✓", n)
for n, x in bad: print("  ✗", n, "\n", x)
print("OK %d FAIL %d" % (len(ok), len(bad)))
