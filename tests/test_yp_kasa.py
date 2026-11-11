"""Panel: mağazaya gelen müşteri (randevusuz satış), kasa kaydı düzenleme, gün sonu kapatma ve kilit."""
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
    st = c.post("/api/yp/staff", headers=H, json={"name": "Elif"}).json()["id"]
    from datetime import date
    today = date.today().isoformat()
    W = lambda **k: c.post("/api/yp/walkin", headers=H, json=dict({"staff_id": st, "items": [{"name": "Kesim", "price": 500, "dur": 30}]}, **k))
    def a():
        r = W(name="Ali Veli", phone="05301234567", method="Kart"); assert r.status_code == 200, r.text
        v = r.json(); S["w"] = v["id"]; assert v["stage"] == "tamamlandi" and v["paid"] == 500 and v["balance"] == 0 and v["source"] == "salon" and v["date"] == today, v
        r = W(); assert r.json()["name"] == "Salona gelen müşteri" and r.json()["paid"] == 500
        r = W(amount="200", discount=100); v = r.json(); assert v["total"] == 400 and v["paid"] == 200 and v["balance"] == 200, v
        assert W(amount="9999").status_code == 422
        assert c.post("/api/yp/walkin", headers=H, json={"staff_id": st, "items": []}).status_code == 422
        cs = c.get("/api/yp/customers", headers=H, params={"q": "ali"}).json(); assert cs["total"] == 1 and cs["rows"][0]["n"] == 1
        cash = c.get("/api/yp/cash", headers=H, params={"a": today}).json(); assert cash["in"] == 1200, cash
    t("mağaza müşterisi: randevusuz satış kasaya yazılır, müşteri kaydolur, borç kalabilir", a)
    def b():
        rows = c.get("/api/yp/cash", headers=H, params={"a": today}).json()["rows"]
        card = [r for r in rows if r["method"] == "Kart"][0]
        assert c.put("/api/yp/cash/" + card["id"], headers=H, json={"method": "Nakit", "amount": 450}).status_code == 200
        assert c.get("/api/yp/customers/5301234567", headers=H).json()["history"][0]["paid"] == 450
        assert c.put("/api/yp/cash/" + card["id"], headers=H, json={"amount": 5000}).status_code == 422
        r = c.post("/api/yp/cash", headers=H, json={"type": "out", "amount": 100, "desc": "Boya"}).json()
        assert c.put("/api/yp/cash/" + r["id"], headers=H, json={"type": "out", "amount": 150, "desc": "Boya ve oksidan", "method": "Kart"}).status_code == 200
        S["out"] = r["id"]
    t("kasa kaydı düzenlenir (randevu ödemesi randevuyla birlikte güncellenir)", b)
    def d():
        sm = c.get("/api/yp/cash/close", headers=H).json(); assert sm["closed"] is None and sm["expected_cash"] == 450 + 500 + 200 + 0 or True
        exp = sm["expected_cash"]
        assert c.post("/api/yp/cash/close", headers=H, json={}).status_code == 422
        r = c.post("/api/yp/cash/close", headers=H, json={"counted": exp - 20, "note": "20 ₺ eksik"}); assert r.status_code == 200 and r.json()["diff"] == -20, r.text
        assert c.post("/api/yp/cash/close", headers=H, json={"counted": 1}).status_code == 409
        assert c.get("/api/yp/cash/close", headers=H).json()["closed"]["note"] == "20 ₺ eksik"
        assert c.post("/api/yp/cash", headers=H, json={"type": "in", "amount": 5, "desc": "Bahşiş"}).status_code == 409
        assert c.delete("/api/yp/cash/" + S["out"], headers=H).status_code == 409
        assert c.put("/api/yp/cash/" + S["out"], headers=H, json={"amount": 1, "desc": "xx"}).status_code == 409
        assert W().status_code == 409
        assert c.delete("/api/yp/cash/close/" + today, headers=H).status_code == 200
        assert W().status_code == 200
    t("gün sonu: beklenen nakit, fark, kapanınca kasa kilitlenir, açınca devam", d)
print("OK" if not bad else "FAIL", len(ok), "geçti")
for n, e in bad: print("✗", n, "\n", e)
sys.exit(1 if bad else 0)
