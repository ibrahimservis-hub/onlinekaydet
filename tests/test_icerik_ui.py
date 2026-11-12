"""İçerik ekranı tarayıcıda: tür geçişi, form tanımdan kuruluyor, onay, sıralama, boş ekran."""
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
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Kuaför"}).json()
    EMAIL, PW = j["email"], j["password"]
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
    for n2 in range(3):
        c.post("/api/public/yp/yorum", json={"name": "Müşteri %d" % n2, "rating": 5,
                                             "text": "Çok memnun kaldım %d" % n2})

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
        pg.click("#nav a[data-r=icerik]"); pg.wait_for_selector("#iclist .r4", timeout=8000)
        tx = pg.inner_text(".ictab")
        assert "Müşteri yorumları" in tx and "3 onay bekliyor" in tx, tx[:200]
        assert "Blog yazıları" in tx and "Sık sorulanlar" in tx
        assert pg.eval_on_selector_all("#iclist .r4", "a=>a.length") == 3
        assert pg.eval_on_selector_all("#iclist .r4.bek2", "a=>a.length") == 3, "bekleyenler ayrı görünmeli"
    t("içerik türleri ve bekleyen yorumlar açılıyor", a)

    def b():
        pg.click('#iclist .r4 [data-a=ic-karar][data-v=onay]'); pg.wait_for_timeout(1300)
        assert "Onaylandı" in pg.inner_text("#toast") or "sitede" in pg.inner_text("#toast")
        assert pg.eval_on_selector_all("#iclist .r4.bek2", "a=>a.length") == 2
        tx = pg.inner_text(".ictab")
        assert "2 onay bekliyor" in tx, tx[:200]
        pg.click('[data-a=icseg][data-v=yayin]'); pg.wait_for_timeout(700)
        assert pg.eval_on_selector_all("#iclist .r4", "a=>a.length") == 1
        pg.click('[data-a=icseg][data-v=""]'); pg.wait_for_timeout(700)
    t("yorum onaylanıyor, sayaç ve süzgeç güncelleniyor", b)

    def d():
        pg.click('[data-a=ic-tur][data-v=sss]'); pg.wait_for_selector(".bosluk", timeout=6000)
        assert "Sık sorulanlar" in pg.inner_text(".bosluk"), "boş ekran türü anlatmalı"
        pg.click("[data-a=ic-yeni]"); pg.wait_for_selector("#icf", timeout=6000)
        alan = pg.eval_on_selector_all("#icf [name]", "a=>a.map(x=>x.name)")
        assert alan == ["q", "a", "group", "on"], "form tür tanımından kurulmalı: %s" % alan
        pg.fill("#icf [name=q]", "Randevumu nasıl iptal ederim?")
        pg.fill("#icf [name=a]", "Bize mesaj atmanız yeterli.")
        pg.click("#icf button.p"); pg.wait_for_timeout(1300)
        assert "Randevumu nasıl" in pg.inner_text("#iclist")
    t("tür değişince form alanları değişiyor, kayıt ekleniyor", d)

    def e():
        pg.click("[data-a=ic-yeni]"); pg.wait_for_selector("#icf", timeout=6000)
        pg.fill("#icf [name=q]", "Cevapsız soru")
        pg.click("#icf button.p"); pg.wait_for_timeout(1100)
        assert "gerekli" in pg.inner_text("#toast").lower(), pg.inner_text("#toast")
        pg.evaluate("closeM()")
    t("zorunlu alan boşsa hata söyleniyor", e)

    def f():
        for q in ("Ödeme nasıl yapılır?", "Geç kalırsam ne olur?"):
            pg.click("[data-a=ic-yeni]"); pg.wait_for_selector("#icf", timeout=6000)
            pg.fill("#icf [name=q]", q); pg.fill("#icf [name=a]", "Cevap")
            pg.click("#icf button.p"); pg.wait_for_timeout(1100)
        ids = pg.eval_on_selector_all("#iclist .r4", "a=>a.map(x=>x.dataset.id)")
        assert len(ids) == 3
        pg.eval_on_selector_all("#iclist .r4", """a=>{var p=a[0].parentNode;p.insertBefore(a[2],a[0]);}""")
        yeni = pg.eval_on_selector_all("#iclist .r4", "a=>a.map(x=>x.dataset.id)")
        pg.evaluate("""ids=>api('/yp/content/sss/sira',{method:'POST',body:{ids:ids}})""", yeni)
        pg.wait_for_timeout(900)
        r = c.get("/api/yp/content/sss", headers=H).json()["items"]
        assert [x["id"] for x in r] == yeni, "sıra sunucuya yazılmalı"
    t("sıralama sunucuya kaydediliyor", f)

    def g():
        pg.click('[data-a=ic-tur][data-v=duyuru]'); pg.wait_for_timeout(800)
        pg.click("[data-a=ic-yeni]"); pg.wait_for_selector("#icf", timeout=6000)
        secenek = pg.eval_on_selector_all("#icf [name=color] option", "a=>a.map(x=>x.value)")
        assert "turuncu" in secenek and "mor" not in secenek, secenek
        assert pg.get_attribute("#icf [name=until]", "type") == "date"
        pg.fill("#icf [name=text]", "Bayram boyunca kapalıyız")
        pg.select_option("#icf [name=color]", "turuncu")
        pg.click("#icf button.p"); pg.wait_for_timeout(1300)
        assert "Bayram boyunca" in pg.inner_text("#iclist")
    t("seçenek listesi ve tarih alanı tanımdan geliyor", g)

    def h():
        pg.click("#iclist [data-a=ic-duzen]"); pg.wait_for_selector("#icf", timeout=6000)
        assert pg.input_value("#icf [name=text]") == "Bayram boyunca kapalıyız"
        pg.fill("#icf [name=text]", "Bayramda 9-13 arası açığız")
        pg.click("#icf button.p"); pg.wait_for_timeout(1300)
        assert "9-13 arası" in pg.inner_text("#iclist")
        pg.click("#iclist [data-a=ic-duzen]"); pg.wait_for_selector("#icf", timeout=6000)
        pg.click("#icf [data-a=ic-sil]"); pg.wait_for_selector("#askok", timeout=4000)
        pg.click("#askok"); pg.wait_for_timeout(1300)
        assert pg.is_visible(".bosluk"), "silinince boş ekran"
    t("düzenleme ve silme çalışıyor", h)

    def i():
        real = [e for e in errs if "favicon" not in e]
        assert not real, real[:2]
    t("içerik ekranında JavaScript hatası yok", i)
    br.close()
srv.should_exit = True
for x in ok: print("  ✓", x)
for x, e in bad: print("  ✗", x, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
