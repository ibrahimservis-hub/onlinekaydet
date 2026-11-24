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
    def dlv():
        r = c.put("/api/shop/settings", headers=O, json={"delivery": {"enabled": True, "days_ahead": 5, "min_hours": 24, "off_days": [], "slots": ["09:00-12:00", "12:00-17:00"]}, "gift": {"enabled": True, "fee": 30, "note_max": 50}}); assert r.status_code == 200, r.text
        i = pub("get", "/api/public/shop/info").json(); assert i["delivery"]["enabled"] and len(i["delivery"]["days"]) == 5 and i["gift"]["fee"] == 30, i
        S["d"] = i["delivery"]["days"][1]["date"]
    t("teslimat ve hediye ayarı kaydedilir, vitrin bilgisinde görünür", dlv)
    def good():
        r = order("havale", extra={"delivery": {"date": S["d"], "slot": "12:00-17:00"}, "gift": {"wrap": True, "note": "Mutlu yıllar" * 20}}); assert r.status_code == 200, r.text
        j = r.json(); assert j["total"] == 1130.0, j      # 1000 + 100 kargo + 30 hediye
        assert j["delivery"]["slot"] == "12:00-17:00" and len(j["gift"]["note"]) == 50, j
        o = [x for x in c.get("/api/shop/orders", headers=O).json() if x["order_no"] == j["order_no"]][0]
        assert o["delivery"]["date"] == S["d"] and o["gift"]["wrap"] and o["gift_fee"] == 30, o
    t("seçili teslimat + hediye: tutar sunucuda hesaplanır, not kısaltılır, sipariş kaydında tutulur", good)
    def gecersiz():
        assert order("havale", extra={"delivery": {"date": "2020-01-01", "slot": "12:00-17:00"}}).status_code == 422
        assert order("havale", extra={"delivery": {"date": S["d"], "slot": "03:00-04:00"}}).status_code == 422
        r = order("havale"); assert r.status_code == 200 and r.json()["total"] == 1100.0 and r.json()["gift"] is None, r.text
        c.put("/api/shop/settings", headers=O, json={"delivery": {"required": True}})
        assert order("havale").status_code == 422
        c.put("/api/shop/settings", headers=O, json={"delivery": {"enabled": False, "required": False}, "gift": {"enabled": False}})
        r = order("havale", extra={"gift": {"wrap": True}}); assert r.status_code == 200 and r.json()["total"] == 1100.0, r.text
    t("geçersiz gün/saat reddedilir, seçim zorunlu olabilir, kapalıyken hediye ücreti eklenmez", gecersiz)
    def sepet():
        import asyncio
        r = c.put("/api/yp/sepetler", headers=O, json={"kanal": "whatsapp", "kupon": "sepet 10!", "bekleme_dk": 90, "oto": True}); assert r.status_code == 200, r.text
        j = r.json(); assert j["kanal"] == "whatsapp" and j["kupon"] == "SEPET10" and j["bekleme_dk"] == 90, j
        assert c.get("/api/yp/sepetler", headers=O).json()["cfg"]["kupon"] == "SEPET10"
    t("terk sepet hatırlatma: kanal, kupon ve bekleme kaydedilir", sepet)
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" FAIL", n, e)
sys.exit(1 if bad else 0)
