"""Tarayıcıda mağaza ürün karşılaştırma: kartta Karşılaştır, alt çubuk, yan yana tablo, farklar."""
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
    except Exception as e: bad.append((n, repr(e)[:500]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Karşılaştırma Firma", "email": "cmp@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "cmp@x.com", "sifre12345")
    async def setup():
        f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
        await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": "p01-cine-kombi"}}, upsert=True)
        await s.db.main().firm_domains.insert_one({"id": "dc1", "domain": "cmp-test.com", "firm_id": F, "db": f["db"], "status": "yayinda"})
    c.portal.call(setup)
    import domains; domains._cache["t"] = 0
    H = {"Host": "cmp-test.com"}
    def get(p): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers=H)
    c.put("/api/site/features", headers=O, json={"shop_enabled": True})
    for n, pr, sp in (("Kombi pompası A", 1200, [{"k": "Güç", "v": "90 W"}, {"k": "Garanti", "v": "2 yıl"}]),
                      ("Kombi pompası B", 950, [{"k": "Güç", "v": "70 W"}, {"k": "Garanti", "v": "2 yıl"}]),
                      ("Kombi pompası C", 1500, [{"k": "Güç", "v": "120 W"}])):
        r = c.post("/api/shop/products", headers=O, json={"name": n, "price": pr, "stock": 5, "category": "Yedek parça", "brand": "Wilo", "specs": sp})
        assert r.status_code == 200, r.text
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try:
        sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--host-resolver-rules=MAP cmp-test.com 127.0.0.1"])
    for vw in ({"width": 1366, "height": 900}, {"width": 390, "height": 844}):
        pg = br.new_page(viewport=vw); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("response", lambda r: errs.append("RESP %s %s" % (r.status, r.url)) if r.status>=400 or ("javascript" not in (r.headers.get("content-type") or "") and r.request.resource_type=="script") else None)
        B = "http://cmp-test.com:%d" % PORT
        import urllib.parse as _up
        def _doc(route):
            rq = route.request; u = _up.urlparse(rq.url)
            if rq.resource_type == "document" and not u.path.startswith("/api"):
                r = c.get("/api/public/hosted-site?p=" + _up.quote(u.path, safe=""), headers=H)
                return route.fulfill(status=r.status_code, body=r.content, headers={"content-type": "text/html; charset=utf-8"})
            hd = {k: v for k, v in rq.headers.items() if k.lower() in ("authorization", "content-type")}; hd.update(H)
            r = c.request(rq.method, u.path + ("?" + u.query if u.query else ""), headers=hd, content=rq.post_data_buffer)
            return route.fulfill(status=r.status_code, body=r.content, headers={"content-type": r.headers.get("content-type", "application/octet-stream")})
        pg.route("http://cmp-test.com:%d/**" % PORT, _doc)
        def a():
            pg.goto(B + "/magaza"); pg.wait_for_selector("[data-cm]", timeout=15000)
            cm = pg.locator("[data-cm]")
            assert cm.count() == 3, cm.count()
            cm.nth(0).click(); assert pg.locator("#okm-cmb").is_visible()
            assert pg.locator("#okm-cmg").is_disabled(), "tek ürünle karşılaştır kapalı"
            cm.nth(1).click(); cm.nth(2).click()
            assert "3 ürün" in pg.locator("#okm-cmb").inner_text()
            pg.click("#okm-cmg"); pg.wait_for_selector(".cmt table", timeout=8000)
            tx = pg.locator(".cmt").inner_text()
            assert "Güç" in tx and "120 W" in tx and "Garanti" in tx and "En uygun fiyat" in tx, tx
            assert not pg.locator("#okm-cmb").is_visible(), "karşılaştırma sayfasında çubuk gizli"
            pg.check("#okm-cmd"); tx2 = pg.locator(".cmt tbody").inner_text()
            assert "Marka" not in tx2 and "Güç" in tx2, "yalnız farklar: aynı marka satırı gizlenir"
            pg.locator("[data-cmr]").first.click(); pg.wait_for_timeout(200)
            assert pg.locator(".cmt thead td").count() == 2
            pg.screenshot(path="/tmp/cmp_%d.png" % vw["width"], full_page=False)
            pg.reload(); pg.wait_for_selector(".cmt table", timeout=8000)
            assert pg.locator(".cmt thead td").count() == 2, "seçim kalıcı (yenileyince)"
            assert pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), ("yatay taşma yok", pg.evaluate("[].slice.call(document.querySelectorAll('body *')).filter(function(e){var r=e.getBoundingClientRect();return r.right>innerWidth+1&&!e.closest('.cmt table')}).slice(0,6).map(function(e){return e.tagName+'.'+e.className+' '+Math.round(e.getBoundingClientRect().right)})"))
            pg.evaluate("localStorage.removeItem('okcmp-live')")
        t("karşılaştırma akışı %dpx" % vw["width"], a)
        def b():
            pg.goto(B + "/magaza"); pg.wait_for_selector("[data-cm]", timeout=15000)
            href = pg.locator(".pc h3 a").first.get_attribute("href")
            pg.goto(B + href); pg.wait_for_selector("#okm-cmp", timeout=15000)
            pg.click("#okm-cmp"); assert "Karşılaştırmada" in pg.locator("#okm-cmp").inner_text()
            assert pg.locator("#okm-cmb").is_visible()
        t("ürün sayfasında karşılaştır düğmesi %dpx" % vw["width"], b)
        assert not [e for e in errs if "/tema-urun/" not in e], errs
        pg.close()
    br.close()
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" FAIL", n, e)
sys.exit(1 if bad else 0)
