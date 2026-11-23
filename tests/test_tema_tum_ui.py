"""Tarayıcıda, farklı aileden temalarda: bölümde yazı düzenle, gizle/göster, kütüphaneden ekle/kaldır (panel arayüzü)."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn
from starlette.testclient import TestClient
from playwright.sync_api import sync_playwright
s = boot.server; ok, bad = [], []; PGX = [None]
THEMES = sys.argv[1:] or ["1-kombi", "2-klima", "07-kombi-kizil", "22-tesisat-sari", "31-magaza-kombi", "p01-cine-kombi", "p10-neon-klima", "p25-lux-kombi", "p45-edit-bilgisayar",
                          "k5-atolye-kuafor", "k8-sakin-kuafor", "k10-atolye-kuafor"]
def t(n, f):
    try: f(); ok.append(n); print("  ✓", n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-700:])); print("  ✗", n); print(bad[-1][1][-350:])
        try: PGX[0].screenshot(path="/tmp/ui_fail_%s.png" % n.split(":")[0])
        except Exception: pass
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ali", "phone": "05524165755", "sector": "Kombi"}).json()
    EMAIL, PW = j["email"], j["password"]
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
    c.post("/api/yp/sectors/teknik", headers=H, json={})
    async def tema(slug):
        f = await s.db.main().firms.find_one({"login_email": EMAIL}, {"_id": 0, "db": 1}); S = s.db.firm(f["db"])
        await S.app_settings.update_one({"_id": "brand"}, {"$set": {"theme": slug}}, upsert=True)
        await S.app_settings.delete_one({"_id": "site_profile"}); await S.yp_pages.delete_many({"id": "tema-ek"})
    port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
    srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
    for _ in range(60):
        try: sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
        except OSError: time.sleep(0.2)
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = br.new_page(viewport={"width": 1440, "height": 960}); PGX[0] = pg; errs = []; pg.on("pageerror", lambda e: errs.append((str(e)[:120], (getattr(e, "stack", "") or "")[:300])))
        pg.goto("http://127.0.0.1:%d/salon" % PORT); pg.wait_for_selector("#lf", timeout=15000)
        pg.fill("#lf input[name=email]", EMAIL); pg.fill("#lf input[name=password]", PW)
        pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(400)
        for sl in THEMES:
            c.portal.call(tema, sl); errs.clear()
            def akis(sl=sl):
                pg.evaluate("location.hash='#bugun'"); pg.reload(); pg.wait_for_selector("#app:not([hidden])", timeout=15000)
                pg.evaluate("location.hash='#site'"); pg.wait_for_selector(".stabs button", timeout=10000); pg.wait_for_timeout(1500)
                pg.click('.stabs button[data-t="bolum"]'); pg.wait_for_timeout(250)
                pg.click('[data-a="sted"][data-e="tema"]'); pg.wait_for_selector("#bl .row", timeout=20000)
                n0 = pg.locator("#bl .row").count(); assert n0 >= 3, n0
                # yazı düzenle
                btn = pg.locator('#bl [data-a="bedit"]:not([disabled])').first; btn.click(); pg.wait_for_selector("#btf input", timeout=10000)
                mk = "UIMARK" + str(len(sl)); pg.locator('#btf input[name^="t"]').first.fill(mk); pg.locator("#btf .btn.p").click(); pg.wait_for_timeout(1500)
                ed = c.get("/api/site/profile", headers=H).json()["profile"]["edits"].get(sl) or {}
                assert any(mk in v.values() for v in ed.values()), ed
                # gizle / göster
                tg = pg.locator('#bl [data-a="btog"]:not([disabled])'); k = min(2, tg.count() - 1)
                idx = int(tg.nth(k).get_attribute("data-i")); nm = pg.evaluate("CUR.blocks[%d].name" % idx); was = pg.evaluate("CUR.blocks[%d].hidden" % idx)
                tg.nth(k).click(); pg.wait_for_timeout(1200)
                hid = c.get("/api/site/profile", headers=H).json()["profile"]["layout"]["hidden"]; assert (nm in hid) != was, (nm, was, hid)
                pg.locator('#bl [data-a="btog"]:not([disabled])').nth(k).click(); pg.wait_for_timeout(1200)
                hid = c.get("/api/site/profile", headers=H).json()["profile"]["layout"]["hidden"]; assert (nm in hid) == was, (nm, was, hid)
                # ekle / kaldır
                n1 = pg.locator("#bl .row").count()
                pg.click('[data-a="tekadd"]'); pg.wait_for_selector(".bxcard", timeout=10000); pg.locator(".bxcard").first.click(); pg.wait_for_selector("#bxf", timeout=10000)
                pg.locator('#bxf .mf .btn.p').first.click(); pg.wait_for_timeout(1500)
                assert pg.locator('#bl [data-a="tekset"]').count() == 1 and pg.locator("#bl .row").count() == n1 + 1
                pg.evaluate("document.getElementById('ov').hidden=true"); pg.click('#bl [data-a="tekdel"]'); pg.wait_for_timeout(300)
                okb = pg.locator('#ov button:has-text("Kaldır")')
                if okb.count(): okb.last.click()
                pg.wait_for_timeout(1500); assert pg.locator('#bl [data-a="tekset"]').count() == 0
                assert not errs, errs
            pass
            t(sl + ": yazı düzenle, gizle/göster, bölüm ekle/kaldır", akis)
        br.close()
    srv.should_exit = True
print("ok", len(ok), "bad", len(bad))
