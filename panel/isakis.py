# -*- coding: utf-8 -*-
"""Sektörel iş akışları: servis formu, dava dosyası, muayene, iş emri, kursiyer.

Randevu her sektöre yetmez. Kombi servisi yapan usta cihazın marka, model ve seri
numarasını, yapılan işlemi, takılan parçayı ve müşterinin imzasını tutmak zorunda;
avukat dosya numarası, mahkeme, esas no ve duruşma tarihiyle çalışır. Bunlar aynı
ekranın farklı adları değil, farklı işlerdir.

Burada her akış **veri olarak** tanımlanıyor: adımları, alanları, imza isteyip
istemediği, çıktısının nasıl basılacağı. Panel bu tanımdan ekranı ve çıktıyı
kendisi kuruyor; yeni bir sektör geldiğinde tanım yazmak yetiyor.

İki kural:
* **Adım atlanmaz.** Her akışın kendi sırası var; imza isteyen akış, imza
  alınmadan "tamamlandı" durumuna geçmez.
* **Çıktı kaydın kendisinden üretilir.** Form ne diyorsa belge onu yazar; ayrıca
  elle doldurulan ikinci bir belge yoktur.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                                  # noqa: BLE001
    TR = timezone(timedelta(hours=3))


def F(key, label, typ="text", req=False, hint="", opt=(), col=False, max=0):
    return {"key": key, "label": label, "type": typ, "required": req, "hint": hint,
            "options": list(opt), "col": col, "max": max}


def A(aid, name, desc, steps, fields, sign, doc, sectors, parts=False, money=False):
    return {"id": aid, "name": name, "desc": desc, "steps": list(steps), "fields": fields,
            "sign": sign, "doc": doc, "sectors": list(sectors), "parts": parts, "money": money}


ADIM = {"yeni": "Kayıt açıldı", "yolda": "Yolda", "islemde": "İşlemde", "parca": "Parça bekliyor",
        "bitti": "Tamamlandı", "iptal": "İptal",
        "acik": "Açık", "durusma": "Duruşma bekliyor", "karar": "Karar aşaması", "kapandi": "Kapandı",
        "kayit": "Kayıt", "ders": "Ders aşaması", "sinav": "Sınav", "mezun": "Mezun",
        "muayene": "Muayene", "tedavi": "Tedavi", "kontrol": "Kontrol"}

FLOWS = [
    A("servis", "Servis formu", "Cihaz arızası, yapılan işlem ve müşteri imzası",
      ["yeni", "yolda", "islemde", "parca", "bitti", "iptal"],
      [F("cihaz", "Cihaz", req=True, col=True, hint="Kombi, klima, beyaz eşya…"),
       F("marka", "Marka", col=True), F("model", "Model"),
       F("seri", "Seri numarası", hint="Cihazın etiketinde yazar"),
       F("garanti", "Garanti durumu", "sel", opt=["Garantili", "Garanti dışı", "Bilinmiyor"], col=True),
       F("sikayet", "Müşteri şikâyeti", "area", req=True, max=1500),
       F("tespit", "Tespit edilen arıza", "area", max=1500),
       F("islem", "Yapılan işlem", "area", max=2000),
       F("oneri", "Öneri / sonraki bakım", "area", max=800),
       F("sonraki", "Sonraki bakım tarihi", "date")],
      sign=True, doc="servis", sectors=["teknik", "oto", "beyazesya"], parts=True, money=True),
    A("dosya", "Dava dosyası", "Mahkeme, esas numarası ve duruşma takibi",
      ["acik", "durusma", "karar", "kapandi", "iptal"],
      [F("dosya_no", "Dosya numarası", req=True, col=True),
       F("mahkeme", "Mahkeme", req=True, col=True),
       F("esas", "Esas numarası", col=True, hint="Örnek: 2026/1234"),
       F("tur", "Dava türü", "sel", opt=["Hukuk", "Ceza", "İcra", "İdare", "İş", "Aile", "Ticaret"], col=True),
       F("karsi", "Karşı taraf"), F("konu", "Konu", "area", req=True, max=2000),
       F("durusma", "Duruşma tarihi", "date", col=True),
       F("asama", "Son durum", "area", max=2000),
       F("vekalet", "Vekâlet ücreti", "num")],
      sign=False, doc="dosya", sectors=["avukat"], money=True),
    A("muayene", "Muayene kaydı", "Hasta, tanı, tedavi ve aşı takibi",
      ["muayene", "tedavi", "kontrol", "bitti"],
      [F("hasta", "Hasta adı", req=True, col=True, hint="Hayvanın adı ya da hastanın adı"),
       F("tur", "Tür / yaş", col=True), F("sikayet", "Şikâyet", "area", req=True, max=1200),
       F("bulgu", "Muayene bulgusu", "area", max=1500),
       F("tani", "Tanı", col=True, max=200), F("tedavi", "Uygulanan tedavi", "area", max=1500),
       F("recete", "Reçete", "area", max=1200),
       F("asi", "Yapılan aşı"), F("kontrol", "Kontrol tarihi", "date")],
      sign=False, doc="muayene", sectors=["veteriner", "saglik"], money=True),
    A("isemri", "İş emri", "Araç kabul, yapılan işlem ve teslim",
      ["yeni", "islemde", "parca", "bitti", "iptal"],
      [F("plaka", "Plaka", req=True, col=True), F("arac", "Araç", col=True),
       F("km", "Kilometre", "num"), F("sikayet", "Müşteri şikâyeti", "area", req=True, max=1500),
       F("islem", "Yapılan işlem", "area", max=2000),
       F("sonraki_km", "Sonraki bakım km", "num"), F("teslim", "Teslim tarihi", "date")],
      sign=True, doc="servis", sectors=["oto"], parts=True, money=True),
    A("kursiyer", "Kursiyer kaydı", "Ders, sınav ve evrak takibi",
      ["kayit", "ders", "sinav", "mezun", "iptal"],
      [F("sinif", "Sınıf", "sel", req=True, col=True, opt=["A1", "A2", "A", "B", "B1", "C", "D", "E", "F"]),
       F("tc", "TC kimlik numarası", col=True), F("saglik", "Sağlık raporu", "sel",
                                                  opt=["Alındı", "Eksik"], col=True),
       F("ders_teorik", "Teorik ders (saat)", "num"), F("ders_direksiyon", "Direksiyon (saat)", "num"),
       F("sinav1", "Teorik sınav tarihi", "date"), F("sinav2", "Direksiyon sınavı", "date"),
       F("not", "Not", "area", max=1200)],
      sign=False, doc="kursiyer", sectors=["surucu"], money=True),
]
BY_ID = {f["id"]: f for f in FLOWS}


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


def _int(v, d=0):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return d


def clean(fl, data, old=None):
    old = old or {}
    out = {}
    for f in fl["fields"]:
        k = f["key"]
        if k not in data and k in old:
            out[k] = old[k]
            continue
        v = data.get(k)
        if f["type"] == "area":
            v = _long(v, f["max"] or 2000)
        elif f["type"] == "num":
            v = _num(v)
        elif f["type"] == "date":
            v = _t(v, 10)
            if v and (len(v) != 10 or v[4] != "-"):
                raise HTTPException(422, "%s geçerli bir tarih olmalı" % f["label"])
        elif f["type"] == "sel":
            v = _t(v, 40)
            if v and f["options"] and v not in f["options"]:
                raise HTTPException(422, "%s için seçenek: %s" % (f["label"], ", ".join(f["options"])))
        else:
            v = _t(v, f["max"] or 160)
        if f["required"] and not v:
            raise HTTPException(422, "%s alanı gerekli" % f["label"])
        out[k] = v
    return out


def parcalar(v):
    out, toplam = [], 0.0
    for p in (v or [])[:60]:
        ad = _t((p or {}).get("name"), 120)
        if not ad:
            continue
        adet = max(_int(p.get("qty"), 1), 1)
        fiyat = _num(p.get("price"))
        out.append({"name": ad, "code": _t(p.get("code"), 40), "qty": adet, "price": fiyat})
        toplam += adet * fiyat
    return out, round(toplam, 2)


def view(fl, r):
    r = dict(r)
    r["flow_name"] = fl["name"]
    r["step_name"] = ADIM.get(r.get("step"), r.get("step", ""))
    r["next"] = [{"id": s, "name": ADIM.get(s, s)} for s in fl["steps"] if s != r.get("step")]
    _, pt = parcalar(r.get("parts"))
    r["parts_total"] = pt
    r["total"] = round(pt + _num(r.get("labor")), 2)
    r["signed"] = bool(r.get("sign"))
    return r


def register(api_router, db, deps):
    adm = deps["require_admin"]

    async def firma_akislari():
        d = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
        sec = d.get("sector")
        if not sec:
            s = await db.app_settings.find_one({"_id": "sector"}, {"_id": 0}) or {}
            sec = s.get("key") or ""
        return [f for f in FLOWS if sec in f["sectors"]], sec

    async def bul(fid, rid):
        fl = BY_ID.get(_t(fid, 20))
        if not fl:
            raise HTTPException(404, "İş akışı bulunamadı")
        r = await db.yp_isler.find_one({"id": _t(rid, 24), "flow": fl["id"]}, {"_id": 0})
        if not r:
            raise HTTPException(404, "Kayıt bulunamadı")
        return fl, r

    @api_router.get("/yp/is")
    async def akislar(_: dict = Depends(adm)):
        fls, sec = await firma_akislari()
        say = {}
        for r in await db.yp_isler.find({}, {"_id": 0, "flow": 1, "step": 1}).to_list(20000):
            d = say.setdefault(r["flow"], {"n": 0, "acik": 0})
            d["n"] += 1
            if r.get("step") not in ("bitti", "iptal", "kapandi", "mezun"):
                d["acik"] += 1
        return {"sector": sec, "flows": [dict({k: f[k] for k in ("id", "name", "desc", "sign", "parts", "money")},
                                              steps=[{"id": s, "name": ADIM.get(s, s)} for s in f["steps"]],
                                              fields=f["fields"], **say.get(f["id"], {"n": 0, "acik": 0}))
                                         for f in fls]}

    @api_router.get("/yp/is/{fid}")
    async def liste(fid: str, q: str = "", step: str = "", _: dict = Depends(adm)):
        fl = BY_ID.get(_t(fid, 20))
        if not fl:
            raise HTTPException(404, "İş akışı bulunamadı")
        rows = await db.yp_isler.find({"flow": fl["id"]}, {"_id": 0}).to_list(5000)
        qq = _t(q, 60).lower()
        if qq:
            rows = [r for r in rows if qq in " ".join(str(v) for v in r.values()).lower()]
        if step:
            rows = [r for r in rows if r.get("step") == step]
        rows.sort(key=lambda r: r.get("at") or "", reverse=True)
        allr = await db.yp_isler.find({"flow": fl["id"]}, {"_id": 0, "step": 1}).to_list(5000)
        return {"flow": dict(fl, steps=[{"id": s, "name": ADIM.get(s, s)} for s in fl["steps"]]),
                "items": [view(fl, r) for r in rows],
                "counts": dict({s: len([r for r in allr if r.get("step") == s]) for s in fl["steps"]},
                               hepsi=len(allr))}

    @api_router.post("/yp/is/{fid}")
    async def ekle(fid: str, payload: dict, _: dict = Depends(adm)):
        fl = BY_ID.get(_t(fid, 20))
        if not fl:
            raise HTTPException(404, "İş akışı bulunamadı")
        ad = _t((payload.get("customer") or {}).get("name"), 90)
        if not ad:
            raise HTTPException(422, "Müşteri adı gerekli")
        d = clean(fl, payload.get("data") or {})
        pl, pt = parcalar(payload.get("parts")) if fl["parts"] else ([], 0.0)
        n = await db.yp_isler.count_documents({"flow": fl["id"]})
        r = {"id": uuid.uuid4().hex[:12], "flow": fl["id"],
             "no": "%s-%s-%04d" % (fl["id"][:3].upper(), _now()[:4], n + 1),
             "customer": {"name": ad, "phone": "".join(ch for ch in str((payload.get("customer") or {}).get("phone") or "")
                                                       if ch.isdigit())[-11:],
                          "address": _t((payload.get("customer") or {}).get("address"), 300)},
             "data": d, "parts": pl, "labor": _num(payload.get("labor")) if fl["money"] else 0.0,
             "step": fl["steps"][0], "staff": _t(payload.get("staff"), 60),
             "sign": "", "at": _now(), "timeline": [{"at": _now(), "step": fl["steps"][0], "note": "kayıt açıldı"}]}
        await db.yp_isler.insert_one(dict(r))
        return {"ok": True, "item": view(fl, r)}

    @api_router.put("/yp/is/{fid}/{rid}")
    async def guncelle(fid: str, rid: str, payload: dict, _: dict = Depends(adm)):
        fl, old = await bul(fid, rid)
        st = {"at2": _now()}
        if "data" in payload:
            st["data"] = clean(fl, payload["data"], old.get("data"))
        if "parts" in payload and fl["parts"]:
            st["parts"], _pt = parcalar(payload["parts"])
        if "labor" in payload and fl["money"]:
            st["labor"] = _num(payload["labor"])
        if "staff" in payload:
            st["staff"] = _t(payload["staff"], 60)
        if "customer" in payload:
            c = dict(old.get("customer") or {})
            for k, n in (("name", 90), ("phone", 20), ("address", 300)):
                if k in payload["customer"]:
                    c[k] = _t(payload["customer"][k], n)
            st["customer"] = c
        await db.yp_isler.update_one({"id": old["id"]}, {"$set": st})
        return {"ok": True, "item": view(fl, dict(old, **st))}

    @api_router.post("/yp/is/{fid}/{rid}/adim")
    async def adim(fid: str, rid: str, payload: dict, _: dict = Depends(adm)):
        fl, r = await bul(fid, rid)
        yeni = _t(payload.get("step"), 20)
        if yeni not in fl["steps"]:
            raise HTTPException(422, "Bu akışta böyle bir adım yok")
        bitis = ("bitti", "kapandi", "mezun")
        if yeni in bitis and fl["sign"] and not r.get("sign"):
            raise HTTPException(422, "Önce müşteri imzasını alın; imzasız form tamamlanmış sayılmaz")
        st = {"step": yeni, "at2": _now()}
        await db.yp_isler.update_one({"id": r["id"]}, {"$set": st, "$push": {"timeline": {
            "at": _now(), "step": yeni, "note": _t(payload.get("note"), 200) or ADIM.get(yeni, yeni)}}})
        return {"ok": True, "item": view(fl, await db.yp_isler.find_one({"id": r["id"]}, {"_id": 0}))}

    @api_router.post("/yp/is/{fid}/{rid}/imza")
    async def imza(fid: str, rid: str, payload: dict, _: dict = Depends(adm)):
        fl, r = await bul(fid, rid)
        if not fl["sign"]:
            raise HTTPException(422, "Bu akış imza istemiyor")
        im = str(payload.get("sign") or "")
        if not im.startswith("data:image/png;base64,") or len(im) < 80:
            raise HTTPException(422, "İmza alınamadı; müşteriye ekrana imzalatın")
        if len(im) > 400000:
            raise HTTPException(422, "İmza çok büyük")
        st = {"sign": im, "sign_at": _now(), "sign_by": _t(payload.get("by"), 90) or (r.get("customer") or {}).get("name", "")}
        await db.yp_isler.update_one({"id": r["id"]}, {"$set": st})
        return {"ok": True, "item": view(fl, dict(r, **st))}

    @api_router.delete("/yp/is/{fid}/{rid}")
    async def sil(fid: str, rid: str, _: dict = Depends(adm)):
        fl, r = await bul(fid, rid)
        await db.yp_isler.delete_one({"id": r["id"]})
        return {"ok": True}

    @api_router.post("/yp/is/{fid}/{rid}/belge")
    async def belge(fid: str, rid: str, _: dict = Depends(adm)):
        fl, r = await bul(fid, rid)
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        return {"ok": True, "html": belge_html(fl, view(fl, r), g.get("company_name") or "")}

    return api_router


def _tel(v):
    d = "".join(ch for ch in str(v or "") if ch.isdigit())
    return "%s %s %s %s" % (d[:4], d[4:7], d[7:9], d[9:]) if len(d) == 11 else (v or "")


def _e(v):
    return str(v or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def belge_html(fl, r, firma=""):
    """Kaydın kendisinden üretilen, yazdırmaya hazır belge."""
    c = r.get("customer") or {}
    satir = []
    for f in fl["fields"]:
        v = (r.get("data") or {}).get(f["key"])
        if v in (None, "", 0):
            continue
        satir.append("<tr><th>%s</th><td>%s</td></tr>"
                     % (_e(f["label"]), _e(v).replace("\n", "<br>")))
    par = ""
    if fl["parts"] and r.get("parts"):
        par = ("<h3>Kullanılan parçalar</h3><table class='p'><tr><th>Parça</th><th>Kod</th>"
               "<th class='r'>Adet</th><th class='r'>Tutar</th></tr>%s</table>"
               % "".join("<tr><td>%s</td><td>%s</td><td class='r'>%d</td><td class='r'>%s ₺</td></tr>"
                         % (_e(p["name"]), _e(p.get("code")), p["qty"], ("%g" % (p["qty"] * p["price"])))
                         for p in r["parts"]))
    para = ""
    if fl["money"]:
        para = ("<div class='tt'><div><span>Parça</span><span>%g ₺</span></div>"
                "<div><span>İşçilik</span><span>%g ₺</span></div>"
                "<div class='b'><span>Toplam</span><span>%g ₺</span></div></div>"
                % (r.get("parts_total", 0), r.get("labor", 0), r.get("total", 0)))
    imza = ""
    if fl["sign"]:
        imza = ("<div class='sg2'><div><div class='lbl'>Müşteri imzası</div>%s"
                "<div class='nm'>%s</div></div><div><div class='lbl'>Yetkili</div>"
                "<div class='ln2'></div><div class='nm'>%s</div></div></div>"
                % (("<img src='%s' alt='imza'>" % _e(r.get("sign"))) if r.get("sign")
                   else "<div class='ln2'></div>",
                   _e(r.get("sign_by") or c.get("name")), _e(r.get("staff") or firma)))
    css = ("@page{size:A4;margin:12mm}*{box-sizing:border-box}"
           "body{font:13px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#101828;margin:0}"
           ".hd{display:flex;justify-content:space-between;align-items:flex-start;"
           "border-bottom:2px solid #101828;padding-bottom:9px;margin-bottom:12px}"
           ".hd h1{font-size:18px;margin:0}.no{font:700 15px ui-monospace,Menlo,monospace}"
           ".mus{border:1px solid #d0d5dd;border-radius:8px;padding:10px 12px;margin-bottom:12px}"
           ".mus b{font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:#667085;display:block;margin-bottom:4px}"
           "table{width:100%;border-collapse:collapse;margin-bottom:10px}"
           "th{text-align:left;color:#667085;font-weight:600;width:180px;vertical-align:top;"
           "padding:7px 8px 7px 0;border-bottom:1px solid #eaecf0;font-size:12px}"
           "td{padding:7px 0;border-bottom:1px solid #eaecf0;vertical-align:top}"
           "table.p th{width:auto;text-transform:uppercase;font-size:11px}.r{text-align:right}"
           "h3{font-size:13px;margin:14px 0 6px}"
           ".tt{margin-left:auto;width:48%;margin-top:6px}"
           ".tt div{display:flex;justify-content:space-between;padding:3px 0}"
           ".tt .b{font-weight:700;border-top:1px solid #101828;margin-top:4px;padding-top:6px}"
           ".sg2{display:flex;gap:30px;margin-top:26px}.sg2>div{flex:1;text-align:center}"
           ".sg2 .lbl{font-size:11px;color:#667085;text-transform:uppercase;letter-spacing:.05em}"
           ".sg2 img{height:70px;max-width:100%;object-fit:contain;display:block;margin:4px auto 0}"
           ".sg2 .ln2{height:70px;border-bottom:1px solid #98a2b3;margin-bottom:4px}"
           ".sg2 .nm{font-size:12px;margin-top:4px;border-top:1px solid #98a2b3;padding-top:4px}"
           ".ft4{margin-top:18px;font-size:11px;color:#667085;border-top:1px solid #eaecf0;padding-top:8px}")
    return ("<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>%s</title><style>%s</style></head>"
            "<body><div class='hd'><div><h1>%s</h1><div style='color:#667085;font-size:12px'>%s</div></div>"
            "<div style='text-align:right'><div class='no'>%s</div>"
            "<div style='color:#667085;font-size:12px'>%s</div></div></div>"
            "<div class='mus'><b>Müşteri</b>%s<br>%s%s</div>"
            "<table>%s</table>%s%s%s"
            "<div class='ft4'>Bu belge %s tarafından düzenlenmiştir.</div>"
            "<script>window.onload=function(){setTimeout(function(){window.print()},250)}</script>"
            "</body></html>"
            % (_e(fl["name"]), css, _e(fl["name"]), _e(firma), _e(r.get("no")),
               _e(str(r.get("at") or "")[:16].replace("T", " ")),
               _e(c.get("name")), _e(_tel(c.get("phone"))),
               ("<br>" + _e(c.get("address"))) if c.get("address") else "",
               "".join(satir), par, para, imza, _e(firma)))
