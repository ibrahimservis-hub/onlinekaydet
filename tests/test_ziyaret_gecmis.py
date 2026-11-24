"""Ziyaretçi takibi: geçmiş oturumlar ve organik özet uçları."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-500:]))
UA = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}
with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    def send(sid, ev, path="/", **k):
        d = {"sid": sid, "event": ev, "path": path, "host": "onlinekaydet.com"}; d.update(k)
        return c.post("/api/public/track", json=d, headers=UA)
    def seed():
        send("sgzsid001", "pageview", "/", referrer="https://www.google.com/", search="", title="Ana")
        send("sgzsid001", "pageview", "/fiyatlar.html", title="Fiyat")
        send("sgzsid001", "event", "/fiyatlar.html", label="whatsapp_click")
        send("sgzsid002", "pageview", "/temalar.html", referrer="https://www.bing.com/search?q=x")
        send("sgzsid003", "pageview", "/", search="?gclid=abc&utm_campaign=k1")
        send("sgzsid004", "pageview", "/", referrer="")
    t("ziyaretler kaydedilir", seed)
    def hist():
        r = c.get("/api/analytics/history?days=7", headers=A).json()
        assert r["total"] >= 4, r["total"]
        x = next(i for i in r["items"] if i["id"] == "sgzsid001")
        assert x["channel"] == "organik" and x["source_name"] == "google"
        assert [j["path"] for j in x["journey"]] == ["/", "/fiyatlar.html"], x["journey"]
        assert x["conv_whatsapp"] == 1 and x["events"][0]["type"] == "whatsapp_click"
        r2 = c.get("/api/analytics/history?days=7&channel=organik", headers=A).json()
        assert r2["total"] >= 2 and all(i["channel"] == "organik" for i in r2["items"])
        r3 = c.get("/api/analytics/history?days=7&q=temalar", headers=A).json()
        assert any(i["id"] == "sgzsid002" for i in r3["items"]) and not any(i["id"] == "sgzsid001" for i in r3["items"])
        ck = dict(c.cookies); c.cookies.clear()
        try: assert c.get("/api/analytics/history").status_code in (401, 403)
        finally: c.cookies.update(ck)
    t("geçmiş: oturum yolculuğu, kaynak süzgeci, arama", hist)
    def org():
        r = c.get("/api/analytics/organic?days=7", headers=A).json()
        k = r["kpi"]
        assert k["organic"] >= 2 and k["total"] >= 4 and 0 < k["share"] <= 100
        names = {e["name"] for e in r["engines"]}
        assert {"google", "bing"} <= names, names
        assert any(l["page"] == "/" for l in r["landing"]) and len(r["daily"]) == 7
        ck = dict(c.cookies); c.cookies.clear()
        try: assert c.get("/api/analytics/organic").status_code in (401, 403)
        finally: c.cookies.update(ck)
    t("organik: motor dağılımı, giriş sayfaları, pay", org)
print(len(ok), "geçti", len(bad), "kaldı")
for n, e in bad: print("HATA:", n, e)
sys.exit(1 if bad else 0)
