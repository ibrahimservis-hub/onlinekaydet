"""Çok dilli site: dil ayarı, çeviri tablosu, /en gibi dil adresleri, dil seçici, sağdan sola yazım, otomatik çeviri.
Çeviri HTML düzeyinde çalışır: sayfadaki Türkçe metinler (başlık, açıklama, düğme, menü, alt/placeholder) bir tabloya çıkarılır,
karşılıkları varsa ziyaretçinin dilinde yerine konur. Hem bölüm motoru hem tema siteleri aynı yoldan çevrilir."""
import asyncio
import hashlib
import html as _h
import json
import re

import requests
from fastapi import Depends, HTTPException

LANGS = {"tr": ("Türkçe", "TR"), "en": ("English", "EN"), "de": ("Deutsch", "DE"), "ar": ("العربية", "AR"), "ru": ("Русский", "RU"),
         "fr": ("Français", "FR"), "es": ("Español", "ES"), "nl": ("Nederlands", "NL"), "it": ("Italiano", "IT"), "az": ("Azərbaycanca", "AZ")}
RTL = {"ar"}
_EN, _EN_DE = ["en"], ["en", "de"]
SEKTOR_DIL = {  # sektör paketi -> önerilen başlangıç dilleri (ana dil hariç)
    "kuafor": _EN, "teknik": _EN, "oto": _EN_DE, "veteriner": _EN, "otel": ["en", "de", "ru", "ar"], "fitness": _EN, "market": _EN,
    "eticaret": _EN, "lokanta": ["en", "de", "ar"], "emlak": ["en", "ar", "ru"], "avukat": _EN, "saglik": ["en", "ar"], "surucu": _EN,
    "kurs": _EN, "temizlik": _EN, "organizasyon": _EN_DE,
}
DEF = {"on": False, "ana": "tr", "diller": [], "tarayici": True, "adresli": True, "rtl": True, "gorunum": "ad"}
_SKIP = re.compile(r"(<script\b.*?</script>|<style\b.*?</style>|<noscript\b.*?</noscript>|<svg\b.*?</svg>)", re.S | re.I)
_TXT = re.compile(r">([^<>]+)<")
_EXT = re.compile(r"\.(css|js|png|jpe?g|gif|webp|svg|ico|xml|txt|pdf|json|woff2?)(\?|$)", re.I)


def key(s):
    return hashlib.sha1(s.strip().encode("utf-8")).hexdigest()[:16]


def _ok(t):
    t = _h.unescape(t).strip()
    return 2 <= len(t) <= 400 and re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]{2}", t) and not re.fullmatch(r"[\W\d_]+", t)


def extract(html):
    """Sayfadaki çevrilebilir metinler (sıralı, tekrarsız)."""
    out, seen = [], set()
    for part in _SKIP.split(html):
        if _SKIP.fullmatch(part or ""):
            continue
        cands = [m.group(1) for m in _TXT.finditer(part)]
        cands += re.findall(r'\b(?:alt|placeholder|title)="([^"<>]+)"', part)
        cands += re.findall(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', part)
        for c in cands:
            t = _h.unescape(c).strip()
            if _ok(t) and t not in seen:
                seen.add(t)
                out.append(t)
    return out


def translate_html(html, tr):
    """tr: {kaynak metin: çeviri}. Boşluk düzenini koruyarak değiştirir."""
    if not tr:
        return html

    def rep_text(m):
        raw = m.group(1)
        t = _h.unescape(raw).strip()
        v = tr.get(t)
        return (">" + raw.replace(raw.strip(), _h.escape(v, quote=False), 1) + "<") if v else m.group(0)

    def rep_attr(m):
        v = tr.get(_h.unescape(m.group(2)).strip())
        return '%s="%s"' % (m.group(1), _h.escape(v)) if v else m.group(0)

    def rep_meta(m):
        v = tr.get(_h.unescape(m.group(2)).strip())
        return m.group(1) + _h.escape(v) + m.group(3) if v else m.group(0)
    out = []
    for part in _SKIP.split(html):
        if not part or _SKIP.fullmatch(part):
            out.append(part or "")
            continue
        part = _TXT.sub(rep_text, part)
        part = re.sub(r'\b(alt|placeholder|title)="([^"<>]+)"', rep_attr, part)
        part = re.sub(r'(<meta[^>]+name="description"[^>]+content=")([^"]+)(")', rep_meta, part)
        out.append(part)
    return "".join(out)


def prefix_links(html, lang):
    def rep(m):
        u = m.group(3)
        if u.startswith(("/api", "/static", "/uploads", "//")) or _EXT.search(u):
            return m.group(0)
        return m.group(1) + m.group(2) + "/" + lang + (u if u != "/" else "") + m.group(2)
    return re.sub(r'(<a\b[^>]*?\bhref=)(["\'])(/[^"\']*)\2', rep, html)


def selector(cfg, cur, rest):
    langs = [cfg["ana"]] + [d for d in cfg["diller"] if d != cfg["ana"]]
    if len(langs) < 2:
        return ""
    opts = []
    for c in langs:
        nm, kd = LANGS.get(c, (c, c.upper()))
        lab = {"ad": nm, "kod": kd, "bayrak": kd}.get(cfg.get("gorunum"), nm)
        href = ("/" if c == cfg["ana"] else "/" + c + "/") + rest.lstrip("/") if cfg.get("adresli") else "?dil=" + c
        opts.append('<a href="%s" data-d="%s"%s>%s</a>' % (_h.escape(href), c, ' class="on"' if c == cur else "", _h.escape(lab)))
    nm = LANGS.get(cur, (cur, cur.upper()))[0]
    css = ("<style>.okdil{position:fixed;left:14px;bottom:14px;z-index:9500;font:600 13px system-ui,sans-serif}"
           ".okdil>b{display:block;background:#fff;color:#0a1f44;border:1px solid #cfd5e2;border-radius:10px;padding:8px 12px;cursor:pointer;box-shadow:0 4px 16px #0a1f4426}"
           ".okdil div{display:none;position:absolute;bottom:42px;left:0;min-width:140px;background:#fff;border-radius:10px;box-shadow:0 8px 28px #0a1f4430;padding:6px}"
           ".okdil.ac div{display:block}.okdil a{display:block;padding:8px 10px;border-radius:6px;color:#0a1f44;text-decoration:none;font-weight:500}"
           ".okdil a.on{background:#fff3e8;color:#f27a1a;font-weight:700}[dir=rtl] .okdil{left:auto;right:14px}@media(max-width:860px){.okdil{bottom:84px}.okdil div{bottom:42px}}</style>")
    js = ("<script>(function(){var b=document.querySelector('.okdil');b.firstChild.onclick=function(){b.classList.toggle('ac')};"
          "b.querySelectorAll('a').forEach(function(a){a.onclick=function(){document.cookie='dil='+a.dataset.d+';path=/;max-age=31536000'}});"
          "var m=document.cookie.match(/(?:^|; )dil=(\\w+)/);if(!m&&%s){var n=(navigator.language||'').slice(0,2),ok=%s;"
          "if(n!==%s&&ok.indexOf(n)>=0){document.cookie='dil='+n+';path=/;max-age=31536000';var t=b.querySelector('a[data-d=\"'+n+'\"]');if(t&&t.href&&%s)location.href=t.href}}})()</script>"
          % ("true" if cfg.get("tarayici") else "false", json.dumps(langs), json.dumps(cur), "true" if cfg.get("adresli") else "false"))
    return css + '<div class="okdil"><b>🌐 %s ▾</b><div>%s</div></div>' % (_h.escape(nm), "".join(opts)) + js


def apply_page(html, cfg, cur, rest, tr):
    """Ziyaretçinin diline göre sayfayı çevirir, seçici ve dil işaretlerini ekler."""
    if cur != cfg["ana"]:
        html = translate_html(html, tr)
        if cfg.get("adresli"):
            html = prefix_links(html, cur)
    html = re.sub(r"<html\b([^>]*?)>", lambda m: "<html%s lang=\"%s\"%s>" % (re.sub(r'\s(lang|dir)="[^"]*"', "", m.group(1)), cur, ' dir="rtl"' if cfg.get("rtl") and cur in RTL else ""), html, 1)
    alt = "".join('<link rel="alternate" hreflang="%s" href="%s">' % (c, ("/" if c == cfg["ana"] else "/" + c + "/") + rest.lstrip("/"))
                  for c in [cfg["ana"]] + cfg["diller"]) if cfg.get("adresli") else ""
    if alt and "</head>" in html:
        html = html.replace("</head>", alt + "</head>", 1)
    sel = selector(cfg, cur, rest)
    if sel and "</body>" in html:
        html = html.replace("</body>", sel + "</body>", 1)
    return html


async def get_cfg(db, sector=""):
    d = await db.app_settings.find_one({"_id": "yp_dil"}, {"_id": 0}) or {}
    c = dict(DEF, **{k: v for k, v in d.items() if k in DEF})
    if "diller" not in d:
        c["diller"] = list(SEKTOR_DIL.get(sector, ["en"]))
    c["diller"] = [x for x in c["diller"] if x in LANGS and x != c["ana"]]
    return c


async def sektor(db):
    d = await db.app_settings.find_one({"_id": "yp_pack"}, {"_id": 0}) or {}
    s = d.get("sector")
    if not s:
        s = (await db.app_settings.find_one({"_id": "sector"}, {"_id": 0}) or {}).get("key") or ""
    return s


async def parse_path(db, path):
    """('en', 'hizmetler') ya da (ana dil, yol). Dil kapalıysa dokunmaz."""
    p = (path or "/").split("?")[0].strip("/")
    cfg = await get_cfg(db, await sektor(db))
    if not cfg["on"]:
        return None, path, cfg
    first, _, rest = p.partition("/")
    if first in cfg["diller"] and cfg.get("adresli"):
        return first, "/" + rest, cfg
    return cfg["ana"], path, cfg


async def tablo(db, lang):
    rows = await db.yp_ceviri.find({"lang": lang}, {"_id": 0, "src": 1, "text": 1}).to_list(5000)
    return {r["src"]: r["text"] for r in rows if r.get("text")}


def _chunks(a, n):
    for i in range(0, len(a), n):
        yield a[i:i + n]


def register(api_router, db, deps):
    adm = deps["require_admin"]

    async def ek_metinler():
        """Panelden girilen içerikler: sayfada o an görünmese de (ör. 20'den sonraki ürünler) çeviri tablosuna girsin. {metin: tür}"""
        out = {}

        async def al(col, alanlar, tur, flt=None, n=300):
            try:
                async for r in getattr(db, col).find(flt or {}, {"_id": 0, **{a: 1 for a in alanlar}}).limit(n):
                    for a in alanlar:
                        v = re.sub(r"\s+", " ", str(r.get(a) or "")).strip()
                        if 2 <= len(v) <= 240 and re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", v):
                            out.setdefault(v, tur)
            except Exception:                                      # noqa: BLE001
                pass
        await al("shop_products", ["name", "short"], "Ürün", {"active": True})
        await al("shop_categories", ["name"], "Kategori")
        await al("yp_services", ["name"], "Hizmet")
        await al("yp_pages", ["title"], "Sayfa", {"status": "live"}, 60)
        return out

    async def metinler():
        raw = getattr(api_router, "site_render_raw", None)
        slugs = [""]
        async for p in db.yp_pages.find({"status": "live"}, {"_id": 0, "slug": 1, "home": 1}):
            if p.get("slug") and not p.get("home"):
                slugs.append(p["slug"])
        out, seen = [], set()
        # mağaza açıksa vitrin ve ürün sayfaları da çevrilir (ürün adı, açıklama, düğmeler)
        try:
            ft = await db.app_settings.find_one({"_id": "site_features"}, {"_id": 0, "shop_enabled": 1}) or {}
            if ft.get("shop_enabled"):
                slugs.append("magaza")
                async for pr in db.shop_products.find({"active": True}, {"_id": 0, "slug": 1, "id": 1}).limit(20):
                    slugs.append("magaza/urun/" + (pr.get("slug") or pr.get("id") or ""))
        except Exception:                                          # noqa: BLE001
            pass
        for s in slugs[:60]:
            try:
                r = await raw("/" + s) if raw else None
            except Exception:                                      # noqa: BLE001
                r = None
            if r and r[1] == "text/html":
                for t in extract(r[0]):
                    if t not in seen:
                        seen.add(t)
                        out.append(t)
        for k in await ek_metinler():
            if k not in seen:
                seen.add(k)
                out.append(k)
        return out[:1500]

    @api_router.get("/yp/dil")
    async def dil_get(_: dict = Depends(adm)):
        cfg = await get_cfg(db, await sektor(db))
        prog = {}
        tx = await metinler()
        for c in cfg["diller"]:
            t = await tablo(db, c)
            ok = sum(1 for x in tx if x in t)
            prog[c] = {"hazir": ok, "toplam": len(tx), "yuzde": int(100 * ok / len(tx)) if tx else 0}
        return {"cfg": cfg, "diller": [{"id": k, "ad": v[0], "kod": v[1], "rtl": k in RTL} for k, v in LANGS.items()],
                "ilerleme": prog, "oneri": SEKTOR_DIL.get(await sektor(db), ["en"])}

    @api_router.put("/yp/dil")
    async def dil_put(payload: dict, _: dict = Depends(adm)):
        cur = await get_cfg(db, await sektor(db))
        u = {}
        for k in ("on", "tarayici", "adresli", "rtl"):
            if k in payload:
                u[k] = bool(payload[k])
        if payload.get("gorunum") in ("ad", "kod", "bayrak"):
            u["gorunum"] = payload["gorunum"]
        if payload.get("ana") in LANGS:
            u["ana"] = payload["ana"]
        if isinstance(payload.get("diller"), list):
            u["diller"] = [x for x in dict.fromkeys(payload["diller"]) if x in LANGS][:9]
        cur.update(u)
        cur["diller"] = [x for x in cur["diller"] if x != cur["ana"]]
        await db.app_settings.update_one({"_id": "yp_dil"}, {"$set": cur}, upsert=True)
        return cur

    @api_router.get("/yp/dil/ceviri")
    async def ceviri_list(lang: str, _: dict = Depends(adm)):
        if lang not in LANGS:
            raise HTTPException(404, "Dil bulunamadı")
        t = await tablo(db, lang)
        tur = await ek_metinler()
        rows = [{"k": key(x), "src": x, "text": t.get(x, ""), "durum": "hazir" if x in t else "eksik", "tur": tur.get(x, "Sayfa metni")} for x in await metinler()]
        return {"rows": rows, "eksik": sum(1 for r in rows if r["durum"] == "eksik")}

    @api_router.put("/yp/dil/ceviri")
    async def ceviri_put(payload: dict, _: dict = Depends(adm)):
        lang = payload.get("lang")
        if lang not in LANGS:
            raise HTTPException(404, "Dil bulunamadı")
        n = 0
        for it in (payload.get("items") or [])[:500]:
            src, text = str(it.get("src") or "").strip()[:400], str(it.get("text") or "").strip()[:800]
            if not src:
                continue
            if text:
                await db.yp_ceviri.update_one({"lang": lang, "src": src}, {"$set": {"text": text, "by": "elle"}}, upsert=True)
            else:
                await db.yp_ceviri.delete_one({"lang": lang, "src": src})
            n += 1
        return {"ok": True, "n": n}

    def _llm(c, lang, texts):
        body = {"model": c.get("chat_model") or "gpt-4o-mini", "temperature": 0.2, "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": "Bir web sitesinin Türkçe metinlerini %s diline çevir. Kısa, doğal ve pazarlama diline uygun yaz. "
                              "Sayıları, marka adlarını, telefonları değiştirme. Yalnızca JSON döndür: {\"t\":[çeviriler]} — aynı sayıda ve aynı sırada." % LANGS[lang][0]},
                             {"role": "user", "content": json.dumps(texts, ensure_ascii=False)}]}
        r = requests.post(c["base_url"].rstrip("/") + "/chat/completions", headers={"Authorization": "Bearer " + c["api_key"]}, json=body, timeout=90)
        r.raise_for_status()
        out = json.loads(r.json()["choices"][0]["message"]["content"]).get("t") or []
        return out if len(out) == len(texts) else []

    @api_router.post("/yp/dil/oto")
    async def ceviri_oto(payload: dict, _: dict = Depends(adm)):
        lang = payload.get("lang")
        if lang not in LANGS or lang == "tr":
            raise HTTPException(422, "Geçerli bir dil seçin")
        c = await db.app_settings.find_one({"_id": "ai"}, {"_id": 0}) or {}
        if not (c.get("enabled") and c.get("api_key")):
            raise HTTPException(400, "Otomatik çeviri için önce Ayarlar › Yapay zekâ bölümünde bağlantı anahtarını girip açın.")
        c.setdefault("base_url", "https://api.openai.com/v1")
        t = await tablo(db, lang)
        todo = [x for x in await metinler() if x not in t][:200]
        done = 0
        for ch in _chunks(todo, 25):
            try:
                out = await asyncio.to_thread(_llm, c, lang, ch)
            except Exception as e:                                 # noqa: BLE001
                raise HTTPException(502, "Çeviri servisi yanıt vermedi: %s" % str(e)[:120])
            for src, tx in zip(ch, out):
                if isinstance(tx, str) and tx.strip():
                    await db.yp_ceviri.update_one({"lang": lang, "src": src}, {"$set": {"text": tx.strip()[:800], "by": "otomatik"}}, upsert=True)
                    done += 1
        return {"ok": True, "cevrilen": done, "kalan": max(0, len(todo) - done)}

    @api_router.get("/public/dil")
    async def dil_public():
        cfg = await get_cfg(db, await sektor(db))
        return {"on": cfg["on"], "ana": cfg["ana"], "diller": [{"id": c, "ad": LANGS[c][0]} for c in [cfg["ana"]] + cfg["diller"]] if cfg["on"] else []}
