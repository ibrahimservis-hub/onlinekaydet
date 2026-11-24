"""Servis kayıtları ekranlarının sektöre göre dili.

Müşteri panelindeki servis, takvim, müşteri, stok, teklif, rapor ve ayar ekranları teknik servis için yazıldı
("Yolda", "Arıza", "Cihaz", "Seri no", "Marka", "Yedek parça"). Kurs, avukat, temizlik, nakliye gibi işlerde bu kelimeler
yanlış olur. Burada her sektörün iş akışı (durumlar, düğmeler, adımlar) ve ekran metinleri sektörün kendi terimleriyle
üretilir; panel bunu /yp/boot içinde `sv` olarak alır. Teknik servis sektörlerinde None döner, panelin varsayılanı geçerli kalır.
"""
import sektor_dil as SD

# sektör -> iş akışı türü. Anahtarı olmayan sektörler (randevu ve sipariş aileleri) kendi ekranını kullanır.
ARCH_OF = {}
for _a, _ks in {
    "arac": ("oto_yikama", "oto_kaplama"),
    "arac_servis": ("oto_servis", "lastikci"),
    "teslim": ("ayakkabi_tamir", "telefon_tamir", "terzi", "kuru_temizleme", "hali_yikama"),
    "saha_teknik": ("asansor", "su_aritma", "jenerator", "yazici_servis", "gunes_enerjisi", "cilingir"),
    "saha_hizmet": ("temizlik", "bocek_ilaclama", "havuz_bakim", "peyzaj", "tadilat", "cam_dograma"),
    "egitim": ("surucu_kursu", "src_kursu", "etut_merkezi", "dil_okulu", "muzik_kursu", "anaokulu", "ozel_ders", "bilgisayar_kursu"),
    "dosya": ("avukat", "muhasebe", "tercume", "mimar"),
    "etkinlik": ("dugun_salonu", "dj_muzik", "fotografci", "tur_organizasyon"),
    "yol": ("oto_cekici", "nakliye", "kurye", "transfer", "arac_kiralama"),
    "emlak": ("emlakci",),
}.items():
    for _k in _ks:
        ARCH_OF[_k] = _a

_TLO = str.maketrans({"I": "ı", "İ": "i"})


def _lo(s):
    return s.translate(_TLO).lower()


def _fmt(v, p):
    if isinstance(v, str):
        for k, x in p.items():
            v = v.replace("{" + k + "}", x)
        return v
    if isinstance(v, (list, tuple)):
        return type(v)(_fmt(x, p) for x in v)
    if isinstance(v, dict):
        return {k: _fmt(x, p) for k, x in v.items()}
    return v


def _terms(key):
    r = SD.ROWS[key]
    K, KP = SD._sp(r["kisi"])
    I, IP = SD._sp(r["is"])
    if IP.endswith("Defteri"):
        IP = I + "ler"
    C, CP = SD._sp(r["cihaz"])
    return {"K": K, "k": _lo(K), "KP": KP, "kp": _lo(KP), "I": I, "i": _lo(I), "IP": IP, "ip": _lo(IP),
            "C": C, "c": _lo(C), "CP": CP, "cp": _lo(CP), "S": r["sorun"], "s": _lo(r["sorun"]),
            "STOK": r["stok"], "TEKLIF": r["teklif"], "YER": r["yer"]}


# ---- ortak: her iş akışının kullandığı ek metinler (ekran başlıkları, tablo sütunları, belge etiketleri)
def _ek(part="Parça", brand="Marka", dev_rep="Cihaz türü", **o):
    d = {"smSub": "Her {c} ve {i} geçmişi tek kartta.", "repeatNote": "Aynı {s} birden fazla kez kaydedilmiş.",
         "devsH": "{CP}", "devAdd": "{C} ekle", "devNone": "Kayıtlı {c} yok.", "histH": "{I} geçmişi",
         "partsT": "{STOK}", "partsSub": "Kullanılan " + _lo(part) + " kayıt tamamlanınca stoktan düşer, iptalde geri gelir.",
         "partAddB": part + " ekle", "partKinds": part + " çeşidi", "partName": part, "partNone": part + " bulunamadı.",
         "partSearch": part + ", kod veya tedarikçi ara", "brandCol": brand, "brandsT": brand + "ler" if not brand.endswith("e") else brand + "ler",
         "brandAdd": brand + " ekle", "brandNone": brand + " yok.", "ayarT": "{I} ayarları",
         "ayarSub": "Belgelerde görünen firma bilgileri, {k} ekranı kuralları ve " + _lo(brand) + " listesi.",
         "teklifT": "{TEKLIF}", "teklifSub": "Müşteriye " + _lo(part) + " ve işçilik toplamını tek tutar olarak verin; onaylanınca kayda çevirin.",
         "teklifDev": "{C} / {s}", "teklifPart": part + " adı", "teklifFault": "{S}:",
         "fisT": "{I} fişi", "fisDev": "{C}", "fisFault": "{S}", "fisPart": part, "fisDone": "Yapılan iş",
         "rBrand": brand + " bazında", "rBrandC": brand, "rDev": dev_rep + " bazında", "rDevC": dev_rep,
         "navStok": "{STOK}", "navTeklif": "Teklifler", "navAyar": "{I} ayarları", "navAt": "Atölye"}
    d.update(o)
    return d


STD_ST = {"yeni": ["Talep alındı", "y"], "atandi": ["{K} atandı", "b"], "yolda": ["Yolda", "b"], "basladi": ["İşlemde", "b"],
          "tamamlandi": ["Tamamlandı", "g"], "faturalandi": ["Faturalandı", "g"], "iptal": ["İptal", "r"]}
STEPS6 = ["yeni", "atandi", "yolda", "basladi", "tamamlandi", "faturalandi"]
STEPS5N = ["yeni", "atandi", "basladi", "tamamlandi", "faturalandi"]


def _st(**o):
    d = {k: list(v) for k, v in STD_ST.items()}
    for k, v in o.items():
        d[k] = list(v)
    return d


# ---- iş akışı türleri
ARCH = {
    # araç bakım, yıkama, kaplama: araç kabul edilir, uygulama yapılır, teslim edilir
    "arac": {
        "ad": "Araç kaydı", "ads": "Araç kayıtları", "sub": "Araç kabulünden teslime kadar her iş burada: hangi araç, hangi uygulama, kim yapıyor, ne kadar.",
        "st": _st(yeni=("Talep alındı", "y"), yolda=("Araç teslim alındı", "b"), basladi=("Uygulamada", "b"), tamamlandi=("Teslime hazır", "g"), faturalandi=("Teslim edildi", "g")),
        "next": {"atandi": [["yolda", "Aracı teslim aldım"], ["basladi", "Uygulamaya başla"]], "yolda": [["basladi", "Uygulamaya başla"]]},
        "steps": STEPS6, "pkg": True, "ws": False,
        "L": {"dev": "Araç ve uygulama", "arama": "Numara, müşteri, telefon, plaka veya uygulama ara", "devD": "Araç", "serD": "Plaka",
              "faultL": "Uygulama / istek", "faultPh": "Örn. Seramik kaplama, iç detay temizlik, far parlatma", "brandL": "Uygulama paketi", "typeL": "Araç tipi",
              "typePh": "Örn. SUV, sedan, hatchback", "modelL": "Araç (marka ve model)", "modelPh": "Örn. Volkswagen Passat", "serL": "Plaka", "serPh": "06 ABC 123",
              "whenL": "Teslim / randevu zamanı", "whenD": "Randevu", "addrL": "Adres (araç alıma gidilecekse)", "addrPh": "Boş bırakılabilir",
              "doneL": "Yapılan uygulama", "donePh": "Hangi uygulamalar yapıldı? Örn. 2 kat seramik, iç detay", "partsL": "Kullanılan ürün ve sarf", "partAdd": "+ Ürün ekle",
              "laborL": "Uygulama ücreti (₺)", "finish": "Teslime hazır yap", "fin": "Teslim edildi olarak işaretle", "again": "Tekrar uygulama / rötuş: yeniden ata",
              "kapTitle": "Uygulamayı tamamla"},
        "ek": dict(part="Ürün", brand="Uygulama paketi", dev_rep="Araç tipi", smSub="Her müşterinin aracı ve uygulama geçmişi tek kartta.",
                   repeatNote="Aynı araç için aynı uygulama birden fazla kez kaydedilmiş.", devsH="Araçlar", devAdd="Araç ekle", devNone="Kayıtlı araç yok.",
                   histH="Uygulama geçmişi", brandsT="Uygulama paketleri", fisT="Araç teslim fişi", fisDev="Araç", fisFault="Uygulama", fisDone="Yapılan uygulama",
                   teklifDev="Araç / uygulama", teklifFault="Uygulama:", teklifSub="Müşteriye ürün ve uygulama ücretini tek tutar olarak verin; onaylanınca araç kaydına çevirin.",
                   navStok="Ürün ve sarf stoğu", partsT="Ürün ve sarf stoğu", navAyar="Uygulama ayarları", ayarT="Uygulama ayarları", navAt="Araç teslim"),
        "hide": ["satolye"],
    },
    # oto servis, lastikçi: araç atölyeye bırakılır
    "arac_servis": {
        "ad": "{I}", "ads": "{IP}", "sub": "Araç kabulünden teslime kadar her iş burada: hangi araç, hangi iş, kim yapıyor, ne kadar.",
        "st": _st(yeni=("Talep alındı", "y"), yolda=("Araç teslim alındı", "b"), basladi=("İşlemde", "b"), tamamlandi=("Teslime hazır", "g"), faturalandi=("Teslim edildi", "g")),
        "next": {"atandi": [["yolda", "Aracı teslim aldım"], ["basladi", "İşleme başla"]], "yolda": [["basladi", "İşleme başla"]]},
        "steps": STEPS6, "ws": False,
        "L": {"dev": "Araç ve iş", "arama": "Numara, müşteri, telefon, plaka veya iş ara", "devD": "Araç", "serD": "Plaka", "faultL": "{S} / yapılacak iş",
              "faultPh": "Örn. Periyodik bakım, fren balatası, lastik değişimi", "brandL": "Araç markası", "typeL": "Araç tipi", "typePh": "Örn. SUV, sedan, hafif ticari",
              "modelL": "Model", "modelPh": "Örn. Passat 1.6 TDI", "serL": "Plaka", "serPh": "06 ABC 123", "serial": True, "whenL": "Teslim / randevu zamanı", "whenD": "Randevu",
              "addrL": "Adres (araç alıma gidilecekse)", "addrPh": "Boş bırakılabilir", "doneL": "Yapılan iş", "donePh": "Hangi işlemler yapıldı?", "partsL": "Kullanılan parça ve sarf",
              "partAdd": "+ Parça ekle", "laborL": "İşçilik ücreti (₺)", "finish": "Teslime hazır yap", "fin": "Teslim edildi olarak işaretle",
              "again": "Tekrar {s}: yeniden ata", "kapTitle": "İşi tamamla"},
        "ek": dict(part="Parça", brand="Araç markası", dev_rep="Araç tipi", smSub="Her müşterinin aracı ve iş geçmişi tek kartta.", devsH="Araçlar", devAdd="Araç ekle",
                   devNone="Kayıtlı araç yok.", fisT="Araç teslim fişi", fisDev="Araç", fisFault="İş", teklifDev="Araç / iş", navAt="Araç teslim"),
        "hide": ["satolye"],
    },
    # telefon, ayakkabı, terzi, kuru temizleme, halı yıkama: eşya teslim alınır, işlenir, teslim edilir
    "teslim": {
        "ad": "{I}", "ads": "{IP}", "sub": "Teslim alınan {c} burada başlar, teslim edilene kadar takip edilir: kim, ne zaman, hangi {k}, ne kadar.",
        "st": _st(yeni=("Kayıt alındı", "y"), yolda=("Teslim alındı", "b"), basladi=("İşlemde", "b"), tamamlandi=("Hazır", "g"), faturalandi=("Teslim edildi", "g")),
        "next": {"atandi": [["yolda", "Teslim aldım"], ["basladi", "İşleme başla"]], "yolda": [["basladi", "İşleme başla"]]},
        "steps": STEPS6, "ws": False,
        "L": {"dev": "{C} ve işlem", "arama": "Numara, müşteri, telefon veya {c} ara", "devD": "{C}", "serD": "Etiket no", "faultL": "Yapılacak işlem",
              "faultPh": "Müşterinin istediği işlem", "brandL": "İşlem türü", "typeL": "{C} türü", "typePh": "", "modelL": "Ayrıntı", "modelPh": "Renk, beden, model...",
              "serL": "Etiket no", "serPh": "", "serial": True, "whenL": "Teslim tarihi", "whenD": "Teslim", "addrL": "Adres (alıma gidilecekse)", "addrPh": "Boş bırakılabilir",
              "doneL": "Yapılan işlem", "donePh": "Ne yapıldı?", "partsL": "Kullanılan malzeme", "partAdd": "+ Malzeme ekle", "laborL": "İşçilik ücreti (₺)",
              "finish": "Hazır yap", "fin": "Teslim edildi olarak işaretle", "again": "Tekrar işlem: yeniden ata", "kapTitle": "İşlemi tamamla"},
        "ek": dict(part="Malzeme", brand="İşlem türü", dev_rep="{C} türü", fisT="Teslim fişi", fisDone="Yapılan işlem", fisFault="İstenen işlem", teklifDev="{C} / işlem",
                   teklifFault="İşlem:", navAt="Teslim bekleyen"),
        "hide": ["satolye"],
    },
    # asansör, su arıtma, jeneratör, yazıcı, güneş enerjisi, çilingir: teknisyen müşterinin yerine gider
    "saha_teknik": {
        "ad": "{I}", "ads": "{IP}", "sub": "Müşterinin çağrısından tamamlanmasına kadar her kayıt burada: kim, ne zaman, hangi {k}, ne kadar.",
        "st": _st(yeni=("Talep alındı", "y"), yolda=("Yolda", "b"), basladi=("İşlemde", "b"), tamamlandi=("Tamamlandı", "g"), faturalandi=("Faturalandı", "g")),
        "next": {"atandi": [["yolda", "Yola çıktı"], ["basladi", "İşe başladı"]], "yolda": [["basladi", "İşe başladı"]]},
        "steps": ["yeni", "atandi", "yolda", "basladi", "tamamlandi"], "ws": False,
        "L": {"dev": "{C} ve {s}", "arama": "Numara, müşteri, telefon, adres veya {s} ara", "devD": "{C}", "faultL": "{S} / yapılacak iş", "faultPh": "Müşterinin anlattığı {s}",
              "typeL": "{C} türü", "typePh": "", "again": "Tekrar {s}: yeniden ata"},
        "ek": dict(part="Parça", brand="Marka", dev_rep="{C} türü"),
        "hide": [],
    },
    # temizlik, ilaçlama, havuz, peyzaj, tadilat, cam doğrama: ekip adrese gider, hizmeti yapar
    "saha_hizmet": {
        "ad": "{I}", "ads": "{IP}", "sub": "Talepten tamamlanmaya kadar her {i} burada: kim, nerede, ne zaman, hangi {k}, ne kadar.",
        "st": _st(yeni=("Talep alındı", "y"), yolda=("Yolda", "b"), basladi=("Çalışmada", "b"), tamamlandi=("Tamamlandı", "g"), faturalandi=("Faturalandı", "g")),
        "next": {"atandi": [["yolda", "Yola çıktı"], ["basladi", "Çalışmaya başla"]], "yolda": [["basladi", "Çalışmaya başla"]]},
        "steps": ["yeni", "atandi", "yolda", "basladi", "tamamlandi", "faturalandi"], "ws": False,
        "L": {"dev": "Yer ve iş", "arama": "Numara, müşteri, telefon, adres veya iş ara", "devD": "Hizmet", "serD": "", "faultL": "Yapılacak iş", "faultPh": "Örn. Detaylı temizlik, 3+1 daire",
              "brandL": "Hizmet türü", "typeL": "Alan / ölçü", "typePh": "Örn. 3+1 daire, 120 m²", "modelL": "Not", "modelPh": "Kat, kapı kodu, özel istek", "serL": "", "serPh": "",
              "whenL": "Planlanan zaman", "whenD": "Planlanan", "addrL": "Adres", "addrPh": "Mahalle, sokak, kapı no, ilçe", "doneL": "Yapılan iş", "donePh": "Neler yapıldı?",
              "partsL": "Kullanılan malzeme", "partAdd": "+ Malzeme ekle", "laborL": "İşçilik ücreti (₺)", "finish": "Tamamla", "fin": "Faturalandı olarak işaretle",
              "again": "Tekrar iş: yeniden ata", "kapTitle": "İşi tamamla"},
        "ek": dict(part="Malzeme", brand="Hizmet türü", dev_rep="Alan", fisT="{I} fişi", fisFault="Yapılan hizmet", teklifDev="{C} / iş", teklifFault="İş:", navAt="Atölye"),
        "hide": ["satolye"],
    },
    # kurslar: kayıt, eğitmen, ders, ödeme
    "egitim": {
        "ad": "{I}", "ads": "{IP}", "sub": "Ön kayıttan ödemeye kadar her {i} burada: kim, hangi program, hangi {k}, ne kadar.",
        "st": _st(yeni=("Ön kayıt", "y"), basladi=("Eğitimde", "b"), tamamlandi=("Tamamlandı", "g"), faturalandi=("Ödemesi alındı", "g")),
        "next": {"atandi": [["basladi", "Eğitime başla"]]},
        "steps": STEPS5N, "ws": False,
        "L": {"dev": "{C} ve program", "arama": "Numara, {c}, telefon veya program ara", "devD": "{C}", "serD": "", "faultL": "Kayıt amacı / not", "faultPh": "Örn. B sınıfı ehliyet, hafta sonu grubu",
              "brandL": "Program", "typeL": "Grup / sınıf", "typePh": "Örn. Hafta içi akşam grubu", "modelL": "Seviye", "modelPh": "Örn. Başlangıç", "serL": "", "serPh": "",
              "whenL": "Başlangıç zamanı", "whenD": "Başlangıç", "addrL": "Adres (isteğe bağlı)", "addrPh": "Boş bırakılabilir", "doneL": "İşlenen konular ve notlar", "donePh": "Hangi konular işlendi?",
              "partsL": "Verilen materyal", "partAdd": "+ Materyal ekle", "laborL": "Eğitim ücreti (₺)", "finish": "Eğitimi tamamla", "fin": "Ödemesi alındı olarak işaretle",
              "again": "Telafi: yeniden ata", "kapTitle": "Eğitimi tamamla"},
        "ek": dict(part="Materyal", brand="Program", dev_rep="Grup", smSub="Her {c} ve eğitim geçmişi tek kartta.", repeatNote="Aynı konu birden fazla kez kaydedilmiş.",
                   histH="Eğitim geçmişi", partsSub="Verilen materyaller kayıt tamamlanınca stoktan düşer, iptalde geri gelir.", brandsT="Programlar",
                   teklifSub="Adaya eğitim ücretini tek tutar olarak verin; onaylanınca kayda çevirin.", teklifDev="{C} / program", teklifPart="Kalem", teklifFault="Konu:",
                   fisT="{I} makbuzu", fisFault="Konu", fisDone="İşlenen konular", rDev="Grup bazında", rDevC="Grup", navAt="Eğitim"),
        "hide": ["satolye", "skonum"],
    },
    # avukat, muhasebe, tercüme, mimar: dosya açılır, çalışılır, ücret alınır
    "dosya": {
        "ad": "{I}", "ads": "{IP}", "sub": "Talepten teslime kadar her {i} burada: kim, ne konuda, hangi {k}, ne kadar.",
        "st": _st(yeni=("Talep alındı", "y"), basladi=("Çalışmada", "b"), tamamlandi=("Tamamlandı", "g"), faturalandi=("Ücret alındı", "g")),
        "next": {"atandi": [["basladi", "Çalışmaya başla"]]},
        "steps": STEPS5N, "ws": False,
        "L": {"dev": "{C} ve konu", "arama": "Numara, {c}, telefon veya konu ara", "devD": "{C}", "serD": "", "faultL": "Konu", "faultPh": "Talebin kısa özeti",
              "brandL": "{I} türü", "typeL": "Alt konu", "typePh": "", "modelL": "Not", "modelPh": "", "serL": "", "serPh": "", "whenL": "Planlanan zaman", "whenD": "Planlanan",
              "addrL": "Adres (isteğe bağlı)", "addrPh": "Boş bırakılabilir", "doneL": "Yapılan çalışma", "donePh": "Ne yapıldı?", "partsL": "Masraf ve harçlar", "partAdd": "+ Masraf ekle",
              "laborL": "Ücret (₺)", "finish": "Tamamla", "fin": "Ücret alındı olarak işaretle", "again": "Tekrar çalışma: yeniden ata", "kapTitle": "Çalışmayı tamamla"},
        "ek": dict(part="Masraf", brand="{I} türü", dev_rep="Konu", smSub="Her {c} ve {i} geçmişi tek kartta.", repeatNote="Aynı konu birden fazla kez kaydedilmiş.",
                   partsSub="Kullanılan malzemeler kayıt tamamlanınca stoktan düşer, iptalde geri gelir.", brandsT="{I} türleri",
                   teklifSub="Müşteriye ücreti tek tutar olarak verin; onaylanınca kayda çevirin.", teklifDev="{C} / konu", teklifPart="Kalem", teklifFault="Konu:",
                   fisT="{I} makbuzu", fisFault="Konu", fisDone="Yapılan çalışma", fisPart="Masraf", rDev="Konu bazında", rDevC="Konu", navAt="Teslim"),
        "hide": ["satolye", "skonum"],
    },
    # düğün salonu, DJ, fotoğrafçı, tur: etkinlik planlanır, yapılır, ödeme alınır
    "etkinlik": {
        "ad": "{I}", "ads": "{IP}", "sub": "Talepten etkinlik sonrasına kadar her {i} burada: kim, ne zaman, hangi {k}, ne kadar.",
        "st": _st(yeni=("Talep alındı", "y"), basladi=("Etkinlikte", "b"), tamamlandi=("Tamamlandı", "g"), faturalandi=("Ödeme alındı", "g")),
        "next": {"atandi": [["basladi", "Etkinliğe başla"]]},
        "steps": STEPS5N, "ws": False,
        "L": {"dev": "{C} ve istek", "arama": "Numara, müşteri, telefon, {c} veya konu ara", "devD": "{C}", "serD": "", "faultL": "İstek / konu", "faultPh": "Müşterinin planı ve özel istekleri",
              "brandL": "Paket", "typeL": "Kişi sayısı / süre", "typePh": "", "modelL": "Not", "modelPh": "", "serL": "", "serPh": "", "whenL": "Etkinlik zamanı", "whenD": "Etkinlik",
              "addrL": "Mekân / adres", "addrPh": "Etkinliğin yapılacağı yer", "doneL": "Yapılanlar", "donePh": "Neler yapıldı?", "partsL": "Kullanılan ekipman ve malzeme", "partAdd": "+ Ekipman ekle",
              "laborL": "Hizmet bedeli (₺)", "finish": "Tamamla", "fin": "Ödeme alındı olarak işaretle", "again": "Tekrar etkinlik: yeniden ata", "kapTitle": "Etkinliği tamamla"},
        "ek": dict(part="Ekipman", brand="Paket", dev_rep="Etkinlik", smSub="Her müşterinin {c} ve etkinlik geçmişi tek kartta.", repeatNote="Aynı konu birden fazla kez kaydedilmiş.",
                   histH="Etkinlik geçmişi", partsSub="Kullanılan ekipman ve malzemeler kayıt tamamlanınca stoktan düşer, iptalde geri gelir.", brandsT="Paketler",
                   teklifSub="Müşteriye hizmet bedelini tek tutar olarak verin; onaylanınca kayda çevirin.", teklifDev="{C} / istek", teklifPart="Kalem", teklifFault="İstek:",
                   fisT="{I} makbuzu", fisFault="İstek", fisDone="Yapılanlar", rDev="Etkinlik bazında", rDevC="Etkinlik", navAt="Etkinlik"),
        "hide": ["satolye", "skonum"],
    },
    # çekici, nakliye, kurye, transfer, araç kiralama: yola çıkılır, taşınır, teslim edilir
    "yol": {
        "ad": "{I}", "ads": "{IP}", "sub": "Çağrıdan teslime kadar her {i} burada: kim, nereden nereye, hangi {k}, ne kadar.",
        "st": _st(yeni=("Talep alındı", "y"), yolda=("Yolda", "b"), basladi=("Taşımada", "b"), tamamlandi=("Teslim edildi", "g"), faturalandi=("Faturalandı", "g")),
        "next": {"atandi": [["yolda", "Yola çıktı"], ["basladi", "Taşımaya başla"]], "yolda": [["basladi", "Taşımaya başla"]]},
        "steps": STEPS6, "ws": False,
        "L": {"dev": "{C} ve güzergâh", "arama": "Numara, müşteri, telefon, adres veya {c} ara", "devD": "{C}", "serD": "", "faultL": "İş / güzergâh", "faultPh": "Nereden nereye, ne taşınacak",
              "brandL": "Hizmet türü", "typeL": "{C} türü", "typePh": "", "modelL": "Not", "modelPh": "", "serL": "", "serPh": "", "whenL": "Planlanan zaman", "whenD": "Planlanan",
              "addrL": "Alım adresi", "addrPh": "Mahalle, sokak, kapı no, ilçe", "doneL": "Yapılan iş", "donePh": "Teslim bilgisi, notlar", "partsL": "Ek masraflar", "partAdd": "+ Masraf ekle",
              "laborL": "Hizmet bedeli (₺)", "finish": "Teslim edildi", "fin": "Faturalandı olarak işaretle", "again": "Tekrar iş: yeniden ata", "kapTitle": "İşi tamamla"},
        "ek": dict(part="Masraf", brand="Hizmet türü", dev_rep="{C} türü", partsSub="Kullanılan malzemeler kayıt tamamlanınca stoktan düşer, iptalde geri gelir.",
                   teklifSub="Müşteriye hizmet bedelini tek tutar olarak verin; onaylanınca kayda çevirin.", teklifDev="{C} / güzergâh", teklifPart="Kalem", teklifFault="İş:",
                   fisT="{I} fişi", fisFault="İş", fisPart="Masraf", navAt="Teslim"),
        "hide": ["satolye"],
    },
    # emlak: talep, gösterim, görüşme, komisyon
    "emlak": {
        "ad": "{I}", "ads": "{IP}", "sub": "Talepten sonuca kadar her {i} burada: kim, hangi {c}, hangi {k}, ne kadar.",
        "st": _st(yeni=("Talep alındı", "y"), yolda=("Gösterimde", "b"), basladi=("Görüşmede", "b"), tamamlandi=("Sonuçlandı", "g"), faturalandi=("Komisyon alındı", "g")),
        "next": {"atandi": [["yolda", "Gösterime çıktı"], ["basladi", "Görüşmeye başla"]], "yolda": [["basladi", "Görüşmeye başla"]]},
        "steps": STEPS6, "ws": False,
        "L": {"dev": "{C} ve talep", "arama": "Numara, müşteri, telefon, {c} veya konu ara", "devD": "{C}", "serD": "", "faultL": "Talep / konu", "faultPh": "Örn. 3+1 kiralık daire, Kadıköy",
              "brandL": "Talep türü", "typeL": "Konut / iş yeri", "typePh": "Örn. Daire, dükkân", "modelL": "Bütçe / not", "modelPh": "", "serL": "", "serPh": "", "whenL": "Gösterim zamanı", "whenD": "Gösterim",
              "addrL": "Adres", "addrPh": "İlan adresi", "doneL": "Sonuç", "donePh": "Görüşme sonucu, notlar", "partsL": "Masraflar", "partAdd": "+ Masraf ekle", "laborL": "Komisyon (₺)",
              "finish": "Sonuçlandır", "fin": "Komisyon alındı olarak işaretle", "again": "Tekrar görüşme: yeniden ata", "kapTitle": "Talebi sonuçlandır"},
        "ek": dict(part="Masraf", brand="Talep türü", dev_rep="İlan türü", smSub="Her müşterinin talepleri ve görüşme geçmişi tek kartta.", repeatNote="Aynı talep birden fazla kez kaydedilmiş.",
                   histH="Görüşme geçmişi", partsSub="Kullanılan malzemeler kayıt tamamlanınca stoktan düşer, iptalde geri gelir.", brandsT="Talep türleri",
                   teklifSub="Müşteriye komisyon ve hizmet bedelini tek tutar olarak verin; onaylanınca kayda çevirin.", teklifDev="{C} / talep", teklifPart="Kalem", teklifFault="Talep:",
                   fisT="{I} makbuzu", fisFault="Talep", fisPart="Masraf", rDev="İlan türü bazında", rDevC="İlan türü", navAt="Portföy"),
        "hide": ["satolye"],
    },
}

# sektöre özgü ince ayarlar (iş akışı türünün üstüne biner)
OVR = {
    "cilingir": {"st": {"yeni": ["Çağrı alındı", "y"], "yolda": ["Çilingir yolda", "b"], "basladi": ["Kapıda, işlemde", "b"]}, "L": {"faultL": "Sorun / yapılacak iş", "faultPh": "Örn. Kapıda kaldım, kilit değişimi", "serL": "", "serD": "", "brandL": "Kilit türü", "typeL": "Kapı türü", "typePh": "Örn. çelik kapı, araç"}},
    "gunes_enerjisi": {"L": {"serD": "Sistem seri no", "serL": "Sistem seri no"}, "st": {"basladi": ["Montajda", "b"]}, "next": {"atandi": [["yolda", "Sahaya çıktı"], ["basladi", "Montaja başla"]], "yolda": [["basladi", "Montaja başla"]]}},
    "asansor": {"L": {"serD": "Asansör no", "serL": "Asansör no / etiket"}},
    "su_aritma": {"L": {"serD": "Cihaz seri no", "serL": "Cihaz seri no"}},
    "jenerator": {"L": {"serD": "Jeneratör seri no", "serL": "Jeneratör seri no"}},
    "yazici_servis": {"L": {"serD": "Yazıcı seri no", "serL": "Yazıcı seri no"}},
    "telefon_tamir": {"L": {"brandL": "Marka", "modelL": "Model", "modelPh": "Örn. iPhone 13", "serL": "IMEI / seri no", "serD": "IMEI", "typeL": "Cihaz türü", "typePh": "Örn. telefon, tablet",
                           "faultPh": "Örn. Ekran kırık, şarj almıyor", "brandL2": "Marka"}, "ek": {"brand": "Marka", "part": "Parça", "dev_rep": "Cihaz türü"}},
    "ayakkabi_tamir": {"L": {"brandL": "İşlem türü", "faultPh": "Örn. Taban yapıştırma, topuk değişimi", "modelL": "Ayrıntı", "modelPh": "Renk, numara"}},
    "terzi": {"st": {"yeni": ["Sipariş alındı", "y"], "basladi": ["Dikimde", "b"], "tamamlandi": ["Prova / teslime hazır", "g"]}, "L": {"faultL": "Yapılacak işlem", "faultPh": "Örn. Paça kısaltma, bel daraltma, elbise dikimi",
                                                                                                                              "brandL": "İşlem türü", "modelL": "Ölçü / not", "modelPh": "Ölçüler, kumaş, renk", "serD": "Sipariş no", "serL": "Sipariş no"}},
    "kuru_temizleme": {"L": {"brandL": "İşlem türü", "faultPh": "Örn. Takım elbise kuru temizleme, leke çıkarma", "modelL": "Ayrıntı", "modelPh": "Renk, leke yeri"},
                       "st": {"basladi": ["Temizlemede", "b"]}, "next": {"atandi": [["yolda", "Teslim aldım"], ["basladi", "Temizlemeye başla"]], "yolda": [["basladi", "Temizlemeye başla"]]}},
    "hali_yikama": {"L": {"brandL": "Yıkama türü", "faultPh": "Örn. 2 adet 4x6 halı, leke var", "modelL": "Ölçü", "modelPh": "Örn. 200x300 cm", "typeL": "Halı türü", "typePh": "Örn. makine, yün, ipek", "serD": "Etiket no"},
                    "st": {"yolda": ["Halı teslim alındı", "b"], "basladi": ["Yıkamada", "b"]}, "next": {"atandi": [["yolda", "Halıyı teslim aldım"], ["basladi", "Yıkamaya başla"]], "yolda": [["basladi", "Yıkamaya başla"]]}},
    "lastikci": {"L": {"faultPh": "Örn. 4 lastik değişimi, balans, rot ayarı", "brandL": "Lastik markası", "modelL": "Lastik ebadı", "modelPh": "Örn. 205/55 R16"}},
    "oto_servis": {"L": {"faultPh": "Örn. Periyodik bakım, fren sesi, motor arızası"}},
    "temizlik": {"L": {"faultPh": "Örn. Taşınma sonrası temizlik, ofis temizliği", "brandL": "Temizlik türü", "typePh": "Örn. 3+1 daire, 120 m²"}, "st": {"basladi": ["Temizlikte", "b"], "yolda": ["Ekip yolda", "b"]},
                "next": {"atandi": [["yolda", "Ekip yola çıktı"], ["basladi", "Temizliğe başla"]], "yolda": [["basladi", "Temizliğe başla"]]}},
    "bocek_ilaclama": {"L": {"faultPh": "Örn. Hamam böceği, fare, bahçe ilaçlama", "brandL": "İlaçlama türü", "typeL": "Alan", "typePh": "Örn. 2+1 daire, bahçe"},
                       "st": {"basladi": ["İlaçlamada", "b"]}, "next": {"atandi": [["yolda", "Yola çıktı"], ["basladi", "İlaçlamaya başla"]], "yolda": [["basladi", "İlaçlamaya başla"]]}},
    "havuz_bakim": {"L": {"faultPh": "Örn. Haftalık bakım, su bulanık, pompa sesi", "brandL": "Bakım türü", "typeL": "Havuz boyutu", "typePh": "Örn. 8x4 m"}, "st": {"basladi": ["Bakımda", "b"]},
                    "next": {"atandi": [["yolda", "Yola çıktı"], ["basladi", "Bakıma başla"]], "yolda": [["basladi", "Bakıma başla"]]}},
    "peyzaj": {"L": {"faultPh": "Örn. Bahçe düzenleme, çim ekimi, sulama sistemi", "brandL": "İş türü", "typeL": "Alan", "typePh": "Örn. 300 m² bahçe"}, "st": {"yolda": ["Keşfe çıkıldı", "b"], "basladi": ["Uygulamada", "b"]},
               "next": {"atandi": [["yolda", "Keşfe çıktı"], ["basladi", "Uygulamaya başla"]], "yolda": [["basladi", "Uygulamaya başla"]]}},
    "tadilat": {"L": {"faultPh": "Örn. Banyo yenileme, boya badana, mutfak", "brandL": "İş türü", "typeL": "Alan", "typePh": "Örn. 90 m² daire"}, "st": {"yolda": ["Keşfe çıkıldı", "b"], "basladi": ["Şantiyede", "b"]},
                "next": {"atandi": [["yolda", "Keşfe çıktı"], ["basladi", "Çalışmaya başla"]], "yolda": [["basladi", "Çalışmaya başla"]]}},
    "cam_dograma": {"L": {"faultPh": "Örn. PVC pencere değişimi, cam balkon", "brandL": "Ürün türü", "typeL": "Ölçü", "typePh": "Örn. 5 pencere, 1 kapı"}, "st": {"yolda": ["Ölçüye çıkıldı", "b"], "basladi": ["Montajda", "b"]},
                    "next": {"atandi": [["yolda", "Ölçüye çıktı"], ["basladi", "Montaja başla"]], "yolda": [["basladi", "Montaja başla"]]}},
    "surucu_kursu": {"L": {"brandL": "Ehliyet sınıfı", "faultPh": "Örn. B sınıfı ehliyet, direksiyon dersi", "typeL": "Grup / dönem", "typePh": "Örn. Hafta sonu grubu", "modelL": "Direksiyon aracı"}},
    "src_kursu": {"L": {"brandL": "SRC belgesi", "faultPh": "Örn. SRC 1, SRC 2", "typeL": "Grup / dönem"}},
    "etut_merkezi": {"L": {"brandL": "Ders", "typeL": "Sınıf / grup", "typePh": "Örn. 8. sınıf, LGS grubu", "modelL": "Okul / not"}},
    "dil_okulu": {"L": {"brandL": "Dil ve seviye", "typePh": "Örn. İngilizce B1, akşam grubu"}},
    "muzik_kursu": {"L": {"brandL": "Enstrüman", "typePh": "Örn. Gitar, bireysel ders", "modelL": "Seviye"}},
    "anaokulu": {"L": {"brandL": "Sınıf", "typeL": "Yaş grubu", "typePh": "Örn. 4 yaş", "faultL": "Veli notu", "faultPh": "Alerji, özel durum, servis ihtiyacı", "addrL": "Veli adresi"}},
    "ozel_ders": {"L": {"brandL": "Ders", "typeL": "Sınıf / seviye", "typePh": "Örn. 9. sınıf matematik", "whenL": "Ders zamanı"}},
    "bilgisayar_kursu": {"L": {"brandL": "Kurs", "typePh": "Örn. Ofis programları, hafta içi grubu"}},
    "avukat": {"L": {"brandL": "Dosya türü", "typeL": "Mahkeme / kurum", "modelL": "Dosya no", "faultPh": "Örn. İş davası, boşanma, icra takibi"}, "st": {"basladi": ["Dosya üzerinde çalışılıyor", "b"], "faturalandi": ["Vekâlet ücreti alındı", "g"]}},
    "muhasebe": {"L": {"brandL": "Hizmet türü", "typeL": "Dönem", "typePh": "Örn. Mart 2026 beyannamesi", "faultPh": "Örn. KDV beyannamesi, işe giriş bildirgesi"}, "st": {"basladi": ["İşlemde", "b"]}},
    "tercume": {"L": {"brandL": "Dil çifti", "typeL": "Belge türü", "typePh": "Örn. Diploma, sözleşme", "modelL": "Sayfa / kelime sayısı", "faultPh": "Örn. Yeminli tercüme, noter onaylı"}, "st": {"basladi": ["Çeviride", "b"], "tamamlandi": ["Teslime hazır", "g"]}},
    "mimar": {"L": {"brandL": "Proje türü", "typeL": "Alan", "typePh": "Örn. 180 m² villa", "faultPh": "Örn. Ruhsat projesi, iç mimari, tadilat projesi"}, "st": {"basladi": ["Projelendirmede", "b"]}},
    "dugun_salonu": {"L": {"brandL": "Organizasyon türü", "typeL": "Davetli sayısı", "typePh": "Örn. 250 kişi", "addrL": "Salon / adres", "whenL": "Organizasyon zamanı", "whenD": "Organizasyon"}, "st": {"basladi": ["Organizasyonda", "b"]}},
    "dj_muzik": {"L": {"brandL": "Hizmet paketi", "typeL": "Süre", "typePh": "Örn. 5 saat", "faultPh": "Örn. Düğün, nişan, kurumsal etkinlik"}},
    "fotografci": {"L": {"brandL": "Çekim türü", "typeL": "Süre / paket", "typePh": "Örn. Dış çekim, 3 saat", "addrL": "Çekim yeri", "whenL": "Çekim zamanı", "whenD": "Çekim", "doneL": "Çekilenler ve teslim", "donePh": "Çekim özeti, teslim edilen albüm"},
                  "st": {"basladi": ["Çekimde", "b"], "tamamlandi": ["Teslime hazır", "g"]}, "next": {"atandi": [["basladi", "Çekime başla"]]}},
    "tur_organizasyon": {"L": {"brandL": "Tur", "typeL": "Kişi sayısı", "typePh": "Örn. 12 kişi", "addrL": "Buluşma noktası", "whenL": "Tur zamanı", "whenD": "Tur"}, "st": {"basladi": ["Turda", "b"]}, "next": {"atandi": [["basladi", "Tura başla"]]}},
    "oto_cekici": {"L": {"faultL": "Arıza / güzergâh", "faultPh": "Araç nerede, nereye çekilecek", "brandL": "Araç markası", "typeL": "Araç tipi", "serL": "Plaka", "serD": "Plaka", "serial": True, "serPh": "06 ABC 123", "addrL": "Araç konumu"},
                   "st": {"basladi": ["Araç yüklendi", "b"], "tamamlandi": ["Teslim edildi", "g"]}, "next": {"atandi": [["yolda", "Yola çıktı"], ["basladi", "Aracı yükledim"]], "yolda": [["basladi", "Aracı yükledim"]]}},
    "nakliye": {"L": {"brandL": "Taşıma türü", "typeL": "Eşya / oda sayısı", "typePh": "Örn. 3+1 ev eşyası", "faultPh": "Örn. Evden eve nakliyat, asansörlü", "addrL": "Yükleme adresi", "modelL": "Boşaltma adresi", "modelPh": "Varılacak adres"},
                 "st": {"basladi": ["Yüklemede", "b"], "tamamlandi": ["Teslim edildi", "g"]}, "next": {"atandi": [["yolda", "Yola çıktı"], ["basladi", "Yüklemeye başla"]], "yolda": [["basladi", "Yüklemeye başla"]]}},
    "kurye": {"L": {"brandL": "Teslimat türü", "typeL": "Paket türü", "faultPh": "Nereden nereye, paket bilgisi", "addrL": "Alım adresi", "modelL": "Teslim adresi", "modelPh": "Varılacak adres"},
              "st": {"yolda": ["Paket alındı", "b"], "basladi": ["Teslimata çıktı", "b"], "tamamlandi": ["Teslim edildi", "g"]},
              "next": {"atandi": [["yolda", "Paketi aldım"], ["basladi", "Teslimata çık"]], "yolda": [["basladi", "Teslimata çık"]]}},
    "transfer": {"L": {"brandL": "Transfer türü", "typeL": "Yolcu sayısı", "typePh": "Örn. 4 kişi", "faultL": "Güzergâh", "faultPh": "Nereden nereye, uçuş saati", "addrL": "Alış noktası", "modelL": "Varış noktası", "modelPh": "Varılacak yer"},
                 "st": {"yolda": ["Yolcuya gidiyor", "b"], "basladi": ["Transferde", "b"], "tamamlandi": ["Tamamlandı", "g"]}, "next": {"atandi": [["yolda", "Yola çıktı"], ["basladi", "Transfere başla"]], "yolda": [["basladi", "Transfere başla"]]}},
    "arac_kiralama": {"L": {"brandL": "Araç sınıfı", "typeL": "Kiralama süresi", "typePh": "Örn. 3 gün", "faultL": "Kiralama notu", "faultPh": "Teslim yeri, ek sürücü, sigorta", "whenL": "Teslim zamanı", "whenD": "Teslim"},
                      "st": {"yolda": ["Araç hazır", "b"], "basladi": ["Kirada", "b"], "tamamlandi": ["İade alındı", "g"]}, "next": {"atandi": [["yolda", "Araç hazır"], ["basladi", "Aracı teslim ettim"]], "yolda": [["basladi", "Aracı teslim ettim"]]}},
    "emlakci": {},
}

# yeni kayıt formunda gösterilecek alanları belirleyen ek bayraklar: serial (plaka/seri alanı), ws (atölyeye al düğmesi)


def build(key):
    """Sektör için servis ekranı dili; teknik servis ve bu akışa girmeyen sektörlerde None."""
    if not key or key not in SD.ROWS or key in SD.SADE:
        return None
    arch = ARCH_OF.get(key)
    if not arch or SD.FAMILY.get(key, "") in ("randevu", "siparis"):
        return None
    a = ARCH[arch]
    o = OVR.get(key, {})
    p = _terms(key)
    st = {k: list(v) for k, v in a["st"].items()}
    for k, v in (o.get("st") or {}).items():
        st[k] = list(v)
    nxt = o.get("next") or a["next"]
    L = dict(a["L"])
    L.update(o.get("L") or {})
    L.pop("brandL2", None)
    ek = dict(a["ek"])
    ek.update(o.get("ek") or {})
    ekd = _ek(**ek)
    # sektöre uymayan menü: atölye ekranı yalnız cihaz teslim alınan işlerde anlamlı; aksi halde gizlenir
    hide = list(a.get("hide") or [])
    out = {
        "arch": arch, "ad": a["ad"], "ads": a["ads"], "sub": a["sub"], "st": st, "next": nxt, "steps": list(a["steps"]),
        "pkg": bool(a.get("pkg")), "ws": bool(a.get("ws")), "L": dict(L, **ekd), "hide": hide,
    }
    out = _fmt(out, p)
    out["st"] = {k: v for k, v in out["st"].items()}
    # kelime düzeyi sözlük: panelde sabit yazılı kalmış cihaz / arıza / usta kelimeleri sektörün terimine döner
    lx = []
    if p["C"] != "Cihaz":
        lx.append(["cihaz", p["C"], p["CP"], True])
    if p["S"] != "Arıza":
        lx.append(["arıza", p["S"], p["S"], True])
    if p["K"] not in ("Usta", "Teknisyen"):
        lx.append(["usta", p["K"], p["KP"], True])
        lx.append(["teknisyen", p["K"], p["KP"], True])
    out["lx"] = lx
    return out
