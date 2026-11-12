"""Toplu işlemler: ürün ve siparişte çoklu seçim, fiş yazdırma, Excel'e aktarma."""
import sys, os, threading, time, socket
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn
from starlette.testclient import TestClient
from playwright.sync_api import sync_playwright

s = boot.server
ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:]))

with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "E-ticaret"}).json()
    EMAIL, PW = j["email"], j["password"]
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": EMAIL, "password": PW}).json()["token"]}
    c.post("/api/yp/sectors/eticaret", headers=H, json={})
    P = []
    for n in range(6):
        P.append(c.post("/api/yp/products", headers=H, json={
            "name": "Ürün %d" % (n + 1), "price": 100 + n * 100, "cost": 40 + n * 30, "stock": 20,
            "cat": "Gömlek" if n < 3 else "Kazak", "brand": "Nevermore"}).json()["id"])
    O = []
    for n in range(4):
        O.append(c.post("/api/yp/orders", headers=H, json={
            "channel": "site", "customer": {"name": "Müşteri %d" % (n + 1), "phone": "053211122%02d" % n,
                                            "city": "İstanbul", "address": "Kadıköy Moda Cad. 14/5"},
            "items": [{"product": P[n], "name": "Ürün %d" % (n + 1), "price": 100 + n * 100, "qty": 2}],
            "ship_fee": 49.9}).json()["item"]["id"])

    # --- sunucu tarafı
    def a():
        r = c.post("/api/yp/products/bulk", headers=H, json={"ids": P[:3], "op": "price", "percent": 10}).json()
        assert r["n"] == 3
        p0 = c.get("/api/yp/products/" + P[0], headers=H).json()
        assert p0["price"] == 110.0, p0["price"]
        r2 = c.post("/api/yp/products/bulk", headers=H, json={"ids": P[:3], "op": "sale", "percent": 20}).json()
        assert r2["n"] == 3
        p0 = c.get("/api/yp/products/" + P[0], headers=H).json()
        assert p0["sale_price"] == 88.0 and p0["discount"] == 20, p0
    t("toplu zam ve toplu indirim doğru hesaplanıyor", a)

    def b():
        c.post("/api/yp/products/bulk", headers=H, json={"ids": P[3:], "op": "stock", "add": -5})
        assert c.get("/api/yp/products/" + P[3], headers=H).json()["stock"] == 13, "20 − 2 (sipariş) − 5 = 13"
        c.post("/api/yp/products/bulk", headers=H, json={"ids": P[3:], "op": "stock", "set": 7})
        assert c.get("/api/yp/products/" + P[5], headers=H).json()["stock"] == 7
        c.post("/api/yp/products/bulk", headers=H, json={"ids": P, "op": "brand", "brand": "Moda TR"})
        assert c.get("/api/yp/products/" + P[2], headers=H).json()["brand"] == "Moda TR"
        c.post("/api/yp/products/bulk", headers=H, json={"ids": P[:2], "op": "channel", "channel": "trendyol", "on": True})
        assert "trendyol" in c.get("/api/yp/products/" + P[0], headers=H).json()["channels_on"]
    t("toplu stok, marka ve pazaryeri açma işliyor", b)

    def d():
        r = c.post("/api/yp/orders/bulk", headers=H, json={"ids": O, "op": "status", "status": "onaylandi"}).json()
        assert r["n"] == 4 and not r["skipped"], r
        r2 = c.post("/api/yp/orders/bulk", headers=H, json={"ids": O, "op": "status", "status": "kargoda"}).json()
        assert r2["n"] == 0 and len(r2["skipped"]) == 4, r2
        assert "kargo firması" in r2["skipped"][0]["why"], r2["skipped"][0]
        c.post("/api/yp/orders/bulk", headers=H, json={"ids": O, "op": "cargo", "cargo": {"firm": "aras"}})
        r3 = c.post("/api/yp/orders/bulk", headers=H, json={"ids": O, "op": "status", "status": "kargoda"}).json()
        assert r3["n"] == 4 and not r3["skipped"], r3
        o = c.get("/api/yp/orders/" + O[0], headers=H).json()["item"]
        assert o["cargo_name"] == "Aras Kargo" and o["status"] == "kargoda"
    t("toplu durum değişimi akışı zorluyor, kargosuz siparişi sebebiyle atlıyor", d)

    def e():
        r = c.post("/api/yp/orders/bulk", headers=H, json={"ids": O[:2], "op": "status", "status": "iptal"}).json()
        assert r["n"] == 2
        assert c.get("/api/yp/products/" + P[0], headers=H).json()["stock"] == 20, "iptalde stok geri dönmeli"
        r2 = c.post("/api/yp/orders/bulk", headers=H, json={"ids": O[:2], "op": "status", "status": "teslim"}).json()
        assert r2["n"] == 0 and len(r2["skipped"]) == 2, r2
    t("toplu iptalde stok geri dönüyor, iptal edilen sipariş canlanmıyor", e)

    def f():
        r = c.post("/api/yp/orders/print", headers=H, json={"ids": O[2:], "kind": "kargo"}).json()
        h = r["html"]
        assert r["n"] == 2 and h.count("class='f'") == 2, r["n"]
        assert "Kargo fişi" in h and "Aras Kargo" in h and "Kadıköy" in h
        assert "0532 111 22" in h, "telefon okunur biçimde yazılmalı"
        assert "window.print" in h
        r2 = c.post("/api/yp/orders/print", headers=H, json={"ids": O[2:], "kind": "siparis"}).json()
        assert "Sipariş fişi" in r2["html"] and "Genel toplam" in r2["html"] and "Ürün 3" in r2["html"]
        assert "Sipariş bilgisi" in r2["html"] and "Gönderici" not in r2["html"], "sipariş fişinde kargo kutusu olmaz"
        assert c.post("/api/yp/orders/print", headers=H, json={"ids": [], "kind": "kargo"}).status_code == 422
    t("toplu kargo fişi ve sipariş fişi yazdırmaya hazır geliyor", f)

    def g():
        r = c.post("/api/yp/orders/export", headers=H, json={"ids": O}).json()
        assert r["n"] == 4 and r["name"].endswith(".csv")
        assert r["csv"].startswith("﻿"), "Excel Türkçe karakter için BOM ister"
        assert "Sipariş no;Tarih" in r["csv"] and "Müşteri 1" in r["csv"] and "Aras Kargo" in r["csv"]
        assert len(r["csv"].strip().split("\n")) == 5
        r2 = c.post("/api/yp/products/export", headers=H, json={"ids": []}).json()
        assert r2["n"] == 6 and "Ürün adı;Stok kodu" in r2["csv"] and "Moda TR" in r2["csv"]
    t("sipariş ve ürün listeleri Excel'in açtığı CSV olarak iniyor", g)

    def h():
        assert c.post("/api/yp/orders/bulk", headers=H, json={"ids": [], "op": "status"}).status_code == 422
        assert c.post("/api/yp/orders/bulk", headers=H, json={"ids": O, "op": "yok"}).status_code == 422
        assert c.post("/api/yp/orders/bulk", headers=H, json={"ids": O, "op": "cargo", "cargo": {"firm": "yok"}}).status_code == 422
        assert c.post("/api/yp/products/bulk", headers=H, json={"ids": P, "op": "yok"}).status_code == 422
    t("hatalı toplu istek reddediliyor", h)

# --- tarayıcı tarafı
port = socket.socket(); port.bind(("127.0.0.1", 0)); PORT = port.getsockname()[1]; port.close()
srv = uvicorn.Server(uvicorn.Config(s.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(60):
    try:
        sk = socket.create_connection(("127.0.0.1", PORT), 0.3); sk.close(); break
    except OSError: time.sleep(0.2)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1440, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:%d/salon" % PORT); pg.wait_for_selector("#lf", timeout=15000)
    pg.fill("#lf input[name=email]", EMAIL); pg.fill("#lf input[name=password]", PW)
    pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(500)

    def i():
        pg.click("#nav a[data-r=urun]"); pg.wait_for_selector("#ulist tbody tr", timeout=8000)
        assert not pg.is_visible("#selbar-urun"), "seçim yokken çubuk görünmemeli"
        pg.check("#ulist tbody tr:nth-child(1) input[data-sel=urun]")
        pg.check("#ulist tbody tr:nth-child(2) input[data-sel=urun]")
        pg.wait_for_selector(".selbar", timeout=4000)
        assert "2 ürün seçildi" in pg.inner_text(".selbar")
        pg.check("input[data-selall=urun]"); pg.wait_for_timeout(300)
        assert "6 ürün seçildi" in pg.inner_text(".selbar")
    t("ürün listesinde tek tek ve tümünü seçme çalışıyor", i)

    def k():
        pg.click("[data-a=usel-stok]"); pg.wait_for_selector("#ubf", timeout=5000)
        pg.fill("#ubf input[name=set]", "33")
        pg.click("#ubf button.p"); pg.wait_for_timeout(1200)
        txt = pg.inner_text("#ulist")
        assert txt.count("33") >= 5, "tüm ürünlerin stoğu 33 olmalı"
        assert not pg.is_visible("#selbar-urun"), "işlem sonrası seçim bırakılmalı"
    t("toplu stok güncelleme panelden uygulanıyor", k)

    def l():
        pg.click("#nav a[data-r=siparis]"); pg.wait_for_selector("#slist tbody tr", timeout=8000)
        pg.check("input[data-selall=siparis]"); pg.wait_for_selector(".selbar", timeout=4000)
        assert "4 sipariş seçildi" in pg.inner_text(".selbar")
        opts = pg.eval_on_selector_all("#sbkargo option", "o=>o.length")
        assert opts > 5, "kargo firmaları dolmalı: %s" % opts
        pg.select_option("#sbdurum", "teslim"); pg.wait_for_timeout(1500)
        assert "Atlanan siparişler" in pg.inner_text("#ov"), "iptal edilenler gerekçesiyle gösterilmeli"
        pg.click("#ov [data-a=close]"); pg.wait_for_timeout(400)
        tx = pg.inner_text("#main")
        assert "Teslim edildi" in tx
    t("sipariş listesinde toplu durum değiştirme çalışıyor", l)

    def m():
        pg.evaluate("closeM()"); pg.wait_for_timeout(250)
        pg.check("input[data-selall=siparis]"); pg.wait_for_selector(".selbar", timeout=4000)
        with pg.context.expect_page() as pop:
            pg.click("[data-a=ssel-kargofis]")
        p2 = pop.value; p2.wait_for_load_state("domcontentloaded"); p2.wait_for_timeout(400)
        body = p2.inner_text("body")
        assert "Kargo fişi" in body and "Müşteri 3" in body, body[:200]
        p2.close()
    t("toplu kargo fişi yeni sekmede yazdırmaya hazır açılıyor", m)

    def n():
        real = [e for e in errs if "favicon" not in e]
        assert not real, real[:2]
    t("toplu işlem ekranlarında JavaScript hatası yok", n)
    br.close()
srv.should_exit = True
for x in ok: print("  ✓", x)
for x, e in bad: print("  ✗", x, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
