"""SMS akışı (gerçek sunucu + sahte İleti Merkezi): atama / yolda / tamamlandı mesajları, ayar kapalıyken gitmeme, firma izolasyonu."""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; import notify
CALLS = []
class R:
    status_code = 200
    def __init__(s, j): s._j = j; s.text = json.dumps(j)
    def json(s): return s._j
def fake_post(url, json=None, **k):
    CALLS.append((url, json)); ok = json["request"]["authentication"]["hash"] == "gizli"
    return R({"response": {"status": {"code": 200 if ok else 401, "message": "ok" if ok else "Üyelik bilgileri hatalı"}, "order": {"id": "99"}}})
notify.requests.post = fake_post
ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:300]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
def wait(n, to=3):
    t0 = time.time()
    while len(CALLS) < n and time.time() - t0 < to: time.sleep(0.05)
    time.sleep(0.15)
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    c.post("/api/admin/firms", headers=A, json={"name": "Ege Kombi", "email": "hasan@egekombi.com", "password": "sifre12345", "features": {}})
    O = tok(c, "hasan@egekombi.com", "sifre12345")
    c.post("/api/technicians", headers=O, json={"email": "usta1@egekombi.com", "password": "usta12345", "name": "Hasan Demir", "phone": "05320000001", "commission_percent": 0})
    TID = c.get("/api/technicians", headers=O).json()[0]["id"]; U = tok(c, "usta1@egekombi.com", "usta12345")
    CU = c.post("/api/customers", headers=O, json={"name": "Ayşe Yılmaz", "phone": "05321112233", "address": "Bornova"}).json()
    B = c.get("/api/brands", headers=O).json()[0]
    DV = c.post("/api/devices", headers=O, json={"customer_id": CU["id"], "brand_id": B["id"], "type": "kombi", "model": "Luna 3"}).json()
    def job(): return c.post("/api/jobs", headers=O, json={"customer_id": CU["id"], "device_id": DV["id"], "fault_description": "Isıtmıyor", "assigned_technician_id": TID}).json()
    def cfgset(d): r = c.put("/api/governance/notify-settings", headers=O, json=d); assert r.status_code == 200, r.text
    def a():
        n0 = len(CALLS); job(); time.sleep(0.6); assert len(CALLS) == n0, "sağlayıcı yokken mesaj gitmemeli"
    t("sağlayıcı seçilmemişken SMS gitmez, kayıt akışı bozulmaz", a)
    cfgset({"provider": "iletimerkezi", "iletimerkezi": {"key": "k", "hash": "gizli", "sender": "EGEKOMBI"}, "customer": {"enabled": True, "channel": "sms", "events": {"assigned": True, "on_the_way": True, "done": True}}})
    def b():
        r = c.get("/api/governance/notify-settings", headers=O).json(); assert r["iletimerkezi"]["hash"] == "********", "gizli anahtar maskelenmeli"
    t("API anahtarı ekranda maskelenir", b)
    def d():
        n0 = len(CALLS); j = job(); wait(n0 + 1)
        assert len(CALLS) >= n0 + 1, "atama SMS'i gitmedi"
        url, body = CALLS[n0]; m = body["request"]["order"]["message"]
        assert url.endswith("/v1/send-sms/json") and body["request"]["order"]["sender"] == "EGEKOMBI" and body["request"]["order"]["iys"] == "0"
        assert m["receipents"]["number"] == ["5321112233"] and "Hasan" in m["text"] and "Ayşe" in m["text"], m
        S["j"] = j
    t("atama: müşteriye doğru numara/gönderici/metinle SMS gider (İleti Merkezi biçimi)", d)
    def e():
        n0 = len(CALLS)
        r = c.put(f"/api/jobs/{S['j']['id']}", headers=U, json={"status": "yolda"}); assert r.status_code == 200
        r = c.put(f"/api/jobs/{S['j']['id']}", headers=U, json={"status": "basladi"}); assert r.status_code == 200
        r = c.put(f"/api/jobs/{S['j']['id']}", headers=U, json={"status": "tamamlandi", "work_done": "ok"}); assert r.status_code == 200, r.text
        wait(n0 + 2); txt = [x[1]["request"]["order"]["message"]["text"] for x in CALLS[n0:]]
        assert any("teşekkür" in x or "tamamlandı" in x for x in txt), txt
    t("tamamlanınca müşteriye 'tamamlandı' SMS'i gider", e)
    def f():
        n0 = len(CALLS); cfgset({"customer": {"events": {"done": False, "assigned": False}}}); j = job()
        for st in ("yolda", "basladi"): c.put(f"/api/jobs/{j['id']}", headers=U, json={"status": st})
        c.put(f"/api/jobs/{j['id']}", headers=U, json={"status": "tamamlandi", "work_done": "ok"}); time.sleep(0.8)
        txt = [x[1]["request"]["order"]["message"]["text"] for x in CALLS[n0:]]
        assert not any("tamamlandı" in x for x in txt) and not any("kaydınız alındı" in x for x in txt), txt
    t("adım mesajı kapatılınca o adımda SMS gitmez", f)
    def g():
        cfgset({"iletimerkezi": {"hash": "yanlis"}, "customer": {"events": {"assigned": True}}}); n0 = len(CALLS); j = job(); wait(n0 + 1)
        assert j["status"] == "atandi", "SMS hatası kaydı bozmamalı"
        ob = c.get("/api/governance/outbox", headers=O) if False else None
    t("sağlayıcı hata dönerse kayıt akışı bozulmaz", g)
    def h():
        c.post("/api/admin/firms", headers=A, json={"name": "Baska", "email": "x@baska.com", "password": "sifre12345", "features": {}}); O2 = tok(c, "x@baska.com", "sifre12345")
        r = c.get("/api/governance/notify-settings", headers=O2).json(); assert r["provider"] == "none" and r["iletimerkezi"]["key"] == ""
    t("başka firma Ege'nin SMS ayarını/anahtarını göremez", h)
print(f"GEÇTİ {len(ok)}/{len(ok)+len(bad)}")
for a in bad: print("BAŞARISIZ", a)
