"""Muhasebe+: KDV raporu, bütçe/hedef, banka ekstresi içe aktarma, fatura kayıtları (e-fatura/e-arşiv köprüsü),
muhasebeciye aylık paket (Excel).

NOT: Resmî e-fatura/e-arşiv kesimi bir Özel Entegratör (Paraşüt, Uyumsoft, Foriba, Logo vb.) hesabı gerektirir.
Bu modül faturayı panelde hazırlar ve ayarlanan webhook'a (entegratörün/Make/Zapier adresi) JSON olarak gönderir;
doğrudan GİB bağlantısı yapmaz."""
import csv
import hashlib
import io
import re
import uuid
from collections import defaultdict
from calendar import monthrange
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests
from fastapi import Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response

import notify

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:
    TR = timezone(timedelta(hours=3))

DEFAULTS = {
    "vat_rate": 20.0, "prices_include_vat": True, "expense_vat_default": 20.0,
    "budget": {"monthly_revenue_target": 0.0, "expense_budgets": {}},
    "invoice": {"webhook_url": "", "webhook_headers": "", "prefix": "FT", "default_type": "e-arsiv"},
    "company": {"name": "", "tax_no": "", "tax_office": "", "address": ""},
}
CAT_KEYWORDS = [
    (r"kira", "Kira"), (r"elektrik|enerjisa|tedaş|igdaş|su idare|aski|doğalgaz|dogalgaz|bedaş", "Elektrik / Su / Doğalgaz"),
    (r"turkcell|vodafone|türk telekom|turk telekom|superonline|internet", "İnternet / Telefon"),
    (r"opet|shell|petrol|po\b|bp\b|akaryakıt|akaryakit|total", "Yakıt"), (r"google ads|facebook|meta ads|reklam", "Reklam (Google Ads vb.)"),
    (r"sgk|vergi|kdv|muhtasar|damga", "SGK / Vergi"), (r"maaş|maas", "Maaş"), (r"migros|bim|a101|şok|sok market|yemek|restoran|lokanta", "Yemek"),
    (r"kargo|yurtiçi|yurtici|aras kargo|mng|ptt", "Kargo / Nakliye"), (r"muhasebe|danışman|danisman|mali müşavir", "Muhasebe / Danışmanlık"),
]


def _id():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc).isoformat()


def _day(s):
    return (s or "")[:10]


def month_range(month: Optional[str]):
    now = datetime.now(TR)
    if not month:
        month = now.strftime("%Y-%m")
    y, m = int(month[:4]), int(month[5:7])
    first = f"{y:04d}-{m:02d}-01"
    last = f"{y:04d}-{m:02d}-{monthrange(y, m)[1]:02d}"
    return month, first, last


def split_vat(gross: float, rate: float, included: bool = True):
    if included:
        base = gross / (1 + rate / 100.0)
        return round(base, 2), round(gross - base, 2), round(gross, 2)
    return round(gross, 2), round(gross * rate / 100.0, 2), round(gross * (1 + rate / 100.0), 2)


def parse_amount(v) -> Optional[float]:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d,.\-+()]", "", str(v))
    neg = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = s.strip("()+-")
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if len(s.split(",")[-1]) <= 2 else s.replace(",", "")
    elif "." in s and (s.count(".") > 1 or len(s.split(".")[-1]) == 3):
        s = s.replace(".", "")          # Türkçe biçim: 3.500 = 3500
    try:
        x = float(s)
    except ValueError:
        return None
    return -x if neg else x


def parse_date(v) -> Optional[str]:
    if isinstance(v, datetime):
        return v.date().isoformat()
    s = str(v or "").strip()[:19]
    for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%d.%m.%y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def read_table(raw: bytes, filename: str):
    """CSV/XLSX -> satır listesi (list[list])."""
    if filename.lower().endswith((".xlsx", ".xlsm")):
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
        ws = wb.active
        return [list(r) for r in ws.iter_rows(values_only=True)]
    for enc in ("utf-8-sig", "cp1254", "latin-1"):
        try:
            txt = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    sample = txt[:4000]
    delim = ";" if sample.count(";") >= sample.count(",") else ","
    if sample.count("\t") > max(sample.count(";"), sample.count(",")):
        delim = "\t"
    return [r for r in csv.reader(io.StringIO(txt), delimiter=delim)]


def detect_mapping(rows):
    """Başlık satırını ve sütunları bulur."""
    for hi, r in enumerate(rows[:15]):
        cells = [str(c or "").strip().lower() for c in r]
        def find(*keys):
            for i, c in enumerate(cells):
                if any(k in c for k in keys):
                    return i
            return None
        d = find("tarih", "date")
        desc = find("açıklama", "aciklama", "description", "işlem", "islem", "detay")
        amt = find("tutar", "amount", "miktar")
        deb = find("borç", "borc", "çıkış", "cikis", "debit", "gider")
        cre = find("alacak", "giriş", "giris", "credit", "gelir")
        if d is not None and (amt is not None or deb is not None or cre is not None):
            return {"header_row": hi, "date": d, "desc": desc if desc is not None else d, "amount": amt, "debit": deb, "credit": cre}
    return {"header_row": 0, "date": 0, "desc": 1, "amount": 2, "debit": None, "credit": None}


def suggest_category(desc: str, amount: float):
    d = (desc or "").lower()
    if amount > 0:
        return "gelir", "Diğer Gelir"
    for rx, cat in CAT_KEYWORDS:
        if re.search(rx, d):
            return "gider", cat
    return "gider", "Diğer"


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    async def settings():
        s = (await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}).get("finance_plus") or {}
        out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULTS.items()}
        for k, v in s.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k].update(v)
            else:
                out[k] = v
        return out

    @api_router.get("/finance/plus-settings")
    async def get_settings(_: dict = Depends(require_admin)):
        return await settings()

    @api_router.put("/finance/plus-settings")
    async def put_settings(payload: dict, _: dict = Depends(require_admin)):
        cur = await settings()
        for k in DEFAULTS:
            if k in payload:
                if isinstance(DEFAULTS[k], dict):
                    cur[k].update(payload[k] or {})
                else:
                    cur[k] = payload[k]
        await db.app_settings.update_one({"_id": "global"}, {"$set": {"finance_plus": cur}}, upsert=True)
        return cur

    # ============================================================ KDV
    async def vat_for(month):
        s = await settings()
        month, a, b = month_range(month)
        txs = [t for t in await db.cash_transactions.find({}, {"_id": 0}).to_list(200000) if a <= _day(t.get("date")) <= b]
        inc = [t for t in txs if t["type"] == "gelir"]
        exp = [t for t in txs if t["type"] == "gider"]
        rate = float(s["vat_rate"])
        g_inc = sum(t["amount"] for t in inc)
        base, vat, _ = split_vat(g_inc, rate, s["prices_include_vat"])
        invoiced_jobs = {i["job_id"] for i in await db.invoices.find({"status": {"$ne": "iptal"}}, {"_id": 0, "job_id": 1}).to_list(50000) if i.get("job_id")}
        inc_invoiced = sum(t["amount"] for t in inc if t.get("job_id") in invoiced_jobs)
        rows_in = []
        for t in inc:
            bs, v, _g = split_vat(t["amount"], rate, s["prices_include_vat"])
            rows_in.append({"date": _day(t["date"]), "description": t.get("description", ""), "category": t.get("category", ""), "gross": t["amount"], "base": bs, "vat": v, "invoiced": t.get("job_id") in invoiced_jobs})
        rows_out, in_vat, in_base, no_inv = [], 0.0, 0.0, 0.0
        for t in exp:
            if t.get("has_invoice"):
                r = float(t["vat_rate"]) if t.get("vat_rate") is not None else float(s["expense_vat_default"])
                bs, v, _g = split_vat(t["amount"], r, True)
                in_vat += v
                in_base += bs
                rows_out.append({"date": _day(t["date"]), "description": t.get("description", ""), "category": t.get("category", ""), "party": t.get("party", ""), "invoice_no": t.get("invoice_no", ""), "gross": t["amount"], "rate": r, "base": bs, "vat": v})
            else:
                no_inv += t["amount"]
        return {"month": month, "rate": rate, "prices_include_vat": s["prices_include_vat"],
                "sales": {"gross": round(g_inc, 2), "base": base, "vat": vat, "invoiced_gross": round(inc_invoiced, 2), "not_invoiced_gross": round(g_inc - inc_invoiced, 2)},
                "purchases": {"base": round(in_base, 2), "vat": round(in_vat, 2), "no_invoice_total": round(no_inv, 2)},
                "payable": round(vat - in_vat, 2), "rows_in": rows_in, "rows_out": rows_out}

    @api_router.get("/finance/vat")
    async def vat_report(month: Optional[str] = None, _: dict = Depends(require_admin)):
        cur = await vat_for(month)
        now = datetime.now(TR)
        series = []
        for i in range(5, -1, -1):
            y, m = now.year, now.month - i
            while m < 1:
                m += 12
                y -= 1
            v = await vat_for(f"{y:04d}-{m:02d}")
            series.append({"month": v["month"], "calculated": v["sales"]["vat"], "deductible": v["purchases"]["vat"], "payable": v["payable"]})
        cur["series"] = series
        return cur

    # ============================================================ BÜTÇE
    async def budget_state(month):
        s = await settings()
        month, a, b = month_range(month)
        txs = [t for t in await db.cash_transactions.find({}, {"_id": 0}).to_list(200000) if a <= _day(t.get("date")) <= b]
        rev = sum(t["amount"] for t in txs if t["type"] == "gelir")
        by = defaultdict(float)
        for t in txs:
            if t["type"] == "gider":
                by[t.get("category") or "Kategorisiz"] += t["amount"]
        y, m = int(month[:4]), int(month[5:7])
        dim = monthrange(y, m)[1]
        now = datetime.now(TR)
        elapsed = dim if (now.year, now.month) > (y, m) else (now.day if (now.year, now.month) == (y, m) else 0)
        target = float(s["budget"].get("monthly_revenue_target") or 0)
        proj = round(rev / elapsed * dim, 2) if elapsed else 0
        cats = []
        for cat, lim in (s["budget"].get("expense_budgets") or {}).items():
            lim = float(lim or 0)
            used = round(by.get(cat, 0), 2)
            cats.append({"category": cat, "budget": lim, "used": used, "pct": round(used * 100 / lim, 1) if lim else 0, "status": "over" if lim and used > lim else "warn" if lim and used > lim * 0.9 else "ok"})
        return {"month": month, "revenue": round(rev, 2), "target": target, "revenue_pct": round(rev * 100 / target, 1) if target else 0,
                "projected": proj, "on_track": (proj >= target) if target and elapsed else None, "expenses_total": round(sum(by.values()), 2),
                "categories": cats, "unbudgeted": [{"category": k, "used": round(v, 2)} for k, v in by.items() if k not in (s["budget"].get("expense_budgets") or {})]}

    @api_router.get("/finance/budget")
    async def budget(month: Optional[str] = None, _: dict = Depends(require_admin)):
        return await budget_state(month)

    async def budget_hook(_db):
        """Zamanlayıcı: bütçe aşımında sahibe bir kez bildirim."""
        st = await budget_state(None)
        for c in st["categories"]:
            if c["status"] == "over":
                key = f"{st['month']}|{c['category']}"
                if not await db.budget_alerts.find_one({"key": key}):
                    await db.budget_alerts.insert_one({"key": key, "at": _now()})
                    await notify.notify_owner(db, f"Bütçe aşıldı: {c['category']} — {c['used']:.0f} / {c['budget']:.0f} TL ({st['month']})", "budget")
    import governance
    governance.HOOKS.append(budget_hook)

    # ============================================================ BANKA EKSTRESİ
    def _row_key(date, desc, amount):
        return hashlib.sha1(f"{date}|{desc.strip().lower()}|{amount:.2f}".encode()).hexdigest()[:20]

    @api_router.post("/finance/import/preview")
    async def import_preview(file: UploadFile = File(...), date_col: Optional[int] = Form(None), desc_col: Optional[int] = Form(None),
                             amount_col: Optional[int] = Form(None), debit_col: Optional[int] = Form(None), credit_col: Optional[int] = Form(None),
                             _: dict = Depends(require_admin)):
        raw = await file.read()
        if len(raw) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Dosya 5 MB'tan büyük")
        try:
            rows = read_table(raw, file.filename or "x.csv")
        except Exception as e:                          # noqa: BLE001
            raise HTTPException(status_code=400, detail="Dosya okunamadı: " + str(e)[:100])
        mp = detect_mapping(rows)
        for k, v in (("date", date_col), ("desc", desc_col), ("amount", amount_col), ("debit", debit_col), ("credit", credit_col)):
            if v is not None:
                mp[k] = v
        headers = [str(c or "") for c in (rows[mp["header_row"]] if rows else [])]
        existing = await db.cash_transactions.find({}, {"_id": 0, "amount": 1, "date": 1, "import_key": 1, "type": 1, "description": 1, "id": 1}).to_list(200000)
        keys = {t["import_key"] for t in existing if t.get("import_key")}
        out = []
        for i, r in enumerate(rows[mp["header_row"] + 1:]):
            def cell(ix):
                return r[ix] if ix is not None and ix < len(r) else None
            d = parse_date(cell(mp["date"]))
            if not d:
                continue
            desc = str(cell(mp["desc"]) or "").strip()
            if mp["amount"] is not None:
                amt = parse_amount(cell(mp["amount"]))
            else:
                deb, cre = parse_amount(cell(mp["debit"])) or 0, parse_amount(cell(mp["credit"])) or 0
                amt = cre - abs(deb) if (cre or deb) else None
            if amt in (None, 0):
                continue
            key = _row_key(d, desc, amt)
            typ, cat = suggest_category(desc, amt)
            # manuel girilmiş benzer hareket (aynı tutar, ±3 gün)
            match = None
            for t in existing:
                if t.get("type") == typ and abs(float(t["amount"]) - abs(amt)) < 0.01 and t.get("date"):
                    try:
                        if abs((datetime.fromisoformat(_day(t["date"])) - datetime.fromisoformat(d)).days) <= 3:
                            match = t["id"]
                            break
                    except ValueError:
                        pass
            out.append({"idx": i, "date": d, "description": desc[:200], "amount": round(abs(amt), 2), "signed": round(amt, 2), "type": typ, "category": cat,
                        "key": key, "duplicate": key in keys, "matched_tx_id": match, "import": key not in keys and not match})
        return {"mapping": mp, "headers": headers, "rows": out, "categories": None}

    @api_router.post("/finance/import/commit")
    async def import_commit(payload: dict, user: dict = Depends(require_admin)):
        acc = payload.get("account_id")
        if not acc or not await db.accounts.find_one({"id": acc}):
            raise HTTPException(status_code=400, detail="Hesap seçin")
        n = 0
        for r in payload.get("rows", []):
            if not r.get("import") or float(r.get("amount") or 0) <= 0 or r.get("type") not in ("gelir", "gider"):
                continue
            if await db.cash_transactions.find_one({"import_key": r.get("key")}):
                continue
            await db.cash_transactions.insert_one({
                "id": _id(), "type": r["type"], "amount": float(r["amount"]), "description": (r.get("description") or "")[:200], "date": r["date"] + "T12:00:00+03:00",
                "account_id": acc, "category": r.get("category") or "", "payment_method": "havale", "created_by": user["id"], "import_key": r.get("key"), "source": "ekstre"})
            n += 1
        return {"created": n}

    # ============================================================ FATURA KAYITLARI
    async def next_number(prefix):
        year = datetime.now(TR).year
        c = await db.counters.find_one_and_update({"_id": f"invoice-{year}"}, {"$inc": {"n": 1}}, upsert=True, return_document=True)
        return f"{prefix}{year}{int(c['n']):06d}"

    @api_router.post("/jobs/{job_id}/invoice")
    async def invoice_from_job(job_id: str, payload: dict, user: dict = Depends(require_admin)):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            raise HTTPException(status_code=404, detail="Servis kaydı bulunamadı")
        ex = await db.invoices.find_one({"job_id": job_id, "status": {"$ne": "iptal"}}, {"_id": 0})
        if ex:
            return ex
        s = await settings()
        rate = float((payload or {}).get("vat_rate", s["vat_rate"]))
        lines = [{"name": p.get("name", ""), "qty": p.get("qty", 1), "unit_price": p.get("unit_price", 0), "total": p.get("total", 0)} for p in job.get("parts_used", [])]
        if float(job.get("labor_fee", 0) or 0) > 0:
            lines.append({"name": "İşçilik / servis bedeli", "qty": 1, "unit_price": job["labor_fee"], "total": job["labor_fee"]})
        gross = float(job.get("total_amount", 0) or sum(l["total"] for l in lines))
        base, vat, total = split_vat(gross, rate, s["prices_include_vat"])
        inv = {"id": _id(), "number": await next_number(s["invoice"]["prefix"] or "FT"), "type": (payload or {}).get("type") or s["invoice"]["default_type"], "job_id": job_id,
               "job_number": job.get("job_number"), "customer_name": job.get("customer_name", ""), "customer_phone": job.get("customer_phone", ""), "customer_address": job.get("customer_address", ""),
               "tax_no": (payload or {}).get("tax_no", ""), "lines": lines, "vat_rate": rate, "base": base, "vat": vat, "total": total, "status": "taslak", "provider_ref": "", "error": "",
               "issued_at": _now(), "created_by": user["name"]}
        await db.invoices.insert_one(dict(inv))
        await db.service_jobs.update_one({"id": job_id}, {"$set": {"invoice_id": inv["id"], "invoice_number": inv["number"]}})
        return inv

    @api_router.get("/finance/invoices")
    async def invoices(status: Optional[str] = None, _: dict = Depends(require_admin)):
        q = {"status": status} if status else {}
        return await db.invoices.find(q, {"_id": 0}).sort("issued_at", -1).to_list(2000)

    @api_router.put("/finance/invoices/{iid}")
    async def invoice_update(iid: str, payload: dict, _: dict = Depends(require_admin)):
        upd = {k: payload[k] for k in ("status", "provider_ref", "tax_no", "customer_name", "customer_address", "type") if k in payload}
        if upd.get("status") and upd["status"] not in ("taslak", "gonderildi", "kesildi", "iptal", "hata"):
            raise HTTPException(status_code=400, detail="Geçersiz durum")
        r = await db.invoices.update_one({"id": iid}, {"$set": upd})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Fatura bulunamadı")
        return await db.invoices.find_one({"id": iid}, {"_id": 0})

    @api_router.post("/finance/invoices/{iid}/send")
    async def invoice_send(iid: str, _: dict = Depends(require_admin)):
        inv = await db.invoices.find_one({"id": iid}, {"_id": 0})
        if not inv:
            raise HTTPException(status_code=404, detail="Fatura bulunamadı")
        s = await settings()
        url = s["invoice"].get("webhook_url")
        if not url:
            raise HTTPException(status_code=400, detail="Fatura webhook adresi tanımlı değil (Muhasebe → KDV & Fatura → Ayarlar)")
        body = {"invoice": inv, "company": s["company"]}
        try:
            import asyncio
            hd = {"Content-Type": "application/json", **notify._headers(s["invoice"].get("webhook_headers", ""))}
            r = await asyncio.to_thread(lambda: requests.post(url, json=body, headers=hd, timeout=20))
            if r.status_code >= 300:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:150]}")
            ref = ""
            try:
                ref = str(r.json().get("id") or r.json().get("ref") or "")
            except Exception:                           # noqa: BLE001
                pass
            await db.invoices.update_one({"id": iid}, {"$set": {"status": "gonderildi", "provider_ref": ref or inv.get("provider_ref", ""), "error": "", "sent_at": _now()}})
        except Exception as e:                          # noqa: BLE001
            await db.invoices.update_one({"id": iid}, {"$set": {"status": "hata", "error": str(e)[:200]}})
            raise HTTPException(status_code=502, detail="Gönderilemedi: " + str(e)[:150])
        return await db.invoices.find_one({"id": iid}, {"_id": 0})

    # ============================================================ MUHASEBECİ PAKETİ
    @api_router.get("/finance/accountant-pack")
    async def accountant_pack(month: Optional[str] = None, _: dict = Depends(require_admin)):
        from openpyxl import Workbook
        from openpyxl.styles import Font
        v = await vat_for(month)
        month, a, b = month_range(month)
        txs = [t for t in await db.cash_transactions.find({}, {"_id": 0}).to_list(200000) if a <= _day(t.get("date")) <= b]
        accs = {x["id"]: x["name"] for x in await db.accounts.find({}, {"_id": 0}).to_list(100)}
        invs = [i for i in await db.invoices.find({}, {"_id": 0}).to_list(5000) if a <= _day(i.get("issued_at")) <= b]
        wb = Workbook()

        def sheet(title, head, rows):
            ws = wb.create_sheet(title)
            ws.append(head)
            for c in ws[1]:
                c.font = Font(bold=True)
            for r in rows:
                ws.append(r)
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(40, max(10, max(len(str(c.value or "")) for c in col) + 2))
        wb.remove(wb.active)
        sheet("KDV Özeti", ["Kalem", "Tutar"], [["Satış (KDV dahil)", v["sales"]["gross"]], ["Satış matrahı", v["sales"]["base"]], ["Hesaplanan KDV", v["sales"]["vat"]], ["Faturalı gider matrahı", v["purchases"]["base"]],
                                                ["İndirilecek KDV", v["purchases"]["vat"]], ["Ödenecek KDV", v["payable"]], ["Faturasız gider toplamı", v["purchases"]["no_invoice_total"]]])
        sheet("Gelirler", ["Tarih", "Açıklama", "Kategori", "Brüt", "Matrah", "KDV", "Faturalı"], [[r["date"], r["description"], r["category"], r["gross"], r["base"], r["vat"], "Evet" if r["invoiced"] else "Hayır"] for r in v["rows_in"]])
        sheet("Giderler", ["Tarih", "Açıklama", "Kategori", "Firma", "Fatura No", "Brüt", "KDV %", "Matrah", "KDV"], [[r["date"], r["description"], r["category"], r["party"], r["invoice_no"], r["gross"], r["rate"], r["base"], r["vat"]] for r in v["rows_out"]])
        sheet("Tüm Hareketler", ["Tarih", "Tür", "Açıklama", "Kategori", "Hesap", "Tutar", "Yöntem", "Fatura/Makbuz"], [[_day(t.get("date")), t["type"], t.get("description", ""), t.get("category", ""), accs.get(t.get("account_id"), ""), t["amount"], t.get("payment_method", ""), t.get("invoice_no") or t.get("receipt_no", "")] for t in sorted(txs, key=lambda x: x.get("date", ""))])
        sheet("Faturalar", ["No", "Tür", "Müşteri", "Vergi No", "Matrah", "KDV", "Toplam", "Durum", "Tarih"], [[i["number"], i["type"], i["customer_name"], i.get("tax_no", ""), i["base"], i["vat"], i["total"], i["status"], _day(i["issued_at"])] for i in invs])
        buf = io.BytesIO()
        wb.save(buf)
        return Response(content=buf.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f'attachment; filename="muhasebe-paketi-{month}.xlsx"'})


async def ensure_indexes(db):
    await db.invoices.create_index("id", unique=True)
    await db.invoices.create_index("job_id")
    await db.cash_transactions.create_index("import_key", sparse=True)
