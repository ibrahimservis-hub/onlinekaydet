"""Sektöre özel kayıt motoru: her aile için kayıt aç, adım ilerlet, ödeme al, kapat; teknik sektör etkilenmez."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import sektor, sektor_kayit, demo
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-600:]))
SAMPLE = ["kuafor", "tekstil", "oto_cekici", "avukat", "dis_klinigi", "oto_servis", "cilingir", "surucu_kursu", "nakliye", "eticaret", "mimar", "kombi"]
with TestClient(s.app) as c:
    n = [0]
    def login(k):
        demo._RATE.clear(); n[0] += 1
        r = c.post("/api/public/demo", json={"name": "Deneme Kisi", "phone": "0552417%04d" % (7000 + n[0]), "sector": k}); assert r.status_code == 200, (k, r.text)
        d = r.json(); tok = c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]}).json()["token"]
        return {"Authorization": "Bearer " + tok}
    def flow(k):
        H = login(k)
        sc = c.get("/api/admin/kayit/schema", headers=H)
        if k == "kombi":
            assert sc.status_code == 404; return
        assert sc.status_code == 200, (k, sc.text[:200]); sc = sc.json()
        assert len(sc["steps"]) == 5 and sc["sections"] and sc["items"] and sc["check"]["opts"], k
        body = {"customer_name": "Test Müşteri", "customer_phone": "05551112233", "when": "2026-11-12T14:30", "discount": 10, "check": {sc["check"]["opts"][0]["k"]: True}}
        it = sc["items"][0]; body[it["k"]] = [{"name": "Kalem A", "qty": 2, "price": 100}]
        if sc["family"] == "yol": body.update({"km": 10, "km_rate": 20, "base": 300})
        r = c.post("/api/admin/kayit", json=body, headers=H); assert r.status_code == 200, (k, r.text[:300]); d = r.json()
        total = d["sums"]["total"]; assert total > 0 and d["status"] == sc["steps"][0]["k"], (k, d["sums"])
        assert total == round(sum(l["v"] for l in d["sums"]["lines"]) - 10, 2), k
        rid = d["id"]
        for st in sc["steps"][1:-1]:
            assert c.post("/api/admin/kayit/%s/adim" % rid, json={"to": st["k"]}, headers=H).status_code == 200, (k, st)
        last = sc["steps"][-1]["k"]
        r = c.post("/api/admin/kayit/%s/adim" % rid, json={"to": last}, headers=H)
        if sc["pay"]:
            assert r.status_code == 400, (k, "ödeme almadan kapanmamalı")
            assert c.post("/api/admin/kayit/%s/odeme" % rid, json={"amount": total + 5, "method": "Nakit"}, headers=H).status_code == 400
            assert c.post("/api/admin/kayit/%s/odeme" % rid, json={"amount": total, "method": "Kart"}, headers=H).status_code == 200
            assert c.post("/api/admin/kayit/%s/adim" % rid, json={"to": last}, headers=H).status_code == 200, k
        else:
            assert r.status_code == 200, k
        ls = c.get("/api/admin/kayit", headers=H).json(); assert ls["rows"] and ls["rows"][0]["cols"][0] and ls["summary"], k
        assert c.get("/api/admin/kayit?flt=" + last, headers=H).json()["rows"], k
        assert c.delete("/api/admin/kayit/%s" % rid, headers=H).status_code == 200
        r = c.post("/api/admin/kayit", json={"customer_name": ""}, headers=H); assert r.status_code == 400
    for k in SAMPLE:
        t("kayıt akışı: " + k, (lambda k=k: flow(k)))
    def allsch():
        for k in sektor.SECTORS:
            tp = sektor_kayit.template(k)
            if k in ("kombi", "klima", "beyaz_esya", "elektronik", "bilgisayar", "tesisat", "elektrik", "guvenlik"): assert tp is None
            else: assert tp and len(tp["steps"]) == 5 and all(f.get("k") and f.get("l") for _, fl in tp["sections"] for f in fl), k
    t("78 sektör: teknik 8 şablonsuz, diğer 70 şablonlu", allsch)
for n_ in ok: print("  ✓", n_)
for n_, e in bad: print("HATA:", n_, e)
print(len(ok), "geçti,", len(bad), "hata")
