"""E-ticaret bölümleri: her biri kendi kuralıyla seçer ve kendi davranışını gösterir."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import blokgen, blok_eticaret
blokgen.kayit_al(blok_eticaret.KAYIT, blok_eticaret.CSS)
ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-600:]))

def U(i, ad, fiyat, ind=0, stok=10, cat="Bakım", marka="Nisan", yeni=None):
    yeni = yeni or "2026-01-%02d" % (i + 1)
    return {"id": "p%d" % i, "slug": "u%d" % i, "name": ad, "price": fiyat,
            "sale_price": round(fiyat * (100 - ind) / 100, 2) if ind else 0,
            "stock": stok, "low_at": 5, "track_stock": True, "cat": cat, "brand": marka,
            "images": ["k%d" % i], "status": "live", "channels": {"site": True}, "created_at": yeni}

URUN = [U(1, "Şampuan", 200, ind=50), U(2, "Krem", 400, ind=10), U(3, "Serum", 900, stok=2),
        U(4, "Maske", 150, cat="Saç", marka="Vega"), U(5, "Fırça", 300, stok=0)]
SATIS = {"p4": 90, "p2": 40, "p1": 5}
D = {"urunler": URUN, "satis": SATIS, "rozetler": [{"id": "indirim", "name": "İndirim", "color": "#c0392b"}],
     "kategoriler": [{"ad": "Bakım", "n": 3, "img": "k1"}, {"ad": "Saç", "n": 1, "img": "k4"}],
     "markalar": [{"ad": "Nisan", "n": 4}, {"ad": "Vega", "n": 1}]}

def B(bid, **st):
    s = {"title": "Başlık", "count": 8, "cols": 4, "cols_m": "2"}
    s.update(st)
    return {"iid": "i_" + bid, "bid": bid, "wire": "g3", "on": True, "set": s}

def ad_sirasi(h):
    return re.findall(r"<h3>([^<]+)</h3>", h)

def a():
    h = blokgen.block_html(B("v_indirim"), "", D)
    assert ad_sirasi(h)[0] == "Şampuan", "en yüksek indirimli önce gelmeli: %s" % ad_sirasi(h)
    assert "Fırça" not in h, "indirimsiz ürün girmemeli"
    assert "%50" in h and "%10" in h, "indirim yüzdesi rozet olmalı"
t("indirimli ürünler: orana göre sıralı, yüzde rozetli, indirimsizi almaz", a)

def b():
    h = blokgen.block_html(B("v_coksatan"), "", D)
    assert ad_sirasi(h)[0] == "Maske", "en çok satan önce: %s" % ad_sirasi(h)
    assert "1." in h and "2." in h, "sıra numarası olmalı"
t("çok satanlar: satış adedine göre sıralı, sıra numaralı", b)

def b2():
    d2 = dict(D, satis={})
    h = blokgen.block_html(B("v_coksatan"), "", d2)
    assert "1." not in h, "satış kaydı yokken uydurma sıra numarası basılmamalı"
    assert "<h3>" in h, "ürünler yine de listelenmeli"
t("satış kaydı yokken sıra numarası uydurulmaz", b2)

def c_():
    hi = blokgen.block_html(B("v_indirim"), "", D)
    hc = blokgen.block_html(B("v_coksatan"), "", D)
    assert ad_sirasi(hi) != ad_sirasi(hc), "iki bölüm aynı çıktıyı vermemeli"
    hy = blokgen.block_html(B("v_yeni"), "", D)
    assert ad_sirasi(hy)[0] == "Fırça", "en yeni önce: %s" % ad_sirasi(hy)
    assert "YENİ" in hy
t("indirimli, çok satan ve yeni gelenler birbirinden farklı çıkar", c_)

def d_():
    h = blokgen.block_html(B("v_tukeniyor"), "", D)
    adlar = ad_sirasi(h)
    assert adlar == ["Serum"], "yalnız az stoklu: %s" % adlar
    assert "Son 2 adet" in h and "SON 2" in h
    assert "Fırça" not in h, "stoğu biten girmemeli"
t("tükenmek üzere: yalnız az stoklu, kalan adet yazılı", d_)

def e():
    h = blokgen.block_html(B("v_firsat", end="2027-01-01T00:00:00Z"), "", D)
    assert 'class="bke-sayac"' in h and 'data-bit="2027-01-01T00:00:00Z"' in h, "sayaç olmalı"
    assert "FIRSAT" in h
    h2 = blokgen.block_html(B("v_firsat"), "", D)
    assert "bke-sayac" not in h2, "bitiş saati yoksa sayaç çıkmamalı"
t("fırsat ürünleri: bitiş saati verilince geri sayar", e)

def f():
    h = blokgen.block_html(B("v_secili", rule="manuel", items=["p3", "p1"]), "", D)
    assert ad_sirasi(h) == ["Serum", "Şampuan"], "elle seçilen sırayla: %s" % ad_sirasi(h)
t("öne çıkanlar: elle seçilen ürünler, seçilen sırayla", f)

def g():
    h = blokgen.block_html(B("v_serit", anim_auto=True), "", D)
    assert 'class="bke-serit"' in h and 'data-oto="1"' in h and "prefers-reduced-motion" in h
    assert 'tabindex="0"' in h and 'role="region"' in h, "klavyeyle gezilebilmeli"
t("ürün şeridi: otomatik kayar ama hareket azaltma ayarına uyar", g)

def h_():
    h = blokgen.block_html(B("v_buyuk_kart"), "", D)
    assert "bke-buyuk-d" in h and h.count("bke-k ") >= 2
    assert "bke-buyuk" in h, "bir kart büyük olmalı"
t("büyük kart: bir büyük, yanında küçükler", h_)

def i():
    # satışı olan ama stoğu biten ürün: düğme kapalı olmalı
    d2 = dict(D, satis={"p5": 120, "p4": 90, "p2": 40})
    h = blokgen.block_html(B("v_hizli_sepet"), "", d2)
    assert ad_sirasi(h)[0] == "Fırça", "en çok satan önce: %s" % ad_sirasi(h)
    assert h.count('class="bke-sep"') == len(ad_sirasi(h)), "her kartta bir düğme olmalı"
    assert "disabled" in h and ">Tükendi<" in h, "stoğu biten üründe düğme kapalı olmalı"
    assert ">Sepete ekle<" in h, "stoğu olanda açık olmalı"
t("hızlı sepet: her kartta düğme, stoğu bitende kapalı", i)

def j():
    h = blokgen.block_html(B("v_birlikte", rule="manuel", items=["p1", "p2"]), "", D)
    assert "bke-arti" in h and "Birlikte:" in h
    assert "460" in h, "toplam fiyat 100 + 360 = 460 olmalı"
t("birlikte alınanlar: ürünler artı ile birleşir, toplam yazar", j)

def k():
    h = blokgen.block_html(B("v_kategori"), "", D)
    assert "Bakım" in h and "3 ürün" in h and "/magaza?kat=Bakım" in h
    hm = blokgen.block_html(B("v_marka"), "", D)
    assert "Nisan" in hm and "/magaza?marka=Nisan" in hm
t("kategori ve marka vitrinleri kendi listelerinden gelir", k)

def l():
    h = blokgen.block_html(B("v_izgara", cat="Saç"), "", D)
    assert ad_sirasi(h) == ["Maske"], "kategori süzgeci çalışmalı: %s" % ad_sirasi(h)
t("kategori seçilince yalnız o kategori gösterilir", l)

def m():
    bos = {"urunler": [], "satis": {}, "rozetler": [], "kategoriler": [], "markalar": []}
    for bid in ("v_indirim", "v_coksatan", "v_yeni", "v_tukeniyor", "v_izgara"):
        h = blokgen.block_html(B(bid), "", bos)
        assert "<h3>" not in h and "bke-k" not in h, "%s: ürün yokken kart basmamalı" % bid
        h2 = blokgen.block_html(B(bid, title=""), "", bos)
        assert h2 == "", "%s: başlık da yoksa bölüm hiç çıkmamalı" % bid
t("ürün yokken uydurma kart basılmaz", m)

def n():
    kotu = dict(U(9, '<script>zarar()</script>', 100), cat='"><b>KOTU</b>', brand="<i>KOTU</i>")
    d2 = dict(D, urunler=[kotu], kategoriler=[{"ad": '"><b>KOTU</b>', "n": 1, "img": ""}],
              markalar=[{"ad": "<i>KOTU</i>", "n": 1}])
    for bid in ("v_izgara", "v_kategori", "v_marka"):
        h = blokgen.block_html(B(bid), "", d2)
        assert "<script>" not in h, "%s: betik kaçırmalı" % bid
        assert "<b>KOTU" not in h and "<i>KOTU" not in h, "%s: etiket ham geçmemeli" % bid
        if "KOTU" in h:
            assert "&lt;" in h, "%s: kaçırılmış olmalı" % bid
t("ürün adı, kategori ve marka siteye betik olarak geçemez", n)

def o():
    h = blokgen.block_html(B("v_indirim", count=2), "", D)
    assert len(ad_sirasi(h)) == 2, "kaç tane gösterilsin ayarı uygulanmalı"
t("kaç ürün gösterileceği ayarı uygulanır", o)

def p_():
    web = blokgen.block_html(B("v_izgara", cols=4, cols_m="1"), "", D)
    tel = blokgen.block_html({"iid": "i", "bid": "v_izgara", "wire": "g3", "on": True,
                              "set": {"title": "B", "cols": 4, "cols_m": "1", "count": 8},
                              "set_m": {"cols_m": "kaydırmalı"}}, "phone", D)
    assert "--cm:1" in web and "--cm:auto" in tel, "telefon sütun ayarı ayrı uygulanmalı"
t("telefon sütun ayarı yalnız telefonda geçerli", p_)

def q():
    h = blokgen.block_html(B("uyelik", fav=True, wallet=True), "", D)
    assert "Favori listesi" in h and "Cüzdan" in h and "/uye-girisi" in h
    assert "Google ile giriş" not in h, "kapalı özellik yazılmamalı"
t("üyelik bölümü yalnız açık özellikleri sayar", q)

def r():
    h = blokgen.block_html(B("siparis_takip"), "", D)
    assert 'action="/siparis-takip"' in h and 'name="kod"' in h and 'class="bk-sr"' in h
    hs = blokgen.block_html(B("v_stok_haber"), "", D)
    assert 'type="email"' in hs and "required" in hs
t("sipariş takip ve stok haber formları etiketli ve doğrulamalı", r)

def s_():
    h = blokgen.block_html(B("guvence", items="Ücretsiz kargo | 500 ₺ üzeri\n14 gün iade | Koşulsuz"), "", D)
    assert "Ücretsiz kargo" in h and "14 gün iade" in h
    assert blokgen.block_html(B("guvence", items=""), "", D) == "", "madde yoksa çıkmamalı"
t("güvence şeridi maddelerden kurulur, boşsa çıkmaz", s_)

def u():
    h = blokgen.block_html(B("taksit"), "", dict(D, taksit=[{"banka": "X Bank", "ay": [3, 6], "tutar": [100, 50]}]))
    assert "<table" in h and "X Bank" in h and 'scope="row"' in h and "<caption" in h
    assert blokgen.block_html(B("taksit"), "", D) == "", "veri yoksa tablo çıkmamalı"
t("taksit tablosu erişilebilir kurulur, veri yoksa çıkmaz", u)

def w():
    eksik = [bid for bid in blok_eticaret.KAYIT if bid not in blokgen.OZEL]
    assert not eksik, eksik
    import blocks
    et = {b["id"] for b in blocks.BLOCKS if b["cat"] == "eticaret"}
    yok = sorted(et - set(blok_eticaret.KAYIT))
    assert not yok, "kendi kodu olmayan e-ticaret bölümü: %s" % yok
t("22 e-ticaret bölümünün hepsinin kendi kodu var", w)

print("\n".join("  ✓ " + n for n in ok))
for n, e in bad: print("  ✗ " + n + "\n" + e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA: %d/%d" % (len(bad), len(ok) + len(bad))))
sys.exit(1 if bad else 0)
