"""Web Sitem: bilgi sekmesi 4 ayrı bölüm; kayan fotoğraf sırası ◀ ▶ ile değişiyor ve kaydediliyor."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n); print("  ✓", n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:])); print("  ✗", n); print(bad[-1][1][-400:])
with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    r = c.post("/api/admin/firms", headers=A, json={"name": "Site Duzen", "email": "sd@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "sd@x.com", "password": "sifre12345"}).json()["token"]}
    c.post("/api/yp/sectors/kuafor", headers=H, json={})
    import io, base64
    from PIL import Image
    def img(col):
        b = io.BytesIO(); Image.new("RGB", (64, 48), col).save(b, "JPEG"); return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
    ks = []
    for col in ("red", "green", "blue"):
        r = c.post("/api/site/image", headers=H, json={"data": img(col), "kind": "slides"}); assert r.status_code == 200, r.text; ks.append(r.json()["k"])
    pr = c.get("/api/site/profile", headers=H).json()["profile"]; pr["slides"] = [{"k": k} for k in ks]
    assert c.put("/api/site/profile", headers=H, json=pr).status_code == 200
    import uvicorn
    from playwright.sync_api import sync_playwright
    port = socket.socket(); port.bind(("127.0.0.1", 0)); P = port.getsockname()[1]; port.close()
    srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=P, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start(); time.sleep(2)
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = br.new_page(viewport={"width": 1280, "height": 1000}); errs = []; pg.on("pageerror", lambda x: errs.append(str(x)[:160]))
        pg.goto("http://127.0.0.1:%d/salon" % P); pg.wait_for_selector("#lf")
        pg.fill("#lf input[name=email]", "sd@x.com"); pg.fill("#lf input[name=password]", "sifre12345"); pg.click("#lb")
        pg.wait_for_selector("#app:not([hidden])"); pg.wait_for_timeout(1200)
        pg.evaluate("location.hash='#site'"); pg.wait_for_selector("[data-a=sitetab]", timeout=15000)
        pg.click("[data-a=sitetab][data-t=bilgi]"); pg.wait_for_selector(".bsec", timeout=8000)
        def a(): assert len(pg.query_selector_all(".bsec")) == 4 and not errs, errs
        t("bilgi sekmesi dört ayrı bölüm", a)
        pg.screenshot(path="/tmp/sd_bilgi.png")
        pg.click("[data-a=sitetab][data-t=gorsel]"); pg.wait_for_selector(".ph .it[data-dk=slides]", timeout=8000)
        def b(): assert len(pg.query_selector_all(".ph .it[data-dk=slides]")) == 3
        t("üç fotoğraf sıralanabilir kartta", b)
        pg.screenshot(path="/tmp/sd_gorsel.png")
        pg.click(".ph .it[data-dk=slides][data-di='0'] [data-a=phmv][data-d='1']"); pg.wait_for_timeout(1500)
        def d():
            got = [x["k"] for x in c.get("/api/site/profile", headers=H).json()["profile"]["slides"]]
            assert got == [ks[1], ks[0], ks[2]], got
        t("▶ ile sıra değişti ve kaydedildi", d)
        pg.click("[data-a=sitetab][data-t=yasal]"); pg.wait_for_selector("[data-a=ys-duzenle]", timeout=8000)
        def e(): assert len(pg.query_selector_all("[data-a=ys-duzenle]")) >= 5 and pg.query_selector("#ysb input[name=seller_title]").input_value() == "Site Duzen"
        t("yasal sekmesi: metinler ve otomatik firma unvanı", e)
        pg.screenshot(path="/tmp/sd_yasal.png")
        pg.click("[data-a=ys-duzenle][data-s=gizlilik-kvkk]"); pg.wait_for_selector("#ysed")
        pg.evaluate("document.getElementById('ysed').innerHTML+='<p>Özel eklenen paragraf: verileriniz yalnızca bizde kalır ve üçüncü kişilerle paylaşılmaz.</p>'")
        pg.click("[data-a=ys-kaydet]"); pg.wait_for_timeout(1500)
        def f():
            d = [x for x in c.get("/api/yp/yasal", headers=H).json()["docs"] if x["slug"] == "gizlilik-kvkk"][0]
            assert d["custom"] and "Özel eklenen paragraf" in d["html"] and not errs, errs
        t("metin ekranda düzenlenip kaydedildi", f)
        br.close()
print("OK %d" % len(ok) if not bad else "HATA %d/%d" % (len(bad), len(ok) + len(bad)))
os._exit(0)
