"""Çek-senet, müşavir, depo/sayım, hızlı satış, ihracat, API, geri bildirim ekranları (tarayıcı)."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import xml_ice, uvicorn, requests as rq
xml_ice.fetch_bytes = lambda url, timeout=40: b'<Tarih_Date Tarih="17.11.2026"><Currency Kod="USD"><Unit>1</Unit><ForexBuying>40.5</ForexBuying><ForexSelling>40.6</ForexSelling></Currency></Tarih_Date>'
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8768, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8768/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
B = "http://127.0.0.1:8768/api"
T = rq.post(B + "/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]
r = rq.post(B + "/admin/firms", json={"name": "Ek UI", "email": "eu@x.com", "password": "sifre12345", "package": "tam", "sector": "eticaret"}, headers={"Authorization": "Bearer " + T}); assert r.status_code == 200, r.text
O = {"Authorization": "Bearer " + rq.post(B + "/auth/login", json={"email": "eu@x.com", "password": "sifre12345"}).json()["token"]}
rq.put(B + "/site/features", json={"shop_enabled": True}, headers=O)
p = rq.post(B + "/yp/products", json={"name": "Süt 1L", "price": 30, "stock": 10, "barcode": "869111", "sku": "SUT1", "cat": "Gıda"}, headers=O); assert p.status_code == 200, p.text
from playwright.sync_api import sync_playwright
bad = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1360, "height": 900}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto("http://127.0.0.1:8768/salon"); pg.wait_for_timeout(1000)
    pg.fill("input[name=email]", "eu@x.com"); pg.fill("input[name=password]", "sifre12345"); pg.click("form button"); pg.wait_for_timeout(2500)
    def go(h, txt):
        pg.evaluate("location.hash='#%s'" % h); pg.wait_for_timeout(1200)
        assert txt in pg.inner_text("#main"), (h, pg.inner_text("#main")[:300])
    try:
        go("cek", "Çek, senet ve banka")
        pg.fill("#cs-p", "ABC Ltd"); pg.fill("#cs-a", "1500,50"); pg.fill("#cs-v", "2026-12-01"); pg.click("[data-a=ek-cs-add]"); pg.wait_for_timeout(1200)
        assert "ABC Ltd" in pg.inner_text("#main")
        pg.click("[data-a=ek-cs-ok]"); pg.wait_for_timeout(500); pg.click("[data-a=ek-cs-onay]"); pg.wait_for_timeout(1500)
        assert "Tahsil edildi" in pg.inner_text("#main"), pg.inner_text("#main")[:400]
        pg.click("[data-a=ek-kur-cevir]"); pg.wait_for_timeout(800); assert "4.060" in pg.inner_text("#kr-s") or "4060" in pg.inner_text("#kr-s"), pg.inner_text("#kr-s")
        pg.locator("#main").screenshot(path="/tmp/ek_cek.png")
        go("musavir", "Mali müşavir erişimi"); pg.fill("#ms-ad", "Ali Bey"); pg.click("[data-a=ek-mus-yeni]"); pg.wait_for_timeout(1000); assert "/api/public/musavir/" in pg.inner_text("#ms-sonuc")
        go("stokek", "Depo, lot ve sayım"); pg.fill("#dp-ad", "Ana depo"); pg.click("[data-a=ek-depo-ekle]"); pg.wait_for_timeout(1000)
        pg.fill("#lt-b", "869111"); pg.fill("#lt-q", "5"); pg.fill("#lt-s", "2026-11-25"); pg.fill("#lt-l", "L1"); pg.click("[data-a=ek-lot-ekle]"); pg.wait_for_timeout(1200)
        assert "L1" in pg.inner_text("#main")
        pg.fill("#sy-t", "869111;12"); pg.click("[data-a=ek-sayim-on]"); pg.wait_for_timeout(900); assert "Süt 1L" in pg.inner_text("#sy-s")
        pg.fill("#tf-d", "10"); pg.click("[data-a=ek-tf-on]"); pg.wait_for_timeout(900); assert "ürün değişecek" in pg.inner_text("#tf-s"), pg.inner_text("#tf-s")
        pg.locator("#main").screenshot(path="/tmp/ek_stok.png")
        go("hizli", "Hızlı satış"); pg.fill("#hz-k", "869111"); pg.press("#hz-k", "Enter"); pg.wait_for_timeout(1200)
        assert "Süt 1L" in pg.inner_text("#main"); pg.click("[data-a=ek-hz-sat]"); pg.wait_for_timeout(1500)
        assert "HS-" in pg.inner_text("#main"), pg.inner_text("#main")[:500]
        pg.locator("#main").screenshot(path="/tmp/ek_hizli.png")
        go("ihracat", "E-ihracat"); pg.check("#ih-ak"); pg.click("[data-a=ek-ih-kaydet]"); pg.wait_for_timeout(800)
        go("apiek", "API anahtarları"); pg.fill("#ap-ad", "Deneme"); pg.click("[data-a=ek-api-yeni]"); pg.wait_for_timeout(900); assert "ok_" in pg.inner_text("#ap-s")
        kk = pg.inner_text("#ap-s").split("\n")[1].strip(); kt = rq.get(B + "/yp/api-anahtar", headers=O).json()["taban"]
        rr = rq.get(B.replace("/api", "") + kt + "/urunler", headers={"X-API-Key": kk}); assert rr.status_code == 200 and rr.json()["toplam"] == 1, rr.text
        assert "/api/public/" in pg.inner_text("#main")
        rq.post(B.replace("/api","") + rq.get(B + "/yp/api-anahtar", headers=O).json()["form"], json={"tur": "sikayet", "mesaj": "Servis geç geldi, bilgi verilmedi."})
        go("gbildirim", "Şikayet ve öneriler"); assert "Servis geç geldi" in pg.inner_text("#main")
        assert not errs, errs
    except Exception as e:
        import traceback; bad.append(traceback.format_exc()[-800:]); pg.screenshot(path="/tmp/ek_ui_err.png")
    br.close()
print("GEÇTİ" if not bad else "BAŞARISIZ\n" + bad[0]); os._exit(1 if bad else 0)
