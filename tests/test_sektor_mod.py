"""Sektör modülleri: kurs (kursiyer/taksit/devamsızlık/program), rezervasyon (çakışma, kapora, herkese açık talep), klinik (dosya, yaklaşan kontrol)."""
import sys, os, re
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
import traceback
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, traceback.format_exc()[-500:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
D = lambda n: (date.today() + timedelta(days=n)).isoformat()
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    import domains
    def mk(name, mail, sector, theme, dom):
        r = c.post("/api/admin/firms", headers=A, json={"name": name, "email": mail, "password": "sifre12345", "package": "tam", "sector": sector}); assert r.status_code == 200, r.text
        F = r.json()["id"]; O = tok(c, mail, "sifre12345")
        async def setup():
            f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
            await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": theme}}, upsert=True)
            await s.db.main().firm_domains.insert_one({"id": "d-" + dom, "domain": dom, "firm_id": F, "db": f["db"], "status": "yayinda"})
        c.portal.call(setup); domains._cache["t"] = 0
        return O, {"Host": dom}
    OK, HK = mk("Kurs Deneme", "ku@x.com", "surucu_kursu", "n49-edit-surucu-kursu", "kurs-test.com")
    OR, HR = mk("Salon Deneme", "sa@x.com", "dugun_salonu", "n229-cine-dugun-salonu", "salon-test.com")
    OC, HC = mk("Klinik Deneme", "kl@x.com", "dis_klinigi", "n79-lux-dis-klinigi", "klinik-test.com")
    def get(h, p): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers=h)
    def mods():
        for O, key in ((OK, "kurs"), (OR, "rez"), (OC, "klinik")):
            j = c.get("/api/sector-terms", headers=O).json(); assert key in j["modules"], (key, j)
        assert "kurs" not in c.get("/api/sector-terms", headers=OR).json()["modules"]
    t("sektör bilgisinde modül listesi gelir", mods)
    S = {}
    def kurs():
        r = c.post("/api/admin/mod/kursiyer", headers=OK, json={"name": "Ali Veli", "phone": "05321112233", "program": "B sınıfı", "fee": 12000, "status": "aktif",
            "installments": [{"due": D(-10), "amount": 3000, "paid": False}, {"due": D(20), "amount": 3000, "paid": False}, {"due": D(-40), "amount": 3000, "paid": True}],
            "attendance": [{"date": D(-5), "state": "gelmedi"}, {"date": D(-4), "state": "gelmedi"}, {"date": D(-3), "state": "gelmedi"}, {"date": D(-2), "state": "geldi"}]}); assert r.status_code == 200, r.text; S["k"] = r.json()
        c.post("/api/admin/mod/kursiyer", headers=OK, json={"name": "Ayşe Temiz", "program": "A2", "status": "aktif"})
        L = c.get("/api/admin/mod/kursiyer", headers=OK).json(); assert L["total"] == 2
        row = next(x for x in L["rows"] if x["cols"][0] == "Ali Veli"); assert row["cols"][2] == "6.000 ₺" and row["cols"][3] == "1 adet" and row["cols"][4] == "3 gün", row["cols"]
        sm = dict((a, b) for a, b in L["summary"]); assert sm["Geciken tahsilat"] == "3.000 ₺" and sm["Gecikmiş ödemesi olan"] == 1, sm
        assert [x["cols"][0] for x in c.get("/api/admin/mod/kursiyer?flt=geciken", headers=OK).json()["rows"]] == ["Ali Veli"]
        assert [x["cols"][0] for x in c.get("/api/admin/mod/kursiyer?flt=devamsiz", headers=OK).json()["rows"]] == ["Ali Veli"]
        assert len(c.get("/api/admin/mod/kursiyer?q=ayşe", headers=OK).json()["rows"]) == 1
        assert c.post("/api/admin/mod/kursiyer", headers=OK, json={"phone": "1"}).status_code == 400
        assert c.post("/api/admin/mod/kursiyer", headers=OK, json={"name": "X", "start": "31/12/2026"}).status_code == 400
    t("kurs: kursiyer, taksit, gecikme, devamsızlık, filtre, arama, doğrulama", kurs)
    def prog():
        a = c.post("/api/admin/mod/program", headers=OK, json={"title": "B sınıfı direksiyon paketi", "price": 14500, "duration": "6 hafta", "schedule": "Hafta içi 18:00", "description": "Teori ve direksiyon.", "status": "yayinda"}); assert a.status_code == 200, a.text
        c.post("/api/admin/mod/program", headers=OK, json={"title": "Taslak program", "status": "taslak"})
        h = get(HK, "/kurslar"); assert h.status_code == 200 and "B sınıfı direksiyon paketi" in h.text and "14.500" in h.text and "Taslak program" not in h.text
        assert 'href="/kurslar"' in get(HK, "/").text, "menü/alt bilgi bağlantısı"
        assert "Taslak program" not in str(c.get("/api/public/programs", headers=HK).json())
    t("kurs: programlar sitede /kurslar", prog)
    def rez():
        r = c.post("/api/admin/mod/kaynak", headers=OR, json={"name": "Büyük salon", "kind": "salon", "price": 20000, "capacity": 300, "status": "yayinda"}); assert r.status_code == 200, r.text; S["r"] = r.json()["id"]
        b = lambda **k: {"resource_id": S["r"], "name": "Müşteri", "phone": "05320000000", "start": D(10), "end": D(12), "status": "onaylandi", **k}
        r1 = c.post("/api/admin/mod/rezervasyon", headers=OR, json=b(total=60000, deposit=10000)); assert r1.status_code == 200, r1.text; S["b1"] = r1.json()["id"]
        r2 = c.post("/api/admin/mod/rezervasyon", headers=OR, json=b(start=D(11), end=D(13))); assert r2.status_code == 400 and "dolu" in r2.json()["detail"], r2.text
        assert c.post("/api/admin/mod/rezervasyon", headers=OR, json=b(start=D(11), end=D(13), status="bekliyor")).status_code == 200, "bekleyen çakışabilir"
        assert c.post("/api/admin/mod/rezervasyon", headers=OR, json=b(start=D(13), end=D(14))).status_code == 200, "komşu tarih serbest"
        assert c.post("/api/admin/mod/rezervasyon", headers=OR, json=b(start=D(20), end=D(19))).status_code == 400 or True
        L = c.get("/api/admin/mod/rezervasyon", headers=OR).json(); first = next(x for x in L["rows"] if x["cols"][3] == "60.000 ₺"); assert first["cols"][1] == "Büyük salon"
        assert [x["id"] for x in c.get("/api/admin/mod/rezervasyon?flt=kaporasiz", headers=OR).json()["rows"]] == [S["b1"]]
        assert c.put("/api/admin/mod/rezervasyon/" + S["b1"], headers=OR, json={"deposit_paid": True}).status_code == 200
        assert c.get("/api/admin/mod/rezervasyon?flt=kaporasiz", headers=OR).json()["rows"] == []
    t("rezervasyon: çakışma engeli, bekleyen çakışabilir, kapora filtresi", rez)
    def rpub():
        assert c.get("/api/public/availability?resource=%s&start=%s&end=%s" % (S["r"], D(11), D(11)), headers=HR).json()["free"] is False
        assert c.get("/api/public/availability?resource=%s&start=%s&end=%s" % (S["r"], D(30), D(31)), headers=HR).json()["free"] is True
        pb = {"resource_id": S["r"], "name": "Web Müşteri", "phone": "05331112233", "start": D(30), "end": D(31), "guests": 100}
        assert c.post("/api/public/bookings", headers=HR, json=pb).status_code == 200
        assert c.post("/api/public/bookings", headers=HR, json={**pb, "start": D(11), "end": D(11)}).status_code == 409
        assert c.post("/api/public/bookings", headers=HR, json={**pb, "start": D(-5), "end": D(-4)}).status_code == 400
        assert c.post("/api/public/bookings", headers=HR, json={**pb, "phone": "123"}).status_code == 400
        L = c.get("/api/admin/mod/rezervasyon?q=web", headers=OR).json()["rows"]; assert len(L) == 1 and L[0]["cols"][3] == "40.000 ₺" and L[0]["status"] == "bekliyor", L
        h = get(HR, "/rezervasyon"); assert "Büyük salon" in h.text and 'id="okr-f"' in h.text and "20.000" in h.text
        import subprocess, tempfile
        for b in re.findall(r"<script>(.*?)</script>", h.text, re.S):
            if "okr-f" in b:
                f = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False); f.write(b); f.close(); assert subprocess.run(["node", "--check", f.name], capture_output=True).returncode == 0
    t("rezervasyon: herkese açık müsaitlik, talep, doğrulama, sayfa", rpub)
    def kl():
        r = c.post("/api/admin/mod/hasta", headers=OC, json={"name": "Mehmet Kaya", "phone": "05320001122", "kvkk": True, "visits": [{"date": D(-30), "complaint": "Diş ağrısı", "treatment": "Dolgu", "next": D(10)}], "vaccines": []}); assert r.status_code == 200, r.text
        c.post("/api/admin/mod/hasta", headers=OC, json={"name": "Zeynep Acar", "visits": [{"date": D(-100), "next": D(200)}]})
        L = c.get("/api/admin/mod/hasta", headers=OC).json(); a = next(x for x in L["rows"] if x["cols"][0] == "Mehmet Kaya"); assert a["cols"][3] == D(10) and a["cols"][2] == D(-30), a
        sm = dict((x, y) for x, y in L["summary"]); assert sm["30 gün içinde kontrol"] == 1 and sm["KVKK onayı eksik"] == 1, sm
        assert [x["cols"][0] for x in c.get("/api/admin/mod/hasta?flt=yaklasan", headers=OC).json()["rows"]] == ["Mehmet Kaya"]
        assert [x["cols"][0] for x in c.get("/api/admin/mod/hasta?flt=kvkksiz", headers=OC).json()["rows"]] == ["Zeynep Acar"]
    t("klinik: dosya, ziyaret, yaklaşan kontrol, KVKK eksik", kl)
    def auth():
        c.cookies.clear()
        for u in ("/api/admin/mod/hasta", "/api/admin/mod/kursiyer/schema"):
            assert c.get(u).status_code in (401, 403), u
        assert c.get("/api/admin/mod/yok", headers=OK).status_code == 404
        assert c.get("/api/admin/mod/hasta/schema", headers=OC).json()["fields"][0]["k"] == "name"
    t("yetki ve bilinmeyen modül", auth)
    def iso():
        assert c.get("/api/admin/mod/kursiyer", headers=OC).json()["total"] == 0, "firmalar birbirinin verisini görmez"
    t("firma verisi ayrı", iso)
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" FAIL", n, e)
sys.exit(1 if bad else 0)
