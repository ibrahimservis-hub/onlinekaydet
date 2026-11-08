# -*- coding: utf-8 -*-
"""Firmalar: ServisPlus panelini kendi verisiyle kullanan müşteri firmalar (yalnız yönetici ekranı).

Her firma ayrı bir MongoDB veritabanında çalışır (tenant.py). Burada firma kaydı (ana veritabanı `firms`),
firmanın veritabanının hazırlanması, ek özellik anahtarları, askıya alma ve firmanın işlerini (adımlarıyla) izleme var.
"""
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import base64

from fastapi import Depends, HTTPException, Request, Response
from pydantic import BaseModel

import tenant

MODULES = {"servis": "Servis kayıtları", "personel": "Usta / personel", "muhasebe": "Muhasebe ve kasa", "rapor": "Raporlar",
           "sms": "SMS ve mesaj şablonları", "magaza": "Yedek parça mağazası", "site": "Web sitesi", "pazarlama": "Pazarlama",
           "bakim": "Bakım hatırlatma ve garanti", "teklif": "Teklif ve onay", "bayi": "Bayi (B2B)", "qr": "QR cihaz etiketi",
           "atama": "Otomatik usta atama", "takip": "Canlı usta takibi"}
# Henüz yazılmamış Kurumsal modüller: satış sayfasında "Yakında"; atanamaz, yalnızca bilgi olarak listelenir.
SOON = {"odeme": "Ödeme linki (online tahsilat)", "efatura": "E-arşiv fatura bağlantısı", "portal": "Müşteri portalı",
        "offline": "Çevrimdışı usta uygulaması", "arayan": "Arayan numara tanıma"}
# modül -> kapatıldığında engellenen API ön ekleri (servis çekirdektir, kapatılamaz)
MODULE_PREFIX = {"muhasebe": ("finance", "cash", "accounting", "receivables", "profit", "export-xlsx"),
                 "rapor": ("rapor", "reports", "analytics", "performance"),
                 "magaza": ("shop", "parts"), "site": ("site", "site-reviews-settings", "media", "studio", "visitors"),
                 "pazarlama": ("mkt", "growth"), "sms": ("msg-templates", "governance/notify"),
                 "bakim": ("maintenance", "warranty-claims"), "teklif": ("quotes",), "bayi": ("dealers", "partners"),
                 "qr": ("qr",), "atama": ("autoassign",), "takip": ("admin/tech-locations",)}
DEFAULT_PACKAGES = {
    "baslangic": {"name": "Başlangıç", "price": 0, "modules": ["servis", "personel"]},
    "profesyonel": {"name": "Profesyonel", "price": 0, "modules": ["servis", "personel", "muhasebe", "rapor", "sms"]},
    "tam": {"name": "Tam Paket", "price": 0, "modules": list(["servis", "personel", "muhasebe", "rapor", "sms", "magaza", "site", "pazarlama"])},
    "kurumsal": {"name": "Kurumsal", "price": 0, "modules": ["servis", "personel", "muhasebe", "rapor", "sms", "magaza", "site", "pazarlama",
                                                          "bakim", "teklif", "bayi", "qr", "atama", "takip"]},
}
DEFAULT_FEATURES = {"customer_add": True}
FEATURE_LABELS = {"customer_add": "Müşteriyi kendi ekleme"}
DEFAULT_PDF_NOTE = ("KİŞİSEL VERİLERİN KORUNMASI: Bu formda yer alan kişisel veriler, {firma_adi} ({adres}) tarafından servis "
                    "hizmetinin yürütülmesi, kayıt ve faturalandırma amaçlarıyla 6698 sayılı KVKK kapsamında işlenir. Haklarınız ve "
                    "aydınlatma metni için {telefon} numarasından {firma_adi} ile iletişime geçebilirsiniz.")


def _now():
    return datetime.now(timezone.utc).isoformat()


def expired(f):
    e = (f or {}).get("expires_at") or ""
    return bool(e) and e < _now()


MAX_SUB = 3
MAINT_LOOP = None
GATE = None            # server.py ara katmanı: await GATE(db_adı, yol) -> engel mesajı | None
ACCESS = None          # server.py ara katmanı çağırır: await ACCESS(db_adı, alt_kullanıcı_e-postası)
_ACC = {}


class FirmIn(BaseModel):
    name: str
    email: str
    password: str
    contact_name: Optional[str] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""
    tax_no: Optional[str] = ""
    tax_office: Optional[str] = ""
    features: Optional[dict] = None
    logo: Optional[str] = None
    usage_days: Optional[int] = None
    package: Optional[str] = None
    modules: Optional[list] = None
    sector: Optional[str] = None


class FirmUp(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_no: Optional[str] = None
    tax_office: Optional[str] = None
    features: Optional[dict] = None
    status: Optional[str] = None            # aktif | askida
    logo: Optional[str] = None              # data:image/...;base64 ('' = kaldır)
    usage_days: Optional[int] = None        # bugünden itibaren gün; 0 = sınırsız
    package: Optional[str] = None
    modules: Optional[list] = None


class PdfNoteIn(BaseModel):
    text: str = ""


class SubIn(BaseModel):
    name: Optional[str] = ""
    email: str
    password: str


class FirmSelf(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_no: Optional[str] = None
    tax_office: Optional[str] = None
    logo: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


class TemplateIn(BaseModel):
    pdf_note: str


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]
    verify_password = deps["verify_password"]
    hash_password = deps["hash_password"]

    def need_main():
        if tenant.current():
            raise HTTPException(status_code=403, detail="Bu işlem yalnız ana yönetim içindir")

    async def audit(me, action, detail):
        try:
            import governance
            await governance.audit(db.main(), me, action, detail)
        except Exception:                                  # noqa: BLE001
            pass

    async def derive_from_main():
        """ServisPlus'ın kendi PDF notundan şablon üretir: ServisPlus adı/telefonu/adresi yer tutuculara çevrilir."""
        g = await db.main().app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        note = (g.get("default_pdf_note") or "").strip()
        if not note:
            return DEFAULT_PDF_NOTE
        for key, ph in (("company_address", "{adres}"), ("company_phone", "{telefon}"), ("company_name", "{firma_adi}")):
            v = (g.get(key) or "").strip()
            if len(v) >= 3:
                note = note.replace(v, ph)
        note = re.sub(r"(?i)\b(?:https?://)?(?:www\.|bayi\.)?servisplus\.net\.tr\S*", "", note)
        note = re.sub(r"(?<![\w.])servis\s*plus(?:\s+usta)?(?![\w.])", "{firma_adi}", note, flags=re.I)
        note = re.sub(r"0?\s?544[\s-]?444[\s-]?4[\s-]?004|0?850[\s\d]{7,10}", "{telefon}", note)
        return re.sub(r"[ \t]{2,}", " ", note).strip()

    async def template():
        d = await db.main().app_settings.find_one({"_id": "firm_defaults"}, {"_id": 0}) or {}
        return d.get("pdf_note") or await derive_from_main()

    def render(tpl, f):
        return (tpl.replace("{firma_adi}", f.get("name", "")).replace("{adres}", f.get("address", "") or "-")
                .replace("{telefon}", f.get("phone", "") or "-"))

    async def packages_get():
        d = await db.main().app_settings.find_one({"_id": "packages"}, {"_id": 0}) or {}
        items = d.get("items")
        if not items:
            return DEFAULT_PACKAGES
        return {**items, **{k: v for k, v in DEFAULT_PACKAGES.items() if k == "kurumsal" and k not in items}}

    def clean_modules(v):
        out = ["servis"] + [m for m in (v or []) if m in MODULES and m != "servis"]
        return list(dict.fromkeys(out))

    async def resolve_modules(package, modules):
        if modules is not None:
            return clean_modules(modules)
        pk = (await packages_get()).get(package or "")
        if package and not pk:
            raise HTTPException(status_code=400, detail="Bilinmeyen paket")
        return clean_modules((pk or {}).get("modules") or ["servis"])

    @api_router.get("/admin/packages")
    async def packages_list(me: dict = Depends(require_admin)):
        need_main()
        return {"packages": await packages_get(), "modules": MODULES, "soon": SOON}

    @api_router.put("/admin/packages")
    async def packages_save(body: dict, me: dict = Depends(require_admin)):
        need_main()
        items = {}
        for k, v in (body.get("packages") or {}).items():
            if not re.match(r"^[a-z0-9_]{2,30}$", k):
                raise HTTPException(status_code=400, detail="Paket anahtarı geçersiz")
            items[k] = {"name": str(v.get("name") or k)[:40], "price": float(v.get("price") or 0), "modules": clean_modules(v.get("modules"))}
        if not items:
            raise HTTPException(status_code=400, detail="En az bir paket olmalı")
        await db.main().app_settings.update_one({"_id": "packages"}, {"$set": {"items": items}}, upsert=True)
        return {"packages": items}

    _MOD = {}

    async def gate(dbname, path):
        """Firmanın paketinde olmayan modülün API'sini kapatır. Modül listesi 30 sn önbellekte."""
        import time as _t
        e = _MOD.get(dbname)
        if not e or _t.monotonic() - e[0] > 30:
            f = await db.main().firms.find_one({"db": dbname}, {"_id": 0, "modules": 1})
            e = (_t.monotonic(), (f or {}).get("modules"))
            _MOD[dbname] = e
        mods = e[1]
        if mods is None:
            return None                                   # modül tanımı olmayan eski firma: kısıt yok
        seg = path[5:] if path.startswith("/api/") else ""
        for m, pre in MODULE_PREFIX.items():
            if m not in mods and any(seg == p or seg.startswith(p + "/") for p in pre):
                return f"“{MODULES[m]}” bu paketinizde yok. Paket yükseltmek için bizimle iletişime geçin."
        return None

    global GATE
    GATE = gate

    @api_router.get("/firm/package")
    async def firm_package(request: Request, user: dict = Depends(get_current_user)):
        f = await my_firm(request)
        mods = f.get("modules") or list(MODULES)
        return {"package": f.get("package", ""), "modules": mods, "labels": {m: MODULES[m] for m in MODULES}, "locked": [m for m in MODULES if m not in mods], "soon": SOON}

    async def push_settings(f):
        fdb = db.firm(f["db"])
        await fdb.app_settings.update_one({"_id": "global"}, {"$set": {
            "company_name": f.get("name", ""), "company_phone": f.get("phone", ""), "company_address": f.get("address", ""),
            "company_tax_no": f.get("tax_no", ""), "company_tax_office": f.get("tax_office", ""),
            "default_pdf_note": render(f.get("pdf_note") or await template(), f),
            "is_firm": True, "has_logo": bool(f.get("logo")),
            # firma kendi verisinin sahibi: gece gizleme ve 7 gün sınırı uygulanmaz
            "tech_visibility": {"enabled": False, "hide_from": "22:00", "show_from": "07:00", "done_days": 36500}}}, upsert=True)
        await fdb.app_settings.update_one({"_id": "firm_logo"}, {"$set": {"data": f.get("logo", "")}}, upsert=True)
        await fdb.app_settings.update_one({"_id": "firm"}, {"$set": {
            "firm_id": f["id"], "name": f.get("name", ""), "features": f.get("features") or {}}}, upsert=True)

    def feats(v):
        out = dict(DEFAULT_FEATURES)
        for k in DEFAULT_FEATURES:
            if isinstance(v, dict) and k in v:
                out[k] = bool(v[k])
        return out

    def clean_logo(v):
        v = (v or "").strip()
        if not v:
            return ""
        if not re.match(r"^data:image/(png|jpeg|jpg|webp);base64,[A-Za-z0-9+/=]+$", v) or len(v) > 1_200_000:
            raise HTTPException(status_code=400, detail="Logo PNG/JPG/WEBP olmalı ve 800 KB'ı geçmemeli")
        return v

    async def get_firm(fid):
        f = await db.main().firms.find_one({"id": fid}, {"_id": 0})
        if not f:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")
        return f

    async def stats(f):
        fdb = db.firm(f["db"])
        by = {}
        async for r in fdb.service_jobs.aggregate([{"$group": {"_id": "$status", "n": {"$sum": 1}}}]):
            by[r["_id"] or "yeni"] = r["n"]
        last = await fdb.service_jobs.find({}, {"_id": 0, "updated_at": 1}).sort("updated_at", -1).limit(1).to_list(1)
        open_n = sum(n for s, n in by.items() if s in ("yeni", "atandi", "yolda", "basladi"))
        done_n = sum(n for s, n in by.items() if s in ("tamamlandi", "faturalandi"))
        rp = await build_report(fdb, 2)
        return {"by_status": by, "open": open_n, "done": done_n, "total": sum(by.values()),
                "customers": await fdb.customers.count_documents({}),
                "last_activity": last[0]["updated_at"] if last else "",
                "revenue_total": rp["total"]["revenue"], "revenue_month": rp["current"]["revenue"], "jobs_month": rp["current"]["jobs"],
                "avg_ticket": rp["avg_ticket"], "cancelled": by.get("iptal", 0)}

    @api_router.get("/admin/firms")
    async def firms_list(me: dict = Depends(require_admin)):
        need_main()
        out = []
        for f in await db.main().firms.find({"status": {"$ne": "silindi"}}, {"_id": 0}).sort("created_at", -1).to_list(500):
            f["stats"] = await stats(f)
            f["has_logo"] = bool(f.pop("logo", ""))
            f["expired"] = expired(f)
            f["users"] = await db.main().firm_users.find({"firm_id": f["id"]}, {"_id": 0, "password_hash": 0}).sort("created_at", 1).to_list(10)
            f.pop("db", None)
            out.append(f)
        return {"firms": out, "feature_labels": FEATURE_LABELS}

    @api_router.post("/admin/firms")
    async def firms_create(p: FirmIn, me: dict = Depends(require_admin)):
        need_main()
        name = (p.name or "").strip()
        email = (p.email or "").lower().strip()
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Firma adı yazın")
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise HTTPException(status_code=400, detail="Geçerli bir kullanıcı adı (e-posta) yazın")
        if len(p.password or "") < 8:
            raise HTTPException(status_code=400, detail="Şifre en az 8 karakter olmalı")
        if await db.main().firms.find_one({"login_email": email}) or await db.main().users.find_one({"email": email}):
            raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kayıtlı")
        fid = uuid.uuid4().hex[:12]
        f = {"id": fid, "db": db.firm_db_name(fid), "name": name, "login_email": email, "contact_name": (p.contact_name or "").strip(),
             "phone": (p.phone or "").strip(), "address": (p.address or "").strip(), "tax_no": (p.tax_no or "").strip(),
             "tax_office": (p.tax_office or "").strip(), "features": feats(p.features), "status": "aktif", "created_at": _now(),
             "logo": clean_logo(p.logo), "expires_at": "",
             "package": (p.package or ""), "modules": await resolve_modules(p.package, p.modules), "sector": (p.sector or "")}
        import sektor
        if p.sector and p.sector not in sektor.SECTORS:
            raise HTTPException(status_code=400, detail="Bilinmeyen sektör")
        if p.usage_days and p.usage_days > 0:
            f["expires_at"] = (datetime.now(timezone.utc) + timedelta(days=min(p.usage_days, 36500))).isoformat()
        fdb = db.firm(f["db"])
        await fdb.users.insert_one({"id": str(uuid.uuid4()), "email": email, "password_hash": hash_password(p.password),
                                    "name": f["contact_name"] or name, "phone": f["phone"], "role": "admin",
                                    "commission_percent": 0.0, "is_active": True, "firm_owner": True, "created_at": _now()})
        try:                                              # marka listesi (Yeni servis kaydı için hazır gelsin)
            br = await db.main().brands.find({}, {"_id": 0}).to_list(500)
            if br:
                await fdb.brands.insert_many(br)
        except Exception:                                 # noqa: BLE001
            pass
        await push_settings(f)
        await db.main().firms.insert_one(dict(f))
        await audit(me, "FİRMA EKLEDİ", name)
        import sahip
        setup_res = await sahip.on_create(db, f, p.password)
        f.pop("db", None)
        f.pop("_id", None)
        f["setup"] = setup_res
        f["has_logo"] = bool(f.pop("logo", ""))
        return f

    @api_router.put("/admin/firms/{fid}")
    async def firms_update(fid: str, p: FirmUp, me: dict = Depends(require_admin)):
        need_main()
        f = await get_firm(fid)
        fdb = db.firm(f["db"])
        upd = {}
        for k in ("name", "contact_name", "phone", "address", "tax_no", "tax_office"):
            v = getattr(p, k)
            if v is not None:
                upd[k] = v.strip()
        if p.features is not None:
            upd["features"] = feats({**(f.get("features") or {}), **p.features})
        if p.logo is not None:
            upd["logo"] = clean_logo(p.logo)
        if p.package is not None or p.modules is not None:
            upd["package"] = p.package if p.package is not None else f.get("package", "")
            upd["modules"] = await resolve_modules(upd["package"], p.modules)
        if p.usage_days is not None:
            upd["expires_at"] = (datetime.now(timezone.utc) + timedelta(days=min(p.usage_days, 36500))).isoformat() if p.usage_days > 0 else ""
        uset = {}
        if p.email is not None:
            em = p.email.lower().strip()
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", em):
                raise HTTPException(status_code=400, detail="Geçerli bir kullanıcı adı (e-posta) yazın")
            if em != f["login_email"]:
                if await db.main().firms.find_one({"login_email": em}) or await db.main().users.find_one({"email": em}):
                    raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kayıtlı")
                upd["login_email"] = em
                uset["email"] = em
        if p.password:
            if len(p.password) < 8:
                raise HTTPException(status_code=400, detail="Şifre en az 8 karakter olmalı")
            uset["password_hash"] = hash_password(p.password)
            uset["tokens_valid_after"] = int(time.time())
        if p.status in ("aktif", "askida"):
            upd["status"] = p.status
            uset["is_active"] = p.status == "aktif"
            if p.status == "askida":
                uset["tokens_valid_after"] = int(time.time())
        if upd:
            await db.main().firms.update_one({"id": fid}, {"$set": upd})
        if uset:
            await fdb.users.update_many({"firm_owner": True}, {"$set": uset})
        f = await get_firm(fid)
        _ACC.clear()
        _MOD.clear()
        await push_settings(f)
        await audit(me, "FİRMA GÜNCELLEDİ", f["name"])
        f["stats"] = await stats(f)
        f["has_logo"] = bool(f.pop("logo", ""))
        f.pop("db", None)
        return f

    @api_router.get("/admin/firms/{fid}/jobs")
    async def firm_jobs(fid: str, status: Optional[str] = None, limit: int = 100, me: dict = Depends(require_admin)):
        need_main()
        f = await get_firm(fid)
        q = {"status": status} if status else {}
        rows = await db.firm(f["db"]).service_jobs.find(q, {"_id": 0, "id": 1, "job_number": 1, "customer_name": 1, "customer_phone": 1,
            "device_type": 1, "device_brand_name": 1, "fault_description": 1, "status": 1, "total_amount": 1, "created_at": 1,
            "updated_at": 1, "completed_at": 1}).sort("created_at", -1).limit(max(1, min(limit, 500))).to_list(500)
        return {"firm": {"id": f["id"], "name": f["name"]}, "jobs": rows}

    @api_router.delete("/admin/firms/{fid}/jobs/{jid}")
    async def firm_job_delete(fid: str, jid: str, me: dict = Depends(require_admin)):
        need_main()
        f = await get_firm(fid)
        j = await db.firm(f["db"]).service_jobs.find_one({"id": jid}, {"_id": 0, "job_number": 1, "customer_name": 1})
        if not j:
            raise HTTPException(status_code=404, detail="İş bulunamadı")
        await db.firm(f["db"]).service_jobs.delete_one({"id": jid})
        await audit(me, "FİRMA İŞİ SİLDİ", "%s: %s %s" % (f["name"], j.get("job_number", ""), j.get("customer_name", "")))
        return {"ok": True}

    @api_router.get("/admin/firms/{fid}/jobs/{jid}")
    async def firm_job(fid: str, jid: str, me: dict = Depends(require_admin)):
        need_main()
        f = await get_firm(fid)
        j = await db.firm(f["db"]).service_jobs.find_one({"id": jid}, {"_id": 0, "workshop.photos": 0})
        if not j:
            raise HTTPException(status_code=404, detail="İş bulunamadı")
        steps = [{"k": "yeni", "label": "Talep", "at": j.get("created_at", "")},
                 {"k": "basladi", "label": "Başladı", "at": j.get("started_at", "")},
                 {"k": "tamamlandi", "label": "Tamamlandı", "at": j.get("completed_at", "")}]
        j["steps"] = steps
        j["has_customer_signature"] = bool(j.get("signature_url"))
        j["has_tech_signature"] = bool(j.get("tech_signature_url"))
        return j

    @api_router.get("/admin/firm-template")
    async def tpl_get(me: dict = Depends(require_admin)):
        need_main()
        return {"pdf_note": await template(), "placeholders": ["{firma_adi}", "{adres}", "{telefon}"]}

    @api_router.post("/admin/firm-template/from-main")
    async def tpl_from_main(me: dict = Depends(require_admin)):
        """ServisPlus PDF notunu firma şablonuna çevirip kaydeder ve tüm firmalara uygular."""
        need_main()
        txt = await derive_from_main()
        await db.main().app_settings.update_one({"_id": "firm_defaults"}, {"$set": {"pdf_note": txt}}, upsert=True)
        n = 0
        for f in await db.main().firms.find({"status": {"$ne": "silindi"}}, {"_id": 0}).to_list(500):
            await push_settings(f)
            n += 1
        await audit(me, "FİRMA PDF METNİ", "ServisPlus metninden oluşturuldu")
        return {"pdf_note": txt, "updated_firms": n}

    @api_router.put("/admin/firm-template")
    async def tpl_put(p: TemplateIn, me: dict = Depends(require_admin)):
        need_main()
        await db.main().app_settings.update_one({"_id": "firm_defaults"}, {"$set": {"pdf_note": p.pdf_note}}, upsert=True)
        n = 0
        for f in await db.main().firms.find({"status": {"$ne": "silindi"}}, {"_id": 0}).to_list(500):
            await push_settings(f)
            n += 1
        await audit(me, "FİRMA PDF METNİ", "şablon güncellendi")
        return {"ok": True, "updated_firms": n}

    async def access_ok(dbname, fu):
        """Firma jetonu geçerli mi: firma silinmemiş, süresi dolmamış, (alt kullanıcıysa) açık olmalı. 30 sn önbellek."""
        import time as _t
        k = (dbname, fu or "")
        e = _ACC.get(k)
        if e and _t.monotonic() - e[0] < 30:
            return e[1]
        f = await db.main().firms.find_one({"db": dbname}, {"_id": 0, "status": 1, "expires_at": 1, "id": 1})
        ok = bool(f) and f.get("status") not in ("silindi", "askida") and not expired(f)
        if ok and fu:
            ok = bool(await db.main().firm_users.find_one({"firm_id": f["id"], "email": fu, "active": {"$ne": False}}, {"_id": 1}))
        _ACC[k] = (_t.monotonic(), ok)
        return ok

    global ACCESS
    ACCESS = access_ok

    async def my_firm(request):
        if not tenant.current():
            raise HTTPException(status_code=403, detail="Yalnızca firma hesabı")
        d = await db.app_settings.find_one({"_id": "firm"}, {"_id": 0}) or {}
        f = await db.main().firms.find_one({"id": d.get("firm_id")}, {"_id": 0})
        if not f:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")
        return f

    @api_router.get("/firm/users")
    async def firm_users(request: Request, user: dict = Depends(get_current_user)):
        f = await my_firm(request)
        rows = await db.main().firm_users.find({"firm_id": f["id"]}, {"_id": 0, "password_hash": 0, "firm_id": 0, "db": 0}).sort("created_at", 1).to_list(10)
        return {"users": rows, "max": MAX_SUB, "can_manage": not getattr(request.state, "fu", ""), "owner": f.get("login_email", "")}

    @api_router.post("/firm/users")
    async def firm_user_add(p: SubIn, request: Request, user: dict = Depends(get_current_user)):
        f = await my_firm(request)
        if getattr(request.state, "fu", ""):
            raise HTTPException(status_code=403, detail="Kullanıcı eklemeyi yalnızca ana hesap yapabilir")
        em = (p.email or "").lower().strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", em):
            raise HTTPException(status_code=400, detail="Geçerli bir kullanıcı adı (e-posta) yazın")
        if len(p.password or "") < 8:
            raise HTTPException(status_code=400, detail="Şifre en az 8 karakter olmalı")
        if await db.main().firm_users.count_documents({"firm_id": f["id"]}) >= MAX_SUB:
            raise HTTPException(status_code=400, detail="En fazla %d kullanıcı eklenebilir" % MAX_SUB)
        if (await db.main().firms.find_one({"login_email": em}) or await db.main().users.find_one({"email": em})
                or await db.main().firm_users.find_one({"email": em})):
            raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kayıtlı")
        doc = {"id": uuid.uuid4().hex[:12], "firm_id": f["id"], "db": f["db"], "email": em, "name": (p.name or "").strip(),
               "password_hash": hash_password(p.password), "active": True, "created_at": _now()}
        await db.main().firm_users.insert_one(dict(doc))
        await audit(user, "FİRMA KULLANICI EKLEDİ", f["name"] + ": " + em)
        doc.pop("password_hash"); doc.pop("db"); doc.pop("firm_id")
        return doc

    @api_router.delete("/firm/users/{uid}")
    async def firm_user_del(uid: str, request: Request, user: dict = Depends(get_current_user)):
        f = await my_firm(request)
        if getattr(request.state, "fu", ""):
            raise HTTPException(status_code=403, detail="Yalnızca ana hesap silebilir")
        r = await db.main().firm_users.delete_one({"id": uid, "firm_id": f["id"]})
        _ACC.clear()
        await audit(user, "FİRMA KULLANICI SİLDİ", f["name"])
        return {"ok": bool(r.deleted_count)}

    @api_router.delete("/admin/firms/{fid}/users/{uid}")
    async def admin_firm_user_del(fid: str, uid: str, me: dict = Depends(require_admin)):
        need_main()
        r = await db.main().firm_users.delete_one({"id": uid, "firm_id": fid})
        _ACC.clear()
        await audit(me, "FİRMA KULLANICI SİLDİ", fid)
        return {"ok": bool(r.deleted_count)}

    @api_router.put("/admin/firms/{fid}/users/{uid}")
    async def admin_firm_user_toggle(fid: str, uid: str, body: dict, me: dict = Depends(require_admin)):
        need_main()
        await db.main().firm_users.update_one({"id": uid, "firm_id": fid}, {"$set": {"active": bool(body.get("active", True))}})
        _ACC.clear()
        return {"ok": True}

    @api_router.get("/firm/me")
    async def firm_me(request: Request, user: dict = Depends(get_current_user)):
        if not tenant.current():
            return {"firm": None}
        d = await db.app_settings.find_one({"_id": "firm"}, {"_id": 0}) or {}
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0, "has_logo": 1, "company_phone": 1, "company_address": 1}) or {}
        m = await db.main().firms.find_one({"id": d.get("firm_id")}, {"_id": 0, "contact_name": 1, "tax_no": 1, "tax_office": 1, "login_email": 1, "pdf_note": 1}) or {}
        return {"firm": {"name": d.get("name", ""), "features": d.get("features") or {}, "has_logo": bool(g.get("has_logo")), "sub": bool(getattr(request.state, "fu", "")),
                         "phone": g.get("company_phone", ""), "address": g.get("company_address", ""),
                         "contact_name": m.get("contact_name", ""), "tax_no": m.get("tax_no", ""), "tax_office": m.get("tax_office", ""),
                         "login_email": m.get("login_email", ""), "pdf_custom": bool(m.get("pdf_note")),
                         "pdf_raw": m.get("pdf_note") or await template()}}

    @api_router.put("/firm/me")
    async def firm_me_update(p: FirmSelf, user: dict = Depends(get_current_user)):
        if not tenant.current():
            raise HTTPException(status_code=403, detail="Yalnızca firma hesabı")
        d = await db.app_settings.find_one({"_id": "firm"}, {"_id": 0}) or {}
        fid = d.get("firm_id")
        f = await db.main().firms.find_one({"id": fid}, {"_id": 0})
        if not f:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")
        upd, changed = {}, []
        for k in ("name", "contact_name", "phone", "address"):          # bu alanları yalnızca yönetici değiştirir
            v = getattr(p, k)
            if v is not None and v.strip() != (f.get(k) or ""):
                raise HTTPException(status_code=403, detail="Firma adı, yetkili, telefon ve adresi yalnızca yönetici değiştirebilir")
        if p.logo is not None and (p.logo or "") != "":
            raise HTTPException(status_code=403, detail="Logoyu yalnızca yönetici değiştirebilir")
        for k, lab in (("name", "Firma adı"), ("contact_name", "Yetkili"), ("phone", "Telefon"), ("address", "Adres"), ("tax_no", "Vergi no"), ("tax_office", "Vergi dairesi")):
            v = getattr(p, k)
            if v is None:
                continue
            v = v.strip()
            if k == "name" and len(v) < 2:
                raise HTTPException(status_code=400, detail="Firma adı yazın")
            if v != (f.get(k) or ""):
                upd[k] = v
                changed.append(lab)
        if p.new_password:
            if len(p.new_password) < 8:
                raise HTTPException(status_code=400, detail="Yeni şifre en az 8 karakter olmalı")
            cur = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 1}) or {}
            if not p.current_password or not verify_password(p.current_password, cur.get("password_hash", "")):
                raise HTTPException(status_code=400, detail="Mevcut şifre yanlış")
            await db.users.update_one({"id": user["id"]}, {"$set": {"password_hash": hash_password(p.new_password)}})
            changed.append("Şifre")
        if not changed:
            return {"ok": True, "changed": []}
        entry = {"at": _now(), "fields": changed}
        ops = {"$push": {"self_edits": {"$each": [entry], "$slice": -20}}}
        if upd:
            ops["$set"] = upd
        await db.main().firms.update_one({"id": fid}, ops)
        f = await db.main().firms.find_one({"id": fid}, {"_id": 0})
        await push_settings(f)
        await audit(user, "FİRMA KENDİ BİLGİSİNİ GÜNCELLEDİ", f["name"] + ": " + ", ".join(changed))
        return {"ok": True, "changed": changed}

    @api_router.put("/firm/pdf-note")
    async def firm_pdf_note(p: PdfNoteIn, request: Request, user: dict = Depends(get_current_user)):
        """Firmanın kendi servis fişi alt metni; boş gönderilirse ortak şablona döner."""
        f = await my_firm(request)
        txt = (p.text or "").strip()[:3000]
        await db.main().firms.update_one({"id": f["id"]}, {"$set": {"pdf_note": txt}, "$push": {"self_edits": {"$each": [{"at": _now(), "fields": ["PDF alt metni"]}], "$slice": -20}}})
        f = await db.main().firms.find_one({"id": f["id"]}, {"_id": 0})
        await push_settings(f)
        await audit(user, "FİRMA PDF METNİ", f["name"] + (": özel metin" if txt else ": ortak şablona döndü"))
        return {"ok": True, "custom": bool(txt), "text": render(txt or await template(), f), "raw": txt or await template()}

    async def build_report(fdb, months=12):
        months = max(1, min(int(months or 12), 36))
        rows = await fdb.service_jobs.find({}, {"_id": 0, "status": 1, "total_amount": 1, "labor_fee": 1, "parts_used": 1, "completed_at": 1,
                                                "updated_at": 1, "created_at": 1, "device_type": 1, "customer_name": 1}).to_list(100000)
        def num(x):
            try:
                return float(x or 0)
            except Exception:                              # noqa: BLE001
                return 0.0
        now = datetime.now(timezone(timedelta(hours=3)))
        keys = []
        y, m = now.year, now.month
        for _ in range(months):
            keys.append("%04d-%02d" % (y, m))
            m -= 1
            if m == 0:
                y, m = y - 1, 12
        keys.reverse()
        by = {k: {"month": k, "jobs": 0, "revenue": 0.0, "parts": 0.0, "labor": 0.0} for k in keys}
        dev, cust = {}, {}
        tot = {"revenue": 0.0, "parts": 0.0, "labor": 0.0, "jobs": 0}
        openn = cancelled = 0
        for j in rows:
            st = j.get("status")
            if st in ("yeni", "atandi", "yolda", "basladi"):
                openn += 1
                continue
            if st == "iptal":
                cancelled += 1
                continue
            if st not in ("tamamlandi", "faturalandi"):
                continue
            parts = sum(num(p.get("qty", 1)) * num(p.get("unit_price")) for p in (j.get("parts_used") or []))
            labor = num(j.get("labor_fee"))
            rev = num(j.get("total_amount")) or (parts + labor)
            tot["revenue"] += rev; tot["parts"] += parts; tot["labor"] += labor; tot["jobs"] += 1
            k = (j.get("completed_at") or j.get("updated_at") or j.get("created_at") or "")[:7]
            if k in by:
                b = by[k]; b["jobs"] += 1; b["revenue"] += rev; b["parts"] += parts; b["labor"] += labor
            d = (j.get("device_type") or "Diğer").strip().title() or "Diğer"
            e = dev.setdefault(d, {"name": d, "jobs": 0, "revenue": 0.0}); e["jobs"] += 1; e["revenue"] += rev
            c = (j.get("customer_name") or "—").strip()
            e2 = cust.setdefault(c, {"name": c, "jobs": 0, "revenue": 0.0}); e2["jobs"] += 1; e2["revenue"] += rev
        ml = list(by.values())
        for b in ml:
            for k2 in ("revenue", "parts", "labor"):
                b[k2] = round(b[k2], 2)
        cur = ml[-1]; prev = ml[-2] if len(ml) > 1 else {"revenue": 0, "jobs": 0}
        chg = round((cur["revenue"] - prev["revenue"]) / prev["revenue"] * 100, 1) if prev["revenue"] else None
        best = max(ml, key=lambda b: b["revenue"]) if ml else None
        return {"months": ml, "current": cur, "previous": prev, "change_pct": chg,
                "total": {k2: (round(v, 2) if isinstance(v, float) else v) for k2, v in tot.items()},
                "avg_ticket": round(tot["revenue"] / tot["jobs"], 2) if tot["jobs"] else 0,
                "open": openn, "cancelled": cancelled, "best_month": best if best and best["revenue"] else None,
                "devices": sorted([dict(v, revenue=round(v["revenue"], 2)) for v in dev.values()], key=lambda x: -x["revenue"])[:6],
                "customers": sorted([dict(v, revenue=round(v["revenue"], 2)) for v in cust.values()], key=lambda x: -x["revenue"])[:5]}


    @api_router.get("/firm/report")
    async def firm_report(request: Request, months: int = 12, user: dict = Depends(get_current_user)):
        """Aylık/toplam ciro raporu (tamamlanan ve faturalanan işler)."""
        await my_firm(request)
        return await build_report(db, months)

    @api_router.get("/admin/firms/{fid}/report")
    async def admin_firm_report(fid: str, months: int = 12, me: dict = Depends(require_admin)):
        need_main()
        f = await get_firm(fid)
        return await build_report(db.firm(f["db"]), months)


    # ---------------- Firma modülleri: bakım hatırlatma, kasa, stok, iş atama ----------------
    def fonly():
        if not tenant.current():
            raise HTTPException(status_code=403, detail="Yalnızca firma hesabı")

    def owner_only(request):
        fonly()
        if getattr(request.state, "fu", ""):
            raise HTTPException(status_code=403, detail="Bu bölümü yalnızca yönetici (ana hesap) kullanabilir")

    def _d(v, field="Tarih", required=False):
        v = (v or "").strip()[:10]
        if not v and not required:
            return ""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail=field + " geçersiz (GG.AA.YYYY)")
        return v

    def _amt(v):
        try:
            x = round(float(v), 2)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Tutar geçersiz")
        if not (0 < x < 100000000):
            raise HTTPException(status_code=400, detail="Tutar geçersiz")
        return x

    def _today():
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _add_months(d, n):
        y, m, dd = [int(x) for x in d.split("-")]
        t = y * 12 + (m - 1) + int(n)
        y, m = divmod(t, 12)
        m += 1
        import calendar
        return "%04d-%02d-%02d" % (y, m, min(dd, calendar.monthrange(y, m)[1]))

    # --- iş atama (yalnız yönetici) ---
    @api_router.put("/firm/jobs/{jid}/assign")
    async def firm_job_assign(jid: str, body: dict, request: Request, user: dict = Depends(get_current_user)):
        owner_only(request)
        j = await db.service_jobs.find_one({"id": jid}, {"_id": 0, "id": 1})
        if not j:
            raise HTTPException(status_code=404, detail="Servis kaydı bulunamadı")
        em = str(body.get("assignee") or "").lower().strip()
        name = ""
        if em:
            f = await my_firm(request)
            u = await db.main().firm_users.find_one({"firm_id": f["id"], "email": em, "active": {"$ne": False}}, {"_id": 0, "name": 1})
            if not u:
                raise HTTPException(status_code=400, detail="Kullanıcı bulunamadı")
            name = u.get("name") or em
        await db.service_jobs.update_one({"id": jid}, {"$set": {"assigned_to_fu": em, "assigned_to_name": name}})
        return {"ok": True, "assigned_to_fu": em, "assigned_to_name": name}

    # --- bakım hatırlatma ---
    class MaintIn(BaseModel):
        name: str
        phone: Optional[str] = ""
        address: Optional[str] = ""
        device: Optional[str] = ""
        last_date: Optional[str] = ""
        next_date: str
        interval_months: Optional[int] = 12
        note: Optional[str] = ""

    def _maint_doc(p):
        name = (p.name or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Müşteri adı yazın")
        return {"name": name[:120], "phone": re.sub(r"[^0-9+ ]", "", p.phone or "")[:20], "address": (p.address or "").strip()[:300],
                "device": (p.device or "").strip()[:120], "last_date": _d(p.last_date, "Son bakım tarihi"),
                "next_date": _d(p.next_date, "Sonraki bakım tarihi", True), "interval_months": max(1, min(int(p.interval_months or 12), 120)),
                "note": (p.note or "").strip()[:500]}

    @api_router.get("/firm/maint")
    async def maint_list(user: dict = Depends(get_current_user)):
        fonly()
        rows = await db.fm_maint.find({}, {"_id": 0}).sort("next_date", 1).to_list(5000)
        t = _today()
        wk = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
        for r in rows:
            n = r.get("next_date") or ""
            r["days_left"] = (datetime.strptime(n, "%Y-%m-%d") - datetime.strptime(t, "%Y-%m-%d")).days if n else None
        return {"items": rows, "overdue": sum(1 for r in rows if r["next_date"] < t), "today": sum(1 for r in rows if r["next_date"] == t),
                "week": sum(1 for r in rows if t <= r["next_date"] <= wk), "due": sum(1 for r in rows if r["next_date"] <= t)}

    @api_router.post("/firm/maint")
    async def maint_add(p: MaintIn, user: dict = Depends(get_current_user)):
        fonly()
        doc = _maint_doc(p)
        doc.update({"id": uuid.uuid4().hex[:12], "created_at": _now(), "created_by": user.get("name", "")})
        await db.fm_maint.insert_one(dict(doc))
        return doc

    @api_router.put("/firm/maint/{mid}")
    async def maint_edit(mid: str, p: MaintIn, user: dict = Depends(get_current_user)):
        fonly()
        r = await db.fm_maint.update_one({"id": mid}, {"$set": _maint_doc(p)})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
        return {"ok": True}

    @api_router.post("/firm/maint/{mid}/done")
    async def maint_done(mid: str, user: dict = Depends(get_current_user)):
        """Bakım yapıldı: son bakım bugün olur, sonraki bakım aralık kadar ileri taşınır."""
        fonly()
        m = await db.fm_maint.find_one({"id": mid}, {"_id": 0})
        if not m:
            raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
        t = _today()
        nx = _add_months(t, m.get("interval_months") or 12)
        await db.fm_maint.update_one({"id": mid}, {"$set": {"last_date": t, "next_date": nx, "notified": ""}})
        return {"ok": True, "last_date": t, "next_date": nx}

    @api_router.delete("/firm/maint/{mid}")
    async def maint_del(mid: str, user: dict = Depends(get_current_user)):
        fonly()
        r = await db.fm_maint.delete_one({"id": mid})
        return {"ok": bool(r.deleted_count)}

    # --- kasa hareketleri (yalnız yönetici) ---
    class CashIn(BaseModel):
        kind: str
        amount: float
        title: str
        method: Optional[str] = "nakit"
        date: Optional[str] = ""

    @api_router.get("/firm/cash")
    async def cash_list(request: Request, month: Optional[str] = None, user: dict = Depends(get_current_user)):
        owner_only(request)
        m = month if (month and re.match(r"^\d{4}-\d{2}$", month)) else _today()[:7]
        allr = await db.fm_cash.find({}, {"_id": 0}).sort([("date", -1), ("created_at", -1)]).to_list(20000)
        inc = sum(r["amount"] for r in allr if r["kind"] == "gelir")
        exp = sum(r["amount"] for r in allr if r["kind"] == "gider")
        rows = [r for r in allr if (r.get("date") or "")[:7] == m]
        mi = sum(r["amount"] for r in rows if r["kind"] == "gelir")
        me_ = sum(r["amount"] for r in rows if r["kind"] == "gider")
        return {"month": m, "items": rows[:1000], "month_income": round(mi, 2), "month_expense": round(me_, 2), "balance": round(inc - exp, 2)}

    @api_router.post("/firm/cash")
    async def cash_add(p: CashIn, request: Request, user: dict = Depends(get_current_user)):
        owner_only(request)
        if p.kind not in ("gelir", "gider"):
            raise HTTPException(status_code=400, detail="Tür geçersiz")
        title = (p.title or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Açıklama yazın")
        doc = {"id": uuid.uuid4().hex[:12], "kind": p.kind, "amount": _amt(p.amount), "title": title[:160],
               "method": (p.method or "nakit")[:20], "date": _d(p.date) or _today(), "created_at": _now()}
        await db.fm_cash.insert_one(dict(doc))
        return doc

    @api_router.delete("/firm/cash/{cid}")
    async def cash_del(cid: str, request: Request, user: dict = Depends(get_current_user)):
        owner_only(request)
        r = await db.fm_cash.delete_one({"id": cid})
        return {"ok": bool(r.deleted_count)}

    # --- stok yönetimi (yalnız yönetici) ---
    class StockIn(BaseModel):
        name: str
        qty: Optional[float] = 0
        unit_price: Optional[float] = 0
        min_qty: Optional[float] = 0
        place: Optional[str] = ""

    def _stock_doc(p):
        name = (p.name or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Ürün adı yazın")
        def n(x):
            try:
                v = round(float(x or 0), 2)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Sayı geçersiz")
            if v < 0 or v > 100000000:
                raise HTTPException(status_code=400, detail="Sayı geçersiz")
            return v
        return {"name": name[:120], "unit_price": n(p.unit_price), "min_qty": n(p.min_qty), "place": (p.place or "").strip()[:60]}, n(p.qty)

    @api_router.get("/firm/stock")
    async def stock_list(request: Request, user: dict = Depends(get_current_user)):
        owner_only(request)
        rows = await db.fm_stock.find({}, {"_id": 0}).sort("name", 1).to_list(5000)
        for r in rows:
            r["low"] = r.get("min_qty", 0) > 0 and r.get("qty", 0) <= r.get("min_qty", 0)
        return {"items": rows, "count": len(rows), "low": sum(1 for r in rows if r["low"]),
                "value": round(sum(r.get("qty", 0) * r.get("unit_price", 0) for r in rows), 2)}

    @api_router.post("/firm/stock")
    async def stock_add(p: StockIn, request: Request, user: dict = Depends(get_current_user)):
        owner_only(request)
        d, q = _stock_doc(p)
        d.update({"id": uuid.uuid4().hex[:12], "qty": q, "created_at": _now()})
        await db.fm_stock.insert_one(dict(d))
        return d

    @api_router.put("/firm/stock/{sid}")
    async def stock_edit(sid: str, p: StockIn, request: Request, user: dict = Depends(get_current_user)):
        owner_only(request)
        d, _q = _stock_doc(p)
        r = await db.fm_stock.update_one({"id": sid}, {"$set": d})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Ürün bulunamadı")
        return {"ok": True}

    @api_router.post("/firm/stock/{sid}/move")
    async def stock_move(sid: str, body: dict, request: Request, user: dict = Depends(get_current_user)):
        owner_only(request)
        kind = body.get("kind")
        if kind not in ("giris", "cikis"):
            raise HTTPException(status_code=400, detail="Hareket türü geçersiz")
        q = _amt(body.get("qty"))
        s = await db.fm_stock.find_one({"id": sid}, {"_id": 0})
        if not s:
            raise HTTPException(status_code=404, detail="Ürün bulunamadı")
        nq = round(s.get("qty", 0) + (q if kind == "giris" else -q), 2)
        if nq < 0:
            raise HTTPException(status_code=400, detail="Stokta yeterli adet yok (mevcut %s)" % s.get("qty", 0))
        await db.fm_stock.update_one({"id": sid}, {"$set": {"qty": nq}})
        await db.fm_stock_log.insert_one({"id": uuid.uuid4().hex[:12], "stock_id": sid, "kind": kind, "qty": q, "note": str(body.get("note") or "")[:120], "at": _now()})
        return {"ok": True, "qty": nq}

    @api_router.delete("/firm/stock/{sid}")
    async def stock_del(sid: str, request: Request, user: dict = Depends(get_current_user)):
        owner_only(request)
        r = await db.fm_stock.delete_one({"id": sid})
        return {"ok": bool(r.deleted_count)}


    async def maint_loop():
        """Her saat: bakım günü gelen/geçen kayıtlar için firma sahibine (günde bir kez) bildirim gönderir."""
        import asyncio
        import fieldops
        await asyncio.sleep(90)
        while True:
            try:
                t = _today()
                async for f in db.main().firms.find({"status": {"$nin": ["silindi", "askida"]}}, {"_id": 0, "db": 1, "expires_at": 1}):
                    if expired(f):
                        continue
                    tok = tenant.set_firm(f["db"])
                    try:
                        due = await db.fm_maint.find({"next_date": {"$lte": t}, "notified": {"$ne": t}}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
                        if due:
                            owner = await db.users.find_one({"firm_owner": True}, {"_id": 0, "id": 1})
                            if owner:
                                names = ", ".join(d["name"] for d in due[:3]) + (" +%d" % (len(due) - 3) if len(due) > 3 else "")
                                await fieldops.push_to(db, [owner["id"]], "Kombi bakım zamanı", "%d müşterinin bakımı geldi: %s" % (len(due), names), "/tech")
                            await db.fm_maint.update_many({"id": {"$in": [d["id"] for d in due]}}, {"$set": {"notified": t}})
                    finally:
                        tenant.reset(tok)
            except Exception:                              # noqa: BLE001
                pass
            await asyncio.sleep(3600)

    global MAINT_LOOP
    MAINT_LOOP = maint_loop

    @api_router.get("/firm/logo")
    async def firm_logo(user: dict = Depends(get_current_user)):
        if not tenant.current():
            raise HTTPException(status_code=404, detail="Logo yok")
        d = await db.app_settings.find_one({"_id": "firm_logo"}, {"_id": 0}) or {}
        m = re.match(r"^data:(image/[a-z]+);base64,(.+)$", d.get("data") or "")
        if not m:
            raise HTTPException(status_code=404, detail="Logo yok")
        return Response(content=base64.b64decode(m.group(2)), media_type=m.group(1), headers={"Cache-Control": "private, max-age=300"})
