"""Her sektör için gerçek tarayıcıda müşteri paneli denetimi: açılan panel sektöre uygun mu (menü, modüller, metinler)?
Kullanım: python3 tests/denetim_panel_sektor.py [sektor1,sektor2]   Çıktı: SORUN satırları + özet."""
import sys, os, threading, time, socket, re, json
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn
from starlette.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import sektor, sektor_dil, demo
demo.GUNLUK_LIMIT = 10 ** 6
KEYS = list(sektor.SECTORS)
if len(sys.argv) > 1: KEYS = sys.argv[1].split(",")
# aile → panelde görünmemesi gereken (başka sektöre ait) sözcükler
YASAK = {
    "randevu": ["usta", "garanti", "atölye", "yedek parça", "saha operasyon", "arıza"],
    "siparis": ["usta", "garanti", "atölye", "arıza", "saha operasyon"],
    "yol": ["usta", "garanti", "atölye", "yedek parça"],
    "proje": ["usta", "garanti", "atölye", "yedek parça", "arıza", "saha operasyon"],
}
rows = []
def note(k, m): rows.append((k, m)); print("SORUN", k, m, flush=True)
users = {}
with TestClient(boot.server.app) as c:
    for i, k in enumerate(KEYS):
        demo._RATE.clear()
        r = c.post("/api/public/demo", json={"name": "Deneme Kisi", "phone": "0553%07d" % (5000 + i), "sector": k})
        if r.status_code != 200: note(k, "demo açılmadı %s" % r.text[:80]); continue
        users[k] = r.json()
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try: sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)
U = "http://127.0.0.1:%d/salon" % PORT
JS_ROUTES = "[...document.querySelectorAll('#nav a[data-rs]')].flatMap(a=>a.dataset.rs.split(',')).filter((x,i,a)=>a.indexOf(x)===i)"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for k, d in users.items():
        fam = sektor_dil.family(k)
        ctx = b.new_context(viewport={"width": 1440, "height": 900}); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("JS: " + str(e)[:100]))
        try:
            pg.goto(U); pg.wait_for_selector("#lf", timeout=15000)
            pg.fill("#lf input[name=email]", d["email"]); pg.fill("#lf input[name=password]", d["password"])
            pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(500)
        except Exception as e:
            note(k, "panel açılmadı: %s" % str(e)[:80]); ctx.close(); continue
        bt = pg.evaluate("B")
        if bt.get("sector") != k: note(k, "açılan panel sektörü %r, beklenen %r" % (bt.get("sector"), k))
        routes = pg.evaluate(JS_ROUTES)
        if len(routes) < 4: note(k, "menü çok az: %s" % routes)
        yasak = YASAK.get(fam, [])
        for r in routes[:60]:
            try:
                pg.evaluate("location.hash='#%s'" % r); pg.wait_for_timeout(900)
                t = pg.inner_text("#main")
            except Exception as e:
                note(k, "%s sayfası okunamadı" % r); continue
            low = t.lower()
            if r in ('dil', 'markaseo'): low = ''          # çeviri kataloğu / demo marka adları: sektör metni değil
            if len(t.strip()) < 15 and r != 'dil': note(k, "%s sayfası boş" % r)
            for y in yasak:
                if y in low:
                    i = low.find(y); note(k, "%s sayfasında '%s' geçiyor: …%s…" % (r, y, t[max(0, i - 25):i + 35].replace("\n", " ")))
            if re.search(r"undefined|\[object|NaN|\{\{|Traceback", t): note(k, "%s sayfasında bozuk metin" % r)
        # menü etiketleri de aynı denetimden geçsin
        nav = pg.inner_text("#nav").lower()
        for y in yasak:
            if y in nav: note(k, "menüde '%s' var" % y)
        for e in errs[:3]: note(k, e)
        print("tamam", k, fam or "teknik", len(routes), flush=True)
        ctx.close()
    b.close()
print("\nÖZET: %d sektör, %d sorun" % (len(users), len(rows)))
os._exit(0)
