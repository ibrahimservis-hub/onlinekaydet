"""Teslim sipariş kasaya düşer (bir kez); toplu fatura taslağı; faturalı sipariş tekrar faturalanmaz."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    pid = c.post("/api/yp/products", headers=H, json={"name": "Keten Gömlek", "price": 900, "cost": 400, "stock": 10, "cat": "Gömlek"}).json()["id"]
    ids = []
    for k in range(2):
        r = c.post("/api/yp/orders", headers=H, json={"channel": "site", "payment": "kart", "customer": {"name": "Mehmet %d" % k, "phone": "0532 111 22 3%d" % k, "city": "İstanbul", "address": "Kadıköy"},
                   "items": [{"product": pid, "name": "Keten Gömlek", "price": 900, "qty": 1, "cost": 400}]})
        assert r.status_code == 200, r.text
        ids.append(r.json()["item"]["id"] if "item" in r.json() else r.json()["id"])
    # teslim akışı: yeni -> ... -> teslim
    for oid in ids:
        for st in ("onaylandi", "hazirlaniyor", "kargoda", "teslim"):
            r = c.post("/api/yp/orders/%s/status" % oid, headers=H, json={"status": st})
            if r.status_code == 422 and "kargo" in r.text:
                c.post("/api/yp/orders/bulk", headers=H, json={"ids": [oid], "op": "cargo", "cargo": {"firm": "yurtici"}})
                r = c.post("/api/yp/orders/%s/status" % oid, headers=H, json={"status": st})
            assert r.status_code == 200, (st, r.text)
    cash = c.get("/api/yp/cash?a=2000-01-01&b=2100-01-01", headers=H).json()
    sip = [x for x in cash["rows"] if x["kind"] == "siparis"]
    assert len(sip) == 2 and cash["in"] >= 1800, cash
    # ikinci kez teslim işareti kasayı çoğaltmaz
    c.post("/api/yp/orders/bulk", headers=H, json={"ids": ids, "op": "status", "status": "teslim"})
    assert len([x for x in c.get("/api/yp/cash?a=2000-01-01&b=2100-01-01", headers=H).json()["rows"] if x["kind"] == "siparis"]) == 2
    # toplu fatura
    r = c.post("/api/yp/orders/fatura", headers=H, json={"ids": ids}).json()
    assert r["n"] == 2, r
    inv = c.get("/api/yp/invoices", headers=H).json()
    assert inv["n"] == 2 and abs(inv["toplam"] - 1800) < 0.01 and abs(inv["kdv"] - 300) < 0.01, inv
    r2 = c.post("/api/yp/orders/fatura", headers=H, json={"ids": ids}).json()
    assert r2["n"] == 0 and len(r2["skipped"]) == 2, r2
    ex = c.post("/api/yp/invoices/export", headers=H, json={"ids": [x["id"] for x in inv["rows"]]}).json()
    assert ex["n"] == 2 and "Fatura No" in ex["csv"]
    d = c.post("/api/yp/invoices/durum", headers=H, json={"ids": [inv["rows"][0]["id"]], "state": "iptal"}).json()
    assert d["n"] == 1
    assert c.post("/api/yp/orders/fatura", headers=H, json={"ids": ids}).json()["n"] == 1
print("OK")
