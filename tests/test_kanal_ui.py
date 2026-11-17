"""Yeni panel: Pazaryeri ürünleri ekranı — liste, kategori ara/eşle, marka ara/eşle, kaydet."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests
from playwright.sync_api import sync_playwright
s = boot.server; ok, bad = [], []
import shop_sync
def t(n, f):
    try: f(); ok.append(n); print("  +", n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:])); print("  -", n)
TREE = {"categories": [{"id": 1, "name": "Ev", "subCategories": [{"id": 10, "name": "Kombi", "subCategories": []}]}]}
async def fh(method, url, headers, body=None):
    if url.endswith("/product-categories"): return 200, TREE
    if "brands/by-name" in url: return 200, [{"id": 77, "name": "Demirdöküm"}]
    return 200, {}
shop_sync.HTTP["fn"] = fh
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try: socket.create_connection(("127.0.0.1", PORT), 0.3).close(); break
    except OSError: time.sleep(0.2)
U = "http://127.0.0.1:%d" % PORT
L = lambda e, p: {"Authorization": "Bearer " + requests.post(U + "/api/auth/login", json={"email": e, "password": p}).json()["token"]}
A = L("admin@servis.com", "admin123")
F = requests.post(U + "/api/admin/firms", headers=A, json={"name": "Kanal Firma", "email": "kn@x.com", "password": "sifre12345", "package": "tam"}).json()["id"]
O = L("kn@x.com", "sifre12345")
requests.put(U + "/api/site/features", headers=O, json={"shop_enabled": True})
import asyncio
from starlette.testclient import TestClient
with TestClient(s.app) as c:
    async def go():
        f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
        await s.db.main().firms.update_one({"id": F}, {"$addToSet": {"modules": "eticaret"}})
        await s.db.firm(f["db"]).app_settings.update_one({"_id": "sp_modules"}, {"$set": {"config": {"trendyol": {"seller_id": "1", "api_key": "k", "api_secret": "s"}}}}, upsert=True)
    c.portal.call(go)
    rc = c.post("/api/shop/categories", headers=O, json={"name": "Kombi"}); assert rc.status_code == 200, rc.text
    cat = rc.json()
    r = c.post("/api/shop/products", headers=O, json={"name": "Kombi A", "brand": "Demirdöküm", "price": 100, "stock": 5, "category_id": cat["id"], "barcode": "8690000000111"}); assert r.status_code == 200, r.text
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = br.new_page(viewport={"width": 1280, "height": 900}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(U + "/salon"); pg.wait_for_selector("#lf"); pg.fill("#lf input[name=email]", "kn@x.com"); pg.fill("#lf input[name=password]", "sifre12345"); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])")
        def liste():
            pg.evaluate("location.hash='#kanal'"); pg.wait_for_selector("#kn table", timeout=8000)
            assert "Kombi A" in pg.inner_text("#kn")
        t("Pazaryeri ürünleri ekranı açılır, ürün listelenir", liste)
        def esle():
            pg.click("[data-k=knmap]"); pg.wait_for_selector("[data-cid]", timeout=6000)
            pg.fill(".knqc", "kombi"); pg.click("[data-k=knfc]"); pg.wait_for_selector("[data-k=knpick]", timeout=6000)
            pg.click("[data-k=knpick]"); assert pg.input_value(".kne") == "10"
            pg.click("[data-k=knsave]"); pg.wait_for_timeout(700)
            m = c.get("/api/shop/channels/trendyol/catmap", headers=O).json()
            assert m["categories"][0]["map"]["ext_id"] == "10", m
        t("kategori Trendyol ağacından aranır, seçilir, kaydedilir", esle)
        def marka():
            pg.click("[data-k=knfb]"); pg.wait_for_selector("[data-k=knbpick]", timeout=6000); pg.click("[data-k=knbpick]")
            pg.click("[data-k=knbsave]"); pg.wait_for_timeout(700)
            assert c.get("/api/shop/channels/trendyol/catmap", headers=O).json()["brands"][0]["ext_id"] == "77"
        t("marka kodu aranır ve kaydedilir", marka)
        def geri():
            pg.click("[data-k=knback]"); pg.wait_for_selector("#kn table"); pg.click("[data-k=knval]"); pg.wait_for_timeout(800)
        t("listeye dönülür, denetim çalışır", geri)
        t("JS hatası yok", lambda: (_ for _ in ()).throw(AssertionError(errs)) if errs else None)
        br.close()
print("OK", len(ok), "FAIL", len(bad))
for n, e in bad: print(n, e)
