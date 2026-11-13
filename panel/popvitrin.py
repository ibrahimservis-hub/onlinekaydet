# -*- coding: utf-8 -*-
"""Popup ürün vitrini: sitede gecikmeyle (ya da çıkışa yönelince) açılan, seçili ürünleri gösteren pencere.

Ürünler mağazadan canlı gelir: indirimli, yeni gelen, çok satan ya da elle seçilen. Stokta olmayan ürün gösterilmez.
Ziyaretçi kapatınca ayarlanan sıklıkta (oturumda bir / günde bir / her sayfa) tekrar görünmez. Mağaza kapalıysa hiç çıkmaz."""
import html as _h
import re
import zlib

from fastapi import Depends, HTTPException

import realimg

DEF = {"on": False, "kural": "indirimli", "ids": [], "adet": 4, "baslik": "Kaçırmayın", "alt": "Sizin için seçtiğimiz ürünler",
       "buton": "Tüm ürünler", "gecikme": 6, "cikis": True, "siklik": "oturum", "sayfa": "hepsi"}
KURALLAR = {"indirimli": "İndirimli ürünler", "yeni": "Yeni gelenler", "cok_satan": "Çok satanlar", "secili": "Benim seçtiklerim"}
SIKLIK = {"oturum": "Ziyarette bir kez", "gun": "Günde bir kez", "her": "Her sayfada"}
SAYFA = {"hepsi": "Tüm sayfalar", "ana": "Yalnız ana sayfa"}
_KR = [(k, re.compile(rx)) for k, rx in realimg.KINDS]


async def get_cfg(db):
    d = await db.app_settings.find_one({"_id": "yp_popvitrin"}, {"_id": 0}) or {}
    return dict(DEF, **{k: v for k, v in d.items() if k in DEF})


def _stokta(p):
    return (not p.get("track_stock", True)) or (p.get("stock") or 0) > 0


def _img(p):
    im = (p.get("images") or [""])[0]
    if im:
        return im
    s = ("%s %s" % (p.get("name") or "", p.get("category") or "")).lower().replace("İ", "i")
    for k, rx in _KR:
        if rx.search(s):
            return "/tema-urun/%s%d.jpg" % (k, zlib.crc32(s.encode()) % 3 + 1)
    return ""


async def urunler(db, c):
    """Kurala göre gösterilecek ürünler (en fazla c['adet'])."""
    n = max(1, min(int(c.get("adet") or 4), 8))
    rows = [p for p in await db.shop_products.find({"active": True}, {"_id": 0}).to_list(5000) if _stokta(p)]
    k = c.get("kural")
    if k == "secili":
        by = {p["id"]: p for p in rows}
        rows = [by[i] for i in (c.get("ids") or []) if i in by]
    elif k == "yeni":
        rows.sort(key=lambda p: p.get("created_at") or "", reverse=True)
    elif k == "cok_satan":
        rows.sort(key=lambda p: (p.get("sold") or 0, p.get("created_at") or ""), reverse=True)
        rows = [p for p in rows if (p.get("sold") or 0) > 0] or rows
    else:
        rows = [p for p in rows if (p.get("old_price") or 0) > (p.get("price") or 0)]
        rows.sort(key=lambda p: 1 - p["price"] / p["old_price"], reverse=True)
    return rows[:n]


def _tl(v):
    s = ("%.2f" % float(v or 0)).rstrip("0").rstrip(".")
    a, _, b = s.partition(".")
    a = "{:,}".format(int(a)).replace(",", ".")
    return a + ("," + b if b else "") + " ₺"


def render_html(c, prods, path="/"):
    """Sayfa sonuna eklenecek parça; gösterilecek bir şey yoksa ''."""
    if not c.get("on") or not prods:
        return ""
    p0 = (path or "/").split("?")[0]
    if p0.startswith(("/hesabim", "/magaza/odeme")) or (c.get("sayfa") == "ana" and p0.strip("/") != ""):
        return ""
    key = "okpv" + str(zlib.crc32(("%s|%s|%s" % (c.get("kural"), ",".join(p["id"] for p in prods), c.get("baslik"))).encode()))
    E = lambda s: _h.escape(str(s or ""))  # noqa: E731
    kart = []
    for p in prods:
        u = "/magaza/urun/" + E(p.get("slug") or p["id"])
        im = _img(p)
        dc = int(round((1 - p["price"] / p["old_price"]) * 100)) if (p.get("old_price") or 0) > (p.get("price") or 0) else 0
        kart.append('<a class="pvpc" href="%s"><span class="pvim">%s%s</span><span class="pvnm">%s</span><span class="pvpr"><b>%s</b>%s</span></a>' % (
            u, ('<img loading="lazy" alt="%s" src="%s">' % (E(p["name"]), E(im))) if im else "",
            ('<i>%%%d</i>' % dc) if dc else "", E(p["name"]), _tl(p["price"]),
            ("<s>%s</s>" % _tl(p["old_price"])) if dc else ""))
    sik = c.get("siklik") if c.get("siklik") in SIKLIK else "oturum"
    gec = max(0, min(int(c.get("gecikme") or 0), 120))
    css = ("<style>#K{position:fixed;inset:0;z-index:9650;background:#0009;display:none;align-items:center;justify-content:center;padding:16px}"
           "#K.on{display:flex;animation:K-f .25s ease}@keyframes K-f{from{opacity:0}to{opacity:1}}"
           "#K .pvbx:focus{outline:none}#K .pvbx{background:var(--fbg,var(--bg,#fff));color:var(--ink,#0f172a);width:min(760px,100%);max-height:calc(100vh - 32px);overflow:auto;border-radius:var(--r,16px);padding:24px;position:relative;font-family:var(--fb,system-ui,sans-serif);box-shadow:0 24px 60px #0005}"
           "#K h2{margin:0 44px 4px 0;font:800 clamp(1.25rem,3vw,1.7rem)/1.2 var(--fd,inherit)}#K .pval{margin:0 0 16px;opacity:.72}"
           "#K .pvx{position:absolute;top:8px;right:8px;width:44px;height:44px;border:0;background:none;color:inherit;font-size:26px;cursor:pointer;border-radius:50%}"
           "#K .pvgr{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}"
           "#K .pvpc{display:flex;flex-direction:column;gap:6px;text-decoration:none;color:inherit;border:1px solid #8883;border-radius:12px;padding:8px;transition:transform .15s,box-shadow .15s}"
           "#K .pvpc:hover{transform:translateY(-2px);box-shadow:0 8px 20px #0002}#K .pvim{aspect-ratio:1/1;border-radius:8px;overflow:hidden;background:#8881;position:relative;display:block}"
           "#K .pvim img{width:100%;height:100%;object-fit:cover;display:block}#K .pvim i{position:absolute;left:6px;top:6px;background:#dc2626;color:#fff;font:700 12px/1 system-ui;padding:4px 7px;border-radius:99px;font-style:normal}"
           "#K .pvnm{font-weight:600;font-size:.92rem;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}"
           "#K .pvpr b{font-weight:800}#K .pvpr s{opacity:.55;margin-left:6px;font-size:.85em}"
           "#K .pvft{margin-top:16px;display:flex;justify-content:center}#K .pvft a{display:inline-flex;align-items:center;min-height:44px;padding:0 22px;border-radius:var(--r,10px);background:var(--ac,#0a1f44);color:var(--on-ac,#fff);font-weight:700;text-decoration:none}"
           "@media(max-width:560px){#K{align-items:flex-end;padding:0}#K .pvbx{border-radius:18px 18px 0 0;padding:20px 16px calc(16px + env(safe-area-inset-bottom))}#K .pvgr{grid-template-columns:repeat(2,1fr)}}"
           "@media(prefers-reduced-motion:reduce){#K.on{animation:none}#K .pvpc{transition:none}}</style>").replace("K", key)
    body = ('<div id="%s" role="dialog" aria-modal="true" aria-labelledby="%s-h"><div class="pvbx" tabindex="-1"><button class="pvx" type="button" aria-label="Kapat">×</button>'
            '<h2 id="%s-h">%s</h2>%s<div class="pvgr">%s</div><div class="pvft"><a href="/magaza">%s</a></div></div></div>') % (
        key, key, key, E(c.get("baslik") or "Kaçırmayın"), ('<p class="pval">%s</p>' % E(c["alt"])) if c.get("alt") else "",
        "".join(kart), E(c.get("buton") or "Tüm ürünler"))
    js = ("<script>(function(){var k='%s',s='%s',e=document.getElementById(k);if(!e)return;"
          "var st=s==='gun'?localStorage:sessionStorage,now=new Date().toISOString().slice(0,10);"
          "try{var v=st.getItem(k);if(s!=='her'&&v&&(s!=='gun'||v===now)){e.remove();return}}catch(x){}"
          "var shown=0,show=function(){if(shown)return;shown=1;e.classList.add('on');var b=e.querySelector('.pvbx');if(b)b.focus({preventScroll:true})},"
          "hide=function(){e.classList.remove('on');try{st.setItem(k,now)}catch(x){}};"
          "e.querySelector('.pvx').onclick=hide;e.addEventListener('click',function(v){if(v.target===e)hide()});"
          "document.addEventListener('keydown',function(v){if(v.key==='Escape'&&e.classList.contains('on'))hide()});"
          "[].forEach.call(e.querySelectorAll('a'),function(a){a.addEventListener('click',function(){try{st.setItem(k,now)}catch(x){}})});"
          "%s%s})()</script>") % (key, sik, ("setTimeout(show,%d);" % (gec * 1000)) if gec or not c.get("cikis") else "",
                                  "if(matchMedia('(pointer:fine)').matches)document.addEventListener('mouseout',function(v){if(!v.relatedTarget&&v.clientY<8)show()});" if c.get("cikis") else "")
    return css + body + js


def register(api_router, db, deps):
    adm = deps["require_admin"]

    def out(c):
        return dict(c, kurallar=KURALLAR, sikliklar=SIKLIK, sayfalar=SAYFA)

    @api_router.get("/yp/popvitrin")
    async def pv_get(_: dict = Depends(adm)):
        c = await get_cfg(db)
        o = out(c)
        o["onizleme"] = [{"id": p["id"], "name": p["name"], "price": p.get("price"), "img": _img(p)} for p in await urunler(db, c)]
        sec = {p["id"]: p for p in await db.shop_products.find({"id": {"$in": c.get("ids") or []}}, {"_id": 0, "id": 1, "name": 1, "price": 1}).to_list(50)}
        o["secili"] = [sec[i] for i in c.get("ids") or [] if i in sec]
        f = await db.app_settings.find_one({"_id": "site_features"}, {"_id": 0, "shop_enabled": 1}) or {}
        o["magaza_acik"] = bool(f.get("shop_enabled"))
        return o

    @api_router.get("/yp/popvitrin/ara")
    async def pv_ara(q: str = "", _: dict = Depends(adm)):
        q = q.strip().lower()
        rows = await db.shop_products.find({"active": True}, {"_id": 0, "id": 1, "name": 1, "price": 1, "sku": 1, "stock": 1, "track_stock": 1}).to_list(5000)
        rows = [r for r in rows if not q or q in (r.get("name") or "").lower() or q in (r.get("sku") or "").lower()]
        return {"rows": [{"id": r["id"], "name": r["name"], "price": r.get("price"), "stokta": _stokta(r)} for r in rows[:20]]}

    @api_router.put("/yp/popvitrin")
    async def pv_put(payload: dict, _: dict = Depends(adm)):
        c = await get_cfg(db)
        for k in ("on", "cikis"):
            if k in payload:
                c[k] = bool(payload[k])
        for k, allowed in (("kural", KURALLAR), ("siklik", SIKLIK), ("sayfa", SAYFA)):
            if k in payload:
                if payload[k] not in allowed:
                    raise HTTPException(422, "Geçersiz seçim")
                c[k] = payload[k]
        for k, n in (("baslik", 60), ("alt", 120), ("buton", 30)):
            if k in payload:
                c[k] = str(payload[k] or "").strip()[:n]
        if "adet" in payload:
            c["adet"] = max(1, min(int(payload.get("adet") or 4), 8))
        if "gecikme" in payload:
            c["gecikme"] = max(0, min(int(payload.get("gecikme") or 0), 120))
        if "ids" in payload:
            c["ids"] = [str(i)[:40] for i in (payload.get("ids") or [])][:8]
        if c["on"] and c["kural"] == "secili" and not c["ids"]:
            raise HTTPException(422, "Gösterilecek en az bir ürün seçin")
        await db.app_settings.update_one({"_id": "yp_popvitrin"}, {"$set": c}, upsert=True)
        return await pv_get(_)
