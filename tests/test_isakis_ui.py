"""İş akışı ve destek ekranları tarayıcıda: form, adım, imza tuvali, belge, talep."""
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
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Kuaför"}).json()
    EMAIL, PW = j["email"], j["password"]
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
    c.post("/api/yp/sectors/teknik", headers=H, json={})

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
        nav = pg.eval_on_selector_all("#nav a[data-r]", "a=>a.map(x=>x.dataset.r)")
        assert "is" in nav and "destek" in nav, nav
        pg.click("a[data-r=is]"); pg.wait_for_selector(".bosluk", timeout=8000)
        assert "Servis formu" in pg.inner_text("#main")
    t("teknik serviste İş kayıtları menüsü açılıyor", a)

    def b():
        pg.click("[data-a=is-yeni]"); pg.wait_for_selector("#isf", timeout=6000)
        alan = pg.eval_on_selector_all("#isf [name]", "a=>a.map(x=>x.name)")
        for k in ("_ad", "cihaz", "marka", "seri", "sikayet", "_iscilik"):
            assert k in alan, "%s alanı olmalı: %s" % (k, alan)
        pg.fill("#isf [name=_ad]", "Mehmet Yıldız"); pg.fill("#isf [name=_tel]", "05321112233")
        pg.fill("#isf [name=cihaz]", "Kombi"); pg.fill("#isf [name=marka]", "DemirDöküm")
        pg.fill("#isf [name=seri]", "DD-99120")
        pg.fill("#isf [name=sikayet]", "Isıtmıyor, E6 arıza kodu veriyor")
        pg.fill("#isf [name=_iscilik]", "600")
        pg.click("[data-a=is-parca-ekle]"); pg.wait_for_timeout(300)
        pg.fill('#prclist [data-pn="0"][data-f=name]', "Genleşme tankı")
        pg.fill('#prclist [data-pn="0"][data-f=price]', "850")
        pg.click("#isf button.p"); pg.wait_for_timeout(1400)
        tx = pg.inner_text("#islist")
        assert "Mehmet Yıldız" in tx and "Kombi" in tx and "1.450" in tx.replace(",00", ""), tx[:300]
    t("servis kaydı açılıyor, parça ve işçilik toplanıyor", b)

    def d():
        pg.click("#islist [data-a=is-ac]"); pg.wait_for_selector(".md .flow", timeout=6000)
        m = pg.inner_text(".md")
        assert "DD-99120" in m and "Genleşme tankı" in m and "Alınmadı" in m, m[:300]
        pg.click('.md [data-a=is-adim][data-v=bitti]'); pg.wait_for_timeout(1200)
        assert "imza" in pg.inner_text("#toast").lower(), pg.inner_text("#toast")
    t("imzasız kayıt tamamlanamıyor, sebebi söyleniyor", d)

    def e():
        pg.click(".md [data-a=is-imza]"); pg.wait_for_selector("#imzapad", timeout=6000)
        assert "belgeye basılacak" in pg.inner_text(".md"), "müşteriye özet gösterilmeli"
        pg.click("[data-a=imza-kaydet]"); pg.wait_for_timeout(700)
        assert "imzalamadı" in pg.inner_text("#toast"), pg.inner_text("#toast")
        box = pg.query_selector("#imzapad").bounding_box()
        pg.mouse.move(box["x"] + 40, box["y"] + 110)
        pg.mouse.down()
        for dx, dy in [(60, -40), (120, 30), (190, -30), (250, 20), (300, -20)]:
            pg.mouse.move(box["x"] + dx, box["y"] + 90 + dy)
        pg.mouse.up(); pg.wait_for_timeout(300)
        pg.click("[data-a=imza-kaydet]"); pg.wait_for_timeout(1600)
        assert "İmza kaydedildi" in pg.inner_text("#toast"), pg.inner_text("#toast")
        r = c.get("/api/yp/is/servis", headers=H).json()["items"][0]
        assert r["signed"] and r["sign"].startswith("data:image/png;base64,"), "imza PNG olarak kaydedilmeli"
        assert len(r["sign"]) > 2000, "boş tuval kaydedilmemeli"
    t("imza tuvali çalışıyor, boş imza reddediliyor, PNG kaydediliyor", e)

    def f():
        pg.wait_for_selector(".md", timeout=6000)
        assert "Alındı" in pg.inner_text(".md"), pg.inner_text(".md")[:200]
        pg.click('.md [data-a=is-adim][data-v=bitti]'); pg.wait_for_timeout(1500)
        assert "Tamamlandı" in pg.inner_text("#islist")
    t("imza alınınca kayıt tamamlanıyor", f)

    def g():
        pg.evaluate("closeM()"); pg.wait_for_timeout(400)
        pg.click("#islist [data-a=is-ac]"); pg.wait_for_selector(".md", timeout=6000)
        with pg.context.expect_page() as pop:
            pg.click(".md [data-a=is-belge]")
        p2 = pop.value; p2.wait_for_load_state("domcontentloaded"); p2.wait_for_timeout(500)
        body = p2.inner_text("body")
        assert "Servis formu" in body and "DD-99120" in body, repr(body[:400])
        assert "İMZASI" in body, "imza alanı belgede olmalı (büyük harf çevrimi Türkçe'de şaşırtır)"
        assert p2.eval_on_selector_all("img", "a=>a.length") >= 1, "imza belgede resim olarak olmalı"
        p2.close(); pg.evaluate("closeM()")
    t("belge yeni sekmede imzasıyla açılıyor", g)

    def h():
        pg.evaluate("closeM()"); pg.wait_for_timeout(300)
        pg.click("a[data-r=destek]"); pg.wait_for_selector(".bosluk", timeout=8000)
        pg.click("[data-a=dt-yeni]"); pg.wait_for_selector("#dtf", timeout=6000)
        ek = pg.eval_on_selector_all("#dtf [name=screen] option", "a=>a.map(x=>x.value)")
        assert "Siparişler" in ek and "Kasa" in ek, ek[:5]
        pg.fill("#dtf [name=subject]", "Kargo fişinde barkod çıkmıyor")
        pg.select_option("#dtf [name=category]", "hata")
        pg.select_option("#dtf [name=screen]", "Siparişler")
        pg.fill("#dtf [name=body]", "Kargo fişi yazdırınca barkod boş geliyor, ekran görüntüsü ekte.")
        pg.check("#dtf [name=acil]")
        pg.click("#dtf button.p"); pg.wait_for_timeout(1400)
        tx = pg.inner_text("#main")
        assert "Kargo fişinde barkod" in tx and "İşim duruyor" in tx and "DT-" in tx, tx[:300]
    t("destek talebi açılıyor, ekran ve aciliyet kaydediliyor", h)

    def i():
        pg.click(".tkt .k"); pg.wait_for_selector("#dmf", timeout=6000)
        assert "Siparişler" in pg.inner_text(".md")
        pg.fill("#dmf [name=text]", "Bir de şunu fark ettim")
        pg.click("#dmf button.p"); pg.wait_for_timeout(1400)
        assert "Bir de şunu" in pg.inner_text(".msg2")
        pg.click("[data-a=dt-kapat]"); pg.wait_for_selector("#askok", timeout=4000)
        pg.click("#askok"); pg.wait_for_timeout(1400)
        pg.click('[data-a=dseg][data-v=kapandi]'); pg.wait_for_timeout(800)
        assert "Kapandı" in pg.inner_text("#main")
    t("talebe mesaj ekleniyor ve talep kapatılıyor", i)

    def k():
        real = [e for e in errs if "favicon" not in e]
        assert not real, real[:2]
    t("iş akışı ve destek ekranlarında JavaScript hatası yok", k)
    br.close()
srv.should_exit = True
for x in ok: print("  ✓", x)
for x, e in bad: print("  ✗", x, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
