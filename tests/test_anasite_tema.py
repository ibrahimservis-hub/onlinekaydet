"""Yönetim paneli: tema galerisi + onlinekaydet.com sitesi düzenleyicisi."""
import sys, os, threading, time, socket, tempfile, shutil
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"; os.environ["ANASITE_DIR"] = tempfile.mkdtemp()
import logging; logging.disable(logging.CRITICAL)
import uvicorn
from playwright.sync_api import sync_playwright
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n); print("  +", n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-900:])); print("  -", n)
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try: sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)
import wsgiref  # noqa
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for W, H in ((1440, 900), (390, 800)):
        pg = br.new_page(viewport={"width": W, "height": H}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://127.0.0.1:%d/yonetim" % PORT); pg.wait_for_selector("#le", timeout=15000)
        pg.fill("#le", "admin@servis.com"); pg.fill("#lp", "admin123"); pg.click("button[type=submit]"); pg.wait_for_selector(".tbar", timeout=15000)
        def g():
            pg.evaluate("location.hash='#temalar'"); pg.wait_for_selector("img[src*=tema-thumb]", timeout=8000)
            n = pg.locator("img[src*=tema-thumb]").count(); assert n >= 60, n
            pg.select_option("select >> nth=0", "kombi"); pg.wait_for_timeout(700)
            assert 0 < pg.locator("img[src*=tema-thumb]").count() < 60
            assert pg.locator("a:has-text('Önizle')").first.get_attribute("href").startswith("/tema-onizleme/")
        t("%d: tema galerisi sektöre göre süzülür" % W, g)
        def a():
            pg.evaluate("location.hash='#anasite'"); pg.wait_for_selector("#anaf [data-k]", timeout=8000)
            e = pg.locator("#anaf [data-k^=t]").first; v = e.input_value(); e.fill(v + " DENEME"); pg.click("button.bt.o:has-text(\"Kaydet\")"); pg.wait_for_timeout(900)
            assert "düzenli" in pg.inner_text(".side") + pg.inner_text("body")
        t("%d: ana site metni düzenlenip kaydedilir" % W, a)
        t("%d: JS hatası yok" % W, lambda: (_ for _ in ()).throw(AssertionError(errs)) if errs else None)
        pg.close()
    br.close()
# yayın: düzenlenen sayfa servis edilir
import passenger_wsgi as pw_
pw_._OVR = os.environ["ANASITE_DIR"]
def yay():
    r = pw_._ovr_file("/"); assert r and r.endswith("index.html"), r
    assert "DENEME" in open(r, encoding="utf-8").read()
t("düzenlenen ana sayfa sunucuda önce servis edilir", yay)
print("OK", len(ok), "FAIL", len(bad))
for n, e in bad: print(n, e)
shutil.rmtree(os.environ["ANASITE_DIR"], ignore_errors=True)
