"""Sahip paneli: firma için otomatik doldurulan Hizmet (abonelik) Sözleşmesi PDF'i.
Firma kartındaki bilgiler (unvan, yetkili, telefon, e-posta, adres, vergi, paket, sektör) sözleşmeye otomatik gelir;
eksik bilgi için doldurulabilir boş çizgi bırakılır. Satıcı bilgisi 'satis' ayarlarından (unvan, VKN, adres) okunur."""
import io
import re
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.responses import Response

import tenant

BOS = "_" * 28
def sure_coz(sure):
    """'aylik' | 'yillik' | 'iki_yil' | 'm<ay>' (ör. m6, m36) -> ay sayısı (1-120)"""
    s = str(sure or "yillik")
    ay = {"aylik": 1, "yillik": 12, "iki_yil": 24}.get(s)
    if ay is None:
        m = re.fullmatch(r"m(\d{1,3})", s)
        ay = int(m.group(1)) if m else 12
    return max(1, min(120, ay))


def sure_bilgi(ay):
    """(etiket, gün)"""
    if ay % 12 == 0:
        return "%d yıllık" % (ay // 12), ay // 12 * 365
    return "%d aylık" % ay, ay * 30


def tl(x):
    s = "{:,.2f}".format(float(x)).replace(",", "X").replace(".", ",").replace("X", ".")
    return s[:-3] if s.endswith(",00") else s


def _t(v, n=300):
    return " ".join(str(v or "").split())[:n]


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def v(x):
    """Dolu ise kaçışlı metin, boş ise doldurulabilir çizgi."""
    x = _t(x)
    return _esc(x) if x else BOS


def madde_listesi(f, fy, sat, mus, modul_adlari, bugun, bitis, no):
    """Sözleşme maddeleri: [(başlık, [paragraf, ...])]"""
    firma = mus["unvan"]
    return [
        ("1. TARAFLAR", [
            "<b>HİZMET SAĞLAYICI:</b> %s — VKN: %s, Vergi Dairesi: %s — Adres: %s — E-posta: %s (bundan sonra “OnlineKaydet” denir)." % (
                v(sat["unvan"] or "OnlineKaydet"), v(sat["vkn"]), v(sat["vergi_dairesi"]), v(sat["adres"]), v(sat["eposta"])),
            "<b>MÜŞTERİ:</b> %s — Yetkili: %s — Vergi No / TCKN: %s, Vergi Dairesi: %s — Adres: %s — Telefon: %s — E-posta (panel kullanıcı adı): %s (bundan sonra “Müşteri” denir)." % (
                v(firma), v(mus["yetkili"]), v(mus["vkn"]), v(mus["vd"]), v(mus["adres"]), v(mus["telefon"]), v(mus["email"])),
        ]),
        ("2. KONU", [
            "İşbu sözleşmenin konusu, OnlineKaydet'in internet üzerinden sunduğu servis/randevu/iş takibi, müşteri ve stok yönetimi, muhasebe ve web sitesi yazılımına (“Hizmet”) Müşteri'nin "
            "%s abonelik süresince erişmesine ilişkin şartların belirlenmesidir. Yazılım Müşteri'ye lisanslanır; mülkiyeti devredilmez." % _esc(fy["sure_ad"]),
        ]),
        ("3. HİZMETİN KAPSAMI", [
            "Seçilen paket: <b>%s</b>. %s" % (_esc(fy["paket_ad"]), ("Sektör: <b>%s</b>. " % _esc(mus["sektor"]) if mus["sektor"] else "") +
                                            ("Pakete dahil modüller: %s." % _esc(", ".join(modul_adlari)) if modul_adlari else "")),
            "Hizmet; barındırma, yedekleme, güvenlik güncellemeleri ve standart e-posta/telefon destek hizmetini içerir. Paket dışı özel geliştirme, veri aktarımı ve yerinde eğitim ayrıca fiyatlandırılır ve yazılı onayla yapılır.",
        ]),
        ("4. SÜRE VE YENİLEME", [
            "Sözleşme %s tarihinde başlar, <b>%s</b> tarihine kadar (%s) geçerlidir. Süre bitiminde Müşteri paketi yenilemezse panele erişim askıya alınır; veriler "
            "askı tarihinden itibaren 30 gün boyunca saklanır ve bu süre içinde talep edilirse dışa aktarılır, sonrasında silinir." % (bugun, bitis, _esc(fy["sure_ad"])),
        ]),
        ("5. BEDEL VE ÖDEME", [
            "Abonelik bedeli: %s ₺ + KDV (%%%s) %s ₺ = <b>%s ₺ (KDV dahil)</b>%s." % (tl(fy["matrah"]), tl(fy["kdv_oran"]), tl(fy["kdv"]), tl(fy["toplam"]),
                                                                              (" — %s" % _esc(fy["not"]) if fy.get("not") else "")),
            "Ödeme, sözleşme tarihinde peşin olarak kredi kartı veya havale/EFT ile yapılır. Ödeme alındığında fatura düzenlenir ve e-posta ile iletilir. "
            "Ödeme yapılmadan hizmet etkinleştirilmeyebilir. Yenileme dönemlerinde güncel liste fiyatı uygulanır; değişiklik, yenilemeden en az 15 gün önce bildirilir.",
        ]),
        ("6. MÜŞTERİ'NİN YÜKÜMLÜLÜKLERİ", [
            "Müşteri; kullanıcı adı ve şifresinin gizliliğinden, panele girdiği verilerin doğruluğundan ve hukuka uygunluğundan, kendi müşterilerine ait kişisel verileri "
            "6698 sayılı KVKK'ya uygun işlemekten sorumludur. Hizmeti yasa dışı amaçla, sistemin güvenliğini bozacak veya başkalarının haklarını ihlal edecek şekilde kullanamaz; "
            "erişim bilgilerini üçüncü kişilerle paylaşamaz ve hizmeti izinsiz yeniden satamaz.",
        ]),
        ("7. KİŞİSEL VERİLER VE GİZLİLİK", [
            "Müşteri'nin panele girdiği veriler bakımından Müşteri “veri sorumlusu”, OnlineKaydet “veri işleyen”dir. OnlineKaydet bu verileri yalnızca Hizmeti sunmak amacıyla işler, "
            "her firmanın verisini ayrı bir veritabanında tutar, makul teknik ve idari güvenlik tedbirlerini uygular ve yasal zorunluluk dışında üçüncü kişilere aktarmaz. "
            "Taraflar, işbu sözleşme kapsamında öğrendikleri ticari sırları gizli tutar; bu yükümlülük sözleşme bitiminden sonra 2 yıl devam eder.",
        ]),
        ("8. HİZMET SEVİYESİ", [
            "OnlineKaydet hizmeti süreklilik esasıyla sunar; planlı bakım, mücbir sebep, internet/altyapı sağlayıcılarından ve Müşteri'nin kendi kusurundan kaynaklanan kesintilerden "
            "sorumlu değildir. Planlı bakımlar mümkün olduğunca düşük kullanım saatlerinde yapılır ve önceden duyurulur.",
        ]),
        ("9. FESİH", [
            "Taraflardan biri sözleşmeye aykırılık halinde, yazılı ihtara rağmen 7 gün içinde aykırılığı gidermeyen karşı tarafın sözleşmesini feshedebilir. Müşteri'nin ödenen "
            "dönem bedeli, hizmetin kullanıldığı dönem için iade edilmez; OnlineKaydet'in sözleşmeye aykırılığı nedeniyle fesih halinde kullanılmayan dönem bedeli oransal iade edilir. "
            "Tüketici mevzuatının zorunlu hükümleri saklıdır.",
        ]),
        ("10. SORUMLULUĞUN SINIRI", [
            "OnlineKaydet'in bu sözleşmeden doğan toplam sorumluluğu, kasıt ve ağır kusur halleri dışında, Müşteri'nin ilgili dönem için ödediği abonelik bedeliyle sınırlıdır. "
            "Dolaylı zararlar, kâr kaybı ve veri kaybı (yedekleme yükümlülüğünün yerine getirilmiş olması halinde) kapsam dışıdır.",
        ]),
        ("11. FİKRİ MÜLKİYET", [
            "Yazılımın, arayüzün, tasarımların ve markanın tüm hakları OnlineKaydet'e aittir. Müşteri'nin panele yüklediği içerik ve verilerin hakları Müşteri'ye aittir.",
        ]),
        ("12. TEBLİGAT, UYUŞMAZLIK VE YÜRÜRLÜK", [
            "Taraflar yukarıda yazılı e-posta ve adreslerini tebligat adresi olarak kabul eder; değişiklikler yazılı bildirilir. Bu sözleşmeden doğacak uyuşmazlıklarda "
            "%s Mahkemeleri ve İcra Daireleri yetkilidir. Sözleşme iki nüsha olarak düzenlenmiş olup %s tarihinde imzalanarak yürürlüğe girmiştir; elektronik ortamda onaylanması da imza yerine geçer." % (
                _esc(sat.get("mahkeme") or "Ankara"), bugun),
        ]),
    ]


def pdf_olustur(f, fy, sat, modul_adlari, no):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT as TA_JUSTIFY
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, KeepTogether
    import satin_al
    R, B = satin_al._font()
    try:
        pdfmetrics.registerFontFamily(R, normal=R, bold=B, italic=R, boldItalic=B)
    except Exception:                                              # noqa: BLE001
        pass
    tr = timezone(timedelta(hours=3))
    simdi = datetime.now(tr)
    bugun = simdi.strftime("%d.%m.%Y")
    bitis = (simdi + timedelta(days=fy["gun"])).strftime("%d.%m.%Y")
    mus = {"unvan": (f.get("demo_firma") if f.get("demo") and f.get("demo_firma") else f.get("name")) or "", "yetkili": f.get("contact_name") or "",
           "vkn": f.get("tax_no") or "", "vd": f.get("tax_office") or "", "adres": f.get("address") or "", "telefon": f.get("phone") or "",
           "email": f.get("login_email") or f.get("email") or "", "sektor": f.get("sector_ad") or ""}
    ink = colors.HexColor("#1d2433")
    st_b = ParagraphStyle("b", fontName=R, fontSize=9.2, leading=13.2, alignment=TA_JUSTIFY, textColor=ink, spaceAfter=4)
    st_h = ParagraphStyle("h", fontName=B, fontSize=10, leading=14, textColor=colors.HexColor("#b4244a"), spaceBefore=8, spaceAfter=3)
    st_t = ParagraphStyle("t", fontName=B, fontSize=15, leading=19, textColor=ink, alignment=1, spaceAfter=2)
    st_s = ParagraphStyle("s", fontName=R, fontSize=9, leading=12, textColor=colors.HexColor("#555b6b"), alignment=1, spaceAfter=10)
    st_c = ParagraphStyle("c", fontName=R, fontSize=9, leading=13, textColor=ink, alignment=1)

    def sayfa(c, d):
        c.saveState()
        c.setFont(R, 7.5); c.setFillColor(colors.HexColor("#777e8c"))
        c.drawString(18 * mm, 10 * mm, "Sözleşme No: %s" % no)
        c.drawRightString(A4[0] - 18 * mm, 10 * mm, "Sayfa %d" % d.page)
        c.setStrokeColor(colors.HexColor("#e8456e")); c.setLineWidth(1.6); c.line(18 * mm, A4[1] - 12 * mm, A4[0] - 18 * mm, A4[1] - 12 * mm)
        c.restoreState()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=20 * mm, bottomMargin=18 * mm,
                            title="Hizmet Sözleşmesi %s" % no, author="OnlineKaydet")
    el = [Paragraph("ONLİNEKAYDET HİZMET (ABONELİK) SÖZLEŞMESİ", st_t), Paragraph("Sözleşme No: %s · Tarih: %s" % (no, bugun), st_s)]
    for baslik, paras in madde_listesi(f, fy, sat, mus, modul_adlari, bugun, bitis, no):
        el.append(Paragraph(baslik, st_h))
        for p in paras:
            el.append(Paragraph(p, st_b))
    sag = [[Paragraph("<b>HİZMET SAĞLAYICI</b><br/>%s" % v(sat["unvan"] or "OnlineKaydet"), st_c), Paragraph("<b>MÜŞTERİ</b><br/>%s" % v(mus["unvan"]), st_c)],
           [Paragraph("<br/><br/>Kaşe / İmza", st_c), Paragraph("<br/><br/>Kaşe / İmza", st_c)],
           [Paragraph("Ad Soyad: ______________________", st_c), Paragraph("Ad Soyad: %s" % (_esc(mus["yetkili"]) if mus["yetkili"] else "______________________"), st_c)],
           [Paragraph("Tarih: %s" % bugun, st_c), Paragraph("Tarih: %s" % bugun, st_c)]]
    tb = Table(sag, colWidths=[87 * mm, 87 * mm], rowHeights=[None, 26 * mm, None, None])
    tb.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), .6, colors.HexColor("#c9ccd6")), ("INNERGRID", (0, 0), (-1, -1), .4, colors.HexColor("#dfe1e8")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    el += [Spacer(1, 10), KeepTogether([Paragraph("İMZALAR", st_h), tb])]
    doc.build(el, onFirstPage=sayfa, onLaterPages=sayfa)
    return buf.getvalue()


def register(api_router, db, deps):
    adm = deps["require_admin"]

    @api_router.get("/admin/firms/{fid}/sozlesme.pdf")
    async def sozlesme(fid: str, paket: str = "", sure: str = "yillik", bedel: str = "", kdv_dahil: int = 0, _: dict = Depends(adm)):
        """Firma kartındaki bilgilerle hazır sözleşme PDF'i. paket/sure/bedel verilmezse firmanın paketi ve yıllık liste fiyatı kullanılır."""
        if tenant.current():
            raise HTTPException(403, "Yalnızca platform sahibi")
        f = await db.main().firms.find_one({"id": fid}, {"_id": 0})
        if not f:
            raise HTTPException(404, "Firma bulunamadı")
        import firms
        pks = await firms.API["packages"]()
        pid = paket if paket in pks else (f.get("package") if f.get("package") in pks else "")
        if not pid:
            pid = next((k for k, x in pks.items() if float(x.get("price") or 0) > 0), "")
        pk = pks.get(pid) or {}
        ay = sure_coz(sure)
        ad, gun = sure_bilgi(ay)
        aylik = float(pk.get("price") or 0)
        yillik = float(pk.get("yearly") or 0) or aylik * 10
        matrah = yillik * ay / 12 if ay >= 12 else aylik * ay
        satis = await db.main().app_settings.find_one({"_id": "satis"}, {"_id": 0}) or {}
        oran = float(satis.get("kdv", 20.0))
        notu = ""
        if bedel:
            try:
                b = float(str(bedel).replace(",", "."))
            except ValueError:
                raise HTTPException(422, "Bedel sayı olmalı")
            matrah = b / (1 + oran / 100) if kdv_dahil else b
            notu = "anlaşılan özel bedel"
        matrah = round(matrah, 2)
        kdv = round(matrah * oran / 100, 2)
        fy = {"paket_ad": pk.get("name") or pid or BOS, "sure_ad": ad, "gun": gun, "matrah": matrah, "kdv_oran": oran, "kdv": kdv, "toplam": round(matrah + kdv, 2), "not": notu}
        try:
            import sektor
            f["sector_ad"] = (sektor.SECTORS.get(f.get("sector") or "") or {}).get("name") or ""
        except Exception:                                          # noqa: BLE001
            f["sector_ad"] = ""
        sat = {k: _t(satis.get(k)) for k in ("unvan", "vkn", "vergi_dairesi", "adres", "eposta", "mahkeme")}
        try:
            import firms as _f
            mods = [_f.MODULES.get(m, m) for m in (pk.get("modules") or [])]
        except Exception:                                          # noqa: BLE001
            mods = []
        no = "SZ-%s-%s" % (datetime.now(timezone(timedelta(hours=3))).strftime("%Y%m%d"), re.sub(r"[^A-Za-z0-9]", "", fid)[:4].upper())
        data = pdf_olustur(f, fy, sat, mods, no)
        ad_dosya = re.sub(r"[^A-Za-z0-9_-]+", "-", _t(f.get("name"), 40)) or "firma"
        return Response(data, media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="Sozlesme-%s-%s.pdf"' % (ad_dosya, no)})
