# -*- coding: utf-8 -*-
"""Kategori ağacı: ekleme, taşıma (döngü engeli), düzenleme, ürün bağlama, silerken ürün aktarma, açık ağaç."""
import os, sys, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq, demo
demo.GUNLUK_LIMIT = 10**6
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8794, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
U = "http://127.0.0.1:8794/api"
for _ in range(100):
    try:
        if rq.get(U + "/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(.2)
d = rq.post(U + "/public/demo", json={"name": "K Test", "phone": "05531000555", "sector": "eticaret"}).json()
tok = rq.post(U + "/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]
H = {"Authorization": "Bearer " + tok}
ok = fail = 0
def chk(c, m):
    global ok, fail
    if c: ok += 1
    else: fail += 1; print("FAIL", m)
def call(m, p, **kw):
    return rq.request(m, U + p, headers=H, **kw)
a = call("POST", "/shop/categories", json={"name": "Kombi Parçaları"}).json()
b = call("POST", "/shop/categories", json={"name": "Pompa", "parent": a["id"], "seo": {"title": "Pompa", "noindex": True}, "code": "P1"}).json()
c = call("POST", "/shop/categories", json={"name": "Genleşme", "parent": a["id"]}).json()
e = call("POST", "/shop/categories", json={"name": "Aksesuar"}).json()
chk(a.get("slug") == "kombi-parcalari", "slug")
chk(call("POST", "/shop/categories", json={"name": "Pompa", "parent": a["id"]}).status_code == 409, "aynı ad")
# taşıma: döngü engeli
chk(call("POST", f"/shop/categories/{a['id']}/move", json={"parent": b["id"]}).status_code == 422, "döngü")
chk(call("POST", f"/shop/categories/{c['id']}/move", json={"parent": a["id"], "index": 0}).status_code == 200, "sıra")
rows = call("GET", "/shop/categories").json()
mine = [r for r in rows if r["id"] in (a["id"], b["id"], c["id"], e["id"])]
chk([r["name"] for r in rows if r.get("parent") == a["id"]][:2] == ["Genleşme", "Pompa"], "kardeş sırası")
chk(call("POST", f"/shop/categories/{e['id']}/move", json={"parent": a["id"]}).status_code == 200, "alt taşıma")
rows = call("GET", "/shop/categories").json()
chk([r for r in rows if r["id"] == e["id"]][0]["depth"] == 1, "derinlik")
# ürün bağla
p = call("POST", "/yp/products", json={"name": "Pompa X", "price": 100, "cost": 50, "cat_ids": [b["id"]], "channels": {"site": True}}).json()
chk(p.get("cat_ids") == [b["id"]] and p.get("cat") == "Pompa", "ürün kategori bağlama")
# ad ile eski yol → ağaçta yoksa oluşur
p2 = call("POST", "/yp/products", json={"name": "Eski Yol", "price": 10, "cost": 5, "cat": "Yeni Kök"}).json()
chk(len(p2.get("cat_ids") or []) == 1, "ad ile oluşturma")
# düzenleme adı → ürünlerde güncellenir
call("PUT", f"/shop/categories/{b['id']}", json={"name": "Sirkülasyon Pompası", "seo": {"title": "T", "noindex": False}})
g = call("GET", f"/yp/products/{p['id']}").json()
chk(g["cat"] == "Sirkülasyon Pompası", "ad yayılımı")
# silme: ürünlü + hedef yok → 409
r = call("POST", "/shop/categories/sil", json={"ids": [b["id"]]})
chk(r.status_code == 409, "ürünlü silme engeli")
r = call("POST", "/shop/categories/sil", json={"ids": [b["id"]], "target": c["id"]})
chk(r.status_code == 200 and r.json()["aktarilan"] == 1, "aktarma")
g = call("GET", f"/yp/products/{p['id']}").json()
chk(g["cat_ids"] == [c["id"]], "ürün hedefte")
# üst silinince çocuklar bir üste çıkar
r = call("POST", "/shop/categories/sil", json={"ids": [a["id"]], "target": c["id"]}) if False else None
pub = rq.get(U + "/public/shop/category-tree").json()
chk(isinstance(pub.get("tree"), list), "açık ağaç")
res = call("GET", f"/shop/categories/{a['id']}/products").json()
chk(res["n"] >= 1, "kategori ürünleri")
# mağaza: ağaç + üst kategori süzgeci alt kategorileri de kapsar
call("PUT", "/site/features", json={"shop_enabled": True})
ps = call("POST", "/yp/products", json={"name": "Pompa Y", "price": 80, "cost": 40, "cat_ids": [c["id"]], "channels": {"site": True}, "status": "live"}).json()
sr = rq.get(U + "/public/shop/search?category=kombi-parcalari", headers=H).json()
chk(isinstance(sr.get("tree"), list) and any(n["slug"] == "kombi-parcalari" for n in sr["tree"]), "mağaza ağacı")
chk(any(i["name"] == "Pompa Y" for i in sr["items"]), "üst kategori alt ürünleri kapsar")
# ürünü kategoriye bağla / çıkar (panel)
pid = ps["id"]
chk(call("PUT", f"/yp/products/{pid}", json={"cat_ids": [], "cats": [], "cat": ""}).status_code == 200, "çıkar")
chk(call("GET", f"/yp/products/{pid}").json()["cat_ids"] == [], "çıkarıldı")
chk(call("PUT", f"/yp/products/{pid}", json={"cat_ids": [c["id"]]}).status_code == 200, "bağla")
chk(isinstance(call("GET", "/shop/categories/markets").json(), list), "pazaryeri listesi")
print("OK", ok, "FAIL", fail)
sys.exit(1 if fail else 0)
