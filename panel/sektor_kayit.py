# -*- coding: utf-8 -*-
"""Sektöre özel kayıt motoru: her iş kolunun kendi kayıt ekranı, adımları, girişleri ve kapanışı.
Teknik servis sektörleri (kombi, klima...) mevcut servis kaydı ekranını kullanır; diğer sektörler burada tanımlı şablonu kullanır.
API (firma yöneticisi): GET /admin/kayit/schema, GET /admin/kayit, GET|POST|PUT|DELETE /admin/kayit[/id],
POST /admin/kayit/{id}/adim, POST /admin/kayit/{id}/odeme."""
import re
import time
import uuid
from datetime import date, datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.responses import Response

import sektor
import sektor_dil

MAX_ITEMS = 100


def F(k, l, t="text", **kw):
    return dict(k=k, l=l, t=t, **kw)


def S(*pairs):
    return [{"k": a, "l": b} for a, b in pairs]


# ------------------------------------------------------------------ aile şablonları
# steps: sıralı adımlar; last = kapanış adımı; side = yan durumlar (gelmedi/iptal) ; pay = kapanıştan önce tahsilat şartı
FAM = {
    "randevu": dict(
        prefix="RD", noun="Randevu", plural="Randevu Defteri", staff_l="Uzman", pay=True, comm=30,
        steps=S(("alindi", "Randevu alındı"), ("geldi", "Geldi"), ("islemde", "İşlemde"), ("odeme", "Ödeme"), ("tamam", "Tamamlandı")),
        side=S(("gelmedi", "Gelmedi"), ("iptal", "İptal")),
        sections=[("Müşteri ve randevu", [F("customer_name", "Müşteri", req=1), F("customer_phone", "Telefon"), F("staff", "Uzman", "staff"), F("when", "Tarih ve saat", "dt", req=1),
                                          F("duration", "Süre (dk)", "num"), F("place", "Koltuk / oda"), F("source", "Müşteri kaynağı", "select", opts=[("tel", "Telefon"), ("site", "Web sitesi"), ("yuruyen", "Yürüyen müşteri"), ("tavsiye", "Tavsiye")])])],
        items=[dict(k="hizmetler", l="Hizmetler", name="Hizmet", staff=True, sug="brands"), dict(k="urunler", l="Kullanılan / satılan ürün", name="Ürün")],
        check=("Müşteri kartı", [("alerji", "Alerji / hassasiyet sorusu soruldu"), ("onceki", "Önceki işlem notu kontrol edildi"), ("foto", "İşlem fotoğrafı (isteğe bağlı)")]),
        notes_l="Müşteri notu / formül", next_l="Sonraki randevu önerisi", hesap=[("hizmetler", "Hizmetler"), ("urunler", "Ürün")], filters=("bugun", "odemesiz")),
    "siparis": dict(
        prefix="SP", noun="Sipariş", plural="Siparişler", staff_l="Hazırlayan", pay=True, comm=0,
        steps=S(("yeni", "Yeni sipariş"), ("odeme_onay", "Ödeme onayı"), ("hazirlaniyor", "Hazırlanıyor"), ("kargoda", "Kargoda"), ("teslim", "Teslim edildi")),
        side=S(("iade", "İade"), ("iptal", "İptal")),
        sections=[("Müşteri ve teslimat", [F("customer_name", "Müşteri", req=1), F("customer_phone", "Telefon"), F("when", "Sipariş tarihi", "dt"), F("receiver", "Teslim alan"),
                                           F("address", "Teslimat adresi", "area"), F("cargo", "Kargo firması", "select", opts=[("", "Seçin"), ("yurtici", "Yurtiçi Kargo"), ("aras", "Aras Kargo"), ("mng", "MNG Kargo"), ("ptt", "PTT Kargo"), ("elden", "Elden teslim")]),
                                           F("tracking", "Takip no"), F("eta", "Tahmini teslim", "date"), F("shipping", "Kargo ücreti (₺)", "num"), F("channel", "Kanal", "select", opts=[("site", "Web sitesi"), ("pazaryeri", "Pazaryeri"), ("tel", "Telefon / WhatsApp"), ("magaza", "Mağaza")])])],
        items=[dict(k="kalemler", l="Sipariş kalemleri", name="Ürün", opt="Beden / renk / seçenek", sug="brands")],
        check=("Paketleme", [("stok", "Stoktan düşüldü"), ("etiket", "Koli etiketi basıldı"), ("barkod", "Kargo barkodu yapıştırıldı"), ("fatura", "Fatura koliye eklendi")]),
        notes_l="Sipariş notu", next_l="", hesap=[("kalemler", "Ara toplam")], extra_lines=[("shipping", "Kargo ücreti")], filters=("odemesiz",)),
    "yol": dict(
        prefix="CK", noun="Çağrı", plural="Çağrılar", staff_l="Sürücü / ekip", pay=True, comm=25,
        steps=S(("cagri", "Çağrı alındı"), ("yonlendirildi", "Araç yönlendirildi"), ("yolda", "Yolda"), ("yukleme", "Yükleme / taşıma"), ("teslim", "Teslim edildi")),
        side=S(("iptal", "İptal")),
        sections=[("Müşteri ve çağrı", [F("customer_name", "Arayan / müşteri", req=1), F("customer_phone", "Telefon"), F("when", "Çağrı zamanı", "dt"), F("staff", "Sürücü / ekip", "staff"), F("vehicle", "Araç / yük", ), F("plate", "Plaka / detay"),
                                         F("kind", "Yardım türü", "select", opts=[("cekici", "Çekici"), ("aku", "Akü takviye"), ("lastik", "Lastik"), ("yakit", "Yakıt"), ("kilit", "Kilitli kaldı"), ("diger", "Diğer")]), F("insurance", "Sigorta / anlaşma")]),
                  ("Güzergâh", [F("from", "Alış noktası", "area"), F("to", "Bırakış noktası", "area"), F("km", "Mesafe (km)", "num"), F("km_rate", "Kilometre ücreti (₺)", "num"), F("base", "Çıkış ücreti (₺)", "num")])],
        items=[dict(k="masraflar", l="Ek masraflar (otoyol, vinç, ambalaj)", name="Masraf")],
        check=("Yükleme kontrolü", [("foto", "Araç / yük fotoğrafı alındı"), ("hasar", "Mevcut hasar işaretlendi"), ("imza", "Teslim imzası alındı")]),
        notes_l="Çağrı notu", next_l="", hesap=[("masraflar", "Ek masraflar")], base_lines=[("base", "Çıkış ücreti"), ("km_total", "Kilometre ücreti")], filters=("bugun", "odemesiz")),
    "proje": dict(
        prefix="IS", noun="Dosya", plural="Dosyalar", staff_l="Sorumlu", pay=False, comm=0,
        steps=S(("talep", "Yeni talep"), ("teklif", "Teklif"), ("onay", "Onay"), ("calisma", "Çalışma sürüyor"), ("teslim", "Teslim / kapanış")),
        side=S(("iptal", "İptal")),
        sections=[("Müşteri ve iş", [F("customer_name", "Müşteri", req=1), F("customer_phone", "Telefon"), F("staff", "Sorumlu", "staff"), F("when", "Açılış", "dt"), F("subject", "Konu / iş türü"), F("deadline", "Hedef tarih", "date")])],
        items=[dict(k="kalemler", l="Hizmet kalemleri", name="Kalem", sug="brands"), dict(k="masraflar", l="Malzeme ve masraflar", name="Masraf")],
        check=("Belgeler", [("sozlesme", "Sözleşme imzalandı"), ("evrak", "Gerekli evraklar tamam"), ("teslimtut", "Teslim tutanağı")]),
        notes_l="İş notu", next_l="", hesap=[("kalemler", "Hizmet bedeli"), ("masraflar", "Malzeme / masraf")], filters=("odemesiz",)),
    "atolye": dict(
        prefix="AT", noun="Kayıt", plural="Kayıtlar", staff_l="Usta", pay=True, comm=30,
        steps=S(("alindi", "Teslim alındı"), ("inceleme", "İnceleme"), ("onay", "Müşteri onayı"), ("islemde", "Çalışılıyor"), ("hazir", "Hazır / teslim edildi")),
        side=S(("iptal", "İptal")),
        sections=[("Müşteri ve teslim", [F("customer_name", "Müşteri", req=1), F("customer_phone", "Telefon"), F("staff", "Usta", "staff"), F("when", "Teslim alma", "dt"), F("eta", "Tahmini teslim", "date"),
                                         F("item", "Araç / eşya"), F("plate", "Plaka / seri no"), F("complaint", "Şikâyet / istek", "area")])],
        items=[dict(k="isler", l="Yapılan işlemler", name="İşlem"), dict(k="parcalar", l="Parça / malzeme", name="Parça", sug="brands")],
        check=("Teslim kontrolü", [("foto", "Teslim alırken fotoğraf çekildi"), ("onay", "Fiyat müşteriye bildirildi"), ("test", "Teslimden önce test edildi")]),
        notes_l="Usta notu", next_l="Sonraki bakım önerisi", hesap=[("isler", "İşçilik"), ("parcalar", "Parça")], filters=("bugun", "odemesiz")),
    "saha": dict(
        prefix="SH", noun="Servis", plural="Servisler", staff_l="Ekip", pay=True, comm=30,
        steps=S(("talep", "Talep alındı"), ("planlandi", "Planlandı"), ("yolda", "Yolda"), ("islemde", "İşlemde"), ("tamam", "Tamamlandı")),
        side=S(("iptal", "İptal")),
        sections=[("Müşteri ve adres", [F("customer_name", "Müşteri", req=1), F("customer_phone", "Telefon"), F("staff", "Ekip", "staff"), F("when", "Planlanan zaman", "dt"), F("address", "Adres", "area"), F("scope", "Hizmet / kapsam"), F("area_m2", "Alan / adet", "num")])],
        items=[dict(k="isler", l="Yapılan işler", name="İş", sug="brands"), dict(k="malzeme", l="Malzeme", name="Malzeme")],
        check=("Tamamlama", [("foto", "Öncesi / sonrası fotoğraf"), ("imza", "Müşteri onayı alındı"), ("garanti", "Garanti / bakım periyodu bildirildi")]),
        notes_l="Servis notu", next_l="Sonraki bakım tarihi", hesap=[("isler", "İş"), ("malzeme", "Malzeme")], filters=("bugun", "odemesiz")),
    "kurs": dict(
        prefix="KR", noun="Kayıt", plural="Kayıtlar", staff_l="Eğitmen", pay=True, comm=0,
        steps=S(("on_kayit", "Ön kayıt"), ("gorusme", "Görüşme"), ("kayit", "Kayıt yapıldı"), ("egitim", "Eğitim sürüyor"), ("mezun", "Tamamlandı")),
        side=S(("ayrildi", "Ayrıldı")),
        sections=[("Kursiyer / öğrenci", [F("customer_name", "Ad soyad", req=1), F("customer_phone", "Telefon"), F("guardian", "Veli / yakını"), F("staff", "Eğitmen", "staff"), F("when", "Kayıt tarihi", "dt"), F("program", "Program / sınıf"), F("level", "Seviye / grup")])],
        items=[dict(k="ucretler", l="Ücret kalemleri", name="Kalem", sug="brands")],
        check=("Evrak", [("sozlesme", "Kayıt sözleşmesi imzalandı"), ("evrak", "İstenen belgeler alındı"), ("kvkk", "KVKK onayı alındı")]),
        notes_l="Not", next_l="", hesap=[("ucretler", "Eğitim ücreti")], filters=("odemesiz",)),
}
SECTOR_FAMILY = dict(sektor_dil.FAMILY)
for _k in ("surucu_kursu", "src_kursu", "etut_merkezi", "dil_okulu", "muzik_kursu", "anaokulu", "ozel_ders", "bilgisayar_kursu"):
    SECTOR_FAMILY[_k] = "kurs"
for _k in ("terzi", "oto_servis", "oto_yikama", "oto_kaplama", "lastikci", "ayakkabi_tamir", "telefon_tamir", "yazici_servis", "kuru_temizleme", "hali_yikama"):
    SECTOR_FAMILY[_k] = "atolye"
for _k in ("temizlik", "bocek_ilaclama", "cilingir", "asansor", "su_aritma", "havuz_bakim", "jenerator"):
    SECTOR_FAMILY[_k] = "saha"
SECTOR_FAMILY["emlakci"] = "proje"
SECTOR_FAMILY["gunes_enerjisi"] = "proje"

# sektöre özel: adım adları, ek alanlar, kontrol listesi, terimler (aile şablonunun üzerine biner)
SX = {
    "kuafor": dict(extra=[F("formula", "Boya formülü / işlem notu", "area")], title="Randevu"),
    "tirnak_studyo": dict(extra=[F("design", "Model / renk seçimi")]),
    "dis_klinigi": dict(title="Hasta randevusu", extra=[F("tooth", "Diş no / bölge"), F("treat", "Tedavi planı", "area")],
                        check=("Hasta kontrol", [("anamnez", "Anamnez formu dolduruldu"), ("kvkk", "KVKK / onam alındı"), ("rontgen", "Röntgen eklendi")]), next_l="Kontrol randevusu"),
    "veteriner": dict(title="Muayene", extra=[F("animal", "Hayvan adı / türü"), F("age", "Yaş / kilo"), F("vaccine", "Aşı / ilaç notu", "area")], next_l="Sonraki aşı / kontrol"),
    "psikolog": dict(title="Seans", extra=[F("topic", "Seans konusu")], check=("Seans", [("onam", "Bilgilendirilmiş onam alındı"), ("kvkk", "KVKK onayı alındı")])),
    "diyetisyen": dict(title="Görüşme", extra=[F("weight", "Kilo (kg)", "num"), F("target", "Hedef")], next_l="Sonraki ölçüm"),
    "fizyoterapi": dict(title="Seans", extra=[F("region", "Bölge / şikâyet"), F("session_no", "Seans no", "num")]),
    "optik": dict(title="Muayene / sipariş", extra=[F("rx", "Numara (sağ / sol)"), F("frame", "Çerçeve / cam seçimi")]),
    "spor_salonu": dict(title="Üyelik / ders", extra=[F("membership", "Üyelik paketi")]),
    "tekstil": dict(title="Toptan sipariş", extra=[F("season", "Sezon / koleksiyon")], hesap_note="KDV ve toplu alım indirimi hesaba yansır"),
    "eticaret": dict(title="Sipariş"), "market": dict(title="Sipariş", extra=[F("slot", "Teslimat saati aralığı")]),
    "lokanta": dict(title="Rezervasyon / sipariş", extra=[F("table", "Masa no"), F("guests", "Kişi sayısı", "num")]),
    "pastane": dict(title="Özel sipariş", extra=[F("deadline", "Teslim günü / saati"), F("note_cake", "Yazı / tasarım notu", "area")]),
    "cicekci": dict(title="Çiçek siparişi", extra=[F("card_text", "Kart yazısı", "area")]),
    "catering": dict(title="Organizasyon", extra=[F("guests", "Kişi sayısı", "num"), F("event_date", "Etkinlik günü", "date")]),
    "oto_cekici": dict(title="Çekici çağrısı"), "nakliye": dict(title="Taşıma işi", extra=[F("rooms", "Oda / hacim"), F("floor", "Kat / asansör")],
                                                           steps=S(("kesif", "Keşif"), ("teklif", "Teklif onayı"), ("hazirlik", "Paketleme"), ("yolda", "Yolda"), ("teslim", "Teslim edildi"))),
    "kurye": dict(title="Teslimat", steps=S(("alindi", "Alındı"), ("kuryede", "Kuryede"), ("yolda", "Yolda"), ("teslim", "Teslim edildi"), ("imza", "İmzalandı"))),
    "transfer": dict(title="Transfer", extra=[F("flight", "Uçuş / sefer no"), F("pax", "Yolcu sayısı", "num")]),
    "arac_kiralama": dict(title="Kiralama", extra=[F("pickup", "Teslim tarihi", "date"), F("return", "İade tarihi", "date"), F("deposit", "Depozito (₺)", "num")],
                          steps=S(("rez", "Rezervasyon"), ("teslim", "Araç teslim"), ("kirada", "Kirada"), ("iade", "İade alındı"), ("kapandi", "Kapandı"))),
    "avukat": dict(title="Dosya", extra=[F("court", "Mahkeme / birim"), F("case_no", "Esas no"), F("opponent", "Karşı taraf"), F("hearing", "Sonraki duruşma", "date")],
                   steps=S(("gorusme", "Görüşme"), ("vekalet", "Vekalet"), ("dava", "Dava / işlem açıldı"), ("durusma", "Duruşma / takip"), ("karar", "Karar / kapanış")),
                   check=("Evrak", [("vekalet", "Vekâletname alındı"), ("nufus", "Kimlik / nüfus kaydı"), ("belge", "Delil ve belgeler dosyada")]), items=[dict(k="kalemler", l="Vekalet ücreti ve masraflar", name="Kalem")]),
    "mimar": dict(title="Proje", steps=S(("gorusme", "Görüşme"), ("on_proje", "Ön proje"), ("onay", "Onay"), ("uygulama", "Uygulama projesi"), ("teslim", "Teslim")), extra=[F("m2", "Alan (m²)", "num")]),
    "muhasebe": dict(title="Müşteri dosyası", steps=S(("evrak", "Evrak alındı"), ("islemde", "İşlemde"), ("beyan", "Beyanname"), ("onay", "Müşteri onayı"), ("tamam", "Tamamlandı")), extra=[F("period", "Dönem")]),
    "tadilat": dict(title="İş", steps=S(("kesif", "Keşif"), ("teklif", "Teklif"), ("onay", "Onay"), ("uygulama", "Uygulama"), ("teslim", "Teslim")), extra=[F("address", "İş adresi", "area"), F("m2", "Alan (m²)", "num")]),
    "fotografci": dict(title="Çekim", steps=S(("teklif", "Teklif"), ("plan", "Çekim planı"), ("cekim", "Çekim"), ("duzenleme", "Düzenleme"), ("teslim", "Teslim")), extra=[F("event_date", "Çekim günü", "date"), F("place", "Mekân")]),
    "dugun_salonu": dict(title="Etkinlik", steps=S(("gorusme", "Salon gezme"), ("kapora", "Kapora"), ("hazirlik", "Hazırlık"), ("etkinlik", "Etkinlik günü"), ("kapandi", "Kapandı")), extra=[F("guests", "Davetli sayısı", "num"), F("event_date", "Etkinlik günü", "date")]),
    "emlakci": dict(title="Müşteri talebi", steps=S(("talep", "Talep"), ("gosterim", "Yer gösterme"), ("teklif", "Teklif"), ("sozlesme", "Sözleşme"), ("tapu", "Tapu / teslim")), extra=[F("budget", "Bütçe (₺)", "num"), F("region", "Bölge")]),
    "oto_servis": dict(title="Araç kaydı", extra=[F("km", "Kilometre", "num")], next_l="Sonraki bakım (km / tarih)"),
    "oto_yikama": dict(title="Yıkama kaydı", steps=S(("alindi", "Araç alındı"), ("yikama", "Yıkamada"), ("detay", "Detay işlem"), ("hazir", "Hazır"), ("teslim", "Teslim edildi"))),
    "lastikci": dict(title="Lastik kaydı", extra=[F("size", "Lastik ölçüsü")]),
    "telefon_tamir": dict(title="Cihaz kaydı", extra=[F("imei", "IMEI / seri no"), F("pass", "Cihaz kilidi var mı?", "select", opts=[("hayir", "Yok"), ("evet", "Var (müşteri bildirdi)")])]),
    "kuru_temizleme": dict(title="Teslim fişi", steps=S(("alindi", "Teslim alındı"), ("yikamada", "İşlemde"), ("hazir", "Hazır"), ("teslim", "Teslim edildi"), ("odendi", "Ödendi"))),
    "hali_yikama": dict(title="Halı kaydı", steps=S(("alindi", "Teslim alındı"), ("yikamada", "Yıkamada"), ("kurutma", "Kurutma"), ("hazir", "Hazır"), ("teslim", "Teslim edildi"))),
    "cilingir": dict(title="Çilingir çağrısı", extra=[F("lock", "Kilit türü")]),
    "bocek_ilaclama": dict(title="İlaçlama", extra=[F("pest", "Zararlı türü"), F("m2", "Alan (m²)", "num")], next_l="Tekrar ilaçlama tarihi"),
    "asansor": dict(title="Asansör bakımı", extra=[F("building", "Bina / asansör no")], next_l="Sonraki bakım tarihi"),
    "su_aritma": dict(title="Servis", extra=[F("model", "Cihaz modeli")], next_l="Filtre değişim tarihi"),
    "havuz_bakim": dict(title="Havuz servisi", extra=[F("pool", "Havuz ölçüsü / tip")], next_l="Sonraki bakım"),
    "jenerator": dict(title="Servis", extra=[F("kva", "Güç (kVA)")], next_l="Sonraki bakım"),
    "surucu_kursu": dict(title="Kursiyer kaydı", extra=[F("cls", "Sınıf (B, A2...)")], steps=S(("on_kayit", "Ön kayıt"), ("evrak", "Evrak"), ("teori", "Teori"), ("direksiyon", "Direksiyon"), ("sinav", "Sınav / tamamlandı"))),
}


def family_of(key):
    return SECTOR_FAMILY.get(key, "")


def template(key):
    fam = family_of(key)
    if not fam or key in sektor_dil.SADE:
        return None
    t = dict(FAM[fam])
    t["family"] = fam
    sx = SX.get(key, {})
    sec = sektor.SECTORS.get(key, {})
    t["title"] = sx.get("title") or t["noun"]
    if sx.get("steps"):
        t["steps"] = sx["steps"]
    if sx.get("check"):
        t["check"] = sx["check"]
    if sx.get("items"):
        t["items"] = sx["items"]
    if sx.get("next_l") is not None:
        t["next_l"] = sx["next_l"]
    secs = [(a, list(b)) for a, b in t["sections"]]
    if sx.get("extra"):
        secs.append(("Detaylar", sx["extra"]))
    t["sections"] = secs
    t["sug"] = list((sec.get("brands") or {}).keys()) if isinstance(sec.get("brands"), dict) else list(sec.get("brands") or [])
    return t


def public_schema(key):
    t = template(key)
    if not t:
        return None
    ch = t["check"]
    return {
        "family": t["family"], "title": t["title"], "plural": t["plural"], "steps": t["steps"], "side": t["side"], "staff_l": t["staff_l"],
        "sections": [{"t": a, "fields": b} for a, b in t["sections"]],
        "items": [dict(i, sug=(t["sug"] if i.get("sug") == "brands" else [])) for i in t["items"]],
        "check": {"t": ch[0], "opts": [{"k": a, "l": b} for a, b in ch[1]]},
        "notes_l": t["notes_l"], "next_l": t.get("next_l", ""), "pay": t["pay"], "comm": t["comm"],
        "base_lines": [{"k": a, "l": b} for a, b in t.get("base_lines", [])], "extra_lines": [{"k": a, "l": b} for a, b in t.get("extra_lines", [])],
        "hesap": [{"k": a, "l": b} for a, b in t["hesap"]], "filters": list(t.get("filters", ())),
    }


# ------------------------------------------------------------------ doğrulama ve hesap
def _num(v, hi=10 ** 9):
    try:
        x = float(str(v).replace(",", ".")) if v not in (None, "") else 0.0
    except ValueError:
        return 0.0
    return max(0.0, min(hi, round(x, 2)))


def _txt(v, n=200):
    return str(v or "").strip()[:n]


def _field(f, v):
    t = f["t"]
    if t == "num":
        return _num(v)
    if t == "select":
        ok = {o[0] for o in f["opts"]}
        return v if v in ok else f["opts"][0][0]
    if t == "area":
        return _txt(v, 1000)
    if t == "dt":
        s = _txt(v, 20)
        return s if re.match(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?$", s) else ""
    if t == "date":
        s = _txt(v, 10)
        return s if re.match(r"^\d{4}-\d{2}-\d{2}$", s) else ""
    return _txt(v, 120)


def clean_items(tpl, p):
    out = {}
    for it in tpl["items"]:
        rows = []
        for r in (p.get(it["k"]) or [])[:MAX_ITEMS]:
            if not isinstance(r, dict):
                continue
            row = {"name": _txt(r.get("name"), 120), "qty": _num(r.get("qty")) or 1.0, "price": _num(r.get("price"))}
            if it.get("opt"):
                row["opt"] = _txt(r.get("opt"), 60)
            if it.get("staff"):
                row["staff"] = _txt(r.get("staff"), 60)
            if row["name"] or row["price"]:
                rows.append(row)
        out[it["k"]] = rows
    return out


def sums(tpl, d):
    """Hesap satırları + toplam + kalan. Tek yerden hesaplanır (arayüz sunucudan gelen değeri gösterir)."""
    lines = []
    for k, l in tpl["hesap"]:
        v = round(sum(r["qty"] * r["price"] for r in d.get(k, [])), 2)
        lines.append({"k": k, "l": l, "v": v})
    for k, l in tpl.get("base_lines", []):
        v = _num(d.get("base")) if k == "base" else round(_num(d.get("km")) * _num(d.get("km_rate")), 2)
        lines.append({"k": k, "l": l, "v": v})
    for k, l in tpl.get("extra_lines", []):
        lines.append({"k": k, "l": l, "v": _num(d.get(k))})
    gross = round(sum(x["v"] for x in lines), 2)
    disc = min(_num(d.get("discount")), gross)
    total = round(gross - disc, 2)
    paid = round(sum(_num(x.get("amount")) for x in d.get("payments", [])), 2)
    comm = round(total * _num(d.get("comm_pct")) / 100.0, 2)
    return {"lines": lines, "gross": gross, "discount": disc, "total": total, "paid": paid, "balance": round(max(total - paid, 0), 2), "commission": comm}


def belge_html(t, r, sm, g):
    """Kayıttan yazdırılabilir belge: başlık sektörün adıyla, alanlar şablondan, imza kutuları."""
    import html as _h
    e = lambda v: _h.escape(str(v if v is not None else ""))
    para = lambda v: ("%.2f" % float(v or 0)).replace(".", ",") + " ₺"
    adim = {x["k"]: x["l"] for x in t["steps"] + t["side"]}
    out = []
    for baslik, alanlar in t["sections"]:
        satir = []
        for f in alanlar:
            v = r.get(f["k"])
            if f["t"] == "select":
                v = dict(f["opts"]).get(v, v)
            elif f["t"] in ("dt", "date"):
                v = (v or "").replace("T", " ")
            elif f["t"] == "num" and not v:
                v = ""
            if v not in ("", None):
                satir.append("<tr><th>%s</th><td>%s</td></tr>" % (e(f["l"]), e(v)))
        if satir:
            out.append("<h2>%s</h2><table class=kv>%s</table>" % (e(baslik), "".join(satir)))
    for it in t["items"]:
        rows = r.get(it["k"]) or []
        if rows:
            out.append("<h2>%s</h2><table class=ln><tr><th>%s</th><th class=n>Adet</th><th class=n>Birim</th><th class=n>Tutar</th></tr>%s</table>" % (
                e(it["l"]), e(it["name"]), "".join("<tr><td>%s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>" % (
                    e(x.get("name")), e(("%g" % x.get("qty", 1))), para(x.get("price")), para(x.get("qty", 1) * x.get("price", 0))) for x in rows)))
    ozet = "".join("<tr><th>%s</th><td class=n>%s</td></tr>" % (e(l["l"]), para(l["v"])) for l in sm["lines"] if l["v"])
    if sm["discount"]:
        ozet += "<tr><th>İndirim</th><td class=n>-%s</td></tr>" % para(sm["discount"])
    ozet += "<tr class=tot><th>Toplam</th><td class=n>%s</td></tr>" % para(sm["total"])
    if sm["paid"]:
        ozet += "<tr><th>Alınan</th><td class=n>%s</td></tr><tr><th>Kalan</th><td class=n>%s</td></tr>" % (para(sm["paid"]), para(sm["balance"]))
    if sm["total"]:
        out.append("<table class='kv sum'>%s</table>" % ozet)
    chk = t["check"]
    done = [o[1] for o in chk[1] if (r.get("check") or {}).get(o[0])]
    todo = [o[1] for o in chk[1] if not (r.get("check") or {}).get(o[0])]
    if done or todo:
        out.append("<h2>%s</h2><ul class=ck>%s</ul>" % (e(chk[0]), "".join("<li>&#9745; %s</li>" % e(x) for x in done) + "".join("<li>&#9744; %s</li>" % e(x) for x in todo)))
    if r.get("notes"):
        out.append("<h2>%s</h2><p class=nt>%s</p>" % (e(t.get("notes_l") or "Not"), e(r["notes"])))
    tarih = datetime.fromtimestamp(r.get("created_at") or time.time()).strftime("%d.%m.%Y %H:%M")
    firma = g.get("company_name") or "OnlineKaydet"
    iletisim = " · ".join(x for x in (g.get("company_phone"), g.get("company_address")) if x)
    css = ("@page{size:A4;margin:14mm}body{font:13px/1.45 system-ui,Segoe UI,Arial;color:#0a1f44;margin:0}.pg{max-width:780px;margin:0 auto;padding:18px}"
           "header{display:flex;justify-content:space-between;border-bottom:3px solid #f27a1a;padding-bottom:10px;margin-bottom:12px}header h1{margin:0;font-size:22px}"
           "header .r{text-align:right;font-size:12px}h2{font-size:13px;text-transform:uppercase;letter-spacing:.04em;margin:16px 0 6px;color:#f27a1a}"
           "table{width:100%;border-collapse:collapse}th,td{padding:5px 8px;border-bottom:1px solid #dbe2ee;text-align:left;vertical-align:top}.kv th{width:34%;font-weight:600;color:#475569}"
           ".ln th{background:#eef2f8;font-size:12px}.n{text-align:right}.sum{max-width:320px;margin-left:auto;margin-top:12px}.tot th,.tot td{font-size:15px;font-weight:800;border-top:2px solid #0a1f44}"
           ".ck{list-style:none;padding:0;margin:0;columns:2}.nt{white-space:pre-wrap;border:1px solid #dbe2ee;border-radius:6px;padding:8px}"
           ".sg{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-top:46px}.sg div{border-top:1px solid #0a1f44;padding-top:5px;font-size:12px;text-align:center}"
           "footer{margin-top:26px;font-size:11px;color:#64748b;border-top:1px solid #dbe2ee;padding-top:8px}.bar{padding:10px;text-align:center;background:#eef2f8}"
           "@media print{.bar{display:none}}")
    return ('<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>%s %s</title><style>%s</style></head><body>'
            '<div class="bar"><button onclick="window.print()" style="min-height:44px;padding:0 20px;font:700 15px system-ui">Yazdır / PDF olarak kaydet</button></div>'
            '<div class="pg"><header><div><h1>%s</h1><div>%s</div></div><div class="r"><b>%s</b><br>%s<br>Durum: %s</div></header>%s'
            '<div class="sg"><div>%s</div><div>%s</div></div>'
            '<footer>Bu belge OnlineKaydet ile hazırlanmıştır. Kişisel veriler 6698 sayılı KVKK kapsamında işlenir.</footer></div></body></html>') % (
        e(t["title"]), e(r.get("no")), css, e(t["title"]), e(firma + (" · " + iletisim if iletisim else "")), e(r.get("no")), e(tarih),
        e(adim.get(r.get("status"), r.get("status"))), "".join(out), e(r.get("customer_name") or "Müşteri"), e(r.get("staff") or firma))



def clean(tpl, p):
    d = {}
    for _, fl in tpl["sections"]:
        for f in fl:
            if f["t"] == "staff":
                d[f["k"]] = _txt(p.get(f["k"]), 60)
            else:
                d[f["k"]] = _field(f, p.get(f["k"]))
    if not d.get("customer_name"):
        raise ValueError(tpl["noun"] + " için müşteri adı gerekli")
    d.update(clean_items(tpl, p))
    d["check"] = {o[0]: bool((p.get("check") or {}).get(o[0])) for o in tpl["check"][1]}
    d["notes"] = _txt(p.get("notes"), 1500)
    d["next_note"] = _txt(p.get("next_note"), 300)
    d["discount"] = _num(p.get("discount"))
    d["base"] = _num(p.get("base"))
    d["shipping"] = _num(p.get("shipping"))
    d["km"] = _num(d.get("km")) if "km" in d else _num(p.get("km"))
    d["km_rate"] = _num(d.get("km_rate")) if "km_rate" in d else _num(p.get("km_rate"))
    d["comm_pct"] = min(_num(p.get("comm_pct", tpl["comm"]), 100), 100) if p.get("comm_pct") not in (None, "") else float(tpl["comm"])
    return d


def row_cols(tpl, r):
    st = {s["k"]: s["l"] for s in tpl["steps"] + tpl["side"]}
    when = (r.get("when") or "").replace("T", " ")
    return [r.get("no", ""), r.get("customer_name", ""), when or "—", r.get("staff") or "—", ("%.2f ₺" % r.get("total", 0)).replace(".", ",") if r.get("total") else "—", st.get(r.get("status"), "")]


def headers(tpl):
    return ["No", "Müşteri", "Zaman", tpl["staff_l"], "Tutar", "Durum"]


# ------------------------------------------------------------------ API
def register(api_router, db, deps):
    require_admin = deps["require_admin"]

    async def sec_key():
        d = await db.app_settings.find_one({"_id": "sector"}, {"_id": 0}) or {}
        return d.get("key") or ""

    async def tpl_or_404():
        key = await sec_key()
        t = template(key)
        if not t:
            raise HTTPException(404, "Bu sektör mevcut servis kaydı ekranını kullanır")
        return key, t

    @api_router.get("/admin/kayit/schema")
    async def k_schema(_: dict = Depends(require_admin)):
        key, t = await tpl_or_404()
        s = public_schema(key)
        users = await db.users.find({"is_active": {"$ne": False}}, {"_id": 0, "name": 1}).to_list(200)
        s["staff"] = [u["name"] for u in users if u.get("name")]
        s["headers"] = headers(t)
        return s

    @api_router.get("/admin/kayit")
    async def k_list(q: str = "", flt: str = "", _: dict = Depends(require_admin)):
        key, t = await tpl_or_404()
        rows = await db.records.find({}, {"_id": 0}).sort("created_at", -1).to_list(5000)
        q = q.strip().lower()
        today = date.today().isoformat()
        out, cnt = [], {}
        for r in rows:
            cnt[r.get("status")] = cnt.get(r.get("status"), 0) + 1
            if q and not any(q in str(r.get(f, "")).lower() for f in ("no", "customer_name", "customer_phone", "staff")):
                continue
            if flt == "bugun" and not (r.get("when") or "").startswith(today):
                continue
            if flt == "odemesiz" and not (r.get("balance", 0) > 0 and r.get("status") not in ("iptal",)):
                continue
            if flt and flt not in ("bugun", "odemesiz") and r.get("status") != flt:
                continue
            out.append({"id": r["id"], "cols": row_cols(t, r), "status": r.get("status", "")})
        open_ = sum(1 for r in rows if r.get("status") not in (t["steps"][-1]["k"], "iptal", "gelmedi", "iade", "ayrildi"))
        summary = [[t["plural"] + " (toplam)", len(rows)], ["Açık", open_], ["Bugün", sum(1 for r in rows if (r.get("when") or "").startswith(today))],
                   ["Bekleyen tahsilat", ("%.2f ₺" % sum(r.get("balance", 0) for r in rows if r.get("status") != "iptal")).replace(".", ",")]]
        return {"rows": out, "summary": summary, "counts": cnt, "total": len(rows)}

    @api_router.get("/admin/kayit/{rid}/belge")
    async def k_belge(rid: str, _: dict = Depends(require_admin)):
        """Sektöre göre başlıklı, yazdırılabilir A4 belge (tarayıcıdan 'PDF olarak kaydet')."""
        key, t = await tpl_or_404()
        r = await db.records.find_one({"id": rid}, {"_id": 0})
        if not r:
            raise HTTPException(404, "Kayıt bulunamadı")
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        return Response(belge_html(t, r, sums(t, r), g), media_type="text/html; charset=utf-8")

    @api_router.get("/admin/kayit/{rid}")
    async def k_one(rid: str, _: dict = Depends(require_admin)):
        key, t = await tpl_or_404()
        r = await db.records.find_one({"id": rid}, {"_id": 0})
        if not r:
            raise HTTPException(404, "Kayıt bulunamadı")
        r["sums"] = sums(t, r)
        return r

    async def next_no(t):
        n = await db.records.count_documents({})
        return "%s-%d" % (t["prefix"], 1001 + n)

    @api_router.post("/admin/kayit")
    async def k_add(payload: dict, user: dict = Depends(require_admin)):
        key, t = await tpl_or_404()
        try:
            d = clean(t, payload)
        except ValueError as e:
            raise HTTPException(400, str(e))
        d.update({"id": str(uuid.uuid4()), "no": await next_no(t), "status": t["steps"][0]["k"], "payments": [], "created_at": time.time(), "updated_at": time.time(),
                  "created_by": user.get("id", ""), "sector": key})
        s = sums(t, d)
        d.update({"total": s["total"], "paid": 0.0, "balance": s["total"], "commission": s["commission"]})
        await db.records.insert_one(dict(d))
        d.pop("_id", None)
        d["sums"] = s
        return d

    @api_router.put("/admin/kayit/{rid}")
    async def k_put(rid: str, payload: dict, _: dict = Depends(require_admin)):
        key, t = await tpl_or_404()
        old = await db.records.find_one({"id": rid}, {"_id": 0})
        if not old:
            raise HTTPException(404, "Kayıt bulunamadı")
        try:
            d = clean(t, payload)
        except ValueError as e:
            raise HTTPException(400, str(e))
        merged = {**old, **d}
        s = sums(t, merged)
        d.update({"total": s["total"], "balance": s["balance"], "commission": s["commission"], "updated_at": time.time()})
        await db.records.update_one({"id": rid}, {"$set": d})
        out = await db.records.find_one({"id": rid}, {"_id": 0})
        out["sums"] = s
        return out

    @api_router.delete("/admin/kayit/{rid}")
    async def k_del(rid: str, _: dict = Depends(require_admin)):
        r = await db.records.delete_one({"id": rid})
        if not r.deleted_count:
            raise HTTPException(404, "Kayıt bulunamadı")
        return {"ok": True}

    @api_router.post("/admin/kayit/{rid}/adim")
    async def k_step(rid: str, payload: dict, user: dict = Depends(require_admin)):
        key, t = await tpl_or_404()
        r = await db.records.find_one({"id": rid}, {"_id": 0})
        if not r:
            raise HTTPException(404, "Kayıt bulunamadı")
        to = _txt(payload.get("to"), 30)
        valid = {s["k"] for s in t["steps"] + t["side"]}
        if to not in valid:
            raise HTTPException(400, "Geçersiz adım")
        last = t["steps"][-1]["k"]
        s = sums(t, r)
        if to == last and t["pay"] and s["balance"] > 0:
            raise HTTPException(400, "Kapatmadan önce ödemeyi alın (kalan %.2f ₺)" % s["balance"])
        upd = {"status": to, "updated_at": time.time()}
        if to == last:
            upd["closed_at"] = time.time()
        await db.records.update_one({"id": rid}, {"$set": upd, "$push": {"history": {"to": to, "at": time.time(), "by": user.get("name", "")}}})
        return {"ok": True, "status": to}

    @api_router.post("/admin/kayit/{rid}/odeme")
    async def k_pay(rid: str, payload: dict, user: dict = Depends(require_admin)):
        key, t = await tpl_or_404()
        r = await db.records.find_one({"id": rid}, {"_id": 0})
        if not r:
            raise HTTPException(404, "Kayıt bulunamadı")
        amt = _num(payload.get("amount"))
        s = sums(t, r)
        if amt <= 0:
            raise HTTPException(400, "Tutar girin")
        if amt > s["balance"] + 0.001:
            raise HTTPException(400, "Tutar kalan bakiyeden fazla (%.2f ₺)" % s["balance"])
        method = payload.get("method") if payload.get("method") in ("Nakit", "Kart", "Havale") else "Nakit"
        pay = {"id": uuid.uuid4().hex[:10], "amount": amt, "method": method, "at": datetime.now().isoformat(timespec="minutes")}
        paid = round(s["paid"] + amt, 2)
        await db.records.update_one({"id": rid}, {"$push": {"payments": pay}, "$set": {"paid": paid, "balance": round(max(s["total"] - paid, 0), 2), "updated_at": time.time()}})
        await db.cash_transactions.insert_one({"id": str(uuid.uuid4()), "type": "gelir", "amount": amt, "date": datetime.now().isoformat(), "created_by": user.get("id", ""),
                                               "technician_id": "", "job_id": "", "category": t["noun"] + " geliri", "payment_method": method,
                                               "description": "%s geliri - %s - %s" % (t["noun"], r.get("no", ""), r.get("customer_name", ""))})
        return {"ok": True, "paid": paid, "balance": round(max(s["total"] - paid, 0), 2)}
