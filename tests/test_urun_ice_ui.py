"""Tarayıcıda: Excel/CSV ile ürün yükleme sihirbazı (dosya seç → eşle → önizle → yükle → hata dosyası)."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn
from starlette.testclient import TestClient
from playwright.sync_api import sync_playwright
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-900:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ali", "phone": "05524165755", "sector": "Kuaför"}).json()
    EMAIL, PW = j["email"], j["password"]
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
    c.post("/api/yp/sectors/kuafor", headers=H, json={})
    async def setup():
        f = await s.db.main().firms.find_one({"login_email": EMAIL}, {"_id": 0, "db": 1})
        await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": "k5-atolye-kuafor"}}, upsert=True)
        fm = await s.db.main().firms.find_one({"login_email": EMAIL}, {"_id": 0, "modules": 1})
        await s.db.main().firms.update_one({"login_email": EMAIL}, {"$set": {"modules": list(fm.get("modules") or ["servis", "site", "randevu", "muhasebe", "rapor", "sms", "pazarlama", "personel"]) + ["eticaret"]}})
    c.portal.call(setup)
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try:
        sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1440, "height": 960})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:%d/salon" % PORT); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", EMAIL); pg.fill("#lf input[name=password]", PW)
    pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(400)
    def prod():
        H2 = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
        return c.post("/api/yp/products", headers=H2, json={"name": "Deneme Lamba", "price": 500, "cost": 200, "stock": 7, "cat": "Ev"}).json()["id"]
    def TK():
        return {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
    def a():
        pg.evaluate("V.urun().catch(function(){})"); pg.wait_for_timeout(800)
        pg.click("[data-a=urun-ice]"); pg.wait_for_selector("#icef", timeout=5000)
        open("/tmp/ice_test.csv", "w", encoding="utf-8").write("Ürün adı;Stok kodu;Satış fiyatı;Stok\nTabak Seti;TB-1;250;8\nBardak;BR-1;40;20\nHatalı;HT-1;abc;1\n")
        pg.set_input_files("#icef", "/tmp/ice_test.csv")
        pg.wait_for_selector("[data-ice=name]", timeout=8000)
        assert pg.input_value("[data-ice=name]") == "Ürün adı" and pg.input_value("[data-ice=price]") == "Satış fiyatı"
        pg.click("[data-a=ice-onizle]"); pg.wait_for_selector("text=Önizleme", timeout=8000)
        tx = pg.inner_text("#ov")
        assert "2 yeni ürün" in tx.replace("\n", " ") and "Satır 4" in tx, tx
        pg.screenshot(path="/tmp/ice_onizleme.png")
        pg.click("[data-a=ice-calistir]"); pg.wait_for_selector("text=Yükleme bitti", timeout=8000)
        assert "2" in pg.inner_text("#ov") and pg.is_visible("[data-a=ice-hata]")
        with pg.expect_download() as dl:
            pg.click("[data-a=ice-hata]")
        assert "hata" in dl.value.suggested_filename
        pg.click("#ov [data-a=close]"); pg.wait_for_timeout(800)
        rows = c.get("/api/yp/products", headers=TK()).json()["rows"]
        assert {r["sku"] for r in rows} >= {"TB-1", "BR-1"} and "HT-1" not in {r["sku"] for r in rows}
        assert "Tabak Seti" in pg.inner_text("body")
    t("sihirbaz: dosya seç, eşle, önizle, yükle, hata dosyası, liste yenilenir", a)
    assert not errs, errs
    br.close()
print("OK", len(ok), "FAIL", len(bad))
for n in ok: print("  ✓", n)
for n, tb in bad: print("  ✗", n, "\n", tb)
