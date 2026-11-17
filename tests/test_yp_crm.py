"""Panel: müşteri veri tabanı (arama, süzgeç, sıralama, ayrıntı) ve randevu listesi."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-600:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe Kaya", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    import _temiz; _temiz.bos(c, s, j)
    from datetime import date, timedelta
    def day(n): return (date.today() + timedelta(days=n)).isoformat()
    st1 = c.post("/api/yp/staff", headers=H, json={"name": "Elif"}).json()["id"]
    st2 = c.post("/api/yp/staff", headers=H, json={"name": "Can"}).json()["id"]
    def mk(name, ph, d, tm, st, svc, price, stage=None, pay=0, note=""):
        r = c.post("/api/yp/appts", headers=H, json={"name": name, "phone": ph, "date": d, "time": tm, "staff_id": st, "note": note,
                                                      "items": [{"name": svc, "price": price, "dur": 30}], "force": True}); assert r.status_code == 200, r.text
        i = r.json()["id"]
        if stage: assert c.post("/api/yp/appts/%s/stage" % i, headers=H, json={"to": stage}).status_code == 200
        if pay: assert c.post("/api/yp/appts/%s/pay" % i, headers=H, json={"amount": pay, "method": "Nakit"}).status_code == 200, "pay"
        return i
    # Zeynep: 3 tamamlanan (düzenli), son 5 gün önce, 1 yaklaşan
    for k, d in enumerate((-70, -30, -5)): mk("Zeynep Demir", "05321112233", day(d), "10:%02d" % (k * 5), st1, "Saç boyama", 1000, "tamamlandi", 1000)
    mk("Zeynep Demir", "05321112233", day(3), "11:00", st1, "Fön", 300)
    # Merve: tek ziyaret 90 gün önce, ödemenin yarısı alınmış -> kayıp + borç
    mk("Merve Aydın", "05443334455", day(-90), "12:00", st2, "Kesim", 600, "tamamlandi", 200)
    # Selin: gelmedi
    i_g = mk("Selin Koç", "05556667788", day(-2), "14:00", st2, "Manikür", 400, "gelmedi")
    def a():
        r = c.get("/api/yp/customers", headers=H).json(); assert r["total"] == 3 and r["all"] == 3, r
        z = [x for x in r["rows"] if x["phone"] == "5321112233"][0]
        assert z["n"] == 3 and z["spent"] == 3000 and z["avg"] == 1000 and z["fav"] == "Saç boyama" and z["next"] == day(3) and "duzenli" in z["segs"] and "yaklasan" in z["segs"], z
        assert r["counts"]["duzenli"] == 1 and r["counts"]["kayip"] == 1 and r["counts"]["borc"] == 1 and r["counts"]["gelmedi"] == 1, r["counts"]
    t("müşteri özeti: ziyaret, harcama, ortalama, sık hizmet, sıradaki, bölümler", a)
    def b():
        g = lambda **k: c.get("/api/yp/customers", headers=H, params=k).json()
        assert [x["name"] for x in g(q="zeynep")["rows"]] == ["Zeynep Demir"]
        assert g(q="0544 333")["total"] == 1                       # telefonla, boşluklu
        assert g(q="kesim")["total"] == 1                          # hizmet adıyla
        assert [x["name"] for x in g(seg="kayip")["rows"]] == ["Merve Aydın"]
        assert g(seg="borc")["rows"][0]["balance"] == 400
        assert g(staff=st2)["total"] == 2 and g(svc="Fön")["total"] == 0 and g(svc="Kesim")["total"] == 1
        assert [x["name"] for x in g(sort="spent")["rows"]][0] == "Zeynep Demir"
        assert [x["name"] for x in g(sort="name")["rows"]] == ["Merve Aydın", "Selin Koç", "Zeynep Demir"]
        assert len(g(limit=2)["rows"]) == 2 and g(limit=2, offset=2)["rows"][0]["name"]
    t("müşteri arama, süzgeç, sıralama, sayfalama", b)
    def d():
        r = c.get("/api/yp/customers/5321112233", headers=H).json()
        assert len(r["history"]) == 4 and r["stats"]["n"] == 3 and r["stats"]["svc"][0] == ["Saç boyama", 3], r["stats"]
        assert c.put("/api/yp/customers/5321112233", headers=H, json={"note": "Kızıl ton", "name": "Zeynep D."}).status_code == 200
        assert c.get("/api/yp/customers", headers=H, params={"q": "kızıl"}).json()["total"] == 1
    t("müşteri ayrıntısı ve not/ad kaydı, notta arama", d)
    def e():
        f = lambda **k: c.get("/api/yp/appts/find", headers=H, params=k).json()
        assert f()["total"] == 6
        assert f(stage="tamamlandi")["total"] == 4 and f(stage="gelmedi")["total"] == 1 and f(stage="acik")["total"] == 1
        assert f(stage="odeme")["total"] == 1 and f(stage="odeme")["sum"]["balance"] == 400
        assert f(a=day(0), order="asc")["total"] == 1 and f(b=day(-1))["total"] == 5
        assert f(q="05443")["total"] == 1 and f(q="fön")["total"] == 1 and f(staff=st2)["total"] == 2
        rows = f(order="asc")["rows"]; assert rows == sorted(rows, key=lambda x: (x["date"], x["time"]))
        assert len(f(limit=2)["rows"]) == 2
    t("randevu listesi: arama, durum, kişi, tarih, ödeme bekleyen", e)
    def g():
        r = c.get("/api/yp/appts/%s" % i_g, headers=H); assert r.status_code == 200 and r.json()["stage"] == "gelmedi"
        assert c.get("/api/yp/appts/yok", headers=H).status_code == 404
        with TestClient(s.app) as c2: assert c2.get("/api/yp/appts/find").status_code in (401, 403)
    t("tek randevu getirilir, girişsiz erişilemez", g)
print("OK" if not bad else "FAIL", len(ok), "geçti")
for n, e in bad: print("✗", n, "\n", e)
sys.exit(1 if bad else 0)
