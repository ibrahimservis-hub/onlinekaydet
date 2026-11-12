# -*- coding: utf-8 -*-
"""Çerez onay bandı: tek tuşla açılır, çerez politikası sayfası kendiliğinden gelir.

Band yalnız yerel depolamaya (localStorage) yazar, çerez kurmaz; bu yüzden bandın kendisi için
onay gerekmez. Ziyaretçi onaylayana kadar ölçüm/pazarlama betikleri çalışmaz: betikler
`window.okCerez.izin("olcum")` ya da `ok-cerez` olayıyla bekletilir (KVKK ve 6563 ile uyumlu
yaklaşım; hukuki danışman onayı önerilir).
"""
import html as _h
import re

VARSAYILAN = {
    "on": False,
    "text": "Bu sitede, sitenin düzgün çalışması için zorunlu çerezler kullanılır. "
            "İzin verirseniz ziyaret istatistiklerini de ölçeriz.",
    "accept": "Kabul et",
    "reject": "Yalnız zorunlu olanlar",
    "settings": "Çerez politikası",
    "pos": "alt",            # alt | üst | ortada pencere
    "link": "/cerez-politikasi",
    "olcum": True,           # ölçüm betikleri onay bekler
    "pazarlama": True,       # pazarlama betikleri onay bekler
    "ay": 12,                # kaç ay sonra yeniden sorulur
}
KONUM = ("alt", "üst", "ortada pencere")


def _t(v, n, d=""):
    v = re.sub(r"\s+", " ", str(v or "")).strip()[:n]
    return v or d


def temizle(x, eski=None):
    """Panelden gelen ayarları güvenli hâle getirir."""
    e = dict(VARSAYILAN, **(eski or {}))
    x = x if isinstance(x, dict) else {}
    out = dict(e)
    out["on"] = bool(x.get("on", e["on"]))
    out["text"] = _t(x.get("text", e["text"]), 400, VARSAYILAN["text"])
    out["accept"] = _t(x.get("accept", e["accept"]), 40, VARSAYILAN["accept"])
    out["reject"] = _t(x.get("reject", e["reject"]), 40)
    out["settings"] = _t(x.get("settings", e["settings"]), 40, VARSAYILAN["settings"])
    p = _t(x.get("pos", e["pos"]), 20)
    out["pos"] = p if p in KONUM else "alt"
    lk = _t(x.get("link", e["link"]), 200, VARSAYILAN["link"])
    out["link"] = lk if re.fullmatch(r"(/[A-Za-z0-9\-/_]{0,120}|https://[^\s\"'<>]{3,180})", lk) else VARSAYILAN["link"]
    out["olcum"] = bool(x.get("olcum", e["olcum"]))
    out["pazarlama"] = bool(x.get("pazarlama", e["pazarlama"]))
    try:
        ay = int(x.get("ay", e["ay"]))
    except (TypeError, ValueError):
        ay = VARSAYILAN["ay"]
    out["ay"] = min(max(ay, 1), 24)
    return out


def bekleyen(cfg):
    """Onaya bağlanan başlıklar."""
    return [k for k in ("olcum", "pazarlama") if cfg.get(k)]


def band(cfg, accent="#1155cc", dark="#15202e"):
    """Siteye eklenecek band. Kapalıysa boş döner."""
    cfg = dict(VARSAYILAN, **(cfg or {}))
    if not cfg.get("on"):
        return ""
    E = _h.escape
    pos = cfg["pos"]
    kutu = ("left:16px;right:16px;bottom:16px" if pos == "alt" else
            "left:16px;right:16px;top:16px" if pos == "üst" else
            "left:50%;top:50%;transform:translate(-50%,-50%);max-width:520px")
    ort = pos == "ortada pencere"
    red = ('<button type="button" data-ok-cerez="red" class="okc-b okc-g">%s</button>' % E(cfg["reject"])) if cfg.get("reject") else ""
    lnk = ('<a href="%s" class="okc-l">%s</a>' % (E(cfg["link"]), E(cfg["settings"]))) if cfg.get("settings") else ""
    bekle = ",".join('"%s"' % k for k in bekleyen(cfg))
    return (
        "<style>"
        "#okc{position:fixed;%(kutu)s;z-index:2147483000;background:%(dark)s;color:#fff;border-radius:14px;"
        "padding:16px 18px;box-shadow:0 10px 34px rgba(0,0,0,.28);font:15px/1.55 system-ui,-apple-system,'Segoe UI',sans-serif;"
        "display:none;gap:14px;align-items:center;flex-wrap:wrap}"
        "#okc.ac{display:flex}"
        "#okc.okc-ort{flex-direction:column;align-items:stretch;flex-wrap:nowrap}"
        "#okc.okc-ort p{flex:0 0 auto}#okc.okc-ort .okc-r{justify-content:flex-end}"
        "#okc p{margin:0;flex:1 1 300px;font-size:14.5px;color:#eef2f8}"
        "#okc .okc-r{display:flex;gap:9px;align-items:center;flex-wrap:wrap}"
        ".okc-b{min-height:42px;padding:0 18px;border-radius:9px;border:0;font:600 14.5px inherit;cursor:pointer;background:%(accent)s;color:#fff}"
        ".okc-g{background:transparent;border:1px solid rgba(255,255,255,.45);color:#fff}"
        ".okc-l{color:#cfe0ff;font-size:13.5px;text-decoration:underline;text-underline-offset:2px}"
        "#okc-ov{position:fixed;inset:0;background:rgba(8,14,24,.55);z-index:2147482999;display:none}"
        "#okc-ov.ac{display:block}"
        "@media(max-width:640px){#okc{left:10px;right:10px;%(mob)s;padding:14px;gap:10px}"
        "#okc .okc-r{width:100%%;flex-direction:column-reverse;align-items:stretch;gap:8px}"
        ".okc-b{width:100%%;white-space:nowrap}.okc-l{text-align:center;display:block;margin-top:2px}}"
        "</style>"
        "%(ov)s"
        "<div id=\"okc\" class=\"%(ortc)s\" role=\"dialog\" aria-live=\"polite\" aria-label=\"Çerez tercihi\">"
        "<p>%(text)s</p><div class=\"okc-r\">%(lnk)s%(red)s"
        "<button type=\"button\" data-ok-cerez=\"kabul\" class=\"okc-b\">%(kabul)s</button></div></div>"
        "<script>(function(){var A=%(ay)d,B=[%(bekle)s],K=\"ok_cerez\";"
        "function oku(){try{var v=JSON.parse(localStorage.getItem(K)||\"null\");"
        "if(!v||typeof v.t!==\"number\")return null;if(Date.now()-v.t>A*2629800000)return null;return v}catch(e){return null}}"
        "function yay(v){window.okCerez.onay=v.k;"
        "try{window.dispatchEvent(new CustomEvent(\"ok-cerez\",{detail:{onay:v.k,basliklar:B}}))}catch(e){}}"
        "window.okCerez={onay:null,basliklar:B,"
        "izin:function(b){return B.indexOf(b)<0||this.onay===true},"
        "sor:function(){ac()},"
        "bekle:function(b,f){if(this.izin(b))return f();window.addEventListener(\"ok-cerez\",function(){if(window.okCerez.izin(b))f()})}};"
        "var el,ov;function ac(){el&&el.classList.add(\"ac\");ov&&ov.classList.add(\"ac\")}"
        "function kapat(){el&&el.classList.remove(\"ac\");ov&&ov.classList.remove(\"ac\")}"
        "function yaz(k){var v={k:k,t:Date.now()};try{localStorage.setItem(K,JSON.stringify(v))}catch(e){}kapat();yay(v)}"
        "function kur(){el=document.getElementById(\"okc\");ov=document.getElementById(\"okc-ov\");"
        "var v=oku();if(v){yay(v);return}ac();"
        "document.addEventListener(\"click\",function(e){var t=e.target.closest&&e.target.closest(\"[data-ok-cerez]\");"
        "if(!t)return;e.preventDefault();yaz(t.getAttribute(\"data-ok-cerez\")===\"kabul\")})}"
        "if(document.readyState!==\"loading\")kur();else document.addEventListener(\"DOMContentLoaded\",kur)})();</script>"
    ) % {"kutu": kutu, "dark": dark, "accent": accent,
         "ortc": "okc-ort" if ort else "",
         "mob": "bottom:10px;top:auto;transform:none" if ort else ("bottom:10px" if pos == "alt" else "top:10px"),
         "ov": '<div id="okc-ov"></div>' if ort else "",
         "text": E(cfg["text"]), "lnk": lnk, "red": red, "kabul": E(cfg["accept"]),
         "ay": int(cfg["ay"]), "bekle": bekle}


def ekle(h, cfg, accent="#1155cc"):
    """Üretilmiş sayfaya bandı ekler."""
    b = band(cfg, accent)
    if not b or not h or "</body>" not in h:
        return h
    return h.replace("</body>", b + "</body>", 1)


def register(api_router, db, deps):
    from fastapi import Depends
    require_admin = deps["require_admin"]

    async def oku():
        return dict(VARSAYILAN, **((await db.app_settings.find_one({"_id": "cerez"}, {"_id": 0})) or {}))

    @api_router.get("/yp/cerez")
    async def cerez_get(_: dict = Depends(require_admin)):
        """Çerez bandı ayarları."""
        c = await oku()
        return {"cfg": c, "konumlar": list(KONUM), "bekleyen": bekleyen(c)}

    @api_router.put("/yp/cerez")
    async def cerez_put(payload: dict, _: dict = Depends(require_admin)):
        c = temizle(payload, await oku())
        await db.app_settings.update_one({"_id": "cerez"}, {"$set": c}, upsert=True)
        return {"ok": True, "cfg": c}
