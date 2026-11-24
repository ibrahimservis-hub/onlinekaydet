#!/usr/bin/env python3
"""20 sinematik demo sitesini panel temasına çevirir.
docs/demo/<slug>/index.html -> themes/html/c<NN>-<slug>.html (+ panel/themes.json kayıtları).
Her bölüm <div class="ed" data-nm="..."> bloğu olur; yazı, yazı tipi ve görseller panelden düzenlenir."""
import html, json, os, re, sys
from bs4 import BeautifulSoup

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEMO = os.path.join(ROOT, "docs", "demo")
OUT = os.path.join(ROOT, "themes", "html")
TJ = os.path.join(ROOT, "panel", "themes.json")

# slug: (sektör, tema adı = firma adı yerine geçen örnek ad)
T = [
    ("makas", "kuafor", "Makas Berber"), ("motor", "oto_servis", "Motor Atölye"), ("firin", "pastane", "Fırın 1923"),
    ("pati", "veteriner", "Pati Vet"), ("emlak", "emlakci", "Anahtar Emlak"), ("form", "spor_salonu", "Form Stüdyo"),
    ("lumi", "estetik_merkezi", "Lumi Estetik"), ("sofra", "lokanta", "Sofra Bistro"), ("isi", "kombi", "Isı Usta"),
    ("gulus", "dis_klinigi", "Gülüş Diş Kliniği"), ("atlas", "tekstil", "Atlas Butik"), ("bahar", "cicekci", "Bahar Çiçek"),
    ("tekno", "telefon_tamir", "Teknofix"), ("beyaz", "beyaz_esya", "Beyaz Servis"), ("volt", "elektrik", "Volt & Su"),
    ("piril", "temizlik", "Pırıl Temizlik"), ("yuk", "nakliye", "Yük Nakliyat"), ("denge", "diyetisyen", "Denge Diyet"),
    ("ses", "psikolog", "İç Ses"), ("direksiyon", "surucu_kursu", "Direksiyon Sürücü Kursu"),
]
ADR = "Atatürk Cad. No:12 · Ankara"


def lum(c):
    c = c.lstrip("#")
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    return .299 * r + .587 * g + .114 * b


def var(h, k):
    m = re.search(r"--%s:(#[0-9a-fA-F]{6})" % k, h)
    return m.group(1) if m else None


def _leaf(v):
    from html import escape as E
    if isinstance(v, bool):
        return '<p data-t="b">%s</p>' % ("true" if v else "false")
    if v is None:
        return '<p data-t="z"></p>'
    if isinstance(v, (int, float)):
        return '<p data-t="n">%s</p>' % E(str(v))
    if isinstance(v, str):
        m = re.search(r"/photos/(\d+)/", v)
        if v.startswith("https://images.pexels.com") and m:
            return '<div data-t="s"><img data-i="%s" src="%s" alt="" loading="lazy"></div>' % (m.group(1), E(v, quote=True))
        return '<p data-t="s">%s</p>' % E(v)
    raise ValueError


def _node(v):
    from html import escape as E
    if isinstance(v, dict):
        return '<div data-t="o">' + "".join(('<p data-t="k">%s</p>%s' if not re.fullmatch(r"[a-z0-9_]{1,12}", k) else '<div data-t="k">%s</div>%s') % (E(k), _node(x)) for k, x in v.items()) + "</div>"
    if isinstance(v, list):
        return '<div data-t="a">' + "".join(_node(x) for x in v) + "</div>"
    return _leaf(v)


# etkileşimli kutuların verisi (const C) sayfada gizli HTML olur; panel yazı/görselleri düzenler, betik çalışırken bunu okur
SHIM = ("const C=(function(){var r=document.querySelector('.cdata>[data-t]');function P(e){var t=e.getAttribute('data-t'),x;"
        "if(t=='s'){x=e.querySelector('img');return x?x.getAttribute('src'):e.textContent.trim()}"
        "if(t=='b')return e.textContent.trim()=='true';if(t=='z')return null;"
        "if(t=='n')return parseFloat(e.textContent.trim().replace(',','.'))||0;"
        "if(t=='a')return [].map.call(e.children,P);"
        "var o={},k;[].forEach.call(e.children,function(c){if(c.getAttribute('data-t')=='k')k=c.textContent.trim();else o[k]=P(c)});return o}"
        "return r?P(r):{}})();")


def conv(i, slug, sector, name):
    h = open(os.path.join(DEMO, slug, "index.html"), encoding="utf-8").read()
    # örnek adres ve notlar -> sitegen'in tanıdığı kalıp
    h = re.sub(r"Örnek \w+\.(?:,? Örnek \w+\.)?(?: ·)? ?Ankara", ADR, h)
    h = h.replace(" · Örnek tasarım", "").replace("Örnek tasarım", "")
    soup = BeautifulSoup(h, "html.parser")
    body = soup.body
    # marka adı: menüde, alt bilgide ve dev yazıda tema adı (apply_profile firma adıyla değiştirir)
    nav = body.find("nav")
    lg = nav.find("a", class_="lg") or nav.find("a")
    lg.clear(); lg.string = name
    ft = body.find("footer")
    fb = ft.find("b")
    if fb:
        fb.clear(); fb.string = name
    big = ft.find(class_="big")
    if big:
        big.clear(); big.string = name
    for p in ft.find_all("p"):
        if "©" in p.get_text():
            p.clear(); p.string = "© " + name
    # görseller: <img data-i=ID> panelden değiştirilebilsin
    for im in body.find_all("img"):
        m = re.search(r"/photos/(\d+)/", im.get("src", ""))
        if m:
            im["data-i"] = m.group(1)
    main = body.find("main")
    names, used = [], set()

    def nm(el, k):
        if k == 0:
            return "Ana görsel"
        hd = el.find(["h2", "h3", "h1"])
        t = re.sub(r'["\\\[\]<>{}]', "", hd.get_text(" ", strip=True)) if hd else ""
        t = (t[:26].rsplit(" ", 1)[0] if len(t) > 26 else t) or ("Bölüm %d" % (k + 1))
        t = "Bölüm: " + t if t in ("Menü", "Alt bilgi", "Ana görsel") else t
        while t in used:
            t += " "
        used.add(t)
        return t.strip() if t.strip() not in used - {t} else t + "·"

    blocks = []
    nav_html = str(nav)
    blocks.append(("Menü", nav_html))
    for k, el in enumerate(main.find_all(True, recursive=False)):
        blocks.append((nm(el, k), str(el)))
    extra = "".join(str(el) for el in body.find_all(True, recursive=False)
                    if el.name not in ("nav", "main", "footer", "noscript", "script") and el.get("id") != "pre")
    blocks.append(("Alt bilgi", str(ft) + extra))      # sepet çekmecesi gibi gövdeye bağlı öğeler alt bilgiyle gider
    # sıra: pre (preloader) + bloklar + <noscript> + betikler
    pre = body.find("div", id="pre")
    tail = []
    for el in body.find_all(True, recursive=False):
        if el.name in ("noscript", "script"):
            tail.append(str(el))
    cdata = ""
    for k, t_ in enumerate(tail):
        m = re.search(r"const C=(.*?);</script>", t_ + "", re.S) if "const C=" in t_ else None
        if m:
            data = json.loads(m.group(1).replace("\\/", "/"))
            cdata = '<div class="ed" data-nm="Etkileşimli veriler"><div class="cdata" hidden style="display:none">%s</div></div>' % _node(data)
            tail[k] = t_.replace("const C=" + m.group(1) + ";", SHIM, 1)
    for k, t_ in enumerate(tail):                      # ana betik bölünür: iç sayfalar yalnız önyükleme + mobil menüyü alır
        if t_.startswith("<script>window.MOB="):
            m2 = t_.rfind("\n(function(){var $=function(s,r)")
            m3 = t_.find("\n})();", m2) + len("\n})();") if m2 > 0 else -1
            e1 = t_.find("scrub:scrub}})();")
            e1 = e1 + len("scrub:scrub}})();") if e1 > 0 else t_.find(";\n", 0) + 1       # önyükleme yoksa yalnız window.MOB satırı
            if 0 < e1 <= m2 and m3 > m2:
                tail[k] = ('<script data-ok="boot">' + t_[len("<script>"):e1] + '</script><script data-ok="mob">' + t_[m2:m3] + "</script><script>"
                           + t_[e1:m2] + t_[m3:])
    bh = ['<div class="ed" data-nm="%s">%s</div>' % (n, x) for n, x in blocks]
    body_html = (str(pre) if pre else "") + "".join(bh[:-1]) + cdata + bh[-1] + "".join(tail)
    head = str(soup.head)
    head = head.replace("</style>", ".ed{display:contents}</style>", 1)
    out = "<!doctype html><html lang=\"tr\">" + head + "<body>" + body_html + "</body></html>"
    for lib in ("gsap", "ScrollTrigger", "lenis"):          # kütüphaneler sayfaya gömülür (müşteri sitesinde ../lib yok)
        js = open(os.path.join(DEMO, "lib", lib + ".min.js"), encoding="utf-8").read().replace("</script", "<\\/script")
        out = out.replace('<script src="../lib/%s.min.js"></script>' % lib, "<script>" + js + "</script>")
    slg = "c%02d-%s" % (i + 1, slug)
    open(os.path.join(OUT, slg + ".html"), "w", encoding="utf-8").write(out)
    bg, ink, ac = var(h, "bg"), var(h, "ink"), var(h, "ac")
    cols = [c for c in (bg, ink) if c]
    dark = min(cols, key=lum) if cols else "#111111"
    soft = max(cols, key=lum) if cols else "#f4f1ea"
    return {"slug": slg, "sector": sector, "dark": dark, "accent": ac or "#e8502b", "soft": soft, "radius": 16, "name": html.escape(name, quote=False), "premium": True}


def main():
    recs = [conv(i, s, sec, n) for i, (s, sec, n) in enumerate(T)]
    th = json.load(open(TJ, encoding="utf-8"))
    th = [t for t in th if not re.match(r"c\d\d-", t["slug"])]
    th += recs
    json.dump(th, open(TJ, "w", encoding="utf-8"), ensure_ascii=False)
    print(len(recs), "tema yazıldı;", len(th), "toplam")


if __name__ == "__main__":
    main()
