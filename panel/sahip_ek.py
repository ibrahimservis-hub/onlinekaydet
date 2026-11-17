# -*- coding: utf-8 -*-
"""Platform sahibi için: talepler (düzenle/not/sil/toplu/CSV, firmaya bağlantı), form özeti, platform muhasebesi."""
import csv
import io
import re
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import Depends, HTTPException
from fastapi.responses import PlainTextResponse

import tenant
from leads import STATUSES, _norm_phone

GIDER_KAT = ["Sunucu / alan adı", "Reklam", "SMS", "Maaş", "Vergi / SGK", "Yazılım / abonelik", "Ofis", "Diğer"]
GELIR_KAT = ["Firma aboneliği", "Kurulum", "Özel tasarım", "Bayilik", "Diğer"]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _f(v):
    try:
        v = str(v).strip().replace(" ", "")
        if "," in v:
            v = v.replace(".", "").replace(",", ".")
        return float(v)
    except Exception:       # noqa: BLE001
        return 0.0


def register(api_router, db, deps):
    adm = Depends(deps["require_admin"])

    def need_main():
        if tenant.current():
            raise HTTPException(403, "Bu işlem yalnız ana yönetim içindir")

    def M():
        return db.main()

    async def firm_map():
        """telefon ve firma adına göre firma eşlemesi (demo ve gerçek)."""
        by_phone, by_name = {}, {}
        for f in await M().firms.find({}, {"_id": 0, "id": 1, "name": 1, "phone": 1, "demo_phone": 1, "status": 1, "demo": 1, "expires_at": 1, "created_at": 1}).to_list(20000):
            for p in (f.get("demo_phone"), f.get("phone")):
                p = _norm_phone(p)
                if p:
                    by_phone.setdefault(p, f)
            by_name.setdefault((f.get("name") or "").strip().lower(), f)
        return by_phone, by_name

    def baglan(l, bp, bn):
        f = bp.get(l.get("phone")) or bn.get((l.get("firm") or "").strip().lower())
        if f:
            l["firm_id"], l["firm_name"], l["firm_demo"] = f["id"], f["name"], bool(f.get("demo"))
            l["firm_durum"] = "doldu" if (f.get("expires_at") or "9") < _now() else f.get("status", "aktif")
        return l

    # ------------------------------------------------------------------ talepler
    @api_router.get("/admin/talepler")
    async def talepler(durum: str = "", form: str = "", q: str = "", _: dict = adm):
        need_main()
        flt = {}
        if durum in STATUSES:
            flt["status"] = durum
        if form:
            flt["form"] = form
        if q:
            rx = {"$regex": re.escape(q), "$options": "i"}
            flt["$or"] = [{"name": rx}, {"phone": rx}, {"firm": rx}, {"note": rx}]
        rows = await M().leads.find(flt, {"_id": 0}).sort("created_at", -1).to_list(2000)
        bp, bn = await firm_map()
        rows = [baglan(l, bp, bn) for l in rows]
        counts = {s: await M().leads.count_documents({"status": s}) for s in STATUSES}
        formlar = {}
        for l in await M().leads.find({}, {"_id": 0, "form": 1}).to_list(50000):
            k = l.get("form") or "(belirsiz)"
            formlar[k] = formlar.get(k, 0) + 1
        return {"leads": rows, "counts": counts, "formlar": dict(sorted(formlar.items(), key=lambda x: -x[1]))}

    @api_router.put("/admin/talepler/{lid}")
    async def talep_duzenle(lid: str, p: dict, _: dict = adm):
        need_main()
        up = {}
        if "status" in p:
            if p["status"] not in STATUSES:
                raise HTTPException(422, "Durum geçersiz")
            up["status"] = p["status"]
        if "name" in p:
            n = " ".join(str(p["name"]).split())[:80]
            if len(n) < 2:
                raise HTTPException(422, "Ad en az 2 karakter")
            up["name"] = n
        if "phone" in p:
            ph = _norm_phone(p["phone"])
            if not ph:
                raise HTTPException(422, "Telefon geçersiz (05xx xxx xx xx)")
            up["phone"] = ph
        for k, n in (("firm", 100), ("sector", 40), ("city", 60), ("note", 1000)):
            if k in p:
                up[k] = str(p[k] or "").strip()[:n]
        if not up:
            raise HTTPException(422, "Değişiklik yok")
        up["updated_at"] = _now()
        r = await M().leads.update_one({"id": lid}, {"$set": up})
        if not r.matched_count:
            raise HTTPException(404, "Talep bulunamadı")
        return {"ok": True}

    @api_router.post("/admin/talepler/{lid}/not")
    async def talep_not(lid: str, p: dict, me: dict = adm):
        need_main()
        t = str(p.get("metin") or "").strip()[:500]
        if not t:
            raise HTTPException(422, "Not boş olamaz")
        n = {"id": uuid.uuid4().hex[:10], "metin": t, "at": _now(), "kim": me.get("name") or me.get("email") or ""}
        r = await M().leads.update_one({"id": lid}, {"$push": {"notlar": n}})
        if not r.matched_count:
            raise HTTPException(404, "Talep bulunamadı")
        return n

    @api_router.delete("/admin/talepler/{lid}/not/{nid}")
    async def talep_not_sil(lid: str, nid: str, _: dict = adm):
        need_main()
        await M().leads.update_one({"id": lid}, {"$pull": {"notlar": {"id": nid}}})
        return {"ok": True}

    @api_router.get("/admin/firms/{fid}/notlar")
    async def firma_notlar(fid: str, _: dict = adm):
        need_main()
        return await M().firm_notes.find({"fid": fid}, {"_id": 0}).sort("at", -1).to_list(200)

    @api_router.post("/admin/firms/{fid}/notlar")
    async def firma_not_ekle(fid: str, p: dict, me: dict = adm):
        need_main()
        if not await M().firms.find_one({"id": fid}):
            raise HTTPException(404, "Firma bulunamadı")
        t = str(p.get("metin") or "").strip()[:500]
        if not t:
            raise HTTPException(422, "Not boş olamaz")
        n = {"id": uuid.uuid4().hex[:10], "fid": fid, "metin": t, "adim": str(p.get("adim") or "")[:60],
             "at": _now(), "kim": me.get("name") or me.get("email") or ""}
        await M().firm_notes.insert_one(dict(n))
        return n

    @api_router.delete("/admin/firms/{fid}/notlar/{nid}")
    async def firma_not_sil(fid: str, nid: str, _: dict = adm):
        need_main()
        await M().firm_notes.delete_one({"id": nid, "fid": fid})
        return {"ok": True}

    @api_router.delete("/admin/talepler/{lid}")
    async def talep_sil(lid: str, _: dict = adm):
        need_main()
        r = await M().leads.delete_one({"id": lid})
        if not r.deleted_count:
            raise HTTPException(404, "Talep bulunamadı")
        return {"ok": True}

    @api_router.post("/admin/talepler/toplu")
    async def talep_toplu(p: dict, _: dict = adm):
        need_main()
        ids = [str(i) for i in (p.get("ids") or [])][:500]
        if not ids:
            raise HTTPException(422, "Kayıt seçin")
        if p.get("islem") == "sil":
            r = await M().leads.delete_many({"id": {"$in": ids}})
            return {"ok": True, "adet": r.deleted_count}
        if p.get("islem") == "durum" and p.get("durum") in STATUSES:
            r = await M().leads.update_many({"id": {"$in": ids}}, {"$set": {"status": p["durum"], "updated_at": _now()}})
            return {"ok": True, "adet": r.modified_count}
        raise HTTPException(422, "İşlem geçersiz")

    @api_router.get("/admin/talepler.csv")
    async def talep_csv(form: str = "", _: dict = adm):
        need_main()
        rows = await M().leads.find({"form": form} if form else {}, {"_id": 0}).sort("created_at", -1).to_list(20000)
        o = io.StringIO()
        w = csv.writer(o, delimiter=";")
        w.writerow(["Tarih", "Ad", "Telefon", "Firma", "Sektör", "Form", "Durum", "Kaynak", "Sayfa", "Ekstra", "Notlar"])
        for l in rows:
            s = l.get("src") or {}
            w.writerow([l.get("created_at", "")[:16].replace("T", " "), l.get("name", ""), "0" + str(l.get("phone", "")), l.get("firm", ""), l.get("sector", ""),
                        l.get("form", ""), l.get("status", ""), s.get("utm_source") or s.get("ref") or "doğrudan", s.get("page", ""),
                        "; ".join("%s: %s" % kv for kv in (l.get("extra") or {}).items()), " | ".join(n["metin"] for n in l.get("notlar", [])) or l.get("note", "")])
        return PlainTextResponse("﻿" + o.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="talepler.csv"'})

    # ------------------------------------------------------------------ platform muhasebesi
    def ay_ok(a):
        return a if re.fullmatch(r"\d{4}-\d{2}", a or "") else ""

    @api_router.get("/admin/muhasebe")
    async def muhasebe(ay: str = "", _: dict = adm):
        need_main()
        ay = ay_ok(ay) or datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3))).strftime("%Y-%m")
        firmalar = {f["id"]: f["name"] for f in await M().firms.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(20000)}
        kayit = []
        for p in await M().firm_payments.find({}, {"_id": 0}).to_list(50000):
            kayit.append({"id": p["id"], "kaynak": "odeme", "tur": "gelir", "tutar": p["amount"], "kategori": "Firma aboneliği", "aciklama": "%s · %s%s" % (firmalar.get(p["firm_id"], "silinmiş firma"), p.get("method", ""), (" · " + p["note"]) if p.get("note") else ""),
                          "tarih": p["at"][:10], "firma": firmalar.get(p["firm_id"], "")})
        for e in await M().platform_ledger.find({}, {"_id": 0}).to_list(50000):
            kayit.append({**e, "kaynak": "manuel"})
        aylar = {}
        for k in kayit:
            a = aylar.setdefault(k["tarih"][:7], {"gelir": 0.0, "gider": 0.0})
            a[k["tur"]] += k["tutar"]
        seri = []
        d = datetime.now(timezone.utc).replace(day=1)
        for _i in range(12):
            key = d.strftime("%Y-%m")
            a = aylar.get(key, {"gelir": 0.0, "gider": 0.0})
            seri.append({"ay": key, "gelir": round(a["gelir"], 2), "gider": round(a["gider"], 2), "net": round(a["gelir"] - a["gider"], 2)})
            d = (d - timedelta(days=1)).replace(day=1)
        secili = sorted([k for k in kayit if k["tarih"].startswith(ay)], key=lambda x: x["tarih"], reverse=True)
        kat = {}
        for k in secili:
            kk = (k["tur"], k["kategori"])
            kat[kk] = round(kat.get(kk, 0) + k["tutar"], 2)
        g, gi = sum(k["tutar"] for k in secili if k["tur"] == "gelir"), sum(k["tutar"] for k in secili if k["tur"] == "gider")
        return {"ay": ay, "gelir": round(g, 2), "gider": round(gi, 2), "net": round(g - gi, 2), "kayitlar": secili, "seri": list(reversed(seri)),
                "kategoriler": [{"tur": t, "kategori": c, "tutar": v} for (t, c), v in sorted(kat.items())], "gelir_kat": GELIR_KAT, "gider_kat": GIDER_KAT}

    @api_router.post("/admin/muhasebe")
    async def muh_ekle(p: dict, me: dict = adm):
        need_main()
        tur = p.get("tur")
        if tur not in ("gelir", "gider"):
            raise HTTPException(422, "Tür gelir ya da gider olmalı")
        tutar = round(_f(p.get("tutar")), 2)
        if tutar <= 0:
            raise HTTPException(422, "Tutar 0'dan büyük olmalı")
        tarih = str(p.get("tarih") or "")[:10] or datetime.now(timezone.utc).date().isoformat()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", tarih):
            raise HTTPException(422, "Tarih YYYY-AA-GG olmalı")
        d = {"id": uuid.uuid4().hex[:12], "tur": tur, "tutar": tutar, "kategori": str(p.get("kategori") or "Diğer")[:40], "aciklama": str(p.get("aciklama") or "")[:200],
             "tarih": tarih, "at": _now(), "kim": me.get("name") or me.get("email") or ""}
        await M().platform_ledger.insert_one(dict(d))
        return d

    @api_router.delete("/admin/muhasebe/{eid}")
    async def muh_sil(eid: str, _: dict = adm):
        need_main()
        r = await M().platform_ledger.delete_one({"id": eid})
        if not r.deleted_count:
            raise HTTPException(404, "Kayıt yok (firma ödemeleri abonelik ekranından yönetilir)")
        return {"ok": True}

    @api_router.get("/admin/muhasebe.csv")
    async def muh_csv(ay: str = "", _: dict = adm):
        r = await muhasebe(ay, _)
        o = io.StringIO()
        w = csv.writer(o, delimiter=";")
        w.writerow(["Tarih", "Tür", "Kategori", "Açıklama", "Tutar"])
        for k in reversed(r["kayitlar"]):
            w.writerow([k["tarih"], "Gelir" if k["tur"] == "gelir" else "Gider", k["kategori"], k["aciklama"], ("%.2f" % k["tutar"]).replace(".", ",")])
        return PlainTextResponse("﻿" + o.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="muhasebe-%s.csv"' % r["ay"]})
