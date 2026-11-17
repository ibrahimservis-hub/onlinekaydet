"""Çeviri: yapay zekâ anahtarı yokken ücretsiz servisle otomatik çeviri (servis taklit edilir)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
import demo, dil; demo.GUNLUK_LIMIT = 10 ** 6
class R:
    def __init__(s, j): s._j = j
    def raise_for_status(s): pass
    def json(s): return s._j
calls = []
def fake(url, params=None, timeout=0):
    calls.append(params["q"]); return R({"responseStatus": 200, "responseData": {"translatedText": "EN:" + params["q"]}})
dil.requests.get = fake
ok = bad = 0
with TestClient(boot.server.app) as c:
    d = c.post("/api/public/demo", json={"name": "Deneme Kisi", "phone": "05530007788", "sector": "kuafor"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
    c.put("/api/yp/dil", headers=H, json={"on": True, "diller": ["en"]})
    r = c.post("/api/yp/dil/oto", headers=H, json={"lang": "en"})
    print(r.status_code, r.text[:120])
    assert r.status_code == 200 and r.json()["cevrilen"] > 0 and calls
    t = c.get("/api/yp/dil/ceviri?lang=en", headers=H); print(t.status_code)
    print("OK: ücretsiz servisle", r.json()["cevrilen"], "metin çevrildi")
