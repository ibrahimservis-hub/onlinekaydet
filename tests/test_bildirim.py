"""Bildirim ve SMS şablonları: sektöre göre metin, SMS parça hesabı, duyuru ve stok/fiyat haberi."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import bildirim as B
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:]))

# ---- saf hesaplar
def a():
    i = B.sms_info("Randevunuz yarin saat 15:30 icin alindi.")
    assert i["encoding"] == "GSM-7" and i["parts"] == 1, i
    i2 = B.sms_info("Randevunuz yarın saat 15:30 için alındı.")
    assert i2["unicode"] and i2["per_part"] == 70, "Türkçe karakter UCS-2'ye düşmeli: %s" % i2
    uzun = "a" * 161
    assert B.sms_info(uzun)["parts"] == 2 and B.sms_info(uzun)["per_part"] == 153, B.sms_info(uzun)
    tr = "ş" * 71
    assert B.sms_info(tr)["parts"] == 2 and B.sms_info(tr)["per_part"] == 67, B.sms_info(tr)
    assert B.sms_info("a" * 160)["parts"] == 1
    assert B.sms_info("€")["chars"] == 2, "uzantı karakteri 2 sayılır"
t("SMS parça hesabı GSM-7 ve UCS-2 kurallarına uyuyor", a)

def b():
    tr = "Sipariş kargoya verildi, iyi günler"
    i = B.sms_info(tr)
    assert i["unicode"] and i["simple"]["text"] == "Siparis kargoya verildi, iyi gunler"
    assert B.sms_info(i["simple"]["text"])["encoding"] == "GSM-7"
    uzun = "ğ" * 100
    i2 = B.sms_info(uzun)
    assert i2["parts"] == 2 and i2["simple"]["parts"] == 1, "sadeleşince tek SMS'e inmeli: %s" % i2
t("Türkçe karakterleri sadeleştirme seçeneği parça sayısını düşürüyor", b)

def d():
    assert B.render("Sayin {ad}, {tarih} randevunuz var", {"ad": "Ali", "tarih": "14 Kasım"}) \
        == "Sayin Ali, 14 Kasım randevunuz var"
    assert B.render("{ad} {yok}", {"ad": "Ali"}) == "Ali —", "karşılığı olmayan değişken boş bırakılmaz"
t("değişkenler dolduruluyor", d)

def e():
    try:
        B.check_text("randevu_hatirlatma", "Sayin {musteri_adi} gelin")
        assert False, "tanınmayan değişken kabul edilmemeli"
    except Exception as x:
        m = str(getattr(x, "detail", x))
        assert "{musteri_adi}" in m and "{ad}" in m, m
    B.check_text("randevu_hatirlatma", "Sayin {ad}, {tarih} {saat} randevunuz var")
    try:
        B.check_text("siparis_kargoda", "{personel} yola cikardi")
        assert False, "sipariş bildiriminde randevu değişkeni olmamalı"
    except Exception:
        pass
t("tanınmayan değişken kaydedilmiyor, kullanılabilir liste söyleniyor", e)

with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}

    def f():
        r = c.get("/api/yp/notify", headers=H).json()
        ids = [i["id"] for i in r["items"]]
        assert "randevu_hatirlatma" in ids, ids
        assert "siparis_kargoda" not in ids, "kuaförde sipariş bildirimi görünmemeli"
        assert r["sms_ready"] is False, "SMS sağlayıcısı yokken hazır değil"
        h = [i for i in r["items"] if i["id"] == "randevu_hatirlatma"][0]
        assert "randevunuzu hatirlatiriz" in h["text"] and h["sms"]["parts"] == 1
        assert not h["custom"] and h["on"]
    t("kuaförde yalnız randevu bildirimleri, hazır metinle geliyor", f)

    def g():
        c.post("/api/yp/sectors/eticaret", headers=H, json={})
        r = c.get("/api/yp/notify", headers=H).json()
        ids = [i["id"] for i in r["items"]]
        for x in ("siparis_kargoda", "stoga_geldi", "fiyat_dustu", "iade_onay"):
            assert x in ids, "%s eksik" % x
        s1 = [i for i in r["items"] if i["id"] == "siparis_alindi"][0]
        assert "siparisiniz alindi" in s1["text"], s1["text"]
        assert r["flow"] == "siparis", r["flow"]
    t("e-ticarete geçince sipariş, kargo ve stok bildirimleri açılıyor, metin sektöre göre", g)

    def h():
        r = c.put("/api/yp/notify/randevu_hatirlatma", headers=H,
                  json={"text": "{firma}: {ad}, yarin {saat} randevunuz var. Iptal: {iptal_link}",
                        "channels": ["sms", "whatsapp"]})
        assert r.status_code == 200, r.text
        it = r.json()["item"]
        assert it["custom"] and it["channels"] == ["sms", "whatsapp"]
        bad2 = c.put("/api/yp/notify/randevu_hatirlatma", headers=H, json={"text": "{yanlis_alan}"})
        assert bad2.status_code == 422 and "tanınmıyor" in bad2.json()["detail"], bad2.json()
        bos = c.put("/api/yp/notify/randevu_hatirlatma", headers=H, json={"text": "   "})
        assert bos.status_code == 422
        r2 = c.post("/api/yp/notify/randevu_hatirlatma/sifirla", headers=H).json()
        assert not r2["item"]["custom"] and "hatirlatiriz" in r2["item"]["text"], r2["item"]
    t("şablon düzenleniyor, bozulursa hazır metne dönülüyor", h)

    def i():
        r = c.post("/api/yp/notify/siparis_kargoda/onizle", headers=H,
                   json={"text": "{firma}: {siparis_no} siparişiniz {kargo} ile yolda. Takip: {takip}"}).json()
        assert "SP-2026-00412" in r["text"] and "Aras Kargo" in r["text"], r["text"]
        assert r["sms"]["unicode"], "Türkçe karakter var"
        r2 = c.post("/api/yp/notify/siparis_kargoda/onizle", headers=H,
                    json={"text": "{firma}: {siparis_no} siparişiniz yolda", "sade": True}).json()
        assert "siparisiniz" in r2["text"] and not r2["sms"]["unicode"], r2
    t("önizleme gerçek örnek veriyle doluyor, sadeleştirme çalışıyor", i)

    def k():
        st = c.get("/api/yp/boot", headers=H).json()["staff"][0]["id"]
        for n2 in range(3):
            rr = c.post("/api/yp/appts", headers=H, json={"name": "Müşteri %d" % n2, "phone": "053200000%02d" % n2,
                                                          "date": "2026-11-20", "time": "1%d:00" % n2,
                                                          "staff_id": st,
                                                          "items": [{"name": "Kesim", "price": 300, "dur": 30}]})
            assert rr.status_code == 200, rr.text
        r = c.post("/api/yp/notify/duyuru", headers=H,
                   json={"text": "Kasım ayına özel %20 indirim", "segment": "hepsi", "dene": True}).json()
        assert r["n"] >= 1, r
        assert r["sms"]["unicode"] and r["toplam_sms"] == r["n"] * r["sms"]["parts"], r
        assert "indirim" in r["ornek"]
        g2 = c.post("/api/yp/notify/duyuru", headers=H, json={"text": "Kasim indirimi", "segment": "hepsi"})
        assert g2.status_code == 422 and "SMS sağlayıcı" in g2.json()["detail"], g2.json()
        c.put("/api/yp/integrations/netgsm", headers=H,
              json={"keys": {"user": "850", "pass": "x", "header": "DEMO"}, "on": True})
        g3 = c.post("/api/yp/notify/duyuru", headers=H, json={"text": "Kasim indirimi", "segment": "hepsi"}).json()
        assert g3["n"] >= 1 and not g3["err"], g3
        lst = c.get("/api/yp/notify/duyuru/liste", headers=H).json()["items"]
        assert lst and lst[0]["state"] == "bitti" and lst[0]["total_sms"] == lst[0]["n"], lst[0]
    t("duyuru önce kaç kişi ve kaç SMS olduğunu söylüyor, sağlayıcısız göndermiyor", k)

    def l():
        pid = c.post("/api/yp/products", headers=H, json={"name": "Keten Gömlek", "price": 899,
                                                          "cost": 400, "stock": 0}).json()["id"]
        assert c.post("/api/yp/notify/takip", headers=H,
                      json={"product": pid, "phone": "05321112233", "kind": "stok"}).json()["ok"]
        c.post("/api/yp/notify/takip", headers=H, json={"product": pid, "phone": "05321112233", "kind": "fiyat"})
        assert c.post("/api/yp/notify/takip", headers=H,
                      json={"product": pid, "phone": "123"}).status_code == 422
        r = c.post("/api/yp/notify/takip/calistir", headers=H).json()
        assert r["n"] == 0, "stok hâlâ 0, fiyat düşmedi: %s" % r
        c.put("/api/yp/products/" + pid, headers=H, json={"stock": 5, "sale_price": 719})
        r2 = c.post("/api/yp/notify/takip/calistir", headers=H).json()
        assert r2["n"] == 2, "stoğa geldi ve fiyat düştü haberleri: %s" % r2
        r3 = c.post("/api/yp/notify/takip/calistir", headers=H).json()
        assert r3["n"] == 0, "aynı takip ikinci kez bildirilmemeli"
        log = c.get("/api/yp/notify/log", headers=H).json()["items"]
        olay = [x["event"] for x in log]
        assert "stoga_geldi" in olay and "fiyat_dustu" in olay, olay[:5]
        msg = [x for x in log if x["event"] == "fiyat_dustu"][0]["text"]
        assert "899" in msg and "719" in msg, msg
    t("stoğa gelince ve fiyat düşünce haber gidiyor, iki kez gitmiyor", l)

for x in ok: print("  ✓", x)
for x, e in bad: print("  ✗", x, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
