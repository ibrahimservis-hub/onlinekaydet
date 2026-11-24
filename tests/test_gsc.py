"""Search Console bağlantısı: ayar kaydı (anahtar geri dönmez), veri çekme (Google sahte), hata iletileri."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-500:]))
key = rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
SA = {"client_email": "okr@proje.iam.gserviceaccount.com", "private_key": key, "type": "service_account"}
import gsc
class R:
    def __init__(s, code, j): s.status_code = code; s._j = j; s.headers = {"content-type": "application/json"}
    def json(s): return s._j
MODE = {"code": 200}
def fake_post(url, **k):
    if "oauth2.googleapis.com" in url: return R(200, {"access_token": "tok", "expires_in": 3600})
    if MODE["code"] != 200: return R(MODE["code"], {})
    dim = k["json"]["dimensions"][0]
    if dim == "query": return R(200, {"rows": [{"keys": ["servis programı"], "clicks": 12, "impressions": 300, "ctr": 0.04, "position": 7.2}]})
    if dim == "page": return R(200, {"rows": [{"keys": ["https://onlinekaydet.com/"], "clicks": 20, "impressions": 500, "ctr": 0.04, "position": 5.0}]})
    return R(200, {"rows": [{"keys": ["2026-11-20"], "clicks": 5, "impressions": 100, "ctr": .05, "position": 6}, {"keys": ["2026-11-21"], "clicks": 15, "impressions": 400, "ctr": .0375, "position": 5}]})
gsc.requests.post = fake_post
with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    def a():
        assert c.get("/api/admin/gsc/ayar", headers=A).json()["configured"] is False
        assert c.get("/api/analytics/gsc", headers=A).json() == {"configured": False}
        assert c.post("/api/admin/gsc/ayar", headers=A, json={"site": "kötü adres", "sa_json": json.dumps(SA)}).status_code == 422
        assert c.post("/api/admin/gsc/ayar", headers=A, json={"site": "sc-domain:onlinekaydet.com", "sa_json": "{}"}).status_code == 422
    t("ayar yokken boş; geçersiz giriş reddedilir", a)
    def b():
        r = c.post("/api/admin/gsc/ayar", headers=A, json={"site": "sc-domain:onlinekaydet.com", "sa_json": json.dumps(SA)})
        assert r.status_code == 200, r.text
        g = c.get("/api/admin/gsc/ayar", headers=A).json()
        assert g["configured"] and g["client_email"] == SA["client_email"] and "private_key" not in json.dumps(g)
    t("kayıt: anahtar panele geri dönmez", b)
    def d():
        v = c.get("/api/analytics/gsc?days=28", headers=A).json()
        assert v["configured"] and v["kpi"]["clicks"] == 20 and v["kpi"]["impressions"] == 500
        assert v["queries"][0]["name"] == "servis programı" and v["queries"][0]["ctr"] == 4.0
        assert [x["label"] for x in v["daily"]] == ["11.20", "11.21"] and v["pages"][0]["clicks"] == 20
    t("veri: kelimeler, sayfalar, günlük seri", d)
    def e():
        gsc._CACHE.clear(); MODE["code"] = 403
        r = c.get("/api/analytics/gsc?days=28", headers=A)
        assert r.status_code == 403 and "okr@proje" in r.text, r.text
        gsc._CACHE.clear(); MODE["code"] = 404
        assert c.get("/api/analytics/gsc?days=28", headers=A).status_code == 404
        MODE["code"] = 200
    t("erişim yok / mülk yok iletileri", e)
    def f():
        assert c.delete("/api/admin/gsc/ayar", headers=A).json()["ok"]
        assert c.get("/api/admin/gsc/ayar", headers=A).json()["configured"] is False
    t("bağlantı kaldırılır", f)
print(len(ok), "geçti", len(bad), "kaldı")
for n, e in bad: print("HATA:", n, e)
sys.exit(1 if bad else 0)
