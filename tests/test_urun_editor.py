"""Tarayıcıda: tam sayfa ürün düzenleyici (pazaryeri fiyatı, SEO, kategori, kâr)."""
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
        import traceback; bad.append((n, traceback.format_exc()[-900:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ali", "phone": "05524165755", "sector": "Kuaför"}).json()
    EMAIL, PW = j["email"], j["password"]
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
    c.post("/api/yp/sectors/kuafor", headers=H, json={})
    async def setup():
        f = await s.db.main().firms.find_one({"login_email": EMAIL}, {"_id": 0, "db": 1})
        await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": "k5-atolye-kuafor"}}, upsert=True)
        fm = await s.db.main().firms.find_one({"login_email": EMAIL}, {"_id": 0, "modules": 1})
        await s.db.main().firms.update_one({"login_email": EMAIL}, {"$set": {"modules": list(fm.get("modules") or ["servis", "site", "randevu", "muhasebe", "rapor", "sms", "pazarlama", "personel"]) + ["eticaret"]}})
    c.portal.call(setup)
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try:
        sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1440, "height": 960})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:%d/salon" % PORT); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", EMAIL); pg.fill("#lf input[name=password]", PW)
    pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(400)
    def prod():
        H2 = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
        return c.post("/api/yp/products", headers=H2, json={"name": "Deneme Lamba", "price": 500, "cost": 200, "stock": 7, "cat": "Ev"}).json()["id"]
    def TK():
        return {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
    def a():
        pg.evaluate("V.urun().catch(function(){})"); pg.wait_for_timeout(800)
        pg.click("[data-a=urun-yeni]"); pg.wait_for_selector("#uef", timeout=6000)
        assert pg.locator(".ues").count() >= 8
        pg.fill("#uef input[name=name]", "Test Kombi Pompası 24 kW")
        assert pg.input_value("#uef input[name=slug]") == "test-kombi-pompasi-24-kw"
        pg.fill("#uef input[name=short]", "Sessiz çalışan pompa")
        pg.fill("#uef textarea[name=desc]", "Kombiler için sirkülasyon pompası. Orijinal yedek parça, 2 yıl garantili.")
        pg.fill("#uef input[name=price]", "1200"); pg.fill("#uef input[name=cost]", "700")
        pg.fill("#uef input[name=sku]", "POMPA-24")
        pg.fill("#uecat", "Pompa"); pg.click("[data-a=ue-cat]")
        pg.fill("#uetag", "kombi"); pg.click("[data-a=ue-tag]")
        pg.click("[data-a=ue-spec]"); pg.fill("#uespecs input[data-sp=k]", "Güç"); pg.fill("#uespecs input[data-sp=v]", "24 kW")
        pg.fill("#uef input[name=seo_title]", "Kombi Pompası 24 kW | Test")
        pg.fill("#uef input[name=en]", "20"); pg.fill("#uef input[name=boy]", "20"); pg.fill("#uef input[name=yuk]", "30")
        pg.wait_for_timeout(500)
        ks = pg.evaluate("Object.keys(UE.ch).filter(function(k){return k!=='site'})")
        if ks:
            k = ks[0]
            pg.click("[data-a=ue-chtog][data-k=%s]" % k); pg.wait_for_timeout(200)
            pg.evaluate("UE.ch[%r].mod='sabit';UE.ch[%r].fiyat='1350'" % (k, k))
        pg.click(".uetop [data-a=ue-kaydet][data-v=live]")
        pg.wait_for_selector("#uef", state="detached", timeout=6000)
        r = c.get("/api/yp/products?q=POMPA-24", headers=TK()).json()
        it = (r.get("rows") or r.get("items"))[0]
        full = c.get("/api/yp/products/" + it["id"], headers=TK()).json(); full = full.get("item") or full
        assert full["slug"] == "test-kombi-pompasi-24-kw", full.get("slug")
        assert full["seo"]["title"].startswith("Kombi Pompası"), full.get("seo")
        assert full["cats"][0] == "Pompa" and "kombi" in full["tags"]
        assert full["specs"][0]["k"] == "Güç"
        assert full.get("desi", 0) > 0 or full["ship"].get("en") == 20, (full.get("desi"), full["ship"])
        if ks: assert full["ch_price"][ks[0]]["fiyat"] == 1350, full["ch_price"]
        globals()["PID"] = it["id"]
    t("Düzenleyici: yeni ürün, kanal fiyatı, SEO, kategori, desi", a)
    def b():
        pg.evaluate("V.urun().catch(function(){})"); pg.wait_for_selector("[data-a=urun-ac]", timeout=8000)
        pg.click("[data-a=urun-ac][data-id=\"%s\"]" % PID); pg.wait_for_selector("#uef", timeout=6000)
        assert pg.input_value("#uef input[name=sku]") == "POMPA-24"
        assert "Kombi Pompası" in pg.inner_text(".ueserp")
        pg.click("[data-a=ue-kopya]"); pg.wait_for_timeout(800)
        assert pg.input_value("#uef input[name=name]").endswith("(kopya)")
        assert pg.input_value("#uef input[name=sku]") == ""
    t("Düzenleyici: mevcut ürünü aç, SERP önizleme, kopya", b)
    def d():
        pg.evaluate("location.hash='#bugun'"); pg.wait_for_timeout(600)
        assert pg.evaluate("UE") is None
    t("Düzenleyici: başka sayfaya geçince durum temizlenir", d)
    assert not errs, errs
    br.close()
for n in ok: print("  ✓", n)
for n, e in bad: print("  ✗", n, "\n", e)
print("OK %d FAIL %d" % (len(ok), len(bad)))
