# -*- coding: utf-8 -*-
"""Sektör şablonları: firma açılırken seçilen sektöre göre cihaz kataloğu, kontrol listesi, sık arızalar ve servis ayarı hazır gelir.

DİKKAT: Marka/model listeleri BAŞLANGIÇ listesidir (en yaygın olanlar); eksiği firma Cihaz Kataloğu'ndan tamamlar.
Kontrol listesi maddeleri genel iyi uygulama maddeleridir, yasal/üretici zorunluluğu yerine geçmez.
"""
import uuid
from datetime import datetime, timezone

SECTORS = {
    "kombi": {
        "name": "Kombi & Isıtma", "type": "kombi",
        "brands": {"Baymak": ["Luna 3 Comfort", "Duo-Tec Compact"], "Vaillant": ["ecoTEC Pure", "turboTEC Pro"], "Bosch": ["Condens 2000 W"],
                   "Demirdöküm": ["Nitromix", "Ademix"], "ECA": ["Proteus Premix", "Confeo Premix"], "Buderus": ["Logamax Plus GB062"],
                   "Viessmann": ["Vitodens 100-W"], "Protherm": [], "Immergas": []},
        "faults": ["Isıtmıyor", "Sıcak su yok", "Basınç düşüyor", "Ses yapıyor", "Hata kodu veriyor", "Petek ısınmıyor", "Sürekli kapanıyor"],
        "checklist": [("Gaz kaçak kontrolü", True), ("Su basıncı (1–1,5 bar)", True), ("Brülör ve ateşleme", True), ("Eşanjör kontrolü", False),
                      ("Baca gazı ölçümü", False), ("İşlem öncesi/sonrası fotoğraf", False)],
        "servis": {"foto_once": "zorunlu", "foto_sonra": "zorunlu"}, "pdf_title": "SERVİS FORMU"},
    "klima": {
        "name": "Klima & Soğutma", "type": "klima",
        "brands": {"Daikin": [], "Mitsubishi Electric": [], "Samsung": [], "LG": [], "Arçelik": [], "Vestel": [], "Bosch": [], "Airfel": []},
        "faults": ["Soğutmuyor", "Isıtmıyor", "Su damlatıyor", "Ses yapıyor", "Açılmıyor", "Gaz eksik", "Hata kodu veriyor"],
        "checklist": [("Filtre temizliği", True), ("Gaz basıncı kontrolü", True), ("Drenaj hattı", True), ("İç/dış ünite temizliği", False), ("Elektrik bağlantıları", False)],
        "servis": {"foto_once": "istege_bagli", "foto_sonra": "zorunlu"}, "pdf_title": "SERVİS FORMU"},
    "beyaz_esya": {
        "name": "Beyaz Eşya", "type": "beyaz eşya",
        "brands": {"Arçelik": [], "Beko": [], "Bosch": [], "Siemens": [], "Samsung": [], "LG": [], "Vestel": [], "Profilo": [], "Altus": []},
        "faults": ["Çalışmıyor", "Su almıyor", "Su boşaltmıyor", "Soğutmuyor", "Ses yapıyor", "Kapak açılmıyor", "Hata kodu veriyor"],
        "checklist": [("Elektrik ve priz kontrolü", True), ("Su giriş/çıkış hortumları", False), ("Filtre temizliği", False), ("Deneme çalıştırma", True)],
        "servis": {"foto_once": "istege_bagli", "foto_sonra": "istege_bagli"}, "pdf_title": "SERVİS FORMU"},
    "elektronik": {
        "name": "Elektronik & TV", "type": "tv",
        "brands": {"Samsung": [], "LG": [], "Sony": [], "Philips": [], "Vestel": [], "Arçelik": [], "TCL": [], "Hisense": []},
        "faults": ["Açılmıyor", "Görüntü yok", "Ses yok", "Ekran bozuk", "Kumanda çalışmıyor", "Bağlantı sorunu"],
        "checklist": [("Cihaz dış durum fotoğrafı", True), ("Aksesuar teslim listesi", False), ("Deneme çalıştırma", True)],
        "servis": {"foto_once": "zorunlu", "foto_sonra": "istege_bagli"}, "pdf_title": "SERVİS FORMU"},
    "bilgisayar": {
        "name": "Bilgisayar & Telefon", "type": "bilgisayar",
        "brands": {"Apple": [], "Samsung": [], "Lenovo": [], "HP": [], "Dell": [], "Asus": [], "Huawei": [], "Xiaomi": []},
        "faults": ["Açılmıyor", "Ekran kırık", "Şarj olmuyor", "Yavaş çalışıyor", "Virüs / yazılım", "Pil sorunu", "Su teması"],
        "checklist": [("Şifre/yedek bilgisi alındı", True), ("Cihaz dış durum fotoğrafı", True), ("Aksesuar teslim listesi", False), ("Test sonrası teslim", True)],
        "servis": {"foto_once": "zorunlu", "foto_sonra": "istege_bagli"}, "pdf_title": "TEKNİK SERVİS FORMU"},
    "tesisat": {
        "name": "Tesisat & Su", "type": "tesisat",
        "brands": {}, "faults": ["Su kaçağı", "Tıkanıklık", "Musluk/batarya", "Rezervuar", "Basınç düşük", "Sıcak su sorunu"],
        "checklist": [("Ana vana kapatıldı", True), ("Kaçak/sızdırmazlık testi", True), ("Çalışma alanı temizlendi", False)],
        "servis": {"foto_once": "zorunlu", "foto_sonra": "zorunlu"}, "pdf_title": "SERVİS FORMU"},
    "elektrik": {
        "name": "Elektrik", "type": "elektrik",
        "brands": {}, "faults": ["Elektrik kesik", "Sigorta atıyor", "Priz/anahtar arızası", "Aydınlatma", "Pano işi", "Kaçak akım"],
        "checklist": [("Enerji kesildi, gerilim yok teyidi", True), ("Topraklama kontrolü", True), ("İşlem sonrası test", True)],
        "servis": {"foto_once": "zorunlu", "foto_sonra": "zorunlu"}, "pdf_title": "SERVİS FORMU"},
    "guvenlik": {
        "name": "Güvenlik & Kamera", "type": "güvenlik",
        "brands": {"Hikvision": [], "Dahua": [], "Uniview": [], "Ajax": [], "Hilook": []},
        "faults": ["Görüntü yok", "Kayıt almıyor", "Alarm çalıyor", "Uzaktan erişim", "Yeni kurulum", "Kablo/bağlantı"],
        "checklist": [("Kamera görüş açısı testi", True), ("Kayıt cihazı/disk kontrolü", True), ("Uzaktan erişim testi", False)],
        "servis": {"foto_once": "zorunlu", "foto_sonra": "zorunlu"}, "pdf_title": "SERVİS FORMU"},
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def public_list():
    return {k: {"name": v["name"], "brands": len(v["brands"]), "faults": len(v["faults"]), "group": "teknik" if k in TEKNIK else "genel"} for k, v in SECTORS.items()}


async def apply(fdb, key: str) -> dict:
    """Firma veritabanına sektör şablonunu yazar. İdempotent: tekrar çağrılırsa kayıt çoğalmaz."""
    sec = SECTORS.get(key)
    if not sec:
        raise KeyError(key)
    n_models = 0
    for brand, models in sec["brands"].items():
        for model in (models or [""]):
            if model == "" and models:
                continue
            q = {"brand": brand, "model": model or "(genel)"}
            if await fdb.device_catalog.find_one(q):
                continue
            await fdb.device_catalog.insert_one({"id": uuid.uuid4().hex[:12], "type": sec["type"], "brand": brand, "model": model or "(genel)",
                                                 "kind": "", "power": "", "error_codes": "", "source": "baslangic", "created_at": _now()})
            n_models += 1
    if not await fdb.checklist_templates.find_one({"name": f"{sec['name']} kontrol listesi"}):
        await fdb.checklist_templates.insert_one({
            "id": uuid.uuid4().hex[:12], "name": f"{sec['name']} kontrol listesi", "device_type": sec["type"], "active": True, "created_at": _now(),
            "items": [{"id": uuid.uuid4().hex[:8], "text": t, "required": r} for t, r in sec["checklist"]]})
    servis = {**sec.get("servis", {}), "pdf": {"title": sec["pdf_title"]}}
    await fdb.app_settings.update_one({"_id": "servis"}, {"$set": servis}, upsert=True)
    await fdb.app_settings.update_one({"_id": "sector"}, {"$set": {"key": key, "name": sec["name"], "type": sec["type"], "faults": sec["faults"], "terms": sec.get("terms", {}), "at": _now()}}, upsert=True)
    return {"sector": key, "models": n_models, "checklist": len(sec["checklist"]), "faults": len(sec["faults"])}


# --- teknik olmayan sektörler (oto servis, çekici, kuaför, nakliye, tekstil, e-ticaret...) ---
from sektor_ek import NEW as _NEW  # noqa: E402
SECTORS.update({k: {kk: vv for kk, vv in v.items() if kk != "site"} for k, v in _NEW.items()})
import sektor_dil as _dil  # noqa: E402
for _k in _dil.ROWS:
    if _k in SECTORS:
        SECTORS[_k]["terms"] = _dil.labels(_k)
TEKNIK = ("kombi", "klima", "beyaz_esya", "elektronik", "bilgisayar", "tesisat", "elektrik", "guvenlik")


def register(api_router, db, deps):
    """Firma panelinin sektör diline erişmesi için: GET /api/sector-terms -> {key, name, terms}."""
    gcu = deps["get_current_user"]
    from fastapi import Depends

    @api_router.get("/sector-terms")
    async def sector_terms(user=Depends(gcu)):
        d = await db.app_settings.find_one({"_id": "sector"}, {"_id": 0}) or {}
        key = d.get("key") or ""
        sec = SECTORS.get(key) or {}
        import sektor_mod
        import sektor_dil
        terms = sektor_dil.labels(key) or d.get("terms") or sec.get("terms") or {}
        _kt = __import__("sektor_kayit").template(key)
        if _kt:
            terms = dict(terms)
            terms["Kayıtlar"] = _kt["plural"]
        return {"key": key, "name": d.get("name") or sec.get("name") or "", "terms": terms, "lex": sektor_dil.lex(key), "hide": sektor_dil.hide(key), "family": sektor_dil.family(key), "kayit": bool(__import__("sektor_kayit").template(key)), "modules": sektor_mod.modules_for(key)}
