"""Stok ve satış eklentileri: çoklu depo, lot / son kullanma tarihi, stok sayımı, toplu fiyat güncelleme,
barkodlu hızlı satış, e-ihracat (proforma), API anahtarlı açık REST API ve şikayet / öneri formu."""
import hashlib
import re
import secrets
import time
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import Depends, HTTPException, Header, Request
from fastapi.responses import HTMLResponse

import pazaryeri
import tenant

_RL = {}


def _id():
    return uuid.uuid4().hex


def _now():
    return datetime.now(timezone.utc).isoformat()


def _f(v, d=0.0):
    try:
        if isinstance(v, str):
            v = v.strip().replace(" ", "")
            if "," in v:
                v = v.replace(".", "").replace(",", ".")
        return float(v)
    except Exception:       # noqa: BLE001
        return d


def _i(v):
    return int(_f(v))


def _limit(key, n, sec):
    now = time.time()
    q = [t for t in _RL.get(key, []) if now - t < sec]
    if len(q) >= n:
        _RL[key] = q
        raise HTTPException(429, "Çok fazla istek; biraz sonra tekrar deneyin")
    q.append(now)
    _RL[key] = q


def _esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def yuvarla(x, mod):
    """mod: '' | '1' (tam TL) | '5' (5'e) | '90' (…,90) | '99' (…,99)"""
    if mod == "1":
        return float(round(x))
    if mod == "5":
        return float(round(x / 5.0) * 5)
    if mod in ("90", "99"):
        t = int(x)
        return float(t + int(mod) / 100.0) if x - t > 0 else float(max(t - 1, 0) + int(mod) / 100.0)
    return round(x, 2)


def yeni_fiyat(eski, mod, deger, yr=""):
    if mod == "yuzde":
        f = eski * (1 + deger / 100.0)
    elif mod == "sabit":
        f = eski + deger
    elif mod == "yeni":
        f = deger
    else:
        raise HTTPException(422, "Geçersiz yöntem")
    return max(0.0, yuvarla(f, yr))


async def _urun_bul(db, kod):
    kod = str(kod or "").strip()
    if not kod:
        return None
    p = await db.yp_products.find_one({"$or": [{"barcode": kod}, {"sku": kod}, {"id": kod}]}, {"_id": 0})
    if not p:
        sp = await db.shop_products.find_one({"$or": [{"barcode": kod}, {"sku": kod}]}, {"_id": 0, "id": 1})
        if sp:
            p = await db.yp_products.find_one({"id": sp["id"]}, {"_id": 0})
    return p


def _net(p):
    pr, sl = _f(p.get("price")), _f(p.get("sale_price"))
    return sl if 0 < sl < pr else pr


async def _stok_log(db, pid, delta, before, after, source, ref):
    await db.yp_stock_log.insert_one({"id": uuid.uuid4().hex[:12], "key": "%s|%s|%s" % (source, ref, pid), "product": pid, "delta": delta,
                                      "before": before, "after": after, "source": source, "ref": ref, "variant": "", "at": _now(), "seq": time.time()})
    await pazaryeri._ayna(db, pid)


def register(api_router, db, deps):
    adm = Depends(deps["require_admin"])

    # ------------------------------------------------------------ depolar
    @api_router.get("/yp/depo")
    async def depo_list(_: dict = adm):
        rows = await db.stok_depo.find({}, {"_id": 0}).sort("created_at", 1).to_list(100)
        for r in rows:
            lots = await db.stok_lot.find({"depo_id": r["id"], "qty": {"$gt": 0}}, {"_id": 0, "qty": 1}).to_list(50000)
            r["lot_sayisi"], r["toplam_adet"] = len(lots), sum(x["qty"] for x in lots)
        return {"rows": rows}

    @api_router.post("/yp/depo")
    async def depo_add(payload: dict, _: dict = adm):
        ad = str(payload.get("name") or "").strip()[:60]
        if not ad:
            raise HTTPException(422, "Depo adı gerekli")
        if await db.stok_depo.find_one({"name": ad}, {"_id": 1}):
            raise HTTPException(409, "Bu adla depo var")
        d = {"id": _id(), "name": ad, "address": str(payload.get("address") or "")[:200], "created_at": _now()}
        await db.stok_depo.insert_one(dict(d))
        return d

    @api_router.delete("/yp/depo/{did}")
    async def depo_del(did: str, _: dict = adm):
        if await db.stok_lot.find_one({"depo_id": did, "qty": {"$gt": 0}}, {"_id": 1}):
            raise HTTPException(409, "İçinde stok olan depo silinemez; önce transfer edin")
        await db.stok_depo.delete_one({"id": did})
        return {"ok": True}

    # ------------------------------------------------------------ lot / SKT
    @api_router.post("/yp/stok/lot")
    async def lot_giris(payload: dict, user: dict = adm):
        p = await _urun_bul(db, payload.get("product") or payload.get("barcode"))
        if not p:
            raise HTTPException(404, "Ürün bulunamadı")
        qty = _i(payload.get("qty"))
        if qty <= 0:
            raise HTTPException(422, "Adet 1 veya daha fazla olmalı")
        depo = str(payload.get("depo_id") or "")
        if depo and not await db.stok_depo.find_one({"id": depo}, {"_id": 1}):
            raise HTTPException(404, "Depo bulunamadı")
        skt = str(payload.get("skt") or "")[:10]
        if skt and not re.match(r"^\d{4}-\d{2}-\d{2}$", skt):
            raise HTTPException(422, "Son kullanma tarihi YYYY-AA-GG biçiminde olmalı")
        lot = {"id": _id(), "product": p["id"], "product_name": p.get("name", ""), "lot": str(payload.get("lot") or "").strip()[:40] or time.strftime("L%y%m%d"),
               "skt": skt, "qty": qty, "ilk_qty": qty, "depo_id": depo, "created_at": _now()}
        await db.stok_lot.insert_one(dict(lot))
        before = _i(p.get("stock"))
        await db.yp_products.update_one({"id": p["id"]}, {"$inc": {"stock": qty}})
        await _stok_log(db, p["id"], qty, before, before + qty, "lot_giris", lot["id"])
        lot.pop("_id", None)
        return lot

    @api_router.get("/yp/stok/lot")
    async def lot_list(urun: str = "", depo: str = "", _: dict = adm):
        q = {"qty": {"$gt": 0}}
        if urun:
            q["product"] = urun
        if depo:
            q["depo_id"] = depo
        rows = await db.stok_lot.find(q, {"_id": 0}).sort([("skt", 1)]).to_list(5000)
        return {"rows": rows}

    @api_router.get("/yp/stok/skt")
    async def skt_rapor(gun: int = 60, _: dict = adm):
        bugun = datetime.now(timezone.utc).date()
        sinir = (bugun + timedelta(days=max(1, min(730, gun)))).isoformat()
        rows = await db.stok_lot.find({"qty": {"$gt": 0}, "skt": {"$ne": "", "$lte": sinir}}, {"_id": 0}).sort("skt", 1).to_list(5000)
        for r in rows:
            r["kalan_gun"] = (datetime.fromisoformat(r["skt"]).date() - bugun).days
            r["durum"] = "gecmis" if r["kalan_gun"] < 0 else ("kritik" if r["kalan_gun"] <= 15 else "yaklasiyor")
        return {"rows": rows, "gecmis": sum(1 for r in rows if r["durum"] == "gecmis")}

    @api_router.post("/yp/stok/lot/{lid}/dusur")
    async def lot_dusur(lid: str, payload: dict, _: dict = adm):
        """Fire / imha / bozulma: lottan düşer, ürün stoğunu da azaltır."""
        lot = await db.stok_lot.find_one({"id": lid}, {"_id": 0})
        if not lot:
            raise HTTPException(404, "Lot bulunamadı")
        n = min(_i(payload.get("qty")) or lot["qty"], lot["qty"])
        if n <= 0:
            raise HTTPException(422, "Adet geçersiz")
        await db.stok_lot.update_one({"id": lid}, {"$inc": {"qty": -n}})
        p = await db.yp_products.find_one({"id": lot["product"]}, {"_id": 0}) or {}
        before = _i(p.get("stock"))
        after = max(0, before - n)
        await db.yp_products.update_one({"id": lot["product"]}, {"$set": {"stock": after}})
        await _stok_log(db, lot["product"], -n, before, after, "lot_fire", lid + str(time.time()))
        return {"ok": True, "dusen": n}

    @api_router.post("/yp/stok/transfer")
    async def transfer(payload: dict, _: dict = adm):
        lot = await db.stok_lot.find_one({"id": payload.get("lot_id")}, {"_id": 0})
        hedef = str(payload.get("to_depo") or "")
        if not lot or not await db.stok_depo.find_one({"id": hedef}, {"_id": 1}):
            raise HTTPException(404, "Lot ya da hedef depo bulunamadı")
        n = _i(payload.get("qty"))
        if n <= 0 or n > lot["qty"]:
            raise HTTPException(422, "Adet 1 ile %d arasında olmalı" % lot["qty"])
        if lot.get("depo_id") == hedef:
            raise HTTPException(422, "Aynı depo")
        await db.stok_lot.update_one({"id": lot["id"]}, {"$inc": {"qty": -n}})
        yeni = {**lot, "id": _id(), "qty": n, "ilk_qty": n, "depo_id": hedef, "created_at": _now(), "transfer_from": lot["id"]}
        await db.stok_lot.insert_one(dict(yeni))
        return {"ok": True, "yeni_lot": yeni["id"]}

    # ------------------------------------------------------------ sayım
    @api_router.post("/yp/stok/sayim")
    async def sayim(payload: dict, user: dict = adm):
        satirlar, farklar = payload.get("items") or [], []
        if not isinstance(satirlar, list) or not satirlar:
            raise HTTPException(422, "Sayılan ürün listesi boş")
        for it in satirlar[:2000]:
            p = await _urun_bul(db, it.get("product") or it.get("barcode"))
            if not p:
                farklar.append({"kod": str(it.get("product") or it.get("barcode") or ""), "hata": "Ürün bulunamadı"})
                continue
            sayilan, sistem = _i(it.get("sayilan")), _i(p.get("stock"))
            if sayilan < 0:
                farklar.append({"kod": p["id"], "ad": p.get("name", ""), "hata": "Negatif sayım"})
                continue
            farklar.append({"product": p["id"], "ad": p.get("name", ""), "sistem": sistem, "sayilan": sayilan, "fark": sayilan - sistem})
        uygula = bool(payload.get("uygula"))
        uygulanan = 0
        if uygula:
            ref = _id()
            for f in farklar:
                if f.get("fark"):
                    await db.yp_products.update_one({"id": f["product"]}, {"$set": {"stock": f["sayilan"]}})
                    await _stok_log(db, f["product"], f["fark"], f["sistem"], f["sayilan"], "sayim", ref)
                    uygulanan += 1
            await db.stok_sayim.insert_one({"id": ref, "at": _now(), "by": user.get("id"), "satir": len(farklar), "duzeltilen": uygulanan,
                                            "farklar": [f for f in farklar if f.get("fark")][:500]})
        return {"farklar": farklar, "uygulandi": uygula, "duzeltilen": uygulanan,
                "eksik_toplam": sum(-f["fark"] for f in farklar if f.get("fark", 0) < 0), "fazla_toplam": sum(f["fark"] for f in farklar if f.get("fark", 0) > 0)}

    @api_router.get("/yp/stok/sayim")
    async def sayim_gecmis(_: dict = adm):
        return {"rows": await db.stok_sayim.find({}, {"_id": 0}).sort("at", -1).to_list(30)}

    # ------------------------------------------------------------ toplu fiyat
    @api_router.post("/yp/stok/toplu-fiyat")
    async def toplu_fiyat(payload: dict, user: dict = adm):
        mod, deger, yr = str(payload.get("mod") or ""), _f(payload.get("deger")), str(payload.get("yuvarla") or "")
        if mod == "yuzde" and not -90 <= deger <= 1000:
            raise HTTPException(422, "Yüzde -90 ile 1000 arasında olmalı")
        q = {}
        if payload.get("category"):
            q["cat"] = str(payload["category"])
        if payload.get("brand"):
            q["brand"] = str(payload["brand"])
        prods = await db.yp_products.find(q, {"_id": 0, "id": 1, "name": 1, "price": 1, "sale_price": 1}).to_list(20000)
        if not prods:
            raise HTTPException(404, "Bu süzgece uyan ürün yok")
        liste = []
        for p in prods:
            eski = _f(p.get("price"))
            if mod != "yeni" and eski <= 0:
                continue
            yeni = yeni_fiyat(eski, mod, deger, yr)
            if abs(yeni - eski) >= 0.005:
                liste.append({"id": p["id"], "ad": p.get("name", ""), "eski": eski, "yeni": yeni})
        if payload.get("onizle", True):
            return {"onizleme": True, "adet": len(liste), "ornek": liste[:15]}
        ref = _id()
        for x in liste:
            await db.yp_products.update_one({"id": x["id"]}, {"$set": {"price": x["yeni"]}})
            await pazaryeri._ayna(db, x["id"])
        await db.fiyat_gecmis.insert_one({"id": ref, "at": _now(), "by": user.get("id"), "mod": mod, "deger": deger, "adet": len(liste), "degisim": liste[:2000]})
        return {"onizleme": False, "adet": len(liste), "geri_al_kodu": ref}

    @api_router.post("/yp/stok/toplu-fiyat/{ref}/geri-al")
    async def toplu_geri(ref: str, _: dict = adm):
        g = await db.fiyat_gecmis.find_one({"id": ref, "geri_alindi": {"$ne": True}}, {"_id": 0})
        if not g:
            raise HTTPException(404, "Kayıt yok ya da zaten geri alındı")
        for x in g["degisim"]:
            await db.yp_products.update_one({"id": x["id"]}, {"$set": {"price": x["eski"]}})
            await pazaryeri._ayna(db, x["id"])
        await db.fiyat_gecmis.update_one({"id": ref}, {"$set": {"geri_alindi": True}})
        return {"ok": True, "adet": len(g["degisim"])}

    # ------------------------------------------------------------ hızlı satış
    @api_router.get("/yp/hizli/bul")
    async def hizli_bul(kod: str, _: dict = adm):
        p = await _urun_bul(db, kod)
        if not p:
            rx = {"$regex": re.escape(kod), "$options": "i"}
            ps = await db.yp_products.find({"name": rx, "status": {"$ne": "draft"}}, {"_id": 0, "id": 1, "name": 1, "stock": 1, "price": 1, "sale_price": 1, "barcode": 1}).to_list(8)
            return {"bulundu": False, "oneriler": [{"id": x["id"], "name": x["name"], "stock": x.get("stock", 0), "fiyat": _net(x), "barcode": x.get("barcode", "")} for x in ps]}
        return {"bulundu": True, "urun": {"id": p["id"], "name": p.get("name", ""), "stock": _i(p.get("stock")), "fiyat": _net(p), "barcode": p.get("barcode", ""),
                                          "kdv": _f(p.get("vat"), 20)}}

    @api_router.post("/yp/hizli/sat")
    async def hizli_sat(payload: dict, user: dict = adm):
        items = payload.get("items") or []
        if not items:
            raise HTTPException(422, "Sepet boş")
        odeme = str(payload.get("odeme") or "nakit")
        if odeme not in ("nakit", "kart", "havale"):
            raise HTTPException(422, "Ödeme türü geçersiz")
        acc = payload.get("account_id")
        if not acc or not await db.accounts.find_one({"id": acc}, {"_id": 1}):
            raise HTTPException(422, "Kasa/banka hesabı seçin")
        fis = "HS-%s-%04d" % (datetime.now(timezone.utc).strftime("%y%m%d"), await db.hizli_satis.count_documents({}) % 10000 + 1)
        alinan, satir, toplam = [], [], 0.0
        for it in items[:100]:
            p = await _urun_bul(db, it.get("product") or it.get("barcode"))
            n = _i(it.get("qty") or 1)
            if not p or n <= 0:
                raise HTTPException(404, "Ürün bulunamadı: %s" % (it.get("product") or it.get("barcode")))
            r = await pazaryeri.take_stock(db, p["id"], n, "hizli", fis)
            if not r.get("ok"):
                for t in alinan:
                    await pazaryeri.give_stock(db, t["id"], t["qty"], "geri_al", fis + "-geri-" + t["id"])
                raise HTTPException(409, "%s: %s" % (p.get("name", ""), r.get("err") or "Stok düşülemedi"))
            alinan.append({"id": p["id"], "qty": n})
            fyt = _f(it.get("fiyat")) if it.get("fiyat") not in (None, "") else _net(p)
            tut = round(fyt * n, 2)
            toplam += tut
            satir.append({"product": p["id"], "ad": p.get("name", ""), "qty": n, "fiyat": fyt, "tutar": tut})
        indirim = max(0.0, min(_f(payload.get("indirim")), toplam))
        net = round(toplam - indirim, 2)
        await db.cash_transactions.insert_one({"id": _id(), "type": "gelir", "amount": net, "account_id": acc, "description": "Hızlı satış " + fis,
                                               "date": datetime.now(timezone.utc).date().isoformat(), "category": "Perakende satış", "created_by": user.get("id"), "hizli_fis": fis})
        doc = {"id": _id(), "fis": fis, "at": _now(), "items": satir, "ara_toplam": round(toplam, 2), "indirim": indirim, "toplam": net, "odeme": odeme,
               "account_id": acc, "by": user.get("id"), "musteri": str(payload.get("musteri") or "")[:80]}
        await db.hizli_satis.insert_one(dict(doc))
        doc.pop("_id", None)
        return doc

    @api_router.get("/yp/hizli/gecmis")
    async def hizli_gecmis(_: dict = adm):
        rows = await db.hizli_satis.find({}, {"_id": 0}).sort("at", -1).to_list(50)
        bugun = datetime.now(timezone.utc).date().isoformat()
        return {"rows": rows, "bugun_toplam": round(sum(r["toplam"] for r in rows if r["at"][:10] == bugun), 2)}

    # ------------------------------------------------------------ e-ihracat
    @api_router.get("/yp/ihracat")
    async def ihr_get(_: dict = adm):
        a = await db.yp_ayar.find_one({"id": "ihracat"}, {"_id": 0}) or {}
        return {"aktif": bool(a.get("aktif")), "ulkeler": a.get("ulkeler", []), "para": a.get("para", "USD"), "incoterm": a.get("incoterm", "EXW"),
                "min_siparis": a.get("min_siparis", 0), "not": a.get("not", ""), "firma": a.get("firma", {})}

    @api_router.put("/yp/ihracat")
    async def ihr_put(payload: dict, _: dict = adm):
        upd = {"aktif": bool(payload.get("aktif")), "para": str(payload.get("para") or "USD").upper()[:3],
               "incoterm": str(payload.get("incoterm") or "EXW").upper()[:3], "min_siparis": max(0, _f(payload.get("min_siparis"))),
               "ulkeler": [str(x).strip()[:40] for x in (payload.get("ulkeler") or []) if str(x).strip()][:60], "not": str(payload.get("not") or "")[:500],
               "firma": {k: str((payload.get("firma") or {}).get(k) or "")[:160] for k in ("unvan", "adres", "vergi_no", "iban", "swift")}}
        await db.yp_ayar.update_one({"id": "ihracat"}, {"$set": upd}, upsert=True)
        return {"ok": True}

    @api_router.put("/yp/ihracat/urun/{pid}")
    async def ihr_urun(pid: str, payload: dict, _: dict = adm):
        gtip = re.sub(r"[^0-9.]", "", str(payload.get("gtip") or ""))[:14]
        await db.yp_products.update_one({"id": pid}, {"$set": {"ihracat": {"gtip": gtip, "mensei": str(payload.get("mensei") or "Türkiye")[:40],
                                                                            "agirlik_kg": max(0, _f(payload.get("agirlik_kg")))}}})
        return {"ok": True}

    @api_router.post("/yp/ihracat/proforma", response_class=HTMLResponse)
    async def proforma(payload: dict, _: dict = adm):
        a = await ihr_get(_)
        para = str(payload.get("para") or a["para"]).upper()
        kur = 1.0
        if para != "TRY":
            c = await db.yp_ayar.find_one({"id": "kur"}, {"_id": 0}) or {}
            k = (c.get("kurlar") or {}).get(para)
            kur = _f(payload.get("kur")) or (k or {}).get("satis") or 0
            if kur <= 0:
                raise HTTPException(422, "Kur bulunamadı: önce Kur sayfasından güncelleyin ya da kuru yazın")
        satir, top, kg = [], 0.0, 0.0
        for it in payload.get("items") or []:
            p = await _urun_bul(db, it.get("product") or it.get("barcode"))
            n = _i(it.get("qty") or 1)
            if not p or n <= 0:
                raise HTTPException(404, "Ürün bulunamadı")
            ih = p.get("ihracat") or {}
            birim = round(_net(p) / kur, 2) if para != "TRY" else _net(p)
            top += birim * n
            kg += _f(ih.get("agirlik_kg")) * n
            satir.append("<tr><td>%s</td><td>%s</td><td>%s</td><td style='text-align:right'>%d</td><td style='text-align:right'>%.2f</td><td style='text-align:right'>%.2f</td></tr>" % (
                _esc(p.get("name")), _esc(ih.get("gtip") or "—"), _esc(ih.get("mensei") or "Türkiye"), n, birim, birim * n))
        if not satir:
            raise HTTPException(422, "Kalem yok")
        f = a["firma"]
        return HTMLResponse(
            "<!doctype html><meta charset=utf-8><title>Proforma fatura</title><body style='font:14px system-ui;max-width:860px;margin:24px auto;padding:0 14px'>"
            "<h2>PROFORMA FATURA</h2><p><b>%s</b><br>%s<br>Vergi no: %s</p><p>Alıcı: <b>%s</b> — %s<br>Teslim şekli: %s · Para birimi: %s · Tarih: %s</p>"
            "<table border=1 cellpadding=6 style='border-collapse:collapse;width:100%%'><tr><th>Ürün</th><th>GTİP</th><th>Menşei</th><th>Adet</th><th>Birim</th><th>Tutar</th></tr>%s"
            "<tr><td colspan=5 style='text-align:right'><b>Toplam</b></td><td style='text-align:right'><b>%.2f %s</b></td></tr></table>"
            "<p>Brüt ağırlık (kayıtlı): %.2f kg</p><p>Banka: IBAN %s · SWIFT %s</p><p style='color:#667;font-size:12px'>%s Bu belge proformadır; resmî ihracat faturası yerine geçmez.</p>" % (
                _esc(f.get("unvan")), _esc(f.get("adres")), _esc(f.get("vergi_no")), _esc(payload.get("alici")), _esc(payload.get("ulke")),
                a["incoterm"], para, datetime.now(timezone.utc).strftime("%d.%m.%Y"), "".join(satir), top, para, kg, _esc(f.get("iban")), _esc(f.get("swift")), _esc(a["not"])))

    # ------------------------------------------------------------ API anahtarları ve açık API
    @api_router.get("/yp/api-anahtar")
    async def key_list(_: dict = adm):
        return {"rows": await db.api_anahtar.find({"iptal": False}, {"_id": 0, "hash": 0}).sort("created_at", -1).to_list(50),
                "taban": "/api/public/" + tenant.public_token("v1"), "form": "/api/public/" + tenant.public_token("geri-bildirim")}

    @api_router.post("/yp/api-anahtar")
    async def key_new(payload: dict, _: dict = adm):
        ham = "ok_" + secrets.token_urlsafe(30)
        yaz = bool(payload.get("yazma"))
        d = {"id": _id(), "ad": str(payload.get("ad") or "Anahtar").strip()[:60], "hash": hashlib.sha256(ham.encode()).hexdigest(), "onek": ham[:7],
             "yazma": yaz, "created_at": _now(), "son_kullanim": "", "iptal": False}
        await db.api_anahtar.insert_one(dict(d))
        return {"id": d["id"], "ad": d["ad"], "anahtar": ham, "yazma": yaz, "not": "Anahtar yalnızca şimdi gösterilir."}

    @api_router.delete("/yp/api-anahtar/{kid}")
    async def key_del(kid: str, _: dict = adm):
        await db.api_anahtar.update_one({"id": kid}, {"$set": {"iptal": True}})
        return {"ok": True}

    async def key_auth(request: Request, x_api_key: str = Header(default=""), yazma=False):
        h = hashlib.sha256((x_api_key or "").encode()).hexdigest()
        _limit("k:" + h, 120, 60)
        k = await db.api_anahtar.find_one({"hash": h, "iptal": False}, {"_id": 0})
        if not k:
            raise HTTPException(401, "API anahtarı geçersiz (X-API-Key başlığı)")
        if yazma and not k.get("yazma"):
            raise HTTPException(403, "Bu anahtar yalnızca okuma yetkili")
        await db.api_anahtar.update_one({"id": k["id"]}, {"$set": {"son_kullanim": _now()}})
        return k

    def _pub(p):
        return {"id": p["id"], "ad": p.get("name", ""), "sku": p.get("sku", ""), "barkod": p.get("barcode", ""), "marka": p.get("brand", ""),
                "kategori": p.get("cat", ""), "fiyat": _net(p), "liste_fiyati": _f(p.get("price")), "stok": _i(p.get("stock")), "aktif": p.get("status") != "draft"}

    @api_router.get("/public/v1/urunler")
    async def v1_urunler(request: Request, sayfa: int = 1, adet: int = 100, q: str = "", x_api_key: str = Header(default="")):
        await key_auth(request, x_api_key)
        adet = max(1, min(500, adet))
        flt = {}
        if q:
            rx = {"$regex": re.escape(q), "$options": "i"}
            flt["$or"] = [{"name": rx}, {"sku": rx}, {"barcode": rx}]
        toplam = await db.yp_products.count_documents(flt)
        rows = await db.yp_products.find(flt, {"_id": 0}).sort("name", 1).skip((max(1, sayfa) - 1) * adet).limit(adet).to_list(adet)
        return {"toplam": toplam, "sayfa": sayfa, "urunler": [_pub(p) for p in rows]}

    @api_router.get("/public/v1/urunler/{kod}")
    async def v1_urun(kod: str, request: Request, x_api_key: str = Header(default="")):
        await key_auth(request, x_api_key)
        p = await _urun_bul(db, kod)
        if not p:
            raise HTTPException(404, "Ürün bulunamadı")
        return _pub(p)

    @api_router.put("/public/v1/urunler/{kod}")
    async def v1_guncelle(kod: str, payload: dict, request: Request, x_api_key: str = Header(default="")):
        await key_auth(request, x_api_key, yazma=True)
        p = await _urun_bul(db, kod)
        if not p:
            raise HTTPException(404, "Ürün bulunamadı")
        upd = {}
        if "fiyat" in payload:
            f = _f(payload["fiyat"], -1)
            if f < 0:
                raise HTTPException(422, "Fiyat geçersiz")
            upd["price"] = round(f, 2)
        if "stok" in payload:
            s = _i(payload["stok"])
            if s < 0:
                raise HTTPException(422, "Stok negatif olamaz")
            upd["stock"] = s
        if not upd:
            raise HTTPException(422, "fiyat veya stok gönderin")
        await db.yp_products.update_one({"id": p["id"]}, {"$set": upd})
        if "stock" in upd:
            await _stok_log(db, p["id"], upd["stock"] - _i(p.get("stock")), _i(p.get("stock")), upd["stock"], "api", _id())
        else:
            await pazaryeri._ayna(db, p["id"])
        return _pub(await db.yp_products.find_one({"id": p["id"]}, {"_id": 0}))

    # ------------------------------------------------------------ şikayet / öneri formu
    @api_router.post("/public/geri-bildirim")
    async def gb_gonder(payload: dict, request: Request):
        if payload.get("website"):
            return {"ok": True}
        ip = (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "")).split(",")[0].strip()
        _limit("gb:" + ip, 5, 3600)
        msg = str(payload.get("mesaj") or "").strip()
        if len(msg) < 10:
            raise HTTPException(422, "Mesaj en az 10 karakter olmalı")
        tur = str(payload.get("tur") or "oneri")
        tur = tur if tur in ("sikayet", "oneri", "tesekkur") else "oneri"
        d = {"id": _id(), "tur": tur, "ad": str(payload.get("ad") or "").strip()[:80], "iletisim": str(payload.get("iletisim") or "").strip()[:120],
             "mesaj": msg[:2000], "durum": "yeni", "created_at": _now(), "cevap": ""}
        await db.geri_bildirim.insert_one(dict(d))
        return {"ok": True, "takip_no": d["id"][:8].upper()}

    @api_router.get("/yp/geri-bildirim")
    async def gb_list(durum: str = "", _: dict = adm):
        q = {"durum": durum} if durum else {}
        rows = await db.geri_bildirim.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
        return {"rows": rows, "yeni": await db.geri_bildirim.count_documents({"durum": "yeni"})}

    @api_router.post("/yp/geri-bildirim/{gid}")
    async def gb_durum(gid: str, payload: dict, _: dict = adm):
        durum = str(payload.get("durum") or "")
        if durum not in ("yeni", "inceleniyor", "cozuldu"):
            raise HTTPException(422, "Durum geçersiz")
        await db.geri_bildirim.update_one({"id": gid}, {"$set": {"durum": durum, "cevap": str(payload.get("cevap") or "")[:1000]}})
        return {"ok": True}
