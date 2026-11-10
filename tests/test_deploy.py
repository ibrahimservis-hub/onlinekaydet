"""Dağıtım uç noktası: yalnızca GitHub raw adresi, yol kısıtı, derleme denemesi, tek eşleşmeli düzenleme."""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
import requests as _rq
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-400:]))
PAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "panel")
class Resp:
    def __init__(s, d): s.d = d; s.status_code = 200
    def json(s): return s.d
with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    U = "https://raw.githubusercontent.com/x/y/main/b.json?token=T"
    def post(bundle, url=U):
        real = _rq.get; _rq.get = lambda *a, **k: Resp(bundle)
        try: return c.post("/api/admin/deploy", headers=A, json={"url": url})
        finally: _rq.get = real
    def a():
        assert post({}, "https://evil.com/b.json").status_code == 422
        assert post({"files": {"app/../x.py": "1"}}).status_code == 422
        assert post({"files": {"etc/passwd.txt": "1"}}).status_code == 422
        assert post({"files": {"app/x.exe": "1"}}).status_code == 422
    t("yalnızca raw.githubusercontent.com ve izinli yollar", a)
    def b():
        assert post({"files": {"app/_dep_test.py": "def (:"}}).status_code == 422
        assert not os.path.exists(os.path.join(PAN, "_dep_test.py"))
    t("söz dizimi hatalı Python yazılmaz", b)
    def d():
        r = post({"files": {"app/_dep_test.txt": "merhaba dunya"}, "edits": [{"path": "app/_dep_test.txt", "old": "dunya", "new": "evren"}]}); assert r.status_code == 200, r.text
        p = os.path.join(PAN, "_dep_test.txt"); assert open(p).read() == "merhaba evren"
        r = post({"edits": [{"path": "app/_dep_test.txt", "old": "yok", "new": "x"}]}); assert r.status_code == 409
        r = post({"files": {"app/_dep_test.txt": "yeni"}}); assert open(p).read() == "yeni" and os.path.exists(p + ".bak-deploy")
        os.remove(p); os.remove(p + ".bak-deploy")
    t("dosya yazar, düzenleme tek eşleşmeyle uygulanır, yedek alır", d)
print("GEÇTİ", len(ok)); [print("  ✓", x) for x in ok]
for n, e in bad: print("HATA:", n, e)
sys.exit(1 if bad else 0)
