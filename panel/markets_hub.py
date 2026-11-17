# -*- coding: utf-8 -*-
"""Pazaryeri merkezi: tüm pazaryerlerinden siparişleri OTOMATİK çeker, sipariş listesine ekler ve tek stok havuzundan düşer.

- Pazaryerleri: Trendyol, Hepsiburada, N11 (belgeli uçlar) + Çiçeksepeti, Pazarama, PttAVM (uçlar ayardan değiştirilebilir; gerçek hesapla test edilmelidir).
- Otomatik çekim: 5 dakikada bir, bağlantı bilgisi tam olan her firma ve pazaryeri için. Tek işçi çalışsın diye veritabanında kısa süreli kilit (lease) vardır.
- Stok doğruluğu: ilk bağlanışta bulunan ESKİ siparişler listeye "geçmiş" diye alınır ama stoktan düşülmez (stok zaten güncel girilmiştir);
  yalnızca bağlantıdan SONRA gelen siparişler stoğu bir kez düşer. İptal/iade olursa stok geri gelir. Düşen stok tüm kanallara yansır.
- Çekilen sipariş `sp_market_orders` (ham kayıt) ve `shop_orders` (kaynak=pazaryeri, external=True) koleksiyonlarına yazılır.
"""
import asyncio
import base64
import logging
import os
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from pymongo.errors import DuplicateKeyError

import shop_sync
import shop_channels as ch

log = logging.getLogger("markets_hub")

ALL = ["trendyol", "hepsiburada", "n11", "ciceksepeti", "pazarama", "pttavm"]
# Yemek platformları (restoran/lokanta): siparişler aynı sipariş listesine düşer; ürün listesi/stok gönderimi yoktur.
FOOD = {"yemeksepeti": "Yemeksepeti", "trendyol_yemek": "Trendyol Yemek", "getir_yemek": "Getir Yemek", "migros_yemek": "Migros Yemek"}
ALL = ALL + list(FOOD)
PREFIX = {"trendyol": "TY", "hepsiburada": "HB", "n11": "N11", "ciceksepeti": "CS", "pazarama": "PZ", "pttavm": "PTT",
          "yemeksepeti": "YS", "trendyol_yemek": "TYY", "getir_yemek": "GY", "migros_yemek": "MY"}
VERIFIED = {"trendyol": True, "hepsiburada": True, "n11": True, "ciceksepeti": False, "pazarama": False, "pttavm": False,
            "yemeksepeti": False, "trendyol_yemek": False, "getir_yemek": False, "migros_yemek": False}


def _name(mk: str) -> str:
    return FOOD.get(mk) or ch.MARKETS[mk]["name"]
INTERVAL = int(os.environ.get("MARKET_PULL_S", "300"))
_TOK = {}                      # Pazarama erişim anahtarı önbelleği


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _first(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d.get(k)
    return None


# =================================================================== bağlantı bilgisi / istek kurulumu
connected = shop_sync.connected


async def _pazarama_token(c: dict) -> str:
    key = c.get("client_id")
    hit = _TOK.get(key)
    if hit and hit[1] > time.time():
        return hit[0]
    url = c.get("token_url") or "https://isortagimgiris.pazarama.com/connect/token"
    basic = base64.b64encode(f"{c['client_id']}:{c['client_secret']}".encode()).decode()
    hdr = {"Authorization": "Basic " + basic, "Content-Type": "application/x-www-form-urlencoded"}
    code, data = await shop_sync.http("POST", url, hdr, {"__form__": {"grant_type": "client_credentials", "scope": "merchantgatewayapi.fullaccess"}})
    tok = (data or {}).get("access_token") if isinstance(data, dict) else None
    if code >= 300 or not tok:
        raise RuntimeError(f"Pazarama anahtarı alınamadı ({code}): {str(data)[:120]}")
    _TOK[key] = (tok, time.time() + min(int(_f((data or {}).get("expires_in"), 3600)), 3600) - 120)
    return tok


async def headers(mk: str, c: dict) -> dict:
    if mk in ("trendyol", "hepsiburada", "n11"):
        return shop_sync._headers(mk, c)
    if mk == "trendyol_yemek":
        return {"Authorization": "Basic " + base64.b64encode(f"{c['api_key']}:{c['api_secret']}".encode()).decode(),
                "User-Agent": f"{c.get('seller_id')} - SelfIntegration", "Content-Type": "application/json"}
    if mk in ("getir_yemek", "migros_yemek"):
        return {"Authorization": c.get("token") or "", "x-api-key": c.get("token") or "", "Content-Type": "application/json"}
    if mk == "yemeksepeti":
        return {"Authorization": "Bearer " + (c.get("token") or ""), "Content-Type": "application/json"}
    if mk == "ciceksepeti":
        return {"x-api-key": c["api_key"], "Content-Type": "application/json"}
    if mk == "pazarama":
        return {"Authorization": "Bearer " + await _pazarama_token(c), "Content-Type": "application/json"}
    return {"Api-Key": c["api_key"], "Access-Token": c["access_token"], "Content-Type": "application/json"}


def order_request(mk: str, c: dict) -> tuple:
    """(yöntem, adres, gövde) — adres/yöntem ayardaki orders_url / orders_method ile değiştirilebilir."""
    since = (datetime.now(timezone.utc) - timedelta(days=7))
    if mk == "trendyol":
        sid = c.get("seller_id")
        m, u, b = "GET", f"https://apigw.trendyol.com/integration/order/sellers/{sid}/orders?size=50&orderByField=PackageLastModifiedDate&orderByDirection=DESC", None
    elif mk == "hepsiburada":
        m, u, b = "GET", f"https://oms-external.hepsiburada.com/packages/merchantid/{c.get('merchant_id')}?limit=50&offset=0", None
    elif mk == "n11":
        m, u, b = "GET", "https://api.n11.com/rest/delivery/v1/shipmentPackages?size=50", None
    elif mk == "ciceksepeti":
        m, u, b = "POST", "https://apis.ciceksepeti.com/api/v1/Order/GetOrders", {"PageSize": 50, "Page": 0}
    elif mk == "pazarama":
        m, u, b = "POST", "https://isortagimapi.pazarama.com/order/getOrdersForApi", {"pageSize": 50, "pageNumber": 1, "startDate": since.strftime("%Y-%m-%dT%H:%M:%S"), "endDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")}
    elif mk == "trendyol_yemek":
        m, u, b = "GET", f"https://api.tgoapis.com/integrator/order/meal/suppliers/{c.get('seller_id')}/packages?size=50", None
    elif mk in ("getir_yemek", "migros_yemek", "yemeksepeti"):
        m, u, b = "GET", "", None                                   # adres ayardan gelir (orders_url); yemeksepeti siparişleri çoğunlukla webhook ile gelir
    else:
        m, u, b = "GET", "https://integration-api.pttavm.com/api/orders?page=1&size=50", None
    return (c.get("orders_method") or m).upper(), (c.get("orders_url") or u), b


def stock_request(mk: str, c: dict, prods: list) -> tuple:
    """Yeni pazaryerleri için stok gönderimi: (adres, gövde). Eski üçü shop_sync.urls/stock_body kullanır."""
    rows = [(p.get("sku") or p.get("barcode"), ch.channel_stock(p, mk), ch.channel_price(p, mk), max(float(p.get("old_price") or 0), ch.channel_price(p, mk))) for p in prods]
    if mk == "ciceksepeti":
        return (c.get("stock_url") or "https://apis.ciceksepeti.com/api/v1/Products/price-and-stock",
                {"items": [{"stockCode": s, "stockQuantity": q, "salesPrice": pr, "listPrice": lp} for s, q, pr, lp in rows]})
    if mk == "pazarama":
        return (c.get("stock_url") or "https://isortagimapi.pazarama.com/product/updateStock-v2",
                {"stockList": [{"code": s, "stockCount": q} for s, q, _pr, _lp in rows]})
    return (c.get("stock_url") or "https://integration-api.pttavm.com/api/products/stock",
            {"items": [{"sku": s, "stock": q, "price": pr} for s, q, pr, _lp in rows]})


# =================================================================== normalize
def map_status(s: str) -> str:
    low = str(s or "").strip().lower()
    if any(k in low for k in ("undeliver", "cancel", "iptal", "return", "iade", "unsupplied")):
        return "iptal"
    if any(k in low for k in ("deliver", "teslim")):
        return "teslim_edildi"
    if any(k in low for k in ("ship", "kargo", "transit", "yolda", "ontheway", "on_the_way", "dispatch", "picked")):
        return "kargoda"
    if any(k in low for k in ("pick", "invoic", "hazir", "prepar", "fatura", "ready", "cook")):
        return "hazirlaniyor"
    return "onaylandi"


def _ts(v):
    """Epoch (sn/ms) veya ISO metin -> datetime(UTC) | None."""
    try:
        if isinstance(v, (int, float)) or (isinstance(v, str) and v.strip().isdigit()):
            n = float(v)
            return datetime.fromtimestamp(n / 1000 if n > 1e11 else n, timezone.utc)
        if isinstance(v, str) and v:
            d = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None
    return None


def rows_of(data):
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for k in ("content", "items", "data", "shipmentPackages", "packages", "orders", "orderList", "result", "supplierOrderListWithBranch"):
        v = data.get(k)
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            r = rows_of(v)
            if r:
                return r
    return []


def normalize(mk: str, r: dict) -> dict:
    key = str(_first(r, "orderNumber", "orderId", "id", "packageNumber", "number", "orderCode", "orderNo") or "")
    raw_lines = _first(r, "lines", "items", "orderItems", "lineItems", "orderLines", "products", "orderDetails") or []
    lines = []
    for ln in raw_lines if isinstance(raw_lines, list) else []:
        if not isinstance(ln, dict):
            continue
        code = str(_first(ln, "barcode", "merchantSku", "stockCode", "sku", "productCode", "code", "productBarcode") or "").strip()
        qty = int(_f(_first(ln, "quantity", "qty", "count", "piece", "adet"), 1)) or 1
        price = _f(_first(ln, "price", "salePrice", "unitPrice", "amount", "totalPrice"))
        lines.append({"barcode": code, "quantity": qty, "name": str(_first(ln, "productName", "name", "title", "productTitle") or code)[:200], "price": price})
    total = _f(_first(r, "totalPrice", "totalAmount", "grossAmount", "total", "orderTotal", "payableAmount", "grandTotal", "totalPayment")) or round(sum(x["price"] * x["quantity"] for x in lines), 2)
    adr = _first(r, "shipmentAddress", "shippingAddress", "deliveryAddress", "address") or {}
    adr = adr if isinstance(adr, dict) else {"fullAddress": str(adr)}
    cu = r.get("customer") if isinstance(r.get("customer"), dict) else {}
    if cu:                                                          # yemek platformları müşteriyi iç içe verir
        r = dict(r, customerName=_first(cu, "name", "fullName", "firstName") or "", customerPhone=_first(cu, "phone", "mobile", "gsm") or "")
        if not adr or not _first(adr, "fullAddress", "address", "address1", "addressDetail"):
            adr = _first(cu, "address", "deliveryAddress") or adr
            adr = adr if isinstance(adr, dict) else {"fullAddress": str(adr or "")}
    name = (str(_first(r, "customerFirstName", "firstName") or "") + " " + str(_first(r, "customerLastName", "lastName") or "")).strip() or \
        str(_first(r, "customerName", "buyerName", "receiverName", "fullName") or _first(adr, "fullName", "name") or "")
    created = _ts(_first(r, "orderDate", "createdDate", "createDate", "createdAt", "packageCreationDate", "orderCreatedDate", "creationDate", "date"))
    return {"key": key, "number": key, "status_raw": str(_first(r, "status", "packageStatus", "shipmentPackageStatus", "orderStatus", "statusName") or ""),
            "total": total, "lines": lines, "created": created,
            "customer": {"name": name.strip()[:120], "phone": str(_first(r, "customerPhone", "phone", "gsm", "receiverPhone") or _first(adr, "phone", "gsm") or "")[:30],
                         "email": str(_first(r, "customerEmail", "email") or "")[:120], "city": str(_first(adr, "city", "cityName", "il") or "")[:60],
                         "district": str(_first(adr, "district", "districtName", "ilce") or "")[:60],
                         "address": str(_first(adr, "fullAddress", "address", "address1", "addressDetail") or "")[:300]}}


# =================================================================== çekim
async def _state(db) -> dict:
    return (await db.app_settings.find_one({"_id": "market_auto"}, {"_id": 0})) or {}


async def _set_state(db, mk: str, **kw):
    await db.app_settings.update_one({"_id": "market_auto"}, {"$set": {f"{mk}.{k}": v for k, v in kw.items()}}, upsert=True)


async def fetch(mk: str, c: dict) -> list:
    m, u, b = order_request(mk, c)
    if not u:                                                       # yalnızca webhook ile sipariş alan platform (Yemeksepeti)
        return []
    code, data = await shop_sync.http(m, u, await headers(mk, c), b)
    if code >= 300:
        raise RuntimeError(f"{mk} yanıtı {code}: {str(data)[:200]}")
    return rows_of(data)


async def _product_id(db, cache: dict, code: str):
    if not code:
        return ""
    if code not in cache:
        p = await db.shop_products.find_one({"$or": [{"barcode": code}, {"sku": code}]}, {"_id": 0, "id": 1})
        cache[code] = (p or {}).get("id", "")
    return cache[code]


async def ingest(db, mk: str, rows: list, since: datetime) -> dict:
    """Siparişleri yazar. since'ten ESKİ olanlar geçmiş sayılır (stok düşülmez)."""
    new = hist = upd = 0
    cache = {}
    for r in rows:
        try:
            n = normalize(mk, r)
            if not n["key"]:
                continue
            mapped = map_status(n["status_raw"])
            old = n["created"] is not None and n["created"] < since
            doc = {"market": mk, "key": n["key"], "raw": r, "pulled_at": _now(), "number": n["number"], "total": n["total"], "customer": n["customer"]["name"], "status": n["status_raw"]}
            exists = await db.sp_market_orders.find_one({"market": mk, "key": n["key"]}, {"_id": 0, "stock_applied": 1})
            await db.sp_market_orders.update_one({"market": mk, "key": n["key"]}, {"$set": doc}, upsert=True)
            if old and not exists:
                # bağlantıdan önceki sipariş: stok zaten güncel girilmiştir; ikinci kez düşmesin
                await db.sp_market_orders.update_one({"market": mk, "key": n["key"]}, {"$set": {"stock_applied": True, "stock_restored": True, "baseline": True}})
                hist += 1
            else:
                await shop_sync.apply_market_order(db, mk, n["key"], {"status": "cancelled" if mapped == "iptal" else n["status_raw"], "lines": n["lines"]})
            try:                                                       # müşteri panelindeki Siparişler listesi
                import dis_siparis
                kom = (await shop_sync.market_cfg(db, mk)).get("komisyon")
                await dis_siparis.yaz(db, mk, n, mapped, comm=_f(kom) if kom not in (None, "") else None)
            except Exception as e:                             # noqa: BLE001
                log.warning("panel sipariş kaydı (%s): %s", mk, e)
            # sipariş listesi kaydı
            no = f"{PREFIX[mk]}-{n['key']}"[:40]
            cur = await db.shop_orders.find_one({"order_no": no}, {"_id": 0, "id": 1, "status": 1})
            if cur:
                if cur["status"] != mapped:
                    await db.shop_orders.update_one({"id": cur["id"]}, {"$set": {"status": mapped, "updated_at": _now(), "market_status": n["status_raw"]},
                                                                        "$push": {"history": {"status": mapped, "at": _now(), "by": mk}}})
                    upd += 1
                continue
            items = []
            for ln in n["lines"]:
                items.append({"product_id": await _product_id(db, cache, ln["barcode"]), "name": ln["name"], "sku": ln["barcode"], "qty": ln["quantity"],
                              "price": ln["price"], "line_total": round(ln["price"] * ln["quantity"], 2)})
            name = _name(mk)
            order = {"id": str(uuid.uuid4()), "order_no": no, "status": mapped, "customer": n["customer"], "note": f"{name} siparişi", "items": items,
                     "subtotal": n["total"], "shipping": 0, "cod_fee": 0, "total": n["total"], "account_id": "", "phone_key": "", "admin_note": "", "tracking_no": "", "carrier": "",
                     "payment": {"method": "pazaryeri", "label": name, "status": "odendi", "amount": n["total"]}, "source": mk, "external": True, "historical": bool(old),
                     "market_status": n["status_raw"], "created_at": (n["created"] or datetime.now(timezone.utc)).isoformat(), "updated_at": _now(),
                     "history": [{"status": mapped, "at": _now(), "by": mk, "note": name}]}
            try:
                await db.shop_orders.insert_one(order)
            except DuplicateKeyError:
                continue
            if not old:
                new += 1
                try:
                    import notify
                    await notify.notify_owner_t(db, f"Yeni {name} siparişi {no}: {n['total']:.2f} TL", kind="shop_order")
                except Exception:                                  # noqa: BLE001
                    pass
        except Exception as e:                                     # noqa: BLE001
            log.warning("sipariş işlenemedi (%s): %s", mk, e)
    return {"new": new, "historical": hist, "updated": upd}


async def pull(db, mk: str) -> dict:
    """Tek pazaryeri: siparişleri çek, işle, durumu kaydet. Hata olursa durum kaydına yazılır ve yeniden fırlatılır."""
    c = await shop_sync.market_cfg(db, mk)
    if not connected(mk, c):
        raise HTTPException(status_code=400, detail=f"{_name(mk)} bağlantı bilgileri eksik (Aç/Kapat & Ayarlar)")
    st = (await _state(db)).get(mk) or {}
    since = _ts(st.get("since"))
    first = since is None
    if first:
        since = datetime.now(timezone.utc)
        await _set_state(db, mk, since=since.isoformat())
    try:
        rows = await fetch(mk, c)
        res = await ingest(db, mk, rows, since)
    except Exception as e:                                         # noqa: BLE001
        await _set_state(db, mk, last=_now(), error=str(e)[:200])
        raise
    await _set_state(db, mk, last=_now(), error="", seen=len(rows), imported=int(st.get("imported") or 0) + res["new"])
    return {"ok": True, "pulled": len(rows), **res, "first": first}


async def pull_all(db) -> int:
    d = await db.app_settings.find_one({"_id": "sp_modules"}, {"_id": 0, "flags": 1}) or {}
    n = 0
    for mk in ALL:
        c = await shop_sync.market_cfg(db, mk)                     # yönetim ayarı ya da müşteri panelindeki Entegrasyonlar
        if not c or not connected(mk, c) or (d.get("flags") or {}).get(mk) is False:
            continue
        if mk == "yemeksepeti" and not c.get("orders_url"):
            continue                                               # bildirimle (webhook) çalışır
        try:
            await pull(db, mk)
            n += 1
        except Exception as e:                                     # noqa: BLE001
            log.warning("otomatik çekim %s: %s", mk, e)
    return n


# =================================================================== zamanlayıcı
async def _lease(main, secs: int) -> bool:
    now = time.time()
    try:
        await main.market_lease.find_one_and_update({"_id": "lease", "until": {"$lt": now}}, {"$set": {"until": now + secs, "by": os.getpid()}}, upsert=True)
        return True
    except DuplicateKeyError:
        return False


async def run_cycle(db, firms_mod, tenant) -> int:
    main = db.main()
    if not await _lease(main, max(60, INTERVAL - 30)):
        return 0
    total = 0
    try:
        total += await pull_all(db)                                # firmasız (kendi) hesap
    except Exception as e:                                         # noqa: BLE001
        log.warning("ana hesap çekimi: %s", e)
    async for f in main.firms.find({"status": {"$nin": ["silindi", "askida"]}}, {"_id": 0, "db": 1, "expires_at": 1}):
        try:
            if firms_mod.expired(f):
                continue
            tok = tenant.set_firm(f["db"])
            try:
                total += await pull_all(db)
            finally:
                tenant.reset(tok)
        except Exception as e:                                     # noqa: BLE001
            log.warning("firma çekimi: %s", e)
        await asyncio.sleep(0)
    return total


async def auto_loop(db, firms_mod, tenant, first_delay=150):
    await asyncio.sleep(first_delay)
    while True:
        try:
            await run_cycle(db, firms_mod, tenant)
        except asyncio.CancelledError:
            raise
        except Exception as e:                                     # noqa: BLE001
            log.warning("pazaryeri döngüsü: %s", e)
        await asyncio.sleep(INTERVAL)


# =================================================================== uçlar
YEMEK_DURUM = {"kabul": ("onaylandi", "accepted"), "hazirlaniyor": ("hazirlaniyor", "preparing"), "hazir": ("hazirlaniyor", "ready"),
               "yolda": ("kargoda", "dispatched"), "teslim": ("teslim_edildi", "delivered"), "iptal": ("iptal", "cancelled")}


def register(api_router, db, deps):
    adm = Depends(deps["require_admin"])

    @api_router.post("/public/yemek/{mk}")
    async def yemek_webhook(mk: str, request: Request):
        """Yemeksepeti gibi siparişi kendisi gönderen platformlar için. Adres: /api/public/<firma_no>~yemek/<platform>?k=<anahtar>"""
        if mk not in FOOD:
            raise HTTPException(status_code=404, detail="Bilinmeyen platform")
        c = await shop_sync.market_cfg(db, mk)
        key = c.get("webhook_key") or ""
        got = request.query_params.get("k") or request.headers.get("x-webhook-key") or request.headers.get("authorization", "").replace("Bearer ", "").replace("Basic ", "")
        if not key or got != key:
            raise HTTPException(status_code=401, detail="Anahtar hatalı")
        try:
            body = await request.json()
        except Exception:                                          # noqa: BLE001
            raise HTTPException(status_code=422, detail="Geçersiz sipariş verisi")
        rows = rows_of(body) if not (isinstance(body, dict) and (body.get("orderId") or body.get("id") or body.get("code"))) else [body]
        res = await ingest(db, mk, rows, datetime(2000, 1, 1, tzinfo=timezone.utc))
        await _set_state(db, mk, last=_now(), error="", imported=int(((await _state(db)).get(mk) or {}).get("imported") or 0))
        return {"ok": True, **res}

    @api_router.post("/admin/yemek/{mk}/siparis/{no}/durum")
    async def yemek_durum(mk: str, no: str, payload: dict, _: dict = adm):
        """Sipariş durumunu panelde günceller; ayarda status_url varsa platforma da bildirir (kabul, hazır, yolda, teslim, iptal)."""
        if mk not in FOOD:
            raise HTTPException(status_code=404, detail="Bilinmeyen platform")
        d = str(payload.get("durum") or "")
        if d not in YEMEK_DURUM:
            raise HTTPException(status_code=422, detail="Durum: " + ", ".join(YEMEK_DURUM))
        loc, remote = YEMEK_DURUM[d]
        o = await db.shop_orders.find_one({"order_no": no, "source": mk}, {"_id": 0, "id": 1})
        if not o:
            raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
        await db.shop_orders.update_one({"id": o["id"]}, {"$set": {"status": loc, "updated_at": _now()},
                                                          "$push": {"history": {"status": loc, "at": _now(), "by": "panel"}}})
        ext = no.split("-", 1)[-1]
        yst = "teslim" if loc == "teslim_edildi" else loc
        await db.yp_orders.update_one({"channel": mk, "market_no": ext}, {"$set": {"status": yst},
                                      "$push": {"timeline": {"at": _now(), "by": "panel", "state": yst, "note": "durum: " + d}}})
        c = await shop_sync.market_cfg(db, mk)
        url, sent = c.get("status_url") or "", None
        if url:
            try:
                code, data = await shop_sync.http("POST", url.replace("{id}", ext), await headers(mk, c), {"orderId": ext, "status": remote})
                sent = {"ok": code < 300, "status": code}
            except Exception as e:                                 # noqa: BLE001
                sent = {"ok": False, "message": str(e)[:160]}
        return {"ok": True, "status": loc, "platform": sent}

    @api_router.get("/admin/market/status")
    async def status(_: dict = adm):
        d = await db.app_settings.find_one({"_id": "sp_modules"}, {"_id": 0}) or {}
        cfgs, flags, st = d.get("config") or {}, d.get("flags") or {}, await _state(db)
        out = []
        for mk in ALL:
            c = cfgs.get(mk) or {}
            s = st.get(mk) or {}
            out.append({"id": mk, "name": _name(mk), "connected": connected(mk, c), "enabled": flags.get(mk) is not False and connected(mk, c),
                        "verified": VERIFIED[mk], "last": s.get("last") or "", "error": s.get("error") or "", "imported": int(s.get("imported") or 0), "since": s.get("since") or ""})
        return {"markets": out, "auto_every_min": max(1, INTERVAL // 60)}
