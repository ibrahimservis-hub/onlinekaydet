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
    def fe(js):
        for f in pg.frames:
            if f.url.startswith("blob:"):
                return f.evaluate(js)
    def nav():
        pg.reload(); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(600)
        txt = pg.locator("nav, #nav, .nav, aside").first.inner_text()
        for w in ("Ürünler", "Siparişler", "Kampanyalar", "Pazaryerleri", "İadeler"):
            assert w in txt, (w, txt)
        pg.evaluate("location.hash='#pazaryeri'"); pg.wait_for_timeout(1500)
        m = pg.locator("#main").inner_text()
        assert "Trendyol" in m and "Hepsiburada" in m, m[:400]
        pg.screenshot(path="/tmp/es_pazar.png")
    t("e-ticaret açılınca menüde mağaza alanları ve pazaryerleri", nav)
    def kutup():
        pg.evaluate("location.hash='#site'"); pg.wait_for_selector(".stabs button", timeout=10000)
        pg.click('.stabs button[data-t="bolum"]'); pg.wait_for_timeout(250)
        pg.click('[data-a="sted"][data-e="tema"]'); pg.wait_for_selector("#bl .row", timeout=15000)
        pg.click('[data-a="tekadd"]'); pg.wait_for_selector(".bxcard", timeout=10000)
        pg.click('[data-a="bxcat"][data-c="eticaret"]'); pg.wait_for_timeout(800)
        n = pg.locator("#bxg .bxcard").count(); assert n >= 15, n
        pg.wait_for_timeout(3500)
        canli = pg.locator("#bxg .bxlive iframe").count(); assert canli >= 4, canli
        pg.screenshot(path="/tmp/es_kutup.png")
        pg.locator('#bxg .bxcard[data-b="v_indirim"] [data-a="bxprev"]').click(); pg.wait_for_timeout(2500)
        assert pg.locator("#bxpvo:not([hidden]) #bxpvf").count() == 1
        pg.screenshot(path="/tmp/es_pv_web.png")
        pg.click('[data-a="bxpvdev"][data-d="phone"]'); pg.wait_for_timeout(2500)
        pg.screenshot(path="/tmp/es_pv_tel.png")
        pg.click('[data-a="bxpvekle"]'); pg.wait_for_timeout(2500)
        pg.screenshot(path="/tmp/es_ekle.png"); print("TOAST", pg.evaluate("(document.querySelector('#toast,.toast')||{}).innerText"), pg.evaluate("document.getElementById('ov').hidden"))
        assert pg.locator("#bxf").count() or pg.locator('#bl [data-a="tekset"]').count(), "eklendi"
        assert not errs, errs
    t("kuaförde bile e-ticaret bölümleri kütüphanede, canlı önizlemeli", kutup)
print("OK", len(ok), "FAIL", len(bad))
for n, e in bad: print("---", n, e)
