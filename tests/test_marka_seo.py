# -*- coding: utf-8 -*-
"""Marka sayfası (/magaza/marka/<adres>) ve SEO şablonları: API, sunucuda meta, sitemap, korumalar."""
import os, sys, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq, demo, jwt as _jwt
demo.GUNLUK_LIMIT = 10**6
PORT = 8797
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
U = "http://127.0.0.1:%d/api" % PORT
for _ in range(100):
    try:
        if rq.get(U + "/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(.2)
d = rq.post(U + "/public/demo", json={"name": "Marka Test", "phone": "05531000888", "sector": "eticaret"}).json()
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

def yeni(name, price, **kw):
    body = {"name": name, "price": price, "cost": 10, "stock": 20, "channels": {"site": True}, "cat": "Kombi"}
    body.update(kw)
    r = call("POST", "/yp/products", json=body); assert r.status_code == 200, r.text
    j = r.json(); return j.get("item") or j

a = yeni("Nova Kombi 24 kW", 18500, brand="Çelik Marka", model="N24")
b = yeni("Nova Kombi 28 kW", 21000, brand="Çelik Marka")
c = yeni("Duvar Tipi Klima", 15000, brand="Soğutma & Co")
d2 = yeni("Markasız Ürün", 100)

# şablon doğrulama
r = call("PUT", "/shop/seo-templates", json={"values": {"product_title": "{urun} {olmayan}"}})
chk(r.status_code == 422, "bilinmeyen değişken reddedilmeli %s" % r.status_code)
r = call("GET", "/shop/seo-templates").json()
chk(r["defaults"]["product_title"].startswith("{urun}") and all(v == "" for v in r["values"].values()), "başlangıçta boş %s" % r["values"])

# marka listesi ve sayfa
bl = pub("GET", "/public/shop/brands").json()
sl = {x["name"]: x for x in bl}
chk("Çelik Marka" in sl and sl["Çelik Marka"]["count"] == 2 and sl["Çelik Marka"]["slug"] == "celik-marka", "marka listesi %s" % bl)
chk("Soğutma & Co" in sl and sl["Soğutma & Co"]["slug"] == "sogutma-co", "özel karakter adresi %s" % [x["slug"] for x in bl])
chk(all(x["name"] for x in bl), "markasız ürün listede olmamalı")
g = pub("GET", "/public/shop/brands/celik-marka").json()
chk(g["name"] == "Çelik Marka" and g["count"] == 2 and "Çelik Marka" in g["seo_title"], "marka sayfası %s" % g)
chk(pub("GET", "/public/shop/brands/yok-boyle").status_code == 404, "olmayan marka 404")

# yönetim: içerik + SEO kaydı
adm = call("GET", "/shop/brand-pages").json()
chk(len(adm) >= 2 and adm[0]["slug"], "yönetim listesi")
r = call("PUT", "/shop/brand-pages/celik-marka", json={"desc": "Türkiye'de üretilen kombiler.", "logo": "https://ornek.com/logo.png", "seo_title": "Çelik Marka Kombi Modelleri", "seo_desc": "Özel açıklama"})
chk(r.status_code == 200, "kaydet %s" % r.text)
chk(call("PUT", "/shop/brand-pages/celik-marka", json={"logo": "javascript:alert(1)"}).status_code == 422, "tehlikeli logo reddedilmeli")
chk(call("PUT", "/shop/brand-pages/yok", json={}).status_code == 404, "olmayan marka kaydı 404")
g = pub("GET", "/public/shop/brands/celik-marka").json()
chk(g["desc"].startswith("Türkiye") and g["seo_title"] == "Çelik Marka Kombi Modelleri" and g["seo_desc"] == "Özel açıklama", "içerik yansıdı %s" % g)

# şablon: elle yazılmamış ürün şablondan başlık alır, elle yazılmış korunur
call("PUT", "/shop/seo-templates", json={"values": {"product_title": "{urun} | {kategori} | {firma}", "product_desc": "{urun} - {marka} {model} {fiyat}", "brand_title": "{marka} Ürünleri | {firma}"}})
p = pub("GET", "/public/shop/products/" + (a.get("slug") or a["id"])).json()
chk(p["seo_title"].startswith("Nova Kombi 24 kW | Kombi | "), "şablon başlığı %s" % p["seo_title"])
chk("Çelik Marka" in p["seo_desc"] and "N24" in p["seo_desc"] and "18.500 TL" in p["seo_desc"], "şablon açıklaması %s" % p["seo_desc"])
chk(p.get("brand_slug") == "celik-marka", "marka adresi ürün çıktısında")
p2 = pub("GET", "/public/shop/products/" + (b.get("slug") or b["id"])).json()
chk("{" not in p2["seo_title"] and "| |" not in p2["seo_title"] and "{" not in p2["seo_desc"], "boş değişken temizlenmeli: %s / %s" % (p2["seo_title"], p2["seo_desc"]))
call("PUT", f"/yp/products/{c['id']}", json={**c, "seo": {"title": "Elle Yazılan Başlık"}})
p3 = pub("GET", "/public/shop/products/" + (c.get("slug") or c["id"])).json()
chk(p3["seo_title"] == "Elle Yazılan Başlık", "elle yazılan öncelikli %s" % p3["seo_title"])
g = pub("GET", "/public/shop/brands/sogutma-co").json()
chk(g["seo_title"].startswith("Soğutma & Co Ürünleri | "), "marka şablonu %s" % g["seo_title"])

# marka gizleme
call("PUT", "/shop/brand-pages/sogutma-co", json={"hidden": True})
chk(pub("GET", "/public/shop/brands/sogutma-co").status_code == 404, "gizli marka 404")
chk("sogutma-co" not in [x["slug"] for x in pub("GET", "/public/shop/brands").json()], "gizli marka listede yok")

# marka filtresi mağaza aramasında
s = pub("GET", "/public/shop/search?brand=celik-marka").json()
chk(s["total"] == 2, "marka filtresi %s" % s["total"])

# sunucuda üretilen sayfa: başlık, açıklama, noindex (arama motoru HTML'i görür)
B = "http://127.0.0.1:%d/demo/%s~" % (PORT, fid)
h = rq.get(B + "/magaza/marka/celik-marka").text
chk("<title>Çelik Marka Kombi Modelleri" in h and 'content="Özel açıklama"' in h, "marka sayfası meta: %s" % h[:300].replace("\n", " "))
h = rq.get(B + "/magaza/urun/" + (a.get("slug") or a["id"])).text
chk("<title>Nova Kombi 24 kW | Kombi |" in h and "N24" in h, "ürün sayfası meta")
chk(rq.get(B + "/magaza/marka/yok-boyle").status_code == 404, "olmayan marka sayfası 404")
chk(rq.get(B + "/magaza/markalar").status_code == 200, "markalar listesi sayfası")
call("PUT", "/shop/brand-pages/celik-marka", json={"noindex": True, "seo_title": "Çelik Marka Kombi Modelleri"})
chk('noindex' in rq.get(B + "/magaza/marka/celik-marka").text, "noindex etiketi")

# sürüm içi: panel kodu ve mağaza kodu derleniyor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import marka_seo, storefront
chk(marka_seo.render("{urun} | {kategori} | {firma}", {"urun": "A", "kategori": "", "firma": "F"}, 70) == "A | F", "ayraç temizliği: %r" % marka_seo.render("{urun} | {kategori} | {firma}", {"urun": "A", "kategori": "", "firma": "F"}, 70))
chk(marka_seo.render("{urun}", {"urun": "x" * 200}, 70) == "x" * 70, "uzunluk sınırı")
chk(marka_seo.slugify("Çelik İşçilik Ğ") == "celik-iscilik-g", "slug %s" % marka_seo.slugify("Çelik İşçilik Ğ"))
chk("brandInit" in storefront.shop_page() and "/magaza/markalar" in storefront.shop_page(), "mağaza kodu marka görünümü içeriyor")
print("OK %d FAIL %d" % (ok, fail)); os._exit(1 if fail else 0)
