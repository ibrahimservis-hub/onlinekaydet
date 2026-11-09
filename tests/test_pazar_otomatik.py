"""Pazaryeri siparişleri otomatik sisteme düşer: sipariş listesi, tek seferlik stok düşümü, eski siparişler stok bozmaz, iptalde stok geri gelir."""
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
    S["bc"] = ean("869000000011")
    def prod():
        r = c.post("/api/shop/products", headers=O, json={"name": "Kombi A", "brand": "B", "price": 100, "stock": 10, "sku": "KA-1", "barcode": S["bc"], "kdv": 20, "desi": 5,
                "description": "Açıklama metni en az otuz karakter olmalıdır tamam.", "images": ["https://x.com/a.jpg"]}); assert r.status_code == 200, r.text; S["pid"] = r.json()["id"]
    t("ürün oluşturulur", prod)
    def stock():
        return next(p for p in c.get("/api/shop/admin/products", headers=O).json()["rows"] if p["id"] == S["pid"])["stock"] if False else c.portal.call(lambda: None) or _stock()
    def _stock():
        async def go():
            return (await s.db.firm(S["db"]).shop_products.find_one({"id": S["pid"]}, {"_id": 0, "stock": 1}))["stock"]
        return c.portal.call(go)
    def mk_order(no, qty, st="Created", d=0):
        return {"orderNumber": no, "status": st, "orderDate": NOW_MS(d), "grossAmount": 100 * qty, "customerFirstName": "Ali", "customerLastName": "Veli",
                "shipmentAddress": {"city": "Ankara", "district": "Çankaya", "fullAddress": "Test mah. 1"}, "lines": [{"barcode": S["bc"], "quantity": qty, "productName": "Kombi A", "price": 100}]}
    def first_pull():
        RESP["orders"]["trendyol"] = {"content": [mk_order("OLD1", 3, "Delivered", -86400 * 5)]}
        r = c.post("/api/admin/market/trendyol/pull-orders", headers=O); assert r.status_code == 200, r.text
        j = r.json(); assert j["first"] and j["historical"] == 1 and j["new"] == 0, j
        assert _stock() == 10, "eski sipariş stoğu bozmamalı"
        rows = c.get("/api/shop/orders", headers=O).json(); rows = rows.get("rows", rows) if isinstance(rows, dict) else rows
        o = next(x for x in rows if x["order_no"] == "TY-OLD1"); assert o["source"] == "trendyol" and o["status"] == "teslim_edildi" and o["external"], o
    t("ilk bağlantı: eski sipariş listeye girer, stok düşmez", first_pull)
    def new_order():
        RESP["orders"]["trendyol"] = {"content": [mk_order("NEW1", 2, "Created", 60), mk_order("OLD1", 3, "Delivered", -86400 * 5)]}
        j = c.post("/api/admin/market/trendyol/pull-orders", headers=O).json(); assert j["new"] == 1, j
        assert _stock() == 8, _stock()
        c.post("/api/admin/market/trendyol/pull-orders", headers=O)
        assert _stock() == 8, "aynı sipariş ikinci kez düşmemeli"
    t("yeni sipariş otomatik düşer, tekrar çekimde çift düşmez", new_order)
    def cancel():
        RESP["orders"]["trendyol"] = {"content": [mk_order("NEW1", 2, "Cancelled", 60)]}
        c.post("/api/admin/market/trendyol/pull-orders", headers=O)
        assert _stock() == 10, _stock()
        rows = c.get("/api/shop/orders", headers=O).json(); rows = rows.get("rows", rows) if isinstance(rows, dict) else rows
        assert next(x for x in rows if x["order_no"] == "TY-NEW1")["status"] == "iptal"
    t("pazaryeri iptali: stok geri gelir, sipariş iptal görünür", cancel)
    def manual_cancel_guard():
        rows = c.get("/api/shop/orders", headers=O).json(); rows = rows.get("rows", rows) if isinstance(rows, dict) else rows
        o = next(x for x in rows if x["order_no"] == "TY-OLD1")
        c.put(f"/api/shop/orders/{o['id']}", headers=O, json={"status": "iptal"})
        assert _stock() == 10, "pazaryeri siparişini elle iptal etmek stoğu ikinci kez artırmamalı"
    t("pazaryeri siparişi elle iptal edilince stok şişmez", manual_cancel_guard)
    def pazarama():
        c.post("/api/admin/market/pazarama/pull-orders", headers=O)       # ilk çağrı since'i koyar
        RESP["orders"]["getOrdersForApi"] = {"data": [{"orderNumber": "P77", "orderStatus": "Hazırlanıyor", "createdDate": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time() + 120)),
              "totalAmount": 100, "orderItems": [{"stockCode": "KA-1", "quantity": 1, "name": "Kombi A", "salePrice": 100}], "customerName": "Ayşe Y"}]}
        j = c.post("/api/admin/market/pazarama/pull-orders", headers=O).json(); assert j["new"] == 1, j
        assert _stock() == 9, _stock()
        assert any("connect/token" in u for _m, u, _h, _b in CALLS), "OAuth anahtarı alınmalı"
        assert any(h.get("Authorization") == "Bearer TOK1" for _m, u, h, _b in CALLS if "getOrdersForApi" in u)
    t("Pazarama: anahtar alınır, sipariş düşer", pazarama)
    def push_all():
        r = c.get("/api/admin/market/status", headers=O).json(); ids = {m["id"]: m for m in r["markets"]}
        assert len(ids) == 6 and ids["trendyol"]["connected"] and ids["pazarama"]["connected"] and not ids["pttavm"]["connected"], ids
        assert ids["trendyol"]["last"] and ids["trendyol"]["imported"] >= 1
    t("durum ucu: 6 pazaryeri, bağlı olanlar ve son çekim", push_all)
    def cycle():
        RESP["orders"]["trendyol"] = {"content": [mk_order("NEW2", 1, "Created", 90)]}
        async def go():
            await s.db.main().market_lease.delete_many({})
            return await markets_hub.run_cycle(s.db, firms, tenant)
        n = c.portal.call(go); assert n >= 2, n
        assert _stock() == 8, _stock()
    t("zamanlayıcı döngüsü tüm firmaları gezer ve siparişi düşer", cycle)
    def lease():
        async def go():
            return await markets_hub.run_cycle(s.db, firms, tenant)
        assert c.portal.call(go) == 0, "kilit varken ikinci işçi çalışmamalı"
    t("kilit: aynı anda tek işçi çeker", lease)
    def stock_push():
        async def go():
            d = s.db.firm(S["db"])
            await d.shop_products.update_one({"id": S["pid"]}, {"$set": {"channels.ciceksepeti": {"enabled": True, "buffer": 1, "price": 0}, "market_sync.ciceksepeti.listed": True}})
            await shop_sync._enqueue(d, [S["pid"]], markets=["ciceksepeti"])
            return await shop_sync.process_queue(d)
        tk = tenant.set_firm(S["db"])
        try: res = c.portal.call(go)
        finally: tenant.reset(tk)
        assert res["sent"] >= 1 and res["failed"] == 0, res
        call = [x for x in CALLS if "price-and-stock" in x[1]][-1]
        assert call[0] == "PUT" and call[3]["items"][0]["stockQuantity"] == 7 and call[2].get("x-api-key") == "ck", call
    t("Çiçeksepeti stok gönderimi: havuz - güvenlik payı", stock_push)
    def attrs():
        r = c.post("/api/shop/categories", headers=O, json={"name": "Kombi"}); assert r.status_code == 200, r.text; cid = r.json()["id"]
        rr = c.put(f"/api/shop/products/{S['pid']}", headers=O, json={"category_id": cid, "category_ids": [cid]}); assert rr.status_code == 200, rr.text
        RESP["orders"]["product-categories"] = {"categoryAttributes": [{"attribute": {"id": 47, "name": "Renk"}, "required": True, "allowCustom": False, "attributeValues": [{"id": 9001, "name": "Beyaz"}, {"id": 9002, "name": "Siyah"}]},
                                                                      {"attribute": {"id": 91, "name": "Ebat"}, "required": True, "allowCustom": True, "attributeValues": []}]}
        r = c.get("/api/shop/channels/trendyol/category-attrs?ext_id=1234", headers=O); assert r.status_code == 200, r.text
        at = r.json()["attrs"]; assert at[0]["name"] == "Renk" and len(at[0]["values"]) == 2 and at[1]["allow_custom"], at
        assert c.get("/api/shop/channels/pazarama/category-attrs?ext_id=1", headers=O).status_code == 501
        r = c.put(f"/api/shop/channels/trendyol/catmap/{cid}", headers=O, json={"ext_id": "1234", "required_attrs": at, "attrs": {"47": "9001"}}); assert r.status_code == 200, r.text
        r = c.put(f"/api/shop/channels/pazarama/catmap/{cid}", headers=O, json={"ext_id": "55", "required_attrs": [{"name": "Renk"}, {"name": "Ebat / Beden", "required": False}], "attrs": {}}); assert r.status_code == 200, r.text
        m = next(x for x in c.get("/api/shop/channels/pazarama/catmap", headers=O).json()["categories"] if x["id"] == cid)["map"]
        assert [a["id"] for a in m["required_attrs"]] == ["n_renk", "n_ebat_beden"], m
        c.put(f"/api/shop/channels/pazarama/products/{S['pid']}", headers=O, json={"enabled": True})
        rows = c.get("/api/shop/channels/pazarama/products", headers=O).json()["rows"]; assert rows, c.get("/api/shop/channels/pazarama/products", headers=O).text[:300]
        msg = " ".join(i["msg"] for i in rows[0]["issues"]); assert "Renk" in msg and "Ebat" not in msg, msg          # zorunlu olmayan özellik engel olmaz
        r = c.put(f"/api/shop/products/{S['pid']}", headers=O, json={"market_attrs": {"pazarama": {"n_renk": "Beyaz"}, "trendyol": {"91": "24 kW"}}}); assert r.status_code == 200, r.text
        rows = c.get("/api/shop/channels/pazarama/products", headers=O).json()["rows"]
        assert "Renk" not in " ".join(i["msg"] for i in rows[0]["issues"]), rows[0]["issues"]
        p = c.portal.call(lambda: None) or None
        async def go():
            d = s.db.firm(S["db"]); pr = await d.shop_products.find_one({"id": S["pid"]}, {"_id": 0}); cm = await d.market_catmap.find_one({"market": "trendyol", "category_id": cid}, {"_id": 0})
            return shop_sync.trendyol_item(pr, cm, {"b": "1"} if False else {(pr.get("brand") or "").strip().lower(): "5"}, {})
        it = c.portal.call(go)["attributes"]
        assert {"attributeId": 47, "attributeValueId": 9001} in it and {"attributeId": 91, "customAttributeValue": "24 kW"} in it, it
    t("özellik eşleme: Trendyol'dan getir, elle ekle, zorunlu değil engel olmaz, ürüne özel değer, Trendyol gövdesi", attrs)
    def paketkart():
        r = c.post("/api/admin/firms", headers=A, json={"name": "Süreli Firma", "email": "sr@x.com", "password": "sifre12345", "package": "tam", "usage_days": 10}); assert r.status_code == 200, r.text
        P = c.get("/api/firm/package", headers=tok(c, "sr@x.com", "sifre12345")).json()
        assert P["unlimited"] is False and P["days_left"] in (9, 10) and P["expires_at"], P
        Q = c.get("/api/firm/package", headers=O).json(); assert Q["unlimited"] is True and Q["days_left"] is None and Q["modules"], Q
    t("Genel Bakış kartı verisi: paket, bitiş tarihi, kalan gün, süresiz", paketkart)
print("\nGEÇTİ" if not bad else "\nHATA", f"{len(ok)}/{len(ok)+len(bad)}")
for n in ok: print(" +", n)
for n, e in bad: print(" -", n, e)
