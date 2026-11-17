"""/yonetim: tüm ekranlar ve tüm firma sekmeleri hatasız açılıyor mu."""
import sys, os, threading, time, re
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8770, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8770/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8770"
src = open(os.path.join(os.path.dirname(__file__), "..", "panel/sahip/src.html"), encoding="utf-8").read()
navs = re.findall(r'\["([^"]+)","[a-z]+","([a-z]+)"\]', re.search(r"const NAV=(.*?);\n", src).group(1))
tabs = re.findall(r'\["([a-z]+)","([^"]+)"\]', re.search(r"const TABS=(.*?);\n", src).group(1))
from playwright.sync_api import sync_playwright
bad = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_context(viewport={"width": 1360, "height": 900}).new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160])); pg.on("console", lambda m: m.type == "error" and "403" not in m.text and errs.append(m.text[:160]))
    pg.goto(U + "/yonetim"); pg.wait_for_timeout(1200)
    pg.fill("#le", "admin@servis.com"); pg.fill("#lp", "admin123"); pg.click("form button[type=submit]"); pg.wait_for_timeout(2500)
    for _, h in navs:
        errs.clear(); pg.evaluate("location.hash='#%s'" % h); pg.wait_for_timeout(1200)
        t = pg.inner_text("body")
        if errs or len(t) < 80 or "Beklenmeyen" in t: bad.append((h, errs[:2], t[:80]))
    pg.evaluate("api('/admin/firms',{method:'POST',body:{name:'Tarama Kuaför',email:'tarama@test.com',password:'Tarama12345',sector:'kuafor',package:'',usage_days:14}})"); pg.wait_for_timeout(2500)
    ids = pg.evaluate("api('/admin/firms').then(d=>d.firms.map(f=>f.id))")
    print("ekran", len(navs), "firma", len(ids or []), "sekme", len(tabs))
    for fid in (ids or [])[:1]:
        for k, _ in tabs:
            errs.clear(); pg.evaluate("location.hash='#firma/%s/%s'" % (fid, k)); pg.wait_for_timeout(2200)
            t = pg.inner_text("body")
            if errs or "Tarama Kuaför" not in t: bad.append((k, errs[:2], t[:80]))
    # örnek randevu
    pg.evaluate("location.hash='#firma/%s'" % ids[0]); pg.wait_for_timeout(1800)
    pg.locator("button:has-text('Örnek randevu ekle')").click(); pg.wait_for_timeout(2500)
    n = pg.evaluate("fapi('%s','/yp/boot').then(b=>fapi('%s','/yp/appts?a='+b.today+'&b='+b.today)).then(r=>r.rows.length)" % (ids[0], ids[0]))
    print("örnek randevu", n, "| toast:", pg.inner_text("body")[-120:].replace("\n"," "))
    # kurulum adımlarında not ekle / sil
    pg.evaluate("location.hash='#kurulum'"); pg.wait_for_timeout(1500)
    pg.locator("details summary").first.click(); pg.locator("button:has-text('Not ekle')").first.click(); pg.fill("#m_t", "Logo bekleniyor"); pg.click("[data-ok]"); pg.wait_for_timeout(1500)
    pg.locator("details summary").first.click(); pg.wait_for_timeout(300)
    if "Logo bekleniyor" not in pg.inner_text("body"): bad.append("not eklenmedi")
    pg.locator("details button:has-text('Sil')").first.click(); pg.wait_for_timeout(1500)
    pg.locator("details summary").first.click(); pg.wait_for_timeout(300)
    if "Logo bekleniyor" in pg.inner_text("body"): bad.append("not silinmedi")
    br.close()
print("HATA" if bad else "GEÇTİ", bad)
