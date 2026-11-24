"""Satın alma sayfası tarayıcıda: form, doğrulama, havale, kart dönüşü, sonuç sayfası, mobil taşma, sahip Siparişler ekranı."""
import sys, os, threading, time, json
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import entg_probe, notify, satin_al
TK = []
POSTA = []
def gonder(cfg, channel, to, text, subject):
    if channel == "email": POSTA.append((to, text)); return "ok"
    return "x"
notify._dispatch = gonder
POSTA = []
SON = {"d": {"status": "success", "paymentStatus": "SUCCESS", "paidPrice": 0, "basketId": ""}}
class R:
    status_code = 200
    def __init__(s, j): s._j = j
    def json(s): return s._j
def istek(*a, **k):
    u = str(a[1] if len(a) > 1 else a[0]) + str(k.get("url", ""))
    if "initialize" in u: TK.append("T%d" % (len(TK) + 1)); return R({"status": "success", "token": TK[-1], "paymentPageUrl": "http://127.0.0.1:8772/__iyzico__", "checkoutFormContent": ""})
    if "detail" in u: return R(dict(SON["d"]))
    return R({"status": "success"})
entg_probe._istek = istek
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8771, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8771/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
SITE = os.path.join(os.path.dirname(__file__), "..", "site")
class H(BaseHTTPRequestHandler):
    def log_message(s, *a): pass
    def _px(s):
        n = int(s.headers.get("Content-Length") or 0); b = s.rfile.read(n) if n else None
        r = rq.request(s.command, "http://127.0.0.1:8771" + s.path, data=b, headers={k: v for k, v in s.headers.items() if k.lower() in ("content-type", "authorization")}, allow_redirects=False)
        s.send_response(r.status_code)
        for k in ("Content-Type", "Location"):
            if k in r.headers: s.send_header(k, r.headers[k])
        s.end_headers(); s.wfile.write(r.content)
    do_POST = do_PUT = do_DELETE = _px
    def do_GET(s):
        if s.path.startswith("/api/"): return s._px()
        p = s.path.split("?")[0]
        if p.startswith("/__iyzico__"): s.send_response(200); s.send_header("Content-Type", "text/html"); s.end_headers(); s.wfile.write(b"<h1>iyzico</h1>"); return
        f = os.path.join(SITE, p.lstrip("/") or "index.html")
        if not os.path.isfile(f): s.send_response(404); s.end_headers(); return
        ct = {"html": "text/html", "js": "application/javascript", "css": "text/css", "png": "image/png"}.get(f.rsplit(".", 1)[-1], "application/octet-stream")
        s.send_response(200); s.send_header("Content-Type", ct + "; charset=utf-8"); s.end_headers(); s.wfile.write(open(f, "rb").read())
GON = None
ps = ThreadingHTTPServer(("127.0.0.1", 8772), H); threading.Thread(target=ps.serve_forever, daemon=True).start()
U = "http://127.0.0.1:8772"; API = "http://127.0.0.1:8771/api"
tok = rq.post(API + "/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]; A = {"Authorization": "Bearer " + tok}
def kaydet(pid, keys): 
    r = rq.put(API + "/admin/baglanti/" + pid, json={"keys": keys, "on": True}, headers=A); assert r.status_code == 200, r.text
rq.put(API + "/admin/satis/ayar", json={"site_url": U, "unvan": "Test AŞ", "kdv": 20}, headers=A)
ok, bad = [], []
from playwright.sync_api import sync_playwright
def t(n):
    def d(f):
        try: f(); ok.append(n)
        except Exception as e:
            import traceback; bad.append(n); print("FAIL", n, "\n", traceback.format_exc()[-700:])
        return f
    return d
FORM = {"ad": "Ayşe Kaya", "firma": "Kaya Servis", "email": "ayse@kayaservis.com", "telefon": "05321112233", "vergi_dairesi": "Çankaya", "vergi_no": "1234567890", "il": "Ankara", "adres": "Atatürk Bulvarı No 5 Çankaya"}
def doldur(pg):
    for k, v in FORM.items():
        pg.fill('[name="%s"]' % k, v)
    pg.select_option("#sektor", index=1); pg.check("#kabul")
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = br.new_context(viewport={"width": 1360, "height": 900}); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    @t("hiç ödeme yöntemi yokken form kapalı ve açıklama gösterir")
    def _():
        pg.goto(U + "/satin-al.html"); pg.wait_for_selector("#ic:not([hidden])", timeout=8000)
        assert "Online ödeme şu an kapalı" in pg.inner_text("#yn"); assert pg.is_disabled("#go")
    kaydet("iyzico", {"api_key": "sandbox-abc", "secret_key": "sandbox-secret", "mod": "sandbox"}) if False else None
    import json as _j
    r = rq.get(API + "/admin/baglanti", headers=A).json()
    fl = [f["key"] for i in r["items"] if i["id"] == "iyzico" for f in i["fields"]]
    kaydet("iyzico", {k: ("sandbox" if k in ("mod", "ortam") else "x-" + k + "-1234") for k in fl})
    hv = [f["key"] for i in r["items"] if i["id"] == "havale" for f in i["fields"]]
    kaydet("havale", {k: ("TR330006100519786457841326" if k == "iban" else "Servis AŞ" if k == "unvan" else "Banka") for k in hv})
    @t("paketler gerçek fiyatla gelir, seçim özeti değiştirir, KDV hesaplanır")
    def _():
        pg.goto(U + "/satin-al.html?paket=profesyonel&sure=aylik"); pg.wait_for_selector("#pk label", timeout=8000)
        api = rq.get(API + "/public/satin-al/paketler").json(); p = [x for x in api["paketler"] if x["id"] == "profesyonel"][0]
        assert pg.is_checked("#pk-profesyonel") and pg.is_checked("#su-a")
        top = pg.inner_text("#o4").replace("\xa0", " ")
        assert ("%s" % int(p["aylik"]["toplam"])) in top.replace(".", ""), (top, p["aylik"]["toplam"])
        pg.click("label[for=su-y]"); y = pg.inner_text("#o4").replace(".", "").replace("\xa0", " ")
        assert str(int(p["yillik"]["toplam"])) in y, (y, p["yillik"]["toplam"])
        assert pg.inner_text("#okd") == "KDV %20"
    @t("eksik form gönderilmez, hata alanları işaretlenir")
    def _():
        pg.goto(U + "/satin-al.html"); pg.wait_for_selector("#pk label"); pg.click("#go"); pg.wait_for_timeout(300)
        assert pg.locator(".f.bad").count() >= 8 and "düzeltin" in pg.inner_text("#err")
        pg.fill("#email", "yanlis"); pg.fill("#vn", "123"); pg.click("#go"); assert pg.locator('[data-f="email"].bad').count() == 1 and pg.locator('[data-f="vergi_no"].bad').count() == 1
    @t("havale: sipariş açılır, IBAN ve sipariş no gösterilir, sonuç sayfası beklemeyi anlatır")
    def _():
        pg.goto(U + "/satin-al.html?paket=baslangic"); pg.wait_for_selector("#pk label"); doldur(pg)
        pg.check("input[name=yontem][value=havale]"); pg.click("#go"); pg.wait_for_selector("#hv.on", timeout=8000)
        tx = pg.inner_text("#hv"); assert "TR33" in tx and "OK-" in tx, tx
        pg.click("#hv a"); pg.wait_for_selector("#bs"); pg.wait_for_function("document.getElementById('bs').textContent.includes('Havale')", timeout=8000)
    @t("kart: iyzico sayfasına yönlenir; ödeme sonrası dönüş sonuç sayfasında firma, fatura ve giriş görünür")
    def _():
        POSTA.clear(); pg.goto(U + "/satin-al.html?paket=profesyonel&sure=yillik"); pg.wait_for_selector("#pk label")
        for k, v in FORM.items(): pg.fill('[name="%s"]' % k, v.replace("ayse@", "kart1@"))
        pg.select_option("#sektor", index=1); pg.check("#kabul"); pg.check("input[name=yontem][value=kart]")
        with pg.expect_navigation(url="**/__iyzico__*", timeout=10000): pg.click("#go")
        sip = pg.evaluate("JSON.parse(sessionStorage.getItem('ok_sip'))")
        o = rq.get(API + "/public/satin-al/durum", params=sip).json(); SON["d"].update(paidPrice=o["toplam"], basketId=o["no"])
        r = rq.post(API + "/public/satin-al/donus", data={"token": TK[-1]}, allow_redirects=False); assert r.status_code in (302, 303), r.status_code
        pg.goto(r.headers["Location"]); pg.wait_for_function("document.getElementById('bs').textContent.includes('hazır')", timeout=10000)
        tx = pg.inner_text("#ok"); assert "kart1@kayaservis.com" in tx and "OKSIP" not in tx and "OK" in tx
        assert pg.locator('a:has-text("Faturayı indir")').count() == 1
        pdf = rq.get(U + pg.get_attribute('a:has-text("Faturayı indir")', "href")); assert pdf.content[:4] == b"%PDF"
        assert POSTA, "giriş bilgisi e-postası gitmedi"
        pg.screenshot(path="/tmp/sa_sonuc.png")
    @t("reddedilen kart: sonuç sayfası başarısız der ve tekrar denemeyi sunar")
    def _():
        SON["d"].update(status="failure", paymentStatus="FAILURE")
        pg.goto(U + "/satin-al.html?paket=baslangic"); pg.wait_for_selector("#pk label")
        for k, v in FORM.items(): pg.fill('[name="%s"]' % k, v.replace("ayse@", "red@"))
        pg.select_option("#sektor", index=1); pg.check("#kabul"); pg.check("input[name=yontem][value=kart]")
        with pg.expect_navigation(url="**/__iyzico__*", timeout=10000): pg.click("#go")
        r = rq.post(API + "/public/satin-al/donus", data={"token": TK[-1]}, allow_redirects=False); pg.goto(r.headers["Location"])
        pg.wait_for_function("document.getElementById('bs').textContent.includes('tamamlanamadı')", timeout=10000); assert pg.locator('a:has-text("Tekrar dene")').count() == 1
        SON["d"].update(status="success", paymentStatus="SUCCESS")
    @t("sonuç sayfası geçersiz bağlantıda sipariş bulunamadı der")
    def _():
        pg.goto(U + "/satin-al-sonuc.html?no=OK-2026-999999&k=yanlis"); pg.wait_for_function("document.getElementById('bs').textContent.includes('bulunamadı')", timeout=8000)
    for w in (390, 360):
        @t("mobilde yatay taşma yok (%d px) ve sabit alt çubuk görünür" % w)
        def _(w=w):
            m = br.new_context(viewport={"width": w, "height": 800}).new_page()
            m.goto(U + "/satin-al.html"); m.wait_for_selector("#pk label"); m.wait_for_timeout(300)
            sw = m.evaluate("document.documentElement.scrollWidth"); assert sw <= w, sw
            assert m.is_visible(".bar") and m.evaluate("getComputedStyle(document.querySelector('.bar')).position") == "fixed"
            m.screenshot(path="/tmp/sa_mobil_%d.png" % w, full_page=True)
    @t("sahip paneli Siparişler: liste, havale onayı ve ayar kaydı")
    def _():
        a = ctx.new_page(); a.goto(U.replace("8772", "8771") + "/yonetim"); a.wait_for_timeout(1200)
        a.fill("#le", "admin@servis.com"); a.fill("#lp", "admin123"); a.click("form button[type=submit]"); a.wait_for_timeout(2500)
        a.evaluate("location.hash='#siparis'"); a.wait_for_selector("table tr", timeout=8000)
        tx = a.inner_text("body"); assert "kayaservis.com" in tx and "Havale bekleniyor" in tx and "Tamamlandı" in tx, tx[:300]
        a.screenshot(path="/tmp/sa_siparis.png", full_page=True)
        a.click("tr:has-text('Havale bekleniyor') button:has-text('Aç')"); a.wait_for_selector(".mdl"); a.once("dialog", lambda d: d.accept())
        a.click("[data-a=havale]"); a.wait_for_timeout(2500)
        assert "Havale bekleniyor" not in a.inner_text("table") or a.inner_text("table").count("Havale bekleniyor") == 0
        a.click("button:has-text('Satış ayarları')"); a.wait_for_selector(".mdl"); a.fill("#m_kdv", "10"); a.click("[data-ok]"); a.wait_for_timeout(800)
        assert rq.get(API + "/admin/satis/ayar", headers=A).json()["kdv"] == 10
    @t("sayfa hatası yok")
    def _(): assert not errs, errs
print("OK", len(ok)); 
if bad: print("BAŞARISIZ", bad); sys.exit(1)
