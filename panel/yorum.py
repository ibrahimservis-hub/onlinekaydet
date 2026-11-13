"""Ürün yorumları: fotoğraflı yorum, yönetici onayı, doğrulanmış alıcı rozeti, teslimden sonra yorum hatırlatma SMS'i."""
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request

YOR_DEF = {"hatirla": False, "gun": 3, "oto_onay": False,
           "metin": "Merhaba {ad}, siparişiniz elinize ulaştı mı? Ürünü değerlendirirseniz çok seviniriz: {link}"}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _tel(v):
    return re.sub(r"\D", "", str(v or ""))[-10:]


def _foto_ok(x):
    return isinstance(x, str) and re.match(r"^data:image/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+$", x) is not None and len(x) <= 450000


async def hatirlat_tara(db, host=""):
    """Teslim edileli `gun` günü geçen siparişlere bir kez yorum isteği SMS'i yollar."""
    import notify
    cfg = await _cfg(db)
    if not cfg["hatirla"]:
        return 0
    sinir = (datetime.now(timezone.utc) - timedelta(days=int(cfg["gun"]))).isoformat(timespec="seconds")
    n = 0
    async for o in db.shop_orders.find({"status": "teslim_edildi", "yorum_hat": {"$exists": False}}, {"_id": 0}).limit(100):
        t = next((h["at"] for h in reversed(o.get("history") or []) if h.get("status") == "teslim_edildi"), o.get("updated_at") or "")
        if not t or t > sinir:
            continue
        c = o.get("customer") or {}
        it = (o.get("items") or [{}])[0]
        p = await db.shop_products.find_one({"id": it.get("product_id")}, {"_id": 0, "slug": 1, "id": 1})
        link = ("https://%s" % host if host else "") + "/magaza/urun/" + str((p or {}).get("slug") or (p or {}).get("id") or "")
        ad = (c.get("name") or "").split(" ")[0] or "değerli müşterimiz"
        r = await notify.send(db, "sms", c.get("phone", ""), cfg["metin"].replace("{ad}", ad).replace("{link}", link), kind="yorum_hat", ref="order:" + o["id"])
        if (r or {}).get("status") == "sent":
            await db.shop_orders.update_one({"id": o["id"]}, {"$set": {"yorum_hat": _now()}})
            n += 1
    return n


async def _cfg(db):
    d = await db.app_settings.find_one({"_id": "yp_yorum"}, {"_id": 0}) or {}
    return {**YOR_DEF, **d}


def register(api_router, db, deps):
    adm = deps["require_admin"]

    @api_router.get("/public/shop/yorum/{pid}")
    async def yorum_liste(pid: str):
        rows = await db.shop_reviews.find({"pid": pid, "status": "ok"}, {"_id": 0, "phone": 0}).sort("at", -1).to_list(100)
        ort = round(sum(r["rating"] for r in rows) / len(rows), 1) if rows else 0
        return {"rows": rows, "adet": len(rows), "ortalama": ort}

    @api_router.post("/public/shop/yorum")
    async def yorum_ekle(payload: dict):
        pid = str(payload.get("product_id", ""))
        p = await db.shop_products.find_one({"id": pid, "active": True}, {"_id": 0, "id": 1})
        if not p:
            raise HTTPException(404, "Ürün bulunamadı")
        try:
            puan = int(payload.get("rating"))
        except (TypeError, ValueError):
            puan = 0
        if not 1 <= puan <= 5:
            raise HTTPException(422, "Lütfen 1-5 arası puan verin")
        ad = str(payload.get("name", "")).strip()[:60]
        txt = str(payload.get("text", "")).strip()[:1500]
        if not ad or len(txt) < 5:
            raise HTTPException(422, "Adınızı ve yorumunuzu yazın")
        ph = _tel(payload.get("phone"))
        fotos = [f for f in (payload.get("photos") or [])[:3]]
        if any(not _foto_ok(f) for f in fotos):
            raise HTTPException(422, "Fotoğraflar JPG/PNG/WEBP olmalı ve küçük boyutlu olmalı")
        if ph and await db.shop_reviews.find_one({"pid": pid, "phone": ph}):
            raise HTTPException(409, "Bu ürüne zaten yorum yazdınız")
        dogru = False
        if len(ph) == 10:
            async for o in db.shop_orders.find({"status": "teslim_edildi", "items.product_id": pid}, {"_id": 0, "customer.phone": 1}).limit(500):
                if _tel((o.get("customer") or {}).get("phone")) == ph:
                    dogru = True
                    break
        cfg = await _cfg(db)
        durum = "ok" if cfg["oto_onay"] else "bekliyor"
        await db.shop_reviews.insert_one({"id": secrets.token_hex(8), "pid": pid, "name": ad, "rating": puan, "text": txt, "photos": fotos,
                                          "phone": ph, "dogrulanmis": dogru, "status": durum, "at": _now()})
        return {"ok": True, "onay_bekliyor": durum != "ok"}

    @api_router.get("/yp/yorumlar")
    async def yp_liste(durum: str = "", _: dict = Depends(adm)):
        q = {"status": durum} if durum in ("ok", "bekliyor") else {}
        rows = await db.shop_reviews.find(q, {"_id": 0}).sort("at", -1).to_list(300)
        for r in rows:
            p = await db.shop_products.find_one({"id": r["pid"]}, {"_id": 0, "name": 1})
            r["urun"] = (p or {}).get("name", "(silinmiş ürün)")
        return {"rows": rows, "cfg": await _cfg(db)}

    @api_router.put("/yp/yorumlar/ayar")
    async def yp_ayar(payload: dict, _: dict = Depends(adm)):
        c = await _cfg(db)
        for k in ("hatirla", "oto_onay"):
            if k in payload:
                c[k] = bool(payload[k])
        if "gun" in payload:
            try:
                c["gun"] = max(1, min(30, int(payload["gun"])))
            except (TypeError, ValueError):
                raise HTTPException(422, "Gün sayısı geçersiz")
        if "metin" in payload:
            c["metin"] = str(payload["metin"]).strip()[:300] or YOR_DEF["metin"]
        await db.app_settings.update_one({"_id": "yp_yorum"}, {"$set": c}, upsert=True)
        return c

    @api_router.put("/yp/yorumlar/{rid}")
    async def yp_durum(rid: str, payload: dict, _: dict = Depends(adm)):
        st = "ok" if payload.get("status") == "ok" else "bekliyor"
        r = await db.shop_reviews.update_one({"id": rid}, {"$set": {"status": st}})
        if not r.matched_count:
            raise HTTPException(404, "Yorum bulunamadı")
        return {"ok": True, "status": st}

    @api_router.delete("/yp/yorumlar/{rid}")
    async def yp_sil(rid: str, _: dict = Depends(adm)):
        await db.shop_reviews.delete_one({"id": rid})
        return {"ok": True}

    @api_router.post("/yp/yorumlar/hatirlat")
    async def yp_hatirlat(request: Request, _: dict = Depends(adm)):
        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
        return {"gonderilen": await hatirlat_tara(db, host)}

    try:
        import governance

        async def _hook(d):
            try:
                await hatirlat_tara(d)
            except Exception:      # noqa: BLE001
                pass
        governance.HOOKS.append(_hook)
    except Exception:      # noqa: BLE001
        pass
