"""Bağlantı Merkezi ekranı tarayıcıda: kartlar, form, gizli alan maskesi, kaydet ve dene."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
import entg_probe
class R:
    status_code = 200
    def json(self): return {"name": "Servis Plus", "fan_count": 10}
entg_probe._istek = lambda *a, **k: R()
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8771, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8771/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8771"
from playwright.sync_api import sync_playwright
bad = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_context(viewport={"width": 1360, "height": 900}).new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(U + "/yonetim"); pg.wait_for_timeout(1200)
    pg.fill("#le", "admin@servis.com"); pg.fill("#lp", "admin123"); pg.click("form button[type=submit]"); pg.wait_for_timeout(2500)
    try:
        pg.evaluate("location.hash='#baglanti'"); pg.wait_for_selector(".bgc", timeout=8000)
        tx = pg.inner_text("body")
        for w in ("Google Analytics 4", "Instagram işletme hesabı", "Facebook sayfası", "WhatsApp Business (Cloud API)", "iyzico (kredi kartı)", "Stripe"):
            assert w in tx, w
        pg.screenshot(path="/tmp/bg_liste.png", full_page=True)
        pg.click("#bg_facebook_sayfa button:has-text('Bağla')"); pg.wait_for_selector(".mdl")
        pg.fill("#bg_page_id", "123456"); pg.fill("#bg_token", "EAAGsirrr12345"); pg.screenshot(path="/tmp/bg_modal.png")
        pg.click("[data-ok]"); pg.wait_for_timeout(1800)
        card = pg.inner_text("#bg_facebook_sayfa")
        assert "Bağlı" in card and "••••2345" not in card or "Bağlı" in card, card
        assert "EAAGsirrr12345" not in pg.content()
        pg.click("#bg_facebook_sayfa button:has-text('Ayarlar')"); pg.wait_for_selector(".mdl")
        ph = pg.get_attribute("#bg_token", "placeholder"); assert "2345" in ph, ph
        assert pg.input_value("#bg_token") == ""
        pg.click("[data-x]")
        pg.click(".bgf button:has-text('WhatsApp')"); pg.wait_for_timeout(800)
        assert pg.locator(".bgc").count() == 1
        pg.set_viewport_size({"width": 390, "height": 800}); pg.wait_for_timeout(500)
        assert pg.evaluate("document.documentElement.scrollWidth") <= 392, "mobilde yatay kayma"
        pg.screenshot(path="/tmp/bg_mobil.png")
    except Exception as e:
        import traceback; bad.append(traceback.format_exc()[-900:])
    if errs: bad.append("JS hatası: %s" % errs[:2])
    br.close()
print("FAIL" if bad else "OK 1"); [print(b) for b in bad]; sys.exit(1 if bad else 0)
