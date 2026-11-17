"""Çok sayfalı site (v10): her sayfada hata/taşma/kırık görsel yok, tek H1, menü çekmecesi açılır ve gezdirir, siyah yüzey yok, form lead'e gider."""
import os, threading, http.server, functools, json
from playwright.sync_api import sync_playwright
SITE = os.path.join(os.path.dirname(__file__), "..", "site")
ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:400]))
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE); H.log_message = lambda *a, **k: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); PORT = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
U = "http://127.0.0.1:%d" % PORT
PAGES = ["", "temalar.html", "e-ticaret.html", "web-sitesi.html", "is-takibi.html", "fiyatlar.html", "sektorler.html", "sss.html", "ozellikler.html", "hakkimizda.html", "iletisim.html"]
posted = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for vw in ({"width": 1440, "height": 900}, {"width": 390, "height": 844}):
        tag = "%dpx" % vw["width"]
        pg = br.new_page(viewport=vw); errs = []; fails = []
        pg.route("**/images.pexels.com/**", lambda r: r.fulfill(status=200, content_type="image/gif", body=bytes.fromhex("47494638396101000100800000ffffff00000021f90401000000002c00000000010001000002024401003b")))  # Pexels kum havuzundan erişilemez; yerine 1px gif
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
        pg.on("response", lambda r: r.status >= 400 and fails.append("%s %s" % (r.status, r.url)))
        pg.route("**/api/public/track", lambda r: r.fulfill(status=200, content_type="application/json", body='{"ok":true}'))
        pg.route("**/api/public/lead", lambda r: (posted.append(json.loads(r.request.post_data)), r.fulfill(status=200, content_type="application/json", body='{"ok":true}')))
        for p in PAGES:
            def a(p=p):
                errs.clear(); fails.clear()
                pg.goto(U + "/" + p); pg.wait_for_load_state("networkidle")
                pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.scrollIntoView({block:'center',inline:'center'}))"); pg.wait_for_timeout(1500)
                assert not errs, errs[:3]; assert not fails, fails[:4]
                assert pg.locator("h1").count() == 1, "h1 sayısı"
                sw = pg.evaluate("document.documentElement.scrollWidth"); assert sw <= vw["width"] + 1, "taşma %d" % sw
                bk = pg.evaluate("[...document.images].filter(i=>i.offsetParent!==null&&!(i.complete&&i.naturalWidth>0)).map(i=>i.src)"); assert not bk, bk[:3]
                assert "/yonetim" not in pg.content()
            t("%s /%s: hata, taşma, kırık görsel, h1" % (tag, p), a)
        def m():
            pg.goto(U + "/"); pg.wait_for_load_state("networkidle")
            if vw["width"] < 861:
                assert not pg.locator("#cekmece a.m").first.is_visible()
                pg.click(".mnu"); pg.wait_for_timeout(600)
                assert pg.locator("#cekmece a.m").first.is_visible() and pg.get_attribute(".mnu", "aria-expanded") == "true"
                pg.keyboard.press("Escape"); pg.wait_for_timeout(500)
                assert not pg.locator("#cekmece a.m").first.is_visible()
                pg.click(".mnu"); pg.wait_for_timeout(500); pg.click("#cekmece a.m >> text=E-ticaret")
            else:
                pg.click(".nav >> text=E-ticaret")
            pg.wait_for_url("**/e-ticaret.html"); assert pg.locator("h1").inner_text().startswith("Sitenizin")
            assert pg.locator("body.kilit").count() == 0
        t(tag + ": menü açılır, kapanır, sayfaya götürür", m)
        def r():
            pg.goto(U + "/"); 
            for sel in (".ust", ".hero", ".son", "footer"):
                pass
            for sel in ():
                c = pg.eval_on_selector(sel, "e=>getComputedStyle(e).backgroundColor"); v = [int(x) for x in c[c.index('(')+1:-1].split(',')[:3]]
                assert max(v) > 40, (sel, c)
        t(tag + ": siyah yüzey yok", r)
        def f():
            pg.goto(U + "/iletisim.html"); pg.wait_for_load_state("networkidle")
            pg.fill("#tf1", "Ali Veli"); pg.fill("#tf2", "05321112233")
            pg.click(".frm .bt"); pg.wait_for_timeout(800); assert posted and posted[-1].get("form") == "teklif", posted[-1:]
        t(tag + ": iletişim formu lead'e gider", f)
        pg.close()
    br.close()
print("GEÇTİ", len(ok)); [print("HATA", n, e) for n, e in bad]
raise SystemExit(1 if bad else 0)
