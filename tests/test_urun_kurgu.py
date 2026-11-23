# -*- coding: utf-8 -*-
"""Ürün kurguları: öznitelik filtreleri, kişiselleştirme alanları (zorunlu, ek ücret, sunucuda doğrulama), sepet önerisi."""
import os, sys, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq, demo, jwt as _jwt
demo.GUNLUK_LIMIT = 10**6
PORT = 8798
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
U = "http://127.0.0.1:%d/api" % PORT
for _ in range(100):
    try:
        if rq.get(U + "/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(.2)
d = rq.post(U + "/public/demo", json={"name": "Kurgu Test", "phone": "05531000999", "sector": "eticaret"}).json()
tok = rq.post(U + "/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]
H = {"Authorization": "Bearer " + tok}
fid = str(_jwt.decode(tok, options={"verify_signature": False}).get("firm")).rsplit("_f_", 1)[-1]
ok = fail = 0
def chk(c, m):
    global ok, fail
    if c: ok += 1
    else: fail += 1; print("FAIL", m)
def call(m, p, **kw): return rq.request(m, U + p, headers=H, **kw)
def pub(m, p, **kw):
    a, b = p.rsplit("/", 1)
    return rq.request(m, U + a + "/" + fid + "~" + b, **kw)

def yeni(name, price, specs=None, **kw):
    body = {"name": name, "price": price, "cost": 10, "stock": 20, "channels": {"site": True}, "cat": "Hediyelik", "specs": specs or []}
    body.update(kw)
    r = call("POST", "/yp/products", json=body); assert r.status_code == 200, r.text
    j = r.json(); return j.get("item") or j

PZ = [{"label": "Üzerine yazılacak isim", "type": "text", "required": True, "max": 12, "fee": 30},
      {"label": "Renk", "type": "select", "options": "Altın, Gümüş", "fee": 0},
      {"label": "Hediye paketi", "type": "checkbox", "fee": 15}]
a = yeni("Isimli Kolye", 500, [{"k": "Malzeme", "v": "Gümüş"}, {"k": "Renk", "v": "Kırmızı"}], personalization=PZ)
b = yeni("Zincir Bileklik", 300, [{"k": "Malzeme", "v": "Altın"}, {"k": "Renk", "v": "Mavi"}])
c = yeni("Yüzük", 400, [{"k": "Malzeme", "v": "Gümüş"}, {"k": "Renk", "v": "Kırmızı"}])
call("PUT", f"/yp/products/{a['id']}", json={**a, "related": [b["id"]]})

# kişiselleştirme tanımı temizlendi ve açığa çıktı
g = pub("GET", "/public/shop/products/" + (a.get("slug") or a["id"])).json()
pz = g.get("personalization") or []
chk(len(pz) == 3 and pz[0]["required"] and pz[0]["fee"] == 30 and pz[1]["options"] == ["Altın", "Gümüş"], "tanım %s" % pz)

# öznitelik filtreleri
r = pub("GET", "/public/shop/search").json()
at = {x["key"]: {v["v"]: v["count"] for v in x["values"]} for x in r.get("attrs", [])}
chk(at.get("Malzeme", {}).get("Gümüş", 0) >= 2 and at.get("Renk", {}).get("Kırmızı", 0) >= 2, "facet sayıları %s" % at)
r = pub("GET", "/public/shop/search?a=" + rq.utils.quote("Malzeme:Gümüş")).json()
names = sorted(x["name"] for x in r["items"])
chk(all(n in ("Isimli Kolye", "Yüzük") for n in names) and len(names) >= 2 and "Zincir Bileklik" not in names, "filtre sonucu %s" % names)
r2 = pub("GET", "/public/shop/search?a=" + rq.utils.quote("Malzeme:Gümüş|Renk:Mavi")).json()
chk(r2["total"] == 0, "AND mantığı: %s" % r2["total"])
r3 = pub("GET", "/public/shop/search?a=" + rq.utils.quote("Malzeme:Gümüş|Malzeme:Altın")).json()
chk(r3["total"] >= 3, "aynı özellikte OR: %s" % r3["total"])
r4 = pub("GET", "/public/shop/search?a=" + rq.utils.quote("Renk:Kırmızı")).json()
mal = {v["v"]: v["count"] for x in r4["attrs"] if x["key"] == "Malzeme" for v in x["values"]}
chk("Altın" not in mal and mal.get("Gümüş", 0) >= 2, "diğer filtreye göre sayılar %s" % mal)
chk(pub("GET", "/public/shop/search?a=" + rq.utils.quote("x.y:1|$ne:2")).status_code == 200, "kötü anahtar çökmez")

# sepet önerisi
r = pub("GET", "/public/shop/cart-suggest?ids=" + a["id"]).json()
chk([x["id"] for x in r["items"]][:1] == [b["id"]], "birlikte satılacak önce %s" % [x["name"] for x in r["items"]])
chk(a["id"] not in [x["id"] for x in r["items"]], "sepettekini önermez")
chk(pub("GET", "/public/shop/cart-suggest?ids=").json()["items"] == [], "boş sepet")

# sipariş
call("PUT", "/shop/settings", json={"bank_accounts": [{"bank": "Ziraat", "holder": "Mağaza", "iban": "TR330006100519786457841326"}]})
rr = pub("POST", "/public/customer/register", json={"name": "Ali Veli", "phone": "0532 555 11 22", "password": "parola1234"})
CT = {"Authorization": "Bearer " + rr.json()["token"]}
def siparis(custom, pid=None):
    body = {"customer": {"name": "Ali Veli", "phone": "0532 555 11 22", "address": "Atatürk cad. no 5 Çankaya", "city": "Ankara", "district": "Çankaya"},
            "items": [{"product_id": pid or a["id"], "qty": 2, "custom": custom}], "accept_terms": True, "payment_method": "havale"}
    return pub("POST", "/public/shop/orders", json=body, headers=CT)
r = siparis({})
chk(r.status_code == 422 and "isim" in r.text.lower(), "zorunlu alan %s %s" % (r.status_code, r.text[:100]))
r = siparis({"f1": "Ayşe", "f2": "Bronz"})
chk(r.status_code == 422, "geçersiz seçim %s" % r.status_code)
r = siparis({"f1": "Ayşe", "f2": "Altın", "f3": True})
chk(r.status_code == 200, "geçerli sipariş %s %s" % (r.status_code, r.text[:120]))
j = r.json()
chk(abs(j["subtotal"] - 2 * (500 + 30 + 15)) < 0.01, "ek ücretler sunucuda toplandı: %s" % j.get("subtotal"))
o = [x for x in call("GET", "/shop/orders").json() if x["order_no"] == j["order_no"]][0]
it = o["items"][0]
chk([c["value"] for c in it["custom"]] == ["Ayşe", "Altın", "Evet"] and "Üzerine yazılacak isim: Ayşe" in it["variant"], "siparişte görünür %s" % it.get("variant"))
r = siparis({"f1": "A" * 40})
chk(r.status_code == 200 and [c["value"] for c in [x for x in call("GET", "/shop/orders").json() if x["order_no"] == r.json()["order_no"]][0]["items"][0]["custom"]][0] == "A" * 12, "uzunluk sınırlandı")
r = siparis({"f1": "Zorunlu"}, pid=b["id"])
chk(r.status_code == 200 and abs(r.json()["subtotal"] - 600) < 0.01, "tanımsız üründe ek ücret yok: %s" % r.text[:100])

# tarayıcı: ürün sayfasında alanlar, sepet, öneri
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1280, "height": 900})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    base = "http://127.0.0.1:%d/demo/%s~" % (PORT, fid)
    pg.goto(base + "/magaza/urun/" + (a.get("slug") or a["id"])); pg.wait_for_timeout(2500); pg.wait_for_selector("#okm-pz-f1", timeout=5000)
    pg.click("#okm-pa2"); pg.wait_for_timeout(300)
    chk(pg.locator("#okm-pz-f1").evaluate("e=>document.activeElement===e") or pg.evaluate("document.querySelectorAll('#okm-pz-f1').length") == 1, "zorunlu alan uyarısı")
    pg.fill("#okm-pz-f1", "Elif"); pg.select_option("#okm-pz-f2", "Gümüş"); pg.check("#okm-pz-f3"); pg.wait_for_timeout(200)
    chk("+45" in pg.inner_text("#okm-pzf").replace(" ", "").replace(",00", "") or "45" in pg.inner_text("#okm-pzf"), "ücret satırı %s" % pg.inner_text("#okm-pzf"))
    pg.click("#okm-pa2"); pg.wait_for_timeout(400)
    cart = pg.evaluate("JSON.parse(localStorage.getItem('okcart-live')||'[]')")
    chk(cart and cart[0]["price"] == 545 and cart[0]["cz"]["f1"] == "Elif" and "Elif" in cart[0]["vl"], "sepet kalemi %s" % cart)
    pg.goto(base + "/magaza#sepet"); pg.wait_for_selector("#okm-sg .pc", timeout=15000)
    chk("Zincir Bileklik" in pg.inner_text("#okm-sg"), "sepette öneri")
    # filtre kenar çubuğu
    pg.goto(base + "/magaza"); pg.wait_for_selector("input[data-ak]", timeout=15000)
    n0 = pg.locator(".pc").count()
    pg.click("input[data-ak=Malzeme][data-av=Altın]"); pg.wait_for_timeout(700)
    chk(pg.locator(".pc").count() < n0 and "Zincir Bileklik" in pg.inner_text("#okm-g"), "filtre uygulanıyor %d→%d" % (n0, pg.locator(".pc").count()))
    chk(not errs, "sayfa hatası %s" % errs[:2])
    br.close()
print("OK", ok, "FAIL", fail)
sys.exit(1 if fail else 0)
