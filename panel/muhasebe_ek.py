"""Muhasebe eklentileri: çek-senet portföyü, banka ekstresi (CSV) içe aktarma, TCMB döviz kuru,
mali müşavir için salt-okunur erişim bağlantısı (ay özeti + CSV)."""
import csv
import hashlib
import io
import re
import secrets
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Depends, HTTPException

import tenant
from fastapi.responses import HTMLResponse, PlainTextResponse

CS_DURUM = {
    "alacak": {"portfoy": "Portföyde", "tahsil": "Tahsil edildi", "ciro": "Ciro edildi", "karsiliksiz": "Karşılıksız", "iade": "İade"},
    "borc": {"bekliyor": "Ödenecek", "odendi": "Ödendi", "iptal": "İptal"},
}
KUR_KODLARI = ("USD", "EUR", "GBP", "CHF", "SAR", "RUB", "AUD", "CAD", "JPY")


def _id():
    return uuid.uuid4().hex


def _now():
    return datetime.now(timezone.utc).isoformat()


def _f(v, d=0.0):
    try:
        if isinstance(v, str):
            v = v.strip().replace("₺", "").replace("TL", "").replace(" ", "")
            if "," in v:
                v = v.replace(".", "").replace(",", ".")
        return float(v)
    except Exception:       # noqa: BLE001
        return d


def _tarih(s):
    s = str(s or "").strip()
    for fm in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[:19] if "T" in fm else s[:10], fm).date().isoformat()
        except Exception:   # noqa: BLE001
            continue
    return ""


def parse_tcmb(data: bytes):
    root = ET.fromstring(data)
    out = {}
    for c in root.iter("Currency"):
        k = c.get("Kod") or c.get("CurrencyCode")
        if k in KUR_KODLARI:
            unit = _f(c.findtext("Unit"), 1) or 1
            al, sat = _f(c.findtext("ForexBuying")), _f(c.findtext("ForexSelling"))
            if al:
                out[k] = {"alis": round(al / unit, 4), "satis": round((sat or al) / unit, 4)}
    return {"tarih": root.get("Tarih") or root.get("Date") or "", "kurlar": out}


def parse_ekstre(text: str):
    """Banka ekstresi CSV: tarih, açıklama, tutar (veya borç/alacak) sütunlarını başlıktan tanır."""
    text = (text or "").lstrip("﻿")
    if not text.strip():
        raise HTTPException(422, "Dosya boş")
    sep = max((";", ",", "\t"), key=lambda s: text.split("\n", 1)[0].count(s))
    rows = list(csv.reader(io.StringIO(text), delimiter=sep))
    if len(rows) < 2:
        raise HTTPException(422, "Ekstrede satır bulunamadı")
    hd = [re.sub(r"[^a-zçğıöşü0-9]", "", h.lower().replace("İ", "i").replace("I", "ı")) for h in rows[0]]

    def col(*names):
        for i, h in enumerate(hd):
            if any(n in h for n in names):
                return i
        return -1
    ct, ca, cm = col("tarih", "date"), col("açıklama", "aciklama", "description", "işlem", "islem"), col("tutar", "amount")
    cb, cal = col("borç", "borc", "çıkış", "cikis"), col("alacak", "giriş", "giris")
    if ct < 0 or (cm < 0 and cb < 0 and cal < 0):
        raise HTTPException(422, "Başlık satırında 'Tarih' ve 'Tutar' (ya da Borç/Alacak) sütunları olmalı")
    out = []
    for r in rows[1:]:
        if not r or len(r) <= ct:
            continue
        d = _tarih(r[ct])
        if not d:
            continue
        if cm >= 0 and len(r) > cm and r[cm].strip():
            tutar = _f(r[cm])
        else:
            tutar = (_f(r[cal]) if cal >= 0 and len(r) > cal else 0) - abs(_f(r[cb]) if cb >= 0 and len(r) > cb else 0)
        if not tutar:
            continue
        out.append({"date": d, "description": (r[ca].strip() if ca >= 0 and len(r) > ca else "")[:200] or "Banka hareketi", "amount": round(tutar, 2)})
    if not out:
        raise HTTPException(422, "Geçerli satır bulunamadı (tarih biçimi: 31.12.2026 veya 2026-12-31)")
    return out


def register(api_router, db, deps):
    adm = Depends(deps["require_admin"])

    # ---------------------------------------------------------------- çek / senet
    def clean_cs(p, cur=None):
        cur = cur or {}
        t = str(p.get("type", cur.get("type", "cek")))
        t = t if t in ("cek", "senet") else "cek"
        d = str(p.get("direction", cur.get("direction", "alacak")))
        d = d if d in ("alacak", "borc") else "alacak"
        amt = round(_f(p.get("amount", cur.get("amount", 0))), 2)
        if amt <= 0:
            raise HTTPException(422, "Tutar 0'dan büyük olmalı")
        due = _tarih(p.get("due", cur.get("due", "")))
        if not due:
            raise HTTPException(422, "Vade tarihi gerekli")
        party = str(p.get("party", cur.get("party", ""))).strip()[:120]
        if not party:
            raise HTTPException(422, "Kişi / firma adı gerekli")
        return {"type": t, "direction": d, "party": party, "no": str(p.get("no", cur.get("no", ""))).strip()[:40],
                "bank": str(p.get("bank", cur.get("bank", ""))).strip()[:80], "amount": amt, "due": due,
                "issued": _tarih(p.get("issued", cur.get("issued", ""))), "note": str(p.get("note", cur.get("note", ""))).strip()[:300]}

    @api_router.get("/yp/cek-senet")
    async def cs_list(durum: str = "", yon: str = "", _: dict = adm):
        q = {}
        if yon in ("alacak", "borc"):
            q["direction"] = yon
        rows = await db.cek_senet.find(q, {"_id": 0}).sort("due", 1).to_list(5000)
        if durum:
            rows = [r for r in rows if r["status"] == durum]
        bugun = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3))).date()
        ozet = {"portfoy_alacak": 0.0, "odenecek_borc": 0.0, "geciken": 0, "yedi_gun": 0, "yedi_gun_tutar": 0.0}
        for r in rows:
            acik = r["status"] in ("portfoy", "bekliyor")
            vade = datetime.fromisoformat(r["due"]).date()
            r["kalan_gun"] = (vade - bugun).days
            r["durum_ad"] = CS_DURUM[r["direction"]].get(r["status"], r["status"])
            if not acik:
                continue
            ozet["portfoy_alacak" if r["direction"] == "alacak" else "odenecek_borc"] += r["amount"]
            if r["kalan_gun"] < 0:
                ozet["geciken"] += 1
            elif r["kalan_gun"] <= 7:
                ozet["yedi_gun"] += 1
                ozet["yedi_gun_tutar"] += r["amount"]
        for k in ("portfoy_alacak", "odenecek_borc", "yedi_gun_tutar"):
            ozet[k] = round(ozet[k], 2)
        return {"rows": rows, "ozet": ozet, "durumlar": CS_DURUM}

    @api_router.post("/yp/cek-senet")
    async def cs_add(payload: dict, _: dict = adm):
        doc = clean_cs(payload)
        doc.update({"id": _id(), "status": "portfoy" if doc["direction"] == "alacak" else "bekliyor", "created_at": _now(), "history": []})
        await db.cek_senet.insert_one(dict(doc))
        doc.pop("_id", None)
        return doc

    @api_router.put("/yp/cek-senet/{cid}")
    async def cs_upd(cid: str, payload: dict, _: dict = adm):
        cur = await db.cek_senet.find_one({"id": cid}, {"_id": 0})
        if not cur:
            raise HTTPException(404, "Kayıt bulunamadı")
        if cur["status"] in ("tahsil", "odendi"):
            raise HTTPException(409, "Kasaya işlenmiş kayıt değiştirilemez")
        upd = clean_cs(payload, cur)
        await db.cek_senet.update_one({"id": cid}, {"$set": upd})
        return {**cur, **upd}

    @api_router.delete("/yp/cek-senet/{cid}")
    async def cs_del(cid: str, _: dict = adm):
        cur = await db.cek_senet.find_one({"id": cid}, {"_id": 0})
        if not cur:
            raise HTTPException(404, "Kayıt bulunamadı")
        if cur["status"] in ("tahsil", "odendi"):
            raise HTTPException(409, "Kasaya işlenmiş kayıt silinemez")
        await db.cek_senet.delete_one({"id": cid})
        return {"ok": True}

    @api_router.post("/yp/cek-senet/{cid}/durum")
    async def cs_durum(cid: str, payload: dict, user: dict = adm):
        cur = await db.cek_senet.find_one({"id": cid}, {"_id": 0})
        if not cur:
            raise HTTPException(404, "Kayıt bulunamadı")
        yeni = str(payload.get("status", ""))
        if yeni not in CS_DURUM[cur["direction"]]:
            raise HTTPException(422, "Geçersiz durum")
        if cur["status"] in ("tahsil", "odendi"):
            raise HTTPException(409, "Kasaya işlenmiş kayıt tekrar değiştirilemez")
        upd = {"status": yeni, "history": (cur.get("history") or []) + [{"status": yeni, "at": _now()}]}
        if yeni in ("tahsil", "odendi"):
            acc = payload.get("account_id")
            if not acc or not await db.accounts.find_one({"id": acc}, {"_id": 1}):
                raise HTTPException(422, "Kasa/banka hesabı seçin")
            gelir = cur["direction"] == "alacak"
            tx = {"id": _id(), "type": "gelir" if gelir else "gider", "amount": cur["amount"], "account_id": acc,
                  "description": "%s %s — %s" % ("Çek" if cur["type"] == "cek" else "Senet", cur.get("no") or "", cur["party"]),
                  "date": _tarih(payload.get("date")) or datetime.now(timezone.utc).date().isoformat(),
                  "category": "Çek/Senet tahsilatı" if gelir else "Çek/Senet ödemesi", "created_by": user.get("id"), "cek_senet_id": cid}
            await db.cash_transactions.insert_one(tx)
            upd["cash_tx"] = tx["id"]
        await db.cek_senet.update_one({"id": cid}, {"$set": upd})
        return {"ok": True, **upd}

    # ---------------------------------------------------------------- banka ekstresi
    @api_router.post("/yp/banka/ekstre")
    async def ekstre(payload: dict, user: dict = adm):
        acc = payload.get("account_id")
        a = await db.accounts.find_one({"id": acc}, {"_id": 0})
        if not a:
            raise HTTPException(422, "Hesap seçin")
        rows = parse_ekstre(str(payload.get("csv") or ""))
        yeni = tekrar = 0
        for r in rows:
            h = hashlib.sha1(("%s|%s|%s|%s" % (acc, r["date"], r["amount"], r["description"])).encode()).hexdigest()
            if await db.cash_transactions.find_one({"ekstre_hash": h}, {"_id": 1}):
                tekrar += 1
                continue
            await db.cash_transactions.insert_one({
                "id": _id(), "type": "gelir" if r["amount"] > 0 else "gider", "amount": abs(r["amount"]), "account_id": acc,
                "description": r["description"], "date": r["date"], "category": "Banka ekstresi", "created_by": user.get("id"),
                "ekstre_hash": h, "source": "ekstre"})
            yeni += 1
        return {"eklenen": yeni, "tekrar_atlanan": tekrar, "toplam": len(rows)}

    # ---------------------------------------------------------------- döviz kuru
    @api_router.get("/yp/kur")
    async def kur(yenile: bool = False, _: dict = adm):
        c = await db.yp_ayar.find_one({"id": "kur"}, {"_id": 0}) or {}
        taze = c.get("at") and datetime.fromisoformat(c["at"]) > datetime.now(timezone.utc) - timedelta(hours=3)
        if c and taze and not yenile:
            return c
        try:
            import asyncio
            import xml_ice
            data = await asyncio.to_thread(xml_ice.fetch_bytes, "https://www.tcmb.gov.tr/kurlar/today.xml", 15)
            p = parse_tcmb(data)
            c = {"id": "kur", "at": _now(), "kaynak": "TCMB", **p}
            await db.yp_ayar.update_one({"id": "kur"}, {"$set": c}, upsert=True)
        except Exception:       # noqa: BLE001
            if not c:
                raise HTTPException(502, "Kur bilgisi şu an alınamadı; biraz sonra tekrar deneyin")
            c["eski"] = True
        return c

    @api_router.get("/yp/kur/cevir")
    async def cevir(tutar: float, para: str = "USD", _: dict = adm):
        c = await kur(False, _)
        k = (c.get("kurlar") or {}).get(para.upper())
        if not k:
            raise HTTPException(404, "Bu para birimi yok")
        return {"tutar": tutar, "para": para.upper(), "kur": k["satis"], "tl": round(tutar * k["satis"], 2)}

    # ---------------------------------------------------------------- mali müşavir erişimi
    @api_router.get("/yp/musavir")
    async def mus_list(_: dict = adm):
        rows = await db.musavir_erisim.find({}, {"_id": 0, "token_hash": 0}).sort("created_at", -1).to_list(50)
        return {"rows": rows}

    @api_router.post("/yp/musavir")
    async def mus_new(payload: dict, _: dict = adm):
        gun = max(1, min(365, int(_f(payload.get("gun"), 30))))
        tok = secrets.token_urlsafe(24)
        doc = {"id": _id(), "ad": str(payload.get("ad") or "Mali müşavir").strip()[:80],
               "token_hash": hashlib.sha256(tok.encode()).hexdigest(), "created_at": _now(),
               "bitis": (datetime.now(timezone.utc) + timedelta(days=gun)).isoformat(), "iptal": False, "son_giris": ""}
        await db.musavir_erisim.insert_one(dict(doc))
        return {"id": doc["id"], "ad": doc["ad"], "bitis": doc["bitis"], "yol": "/api/public/musavir/" + tenant.public_token(tok),
                "not": "Bu bağlantı yalnızca şimdi gösterilir; kaybederseniz yenisini oluşturun."}

    @api_router.delete("/yp/musavir/{mid}")
    async def mus_del(mid: str, _: dict = adm):
        await db.musavir_erisim.update_one({"id": mid}, {"$set": {"iptal": True}})
        return {"ok": True}

    async def mus_dogrula(tok):
        h = hashlib.sha256(tok.encode()).hexdigest()
        d = await db.musavir_erisim.find_one({"token_hash": h, "iptal": False}, {"_id": 0})
        if not d or datetime.fromisoformat(d["bitis"]) < datetime.now(timezone.utc):
            raise HTTPException(404, "Bağlantı geçersiz veya süresi dolmuş")
        await db.musavir_erisim.update_one({"id": d["id"]}, {"$set": {"son_giris": _now()}})
        return d

    async def ay_hareket(ay):
        if not re.match(r"^\d{4}-\d{2}$", ay or ""):
            ay = datetime.now(timezone.utc).strftime("%Y-%m")
        rows = await db.cash_transactions.find({"date": {"$regex": "^" + ay}, "type": {"$in": ["gelir", "gider"]}}, {"_id": 0}).sort("date", 1).to_list(20000)
        return ay, rows

    @api_router.get("/public/musavir/{tok}/ozet")
    async def mus_ozet(tok: str, ay: str = ""):
        await mus_dogrula(tok)
        ay, rows = await ay_hareket(ay)
        gelir = round(sum(r["amount"] for r in rows if r["type"] == "gelir"), 2)
        gider = round(sum(r["amount"] for r in rows if r["type"] == "gider"), 2)
        kat = {}
        for r in rows:
            kk = (r["type"], r.get("category") or "Diğer")
            kat[kk] = round(kat.get(kk, 0) + r["amount"], 2)
        return {"ay": ay, "gelir": gelir, "gider": gider, "net": round(gelir - gider, 2), "adet": len(rows),
                "kategoriler": [{"tur": k[0], "kategori": k[1], "tutar": v} for k, v in sorted(kat.items())]}

    @api_router.get("/public/musavir/{tok}/csv")
    async def mus_csv(tok: str, ay: str = ""):
        await mus_dogrula(tok)
        ay, rows = await ay_hareket(ay)
        o = io.StringIO()
        w = csv.writer(o, delimiter=";")
        w.writerow(["Tarih", "Tür", "Kategori", "Açıklama", "Tutar"])
        for r in rows:
            w.writerow([r["date"][:10], "Gelir" if r["type"] == "gelir" else "Gider", r.get("category", ""), r.get("description", ""),
                        ("%.2f" % r["amount"]).replace(".", ",")])
        return PlainTextResponse("﻿" + o.getvalue(), headers={"Content-Disposition": 'attachment; filename="hareketler-%s.csv"' % ay},
                                 media_type="text/csv; charset=utf-8")

    @api_router.get("/public/musavir/{tok}", response_class=HTMLResponse)
    async def mus_sayfa(tok: str, ay: str = ""):
        await mus_dogrula(tok)
        o = await mus_ozet(tok, ay)
        satir = "".join("<tr><td>%s</td><td>%s</td><td style='text-align:right'>%.2f</td></tr>" % (
            "Gelir" if k["tur"] == "gelir" else "Gider", k["kategori"].replace("<", "&lt;"), k["tutar"]) for k in o["kategoriler"])
        return HTMLResponse(
            "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><meta name=robots content=noindex>"
            "<title>Mali müşavir görünümü</title><body style='font:15px system-ui;max-width:720px;margin:24px auto;padding:0 14px'>"
            "<h2>Mali müşavir görünümü — %s</h2><p>Gelir <b>%.2f ₺</b> · Gider <b>%.2f ₺</b> · Net <b>%.2f ₺</b> (%d hareket)</p>"
            "<form><input name=ay value='%s' pattern='\\d{4}-\\d{2}'> <button>Ay değiştir</button> <a href='%s/csv?ay=%s'>CSV indir</a></form>"
            "<table border=1 cellpadding=6 style='border-collapse:collapse;width:100%%;margin-top:12px'><tr><th>Tür</th><th>Kategori</th><th>Tutar ₺</th></tr>%s</table>"
            "<p style='color:#667;font-size:13px'>Bu sayfa salt okunurdur.</p>" % (
                o["ay"], o["gelir"], o["gider"], o["net"], o["adet"], o["ay"], "/api/public/musavir/" + tok, o["ay"], satir))
