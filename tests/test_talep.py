"""Satış sayfası talepleri: doğrulama, bot tuzağı, hız sınırı, tekrar kaydı, sahip listesi."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:300]))
with TestClient(s.app) as c:
    c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"})
    P = {"name": "Ayşe Yılmaz", "phone": "0532 111 22 33", "firm": "Ege Kombi", "sector": "kombi", "form": "ana-sayfa", "src": {"utm_source": "google", "page": "/"}, "extra": {"usta": "2-5"}}
    with TestClient(s.app) as pub:
        def a():
            r = pub.post("/api/public/lead", json=P); assert r.status_code == 200 and r.json()["ok"], r.text
            L = c.get("/api/admin/leads").json(); assert L["counts"]["yeni"] == 1 and L["leads"][0]["phone"] == "5321112233" and L["leads"][0]["src"]["utm_source"] == "google"
        t("talep kaydolur, telefon 10 haneye çevrilir, kaynak saklanır", a)
        def b():
            assert pub.post("/api/public/lead", json=P).status_code == 200
            assert c.get("/api/admin/leads").json()["counts"]["yeni"] == 1
        t("aynı telefon 10 dakikada ikinci kez kaydolmaz", b)
        def d():
            for bad_ in ({**P, "phone": "123"}, {**P, "name": "A"}, {**P, "phone": "0432 111 22 33"}):
                assert pub.post("/api/public/lead", json=bad_).status_code == 422, bad_
        t("geçersiz telefon/ad 422", d)
        def e():
            r = pub.post("/api/public/lead", json={**P, "phone": "05329998877", "website": "http://spam"}); assert r.status_code == 200
            assert c.get("/api/admin/leads").json()["counts"]["yeni"] == 1
        t("bot tuzağı dolu ise kayıt yapılmaz", e)
        def f():
            codes = [pub.post("/api/public/lead", json={**P, "phone": f"0533111{i:04d}"}).status_code for i in range(8)]
            assert 429 in codes, codes
        t("aynı IP'den saatte 6'dan fazla talep 429", f)
    def g():
        with TestClient(s.app) as x: assert x.get("/api/admin/leads").status_code in (401, 403)
    t("talep listesi girişsiz açılmaz", g)
    def h():
        i = c.get("/api/admin/leads").json()["leads"][0]["id"]
        assert c.put(f"/api/admin/leads/{i}", json={"status": "arandi", "note": "yarın"}).status_code == 200
        assert c.put(f"/api/admin/leads/{i}", json={"status": "x"}).status_code == 422
        assert c.get("/api/admin/leads?status=arandi").json()["leads"][0]["note"] == "yarın"
    t("durum ve not güncellenir, geçersiz durum 422", h)
    def k():
        r = c.post("/api/admin/firms", json={"name": "Z Servis", "email": "z@z.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200
        with TestClient(s.app) as fz:
            T = fz.post("/api/auth/login", json={"email": "z@z.com", "password": "sifre12345"}).json()["token"]
            assert fz.get("/api/admin/leads", headers={"Authorization": "Bearer " + T}).status_code == 403
    t("firma yöneticisi talep listesini göremez", k)
print(f"GEÇTİ {len(ok)}/{len(ok)+len(bad)}")
for a in bad: print("BAŞARISIZ", a)
