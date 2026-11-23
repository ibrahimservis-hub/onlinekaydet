# -*- coding: utf-8 -*-
"""Excel/CSV ile toplu ürün yükleme: şablon, dosya okuma, sütun eşleme, önizleme (kuru çalıştırma), içe aktarma, hata raporu.

Akış: parse (dosya → iş) → preview (eşleme+mod → plan, hiçbir şey yazılmaz) → run (planı yazar) → errors (hata satırları CSV).
Aynı «Ana stok kodu» taşıyan satırlar tek ürünün seçenekleri (renk/beden) olur. Güncellemede yalnız eşlenen ve dolu hücreler değişir."""
import base64
import csv
import io
import re
import time
import uuid

from fastapi import Depends, HTTPException

import urun

MAX_ROWS, MAX_BYTES = 5000, 5 * 1024 * 1024
ALAN = [  # (alan, şablon başlığı, takma adlar)
    ("name", "Ürün adı", ["urun adi", "ad", "baslik", "urun", "name", "title"]),
    ("sku", "Stok kodu", ["stok kodu", "sku", "urun kodu", "kod"]),
    ("barcode", "Barkod", ["barkod", "gtin", "ean", "barcode"]),
    ("cat", "Kategori", ["kategori", "category"]),
    ("brand", "Marka", ["marka", "brand"]),
    ("model", "Model", ["model"]),
    ("cost", "Alış fiyatı", ["alis", "alis fiyati", "maliyet", "cost"]),
    ("price", "Satış fiyatı", ["satis", "satis fiyati", "fiyat", "price"]),
    ("sale_price", "İndirimli fiyat", ["indirimli", "indirimli fiyat", "indirimli satis fiyati", "sale"]),
    ("vat", "KDV", ["kdv", "kdv orani", "vat"]),
    ("stock", "Stok", ["stok", "stok adedi", "adet", "miktar", "stock"]),
    ("desc", "Açıklama", ["aciklama", "urun aciklamasi", "description", "detay"]),
    ("img1", "Görsel 1", ["gorsel 1", "gorsel", "resim", "resim 1", "image", "gorsel linki"]),
    ("img2", "Görsel 2", ["gorsel 2", "resim 2"]),
    ("img3", "Görsel 3", ["gorsel 3", "resim 3"]),
    ("img4", "Görsel 4", ["gorsel 4", "resim 4"]),
    ("img5", "Görsel 5", ["gorsel 5", "resim 5"]),
    ("status", "Durum", ["durum", "status", "yayin"]),
    ("group", "Ana stok kodu", ["ana stok kodu", "ana kod", "grup", "parent", "ana urun kodu"]),
    ("o1n", "Seçenek 1 adı", ["secenek 1 adi", "varyant 1 adi"]),
    ("o1v", "Seçenek 1 değeri", ["secenek 1 degeri", "secenek 1", "renk", "varyant 1"]),
    ("o2n", "Seçenek 2 adı", ["secenek 2 adi", "varyant 2 adi"]),
    ("o2v", "Seçenek 2 değeri", ["secenek 2 degeri", "secenek 2", "beden", "varyant 2"]),
]
ETIKET = {a: b for a, b, _ in ALAN}
_SCI = re.compile(r"^\d+([.,]\d+)?[eE]\+\d+$")


def _norm(s):
    s = str(s or "").strip().lower()
    for a, b in (("ı", "i"), ("ğ", "g"), ("ü", "u"), ("ş", "s"), ("ö", "o"), ("ç", "c"), ("i̇", "i")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def oto_esle(basliklar):
    """Başlık → alan eşlemesi (şablon başlığı ya da takma ad). {alan: başlık}"""
    out, kul = {}, set()
    tab = {}
    for a, b, al in ALAN:
        tab.setdefault(_norm(b), a)
        for x in al:
            tab.setdefault(_norm(x), a)
    for h in basliklar:
        a = tab.get(_norm(h))
        if a and a not in out and h not in kul:
            out[a] = h
            kul.add(h)
    return out


def sablon_csv():
    ornek = [
        ["Keten Gömlek", "KG-01", "8690000000014", "Gömlek", "Nevermore", "", "400", "900", "", "20", "10", "Yumuşak dokulu keten gömlek", "https://site.com/g1.jpg", "", "", "Yayında", "", "", "", "", ""],
        ["Tişört", "TS-B-M", "", "Tişört", "Nevermore", "", "100", "300", "250", "20", "5", "", "", "", "", "Yayında", "TS", "Renk", "Beyaz", "Beden", "M"],
        ["", "TS-B-L", "", "", "", "", "", "300", "", "", "3", "", "", "", "", "", "TS", "Renk", "Beyaz", "Beden", "L"],
    ]
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_ALL)
    w.writerow([b for _a, b, _x in ALAN])
    for r in ornek:
        w.writerow(r)
    return "﻿" + buf.getvalue()


def sablon_xlsx(markalar=(), kategoriler=()):
    """Örnek satırlı, açıklamalı Excel şablonu (base64 için bayt döner)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.worksheet.datavalidation import DataValidation
    wb = Workbook()
    ws = wb.active
    ws.title = "Ürünler"
    bas = [b for _a, b, _x in ALAN]
    ws.append(bas)
    ornek = [
        {"Ürün adı": "Keten Gömlek", "Stok kodu": "KG-01", "Barkod": "8690000000014", "Kategori": "Gömlek", "Marka": "Nevermore", "Alış fiyatı": 400, "Satış fiyatı": 900,
         "KDV": 20, "Stok": 10, "Açıklama": "Yumuşak dokulu keten gömlek", "Görsel 1": "https://site.com/gorsel1.jpg", "Görsel 2": "https://site.com/gorsel2.jpg", "Durum": "Yayında"},
        {"Ürün adı": "Tişört", "Stok kodu": "TS-B-M", "Kategori": "Tişört", "Marka": "Nevermore", "Alış fiyatı": 100, "Satış fiyatı": 300, "İndirimli fiyat": 250, "KDV": 20, "Stok": 5,
         "Görsel 1": "https://site.com/tisort.jpg", "Durum": "Yayında", "Ana stok kodu": "TS", "Seçenek 1 adı": "Renk", "Seçenek 1 değeri": "Beyaz", "Seçenek 2 adı": "Beden", "Seçenek 2 değeri": "M"},
        {"Stok kodu": "TS-B-L", "Satış fiyatı": 300, "Stok": 3, "Ana stok kodu": "TS", "Seçenek 1 adı": "Renk", "Seçenek 1 değeri": "Beyaz", "Seçenek 2 adı": "Beden", "Seçenek 2 değeri": "L"},
    ]
    for o in ornek:
        ws.append([o.get(b, "") for b in bas])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F3A5F")
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for i, b in enumerate(bas, start=1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = max(14, min(34, len(b) + 6))
    ws.freeze_panes = "A2"
    for r in range(2, 2002):                       # barkod ve stok kodu metin kalsın (bilimsel gösterim olmasın)
        for col in (2, 3):
            ws.cell(r, col).number_format = "@"
    ac = wb.create_sheet("Açıklama")
    ac.append(["Sütun", "Ne yazılır", "Zorunlu"])
    yaz = {"name": ("Ürünün adı", "Evet"), "sku": ("Benzersiz stok kodu; güncellemede eşleşme için kullanılır", "Önerilir"), "barcode": ("EAN/GTIN; hücre Metin biçiminde olmalı", "Hayır"),
           "cat": ("Kategori adı; yoksa oluşturulur", "Hayır"), "brand": ("Markalar sayfasındaki adla aynı yazın; yoksa otomatik eklenir", "Hayır"), "model": ("Model adı", "Hayır"),
           "cost": ("Alış fiyatı (sayı)", "Hayır"), "price": ("KDV dâhil satış fiyatı", "Evet"), "sale_price": ("İndirimli fiyat; boşsa indirim yok", "Hayır"), "vat": ("0, 1, 10 ya da 20", "Hayır"),
           "stock": ("Stok adedi", "Hayır"), "desc": ("Ürün açıklaması", "Hayır"), "status": ("Yayında ya da Taslak", "Hayır"),
           "group": ("Renk/beden gibi seçenekli ürünlerde aynı değeri taşıyan satırlar tek ürün olur", "Seçenekli ürünlerde")}
    for a, b, _x in ALAN:
        if a.startswith("img"):
            ac.append([b, "Tam görsel bağlantısı (https://…). Bir hücreye birden fazlasını | ile ayırarak yazabilirsiniz", "Hayır"])
        elif a in yaz:
            ac.append([b, yaz[a][0], yaz[a][1]])
        else:
            ac.append([b, "Seçenekli ürünlerde renk/beden adı ve değeri (örn. Renk → Beyaz)", "Seçenekli ürünlerde"])
    for c in ac[1]:
        c.font = Font(bold=True)
    ac.column_dimensions["A"].width = 22
    ac.column_dimensions["B"].width = 90
    ac.column_dimensions["C"].width = 20
    if markalar:
        mk = wb.create_sheet("Markalar")
        mk.append(["Kayıtlı markalarınız"])
        for m in markalar:
            mk.append([m])
        mk["A1"].font = Font(bold=True)
        mk.column_dimensions["A"].width = 30
        dv = DataValidation(type="list", formula1="=Markalar!$A$2:$A$%d" % (len(markalar) + 1), allow_blank=True, showErrorMessage=False)
        ws.add_data_validation(dv)
        dv.add("E2:E2001")
    if kategoriler:
        kt = wb.create_sheet("Kategoriler")
        kt.append(["Kayıtlı kategorileriniz"])
        for m in kategoriler:
            kt.append([m])
        kt["A1"].font = Font(bold=True)
        kt.column_dimensions["A"].width = 30
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def oku(raw, ad):
    """Dosya baytlarından (başlıklar, satırlar). CSV (; , sekme) ya da xlsx."""
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "Dosya 5 MB'ı aşıyor; ürünleri parçalara bölün")
    rows = []
    if raw[:2] == b"PK" or ad.lower().endswith((".xlsx", ".xlsm")):
        try:
            from openpyxl import load_workbook
            wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
            for r in wb.worksheets[0].iter_rows(values_only=True):
                rows.append(["" if v is None else (str(int(v)) if isinstance(v, float) and v == int(v) and abs(v) < 1e15 else str(v)) for v in r])
        except Exception:                                          # noqa: BLE001
            raise HTTPException(422, "Excel dosyası okunamadı; .xlsx ya da CSV olarak kaydedin")
    else:
        try:
            txt = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            txt = raw.decode("cp1254", "replace")
        ilk = txt.split("\n", 1)[0]
        d = max(";,\t", key=lambda c: ilk.count(c))
        rows = [r for r in csv.reader(io.StringIO(txt), delimiter=d)]
    rows = [r for r in rows if any(str(x).strip() for x in r)]
    if len(rows) < 2:
        raise HTTPException(422, "Dosyada başlık satırı ve en az bir ürün satırı olmalı")
    head = [str(h).strip() for h in rows[0]]
    if len(rows) - 1 > MAX_ROWS:
        raise HTTPException(422, "En fazla %d satır yüklenebilir (dosyada %d var)" % (MAX_ROWS, len(rows) - 1))
    return head, [dict(zip(head, [str(x).strip() for x in r] + [""] * (len(head) - len(r)))) for r in rows[1:]]


def _hucre(satir, eslesme, alan):
    h = eslesme.get(alan)
    return (satir.get(h, "") if h else "").strip()


def _barkod(v):
    if v and _SCI.match(v.strip()):
        raise HTTPException(422, "Barkod bilimsel gösterimde (%s); Excel'de hücreyi Metin biçimine çevirip yeniden yazın" % v)
    return v


def kur(satirlar, eslesme):
    """Satırları ürün gruplarına çevir: [(ilk_satır_no, ürün_alanları, hata)]. Hata varsa ürün None."""
    gruplar, sira = {}, []
    for i, s in enumerate(satirlar, start=2):
        g = _hucre(s, eslesme, "group")
        anahtar = ("g:" + g) if g else "r:%d" % i
        if anahtar not in gruplar:
            gruplar[anahtar] = []
            sira.append(anahtar)
        gruplar[anahtar].append((i, s))
    out = []
    for k in sira:
        rows = gruplar[k]
        no, s0 = rows[0]
        try:
            p = {}
            for a in ("name", "sku", "barcode", "cat", "brand", "model", "desc"):
                v = _hucre(s0, eslesme, a)
                if v:
                    p[a] = _barkod(v) if a == "barcode" else v
            for a in ("cost", "price", "sale_price", "vat", "stock"):
                v = _hucre(s0, eslesme, a)
                if v:
                    if urun._num(v, None) is None:
                        raise HTTPException(422, "%s sayı olmalı: %s" % (ETIKET[a], v))
                    p[a] = urun._num(v)
            imgs = []
            for a in ("img1", "img2", "img3", "img4", "img5"):
                for u in re.split(r"[|\s]+", _hucre(s0, eslesme, a)):
                    if u:
                        if not re.match(r"^(https?://|/)", u):
                            raise HTTPException(422, "Görsel bağlantısı http(s):// ile başlamalı: %s" % u[:60])
                        imgs.append(u)
            if imgs:
                p["images"] = imgs
            st = _hucre(s0, eslesme, "status").lower()
            if st:
                p["status"] = "draft" if st in ("taslak", "draft", "pasif", "hayır", "hayir", "0") else "live"
            if _hucre(s0, eslesme, "group"):
                vs = []
                for rno, s in rows:
                    opts = {}
                    for n_, v_ in (("o1n", "o1v"), ("o2n", "o2v")):
                        val = _hucre(s, eslesme, v_)
                        if val:
                            ad = _hucre(s, eslesme, n_) or (eslesme.get(v_) if eslesme.get(v_) else "Seçenek")
                            opts[ad] = val
                    if not opts:
                        raise HTTPException(422, "Satır %d: aynı Ana stok kodlu satırlarda Seçenek değeri (Renk/Beden) gerekli" % rno)
                    sk = _hucre(s, eslesme, "sku")
                    bc = _barkod(_hucre(s, eslesme, "barcode"))
                    vs.append({"opts": opts, "sku": sk, "barcode": bc, "stock": urun._int(urun._num(_hucre(s, eslesme, "stock"))),
                               "price": urun._num(_hucre(s, eslesme, "price")), "sale_price": urun._num(_hucre(s, eslesme, "sale_price"))})
                p["variants"] = vs
                p["sku"] = _hucre(s0, eslesme, "group")
                p.pop("barcode", None)
                p.pop("stock", None)
            out.append((no, p, ""))
        except HTTPException as e:
            out.append((no, None, str(e.detail)))
    return out


def register(api_router, db, deps):
    adm = Depends(deps["require_admin"])

    async def is_(jid):
        j = await db.yp_import_jobs.find_one({"id": jid}, {"_id": 0})
        if not j:
            raise HTTPException(404, "Yükleme oturumu bulunamadı; dosyayı yeniden seçin")
        return j

    @api_router.get("/yp/products/import/template")
    async def sablon(_: dict = adm):
        mk = [b["name"] async for b in db.brands.find({"is_active": {"$ne": False}}, {"_id": 0, "name": 1}).sort("name", 1)]
        kt = sorted({str(x) for x in await db.yp_products.distinct("cat") if x})[:300]
        try:
            xl = base64.b64encode(sablon_xlsx(mk, kt)).decode()
        except Exception:                                          # noqa: BLE001
            xl = ""
        return {"ok": True, "name": "urun-sablonu.csv", "xlsx": xl, "xlsx_name": "urun-yukleme-sablonu.xlsx", "csv": sablon_csv(), "alanlar": [{"alan": a, "baslik": b} for a, b, _x in ALAN]}

    @api_router.post("/yp/products/import/parse")
    async def parse(payload: dict, _: dict = adm):
        data = str(payload.get("data") or "")
        if "," in data[:100] and data.startswith("data:"):
            data = data.split(",", 1)[1]
        try:
            raw = base64.b64decode(data, validate=False)
        except Exception:                                          # noqa: BLE001
            raise HTTPException(422, "Dosya okunamadı")
        head, rows = oku(raw, str(payload.get("name") or ""))
        jid = uuid.uuid4().hex[:12]
        await db.yp_import_jobs.delete_many({"at_ts": {"$lt": time.time() - 6 * 3600}})
        await db.yp_import_jobs.insert_one({"id": jid, "name": str(payload.get("name") or "")[:120], "head": head, "rows": rows,
                                            "state": "yuklendi", "at_ts": time.time()})
        return {"ok": True, "job": jid, "headers": head, "count": len(rows), "mapping": oto_esle(head),
                "sample": rows[:3], "fields": [{"alan": a, "baslik": b} for a, b, _x in ALAN]}

    async def planla(j, payload):
        es = {a: h for a, h in (payload.get("mapping") or {}).items() if a in ETIKET and h in j["head"]}
        mod = payload.get("mode") if payload.get("mode") in ("ekle", "guncelle", "ikisi") else "ikisi"
        anahtar = "barcode" if payload.get("key") == "barcode" else "sku"
        if "name" not in es and mod != "guncelle":
            raise HTTPException(422, "«Ürün adı» sütununu eşleyin")
        if anahtar not in es and (mod != "ekle"):
            raise HTTPException(422, "Güncelleme için «%s» sütununu eşleyin" % ETIKET[anahtar])
        plan, hatalar, gorulen = [], [], set()
        for no, p, hata in kur(j["rows"], es):
            if hata:
                hatalar.append({"satir": no, "hata": hata})
                continue
            kv = (p.get(anahtar) or "").strip()
            old = await db.yp_products.find_one({anahtar: kv}, {"_id": 0}) if kv else None
            if kv and kv in gorulen:
                hatalar.append({"satir": no, "hata": "Dosyada aynı %s birden fazla ürün satırında: %s" % (ETIKET[anahtar].lower(), kv)})
                continue
            if kv:
                gorulen.add(kv)
            if old and mod == "ekle":
                hatalar.append({"satir": no, "hata": "Bu %s ile ürün zaten var (%s); «ekle» modunda atlandı" % (ETIKET[anahtar].lower(), kv)})
                continue
            if not old and mod == "guncelle":
                hatalar.append({"satir": no, "hata": "Güncellenecek ürün bulunamadı (%s)" % (kv or "boş")})
                continue
            try:
                if old:
                    m = dict(old)
                    m.update({k: v for k, v in p.items() if v not in ("", None) and not (k == "variants" and not v)})
                    if "variants" in p and old.get("variants"):                 # mevcut seçenekleri stok koduyla eşleyip kimliklerini koru
                        by = {v.get("sku"): v for v in old["variants"] if v.get("sku")}
                        for v in p["variants"]:
                            o = by.get(v.get("sku"))
                            if o:
                                v["id"] = o["id"]
                                v["image"] = o.get("image", "")
                    o2 = urun.clean(m, old)
                    plan.append({"no": no, "tur": "guncelle", "id": old["id"], "doc": o2, "ad": o2["name"]})
                else:
                    o2 = urun.clean(p)
                    plan.append({"no": no, "tur": "ekle", "doc": o2, "ad": o2["name"]})
            except HTTPException as e:
                hatalar.append({"satir": no, "hata": str(e.detail)})
        # dosya içi ve veri tabanında stok kodu/barkod çakışması (yeni ürünler)
        sk = {}
        for pl in plan:
            s_ = pl["doc"].get("sku")
            if s_ and pl["tur"] == "ekle":
                if s_ in sk:
                    hatalar.append({"satir": pl["no"], "hata": "Stok kodu dosyada tekrar ediyor: " + s_})
                    pl["atla"] = True
                sk[s_] = 1
                if await db.yp_products.find_one({"sku": s_}, {"_id": 1}):
                    hatalar.append({"satir": pl["no"], "hata": "Bu stok kodu başka üründe kullanılıyor: " + s_})
                    pl["atla"] = True
        plan = [x for x in plan if not x.get("atla")]
        return plan, hatalar

    @api_router.post("/yp/products/import/preview")
    async def preview(payload: dict, _: dict = adm):
        j = await is_(str(payload.get("job") or ""))
        plan, hatalar = await planla(j, payload)
        await db.yp_import_jobs.update_one({"id": j["id"]}, {"$set": {"opts": {"mapping": payload.get("mapping") or {}, "mode": payload.get("mode"), "key": payload.get("key")},
                                                                      "errors": hatalar, "state": "onizleme"}})
        return {"ok": True, "ekle": sum(1 for x in plan if x["tur"] == "ekle"), "guncelle": sum(1 for x in plan if x["tur"] == "guncelle"),
                "hata": len(hatalar), "errors": hatalar[:30], "ornek": [{"satir": x["no"], "tur": x["tur"], "ad": x["ad"]} for x in plan[:8]]}

    @api_router.post("/yp/products/import/run")
    async def run(payload: dict, user: dict = adm):
        j = await is_(str(payload.get("job") or ""))
        if j.get("state") == "bitti":
            raise HTTPException(409, "Bu yükleme zaten tamamlandı")
        if j.get("state") != "onizleme":
            raise HTTPException(409, "Önce önizleme yapın")
        plan, hatalar = await planla(j, j["opts"])
        ids, ekle, gunc = [], 0, 0
        for x in plan:
            doc = x["doc"]
            if x["tur"] == "ekle":
                doc.update({"id": uuid.uuid4().hex[:12], "low_at": 5, "created_at": urun._now(), "updated_at": urun._now(), "by": user.get("name", "")})
                if await db.yp_products.find_one({"slug": doc["slug"]}, {"_id": 1}):
                    doc["slug"] = (doc["slug"] + "-" + doc["id"][:4])[:80]
                await db.yp_products.insert_one(dict(doc))
                ids.append(doc["id"])
                ekle += 1
            else:
                doc["updated_at"] = urun._now()
                doc.pop("slug", None) if False else None
                await db.yp_products.update_one({"id": x["id"]}, {"$set": doc})
                ids.append(x["id"])
                gunc += 1
        for bn in {str(x["doc"].get("brand") or "").strip() for x in plan} - {""}:   # listede olmayan markalar otomatik eklenir
            if not await db.brands.find_one({"name": {"$regex": "^" + re.escape(bn) + "$", "$options": "i"}}, {"_id": 1}):
                await db.brands.insert_one({"id": str(uuid.uuid4()), "name": bn, "logo_url": "", "is_active": True, "created_at": urun._now()})
        for pid in ids:                                                  # aynayı yükleme bitince, ürün başına bir kez
            await urun._ayna(db, pid)
        await db.yp_import_jobs.update_one({"id": j["id"]}, {"$set": {"state": "bitti", "errors": hatalar, "rows": [], "sonuc": {"ekle": ekle, "guncelle": gunc}}})
        return {"ok": True, "ekle": ekle, "guncelle": gunc, "hata": len(hatalar), "job": j["id"]}

    @api_router.get("/yp/products/import/{jid}/errors")
    async def hatalar_csv(jid: str, _: dict = adm):
        j = await is_(jid)
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_ALL)
        w.writerow(["Satır", "Hata"])
        for e in j.get("errors") or []:
            w.writerow([e["satir"], e["hata"]])
        return {"ok": True, "name": "yukleme-hatalari.csv", "csv": "﻿" + buf.getvalue(), "n": len(j.get("errors") or [])}
