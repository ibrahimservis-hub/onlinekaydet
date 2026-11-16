"""Vitrinde bayi: başvuru formu, onay sonrası bayi fiyatı ve şerit, cari ödeme ile sipariş (tarayıcı)."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn
from starlette.testclient import TestClient
from playwright.sync_api import sync_playwright
s = boot.server; ok, bad, S = [], [], {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-1200:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
c = TestClient(s.app); c.__enter__()
A = tok(c, "admin@servis.com", "admin123")
r = c.post("/api/admin/firms", headers=A, json={"name": "Bayi Vitrin", "email": "bv@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
F = r.json()["id"]; O = tok(c, "bv@x.com", "sifre12345")
async def _setup():
    f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
    await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": "p01-cine-kombi"}}, upsert=True)
    await s.db.main().firm_domains.insert_one({"id": "dbv1", "domain": "bv-test.com", "firm_id": F, "db": f["db"], "status": "yayinda"})
c.portal.call(_setup)
import domains; domains._cache["t"] = 0
c.put("/api/site/features", headers=O, json={"shop_enabled": True, "customer_portal_enabled": True})
c.put("/api/shop/settings", headers=O, json={"shipping_fee": 0, "bank_accounts": [{"bank": "Ziraat", "holder": "M", "iban": "TR330006100519786457841326"}]})
PID = c.post("/api/yp/products", headers=O, json={"name": "Tabak Seti", "price": 1000, "cost": 500, "sku": "TB", "stock": 50, "category": "Mutfak"}).json()["id"]
rr = c.post("/api/public/customer/%s~register" % F, json={"name": "Ali Bayi", "phone": "0532 555 11 22", "password": "parola1234"}); TOKEN = rr.json()["token"]
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try: sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)
URL = "http://bv-test.com:%d/magaza" % PORT
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--host-resolver-rules=MAP bv-test.com 127.0.0.1"])
    ctx = br.new_context(viewport={"width": 1280, "height": 900}); ctx.add_init_script("localStorage.setItem('okc_token','%s')" % TOKEN)
    import urllib.parse as _up
    H = {"Host": "bv-test.com"}
    def _doc(route):
        rq = route.request; u = _up.urlparse(rq.url)
        if rq.resource_type == "document" and not u.path.startswith("/api"):
            r = c.get("/api/public/hosted-site?p=" + _up.quote(u.path, safe=""), headers=H)
            return route.fulfill(status=r.status_code, body=r.content, headers={"content-type": "text/html; charset=utf-8"})
        hd = {k: v for k, v in rq.headers.items() if k.lower() in ("authorization", "content-type")}; hd.update(H)
        r = c.request(rq.method, u.path + ("?" + u.query if u.query else ""), headers=hd, content=rq.post_data_buffer)
        return route.fulfill(status=r.status_code, body=r.content, headers={"content-type": r.headers.get("content-type", "application/octet-stream")})
    ctx.route("http://bv-test.com:%d/**" % PORT, _doc)
    pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    def a():
        pg.goto(URL)
        try: pg.wait_for_selector("text=Tabak Seti", timeout=15000)
        except Exception: raise AssertionError("sayfa: " + pg.inner_text("body")[:1500].replace("\n"," ") + " | " + pg.url)
        assert "1.000" in pg.inner_text("#okm-root") or "1000" in pg.inner_text("#okm-root"), pg.inner_text("#okm-root")
        pg.click("[data-go=bayi]"); pg.wait_for_selector("#b_c")
        pg.click("#b_go"); pg.wait_for_selector("#b_er", state="visible", timeout=5000)
        pg.fill("#b_c", "Ali Hırdavat Ltd."); pg.fill("#b_t", "1234567890"); pg.fill("#b_a", "Sanayi sitesi 5. blok Ankara"); pg.click("#b_go")
        pg.wait_for_selector("text=inceleniyor", timeout=8000)
    t("bayi olmayan hesap başvurur, başvuru inceleniyor görünür", a)
    def b():
        d = c.get("/api/yp/b2b/dealers", headers=O).json()["rows"][0]["id"]
        g = c.post("/api/yp/b2b/groups", headers=O, json={"name": "Altın", "discount_pct": 20, "min_order": 500}).json()["id"]
        assert c.post("/api/yp/b2b/dealers/" + d, headers=O, json={"status": "approved", "group_id": g, "credit_limit": 3000}).status_code == 200
        pg.goto(URL); pg.wait_for_selector("text=Tabak Seti", timeout=15000); pg.wait_for_timeout(600)
        txt = pg.inner_text("#okm-root")
        assert "Bayi hesabı" in txt and "%20 iskonto" in txt and "3.000" in txt, txt[:600]
        assert "800" in pg.inner_text("#okm-root"), pg.inner_text("#okm-root")
    t("onay sonrası bayi şeridi ve bayi fiyatı", b)
    def d():
        pg.click("text=Tabak Seti >> nth=0"); pg.wait_for_selector("text=Sepete ekle", timeout=8000)
        assert "800" in pg.inner_text("#okm-v"), "ürün sayfasında bayi fiyatı"
        pg.click("text=Sepete ekle"); pg.wait_for_timeout(500)
        pg.goto(URL + "#checkout"); pg.wait_for_selector("[name=pm]", timeout=10000); pg.wait_for_timeout(500)
        txt = pg.inner_text("#okm-v"); assert "Cari hesaba yaz" in txt and "Toplam" in txt and "800" in txt, txt[:700]
        assert pg.locator("[name=pm]").first.get_attribute("value") == "cari"
    t("sepet ve ödeme: bayi fiyatı, cari ödeme seçeneği", d)
    def e():
        if pg.locator("[name=ad]").count() == 0:
            pg.fill("#n_t", "İş"); pg.fill("#n_n", "Ali Bayi"); pg.fill("#n_p", "0532 555 11 22"); pg.fill("#n_c", "Ankara"); pg.fill("#n_d", "Çankaya"); pg.fill("#n_a", "Sanayi sitesi 5. blok")
        pg.check("#o_ok"); pg.click("#okm-go"); pg.wait_for_selector("text=cari hesabınıza işlendi", timeout=10000)
        me = c.get("/api/public/b2b/%s~me" % F, headers={"Authorization": "Bearer " + TOKEN}).json(); assert me["bakiye"] == 800 and me["kullanilabilir"] == 2200, me
    t("cari sipariş tamamlanır, borç yazılır", e)
    t("JavaScript hatası yok", lambda: errs and (_ for _ in ()).throw(AssertionError(errs[:3])))
    pg.screenshot(path="/tmp/bayi_vitrin.png")
    br.close()
srv.should_exit = True
for n in ok: print("  ✓", n)
for n, e in bad: print("  ✗", n, e)
print("OK", len(ok), "FAIL", len(bad)); sys.exit(1 if bad else 0)
