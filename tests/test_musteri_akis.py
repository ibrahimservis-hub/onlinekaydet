"""Müşteri paneli (randevu ailesi): personel, hizmet, randevu, çakışma, durum, ödeme-kasa, ekip raporu, müşteri, rapor, siteden gelen randevu."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
import demo
demo.GUNLUK_LIMIT = 10**6
s = boot.server; ok = []; bad = []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-600:]))
with TestClient(s.app) as c:
    d = c.post("/api/public/demo", json={"name": "Akış Test", "phone": "05328880011", "sector": "kuafor"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]}
    boot_ = c.get("/api/yp/boot", headers=H).json(); today = boot_["today"]
    S = {}
    def personel():
        r = c.post("/api/yp/staff", headers=H, json={"name": "Zeynep Usta", "commission": 40, "title": "Kıdemli"}); assert r.status_code == 200, r.text
        S["st"] = r.json()["id"]; b = c.get("/api/yp/boot", headers=H).json(); assert S["st"] in [x["id"] for x in b["staff"]]
        assert c.put("/api/yp/staff/" + S["st"], headers=H, json={"name": "Zeynep Usta", "commission": 45}).status_code == 200
    t("personel ekle/güncelle, boot'ta görünür", personel)
    def hizmet():
        r = c.post("/api/yp/services", headers=H, json={"name": "Keratin bakım", "dur": 60, "price": 1500}); assert r.status_code == 200, r.text
        S["sv"] = r.json()["id"]; assert c.put("/api/yp/services/" + S["sv"], headers=H, json={"name": "Keratin bakım", "dur": 60, "price": 1600}).status_code == 200
        assert "Keratin bakım" in [x["name"] for x in c.get("/api/yp/boot", headers=H).json()["services"]]
    t("hizmet ekle/güncelle", hizmet)
    def randevu():
        body = {"name": "Selin Kaya", "phone": "05325551234", "date": today, "time": "09:00", "staff_id": S["st"], "items": [{"name": "Keratin bakım", "price": 1600, "dur": 60}], "source": "telefon"}
        r = c.post("/api/yp/appts", headers=H, json=body); assert r.status_code == 200, r.text; S["ap"] = r.json()["id"]
        rows = c.get("/api/yp/appts?a=%s&b=%s" % (today, today), headers=H).json()["rows"]; assert S["ap"] in [x["id"] for x in rows]
        assert [x for x in rows if x["id"] == S["ap"]][0]["staff_id"] == S["st"]
        r2 = c.post("/api/yp/appts", headers=H, json=dict(body, name="Başka", time="09:30")); assert r2.status_code == 409, "çakışma engellenmedi"
        r3 = c.post("/api/yp/appts", headers=H, json=dict(body, name="Başka", time="09:30", force=True)); assert r3.status_code == 200
        S["ap2"] = r3.json()["id"]
        r4 = c.post("/api/yp/appts", headers=H, json=dict(body, staff_id="yok")); assert r4.status_code == 422
    t("randevu: personelle görünür, çakışma 409, zorla ekleme, personelsiz 422", randevu)
    def tasi():
        r = c.put("/api/yp/appts/" + S["ap"], headers=H, json={"time": "11:00"}); assert r.status_code == 200 and r.json()["time"] == "11:00", r.text
        r = c.get("/api/yp/appts/" + S["ap"], headers=H); assert r.status_code == 200
    t("randevu saatini taşı, detay", tasi)
    def odeme():
        r = c.post("/api/yp/appts/%s/pay" % S["ap"], headers=H, json={"amount": 5000, "method": "Nakit"}); assert r.status_code == 422, "fazla tutar kabul edildi"
        r = c.post("/api/yp/appts/%s/pay" % S["ap"], headers=H, json={"amount": 600, "method": "Nakit"}); assert r.status_code == 200, r.text
        r = c.post("/api/yp/appts/%s/pay" % S["ap"], headers=H, json={"amount": 1000, "method": "Kredi kartı"}); assert r.status_code == 200
        v = c.get("/api/yp/appts/" + S["ap"], headers=H).json(); assert v["stage"] == "tamamlandi" and v["balance"] == 0, v
        cash = c.get("/api/yp/cash?a=%s&b=%s" % (today, today), headers=H).json(); assert "1600" in str(cash) or 1600 in str(cash), str(cash)[:300]
        r = c.post("/api/yp/appts/%s/stage" % S["ap"], headers=H, json={"to": "iptal"}); assert r.status_code == 422, "ödemeli randevu iptal edilebildi"
    t("ödeme: kısmi+tam, kasa, tamamlandı, ödemeliyi iptal engeli", odeme)
    def durum():
        r = c.post("/api/yp/appts/%s/stage" % S["ap2"], headers=H, json={"to": "gelmedi"}); assert r.status_code == 200 and r.json()["stage"] == "gelmedi"
        assert c.post("/api/yp/appts/%s/stage" % S["ap2"], headers=H, json={"to": "bilinmez"}).status_code == 422
    t("durum değiştir (gelmedi)", durum)
    def ekip():
        r = c.get("/api/yp/team?a=%s&b=%s" % (today, today), headers=H); assert r.status_code == 200, r.text
        x = r.json(); sx = str(x); assert "Zeynep Usta" in sx, sx[:300]
    t("ekip raporunda personel görünür", ekip)
    def musteri():
        m = c.get("/api/yp/customers?q=Selin", headers=H).json(); assert any("Selin" in r["name"] for r in m["rows"]), m
        assert c.get("/api/yp/customers/05325551234", headers=H).status_code == 200
        assert c.put("/api/yp/customers/05325551234", headers=H, json={"note": "Sarı boya sever"}).status_code == 200
    t("müşteri listesi, detay, not", musteri)
    def rapor():
        r = c.get("/api/yp/report?a=%s&b=%s" % (today, today), headers=H); assert r.status_code == 200 and "1600" in r.text.replace(".0", ""), r.text[:300]
    t("rapor gelir içerir", rapor)
    def kasa():
        r = c.post("/api/yp/cash", headers=H, json={"type": "out", "amount": 250, "method": "Nakit", "desc": "Malzeme alımı"}); assert r.status_code == 200, r.text
        cid = r.json()["id"]; assert c.put("/api/yp/cash/" + cid, headers=H, json={"amount": 300, "desc": "Malzeme alımı", "type": "out"}).status_code == 200
        assert c.get("/api/yp/cash/close?day=" + today, headers=H).status_code in (200, 422)
        assert c.delete("/api/yp/cash/" + cid, headers=H).status_code == 200
    t("kasa: gider ekle/güncelle/sil", kasa)
    def walkin():
        r = c.post("/api/yp/walkin", headers=H, json={"name": "Yoldan Gelen", "staff_id": S["st"], "items": [{"name": "Keratin bakım", "price": 1600, "dur": 60}], "amount": 1600, "method": "Nakit"}); assert r.status_code == 200, r.text
    t("yoldan gelen müşteri (walk-in)", walkin)
    def site_randevu():
        A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
        fid = [x for x in c.get("/api/admin/firms", headers=A).json()["firms"] if x["name"] == boot_["firm"]][0]["id"]
        from datetime import date, timedelta
        gun = (date.fromisoformat(today) + timedelta(days=1)).isoformat()
        base = "/api/public/%s~yp/" % fid
        sl = c.get(base + "slots?date=" + gun + "&dur=60"); assert sl.status_code == 200, sl.text
        acik = [x for x in sl.json().get("slots", []) if x["available"]]
        assert acik, "online randevuda boş saat yok (online randevu kapalı olabilir): " + sl.text[:200]
        sv = [x["id"] for x in c.get("/api/yp/boot", headers=H).json()["services"]][:1]
        r = c.post(base + "book", json={"name": "Site Müşterisi", "phone": "05326667788", "date": gun, "time": acik[0]["time"], "services": sv, "staff_id": S["st"]}); assert r.status_code == 200, r.text
        req = c.get("/api/yp/requests", headers=H).json()["rows"]; x = [q for q in req if q["name"] == "Site Müşterisi"]; assert x, "bekleyen taleplerde görünmüyor"
        assert x[0]["staff_id"] == S["st"]
        r = c.post("/api/yp/appts/%s/stage" % x[0]["id"], headers=H, json={"to": "bekliyor"}); assert r.status_code == 200, r.text
        rows = c.get("/api/yp/appts?a=%s&b=%s" % (gun, gun), headers=H).json()["rows"]; assert "Site Müşterisi" in [q["name"] for q in rows], "takvimde görünmüyor"
        r2 = c.post(base + "book", json={"name": "Site Müşterisi 2", "phone": "05326667789", "date": gun, "time": acik[0]["time"], "services": sv, "staff_id": S["st"]}); assert r2.status_code == 409, "dolu saate randevu alındı"
    t("siteden randevu: boş saat, talep, personelde, takvimde, dolu saat 409", site_randevu)
print("OK" if not bad else "BAŞARISIZ", len(ok), ok if not bad else "")
for n, e in bad: print("---", n, "\n", e)
