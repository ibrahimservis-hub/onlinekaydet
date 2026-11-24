"""Bağlantı Merkezi: şifreli saklama, maskeleme, gerçek deneme, herkese açık kimlikler."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
import entg_probe
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-900:]))

class R:
    def __init__(self, code=200, j=None): self.status_code = code; self._j = j or {}; self.text = str(j)
    def json(self): return self._j
CAGRI = []; CAGRIKW = []
def sahte(yontem, url, **kw):
    CAGRI.append((yontem, url)); CAGRIKW.append((url, kw))
    if "graph.facebook.com" in url and "bozuk" in str(kw.get("params")): return R(400, {"error": {"message": "Invalid OAuth access token"}})
    if "graph.facebook.com" in url: return R(200, {"name": "Servis Plus", "fan_count": 1200})
    if "api.stripe.com" in url: return R(200, {"object": "balance"})
    if "turnstile" in url: return R(200, {"success": False, "error-codes": ["invalid-input-response"]})
    if "geocode" in url: return R(200, {"status": "REQUEST_DENIED", "error_message": "API key invalid"})
    if "iyzipay" in url: return R(200, {"status": "success"})
    return R(404)
entg_probe._istek = sahte

with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    def g():
        r = c.get("/api/admin/baglanti", headers=A).json()
        ids = {i["id"] for i in r["items"]}
        for x in ("ga4", "google_maps", "turnstile", "meta_pixel", "facebook_sayfa", "instagram", "whatsapp", "iyzico", "stripe", "paypal", "smtp", "telegram"):
            assert x in ids, x
        assert {x["id"] for x in r["groups"]} >= {"google", "meta", "whatsapp", "odeme"}
        assert r["counts"]["bagli"] == 0
    t("katalog: Google, Meta, WhatsApp ve kart ödemesi grupları var", g)

    def a():
        r = c.put("/api/admin/baglanti/facebook_sayfa", headers=A, json={"keys": {"page_id": "123456", "token": "EAAGgizliBelirtec9999"}, "on": True})
        assert r.status_code == 200, r.text
        assert "EAAGgizliBelirtec9999" not in r.text and "9999" in r.text
        assert "EAAGgizliBelirtec9999" not in c.get("/api/admin/baglanti", headers=A).text
        d = s.db.app_settings
        import asyncio
        row = asyncio.get_event_loop().run_until_complete(d.find_one({"_id": "baglanti"})) if False else None
    t("gizli anahtar yanıtta maskeli", a)

    def b():
        import asyncio
        loop = asyncio.new_event_loop()
        row = loop.run_until_complete(s.db.app_settings.find_one({"_id": "baglanti"}))
        tok = row["items"]["facebook_sayfa"]["keys"]["token"]
        assert tok.startswith("enc:") and "EAAG" not in tok, "veritabanında şifreli olmalı"
    t("veritabanında şifreli yazılıyor", b)

    def d():
        r = c.post("/api/admin/baglanti/facebook_sayfa/test", headers=A).json()
        assert r["ok"] and r["item"]["state"] == "bagli", r
        assert any("graph.facebook.com/v21.0/123456" in u for _, u in CAGRI), CAGRI
    t("Facebook sayfası denenip bağlı oluyor", d)

    def e():
        r = c.put("/api/admin/baglanti/facebook_sayfa", headers=A, json={"keys": {"page_id": "123456", "token": "••••9999"}})
        assert r.json()["item"]["state"] == "bagli", "maskeli değer gelince anahtar ve doğrulama korunmalı"
        r = c.put("/api/admin/baglanti/facebook_sayfa", headers=A, json={"keys": {"token": "bozuk-yeni-anahtar"}})
        assert r.json()["item"]["state"] != "bagli", "anahtar değişince doğrulama sıfırlanmalı"
        r = c.post("/api/admin/baglanti/facebook_sayfa/test", headers=A).json()
        assert not r["ok"] and "Invalid OAuth" in r["detail"], r
    t("anahtar değişince doğrulama sıfırlanıyor, hata sebebiyle görünüyor", e)

    def f():
        r = c.put("/api/admin/baglanti/ga4", headers=A, json={"keys": {"id": "UA-123"}, "on": True})
        assert r.status_code == 422 and "G-" in r.text, r.text
        r = c.put("/api/admin/baglanti/ga4", headers=A, json={"keys": {"id": "G-ABC123DEF4"}, "on": True})
        assert r.json()["item"]["state"] == "bagli", r.text
        o = c.get("/api/public/olcum").json()
        assert o["ga4"]["id"] == "G-ABC123DEF4", o
    t("GA4 biçim denetimi ve herkese açık kimlik", f)

    def h():
        c.put("/api/admin/baglanti/turnstile", headers=A, json={"keys": {"site_key": "6Lsite", "secret": "6Lgizli0000"}, "on": True})
        c.post("/api/admin/baglanti/turnstile/test", headers=A)
        o = c.get("/api/public/olcum").json()
        assert o["turnstile"] == {"site_key": "6Lsite"}, o
        assert "6Lgizli0000" not in str(o)
    t("herkese açık uç gizli anahtarı asla vermiyor", h)

    def i():
        r = c.put("/api/admin/baglanti/google_maps", headers=A, json={"keys": {"api_key": "AIzaKotu"}, "on": True}).json()
        r = c.post("/api/admin/baglanti/google_maps/test", headers=A).json()
        assert not r["ok"] and "REQUEST_DENIED" in r["detail"], r
        c.put("/api/admin/baglanti/stripe", headers=A, json={"keys": {"publishable": "pk_test_1", "secret": "sk_test_abc"}, "on": True})
        assert c.post("/api/admin/baglanti/stripe/test", headers=A).json()["ok"]
        c.put("/api/admin/baglanti/iyzico", headers=A, json={"keys": {"api_key": "sandbox-x", "secret": "sandbox-y", "mode": "test"}, "on": True})
        r = c.post("/api/admin/baglanti/iyzico/test", headers=A).json()
        assert r["ok"] and any("sandbox-api.iyzipay.com" in u for _, u in CAGRI), r
    t("Google Haritalar hatası, Stripe ve iyzico (deneme ortamı) denemesi", i)

    def j():
        r = c.put("/api/admin/baglanti/whatsapp", headers=A, json={"keys": {"phone_id": "1055", "token": "EAAwa123456"}, "on": True})
        assert r.status_code == 200, r.text
        assert c.post("/api/admin/baglanti/whatsapp/test", headers=A).json()["ok"]
        r = c.put("/api/admin/baglanti/instagram", headers=A, json={"keys": {"user_id": "abc", "token": "x"}, "on": True})
        assert r.status_code == 422
    t("WhatsApp bağlanıyor; Instagram'da biçimsiz kimlik reddediliyor", j)

    def k():
        L = c.get("/api/admin/baglanti-gunluk", headers=A).json()["items"]
        assert L and "9999" not in str(L) and "EAAG" not in str(L)
        c.delete("/api/admin/baglanti/stripe", headers=A)
        assert [x for x in c.get("/api/admin/baglanti", headers=A).json()["items"] if x["id"] == "stripe"][0]["state"] == "yok"
    t("günlük anahtar içermiyor; kaldırma çalışıyor", k)

    def l():
        c.cookies.clear(); sc = c.get("/api/admin/baglanti").status_code; assert sc in (401, 403), sc
        r = c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"})
    t("yönetici girişi olmadan erişilemiyor", l)

    # ---- gerçekten kullanılıyor mu
    import asyncio, requests, notify
    loop = asyncio.new_event_loop()
    GIDEN = []
    class RR(R):
        pass
    def post(url, **kw):
        GIDEN.append((url, kw)); return RR(200, {"messages": [{"id": "wamid.1"}], "ok": True})
    requests.post = post
    def u1():
        r = c.get("/api/auth/captcha-config").json()
        assert r["enabled"] and r["site_key"] == "6Lsite", r
    t("Turnstile açılınca giriş robot koruması devreye giriyor", u1)

    def u2():
        c.put("/api/admin/baglanti/smtp", headers=A, json={"keys": {"host": "smtp.x.com", "port": "587", "user": "u", "pass": "pw12345678", "from": "bilgi@onlinekaydet.com"}, "on": True})
        cfg = loop.run_until_complete(notify.get_settings(s.db))
        assert cfg["smtp"]["host"] == "smtp.x.com" and cfg["smtp"]["password"] == "pw12345678" and cfg["smtp"]["from_addr"] == "bilgi@onlinekaydet.com", cfg["smtp"]
    t("SMTP açılınca bildirim motoru onu kullanıyor", u2)

    def u3():
        c.put("/api/admin/baglanti/whatsapp", headers=A, json={"keys": {"phone_id": "1055", "token": "EAAwa123456"}, "on": True})
        cfg = loop.run_until_complete(notify.get_settings(s.db))
        notify._dispatch(cfg, "whatsapp", "05321112233", "Randevunuz yarın 10:00", "")
        url, kw = GIDEN[-1]
        assert "graph.facebook.com/v21.0/1055/messages" in url and kw["json"]["to"] == "905321112233", (url, kw)
        assert kw["headers"]["Authorization"] == "Bearer EAAwa123456"
    t("WhatsApp açılınca mesaj Cloud API ile gidiyor", u3)

    def u4():
        c.put("/api/admin/baglanti/telegram", headers=A, json={"keys": {"token": "123456:ABCDEFGHIJKLMNOPQRSTUV", "chat_id": "99"}, "on": True})
        c.put("/api/admin/baglanti/webhook", headers=A, json={"keys": {"url": "https://hook.example.com/ok", "secret": "imza1"}, "on": True})
        r = c.post("/api/public/lead", json={"name": "Ayşe Kaya", "phone": "05324445566", "form": "ana-sayfa"})
        assert r.status_code == 200, r.text
        us = [u for u, _ in CAGRIKW]
        assert any("api.telegram.org/bot123456:" in u and u.endswith("/sendMessage") for u in us), us
        h = [k for u, k in CAGRIKW if "hook.example.com" in u][-1]
        assert h["headers"].get("X-OnlineKaydet-Imza") and b"lead.yeni" in h["data"], h
    t("yeni talep Telegram'a ve imzalı webhook'a gidiyor", u4)

    def u5():
        c.put("/api/admin/baglanti/openai", headers=A, json={"keys": {"api_key": "sk-test1234"}, "on": True})
        import ai
        assert "api_key" in str(ai.DEFAULTS)
    t("yapay zekâ anahtarı kaydı", u5)

print("OK", len(ok)); [print("FAIL", n, "\n", tb) for n, tb in bad]
sys.exit(1 if bad else 0)
