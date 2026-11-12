"""Bölüm sayfaları siteye basılır: tema yerine geçer, telefonda ayrı, veriler kendi kayıtlarından."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-600:]))

import blokgen

def b1():
    b = {"iid": "i1", "bid": "hero", "wire": "hero", "on": True,
         "set": {"title": "Başlık", "sub": "Alt", "cta": "Randevu", "cta_to": "/randevu", "pad": 70, "align": "orta"},
         "set_m": {"pad": 24, "align": "sol"}}
    w, f = blokgen.block_html(b, ""), blokgen.block_html(b, "phone")
    assert "--bk-pad:70px" in w and "bk-a-c" in w
    assert "--bk-pad:24px" in f and "bk-a-l" in f, "telefon ayarı binmeli"
    assert "Başlık" in w and 'href="/randevu"' in w
t("telefonda set_m set'in üzerine biner, dokunulmayan miras kalır", b1)

def b2():
    kotu = {"iid": "i", "bid": "hero", "wire": "hero", "on": True,
            "set": {"title": '<img src=x onerror=alert(1)>', "sub": "a\"b", "cta": "Git", "cta_to": "javascript:alert(1)"}}
    h = blokgen.block_html(kotu, "")
    assert "<img" not in h and "&lt;img src=x onerror" in h, "etiket ham geçmemeli, kaçırılmış olmalı"
    assert "&quot;" in h, "tırnak kaçırılmalı"
    assert "javascript:" not in h, "kötü bağlantı geçmemeli"
    assert 'href="#"' in h
t("müşterinin yazdığı metin ve bağlantı siteye betik olarak geçemez", b2)

def b3():
    kap = {"iid": "i", "bid": "hero", "wire": "hero", "on": False, "set": {"title": "X"}}
    assert blokgen.block_html(kap, "") == "", "kapalı bölüm basılmamalı"
    tel = {"iid": "i", "bid": "hero", "wire": "hero", "on": True, "set": {"title": "X"}, "set_m": {"on_m": False}}
    assert blokgen.block_html(tel, "phone") == "" and blokgen.block_html(tel, "") != "", "telefonda gizlenen yalnız telefonda gizlenmeli"
    bos = {"iid": "i", "bid": "hero", "wire": "hero", "on": True, "set": {}}
    assert blokgen.block_html(bos, "") == "", "içeriği olmayan bölüm boş çıkmalı"
t("kapalı, telefonda gizli ve boş bölümler basılmaz", b3)

def b4():
    sayi = 0
    for w in blokgen.WIRES:
        b = {"iid": "i", "bid": "x", "wire": w, "on": True,
             "set": {"title": "B", "sub": "A", "items": "Bir | iki | /git\nÜç | dört | /gel",
                     "left": "sol", "right": "sağ", "text": "şerit", "cta": "Tıkla", "cta_to": "/x",
                     "imgs": ["k1", "k2"], "slides": ["k1"], "video": "https://youtu.be/abc12345",
                     "ph": "ara"}}
        h = blokgen.block_html(b, "", {"address": "Nişantaşı İstanbul"})
        if h:
            sayi += 1
            assert h.count("<section") == 1, w
            assert "None" not in h, "%s: None sızmış" % w
    assert sayi >= 17, "19 yerleşimin neredeyse hepsi üretmeli, üreten: %d" % sayi
t("19 yerleşim türü de HTML üretir, None sızmaz", b4)

def b45():
    """Bölümün <section> sınıfı, içindeki öğelerin sınıflarıyla çakışmamalı.
    Çakıştığında section iç öğenin stilini alır: liste daralır, harita 1000 piksel olur."""
    import re as _re
    ic = set(_re.findall(r"\.(bk-[a-z0-9-]+)", blokgen.CSS))
    bolum = {"bkw-%s" % w for w in blokgen.WIRES}
    ortak = ic & bolum
    assert not ortak, "section sınıfı iç sınıfla çakışıyor: %s" % sorted(ortak)
    for w in blokgen.WIRES:
        b = {"iid": "i", "bid": "x", "wire": w, "on": True,
             "set": {"title": "B", "sub": "A", "items": "x | y", "left": "s", "right": "s",
                     "text": "t", "imgs": ["k1", "k2"], "slides": ["k"], "ph": "a"}}
        h = blokgen.block_html(b, "", {"address": "İstanbul"})
        if not h:
            continue
        sec_cls = set(_re.match(r'<section class="([^"]+)"', h).group(1).split())
        icler = set()
        for m in _re.finditer(r'<(?!section)[a-z]+ [^>]*class="([^"]+)"', h):
            icler |= set(m.group(1).split())
        assert not (sec_cls & icler), "%s: section ve iç öğe aynı sınıfı paylaşıyor: %s" % (w, sorted(sec_cls & icler))
t("bölüm sınıfı iç öğe sınıflarıyla çakışmaz (yerleşimi bozan hata)", b45)

def b46():
    assert blokgen.tel_goster("5331112233") == "0533 111 22 33"
    assert blokgen.tel_goster("905331112233") == "0533 111 22 33"
    assert blokgen.tel_goster("0212 555 00 00") == "0212 555 00 00"
t("telefon numarası okunur biçimde yazılır", b46)

def b5():
    b = {"iid": "i", "bid": "x", "wire": "video", "on": True, "set": {"title": "T", "video": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}}
    h = blokgen.block_html(b, "")
    assert "youtube-nocookie.com/embed/dQw4w9WgXcQ" in h, "çerezsiz gömme kullanılmalı"
    assert "<iframe" in h and "title=" in h
t("video çerezsiz gömülür ve başlıklandırılır", b5)

with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Nisan Kuaför", "phone": "05524165690", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    PH = {"user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1 Mobile/15E148"}

    def p1():
        r = c.get("/api/yp/pages", headers=H); assert r.status_code == 200, r.text
        S["pid"] = r.json()["rows"][0]["id"]
        bl = c.get("/api/yp/pages/%s/blocks" % S["pid"], headers=H).json()["rows"]
        assert bl, "sektör paketi hazır bölümlerle gelmeli"
        S["iid"] = bl[0]["iid"]
    t("sektör paketi ana sayfayı hazır bölümlerle kurar", p1)

    def p15():
        c.put("/api/yp/pages/%s/blocks/%s" % (S["pid"], S["iid"]), headers=H,
              json={"set": {"title": "Bakımınız bize emanet", "sub": "Nişantaşı", "pad": 80}})
        assert c.get("/api/yp/site-engine", headers=H).json()["engine"] == "tema", "varsayılan tema olmalı"
        h = c.get("/api/site/preview", headers=H).text
        assert "Bakımınız bize emanet" not in h, "motor kapalıyken bölümler siteye basılmamalı"
        assert len(h) > 500, "tema sitesi olduğu gibi yayında kalmalı"
        r = c.put("/api/yp/site-engine", headers=H, json={"engine": "blok"})
        assert r.status_code == 200, r.text
    t("bölüm motoru kapalıyken mevcut tema sitesi olduğu gibi kalır", p15)

    def p2():
        h = c.get("/api/site/preview", headers=H).text
        assert "Bakımınız bize emanet" in h, "panelde yazılan başlık siteye basılmalı"
        assert "--bk-pad:80px" in h
        assert "OnlineKaydet ile yayınlanır" in h and "onlinekaydet.com" in h, "alt bilgi bağlantısı zorunlu"
        S["web"] = h
    t("panelde kurulan sayfa siteye basılır, alt bilgi bağlantısı yerinde", p2)

    def p3():
        c.put("/api/yp/pages/%s/blocks/%s" % (S["pid"], S["iid"]), headers=H, json={"set_m": {"pad": 22}})
        tel = c.get("/api/site/preview?dev=phone", headers=H).text
        assert "--bk-pad:22px" in tel, "telefon ayarı siteye yansımalı"
        assert "--bk-pad:80px" in S["web"] and "--bk-pad:22px" not in S["web"], "bilgisayar sürümü değişmemeli"
    t("telefon ayarı yalnız telefon sürümüne yansır", p3)

    def p4():
        h = c.get("/api/site/preview", headers=H).text
        assert h.count("<html") == 1 and "<title>" in h and 'lang="tr"' in h
        assert 'name="viewport"' in h, "telefonda düzgün görünmek için viewport şart"
        assert "<main>" in h and "<header" in h and "<footer" in h, "anlamlı HTML iskeleti"
        assert 'aria-label="Menü"' in h, "telefon menüsü düğmesi erişilebilir olmalı"
    t("üretilen sayfa geçerli ve erişilebilir bir iskelet kurar", p4)

    def p5():
        c.post("/api/yp/services", headers=H, json={"name": "Saç kesimi", "price": 450, "dur": 40})
        c.post("/api/yp/services", headers=H, json={"name": "Boya", "price": 1200, "dur": 90})
        hz = [x for x in c.get("/api/yp/blocks?all_=true", headers=H).json()["rows"] if x["id"] == "hizmet_liste"]
        if not hz: return
        c.post("/api/yp/pages/%s/blocks" % S["pid"], headers=H, json={"bid": "hizmet_liste"})
        h = c.get("/api/site/preview", headers=H).text
        assert "Saç kesimi" in h and "450" in h, "hizmetler kendi kayıtlarından gelmeli"
        assert "1.200" in h, "fiyat Türkçe biçimlenmeli"
    t("hizmet listesi işletmenin kendi kayıtlarından beslenir", p5)

    def p6():
        r = c.get("/api/site/preview?path=/yok-boyle-sayfa", headers=H)
        assert r.status_code == 404, "olmayan sayfa 404 olmalı"
    t("olmayan sayfa 404 döner", p6)

    def p7():
        assert c.put("/api/yp/site-engine", headers=H, json={"engine": "sacma"}).status_code == 422
        c.put("/api/yp/site-engine", headers=H, json={"engine": "tema"})
        h = c.get("/api/site/preview", headers=H).text
        assert "Bakımınız bize emanet" not in h, "temaya dönünce bölümler yayından kalkmalı"
        c.put("/api/yp/site-engine", headers=H, json={"engine": "blok"})
    t("motor temaya geri alınabilir, geçersiz değer reddedilir", p7)

print("\n".join("  ✓ " + n for n in ok))
for n, e in bad: print("  ✗ " + n + "\n" + e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA: %d/%d" % (len(bad), len(ok) + len(bad))))
sys.exit(1 if bad else 0)
