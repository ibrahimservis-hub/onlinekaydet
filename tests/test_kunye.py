"""Sözleşme müşteri künyesi (vergi levhası bilgileri): kaydet, geri oku, PDF metnine gir."""
import sys, os, io
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:500]))
with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    S["f"] = c.post("/api/admin/firms", json={"name": "Künye Firma", "email": "ky@ornek.com", "password": "Sifre123!", "tax_no": "", "address": "Eski adres"}, headers=A).json()["id"]
    U = "/api/admin/firms/%s/kunye" % S["f"]
    t("varsayılan firma kartından gelir", lambda: (lambda j: (j["unvan"] == "Künye Firma" and j["adres"] == "Eski adres") or (_ for _ in ()).throw(AssertionError(j)))(c.get(U, headers=A).json()))
    K = {"unvan": "Künye Ticaret Ltd. Şti.", "vd": "Çankaya", "vkn": "1234567890", "adres": "Atatürk Blv. No:1 Çankaya Ankara", "yetkili": "Ayşe Yılmaz", "telefon": "0532 000 00 00", "eposta": "a@k.com", "mersis": "0123456789012345", "sicil": "99887"}
    def kaydet():
        assert c.put(U, json=K, headers=A).status_code == 200
        j = c.get(U, headers=A).json(); assert all(j[k] == K[k] for k in K), j
        fr = [x for x in c.get("/api/admin/firms", headers=A).json()["firms"] if x["id"] == S["f"]][0]; assert fr.get("tax_no") == "1234567890" and fr.get("tax_office") == "Çankaya"
    t("künye kaydedilir ve firmaya yansır", kaydet)
    t("hatalı vergi no reddedilir", lambda: (c.put(U, json={**K, "vkn": "123"}, headers=A).status_code == 422) or (_ for _ in ()).throw(AssertionError("422 bekleniyordu")))
    def pdf():
        r = c.get("/api/admin/firms/%s/sozlesme.pdf?sure=m6" % S["f"], headers=A); assert r.status_code == 200 and r.content[:4] == b"%PDF"
    t("PDF üretilir", pdf)
    def madde():
        import sozlesme
        f = {"kunye": K}; 
        mus = {"unvan": K["unvan"], "yetkili": K["yetkili"], "vkn": K["vkn"], "vd": K["vd"], "adres": K["adres"], "telefon": K["telefon"], "email": K["eposta"], "sektor": "", "mersis": K["mersis"], "sicil": K["sicil"]}
        sat = {k: "" for k in ("unvan", "vkn", "vergi_dairesi", "adres", "eposta", "mahkeme")}
        fy = {"paket_ad": "P", "sure_ad": "6 ay", "gun": 183, "matrah": 1, "kdv_oran": 20, "kdv": 0.2, "toplam": 1.2, "not": ""}
        txt = str(sozlesme.madde_listesi(mus, fy, sat, mus, [], "01.01.2026", "01.07.2026", "X"))
        assert "0123456789012345" in txt and "99887" in txt and "Çankaya" in txt
    t("MERSİS ve sicil maddede yer alır", madde)
    t("giriş yapmadan erişilemez", lambda: all(TestClient(s.app).request(m, U).status_code in (401, 403) for m in ("get", "put")) or (_ for _ in ()).throw(AssertionError("açık")))
print("OK %d geçti" % len(ok) if not bad else "FAIL", *bad, sep="\n")
