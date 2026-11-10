"""İş modülleri uçtan uca (gerçek uygulama + paket kapıları): muhasebe/kasa, personel maaşı, raporlar, kupon, bakım paketi, sadakat."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-500:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    def mk(name, email, mods):
        r = c.post("/api/admin/firms", headers=A, json={"name": name, "email": email, "password": "sifre12345", "package": "baslangic", "sector": "kuafor"}); assert r.status_code == 200, r.text
        assert c.put(f"/api/admin/firms/{r.json()['id']}", headers=A, json={"modules": mods}).status_code == 200
        return tok(c, email, "sifre12345")
    FULL = ["personel", "muhasebe", "rapor", "pazarlama", "randevu", "site"]
    H = mk("Tam Salon", "tam@salon.com", FULL)
    def bal(name):
        r = c.get("/api/finance/accounts", headers=H); assert r.status_code == 200, r.text
        return next(a for a in r.json() if a["name"] == name)
    def a():
        r = c.post("/api/finance/accounts", headers=H, json={"name": "Banka", "type": "banka", "opening_balance": 1000}); assert r.status_code == 200, r.text; S["bk"] = r.json()["id"]
        for ty, amt in (("gelir", 500), ("gider", 200)):
            r = c.post("/api/cash/transactions", headers=H, json={"type": ty, "amount": amt, "account_id": S["bk"], "description": "t", "category": "Genel"}); assert r.status_code == 200, r.text
        b = bal("Banka"); v = b.get("balance", b.get("current")); assert round(v) == 1300, b
    t("muhasebe: hesap açılışı + gelir/gider hesap bakiyesine işler (1000+500-200)", a)
    def b():
        accs = c.get("/api/finance/accounts", headers=H).json(); other = next(x for x in accs if x["id"] != S["bk"])
        r = c.post("/api/finance/transfer", headers=H, json={"amount": 300, "from_account_id": S["bk"], "to_account_id": other["id"]}); assert r.status_code == 200, r.text
        b = bal("Banka"); v = b.get("balance", b.get("current")); assert round(v) == 1000, b
        assert c.post("/api/finance/transfer", headers=H, json={"amount": 0, "from_account_id": S["bk"], "to_account_id": other["id"]}).status_code == 400
        assert c.post("/api/finance/transfer", headers=H, json={"amount": 5, "from_account_id": S["bk"], "to_account_id": S["bk"]}).status_code == 400
    t("virman: hesaplar arası aktarım bakiyeyi düşürür; sıfır tutar / aynı hesap reddedilir", b)
    def d():
        r = c.get("/api/cash/summary", headers=H).json(); assert r["income"] >= 500 and r["expense"] >= 200 and round(r["net_profit"], 2) == round(r["income"] - r["expense"] - r["technician_total_commission"], 2), r
        o = c.get("/api/finance/overview", headers=H); assert o.status_code == 200, o.text
    t("kasa özeti ve genel bakış tutarlı (net = gelir − gider − usta primi)", d)
    def e():
        r = c.post("/api/finance/staff", headers=H, json={"name": "Elif Usta", "title": "Kuaför", "salary": 20000}); assert r.status_code == 200, r.text; sid = r.json()["id"]
        r = c.post(f"/api/finance/staff/{sid}/pay", headers=H, json={"kind": "maas"}); assert r.status_code == 200 and r.json()["amount"] == 20000 and r.json()["category"] == "Maaş", r.text
        r = c.post(f"/api/finance/staff/{sid}/pay", headers=H, json={"kind": "avans", "amount": 1500}); assert r.status_code == 200, r.text
        st = next(x for x in c.get("/api/finance/staff", headers=H).json() if x["id"] == sid); assert st["salary_paid_this_month"] and st["advance_total"] == 1500 and st["paid_this_month"] == 21500, st
        assert c.post(f"/api/finance/staff/{sid}/pay", headers=H, json={"kind": "avans", "amount": 0}).status_code == 400
        sm = c.get("/api/cash/summary", headers=H).json(); assert sm["expense"] >= 200 + 21500, sm
    t("personel: maaş + avans ödemesi gider olarak kasaya işler, aylık toplamlar doğru", e)
    def f():
        for p in ("ozet", "musteri", "usta", "site", "finans"):
            r = c.get("/api/rapor/" + p, headers=H); assert r.status_code == 200, (p, r.status_code, r.text[:150])
        fin = c.get("/api/rapor/finans", headers=H).json(); assert isinstance(fin, dict) and fin, fin
    t("raporlar: özet / müşteri / usta / site / finans uçları açılır", f)
    def g():
        r = c.post("/api/growth/coupons", headers=H, json={"code": "yaz10", "type": "percent", "value": 10, "max_uses": 2, "label": "Yaz"}); assert r.status_code == 200 and r.json()["code"] == "YAZ10", r.text
        assert c.post("/api/growth/coupons", headers=H, json={"code": "YAZ10", "type": "percent", "value": 5}).status_code == 400, "aynı kod tekrar açılamaz"
        assert c.post("/api/growth/coupons", headers=H, json={"code": "BUYUK", "type": "percent", "value": 150}).status_code == 422
        D = {"Host": "x"}
        j = c.get("/api/public/coupon/yaz10", headers=H).json(); assert j["valid"] and j["value"] == 10, j
        assert c.get("/api/public/coupon/YOKKOD", headers=H).json()["valid"] is False
        cid = r.json()["id"]; assert c.put(f"/api/growth/coupons/{cid}", headers=H, json={"active": False}).status_code == 200
        assert c.get("/api/public/coupon/YAZ10", headers=H).json()["valid"] is False, "pasif kupon geçersiz"
    t("kupon: oluştur, tekrar/aşırı yüzde reddi, geçerlilik kontrolü, pasife alınca geçersiz", g)
    def h():
        cu = c.post("/api/customers", headers=H, json={"name": "Ayşe Müşteri", "phone": "05321112233"}); assert cu.status_code == 200, cu.text
        pk = c.post("/api/growth/packages", headers=H, json={"name": "5'li Bakım", "price": 1000, "period_months": 6, "visits": 2}); assert pk.status_code == 200, pk.text
        sb = c.post("/api/growth/subscriptions", headers=H, json={"package_id": pk.json()["id"], "customer_id": cu.json()["id"]}); assert sb.status_code == 200, sb.text
        sid = sb.json()["id"]
        before = c.get("/api/cash/summary", headers=H).json()["income"]
        v1 = c.post(f"/api/growth/subscriptions/{sid}/visit", headers=H, json={}); assert v1.status_code == 200 and v1.json()["visits_left"] == 1, v1.text
        assert c.post(f"/api/growth/subscriptions/{sid}/visit", headers=H, json={}).status_code == 200
        assert c.post(f"/api/growth/subscriptions/{sid}/visit", headers=H, json={}).status_code == 400, "hak bitince ziyaret yazılamaz"
        assert before >= 1000, "paket bedeli gelir olarak kasaya işlenmeli"
        S["cust"] = cu.json()["id"]
    t("bakım paketi: abonelik gelir yazar, ziyaret hakkı düşer, hak bitince reddeder", h)
    def i():
        assert c.get("/api/growth/loyalty", headers=H).status_code == 200
        r = c.get(f"/api/growth/loyalty/{S['cust']}", headers=H); assert r.status_code == 200 and r.json()["balance"] == 0, r.text
        assert c.post(f"/api/growth/loyalty/{S['cust']}/redeem", headers=H, json={"points": 10, "job_id": "yok"}).status_code in (400, 404)
    t("sadakat: pano ve müşteri bakiyesi açılır; bakiyesiz/olmayan işte puan harcanamaz", i)
    def k():
        E = mk("Boş Salon", "bos@salon.com", ["site"])
        for p in ("/api/finance/accounts", "/api/cash/summary", "/api/rapor/ozet", "/api/growth/coupons", "/api/growth/packages", "/api/finance/staff"):
            r = c.get(p, headers=E); assert r.status_code == 403 and "paketinizde yok" in r.text, (p, r.status_code)
        M = mk("Sadece Muhasebe", "muh@salon.com", ["muhasebe"])
        assert c.get("/api/finance/accounts", headers=M).status_code == 200 and c.get("/api/rapor/ozet", headers=M).status_code == 403 and c.get("/api/growth/coupons", headers=M).status_code == 403
    t("paket kapıları: boş pakette muhasebe/rapor/kupon/paket/personel 403; muhasebe paketi yalnız muhasebeyi açar", k)
print("OK", len(ok), "FAIL", len(bad))
for n, e in bad: print("-", n, "\n", e)
sys.exit(1 if bad else 0)
