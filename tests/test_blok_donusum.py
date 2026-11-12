"""Dönüşüm, içerik ve bilgi bölümleri: formlar etiketli, yasal metinler uydurulmuyor."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import blokgen, blok_donusum
blokgen.kayit_al(blok_donusum.KAYIT, blok_donusum.CSS)
ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-600:]))

D = {"hizmetler": [{"name": "Kesim", "price": 450}, {"name": "Boya", "price": 1200}],
     "ekip": [{"ad": "Ayşe", "unvan": "Kurucu"}],
     "yazilar": [{"baslik": "Saç bakımı", "ozet": "Kısa özet", "slug": "sac-bakimi", "tarih": "2026-03-01", "img": "k1"}],
     "sss": [{"soru": "Randevu şart mı?", "cevap": "Hayır"}],
     "dosyalar": [{"ad": "Fiyat listesi", "url": "https://x.com/f.pdf", "tur": "pdf", "boyut": "1,2 MB"}],
     "adres": "Nişantaşı, İstanbul",
     "saatler": [{"ac": "09:00", "kapa": "19:00"}, {"ac": "09:00", "kapa": "19:00"}, {"ac": "09:00", "kapa": "19:00"},
                 {"ac": "09:00", "kapa": "19:00"}, {"ac": "09:00", "kapa": "19:00"},
                 {"ac": "10:00", "kapa": "18:00"}, {"kapali": True}],
     "bugun": 2, "acik_mi": True,
     "subeler": [{"ad": "Merkez", "adres": "Nişantaşı", "tel": "0212 555 00 00"}],
     "bolgeler": ["Teşvikiye", "Maçka"],
     "iletisim": {"tel": "0533 111 22 33", "eposta": "a@b.com", "adres": "Nişantaşı", "whatsapp": "905331112233"},
     "baglantilar": {"instagram": "https://instagram.com/x"},
     "yasal": [("gizlilik-kvkk", "Gizlilik ve KVKK"), ("cerez-politikasi", "Çerez Politikası")]}

def B(bid, **st):
    return {"iid": "ii", "bid": bid, "wire": "form", "on": True, "set": st}

def a():
    h = blokgen.block_html(B("iletisim_form", title="Bize yazın", kvkk=True, fields="Konu"), "", D)
    assert h.count("<label") >= 4, "her alanın etiketi olmalı"
    assert 'name="ek_konu"' in h, "işletmenin eklediği alan çıkmalı"
    assert 'name="kvkk"' in h and "required" in h, "KVKK onayı zorunlu olmalı"
    assert "/gizlilik-kvkk" in h
    h2 = blokgen.block_html(B("iletisim_form", title="X", kvkk=False), "", D)
    assert 'name="kvkk"' not in h2, "KVKK kapatılabilmeli"
t("iletişim formu: etiketli alanlar, ek alanlar, KVKK onayı", a)

def b():
    h = blokgen.block_html(B("randevu_form", title="Randevu"), "", D)
    assert "Kesim" in h and "450" in h and "Boya" in h, "hizmetler panelden gelmeli"
    assert "Ayşe" in h and "Fark etmez" in h
    assert 'type="date"' in h and 'name="tel"' in h
    bos = blokgen.block_html(B("randevu_form", title="R"), "", {"hizmetler": [], "ekip": []})
    assert "<select" not in bos, "hizmet yoksa boş liste basılmamalı"
t("randevu formu hizmet ve ekip listesini panelden alır", b)

def c_():
    h = blokgen.block_html(B("geri_arama", title="Sizi arayalım"), "", D)
    assert h.count("<label") <= 3, "geri arama kısa olmalı"
    assert 'name="tel"' in h
t("geri arama formu kısa tutulur", c_)

def d_():
    h = blokgen.block_html(B("whatsapp", num="0533 111 22 33", msg="Merhaba", pos="sol alt"), "", D)
    assert "wa.me/905331112233" in h or "wa.me/05331112233" in h
    assert "bkd-wa-sol" in h and "aria-label" in h
    assert blokgen.block_html(B("whatsapp"), "", {"iletisim": {}}) == "", "numara yoksa çıkmamalı"
    oto = blokgen.block_html(B("whatsapp"), "", D)
    assert "wa.me/905331112233" in oto, "numara ayarlardan da gelebilmeli"
t("WhatsApp düğmesi: numara ayarlardan gelir, konumu seçilir", d_)

def e():
    h = blokgen.block_html(B("popup", title="Hoş geldiniz", when="çıkarken", once=True), "", D)
    assert 'data-ne="cikis"' in h and 'data-bir="1"' in h
    assert 'aria-modal="true"' in h and "Escape" in h, "pencere klavyeyle kapanmalı"
    h2 = blokgen.block_html(B("popup", title="X", when="5 sn sonra", once=False), "", D)
    assert 'data-ne="5000"' in h2 and 'data-bir=""' in h2
t("açılır pencere: ne zaman açılacağı ve bir kez gösterimi", e)

def f():
    h = blokgen.block_html(B("gerisayim", title="Son gün", end="2027-01-01T00:00:00Z"), "", D)
    assert "bkd-gsk" in h and 'data-bit="2027-01-01T00:00:00Z"' in h
    assert "hidden=true" in h or "s.hidden" in h, "süre dolunca gizlenmeli"
    assert blokgen.block_html(B("gerisayim", title="X"), "", D) == "", "bitiş saati yoksa çıkmamalı"
t("geri sayım: süre dolunca bölüm kendini gizler", f)

def g():
    h = blokgen.block_html(B("blog", title="Yazılar", count=4, cols=3), "", D)
    assert "Saç bakımı" in h and "/blog/sac-bakimi" in h and "<time" in h
    assert blokgen.block_html(B("blog", title="Y"), "", {"yazilar": []}) != ""
    assert blokgen.block_html(B("blog"), "", {"yazilar": []}) == ""
t("blog: yazılar panelden, tarih makine okunur biçimde", g)

def h_():
    h = blokgen.block_html(B("sss", title="SSS", search=True), "", D)
    assert "Randevu şart mı?" in h and "<details" in h
    assert "bkd-ara" in h and 'type="search"' in h and "bk-sr" in h
    h2 = blokgen.block_html(B("sss", title="S", items="Soru | Cevap"), "", {"sss": []})
    assert "Soru" in h2, "elle yazılan sorular da çalışmalı"
t("SSS: panelden veya elle, arama kutusu etiketli", h_)

def i():
    h = blokgen.block_html(B("zaman", title="Tarihçe", items="2014 | Açılış | İlk salon\n2020 | Büyüme | İkinci şube"), "", D)
    assert "<ol" in h and "2014" in h and "İlk salon" in h
    hr = blokgen.block_html(B("rehber", title="Rehber", items="Ara | Telefonla\nGel | Zamanında"), "", D)
    assert "<ol" in hr and h.count("<li") >= 2
t("zaman çizelgesi ve rehber sıralı liste olur", i)

def j():
    h = blokgen.block_html(B("dosya", title="Belgeler"), "", D)
    assert "Fiyat listesi" in h and "PDF" in h and "1,2 MB" in h
    assert 'rel="noopener"' in h and "download" in h
t("dosya listesi: tür ve boyut yazar, güvenli açılır", j)

def k():
    h = blokgen.block_html(B("harita", title="Nerede", zoom=16), "", D)
    assert "output=embed" in h and "Yol tarifi al" in h and "title=" in h
    assert blokgen.block_html(B("harita", title="N"), "", {"adres": ""}) == "", "adres yoksa harita çıkmamalı"
t("harita: adres ayarlardan, yol tarifi bağlantısıyla", k)

def l():
    h = blokgen.block_html(B("saatler", title="Saatler", now=True), "", D)
    assert "Çarşamba" in h and "bugün" in h and "bkd-bugun" in h
    assert "Şu anda açığız" in h and "Kapalı" in h
    h2 = blokgen.block_html(B("saatler", title="S", now=False), "", D)
    assert "Şu anda" not in h2, "şimdi durumu kapatılabilmeli"
t("çalışma saatleri: bugün işaretli, açık/kapalı durumu yazar", l)

def m():
    h = blokgen.block_html(B("subeler", title="Şubeler", cols=3), "", D)
    assert "Merkez" in h and "tel:02125550000" in h and "Yol tarifi" in h
    hb = blokgen.block_html(B("bolgeler", title="Bölgeler"), "", D)
    assert "Teşvikiye" in hb and "Maçka" in hb
t("şubeler ve hizmet bölgeleri kendi listelerinden gelir", m)

def n():
    h = blokgen.block_html(B("iletisim_bilgi", title="İletişim"), "", D)
    assert "tel:05331112233" in h and "mailto:a@b.com" in h and "Instagram" in h
t("iletişim bilgileri tıklanabilir bağlantılarla gelir", n)

def o():
    h = blokgen.block_html(B("kvkk", title="Yasal"), "", D)
    assert "/gizlilik-kvkk" in h and "/cerez-politikasi" in h
    assert "kullanim-kosullari" not in h, "olmayan metne bağlantı verilmemeli"
    assert blokgen.block_html(B("kvkk", title="Y"), "", {"yasal": []}) == "", "hiç metin yoksa bölüm çıkmamalı"
    hi = blokgen.block_html(B("iade_kosul", title="İade"), "", D)
    assert hi == "", "iade metinleri yoksa çıkmamalı"
t("yasal bölümler yalnız gerçekten var olan metinlere bağlanır", o)

def p_():
    kotu = dict(D, subeler=[{"ad": "<script>x()</script>", "adres": "<b>K</b>", "tel": "0"}],
                bolgeler=["<i>B</i>"], yazilar=[{"baslik": "<u>Y</u>", "ozet": "", "slug": "<s>", "tarih": ""}])
    for bid in ("subeler", "bolgeler", "blog"):
        h = blokgen.block_html(B(bid, title="T"), "", kotu)
        assert "<script>" not in h and "<b>K" not in h and "<i>B" not in h and "<u>Y" not in h, "%s kaçırmalı" % bid
t("şube, bölge ve yazı adları siteye betik olarak geçemez", p_)

def q():
    import blocks
    hedef = {b["id"] for b in blocks.BLOCKS if b["cat"] in ("donusum", "icerik", "bilgi")}
    yok = sorted(hedef - set(blok_donusum.KAYIT))
    assert not yok, "kendi kodu olmayan bölüm: %s" % yok
    assert len(hedef) == 23
t("dönüşüm, içerik ve bilgi bölümlerinin (23) hepsinin kendi kodu var", q)

print("\n".join("  ✓ " + n for n in ok))
for n, e in bad: print("  ✗ " + n + "\n" + e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA: %d/%d" % (len(bad), len(ok) + len(bad))))
sys.exit(1 if bad else 0)
