"""Yeni yönetim paneli (/api/yp): randevu -> ödeme -> kasa -> rapor, çakışma, siteden gelen talep, kasa silme, ekip primi."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-500:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe Kaya", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    from datetime import date, timedelta
    D = (date.today() + timedelta(days=1)).isoformat()
    def a():
        r = c.get("/api/yp/boot", headers=H); assert r.status_code == 200, r.text
        d = r.json(); assert d["services"] and d["terms"]["kisi"], d; S["boot"] = d
    t("açılış verisi: hizmet listesi ve sektör dili gelir", a)
    def b():
        from starlette.testclient import TestClient as TC
        with TC(s.app) as c2: assert c2.get("/api/yp/boot").status_code in (401, 403)
    t("girişsiz erişilemez", b)
    def st():
        r = c.post("/api/yp/staff", headers=H, json={"name": "Elif Usta", "commission": 40, "salary": 20000, "off": [0]}); assert r.status_code == 200, r.text
        S["st"] = r.json()["id"]; assert r.json()["commission"] == 40
        r = c.post("/api/yp/staff", headers=H, json={"name": "Can"}); S["st2"] = r.json()["id"]
        assert len(c.get("/api/yp/boot", headers=H).json()["staff"]) >= 2
    t("ekip: kişi eklenir", st)
    def ap():
        sv = S["boot"]["services"][0]
        body = {"name": "Zeynep Demir", "phone": "0532 111 22 33", "date": D, "time": "10:00", "staff_id": S["st"], "items": [{"name": sv["name"], "price": 1000, "dur": 60}]}
        r = c.post("/api/yp/appts", headers=H, json=body); assert r.status_code == 200, r.text
        v = r.json(); S["ap"] = v["id"]; assert v["stage"] == "bekliyor" and v["total"] == 1000 and v["phone"] == "5321112233" and v["no"].startswith("RD-"), v
        r = c.post("/api/yp/appts", headers=H, json=dict(body, time="10:30")); assert r.status_code == 409, r.text
        assert c.post("/api/yp/appts", headers=H, json=dict(body, time="10:30", staff_id=S["st2"])).status_code == 200
        assert c.post("/api/yp/appts", headers=H, json=dict(body, time="10:30", force=True)).status_code == 200
        assert c.post("/api/yp/appts", headers=H, json=dict(body, items=[])).status_code == 422
    t("randevu açılır, aynı kişide çakışma 409, başka kişide serbest", ap)
    def tk():
        r = c.get("/api/yp/appts?a=%s" % D, headers=H).json()["rows"]; assert any(x["id"] == S["ap"] for x in r)
    t("takvimde görünür", tk)
    def pay():
        r = c.post("/api/yp/appts/%s/pay" % S["ap"], headers=H, json={"amount": 400, "method": "Kart"}); assert r.status_code == 200, r.text
        v = r.json(); assert v["paid"] == 400 and v["balance"] == 600 and v["stage"] == "bekliyor", v
        k = c.get("/api/yp/cash?a=%s&b=%s" % (D, D + ""), headers=H).json()
        # kasa satırı bugünün saatiyle yazılır
        today = date.today().isoformat()
        k = c.get("/api/yp/cash?a=%s&b=%s" % (today, today), headers=H).json()
        assert k["in"] == 400 and k["rows"][0]["kind"] == "randevu" and k["rows"][0]["ref"] == S["ap"], k
        assert c.post("/api/yp/appts/%s/pay" % S["ap"], headers=H, json={"amount": 700}).status_code == 422
        r = c.post("/api/yp/appts/%s/pay" % S["ap"], headers=H, json={"amount": 600, "method": "Nakit"}); v = r.json()
        assert v["balance"] == 0 and v["stage"] == "tamamlandi", v
        k = c.get("/api/yp/cash?a=%s&b=%s" % (today, today), headers=H).json(); assert k["in"] == 1000 and len(k["rows"]) == 2, k
        S["cash"] = k["rows"][0]["id"]
    t("ödeme kasaya aynı anda düşer, tam ödemede randevu tamamlanır, fazla tutar reddedilir", pay)
    def man():
        assert c.post("/api/yp/cash", headers=H, json={"type": "out", "amount": 300, "desc": "Şampuan alımı"}).status_code == 200
        r = c.post("/api/yp/cash", headers=H, json={"type": "out", "amount": 5000, "desc": "Avans", "staff_id": S["st"]}); assert r.json()["kind"] == "personel"
        assert c.post("/api/yp/cash", headers=H, json={"type": "in", "amount": 0, "desc": "x"}).status_code == 422
        today = date.today().isoformat()
        k = c.get("/api/yp/cash?a=%s&b=%s" % (today, today), headers=H).json(); assert k["out"] == 5300 and k["in"] == 1000
    t("elle gider ve personel avansı girilir", man)
    def tm():
        today = date.today()
        a_ = (today - timedelta(days=30)).isoformat(); b_ = (today + timedelta(days=30)).isoformat()
        rows = {x["id"]: x for x in c.get("/api/yp/team?a=%s&b=%s" % (a_, b_), headers=H).json()["rows"]}
        e = rows[S["st"]]; assert e["revenue"] == 1000 and e["prim"] == 400 and e["paid_out"] == 5000 and e["payable"] == 20000 + 400 - 5000, e
    t("ekip: ciro, prim, avans düşülmüş ödenecek tutar", tm)
    def rp():
        today = date.today()
        a_ = (today - timedelta(days=30)).isoformat(); b_ = (today + timedelta(days=30)).isoformat()
        r = c.get("/api/yp/report?a=%s&b=%s" % (a_, b_), headers=H).json()
        assert r["in"] == 1000 and r["out"] == 5300 and r["appts"] >= 1 and r["services"][0][2] == 1000 and r["staff"][0][1] == 1000, r
    t("rapor: gelir, gider, hizmet ve kişi cirosu", rp)
    def dl():
        assert c.post("/api/yp/appts/%s/stage" % S["ap"], headers=H, json={"to": "iptal"}).status_code == 422
        assert c.delete("/api/yp/cash/" + S["cash"], headers=H).status_code == 200
        today = date.today().isoformat()
        k = c.get("/api/yp/cash?a=%s&b=%s" % (today, today), headers=H).json(); assert k["in"] == 400 or k["in"] == 600, k
        v = [x for x in c.get("/api/yp/appts?a=%s" % D, headers=H).json()["rows"] if x["id"] == S["ap"]][0]
        assert v["paid"] == k["in"] and v["balance"] == 1000 - k["in"], v
    t("ödenmiş randevu iptal edilemez; kasa satırı silinince ödeme randevudan da düşer", dl)
    def site():
        g = c.get("/api/growth/settings", headers=H); assert g.status_code == 200, g.text
        cfg = g.json(); cfg["booking"]["enabled"] = True; cfg["booking"]["min_notice_hours"] = 0; cfg["booking"]["capacity"] = 3
        assert c.put("/api/growth/settings", headers=H, json=cfg).status_code == 200
        day = c.get("/api/public/booking/config", headers=H).json()["days"][2]
        sl = [x for x in c.get("/api/public/booking/slots?date=" + day, headers=H).json()["slots"] if x["available"]]; assert sl
        tm = sl[0]["time"]
        r = c.post("/api/public/booking", headers=H, json={"name": "Mine Ak", "phone": "05559998877", "date": day, "time": tm, "device_type": "Saç boyama", "fault": "Kızıl ton"}); assert r.status_code == 200, r.text
        rr = c.get("/api/yp/requests", headers=H).json()["rows"]; x = [q for q in rr if q["name"] == "Mine Ak"][0]
        assert x["stage"] == "talep" and x["want"] == "Saç boyama"
        assert any(q["id"] == x["id"] for q in c.get("/api/yp/appts?a=%s" % day, headers=H).json()["rows"])
        r = c.put("/api/yp/appts/" + x["id"], headers=H, json={"name": "Mine Ak", "date": day, "time": tm, "staff_id": S["st2"], "items": [{"name": "Boya", "price": 1400, "dur": 90}]})
        assert r.status_code == 200 and r.json()["stage"] == "bekliyor" and r.json()["no"], r.text
        assert not [q for q in c.get("/api/yp/requests", headers=H).json()["rows"] if q["id"] == x["id"]]
    t("siteden gelen talep onaylanıp takvime alınır", site)
    def cu():
        r = c.get("/api/yp/customers", headers=H).json(); assert any(x["phone"] == "5321112233" and x["n"] == 1 for x in r["rows"]), r
        d = c.get("/api/yp/customers/5321112233", headers=H).json(); assert d["history"]
        assert c.put("/api/yp/customers/5321112233", headers=H, json={"note": "Alerjisi var"}).status_code == 200
        assert c.get("/api/yp/customers/5321112233", headers=H).json()["customer"]["note"] == "Alerjisi var"
    t("müşteri listesi, geçmiş ve not", cu)
print("OK %d" % len(ok)); [print("HATA", n, "\n", e) for n, e in bad]
sys.exit(1 if bad else 0)
