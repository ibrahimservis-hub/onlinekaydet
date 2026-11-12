"""Tanıtım, hizmet ve ekip bölümleri: her biri kendi davranışını gösterir."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import blokgen, blok_tanitim
blokgen.kayit_al(blok_tanitim.KAYIT, blok_tanitim.CSS)
ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-600:]))

HZ = [{"name": "Saç kesimi", "price": 450, "dur": 40, "cat": "Saç"},
      {"name": "Boya", "price": 1200, "dur": 90, "cat": "Saç"},
      {"name": "Manikür", "price": 350, "dur": 45, "cat": "El bakımı"}]
D = {"hizmetler": HZ, "ekip": [{"ad": "Ayşe Yıldız", "unvan": "Kurucu", "img": ""},
                               {"ad": "Mert Kaya", "unvan": "Stilist", "img": "k1"}],
     "paketler": [{"ad": "5 seans", "fiyat": 2000, "aciklama": "Tek ödeme", "kazanc": 250}],
     "cekler": [{"tutar": 500}, {"tutar": 1000}], "duyuru": "", "ilanlar": []}

def B(bid, **st):
    return {"iid": "i_" + bid, "bid": bid, "wire": "g3", "on": True, "set": st}

def a():
    h = blokgen.block_html(B("hero", title="Bakım", sub="Alt", cta="Al", cta_to="/r", align="orta"), "", D)
    assert "<h1>Bakım</h1>" in h and "bkt-a-c" in h
    hi = blokgen.block_html(B("hero", title="B", img="k9"), "", D)
    assert "bkt-ov" in hi and "linear-gradient" in hi, "görselli kapak karartılmalı"
    assert blokgen.block_html(B("hero"), "", D) == "", "yazısı yoksa çıkmamalı"
t("ana görsel: hizalama, görsel karartma, boşsa çıkmama", a)

def b():
    h = blokgen.block_html(B("hero_video", title="T", video="https://youtu.be/abc12345", poster="p1"), "", D)
    assert "youtube-nocookie" in h and "bkt-vhero" in h
    tel = blokgen.block_html(B("hero_video", title="T", video="https://youtu.be/abc12345", poster="p1"), "phone", D)
    assert "iframe" not in tel and "p1" in tel, "telefonda video yerine kapak görseli olmalı"
t("video kapak: telefonda video yerine kapak görseli kullanılır", b)

def c_():
    h = blokgen.block_html(B("hero_slider", slides=["a", "b", "c"], dots=True, arrows=True, speed=4), "", D)
    assert h.count("<li") == 3 and 'data-hiz="4"' in h
    assert "bkt-ok" in h and "bkt-nk" in h and "ArrowRight" in h, "ok, nokta ve klavye olmalı"
    assert "prefers-reduced-motion" in h
    assert blokgen.block_html(B("hero_slider", slides=[]), "", D) == ""
t("slider: ok, nokta, klavye ve hareket azaltma", c_)

def d_():
    h = blokgen.block_html(B("hero_search", title="Ne arıyorsunuz?", scope="hizmet"), "", D)
    assert 'action="/hizmetler"' in h and 'role="search"' in h and "bk-sr" in h
    h2 = blokgen.block_html(B("hero_search", title="X", scope="ürün"), "", D)
    assert 'action="/magaza"' in h2, "kapsam aramanın yerini değiştirmeli"
t("arama kutulu kapak: kapsam aramanın hedefini belirler", d_)

def e():
    h = blokgen.block_html(B("sayilarla", items="12 | yıllık deneyim\n9.400 | müşteri", count_anim=True), "", D)
    assert 'data-hedef="12"' in h and 'data-hedef="9400"' in h, "sayı ayrıştırılmalı"
    assert "IntersectionObserver" in h
    h2 = blokgen.block_html(B("sayilarla", items="12 | yıl", count_anim=False), "", D)
    assert "data-hedef" not in h2, "animasyon kapalıyken sayaç olmamalı"
t("sayılarla: rakam ayrıştırılır, animasyon kapatılabilir", e)

def f():
    h = blokgen.block_html(B("duyuru_bar", text="Kargo bedava", end="2027-01-01", closable=True), "", D)
    assert "Kargo bedava" in h and "bkt-dsy" in h and 'class="bkt-dx"' in h
    assert "localStorage" in h, "kapatınca hatırlanmalı"
    h2 = blokgen.block_html(B("duyuru_bar", text="X", closable=False), "", D)
    assert 'class="bkt-dx"' not in h2, "kapatma kapalıyken düğme çıkmamalı"
    assert blokgen.block_html(B("duyuru_bar"), "", D) == "", "yazısı yoksa çıkmamalı"
t("duyuru çubuğu: geri sayım, kapatma ve hatırlama", f)

def g():
    h = blokgen.block_html(B("hizmet_liste", title="Hizmetler", show_price=True, show_dur=True), "", D)
    assert "Saç kesimi" in h and "450 ₺" in h and "40 dk" in h
    h2 = blokgen.block_html(B("hizmet_liste", title="H", show_price=False, show_dur=False), "", D)
    assert "450" not in h2 and "40 dk" not in h2, "kapatılan sütun gösterilmemeli"
    h3 = blokgen.block_html(B("hizmet_liste", title="H", group=True), "", D)
    assert "El bakımı" in h3 and "bkt-gb" in h3, "gruplama kategoriye göre olmalı"
t("hizmet listesi: fiyat/süre açılıp kapanır, kategoriye göre gruplanır", g)

def h_():
    h = blokgen.block_html(B("fiyat_tablo", title="Fiyatlar"), "", D)
    assert "<table" in h and 'scope="col"' in h and "<caption" in h and "1.200 ₺" in h
    h2 = blokgen.block_html(B("hizmet_sekme", title="H"), "", D)
    assert "<details" in h2 and "Saç" in h2 and "El bakımı" in h2
t("fiyat tablosu ve sekmeli hizmetler erişilebilir kurulur", h_)

def i():
    h = blokgen.block_html(B("surec", title="Nasıl çalışır", items="Arayın | Randevu alın\nGelin | İşlem yapılır"), "", D)
    assert "<ol" in h and "bkt-no" in h and h.count("<li") == 2
t("süreç adımları numaralı sırada liste olur", i)

def j():
    h = blokgen.block_html(B("hesaplayici", title="Hesapla", items="Kesim | 450\nBoya | 1200"), "", D)
    assert 'data-tutar="450"' in h and 'data-tutar="1200"' in h
    assert "aria-live" in h, "toplam ekran okuyucuya bildirilmeli"
t("fiyat hesaplayıcı: tutarlar okunur, toplam sesli bildirilir", j)

def k():
    h = blokgen.block_html(B("karsilastirma", title="K", items="Randevu | var | yok\nOtopark | yok | var"), "", D)
    assert "bkt-var" in h and "bkt-yok" in h
    assert h.count("bk-sr") >= 2, "işaretin yanında yazısı da olmalı (renk körü)"
t("karşılaştırma: işaretlerin yanında yazılı karşılığı var", k)

def l():
    h = blokgen.block_html(B("ekip", title="Ekibimiz", cols=4), "", D)
    assert "Ayşe Yıldız" in h and "Kurucu" in h
    assert "AY" in h, "fotoğrafı olmayanda baş harf olmalı"
    assert "k1" in h, "fotoğrafı olan görseli göstermeli"
t("ekip kartları: fotoğrafı olmayanda baş harf gösterilir", l)

def m():
    h = blokgen.block_html(B("paketler", title="Paketler"), "", D)
    assert "5 seans" in h and "2.000" in h and "250 ₺ kazanç" in h
    assert blokgen.block_html(B("paketler", title="P"), "", {"paketler": []}) != ""
    assert blokgen.block_html(B("paketler"), "", {"paketler": []}) == "", "paket ve başlık yoksa çıkmamalı"
t("paketler: fiyat ve kazanç yazar, paket yoksa uydurmaz", m)

def n():
    h = blokgen.block_html(B("hediye_ceki", title="Hediye"), "", D)
    assert "500 ₺" in h and "1.000 ₺" in h and "/hediye-ceki?t=500" in h
t("hediye çeki: tutarlar işletmenin tanımladıklarından gelir", n)

def o():
    h = blokgen.block_html(B("teklif", title="Teklif"), "", D)
    assert 'name="ad"' in h and 'name="tel"' in h and "required" in h and "<label" in h
t("teklif formu etiketli ve zorunlu alanlı", o)

def p_():
    kotu = {"hizmetler": [{"name": "<script>x()</script>", "price": 10, "dur": 5, "cat": "<b>K</b>"}],
            "ekip": [{"ad": "<i>E</i>", "unvan": "<u>U</u>", "img": ""}], "paketler": [], "cekler": []}
    for bid in ("hizmet_liste", "hizmet_sekme", "fiyat_tablo", "ekip"):
        h = blokgen.block_html(B(bid, title="T", group=True), "", kotu)
        assert "<script>" not in h and "<b>K" not in h and "<i>E" not in h, "%s kaçırmalı" % bid
t("hizmet ve ekip adları siteye betik olarak geçemez", p_)

def q():
    import blocks
    hedef = {b["id"] for b in blocks.BLOCKS if b["cat"] in ("tanitim", "hizmet", "ekip")}
    yok = sorted(hedef - set(blok_tanitim.KAYIT))
    assert not yok, "kendi kodu olmayan bölüm: %s" % yok
    assert len(hedef) == 23
t("tanıtım, hizmet ve ekip bölümlerinin (23) hepsinin kendi kodu var", q)

print("\n".join("  ✓ " + n for n in ok))
for n, e in bad: print("  ✗ " + n + "\n" + e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA: %d/%d" % (len(bad), len(ok) + len(bad))))
sys.exit(1 if bad else 0)
