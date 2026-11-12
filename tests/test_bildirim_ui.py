"""Bildirim ekranı tarayıcıda: şablon düzenleme, SMS sayacı, sadeleştirme, duyuru, takip."""
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
    pid = c.post("/api/yp/products", headers=H, json={"name": "Keten Gömlek", "price": 899,
                                                      "cost": 400, "stock": 0}).json()["id"]
    c.post("/api/yp/notify/takip", headers=H, json={"product": pid, "phone": "05321112233", "kind": "stok"})
    st = c.get("/api/yp/boot", headers=H).json()["staff"][0]["id"]
    for n2 in range(3):
        c.post("/api/yp/appts", headers=H, json={"name": "Müşteri %d" % n2, "phone": "053200000%02d" % n2,
                                                 "date": "2026-11-20", "time": "1%d:00" % n2, "staff_id": st,
                                                 "items": [{"name": "Kesim", "price": 300, "dur": 30}]})

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
        pg.click("#nav a[data-r=bildirim]"); pg.wait_for_selector("#blist .n", timeout=8000)
        tx = pg.inner_text("#main")
        assert "Kargoya verildi" in tx and "Stoğa gelince haber ver" in tx, tx[:300]
        assert "SMS sağlayıcısı bağlı değil" in tx, "bağlı değilken uyarı"
        assert pg.eval_on_selector_all("#blist .n", "a=>a.length") >= 10
    t("bildirim listesi sektöre göre açılıyor, sağlayıcı uyarısı veriyor", a)

    def b():
        pg.click('[data-a=bseg][data-v=stok]'); pg.wait_for_timeout(400)
        tx = pg.inner_text("#blist")
        assert "Stoğa gelince" in tx and "Kargoya verildi" not in tx, tx[:200]
        pg.click('[data-a=bseg][data-v=""]'); pg.wait_for_timeout(400)
    t("küme süzgeci çalışıyor", b)

    def d():
        pg.click('#blist .n[data-id=siparis_kargoda] [data-a=bil-ac2]'); pg.wait_for_selector("#bilf", timeout=6000)
        pg.wait_for_timeout(700)
        assert "SP-2026-00412" in pg.inner_text("#bilprev"), "önizleme örnek veriyle dolmalı"
        assert "{takip}" in pg.inner_text(".varl"), "değişken listesi"
        pg.fill("#biltxt", "{firma}: {siparis_no} siparişiniz {kargo} ile yola çıktı.")
        pg.wait_for_timeout(800)
        assert "Türkçe" in pg.inner_text("#bilsms"), pg.inner_text("#bilsms")
    t("şablon düzenlenirken önizleme ve SMS uzunluğu anında güncelleniyor", d)

    def e():
        onc = pg.inner_text("#bilsms")
        pg.click("#bilf [data-a=bil-sade]"); pg.wait_for_timeout(800)
        v = pg.input_value("#biltxt")
        assert "siparisiniz" in v and "cikti" in v, v
        assert "Türkçe" not in pg.inner_text("#bilsms"), pg.inner_text("#bilsms")
    t("Türkçe karakterleri sadeleştir düğmesi metni ve sayacı düzeltiyor", e)

    def f():
        pg.click("#bilf [data-a=bil-var][data-v=takip]"); pg.wait_for_timeout(600)
        assert "{takip}" in pg.input_value("#biltxt")
        pg.click("#bilf button.p"); pg.wait_for_timeout(1200)
        tx = pg.inner_text("#blist")
        assert "düzenlendi" in tx, tx[:300]
    t("değişken tıklanınca metne ekleniyor, şablon kaydediliyor", f)

    def g():
        pg.click('#blist .n[data-id=siparis_kargoda] [data-a=bil-ac2]'); pg.wait_for_selector("#bilf", timeout=6000)
        pg.click("#bilf [data-a=bil-sifirla]"); pg.wait_for_timeout(1200)
        tx = pg.inner_text('#blist .n[data-id=siparis_kargoda]')
        assert "düzenlendi" not in tx and "yola cikti" in tx, tx
    t("hazır metne dön çalışıyor", g)

    def h():
        pg.click('#blist .n[data-id=dogum_gunu] input[data-a=bil-ac]'); pg.wait_for_timeout(900)
        r = c.get("/api/yp/notify", headers=H).json()
        d2 = [i for i in r["items"] if i["id"] == "dogum_gunu"][0]
        assert d2["on"] is True, d2
    t("bildirim açma düğmesi kaydediyor", h)

    def i():
        pg.click("[data-a=bil-duyuru]"); pg.wait_for_selector("#duyf", timeout=6000)
        assert pg.is_disabled("#duygo"), "hesaplamadan gönderilemez"
        pg.fill("#duytxt", "Kasım ayına özel indirim")
        pg.click("[data-a=duy-hesap]"); pg.wait_for_timeout(1200)
        tx = pg.inner_text("#duyozet")
        assert "Gönderilecek kişi" in tx and "Toplam SMS" in tx, tx[:200]
        assert "Türkçe" in pg.inner_text("#duysms")
        assert not pg.is_disabled("#duygo")
        pg.click("#duygo"); pg.wait_for_selector("#askok", timeout=4000)
        pg.click("#askok"); pg.wait_for_timeout(1200)
        assert "sağlayıcı" in pg.inner_text("#toast"), pg.inner_text("#toast")
    t("duyuru önce hesaplıyor, sağlayıcısız göndermiyor", i)

    def k():
        pg.evaluate("closeM()"); pg.wait_for_timeout(300)
        pg.click("[data-a=bil-takip]"); pg.wait_for_selector(".md table", timeout=6000)
        assert "Keten Gömlek" in pg.inner_text(".md") and "Stoğa gelince" in pg.inner_text(".md")
        c.put("/api/yp/products/" + pid, headers=H, json={"stock": 10})
        pg.click("[data-a=takip-calistir]"); pg.wait_for_timeout(1200)
        assert "haber verildi" in pg.inner_text("#toast"), pg.inner_text("#toast")
        pg.click("[data-a=bil-kayit]"); pg.wait_for_selector(".md .logrow", timeout=6000)
        assert "0532 111 22 33" in pg.inner_text(".md"), pg.inner_text(".md")[:200]
        pg.evaluate("closeM()")
    t("stok takibi ekranı ve gönderim kaydı çalışıyor", k)

    def l():
        real = [e for e in errs if "favicon" not in e]
        assert not real, real[:2]
    t("bildirim ekranında JavaScript hatası yok", l)
    br.close()
srv.should_exit = True
for x in ok: print("  ✓", x)
for x, e in bad: print("  ✗", x, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
