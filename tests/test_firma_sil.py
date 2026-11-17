"""Yönetim paneli: firma listesinde alan adı, toplu/tekli silme; destek girişi askıdaki firmada da açılır."""
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
        import traceback; bad.append((n, traceback.format_exc()[-900:])); print("  -", n, bad[-1][1][-300:])
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try: socket.create_connection(("127.0.0.1", PORT), 0.3).close(); break
    except OSError: time.sleep(0.2)
U = "http://127.0.0.1:%d" % PORT
A = {"Authorization": "Bearer " + requests.post(U + "/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
def mk(n):
    r = requests.post(U + "/api/admin/firms", headers=A, json={"name": "Silinecek %s" % n, "email": "sil%s@x.com" % n, "password": "Parola12345", "phone": "05320000%03d" % n, "sector": "kombi", "package": "kurumsal", "usage_days": 30})
    assert r.status_code in (200, 201), r.text; return r.json()
f1, f2, f3 = mk(1), mk(2), mk(3)
fid = lambda f: (f.get("firm") or f).get("id")
def ids(): return {x["id"] for x in requests.get(U + "/api/admin/firms", headers=A).json()["firms"]}
def list_domains():
    r = requests.get(U + "/api/admin/firms", headers=A).json()["firms"]; assert all("domains" in x for x in r)
t("firma listesi alan adı bilgisini taşır", list_domains)
def kurumsal_hepsi():
    import firms
    r = requests.get(U + "/api/admin/packages", headers=A).json()["packages"]["kurumsal"]["modules"]
    assert set(firms.ALL_MODS) <= set(r) and "eticaret" in r, r
t("Kurumsal paket e-ticaret dahil tüm modülleri içerir", kurumsal_hepsi)
def destek_askida():
    requests.put(U + "/api/admin/firms/%s" % fid(f1), headers=A, json={"status": "askida"})
    r = requests.post(U + "/api/admin/firms/%s/support-link" % fid(f1), headers=A, json={"to": "salon"}).json()
    e = requests.get(U + r["url"], allow_redirects=False); assert e.status_code == 200, e.status_code
    tk = e.cookies.get("access_token"); assert tk
    c = requests.get(U + "/api/firm/package", headers={"Authorization": "Bearer " + tk}); assert c.status_code == 200, (c.status_code, c.text[:200])
t("askıdaki firmaya sahip destek girişi açılır", destek_askida)
def tekli():
    r = requests.post(U + "/api/admin/firms/sil", headers=A, json={"ids": [fid(f1)]}); assert r.json()["silinen"] == 1
    assert fid(f1) not in ids()
t("tek firma silinir", tekli)
def toplu():
    r = requests.post(U + "/api/admin/firms/sil", headers=A, json={"ids": [fid(f2), fid(f3)], "kalici": True}); assert r.json()["silinen"] == 2
    assert not ({fid(f2), fid(f3)} & ids())
t("toplu kalıcı silme", toplu)
f4, f5 = mk(4), mk(5)
def ui():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); pg = br.new_page(viewport={"width": 1440, "height": 900}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("dialog", lambda d: d.accept("SİL") if d.type == "prompt" else d.accept())
        pg.goto(U + "/yonetim"); pg.wait_for_selector("#le"); pg.fill("#le", "admin@servis.com"); pg.fill("#lp", "admin123"); pg.click("button[type=submit]"); pg.wait_for_selector(".tbar")
        pg.evaluate("location.hash='#firmalar'"); pg.wait_for_selector(".fsk"); assert "Alan adı" in pg.inner_text("table")
        pg.locator('.fsk[data-id="%s"]' % fid(f4)).check(); pg.locator('.fsk[data-id="%s"]' % fid(f5)).check()
        assert "2 firma seçili" in pg.inner_text("#fsbar")
        pg.click("#fsbar button:has-text('Seçilenleri sil')"); pg.wait_for_timeout(1200)
        assert not ({fid(f4), fid(f5)} & ids()); assert not errs, errs; br.close()
t("yönetim ekranından toplu seçip silinir", ui)
print("OK", len(ok), "FAIL", len(bad))
