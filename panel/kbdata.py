# -*- coding: utf-8 -*-
"""Arıza Asistanı bilgi tabanı: site arıza kodu sayfalarından derlenen 589 kod + yaygın belirtiler."""
import json, os, re

BRANDS = {"demirdokum": "Demirdöküm", "arcelik": "Arçelik", "bulasik": "Bulaşık", "ugur": "Uğur", "mitsubishi-electric": "Mitsubishi Electric",
          "mitsubishi-heavy": "Mitsubishi Heavy", "hi-level": "Hi-Level", "rota-klima": "Rota", "fujiplus": "Fujiplus", "lg": "LG", "jvc": "JVC",
          "tcl": "TCL", "eca": "ECA", "awox": "Awox", "bosch": "Bosch"}

PARTS = [("ntc", "NTC sıcaklık sensörü"), ("sensör", "Sıcaklık/basınç sensörü"), ("fan", "Fan motoru"), ("elektrot", "Ateşleme/iyonizasyon elektrodu"),
         ("pompa", "Sirkülasyon pompası"), ("eşanjör", "Eşanjör"), ("gaz valf", "Gaz valfi"), ("kart", "Elektronik kart"), ("basınç", "Basınç şalteri/manometre"),
         ("kompresör", "Kompresör"), ("kapasitör", "Kapasitör"), ("drenaj", "Drenaj pompası/hortumu"), ("termostat", "Termostat"), ("vana", "Üç yollu vana"),
         ("baca", "Baca/atık gaz sensörü"), ("backlight", "Arka ışık (LED bar)"), ("power", "Güç kartı"), ("main", "Ana kart"), ("t-con", "T-Con kartı"), ("panel", "Panel")]


def _pretty(b):
    return BRANDS.get(b) or " ".join(w.capitalize() for w in b.split("-"))


def _steps(fix):
    s = [x.strip() for x in re.split(r"(?<=[.])\s+", fix or "") if len(x.strip()) > 3]
    return s[:8] or ["Cihaz modeli ve ekrandaki tam kodla servis kaydı açın"]


_MIN = {"kombi": 60, "klima": 75, "şofben": 45, "televizyon": 60}


def code_entries():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kb_codes.json")
    try:
        rows = json.load(open(p, encoding="utf8"))
    except Exception:
        return []
    out = []
    for r in rows:
        code, t = r["c"].strip(), r["t"].strip()
        low = (t + " " + r["m"] + " " + r["f"]).lower()
        parts = []
        for k, v in PARTS:
            if k in low and v not in parts:
                parts.append(v)
        brand = _pretty(r["b"]) if r["b"] else ""
        sym = code.lower() == "belirti"
        if sym:
            out.append({"device_type": r["d"], "brand": brand, "code": "", "title": t, "causes": [x for x in [r["m"]] if x], "parts": [k for _, k in PARTS if _[:5] in low][:4],
                        "est_minutes": _MIN.get(r["d"], 60), "steps": _steps(r["f"]), "keywords": f"{brand} {r['d']} belirti {t}".lower(), "price_min": 0, "price_max": 0,
                        "notes": "Kaynak: servisplus.net.tr arıza rehberi (belirti). Fiyat alanını kendi tarifenize göre doldurun.", "is_active": True, "source": "belirti-rehberi"})
            continue
        out.append({"device_type": r["d"], "brand": brand, "code": code, "title": f"{code} — {t}" if t else code,
                    "causes": [x for x in [r["m"]] if x], "parts": parts[:5], "est_minutes": _MIN.get(r["d"], 60), "steps": _steps(r["f"]),
                    "keywords": f"{brand} {r['d']} {code} arıza kodu hata kodu {t}".lower(), "price_min": 0, "price_max": 0,
                    "notes": "Kaynak: servisplus.net.tr arıza kodu rehberi. Model/yazılıma göre değişebilir; fiyat alanını kendi tarifenize göre doldurun.", "is_active": True, "source": "kod-rehberi"})
    return out


def _h(dt, title, causes, parts, minutes, steps, kw=""):
    return {"device_type": dt, "brand": "", "code": "", "title": title, "causes": causes, "parts": parts, "est_minutes": minutes, "steps": steps,
            "keywords": kw, "price_min": 0, "price_max": 0, "notes": "Yaygın belirti rehberi — fiyat alanını kendi tarifenize göre düzenleyin.", "is_active": True, "source": "belirti-rehberi"}


HAND = [
    # ---- kombi
    _h("kombi", "Kombi su akıtıyor / damlatıyor", ["Emniyet ventili damlatıyor", "Genleşme tankı hava kaybı", "Bağlantı conta/o-ring kaçağı", "Eşanjör/ısıtma devresi sızıntısı", "Basınç fazla yükselmiş"],
       ["Emniyet ventili", "Conta/o-ring seti", "Genleşme tankı", "Eşanjör"], 60, ["Su damlasının geldiği noktayı kuru bezle tespit edin", "Soğukken basıncı 1-1,5 bara ayarlayın", "Emniyet ventili çıkışını ve contaları kontrol edin", "Genleşme tankı hava basıncını ölçün"], "su akıtıyor damlatıyor sızıntı kaçak su yapıyor"),
    _h("kombi", "Kombi sürekli açılıp kapanıyor (kısa çevrim)", ["Oda termostatı/oda sensörü", "Pompa debisi düşük, filtre tıkalı", "Gaz ayarı/modülasyon", "Baca geri tepmesi", "Kireçlenmiş eşanjör"],
       ["Oda termostatı", "Sirkülasyon pompası", "NTC sensör"], 60, ["Termostat ayarını ve pil/bağlantısını kontrol edin", "Tesisat filtresini temizleyin", "Pompa hızını ve sistem havasını kontrol edin", "Gaz ayarı ve baca durumunu inceleyin"], "açılıp kapanıyor sürekli kapanıyor kısa çevrim stop ediyor devreye giriyor"),
    _h("kombi", "Kombi ses yapıyor (gurultu, tıkırtı, kaynama sesi)", ["Sistemde hava", "Kireçli eşanjör (kaynama sesi)", "Pompa yatak/rotor sorunu", "Fan balansı bozuk", "Tesisat debisi düşük"],
       ["Sirkülasyon pompası", "Fan", "Eşanjör"], 60, ["Hava alın, basıncı kontrol edin", "Pompa hız kademesini ve miline dönüşünü inceleyin", "Eşanjör kireç temizliği yapın", "Fan ve baca bağlantısını kontrol edin"], "ses gürültü uğultu tıkırtı vızıltı kaynama sesi"),
    _h("kombi", "Kombi elektrik gelmiyor / ekran kapalı", ["Fiş/sigorta/priz sorunu", "Elektronik kart sigortası", "Ana kart arızası", "Ekran/panel bağlantısı"],
       ["Kart sigortası", "Elektronik kart", "Ekran kartı"], 45, ["Priz ve fişi başka cihazla test edin", "Kart sigortasını ve besleme gerilimini ölçün", "Kart ve ekran bağlantı kablolarını kontrol edin"], "açılmıyor ekran gelmiyor ölü elektrik yok"),
    _h("kombi", "Kombi kalorifer sıcak ama kullanım suyu soğuk (ya da tersi)", ["Üç yollu vana motoru/mekaniği", "Kullanım suyu NTC sensörü", "Plakalı eşanjör tıkalı", "Akış sensörü"],
       ["Üç yollu vana", "NTC sensör", "Plakalı eşanjör", "Akış sensörü"], 75, ["Vana motorunun hareketini gözlemleyin", "NTC direncini ölçün", "Plakalı eşanjörü kireç açısından kontrol edin"], "sıcak su soğuk kalorifer çalışıyor sıcak su yok ılık"),
    _h("kombi", "Kombi kilitleniyor (reset gerektiriyor)", ["Alev algılanmıyor", "Gaz kesintisi", "Aşırı ısınma limit termostat", "Baca/fan sorunu"], ["İyonizasyon elektrodu", "Gaz valfi", "Limit termostat"], 60, ["Gaz vanası ve gaz beslemesini kontrol edin", "Resetleyip hata kodunu not edin", "Elektrot ve fan testini yapın"], "kilitleniyor reset istiyor hata veriyor"),
    _h("kombi", "Kombi gaz kokusu / baca gazı şüphesi", ["Gaz bağlantı kaçağı", "Baca tıkanıklığı", "Yanma sorunu"], ["Gaz bağlantı contası", "Baca"], 60, ["ÖNCE gaz vanasını kapatın, ortamı havalandırın, elektrik anahtarına dokunmayın", "Dışarıdan gaz dağıtım şirketini arayın", "Kaçak giderilmeden cihazı çalıştırmayın"], "gaz kokusu karbonmonoksit baca gazı koku"),
    # ---- klima
    _h("klima", "Klima ısıtmıyor", ["4 yollu vana arızası", "Gaz eksik", "Dış ünite buzlanma / defrost sensörü", "Kompresör sorunu", "Mod/uzaktan kumanda ayarı"], ["4 yollu vana", "Defrost sensörü", "Gaz tamamlama", "Kompresör"], 75, ["Isıtma modunu ve ayar sıcaklığını doğrulayın", "4 yollu vana bobinini ve gaz basıncını ölçün", "Dış ünite buzlanmasını kontrol edin"], "ısıtmıyor ısıtma yok sıcak üflemiyor"),
    _h("klima", "Klima dış ünite çalışmıyor / iç ünite çalışıyor", ["Kapasitör", "Kompresör kontaktör/ röle", "Dış ünite kartı", "Haberleşme kablosu"], ["Kapasitör", "Dış ünite kartı", "Kompresör"], 75, ["Dış ünite beslemesini ve haberleşmeyi ölçün", "Kapasitörü test edin", "Kompresör sargı dirençlerini ölçün"], "dış ünite çalışmıyor kompresör çalışmıyor"),
    _h("klima", "Klima kötü kokuyor", ["Evaporatör ve filtre bakterisi/küf", "Drenaj suyu birikmesi"], ["Filtre"], 60, ["Filtreyi yıkayın", "Evaporatör ve fan kafesini kimyasalla temizleyin", "Drenaj hattını açın"], "koku kokuyor küf rutubet"),
    _h("klima", "Klima ses yapıyor / titreşim", ["Fan kanadı/ rulman", "Dış ünite montaj gevşekliği", "Kompresör"], ["Fan motoru", "Montaj lastiği"], 45, ["Montaj ayaklarını ve vidaları sıkın", "Fan kanadı ve rulmanı kontrol edin"], "ses gürültü titreşim vızıltı"),
    _h("klima", "Klima uzaktan kumandaya cevap vermiyor / ekran kapalı", ["Kumanda pili", "IR alıcı", "İç ünite kartı"], ["Kumanda", "İç ünite alıcı", "İç ünite kartı"], 30, ["Kumanda pilini değiştirin", "Cihaz üstü acil çalıştırma tuşunu deneyin", "Besleme ve kartı kontrol edin"], "kumanda çalışmıyor açılmıyor ekran"),
    _h("klima", "Klima buz tutuyor", ["Gaz eksikliği", "Filtre/evaporatör kirli", "İç ünite fanı zayıf"], ["Gaz tamamlama", "Fan motoru"], 60, ["Cihazı kapatıp buzu çözün", "Filtre ve evaporatörü temizleyin", "Gaz basıncını ölçün"], "buz tutuyor buzlanma donuyor"),
    # ---- buzdolabı
    _h("buzdolabı", "Buzdolabı soğutmuyor", ["Kompresör/ röle-termik arızası", "Gaz kaçağı", "Defrost (buz çözme) sistemi arızası", "Fan motoru", "Termostat/sensör kartı"], ["Kompresör rölesi", "Defrost ısıtıcı/ termik", "Evaporatör fanı", "Termostat", "Elektronik kart"], 75, ["Kompresörün çalışıp çalışmadığını dinleyin", "Evaporatörde buzlanma var mı bakın", "Fan, defrost ısıtıcı ve termiği ölçün", "Termostat/sensör ve kartı test edin"], "soğutmuyor soğutmuyor ısınıyor ılık"),
    _h("buzdolabı", "Buzdolabı buzluk çalışıyor, alt bölüm soğutmuyor", ["Evaporatör fanı", "Defrost arızası (buzlanma hava kanalını tıkıyor)", "Damper/ hava kapağı", "Sensör"], ["Evaporatör fanı", "Defrost ısıtıcı", "Damper"], 75, ["Arka paneli açıp buzlanmayı kontrol edin", "Fan motoru ve damperi test edin", "Defrost elemanlarını ölçün"], "buzluk soğuk dolap ılık alt bölüm soğutmuyor"),
    _h("buzdolabı", "Buzdolabı su akıtıyor", ["Defrost tahliye hortumu tıkalı", "Buz birikmesi", "Kapak contası", "Su bağlantısı (dispenser)"], ["Tahliye hortumu", "Kapı contası", "Su filtresi/valfi"], 45, ["Tahliye deliğini ve hortumu açın", "Kapak contasını kontrol edin", "Su girişi bağlantılarına bakın"], "su akıtıyor su birikiyor sızıntı"),
    _h("buzdolabı", "Buzdolabı sürekli çalışıyor / durmuyor", ["Kapak contası kaçırıyor", "Kirli kondenser", "Termostat/sensör", "Gaz eksik"], ["Kapı contası", "Termostat", "Sensör"], 45, ["Kapı contasını kağıt testiyle kontrol edin", "Kondenseri temizleyin", "Sıcaklık sensörü ve termostatı ölçün"], "sürekli çalışıyor durmuyor kompresör durmuyor"),
    _h("buzdolabı", "Buzdolabı ses yapıyor", ["Fan kanadı buza sürtüyor", "Kompresör yatakları", "Montaj/ayak dengesi"], ["Fan motoru", "Kompresör takozu"], 45, ["Buzlanmayı giderin", "Ayakları ve boruların temasını kontrol edin", "Fan motorunu test edin"], "ses gürültü vızıltı tıkırtı"),
    _h("buzdolabı", "Buzdolabı alarm veriyor / kapı açık uyarısı", ["Kapı sensörü", "Sıcaklık yükselmesi", "Kapak contası"], ["Kapı sensörü", "Kapı contası"], 30, ["Kapının tam kapandığını doğrulayın", "Sensör ve alarm susturma ayarını kontrol edin"], "alarm ötüyor uyarı bip"),
    # ---- çamaşır makinesi
    _h("çamaşır makinesi", "Çamaşır makinesi sıkmıyor", ["Kayış/motor kömürü (kollektörlü motor)", "Boşaltma pompası tıkalı", "Dengesiz yük", "Kapak kilidi", "Motor sürücü kartı"], ["Motor kömürü", "Motor kayışı", "Su tahliye pompası", "Elektronik kart"], 60, ["Pompa filtresini temizleyin", "Yükü dengeleyin", "Kömür ve kayış durumunu kontrol edin", "Kartı ve kapak kilidini test edin"], "sıkmıyor sıkma yapmıyor sıkma devri"),
    _h("çamaşır makinesi", "Çamaşır makinesi su almıyor", ["Musluk kapalı/ filtre tıkalı", "Su giriş valfi", "Basınç şalteri", "Kapak kilidi"], ["Su giriş valfi", "Basınç şalteri (prosestat)", "Giriş filtresi"], 45, ["Musluk ve giriş filtresini kontrol edin", "Valf bobinini ölçün", "Basınç şalterini test edin"], "su almıyor su gelmiyor su alamıyor"),
    _h("çamaşır makinesi", "Çamaşır makinesi su boşaltmıyor", ["Pompa filtresi tıkalı", "Tahliye pompası arızası", "Tahliye hortumu bükülmüş", "Kart"], ["Tahliye pompası", "Hortum"], 45, ["Pompa filtresini temizleyin", "Pompanın dönüşünü kontrol edin", "Hortum yolunu açın"], "su boşaltmıyor su tahliye etmiyor su kalıyor"),
    _h("çamaşır makinesi", "Çamaşır makinesi su sızdırıyor", ["Kapak lastiği", "Pompa filtresi kapağı", "Hortum bağlantısı", "Deterjan çekmecesi taşması", "Küvet/ amortisör"], ["Kapak lastiği", "Hortum", "Pompa"], 45, ["Sızıntı noktasını kuru bezle tespit edin", "Filtre kapağı ve hortum bağlantılarını sıkın", "Lastiği değerlendirin"], "su sızdırıyor akıtıyor su yapıyor"),
    _h("çamaşır makinesi", "Çamaşır makinesi çalışmıyor / program başlamıyor", ["Kapak kilidi", "Elektronik kart", "Program seçici", "Motor"], ["Kapak kilidi", "Elektronik kart", "Program seçici"], 60, ["Kapağın tam kapandığını ve kilit sesini doğrulayın", "Besleme ve kartı kontrol edin", "Kilit rezistansını ölçün"], "çalışmıyor açılmıyor program başlamıyor"),
    _h("çamaşır makinesi", "Çamaşır makinesi çok ses yapıyor / titriyor", ["Amortisörler", "Rulman", "Dengesiz çamaşır", "Nakliye cıvataları"], ["Amortisör", "Rulman seti"], 90, ["Ayakları ve nakliye cıvatalarını kontrol edin", "Amortisörleri değerlendirin", "Rulman boşluğunu kontrol edin"], "ses gürültü titriyor zıplıyor uğultu"),
    _h("çamaşır makinesi", "Çamaşır makinesi kapağı açılmıyor", ["Kapak kilidi", "Su boşalmadı", "Program bitmedi"], ["Kapak kilidi"], 30, ["Suyu boşaltın (pompa filtresi)", "Kilit ısıtıcı elemanı ve mandalı kontrol edin"], "kapak açılmıyor kilitli"),
    # ---- bulaşık makinesi
    _h("bulaşık makinesi", "Bulaşık makinesi yıkamıyor / bulaşıklar kirli kalıyor", ["Sprey kolları tıkalı", "Filtre kirli", "Yıkama pompası", "Su ısıtıcı", "Su sertliği/ tuz eksik"], ["Sprey kolu", "Yıkama pompası", "Isıtıcı"], 45, ["Sprey kolları ve filtreyi temizleyin", "Tuz ve parlatıcıyı kontrol edin", "Pompa basıncını ve ısıtıcıyı test edin"], "yıkamıyor kirli bırakıyor temiz yıkamıyor"),
    _h("bulaşık makinesi", "Bulaşık makinesi su boşaltmıyor", ["Filtre/ tahliye hortumu tıkalı", "Tahliye pompası", "Tek yönlü valf", "Gider bağlantısı"], ["Tahliye pompası", "Hortum"], 45, ["Filtreyi ve sifonu temizleyin", "Pompayı test edin", "Hortum yolunu kontrol edin"], "su boşaltmıyor su kalıyor tahliye"),
    _h("bulaşık makinesi", "Bulaşık makinesi su almıyor / su seviyesi hatası", ["Su giriş valfi", "Su girişi filtresi", "Seviye sensörü (prosestat)", "Musluk"], ["Su giriş valfi", "Basınç şalteri"], 45, ["Musluğu ve giriş filtresini kontrol edin", "Valf ve seviye şalterini test edin"], "su almıyor su gelmiyor"),
    _h("bulaşık makinesi", "Bulaşık makinesi kurutmuyor / ısıtmıyor", ["Isıtıcı rezistans", "NTC sensörü", "Kuruma sistemi/ parlatıcı bitmiş", "Kart"], ["Isıtıcı rezistans", "NTC sensör", "Elektronik kart"], 60, ["Parlatıcı seviyesini kontrol edin", "Rezistansı ve NTC'yi ölçün"], "kurutmuyor ısıtmıyor ıslak kalıyor"),
    _h("bulaşık makinesi", "Bulaşık makinesi su sızdırıyor", ["Kapak contası", "Hortum bağlantıları", "Aşırı köpük", "Pompa contası"], ["Kapak contası", "Hortum", "Pompa contası"], 45, ["Doğru deterjan kullanımını doğrulayın", "Kapak contası ve hortumları kontrol edin"], "su sızdırıyor akıtıyor sızıntı"),
    _h("bulaşık makinesi", "Bulaşık makinesi çalışmıyor / açılmıyor", ["Kapak kilit anahtarı", "Elektronik kart", "Sigorta/ Filtre"], ["Kapak kilidi", "Elektronik kart"], 45, ["Kapağın tam kapandığını doğrulayın", "Kilit mikro anahtarını ve kartı kontrol edin"], "çalışmıyor açılmıyor program başlamıyor"),
    # ---- kurutma makinesi
    _h("kurutma makinesi", "Kurutma makinesi kurutmuyor / geç kurutuyor", ["Havalandırma tıkalı/ filtre kirli", "Rezistans/ ısı pompası", "Kondenser kirli", "NTC/termostat"], ["Rezistans", "Termostat", "NTC sensör"], 60, ["Havalandırma ve filtreyi temizleyin", "Kondenseri yıkayın", "Rezistansı ve termostatları ölçün"], "kurutmuyor geç kurutuyor nemli çıkıyor"),
    _h("kurutma makinesi", "Kurutma makinesi dönmüyor / çalışmıyor", ["Kayış kopmuş", "Motor/ kondansatör", "Kapak anahtarı", "Kart"], ["Kayış", "Motor", "Kapak anahtarı"], 60, ["Kayışı kontrol edin", "Motor ve kapak şalterini test edin"], "dönmüyor çalışmıyor açılmıyor"),
    _h("kurutma makinesi", "Kurutma makinesi su dolu uyarısı veriyor", ["Su haznesi dolu", "Pompa/ hortum tıkalı", "Seviye sensörü"], ["Pompa", "Seviye sensörü"], 30, ["Hazneyi boşaltın", "Pompa ve hortumu temizleyin"], "su dolu uyarısı su haznesi pompa"),
    # ---- fırın
    _h("fırın", "Fırın ısıtmıyor", ["Alt/üst rezistans", "Termostat/sıcaklık sensörü", "Fonksiyon düğmesi/ programlayıcı", "Gaz fırında emniyet ventili/ ocak ateşleme"], ["Rezistans", "Termostat", "Sıcaklık sensörü", "Fonksiyon anahtarı"], 60, ["Rezistansların direncini ölçün", "Termostat ve düğme kontaklarını test edin"], "ısıtmıyor ısınmıyor ısınmıyor ısı yok"),
    _h("fırın", "Fırın aşırı ısınıyor / ayarı tutmuyor", ["Termostat kalibrasyonu", "Sıcaklık sensörü", "Kart"], ["Termostat", "Sıcaklık sensörü"], 45, ["Termometre ile karşılaştırın", "Termostat/sensörü değiştirin"], "fazla ısınıyor yakıyor sıcaklık ayarı"),
    _h("fırın", "Ocak/fırın gaz ateşleme çakmıyor", ["Ateşleme bujisi kirli/ aşınmış", "Ateşleme trafosu/ kondansatör", "Gaz memesi tıkalı", "Termoelemanlı emniyet"], ["Buji", "Ateşleme ünitesi", "Termoelaman"], 45, ["Buji ve meme temizliğini yapın", "Gaz vanasını doğrulayın", "Ateşleme ünitesini test edin"], "çakmıyor ateşleme yok tık tık"),
    _h("fırın", "Fırın lambası yanmıyor / fan çalışmıyor", ["Ampul", "Fan motoru", "Yönlendirme düğmesi"], ["Fırın ampulü", "Fan motoru"], 30, ["Ampulü değiştirin", "Fan motorunu ve düğmeyi test edin"], "lamba yanmıyor fan çalışmıyor"),
    # ---- televizyon
    _h("televizyon", "Televizyon açılmıyor", ["Güç kartı (power board)", "Ana kart (mainboard)", "Standby voltajı yok", "Sigorta/ kondansatörler"], ["Güç kartı", "Ana kart", "Kondansatör seti"], 75, ["Standby LED durumunu gözlemleyin", "Güç kartı çıkış voltajlarını ölçün", "Şişmiş kondansatörleri kontrol edin"], "açılmıyor ölü kırmızı ışık yanıyor standby"),
    _h("televizyon", "Televizyon görüntü yok ses var", ["Arka ışık (LED bar) arızası", "Inverter/ güç kartı", "T-Con kartı", "Ana kart-panel bağlantısı (LVDS)"], ["LED bar", "T-Con kartı", "Güç kartı"], 90, ["El feneri testi: görüntü silik görünüyorsa arka ışığı arızalıdır", "LED bar ve sürücü voltajını ölçün", "LVDS ve T-Con bağlantısını kontrol edin"], "görüntü yok ses var ekran karanlık siyah ekran"),
    _h("televizyon", "Televizyon ekranında çizgi / bozuk görüntü", ["T-Con kartı", "Panel flex kablo", "Panel arızası", "Ana kart"], ["T-Con kartı", "Flex kablo", "Panel"], 90, ["Menüde de çizgi varsa panel/T-Con'dur", "Flex bağlantılarını yeniden oturtun", "Panel onarılabilirliğini değerlendirin"], "çizgi dikey yatay bozuk renk lekeli görüntü"),
    _h("televizyon", "Televizyon kendi kendine kapanıyor / yeniden başlıyor", ["Güç kartı", "Yazılım hatası", "Aşırı ısınma", "Ana kart"], ["Güç kartı", "Ana kart"], 60, ["Yazılımı güncelleyin/ fabrika ayarı", "Kondansatör ve voltajları kontrol edin"], "kapanıyor yeniden başlıyor donuyor açılıp kapanıyor logo"),
    _h("televizyon", "Televizyon WiFi / internet bağlanmıyor", ["Modem/ ağ ayarı", "WiFi modülü", "Yazılım"], ["WiFi modülü"], 30, ["Modemi ve ağ ayarlarını kontrol edin", "Fabrika ayarı/ güncelleme yapın", "Modülü test edin"], "wifi internet bağlanmıyor ağ kablosuz"),
    _h("televizyon", "Televizyon ses yok / kısık", ["Hoparlör", "Ses amfi entegresi", "Ayar/ HDMI-ARC", "Ana kart"], ["Hoparlör", "Ana kart"], 45, ["Ses ayarlarını ve çıkış tipini kontrol edin", "Hoparlör direncini ölçün"], "ses yok kısık cızırtı hoparlör"),
    # ---- şofben / ocak
    _h("şofben", "Şofben ateşlemiyor / yanmıyor", ["Pil bitmiş", "Su akış sensörü", "Ateşleme elektrodu", "Gaz valfi", "Baca/ hava sensörü"], ["Pil", "Ateşleme elektrodu", "Gaz valfi", "Su akış sensörü"], 45, ["Pilleri değiştirin", "Su basıncını ve filtreyi kontrol edin", "Elektrot ve gaz valfini test edin"], "yanmıyor ateşlemiyor çakmıyor tık tık"),
    _h("şofben", "Şofben su ısıtmıyor / ılık veriyor", ["Kireçli eşanjör", "Gaz ayarı", "Su-gaz valfi membranı", "Sıcaklık sensörü"], ["Eşanjör", "Su-gaz valfi", "NTC sensör"], 60, ["Eşanjör kireç temizliği yapın", "Gaz basıncı ve membranı kontrol edin"], "ısıtmıyor ılık su soğuk su"),
    _h("şofben", "Şofben su kaçırıyor", ["Bağlantı contaları", "Eşanjör delinmesi", "Su valfi"], ["Conta seti", "Eşanjör"], 45, ["Kaçak noktasını tespit edin", "Contaları yenileyin", "Eşanjörü değerlendirin"], "su kaçırıyor akıtıyor damlatıyor"),
    # ---- genel
    _h("beyaz eşya", "Cihaza elektrik gelmiyor / sigorta atıyor", ["Priz ve sigorta", "Kaçak akım", "Güç kablosu/ kart", "Rezistans kaçağı"], ["Güç kablosu", "Elektronik kart", "Rezistans"], 45, ["Prizi ve sigortayı başka cihazla test edin", "İzolasyon/ kaçak ölçümü yapın"], "elektrik gelmiyor sigorta atıyor kaçak akım"),
]


def all_entries():
    return code_entries() + HAND
