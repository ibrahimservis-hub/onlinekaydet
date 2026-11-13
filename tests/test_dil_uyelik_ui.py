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
    def tok(e, p): return {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": e, "password": p}).json()["token"]}
    A = tok("admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Dil UI", "email": "dui@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    c.put("/api/admin/firms/%s" % r.json()["id"], headers=A, json={"premium_themes": True})
    EMAIL, PW = "dui@x.com", "sifre12345"; H = tok(EMAIL, PW)
    c.post("/api/yp/sectors/kuafor", headers=H)
    assert c.put("/api/brand", headers=H, json={"theme": "k6-butik-kuafor", "dark": "#1a1a1a", "accent": "#b08d57", "radius": 8}).status_code == 200

port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try:
        sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1400, "height": 960})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:%d/salon" % PORT); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", EMAIL); pg.fill("#lf input[name=password]", PW)
    pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(400)
    def uy():
        pg.click('#nav a[data-r=uyelik]'); pg.wait_for_selector('[data-a="uy-tog"]', timeout=10000)
        assert "Hesabım bölümleri" in pg.inner_text("#main")
        pg.click('[data-k="on"]'); pg.wait_for_timeout(600)
        assert pg.locator('[data-k="on"]').get_attribute("aria-checked") == "true"
    t("Üyelik ekranı açılır, anahtar kaydedilir", uy)
    def gg():
        pg.click('[data-k="google"]'); pg.wait_for_selector('#uyg input[name=gid]', timeout=10000)
        assert "SMS sağlayıcısı" not in pg.inner_text("#main")            # SMS kapalıyken uyarı yok
        pg.fill('#uyg input[name=gid]', "abc-1.apps.googleusercontent.com"); pg.click('#uyg button'); pg.wait_for_timeout(700)
        pg.click('[data-k="sms"]'); pg.wait_for_timeout(700)
        assert "SMS sağlayıcısı bağlı değil" in pg.inner_text("#main")      # bağlı değilken açıkça uyarır
        assert pg.input_value('#uyg input[name=gid]').startswith("abc-1")
    t("Google istemci kimliği girilir, SMS bağlı değilse uyarı çıkar", gg)
    def dl():
        pg.click('#nav a[data-r=dil]'); pg.wait_for_selector('[data-a="dl-dil"]', timeout=10000)
        assert pg.locator('[data-a="dl-dil"][data-id="en"]').get_attribute("aria-pressed") == "true"   # kuaför için İngilizce hazır gelir
        pg.click('[data-a="dl-dil"][data-id="de"]'); pg.wait_for_timeout(700)
        assert pg.locator('[data-a="dl-dil"][data-id="de"]').get_attribute("aria-pressed") == "true"
        pg.wait_for_selector('[data-a="dl-oto"]', timeout=10000)
        pg.wait_for_selector("#dlt input[data-dl]", timeout=10000)
        pg.locator('#dlt input[data-dl]').first.fill("Hello"); pg.click('[data-a="dl-kaydet"]'); pg.wait_for_timeout(700)
        assert pg.locator('#dlt input[data-dl]').first.input_value() == "Hello"
    t("Diller: dil eklenir, çeviri tablosu kaydedilir", dl)
    def onz():
        pg.evaluate("location.hash='#site'"); pg.wait_for_selector(".stabs button", timeout=10000)
        pg.click('.stabs button[data-t="bolum"]'); pg.wait_for_timeout(250)
        pg.click('[data-a="sted"][data-e="blok"]'); pg.wait_for_selector('[data-a="bxadd"]', timeout=10000)
        pg.click('[data-a="bxadd"]'); pg.wait_for_selector('.bxcard [data-a="bxprev"]', timeout=10000)
        pg.locator('.bxcard [data-a="bxprev"]').first.click(); pg.wait_for_selector('#ov iframe', timeout=10000)
        assert "pexels" in pg.get_attribute('#ov iframe', 'srcdoc')
    t("katalogda Önizle örnek fotoğraflı bölümü gösterir", onz)
    pg.evaluate("document.getElementById('ov').hidden=true")
    def uy2():
        pg.click('#nav a[data-r=uyelik]'); pg.wait_for_selector('[data-a="uy-sms"]', timeout=10000)
        assert pg.locator('[data-a="uy-xlsx"]').count() == 1 and pg.locator('[data-k="cuzdan_on"]').count() == 1
        pg.click('[data-a="uy-sms"]'); pg.wait_for_selector('#uysf', timeout=8000); pg.wait_for_timeout(600)
        assert "üyeye gidecek" in pg.inner_text("#uysn")
        pg.evaluate("document.getElementById(\"ov\").hidden=true")
    t("Üyelik: toplu SMS penceresi ve Excel düğmesi", uy2)
    def dl2():
        pg.click('#nav a[data-r=dil]'); pg.wait_for_selector('#dl-ana', timeout=10000)
        pg.fill('#dl-kor', "OnlineKaydet, Servis Plus"); pg.click('[data-a="dl-kor"]'); pg.wait_for_timeout(600)
        pg.select_option('#dl-gor', 'kod'); pg.wait_for_timeout(600)
        c2 = c.get("/api/yp/dil", headers=H).json()["cfg"]
        assert c2["korunan"] == ["OnlineKaydet", "Servis Plus"] and c2["gorunum"] == "kod", c2
        assert pg.locator('[data-a="dl-csv"]').count() == 1
    t("Diller: ana dil, görünüm, sözlük ve CSV", dl2)
    def du():
        pg.click('#nav a[data-r=duyuru]'); pg.wait_for_selector('#duf', timeout=10000)
        pg.fill('#duf textarea[name=text]', "Bayram indirimi başladı"); pg.click('#duf button[type=submit]'); pg.wait_for_timeout(600)
        pg.click('[data-a="du-tog"]'); pg.wait_for_timeout(700)
        d = c.get("/api/yp/duyuru", headers=H).json()
        assert d["on"] and d["text"] == "Bayram indirimi başladı", d
    t("Duyuru ekranı: metin kaydedilir, yayına alınır", du)
    def ep():
        pg.evaluate("V.eplus()"); pg.wait_for_selector('#epck', timeout=10000)
        assert pg.locator('#epfd').count() == 1 and pg.locator('#eprk').count() == 1 and pg.locator('#epdl .epd').count() == 6
        pg.click('[data-a="ep-dl"]'); assert pg.locator('#epdl .epd').count() == 7
        pg.click('[data-k="akakce"]'); pg.wait_for_selector('[data-k="akakce"].on', timeout=8000)
        assert c.get("/api/yp/feed", headers=H).json()["akakce"] is True
    t("Fiyat ve güvenlik ekranı: besleme, risk, çark dilimleri", ep)
    def dt():
        pg.evaluate("V.destek()"); pg.wait_for_selector('[data-a="dt-yeni"]', timeout=10000); pg.click('[data-a="dt-yeni"]'); pg.wait_for_selector('#dtdrop', timeout=8000)
        png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        pg.evaluate("""(b64)=>{var bin=atob(b64),u=new Uint8Array(bin.length);for(var i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);
          var f=new File([u],'image.png',{type:'image/png'}),dt=new DataTransfer();dt.items.add(f);
          document.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}))}""", png)
        pg.wait_for_selector('#dtek img', timeout=8000)
        pg.evaluate("""(b64)=>{var bin=atob(b64),u=new Uint8Array(bin.length);for(var i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);
          var f=new File([u],'b.png',{type:'image/png'}),dt=new DataTransfer();dt.items.add(f);
          document.getElementById('dtdrop').dispatchEvent(new DragEvent('drop',{dataTransfer:dt,bubbles:true,cancelable:true}))}""", png)
        pg.wait_for_function("document.querySelectorAll('#dtek img').length==2", timeout=8000)
    t("Destek: Ctrl+V ile yapıştırma ve sürükle-bırak ekran görüntüsü ekler", dt)
    t("sayfa hatası yok", lambda: errs and (_ for _ in ()).throw(AssertionError(errs)) or None)
    br.close()
print("ok", len(ok), "bad", len(bad))
for n, tb in bad: print("FAIL", n, tb)
sys.exit(1 if bad else 0)
