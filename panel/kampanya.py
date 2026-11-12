# -*- coding: utf-8 -*-
"""Kampanya motoru: X al Y öde, kademeli indirim, sepet indirimi, kupon, bedava kargo.

Hesap tek yerden yapılır (`apply_campaigns`) ve saf bir fonksiyondur: veritabanı
görmez, bu yüzden hem sepet ekranı hem sipariş kaydı hem de panelin "kampanya
dene" ekranı aynı sonucu üretir.

Üst üste binme kuralı: "tek başına" işaretli kampanya başkasıyla birleşmez.
Motor hem birleşebilenlerin toplamını hem her "tek başına" kampanyayı ayrı
hesaplar, müşteri lehine olanı seçer. Böylece müşteri her zaman en iyi fiyatı
görür, satıcı da iki indirimin üst üste binip zarar etmesini yaşamaz.

İndirim adet bazında işler: 3 al 2 öde dendiğinde bedava olan, kampanyaya giren
ürünlerin **en ucuzudur**; yuvarlama her satırda ayrı yapılır ki toplamla satır
toplamı birbirini tutsun.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException

from urun import _int, _num, _t

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

TYPES = {
    "x_al_y_ode":   "X al Y öde",
    "kademeli":     "X alana Y ürün indirimli",
    "sepet":        "Sepet tutarına indirim",
    "urun":         "Ürün / kategori indirimi",
    "kargo":        "Bedava kargo",
    "kupon":        "Kupon kodu",
    "hediye":       "Hediye ürün",
}
PAYMENTS = ("", "kredi", "havale", "kapida", "taksit")


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


def _today():
    return _now()[:10]


# ---------------------------------------------------------------- kapsam ve koşul
def in_scope(sc, it):
    """Ürün kampanyanın kapsamına giriyor mu?"""
    sc = sc or {}
    pid = str(it.get("product") or "")
    if pid and pid in (sc.get("exclude") or []):
        return False
    if (it.get("cat") or "") in (sc.get("exclude_cats") or []):
        return False
    if sc.get("all"):
        return True
    return bool((pid and pid in (sc.get("products") or []))
                or ((it.get("cat") or "") in (sc.get("cats") or []))
                or ((it.get("brand") or "") in (sc.get("brands") or [])))


def scope_sum(c, items):
    return round(sum(_num(i.get("price")) * _int(i.get("qty"), 1)
                     for i in items if in_scope(c.get("scope"), i)), 2)


def eligible(c, cart, ctx):
    """Kampanya bu sepete uygulanabilir mi? (sebebiyle birlikte)"""
    ctx = ctx or {}
    if not c.get("on", True):
        return False, "kapalı"
    day = str(ctx.get("day") or _today())[:10]
    if c.get("start") and day < str(c["start"])[:10]:
        return False, "henüz başlamadı"
    if c.get("end") and day > str(c["end"])[:10]:
        return False, "süresi bitti"
    cd = c.get("cond") or {}
    lim = c.get("limit") or {}
    if _int(lim.get("total")) and _int(lim.get("used")) >= _int(lim.get("total")):
        return False, "kullanım hakkı bitti"
    if c.get("type") == "kupon":
        code = _t(cd.get("code"), 40).lower()
        if not code:
            return False, "kupon kodu tanımsız"
        if _t(ctx.get("code"), 40).lower() != code:
            return False, "kupon kodu girilmedi"
    items = cart.get("items") or []
    sub = scope_sum(c, items)
    qty = sum(_int(i.get("qty"), 1) for i in items if in_scope(c.get("scope"), i))
    if _num(cd.get("min_total")) and sub < _num(cd.get("min_total")):
        return False, "en az %s ₺ tutar gerekli" % _num(cd["min_total"])
    if _int(cd.get("min_qty")) and qty < _int(cd["min_qty"]):
        return False, "en az %d ürün gerekli" % _int(cd["min_qty"])
    if cd.get("payment") and _t(ctx.get("payment"), 20) != cd["payment"]:
        return False, "ödeme tipi uygun değil"
    if cd.get("group") and _t(ctx.get("group"), 40) != cd["group"]:
        return False, "müşteri grubu uygun değil"
    if cd.get("first_order") and _int(ctx.get("orders")) > 0:
        return False, "sadece ilk siparişte"
    if cd.get("new_member") and _int(ctx.get("member_days"), 9999) > _int(cd.get("new_days"), 30):
        return False, "sadece yeni üyelerde"
    if not qty and c.get("type") in ("x_al_y_ode", "kademeli", "urun"):
        return False, "kapsamda ürün yok"
    return True, ""


# ---------------------------------------------------------------- tek kampanya hesabı
def _units(c, items):
    """Kapsamdaki ürünleri adet adet aç: 3 al 2 öde ancak adet üzerinden doğru çalışır."""
    out = []
    for n, it in enumerate(items):
        if not in_scope(c.get("scope"), it):
            continue
        p = _num(it.get("price"))
        for _ in range(max(_int(it.get("qty"), 1), 0)):
            out.append({"row": n, "price": p})
    return out


def _spread(cuts, items):
    """Adet indirimlerini satırlara topla."""
    rows = {}
    for u, cut in cuts:
        if cut > 0:
            rows[u["row"]] = round(rows.get(u["row"], 0.0) + cut, 2)
    return rows


def run_one(c, cart, ctx):
    """Bir kampanyanın sepete etkisi: satır indirimleri, toplam, kargo ve hediye."""
    items = cart.get("items") or []
    typ = c.get("type")
    g = c.get("gain") or {}
    cd = c.get("cond") or {}
    cuts, free_ship, gift, note = [], False, "", ""

    if typ == "x_al_y_ode":
        buy, pay = max(_int(cd.get("buy"), 2), 1), max(_int(cd.get("pay"), 1), 0)
        if pay >= buy:
            return None
        us = sorted(_units(c, items), key=lambda u: u["price"])
        free = (len(us) // buy) * (buy - pay)
        if _int(cd.get("max_use")):
            free = min(free, _int(cd["max_use"]) * (buy - pay))
        for u in us[:free]:
            cuts.append((u, u["price"]))
        note = "%d adet bedava" % free if free else ""

    elif typ == "kademeli":
        buy, give = max(_int(cd.get("buy"), 1), 1), max(_int(cd.get("give"), 1), 1)
        pct = min(max(_num(g.get("y_percent")), 0.0), 100.0)
        us = sorted(_units(c, items), key=lambda u: -u["price"])
        step, n = buy + give, 0
        while (n + 1) * step <= len(us) + give and (n * step + buy) <= len(us):
            grp = us[n * step:(n + 1) * step]
            for u in sorted(grp, key=lambda u: u["price"])[:give]:
                cuts.append((u, round(u["price"] * pct / 100.0, 2)))
            n += 1
        note = "%d ürün %%%s indirimli" % (n * give, _num(pct)) if n else ""

    elif typ == "urun":
        pct = min(max(_num(g.get("percent")), 0.0), 100.0)
        amt = _num(g.get("amount"))
        for u in _units(c, items):
            cut = round(u["price"] * pct / 100.0, 2) if pct else min(amt, u["price"])
            cuts.append((u, cut))

    elif typ in ("sepet", "kupon"):
        base = scope_sum(c, items)
        pct = min(max(_num(g.get("percent")), 0.0), 100.0)
        total = round(base * pct / 100.0, 2) if pct else min(_num(g.get("amount")), base)
        cap = _num(g.get("max_amount"))
        if cap:
            total = min(total, cap)
        us = _units(c, items)
        left = total
        for n, u in enumerate(us):
            share = round(total * u["price"] / base, 2) if base else 0.0
            share = left if n == len(us) - 1 else min(share, left)
            cuts.append((u, max(share, 0.0)))
            left = round(left - share, 2)
        free_ship = bool(g.get("free_ship"))

    elif typ == "kargo":
        free_ship = True
        note = "kargo bedava"

    elif typ == "hediye":
        gift = _t(g.get("gift"), 24)
        note = "hediye ürün"

    else:
        return None

    rows = _spread(cuts, items)
    disc = round(sum(rows.values()), 2)
    if not disc and not free_ship and not gift:
        return None
    return {"id": c.get("id", ""), "name": _t(c.get("name"), 80) or TYPES.get(typ, typ), "type": typ,
            "discount": disc, "rows": rows, "free_ship": free_ship, "gift": gift, "note": note}


# ---------------------------------------------------------------- sepete uygula
def apply_campaigns(cart, camps, ctx=None):
    """Sepete kampanyaları uygula ve müşteri lehine olan bileşimi seç."""
    ctx = ctx or {}
    items = [dict(i) for i in (cart.get("items") or [])]
    sub = round(sum(_num(i.get("price")) * _int(i.get("qty"), 1) for i in items), 2)
    ship0 = _num(cart.get("ship"))
    ok, skipped = [], []
    for c in camps or []:
        fit, why = eligible(c, cart, ctx)
        if not fit:
            skipped.append({"id": c.get("id", ""), "name": _t(c.get("name"), 80), "why": why})
            continue
        r = run_one(c, {"items": items}, ctx)
        if r:
            r["priority"] = _int(c.get("priority"), 10)
            r["exclusive"] = bool(c.get("exclusive"))
            ok.append(r)
        else:
            skipped.append({"id": c.get("id", ""), "name": _t(c.get("name"), 80), "why": "indirim çıkmadı"})
    ok.sort(key=lambda r: (-r["priority"], r["id"]))

    stack = [r for r in ok if not r["exclusive"]]
    best = stack
    bv = sum(r["discount"] for r in stack) + (ship0 if any(r["free_ship"] for r in stack) else 0)
    for r in ok:
        if not r["exclusive"]:
            continue
        v = r["discount"] + (ship0 if r["free_ship"] else 0)
        if v > bv + 0.005:
            best, bv = [r], v
    for r in ok:
        if r not in best:
            skipped.append({"id": r["id"], "name": r["name"], "why": "tek başına kampanya ile birleşmez"})

    rows = {}
    for r in best:
        for k, v in r["rows"].items():
            rows[k] = round(rows.get(k, 0.0) + v, 2)
    for n, it in enumerate(items):
        line = round(_num(it.get("price")) * _int(it.get("qty"), 1), 2)
        it["discount"] = min(rows.get(n, 0.0), line)
        it["line_total"] = round(line - it["discount"], 2)
    disc = round(sum(i["discount"] for i in items), 2)
    free_ship = any(r["free_ship"] for r in best)
    ship = 0.0 if free_ship else ship0
    return {"items": items, "subtotal": sub, "discount": disc, "ship": ship, "ship_full": ship0,
            "free_ship": free_ship, "gifts": [r["gift"] for r in best if r["gift"]],
            "total": round(max(sub - disc, 0.0) + ship, 2),
            "lines": [{"id": r["id"], "name": r["name"], "type": r["type"], "discount": r["discount"],
                       "free_ship": r["free_ship"], "note": r["note"]} for r in best],
            "skipped": skipped}


# ---------------------------------------------------------------- kayıt doğrulama
def clean(c, old=None):
    old = old or {}
    typ = _t(c.get("type"), 20) or old.get("type") or "sepet"
    if typ not in TYPES:
        raise HTTPException(422, "Kampanya tipi geçersiz")
    name = _t(c.get("name"), 80) or old.get("name") or ""
    if not name:
        raise HTTPException(422, "Kampanya adı gerekli")
    sc, cd, g = c.get("scope") or {}, c.get("cond") or {}, c.get("gain") or {}
    scope = {"all": bool(sc.get("all")),
             "cats": [_t(x, 40) for x in (sc.get("cats") or [])][:60],
             "brands": [_t(x, 40) for x in (sc.get("brands") or [])][:60],
             "products": [_t(x, 24) for x in (sc.get("products") or [])][:300],
             "exclude": [_t(x, 24) for x in (sc.get("exclude") or [])][:300],
             "exclude_cats": [_t(x, 40) for x in (sc.get("exclude_cats") or [])][:60]}
    if not (scope["all"] or scope["cats"] or scope["brands"] or scope["products"]):
        if typ in ("x_al_y_ode", "kademeli", "urun"):
            raise HTTPException(422, "Kapsam seçilmeli: tüm ürünler, kategori, marka veya ürün")
        scope["all"] = True
    cond = {"buy": _int(cd.get("buy")), "pay": _int(cd.get("pay")), "give": _int(cd.get("give")),
            "min_total": _num(cd.get("min_total")), "min_qty": _int(cd.get("min_qty")),
            "max_use": _int(cd.get("max_use")), "payment": _t(cd.get("payment"), 20),
            "group": _t(cd.get("group"), 40), "first_order": bool(cd.get("first_order")),
            "new_member": bool(cd.get("new_member")), "new_days": _int(cd.get("new_days"), 30),
            "code": _t(cd.get("code"), 40).upper()}
    if cond["payment"] and cond["payment"] not in PAYMENTS:
        raise HTTPException(422, "Ödeme tipi geçersiz")
    gain = {"percent": min(max(_num(g.get("percent")), 0.0), 100.0), "amount": _num(g.get("amount")),
            "y_percent": min(max(_num(g.get("y_percent")), 0.0), 100.0),
            "max_amount": _num(g.get("max_amount")), "free_ship": bool(g.get("free_ship")),
            "gift": _t(g.get("gift"), 24)}
    if typ == "x_al_y_ode":
        if cond["buy"] < 2 or cond["pay"] < 1 or cond["pay"] >= cond["buy"]:
            raise HTTPException(422, "X al Y öde: alınan adet ödenenden büyük olmalı (örnek 3 al 2 öde)")
    if typ == "kademeli":
        if cond["buy"] < 1 or cond["give"] < 1 or gain["y_percent"] <= 0:
            raise HTTPException(422, "Kademeli indirim: alınan adet, verilen adet ve indirim oranı gerekli")
    if typ in ("sepet", "kupon", "urun") and not (gain["percent"] or gain["amount"] or gain["free_ship"]):
        raise HTTPException(422, "İndirim oranı veya tutarı girilmeli")
    if typ == "kupon" and not cond["code"]:
        raise HTTPException(422, "Kupon kodu gerekli")
    if typ == "hediye" and not gain["gift"]:
        raise HTTPException(422, "Hediye ürün seçilmeli")
    out = {"id": old.get("id") or uuid.uuid4().hex[:12], "name": name, "type": typ,
           "on": bool(c.get("on", old.get("on", True))), "priority": _int(c.get("priority"), old.get("priority", 10)),
           "exclusive": bool(c.get("exclusive", old.get("exclusive", False))),
           "start": _t(c.get("start", old.get("start", "")), 10), "end": _t(c.get("end", old.get("end", "")), 10),
           "label": _t(c.get("label", old.get("label", "")), 40), "scope": scope, "cond": cond, "gain": gain,
           "limit": {"per_cust": _int((c.get("limit") or {}).get("per_cust")),
                     "total": _int((c.get("limit") or {}).get("total")),
                     "used": _int((old.get("limit") or {}).get("used"))},
           "created_at": old.get("created_at") or _now(), "at": _now()}
    if out["start"] and out["end"] and out["end"] < out["start"]:
        raise HTTPException(422, "Bitiş tarihi başlangıçtan önce olamaz")
    return out


def summary(c):
    """Panelde ve sitede gösterilecek tek satırlık özet."""
    cd, g = c.get("cond") or {}, c.get("gain") or {}
    t = c.get("type")
    if t == "x_al_y_ode":
        return "%d al %d öde" % (_int(cd.get("buy")), _int(cd.get("pay")))
    if t == "kademeli":
        return "%d alana %d ürün %%%s" % (_int(cd.get("buy")), _int(cd.get("give")), _num(g.get("y_percent")))
    if t == "kargo":
        return "%s ₺ üzeri kargo bedava" % _num(cd.get("min_total")) if _num(cd.get("min_total")) else "kargo bedava"
    if t == "hediye":
        return "hediye ürün"
    if t == "kupon":
        kod = cd.get("code") or ""
        return "%s kodu ile %s" % (kod, "%%%s" % _num(g.get("percent")) if _num(g.get("percent"))
                                   else "%s ₺" % _num(g.get("amount")))
    base = "%%%s indirim" % _num(g.get("percent")) if _num(g.get("percent")) else "%s ₺ indirim" % _num(g.get("amount"))
    return ("%s ₺ üzeri %s" % (_num(cd.get("min_total")), base)) if _num(cd.get("min_total")) else base


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    async def all_camps(only_on=True):
        q = {"on": True} if only_on else {}
        return await db.yp_camps.find(q, {"_id": 0}).to_list(400)

    @api_router.get("/yp/campaigns")
    async def camp_list(q: str = "", typ: str = "", state: str = "", _=Depends(require_admin)):
        cs = await all_camps(False)
        qq = _t(q, 60).lower()
        if qq:
            cs = [c for c in cs if qq in (c.get("name", "") + " " + (c.get("cond") or {}).get("code", "")).lower()]
        if typ:
            cs = [c for c in cs if c.get("type") == typ]
        day = _today()
        def st(c):
            if not c.get("on"):
                return "kapali"
            if c.get("end") and c["end"] < day:
                return "bitti"
            if c.get("start") and c["start"] > day:
                return "bekliyor"
            return "aktif"
        for c in cs:
            c["state"], c["summary"] = st(c), summary(c)
        if state:
            cs = [c for c in cs if c["state"] == state]
        cs.sort(key=lambda c: (-_int(c.get("priority"), 10), c.get("name", "")))
        return {"items": cs, "types": [{"id": k, "name": v} for k, v in TYPES.items()],
                "counts": {k: len([c for c in cs if c["state"] == k]) for k in ("aktif", "bekliyor", "bitti", "kapali")}}

    @api_router.post("/yp/campaigns")
    async def camp_add(payload: dict, _=Depends(require_admin)):
        c = clean(payload)
        await db.yp_camps.insert_one(dict(c))
        return {"ok": True, "item": c, "summary": summary(c)}

    @api_router.put("/yp/campaigns/{cid}")
    async def camp_put(cid: str, payload: dict, _=Depends(require_admin)):
        old = await db.yp_camps.find_one({"id": _t(cid, 24)}, {"_id": 0})
        if not old:
            raise HTTPException(404, "Kampanya bulunamadı")
        c = clean(payload, old)
        await db.yp_camps.update_one({"id": c["id"]}, {"$set": c})
        return {"ok": True, "item": c, "summary": summary(c)}

    @api_router.delete("/yp/campaigns/{cid}")
    async def camp_del(cid: str, _=Depends(require_admin)):
        r = await db.yp_camps.delete_one({"id": _t(cid, 24)})
        if not r.deleted_count:
            raise HTTPException(404, "Kampanya bulunamadı")
        return {"ok": True}

    @api_router.post("/yp/campaigns/try")
    async def camp_try(payload: dict, _=Depends(require_admin)):
        """Panelden sepet kurup kampanyaları denemek için: hangi kampanya neden girmedi de yazar."""
        items = []
        for it in (payload.get("items") or [])[:60]:
            pid = _t((it or {}).get("product"), 24)
            p = await db.yp_products.find_one({"id": pid}, {"_id": 0}) if pid else None
            items.append({"product": pid, "name": _t((it or {}).get("name") or (p or {}).get("name"), 120),
                          "cat": _t((it or {}).get("cat") or (p or {}).get("cat"), 40),
                          "brand": _t((it or {}).get("brand") or (p or {}).get("brand"), 40),
                          "price": _num(it.get("price") if it.get("price") is not None else (p or {}).get("price")),
                          "qty": max(_int(it.get("qty"), 1), 1)})
        camps = await all_camps(False)
        ctx = {"payment": _t(payload.get("payment"), 20), "code": _t(payload.get("code"), 40),
               "group": _t(payload.get("group"), 40), "orders": _int(payload.get("orders")),
               "member_days": _int(payload.get("member_days"), 9999), "day": _today()}
        return apply_campaigns({"items": items, "ship": _num(payload.get("ship"))}, camps, ctx)

    return api_router
