# -*- coding: utf-8 -*-
"""Kampanya motoru testleri: X al Y öde, kademeli, sepet, kupon, kargo, birleşme kuralı."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import boot  # noqa: F401  (mongomock + ortam)
from kampanya import apply_campaigns, clean, eligible, summary

n = 0


def ok(c, m):
    global n
    assert c, m
    n += 1


def C(**kw):
    d = {"id": kw.pop("id", "c1"), "name": kw.pop("name", "Kampanya"), "on": True, "priority": 10,
         "exclusive": False, "start": "", "end": "", "scope": {"all": True}, "cond": {}, "gain": {},
         "limit": {}}
    d.update(kw)
    return d


def cart(*rows, ship=0.0):
    return {"items": [{"product": "p%d" % i, "name": r[0], "price": r[1], "qty": r[2],
                       "cat": r[3] if len(r) > 3 else "", "brand": ""} for i, r in enumerate(rows)],
            "ship": ship}

# 1) 3 al 2 öde: en ucuz bedava
r = apply_campaigns(cart(("Gömlek", 300, 1), ("Tişört", 100, 1), ("Kazak", 200, 1)),
                    [C(type="x_al_y_ode", cond={"buy": 3, "pay": 2})])
ok(r["discount"] == 100.0, "3 al 2 öde en ucuzu bedava vermeli, çıkan: %s" % r["discount"])
ok(r["total"] == 500.0, "toplam 500 olmalı: %s" % r["total"])

# 2) 3 al 2 öde aynı üründen 7 adet: iki grup tamam, 1 adet artar
r = apply_campaigns(cart(("Çorap", 50, 7)), [C(type="x_al_y_ode", cond={"buy": 3, "pay": 2})])
ok(r["discount"] == 100.0, "7 adette 2 adet bedava olmalı: %s" % r["discount"])

# 3) kapsam dışı ürün kampanyaya girmez
r = apply_campaigns(cart(("Gömlek", 300, 2, "ust"), ("Ayakkabı", 900, 1, "ayak")),
                    [C(type="x_al_y_ode", cond={"buy": 2, "pay": 1},
                       scope={"all": False, "cats": ["ust"]})])
ok(r["discount"] == 300.0, "sadece kapsamdaki gömlek bedava olmalı: %s" % r["discount"])

# 4) kademeli: 2 alana 3. ürün %50
r = apply_campaigns(cart(("A", 100, 3)), [C(type="kademeli", cond={"buy": 2, "give": 1},
                                            gain={"y_percent": 50})])
ok(r["discount"] == 50.0, "3. ürün yarı fiyat olmalı: %s" % r["discount"])

# 5) sepet indirimi eşiğin altında girmez, üstünde girer
c = C(type="sepet", cond={"min_total": 1000}, gain={"percent": 10})
r1 = apply_campaigns(cart(("A", 400, 2)), [c])
r2 = apply_campaigns(cart(("A", 400, 3)), [c])
ok(r1["discount"] == 0.0 and r2["discount"] == 120.0, "eşik: %s / %s" % (r1["discount"], r2["discount"]))
ok(any("tutar gerekli" in s["why"] for s in r1["skipped"]), "neden girmediği yazılmalı")

# 6) kupon kodu olmadan geçmez, kodla geçer
c = C(type="kupon", cond={"code": "hosgeldin"}, gain={"amount": 75})
ok(apply_campaigns(cart(("A", 500, 1)), [c])["discount"] == 0.0, "kod girilmeden indirim olmamalı")
r = apply_campaigns(cart(("A", 500, 1)), [c], {"code": "HOSGELDIN"})
ok(r["discount"] == 75.0, "kupon indirimi: %s" % r["discount"])

# 7) bedava kargo kargoyu sıfırlar
r = apply_campaigns(cart(("A", 600, 1), ship=49.9), [C(type="kargo", cond={"min_total": 500})])
ok(r["ship"] == 0.0 and r["free_ship"] and r["total"] == 600.0, "kargo bedava: %s" % r)

# 8) tek başına kampanya: müşteri lehine olan seçilir, diğeri gerekçeyle dışarıda kalır
camps = [C(id="a", name="Sepet 10", type="sepet", gain={"percent": 10}),
         C(id="b", name="Tek basina 25", type="sepet", gain={"percent": 25}, exclusive=True, priority=20)]
r = apply_campaigns(cart(("A", 1000, 1)), camps)
ok(r["discount"] == 250.0 and len(r["lines"]) == 1 and r["lines"][0]["id"] == "b",
   "tek basina 25 secilmeli: %s" % r["discount"])
ok(any(s["id"] == "a" for s in r["skipped"]), "birleşmeyen kampanya gerekçeli listelenmeli")

# 9) birleşebilenler toplanır
r = apply_campaigns(cart(("A", 1000, 1), ship=30),
                    [C(id="a", type="sepet", gain={"percent": 10}),
                     C(id="b", type="kargo")])
ok(r["discount"] == 100.0 and r["ship"] == 0.0 and r["total"] == 900.0, "iki kampanya birleşmeli: %s" % r)

# 10) tarih penceresi ve kapalı kampanya
ok(not eligible(C(type="sepet", end="2020-01-01", gain={"percent": 5}), cart(("A", 100, 1)), {})[0],
   "süresi bitmiş kampanya girmemeli")
ok(not eligible(C(type="sepet", on=False, gain={"percent": 5}), cart(("A", 100, 1)), {})[0],
   "kapalı kampanya girmemeli")

# 11) kullanım hakkı bitmişse girmez
ok(not eligible(C(type="sepet", gain={"percent": 5}, limit={"total": 10, "used": 10}),
                cart(("A", 100, 1)), {})[0], "kullanım hakkı bitmiş kampanya girmemeli")

# 12) satır indirimleri satır toplamıyla tutarlı
r = apply_campaigns(cart(("A", 333, 1), ("B", 667, 1)), [C(type="sepet", gain={"percent": 10})])
ok(round(sum(i["discount"] for i in r["items"]), 2) == r["discount"] == 100.0,
   "satır indirimleri toplamı kampanya indirimine eşit olmalı: %s" % r)
ok(r["items"][0]["line_total"] + r["items"][1]["line_total"] == 900.0, "satır toplamları tutmalı")

# 13) indirim satır tutarını aşmaz
r = apply_campaigns(cart(("A", 50, 1)), [C(type="urun", gain={"amount": 500})])
ok(r["discount"] == 50.0 and r["total"] == 0.0, "indirim ürün bedelini aşmamalı: %s" % r)

# 14) ilk sipariş / ödeme tipi koşulları
c = C(type="sepet", cond={"first_order": True, "payment": "havale"}, gain={"percent": 5})
ok(not eligible(c, cart(("A", 100, 1)), {"orders": 2, "payment": "havale"})[0], "ilk sipariş koşulu")
ok(eligible(c, cart(("A", 100, 1)), {"orders": 0, "payment": "havale"})[0], "koşullar tutunca girmeli")

# 15) doğrulama: hatalı X al Y öde reddedilir, özet metni üretilir
try:
    clean({"name": "Yanlış", "type": "x_al_y_ode", "cond": {"buy": 2, "pay": 3}, "scope": {"all": True}})
    ok(False, "ödenen adet alınandan büyükse hata vermeli")
except Exception as e:                                             # noqa: BLE001
    ok("büyük olmalı" in str(getattr(e, "detail", e)), "anlaşılır hata mesajı: %s" % e)
c = clean({"name": "Yazlık", "type": "x_al_y_ode", "cond": {"buy": 3, "pay": 2}, "scope": {"all": True}})
ok(summary(c) == "3 al 2 öde", "özet metni: %s" % summary(c))

print("OK %d geçti" % n)
