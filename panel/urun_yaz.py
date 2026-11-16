# -*- coding: utf-8 -*-
"""Ürün açıklaması ve SEO metni önerisi.

Yapay zekâ anahtarı varsa yapay zekâ yazar; anahtar yok, kapalı ya da günlük limit doluysa ürün bilgisinden
kurallı şablon üretir. Hiçbir şey kaydedilmez, öneri döner; kullanıcı onaylayınca düzenleyici uygular."""
import html as _html
import json
import re

from fastapi import Depends, HTTPException

ALANLAR = ("short", "desc", "seo_title", "seo_desc", "seo_keywords", "alt")
_TAG = re.compile(r"<[^>]+>")


def _t(v, n=200):
    return " ".join(_TAG.sub(" ", _html.unescape(str(v if v is not None else ""))).split())[:n]


def _kes(s, n):
    s = " ".join(str(s).split())
    if len(s) <= n:
        return s
    s = s[:n - 1].rsplit(" ", 1)[0].rstrip(" ,;:-–|")
    return s + "…"


def sablon(p):
    """Ürün bilgisinden kurallı metin. Bilgi uydurmaz: yalnız verilen alanlar kullanılır."""
    ad, marka, kat = _t(p.get("name"), 120), _t(p.get("brand"), 60), _t(p.get("cat"), 60)
    model = _t(p.get("model"), 60)
    ozel = [(_t(x.get("k"), 60), _t(x.get("v"), 100)) for x in (p.get("specs") or []) if x.get("k") and x.get("v")][:8]
    ad = ad or "Ürün"
    ilk = ad if (not marka or marka.lower() in ad.lower()) else marka + " " + ad
    kisa = _kes("%s%s. %s" % (ilk, " (%s)" % model if model and model.lower() not in ad.lower() else "",
                              ("%s kategorisinde, " % kat if kat else "") + "hızlı kargo ve güvenli alışveriş"), 160)
    par = ["%s, %s." % (ilk, ("%s kategorisindeki ürünlerimiz arasında" % kat) if kat else "ürünlerimiz arasında")]
    if ozel:
        par.append("Öne çıkan özellikler: " + "; ".join("%s: %s" % x for x in ozel) + ".")
    gun = ((p.get("ship") or {}).get("gun"))
    if gun:
        par.append("Siparişiniz yaklaşık %s iş gününde kargoya verilir." % gun)
    if (p.get("ship") or {}).get("ucretsiz"):
        par.append("Bu üründe kargo ücretsizdir.")
    par.append("Stok ve fiyat bilgisi güncel tutulur; sorularınız için bize ulaşabilirsiniz.")
    kws = [x for x in dict.fromkeys([ad, marka, kat, model] + [v for _k, v in ozel[:2]] + list(p.get("tags") or [])[:4]) if x]
    return {"short": kisa, "desc": "\n\n".join(par),
            "seo_title": _kes(ilk + (" | " + kat if kat and len(ilk) < 45 else ""), 70),
            "seo_desc": _kes("%s%s" % (ilk, " – " + "; ".join("%s %s" % x for x in ozel[:2]) if ozel else "") + ". Hızlı kargo, güvenli ödeme.", 160),
            "seo_keywords": ", ".join(kws[:8]), "alt": _kes(ilk, 120)}


def _istem(p, alanlar, ton):
    bilgi = {k: p.get(k) for k in ("name", "brand", "model", "cat", "tags", "short") if p.get(k)}
    bilgi["ozellikler"] = [{x.get("k"): x.get("v")} for x in (p.get("specs") or [])][:20]
    if p.get("desc"):
        bilgi["mevcut_aciklama"] = _t(p["desc"], 800)
    sis = ("Türkçe e-ticaret ürün metni yazarsın. YALNIZ verilen bilgilere dayan; verilmeyen özellik, ölçü, garanti süresi, fiyat, "
           "sertifika ya da stok sözü uydurma. Abartılı iddia yok. Ton: %s. HTML kullanma, düz metin. "
           "Sadece JSON döndür; anahtarlar: %s. Sınırlar: short en çok 160, seo_title en çok 70, seo_desc en çok 160 karakter; "
           "desc 2-4 kısa paragraf; seo_keywords virgülle en çok 8; alt en çok 120 karakter.") % (ton, ", ".join(alanlar))
    return [{"role": "system", "content": sis}, {"role": "user", "content": json.dumps(bilgi, ensure_ascii=False)}]


def temizle(d, alanlar):
    lim = {"short": 160, "seo_title": 70, "seo_desc": 160, "seo_keywords": 200, "alt": 120, "desc": 4000}
    out = {}
    for k in alanlar:
        v = d.get(k)
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v)
        if v:
            out[k] = _kes(_t(v, lim[k] + 50), lim[k]) if k != "desc" else "\n\n".join(_t(x, 1200) for x in str(v).split("\n\n") if x.strip())[:4000]
    return out


def register(api_router, db, deps):
    adm = Depends(deps["require_admin"])

    @api_router.post("/yp/products/ai-text")
    async def ai_text(payload: dict, user: dict = adm):
        """Gövde: {product: {...düzenleyicideki alanlar}, alanlar: [...], ton}. Kaydetmez; öneri döner."""
        p = payload.get("product") or {}
        if not _t(p.get("name")):
            raise HTTPException(422, "Önce ürün adını yazın")
        alanlar = [a for a in (payload.get("alanlar") or ALANLAR) if a in ALANLAR] or list(ALANLAR)
        ton = _t(payload.get("ton") or "sade ve güven veren", 40)
        base = sablon(p)
        out, kaynak, uyari = {k: base[k] for k in alanlar}, "sablon", ""
        h = getattr(api_router, "ai_helpers", None)
        if h:
            try:
                c = await h["guard"](user)
                raw = await h["chat"](c, _istem(p, alanlar, ton), max_tokens=900, json_mode=True)
                d = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
                ai = temizle(d, alanlar)
                if ai:
                    out.update(ai)
                    kaynak = "ai"
            except HTTPException as e:
                uyari = str(e.detail)[:160]
            except Exception:                                      # noqa: BLE001
                uyari = "Yapay zekâ yanıtı okunamadı; şablon metin gösteriliyor"
        return {"ok": True, "kaynak": kaynak, "uyari": uyari, "oneri": out}
