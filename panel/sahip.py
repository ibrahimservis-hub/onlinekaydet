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
import os
import asyncio
import json
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
        for f in await db.main().firms.find({"status": {"$ne": "silindi"}}, {"_id": 0, "id": 1, "name": 1, "expires_at": 1, "status": 1, "package": 1, "phone": 1, "demo": 1, "demo_firma": 1, "contact_name": 1}).to_list(5000):
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

    # ------------------------------------------------------------------ tema üretimi (yeni sektör temaları sunucuda üretilir)
    @api_router.post("/admin/themes/generate")
    async def themes_generate(me: dict = Depends(require_admin)):
        main_only()
        import subprocess, sys as _sys
        here = os.path.dirname(os.path.abspath(__file__))
        gdir = os.path.join(here, "..", "themes")
        if not os.path.isfile(os.path.join(gdir, "gen4.py")):
            raise HTTPException(404, "Tema üreticisi sunucuda yok")
        r = await asyncio.get_event_loop().run_in_executor(None, lambda: subprocess.run(
            [_sys.executable, "gen4.py"], cwd=gdir, env={**os.environ, "OK_APP_DIR": here, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600))
        return {"ok": r.returncode == 0, "out": (r.stdout or "")[-400:], "err": (r.stderr or "")[-800:], "note": "themes.json değişti: uygulamayı yeniden başlatın"}

    # ------------------------------------------------------------------ dağıtım: GitHub'daki paketi sunucuya uygular
    @api_router.post("/admin/deploy")
    async def deploy(payload: dict, me: dict = Depends(require_admin)):
        """payload: {url: raw.githubusercontent.com paket adresi, restart: bool}. Paket: {"files": {yol: metin}, "edits": [{path, old, new}]}.
        Yollar 'app/' (uygulama klasörü) ve 'themes/' ile başlar. Python dosyaları yazılmadan önce derleme denemesinden geçer; eski dosya .bak-deploy olarak saklanır."""
        main_only()
        from urllib.parse import urlparse
        u = urlparse(str(payload.get("url") or ""))
        if u.scheme != "https" or u.hostname != "raw.githubusercontent.com":
            raise HTTPException(422, "Yalnızca raw.githubusercontent.com adresi")
        r = await asyncio.get_event_loop().run_in_executor(None, lambda: requests.get(str(payload["url"]), timeout=90))
        if r.status_code != 200:
            raise HTTPException(502, "Paket indirilemedi: %s" % r.status_code)
        bundle = r.json()
        here = os.path.dirname(os.path.abspath(__file__))
        roots = {"app": here, "themes": os.path.normpath(os.path.join(here, "..", "themes")), "docroot": os.path.normpath(os.path.join(here, "..", "onlinekaydet.com"))}

        def dest(rel):
            parts = str(rel).split("/")
            if parts[0] not in roots or ".." in parts or not parts[-1] or not parts[-1].endswith((".py", ".js", ".html", ".json", ".css", ".txt", ".svg", ".xml", ".webp", ".png", ".jpg", ".woff2", ".mp4")):
                raise HTTPException(422, "İzin verilmeyen yol: %s" % rel)
            root = roots[parts[0]]
            path = os.path.normpath(os.path.join(root, *parts[1:]))
            if not path.startswith(root + os.sep):
                raise HTTPException(422, "İzin verilmeyen yol: %s" % rel)
            return path

        plan = []
        for rel, content in (bundle.get("files") or {}).items():
            if isinstance(content, dict) and "b64" in content:
                import base64
                plan.append((dest(rel), base64.b64decode(content["b64"]), rel))
            else:
                plan.append((dest(rel), str(content), rel))
        for e in bundle.get("edits") or []:
            path = dest(e["path"])
            cur = open(path, encoding="utf-8").read() if os.path.isfile(path) else ""
            for pp, cc, _ in plan:
                if pp == path:
                    cur = cc
            if cur.count(e["old"]) != 1:
                raise HTTPException(409, "Değişiklik uygulanamadı (eşleşme %d): %s" % (cur.count(e["old"]), e["path"]))
            plan = [x for x in plan if x[0] != path] + [(path, cur.replace(e["old"], e["new"], 1), e["path"])]
        for path, content, rel in plan:
            if isinstance(content, bytes):
                continue
            if path.endswith(".py"):
                try:
                    compile(content, path, "exec")
                except SyntaxError as ex:
                    raise HTTPException(422, "Söz dizimi hatası %s: %s" % (rel, ex))
            if path.endswith(".json"):
                json.loads(content)
        done = []
        for path, content, rel in plan:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.isfile(path):
                import shutil
                shutil.copyfile(path, path + ".bak-deploy")
            if isinstance(content, bytes):
                open(path, "wb").write(content)
            else:
                open(path, "w", encoding="utf-8").write(content)
            done.append(rel)
        if payload.get("restart"):
            tdir = os.path.join(here, "tmp")
            os.makedirs(tdir, exist_ok=True)
            open(os.path.join(tdir, "restart.txt"), "w").write(_now())
        return {"ok": True, "written": done, "restart": bool(payload.get("restart"))}

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

    # ------------------------------------------------------------------ paket izinleri (sektör / modül / rapor / entegrasyon / bölüm)
    def _izin_katalog():
        import blocks, entegrasyon, yprapor
        mods = sorted({m for p in blocks.SECTOR_PACKS.values() for m in p["modules"]})
        return {"sectors": [{"id": p["id"], "name": p["name"]} for p in blocks.pack_list()],
                "modules": [{"id": m, "name": m} for m in mods],
                "reports": [{"id": r["id"], "name": r["name"], "group": r["group"]} for r in yprapor.REPORTS],
                "integrations": [{"id": p["id"], "name": p["name"], "group": p["group"]} for p in entegrasyon.CATALOG],
                "blocks": [{"id": b["id"], "name": b["name"], "group": b.get("cat", "")} for b in blocks.BLOCKS]}

    _IZIN = {"sectors_allowed": "sectors", "modules": "modules", "reports_allowed": "reports", "integrations_allowed": "integrations", "allow": "blocks"}

    @api_router.get("/admin/firms/{fid}/yp-izin")
    async def yp_izin_get(fid: str, me: dict = Depends(require_admin)):
        main_only()
        f = await get_firm(fid)
        d = await db.firm(f["db"]).app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
        return {"izin": {k: d.get(k) for k in _IZIN}, "sector": d.get("sector", ""), "katalog": _izin_katalog()}

    @api_router.put("/admin/firms/{fid}/yp-izin")
    async def yp_izin_put(fid: str, payload: dict, me: dict = Depends(require_admin)):
        """Her anahtar liste (yalnız bunlar açık) ya da null (kısıt yok / paketin kendi listesi) olabilir."""
        main_only()
        f = await get_firm(fid)
        kat = _izin_katalog()
        sets, unsets = {}, {}
        for k, kk in _IZIN.items():
            if k not in payload:
                continue
            v = payload[k]
            if v is None:
                unsets[k] = ""
                continue
            if not isinstance(v, list):
                raise HTTPException(status_code=422, detail="Liste bekleniyor: " + k)
            gecerli = {x["id"] for x in kat[kk]}
            sets[k] = [x for x in dict.fromkeys(str(i) for i in v) if x in gecerli]
        if not sets and not unsets:
            raise HTTPException(status_code=422, detail="Değişiklik yok")
        up = {}
        if sets:
            up["$set"] = sets
        if unsets:
            up["$unset"] = unsets
        await db.firm(f["db"]).app_settings.update_one({"_id": "yp_pack"}, up, upsert=True)
        await audit(me, "PAKET İZNİ", f"{f['name']}: " + ", ".join(sorted(list(sets) + list(unsets))))
        return await yp_izin_get(fid, me)

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

    # ------------------------------------------------------------------ sahip müdahalesi: destek girişi, şifre, kayıt, günlük
    @api_router.post("/admin/firms/{fid}/support-link")
    async def support_link(fid: str, body: dict = None, me: dict = Depends(require_admin)):
        main_only()
        f = await get_firm(fid)
        code = uuid.uuid4().hex
        import re as _re
        body = body or {}
        to = "salon" if body.get("to") == "salon" else "admin"
        h = body.get("h") if _re.fullmatch(r"[a-z0-9/_-]{0,40}", str(body.get("h") or "")) else ""
        await db.main().support_codes.insert_one({"code": code, "firm_id": fid, "at": _now(), "ts": datetime.now(timezone.utc).timestamp(), "to": to, "h": h})
        await audit(me, "DESTEK GİRİŞİ", f["name"])
        return {"url": "/api/admin/support-enter?c=" + code}

    @api_router.get("/admin/support-enter")
    async def support_enter(c: str = ""):
        d = await db.main().support_codes.find_one_and_delete({"code": c})
        if not d or datetime.now(timezone.utc).timestamp() - d.get("ts", 0) > 90:
            raise HTTPException(status_code=403, detail="Bağlantının süresi dolmuş")
        f = await db.main().firms.find_one({"id": d["firm_id"]}, {"_id": 0})
        if not f:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")
        u = await db.firm(f["db"]).users.find_one({"firm_owner": True})
        if not u:
            raise HTTPException(status_code=404, detail="Firma yöneticisi bulunamadı")
        token = deps["create_access_token"](u["id"], u["email"], u["role"], firm=f["db"], sup=True)
        from fastapi.responses import HTMLResponse
        r = HTMLResponse('<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>Açılıyor…</title><script>try{localStorage.setItem("token",%s);localStorage.setItem("ypt",%s);localStorage.removeItem("spx_firm")}catch(e){}location.replace(%s)</script>' % (__import__("json").dumps(token), __import__("json").dumps(token), __import__("json").dumps(("/salon" + ("#" + d["h"] if d.get("h") else "")) if d.get("to") == "salon" else "/admin")),
                         headers={"Cache-Control": "no-store"})
        r.set_cookie(key="access_token", value=token, httponly=True, secure=False, samesite="lax", max_age=6 * 3600, path="/")
        return r

    @api_router.put("/admin/firms/{fid}/users/{uid}/password")
    async def sub_password(fid: str, uid: str, body: dict, me: dict = Depends(require_admin)):
        main_only()
        pw = str(body.get("password") or "")
        if len(pw) < 8:
            raise HTTPException(status_code=400, detail="Şifre en az 8 karakter olmalı")
        f = await get_firm(fid)
        h = deps["hash_password"](pw)
        r = await db.main().firm_users.update_one({"id": uid, "firm_id": fid}, {"$set": {"password_hash": h}})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        await audit(me, "FİRMA KULLANICI ŞİFRE", f["name"])
        return {"ok": True}

    @api_router.get("/admin/firms/{fid}/staff")
    async def firm_staff(fid: str, me: dict = Depends(require_admin)):
        main_only()
        f = await get_firm(fid)
        rows = await db.firm(f["db"]).users.find({}, {"_id": 0, "password_hash": 0}).to_list(200)
        return {"users": [{"id": u.get("id"), "name": u.get("name", ""), "email": u.get("email", ""), "role": u.get("role", ""),
                           "owner": bool(u.get("firm_owner")), "active": u.get("is_active", True), "phone": u.get("phone", "")} for u in rows]}

    @api_router.put("/admin/firms/{fid}/staff/{uid}")
    async def firm_staff_set(fid: str, uid: str, body: dict, me: dict = Depends(require_admin)):
        main_only()
        f = await get_firm(fid)
        upd = {}
        if "active" in body:
            upd["is_active"] = bool(body["active"])
        if body.get("password"):
            if len(str(body["password"])) < 8:
                raise HTTPException(status_code=400, detail="Şifre en az 8 karakter olmalı")
            upd["password_hash"] = deps["hash_password"](str(body["password"]))
        if not upd:
            raise HTTPException(status_code=400, detail="Değişiklik yok")
        r = await db.firm(f["db"]).users.update_one({"id": uid}, {"$set": upd})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        await audit(me, "FİRMA PERSONEL GÜNCELLEDİ", f["name"])
        return {"ok": True}

    @api_router.get("/admin/firms/{fid}/audit")
    async def firm_audit(fid: str, me: dict = Depends(require_admin)):
        main_only()
        f = await get_firm(fid)
        rows = await db.main().audit_log.find({"detail": {"$regex": __import__("re").escape(f["name"][:30])}}, {"_id": 0}).sort("at", -1).limit(80).to_list(80)
        return {"rows": rows}

    # ------------------------------------------------------------------ sahip: firma verisine doğrudan müdahale (oturum + not)
    @api_router.post("/admin/firms/{fid}/session")
    async def firm_session(fid: str, me: dict = Depends(require_admin)):
        """Sahip ekranının firma sekmeleri, firmanın kendi uçlarını firma yöneticisi jetonuyla çağırır (tek kaynak, aynı kurallar)."""
        main_only()
        f = await get_firm(fid)
        u = await db.firm(f["db"]).users.find_one({"firm_owner": True})
        if not u:
            raise HTTPException(status_code=404, detail="Firma yöneticisi bulunamadı")
        token = deps["create_access_token"](u["id"], u["email"], u["role"], firm=f["db"])
        await audit(me, "SAHİP OTURUMU", f["name"])
        return {"token": token, "firm": f["name"]}

    @api_router.post("/admin/firms/{fid}/note")
    async def firm_note(fid: str, body: dict, me: dict = Depends(require_admin)):
        main_only()
        f = await get_firm(fid)
        await audit(me, "SAHİP İŞLEMİ: " + str(body.get("action") or "")[:50], f["name"] + ": " + str(body.get("detail") or "")[:200])
        return {"ok": True}

    # ------------------------------------------------------------------ satış hattı
    STAGES = ["aday", "demo", "kurulum", "odeme"]

    @api_router.get("/admin/pipeline")
    async def pipe_list(me: dict = Depends(require_admin)):
        main_only()
        cards = await db.main().sales_pipeline.find({}, {"_id": 0}).sort("updated_at", -1).to_list(1000)
        act = [{"id": f["id"], "name": f.get("name", ""), "package": f.get("package", "")}
               for f in await db.main().firms.find({"status": "aktif"}, {"_id": 0, "id": 1, "name": 1, "package": 1}).to_list(500)]
        return {"stages": STAGES, "cards": cards, "active": act}

    @api_router.post("/admin/pipeline")
    async def pipe_add(body: dict, me: dict = Depends(require_admin)):
        main_only()
        name = str(body.get("name") or "").strip()[:80]
        if not name:
            raise HTTPException(status_code=400, detail="Firma / kişi adı yazın")
        st = body.get("stage") if body.get("stage") in STAGES else "aday"
        doc = {"id": uuid.uuid4().hex[:12], "name": name, "city": str(body.get("city") or "")[:40], "phone": str(body.get("phone") or "")[:20],
               "source": str(body.get("source") or "")[:40], "amount": float(body.get("amount") or 0), "stage": st, "notes": [],
               "created_at": _now(), "updated_at": _now()}
        if body.get("note"):
            doc["notes"].append({"at": _now(), "text": str(body["note"])[:500]})
        await db.main().sales_pipeline.insert_one(dict(doc))
        return doc

    @api_router.put("/admin/pipeline/{cid}")
    async def pipe_set(cid: str, body: dict, me: dict = Depends(require_admin)):
        main_only()
        upd = {}
        for k, n in (("name", 80), ("city", 40), ("phone", 20), ("source", 40)):
            if k in body:
                upd[k] = str(body[k] or "").strip()[:n]
        if "amount" in body:
            upd["amount"] = float(body["amount"] or 0)
        if "stage" in body:
            if body["stage"] not in STAGES:
                raise HTTPException(status_code=400, detail="Geçersiz adım")
            upd["stage"] = body["stage"]
        upd["updated_at"] = _now()
        ops = {"$set": upd}
        if body.get("add_note"):
            ops["$push"] = {"notes": {"at": _now(), "text": str(body["add_note"])[:500]}}
        r = await db.main().sales_pipeline.update_one({"id": cid}, ops)
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Kart bulunamadı")
        return await db.main().sales_pipeline.find_one({"id": cid}, {"_id": 0})

    @api_router.delete("/admin/pipeline/{cid}")
    async def pipe_del(cid: str, me: dict = Depends(require_admin)):
        main_only()
        await db.main().sales_pipeline.delete_one({"id": cid})
        return {"ok": True}

    # ------------------------------------------------------------------ kurulum adımları (otomatik + elle işaretlenen)
    MANUAL_STEPS = [("urun", "Ürün ve stok aktarıldı"), ("odeme", "İlk ödeme alındı"), ("egitim", "Eğitim yapıldı ve teslim edildi")]

    @api_router.get("/admin/onboarding")
    async def onb_list(me: dict = Depends(require_admin)):
        main_only()
        doms = {}
        async for d in db.main().firm_domains.find({}, {"_id": 0}):
            doms.setdefault(d["firm_id"], []).append(d)
        man = {m["firm_id"]: m async for m in db.main().onboarding.find({}, {"_id": 0})}
        import asyncio

        async def one(f):
            fdb = db.firm(f["db"])
            try:
                g, lg, br, ig, users, jobs = await asyncio.gather(
                    fdb.app_settings.find_one({"_id": "global"}, {"_id": 0}), fdb.app_settings.find_one({"_id": "firm_logo"}, {"_id": 0}),
                    fdb.app_settings.find_one({"_id": "brand"}, {"_id": 0}), fdb.app_settings.find_one({"_id": "integrations"}, {"_id": 0}),
                    fdb.users.count_documents({}), fdb.jobs.count_documents({}))
                g, lg, br, ig = g or {}, lg or {}, br or {}, ig or {}
            except Exception:                                    # noqa: BLE001
                g = lg = br = ig = {}
                users = jobs = 0
            dl = doms.get(f["id"], [])
            m = man.get(f["id"], {})
            done = m.get("done") or {}
            items = [{"k": "tel", "t": "Firma telefonu girildi", "ok": bool(g.get("company_phone")), "auto": True},
                     {"k": "logo", "t": "Logo yüklendi", "ok": bool(lg.get("data")), "auto": True},
                     {"k": "tema", "t": "Site teması seçildi", "ok": bool(br.get("theme")), "auto": True},
                     {"k": "alan", "t": "Alan adı bağlandı", "ok": any(x["status"] == "yayinda" for x in dl), "auto": True},
                     {"k": "sms", "t": "SMS bağlantısı doğrulandı", "ok": bool(ig.get("sms_verified")), "auto": True},
                     {"k": "kisi", "t": "Personel eklendi", "ok": users > 1, "auto": True},
                     {"k": "is", "t": "İlk servis kaydı açıldı", "ok": jobs > 0, "auto": True}]
            items += [{"k": k, "t": t, "ok": bool(done.get(k)), "auto": False} for k, t in MANUAL_STEPS]
            return {"id": f["id"], "name": f.get("name", ""), "demo": bool(f.get("demo")), "demo_firma": f.get("demo_firma", ""), "contact_name": f.get("contact_name", ""),
                    "status": f.get("status", ""), "domains": [x["domain"] for x in dl],
                    "items": items, "done": sum(1 for i in items if i["ok"]), "total": len(items), "note": m.get("note", "")}
        firms_l = await db.main().firms.find({"status": {"$ne": "silindi"}}, {"_id": 0}).sort("created_at", -1).to_list(300)
        out = await asyncio.gather(*[one(f) for f in firms_l])
        return {"firms": list(out)}

    @api_router.put("/admin/onboarding/{fid}")
    async def onb_set(fid: str, body: dict, me: dict = Depends(require_admin)):
        main_only()
        await get_firm(fid)
        upd = {}
        if body.get("key") in [k for k, _ in MANUAL_STEPS]:
            upd["done." + body["key"]] = bool(body.get("ok"))
        if "note" in body:
            upd["note"] = str(body.get("note") or "")[:1000]
        if not upd:
            raise HTTPException(status_code=400, detail="Değişiklik yok")
        await db.main().onboarding.update_one({"firm_id": fid}, {"$set": upd}, upsert=True)
        return {"ok": True}

    # ------------------------------------------------------------------ toplu SMS / duyuru
    @api_router.post("/admin/bulk-sms")
    async def bulk_sms(body: dict, me: dict = Depends(require_admin)):
        main_only()
        text = str(body.get("text") or "").strip()
        ids = [str(x) for x in (body.get("ids") or [])][:500]
        if not text or not ids:
            raise HTTPException(status_code=400, detail="Mesaj ve en az bir firma gerekli")
        cfg = await notify.get_settings(db.main())
        if cfg.get("provider") == "none":
            raise HTTPException(status_code=400, detail="Platform SMS ayarı kapalı (Sistem Durumu / Bildirim ayarlarından açın)")
        sent = skipped = 0
        for fid in ids:
            f = await db.main().firms.find_one({"id": fid}, {"_id": 0})
            if not f or not notify.norm_msisdn(f.get("phone", "")):
                skipped += 1
                continue
            ad = (f.get("contact_name") or f.get("name", "")).split(" ")[0]
            r = await notify.send(db.main(), "sms", f["phone"], notify.render(text, {"ad": ad, "firma": f.get("name", "")}), kind="owner_bulk", ref=fid, cfg=cfg)
            sent += 1 if r.get("status") != "failed" else 0
            skipped += 1 if r.get("status") == "failed" else 0
        await audit(me, "TOPLU SMS", f"{sent} gönderildi, {skipped} atlandı")
        return {"sent": sent, "skipped": skipped}

    # ------------------------------------------------------------------ sahip paneli sayfası
    SP = Path(__file__).parent / "sahip" / "index.html"

    @app.get("/yonetim")
    async def sahip_page():
        if not SP.is_file():
            raise HTTPException(status_code=404, detail="Yönetim paneli yüklenmemiş")
        return FileResponse(str(SP), media_type="text/html", headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"})
