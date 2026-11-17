# -*- coding: utf-8 -*-
"""Etiket tasarımı: kargo şablonu (A4 fiş), kargo etiketi (A6 / 10x15) ve restoran QR etiketi.

Üçü de müşteri panelinden tasarlanır: stil, renk, yazı tipi, köşe, boyut, hangi alanların
görüneceği ve kendi metinleri. Firma adı, telefon, adres ve logo ayarlardan kendiliğinden gelir;
kullanıcı her etikete elle yazmaz. Önizleme ile baskı aynı üreticiyi kullanır.
"""
import re

import barkod
import qr as QR

FONTS = {"sans": "-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif",
         "serif": "Georgia,'Times New Roman',serif",
         "mono": "ui-monospace,'SF Mono',Menlo,Consolas,monospace",
         "yuvarlak": "'Trebuchet MS','Segoe UI',Verdana,sans-serif"}
FONT_AD = {"sans": "Sade", "serif": "Klasik (serif)", "mono": "Daktilo", "yuvarlak": "Yumuşak"}

KARGO_BOY = {"a6": ("105mm", "148mm", "A6 (105×148 mm)"), "10x15": ("100mm", "150mm", "Termal 10×15 cm"),
             "a5": ("148mm", "210mm", "A5 (148×210 mm)")}
QR_BOY = {"a4-4": "A4 — sayfada 4 kart", "a4-6": "A4 — sayfada 6 kart", "a5": "A5 — sayfada 1 kart",
          "10x15": "10×15 cm — masa standı"}
FIS_BOY = {"a4": "A4", "a5": "A5"}

STIL = {
    "fis": [("klasik", "Klasik", "Çizgili, resmi belge"), ("serit", "Renkli şerit", "Üstte renkli başlık bandı"),
            ("minimal", "Sade", "İnce çizgi, bol boşluk")],
    "etiket": [("klasik", "Klasik", "Kutulu, kargo firması düzeni"), ("serit", "Renkli şerit", "Üstte renkli başlık"),
               ("kalin", "Kalın çerçeve", "Alıcı adı çok büyük, kalın çerçeve"),
               ("minimal", "Sade", "İnce çizgi"), ("termal", "Termal (siyah-beyaz)", "Termal yazıcı için tek renk")],
    "qr": [("logo-ust", "Logo üstte", "Üstte logo, altında QR"), ("cerceve", "Çift çerçeve", "Çerçeveli kart"),
           ("koyu", "Koyu zemin", "Koyu kart, beyaz QR paneli"), ("serit", "Şeritli", "Renkli üst ve alt bant"),
           ("minimal", "Sade", "Yalnız logo ve QR")],
}

DEF = {
    "fis": {"stil": "klasik", "renk": "#101828", "vurgu": "#e11d48", "font": "sans", "boyut": "a4", "logo": True,
            "tel": True, "adres": True, "imza": True, "alt": "Bizi tercih ettiğiniz için teşekkür ederiz.", "koseler": 8},
    "etiket": {"stil": "klasik", "renk": "#0f172a", "vurgu": "#e11d48", "font": "sans", "boyut": "a6", "logo": True,
               "tel": True, "adres": True, "barkod": True, "icerik": True, "not": True, "alt": "", "koseler": 8},
    "qr": {"stil": "logo-ust", "renk": "#101828", "vurgu": "#e11d48", "font": "sans", "boyut": "a4-4", "logo": True,
           "firma": True, "masa": True, "url": True, "baslik": "Menü", "not": "Kareyi kamerayla okutun",
           "alt": "", "koseler": 14, "kesik": True},
}
BOOLS = {"fis": ("logo", "tel", "adres", "imza"), "etiket": ("logo", "tel", "adres", "barkod", "icerik", "not"),
         "qr": ("logo", "firma", "masa", "url", "kesik")}
TEXTS = {"fis": {"alt": 160}, "etiket": {"alt": 100}, "qr": {"baslik": 40, "not": 120, "alt": 100}}
BOYUTLAR = {"fis": set(FIS_BOY), "etiket": set(KARGO_BOY), "qr": set(QR_BOY)}
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def temiz(tip: str, gelen: dict, eski: dict = None) -> dict:
    """Gelen ayarı doğrula; geçersiz değer sessizce varsayılana/eskiye döner (baskı bozulmasın)."""
    cfg = dict(DEF[tip])
    cfg.update({k: v for k, v in (eski or {}).items() if k in cfg})
    g = gelen or {}
    if g.get("stil") in {s[0] for s in STIL[tip]}:
        cfg["stil"] = g["stil"]
    for k in ("renk", "vurgu"):
        if isinstance(g.get(k), str) and HEX.match(g[k]):
            cfg[k] = g[k].lower()
    if g.get("font") in FONTS:
        cfg["font"] = g["font"]
    if g.get("boyut") in BOYUTLAR[tip]:
        cfg["boyut"] = g["boyut"]
    for k in BOOLS[tip]:
        if k in g:
            cfg[k] = bool(g[k])
    for k, n in TEXTS[tip].items():
        if k in g:
            cfg[k] = str(g[k] or "").strip()[:n]
    if "koseler" in g:
        try:
            cfg["koseler"] = max(0, min(int(g["koseler"]), 28))
        except (TypeError, ValueError):
            pass
    return cfg


def _e(v):
    return str(v or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _tel(v):
    d = "".join(ch for ch in str(v or "") if ch.isdigit())
    return "%s %s %s %s" % (d[:4], d[4:7], d[7:9], d[9:]) if len(d) == 11 else str(v or "")


def _n(v):
    try:
        return ("%.2f" % float(v)).replace(".", ",")
    except (TypeError, ValueError):
        return "0,00"


def _ink(hexc: str) -> str:
    """Arka plan renginde okunur yazı rengi (beyaz/siyah)."""
    h = hexc.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#101828" if (0.299 * r + 0.587 * g + 0.114 * b) > 165 else "#ffffff"


def _logo(info: dict, cfg: dict, cls="lg"):
    """Logo varsa görsel; yoksa firma adının baş harfleriyle yazı işareti. Kapalıysa boş."""
    if not cfg.get("logo"):
        return ""
    if info.get("logo"):
        return '<img class="%s" src="%s" alt="">' % (cls, _e(info["logo"]))
    ad = (info.get("ad") or "").strip()
    if not ad:
        return ""
    ini = "".join(w[0] for w in ad.split()[:2]).upper()
    return '<span class="%s mn">%s</span>' % (cls, _e(ini))


def _firma_blok(info: dict, cfg: dict, ad=True):
    p = []
    if ad and info.get("ad"):
        p.append("<b>%s</b>" % _e(info["ad"]))
    if cfg.get("tel") and info.get("tel"):
        p.append("<span>%s</span>" % _e(_tel(info["tel"])))
    if cfg.get("adres") and info.get("adres"):
        p.append("<span>%s</span>" % _e(info["adres"]))
    return "<div class='fb'>%s</div>" % "".join(p) if p else ""


def _vars(cfg):
    return ("--c:%s;--a:%s;--ci:%s;--ai:%s;--r:%dpx;font-family:%s" %
            (cfg["renk"], cfg["vurgu"], _ink(cfg["renk"]), _ink(cfg["vurgu"]), cfg["koseler"], FONTS[cfg["font"]]))


EKRAN = ("@media screen{html{background:#e4e7ec}body{padding:14px 0}.sy{background:#fff;margin:0 auto 14px;"
         "box-shadow:0 1px 3px #1018281f,0 8px 24px #10182814}}")
TEMEL = "*{box-sizing:border-box;margin:0}img{display:block}svg{max-width:100%;height:auto}"
MONO = (".mn{display:inline-grid;place-items:center;border-radius:50%;background:var(--c);color:var(--ci);"
        "font-weight:700;letter-spacing:.02em}")


def _sar(baslik, css, govde, otomatik=True):
    js = "<script>window.onload=function(){setTimeout(function(){window.print()},300)}</script>" if otomatik else ""
    return ("<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>%s</title><style>%s</style></head>"
            "<body>%s%s</body></html>" % (_e(baslik), css, govde, js))


# ======================================================================================= KARGO ETİKETİ
def _bk(kod):
    kod = str(kod or "")
    m = 2.1 if len(kod) <= 12 else 1.6 if len(kod) <= 18 else 1.2
    return barkod.svg(kod, height=58, module=m)


def etiket_html(orders, cfg, info, otomatik=True):
    w, h, _ad = KARGO_BOY[cfg["boyut"]]
    st = cfg["stil"]
    termal = st == "termal"
    c, a = ("#000000", "#000000") if termal else (cfg["renk"], cfg["vurgu"])
    cfg2 = dict(cfg, renk=c, vurgu=a)
    css = (TEMEL + "@page{size:%s %s;margin:0}" % (w, h) + EKRAN + MONO
           + ".sy{width:%s;height:%s;overflow:hidden;page-break-after:always;position:relative;color:#101828;--cw:%s;--c:%s;--a:%s;--ci:%s;--ai:%s;--r:%dpx;font-family:%s}"
           % (w, h, w, c, a, _ink(c), _ink(a), 0 if termal else cfg["koseler"], FONTS[cfg["font"]])
           + ".sy:last-child{page-break-after:auto}"
           ".l{display:flex;flex-direction:column;height:100%;padding:4mm;gap:2.4mm;font-size:9.5pt;line-height:1.3}"
           ".hd{display:flex;align-items:center;gap:3mm}.lg{max-height:11mm;max-width:26mm;object-fit:contain}"
           ".mn.lg{width:11mm;height:11mm;font-size:12pt}.fb{display:flex;flex-direction:column;font-size:7.5pt;line-height:1.25;min-width:0}"
           ".fb b{font-size:9pt}.kg{margin-left:auto;text-align:right}.kg b{display:block;font-size:12pt;letter-spacing:.02em}"
           ".kg span{font:600 8pt ui-monospace,Menlo,monospace}"
           ".al{border:1px solid var(--c);border-radius:var(--r);padding:2.6mm 3mm}.al small,.bx small{display:block;font-size:6.5pt;"
           "letter-spacing:.09em;text-transform:uppercase;opacity:.65;margin-bottom:.8mm}"
           ".al .ad{font-size:15pt;font-weight:700;line-height:1.15}.al .tl{font:600 10.5pt ui-monospace,Menlo,monospace;margin-top:.6mm}"
           ".al .adr{font-size:10.5pt;margin-top:1mm;line-height:1.3}"
           ".bcw{text-align:center;border:1px solid var(--c);border-radius:var(--r);padding:2mm 2mm 1mm}.bcw small{display:block;font-size:6.5pt;letter-spacing:.09em;text-transform:uppercase;opacity:.65}"
           ".bcw svg{margin:1mm auto 0;width:100%;max-height:19mm}"
           ".ft{display:flex;gap:2mm;margin-top:auto;align-items:stretch}.ft div{flex:1;border:1px solid var(--c);border-radius:var(--r);padding:1.6mm 2.2mm;font-size:8.5pt}"
           ".ft small{display:block;font-size:6pt;letter-spacing:.09em;text-transform:uppercase;opacity:.65}.ft b{font-size:11pt}"
           ".ft .od{background:var(--a);color:var(--ai);border-color:var(--a)}.nt{font-size:8pt;border-left:2px solid var(--a);padding-left:2mm}"
           ".sl{font-size:7pt;text-align:center;opacity:.7}"
           ".ic{margin-top:auto;font-size:8.5pt;line-height:1.35}.ic small{display:block;font-size:6.5pt;letter-spacing:.09em;text-transform:uppercase;opacity:.65;margin-bottom:.6mm}"
           ".ic+.ft{margin-top:0}")
    if st == "serit":
        css += (".hd{margin:-4mm -4mm 0;padding:3.2mm 4mm;background:var(--c);color:var(--ci)}.hd .fb{color:var(--ci)}"
                ".hd .lg{background:#fff;border-radius:calc(var(--r)/1.6);padding:1mm}.hd .mn.lg{background:#fff;color:var(--c)}"
                ".al{border-color:transparent;background:#f2f4f7}.bcw,.ft div{border-color:#d0d5dd}.ft .od{border-color:var(--a)}")
    elif st == "kalin":
        css += (".l{border:2.2mm solid var(--c);border-radius:calc(var(--r)*1.2)}.al{border:0;padding:1mm 0}"
                ".al .ad{font-size:21pt;font-weight:800;line-height:1.05}.al .adr{font-size:12pt}.al .tl{font-size:12pt}"
                ".al small{color:var(--a);opacity:1;font-weight:700}.bcw{border:0;border-top:.6mm solid var(--c);border-radius:0}"
                ".ft div{border:0;border-top:.6mm solid var(--c);border-radius:0;padding:1.6mm 0}.ft .od{padding:1.6mm 2.4mm;border-radius:var(--r)}")
    elif st == "minimal":
        css += (".al,.bcw,.ft div{border:0;border-bottom:.3mm solid #98a2b3;border-radius:0;padding-left:0;padding-right:0}"
                ".ft .od{background:none;color:inherit;border-bottom:.6mm solid var(--a)}.ft .od b{color:var(--a)}.hd{padding-bottom:2mm;border-bottom:.3mm solid #98a2b3}")
    elif st == "termal":
        css += (".al,.bcw,.ft div{border-width:.5mm;border-color:#000}.ft .od{background:#000;color:#fff}.nt{border-color:#000}"
                ".mn{background:#000;color:#fff}.al .ad{font-size:17pt;font-weight:800}")
    out = []
    for o in orders:
        c_ = o.get("customer") or {}
        adr = " ".join(x for x in [c_.get("address"), c_.get("district"), c_.get("city")] if x)
        cg = o.get("cargo") or {}
        kod = (cg.get("barcode") or cg.get("code") or o.get("no") or "")
        kodad = "Gönderi barkodu" if cg.get("barcode") else ("Kargo takip no" if cg.get("code") else "Sipariş no")
        cargo_ad = o.get("cargo_name") or ""
        adet = sum(int(i.get("qty") or 1) for i in o.get("items") or [])
        kapida = not o.get("paid")
        hd = ("<div class='hd'>%s%s<div class='kg'><b>%s</b><span>%s</span></div></div>"
              % (_logo(info, cfg2), _firma_blok(info, cfg2), _e(cargo_ad or "KARGO"), _e(o.get("no"))))
        al = ("<div class='al'><small>Alıcı</small><div class='ad'>%s</div><div class='tl'>%s</div><div class='adr'>%s</div></div>"
              % (_e(c_.get("name")) or "—", _e(_tel(c_.get("phone"))), _e(adr) or "—"))
        bc = ("<div class='bcw'><small>%s</small>%s</div>" % (kodad, _bk(kod))) if cfg["barkod"] and kod else ""
        ft = ""
        if cfg["icerik"]:
            its = o.get("items") or []
            lst = "".join("<div><b>%s×</b> %s</div>" % (int(i.get("qty") or 1), _e(str(i.get("name") or "")[:46])) for i in its[:4])
            if len(its) > 4:
                lst += "<div>+%d ürün daha</div>" % (len(its) - 4)
            ft = ("<div class='ic'><small>İçerik</small>%s</div>" % lst if lst else "") + ("<div class='ft'><div><small>Ürün</small><b>%d adet</b></div><div><small>Tutar</small><b>%s ₺</b></div>"
                  "<div class='%s'><small>Ödeme</small><b>%s</b></div></div>"
                  % (adet, _n(o.get("total")), "od" if kapida else "", "Kapıda öde" if kapida else "Ödendi"))
        nt = ("<div class='nt'>%s</div>" % _e(o.get("note"))) if cfg["not"] and o.get("note") else ""
        sl = ("<div class='sl'>%s</div>" % _e(cfg["alt"])) if cfg["alt"] else ""
        out.append("<div class='sy'><div class='l'>%s%s%s%s%s%s</div></div>" % (hd, al, bc, nt, ft, sl))
    return _sar("Kargo etiketi", css, "".join(out), otomatik)


# ======================================================================================= KARGO ŞABLONU (FİŞ) EKİ
def fis_css(cfg):
    """Mevcut fis_html CSS'ine eklenen tasarım katmanı."""
    st = cfg["stil"]
    css = ("@page{size:%s;margin:10mm}body{%s}" % (cfg["boyut"].upper(), _vars(cfg)) + MONO
           + ".hd{border-bottom-color:var(--c)}.bx{border-radius:var(--r)}.fh{display:flex;align-items:center;gap:3.4mm}"
           ".fh .lg{max-height:15mm;max-width:38mm;object-fit:contain}.mn.lg{width:14mm;height:14mm;font-size:15pt}"
           ".fh .fb{display:flex;flex-direction:column;font-size:11px;color:#475467;line-height:1.35}.fh .fb b{font-size:14px;color:#101828}"
           ".fa{margin-top:10px;text-align:center;font-size:12px;color:#475467;border-top:1px solid #eaecf0;padding-top:8px}"
           ".tot .b{border-top-color:var(--c)}th{color:var(--c)}.hd .no{color:var(--c)}")
    if st == "serit":
        css += (".hd{background:var(--c);color:var(--ci);border:0;padding:12px 14px;border-radius:var(--r);align-items:center}"
                ".hd h1,.hd .no{color:var(--ci)}.hd div,.hd .fb,.hd .fb b{color:var(--ci)!important}.hd .lg{background:#fff;border-radius:calc(var(--r)/1.6);padding:4px}"
                ".hd .mn.lg{background:#fff;color:var(--c)}.bx b{color:var(--a)}.tot .b{background:var(--a);color:var(--ai);border:0;padding:7px 9px;border-radius:calc(var(--r)/1.6)}")
    elif st == "minimal":
        css += (".hd{border-bottom:1px solid #98a2b3}.bx{border:0;border-bottom:1px solid #d0d5dd;border-radius:0;padding-left:0}"
                "th{border-bottom:1px solid #101828}.tot .b{border-top:1px solid #101828}")
    return css


def fis_baslik(info, cfg, baslik):
    """Fişin üst bölümü: logo + firma bilgisi (solda), belge adı (altında)."""
    return ("<div class='fh'>%s%s</div>" % (_logo(info, cfg), _firma_blok(info, cfg))) if (cfg.get("logo") or cfg.get("tel") or cfg.get("adres") or info.get("ad")) else ""


# ======================================================================================= QR ETİKETİ
QR_SAYFA = {"a4-4": ("A4", 2, "86mm", "125mm", 4), "a4-6": ("A4", 2, "86mm", "84mm", 6),
            "a5": ("A5", 1, "128mm", "190mm", 1), "10x15": ("100mm 150mm", 1, "92mm", "142mm", 1)}


def qr_html(kartlar, cfg, info, otomatik=True):
    """kartlar: [{"no": 3, "url": "https://..."}]. Logo üstte, altında QR; firma bilgisi ayarlardan."""
    sayfa, kol, w, h, adet = QR_SAYFA[cfg["boyut"]]
    st = cfg["stil"]
    c, a = cfg["renk"], cfg["vurgu"]
    kk = {"a4-4": 1.0, "a4-6": 0.82, "a5": 1.35, "10x15": 1.25}[cfg["boyut"]]
    qpx = {"a4-4": 5, "a4-6": 4, "a5": 6, "10x15": 6}[cfg["boyut"]]
    koyu = st == "koyu"
    css = (TEMEL + "@page{size:%s;margin:%s}" % (sayfa, "0" if cfg["boyut"] == "10x15" else "10mm") + EKRAN + MONO
           + "body{%s;color:%s}" % (_vars(cfg), "#101828")
           + ".pg{display:grid;grid-template-columns:repeat(%d,%s);gap:6mm;justify-content:center;page-break-after:always;padding:%s}"
           % (kol, w, "4mm 0" if cfg["boyut"] != "10x15" else "3mm")
           + ".pg:last-child{page-break-after:auto}"
           ".k{width:%s;height:%s;border-radius:var(--r);padding:%.1fmm 5mm;display:flex;flex-direction:column;align-items:center;text-align:center;gap:%.1fmm;position:relative;overflow:hidden;background:#fff;page-break-inside:avoid}"
           % (w, h, 6 * kk, 2.4 * kk)
           + ".k .lg{max-height:%.0fmm;max-width:%.0fmm;object-fit:contain}.k .mn.lg{width:%.0fmm;height:%.0fmm;font-size:%.0fpt}"
           % (17 * kk, 46 * kk, 15 * kk, 15 * kk, 17 * kk)
           + ".k .fa{font-size:%.1fpt;font-weight:700;letter-spacing:.02em}.k .bs{font-size:%.0fpt;font-weight:800;line-height:1.1;color:var(--c)}"
           % (10 * kk, 20 * kk)
           + ".k .nt{font-size:%.1fpt;opacity:.75}.k .qb{background:#fff;padding:2mm;border-radius:calc(var(--r)/1.5);margin-top:auto}.k .qb svg{display:block;width:%.0fmm;height:%.0fmm}"
           % (9.5 * kk, 46 * kk, 46 * kk)
           + ".k .ms{font-size:%.0fpt;font-weight:800;color:var(--a);letter-spacing:.02em}.k .u{font-size:%.1fpt;opacity:.6;word-break:break-all}.k .al{font-size:%.1fpt;font-weight:600}"
           % (15 * kk, 7.5 * kk, 9 * kk)
           + ".k.kes{outline:.3mm dashed #98a2b3;outline-offset:-.3mm}")
    if st == "logo-ust":
        css += ".k{border:.4mm solid #d0d5dd}"
    elif st == "cerceve":
        css += (".k{border:.9mm solid var(--c);box-shadow:inset 0 0 0 1.6mm #fff,inset 0 0 0 2.2mm var(--a)}.k .bs{color:var(--c)}")
    elif st == "koyu":
        css += (".k{background:var(--c);color:var(--ci)}.k .bs{color:var(--ci)}.k .ms{color:var(--a)}.k .nt,.k .u{color:var(--ci);opacity:.75}"
                ".k .mn.lg{background:#fff;color:var(--c)}.k .lg:not(.mn){background:#fff;border-radius:calc(var(--r)/1.6);padding:1.2mm}"
                ".k .qb{padding:3mm;box-shadow:0 0 0 1mm var(--a)}")
    elif st == "serit":
        css += (".k{border:.3mm solid #d0d5dd;padding-top:0;padding-bottom:0}.k .ust{width:calc(100%% + 10mm);margin:0 -5mm;padding:%.1fmm 5mm;background:var(--c);color:var(--ci);display:flex;flex-direction:column;align-items:center;gap:1.6mm}"
                ".k .ust .bs{color:var(--ci)}.k .ust .lg:not(.mn){background:#fff;border-radius:calc(var(--r)/1.6);padding:1.2mm}.k .ust .mn.lg{background:#fff;color:var(--c)}"
                ".k .alt{width:calc(100%% + 10mm);margin:auto -5mm 0;padding:%.1fmm 5mm;background:var(--a);color:var(--ai)}.k .alt .ms,.k .alt .u{color:var(--ai)}"
                % (4 * kk, 3 * kk))
    elif st == "minimal":
        css += ".k{border:0}.k .bs{font-size:%.0fpt;font-weight:700}" % (16 * kk)
    out, cur = [], []
    for it in kartlar:
        masa = ("<div class='ms'>Masa %s</div>" % _e(it["no"])) if cfg["masa"] and it.get("no") else ""
        url = ("<div class='u'>%s</div>" % _e(re.sub(r"^https?://", "", it["url"]))) if cfg["url"] else ""
        lg = _logo(info, cfg)
        fa = ("<div class='fa'>%s</div>" % _e(info["ad"])) if cfg["firma"] and info.get("ad") else ""
        bs = ("<div class='bs'>%s</div>" % _e(cfg["baslik"])) if cfg["baslik"] else ""
        nt = ("<div class='nt'>%s</div>" % _e(cfg["not"])) if cfg["not"] else ""
        al = ("<div class='al'>%s</div>" % _e(cfg["alt"])) if cfg["alt"] else ""
        qrs = "<div class='qb'>%s</div>" % QR.svg(it["url"], px=qpx, kenar=1, renk=("#000000" if koyu else c))
        if st == "serit":
            ic = ("<div class='ust'>%s%s%s</div>%s%s<div class='alt'>%s%s%s</div>" % (lg, fa, bs, nt, qrs, masa, url, al))
        else:
            ic = lg + fa + bs + nt + qrs + masa + url + al
        cur.append("<div class='k%s'>%s</div>" % (" kes" if cfg["kesik"] and st in ("logo-ust", "minimal", "koyu") else "", ic))
        if len(cur) == adet:
            out.append("<div class='pg'>%s</div>" % "".join(cur)); cur = []
    if cur:
        out.append("<div class='pg'>%s</div>" % "".join(cur))
    return _sar("QR etiketi", css, "".join(out), otomatik)


# ======================================================================================= ÖRNEK VERİ (önizleme)
def ornek_siparis():
    """Önizleme için işaretli örnek sipariş; gerçek müşteri gibi görünmesin diye adı 'Örnek Alıcı'."""
    return {"no": "SP-0001", "at": "2026-01-01T10:00", "paid": False, "total": 349.9, "subtotal": 349.9, "note": "Zili çalmayın, kapıya bırakın.",
            "customer": {"name": "Örnek Alıcı", "phone": "05320000000", "address": "Örnek Mah. Örnek Sk. No:1 D:2", "district": "Merkez", "city": "Ankara"},
            "cargo": {"firm": "", "code": "", "barcode": "8690000012345"}, "cargo_name": "Kargo firması",
            "channel_name": "Web sitesi", "items": [{"name": "Örnek ürün", "sku": "ORN-1", "qty": 2, "price": 149.95, "barcode": ""}]}


# ======================================================================================= UÇLAR
import json  # noqa: E402

from fastapi import Depends, HTTPException  # noqa: E402


async def firma_bilgisi(db) -> dict:
    g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
    lg = (await db.app_settings.find_one({"_id": "firm_logo"}, {"_id": 0}) or {}).get("data") or ""
    return {"ad": g.get("company_name") or "", "tel": g.get("company_phone") or "", "adres": g.get("company_address") or "", "logo": lg}


async def ayar_oku(db, tip: str) -> dict:
    d = (await db.app_settings.find_one({"_id": "yp_etiket"}, {"_id": 0}) or {}).get(tip) or {}
    cfg = temiz(tip, {}, d)
    if tip == "qr":                                                  # başlık ve not eski QR ayarından gelir (tek kaynak)
        q = await db.app_settings.find_one({"_id": "yp_qr"}, {"_id": 0}) or {}
        cfg["baslik"] = q.get("title") if q.get("title") is not None else cfg["baslik"]
        cfg["not"] = q.get("note") if q.get("note") is not None else cfg["not"]
    return cfg


def register(api_router, db, deps):
    adm = Depends(deps["require_admin"])

    def tipi(tip):
        if tip not in DEF:
            raise HTTPException(404, "Etiket türü bulunamadı")
        return tip

    @api_router.get("/yp/etiket")
    async def liste(_: dict = adm):
        info = await firma_bilgisi(db)
        q = await db.app_settings.find_one({"_id": "yp_qr"}, {"_id": 0}) or {}
        return {"firma": {"ad": info["ad"], "tel": info["tel"], "adres": info["adres"], "logo": bool(info["logo"])},
                "cfg": {t: await ayar_oku(db, t) for t in DEF},
                "stiller": {t: [{"id": a, "ad": b, "not": c} for a, b, c in STIL[t]] for t in STIL},
                "boyutlar": {"fis": [{"id": k, "ad": v} for k, v in FIS_BOY.items()],
                             "etiket": [{"id": k, "ad": v[2]} for k, v in KARGO_BOY.items()],
                             "qr": [{"id": k, "ad": v} for k, v in QR_BOY.items()]},
                "fontlar": [{"id": k, "ad": v} for k, v in FONT_AD.items()], "masa": int(q.get("tables") or 12)}

    @api_router.put("/yp/etiket/{tip}")
    async def kaydet(tip: str, payload: dict, _: dict = adm):
        tipi(tip)
        cur = (await db.app_settings.find_one({"_id": "yp_etiket"}, {"_id": 0}) or {}).get(tip) or {}
        cfg = temiz(tip, payload, cur)
        await db.app_settings.update_one({"_id": "yp_etiket"}, {"$set": {tip: cfg}}, upsert=True)
        if tip == "qr":                                              # başlık, not, masa sayısı eski QR ayarında durur
            st = {}
            if "baslik" in payload:
                st["title"] = cfg["baslik"] or "Menü"
            if "not" in payload:
                st["note"] = cfg["not"]
            if "masa" in payload:
                try:
                    st["tables"] = max(min(int(payload["masa"]), 200), 1)
                except (TypeError, ValueError):
                    pass
            if st:
                await db.app_settings.update_one({"_id": "yp_qr"}, {"$set": st}, upsert=True)
        return {"ok": True, "cfg": await ayar_oku(db, tip)}

    async def uret(tip, cfg, order_id="", otomatik=False):
        info = await firma_bilgisi(db)
        if tip == "etiket":
            o = None
            if order_id:
                o = await db.yp_orders.find_one({"id": order_id}, {"_id": 0})
                if o:
                    import siparis
                    o = siparis.view(o)
            return etiket_html([o or ornek_siparis()], cfg, info, otomatik)
        if tip == "fis":
            import siparis
            o = siparis.view(ornek_siparis())
            if order_id:
                r = await db.yp_orders.find_one({"id": order_id}, {"_id": 0})
                o = siparis.view(r) if r else o
            h = siparis.fis_html([o], "kargo", info["ad"], cfg, info)
            return h if otomatik else h.replace("window.print()", "void 0")
        d = await db.app_settings.find_one({"_id": "yp_qr"}, {"_id": 0}) or {}
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        site = (g.get("site_url") or g.get("domain") or "onlinekaydet.com").rstrip("/")
        site = site if site.startswith("http") else "https://" + site
        return qr_html([{"no": 1, "url": "%s/menu?masa=1" % site}, {"no": 2, "url": "%s/menu?masa=2" % site}], cfg, info, otomatik)

    @api_router.post("/yp/etiket/{tip}/onizleme")
    async def onizleme(tip: str, payload: dict, _: dict = adm):
        tipi(tip)
        cfg = temiz(tip, payload.get("cfg") or {}, await ayar_oku(db, tip))
        if tip == "qr":
            cfg["baslik"] = str((payload.get("cfg") or {}).get("baslik", cfg["baslik"]))[:40]
            cfg["not"] = str((payload.get("cfg") or {}).get("not", cfg["not"]))[:120]
        return {"ok": True, "html": await uret(tip, cfg, str(payload.get("order_id") or "")[:24])}

    @api_router.post("/yp/etiket/{tip}/stiller")
    async def stiller(tip: str, payload: dict, _: dict = adm):
        """Her stilin küçük önizlemesi: kullanıcı tasarımı resme bakarak seçer."""
        tipi(tip)
        base = temiz(tip, payload.get("cfg") or {}, await ayar_oku(db, tip))
        if tip == "qr":
            base["baslik"] = str((payload.get("cfg") or {}).get("baslik", base["baslik"]))[:40]
            base["not"] = str((payload.get("cfg") or {}).get("not", base["not"]))[:120]
        return {"ok": True, "items": {s[0]: await uret(tip, dict(base, stil=s[0])) for s in STIL[tip]}}
