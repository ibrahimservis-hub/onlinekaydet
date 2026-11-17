"""/salon: süre dolunca tam ekran 'Kullanım süreniz doldu' görünür."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq, asyncio, firms
from datetime import datetime, timezone, timedelta
s = boot.server
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=8772, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8772/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8772"
d = rq.post(U + "/api/public/demo", json={"name": "UI Sure", "phone": "05327770022", "sector": "kuafor"}).json()
tok = rq.post(U + "/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]
from playwright.sync_api import sync_playwright
bad = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 390, "height": 800})
    pg.goto(U + "/giris"); pg.evaluate("t=>{localStorage.setItem('token',t);localStorage.setItem('ypt',t)}", tok)
    pg.goto(U + "/salon#bugun"); pg.wait_for_timeout(2500)
    if pg.is_visible("#sureDoldu"): bad.append("süre dolmadan overlay çıktı")
    async def exp():
        await s.db.main().firms.update_many({"demo": True}, {"$set": {"expires_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()}}); firms._ACC.clear()
    th = threading.Thread(target=lambda: asyncio.run(exp())); th.start(); th.join()
    pg.reload(); pg.wait_for_timeout(2500)
    if not pg.is_visible("#sureDoldu") or "süreniz doldu" not in pg.inner_text("#sureDoldu"): bad.append("overlay yok: " + pg.inner_text("body")[:100])
    pg.screenshot(path="/tmp/sure_doldu.png"); br.close()
print("GEÇTİ" if not bad else "BAŞARISIZ %s" % bad); os._exit(1 if bad else 0)
