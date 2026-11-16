"""Yeni ana sayfa (site/index.html, v9): hata yok, görseller yüklenir, taşma yok, form lead'e gider, SSS ve tema filtresi çalışır, SEO etiketleri var."""
import sys, os, threading, http.server, functools, json, re
from playwright.sync_api import sync_playwright
SITE = os.path.join(os.path.dirname(__file__), "..", "site")
ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:500]))
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE); H.log_message = lambda *a, **k: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); PORT = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
U = "http://127.0.0.1:%d/" % PORT
posted = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for vw in ({"width": 1440, "height": 900}, {"width": 390, "height": 844}):
        tag = "%dpx" % vw["width"]
        pg = br.new_page(viewport=vw); errs = []; fails = []
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
        pg.on("response", lambda r: r.status >= 400 and fails.append("%s %s" % (r.status, r.url)))
        def lead(route):
            posted.append(json.loads(route.request.post_data)); route.fulfill(status=200, content_type="application/json", body='{"ok":true}')
        pg.route("**/api/public/lead", lead)
        pg.goto(U); pg.wait_for_load_state("networkidle")
        def a(): assert not errs, errs[:3]; assert not fails, fails[:5]
        t(tag + ": konsol ve ağ hatası yok", a)
        def b():
            assert pg.evaluate("document.documentElement.scrollWidth") <= vw["width"] + 1, pg.evaluate("document.documentElement.scrollWidth")
            pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(300)
            pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.scrollIntoView())"); pg.wait_for_timeout(1500)
            br_ = pg.evaluate("[...document.images].filter(i=>i.offsetParent!==null&&!(i.complete&&i.naturalWidth>0)).map(i=>i.src)"); assert not br_, br_[:3]
        t(tag + ": yatay taşma ve kırık görsel yok", b)
        def c():
            assert pg.locator("h1").count() == 1 and "mağazanız" in pg.inner_text("h1")
            assert pg.locator("link[rel=canonical]").get_attribute("href") == "https://onlinekaydet.com/"
            lds = json.loads(pg.eval_on_selector("script[type='application/ld+json']", "e=>e.textContent"))
            types = [x["@type"] for x in lds]; assert types == ["Organization", "WebSite", "SoftwareApplication", "FAQPage"], types
            assert len(lds[3]["mainEntity"]) >= 6 and all(q["acceptedAnswer"]["text"] for q in lds[3]["mainEntity"])
            body = pg.content(); assert "/yonetim" not in body, "yönetim paneli bağlantısı sızmış"; assert 'href="/uye-girisi"' in body
        t(tag + ": h1, canonical, JSON-LD, yönetim bağlantısı yok", c)
        def d():
            pg.evaluate("document.querySelector('#teklif').scrollIntoView()"); pg.wait_for_timeout(300)
            pg.fill("#tf1", "Ali Veli"); pg.fill("#tf2", "0532 555 11 22"); pg.fill("#tf3", "Veli Ltd."); pg.select_option("#tf4", "Teknik servis")
            pg.click("#teklif-form button.bt"); pg.wait_for_selector("text=Talebiniz alındı", timeout=5000)
            p = posted[-1]; assert p["name"] == "Ali Veli" and p["phone"] and p["firm"] == "Veli Ltd." and p["sector"] == "Teknik servis" and p["form"] == "teklif", p
        t(tag + ": teklif formu lead'e gider", d)
        def e():
            q = pg.locator(".q").nth(1); q.click(); assert "ac" in q.get_attribute("class"); q.click(); assert "ac" not in q.get_attribute("class")
            pg.locator(".flt button").nth(1).click(); pg.wait_for_timeout(200)
            assert pg.locator(".tkg .tk:not([hidden])").count() > 0
        t(tag + ": SSS açılır, tema filtresi çalışır", e)
        pg.close()
    br.close()
for n in ok: print("  ✓", n)
for n, e in bad: print("  ✗", n, e)
print("OK", len(ok), "FAIL", len(bad)); sys.exit(1 if bad else 0)
