"""Sahip tarafı: sektör kurulumu, hoş geldin SMS, abonelik/ödeme, genel bakış, müdahale, otomatik açılma kuralları, bağlantı testi."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from datetime import datetime, timedelta, timezone
from starlette.testclient import TestClient
s = boot.server; import notify
CALLS = []
class R:
    status_code = 200
    def __init__(s, j): s._j = j; s.text = json.dumps(j)
    def json(s): return s._j
def fake_post(url, json=None, **k):
    CALLS.append((url, json)); good = json["request"]["authentication"]["hash"] == "gizli"
    st = {"code": 200 if good else 401, "message": "ok" if good else "Üyelik bilgileri hatalı"}
    if url.endswith("get-balance/json"): return R({"response": {"status": st, "balance": {"amount": "10", "sms": "250"}}})
    return R({"response": {"status": st, "order": {"id": "7"}}})
notify.requests.post = fake_post
ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:300]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    run = c.portal.call
    mainx = lambda coro_fn: run(coro_fn)
    # platform SMS ayarı (sahip): hoş geldin ve hatırlatma bununla gider
    assert c.put("/api/governance/notify-settings", headers=A, json={"provider": "iletimerkezi", "iletimerkezi": {"key": "k", "hash": "gizli", "sender": "ONLINEKYDT"}}).status_code == 200
    def a():
        r = c.post("/api/admin/firms", headers=A, json={"name": "Ege Kombi", "email": "hasan@egekombi.com", "password": "sifre12345", "phone": "05321112233",
                                                      "contact_name": "Hasan Yıldız", "package": "profesyonel", "sector": "kombi", "usage_days": 30}); assert r.status_code == 200, r.text
        S["f"] = r.json(); st = r.json()["setup"]; assert st["sector"]["models"] >= 10 and st["sector"]["checklist"] == 6 and st["welcome"] == "sent", st
        S["O"] = tok(c, "hasan@egekombi.com", "sifre12345")
    t("sektör seçerek firma aç: katalog+kontrol listesi kuruldu, hoş geldin SMS'i gitti", a)
    def b():
        cat = c.get("/api/catalog", headers=S["O"]).json(); assert any(x["brand"] == "Baymak" for x in cat) and all(x["type"] == "kombi" for x in cat)
        ss = c.get("/api/service-settings", headers=S["O"]).json(); assert ss["foto_once"] == "zorunlu" and ss["foto_sonra"] == "zorunlu"
        cl = c.get("/api/checklists/templates", headers=S["O"]).json(); assert len(cl) == 1 and cl[0]["device_type"] == "kombi"
        S["n"] = len(cat)
    t("firma içi veri sektöre göre geldi (katalog, foto kuralı, kontrol listesi)", b)
    def d():
        w = [x for x in CALLS if "OnlineKaydet hesabınız" in json.dumps(x[1], ensure_ascii=False)]; assert w, "hoş geldin çağrısı yok"
        m = w[0][1]["request"]["order"]["message"]; assert m["receipents"]["number"] == ["5321112233"] and "hasan@egekombi.com" in m["text"] and "sifre12345" in m["text"]
        async def ob(): return await s.db.main().outbox.find_one({"kind": "firm_welcome"}, {"_id": 0})
        o = c.portal.call(ob); assert "sifre12345" not in o["text"] and "********" in o["text"], "şifre kayıtta maskelenmeli"
    t("hoş geldin mesajı doğru numara/bilgi ile gider, şifre kayıtta maskelenir", d)
    def e():
        r = c.post(f"/api/admin/firms/{S['f']['id']}/sector", headers=A, json={"sector": "kombi"}); assert r.status_code == 200 and r.json()["models"] == 0, "tekrar uygulama kayıt çoğaltmamalı"
        assert len(c.get("/api/catalog", headers=S["O"]).json()) == S["n"]
        assert c.post(f"/api/admin/firms/{S['f']['id']}/sector", headers=A, json={"sector": "uydurma"}).status_code == 400
        assert c.post("/api/admin/firms", headers=A, json={"name": "Y Firma", "email": "y@y.com", "password": "sifre12345", "sector": "uydurma"}).status_code == 400
    t("sektör şablonu tekrar uygulanınca çoğalmaz; bilinmeyen sektör reddedilir", e)
    def f():
        fid = S["f"]["id"]; before = c.get("/api/admin/firms", headers=A).json()["firms"][0]["expires_at"]
        r = c.post(f"/api/admin/firms/{fid}/payments", headers=A, json={"amount": 1500, "extend_days": 30, "note": "Yıllık"}); assert r.status_code == 200, r.text
        assert r.json()["expires_at"] > before
        assert c.post(f"/api/admin/firms/{fid}/payments", headers=A, json={"amount": -5}).status_code == 400
        assert len(c.get(f"/api/admin/firms/{fid}/payments", headers=A).json()) == 1
    t("ödeme kaydı süreyi uzatır; geçersiz tutar reddedilir", f)
    def g():
        fid = S["f"]["id"]; c.put(f"/api/admin/firms/{fid}", headers=A, json={"status": "askida"}); assert c.get("/api/jobs", headers=S["O"]).status_code in (401, 403)
        r = c.post(f"/api/admin/firms/{fid}/payments", headers=A, json={"amount": 100, "extend_days": 10}); assert r.status_code == 200
        S["O"] = tok(c, "hasan@egekombi.com", "sifre12345"); assert c.get("/api/jobs", headers=S["O"]).status_code == 200, "ödeme sonrası firma açılmalı"
    t("askıdaki firma ödeme gelince yeniden açılır", g)
    def h():
        c.post("/api/admin/firms", headers=A, json={"name": "Yakın Bitiş", "email": "y1@y.com", "password": "sifre12345", "phone": "05320000009", "usage_days": 5})
        c.post("/api/admin/firms", headers=A, json={"name": "Süresi Dolmuş", "email": "y2@y.com", "password": "sifre12345", "phone": "05320000008", "usage_days": 5})
        async def force(): await s.db.main().firms.update_one({"login_email": "y2@y.com"}, {"$set": {"expires_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()}})
        c.portal.call(force)
        r = c.get("/api/admin/subscriptions?days=14", headers=A).json(); assert [x["name"] for x in r["expiring"]] == ["Yakın Bitiş"] and [x["name"] for x in r["expired"]] == ["Süresi Dolmuş"], r
    t("abonelik listesi: yaklaşan ve dolmuş firmalar ayrı", h)
    def i():
        n0 = len(CALLS); r = c.post("/api/admin/subscriptions/remind", headers=A, json={"days": 14}).json(); assert r["sent"] == 2, r
        txt = " ".join(json.dumps(x[1], ensure_ascii=False) for x in CALLS[n0:]); assert "Yakın Bitiş" in txt and "doldu" in txt
        assert c.post("/api/admin/subscriptions/remind", headers=A, json={"days": 14}).json()["sent"] == 0, "3 gün içinde tekrar gönderilmemeli"
    t("süre hatırlatma SMS'i gider, aynı firmaya tekrar tekrar gitmez", i)
    def j():
        r = c.get("/api/admin/overview", headers=A).json()
        assert r["firms"] == 3 and r["suspended"] == 0 and r["expired"] == 1 and r["expiring_14d"] == 1 and r["revenue_30d"] == 1600 and r["packages"].get("profesyonel") == 1 and r["sectors"].get("kombi") == 1, r
    t("genel bakış sayıları doğru (firma, süre, gelir, paket, sektör)", j)
    def k():
        fid = S["f"]["id"]; r = c.put(f"/api/admin/firms/{fid}/service-settings", headers=A, json={"imza": {"enabled": False}}); assert r.status_code == 200 and r.json()["imza"]["enabled"] is False
        assert c.get("/api/service-settings", headers=S["O"]).json()["imza"]["enabled"] is False
        log = c.get("/api/firm/owner-edits", headers=S["O"]).json(); assert log and log[-1]["keys"] == ["imza"], log
        assert c.put(f"/api/admin/firms/{fid}/service-settings", headers=S["O"], json={"imza": {"enabled": True}}).status_code == 403
    t("sahip firma adına ayar düzenler; firma değişikliği ve kaydı görür; firma sahip ucuna giremez", k)
    def l():
        cp = c.get("/api/firm/capabilities", headers=S["O"]).json()
        assert cp["pdf_phone"]["state"] == "acik" and cp["pdf_logo"]["state"] == "kapali" and cp["sms"]["state"] == "kapali" and cp["card_payment"]["state"] == "kapali", cp
    t("otomatik kurallar: telefon girili→açık; logo/SMS/ödeme boş→kapalı", l)
    def m():
        O = S["O"]; assert c.put("/api/governance/notify-settings", headers=O, json={"provider": "iletimerkezi", "iletimerkezi": {"key": "k", "hash": "yanlis", "sender": "EGE"}}).status_code == 200
        r = c.post("/api/firm/test-sms", headers=O, json={}).json(); assert r["ok"] is False and "doğrulanamadı" in r["detail"], r
        assert c.get("/api/firm/capabilities", headers=O).json()["sms"]["state"] == "dogrulanmadi"
        c.put("/api/governance/notify-settings", headers=O, json={"iletimerkezi": {"hash": "gizli"}})
        r = c.post("/api/firm/test-sms", headers=O, json={}).json(); assert r["ok"] is True and r["balance"] == "250", r
        assert c.get("/api/firm/capabilities", headers=O).json()["sms"]["state"] == "acik"
        assert c.post("/api/firm/test-sms", headers=S["O"], json={}).status_code == 200
    t("SMS bağlantı testi: yanlış anahtar reddedilir; doğru anahtarda bakiye döner ve özellik açılır", m)
    def n():
        O = S["O"]; r = c.put("/api/firm/integrations", headers=O, json={"payment": {"provider": "iyzico", "api_key": "AK123", "secret": "SK456"}}); assert r.status_code == 200
        assert r.json()["payment"]["api_key"] == "********" and r.json()["payment"]["provider"] == "iyzico"
        assert c.get("/api/firm/capabilities", headers=O).json()["card_payment"]["state"] == "dogrulanmadi", "doğrulama yapılmadan 'açık' denmemeli"
        c.put("/api/firm/integrations", headers=O, json={"payment": {"provider": "iyzico", "api_key": "********", "secret": "********"}})
        async def raw():
            fm = await s.db.main().firms.find_one({"login_email": "hasan@egekombi.com"}); return (await s.db.firm(fm["db"]).app_settings.find_one({"_id": "integrations"}))["payment"]
        p = c.portal.call(raw); assert p["api_key"] == "AK123" and p["secret"] == "SK456", "maskeli değer gerçek anahtarı ezmemeli"
        assert c.put("/api/firm/integrations", headers=O, json={"payment": {"provider": "bilinmeyen"}}).status_code == 400
    t("ödeme bilgileri maskelenir, maske eski anahtarı bozmaz, doğrulanmadan 'açık' denmez", n)
    def o():
        for url in ("/api/admin/overview", "/api/admin/subscriptions", "/api/admin/sectors", "/api/admin/packages"):
            assert c.get(url, headers=S["O"]).status_code == 403, url
    t("firma yöneticisi sahip uçlarının hiçbirine giremez", o)
print(f"GEÇTİ {len(ok)}/{len(ok)+len(bad)}")
for a in bad: print("BAŞARISIZ", a)
