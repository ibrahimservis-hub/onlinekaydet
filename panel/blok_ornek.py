"""Bölümler için örnek içerik: gerçek (Pexels, ücretsiz lisans) fotoğraf + açıklayıcı metin.
Yeni eklenen bölüm boş görünmesin, katalogda her tasarımın ne işe yaradığı anlaşılsın diye kullanılır.
Fotoğraf kimlikleri Pexels sayfalarındaki açıklamalarıyla doğrulanmıştır."""
import zlib

HAVUZ = {
    "kuafor": [3356170, 7755222, 17784004],
    "teknik": [7859953, 29226620, 6419128],
    "veteriner": [7470754, 6234618, 7470634, 7469222],
    "otel": [6186819, 6394574, 19988067, 29702286],
    "fitness": [6339488],
    "market": [28670064, 2733918, 264636],
    "organizasyon": [5038739, 19351562, 34061566, 14703704],
    "lokanta": [4916299, 7129403],
    "oto": [8985615, 8986119, 29284925],
    "avukat": [5668802, 5668791, 5669619],
    "emlak": [8815915, 7642008, 8112187],
    "surucu": [9518026, 9518031],
    "saglik": [3845737, 3845683, 3845745],
    "temizlik": [6195273, 6197111],
    "kurs": [9158761, 18870256, 6936022],
    "eticaret": [7857532, 7857542, 7289727],
}
GENEL = [3356170, 7857532, 8815915, 3845737]

BASLIK = {
    "kuafor": "Saçınıza uzman dokunuş", "teknik": "Arızanız aynı gün çözülsün", "veteriner": "Dostunuz için güvenilir klinik",
    "otel": "Konforlu bir konaklama", "fitness": "Hedefinize birlikte ulaşalım", "market": "Taze ürünler kapınızda",
    "organizasyon": "Hayalinizdeki organizasyon", "lokanta": "Lezzet sofranızda", "oto": "Aracınız güvenli ellerde",
    "avukat": "Hukuki süreçte yanınızdayız", "emlak": "Doğru eve giden yol", "surucu": "Direksiyon başında güvenle",
    "saglik": "Sağlığınız için randevu alın", "temizlik": "Pırıl pırıl mekânlar", "eticaret": "Beğendiğiniz ürünler bir tık uzakta",
    "kurs": "Öğrenmenin en kolay yolu",
}


def foto_kimlik(bid, pack):
    havuz = HAVUZ.get(pack) or GENEL
    return havuz[zlib.crc32(str(bid).encode()) % len(havuz)]


def _px(i, w):
    return "https://images.pexels.com/photos/%d/pexels-photo-%d.jpeg?auto=compress&cs=tinysrgb&w=%d" % (i, i, w)


def foto(bid, pack, w=900):
    return _px(foto_kimlik(bid, pack), w)


def ornek_set(meta, pack):
    """Alan tanımına göre örnek ayar: başlık, açıklama (= bölümün işlevi), düğme, fotoğraf."""
    out = {}
    hero = str(meta["id"]).startswith("hero")
    for f in meta["fields"]:
        k, t = f["k"], f["t"]
        if k == "title":
            out[k] = (BASLIK.get(pack) or meta["name"]) if hero else meta["name"]
        elif k == "sub":
            out[k] = meta["desc"]
        elif k == "cta":
            out[k] = "Randevu al"
        elif t == "img" and k in ("img", "poster"):
            out[k] = foto(meta["id"], pack, 1400)
        elif t == "imgs":
            out[k] = [_px(i, 800) for i in (HAVUZ.get(pack) or GENEL)[:6]]
    return out


# ---------------------------------------------------------------- önizleme için örnek veri
YORUM = [("Siparişim ertesi gün elimdeydi, paketleme çok özenliydi.", "Elif K.", 5),
         ("Fiyat/performans çok iyi, ikinci kez alıyorum.", "Mert A.", 5),
         ("Müşteri hizmetleri hızlı döndü, değişim sorunsuz oldu.", "Zeynep T.", 4)]


def ornek_urunler(origin="", sector=""):
    """Gerçek ürün yokken vitrin bölümlerinin nasıl çalıştığını gösteren örnek ürünler (gerçek fotoğraflı)."""
    import re as _re
    import realimg
    import sektor_ek
    liste = sektor_ek.DEMO_URUN.get(sector) or sektor_ek.DEMO_URUN["eticaret"]
    out = []
    for i, (ad, marka, kat, fiyat, eski, stok) in enumerate(liste):
        tur = next((k for k, rx in realimg.KINDS if _re.search(rx, (ad + " " + kat).lower())), "")
        img = ("%s/tema-urun/%s%d.jpg" % (origin, tur, i % 3 + 1)) if tur else ""
        out.append({"id": "ornek%d" % i, "slug": "ornek-%d" % i, "name": ad, "brand": marka, "cat": kat,
                    "price": eski or fiyat, "sale_price": fiyat if eski else 0, "stock": stok if i != 5 else 3, "low_at": 5,
                    "track_stock": True, "images": [img] if img else [], "status": "active",
                    "created_at": "2026-11-%02d" % (28 - i)})
    return out


def ornek_veri(meta, d, origin="", sector=""):
    """Bölümün beslendiği liste boşsa örnekle doldurur (yalnız önizleme)."""
    mg = meta.get("manage") or ""
    d = dict(d or {})
    if mg.startswith("Ürünler") and not d.get("urunler"):
        ur = ornek_urunler(origin, sector)
        d["urunler"] = ur
        d["satis"] = {p["id"]: 40 - i * 4 for i, p in enumerate(ur)}
        kt = {}
        for p in ur:
            e = kt.setdefault(p["cat"], {"ad": p["cat"], "n": 0, "img": ""})
            e["n"] += 1
            e["img"] = e["img"] or (p["images"] or [""])[0]
        d["kategoriler"] = list(kt.values())
        d["markalar"] = [{"ad": "Atölye", "n": 5}, {"ad": "Nova", "n": 3}, {"ad": "Lino", "n": 2}]
        d["cards"] = [(p["name"], "%s ₺" % (p["sale_price"] or p["price"]), "#", (p["images"] or [""])[0]) for p in ur]
    ornek_ortak(d, sector)
    if mg.startswith("Yorumlar") and not d.get("yorumlar"):
        d["yorumlar"] = [{"yazi": a, "ad": b, "puan": c} for a, b, c in YORUM]
        d["quotes"] = [(a, b) for a, b, _c in YORUM]
    return d


# blok kimliği -> örnek alan değerleri (yalnız önizlemede, alan boşsa)
ALAN = {
    "sayilarla": {"items": "1.250+|Mutlu müşteri\n12|Yıllık deneyim\n4,9|Google puanı\n%98|Tekrar gelen"},
    "deger": {"items": "Aynı gün hizmet|Randevunuz gün içinde\nŞeffaf fiyat|Sürpriz ücret yok\nGaranti|Memnun kalmazsanız tekrar"},
    "surec": {"items": "Randevu alın|Size uygun saati seçin\nGelin, konuşalım|İhtiyacınızı birlikte belirleyelim\nSonuç|Memnun ayrılın"},
    "hesaplayici": {"items": "Temel hizmet|450\nEk bakım|250\nEvde hizmet|150"},
    "karsilastirma": {"items": "Online randevu|var|yok\nŞeffaf fiyat|var|yok\nGaranti|var|yok"},
    "guvence": {"items": "Hızlı kargo|1-2 iş gününde kapınızda\nKolay iade|14 gün içinde ücretsiz\nGüvenli ödeme|256 bit SSL ile\nTaksit|Tüm kartlara 6 taksit"},
    "basinda": {"items": "Yılın en iyi işletmesi|Yerel Gazete|\nYeni şubemiz açıldı|Şehir Haber|"},
    "guven_rozet": {"items": "SSL|Güvenli bağlantı\nKVKK|Verileriniz korunur\n3D Secure|Güvenli ödeme"},
    "video_galeri": {"items": "Tanıtım|https://www.youtube.com/watch?v=ScMzIvxBSi4\nAtölye|https://www.youtube.com/watch?v=aqz-KE-bpKQ"},
    "video_tanitim": {"video": "https://www.youtube.com/watch?v=ScMzIvxBSi4"},
    "s_video": {"video": "https://www.youtube.com/watch?v=ScMzIvxBSi4"},
    "zaman": {"items": "2014|Kuruluş|İlk dükkânımızı açtık\n2019|Büyüme|İkinci şube\n2026|Bugün|Online randevu ve mağaza"},
    "sekme": {"items": "Hizmetler|Tüm hizmetlerimiz uzman kadromuzla.\nFiyatlar|Fiyatlarımız sitede açıkça yazılı.\nGaranti|İşimize güveniyoruz."},
    "sss": {"items": "Randevu nasıl alırım?|Sitedeki randevu düğmesinden saniyeler içinde.\nKartla ödeyebilir miyim?|Evet, tüm kartlar geçerlidir.\nİptal edebilir miyim?|Randevudan 2 saat öncesine kadar ücretsiz."},
    "rehber": {"items": "Hazırlık|Gelmeden önce bilmeniz gerekenler\nGün içinde|Ne kadar sürer, neler olur\nSonrası|Bakım önerileri"},
    "bolgeler": {"items": "Merkez\nYeni Mahalle\nSanayi\nSahil"},
    "sosyal": {"items": "Instagram|https://instagram.com/\nFacebook|https://facebook.com/\nYouTube|https://youtube.com/"},
    "s_baslik": {"text": "Bölüm başlığı burada"}, "s_yazi": {"text": "Buraya istediğiniz yazıyı yazabilirsiniz. Paragraflar, kısa açıklamalar ve duyurular için idealdir."},
    "s_2kolon": {"left": "Sol sütun: hizmetinizi anlatın.", "right": "Sağ sütun: neden sizi seçmeliler?"},
    "s_3kolon": {"items": "Hızlı|Aynı gün dönüş\nGüvenilir|Yazılı garanti\nUygun|Şeffaf fiyat"},
    "s_buton": {"text": "Hemen randevu al", "to": "#"}, "s_harita": {"adr": "Atatürk Cad. No:10, İzmir"},
    "alinti": {"text": "İşini sevenle çalışmak her şeyi değiştiriyor.", "who": "Bir müşterimiz"},
    "whatsapp": {"num": "905320000000", "msg": "Merhaba, bilgi almak istiyorum"},
    "duyuru_bar": {"text": "Bu haftaya özel tüm ürünlerde %20 indirim"},
}
_GUN = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def ornek_alan(meta, sector, origin=""):
    """ornek_set + bölüme özel örnek maddeler + ileri tarihli geri sayım + ürün kuralı."""
    from datetime import datetime, timedelta
    out = ornek_set(meta, sector)
    out.update(ALAN.get(meta["id"], {}))
    keys = {f["k"] for f in meta["fields"]}
    if "end" in keys:
        out["end"] = (datetime.utcnow() + timedelta(days=3, hours=5)).strftime("%Y-%m-%dT%H:%M")
        out.setdefault("title", meta["name"])
    if "rule" in keys:
        out["rule"] = {"v_indirim": "indirim", "v_coksatan": "coksatan", "v_tukeniyor": "stok_az", "v_kampanya": "kampanyali"}.get(meta["id"], "yeni")
    if "imgs" in keys or meta["id"] in ("parallax", "logo_akis", "once_sonra", "gorsel_360"):
        out.setdefault("imgs", [_px(i, 900) for i in (HAVUZ.get(sector) or GENEL)] * (4 if meta["id"] == "gorsel_360" else 1))
    if meta["id"] == "parallax":
        out.setdefault("img", foto(meta["id"], sector, 1600))
        out.setdefault("title", BASLIK.get(sector) or meta["name"])
    return out


def ornek_ortak(d, sector):
    """Hizmet, paket, ekip, saat, iletişim, ödeme gibi listelerin örnekleri (boşsa)."""
    import sitegen
    sv = (sitegen.DEFAULTS.get(sector) or {}).get("services") or [("Temel hizmet", ""), ("Bakım", ""), ("Danışmanlık", "")]
    d.setdefault("hizmetler", [])
    if not d["hizmetler"]:
        d["hizmetler"] = [{"name": a, "desc": b, "price": 350 + 150 * i, "dur": 30 + 15 * (i % 3), "cat": "Hizmetler"} for i, (a, b) in enumerate(sv[:6])]
    if not d.get("paketler"):
        d["paketler"] = [{"ad": "3'lü paket", "fiyat": 1200, "aciklama": "Üç seans, dilediğiniz zaman", "kazanc": 150},
                         {"ad": "Aylık bakım", "fiyat": 900, "aciklama": "Ayda iki ziyaret", "kazanc": 100}]
    if not d.get("ekip"):
        d["ekip"] = [{"ad": "Ayşe Yılmaz", "unvan": "Uzman", "img": ""}, {"ad": "Mehmet Kaya", "unvan": "Kurucu", "img": ""}, {"ad": "Deniz Aksoy", "unvan": "Uzman", "img": ""}]
        d["cards"] = d.get("cards") or [(x["ad"], x["unvan"], "", "") for x in d["ekip"]]
    if not d.get("saatler"):
        d["saatler"] = [{"gun": g, "ac": "09:00", "kapa": "19:00", "kapali": i == 6} for i, g in enumerate(_GUN)]
        d["bugun"], d["acik_mi"] = 2, True
    if not (d.get("iletisim") or {}).get("tel"):
        d["iletisim"] = {"tel": "0532 000 00 00", "eposta": "bilgi@ornek.com", "adres": "Atatürk Cad. No:10, İzmir", "whatsapp": "905320000000"}
    d["adres"] = d.get("adres") or "Atatürk Cad. No:10, İzmir"
    d["address"] = d.get("address") or d["adres"]
    if not d.get("kartlar"):
        d["kartlar"] = ["Visa", "Mastercard", "Troy", "American Express"]
    if not d.get("taksit"):
        d["taksit"] = [{"banka": b, "ay": ["Tek çekim", "3 taksit", "6 taksit"], "tutar": [1000, 343, 175]} for b in ("Bonus", "World", "Maximum")]
    if not d.get("google"):
        d["google"] = {"puan": 4.9, "adet": 128, "yorumlar": [{"yazi": a, "ad": b, "puan": c} for a, b, c in YORUM]}
    elif not (d["google"] or {}).get("yorumlar"):
        d["google"] = dict(d["google"], puan=4.9, adet=128, yorumlar=[{"yazi": a, "ad": b, "puan": c} for a, b, c in YORUM])
    if not d.get("yazilar"):
        d["yazilar"] = [{"baslik": "Mevsim geçişinde bakım önerileri", "ozet": "Kısa ve uygulanabilir ipuçları.", "slug": "ornek", "img": foto("blog1", sector, 800), "tarih": "2026-11-01"},
                        {"baslik": "Sık yapılan 5 hata", "ozet": "Bunlardan kaçınarak zaman kazanın.", "slug": "ornek2", "img": foto("blog2", sector, 800), "tarih": "2026-10-20"}]
    if not d.get("sss"):
        d["sss"] = [{"soru": "Randevu nasıl alırım?", "cevap": "Sitedeki randevu düğmesinden."}, {"soru": "Kartla ödeme var mı?", "cevap": "Evet."}]
    if not d.get("fotograflar"):
        d["fotograflar"] = [_px(i, 900) for i in (HAVUZ.get(sector) or GENEL)]
    if not d.get("subeler"):
        d["subeler"] = [{"ad": "Merkez şube", "adres": "Atatürk Cad. No:10", "tel": "0532 000 00 00"}, {"ad": "Sahil şube", "adres": "Kordon Boyu No:5", "tel": "0532 000 00 01"}]
    if not d.get("baglantilar"):
        d["baglantilar"] = {"instagram": "https://instagram.com/", "facebook": "https://facebook.com/"}
    d.setdefault("duyuru", "Bu haftaya özel tüm ürünlerde %20 indirim")
    if not d.get("yasal"):
        d["yasal"] = [{"slug": "gizlilik-kvkk", "title": "Gizlilik ve KVKK"}, {"slug": "cerez-politikasi", "title": "Çerez politikası"}, {"slug": "kullanim-kosullari", "title": "Kullanım koşulları"}]
    return d
