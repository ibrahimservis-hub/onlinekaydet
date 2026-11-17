"""Demo süresi dolunca: giriş kapanır, açık oturum kapanır; uzatılınca / satın alma çevrilince açılır."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from datetime import datetime, timezone, timedelta
from starlette.testclient import TestClient
import asyncio, firms
s = boot.server
with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    d = c.post("/api/public/demo", json={"name": "Sure Test", "phone": "05327770011", "sector": "kuafor"}).json()
    f = [x for x in c.get("/api/admin/firms", headers=A).json()["firms"] if x.get("demo")][0]
    assert d["days"] == 7
    gun = (datetime.fromisoformat(f["expires_at"]) - datetime.now(timezone.utc)).total_seconds() / 86400; assert 6.9 < gun < 7.1, gun
    lg = lambda: c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]})
    tok = lg().json()["token"]; H = {"Authorization": "Bearer " + tok}
    assert c.get("/api/yp/boot", headers=H).status_code == 200
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    async def set_exp(v):
        await s.db.main().firms.update_one({"id": f["id"]}, {"$set": {"expires_at": v}}); firms._ACC.clear()
    c.portal.call(set_exp, past)
    r = lg(); assert r.status_code == 403 and "süreniz doldu" in r.json()["detail"], (r.status_code, r.text)
    r = c.get("/api/yp/boot", headers=H); assert r.status_code == 403 and "süreniz doldu" in r.json()["detail"], (r.status_code, r.text)
    # satış olmadı ama uzatıldı -> açılır
    c.portal.call(set_exp, (datetime.now(timezone.utc) + timedelta(days=3)).isoformat())
    assert lg().status_code == 200 and c.get("/api/yp/boot", headers=H).status_code == 200
    # süre dolu + demo temizliği: firma ve verisi silinir
    c.portal.call(set_exp, past)
    r = c.post("/api/admin/demo-cleanup", headers=A, json={}).json(); assert f["name"] in r["removed"], r
print("GEÇTİ")
