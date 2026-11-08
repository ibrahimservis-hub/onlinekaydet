"""Gerçek sunucu (test veritabanıyla) üzerinde: firma aç -> usta/müşteri/cihaz/iş -> atama -> usta adımları -> ayar kuralları -> PDF."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server
ok, bad = [], []
def t(name, fn):
    try: fn(); ok.append(name)
    except Exception as e: bad.append((name, repr(e)[:300]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
def pdftxt(b):
    open("/tmp/_f.pdf", "wb").write(b); return subprocess.run(["pdftotext", "/tmp/_f.pdf", "-"], capture_output=True, text=True).stdout

with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Ege Kombi", "email": "hasan@egekombi.com", "password": "sifre12345", "features": {}}); assert r.status_code == 200, r.text
    O = tok(c, "hasan@egekombi.com", "sifre12345")
    S = {}
    def f1():
        r = c.get("/api/service-settings", headers=O); assert r.status_code == 200 and r.json()["imza"]["enabled"] is True; S["d"] = r.json()
    t("varsayılan servis ayarları gelir", f1)
    # --- kurulum: usta, müşteri, cihaz
    r = c.post("/api/technicians", headers=O, json={"email": "usta1@egekombi.com", "password": "usta12345", "name": "Hasan Demir", "phone": "05320000001", "commission_percent": 0}); assert r.status_code == 200, r.text
    TID = r.json()["id"]; U = tok(c, "usta1@egekombi.com", "usta12345")
    r = c.post("/api/technicians", headers=O, json={"email": "usta2@egekombi.com", "password": "usta12345", "name": "Murat Kaya", "phone": "05320000002", "commission_percent": 0}); T2 = r.json()["id"]; U2 = tok(c, "usta2@egekombi.com", "usta12345")
    CU = c.post("/api/customers", headers=O, json={"name": "Ayşe Yılmaz", "phone": "05321112233", "address": "Kazımdirik 123/4", "district": "Bornova", "city": "İzmir"}).json()
    B = c.get("/api/brands", headers=O).json()[0]
    DV = c.post("/api/devices", headers=O, json={"customer_id": CU["id"], "brand_id": B["id"], "type": "kombi", "model": "Luna 3"}).json()
    def newjob(assign=TID):
        r = c.post("/api/jobs", headers=O, json={"customer_id": CU["id"], "device_id": DV["id"], "fault_description": "Isıtmıyor E01", "scheduled_at": "2026-11-08T11:00", "assigned_technician_id": assign}); assert r.status_code == 200, r.text; return r.json()
    def put(H, jid, body): return c.put(f"/api/jobs/{jid}", headers=H, json=body)
    def sett(body): r = c.put("/api/service-settings", headers=O, json=body); assert r.status_code == 200, r.text; return r.json()

    def a():
        j = newjob(); assert j["status"] == "atandi" and j["assigned_technician_name"] == "Hasan Demir"
        assert c.get("/api/jobs", headers=U).json() and not c.get("/api/jobs", headers=U2).json()
    t("kayıt ata: usta kendi işini görür, diğer usta görmez", a)
    def b():
        j = newjob(); r = put(U2, j["id"], {"status": "yolda"}); assert r.status_code == 403, r.status_code
    t("başka usta işi değiştiremez", b)
    def d():
        sett({"foto_once": "zorunlu", "foto_sonra": "zorunlu"}); j = newjob()
        assert put(U, j["id"], {"status": "yolda"}).status_code == 200
        r = put(U, j["id"], {"status": "basladi"}); assert r.status_code == 400 and "öncesi" in r.text
        assert put(U, j["id"], {"status": "basladi", "photos_before": ["a.jpg"]}).status_code == 200
        r = put(U, j["id"], {"status": "tamamlandi", "work_done": "x"}); assert r.status_code == 400 and "sonrası" in r.text
        r = put(U, j["id"], {"status": "tamamlandi", "work_done": "Basınç ayarlandı", "photos_after": ["b.jpg"], "labor_fee": 500, "parts_used": [{"name": "Sensör", "qty": 1, "unit_price": 650}]})
        assert r.status_code == 200 and r.json()["status"] == "tamamlandi" and r.json()["total_amount"] == 1150, r.text
        S["done"] = j["id"]
    t("foto zorunlu: öncesiz başlamaz, sonrasız bitmez, tam akış 1150 TL", d)
    def e():
        sett({"foto_once": "kapali", "foto_sonra": "kapali", "imza": {"enabled": False}}); j = newjob()
        for st in ("yolda", "basladi"): assert put(U, j["id"], {"status": st}).status_code == 200
        r = put(U, j["id"], {"status": "tamamlandi", "work_done": "ok", "signature_url": "imza.png"}); assert r.status_code == 200
        assert not r.json().get("signature_url"), "imza kapalıyken saklanmamalı"; S["nosig"] = j["id"]
    t("imza kapalı: imzasız biter, gönderilen imza saklanmaz", e)
    def f():
        sett({"imza": {"enabled": True, "required": True}}); j = newjob()
        for st in ("yolda", "basladi"): put(U, j["id"], {"status": st})
        assert put(U, j["id"], {"status": "tamamlandi", "work_done": "ok"}).status_code == 400
        r = put(U, j["id"], {"status": "tamamlandi", "work_done": "ok", "signature_url": "imza.png"}); assert r.status_code == 200 and r.json()["signature_url"] == "imza.png"; S["sig"] = j["id"]
    t("imza zorunlu: imzasız bitmez, imzalıysa biter", f)
    def g():
        sett({"usta_imza": {"enabled": True}}); j = newjob()
        for st in ("yolda", "basladi"): put(U, j["id"], {"status": st})
        assert put(U, j["id"], {"status": "tamamlandi", "work_done": "ok", "signature_url": "s"}).status_code == 400
        assert put(U, j["id"], {"status": "tamamlandi", "work_done": "ok", "signature_url": "s", "tech_signature_url": "u"}).status_code == 200
        sett({"usta_imza": {"enabled": False}})
    t("usta imzası açılınca zorunlu olur", g)
    def h():
        r = c.put("/api/service-settings", headers=O, json={"steps": {"tamamlandi": {"enabled": False}}}); assert r.status_code == 400
        sett({"steps": {"yolda": {"enabled": False}}}); j = newjob(); assert put(U, j["id"], {"status": "yolda"}).status_code == 400
        assert put(U, j["id"], {"status": "basladi"}).status_code == 200
        sett({"steps": {"yolda": {"enabled": True}}})
    t("kapatılan adım uygulanmaz, zorunlu adım kapatılamaz", h)
    def i():
        r = c.put("/api/service-settings", headers=U, json={"foto_once": "kapali"}); assert r.status_code == 403
    t("usta ayarı değiştiremez", i)
    def k():
        r = c.put("/api/service-settings", headers=O, json={"foto_once": "saçma"}); assert r.status_code == 400
    t("geçersiz ayar reddedilir", k)
    def l():
        sett({"imza": {"enabled": True, "required": False}, "pdf": {"title": "SERVİS FORMU"}})
        jj = c.get(f"/api/jobs/{S['sig']}", headers=O).json()
        r = c.get(f"/api/jobs/{S['sig']}/fis.pdf", headers=O); assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
        x = pdftxt(r.content); assert "SERVİS FORMU" in x and "Müşteri imzası" in x and "Ayşe Yılmaz" in x and "Isıtmıyor" in x, x
        open("/tmp/ok_fis_imzali.pdf", "wb").write(r.content)
    t("PDF: imza açık → imza alanı var, müşteri/arıza bilgisi var", l)
    def m():
        sett({"imza": {"enabled": False}}); x = pdftxt(c.get(f"/api/jobs/{S['done']}/fis.pdf", headers=O).content)
        assert "Müşteri imzası" not in x and "1150.00 TL" in x and "Sensör" in x, x
        open("/tmp/ok_fis_imzasiz.pdf", "wb").write(c.get(f"/api/jobs/{S['done']}/fis.pdf", headers=O).content)
        sett({"imza": {"enabled": True}})
    t("PDF: imza kapalı → imza alanı yok, parça ve toplam var", m)
    def n():
        sett({"pdf": {"blocks": {"parca": False, "toplam": False}}}); x = pdftxt(c.get(f"/api/jobs/{S['done']}/fis.pdf", headers=O).content)
        assert "Sensör" not in x and "TOPLAM" not in x; sett({"pdf": {"blocks": {"parca": True, "toplam": True}}})
        r = c.get(f"/api/jobs/{S['done']}/fis.pdf", headers=U2); assert r.status_code == 403
    t("PDF blokları kapanır; başka usta fişi alamaz", n)
    def o():
        r = c.post("/api/catalog", headers=O, json={"brand": "Baymak", "model": "Luna 3 Comfort 24/28", "type": "kombi", "error_codes": "E01,E02"}); assert r.status_code == 200, r.text
        assert c.post("/api/catalog", headers=O, json={"brand": "Baymak", "model": "Luna 3 Comfort 24/28"}).status_code == 400
        assert len(c.get("/api/catalog", headers=U).json()) == 1 and c.post("/api/catalog", headers=U, json={"brand": "X1", "model": "Y"}).status_code == 403
    t("cihaz kataloğu: ekle, tekrar reddet, usta okur ama ekleyemez", o)
    def p():
        r = c.post("/api/auth/login", json={"email": "hasan@egekombi.com", "password": "sifre12345"})
        assert c.get("/api/admin/firms", headers=O).status_code == 403, "firma yöneticisi platform uçlarına girmemeli"
        assert c.get("/api/admin/firms", headers=A).status_code == 200
    t("firma yöneticisi platform (firma listesi) ucuna giremez", p)
    def q():
        c.post("/api/admin/firms", headers=A, json={"name": "Baska Firma", "email": "x@baska.com", "password": "sifre12345", "features": {}})
        O2 = tok(c, "x@baska.com", "sifre12345"); assert c.get("/api/jobs", headers=O2).json() == [] and c.get("/api/customers", headers=O2).json() == []
        assert c.get("/api/service-settings", headers=O2).json()["foto_once"] == "istege_bagli"   # Ege'nin ayarı sızmaz
        assert c.get(f"/api/jobs/{S['done']}", headers=O2).status_code == 404
    t("firma izolasyonu: başka firma işi/müşteriyi/ayarı göremez", q)
print(f"GEÇTİ {len(ok)}/{len(ok)+len(bad)}")
for a in bad: print("BAŞARISIZ", a)
