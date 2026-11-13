# -*- coding: utf-8 -*-
"""E-ticaret ek araçları (PRD adım 4-5):
  1) Akakçe / Cimri fiyat karşılaştırma XML beslemesi
  2) Buybox takibi ve otomatik fiyatlandırma (rakip fiyatı girilir ya da pazaryeri bağlantısından gelir)
  3) Sipariş risk puanı (sipariş anında hesaplanır, panelde görünür, riskliyse sahibe haber gider)
  4) Çarkıfelek (ziyaretçi telefonuyla bir kez çevirir, kazandığı kupon kampanya olarak açılır)
"""
import html as _h
import json
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.responses import Response

import kampanya

FEED_DEF = {"akakce": False, "cimri": False, "kargo": 0.0, "teslim_gun": 3, "sadece_stoklu": True}
BB_DEF = {"oto": False, "fark": 0.01}
RISK_DEF = {"on": True, "tutar_esik": 5000.0, "kapida_esik": 2000.0, "saat_adet": 3, "bildir": True, "orta": 30, "yuksek": 60}
CARK_DEF = {"on": False, "baslik": "Çarkı çevir, kupon kazan", "gecerlilik_gun": 7, "min_sepet": 0.0,
            "dilim": [{"ad": "%5 indirim", "tur": "yuzde", "deger": 5, "agirlik": 30},
                      {"ad": "%10 indirim", "tur": "yuzde", "deger": 10, "agirlik": 15},
                      {"ad": "Ücretsiz kargo", "tur": "kargo", "deger": 0, "agirlik": 15},
                      {"ad": "Bu sefer olmadı", "tur": "yok", "deger": 0, "agirlik": 30},
                      {"ad": "50 TL indirim", "tur": "tutar", "deger": 50, "agirlik": 5},
                      {"ad": "%15 indirim", "tur": "yuzde", "deger": 15, "agirlik": 5}]}
TEK_KULLANIM = {"mailinator.com", "10minutemail.com", "guerrillamail.com", "tempmail.com", "yopmail.com", "trashmail.com", "sharklasers.com"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _num(v, d=0.0):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return d


async def _cfg(db, key, default):
    d = await db.app_settings.find_one({"_id": key}, {"_id": 0}) or {}
    return dict(default, **{k: v for k, v in d.items() if k in default})


# ------------------------------------------------------------------ 1) XML besleme
def _x(v):
    return _h.escape(str(v if v is not None else ""), quote=False)


def feed_xml(urls, tur, rows, base, c):
    """tur: akakce | cimri. rows: mağaza ürünleri."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<Products>"]
    for p in rows:
        slug = p.get("slug") or p.get("id")
        img = (p.get("images") or [""])[0]
        if img.startswith("/"):
            img = base + img
        link = "%s/magaza/urun/%s" % (base, slug)
        stok = (not p.get("track_stock", True)) or p.get("stock", 0) > 0
        if c["sadece_stoklu"] and not stok:
            continue
        price = "%.2f" % _num(p.get("price"))
        if tur == "akakce":
            out.append("<Product><ProductId>%s</ProductId><ProductName>%s</ProductName><ProductUrl>%s</ProductUrl><Price>%s</Price>"
                       "<Category>%s</Category><Brand>%s</Brand><Stock>%s</Stock><ImageUrl>%s</ImageUrl><Gtin>%s</Gtin>"
                       "<ShippingCost>%.2f</ShippingCost><DeliveryTime>%s</DeliveryTime></Product>" % (
                           _x(p["id"]), _x(p.get("name")), _x(link), price, _x(p.get("category")), _x(p.get("brand")),
                           p.get("stock", 0) if p.get("track_stock", True) else 999, _x(img), _x(p.get("gtin")), c["kargo"], c["teslim_gun"]))
        else:
            out.append("<Product><ProductId>%s</ProductId><ProductName>%s</ProductName><ProductUrl>%s</ProductUrl><Price>%s</Price>"
                       "<Category>%s</Category><Brand>%s</Brand><Stock>%s</Stock><Image1>%s</Image1><Barcode>%s</Barcode>"
                       "<ShippingPrice>%.2f</ShippingPrice><DeliveryDay>%s</DeliveryDay></Product>" % (
                           _x(p["id"]), _x(p.get("name")), _x(link), price, _x(p.get("category")), _x(p.get("brand")),
                           "Var" if stok else "Yok", _x(img), _x(p.get("gtin")), c["kargo"], c["teslim_gun"]))
    out.append("</Products>")
    return "\n".join(out)


# ------------------------------------------------------------------ 3) Sipariş risk puanı
async def risk_hesapla(db, order, cfg=None):
    """Sipariş sözlüğünden {puan, seviye, nedenler} üretir. Siparişi kaydetmez."""
    c = cfg or await _cfg(db, "yp_risk", RISK_DEF)
    if not c["on"]:
        return None
    cu, total, pm = order.get("customer") or {}, _num(order.get("total")), (order.get("payment") or {}).get("method", "")
    pk, nedenler, puan = order.get("phone_key") or "", [], 0

    def ekle(n, p):
        nonlocal puan
        puan += p
        nedenler.append(n)
    if c["tutar_esik"] and total >= c["tutar_esik"]:
        ekle("Yüksek sipariş tutarı", 20)
    if pm in ("kapida", "kapida_nakit", "kapida_kart") and c["kapida_esik"] and total >= c["kapida_esik"]:
        ekle("Yüksek tutarlı kapıda ödeme", 15)
    if len(str(cu.get("address", "")).strip()) < 15:
        ekle("Adres çok kısa", 10)
    dom = str(cu.get("email", "")).split("@")[-1].lower()
    if dom in TEK_KULLANIM:
        ekle("Tek kullanımlık e-posta", 15)
    if pk:
        onceki = await db.shop_orders.count_documents({"phone_key": pk})
        if not onceki:
            ekle("İlk sipariş", 10)
        saat = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        if await db.shop_orders.count_documents({"phone_key": pk, "created_at": {"$gte": saat}}) >= max(1, int(c["saat_adet"])):
            ekle("Aynı telefondan 1 saatte çok sipariş", 30)
        if await db.shop_orders.count_documents({"phone_key": pk, "status": "iptal"}) >= 2:
            ekle("Geçmişte birden fazla iptal", 25)
    adr = str(cu.get("address", "")).strip()
    if len(adr) >= 15:
        hafta = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        fark = {x for x in [o.get("phone_key") async for o in db.shop_orders.find({"customer.address": adr, "created_at": {"$gte": hafta}}, {"phone_key": 1})] if x and x != pk}
        if len(fark) >= 2:
            ekle("Aynı adrese farklı telefonlarla sipariş", 25)
    puan = min(100, puan)
    seviye = "yuksek" if puan >= c["yuksek"] else ("orta" if puan >= c["orta"] else "dusuk")
    return {"puan": puan, "seviye": seviye, "nedenler": nedenler, "bildir": bool(c["bildir"])}


# ------------------------------------------------------------------ 2) Buybox
def buybox_hedef(p, fark):
    """Ürün için yeni fiyat; değişim yoksa None. bb: {on, rakip, min, max}"""
    bb = p.get("bb") or {}
    rakip = _num(bb.get("rakip"))
    if not (bb.get("on") and rakip > 0):
        return None
    hedef = round(rakip - fark, 2)
    if bb.get("min") and hedef < _num(bb["min"]):
        hedef = _num(bb["min"])
    if bb.get("max") and hedef > _num(bb["max"]):
        hedef = _num(bb["max"])
    hedef = round(hedef, 2)
    return hedef if hedef > 0 and abs(hedef - _num(p.get("price"))) >= 0.005 else None


async def buybox_uygula(db, sadece_oto=False):
    c = await _cfg(db, "yp_buybox", BB_DEF)
    if sadece_oto and not c["oto"]:
        return []
    degisen = []
    async for p in db.shop_products.find({"bb.on": True}, {"_id": 0}):
        h = buybox_hedef(p, _num(c["fark"]))
        if h is None:
            continue
        await db.shop_products.update_one({"id": p["id"]}, {"$set": {"price": h, "updated_at": _now()}})
        await db.yp_buybox_log.insert_one({"pid": p["id"], "ad": p.get("name"), "eski": p.get("price"), "yeni": h, "rakip": (p.get("bb") or {}).get("rakip"), "at": _now()})
        degisen.append({"id": p["id"], "ad": p.get("name"), "eski": p.get("price"), "yeni": h})
    if degisen:
        try:
            import shop_sync
            await shop_sync._enqueue(db, [d["id"] for d in degisen])
        except Exception:      # noqa: BLE001
            pass
    return degisen


# ------------------------------------------------------------------ 4) Çarkıfelek
def cark_temiz(d):
    out = []
    for x in (d or [])[:12]:
        tur = x.get("tur") if x.get("tur") in ("yuzde", "tutar", "kargo", "yok") else "yok"
        ad = str(x.get("ad", "")).strip()[:30]
        if ad:
            out.append({"ad": ad, "tur": tur, "deger": max(0.0, _num(x.get("deger"))), "agirlik": max(0, min(1000, int(_num(x.get("agirlik"), 1))))})
    return out


def cark_html(c):
    """Sayfaya eklenen yüzen düğme + pencere. Kapalıysa boş."""
    if not (c["on"] and len(c["dilim"]) >= 2):
        return ""
    ad = json.dumps([d["ad"] for d in c["dilim"]], ensure_ascii=False).replace("</", "<\\/")
    css = ("<style>#okck{position:fixed;left:14px;bottom:18px;z-index:9400;background:#f27a1a;color:#fff;border:0;border-radius:999px;min-height:46px;padding:0 18px;font:700 14px system-ui;cursor:pointer;box-shadow:0 6px 18px #0004}"
           "#okckm{position:fixed;inset:0;z-index:9700;background:#0a1f44d9;display:none;place-items:center;padding:16px}#okckm.on{display:grid}"
           "#okckm .b{background:#fff;color:#0a1f44;border-radius:18px;padding:22px;max-width:380px;width:100%;text-align:center;font:15px system-ui}"
           "#okckm h3{margin:0 0 10px;font:800 20px system-ui}#okckm input{width:100%;box-sizing:border-box;min-height:46px;border:1px solid #c9d2e0;border-radius:10px;padding:0 12px;font-size:16px;margin:8px 0}"
           "#okckm .go{width:100%;min-height:46px;border:0;border-radius:10px;background:#0a1f44;color:#fff;font:700 15px system-ui;cursor:pointer}#okckm .x{float:right;background:none;border:0;font-size:24px;min-width:44px;min-height:44px;cursor:pointer}"
           "#okckw{width:240px;height:240px;margin:6px auto;transition:transform 4.2s cubic-bezier(.12,.7,.1,1)}@media(prefers-reduced-motion:reduce){#okckw{transition:none}}"
           "#okckr{margin-top:8px;font-weight:700;min-height:22px}</style>")
    js = ("<script>(function(){var D=%s,N=D.length,ac=document.getElementById('okckm'),W=document.getElementById('okckw'),R=document.getElementById('okckr'),Pn=document.getElementById('okckp');"
          "var C=['#0a1f44','#f27a1a'],s='<svg viewBox=\"-120 -120 240 240\" width=\"240\" height=\"240\">',a=2*Math.PI/N,i;"
          "for(i=0;i<N;i++){var x1=110*Math.sin(a*i),y1=-110*Math.cos(a*i),x2=110*Math.sin(a*(i+1)),y2=-110*Math.cos(a*(i+1)),m=a*(i+.5)*180/Math.PI;"
          "s+='<path d=\"M0 0L'+x1+' '+y1+'A110 110 0 0 1 '+x2+' '+y2+'Z\" fill=\"'+C[i%%2]+'\" stroke=\"#fff\" stroke-width=\"2\"/><text transform=\"rotate('+(m-90)+') translate(26 3)\" fill=\"#fff\" font-size=\"10\" font-family=\"system-ui\" font-weight=\"700\">'+(D[i].length>15?D[i].slice(0,14)+'…':D[i]).replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</text>'}"
          "W.innerHTML=s+'</svg>';var rot=0;"
          "document.getElementById('okck').onclick=function(){ac.classList.add('on')};ac.querySelector('.x').onclick=function(){ac.classList.remove('on')};"
          "ac.querySelector('.go').onclick=function(){var b=this;b.disabled=true;R.textContent='';fetch('/api/public/cark/cevir',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:Pn.value})}).then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error(j.detail||'Hata');return j})})"
          ".then(function(j){var hedef=360-(a*(j.index+.5)*180/Math.PI);rot+=1440+((hedef-rot%%360)+360)%%360;W.style.transform='rotate('+rot+'deg)';setTimeout(function(){R.textContent=j.kod?('Kazandınız: '+j.ad+' — Kupon kodunuz: '+j.kod):(j.ad+'. Tekrar bekleriz!');b.disabled=false},4300)})"
          ".catch(function(e){R.textContent=e.message;b.disabled=false})}})()</script>") % ad
    kutu = ('<div id="okckm" role="dialog" aria-modal="true" aria-label="Çarkıfelek"><div class="b"><button class="x" aria-label="Kapat">×</button><h3>%s</h3>'
            '<div style="position:relative"><div style="position:absolute;left:50%%;top:-2px;transform:translateX(-50%%);z-index:2;width:0;height:0;border-left:11px solid transparent;border-right:11px solid transparent;border-top:20px solid #f27a1a"></div><div id="okckw"></div></div><input id="okckp" type="tel" inputmode="tel" autocomplete="tel" placeholder="Telefon numaranız" aria-label="Telefon numaranız">'
            '<button class="go">Çevir</button><div id="okckr" aria-live="polite"></div></div></div>' % _h.escape(c["baslik"]))
    return css + '<button id="okck" type="button">Çarkı çevir</button>' + kutu + js


async def webhook_gonder(db, olay, veri):
    """Bağlı 'Webhook / API' entegrasyonuna olayı imzalı JSON olarak yollar. Hata siparişi/randevuyu etkilemez."""
    try:
        row = await db.yp_integrations.find_one({"id": "webhook", "on": True}, {"_id": 0})
        k = (row or {}).get("keys") or {}
        url = str(k.get("url") or "")
        if not url.startswith(("https://", "http://")):
            return False
        import asyncio
        import hashlib
        import hmac
        gov = json.dumps({"olay": olay, "veri": veri, "zaman": _now()}, ensure_ascii=False, default=str).encode()
        h = {"Content-Type": "application/json; charset=utf-8", "X-OnlineKaydet-Olay": olay}
        if k.get("secret"):
            h["X-OnlineKaydet-Imza"] = hmac.new(str(k["secret"]).encode(), gov, hashlib.sha256).hexdigest()

        def _post():
            import requests
            return requests.post(url, data=gov, headers=h, timeout=5).status_code
        return 200 <= await asyncio.to_thread(_post) < 300
    except Exception:      # noqa: BLE001
        return False


async def haberver_tara(db, host=""):
    """Stok geldi / fiyat düştü talepleri için SMS yollar; her talep bir kez işlenir. Giden sayısını döner."""
    import notify
    n = 0
    async for a in db.shop_alerts.find({"sent": ""}, {"_id": 0}).limit(200):
        p = await db.shop_products.find_one({"id": a["pid"], "active": True}, {"_id": 0, "name": 1, "price": 1, "stock": 1, "slug": 1, "track_stock": 1})
        if not p:
            continue
        stokta = (not p.get("track_stock", True)) or p.get("stock", 0) > 0
        if a["tur"] == "stok" and not stokta:
            continue
        if a["tur"] == "fiyat" and not _num(p.get("price")) < _num(a.get("price_at")):
            continue
        link = ("https://%s" % host if host else "") + "/magaza/urun/" + str(p.get("slug") or a["pid"])
        metin = ("%s yeniden stokta! Hemen incele: %s" % (p["name"], link)) if a["tur"] == "stok" else \
                ("%s fiyatı düştü: %.2f TL (önceki %.2f TL). %s" % (p["name"], _num(p["price"]), _num(a["price_at"]), link))
        r = await notify.send(db, "sms", a["phone"], metin, kind="haber_ver", ref="alert:" + a["id"])
        if (r or {}).get("status") == "sent":
            await db.shop_alerts.update_one({"id": a["id"]}, {"$set": {"sent": _now()}})
            n += 1
    return n


SEPET_DEF = {"oto": False, "bekleme_dk": 120, "metin": "Merhaba {ad}, sepetinizde ürünler sizi bekliyor. Tamamlamak için: {link}"}


def sepet_durum(c, now=None):
    now = now or datetime.now(timezone.utc)
    try:
        t = datetime.fromisoformat(c["updated_at"])
    except Exception:      # noqa: BLE001
        return "aktif"
    return "terk" if (now - t) >= timedelta(minutes=60) else "aktif"


async def sepet_hatirla(db, c, host, metin):
    """Sepet sahibine SMS gider; aynı sepete ikinci kez gitmez."""
    import notify
    ad = (c.get("name") or "").split(" ")[0] or "değerli müşterimiz"
    link = "https://%s/magaza" % host if host else "/magaza"
    r = await notify.send(db, "sms", c.get("phone", ""), metin.replace("{ad}", ad).replace("{link}", link), kind="sepet_hatirlat", ref="sepet:" + c["id"])
    if (r or {}).get("status") == "sent":
        await db.shop_carts.update_one({"id": c["id"]}, {"$set": {"hatirlatildi": _now()}})
    return r


def register(api_router, db, deps):
    adm = deps["require_admin"]
    secret, alg = deps.get("JWT_SECRET"), deps.get("JWT_ALGORITHM", "HS256")

    # ---- XML besleme
    @api_router.get("/yp/feed")
    async def feed_get(request: Request, _: dict = Depends(adm)):
        c = await _cfg(db, "yp_feed", FEED_DEF)
        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
        base = "https://" + host
        return dict(c, urls={"akakce": base + "/api/public/feed/akakce.xml", "cimri": base + "/api/public/feed/cimri.xml"})

    @api_router.put("/yp/feed")
    async def feed_put(payload: dict, _: dict = Depends(adm)):
        c = await _cfg(db, "yp_feed", FEED_DEF)
        for k in ("akakce", "cimri", "sadece_stoklu"):
            if k in payload:
                c[k] = bool(payload[k])
        if "kargo" in payload:
            c["kargo"] = max(0.0, _num(payload["kargo"]))
        if "teslim_gun" in payload:
            c["teslim_gun"] = max(0, min(30, int(_num(payload["teslim_gun"]))))
        await db.app_settings.update_one({"_id": "yp_feed"}, {"$set": c}, upsert=True)
        return c

    async def servis(tur, request):
        c = await _cfg(db, "yp_feed", FEED_DEF)
        if not c[tur]:
            raise HTTPException(404, "Bu besleme kapalı")
        rows = await db.shop_products.find({"active": True}, {"_id": 0}).to_list(5000)
        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
        return Response(feed_xml(None, tur, rows, "https://" + host, c), media_type="application/xml; charset=utf-8")

    @api_router.get("/public/feed/akakce.xml")
    async def feed_akakce(request: Request):
        return await servis("akakce", request)

    @api_router.get("/public/feed/cimri.xml")
    async def feed_cimri(request: Request):
        return await servis("cimri", request)

    # ---- Buybox
    @api_router.get("/yp/buybox")
    async def bb_list(_: dict = Depends(adm)):
        c = await _cfg(db, "yp_buybox", BB_DEF)
        rows = []
        async for p in db.shop_products.find({}, {"_id": 0, "id": 1, "name": 1, "price": 1, "bb": 1, "brand": 1}).sort("name", 1):
            bb = p.get("bb") or {}
            rows.append({"id": p["id"], "ad": p.get("name"), "fiyat": p.get("price"), "on": bool(bb.get("on")), "rakip": bb.get("rakip") or 0,
                         "min": bb.get("min") or 0, "max": bb.get("max") or 0, "hedef": buybox_hedef(p, _num(c["fark"]))})
        log = await db.yp_buybox_log.find({}, {"_id": 0}).sort("at", -1).to_list(15)
        return {"cfg": c, "rows": rows, "log": log}

    @api_router.put("/yp/buybox")
    async def bb_cfg(payload: dict, _: dict = Depends(adm)):
        c = await _cfg(db, "yp_buybox", BB_DEF)
        if "oto" in payload:
            c["oto"] = bool(payload["oto"])
        if "fark" in payload:
            c["fark"] = max(0.0, _num(payload["fark"]))
        await db.app_settings.update_one({"_id": "yp_buybox"}, {"$set": c}, upsert=True)
        return c

    @api_router.put("/yp/buybox/{pid}")
    async def bb_put(pid: str, payload: dict, _: dict = Depends(adm)):
        p = await db.shop_products.find_one({"id": pid}, {"_id": 0, "bb": 1})
        if p is None:
            raise HTTPException(404, "Ürün bulunamadı")
        bb = dict(p.get("bb") or {})
        if "on" in payload:
            bb["on"] = bool(payload["on"])
        for k in ("rakip", "min", "max"):
            if k in payload:
                bb[k] = max(0.0, _num(payload[k]))
        if bb.get("min") and bb.get("max") and bb["min"] > bb["max"]:
            raise HTTPException(422, "En düşük fiyat, en yüksek fiyattan büyük olamaz")
        await db.shop_products.update_one({"id": pid}, {"$set": {"bb": bb}})
        return bb

    @api_router.post("/yp/buybox/uygula")
    async def bb_run(_: dict = Depends(adm)):
        return {"degisen": await buybox_uygula(db)}

    try:
        import governance

        async def _hook(d):
            try:
                await buybox_uygula(d, sadece_oto=True)
            except Exception:      # noqa: BLE001
                pass
        governance.HOOKS.append(_hook)
    except Exception:      # noqa: BLE001
        pass

    # ---- Risk
    @api_router.get("/yp/risk")
    async def risk_get(_: dict = Depends(adm)):
        return await _cfg(db, "yp_risk", RISK_DEF)

    @api_router.put("/yp/risk")
    async def risk_put(payload: dict, _: dict = Depends(adm)):
        c = await _cfg(db, "yp_risk", RISK_DEF)
        for k in ("on", "bildir"):
            if k in payload:
                c[k] = bool(payload[k])
        for k in ("tutar_esik", "kapida_esik"):
            if k in payload:
                c[k] = max(0.0, _num(payload[k]))
        for k in ("saat_adet", "orta", "yuksek"):
            if k in payload:
                c[k] = max(1, min(100, int(_num(payload[k], 1))))
        await db.app_settings.update_one({"_id": "yp_risk"}, {"$set": c}, upsert=True)
        return c

    # ---- Çarkıfelek
    @api_router.get("/yp/cark")
    async def cark_get(_: dict = Depends(adm)):
        c = await _cfg(db, "yp_cark", CARK_DEF)
        return dict(c, cevrilen=await db.yp_cark_log.count_documents({}), kazanan=await db.yp_cark_log.count_documents({"kod": {"$ne": ""}}))

    @api_router.put("/yp/cark")
    async def cark_put(payload: dict, _: dict = Depends(adm)):
        c = await _cfg(db, "yp_cark", CARK_DEF)
        if "on" in payload:
            c["on"] = bool(payload["on"])
        if "baslik" in payload:
            c["baslik"] = str(payload["baslik"]).strip()[:60] or CARK_DEF["baslik"]
        if "gecerlilik_gun" in payload:
            c["gecerlilik_gun"] = max(1, min(90, int(_num(payload["gecerlilik_gun"], 7))))
        if "min_sepet" in payload:
            c["min_sepet"] = max(0.0, _num(payload["min_sepet"]))
        if "dilim" in payload:
            d = cark_temiz(payload["dilim"])
            if len(d) < 2:
                raise HTTPException(422, "En az 2 dilim gerekli")
            if not any(x["agirlik"] > 0 for x in d):
                raise HTTPException(422, "En az bir dilimin ağırlığı sıfırdan büyük olmalı")
            c["dilim"] = d
        await db.app_settings.update_one({"_id": "yp_cark"}, {"$set": c}, upsert=True)
        return c

    @api_router.post("/public/cark/cevir")
    async def cark_cevir(payload: dict, request: Request):
        c = await _cfg(db, "yp_cark", CARK_DEF)
        if not c["on"]:
            raise HTTPException(404, "Çarkıfelek şu an kapalı")
        ph = re.sub(r"\D", "", str(payload.get("phone", "")))[-10:]
        if len(ph) != 10 or not ph.startswith("5"):
            raise HTTPException(422, "Lütfen geçerli bir cep telefonu numarası girin (5xx xxx xx xx)")
        ilk = await db.yp_cark_log.insert_one({"phone": ph, "at": _now(), "kod": ""}) if not await db.yp_cark_log.find_one({"phone": ph}) else None
        if ilk is None:
            raise HTTPException(409, "Bu telefon numarasıyla çarkı daha önce çevirdiniz.")
        d = c["dilim"]
        top = sum(x["agirlik"] for x in d)
        r, acc, idx = secrets.randbelow(max(1, top)), 0, 0
        for i, x in enumerate(d):
            acc += x["agirlik"]
            if r < acc:
                idx = i
                break
        x = d[idx]
        kod = ""
        if x["tur"] != "yok":
            kod = "CARK-" + secrets.token_hex(3).upper()
            bitis = (datetime.now(timezone.utc) + timedelta(days=int(c["gecerlilik_gun"]))).date().isoformat()
            gain = {"percent": x["deger"]} if x["tur"] == "yuzde" else ({"amount": x["deger"]} if x["tur"] == "tutar" else {"free_ship": True})
            camp = kampanya.clean({"name": "Çarkıfelek " + kod, "type": "kupon", "on": True, "end": bitis, "label": "Çarkıfelek",
                                   "cond": {"code": kod, "max_use": 1, "min_total": c["min_sepet"]}, "gain": gain, "limit": {"total": 1}})
            await db.yp_camps.insert_one(dict(camp))
            await db.yp_cark_log.update_one({"phone": ph}, {"$set": {"kod": kod, "dilim": x["ad"]}})
        else:
            await db.yp_cark_log.update_one({"phone": ph}, {"$set": {"dilim": x["ad"]}})
        return {"index": idx, "ad": x["ad"], "kod": kod}

    # ---- Aktif / terk edilmiş sepetler
    async def musteri(request: Request):
        import jwt
        h = request.headers.get("authorization", "")
        try:
            pl = jwt.decode(h[7:], secret, algorithms=[alg]) if h.lower().startswith("bearer ") else {}
        except Exception:      # noqa: BLE001
            pl = {}
        acc = await db.customer_accounts.find_one({"id": pl.get("sub")}, {"_id": 0}) if pl.get("typ") == "customer" else None
        if not acc:
            raise HTTPException(401, "Giriş yapmanız gerekiyor")
        return acc

    @api_router.put("/public/shop/sepet")
    async def sepet_kaydet(payload: dict, request: Request):
        a = await musteri(request)
        items, top = [], 0.0
        for it in (payload.get("items") or [])[:30]:
            p = await db.shop_products.find_one({"id": it.get("id") or it.get("product_id"), "active": True}, {"_id": 0, "id": 1, "name": 1, "price": 1, "images": 1})
            if not p:
                continue
            q = max(1, min(int(_num(it.get("q") or it.get("qty"), 1)), 20))
            items.append({"id": p["id"], "name": p["name"], "price": p["price"], "q": q})
            top += p["price"] * q
        if not items:
            await db.shop_carts.delete_one({"account_id": a["id"]})
            return {"ok": True, "n": 0}
        cur = await db.shop_carts.find_one({"account_id": a["id"]}, {"_id": 0, "id": 1, "hatirlatildi": 1}) or {}
        await db.shop_carts.update_one({"account_id": a["id"]}, {"$set": {
            "id": cur.get("id") or secrets.token_hex(8), "account_id": a["id"], "name": a.get("name", ""), "phone": a.get("phone", ""), "items": items,
            "total": round(top, 2), "updated_at": _now(), "hatirlatildi": cur.get("hatirlatildi", "")}}, upsert=True)
        return {"ok": True, "n": len(items)}

    @api_router.get("/yp/sepetler")
    async def sepet_liste(_: dict = Depends(adm)):
        c = await _cfg(db, "yp_sepet", SEPET_DEF)
        rows = await db.shop_carts.find({}, {"_id": 0}).sort("updated_at", -1).to_list(500)
        for r in rows:
            r["durum"] = sepet_durum(r)
        return {"cfg": c, "rows": rows, "ozet": {"aktif": sum(1 for r in rows if r["durum"] == "aktif"), "terk": sum(1 for r in rows if r["durum"] == "terk"),
                                                 "tutar": round(sum(r["total"] for r in rows if r["durum"] == "terk"), 2)}}

    @api_router.put("/yp/sepetler")
    async def sepet_cfg(payload: dict, _: dict = Depends(adm)):
        c = await _cfg(db, "yp_sepet", SEPET_DEF)
        if "oto" in payload:
            c["oto"] = bool(payload["oto"])
        if "bekleme_dk" in payload:
            c["bekleme_dk"] = max(60, min(2880, int(_num(payload["bekleme_dk"], 120))))
        if "metin" in payload and str(payload["metin"]).strip():
            c["metin"] = str(payload["metin"]).strip()[:300]
        await db.app_settings.update_one({"_id": "yp_sepet"}, {"$set": c}, upsert=True)
        return c

    @api_router.post("/yp/sepetler/{cid}/hatirla")
    async def sepet_hatirla_api(cid: str, request: Request, _: dict = Depends(adm)):
        c = await db.shop_carts.find_one({"id": cid}, {"_id": 0})
        if not c:
            raise HTTPException(404, "Sepet bulunamadı")
        if not c.get("phone"):
            raise HTTPException(422, "Bu müşterinin telefonu yok")
        cfg = await _cfg(db, "yp_sepet", SEPET_DEF)
        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
        r = await sepet_hatirla(db, c, host, cfg["metin"])
        if (r or {}).get("status") != "sent":
            raise HTTPException(422, "SMS gönderilemedi. SMS bağlantınızı kontrol edin.")
        return {"ok": True}

    try:
        import governance

        async def _sepet_hook(d):
            try:
                cfg = await _cfg(d, "yp_sepet", SEPET_DEF)
                if not cfg["oto"]:
                    return
                esik = (datetime.now(timezone.utc) - timedelta(minutes=int(cfg["bekleme_dk"]))).isoformat()
                async for c in d.shop_carts.find({"updated_at": {"$lte": esik}, "hatirlatildi": {"$in": ["", None]}}, {"_id": 0}).limit(50):
                    if c.get("phone"):
                        await sepet_hatirla(d, c, "", cfg["metin"])
            except Exception:      # noqa: BLE001
                pass
        governance.HOOKS.append(_sepet_hook)
    except Exception:      # noqa: BLE001
        pass

    # ---- Stoğa gelince / fiyat düşünce haber ver
    @api_router.post("/public/shop/haberver")
    async def haber_ekle(payload: dict):
        ph = re.sub(r"\D", "", str(payload.get("phone", "")))[-10:]
        if len(ph) != 10 or not ph.startswith("5"):
            raise HTTPException(422, "Lütfen geçerli bir cep telefonu numarası girin (5xx xxx xx xx)")
        tur = "fiyat" if payload.get("tur") == "fiyat" else "stok"
        p = await db.shop_products.find_one({"id": str(payload.get("product_id", "")), "active": True}, {"_id": 0, "id": 1, "price": 1, "stock": 1, "track_stock": 1})
        if not p:
            raise HTTPException(404, "Ürün bulunamadı")
        if tur == "stok" and ((not p.get("track_stock", True)) or p.get("stock", 0) > 0):
            raise HTTPException(409, "Bu ürün zaten stokta")
        if await db.shop_alerts.find_one({"pid": p["id"], "phone": ph, "tur": tur, "sent": ""}):
            return {"ok": True, "tekrar": True}
        if await db.shop_alerts.count_documents({"phone": ph, "sent": ""}) >= 10:
            raise HTTPException(429, "Bu numara için çok fazla bekleyen talep var")
        await db.shop_alerts.insert_one({"id": secrets.token_hex(8), "pid": p["id"], "phone": ph, "tur": tur, "price_at": p.get("price"), "sent": "", "at": _now()})
        return {"ok": True}

    @api_router.get("/yp/haberver")
    async def haber_liste(_: dict = Depends(adm)):
        sat = {}
        async for a in db.shop_alerts.find({}, {"_id": 0}):
            k = (a["pid"], a["tur"])
            sat.setdefault(k, {"pid": a["pid"], "tur": a["tur"], "bekleyen": 0, "giden": 0})
            sat[k]["giden" if a["sent"] else "bekleyen"] += 1
        for v in sat.values():
            p = await db.shop_products.find_one({"id": v["pid"]}, {"_id": 0, "name": 1})
            v["ad"] = (p or {}).get("name", "(silinmiş ürün)")
        return {"rows": sorted(sat.values(), key=lambda r: -r["bekleyen"])}

    @api_router.post("/yp/haberver/tara")
    async def haber_tara(request: Request, _: dict = Depends(adm)):
        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
        return {"gonderilen": await haberver_tara(db, host)}

    try:
        import governance

        async def _haber_hook(d):
            try:
                await haberver_tara(d)
            except Exception:      # noqa: BLE001
                pass
        governance.HOOKS.append(_haber_hook)
    except Exception:      # noqa: BLE001
        pass
