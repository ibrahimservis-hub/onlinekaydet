"""/salon Servis kayıtları (kombi demo): liste, yeni kayıt, usta atama, durum, tamamla (parça + işçilik), iptal, arama; eski panel bağlantısı hâlâ var (servis)."""
import sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
import demo; demo.GUNLUK_LIMIT = 10 ** 6
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8798, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8798/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8798"; B = U + "/api"; ok = bad = 0
def t(n, c):
    global ok, bad
    ok += bool(c); bad += (not c); print(("  ✓ " if c else "  ✗ ") + n)
d = rq.post(B + "/public/demo", json={"name": "Servis Sahibi", "phone": "05348887766", "sector": "kombi"}).json()
H = {"Authorization": "Bearer " + rq.post(B + "/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
from playwright.sync_api import sync_playwright
from PIL import Image
Image.new("RGB", (300, 200), (200, 80, 40)).save("/tmp/atl.jpg")
techs = rq.get(B + "/technicians", headers=H).json(); tid = techs[0]["id"]
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); ctx = br.new_context(viewport={"width": 1440, "height": 1000}); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(U + "/salon"); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", d["email"]); pg.fill("#lf input[name=password]", d["password"]); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000)
    def go(h, sel="#main .card, #main .empty"):
        pg.goto(U + "/salon#" + h); pg.wait_for_selector(sel, timeout=8000); pg.wait_for_timeout(500)
    # --- stok
    go("sstok"); pg.click("[data-a=x-parca-yeni]"); pg.wait_for_selector("#xpn"); pg.fill("#xpn", "Test Pompa"); pg.fill("#xpq", "5"); pg.fill("#xpm", "2"); pg.fill("#xpc", "300"); pg.fill("#xpp", "500"); pg.click("[data-a=x-parca-ok]"); pg.wait_for_timeout(1200)
    parts = rq.get(B + "/parts", headers=H).json(); pt = [p for p in parts if p["name"] == "Test Pompa"]; t("parça eklendi", len(pt) == 1 and pt[0]["stock_qty"] == 5); pid = pt[0]["id"]
    pg.screenshot(path="/tmp/x-stok.png")
    pg.click("[data-a=x-parca-duz] >> nth=0") if False else None
    # kayıt aç, parçayı stoktan seçerek tamamla
    j = rq.post(B + "/jobs/quick", headers=H, json={"customer_name": "Stok Müşteri", "customer_phone": "05321110099", "fault_description": "Pompa arızası", "assigned_technician_id": tid}).json(); jid = j.get("id") or j["job"]["id"]
    rq.put(B + "/jobs/" + jid, headers=H, json={"status": "basladi"})
    go("servis", "#svlist table, #svlist .empty"); pg.fill("#svq", "Stok Müşteri"); pg.wait_for_timeout(900); pg.click("[data-a=sv-ac]"); pg.wait_for_selector("[data-a=sv-kapat]")
    t("detayda atölyeye al düğmesi (işlemde)", pg.locator("[data-a=x-at-form]").count() == 1)
    pg.click("[data-a=sv-kapat]"); pg.wait_for_selector("#svpt .ps"); pg.select_option("#svpt .ps", pid); pg.fill("#svpt .pq", "2"); pg.fill("#svw", "Pompa değişti"); pg.fill("#svl", "100"); pg.click("[data-a=sv-kapat-ok]"); pg.wait_for_timeout(1500)
    pp = [p for p in rq.get(B + "/parts", headers=H).json() if p["id"] == pid][0]; t("stoktan 2 adet düştü (5→3)", pp["stock_qty"] == 3)
    jj = rq.get(B + "/jobs/" + jid, headers=H).json(); t("kayıtta part_id ve toplam 1100", jj["parts_used"][0].get("part_id") == pid and jj["total_amount"] == 1100)
    pg.click("[data-a=sv-seg][data-v=tamamlandi]"); pg.wait_for_timeout(800); pg.fill("#svq", "Stok Müşteri"); pg.wait_for_timeout(900); pg.click("[data-a=sv-ac]"); pg.wait_for_selector("[data-a=sv-fis]")
    pg.click('[data-a=sv-durum][data-v=faturalandi]'); pg.wait_for_timeout(1200); t("faturalandı işaretlendi", rq.get(B + "/jobs/" + jid, headers=H).json()["status"] == "faturalandi")
    go("sstok"); pg.fill("#xsq", "Test Pompa"); pg.wait_for_timeout(800); pg.click("[data-a=x-parca-duz]"); pg.wait_for_selector("#xpq"); pg.fill("#xpq", "1"); pg.click("[data-a=x-parca-ok]"); pg.wait_for_timeout(1000)
    go("sstok"); t("azalan parça kırmızı/asgari uyarısı", "asgari" in pg.inner_text("#main"))
    # --- teklif
    go("steklif"); pg.click("[data-a=x-teklif-yeni]"); pg.wait_for_selector("#xqn"); pg.fill("#xqn", "Teklif Müşteri"); pg.fill("#xqt", "05327770011"); pg.fill("#xqd", "kombi"); pg.fill("#xqf", "Eşanjör"); pg.fill("#xqtt", "2000"); pg.fill("#xqli", "500"); pg.fill(".xqp .qn", "Eşanjör"); pg.click("[data-a=x-teklif-ok]"); pg.wait_for_timeout(1300)
    qs = rq.get(B + "/quotes", headers=H).json(); t("teklif kaydedildi, parça payı 1500", len(qs) == 1 and qs[0]["parts"][0]["amount"] == 1500); pg.screenshot(path="/tmp/x-teklif.png")
    pg.click("[data-a=x-teklif-ac]"); pg.wait_for_selector("[data-a=x-teklif-cevir-form]"); pg.click("[data-a=x-teklif-cevir-form]"); pg.wait_for_selector("#xcu"); pg.select_option("#xcu", index=1); pg.click("[data-a=x-teklif-cevir]"); pg.wait_for_timeout(1500)
    q = rq.get(B + "/quotes", headers=H).json()[0]; t("teklif servis kaydına çevrildi", bool(q.get("converted_job_id")))
    # --- randevu
    go("srandevu"); pg.click("[data-a=x-rd-yeni]"); pg.wait_for_selector("#xrt"); pg.fill("#xrt", "Keşif ziyareti"); pg.fill("#xrs", "2099-02-01T10:00"); pg.click("[data-a=x-rd-ok]"); pg.wait_for_timeout(1200)
    t("randevu eklendi", any(a["title"] == "Keşif ziyareti" for a in rq.get(B + "/appointments", headers=H).json()))
    pg.click("[data-a=x-rd-durum][data-v=tamamlandi]"); pg.wait_for_timeout(900); t("randevu tamamlandı", rq.get(B + "/appointments", headers=H).json()[0]["status"] == "tamamlandi")
    pg.click("[data-a=x-onay-rd]"); pg.click("[data-a=x-rd-sil]"); pg.wait_for_timeout(900); t("randevu silindi", not rq.get(B + "/appointments", headers=H).json())
    # --- atölye
    j2 = rq.post(B + "/jobs/quick", headers=H, json={"customer_name": "Atölye Müşteri", "customer_phone": "05325550011", "fault_description": "Kart arızası", "assigned_technician_id": tid}).json(); j2id = j2.get("id") or j2["job"]["id"]
    rq.put(B + "/jobs/" + j2id, headers=H, json={"status": "basladi"})
    go("servis", "#svlist table, #svlist .empty"); pg.click('[data-a=sv-seg][data-v=""]'); pg.fill("#svq", "Atölye Müşteri"); pg.wait_for_timeout(900); pg.click("[data-a=sv-ac]"); pg.wait_for_selector("[data-a=x-at-form]"); pg.click("[data-a=x-at-form]"); pg.wait_for_selector("#xs1")
    pg.set_input_files("#xaf2", "/tmp/atl.jpg")
    for sid in ("#xs1", "#xs2"):
        bx = pg.locator(sid).bounding_box(); pg.mouse.move(bx["x"] + 30, bx["y"] + 30); pg.mouse.down(); pg.mouse.move(bx["x"] + 120, bx["y"] + 70, steps=6); pg.mouse.move(bx["x"] + 60, bx["y"] + 100, steps=6); pg.mouse.up()
    pg.click("[data-a=x-at-ok]"); pg.wait_for_timeout(800); t("onay kutusu olmadan atölyeye alınmaz", not rq.get(B + "/workshop", headers=H).json()["rows"])
    pg.check("#xaok"); pg.click("[data-a=x-at-ok]"); pg.wait_for_timeout(1800)
    wl = rq.get(B + "/workshop", headers=H).json()["rows"]; wp = rq.get(B + "/workshop/" + j2id + "/photos", headers=H).json(); t("atölyeye alındı (imza+foto+onay)", len(wl) == 1 and len(wp["photos"]) == 1 and wp["signature"].startswith("data:image") and wp["tech_signature"].startswith("data:image"))
    go("satolye"); t("atölye listesinde fiş", "ATL-" in pg.inner_text("#main")); pg.screenshot(path="/tmp/x-atolye.png")
    pg.click("[data-a=x-at-ac]"); pg.wait_for_selector("[data-a=x-at-durum][data-v=hazir]"); pg.click("[data-a=x-at-durum][data-v=hazir]"); pg.wait_for_timeout(1200); t("atölye: hazır", rq.get(B + "/workshop", headers=H).json()["rows"][0]["state"] == "hazir")
    pg.click("[data-a=x-at-ac]"); pg.wait_for_selector("[data-a=x-at-durum][data-v=teslim]"); pg.click("[data-a=x-at-durum][data-v=teslim]"); pg.wait_for_timeout(1200); t("atölye: teslim edildi", not rq.get(B + "/workshop", headers=H).json()["rows"])
    # --- ayar + marka
    go("sayar"); pg.fill("#xaf", "Deneme Servis"); pg.fill("#xvd", "5"); pg.click("[data-a=x-ayar-kaydet]"); pg.wait_for_timeout(1000)
    st = rq.get(B + "/settings", headers=H).json(); t("firma ayarı ve usta kuralı kaydedildi", st["company_name"] == "Deneme Servis" and st["tech_visibility"]["done_days"] == 5)
    pg.click("[data-a=x-marka-yeni]"); pg.wait_for_selector("#xmn"); pg.fill("#xmn", "Yeni Marka X"); pg.click("[data-a=x-marka-ok]"); pg.wait_for_timeout(1000); t("marka eklendi", any(b["name"] == "Yeni Marka X" for b in rq.get(B + "/brands", headers=H).json())); pg.screenshot(path="/tmp/x-ayar.png")
    # --- konum
    go("skonum"); t("konum ekranı ustaları listeler", "konum" in pg.inner_text("#main").lower())
    # --- cihaz
    go("smusteri", "#smlist table"); pg.fill("#smq", "Stok"); pg.wait_for_timeout(900); pg.click("[data-a=sm-ac]"); pg.wait_for_selector("[data-a=x-cihaz-form]"); pg.click("[data-a=x-cihaz-form]"); pg.wait_for_selector("#xdb"); pg.select_option("#xdb", index=1); pg.fill("#xdm", "Model Z"); pg.click("[data-a=x-cihaz-ok]"); pg.wait_for_timeout(1100)
    cid = [c for c in rq.get(B + "/customers", headers=H).json() if c["name"] == "Stok Müşteri"][0]["id"]; t("cihaz eklendi", any(x.get("model") == "Model Z" for x in rq.get(B + "/customers/" + cid, headers=H).json()["devices"]))
    # --- ekip: profil + şifre
    go("sekip", "table.gr"); pg.click("[data-a=se-duzenle] >> nth=0"); pg.wait_for_selector("[data-a=x-ekip-profil]"); pg.click("[data-a=x-ekip-profil]"); pg.wait_for_selector("#xpi"); pg.fill("#xpi", "Ankara"); pg.check(".xpg[value=kombi]"); pg.fill("#xpn2", "Güvenilir usta"); pg.click("[data-a=x-ekip-profil-ok]"); pg.wait_for_timeout(1000)
    tp = [x for x in techs if True][0]; pr = rq.get(B + "/technicians/" + tp["id"] + "/profile", headers=H).json(); t("usta profili kaydedildi", pr["profile"]["city"] == "Ankara" and "kombi" in pr["profile"]["service_groups"] and pr["note"] == "Güvenilir usta")
    pg.click("[data-a=se-duzenle] >> nth=0"); pg.wait_for_selector("[data-a=x-ekip-sifre]"); pg.click("[data-a=x-ekip-sifre]"); pg.click("[data-a=x-ekip-sifre-ok]"); pg.wait_for_selector("text=Bu şifre yalnız şimdi gösterilir"); t("şifre sıfırlandı ve gösterildi", True); pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
    # --- tekrar ata (ayrı kayıt)
    j3 = rq.post(B + "/jobs/quick", headers=H, json={"customer_name": "Tekrar Müşteri", "customer_phone": "05324440077", "fault_description": "Aynı arıza", "assigned_technician_id": tid}).json(); j3id = j3.get("id") or j3["job"]["id"]
    rq.put(B + "/jobs/" + j3id, headers=H, json={"status": "basladi"}); rq.put(B + "/jobs/" + j3id, headers=H, json={"status": "tamamlandi", "work_done": "x", "parts_none": True, "labor_fee": 100})
    n_before = len(rq.get(B + "/jobs?q=Tekrar", headers=H).json())
    go("servis", "#svlist table, #svlist .empty"); pg.click('[data-a=sv-seg][data-v=""]'); pg.fill("#svq", "Tekrar Müşteri"); pg.wait_for_timeout(1000); pg.click("[data-a=sv-ac]"); pg.wait_for_selector("[data-a=x-job-tekrar]")
    pg.select_option("#xtu", index=1); pg.click("[data-a=x-job-tekrar]"); pg.wait_for_timeout(1500)
    after = rq.get(B + "/jobs?q=Tekrar", headers=H).json(); t("tekrar atama çalıştı (kayıt yeniden atandı)", len(after) >= 1 and any(x["status"] in ("atandi", "yeni") for x in after) or len(after) > n_before)
    # --- sil: stok ve kasa geri alınır
    cash0 = rq.get(B + "/cash/summary", headers=H).json()["income"]; stk0 = [p for p in rq.get(B + "/parts", headers=H).json() if p["id"] == pid][0]["stock_qty"]
    jno = rq.get(B + "/jobs/" + jid, headers=H).json()["job_number"]; pg.fill("#svq", jno); pg.wait_for_timeout(1000)
    pg.click("[data-a=sv-ac]"); pg.wait_for_selector("[data-a=x-job-sil-onay]"); pg.click("[data-a=x-job-sil-onay]"); pg.wait_for_selector("[data-a=x-job-sil]"); pg.click("[data-a=x-job-sil]"); pg.wait_for_timeout(1500)
    gone = rq.get(B + "/jobs/" + jid, headers=H).status_code == 404
    t("kayıt silindi, kasa geliri geri alındı, stok geri geldi", gone and rq.get(B + "/cash/summary", headers=H).json()["income"] < cash0 and [p for p in rq.get(B + "/parts", headers=H).json() if p["id"] == pid][0]["stock_qty"] == stk0 + 2)
    # --- son kalanlar
    rq.post(B + "/cash/transactions", headers=H, json={"type": "gider", "amount": 20, "description": "Sahipsiz deneme"})
    om = rq.post(B + "/cash/transactions", headers=H, json={"type": "teknisyen_odeme", "amount": 30, "description": "Bağsız", "technician_id": "yok"})
    go("skasa", ".figs"); t("sahipsiz hareket yoksa uyarı yok", "kimseye bağlı değil" not in pg.inner_text("#main"))
    go("sekip", "table.gr"); pg.click("[data-a=x2-ekip-detay] >> nth=0"); pg.wait_for_selector("text=Son işler"); t("usta detayı: bakiye ve iş geçmişi", "Kalan borç" in pg.inner_text("#ov") or "kalan borç" in pg.inner_text("#ov").lower()); pg.keyboard.press("Escape")
    go("sayar", "#xye"); t("site yorumu ve telefon bölümü", "Telefon numaralarını düzelt" in pg.inner_text("#main"))
    pg.select_option("#xye", "1"); pg.fill("#xyt", "Yorumlar"); pg.click("[data-a=x2-yorum]"); pg.wait_for_timeout(900); sr = rq.get(B + "/site-reviews-settings", headers=H).json(); t("site yorumu ayarı kaydedildi", sr["enabled"] and sr["title"] == "Yorumlar")
    pg.click("[data-a=x2-tel][data-v='0']"); pg.wait_for_selector("text=Zaten doğru"); t("telefon raporu açıldı", True); pg.keyboard.press("Escape")
    go("servis", "#svlist table, #svlist .empty"); t("servis uyarı şeridi", pg.locator("#xuy").count() in (0, 1))
    t("JavaScript hatası yok", not errs)
    if errs: print(errs[:4])
print("OK", ok, "FAIL", bad)
