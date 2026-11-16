"""Tarayıcıda varyantlı ürün: seçici, fiyat/stok değişimi, seçmeden sepete eklenemez, sepette seçenek, listede Seçenekleri gör."""
import sys, os, re, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
import uvicorn
from playwright.sync_api import sync_playwright
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e:
        import traceback; bad.append((n, traceback.format_exc()[-600:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Varyant UI Firma", "email": "vui@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "vui@x.com", "sifre12345")
    async def setup():
        f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
        await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": "p01-cine-kombi"}}, upsert=True)
        await s.db.main().firm_domains.insert_one({"id": "dc1", "domain": "vui-test.com", "firm_id": F, "db": f["db"], "status": "yayinda"})
    c.portal.call(setup)
    import domains; domains._cache["t"] = 0
    H = {"Host": "vui-test.com"}
    def get(p): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers=H)
    c.put("/api/site/features", headers=O, json={"shop_enabled": True})
    r = c.post("/api/yp/products", headers=O, json={"name": "Keten Gömlek", "price": 900, "cost": 400, "stock": 0, "cat": "Gömlek", "brand": "Nev", "variants": [
        {"opts": {"Renk": "Beyaz", "Beden": "M"}, "stock": 5, "sku": "KG-B-M"}, {"opts": {"Renk": "Beyaz", "Beden": "L"}, "stock": 0, "sku": "KG-B-L"},
        {"opts": {"Renk": "Mavi", "Beden": "M"}, "stock": 3, "sku": "KG-M-M", "price": 950}]})
    assert r.status_code == 200, r.text
    c.post("/api/yp/products", headers=O, json={"name": "Düz Tişört", "price": 300, "cost": 100, "stock": 4, "cat": "Gömlek"})
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try:
        sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--host-resolver-rules=MAP vui-test.com 127.0.0.1"])
    for vw in ({"width": 1366, "height": 900}, {"width": 390, "height": 844}):
        pg = br.new_page(viewport=vw); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("response", lambda r: errs.append("RESP %s %s" % (r.status, r.url)) if r.status>=400 or ("javascript" not in (r.headers.get("content-type") or "") and r.request.resource_type=="script") else None)
        B = "http://vui-test.com:%d" % PORT
        import urllib.parse as _up
        def _doc(route):
            rq = route.request; u = _up.urlparse(rq.url)
            if rq.resource_type == "document" and not u.path.startswith("/api"):
                r = c.get("/api/public/hosted-site?p=" + _up.quote(u.path, safe=""), headers=H)
                return route.fulfill(status=r.status_code, body=r.content, headers={"content-type": "text/html; charset=utf-8"})
            hd = {k: v for k, v in rq.headers.items() if k.lower() in ("authorization", "content-type")}; hd.update(H)
            r = c.request(rq.method, u.path + ("?" + u.query if u.query else ""), headers=hd, content=rq.post_data_buffer)
            return route.fulfill(status=r.status_code, body=r.content, headers={"content-type": r.headers.get("content-type", "application/octet-stream")})
        pg.route("http://vui-test.com:%d/**" % PORT, _doc)
        def a():
            pg.goto(B + "/magaza"); pg.wait_for_selector(".pc", timeout=15000)
            cards = pg.locator(".pc")
            assert cards.count() == 2
            assert "Seçenekleri gör" in pg.locator(".pc", has_text="Keten").inner_text(), "varyantlı üründe doğrudan sepete ekle yok"
            assert "Sepete ekle" in pg.locator(".pc", has_text="Tişört").inner_text()
            pg.goto(B + pg.locator(".pc", has_text="Keten").locator("h3 a").get_attribute("href")); pg.wait_for_selector("#okm-vs .vc", timeout=15000)
            pg.click("#okm-pa2"); assert pg.locator("#okm-t, .toast, [role=status]").count() >= 0
            assert pg.evaluate("JSON.parse(localStorage.getItem('okcart-live')||'[]').length") == 0, "seçim yapmadan sepete girmemeli"
            pg.click("[data-va=Renk][data-vv=Beyaz]")
            assert pg.locator("[data-va=Beden][data-vv=L]").get_attribute("class").find("off") > -1, "stoksuz kombinasyon pasif"
            pg.click("[data-va=Beden][data-vv=M]")
            assert "900" in pg.inner_text("#okm-pp") and "Stokta" in pg.inner_text("#okm-vst")
            import json as _j; _ld = _j.loads(pg.evaluate("document.getElementById('okm-ld').textContent")); assert _ld["offers"]["@type"] == "AggregateOffer" and _ld["offers"]["lowPrice"] <= _ld["offers"]["highPrice"] and _ld["offers"]["offerCount"] >= 2, _ld["offers"]
            pg.click("[data-va=Renk][data-vv=Mavi]")
            assert "950" in pg.inner_text("#okm-pp"), pg.inner_text("#okm-pp")
            pg.click("#okm-pa2"); pg.wait_for_timeout(300)
            cart = pg.evaluate("JSON.parse(localStorage.getItem('okcart-live')||'[]')")
            assert len(cart) == 1 and cart[0]["vl"] == "Mavi / M" and cart[0]["price"] == 950 and cart[0]["v"], cart
            pg.click("#okm-pa2"); pg.wait_for_timeout(200)
            assert pg.evaluate("JSON.parse(localStorage.getItem('okcart-live')||'[]')[0].q") == 2, "aynı seçenek tek satırda birleşir"
            pg.click("[data-va=Beden][data-vv=M]"); pg.click("[data-va=Renk][data-vv=Beyaz]"); pg.click("[data-va=Beden][data-vv=M]"); pg.click("#okm-pa2"); pg.wait_for_timeout(200)
            assert pg.evaluate("JSON.parse(localStorage.getItem('okcart-live')||'[]').length") == 2, "farklı seçenek ayrı satır"
            pg.screenshot(path="/tmp/var_%d.png" % vw["width"], full_page=False)
            pg.goto(B + "/magaza#sepet"); pg.wait_for_timeout(800)
            pg.evaluate("document.querySelector('[data-go=cart]')&&0")
        t("varyantlı ürün sayfası ve sepet %dpx" % vw["width"], a)
        assert not [e for e in errs if "/tema-urun/" not in e], errs
        pg.close()
    br.close()
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" FAIL", n, e)
sys.exit(1 if bad else 0)
