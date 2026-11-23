# -*- coding: utf-8 -*-
"""Meta: Conversions API (sipariş → Purchase, özetlenmiş kişi verisi, onay, event_id) ve katalog akışı."""
import os, sys, threading, time, hashlib
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq, demo, jwt as _jwt
import meta_capi, entg_probe
demo.GUNLUK_LIMIT = 10**6
PORT = 8797
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
U = "http://127.0.0.1:%d/api" % PORT
for _ in range(100):
    try:
        if rq.get(U + "/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(.2)
d = rq.post(U + "/public/demo", json={"name": "Meta Test", "phone": "05531000888", "sector": "eticaret"}).json()
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

SENT = []
class R:
    def __init__(s, code, j): s.status_code, s._j = code, j
    def json(s): return s._j
def fake(yontem, url, **kw):
    SENT.append((yontem, url, kw))
    if "/events" in url: return R(200, {"events_received": 1})
    return R(200, {"name": "Test Pixel", "product_count": 12})
meta_capi._istek = fake; entg_probe._istek = fake

# bağlantı denemesi
chk(call("PUT", "/yp/integrations/meta_pixel", json={"keys": {"id": "123456789012345", "token": "EAAB-test", "test_code": "TEST777"}}).json().get("ok") is True, "pixel kaydet")
r = call("POST", "/yp/integrations/meta_pixel/test").json()
chk(r.get("ok") and "Test Pixel" in r.get("msg", ""), "pixel deneme %s" % r)
_r = call("PUT", "/yp/integrations/facebook_catalog", json={"keys": {"catalog_id": "998877"}}); print("katalog", _r.status_code, _r.text[:160])
chk(_r.json().get("ok") is True, "katalog kaydet")

# katalog akışı
x = pub("GET", "/public/feed/meta.xml")
chk(x.status_code == 200 and "<g:price>" in x.text and "<g:availability>" in x.text and x.text.count("<item>") >= 3, "akış %s %s" % (x.status_code, x.text[:120]))
chk("TRY" in x.text and "<g:brand>" in x.text and "<g:link>" in x.text, "akış alanları")
call("PUT", "/yp/integrations/facebook_catalog", json={"keys": {"catalog_id": "998877"}, "on": False})
chk(pub("GET", "/public/feed/meta.xml").status_code == 404, "kapalıyken akış yok")
call("PUT", "/yp/integrations/facebook_catalog", json={"keys": {"catalog_id": "998877"}, "on": True})
chk(call("GET", "/yp/meta").json().get("capi_on") is True, "durum capi")

# sipariş → CAPI
prods = call("GET", "/shop/products").json()
pid = prods[0]["id"]
call("PUT", "/shop/settings", json={"bank_accounts": [{"bank": "Ziraat", "holder": "Mağaza", "iban": "TR330006100519786457841326"}]})
rr = pub("POST", "/public/customer/register", json={"name": "Ali Veli", "phone": "0532 555 11 22", "password": "parola1234"})
CT = {"Authorization": "Bearer " + rr.json()["token"]}
def siparis(mk):
    body = {"customer": {"name": "Ali Veli Yılmaz", "phone": "0532 555 11 22", "address": "Atatürk cad. no 5 Çankaya", "city": "Ankara", "district": "Çankaya", "email": "Ali@Test.com"},
            "items": [{"product_id": pid, "qty": 1}], "accept_terms": True, "payment_method": "havale"}
    if mk is not None: body["mk"] = mk
    return pub("POST", "/public/shop/orders", json=body, headers=CT)
r = siparis({"pz": True, "fbp": "fb.1.123.456", "fbc": "fb.1.123.IwAR", "url": "https://x.test/magaza"})
chk(r.status_code == 200, "sipariş %s %s" % (r.status_code, r.text[:200]))
no = r.json().get("order_no")
for _ in range(30):
    if any("/events" in s[1] for s in SENT): break
    time.sleep(.2)
ev = [s for s in SENT if "/events" in s[1]]
chk(len(ev) == 1, "bir olay gönderildi %d" % len(ev))
if ev:
    b = ev[0][2]["json"]; o = b["data"][0]
    chk(ev[0][1].endswith("/123456789012345/events") and b["access_token"] == "EAAB-test" and b["test_event_code"] == "TEST777", "adres, anahtar, test kodu")
    chk(o["event_name"] == "Purchase" and o["event_id"] == no and o["action_source"] == "website", "olay kimliği sipariş no")
    chk(o["user_data"]["em"] == [hashlib.sha256(b"ali@test.com").hexdigest()], "e-posta özetli ve küçük harf")
    chk(o["user_data"]["ph"] == [hashlib.sha256(b"905325551122").hexdigest()], "telefon 90'lı özetli")
    chk(o["user_data"]["fbp"] == "fb.1.123.456" and o["user_data"]["fbc"] == "fb.1.123.IwAR", "fbp/fbc")
    chk("ali@test.com" not in str(b).lower() and "5325551122" not in str(b), "düz kişi verisi yok")
    chk(o["custom_data"]["currency"] == "TRY" and o["custom_data"]["value"] > 0 and o["custom_data"]["order_id"] == no, "tutar")
# çerez reddi → gönderilmez
n0 = len([s for s in SENT if "/events" in s[1]])
siparis({"pz": False}); time.sleep(1.2)
chk(len([s for s in SENT if "/events" in s[1]]) == n0, "pazarlama çerezi reddedilince gönderilmez")
# hata siparişi bozmaz
def bozuk(yontem, url, **kw):
    if "/events" in url: return R(400, {"error": {"message": "Invalid token"}})
    return fake(yontem, url, **kw)
meta_capi._istek = bozuk
r = siparis({"pz": True}); time.sleep(1.2)
chk(r.status_code == 200, "Meta hatası siparişi bozmaz")
st = call("GET", "/yp/meta").json()
chk(any(x["event"] == "capi hata" and "Invalid token" in x["note"] for x in st["son"]), "hata günlükte %s" % st["son"])
print("OK", ok, "FAIL", fail)
sys.exit(1 if fail else 0)
