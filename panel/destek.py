# -*- coding: utf-8 -*-
"""Destek talepleri: işletmeden OnlineKaydet'e açılan kayıtlar.

Telefonla destek, yazıya dökülmediği için iki kez anlatılır. Burada her talep
numaralı, ekran görüntülü ve zaman damgalı tutuluyor; hangi ekranda olduğu
kayıttan belli oluyor, aynı soru ikinci kez sorulduğunda geçmişi açılıyor.

Durum akışı zorlanır: kapanmış talep yeniden açılmaz, yerine yeni talep açılır
ve eskisine bağlanır — böylece "şu talebi tekrar açtım" karmaşası olmaz.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

KONULAR = [("hata", "Bir şey çalışmıyor"), ("soru", "Nasıl yapılır?"),
           ("entegrasyon", "Entegrasyon / bağlantı"), ("fatura", "Abonelik ve fatura"),
           ("istek", "Yeni özellik isteği"), ("diger", "Diğer")]
ONCELIK = [("normal", "Normal"), ("yuksek", "İşim duruyor")]
DURUM = {"acik": "Açık", "yanit": "Yanıtlandı", "bekliyor": "Sizden yanıt bekliyor",
         "kapandi": "Kapandı"}
EKRANLAR = ["Bugün", "Takvim", "Randevular", "Müşteriler", "Kasa", "Ürünler", "Siparişler",
            "Kampanyalar", "İçerikler", "Bildirimler", "Entegrasyonlar", "Ekip", "Raporlar",
            "Web Sitem", "Ayarlar", "Site (müşteri tarafı)"]


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


def _t(v, n):
    return " ".join(str(v or "").split())[:n]


def _long(v, n):
    return str(v or "").replace("\r", "")[:n].strip()


def dosyalar(v):
    """Ekler yalnız kendi yükleme ucumuzdan gelebilir; dışarıdan bağlantı kabul edilmez."""
    out = []
    for f in (v or [])[:8]:
        u = _t((f or {}).get("url") if isinstance(f, dict) else f, 400)
        if u.startswith("/api/files/") or u.startswith("/uploads/"):
            out.append({"url": u, "name": _t((f or {}).get("name") if isinstance(f, dict) else "", 120)})
    return out


def view(t):
    t = dict(t)
    t["state_name"] = DURUM.get(t.get("state"), t.get("state", ""))
    t["n_mesaj"] = len(t.get("messages") or [])
    son = (t.get("messages") or [{}])[-1]
    t["last_by"] = son.get("by", "")
    t["last_at"] = son.get("at", t.get("at", ""))
    return t


def register(api_router, db, deps):
    adm = deps["require_admin"]

    @api_router.get("/yp/destek")
    async def liste(state: str = "", q: str = "", _: dict = Depends(adm)):
        rows = await db.yp_tickets.find({}, {"_id": 0}).to_list(2000)
        qq = _t(q, 60).lower()
        if qq:
            rows = [r for r in rows if qq in (r.get("subject", "") + " " + r.get("no", "")).lower()]
        if state == "acik":
            rows = [r for r in rows if r.get("state") != "kapandi"]
        elif state in DURUM:
            rows = [r for r in rows if r.get("state") == state]
        rows.sort(key=lambda r: r.get("last_at") or r.get("at") or "", reverse=True)
        allr = await db.yp_tickets.find({}, {"_id": 0, "state": 1}).to_list(2000)
        return {"items": [view(r) for r in rows],
                "counts": dict({k: len([x for x in allr if x.get("state") == k]) for k in DURUM},
                               hepsi=len(allr), acik=len([x for x in allr if x.get("state") != "kapandi"])),
                "konular": [{"id": k, "name": n} for k, n in KONULAR],
                "oncelik": [{"id": k, "name": n} for k, n in ONCELIK],
                "ekranlar": list(EKRANLAR), "states": [{"id": k, "name": v} for k, v in DURUM.items()]}

    @api_router.get("/yp/destek/{tid}")
    async def tek(tid: str, _: dict = Depends(adm)):
        t = await db.yp_tickets.find_one({"id": _t(tid, 24)}, {"_id": 0})
        if not t:
            raise HTTPException(404, "Talep bulunamadı")
        return {"item": view(t)}

    @api_router.post("/yp/destek")
    async def ac(payload: dict, user: dict = Depends(adm)):
        konu = _t(payload.get("subject"), 140)
        if len(konu) < 5:
            raise HTTPException(422, "Konuyu birkaç kelimeyle yazın")
        body = _long(payload.get("body"), 6000)
        if len(body) < 10:
            raise HTTPException(422, "Sorunu biraz daha anlatın; ne yaptınız, ne bekliyordunuz?")
        kat = _t(payload.get("category"), 20)
        if kat not in dict(KONULAR):
            raise HTTPException(422, "Konu başlığı seçin")
        onc = _t(payload.get("priority"), 20) or "normal"
        if onc not in dict(ONCELIK):
            raise HTTPException(422, "Öncelik geçersiz")
        n = await db.yp_tickets.count_documents({})
        ek = dosyalar(payload.get("files"))
        t = {"id": uuid.uuid4().hex[:12], "no": "DT-%s-%04d" % (_now()[:4], n + 1),
             "subject": konu, "category": kat, "priority": onc,
             "screen": _t(payload.get("screen"), 60), "state": "acik",
             "at": _now(), "last_at": _now(), "by": user.get("email") or "panel",
             "parent": _t(payload.get("parent"), 24),
             "messages": [{"at": _now(), "by": "isletme", "text": body, "files": ek}]}
        await db.yp_tickets.insert_one(dict(t))
        return {"ok": True, "item": view(t)}

    @api_router.post("/yp/destek/{tid}/mesaj")
    async def mesaj(tid: str, payload: dict, _: dict = Depends(adm)):
        t = await db.yp_tickets.find_one({"id": _t(tid, 24)}, {"_id": 0})
        if not t:
            raise HTTPException(404, "Talep bulunamadı")
        if t.get("state") == "kapandi":
            raise HTTPException(422, "Bu talep kapandı. Aynı konu sürüyorsa yeni talep açın, eskisine bağlanır.")
        text = _long(payload.get("text"), 6000)
        ek = dosyalar(payload.get("files"))
        if not text and not ek:
            raise HTTPException(422, "Mesaj yazın ya da ekran görüntüsü ekleyin")
        m = {"at": _now(), "by": "isletme", "text": text, "files": ek}
        await db.yp_tickets.update_one({"id": t["id"]}, {"$push": {"messages": m},
                                                         "$set": {"state": "acik", "last_at": _now()}})
        return {"ok": True, "item": view(await db.yp_tickets.find_one({"id": t["id"]}, {"_id": 0}))}

    @api_router.post("/yp/destek/{tid}/kapat")
    async def kapat(tid: str, payload: dict, _: dict = Depends(adm)):
        t = await db.yp_tickets.find_one({"id": _t(tid, 24)}, {"_id": 0})
        if not t:
            raise HTTPException(404, "Talep bulunamadı")
        st = {"state": "kapandi", "closed_at": _now(), "last_at": _now(),
              "rating": max(min(int(payload.get("rating") or 0), 5), 0)}
        await db.yp_tickets.update_one({"id": t["id"]}, {"$set": st})
        return {"ok": True, "item": view(dict(t, **st))}

    return api_router
