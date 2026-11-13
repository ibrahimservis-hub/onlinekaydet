"""Popup ürün vitrini: ayar API, kural seçimi, sitede pencere (gecikme, kapatınca tekrar çıkmaz), panel ekranı."""
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
    r = c.post("/api/admin/firms", headers=A, json={"name": "Vitrin Pop Firma", "email": "pv@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "pv@x.com", "sifre12345")
    async def setup():
        f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
        await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": "p01-cine-kombi"}}, upsert=True)
        await s.db.main().firm_domains.insert_one({"id": "dp1", "domain": "pv-test.com", "firm_id": F, "db": f["db"], "status": "yayinda"})
        fm = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "modules": 1})
        await s.db.main().firms.update_one({"id": F}, {"$set": {"modules": list(fm.get("modules") or []) + ["eticaret"]}})
    c.portal.call(setup)
    import domains; domains._cache["t"] = 0
    H = {"Host": "pv-test.com"}
    def get(p): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers=H)
    c.put("/api/site/features", headers=O, json={"shop_enabled": True})
    P = {}
    for n, pr, old, st in (("Kombi pompası A", 1200, 1500, 5), ("Kombi pompası B", 950, 0, 5), ("Kombi pompası C", 800, 1000, 0), ("Termostat", 600, 900, 3)):
        r = c.post("/api/shop/products", headers=O, json={"name": n, "price": pr, "old_price": old, "stock": st, "category": "Yedek parça", "brand": "Wilo"})
        assert r.status_code == 200, r.text; P[n] = r.json()["id"]
    def page(p="/"): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers=H).text
    def api1():
        assert 'id="okpv' not in page(), "kapalıyken pencere yok"
        r = c.put("/api/yp/popvitrin", headers=O, json={"on": True, "kural": "indirimli", "adet": 4, "baslik": "Haftanın fırsatları", "gecikme": 1, "cikis": False})
        assert r.status_code == 200, r.text
        names = [x["name"] for x in r.json()["onizleme"]]
        assert names == ["Termostat", "Kombi pompası A"], ("indirim oranına göre, stoksuz C yok", names)
        h = page()
        assert 'id="okpv' in h and "Haftanın fırsatları" in h and "Termostat" in h and "Kombi pompası C" not in h and "Kombi pompası B" not in h
        assert "/magaza/urun/" in h
        assert 'id="okpv' not in page("/hesabim"), "hesabım sayfasında çıkmaz"
    t("indirimli kuralı: en yüksek indirim önce, stokta olmayan gösterilmez", api1)
    def api2():
        r = c.put("/api/yp/popvitrin", headers=O, json={"kural": "secili", "ids": []})
        assert r.status_code == 422, "seçili kuralda ürün zorunlu"
        r = c.put("/api/yp/popvitrin", headers=O, json={"kural": "secili", "ids": [P["Kombi pompası B"]]})
        assert [x["name"] for x in r.json()["onizleme"]] == ["Kombi pompası B"]
        r = c.put("/api/yp/popvitrin", headers=O, json={"sayfa": "ana"})
        assert 'id="okpv' in page("/") and 'id="okpv' not in page("/magaza"), "yalnız ana sayfa"
        r = c.put("/api/yp/popvitrin", headers=O, json={"kural": "yeni", "sayfa": "hepsi", "siklik": "oturum"})
        assert r.json()["onizleme"][0]["name"] == "Termostat"
        c.put("/api/site/features", headers=O, json={"shop_enabled": False})
        assert 'id="okpv' not in page(), "mağaza kapalıyken çıkmaz"
        c.put("/api/site/features", headers=O, json={"shop_enabled": True})
        assert c.put("/api/yp/popvitrin", headers=O, json={"kural": "uydurma"}).status_code == 422
    t("seçili/yeni kuralı, yalnız ana sayfa, mağaza kapalıyken gizli", api2)
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try:
        sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)
import urllib.parse as _up
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--host-resolver-rules=MAP pv-test.com 127.0.0.1"])
    for vw in ({"width": 1366, "height": 900}, {"width": 390, "height": 844}):
        pg = br.new_page(viewport=vw); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        B = "http://pv-test.com:%d" % PORT
        def _doc(route):
            rq = route.request; u = _up.urlparse(rq.url)
            if rq.resource_type == "document" and not u.path.startswith("/api"):
                r = c.get("/api/public/hosted-site?p=" + _up.quote(u.path, safe=""), headers=H)
                return route.fulfill(status=r.status_code, body=r.content, headers={"content-type": "text/html; charset=utf-8"})
            hd = {k: v for k, v in rq.headers.items() if k.lower() in ("authorization", "content-type")}; hd.update(H)
            r = c.request(rq.method, u.path + ("?" + u.query if u.query else ""), headers=hd, content=rq.post_data_buffer)
            return route.fulfill(status=r.status_code, body=r.content, headers={"content-type": r.headers.get("content-type", "application/octet-stream")})
        pg.route(B + "/**", _doc)
        def a():
            pg.goto(B + "/"); box = pg.locator("[role=dialog][id^=okpv]")
            assert not box.is_visible(), "gecikmeden önce görünmez"
            pg.wait_for_selector("[id^=okpv].on", timeout=5000)
            assert box.locator(".pvpc").count() >= 1
            pg.wait_for_timeout(300); pg.screenshot(path="/tmp/pv_%d.png" % vw["width"])
            assert pg.evaluate("document.querySelector('[id^=okpv] .pvbx').getBoundingClientRect().right<=innerWidth+1")
            pg.keyboard.press("Escape"); assert not box.is_visible(), "Esc ile kapanır"
            pg.goto(B + "/"); pg.wait_for_timeout(2200)
            assert pg.locator("[role=dialog][id^=okpv]").count() == 0, "aynı ziyarette tekrar çıkmaz"
        t("sitede popup %dpx: gecikmeyle açılır, Esc kapatır, tekrar çıkmaz" % vw["width"], a)
        assert not [e for e in errs], errs
        pg.close()
    # panel ekranı
    pg = br.new_page(viewport={"width": 1366, "height": 900}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    def ui():
        pg.goto("http://127.0.0.1:%d/salon" % PORT); pg.wait_for_selector("#lf", timeout=15000)
        pg.fill("#lf input[name=email]", "pv@x.com"); pg.fill("#lf input[name=password]", "sifre12345")
        pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(500)
        pg.evaluate("location.hash='#popvitrin'"); pg.wait_for_selector("#pvf", timeout=8000)
        pg.select_option("#pvf select[name=kural]", "secili"); assert pg.locator("#pvsec").is_visible()
        pg.fill("#pvq", "Termo"); pg.wait_for_selector("[data-a=pv-ekle]", timeout=5000); pg.click("[data-a=pv-ekle]")
        pg.fill("#pvf input[name=baslik]", "Panelden başlık"); pg.click("#pvf button[type=submit]"); pg.wait_for_timeout(700)
        assert "Termostat" in pg.locator("#pvon").inner_text()
        r = c.get("/api/yp/popvitrin", headers=O).json()
        assert r["kural"] == "secili" and r["baslik"] == "Panelden başlık" and P["Termostat"] in r["ids"], r
        pg.screenshot(path="/tmp/pv_panel.png", full_page=True)
    t("panel ekranı: seçili ürün ekle, kaydet, önizleme", ui)
    assert not errs, errs
    br.close()
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" FAIL", n, e)
sys.exit(1 if bad else 0)
