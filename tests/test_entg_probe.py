"""Entegrasyon denemesi gerçek uçlara gider: bakiye/hesap sorgusu, SMS göndermeden."""
import sys, os, asyncio, json
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import entg_probe as P
ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-500:]))

ISTEK = []
class Y:                                           # sahte yanıt
    def __init__(self, kod=200, govde=None, metin=""):
        self.status_code = kod; self._g = govde; self.text = metin or json.dumps(govde or {})
    def json(self):
        if self._g is None: raise ValueError("gövde yok")
        return self._g

def kur(yanit):
    def sahte(yontem, url, **kw):
        ISTEK.append((yontem, url, kw))
        return yanit(yontem, url, kw) if callable(yanit) else yanit
    P._istek = sahte
    ISTEK.clear()

def c(pid, keys):
    return asyncio.run(P.probe(pid, {"keys": keys}))

def a():
    kur(Y(200, {"balance": "134.00"}))
    o, e, m = c("verimor", {"user": "u", "pass": "p"})
    assert o and "134.00" in m, m
    assert ISTEK[0][0] == "GET" and "sms.verimor.com.tr/v2/balance" in ISTEK[0][1]
    assert ISTEK[0][2]["params"]["username"] == "u"
    assert "send" not in ISTEK[0][1], "deneme SMS göndermemeli"
t("Verimor bakiyeyi okur, SMS göndermez", a)

def b():
    kur(Y(401, {}))
    o, e, m = c("verimor", {"user": "u", "pass": "yanlis"})
    assert not o and "parola" in e.lower(), e
t("Verimor yanlış parolada anlaşılır hata verir", b)

def d():
    kur(Y(200, {"response": {"status": {"code": 200}, "balance": {"amount": "12.5", "sms": "740"}}}))
    o, e, m = c("iletimerkezi", {"user": "k", "pass": "h"})
    assert o and "12.5" in m and "740" in m, m
    assert ISTEK[0][0] == "POST" and ISTEK[0][1].endswith("/v1/get-balance/json")
    assert ISTEK[0][2]["json"]["request"]["authentication"]["key"] == "k"
t("İleti Merkezi bakiyeyi okur (TL ve SMS adedi)", d)

def e_():
    kur(Y(200, {"response": {"status": {"code": 401, "message": "Yetkisiz"}}}))
    o, er, m = c("iletimerkezi", {"user": "k", "pass": "h"})
    assert not o and "Yetkisiz" in er and "401" in er, er
t("İleti Merkezi hata kodunu ve mesajını aktarır", e_)

def f():
    kur(Y(200, {"supplierAddresses": [{"id": 1}, {"id": 2}]}))
    o, er, m = c("trendyol", {"api_key": "AK", "api_secret": "AS", "seller_id": "12345"})
    assert o and "2" in m, m
    u = ISTEK[0][1]
    assert u == "https://apigw.trendyol.com/integration/sellers/12345/addresses", u
    import base64
    assert ISTEK[0][2]["headers"]["Authorization"] == "Basic " + base64.b64encode(b"AK:AS").decode()
    assert ISTEK[0][2]["headers"]["User-Agent"] == "12345 - SelfIntegration"
t("Trendyol resmî uca Basic Auth ile sorar, adres sayısını döner", f)

def g():
    kur(Y(401, {}))
    o, er, m = c("trendyol", {"api_key": "A", "api_secret": "B", "seller_id": "1"})
    assert not o and "Satıcı No" in er, er
    kur(Y(404, {}))
    o2, er2, _ = c("trendyol", {"api_key": "A", "api_secret": "B", "seller_id": "1"})
    assert not o2 and "bulamadı" in er2, er2
t("Trendyol 401 ve 404 ayrı ayrı anlatılır", g)

def h():
    kur(Y(400, {"error": {"message": "Invalid OAuth access token"}}))
    o, er, m = c("whatsapp", {"phone_id": "123", "token": "x"})
    assert not o and "Invalid OAuth" in er, er
    kur(Y(200, {"verified_name": "Kuaför Test"}))
    o2, _e, m2 = c("whatsapp", {"phone_id": "123", "token": "x"})
    assert o2 and "Kuaför Test" in m2, m2
    assert ISTEK[0][2]["params"]["access_token"] == "x"
t("WhatsApp hesabı okunur, hata mesajı aynen gösterilir", h)

def i():
    kur(Y(200, {}))
    o, er, m = c("netgsm", {"user": "u", "pass": "p", "header": "H"})
    assert o and "canlı deneme yapılmadı" in m, m
    assert not ISTEK, "doğrulanmış ucu olmayan sağlayıcıya çağrı yapılmamalı"
t("Doğrulanmış ucu olmayan sağlayıcıda uydurma adres çağrılmaz", i)

def j():
    def patla(*a, **k): raise OSError("ağ yok")
    P._istek = patla
    o, er, m = c("verimor", {"user": "u", "pass": "p"})
    assert not o and "Bağlantı kurulamadı" in er and "ağ yok" in er, er
t("Ağ hatası çökertmez, anlaşılır mesaja çevrilir", j)

def k():
    import smtplib
    sinif = {}
    class S:
        def __init__(self, host, port, timeout=None): sinif["adres"] = (host, port)
        def ehlo(self): pass
        def starttls(self, context=None): sinif["tls"] = True
        def login(self, u, p):
            sinif["giris"] = (u, p)
            if p == "yanlis": raise smtplib.SMTPAuthenticationError(535, b"bad")
        def quit(self): pass
    eski = smtplib.SMTP; smtplib.SMTP = S
    try:
        o, er, m = asyncio.run(P.probe("smtp", {"keys": {"host": "mail.x.com", "port": "587", "user": "a@x.com", "pass": "dogru"}}))
        assert o and "oturum açıldı" in m, m
        assert sinif["adres"] == ("mail.x.com", 587) and sinif["tls"] and sinif["giris"][0] == "a@x.com"
        o2, er2, _ = asyncio.run(P.probe("smtp", {"keys": {"host": "mail.x.com", "port": "587", "user": "a@x.com", "pass": "yanlis"}}))
        assert not o2 and "kabul etmedi" in er2, er2
        o3, er3, _ = asyncio.run(P.probe("smtp", {"keys": {"host": "x", "port": "abc"}}))
        assert not o3 and "sayı olmalı" in er3, er3
    finally:
        smtplib.SMTP = eski
t("SMTP: STARTTLS ile oturum açılır, yanlış parola ve bozuk port ayrı anlatılır", k)


# ---- uç seviyesi: panelden "Bağlantıyı dene" düğmesi
from starlette.testclient import TestClient
import entg_probe
with TestClient(boot.server.app) as cl:
    j = cl.post("/api/public/demo", json={"name": "Deneme AŞ", "phone": "05524165777", "sector": "E-ticaret"}).json()
    H = {"Authorization": "Bearer " + cl.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}

    def u1():
        r = cl.put("/api/yp/integrations/verimor", headers=H, json={"keys": {"user": "u", "pass": "p", "header": "FIRMA"}, "on": True})
        assert r.status_code == 200, r.text
        kur(Y(200, {"balance": "88.00"}))
        d = cl.post("/api/yp/integrations/verimor/test", headers=H)
        assert d.status_code == 200, d.text
        v = d.json(); assert v["ok"] and "88.00" in v["msg"], v
    t("panelden denenince gerçek sorgu yapılır, bakiye panele yazılır", u1)

    def u2():
        kur(Y(401, {}))
        v = cl.post("/api/yp/integrations/verimor/test", headers=H).json()
        assert not v["ok"] and "parola" in v["msg"].lower(), v
        g = cl.get("/api/yp/integrations/verimor", headers=H).json()
        assert g["item"]["ok"] is False, "hata durumu kaydedilmeli"
    t("deneme başarısızsa hata panelde saklanır", u2)

    def u3():
        cl.put("/api/yp/integrations/netgsm", headers=H, json={"keys": {"user": "u", "pass": "p", "header": "FIRMA"}, "on": True})
        v = cl.post("/api/yp/integrations/netgsm/test", headers=H).json()
        assert v["ok"] and "canlı deneme yapılmadı" in v["msg"], v
    t("canlı ucu olmayan sağlayıcıda dürüst mesaj verilir", u3)

    def u4():
        v = cl.post("/api/yp/integrations/verimor/test", headers={"Authorization": "Bearer yok"})
        assert v.status_code in (401, 403), v.status_code
    t("deneme ucu yetkisiz erişime kapalı", u4)

print("\n".join("  ✓ " + n for n in ok))
for n, er in bad: print("  ✗ " + n + "\n" + er)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA: %d/%d" % (len(bad), len(ok) + len(bad))))
sys.exit(1 if bad else 0)
