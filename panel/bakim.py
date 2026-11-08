"""Yıllık bakım hatırlatma + tek tıkla servis kaydı (GÜNCELLEME 171).

Yönetim: Servis Kayıtları sayfasındaki "Bakım zamanı gelenler" kartı → /maintenance/due, /maintenance/remind, /maintenance/create-job
Müşteri: hatırlatma mesajındaki /bakim/<jeton> bağlantısı → tek dokunuşla servis talebi (iş emri) oluşur.
Mevcut hatırlatma motoruna (growth.py) dokunmaz; yalnızca ekleme yapar. Mesaj kanalı/ayarı bildirim ayarlarından gelir.
"""
import hashlib
import re
import secrets
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

import notify

DONE = ("tamamlandi", "faturalandi")
TR = ZoneInfo("Europe/Istanbul")
TYPES = ("kombi", "klima", "kazan")
SYS = {"id": "bakim-hatirlatma", "name": "Bakım hatırlatma", "role": "admin", "email": ""}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _d(ts):
    return str(ts or "")[:10]


def _first(n):
    return (n or "").split(" ")[0] if n else ""


def _key(cid, dev):
    return hashlib.sha1(f"{cid}|{dev}".encode()).hexdigest()[:16]


_PAGE = r"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta name="theme-color" content="#0a1f44"><title>Yıllık Bakım · ServisPlus</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f6f7f9;font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif;color:#273142}.top{background:#0a1f44;color:#fff;padding:22px 16px 56px}.w{max-width:480px;margin:0 auto}h1{margin:6px 0 2px;font-size:24px}.top p{margin:0;opacity:.8}
.c{background:#fff;border:1px solid #e6e8ec;padding:18px;margin:-34px auto 12px;max-width:480px}b.k{display:block;color:#0a1f44;font-size:17px;margin-bottom:4px}select,textarea{width:100%;padding:12px;border:1px solid #cfd6e2;font:inherit;margin-top:8px;background:#fff}
button{display:block;width:100%;margin-top:14px;padding:15px;border:0;background:#f27a1a;color:#fff;font:700 16px system-ui;cursor:pointer}button:disabled{opacity:.6}.s{color:#6b7280;font-size:13px;margin-top:10px}.ok{color:#0f9d58;font-weight:700}.er{color:#b91c1c;font-weight:600;margin-top:8px}a{color:#1155cc}</style></head><body>
<div class="top"><div class="w"><div style="font-weight:800;letter-spacing:.02em">ServisPlus</div><h1>Yıllık bakım zamanı</h1><p id="sub">&nbsp;</p></div></div>
<div class="c" id="a">Yükleniyor…</div>
<script>
var T=location.pathname.split('/').filter(Boolean).pop(),A=document.getElementById('a');
function e(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
fetch('/api/public/bakim/'+encodeURIComponent(T)).then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error(j.detail||'Bağlantı geçersiz');return j})}).then(function(d){
 document.getElementById('sub').textContent='Merhaba '+d.ad;
 if(d.job_number){A.innerHTML='<b class="k ok">✔ Talebiniz alındı</b>Kayıt No: <b>'+e(d.job_number)+'</b><div class="s">Ekibimiz sizi arayıp uygun günü netleştirecek.'+(d.phone?' Sorunuz için: <a href="tel:'+e(d.phone)+'">'+e(d.phone)+'</a>':'')+'</div>';return}
 A.innerHTML='<b class="k">'+e(d.device||'Cihazınız')+'</b>Son servisiniz: '+e(d.last||'-')+'. Düzenli yıllık bakım; verimi, güvenliği ve ömrü korur.'+
 '<select id="w"><option>Fark etmez, sizi arayın</option><option>Hafta içi sabah</option><option>Hafta içi öğleden sonra</option><option>Hafta içi akşam</option><option>Hafta sonu</option></select>'+
 '<button id="go">Bakım için servis kaydı oluştur</button><div class="er" id="er"></div><div class="s">Tek dokunuşla kaydınız oluşur; ücretsiz keşif/fiyat bilgisi sizi aradığımızda verilir. İstemiyorsanız bu mesajı yok sayabilirsiniz.</div>';
 document.getElementById('go').onclick=function(){var b=this;b.disabled=true;fetch('/api/public/bakim/'+encodeURIComponent(T)+'/talep',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({when:document.getElementById('w').value})}).then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error(j.detail||'Hata');location.reload()})}).catch(function(x){document.getElementById('er').textContent=x.message;b.disabled=false})};
}).catch(function(x){document.getElementById('sub').textContent='';A.innerHTML='<b class="k">Bu bağlantı geçerli değil</b>'+e(x.message)+'. Lütfen bizi arayın.'});
</script></body></html>"""


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    quick_create_job = deps["quick_create_job"]
    app = deps["app"]

    async def months():
        g = await db.app_settings.find_one({"_id": "growth"}, {"_id": 0, "reminders.maintenance_months": 1}) or {}
        try:
            return max(3, min(36, int(((g.get("reminders") or {}).get("maintenance_months")) or 12)))
        except (TypeError, ValueError):
            return 12

    async def company():
        s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        return s.get("company_phone", ""), (s.get("base_url") or "https://bayi.servisplus.net.tr")

    async def compute(ahead=30):
        mo = await months()
        today = datetime.now(TR).date()
        limit = (today + timedelta(days=int(ahead))).isoformat()
        proj = {"_id": 0, "id": 1, "customer_id": 1, "device_id": 1, "device_type": 1, "device_brand_name": 1, "device_model": 1, "status": 1,
                "completed_at": 1, "updated_at": 1, "customer_name": 1, "customer_phone": 1}
        jobs = await db.service_jobs.find({"device_type": {"$exists": True}}, proj).to_list(300000)
        custs = {c["id"]: c for c in await db.customers.find({}, {"_id": 0, "id": 1, "name": 1, "phone": 1, "city": 1, "district": 1, "bakim_optout": 1}).to_list(200000)}
        last, open_ = {}, set()
        for j in jobs:
            t = (j.get("device_type") or "").lower()
            if not any(x in t for x in TYPES) or not j.get("customer_id"):
                continue
            dev = j.get("device_id") or t
            k = (j["customer_id"], dev)
            if j.get("status") in DONE:
                dd = _d(j.get("completed_at") or j.get("updated_at"))
                if dd and dd > (last.get(k) or ("", None))[0]:
                    last[k] = (dd, j)
            elif j.get("status") != "iptal":
                open_.add((j["customer_id"], t))
        rem = {r["key"]: r for r in await db.maintenance_reminders.find({}, {"_id": 0}).to_list(50000)}
        out = []
        for (cid, dev), (dd, j) in last.items():
            c = custs.get(cid)
            t = (j.get("device_type") or "").lower()
            if not c or c.get("bakim_optout") or not re.sub(r"\D", "", c.get("phone") or "") or (cid, t) in open_:
                continue
            try:
                due = (datetime.fromisoformat(dd).date() + timedelta(days=mo * 30))
            except ValueError:
                continue
            if due.isoformat() > limit:
                continue
            k = _key(cid, dev)
            r = rem.get(k) or {}
            out.append({"key": k, "customer_id": cid, "name": c.get("name", ""), "phone": c.get("phone", ""), "city": c.get("city", ""), "district": c.get("district", ""),
                        "device": " ".join(x for x in (j.get("device_brand_name"), j.get("device_model"), j.get("device_type")) if x), "device_type": j.get("device_type", ""),
                        "brand": j.get("device_brand_name", ""), "device_id": j.get("device_id", ""), "last": dd, "due": due.isoformat(), "overdue_days": max(0, (today - due).days),
                        "reminded_at": r.get("sent_at", ""), "requested": bool(r.get("job_id"))})
        out.sort(key=lambda x: x["due"])
        return out

    @api_router.get("/maintenance/due")
    async def due(ahead: int = 30, _: dict = Depends(require_admin)):
        return {"months": await months(), "items": await compute(max(0, min(120, ahead)))}

    @api_router.post("/maintenance/remind")
    async def remind(payload: dict, _: dict = Depends(require_admin)):
        want = set(payload.get("keys") or [])
        rows = [r for r in await compute(120) if r["key"] in want]
        if not rows:
            raise HTTPException(404, "Kayıt bulunamadı")
        cn = await notify.get_settings(db)
        tel, base = await company()
        sent, failed, links = 0, 0, {}
        for r in rows:
            if not notify.norm_msisdn(r["phone"]):
                failed += 1
                continue
            old = await db.maintenance_reminders.find_one({"key": r["key"]}, {"_id": 0}) or {}
            tok = old.get("token") or secrets.token_urlsafe(12)
            link = base.rstrip("/") + "/bakim/" + tok
            links[r["key"]] = link
            text = (f"Merhaba {_first(r['name'])}, {r['device'] or 'cihazınız'} için yıllık bakım zamanı geldi. "
                    f"Tek dokunuşla servis kaydı oluşturmak için: {link}" + (f" — Bilgi: {tel}" if tel else ""))
            res = await notify.send(db, cn["customer"].get("channel", "sms"), r["phone"], text, kind="reminder_bakim", ref=r["key"], cfg=cn)
            ok = bool(res and res.get("status") == "sent")
            sent += 1 if ok else 0
            failed += 0 if ok else 1
            await db.maintenance_reminders.update_one({"key": r["key"]}, {"$set": {
                "key": r["key"], "token": tok, "customer_id": r["customer_id"], "device": r["device"], "device_type": r["device_type"], "brand": r["brand"], "device_id": r.get("device_id", ""),
                "last": r["last"], "ad": _first(r["name"]), "sent_at": _now() if ok else old.get("sent_at", ""), "last_try": _now()}}, upsert=True)
        return {"sent": sent, "failed": failed, "links": links}

    async def make_job(r, user, when="", source="bakim_hatirlatma", note="Yıllık bakım"):
        c = await db.customers.find_one({"id": r["customer_id"]}, {"_id": 0}) or {}
        dev = {}
        if r.get("device_id") and await db.devices.find_one({"id": r["device_id"]}, {"_id": 1}):
            dev = {"device_id": r["device_id"]}
        elif r.get("brand"):
            b = await db.brands.find_one({"name": r["brand"]}, {"_id": 0, "id": 1})
            if b:
                dev = {"brand_id": b["id"]}
        job = await quick_create_job({**dev,
            "customer_id": r["customer_id"], "customer_name": c.get("name") or r.get("name", ""), "customer_phone": c.get("phone") or r.get("phone", ""),
            "customer_city": c.get("city", ""), "customer_district": c.get("district", ""), "customer_address": c.get("address", ""),
            "device_type": r.get("device_type", ""), "device_brand_name": r.get("brand", ""),
            "fault_description": f"{note} — son servis {r.get('last', '-')}" + (f". Müşteri tercihi: {when}" if when else ""),
            "source_channel": source, "source_detail": "yıllık bakım hatırlatma"}, user)
        return job

    @api_router.post("/maintenance/create-job")
    async def create_job(payload: dict, user: dict = Depends(require_admin)):
        r = next((x for x in await compute(120) if x["key"] == payload.get("key")), None)
        if not r:
            raise HTTPException(404, "Kayıt bulunamadı (zaten servis kaydı olabilir)")
        job = await make_job(r, user, note="Yıllık bakım (yönetim kaydı)", source="bakim_yonetim")
        await db.maintenance_reminders.update_one({"key": r["key"]}, {"$set": {"key": r["key"], "job_id": job["id"], "job_at": _now()}}, upsert=True)
        return {"ok": True, "job_id": job["id"], "job_number": job.get("job_number")}

    @api_router.post("/maintenance/skip")
    async def skip(payload: dict, _: dict = Depends(require_admin)):
        """Müşteri artık hatırlatma istemiyor (örn. cihazı sattı): bir daha listelenmez."""
        r = next((x for x in await compute(120) if x["key"] == payload.get("key")), None)
        if not r:
            raise HTTPException(404, "Kayıt bulunamadı")
        await db.customers.update_one({"id": r["customer_id"]}, {"$set": {"bakim_optout": True}})
        return {"ok": True}

    # ------------------------------------------------------------------ müşteri bağlantısı
    @api_router.get("/public/bakim/{token}")
    async def pub_get(token: str):
        r = await db.maintenance_reminders.find_one({"token": token}, {"_id": 0}) if len(token) >= 10 else None
        if not r:
            raise HTTPException(404, "Bağlantı geçersiz")
        tel, _b = await company()
        out = {"ad": r.get("ad", ""), "device": r.get("device", ""), "last": r.get("last", ""), "phone": tel}
        if r.get("job_id"):
            j = await db.service_jobs.find_one({"id": r["job_id"]}, {"_id": 0, "job_number": 1})
            out["job_number"] = (j or {}).get("job_number", "")
        return out

    @api_router.post("/public/bakim/{token}/talep")
    async def pub_talep(token: str, payload: dict, request: Request):
        r = await db.maintenance_reminders.find_one({"token": token}, {"_id": 0}) if len(token) >= 10 else None
        if not r:
            raise HTTPException(404, "Bağlantı geçersiz")
        if r.get("job_id"):
            return {"ok": True}
        # çift tıklamaya karşı önce kilitle
        got = await db.maintenance_reminders.update_one({"token": token, "job_id": {"$exists": False}}, {"$set": {"job_id": "pending"}})
        if not got.modified_count:
            return {"ok": True}
        try:
            job = await make_job(r, SYS, when=str(payload.get("when", ""))[:80])
        except Exception:
            await db.maintenance_reminders.update_one({"token": token}, {"$unset": {"job_id": ""}})
            raise HTTPException(500, "Kayıt oluşturulamadı, lütfen bizi arayın")
        await db.maintenance_reminders.update_one({"token": token}, {"$set": {"job_id": job["id"], "job_at": _now()}})
        try:
            await notify.notify_owner_t(db, f"Bakım hatırlatma linkinden yeni servis kaydı: {r.get('ad', '')} · {r.get('device', '')} ({job.get('job_number', '')})", kind="maintenance")
        except Exception:
            pass
        return {"ok": True}

    @app.get("/bakim/{token}", include_in_schema=False)
    async def bakim_page(token: str):
        return HTMLResponse(_PAGE, headers={"Cache-Control": "no-store"})
