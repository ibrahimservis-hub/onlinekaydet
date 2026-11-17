"""Bilgi bankası rehberleri için gerçek panel ekran görüntüleri (demo restoran hesabı, örnek yemekler). Çıktı: site/v9/img/bilgi/*.webp"""
import sys, os, threading, time, socket, io
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests, demo, shop_sync
from PIL import Image
from playwright.sync_api import sync_playwright
demo.GUNLUK_LIMIT = 10 ** 6
OUT = os.path.join(os.path.dirname(__file__), "..", "site", "v9", "img", "bilgi")
async def fake(m, u, h, b):
    if u.endswith("/stores?page=0&size=50"): return 200, {"restaurants": [{"id": 7, "name": "Şube 1"}]}
    if u.endswith("/stores/7/products"):
        return 200, {"products": [{"id": 1, "name": "Adana Kebap", "sellingPrice": 240, "status": "ACTIVE"}, {"id": 2, "name": "Mercimek Çorbası", "sellingPrice": 80, "status": "ACTIVE"},
                                  {"id": 3, "name": "Künefe", "sellingPrice": 110, "status": "ACTIVE"}, {"id": 4, "name": "Ayran", "sellingPrice": 30, "status": "ACTIVE"}]}
    return 200, {}
shop_sync.HTTP["fn"] = fake
s = boot.server
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try: socket.create_connection(("127.0.0.1", PORT), 0.3).close(); break
    except OSError: time.sleep(0.2)
U = "http://127.0.0.1:%d" % PORT
d = requests.post(U + "/api/public/demo", json={"name": "Mehmet", "phone": "05321110088", "sector": "lokanta"}).json()
H = {"Authorization": "Bearer " + requests.post(U + "/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
FOODS = [("Adana Kebap", 260, "Kebaplar", 20, ["gluten"], 2), ("Mercimek Çorbası", 80, "Çorbalar", 10, [], 0), ("Künefe", 120, "Tatlılar", 15, ["gluten", "süt"], 0),
         ("Ayran", 30, "İçecekler", 2, ["süt"], 0), ("Izgara Köfte", 230, "Kebaplar", 20, ["gluten"], 1), ("Baklava", 140, "Tatlılar", 5, ["gluten", "fıstık"], 0)]
for n, pr, b, hz, al, ac in FOODS:
    r = requests.post(U + "/api/yp/products", headers=H, json={"name": n, "price": pr, "vat": 10, "stock": 99, "desc": "Günlük taze hazırlanır.", "channels": {"site": True, "trendyol_yemek": True, "yemeksepeti": True},
        "food": {"bolum": b, "hazirlik": hz, "alerjen": al, "aci": ac, "cikarilabilir": ["soğan"] if b == "Kebaplar" else [], "gruplar": [{"ad": "Yan ürün", "min": 1, "max": 1, "secenekler": [{"ad": "Pilav", "fiyat": 0}, {"ad": "Salata", "fiyat": 15}]}] if b == "Kebaplar" else []}})
    assert r.status_code in (200, 201), r.text
requests.put(U + "/api/yp/integrations/trendyol_yemek", headers=H, json={"on": True, "keys": {"seller_id": "123", "api_key": "k", "api_secret": "s"}})
for i, (n, tt) in enumerate([("Ayşe Demir", 340), ("Can Yıldız", 190), ("Elif Kaya", 520)]):
    requests.post(U + "/api/yp/orders", headers=H, json={"customer": {"name": n, "phone": "0533000000%d" % i, "address": "Çankaya"}, "items": [{"name": "Adana Kebap", "qty": 1, "price": tt}], "channel": ["telefon", "yemeksepeti", "trendyol_yemek"][i]})
def kaydet(pg, ad, clip=None):
    im = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB"); im = im.resize((1000, int(im.height * 1000 / im.width)), Image.LANCZOS)
    im.save(os.path.join(OUT, ad + ".webp"), "WEBP", quality=82); print(ad, im.size)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); pg = br.new_page(viewport={"width": 1280, "height": 770})
    pg.goto(U + "/salon"); pg.wait_for_selector("#lf"); pg.fill("#lf input[name=email]", d["email"]); pg.fill("#lf input[name=password]", d["password"]); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])")
    def git(h, sel=None, w=1800):
        pg.evaluate("location.hash='%s'" % h); pg.wait_for_timeout(w)
        if sel: pg.wait_for_selector(sel, timeout=8000)
    git("#urun", "#main table, #main .row", 1500); kaydet(pg, "y_menu")
    git("#menusync", "#main table", 1800); kaydet(pg, "y_gonder")
    git("#siparis", "#slist", 2000); kaydet(pg, "y_siparis")
    git("#etiket", ".etg", 2500); kaydet(pg, "e_etiket")
    pg.click("[data-e=tip][data-v=qr]"); pg.wait_for_timeout(2200); kaydet(pg, "e_qr")
    git("#entegrasyon", ".egrp", 2000); kaydet(pg, "g_ent")
    git("#alanadi", "#xdn", 1500); kaydet(pg, "a_alan")
    git("#urun", "#main", 1200); pg.click("[data-a=urun-yeni]"); pg.wait_for_selector("#ue-yemek", timeout=8000); pg.wait_for_timeout(800)
    pg.evaluate("document.querySelector('#ue-yemek').scrollIntoView({block:'start'});[document.scrollingElement,document.querySelector('#main'),document.querySelector('main')].forEach(function(e){if(e&&e.scrollTop>80)e.scrollTop-=90})"); pg.wait_for_timeout(900); kaydet(pg, "y_yemekbilgi")
    br.close()
