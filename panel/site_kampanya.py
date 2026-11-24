"""Ana sayfa ve fiyat sayfasındaki kampanya şeridi/sayacı.

- Kampanyalar ana veritabanında (campaigns) tutulur; sahip panelinden düzenlenir.
- /public/campaign o an geçerli kampanyayı döndürür; süre dolunca bir sonraki otomatik gelir.
- Hiçbiri geçerli değilse sürekli (always) kampanya gösterilir.
"""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends

TR = timezone(timedelta(hours=3))
OFFER = "2 yıllık lisans alana 1 yıl hediye"
ALANLAR = ("name", "strip", "l1", "l2", "em", "lead", "badge_top", "badge_big", "badge_sub", "accent", "cta", "start", "end")
HEX = "0123456789abcdefABCDEF"


def _d(y, m, d, h=0):
    return datetime(y, m, d, h, 0, tzinfo=TR).isoformat()


def _k(i, name, s, e, strip, l1, l2, em, lead, big="2 YIL AL", sub="1 YIL HEDİYE", accent="#d0345f", yearly=False):
    return {"id": i, "name": name, "start": s, "end": e, "strip": strip, "l1": l1, "l2": l2, "em": em, "lead": lead,
            "badge_top": "KAMPANYA", "badge_big": big, "badge_sub": sub, "accent": accent, "cta": "Kampanyayı yakalayın",
            "active": True, "yearly": yearly, "always": False}


SEED = [
    {"id": "surekli", "name": "Her zaman (kampanya yokken)", "start": "", "end": "", "strip": "7 gün ücretsiz demo · Kart bilgisi gerekmez",
     "l1": "Sitenizi açın,", "l2": "siparişi alın,", "em": "işi takip edin.",
     "lead": "Sektörünüze hazır temayı seçin. Sipariş, randevu, kasa ve personel tek panelde.",
     "badge_top": "ÜCRETSİZ", "badge_big": "7 GÜN", "badge_sub": "deneme", "accent": "#d0345f", "cta": "Ücretsiz deneyin",
     "active": True, "yearly": False, "always": True},
    _k("efsane-kasim-2026", "Efsane Kasım 2026", _d(2026, 11, 1), _d(2026, 12, 1), "Efsane Kasım: 2 yıllık lisans alana 1 yıl hediye",
       "Efsane Kasım'da", "işinizi dijitale taşıyın,", "2 yıl al, 1 yıl hediye.", "Kasım'a özel fırsatla sitenizi, siparişinizi ve randevularınızı tek panelde toplayın.", accent="#2f6fe0"),
    _k("yilbasi-2026", "Yılbaşı kampanyası", _d(2026, 12, 1), _d(2027, 1, 1), "Yeni yıla özel: 2 yıllık lisans alana 1 yıl hediye",
       "Yeni yıla", "yeni bir düzenle girin,", "2 yıl al, 1 yıl hediye.", "Yıla hazır başlayın: sitenizi kurun, siparişleri ve işleri aynı yerden yönetin.", accent="#c8352f", yearly=True),
    _k("yeni-duzen-2027", "Yeni yıl, yeni düzen", _d(2027, 1, 1), _d(2027, 2, 8), "Yeni yıl düzeni: 2 yıllık lisans alana 1 yıl hediye",
       "Yeni yıl,", "yeni düzen:", "2 yıl al, 1 yıl hediye.", "Defteri, Excel'i ve dağınık notları bırakın; kayıtlarınız tek panelde düzenli dursun.", accent="#0e8a8a"),
    _k("ramazan-2027", "Ramazan'a hoş geldin", _d(2027, 2, 8), _d(2027, 3, 9), "Hoş geldin Ramazan: 2 yıllık lisans alana 1 yıl hediye",
       "Hoş geldin Ramazan,", "işiniz kolay ilerlesin,", "2 yıl al, 1 yıl hediye.", "Yoğun dönemde siparişleriniz ve randevularınız karışmasın; hepsi tek panelde.", accent="#7a5cc4"),
    _k("ramazan-bayrami-2027", "Ramazan Bayramı", _d(2027, 3, 9), _d(2027, 3, 12), "Bayramınız mübarek olsun: 2 yıl al, 1 yıl hediye",
       "Bayramınız", "mübarek olsun,", "2 yıl al, 1 yıl hediye.", "Bayram sonrası düzenli bir başlangıç için kampanya bu günlerde de geçerli.", accent="#c27a1b"),
    _k("bahar-2027", "Bahar kampanyası", _d(2027, 3, 12), _d(2027, 4, 16), "Bahar kampanyası: 2 yıllık lisans alana 1 yıl hediye",
       "Baharda işinizi", "yeniden kurun,", "2 yıl al, 1 yıl hediye.", "Yeni sezona hazır bir site ve düzenli bir iş takibiyle başlayın.", accent="#2e9e5b"),
    _k("23-nisan-2027", "23 Nisan", _d(2027, 4, 16), _d(2027, 4, 24), "23 Nisan'a özel: 2 yıllık lisans alana 1 yıl hediye",
       "23 Nisan", "coşkusuna özel,", "2 yıl al, 1 yıl hediye.", "Çocuk Bayramı haftasına özel kampanya: sitenizi bugün kurun.", accent="#d4382c", yearly=True),
    _k("anneler-gunu-2027", "Anneler Günü", _d(2027, 4, 24), _d(2027, 5, 10), "Anneler Günü'ne özel: 2 yıl al, 1 yıl hediye",
       "Anneler Günü'ne", "özel fırsat,", "2 yıl al, 1 yıl hediye.", "Çiçekçi, butik ve hediyelik işletmeler için sezonun en yoğun günlerine hazır olun.", accent="#d6498a"),
    _k("kurban-bayrami-2027", "Kurban Bayramı ve 19 Mayıs", _d(2027, 5, 10), _d(2027, 5, 20), "Bayram ve 19 Mayıs'a özel: 2 yıl al, 1 yıl hediye",
       "Bayramınız mübarek,", "19 Mayıs kutlu olsun,", "2 yıl al, 1 yıl hediye.", "Bayram dönemi kampanyasıyla işinizi dijitale taşıyın.", accent="#b3472f"),
    _k("yaz-2027", "Yaz sezonu", _d(2027, 5, 20), _d(2027, 6, 14), "Yaz sezonu kampanyası: 2 yıllık lisans alana 1 yıl hediye",
       "Yaz sezonuna", "hazır girin,", "2 yıl al, 1 yıl hediye.", "Sezon yoğunluğu başlamadan sitenizi ve randevu düzeninizi kurun.", accent="#e0861a"),
    _k("babalar-gunu-2027", "Babalar Günü", _d(2027, 6, 14), _d(2027, 6, 21), "Babalar Günü'ne özel: 2 yıl al, 1 yıl hediye",
       "Babalar Günü'ne", "özel fırsat,", "2 yıl al, 1 yıl hediye.", "Hediye ve hizmet satan işletmeler için haftaya özel kampanya.", accent="#1f5fa8"),
    _k("yaz-ortasi-2027", "Yaz ortası", _d(2027, 6, 21), _d(2027, 9, 1), "Yaz kampanyası: 2 yıllık lisans alana 1 yıl hediye",
       "Yazın işinizi", "yavaşlatmayın,", "2 yıl al, 1 yıl hediye.", "Tatil sezonunda da siparişleriniz ve randevularınız panelden takipte olsun.", accent="#1aa0b8"),
    _k("yeni-sezon-2027", "Yeni sezon", _d(2027, 9, 1), _d(2027, 10, 20), "Yeni sezon kampanyası: 2 yıllık lisans alana 1 yıl hediye",
       "Yeni sezona", "düzenli başlayın,", "2 yıl al, 1 yıl hediye.", "Okul, iş ve sezon açılışında sitenizi ve kayıtlarınızı toparlayın.", accent="#7a4fd0"),
    _k("29-ekim-2027", "29 Ekim Cumhuriyet Bayramı", _d(2027, 10, 20), _d(2027, 10, 30), "Cumhuriyet Bayramı'na özel: 2 yıl al, 1 yıl hediye",
       "Cumhuriyet", "Bayramı kutlu olsun,", "2 yıl al, 1 yıl hediye.", "Bayram haftasına özel kampanyayla işinizi dijitale taşıyın.", accent="#c8312b", yearly=True),
    _k("ogretmenler-gunu-2027", "Öğretmenler Günü", _d(2027, 11, 15), _d(2027, 11, 25), "Öğretmenler Günü'ne özel: 2 yıl al, 1 yıl hediye",
       "Öğretmenler Günü'ne", "özel fırsat,", "2 yıl al, 1 yıl hediye.", "Kurs, etüt ve özel ders veren işletmeler için randevu ve kayıt düzeni.", accent="#2a6fd6", yearly=True),
]


def _parse(s):
    try:
        d = datetime.fromisoformat(str(s))
        return d if d.tzinfo else d.replace(tzinfo=TR)
    except (TypeError, ValueError):
        return None


def _at(c, now):
    """Kampanyanın şimdiye göre geçerli penceresini döndürür (yıllık tekrar varsa en yakın yıl)."""
    s, e = _parse(c.get("start")), _parse(c.get("end"))
    if not s or not e or e <= s:
        return None
    if c.get("yearly"):
        for dy in (0, -1, 1):
            try:
                s2, e2 = s.replace(year=s.year + dy), e.replace(year=e.year + dy)
            except ValueError:
                continue
            if s2 <= now < e2:
                return s2, e2
        return None
    return (s, e) if s <= now < e else None


def pick(rows, now=None):
    now = now or datetime.now(TR)
    best = None
    for c in rows:
        if not c.get("active", True) or c.get("always"):
            continue
        w = _at(c, now)
        if w and (best is None or w[0] > best[1][0]):
            best = (c, w)
    if best:
        return best[0], best[1][1]
    alw = next((c for c in rows if c.get("always") and c.get("active", True)), None)
    return alw, None


def _clean(p, cur=None):
    out = {}
    for k in ALANLAR:
        if k in p:
            v = str(p[k] or "").strip()
            out[k] = v[:160] if k not in ("lead",) else v[:260]
    if "accent" in out and not (len(out["accent"]) == 7 and out["accent"][0] == "#" and all(c in HEX for c in out["accent"][1:])):
        raise HTTPException(422, "Renk #rrggbb biçiminde olmalı")
    for k in ("start", "end"):
        if k in out and out[k] and not _parse(out[k]):
            raise HTTPException(422, "Tarih biçimi geçersiz")
    for k in ("active", "yearly"):
        if k in p:
            out[k] = bool(p[k])
    return out


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    def main():
        return db.main()

    def need_main():
        from tenant import current
        if current():
            raise HTTPException(403, "Bu işlem yalnız ana yönetim içindir")

    async def rows():
        col = main().site_campaigns
        if not await col.find_one({}):
            await col.insert_many([dict(x) for x in SEED])
        return await col.find({}, {"_id": 0}).to_list(500)

    @api_router.get("/public/campaign")
    async def public_campaign():
        c, end = pick(await rows())
        if not c:
            raise HTTPException(404, "Kampanya yok")
        out = {k: c.get(k, "") for k in ("id", "name", "strip", "l1", "l2", "em", "lead", "badge_top", "badge_big", "badge_sub", "accent", "cta")}
        out["always"] = bool(c.get("always"))
        out["end_ms"] = int(end.timestamp() * 1000) if end else 0
        out["now_ms"] = int(datetime.now(TR).timestamp() * 1000)
        out["offer"] = OFFER
        return out

    @api_router.get("/admin/campaigns")
    async def camp_list(me: dict = Depends(require_admin)):
        need_main()
        rs = await rows()
        c, end = pick(rs)
        now = datetime.now(TR)
        for r in rs:
            w = _at(r, now)
            s = _parse(r.get("start"))
            r["state"] = ("live" if c and r["id"] == c["id"] else "off" if not r.get("active", True) else "always" if r.get("always")
                          else "next" if s and s > now else "past")
        rs.sort(key=lambda r: (r.get("always", False), r.get("start") or ""))
        return {"campaigns": rs, "live": (c or {}).get("id"), "end": end.isoformat() if end else ""}

    @api_router.post("/admin/campaigns")
    async def camp_new(p: dict, me: dict = Depends(require_admin)):
        need_main()
        d = _clean(p)
        if not d.get("name") or not d.get("start") or not d.get("end"):
            raise HTTPException(422, "Ad, başlangıç ve bitiş gerekli")
        d.setdefault("badge_top", "KAMPANYA")
        d.update({"id": uuid.uuid4().hex[:10], "active": d.get("active", True), "yearly": d.get("yearly", False), "always": False})
        await main().site_campaigns.insert_one(dict(d))
        d.pop("_id", None)
        return d

    @api_router.put("/admin/campaigns/{cid}")
    async def camp_set(cid: str, p: dict, me: dict = Depends(require_admin)):
        need_main()
        d = _clean(p)
        cur = await main().site_campaigns.find_one({"id": cid})
        if not cur:
            raise HTTPException(404, "Kampanya bulunamadı")
        if cur.get("always"):
            d.pop("start", None)
            d.pop("end", None)
            d.pop("yearly", None)
        await main().site_campaigns.update_one({"id": cid}, {"$set": d})
        return {"ok": True}

    @api_router.delete("/admin/campaigns/{cid}")
    async def camp_del(cid: str, me: dict = Depends(require_admin)):
        need_main()
        cur = await main().site_campaigns.find_one({"id": cid})
        if not cur:
            raise HTTPException(404, "Kampanya bulunamadı")
        if cur.get("always"):
            raise HTTPException(422, "Sürekli kampanya silinemez; pasif yapabilirsiniz")
        await main().site_campaigns.delete_one({"id": cid})
        return {"ok": True}
