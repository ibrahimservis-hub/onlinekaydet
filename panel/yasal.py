# -*- coding: utf-8 -*-
"""Yasal metinler: firmanın modülüne göre gereken metinler siteye otomatik gelir.

- Her sitede: KVKK Aydınlatma, Gizlilik ve Güvenlik, Çerez Politikası, Ticari İleti İzni.
- E-ticaret açıksa ek olarak: Mesafeli Satış, Ön Bilgilendirme, İade Koşulları, Teslimat ve Kargo, Üyelik Sözleşmesi.
- Randevu alınan işlerde ek olarak: Randevu ve İptal Koşulları.
Satıcı bilgileri (unvan, adres, vergi, iletişim) firma kaydından ve site bilgilerinden otomatik doldurulur;
müşteri dilediği alanı ya da metnin tamamını kendisi değiştirebilir (özel metin), varsayılana dönebilir, footer'dan gizleyebilir.
Aynı depo (shop_settings.legal / legal_docs) mağaza ayarlarıyla ortaktır.
"""
import re
import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException

import shop_legal

COMMON = ["gizlilik-kvkk", "gizlilik-guvenlik", "cerez-politikasi", "ticari-ileti-izni"]
SHOP = ["mesafeli-satis-sozlesmesi", "on-bilgilendirme-formu", "iptal-iade-cayma", "teslimat-ve-kargo", "uyelik-sozlesmesi"]
RANDEVU = ["randevu-iptal-kosullari"]
ALANLAR = [("seller_title", "Unvan / firma adı", 120), ("address", "Adres", 250), ("phone", "Telefon", 30), ("email", "E-posta", 90),
           ("tax_office", "Vergi dairesi", 60), ("tax_no", "Vergi no / TC kimlik no", 20), ("mersis", "MERSİS no", 30), ("kep", "KEP adresi", 90)]


def _now():
    return datetime.now(timezone.utc).isoformat()


async def _firma(db):
    try:
        import tenant
        t = tenant.current()
        if t:
            return await db.main().firms.find_one({"db": t}, {"_id": 0}) or {}
    except Exception:                                              # noqa: BLE001
        pass
    return {}


async def otomatik(db):
    """Firma kaydı ve site bilgilerinden satıcı alanları."""
    f = await _firma(db)
    p = await db.app_settings.find_one({"_id": "site_profile"}, {"_id": 0}) or {}
    pr = p.get("profile") if isinstance(p.get("profile"), dict) else p
    g = lambda *ks: next((str(x).strip() for x in ks if x and str(x).strip()), "")
    return {"seller_title": g(f.get("demo_firma") if f.get("demo") else "", f.get("name")),
            "address": g(pr.get("address"), f.get("address")), "phone": g(pr.get("phone"), f.get("phone"), pr.get("whatsapp")),
            "email": g(pr.get("email"), f.get("contact_email"), f.get("login_email")),
            "tax_office": g(f.get("tax_office")), "tax_no": g(f.get("tax_no")), "mersis": "", "kep": ""}


async def satici(db, legal=None):
    """Etkin satıcı bilgisi: müşterinin yazdığı alan, yoksa otomatik. Döner: (legal, {alan: 'oto'|'elle'})."""
    if legal is None:
        sc = await db.app_settings.find_one({"_id": "shop_settings"}, {"_id": 0, "legal": 1}) or {}
        legal = sc.get("legal") or {}
    oto = await otomatik(db)
    out = dict(legal)
    kaynak = {}
    for k, _, _ in ALANLAR:
        v = str(legal.get(k) or "").strip()
        if v:
            kaynak[k] = "elle"
        else:
            out[k] = oto.get(k, "")
            kaynak[k] = "oto" if out[k] else ""
    return out, kaynak


async def gereken(db, shop_on=None):
    """Bu firmanın sitesinde olması gereken metinlerin slug listesi (sıralı)."""
    mods, sec, acik = [], "", False
    try:
        import blocks
        mods, sec, acik = await blocks.firma_modulleri(db)
    except Exception:                                              # noqa: BLE001
        pass
    feats = await db.app_settings.find_one({"_id": "site_features"}, {"_id": 0}) or {}
    shop = bool(shop_on) or acik or bool(feats.get("shop_enabled"))
    randevu = "randevu" in (mods or []) or "servis" in (mods or []) or not mods
    out = (SHOP if shop else []) + COMMON + (RANDEVU if (randevu and not shop) else [])
    return out, shop


async def cfg_ve_satici(db, shop_on=None):
    """Sayfa üretimi için: (cfg, legal) — cfg._genel mağazasız sitede sade metinleri seçtirir."""
    import shop as shopmod
    sc = await db.app_settings.find_one({"_id": "shop_settings"}, {"_id": 0}) or {}
    _, shop = await gereken(db, shop_on)
    cfg = {**shopmod.SHOP_DEFAULT, **sc, "_genel": not shop}
    legal, _k = await satici(db, shopmod.merge_legal(cfg.get("legal")))
    return cfg, legal


async def footer_listesi(db, shop_on=None):
    """[(slug, başlık)] — gizlenmeyenler."""
    sl, _ = await gereken(db, shop_on)
    sc = await db.app_settings.find_one({"_id": "shop_settings"}, {"_id": 0, "legal_hide": 1}) or {}
    gizli = set(sc.get("legal_hide") or [])
    return [(k, shop_legal.TITLES[k]) for k in sl if k not in gizli]


def register(api_router, db, deps):
    adm = deps["require_admin"]

    @api_router.get("/yp/yasal")
    async def liste(_: dict = Depends(adm)):
        cfg, legal = await cfg_ve_satici(db)
        sl, shop = await gereken(db)
        sc = await db.app_settings.find_one({"_id": "shop_settings"}, {"_id": 0}) or {}
        _, kaynak = await satici(db)
        gizli = set(sc.get("legal_hide") or [])
        docs = []
        for k in sl:
            c = (sc.get("legal_docs") or {}).get(k) or {}
            docs.append({"slug": k, "title": shop_legal.TITLES[k], "custom": bool(c.get("html")), "gizli": k in gizli,
                         "html": shop_legal.doc_html(k, legal, cfg, sc.get("legal_docs")), "default_html": shop_legal.default_html(k, legal, cfg)})
        eksik = [lbl for k, lbl, _ in ALANLAR if k in ("seller_title", "address", "phone", "email") and not str(legal.get(k) or "").strip()]
        return {"shop": shop, "docs": docs, "eksik": eksik,
                "bilgi": [{"k": k, "ad": lbl, "v": str(legal.get(k) or ""), "kaynak": kaynak.get(k, ""), "max": mx} for k, lbl, mx in ALANLAR],
                "not": "Metinler genel şablondur. Firmanıza göre düzenleyin; hukuki danışman onayı önerilir."}

    @api_router.put("/yp/yasal/bilgi")
    async def bilgi_kaydet(payload: dict, _: dict = Depends(adm)):
        sc = await db.app_settings.find_one({"_id": "shop_settings"}, {"_id": 0, "legal": 1}) or {}
        legal = dict(sc.get("legal") or {})
        for k, _lbl, mx in ALANLAR:
            if k in payload:
                v = " ".join(str(payload.get(k) or "").split())[:mx]
                if v:
                    legal[k] = v
                else:
                    legal.pop(k, None)               # boş bırakılırsa firma kaydından otomatik dolar
        await db.app_settings.update_one({"_id": "shop_settings"}, {"$set": {"legal": legal, "updated_at": _now()}}, upsert=True)
        return {"ok": True}

    @api_router.put("/yp/yasal/{slug}")
    async def metin_kaydet(slug: str, payload: dict, _: dict = Depends(adm)):
        if slug not in shop_legal.TITLES:
            raise HTTPException(404, "Metin bulunamadı")
        sc = await db.app_settings.find_one({"_id": "shop_settings"}, {"_id": 0}) or {}
        docs, gizli = dict(sc.get("legal_docs") or {}), set(sc.get("legal_hide") or [])
        if "gizli" in payload:
            (gizli.add if payload.get("gizli") else gizli.discard)(slug)
        if payload.get("reset"):
            docs.pop(slug, None)
        elif "html" in payload:
            h = str(payload.get("html") or "")[:60000]
            if len(re.sub(r"<[^>]+>", "", h).strip()) < 40:
                raise HTTPException(422, "Metin çok kısa")
            if re.search(r"<\s*(script|iframe|object|embed|style|link|form)|\bon\w+\s*=|javascript:", h, re.I):
                raise HTTPException(422, "Metinde betik veya gömülü içerik olamaz")
            docs[slug] = {"html": h, "at": _now()}
        await db.app_settings.update_one({"_id": "shop_settings"}, {"$set": {"legal_docs": docs, "legal_hide": sorted(gizli), "updated_at": _now()}}, upsert=True)
        return {"ok": True}
