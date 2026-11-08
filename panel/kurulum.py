# G177: Kurulum durumu — eksik ayarları tek listede gösterir (salt okunur).
# Gizli değerler ASLA döndürülmez; yalnızca "dolu / boş" bilgisi verilir.
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import Depends


def _s(v):
    return bool(str(v or "").strip())


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    async def _doc(i):
        return await db.app_settings.find_one({"_id": i}, {"_id": 0}) or {}

    @api_router.get("/admin/kurulum")
    async def kurulum(_: dict = Depends(require_admin)):
        return await _kurulum()

    async def _kurulum():
        glob, grow, mkt, mods, feat = await _doc("global"), await _doc("growth"), await _doc("mkt"), await _doc("sp_modules"), await _doc("site_features")
        nt = glob.get("notify") or {}
        prov = nt.get("provider") or "none"
        cust = nt.get("customer") or {}
        alert = nt.get("admin_alert") or {}
        smtp = nt.get("smtp") or {}
        g = (mkt.get("google") or {})
        gcred = _s(g.get("client_id")) and _s(g.get("client_secret"))
        flags, conf = mods.get("flags") or {}, mods.get("config") or {}
        iy = conf.get("iyzico") or {}
        soc = conf.get("social") or {}
        booking = (grow.get("booking") or {})
        rem = (grow.get("reminders") or {})
        shop_on = bool(feat.get("shop_enabled", False))

        # (anahtar, başlık, durum, önem, açıklama, panelde nereden)
        items = [
            ("sms_wa", "SMS / WhatsApp sağlayıcısı", prov != "none", "kritik",
             "Müşteriye takip linki, ustaya iş bildirimi ve yeni usta giriş bilgileri bu sağlayıcı ile gider. Seçilmezse hiçbir mesaj gönderilmez.",
             "ek:wa"),
            ("cust_msg", "Müşteri mesajları açık", bool(cust.get("enabled")) and prov != "none", "kritik",
             "İş atandı / usta yolda / tamamlandı mesajları ve memnuniyet anketi.", "ek:wa"),
            ("admin_alert", "Yönetici uyarısı (telefon/e-posta)", bool(alert.get("enabled")) and bool((alert.get("phones") or []) or (alert.get("emails") or [])), "önerilir",
             "Kritik olaylarda (iptal, şikâyet, sistem hatası) size anında haber verir.", "ek:wa"),
            ("smtp", "E-posta gönderimi (SMTP)", _s(smtp.get("host")) and _s(smtp.get("from_addr")), "önerilir",
             "Fatura/rapor e-postaları ve e-posta ile uyarı için.", "ek:wa"),
            ("review", "Google yorum bağlantısı", _s(grow.get("google_review_url")), "önerilir",
             "4-5 puan veren müşteriye Google'da yorum bırakma linki gösterilir.", "/admin/growth"),
            ("booking", "Online randevu", bool(booking.get("enabled")), "isteğe bağlı",
             "Müşteri takip sayfasından ve siteden boş saat seçerek randevu alır.", "/admin/growth"),
            ("reminders", "Otomatik bakım/garanti hatırlatma", bool(rem.get("enabled")), "isteğe bağlı",
             "Bakım zamanı gelen ve garantisi biten müşterilere hatırlatma.", "/admin/growth"),
            ("gsc", "Google Search Console bağlantısı", gcred and _s(g.get("gsc_refresh_token")), "önerilir",
             "Arama sorguları, tıklama ve dizin durumu panele gelir. Google Search Console sayfasından \"Google ile bağlan\" ile bağlanır.", "ek:gsc"),
            ("ads", "Google Ads bağlantısı", gcred and _s(g.get("ads_refresh_token")) and _s(g.get("developer_token")), "isteğe bağlı",
             "Reklam harcaması ve dönüşümler Rapor Merkezi'ne otomatik gelir.", "/admin/marketing"),
            ("ga4", "Google Analytics 4", bool(flags.get("ga4")) and _s((conf.get("ga4") or {}).get("measurement_id")), "isteğe bağlı",
             "Site trafiği Google Analytics'te de ölçülür (panel kendi ziyaretçi takibini zaten yapıyor).", "ek:moduller"),
            ("turnstile", "Giriş ekranı bot koruması (Turnstile)", bool(flags.get("turnstile")) and _s((conf.get("turnstile") or {}).get("site_key")) and _s((conf.get("turnstile") or {}).get("secret_key")), "önerilir",
             "Panel giriş ekranını otomatik şifre denemelerine karşı korur.", "ek:moduller"),
            ("social", "Sosyal medya hesapları", any(_s(v) for k, v in soc.items() if k != "whatsapp"), "isteğe bağlı",
             "Sitenin alt bilgisinde simge olarak çıkar, Google'a işletme profili olarak bildirilir.", "ek:moduller"),
        ]
        if shop_on:
            items.append(("iyzico", "Kartla online ödeme (iyzico)", bool(flags.get("iyzico")) and _s(iy.get("api_key")) and _s(iy.get("secret_key")), "önerilir",
                          "Mağaza açık; kartla ödeme için iyzico anahtarları gerekir.", "ek:moduller"))
        out = [{"key": k, "label": l, "ok": bool(o), "level": lv, "desc": d, "where": w} for k, l, o, lv, d, w in items]
        order = {"kritik": 0, "önerilir": 1, "isteğe bağlı": 2}
        out.sort(key=lambda x: (x["ok"], order.get(x["level"], 3)))
        miss = [x for x in out if not x["ok"]]
        return {"items": out, "missing": len(miss), "critical": sum(1 for x in miss if x["level"] == "kritik"),
                "shop_enabled": shop_on,
                "server_side": ["Sunucu kapanınca telefona uyarı (NTFY_KONU) ve UptimeRobot sunucu tarafında ayarlanır; panelden görünmez."]}

    # G178: Genel Bakış "Bugün" şeridi — tek istekte günün özeti (salt okunur)
    CLOSED = ["tamamlandi", "faturalandi", "iptal"]

    @api_router.get("/admin/bugun")
    async def bugun(_: dict = Depends(require_admin)):
        try:
            import governance
            tz = governance.notify_tz()
        except Exception:                                 # noqa: BLE001
            tz = timezone(timedelta(hours=3))
        now = datetime.now(tz)
        day = now.strftime("%Y-%m-%d")
        nowkey = now.strftime("%Y-%m-%dT%H:%M")
        start_utc = datetime(now.year, now.month, now.day, tzinfo=tz).astimezone(timezone.utc).isoformat()

        async def _recv():
            rows = await db.service_jobs.find({"status": {"$in": ["tamamlandi", "faturalandi"]}, "payment_status": {"$in": ["veresiye", "kismi"]}},
                                              {"_id": 0, "total_amount": 1, "collected_amount": 1}).to_list(5000)
            def f(x):
                try:
                    return float(x or 0)
                except (TypeError, ValueError):
                    return 0.0
            vals = [f(r.get("total_amount")) - f(r.get("collected_amount")) for r in rows]
            vals = [v for v in vals if v > 0.5]
            return round(sum(vals), 2), len(vals)

        async def _done():
            rows = await db.service_jobs.find({"status": {"$in": ["tamamlandi", "faturalandi"]}, "completed_at": {"$gte": start_utc}},
                                              {"_id": 0, "total_amount": 1}).to_list(2000)
            tot = 0.0
            for r in rows:
                try:
                    tot += float(r.get("total_amount") or 0)
                except (TypeError, ValueError):
                    pass
            return len(rows), round(tot, 2)

        sched, created, unassigned, overdue, open_, onway, done, recv, k = await asyncio.gather(
            db.service_jobs.count_documents({"scheduled_at": {"$regex": "^" + day}, "status": {"$nin": CLOSED}}),
            db.service_jobs.count_documents({"created_at": {"$gte": start_utc}}),
            db.service_jobs.count_documents({"status": "yeni", "$or": [{"assigned_technician_id": ""}, {"assigned_technician_id": None}, {"assigned_technician_id": {"$exists": False}}]}),
            db.service_jobs.count_documents({"status": {"$nin": CLOSED}, "scheduled_at": {"$ne": "", "$lt": nowkey, "$exists": True}}),
            db.service_jobs.count_documents({"status": {"$nin": CLOSED}}),
            db.service_jobs.count_documents({"status": "yolda"}),
            _done(), _recv(), _kurulum())
        return {"day": day, "scheduled_today": sched, "created_today": created, "unassigned": unassigned, "overdue": overdue,
                "open": open_, "on_the_way": onway, "done_today": done[0], "revenue_today": done[1],
                "receivable": recv[0], "receivable_n": recv[1], "setup_missing": k["missing"], "setup_critical": k["critical"]}
