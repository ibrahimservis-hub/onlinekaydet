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
    def fe(js):
        for f in pg.frames:
            if f.url.startswith("blob:"):
                return f.evaluate(js)
    def nav_ui():
        pg.evaluate("location.hash='#site'"); pg.wait_for_selector(".stabs button", timeout=10000)
        pg.click('.stabs button[data-t="bolum"]'); pg.wait_for_timeout(250)
        pg.click('[data-a="sted"][data-e="tema"]'); pg.wait_for_selector("#bl .row", timeout=15000)
        pg.wait_for_selector("#nvc .nvd", timeout=10000)
        assert pg.locator("#nvc details.nvd").count() == 4
        names = pg.locator("#nvc summary b").all_inner_texts(); assert names == ["Tüm tema", "Üst menü (bilgisayar)", "Mobil menü", "Mobil alt çubuk"], names
        pg.click('#nvc details[data-id="tw"] summary'); pg.wait_for_timeout(300)
        pg.evaluate("var i=document.querySelector('[data-nv=\\'tw.ac\\']');i.value='#c2185b';i.dispatchEvent(new Event('input',{bubbles:true}))")
        pg.select_option('[data-nv="tw.kose"]', "keskin"); pg.select_option('[data-nv="tw.fd"]', "Playfair Display")
        pg.wait_for_timeout(2500)
        fr = pg.frame_locator("#pvf")
        css = fe("document.getElementById('oktw').textContent")
        assert "#c2185b" in css and "Playfair" in css, css
        pg.screenshot(path="/tmp/nv_tw.png")
        pg.click('#nvc details[data-id="drw"] summary'); pg.wait_for_timeout(2500)
        assert pg.evaluate("document.getElementById('pvf').style.width") == "413px", "mobil menü açılınca telefon önizleme"
        assert fe("document.getElementById('mn').checked"), "çekmece önizlemede açık"
        pg.evaluate("var i=document.querySelector('[data-nv=\\'nav.drw.bg\\']');i.value='#1b5e20';i.dispatchEvent(new Event('input',{bubbles:true}))")
        pg.wait_for_timeout(2600)
        assert fe("document.getElementById('mn').checked"), "kayıttan sonra da açık"
        pg.screenshot(path="/tmp/nv_drw.png")
        pg.click('#nvc details[data-id="bar"] summary'); pg.wait_for_timeout(300)
        n0 = pg.locator("#nvc details[data-id=bar] .nvr:not(.add)").count(); assert n0 >= 4, n0
        pg.fill('#nvl', "Konumumuz"); pg.fill('#nvh', "/iletisim"); pg.click('[data-a="nvxadd"]'); pg.wait_for_timeout(2600)
        assert pg.locator("#nvc details[data-id=bar] .nvr:not(.add)").count() == n0 + 1
        pg.click('[data-a="nvup"][data-i="1"]'); pg.wait_for_timeout(2600)
        bar = fe("document.querySelector('[data-oknav=bar]').innerText")
        assert "Konumumuz" in bar, bar
        pg.screenshot(path="/tmp/nv_bar.png")
        pg.evaluate("document.querySelector('#nvc details[data-id=tw]').open=true"); pg.wait_for_timeout(200); pg.click('[data-a="nvtwreset"]'); pg.wait_for_timeout(2500)
        assert fe("!document.getElementById('oktw')")
        assert not errs, errs
    t("hazır tema: tüm tema + menü + mobil menü + alt çubuk tasarımı", nav_ui)
print("OK", len(ok), "FAIL", len(bad))
for n, e in bad: print("---", n, e)
