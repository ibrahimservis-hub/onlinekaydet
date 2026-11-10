"""Mağaza örnek ürünleri için gerçek fotoğraf katmanı (Pexels, ücretsiz lisans).
Tema kodundaki okPimg() çizimi yerine kategori eşleşirse /tema-urun/<tür><1-3>.jpg fotoğrafı gösterilir; eşleşmezse eski çizim kalır.
Hem eski hem yeni temalara çalışma zamanında uygulanır (tekrar uygulanmaz)."""
import re

KINDS = [  # (tür, js düzenli ifadesi: küçük harfli ad + kategori)
    ("canta", r"çanta|canta|cüzdan|valiz|sırt çant"),
    ("ayakkabi", r"ayakkab|sneaker|terlik|sandalet|çizme|bot "),
    ("giyim", r"tişört|tisort|gömlek|elbise|pantolon|ceket|mont|kazak|giyim|etek|şort|hırka|sweat"),
    ("saat", r"saat|takı|kolye|yüzük|bilezik|gözlük"),
    ("mama", r"mama|kedi|köpek|kopek"),
    ("kozmetik", r"bakım|bakim|krem|cilt|wax|şekillendir|şampuan|parfüm|serum|losyon|sabun|kozmetik"),
    ("bitki", r"saksı|saksi|orkide|çiçek|cicek|bitki"),
    ("lastik", r"lastik|amortisör|amortisor|süspansiyon|suspansiyon"),
    ("baski", r"baskı|baski|kartvizit|promosyon|kupa"),
    ("kamera", r"kamera|alarm|diyafon|nvr|kayıt cihaz|güvenlik"),
    ("tv", r"\btv\b|uydu|hoparlör|hoparlor|lnb|televizyon"),
    ("kablo", r"kablo|nym|iletken"),
    ("pano", r"pano|sigorta|kaçak akım|priz|anahtar"),
    ("ev", r"aydınlat|aydinlat|avize|lamba|ledli|vazo|dekor|yastık|battaniye|halı"),
    ("bilgisayar", r"ssd|\bram\b|bellek|güç kaynağ|dizüstü|klavye|adaptör|adaptor|usb|switch|depolama|soğutucu fan|hub|poe"),
    ("tesisat", r"boru|rakor|sifon|armatür|armatur|batarya|bakır|bakir|musluk"),
    ("pompa", r"pompa|motor|\bfan\b|vana|valf|eşanjör|esanjor|tank|rezervuar|şamandıra|samandira|kompresör|gaz|filtre"),
    ("elektronik", r"sensör|sensor|termostat|kart|elektronik|röle|role|kapasitör|kapasitor|elektrik"),
    ("telefon", r"telefon|kılıf|kilif|şarj|sarj|kulaklık|kulaklik|powerbank|tablet"),
    ("parca", r"conta|kayış|kayis|sarf|montaj|kilit|rezistans|kurutma|koruma|bağlantı|baglanti|yedek|parça|parca"),
    ("hediye", r"hediye|paket"),
]
MARK = "window.okReal=function"
PRELUDE = ("<script>" + MARK + "(n,c,k){var l=(String(n||'')+' '+String(c||'')).toLowerCase().replace(/İ/g,'i'),s=String(n||'')+String(c||''),h=0,i,R=["
           + ",".join("[/%s/,'%s']" % (rx, k) for k, rx in KINDS) + "];for(i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))%997;"
           "for(i=0;i<R.length;i++)if(R[i][0].test(l))return '<img class=\"okpimg\" loading=\"lazy\" alt=\"'+String(n||'Ürün').replace(/\"/g,'')+'\" src=\"/tema-urun/'+R[i][1]+((h+(k||0))%3+1)+'.jpg\" style=\"width:100%;height:100%;object-fit:cover;display:block\">';return ''};</script>")
HEAD = "function okPimg(n,c){"
PATCH = "function okPimg(n,c){var Z=window.okReal&&window.okReal(n,c);if(Z)return Z;"


def apply(h):
    if HEAD not in h or MARK in h:
        return h
    h = h.replace(HEAD, PATCH, 1)
    return h.replace("</head>", PRELUDE + "</head>", 1) if "</head>" in h else PRELUDE + h
