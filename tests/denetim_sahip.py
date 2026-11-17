"""Sahip paneli (/yonetim): tüm menü ekranları masaüstü ve mobil; JS hatası, 4xx/5xx, taşma."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
import demo; demo.GUNLUK_LIMIT = 10 ** 6
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8802, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8802/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8802"; B = U + "/api"
for i in range(3): rq.post(B + "/public/demo", json={"name": "Demo Firma %d" % i, "phone": "05337770%03d" % i, "sector": ["kombi", "kuafor", "lokanta"][i]})
from playwright.sync_api import sync_playwright
rep = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for tag, vp, mob in (("masaüstü", {"width": 1440, "height": 900}, False), ("mobil", {"width": 390, "height": 800}, True)):
        ctx = br.new_context(viewport=vp, is_mobile=mob, has_touch=mob); pg = ctx.new_page(); errs, bad = [], []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.on("response", lambda r: bad.append("%s %s" % (r.status, r.url.replace(U, "")[:70])) if r.status >= 400 and "/api/" in r.url and "/auth/me" not in r.url else None)
        pg.goto(U + "/yonetim"); pg.wait_for_selector("#le", timeout=15000); pg.fill("#le", "admin@servis.com"); pg.fill("#lp", "admin123"); pg.keyboard.press("Enter"); pg.wait_for_timeout(2500)
        ids = pg.evaluate("NAV.filter(x=>x[0]!=='g').map(x=>x[2])")
        for r in ids:
            errs.clear(); bad.clear(); pg.evaluate("go('%s')" % r) if pg.evaluate("typeof go==='function'") else pg.evaluate("location.hash='#%s'" % r); pg.wait_for_timeout(1800)
            m = pg.evaluate("({sw:document.documentElement.scrollWidth,iw:innerWidth,t:(document.body.innerText||'').length,l:(document.body.innerText||'').indexOf('Yükleniyor')>-1})")
            pr = []
            if m["sw"] > m["iw"] + 2: pr.append("yatay taşma %d>%d" % (m["sw"], m["iw"]))
            if m["t"] < 40: pr.append("boş")
            if errs: pr.append("JS: " + errs[0])
            if bad: pr.append("API: " + ", ".join(sorted(set(bad))[:3]))
            if pr: rep.append((tag, r, " | ".join(pr))); 
            if pr and "taşma" in " ".join(pr): pg.screenshot(path="/tmp/mob/sahip-%s-%s.png" % (tag, r))
        print(tag, "ekran", len(ids), flush=True); ctx.close()
    br.close()
for x in rep: print("SORUN", *x)
print("TOPLAM", len(rep))
