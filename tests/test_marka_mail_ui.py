"""Panelde Marka ve SEO + Müşteri e-postaları sayfaları gerçek tarayıcıda: menüde görünür, çizilir, kaydeder, hata vermez."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn
from starlette.testclient import TestClient
from playwright.sync_api import sync_playwright
s = boot.server
ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-900:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165766", "sector": "E-ticaret"}).json()
    EMAIL, PW = j["email"], j["password"]
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
    c.post("/api/yp/sectors/eticaret", headers=H, json={})
    for nm, br in [("Keten Gömlek", "Nevermore"), ("Yün Kazak", "Nevermore"), ("Çorap", "Soft")]:
        c.post("/api/yp/products", headers=H, json={"name": nm, "price": 100, "cost": 10, "stock": 5, "cat": "Giyim", "brand": br, "channels": {"site": True}})
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try: sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)
U = "http://127.0.0.1:%d/salon" % PORT
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1440, "height": 900}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(U); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", EMAIL); pg.fill("#lf input[name=password]", PW)
    pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(600)

    def a():
        nav = pg.eval_on_selector_all("#nav a[data-rs]", "a=>a.flatMap(x=>x.dataset.rs.split(','))")
        assert "markaseo" in nav and "musterimail" in nav, nav
    t("menüde Marka ve SEO ile Müşteri e-postaları var", a)

    def m():
        pg.evaluate("location.hash='#markaseo'"); pg.wait_for_selector("#mst-product_title", timeout=8000)
        txt = pg.inner_text("#main")
        assert "Nevermore" in txt and "Soft" in txt and "/magaza/marka/nevermore" in txt, txt[:400]
        pg.fill("#mst-product_title", "{urun} | {kategori} | {firma}"); pg.wait_for_timeout(150)
        assert "Örnek Ürün | Örnek Kategori |" in pg.inner_text("#msp-product_title")
        pg.click("[data-a=ms-kaydet]"); pg.wait_for_selector("#toast:not([hidden])", timeout=4000)
        pg.click("[data-a=ms-duz][data-id=nevermore]"); pg.wait_for_selector("#msf", timeout=4000)
        pg.fill("#msd", "Giyim markası"); pg.click("[data-a=ms-ykaydet]"); pg.wait_for_timeout(700)
        assert "içerik yok" in pg.inner_text("tr:has-text('Soft')") and "içerik yok" not in pg.inner_text("tr:has-text('Nevermore')")
    t("Marka ve SEO: liste, şablon önizleme, kayıt, marka düzenleme", m)

    def e():
        pg.evaluate("location.hash='#musterimail'"); pg.wait_for_selector("#mm-body", timeout=8000)
        assert "SMTP" in pg.inner_text("#main")
        pg.click("[data-a=mm-sec][data-id=kargoya_verildi]"); pg.wait_for_timeout(200)
        assert "{takip_no}" in pg.input_value("#mm-body")
        pg.click("[data-a=mm-ekle][data-id=firma]"); assert "{firma}" in pg.input_value("#mm-body")
        pg.check("#mm-on"); pg.click("[data-a=mm-kaydet]"); pg.wait_for_timeout(600)
        assert pg.is_checked("#mm-on")
        pg.fill("#mm-to", "a@b.co"); pg.click("[data-a=mm-deneme]"); pg.wait_for_selector("#toast.bad", timeout=4000)
    t("Müşteri e-postaları: sekmeler, değişken ekleme, kaydet, SMTP yokken deneme uyarısı", e)

    def r():
        pg.set_viewport_size({"width": 390, "height": 800}); pg.evaluate("location.hash='#markaseo'"); pg.wait_for_timeout(500)
        assert pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"), "yatay taşma"
        pg.evaluate("location.hash='#musterimail'"); pg.wait_for_timeout(500)
        assert pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"), "yatay taşma (e-posta)"
    t("telefonda yatay taşma yok", r)
    def h():
        sor = [x for x in errs if "422" not in x]       # 422: SMTP yokken deneme gönderiminin beklenen reddi
        assert not sor, sor[:3]
    t("tarayıcı hatası yok", h)
    b.close()
for n in ok: print("  ✓", n)
for n, tb in bad: print("  ✗", n, "\n", tb)
print("OK %d FAIL %d" % (len(ok), len(bad))); os._exit(1 if bad else 0)
