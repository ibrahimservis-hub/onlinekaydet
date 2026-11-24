# -*- coding: utf-8 -*-
"""Meta (Facebook / Instagram) tarafı: sunucu taraflı Conversions API ve ürün kataloğu akışı.

1) Conversions API: sipariş oluşunca `Purchase` olayı sunucudan Meta'ya gider. Tarayıcıdaki pixel aynı olayı
   aynı `event_id` (sipariş numarası) ile gönderdiği için Meta ikisini tek sayar; reklam engelleyici ya da
   çerez reddi olan ziyaretçilerin siparişleri de ölçülür. Ziyaretçi pazarlama çerezini reddettiyse olay
   gönderilmez. E-posta ve telefon SHA-256 ile özetlenerek gider, düz hâliyle hiçbir yere yazılmaz.
2) Katalog akışı: /api/public/feed/meta.xml — Meta Commerce Manager'da "Zamanlanmış akış" olarak eklenir.
   Ürün, varyant, indirimli fiyat, stok ve görseller dahildir; yalnız `facebook_catalog` açıkken yayınlanır.
"""
import asyncio
import hashlib
import html as _h
import re
import time
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.responses import Response

GRAPH = "https://graph.facebook.com/v21.0"


def _istek(yontem, url, **kw):
    """Ağ çağrısı. Testler bu işlevi değiştirir."""
    import requests
    kw.setdefault("timeout", 10)
    return requests.request(yontem, url, **kw)


def _sha(v):
    v = str(v or "").strip().lower()
    return hashlib.sha256(v.encode("utf-8")).hexdigest() if v else ""


def tel_norm(p):
    d = re.sub(r"\D", "", str(p or ""))
    if d.startswith("00"):
        d = d[2:]
    if d.startswith("0"):
        d = "90" + d[1:]
    elif len(d) == 10:
        d = "90" + d
    return d


def ad_ayir(ad):
    p = str(ad or "").strip().split()
    if not p:
        return "", ""
    return p[0], (p[-1] if len(p) > 1 else "")


async def ayar(db):
    """Pixel kimliği ve API anahtarı; ikisi de varsa ve entegrasyon açıksa."""
    r = await db.yp_integrations.find_one({"id": "meta_pixel", "on": True}, {"_id": 0, "keys": 1}) or {}
    k = r.get("keys") or {}
    pid, tok = str(k.get("id") or "").strip(), str(k.get("token") or "").strip()
    if not (pid.isdigit() and tok):
        return None
    return {"pixel": pid, "token": tok, "test": str(k.get("test_code") or "").strip()}


def olay_kur(order, mk, ip, ua, host=""):
    """Purchase olayı gövdesi (Meta Conversions API biçimi)."""
    cu = order.get("customer") or {}
    fn, ln = ad_ayir(cu.get("name"))
    ud = {"client_ip_address": ip or "", "client_user_agent": ua or ""}
    for k, v in (("em", _sha(cu.get("email"))), ("ph", _sha(tel_norm(cu.get("phone")))), ("fn", _sha(fn)), ("ln", _sha(ln)),
                 ("ct", _sha(re.sub(r"\s", "", str(cu.get("city") or "")))), ("country", _sha("tr")),
                 ("external_id", _sha(order.get("account_id") or order.get("phone_key")))):
        if v:
            ud[k] = [v]
    if mk.get("fbp"):
        ud["fbp"] = str(mk["fbp"])[:120]
    if mk.get("fbc"):
        ud["fbc"] = str(mk["fbc"])[:200]
    items = order.get("items") or []
    url = str(mk.get("url") or "")[:500] or ("https://%s/magaza" % host if host else "")
    return {
        "event_name": "Purchase", "event_time": int(time.time()), "event_id": str(order.get("order_no")),
        "action_source": "website", "event_source_url": url, "user_data": ud,
        "custom_data": {"currency": "TRY", "value": round(float(order.get("total") or 0), 2), "order_id": str(order.get("order_no")),
                        "content_type": "product", "content_ids": [str(i.get("product_id") or i.get("id") or "") for i in items],
                        "contents": [{"id": str(i.get("product_id") or i.get("id") or ""), "quantity": int(i.get("qty") or 1),
                                      "item_price": round(float(i.get("price") or 0), 2)} for i in items],
                        "num_items": sum(int(i.get("qty") or 1) for i in items)},
    }


def _gonder(cfg, olay):
    body = {"data": [olay], "access_token": cfg["token"]}
    if cfg.get("test"):
        body["test_event_code"] = cfg["test"]
    r = _istek("POST", "%s/%s/events" % (GRAPH, cfg["pixel"]), json=body)
    try:
        j = r.json()
    except Exception:                                              # noqa: BLE001
        j = {}
    if r.status_code >= 400:
        return False, ((j.get("error") or {}).get("message") or "kod %s" % r.status_code)[:200]
    return True, "%s olay alındı" % j.get("events_received", 1)


async def purchase(db, order, mk, ip, ua, host=""):
    """Siparişi Meta'ya bildirir. Hiçbir hata siparişi bozmaz; sonuç entegrasyon günlüğüne yazılır."""
    try:
        if not isinstance(mk, dict) or mk.get("pz") is False:
            return None                                            # pazarlama çerezi reddedildi
        cfg = await ayar(db)
        if not cfg:
            return None
        ok, msg = await asyncio.to_thread(_gonder, cfg, olay_kur(order, mk, ip, ua, host))
        await db.yp_int_log.insert_one({"id": "mc" + str(int(time.time() * 1000)), "int": "meta_pixel",
                                        "event": "capi purchase" if ok else "capi hata", "note": ("%s · %s" % (order.get("order_no"), msg))[:300],
                                        "at": datetime.now(timezone.utc).isoformat()})
        return ok
    except Exception:                                              # noqa: BLE001
        return None


# ------------------------------------------------------------------ katalog akışı
def _x(v):
    return _h.escape(str(v if v is not None else ""), quote=False)


def feed_xml(rows, base, firma, akis=None):
    items = []

    def madde(p, vid="", vlabel="", price=None, stock=None, img=None, group=""):
        slug = p.get("slug") or p["id"]
        fiyat = float(price if price is not None else p.get("price") or 0)
        eski = float(p.get("old_price") or 0)
        im = img or (p.get("images") or [""])[0]
        if im.startswith("/"):
            im = base + im
        extra = [("https:" + u if u.startswith("//") else (base + u if u.startswith("/") else u)) for u in (p.get("images") or [])[1:10]]
        var_dahil = p.get("track_stock", True)
        stok = (not var_dahil) or int(stock if stock is not None else p.get("stock", 0) or 0) > 0
        ad = p.get("name") or ""
        if vlabel:
            ad = "%s - %s" % (ad, vlabel)
        link = "%s/magaza/urun/%s" % (base, slug) + (("?v=" + vid) if vid else "")
        s = ["<item>", "<g:id>%s</g:id>" % _x(vid or p["id"]), "<g:title>%s</g:title>" % _x(ad[:150]),
             "<g:description>%s</g:description>" % _x(re.sub(r"<[^>]+>", " ", p.get("description") or p.get("short") or ad)[:5000]),
             "<g:link>%s</g:link>" % _x(link), "<g:availability>%s</g:availability>" % ("in stock" if stok else "out of stock"),
             "<g:condition>new</g:condition>"]
        if eski > fiyat > 0:
            s += ["<g:price>%.2f TRY</g:price>" % eski, "<g:sale_price>%.2f TRY</g:sale_price>" % fiyat]
        else:
            s.append("<g:price>%.2f TRY</g:price>" % fiyat)
        if im:
            s.append("<g:image_link>%s</g:image_link>" % _x(im))
        for u in extra:
            s.append("<g:additional_image_link>%s</g:additional_image_link>" % _x(u))
        s.append("<g:brand>%s</g:brand>" % _x(p.get("brand") or firma))
        _k = (akis or {}).get((p.get("category") or "").strip()) or {}
        if _k.get("yol") or p.get("category"):
            s.append("<g:product_type>%s</g:product_type>" % _x(_k.get("yol") or p["category"]))
        if _k.get("google"):
            s.append("<g:google_product_category>%s</g:google_product_category>" % _x(_k["google"]))
        if p.get("gtin"):
            s.append("<g:gtin>%s</g:gtin>" % _x(p["gtin"]))
        elif p.get("sku"):
            s.append("<g:mpn>%s</g:mpn>" % _x(p["sku"]))
        if group:
            s.append("<g:item_group_id>%s</g:item_group_id>" % _x(group))
        s.append("</item>")
        items.append("".join(s))

    for p in rows:
        vs = [v for v in (p.get("variants") or []) if v.get("active", True)]
        if vs:
            for v in vs:
                madde(p, vid=str(v["id"]), vlabel=v.get("label") or "", price=v.get("price") or p.get("price"), stock=v.get("stock"),
                      img=v.get("image") or None, group=p["id"])
        else:
            madde(p)
    return ('<?xml version="1.0" encoding="UTF-8"?><rss xmlns:g="http://base.google.com/ns/1.0" version="2.0"><channel>'
            "<title>%s</title><link>%s</link><description>%s ürünleri</description>%s</channel></rss>" % (_x(firma), _x(base), _x(firma), "".join(items)))


def register(api_router, db, deps):
    adm = deps["require_admin"]

    async def firma_adi():
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0, "company_name": 1}) or {}
        return g.get("company_name") or "Mağaza"

    @api_router.get("/public/feed/meta.xml")
    async def feed_meta(request: Request):
        r = await db.yp_integrations.find_one({"id": "facebook_catalog", "on": True}, {"_id": 1})
        if not r:
            raise HTTPException(404, "Bu besleme kapalı")
        rows = await db.shop_products.find({"active": True}, {"_id": 0}).to_list(5000)
        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
        import kategori
        return Response(feed_xml(rows, "https://" + host, await firma_adi(), await kategori.akis_haritasi(db)), media_type="application/xml; charset=utf-8")

    @api_router.get("/yp/meta")
    async def meta_durum(request: Request, _: dict = Depends(adm)):
        """Panelde gösterilecek akış adresi ve sunucu taraflı gönderim durumu."""
        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
        cat = await db.yp_integrations.find_one({"id": "facebook_catalog", "on": True}, {"_id": 1})
        cfg = await ayar(db)
        son = await db.yp_int_log.find({"int": "meta_pixel", "event": {"$in": ["capi purchase", "capi hata"]}}, {"_id": 0}).sort("at", -1).to_list(5)
        return {"feed_url": "https://%s/api/public/feed/meta.xml" % host, "feed_on": bool(cat), "capi_on": bool(cfg), "test_mode": bool(cfg and cfg["test"]), "son": son}
