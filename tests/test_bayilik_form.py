"""bayilik.html#kayit: sektör alanı yok; form /api/public/lead'e form=bayilik olarak düşer ve yönetimde görünür."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
html = open(os.path.join(os.path.dirname(__file__), "..", "site", "bayilik.html"), encoding="utf-8").read()
sec = html[html.index('id="kayit"'):]
sec = sec[:sec.index("</section>")]
assert "Sektör" not in sec and "<select" not in sec, "kayıt formunda sektör kalmamalı"
assert all(x in sec for x in ("Ad soyad", "Telefon", "Firma adı"))
assert 'data-form="bayilik"' in sec
with TestClient(boot.server.app) as c:
    r = c.post("/api/public/lead", json={"name": "Deneme Bayi", "phone": "05324445566", "firm": "Deneme Ltd", "sector": "", "form": "bayilik", "src": {"page": "bayilik.html"}})
    assert r.status_code == 200 and r.json()["ok"], r.text
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    L = c.get("/api/admin/leads", headers=A).json()["leads"]
    x = [l for l in L if l["phone"] == "5324445566"]
    assert x and x[0]["form"] == "bayilik" and x[0]["firm"] == "Deneme Ltd" and x[0]["status"] == "yeni", x
    assert c.post("/api/public/lead", json={"name": "A", "phone": "123", "form": "bayilik"}).status_code == 422
print("OK bayilik formu")
