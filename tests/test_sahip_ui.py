"""Tarayıcıda: sahip paneli yeni kabuk (ikon rayı, üst çubuk, grup sekmeleri)."""
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
    pass
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try:
        sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1440, "height": 900})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:%d/yonetim" % PORT); pg.wait_for_selector("#le", timeout=15000)
    pg.fill("#le", os.environ.get("ADMIN_EMAIL", "admin@servis.com")); pg.fill("#lp", os.environ.get("ADMIN_PASSWORD", "admin123"))
    pg.click("button[type=submit]"); pg.wait_for_selector(".tbar", timeout=15000); pg.wait_for_timeout(800)
    def a():
        assert pg.locator(".side nav a").count() == 5
        assert pg.locator(".gtabs").count() == 0  # Genel Bakış tek sayfa
    t("rayda 5 grup, genel bakışta sekme yok", a)
    def b():
        pg.click(".side nav a:nth-child(3)"); pg.wait_for_selector(".gtabs", timeout=5000)
        tabs = pg.locator(".gtabs a").all_inner_texts()
        assert tabs == ["Firmalar", "Kurulum Adımları", "Toplu İşlemler", "Yetki ve Roller"], tabs
        pg.click(".gtabs a:nth-child(3)"); pg.wait_for_timeout(600)
        assert "toplu" in pg.evaluate("location.hash") and pg.locator(".gtabs a.on").inner_text() == "Toplu İşlemler"
    t("Firmalar grubu sekmeleri çalışıyor", b)
    def c3():
        for r in ["satis", "talepler", "abonelik", "paketler", "alanadlari", "hazirlik", "sistem", "yetki", "genel"]:
            pg.evaluate("location.hash='#%s'" % r); pg.wait_for_timeout(500)
            assert pg.locator(".tbar").count() == 1, r
    t("tüm ekranlar açılıyor", c3)
    t("JavaScript hatası yok", lambda: errs and (_ for _ in ()).throw(AssertionError(errs[:3])))
    pg.evaluate("location.hash='#genel'"); pg.wait_for_timeout(800); pg.screenshot(path="/tmp/sahip1.png")
    pg.evaluate("location.hash='#firmalar'"); pg.wait_for_timeout(800); pg.screenshot(path="/tmp/sahip2.png")
    pg.set_viewport_size({"width": 390, "height": 800}); pg.wait_for_timeout(400); pg.screenshot(path="/tmp/sahip3.png")
    br.close()
srv.should_exit = True
for n in ok: print("  ✓", n)
for n, e in bad: print("  ✗", n, e)
print("OK", len(ok), "FAIL", len(bad)); sys.exit(1 if bad else 0)
