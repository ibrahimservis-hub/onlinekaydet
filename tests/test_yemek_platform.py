"""Restoran: Yemeksepeti (bildirimle), Trendyol/Getir/Migros Yemek (çekimle) siparişleri sipariş listesine düşer; müşteri panelinden girilen anahtar çalışır."""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
import demo, shop_sync
demo.GUNLUK_LIMIT = 10 ** 6
s = boot.server; ok = bad = 0
def t(n, c):
    global ok, bad
    ok += bool(c); bad += (not c); print(("  ✓ " if c else "  ✗ ") + n)
CALLS = []
async def fake(m, u, h, b):
    CALLS.append((m, u, h, b))
    if "tgoapis" in u and m == "GET":
        return 200, {"page": 0, "size": 50, "content": [{"id": "a" * 64, "orderNumber": "T-1001", "orderCode": "1E1", "packageStatus": "Created", "totalPrice": 245.5, "packageCreationDate": 9999999999000,
                      "customer": {"id": 1, "firstName": "Ayşe", "lastName": "Y."}, "address": {"address1": "Çankaya Ankara", "city": "Ankara", "district": "Çankaya", "phone": "05320000000", "floor": "TGO Yemek"},
                      "lines": [{"price": 100, "unitSellingPrice": 100, "productId": 11, "name": "Adana Kebap", "items": [{"packageItemId": "p1", "isCancelled": False}, {"packageItemId": "p2", "isCancelled": False}]},
                                {"price": 45.5, "unitSellingPrice": 45.5, "productId": 12, "name": "Ayran", "items": [{"packageItemId": "p3", "isCancelled": False}]}]}]}
    if "tgoapis" in u:
        return 200, {}
    if "getir.example" in u:
        return 200, {"orders": [{"id": "G77", "status": "NEW", "totalAmount": 120, "items": [{"name": "Lahmacun", "quantity": 3, "price": 40}]}]}
    return 200, {"ok": True}
shop_sync.HTTP["fn"] = fake
with TestClient(s.app) as c:
    d = c.post("/api/public/demo", json={"name": "Mehmet", "phone": "05321110099", "sector": "lokanta"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
    L = c.get("/api/yp/integrations", headers=H); t("entegrasyon listesi açılır", L.status_code == 200)
    ids = str(L.json())
    for k in ("yemeksepeti", "trendyol_yemek", "getir_yemek", "migros_yemek"):
        t("restoranda %s var" % k, k in ids)
    # 0) ilk başarılı bağlantı kendiliğinden etkin olur; sonra bilerek kapatılırsa kapalı kalır
    r = c.put("/api/yp/integrations/trendyol_yemek", headers=H, json={"keys": {"seller_id": "123", "api_key": "k", "api_secret": "s"}, "on": False}); t("ilk bağlantı: on=False gönderilse de etkin", r.json()["item"]["on"] is True)
    r = c.put("/api/yp/integrations/trendyol_yemek", headers=H, json={"on": False}); t("bilerek kapatılırsa kapalı kalır", r.json()["item"]["on"] is False)
    # 1) Trendyol Yemek: müşteri panelinden anahtar girilir -> sipariş çekilir
    r = c.put("/api/yp/integrations/trendyol_yemek", headers=H, json={"on": True, "keys": {"seller_id": "123", "api_key": "k", "api_secret": "s"}}); t("trendyol yemek anahtarı kaydedildi", r.status_code == 200 and r.json().get("ok"))
    r = c.post("/api/admin/market/trendyol_yemek/pull-orders", headers=H); t("trendyol yemek çekimi çalışır: %s" % r.text[:80], r.status_code == 200)
    r = c.post("/api/admin/market/trendyol_yemek/pull-orders", headers=H)
    o = [x for x in c.get("/api/shop/admin/orders", headers=H).json().get("rows", [])] if c.get("/api/shop/admin/orders", headers=H).status_code == 200 else []
    g = [x for x in CALLS if "tgoapis" in x[1] and x[0] == "GET"][0]
    t("istek Trendyol Yemek adresine gitti, zorunlu başlıklar var", "Basic" in g[2].get("Authorization", "") and g[2].get("x-agentname") and g[2].get("x-executor-user") and g[2]["User-Agent"].startswith("123 - ") and "/suppliers/123/packages" in g[1])
    rr = c.get("/api/yp/orders?limit=100", headers=H).json(); rr = rr.get("rows") or rr.get("items") or rr
    tt = [x for x in rr if x["no"] == "TYY-T-1001"][0]
    t("trendyol yemek: kalem adedi items sayısından, müşteri, TGO maskesi boş", len(tt["items"]) == 2 and sorted(i["qty"] for i in tt["items"]) == [1, 2] and tt["customer"]["name"] == "Ayşe Y.")
    # 2) Getir Yemek: adres + anahtar
    c.put("/api/yp/integrations/getir_yemek", headers=H, json={"on": True, "keys": {"token": "tk", "orders_url": "https://getir.example/orders"}})
    r = c.post("/api/admin/market/getir_yemek/pull-orders", headers=H); t("getir yemek çekimi", r.status_code == 200)
    for dm, tail, body in (("kabul", "/packages/picked", {"packageId": "a" * 64, "preparationTime": 20}), ("hazir", "/packages/invoiced", None), ("yolda", "/manual-shipped", None), ("teslim", "/manual-delivered", None), ("iptal", "/packages/unsupplied", {"packageId": "a" * 64, "itemIdList": ["p1", "p2", "p3"], "reasonId": 623})):
        n0 = len(CALLS); r = c.post("/api/admin/yemek/trendyol_yemek/siparis/TYY-T-1001/durum", headers=H, json={"durum": dm})
        w = [x for x in CALLS[n0:] if x[0] == "PUT"]
        t("trendyol yemek %s -> doğru uç: %s" % (dm, r.text[:60]), r.status_code == 200 and len(w) == 1 and w[0][1].endswith(tail) and (body is None or w[0][3] == body) and w[0][2].get("x-agentname"))
    # 3) Yemeksepeti: bildirim (firma numarası adreste)
    c.put("/api/yp/integrations/yemeksepeti", headers=H, json={"on": True, "keys": {"webhook_key": "gizli123", "komisyon": "20"}})
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    fid = [f for f in c.get("/api/admin/firms", headers=A).json()["firms"] if f.get("demo")][0]["id"]
    r = c.post("/api/public/%s~yemek/yemeksepeti?k=yanlis" % fid, json={"orderId": "Y1"}); t("yanlış anahtar reddedilir", r.status_code == 401)
    body = {"orderId": "Y1", "status": "NEW", "totalAmount": 300, "customer": {"name": "Can K.", "phone": "05331112233"}, "items": [{"name": "Döner", "quantity": 2, "price": 150}]}
    r = c.post("/api/public/%s~yemek/yemeksepeti?k=gizli123" % fid, json=body); t("yemeksepeti bildirimi kabul: %s" % r.text[:80], r.status_code == 200 and r.json()["ok"])
    c.post("/api/public/%s~yemek/yemeksepeti?k=gizli123" % fid, json=body)
    # 3b) Yemeksepeti gerçek yük biçimi (developer.yemeksepeti.com örneği)
    ysb = {"order_id": "7b0c6c1e-0000-4000-8000-000000000001", "order_code": "AB12", "status": "READY_FOR_PICKUP", "client": {"store_id": "S1"},
           "customer": {"first_name": "Deniz", "last_name": "Kaya", "phone_number": "05340000000", "delivery_address": {"formattedAddress": "Kızılay Ankara", "city": "Ankara"}},
           "items": [{"sku": "DONER1", "barcode": ["8690000000111"], "name": "Döner", "status": "IN_CART", "pricing": {"unit_price": 90, "quantity": 2, "total_price": 180}},
                     {"sku": "X", "name": "Yok", "status": "NOT_FOUND", "pricing": {"unit_price": 10, "quantity": 1}}],
           "payment": {"order_total": 180, "delivery_fee": 0}, "sys": {"created_at": "2999-01-01T10:00:00Z"}}
    r = c.post("/api/public/%s~yemek/yemeksepeti" % fid, headers={"Authorization": "Basic gizli123"}, json=ysb); t("yemeksepeti gerçek yük + Basic başlığı: %s" % r.text[:60], r.status_code == 200)
    ysb["status"] = "CANCELLED"; c.post("/api/public/%s~yemek/yemeksepeti?k=gizli123" % fid, json=ysb)
    rows = (lambda L: L.get("rows") or L.get("items") or L)(c.get("/api/yp/orders?limit=100", headers=H).json())
    z = [x for x in rows if x["no"].startswith("YS-7b0c6c1e")]
    t("gerçek yük: tek kayıt, tutar 180, müşteri, bulunamayan kalem hariç, iptal", len(z) == 1 and z[0]["total"] == 180 and z[0]["customer"]["name"] == "Deniz Kaya" and len(z[0]["items"]) == 1 and z[0]["status"] == "iptal")
    # 4) müşteri panelindeki Siparişler listesi
    L = c.get("/api/yp/orders?limit=100", headers=H).json(); rows = L.get("rows") or L.get("items") or L
    ch = [x["channel"] for x in rows]
    t("siparişler listesinde 3 platform siparişi (tekrarsız)", [x["no"] for x in rows].count("YS-Y1") == 1 and "TYY-T-1001" in [x["no"] for x in rows] and "GY-G77" in [x["no"] for x in rows])
    ys = [x for x in rows if x["no"] == "YS-Y1"][0]
    t("kanal adı ve kâr hesabı (%%20 komisyon)", ys["channel_name"] == "Yemeksepeti" and ys["total"] == 300)
    ty = [x for x in rows if x["no"] == "TYY-T-1001"][0]
    t("trendyol yemek müşteri ve ürünler", ty["customer"]["name"] == "Ayşe Y." and len(ty["items"]) == 2)
    # 5) durum bildirimi
    r = c.post("/api/admin/yemek/yemeksepeti/siparis/YS-Y1/durum", headers=H, json={"durum": "hazir"}); t("durum güncellenir: %s" % r.text[:80], r.status_code == 200)
    rows = (lambda L: L.get("rows") or L.get("items") or L)(c.get("/api/yp/orders?limit=100", headers=H).json())
    t("panel listesinde durum da değişti", [x for x in rows if x["no"] == "YS-Y1"][0]["status"] == "hazirlaniyor")
    r = c.post("/api/admin/yemek/yemeksepeti/siparis/YS-Y1/durum", headers=H, json={"durum": "x"}); t("geçersiz durum reddedilir", r.status_code == 422)
print("OK", ok, "FAIL", bad)
