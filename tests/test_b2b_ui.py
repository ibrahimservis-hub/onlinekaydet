"""Tarayıcıda: Bayiler ekranı (grup, başvuru onayı, cari ekstre, toptan fiyat)."""
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
        F = FID
        pid = c.post("/api/yp/products", headers=T, json={"name": "Tabak Seti", "price": 1000, "cost": 500, "sku": "TB", "stock": 20}).json()["id"]
        rr = c.post("/api/public/customer/%s~register" % F, json={"name": "Ali Bayi", "phone": "0532 555 11 22", "password": "parola1234"}); assert rr.status_code in (200, 201), rr.text
        H = {"Authorization": "Bearer " + rr.json()["token"]}
        assert c.post("/api/public/b2b/%s~apply" % F, headers=H, json={"company": "Ali Hırdavat Ltd.", "tax_no": "1234567890", "address": "Sanayi sitesi 5. blok Ankara"}).status_code == 200
        pg.evaluate("V.bayi().catch(function(){})"); pg.wait_for_selector("text=Ali Hırdavat Ltd.", timeout=8000)
        assert "Onay bekliyor" in pg.inner_text("#main")
        pg.click("[data-a=by-gruplar]"); pg.wait_for_selector("#bygf", timeout=5000)
        pg.fill("#bygf [name=name]", "Altın bayi"); pg.fill("#bygf [name=discount_pct]", "20"); pg.fill("#bygf [name=min_order]", "500")
        pg.click("#bygf button.p"); pg.wait_for_selector("text=Altın bayi", timeout=5000)
        assert "%20" in pg.inner_text("#ov")
        pg.click("#ov [data-a=close]"); pg.wait_for_timeout(300)
        pg.click("[data-a=by-duzenle]"); pg.wait_for_selector("#byf", timeout=5000)
        pg.select_option("#byf [name=status]", "approved"); pg.select_option("#byf [name=group_id]", label="Altın bayi (%20)")
        pg.fill("#byf [name=credit_limit]", "3000"); pg.click("#byf button.p"); pg.wait_for_selector("text=Onaylı", timeout=5000)
        pg.wait_for_timeout(500)
        assert "Altın bayi" in pg.inner_text("#main") and "3.000" in pg.inner_text("#main"), pg.inner_text("#main")
        pg.screenshot(path="/tmp/bayi_liste.png")
        pg.click("[data-a=by-ekstre]"); pg.wait_for_selector("#byl", timeout=5000)
        pg.fill("#byl [name=tutar]", "250"); pg.fill("#byl [name=aciklama]", "Peşin tahsilat"); pg.select_option("#byl [name=tur]", "borc"); pg.click("#byl button.p")
        pg.wait_for_selector("text=Peşin tahsilat", timeout=5000)
        assert "250" in pg.inner_text("#ov")
        pg.click("#ov [data-a=close]"); pg.wait_for_timeout(300)
        pg.click("[data-a=by-fiyat]"); pg.wait_for_selector(".byp", timeout=5000)
        pg.fill(".byp", "700"); pg.click("[data-a=by-fkaydet]"); pg.wait_for_timeout(800)
        me = c.get("/api/public/b2b/%s~products" % F, headers=H).json()
        row = [x for x in me["rows"] if x["sku"] == "TB"][0]
        assert row["price"] == 700 and me["bayi"]["bakiye"] == 250 and me["bayi"]["status"] == "approved", (row, me["bayi"])
    t("bayiler: grup oluştur, başvuruyu onayla, cari kaydı, toptan fiyat", a)
    assert not errs, errs
    br.close()
print("OK", len(ok), "FAIL", len(bad))
for n in ok: print("  ✓", n)
for n, tb in bad: print("  ✗", n, "\n", tb)
