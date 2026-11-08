"""Kârlılık analizi, müşteri iş takibi (link + ETA + anket) ve arıza teşhis asistanı (bilgi tabanı)."""
import asyncio
import re
import secrets
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:
    TR = timezone(timedelta(hours=3))

DONE = ("tamamlandi", "faturalandi")
ADS = ("google_ads", "meta_ads", "diger_reklam")
DEFAULT_PROFIT = {"travel_cost_per_job": 0.0, "other_cost_per_job": 0.0, "target_margin_pct": 25.0, "ad_spend": {}}
STATUS_TR = {"yeni": "Talebiniz alındı", "atandi": "Usta atandı", "yolda": "Usta yolda", "basladi": "Servis işlemi başladı",
             "tamamlandi": "İş tamamlandı", "faturalandi": "İş tamamlandı", "iptal": "İptal edildi"}

_CAT = {"kombi": "kombi", "klima": "klima", "sofben": "sofben", "tv": "televizyon", "televizyon": "televizyon",
        "buzdolabi": "beyaz-esya", "camasir": "beyaz-esya", "bulasik": "beyaz-esya", "kurutma": "beyaz-esya", "firin": "beyaz-esya"}

FAULT_KEYS = [
    ("Su yapıyor / kaçak", ["su yap", "kaçak", "kacak", "damla", "akıt", "akit", "su kaçır"]),
    ("Isıtmıyor / sıcak su yok", ["ısıtm", "isitm", "sıcak su", "sicak su", "petek"]),
    ("Soğutmuyor", ["soğutm", "sogutm", "soğuk", "buzlan", "gaz"]),
    ("Çalışmıyor / açılmıyor", ["çalışm", "calism", "açılm", "acilm", "çalış", "tepki", "elektrik"]),
    ("Hata kodu / arıza kodu", ["hata kodu", "kod", "e0", "e1", "f0", "f1"]),
    ("Ses / gürültü", ["ses", "gürültü", "gurultu", "titre"]),
    ("Su boşaltmıyor / almıyor", ["boşalt", "bosalt", "su almı", "su almi"]),
    ("Görüntü / ekran", ["görüntü", "goruntu", "ekran", "ses var"]),
    ("Bakım / temizlik", ["bakım", "bakim", "temizl", "periyodik"]),
]


def _id():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc).isoformat()


def _day(s):
    return (s or "")[:10]


def fault_cat(text: str) -> str:
    t = (text or "").lower()
    for name, keys in FAULT_KEYS:
        if any(k in t for k in keys):
            return name
    return "Diğer"


def norm_phone(p):
    d = re.sub(r"\D", "", p or "")
    return d[-10:]


# ---------------------------------------------------------------- bilgi tabanı tohum verisi (başlangıç; panelden düzenlenir)
def _kb(dt, title, causes, parts, minutes, steps, brand="", code="", keywords=""):
    return {"device_type": dt, "brand": brand, "code": code, "title": title, "causes": causes, "parts": parts, "est_minutes": minutes,
            "steps": steps, "keywords": keywords, "price_min": 0, "price_max": 0, "notes": "Başlangıç bilgisi — kendi tecrübenize göre düzenleyin.", "is_active": True}


SEED_KB = [
    _kb("kombi", "Basınç sürekli düşüyor (su yapıyor)", ["Genleşme tankı hava kaçırıyor", "Emniyet ventili damlatıyor", "Doldurma vanası/tesisat kaçağı", "Eşanjörde mikro delik"],
        ["Genleşme tankı", "Emniyet ventili", "Doldurma vanası/anahtarı", "Eşanjör"], 60, ["Soğukken basıncı 1-1,5 bara getirin", "Tesisat ve kombi içi kaçak kontrolü", "Genleşme tankı hava basıncını ölçün (≈1 bar)", "Emniyet ventili çıkışını kontrol edin"], keywords="basınç su yapıyor su kaybı"),
    _kb("kombi", "Sıcak su gelmiyor / yetersiz", ["Üç yollu vana arızası", "Plakalı eşanjör kireçli", "NTC sıcaklık sensörü", "Akış sensörü/flowmetre arızası"],
        ["Üç yollu vana motoru", "Plakalı eşanjör", "NTC sensör", "Akış sensörü"], 75, ["Kullanım suyu akışını ve akış sensörünü kontrol edin", "Eşanjör kireç durumunu inceleyin", "NTC direncini ölçün"], keywords="sıcak su yok kullanım suyu"),
    _kb("kombi", "Petekler ısınmıyor", ["Sirkülasyon pompası arızası", "Sistemde hava", "Üç yollu vana kalmış", "Filtre/tesisat tıkanıklığı", "Oda termostatı"],
        ["Sirkülasyon pompası", "Üç yollu vana", "Oda termostatı"], 60, ["Havayı alın, basıncı kontrol edin", "Pompanın döndüğünü doğrulayın", "Termostat kontağını test edin"], keywords="petek ısınmıyor kalorifer"),
    _kb("kombi", "Ateşleme yapmıyor / alev gitmiyor", ["Ateşleme elektrodu/trafosu", "İyonizasyon elektrodu kirli", "Gaz valfi", "Gaz girişi/ gaz basıncı", "Baca/fan sorunu"],
        ["Ateşleme elektrodu", "Ateşleme trafosu", "İyonizasyon elektrodu", "Gaz valfi"], 60, ["Gaz vanasını ve gaz beslemesini kontrol edin", "Elektrot mesafesi ve temizliği", "Fan ve hava basınç şalterini test edin"], keywords="ateşleme alev yanmıyor kilitleniyor"),
    _kb("kombi", "Fan / baca gürültüsü ve hata", ["Fan arızası", "Hava basınç şalteri", "Baca tıkanıklığı"], ["Fan", "Hava basınç şalteri"], 60, ["Baca bağlantısını ve tıkanıklığı kontrol edin", "Fan beslemesini ölçün"], keywords="fan ses gürültü baca"),
    _kb("klima", "Soğutmuyor", ["Gaz eksik/kaçak", "Kompresör veya kondansatör (kapasitör)", "İç/dış ünite kirli", "Dış ünite fan motoru"], ["Kapasitör", "Fan motoru", "Gaz tamamlama", "Kompresör"], 75,
       ["Filtre ve eşanjör temizliği", "Gaz basıncı ölçümü", "Kapasitör ve fan motoru testi"], keywords="soğutmuyor soğutma gaz"),
    _kb("klima", "İç ünite su damlatıyor", ["Drenaj hortumu tıkalı", "Ünite eğimi yanlış", "Kirli evaporatör/ buzlanma"], ["Drenaj hortumu"], 45, ["Drenajı üfleyerek/ temizleyerek açın", "Eğimi ve filtreyi kontrol edin"], keywords="su damlatıyor damlama"),
    _kb("klima", "Açılmıyor / tepki vermiyor", ["Kumanda/pili", "Besleme sigortası", "İç ünite kartı", "Dış ünite haberleşme"], ["Kart", "Sigorta"], 45, ["Beslemeyi ve sigortayı ölçün", "Kart ve haberleşme kablosunu kontrol edin"], keywords="çalışmıyor açılmıyor"),
    _kb("buzdolabi", "Soğutmuyor", ["Gaz kaçağı", "Kompresör/ röle-termik", "Termostat veya sensör", "Evaporatör fanı", "Defrost rezistansı"], ["Röle-termik", "Termostat/sensör", "Evaporatör fanı", "Defrost rezistansı"], 60,
       ["Kompresör çalışıyor mu dinleyin", "Fan ve defrost devresini kontrol edin", "Buzlanma varsa defrost testi yapın"], keywords="soğutmuyor soğutma"),
    _kb("buzdolabi", "Aşırı buzlanma", ["Defrost rezistansı", "Defrost termostatı/sensörü", "Kapı contası kaçırıyor"], ["Defrost rezistansı", "Defrost termostatı", "Kapı contası"], 60, ["Contayı kağıt testiyle kontrol edin", "Defrost elemanlarını ölçün"], keywords="buzlanma buz tutuyor"),
    _kb("buzdolabi", "Yüksek ses / titreşim", ["Fan pervanesi", "Kompresör ayakları", "Boru temasları"], ["Fan motoru"], 30, ["Sesin kaynağını belirleyin", "Boruları ve ayakları sabitleyin"], keywords="ses gürültü titreme"),
    _kb("camasir", "Su boşaltmıyor", ["Pompa tıkalı/arızalı", "Filtre tıkanık", "Boşaltma hortumu"], ["Tahliye pompası"], 45, ["Pompa filtresini temizleyin", "Hortumu kontrol edin", "Pompa beslemesini ölçün"], keywords="su boşaltmıyor tahliye"),
    _kb("camasir", "Su almıyor", ["Su giriş valfi", "Giriş filtresi tıkalı", "Basınç şalteri (seviye)"], ["Su giriş valfi", "Basınç şalteri"], 45, ["Musluğu ve filtreyi kontrol edin", "Valf bobinini ölçün"], keywords="su almıyor"),
    _kb("camasir", "Sıkma/çalkalama yapmıyor, dönmüyor", ["Kayış veya motor kömürü", "Motor/ tacho", "Elektronik kart"], ["Kayış", "Motor kömürü", "Kart"], 75, ["Kayış ve kasnağı kontrol edin", "Motor kömürlerini ölçün"], keywords="sıkma dönmüyor tambur"),
    _kb("camasir", "Kapı açılmıyor / kilit hatası", ["Kapı kilidi arızası", "Kart/ rölesi"], ["Kapı kilidi"], 30, ["Kilit rezistansını kontrol edin", "Kapı kolunu ve kilit mandalını inceleyin"], keywords="kapı kilit açılmıyor"),
    _kb("bulasik", "Yıkamıyor / bulaşıklar kirli", ["Püskürtme kolları tıkalı", "Sirkülasyon pompası", "Filtre kirli", "Deterjan/ tuz/ parlatıcı"], ["Sirkülasyon pompası", "Püskürtme kolu"], 45, ["Filtreleri ve kolları temizleyin", "Pompa basıncını kontrol edin"], keywords="yıkamıyor kirli"),
    _kb("bulasik", "Su boşaltmıyor", ["Tahliye pompası", "Filtre/ sifon tıkalı"], ["Tahliye pompası"], 45, ["Filtreyi ve sifonu kontrol edin", "Pompayı test edin"], keywords="su boşaltmıyor tahliye"),
    _kb("firin", "Isıtmıyor", ["Rezistans arızası", "Termostat/ sensör", "Kart"], ["Rezistans", "Termostat", "Sensör"], 45, ["Rezistans sürekliliğini ölçün", "Termostat ve sensörü test edin"], keywords="ısıtmıyor ısınmıyor"),
    _kb("kurutma", "Kurutmuyor", ["Rezistans", "Filtre/ kondenser kirli", "NTC sensör", "Fan"], ["Rezistans", "NTC", "Kondenser"], 60, ["Filtre ve kondenseri temizleyin", "Rezistans ve NTC değerlerini ölçün"], keywords="kurutmuyor ıslak"),
    _kb("televizyon", "Görüntü yok, ses var", ["Arka aydınlatma (LED şerit)", "Güç/ inverter kartı"], ["LED şerit", "Güç kartı"], 90, ["Ekrana el feneriyle yan bakın (silik görüntü var mı)", "LED şerit beslemesini ölçün"], keywords="görüntü yok karanlık"),
    _kb("televizyon", "Açılmıyor", ["Güç kartı", "Ana kart (main board)", "Standby devresi"], ["Güç kartı", "Ana kart"], 75, ["Standby ışığını kontrol edin", "Güç kartı çıkış gerilimlerini ölçün"], keywords="açılmıyor çalışmıyor"),
]


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]

    # ============================================================ KÂRLILIK
    async def get_profit_cfg():
        s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        cfg = {**DEFAULT_PROFIT, **(s.get("profit") or {})}
        cfg["ad_spend"] = dict(cfg.get("ad_spend") or {})
        return cfg

    @api_router.get("/profit/settings")
    async def profit_settings(_: dict = Depends(require_admin)):
        return await get_profit_cfg()

    @api_router.put("/profit/settings")
    async def put_profit_settings(payload: dict, _: dict = Depends(require_admin)):
        cfg = await get_profit_cfg()
        for k in ("travel_cost_per_job", "other_cost_per_job", "target_margin_pct"):
            if k in payload:
                cfg[k] = max(0.0, float(payload[k] or 0))
        if isinstance(payload.get("ad_spend"), dict):
            cfg["ad_spend"] = {str(m)[:7]: max(0.0, float(v or 0)) for m, v in payload["ad_spend"].items() if re.match(r"^\d{4}-\d{2}$", str(m)[:7])}
        await db.app_settings.update_one({"_id": "global"}, {"$set": {"profit": cfg}}, upsert=True)
        return cfg

    @api_router.get("/reports/profitability")
    async def profitability(date_from: Optional[str] = None, date_to: Optional[str] = None, _: dict = Depends(require_admin)):
        now = datetime.now(TR)
        date_to = date_to or now.strftime("%Y-%m-%d")
        date_from = date_from or (now - timedelta(days=89)).strftime("%Y-%m-%d")
        cfg = await get_profit_cfg()
        jobs_all = await db.service_jobs.find({}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(100000)
        parts = {p["id"]: p for p in await db.spare_parts.find({}, {"_id": 0}).to_list(50000)}
        custs = {c["id"]: c for c in await db.customers.find({}, {"_id": 0, "id": 1, "city": 1}).to_list(100000)}
        # reklam iş sayısı (ay bazında) -> iş başına reklam payı
        ads_cnt = defaultdict(int)
        for j in jobs_all:
            if (j.get("source_channel") or "") in ADS:
                ads_cnt[_day(j.get("created_at"))[:7]] += 1
        rows, missing_cost = [], 0
        for j in jobs_all:
            if j.get("status") not in DONE:
                continue
            d = _day(j.get("completed_at") or j.get("updated_at"))
            if not (date_from <= d <= date_to):
                continue
            rev = float(j.get("total_amount", 0) or 0)
            pc, miss = 0.0, False
            for p in j.get("parts_used") or []:
                sp = parts.get(p.get("part_id") or "")
                if sp and float(sp.get("cost", 0) or 0) > 0:
                    pc += float(p.get("qty", 0) or 0) * float(sp["cost"])
                elif float(p.get("total", 0) or 0) > 0:
                    miss = True
            missing_cost += 1 if miss else 0
            tech = float(j.get("technician_commission_amount", 0) or 0)
            travel = float(j.get("travel_cost") if j.get("travel_cost") not in (None, "") else cfg["travel_cost_per_job"])
            other = float(cfg["other_cost_per_job"])
            ad = 0.0
            if (j.get("source_channel") or "") in ADS:
                m = _day(j.get("created_at"))[:7]
                if ads_cnt[m]:
                    ad = float(cfg["ad_spend"].get(m, 0)) / ads_cnt[m]
            cost = pc + tech + travel + other + ad
            rows.append({"id": j["id"], "job_number": j.get("job_number"), "date": d, "customer": j.get("customer_name"), "device_type": j.get("device_type") or "Belirtilmemiş",
                         "brand": j.get("device_brand_name") or "Belirtilmemiş", "city": (custs.get(j.get("customer_id"), {}).get("city") or "Belirtilmemiş").title(),
                         "channel": j.get("source_channel") or "belirtilmemis", "technician": j.get("assigned_technician_name") or "Atanmamış",
                         "fault": fault_cat(j.get("fault_description")), "revenue": round(rev, 2), "parts_cost": round(pc, 2), "tech_share": round(tech, 2),
                         "travel": round(travel, 2), "other": round(other, 2), "ad": round(ad, 2), "profit": round(rev - cost, 2), "missing_cost": miss})

        def agg(keyf):
            g = defaultdict(lambda: {"jobs": 0, "revenue": 0.0, "cost": 0.0, "profit": 0.0, "loss_jobs": 0})
            for r in rows:
                x = g[keyf(r)]
                x["jobs"] += 1
                x["revenue"] += r["revenue"]
                x["profit"] += r["profit"]
                x["cost"] += r["revenue"] - r["profit"]
                x["loss_jobs"] += 1 if r["profit"] < 0 else 0
            out = []
            tm = float(cfg["target_margin_pct"]) / 100.0
            for k, v in g.items():
                avg_cost = v["cost"] / v["jobs"]
                out.append({"name": k, "jobs": v["jobs"], "revenue": round(v["revenue"], 2), "cost": round(v["cost"], 2), "profit": round(v["profit"], 2),
                            "avg_profit": round(v["profit"] / v["jobs"], 2), "margin_pct": round(v["profit"] / v["revenue"] * 100, 1) if v["revenue"] else 0,
                            "loss_jobs": v["loss_jobs"], "avg_price": round(v["revenue"] / v["jobs"], 2),
                            "suggested_min_price": round(avg_cost / (1 - tm), 0) if tm < 1 else 0})
            return sorted(out, key=lambda x: x["profit"])

        rev = sum(r["revenue"] for r in rows)
        prof = sum(r["profit"] for r in rows)
        groups = {"device_type": agg(lambda r: r["device_type"]), "brand": agg(lambda r: r["brand"]), "city": agg(lambda r: r["city"]),
                  "fault": agg(lambda r: r["fault"]), "channel": agg(lambda r: r["channel"]), "technician": agg(lambda r: r["technician"])}
        insights = []
        for key, label in (("device_type", "cihaz türü"), ("fault", "arıza türü"), ("brand", "marka"), ("city", "şehir"), ("channel", "kanal")):
            for g in groups[key]:
                if g["jobs"] >= 3 and g["profit"] < 0:
                    insights.append({"level": "kayip", "text": f"{g['name']} ({label}) {g['jobs']} işte toplam {abs(g['profit']):,.0f} ₺ zarar ettirdi; ortalama satış {g['avg_price']:,.0f} ₺, en az {g['suggested_min_price']:,.0f} ₺ istenmeli."})
                elif g["jobs"] >= 3 and g["margin_pct"] < cfg["target_margin_pct"] / 2:
                    insights.append({"level": "dusuk", "text": f"{g['name']} ({label}) marjı düşük (%{g['margin_pct']}); hedef %{cfg['target_margin_pct']:g}."})
        if missing_cost:
            insights.append({"level": "bilgi", "text": f"{missing_cost} işte kullanılan parçanın alış fiyatı (maliyet) tanımlı değil; Yedek Parça sayfasında maliyet girin, kâr daha doğru hesaplanır."})
        if not any(cfg["ad_spend"].values()) and any(r["channel"] in ADS for r in rows):
            insights.append({"level": "bilgi", "text": "Reklam kaynaklı işler var ama aylık reklam harcaması girilmemiş; reklam payı 0 sayıldı."})
        return {"range": {"from": date_from, "to": date_to}, "settings": cfg,
                "totals": {"jobs": len(rows), "revenue": round(rev, 2), "profit": round(prof, 2), "margin_pct": round(prof / rev * 100, 1) if rev else 0,
                           "avg_profit": round(prof / len(rows), 2) if rows else 0, "loss_jobs": len([r for r in rows if r["profit"] < 0]),
                           "parts_cost": round(sum(r["parts_cost"] for r in rows), 2), "tech_share": round(sum(r["tech_share"] for r in rows), 2),
                           "travel": round(sum(r["travel"] + r["other"] for r in rows), 2), "ad": round(sum(r["ad"] for r in rows), 2)},
                "groups": groups, "insights": insights, "worst_jobs": sorted(rows, key=lambda r: r["profit"])[:15]}

    # ============================================================ MÜŞTERİ İŞ TAKİBİ
    async def job_for_actor(job_id: str, user: dict):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            raise HTTPException(status_code=404, detail="Servis kaydı bulunamadı")
        if user.get("role") != "admin" and job.get("assigned_technician_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Bu iş size atanmamış")
        return job

    async def ensure_token(job):
        if job.get("track_token"):
            return job["track_token"]
        tok = secrets.token_urlsafe(16)
        await db.service_jobs.update_one({"id": job["id"]}, {"$set": {"track_token": tok}})
        return tok

    @api_router.post("/jobs/{job_id}/track-link")
    async def track_link(job_id: str, user: dict = Depends(get_current_user)):
        job = await job_for_actor(job_id, user)
        tok = await ensure_token(job)
        return {"token": tok, "path": f"/takip/{tok}"}

    @api_router.post("/jobs/{job_id}/on-the-way")
    async def on_the_way(job_id: str, payload: dict, user: dict = Depends(get_current_user)):
        job = await job_for_actor(job_id, user)
        if job.get("status") in DONE or job.get("status") == "iptal":
            raise HTTPException(status_code=400, detail="Bu iş kapalı")
        eta = int(max(1, min(480, int(payload.get("eta_minutes") or 30))))
        upd = {"eta_minutes": eta, "eta_set_at": _now(), "on_the_way_at": _now()}
        if job.get("status") in ("yeni", "atandi"):
            upd["status"] = "yolda"
        if payload.get("lat") is not None and payload.get("lng") is not None:
            upd["tech_location"] = {"lat": round(float(payload["lat"]), 5), "lng": round(float(payload["lng"]), 5), "at": _now()}
        await db.service_jobs.update_one({"id": job_id}, {"$set": upd})
        tok = await ensure_token(job)
        try:
            import asyncio, notify
            asyncio.create_task(notify.job_event(db, "on_the_way", {**job, **upd, "track_token": tok}))
        except Exception:
            pass
        return {"ok": True, "token": tok, "eta_minutes": eta, "status": upd.get("status", job.get("status"))}

    @api_router.post("/jobs/{job_id}/location")
    async def share_location(job_id: str, payload: dict, user: dict = Depends(get_current_user)):
        await job_for_actor(job_id, user)
        await db.service_jobs.update_one({"id": job_id}, {"$set": {"tech_location": {"lat": round(float(payload["lat"]), 5), "lng": round(float(payload["lng"]), 5), "at": _now()}}})
        return {"ok": True}

    @api_router.put("/jobs/{job_id}/travel-cost")
    async def set_travel(job_id: str, payload: dict, _: dict = Depends(require_admin)):
        await db.service_jobs.update_one({"id": job_id}, {"$set": {"travel_cost": float(payload.get("travel_cost") or 0)}})
        return {"ok": True}

    def _first(name):
        return (name or "").split(" ")[0] if name else ""

    def _mask(name):
        p = (name or "").split()
        return " ".join([p[0]] + [x[0] + "." for x in p[1:]]) if p else ""

    @api_router.get("/public/track/{token}")
    async def public_track_job(token: str, request: Request):
        job = await db.service_jobs.find_one({"track_token": token}, {"_id": 0})
        if not job or len(token) < 12:
            raise HTTPException(status_code=404, detail="Takip bağlantısı geçersiz")
        s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        st = job.get("status")
        loc = job.get("tech_location")
        show_loc = bool(loc and st == "yolda" and loc.get("at") and loc["at"] > (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat())
        eta_left = None
        if st == "yolda" and job.get("eta_set_at") and job.get("eta_minutes"):
            try:
                end = datetime.fromisoformat(job["eta_set_at"]) + timedelta(minutes=int(job["eta_minutes"]))
                eta_left = max(0, int((end - datetime.now(timezone.utc)).total_seconds() // 60))
            except Exception:
                pass
        done = st in DONE
        _tu = await db.users.find_one({"id": job.get("assigned_technician_id")}, {"_id": 0, "photo_path": 1, "photo_status": 1}) if job.get("assigned_technician_id") else None
        g = await db.app_settings.find_one({"_id": "growth"}, {"_id": 0, "google_review_url": 1}) or {}
        review_url = g.get("google_review_url", "") if (job.get("survey") or {}).get("rating", 0) >= 4 else ""
        return {"review_url": review_url, "job_number": job.get("job_number"), "status": st, "status_label": STATUS_TR.get(st, st), "customer": _mask(job.get("customer_name")),
                "device": " ".join(x for x in [job.get("device_brand_name"), job.get("device_type")] if x), "scheduled_at": job.get("scheduled_at", ""),
                "technician": _first(job.get("assigned_technician_name")), "technician_photo": bool((_tu or {}).get("photo_path")) and (_tu or {}).get("photo_status") not in ("pending", "rejected"), "eta_minutes": job.get("eta_minutes"), "eta_left": eta_left,
                "location": {"lat": loc["lat"], "lng": loc["lng"]} if show_loc else None,
                "work_done": job.get("work_done", "") if done else "", "total": job.get("total_amount") if done else None,
                "created_at": job.get("created_at"), "completed_at": job.get("completed_at", ""),
                "survey": job.get("survey"), "can_rate": done and not job.get("survey"),
                "company": {"name": s.get("company_name", ""), "phone": s.get("company_phone", "")}}

    _rate = defaultdict(list)

    @api_router.post("/public/track/{token}/survey")
    async def public_survey(token: str, payload: dict, request: Request):
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
        now = datetime.now(timezone.utc).timestamp()
        _rate[ip] = [t for t in _rate[ip] if now - t < 600]
        if len(_rate[ip]) >= 10:
            raise HTTPException(status_code=429, detail="Çok fazla deneme")
        _rate[ip].append(now)
        job = await db.service_jobs.find_one({"track_token": token}, {"_id": 0})
        if not job:
            raise HTTPException(status_code=404, detail="Takip bağlantısı geçersiz")
        if job.get("status") not in DONE:
            raise HTTPException(status_code=400, detail="İş tamamlanınca değerlendirebilirsiniz")
        if job.get("survey"):
            raise HTTPException(status_code=400, detail="Bu iş zaten değerlendirildi")
        rating = int(payload.get("rating") or 0)
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=422, detail="1-5 arası puan verin")
        comment = str(payload.get("comment") or "")[:1000].strip()
        survey = {"rating": rating, "comment": comment, "at": _now(), "punctual": payload.get("punctual"), "polite": payload.get("polite")}
        await db.service_jobs.update_one({"id": job["id"]}, {"$set": {"survey": survey, "customer_rating": rating}})
        await db.reviews.insert_one({"id": _id(), "name": _mask(job.get("customer_name")) or "Müşteri", "rating": rating, "comment": comment,
                                     "city": "", "job_number": job.get("job_number", ""), "brand": job.get("device_brand_name", ""), "category": _CAT.get((job.get("device_type") or "").lower(), ""), "status": "beklemede", "reply": "", "origin": "anket", "created_at": _now()})
        import notify as _n
        await _n.push_admins_t(db, "Yeni müşteri değerlendirmesi", f"{job.get('job_number', '')} · {rating}★ {comment[:120]}".strip(), "/admin/reviews")
        if rating <= 3:                                  # düşük puan: yönetime anında haber (uyarı kanalı açıksa)
            try:
                import notify
                await notify.notify_owner_t(db, f"[ServisPlus] Düşük puan: {job.get('job_number', '')} - {rating}★. " + (f"Yorum: {comment[:160]}. " if comment else "") + "Müşteriyi arayın (panel > Müşteri Memnuniyeti).", kind="low_rating")
            except Exception:                            # noqa: BLE001
                pass
        return {"ok": True}

    # ============================================================ ARIZA TEŞHİS ASİSTANI
    class _KB:
        fields = ("device_type", "brand", "code", "title", "causes", "parts", "est_minutes", "steps", "keywords", "price_min", "price_max", "notes", "is_active")

    def _clean_kb(p: dict) -> dict:
        out = {}
        for k in _KB.fields:
            if k in p:
                v = p[k]
                if k in ("causes", "parts", "steps"):
                    v = [str(x).strip()[:300] for x in (v if isinstance(v, list) else str(v).split("\n")) if str(x).strip()][:30]
                elif k in ("est_minutes", "price_min", "price_max"):
                    v = float(v or 0)
                elif k == "is_active":
                    v = bool(v)
                else:
                    v = str(v or "").strip()[:400]
                out[k] = v
        return out

    @api_router.get("/diagnosis")
    async def kb_list(_: dict = Depends(require_admin)):
        return await db.diagnosis_kb.find({}, {"_id": 0}).sort([("device_type", 1), ("title", 1)]).to_list(2000)

    @api_router.post("/diagnosis")
    async def kb_create(payload: dict, user: dict = Depends(require_admin)):
        d = _clean_kb(payload)
        if not d.get("title") or not d.get("device_type"):
            raise HTTPException(status_code=400, detail="Cihaz türü ve başlık zorunlu")
        doc = {"id": _id(), "is_active": True, "created_at": _now(), "created_by": user["name"], **d}
        await db.diagnosis_kb.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.put("/diagnosis/{kid}")
    async def kb_update(kid: str, payload: dict, _: dict = Depends(require_admin)):
        r = await db.diagnosis_kb.update_one({"id": kid}, {"$set": _clean_kb(payload)})
        if not r.matched_count:
            raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
        return {"ok": True}

    @api_router.delete("/diagnosis/{kid}")
    async def kb_delete(kid: str, _: dict = Depends(require_admin)):
        await db.diagnosis_kb.delete_one({"id": kid})
        return {"ok": True}

    @api_router.post("/diagnosis/seed-defaults")
    async def kb_seed(user: dict = Depends(require_admin)):
        return {"ok": True, "added": await kb_seed_all(db, user["name"])}

    _TR = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ö": "o", "Ö": "o", "ü": "u", "Ü": "u"})
    _STOP = {"ve", "ile", "bir", "ariza", "arizasi", "kodu", "kod", "hata", "hatasi", "veriyor", "veriyo", "cihaz", "cihazi", "neden", "nasil", "icin", "var", "olan", "gibi", "bana", "mi", "mu", "ne", "yok", "oldu"}
    _DEV = {"kombi": "kombi", "klima": "klima", "sofben": "şofben", "tv": "televizyon", "televizyon": "televizyon", "televizyonu": "televizyon", "buzdolabi": "buzdolabı",
            "buzdolabim": "buzdolabı", "camasir": "çamaşır makinesi", "bulasik": "bulaşık makinesi", "kurutma": "kurutma makinesi", "firin": "fırın", "ocak": "fırın",
            "ankastre": "fırın", "derin": "buzdolabı", "dondurucu": "buzdolabı"}

    def _f(s):
        return (s or "").translate(_TR).lower()

    def _tokens(s):
        return [t for t in re.split(r"[^a-z0-9]+", _f(s)) if len(t) >= 3 and t not in _STOP]

    def _ncode(c):
        c = re.split(r"[\s(]", _f(c).strip())[0]
        return re.sub(r"(?<=[a-z])0+(?=\d)", "", re.sub(r"[^a-z0-9]", "", c))

    def _codeset(c):
        c = re.sub(r"\(.*?\)", "", _f(c))
        out = set()
        for p in re.split(r"\s*/\s*|,|\s+ve\s+", c):
            m = re.match(r"^\s*([a-z]*)\.?\s*(\d+)\s*[-–—]\s*[a-z]*\.?\s*(\d+)", p)
            if m and 0 <= int(m.group(3)) - int(m.group(2)) <= 30:
                w = len(m.group(2))
                for n in range(int(m.group(2)), int(m.group(3)) + 1):
                    out.add(_ncode(m.group(1) + str(n).zfill(w)))
            else:
                n = _ncode(p)
                if n:
                    out.add(n)
        return out

    _SYN = {"akitiyor": ["damlat", "sizint", "kacak", "su yap"], "sogutmuyor": ["sogutma", "isiniyor"], "isitmiyor": ["isinm", "isitma"], "calismiyor": ["acilm", "calism"],
            "acilmiyor": ["calism", "acilm", "olu"], "ses": ["gurult", "titres", "vizilti"], "gurultu": ["ses", "titres"], "yanmiyor": ["atesle", "alev"], "kokuyor": ["koku"]}

    def _stem(t):
        return t[:max(4, len(t) - 3)] if len(t) >= 6 else t

    @api_router.get("/diagnosis/search")
    async def kb_search(q: str = "", device_type: str = "", brand: str = "", code: str = "", user: dict = Depends(get_current_user)):
        """Bilgi tabanı eşleşmeleri (kod/marka/cihaz/belirti) + kendi geçmiş işlerinizden benzer iş istatistiği."""
        kb = await db.diagnosis_kb.find({"is_active": {"$ne": False}}, {"_id": 0}).to_list(5000)
        fq = _f(q)
        qt = _tokens(q)
        # cihaz türü: parametre yoksa sorgudan çıkar
        dt = _f(device_type).strip()
        if not dt:
            for t in re.split(r"[^a-z0-9]+", fq):
                if t in _DEV:
                    dt = _f(_DEV[t])
                    break
        # marka: parametre yoksa sorguda geçen bilinen marka
        brands = {_f(d.get("brand")): d.get("brand") for d in kb if d.get("brand")}
        br = _f(brand).strip()
        if not br:
            for fb in sorted(brands, key=len, reverse=True):
                if fb and re.search(r"(^|[^a-z0-9])" + re.escape(fb) + r"([^a-z0-9]|$)", fq):
                    br = fb
                    break
        # kod adayları: "e01", "e 01", "f28", "lp"
        cands = set()
        if code:
            cands.add(_ncode(code))
        for m in re.finditer(r"(?<![a-z0-9])([a-z]{1,3})[\s\-]?(\d{1,3}[a-z]?)(?![a-z0-9])", fq):
            cands.add(_ncode(m.group(1) + m.group(2)))
        known_codes = set()
        for d in kb:
            if d.get("code"):
                known_codes |= _codeset(d["code"])
        for t in re.split(r"[^a-z0-9]+", fq):
            if t and t in known_codes and len(t) <= 4:
                cands.add(_ncode(t))
        cands = {c for c in cands if c and c in known_codes}
        words = [t for t in qt if _ncode(t) not in cands and t not in brands and t not in _DEV and _f(brand) != t]
        scored, weak_list = [], []
        for d in kb:
            ddt = _f(d.get("device_type"))
            sc = 0
            if dt:
                if dt in ddt or ddt in dt or ddt == "beyaz esya":
                    sc += 3 if ddt != "beyaz esya" else 1
                else:
                    continue
            dbr = _f(d.get("brand"))
            if br:
                if dbr:
                    if br in dbr or dbr in br:
                        sc += 6
                    else:
                        continue
            codehit = bool(d.get("code") and (_codeset(d["code"]) & cands))
            if codehit:
                sc += 14 + (6 if _ncode(d["code"]) in cands else 0)
            elif cands and not words:
                continue
            title, kw = _f(d.get("title")), _f(d.get("keywords"))
            body = _f(" ".join(d.get("causes", []) + d.get("steps", []) + d.get("parts", [])))
            ts = strong = weak = 0
            for t in words:
                alts = [_stem(t)] + _SYN.get(t, [])
                if any(a in title for a in alts):
                    ts += 4; strong += 1
                elif any(a in kw for a in alts):
                    ts += 3; strong += 1
                elif _stem(t) in body:
                    ts += 1; weak += 1
            if words and not codehit and not (strong or weak >= 2):
                if weak:
                    weak_list.append((sc + ts, d))
                continue
            if words and strong >= 2:
                ts += 2
            sc += ts
            if not words and not cands and not (dt or br):
                continue
            if d.get("source") == "belirti-rehberi" and not codehit:
                sc += 1
            scored.append((sc, d))
        if not scored:
            scored = weak_list
        scored.sort(key=lambda x: (-x[0], x[1].get("brand") != "", x[1].get("title", "")))
        matches = [d for _, d in scored[:12]]
        # geçmiş benzer işler
        jobs = await db.service_jobs.find({"status": {"$in": list(DONE)}}, {"_id": 0, "device_type": 1, "device_brand_name": 1, "fault_description": 1, "work_done": 1,
                                                                          "total_amount": 1, "parts_used": 1, "created_at": 1, "completed_at": 1, "job_number": 1}).sort("completed_at", -1).to_list(3000)
        sim = []
        for j in jobs:
            if dt and (j.get("device_type") or "") and dt not in _f(j.get("device_type")):
                continue
            if br and (j.get("device_brand_name") or "") and br not in _f(j.get("device_brand_name")):
                continue
            text = _f(f"{j.get('fault_description','')} {j.get('work_done','')}")
            hit = sum(1 for t in words if _stem(t) in text) + (3 if any(c in re.sub(r"[^a-z0-9]", "", text) for c in cands) else 0)
            if (words or cands) and hit == 0:
                continue
            sim.append(j)
        pcount, durs, prices = defaultdict(lambda: [0, 0.0]), [], []
        for j in sim:
            prices.append(float(j.get("total_amount", 0) or 0))
            for p in j.get("parts_used") or []:
                pcount[p.get("name", "?")][0] += 1
                pcount[p.get("name", "?")][1] += float(p.get("total", 0) or 0)
            try:
                if j.get("created_at") and j.get("completed_at"):
                    h = (datetime.fromisoformat(j["completed_at"]) - datetime.fromisoformat(j["created_at"])).total_seconds() / 3600
                    if 0 < h < 240:
                        durs.append(h)
            except Exception:
                pass
        stats = {"count": len(sim), "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
                 "min_price": round(min(prices), 2) if prices else 0, "max_price": round(max(prices), 2) if prices else 0,
                 "avg_close_hours": round(sum(durs) / len(durs), 1) if durs else 0,
                 "top_parts": sorted([{"name": k, "jobs": v[0], "amount": round(v[1], 2)} for k, v in pcount.items()], key=lambda x: -x["jobs"])[:6],
                 "examples": [{"job_number": j.get("job_number"), "fault": j.get("fault_description", "")[:120], "work_done": (j.get("work_done") or "")[:160], "total": j.get("total_amount", 0)} for j in sim[:4]]}
        return {"matches": matches, "similar": stats, "detected": {"device_type": dt, "brand": brands.get(br, br), "codes": sorted(cands)}, "kb_total": len(kb)}


async def kb_seed_all(db, by="sistem"):
    """Site arıza kodu rehberi + yaygın belirtiler; mevcut kayıtlara dokunmaz, olmayanları ekler."""
    import kbdata
    have = {(d.get("device_type"), d.get("brand", ""), d.get("code", ""), d.get("title")) async for d in db.diagnosis_kb.find({}, {"_id": 0, "device_type": 1, "brand": 1, "code": 1, "title": 1})}
    docs = []
    for d in kbdata.all_entries() + SEED_KB:
        k = (d["device_type"], d.get("brand", ""), d.get("code", ""), d["title"])
        if k in have:
            continue
        have.add(k)
        docs.append({"id": _id(), "created_at": _now(), "created_by": by, **d})
    if docs:
        await db.diagnosis_kb.insert_many(docs)
    return len(docs)


async def ensure_indexes(db):
    await db.service_jobs.create_index("track_token", sparse=True)
    await db.diagnosis_kb.create_index("id", unique=True)
    try:
        if await db.diagnosis_kb.count_documents({"source": "kod-rehberi"}, limit=5) < 5:
            asyncio.create_task(kb_seed_all(db))
    except Exception:
        pass
