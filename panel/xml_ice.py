# -*- coding: utf-8 -*-
"""Tedarikçi / XML ürün aktarma.

Akış:
  1) Panelde XML adresi yapıştırılır, "Analiz et" der: ürün düğümü ve alanlar otomatik bulunur, eşleşme önerilir.
  2) Eşleşme (ad, stok kodu, barkod, fiyat, stok, kategori, marka, resim, açıklama, para birimi) ve fiyat kuralı (kâr %, sabit TL, yuvarlama) kaydedilir.
  3) "Şimdi çalıştır": yeni ürünleri ekler, mevcutları (stok kodu / barkod ile) günceller; istenirse feedde olmayanları pasif yapar.
  4) İsteğe bağlı otomatik güncelleme (6 / 12 / 24 saatte bir, mevcut zamanlayıcıya bağlanır).

Güvenlik: yalnızca http/https; özel ağ / yerel adresler engellenir (SSRF); DOCTYPE/ENTITY içeren XML reddedilir (XXE, "billion laughs");
boyut ve süre sınırı vardır. Telifli içerik sorumluluğu kaynak sahibindedir; yalnızca yetkili olduğunuz beslemeleri kullanın.
"""
import asyncio
import ipaddress
import logging
import math
import re
import socket
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse

import requests
from fastapi import Depends, HTTPException

import shop as shopmod

log = logging.getLogger("xml_ice")
MAX_BYTES = 25 * 1024 * 1024
MAX_ITEMS = 5000
UA = "OnlineKaydet-XML/1.0 (+https://onlinekaydet.com)"

# alan → olası etiket adları (küçük harf, ayraçsız karşılaştırılır)
SYN = {
    "name": ["name", "productname", "urunadi", "urunismi", "title", "baslik", "adi", "isim", "stokadi", "malinadi"],
    "sku": ["productcode", "stokkodu", "sku", "code", "kod", "modelcode", "urunkodu", "stockcode", "productid", "id", "malkodu"],
    "barcode": ["barcode", "barkod", "ean", "gtin", "ean13"],
    "price": ["price", "saleprice", "satisfiyati", "fiyat", "listprice", "pricetl", "satisfiyat", "birimfiyat", "fiyati", "price1", "kdvlifiyat", "kdvlisatisfiyati"],
    "stock": ["stock", "stok", "quantity", "miktar", "stokadedi", "adet", "qty", "stockamount", "stokmiktari", "envanter"],
    "category": ["category", "kategori", "categoryname", "cat", "kategoriadi", "anakategori", "kategoriyolu", "categorypath"],
    "brand": ["brand", "marka", "manufacturer", "markaadi", "brandname", "uretici"],
    "images": ["image", "image1", "picture", "picture1", "resim", "resim1", "foto", "imageurl", "photo", "images", "resimler", "resimurl", "gorsel"],
    "description": ["description", "aciklama", "detail", "detay", "urunaciklamasi", "longdescription", "content", "icerik", "desc"],
    "currency": ["currency", "parabirimi", "dovizturu", "doviztipi", "currencycode", "kur", "doviz"],
    "vat": ["tax", "kdv", "vat", "vatrate", "kdvorani", "taxrate"],
}
FIELDS = list(SYN)
SOURCE_DEFAULT = {
    "name": "", "url": "", "item_path": "", "mapping": {}, "markup_percent": 0.0, "markup_fixed": 0.0, "round_to": 0.0,
    "currency": "TRY", "usd_rate": 0.0, "eur_rate": 0.0, "price_includes_vat": True, "default_vat": 20.0,
    "new_active": True, "update_stock": True, "update_price": True, "update_content": False, "hide_out_of_stock": False,
    "deactivate_missing": False, "category_filter": "", "min_stock": 0, "auto_hours": 0, "default_brand": "", "default_category": "",
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")).lower())


def parse_number(v):
    """Türkçe ve İngilizce sayı biçimlerini çözer: 1.234,56 · 1234.56 · 1,234.56 · 12,5 · %20"""
    s = re.sub(r"[^0-9,.\-]", "", str(v or ""))
    if not s or s in "-.,":
        return 0.0
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        s = s.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif "," in s:
        a, b = s.rsplit(",", 1)
        s = (a.replace(",", "") + b) if (len(b) == 3 and a and "," not in a and len(a) <= 3 and len(s) > 4) else s.replace(",", ".")
        if s.count(".") > 1:
            s = s.replace(".", "", s.count(".") - 1)
    elif "." in s:
        if re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):
            s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


# ------------------------------------------------------------------ güvenli çekim
def assert_public_url(url):
    u = urlparse(url or "")
    if u.scheme not in ("http", "https") or not u.hostname:
        raise HTTPException(422, "Geçerli bir http/https adresi girin")
    try:
        infos = socket.getaddrinfo(u.hostname, u.port or (443 if u.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise HTTPException(422, "Adres bulunamadı (alan adı çözülemedi)")
    for inf in infos:
        ip = ipaddress.ip_address(inf[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise HTTPException(422, "Bu adrese bağlanılamaz (yerel/özel ağ adresi)")


def fetch_bytes(url, timeout=40):
    cur = url
    for _ in range(4):
        assert_public_url(cur)
        r = requests.get(cur, headers={"User-Agent": UA, "Accept": "application/xml,text/xml,*/*"}, timeout=timeout, stream=True, allow_redirects=False)
        if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("Location"):
            cur = urljoin(cur, r.headers["Location"])
            continue
        if r.status_code >= 400:
            raise HTTPException(422, "XML adresi yanıt vermedi (HTTP %d)" % r.status_code)
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf += chunk
            if len(buf) > MAX_BYTES:
                raise HTTPException(422, "XML dosyası çok büyük (en çok 25 MB)")
        return bytes(buf)
    raise HTTPException(422, "Çok fazla yönlendirme")


# ------------------------------------------------------------------ çözümleme
def parse_xml(data):
    head = data[:4096].lower()
    if b"<!doctype" in head or b"<!entity" in data[:200000].lower():
        raise HTTPException(422, "Güvenlik nedeniyle DOCTYPE/ENTITY içeren XML kabul edilmez")
    try:
        return ET.fromstring(data)
    except ET.ParseError as e:
        raise HTTPException(422, "XML okunamadı: %s" % str(e)[:80])


def _tag(e):
    t = e.tag if isinstance(e.tag, str) else ""
    return t.rsplit("}", 1)[-1]


def find_items(root):
    """En çok tekrar eden, en az 3 alt alanı olan düğümü ürün düğümü sayar."""
    best, score = None, 0
    stack = [(root, _tag(root))]
    stats = {}
    while stack:
        e, p = stack.pop()
        kids = list(e)
        if kids:
            st = stats.setdefault(p, [0, 0, []])
            st[0] += 1
            st[1] += sum(1 for k in kids if len(k) == 0)
            if len(st[2]) < 2:
                st[2].append(e)
        for k in kids:
            if isinstance(k.tag, str):
                stack.append((k, p + "/" + _tag(k)))
    for p, (cnt, leaf, ex) in stats.items():
        avg = leaf / max(1, cnt)
        if avg >= 3 and cnt >= 1:
            sc = cnt * min(avg, 12)
            if sc > score:
                best, score = p, sc
    return best


def items_at(root, path):
    parts = path.split("/")
    if parts[0] != _tag(root):
        return []
    cur = [root]
    for part in parts[1:]:
        cur = [k for e in cur for k in e if isinstance(k.tag, str) and _tag(k) == part]
    return cur


def flatten(item):
    out = {}

    def add(k, v):
        v = (v or "").strip()
        if not v:
            return
        out.setdefault(k, []).append(v)

    def walk(e, pre):
        for a, v in e.attrib.items():
            add((pre + "@" + a.rsplit("}", 1)[-1]).lstrip("/"), v)
        kids = [k for k in e if isinstance(k.tag, str)]
        if not kids:
            add(pre.lstrip("/"), e.text)
            return
        for k in kids:
            walk(k, pre + "/" + _tag(k))
    for a, v in item.attrib.items():
        add("@" + a.rsplit("}", 1)[-1], v)
    for k in item:
        if isinstance(k.tag, str):
            walk(k, "/" + _tag(k))
    return out


def suggest_mapping(paths):
    """alan → yol önerisi. Yol adının son parçası eş anlamlılarla karşılaştırılır."""
    m = {}
    flat = [(p, _norm(re.split(r"[/@]", p)[-1] or p)) for p in paths]
    for fld in FIELDS:
        if fld == "images":
            hit = [p for p, n in flat if n in SYN["images"] or re.fullmatch(r"(image|picture|resim|foto|gorsel|photo)\d{1,2}", n)]
            if hit:
                m["images"] = ",".join(hit[:8])
            continue
        for syn in SYN[fld]:
            hit = next((p for p, n in flat if n == syn), None)
            if hit and hit not in m.values():
                m[fld] = hit
                break
    return m


def pick(flat, path):
    vals = []
    for p in [x.strip() for x in (path or "").split(",") if x.strip()]:
        vals += flat.get(p, [])
    return vals


def sale_price(base, src):
    if base <= 0:
        return 0.0
    p = base * (1 + _f(src.get("markup_percent")) / 100.0) + _f(src.get("markup_fixed"))
    step = _f(src.get("round_to"))
    if step > 0:
        p = math.ceil(p / step) * step
    return round(p, 2)


def to_item(flat, src):
    mp = src.get("mapping") or {}

    def first(f):
        v = pick(flat, mp.get(f))
        return v[0] if v else ""
    name = first("name")
    sku = first("sku")
    barcode = first("barcode")
    key = sku or barcode or shopmod.slugify(name)
    price = parse_number(first("price"))
    cur = (first("currency") or src.get("currency") or "TRY").upper().replace("TL", "TRY")
    warn = ""
    if cur in ("USD", "DOLAR", "$"):
        rate = _f(src.get("usd_rate"))
        price, warn = (price * rate, "") if rate > 0 else (0.0, "USD kuru girilmemiş")
    elif cur in ("EUR", "EURO", "€"):
        rate = _f(src.get("eur_rate"))
        price, warn = (price * rate, "") if rate > 0 else (0.0, "EUR kuru girilmemiş")
    if not src.get("price_includes_vat", True) and price > 0:
        price *= 1 + (parse_number(first("vat")) or _f(src.get("default_vat"), 20.0)) / 100.0
    imgs = []
    for v in pick(flat, mp.get("images")):
        for part in re.split(r"[\s,;|]+(?=https?://)", v):
            if re.match(r"^https?://", part.strip()):
                imgs.append(part.strip())
    seen = set()
    imgs = [x for x in imgs if not (x in seen or seen.add(x))][:12]
    return {"key": key[:80], "name": name, "sku": sku, "barcode": barcode, "price": round(price, 2), "stock": int(parse_number(first("stock"))),
            "category": first("category"), "brand": first("brand"), "images": imgs, "description": first("description"), "warn": warn}


def read_items(root, src):
    path = src.get("item_path") or find_items(root)
    if not path:
        raise HTTPException(422, "Ürün listesi bulunamadı; XML yapısı tanınmadı")
    return path, items_at(root, path)


def category_ok(cat, flt):
    words = [w.strip().lower() for w in re.split(r"[,;\n]", flt or "") if w.strip()]
    return (not words) or any(w in (cat or "").lower() for w in words)


_RUNNING = set()


async def run_source(dbx, src):
    sid = src["id"]
    if sid in _RUNNING:
        raise HTTPException(409, "Bu kaynak şu an çalışıyor")
    _RUNNING.add(sid)
    try:
        data = await asyncio.to_thread(fetch_bytes, src["url"])
        root = parse_xml(data)
        path, nodes = read_items(root, src)
        if len(nodes) > MAX_ITEMS:
            nodes = nodes[:MAX_ITEMS]
        added = updated = skipped = pasif = nopr = 0
        warns, seen = [], set()
        for node in nodes:
            it = to_item(flatten(node), src)
            if not it["name"] or not it["key"]:
                skipped += 1
                continue
            if not category_ok(it["category"], src.get("category_filter")) or it["stock"] < int(src.get("min_stock") or 0):
                skipped += 1
                continue
            if it["warn"] and it["warn"] not in warns:
                warns.append(it["warn"])
            seen.add(it["key"])
            base = it["price"]
            price = sale_price(base, src)
            if base <= 0:
                nopr += 1
            cur = await dbx.shop_products.find_one({"src.xml_id": sid, "src.key": it["key"]}, {"_id": 0})
            if not cur and it["sku"]:
                cur = await dbx.shop_products.find_one({"sku": it["sku"], "src.xml_id": {"$exists": False}}, {"_id": 0})
            if cur:
                upd = {"updated_at": _now(), "src.xml_id": sid, "src.key": it["key"], "src.base_price": base, "src.fetched_at": _now()}
                if src.get("update_price") and price > 0 and not cur.get("price_manual"):
                    upd["price"] = price
                if src.get("update_stock"):
                    upd["stock"] = it["stock"]
                    upd["track_stock"] = True
                    if src.get("hide_out_of_stock"):
                        upd["active"] = it["stock"] > 0
                if src.get("update_content") and not cur.get("locked"):
                    upd.update({k: v for k, v in (("name", it["name"][:160]), ("description", it["description"][:12000]),
                                                  ("images", it["images"]), ("brand", it["brand"] or cur.get("brand", ""))) if v})
                await dbx.shop_products.update_one({"id": cur["id"]}, {"$set": upd})
                updated += 1
            else:
                doc = shopmod.clean_product({
                    "name": it["name"], "brand": it["brand"] or src.get("default_brand", ""), "category": it["category"] or src.get("default_category", ""),
                    "description": it["description"], "short": (it["description"] or "")[:240], "images": it["images"], "sku": it["sku"],
                    "price": price, "stock": it["stock"], "track_stock": True,
                    "active": bool(src.get("new_active") and price > 0 and not (src.get("hide_out_of_stock") and it["stock"] <= 0))})
                slug = shopmod.slugify(it["name"])
                n, base_slug = 2, slug
                while await dbx.shop_products.find_one({"slug": slug}):
                    slug, n = "%s-%d" % (base_slug, n), n + 1
                doc.update({"id": uuid.uuid4().hex, "slug": slug, "created_at": _now(), "updated_at": _now(), "sold": 0, "price_manual": False,
                            "barcode": it["barcode"], "src": {"xml_id": sid, "key": it["key"], "base_price": base, "fetched_at": _now()}})
                await dbx.shop_products.insert_one(dict(doc))
                added += 1
        if src.get("deactivate_missing") and seen:
            r = await dbx.shop_products.update_many({"src.xml_id": sid, "src.key": {"$nin": list(seen)}, "active": True}, {"$set": {"active": False, "updated_at": _now()}})
            pasif = r.modified_count
        res = {"item_path": path, "toplam": len(nodes), "eklenen": added, "guncellenen": updated, "atlanan": skipped, "fiyatsiz": nopr,
               "pasif_yapilan": pasif, "uyari": warns[:3], "at": _now()}
        await dbx.xml_sources.update_one({"id": sid}, {"$set": {"last_run": _now(), "last_result": res}})
        return res
    except HTTPException as e:
        res = {"hata": e.detail, "at": _now()}
        await dbx.xml_sources.update_one({"id": sid}, {"$set": {"last_run": _now(), "last_result": res}})
        raise
    finally:
        _RUNNING.discard(sid)


# ------------------------------------------------------------------ kayıt
def register(api_router, db, deps):
    adm = Depends(deps["require_admin"])

    def clean_src(p, cur=None):
        out = dict({**SOURCE_DEFAULT, **(cur or {})})
        for k in ("name", "default_brand", "default_category", "category_filter"):
            if k in p:
                out[k] = str(p[k] or "").strip()[:200]
        if "url" in p:
            out["url"] = str(p["url"] or "").strip()[:600]
        if "item_path" in p:
            out["item_path"] = str(p["item_path"] or "").strip()[:200]
        if "mapping" in p and isinstance(p["mapping"], dict):
            out["mapping"] = {k: str(v)[:400] for k, v in p["mapping"].items() if k in FIELDS and v}
        for k, lo, hi in (("markup_percent", -50, 1000), ("markup_fixed", 0, 1e7), ("round_to", 0, 1000), ("usd_rate", 0, 1e4), ("eur_rate", 0, 1e4), ("default_vat", 0, 100)):
            if k in p:
                out[k] = max(lo, min(hi, _f(p[k])))
        if "min_stock" in p:
            out["min_stock"] = max(0, int(_f(p["min_stock"])))
        if "auto_hours" in p:
            out["auto_hours"] = int(_f(p["auto_hours"])) if int(_f(p["auto_hours"])) in (0, 6, 12, 24) else 0
        if "currency" in p:
            out["currency"] = str(p["currency"] or "TRY").upper()[:4]
        for k in ("price_includes_vat", "new_active", "update_stock", "update_price", "update_content", "hide_out_of_stock", "deactivate_missing"):
            if k in p:
                out[k] = bool(p[k])
        if not out["name"]:
            raise HTTPException(422, "Kaynak adı gerekli")
        if not re.match(r"^https?://", out["url"]):
            raise HTTPException(422, "XML adresi http:// veya https:// ile başlamalı")
        if not out["mapping"].get("name"):
            raise HTTPException(422, "Ürün adı alanını eşleştirin")
        if not (out["mapping"].get("sku") or out["mapping"].get("barcode")):
            raise HTTPException(422, "Stok kodu ya da barkod alanını eşleştirin (ürünleri tanımak için)")
        return out

    async def get_src(sid):
        d = await db.xml_sources.find_one({"id": sid}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Kaynak bulunamadı")
        return d

    @api_router.post("/yp/xml/analiz")
    async def analiz(payload: dict, _: dict = adm):
        url = str(payload.get("url") or "").strip()
        data = await asyncio.to_thread(fetch_bytes, url)
        root = parse_xml(data)
        path = str(payload.get("item_path") or "").strip() or find_items(root)
        if not path:
            raise HTTPException(422, "Ürün listesi bulunamadı; XML yapısı tanınmadı")
        its = items_at(root, path)
        if not its:
            raise HTTPException(422, "Bu yolda ürün bulunamadı")
        flats = [flatten(e) for e in its[:30]]
        paths = []
        for f in flats:
            for p in f:
                if p not in paths:
                    paths.append(p)
        sample = {p: next((f[p][0] for f in flats if p in f), "")[:140] for p in paths}
        return {"item_path": path, "count": len(its), "fields": [{"path": p, "sample": sample[p]} for p in paths][:120],
                "mapping": suggest_mapping(paths), "bytes": len(data)}

    @api_router.get("/yp/xml")
    async def listele(_: dict = adm):
        rows = await db.xml_sources.find({}, {"_id": 0}).sort("created_at", 1).to_list(50)
        for r in rows:
            r["product_count"] = await db.shop_products.count_documents({"src.xml_id": r["id"]})
        return {"sources": rows, "fields": FIELDS}

    @api_router.post("/yp/xml")
    async def olustur(payload: dict, _: dict = adm):
        doc = clean_src(payload)
        doc.update({"id": uuid.uuid4().hex, "created_at": _now(), "last_run": "", "last_result": {}})
        await db.xml_sources.insert_one(dict(doc))
        doc.pop("_id", None)
        return doc

    @api_router.put("/yp/xml/{sid}")
    async def guncelle(sid: str, payload: dict, _: dict = adm):
        cur = await get_src(sid)
        upd = clean_src(payload, cur)
        await db.xml_sources.update_one({"id": sid}, {"$set": {k: upd[k] for k in SOURCE_DEFAULT}})
        return {**cur, **upd}

    @api_router.delete("/yp/xml/{sid}")
    async def sil(sid: str, urunleri_sil: bool = False, _: dict = adm):
        await get_src(sid)
        await db.xml_sources.delete_one({"id": sid})
        n = 0
        if urunleri_sil:
            n = (await db.shop_products.delete_many({"src.xml_id": sid})).deleted_count
        else:
            await db.shop_products.update_many({"src.xml_id": sid}, {"$unset": {"src.xml_id": ""}})
        return {"ok": True, "silinen_urun": n}

    @api_router.post("/yp/xml/{sid}/calistir")
    async def calistir_api(sid: str, _: dict = adm):
        return await run_source(db, await get_src(sid))

    try:
        import governance

        async def _hook(d):
            try:
                for s in await d.xml_sources.find({"auto_hours": {"$gt": 0}}, {"_id": 0}).to_list(20):
                    last = s.get("last_run") or ""
                    if last and datetime.fromisoformat(last) > datetime.now(timezone.utc) - timedelta(hours=int(s["auto_hours"])):
                        continue
                    try:
                        await run_source(d, s)
                    except Exception as e:      # noqa: BLE001
                        log.warning("xml otomatik: %s", e)
            except Exception:                   # noqa: BLE001
                pass
        governance.HOOKS.append(_hook)
    except Exception:                           # noqa: BLE001
        pass
