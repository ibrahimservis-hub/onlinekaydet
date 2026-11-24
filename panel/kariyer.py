# -*- coding: utf-8 -*-
"""Kariyer: iş ilanları ve başvurular (platform düzeyi, ana veritabanı).

Genel uçlar: ilan listesi ve başvuru (ad, iletişim, CV). CV sunucu diskinde rastgele adla saklanır,
yalnız yönetim indirebilir. Başvuru KVKK aydınlatma onayı olmadan kabul edilmez."""
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, HTTPException, Request
from fastapi.responses import FileResponse

DURUM = ("yeni", "inceleniyor", "gorusme", "olumsuz", "ise_alindi")
TURLER = ("Tam zamanlı", "Yarı zamanlı", "Uzaktan", "Staj")
CV_UZANTI = {"pdf", "doc", "docx"}
CV_MAX = 5 * 1024 * 1024
_RATE: dict = {}

# Başlangıç pozisyonları: sahibi panelden düzenler, kapatır ya da yenisini ekler.
VARSAYILAN = [
    ("Satış ve Müşteri Danışmanı", "Satış", "Tam zamanlı", "Ankara / Uzaktan",
     "Yeni işletmelerle görüşür, ihtiyacı dinler, uygun paketi anlatır ve kurulum sürecini başlatır.",
     ["Gelen talepleri aramak ve takip etmek", "Demo ve tanıtım görüşmeleri yapmak", "Kurulum sürecini müşteriyle birlikte yürütmek"],
     ["Telefonda ve yazışmada rahat iletişim", "Küçük işletmelerin işleyişini merak etmek", "Satış ya da müşteri ilişkilerinde deneyim artı"]),
    ("Müşteri Başarı ve Teknik Destek Uzmanı", "Destek", "Tam zamanlı", "Ankara / Uzaktan",
     "Müşterilerin panelde yaşadığı soruları çözer, eğitim verir, geri bildirimi ürün ekibine iletir.",
     ["Destek taleplerini yanıtlamak", "Müşterilere panel kullanımını anlatmak", "Sık gelen soruları bilgi bankasına dönüştürmek"],
     ["Açık ve sabırlı anlatım", "Web ve temel bilgisayar bilgisi", "Sorun çözmeye istekli olmak"]),
    ("Python / FastAPI Yazılım Geliştirici", "Yazılım", "Tam zamanlı", "Uzaktan",
     "Panel, mağaza ve entegrasyon altyapısını geliştirir; testlerle birlikte sürdürülebilir kod yazar.",
     ["Yeni özellikleri uçtan uca geliştirmek", "Pazaryeri, kargo ve ödeme entegrasyonlarına bakmak", "Test yazmak ve hata ayıklamak"],
     ["Python ve REST API deneyimi", "MongoDB ya da benzeri veritabanı bilgisi", "Git ile çalışma alışkanlığı"]),
    ("Ön Yüz (Frontend) Geliştirici", "Yazılım", "Tam zamanlı", "Uzaktan",
     "Müşteri paneli, vitrin ve site temalarının arayüzünü hızlı, erişilebilir ve mobil uyumlu yapar.",
     ["Arayüz bileşenleri geliştirmek", "Tema ve site editörü ekranlarını iyileştirmek", "Hız ve erişilebilirlik ölçümlerini takip etmek"],
     ["HTML, CSS ve JavaScript'e hakimiyet", "Mobil öncelikli düşünme", "Tasarımı koda doğru taşıma"]),
    ("Dijital Pazarlama ve SEO Uzmanı", "Pazarlama", "Tam zamanlı", "Ankara / Uzaktan",
     "Sitenin ve müşteri sitelerinin arama sonuçlarındaki görünürlüğünü artırır; içerik planını yönetir.",
     ["Anahtar kelime ve içerik planı hazırlamak", "Search Console ve analiz verilerini izlemek", "Reklam ve sosyal medya kampanyalarını yürütmek"],
     ["SEO ve Google Ads temel bilgisi", "Analitik araçlarla çalışma", "Türkçe yazım gücü"]),
    ("İçerik Yazarı", "Pazarlama", "Yarı zamanlı", "Uzaktan",
     "Blog, rehber ve sektör sayfalarını küçük işletme sahibinin anlayacağı dille yazar.",
     ["Sektörlere özel blog yazıları hazırlamak", "Bilgi bankası makalelerini güncellemek", "Metinleri kontrol edip düzeltmek"],
     ["Güçlü Türkçe", "Araştırma yapıp sadeleştirme", "Örnek yazılarını paylaşabilmek"]),
    ("Grafik ve Arayüz Tasarımcısı", "Tasarım", "Tam zamanlı", "Uzaktan",
     "Tema, görsel ve panel ekranlarını tutarlı ve özgün bir dille tasarlar.",
     ["Sektör temaları tasarlamak", "Panel ve vitrin ekranlarını çizmek", "Görsel kimliği tutarlı tutmak"],
     ["Figma ya da benzeri araç deneyimi", "Tipografi ve renk duyusu", "Portfolyo paylaşabilmek"]),
    ("Stajyer (Yazılım / Pazarlama / Destek)", "Staj", "Staj", "Ankara / Uzaktan",
     "Öğrenmek ve gerçek bir ürünün içinde çalışmak isteyenler için kısa dönem staj.",
     ["Ekibe bağlı olarak görev almak", "Haftalık hedeflerle ilerlemek"],
     ["Öğrenci ya da yeni mezun olmak", "Öğrenmeye açık olmak"]),
]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _slug(s):
    t = s.lower().translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU"))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]


def _lines(v, n=8, w=200):
    if isinstance(v, str):
        v = v.split("\n")
    return [str(x).strip()[:w] for x in (v or []) if str(x).strip()][:n]


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    CV_DIR = Path(os.environ.get("KARIYER_DIR") or (Path(__file__).resolve().parent / "kariyer_cv"))

    def main():
        return db.main()

    def need_main():
        from tenant import current
        if current():
            raise HTTPException(403, "Bu işlem yalnız ana yönetim içindir")

    async def tohum():
        if await main().kariyer_ilan.count_documents({}):
            return
        for i, (t, d, tur, yer, ozet, gor, nit) in enumerate(VARSAYILAN):
            await main().kariyer_ilan.insert_one({"id": str(uuid.uuid4()), "slug": _slug(t), "title": t, "dept": d, "type": tur, "city": yer,
                                                  "summary": ozet, "duties": gor, "reqs": nit, "active": True, "order": i, "created_at": _now()})

    @api_router.get("/public/kariyer")
    async def pub_list():
        await tohum()
        rows = await main().kariyer_ilan.find({"active": True}, {"_id": 0}).sort("order", 1).to_list(100)
        return {"ilanlar": rows}

    @api_router.post("/public/kariyer/basvuru")
    async def pub_apply(request: Request):
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
        now = time.time()
        hist = [t for t in _RATE.get(ip, []) if now - t < 3600]
        if len(hist) >= 5:
            raise HTTPException(429, "Çok fazla deneme, biraz sonra tekrar deneyin")
        form = await request.form()
        if str(form.get("website") or "").strip():
            return {"ok": True}
        name = " ".join(str(form.get("name") or "").split())[:80]
        email = str(form.get("email") or "").strip()[:120]
        phone = re.sub(r"\D", "", str(form.get("phone") or ""))[-11:]
        if len(name) < 3:
            raise HTTPException(422, "Lütfen adınızı ve soyadınızı yazın")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise HTTPException(422, "E-posta adresi geçersiz")
        if len(phone) < 10:
            raise HTTPException(422, "Telefon numarası geçersiz")
        if str(form.get("kvkk") or "") not in ("1", "true", "on"):
            raise HTTPException(422, "Başvuru için aydınlatma metnini onaylamalısınız")
        ilan_id = str(form.get("ilan") or "").strip()
        ilan = await main().kariyer_ilan.find_one({"id": ilan_id, "active": True}, {"_id": 0}) if ilan_id and ilan_id != "genel" else None
        if ilan_id and ilan_id != "genel" and not ilan:
            raise HTTPException(422, "Bu ilan artık yayında değil")
        cv = None
        f = form.get("cv")
        if f is not None and getattr(f, "filename", ""):
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            if ext not in CV_UZANTI:
                raise HTTPException(422, "Özgeçmiş PDF, DOC ya da DOCX olmalı")
            data = await f.read()
            if len(data) > CV_MAX:
                raise HTTPException(422, "Özgeçmiş en fazla 5 MB olabilir")
            if not data:
                raise HTTPException(422, "Özgeçmiş dosyası boş")
            CV_DIR.mkdir(parents=True, exist_ok=True)
            fn = "%s.%s" % (uuid.uuid4().hex, ext)
            (CV_DIR / fn).write_bytes(data)
            cv = {"file": fn, "name": re.sub(r"[^\w.\- ]", "_", f.filename)[:80], "size": len(data)}
        hist.append(now)
        _RATE[ip] = hist
        doc = {"id": str(uuid.uuid4()), "ilan_id": ilan["id"] if ilan else "genel", "ilan": ilan["title"] if ilan else "Genel başvuru",
               "name": name, "email": email, "phone": phone, "city": str(form.get("city") or "").strip()[:60],
               "link": str(form.get("link") or "").strip()[:200], "message": str(form.get("message") or "").strip()[:1500],
               "cv": cv, "status": "yeni", "note": "", "kvkk": {"onay": True, "at": _now()}, "created_at": _now()}
        await main().kariyer_basvuru.insert_one(dict(doc))
        try:
            import baglanti
            await baglanti.bildir(main(), "kariyer.basvuru", "Yeni iş başvurusu: %s · %s" % (name, doc["ilan"]), {"id": doc["id"], "name": name, "ilan": doc["ilan"]})
        except Exception:                                      # noqa: BLE001
            pass
        return {"ok": True}

    # ------------------------------------------------------------- yönetim
    @api_router.get("/admin/kariyer")
    async def adm_list(durum: str = "", _: dict = Depends(require_admin)):
        need_main()
        await tohum()
        ilan = await main().kariyer_ilan.find({}, {"_id": 0}).sort("order", 1).to_list(200)
        q = {"status": durum} if durum in DURUM else {}
        bas = await main().kariyer_basvuru.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
        sayac = {s: await main().kariyer_basvuru.count_documents({"status": s}) for s in DURUM}
        for i in ilan:
            i["basvuru"] = await main().kariyer_basvuru.count_documents({"ilan_id": i["id"]})
        return {"ilanlar": ilan, "basvurular": bas, "sayac": sayac, "turler": list(TURLER), "durumlar": list(DURUM)}

    def _ilan_alanlari(p, cur=None):
        cur = dict(cur or {})
        for k, n in (("title", 100), ("dept", 40), ("city", 60), ("summary", 400)):
            if k in p:
                cur[k] = str(p[k]).strip()[:n]
        if "type" in p:
            cur["type"] = p["type"] if p["type"] in TURLER else "Tam zamanlı"
        for k in ("duties", "reqs"):
            if k in p:
                cur[k] = _lines(p[k])
        if "active" in p:
            cur["active"] = bool(p["active"])
        if "order" in p:
            try:
                cur["order"] = int(p["order"])
            except (TypeError, ValueError):
                pass
        return cur

    @api_router.post("/admin/kariyer/ilan")
    async def adm_add(payload: dict, _: dict = Depends(require_admin)):
        need_main()
        d = _ilan_alanlari(payload, {"type": "Tam zamanlı", "active": True, "duties": [], "reqs": [], "dept": "", "city": "", "summary": ""})
        if len(d.get("title", "")) < 3:
            raise HTTPException(422, "İlan başlığı gerekli")
        d["id"] = str(uuid.uuid4())
        d["slug"] = _slug(d["title"])
        d.setdefault("order", await main().kariyer_ilan.count_documents({}))
        d["created_at"] = _now()
        await main().kariyer_ilan.insert_one(dict(d))
        return {"ok": True, "id": d["id"]}

    @api_router.put("/admin/kariyer/ilan/{iid}")
    async def adm_edit(iid: str, payload: dict, _: dict = Depends(require_admin)):
        need_main()
        cur = await main().kariyer_ilan.find_one({"id": iid}, {"_id": 0})
        if not cur:
            raise HTTPException(404, "İlan bulunamadı")
        d = _ilan_alanlari(payload, cur)
        if len(d.get("title", "")) < 3:
            raise HTTPException(422, "İlan başlığı gerekli")
        await main().kariyer_ilan.update_one({"id": iid}, {"$set": d})
        return {"ok": True}

    @api_router.delete("/admin/kariyer/ilan/{iid}")
    async def adm_del(iid: str, _: dict = Depends(require_admin)):
        need_main()
        await main().kariyer_ilan.delete_one({"id": iid})
        return {"ok": True}

    @api_router.put("/admin/kariyer/basvuru/{bid}")
    async def adm_app_edit(bid: str, payload: dict, _: dict = Depends(require_admin)):
        need_main()
        sets = {}
        if "status" in payload:
            if payload["status"] not in DURUM:
                raise HTTPException(422, "Durum geçersiz")
            sets["status"] = payload["status"]
        if "note" in payload:
            sets["note"] = str(payload["note"])[:600]
        if not sets:
            raise HTTPException(422, "Değişiklik yok")
        r = await main().kariyer_basvuru.update_one({"id": bid}, {"$set": sets})
        if not r.matched_count:
            raise HTTPException(404, "Başvuru bulunamadı")
        return {"ok": True}

    @api_router.delete("/admin/kariyer/basvuru/{bid}")
    async def adm_app_del(bid: str, _: dict = Depends(require_admin)):
        need_main()
        b = await main().kariyer_basvuru.find_one({"id": bid}, {"_id": 0})
        if b and b.get("cv"):
            try:
                (CV_DIR / b["cv"]["file"]).unlink()
            except OSError:
                pass
        await main().kariyer_basvuru.delete_one({"id": bid})
        return {"ok": True}

    @api_router.get("/admin/kariyer/basvuru/{bid}/cv")
    async def adm_cv(bid: str, _: dict = Depends(require_admin)):
        need_main()
        b = await main().kariyer_basvuru.find_one({"id": bid}, {"_id": 0})
        if not b or not b.get("cv"):
            raise HTTPException(404, "Özgeçmiş yok")
        p = (CV_DIR / b["cv"]["file"]).resolve()
        if CV_DIR.resolve() not in p.parents or not p.exists():
            raise HTTPException(404, "Dosya bulunamadı")
        return FileResponse(str(p), filename=b["cv"]["name"] or p.name)
