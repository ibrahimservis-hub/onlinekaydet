# -*- coding: utf-8 -*-
"""Kategori ağacı: ana/alt kategori, sürükle-taşı sıralama, silerken ürün aktarma, düzenleme (SEO, sosyal, görünüm),
pazaryeri kodu bağlama ve sitede kategori ağacı.

Tek kaynak `shop_categories` (id, name, parent, sort, ...). Panel ürünü (yp_products) `cat_ids` ile ağaca bağlanır;
`cat`/`cats` ürün üzerinde ad olarak tutulur (liste, dışa aktarım ve eski kayıtlar için).
"""
import re
import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException

_TR = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosuCGIOSUaiu")


def _now():
    return datetime.now(timezone.utc).isoformat()


def slugify(s, n=70):
    s = str(s or "").translate(_TR).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:n]


def _t(v, n):
    return str(v or "").strip()[:n]


ALANLAR = ("code", "adwords_name", "adwords_type")

# Google ürün kategorisi (Merchant Center taksonomisi): üst düzey kategoriler ve sık kullanılan bir alt kategori.
GOOGLE_KAT = [("1", "Animals & Pet Supplies"), ("166", "Apparel & Accessories"), ("8", "Arts & Entertainment"), ("537", "Baby & Toddler"),
              ("111", "Business & Industrial"), ("141", "Cameras & Optics"), ("222", "Electronics"), ("412", "Food, Beverages & Tobacco"),
              ("436", "Furniture"), ("632", "Hardware"), ("469", "Health & Beauty"), ("536", "Home & Garden"), ("5181", "Luggage & Bags"),
              ("783", "Media"), ("922", "Office Supplies"), ("5605", "Religious & Ceremonial"), ("2092", "Software"), ("988", "Sporting Goods"),
              ("1239", "Toys & Games"), ("888", "Vehicles & Parts"), ("8025", "Vehicles & Parts > Vehicle Parts & Accessories")]
# Kategori adından Google kategorisi tahmini (ad içinde geçen kelimeye göre). Panelde değiştirilebilir.
GOOGLE_TAHMIN = [("yedek parça|oto|araç|araba|lastik|jant|akü|kaplama|detailing", "8025"), ("kombi|klima|şofben|radyatör|tesisat|musluk|batarya|vana|boru", "632"),
                 ("beyaz eşya|buzdolabı|çamaşır|bulaşık|fırın|ocak|süpürge|ütü", "536"), ("telefon|bilgisayar|laptop|tablet|kulaklık|şarj|kablo|televizyon|elektronik", "222"),
                 ("kamera|güvenlik|lens", "141"), ("giyim|elbise|ayakkabı|çanta|aksesuar|saat|takı", "166"), ("kozmetik|güzellik|bakım|parfüm|saç|cilt|makyaj|sağlık", "469"),
                 ("mobilya|koltuk|masa|sandalye|yatak|dolap", "436"), ("bahçe|ev|dekor|mutfak|aydınlatma|halı|perde", "536"), ("oyuncak|oyun", "1239"),
                 ("bebek|çocuk", "537"), ("kırtasiye|ofis", "922"), ("spor|fitness|bisiklet|kamp", "988"), ("evcil|kedi|köpek|mama|akvaryum", "1"),
                 ("gıda|içecek|kahve|çay|yiyecek|tatlı|market", "412"), ("kitap|müzik|film", "783"), ("yazılım|lisans", "2092"), ("hırdavat|el aleti|matkap|vida|boya", "632")]


def google_tahmin(ad):
    a = str(ad or "").lower()
    for kelimeler, kod in GOOGLE_TAHMIN:
        if any(k in a for k in kelimeler.split("|")):
            return kod
    return ""


def _kat_google(rows):
    """{kategori id: (yol, google kategorisi)}; Google değeri yoksa en yakın üst kategoriden gelir."""
    by_id = {r["id"]: r for r in rows}
    out = {}
    for r in rows:
        yol, g, cid, seen = [], "", r["id"], set()
        while cid and cid in by_id and cid not in seen:
            seen.add(cid)
            yol.append(by_id[cid]["name"])
            g = g or (by_id[cid].get("google_cat") or "")
            cid = by_id[cid].get("parent") or ""
        out[r["id"]] = (" > ".join(reversed(yol)), g)
    return out


async def akis_haritasi(db):
    """Ürün akışları için: {kategori adı: {"yol": "Ana > Alt", "google": "kod ya da yol"}} (aynı ad birden çoksa ilki)."""
    rows = [r for r in await tum(db) if r.get("active", True)]
    kg = _kat_google(rows)
    out = {}
    for r in rows:
        out.setdefault(r["name"], {"yol": kg[r["id"]][0], "google": kg[r["id"]][1]})
    return out



def _alanlar(p, c=None):
    """Düzenleme formundan gelen alanları temizle. c verilirse eksik alanlar eski değerde kalır."""
    c = c or {}
    out = {}
    for k, n in (("code", 40), ("adwords_name", 120), ("adwords_type", 120), ("google_cat", 200)):
        if k in p or k not in c:
            out[k] = _t(p.get(k), n)
    for k, d in (("active", True), ("oos_last", False), ("list_variants", False), ("show_video", False), ("auto_video", False), ("native", False)):
        if k in p:
            out[k] = bool(p.get(k))
        elif k not in c:
            out[k] = d
    if "page_html" in p:
        out["page_html"] = str(p.get("page_html") or "")[:20000]
    seo = p.get("seo")
    if isinstance(seo, dict):
        out["seo"] = {"title": _t(seo.get("title"), 70), "keywords": _t(seo.get("keywords"), 250), "desc": _t(seo.get("desc"), 320),
                      "noindex": bool(seo.get("noindex")), "nofollow": bool(seo.get("nofollow"))}
    soc = p.get("social")
    if isinstance(soc, dict):
        img = _t(soc.get("img"), 300)
        if img and not re.match(r"^(https?://|/)", img):
            raise HTTPException(422, "Sosyal medya resim yolu http(s):// ya da / ile başlamalı")
        out["social"] = {"title": _t(soc.get("title"), 90), "desc": _t(soc.get("desc"), 200), "img": img}
    img = p.get("img")
    if img is not None:
        img = _t(img, 300)
        if img and not re.match(r"^(https?://|/)", img):
            raise HTTPException(422, "Görsel yolu http(s):// ya da / ile başlamalı")
        out["img"] = img
    return out


def _agac(rows):
    """Düz listeden {id: [çocuk id'ler]} ve kökler (sıralı)."""
    ch = {}
    for r in rows:
        ch.setdefault(r.get("parent") or "", []).append(r)
    for k in ch:
        ch[k].sort(key=lambda r: (r.get("sort", 100), r.get("name", "").lower()))
    return ch


def _torunlar(rows, cid):
    ch = _agac(rows)
    out, st = [], [cid]
    while st:
        x = st.pop()
        for c in ch.get(x, []):
            out.append(c["id"])
            st.append(c["id"])
    return out


async def _benzersiz_slug(db, base, hariç=""):
    base = base or "kategori"
    s, n = base, 2
    while await db.shop_categories.find_one({"slug": s, "id": {"$ne": hariç}}, {"_id": 1}):
        s, n = f"{base}-{n}", n + 1
    return s


async def _sirala(db, parent, ids):
    """Kardeşleri verilen sıraya göre 10, 20, 30… olarak numarala."""
    for i, cid in enumerate(ids):
        await db.shop_categories.update_one({"id": cid}, {"$set": {"sort": (i + 1) * 10, "parent": parent}})


async def tum(db):
    rows = await db.shop_categories.find({}, {"_id": 0}).to_list(5000)
    dirty = False
    for r in rows:                                         # eski kayıtlarda adres yoksa üret
        if not r.get("slug"):
            r["slug"] = await _benzersiz_slug(db, slugify(r["name"]), r["id"])
            await db.shop_categories.update_one({"id": r["id"]}, {"$set": {"slug": r["slug"]}})
            dirty = True
    return rows


async def coz(db, o, ids=None):
    """Ürün belgesindeki kategorileri ağaca bağla. ids (ağaç kimlikleri) verilirse onlar esastır; yoksa adlardan eşle/oluştur."""
    rows = await tum(db)
    by_id = {r["id"]: r for r in rows}
    sel = []
    if isinstance(ids, list) and ids:
        for i in ids[:10]:
            if i in by_id and i not in sel:
                sel.append(i)
    else:
        adlar = [a for a in (o.get("cats") or []) if a] or ([o["cat"]] if o.get("cat") else [])
        for a in adlar[:10]:
            hit = next((r for r in rows if r["name"].strip().lower() == a.strip().lower()), None)
            if not hit:
                hit = {"id": str(uuid.uuid4()), "name": a.strip()[:80], "parent": "", "sort": 100, "active": True, "created_at": _now()}
                hit["slug"] = await _benzersiz_slug(db, slugify(hit["name"]))
                await db.shop_categories.insert_one(dict(hit))
                rows.append(hit)
                by_id[hit["id"]] = hit
            if hit["id"] not in sel:
                sel.append(hit["id"])
    names = [by_id[i]["name"] for i in sel]
    o["cat_ids"] = sel
    o["cats"] = names
    o["cat"] = names[0] if names else ""
    return o


def _kok_yolu(by_id, cid):
    yol, seen = [], set()
    while cid and cid in by_id and cid not in seen:
        seen.add(cid)
        yol.append(by_id[cid]["name"])
        cid = by_id[cid].get("parent") or ""
    return " › ".join(reversed(yol))


async def adlar_icin(db, ref):
    """Mağaza süzgeci: slug ya da ad → o kategori ve tüm alt kategorilerinin adları (bulunamazsa None)."""
    ref = str(ref or "").strip()
    if not ref:
        return None
    rows = await tum(db)
    hit = next((r for r in rows if r.get("slug") == ref), None) or next((r for r in rows if r["name"] == ref), None)
    if not hit:
        return None
    ids = [hit["id"]] + _torunlar(rows, hit["id"])
    by_id = {r["id"]: r for r in rows}
    return [by_id[i]["name"] for i in ids if by_id[i].get("active", True)]


async def kategori_sayfasi(db, slug):
    """Herkese açık kategori sayfası bilgisi (adres: /magaza/kategori/<slug>); gizli kategori için None."""
    rows = await tum(db)
    c = next((r for r in rows if r.get("slug") == slug and r.get("active", True)), None)
    if not c:
        return None
    try:
        import marka_seo
        tpl, firma = await marka_seo.templates(db), await marka_seo.firma_adi(db)
        v = {"kategori": c["name"], "firma": firma, "marka": "", "urun": "", "model": "", "fiyat": ""}
        t0 = marka_seo.render(tpl.get("category_title") or "", v, 70)
        d0 = marka_seo.render(tpl.get("category_desc") or "", v, 170)
    except Exception:                                      # noqa: BLE001
        t0, d0, firma = "", "", ""
    seo = c.get("seo") or {}
    soc = c.get("social") or {}
    return {"id": c["id"], "slug": slug, "name": c["name"], "img": c.get("img", ""), "kw": seo.get("keywords", ""),
            "seo_title": (seo.get("title") or "").strip() or t0 or (c["name"] + " · " + firma).strip(" ·"),
            "seo_desc": (seo.get("desc") or "").strip() or d0, "noindex": bool(seo.get("noindex")),
            "og_title": soc.get("title") or "", "og_desc": soc.get("desc") or "", "og_img": soc.get("img") or c.get("img", "")}


async def kategori_adresleri(db):
    """Site haritası için: ürünü olan, açık ve noindex olmayan kategorilerin adresleri (alt kategori ürünleri üste sayılır)."""
    rows = await tum(db)
    names = {}
    async for p in db.shop_products.find({"active": True}, {"_id": 0, "category": 1}):
        n = (p.get("category") or "").strip()
        if n:
            names[n] = names.get(n, 0) + 1
    ch = _agac([r for r in rows if r.get("active", True)])
    out = []

    def say(r):
        n = names.get(r["name"], 0) + sum(say(c) for c in ch.get(r["id"], []))
        if n and not (r.get("seo") or {}).get("noindex") and r.get("slug"):
            out.append("magaza/kategori/" + r["slug"])
        return n
    for r in ch.get("", []):
        say(r)
    return out


async def agac_acik(db, sayim):
    """Sitede gösterilecek ağaç: yalnız etkin kategoriler; sayım ad bazlı (alt kategoriler üste toplanır)."""
    rows = [r for r in await tum(db) if r.get("active", True)]
    ch = _agac(rows)

    def dugum(r):
        kids = [dugum(c) for c in ch.get(r["id"], [])]
        n = sayim.get(r["name"], 0) + sum(k["count"] for k in kids)
        return {"id": r["id"], "name": r["name"], "slug": r.get("slug", ""), "count": n, "img": r.get("img", ""), "children": kids,
                "seo": r.get("seo") or {}, "social": r.get("social") or {}, "page_html": r.get("page_html", ""),
                "oos_last": bool(r.get("oos_last"))}

    out = [dugum(r) for r in ch.get("", [])]
    return out


def register(api_router, db, deps):
    adm = deps["require_admin"]

    async def mp_map():
        out = {}
        async for m in db.market_catmap.find({}, {"_id": 0}):
            if m.get("ext_id"):
                out.setdefault(m["category_id"], []).append({"market": m["market"], "ext_id": m["ext_id"], "ext_name": m.get("ext_name", "")})
        return out

    async def kullanim():
        used = {}
        async for p in db.yp_products.find({}, {"_id": 0, "cat_ids": 1, "cat": 1}):
            for i in (p.get("cat_ids") or []):
                used[i] = used.get(i, 0) + 1
        return used

    @api_router.get("/shop/categories")
    async def cat_list(_: dict = Depends(adm)):
        rows = await tum(db)
        used, mp = await kullanim(), await mp_map()
        by_id = {r["id"]: r for r in rows}
        ch = _agac(rows)
        order = []

        def gez(pid, depth):
            for c in ch.get(pid, []):
                order.append((c, depth))
                gez(c["id"], depth + 1)

        gez("", 0)
        out = []
        for c, d in order:
            tor = _torunlar(rows, c["id"])
            out.append(dict(c, parent=c.get("parent") or "", depth=d, products=used.get(c["id"], 0), total=used.get(c["id"], 0) + sum(used.get(i, 0) for i in tor),
                            children=len(ch.get(c["id"], [])), path=_kok_yolu(by_id, c["id"]), markets=mp.get(c["id"], [])))
        return out

    @api_router.get("/shop/categories/markets")
    async def cat_markets(_: dict = Depends(adm)):
        """Kategori kodu girilebilecek pazaryerleri: yalnız API bilgisi girilmiş olanlar."""
        import urun
        return [{"id": k["id"], "name": k["name"]} for k in await urun._kanallar_aktif(db) if k.get("aktif") and k["id"] != "site"]

    @api_router.post("/shop/categories")
    async def cat_add(payload: dict, _: dict = Depends(adm)):
        name = _t(payload.get("name"), 80)
        if len(name) < 2:
            raise HTTPException(422, "Kategori adı gerekli")
        parent = str(payload.get("parent") or "")
        if parent and not await db.shop_categories.find_one({"id": parent}, {"_id": 1}):
            raise HTTPException(422, "Üst kategori bulunamadı")
        if await db.shop_categories.find_one({"name": name, "parent": parent}, {"_id": 1}):
            raise HTTPException(409, "Bu kategori zaten var")
        sib = await db.shop_categories.find({"parent": parent}, {"_id": 0, "sort": 1}).to_list(2000)
        doc = {"id": str(uuid.uuid4()), "name": name, "parent": parent, "sort": max([s.get("sort", 100) for s in sib] + [0]) + 10,
               "slug": await _benzersiz_slug(db, slugify(payload.get("slug") or name)), "created_at": _now()}
        doc.update(_alanlar(payload))
        if not doc.get("google_cat"):
            doc["google_cat"] = google_tahmin(name)                  # ad, üst kategori yoksa kelimeden tahmin edilir; panelde değiştirilebilir
        await db.shop_categories.insert_one(dict(doc))
        return doc

    @api_router.put("/shop/categories/{cid}")
    async def cat_edit(cid: str, payload: dict, _: dict = Depends(adm)):
        c = await db.shop_categories.find_one({"id": cid}, {"_id": 0})
        if not c:
            raise HTTPException(404, "Kategori yok")
        up = _alanlar(payload, c)
        if "name" in payload:
            name = _t(payload.get("name"), 80)
            if len(name) < 2:
                raise HTTPException(422, "Kategori adı gerekli")
            if name != c["name"] and await db.shop_categories.find_one({"name": name, "parent": c.get("parent", ""), "id": {"$ne": cid}}, {"_id": 1}):
                raise HTTPException(409, "Aynı seviyede bu adda kategori var")
            up["name"] = name
        if "slug" in payload:
            sl = slugify(payload.get("slug"))
            if sl:
                up["slug"] = await _benzersiz_slug(db, sl, cid)
        if "sort" in payload:
            try:
                up["sort"] = int(float(payload.get("sort")))
            except (TypeError, ValueError):
                pass
        await db.shop_categories.update_one({"id": cid}, {"$set": up})
        if up.get("name") and up["name"] != c["name"]:        # ürünlerdeki ad hep ağaçla aynı kalır
            async for p in db.yp_products.find({"cat_ids": cid}, {"_id": 0, "id": 1, "cats": 1, "cat_ids": 1}):
                rows = {r["id"]: r["name"] for r in await db.shop_categories.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(5000)}
                names = [rows.get(i, "") for i in (p.get("cat_ids") or []) if rows.get(i)]
                await db.yp_products.update_one({"id": p["id"]}, {"$set": {"cats": names, "cat": names[0] if names else ""}})
            await db.shop_products.update_many({"category_id": cid}, {"$set": {"category": up["name"]}})
        return {"ok": True, "slug": up.get("slug", c.get("slug", ""))}

    @api_router.post("/shop/categories/{cid}/move")
    async def cat_move(cid: str, payload: dict, _: dict = Depends(adm)):
        """Başka kategorinin altına ya da aynı seviyede istenen sıraya taşı. parent='' → ana kategori; index → kardeşler arası sıra."""
        rows = await tum(db)
        c = next((r for r in rows if r["id"] == cid), None)
        if not c:
            raise HTTPException(404, "Kategori yok")
        parent = str(payload.get("parent") or "")
        if parent:
            if parent == cid or parent in _torunlar(rows, cid):
                raise HTTPException(422, "Kategori kendi alt kategorisinin içine taşınamaz")
            if not any(r["id"] == parent for r in rows):
                raise HTTPException(422, "Hedef kategori bulunamadı")
        if any(r["id"] != cid and (r.get("parent") or "") == parent and r["name"] == c["name"] for r in rows):
            raise HTTPException(409, "Hedefte aynı adda bir kategori var")
        sib = sorted([r for r in rows if (r.get("parent") or "") == parent and r["id"] != cid], key=lambda r: (r.get("sort", 100), r["name"].lower()))
        ids = [r["id"] for r in sib]
        try:
            idx = int(payload.get("index", len(ids)))
        except (TypeError, ValueError):
            idx = len(ids)
        ids.insert(min(max(idx, 0), len(ids)), cid)
        await _sirala(db, parent, ids)
        return {"ok": True}

    @api_router.get("/shop/categories/{cid}/products")
    async def cat_products(cid: str, alt: bool = True, _: dict = Depends(adm)):
        rows = await tum(db)
        if not any(r["id"] == cid for r in rows):
            raise HTTPException(404, "Kategori yok")
        ids = [cid] + (_torunlar(rows, cid) if alt else [])
        ps = await db.yp_products.find({"cat_ids": {"$in": ids}}, {"_id": 0, "id": 1, "name": 1, "sku": 1, "price": 1, "sale_price": 1, "stock": 1, "status": 1}).to_list(300)
        return {"items": ps, "n": len(ps)}

    @api_router.get("/shop/categories/google")
    async def cat_google(_: dict = Depends(adm)):
        return [{"id": k, "name": n} for k, n in GOOGLE_KAT]

    @api_router.post("/shop/categories/birlestir")
    async def cat_birlestir(payload: dict, _: dict = Depends(adm)):
        """Seçili kategorileri tek kategoride topla: ürünler hedefe taşınır, alt kategoriler hedefin altına geçer, kaynaklar silinir."""
        ids = [str(i) for i in (payload.get("ids") or [])][:200]
        target = str(payload.get("target") or "")
        rows = await tum(db)
        by_id = {r["id"]: r for r in rows}
        if target not in by_id:
            raise HTTPException(422, "Hedef kategori seçin")
        kaynak = [i for i in ids if i in by_id and i != target]
        if not kaynak:
            raise HTTPException(422, "Birleştirmek için en az iki kategori seçin")
        yasak = set(_torunlar(rows, target))
        if any(i in yasak for i in kaynak):
            raise HTTPException(422, "Alt kategori, üst kategorisiyle birleştirilemez: önce taşıyın")
        yeni_ad = _t(payload.get("name"), 80)
        moved = 0
        for i in kaynak:
            async for p in db.yp_products.find({"cat_ids": i}, {"_id": 0, "id": 1, "cat_ids": 1}):
                new = [t for t in (p.get("cat_ids") or []) if t != i]
                if target not in new:
                    new.append(target)
                moved += 1
                names = [(yeni_ad if x == target and yeni_ad else by_id[x]["name"]) for x in new if x in by_id]
                await db.yp_products.update_one({"id": p["id"]}, {"$set": {"cat_ids": new, "cats": names, "cat": names[0] if names else ""}})
            await db.shop_categories.update_many({"parent": i}, {"$set": {"parent": target}})
            await db.shop_categories.delete_one({"id": i})
            await db.market_catmap.delete_many({"category_id": i})
        if yeni_ad and yeni_ad != by_id[target]["name"]:
            if await db.shop_categories.find_one({"name": yeni_ad, "parent": by_id[target].get("parent", ""), "id": {"$ne": target}}, {"_id": 1}):
                raise HTTPException(409, "Aynı seviyede bu adda kategori var")
            await db.shop_categories.update_one({"id": target}, {"$set": {"name": yeni_ad}})
            by_id[target]["name"] = yeni_ad
        # kaynak kategorinin Google kodu hedefte boşsa devral
        if not by_id[target].get("google_cat"):
            g = next((by_id[i].get("google_cat") for i in kaynak if by_id[i].get("google_cat")), "")
            if g:
                await db.shop_categories.update_one({"id": target}, {"$set": {"google_cat": g}})
        # çocukları aynı adda çakışırsa sonuna numara ekleme yerine bırak (kardeş adı aynıysa birleşme yeniden denenebilir)
        try:
            import urun_ayna
            async for p in db.yp_products.find({"cat_ids": target}, {"_id": 0, "id": 1}):
                await urun_ayna.ayna(db, p["id"])
        except Exception:                                  # noqa: BLE001
            pass
        return {"ok": True, "birlesen": len(kaynak), "aktarilan": moved}

    @api_router.post("/shop/categories/sil")
    async def cat_sil(payload: dict, _: dict = Depends(adm)):
        """Seçilileri sil. Ürünü olan kategoride target (hedef kategori) gerekir: ürünler oraya aktarılır. Alt kategoriler bir üste çıkar."""
        ids = [str(i) for i in (payload.get("ids") or [])][:200]
        target = str(payload.get("target") or "")
        rows = await tum(db)
        by_id = {r["id"]: r for r in rows}
        ids = [i for i in ids if i in by_id]
        if not ids:
            raise HTTPException(422, "Silinecek kategori seçin")
        if target and (target in ids or target not in by_id):
            raise HTTPException(422, "Hedef kategori silinecekler arasında olamaz")
        used = await kullanim()
        gerek = [i for i in ids if used.get(i)]
        if gerek and not target:
            raise HTTPException(409, {"urunlu": [{"id": i, "name": by_id[i]["name"], "n": used[i]} for i in gerek]})
        moved = 0
        for i in ids:
            if used.get(i) and target:
                async for p in db.yp_products.find({"cat_ids": i}, {"_id": 0, "id": 1, "cat_ids": 1}):
                    new = [t for t in (p.get("cat_ids") or []) if t != i]
                    if target not in new:
                        new.append(target)
                    names = [by_id[x]["name"] for x in new if x in by_id]
                    await db.yp_products.update_one({"id": p["id"]}, {"$set": {"cat_ids": new, "cats": names, "cat": names[0] if names else ""}})
                    moved += 1
        for i in ids:
            c = by_id[i]
            up = (c.get("parent") or "")
            await db.shop_categories.update_many({"parent": i}, {"$set": {"parent": up if up not in ids else ""}})
            await db.shop_categories.delete_one({"id": i})
            await db.market_catmap.delete_many({"category_id": i})
        try:
            import urun_ayna
            async for p in db.yp_products.find({}, {"_id": 0, "id": 1}):
                await urun_ayna.ayna(db, p["id"])
        except Exception:                                  # noqa: BLE001
            pass
        return {"ok": True, "silinen": len(ids), "aktarilan": moved}

    @api_router.get("/public/shop/category-page/{slug}")
    async def pub_cat_page(slug: str):
        c = await kategori_sayfasi(db, slug)
        if not c:
            raise HTTPException(404, "Kategori yok")
        return c

    @api_router.get("/public/shop/category-tree")
    async def pub_tree():
        cc = {}
        async for p in db.shop_products.find({"active": True}, {"_id": 0, "category": 1}):
            c = (p.get("category") or "").strip()
            if c:
                cc[c] = cc.get(c, 0) + 1
        return {"tree": await agac_acik(db, cc)}
