"""Siteden randevu: ekip/hizmet panelden gelir, doluluk kişi bazında, bekleyen talep de dolu sayılır, deneme (dry) kayıt yazmaz."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
from datetime import date, timedelta
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-700:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe Kaya", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    import _temiz; _temiz.bos(c, s, j)
    D = date.today() + timedelta(days=1)
    while D.weekday() == 6: D += timedelta(days=1)
    D = D.isoformat()
    def setup():
        boot_ = c.get("/api/yp/boot", headers=H).json(); S["sv"] = boot_["services"]
        r = c.post("/api/yp/staff", headers=H, json={"name": "Elif Usta"}); S["a"] = r.json()["id"]
        r = c.post("/api/yp/staff", headers=H, json={"name": "Can Usta"}); S["b"] = r.json()["id"]
        g = c.get("/api/growth/settings", headers=H).json(); g["booking"].update({"enabled": True, "start": "09:00", "end": "18:00", "slot_minutes": 60, "closed_weekdays": [6], "min_notice_hours": 0, "days_ahead": 14})
        assert c.put("/api/growth/settings", headers=H, json=g).status_code == 200
    t("hazırlık", setup)
    def info():
        r = c.get("/api/public/yp/info", headers=H); assert r.status_code == 200, r.text
        d = r.json(); names = [x["name"] for x in d["staff"]]
        assert d["enabled"] and "Elif Usta" in names and "Can Usta" in names and d["services"] and D in d["days"], d
    t("ekip ve hizmetler panelden gelir", info)
    N = [0]
    def hh():
        N[0] += 1; return dict(H, **{"x-forwarded-for": "10.0.%d.%d" % (N[0] // 250, N[0] % 250)})
    def book(sid, tm, sv=0, **k):
        return c.post("/api/public/yp/book", headers=hh(), json=dict({"name": "Zeynep Demir", "phone": "0532 111 22 33", "date": D, "time": tm, "staff_id": sid, "services": [S["sv"][sv]["id"]]}, **k))
    def slot(tm):
        r = c.get("/api/public/yp/slots?date=%s" % D, headers=H); assert r.status_code == 200, r.text
        return next(x for x in r.json()["slots"] if x["time"] == tm), r.json()
    def b1():
        r = book(S["a"], "10:00"); assert r.status_code == 200 and "iletildi" in r.json()["message"], r.text
        x, raw = slot("10:00"); assert S["a"] not in x["free"] and S["b"] in x["free"], x
        assert any(S["a"] == k for k in raw["busy"]), raw
    t("randevu iletilir ve o kişi o saatte dolu olur", b1)
    def b2():
        assert book(S["a"], "10:00").status_code == 409
        for i in c.get("/api/public/yp/info", headers=H).json()["staff"]:
            if i["id"] != S["a"]: assert book(i["id"], "10:00").status_code == 200
        x, _ = slot("10:00"); assert not x["available"] and x["free"] == [], x
        assert book("", "10:00").status_code == 409
    t("aynı kişi 409, diğer kişi serbest, ikisi de doluysa saat kapanır", b2)
    def b3():
        r = book("", "11:00"); assert r.status_code == 200 and r.json()["staff_id"], r.text
        n = len(c.get("/api/public/yp/info", headers=H).json()["staff"])
        for _ in range(n - 1): assert book("", "11:00").status_code == 200
        assert book("", "11:00").status_code == 409
    t("kişi seçilmezse boş olan atanır", b3)
    def b4():
        n0 = len(c.get("/api/yp/requests", headers=H).json()["rows"])
        r = book(S["a"], "14:00", dry=True); assert r.status_code == 200 and r.json()["dry"], r.text
        assert len(c.get("/api/yp/requests", headers=H).json()["rows"]) == n0
        x, _ = slot("14:00"); assert S["a"] in x["free"]
    t("deneme kaydı randevu yazmaz", b4)
    def b5():
        rows = c.get("/api/yp/requests", headers=H).json()["rows"]
        assert rows and all(r["stage"] == "talep" and r["staff_id"] for r in rows), rows
        assert c.post("/api/public/yp/book", headers=hh(), json={"name": "A", "phone": "1", "date": D, "time": "10:00"}).status_code == 422
        assert book(S["a"], "10:00").status_code == 409
    t("talep panele düşer, kişi/telefon doğrulanır", b5)
    def b6():
        c.put("/api/growth/settings", headers=H, json=dict(c.get("/api/growth/settings", headers=H).json(), booking=dict(c.get("/api/growth/settings", headers=H).json()["booking"], enabled=False)))
        assert book(S["a"], "15:00").status_code == 400
        assert book(S["a"], "15:00", dry=True).status_code == 200
    t("kapalıyken gerçek randevu alınmaz, deneme çalışır", b6)
print("OK", len(ok)); [print("FAIL", n, e) for n, e in bad]
sys.exit(1 if bad else 0)
