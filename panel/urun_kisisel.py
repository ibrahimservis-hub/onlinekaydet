# -*- coding: utf-8 -*-
"""Ürün kişiselleştirme alanları: isim yazdırma, not, seçenek, hediye paketi gibi müşteriden alınan bilgiler.

Tanım ürün kaydında `personalization` listesidir. Alan başına: id, label, type (text | textarea | select | checkbox),
required, max, options (select için), fee (doldurulunca/işaretlenince ürün başına eklenen ücret), hint.
Fiyat ve zorunluluk sunucuda hesaplanır; tarayıcının gönderdiği tutara güvenilmez.
"""
import re

from fastapi import HTTPException

TIPLER = ("text", "textarea", "select", "checkbox")


def _t(v, n):
    return re.sub(r"[<>]", "", re.sub(r"\s+", " ", str(v or ""))).strip()[:n]


def _f(v):
    try:
        return max(0.0, round(float(str(v).replace(",", ".")), 2))
    except (TypeError, ValueError):
        return 0.0


def temizle(lst):
    """Panelden gelen tanımı güvenli hâle getirir (en çok 6 alan)."""
    out, used = [], set()
    for i, r in enumerate((lst or [])[:6]):
        if not isinstance(r, dict):
            continue
        label = _t(r.get("label"), 60)
        if not label:
            continue
        tip = r.get("type") if r.get("type") in TIPLER else "text"
        fid = re.sub(r"[^a-z0-9]", "", str(r.get("id") or "").lower())[:12] or ("f%d" % (i + 1))
        while fid in used:
            fid += "x"
        used.add(fid)
        opts = []
        if tip == "select":
            raw = r.get("options") or []
            if isinstance(raw, str):
                raw = raw.split(",")
            for o in raw[:20]:
                o = _t(o, 40)
                if o and o not in opts:
                    opts.append(o)
            if len(opts) < 2:
                tip = "text"
                opts = []
        try:
            mx = int(r.get("max") or (500 if tip == "textarea" else 60))
        except (TypeError, ValueError):
            mx = 60
        out.append({"id": fid, "label": label, "type": tip, "required": bool(r.get("required")),
                    "max": max(1, min(mx, 500)), "options": opts, "fee": _f(r.get("fee")), "hint": _t(r.get("hint"), 120)})
    return out


def uygula(p, values):
    """Müşterinin girdiği değerleri doğrular. ([{id,label,value,fee}], ürün başına ek ücret) döndürür; hata varsa 422."""
    defs = p.get("personalization") or []
    values = values if isinstance(values, dict) else {}
    out, fee = [], 0.0
    for d in defs:
        raw = values.get(d["id"])
        if d["type"] == "checkbox":
            val = "Evet" if raw in (True, "true", "1", 1, "Evet") else ""
        else:
            val = _t(raw, d.get("max", 60))
            if d["type"] == "select" and val and val not in (d.get("options") or []):
                raise HTTPException(422, "'%s' için geçersiz seçim" % d["label"])
        if d.get("required") and not val:
            raise HTTPException(422, "'%s' için %s bilgisini doldurun" % (p.get("name", "ürün"), d["label"]))
        if not val:
            continue
        f = float(d.get("fee") or 0)
        fee += f
        out.append({"id": d["id"], "label": d["label"], "value": val, "fee": f})
    return out, round(fee, 2)


def ozet(custom):
    """Sipariş satırında görünen kısa metin: 'Yazı: Ali · Hediye paketi: Evet'."""
    return " · ".join("%s: %s" % (c["label"], c["value"]) for c in (custom or []))
