# -*- coding: utf-8 -*-
"""Kanal yönetimi uçları + stok/fiyat kuyruğu + pazaryeri sipariş stoğu (bkz. shop_channels.py ilkeleri)."""
import asyncio
import csv
import io
import json
import re
import uuid
import base64
from datetime import datetime, timezone
from typing import Optional

import requests
from fastapi import Depends, HTTPException, Request
from fastapi.responses import Response

import shop_channels as ch

HTTP = {"fn": None}          # testlerde taklit edilir: fn(method, url, headers, body) -> (status, data)
CANCELLED = {"cancelled", "canceled", "iptal", "returned", "unsupplied", "cancel"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


async def market_cfg(db, mk: str) -> dict:
    d = await db.app_settings.find_one({"_id": "sp_modules"}, {"_id": 0}) or {}
    c = dict((d.get("config") or {}).get(mk, {}) or {})
    if not c:
        ig = (await db.app_settings.find_one({"_id": "integrations"}, {"_id": 0}) or {}).get("marketplace") or {}
        if ig.get("provider") == mk:
            c = {"seller_id": ig.get("seller_id") or ig.get("merchant_id", ""), "merchant_id": ig.get("merchant_id") or ig.get("seller_id", ""),
                 "api_key": ig.get("api_key", ""), "api_secret": ig.get("api_secret", ""), "service_key": ig.get("api_secret", ""),
                 "app_key": ig.get("api_key", ""), "app_secret": ig.get("api_secret", "")}
    return c


def connected(mk: str, c: dict) -> bool:
    if mk == "trendyol":
        return bool(c.get("seller_id") and c.get("api_key") and c.get("api_secret"))
    if mk == "hepsiburada":
        return bool(c.get("merchant_id") and c.get("service_key"))
    if mk == "n11":
        return bool(c.get("app_key") and c.get("app_secret"))
    if mk == "ciceksepeti":
        return bool(c.get("api_key"))
    if mk == "pazarama":
        return bool(c.get("client_id") and c.get("client_secret"))
    if mk == "pttavm":
        return bool(c.get("api_key") and c.get("access_token"))
    return False


def _headers(mk: str, c: dict) -> dict:
    if mk == "trendyol":
        return {"Authorization": "Basic " + base64.b64encode(f"{c['api_key']}:{c['api_secret']}".encode()).decode(),
                "User-Agent": f"{c['seller_id']} - SelfIntegration", "Content-Type": "application/json"}
    if mk == "hepsiburada":
        return {"Authorization": "Basic " + base64.b64encode(f"{c['merchant_id']}:{c['service_key']}".encode()).decode(),
                "User-Agent": c.get("developer") or "onlinekaydet", "Content-Type": "application/json"}
    return {"appkey": c["app_key"], "appsecret": c["app_secret"], "Content-Type": "application/json"}


async def http(method: str, url: str, headers: dict, body=None):
    if HTTP["fn"]:
        return await HTTP["fn"](method, url, headers, body)

    def go():
        if isinstance(body, dict) and "__form__" in body:
            data = body["__form__"]                       # form gövdesi (OAuth anahtar isteği)
        else:
            data = json.dumps(body) if body is not None else None
        r = requests.request(method, url, headers=headers, data=data, timeout=25)
        try:
            return r.status_code, r.json()
        except Exception:                                  # noqa: BLE001
            return r.status_code, {"raw": r.text[:300]}
    return await asyncio.to_thread(go)


def urls(mk: str, c: dict) -> dict:
    if mk == "trendyol":
        sid = c.get("seller_id")
        return {"stock": f"https://apigw.trendyol.com/integration/inventory/sellers/{sid}/products/price-and-inventory",
                "create": f"https://apigw.trendyol.com/integration/product/sellers/{sid}/products",
                "batch": f"https://apigw.trendyol.com/integration/product/sellers/{sid}/products/batch-requests/"}
    if mk == "hepsiburada":
        mid = c.get("merchant_id")
        return {"stock": f"https://listing-external.hepsiburada.com/listings/merchantid/{mid}/inventory-uploads"}
    return {"stock": "https://api.n11.com/ms/product/tasks/price-stock-update"}


def stock_body(mk: str, prods: list) -> object:
    if mk == "trendyol":
        return {"items": [{"barcode": p["barcode"] or p["sku"], "quantity": ch.channel_stock(p, mk), "salePrice": ch.channel_price(p, mk),
                           "listPrice": max(float(p.get("old_price") or 0), ch.channel_price(p, mk))} for p in prods]}
    if mk == "hepsiburada":
        return [{"merchantSku": p["sku"], "availableStock": ch.channel_stock(p, mk), "price": ch.channel_price(p, mk)} for p in prods]
    return {"payload": {"integrator": "OnlineKaydet", "skus": [{"stockCode": p["sku"], "quantity": ch.channel_stock(p, mk), "listPrice": max(float(p.get("old_price") or 0), ch.channel_price(p, mk)),
                                                             "salePrice": ch.channel_price(p, mk), "currencyType": "TL"} for p in prods]}}


def _attr_list(cm: dict, attrs: dict) -> list:
    """Kategori özellikleri: değer listede varsa değer kodu, yoksa serbest metin olarak gönderilir."""
    meta = {str(a.get("id")): a for a in (cm.get("required_attrs") or [])}
    out = []
    for k, v in attrs.items():
        v = str(v).strip()
        if not str(k).isdigit() or not v:
            continue
        vals = {str(x.get("id")) for x in (meta.get(str(k)) or {}).get("values") or []}
        if v.isdigit() and (not vals or v in vals):
            out.append({"attributeId": int(k), "attributeValueId": int(v)})
        else:
            out.append({"attributeId": int(k), "customAttributeValue": v})
    return out


def trendyol_item(p: dict, cm: dict, bm: dict, settings: dict) -> dict:
    """Trendyol createProducts (v2) kalemi — alan adları resmi belgedeki gibi."""
    attrs = {**(cm.get("attrs") or {}), **((p.get("market_attrs") or {}).get("trendyol") or {})}
    item = {"barcode": p["barcode"], "title": p["name"][:100], "productMainId": p.get("model") or p["sku"], "brandId": int(bm[(p.get("brand") or "").strip().lower()]),
            "categoryId": int(cm["ext_id"]), "quantity": ch.channel_stock(p, "trendyol"), "stockCode": p["sku"], "dimensionalWeight": float(p.get("desi") or 1),
            "description": (p.get("description") or p.get("short") or "")[:30000], "currencyType": "TRY",
            "listPrice": max(float(p.get("old_price") or 0), ch.channel_price(p, "trendyol")), "salePrice": ch.channel_price(p, "trendyol"), "vatRate": int(p.get("kdv", 20)),
            "images": [{"url": u} for u in ([(settings["origin"] + x if str(x).startswith("/") else x) for x in (p.get("images") or [])] if settings.get("origin") else (settings.get("abs_images") or {}).get(p["id"], p.get("images") or []))][:8],
            "attributes": _attr_list(cm, attrs)}
    if settings.get("cargo_company_id"):
        item["cargoCompanyId"] = int(settings["cargo_company_id"])
    return item


def register(api_router, db, deps):
    adm = Depends(deps["require_admin"])

    async def catmaps(mk: str) -> dict:
        return {d["category_id"]: d async for d in db.market_catmap.find({"market": mk}, {"_id": 0})}

    async def brandmap(mk: str) -> dict:
        d = await db.app_settings.find_one({"_id": f"brandmap_{mk}"}, {"_id": 0}) or {}
        return {k.lower(): v for k, v in (d.get("map") or {}).items()}

    async def mset(mk: str) -> dict:
        return await db.app_settings.find_one({"_id": f"market_settings_{mk}"}, {"_id": 0}) or {}

    def check_mk(mk):
        if mk not in ch.MARKETS or not ch.MARKETS[mk]["live"]:
            raise HTTPException(404, "Bu pazaryeri henüz desteklenmiyor")

    # ------------------------------------------------------------------ iç kategori ağacı
    @api_router.get("/shop/categories")
    async def cat_list(_: dict = adm):
        rows = await db.shop_categories.find({}, {"_id": 0}).sort([("sort", 1), ("name", 1)]).to_list(2000)
        used = {}
        async for p in db.shop_products.find({}, {"_id": 0, "category_id": 1}):
            used[p.get("category_id", "")] = used.get(p.get("category_id", ""), 0) + 1
        return [{**r, "products": used.get(r["id"], 0)} for r in rows]

    @api_router.post("/shop/categories")
    async def cat_add(payload: dict, _: dict = adm):
        name = str(payload.get("name", "")).strip()[:80]
        if len(name) < 2:
            raise HTTPException(422, "Kategori adı gerekli")
        parent = str(payload.get("parent") or "")
        if parent and not await db.shop_categories.find_one({"id": parent}, {"_id": 1}):
            raise HTTPException(422, "Üst kategori bulunamadı")
        if await db.shop_categories.find_one({"name": name, "parent": parent}, {"_id": 1}):
            raise HTTPException(409, "Bu kategori zaten var")
        doc = {"id": str(uuid.uuid4()), "name": name, "parent": parent, "sort": int(_f(payload.get("sort"), 100)), "created_at": _now()}
        await db.shop_categories.insert_one(dict(doc))
        return doc

    @api_router.put("/shop/categories/{cid}")
    async def cat_edit(cid: str, payload: dict, _: dict = adm):
        c = await db.shop_categories.find_one({"id": cid}, {"_id": 0})
        if not c:
            raise HTTPException(404, "Kategori yok")
        name = str(payload.get("name", c["name"])).strip()[:80]
        if len(name) < 2:
            raise HTTPException(422, "Kategori adı gerekli")
        await db.shop_categories.update_one({"id": cid}, {"$set": {"name": name, "sort": int(_f(payload.get("sort"), c.get("sort", 100)))}})
        await db.shop_products.update_many({"category_id": cid}, {"$set": {"category": name}})        # ürünlerdeki ad hep ağaçla aynı kalır
        return {"ok": True}

    @api_router.delete("/shop/categories/{cid}")
    async def cat_del(cid: str, _: dict = adm):
        if await db.shop_products.count_documents({"category_id": cid}) or await db.shop_categories.count_documents({"parent": cid}):
            raise HTTPException(409, "Kategoride ürün veya alt kategori var; önce taşıyın")
        await db.shop_categories.delete_one({"id": cid})
        await db.market_catmap.delete_many({"category_id": cid})
        return {"ok": True}

    # ------------------------------------------------------------------ pazaryeri eşlemeleri
    @api_router.get("/shop/channels")
    async def chan_overview(_: dict = adm):
        out = []
        prods = await db.shop_products.find({}, {"_id": 0}).to_list(50000)
        for mk, meta in ch.MARKETS.items():
            row = {"id": mk, "name": meta["name"], "live": meta["live"], "connected": False, "counts": {}}
            if meta["live"]:
                row["connected"] = connected(mk, await market_cfg(db, mk))
                cm, bm = await catmaps(mk), await brandmap(mk)
                cnt = {}
                for p in prods:
                    s = ch.state(p, mk, cm.get(p.get("category_id", "")), bm)["status"]
                    cnt[s] = cnt.get(s, 0) + 1
                row["counts"] = cnt
            out.append(row)
        return {"channels": out, "total": len(prods)}

    @api_router.get("/shop/channels/{mk}/catmap")
    async def catmap_get(mk: str, _: dict = adm):
        check_mk(mk)
        cats = await db.shop_categories.find({}, {"_id": 0}).sort("name", 1).to_list(2000)
        cm = await catmaps(mk)
        bm = (await db.app_settings.find_one({"_id": f"brandmap_{mk}"}, {"_id": 0}) or {}).get("map") or {}
        brands = sorted({(p.get("brand") or "").strip() async for p in db.shop_products.find({}, {"_id": 0, "brand": 1}) if (p.get("brand") or "").strip()})
        return {"categories": [{**c, "map": cm.get(c["id"])} for c in cats], "brands": [{"name": b, "ext_id": bm.get(b, bm.get(b.lower(), ""))} for b in brands], "settings": await mset(mk)}

    @api_router.put("/shop/channels/{mk}/catmap/{cid}")
    async def catmap_put(mk: str, cid: str, payload: dict, _: dict = adm):
        check_mk(mk)
        if not await db.shop_categories.find_one({"id": cid}, {"_id": 1}):
            raise HTTPException(404, "Kategori yok")
        ext = str(payload.get("ext_id", "")).strip()[:40]
        if ext and not ext.isdigit() and mk == "trendyol":
            raise HTTPException(422, "Trendyol kategori kodu sayı olmalı")
        req = []
        for a in (payload.get("required_attrs") or [])[:60]:
            aid = str(a.get("id") if a.get("id") not in (None, "") else "n_" + re.sub(r"[^a-z0-9]+", "_", str(a.get("name", "")).lower())).strip()[:30]
            if not aid or aid == "n_":
                continue
            vals = [{"id": str(v.get("id"))[:20], "name": str(v.get("name", ""))[:80]} for v in (a.get("values") or [])[:500] if isinstance(v, dict) and v.get("id") is not None]
            req.append({"id": aid, "name": str(a.get("name", ""))[:60], "required": a.get("required", True) is not False, "allow_custom": bool(a.get("allow_custom")), "values": vals})
        attrs = {str(k)[:20]: str(v)[:40] for k, v in (payload.get("attrs") or {}).items()}
        if not ext:
            await db.market_catmap.delete_one({"market": mk, "category_id": cid})
        else:
            await db.market_catmap.update_one({"market": mk, "category_id": cid}, {"$set": {"market": mk, "category_id": cid, "ext_id": ext, "ext_name": str(payload.get("ext_name", ""))[:120],
                                                                                          "required_attrs": req, "attrs": attrs, "updated_at": _now()}}, upsert=True)
        return {"ok": True}

    @api_router.get("/shop/channels/{mk}/category-attrs")
    async def category_attrs(mk: str, ext_id: str, _: dict = adm):
        """Pazaryerinin kategori özelliklerini (renk, beden/ebat ...) ve seçilebilir değerlerini getirir. Şimdilik yalnızca Trendyol'da otomatik."""
        check_mk(mk)
        ext_id = str(ext_id).strip()
        if mk != "trendyol":
            raise HTTPException(501, "Bu pazaryerinde özellikler elle eklenir (Özellik ekle düğmesi); satıcı panelindeki kategori şablonundaki adları yazın.")
        if not ext_id.isdigit():
            raise HTTPException(422, "Önce Trendyol kategori kodunu (sayı) girin")
        c = await market_cfg(db, mk)
        if not connected(mk, c):
            raise HTTPException(400, "Önce Trendyol anahtarlarını girin (Pazaryerleri > Aç/Kapat & Ayarlar)")
        code, data = await http("GET", f"https://apigw.trendyol.com/integration/product/product-categories/{ext_id}/attributes", _headers(mk, c))
        if code >= 300:
            raise HTTPException(502, f"Trendyol yanıtı {code}: {str(data)[:160]}")
        out = []
        for a in (data.get("categoryAttributes") or []):
            at = a.get("attribute") or {}
            if at.get("id") is None:
                continue
            out.append({"id": str(at["id"]), "name": at.get("name", ""), "required": bool(a.get("required")), "allow_custom": bool(a.get("allowCustom")),
                        "values": [{"id": str(v.get("id")), "name": v.get("name", "")} for v in (a.get("attributeValues") or []) if v.get("id") is not None][:500]})
        return {"attrs": out}

    @api_router.put("/shop/channels/{mk}/brandmap")
    async def brandmap_put(mk: str, payload: dict, _: dict = adm):
        check_mk(mk)
        m = {str(k).strip()[:60]: str(v).strip()[:40] for k, v in (payload.get("map") or {}).items() if str(v).strip()}
        await db.app_settings.update_one({"_id": f"brandmap_{mk}"}, {"$set": {"map": m}}, upsert=True)
        return {"ok": True}

    @api_router.put("/shop/channels/{mk}/settings")
    async def mset_put(mk: str, payload: dict, _: dict = adm):
        check_mk(mk)
        s = {"cargo_company_id": str(payload.get("cargo_company_id", "")).strip()[:10], "shipment_template": str(payload.get("shipment_template", "")).strip()[:60],
             "default_buffer": max(0, int(_f(payload.get("default_buffer"), 0)))}
        await db.app_settings.update_one({"_id": f"market_settings_{mk}"}, {"$set": s}, upsert=True)
        return s

    # ------------------------------------------------------------------ kanal ürün ekranı (stok/fiyat/durum matrisi)
    @api_router.get("/shop/catalog")
    async def catalog(q: str = "", category: str = "", stock: str = "", channel: str = "", page: int = 1, per: int = 40, _: dict = adm):
        """Tek ürün listesi: tüm kanalların (site + pazaryerleri) durumu aynı satırda."""
        mks = [m for m, v in ch.MARKETS.items() if v.get("live")]
        cms = {m: await catmaps(m) for m in mks}
        bms = {m: await brandmap(m) for m in mks}
        flt = {}
        if q.strip():
            rx = {"$regex": re.escape(q.strip()), "$options": "i"}
            flt["$or"] = [{"name": rx}, {"sku": rx}, {"barcode": rx}, {"brand": rx}]
        if category:
            flt["$and"] = [{"$or": [{"category": category}, {"category_ids": category}, {"category_id": category}]}]
        rows, cats, low, out = [], {}, 0, 0
        async for p in db.shop_products.find(flt, {"_id": 0, "specs": 0, "description": 0}).sort("name", 1):
            stk = int(p.get("stock") or 0)
            mn = int(p.get("min_stock") or 0)
            is_low = stk <= mn if mn else stk <= 2
            if stk <= 0:
                out += 1
            elif is_low:
                low += 1
            if stock == "out" and stk > 0:
                continue
            if stock == "low" and not (stk > 0 and is_low):
                continue
            chs = {"site": {"on": bool(p.get("active", True)), "status": "yayinda" if p.get("active", True) else "kapali", "issues": []}}
            for m in mks:
                st = ch.state(p, m, cms[m].get(p.get("category_id", "")), bms[m])
                chs[m] = {"on": st["status"] != "kapali", "status": st["status"], "issues": [i.get("msg", "") for i in st["issues"]][:4], "error": st["error"]}
            if channel and channel != "all":
                if channel.startswith("no_"):
                    if chs.get(channel[3:], {}).get("on"):
                        continue
                elif not chs.get(channel, {}).get("on"):
                    continue
            cats[p.get("category", "")] = cats.get(p.get("category", ""), 0) + 1
            rows.append({"id": p["id"], "name": p["name"], "sku": p.get("sku", ""), "barcode": p.get("barcode", ""), "brand": p.get("brand", ""), "category": p.get("category", ""),
                         "shelf": p.get("shelf", ""), "stock": stk, "price": p.get("price", 0), "min_stock": mn, "low": is_low and stk > 0, "image": (p.get("images") or [""])[0], "ch": chs})
        per = max(10, min(per, 200))
        return {"total": len(rows), "low": low, "out": out, "rows": rows[(page - 1) * per: page * per], "page": page, "per": per, "markets": [{"id": m, "name": ch.MARKETS[m]["name"]} for m in mks]}

    @api_router.get("/shop/channels/{mk}/products")
    async def chan_products(mk: str, status: str = "", q: str = "", page: int = 1, per: int = 50, _: dict = adm):
        check_mk(mk)
        cm, bm = await catmaps(mk), await brandmap(mk)
        flt = {}
        if q.strip():
            rx = {"$regex": re.escape(q.strip()), "$options": "i"}
            flt["$or"] = [{"name": rx}, {"sku": rx}, {"barcode": rx}, {"brand": rx}]
        rows = []
        counts = {}
        async for p in db.shop_products.find(flt, {"_id": 0, "specs": 0}).sort("name", 1):
            stt = ch.state(p, mk, cm.get(p.get("category_id", "")), bm)
            counts[stt["status"]] = counts.get(stt["status"], 0) + 1
            if status and stt["status"] != status:
                continue
            rows.append({"id": p["id"], "name": p["name"], "sku": p.get("sku", ""), "barcode": p.get("barcode", ""), "brand": p.get("brand", ""), "category": p.get("category", ""),
                         "shelf": p.get("shelf", ""), "pool_stock": p.get("stock", 0), "site_price": p.get("price", 0), "min_stock": p.get("min_stock", 0),
                         "image": (p.get("images") or [""])[0], **stt})
        per = max(10, min(per, 200))
        return {"total": len(rows), "counts": counts, "rows": rows[(page - 1) * per: page * per], "page": page, "per": per}

    @api_router.post("/yp/products/bulk-market")
    async def bulk_market(payload: dict, request: Request, _: dict = adm):
        """Seçili panel ürünleri için toplu pazaryeri işlemi.
        send: seçili pazaryerlerini açar, eksikleri raporlar, hazır ürünleri (Trendyol bağlıysa) gönderir.
        close: ürünü tüm kanallarda satışa kapatır ve yayındaki pazaryerlerine stok 0 bildirir.  open: sitede yeniden açar."""
        import urun_ayna
        ids = [str(i) for i in (payload.get("ids") or [])][:500]
        op = payload.get("op")
        mks = [m for m in (payload.get("markets") or []) if m in ch.MARKETS and ch.MARKETS[m]["live"]]
        if not ids or op not in ("send", "close", "open"):
            raise HTTPException(422, "Ürünleri ve işlemi seçin")
        if op == "send" and not mks:
            raise HTTPException(422, "En az bir pazaryeri seçin")
        prods = [p async for p in db.yp_products.find({"id": {"$in": ids}}, {"_id": 0})]
        if not prods:
            raise HTTPException(404, "Ürün bulunamadı")
        now = _now()
        for p in prods:
            chs = dict(p.get("channels") or {})
            up = {}
            if op == "send":
                for m in mks:
                    chs[m] = True
                up["status"] = "live"
            elif op == "close":
                chs = {k: False for k in list(chs) + ["site"]}
            else:
                chs["site"] = True
                up["status"] = "live"
            up.update(channels=chs, updated_at=now)
            await db.yp_products.update_one({"id": p["id"]}, {"$set": up})
            await urun_ayna.ayna(db, p["id"])
        pids = [p["id"] for p in prods]
        if op == "open":
            return {"ok": True, "op": op, "n": len(pids)}
        if op == "close":
            n = await _enqueue(db, pids, kinds=("stock",), force=True)
            res = await process_queue(db) if n else {"sent": 0, "failed": 0}
            return {"ok": True, "op": op, "n": len(pids), "queued": n, "sent": res["sent"], "failed": res["failed"]}
        out = []
        for mk in mks:
            cm, bm = await catmaps(mk), await brandmap(mk)
            ready, blocked = [], []
            async for sp in db.shop_products.find({"id": {"$in": pids}}, {"_id": 0}):
                iss = ch.issues(sp, mk, cm.get(sp.get("category_id", "")), bm)
                (blocked if iss else ready).append((sp, iss))
            r = {"market": mk, "name": ch.MARKETS[mk]["name"], "enabled": len(pids), "ready": len(ready), "sent": 0, "note": "",
                 "blocked": [{"id": sp["id"], "name": sp["name"], "issues": [i["msg"] for i in iss][:4]} for sp, iss in blocked[:20]],
                 "blocked_n": len(blocked)}
            if ready:
                if mk == "trendyol":
                    try:
                        x = await create_listing(mk, {"ids": [sp["id"] for sp, _i in ready], "dry_run": False}, request, None)
                        r["sent"] = x.get("sent", 0)
                    except HTTPException as e:
                        r["note"] = str(e.detail)
                else:
                    r["note"] = "Bu pazaryerine ürün açma otomatik değil; hazır ürünleri Pazaryerleri ekranındaki dışa aktarma dosyasıyla yükleyin"
            elif not blocked:
                r["note"] = "Gönderilecek ürün yok"
            out.append(r)
        await _enqueue(db, pids, markets=mks, kinds=("stock",))
        return {"ok": True, "op": op, "n": len(pids), "markets": out}

    @api_router.put("/shop/channels/{mk}/products/{pid}")
    async def chan_product_set(mk: str, pid: str, payload: dict, _: dict = adm):
        check_mk(mk)
        p = await db.shop_products.find_one({"id": pid}, {"_id": 0})
        if not p:
            raise HTTPException(404, "Ürün yok")
        cur = p.get("channels") or {}
        chs = ch.clean_channels({mk: {**(cur.get(mk) or {}), **{k: payload[k] for k in ("enabled", "price", "buffer") if k in payload}}}, cur)
        await db.shop_products.update_one({"id": pid}, {"$set": {"channels": {**cur, **chs}, "updated_at": _now()}})
        await enqueue(db, [pid], markets=[mk], kinds=("stock",))
        return {"ok": True}

    # ------------------------------------------------------------------ stok hareketi (kolay stok / raf)
    @api_router.post("/shop/products/{pid}/stock")
    async def stock_adjust(pid: str, payload: dict, user: dict = adm):
        """mode: set (sayım) | add (giriş) | remove (çıkış). Her işlem stok hareketine yazılır; kanallara kuyrukla iletilir."""
        p = await db.shop_products.find_one({"id": pid}, {"_id": 0})
        if not p:
            raise HTTPException(404, "Ürün yok")
        mode = payload.get("mode", "set")
        n = int(_f(payload.get("qty"), -1))
        if n < 0 or mode not in ("set", "add", "remove"):
            raise HTTPException(422, "Geçerli bir adet girin")
        old = int(p.get("stock") or 0)
        new = n if mode == "set" else (old + n if mode == "add" else old - n)
        if new < 0:
            raise HTTPException(422, "Stok eksiye düşemez (mevcut: %d)" % old)
        upd = {"stock": new, "track_stock": True, "updated_at": _now()}
        if "shelf" in payload:
            upd["shelf"] = str(payload["shelf"]).strip()[:30]
        await db.shop_products.update_one({"id": pid}, {"$set": upd})
        await db.shop_stock_log.insert_one({"id": str(uuid.uuid4()), "product_id": pid, "name": p["name"], "mode": mode, "qty": n, "old": old, "new": new,
                                            "reason": str(payload.get("reason", ""))[:120], "by": (user or {}).get("name", ""), "source": "panel", "at": _now()})
        await enqueue(db, [pid])
        return {"ok": True, "stock": new}

    @api_router.get("/shop/stock-log")
    async def stock_log(product_id: str = "", _: dict = adm):
        flt = {"product_id": product_id} if product_id else {}
        return await db.shop_stock_log.find(flt, {"_id": 0}).sort("at", -1).to_list(300)

    @api_router.get("/shop/low-stock")
    async def low_stock(_: dict = adm):
        rows = await db.shop_products.find({"track_stock": True, "active": True}, {"_id": 0, "id": 1, "name": 1, "stock": 1, "min_stock": 1, "shelf": 1, "sku": 1}).to_list(50000)
        return sorted([r for r in rows if int(r.get("stock") or 0) <= int(r.get("min_stock") or 0)], key=lambda r: r.get("stock", 0))

    # ------------------------------------------------------------------ hazırlık kontrolü, dışa aktarma, ürün açma
    @api_router.get("/shop/channels/{mk}/validate")
    async def validate(mk: str, _: dict = adm):
        check_mk(mk)
        cm, bm = await catmaps(mk), await brandmap(mk)
        out = []
        async for p in db.shop_products.find({"channels." + mk + ".enabled": True}, {"_id": 0}):
            iss = ch.issues(p, mk, cm.get(p.get("category_id", "")), bm)
            out.append({"id": p["id"], "name": p["name"], "issues": iss, "ready": not iss})
        return {"ready": sum(1 for r in out if r["ready"]), "blocked": sum(1 for r in out if not r["ready"]), "rows": out}

    @api_router.post("/shop/channels/{mk}/create")
    async def create_listing(mk: str, payload: dict, request: Request, _: dict = adm):
        """Hazır ürünleri pazaryerinde açar. dry_run (varsayılan açık): hiçbir şey göndermez, gidecek içeriği ve eksikleri gösterir."""
        check_mk(mk)
        dry = payload.get("dry_run", True) is not False
        ids = [str(x) for x in (payload.get("ids") or [])][:200]
        cm, bm, st = await catmaps(mk), await brandmap(mk), await mset(mk)
        flt = {"channels." + mk + ".enabled": True}
        if ids:
            flt["id"] = {"$in": ids}
        ready, blocked = [], []
        async for p in db.shop_products.find(flt, {"_id": 0}):
            iss = ch.issues(p, mk, cm.get(p.get("category_id", "")), bm)
            (blocked if iss else ready).append((p, iss))
        if mk != "trendyol":
            raise HTTPException(501, "Bu pazaryerinde ürün açma, hesap doğrulaması gerektirdiği için henüz otomatik değil. Dışa aktarma dosyasını (CSV) kullanın.")
        base = {**st}
        origin = (request.headers.get("origin") or "").rstrip("/") or ("https://" + (request.headers.get("x-forwarded-host") or request.headers.get("host") or ""))
        base["origin"] = origin
        base["abs_images"] = {p["id"]: [(origin + u if str(u).startswith("/") else u) for u in (p.get("images") or [])] for p, _i in ready}
        items = [trendyol_item(u, cm[p["category_id"]], bm, base) for p, _i in ready for u in ch.units(p, mk, cm[p["category_id"]])]
        res = {"dry_run": dry, "ready": len(ready), "blocked": [{"id": p["id"], "name": p["name"], "issues": i} for p, i in blocked]}
        if dry:
            res["preview"] = items[:3]
            return res
        c = await market_cfg(db, mk)
        if not connected(mk, c):
            raise HTTPException(400, "Trendyol bilgileri eksik (Entegrasyonlar)")
        if not items:
            raise HTTPException(422, "Gönderilecek hazır ürün yok")
        code, data = await http("POST", urls(mk, c)["create"], _headers(mk, c), {"items": items})
        if code >= 300:
            raise HTTPException(502, f"Trendyol yanıtı {code}: {str(data)[:200]}")
        batch = str((data or {}).get("batchRequestId") or "")
        for p, _i in ready:
            await db.shop_products.update_one({"id": p["id"]}, {"$set": {f"market_sync.{mk}.batch": batch, f"market_sync.{mk}.at": _now(), f"market_sync.{mk}.error": "",
                                                                          f"market_sync.{mk}.created_sent": True}})
        return {**res, "sent": len(items), "batch": batch}

    @api_router.post("/shop/channels/{mk}/batch-check")
    async def batch_check(mk: str, payload: dict, _: dict = adm):
        check_mk(mk)
        if mk != "trendyol":
            raise HTTPException(501, "Yalnızca Trendyol")
        c = await market_cfg(db, mk)
        bid = re.sub(r"[^A-Za-z0-9\-]", "", str(payload.get("batch", "")))[:80]
        if not bid or not connected(mk, c):
            raise HTTPException(422, "Toplu işlem kodu veya bağlantı eksik")
        code, data = await http("GET", urls(mk, c)["batch"] + bid, _headers(mk, c))
        if code >= 300:
            raise HTTPException(502, f"Trendyol yanıtı {code}")
        done = 0
        for it in (data or {}).get("items") or []:
            bc = str((it.get("requestItem") or {}).get("barcode") or "")
            ok = it.get("status") == "SUCCESS"
            err = "; ".join(it.get("failureReasons") or [])[:300]
            if bc:
                await db.shop_products.update_one({"barcode": bc}, {"$set": {f"market_sync.{mk}.listed": ok or None, f"market_sync.{mk}.error": "" if ok else err, f"market_sync.{mk}.at": _now()}})
                done += 1
        return {"checked": done, "status": (data or {}).get("status"), "failed": (data or {}).get("failedItemCount")}

    @api_router.post("/shop/channels/{mk}/mark-listed")
    async def mark_listed(mk: str, payload: dict, _: dict = adm):
        """Pazaryerinde zaten yayında olan ürünleri (barkoduyla) 'yayında' olarak eşler; sonra stok/fiyat gönderimi başlar."""
        check_mk(mk)
        ids = [str(x) for x in (payload.get("ids") or [])][:2000]
        r = await db.shop_products.update_many({"id": {"$in": ids}, f"channels.{mk}.enabled": True}, {"$set": {f"market_sync.{mk}.listed": True, f"market_sync.{mk}.error": ""}})
        await enqueue(db, ids, markets=[mk])
        return {"ok": True, "marked": r.modified_count}

    @api_router.get("/shop/channels/{mk}/export.csv")
    async def export_csv(mk: str, _: dict = adm):
        check_mk(mk)
        cm, bm = await catmaps(mk), await brandmap(mk)
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=";")
        w.writerow(["Barkod", "Stok Kodu", "Ürün Adı", "Marka", "Kategori (kod)", "Açıklama", "Görsel 1", "Görsel 2", "Görsel 3", "Satış Fiyatı", "KDV", "Stok", "Desi", "Hazırlık Günü", "Eksikler"])
        async for p in db.shop_products.find({"channels." + mk + ".enabled": True}, {"_id": 0}):
            cmm = cm.get(p.get("category_id", "")) or {}
            iss = ch.issues(p, mk, cmm, bm)
            im = (p.get("images") or []) + ["", "", ""]
            w.writerow([p.get("barcode", ""), p.get("sku", ""), p["name"], p.get("brand", ""), cmm.get("ext_id", ""), re.sub(r"<[^>]+>", " ", p.get("description") or p.get("short") or "")[:4000],
                        im[0], im[1], im[2], ch.channel_price(p, mk), p.get("kdv", ""), ch.channel_stock(p, mk), p.get("desi", ""), p.get("delivery_days", ""), " | ".join(i["msg"] for i in iss)])
        return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f"attachment; filename={mk}-urunler.csv"})

    # ------------------------------------------------------------------ kuyruk
    async def enqueue(db_, product_ids, markets=None, kinds=("stock",)):
        return await _enqueue(db_, product_ids, markets, kinds)

    @api_router.post("/shop/sync/run")
    async def sync_run(_: dict = adm):
        return await process_queue(db)

    @api_router.get("/shop/sync/queue")
    async def sync_queue(_: dict = adm):
        rows = await db.shop_sync_queue.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
        return {"pending": sum(1 for r in rows if r["status"] == "bekliyor"), "failed": sum(1 for r in rows if r["status"] == "hata"), "rows": rows}

    api_router.shop_enqueue = lambda ids, **kw: _enqueue(db, ids, **kw)
    api_router.shop_process = lambda: process_queue(db)
    api_router.shop_apply_market_order = lambda mk, key, raw: apply_market_order(db, mk, key, raw)


# =================================================================== kuyruk çekirdeği
async def _enqueue(db, product_ids, markets=None, kinds=("stock",), force=False):
    """Ürün(ler)in açık ve bağlı pazaryerlerine gidecek stok/fiyat işi ekler (aynı ürün+pazaryeri için bekleyen varsa tekrar eklemez)."""
    try:                                                       # panel ürünü ise düşen/artan stoğu panele de yaz
        import urun_ayna
        await urun_ayna.geri(db, list(product_ids or []))
    except Exception:                                          # noqa: BLE001
        pass
    n = 0
    for pid in dict.fromkeys(product_ids or []):
        p = await db.shop_products.find_one({"id": pid}, {"_id": 0, "channels": 1, "market_sync": 1})
        if not p:
            continue
        for mk, c in (p.get("channels") or {}).items():
            if mk == "site" or (not c.get("enabled") and not force) or (markets and mk not in markets):
                continue
            if not ((p.get("market_sync") or {}).get(mk) or {}).get("listed"):
                continue                       # pazaryerinde henüz yayında olmayan ürüne stok gönderilmez
            for k in kinds:
                if await db.shop_sync_queue.find_one({"market": mk, "product_id": pid, "kind": k, "status": "bekliyor"}, {"_id": 1}):
                    continue
                await db.shop_sync_queue.insert_one(ch.new_job(mk, pid, k))
                n += 1
    return n


async def process_queue(db, limit=100):
    """Bekleyen işleri pazaryeri başına tek toplu istekle gönderir. Başarısızlar en fazla 5 kez denenir."""
    sent, failed = 0, 0
    jobs = await db.shop_sync_queue.find({"status": "bekliyor"}, {"_id": 0}).sort("created_at", 1).to_list(1000)
    by_mk = {}
    for j in jobs:
        by_mk.setdefault(j["market"], []).append(j)
    for mk, js in by_mk.items():
        c = await market_cfg(db, mk)
        for i in range(0, len(js), limit):
            part = js[i:i + limit]
            ids = list(dict.fromkeys(j["product_id"] for j in part))
            prods = [p async for p in db.shop_products.find({"id": {"$in": ids}}, {"_id": 0})]
            prods = [u for p in prods for u in ch.units(p, mk) if (u.get("barcode") or u.get("sku"))]
            err = ""
            if not connected(mk, c):
                err = "Pazaryeri bağlantı bilgileri eksik"
            elif prods:
                try:
                    if mk in ("ciceksepeti", "pazarama", "pttavm"):
                        import markets_hub
                        u_, b_ = markets_hub.stock_request(mk, c, prods)
                        code, data = await http(c.get("stock_method") or ("PUT" if mk == "ciceksepeti" else "POST"), u_, await markets_hub.headers(mk, c), b_)
                    else:
                        code, data = await http("POST", urls(mk, c)["stock"], _headers(mk, c), stock_body(mk, prods))
                    if code >= 300:
                        err = f"{mk} yanıtı {code}: {str(data)[:160]}"
                except Exception as e:                       # noqa: BLE001
                    err = f"Bağlantı hatası: {str(e)[:120]}"
            for j in part:
                if not err:
                    await db.shop_sync_queue.update_one({"id": j["id"]}, {"$set": {"status": "tamam", "done_at": _now(), "error": ""}})
                else:
                    att = j["attempts"] + 1
                    await db.shop_sync_queue.update_one({"id": j["id"]}, {"$set": {"attempts": att, "error": err, "status": "hata" if att >= 5 else "bekliyor"}})
            for pid_ in dict.fromkeys(p.get("parent_id") or p["id"] for p in prods):
                await db.shop_products.update_one({"id": pid_}, {"$set": {f"market_sync.{mk}.at": _now(), f"market_sync.{mk}.error": err}})
            sent += 0 if err else len(part)
            failed += len(part) if err else 0
    return {"sent": sent, "failed": failed}


def _lines(mk: str, raw: dict) -> list:
    """Pazaryeri siparişinden (barkod/stok kodu, adet) satırları."""
    out = []
    for ln in (raw.get("lines") or raw.get("items") or raw.get("lineItems") or raw.get("orderItems") or []):
        code = str(ln.get("barcode") or ln.get("merchantSku") or ln.get("stockCode") or ln.get("sku") or "").strip()
        qty = int(_f(ln.get("quantity") or ln.get("qty") or 1, 1))
        if code and qty > 0:
            out.append((code, qty))
    return out


async def _bul(db, code):
    """Pazaryeri satır kodundan (barkod/stok kodu) ürün ve varyant bul: (pid, vid) ya da (None, "")."""
    p = await db.shop_products.find_one({"variants": {"$elemMatch": {"$or": [{"barcode": code}, {"sku": code}]}}}, {"_id": 0, "id": 1, "variants": 1})
    if p:
        v = next((x for x in p["variants"] if code and code in (x.get("barcode"), x.get("sku"))), None)
        return p["id"], (v or {}).get("id", "")
    p = await db.shop_products.find_one({"$or": [{"barcode": code}, {"sku": code}]}, {"_id": 0, "id": 1})
    return (p["id"], "") if p else (None, "")


async def _varyant_stok(db, pid, vid, delta):
    """Varyant stoğunu değiştir; eksiye düşmesin; toplam stok varyantlardan yeniden hesaplanır."""
    await db.shop_products.update_one({"id": pid, "variants.id": vid}, {"$inc": {"variants.$.stock": delta}})
    await db.shop_products.update_one({"id": pid, "variants": {"$elemMatch": {"id": vid, "stock": {"$lt": 0}}}}, {"$set": {"variants.$.stock": 0}})
    d = await db.shop_products.find_one({"id": pid}, {"_id": 0, "variants": 1})
    await db.shop_products.update_one({"id": pid}, {"$set": {"stock": sum(int(v.get("stock") or 0) for v in (d or {}).get("variants", []) if v.get("active", True))}})


async def apply_market_order(db, mk: str, key: str, raw: dict):
    """Pazaryeri siparişi bir kez stoktan düşer; iptal/iade durumuna geçerse stok geri gelir; diğer pazaryerlerine bildirilir."""
    status = str(raw.get("status") or raw.get("packageStatus") or raw.get("shipmentPackageStatus") or "").strip().lower()
    await db.sp_market_orders.update_one({"market": mk, "key": key}, {"$setOnInsert": {"market": mk, "key": key}}, upsert=True)
    doc = await db.sp_market_orders.find_one({"market": mk, "key": key}, {"_id": 0, "stock_applied": 1, "stock_restored": 1}) or {}
    touched = []
    if status in CANCELLED:
        if doc.get("stock_applied") and not doc.get("stock_restored"):
            r = await db.sp_market_orders.update_one({"market": mk, "key": key, "stock_restored": {"$ne": True}}, {"$set": {"stock_restored": True}})
            if r.modified_count:
                for code, qty in _lines(mk, raw):
                    pid, vid = await _bul(db, code)
                    if pid:
                        if vid:
                            await _varyant_stok(db, pid, vid, qty)
                        else:
                            await db.shop_products.update_one({"id": pid, "track_stock": True}, {"$inc": {"stock": qty}})
                        await _log(db, pid, "+%d" % qty, "pazaryeri iptali", mk, key)
                        touched.append(pid)
    elif not doc.get("stock_applied"):
        r = await db.sp_market_orders.update_one({"market": mk, "key": key, "stock_applied": {"$ne": True}}, {"$set": {"stock_applied": True}})
        if r.modified_count:
            for code, qty in _lines(mk, raw):
                pid, vid = await _bul(db, code)
                if not pid:
                    await db.sp_market_orders.update_one({"market": mk, "key": key}, {"$push": {"unmatched": code}})
                    continue
                if vid:
                    await _varyant_stok(db, pid, vid, -qty)
                    await db.shop_products.update_one({"id": pid}, {"$inc": {"sold": qty}})
                else:
                    await db.shop_products.update_one({"id": pid, "track_stock": True}, {"$inc": {"stock": -qty, "sold": qty}})
                    await db.shop_products.update_one({"id": pid, "stock": {"$lt": 0}}, {"$set": {"stock": 0}})
                await _log(db, pid, "-%d" % qty, "pazaryeri siparişi", mk, key)
                touched.append(pid)
    if touched:
        await _enqueue(db, touched)                            # düşen stok, siparişin geldiği pazaryeri dahil tüm kanallara yansır
    return touched


async def _log(db, pid, qty, reason, mk, key):
    p = await db.shop_products.find_one({"id": pid}, {"_id": 0, "name": 1, "stock": 1})
    await db.shop_stock_log.insert_one({"id": str(uuid.uuid4()), "product_id": pid, "name": (p or {}).get("name", ""), "mode": "order", "qty": qty, "old": None,
                                        "new": (p or {}).get("stock"), "reason": f"{reason} ({mk} {key})", "by": "sistem", "source": mk, "at": _now()})
