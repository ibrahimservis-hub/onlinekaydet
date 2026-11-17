"""Yemek menüsü: Trendyol Yemek'te fiyat ve satış durumunu panelden gönderir; tüm platformlar için menü dosyası verir.

Trendyol Go (developers.tgoapps.com) menü servisleri yalnızca okuma, ürün/bölüm durumu ve fiyat güncellemedir;
yeni ürün oluşturma yoktur — ürün ilk kez Trendyol Yemek satıcı panelinde açılır, burada eşleştirilir.
Yemeksepeti, Getir ve Migros için herkese açık menü servisi belgesi yoktur; menü dosyası (CSV) verilir.
"""
import csv
import io
import re

from fastapi import Depends, HTTPException
from fastapi.responses import Response

import shop_sync
import urun
from markets_hub import FOOD, headers


def _ad(s):
    s = str(s or "").lower()
    for a, b in (("ı", "i"), ("ğ", "g"), ("ü", "u"), ("ş", "s"), ("ö", "o"), ("ç", "c"), ("i̇", "i")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "", s)


def _base(c, kind="product"):
    host = "stageapi.tgoapis.com" if str(c.get("env") or "").lower() in ("stage", "test") else "api.tgoapis.com"
    return f"https://{host}/integrator/{kind}/meal/suppliers/{c.get('seller_id')}"


async def tgo_stores(c, h):
    if c.get("store_id"):
        return [{"id": str(c["store_id"]), "name": "Restoran"}]
    code, d = await shop_sync.http("GET", _base(c, "store") + "/stores?page=0&size=50", h)
    if code >= 300:
        raise HTTPException(502, "Trendyol Yemek restoran listesi alınamadı (%s): %s" % (code, str(d)[:140]))
    return [{"id": str(r.get("id")), "name": r.get("name") or "Restoran"} for r in (d.get("restaurants") or []) if r.get("id")]


async def tgo_menu(c, h):
    """[{id, ad, fiyat, durum, magaza, magaza_ad}]"""
    out = []
    for st in await tgo_stores(c, h):
        code, d = await shop_sync.http("GET", _base(c) + f"/stores/{st['id']}/products", h)
        if code >= 300:
            raise HTTPException(502, "Trendyol Yemek menüsü alınamadı (%s): %s" % (code, str(d)[:140]))
        for p in d.get("products") or []:
            out.append({"id": str(p.get("id")), "ad": p.get("name") or "", "fiyat": float(p.get("sellingPrice") or 0),
                        "durum": p.get("status") or "", "magaza": st["id"], "magaza_ad": st["name"]})
    return out


def _fiyat(p, mk):
    return urun.kanal_fiyat(p, mk)[1]


def eslestir(prods, remote, mk):
    """Yerel ürün ↔ platform ürünü: önce kayıtlı kimlik, sonra aynı ad."""
    byid = {r["id"]: r for r in remote}
    byad = {}
    for r in remote:
        byad.setdefault(_ad(r["ad"]), r)
    rows = []
    for p in prods:
        f = p.get("food") or {}
        r = byid.get((f.get("ext") or {}).get(mk)) or byad.get(_ad(p.get("name")))
        loc = _fiyat(p, mk)
        rows.append({"id": p["id"], "ad": p.get("name"), "fiyat": loc, "aktif": f.get("aktif") is not False and p.get("status") != "draft",
                     "uzak": r, "durum": "eslesmedi" if not r else ("fark" if abs(r["fiyat"] - loc) > 0.001 or
                                                                    (r["durum"] == "ACTIVE") != (f.get("aktif") is not False and p.get("status") != "draft") else "esit")})
    return rows


async def _prods(db, mk):
    rows = await db.yp_products.find({f"channels.{mk}": True}, {"_id": 0}).to_list(5000)
    return rows


def menu_csv(prods, mk):
    o = io.StringIO()
    w = csv.writer(o, delimiter=";")
    w.writerow(["Bölüm", "Ürün adı", "Açıklama", "Fiyat (₺)", "KDV %", "Görsel", "Hazırlık (dk)", "Porsiyon", "Kalori", "Alerjenler",
                "Vejetaryen", "Vegan", "Acı (0-3)", "Çıkarılabilir malzemeler", "Seçenek grupları", "Durum"])
    for p in prods:
        f = p.get("food") or {}
        gr = " | ".join("%s (min %d, max %d): %s" % (g["ad"], g["min"], g["max"], ", ".join("%s +%.2f" % (x["ad"], x["fiyat"]) if x["fiyat"] else x["ad"] for x in g["secenekler"]))
                        for g in f.get("gruplar") or [])
        w.writerow([f.get("bolum") or p.get("cat") or "", p.get("name"), (p.get("short") or p.get("desc") or "")[:300].replace("\n", " "),
                    "%.2f" % _fiyat(p, mk), p.get("vat", 10), (p.get("images") or [""])[0], f.get("hazirlik", ""), f.get("porsiyon", ""), f.get("kalori") or "",
                    ", ".join(f.get("alerjen") or []), "evet" if f.get("vejetaryen") else "", "evet" if f.get("vegan") else "", f.get("aci") or 0,
                    ", ".join(f.get("cikarilabilir") or []), gr, "Aktif" if f.get("aktif") is not False and p.get("status") != "draft" else "Pasif"])
    return "﻿" + o.getvalue()


def register(api_router, db, deps):
    adm = Depends(deps["require_admin"])

    async def yalniz_yemek():
        if not await urun.yemek_firma(db):
            raise HTTPException(404, "Bu sektörde yemek menüsü yok")

    @api_router.get("/yp/menu/{mk}")
    async def durum(mk: str, _: dict = adm):
        await yalniz_yemek()
        if mk not in FOOD:
            raise HTTPException(404, "Bilinmeyen platform")
        c = await shop_sync.market_cfg(db, mk)
        prods = await _prods(db, mk)
        base = {"mk": mk, "ad": FOOD[mk], "bagli": shop_sync.connected(mk, c), "api": mk == "trendyol_yemek", "adet": len(prods)}
        if mk != "trendyol_yemek":
            return dict(base, rows=eslestir(prods, [], mk), not_="Bu platformun menü servisi herkese açık değil; menü dosyasını indirip platformun panelinden yükleyin.")
        if not base["bagli"]:
            return dict(base, rows=eslestir(prods, [], mk), not_="Önce Bağlantı ekranından Trendyol Yemek bilgilerini girin.")
        h = await headers(mk, c)
        return dict(base, rows=eslestir(prods, await tgo_menu(c, h), mk))

    @api_router.post("/yp/menu/{mk}/gonder")
    async def gonder(mk: str, payload: dict, _: dict = adm):
        await yalniz_yemek()
        """Seçili ürünlerin fiyatını ve satış durumunu Trendyol Yemek'e gönderir (yalnızca değişenler)."""
        if mk != "trendyol_yemek":
            raise HTTPException(422, "Bu platform için gönderim yok; menü dosyasını kullanın")
        c = await shop_sync.market_cfg(db, mk)
        if not shop_sync.connected(mk, c):
            raise HTTPException(422, "Trendyol Yemek bağlantısı eksik")
        h = await headers(mk, c)
        ids = set(payload.get("ids") or [])
        prods = [p for p in await _prods(db, mk) if not ids or p["id"] in ids]
        rows = [r for r in eslestir(prods, await tgo_menu(c, h), mk) if r["uzak"]]
        fiyat, durumlar, atlanan = [], [], 0
        for r in rows:
            u = r["uzak"]
            if abs(u["fiyat"] - r["fiyat"]) > 0.001:
                fiyat.append({"productId": int(u["id"]) if u["id"].isdigit() else u["id"], "sellingPrice": r["fiyat"]})
            if (u["durum"] == "ACTIVE") != r["aktif"]:
                durumlar.append((u, "ACTIVE" if r["aktif"] else "PASSIVE"))
            if abs(u["fiyat"] - r["fiyat"]) <= 0.001 and (u["durum"] == "ACTIVE") == r["aktif"]:
                atlanan += 1
            await db.yp_products.update_one({"id": r["id"]}, {"$set": {f"food.ext.{mk}": u["id"]}})
        out = {"fiyat": 0, "durum": 0, "hata": [], "batch": None, "atlanan": atlanan}
        for i in range(0, len(fiyat), 1000):                      # tek istekte en çok 1000 ürün
            code, d = await shop_sync.http("POST", _base(c) + "/products/price", h, {"items": fiyat[i:i + 1000]})
            if code < 300:
                out["fiyat"] += len(fiyat[i:i + 1000])
                out["batch"] = d.get("batchRequestId")
            else:
                out["hata"].append("Fiyat (%s): %s" % (code, str(d)[:140]))
        for u, st in durumlar:
            code, d = await shop_sync.http("PUT", _base(c) + f"/stores/{u['magaza']}/products/{u['id']}/status", h, {"status": st})
            if code < 300:
                out["durum"] += 1
            else:
                out["hata"].append("%s durum (%s): %s" % (u["ad"], code, str(d)[:120]))
        return {"ok": not out["hata"], **out}

    @api_router.get("/yp/menu/{mk}/sonuc/{batch}")
    async def sonuc(mk: str, batch: str, _: dict = adm):
        await yalniz_yemek()
        if mk != "trendyol_yemek":
            raise HTTPException(404, "Yok")
        c = await shop_sync.market_cfg(db, mk)
        code, d = await shop_sync.http("GET", _base(c) + f"/batch-requests/{batch}", await headers(mk, c))
        if code >= 300:
            raise HTTPException(502, str(d)[:160])
        bad = [{"urun": (i.get("requestItem") or {}).get("productId"), "neden": i.get("failureReasons")} for i in d.get("items") or [] if i.get("status") != "SUCCESS"]
        return {"durum": d.get("status"), "toplam": d.get("itemCount"), "hatali": d.get("failedItemCount"), "hatalar": bad}

    @api_router.post("/yp/menu/{mk}/esle")
    async def esle(mk: str, payload: dict, _: dict = adm):
        await yalniz_yemek()
        pid, rid = str(payload.get("id") or ""), str(payload.get("uzak") or "")[:40]
        if mk not in FOOD or not pid:
            raise HTTPException(422, "Ürün seçin")
        await db.yp_products.update_one({"id": pid}, {"$set": {f"food.ext.{mk}": rid}} if rid else {"$unset": {f"food.ext.{mk}": ""}})
        return {"ok": True}

    @api_router.get("/yp/menu/{mk}/dosya")
    async def dosya(mk: str, _: dict = adm):
        await yalniz_yemek()
        if mk not in FOOD:
            raise HTTPException(404, "Bilinmeyen platform")
        body = menu_csv(await _prods(db, mk), mk)
        return Response(content=body.encode("utf-8"), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="menu-%s.csv"' % mk})
