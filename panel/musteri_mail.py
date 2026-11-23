# -*- coding: utf-8 -*-
"""Müşteriye giden sipariş e-postaları: sipariş alındı, onaylandı, kargoya verildi, teslim edildi, iptal, iade onayı, iade ödemesi.

- Şablonlar panelden düzenlenir (konu + metin, {değişken}li). Her olay tek tek açılıp kapatılır.
- Aynı sipariş ve olay için e-posta yalnız bir kez gider (musteri_mail_log).
- E-posta adresi yoksa, SMTP girilmemişse, ya da pazaryeri/dış kaynaklı siparişse hiçbir şey gönderilmez; hata sipariş akışını bozmaz.
- Gönderim notify.send ile yapılır, Bildirim kayıtlarında (outbox) görünür."""
import re
import time

from fastapi import Depends, HTTPException

import notify

OLAYLAR = {
    "siparis_alindi": "Sipariş alındı",
    "siparis_onaylandi": "Sipariş onaylandı (ödeme alındı)",
    "kargoya_verildi": "Kargoya verildi",
    "teslim_edildi": "Teslim edildi",
    "iptal": "Sipariş iptal edildi",
    "iade_onaylandi": "İade talebi onaylandı",
    "iade_odendi": "İade ödemesi yapıldı",
}
DEGISKENLER = ["ad", "siparis_no", "tutar", "urunler", "kargo_firmasi", "takip_no", "iade_tutari", "firma"]
VARSAYILAN = {
    "siparis_alindi": {"on": True, "subject": "{firma} — {siparis_no} numaralı siparişiniz alındı",
                       "body": "Merhaba {ad},\n\nSiparişiniz alındı. Sipariş numaranız: {siparis_no}\n\n{urunler}\n\nToplam: {tutar}\n\nSiparişinizin durumu değiştikçe size yeniden e-posta göndereceğiz.\n\nTeşekkür ederiz,\n{firma}"},
    "siparis_onaylandi": {"on": True, "subject": "{firma} — {siparis_no} siparişiniz onaylandı",
                          "body": "Merhaba {ad},\n\n{siparis_no} numaralı siparişiniz onaylandı ve hazırlanmaya başlandı.\n\nToplam: {tutar}\n\nTeşekkür ederiz,\n{firma}"},
    "kargoya_verildi": {"on": True, "subject": "{firma} — {siparis_no} siparişiniz kargoya verildi",
                        "body": "Merhaba {ad},\n\n{siparis_no} numaralı siparişiniz kargoya verildi.\nKargo firması: {kargo_firmasi}\nTakip numarası: {takip_no}\n\nKargo firmasının sitesinden takip numaranızla gönderinizi izleyebilirsiniz.\n\nTeşekkür ederiz,\n{firma}"},
    "teslim_edildi": {"on": True, "subject": "{firma} — {siparis_no} siparişiniz teslim edildi",
                      "body": "Merhaba {ad},\n\n{siparis_no} numaralı siparişiniz teslim edildi. Bizi tercih ettiğiniz için teşekkür ederiz.\n\nBir sorun varsa bu e-postayı yanıtlayarak ya da bizi arayarak bize ulaşabilirsiniz.\n\n{firma}"},
    "iptal": {"on": True, "subject": "{firma} — {siparis_no} siparişiniz iptal edildi",
              "body": "Merhaba {ad},\n\n{siparis_no} numaralı siparişiniz iptal edildi.\nÖdeme yaptıysanız iade süreci hakkında size ayrıca bilgi verilecektir.\n\nSorularınız için bize ulaşabilirsiniz.\n\n{firma}"},
    "iade_onaylandi": {"on": True, "subject": "{firma} — {siparis_no} iade talebiniz onaylandı",
                       "body": "Merhaba {ad},\n\n{siparis_no} numaralı siparişinize ait iade talebiniz onaylandı.\n\n{urunler}\n\nİade tutarı: {iade_tutari}\nÜrünler bize ulaştığında ödemeniz iade edilecektir.\n\n{firma}"},
    "iade_odendi": {"on": True, "subject": "{firma} — {siparis_no} iade ödemeniz yapıldı",
                    "body": "Merhaba {ad},\n\n{siparis_no} numaralı siparişinize ait {iade_tutari} tutarındaki iade ödemeniz yapıldı. Bankanıza bağlı olarak hesabınıza yansıması birkaç iş günü sürebilir.\n\n{firma}"},
}
YABANCI_KANAL = ("trendyol", "hepsiburada", "n11", "amazon", "ciceksepeti", "pttavm", "yemeksepeti", "getir", "trendyol_go", "migros")


def tl(v):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return ""
    s = ("%.2f" % n).rstrip("0").rstrip(".")
    a, _, b = s.partition(".")
    return "{:,}".format(int(a)).replace(",", ".") + ("," + b if b else "") + " TL"


def _t(v, n):
    return str(v or "").strip()[:n]


def doldur(tpl, v):
    t = str(tpl or "")
    for k, x in v.items():
        t = t.replace("{" + k + "}", str(x if x is not None else ""))
    t = re.sub(r"\{[a-z_]+\}", "", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def urun_satirlari(items):
    out = []
    for i in (items or [])[:30]:
        ad = i.get("name") or i.get("ad") or ""
        ek = i.get("vl") or i.get("variant") or ""
        out.append("• %s x %s%s — %s" % (i.get("qty") or i.get("adet") or 1, ad, (" (" + ek + ")") if ek else "", tl((i.get("price") or 0) * (i.get("qty") or 1))))
    return "\n".join(out)


async def ayarlar(db):
    d = await db.app_settings.find_one({"_id": "musteri_mail"}, {"_id": 0}) or {}
    out = {"on": bool(d.get("on")), "events": {}}
    for k, v in VARSAYILAN.items():
        o = (d.get("events") or {}).get(k) or {}
        out["events"][k] = {"on": bool(o.get("on", v["on"])), "subject": _t(o.get("subject"), 200) or v["subject"], "body": _t(o.get("body"), 4000) or v["body"]}
    return out


def vars_shop(o, firma):
    c = o.get("customer") or {}
    return {"ad": (c.get("name") or "").split(" ")[0] or "Müşterimiz", "siparis_no": o.get("order_no", ""), "tutar": tl(o.get("total")),
            "urunler": urun_satirlari(o.get("items")), "kargo_firmasi": o.get("carrier") or "—", "takip_no": o.get("tracking_no") or "—",
            "iade_tutari": tl(o.get("total")), "firma": firma}


async def gonder(db, olay, to, v, ref, kanal=""):
    """Tek e-posta. True: gönderildi. Asla istisna fırlatmaz."""
    try:
        if olay not in OLAYLAR or not to or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(to)):
            return False
        if kanal and str(kanal).lower() in YABANCI_KANAL:
            return False
        a = await ayarlar(db)
        e = a["events"][olay]
        if not a["on"] or not e["on"]:
            return False
        key = "%s:%s" % (ref, olay)
        if await db.musteri_mail_log.find_one({"key": key}, {"_id": 1}):
            return False
        cfg = await notify.get_settings(db)
        if not (cfg.get("smtp") or {}).get("host"):
            await db.musteri_mail_log.insert_one({"key": key, "olay": olay, "to": to, "status": "smtp_yok", "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
            return False
        await db.musteri_mail_log.insert_one({"key": key, "olay": olay, "to": to, "status": "gonderiliyor", "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        r = await notify.send(db, "email", to, doldur(e["body"], v), doldur(e["subject"], v)[:200], kind="musteri_" + olay, ref=str(ref), cfg=cfg)
        await db.musteri_mail_log.update_one({"key": key}, {"$set": {"status": r.get("status", "")}})
        return r.get("status") == "sent"
    except Exception:                                                      # noqa: BLE001
        return False


async def firma_adi(db):
    import marka_seo
    return (await marka_seo.firma_adi(db)) or "Mağazamız"


async def shop_olay(db, olay, o):
    """shop_orders belgesi için (web sitesi siparişleri). Dış kaynaklı siparişe gönderilmez."""
    if not o or o.get("external") or o.get("market_status"):
        return False
    return await gonder(db, olay, (o.get("customer") or {}).get("email"), vars_shop(o, await firma_adi(db)), "shop:" + str(o.get("id") or o.get("order_no")))


def shop_durum_olayi(durum):
    return {"onaylandi": "siparis_onaylandi", "kargoda": "kargoya_verildi", "teslim_edildi": "teslim_edildi", "iptal": "iptal"}.get(durum)


async def yp_olay(db, olay, o, ret=None):
    """yp_orders belgesi için (panelden girilen siparişler). Pazaryeri kanalları atlanır."""
    if not o or o.get("market_no"):
        return False
    try:
        from siparis import CARGOS, _PAZAR
        if o.get("channel") in _PAZAR:                                     # pazaryeri siparişi: müşteriye pazaryeri yazar
            return False
    except Exception:                                                      # noqa: BLE001
        CARGOS = {}
    c = o.get("customer") or {}
    cg = o.get("cargo") or {}
    firma = await firma_adi(db)
    v = {"ad": (c.get("name") or "").split(" ")[0] or "Müşterimiz", "siparis_no": o.get("no", ""), "tutar": tl(o.get("total")),
         "urunler": urun_satirlari((ret or o).get("items")), "kargo_firmasi": CARGOS.get(cg.get("firm"), cg.get("firm")) or "—",
         "takip_no": cg.get("code") or cg.get("barcode") or "—", "iade_tutari": tl((ret or {}).get("refund") or o.get("total")), "firma": firma}
    return await gonder(db, olay, c.get("email"), v, "yp:" + str(o.get("id")) + (":" + ret["id"] if ret else ""), o.get("channel"))


YP_DURUM = {"onaylandi": "siparis_onaylandi", "kargoda": "kargoya_verildi", "teslim": "teslim_edildi", "iptal": "iptal"}


def register(api_router, db, deps):
    adm = deps["require_admin"]

    @api_router.get("/shop/customer-mail")
    async def cm_get(_: dict = Depends(adm)):
        cfg = await notify.get_settings(db)
        a = await ayarlar(db)
        return {**a, "labels": OLAYLAR, "vars": DEGISKENLER, "defaults": VARSAYILAN,
                "smtp_ok": bool((cfg.get("smtp") or {}).get("host")), "from_addr": (cfg.get("smtp") or {}).get("from_addr") or (cfg.get("smtp") or {}).get("user") or ""}

    @api_router.put("/shop/customer-mail")
    async def cm_put(payload: dict, _: dict = Depends(adm)):
        ev = {}
        for k in OLAYLAR:
            o = (payload.get("events") or {}).get(k) or {}
            subj, body = _t(o.get("subject"), 200), _t(o.get("body"), 4000)
            for t in (subj, body):
                bad = [x for x in re.findall(r"\{([^{}]*)\}", t) if x not in DEGISKENLER]
                if bad:
                    raise HTTPException(422, "%s: bilinmeyen değişken {%s}. Kullanılabilir: %s" % (OLAYLAR[k], bad[0], " ".join("{" + x + "}" for x in DEGISKENLER)))
            ev[k] = {"on": bool(o.get("on", True)), "subject": subj, "body": body}
        await db.app_settings.update_one({"_id": "musteri_mail"}, {"$set": {"on": bool(payload.get("on")), "events": ev, "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S")}}, upsert=True)
        return await cm_get(_)

    @api_router.post("/shop/customer-mail/test")
    async def cm_test(payload: dict, _: dict = Depends(adm)):
        """Seçilen şablonu örnek siparişle yöneticinin yazdığı adrese gönderir (kayıt tutulmaz, bir kez kuralına takılmaz)."""
        olay, to = _t(payload.get("event"), 30), _t(payload.get("to"), 120)
        if olay not in OLAYLAR:
            raise HTTPException(422, "Olay geçersiz")
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", to):
            raise HTTPException(422, "Geçerli bir e-posta adresi yazın")
        cfg = await notify.get_settings(db)
        if not (cfg.get("smtp") or {}).get("host"):
            raise HTTPException(422, "Önce Bağlantı bölümünden e-posta (SMTP) ayarlarını girin")
        o = (payload.get("template") or {})
        e = (await ayarlar(db))["events"][olay]
        subj, body = _t(o.get("subject"), 200) or e["subject"], _t(o.get("body"), 4000) or e["body"]
        v = {"ad": "Ayşe", "siparis_no": "SP-0001", "tutar": "1.250 TL", "urunler": "• 1 x Örnek Ürün — 1.250 TL", "kargo_firmasi": "Aras Kargo",
             "takip_no": "123456789", "iade_tutari": "1.250 TL", "firma": await firma_adi(db)}
        r = await notify.send(db, "email", to, doldur(body, v), "[Deneme] " + doldur(subj, v)[:190], kind="musteri_deneme", ref="test", cfg=cfg)
        if r.get("status") != "sent":
            raise HTTPException(422, "Gönderilemedi: " + (r.get("error") or "bilinmeyen hata"))
        return {"ok": True}

    @api_router.get("/shop/customer-mail/log")
    async def cm_log(_: dict = Depends(adm)):
        rows = await db.musteri_mail_log.find({}, {"_id": 0}).sort("at", -1).to_list(40)
        return [{**r, "olay_adi": OLAYLAR.get(r.get("olay"), r.get("olay", ""))} for r in rows]
