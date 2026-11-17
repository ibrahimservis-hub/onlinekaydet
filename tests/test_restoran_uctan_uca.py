"""Restoran (lokanta) uçtan uca: demo /salon'a gider, eski panel bağlantısı yok, 4 platform bağlanır, siparişler listeye/rapora/kasaya düşer, durum akışı, tekrar sipariş yazılmaz, sahip paneli görür."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
import demo, shop_sync
demo.GUNLUK_LIMIT = 10 ** 6
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8794, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8794/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8794"; B = U + "/api"; ok = bad = 0
def t(n, c):
    global ok, bad
    ok += bool(c); bad += (not c); print(("  ✓ " if c else "  ✗ ") + n)
async def fake(m, u, h, b):
    if "tgoapis" in u:
        return 200, {"content": [{"orderNumber": "T-1", "status": "Created", "totalPrice": 300, "createdDate": 9999999999000, "customer": {"name": "Ayşe Y.", "phone": "05320000000"},
                                   "address": {"fullAddress": "Çankaya"}, "lines": [{"name": "Kebap", "quantity": 2, "price": 150}]}]}
    if "getir.example" in u:
        return 200, {"orders": [{"id": "G1", "status": "NEW", "totalAmount": 120, "items": [{"name": "Lahmacun", "quantity": 3, "price": 40}]}]}
    if "migros.example" in u:
        return 200, {"orders": [{"id": "M1", "status": "PREPARING", "totalAmount": 80, "items": [{"name": "Pide", "quantity": 1, "price": 80}]}]}
    return 200, {"ok": True}
shop_sync.HTTP["fn"] = fake
d = rq.post(B + "/public/demo", json={"name": "Restoran Sahibi", "phone": "05347778899", "sector": "lokanta"}).json()
t("demo yanıtı /salon'a yönlendirir", d.get("panel") == "/salon")
H = {"Authorization": "Bearer " + rq.post(B + "/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
bo = rq.get(B + "/yp/boot", headers=H).json(); t("boot: eski panel kapalı", bo.get("eski_panel") is False)
A = {"Authorization": "Bearer " + rq.post(B + "/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
fid = [f for f in rq.get(B + "/admin/firms", headers=A).json()["firms"] if f.get("demo")][-1]["id"]
P = lambda k, keys: rq.put(B + "/yp/integrations/" + k, headers=H, json={"on": True, "keys": keys}).json()
t("trendyol yemek kaydı", P("trendyol_yemek", {"seller_id": "9", "api_key": "a", "api_secret": "b", "komisyon": "15"}).get("ok"))
t("getir yemek kaydı", P("getir_yemek", {"token": "x", "orders_url": "https://getir.example/o"}).get("ok"))
t("migros yemek kaydı", P("migros_yemek", {"token": "y", "orders_url": "https://migros.example/o"}).get("ok"))
t("yemeksepeti kaydı", P("yemeksepeti", {"webhook_key": "gizli"}).get("ok"))
for k in ("trendyol_yemek", "getir_yemek", "migros_yemek"):
    r = rq.post(B + "/admin/market/%s/test" % k, headers=H); t("%s bağlantı testi" % k, r.status_code == 200 and r.json().get("ok"))
    r = rq.post(B + "/admin/market/%s/pull-orders" % k, headers=H); t("%s sipariş çekimi" % k, r.status_code == 200 and r.json().get("new") == 1)
    r = rq.post(B + "/admin/market/%s/pull-orders" % k, headers=H); t("%s ikinci çekimde tekrar yazmaz" % k, r.json().get("new") == 0)
body = {"orderId": "Y1", "status": "NEW", "totalAmount": 200, "customer": {"name": "Can K.", "phone": "05331112233"}, "items": [{"name": "Döner", "quantity": 2, "price": 100}]}
w = lambda: rq.post(B + "/public/%s~yemek/yemeksepeti?k=gizli" % fid, json=body)
t("yemeksepeti bildirimi", w().json().get("ok")); w()
t("yanlış anahtar 401", rq.post(B + "/public/%s~yemek/yemeksepeti?k=x" % fid, json=body).status_code == 401)
rows = rq.get(B + "/yp/orders?limit=100", headers=H).json()["items"]; no = [x["no"] for x in rows]
t("4 platform siparişi listede, tekrarsız", all(no.count(k) == 1 for k in ("TYY-T-1", "GY-G1", "MY-M1", "YS-Y1")))
t("hazırlanıyor durumu platformdan alındı", [x for x in rows if x["no"] == "MY-M1"][0]["status"] == "hazirlaniyor")
for d_, st in (("kabul", "onaylandi"), ("hazir", "hazirlaniyor"), ("yolda", "kargoda"), ("teslim", "teslim")):
    r = rq.post(B + "/admin/yemek/yemeksepeti/siparis/YS-Y1/durum", headers=H, json={"durum": d_}); t("durum %s" % d_, r.status_code == 200)
rows = rq.get(B + "/yp/orders?limit=100", headers=H).json()["items"]; t("teslim durumu listede", [x for x in rows if x["no"] == "YS-Y1"][0]["status"] == "teslim")
ty = [x for x in rows if x["no"] == "TYY-T-1"][0]; t("trendyol yemek müşteri/ürün/tutar", ty["customer"]["name"] == "Ayşe Y." and ty["total"] == 300 and ty["items"][0]["qty"] == 2)
rp = rq.get(B + "/yp/rapor", headers=H).json(); t("raporlar açılır", rp.get("items") is not None)
ids = [r["id"] for r in rp["items"]]
t("kanal raporu var", "kanal" in ids)
if "kanal" in ids:
    kr = rq.get(B + "/yp/rapor/kanal?a=2020-01-01&b=2099-12-31", headers=H).json(); txt = str(kr)
    t("kanal raporunda platformlar görünür", "Yemeksepeti" in txt and "Trendyol Yemek" in txt and "Getir Yemek" in txt)
t("entegrasyon ekranı bağlı sayar", sum(1 for i in rq.get(B + "/yp/integrations", headers=H).json()["items"] if i["id"] in ("yemeksepeti", "trendyol_yemek", "getir_yemek", "migros_yemek") and i["state"] == "bagli") == 4)
st = rq.get(B + "/admin/market/status", headers=H).json()["markets"]; t("durum ekranı 4 platformu listeler", len([m for m in st if m["id"].endswith("yemek") or m["id"] == "yemeksepeti"]) == 4)
tm = rq.get(B + "/admin/firms/%s/terimler" % fid, headers=A); t("sahip paneli firmayı sipariş ailesi olarak görür", tm.status_code == 200 and tm.json().get("family") == "siparis")
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); pg = br.new_page(viewport={"width": 1440, "height": 900}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(U + "/salon"); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", d["email"]); pg.fill("#lf input[name=password]", d["password"]); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(500)
    t("/salon'da eski panel bağlantısı yok", pg.locator("a.old").count() == 0)
    pg.goto(U + "/salon#siparis"); pg.wait_for_timeout(1800); tx = pg.inner_text("#main")
    t("siparişler ekranında 4 platform", all(k in tx for k in ("Yemeksepeti", "Trendyol Yemek", "Getir Yemek", "Migros Yemek")))
    for h in ("#entegrasyon", "#rapor", "#kasa", "#ekip", "#musteri"):
        pg.goto(U + "/salon" + h); pg.wait_for_timeout(900)
    pg.goto(U + "/salon#entegrasyon"); pg.wait_for_timeout(1500); tx = pg.inner_text("#main")
    t("bağlantı ekranında 4 yemek platformu", all(k in tx for k in ("Yemeksepeti", "Trendyol Yemek", "Getir Yemek", "Migros Yemek")))
    t("ekranlarda JavaScript hatası yok", not errs)
    if errs: print(errs[:3])
print("OK", ok, "FAIL", bad)
