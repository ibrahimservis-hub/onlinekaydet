"""/salon Servis kayıtları (kombi demo): liste, yeni kayıt, usta atama, durum, tamamla (parça + işçilik), iptal, arama; eski panel bağlantısı hâlâ var (servis)."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
import demo; demo.GUNLUK_LIMIT = 10 ** 6
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8796, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8796/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8796"; B = U + "/api"; ok = bad = 0
def t(n, c):
    global ok, bad
    ok += bool(c); bad += (not c); print(("  ✓ " if c else "  ✗ ") + n)
d = rq.post(B + "/public/demo", json={"name": "Servis Sahibi", "phone": "05348887766", "sector": "kombi"}).json()
H = {"Authorization": "Bearer " + rq.post(B + "/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); pg = br.new_page(viewport={"width": 1440, "height": 900}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(U + "/salon"); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", d["email"]); pg.fill("#lf input[name=password]", d["password"]); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(600)
    t("kenar çubuğunda Servis kayıtları var", pg.locator('#nav a[data-g="servis"]').count() == 1)
    pg.goto(U + "/salon#servis"); pg.wait_for_selector("#svlist table, #svlist .empty", timeout=8000); pg.wait_for_timeout(500)
    tx = pg.inner_text("#main"); t("başlık ve örnek kayıtlar", "Servis Kayıtları" in tx or "Servis kayıtları" in tx)
    n0 = pg.locator("#svlist tbody tr").count(); t("demo kayıtları listelendi (%d)" % n0, n0 >= 1)
    pg.screenshot(path="/tmp/servis-liste.png")
    pg.click('[data-a=sv-yeni]'); pg.wait_for_selector("#svn")
    pg.fill("#svn", "Hasan Test"); pg.fill("#svt", "05321234567"); pg.fill("#sva", "Çankaya Ankara"); pg.fill("#svc", "kombi"); pg.fill("#svm", "Test 24")
    pg.fill("#svf", "Kombi su basıncı düşüyor"); pg.select_option("#svp", "acil")
    opts = pg.locator("#svu option").count(); t("usta listesi dolu (%d)" % opts, opts >= 2)
    pg.select_option("#svu", index=1); pg.click("[data-a=sv-kaydet]"); pg.wait_for_timeout(1200)
    pg.fill("#svq", "Hasan Test"); pg.wait_for_timeout(900)
    t("yeni kayıt aramada bulunur", pg.locator("#svlist tbody tr").count() == 1 and "Hasan Test" in pg.inner_text("#svlist"))
    t("usta atanınca durum 'Usta atandı'", "Usta atandı" in pg.inner_text("#svlist"))
    pg.click('[data-a=sv-ac]'); pg.wait_for_selector("[data-a=sv-durum]"); pg.screenshot(path="/tmp/servis-detay.png")
    pg.click('[data-a=sv-durum][data-v=yolda]'); pg.wait_for_timeout(1000); t("yola çıktı", "Yolda" in pg.inner_text("#svlist"))
    pg.click('[data-a=sv-ac]'); pg.wait_for_selector("[data-a=sv-kapat]"); pg.click('[data-a=sv-durum][data-v=basladi]'); pg.wait_for_timeout(1000); t("işlemde", "İşlemde" in pg.inner_text("#svlist"))
    pg.click('[data-a=sv-ac]'); pg.click('[data-a=sv-kapat]'); pg.wait_for_selector("#svw")
    pg.click('[data-a=sv-kapat-ok]'); pg.wait_for_timeout(500); t("boş kapanış reddedilir", pg.locator("#svw").count() == 1)
    pg.fill("#svw", "Genleşme tankı basıncı ayarlandı"); pg.fill("#svpt .pn", "Basınç valfi"); pg.fill("#svpt .pu", "250"); pg.fill("#svl", "400")
    pg.click('[data-a=sv-kapat-ok]'); pg.wait_for_timeout(1500)
    pg.click('[data-a=sv-seg][data-v=tamamlandi]'); pg.wait_for_timeout(800); tx = pg.inner_text("#svlist")
    t("tamamlandı ve tutar 650 ₺", "Hasan Test" in tx and "650" in tx)
    jobs = rq.get(B + "/jobs?q=Hasan", headers=H).json(); j = jobs[0]
    t("API: tamamlandı, parça 250, işçilik 400, toplam 650", j["status"] == "tamamlandi" and j["parts_total"] == 250 and j["labor_fee"] == 400 and j["total_amount"] == 650)
    cash = rq.get(B + "/cash-transactions", headers=H) if False else None
    # ikinci kayıt: iptal
    pg.click('[data-a=sv-yeni]'); pg.wait_for_selector("#svn"); pg.fill("#svn", "Vazgeçen Müşteri"); pg.fill("#svt", "05329998877"); pg.fill("#svf", "Klima gaz"); pg.click("[data-a=sv-kaydet]"); pg.wait_for_timeout(1200)
    pg.click('[data-a=sv-seg][data-v=""]'); pg.fill("#svq", "Vazgeçen"); pg.wait_for_timeout(900)
    pg.click('[data-a=sv-ac]'); pg.click('[data-a=sv-iptal]'); pg.fill("#svr", "Müşteri vazgeçti"); pg.click('[data-a=sv-iptal-ok]'); pg.wait_for_timeout(1200)
    j2 = rq.get(B + "/jobs?q=Vazge", headers=H).json()[0]; t("iptal nedeniyle kaydedildi", j2["status"] == "iptal" and j2.get("cancel_reason") == "Müşteri vazgeçti")
    t("eski panel bağlantısı yok", pg.locator("a.old").count() == 0)
    t("JavaScript hatası yok", not errs)
    if errs: print(errs[:3])
print("OK", ok, "FAIL", bad)
