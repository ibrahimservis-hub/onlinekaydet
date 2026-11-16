# -*- coding: utf-8 -*-
"""Pazaryeri bağlantısı, kategori/marka eşleştirme ve stok senkronu.

Stok tek merkezde tutulur: `yp_products.stock`. Hangi kanaldan sipariş gelirse gelsin
stok **koşullu** düşülür (negatife inemez) ve diğer açık kanallara gönderim kuyruğa alınır.
Aynı sipariş iki kez işlenirse stok ikinci kez düşmez (sipariş anahtarı tekildir).
Bu iki kural, satıcının en çok korktuğu şeyi — aynı ürünü iki kanalda birden satmayı — engeller.
"""
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException

from urun import CHANNELS, _int, _num, _t

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

MARKETS = [k for k in CHANNELS if k != "site"]
STATES = ("bekliyor", "gonderildi", "hata")
MAX_TRY = 5


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


# ---------------------------------------------------------------- stok (paylaşılan çekirdek)
async def _ayna(db, pid):
    try:
        import urun_ayna
        await urun_ayna.ayna(db, pid)
    except Exception:                                              # noqa: BLE001
        pass


async def queue_push(db, pid, channel, kind="stock", ref=""):
    await db.yp_sync.insert_one({"id": uuid.uuid4().hex[:12], "product": pid, "channel": channel,
                                 "kind": kind, "state": "bekliyor", "tries": 0, "ref": ref,
                                 "at": _now(), "err": ""})


async def take_stock(db, pid, qty, source, ref, vid=""):
    """Stoğu koşullu düş. Yetersizse hiç düşmez. Aynı `ref` ikinci kez işlenmez."""
    qty = _int(qty)
    if qty <= 0:
        raise HTTPException(422, "Adet 1 veya daha fazla olmalı")
    key = "%s|%s|%s" % (source, ref, pid) + ("|" + vid if vid else "")
    if ref and await db.yp_stock_log.find_one({"key": key}, {"_id": 1}):
        return {"ok": True, "repeat": True, "taken": 0}
    p = await db.yp_products.find_one({"id": pid}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Ürün bulunamadı")
    vs = p.get("variants") or []
    if vs and not vid:
        return {"ok": False, "repeat": False, "taken": 0, "stock": _int(p.get("stock")), "err": "Seçenek (renk/beden vb.) seçilmeli"}
    v = next((x for x in vs if x.get("id") == vid), None) if vid else None
    if vid and not v:
        return {"ok": False, "repeat": False, "taken": 0, "stock": _int(p.get("stock")), "err": "Seçenek bulunamadı"}
    before = _int((v or p).get("stock"))
    if p.get("track_stock", True):
        if v:
            r = await db.yp_products.update_one(
                {"id": pid, "variants": {"$elemMatch": {"id": vid, "stock": {"$gte": qty}}}},
                {"$inc": {"variants.$.stock": -qty, "stock": -qty}})
        else:
            r = await db.yp_products.update_one({"id": pid, "stock": {"$gte": qty}}, {"$inc": {"stock": -qty}})
        if not r.modified_count:
            return {"ok": False, "repeat": False, "taken": 0, "stock": before,
                    "err": "Stok yetersiz: %d adet var, %d istendi" % (before, qty)}
    after = max(before - qty, 0)
    await db.yp_stock_log.insert_one({"id": uuid.uuid4().hex[:12], "key": key, "product": pid, "delta": -qty,
                                      "before": before, "after": after, "source": source, "ref": ref, "variant": vid,
                                      "at": _now(), "seq": time.time()})
    await _ayna(db, pid)
    for k, on in (p.get("channels") or {}).items():
        if on and k != source and k in MARKETS:
            await queue_push(db, pid, k, "stock", ref)
    if after <= 0:
        for k, on in (p.get("channels") or {}).items():
            if on and k in MARKETS:
                await queue_push(db, pid, k, "passive", ref)
    return {"ok": True, "repeat": False, "taken": qty, "stock": after}


async def give_stock(db, pid, qty, source, ref, vid=""):
    """İptal/iade: stoğu geri ekle ve kanallara bildir. Aynı `ref` ikinci kez eklenmez."""
    qty = _int(qty)
    if qty <= 0:
        return {"ok": True, "given": 0}
    key = "iade|%s|%s" % (ref, pid) + ("|" + vid if vid else "")
    if ref and await db.yp_stock_log.find_one({"key": key}, {"_id": 1}):
        return {"ok": True, "repeat": True, "given": 0}
    p = await db.yp_products.find_one({"id": pid}, {"_id": 0})
    if not p:
        return {"ok": False, "given": 0, "err": "Ürün bulunamadı"}
    v = next((x for x in (p.get("variants") or []) if x.get("id") == vid), None) if vid else None
    before = _int((v or p).get("stock"))
    if v:
        await db.yp_products.update_one({"id": pid, "variants.id": vid}, {"$inc": {"variants.$.stock": qty, "stock": qty}})
    else:
        await db.yp_products.update_one({"id": pid}, {"$inc": {"stock": qty}})
    await _ayna(db, pid)
    await db.yp_stock_log.insert_one({"id": uuid.uuid4().hex[:12], "key": key, "product": pid, "delta": qty,
                                      "before": before, "after": before + qty, "source": source, "ref": ref, "variant": vid,
                                      "at": _now(), "seq": time.time()})
    for k, on in (p.get("channels") or {}).items():
        if on and k in MARKETS:
            await queue_push(db, pid, k, "stock", ref)
    return {"ok": True, "repeat": False, "given": qty, "stock": before + qty}


def register(api_router, db, deps):
    adm = deps["require_admin"]
    push = deps.get("channel_push")                                # canlıda pazaryeri API'sine gönderen yardımcı

    # ------------------------------------------------------------ bağlantılar
    @api_router.get("/yp/channels")
    async def channels(_: dict = Depends(adm)):
        have = {c["id"]: c for c in await db.yp_channels.find({}, {"_id": 0, "keys": 0}).to_list(50)}
        rows = []
        for k in MARKETS:
            name, comm = CHANNELS[k]
            c = have.get(k) or {}
            n_map = await db.yp_catmap.count_documents({"channel": k})
            n_list = await db.yp_listings.count_documents({"channel": k})
            rows.append({"id": k, "name": name, "commission": comm, "on": bool(c.get("on")),
                         "status": c.get("status") or ("bagli" if c.get("on") else "yok"),
                         "last_sync": c.get("last_sync", ""), "mapped": n_map, "listings": n_list,
                         "pending": await db.yp_sync.count_documents({"channel": k, "state": "bekliyor"}),
                         "errors": await db.yp_sync.count_documents({"channel": k, "state": "hata"})})
        return {"rows": rows}

    @api_router.put("/yp/channels/{cid}")
    async def channel_put(cid: str, payload: dict, _: dict = Depends(adm)):
        if cid not in MARKETS:
            raise HTTPException(404, "Pazaryeri bulunamadı")
        up = {"id": cid, "on": bool(payload.get("on")), "updated_at": _now()}
        keys = payload.get("keys")
        if isinstance(keys, dict):
            up["keys"] = {_t(k, 40): _t(v, 300) for k, v in list(keys.items())[:10]}
            up["status"] = "bagli" if up["on"] and up["keys"] else "yok"
        await db.yp_channels.update_one({"id": cid}, {"$set": up}, upsert=True)
        return {k: v for k, v in up.items() if k != "keys"}

    # ------------------------------------------------------------ eşleştirme
    @api_router.get("/yp/channels/{cid}/map")
    async def map_get(cid: str, _: dict = Depends(adm)):
        if cid not in MARKETS:
            raise HTTPException(404, "Pazaryeri bulunamadı")
        rows = await db.yp_products.find({}, {"_id": 0, "cat": 1, "brand": 1}).to_list(20000)
        cats, brands = {}, {}
        for r in rows:
            if r.get("cat"):
                cats[r["cat"]] = cats.get(r["cat"], 0) + 1
            if r.get("brand"):
                brands[r["brand"]] = brands.get(r["brand"], 0) + 1
        cm = {m["local"]: m for m in await db.yp_catmap.find({"channel": cid}, {"_id": 0}).to_list(2000)}
        bm = {m["local"]: m for m in await db.yp_brandmap.find({"channel": cid}, {"_id": 0}).to_list(2000)}
        cr = [{"local": k, "n": v, "remote": cm.get(k, {}).get("remote", ""),
               "remote_id": cm.get(k, {}).get("remote_id", ""), "ok": bool(cm.get(k, {}).get("remote_id"))}
              for k, v in sorted(cats.items(), key=lambda x: -x[1])]
        br = [{"local": k, "n": v, "remote": bm.get(k, {}).get("remote", ""),
               "remote_id": bm.get(k, {}).get("remote_id", ""), "ok": bool(bm.get(k, {}).get("remote_id"))}
              for k, v in sorted(brands.items(), key=lambda x: -x[1])]
        return {"channel": cid, "cats": cr, "brands": br,
                "cats_missing": sum(1 for x in cr if not x["ok"]), "brands_missing": sum(1 for x in br if not x["ok"])}

    @api_router.put("/yp/channels/{cid}/map")
    async def map_put(cid: str, payload: dict, _: dict = Depends(adm)):
        if cid not in MARKETS:
            raise HTTPException(404, "Pazaryeri bulunamadı")
        n = 0
        for kind, coll in (("cats", db.yp_catmap), ("brands", db.yp_brandmap)):
            for row in (payload.get(kind) or [])[:2000]:
                loc = _t((row or {}).get("local"), 80)
                if not loc:
                    continue
                rid = _t(row.get("remote_id"), 80)
                if rid:
                    await coll.update_one({"channel": cid, "local": loc},
                                          {"$set": {"channel": cid, "local": loc, "remote_id": rid,
                                                    "remote": _t(row.get("remote"), 160), "at": _now()}}, upsert=True)
                else:
                    await coll.delete_one({"channel": cid, "local": loc})
                n += 1
        return {"ok": True, "n": n}

    # ------------------------------------------------------------ gönderim kuyruğu
    async def queue(pid, channel, kind="stock", ref=""):
        await queue_push(db, pid, channel, kind, ref)

    async def ready(pid, cid):
        """Ürün bu kanala gönderilebilir mi: kategori ve marka eşleşmiş olmalı."""
        p = await db.yp_products.find_one({"id": pid}, {"_id": 0})
        if not p:
            return False, "Ürün yok"
        if p.get("cat") and not await db.yp_catmap.find_one({"channel": cid, "local": p["cat"]}, {"_id": 1}):
            return False, "“%s” kategorisi %s ile eşleşmemiş" % (p["cat"], CHANNELS[cid][0])
        if p.get("brand") and not await db.yp_brandmap.find_one({"channel": cid, "local": p["brand"]}, {"_id": 1}):
            return False, "“%s” markası %s ile eşleşmemiş" % (p["brand"], CHANNELS[cid][0])
        return True, ""

    @api_router.post("/yp/channels/{cid}/send")
    async def send(cid: str, payload: dict, _: dict = Depends(adm)):
        """Ürünleri kanala gönder. Eşleşmemiş kategori/marka varsa o ürün atlanır."""
        if cid not in MARKETS:
            raise HTTPException(404, "Pazaryeri bulunamadı")
        ch = await db.yp_channels.find_one({"id": cid}, {"_id": 0}) or {}
        if not ch.get("on"):
            raise HTTPException(422, "Önce %s bağlantısını açın" % CHANNELS[cid][0])
        ids = [str(i) for i in (payload.get("ids") or [])][:5000]
        if not ids:
            ids = [p["id"] for p in await db.yp_products.find({"status": "live"}, {"_id": 0, "id": 1}).to_list(20000)]
        sent, skip = 0, []
        for pid in ids:
            okk, why = await ready(pid, cid)
            if not okk:
                skip.append({"id": pid, "why": why})
                continue
            await db.yp_listings.update_one({"product": pid, "channel": cid},
                                            {"$set": {"product": pid, "channel": cid, "state": "bekliyor", "at": _now()}}, upsert=True)
            await queue(pid, cid, "full", "elle")
            sent += 1
        return {"ok": True, "sent": sent, "skipped": skip[:50], "skipped_n": len(skip)}

    # ------------------------------------------------------------ stok senkronu
    @api_router.post("/yp/stock/take")
    async def stock_take(payload: dict, _: dict = Depends(adm)):
        """Sipariş geldi: stok düş, diğer kanallara gönderimi kuyruğa al."""
        src = _t(payload.get("source"), 24) or "site"
        if src not in CHANNELS:
            raise HTTPException(422, "Kanal tanınmadı")
        out = []
        for it in (payload.get("items") or [])[:200]:
            out.append(dict(await take_stock(db, _t((it or {}).get("product"), 24), it.get("qty", 1), src,
                                             _t(payload.get("ref"), 60), _t((it or {}).get("variant_id"), 20)), product=it.get("product")))
        bad = [o for o in out if not o["ok"]]
        return {"ok": not bad, "rows": out, "queued": await db.yp_sync.count_documents({"state": "bekliyor"})}

    @api_router.post("/yp/stock/set")
    async def stock_set(payload: dict, _: dict = Depends(adm)):
        """Stoğu elle ayarla; fark tüm açık kanallara gönderilir."""
        pid = _t(payload.get("product"), 24)
        p = await db.yp_products.find_one({"id": pid}, {"_id": 0})
        if not p:
            raise HTTPException(404, "Ürün bulunamadı")
        n = max(_int(payload.get("stock")), 0)
        vid = _t(payload.get("variant_id"), 20)
        if p.get("variants"):
            v = next((x for x in p["variants"] if x.get("id") == vid), None)
            if not v:
                raise HTTPException(422, "Bu üründe seçenek var; hangi seçeneğin stoğu olduğunu belirtin")
            before = _int(v.get("stock"))
            await db.yp_products.update_one({"id": pid, "variants.id": vid}, {"$set": {"variants.$.stock": n, "updated_at": _now()}})
            tot = sum((n if x.get("id") == vid else _int(x.get("stock"))) for x in p["variants"] if x.get("active", True))
            await db.yp_products.update_one({"id": pid}, {"$set": {"stock": tot}})
        else:
            before = _int(p.get("stock"))
            await db.yp_products.update_one({"id": pid}, {"$set": {"stock": n, "updated_at": _now()}})
        await _ayna(db, pid)
        await db.yp_stock_log.insert_one({"id": uuid.uuid4().hex[:12], "key": "", "product": pid, "delta": n - before,
                                          "before": before, "after": n, "source": "elle", "ref": "", "variant": vid, "at": _now(), "seq": time.time()})
        for k, on in (p.get("channels") or {}).items():
            if on and k in MARKETS:
                await queue(pid, k, "stock", "elle")
        return {"ok": True, "stock": n, "before": before}

    @api_router.get("/yp/stock/log")
    async def stock_log(product: str = "", limit: int = 100, _: dict = Depends(adm)):
        q = {"product": product} if product else {}
        rows = await db.yp_stock_log.find(q, {"_id": 0}).sort("seq", -1).to_list(min(max(limit, 1), 500))
        return {"rows": rows}

    # ------------------------------------------------------------ kuyruk işleme
    @api_router.get("/yp/sync")
    async def sync_list(state: str = "", limit: int = 100, _: dict = Depends(adm)):
        q = {"state": state} if state in STATES else {}
        rows = await db.yp_sync.find(q, {"_id": 0}).sort("at", -1).to_list(min(max(limit, 1), 500))
        return {"rows": rows,
                "counts": {s: await db.yp_sync.count_documents({"state": s}) for s in STATES}}

    @api_router.post("/yp/sync/run")
    async def sync_run(payload: dict = None, _: dict = Depends(adm)):
        """Kuyruğu işle. Gönderim yardımcısı yoksa kayıtlar bekler, kaybolmaz."""
        payload = payload or {}
        rows = await db.yp_sync.find({"state": {"$in": ["bekliyor", "hata"]}}, {"_id": 0}).sort("at", 1).to_list(int(payload.get("limit") or 200))
        done, err = 0, 0
        for r in rows:
            if r["tries"] >= MAX_TRY:
                continue
            p = await db.yp_products.find_one({"id": r["product"]}, {"_id": 0})
            if not p:
                await db.yp_sync.update_one({"id": r["id"]}, {"$set": {"state": "hata", "err": "Ürün silinmiş"}})
                err += 1
                continue
            if not push:
                continue
            try:
                await push(r["channel"], r["kind"], p)
                await db.yp_sync.update_one({"id": r["id"]}, {"$set": {"state": "gonderildi", "err": "", "done_at": _now()}})
                await db.yp_channels.update_one({"id": r["channel"]}, {"$set": {"last_sync": _now()}}, upsert=True)
                done += 1
            except Exception as e:                                 # noqa: BLE001
                await db.yp_sync.update_one({"id": r["id"]},
                                            {"$set": {"state": "hata", "err": str(e)[:200]}, "$inc": {"tries": 1}})
                err += 1
        return {"ok": True, "done": done, "err": err,
                "left": await db.yp_sync.count_documents({"state": "bekliyor"})}

    @api_router.post("/yp/sync/retry")
    async def sync_retry(payload: dict = None, _: dict = Depends(adm)):
        payload = payload or {}
        q = {"state": "hata"}
        if payload.get("ids"):
            q["id"] = {"$in": [str(i) for i in payload["ids"]][:500]}
        r = await db.yp_sync.update_many(q, {"$set": {"state": "bekliyor", "tries": 0, "err": ""}})
        return {"ok": True, "n": r.modified_count}
