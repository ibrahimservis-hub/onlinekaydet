"""Site demo formu: sektör seç, SMS kodu iste, kodu gir, hesap bilgileri ve panele gir (API taklit edilir)."""
import json, subprocess, time, os, sys
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8793"], cwd=os.path.join(os.path.dirname(__file__), "..", "site"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
from playwright.sync_api import sync_playwright
bad = []; calls = []
def js(r, body, st=200): r.fulfill(status=st, content_type="application/json", body=json.dumps(body))
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = br.new_page(viewport={"width": 390, "height": 800}); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("**/*pexels*", lambda r: r.abort())
        pg.route("**/api/public/track", lambda r: js(r, {"ok": True}))
        pg.route("**/api/public/demo/ayar", lambda r: js(r, {"kod": True, "sektorler": [{"k": "kuafor", "ad": "Kuaför"}, {"k": "kombi", "ad": "Kombi servisi"}]}))
        pg.route("**/api/public/demo/kod", lambda r: (calls.append(("kod", r.request.post_data_json)), js(r, {"ok": True, "kod": True})))
        def demo(r):
            b = r.request.post_data_json; calls.append(("demo", b))
            js(r, {"ok": True, "email": "demo9@demo.onlinekaydet.com", "password": "abc12345", "tech_email": "usta1.x@demo.onlinekaydet.com", "days": 7, "panel": "/salon"}) if b.get("code") == "123456" else js(r, {"detail": "Doğrulama kodu hatalı"}, 422)
        pg.route("**/api/public/demo", demo)
        pg.route("**/api/auth/login", lambda r: js(r, {"token": "tok123"}))
        pg.goto("http://127.0.0.1:8793/demo.html"); pg.wait_for_timeout(1200)
        pg.fill("#d1", "Ayşe Test"); pg.fill("#d2", "05321112233")
        pg.click(".dform a.bt"); pg.wait_for_timeout(500)
        if "sektör" not in pg.inner_text(".dform").lower() or "Lütfen sektörünüzü" not in pg.inner_text(".dform"): bad.append("sektör zorunlu değil")
        pg.select_option("#d4", "kuafor"); pg.click(".dform a.bt"); pg.wait_for_timeout(900)
        if not pg.is_visible("#d5") or not [c for c in calls if c[0] == "kod"]: bad.append("kod istenmedi")
        pg.fill("#d5", "000000"); pg.click(".dform a.bt"); pg.wait_for_timeout(900)
        if "hatalı" not in pg.inner_text(".dform"): bad.append("yanlış kod mesajı yok")
        pg.fill("#d5", "123456"); pg.click(".dform a.bt"); pg.wait_for_timeout(1200)
        t = pg.inner_text(".dform")
        if "demo9@demo.onlinekaydet.com" not in t or "abc12345" not in t: bad.append("hesap bilgisi görünmüyor: " + t[:120])
        pg.click("#dgopanel"); pg.wait_for_timeout(800)
        if "/salon" not in pg.url: bad.append("panele gitmedi: " + pg.url)
        if errs: bad.append(errs[:2])
        pg.screenshot(path="/tmp/demo_form.png")
        br.close()
finally:
    srv.terminate()
print("GEÇTİ" if not bad else "BAŞARISIZ %s" % bad)
