"""Marka sitelerinden ürün aktarma (başlık, açıklama, teknik özellik, görsel) + kâr oranıyla fiyatlandırma.

Akış:
  1) Kaynak tanımlanır: marka adı, liste/kategori adresleri veya sitemap, ürün adresi deseni, kâr oranı.
  2) "Güncelle" düğmesi ürünleri çeker; yeni ürünleri mağazaya ekler, mevcutları günceller.
  3) Fiyat: marka sitesi fiyat gösteriyorsa (schema.org offers) otomatik alınır; göstermiyorsa ürün başına "liste fiyatı"
     elle girilir veya CSV yüklenir. Satış fiyatı = liste fiyatı × (1 + kâr%) + sabit TL, istenen basamağa yuvarlanır.
  4) Fiyatı olmayan ürünler "pasif" (mağazada görünmez) eklenir, fiyat girilince "aktif et" ile yayına alınır.

Saygılı çekim: robots.txt'e uyar, tanımlayıcı User-Agent kullanır, istekler arasında bekler, ürün sayısı sınırlıdır.
Not: Marka metin/görselleri telifli olabilir; yayınlama sorumluluğu site sahibindedir. Görseller kopyalanmaz,
kaynak adresine bağlanır (isterseniz panelden kendi görselinizle değiştirebilirsiniz).
"""
import asyncio
import builtins
import csv
import io
import json
import logging
import math
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from urllib import robotparser
from urllib.parse import parse_qs, urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup
from fastapi import Depends, HTTPException

import governance
import shop as shopmod

log = logging.getLogger("brand_import")
UA = "Mozilla/5.0 (compatible; ServisPlusCatalogBot/1.0; +https://servisplus.net.tr)"
DELAY = 1.0
SOURCE_DEFAULT = {
    "name": "", "brand": "", "category": "", "site_url": "", "slug": "", "start_urls": [], "sitemap_url": "", "link_regex": "", "cat_regex": "", "markup_percent": 20.0,
    "markup_fixed": 0.0, "round_to": 10, "max_products": 150, "auto_weekly": False, "new_active": False,
}
_DD = "https://www.demirdokum.com.tr/urunler/"
PRESETS = [
    {"name": "Demirdöküm " + n, "brand": "Demirdöküm", "category": n, "start_urls": [_DD + p + "/"], "link_regex": r"/urunler/.+-\d+\.html", "max_products": 300}
    for n, p in [("Kombi", "kombiler"), ("Klima", "klimalar"), ("Isı Pompası", "s-pompalar"), ("Radyatör", "radyatorler"), ("Oda Termostatı", "oda-termostatlar"),
                 ("Termosifon", "termosifonlar"), ("Şofben", "sofbenler"), ("Kazan ve Merkezi Sistem", "kazan-ve-merkezi-sistemler"), ("Kazan", "kazanlar"),
                 ("Elektrikli Isıtıcı", "elektrikli-s-t-c-lar"), ("VRF Sistemi", "vrf-sistemleri")]
]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _f(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def parse_price(v):
    """'12.345,67 TL' / '12345.67' / 12345 -> float"""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d.,]", "", str(v))
    if not s:
        return 0.0
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".") if len(s.split(",")[-1]) <= 2 else s.replace(",", "")
    elif s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[-1]) == 3):
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def sale_price(base, src):
    if base <= 0:
        return 0.0
    p = base * (1 + _f(src.get("markup_percent")) / 100.0) + _f(src.get("markup_fixed"))
    step = _f(src.get("round_to"))
    if step > 0:
        p = math.ceil(p / step) * step
    return round(p, 2)


# ------------------------------------------------------------------ çekim
class Fetcher:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
        self.errs = []
        self.robots = {}
        self.last = 0.0
        self.skipped_robots = 0

    def allowed(self, url):
        host = urlparse(url)
        key = host.scheme + "://" + host.netloc
        if key not in self.robots:
            rp = robotparser.RobotFileParser()
            try:
                r = self.s.get(key + "/robots.txt", timeout=15)
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except Exception:                           # noqa: BLE001
                rp.parse([])
            self.robots[key] = rp
        ok = self.robots[key].can_fetch(UA, url)
        if not ok:
            self.skipped_robots += 1
            self._err(url, "robots.txt engelliyor")
        return ok

    def _err(self, url, why):
        if len(self.errs) < 6:
            self.errs.append("%s → %s" % (url[:90], why))

    def get(self, url, timeout=25):
        if not self.allowed(url):
            return None
        wait = DELAY - (time.time() - self.last)
        if wait > 0:
            time.sleep(wait)
        self.last = time.time()
        try:
            r = self.s.get(url, timeout=timeout)
        except Exception as e:                          # noqa: BLE001
            self._err(url, "bağlantı kurulamadı (%s)" % str(e)[:60])
            return None
        if r.status_code != 200:
            self._err(url, "HTTP %d" % r.status_code)
        if r.status_code == 200 and "charset" not in r.headers.get("content-type", "").lower():
            r.encoding = "utf-8" if r.content[:3000].decode("utf-8", "ignore").count("\ufffd") == 0 else r.apparent_encoding
        return r if r.status_code == 200 else None


def sitemap_urls(f, url, depth=0):
    out = []
    r = f.get(url)
    if not r:
        return out
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", r.text)
    if "<sitemapindex" in r.text[:2000].lower() and depth < 2:
        for sm in locs[:30]:
            out += sitemap_urls(f, sm, depth + 1)
    else:
        out += locs
    return out

# Sitedeki tüm markalar -> (görünen ad, resmi site adresi). Adresler tahmindir; yanlış/boş olanı panelde düzeltin.
HUB_BRANDS = [
    ("airfel", "Airfel", "https://airfel.com/tr/tr"), ("alarko", "Alarko", "https://www.alarko-carrier.com.tr"), ("altus", "Altus", "https://www.altus.com.tr"),
    ("arcelik", "Arçelik", "https://www.arcelik.com.tr"), ("ariston", "Ariston", "https://www.ariston.com/tr-tr"), ("awox", "Awox", "https://www.awox.com.tr"),
    ("baymak", "Baymak", "https://www.baymak.com.tr"), ("beko", "Beko", "https://www.beko.com.tr"), ("beretta", "Beretta", ""),
    ("bosch", "Bosch", "https://www.bosch-home.com.tr"), ("buderus", "Buderus", "https://www.buderus.com/tr/tr/"), ("carrier", "Carrier", ""),
    ("daikin", "Daikin", "https://www.daikin.com.tr"), ("demirdokum", "Demirdöküm", "https://www.demirdokum.com.tr"), ("dijitsu", "Dijitsu", ""),
    ("eca", "ECA", "https://eca.com.tr"), ("electrolux", "Electrolux", "https://www.electrolux.com.tr"), ("ferroli", "Ferroli", "https://www.ferroli.com.tr"),
    ("franke", "Franke", "https://www.franke.com/tr/tr.html"), ("fujiplus", "Fujiplus", ""), ("fujitsu", "Fujitsu", ""), ("general", "General", ""),
    ("gree", "Gree", "https://www.gree.com.tr"), ("grundig", "Grundig", "https://www.grundig.com.tr"), ("haier", "Haier", "https://www.haier-europe.com/tr_TR"),
    ("hi-level", "Hi-Level", ""), ("hoover", "Hoover", "https://www.hoover-home.com/tr_TR"), ("hotpoint", "Hotpoint", ""), ("immergas", "Immergas", ""),
    ("indesit", "Indesit", ""), ("jvc", "JVC", ""), ("kumtel", "Kumtel", "https://www.kumtel.com.tr"), ("lambert", "Lambert", ""),
    ("lg", "LG", "https://www.lg.com/tr"), ("luxell", "Luxell", "https://www.luxell.com.tr"), ("midea", "Midea", ""),
    ("miele", "Miele", "https://www.miele.com.tr"), ("mitsubishi-electric", "Mitsubishi Electric", "https://klima.mitsubishielectric.com.tr"), ("mitsubishi-heavy", "Mitsubishi Heavy", ""),
    ("nordmende", "Nordmende", ""), ("onvo", "Onvo", "https://onvo.com.tr"), ("panasonic", "Panasonic", "https://www.panasonic.com/tr"),
    ("philips", "Philips", "https://www.philips.com.tr"), ("profilo", "Profilo", "https://www.profilo.com.tr"), ("protherm", "Protherm", "https://www.protherm.com.tr"),
    ("regal", "Regal", ""), ("remeha", "Remeha", "https://www.remeha.com.tr"), ("rota-klima", "Rota Klima", "https://www.rotaclimate.com"), ("samsung", "Samsung", "https://www.samsung.com/tr"),
    ("sharp", "Sharp", ""), ("siemens", "Siemens", "https://www.siemens-home.bsh-group.com/tr"), ("sigma", "Sigma", ""), ("silverline", "Silverline", "https://silverline.com/tr/tr-tr"),
    ("skytech", "Skytech", "https://skytech.com.tr"), ("sony", "Sony", "https://www.sony.com.tr"), ("sunny", "Sunny", "https://www.sunny.com.tr"), ("tcl", "TCL", "https://www.tcl.com/tr/tr"),
    ("teka", "Teka", "https://www.teka.com/tr-tr"), ("telefunken", "Telefunken", "http://www.telefunken.com.tr"), ("termodinamik", "Termodinamik", "https://www.termodinamik.com.tr"),
    ("toshiba", "Toshiba", "https://www.toshiba-klima.com.tr"), ("ugur", "Uğur", "https://ugur.com.tr"), ("vaillant", "Vaillant", "https://www.vaillant.com.tr"),
    ("vestel", "Vestel", "https://www.vestel.com.tr"), ("viessmann", "Viessmann", "https://www.viessmann.com.tr"), ("warmhaus", "Warmhaus", "https://www.warmhaus.com/tr"),
    ("whirlpool", "Whirlpool", ""), ("wolf", "Wolf", ""), ("york", "York", ""),
]
_DD = "https://www.demirdokum.com.tr/urunler/"
# Doğrulanmış ek bilgiler: sitemap / liste adresleri / ürün adresi deseni
HUB_EXTRA = {
    "airfel": {"start_urls": ["https://airfel.com/tr/tr/category/klimalar", "https://airfel.com/tr/tr/category/kombiler", "https://airfel.com/tr/tr/category/radyatorler"], "link_regex": r"/detail/"},
    "alarko": {"sitemap_url": "", "start_urls": ["https://www.alarko-carrier.com.tr/" + c for c in ("kombi", "klima", "isi-pompasi", "multi-klima", "vrf-sistemleri")], "link_regex": r"^/urun/[^/]+/[^/]+$"},
    "altus": {"sitemap_url": "https://www.altus.com.tr/sitemap-index.xml", "start_urls": ["https://www.altus.com.tr/urunler/" + c for c in ("beyaz-esya-buzdolabi", "ankastre-ankastre-firinlar", "televizyon-google-tv", "isitma-sogutma-klima", "kucuk-ev-aletleri-supurge")], "cat_regex": r"^/urunler/[^/]+/?$", "link_regex": r"^/urunler/[^/]+/[^/]+/?$"},
    "arcelik": {"sitemap_url": "https://www.arcelik.com.tr/sitemap.xml"},
    "awox": {"sitemap_url": "https://www.awox.com.tr/sitemap/products/0.xml"},
    "baymak": {"start_urls": ["https://www.baymak.com.tr/kombi"], "link_regex": r"/urunler/"},
    "beko": {"sitemap_url": "https://www.beko.com.tr/sitemap.xml"},
    "bosch": {"sitemap_url": "https://www.bosch-home.com.tr/sitemap.xml", "link_regex": r"/mkt-product/"},
    "buderus": {"start_urls": ["https://www.buderus.com/tr/tr/ocs/bireysel-urunler/yogusmali-kombiler-735153-c/"], "link_regex": r"-p/?$"},
    "daikin": {"sitemap_url": "https://www.daikin.com.tr/sitemap.xml"},
    "demirdokum": {"start_urls": [_DD + p + "/" for p in ("kombiler", "klimalar", "s-pompalar", "radyatorler", "oda-termostatlar", "termosifonlar", "sofbenler", "kazan-ve-merkezi-sistemler", "kazanlar", "elektrikli-s-t-c-lar", "vrf-sistemleri")], "link_regex": r"/urunler/.+-\d+\.html"},
    "eca": {"sitemap_url": "https://eca.com.tr/sitemap_index.xml", "link_regex": r"/urun/"},
    "electrolux": {"sitemap_url": "https://www.electrolux.com.tr/globalassets/sitemaps/www.electrolux.com.tr/sitemapindex.xml"},
    "gree": {"sitemap_url": "https://www.gree.com.tr/sitemap.xml", "link_regex": r"/urun/"},
    "protherm": {"start_urls": ["https://www.protherm.com.tr/tum-urunler"], "link_regex": r"/(yogusmali-kombiler|kontrol-cihazlari|[a-z-]+)/[a-z0-9-]+$"},
    "remeha": {"start_urls": ["https://www.remeha.com.tr/urunler/yogusmali-kombiler", "https://www.remeha.com.tr/urunler/yogusmali-kazanlar", "https://www.remeha.com.tr/urunler/oda-termostatlari"], "link_regex": r"/urunler/.+/.+"},
    "teka": {"sitemap_url": "", "link_regex": r"/urun/"},
    "ugur": {"link_regex": r"/urun/"},
    "vaillant": {"sitemap_url": "https://www.vaillant.com.tr/sitemap-products.xml"},
    "vestel": {"sitemap_url": "https://statics.vestel.com.tr/vstlsitemap/sitemap.xml", "link_regex": r"-p-\d+"},
    "viessmann": {"sitemap_url": "https://www.viessmann.com.tr/sitemap.xml", "link_regex": r"/urunlerimiz/"},
    "warmhaus": {"sitemap_url": "https://www.warmhaus.com/sitemap.xml", "link_regex": r"/urunler/"},
    "siemens": {"link_regex": r"/product/"},
    "miele": {"link_regex": r"/product/"},
}
_NEG = re.compile(r"blog|haber|news|kariyer|career|iletisim|contact|hakkimizda|about|gizlilik|privacy|kvkk|cerez|cookie|destek|support|servis|service|sss|faq|login|uye|sepet|basin|press|investor|surdurulebilirlik|bayi|kampanya|campaign|sertifika|katalog|download|indir|\.(jpg|jpeg|png|gif|svg|pdf|zip|webp)$", re.I)
_POS = re.compile(r"urun|product|model|/p/|/pd/|kombi|klima|buzdolab|camasir|bulasik|firin|televizyon|tv|sofben|ocak|kurutma|dondurucu|isitici|radyator|termosifon|kazan|ankastre|aspirator|supurge", re.I)
CATS = [("Kombi", "kombi"), ("Klima", "klima|air-condition"), ("Buzdolabı", "buzdolab|refrigerator"), ("Çamaşır Makinesi", "camasir|washing"), ("Kurutma Makinesi", "kurutma"),
        ("Bulaşık Makinesi", "bulasik|dishwasher"), ("Fırın", "firin|oven"), ("Ocak", "ocak|hob"), ("Televizyon", r"televizyon|\btv\b|oled|qled"), ("Şofben", "sofben"),
        ("Termosifon", "termosifon|su-isitici"), ("Derin Dondurucu", "dondurucu|freezer"), ("Isı Pompası", "isi-pompasi|pompa"), ("Radyatör", "radyator"), ("Kazan", "kazan"),
        ("Aspiratör", "aspirator"), ("Süpürge", "supurge")]


def guess_category(name, url=""):
    t = shopmod.slugify((name or "") + " " + (url or ""))
    for c, rx in CATS:
        if re.search(rx, t):
            return c
    return "Diğer"


def discover_links(f, src):
    """Sadece marka sitesi adresi verilmişse: sitemap'i bul, ürün sayfasına benzeyen adresleri öne al."""
    base = src["site_url"].rstrip("/")
    root = "{u.scheme}://{u.netloc}".format(u=urlparse(base))
    sms = []
    try:
        if f.allowed(root + "/robots.txt"):
            r = f.s.get(root + "/robots.txt", timeout=15)
            sms += re.findall(r"(?im)^\s*sitemap:\s*(\S+)", r.text if r.status_code == 200 else "")
    except Exception:                                   # noqa: BLE001
        pass
    sms += [root + "/sitemap.xml", root + "/sitemap_index.xml", base + "/sitemap.xml"]
    urls = []
    for sm in dict.fromkeys(sms):
        urls += sitemap_urls(f, sm)
        if len(urls) > 200:
            break
    if not urls:                                         # sitemap yoksa ana sayfadan 1 seviye tara
        r = f.get(base)
        first = []
        if r:
            for a in BeautifulSoup(r.text, "html.parser").find_all("a", href=True):
                u = urldefrag(urljoin(base + "/", a["href"]))[0]
                if urlparse(u).netloc == urlparse(base).netloc:
                    first.append(u)
        urls = list(dict.fromkeys(first))
        for u in [x for x in urls if _POS.search(x)][:15]:
            r = f.get(u)
            if r:
                for a in BeautifulSoup(r.text, "html.parser").find_all("a", href=True):
                    v = urldefrag(urljoin(u, a["href"]))[0]
                    if urlparse(v).netloc == urlparse(base).netloc:
                        urls.append(v)
    host = urlparse(base).netloc.replace("www.", "")
    pre = urlparse(base).path.rstrip("/")
    good = [u for u in dict.fromkeys(urls) if host in urlparse(u).netloc and urlparse(u).path.startswith(pre or "/") and not _NEG.search(urlparse(u).path)]
    good.sort(key=lambda u: (len(_POS.findall(urlparse(u).path)), urlparse(u).path.count("/")), reverse=True)
    return good[: max(60, int(src.get("max_products", 150)) * 3)]


def collect_links(f, src):
    if src.get("site_url") and not src.get("start_urls") and not src.get("sitemap_url"):
        return discover_links(f, src)
    out = _collect_links(f, src)
    if not out and src.get("site_url"):                 # ayarlı adres/desen sonuç vermezse otomatik keşfe düş
        return discover_links(f, src)
    return out


_PGKEYS = ("pg", "page", "p", "sayfa", "pageno", "pagenumber", "pageindex", "pi")


# Pazaryeri / mağaza sayfası adresleri: (alan adı parçası, ürün adresi deseni, sayfalama parametresi)
MARKET = [("trendyol.com", r"-p-\d+", "pi"), ("hepsiburada.com", r"-pm?-[A-Za-z0-9]+/?$", "sayfa"), ("n11.com", r"/urun/", "pg")]


def market_cfg(url):
    host = urlparse(url).netloc.lower()
    for dom, rx, pk in MARKET:
        if dom in host:
            pages = [url] + [url + ("&" if "?" in url else "?") + "%s=%d" % (pk, i) for i in range(2, 9)]
            return {"start_urls": pages, "link_regex": rx, "sitemap_url": "", "cat_regex": ""}
    return None


def _collect_links(f, src):
    pat = re.compile(src["link_regex"]) if src.get("link_regex") else None
    cpat = re.compile(src["cat_regex"]) if src.get("cat_regex") else None   # alt kategori sayfaları (taranır, ürün sayılmaz)
    found = []
    queue = list(src.get("start_urls") or [])
    seen = set()
    hosts = {urlparse(u).netloc for u in queue}
    n = 0
    while queue and n < 120:
        page = queue.pop(0)
        if page in seen:
            continue
        seen.add(page)
        r = f.get(page)
        if not r:
            continue
        n += 1
        soup = BeautifulSoup(r.text, "html.parser")
        pu = urlparse(page)
        for a in soup.find_all("a", href=True):
            full = urldefrag(urljoin(page, a["href"]))[0]
            fu = urlparse(full)
            if fu.netloc not in hosts:
                continue
            pq = parse_qs(fu.query)
            if fu.path == pu.path and any(k.lower() in _PGKEYS for k in pq):          # sayfalama bağlantısı
                if full not in seen and len(seen) < 150:
                    queue.append(full)
                continue
            if pat and pat.search(fu.path + (("?" + fu.query) if fu.query else "")):
                found.append(full)
            elif cpat and cpat.search(fu.path) and full not in seen:
                queue.append(full)
        nx = soup.find("link", rel="next") or soup.find("a", rel="next")
        if nx and nx.get("href"):
            queue.append(urljoin(page, nx["href"]))
    if src.get("sitemap_url"):
        for u in sitemap_urls(f, src["sitemap_url"]):
            if (not pat) or pat.search(urlparse(u).path):
                found.append(u)
    return list(dict.fromkeys(found))


def _ld_products(soup):
    out = []

    def walk(o):
        if isinstance(o, list):
            for i in o:
                walk(i)
        elif isinstance(o, dict):
            t = o.get("@type")
            if t == "Product" or (isinstance(t, list) and "Product" in t):
                out.append(o)
            for v in o.values():
                if isinstance(v, (list, dict)):
                    walk(v)
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            walk(json.loads(tag.string or tag.get_text() or "null"))
        except Exception:                               # noqa: BLE001
            continue
    return out


def _txt(el, n=400):
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()[:n]


def parse_product(html, url):
    soup = BeautifulSoup(html, "html.parser")
    ld = (_ld_products(soup) or [None])[0] or {}

    def meta(*names):
        for n in names:
            t = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n})
            if t and t.get("content"):
                return t["content"].strip()
        return ""
    name = (ld.get("name") or "").strip() or (soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "") or meta("og:title")
    # ---- açıklama: ld + sayfadaki açıklama blokları + madde işaretli özellikler
    parts = []
    d0 = (ld.get("description") or "").strip() or meta("og:description", "description")
    if d0:
        parts.append(d0)
    seen = {d0}
    for el in soup.select('[itemprop=description], [class*=description], [id*=description], [class*=aciklama], [id*=aciklama], [class*=product-detail], [class*=urun-detay], [id*=urun-detay], [class*=overview]')[:6]:
        t = _txt(el, 4000)
        if len(t) > 60 and t not in seen and not any(t in x or x in t for x in seen if x):
            parts.append(t)
            seen.add(t)
    feats = []
    for el in soup.select('[class*=feature] li, [class*=ozellik] li, [class*=highlight] li, [class*=benefit] li, [class*=avantaj] li')[:30]:
        t = _txt(el, 200)
        if 5 < len(t) < 200 and t not in feats:
            feats.append(t)
    if feats:
        parts.append("Öne çıkan özellikler:\n" + "\n".join("• " + f for f in feats[:20]))
    desc = "\n\n".join(parts)[:12000]
    # ---- görseller (galeri dahil)
    imgs = ld.get("image") or []
    imgs = [imgs] if isinstance(imgs, (str, dict)) else imgs
    imgs = [i.get("url") if isinstance(i, dict) else i for i in imgs]
    og = meta("og:image")
    if og:
        imgs.append(og)
    for im in soup.find_all("img")[:120]:
        src = im.get("data-zoom-image") or im.get("data-large") or im.get("data-src") or im.get("data-original") or im.get("src") or ""
        if not src and im.get("srcset"):
            src = im["srcset"].split(",")[-1].strip().split(" ")[0]
        if src and re.search(r"(urun|product|upload|media|image|gallery|galeri|cdn|catalog|assets)", src, re.I) and not re.search(r"(logo|icon|ikon|picto|sprite|flag|banner|badge|energy|enerji|\.svg|avatar|placeholder|loading)", src, re.I) and not src.startswith("data:"):
            imgs.append(src)
    imgs = [urljoin(url, i) for i in dict.fromkeys(i for i in imgs if i)][:12]
    sku = str(ld.get("sku") or ld.get("mpn") or "").strip()
    model = str(ld.get("model") or ld.get("mpn") or "").strip()
    price = 0.0
    offers = ld.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if isinstance(offers, dict):
        price = parse_price(offers.get("price") or offers.get("lowPrice"))
    if not price:
        price = parse_price(meta("product:price:amount", "og:price:amount"))
    if not price:                                        # JSON-LD/meta yoksa: "fiyat/price" sınıflı öğelerden ya da sayfadaki ilk "xx.xxx TL"
        for el in soup.find_all(class_=re.compile(r"price|fiyat", re.I))[:12]:
            m = re.search(r"(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d{2,6}(?:,\d{1,2})?)\s*(?:TL|₺)", el.get_text(" ", strip=True))
            if m:
                price = parse_price(m.group(1))
                if price:
                    break
    # ---- teknik özellikler: tablo, dl, "etiket: değer" listeleri, etiket/değer çiftleri
    specs, seenk = [], set()

    def add(k, v):
        k, v = re.sub(r"\s+", " ", k or "").strip(" :"), re.sub(r"\s+", " ", v or "").strip()
        if k and v and len(k) < 60 and k.lower() not in seenk and k != v:
            seenk.add(k.lower())
            specs.append({"k": k[:60], "v": v[:300]})
    for tr in soup.select("table tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        if len(cells) >= 2:
            add(cells[0], " · ".join(c for c in cells[1:] if c))
    for dl in soup.find_all("dl")[:6]:
        for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
            add(dt.get_text(" ", strip=True), dd.get_text(" ", strip=True))
    for li in soup.select('[class*=spec] li, [class*=ozellik] li, [class*=teknik] li, [class*=attribute] li, [class*=property] li')[:120]:
        t = _txt(li, 300)
        if ":" in t:
            k, v = t.split(":", 1)
            add(k, v)
        else:
            kids = [x for x in li.find_all(["span", "div", "strong", "b", "p"], recursive=False)]
            if len(kids) == 2:
                add(kids[0].get_text(" ", strip=True), kids[1].get_text(" ", strip=True))
    for row in soup.select('[class*=spec-row], [class*=specification] [class*=row], [class*=teknik-row], [class*=property-row]')[:120]:
        kids = [x for x in row.find_all(["span", "div", "p", "strong", "b", "dt", "dd"], recursive=False)]
        if len(kids) >= 2:
            add(kids[0].get_text(" ", strip=True), kids[1].get_text(" ", strip=True))
    nspec = len(specs)
    # ---- belgeler (kılavuz, katalog, broşür)
    docs = 0
    for a in soup.find_all("a", href=True):
        if docs >= 5:
            break
        if re.search(r"\.pdf(\?|$)", a["href"], re.I):
            lbl = _txt(a, 50) or "Belge"
            add(("Belge: " + lbl)[:60], urljoin(url, a["href"]))
            docs += 1
    brand = ld.get("brand")
    brand = brand.get("name") if isinstance(brand, dict) else (brand or "")
    return {"name": re.sub(r"\s+", " ", name).strip(), "description": desc, "images": imgs, "sku": sku, "model": model or sku, "price": price,
            "specs": specs[:80], "brand_site": str(brand or "").strip(), "is_product": bool(ld) or bool(price) or nspec >= 3}


# ------------------------------------------------------------------ kayıt
def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    adm = Depends(require_admin)
    RUNNING = {}

    async def get_src(sid):
        d = await db.brand_sources.find_one({"id": sid}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Kaynak bulunamadı")
        return d

    def clean_src(p, cur=None):
        cur = {**SOURCE_DEFAULT, **(cur or {})}
        out = dict(cur)
        for k in ("name", "brand", "category", "sitemap_url", "link_regex", "site_url", "slug"):
            if k in p:
                out[k] = str(p[k] or "").strip()[:300]
        if "start_urls" in p:
            out["start_urls"] = [u.strip() for u in (p["start_urls"] or []) if re.match(r"^https?://", str(u).strip())][:20]
        for k, lo, hi in (("markup_percent", -50, 500), ("markup_fixed", 0, 1000000), ("round_to", 0, 1000)):
            if k in p:
                out[k] = max(lo, min(hi, _f(p[k])))
        if "max_products" in p:
            out["max_products"] = max(1, min(1000, int(_f(p["max_products"], 150))))
        for k in ("auto_weekly", "new_active"):
            if k in p:
                out[k] = bool(p[k])
        if not out["name"] or not out["brand"]:
            raise HTTPException(422, "Kaynak adı ve marka gerekli")
        if not out["start_urls"] and not out["sitemap_url"] and not out["site_url"]:
            raise HTTPException(422, "Marka sitesi adresi, liste adresi veya sitemap adresi gerekli")
        if out["link_regex"]:
            try:
                re.compile(out["link_regex"])
            except re.error:
                raise HTTPException(422, "Ürün adresi deseni geçersiz")
        return out

    @api_router.get("/admin/brand-sources")
    async def list_sources(_: dict = adm):
        rows = await db.brand_sources.find({}, {"_id": 0}).sort("created_at", 1).to_list(100)
        for r in rows:
            r["product_count"] = await db.shop_products.count_documents({"src.source_id": r["id"]})
            r["no_price"] = await db.shop_products.count_documents({"src.source_id": r["id"], "$or": [{"price": 0}, {"price": {"$exists": False}}]})
        return {"sources": rows, "presets": PRESETS}

    @api_router.post("/admin/brand-sources")
    async def create_source(payload: dict, _: dict = adm):
        doc = clean_src(payload)
        doc.update({"id": uuid.uuid4().hex, "created_at": _now(), "last_run": "", "last_result": {}, "status": {"state": "idle"}})
        await db.brand_sources.insert_one(dict(doc))
        doc.pop("_id", None)
        return doc

    @api_router.put("/admin/brand-sources/{sid}")
    async def update_source(sid: str, payload: dict, _: dict = adm):
        cur = await get_src(sid)
        upd = clean_src(payload, cur)
        await db.brand_sources.update_one({"id": sid}, {"$set": {k: upd[k] for k in SOURCE_DEFAULT}})
        return {**cur, **upd}

    @api_router.delete("/admin/brand-sources/{sid}")
    async def delete_source(sid: str, remove_products: bool = False, _: dict = adm):
        await get_src(sid)
        await db.brand_sources.delete_one({"id": sid})
        n = 0
        if remove_products:
            n = (await db.shop_products.delete_many({"src.source_id": sid})).deleted_count
        return {"ok": True, "removed_products": n}

    # --------------------------------------------------------- çalıştır
    async def reprice_product(p, src):
        base = _f((p.get("src") or {}).get("base_price"))
        if p.get("price_manual") or base <= 0:
            return False
        np_ = sale_price(base, src)
        if abs(np_ - _f(p.get("price"))) < 0.005:
            return False
        await db.shop_products.update_one({"id": p["id"]}, {"$set": {"price": np_, "updated_at": _now()}})
        return True

    def run_scrape(src, set_status):
        """Bloklayıcı kısım: (liste, ürün sayfaları) -> ayrıştırılmış ürünler"""
        f = Fetcher()
        links = collect_links(f, src)
        set_status(msg=f"{len(links)} adres bulundu, ürün sayfaları okunuyor…", total=min(len(links), src["max_products"]))
        items, miss = [], 0
        for i, u in enumerate(links):
            if len(items) >= src["max_products"]:
                break
            r = f.get(u)
            if not r:
                miss += 1
                continue
            try:
                p = parse_product(r.text, u)
            except Exception:                           # noqa: BLE001
                miss += 1
                continue
            if p["name"] and (p["is_product"] or (src.get("link_regex") and (p["images"] or p["description"]))):
                p["url"] = u
                items.append(p)
            set_status(done=len(items), msg=f"{len(items)} ürün okundu ({i + 1}/{len(links)} sayfa)")
        return items, {"links": len(links), "unreadable": miss, "robots_blocked": f.skipped_robots, "errors": f.errs[:4]}

    async def apply_items(src, items):
        added = updated = repriced = nopr = 0
        for it in items:
            cur = await db.shop_products.find_one({"src.source_id": src["id"], "src.url": it["url"]}, {"_id": 0})
            base = it["price"] or _f(((cur or {}).get("src") or {}).get("base_price"))
            if cur:
                upd = {"updated_at": _now(), "src.fetched_at": _now()}
                if not cur.get("locked"):
                    upd.update({"name": it["name"][:160], "description": it["description"][:12000], "specs": it["specs"], "model": it.get("model", ""),
                                "images": it["images"] or cur.get("images", []), "short": (it["description"] or "")[:240]})
                if it["price"]:
                    upd["src.base_price"] = it["price"]
                await db.shop_products.update_one({"id": cur["id"]}, {"$set": upd})
                cur2 = await db.shop_products.find_one({"id": cur["id"]}, {"_id": 0})
                if await reprice_product(cur2, src):
                    repriced += 1
                updated += 1
            else:
                price = sale_price(base, src)
                doc = shopmod.clean_product({"name": it["name"], "brand": src["brand"], "category": src["category"] or guess_category(it["name"], it["url"]), "description": it["description"],
                                             "short": (it["description"] or "")[:240], "specs": it["specs"], "images": it["images"], "sku": it["sku"],
                                             "model": it.get("model", ""), "price": price, "track_stock": False, "stock": 0, "active": bool(src["new_active"] and price > 0)})
                slug = shopmod.slugify(f"{src['brand']}-{it['name']}")
                n = 2
                base_slug = slug
                while await db.shop_products.find_one({"slug": slug}):
                    slug, n = f"{base_slug}-{n}", n + 1
                doc.update({"id": uuid.uuid4().hex, "slug": slug, "created_at": _now(), "updated_at": _now(), "sold": 0,
                            "src": {"source_id": src["id"], "url": it["url"], "base_price": base, "fetched_at": _now()}, "price_manual": False})
                await db.shop_products.insert_one(dict(doc))
                added += 1
            if base <= 0:
                nopr += 1
        return {"added": added, "updated": updated, "repriced": repriced, "no_price": nopr}

    async def do_run(sid):
        src = await get_src(sid)
        loop = asyncio.get_running_loop()
        state = {"state": "running", "done": 0, "total": 0, "msg": "Başladı…", "started": _now()}
        RUNNING[sid] = state

        def set_status(**kw):
            state.update(kw)
        try:
            items, info = await asyncio.to_thread(run_scrape, src, set_status)
            state["msg"] = "Mağazaya kaydediliyor…"
            res = await apply_items(src, items)
            res.update(info)
            res["found"] = len(items)
            state.update({"state": "done", "msg": f"Bitti: {res['added']} yeni, {res['updated']} güncellendi"})
            await db.brand_sources.update_one({"id": sid}, {"$set": {"last_run": _now(), "last_result": res, "status": {"state": "done"}}})
        except Exception as e:                          # noqa: BLE001
            log.exception("brand run")
            state.update({"state": "error", "msg": str(e)[:300]})
            await db.brand_sources.update_one({"id": sid}, {"$set": {"last_run": _now(), "last_result": {"error": str(e)[:300]}}})
        finally:
            await asyncio.sleep(0)
        return state

    @api_router.post("/admin/brand-sources/{sid}/run")
    async def run_source(sid: str, _: dict = adm):
        await get_src(sid)
        st = RUNNING.get(sid)
        if st and st.get("state") == "running":
            return {"ok": True, "already": True}
        RUNNING[sid] = {"state": "running", "done": 0, "total": 0, "msg": "Başladı…"}
        asyncio.get_running_loop().create_task(do_run(sid))
        return {"ok": True}

    @api_router.get("/admin/brand-sources/{sid}/status")
    async def source_status(sid: str, _: dict = adm):
        s = RUNNING.get(sid)
        if s:
            return s
        d = await get_src(sid)
        return {"state": "idle", "last_run": d.get("last_run"), "last_result": d.get("last_result")}

    # --------------------------------------------------------- fiyat
    @api_router.get("/admin/brand-sources/{sid}/products")
    async def source_products(sid: str, _: dict = adm):
        src = await get_src(sid)
        rows = await db.shop_products.find({"src.source_id": sid}, {"_id": 0}).sort("name", 1).to_list(2000)
        return {"source": src, "products": [{"id": r["id"], "name": r["name"], "sku": r.get("sku", ""), "image": (r.get("images") or [""])[0],
                                              "url": (r.get("src") or {}).get("url", ""), "base_price": _f((r.get("src") or {}).get("base_price")),
                                              "price": _f(r.get("price")), "active": bool(r.get("active")), "price_manual": bool(r.get("price_manual")),
                                              "locked": bool(r.get("locked"))} for r in rows]}

    @api_router.put("/admin/brand-products/{pid}")
    async def set_product(pid: str, payload: dict, _: dict = adm):
        p = await db.shop_products.find_one({"id": pid}, {"_id": 0})
        if not p or not p.get("src"):
            raise HTTPException(404, "Ürün bulunamadı")
        src = await get_src(p["src"]["source_id"])
        upd = {"updated_at": _now()}
        if "base_price" in payload:
            base = max(0.0, _f(payload["base_price"]))
            upd["src.base_price"] = base
            if not p.get("price_manual"):
                upd["price"] = sale_price(base, src)
        if "price" in payload and payload["price"] not in (None, ""):
            upd["price"] = max(0.0, _f(payload["price"]))
            upd["price_manual"] = True
        if payload.get("auto_price"):
            upd["price_manual"] = False
            upd["price"] = sale_price(_f((p.get("src") or {}).get("base_price")), src)
        if "active" in payload:
            if payload["active"] and _f(upd.get("price", p.get("price"))) <= 0:
                raise HTTPException(422, "Fiyatı olmayan ürün yayına alınamaz")
            upd["active"] = bool(payload["active"])
        if "locked" in payload:
            upd["locked"] = bool(payload["locked"])
        await db.shop_products.update_one({"id": pid}, {"$set": upd})
        return {"ok": True, "price": upd.get("price", p.get("price"))}

    @api_router.post("/admin/brand-sources/{sid}/reprice")
    async def reprice_all(sid: str, payload: dict, _: dict = adm):
        src = await get_src(sid)
        if payload:
            src = clean_src(payload, src)
            await db.brand_sources.update_one({"id": sid}, {"$set": {k: src[k] for k in SOURCE_DEFAULT}})
        n = 0
        for p in await db.shop_products.find({"src.source_id": sid}, {"_id": 0}).to_list(5000):
            if await reprice_product(p, src):
                n += 1
        return {"ok": True, "repriced": n}

    @api_router.post("/admin/brand-sources/{sid}/prices-csv")
    async def prices_csv(sid: str, payload: dict, _: dict = adm):
        """CSV: ürün adı veya SKU ; liste fiyatı  (ayraç ; , veya sekme)"""
        src = await get_src(sid)
        text = str(payload.get("csv") or "")
        if not text.strip():
            raise HTTPException(422, "Boş dosya")
        delim = max([";", ",", "\t"], key=lambda d: text[:2000].count(d))
        prods = await db.shop_products.find({"src.source_id": sid}, {"_id": 0}).to_list(5000)
        by_sku = {p.get("sku", "").lower(): p for p in prods if p.get("sku")}
        norm = lambda s: re.sub(r"[^a-z0-9]", "", shopmod.slugify(s))
        by_name = {norm(p["name"]): p for p in prods}
        ok = miss = 0
        misses = []
        for row in csv.reader(io.StringIO(text), delimiter=delim):
            if len(row) < 2:
                continue
            key, price = row[0].strip(), parse_price(row[1])
            if price <= 0:
                continue
            p = by_sku.get(key.lower()) or by_name.get(norm(key))
            if not p:
                for pn, pp in by_name.items():                 # kısmi eşleşme
                    if norm(key) and (norm(key) in pn or pn in norm(key)) and len(norm(key)) > 5:
                        p = pp
                        break
            if not p:
                miss += 1
                misses.append(key[:60])
                continue
            upd = {"src.base_price": price, "updated_at": _now()}
            if not p.get("price_manual"):
                upd["price"] = sale_price(price, src)
            await db.shop_products.update_one({"id": p["id"]}, {"$set": upd})
            ok += 1
        return {"ok": True, "matched": ok, "unmatched": miss, "unmatched_names": misses[:20]}

    @api_router.post("/admin/brand-sources/{sid}/activate-priced")
    async def activate_priced(sid: str, _: dict = adm):
        await get_src(sid)
        r = await db.shop_products.update_many({"src.source_id": sid, "price": {"$gt": 0}, "active": False}, {"$set": {"active": True, "updated_at": _now()}})
        return {"ok": True, "activated": r.modified_count}

    # --------------------------------------------------------- KOLAY MOD: marka merkezi
    HQ = {"state": "idle", "current": "", "done": 0, "total": 0, "log": {}}
    BR = {b[0]: b for b in HUB_BRANDS}

    async def hub_src(slug, create=True):
        d = await db.brand_sources.find_one({"slug": slug}, {"_id": 0})
        if d or not create:
            return d
        _, name, url = BR[slug]
        doc = {**SOURCE_DEFAULT, "name": name, "brand": name, "slug": slug, "site_url": url, "new_active": True, "markup_percent": 20.0, "max_products": 400,
               **{k: v for k, v in HUB_EXTRA.get(slug, {}).items() if url}, 
               "id": uuid.uuid4().hex, "created_at": _now(), "last_run": "", "last_result": {}, "status": {"state": "idle"}}
        await db.brand_sources.insert_one(dict(doc))
        doc.pop("_id", None)
        return doc

    async def hub_cfg():
        c = await db.brand_hub_cfg.find_one({"_id": "cfg"})
        if not c:
            # ilk kurulumda otomatik güncelleme açık gelir; ilk çalışma ~1 saat sonra (adresleri düzeltmeniz için zaman)
            c = {"_id": "cfg", "auto": True, "interval_h": 24, "last_auto": (datetime.now(timezone.utc) - timedelta(hours=23)).isoformat(), "last_done": "", "last_log": {}, "last_ok": 0, "last_total": 0}
            await db.brand_hub_cfg.insert_one(dict(c))
        c.pop("_id", None)
        return c

    @api_router.put("/admin/brand-hub-cfg")
    async def hub_cfg_set(payload: dict, _: dict = adm):
        await hub_cfg()
        upd = {}
        if "auto" in payload:
            upd["auto"] = bool(payload["auto"])
        if "interval_h" in payload:
            upd["interval_h"] = int(builtins.max(6, min(168, _f(payload["interval_h"], 24))))
        if upd:
            await db.brand_hub_cfg.update_one({"_id": "cfg"}, {"$set": upd})
        return {"ok": True}

    @api_router.get("/admin/brand-hub")
    async def hub_list(_: dict = adm):
        rows = []
        for slug, name, url in HUB_BRANDS:
            d = await db.brand_sources.find_one({"slug": slug}, {"_id": 0})
            r = {"slug": slug, "name": name, "site_url": (d or {}).get("site_url", url) if d else url, "id": (d or {}).get("id", ""),
                 "markup_percent": (d or {}).get("markup_percent", 20.0), "last_run": (d or {}).get("last_run", ""), "last": (d or {}).get("last_result", {}),
                 "count": 0, "active": 0, "no_price": 0, "state": (RUNNING.get((d or {}).get("id", ""), {}) or {}).get("state", "idle")}
            if d:
                r["count"] = await db.shop_products.count_documents({"src.source_id": d["id"]})
                r["active"] = await db.shop_products.count_documents({"src.source_id": d["id"], "active": True})
                r["no_price"] = await db.shop_products.count_documents({"src.source_id": d["id"], "$or": [{"price": 0}, {"price": {"$exists": False}}]})
            rows.append(r)
        return {"brands": rows, "queue": HQ, "cfg": await hub_cfg()}

    @api_router.put("/admin/brand-hub/{slug}")
    async def hub_set(slug: str, payload: dict, _: dict = adm):
        if slug not in BR:
            raise HTTPException(404, "Marka yok")
        d = await hub_src(slug)
        upd = {}
        if "site_url" in payload:
            u = str(payload["site_url"] or "").strip()
            if u and not re.match(r"^https?://", u):
                u = "https://" + u
            upd["site_url"] = u
            mk = market_cfg(u) if u else None
            if mk:                                       # pazaryeri/mağaza sayfası: liste sayfaları + ürün deseni otomatik
                upd.update(mk)
                if "markup_percent" in payload:
                    upd["markup_percent"] = max(-50.0, min(500.0, _f(payload["markup_percent"])))
                await db.brand_sources.update_one({"id": d["id"]}, {"$set": upd})
                return {"ok": True, "market": True}
            upd["start_urls"] = []
            upd["sitemap_url"] = ""
            upd["link_regex"] = ""
            if u and BR[slug][2] and urlparse(u).netloc == urlparse(BR[slug][2]).netloc:   # aynı site ise doğrulanmış ayarları geri yükle
                upd.update({k: v for k, v in HUB_EXTRA.get(slug, {}).items()})
        if "markup_percent" in payload:
            upd["markup_percent"] = max(-50.0, min(500.0, _f(payload["markup_percent"])))
        if upd:
            await db.brand_sources.update_one({"id": d["id"]}, {"$set": upd})
        return {"ok": True}

    def _why(r):
        if not r.get("links"):
            e = (r.get("errors") or [""])[0]
            return "ürün adresi bulunamadı" + (" · " + e if e else "")
        if r.get("robots_blocked"):
            return "robots.txt ürün sayfalarını engelliyor (%d adres)" % r["robots_blocked"]
        e = (r.get("errors") or [""])[0]
        return "%d adres bulundu ama ürün okunamadı" % r["links"] + (" · " + e if e else "")

    async def hub_worker(slugs):
        HQ.update({"state": "running", "done": 0, "total": len(slugs), "log": {}, "current": ""})
        for slug in slugs:
            HQ["current"] = BR[slug][1]
            try:
                d = await hub_src(slug)
                dflt = BR[slug][2]
                if dflt and slug in HUB_EXTRA and urlparse(d.get("site_url") or dflt).netloc == urlparse(dflt).netloc:
                    ex = dict(HUB_EXTRA[slug])
                    await db.brand_sources.update_one({"id": d["id"]}, {"$set": ex})
                    d.update(ex)
                if not d.get("site_url") and not d.get("start_urls"):
                    HQ["log"][slug] = "Site adresi yok"
                else:
                    st = await do_run(d["id"])
                    r = (await get_src(d["id"])).get("last_result") or {}
                    HQ["log"][slug] = st.get("msg", "") if st.get("state") == "error" else ("%d ürün" % r.get("found", 0) + ("" if r.get("found") else " — " + _why(r)))
            except Exception as e:                      # noqa: BLE001
                HQ["log"][slug] = "Hata: " + str(e)[:80]
            HQ["done"] += 1
        HQ.update({"state": "done", "current": ""})
        try:
            ok = sum(1 for v in HQ["log"].values() if re.match(r"^[1-9]\d* ürün", v))
            await db.brand_hub_cfg.update_one({"_id": "cfg"}, {"$set": {"last_done": _now(), "last_log": dict(HQ["log"]), "last_ok": ok, "last_total": len(slugs)}}, upsert=True)
        except Exception:                               # noqa: BLE001
            pass

    @api_router.get("/admin/brand-hub/{slug}/diag")
    async def hub_diag(slug: str, _: dict = adm):
        """Siteye gerçekten ulaşılıyor mu, liste sayfasında kaç ürün adresi görünüyor? (sorun tespiti)"""
        if slug not in BR:
            raise HTTPException(404, "Marka yok")
        d = await hub_src(slug)

        def work():
            f = Fetcher()
            out = {"site": d.get("site_url"), "start_urls": (d.get("start_urls") or [])[:3], "link_regex": d.get("link_regex"), "steps": []}
            tests = (d.get("start_urls") or [])[:2] or [d.get("site_url")]
            for u in tests:
                if not u:
                    continue
                st = {"url": u}
                try:
                    r = f.s.get(u, timeout=20)
                    st.update({"http": r.status_code, "bytes": len(r.content), "final": r.url[:120], "robots_ok": f.allowed(u)})
                    soup = BeautifulSoup(r.text, "html.parser")
                    hrefs = [urldefrag(urljoin(u, a["href"]))[0] for a in soup.find_all("a", href=True)]
                    st["links_total"] = len(hrefs)
                    pat = re.compile(d["link_regex"]) if d.get("link_regex") else None
                    m = [h for h in dict.fromkeys(hrefs) if pat and pat.search(urlparse(h).path)]
                    st["product_links"] = len(m)
                    st["sample"] = m[:3]
                    st["title"] = (soup.title.get_text(strip=True) if soup.title else "")[:80]
                    if r.status_code != 200 or len(r.content) < 2000:
                        st["body_start"] = r.text[:200]
                except Exception as e:                  # noqa: BLE001
                    st["error"] = str(e)[:150]
                out["steps"].append(st)
            return out
        return await asyncio.to_thread(work)

    @api_router.post("/admin/brand-hub/run")
    async def hub_run(payload: dict, _: dict = adm):
        if HQ["state"] == "running":
            return {"ok": True, "already": True}
        slugs = [x for x in (payload.get("slugs") or []) if x in BR] or [b[0] for b in HUB_BRANDS]
        asyncio.get_running_loop().create_task(hub_worker(slugs))
        return {"ok": True, "count": len(slugs)}

    @api_router.post("/admin/brand-hub/markup")
    async def hub_markup(payload: dict, _: dict = adm):
        pct = max(-50.0, min(500.0, _f(payload.get("percent"))))
        upd = {"markup_percent": pct}
        for k in ("fixed", "round_to"):
            if k in payload:
                upd["markup_fixed" if k == "fixed" else "round_to"] = max(0.0, _f(payload[k]))
        await db.brand_sources.update_many({"slug": {"$ne": ""}}, {"$set": upd})
        n = 0
        for src in await db.brand_sources.find({}, {"_id": 0}).to_list(500):
            for p in await db.shop_products.find({"src.source_id": src["id"]}, {"_id": 0}).to_list(5000):
                if await reprice_product(p, src):
                    n += 1
        return {"ok": True, "repriced": n}

    @api_router.post("/admin/brand-hub/publish")
    async def hub_publish(_: dict = adm):
        ids = [s["id"] for s in await db.brand_sources.find({}, {"id": 1, "_id": 0}).to_list(500)]
        r = await db.shop_products.update_many({"src.source_id": {"$in": ids}, "price": {"$gt": 0}, "active": False}, {"$set": {"active": True, "updated_at": _now()}})
        return {"ok": True, "activated": r.modified_count}

    # --------------------------------------------------------- haftalık otomatik
    async def hook(_db):
        try:
            for s in await db.brand_sources.find({"auto_weekly": True, "slug": {"$in": ["", None]}}, {"_id": 0}).to_list(50):
                last = s.get("last_run") or ""
                if last and datetime.fromisoformat(last) > datetime.now(timezone.utc) - timedelta(days=7):
                    continue
                if RUNNING.get(s["id"], {}).get("state") == "running":
                    continue
                await do_run(s["id"])
        except Exception as e:                          # noqa: BLE001
            log.warning("brand hook: %s", e)

    async def hub_hook(_db):
        try:
            c = await hub_cfg()
            if not c.get("auto") or HQ["state"] == "running":
                return
            last = c.get("last_auto") or ""
            if last and datetime.fromisoformat(last) > datetime.now(timezone.utc) - timedelta(hours=int(c.get("interval_h") or 24)):
                return
            await db.brand_hub_cfg.update_one({"_id": "cfg"}, {"$set": {"last_auto": _now()}})
            slugs = [b[0] for b in HUB_BRANDS if (await db.brand_sources.find_one({"slug": b[0]}, {"site_url": 1, "start_urls": 1}) or {"site_url": b[2]}).get("site_url")]
            if slugs:
                asyncio.get_running_loop().create_task(hub_worker(slugs))
        except Exception as e:                          # noqa: BLE001
            log.warning("brand hub hook: %s", e)

    governance.HOOKS.append(hook)
    governance.HOOKS.append(hub_hook)
