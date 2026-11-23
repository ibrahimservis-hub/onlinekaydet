"""Destek rehberleri için güncel panel ekran görüntüleri: demo e-ticaret ve kuaför firması, /tmp/ss/*.png"""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server
os.makedirs("/tmp/ss", exist_ok=True)
with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    def firma(ad, em, sec):
        r = c.post("/api/admin/firms", headers=A, json={"name": ad, "email": em, "password": "sifre12345", "package": "kurumsal"}); assert r.status_code == 200, r.text
        H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": em, "password": "sifre12345"}).json()["token"]}
        c.post("/api/yp/sectors/" + sec, headers=H, json={}); return H
    He = firma("Mavi Butik", "e@x.com", "eticaret")
    ids = []
    pid = []
    for n, pr, cs in (("Keten Gömlek", 890, 420), ("Kot Pantolon", 1190, 560), ("Deri Cüzdan", 650, 280)):
        r = c.post("/api/yp/products", headers=He, json={"name": n, "price": pr, "cost": cs, "stock": 25, "cat": "Giyim", "active": True}); pid.append(r.json()["id"])
    for k, (nm, ph) in enumerate((("Ayşe Demir", "0532 111 22 33"), ("Mehmet Kaya", "0533 222 33 44"), ("Elif Şahin", "0534 333 44 55"))):
        r = c.post("/api/yp/orders", headers=He, json={"channel": "site", "payment": "kart", "customer": {"name": nm, "phone": ph, "city": "İstanbul", "address": "Kadıköy"},
                   "items": [{"product": pid[k], "name": "Ürün", "price": 890, "qty": 1, "cost": 420}]})
        ids.append(r.json().get("item", r.json())["id"])
    for oid in ids[:2]:
        for st in ("onaylandi", "hazirlaniyor"):
            c.post("/api/yp/orders/%s/status" % oid, headers=He, json={"status": st})
    c.post("/api/yp/orders/fatura", headers=He, json={"ids": ids[:2]})
    import uvicorn
    from playwright.sync_api import sync_playwright
    port = socket.socket(); port.bind(("127.0.0.1", 0)); P = port.getsockname()[1]; port.close()
    srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=P, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start(); time.sleep(2)
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = br.new_page(viewport={"width": 1280, "height": 800})
        pg.goto("http://127.0.0.1:%d/salon" % P); pg.wait_for_selector("#lf")
        pg.fill("#lf input[name=email]", "e@x.com"); pg.fill("#lf input[name=password]", "sifre12345"); pg.click("#lb")
        pg.wait_for_selector("#app:not([hidden])"); pg.wait_for_timeout(1800)
        def shot(name, hash_=None, wait=1500, js=None):
            if hash_: pg.evaluate("location.hash='%s'" % hash_)
            pg.wait_for_timeout(wait)
            if js: pg.evaluate(js); pg.wait_for_timeout(900)
            pg.screenshot(path="/tmp/ss/%s.png" % name); print("ok", name)
        shot("n_genel", "#bugun")
        shot("n_urun", "#urun")
        shot("n_siparis", "#siparis", 1800)
        shot("n_siparis_toplu", None, 400, "document.querySelectorAll('#main input[type=checkbox]').forEach(function(e,i){if(i>0&&i<3)e.click()})")
        shot("n_faturalar", None, 300, "document.querySelector('[data-a=fatura-liste]').click()")
        pg.keyboard.press("Escape")
        shot("n_kasa", "#kasa")
        shot("n_entegrasyon", "#entegrasyon", 2000)
        shot("n_site", "#site", 2500)
        pg.click("[data-a=sitetab][data-t=bilgi]"); pg.wait_for_timeout(800); pg.screenshot(path="/tmp/ss/n_site_bilgi.png"); print("ok n_site_bilgi")
        shot("n_rapor", "#rapor", 2000)
        br.close()
os._exit(0)
