"""Yapı, sektörel ve serbest bölümler. HTML bölümünde betik temizliği ayrıca sınanır."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import blokgen, blok_yapi
blokgen.kayit_al(blok_yapi.KAYIT, blok_yapi.CSS, blok_yapi.KABUK)
ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-700:]))

D = {"kategoriler": [{"ad": "Saç", "n": 3, "img": "k1"}, {"ad": "Cilt", "n": 2, "img": "k2"}],
     "hizmetler": [{"name": "Latte", "price": 90, "cat": "İçecek", "desc": "Çift shot"},
                   {"name": "Cheesecake", "price": 160, "cat": "Tatlı"}],
     "odalar": [{"ad": "Deniz manzaralı", "fiyat": 3200, "kisi": 2, "images": ["k1"], "desc": "Balkonlu"}],
     "program": [{"saat": "19:00", "gun": "Salı", "ders": "Yoga", "egitmen": "Ayşe"}],
     "etkinlikler": [{"ad": "Açılış", "kalan": 12}],
     "baglantilar": {"instagram": "https://instagram.com/x"},
     "iletisim": {"tel": "0533 111 22 33"}, "adres": "Nişantaşı", "yil": 2026, "firma": "Nisan",
     "markalar": [{"ad": "Bosch"}], "accent": "#b4600a"}

def B(bid, **st):
    return {"iid": "ii", "bid": bid, "wire": "band", "on": True, "set": st}

# ---- güvenli HTML
def a():
    g = blok_yapi.guvenli_html
    assert "<script" not in g('<script>alert(1)</script><p>iyi</p>') and "iyi" in g('<script>alert(1)</script><p>iyi</p>')
    assert "onerror" not in g('<img src=x onerror=alert(1)>')
    assert "javascript" not in g('<a href="javascript:alert(1)">x</a>')
    assert "<form" not in g('<form action="/x"><input name="a"></form>')
    assert "<style" not in g('<style>body{display:none}</style>')
    assert "<b>kalın</b>" in g("<b>kalın</b>")
    assert 'href="/sayfa"' in g('<a href="/sayfa">x</a>')
t("HTML bölümü: betik, olay, form ve style temizlenir; biçim korunur", a)

def b():
    g = blok_yapi.guvenli_html
    iy = g('<iframe src="https://www.youtube-nocookie.com/embed/abc"></iframe>')
    assert "<iframe" in iy and "title=" in iy, "izinli gömme kalmalı ve başlıklanmalı"
    assert "<iframe" not in g('<iframe src="https://kotu.com/x"></iframe>'), "yabancı gömme atılmalı"
    assert "<iframe" not in g('<iframe src="javascript:alert(1)"></iframe>')
t("HTML bölümü: yalnız bilinen video ve harita gömülebilir", b)

def c_():
    h = blokgen.block_html(B("s_kod", html='<p>Merhaba</p><script>kotu()</script>'), "", D)
    assert "Merhaba" in h and "<script" not in h
    assert blokgen.block_html(B("s_kod", html="   "), "", D) == ""
t("HTML bölümü boşsa çıkmaz, betik siteye geçmez", c_)

# ---- yapı
def d_():
    h = blokgen.block_html(B("mobil_bar", items="Randevu | /randevu\nAra | tel:05331112233", count=4), "", D)
    assert "bky-mb" in h and "/randevu" in h and 'aria-label' in h
    assert "@media(max-width:820px)" in blok_yapi.CSS, "yalnız telefonda görünmeli"
    hk = blokgen.block_html(B("mobil_bar", items="X | javascript:k()"), "", D)
    assert "javascript:" not in hk
t("mobil bar: telefonda altta, kötü bağlantı süzülür", d_)

def e():
    h = blokgen.block_html(B("mobil_menu", source="ürün kategorileri", look="ızgara", img=True, side="sağ", search=True), "", D)
    assert "Saç" in h and "/magaza?kat=Sa" in h and "bky-dr-sag" in h
    assert 'role="dialog"' in h and "Escape" in h, "çekmece klavyeyle kapanmalı"
    assert "k1" in h, "kategori görseli gelmeli"
    h2 = blokgen.block_html(B("mobil_menu", source="elle", items="Hakkımızda | /hakkimizda"), "", D)
    assert "Hakkımızda" in h2 and "Saç" not in h2
t("mobil menü: kategoriler ya da elle; görselli, klavyeyle kapanır", e)

def f():
    rows = [dict(B("footer", cols=2, links="Kurumsal | Hakkımızda | /h\nKurumsal | İletişim | /i\nYardım | SSS | /s"), on=True)]
    h = blokgen.block_html(rows[0], "", D)
    assert "Kurumsal" in h and "SSS" in h and "OnlineKaydet ile yayınlanır" in h
    kb = blokgen.kabuk_ayar(rows, "", {"ii": D})
    assert kb.get("footer_var") is True, "footer bölümü kabuğa bildirmeli"
t("footer: sütunlu bağlantılar, OnlineKaydet bağlantısı korunur", f)

def g():
    rows = [B("menu_gorunum", style="ortalı", sticky=False, shrink=True),
            B("logo_bolum", img="logo1", pos="orta", size=52)]
    assert blokgen.block_html(rows[0], "", D) == "", "kabuk bölümü akışta bir şey basmamalı"
    kb = blokgen.kabuk_ayar(rows, "", {})
    assert kb["menu_yapis"] is False and kb["logo_orta"] is True and kb["logo"] == "logo1" and kb["logo_boy"] == 52
t("menü görünümü ve logo bölümü kabuğu ayarlar", g)

def h_():
    sayfa = blokgen.page_html({"title": "Ana", "home": True},
                              [B("logo_bolum", img="logo1", pos="orta", size=50),
                               B("footer", cols=2, links="A | B | /b")],
                              {"name": "Nisan", "tel": "05331112233", "brand": {}, "yil": 2026},
                              {"ii": D}, "")
    assert "bk-top-orta" in sayfa and "logo1" in sayfa
    assert sayfa.count("OnlineKaydet ile yayınlanır") == 1, "footer bölümü varken hazır alt bilgi tekrar etmemeli"
t("kabuk katkıları sayfaya uygulanır, alt bilgi tekrar etmez", h_)

def i():
    h = blokgen.block_html(B("dil", langs="Türkçe, English, Deutsch", style="kısaltma"), "", D)
    assert "?dil=tu" in h or "?dil=tü" in h or "?dil=en" in h
    assert 'hreflang=' in h and h.count("<a") == 3
    assert blokgen.block_html(B("dil", langs="Türkçe"), "", D) == "", "tek dilde seçici çıkmamalı"
t("dil seçici: iki dilden azsa çıkmaz, hreflang verir", i)

def j():
    h = blokgen.block_html(B("qr_menu", title="Menü", source="ürünler", price=True, call=True, print=True), "", D)
    assert "Latte" in h and "90 ₺" in h and "Garson çağır" in h and "Yazdır" in h
    h2 = blokgen.block_html(B("qr_menu", title="M", source="ürünler", price=False, call=False, print=False), "", D)
    assert "90 ₺" not in h2 and "Garson" not in h2
    assert "@media print" in blok_yapi.CSS, "yazdırmada düğmeler gizlenmeli"
t("QR menü: fiyat, garson çağır ve yazdır ayrı ayrı kapanır", j)

def k():
    h = blokgen.block_html(B("cerez", text="Çerez kullanıyoruz", accept="Tamam", pos="alt"), "", D)
    assert 'id="okc"' in h and "Çerez kullanıyoruz" in h and "#b4600a" in h
t("çerez bölümü site bandının aynısını üretir, tema rengini alır", k)

# ---- sektörel
def l():
    h = blokgen.block_html(B("menu_karti", title="Menü"), "", D)
    assert "İçecek" in h and "Tatlı" in h and "Çift shot" in h and "160 ₺" in h
t("menü kartı kategoriye göre gruplanır", l)

def m():
    h = blokgen.block_html(B("rezervasyon", title="Rezervasyon"), "", D)
    assert 'type="date"' in h and 'type="time"' in h and 'name="kisi"' in h
    hb = blokgen.block_html(B("bilet", title="Bilet"), "", D)
    assert "Açılış" in hb and "12 kişilik yer kaldı" in hb
t("rezervasyon ve bilet formları gerçek alanlarla kurulur", m)

def n():
    h = blokgen.block_html(B("oda", title="Odalar", cols=3), "", D)
    assert "Deniz manzaralı" in h and "3.200" in h and "2 kişilik" in h
    hp = blokgen.block_html(B("ders_program", title="Program"), "", D)
    assert "<table" in hp and "Yoga" in hp and 'scope="col"' in hp
t("oda ve ders programı kendi kayıtlarından gelir", n)

def o():
    h = blokgen.block_html(B("portfoy", title="Portföy"), "", D)
    assert 'action="/portfoy"' in h and 'name="oda"' in h and 'role="search"' in h
    hm = blokgen.block_html(B("marka_liste", title="Markalar"), "", D)
    assert "Bosch" in hm
t("portföy arama ve marka listesi çalışır", o)

# ---- serbest
def p_():
    assert "font-size:60px" in blokgen.block_html(B("s_baslik", text="Başlık", size=60), "", D)
    assert "<hr" in blokgen.block_html(B("s_ayirici", style="nokta"), "", D)
    assert "height:70px" in blokgen.block_html(B("s_bosluk", h=70), "", D)
    assert blokgen.block_html(B("s_buton", text="Git", to="/x"), "", D).count('href="/x"') == 1
    assert "javascript" not in blokgen.block_html(B("s_buton", text="Git", to="javascript:k()"), "", D)
    assert "youtube-nocookie" in blokgen.block_html(B("s_video", video="https://youtu.be/abc12345"), "", D)
    assert "output=embed" in blokgen.block_html(B("s_harita", adr="Nişantaşı"), "", D)
t("serbest bölümler: başlık, ayırıcı, boşluk, buton, video, harita", p_)

def q():
    for bid in ("s_baslik", "s_yazi", "s_resim", "s_resim_yazi", "s_2kolon", "s_3kolon", "s_buton", "s_video", "s_kod"):
        assert blokgen.block_html(B(bid), "", D) == "", "%s: içeriği yokken çıkmamalı" % bid
t("serbest bölümler içeriği yokken sayfaya boş kutu koymaz", q)

def r():
    import blocks
    hedef = {b["id"] for b in blocks.BLOCKS if b["cat"] in ("yapi", "sektorel", "serbest")}
    yok = sorted(hedef - set(blok_yapi.KAYIT))
    assert not yok, "kendi kodu olmayan bölüm: %s" % yok
    tum = {b["id"] for b in blocks.BLOCKS}
    eksik = sorted(tum - set(blokgen.OZEL))
    assert not eksik, "126 bölümün hepsinin kendi kodu olmalı, eksik: %s" % eksik
    assert len(tum) == 126
t("126 bölümün tamamının kendi kodu var", r)

print("\n".join("  ✓ " + n for n in ok))
for n, e in bad: print("  ✗ " + n + "\n" + e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA: %d/%d" % (len(bad), len(ok) + len(bad))))
sys.exit(1 if bad else 0)
