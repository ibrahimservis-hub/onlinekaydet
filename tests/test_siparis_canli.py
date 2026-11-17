"""Yeni panel: Siparişler ekranı açıkken yeni sipariş kendiliğinden listeye düşer."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests
import shop_sync
from playwright.sync_api import sync_playwright
s = boot.server; ok, bad = [], []
GON = []
async def fake(m, u, h, b):
    GON.append((m, u, b))
    if u.endswith('/stores?page=0&size=50'): return 200, {'restaurants': [{'id': 7, 'name': 'Şube'}]}
    if u.endswith('/stores/7/products'): return 200, {'products': [{'id': 1, 'name': 'Adana Kebap', 'sellingPrice': 250, 'status': 'ACTIVE'}]}
    if u.endswith('/products/price'): return 200, {'batchRequestId': 'b9'}
    if '/batch-requests/' in u: return 200, {'status': 'COMPLETED', 'itemCount': 1, 'failedItemCount': 0, 'items': []}
    return 200, {}
shop_sync.HTTP['fn'] = fake
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
d = requests.post(U + "/api/public/demo", json={"name": "Mehmet", "phone": "05321110066", "sector": "lokanta"}).json()
O = {"Authorization": "Bearer " + requests.post(U + "/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1366, "height": 900}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(U + "/salon"); pg.wait_for_selector("#lf"); pg.fill("#lf input[name=email]", d["email"]); pg.fill("#lf input[name=password]", d["password"]); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])")
    pg.evaluate("location.hash='#siparis'"); pg.wait_for_selector("#slist table, #slist .row, #slist", timeout=8000); pg.wait_for_timeout(1500)
    def canli():
        r = requests.post(U + "/api/yp/orders", headers=O, json={"customer": {"name": "Canli Test Musteri", "phone": "05330009988", "address": "Kizilay"}, "items": [{"name": "Kofte", "qty": 1, "price": 100}], "channel": "telefon"})
        assert r.status_code in (200, 201), r.text
        pg.wait_for_function("document.querySelector('#slist') && document.querySelector('#slist').innerText.indexOf('Canli Test Musteri')>-1", timeout=45000)
    t("yeni sipariş sayfa yenilenmeden listeye düşer", canli)
    t("JS hatası yok", lambda: (_ for _ in ()).throw(AssertionError(errs)) if errs else None)
    br.close()
print("OK", len(ok), "FAIL", len(bad))
for n, e in bad: print(n, e)
