# -*- coding: utf-8 -*-
"""Firmaya özel servis ayarları: kayıt adımları, fotoğraf/imza kuralları, cihaz kataloğu, servis fişi (PDF).

Ayarlar firmanın KENDİ veritabanında (db.app_settings {_id:"servis"}) durur; TenantDB sayesinde her firma yalnız kendi
ayarını görür. Kurallar sunucuda uygulanır (update_job içinden enforce çağrılır), ekranlar sadece bu ayarı yansıtır.
"""
import io
import json
import os
import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from fastapi.responses import Response

DONE = ("tamamlandi", "faturalandi")
STEPS = ["yeni", "atandi", "yolda", "basladi", "tamamlandi", "faturalandi", "iptal"]
STEP_LABELS = {"yeni": "Yeni", "atandi": "Atandı", "yolda": "Yolda", "basladi": "Başladı", "tamamlandi": "Tamamlandı",
               "faturalandi": "Faturalandı", "iptal": "İptal / müşteri vazgeçti"}
FOTO_MODES = ("zorunlu", "istege_bagli", "kapali")

DEFAULTS = {
    "steps": {s: {"enabled": True, "label": STEP_LABELS[s]} for s in STEPS},
    "foto_once": "istege_bagli", "foto_sonra": "istege_bagli", "min_foto": 1,
    "imza": {"enabled": True, "required": False, "text": "İşlemi ve ücreti kontrol ettim, onaylıyorum."},
    "usta_imza": {"enabled": False},
    "parca_iscilik": True,
    "katalog": {"zorunlu": False, "elle_yaz": True},
    "pdf": {"paper": "A4", "title": "SERVİS FORMU", "color": "#1155cc", "footer": "",
            "blocks": {"logo": True, "firma": True, "no_tarih": True, "musteri": True, "cihaz": True, "ariza": True,
                       "islem": True, "parca": True, "toplam": True, "garanti": True, "musteri_imza": True,
                       "usta_imza": True, "qr": False}},
}


def _merge(base, over):
    out = json.loads(json.dumps(base))
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def validate(s: dict) -> dict:
    for k in ("foto_once", "foto_sonra"):
        if s[k] not in FOTO_MODES:
            raise HTTPException(status_code=400, detail=f"{k}: geçersiz değer")
    try:
        s["min_foto"] = max(0, min(10, int(s["min_foto"])))
    except Exception:                                      # noqa: BLE001
        raise HTTPException(status_code=400, detail="min_foto sayı olmalı")
    for st in ("atandi", "tamamlandi"):                    # bu adımlar kapatılamaz: akış bozulur
        if not s["steps"].get(st, {}).get("enabled", True):
            raise HTTPException(status_code=400, detail=f"“{STEP_LABELS[st]}” adımı kapatılamaz")
    for st in s["steps"]:
        if st not in STEP_LABELS:
            raise HTTPException(status_code=400, detail="bilinmeyen adım: " + st)
        lb = str(s["steps"][st].get("label") or "").strip()[:40]
        s["steps"][st]["label"] = lb or STEP_LABELS[st]
    s["pdf"]["title"] = str(s["pdf"].get("title") or "SERVİS FORMU")[:60]
    s["pdf"]["footer"] = str(s["pdf"].get("footer") or "")[:400]
    col = str(s["pdf"].get("color") or "#1155cc")
    s["pdf"]["color"] = col if len(col) == 7 and col.startswith("#") else "#1155cc"
    return s


async def get(db) -> dict:
    d = await db.app_settings.find_one({"_id": "servis"}, {"_id": 0}) or {}
    return _merge(DEFAULTS, d)


async def save(db, incoming: dict) -> dict:
    new = validate(_merge(await get(db), incoming or {}))
    await db.app_settings.update_one({"_id": "servis"}, {"$set": new}, upsert=True)
    return new


async def enforce(db, job: dict, update: dict, user: dict):
    """update_job içinden çağrılır; ayara aykırı değişikliği 400 ile reddeder, kapalı alanları temizler."""
    s = await get(db)
    if "signature_url" in update and not s["imza"]["enabled"]:
        update.pop("signature_url")                         # imza kapalıysa hiçbir yerde saklanmaz
    if "tech_signature_url" in update and not s["usta_imza"]["enabled"]:
        update.pop("tech_signature_url")
    new = update.get("status")
    if not new or new == job.get("status"):
        return
    if not s["steps"].get(new, {}).get("enabled", True):
        raise HTTPException(status_code=400, detail=f"“{s['steps'][new]['label']}” adımı bu firmada kapalı")
    if user.get("role") == "admin" and not user.get("fu"):
        return                                              # ofis kuralları atlayabilir (düzeltme için)
    mf = s["min_foto"]
    before = update.get("photos_before", job.get("photos_before") or [])
    after = update.get("photos_after", job.get("photos_after") or [])
    if new == "basladi" and s["foto_once"] == "zorunlu" and len(before) < mf:
        raise HTTPException(status_code=400, detail="İşlem öncesi fotoğraf zorunlu")
    if new in DONE:
        if s["foto_once"] == "zorunlu" and len(before) < mf:
            raise HTTPException(status_code=400, detail="İşlem öncesi fotoğraf zorunlu")
        if s["foto_sonra"] == "zorunlu" and len(after) < mf:
            raise HTTPException(status_code=400, detail="İşlem sonrası fotoğraf zorunlu")
        if s["imza"]["enabled"] and s["imza"]["required"] and not (update.get("signature_url") or job.get("signature_url")):
            raise HTTPException(status_code=400, detail="Müşteri imzası zorunlu")
        if s["usta_imza"]["enabled"] and not (update.get("tech_signature_url") or job.get("tech_signature_url")):
            raise HTTPException(status_code=400, detail="Usta imzası zorunlu")
        if not (update.get("work_done") or job.get("work_done")):
            raise HTTPException(status_code=400, detail="Yapılan işi yazın")


# ------------------------------------------------------------------ servis fişi (PDF)
_FONT = None


def _font():
    global _FONT
    if _FONT:
        return _FONT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    for reg, bold in (("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
                      (os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf"), os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans-Bold.ttf"))):
        if os.path.exists(reg):
            pdfmetrics.registerFont(TTFont("OKSans", reg))
            pdfmetrics.registerFont(TTFont("OKSans-B", bold))
            _FONT = ("OKSans", "OKSans-B")
            return _FONT
    _FONT = ("Helvetica", "Helvetica-Bold")
    return _FONT


def render_pdf(job: dict, cfg: dict, firm: dict) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    f, fb = _font()
    p = cfg["pdf"]
    b = p["blocks"]
    thermal = p["paper"] == "80mm"
    W = 80 * mm if thermal else A4[0]
    H = 400 * mm if thermal else A4[1]
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H))
    m = 6 * mm if thermal else 18 * mm
    y = H - m
    col = p["color"]
    fs = 8 if thermal else 10

    def line(txt, bold=False, size=None, dy=None, color="#273142"):
        nonlocal y
        c.setFillColor(color)
        c.setFont(fb if bold else f, size or fs)
        c.drawString(m, y, str(txt)[:110])
        y -= dy or (size or fs) * 1.5

    def hr():
        nonlocal y
        c.setStrokeColor(col)
        c.setLineWidth(1.2)
        c.line(m, y + 2, W - m, y + 2)
        y -= 8

    if b["firma"]:
        line(firm.get("name", ""), True, fs + 5, color=col)
        sub = " · ".join(x for x in (firm.get("address", ""), firm.get("phone", "")) if x)
        if sub:
            line(sub, size=fs - 1, color="#6b7280")
        hr()
    line(p["title"], True, fs + 3)
    if b["no_tarih"]:
        line(f'No: {job.get("job_number", "")}   Tarih: {(job.get("completed_at") or job.get("created_at") or "")[:10]}', size=fs - 1, color="#6b7280")
    y -= 4
    if b["musteri"]:
        line("Müşteri", True, fs - 1, color=col)
        line(f'{job.get("customer_name", "")}  {job.get("customer_phone", "")}')
        line(job.get("customer_address", ""))
    if b["cihaz"]:
        line("Cihaz", True, fs - 1, color=col)
        line(f'{job.get("device_brand_name", "")} {job.get("device_model", "")} {job.get("device_serial", "")}'.strip())
    if b["ariza"]:
        line("Arıza", True, fs - 1, color=col)
        line(job.get("fault_description", ""))
    if b["islem"]:
        line("Yapılan işlem", True, fs - 1, color=col)
        line(job.get("work_done", ""))
    if b["parca"] and cfg["parca_iscilik"]:
        line("Parça ve işçilik", True, fs - 1, color=col)
        for pt in job.get("parts_used") or []:
            line(f'{pt.get("name", "")} x{pt.get("qty", 1):g}   {pt.get("total", 0):.2f} TL')
        if job.get("labor_fee"):
            line(f'İşçilik   {job.get("labor_fee", 0):.2f} TL')
    if b["toplam"]:
        line(f'TOPLAM: {job.get("total_amount", 0):.2f} TL', True, fs + 1)
    if b["garanti"] and firm.get("pdf_note"):
        line(firm["pdf_note"], size=fs - 1, color="#6b7280")
    y -= 8
    if b["musteri_imza"] and cfg["imza"]["enabled"]:
        line("Müşteri imzası: " + ("[imzalı]" if job.get("signature_url") else "........................"), dy=fs * 2.4)
    if b["usta_imza"] and cfg["usta_imza"]["enabled"]:
        line("Usta imzası: " + ("[imzalı]" if job.get("tech_signature_url") else "........................"), dy=fs * 2.4)
    if b["qr"] and job.get("track_token"):
        line("Takip: /takip/" + job["track_token"], size=fs - 1, color="#6b7280")
    if p.get("footer"):
        line(p["footer"], size=fs - 2, color="#6b7280")
    c.showPage()
    c.save()
    return buf.getvalue()


# ------------------------------------------------------------------ uçlar
def setup(app, api_router, db, get_current_user, tenant):
    def _owner(user):
        if user.get("role") == "admin" or user.get("firm_owner"):
            return
        raise HTTPException(status_code=403, detail="Yalnızca firma yöneticisi")

    @api_router.get("/service-settings")
    async def ss_get(user: dict = Depends(get_current_user)):
        return await get(db)                                 # usta uygulaması da okur (yalnız okuma)

    @api_router.put("/service-settings")
    async def ss_put(payload: dict, user: dict = Depends(get_current_user)):
        _owner(user)
        return await save(db, payload)

    @api_router.get("/catalog")
    async def cat_list(user: dict = Depends(get_current_user)):
        return await db.device_catalog.find({}, {"_id": 0}).sort([("brand", 1), ("model", 1)]).to_list(5000)

    @api_router.post("/catalog")
    async def cat_add(payload: dict, user: dict = Depends(get_current_user)):
        _owner(user)
        brand, model = str(payload.get("brand") or "").strip(), str(payload.get("model") or "").strip()
        if len(brand) < 2 or len(model) < 1:
            raise HTTPException(status_code=400, detail="Marka ve model yazın")
        if await db.device_catalog.find_one({"brand": brand, "model": model}):
            raise HTTPException(status_code=400, detail="Bu model zaten kayıtlı")
        d = {"id": uuid.uuid4().hex[:12], "type": str(payload.get("type") or "")[:40], "brand": brand, "model": model,
             "kind": str(payload.get("kind") or "")[:40], "power": str(payload.get("power") or "")[:20],
             "error_codes": str(payload.get("error_codes") or "")[:200], "created_at": datetime.now(timezone.utc).isoformat()}
        await db.device_catalog.insert_one(dict(d))
        return d

    @api_router.delete("/catalog/{cid}")
    async def cat_del(cid: str, user: dict = Depends(get_current_user)):
        _owner(user)
        await db.device_catalog.delete_one({"id": cid})
        return {"ok": True}

    @api_router.get("/jobs/{job_id}/fis.pdf")
    async def job_pdf(job_id: str, user: dict = Depends(get_current_user)):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            raise HTTPException(status_code=404, detail="Servis kaydı bulunamadı")
        if user.get("role") == "technician" and not user.get("firm_owner") and job.get("assigned_technician_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Bu kayda erişim yetkiniz yok")
        cfg = await get(db)
        fm = await db.app_settings.find_one({"_id": "firm"}, {"_id": 0}) or {}
        gl = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        firm = {"name": fm.get("name") or gl.get("company_name", ""), "address": gl.get("company_address", ""),
                "phone": gl.get("company_phone", ""), "pdf_note": fm.get("pdf_note", "")}
        return Response(render_pdf(job, cfg, firm), media_type="application/pdf",
                        headers={"Content-Disposition": f'inline; filename="{job.get("job_number", "fis")}.pdf"'})
