"""Başlangıç rehberi: sektöre göre adımlar, gerçek veriden tamamlanma, gizleme ve ekran."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n); print("  ✓", n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:])); print("  ✗", n); print(bad[-1][1][-300:])
with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    def firma(ad, em, sec):
        r = c.post("/api/admin/firms", headers=A, json={"name": ad, "email": em, "password": "sifre12345", "package": "baslangic"}); assert r.status_code == 200, r.text
        H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": em, "password": "sifre12345"}).json()["token"]}
        c.post("/api/yp/sectors/" + sec, headers=H, json={}); return H
    Hk = firma("Rehber Kuaför", "rk@x.com", "kuafor")
    He = firma("Rehber Shop", "re@x.com", "eticaret")
    Ht = firma("Rehber Teknik", "rt@x.com", "kombi")
    def a():
        r = c.get("/api/yp/rehber", headers=Hk).json()
        ids = [x["id"] for x in r["steps"]]
        assert ids[0] == "firma" and "hizmet" in ids and "ilk" in ids and "urun" not in ids, ids
        assert not r["bitti"] and r["n"] < r["toplam"], r
    t("randevu işinde randevu adımları geliyor", a)
    def b():
        r = c.get("/api/yp/rehber", headers=He).json()
        ids = [x["id"] for x in r["steps"]]
        assert "urun" in ids and "odeme" in ids and "kargo" in ids and "hizmet" not in ids, ids
    t("sipariş işinde ürün, ödeme ve kargo adımları geliyor", b)
    def d():
        r = c.get("/api/yp/rehber", headers=Ht).json()
        assert r["steps"] == [] and r["bitti"], r
    t("teknik serviste rehber boş (eski panel akışı)", d)
    def e():
        before = c.get("/api/yp/rehber", headers=He).json()
        assert not [x for x in before["steps"] if x["id"] == "urun"][0]["bitti"]
        r = c.post("/api/yp/products", headers=He, json={"name": "Rehber Ürün", "price": 100, "stock": 5, "active": True}); assert r.status_code == 200, r.text
        after = c.get("/api/yp/rehber", headers=He).json()
        assert [x for x in after["steps"] if x["id"] == "urun"][0]["bitti"] and after["n"] == before["n"] + 1, after
    t("ürün ekleyince adım gerçek veriden tamamlanıyor", e)
    def f():
        assert c.post("/api/yp/rehber/gizle", headers=He, json={"gizli": True}).json()["ok"]
        assert c.get("/api/yp/rehber", headers=He).json()["gizli"]
        c.post("/api/yp/rehber/gizle", headers=He, json={"gizli": False})
        assert not c.get("/api/yp/rehber", headers=He).json()["gizli"]
    t("gizleme kaydediliyor ve geri açılıyor", f)
    def g():
        assert c.get("/api/yp/rehber", headers={"Authorization": "Bearer yanlis"}).status_code in (401, 403)
    t("girişsiz erişilemiyor", g)
    # ekran
    import uvicorn
    from playwright.sync_api import sync_playwright
    port = socket.socket(); port.bind(("127.0.0.1", 0)); P = port.getsockname()[1]; port.close()
    srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=P, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start(); time.sleep(2)
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        for tag, vw in (("m", 390), ("d", 1280)):
            pg = br.new_page(viewport={"width": vw, "height": 900}, device_scale_factor=2 if tag == "m" else 1)
            errs = []; pg.on("pageerror", lambda x: errs.append(str(x)[:120]))
            pg.goto("http://127.0.0.1:%d/salon" % P); pg.wait_for_selector("#lf")
            pg.fill("#lf input[name=email]", "re@x.com"); pg.fill("#lf input[name=password]", "sifre12345"); pg.click("#lb")
            pg.wait_for_selector("#app:not([hidden])"); pg.wait_for_timeout(1500)
            pg.screenshot(path="/tmp/rh_%s.png" % tag)
            def ui(): 
                assert pg.query_selector(".rh"), "rehber kartı yok"
                assert len(pg.query_selector_all(".rhl li")) >= 5
                assert pg.query_selector(".rhl li.cur .btn.p")
                assert not errs, errs
            t("ekranda rehber görünüyor (%s)" % tag, ui)
            pg.click("[data-a=rh-gizle]"); pg.wait_for_timeout(1200)
            t("Gizle ile kart kalkıyor (%s)" % tag, lambda: (_ for _ in ()).throw(AssertionError("kart duruyor")) if pg.query_selector(".rh") else None)
            c.post("/api/yp/rehber/gizle", headers=He, json={"gizli": False})
        br.close()
print("OK %d" % len(ok) if not bad else "HATA %d/%d" % (len(bad), len(ok) + len(bad)))
for n, tb in bad: print(n, tb)
os._exit(0)
