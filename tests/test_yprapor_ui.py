"""Rapor ekranı tarayıcıda: liste, tablo, grafik, tarih aralığı, yorum satırı, CSV."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn
from starlette.testclient import TestClient
from playwright.sync_api import sync_playwright

s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:]))

with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "E-ticaret"}).json()
    EMAIL, PW = j["email"], j["password"]
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
    c.post("/api/yp/sectors/eticaret", headers=H, json={})
    pid = c.post("/api/yp/products", headers=H, json={"name": "Keten Gömlek", "price": 900,
                                                      "cost": 400, "stock": 30}).json()["id"]
    for n2 in range(4):
        c.post("/api/yp/orders", headers=H, json={
            "channel": "trendyol" if n2 % 2 else "site",
            "customer": {"name": "Müşteri %d" % n2, "phone": "053200000%02d" % n2},
            "items": [{"product": pid, "name": "Keten Gömlek", "price": 900, "qty": 2, "cost": 400}]})

port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try:
        sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1440, "height": 950})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:%d/salon" % PORT); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", EMAIL); pg.fill("#lf input[name=password]", PW)
    pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(500)

    def a():
        pg.click("a[data-r=rapor]"); pg.wait_for_selector(".rpl .ri", timeout=8000)
        tx = pg.inner_text(".rpl")
        assert "Günlük ciro" in tx and "Satış kanalları" in tx and "Stok durumu" in tx, tx[:200]
        assert "Doluluk" not in tx, "e-ticarette randevu raporu listelenmemeli"
        assert pg.eval_on_selector_all(".rpl .ri", "a=>a.length") >= 4, "rapor sekmeleri"
    t("rapor listesi pakete göre kuruluyor", a)

    def b():
        pg.wait_for_selector("#rapgov table", timeout=8000)
        assert "Günlük ciro" in pg.inner_text(".rpl .ri.on")
        tx = pg.inner_text("#rapgov")
        assert "7.200" in tx, "4 sipariş × 1800 = 7.200: %s" % tx[:200]
        assert pg.is_visible(".gr2b"), "grafik çizilmeli"
        assert pg.eval_on_selector_all(".gr2b .bar", "a=>a.length") >= 1
        yuk = pg.eval_on_selector_all(".gr2b .bar", "a=>a.map(x=>x.getBoundingClientRect().height)")
        assert max(yuk) > 60, "en yüksek çubuk grafiği doldurmalı, çizgiye inmemeli: %s" % yuk
    t("ilk rapor tablo ve grafikle geliyor", b)

    def d():
        pg.click('[data-a=rap-sec][data-v=kanal]'); pg.wait_for_timeout(1200)
        tx = pg.inner_text("#rapgov")
        assert "Trendyol" in tx and "Kendi sitem" in tx, tx[:200]
        assert "KOMİSYON" in tx and "KÂR ORANI" in tx, "sütun başlıkları büyük harf çıkar"
        assert "Komisyon düşülmüş kâra bakın" in pg.inner_text(".yorum"), "yorum satırı görünmeli"
        yuk = pg.eval_on_selector_all(".gr2b .bar", "a=>a.map(x=>x.getBoundingClientRect().height)")
        assert max(yuk) > 60, "kanal grafiği ciroyu çizmeli: %s" % yuk
    t("rapor değişince tablo, sütunlar ve yorum satırı değişiyor", d)

    def e():
        pg.select_option("#rapk", "7"); pg.wait_for_timeout(1100)
        assert "Trendyol" in pg.inner_text("#rapgov")
        pg.select_option("#rapk", "ozel"); pg.wait_for_timeout(300)
        pg.fill("#rapa", "2020-01-01"); pg.wait_for_timeout(1100)
        pg.fill("#rapb", "2020-01-31"); pg.wait_for_timeout(1200)
        assert pg.is_visible(".bosluk"), "veri yoksa boş ekran"
        assert "Tarih aralığını genişletin" in pg.inner_text(".bosluk")
    t("tarih aralığı uygulanıyor, boş aralıkta yol gösteriliyor", e)

    def f():
        pg.select_option("#rapk", "30"); pg.wait_for_timeout(1200)
        with pg.context.expect_page() as pop:
            pg.click("[data-a=rap-yazdir]")
        p2 = pop.value; p2.wait_for_load_state("domcontentloaded"); p2.wait_for_timeout(500)
        body = p2.inner_text("body")
        assert "Satış kanalları" in body and "Trendyol" in body, body[:200]
        p2.close()
    t("rapor yazdırmaya hazır açılıyor", f)

    def g():
        real = [e for e in errs if "favicon" not in e]
        assert not real, real[:2]
    t("rapor ekranında JavaScript hatası yok", g)
    br.close()
srv.should_exit = True
for x in ok: print("  ✓", x)
for x, e in bad: print("  ✗", x, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
