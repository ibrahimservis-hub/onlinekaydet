# -*- coding: utf-8 -*-
"""Müşteri sipariş e-postaları: olay başına bir kez, şablon değişkenleri, kapalıyken/SMTP yokken/adres yokken gitmez, deneme gönderimi."""
import os, sys, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq, demo, jwt as _jwt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import notify, musteri_mail
demo.GUNLUK_LIMIT = 10**6
GIDEN = []
def sahte(cfg, channel, to, text, subject):
    GIDEN.append({"ch": channel, "to": to, "text": text, "subject": subject}); return "ok"
notify._dispatch = sahte
PORT = 8796
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=PORT, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
U = "http://127.0.0.1:%d/api" % PORT
for _ in range(100):
    try:
        if rq.get(U + "/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(.2)
d = rq.post(U + "/public/demo", json={"name": "Mail Test", "phone": "05531000777", "sector": "eticaret"}).json()
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
def bekle(n, sn=4):
    t = time.time()
    while time.time() - t < sn and len(GIDEN) < n: time.sleep(.1)
    time.sleep(.3); return len(GIDEN)

r = call("POST", "/yp/products", json={"name": "Test Kombi", "price": 1000, "cost": 10, "stock": 20, "channels": {"site": True}, "cat": "Kombi"}); j = r.json(); a = j.get("item") or j
call("PUT", "/shop/settings", json={"bank_accounts": [{"bank": "Ziraat", "holder": "Mağaza", "iban": "TR330006100519786457841326"}]})
rr = pub("POST", "/public/customer/register", json={"name": "Ali Veli", "phone": "0532 555 11 22", "password": "parola1234"})
CT = {"Authorization": "Bearer " + rr.json()["token"]}
def siparis(email="ali@ornek.com", pm="havale"):
    body = {"customer": {"name": "Ali Veli", "phone": "0532 555 11 22", "email": email, "address": "Atatürk cad. no 5 Çankaya", "city": "Ankara", "district": "Çankaya"},
            "items": [{"product_id": a["id"], "qty": 2}], "accept_terms": True, "payment_method": pm}
    r = pub("POST", "/public/shop/orders", json=body, headers=CT); assert r.status_code == 200, r.text
    return r.json()["order_no"]
def oid(no): return [x for x in call("GET", "/shop/orders").json() if x["order_no"] == no][0]["id"]

# varsayılan: kapalı, SMTP yok → hiçbir şey gitmez
s = call("GET", "/shop/customer-mail").json()
chk(s["on"] is False and not s["smtp_ok"] and set(s["events"]) == set(musteri_mail.OLAYLAR), "başlangıç ayarı %s" % {k: s[k] for k in ("on", "smtp_ok")})
no0 = siparis()
chk(bekle(1, 1.5) == 0, "kapalıyken e-posta gitmez")

# doğrulama
r = call("PUT", "/shop/customer-mail", json={"on": True, "events": {"kargoya_verildi": {"on": True, "subject": "x", "body": "{yok}"}}})
chk(r.status_code == 422 and "yok" in r.text, "bilinmeyen değişken reddedilmeli %s" % r.status_code)

# açık ama SMTP yok → gitmez, kayıtta 'E-posta ayarı yok'
r = call("PUT", "/shop/customer-mail", json={"on": True, "events": {}}); chk(r.status_code == 200 and r.json()["on"], "açıldı %s" % r.text[:100])
no1 = siparis()
chk(bekle(1, 1.5) == 0, "SMTP yokken gitmez")
chk(any(x["status"] == "smtp_yok" for x in call("GET", "/shop/customer-mail/log").json()), "log: smtp_yok")
chk(call("POST", "/shop/customer-mail/test", json={"event": "iptal", "to": "ben@ornek.com"}).status_code == 422, "SMTP yokken deneme reddedilir")

# SMTP girildi
r = call("PUT", "/governance/notify-settings", json={"smtp": {"host": "smtp.ornek.com", "port": 587, "user": "u", "password": "p", "from_addr": "magaza@ornek.com", "tls": True}}); assert r.status_code == 200, r.text
chk(call("GET", "/shop/customer-mail").json()["smtp_ok"], "smtp_ok")
n = len(GIDEN)
no2 = siparis()
chk(bekle(n + 1) == n + 1, "sipariş alındı e-postası gitmeli (%d)" % len(GIDEN))
m = GIDEN[-1]
chk(m["ch"] == "email" and m["to"] == "ali@ornek.com" and no2 in m["subject"] and "Ali," in m["text"] and no2 in m["text"] and "2 x" in m["text"] and "2.000 TL" in m["text"], "alındı içeriği %s" % m)
chk("{" not in m["text"] and "{" not in m["subject"], "çözülmemiş değişken kalmamalı")

# durum değişimleri: onay → kargo (takip no) → teslim; her biri bir kez
i2 = oid(no2); n = len(GIDEN)
call("PUT", f"/shop/orders/{i2}", json={"status": "onaylandi"}); chk(bekle(n + 1) == n + 1 and "onaylandı" in GIDEN[-1]["subject"], "onay e-postası")
call("PUT", f"/shop/orders/{i2}", json={"status": "onaylandi"}); bekle(n + 2, 1.2); chk(len(GIDEN) == n + 1, "aynı durum tekrar gitmez")
n = len(GIDEN)
call("PUT", f"/shop/orders/{i2}", json={"status": "kargoda", "carrier": "Aras Kargo", "tracking_no": "ARS123456"})
chk(bekle(n + 1) == n + 1 and "kargoya verildi" in GIDEN[-1]["subject"] and "ARS123456" in GIDEN[-1]["text"] and "Aras Kargo" in GIDEN[-1]["text"], "kargo e-postası takip no ile %s" % GIDEN[-1])
n = len(GIDEN)
call("PUT", f"/shop/orders/{i2}", json={"status": "teslim_edildi"}); chk(bekle(n + 1) == n + 1 and "teslim edildi" in GIDEN[-1]["subject"], "teslim e-postası")
n = len(GIDEN)
call("PUT", f"/shop/orders/{i2}", json={"status": "kargoda"}); call("PUT", f"/shop/orders/{i2}", json={"status": "teslim_edildi"}); bekle(n + 2, 1.2)
chk(len(GIDEN) == n + 1 or len(GIDEN) == n, "geri-ileri geçişte kargo/teslim tekrar gitmez (+%d)" % (len(GIDEN) - n))

# tek olayı kapat; şablonu özelleştir; iptal
ev = call("GET", "/shop/customer-mail").json()["events"]
ev["iptal"]["subject"] = "{firma} iptal: {siparis_no}"; ev["iptal"]["body"] = "Sayın {ad}, {siparis_no} iptal."
ev["siparis_alindi"]["on"] = False
call("PUT", "/shop/customer-mail", json={"on": True, "events": ev})
n = len(GIDEN); no3 = siparis(); bekle(n + 1, 1.2); chk(len(GIDEN) == n, "kapatılan olay gitmez")
call("PUT", f"/shop/orders/{oid(no3)}", json={"status": "iptal"}); chk(bekle(n + 1) == n + 1 and GIDEN[-1]["text"] == "Sayın Ali, %s iptal." % no3 and no3 in GIDEN[-1]["subject"], "özel şablonla iptal %s" % GIDEN[-1])

# e-posta adresi yoksa / geçersizse gitmez
n = len(GIDEN); no4 = siparis(email=""); bekle(n + 1, 1.2); chk(len(GIDEN) == n, "adres yoksa gitmez")

# deneme gönderimi
n = len(GIDEN)
r = call("POST", "/shop/customer-mail/test", json={"event": "kargoya_verildi", "to": "ben@ornek.com", "template": {"subject": "Deneme {siparis_no}", "body": "Merhaba {ad} {takip_no}"}})
chk(r.status_code == 200 and len(GIDEN) == n + 1 and GIDEN[-1]["to"] == "ben@ornek.com" and GIDEN[-1]["subject"].startswith("[Deneme] Deneme SP-0001") and "Ayşe 123456789" in GIDEN[-1]["text"], "deneme %s %s" % (r.status_code, GIDEN[-1:]))
chk(call("POST", "/shop/customer-mail/test", json={"event": "iptal", "to": "yanlis"}).status_code == 422, "geçersiz adres")
chk(call("POST", "/shop/customer-mail/test", json={"event": "yok", "to": "a@b.co"}).status_code == 422, "geçersiz olay")

# panelden girilen sipariş (yp_orders) + iade
n = len(GIDEN)
r = call("POST", "/yp/orders", json={"customer": {"name": "Veli Can", "phone": "05321112233", "email": "veli@ornek.com"}, "items": [{"product": a["id"], "name": "Test Kombi", "qty": 1, "price": 1000}], "channel": "telefon"})
assert r.status_code == 200, r.text
yo = (r.json().get("item") or r.json()); yid = yo["id"]
call("POST", f"/yp/orders/{yid}/status", json={"status": "onaylandi"})
chk(bekle(n + 1) == n + 1 and GIDEN[-1]["to"] == "veli@ornek.com" and "onaylandı" in GIDEN[-1]["subject"], "panel siparişi onay e-postası %s" % GIDEN[-1:])
call("PUT", f"/yp/orders/{yid}", json={"cargo": {"firm": "aras", "code": "YP998877"}})
n = len(GIDEN)
r = call("POST", f"/yp/orders/{yid}/status", json={"status": "kargoda"}); assert r.status_code == 200, r.text
chk(bekle(n + 1) == n + 1 and "YP998877" in GIDEN[-1]["text"] and "Aras Kargo" in GIDEN[-1]["text"], "panel kargo e-postası %s" % GIDEN[-1:])
n = len(GIDEN)
call("POST", f"/yp/orders/{yid}/status", json={"status": "teslim"})
r = call("POST", "/yp/returns", json={"order": yid, "items": [{"product": a["id"], "qty": 1, "reason": "diger"}]}); assert r.status_code == 200, r.text
rid = r.json()["item"]["id"]
n = len(GIDEN)
call("POST", f"/yp/returns/{rid}/state", json={"state": "onay"})
chk(bekle(n + 1) == n + 1 and "iade talebiniz onaylandı" in GIDEN[-1]["subject"] and "1.000 TL" in GIDEN[-1]["text"], "iade onay e-postası %s" % GIDEN[-1:])
n = len(GIDEN)
call("POST", f"/yp/returns/{rid}/state", json={"state": "tamam", "refund": 1000})
chk(bekle(n + 1) == n + 1 and "iade ödemeniz yapıldı" in GIDEN[-1]["subject"], "iade ödendi e-postası")

# yetkisiz erişim
chk(rq.get(U + "/shop/customer-mail").status_code in (401, 403), "yetkisiz okunamaz")

# birim: doldur ve satırlar
chk(musteri_mail.doldur("A {ad} {yok}\n\n\n\nB", {"ad": "X"}) == "A X\n\nB", "doldur %r" % musteri_mail.doldur("A {ad} {yok}\n\n\n\nB", {"ad": "X"}))
chk(musteri_mail.tl(1234.5) == "1.234,5 TL" and musteri_mail.tl(100) == "100 TL", "tl biçimi %s" % musteri_mail.tl(1234.5))
print("OK %d FAIL %d" % (ok, fail)); os._exit(1 if fail else 0)
