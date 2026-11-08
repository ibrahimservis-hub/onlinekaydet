"""Sahip paneli + paket kapıları: firma açma, paket seçimi, modül kilidi, paket yükseltme, sahibin paket düzenlemesi."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:300]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    def a():
        r = c.get("/api/admin/packages", headers=A).json(); assert set(r["packages"]) >= {"baslangic", "profesyonel", "tam"}
        r = c.post("/api/admin/firms", headers=A, json={"name": "Mini Servis", "email": "m@mini.com", "password": "sifre12345", "package": "baslangic"}); assert r.status_code == 200, r.text
        S["fid"] = r.json()["id"]; assert r.json()["modules"] == ["servis", "personel"]
    t("sahip paket seçerek firma açar; modüller pakete göre gelir", a)
    def b():
        M = tok(c, "m@mini.com", "sifre12345"); S["M"] = M
        assert c.get("/api/customers", headers=M).status_code == 200 and c.get("/api/jobs", headers=M).status_code == 200
        r = c.get("/api/finance/summary", headers=M) if False else c.get("/api/cash", headers=M); assert r.status_code == 403 and "paketinizde yok" in r.text, (r.status_code, r.text)
        assert c.get("/api/rapor/summary", headers=M).status_code == 403
        assert c.get("/api/shop/products", headers=M).status_code == 403
    t("paketinde olmayan modül (muhasebe/rapor/mağaza) 403 verir, servis açık kalır", b)
    def d():
        r = c.get("/api/firm/package", headers=S["M"]).json(); assert r["package"] == "baslangic" and "muhasebe" in r["locked"] and "servis" not in r["locked"]
    t("firma kendi paketini ve kilitli modülleri görür (menüyü buna göre gizler)", d)
    def e():
        r = c.put(f"/api/admin/firms/{S['fid']}", headers=A, json={"package": "profesyonel"}); assert r.status_code == 200 and "muhasebe" in r.json()["modules"], r.text
        r = c.get("/api/cash", headers=S["M"]); assert r.status_code != 403, "yükseltme sonrası muhasebe açılmalı"
        assert c.get("/api/shop/products", headers=S["M"]).status_code == 403, "mağaza hâlâ kapalı"
    t("paket yükseltilince modül hemen açılır", e)
    def f():
        r = c.put(f"/api/admin/firms/{S['fid']}", headers=A, json={"modules": ["magaza"]}); assert r.json()["modules"] == ["servis", "magaza"]
        assert c.get("/api/jobs", headers=S["M"]).status_code == 200, "servis çekirdek: kapatılamaz"
    t("sahip modülleri tek tek açıp kapatır; servis her zaman açık", f)
    def g():
        assert c.post("/api/admin/firms", headers=A, json={"name": "X Firma", "email": "x@x.com", "password": "sifre12345", "package": "yok"}).status_code == 400
    t("bilinmeyen paket reddedilir", g)
    def h():
        r = c.put("/api/admin/packages", headers=A, json={"packages": {"ozel": {"name": "Özel", "price": 499, "modules": ["personel", "rapor", "uydurma"]}}}); assert r.status_code == 200
        assert r.json()["packages"]["ozel"]["modules"] == ["servis", "personel", "rapor"] and r.json()["packages"]["ozel"]["price"] == 499
        assert c.post("/api/admin/firms", headers=A, json={"name": "Ozel Firma", "email": "o@o.com", "password": "sifre12345", "package": "ozel"}).json()["modules"] == ["servis", "personel", "rapor"]
        S["ok"] = 1
    t("sahip paket içeriğini ve fiyatını düzenler; geçersiz modül ayıklanır", h)
    def i():
        M = S["M"]
        assert c.put("/api/admin/packages", headers=M, json={"packages": {"a1": {"modules": ["tam"]}}}).status_code == 403
        assert c.put(f"/api/admin/firms/{S['fid']}", headers=M, json={"package": "tam"}).status_code == 403, "firma kendi paketini yükseltemez"
    t("firma kendi paketini yükseltemez / paket tanımını değiştiremez", i)
    def j():
        c.put(f"/api/admin/firms/{S['fid']}", headers=A, json={"status": "askida"}); assert c.get("/api/jobs", headers=S["M"]).status_code in (401, 403)
    t("askıya alınan firma erişemez", j)
print(f"GEÇTİ {len(ok)}/{len(ok)+len(bad)}")
for a in bad: print("BAŞARISIZ", a)
