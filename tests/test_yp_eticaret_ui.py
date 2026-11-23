"""Panel e-ticaret ekranları gerçek tarayıcıda: ürün ekle, sipariş aç, iade, kampanya kur ve dene."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn
from starlette.testclient import TestClient
from playwright.sync_api import sync_playwright

s = boot.server
ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-900:]))

# demo firma + e-ticaret paketi + örnek veri
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "E-ticaret"}).json()
    EMAIL, PW = j["email"], j["password"]
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
    c.post("/api/yp/sectors/eticaret", headers=H, json={})
    for nm, pr, co, st, cat in [("Keten Gömlek", 899, 420, 12, "Gömlek"), ("Pamuk Çorap", 149, 40, 60, "Çorap"),
                                ("Yün Kazak", 1249, 600, 3, "Kazak")]:
        c.post("/api/yp/products", headers=H, json={"name": nm, "price": pr, "cost": co, "stock": st,
                                                    "cat": cat, "brand": "Nevermore", "low_at": 5})
    c.post("/api/yp/campaigns", headers=H, json={"name": "3 al 2 öde — Çorap", "type": "x_al_y_ode",
                                                 "cond": {"buy": 3, "pay": 2}, "scope": {"all": False, "cats": ["Çorap"]}})
    c.post("/api/yp/campaigns", headers=H, json={"name": "1.000 ₺ üzeri kargo bedava", "type": "kargo",
                                                 "cond": {"min_total": 1000}, "scope": {"all": True}})
    pid = c.get("/api/yp/products", headers=H).json()["rows"][0]["id"]
    c.post("/api/yp/orders", headers=H, json={"channel": "trendyol",
        "customer": {"name": "Mehmet Yıldız", "phone": "05321112233", "city": "İstanbul", "address": "Kadıköy"},
        "items": [{"product": pid, "name": "Keten Gömlek", "price": 899, "qty": 2, "cost": 420}], "ship_fee": 49.9})

port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
cfg = uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical")
srv = uvicorn.Server(cfg)
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try:
        sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)

U = "http://127.0.0.1:%d/salon" % PORT
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(U); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", EMAIL); pg.fill("#lf input[name=password]", PW)
    pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(600)

    def a():
        nav = pg.eval_on_selector_all("#nav a[data-rs]", "a=>a.flatMap(x=>x.dataset.rs.split(','))")
        assert "urun" in nav and "siparis" in nav and "kampanya" in nav, nav
        assert "randevu" not in nav, "e-ticarette randevu menüsü görünmemeli: %s" % nav
    t("e-ticaret paketinde menü ürün/sipariş/kampanya gösteriyor, randevuyu gizliyor", a)

    def bb():
        pg.click("a[data-r=urun]"); pg.wait_for_selector("#ulist table tbody tr", timeout=8000)
        rows = pg.eval_on_selector_all("#ulist tbody tr", "r=>r.length")
        assert rows == 3, rows
        txt = pg.inner_text("#ulist")
        assert "Keten Gömlek" in txt and "Az stok" in txt, txt[:300]
        assert "899" in txt
    t("ürün listesi fiyat, stok ve az stok uyarısıyla doluyor", bb)

    def d():
        pg.click("[data-a=urun-yeni]"); pg.wait_for_selector("#uef", timeout=5000)
        pg.fill("#uef input[name=name]", "Termal İçlik")
        pg.evaluate("ueGit('fiyat')"); pg.fill("#uef input[name=price]", "249"); pg.fill("#uef input[name=cost]", "90")
        pg.evaluate("ueGit('stok')"); pg.fill("#uef input[name=stock]", "25")
        pg.evaluate("ueGit('kat')"); pg.click("[data-a=ue-katsec]"); pg.fill("#kpn", "İç Giyim"); pg.click("[data-a=kp-yeni]"); pg.wait_for_timeout(400); pg.click("[data-a=kp-tamam]")
        pg.evaluate("ueGit('fiyat')"); assert "Kâr" in pg.inner_text("#uekar"), "kârlılık anında hesaplanmalı"
        pg.click("[data-a=ue-kaydet][data-v=publish]") if pg.locator("[data-a=ue-kaydet][data-v=publish]").count() else pg.click("[data-a=ue-kaydet].p")
        pg.wait_for_timeout(1500)
        pg.goto(pg.url.split("#")[0] + "#urun"); pg.wait_for_selector("#ulist", timeout=8000); pg.wait_for_timeout(800)
        assert "Termal İçlik" in pg.inner_text("#ulist")
    t("ürün ekleme formu kaydediyor, kârı anında gösteriyor", d)

    def e():
        pg.fill("#uq", "çorap"); pg.wait_for_timeout(700)
        assert pg.eval_on_selector_all("#ulist tbody tr", "r=>r.length") == 1
        pg.fill("#uq", ""); pg.wait_for_timeout(700)
        pg.click("#useg button[data-v=az_stok]"); pg.wait_for_timeout(700)
        assert "Yün Kazak" in pg.inner_text("#ulist")
    t("ürün arama ve az stok süzgeci çalışıyor", e)

    def f():
        pg.click("a[data-r=siparis]"); pg.wait_for_selector("#slist table tbody tr", timeout=8000)
        assert "Mehmet Yıldız" in pg.inner_text("#slist")
        assert "Trendyol" in pg.inner_text("#slist")
        assert "Ciro" in pg.inner_text("#sfig") and "Net kâr" in pg.inner_text("#sfig")
    t("sipariş listesi ve ciro/kâr kutuları geliyor", f)

    def g():
        pg.click("#slist [data-a=sip-ac]"); pg.wait_for_selector(".md .flow", timeout=6000)
        m = pg.inner_text(".md")
        assert "Keten Gömlek" in m and "Tahsil edilen" in m and "Net kâr" in m, m[:300]
        assert pg.eval_on_selector_all(".md .flow .stp", "a=>a.length") == 5
        pg.click(".md [data-a=sip-durum][data-v=onaylandi]"); pg.wait_for_timeout(900)
        assert "Onaylandı" in pg.inner_text("#slist")
    t("sipariş detayı açılıyor, durum akışı panelden ilerliyor", g)

    def h():
        pg.click("#slist [data-a=sip-ac]"); pg.wait_for_selector(".md .flow", timeout=6000)
        pg.click(".md [data-a=sip-iade]"); pg.wait_for_selector("#iaf", timeout=6000)
        pg.check("#iaf input[name=pick]")
        pg.fill("#iaf input[name=q0]", "1")
        pg.select_option("#iaf select[name=reason]", "kusurlu urun")
        pg.click("#iaf button.p"); pg.wait_for_timeout(1000)
        tx = pg.inner_text("#main")
        assert "IA-" in tx and "İade talebi" in tx, tx[:300]
        pg.click("[data-a=iade-durum][data-v=onay]"); pg.wait_for_selector("#askok", timeout=4000)
        pg.click("#askok"); pg.wait_for_timeout(1000)
        assert "Onaylandı" in pg.inner_text("#main")
    t("iade talebi alınıyor (2 adetten 1 adet), onayda stok geri dönüyor", h)

    def i():
        pg.evaluate("location.hash='#urun'"); pg.wait_for_selector("#useg button", timeout=8000)
        pg.click('#useg button[data-v=""]'); pg.wait_for_timeout(700)
        pg.fill("#uq", "keten"); pg.wait_for_timeout(900)
        pg.wait_for_selector("#ulist tbody tr", timeout=8000)
        stok = pg.inner_text("#ulist tbody tr td:nth-child(5)")
        assert "11" in stok, "2 satıldı 1 iade döndü → 11 olmalı: %s" % stok
    t("stok sipariş ve iadeye göre doğru: 12 − 2 + 1 = 11", i)

    def k():
        pg.click("a[data-r=kampanya]")
        pg.wait_for_function("()=>{var h=document.querySelector('#main h1');return h&&h.textContent==='Kampanyalar'}", timeout=8000)
        pg.wait_for_selector("#main [data-a=kmp-ac]", timeout=8000)
        tx = pg.inner_text("#main")
        assert "3 al 2 öde" in tx and "kargo bedava" in tx.lower(), tx[:300]
        assert "Aktif" in tx
    t("kampanya listesi açılıyor", k)

    def l():
        pg.click("[data-a=kmp-yeni]"); pg.wait_for_selector("#kf", timeout=6000)
        assert pg.eval_on_selector_all("#kf .ktp", "a=>a.length") == 6
        pg.fill("#kf input[name=name]", "2 alana 3. ürün yarı fiyat")
        pg.click("#kf .ktp[data-v=kademeli]"); pg.wait_for_selector("#kf input[name=give]", timeout=5000)
        assert pg.input_value("#kf input[name=name]") == "2 alana 3. ürün yarı fiyat", "tip değişince ad korunmalı"
        pg.fill("#kf input[name=buy]", "2"); pg.fill("#kf input[name=give]", "1")
        pg.fill("#kf input[name=y_percent]", "50")
        pg.click("#kf button.p"); pg.wait_for_timeout(1000)
        assert "2 alana 3. ürün yarı fiyat" in pg.inner_text("#main")
    t("kampanya kurma: tip değiştirince kural alanları değişiyor, kayıt oluyor", l)

    def m():
        pg.click("[data-a=kmp-dene]"); pg.wait_for_selector("#dsepet", timeout=6000)
        for _ in range(3):
            pg.click("[data-a=dene-ekle]")
        rows = pg.query_selector_all("#dsepet .iline")
        assert len(rows) == 3
        for n in range(3):
            pg.fill('#dsepet [data-dn="%d"][data-f=name]' % n, "Pamuk Çorap")
            pg.fill('#dsepet [data-dn="%d"][data-f=cat]' % n, "Çorap")
            pg.fill('#dsepet [data-dn="%d"][data-f=price]' % n, "149")
        pg.click("[data-a=dene-calistir]"); pg.wait_for_selector("#dsonuc .hit", timeout=6000)
        tx = pg.inner_text("#dsonuc")
        assert "149" in tx and "3 al 2 öde" in tx, tx[:400]
        assert "en az" in tx or "tutar gerekli" in tx, "girmeyen kampanyanın sebebi yazmalı: %s" % tx[:400]
    t("kampanya deneme sepeti: indirim ve girmeyen kampanyanın sebebi görünüyor", m)

    def n():
        real = [e for e in errs if "favicon" not in e and "turnstile" not in e.lower()]
        assert not real, real[:3]
    t("ekranlarda JavaScript hatası yok", n)
    b.close()
srv.should_exit = True
for x in ok: print("  ✓", x)
for x, e in bad: print("  ✗", x, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
