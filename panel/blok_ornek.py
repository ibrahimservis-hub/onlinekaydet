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
