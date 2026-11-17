"""Yeni panel: Yemek menüsü: ürün düzenleyicide yemek bölümü, menü gönderme ekranı, menü dosyası."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests
import shop_sync
from playwright.sync_api import sync_playwright
s = boot.server; ok, bad = [], []
GON = []
async def fake(m, u, h, b):
    GON.append((m, u, b))
    if u.endswith('/stores?page=0&size=50'): return 200, {'restaurants': [{'id': 7, 'name': 'Şube'}]}
    if u.endswith('/stores/7/products'): return 200, {'products': [{'id': 1, 'name': 'Adana Kebap', 'sellingPrice': 250, 'status': 'ACTIVE'}]}
    if u.endswith('/products/price'): return 200, {'batchRequestId': 'b9'}
    if '/batch-requests/' in u: return 200, {'status': 'COMPLETED', 'itemCount': 1, 'failedItemCount': 0, 'items': []}
    return 200, {}
shop_sync.HTTP['fn'] = fake
def t(n, f):
    try: f(); ok.append(n); print("  +", n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:])); print("  -", n)
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try: socket.create_connection(("127.0.0.1", PORT), 0.3).close(); break
    except OSError: time.sleep(0.2)
U = "http://127.0.0.1:%d" % PORT
d = requests.post(U + "/api/public/demo", json={"name": "Mehmet", "phone": "05321110099", "sector": "lokanta"}).json()
O = {"Authorization": "Bearer " + requests.post(U + "/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
requests.put(U + "/api/yp/integrations/trendyol_yemek", headers=O, json={"on": True, "keys": {"seller_id": "123", "api_key": "k", "api_secret": "s"}})
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1366, "height": 1000}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(U + "/salon"); pg.wait_for_selector("#lf"); pg.fill("#lf input[name=email]", d["email"]); pg.fill("#lf input[name=password]", d["password"]); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])")
    def urun():
        pg.evaluate("location.hash='#urun'"); pg.wait_for_selector("[data-a=urun-yeni]", timeout=8000)
        pg.click("[data-a=urun-yeni]"); pg.wait_for_selector("#ue-yemek", timeout=8000)
        pg.fill("input[name=name]", "Adana Kebap"); pg.fill("input[name=price]", "260")
        pg.fill("input[name=food_bolum]", "Kebaplar"); pg.fill("input[name=food_hazirlik]", "20")
        pg.check("[data-al=gluten]")
        pg.click("[data-a=ue-fgekle]"); pg.fill("[data-fg=ad]", "Yan ürün"); pg.fill("[data-fg=min]", "1")
        pg.fill("[data-fo=ad][data-j='0']", "Pilav"); pg.click("[data-a=ue-foekle]"); pg.fill("[data-fo=ad][data-j='1']", "Salata"); pg.fill("[data-fo=fiyat][data-j='1']", "15")
        pg.screenshot(path="/tmp/et/ui-menu-editor.png", full_page=False)
    t("ürün düzenleyicide Yemek menüsü bölümü, seçenek grubu eklenir", urun)
    def kanal():
        pg.evaluate("document.querySelector('#ue-yemek').scrollIntoView()")
        row = pg.query_selector_all("#ue-kanal input[type=checkbox]")
        names = pg.inner_text("#ue-kanal")
        assert "Trendyol Yemek" in names, names[:300]
    t("satış kanallarında yemek pazaryerleri listelenir", kanal)
    def kaydet():
        pg.evaluate("document.querySelector('[data-a=ue-chtog][data-k=trendyol_yemek]').scrollIntoView({block:'center'})"); pg.screenshot(path="/tmp/et/ui-kanal.png"); print("JS", pg.evaluate("(function(){var b=document.querySelector(\"[data-a=ue-chtog][data-k=trendyol_yemek]\");b.click();document.querySelector(\"[data-a=ue-chtog][data-k=yemeksepeti]\").click();return UE.ch.trendyol_yemek.on+\"|\"+(typeof UE)+\"|\"+b.dataset.a})()"))
        pg.click("button[data-a=ue-kaydet][data-v=live]"); pg.wait_for_timeout(1200)
        R0 = requests.get(U + "/api/yp/products?q=Adana", headers=O).json(); rows = R0.get("items") or R0.get("rows") or R0.get("products") or []; print("KEYS", list(R0)[:8])
        it = [x for x in rows if x["name"] == "Adana Kebap"][0]
        f = requests.get(U + "/api/yp/products/" + it["id"], headers=O).json(); f = f.get("item") or f
        assert f["food"]["bolum"] == "Kebaplar" and f["food"]["gruplar"][0]["secenekler"][1]["fiyat"] == 15 and "gluten" in f["food"]["alerjen"], f["food"]
        assert f["channels"].get("trendyol_yemek"), f["channels"]
    t("kaydedilir: bölüm, alerjen, seçenek grubu ve fiyatı", kaydet)
    def ekran():
        pg.evaluate("location.hash='#menusync'"); pg.wait_for_selector("#main table.gr", timeout=8000)
        assert "Adana Kebap" in pg.inner_text("#main") and "Farklı" in pg.inner_text("#main"), pg.inner_text("#main")[:300]
        pg.screenshot(path="/tmp/et/ui-menu-sync.png")
    t("Menü gönder ekranı platformla farkı gösterir", ekran)
    def gonder():
        GON.clear(); pg.click("[data-m=gonder]"); pg.wait_for_timeout(1500)
        assert any(u.endswith("/products/price") and b["items"][0]["sellingPrice"] == 260 for m, u, b in GON), GON
    t("farklar gönderilir (260 ₺)", gonder)
    def dosya():
        pg.click("[data-m=mk][data-v=yemeksepeti]"); pg.wait_for_selector("[data-m=dosya]", timeout=6000)
    t("Yemeksepeti sekmesinde menü dosyası düğmesi", dosya)
    t("JS hatası yok", lambda: (_ for _ in ()).throw(AssertionError(errs)) if errs else None)
    br.close()
print("OK", len(ok), "FAIL", len(bad))
for n, e in bad: print(n, e)
