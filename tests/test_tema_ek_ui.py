"""Tarayıcıda: hazır temada 'Bölüm ekle' → kütüphaneden bölüm, listede 'Eklenen', ayarla, kaldır."""
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
    j = c.post("/api/public/demo", json={"name": "Ali", "phone": "05524165755", "sector": "Kombi"}).json()
    EMAIL, PW = j["email"], j["password"]
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
    c.post("/api/yp/sectors/teknik", headers=H, json={})
    async def setup():
        f = await s.db.main().firms.find_one({"login_email": EMAIL}, {"_id": 0, "db": 1})
        await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": "p01-cine-kombi"}}, upsert=True)
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
    def akis():
        pg.evaluate("location.hash='#site'"); pg.wait_for_selector(".stabs button", timeout=10000)
        pg.click('.stabs button[data-t="bolum"]'); pg.wait_for_timeout(250)
        pg.click('[data-a="sted"][data-e="tema"]'); pg.wait_for_selector("#bl .row", timeout=15000)
        n0 = pg.locator("#bl .row").count()
        pg.click('[data-a="tekadd"]'); pg.wait_for_selector(".bxcard", timeout=10000)
        pg.locator('.bxcard[data-b="sayilarla"]').first.click() if pg.locator('.bxcard[data-b="sayilarla"]').count() else pg.locator(".bxcard").first.click()
        pg.wait_for_selector("#bxf", timeout=10000)
        ta = pg.locator('#bxf textarea').first
        if ta.count():
            ta.fill("1500|Mutlu müşteri\n12|Yıllık deneyim\n4|Usta")
        pg.locator('#bxf .mf .btn.p').first.click(); pg.wait_for_timeout(1500)
        assert pg.locator('#bl [data-a="tekset"]').count() == 1, "eklenen bölüm tema listesinde"
        assert pg.locator("#bl .row").count() == n0 + 1
        assert "span style" not in pg.locator("#bl").inner_text(), "ham kod görünmemeli"; pg.locator("#bl [data-a=tekset]").scroll_into_view_if_needed(); pg.wait_for_timeout(300); pg.screenshot(path="/tmp/tema_ek_liste.png", full_page=False)
        pg.click('#bl [data-a="tekset"]'); pg.wait_for_selector("#bxf", timeout=10000)
        pg.evaluate("document.getElementById('ov').hidden=true")
        pg.click('#bl [data-a="tekdel"]'); pg.wait_for_timeout(300)
        okb = pg.locator('#ov button:has-text("Kaldır")')
        if okb.count(): okb.last.click()
        pg.wait_for_timeout(1500)
        assert pg.locator('#bl [data-a="tekset"]').count() == 0
        assert not errs, errs
    t("hazır temada bölüm ekle / ayarla / kaldır", akis)
    def onizleme():
        pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(300)
        pg.click('[data-a="pvdev"][data-d="web"]'); pg.wait_for_timeout(1500)
        w = pg.evaluate("document.getElementById('pvf').style.width"); assert w == "1280px", w
        bw = pg.evaluate("document.getElementById('pvbox').clientWidth"); assert bw > 600, bw
        pg.screenshot(path="/tmp/pv_web.png")
        pg.click('[data-a="pvdev"][data-d="phone"]'); pg.wait_for_timeout(1200)
        assert pg.evaluate("document.getElementById('pvf').style.width") == "413px"
        pg.screenshot(path="/tmp/pv_tel.png")
        pg.click('[data-a="pvgenis"]'); pg.wait_for_timeout(800)
        assert pg.locator(".sitegrid.genis").count() == 1 and not pg.locator("#sl").is_visible()
        pg.click('[data-a="pvdev"][data-d="web"]'); pg.wait_for_timeout(1200)
        pg.screenshot(path="/tmp/pv_genis.png")
        pg.click('[data-a="pvgenis"]'); pg.wait_for_timeout(500)
        assert pg.locator("#sl").is_visible()
        assert not errs, errs
    t("önizleme: gerçek masaüstü genişliği, büyük telefon, geniş mod", onizleme)
    br.close()
srv.should_exit = True
print("ok", len(ok), "bad", len(bad))
for n, e in bad: print("FAIL", n, "\n", e)
