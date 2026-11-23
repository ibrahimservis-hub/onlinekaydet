"""Mağaza ödeme akışı: ödeme yöntemleri, kapıda ödeme, sunucuda tutar hesabı, iyzico güvenliği, yasal metinler."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:500]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Mağaza Firma", "email": "mg@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "mg@x.com", "sifre12345")
    def P(path): return path.replace("/shop/", f"/shop/{F}~", 1) if "/public/shop/" in path else path
    def pub(m, path, **kw): return getattr(c, m)(P(path), **kw)
    r = c.put("/api/site/features", headers=O, json={"shop_enabled": True, "customer_portal_enabled": True}); assert r.status_code == 200, r.text
    r = c.post("/api/shop/products", headers=O, json={"name": "Eşanjör", "price": 1000, "stock": 5, "category": "Eşanjör", "brand": "Baymak"}); assert r.status_code == 200, r.text
    PID = r.json()["id"]
    r = c.put("/api/shop/settings", headers=O, json={"shipping_fee": 100, "free_shipping_over": 5000, "bank_accounts": [{"bank": "Ziraat", "holder": "Mağaza", "iban": "TR330006100519786457841326"}]}); assert r.status_code == 200, r.text
    r = c.post("/api/public/customer/register", json={"name": "Ali Veli", "phone": "0532 555 11 22", "password": "parola1234"}, headers={"X-Firm": F}) if False else None
    def reg():
        rr = c.post(f"/api/public/customer/{F}~register", json={"name": "Ali Veli", "phone": "0532 555 11 22", "password": "parola1234"})
        assert rr.status_code in (200, 201), rr.text
        S["ct"] = {"Authorization": "Bearer " + rr.json()["token"]}
    t("müşteri hesabı açılır", reg)
    def order(method, qty=1, email="", extra=None):
        body = {"customer": {"name": "Ali Veli", "phone": "0532 555 11 22", "address": "Atatürk cad. no 5 Çankaya", "city": "Ankara", "district": "Çankaya", "email": email},
                "items": [{"product_id": PID, "qty": qty}], "accept_terms": True, "payment_method": method}
        body.update(extra or {}); return pub("post", "/api/public/shop/orders", json=body, headers=S["ct"])
    def info():
        r = pub("get", "/api/public/shop/info"); assert r.status_code == 200, r.text
        ids = [m["id"] for m in r.json()["payment_methods"]]
        assert ids == ["havale"], ids          # kart anahtarsız, kapıda kapalı
        assert any(d["slug"] == "mesafeli-satis-sozlesmesi" for d in r.json()["legal_docs"])
    t("yalnız açık yöntemler görünür (kart anahtarsız ve kapıda kapalıyken havale)", info)
    def closed():
        assert order("kapida_nakit").status_code == 422
        assert order("kart", email="a@b.co").status_code == 422
        assert order("").status_code == 422
        assert order("havale", extra={"accept_terms": False}).status_code == 422
    t("kapalı yöntem, anahtarsız kart, boş yöntem ve onaysız sipariş reddedilir", closed)
    def havale():
        r = order("havale", qty=2); assert r.status_code == 200, r.text
        j = r.json(); assert j["total"] == 2100.0 and j["next"] == "havale" and j["bank_accounts"], j   # 2000 + 100 kargo
        S["hv"] = j["order_no"]
        p = c.get("/api/shop/products", headers=O).json()[0]; assert p["stock"] == 3, p["stock"]
    t("havale siparişi: toplam sunucuda hesaplanır, stok düşer, IBAN döner", havale)
    def cod_toggle():
        r = c.put("/api/shop/settings", headers=O, json={"payments": {"kapida_nakit": {"enabled": True, "fee": 25}, "kapida_kart": {"enabled": True, "fee": 35}}, "cod_max_total": 3000}); assert r.status_code == 200, r.text
        r = order("kapida_nakit"); assert r.status_code == 200, r.text
        j = r.json(); assert j["total"] == 1125.0 and j["cod_fee"] == 25 and j["next"] == "kapida", j
        o = [x for x in c.get("/api/shop/orders", headers=O).json() if x["order_no"] == j["order_no"]][0]
        assert o["status"] == "onaylandi" and o["payment"]["status"] == "kapida_tahsil" and o["consent"]["terms"] and o["consent"]["version"], o
        r = order("kapida_kart", qty=3); assert r.status_code == 422, "kapıda üst sınır aşıldı: " + r.text
        sm = c.get("/api/shop/summary", headers=O).json(); assert sm["cod_pending"] == 1125.0 and sm["revenue"] == 0, sm
    t("kapıda ödeme: ücret eklenir, sipariş onaylı açılır, üst sınır uygulanır, gelir ile ayrılır", cod_toggle)
    def hold():
        r = c.put("/api/shop/settings", headers=O, json={"payments": {"kapida_nakit": {"enabled": False}, "havale": {"enabled": False}, "kapida_kart": {"enabled": False}}}); assert r.status_code == 422, "hiç yöntem açık kalmayabilir"
        r = c.put("/api/shop/settings", headers=O, json={"payments": {"kart": {"enabled": True}}}); assert r.status_code == 422, "anahtarsız kart açılamaz"
    t("tüm yöntemleri kapatma ve anahtarsız kartı açma engellenir", hold)
    def card():
        c.put("/api/firm/integrations", headers=O, json={"payment": {"provider": "iyzico", "api_key": "AK", "secret": "SK", "sandbox": "1"}})
        r = c.put("/api/shop/settings", headers=O, json={"payments": {"kart": {"enabled": True}}}); assert r.status_code == 200, r.text
        assert order("kart").status_code == 422, "e-posta zorunlu"
        r = order("kart", email="ali@ornek.com"); assert r.status_code == 200, r.text
        S["kt"] = r.json()["order_no"]; assert r.json()["next"] == "iyzico" and r.json()["total"] == 1100.0, r.json()
    t("anahtar girilince kart açılır; e-postasız kart siparişi reddedilir", card)
    def iyz():
        calls = []
        async def fake(path, body):
            calls.append((path, body))
            if "initialize" in path: return {"status": "success", "token": "TK1", "paymentPageUrl": "https://sandbox.iyzipay.com/p/TK1"}
            return {"status": "success", "paymentStatus": "SUCCESS", "paidPrice": S.get("paid", 1100.0), "currency": "TRY", "basketId": S["kt"], "paymentId": "PAY1"}
        import shop as _shop; _shop.IYZICO['call'] = fake
        r = pub("post", "/api/public/shop/pay/iyzico/init", json={"order_no": S["kt"], "phone": "0532 555 11 22"}); assert r.status_code == 200, r.text
        body = calls[0][1]; assert body["price"] == "1100.00" and body["callbackUrl"].endswith("/api/public/shop/pay/iyzico/callback") and "servisplus" not in str(body).lower(), body
        S["paid"] = 900.0                                          # eksik tutar ödendi: onaylanmamalı
        r = pub("post", "/api/public/shop/pay/iyzico/callback", data={"token": "TK1"}, follow_redirects=False); assert r.status_code == 303 and "odeme=kontrol" in r.headers["location"], r.headers
        o = [x for x in c.get("/api/shop/orders", headers=O).json() if x["order_no"] == S["kt"]][0]; assert o["status"] == "odeme_bekliyor" and o["flag"] == "odeme_tutar_uyusmazligi", o
        S["paid"] = 1100.0
        r = pub("post", "/api/public/shop/pay/iyzico/callback", data={"token": "TK1"}, follow_redirects=False); assert "odeme=ok" in r.headers["location"], r.headers
        o = [x for x in c.get("/api/shop/orders", headers=O).json() if x["order_no"] == S["kt"]][0]; assert o["status"] == "onaylandi" and o["payment"]["status"] == "odendi", o
        n = len(o["history"]); pub("post", "/api/public/shop/pay/iyzico/callback", data={"token": "TK1"}, follow_redirects=False)
        o = [x for x in c.get("/api/shop/orders", headers=O).json() if x["order_no"] == S["kt"]][0]; assert len(o["history"]) == n, "ikinci geri dönüş sipariş geçmişini çoğaltmamalı"
        r = pub("post", "/api/public/shop/pay/iyzico/init", json={"order_no": S["hv"], "phone": "0532 555 11 22"}); assert r.status_code == 409, "havale siparişi kartla ödenemez"
    t("iyzico: tutar uyuşmazlığı onaylanmaz, doğru tutar bir kez onaylanır, başka yöntem siparişi kartla ödenmez", iyz)
    def expire():
        import asyncio
        p0 = c.get("/api/shop/products", headers=O).json()[0]["stock"]
        r = order("kart", email="ali@ornek.com"); assert r.status_code == 200, r.text; no = r.json()["order_no"]
        assert c.get("/api/shop/products", headers=O).json()[0]["stock"] == p0 - 1
        async def age():
            from datetime import datetime, timezone, timedelta
            f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
            await s.db.firm(f["db"]).shop_orders.update_one({"order_no": no}, {"$set": {"created_at": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()}})
        asyncio.run(age())
        c.get("/api/shop/summary", headers=O)                       # süre dolumu bu çağrıyla da çalışır
        o = [x for x in c.get("/api/shop/orders", headers=O).json() if x["order_no"] == no][0]; assert o["status"] == "iptal", o["status"]
        assert c.get("/api/shop/products", headers=O).json()[0]["stock"] == p0, "stok geri verilmeli"
    t("kartla ödenmeyen sipariş süresi dolunca iptal olur ve stok geri gelir", expire)
    def legal():
        r = pub("get", "/api/public/shop/legal/mesafeli-satis-sozlesmesi"); assert r.status_code == 200 and "Mesafeli" in r.json()["html"], r.text
        assert c.put("/api/shop/settings", headers=O, json={"legal": {"seller_title": "Mağaza Ltd. Şti.", "address": "Ankara", "tax_no": "1234567890"}}).status_code == 200
        r = pub("get", "/api/public/shop/legal/mesafeli-satis-sozlesmesi"); assert "Mağaza Ltd. Şti." in r.json()["html"]
        a = c.get("/api/shop/legal", headers=O).json(); assert isinstance(a["missing"], list) and len(a["docs"]) == 9
        assert c.put("/api/shop/legal/gizlilik-kvkk", headers=O, json={"html": "<script>x</script>" + "a" * 60}).status_code == 422
        assert c.put("/api/shop/legal/gizlilik-kvkk", headers=O, json={"html": "<p>" + "Özel gizlilik metni. " * 5 + "</p>"}).status_code == 200
        assert "Özel gizlilik" in pub("get", "/api/public/shop/legal/gizlilik-kvkk").json()["html"]
        assert pub("get", "/api/public/shop/legal/yok").status_code == 404
    t("yasal metinler: firma bilgisiyle dolar, düzenlenir, güvensiz içerik reddedilir", legal)
    def site():
        async def go():
            f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
            await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": "p01-cine-kombi"}}, upsert=True)
            await s.db.main().firm_domains.insert_one({"id": "dm1", "domain": "magaza-test.com", "firm_id": F, "db": f["db"], "status": "yayinda"})
        c.portal.call(go)
        import domains; domains._cache["t"] = 0
        H = {"Host": "magaza-test.com"}
        r = c.get("/api/public/hosted-site?p=%2F", headers=H); assert r.status_code == 200, r.text[:200]
        assert "/mesafeli-satis-sozlesmesi" in r.text and "/iptal-iade-cayma" in r.text and "/gizlilik-kvkk" in r.text, "footer'da yasal bağlantılar olmalı"
        r = c.get("/api/public/hosted-site?p=%2Fmesafeli-satis-sozlesmesi", headers=H); assert r.status_code == 200 and "Mağaza Ltd. Şti." in r.text and "Cayma hakkı" in r.text, r.text[:300]
        c.put("/api/site/features", headers=O, json={"shop_enabled": False})
        r = c.get("/api/public/hosted-site?p=%2F", headers=H); assert "/mesafeli-satis-sozlesmesi" not in r.text, "mağaza kapalı ve e-ticaret modülü yokken satış metni görünmez"
        c.put("/api/site/features", headers=O, json={"shop_enabled": True})
    t("yayındaki sitede mağaza açıkken footer'a yasal bağlantılar eklenir, sayfalar tema içinde açılır", site)
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" FAIL", n, e)
sys.exit(1 if bad else 0)
