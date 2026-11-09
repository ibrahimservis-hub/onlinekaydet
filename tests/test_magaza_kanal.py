"""Mağaza kanalları: tek ürün/stok havuzu, kategori eşleme, barkod, pazaryeri kuyruğu ve pazaryeri siparişinden stok düşümü."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
import shop_channels as ch, shop_sync
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:600]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
def ean(base12):
    d = [int(x) for x in base12]; s_ = sum(v * (3 if i % 2 else 1) for i, v in enumerate(d)); return base12 + str((10 - s_ % 10) % 10)
CALLS = []
async def fake_http(method, url, headers, body=None):
    CALLS.append((method, url, body))
    if "batch-requests" in url: return 200, {"status": "COMPLETED", "failedItemCount": 0, "items": [{"status": "SUCCESS", "requestItem": {"barcode": S["bc"]}, "failureReasons": []}]}
    if url.endswith("/products"): return 200, {"batchRequestId": "abc-123"}
    return 200, {"ok": True}
shop_sync.HTTP["fn"] = fake_http
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Kanal Firma", "email": "kn@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "kn@x.com", "sifre12345")
    c.put("/api/site/features", headers=O, json={"shop_enabled": True})
    def setcfg():
        async def go():
            f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
            await s.db.firm(f["db"]).app_settings.update_one({"_id": "sp_modules"}, {"$set": {"config": {"trendyol": {"seller_id": "123", "api_key": "k", "api_secret": "s"}}}}, upsert=True)
        c.portal.call(go)
    setcfg()
    S["bc"] = ean("869000000001")
    def cats():
        r = c.post("/api/shop/categories", headers=O, json={"name": "Kombi"}); assert r.status_code == 200, r.text; S["cat"] = r.json()["id"]
        assert c.post("/api/shop/categories", headers=O, json={"name": "Kombi"}).status_code == 409
    t("iç kategori ağacı: ekle, çift ad reddedilir", cats)
    def prod():
        base = {"name": "Baymak Kombi 24 kW", "brand": "Baymak", "price": 20000, "stock": 10, "sku": "BYM-24", "category_id": S["cat"], "kdv": 20, "desi": 25, "shelf": "A-3",
                "description": "Tam yoğuşmalı, 24 kW, A sınıfı enerji verimli duvar tipi kombi cihazı.", "images": ["https://x.com/a.jpg"], "min_stock": 2}
        assert c.post("/api/shop/products", headers=O, json={**base, "barcode": "8690000000000"}).status_code == 422, "sağlama basamağı yanlış barkod"
        assert c.post("/api/shop/products", headers=O, json={**base, "kdv": 18}).status_code == 422
        assert c.post("/api/shop/products", headers=O, json={**base, "category_id": "yok"}).status_code == 422
        r = c.post("/api/shop/products", headers=O, json={**base, "barcode": S["bc"]}); assert r.status_code == 200, r.text
        S["pid"] = r.json()["id"]; assert r.json()["category"] == "Kombi", "kategori adı ağaçtan gelir"
        r = c.post("/api/shop/products", headers=O, json={**base, "sku": "BYM-25", "barcode": S["bc"]}); assert r.status_code == 409, "aynı barkod"
        r = c.post("/api/shop/products", headers=O, json={**base, "barcode": ""}); assert r.status_code == 409, "aynı stok kodu"
    t("ürün: barkod/KDV/kategori doğrulanır, barkod ve stok kodu benzersiz", prod)
    def notready():
        r = c.put(f"/api/shop/channels/trendyol/products/{S['pid']}", headers=O, json={"enabled": True, "buffer": 2}); assert r.status_code == 200, r.text
        r = c.get("/api/shop/channels/trendyol/products", headers=O).json()
        row = r["rows"][0]; assert row["status"] == "eksik" and row["stock"] == 8 and row["pool_stock"] == 10, row
        msgs = " ".join(i["msg"] for i in row["issues"]); assert "kategori eşlemesi" in msgs and "marka kodu" in msgs, msgs
    t("kategori/marka eşlenmeden ürün 'eksik' görünür; kanal stoğu = havuz - pay", notready)
    def mapping():
        r = c.put(f"/api/shop/channels/trendyol/catmap/{S['cat']}", headers=O, json={"ext_id": "abc"}); assert r.status_code == 422
        r = c.put(f"/api/shop/channels/trendyol/catmap/{S['cat']}", headers=O, json={"ext_id": "1234", "ext_name": "Kombi", "required_attrs": [{"id": 47, "name": "Renk"}]}); assert r.status_code == 200, r.text
        v = c.get(f"/api/shop/channels/trendyol/validate", headers=O).json(); assert v["blocked"] == 1 and "Renk" in str(v["rows"][0]["issues"]), v
        r = c.put(f"/api/shop/channels/trendyol/catmap/{S['cat']}", headers=O, json={"ext_id": "1234", "ext_name": "Kombi", "required_attrs": [{"id": 47, "name": "Renk"}], "attrs": {"47": "9001"}}); assert r.status_code == 200
        assert c.put("/api/shop/channels/trendyol/brandmap", headers=O, json={"map": {"Baymak": "555"}}).status_code == 200
        v = c.get("/api/shop/channels/trendyol/validate", headers=O).json(); assert v["ready"] == 1 and v["blocked"] == 0, v
    t("kategori eşleme + zorunlu özellik + marka kodu girilince ürün hazır olur", mapping)
    def dry():
        n = len(CALLS)
        r = c.post("/api/shop/channels/trendyol/create", headers=O, json={}); assert r.status_code == 200, r.text
        j = r.json(); assert j["dry_run"] and j["ready"] == 1 and len(CALLS) == n, "dry-run istek atmaz"
        it = j["preview"][0]; assert it["quantity"] == 8 and it["categoryId"] == 1234 and it["brandId"] == 555 and it["barcode"] == S["bc"] and it["stockCode"] == "BYM-24" and it["vatRate"] == 20, it
        assert it["attributes"] == [{"attributeId": 47, "attributeValueId": 9001}], it
    t("deneme gönderimi: istek atmaz, Trendyol kalemi doğru alanlarla hazırlanır", dry)
    def real():
        r = c.post("/api/shop/channels/trendyol/create", headers=O, json={"dry_run": False}); assert r.status_code == 200, r.text
        assert r.json()["batch"] == "abc-123"
        assert CALLS[-1][0] == "POST" and CALLS[-1][1].endswith("/sellers/123/products")
        r = c.post("/api/shop/channels/trendyol/batch-check", headers=O, json={"batch": "abc-123"}); assert r.status_code == 200, r.text
        row = c.get("/api/shop/channels/trendyol/products", headers=O).json()["rows"][0]; assert row["status"] == "yayinda", row
    t("ürün açılır, toplu işlem sonucu 'yayında' yapar", real)
    def sync_site_order():
        CALLS.clear()
        r = c.post("/api/shop/products/%s/stock" % S["pid"], headers=O, json={"mode": "remove", "qty": 11}); assert r.status_code == 422, "eksiye düşmez"
        r = c.post("/api/shop/products/%s/stock" % S["pid"], headers=O, json={"mode": "set", "qty": 6, "shelf": "B-1", "reason": "sayım"}); assert r.status_code == 200
        q = c.get("/api/shop/sync/queue", headers=O).json(); assert q["pending"] == 1, q
        r = c.post("/api/shop/sync/run", headers=O); assert r.json()["sent"] == 1, r.text
        body = CALLS[-1][2]["items"][0]; assert body["quantity"] == 4 and body["barcode"] == S["bc"] and body["salePrice"] == 20000, body    # 6 - pay 2
        lg = c.get("/api/shop/stock-log?product_id=" + S["pid"], headers=O).json(); assert lg and lg[0]["new"] == 6
    t("panelden stok sayımı kuyruğa girer ve Trendyol'a (havuz - pay) gider; hareket kaydı tutulur", sync_site_order)
    def mk_order():
        CALLS.clear()
        raw = {"status": "Created", "lines": [{"barcode": S["bc"], "quantity": 2}]}
        async def go():
            f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
            d = s.db.firm(f["db"])
            a = await shop_sync.apply_market_order(d, "trendyol", "T1", raw)
            b = await shop_sync.apply_market_order(d, "trendyol", "T1", raw)       # aynı sipariş ikinci kez gelirse düşmez
            cc = await shop_sync.apply_market_order(d, "trendyol", "T1", {**raw, "status": "Cancelled"})
            dd = await shop_sync.apply_market_order(d, "trendyol", "T1", {**raw, "status": "Cancelled"})
            return a, b, cc, dd
        a, b, cc, dd = c.portal.call(go)
        assert a and not b and cc and not dd, (a, b, cc, dd)
        p = [x for x in c.get("/api/shop/products", headers=O).json() if x["id"] == S["pid"]][0]; assert p["stock"] == 6, p["stock"]
    t("pazaryeri siparişi bir kez düşer, iptalde bir kez geri gelir", mk_order)
    def mk_order2():
        raw = {"status": "Created", "lines": [{"barcode": S["bc"], "quantity": 3}, {"barcode": "yok", "quantity": 1}]}
        async def go():
            f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1}); d = s.db.firm(f["db"])
            await shop_sync.apply_market_order(d, "trendyol", "T2", raw)
        c.portal.call(go)
        p = [x for x in c.get("/api/shop/products", headers=O).json() if x["id"] == S["pid"]][0]; assert p["stock"] == 3, p["stock"]
        assert c.get("/api/shop/sync/queue", headers=O).json()["pending"] >= 1, "düşen stok kanallara yansımak üzere kuyruğa girer"
    t("pazaryeri siparişi stoğu düşürür ve tanınmayan barkodu kaydeder", mk_order2)
    def export():
        r = c.get("/api/shop/channels/trendyol/export.csv", headers=O); assert r.status_code == 200 and S["bc"] in r.text and "BYM-24" in r.text
        o = c.get("/api/shop/channels", headers=O).json(); tr = [x for x in o["channels"] if x["id"] == "trendyol"][0]; assert tr["counts"].get("yayinda") == 1, tr
        assert c.get("/api/shop/channels/amazon/products", headers=O).status_code == 404, "henüz desteklenmeyen pazaryeri"
    t("CSV dışa aktarma, kanal özeti, desteklenmeyen pazaryeri 404", export)
    def gtin():
        assert ch.gtin_valid(S["bc"]) and not ch.gtin_valid("12345") and not ch.gtin_valid(S["bc"][:-1] + "0" if S["bc"][-1] != "0" else S["bc"][:-1] + "1")
    t("GTIN doğrulaması", gtin)
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" FAIL", n, e)
sys.exit(1 if bad else 0)
