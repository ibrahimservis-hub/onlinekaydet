# -*- coding: utf-8 -*-
"""Sektör modülleri: tek altyapı, üç grup.
  kurs  : kursiyer kaydı + taksit + devamsızlık, programlar (sürücü kursu, dil, etüt, müzik, spor/yoga...)
  rez   : araç/salon/masa/tur kaynakları + rezervasyon, çakışma kontrolü, kapora (araç kiralama, düğün salonu, lokanta...)
  klinik: hasta dosyası + muayene notları + aşı/kontrol hatırlatması (diş, psikolog, diyetisyen, veteriner...)
Panel ekranı tek ve şema ile çalışır (GET /admin/mod/<anahtar>/schema). Herkese açık: /kurslar, /rezervasyon sayfaları."""
import base64
import re
import time
import uuid
from datetime import date, datetime, timedelta
from html import escape as E

from fastapi import Depends, HTTPException
from fastapi.responses import Response

SECTOR_MODULES = {
    "ilan": {"emlakci", "arac_kiralama", "transfer", "tur_organizasyon"},
    "kurs": {"surucu_kursu", "src_kursu", "etut_merkezi", "dil_okulu", "muzik_kursu", "anaokulu", "ozel_ders", "bilgisayar_kursu", "yuzme_kursu", "yoga_dans", "spor_salonu"},
    "rez": {"arac_kiralama", "dugun_salonu", "lokanta", "transfer", "tur_organizasyon", "spa_hamam"},
    "klinik": {"dis_klinigi", "psikolog", "diyetisyen", "fizyoterapi", "veteriner", "estetik_merkezi", "aile_danisman"},
}


def modules_for(key):
    return [m for m, s in SECTOR_MODULES.items() if key in s]


def F(k, l, t="text", **kw):
    return dict(k=k, l=l, t=t, **kw)


ST_KURSIYER = [("aktif", "Aktif"), ("mezun", "Mezun"), ("ayrildi", "Ayrıldı"), ("donduruldu", "Donduruldu")]
ST_REZ = [("bekliyor", "Bekliyor"), ("onaylandi", "Onaylandı"), ("tamamlandi", "Tamamlandı"), ("iptal", "İptal")]
KIND_RES = [("arac", "Araç"), ("salon", "Salon"), ("masa", "Masa"), ("oda", "Oda"), ("tur", "Tur"), ("diger", "Diğer")]

MODS = {
    "kursiyer": dict(
        title="Kursiyerler", coll="students", group="kurs", search=("name", "phone", "program"),
        fields=[F("name", "Ad soyad", req=1, max=80), F("phone", "Telefon", max=20), F("program", "Program / sınıf", max=80, ph="Örn. B sınıfı direksiyon, A2 İngilizce"),
                F("start", "Kayıt tarihi", "date"), F("fee", "Toplam ücret (₺)", "num"), F("status", "Durum", "select", opts=ST_KURSIYER),
                F("installments", "Taksitler", "rows", sub=[F("due", "Vade", "date"), F("amount", "Tutar (₺)", "num"), F("paid", "Ödendi", "bool")]),
                F("attendance", "Yoklama / devamsızlık", "rows", sub=[F("date", "Tarih", "date"), F("state", "Durum", "select", opts=[("geldi", "Geldi"), ("gelmedi", "Gelmedi"), ("izinli", "İzinli")]), F("note", "Not", max=80)]),
                F("note", "Not", "area", max=1000)],
        headers=["Kursiyer", "Program", "Kalan borç", "Geciken taksit", "Devamsızlık", "Durum"],
        filters=[("", "Tümü"), ("geciken", "Gecikmiş ödemesi olanlar"), ("devamsiz", "3+ devamsızlık"), ("aktif", "Aktif")]),
    "program": dict(
        title="Programlar", coll="programs", group="kurs", search=("title",), public=True,
        fields=[F("title", "Program adı", req=1, max=100), F("price", "Ücret (₺)", "num"), F("duration", "Süre", max=40, ph="Örn. 8 hafta"), F("schedule", "Gün / saat", max=80),
                F("description", "Açıklama", "area", max=2000), F("image", "Görsel", "img"), F("status", "Durum", "select", opts=[("yayinda", "Yayında"), ("taslak", "Taslak")])],
        headers=["Program", "Ücret", "Süre", "Durum"], filters=[("", "Tümü")]),
    "kaynak": dict(
        title="Araç / Salon / Masa", coll="resources", group="rez", search=("name",), public=True,
        fields=[F("name", "Ad", req=1, max=100, ph="Örn. Renault Clio, Büyük salon, 5 numaralı masa"), F("kind", "Tür", "select", opts=KIND_RES), F("price", "Günlük ücret (₺)", "num"),
                F("capacity", "Kapasite (kişi)", "num"), F("description", "Açıklama", "area", max=2000), F("image", "Görsel", "img"),
                F("status", "Durum", "select", opts=[("yayinda", "Yayında"), ("taslak", "Taslak")])],
        headers=["Kaynak", "Tür", "Günlük ücret", "Kapasite", "Durum"], filters=[("", "Tümü")]),
    "rezervasyon": dict(
        title="Rezervasyonlar", coll="bookings", group="rez", search=("name", "phone"),
        fields=[F("resource_id", "Kaynak", "ref", ref="kaynak", req=1), F("name", "Müşteri adı", req=1, max=80), F("phone", "Telefon", max=20), F("start", "Başlangıç", "date", req=1), F("end", "Bitiş", "date", req=1),
                F("guests", "Kişi sayısı", "num"), F("total", "Toplam tutar (₺)", "num"), F("deposit", "Kapora (₺)", "num"), F("deposit_paid", "Kapora alındı", "bool"),
                F("status", "Durum", "select", opts=ST_REZ), F("note", "Not", "area", max=1000)],
        headers=["Müşteri", "Kaynak", "Tarih", "Tutar", "Kapora", "Durum"],
        filters=[("", "Tümü"), ("bekliyor", "Onay bekleyenler"), ("yaklasan", "Önümüzdeki 7 gün"), ("kaporasiz", "Kaporası alınmamış")]),
    "hasta": dict(
        title="Hasta / müşteri dosyaları", coll="patients", group="klinik", search=("name", "phone", "animal"),
        fields=[F("name", "Ad soyad (veteriner için sahibi)", req=1, max=80), F("phone", "Telefon", max=20), F("birth", "Doğum tarihi", "date"), F("animal", "Hayvan adı / türü (veteriner)", max=60),
                F("kvkk", "KVKK aydınlatma / açık rıza alındı", "bool"), F("note", "Genel not", "area", max=2000),
                F("visits", "Muayene / seans notları", "rows", sub=[F("date", "Tarih", "date"), F("complaint", "Şikâyet", max=200), F("treatment", "Yapılan işlem / tanı", max=400), F("rx", "Reçete / öneri", max=300), F("next", "Sonraki kontrol", "date")]),
                F("vaccines", "Aşı / tekrar takibi", "rows", sub=[F("name", "Ad", max=80), F("date", "Tarih", "date"), F("next", "Sonraki", "date")])],
        headers=["Dosya", "Telefon", "Son ziyaret", "Yaklaşan kontrol", "Not"], filters=[("", "Tümü"), ("yaklasan", "30 gün içinde kontrolü olanlar"), ("kvkksiz", "KVKK onayı eksik")]),
}
ORDER = {"kurs": ["kursiyer", "program"], "rez": ["kaynak", "rezervasyon"], "klinik": ["hasta"]}
MAX_IMG_B64 = 900_000


def today():
    return date.today().isoformat()


def _d(v):
    v = str(v or "").strip()
    if not v:
        return ""
    try:
        datetime.strptime(v, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Tarih biçimi geçersiz")
    return v


def _num(v, hi=10 ** 9):
    try:
        x = float(str(v).replace(",", ".").replace(" ", ""))
    except ValueError:
        return 0
    return max(0, min(hi, x))


def clean_value(f, v):
    t = f["t"]
    if t == "text" or t == "area":
        return str(v or "").strip()[:f.get("max", 200)]
    if t == "num":
        return _num(v)
    if t == "date":
        return _d(v)
    if t == "bool":
        return bool(v)
    if t == "select":
        ok = {o[0] for o in f["opts"]}
        return v if v in ok else f["opts"][0][0]
    if t == "ref":
        return str(v or "")[:60]
    if t == "img":
        v = str(v or "")
        if not v:
            return ""
        if not v.startswith("data:image/") or ";base64," not in v:
            return ""
        if len(v) > MAX_IMG_B64:
            raise ValueError("Görsel çok büyük (en fazla ~600 KB)")
        return v
    if t == "rows":
        out = []
        for r in (v or [])[:200]:
            if not isinstance(r, dict):
                continue
            row = {s["k"]: clean_value(s, r.get(s["k"])) for s in f["sub"]}
            if any(row.get(s["k"]) not in ("", 0, False, None) for s in f["sub"]):
                out.append(row)
        return out
    return v


def clean(mod, p, partial=False):
    out = {}
    for f in mod["fields"]:
        if f["k"] not in p and partial:
            continue
        v = clean_value(f, p.get(f["k"]))
        if f.get("req") and not v:
            raise ValueError("%s zorunlu" % f["l"])
        out[f["k"]] = v
    return out


# ---------------------------------------------------------------- hesaplanan alanlar (liste sütunları, filtreler, özetler)
def _fmt(n):
    return "{:,.0f}".format(n or 0).replace(",", ".") + " ₺"


def student_stats(r):
    t = today()
    ins = r.get("installments") or []
    unpaid = [i for i in ins if not i.get("paid")]
    bal = sum(i.get("amount") or 0 for i in unpaid)
    over = [i for i in unpaid if i.get("due") and i["due"] < t]
    absent = sum(1 for a in (r.get("attendance") or []) if a.get("state") == "gelmedi")
    return bal, len(over), absent, sum(i.get("amount") or 0 for i in over)


def booking_dates(r):
    return "%s → %s" % (r.get("start") or "?", r.get("end") or "?")


def next_check(r):
    t = today()
    ds = [v.get("next") for v in (r.get("visits") or []) + (r.get("vaccines") or []) if v.get("next") and v["next"] >= t]
    return min(ds) if ds else ""


def last_visit(r):
    ds = [v.get("date") for v in (r.get("visits") or []) if v.get("date")]
    return max(ds) if ds else ""


def row_cols(key, r, names=None):
    if key == "kursiyer":
        bal, over, absn, _ = student_stats(r)
        return [r.get("name"), r.get("program") or "", _fmt(bal) if bal else "—", ("%d adet" % over) if over else "—", ("%d gün" % absn) if absn else "—", dict(ST_KURSIYER).get(r.get("status"), "")]
    if key == "program":
        return [r.get("title"), _fmt(r.get("price")) if r.get("price") else "—", r.get("duration") or "—", "Yayında" if r.get("status") == "yayinda" else "Taslak"]
    if key == "kaynak":
        return [r.get("name"), dict(KIND_RES).get(r.get("kind"), ""), _fmt(r.get("price")) if r.get("price") else "—", ("%g kişi" % r["capacity"]) if r.get("capacity") else "—", "Yayında" if r.get("status") == "yayinda" else "Taslak"]
    if key == "rezervasyon":
        return [r.get("name"), (names or {}).get(r.get("resource_id"), "—"), booking_dates(r), _fmt(r.get("total")) if r.get("total") else "—",
                ("Alındı" if r.get("deposit_paid") else "Bekliyor") + (" · " + _fmt(r["deposit"]) if r.get("deposit") else "") if r.get("deposit") else "—", dict(ST_REZ).get(r.get("status"), "")]
    if key == "hasta":
        return [r.get("name") + ((" · " + r["animal"]) if r.get("animal") else ""), r.get("phone") or "—", last_visit(r) or "—", next_check(r) or "—", (r.get("note") or "")[:50]]
    return []


def keep(key, r, flt):
    if not flt:
        return True
    t = today()
    if key == "kursiyer":
        bal, over, absn, _ = student_stats(r)
        return (flt == "geciken" and over > 0) or (flt == "devamsiz" and absn >= 3) or (flt == "aktif" and r.get("status") == "aktif")
    if key == "rezervasyon":
        end7 = (date.today() + timedelta(days=7)).isoformat()
        return (flt == "bekliyor" and r.get("status") == "bekliyor") or (flt == "yaklasan" and r.get("status") in ("bekliyor", "onaylandi") and t <= (r.get("start") or "") <= end7) or (flt == "kaporasiz" and r.get("deposit") and not r.get("deposit_paid") and r.get("status") != "iptal")
    if key == "hasta":
        n = next_check(r)
        end30 = (date.today() + timedelta(days=30)).isoformat()
        return (flt == "yaklasan" and n and n <= end30) or (flt == "kvkksiz" and not r.get("kvkk"))
    return True


def summary(key, rows):
    t = today()
    if key == "kursiyer":
        bal = sum(student_stats(r)[0] for r in rows); over = sum(student_stats(r)[3] for r in rows)
        return [["Aktif kursiyer", sum(1 for r in rows if r.get("status") == "aktif")], ["Kalan toplam borç", _fmt(bal)], ["Geciken tahsilat", _fmt(over)], ["Gecikmiş ödemesi olan", sum(1 for r in rows if student_stats(r)[1])]]
    if key == "rezervasyon":
        end7 = (date.today() + timedelta(days=7)).isoformat()
        return [["Onay bekleyen", sum(1 for r in rows if r.get("status") == "bekliyor")], ["7 gün içinde", sum(1 for r in rows if r.get("status") in ("bekliyor", "onaylandi") and t <= (r.get("start") or "") <= end7)],
                ["Bugün başlayan", sum(1 for r in rows if r.get("status") == "onaylandi" and r.get("start") == t)], ["Alınmamış kapora", _fmt(sum(r.get("deposit") or 0 for r in rows if not r.get("deposit_paid") and r.get("status") in ("bekliyor", "onaylandi")))]]
    if key == "hasta":
        end30 = (date.today() + timedelta(days=30)).isoformat()
        return [["Toplam dosya", len(rows)], ["30 gün içinde kontrol", sum(1 for r in rows if next_check(r) and next_check(r) <= end30)], ["KVKK onayı eksik", sum(1 for r in rows if not r.get("kvkk"))]]
    return [["Kayıt", len(rows)]]


# ---------------------------------------------------------------- çakışma kontrolü
async def check_booking(db, row, bid=None):
    if row["status"] != "onaylandi":
        return
    if row["end"] < row["start"]:
        raise ValueError("Bitiş tarihi başlangıçtan önce olamaz")
    q = {"resource_id": row["resource_id"], "status": "onaylandi", "start": {"$lte": row["end"]}, "end": {"$gte": row["start"]}}
    if bid:
        q["id"] = {"$ne": bid}
    other = await db.bookings.find_one(q, {"_id": 0})
    if other:
        raise ValueError("Bu kaynak %s – %s tarihlerinde dolu (onaylı rezervasyon var)" % (other["start"], other["end"]))


async def free(db, rid, start, end):
    q = {"resource_id": rid, "status": "onaylandi", "start": {"$lte": end}, "end": {"$gte": start}}
    return await db.bookings.find_one(q, {"_id": 0}) is None


# ---------------------------------------------------------------- herkese açık sayfalar
def pub_css():
    import ilan
    return ilan.CSS


def kurslar_body(items):
    cards = "".join('<div class="cd"><div class="im">%s</div><div class="in"><h3>%s</h3><div class="pr">%s</div><div class="mt">%s</div><p style="font-size:.9rem;line-height:1.55;white-space:pre-line">%s</p></div></div>' % (
        ('<img loading="lazy" alt="%s" src="/api/public/mod-img/programs/%s">' % (E(i["title"]), E(i["id"]))) if i.get("has_img") else "", E(i["title"]), _fmt(i["price"]) if i.get("price") else "Fiyat için arayın",
        "".join("<span>%s</span>" % E(x) for x in (i.get("duration"), i.get("schedule")) if x), E(i.get("description") or "")) for i in items)
    return pub_css() + '<section class="okl"><div class="w"><h1>Programlarımız</h1><p class="sub">Programlarımız ve ücretleri. Kayıt için bize ulaşın ya da online randevu alın.</p>%s<div class="ct" style="margin-top:22px"><a class="b1" href="/#randevu">Kayıt için randevu al</a></div></div></section>' % (
        ('<div class="g">%s</div>' % cards) if cards else '<div class="em">Şu an yayında program yok.</div>')


def rezervasyon_body(items):
    cards = "".join('<div class="cd"><div class="im">%s</div><div class="in"><h3>%s</h3><div class="pr">%s</div><div class="mt">%s</div><p style="font-size:.9rem;line-height:1.55;white-space:pre-line">%s</p></div></div>' % (
        ('<img loading="lazy" alt="%s" src="/api/public/mod-img/resources/%s">' % (E(i["name"]), E(i["id"]))) if i.get("has_img") else "", E(i["name"]), (_fmt(i["price"]) + " / gün") if i.get("price") else "Fiyat için arayın",
        "".join("<span>%s</span>" % E(x) for x in (dict(KIND_RES).get(i.get("kind")), ("%g kişilik" % i["capacity"]) if i.get("capacity") else "") if x), E(i.get("description") or "")) for i in items)
    opts = "".join('<option value="%s">%s</option>' % (E(i["id"]), E(i["name"])) for i in items)
    form = ('<form id="okr-f" class="okr"><h2>Rezervasyon talebi</h2><label>Seçim<select name="resource_id" required>%s</select></label><div class="two"><label>Başlangıç<input type="date" name="start" required></label><label>Bitiş<input type="date" name="end" required></label></div>'
            '<div class="two"><label>Ad soyad<input name="name" required maxlength="80" autocomplete="name"></label><label>Telefon<input name="phone" required type="tel" maxlength="20" autocomplete="tel"></label></div>'
            '<label>Kişi sayısı<input type="number" name="guests" min="1" max="500"></label><label>Not<textarea name="note" rows="2" maxlength="500"></textarea></label>'
            '<div id="okr-m" role="status"></div><button class="b1" type="submit" style="border:0;cursor:pointer;width:100%%">Talebi gönder</button><p style="font-size:.8rem;color:var(--mut)">Talebiniz onaylandığında sizinle iletişime geçilir.</p></form>') % opts
    css = ('<style>.okr{margin-top:30px;max-width:640px;border:1px solid var(--ln);border-radius:var(--r,12px);padding:20px;background:var(--fbg,#fff);display:grid;gap:12px}.okr h2{margin:0;font:800 1.3rem var(--fd,inherit)}.okr label{display:grid;gap:5px;font:700 .82rem var(--fb,inherit)}'
           '.okr input,.okr select,.okr textarea{min-height:46px;padding:10px 12px;border:1px solid var(--ln);border-radius:8px;background:transparent;color:inherit;font:500 .95rem var(--fb,inherit);width:100%}.okr .two{display:grid;grid-template-columns:1fr 1fr;gap:10px}#okr-m{font-weight:700;font-size:.9rem}</style>')
    js = ('<script>(function(){var f=document.getElementById("okr-f");if(!f)return;var m=document.getElementById("okr-m"),t=new Date().toISOString().slice(0,10);f.start.min=t;f.end.min=t;'
          'function chk(){if(!f.start.value||!f.end.value||f.end.value<f.start.value)return;fetch("/api/public/availability?resource="+encodeURIComponent(f.resource_id.value)+"&start="+f.start.value+"&end="+f.end.value).then(function(r){return r.json()}).then(function(j){m.style.color=j.free?"#15803d":"#b91c1c";m.textContent=j.free?"Bu tarihler müsait.":"Bu tarihlerde dolu görünüyor, başka tarih seçin."}).catch(function(){})}'
          '["start","end","resource_id"].forEach(function(n){f[n].addEventListener("change",chk)});'
          'f.addEventListener("submit",function(e){e.preventDefault();var b=f.querySelector("button");b.disabled=true;var o={};[].forEach.call(new FormData(f).entries(),function(p){o[p[0]]=p[1]});'
          'fetch("/api/public/bookings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(o)}).then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error(typeof j.detail==="string"?j.detail:"Gönderilemedi");return j})}).then(function(){m.style.color="#15803d";m.textContent="Talebiniz alındı. En kısa sürede dönüş yapacağız.";f.reset()}).catch(function(x){m.style.color="#b91c1c";m.textContent=x.message}).then(function(){b.disabled=false})})})();</script>')
    return pub_css() + css + '<section class="okl"><div class="w"><h1>Rezervasyon</h1><p class="sub">Seçeneklerimizi inceleyin, tarih seçip talebinizi gönderin.</p>%s%s</div></section>%s' % (
        ('<div class="g">%s</div>' % cards) if cards else '<div class="em">Şu an rezervasyona açık seçenek yok.</div>', form if items else "", js)


async def public_items(db, coll):
    rows = await getattr(db, coll).find({"status": "yayinda"}, {"_id": 0}).sort("created_at", -1).to_list(300)
    for r in rows:
        r["has_img"] = bool(r.pop("image", ""))
    return rows


SITE_LINKS = [("ilan", "/ilanlar", "İlanlar"), ("kurs", "/kurslar", "Programlar"), ("rez", "/rezervasyon", "Rezervasyon")]


def site_links(sector):
    return [(h, l) for m, h, l in SITE_LINKS if sector in SECTOR_MODULES[m]]


# ---------------------------------------------------------------- uçlar
def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    def mod_of(key):
        m = MODS.get(key)
        if not m:
            raise HTTPException(404, "Modül bulunamadı")
        return m

    def schema_of(m):
        return {"title": m["title"], "fields": m["fields"], "headers": m["headers"], "filters": m["filters"], "public": bool(m.get("public"))}

    async def names():
        rs = await db.resources.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(2000)
        return {r["id"]: r["name"] for r in rs}

    @api_router.get("/admin/mod/{key}/schema")
    async def m_schema(key: str, _: dict = Depends(require_admin)):
        m = mod_of(key)
        s = schema_of(m)
        if key == "rezervasyon":
            s["refs"] = {"kaynak": [{"id": k, "name": v} for k, v in (await names()).items()]}
        return s

    @api_router.get("/admin/mod/{key}")
    async def m_list(key: str, q: str = "", flt: str = "", _: dict = Depends(require_admin)):
        m = mod_of(key)
        proj = {"_id": 0, "image": 0}
        rows = await getattr(db, m["coll"]).find({}, proj).sort("created_at", -1).to_list(5000)
        nm = await names() if key == "rezervasyon" else None
        q = q.strip().lower()
        out = []
        for r in rows:
            if q and not any(q in str(r.get(f, "")).lower() for f in m["search"]):
                continue
            if not keep(key, r, flt):
                continue
            out.append({"id": r["id"], "cols": row_cols(key, r, nm), "status": r.get("status", "")})
        return {"rows": out, "summary": summary(key, rows), "total": len(rows)}

    @api_router.get("/admin/mod/{key}/{rid}")
    async def m_one(key: str, rid: str, _: dict = Depends(require_admin)):
        m = mod_of(key)
        d = await getattr(db, m["coll"]).find_one({"id": rid}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Kayıt bulunamadı")
        return d

    async def save(key, m, payload, rid=None):
        try:
            c = clean(m, payload, partial=bool(rid))
            if key == "rezervasyon":
                old = await db.bookings.find_one({"id": rid}, {"_id": 0}) if rid else {}
                await check_booking(db, {**old, **c}, rid)
        except ValueError as e:
            raise HTTPException(400, str(e))
        coll = getattr(db, m["coll"])
        if rid:
            if not await coll.find_one({"id": rid}, {"_id": 0, "id": 1}):
                raise HTTPException(404, "Kayıt bulunamadı")
            c["updated_at"] = time.time()
            await coll.update_one({"id": rid}, {"$set": c})
            return {**(await coll.find_one({"id": rid}, {"_id": 0, "image": 0}))}
        c.update({"id": str(uuid.uuid4()), "created_at": time.time(), "updated_at": time.time()})
        await coll.insert_one(dict(c))
        c.pop("_id", None); c.pop("image", None)
        return c

    @api_router.post("/admin/mod/{key}")
    async def m_add(key: str, payload: dict, _: dict = Depends(require_admin)):
        return await save(key, mod_of(key), payload)

    @api_router.put("/admin/mod/{key}/{rid}")
    async def m_put(key: str, rid: str, payload: dict, _: dict = Depends(require_admin)):
        return await save(key, mod_of(key), payload, rid)

    @api_router.delete("/admin/mod/{key}/{rid}")
    async def m_del(key: str, rid: str, _: dict = Depends(require_admin)):
        m = mod_of(key)
        r = await getattr(db, m["coll"]).delete_one({"id": rid})
        if not r.deleted_count:
            raise HTTPException(404, "Kayıt bulunamadı")
        return {"ok": True}

    # ---- herkese açık
    @api_router.get("/public/mod-img/{coll}/{rid}")
    async def pub_img(coll: str, rid: str):
        if coll not in ("programs", "resources"):
            raise HTTPException(404, "Yok")
        d = await getattr(db, coll).find_one({"id": rid, "status": "yayinda"}, {"_id": 0, "image": 1})
        im = (d or {}).get("image") or ""
        if ";base64," not in im:
            raise HTTPException(404, "Resim yok")
        head, b = im.split(";base64,", 1)
        return Response(base64.b64decode(b), media_type=head[5:], headers={"Cache-Control": "public, max-age=3600"})

    @api_router.get("/public/resources")
    async def pub_res():
        return await pub_items("resources")

    @api_router.get("/public/programs")
    async def pub_prog():
        return await pub_items("programs")

    @api_router.get("/public/availability")
    async def pub_avail(resource: str, start: str, end: str):
        try:
            s, e = _d(start), _d(end)
        except ValueError:
            raise HTTPException(400, "Tarih geçersiz")
        if not s or not e or e < s:
            raise HTTPException(400, "Tarih aralığı geçersiz")
        if not await db.resources.find_one({"id": resource, "status": "yayinda"}, {"_id": 0, "id": 1}):
            raise HTTPException(404, "Kaynak bulunamadı")
        return {"free": await free(db, resource, s, e)}

    @api_router.post("/public/bookings")
    async def pub_book(payload: dict):
        r = await db.resources.find_one({"id": str(payload.get("resource_id") or ""), "status": "yayinda"}, {"_id": 0})
        if not r:
            raise HTTPException(404, "Seçenek bulunamadı")
        try:
            c = clean(MODS["rezervasyon"], {**payload, "status": "bekliyor", "total": 0, "deposit": 0, "deposit_paid": False})
        except ValueError as e:
            raise HTTPException(400, str(e))
        if c["end"] < c["start"] or c["start"] < today():
            raise HTTPException(400, "Tarihleri kontrol edin")
        if len(re.sub(r"\D", "", c["phone"])) < 10:
            raise HTTPException(400, "Geçerli bir telefon yazın")
        if not await free(db, c["resource_id"], c["start"], c["end"]):
            raise HTTPException(409, "Bu tarihlerde dolu, başka tarih seçin")
        days = (datetime.strptime(c["end"], "%Y-%m-%d") - datetime.strptime(c["start"], "%Y-%m-%d")).days + 1
        c.update({"total": (r.get("price") or 0) * days, "id": str(uuid.uuid4()), "created_at": time.time(), "updated_at": time.time(), "source": "site"})
        await db.bookings.insert_one(dict(c))
        return {"ok": True}

    async def pub_items(coll):
        return await public_items(db, coll)
