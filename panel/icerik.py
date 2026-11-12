# -*- coding: utf-8 -*-
"""İçerik motoru: yorum, blog, SSS, story, duyuru, referans, şube… tek yerden yönetilir.

Panelde kırk küsur bölüm yönetim ekranı istiyor. Her biri için ayrı ekran yazmak
hem uzun sürer hem de her yeni bölümde aynı işi tekrar ettirir. Onun yerine içerik
türünü **veri** olarak tanımlıyoruz: alanlar, liste sütunları, sıralama, onay
gerekip gerekmediği. Panel bu tanımdan hem listeyi hem formu kendisi kuruyor.
Yeni bir bölüm eklendiğinde buraya birkaç satır tanım yazmak yetiyor.

İki kural:

* **Onay gerektiren içerik yayına kendiliğinden çıkmaz.** Müşteri yorumu ve
  başvurular önce bekleyenlere düşer; işletme onaylamadan sitede görünmez.
* **Sıra işletmenindir.** Her tür kendi sırasını taşır; sürükleyip bıraktığınızda
  sitede de o sırayla görünür.
"""
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))

FTYPES = ("text", "area", "num", "sw", "img", "imgs", "date", "sel", "link", "puan")


def F(key, label, typ="text", req=False, hint="", opt=(), max=0, col=False):
    return {"key": key, "label": label, "type": typ, "required": req, "hint": hint,
            "options": list(opt), "max": max, "col": col}


def T(tid, name, desc, fields, blocks, module="", moderate=False, order=True, icon="",
      sort="order", empty=""):
    return {"id": tid, "name": name, "desc": desc, "fields": fields, "blocks": list(blocks),
            "module": module, "moderate": moderate, "order": order, "icon": icon,
            "sort": sort, "empty": empty}


TYPES = [
    T("yorum", "Müşteri yorumları", "Sitede görünen yorumlar; onaylamadan yayına çıkmaz",
      [F("name", "Müşteri adı", req=True, col=True), F("rating", "Puan", "puan", col=True),
       F("text", "Yorum", "area", req=True, max=1200, col=True),
       F("service", "Hizmet / ürün", hint="İsteğe bağlı"),
       F("photo", "Fotoğraf", "img", hint="Müşterinin eklediği fotoğraf"),
       F("reply", "İşletme yanıtı", "area", max=600),
       F("date", "Tarih", "date")],
      ["yorumlar", "yildiz_ozet", "video_yorum"], moderate=True, icon="star",
      empty="Henüz yorum yok. Müşteriler siteden yazdıkça burada onayınızı bekler."),
    T("blog", "Blog yazıları", "Site blog bölümünde görünür",
      [F("title", "Başlık", req=True, col=True), F("summary", "Özet", "area", max=300, col=True),
       F("body", "Yazı", "area", req=True, max=20000),
       F("cover", "Kapak görseli", "img"), F("author", "Yazar"),
       F("date", "Yayın tarihi", "date", col=True), F("tags", "Etiketler", hint="Virgülle ayırın")],
      ["blog"], icon="doc", empty="İlk yazınızı ekleyin; blog bölümü sitede otomatik dolar."),
    T("sss", "Sık sorulanlar", "Site SSS bölümünde görünür",
      [F("q", "Soru", req=True, col=True), F("a", "Cevap", "area", req=True, max=2000, col=True),
       F("group", "Küme", hint="Örnek: Kargo, Ödeme, İade")],
      ["sss"], icon="help", empty="Müşterilerin en çok sorduğu üç soruyla başlayın."),
    T("story", "Hikâyeler", "Sitenin üstünde yuvarlak hikâye balonları",
      [F("title", "Başlık", req=True, col=True), F("cover", "Kapak", "img", req=True),
       F("images", "Kareler", "imgs", hint="Sırayla gösterilir"),
       F("link", "Bağlantı", "link", hint="Tıklayınca gideceği yer"),
       F("until", "Bitiş tarihi", "date", hint="Boşsa süresiz")],
      ["story"], icon="circle", empty="Hikâye ekleyin; sitenizin üstünde yuvarlak balonlar görünür."),
    T("duyuru", "Duyuru çubuğu", "Sitenin en üstünde ince şerit",
      [F("text", "Metin", req=True, col=True, max=160),
       F("link", "Bağlantı", "link"), F("color", "Renk", "sel", opt=["koyu", "yesil", "turuncu", "kirmizi"]),
       F("until", "Bitiş tarihi", "date", col=True)],
      ["duyuru_bar"], icon="bell", empty="Kargo, kampanya ya da tatil duyurusu ekleyin."),
    T("referans", "Referanslar", "Çalıştığınız firmalar ve markalar",
      [F("name", "Firma adı", req=True, col=True), F("logo", "Logo", "img"),
       F("link", "Bağlantı", "link"), F("note", "Not", max=200)],
      ["referans", "markalar", "logo_akis"], icon="store", empty="Logolarıyla birlikte ekleyin."),
    T("vaka", "Vaka / proje", "Yaptığınız işler",
      [F("title", "Başlık", req=True, col=True), F("summary", "Özet", "area", max=400, col=True),
       F("images", "Görseller", "imgs"), F("result", "Sonuç", max=200, col=True),
       F("link", "Bağlantı", "link")],
      ["vaka", "once_sonra"], icon="doc", empty="Bir işinizi öncesi ve sonrasıyla anlatın."),
    T("sertifika", "Belgeler ve sertifikalar", "Yetki belgeleriniz",
      [F("name", "Belge adı", req=True, col=True), F("image", "Görsel", "img"),
       F("year", "Yıl", "num", col=True), F("by", "Veren kurum", col=True)],
      ["sertifika", "guven_rozet"], icon="check", empty="Yetki belgelerinizi ekleyin, güven verir."),
    T("basin", "Basında biz", "Hakkınızda çıkan haberler",
      [F("title", "Başlık", req=True, col=True), F("source", "Yayın", col=True),
       F("date", "Tarih", "date", col=True), F("link", "Bağlantı", "link"), F("logo", "Logo", "img")],
      ["basinda"], icon="doc", empty="Hakkınızda çıkan haberleri ekleyin."),
    T("kariyer", "İş ilanları", "Kariyer bölümünde görünür",
      [F("title", "Pozisyon", req=True, col=True), F("type", "Çalışma şekli", "sel",
                                                     opt=["Tam zamanlı", "Yarı zamanlı", "Dönemsel", "Stajyer"], col=True),
       F("city", "Şehir", col=True), F("body", "İlan metni", "area", req=True, max=6000),
       F("until", "Son başvuru", "date")],
      ["kariyer"], module="", icon="team", empty="Açık pozisyonunuzu yazın, başvurular gelen kutusuna düşer."),
    T("sube", "Şubeler", "Birden fazla adresiniz varsa",
      [F("name", "Şube adı", req=True, col=True), F("address", "Adres", "area", req=True, max=300, col=True),
       F("phone", "Telefon", col=True), F("hours", "Çalışma saatleri"),
       F("map", "Harita bağlantısı", "link")],
      ["subeler", "harita"], icon="pin", empty="Şubelerinizi ekleyin, haritada görünsün."),
    T("bolge", "Hizmet bölgeleri", "Hangi ilçelere gidiyorsunuz",
      [F("name", "Bölge", req=True, col=True), F("note", "Not", max=200, col=True),
       F("fee", "Ek ücret", "num", col=True)],
      ["bolgeler"], icon="pin", empty="Gittiğiniz ilçeleri yazın."),
    T("paket", "Paketler / kampanya kartları", "Fiyat ve paket bölümleri",
      [F("name", "Paket adı", req=True, col=True), F("price", "Fiyat", "num", col=True),
       F("old_price", "Eski fiyat", "num"), F("lines", "İçindekiler", "area", hint="Her satıra bir madde"),
       F("badge", "Rozet", hint="Örnek: En çok tercih edilen"), F("link", "Bağlantı", "link")],
      ["paketler", "fiyat_tablo", "hediye_ceki"], icon="tag", empty="Paketlerinizi fiyatlarıyla ekleyin."),
]
BY_ID = {t["id"]: t for t in TYPES}
VAR_OK = re.compile(r"^[a-z0-9_]+$")


def _now():
    return datetime.now(TR).replace(tzinfo=None).isoformat(timespec="seconds")


def _t(v, n):
    return " ".join(str(v or "").split())[:n]


def _long(v, n):
    return str(v or "").replace("\r", "")[:n].strip()


def _num(v, d=0.0):
    try:
        return round(float(str(v).replace(",", ".")), 2)
    except (TypeError, ValueError):
        return d


def clean(t, data, old=None):
    """Tür tanımına göre doğrula. Tanımda olmayan alan kaydedilmez."""
    old = old or {}
    out = {}
    for f in t["fields"]:
        k, typ = f["key"], f["type"]
        if k not in data and k in old:
            out[k] = old[k]
            continue
        v = data.get(k)
        if typ == "area":
            v = _long(v, f["max"] or 4000)
        elif typ == "num":
            v = _num(v)
        elif typ == "sw":
            v = bool(v)
        elif typ == "puan":
            v = max(min(int(_num(v, 5)), 5), 1)
        elif typ == "imgs":
            v = [_t(x, 400) for x in (v or []) if _t(x, 400)][:30]
        elif typ == "date":
            v = _t(v, 10)
            if v and not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                raise HTTPException(422, "%s geçerli bir tarih olmalı" % f["label"])
        elif typ == "link":
            v = _t(v, 400)
            if v and not re.match(r"^(https?://|/|#)", v):
                v = "https://" + v
        elif typ == "sel":
            v = _t(v, 60)
            if v and f["options"] and v not in f["options"]:
                raise HTTPException(422, "%s için seçenek: %s" % (f["label"], ", ".join(f["options"])))
        else:
            v = _t(v, f["max"] or 200)
        if f["required"] and not v:
            raise HTTPException(422, "%s alanı gerekli" % f["label"])
        out[k] = v
    return out


def view(t, r):
    r = dict(r)
    r["type_name"] = t["name"]
    r["state_name"] = {"onay": "Onay bekliyor", "red": "Reddedildi"}.get(r.get("state"), "Yayında" if r.get("on") else "Gizli")
    return r


def register(api_router, db, deps):
    adm = deps["require_admin"]

    async def firma_turleri():
        """Sektör paketindeki bölümlere göre hangi içerik türleri gerekiyor?"""
        d = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
        sec = d.get("sector")
        if not sec:
            s = await db.app_settings.find_one({"_id": "sector"}, {"_id": 0}) or {}
            sec = s.get("key") or ""
        bloklar, mods = set(), set(d.get("modules") or [])
        try:
            import blocks
            pk = blocks.pack(sec) or {}
            bloklar = set(pk.get("blocks") or [])
            if not mods:
                mods = set(pk.get("modules") or [])
            for b in await db.yp_pages.find({}, {"_id": 0, "blocks": 1}).to_list(400):
                for ins in b.get("blocks") or []:
                    bloklar.add(ins.get("bid"))
        except Exception:                                          # noqa: BLE001
            pass
        out = []
        for t in TYPES:
            if t["module"] and t["module"] not in mods:
                continue
            out.append(dict(t, used=bool(bloklar & set(t["blocks"]))))
        return out

    @api_router.get("/yp/content")
    async def turler(_: dict = Depends(adm)):
        ts = await firma_turleri()
        say = {}
        for r in await db.yp_content.find({}, {"_id": 0, "type": 1, "state": 1, "on": 1}).to_list(20000):
            d = say.setdefault(r["type"], {"n": 0, "onay": 0, "yayin": 0})
            d["n"] += 1
            if r.get("state") == "onay":
                d["onay"] += 1
            elif r.get("on"):
                d["yayin"] += 1
        return {"types": [dict({k: t[k] for k in ("id", "name", "desc", "icon", "moderate", "order",
                                                  "blocks", "used", "empty")},
                               **say.get(t["id"], {"n": 0, "onay": 0, "yayin": 0})) for t in ts]}

    @api_router.get("/yp/content/{tid}")
    async def liste(tid: str, q: str = "", state: str = "", _: dict = Depends(adm)):
        t = BY_ID.get(_t(tid, 30))
        if not t:
            raise HTTPException(404, "İçerik türü bulunamadı")
        rows = await db.yp_content.find({"type": t["id"]}, {"_id": 0}).to_list(5000)
        qq = _t(q, 60).lower()
        if qq:
            rows = [r for r in rows if qq in " ".join(str(v) for v in r.values()).lower()]
        if state == "onay":
            rows = [r for r in rows if r.get("state") == "onay"]
        elif state == "yayin":
            rows = [r for r in rows if r.get("on") and r.get("state") != "onay"]
        elif state == "gizli":
            rows = [r for r in rows if not r.get("on") and r.get("state") != "onay"]
        rows.sort(key=lambda r: (r.get("order", 0), r.get("at", "")))
        allr = await db.yp_content.find({"type": t["id"]}, {"_id": 0, "state": 1, "on": 1}).to_list(5000)
        return {"type": t, "items": [view(t, r) for r in rows],
                "counts": {"hepsi": len(allr),
                           "onay": len([r for r in allr if r.get("state") == "onay"]),
                           "yayin": len([r for r in allr if r.get("on") and r.get("state") != "onay"]),
                           "gizli": len([r for r in allr if not r.get("on") and r.get("state") != "onay"])}}

    @api_router.post("/yp/content/{tid}")
    async def ekle(tid: str, payload: dict, _: dict = Depends(adm)):
        t = BY_ID.get(_t(tid, 30))
        if not t:
            raise HTTPException(404, "İçerik türü bulunamadı")
        d = clean(t, payload.get("data") or payload)
        n = await db.yp_content.count_documents({"type": t["id"]})
        r = dict(d, id=uuid.uuid4().hex[:12], type=t["id"], order=n,
                 on=bool(payload.get("on", True)), state="", at=_now(), by="panel")
        await db.yp_content.insert_one(dict(r))
        return {"ok": True, "item": view(t, r)}

    @api_router.put("/yp/content/{tid}/{cid}")
    async def guncelle(tid: str, cid: str, payload: dict, _: dict = Depends(adm)):
        t = BY_ID.get(_t(tid, 30))
        if not t:
            raise HTTPException(404, "İçerik türü bulunamadı")
        old = await db.yp_content.find_one({"id": _t(cid, 24), "type": t["id"]}, {"_id": 0})
        if not old:
            raise HTTPException(404, "Kayıt bulunamadı")
        d = clean(t, payload.get("data") or payload, old)
        if "on" in payload:
            d["on"] = bool(payload["on"])
        d["at"] = _now()
        await db.yp_content.update_one({"id": old["id"]}, {"$set": d})
        return {"ok": True, "item": view(t, dict(old, **d))}

    @api_router.delete("/yp/content/{tid}/{cid}")
    async def sil(tid: str, cid: str, _: dict = Depends(adm)):
        r = await db.yp_content.delete_one({"id": _t(cid, 24), "type": _t(tid, 30)})
        if not r.deleted_count:
            raise HTTPException(404, "Kayıt bulunamadı")
        return {"ok": True}

    @api_router.post("/yp/content/{tid}/sira")
    async def sirala(tid: str, payload: dict, _: dict = Depends(adm)):
        t = BY_ID.get(_t(tid, 30))
        if not t:
            raise HTTPException(404, "İçerik türü bulunamadı")
        ids = [_t(x, 24) for x in (payload.get("ids") or [])]
        for i, cid in enumerate(ids):
            await db.yp_content.update_one({"id": cid, "type": t["id"]}, {"$set": {"order": i}})
        return {"ok": True, "n": len(ids)}

    @api_router.post("/yp/content/{tid}/{cid}/onay")
    async def onay(tid: str, cid: str, payload: dict, _: dict = Depends(adm)):
        t = BY_ID.get(_t(tid, 30))
        if not t:
            raise HTTPException(404, "İçerik türü bulunamadı")
        r = await db.yp_content.find_one({"id": _t(cid, 24), "type": t["id"]}, {"_id": 0})
        if not r:
            raise HTTPException(404, "Kayıt bulunamadı")
        karar = _t(payload.get("karar"), 10)
        if karar not in ("onay", "red"):
            raise HTTPException(422, "Karar onay veya red olmalı")
        st = {"state": "" if karar == "onay" else "red", "on": karar == "onay", "at": _now()}
        await db.yp_content.update_one({"id": r["id"]}, {"$set": st})
        return {"ok": True, "item": view(t, dict(r, **st))}

    @api_router.get("/public/yp/icerik")
    async def site_veri(t: str = "", limit: int = 50):
        """Sitenin kullandığı içerik: yalnız yayında olanlar, kendi sırasıyla.

        Tema bu uca bir kez sorar ve bölümleri doldurur. Onay bekleyen, reddedilen,
        gizlenen ve süresi geçmiş kayıtlar buradan dönmez.
        """
        ids = [_t(x, 30) for x in (t or "").split(",") if _t(x, 30) in BY_ID]
        if not ids:
            ids = list(BY_ID)
        out = {}
        for tid in ids[:20]:
            rows = await site_icerik(db, tid, min(max(limit, 1), 200))
            tt = BY_ID[tid]
            alanlar = {f["key"] for f in tt["fields"]}
            out[tid] = [{k: v for k, v in r.items() if k in alanlar or k == "id"} for r in rows]
        return {"ok": True, "items": out}

    # Siteden gelen yorum: önce onaya düşer
    @api_router.post("/public/yp/yorum")
    async def yorum_gelen(payload: dict):
        t = BY_ID["yorum"]
        d = clean(t, payload)
        n = await db.yp_content.count_documents({"type": "yorum"})
        r = dict(d, id=uuid.uuid4().hex[:12], type="yorum", order=n, on=False,
                 state="onay", at=_now(), by="site")
        await db.yp_content.insert_one(dict(r))
        return {"ok": True, "msg": "Yorumunuz alındı, onaylandıktan sonra yayınlanacak"}

    # ------------------------------------------------------------ QR menü
    @api_router.get("/yp/qr")
    async def qr_liste(_: dict = Depends(adm)):
        """Masa karekodları: kaç masa varsa o kadar kare, her biri kendi bağlantısına gider."""
        d = await db.app_settings.find_one({"_id": "yp_qr"}, {"_id": 0}) or {}
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        site = (g.get("site_url") or g.get("domain") or "onlinekaydet.com").rstrip("/")
        if not site.startswith("http"):
            site = "https://" + site
        n = max(min(int(d.get("tables") or 12), 200), 1)
        return {"ok": True, "tables": n, "base": site, "title": d.get("title") or "Menü",
                "note": d.get("note") or "Kareyi kamerayla okutun",
                "items": [{"no": i, "url": "%s/menu?masa=%d" % (site, i)} for i in range(1, n + 1)]}

    @api_router.put("/yp/qr")
    async def qr_ayar(payload: dict, _: dict = Depends(adm)):
        st = {"_id": "yp_qr", "tables": max(min(int(payload.get("tables") or 12), 200), 1),
              "title": _t(payload.get("title"), 60) or "Menü",
              "note": _t(payload.get("note"), 160) or "Kareyi kamerayla okutun", "at": _now()}
        await db.app_settings.update_one({"_id": "yp_qr"}, {"$set": st}, upsert=True)
        return {"ok": True}

    @api_router.post("/yp/qr/yazdir")
    async def qr_yazdir(payload: dict, _: dict = Depends(adm)):
        """Masa kartları: A4'e dört kart, kesilip masaya konur."""
        import qr as QR
        d = await qr_liste()
        secili = [int(x) for x in (payload.get("tables") or []) if str(x).isdigit()] or \
                 [x["no"] for x in d["items"]]
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        firma = g.get("company_name") or ""
        kart = []
        for it in d["items"]:
            if it["no"] not in secili:
                continue
            kart.append("<div class='k'><div class='b'>%s</div><div class='n'>%s</div>%s"
                        "<div class='m'>Masa %d</div><div class='u'>%s</div></div>"
                        % (_t(d["title"], 60), _t(d["note"], 160),
                           QR.svg(it["url"], px=5), it["no"],
                           it["url"].replace("https://", "")))
        css = ("@page{size:A4;margin:10mm}*{box-sizing:border-box}"
               "body{font:13px/1.45 -apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#101828;margin:0;"
               "display:grid;grid-template-columns:1fr 1fr;gap:8mm}"
               ".k{border:1px dashed #98a2b3;border-radius:10px;padding:8mm 6mm;text-align:center;"
               "page-break-inside:avoid}"
               ".k .b{font-size:17px;font-weight:700}.k .n{color:#667085;font-size:12px;margin:3px 0 8px}"
               ".k svg{display:block;margin:0 auto}"
               ".k .m{font-weight:700;margin-top:7px}.k .u{color:#667085;font-size:11px;margin-top:2px}")
        return {"ok": True, "n": len(kart),
                "html": ("<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
                         "<title>Masa karekodları — %s</title><style>%s</style></head><body>%s"
                         "<script>window.onload=function(){setTimeout(function(){window.print()},300)}</script>"
                         "</body></html>" % (firma, css, "".join(kart)))}

    @api_router.get("/yp/content/{tid}/bekleyen")
    async def bekleyen(tid: str, _: dict = Depends(adm)):
        t = BY_ID.get(_t(tid, 30))
        if not t:
            raise HTTPException(404, "İçerik türü bulunamadı")
        rows = await db.yp_content.find({"type": t["id"], "state": "onay"}, {"_id": 0}).to_list(500)
        rows.sort(key=lambda r: r.get("at") or "", reverse=True)
        return {"items": [view(t, r) for r in rows]}

    return api_router


async def site_icerik(db, tid, limit=50):
    """Sitede gösterilecek kayıtlar: yalnız yayında olanlar, kendi sırasıyla."""
    rows = await db.yp_content.find({"type": tid, "on": True, "state": {"$ne": "onay"}},
                                    {"_id": 0}).to_list(2000)
    rows.sort(key=lambda r: (r.get("order", 0), r.get("at", "")))
    bugun = _now()[:10]
    rows = [r for r in rows if not r.get("until") or r["until"] >= bugun]
    return rows[:limit]
