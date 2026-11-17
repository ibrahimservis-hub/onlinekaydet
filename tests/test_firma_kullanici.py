"""Müşteri paneli: ek kullanıcı ekleme, rol ile yetkilendirme, giriş (API + ekran)."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests
from playwright.sync_api import sync_playwright
import demo; demo.GUNLUK_LIMIT = 10 ** 6
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n); print("  +", n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-700:])); print("  -", n)
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try: sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)
U = "http://127.0.0.1:%d" % PORT
d = requests.post(U + "/api/public/demo", json={"name": "Deneme Kisi", "phone": "05530009911", "sector": "kuafor"}).json()
def login(e, p):
    r = requests.post(U + "/api/auth/login", json={"email": e, "password": p}); return r, {"Authorization": "Bearer " + r.json().get("token", "")}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1280, "height": 900}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(U + "/salon"); pg.wait_for_selector("#lf"); pg.fill("#lf input[name=email]", d["email"]); pg.fill("#lf input[name=password]", d["password"]); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])")
    def ekle():
        pg.evaluate("location.hash='#ayar'"); pg.wait_for_selector("#fucard:not([hidden])", timeout=8000)
        pg.click("[data-a=fu-new]"); pg.fill("#fuf input[name=name]", "Muhasebeci Ayşe"); pg.fill("#fuf input[name=email]", "ayse@deneme.com"); pg.fill("#fuf input[name=password]", "Sifre12345")
        pg.select_option("#fuf select[name=rol]", "accounting"); pg.click("#fuf button.p"); pg.wait_for_selector("#fusub td:has-text('ayse@deneme.com')", timeout=6000)
        assert "Muhasebe" in pg.inner_text("#fusub")
    t("panelden kullanıcı eklenir ve listelenir", ekle)
    r, H = login("ayse@deneme.com", "Sifre12345")
    t("eklenen kullanıcı giriş yapar", lambda: (r.status_code == 200 or (_ for _ in ()).throw(AssertionError(r.text))))
    def yetki():
        g = lambda p: requests.get(U + p, headers=H).status_code
        assert g("/api/yp/boot") == 200 and g("/api/cash/summary") == 200
        assert g("/api/customers") == 200 and g("/api/site/profile") == 403
        assert requests.post(U + "/api/customers", headers=H, json={"name": "T", "phone": "05551112233"}).status_code == 403
        assert requests.post(U + "/api/firm/users", headers=H, json={"email": "x@deneme.com", "password": "Sifre12345"}).status_code == 403
    t("muhasebe rolü kasayı yönetir, diğerini yalnız okur, kullanıcı ekleyemez", yetki)
    def duzenle():
        pg.click("[data-a=fu-edit]"); pg.select_option("#fuf select[name=rol]", "viewer"); pg.click("#fuf button.p"); pg.wait_for_selector("#fusub td:has-text('Yalnızca görüntüleme')", timeout=6000)
        time.sleep(31)
        r2, H2 = login("ayse@deneme.com", "Sifre12345")
        assert requests.post(U + "/api/customers", headers={"Authorization": "Bearer " + r2.json()["token"]}, json={"name": "T", "phone": "05551112233"}).status_code == 403
        assert requests.get(U + "/api/customers", headers={"Authorization": "Bearer " + r2.json()["token"]}).status_code == 200
    t("rol değişince yetki değişir (görüntüleme: yazamaz)", duzenle)
    def pasif():
        pg.click("[data-a=fu-edit]"); pg.uncheck("#fuf input[name=active]"); pg.click("#fuf button.p"); pg.wait_for_selector("#fusub td:has-text('Pasif')", timeout=6000)
        assert login("ayse@deneme.com", "Sifre12345")[0].status_code in (401, 403)
    t("pasif kullanıcı giriş yapamaz", pasif)
    def sil():
        pg.once("dialog", lambda dl: dl.accept()); pg.click("[data-a=fu-del]"); pg.wait_for_selector("#fusub .empty", timeout=6000)
    t("kullanıcı silinir", sil)
    t("JS hatası yok", lambda: (_ for _ in ()).throw(AssertionError(errs)) if errs else None)
    br.close()
print("OK", len(ok), "FAIL", len(bad))
for n, e in bad: print(n, e)
