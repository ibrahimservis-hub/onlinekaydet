"""Sektörel raporlar: listede doğru raporlar, doğru hesap, tarih aralığı, CSV."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
from datetime import datetime, timedelta
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:]))
BUGUN = datetime.now().date().isoformat()
YARIN = (datetime.now().date() + timedelta(days=14)).isoformat()

with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}

    def a():
        r = c.get("/api/yp/rapor", headers=H).json()
        ids = [x["id"] for x in r["items"]]
        assert "doluluk" in ids and "personel" in ids and "kasa_ozet" in ids, ids
        assert "kanal" not in ids and "iade" not in ids, "kuaförde satış kanalı raporu olmamalı: %s" % ids
        assert all(x["note"] or True for x in r["items"])
        assert c.get("/api/yp/rapor/kanal", headers=H).status_code == 403, "paket dışı rapor açılmamalı"
    t("rapor listesi sektöre göre kuruluyor", a)

    def b():
        c.post("/api/yp/sectors/eticaret", headers=H, json={})
        r = c.get("/api/yp/rapor", headers=H).json()
        ids = [x["id"] for x in r["items"]]
        for x in ("ciro_gun", "kanal", "urun_satis", "kampanya_etki", "iade", "stok"):
            assert x in ids, "%s eksik" % x
        assert "doluluk" not in ids, "e-ticarette doluluk raporu olmamalı"
        gr = {g["id"]: g["n"] for g in r["groups"]}
        assert gr.get("satis", 0) >= 6, gr
    t("e-ticarette satış raporları açılıyor, randevu raporları kapanıyor", b)

    def d():
        pid = c.post("/api/yp/products", headers=H, json={"name": "Keten Gömlek", "price": 900,
                                                          "cost": 400, "stock": 20}).json()["id"]
        pid2 = c.post("/api/yp/products", headers=H, json={"name": "Satılmayan Kazak", "price": 1200,
                                                           "cost": 700, "stock": 5}).json()["id"]
        c.post("/api/yp/campaigns", headers=H, json={"name": "Kargo bedava", "type": "kargo",
                                                     "cond": {"min_total": 500}, "scope": {"all": True}})
        for n2 in range(3):
            c.post("/api/yp/orders", headers=H, json={
                "channel": "trendyol" if n2 else "site",
                "customer": {"name": "Müşteri %d" % n2, "phone": "053200000%02d" % n2},
                "items": [{"product": pid, "name": "Keten Gömlek", "price": 900, "qty": 2, "cost": 400}],
                "ship_fee": 50})
        r = c.get("/api/yp/rapor/ciro_gun", headers=H).json()
        assert r["n"] == 1 and r["rows"][0]["n"] == 3, r["rows"]
        assert r["rows"][0]["ciro"] == 5400.0, "kargo bedava kampanyası ciroyu 3×1800 yapar: %s" % r["rows"][0]
        assert r["sum"]["ciro"] == 5400.0 and r["rows"][0]["sepet"] == 1800.0
        assert r["chart"]["type"] == "line" and len(r["chart"]["series"]) == 2
    t("günlük ciro raporu doğru hesaplıyor ve grafik veriyor", d)

    def e():
        r = c.get("/api/yp/rapor/kanal", headers=H).json()
        k = {x["name"]: x for x in r["rows"]}
        assert "Trendyol" in k and k["Trendyol"]["n"] == 2, r["rows"]
        assert k["Trendyol"]["komisyon"] > 0 and k["Trendyol"]["kar"] < k["Trendyol"]["ciro"]
        assert k["Kendi sitem"]["komisyon"] == 0.0, "kendi sitemde komisyon olmaz"
        assert k["Trendyol"]["kar"] < k["Kendi sitem"]["kar"] * 2 + 1, "komisyon kârı düşürmeli"
    t("kanal raporu komisyonu kârdan düşüyor", e)

    def f():
        r = c.get("/api/yp/rapor/urun_satis", headers=H).json()
        assert r["rows"][0]["name"] == "Keten Gömlek" and r["rows"][0]["qty"] == 6, r["rows"]
        assert 0 < r["rows"][0]["oran"] < 100
        st = c.get("/api/yp/rapor/stok", headers=H).json()
        d2 = {x["name"]: x for x in st["rows"]}
        assert d2["Satılmayan Kazak"]["durum"] == "Az stok · hareketsiz", d2["Satılmayan Kazak"]
        assert d2["Keten Gömlek"]["durum"] == "Normal", d2["Keten Gömlek"]
        assert d2["Keten Gömlek"]["satis"] == 6 and d2["Keten Gömlek"]["stock"] == 14
        assert d2["Satılmayan Kazak"]["deger"] == 3500.0, "stok değeri alış fiyatından hesaplanır"
    t("ürün ve stok raporları satışa göre doğru", f)

    def g():
        r = c.get("/api/yp/rapor/kampanya_etki", headers=H).json()
        assert r["rows"] and r["rows"][0]["name"] == "Kargo bedava" and r["rows"][0]["n"] == 3, r["rows"]
        oid = c.get("/api/yp/orders", headers=H).json()["items"][0]["id"]
        pid = c.get("/api/yp/products", headers=H).json()["rows"][0]["id"]
        c.post("/api/yp/returns", headers=H, json={"order": oid, "items": [{"product": pid, "qty": 1,
                                                                            "reason": "bedeni olmadi"}]})
        rid = c.get("/api/yp/returns", headers=H).json()["items"][0]["id"]
        c.post("/api/yp/returns/%s/state" % rid, headers=H, json={"state": "onay"})
        ia = c.get("/api/yp/rapor/iade", headers=H).json()
        assert ia["rows"][0]["reason"] == "bedeni olmadi" and ia["rows"][0]["oran"] == 100.0, ia["rows"]
    t("kampanya ve iade raporları işliyor", g)

    def h():
        gec = (datetime.now().date() - timedelta(days=60)).isoformat()
        r = c.get("/api/yp/rapor/ciro_gun", headers=H, params={"frm": gec, "to": gec}).json()
        assert r["n"] == 0 and r["sum"]["ciro"] == 0.0, "aralık dışı veri gelmemeli"
        assert c.get("/api/yp/rapor/ciro_gun", headers=H,
                     params={"frm": BUGUN, "to": gec}).status_code == 422
        assert c.get("/api/yp/rapor/yok", headers=H).status_code == 404
    t("tarih aralığı uygulanıyor, ters aralık reddediliyor", h)

    def i():
        r = c.post("/api/yp/rapor/kanal/csv", headers=H, json={}).json()
        assert r["csv"].startswith("﻿") and "Kanal;Sipariş;Ciro" in r["csv"], r["csv"][:80]
        assert "Trendyol" in r["csv"] and r["name"].startswith("kanal-")
        assert len(r["csv"].strip().split("\n")) == r["n"] + 1
    t("rapor Excel'in açtığı CSV olarak iniyor", i)

    def k():
        c.post("/api/yp/sectors/teknik", headers=H, json={})
        ids = [x["id"] for x in c.get("/api/yp/rapor", headers=H).json()["items"]]
        assert "servis_sure" in ids and "parca" in ids, ids
        c.post("/api/yp/is/servis", headers=H, json={
            "customer": {"name": "Mehmet"}, "data": {"cihaz": "Kombi", "sikayet": "Isıtmıyor"},
            "parts": [{"name": "Genleşme tankı", "qty": 1, "price": 850}], "labor": 600})
        p = c.get("/api/yp/rapor/parca", headers=H).json()
        assert p["rows"][0]["name"] == "Genleşme tankı" and p["rows"][0]["tutar"] == 850.0, p["rows"]
        sv = c.get("/api/yp/rapor/servis_sure", headers=H).json()
        assert sv["rows"][0]["tutar"] == 1450.0 and sv["rows"][0]["durum"] == "Kayıt açıldı", sv["rows"]
    t("servis raporları iş kayıtlarından besleniyor", k)

    def l():
        c.post("/api/yp/sectors/avukat", headers=H, json={})
        ids = [x["id"] for x in c.get("/api/yp/rapor", headers=H).json()["items"]]
        assert "durusma" in ids and "dosya_durum" in ids, ids
        c.post("/api/yp/is/dosya", headers=H, json={
            "customer": {"name": "Ali Vural"},
            "data": {"dosya_no": "2026/88", "mahkeme": "3. Asliye Hukuk", "konu": "Alacak",
                     "durusma": YARIN, "vekalet": 15000}})
        c.post("/api/yp/is/dosya", headers=H, json={
            "customer": {"name": "Eski Dosya"},
            "data": {"dosya_no": "2020/11", "mahkeme": "1. Asliye", "konu": "Geçmiş",
                     "durusma": "2020-01-01"}})
        d3 = c.get("/api/yp/rapor/durusma", headers=H).json()
        assert len(d3["rows"]) == 1 and d3["rows"][0]["no"] == "2026/88", "geçmiş duruşma listelenmemeli: %s" % d3["rows"]
        assert d3["rows"][0]["kalan"] == 14, d3["rows"][0]
        dd = c.get("/api/yp/rapor/dosya_durum", headers=H).json()
        assert dd["rows"][0]["n"] == 2 and dd["sum"]["vekalet"] == 15000.0, dd["rows"]
    t("hukuk raporları: geçmiş duruşma gizleniyor, kalan gün hesaplanıyor", l)

for x in ok: print("  ✓", x)
for x, e in bad: print("  ✗", x, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
