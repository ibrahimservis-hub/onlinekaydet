"""Sipariş ve iade: stok düşme/geri verme, durum akışı, kampanyalı sipariş, rapor."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    def mk(name, stock, price=900, cost=400):
        return c.post("/api/yp/products", headers=H, json={
            "name": name, "price": price, "cost": cost, "stock": stock, "cat": "Gömlek",
            "channels": {"trendyol": True}}).json()["id"]
    def stok(pid):
        r = c.get("/api/yp/products/" + pid, headers=H).json()
        return (r.get("item") or r)["stock"]

    def a():
        S["p1"] = mk("Keten Gömlek", 10)
        r = c.post("/api/yp/orders", headers=H, json={
            "channel": "site", "customer": {"name": "Mehmet Yıldız", "phone": "0532 111 22 33",
                                            "city": "İstanbul", "address": "Kadıköy"},
            "items": [{"product": S["p1"], "name": "Keten Gömlek", "price": 900, "qty": 2, "cost": 400}],
            "ship_fee": 50})
        assert r.status_code == 200, r.text
        o = r.json()["item"]; S["o1"] = o["id"]
        assert o["no"].startswith("SP-") and o["status"] == "yeni" and o["state_name"] == "Yeni sipariş"
        assert o["subtotal"] == 1800.0 and o["ship_fee"] == 50.0 and o["total"] == 1850.0
        assert o["customer"]["phone"] == "05321112233", o["customer"]["phone"]
        assert stok(S["p1"]) == 8, "sipariş kaydında stok düşmeli: %s" % stok(S["p1"])
    t("sipariş kaydediliyor, stok anında düşüyor", a)

    def b():
        r = c.post("/api/yp/orders", headers=H, json={
            "customer": {"name": "Zeynep"},
            "items": [{"product": S["p1"], "name": "Keten Gömlek", "price": 900, "qty": 50}]})
        assert r.status_code == 409, r.status_code
        assert "Stok yetersiz" in r.json()["detail"], r.json()
        assert stok(S["p1"]) == 8, "yetersiz stokta sipariş kaydı stoğa dokunmamalı"
        assert c.post("/api/yp/orders", headers=H, json={"customer": {"name": "X"}, "items": []}).status_code == 422
        assert c.post("/api/yp/orders", headers=H, json={
            "customer": {}, "items": [{"name": "A", "price": 10}]}).status_code == 422
    t("stok yetmezse sipariş hiç kaydedilmiyor, eksik bilgi reddediliyor", b)

    def d():
        g = c.get("/api/yp/orders/" + S["o1"], headers=H).json()["item"]
        assert [x["id"] for x in g["next"]] == ["onaylandi", "iptal"]
        assert c.post("/api/yp/orders/%s/status" % S["o1"], headers=H,
                      json={"status": "teslim"}).status_code == 422, "yeniden teslime atlanamaz"
        assert c.post("/api/yp/orders/%s/status" % S["o1"], headers=H, json={"status": "onaylandi"}).json()["ok"]
        r = c.post("/api/yp/orders/%s/status" % S["o1"], headers=H, json={"status": "kargoda"})
        assert r.status_code == 422 and "kargo firması" in r.json()["detail"], r.text
        c.put("/api/yp/orders/" + S["o1"], headers=H, json={"cargo": {"firm": "aras", "code": "1234567890"}})
        o = c.post("/api/yp/orders/%s/status" % S["o1"], headers=H, json={"status": "kargoda"}).json()["item"]
        assert o["cargo_name"] == "Aras Kargo"
        o = c.post("/api/yp/orders/%s/status" % S["o1"], headers=H, json={"status": "teslim"}).json()["item"]
        assert o["paid"] is True and len(o["timeline"]) >= 4, o["timeline"]
    t("durum akışı zorlanıyor, kargosuz sipariş kargoya verilemiyor", d)

    def e():
        o = c.post("/api/yp/orders", headers=H, json={
            "customer": {"name": "İptal Edilecek"},
            "items": [{"product": S["p1"], "name": "Keten Gömlek", "price": 900, "qty": 3}]}).json()["item"]
        assert stok(S["p1"]) == 5
        c.post("/api/yp/orders/%s/status" % o["id"], headers=H, json={"status": "iptal"})
        assert stok(S["p1"]) == 8, "iptalde stok geri dönmeli: %s" % stok(S["p1"])
        assert c.post("/api/yp/orders/%s/status" % o["id"], headers=H,
                      json={"status": "onaylandi"}).status_code == 422, "iptal edilen sipariş canlanmamalı"
    t("iptalde stok rafa geri dönüyor", e)

    def f():
        r = c.post("/api/yp/returns", headers=H, json={
            "order": S["o1"], "items": [{"product": S["p1"], "qty": 1, "reason": "bedeni olmadi"}],
            "detail": "Dar geldi"})
        assert r.status_code == 200, r.text
        ret = r.json()["item"]; S["r1"] = ret["id"]
        assert ret["no"].startswith("IA-") and ret["state"] == "talep" and ret["refund"] == 900.0
        assert c.post("/api/yp/returns", headers=H, json={
            "order": S["o1"], "items": [{"product": S["p1"], "qty": 5}]}).status_code == 422, "satılandan fazla iade"
        before = stok(S["p1"])
        c.post("/api/yp/returns/%s/state" % S["r1"], headers=H, json={"state": "onay"})
        assert stok(S["p1"]) == before + 1, "iade onayında stok geri eklenmeli"
        assert c.post("/api/yp/returns/%s/state" % S["r1"], headers=H,
                      json={"state": "red"}).status_code == 422, "onaydan redde dönülemez"
        rr = c.post("/api/yp/returns/%s/state" % S["r1"], headers=H,
                    json={"state": "tamam", "refund": 900}).json()["item"]
        assert rr["state"] == "tamam" and rr["refund_at"]
    t("iade talebi, onayda stok geri dönüyor, fazla iade engelleniyor", f)

    def g():
        c.post("/api/yp/campaigns", headers=H, json={
            "name": "3 al 2 öde", "type": "x_al_y_ode", "cond": {"buy": 3, "pay": 2}, "scope": {"all": True}})
        pid = mk("Çorap", 30, price=100, cost=30)
        o = c.post("/api/yp/orders", headers=H, json={
            "customer": {"name": "Kampanyalı"},
            "items": [{"product": pid, "name": "Çorap", "price": 100, "qty": 3, "cost": 30}]}).json()["item"]
        assert o["discount"] == 100.0 and o["total"] == 200.0, o
        assert o["camps"] and o["camps"][0]["name"] == "3 al 2 öde"
        assert stok(pid) == 27, "kampanyalı siparişte de stok 3 adet düşmeli"
        assert o["profit"] < 200.0 and o["profit"] > 0, "kâr indirim sonrası hesaplanmalı: %s" % o["profit"]
    t("kampanya siparişe otomatik işliyor, kâr indirim sonrası hesaplanıyor", g)

    def h():
        r = c.get("/api/yp/orders", headers=H, params={"q": "0532 111"}).json()
        assert r["total"] == 1 and r["items"][0]["customer"]["name"] == "Mehmet Yıldız", r["total"]
        assert c.get("/api/yp/orders", headers=H, params={"q": "Çorap"}).json()["total"] == 1
        assert c.get("/api/yp/orders", headers=H, params={"q": "1234567890"}).json()["total"] == 1
        a = c.get("/api/yp/orders", headers=H, params={"status": "acik"}).json()
        assert a["counts"]["iptal"] == 1 and a["counts"]["teslim"] == 1 and a["counts"]["hepsi"] == 3
        assert a["counts"]["acik"] == 1 and a["total"] == 1
        assert all(x["status"] in ("yeni", "onaylandi", "hazirlaniyor", "kargoda") for x in a["items"])
        assert c.get("/api/yp/orders", headers=H, params={"cargo": "aras"}).json()["total"] == 1
    t("sipariş arama ve filtreler çalışıyor (telefon, ürün, kargo kodu, durum)", h)

    def i():
        r = c.get("/api/yp/orders/report/ozet", headers=H).json()
        assert r["n"] == 2 and r["iptal"] == 1, r
        assert r["ciro"] == 2050.0, "iptal ciroya girmemeli: %s" % r["ciro"]
        assert r["indirim"] == 100.0 and r["iade"] == 900.0 and r["iade_n"] == 1
        assert r["sepet"] == 1025.0 and r["kar"] < r["ciro"]
        assert [k["id"] for k in r["kanallar"]][0] == "site"
        assert r["urunler"][0]["qty"] >= 3 and r["gunler"]
    t("sipariş raporu: ciro, kâr, indirim, iade, kanal ve ürün kırılımı", i)

    def k():
        r = c.post("/api/yp/campaigns/try", headers=H, json={
            "items": [{"product": S["p1"], "qty": 3}], "ship": 40}).json()
        assert r["discount"] == 900.0, r
        assert r["items"][0]["name"] == "Keten Gömlek", "ürün bilgisi karttan dolmalı"
    t("kampanya deneme ekranı ürün bilgisini kendi dolduruyor", k)

for n in ok: print("  ✓", n)
for n, e in bad: print("  ✗", n, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
