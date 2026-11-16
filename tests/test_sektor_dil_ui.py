"""Tarayıcıda: Sektör değişince panel metinleri işe uygun olur (randevu → iş emri/seans/dosya; salon → işletme)."""
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
    c.post("/api/yp/sectors/" + os.environ.get("SEK", "kuafor"), headers=H, json={})
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
    SEK = os.environ.get("SEK", "kuafor")
    EXP = {"kuafor": ("Randevu", None), "oto": ("İş Emri", "Randevu"), "avukat": ("Dosya", "Randevu"), "fitness": ("Üye Kaydı", "Randevu"), "market": ("Teslimat", "Randevu"), "teknik": ("Servis Kaydı", "Randevu")}[SEK]
    def a():
        tb = c.get("/api/yp/boot", headers=TK()).json()["terms"]; assert tb["is"] == EXP[0], tb
        pg.evaluate("location.hash='#takvim'"); pg.wait_for_timeout(1500)
        pg.evaluate("location.hash='#randevu'"); pg.wait_for_timeout(1500)
        tx = pg.inner_text("#app")
        assert EXP[0].lower() in tx.lower(), tx[:500]
        if EXP[1]:
            assert EXP[1].lower() not in tx.lower(), "sabit 'randevu' kalmamalı: " + tx[:700]
        pg.screenshot(path="/tmp/sek_%s.png" % SEK)
        if SEK == "avukat":
            pg.evaluate("location.hash='#musteri'"); pg.wait_for_timeout(1500); mt = pg.inner_text("#app")
            assert "Müvekkil" in mt and "Müşteri" not in mt.replace("Mağaza müşteri", ""), mt[:600]
        pg.evaluate("location.hash='#bugun'"); pg.wait_for_timeout(1500)
        tx = pg.inner_text("#app")
        if EXP[1]: assert EXP[1].lower() not in tx.lower() and (SEK == "fitness" or "salon" not in tx.lower()), tx[:700]
    t("panel metinleri sektöre uyuyor: " + SEK, a)
    t("ekranlarda JavaScript hatası yok", lambda: errs and (_ for _ in ()).throw(AssertionError(errs[:3])))
    br.close()
srv.should_exit = True
for n in ok: print("  ✓", n)
for n, e in bad: print("  ✗", n, e)
print("OK", len(ok), "FAIL", len(bad)); sys.exit(1 if bad else 0)
