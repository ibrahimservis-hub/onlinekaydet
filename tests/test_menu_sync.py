"""Yemek menüsü: yemek alanları kaydedilir, Trendyol Yemek'te yalnızca değişen fiyat/durum gönderilir, diğer platformlar için dosya verilir."""
import sys, os
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
    if u.endswith("/stores?page=0&size=50"):
        return 200, {"restaurants": [{"id": 7, "name": "Şube 1"}]}
    if u.endswith("/stores/7/products"):
        return 200, {"products": [{"id": 1, "name": "Adana Kebap", "sellingPrice": 250, "status": "ACTIVE"},
                                  {"id": 2, "name": "Ayran", "sellingPrice": 30, "status": "ACTIVE"},
                                  {"id": 3, "name": "Künefe", "sellingPrice": 90, "status": "ACTIVE"}]}
    if u.endswith("/products/price"):
        return 200, {"batchRequestId": "b-1"}
    if "/batch-requests/" in u:
        return 200, {"status": "COMPLETED", "itemCount": 1, "failedItemCount": 0, "items": [{"status": "SUCCESS", "failureReasons": []}]}
    return 200, {}
shop_sync.HTTP["fn"] = fake
def urun(name, price, extra=None):
    d = {"name": name, "price": price, "vat": 10, "stock": 99, "channels": {"site": True, "trendyol_yemek": True, "yemeksepeti": True},
         "food": {"bolum": "Kebaplar", "hazirlik": 20, "alerjen": ["gluten", "uydurma"], "vejetaryen": False, "aci": 2, "cikarilabilir": ["soğan"],
                  "gruplar": [{"ad": "Yan ürün", "min": 1, "max": 1, "secenekler": [{"ad": "Pilav", "fiyat": 0}, {"ad": "Salata", "fiyat": 15}]}]}}
    d.update(extra or {}); return d
with TestClient(s.app) as c:
    d = c.post("/api/public/demo", json={"name": "Mehmet", "phone": "05321110099", "sector": "lokanta"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
    r = c.post("/api/yp/products", headers=H, json=urun("Adana Kebap", 260)); t("yemek alanlı ürün kaydedilir: %s" % r.text[:60], r.status_code in (200, 201))
    pid = (r.json().get("item") or r.json())["id"]
    f = c.get("/api/yp/products/" + pid, headers=H).json(); f = f.get("item") or f; f = f["food"]
    t("alerjen listesi temizlenir, grup ve süre saklanır", f["alerjen"] == ["gluten"] and f["hazirlik"] == 20 and f["gruplar"][0]["secenekler"][1]["fiyat"] == 15 and f["bolum"] == "Kebaplar")
    r = c.post("/api/yp/products", headers=H, json=urun("Bozuk", 50, {"food": {"gruplar": [{"ad": "Sos", "min": 1, "max": 1, "secenekler": [{"ad": "Acı", "fiyat": 5}]}]}}))
    t("zorunlu seçimde ücretsiz seçenek yoksa reddedilir", r.status_code == 422)
    r = c.post("/api/yp/products", headers=H, json=urun("Ayran", 30, {"food": {"bolum": "İçecek", "aktif": False}})); t("ikinci ürün (pasif)", r.status_code in (200, 201))
    r = c.post("/api/yp/products", headers=H, json=urun("Yeni Tatlı", 70)); t("platformda olmayan ürün", r.status_code in (200, 201))
    c.put("/api/yp/integrations/trendyol_yemek", headers=H, json={"on": True, "keys": {"seller_id": "123", "api_key": "k", "api_secret": "s"}})
    g = c.get("/api/yp/menu/trendyol_yemek", headers=H).json(); R = {x["ad"]: x for x in g["rows"]}
    t("menü okunur, eşleşme ada göre", g["bagli"] and R["Adana Kebap"]["uzak"]["id"] == "1" and R["Yeni Tatlı"]["durum"] == "eslesmedi")
    t("fark: fiyat değişen ve pasif olan işaretlenir", R["Adana Kebap"]["durum"] == "fark" and R["Ayran"]["durum"] == "fark")
    CALLS.clear()
    o = c.post("/api/yp/menu/trendyol_yemek/gonder", headers=H, json={}).json()
    pr = [x for x in CALLS if x[1].endswith("/products/price")]; st = [x for x in CALLS if x[0] == "PUT"]
    t("yalnızca değişen fiyat gönderilir (Adana 260)", len(pr) == 1 and pr[0][3]["items"] == [{"productId": 1, "sellingPrice": 260.0}])
    t("pasif ürün PASSIVE yapılır", len(st) == 1 and st[0][1].endswith("/stores/7/products/2/status") and st[0][3] == {"status": "PASSIVE"})
    t("yanıt: batch, sayılar", o["ok"] and o["batch"] == "b-1" and o["fiyat"] == 1 and o["durum"] == 1)
    t("üstbilgiler (x-agentname) gider", all("x-agentname" in x[2] for x in CALLS))
    s2 = c.get("/api/yp/menu/trendyol_yemek/sonuc/b-1", headers=H).json(); t("toplu sonuç sorgulanır", s2["durum"] == "COMPLETED" and s2["hatali"] == 0)
    r = c.get("/api/yp/menu/yemeksepeti/dosya", headers=H); body = r.content.decode("utf-8-sig")
    t("Yemeksepeti için menü dosyası (CSV)", r.status_code == 200 and "Adana Kebap" in body and "Yan ürün (min 1, max 1): Pilav, Salata +15.00" in body and "gluten" in body)
    y = c.get("/api/yp/menu/yemeksepeti", headers=H).json(); t("diğer platform: gönderim yok, not var", not y["api"] and y.get("not_"))
    t("bilinmeyen platform 404", c.get("/api/yp/menu/xx", headers=H).status_code == 404)
# --- bağlanır bağlanmaz düşen sipariş kaçmaz (otomatik)
import time
NOW = int(time.time() * 1000)
async def fake2(m, u, h, b):
    if "/packages" in u and m == "GET":
        return 200, {"page": 0, "size": 50, "content": [{"id": "z" * 64, "orderNumber": "T-9001", "orderCode": "9A", "packageStatus": "Created", "totalPrice": 120, "packageCreationDate": NOW - 60000,
                      "customer": {"id": 1, "firstName": "Ali", "lastName": "V."}, "address": {"address1": "Kızılay", "city": "Ankara", "district": "Çankaya"},
                      "lines": [{"price": 120, "unitSellingPrice": 120, "productId": 1, "name": "Adana Kebap", "items": [{"packageItemId": "q1", "isCancelled": False}]}]}]}
    return await fake(m, u, h, b)
shop_sync.HTTP["fn"] = fake2
with TestClient(s.app) as c2:
    d = c2.post("/api/public/demo", json={"name": "Mehmet", "phone": "05321110088", "sector": "lokanta"}).json()
    H2 = {"Authorization": "Bearer " + c2.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
    c2.put("/api/yp/integrations/trendyol_yemek", headers=H2, json={"keys": {"seller_id": "123", "api_key": "k", "api_secret": "s"}})
    lst = c2.get("/api/yp/orders?limit=100", headers=H2).json(); txt = str(lst)
    t("bağlantı kurulur kurulmaz 1 dk önce düşen sipariş listede (ilk çekim beklenmeden)", "T-9001" in txt or "9A" in txt)
# --- e-ticaret firması yemek alanlarını görmez
shop_sync.HTTP["fn"] = fake
with TestClient(s.app) as c3:
    d = c3.post("/api/public/demo", json={"name": "Mehmet", "phone": "05321110077", "sector": "eticaret"}).json()
    H3 = {"Authorization": "Bearer " + c3.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
    ch = [x["id"] for x in c3.get("/api/yp/products?limit=1", headers=H3).json()["channels"]]
    t("e-ticaret: ürün kanallarında yemek platformu yok", ch and not any(k in ch for k in ("yemeksepeti", "trendyol_yemek", "getir_yemek", "migros_yemek")) and "trendyol" in ch)
    ig = str(c3.get("/api/yp/integrations", headers=H3).json())
    t("e-ticaret: entegrasyon listesinde yemek platformu yok", "yemeksepeti" not in ig and "trendyol_yemek" not in ig and "Trendyol Yemek" not in ig)
    t("e-ticaret: menü uçları kapalı", c3.get("/api/yp/menu/trendyol_yemek", headers=H3).status_code == 404 and c3.get("/api/yp/menu/yemeksepeti/dosya", headers=H3).status_code == 404)
ch2 = [x["id"] for x in c.get("/api/yp/products?limit=1", headers=H).json()["channels"]]
t("restoran: yalnız site ve yemek platformları", set(ch2) == {"site", "yemeksepeti", "trendyol_yemek", "getir_yemek", "migros_yemek"})
print("OK", ok, "FAIL", bad)
