"""Yeni sektörler için ortak araçlar (ön hazırlık listesi + yönlendirme). Sonuçlar bilgilendirme amaçlıdır."""
from .tools import checks_tool, steps_tool

TOOLS = {}
TOOLS['gen.hazirlik'] = checks_tool('hazirlik', 'cl', 'Başvuru öncesi hazırlık listesi', 'Hazır olanları işaretleyin; başvurudan önce eksiklerinizi görün.', 'Hazır olanlar',
    [('kimlik', 'Kimlik ve iletişim bilgilerim hazır'), ('belge', 'İlgili belge ya da dosyalarım hazır'), ('soru', 'Sormak istediklerimi not ettim'), ('saat', 'Uygun gün ve saatimi belirledim')],
    {'kimlik': 1, 'belge': 1, 'soru': 1, 'saat': 1}, [(0, 'warn', 'Birkaç hazırlık eksik'), (3, 'ok', 'Hemen hemen hazırsınız'), (4, 'ok', 'Tamamen hazırsınız')],
    {'kimlik': 'Randevu formunda telefon numaranızı doğru yazın.', 'belge': 'Hangi belgenin gerektiğini aramadan önce öğrenin.', 'soru': 'Sorularınızı yazarsanız görüşme kısalır.', 'saat': 'Birkaç alternatif saat belirtirseniz randevu kolaylaşır.'},
    'Bu liste genel bir hatırlatmadır.')
TOOLS['gen.soru'] = steps_tool('soru', 'al', 'Hangi hizmet bana uygun?', 'Durumunuzu seçin; ilk adımı görün.', 'Durum',
    [('ilk', 'İlk kez geleceğim'), ('devam', 'Daha önce hizmet aldım, devam edeceğim'), ('acil', 'Acil bir ihtiyacım var'), ('kurum', 'Firmam adına başvuracağım')],
    {'ilk': ('İlk başvuru', 'ok', ['Randevu formunu doldurun.', 'Size dönüş yapılacak; bilgi ve belge listesi iletilir.'], 'Bilgilendirme amaçlıdır.'),
     'devam': ('Devam eden hizmet', 'ok', ['Önceki kaydınızı telefon numaranızla buluruz.', 'Uygun yeni tarihi seçin.'], ''),
     'acil': ('Acil durum', 'warn', ['Önce telefonla arayın.', 'Hayati bir tehlike varsa 112 acil çağrı merkezini arayın.'], 'Bu bir tıbbi ya da hukuki değerlendirme değildir.'),
     'kurum': ('Kurumsal başvuru', 'ok', ['Firma adı ve yetkili kişi bilgisini yazın.', 'Toplu hizmet için teklif hazırlanır.'], '')})
