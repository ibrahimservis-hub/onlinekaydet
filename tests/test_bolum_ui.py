"""Bölüm ekle ekranı tarayıcıda: katalog, arama, ekleme, sıralama, bilgisayar/telefon ayarı, kaldırma."""
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
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165744", "sector": "E-ticaret"}).json()
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
    pg = br.new_page(viewport={"width": 1500, "height": 980})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:%d/salon" % PORT); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", EMAIL); pg.fill("#lf input[name=password]", PW)
    pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(400)

    def ac():
        pg.evaluate("location.hash='#bolum'"); pg.wait_for_selector("#bxl .row", timeout=10000)
        assert pg.locator("#bxpg option").count() >= 1, "sayfa seçici dolmalı"
        assert pg.locator("#bxp .it").count() == pg.locator("#bxl .row").count(), "kaba yerleşim bölüm sayısıyla aynı olmalı"
    t("ekran açılır: sayfa seçici, bölüm listesi ve kaba yerleşim gelir", ac)

    def kat():
        pg.click('[data-a="bxadd"]'); pg.wait_for_selector("#bxg .bxcard", timeout=8000)
        n = pg.locator("#bxg .bxcard").count()
        assert n > 20, "katalogda çok bölüm olmalı, gelen: %d" % n
        assert pg.locator("#bxc button").count() > 5, "kategori listesi gelmeli"
        assert pg.locator(".md.xw").count() == 1, "katalog geniş pencerede açılmalı"
        kart = pg.locator("#bxg .bxcard").first
        assert kart.locator(".wf").count() == 1, "kartta tel çerçeve önizlemesi olmalı"
        assert "Mobil + web ayrı" in kart.inner_text() or "Tek düzen" in kart.inner_text()
    t("katalog açılır: kategoriler, kartlar, tel çerçeve önizlemesi", kat)

    def ktg():
        pg.click('#bxc button[data-c="eticaret"]'); pg.wait_for_timeout(600)
        pg.wait_for_selector("#bxg .bxcard", timeout=8000)
        assert pg.locator('#bxc button[data-c="eticaret"].on').count() == 1, "seçili kategori işaretlenmeli"
        hep = pg.locator("#bxg .bxcard").count()
        pg.fill("#bxq", "indirim"); pg.wait_for_timeout(700)
        az = pg.locator("#bxg .bxcard").count()
        assert az < hep and az > 0, "arama süzmeli (%d -> %d)" % (hep, az)
    t("kategori süzer, arama kutusu daraltır", ktg)

    def ekle():
        once = pg.evaluate("BX.rows.length")
        pg.locator("#bxg .bxcard").first.click()
        pg.wait_for_selector("#bxf", timeout=8000)          # eklenince ayar penceresi açılır
        assert pg.locator('#bxf [data-a="bxfdev"]').count() == 2, "bilgisayar/telefon sekmesi olmalı"
        pg.click('#bxf button[data-a="close"]'); pg.wait_for_timeout(400)
        assert pg.evaluate("BX.rows.length") == once + 1, "bölüm eklenmeli"
    t("karta tıklayınca bölüm eklenir ve ayar penceresi açılır", ekle)

    def kapatPencere():
        if pg.locator("#ov:not([hidden])").count():
            pg.keyboard.press("Escape"); pg.wait_for_timeout(250)

    def ayar():
        kapatPencere()
        pg.locator('#bxl [data-a="bxset"]').last.click(); pg.wait_for_selector("#bxf", timeout=8000)
        alan = pg.locator("#bxf [data-k]").count()
        assert alan > 2, "bilgisayar sekmesinde alanlar gelmeli"
        sec = pg.locator("#bxf select[data-k]").first
        anahtar = sec.get_attribute("data-k")
        secenek = sec.locator("option").nth(1).get_attribute("value")
        sec.select_option(secenek)
        pg.click("#bxf button.p"); pg.wait_for_timeout(700)
        v = pg.evaluate("BX.rows[BX.rows.length-1].set['%s']" % anahtar)
        assert str(v) == secenek, "bilgisayar ayarı kaydedilmeli: %s != %s" % (v, secenek)
        assert pg.evaluate("Object.keys(BX.rows[BX.rows.length-1].set_m||{}).length") == 0, "telefon ayarına dokunulmamalı"
    t("bilgisayar ayarı kaydedilir, telefon ayarına dokunulmaz", ayar)

    def tel():
        kapatPencere()
        pg.locator('#bxl [data-a="bxset"]').last.click(); pg.wait_for_selector("#bxf", timeout=8000)
        hep = pg.locator("#bxf [data-k], #bxf [data-a=bxsw]").count()
        pg.click('#bxf button[data-a="bxfdev"][data-d="phone"]'); pg.wait_for_timeout(500)
        az = pg.locator("#bxf [data-k], #bxf [data-a=bxsw]").count()
        assert az <= hep, "telefon sekmesinde alan sayısı artmamalı"
        assert "bilgisayarla aynı" in pg.inner_text("#bxf"), "miras durumu yazmalı"
        sec = pg.locator("#bxf select[data-k]").first
        anahtar = sec.get_attribute("data-k")
        secenek = sec.locator("option").last.get_attribute("value")
        sec.select_option(secenek)
        pg.click("#bxf button.p"); pg.wait_for_timeout(700)
        sm = pg.evaluate("BX.rows[BX.rows.length-1].set_m")
        assert str(sm.get(anahtar)) == secenek, "telefon ayarı set_m'ye yazılmalı: %s" % sm
        assert "telefona özel" in pg.inner_text("#bxl"), "listede telefona özel rozeti çıkmalı"
        assert len(sm) == 1, "yalnız değiştirilen alan telefona ayrılmalı, gelen: %s" % sm
    t("telefon sekmesi yalnız ayrılabilir alanları gösterir, set_m'ye yazar", tel)

    def miras():
        kapatPencere()
        pg.locator('#bxl [data-a="bxset"]').last.click(); pg.wait_for_selector("#bxf", timeout=8000)
        once = pg.evaluate("JSON.stringify(BX.rows[BX.rows.length-1].set_m)")
        pg.click('#bxf button[data-a="bxfdev"][data-d="phone"]'); pg.wait_for_timeout(500)
        pg.click("#bxf button.p"); pg.wait_for_timeout(700)      # hiçbir şeye dokunmadan kaydet
        sonra = pg.evaluate("JSON.stringify(BX.rows[BX.rows.length-1].set_m)")
        assert once == sonra, "dokunulmayan ayar telefona özel sayılmamalı: %s -> %s" % (once, sonra)
    t("telefonda dokunulmadan kaydetmek mirası bozmaz", miras)

    def geri():
        kapatPencere()
        pg.locator('#bxl [data-a="bxset"]').last.click(); pg.wait_for_selector("#bxf", timeout=8000)
        pg.click('#bxf button[data-a="bxfdev"][data-d="phone"]'); pg.wait_for_timeout(500)
        assert pg.locator('#bxf [data-a="bxgeri"]').count() >= 1, "geri dön bağlantısı olmalı"
        pg.locator('#bxf [data-a="bxgeri"]').first.click(); pg.wait_for_timeout(700)
        assert pg.evaluate("Object.keys(BX.rows[BX.rows.length-1].set_m||{}).length") == 0, "telefon ayarı bırakılmalı"
        pg.click('#bxf button[data-a="close"]'); pg.wait_for_timeout(300)
    t("telefona özel ayar tek tıkla bilgisayardakine döner", geri)

    def sira():
        kapatPencere()
        ad = pg.evaluate("BX.rows.map(function(x){return x.iid})")
        if len(ad) < 2: return
        pg.locator('#bxl [data-a="bxup"]').last.click(); pg.wait_for_timeout(700)
        yeni = pg.evaluate("BX.rows.map(function(x){return x.iid})")
        assert yeni != ad and yeni[-1] == ad[-2], "sıra değişmeli"
        pg.reload(); pg.wait_for_selector("#app:not([hidden])", timeout=15000)
        pg.evaluate("location.hash='#bolum'"); pg.wait_for_selector("#bxl .row", timeout=10000)
        assert pg.evaluate("BX.rows.map(function(x){return x.iid})") == yeni, "sıra sunucuda kalmalı"
    t("yukarı/aşağı sırayı değiştirir ve sunucuda kalır", sira)

    def kapat():
        kapatPencere()
        say = pg.evaluate("BX.rows.length")
        pg.locator('#bxl [data-a="bxtog"]').last.click(); pg.wait_for_timeout(600)
        assert pg.evaluate("BX.rows[BX.rows.length-1].on") is False, "bölüm kapanmalı"
        assert pg.locator("#bxp .it.off").count() >= 1, "kaba yerleşimde sönük görünmeli"
        assert pg.evaluate("BX.rows.length") == say
    t("bölüm açma/kapama kaba yerleşime de yansır", kapat)

    def sil():
        kapatPencere()
        say = pg.evaluate("BX.rows.length")
        pg.locator('#bxl [data-a="bxdel"]').last.click(); pg.wait_for_selector("#askok", timeout=5000)
        pg.click("#askok"); pg.wait_for_timeout(800)
        assert pg.evaluate("BX.rows.length") == say - 1, "bölüm kaldırılmalı"
    t("bölüm onayla kaldırılır", sil)

    def hata():
        assert not errs, "sayfa hatası: " + " | ".join(errs[:3])
    t("ekranda JavaScript hatası yok", hata)
    br.close()
srv.should_exit = True
print("\n".join("  ✓ " + n for n in ok))
for n, e in bad: print("  ✗ " + n + "\n" + e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA: %d/%d" % (len(bad), len(ok) + len(bad))))
sys.exit(1 if bad else 0)
