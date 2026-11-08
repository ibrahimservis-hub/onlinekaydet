"""Pazarlama Merkezi (2/2): organik görünürlük ve site sağlığı.

- Site tarayıcı: Google Ads uyumluluk kontrolü + SEO denetimi (kırık link, başlık/açıklama, şema, marka ibaresi, iddialar)
- Search Console senkronu (sorgu/sayfa/ilçe, sıra kaybedenler, fırsatlar, dizin durumu) - canlı hesapla DENENMEDİ
- İlçe/mahalle sayfa üretici (taslak olarak Stüdyo'ya yazar), sayfa performansı (SEO + iş getirisi), tekrar/ince içerik uyarısı
- Yapılandırılmış veri (LocalBusiness / Service) - site JS'i /api/public/schema'dan ekler
- Google İşletme Profili istatistikleri (elle/CSV) ve yorum paneli (yanıt taslağı: AI veya şablon)
"""
import asyncio
import csv
import hashlib
import io
import re
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, urljoin, quote

import requests
from fastapi import Depends, HTTPException, Response

import insights
import mkt
from mkt import _f, _now, _today, _tr_day, slug, lower_tr, get_cfg

try:
    from bs4 import BeautifulSoup
except Exception:                                      # pragma: no cover
    BeautifulSoup = None

BRANDS = ["demirdöküm", "bosch", "vaillant", "baymak", "arçelik", "beko", "siemens", "samsung", "lg", "eca", "buderus", "viessmann", "ariston",
          "alarko", "protherm", "airfel", "daikin", "mitsubishi", "vestel", "profilo", "miele", "altus", "regal", "uğur", "e.c.a"]
CLAIMS = [(r"en ucuz", "'en ucuz' iddiası"), (r"\ben iyi\b", "'en iyi' üstünlük iddiası"), (r"1 numaral|bir numaral|numara 1", "'1 numara' iddiası"),
          (r"%\s?100\b|yüzde yüz", "%100 iddiası"), (r"garantili (sonuç|tamir|çözüm)", "garantili sonuç iddiası"),
          (r"ücretsiz (keşif|servis|arıza|montaj)", "'ücretsiz' keşif/servis iddiası (koşullarını belirtin)"),
          (r"son \d+ (dakika|saat|kişi)|bugüne özel|stoklarla sınırlı", "yapay aciliyet ifadesi"),
          (r"15 dakikada|30 dakikada|anında (servis|kapınızda)", "süre taahhüdü (doğrulanabilir olmalı)")]
DISCLAIMER_RE = r"yetkili servis(i)? değil|yetkili servis olmad|bağımsız (servis|firma|işletme)|ticari marka|sahiplerine aittir|ilgili firmalara aittir|marka adları"
SERVICES = {
    "kombi": ("Kombi Servisi", ["Kombi petekleri yeterince ısıtmıyor", "Kombi hata kodu veriyor", "Kombide basınç düşüyor", "Sıcak su gelmiyor veya dalgalanıyor",
                                "Kombi su kaçırıyor", "Kombi ses yapıyor ya da sürekli kapanıp açılıyor"]),
    "klima": ("Klima Servisi", ["Klima soğutmuyor veya ısıtmıyor", "İç üniteden su damlıyor", "Klima çalışmıyor / kumandaya tepki vermiyor", "Dış ünite devreye girmiyor",
                                "Klima kötü kokuyor", "Periyodik bakım ve gaz kontrolü"]),
    "beyaz-esya": ("Beyaz Eşya Servisi", ["Buzdolabı soğutmuyor", "Çamaşır makinesi sıkmıyor veya su almıyor", "Bulaşık makinesi su boşaltmıyor",
                                          "Kurutma makinesi kurutmuyor", "Fırın ısınmıyor", "Cihaz hata kodu gösteriyor"]),
    "buzdolabi": ("Buzdolabı Servisi", ["Buzdolabı soğutmuyor", "Buzdolabı buzlanma yapıyor", "Kompresör sürekli çalışıyor", "Buzdolabı su akıtıyor", "Garip ses geliyor"]),
    "camasir-makinesi": ("Çamaşır Makinesi Servisi", ["Çamaşır makinesi sıkmıyor", "Su boşaltmıyor", "Su almıyor", "Titreşim ve yüksek ses", "Kapak kilitlenmiyor"]),
    "bulasik-makinesi": ("Bulaşık Makinesi Servisi", ["Su boşaltmıyor", "Temiz yıkamıyor", "Su almıyor", "Kurutmuyor", "Hata kodu veriyor"]),
    "kurutma-makinesi": ("Kurutma Makinesi Servisi", ["Kurutmuyor", "Isıtmıyor", "Ses yapıyor", "Çalışmıyor", "Su haznesi dolum uyarısı"]),
}


def _pick(opts, seed):
    return opts[int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(opts)]


def _norm_path(p):
    p = (urlparse(p or "/").path or "/")
    return p.rstrip("/") or "/"


def _words(blocks):
    t = " ".join(re.sub("<[^>]+>", " ", str(b.get("text", "")) + " " + " ".join(map(str, b.get("items") or []))) for b in blocks)
    t += " ".join(f"{i.get('q', '')} {i.get('a', '')}" for b in blocks if b.get("type") == "faq" for i in (b.get("items") or []))
    return t


def _shingles(text, n=4):
    w = re.findall(r"\w+", lower_tr(text))
    return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def _jac(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


# ============================================================ site tarayıcı
def _fetch(url):
    r = requests.get(url, headers={"User-Agent": "ServisPlus-Audit/1.0"}, timeout=10, allow_redirects=True)
    ct = r.headers.get("content-type", "")
    if not ("html" in ct or "xml" in ct or "text" in ct):
        return r.status_code, "", r.url
    try:                                               # charset başlığı yoksa requests ISO-8859-1 varsayar; Türkçe sayfalar UTF-8'dir
        txt = r.content.decode("utf-8")
    except UnicodeDecodeError:
        txt = r.text
    return r.status_code, txt, r.url


def analyze_page(url, html):
    soup = BeautifulSoup(html, "html.parser")
    ld = []
    for s in soup.find_all("script", attrs={"type": "application/ld+json"}):
        ld += re.findall(r'"@type"\s*:\s*"([^"]+)"', s.string or s.get_text() or "")
    for s in soup(["script", "style", "noscript"]):
        s.extract()
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    md = soup.find("meta", attrs={"name": "description"})
    rb = soup.find("meta", attrs={"name": "robots"})
    can = soup.find("link", rel="canonical")
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
    host = urlparse(url).netloc
    links = []
    for a in soup.find_all("a", href=True):
        h = a["href"].strip()
        if h.startswith(("mailto:", "tel:", "javascript:", "#", "whatsapp:")):
            continue
        full = urljoin(url, h).split("#")[0]
        if urlparse(full).netloc == host:
            links.append(full)
    return {"url": url, "title": title, "desc": (md.get("content") or "").strip() if md else "", "h1": len(soup.find_all("h1")),
            "canonical": (can.get("href") if can else "") or "", "noindex": bool(rb and "noindex" in (rb.get("content") or "").lower()),
            "words": len(re.findall(r"\w+", text)), "imgs_noalt": sum(1 for i in soup.find_all("img") if not (i.get("alt") or "").strip()),
            "ld": ld, "text": lower_tr(text), "links": links, "viewport": bool(soup.find("meta", attrs={"name": "viewport"})),
            "tel": bool(soup.find("a", href=re.compile(r"^tel:", re.I)))}


def crawl(site, limit=25):
    host = urlparse(site).netloc
    queue, seen, pages, links_all, statuses = [site + "/"], set(), [], defaultdict(set), {}
    try:
        st, txt, _ = _fetch(site + "/sitemap.xml")
        if st == 200:
            locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", txt)
            subs = [l for l in locs if l.endswith(".xml")][:5]
            for sm in subs:
                try:
                    s2, t2, _ = _fetch(sm)
                    locs += re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", t2) if s2 == 200 else []
                except Exception:                      # noqa: BLE001
                    pass
            queue += [l for l in locs if urlparse(l).netloc == host and not l.endswith(".xml")]
    except Exception:                                  # noqa: BLE001
        pass
    while queue and len(pages) < limit:
        u = queue.pop(0).split("#")[0]
        key = u.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        try:
            st, html, final = _fetch(u)
        except Exception as e:                         # noqa: BLE001
            statuses[u] = f"hata: {str(e)[:60]}"
            continue
        statuses[u] = st
        if st != 200 or not html:
            continue
        a = analyze_page(final or u, html)
        pages.append(a)
        for l in a["links"]:
            links_all[l.split("#")[0]].add(u)
            if l.rstrip("/") not in seen and not re.search(r"\.(jpg|jpeg|png|webp|gif|svg|pdf|css|js|ico|xml|zip)(\?|$)", l, re.I):
                queue.append(l)
    return pages, links_all, statuses


def evaluate(site, pages, links_all, statuses, disclaimer=""):
    F = []

    def add(level, code, title, detail="", page=""):
        F.append({"level": level, "code": code, "title": title, "detail": detail, "page": page})

    if not pages:
        add("kritik", "no_pages", "Site taranamadı", "Ana sayfa açılmadı veya içerik alınamadı (adresi ve sunucu erişimini kontrol edin).")
        return F, 0
    if not site.startswith("https://"):
        add("kritik", "https", "Site HTTPS değil", "Reklam politikaları ve güven için tüm site HTTPS olmalı.")
    alltext = " ".join(p["text"] for p in pages)
    urls = " ".join(list(links_all.keys()) + [p["url"] for p in pages]).lower()
    for code, label, keys, lvl in (("privacy", "Gizlilik/KVKK sayfası", ("gizlilik", "kvkk", "aydinlatma"), "kritik"),
                                   ("contact", "İletişim sayfası", ("iletisim",), "kritik"),
                                   ("about", "Hakkımızda sayfası", ("hakkimizda", "hakkinda", "kurumsal"), "uyari"),
                                   ("terms", "Kullanım koşulları / hizmet şartları", ("kullanim", "sartlar", "mesafeli", "terms"), "bilgi")):
        if not any(k in urls for k in keys):
            add(lvl, "missing_" + code, f"{label} bulunamadı", "Site içinde bu sayfaya bağlantı yok. Google Ads uyumluluğu için şeffaf işletme bilgisi önemlidir.")
    home = pages[0]
    if not re.search(r"(\+?90|0)?\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}", home["text"]) and not home["tel"]:
        add("uyari", "no_phone", "Ana sayfada telefon görünmüyor")
    if not re.search(r"mahalle|mah\.|cadde|cad\.|sokak|sok\.|no\s?:\s?\d|bulvar", alltext):
        add("uyari", "no_address", "Sitede açık adres bilgisi yok", "Fiziksel adres/firma unvanı göstermek güveni ve reklam onayını artırır.")
    brands_found = sorted({b for b in BRANDS if len(b) > 3 and re.search(r"\b" + re.escape(b) + r"\b", alltext)})
    has_disc = bool(re.search(DISCLAIMER_RE, alltext))
    if "yetkili servis" in alltext and not has_disc:
        add("kritik", "authorized_claim", "'Yetkili servis' ifadesi var, açıklama yok",
            "Marka yetkili servisi değilseniz bu ifade yanıltıcı sayılabilir (reklam kısıtlamasının sık nedeni). Footer'a 'markaların yetkili servisi değiliz; marka adları sahiplerine aittir' benzeri net ibare ekleyin.")
    elif brands_found and not has_disc:
        add("uyari", "brand_disclaimer", "Marka adları geçiyor, ticari marka/bağımsızlık ibaresi yok", "Geçen markalar: " + ", ".join(brands_found[:8]) +
            ". Bağımsız servisseniz bunu sitede belirtin; reklam metinlerinde marka adını yetkili gibi kullanmayın.")
    for p in pages:
        for rx, label in CLAIMS:
            if re.search(rx, p["text"]):
                add("uyari", "claim", label, "İddianın sitede doğrulanabilir/koşullu olduğundan emin olun.", p["url"])
        t, d = p["title"], p["desc"]
        if not t:
            add("uyari", "title_missing", "Başlık (title) yok", "", p["url"])
        elif len(t) < 20 or len(t) > 65:
            add("bilgi", "title_len", f"Başlık uzunluğu {len(t)} (ideal 20–65)", t[:80], p["url"])
        if not d:
            add("uyari", "desc_missing", "Meta açıklama yok", "", p["url"])
        elif len(d) < 70 or len(d) > 165:
            add("bilgi", "desc_len", f"Meta açıklama uzunluğu {len(d)} (ideal 70–160)", "", p["url"])
        if p["h1"] != 1:
            add("uyari" if p["h1"] == 0 else "bilgi", "h1", f"H1 sayısı {p['h1']} (1 olmalı)", "", p["url"])
        if p["noindex"]:
            add("uyari", "noindex", "Sayfa noindex", "Bilerek değilse arama sonuçlarında çıkmaz.", p["url"])
        if not p["canonical"]:
            add("bilgi", "canonical", "Canonical etiketi yok", "", p["url"])
        if p["words"] < 150:
            add("bilgi", "thin", f"Az içerik ({p['words']} kelime)", "", p["url"])
        if p["imgs_noalt"]:
            add("bilgi", "alt", f"{p['imgs_noalt']} görselde alt metin yok", "", p["url"])
        if not p["viewport"]:
            add("uyari", "viewport", "Mobil uyumluluk etiketi (viewport) yok", "", p["url"])
    titles = defaultdict(list)
    for p in pages:
        if p["title"]:
            titles[p["title"]].append(p["url"])
    for t, us in titles.items():
        if len(us) > 1:
            add("uyari", "dup_title", f"Aynı başlık {len(us)} sayfada", t[:80] + " → " + ", ".join(us[:3]))
    lds = {x for p in pages for x in p["ld"]}
    if not ({"LocalBusiness", "Organization", "HomeAndConstructionBusiness"} & lds):
        add("bilgi", "schema", "Statik HTML'de LocalBusiness şeması görünmüyor", "Panelin şema betiği JS ile ekliyorsa tarayıcıda görünür; bu tarama JS çalıştırmaz.")
    broken = [(l, st) for l, st in statuses.items() if (isinstance(st, int) and st >= 400) or (isinstance(st, str))]
    for l, st in broken[:25]:
        add("uyari", "broken", f"Kırık bağlantı ({st})", l, ", ".join(sorted(links_all.get(l, [])))[:120])
    score = max(0, 100 - 15 * sum(f["level"] == "kritik" for f in F) - 4 * sum(f["level"] == "uyari" for f in F) - sum(f["level"] == "bilgi" for f in F) // 2)
    return F, score


async def run_audit(db, audit_id, site, limit):
    try:
        pages, links_all, statuses = await asyncio.to_thread(crawl, site, limit)
        # kuyruğa girmeyen iç bağlantıların durumunu da kontrol et (en çok 40)
        extra = [l for l in links_all if l.rstrip("/") not in {s.rstrip("/") for s in statuses}][:40]
        for l in extra:
            try:
                st, _h, _f2 = await asyncio.to_thread(_fetch, l)
                statuses[l] = st
            except Exception as e:                     # noqa: BLE001
                statuses[l] = f"hata: {str(e)[:50]}"
        cfg = await get_cfg(db)
        F, score = evaluate(site, pages, links_all, statuses, cfg.get("disclaimer", ""))
        await db.mkt_audits.update_one({"id": audit_id}, {"$set": {"status": "done", "score": score, "pages": len(pages), "findings": F[:400],
                                                                   "counts": {k: sum(f["level"] == k for f in F) for k in ("kritik", "uyari", "bilgi")},
                                                                   "done_at": _now()}})
    except Exception as e:                             # noqa: BLE001
        await db.mkt_audits.update_one({"id": audit_id}, {"$set": {"status": "error", "error": str(e)[:300], "score": 0}})


# ============================================================ Search Console
async def gsc_sync(db, days=28):
    cfg = await get_cfg(db)
    g = cfg["google"]
    site = g.get("gsc_site") or cfg["site_url"]
    tok = await asyncio.to_thread(mkt.g_token, g, "gsc")
    end = _today() - timedelta(days=2)
    start = end - timedelta(days=max(3, min(int(days), 120)) - 1)
    url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{quote(site, safe='')}/searchAnalytics/query"
    rows, off = [], 0
    while off < 100000:
        body = {"startDate": start.isoformat(), "endDate": end.isoformat(), "dimensions": ["date", "query", "page"], "rowLimit": 25000, "startRow": off}
        r = await asyncio.to_thread(mkt._http, "POST", url, {"Authorization": "Bearer " + tok}, body)
        rr = r.get("rows", [])
        rows += rr
        if len(rr) < 25000:
            break
        off += 25000
    docs = []
    for r in rows:
        k = r.get("keys") or []
        if len(k) < 3:
            continue
        docs.append({"day": k[0], "query": k[1], "page": _norm_path(k[2]), "clicks": int(_f(r.get("clicks"))), "impr": int(_f(r.get("impressions"))),
                     "pos": round(_f(r.get("position")), 2)})
    await db.gsc_rows.delete_many({"day": {"$gte": start.isoformat(), "$lte": end.isoformat()}})
    for i in range(0, len(docs), 5000):
        await db.gsc_rows.insert_many(docs[i:i + 5000])
    await db.app_settings.update_one({"_id": "mkt"}, {"$set": {"last_gsc_sync": _now()}}, upsert=True)
    return len(docs)


def _agg(rows, key):
    a = defaultdict(lambda: {"clicks": 0, "impr": 0, "pw": 0.0})
    for r in rows:
        x = a[key(r)]
        x["clicks"] += r["clicks"]
        x["impr"] += r["impr"]
        x["pw"] += r["pos"] * r["impr"]
    out = {}
    for k, x in a.items():
        out[k] = {"clicks": x["clicks"], "impr": x["impr"], "pos": round(x["pw"] / x["impr"], 1) if x["impr"] else 0,
                  "ctr": round(x["clicks"] / x["impr"] * 100, 1) if x["impr"] else 0}
    return out


async def districts_of(db, cfg):
    s = set(cfg.get("districts") or [])
    for c in await db.customers.find({"district": {"$nin": [None, ""]}}, {"_id": 0, "district": 1}).to_list(20000):
        s.add(c["district"].strip())
    return sorted(d for d in s if 2 < len(d) < 40)


# ============================================================ sayfa üretici
def build_page(city, district, svc_key, neighborhoods, stats, brand, phone, disclaimer, siblings):
    label, faults = SERVICES[svc_key]
    seed = f"{district}|{svc_key}"
    place = f"{city} {district}".strip()
    intro = _pick([
        f"{place} bölgesinde {label.lower()} arayanlar için randevu ve arıza kaydı sayfası. Arıza bilgisini ilettiğinizde ekibimiz sizi arayarak uygun zamanı netleştirir.",
        f"{district} ve çevresindeki {label.lower()} talepleri {brand} ekibi tarafından kayıt altına alınır; cihazın türü, markası ve belirtisi paylaşıldıktan sonra servis planlanır.",
        f"{place} için {label.lower()} hizmeti: arızayı yerinde tespit, sonuçları açıklama ve onayınızla onarım yaklaşımıyla çalışırız.",
        f"{district} içinde bir cihaz arızası mı yaşıyorsunuz? {label} talebinizi bırakın, uygun randevu için sizinle iletişime geçelim.",
    ], seed)
    blocks = [{"type": "paragraph", "text": intro}]
    fl = list(faults)
    k = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(fl)
    fl = fl[k:] + fl[:k]
    blocks += [{"type": "heading", "level": 2, "text": f"{district}'de sık karşılaşılan {label.lower().replace(' servisi', '')} arızaları"},
               {"type": "list", "items": fl[:5]}]
    if stats and stats.get("jobs", 0) >= 3:
        tf = ", ".join(f"{n} ({c})" for n, c in stats["faults"][:3]) if stats.get("faults") else ""
        txt = f"{district} bölgesinde şimdiye kadar {stats['jobs']} servis kaydı oluşturduk."
        if tf:
            txt += f" En sık kaydedilen arıza türleri: {tf}."
        if stats.get("rating"):
            txt += f" Anket veren müşterilerimizin ortalama puanı {stats['rating']}/5."
        blocks += [{"type": "heading", "level": 2, "text": f"{district} bölgesinden gerçek servis verileri"}, {"type": "paragraph", "text": txt}]
    if neighborhoods:
        blocks += [{"type": "heading", "level": 2, "text": f"{district} içinde hizmet verdiğimiz mahalleler"}, {"type": "list", "items": neighborhoods[:30]}]
    blocks += [{"type": "heading", "level": 2, "text": "Nasıl çalışıyoruz?"},
               {"type": "list", "items": ["Arıza bilgisini telefon veya form ile iletirsiniz", "Ekibimiz sizi arayıp uygun randevu saatini netleştirir",
                                          "Usta cihazı yerinde inceler, arıza ve işlem kalemlerini size açıklar", "Onayınızla onarım yapılır; işlem sonunda servis kaydınız iletilir"]}]
    q1 = _pick(["Randevu nasıl alırım?", f"{district}'de servis talebini nasıl oluştururum?"], seed + "q1")
    q2 = _pick(["Fiyat nasıl belirleniyor?", "Servis ücreti ne kadar?"], seed + "q2")
    faq = [{"q": q1, "a": "Sitedeki formu doldurabilir veya telefonla arayabilirsiniz; ekibimiz sizi arayarak uygun saati birlikte belirler."},
           {"q": q2, "a": "Ücret arızanın türüne ve gerekirse değişecek parçaya göre değişir. İnceleme sonrası kalemler size açıklanır, onayınız olmadan işlem yapılmaz."},
           {"q": f"{district} dışındaki bölgelere de geliyor musunuz?", "a": "Hizmet bölgelerimiz sayfada ve iletişim sırasında belirtilir; adresinizi paylaşırsanız kapsama girip girmediğini söyleriz."},
           {"q": "Hangi cihazlara bakıyorsunuz?", "a": "Kombi, klima ve beyaz eşya servisi veriyoruz; cihazın marka ve modelini iletmeniz süreci hızlandırır."}]
    blocks.append({"type": "faq", "items": faq})
    if siblings:
        li = "".join(f'<li><a href="/{s["slug"]}/">{s["district"]} {s["label"]}</a></li>' for s in siblings[:8])
        blocks.append({"type": "html", "html": f"<h2 class=\"section-title\">Diğer hizmet bölgeleri</h2><ul>{li}</ul>"})
    if phone:
        blocks.append({"type": "button", "text": "Hemen Arayın", "href": "tel:" + re.sub(r"[^\d+]", "", phone)})
    if disclaimer:
        blocks.append({"type": "paragraph", "text": disclaimer})
    title = f"{district} {label} | {brand}"
    return {"slug": slug(f"{city}-{district}-{svc_key}-servisi" if svc_key != "beyaz-esya" else f"{city}-{district}-beyaz-esya-servisi"),
            "title": title[:70], "description": f"{place} {label.lower()} talebi: arıza kaydı, randevu ve süreç bilgisi. {brand}."[:158],
            "blocks": blocks, "district": district, "service": svc_key, "label": label}


def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    # ---------------------------------------------------------- tarama
    @api_router.post("/mkt/audit/run")
    async def audit_run(payload: dict, _: dict = Depends(require_admin)):
        if BeautifulSoup is None:
            raise HTTPException(500, "beautifulsoup4 kurulu değil")
        cfg = await get_cfg(db)
        running = await db.mkt_audits.find_one({"status": "running"}, {"_id": 0, "id": 1, "at": 1})
        if running and running["at"] > (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat():
            raise HTTPException(409, "Bir tarama zaten sürüyor")
        site = str((payload or {}).get("site_url") or cfg["site_url"]).rstrip("/")
        limit = max(3, min(int((payload or {}).get("limit") or 25), 120))
        aid = str(uuid.uuid4())
        await db.mkt_audits.insert_one({"id": aid, "status": "running", "site": site, "at": _now(), "score": None, "findings": []})
        asyncio.create_task(run_audit(db, aid, site, limit))
        return {"ok": True, "id": aid}

    @api_router.get("/mkt/audit/latest")
    async def audit_latest(_: dict = Depends(require_admin)):
        a = await db.mkt_audits.find({}, {"_id": 0}).sort("at", -1).to_list(1)
        hist = await db.mkt_audits.find({"status": "done"}, {"_id": 0, "findings": 0}).sort("at", -1).to_list(12)
        return {"audit": a[0] if a else None, "history": hist}

    # ---------------------------------------------------------- şema
    @api_router.get("/public/schema")
    async def public_schema(response: Response, path: str = "/"):
        response.headers["Cache-Control"] = "public, max-age=600"
        cfg = await get_cfg(db)
        b = cfg["business"]
        site = cfg["site_url"]
        live = await db.site_content.find_one({"_id": "live"}, {"_id": 0}) or {"state": {}}
        gl = (live.get("state") or {}).get("global") or {}
        phone = b.get("phone") or gl.get("phone_display") or gl.get("phone") or ""
        addr = b.get("address") or gl.get("address") or ""
        out = []
        if b.get("name") and (phone or addr):
            lb = {"@context": "https://schema.org", "@type": "LocalBusiness", "@id": site + "/#business", "name": b["name"], "url": site}
            if phone:
                lb["telephone"] = phone
            if addr or b.get("city"):
                lb["address"] = {"@type": "PostalAddress", "streetAddress": addr, "addressLocality": b.get("city") or "", "addressCountry": "TR"}
            if b.get("price_range"):
                lb["priceRange"] = b["price_range"]
            if b.get("hours"):
                lb["openingHours"] = b["hours"]
            if b.get("areas"):
                lb["areaServed"] = [{"@type": "AdministrativeArea", "name": a} for a in b["areas"][:40]]
            if b.get("same_as"):
                lb["sameAs"] = b["same_as"]
            if b.get("services"):
                lb["hasOfferCatalog"] = {"@type": "OfferCatalog", "name": "Hizmetler",
                                         "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s}} for s in b["services"][:20]]}
            out.append(lb)
        np_ = _norm_path(path)
        for p in (live.get("state") or {}).get("pages") or []:
            if p.get("generated_by") == "mkt" and p.get("status") == "published" and "/" + p["slug"] == np_:
                out.append({"@context": "https://schema.org", "@type": "Service", "name": p.get("title", ""), "serviceType": p.get("label") or "Teknik servis",
                            "areaServed": {"@type": "AdministrativeArea", "name": p.get("district", "")}, "provider": {"@id": site + "/#business"},
                            "url": f"{site}/{p['slug']}/"})
        return out

    # ---------------------------------------------------------- sayfa üretici
    async def load_state():
        import studio
        d = await db.site_content.find_one({"_id": "draft"}, {"_id": 0})
        live = await db.site_content.find_one({"_id": "live"}, {"_id": 0}) or {"version": 0, "state": studio._clean_state({})}
        return studio._clean_state((d or live)["state"]), (d or {}), live

    async def district_stats(name):
        cu = await db.customers.find({"district": {"$regex": "^" + re.escape(name) + "$", "$options": "i"}}, {"_id": 0, "id": 1}).to_list(5000)
        ids = [c["id"] for c in cu]
        if not ids:
            return {}
        jobs = await db.service_jobs.find({"customer_id": {"$in": ids}}, {"_id": 0, "fault_description": 1, "survey": 1, "status": 1}).to_list(20000)
        cnt = defaultdict(int)
        for j in jobs:
            c = insights.fault_cat(j.get("fault_description"))
            if c != "Diğer":
                cnt[c] += 1
        rt = [(j.get("survey") or {}).get("rating") for j in jobs if (j.get("survey") or {}).get("rating")]
        return {"jobs": len(jobs), "faults": sorted(cnt.items(), key=lambda x: -x[1]), "rating": round(sum(rt) / len(rt), 1) if len(rt) >= 3 else 0}

    async def plan(payload):
        cfg = await get_cfg(db)
        city = str(payload.get("city") or cfg["business"].get("city") or "").strip()
        services = [s for s in (payload.get("services") or ["kombi"]) if s in SERVICES]
        if not services:
            raise HTTPException(422, "Geçerli hizmet seçin: " + ", ".join(SERVICES))
        dists = payload.get("districts") or []
        if not dists:
            raise HTTPException(422, "En az bir ilçe girin")
        st, _d, _l = await load_state()
        existing = {p["slug"]: p for p in st["pages"]}
        brand = cfg["business"].get("name") or "ServisPlus"
        gl = st.get("global") or {}
        phone = cfg["business"].get("phone") or gl.get("phone_display") or gl.get("phone") or ""
        built = []
        for d in dists:
            name = str(d.get("name") if isinstance(d, dict) else d).strip()
            if not name:
                continue
            nb = [str(x).strip() for x in ((d.get("neighborhoods") if isinstance(d, dict) else []) or []) if str(x).strip()]
            stats = await district_stats(name)
            for sv in services:
                built.append(build_page(city, name, sv, nb, stats, brand, phone, cfg.get("disclaimer", ""), []))
        for p in built:   # aynı hizmet için kardeş bağlantılar
            sib = [{"slug": q["slug"], "district": q["district"], "label": q["label"]} for q in built if q["service"] == p["service"] and q["slug"] != p["slug"]]
            if sib:
                li = "".join(f'<li><a href="/{s["slug"]}/">{s["district"]} {s["label"]}</a></li>' for s in sib[:8])
                fi = next((i for i, b in enumerate(p["blocks"]) if b["type"] == "faq"), len(p["blocks"]) - 1)
                p["blocks"].insert(fi + 1, {"type": "html", "html": f'<h2 class="section-title">Diğer hizmet bölgeleri</h2><ul>{li}</ul>'})
        sh = {p["slug"]: _shingles(_words(p["blocks"])) for p in built}
        for p in built:
            others = [_jac(sh[p["slug"]], v) for k, v in sh.items() if k != p["slug"]]
            ex = [_jac(sh[p["slug"]], _shingles(_words(e.get("blocks", [])))) for e in existing.values() if e.get("generated_by") == "mkt" and e["slug"] != p["slug"]]
            p["similarity"] = round(max(others + ex + [0]), 2)
            p["words"] = len(re.findall(r"\w+", _words(p["blocks"])))
            p["exists"] = p["slug"] in existing
            warn = []
            if p["words"] < 250:
                warn.append("ince içerik (<250 kelime): mahalle listesi ve gerçek veri ekleyin")
            if p["similarity"] > 0.6:
                warn.append(f"diğer sayfalara %{int(p['similarity'] * 100)} benziyor — mahalle/yerel bilgi ekleyin yoksa 'kopya içerik' sayılabilir")
            if p["exists"]:
                warn.append("bu adres zaten var, atlanır")
            p["warnings"] = warn
        return built, st

    @api_router.post("/mkt/pages/plan")
    async def pages_plan(payload: dict, _: dict = Depends(require_admin)):
        built, _st = await plan(payload)
        return {"pages": [{k: v for k, v in p.items() if k != "blocks"} for p in built]}

    @api_router.post("/mkt/pages/generate")
    async def pages_generate(payload: dict, user: dict = Depends(require_admin)):
        import studio
        built, st = await plan(payload)
        _s, draft, live = await load_state()
        new = []
        for p in built:
            if p["exists"]:
                continue
            new.append({"id": str(uuid.uuid4()), "slug": p["slug"], "title": p["title"], "description": p["description"], "status": "draft", "noindex": False,
                        "blocks": p["blocks"], "generated_by": "mkt", "district": p["district"], "service": p["service"], "label": p["label"]})
        st["pages"] = list(st["pages"]) + new
        st = studio._clean_state(st)
        await db.site_content.update_one({"_id": "draft"}, {"$set": {"state": st, "dirty": True, "base_version": live.get("version", 0),
                                                                     "updated_at": _now(), "updated_by": user["name"]}}, upsert=True)
        return {"ok": True, "created": len(new), "skipped": len(built) - len(new), "slugs": [n["slug"] for n in new],
                "note": "Sayfalar TASLAK olarak eklendi. Site Stüdyosu → Sayfalar'dan gözden geçirip yayınlayın."}

    # ---------------------------------------------------------- sayfa performansı
    @api_router.get("/mkt/pages")
    async def pages_perf(days: int = 90, _: dict = Depends(require_admin)):
        days = max(7, min(days, 365))
        d1 = _today()
        d0 = (d1 - timedelta(days=days - 1)).isoformat()
        P = defaultdict(lambda: {"sessions": 0, "calls": 0, "forms": 0, "leads": 0, "jobs": 0, "done": 0, "revenue": 0.0,
                                 "gsc_clicks": 0, "gsc_impr": 0, "gsc_pos": 0.0})
        for s in await db.visitor_sessions.find({"day": {"$gte": d0}}, {"_id": 0, "landing_page": 1, "conv_call": 1, "conv_form": 1}).to_list(300000):
            p = P[_norm_path(s.get("landing_page"))]
            p["sessions"] += 1
            p["calls"] += int(s.get("conv_call") or 0)
            p["forms"] += int(s.get("conv_form") or 0)
        for m in await db.contact_messages.find({"created_at": {"$gte": d0}}, {"_id": 0, "source": 1, "page": 1}).to_list(100000):
            P[_norm_path((m.get("source") or {}).get("landing_page") or m.get("page"))]["leads"] += 1
        jobs = await db.service_jobs.find({"created_at": {"$gte": d0}}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(100000)
        att = await mkt.attribution(db, jobs)
        for j in jobs:
            a = att[j["id"]]
            if not a["landing"]:
                continue
            p = P[_norm_path(a["landing"])]
            p["jobs"] += 1
            if j.get("status") in mkt.DONE:
                p["done"] += 1
                p["revenue"] += _f(j.get("total_amount"))
        g0 = (d1 - timedelta(days=28)).isoformat()
        gr = await db.gsc_rows.find({"day": {"$gte": g0}}, {"_id": 0}).to_list(500000)
        for k, v in _agg(gr, lambda r: _norm_path(r["page"])).items():
            p = P[k]
            p["gsc_clicks"], p["gsc_impr"], p["gsc_pos"] = v["clicks"], v["impr"], v["pos"]
        st, _d, _l = await load_state()
        sp = {"/" + p["slug"]: p for p in st["pages"]}
        gen = [p for p in st["pages"] if p.get("generated_by") == "mkt"]
        sh = {p["slug"]: _shingles(_words(p.get("blocks", []))) for p in gen[:300]}
        idx = {i["path"]: i for i in await db.page_index.find({}, {"_id": 0}).to_list(2000)}
        out = []
        for path in set(P) | set(sp):
            v = P[path]
            row = {"path": path, **{k: round(x, 2) if isinstance(x, float) else x for k, x in v.items()}, "studio": path in sp,
                   "status": (sp[path].get("status") if path in sp else ""), "generated": bool(path in sp and sp[path].get("generated_by") == "mkt"),
                   "index": idx.get(path, {}).get("verdict", ""), "index_state": idx.get(path, {}).get("state", "")}
            if path in sp:
                row["words"] = len(re.findall(r"\w+", _words(sp[path].get("blocks", []))))
                s = sp[path]["slug"]
                if s in sh:
                    row["similarity"] = round(max([_jac(sh[s], x) for k, x in sh.items() if k != s] + [0]), 2)
            out.append(row)
        out.sort(key=lambda r: (-(r["done"]), -(r["leads"] + r["calls"]), -r["gsc_clicks"], -r["sessions"]))
        return {"days": days, "rows": out[:300]}

    @api_router.post("/mkt/pages/inspect")
    async def page_inspect(payload: dict, _: dict = Depends(require_admin)):
        cfg = await get_cfg(db)
        g = cfg["google"]
        path = _norm_path(payload.get("path") or "/")
        site = g.get("gsc_site") or cfg["site_url"]
        try:
            tok = await asyncio.to_thread(mkt.g_token, g, "gsc")
            r = await asyncio.to_thread(mkt._http, "POST", "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect", {"Authorization": "Bearer " + tok},
                                        {"inspectionUrl": cfg["site_url"] + (path if path != "/" else "/"), "siteUrl": site})
        except Exception as e:                         # noqa: BLE001
            raise HTTPException(502, "Search Console: " + str(e)[:300])
        ir = (r.get("inspectionResult") or {}).get("indexStatusResult") or {}
        doc = {"path": path, "verdict": ir.get("verdict", ""), "state": ir.get("coverageState", ""), "last_crawl": ir.get("lastCrawlTime", ""),
               "canonical": ir.get("googleCanonical", ""), "at": _now()}
        await db.page_index.update_one({"path": path}, {"$set": doc}, upsert=True)
        return doc

    # ---------------------------------------------------------- GSC raporu
    @api_router.post("/mkt/gsc/sync")
    async def gsc_sync_ep(payload: dict, _: dict = Depends(require_admin)):
        try:
            n = await gsc_sync(db, int((payload or {}).get("days") or 28))
        except Exception as e:                         # noqa: BLE001
            raise HTTPException(502, "Search Console: " + str(e)[:300])
        return {"ok": True, "rows": n}

    @api_router.get("/mkt/gsc/summary")
    async def gsc_summary(days: int = 28, _: dict = Depends(require_admin)):
        days = max(6, min(days, 120))
        rows_all = await db.gsc_rows.find({}, {"_id": 0}).to_list(600000)
        if not rows_all:
            return {"empty": True}
        last = max(r["day"] for r in rows_all)
        from datetime import date as _date
        end = _date.fromisoformat(last)
        start = (end - timedelta(days=days - 1)).isoformat()
        rows = [r for r in rows_all if r["day"] >= start]
        mid = (end - timedelta(days=days // 2 - 1)).isoformat()
        rec = [r for r in rows if r["day"] >= mid]
        pri = [r for r in rows if r["day"] < mid]
        tot = _agg(rows, lambda r: "all").get("all", {"clicks": 0, "impr": 0, "pos": 0, "ctr": 0})
        daily = defaultdict(lambda: [0, 0])
        for r in rows:
            daily[r["day"]][0] += r["clicks"]
            daily[r["day"]][1] += r["impr"]
        q = _agg(rows, lambda r: r["query"])
        pg = _agg(rows, lambda r: r["page"])
        top_q = sorted(({"query": k, **v} for k, v in q.items()), key=lambda x: (-x["clicks"], -x["impr"]))[:40]
        top_p = sorted(({"page": k, **v} for k, v in pg.items()), key=lambda x: (-x["clicks"], -x["impr"]))[:40]
        opp = sorted(({"query": k, **v} for k, v in q.items() if 7 <= v["pos"] <= 20 and v["impr"] >= 20), key=lambda x: -x["impr"])[:25]
        cfg = await get_cfg(db)
        dl = await districts_of(db, cfg)
        dist = []
        for d in dl:
            sd = slug(d)
            sub = [r for r in rows if sd in slug(r["query"]) or sd in slug(r["page"])]
            if sub:
                v = _agg(sub, lambda r: "x")["x"]
                dist.append({"district": d, **v})
        dist.sort(key=lambda x: -x["impr"])
        ra, pa = _agg(rec, lambda r: r["page"]), _agg(pri, lambda r: r["page"])
        losers, gainers = [], []
        for k in set(ra) | set(pa):
            a, b = ra.get(k, {"clicks": 0, "impr": 0, "pos": 0}), pa.get(k, {"clicks": 0, "impr": 0, "pos": 0})
            if b["clicks"] >= 3 and (a["clicks"] <= b["clicks"] * 0.7 or (a["pos"] and b["pos"] and a["pos"] - b["pos"] >= 3)):
                losers.append({"page": k, "clicks_before": b["clicks"], "clicks_now": a["clicks"], "pos_before": b["pos"], "pos_now": a["pos"]})
            elif a["clicks"] >= 3 and a["clicks"] >= b["clicks"] * 1.5:
                gainers.append({"page": k, "clicks_before": b["clicks"], "clicks_now": a["clicks"], "pos_before": b["pos"], "pos_now": a["pos"]})
        losers.sort(key=lambda x: x["clicks_now"] - x["clicks_before"])
        gainers.sort(key=lambda x: x["clicks_before"] - x["clicks_now"])
        return {"empty": False, "from": start, "to": last, "totals": tot, "daily": [{"day": k, "clicks": v[0], "impr": v[1]} for k, v in sorted(daily.items())],
                "queries": top_q, "pages": top_p, "opportunities": opp, "districts": dist[:40], "losers": losers[:20], "gainers": gainers[:20],
                "note": "Search Console verisi 2-3 gün gecikmelidir. 'Fırsat': sıra 7–20 arası, gösterimi yüksek sorgular (ilk sayfaya yakın)."}

    # ---------------------------------------------------------- İşletme Profili
    @api_router.get("/mkt/gbp")
    async def gbp_list(_: dict = Depends(require_admin)):
        rows = await db.gbp_stats.find({}, {"_id": 0}).sort("period", -1).to_list(36)
        for i, r in enumerate(rows):
            nxt = rows[i + 1] if i + 1 < len(rows) else None
            r["delta"] = {k: (r.get(k, 0) - nxt.get(k, 0)) for k in ("search_views", "maps_views", "calls", "directions", "website_clicks")} if nxt else {}
        return {"rows": rows, "note": "Google İşletme Profili API erişimi Google onayı gerektirir; bu yüzden değerler panelden elle/CSV ile girilir (Profil → Performans)."}

    @api_router.post("/mkt/gbp")
    async def gbp_put(payload: dict, _: dict = Depends(require_admin)):
        per = str(payload.get("period") or "").strip()[:10]
        if not re.fullmatch(r"\d{4}-\d{2}(-\d{2})?", per):
            raise HTTPException(422, "Dönem YYYY-AA veya YYYY-AA-GG olmalı")
        doc = {"period": per, **{k: int(_f(payload.get(k))) for k in ("search_views", "maps_views", "calls", "directions", "website_clicks", "reviews_count")},
               "rating": round(_f(payload.get("rating")), 2), "updated_at": _now()}
        await db.gbp_stats.update_one({"period": per}, {"$set": doc}, upsert=True)
        return doc

    @api_router.delete("/mkt/gbp/{period}")
    async def gbp_del(period: str, _: dict = Depends(require_admin)):
        await db.gbp_stats.delete_one({"period": period})
        return {"ok": True}

    # ---------------------------------------------------------- yorumlar
    @api_router.get("/mkt/reviews")
    async def rev_list(_: dict = Depends(require_admin)):
        rows = await db.ext_reviews.find({}, {"_id": 0}).sort("date", -1).to_list(500)
        site = await db.reviews.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
        rt = [r["rating"] for r in rows if r.get("rating")]
        return {"reviews": rows, "unanswered": sum(1 for r in rows if not r.get("reply")), "avg": round(sum(rt) / len(rt), 2) if rt else 0, "count": len(rows),
                "site_reviews": site[:50], "site_avg": round(sum(r.get("rating", 0) for r in site) / len(site), 2) if site else 0}

    @api_router.post("/mkt/reviews")
    async def rev_add(payload: dict, _: dict = Depends(require_admin)):
        items = payload.get("items") if isinstance(payload.get("items"), list) else [payload]
        n = 0
        for it in items[:200]:
            rating = int(_f(it.get("rating")))
            if not 1 <= rating <= 5:
                continue
            doc = {"id": str(uuid.uuid4()), "platform": str(it.get("platform") or "google")[:20], "author": str(it.get("author") or "")[:80],
                   "rating": rating, "text": str(it.get("text") or "")[:1500], "date": str(it.get("date") or _today().isoformat())[:10], "reply": "",
                   "created_at": _now()}
            await db.ext_reviews.insert_one(doc)
            n += 1
        return {"ok": True, "added": n}

    @api_router.put("/mkt/reviews/{rid}")
    async def rev_reply(rid: str, payload: dict, _: dict = Depends(require_admin)):
        await db.ext_reviews.update_one({"id": rid}, {"$set": {"reply": str(payload.get("reply") or "")[:1500]}})
        return await db.ext_reviews.find_one({"id": rid}, {"_id": 0})

    @api_router.delete("/mkt/reviews/{rid}")
    async def rev_del(rid: str, _: dict = Depends(require_admin)):
        await db.ext_reviews.delete_one({"id": rid})
        return {"ok": True}

    @api_router.post("/mkt/reviews/{rid}/draft")
    async def rev_draft(rid: str, user: dict = Depends(require_admin)):
        r = await db.ext_reviews.find_one({"id": rid}, {"_id": 0})
        if not r:
            raise HTTPException(404, "Yorum bulunamadı")
        cfg = await get_cfg(db)
        brand = cfg["business"].get("name") or "ServisPlus"
        name = (r.get("author") or "").split(" ")[0]
        ai = None
        try:
            import ai as aimod
            c = {**aimod.DEFAULTS, **(await db.app_settings.find_one({"_id": "ai"}, {"_id": 0}) or {})}
            day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if c["enabled"] and c["api_key"] and await db.ai_usage.count_documents({"day": day}) < int(c["daily_limit"]):
                await db.ai_usage.insert_one({"day": day, "user_id": user["id"], "at": _now()})
                prompt = (f"Müşterinin Google yorumuna işletme adına kısa (en fazla 60 kelime), nazik ve samimi bir yanıt yaz. Puan: {r['rating']}/5. "
                          f"Yorum: {aimod.redact(r.get('text', ''))}\nFiyat/garanti sözü verme; olumsuzsa özür dileyip iletişime davet et. İmza: {brand}.")
                body = {"model": c["chat_model"], "messages": [{"role": "system", "content": c["system_prompt"]}, {"role": "user", "content": prompt}],
                        "max_tokens": 250, "temperature": 0.5}
                res = await asyncio.to_thread(aimod._post, c["base_url"].rstrip("/") + "/chat/completions", {"Authorization": "Bearer " + c["api_key"]}, body)
                ai = res["choices"][0]["message"]["content"].strip()
        except Exception:                              # noqa: BLE001
            ai = None
        if ai:
            return {"draft": ai, "ai": True}
        hi = f"Merhaba {name}," if name else "Merhaba,"
        if r["rating"] >= 4:
            t = f"{hi} güzel yorumunuz ve güveniniz için teşekkür ederiz. Memnun kalmanıza sevindik; ihtiyaç duyduğunuzda yanınızdayız. — {brand}"
        elif r["rating"] == 3:
            t = f"{hi} geri bildiriminiz için teşekkür ederiz. Deneyiminizi daha iyi hale getirmek istiyoruz; eksik kalan noktaları bizimle paylaşırsanız hemen ilgilenelim. — {brand}"
        else:
            t = f"{hi} yaşadığınız olumsuz deneyim için üzgünüz. Konuyu inceleyip çözmek istiyoruz; işletme profilindeki numaradan bize ulaşırsanız en kısa sürede dönüş yapalım. — {brand}"
        return {"draft": t, "ai": False}


async def ensure_indexes(db):
    await db.gsc_rows.create_index("day")
    await db.mkt_audits.create_index("at")
    await db.page_index.create_index("path")
    await db.gbp_stats.create_index("period", unique=True)
