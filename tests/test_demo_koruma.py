"""Demo korumaları: SMS kodu, yanlış kod, kod tekrar kullanımı, saat/gün sınırları, SMS kapalıyken doğrulamasız açılış."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
import notify, demo
s = boot.server; ok = []; bad = []
sent = []
async def fake_send(db, channel, to, text, **kw):
    sent.append((to, text)); return {"status": "sent"}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-700:]))
def D(i, **kw): return dict({"name": "Ziyaret Çi", "phone": "0532%07d" % (2000000 + i), "sector": "kuafor"}, **kw)
with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    def ip(n): return {"X-Forwarded-For": "10.1.0.%d" % n}
    def sms_kapali():
        a = c.get("/api/public/demo/ayar").json(); assert a["kod"] is False and len(a["sektorler"]) > 10
        assert c.post("/api/public/demo", json=D(1), headers=ip(1)).status_code == 200
    t("sms kapalı: doğrulamasız açılır", sms_kapali)
    assert c.put("/api/governance/notify-settings", headers=A, json={"provider": "iletimerkezi", "iletimerkezi": {"key": "k", "hash": "x", "sender": "ONLINEKYDT"}}).status_code == 200
    notify.send = fake_send
    def kod_gerekli():
        assert c.get("/api/public/demo/ayar").json()["kod"] is True
        r = c.post("/api/public/demo", json=D(2), headers=ip(2)); assert r.status_code == 422 and "kod" in r.json()["detail"].lower(), r.text
    t("sms açık: kodsuz açılmaz", kod_gerekli)
    def akis():
        assert c.post("/api/public/demo/kod", json={"phone": D(3)["phone"]}, headers=ip(3)).json()["kod"] is True
        code = sent[-1][1].split(": ")[1][:6]; assert code.isdigit() and len(code) == 6
        r = c.post("/api/public/demo", json=D(3, code="000000" if code != "000000" else "111111"), headers=ip(3)); assert r.status_code == 422 and "hatalı" in r.json()["detail"]
        r = c.post("/api/public/demo", json=D(3, code=code), headers=ip(3)); assert r.status_code == 200 and r.json()["email"], r.text
        r = c.post("/api/public/demo", json=D(3, code=code), headers=ip(3)); assert r.status_code == 422, "kod ikinci kez kullanılamamalı"
    t("kod gönder, yanlış kod, doğru kod, tek kullanım", akis)
    def kod_sinir():
        p = D(4)["phone"]
        assert c.post("/api/public/demo/kod", json={"phone": p}, headers=ip(4)).status_code == 200
        r = c.post("/api/public/demo/kod", json={"phone": p}, headers=ip(4)); assert r.status_code == 429, r.text   # 45 sn bekleme
    t("kod isteği bekleme süresi", kod_sinir)
    def deneme_sinir():
        p = D(5)["phone"]; c.post("/api/public/demo/kod", json={"phone": p}, headers=ip(5))
        for _ in range(5): c.post("/api/public/demo", json=D(5, code="999999"), headers=ip(5))
        code = sent[-1][1].split(": ")[1][:6]
        r = c.post("/api/public/demo", json=D(5, code=code), headers=ip(5)); assert r.status_code == 429, r.text
    t("5 yanlış denemeden sonra kod kilitlenir", deneme_sinir)
    def gunluk():
        old = demo.GUNLUK_LIMIT; demo.GUNLUK_LIMIT = 0
        try:
            r = c.post("/api/public/demo", json=D(6, code="123456"), headers=ip(6)); assert r.status_code == 429 and "kontenjan" in r.json()["detail"], r.text
        finally: demo.GUNLUK_LIMIT = old
    t("günlük toplam sınır", gunluk)
    def bot():
        assert c.post("/api/public/demo/kod", json={"phone": D(7)["phone"], "website": "x"}).json() == {"ok": True}
    t("bot alanı", bot)
print("OK" if not bad else "BAŞARISIZ", len(ok), ok if not bad else bad)
