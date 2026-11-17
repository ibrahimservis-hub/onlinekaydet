"""Alan adı bağlama: /salon'da Alan adı ekranı (ekle, DNS kontrol, kaldır), DNS yönlenmeyen alan adı yayına girmez, sahip onayıyla yayına girer ve Host ile firmanın sitesi açılır."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
import demo; demo.GUNLUK_LIMIT = 10 ** 6
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8801, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8801/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8801"; B = U + "/api"; ok = bad = 0
def t(n, c):
    global ok, bad
    ok += bool(c); bad += (not c); print(("  ✓ " if c else "  ✗ ") + n)
d = rq.post(B + "/public/demo", json={"name": "Alan Adi Deneme", "phone": "05348887711", "sector": "kuafor"}).json()
H = {"Authorization": "Bearer " + rq.post(B + "/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
OW = {"Authorization": "Bearer " + rq.post(B + "/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); pg = br.new_page(viewport={"width": 390, "height": 800}, is_mobile=True); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(U + "/salon"); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", d["email"]); pg.fill("#lf input[name=password]", d["password"]); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000)
    pg.goto(U + "/salon#alanadi"); pg.wait_for_selector("#xdn", timeout=8000); t("Web sitem altında Alan adı ekranı açılır", "Alan adı ekle" in pg.inner_text("#main"))
    pg.screenshot(path="/tmp/alan-bos.png")
    pg.fill("#xdn", "https://www.Deneme-Kuafor.com/"); pg.click("[data-a=x4-ekle]"); pg.wait_for_selector("text=DNS kayıtlarını girin", timeout=6000) if False else pg.wait_for_timeout(1200)
    dl = rq.get(B + "/firm/domain", headers=H).json()["domains"]; t("alan adı temizlenip kaydedildi (deneme-kuafor.com), beklemede", len(dl) == 1 and dl[0]["domain"] == "deneme-kuafor.com" and dl[0]["status"] == "beklemede")
    t("kartta alan adı ve DNS bekleniyor etiketi", "deneme-kuafor.com" in pg.inner_text("#main") and "DNS bekleniyor" in pg.inner_text("#main"))
    t("DNS kayıtları ve adımlar gösterilir", "DNS kayıtları" in pg.inner_text("#main") and "Kontrol et" in pg.inner_text("#main"))
    pg.screenshot(path="/tmp/alan-dolu.png")
    pg.click("[data-a=x4-kontrol]"); pg.wait_for_timeout(1500)
    t("DNS yönlenmeyen alan adı yayına girmez", rq.get(B + "/firm/domain", headers=H).json()["domains"][0]["status"] == "beklemede")
    t("yanlış alan adı reddedilir", rq.post(B + "/firm/domain", headers=H, json={"domain": "gecersiz"}).status_code == 422)
    t("platform alan adı reddedilir", rq.post(B + "/firm/domain", headers=H, json={"domain": "x.onlinekaydet.com"}).status_code == 422)
    # başka firma aynı alan adını alamaz
    d2 = rq.post(B + "/public/demo", json={"name": "Ikinci Firma", "phone": "05348887722", "sector": "kombi"}).json(); H2 = {"Authorization": "Bearer " + rq.post(B + "/auth/login", json={"email": d2["email"], "password": d2["password"]}).json()["token"]}
    t("aynı alan adı başka firmaya bağlanamaz (409)", rq.post(B + "/firm/domain", headers=H2, json={"domain": "deneme-kuafor.com"}).status_code == 409)
    # sahip onayı: yayına al, Host ile site açılır
    r = rq.put(B + "/admin/domains/deneme-kuafor.com/status", headers=OW, json={"status": "yayinda"}); t("sahip alan adını yayına alır", r.status_code == 200)
    time.sleep(0.2)
    s = rq.get(B + "/public/hosted-site?p=/", headers={"Host": "www.deneme-kuafor.com"}); t("alan adından gelen istek firmanın sitesini açar (200, HTML)", s.status_code == 200 and "<html" in s.text.lower())
    s2 = rq.get(B + "/public/hosted-site?p=/", headers={"Host": "baska-alan.com"}); t("bağlı olmayan alan adı firmanın sitesini açmaz", not (s2.status_code == 200 and "<html" in s2.text.lower() and "deneme" in s2.text.lower()))
    pg.reload(); pg.wait_for_selector("#xdn"); t("yayındaki alan adı kartında bağlantı mesajı", "sitenize bağlı" in pg.inner_text("#main"))
    pg.click("[data-a=x4-onay]"); pg.click("[data-a=x4-sil]"); pg.wait_for_timeout(1200); t("alan adı kaldırılır", rq.get(B + "/firm/domain", headers=H).json()["domains"] == [])
    # passenger_wsgi: /salon panel yolu özel alan adında siteye çevrilmez
    src = open(os.path.join(os.path.dirname(__file__), "..", "panel", "passenger_wsgi.py"), encoding="utf-8").read(); t("özel alan adında /salon panel yolu sayılır", '"/salon"' in src.split("_PANEL_PATHS")[1][:80])
    t("JavaScript hatası yok", not errs)
    if errs: print(errs[:3])
print("OK", ok, "FAIL", bad)
