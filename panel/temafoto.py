# -*- coding: utf-8 -*-
"""Tema görselleri: iç sayfalarda ve tema önizlemelerinde kullanılan sektör fotoğrafları.
Gerçek fotoğraf (themes/img, sektör başına 3 adet) varsa o, yoksa tema üretiminde kullanılan çizim sunulur. Müşteri kendi resmini panelden yükleyince onun resmi öncelikli olur."""
import json
import os
import re
import sys

from fastapi import HTTPException, Response

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "..", "themes", "img")
_MAP = {}
try:
    _MAP = json.load(open(os.path.join(HERE, "sektor_foto.json"), encoding="utf-8"))
except Exception:                                                    # noqa: BLE001
    pass
GERCEK = {"beyaz", "bilgisayar", "elektrik", "elektronik", "guvenlik", "klima", "kombi", "tesisat"}   # depoda gerçek fotoğrafı bulunanlar


_OK = {}


def _var(name):
    if name not in _OK:
        try:
            _bytes(name, 1)
            _OK[name] = True
        except Exception:                                            # noqa: BLE001
            _OK[name] = False
    return _OK[name]


def sector_imgs(sector):
    """Sektörün üç görselinin adresleri (görsel yoksa liste boş; sayfa görselsiz düzene döner)."""
    n = _MAP.get(sector or "")
    return ["/api/public/tema-foto/%s-%d" % (n, i) for i in (1, 2, 3)] if n and _var(n) else []


def _bytes(name, i):
    stem = name + ("" if i == 1 else str(i))
    f = os.path.join(IMG, stem + ".jpg")
    if os.path.exists(f) and (name in GERCEK or os.path.exists(os.path.join(IMG, ".real"))):
        return open(f, "rb").read(), "image/jpeg"
    try:
        sys.path.insert(0, os.path.join(HERE, "..", "themes", "ill"))
        import make_ill
        return make_ill.svg_for(stem).encode("utf-8"), "image/svg+xml"
    except Exception:                                                # noqa: BLE001
        if os.path.exists(f):
            return open(f, "rb").read(), "image/jpeg"
    raise HTTPException(404, "Yok")


def register(api_router):
    @api_router.get("/public/tema-thumb/{slug}")
    async def tema_thumb(slug: str):
        f = os.path.join(HERE, "tema_thumb", slug + ".webp")
        if not re.fullmatch(r"[a-z0-9-]{3,60}", slug) or not os.path.isfile(f):
            raise HTTPException(404, "Yok")
        return Response(open(f, "rb").read(), media_type="image/webp", headers={"Cache-Control": "public, max-age=86400"})

    @api_router.get("/public/tema-foto/{name}-{i}")
    async def tema_foto(name: str, i: int):
        if not re.fullmatch(r"[a-z0-9_]{2,40}", name) or i not in (1, 2, 3) or name not in set(_MAP.values()):
            raise HTTPException(404, "Yok")
        b, m = _bytes(name, i)
        return Response(b, media_type=m, headers={"Cache-Control": "public, max-age=86400", "Content-Security-Policy": "sandbox"})
