"""Entegrasyon ekranı tarayıcıda: bağlama, hata gösterimi, deneme, maskeli anahtar, kaldırma."""
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
        pg.click("a[data-r=entegrasyon]"); pg.wait_for_selector("#elist .e", timeout=8000)
        assert pg.eval_on_selector_all(".egrp .c", "a=>a.length") >= 6, "tür kartları"
        tx = pg.inner_text("#main")
        for x in ("iyzico", "Aras Kargo", "Paraşüt", "Nebim V3", "Trendyol"):
            assert x in tx, "%s görünmeli" % x
        assert "bağlı yok" in tx
    t("entegrasyon merkezi türlere ayrılmış olarak açılıyor", a)

    def b():
        pg.fill("#eq", "aras"); pg.wait_for_timeout(400)
        assert pg.eval_on_selector_all("#elist .e", "a=>a.length") == 1
        pg.fill("#eq", ""); pg.wait_for_timeout(400)
        pg.click('.egrp .c[data-v=erp]'); pg.wait_for_selector("#elist .e", timeout=5000)
        tx = pg.inner_text("#elist")
        assert "Nebim" in tx and "iyzico" not in tx, tx[:200]
        pg.click('.egrp .c[data-v=erp]'); pg.wait_for_timeout(600)
    t("arama ve tür süzgeci çalışıyor", b)

    def d():
        pg.fill("#eq", "netgsm"); pg.wait_for_timeout(400)
        pg.click("#elist [data-a=ent-ac]"); pg.wait_for_selector("#entf", timeout=6000)
        assert "Anahtarı nereden alırım" in pg.inner_text(".md"), "yardım kutusu"
        pg.fill("#entf input[name=user]", "8503030000")
        pg.fill("#entf input[name=pass]", "gizli123")
        pg.fill("#entf input[name=header]", "COKUZUNBASLIK")
        pg.click("#entf button.p"); pg.wait_for_timeout(900)
        assert "11 karakter" in pg.inner_text(".md .errbox"), pg.inner_text(".md")[:200]
    t("hatalı anahtar kaydedilmiyor, sebep formda yazıyor", d)

    def e():
        pg.fill("#entf input[name=header]", "ONLINEKAYD")
        pg.click("#entf button.p"); pg.wait_for_timeout(1600)
        pg.fill("#eq", "netgsm"); pg.wait_for_timeout(400)
        tx = pg.inner_text("#elist")
        assert "Bağlı" in tx and "Test" in tx, tx[:200]
    t("düzeltilince bağlanıyor ve listede bağlı görünüyor", e)

    def f():
        pg.click("#elist [data-a=ent-ac]"); pg.wait_for_selector("#entf", timeout=6000)
        v = pg.input_value("#entf input[name=pass]")
        assert v.startswith("••••"), "şifre maskeli gelmeli: %s" % v
        pg.fill("#entf input[name=user]", "8503030001")
        pg.click("#entf button.p"); pg.wait_for_timeout(900)
        r = c.get("/api/yp/integrations/netgsm", headers=H).json()["item"]
        assert [x for x in r["fields"] if x["key"] == "pass"][0]["filled"], "maskeli değer şifreyi silmemeli"
        assert [x for x in r["fields"] if x["key"] == "user"][0]["value"] == "8503030001"
    t("maskeli şifre olduğu gibi gönderilip eski değeri silmiyor", f)

    def g():
        pg.click("#elist [data-a=ent-ac]"); pg.wait_for_selector("#entf", timeout=6000)
        pg.click("#entf [data-a=ent-dene]"); pg.wait_for_timeout(1200)
        assert "çalışıyor" in pg.inner_text("#toast").lower() or pg.is_visible(".md .okbox"), pg.inner_text(".md")[:200]
        pg.evaluate("closeM()")
    t("bağlantıyı dene düğmesi sonucu söylüyor", g)

    def h():
        pg.fill("#eq", "ga4"); pg.wait_for_timeout(300)
        pg.fill("#eq", "Analytics"); pg.wait_for_timeout(500)
        pg.click("#elist [data-a=ent-ac]"); pg.wait_for_selector("#entf", timeout=6000)
        assert not pg.is_visible("#entf [data-a=ent-dene]"), "denemesi olmayan entegrasyonda düğme olmamalı"
        pg.fill("#entf input[name=id]", "UA-123")
        pg.click("#entf button.p"); pg.wait_for_timeout(900)
        assert "G-" in pg.inner_text(".md .errbox")
        pg.fill("#entf input[name=id]", "G-ABC123DEF4")
        pg.click("#entf button.p"); pg.wait_for_timeout(1600)
        pg.fill("#eq", "Analytics"); pg.wait_for_timeout(400)
        assert "Bağlı" in pg.inner_text("#elist")
    t("ölçüm kodu biçim hatası formda gösteriliyor", h)

    def i():
        pg.click("#elist [data-a=ent-ac]"); pg.wait_for_selector("#entf", timeout=6000)
        pg.click("#entf [data-a=ent-sil]"); pg.wait_for_selector("#askok", timeout=4000)
        pg.click("#askok"); pg.wait_for_timeout(1600)
        pg.fill("#eq", "Analytics"); pg.wait_for_timeout(500)
        assert "Bağlı değil" in pg.inner_text("#elist")
    t("bağlantı kaldırılıyor", i)

    def k():
        pg.fill("#eq", ""); pg.wait_for_timeout(300)
        pg.click("[data-a=ent-kayit]"); pg.wait_for_selector(".md .logrow", timeout=6000)
        tx = pg.inner_text(".md")
        assert "Netgsm" in tx and "gizli123" not in tx, "kayıtta şifre görünmemeli"
        pg.evaluate("closeM()")
    t("işlem kaydı açılıyor ve anahtar sızdırmıyor", k)

    def l():
        pg.click("[data-a=ent-hepsini-dene]"); pg.wait_for_timeout(2500)
        tx = pg.inner_text("#main") + pg.inner_text("#toast")
        assert "çalışıyor" in tx.lower() or pg.is_visible(".md"), tx[-200:]
        pg.evaluate("closeM()")
    t("hepsini dene bağlı entegrasyonları sırayla sınıyor", l)

    def m():
        real = [e for e in errs if "favicon" not in e]
        assert not real, real[:2]
    t("entegrasyon ekranında JavaScript hatası yok", m)
    br.close()
srv.should_exit = True
for x in ok: print("  ✓", x)
for x, e in bad: print("  ✗", x, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
