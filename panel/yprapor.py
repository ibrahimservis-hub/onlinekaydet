# -*- coding: utf-8 -*-
"""Sektörel raporlar: işletme hangi işi yapıyorsa o raporları görür.

Kuaförün "stok devir hızı" raporuna, e-ticaretçinin "personel doluluğu"
raporuna ihtiyacı yok. Rapor listesi firmanın modüllerine göre kuruluyor.

Rapor tanımı veri; hesap ayrı bir fonksiyon. Panel tabloyu ve grafiği tanımdan
kuruyor, böylece yeni rapor eklemek bir tanım ve bir fonksiyon yazmak demek.

Sayılar yorumlanmadan verilmiyor: her raporun altında ne anlama geldiğini
söyleyen bir satır var, çünkü "iade oranı %4" tek başına iyi mi kötü mü
belli değildir.
"""
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

GROUPS = [("satis", "Satış"), ("musteri", "Müşteri"), ("randevu", "Randevu"),
          ("servis", "Servis"), ("hukuk", "Dosya"), ("kasa", "Kasa")]


def C(key, label, typ="text", sum_=False):
    return {"key": key, "label": label, "type": typ, "sum": sum_}


def R(rid, name, desc, group, cols, modules=(), chart="", note=""):
    return {"id": rid, "name": name, "desc": desc, "group": group, "cols": cols,
            "modules": list(modules), "chart": chart, "note": note}


REPORTS = [
    R("ciro_gun", "Günlük ciro", "Hangi gün ne kadar sattınız", "satis",
      [C("day", "Gün", "date"), C("n", "Sipariş", "num", True), C("ciro", "Ciro", "para", True),
       C("kar", "Net kâr", "para", True), C("sepet", "Ortalama sepet", "para")],
      ["siparis"], chart="line"),
    R("kanal", "Satış kanalları", "Hangi kanal ne kazandırıyor", "satis",
      [C("name", "Kanal"), C("n", "Sipariş", "num", True), C("ciro", "Ciro", "para", True),
       C("komisyon", "Komisyon", "para", True), C("kar", "Net kâr", "para", True),
       C("oran", "Kâr oranı", "yuzde")],
      ["siparis"], chart="bar",
      note="Komisyon düşülmüş kâra bakın: cirosu yüksek kanal her zaman kârlı değildir."),
    R("urun_satis", "En çok satanlar", "Adet ve kâr olarak", "satis",
      [C("name", "Ürün"), C("qty", "Adet", "num", True), C("ciro", "Ciro", "para", True),
       C("kar", "Kâr", "para", True), C("oran", "Kâr oranı", "yuzde")],
      ["siparis"], chart="bar",
      note="Çok satan ile çok kazandıran aynı ürün olmayabilir."),
    R("kampanya_etki", "Kampanya etkisi", "Hangi kampanya ne getirdi", "satis",
      [C("name", "Kampanya"), C("n", "Kullanım", "num", True), C("indirim", "Verilen indirim", "para", True),
       C("ciro", "Getirdiği ciro", "para", True), C("sepet", "Ortalama sepet", "para")],
      ["kampanya"],
      note="Kampanyalı sepet ortalaması kampanyasızdan düşükse indirim ciroyu büyütmüyor demektir."),
    R("sepet_terk", "Sepet terki", "Ödemeye gitmeyen sepetler ve bekleyen tutar", "satis",
      [C("name", "Müşteri"), C("phone", "Telefon"), C("urun", "Ürünler"), C("tutar", "Sepet tutarı", "para", True),
       C("bekleme", "Bekleme"), C("durum", "Durum")],
      ["shop"], chart="",
      note="Terk edilen sepet, ödeme noktasına gelmeden bırakılan sepettir. Hatırlatma SMS'i bu tutarın bir bölümünü geri kazandırır."),
    R("stok_devir", "Stok devir hızı", "Ürün ne kadar hızlı satılıp yenileniyor", "satis",
      [C("name", "Ürün"), C("stok", "Stok", "num", True), C("satis", "Satılan", "num", True), C("devir", "Devir (satılan/stok)", "num"), C("durum", "Yorum")],
      ["shop"], chart="bar",
      note="Devir 1'in altındaysa ürün stokta bekliyor, 3 ve üstüyse stok yetmeyebilir; ikisi de nakit akışını etkiler."),
    R("iade", "İadeler", "Oran ve sebep kırılımı", "satis",
      [C("reason", "Sebep"), C("n", "Adet", "num", True), C("tutar", "Tutar", "para", True),
       C("oran", "Payı", "yuzde")],
      ["iade"], chart="bar",
      note="Aynı sebep tekrarlıyorsa sorun üründe ya da ürün sayfasındadır."),
    R("stok", "Stok durumu", "Değer, az stok ve hareketsizler", "satis",
      [C("name", "Ürün"), C("stock", "Stok", "num", True), C("deger", "Stok değeri", "para", True),
       C("satis", "Dönemde satılan", "num", True), C("durum", "Durum")],
      ["stok"],
      note="Dönemde hiç satılmayan ürünler parayı rafta tutar."),
    R("musteri_ozet", "Müşteri özeti", "Yeni ve tekrar gelen", "musteri",
      [C("day", "Ay", "date"), C("yeni", "Yeni müşteri", "num", True),
       C("tekrar", "Tekrar gelen", "num", True), C("oran", "Tekrar oranı", "yuzde")],
      [], chart="line",
      note="Tekrar oranı düşüyorsa yeni müşteri bulmak için harcadığınız para yerinde durmuyor."),
    R("doluluk", "Doluluk", "Gün ve saate göre", "randevu",
      [C("slot", "Saat"), C("n", "Randevu", "num", True), C("oran", "Doluluk", "yuzde")],
      ["randevu"], chart="bar",
      note="Boş saatleri kampanyayla doldurmak, yeni müşteri bulmaktan ucuzdur."),
    R("personel", "Personel", "Kişi başına iş ve ciro", "randevu",
      [C("name", "Kişi"), C("n", "Randevu", "num", True), C("ciro", "Ciro", "para", True),
       C("gelmedi", "Gelmeyen", "num", True), C("ort", "Ortalama tutar", "para")],
      ["randevu"], chart="bar"),
    R("gelmeyen", "Gelmeyenler", "Kim ne kadar boş yere yer tuttu", "randevu",
      [C("name", "Müşteri"), C("phone", "Telefon"), C("n", "Gelmedi", "num", True),
       C("son", "Son randevu", "date")],
      ["randevu"],
      note="İki kez gelmeyen müşteriden ön ödeme istemek yaygın bir çözümdür."),
    R("servis_sure", "İş süreleri", "Açılıştan tamamlanmaya", "servis",
      [C("name", "Kayıt"), C("musteri", "Müşteri"), C("gun", "Gün", "num"),
       C("tutar", "Tutar", "para", True), C("durum", "Durum")],
      ["servis"],
      note="Uzun süren işler genelde parça bekler; parça stoğu bu listeden çıkar."),
    R("parca", "Parça kullanımı", "En çok kullanılan ve en pahalı parçalar", "servis",
      [C("name", "Parça"), C("qty", "Adet", "num", True), C("tutar", "Tutar", "para", True)],
      ["servis"], chart="bar",
      note="Sürekli kullandığınız parçayı stokta tutmak işi bir güne indirir."),
    R("dosya_durum", "Dosya durumu", "Hangi aşamada kaç dosya", "hukuk",
      [C("durum", "Aşama"), C("n", "Dosya", "num", True), C("vekalet", "Vekâlet ücreti", "para", True)],
      ["evrak"], chart="bar"),
    R("durusma", "Yaklaşan duruşmalar", "Tarihe göre sıralı", "hukuk",
      [C("durusma", "Duruşma", "date"), C("no", "Dosya"), C("mahkeme", "Mahkeme"),
       C("musteri", "Müvekkil"), C("kalan", "Kalan gün", "num")],
      ["evrak"],
      note="Bu liste tarih sırasıyla gelir; geçmiş duruşmalar görünmez."),
    R("kasa_ozet", "Kasa özeti", "Gelir, gider ve net", "kasa",
      [C("day", "Gün", "date"), C("gelir", "Gelir", "para", True), C("gider", "Gider", "para", True),
       C("net", "Net", "para", True)],
      ["kasa"], chart="line"),
]
BY_ID = {r["id"]: r for r in REPORTS}


def _now():
    return datetime.now(TR).replace(tzinfo=None)


def _d(v, d=None):
    v = str(v or "")[:10]
    return v if len(v) == 10 and v[4] == "-" else (d or "")


def _n(v, d=0.0):
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return d


def _pct(a, b):
    return round(a / b * 100, 1) if b else 0.0


def register(api_router, db, deps):
    adm = deps["require_admin"]

    async def modul():
        d = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
        mods = d.get("modules")
        sec = d.get("sector")
        if not sec:
            s = await db.app_settings.find_one({"_id": "sector"}, {"_id": 0}) or {}
            sec = s.get("key") or ""
        try:
            import blocks
            mods, sec, _e = await blocks.firma_modulleri(db)
        except Exception:                                          # noqa: BLE001
            mods = list(mods or [])
        return set(mods or []), sec

    async def hangi():
        mods, sec = await modul()
        out = []
        izin = ((await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0, "reports_allowed": 1})) or {}).get("reports_allowed")
        for r in REPORTS:
            if r["modules"] and not (set(r["modules"]) & mods):
                continue
            if izin is not None and r["id"] not in izin:                    # sahip bu firmaya yalnız seçili raporları açtı
                continue
            out.append(r)
        return out

    @api_router.get("/yp/rapor")
    async def liste(_: dict = Depends(adm)):
        rs = await hangi()
        return {"items": [{k: r[k] for k in ("id", "name", "desc", "group", "chart", "note", "cols")} for r in rs],
                "groups": [{"id": g, "name": n, "n": len([r for r in rs if r["group"] == g])}
                           for g, n in GROUPS if any(r["group"] == g for r in rs)]}

    # ---------------------------------------------------------- hesaplar
    async def siparisler(a, b):
        rows = await db.yp_orders.find({"at": {"$gte": a, "$lte": b + "T99"}}, {"_id": 0}).to_list(20000)
        return [o for o in rows if o.get("status") != "iptal"]

    async def hesap(rid, a, b):
        import siparis as S
        if rid == "ciro_gun":
            g = {}
            for o in await siparisler(a, b):
                d = g.setdefault(str(o.get("at"))[:10], {"day": str(o.get("at"))[:10], "n": 0, "ciro": 0.0, "kar": 0.0})
                d["n"] += 1
                d["ciro"] = round(d["ciro"] + _n(o.get("total")), 2)
                d["kar"] = round(d["kar"] + S.order_profit(o), 2)
            rows = sorted(g.values(), key=lambda r: r["day"])
            for r in rows:
                r["sepet"] = round(r["ciro"] / r["n"], 2) if r["n"] else 0.0
            return rows
        if rid == "kanal":
            from urun import CHANNELS
            g = {}
            for o in await siparisler(a, b):
                k = o.get("channel", "site")
                nm, kom = CHANNELS.get(k, (k, 0.0))
                d = g.setdefault(k, {"name": nm, "n": 0, "ciro": 0.0, "komisyon": 0.0, "kar": 0.0})
                d["n"] += 1
                d["ciro"] = round(d["ciro"] + _n(o.get("total")), 2)
                d["komisyon"] = round(d["komisyon"] + _n(o.get("total")) * kom / 100.0, 2)
                d["kar"] = round(d["kar"] + S.order_profit(o), 2)
            rows = sorted(g.values(), key=lambda r: -r["ciro"])
            for r in rows:
                r["oran"] = _pct(r["kar"], r["ciro"])
            return rows
        if rid == "sepet_terk":
            rows = []
            for c in await db.shop_carts.find({}, {"_id": 0}).sort("updated_at", -1).to_list(2000):
                if str(c.get("updated_at", ""))[:10] < a or str(c.get("updated_at", ""))[:10] > b:
                    continue
                try:
                    dk = int((datetime.now(timezone.utc) - datetime.fromisoformat(c["updated_at"])).total_seconds() // 60)
                except Exception:                                  # noqa: BLE001
                    dk = 0
                rows.append({"name": c.get("name") or "—", "phone": c.get("phone", ""), "urun": ", ".join("%s ×%s" % (i["name"], i["q"]) for i in c.get("items", []))[:120],
                             "tutar": round(_n(c.get("total")), 2), "bekleme": ("%d sa" % (dk // 60)) if dk >= 60 else ("%d dk" % dk),
                             "durum": ("Terk edildi" if dk >= 60 else "Aktif") + (" · hatırlatıldı" if c.get("hatirlatildi") else "")})
            return rows
        if rid == "stok_devir":
            rows = []
            for p in await db.shop_products.find({"track_stock": {"$ne": False}}, {"_id": 0}).to_list(5000):
                st, sat = int(p.get("stock") or 0), int(p.get("sold") or 0)
                dv = round(sat / st, 2) if st else (float(sat) if sat else 0.0)
                rows.append({"name": p.get("name"), "stok": st, "satis": sat, "devir": dv,
                             "durum": "Tükendi" if st <= 0 else ("Stokta bekliyor" if dv < 1 else ("Hızlı dönüyor, stok yetmeyebilir" if dv >= 3 else "Dengeli"))})
            return sorted(rows, key=lambda r: r["devir"])
        if rid == "urun_satis":
            g = {}
            for o in await siparisler(a, b):
                kom = dict(__import__("urun").CHANNELS).get(o.get("channel"), ("", 0.0))[1]
                for it in o.get("items") or []:
                    d = g.setdefault(it.get("name", ""), {"name": it.get("name", ""), "qty": 0,
                                                          "ciro": 0.0, "kar": 0.0})
                    q = int(it.get("qty") or 1)
                    line = _n(it.get("price")) * q - _n(it.get("discount"))
                    d["qty"] += q
                    d["ciro"] = round(d["ciro"] + line, 2)
                    from urun import profit
                    d["kar"] = round(d["kar"] + profit(line, _n(it.get("cost")) * q,
                                                       _n(it.get("vat"), 20.0), kom, 0.0)["net"], 2)
            rows = sorted(g.values(), key=lambda r: -r["qty"])[:50]
            for r in rows:
                r["oran"] = _pct(r["kar"], r["ciro"])
            return rows
        if rid == "kampanya_etki":
            g = {}
            for o in await siparisler(a, b):
                for c in o.get("camps") or []:
                    d = g.setdefault(c.get("name", ""), {"name": c.get("name", ""), "n": 0,
                                                         "indirim": 0.0, "ciro": 0.0})
                    d["n"] += 1
                    d["indirim"] = round(d["indirim"] + _n(c.get("discount")), 2)
                    d["ciro"] = round(d["ciro"] + _n(o.get("total")), 2)
            rows = sorted(g.values(), key=lambda r: -r["ciro"])
            for r in rows:
                r["sepet"] = round(r["ciro"] / r["n"], 2) if r["n"] else 0.0
            return rows
        if rid == "iade":
            rets = await db.yp_returns.find({"at": {"$gte": a, "$lte": b + "T99"},
                                             "state": {"$in": ["onay", "tamam"]}}, {"_id": 0}).to_list(5000)
            top = sum(_n(r.get("refund")) for r in rets) or 0.0
            g = {}
            for r in rets:
                k = r.get("reason") or "diger"
                d = g.setdefault(k, {"reason": k, "n": 0, "tutar": 0.0})
                d["n"] += 1
                d["tutar"] = round(d["tutar"] + _n(r.get("refund")), 2)
            rows = sorted(g.values(), key=lambda r: -r["tutar"])
            for r in rows:
                r["oran"] = _pct(r["tutar"], top)
            return rows
        if rid == "stok":
            satis = {}
            for o in await siparisler(a, b):
                for it in o.get("items") or []:
                    satis[it.get("product") or it.get("name")] = satis.get(it.get("product") or it.get("name"), 0) \
                        + int(it.get("qty") or 1)
            rows = []
            for p in await db.yp_products.find({}, {"_id": 0}).to_list(20000):
                st = int(p.get("stock") or 0)
                sat = satis.get(p["id"], 0)
                low = st <= int(p.get("low_at") or 5)
                if st <= 0:
                    durum = "Tükendi"
                else:
                    d2 = []
                    if low:
                        d2.append("Az stok")
                    if not sat:
                        d2.append("hareketsiz" if d2 else "Hareketsiz")
                    durum = " · ".join(d2) or "Normal"
                rows.append({"name": p.get("name", ""), "stock": st,
                             "deger": round(st * _n(p.get("cost")), 2), "satis": sat, "durum": durum})
            return sorted(rows, key=lambda r: (r["satis"], -r["deger"]))[:200]
        if rid == "musteri_ozet":
            ilk, ay = {}, {}
            tum = await db.bookings.find({}, {"_id": 0, "phone": 1, "date": 1, "stage": 1}).to_list(50000)
            tum += [{"phone": (o.get("customer") or {}).get("phone"), "date": str(o.get("at"))[:10], "stage": "tamamlandi"}
                    for o in await db.yp_orders.find({}, {"_id": 0, "customer": 1, "at": 1}).to_list(20000)]
            for x in sorted(tum, key=lambda r: r.get("date") or ""):
                if x.get("phone") and x.get("stage") not in ("iptal", "talep"):
                    ilk.setdefault(x["phone"], x.get("date") or "")
            for x in tum:
                d0 = x.get("date") or ""
                if not (a <= d0 <= b) or not x.get("phone"):
                    continue
                k = d0[:7]
                d = ay.setdefault(k, {"day": k, "yeni": set(), "tekrar": set()})
                (d["yeni"] if ilk.get(x["phone"]) == d0 else d["tekrar"]).add(x["phone"])
            rows = []
            for k in sorted(ay):
                y, t2 = len(ay[k]["yeni"]), len(ay[k]["tekrar"] - ay[k]["yeni"])
                rows.append({"day": k, "yeni": y, "tekrar": t2, "oran": _pct(t2, y + t2)})
            return rows
        if rid in ("doluluk", "personel", "gelmeyen"):
            bk = await db.bookings.find({"date": {"$gte": a, "$lte": b}}, {"_id": 0}).to_list(50000)
            bk = [x for x in bk if x.get("status") != "iptal" and x.get("stage") != "talep"]
            if rid == "doluluk":
                g = {}
                for x in bk:
                    s0 = str(x.get("time") or "")[:2]
                    if not s0.isdigit():
                        continue
                    d = g.setdefault(s0, {"slot": "%s:00" % s0, "n": 0})
                    d["n"] += 1
                top = sum(d["n"] for d in g.values()) or 1
                rows = sorted(g.values(), key=lambda r: r["slot"])
                for r in rows:
                    r["oran"] = _pct(r["n"], top)
                return rows
            if rid == "personel":
                st = {s["id"]: s.get("name", "") for s in await db.yp_staff.find({}, {"_id": 0}).to_list(200)}
                g = {}
                for x in bk:
                    k = x.get("staff_id") or ""
                    d = g.setdefault(k, {"name": st.get(k, "Atanmamış"), "n": 0, "ciro": 0.0, "gelmedi": 0})
                    d["n"] += 1
                    if x.get("stage") == "gelmedi":
                        d["gelmedi"] += 1
                    else:
                        d["ciro"] = round(d["ciro"] + _n(x.get("total") or x.get("price")), 2)
                rows = sorted(g.values(), key=lambda r: -r["ciro"])
                for r in rows:
                    r["ort"] = round(r["ciro"] / r["n"], 2) if r["n"] else 0.0
                return rows
            g = {}
            for x in bk:
                if x.get("stage") != "gelmedi":
                    continue
                k = x.get("phone") or x.get("name", "")
                d = g.setdefault(k, {"name": x.get("name", ""), "phone": x.get("phone", ""), "n": 0, "son": ""})
                d["n"] += 1
                d["son"] = max(d["son"], x.get("date") or "")
            return sorted(g.values(), key=lambda r: -r["n"])
        if rid in ("servis_sure", "parca"):
            isler = await db.yp_isler.find({"flow": {"$in": ["servis", "isemri"]},
                                            "at": {"$gte": a, "$lte": b + "T99"}}, {"_id": 0}).to_list(20000)
            if rid == "parca":
                g = {}
                for r in isler:
                    for p in r.get("parts") or []:
                        d = g.setdefault(p.get("name", ""), {"name": p.get("name", ""), "qty": 0, "tutar": 0.0})
                        d["qty"] += int(p.get("qty") or 1)
                        d["tutar"] = round(d["tutar"] + int(p.get("qty") or 1) * _n(p.get("price")), 2)
                return sorted(g.values(), key=lambda r: -r["qty"])[:50]
            import isakis as I
            rows = []
            for r in isler:
                bas = str(r.get("at") or "")[:10]
                son = str(r.get("at2") or r.get("at") or "")[:10]
                try:
                    gun = (datetime.strptime(son, "%Y-%m-%d") - datetime.strptime(bas, "%Y-%m-%d")).days
                except ValueError:
                    gun = 0
                _p, pt = I.parcalar(r.get("parts"))
                rows.append({"name": r.get("no", ""), "musteri": (r.get("customer") or {}).get("name", ""),
                             "gun": gun, "tutar": round(pt + _n(r.get("labor")), 2),
                             "durum": I.ADIM.get(r.get("step"), r.get("step", ""))})
            return sorted(rows, key=lambda r: -r["gun"])
        if rid in ("dosya_durum", "durusma"):
            import isakis as I
            ds = await db.yp_isler.find({"flow": "dosya"}, {"_id": 0}).to_list(20000)
            if rid == "dosya_durum":
                g = {}
                for r in ds:
                    k = I.ADIM.get(r.get("step"), r.get("step", ""))
                    d = g.setdefault(k, {"durum": k, "n": 0, "vekalet": 0.0})
                    d["n"] += 1
                    d["vekalet"] = round(d["vekalet"] + _n((r.get("data") or {}).get("vekalet")), 2)
                return sorted(g.values(), key=lambda r: -r["n"])
            bugun = _now().date().isoformat()
            rows = []
            for r in ds:
                d0 = _d((r.get("data") or {}).get("durusma"))
                if not d0 or d0 < bugun:
                    continue
                kalan = (datetime.strptime(d0, "%Y-%m-%d").date() - _now().date()).days
                rows.append({"durusma": d0, "no": (r.get("data") or {}).get("dosya_no", r.get("no", "")),
                             "mahkeme": (r.get("data") or {}).get("mahkeme", ""),
                             "musteri": (r.get("customer") or {}).get("name", ""), "kalan": kalan})
            return sorted(rows, key=lambda r: r["durusma"])
        if rid == "kasa_ozet":
            g = {}
            for x in await db.yp_cash.find({"at": {"$gte": a, "$lte": b + "T99"}}, {"_id": 0}).to_list(50000):
                k = str(x.get("at"))[:10]
                d = g.setdefault(k, {"day": k, "gelir": 0.0, "gider": 0.0})
                t = _n(x.get("amount") or x.get("total"))
                if x.get("kind") == "gider" or t < 0:
                    d["gider"] = round(d["gider"] + abs(t), 2)
                else:
                    d["gelir"] = round(d["gelir"] + t, 2)
            rows = sorted(g.values(), key=lambda r: r["day"])
            for r in rows:
                r["net"] = round(r["gelir"] - r["gider"], 2)
            return rows
        return []

    @api_router.get("/yp/rapor/{rid}")
    async def tek(rid: str, frm: str = "", to: str = "", _: dict = Depends(adm)):
        r = BY_ID.get(str(rid)[:30])
        if not r:
            raise HTTPException(404, "Rapor bulunamadı")
        if r not in await hangi():
            raise HTTPException(403, "Bu rapor paketinizde yok")
        b = _d(to, _now().date().isoformat())
        a = _d(frm, (_now() - timedelta(days=29)).date().isoformat())
        if a > b:
            raise HTTPException(422, "Başlangıç tarihi bitişten sonra olamaz")
        rows = await hesap(r["id"], a, b)
        toplam = {c["key"]: round(sum(_n(x.get(c["key"])) for x in rows), 2)
                  for c in r["cols"] if c["sum"]}
        ch = None
        if r["chart"] and rows:
            xk = r["cols"][0]["key"]
            yk = [c["key"] for c in r["cols"] if c["type"] in ("para", "num")][:2]
            ch = {"type": r["chart"], "x": [str(x.get(xk, "")) for x in rows[:40]],
                  "series": [{"name": [c["label"] for c in r["cols"] if c["key"] == k][0],
                              "data": [_n(x.get(k)) for x in rows[:40]]} for k in yk]}
        return {"report": r, "from": a, "to": b, "rows": rows, "sum": toplam, "chart": ch, "n": len(rows)}

    @api_router.post("/yp/rapor/{rid}/csv")
    async def csv(rid: str, payload: dict, _: dict = Depends(adm)):
        r = BY_ID.get(str(rid)[:30])
        if not r:
            raise HTTPException(404, "Rapor bulunamadı")
        b = _d(payload.get("to"), _now().date().isoformat())
        a = _d(payload.get("frm"), (_now() - timedelta(days=29)).date().isoformat())
        rows = await hesap(r["id"], a, b)
        def cell(v):
            return '"%s"' % str(v if v is not None else "").replace('"', '""')
        out = [";".join(c["label"] for c in r["cols"])]
        for x in rows:
            out.append(";".join(cell(x.get(c["key"])) for c in r["cols"]))
        return {"ok": True, "n": len(rows), "name": "%s-%s-%s.csv" % (r["id"], a, b),
                "csv": "﻿" + "\n".join(out)}

    return api_router
