"""301/302 yönlendirmeleri ve 404 kaydı: eski adresler yeni sayfaya gider, bulunamayan adresler panelde listelenir."""
import re
from datetime import datetime, timezone
from urllib.parse import unquote

from fastapi import Depends, HTTPException

MAX = 500


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def norm(path):
    """Karşılaştırma için adres: sorgusuz, kodu çözülmüş, küçük harf, sonda / yok."""
    p = unquote(str(path or "/").split("?")[0].split("#")[0]).strip()
    if not p.startswith("/"):
        p = "/" + p
    p = re.sub(r"/{2,}", "/", p).lower()
    return p.rstrip("/") or "/"


async def _rows(db):
    d = await db.app_settings.find_one({"_id": "yp_yonlendirme"}, {"_id": 0}) or {}
    return d.get("rows") or []


async def bul(db, path):
    """Eşleşen yönlendirme: (hedef, kod) ya da None. Tam eşleşme önce, sonra '/eski/*' gibi önek kuralı."""
    p = norm(path)
    rows = await _rows(db)
    for r in rows:
        if r["from"] == p:
            return r["to"], r["code"]
    for r in rows:
        if r["from"].endswith("/*") and (p + "/").startswith(r["from"][:-1]):
            return r["to"], r["code"]
    return None


async def kaydet_404(db, path, ref=""):
    p = norm(path)
    if len(p) > 300 or re.search(r"\.(php|asp|aspx|env|git|sql|bak|ini)\b|wp-|/\.", p):
        return                                                      # tarayıcı botların taramalarını listeye doldurmayalım
    await db.yp_404.update_one({"path": p}, {"$inc": {"n": 1}, "$set": {"last": _now(), "ref": str(ref or "")[:300]}, "$setOnInsert": {"first": _now()}}, upsert=True)


def temizle(rows):
    out, seen = [], set()
    for r in (rows or [])[:MAX]:
        if not isinstance(r, dict):
            continue
        f = norm(r.get("from"))
        to = str(r.get("to") or "").strip()[:500]
        if f == "/" or f in seen:
            raise HTTPException(422, "Ana sayfa yönlendirilemez ya da aynı adres iki kez yazılmış: " + f)
        if not to or not (to.startswith("/") or re.match(r"^https?://[^\s/]+", to)):
            raise HTTPException(422, "Hedef “/sayfa” ya da “https://...” ile başlamalı: " + f)
        if to.startswith("/") and norm(to) == f:
            raise HTTPException(422, "Adres kendisine yönlendirilemez: " + f)
        code = 302 if int(r.get("code") or 301) == 302 else 301
        seen.add(f)
        out.append({"from": f, "to": to, "code": code})
    hedef = {r["from"]: norm(r["to"]) for r in out if r["to"].startswith("/")}
    for f in hedef:                                                 # döngü: a→b→a
        cur, yol = f, set()
        while cur in hedef:
            if cur in yol:
                raise HTTPException(422, "Yönlendirmeler döngü oluşturuyor: " + f)
            yol.add(cur)
            cur = hedef[cur]
    return out


def register(api_router, db, deps):
    adm = deps["require_admin"]

    @api_router.get("/yp/yonlendirme")
    async def liste(_: dict = Depends(adm)):
        log = await db.yp_404.find({}, {"_id": 0}).sort("n", -1).to_list(200)
        kur = {r["from"] for r in await _rows(db)}
        for x in log:
            x["yonlu"] = x["path"] in kur
        return {"rows": await _rows(db), "log404": log}

    @api_router.put("/yp/yonlendirme")
    async def kaydet(payload: dict, _: dict = Depends(adm)):
        rows = temizle(payload.get("rows"))
        await db.app_settings.update_one({"_id": "yp_yonlendirme"}, {"$set": {"rows": rows, "updated_at": _now()}}, upsert=True)
        return {"rows": rows}

    @api_router.delete("/yp/yonlendirme/404")
    async def log_sil(path: str = "", _: dict = Depends(adm)):
        await db.yp_404.delete_many({"path": norm(path)} if path else {})
        return {"ok": True}
