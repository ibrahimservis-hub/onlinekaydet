# -*- coding: utf-8 -*-
"""Sipariş ve iade: durum akışı, kargo, stok düşme/geri verme ve kârlılık.

Stok, siparişin **kaydedildiği an** düşer; iptal ve iade onayında geri döner.
İki işlem de `pazaryeri` modülündeki çekirdeği kullanır: aynı sipariş iki kez
işlense bile stok ikinci kez oynamaz, stok yetersizse sipariş hiç kaydedilmez.

Durum akışı zorlanır: teslim edilmiş sipariş hazırlanıyora dönmez, iptal edilen
sipariş kargoya verilmez. Her değişiklik zaman çizelgesine yazılır; müşteri
"benim siparişim ne oldu" dediğinde satıcı tek ekrandan görür.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException

import barkod
from kampanya import _n, apply_campaigns
from pazaryeri import give_stock, take_stock
from urun import CHANNELS, _int, _num, _t, profit

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

STATES = {"yeni": "Yeni sipariş", "onaylandi": "Onaylandı", "hazirlaniyor": "Hazırlanıyor",
          "kargoda": "Kargoda", "teslim": "Teslim edildi", "iptal": "İptal"}
FLOW = {"yeni": ("onaylandi", "iptal"), "onaylandi": ("hazirlaniyor", "kargoda", "iptal"),
        "hazirlaniyor": ("kargoda", "iptal"), "kargoda": ("teslim", "iptal"), "teslim": (), "iptal": ()}
OPEN = ("yeni", "onaylandi", "hazirlaniyor", "kargoda")
CARGOS = {"aras": "Aras Kargo", "yurtici": "Yurtiçi Kargo", "mng": "MNG Kargo", "ptt": "PTT Kargo",
          "surat": "Sürat Kargo", "ups": "UPS", "sendeo": "Sendeo", "hepsijet": "HepsiJET",
          "trendyol_express": "Trendyol Express", "kolaygelsin": "Kolay Gelsin", "elden": "Elden teslim"}
RSTATES = {"talep": "İade talebi", "onay": "Onaylandı", "red": "Reddedildi", "tamam": "Tamamlandı"}
RREASONS = ("bedeni olmadi", "kusurlu urun", "yanlis urun", "begenmedim", "gec teslim", "diger")
SORTS = {"yeni": [("seq", -1)], "eski": [("seq", 1)], "tutar": [("total", -1)], "tutar_a": [("total", 1)]}


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


def _phone(v):
    d = "".join(ch for ch in str(v or "") if ch.isdigit())
    if d.startswith("90") and len(d) > 11:
        d = d[2:]
    return d[-11:] if len(d) >= 11 else d


def next_no(n):
    """İnsan okuyabilen sipariş numarası: SP-2026-00042."""
    return "SP-%s-%05d" % (_now()[:4], n + 1)


def can_go(cur, new):
    return new in FLOW.get(cur, ())


def clean_items(rows):
    out = []
    for it in (rows or [])[:80]:
        pid = _t((it or {}).get("product"), 24)
        name = _t((it or {}).get("name"), 140)
        qty = max(_int(it.get("qty"), 1), 1)
        price = _num(it.get("price"))
        if not name:
            raise HTTPException(422, "Ürün adı boş olamaz")
        if price <= 0:
            raise HTTPException(422, "%s: fiyat girilmeli" % name)
        out.append({"product": pid, "name": name, "sku": _t(it.get("sku"), 40),
                    "barcode": _t(it.get("barcode"), 40),
                    "variant": _t(it.get("variant"), 60), "qty": qty, "price": price,
                    "cost": _num(it.get("cost")), "vat": _num(it.get("vat"), 20.0),
                    "cat": _t(it.get("cat"), 40), "brand": _t(it.get("brand"), 40)})
    if not out:
        raise HTTPException(422, "Siparişe en az bir ürün eklenmeli")
    return out


def order_profit(o):
    """Siparişin net kârı: satır bazında matrah − alış − komisyon, kargo gideri düşülür."""
    comm = dict(CHANNELS).get(o.get("channel"), ("", 0.0))[1]
    net = 0.0
    for it in o.get("items") or []:
        line = _num(it.get("price")) * _int(it.get("qty"), 1) - _num(it.get("discount"))
        pr = profit(line, _num(it.get("cost")) * _int(it.get("qty"), 1), _num(it.get("vat"), 20.0), comm, 0.0)
        net += pr["net"]
    net -= _num(o.get("ship_cost"))
    return round(net, 2)


def sevk_kodu(o):
    """Fişte basılacak barkod: pazaryerinin verdiği gönderi barkodu > kargo takip no > sipariş no."""
    cg = o.get("cargo") or {}
    return _t(cg.get("barcode"), 40) or _t(cg.get("code"), 40) or _t(o.get("no"), 40)


def view(o):
    o = dict(o)
    o["state_name"] = STATES.get(o.get("status"), o.get("status", ""))
    o["channel_name"] = dict(CHANNELS).get(o.get("channel"), (o.get("channel", ""), 0))[0]
    o["cargo_name"] = CARGOS.get((o.get("cargo") or {}).get("firm", ""), "")
    o["next"] = [{"id": s, "name": STATES[s]} for s in FLOW.get(o.get("status"), ())]
    o["qty"] = sum(_int(i.get("qty"), 1) for i in o.get("items") or [])
    o["profit"] = order_profit(o)
    o["scan"] = sevk_kodu(o)
    return o


def _fis_css():
    return ("@page{size:A4;margin:10mm}*{box-sizing:border-box}"
            "body{font:13px/1.45 -apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#101828;margin:0}"
            ".f{page-break-after:always;padding:6mm 0;border-bottom:1px dashed #d0d5dd}"
            ".f:last-child{page-break-after:auto;border:0}"
            ".hd{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;"
            "border-bottom:2px solid #101828;padding-bottom:8px;margin-bottom:10px}"
            ".hd h1{font-size:18px;margin:0}.hd .no{font:700 15px ui-monospace,Menlo,monospace}"
            ".g{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:12px}"
            ".bx{border:1px solid #d0d5dd;border-radius:8px;padding:9px 11px}"
            ".bx b{display:block;font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:#667085;margin-bottom:4px}"
            "table{width:100%;border-collapse:collapse;margin-top:6px}"
            "th{text-align:left;font-size:11px;text-transform:uppercase;color:#667085;border-bottom:1px solid #d0d5dd;padding:6px 4px}"
            "td{padding:7px 4px;border-bottom:1px solid #eaecf0}.r{text-align:right}"
            "th.a,td.a{width:70px}th.b2,td.b2{width:100px}th.c2,td.c2{width:110px}"
            ".tot{margin-top:8px;margin-left:auto;width:48%}"
            ".tot div{display:flex;justify-content:space-between;padding:3px 0}"
            ".tot .b{font-weight:700;border-top:1px solid #101828;padding-top:6px;margin-top:4px}"
            ".bk{font:700 20px ui-monospace,Menlo,monospace;letter-spacing:.1em;margin-top:8px}"
            ".nt{margin-top:10px;font-size:12px;color:#475467}"
            ".sg{margin-top:16px;display:flex;justify-content:space-between;font-size:11px;color:#667085}"
            ".sg span{border-top:1px solid #98a2b3;padding-top:4px;width:40%;text-align:center}"
            ".bc{text-align:center;padding:9px 11px}.bc svg{display:block;margin:4px auto 0}"
            ".bc2{margin:4px 0 2px}.ub{margin-top:3px}.ub svg{display:block}"
            "@media print{.noprint{display:none}}")


def _tel(v):
    d = "".join(ch for ch in str(v or "") if ch.isdigit())
    return "%s %s %s %s" % (d[:4], d[4:7], d[7:9], d[9:]) if len(d) == 11 else (v or "")


def _esc(v):
    return (str(v or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def fis_html(orders, kind, firm=""):
    """Toplu kargo fişi / sipariş fişi: tek sayfada art arda, her sipariş ayrı kâğıt.

    Barkod kâğıttan okunacak diye SVG basılır. Kargo fişinde sevk barkodu
    (pazaryerinin verdiği gönderi barkodu, yoksa kargo takip numarası) büyük basılır;
    sipariş fişinde ürünlerin kendi barkodları satır satır yer alır ki depoda
    toplama sırasında el terminaliyle okunabilsin.
    """
    out = []
    for o in orders:
        c = o.get("customer") or {}
        adres = " ".join(x for x in [c.get("address"), c.get("district"), c.get("city")] if x)
        cg = o.get("cargo") or {}
        pazar = _t(o.get("market_no"), 40)
        head = ("<div class='hd'><div><h1>%s</h1><div style='color:#667085;font-size:12px'>%s</div></div>"
                "<div style='text-align:right'><div class='no'>%s</div>"
                "<div style='color:#667085;font-size:12px'>%s</div>%s</div></div>"
                % ("Kargo fişi" if kind == "kargo" else "Sipariş fişi", _esc(firm), _esc(o.get("no")),
                   _esc(str(o.get("at") or "")[:16].replace("T", " ")),
                   ("<div style='color:#667085;font-size:12px'>%s: %s</div>"
                    % (_esc(o.get("channel_name") or o.get("channel")), _esc(pazar))) if pazar else ""))
        sag = (("<b>Gönderici</b>%s<br>%s" % (_esc(firm) or "—",
                                              _esc(CARGOS.get(cg.get("firm", ""), "Kargo firması seçilmedi"))))
               if kind == "kargo" else
               ("<b>Sipariş bilgisi</b>Satış kanalı: %s<br>Ödeme: %s<br>Kargo: %s"
                % (_esc(o.get("channel_name") or o.get("channel")),
                   "Ödendi" if o.get("paid") else "Bekliyor",
                   _esc(CARGOS.get(cg.get("firm", ""), "—")))))
        kutu = ("<div class='g'><div class='bx'><b>Alıcı</b>%s<br>%s<br>%s</div>"
                "<div class='bx'>%s</div></div>"
                % (_esc(c.get("name")), _esc(_tel(c.get("phone"))), _esc(adres) or "—", sag))
        sevk = sevk_kodu(o)
        if kind == "kargo":
            etiket = ("Gönderi barkodu" if _t(cg.get("barcode"), 40) else
                      ("Kargo takip numarası" if _t(cg.get("code"), 40) else "Sipariş numarası"))
            body = (kutu
                    + ("<div class='bx bc'><b>%s</b>%s</div>"
                       % (etiket, barkod.svg(sevk, height=62, module=2.0)))
                    + (("<div class='bx bc' style='margin-top:8px'><b>%s sipariş numarası</b>%s</div>"
                        % (_esc(o.get("channel_name") or "Pazaryeri"), barkod.svg(pazar, height=40, module=1.5)))
                       if pazar else "")
                    + ("<div class='nt'>%d ürün · %s ₺ · %s</div>"
                       % (sum(_int(i.get("qty"), 1) for i in o.get("items") or []),
                          _n(o.get("total")), "Kapıda ödeme" if not o.get("paid") else "Ödendi"))
                    + ("<div class='nt'>Not: %s</div>" % _esc(o.get("note")) if o.get("note") else "")
                    + "<div class='sg'><span>Teslim eden</span><span>Teslim alan</span></div>")
        else:
            satir = "".join("<tr><td>%s<div style='color:#667085;font-size:11px'>%s</div>%s</td>"
                            "<td class='r a'>%d</td><td class='r b2'>%s ₺</td><td class='r c2'>%s ₺</td></tr>"
                            % (_esc(i.get("name")), _esc(i.get("sku") or i.get("variant") or ""),
                               ("<div class='ub'>%s</div>" % barkod.svg(_t(i.get("barcode"), 40), height=26,
                                                                       module=1.1)) if i.get("barcode") else "",
                               _int(i.get("qty"), 1), _n(i.get("price")),
                               _n(_num(i.get("price")) * _int(i.get("qty"), 1) - _num(i.get("discount"))))
                            for i in o.get("items") or [])
            kamp = "".join("<div><span>%s</span><span>−%s ₺</span></div>" % (_esc(k.get("name")), _n(k.get("discount")))
                           for k in o.get("camps") or [])
            body = (kutu
                    + ("<div class='bc bc2'>%s</div>" % barkod.svg(sevk, height=44, module=1.6))
                    + "<table><tr><th>Ürün</th><th class='r a'>Adet</th><th class='r b2'>Fiyat</th>"
                    "<th class='r c2'>Tutar</th></tr>%s</table>" % satir
                    + ("<div class='tot'><div><span>Ara toplam</span><span>%s ₺</span></div>%s"
                       "<div><span>Kargo</span><span>%s</span></div>"
                       "<div class='b'><span>Genel toplam</span><span>%s ₺</span></div></div>"
                       % (_n(o.get("subtotal")), kamp,
                          "Bedava" if o.get("free_ship") else _n(o.get("ship_fee")) + " ₺", _n(o.get("total"))))
                    + ("<div class='nt'>Not: %s</div>" % _esc(o.get("note")) if o.get("note") else ""))
        out.append("<div class='f'>%s%s</div>" % (head, body))
    return ("<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>%s</title><style>%s</style></head>"
            "<body>%s<script>window.onload=function(){setTimeout(function(){window.print()},250)}</script>"
            "</body></html>" % ("Kargo fişi" if kind == "kargo" else "Sipariş fişi", _fis_css(), "".join(out)))


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    async def get_order(oid):
        o = await db.yp_orders.find_one({"id": _t(oid, 24)}, {"_id": 0})
        if not o:
            o = await db.yp_orders.find_one({"no": _t(oid, 24).upper()}, {"_id": 0})
        if not o:
            raise HTTPException(404, "Sipariş bulunamadı")
        return o

    async def log(oid, state, note="", by="panel"):
        await db.yp_orders.update_one({"id": oid}, {"$push": {"timeline": {
            "at": _now(), "by": by, "state": state, "note": _t(note, 200)}}})

    # ------------------------------------------------------------ liste ve arama
    @api_router.get("/yp/orders")
    async def order_list(q: str = "", status: str = "", channel: str = "", cargo: str = "",
                         frm: str = "", to: str = "", sort: str = "yeni", offset: int = 0, limit: int = 40,
                         _=Depends(require_admin)):
        f = {}
        if status in STATES:
            f["status"] = status
        elif status == "acik":
            f["status"] = {"$in": list(OPEN)}
        if channel:
            f["channel"] = _t(channel, 24)
        if cargo:
            f["cargo.firm"] = _t(cargo, 24)
        if frm or to:
            f["at"] = {}
            if frm:
                f["at"]["$gte"] = _t(frm, 10)
            if to:
                f["at"]["$lte"] = _t(to, 10) + "T23:59:59"
        qq = _t(q, 60)
        if qq:
            dig = _phone(qq).lstrip("0")
            ors = [{"no": {"$regex": qq.upper()}}, {"customer.name": {"$regex": qq, "$options": "i"}},
                   {"items.name": {"$regex": qq, "$options": "i"}}, {"cargo.code": {"$regex": qq.upper()}}]
            if dig:
                ors.append({"customer.phone": {"$regex": dig}})
            f["$or"] = ors
        rows = await db.yp_orders.find(f, {"_id": 0}).to_list(4000)
        key, rev = (SORTS.get(sort) or SORTS["yeni"])[0]
        rows.sort(key=lambda r: r.get(key) or 0, reverse=rev < 0)
        total = len(rows)
        page = [view(o) for o in rows[max(_int(offset), 0):max(_int(offset), 0) + min(max(_int(limit), 1), 200)]]
        allr = await db.yp_orders.find({}, {"_id": 0, "status": 1, "total": 1}).to_list(8000)
        return {"items": page, "total": total, "offset": _int(offset),
                "sum": round(sum(_num(r.get("total")) for r in rows), 2),
                "counts": dict({k: len([r for r in allr if r.get("status") == k]) for k in STATES},
                               hepsi=len(allr), acik=len([r for r in allr if r.get("status") in OPEN])),
                "states": [{"id": k, "name": v} for k, v in STATES.items()],
                "cargos": [{"id": k, "name": v} for k, v in CARGOS.items()],
                "channels": [{"id": k, "name": v[0]} for k, v in CHANNELS.items()]}

    @api_router.get("/yp/orders/{oid}")
    async def order_get(oid: str, _=Depends(require_admin)):
        o = await get_order(oid)
        rets = await db.yp_returns.find({"order": o["id"]}, {"_id": 0}).to_list(50)
        return {"item": view(o), "returns": rets}

    # ------------------------------------------------------------ sipariş oluştur
    @api_router.post("/yp/orders")
    async def order_add(payload: dict, _=Depends(require_admin)):
        items = clean_items(payload.get("items"))
        cust = payload.get("customer") or {}
        name = _t(cust.get("name"), 90)
        if not name:
            raise HTTPException(422, "Müşteri adı gerekli")
        ch = _t(payload.get("channel"), 24) or "site"
        if ch not in CHANNELS:
            raise HTTPException(422, "Satış kanalı geçersiz")
        # ürün kartındaki barkod, stok kodu, alış fiyatı ve kategori satıra kopyalansın:
        # fiş barkodu ve kâr hesabı bunlara bakar
        for it in items:
            if not it.get("product"):
                continue
            pr = await db.yp_products.find_one({"id": it["product"]}, {"_id": 0})
            if not pr:
                continue
            for k, src in (("barcode", "barcode"), ("sku", "sku"), ("cat", "cat"), ("brand", "brand")):
                if not it.get(k):
                    it[k] = _t(pr.get(src), 60)
            if not _num(it.get("cost")):
                it["cost"] = _num(pr.get("cost"))
            if not _num(it.get("vat")):
                it["vat"] = _num(pr.get("vat"), 20.0)
        camps = await db.yp_camps.find({"on": True}, {"_id": 0}).to_list(400)
        phone = _phone(cust.get("phone"))
        past = await db.yp_orders.count_documents({"customer.phone": phone}) if phone else 0
        calc = apply_campaigns({"items": items, "ship": _num(payload.get("ship_fee"))}, camps,
                               {"payment": _t(payload.get("payment"), 20), "code": _t(payload.get("code"), 40),
                                "group": _t(cust.get("group"), 40), "orders": past, "day": _now()[:10]})
        n = await db.yp_orders.count_documents({})
        oid = uuid.uuid4().hex[:12]
        no = _t(payload.get("no"), 30).upper() or next_no(n)
        # stok: hepsi tutuyorsa düş, biri yetmezse hiçbirini düşme
        taken = []
        for it in calc["items"]:
            if not it.get("product"):
                continue
            r = await take_stock(db, it["product"], it["qty"], ch, no)
            if not r.get("ok"):
                for t in taken:
                    await give_stock(db, t["product"], t["qty"], "geri_al", no + "-geri-" + t["product"])
                raise HTTPException(409, "%s: %s" % (it["name"], r.get("err") or "stok düşülemedi"))
            taken.append(it)
        o = {"id": oid, "no": no, "channel": ch, "at": _now(), "seq": n + 1, "status": "yeni",
             "customer": {"name": name, "phone": phone, "email": _t(cust.get("email"), 90),
                          "city": _t(cust.get("city"), 40), "district": _t(cust.get("district"), 40),
                          "address": _t(cust.get("address"), 400), "group": _t(cust.get("group"), 40),
                          "tckn": "", "note": _t(cust.get("note"), 200)},
             "items": calc["items"], "subtotal": calc["subtotal"], "discount": calc["discount"],
             "camps": calc["lines"], "coupon": _t(payload.get("code"), 40).upper(),
             "ship_fee": calc["ship"], "ship_cost": _num(payload.get("ship_cost")),
             "free_ship": calc["free_ship"], "gifts": calc["gifts"], "total": calc["total"],
             "payment": _t(payload.get("payment"), 20), "paid": bool(payload.get("paid")),
             "market_no": _t(payload.get("market_no"), 40).upper(),
             "cargo": {"firm": _t((payload.get("cargo") or {}).get("firm"), 24),
                       "code": _t((payload.get("cargo") or {}).get("code"), 40).upper(),
                       "barcode": _t((payload.get("cargo") or {}).get("barcode"), 40).upper(), "label": ""},
             "invoice": {"no": "", "uuid": "", "state": ""}, "note": _t(payload.get("note"), 400),
             "timeline": [{"at": _now(), "by": "panel", "state": "yeni", "note": "sipariş oluşturuldu"}]}
        await db.yp_orders.insert_one(dict(o))
        for c in calc["lines"]:
            if c.get("id"):
                await db.yp_camps.update_one({"id": c["id"]}, {"$inc": {"limit.used": 1}})
        return {"ok": True, "item": view(o)}

    # ------------------------------------------------------------ durum, kargo, not
    @api_router.post("/yp/orders/{oid}/status")
    async def order_state(oid: str, payload: dict, _=Depends(require_admin)):
        o = await get_order(oid)
        new = _t(payload.get("status"), 20)
        if new not in STATES:
            raise HTTPException(422, "Durum geçersiz")
        cur = o.get("status", "yeni")
        if new == cur:
            return {"ok": True, "item": view(o)}
        if not can_go(cur, new):
            raise HTTPException(422, "%s durumundan %s durumuna geçilemez" % (STATES[cur], STATES[new]))
        if new == "kargoda" and not (o.get("cargo") or {}).get("firm"):
            raise HTTPException(422, "Kargoya vermek için kargo firması seçilmeli")
        if new == "iptal":
            for it in o.get("items") or []:
                if it.get("product"):
                    await give_stock(db, it["product"], it["qty"], "iptal", o["no"] + "-iptal")
            for c in o.get("camps") or []:
                if c.get("id"):
                    await db.yp_camps.update_one({"id": c["id"], "limit.used": {"$gt": 0}},
                                                 {"$inc": {"limit.used": -1}})
        st = {"status": new}
        if new == "teslim":
            st["paid"] = True
            st["delivered_at"] = _now()
        await db.yp_orders.update_one({"id": o["id"]}, {"$set": st})
        await log(o["id"], new, _t(payload.get("note"), 200) or STATES[new])
        return {"ok": True, "item": view(await get_order(o["id"]))}

    @api_router.put("/yp/orders/{oid}")
    async def order_put(oid: str, payload: dict, _=Depends(require_admin)):
        o = await get_order(oid)
        st = {}
        if "cargo" in payload:
            cg = payload.get("cargo") or {}
            firm = _t(cg.get("firm"), 24)
            if firm and firm not in CARGOS:
                raise HTTPException(422, "Kargo firması geçersiz")
            st["cargo"] = {"firm": firm, "code": _t(cg.get("code"), 40).upper(),
                           "barcode": _t(cg.get("barcode"), 40).upper(),
                           "label": _t(cg.get("label"), 300)}
        for k, f in (("note", lambda v: _t(v, 400)), ("payment", lambda v: _t(v, 20)),
                     ("paid", bool), ("ship_cost", _num),
                     ("market_no", lambda v: _t(v, 40).upper())):
            if k in payload:
                st[k] = f(payload[k])
        if "customer" in payload:
            c = dict(o.get("customer") or {})
            for k, n in (("name", 90), ("email", 90), ("city", 40), ("district", 40),
                         ("address", 400), ("note", 200), ("group", 40)):
                if k in (payload.get("customer") or {}):
                    c[k] = _t(payload["customer"][k], n)
            if (payload.get("customer") or {}).get("phone"):
                c["phone"] = _phone(payload["customer"]["phone"])
            st["customer"] = c
        if not st:
            raise HTTPException(422, "Değişiklik yok")
        await db.yp_orders.update_one({"id": o["id"]}, {"$set": st})
        if "cargo" in st and st["cargo"].get("code"):
            await log(o["id"], o.get("status", ""), "kargo kodu: %s" % st["cargo"]["code"])
        return {"ok": True, "item": view(await get_order(o["id"]))}

    # ------------------------------------------------------------ toplu işlem
    @api_router.post("/yp/orders/bulk")
    async def order_bulk(payload: dict, _=Depends(require_admin)):
        """Seçili siparişlerde toplu değişiklik: durum, kargo firması, ödeme işareti, not.

        Her sipariş kendi akış kuralına göre değerlendirilir; uymayan sipariş atlanır ve
        sebebiyle birlikte geri bildirilir. Böylece 40 siparişlik bir seçimde tek bir
        uygunsuz kayıt yüzünden işlem yarıda kalmaz."""
        ids = [_t(i, 24) for i in (payload.get("ids") or [])][:2000]
        op = _t(payload.get("op"), 20)
        if not ids or op not in ("status", "cargo", "paid", "note"):
            raise HTTPException(422, "Yapılacak işlemi ve siparişleri seçin")
        new = _t(payload.get("status"), 20)
        if op == "status" and new not in STATES:
            raise HTTPException(422, "Durum geçersiz")
        firm = _t((payload.get("cargo") or {}).get("firm"), 24)
        if op == "cargo" and firm and firm not in CARGOS:
            raise HTTPException(422, "Kargo firması geçersiz")
        done, skip = 0, []
        for oid in ids:
            o = await db.yp_orders.find_one({"id": oid}, {"_id": 0})
            if not o:
                continue
            no, cur = o.get("no", ""), o.get("status", "yeni")
            if op == "status":
                if new == cur:
                    continue
                if not can_go(cur, new):
                    skip.append({"no": no, "why": "%s → %s geçişi yok" % (STATES[cur], STATES[new])})
                    continue
                if new == "kargoda" and not (o.get("cargo") or {}).get("firm"):
                    skip.append({"no": no, "why": "kargo firması seçilmemiş"})
                    continue
                if new == "iptal":
                    for it in o.get("items") or []:
                        if it.get("product"):
                            await give_stock(db, it["product"], it["qty"], "iptal", no + "-iptal")
                    for c in o.get("camps") or []:
                        if c.get("id"):
                            await db.yp_camps.update_one({"id": c["id"], "limit.used": {"$gt": 0}},
                                                         {"$inc": {"limit.used": -1}})
                st = {"status": new}
                if new == "teslim":
                    st["paid"] = True
                    st["delivered_at"] = _now()
                await db.yp_orders.update_one({"id": oid}, {"$set": st})
                await log(oid, new, "toplu işlem")
            elif op == "cargo":
                if cur in ("teslim", "iptal"):
                    skip.append({"no": no, "why": "%s siparişte kargo değişmez" % STATES[cur]})
                    continue
                cg = dict(o.get("cargo") or {})
                cg["firm"] = firm or cg.get("firm", "")
                await db.yp_orders.update_one({"id": oid}, {"$set": {"cargo": cg}})
                await log(oid, cur, "kargo firması: %s" % CARGOS.get(cg["firm"], "—"))
            elif op == "paid":
                await db.yp_orders.update_one({"id": oid}, {"$set": {"paid": bool(payload.get("on", True))}})
                await log(oid, cur, "ödeme işaretlendi" if payload.get("on", True) else "ödeme işareti kaldırıldı")
            else:
                await db.yp_orders.update_one({"id": oid}, {"$set": {"note": _t(payload.get("note"), 400)}})
            done += 1
        return {"ok": True, "n": done, "skipped": skip,
                "msg": "%d sipariş güncellendi%s" % (done, (", %d tanesi atlandı" % len(skip)) if skip else "")}

    @api_router.post("/yp/orders/print")
    async def order_print(payload: dict, _=Depends(require_admin)):
        """Toplu kargo fişi veya sipariş fişi: yazdırmaya hazır tek sayfa."""
        ids = [_t(i, 24) for i in (payload.get("ids") or [])][:200]
        kind = "kargo" if _t(payload.get("kind"), 10) != "siparis" else "siparis"
        if not ids:
            raise HTTPException(422, "Fişi yazdırılacak siparişleri seçin")
        rows = [view(o) for o in await db.yp_orders.find({"id": {"$in": ids}}, {"_id": 0}).to_list(200)]
        if not rows:
            raise HTTPException(404, "Sipariş bulunamadı")
        rows.sort(key=lambda o: ids.index(o["id"]) if o["id"] in ids else 0)
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        return {"ok": True, "n": len(rows), "kind": kind,
                "html": fis_html(rows, kind, g.get("company_name") or "")}

    @api_router.post("/yp/orders/export")
    async def order_export(payload: dict, _=Depends(require_admin)):
        """Seçili siparişleri Excel'in açabildiği CSV olarak ver."""
        ids = [_t(i, 24) for i in (payload.get("ids") or [])][:5000]
        q = {"id": {"$in": ids}} if ids else {}
        rows = [view(o) for o in await db.yp_orders.find(q, {"_id": 0}).to_list(5000)]
        rows.sort(key=lambda o: o.get("seq") or 0, reverse=True)
        head = ["Sipariş no", "Tarih", "Durum", "Kanal", "Müşteri", "Telefon", "İl", "Adres",
                "Ürünler", "Adet", "Ara toplam", "İndirim", "Kargo", "Toplam", "Net kâr",
                "Kargo firması", "Takip no", "Ödeme", "Not"]
        def cell(v):
            t = str(v if v is not None else "").replace('"', '""').replace("\n", " ")
            return '"%s"' % t
        lines = [";".join(head)]
        for o in rows:
            c = o.get("customer") or {}
            cg = o.get("cargo") or {}
            lines.append(";".join(cell(x) for x in [
                o.get("no"), str(o.get("at") or "")[:16].replace("T", " "), o.get("state_name"),
                o.get("channel_name"), c.get("name"), c.get("phone"), c.get("city"), c.get("address"),
                " + ".join("%s x%d" % (i.get("name"), _int(i.get("qty"), 1)) for i in o.get("items") or []),
                o.get("qty"), o.get("subtotal"), o.get("discount"), o.get("ship_fee"), o.get("total"),
                o.get("profit"), CARGOS.get(cg.get("firm", ""), ""), cg.get("code"),
                "Ödendi" if o.get("paid") else "Bekliyor", o.get("note")]))
        return {"ok": True, "n": len(rows), "name": "siparisler-%s.csv" % _now()[:10],
                "csv": "\ufeff" + "\n".join(lines)}

    # ------------------------------------------------------------ iade
    @api_router.get("/yp/returns")
    async def ret_list(state: str = "", q: str = "", _=Depends(require_admin)):
        f = {}
        if state in RSTATES:
            f["state"] = state
        rows = await db.yp_returns.find(f, {"_id": 0}).to_list(2000)
        qq = _t(q, 60).upper()
        if qq:
            rows = [r for r in rows if qq in (r.get("no", "") + r.get("order_no", "")).upper()]
        rows.sort(key=lambda r: r.get("at") or "", reverse=True)
        for r in rows:
            r["state_name"] = RSTATES.get(r.get("state"), "")
        allr = await db.yp_returns.find({}, {"_id": 0, "state": 1}).to_list(4000)
        return {"items": rows, "counts": dict({k: len([x for x in allr if x.get("state") == k]) for k in RSTATES},
                                              hepsi=len(allr)),
                "states": [{"id": k, "name": v} for k, v in RSTATES.items()], "reasons": list(RREASONS)}

    @api_router.post("/yp/returns")
    async def ret_add(payload: dict, _=Depends(require_admin)):
        o = await get_order(_t(payload.get("order"), 24))
        if o.get("status") == "iptal":
            raise HTTPException(422, "İptal edilmiş siparişin iadesi olmaz")
        have = {i.get("product") or i.get("name"): _int(i.get("qty"), 1) for i in o.get("items") or []}
        done = {}
        for r in await db.yp_returns.find({"order": o["id"], "state": {"$in": ["talep", "onay", "tamam"]}},
                                          {"_id": 0}).to_list(50):
            for it in r.get("items") or []:
                k = it.get("product") or it.get("name")
                done[k] = done.get(k, 0) + _int(it.get("qty"), 1)
        items = []
        for it in (payload.get("items") or [])[:80]:
            k = _t((it or {}).get("product"), 24) or _t((it or {}).get("name"), 140)
            qty = max(_int(it.get("qty"), 1), 1)
            if k not in have:
                raise HTTPException(422, "Bu ürün siparişte yok")
            if done.get(k, 0) + qty > have[k]:
                raise HTTPException(422, "İade adedi sipariş adedini geçemez (%d adet satıldı)" % have[k])
            src = [i for i in o["items"] if (i.get("product") or i.get("name")) == k][0]
            items.append({"product": src.get("product", ""), "name": src.get("name", ""), "qty": qty,
                          "price": _num(src.get("price")), "reason": _t(it.get("reason"), 40) or "diger"})
        if not items:
            raise HTTPException(422, "İade edilecek ürün seçilmeli")
        n = await db.yp_returns.count_documents({})
        r = {"id": uuid.uuid4().hex[:12], "no": "IA-%s-%05d" % (_now()[:4], n + 1), "order": o["id"],
             "order_no": o.get("no", ""), "customer": (o.get("customer") or {}).get("name", ""),
             "phone": (o.get("customer") or {}).get("phone", ""), "items": items,
             "reason": _t(payload.get("reason"), 40) or items[0]["reason"],
             "detail": _t(payload.get("detail"), 400), "state": "talep",
             "refund": round(sum(_num(i["price"]) * i["qty"] for i in items), 2),
             "cargo": _t(payload.get("cargo"), 24), "at": _now(), "seq": n + 1,
             "timeline": [{"at": _now(), "by": "panel", "state": "talep", "note": "iade talebi alındı"}]}
        await db.yp_returns.insert_one(dict(r))
        return {"ok": True, "item": r}

    @api_router.post("/yp/returns/{rid}/state")
    async def ret_state(rid: str, payload: dict, _=Depends(require_admin)):
        r = await db.yp_returns.find_one({"id": _t(rid, 24)}, {"_id": 0})
        if not r:
            raise HTTPException(404, "İade bulunamadı")
        new = _t(payload.get("state"), 20)
        if new not in RSTATES:
            raise HTTPException(422, "İade durumu geçersiz")
        cur = r.get("state", "talep")
        allow = {"talep": ("onay", "red"), "onay": ("tamam",), "red": (), "tamam": ()}
        if new != cur and new not in allow.get(cur, ()):
            raise HTTPException(422, "%s durumundan %s durumuna geçilemez" % (RSTATES[cur], RSTATES[new]))
        if new == "onay":
            # onayda ürün rafa döner: stok geri eklenir ve açık pazaryerlerine bildirilir
            for it in r.get("items") or []:
                if it.get("product"):
                    await give_stock(db, it["product"], it["qty"], "iade", r["no"])
        st = {"state": new}
        if new == "tamam":
            st["refund_at"] = _now()
            st["refund"] = _num(payload.get("refund"), r.get("refund"))
        await db.yp_returns.update_one({"id": r["id"]}, {"$set": st, "$push": {"timeline": {
            "at": _now(), "by": "panel", "state": new, "note": _t(payload.get("note"), 200) or RSTATES[new]}}})
        return {"ok": True, "item": await db.yp_returns.find_one({"id": r["id"]}, {"_id": 0})}

    # ------------------------------------------------------------ rapor
    @api_router.get("/yp/orders/report/ozet")
    async def order_report(frm: str = "", to: str = "", _=Depends(require_admin)):
        f = {}
        if frm or to:
            f["at"] = {}
            if frm:
                f["at"]["$gte"] = _t(frm, 10)
            if to:
                f["at"]["$lte"] = _t(to, 10) + "T23:59:59"
        rows = await db.yp_orders.find(f, {"_id": 0}).to_list(8000)
        live = [o for o in rows if o.get("status") != "iptal"]
        rets = await db.yp_returns.find({"state": {"$in": ["onay", "tamam"]}}, {"_id": 0}).to_list(4000)
        ch, days = {}, {}
        for o in live:
            k = o.get("channel", "site")
            c = ch.setdefault(k, {"id": k, "name": dict(CHANNELS).get(k, (k, 0))[0], "n": 0, "sum": 0.0, "profit": 0.0})
            c["n"] += 1
            c["sum"] = round(c["sum"] + _num(o.get("total")), 2)
            c["profit"] = round(c["profit"] + order_profit(o), 2)
            d = days.setdefault(str(o.get("at"))[:10], {"day": str(o.get("at"))[:10], "n": 0, "sum": 0.0})
            d["n"] += 1
            d["sum"] = round(d["sum"] + _num(o.get("total")), 2)
        ciro = round(sum(_num(o.get("total")) for o in live), 2)
        kar = round(sum(order_profit(o) for o in live), 2)
        iade = round(sum(_num(r.get("refund")) for r in rets), 2)
        top = {}
        for o in live:
            for it in o.get("items") or []:
                t = top.setdefault(it.get("name", ""), {"name": it.get("name", ""), "qty": 0, "sum": 0.0})
                t["qty"] += _int(it.get("qty"), 1)
                t["sum"] = round(t["sum"] + _num(it.get("price")) * _int(it.get("qty"), 1), 2)
        return {"n": len(live), "ciro": ciro, "kar": kar, "iade": iade, "iade_n": len(rets),
                "sepet": round(ciro / len(live), 2) if live else 0.0,
                "iptal": len([o for o in rows if o.get("status") == "iptal"]),
                "indirim": round(sum(_num(o.get("discount")) for o in live), 2),
                "kanallar": sorted(ch.values(), key=lambda c: -c["sum"]),
                "gunler": sorted(days.values(), key=lambda d: d["day"]),
                "urunler": sorted(top.values(), key=lambda t: -t["qty"])[:20],
                "durumlar": [{"id": k, "name": v, "n": len([o for o in rows if o.get("status") == k])}
                             for k, v in STATES.items()]}

    return api_router
