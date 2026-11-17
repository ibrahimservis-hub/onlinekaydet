"""Sahip paneli: talepler, firmaya gir (müşteri paneli + takvim), ziyaretçiler, muhasebe, firma web sitesi sekmesi."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8769, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8769/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8769"; B = U + "/api"
assert rq.post(B + "/public/demo", json={"name": "Ahmet Yılmaz", "phone": "05321112233", "sector": "kuafor"}).status_code == 200
rq.post(B + "/public/lead", json={"name": "Veli", "phone": "05328887766", "form": "sikayet-ve-oneri", "extra": {"mesaj": "Servis geç geldi"}})
rq.post(B + "/public/track", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/120"}, json={"sid": "ziyaret12345", "event": "pageview", "path": "/e-ticaret.html", "referrer": "https://www.google.com/", "host": "onlinekaydet.com", "search": "?utm_source=google&utm_medium=cpc"})
from playwright.sync_api import sync_playwright
bad = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = br.new_context(viewport={"width": 1360, "height": 900}); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(U + "/yonetim"); pg.wait_for_timeout(1200)
    pg.fill("#le", "admin@servis.com"); pg.fill("#lp", "admin123"); pg.click("form button[type=submit]"); pg.wait_for_timeout(2500)
    def go(h, txt):
        pg.evaluate("location.hash='#%s'" % h); pg.wait_for_timeout(1500)
        assert txt in pg.inner_text("body"), (h, pg.inner_text("body")[:300])
    try:
        go("talepler", "Demo talebi")
        assert "Şikayet / öneri" in pg.inner_text("body") and "Servis geç geldi" in pg.inner_text("body")
        pg.locator("select:has(option:text-is(\"Tüm formlar\"))").select_option(label="Şikayet / öneri (1)"); pg.wait_for_timeout(1200)
        assert "Veli" in pg.inner_text("body") and "Ahmet" not in pg.inner_text("body")
        pg.locator("select:has(option:text-is(\"Tüm formlar\"))").select_option(label="Tüm formlar"); pg.wait_for_timeout(1200)
        # not ekle
        pg.locator("button:has-text('Not')").first.click(); pg.fill("#m_t", "Pazartesi aranacak"); pg.click("[data-ok]"); pg.wait_for_timeout(1200)
        assert "Pazartesi aranacak" in pg.inner_text("body")
        pg.locator("button:has-text('Düzenle')").first.click(); pg.fill("#m_firm", "Veli Berber"); pg.click("[data-ok]"); pg.wait_for_timeout(1200)
        assert "Veli Berber" in pg.inner_text("body")
        pg.screenshot(path="/tmp/sh_talepler.png")
        # firmaya gir -> müşteri paneli, takvim
        with ctx.expect_page() as np_:
            pg.locator("button:has-text('Firmaya gir')").first.click()
        p2 = np_.value; p2.wait_for_timeout(4000)
        assert "/salon" in p2.url and "takvim" in p2.url, p2.url
        assert "Takvim" in p2.inner_text("body"), p2.inner_text("body")[:300]
        p2.screenshot(path="/tmp/sh_firma_takvim.png")
        for h, tx in (("randevu", "Randevu"), ("musteri", "Müşteri"), ("kasa", "Kasa")):
            p2.evaluate("location.hash='#%s'" % h); p2.wait_for_timeout(1500); assert tx in p2.inner_text("body"), (h, p2.inner_text("body")[:200])
        p2.evaluate("location.hash='#site'"); p2.wait_for_timeout(2000); assert len(p2.inner_text("#main")) > 80, p2.inner_text("#main")
        p2.screenshot(path="/tmp/sh_firma_site.png")
        # silme
        pg.bring_to_front(); pg.on("dialog", lambda d: d.accept())
        n0 = pg.locator("tr:has(td input[data-id])").count(); pg.locator("button:has-text('Sil')").last.click(); pg.wait_for_timeout(1500)
        assert pg.locator("tr:has(td input[data-id])").count() == n0 - 1
        go("ziyaret", "Şu an sitede"); assert "Google Ads" in pg.inner_text("body") or "Reklam" in pg.inner_text("body"), pg.inner_text("body")[:600]
        assert "/e-ticaret.html" in pg.inner_text("body"); pg.screenshot(path="/tmp/sh_ziyaret.png")
        go("muhasebe", "Platformun kendi gelir ve giderleri")
        pg.fill("#mh_a", "250,50"); pg.fill("#mh_x", "Alan adı yenileme"); pg.click("button:has-text('Kaydet')"); pg.wait_for_timeout(1300)
        assert "Alan adı yenileme" in pg.inner_text("body") and "250,5" in pg.inner_text("body"); pg.screenshot(path="/tmp/sh_muh.png")
        fid = rq.get(B + "/admin/firms", headers={"Authorization": "Bearer " + pg.evaluate("localStorage.getItem('token')||sessionStorage.getItem('ok_t')||''")}).json()
        go("firmalar", "Demo")
        assert not errs, errs
    except Exception as e:
        import traceback; bad.append(traceback.format_exc()[-900:]); pg.screenshot(path="/tmp/sh_err.png")
    br.close()
print("GEÇTİ" if not bad else "BAŞARISIZ\n" + bad[0]); os._exit(1 if bad else 0)
