"""Tarayıcıda: Sipariş ekle penceresi (telefonla sipariş). Eski: 'Bölüm ekle' → kütüphaneden bölüm, listede 'Eklenen', ayarla, kaldır."""
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
    pid = prod()
    def a():
        pg.evaluate("V.siparis().catch(function(){})"); pg.wait_for_timeout(800)
        pg.click("[data-a=sip-yeni]"); pg.wait_for_selector("#snf", timeout=5000)
        pg.fill("#snf input[name=name]", "Test Müşteri"); pg.fill("#snf input[name=phone]", "05321112233")
        pg.fill("#snq", "Deneme"); pg.wait_for_selector("[data-a=sn-ekle]", timeout=5000)
        pg.click("[data-a=sn-ekle]"); pg.wait_for_selector("#snl table", timeout=3000)
        assert "Telefonla" in pg.locator("#snf select[name=channel]").inner_text()
        pg.click("#snf button[type=submit]"); pg.wait_for_selector("#snf", state="detached", timeout=5000)
        r = c.get("/api/yp/orders", headers={"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}).json()
        assert any(o["channel"] == "telefon" for o in r["items"]), r["items"]
    t("Sipariş ekle penceresi: ürün ara, ekle, kaydet", a)
    assert not errs, errs
    br.close()
for n in ok: print("  ✓", n)
for n, e in bad: print("  ✗", n, "\n", e)
print("OK %d FAIL %d" % (len(ok), len(bad)))
