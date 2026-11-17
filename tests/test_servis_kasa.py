"""/salon Servis kayıtları (kombi demo): liste, yeni kayıt, usta atama, durum, tamamla (parça + işçilik), iptal, arama; eski panel bağlantısı hâlâ var (servis)."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
import demo; demo.GUNLUK_LIMIT = 10 ** 6
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8797, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8797/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8797"; B = U + "/api"; ok = bad = 0
def t(n, c):
    global ok, bad
    ok += bool(c); bad += (not c); print(("  ✓ " if c else "  ✗ ") + n)
d = rq.post(B + "/public/demo", json={"name": "Servis Sahibi", "phone": "05348887766", "sector": "kombi"}).json()
H = {"Authorization": "Bearer " + rq.post(B + "/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
from playwright.sync_api import sync_playwright
# iş: usta + tamamlanmış kayıt (API)
techs = rq.get(B + "/technicians", headers=H).json(); tid = techs[0]["id"]; pct = techs[0].get("commission_percent", 0)
j = rq.post(B + "/jobs/quick", headers=H, json={"customer_name": "Kasa Test", "customer_phone": "05321112233", "fault_description": "Kombi ses yapıyor", "assigned_technician_id": tid}).json()
jid = j.get("id") or (j.get("job") or {}).get("id")
r = rq.put(B + "/jobs/" + jid, headers=H, json={"status": "tamamlandi", "work_done": "Pompa değişti", "parts_used": [{"name": "Pompa", "qty": 1, "unit_price": 500}], "labor_fee": 500}); t("API: kayıt tamamlandı", r.status_code == 200)
cs = rq.get(B + "/cash/summary", headers=H).json(); t("kasa geliri 1000 ve usta primi/borcu yazıldı", cs["income"] >= 1000 and (cs["technician_total_debt"] + cs["technician_total_commission"]) >= 1000 - 1)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); ctx = br.new_context(viewport={"width": 1440, "height": 900}); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(U + "/salon"); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", d["email"]); pg.fill("#lf input[name=password]", d["password"]); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000)
    for h_, k in (("skasa", "Kasa"), ("smusteri", "Müşteriler"), ("sekip", "Ekip"), ("stakvim", "Takvim"), ("srapor", "Raporlar")):
        t("menüde %s" % h_, pg.locator('#nav a[href="#%s"], #nav a[data-g]' % h_).count() >= 1)
    pg.goto(U + "/salon#skasa"); pg.wait_for_selector(".figs", timeout=8000); pg.wait_for_timeout(500)
    tx = pg.inner_text("#main"); t("kasa: gelir görünür", "1.000" in tx or "1000" in tx); t("kasa: servis geliri satırı", "Servis Geliri" in tx)
    pg.screenshot(path="/tmp/s-kasa.png")
    pg.click("[data-a=sk-tab][data-v=usta]"); pg.wait_for_timeout(900);  t("usta hesapları listesi", "kalan borç" in pg.inner_text("#main").lower())
    pg.click('[data-a=sk-odeme] >> nth=0'); pg.wait_for_selector("#skt"); pg.select_option("#sku", index=1); pg.fill("#skt", "100"); pg.click('[data-a=sk-odeme-ok]'); pg.wait_for_timeout(1200)
    cs2 = rq.get(B + "/cash/summary", headers=H).json(); t("usta ödemesi kasaya işlendi", cs2["technician_total_paid"] == cs["technician_total_paid"] + 100)
    pg.click('[data-a=sk-tab][data-v=hareket]'); pg.wait_for_timeout(600); pg.click('[data-a=sk-gider]'); pg.wait_for_selector("#skt"); pg.fill("#skt", "75"); pg.fill("#skc", "Yakıt"); pg.click('[data-a=sk-gider-ok]'); pg.wait_for_timeout(1200)
    t("gider eklendi", rq.get(B + "/cash/summary", headers=H).json()["expense"] >= 75)
    pg.goto(U + "/salon#smusteri"); pg.wait_for_selector("#smlist table", timeout=8000); t("müşteri listesinde Kasa Test", "Kasa Test" in pg.inner_text("#smlist"))
    pg.fill("#smq", "Kasa"); pg.wait_for_timeout(900); pg.click('[data-a=sm-ac] >> nth=0'); pg.wait_for_selector("text=Servis geçmişi"); t("müşteri kartında geçmiş", "Kombi ses" in pg.inner_text(".modal, #modal, body")); pg.screenshot(path="/tmp/s-musteri.png"); pg.keyboard.press("Escape")
    pg.goto(U + "/salon#smusteri"); pg.wait_for_selector("[data-a=sm-yeni]"); pg.click("[data-a=sm-yeni]"); pg.wait_for_selector("#smn"); pg.fill("#smn", "Yeni Müşteri"); pg.fill("#smt", "05324445566"); pg.click("[data-a=sm-kaydet]"); pg.wait_for_timeout(1200)
    t("müşteri eklendi", any(c["name"] == "Yeni Müşteri" for c in rq.get(B + "/customers", headers=H).json()))
    pg.goto(U + "/salon#sekip"); pg.wait_for_selector("table.gr", timeout=8000); t("ekip tablosu ve kalan borç", "kalan borç" in pg.inner_text("#main").lower()); pg.screenshot(path="/tmp/s-ekip.png")
    pg.click("[data-a=se-yeni]"); pg.wait_for_selector("#sen"); pg.fill("#sen", "Yeni Usta"); pg.fill("#see", "yeniusta@test.com"); pg.fill("#sep", "sifre123"); pg.click("[data-a=se-kaydet]"); pg.wait_for_timeout(1500)
    t("usta eklendi", any(x["name"] == "Yeni Usta" for x in rq.get(B + "/technicians", headers=H).json()))
    pg.click('[data-a=se-duzenle] >> nth=0'); pg.wait_for_selector("#seaktif"); pg.fill("#sec", "40"); pg.click("[data-a=se-duz-ok]"); pg.wait_for_timeout(1200)
    t("usta oranı güncellendi", any(x.get("commission_percent") == 40 for x in rq.get(B + "/technicians", headers=H).json()))
    # takvim: planlı açık kayıt
    rq.post(B + "/jobs/quick", headers=H, json={"customer_name": "Takvim Müşteri", "customer_phone": "05327776655", "fault_description": "Bakım", "assigned_technician_id": tid, "scheduled_at": "2099-01-01T10:00"})
    pg.goto(U + "/salon#stakvim"); pg.wait_for_selector("h3, .empty", timeout=8000); pg.wait_for_timeout(500); t("takvimde planlı kayıt", "Takvim Müşteri" in pg.inner_text("#main")); pg.screenshot(path="/tmp/s-takvim.png")
    pg.goto(U + "/salon#srapor"); pg.wait_for_selector(".figs", timeout=8000); pg.wait_for_timeout(500); t("rapor ciro", "Ciro" in pg.inner_text("#main")); pg.screenshot(path="/tmp/s-rapor.png")
    # fiş
    pg.goto(U + "/salon#servis"); pg.wait_for_selector("#svlist tbody tr", timeout=8000); pg.click('[data-a=sv-seg][data-v=tamamlandi]'); pg.wait_for_timeout(800); pg.click('[data-a=sv-ac] >> nth=0'); pg.wait_for_selector("[data-a=sv-fis]")
    with ctx.expect_page() as np_: pg.click("[data-a=sv-fis]")
    fp = np_.value; fp.wait_for_load_state(); ft = fp.inner_text("body"); t("fiş: müşteri ve toplam", "Kasa Test" in ft and "1.000" in ft.replace(" ", "")); fp.screenshot(path="/tmp/s-fis.png")
    t("JavaScript hatası yok", not errs)
    if errs: print(errs[:4])
print("OK", ok, "FAIL", bad)
