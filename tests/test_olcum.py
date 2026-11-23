# -*- coding: utf-8 -*-
"""Ölçüm etiketleri: GTM/GA4/Ads/Pixel enjeksiyonu, çerez onayı, mağaza dataLayer olayları."""
import os, sys, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq, demo
demo.GUNLUK_LIMIT = 10**6
PORT = 8796
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
U = "http://127.0.0.1:%d/api" % PORT
for _ in range(100):
    try:
        if rq.get(U + "/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(.2)
d = rq.post(U + "/public/demo", json={"name": "Olcum Test", "phone": "05531000777", "sector": "eticaret"}).json()
tok = rq.post(U + "/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]
H = {"Authorization": "Bearer " + tok}
ok = fail = 0
def chk(c, m):
    global ok, fail
    if c: ok += 1
    else: fail += 1; print("FAIL", m)
def call(m, p, **kw): return rq.request(m, U + p, headers=H, **kw)
print("fid", repr(_c_fid) if False else "")
import jwt as _jwt
_c = _jwt.decode(tok, options={"verify_signature": False}); print("jwt firm=", _c.get("firm"))
fid = str(_c.get("firm")).rsplit("_f_", 1)[-1]
site = lambda p: rq.get("http://127.0.0.1:%d/demo/%s~/%s" % (PORT, fid, p.lstrip("/")))

# kimlik doğrulama
chk(call("PUT", "/yp/integrations/ga4", json={"keys": {"id": "yanlis"}}).json().get("ok") is False, "ga4 biçim")
chk(call("PUT", "/yp/integrations/gtm", json={"keys": {"id": "GTM-ABCD123"}}).json().get("ok") is True, "gtm kaydet")
chk(call("PUT", "/yp/integrations/ga4", json={"keys": {"id": "G-TEST123456"}}).json().get("ok") is True, "ga4 kaydet")
chk(call("PUT", "/yp/integrations/google_ads", json={"keys": {"id": "AW-123456789", "label": "abcDEF123"}}).json().get("ok") is True, "ads kaydet")
chk(call("PUT", "/yp/integrations/meta_pixel", json={"keys": {"id": "123456789012345"}}).json().get("ok") is True, "pixel kaydet")
chk(call("PUT", "/yp/integrations/tiktok_pixel", json={"keys": {"id": "123456789"}}).json().get("ok") is True, "tiktok kaydet")
chk(call("PUT", "/yp/integrations/search_console", json={"keys": {"id": "abc_DEF-123"}}).json().get("ok") is True, "gsc kaydet")

r = site("index.html")
chk(r.status_code == 200, "ana sayfa %s" % r.status_code)
h = r.text
chk('id="okolc"' in h, "ana sayfada etiket betiği")
chk('"gtm": "GTM-ABCD123"' in h and '"ga4": "G-TEST123456"' in h, "kimlikler betikte")
chk('"ads": "AW-123456789"' in h and '"adl": "abcDEF123"' in h, "ads kimliği ve etiketi")
chk('name="google-site-verification" content="abc_DEF-123"' in h, "search console doğrulama")
chk("googletagmanager.com/ns.html?id=GTM-ABCD123" in h, "gtm noscript")
chk(h.count('id="okolc"') == 1, "tek sefer")

# GTM varken GA4 ayrıca yüklenmez (kod yolunda gtm önce gelir)
chk("if(T.gtm){dataLayer.push({'gtm.start'" in h, "gtm öncelikli")

# kapalı entegrasyon basılmaz
call("PUT", "/yp/integrations/meta_pixel", json={"keys": {"id": "123456789012345"}, "on": False})
h2 = site("index.html").text
chk('"fb"' not in h2, "kapalı pixel basılmaz")

# mağaza: tarayıcıda olaylar
from playwright.sync_api import sync_playwright
call("POST", "/yp/products", json={"name": "Olay Ürünü", "price": 250, "cost": 100, "stock": 9, "channels": {"site": True}})
call("PUT", "/yp/integrations/meta_pixel", json={"keys": {"id": "123456789012345"}, "on": True})
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("**/googletagmanager.com/**", lambda r: r.abort())
    pg.route("**/connect.facebook.net/**", lambda r: r.abort())
    pg.route("**/analytics.tiktok.com/**", lambda r: r.abort())
    pg.goto("http://127.0.0.1:%d/demo/%s~/magaza" % (PORT, fid))
    pg.wait_for_timeout(2500); 0 and print("BODY", pg.inner_text("body")[:300].replace("\n"," | ")); pg.wait_for_selector(".pc", timeout=8000)
    ev = lambda: pg.evaluate("(window.dataLayer||[]).filter(x=>x&&x.event&&x.event!=='gtm.js').map(x=>x.event)")
    chk("view_item_list" in ev(), "view_item_list %s" % ev())
    chk(pg.evaluate("typeof okTrack") == "function", "okTrack tanımlı")
    pg.click(".pc button[data-a]"); pg.wait_for_timeout(500)
    evs = pg.evaluate("(window.dataLayer||[]).filter(x=>x&&x.event==='add_to_cart')")
    chk(evs and evs[-1]["ecommerce"]["items"][0]["quantity"] == 1 and evs[-1]["ecommerce"]["value"] > 0, "add_to_cart olayı %s" % evs)
    pg.click(".pc a.im"); pg.wait_for_timeout(1200)
    chk("view_item" in ev() or pg.evaluate("location.pathname").startswith("/demo"), "ürün sayfası")
    chk(pg.evaluate("typeof fbq") == "function", "meta pixel yüklendi (onay bandı kapalı)")
    chk(not errs, "sayfa hatası %s" % errs[:2])
    # çerez bandı açık: onay gelene kadar reklam/ölçüm betiği yüklenmez, onaydan sonra yüklenir; bekleyen olaylar iletilir
    call("PUT", "/yp/cerez", json={"on": True})
    pg2 = b.new_page()
    pg2.route("**/googletagmanager.com/**", lambda r: r.abort()); pg2.route("**/connect.facebook.net/**", lambda r: r.abort()); pg2.route("**/analytics.tiktok.com/**", lambda r: r.abort())
    pg2.goto("http://127.0.0.1:%d/demo/%s~/magaza" % (PORT, fid)); pg2.wait_for_selector(".pc", timeout=15000); pg2.wait_for_timeout(500)
    chk(pg2.evaluate("typeof fbq") == "undefined", "onaysız pixel yüklenmedi")
    chk(pg2.evaluate("(window.dataLayer||[]).filter(x=>x&&x.event==='gtm.js').length") == 0, "onaysız gtm yüklenmedi")
    pg2.click("[data-ok-cerez=kabul]"); pg2.wait_for_timeout(500)
    chk(pg2.evaluate("typeof fbq") == "function", "onaydan sonra pixel yüklendi")
    chk(pg2.evaluate("(window.dataLayer||[]).filter(x=>x&&x.event==='view_item_list').length") >= 1, "bekleyen olay onaydan sonra iletildi")
    b.close()
print("OK", ok, "FAIL", fail)
sys.exit(1 if fail else 0)
