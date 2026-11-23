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
        pg.evaluate("ueGit('genel')"); 
        pg.fill("#uef input[name=short]", "Sessiz çalışan pompa")
        pg.fill("#uef textarea[name=desc]", "Kombiler için sirkülasyon pompası. Orijinal yedek parça, 2 yıl garantili.")
        pg.evaluate("ueGit('fiyat')"); 
        pg.fill("#uef input[name=price]", "1200"); pg.fill("#uef input[name=cost]", "700")
        pg.evaluate("ueGit('stok')"); 
        pg.fill("#uef input[name=sku]", "POMPA-24")
        pg.evaluate("ueGit('kat')"); 
        pg.click("[data-a=ue-katsec]"); pg.fill("#kpn", "Pompa"); pg.click("[data-a=kp-yeni]"); pg.wait_for_timeout(400); pg.click("[data-a=kp-tamam]")
        pg.fill("#uetag", "kombi"); pg.click("[data-a=ue-tag]")
        pg.evaluate("ueGit('ozellik')"); 
        pg.click("[data-a=ue-spec]"); pg.fill("#uespecs input[data-sp=k]", "Güç"); pg.fill("#uespecs input[data-sp=v]", "24 kW")
        pg.evaluate("ueGit('seo')"); 
        pg.fill("#uef input[name=seo_title]", "Kombi Pompası 24 kW | Test")
        pg.evaluate("ueGit('kargo')"); 
        pg.fill("#uef input[name=en]", "20"); pg.fill("#uef input[name=boy]", "20"); pg.fill("#uef input[name=yuk]", "30")
        pg.wait_for_timeout(500)
        pg.evaluate("ueGit('kanal')"); 
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
    PAGE = '<html><head><title>Kombi Pompası | Magaza</title><meta property="og:title" content="Kombi Pompası"><meta property="og:description" content="Sessiz pompa"><meta property="og:image" content="https://x.test/a.jpg"></head><body></body></html>'
    def m():
        pg.evaluate("V.urun().catch(function(){})"); pg.wait_for_selector("[data-a=um-ac]", timeout=8000)
        pg.click("[data-a=um-ac]"); pg.wait_for_selector("#umenu", timeout=3000)
        assert pg.locator("#umenu [role=menuitem]").count() >= 4
        pg.click("#umenu [data-a=um-hizli]"); pg.wait_for_selector("#hdz", timeout=4000)
        pg.fill("#hdz input[name=price]", "1777"); pg.fill("#hdz input[name=stock]", "9")
        pg.click("#hdz button.p"); pg.wait_for_selector("#hdz", state="detached", timeout=5000)
        it = (c.get("/api/yp/products/" + PID, headers=TK()).json())
        it = it.get("item") or it
        assert it["price"] == 1777 and it["stock"] == 9, (it["price"], it["stock"])
        pg.wait_for_selector("[data-a=um-ac]"); pg.click("[data-a=um-ac]"); pg.click("#umenu [data-a=um-yayin]"); pg.wait_for_timeout(700)
        it = c.get("/api/yp/products/" + PID, headers=TK()).json(); it = it.get("item") or it
        assert it["status"] == "draft", it["status"]
        pg.click("[data-a=um-ac]"); pg.keyboard.press("Escape"); assert pg.locator("#umenu").count() == 0
    t("Ürün satırı menüsü: fiyat/stok, yayından kaldır, Esc", m)
    def h():
        pg.evaluate("V.urun().catch(function(){})"); pg.wait_for_selector("[data-a=urun-hizli]", timeout=8000)
        pg.click("[data-a=urun-hizli]"); pg.wait_for_selector("#hzf", timeout=4000)
        pg.click("#hzf summary"); pg.fill("#hzf textarea[name=html]", PAGE); pg.click("#hzf button.p")
        pg.wait_for_selector("#uef", timeout=6000)
        assert pg.input_value("#uef input[name=name]").startswith("Kombi Pompası")
        assert pg.evaluate("UE.images.length") == 1
    t("Bağlantıdan ürün ekle: kaynak yapıştır → düzenleyici dolu açılır", h)
    def tp():
        H2 = TK()
        c.put("/api/yp/integrations/trendyol", headers=H2, json={"on": True, "keys": {"seller_id": "123", "api_key": "k", "api_secret": "s"}})
        for n in range(2): c.post("/api/yp/products", headers=H2, json={"name": "Toplu %d" % n, "price": 300, "cost": 100, "stock": 5, "sku": "TP%d" % n})
        pg.evaluate("V.urun().catch(function(){})"); pg.wait_for_selector(".gr tbody input[type=checkbox]", timeout=8000)
        pg.locator(".gr tbody input[type=checkbox]").nth(0).check(); pg.locator(".gr tbody input[type=checkbox]").nth(1).check()
        pg.click("[data-a=usel-pgonder]"); pg.wait_for_selector("#ubm", timeout=4000)
        pg.check("#ubm input[value=trendyol]"); pg.click("#ubm button.p")
        pg.wait_for_selector("#ubr", timeout=8000)
        assert "Trendyol" in pg.inner_text("#ubr") and "eksikli" in pg.inner_text("#ubr")
        pg.click("#ubr ~ .mf .btn.p"); pg.wait_for_selector("#ubr", state="detached", timeout=3000)
        pg.wait_for_selector(".gr tbody input[type=checkbox]"); pg.locator(".gr tbody input[type=checkbox]").nth(0).check()
        pg.click("[data-a=usel-kapat]"); pg.wait_for_selector("#ubm", timeout=4000); pg.click("#ubm button.p")
        pg.wait_for_selector("#ubm", state="detached", timeout=6000)
    t("Toplu: pazaryerlerine gönder sonucu, satışa kapat", tp)
    def yz():
        pg.evaluate("V.urun().catch(function(){})"); pg.wait_for_selector("[data-a=urun-yeni]", timeout=8000)
        pg.click("[data-a=urun-yeni]"); pg.wait_for_selector("#uef")
        pg.fill("#uef input[name=name]", "Baxi Eco Plaka Eşanjör"); pg.evaluate("ueGit('genel')"); pg.fill("#uef input[name=short]", "Elle yazılmış kısa metin")
        pg.click("[data-a=ue-yaz][data-v=gen]"); pg.wait_for_selector("#uyf", timeout=6000)
        assert pg.locator("#uyf input[name=short]").is_checked() is False, "dolu alan varsayılan değişmemeli"
        assert pg.locator("#uyf input[name=desc]").is_checked()
        pg.click("[data-a=ue-yaz-uygula]"); pg.wait_for_selector("#uyf", state="detached")
        assert pg.input_value("#uef input[name=short]") == "Elle yazılmış kısa metin"
        assert "Baxi Eco Plaka" in pg.input_value("#uef textarea[name=desc]")
        pg.evaluate("ueGit('seo')"); pg.click("[data-a=ue-yaz][data-v=seo]"); pg.wait_for_selector("#uyf"); pg.click("[data-a=ue-yaz-uygula]")
        assert pg.input_value("#uef input[name=seo_title]").startswith("Baxi")
    t("Düzenleyici: yazı öner (dolu alan korunur, boş alan dolar)", yz)
    def vr():
        pg.evaluate("V.urun().catch(function(){})"); pg.wait_for_selector("[data-a=urun-yeni]", timeout=8000)
        pg.click("[data-a=urun-yeni]"); pg.wait_for_selector("#uef")
        pg.fill("#uef input[name=name]", "Varyantlı Gömlek"); pg.evaluate("ueGit('fiyat')"); pg.fill("#uef input[name=price]", "900"); pg.evaluate("ueGit('varyant')")
        pg.click("[data-a=ue-axekle]"); pg.fill("[data-axn=\"0\"]", "Renk"); pg.dispatch_event("[data-axn=\"0\"]", "change")
        for v in ("Beyaz", "Mavi"):
            pg.fill("[data-axv=\"0\"]", v); pg.press("[data-axv=\"0\"]", "Enter")
        pg.click("[data-a=ue-axekle]"); pg.fill("[data-axn=\"1\"]", "Beden"); pg.dispatch_event("[data-axn=\"1\"]", "change")
        for v in ("M", "L"):
            pg.fill("[data-axv=\"1\"]", v); pg.press("[data-axv=\"1\"]", "Enter")
        pg.click("[data-a=ue-vgen]"); pg.wait_for_selector("#uevar [data-vr=stock]")
        assert pg.locator("#uevar .uetb tbody tr").count() == 4
        pg.fill("#uevst", "3"); pg.click("[data-a=ue-vst]")
        pg.locator("[data-vr=sku]").nth(0).fill("GM-B-M"); pg.locator("[data-vr=price]").nth(1).fill("950")
        assert pg.input_value("#uef input[name=stock]") == "12" and pg.is_editable("#uef input[name=stock]") is False
        pg.click(".uetop [data-a=ue-kaydet][data-v=live]"); pg.wait_for_selector("#uef", state="detached", timeout=6000)
        r = c.get("/api/yp/products?q=Varyantl%C4%B1", headers=TK()).json()["rows"][0]
        full = c.get("/api/yp/products/" + r["id"], headers=TK()).json(); full = full.get("item") or full
        assert len(full["variants"]) == 4 and full["stock"] == 12 and [a["ad"] for a in full["var_axes"]] == ["Renk", "Beden"], full["var_axes"]
        assert full["variants"][0]["sku"] == "GM-B-M" and full["variants"][1]["price"] == 950
        pg.wait_for_selector("[data-a=urun-ac]"); pg.click("[data-a=urun-ac][data-id=\"%s\"]" % r["id"]); pg.wait_for_selector("#uef"); pg.evaluate("ueGit('varyant')"); pg.wait_for_selector("#uevar .uetb tbody tr")
        assert pg.locator("#uevar .uetb tbody tr").count() == 4
    t("Düzenleyici: renk/beden tanımla, kombinasyon üret, stok/fiyat, kaydet", vr)
    assert not errs, errs
    br.close()
for n in ok: print("  ✓", n)
for n, e in bad: print("  ✗", n, "\n", e)
print("OK %d FAIL %d" % (len(ok), len(bad)))
