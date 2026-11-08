"""Yayın sürümleri ve geri alma (yalnızca sahip). Dosya işi cPanel cron'undaki betiklerde yapılır:
bu modül ~/servisplus-surumler/ klasörünü listeler ve geri alma isteğini ~/.servisplus-geri-al-istek dosyasına yazar;
cron (5 dk) isteği alıp uygular. Sunucuya komut çalıştırmaz."""
import os
import re
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request

HOME = os.environ.get("SP_HOME") or os.path.expanduser("~")
SD = os.path.join(HOME, "servisplus-surumler")
PIN = os.path.join(HOME, ".servisplus-pin")
REQ = os.path.join(HOME, ".servisplus-geri-al-istek")
LASTSHA = os.path.join(HOME, ".servisplus-last-sha")
LOG = os.path.join(HOME, "servisplus-deploy.log")
ID_RE = re.compile(r"^\d{8}-\d{6}_[0-9A-Za-z]+$")


def _read(p, n=2000):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read(n).strip()
    except OSError:
        return ""


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    @api_router.get("/governance/surumler")
    async def surum_list(_: dict = Depends(require_admin)):
        items = []
        try:
            for n in sorted(os.listdir(SD), reverse=True):
                if not n.endswith(".tgz"):
                    continue
                i = n[:-4]
                if not ID_RE.match(i):
                    continue
                try:
                    t = datetime.strptime(i[:15], "%Y%m%d-%H%M%S").strftime("%d.%m.%Y %H:%M")
                except ValueError:
                    t = i[:15]
                items.append({"id": i, "tarih": t, "onceki_sha": i.split("_", 1)[1], "boyut_kb": round(os.path.getsize(os.path.join(SD, n)) / 1024)})
        except OSError:
            pass
        tail = []
        try:
            with open(LOG, encoding="utf-8", errors="ignore") as f:
                tail = [x.rstrip()[:240] for x in f.readlines()[-14:]]
        except OSError:
            pass
        return {
            "kurulu": os.path.isdir(SD),
            "surumler": items[:6],
            "sabit": _read(PIN, 200),
            "bekleyen_istek": _read(REQ, 200) or (bool(os.path.exists(REQ)) and "son") or "",
            "son_sha": _read(LASTSHA, 60)[:7],
            "log": tail,
        }

    @api_router.post("/governance/surumler/geri-al")
    async def surum_geri_al(payload: dict, request: Request, user: dict = Depends(require_admin)):
        sid = str(payload.get("id") or "son").strip()
        if str(payload.get("confirm") or "").strip().upper() != "GERİ AL" and str(payload.get("confirm") or "").strip().upper() != "GERI AL":
            raise HTTPException(422, "Onay için GERİ AL yazın")
        if sid != "son" and not (ID_RE.match(sid) and os.path.isfile(os.path.join(SD, sid + ".tgz"))):
            raise HTTPException(404, "Sürüm bulunamadı")
        if sid == "son" and not os.path.isdir(SD):
            raise HTTPException(404, "Henüz kayıtlı sürüm yok")
        try:
            with open(REQ, "w", encoding="utf-8") as f:
                f.write(sid)
        except OSError as e:
            raise HTTPException(500, f"İstek yazılamadı: {e.__class__.__name__}")
        try:
            import governance
            await governance.audit(db, user, "surum_geri_al", f"Önceki sürüme dönüş istendi: {sid}")
        except Exception:                                # noqa: BLE001
            pass
        return {"ok": True, "mesaj": "İstek alındı. Sunucudaki zamanlanmış görev (en geç 5 dakika) önceki sürüme dönecek; sonra güncellemeler durdurulur."}

    @api_router.post("/governance/surumler/sabit-kaldir")
    async def surum_sabit_kaldir(user: dict = Depends(require_admin)):
        if not os.path.exists(PIN):
            return {"ok": True, "mesaj": "Güncellemeler zaten açık."}
        try:
            os.remove(PIN)
        except OSError as e:
            raise HTTPException(500, f"Kaldırılamadı: {e.__class__.__name__}")
        try:
            import governance
            await governance.audit(db, user, "surum_sabit_kaldir", "Güncellemeler yeniden açıldı")
        except Exception:                                # noqa: BLE001
            pass
        return {"ok": True, "mesaj": "Güncellemeler yeniden açıldı; en geç 5 dakikada GitHub'daki son sürüm yayına alınır."}
