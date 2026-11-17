"""/yonetim firma sekmeleri randevulu işte (kuaför) randevu defterini, müşteri/kasa/ekibi gerçek verisiyle gösteriyor mu; servis firması eskisi gibi."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8773, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8773/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8773"; B = U + "/api"
d = rq.post(B + "/public/demo", json={"name": "Salon Sahibi", "phone": "05341112233", "sector": "kuafor"}).json()
H = {"Authorization": "Bearer " + rq.post(B + "/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
bo = rq.get(B + "/yp/boot", headers=H).json(); today = bo["today"]; st = bo["staff"][0]; sv = bo["services"][0]
ap = rq.post(B + "/yp/appts", headers=H, json={"name": "Deniz Aksoy", "phone": "05329998877", "date": today, "time": "17:30", "staff_id": st["id"], "items": [{"name": sv["name"], "price": 700, "dur": 30}], "source": "telefon"}).json()
rq.post(B + "/yp/appts/%s/pay" % ap["id"], headers=H, json={"amount": 700, "method": "Kart"})
rq.post(B + "/yp/cash", headers=H, json={"type": "out", "amount": 120, "method": "Nakit", "desc": "Boya malzemesi"})
d2 = rq.post(B + "/public/demo", json={"name": "Servis Sahibi", "phone": "05342223344", "sector": "kombi"}, headers={"X-Forwarded-For": "7.7.7.7"}).json()
d3 = rq.post(B + "/public/demo", json={"name": "Magaza Sahibi", "phone": "05343334455", "sector": "eticaret"}, headers={"X-Forwarded-For": "8.8.8.8"}).json()
from playwright.sync_api import sync_playwright
bad = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_context(viewport={"width": 1360, "height": 900}).new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(U + "/yonetim"); pg.wait_for_timeout(1200)
    pg.fill("#le", "admin@servis.com"); pg.fill("#lp", "admin123"); pg.click("form button[type=submit]"); pg.wait_for_timeout(2500)
    firms = pg.evaluate("api('/admin/firms').then(d=>d.firms.map(f=>({id:f.id,name:f.name,fam:f.family,stats:f.stats})))")
    fk = [f for f in firms if f["fam"] == "randevu"][0]; fs = [f for f in firms if f["fam"] == "servis"][0]
    if fk["stats"]["done"] != 1 or fk["stats"]["revenue_total"] != 700: bad.append(("firma listesi istatistik", fk["stats"]))
    def tab(fid, t, *need, no=()):
        pg.evaluate("location.hash='#firma/%s/%s'" % (fid, t)); pg.wait_for_timeout(2200)
        x = pg.inner_text("body")
        for n in need:
            if n not in x: bad.append((t, "eksik: " + n, x[-200:].replace("\n", " ")))
        for n in no:
            if n in x: bad.append((t, "olmamalı: " + n))
    tab(fk["id"], "servis", "Deniz Aksoy", "Tamamlandı", sv["name"], st["name"])
    tab(fk["id"], "musteri", "Deniz Aksoy", "05329998877")
    tab(fk["id"], "muh", "Boya malzemesi", "Kart", "Bu ay gelir", no=("Servis Geliri",))
    tab(fk["id"], "pers", "Uzmanlar (randevu ekibi)", st["name"])
    # durum değiştir: randevu ekle -> iptal
    ap2 = rq.post(B + "/yp/appts", headers=H, json={"name": "Taşınacak Kişi", "phone": "05325554433", "date": today, "time": "18:30", "staff_id": st["id"], "items": [{"name": sv["name"], "price": 300, "dur": 30}], "source": "telefon"}).json()
    pg.evaluate("location.hash='#firma/%s/servis'" % fk["id"]); pg.wait_for_timeout(2000)
    row = pg.locator("tr.fr", has_text="Taşınacak Kişi"); row.locator("select").select_option("iptal"); pg.wait_for_timeout(1800)
    if rq.get(B + "/yp/appts/" + ap2["id"], headers=H).json()["stage"] != "iptal": bad.append("yönetimden durum değişmedi")
    # kasa: gider ekle
    pg.evaluate("location.hash='#firma/%s/muh'" % fk["id"]); pg.wait_for_timeout(1800)
    pg.locator("button:has-text('Gider ekle')").click(); pg.fill("#m_amount", "55"); pg.fill("#m_desc", "Temizlik malzemesi"); pg.click("[data-ok]"); pg.wait_for_timeout(1800)
    if "Temizlik malzemesi" not in pg.inner_text("body"): bad.append("kasa gideri eklenmedi")
    # mağaza firması: siparişler sekmesi
    fm = [f for f in firms if f["fam"] == "siparis"][0]
    pg.evaluate("location.hash='#firma/%s/servis'" % fm["id"]); pg.wait_for_timeout(2200)
    xt = pg.inner_text("body")
    if "SP-1001" not in xt or "Siparişler" not in xt: bad.append(("mağaza siparişler sekmesi", xt[-200:].replace("\n", " ")))
    pg.locator("tr.fr", has_text="SP-1001").locator("select").select_option("hazirlaniyor"); pg.wait_for_timeout(1800)
    tk = rq.post(B + "/auth/login", json={"email": d3["email"], "password": d3["password"]}).json()["token"]
    if [o for o in rq.get(B + "/shop/orders", headers={"Authorization": "Bearer " + tk}).json() if o["order_no"] == "SP-1001"][0]["status"] != "hazirlaniyor": bad.append("sipariş durumu değişmedi")
    # servis firması: eski sekmeler
    tab(fs["id"], "servis", "Servis kaydı") if False else None
    pg.evaluate("location.hash='#firma/%s/servis'" % fs["id"]); pg.wait_for_timeout(2200)
    if "DM-1001" not in pg.inner_text("body"): bad.append(("servis firmasında servis sekmesi bozuldu", fs, pg.inner_text("body")[-300:].replace("\n", " ")))
    pg.evaluate("location.hash='#firma/%s/muh'" % fs["id"]); pg.wait_for_timeout(2200)
    if "Servis Geliri" not in pg.inner_text("body"): bad.append("servis firması muhasebe sekmesi bozuldu")
    if errs: bad.append(errs[:3])
    pg.screenshot(path="/tmp/sahip_randevu.png"); br.close()
print("GEÇTİ" if not bad else "BAŞARISIZ %s" % bad); os._exit(1 if bad else 0)
