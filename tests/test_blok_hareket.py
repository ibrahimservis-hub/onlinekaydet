"""Hareketli, güven ve görsel bölümleri: her biri kendi davranışını gösterir, hareket azaltmaya uyar."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import blokgen, blok_hareket
blokgen.kayit_al(blok_hareket.KAYIT, blok_hareket.CSS)
ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-600:]))

YO = [{"yazi": "Çok memnun kaldım", "ad": "Ayşe K.", "puan": 5},
      {"yazi": "Fena değil", "ad": "Mert", "puan": 3},
      {"yazi": "Harika ekip", "ad": "Zeynep", "puan": 5},
      {"yazi": "İyiydi", "ad": "Can", "puan": 4}]
D = {"yorumlar": YO, "fotograflar": ["f1", "f2", "f3", "f4", "f5"], "belgeler": ["b1", "b2"],
     "google": {"puan": 4.8, "adet": 240, "yorumlar": [{"yazi": "Süper", "ad": "G", "puan": 5}]},
     "video_yorum": [{"url": "https://youtu.be/abc12345", "ad": "Ayşe"}],
     "instagram": [], "baglantilar": {"instagram": "https://instagram.com/x"}}

def B(bid, **st):
    return {"iid": "i_" + bid, "bid": bid, "wire": "band", "on": True, "set": st}

def a():
    h = blokgen.block_html(B("kayan_yazi", title="Kampanya", sub="Kargo bedava\nİade kolay", speed=8), "", D)
    assert "bkh-kayan" in h and h.count("Kargo bedava") == 2, "sonsuz akış için içerik iki kez yazılmalı"
    assert 'aria-hidden="true"' in h, "kopya ekran okuyucuya okunmamalı"
    assert "--sure:" in h
t("kayan yazı: içerik iki kez, kopyası ekran okuyucudan gizli", a)

def b():
    h = blokgen.block_html(B("daktilo", title="Merhaba", sub="Kuaför\nBerber"), "", D)
    assert "<h2>" in h and "Merhaba" in h, "animasyon olmasa da başlık görünmeli"
    assert "prefers-reduced-motion" in h, "hareket azaltmaya uymalı"
    assert "data-yaz" in h
t("daktilo: hareket kapalıyken bile başlık okunur", b)

def c_():
    h = blokgen.block_html(B("sayac_anim", title="Rakamlar", sub="12 | yıl\n9.400 | müşteri"), "", D)
    assert 'data-hedef="12"' in h and 'data-hedef="9400"' in h
    assert "IntersectionObserver" in h and "prefers-reduced-motion" in h
t("sayaç: rakam ayrıştırılır, görününce sayar", c_)

def d_():
    h = blokgen.block_html(B("scroll_in", title="Adımlar", sub="Bir | ilk\nİki | sonra"), "", D)
    assert h.count("bkh-gir") >= 2 and "--g:90ms" in h, "sırayla girmeli"
    assert "classList.add('ac')" in h
t("kaydırınca beliren: maddeler sırayla girer, azaltmada hepsi görünür", d_)

def e():
    h = blokgen.block_html(B("sticky", title="Başlık", sub="A | 1\nB | 2"), "", D)
    assert "bkh-yp-s" in h and "position:sticky" in blok_hareket.CSS
    assert "@media(max-width:820px)" in blok_hareket.CSS, "telefonda yapışkanlık kapanmalı"
t("yapışkan bölüm telefonda sabitlikten çıkar", e)

def f():
    h = blokgen.block_html(B("parallax", title="T", img="k1"), "", D)
    assert "bkh-par" in h and "linear-gradient" in h
    tel = blokgen.block_html(B("parallax", title="T", img="k1"), "phone", D)
    assert "bkh-sbt" in tel, "telefonda sabit arka plana düşmeli"
    assert "background-attachment:scroll" in blok_hareket.CSS
t("parallax telefonda sabit arka plana düşer", f)

def g():
    h = blokgen.block_html(B("once_sonra", title="Önce sonra"), "", D)
    assert 'type="range"' in h and "aria-label" in h, "sürgü klavyeyle de çalışmalı"
    assert h.count("<img") == 2
    az = blokgen.block_html(B("once_sonra", title="T"), "", {"fotograflar": ["tek"]})
    assert "bkh-os" not in az, "iki fotoğraf yoksa çıkmamalı"
t("önce-sonra: sürgü klavyeyle çalışır, tek fotoğrafla çıkmaz", g)

def h_():
    h = blokgen.block_html(B("ilerleme"), "", D)
    assert 'role="progressbar"' in h and 'aria-valuenow="0"' in h and "passive" in h
t("ilerleme çubuğu erişilebilir ve kaydırmayı yavaşlatmaz", h_)

def i():
    h = blokgen.block_html(B("yorumlar", title="Yorumlar", min_star=4, style="kart", cols=3), "", D)
    assert "Çok memnun" in h and "Fena değil" not in h, "3 yıldızlı eşiğin altında kalmalı"
    assert "bk-sr" in h, "yıldız sayısı yazıyla da olmalı"
    hk = blokgen.block_html(B("yorumlar", title="Y", min_star=3, style="kayan şerit"), "", D)
    assert "bkh-yrs" in hk and 'tabindex="0"' in hk
    ht = blokgen.block_html(B("yorumlar", title="Y", min_star=3, style="tek büyük"), "", D)
    assert "bkh-tek" in ht and ht.count("<blockquote") == 1
t("yorumlar: puan eşiği uygulanır, üç düzen farklı çıkar", i)

def j():
    h = blokgen.block_html(B("google_yorum", title="Google", show_score=True), "", D)
    assert "4.8" in h and "240 değerlendirme" in h
    h2 = blokgen.block_html(B("google_yorum", title="G", show_score=False), "", D)
    assert "240 değerlendirme" not in h2, "puan kapatılabilmeli"
t("Google yorumları: puan ve adet gösterilir, kapatılabilir", j)

def k():
    h = blokgen.block_html(B("yildiz_ozet", title="Özet"), "", D)
    assert "4,3" in h or "4,2" in h, "ortalama Türkçe virgülle yazılmalı"
    assert h.count("bkh-dg") >= 5, "beş yıldız dağılımı olmalı"
t("yıldız özeti: ortalama ve dağılım çubukları", k)

def l():
    h = blokgen.block_html(B("galeri", title="Galeri", light=True, count=4), "", D)
    assert h.count('data-buyut="') == 4, "dört fotoğrafın dördü de büyütülebilmeli"
    assert "Escape" in h, "büyütme klavyeyle kapanmalı"
    h2 = blokgen.block_html(B("galeri", title="G", light=False), "", D)
    assert 'data-buyut="' not in h2, "büyütme kapalıyken düğme olmamalı"
t("galeri: büyütme açılıp kapanır, klavyeyle kapatılır", l)

def m():
    h = blokgen.block_html(B("masonry", title="M", cols=4), "", D)
    assert "bkh-ms" in h and "column-count" in blok_hareket.CSS
    hk = blokgen.block_html(B("galeri_kayan", title="K", anim_auto=True), "", D)
    assert "bkh-gks" in hk and 'data-oto="1"' in hk and "prefers-reduced-motion" in hk
t("masonry sütunlu, kayan galeri otomatik akar ama azaltmaya uyar", m)

def n():
    h = blokgen.block_html(B("gorsel_360", title="360"), "", D)
    assert "bkh-360" in h and 'role="img"' in h and "ArrowRight" in h
    az = blokgen.block_html(B("gorsel_360", title="T"), "", {"fotograflar": ["a", "b"]})
    assert "bkh-360" not in az, "4 kareden az ise çıkmamalı"
t("360° görsel: sürükle ve klavye, az kareyle çıkmaz", n)

def o():
    h = blokgen.block_html(B("instagram", title="Instagram"), "", D)
    assert "instagram.com/x" in h, "gönderi yoksa hesaba bağlantı verilmeli"
    assert blokgen.block_html(B("instagram", title="I"), "", {"instagram": [], "baglantilar": {}}) == ""
t("Instagram: gönderi yoksa hesaba bağlantı, hesap da yoksa çıkmaz", o)

def p_():
    h = blokgen.block_html(B("tam_gorsel", img="web1", img_m="tel1", title="T"), "", D)
    assert "web1" in h and "tel1" not in h
    tel = blokgen.block_html(B("tam_gorsel", img="web1", img_m="tel1", title="T"), "phone", D)
    assert "tel1" in tel, "telefon için ayrı görsel verilebilmeli"
t("tam genişlik görsel: telefon için ayrı görsel kullanılır", p_)

def q():
    h = blokgen.block_html(B("resim_yazi", title="T", sub="A", img="k1", side="sağ"), "", D)
    assert "bkh-rz-s" in h
    h2 = blokgen.block_html(B("resim_yazi", title="T", sub="A", img="k1", side="sol"), "", D)
    assert "bkh-rz-s" not in h2
t("resim + yazı: resmin yanı seçilebilir", q)

def r():
    h = blokgen.block_html(B("basinda", title="Basında", items="Röportaj | Hürriyet | https://x.com/a"), "", D)
    assert "Hürriyet" in h and 'rel="noopener"' in h
    hk = blokgen.block_html(B("basinda", title="B", items="Haber | Dergi | javascript:k()"), "", D)
    assert "javascript:" not in hk, "kötü bağlantı süzülmeli"
t("basında biz: dış bağlantı güvenli açılır, kötü bağlantı süzülür", r)

def s_():
    kotu = {"yorumlar": [{"yazi": "<script>x()</script>", "ad": "<b>K</b>", "puan": 5}],
            "fotograflar": [], "google": {}, "video_yorum": []}
    for bid in ("yorumlar", "yildiz_ozet"):
        h = blokgen.block_html(B(bid, title="T", min_star=3), "", kotu)
        assert "<script>" not in h and "<b>K" not in h, "%s kaçırmalı" % bid
t("yorum metni siteye betik olarak geçemez", s_)

def u():
    import blocks
    hedef = {b["id"] for b in blocks.BLOCKS if b["cat"] in ("hareketli", "guven", "gorsel")}
    yok = sorted(hedef - set(blok_hareket.KAYIT))
    assert not yok, "kendi kodu olmayan bölüm: %s" % yok
    assert len(hedef) == 27
t("hareketli, güven ve görsel bölümlerinin (27) hepsinin kendi kodu var", u)

print("\n".join("  ✓ " + n for n in ok))
for n, e in bad: print("  ✗ " + n + "\n" + e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA: %d/%d" % (len(bad), len(ok) + len(bad))))
sys.exit(1 if bad else 0)
