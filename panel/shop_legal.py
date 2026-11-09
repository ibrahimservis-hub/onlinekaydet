# -*- coding: utf-8 -*-
"""Mağaza açan firmalar için yasal metinler (otomatik üretim, firma bilgisiyle).

6502 sayılı Tüketicinin Korunması Hakkında Kanun, Mesafeli Sözleşmeler Yönetmeliği ve 6698 sayılı KVKK esas alınan
genel şablonlardır. Firma bilgileri (unvan, adres, vergi no, iletişim) girildikçe metinler dolar; panelden düzenlenebilir.
Hukuki danışman onayı önerilir: şablon, firmanın özel satış koşullarının yerini tutmaz.
"""
import hashlib
from typing import Optional
import html as _h

SLUGS = [
    ("mesafeli-satis-sozlesmesi", "Mesafeli Satış Sözleşmesi"),
    ("on-bilgilendirme-formu", "Ön Bilgilendirme Formu"),
    ("iptal-iade-cayma", "İptal, İade ve Cayma Hakkı"),
    ("teslimat-ve-kargo", "Teslimat ve Kargo Koşulları"),
    ("gizlilik-kvkk", "Gizlilik ve KVKK Aydınlatma Metni"),
    ("cerez-politikasi", "Çerez Politikası"),
]
TITLES = dict(SLUGS)
# Sipariş verirken onaylanması gereken belgeler
CHECKOUT_DOCS = ["mesafeli-satis-sozlesmesi", "on-bilgilendirme-formu", "iptal-iade-cayma", "gizlilik-kvkk"]


def e(x) -> str:
    return _h.escape(str(x or ""), quote=True)


def seller_block(s: dict) -> str:
    rows = [("Unvan", s.get("seller_title")), ("Adres", s.get("address")), ("Telefon", s.get("phone")), ("E-posta", s.get("email")),
            ("Vergi dairesi / no", " / ".join(x for x in (s.get("tax_office"), s.get("tax_no")) if x)), ("MERSİS no", s.get("mersis")), ("KEP adresi", s.get("kep"))]
    rows = [(k, v) for k, v in rows if v]
    if not rows:
        return "<p><em>Satıcı bilgileri henüz girilmedi (Mağaza Ayarları → Satıcı ve yasal bilgiler).</em></p>"
    return "<table class=\"lg-t\">" + "".join("<tr><th>%s</th><td>%s</td></tr>" % (e(k), e(v)) for k, v in rows) + "</table>"


def _days(s) -> int:
    try:
        return max(14, int(s.get("return_days") or 14))
    except (TypeError, ValueError):
        return 14


def _ret_cost(s) -> str:
    return ("İade kargo bedeli satıcı tarafından karşılanır." if s.get("return_shipping") == "satici"
            else "Cayma hakkının kullanılması halinde iade kargo bedeli (satıcının aksini belirtmediği sürece) alıcıya aittir.")


def _doc_sozlesme(s, shop):
    return f"""
<h2>1. Taraflar</h2>
<p><b>SATICI</b></p>{seller_block(s)}
<p><b>ALICI</b>: Sipariş formunda adı, adresi ve iletişim bilgileri yazılı olan kişidir.</p>
<h2>2. Konu</h2>
<p>İşbu sözleşme, ALICI'nın SATICI'ya ait internet sitesinden elektronik ortamda siparişini verdiği, sipariş onayında nitelikleri ve satış bedeli belirtilen ürün(ler)in satışı ve teslimi ile ilgili olarak 6502 sayılı Tüketicinin Korunması Hakkında Kanun ve Mesafeli Sözleşmeler Yönetmeliği hükümleri gereğince tarafların hak ve yükümlülüklerini düzenler.</p>
<h2>3. Sözleşme konusu ürün ve bedel</h2>
<p>Ürünün cinsi, adedi, KDV dahil satış fiyatı, kargo ücreti ve varsa kapıda ödeme bedeli ile toplam tutar, sipariş özetinde ve sipariş onayında gösterilir. Bu değerler ALICI'nın sipariş verdiği andaki değerlerdir.</p>
<h2>4. Ödeme</h2>
<p>Ödeme; sitede sunulan yöntemlerden (havale/EFT, kredi/banka kartı, kapıda ödeme) ALICI'nın seçtiği şekilde yapılır. Kredi/banka kartı ile ödemede kart bilgileri satıcı tarafından saklanmaz; ödeme, lisanslı ödeme kuruluşunun güvenli sayfasında alınır. Havale/EFT ile ödemede sipariş numarası açıklama alanına yazılmalıdır.</p>
<h2>5. Teslimat</h2>
<p>Ürün, ALICI'nın bildirdiği teslimat adresine, sipariş tarihinden itibaren en geç 30 gün içinde ve genel olarak {e(s.get('delivery_days') or '1-3 iş günü')} içinde teslim edilir. Teslimat masrafı sipariş özetinde belirtilir{(' ve kargo firması ' + e(s.get('carrier')) + ' ile yapılır') if s.get('carrier') else ''}. ALICI, teslim anında paketi kontrol eder; hasarlı veya ambalajı açılmış paketi teslim almaz ve tutanak tutturur.</p>
<h2>6. Cayma hakkı</h2>
<p>ALICI, ürünü teslim aldığı tarihten itibaren {_days(s)} gün içinde herhangi bir gerekçe göstermeksizin ve cezai şart ödemeksizin sözleşmeden cayma hakkına sahiptir. Cayma bildirimi yazılı olarak veya kalıcı veri saklayıcısı ile SATICI'ya iletilir. Ürün, kullanılmamış ve yeniden satılabilir durumda, fatura ve varsa tüm aksesuarlarıyla iade edilir. SATICI, cayma bildiriminin ulaşmasından itibaren 14 gün içinde ödemeyi iade eder. {_ret_cost(s)}</p>
<p><b>Cayma hakkının kullanılamayacağı haller (Yönetmelik m.15):</b> ALICI'nın istekleri veya kişisel ihtiyaçları doğrultusunda hazırlanan ürünler; çabuk bozulabilen veya son kullanma tarihi geçebilecek ürünler; teslimden sonra ambalajı açılmış olup sağlık ve hijyen açısından iadesi uygun olmayan ürünler; teslimden sonra başka ürünlerle karışan ve doğası gereği ayrıştırılamayan ürünler; ambalajı açılmış bilgisayar yazılımı, ses/görüntü kayıtları gibi tekrar kullanılabilir ürünler; cayma süresi bitmeden ALICI'nın onayıyla ifasına başlanan hizmetler (ör. yerinde montaj).</p>
<h2>7. Ayıplı ürün ve garanti</h2>
<p>Ayıplı ürünlerde ALICI, Kanun'un 11. maddesindeki seçimlik haklarını (ücretsiz onarım, ürün değişimi, bedel indirimi veya sözleşmeden dönme) kullanabilir. Garanti süresi ve koşulları ürün sayfasında ve garanti belgesinde belirtilir.</p>
<h2>8. Mücbir sebepler</h2>
<p>Tarafların kontrolü dışındaki olağanüstü haller (doğal afet, savaş, grev, nakliye kesintisi vb.) nedeniyle ifa gecikirse taraflar sorumlu tutulamaz; ALICI'ya bilgi verilir, ALICI dilerse siparişi iptal edebilir.</p>
<h2>9. Uyuşmazlık</h2>
<p>İşbu sözleşmeden doğan uyuşmazlıklarda, her yıl Ticaret Bakanlığı tarafından ilan edilen parasal sınırlar dahilinde ALICI'nın veya SATICI'nın yerleşim yerindeki Tüketici Hakem Heyetleri, bu sınırları aşan durumlarda Tüketici Mahkemeleri yetkilidir.</p>
<h2>10. Yürürlük</h2>
<p>ALICI, sitedeki sipariş adımında işbu sözleşmeyi ve Ön Bilgilendirme Formu'nu okuyup onayladığını, elektronik ortamda gerekli teyidi verdiğini kabul eder. Sözleşme, sipariş onayı anında kurulmuş olur.</p>"""


def _doc_onbilgi(s, shop):
    return f"""
<p>İşbu form, 6502 sayılı Kanun ve Mesafeli Sözleşmeler Yönetmeliği uyarınca sipariş vermeden önce ALICI'nın bilgilendirilmesi amacıyla hazırlanmıştır.</p>
<h2>1. Satıcı bilgileri</h2>{seller_block(s)}
<h2>2. Ürünün temel nitelikleri</h2>
<p>Ürünün adı, markası, modeli, teknik özellikleri, adedi ve garanti bilgisi ilgili ürün sayfasında yer alır. Sipariş özeti, ALICI'nın onayına sunulan nihai bilgileri içerir.</p>
<h2>3. Fiyat ve ödeme</h2>
<p>Tüm fiyatlar Türk Lirası ve KDV dahildir. Ürün bedeline ek olarak kargo ücreti ve (kapıda ödeme seçilirse) kapıda ödeme hizmet bedeli sipariş özetinde ayrıca gösterilir. Ödeme yöntemleri: havale/EFT, kredi/banka kartı, kapıda ödeme (satıcı tarafından açılmışsa).</p>
<h2>4. Teslimat</h2>
<p>Teslimat süresi genel olarak {e(s.get('delivery_days') or '1-3 iş günü')}, her durumda en geç 30 gündür. Teslimat adresi ALICI'nın siparişte bildirdiği adrestir.</p>
<h2>5. Cayma hakkı</h2>
<p>ALICI, teslimden itibaren {_days(s)} gün içinde gerekçe göstermeksizin cayma hakkını kullanabilir. Cayma bildirimi: {e(s.get('email') or s.get('phone') or 'satıcı iletişim bilgileri')}. {_ret_cost(s)} İade adresi: {e(s.get('return_address') or s.get('address') or 'satıcı adresi')}.</p>
<p>Cayma hakkının kullanılamayacağı hâller ve ayrıntılar Mesafeli Satış Sözleşmesi'nin 6. maddesindedir.</p>
<h2>6. Şikâyet ve başvuru</h2>
<p>Şikâyetlerinizi yukarıdaki iletişim bilgilerinden iletebilirsiniz. Ayrıca parasal sınırlar dahilinde Tüketici Hakem Heyeti'ne veya Tüketici Mahkemesi'ne başvurabilirsiniz.</p>"""


def _doc_iade(s, shop):
    return f"""
<h2>İptal</h2>
<p>Kargoya verilmeden önce siparişinizi iptal etmek için bize ulaşın ({e(s.get('phone') or s.get('email') or 'iletişim bilgileri')}). Ödemeniz, kullandığınız yönteme göre iade edilir; kartlı ödemelerde bankanıza bağlı olarak yansıması birkaç iş günü sürebilir.</p>
<h2>Cayma hakkı ({_days(s)} gün)</h2>
<p>Ürünü teslim aldığınız tarihten itibaren {_days(s)} gün içinde, gerekçe göstermeksizin iade edebilirsiniz. Ürün kullanılmamış, ambalajı ve aksesuarları eksiksiz ve yeniden satılabilir durumda olmalıdır.</p>
<h2>Nasıl iade edilir?</h2>
<ol><li>Bize yazılı olarak (e-posta, telefon/WhatsApp mesajı) cayma talebinizi bildirin; sipariş numaranızı belirtin.</li>
<li>Ürünü faturasıyla birlikte aşağıdaki adrese gönderin: <b>{e(s.get('return_address') or s.get('address') or 'satıcı adresi')}</b></li>
<li>Ürün tarafımıza ulaştıktan ve kontrol edildikten sonra 14 gün içinde bedel, ödeme yaptığınız yönteme iade edilir.</li></ol>
<p>{_ret_cost(s)}</p>
<h2>İade edilemeyen ürünler</h2>
<p>Kişiye özel hazırlanan, ambalajı açılmış hijyen/sağlık ürünleri, teslimden sonra başka ürünlerle karışan ürünler, ambalajı açılmış yazılım/kayıt ortamları ve cayma süresi bitmeden onayınızla ifasına başlanan hizmetler (ör. yerinde montaj) için cayma hakkı kullanılamaz.</p>
<h2>Hasarlı veya hatalı ürün</h2>
<p>Teslimatta hasarlı gelen veya sonradan hata gösteren ürünler için ayıplı mal hükümleri uygulanır: ücretsiz onarım, değişim, bedel indirimi veya sözleşmeden dönme haklarınızı kullanabilirsiniz. Lütfen ürünü ve paketi fotoğraflayıp bize iletin.</p>"""


def _doc_teslimat(s, shop):
    fee = float(shop.get("shipping_fee") or 0)
    free = float(shop.get("free_shipping_over") or 0)
    kargo = ("Kargo ücreti %.2f TL" % fee) if fee else "Kargo ücretsizdir"
    if fee and free:
        kargo += "; %.2f TL ve üzeri siparişlerde kargo ücretsizdir" % free
    carrier = ("<p>Kargo firması: <b>" + e(s.get("carrier")) + "</b></p>") if s.get("carrier") else ""
    return f"""
<h2>Teslimat süresi</h2>
<p>Siparişler, ödemenin onaylanmasının (kapıda ödemede sipariş teyidinin) ardından {e(s.get('delivery_days') or '1-3 iş günü')} içinde kargoya verilir. Her koşulda teslimat süresi 30 günü aşmaz.</p>
<h2>Kargo ücreti</h2>
<p>{kargo}. Kapıda ödeme seçeneklerinde ek hizmet bedeli sipariş özetinde gösterilir.</p>
<h2>Teslim alırken</h2>
<p>Paketi kargo görevlisinin yanında kontrol edin; ezik, yırtık veya ıslak pakette teslim almayıp tutanak tutturun. Teslimatta bulunamazsanız kargo firması sizinle iletişime geçer.</p>
{carrier}"""


def _doc_gizlilik(s, shop):
    return f"""
<h2>Veri sorumlusu</h2>{seller_block(s)}
<h2>İşlenen kişisel veriler</h2>
<p>Ad soyad, telefon, e-posta, teslimat ve fatura adresi, sipariş ve ödeme durumu bilgileri, müşteri hesabı bilgileri (şifreniz geri döndürülemez biçimde saklanır) ve sitenin kullanımına ilişkin teknik veriler (IP adresi, tarayıcı bilgisi).</p>
<h2>İşleme amaçları</h2>
<p>Siparişin alınması, ödemenin ve teslimatın gerçekleştirilmesi, faturalandırma, garanti ve satış sonrası destek, yasal yükümlülüklerin yerine getirilmesi, müşteri hesabının yönetimi ve (onayınız varsa) kampanya ve bilgilendirme iletişimi.</p>
<h2>Hukuki sebepler</h2>
<p>Sözleşmenin kurulması ve ifası (KVKK m.5/2-c), hukuki yükümlülük (m.5/2-ç), meşru menfaat (m.5/2-f) ve açık rıza (m.5/1) gerektiren işlemlerde rızanız.</p>
<h2>Aktarım</h2>
<p>Verileriniz, hizmetin gerektirdiği ölçüde kargo/kurye firmalarına, ödeme kuruluşuna, SMS ve e-posta hizmet sağlayıcılarına, muhasebe/mali müşavire ve yetkili kamu kurumlarına aktarılabilir. Yurt dışı aktarım gerektiren hizmet sağlayıcılarda mevzuata uygun güvenceler aranır.</p>
<h2>Saklama süresi</h2>
<p>Verileriniz ilgili mevzuatta öngörülen süreler (ör. ticari defter ve fatura için 10 yıl) ve amacın gerektirdiği süre boyunca saklanır, sonra silinir, yok edilir veya anonim hale getirilir.</p>
<h2>Haklarınız (KVKK m.11)</h2>
<p>Verilerinizin işlenip işlenmediğini öğrenme, bilgi talep etme, amacına uygun kullanılıp kullanılmadığını öğrenme, aktarıldığı üçüncü kişileri bilme, eksik/yanlış işlenmişse düzeltilmesini isteme, silinmesini veya yok edilmesini isteme, itiraz etme ve zarara uğramanız halinde tazminat talep etme haklarına sahipsiniz.</p>
<p>Başvurularınızı {e(s.get('email') or s.get('kep') or 'yukarıdaki iletişim bilgileri')} üzerinden iletebilirsiniz. Müşteri hesabınızdan verilerinizi indirebilir veya hesabınızı silebilirsiniz.</p>"""


def _doc_cerez(s, shop):
    return f"""
<p>Sitemiz, düzgün çalışabilmesi için gerekli olan çerez ve tarayıcı depolama (localStorage) teknolojilerini kullanır.</p>
<h2>Zorunlu kullanımlar</h2>
<p>Sepetiniz ve oturumunuz (müşteri girişi), tarayıcınızda saklanır; bunlar olmadan alışveriş yapılamaz. Bu veriler pazarlama amacıyla kullanılmaz.</p>
<h2>İsteğe bağlı kullanımlar</h2>
<p>Ziyaretçi istatistiği veya reklam ölçümü için analiz araçları kullanılıyorsa bunlar yalnızca onayınızla çalışır. Tarayıcı ayarlarınızdan çerezleri silebilir veya engelleyebilirsiniz; bu durumda sepet ve giriş özellikleri çalışmayabilir.</p>
<h2>İletişim</h2><p>Sorularınız için: {e(s.get('email') or s.get('phone') or 'iletişim bilgileri')}.</p>"""


_BUILD = {"mesafeli-satis-sozlesmesi": _doc_sozlesme, "on-bilgilendirme-formu": _doc_onbilgi, "iptal-iade-cayma": _doc_iade,
          "teslimat-ve-kargo": _doc_teslimat, "gizlilik-kvkk": _doc_gizlilik, "cerez-politikasi": _doc_cerez}

CSS = ('<style>.lg{max-width:860px;margin:0 auto;padding:48px 20px 72px;line-height:1.7}.lg h1{font-size:clamp(1.6rem,4vw,2.3rem);margin:0 0 6px}'
       '.lg h2{font-size:1.15rem;margin:26px 0 6px}.lg .lg-d{color:#6b7280;font-size:.85rem;margin:0 0 20px}.lg-t{border-collapse:collapse;margin:8px 0}'
       '.lg-t th{text-align:left;padding:4px 14px 4px 0;vertical-align:top;white-space:nowrap}.lg-t td{padding:4px 0}</style>')


def default_html(slug: str, seller: dict, shop: dict) -> str:
    f = _BUILD.get(slug)
    return f(seller, shop) if f else ""


def doc_html(slug: str, seller: dict, shop: dict, custom: Optional[dict] = None) -> str:
    c = (custom or {}).get(slug) or {}
    return c.get("html") or default_html(slug, seller, shop)


def page(slug: str, seller: dict, shop: dict, custom: Optional[dict], updated: str = "") -> str:
    body = doc_html(slug, seller, shop, custom)
    return '%s<article class="lg"><h1>%s</h1>%s%s</article>' % (CSS, e(TITLES.get(slug, slug)),
                                                                '<p class="lg-d">Son güncelleme: %s</p>' % e(updated[:10]) if updated else "", body)


def version(seller: dict, shop: dict, custom: Optional[dict]) -> str:
    """Sipariş sırasında onaylanan metin sürümü (içerik değişince değişir)."""
    h = hashlib.sha1()
    for slug in CHECKOUT_DOCS:
        h.update(doc_html(slug, seller, shop, custom).encode("utf-8"))
    return h.hexdigest()[:10]


def missing_fields(s: dict) -> list:
    need = [("seller_title", "Satıcı unvanı"), ("address", "Adres"), ("phone", "Telefon"), ("email", "E-posta"), ("tax_no", "Vergi no")]
    return [lbl for k, lbl in need if not str(s.get(k) or "").strip()]
