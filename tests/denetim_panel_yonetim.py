"""Yönetim (owner) panelinden açılan firmalar: sektör ve paket seçimi müşteri panelinde doğru yansıyor mu?
Her (sektör, paket) için firma açılır, firma kullanıcısıyla panele girilir; sektör, modüller, menü ve metinler denetlenir."""
import sys, os, threading, time, socket, re
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn
from starlette.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import sektor_dil
SEC = (sys.argv[1].split(",") if len(sys.argv) > 1 else ["kombi", "oto_servis", "eticaret", "tekstil", "lokanta", "kuafor", "dis_klinigi", "avukat", "emlakci", "nakliye"])
YASAK = {"randevu": ["usta", "garanti", "atölye", "yedek parça", "saha operasyon", "arıza"], "siparis": ["usta", "garanti", "atölye", "arıza", "saha operasyon"],
         "yol": ["usta", "garanti", "atölye", "yedek parça"], "proje": ["usta", "garanti", "atölye", "yedek parça", "arıza", "saha operasyon"]}
rows = []
def note(k, m): rows.append((k, m)); print("SORUN", k, m, flush=True)
made = []
with TestClient(boot.server.app) as c:
    OW = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    pk = c.get("/api/admin/packages", headers=OW).json()["packages"]
    print("paketler:", {k: v["modules"] for k, v in pk.items()}, flush=True)
    n = 0
    for s in SEC:
        for pkg in pk:
            n += 1
            em = "d%d@deneme.com" % n
            r = c.post("/api/admin/firms", headers=OW, json={"name": "Deneme %s %s" % (s, pkg), "email": em, "password": "Deneme1234!", "sector": s, "package": pkg, "phone": "0532%07d" % n})
            if r.status_code != 200: note(s + "/" + pkg, "firma açılmadı %s %s" % (r.status_code, r.text[:90])); continue
            made.append((s, pkg, em))
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try: sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)
U = "http://127.0.0.1:%d/salon" % PORT
NAVJS = "[...document.querySelectorAll('#nav a[data-rs]')].flatMap(a=>a.dataset.rs.split(',')).filter((x,i,a)=>a.indexOf(x)===i)"
seen = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for s, pkg, em in made:
        key = s + "/" + pkg; fam = sektor_dil.family(s)
        ctx = b.new_context(viewport={"width": 1440, "height": 900}); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:100]))
        try:
            pg.goto(U); pg.wait_for_selector("#lf", timeout=15000)
            pg.fill("#lf input[name=email]", em); pg.fill("#lf input[name=password]", "Deneme1234!")
            pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(500)
        except Exception as e:
            note(key, "panel açılmadı: %s" % str(e)[:80]); ctx.close(); continue
        B = pg.evaluate("B"); routes = pg.evaluate(NAVJS); seen[key] = (B.get("modules"), routes)
        if B.get("sector") != s: note(key, "panel sektörü %r (seçilen %r)" % (B.get("sector"), s))
        if B.get("pack") != s: note(key, "pack %r (seçilen %r)" % (B.get("pack"), s))
        for r in routes[:60]:
            try:
                pg.evaluate("location.hash='#%s'" % r); pg.wait_for_timeout(900); t = pg.inner_text("#main")
            except Exception: note(key, "%s okunamadı" % r); continue
            low = t.lower()
            if r in ('dil', 'markaseo'): low = ''          # çeviri kataloğu / demo marka adları: sektör metni değil
            for y in YASAK.get(fam, []):
                if y in low: i = low.find(y); note(key, "%s sayfasında '%s': …%s…" % (r, y, t[max(0, i - 25):i + 35].replace("\n", " ")))
            if re.search(r"undefined|\[object|NaN|\{\{|Traceback", t): note(key, "%s bozuk metin" % r)
        nav = pg.inner_text("#nav").lower()
        for y in YASAK.get(fam, []):
            if y in nav: note(key, "menüde '%s'" % y)
        for e in errs[:2]: note(key, "JS: " + e)
        ctx.close()
    b.close()
# paketler menüyü ayırıyor mu?
print("\n== Paket → menü farkı ==")
for s in SEC:
    sets = {pkg: set(seen.get(s + "/" + pkg, (None, []))[1]) for pkg in ("baslangic", "profesyonel", "tam", "kurumsal")}
    base = sets["baslangic"]
    print(s, {k: len(v) for k, v in sets.items()}, "| başlangıçta olmayıp tamda olan:", sorted(sets["tam"] - base)[:8], "| mods:", {k: seen.get(s + "/" + k, ([], []))[0] for k in ("baslangic", "tam")})
print("\nÖZET: %d firma, %d sorun" % (len(made), len(rows)))
os._exit(0)
