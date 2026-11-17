"""Yeni panel: Etiket tasarımı ekranı — tür sekmeleri, stil seçimi, canlı önizleme, kaydet, yazdır."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests
from playwright.sync_api import sync_playwright
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n); print("  +", n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:])); print("  -", n)
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try: socket.create_connection(("127.0.0.1", PORT), 0.3).close(); break
    except OSError: time.sleep(0.2)
U = "http://127.0.0.1:%d" % PORT
L = lambda e, p: {"Authorization": "Bearer " + requests.post(U + "/api/auth/login", json={"email": e, "password": p}).json()["token"]}
A = L("admin@servis.com", "admin123")
F = requests.post(U + "/api/admin/firms", headers=A, json={"name": "Lezzet Evi", "email": "et@x.com", "password": "sifre12345", "package": "tam", "phone": "03120000000", "address": "Çankaya Ankara"}).json()["id"]
O = L("et@x.com", "sifre12345")
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1366, "height": 900}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(U + "/salon"); pg.wait_for_selector("#lf"); pg.fill("#lf input[name=email]", "et@x.com"); pg.fill("#lf input[name=password]", "sifre12345"); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])")
    def ac():
        pg.evaluate("location.hash='#etiket'"); pg.wait_for_selector("#et .etst", timeout=8000); pg.wait_for_function("document.querySelector('#etpv') && document.querySelector('#etpv').srcdoc.length>500", timeout=8000)
        assert "Lezzet Evi" in pg.inner_text("#et"), pg.inner_text("#et")[:300]
    t("Etiket tasarımı ekranı açılır, firma bilgisi kendiliğinden görünür", ac)
    def onizleme():
        assert pg.eval_on_selector("#etpv", "e=>e.srcdoc.includes('Örnek Alıcı')")
        n = pg.eval_on_selector_all("#et iframe[data-st]", "els=>els.length"); assert n == 5, n
    t("canlı önizleme ve 5 stil küçük resmi", onizleme)
    def stil():
        pg.click("[data-e=stil][data-v=kalin]"); pg.wait_for_timeout(900)
        assert pg.eval_on_selector("#etpv", "e=>e.srcdoc.includes('2.2mm')") or pg.eval_on_selector("#etpv", "e=>e.srcdoc.includes('--r')")
        pg.fill("[data-f=alt]", "Kırılacak eşya değildir"); pg.wait_for_timeout(700)
        assert pg.eval_on_selector("#etpv", "e=>e.srcdoc.includes('Kırılacak eşya değildir')")
    t("stil seçilir, yazı yazınca önizleme güncellenir", stil)
    def kaydet():
        pg.click("[data-e=kaydet]"); pg.wait_for_timeout(800)
        c = requests.get(U + "/api/yp/etiket", headers=O).json()["cfg"]["etiket"]; assert c["stil"] == "kalin" and c["alt"] == "Kırılacak eşya değildir", c
    t("kaydedilir", kaydet)
    def qr():
        pg.click("[data-e=tip][data-v=qr]"); pg.wait_for_selector("#et [data-f=baslik]", timeout=6000)
        pg.wait_for_function("document.querySelector('#etpv').srcdoc.includes('Masa 1')", timeout=6000)
        h = pg.eval_on_selector("#etpv", "e=>e.srcdoc"); assert "<svg" in h and "Lezzet Evi" in h
        pg.screenshot(path="/tmp/et/ui-qr.png")
    t("QR sekmesi: önizlemede firma adı, logo yeri ve QR", qr)
    t("JS hatası yok", lambda: (_ for _ in ()).throw(AssertionError(errs)) if errs else None)
    br.close()
print("OK", len(ok), "FAIL", len(bad))
for n, e in bad: print(n, e)
