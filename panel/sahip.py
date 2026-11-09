# -*- coding: utf-8 -*-
"""Sahip (platform yöneticisi) ve firma yöneticisi için: sektör kurulumu, hoş geldin mesajı, abonelik/ödeme, genel bakış,
otomatik açılma kuralları (capabilities), entegrasyon bilgileri, bağlantı testleri, sahip müdahalesi."""
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from fastapi import Depends, HTTPException, Request
from fastapi.responses import FileResponse

import notify
import sektor
import servis_ayar
import tenant

MASK = "********"
SECRETS = {"payment": ("api_key", "secret"), "marketplace": ("api_key", "api_secret")}
PROVIDERS = {"payment": ("iyzico", "paytr"), "marketplace": ("trendyol", "hepsiburada", "n11")}


def _now():
    return datetime.now(timezone.utc).isoformat()


async def on_create(db, f: dict, password: str):
    """Firma açılırken: sektör şablonu + hoş geldin mesajı. Hata firma açılışını bozmaz."""
    out = {"sector": None, "welcome": "atlandi"}
    fdb = db.firm(f["db"])
    if f.get("sector"):
        out["sector"] = await sektor.apply(fdb, f["sector"])
    try:
        cfg = await notify.get_settings(db.main())              # platformun kendi SMS ayarı (sahip)
        if cfg.get("provider") != "none" and notify.norm_msisdn(f.get("phone", "")):
            tpl = ("Merhaba {ad}, OnlineKaydet hesabınız açıldı.\nGiriş: {link}\nKullanıcı adı: {kullanici}\nŞifre: {sifre}\n"
                   "İlk girişte şifrenizi değiştirmenizi öneririz.")
            vals = {"ad": (f.get("contact_name") or f.get("name", "")).split(" ")[0], "link": "https://onlinekaydet.com/giris",
                    "kullanici": f["login_email"], "sifre": password}
            r = await notify.send(db.main(), "sms", f["phone"], notify.render(tpl, vals), kind="firm_welcome", ref=f["id"],
                                  store_text=notify.render(tpl, dict(vals, sifre=MASK)), cfg=cfg)
            out["welcome"] = r.get("status", "failed")
        else:
            out["welcome"] = "sms_ayari_veya_telefon_yok"
    except Exception as e:                                       # noqa: BLE001
        out["welcome"] = "hata: " + str(e)[:80]
    return out


def register(app, api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]

    def main_only():
        if tenant.current():
            raise HTTPException(status_code=403, detail="Bu işlem yalnız platform sahibi içindir")

    def firm_admin(user):
        if not tenant.current():
            raise HTTPException(status_code=403, detail="Yalnızca firma hesabı")
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Yalnızca firma yöneticisi")

    async def get_firm(fid):
        f = await db.main().firms.find_one({"id": fid}, {"_id": 0})
        if not f:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")
        return f

    async def audit(me, action, detail):
        try:
            import governance
            await governance.audit(db.main(), me, action, detail)
        except Exception:                                        # noqa: BLE001
            pass

    # ------------------------------------------------------------------ sektörler
    @api_router.get("/admin/sectors")
    async def sectors(me: dict = Depends(require_admin)):
        main_only()
        return sektor.public_list()

    @api_router.post("/admin/firms/{fid}/sector")
    async def firm_set_sector(fid: str, body: dict, me: dict = Depends(require_admin)):
        main_only()
        f = await get_firm(fid)
        key = str(body.get("sector") or "")
        if key not in sektor.SECTORS:
            raise HTTPException(status_code=400, detail="Bilinmeyen sektör")
        r = await sektor.apply(db.firm(f["db"]), key)
        await db.main().firms.update_one({"id": fid}, {"$set": {"sector": key}})
        await audit(me, "FİRMA SEKTÖR", f"{f['name']}: {key}")
        return r

    # ------------------------------------------------------------------ abonelik ve ödeme
    @api_router.post("/admin/firms/{fid}/payments")
    async def pay_add(fid: str, body: dict, me: dict = Depends(require_admin)):
        main_only()
        f = await get_firm(fid)
        try:
            amount = round(float(body.get("amount")), 2)
        except Exception:                                        # noqa: BLE001
            raise HTTPException(status_code=400, detail="Tutar sayı olmalı")
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Tutar sıfırdan büyük olmalı")
        days = int(body.get("extend_days") or 0)
        doc = {"id": uuid.uuid4().hex[:12], "firm_id": fid, "amount": amount, "method": str(body.get("method") or "havale")[:20],
               "note": str(body.get("note") or "")[:200], "extend_days": days, "at": _now()}
        await db.main().firm_payments.insert_one(dict(doc))
        if days > 0:                                             # süre, bitişten (veya bugünden, hangisi sonraysa) uzar
            cur = f.get("expires_at") or ""
            base = datetime.fromisoformat(cur) if cur and cur > _now() else datetime.now(timezone.utc)
            new = (base + timedelta(days=min(days, 3650))).isoformat()
            await db.main().firms.update_one({"id": fid}, {"$set": {"expires_at": new, "status": "aktif"}})
            await db.firm(f["db"]).users.update_many({"firm_owner": True}, {"$set": {"is_active": True}})
            doc["expires_at"] = new
            try:
                import firms
                firms._ACC.clear()
            except Exception:                                    # noqa: BLE001
                pass
        await audit(me, "FİRMA ÖDEME", f"{f['name']}: {amount} TL, +{days} gün")
        doc.pop("_id", None)
        return doc

    @api_router.get("/admin/firms/{fid}/payments")
    async def pay_list(fid: str, me: dict = Depends(require_admin)):
        main_only()
        await get_firm(fid)
        return await db.main().firm_payments.find({"firm_id": fid}, {"_id": 0}).sort("at", -1).to_list(500)

    @api_router.get("/admin/subscriptions")
    async def subs(days: int = 14, me: dict = Depends(require_admin)):
        main_only()
        now = _now()
        lim = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
        soon, gone = [], []
        for f in await db.main().firms.find({"status": {"$ne": "silindi"}}, {"_id": 0, "id": 1, "name": 1, "expires_at": 1, "status": 1, "package": 1, "phone": 1}).to_list(5000):
            e = f.get("expires_at") or ""
            if not e:
                continue
            if e < now:
                gone.append(f)
            elif e <= lim:
                soon.append(f)
        return {"expiring": sorted(soon, key=lambda x: x["expires_at"]), "expired": sorted(gone, key=lambda x: x["expires_at"])}

    @api_router.post("/admin/subscriptions/remind")
    async def subs_remind(body: dict, me: dict = Depends(require_admin)):
        """Süresi yaklaşan/dolan firmalara hatırlatma SMS'i (platform SMS ayarıyla)."""
        main_only()
        days = int(body.get("days") or 7)
        cfg = await notify.get_settings(db.main())
        res = await subs(days, me)
        sent, skipped = 0, 0
        for f in res["expiring"] + res["expired"]:
            if cfg.get("provider") == "none" or not notify.norm_msisdn(f.get("phone", "")):
                skipped += 1
                continue
            txt = f"{f['name']}: OnlineKaydet kullanım süreniz {f['expires_at'][:10]} tarihinde {'doldu' if f in res['expired'] else 'dolacak'}. Yenilemek için bizimle iletişime geçin."
            if await db.main().outbox.find_one({"kind": "firm_renew", "ref": f["id"], "created_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()}}):
                skipped += 1                                     # aynı firmaya 3 günde bir
                continue
            r = await notify.send(db.main(), "sms", f["phone"], txt, kind="firm_renew", ref=f["id"], cfg=cfg)
            sent += r.get("status") == "sent"
            skipped += r.get("status") != "sent"
        return {"sent": sent, "skipped": skipped}

    # ------------------------------------------------------------------ genel bakış
    @api_router.get("/admin/overview")
    async def overview(me: dict = Depends(require_admin)):
        main_only()
        firms = await db.main().firms.find({"status": {"$ne": "silindi"}}, {"_id": 0}).to_list(5000)
        now = _now()
        lim = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
        pk, sec = {}, {}
        for f in firms:
            pk[f.get("package") or "-"] = pk.get(f.get("package") or "-", 0) + 1
            sec[f.get("sector") or "-"] = sec.get(f.get("sector") or "-", 0) + 1
        since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        rev = await db.main().firm_payments.find({"at": {"$gte": since}}, {"_id": 0, "amount": 1}).to_list(100000)
        jobs30 = 0
        for f in firms:
            jobs30 += await db.firm(f["db"]).service_jobs.count_documents({"created_at": {"$gte": since}})
        return {"firms": len(firms), "active": sum(f.get("status") == "aktif" and not ((f.get("expires_at") or "~") < now and f.get("expires_at")) for f in firms),
                "suspended": sum(f.get("status") == "askida" for f in firms),
                "expired": sum(bool(f.get("expires_at")) and f["expires_at"] < now for f in firms),
                "expiring_14d": sum(bool(f.get("expires_at")) and now <= f["expires_at"] <= lim for f in firms),
                "packages": pk, "sectors": sec, "revenue_30d": round(sum(r["amount"] for r in rev), 2), "jobs_30d": jobs30}

    # ------------------------------------------------------------------ sahip müdahalesi (firma adına ayar)
    @api_router.get("/admin/firms/{fid}/service-settings")
    async def owner_ss_get(fid: str, me: dict = Depends(require_admin)):
        main_only()
        f = await get_firm(fid)
        return await servis_ayar.get(db.firm(f["db"]))

    @api_router.put("/admin/firms/{fid}/service-settings")
    async def owner_ss_put(fid: str, payload: dict, me: dict = Depends(require_admin)):
        main_only()
        f = await get_firm(fid)
        fdb = db.firm(f["db"])
        new = await servis_ayar.save(fdb, payload)
        entry = {"at": _now(), "by": me.get("email", ""), "keys": sorted(payload.keys())}
        await fdb.app_settings.update_one({"_id": "owner_edits"}, {"$push": {"items": {"$each": [entry], "$slice": -50}}}, upsert=True)
        await audit(me, "SAHİP MÜDAHALESİ", f"{f['name']}: servis ayarı {', '.join(entry['keys'])}")
        return new

    @api_router.get("/firm/owner-edits")
    async def owner_edits(user: dict = Depends(get_current_user)):
        firm_admin(user)
        d = await db.app_settings.find_one({"_id": "owner_edits"}, {"_id": 0}) or {}
        return d.get("items") or []

    # ------------------------------------------------------------------ entegrasyon bilgileri (ödeme / pazaryeri)
    def _mask(kind, d):
        d = dict(d or {})
        for k in SECRETS[kind]:
            if d.get(k):
                d[k] = MASK
        return d

    @api_router.get("/firm/integrations")
    async def integ_get(user: dict = Depends(get_current_user)):
        firm_admin(user)
        d = await db.app_settings.find_one({"_id": "integrations"}, {"_id": 0}) or {}
        return {k: _mask(k, d.get(k)) for k in SECRETS}

    @api_router.put("/firm/integrations")
    async def integ_put(body: dict, user: dict = Depends(get_current_user)):
        firm_admin(user)
        cur = await db.app_settings.find_one({"_id": "integrations"}, {"_id": 0}) or {}
        for kind in SECRETS:
            if kind not in body:
                continue
            inc = dict(body[kind] or {})
            if inc.get("provider") and inc["provider"] not in PROVIDERS[kind]:
                raise HTTPException(status_code=400, detail="Bilinmeyen sağlayıcı")
            old = cur.get(kind) or {}
            for k in SECRETS[kind]:
                if inc.get(k) == MASK:
                    inc[k] = old.get(k, "")
            inc["verified"] = False                              # bilgi değişti: doğrulama sıfırlanır
            cur[kind] = {**old, **inc}
        await db.app_settings.update_one({"_id": "integrations"}, {"$set": cur}, upsert=True)
        return {k: _mask(k, cur.get(k)) for k in SECRETS}

    # ------------------------------------------------------------------ bağlantı testi (SMS)
    @api_router.post("/firm/test-sms")
    async def test_sms(body: dict, user: dict = Depends(get_current_user)):
        firm_admin(user)
        cfg = await notify.get_settings(db)
        prov = cfg.get("provider")
        if prov == "none":
            raise HTTPException(status_code=400, detail="SMS sağlayıcısı seçilmemiş")
        if prov == "iletimerkezi":                               # gönderim yapmadan kimlik + bakiye doğrulaması (resmi get-balance)
            n = cfg["iletimerkezi"]
            if not (n.get("key") and n.get("hash")):
                raise HTTPException(status_code=400, detail="API anahtarı ve hash girilmemiş")
            try:
                r = requests.post("https://api.iletimerkezi.com/v1/get-balance/json",
                                  json={"request": {"authentication": {"key": n["key"], "hash": n["hash"]}}}, timeout=15)
                st = r.json()["response"]["status"]
            except Exception as e:                               # noqa: BLE001
                return {"ok": False, "detail": "Sağlayıcıya ulaşılamadı: " + str(e)[:80]}
            if str(st.get("code")) != "200":
                return {"ok": False, "detail": f"Kimlik doğrulanamadı ({st.get('code')}): {st.get('message')}"}
            bal = (r.json()["response"].get("balance") or {})
            res = {"ok": True, "detail": "Bağlantı ve kimlik doğrulandı", "balance": bal.get("sms", bal)}
        else:
            to = str(body.get("to") or "")
            if not notify.norm_msisdn(to):
                raise HTTPException(status_code=400, detail="Test için bir telefon numarası yazın")
            r = await notify.send(db, "sms", to, "OnlineKaydet SMS bağlantı testi", kind="sms_test", cfg=cfg)
            res = {"ok": r.get("status") == "sent", "detail": "Test SMS'i gönderildi" if r.get("status") == "sent" else r.get("error", "gönderilemedi")}
        await db.app_settings.update_one({"_id": "integrations"}, {"$set": {"sms_verified": res["ok"], "sms_verified_at": _now()}}, upsert=True)
        return res

    # ------------------------------------------------------------------ otomatik açılma kuralları
    @api_router.get("/firm/capabilities")
    async def caps(user: dict = Depends(get_current_user)):
        """Girilen veriye göre özelliklerin açık/kapalı durumu. Boş veri → özellik gizli; bilgi var ama doğrulanmadıysa 'dogrulanmadi'."""
        if not tenant.current():
            raise HTTPException(status_code=403, detail="Yalnızca firma hesabı")
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        lg = await db.app_settings.find_one({"_id": "firm_logo"}, {"_id": 0}) or {}
        ig = await db.app_settings.find_one({"_id": "integrations"}, {"_id": 0}) or {}
        cfg = await notify.get_settings(db)
        prov = cfg.get("provider", "none")
        sms_filled = prov != "none" and any(v for k, v in (cfg.get(prov) or {}).items()) if prov in cfg else prov == "webhook"
        pay = ig.get("payment") or {}
        mk = ig.get("marketplace") or {}
        pay_filled = bool(pay.get("provider") and pay.get("api_key") and pay.get("secret"))
        mk_filled = bool(mk.get("provider") and mk.get("api_key") and mk.get("api_secret"))

        def st(filled, verified=False):
            return "acik" if filled and verified else "dogrulanmadi" if filled else "kapali"
        return {
            "pdf_phone": {"state": "acik" if g.get("company_phone") else "kapali", "why": "Firma telefonu girilince fişte ve sitede görünür"},
            "pdf_logo": {"state": "acik" if lg.get("data") else "kapali", "why": "Logo yüklenince fişte görünür"},
            "sms": {"state": st(sms_filled, bool(ig.get("sms_verified"))), "why": "Sağlayıcı bilgisi girilip bağlantı doğrulanınca müşteri mesajları açılır"},
            "card_payment": {"state": st(pay_filled, bool((ig.get("payment") or {}).get("verified"))), "why": "Ödeme sağlayıcı bilgisi girilince kartla ödeme açılır"},
            "marketplace": {"state": st(mk_filled, bool((ig.get("marketplace") or {}).get("verified"))), "why": "Pazaryeri bilgisi girilince ürün senkronu açılır"},
        }

    # ------------------------------------------------------------------ sahip paneli sayfası
    SP = Path(__file__).parent / "sahip" / "index.html"

    @app.get("/yonetim")
    async def sahip_page():
        if not SP.is_file():
            raise HTTPException(status_code=404, detail="Yönetim paneli yüklenmemiş")
        return FileResponse(str(SP), media_type="text/html", headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"})
