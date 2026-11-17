"""XML aktarım ekranı (yerel demo sunucu, sahte XML)."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import xml_ice as xi, uvicorn, requests as rq
FEED = """<?xml version="1.0" encoding="UTF-8"?><Products>
<Product><ProductCode>A-1</ProductCode><Barcode>8690001</Barcode><ProductName>Kombi Eşanjör</ProductName><Price>1.234,50</Price><Stock>7</Stock><Category>Yedek Parça</Category><Brand>Baymak</Brand><Image1>https://x.test/1.jpg</Image1></Product>
<Product><ProductCode>A-2</ProductCode><ProductName>Fan Motoru</ProductName><Price>310</Price><Stock>0</Stock><Category>Yedek Parça</Category></Product></Products>"""
xi.fetch_bytes = lambda url, timeout=40: FEED.encode("utf-8"); xi.assert_public_url = lambda u: None
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8767, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8767/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
B = "http://127.0.0.1:8767/api"
T = rq.post(B + "/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]
r = rq.post(B + "/admin/firms", json={"name": "Xml UI", "email": "xu@x.com", "password": "sifre12345", "package": "tam", "sector": "eticaret"}, headers={"Authorization": "Bearer " + T}); assert r.status_code == 200, r.text
O = {"Authorization": "Bearer " + rq.post(B + "/auth/login", json={"email": "xu@x.com", "password": "sifre12345"}).json()["token"]}
rq.put(B + "/site/features", json={"shop_enabled": True}, headers=O)
from playwright.sync_api import sync_playwright
bad = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1360, "height": 900}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
    pg.goto("http://127.0.0.1:8767/salon"); pg.wait_for_timeout(1000)
    pg.fill("input[name=email]", "xu@x.com"); pg.fill("input[name=password]", "sifre12345"); pg.click("form button"); pg.wait_for_timeout(2500)
    pg.evaluate("location.hash='#xml'"); pg.wait_for_timeout(1500)
    try:
        assert "XML ile ürün aktarma" in pg.inner_text("#main")
        pg.fill("#xm-ad", "Tedarikçi A"); pg.fill("#xm-url", "https://x.test/f.xml"); pg.click("[data-a=xml-an]"); pg.wait_for_selector("[data-xf=name]", timeout=8000)
        assert pg.eval_on_selector("[data-xf=name]", "e=>e.value") == "ProductName" and pg.eval_on_selector("[data-xf=price]", "e=>e.value") == "Price"
        pg.fill("#xm-mp", "20"); pg.fill("#xm-rt", "5"); pg.locator("#main").screenshot(path="/tmp/xml_ui1.png")
        pg.click("[data-a=xml-save]"); pg.wait_for_selector("[data-a=xml-run]", timeout=10000); pg.wait_for_timeout(500)
        txt = pg.inner_text("#main"); assert "Tedarikçi A" in txt and "2 ürün" in txt and "2</b> eklendi" in pg.inner_html("#main") or "2 eklendi" in txt or "eklendi" in txt, txt[:400]
        pg.locator("#main").screenshot(path="/tmp/xml_ui2.png")
        ps = rq.get(B + "/shop/products", headers=O).json(); assert len(ps) == 2 and {p["sku"] for p in ps} == {"A-1", "A-2"}, ps
        assert [p for p in ps if p["sku"] == "A-1"][0]["price"] == 1485.0
        pg.select_option("[data-a=xml-auto]", "12"); pg.wait_for_timeout(600)
        assert rq.get(B + "/yp/xml", headers=O).json()["sources"][0]["auto_hours"] == 12
        assert not errs, errs
    except Exception as e:
        import traceback; bad.append(traceback.format_exc()[-700:]); pg.screenshot(path="/tmp/xml_ui_err.png")
    br.close()
print("GEÇTİ 1" if not bad else "BAŞARISIZ\n" + bad[0]); os._exit(1 if bad else 0)
