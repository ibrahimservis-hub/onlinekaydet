# -*- coding: utf-8 -*-
"""İlan modülü (emlak, araç kiralama, tur/transfer gibi ilan vitrini olan sektörler).
Panel: /api/admin/listings (ekle, düzenle, sil, yayında/taslak). Herkese açık: /api/public/listings, resimler /api/public/listings/<id>/img/<n>.
Siteye /ilanlar ve /ilan/<ad> sayfaları siteedit.render içinden eklenir (sunucuda üretilir, arama motoru görür)."""
import base64
import re
import time
import uuid
from html import escape as E

from fastapi import Depends, HTTPException
from fastapi.responses import Response

KINDS = {"satilik": "Satılık", "kiralik": "Kiralık", "devren": "Devren", "gunluk": "Günlük kiralık"}
CATS = ["Daire", "Villa", "Müstakil ev", "Arsa", "İş yeri", "Dükkan", "Ofis", "Bina", "Araç", "Tur", "Diğer"]
ILAN_SECTORS = {"emlakci", "arac_kiralama", "transfer", "tur_organizasyon"}
MAX_IMG = 8
MAX_IMG_B64 = 900_000
_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def slugify(s, n=50):
    s = re.sub(r"[^a-z0-9]+", "-", str(s or "").translate(_TR).lower()).strip("-")
    return (s[:n].strip("-")) or "ilan"


def _num(v, lo=0, hi=10 ** 12):
    try:
        x = float(str(v).replace(",", ".").replace(" ", ""))
    except ValueError:
        return 0
    return max(lo, min(hi, x))


def clean(p, old=None):
    """Panelden gelen kaydı doğrular. Hatalıysa ValueError."""
    t = str(p.get("title") or "").strip()[:140]
    if len(t) < 5:
        raise ValueError("Başlık en az 5 karakter olmalı")
    kind = p.get("kind") if p.get("kind") in KINDS else "satilik"
    imgs = []
    for x in (p.get("images") or [])[:MAX_IMG]:
        x = str(x or "")
        if not x.startswith("data:image/") or ";base64," not in x:
            continue
        if len(x) > MAX_IMG_B64:
            raise ValueError("Resim çok büyük (en fazla ~600 KB); küçültüp tekrar yükleyin")
        imgs.append(x)
    feats = [str(f).strip()[:40] for f in (p.get("features") or []) if str(f).strip()][:20]
    out = {
        "title": t, "kind": kind, "category": str(p.get("category") or "Daire")[:30],
        "price": _num(p.get("price")), "city": str(p.get("city") or "").strip()[:40], "district": str(p.get("district") or "").strip()[:40],
        "neighborhood": str(p.get("neighborhood") or "").strip()[:60],
        "rooms": str(p.get("rooms") or "").strip()[:12], "m2": _num(p.get("m2"), 0, 100000), "floor": str(p.get("floor") or "").strip()[:12],
        "age": str(p.get("age") or "").strip()[:12], "heating": str(p.get("heating") or "").strip()[:30],
        "description": str(p.get("description") or "").strip()[:5000], "features": feats, "images": imgs,
        "status": p.get("status") if p.get("status") in ("yayinda", "taslak", "satildi") else "yayinda",
        "featured": bool(p.get("featured")),
    }
    return out


def public_item(d, full=False):
    o = {k: d.get(k) for k in ("id", "slug", "title", "kind", "category", "price", "city", "district", "neighborhood", "rooms", "m2", "floor", "age", "heating", "features", "status", "featured")}
    o["kind_label"] = KINDS.get(d.get("kind"), "")
    o["img_count"] = len(d["images"]) if "images" in d else int(d.get("img_count") or 0)
    if full:
        o["description"] = d.get("description", "")
    return o


def tl(n):
    return "{:,.0f}".format(n or 0).replace(",", ".") + " ₺"


CSS = """<style>.okl{padding:clamp(96px,11vw,130px) 0 clamp(28px,4vw,56px);color:var(--ink);font-family:var(--fb,inherit);--c:var(--ac,#0a1f44)}.okl *{box-sizing:border-box}
.okl h1{font:800 clamp(1.5rem,3vw,2.2rem)/1.15 var(--fd,inherit);margin:0 0 6px}.okl .sub{color:var(--mut);margin:0 0 18px}
.okl .bar{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 20px}.okl .bar button{padding:0 16px;min-height:44px;display:inline-flex;align-items:center;border:1px solid var(--ln);border-radius:99px;background:none;cursor:pointer;color:inherit;font-weight:700;font-size:.9rem}.okl .bar button.on{background:var(--c);color:var(--on-ac,#fff);border-color:var(--c)}
.okl .g{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.okl .cd{display:block;text-decoration:none;color:inherit;border:1px solid var(--ln);border-radius:calc(var(--r,12px)*1.2);overflow:hidden;background:var(--fbg,#fff);transition:.2s}.okl .cd:hover{transform:translateY(-3px);box-shadow:0 18px 34px -20px #0006}
.okl .im{position:relative;aspect-ratio:4/3;background:var(--sf)}.okl .im img{width:100%;height:100%;object-fit:cover;display:block}.okl .bd{position:absolute;left:10px;top:10px;background:var(--c);color:var(--on-ac,#fff);font:700 .74rem var(--fb,inherit);padding:5px 10px;border-radius:99px}.okl .bd.s{background:#dc2626;color:#fff}
.okl .in{padding:14px;display:grid;gap:6px}.okl .in h3{margin:0;font:700 1rem/1.3 var(--fd,inherit)}.okl .pr{font:800 1.25rem var(--fd,inherit)}.okl .mt{font-size:.84rem;color:var(--mut);display:flex;gap:10px;flex-wrap:wrap}
.okl .top{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:clamp(20px,4vw,44px);align-items:start}.okl .mn{aspect-ratio:4/3;border-radius:calc(var(--r,12px)*1.3);overflow:hidden;background:var(--sf);border:1px solid var(--ln)}.okl .mn img{width:100%;height:100%;object-fit:cover;display:block}
.okl .th{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.okl .th img{width:76px;height:58px;object-fit:cover;border-radius:8px;border:2px solid transparent;cursor:pointer}.okl .th img.on{border-color:var(--c)}
.okl .sp{width:100%;border-collapse:collapse;margin:14px 0}.okl .sp td{padding:10px 4px;border-bottom:1px solid var(--ln);font-size:.92rem}.okl .sp td:first-child{color:var(--mut);width:42%}
.okl .ch{display:flex;gap:8px;flex-wrap:wrap}.okl .ch span{padding:6px 12px;border:1px solid var(--ln);border-radius:99px;font-size:.84rem;background:var(--sf)}
.okl .ct{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}.okl .b1,.okl .b2{min-height:52px;padding:0 22px;border-radius:var(--r,10px);font:700 1rem var(--fb,inherit);text-decoration:none;display:inline-flex;align-items:center;justify-content:center;flex:1;min-width:150px}.okl .b1{background:var(--c);color:var(--on-ac,#fff)}.okl .b2{border:1.5px solid var(--ink);color:inherit}
.okl .em{padding:40px 10px;text-align:center;color:var(--mut)}
@media(max-width:900px){.okl .g{grid-template-columns:repeat(2,1fr)}.okl .top{grid-template-columns:1fr}}@media(max-width:520px){.okl .g{grid-template-columns:1fr}}</style>"""


def list_body(items, kind=""):
    kinds = [k for k in KINDS if any(i.get("kind") == k for i in items)]
    tabs = ('<div class="bar" id="okl-bar"><button type="button" class="on" data-k="">Tümü</button>%s</div>' % "".join('<button type="button" data-k="%s">%s</button>' % (k, KINDS[k]) for k in kinds)) if len(kinds) > 1 else ""
    cards = "".join(
        '<a class="cd" data-k="%s" href="/ilan/%s"><div class="im">%s<span class="bd%s">%s</span></div><div class="in"><h3>%s</h3><div class="pr">%s</div><div class="mt">%s</div></div></a>' % (
            E(i.get("kind") or ""), E(i["slug"]), ('<img loading="lazy" alt="%s" src="/api/public/listings/%s/img/0">' % (E(i["title"]), E(i["id"]))) if i.get("img_count") else "",
            " s" if i.get("status") == "satildi" else "", "Satıldı" if i.get("status") == "satildi" else E(i.get("kind_label") or ""), E(i["title"]), tl(i.get("price")) if i.get("price") else "Fiyat sorunuz",
            "".join("<span>%s</span>" % E(x) for x in [i.get("rooms") or "", ("%g m²" % i["m2"]) if i.get("m2") else "", ", ".join(x for x in (i.get("neighborhood"), i.get("district"), i.get("city")) if x)] if x))
        for i in items)
    js = ('<script>(function(){var b=document.getElementById("okl-bar");if(!b)return;b.onclick=function(e){var x=e.target.closest("button");if(!x)return;[].forEach.call(b.children,function(y){y.classList.toggle("on",y===x)});'
          '[].forEach.call(document.querySelectorAll(".okl .cd"),function(c){c.style.display=(!x.dataset.k||c.dataset.k===x.dataset.k)?"":"none"})}})();</script>')
    return CSS + '<section class="okl"><div class="w"><h1>İlanlarımız</h1><p class="sub">Güncel portföyümüz. İlgilendiğiniz ilan için bize yazın ya da yer gösterme randevusu alın.</p>%s%s</div></section>%s' % (
        tabs, ('<div class="g">%s</div>' % cards) if cards else '<div class="em">Şu an yayında ilan yok. Aradığınızı bize yazın, size uygun seçenekleri bulalım.</div>', js)


def detail_body(d, tel="", wa=""):
    i = public_item(d, True)
    n = i["img_count"]
    gal = ('<div class="mn" id="okl-mn"><img alt="%s" src="/api/public/listings/%s/img/0"></div>' % (E(i["title"]), E(i["id"]))) if n else '<div class="mn"></div>'
    if n > 1:
        gal += '<div class="th">%s</div>' % "".join('<img class="%s" alt="Görsel %d" src="/api/public/listings/%s/img/%d" data-n="%d">' % ("on" if k == 0 else "", k + 1, E(i["id"]), k, k) for k in range(n))
    rows = [("İlan türü", i["kind_label"]), ("Kategori", i["category"]), ("Konum", ", ".join(x for x in (i["neighborhood"], i["district"], i["city"]) if x)), ("Oda sayısı", i["rooms"]),
            ("Brüt m²", ("%g" % i["m2"]) if i["m2"] else ""), ("Bulunduğu kat", i["floor"]), ("Bina yaşı", i["age"]), ("Isıtma", i["heating"])]
    table = '<table class="sp">%s</table>' % "".join("<tr><td>%s</td><td>%s</td></tr>" % (E(a), E(b)) for a, b in rows if b)
    feats = ('<div class="ch">%s</div>' % "".join("<span>%s</span>" % E(f) for f in i["features"])) if i["features"] else ""
    ct = ""
    if i.get("status") != "satildi":
        ct = '<div class="ct"><a class="b1" href="/#randevu">Yer gösterme randevusu</a>%s%s</div>' % (('<a class="b2" href="https://wa.me/90%s?text=%s">WhatsApp</a>' % (wa or tel, E("%s ilanı hakkında bilgi almak istiyorum." % i["title"]))) if (wa or tel) else "", ('<a class="b2" href="tel:+90%s">Ara</a>' % tel) if tel else "")
    else:
        ct = '<p class="sub" style="margin-top:14px"><b>Bu ilan satılmıştır.</b> Benzer portföy için bize yazın.</p>'
    js = '<script>(function(){var m=document.getElementById("okl-mn");if(!m)return;var im=m.querySelector("img");[].forEach.call(document.querySelectorAll(".okl .th img"),function(t){t.onclick=function(){im.src=t.src;[].forEach.call(document.querySelectorAll(".okl .th img"),function(x){x.classList.toggle("on",x===t)})}})})();</script>'
    return CSS + ('<section class="okl"><div class="w"><nav style="font:600 .82rem var(--fb,inherit);color:var(--mut);margin-bottom:16px"><a href="/" style="color:inherit">Ana sayfa</a> › <a href="/ilanlar" style="color:inherit">İlanlar</a> › <b>%s</b></nav>'
                  '<div class="top"><div>%s</div><div><h1>%s</h1><div class="pr" style="font-size:1.9rem;margin:8px 0">%s</div>%s%s%s<div style="line-height:1.7;white-space:pre-line">%s</div></div></div></div></section>' % (
                      E(i["title"]), gal, E(i["title"]), tl(i["price"]) if i["price"] else "Fiyat sorunuz", ct, table, feats + ("<br>" if feats else ""), E(i["description"]))) + js


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    @api_router.get("/admin/listings")
    async def admin_list(_: dict = Depends(require_admin)):
        rows = await db.listings.find({}, {"_id": 0, "images": 0}).sort("created_at", -1).to_list(2000)
        for r in rows:
            r["img_count"] = len((await db.listings.find_one({"id": r["id"]}, {"_id": 0, "images": 1}) or {}).get("images") or [])
        return rows

    @api_router.get("/admin/listings/{lid}")
    async def admin_one(lid: str, _: dict = Depends(require_admin)):
        d = await db.listings.find_one({"id": lid}, {"_id": 0})
        if not d:
            raise HTTPException(404, "İlan bulunamadı")
        return d

    @api_router.post("/admin/listings")
    async def admin_add(payload: dict, _: dict = Depends(require_admin)):
        try:
            c = clean(payload)
        except ValueError as e:
            raise HTTPException(400, str(e))
        lid = str(uuid.uuid4())
        c.update({"id": lid, "slug": slugify(c["title"]) + "-" + lid[:6], "created_at": time.time(), "updated_at": time.time()})
        await db.listings.insert_one(dict(c))
        c.pop("_id", None)
        return c

    @api_router.put("/admin/listings/{lid}")
    async def admin_put(lid: str, payload: dict, _: dict = Depends(require_admin)):
        old = await db.listings.find_one({"id": lid}, {"_id": 0})
        if not old:
            raise HTTPException(404, "İlan bulunamadı")
        try:
            c = clean(payload, old)
        except ValueError as e:
            raise HTTPException(400, str(e))
        c["updated_at"] = time.time()
        await db.listings.update_one({"id": lid}, {"$set": c})
        return {**old, **c}

    @api_router.delete("/admin/listings/{lid}")
    async def admin_del(lid: str, _: dict = Depends(require_admin)):
        r = await db.listings.delete_one({"id": lid})
        if not r.deleted_count:
            raise HTTPException(404, "İlan bulunamadı")
        return {"ok": True}

    @api_router.get("/public/listings")
    async def pub_list(kind: str = "", q: str = ""):
        flt = {"status": {"$in": ["yayinda", "satildi"]}}
        if kind in KINDS:
            flt["kind"] = kind
        rows = await db.listings.find(flt, {"_id": 0, "images": 0}).sort([("featured", -1), ("created_at", -1)]).to_list(500)
        for r in rows:
            r["img_count"] = len((await db.listings.find_one({"id": r["id"]}, {"_id": 0, "images": 1}) or {}).get("images") or [])
        q = q.strip().lower()
        if q:
            rows = [r for r in rows if q in (r["title"] + " " + (r.get("district") or "") + " " + (r.get("city") or "") + " " + (r.get("neighborhood") or "")).lower()]
        return [public_item(r) for r in rows]

    @api_router.get("/public/listings/{ref}")
    async def pub_one(ref: str):
        d = await db.listings.find_one({"$or": [{"slug": ref}, {"id": ref}], "status": {"$in": ["yayinda", "satildi"]}}, {"_id": 0})
        if not d:
            raise HTTPException(404, "İlan bulunamadı")
        return public_item(d, True)

    @api_router.get("/public/listings/{lid}/img/{n}")
    async def pub_img(lid: str, n: int):
        d = await db.listings.find_one({"id": lid, "status": {"$in": ["yayinda", "satildi"]}}, {"_id": 0, "images": 1})
        im = (d or {}).get("images") or []
        if n < 0 or n >= len(im):
            raise HTTPException(404, "Resim yok")
        head, b = im[n].split(";base64,", 1)
        return Response(base64.b64decode(b), media_type=head[5:], headers={"Cache-Control": "public, max-age=3600"})
