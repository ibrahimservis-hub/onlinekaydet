"""Siteden demo talebi: hesap açılıyor, 'Panele gir' ile ekranlar açılıyor mu (sektör başına)."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8771, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8771/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8771"
from playwright.sync_api import sync_playwright
secs = sys.argv[1:] or ["kuafor", "kombi", "klima"]
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for i, sec in enumerate(secs):
        r = rq.post(U + "/api/public/demo", json={"name": "Test Kişi", "phone": "0532%07d" % (1000000 + i), "sector": sec}, headers={"X-Forwarded-For": "10.0.0.%d" % (i + 1)})
        if r.status_code != 200: print(sec, "DEMO HATA", r.status_code, r.text[:150]); continue
        d = r.json(); tok = rq.post(U + "/api/auth/login", json={"email": d["email"], "password": d["password"]}).json().get("token")
        pg = br.new_context(viewport={"width": 1300, "height": 850}).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:150])); pg.on("response", lambda x: x.status >= 400 and "/api/" in x.url and errs.append("%s %s" % (x.status, x.url.split("/api/")[1][:60])))
        pg.goto(U + "/giris"); pg.evaluate("t=>{localStorage.setItem('token',t);localStorage.setItem('ypt',t);localStorage.removeItem('spx_firm')}", tok)
        print(sec, "panel:", d.get("panel"))
        if d.get("panel") != "/salon": pg.context.close(); continue
        pg.goto(U + "/salon#bugun"); pg.wait_for_timeout(2500)
        navs = pg.evaluate("Object.keys(V)")
        bad = []
        for v in navs:
            errs.clear(); pg.evaluate("v=>{location.hash='#'+v}", v); pg.wait_for_timeout(900)
            t = pg.inner_text("body")
            if errs or len(t) < 120 or "Hata" in t[:400]: bad.append((v, errs[:2]))
        print("  ekran", len(navs), "| sorunlu:", bad)
        pg.screenshot(path="/tmp/demo_%s.png" % sec)
        pg.context.close()
    br.close()
os._exit(0)
