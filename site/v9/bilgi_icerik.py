# -*- coding: utf-8 -*-
"""Bilgi bankası makaleleri. Adımlar panelin (panel/yp_ui.html, panel/ilan.py) gerçek ekran ve düğme adlarına göre yazıldı."""
def S(*a):
    return '<ol class="steps">'+''.join('<li><b>%s</b>%s</li>'%(t,x) for t,x in a)+'</ol>'
def TIP(x): return '<div class="ipuc"><b>İpucu:</b> %s</div>'%x

A=[]
def add(slug,kat,ad,ozet,body): A.append(dict(slug=slug,kat=kat,ad=ad,ozet=ozet,body=body))

add('urun-ekleme','Mağaza','Ürün nasıl eklenir?','Ürün kartını doldurun, kâr oranını görün, yayınlayın.',
 '<p>Ürünler, mağazanızın temelidir. Bir ürünü bir kez girersiniz; sitenizde ve bağladığınız pazaryerlerinde aynı kayıttan kullanılır.</p>'
 '<h2>Tek ürün ekleme</h2>'+S(
  ('Ürünler sayfasını açın','Panelde ürün listesine girin. Liste boşsa “Ürün ekle” ile başlayabilirsiniz.'),
  ('“Ürün ekle” düğmesine basın','Ürün kartı açılır. Ürünü bir bağlantıdan hazırlamak isterseniz “Bağlantıdan ürün ekle” de vardır.'),
  ('Adı, görselleri ve açıklamayı girin','Görselleri sürükleyerek sıralayın; ilk görsel “Kapak” olur, başka bir görseli “Kapak yap” ile öne alırsınız. Bağlantıdan görsel eklemek ve YouTube ya da Vimeo ürün videosu bağlamak da mümkündür.'),
  ('Fiyatı girin','Satış fiyatı, varsa indirimli fiyat, alış (maliyet) fiyatı, KDV oranı ve ürün başı kargo maliyetini yazın. Sağdaki kutu müşterinin ödeyeceği tutarı, KDV hariç tutarı, net kârı ve kâr oranını anında gösterir. İndirimli fiyat satış fiyatından düşük olmalıdır; zarar ettiren fiyatlarda uyarı çıkar.'),
  ('Stok bilgisini girin','Stok adedi, stok kodu (SKU), barkod (EAN/GTIN) ve az stok uyarısı alanlarını doldurun. Sepette en az/en çok adet de belirlenebilir.'),
  ('Kategori, marka ve etiket seçin','Birden çok kategori eklenebilir; ★ ile ana kategoriyi seçersiniz. Özellikleri (renk, beden, garanti gibi) “+ Özellik ekle” ile girin.'),
  ('Kargo ölçülerini yazın','Ağırlık, en, boy, yükseklik ve kargoya veriliş süresini girin. Desi buradan hesaplanır.'),
  ('SEO alanlarına bakın','Sayfa adresi, SEO başlığı ve meta açıklama boşsa “Boş SEO alanlarını üründen doldur” düğmesi üründen üretir.'),
  ('Kaydedin','“Taslak kaydet” ürünü sitede göstermeden saklar. “Kaydet ve yayınla” ürünü sitenizde yayına alır.'))+
 TIP('Çok ürününüz varsa tek tek girmeyin: Ürünler sayfasındaki “Excel’den yükle” ile toplu yükleyin, “Excel’e aktar” ile listenizi dışarı alın.')+
 '<h2>Varyant ve benzer ürünler</h2><p>Renk ve beden gibi seçenekleri ürün kartındaki varyant bölümünden tanımlayın. “Benzer ürünler” boş kalırsa sitede aynı kategoriden ürünler önerilir.</p>')

add('pazaryerine-gonderme','Mağaza','Ürünler pazaryerine nasıl gönderilir?','Ürünleri seçin, pazaryerlerini işaretleyin, gönderin; eksikler ürün ürün raporlanır.',
 '<p>Ürününüzü bir kez girersiniz; stok ve fiyat bilgisi kanallar arasında eşitlenir. Pazaryerine göndermeden önce ürünün pazaryeri için gerekli bilgileri (kategori, marka, barkod gibi) tam olmalıdır.</p>'
 '<h2>Pazaryerine bağlanma</h2>'+S(
  ('Satış › Pazaryerleri ekranını açın','Her pazaryeri için bağlantı durumu görünür: bağlı ya da bağlı değil.'),
  ('Kanalı bağlayın','İlgili pazaryerinin kartından bağlantı bilgilerinizi girin. Bağlantı kurulunca kanal “bağlı” görünür.'))+
 '<h2>Ürünleri gönderme</h2>'+S(
  ('Ürünler listesinde ürünleri seçin','Tek tek işaretleyin ya da listedeki seçimi kullanın. Seçince üstte toplu işlem çubuğu açılır.'),
  ('“Pazaryerlerine gönder” düğmesine basın','Açılan pencerede Trendyol, Hepsiburada, N11, Çiçeksepeti, Pazarama ve PttAVM için işaret kutuları gelir.'),
  ('Göndermek istediğiniz pazaryerlerini işaretleyin','Yalnız bağlı pazaryerleri seçilebilir.'),
  ('“Gönder” deyin','Hazır ürünler gönderilir. Eksiği olan ürünler gönderilmez; hangi üründe neyin eksik olduğu ürün ürün raporlanır. Eksikleri tamamlayıp yeniden gönderin.'))+
 '<h2>Kanal fiyatı</h2><p>Ürün kartındaki kanal tablosunda her pazaryeri için fiyat belirleyebilirsiniz: “Sitedeki fiyatla”, “Yüzde ekleyerek” (komisyonu fiyata yansıtır) ya da “Bu kanala özel fiyat”. Tablo her kanal için net kârı gösterir.</p>'
 '<h2>Stok ve fiyatı toplu güncelleme</h2><p>Ürünleri seçtiğinizde “Fiyat güncelle”, “İndirim uygula”, “Stok güncelle”, “Kategori / marka” ve “Tek kanalda aç / kapat” işlemleri de gelir.</p>'
 +TIP('“Satışa kapat” dediğinizde ürün sitede görünmez ve pazaryerlerinde stok 0 olarak bildirilir. Yeniden açınca yalnız site açılır; pazaryerleri için “Pazaryerlerine gönder”i tekrar kullanın.'))

add('siparis-ve-kargo','Mağaza','Sipariş ve kargo takibi','Site, pazaryeri ve telefon siparişleri tek listede; durumu ilerletin, kargo kodunu girin.',
 '<p>Siteden, pazaryerinden, telefondan ya da WhatsApp’tan gelen bütün siparişler <b>Siparişler</b> listesinde toplanır. Sipariş kaydedildiğinde stok anında düşer; iptal ve iade onayında stok geri döner.</p>'
 '<h2>Siparişi yürütme</h2>'+S(
  ('Siparişler sayfasını açın','Listenin üstünde ciro, net kâr ve sepet ortalaması görünür.'),
  ('Siparişi açın ve onaylayın','Durum akışı: yeni, onaylandı, hazırlanıyor, kargoda, teslim.'),
  ('Kargo firmasını ve takip kodunu girin','Kargo firması ve takip kodu siparişin kaydında durur.'),
  ('Toplu işlem ve yazdırma','Birden çok siparişi seçip aynı anda ilerletebilir ya da yazdırabilirsiniz.'))+
 '<h2>İade ve iptal</h2><p>İptal ve iade onayladığınızda stok kendiliğinden geri eklenir. İade süreçleri ayrı bir ekranda izlenir.</p>')

add('randevu-ve-takvim','İş takibi','Randevu nasıl verilir ve yönetilir?','Takvimden yeni randevu açın, onaylayın, işlem sonunda ödemeyi alın.',
 '<p>Randevular <b>Takvim</b> ekranında günlük olarak görünür. Müşteri sitenizden randevu talebi gönderdiğinde talep burada “talep” olarak belirir.</p>'
 '<h2>Randevu açma</h2>'+S(
  ('Takvim ekranını açın','Gün gün gezmek için ‹ Bugün › düğmelerini ya da tarih seçiciyi kullanın.'),
  ('“Yeni randevu” düğmesine basın','Müşteri adı, telefon, tarih, saat, hizmeti yapacak kişi, süre (dk), nereden geldiği ve not alanlarını doldurun. Tutar ve gerekirse indirim yazılır.'),
  ('Kaydedin','Randevu takvimde yerini alır; müşteriye hatırlatma mesajı gider (mesaj ayarınız açıksa).'))+
 '<h2>Gelen talebi yönetme</h2>'+S(
  ('Talebi açın','Siteden gelen talepler “Talebi onayla” penceresiyle açılır.'),
  ('“Onayla” ya da “Reddet” deyin','Gerekirse tarihi ve saati değiştirip onaylayın.'))+
 '<h2>Randevu günü</h2>'+S(
  ('Müşteri geldiğinde “Geldi”yi işaretleyin','Gelmediyse “Gelmedi” seçin.'),
  ('İşe başlarken “İşleme al” deyin','Randevunun durumu ilerler.'),
  ('İş bitince “Tamamla ve ödeme al” deyin','Ödeme şeklini seçin. Tahsil edilen tutar <a href="/bilgi-kasa-ve-muhasebe.html">Kasa</a>’ya aynı anda yazılır; prim hesabı da buradan yapılır.'))+
 TIP('Bir müşterinin geçmişini randevu penceresindeki “Müşteri geçmişi” ile görürsünüz. Randevuyu “Düzenle” ile değiştirebilir, “İptal et” ile kapatabilirsiniz.'))

add('musteri-yonetimi','İş takibi','Müşteri kayıtları','Müşteriler randevu aldıkça kendiliğinden birikir; elle de ekleyebilirsiniz.',
 '<p><b>Müşteriler</b> listesi randevu ve siparişlerle kendiliğinden dolar.</p>'
 '<h2>Müşteri ekleme ve arama</h2>'+S(
  ('Müşteriler sayfasını açın','Arama ve süzme alanları listenin üstündedir.'),
  ('Elle eklemek için “Yeni müşteri”ye basın','Ad soyad ve telefonu yazın, kaydedin.'),
  ('Mağazada ya da yüz yüze gelen müşteri için “Mağaza müşterisi” seçin','Randevusuz hızlı satış kaydı açılır.'),
  ('Kayıtları dışarı alın','“Excel’e aktar” ile listenin tamamını indirirsiniz.'))+
 '<h2>Müşteri geçmişi</h2><p>Bir müşteriyi açtığınızda önceki randevuları, ödemeleri ve notları görürsünüz. Rapor ekranında yeni gelen ve geri gelen müşteri sayısı ayrıca gösterilir.</p>')

add('kasa-ve-muhasebe','İş takibi','Kasa ve muhasebe','Randevudan alınan her ödeme kasaya yazılır; gelir ve gideri ayrıca girin.',
 '<p><b>Kasa</b> ekranı gelir ve gider hareketlerinizi bugün, bu hafta ve bu ay olarak gösterir. Randevudan alınan her ödeme buraya aynı anda yazılır; ayrıca elle kayıt girebilirsiniz.</p>'
 '<h2>Kasa hareketi ekleme</h2>'+S(
  ('Kasa ekranını açın','Üstteki seçiciyle dönemi (bugün, bu hafta, bu ay) seçin.'),
  ('Para girdiyse “Para girdi”ye, çıktıysa “Para çıktı”ya basın','Tutarı, açıklamayı ve ödeme şeklini yazıp kaydedin.'),
  ('Randevu dışı satış için “Mağaza müşterisi”ni kullanın','Satış yapılır ve ödemesi kasaya yazılır.'))+
 '<h2>Raporlar</h2><p>Raporlar ekranı ciroyu, giderleri ve net sonucu döneme göre gösterir; yeni ve geri gelen müşteri sayısını da içerir. Sipariş tarafında ciro, net kâr ve sepet ortalaması Siparişler listesinin üstündedir.</p>')

add('personel-ve-prim','İş takibi','Ekip, maaş ve prim','Kişi ekleyin; prim tamamlanan randevulardan kendiliğinden hesaplanır.',
 '<p><b>Ekip</b> ekranı çalışanlarınızı, yaptıkları işi ve hak edişlerini gösterir. Prim, tamamlanan randevulardan kendiliğinden hesaplanır.</p>'
 '<h2>Çalışan ekleme ve ödeme</h2>'+S(
  ('Ekip ekranını açın','Dönemi “Bu ay” ya da “Geçen ay” olarak seçin.'),
  ('“Kişi ekle”ye basın','Ad, maaş ve prim oranını girip kaydedin.'),
  ('Tablodan hak edişi izleyin','Her kişi için bugünkü iş, tamamlanan iş, ciro, prim, maaş, ödenen ve ödenecek tutar yazar. Ödenecek = maaş + prim − dönemde yapılan ödemeler (avans, maaş, prim).'),
  ('“Öde” deyin','Yaptığınız ödeme kasadan gider olarak düşer.')))

add('ilan-ekleme','Web sitesi','Panelden ilan nasıl eklenir?','Emlak, araç kiralama, transfer ve tur gibi işler için ilan vitrini.',
 '<p>İlan bölümü; emlakçı, araç kiralama, transfer ve tur organizasyonu gibi ilan vitrini olan sektörlerde açılır. Eklediğiniz ilanlar sitenizde <b>İlanlar</b> sayfasında listelenir, her ilanın kendi sayfası olur ve arama motorları bu sayfaları görür.</p>'
 '<h2>İlan ekleme</h2>'+S(
  ('Panelde ilan modülünü açın','Mevcut ilanlarınız durumlarıyla birlikte listelenir.'),
  ('Yeni ilan ekleyin','Başlık en az 5 karakter olmalıdır.'),
  ('Türü ve kategoriyi seçin','Tür: Satılık, Kiralık, Devren ya da Günlük kiralık. Kategori: Daire, Villa, Müstakil ev, Arsa, İş yeri, Dükkan, Ofis, Bina, Araç, Tur ya da Diğer.'),
  ('Fiyat ve konumu girin','Fiyat, il, ilçe ve mahalle yazılır.'),
  ('Ayrıntıları doldurun','Oda sayısı, metrekare, kat, bina yaşı ve ısıtma gibi alanlar ile en fazla 5000 karakterlik açıklama girilir. En çok 20 özellik etiketi eklenebilir.'),
  ('Resim yükleyin','Bir ilana en fazla 8 resim eklenir; her biri yaklaşık 600 KB’ı geçmemelidir. Büyük resimleri küçültüp yükleyin.'),
  ('Durumu seçin','“Yayında” ilan sitede görünür; “Taslak” saklanır ama görünmez; “Satıldı” ilan satıldı olarak işaretlenir. “Öne çıkan” işaretiyle ilanı öne alabilirsiniz.')))

add('web-sitesi-duzenleme','Web sitesi','Web sitenizi düzenleme','Metin, yazı tipi, resim ve menü panelden değişir; kodlama gerekmez.',
 '<p>Seçtiğiniz temanın her bölümü panelden düzenlenir. Hazır tema ilk günden yayına uygun gelir; siz yazıları ve resimleri kendinize göre değiştirirsiniz.</p>'
 '<h2>Düzenleme adımları</h2>'+S(
  ('Panelde Web Sitem bölümünü açın','Sitenizin sayfaları ve bölümleri listelenir.'),
  ('Değiştirmek istediğiniz bölümü seçin','Başlık, metin, resim ve düğme yazıları düzenlenir.'),
  ('Yazı tipini ve renkleri ayarlayın','Yazı tipi ve görünüm ayarları tema içinde yapılır.'),
  ('Menüyü düzenleyin','Menüye sayfa ekleyip çıkarabilir, sırayı değiştirebilirsiniz.'),
  ('Kaydedin ve yayınlayın','Değişiklik sitenizde görünür. Alan adı bağlama ve SSL paketin içindedir.'))+
 '<h2>SEO</h2><p>Sayfa başlığı ve açıklamasını her sayfa için düzenleyebilirsiniz. Ürün ve ilan sayfaları için bu alanlar kendi kartlarında bulunur.</p>')

add('baslangic','Başlangıç','İlk gün: hesabı açıp yayına almak','Demo, tema seçimi, bilgilerin girilmesi ve yayın adımları.',
 '<p>OnlineKaydet’te kurulum üç adımdır: deneyin, temanızı seçin, bilgilerinizi girip yayına alın.</p>'+S(
  ('Demo hesabı açın','<a href="/demo.html">Demo sayfasında</a> ad, telefon ve firma adınızı yazın. Demo hesabı 7 gün açık kalır; kart bilgisi istenmez.'),
  ('Temanızı seçin','<a href="/temalar.html">Temalar</a> sayfasından işinize uygun temayı bulun.'),
  ('Bilgilerinizi girin','Firma adı, telefon, hizmetler ya da ürünler ve resimleri panelden ekleyin.'),
  ('Alan adınızı bağlayın','Alan adı bağlama ve SSL pakete dahildir.'),
  ('Yayına alın','Siteniz yayına girer; randevu ve siparişler panelinize düşmeye başlar.'))+
 TIP('Takıldığınız yerde <a href="/iletisim.html">bize yazın</a> ya da 0544 444 40 04’ü arayın.'))
