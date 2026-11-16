"""Tarayıcıda: Ortaklar ekranı (ortak ekle, link, komisyon, ödeme)."""
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
    async def fid_(): return (await s.db.main().firms.find_one({"login_email": EMAIL}, {"_id": 0, "id": 1}))["id"]
    FID = c.portal.call(fid_)
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
        T = TK()
        c.put("/api/site/features", headers=T, json={"shop_enabled": True, "customer_portal_enabled": True})
        c.put("/api/shop/settings", headers=T, json={"shipping_fee": 0, "bank_accounts": [{"bank": "Ziraat", "holder": "M", "iban": "TR330006100519786457841326"}]})
        pid = c.post("/api/yp/products", headers=T, json={"name": "Tabak Seti", "price": 1000, "cost": 500, "sku": "TB", "stock": 20}).json()["id"]
        pg.evaluate("location.hash='#ortak'"); pg.wait_for_selector("[data-a=or-yeni]", timeout=8000)
        assert "Henüz ortak yok" in pg.inner_text("#main")
        pg.click("[data-a=or-yeni]"); pg.wait_for_selector("#orf", timeout=5000)
        pg.fill("#orf [name=name]", "Ayşe Blog"); pg.fill("#orf [name=phone]", "0533 111 22 33"); pg.fill("#orf [name=pct]", "12"); pg.fill("#orf [name=code]", "AYSE12")
        pg.click("#orf button.p"); pg.wait_for_selector("text=Ayşe Blog", timeout=5000); pg.wait_for_timeout(400)
        tx = pg.inner_text("#main"); assert "AYSE12" in tx and "%12" in tx, tx
        rr = c.post("/api/public/customer/%s~register" % FID, json={"name": "Veli", "phone": "0532 000 11 22", "password": "parola1234"}); H = {"Authorization": "Bearer " + rr.json()["token"]}
        r = c.post("/api/public/shop/%s~orders" % FID, headers=H, json={"customer": {"name": "Veli", "phone": "0532 000 11 22", "address": "Atatürk cad. 12 Ankara"}, "items": [{"product_id": pid, "qty": 1}], "accept_terms": True, "payment_method": "havale", "ref": "AYSE12"}); assert r.status_code == 200, r.text
        no = r.json()["order_no"]; o = [x for x in c.get("/api/shop/orders", headers=T).json() if x["order_no"] == no][0]
        assert c.put("/api/shop/orders/" + o["id"], headers=T, json={"status": "teslim_edildi"}).status_code == 200
        pg.evaluate("V.ortak().catch(function(){})"); pg.wait_for_timeout(900)
        assert "120" in pg.inner_text("#main"), pg.inner_text("#main")
        pg.screenshot(path="/tmp/ortak_liste.png")
        pg.click("[data-a=or-detay]"); pg.wait_for_selector("[data-a=or-ode]", timeout=5000)
        assert no in pg.inner_text("#ov")
        pg.click("[data-a=or-ode]"); pg.wait_for_selector("#askok", timeout=4000); pg.click("#askok"); pg.wait_for_timeout(1200)
        row = c.get("/api/yp/ortak", headers=T).json()["rows"][0]; assert row["paid"] == 120 and row["approved"] == 0, row
        pg.click("[data-a=or-duzenle]"); pg.wait_for_selector("#orf", timeout=5000)
        pg.select_option("#orf [name=status]", "passive"); pg.click("#orf button.p"); pg.wait_for_timeout(900)
        assert "pasif" in pg.inner_text("#main")
    t("ortaklar: ekle, sipariş komisyonu, ödendi işaretle, pasife al", a)
    t("ekranlarda JavaScript hatası yok", lambda: errs and (_ for _ in ()).throw(AssertionError(errs[:3])))
    br.close()
srv.should_exit = True
for n in ok: print("  ✓", n)
for n, e in bad: print("  ✗", n, e)
print("OK", len(ok), "FAIL", len(bad)); sys.exit(1 if bad else 0)
