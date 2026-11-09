"""62 premium tarif + 8 mevcut temanın premium sınıfına alınması. Yön x sektör x palet x yazı tipi x düzen kombinasyonları."""
SECT = ['kombi', 'klima', 'beyaz_esya', 'elektronik', 'bilgisayar', 'tesisat', 'elektrik', 'guvenlik']
TP = {'kombi': 'kombi', 'klima': 'klima', 'beyaz_esya': 'beyaz', 'elektronik': 'tv', 'bilgisayar': 'pc', 'tesisat': 'tes', 'elektrik': 'elk', 'guvenlik': 'gvn'}
TOOLN = {'kombi': ['kod', 'bakim', 'teshis', 'kw'], 'klima': ['btu', 'kod', 'bakim', 'montaj', 'tasarruf'], 'beyaz': ['karar', 'belirti', 'parca', 'liste'], 'tv': ['teshis', 'kod', 'karar', 'teslim'],
         'pc': ['saglik', 'veri', 'upgrade', 'paket'], 'tes': ['kacak', 'damla', 'acil', 'sure'], 'elk': ['kesit', 'maliyet', 'sigorta', 'acil'], 'gvn': ['depo', 'kesif', 'risk', 'bakim', 'alarm']}
NAMES = {
 'kombi': ['Alev Kombi', 'Sıcak Yuva Kombi', 'Termo Usta', 'Kor Isı', 'Yuva Kombi', 'Konfor Isı', 'Ateş Kombi', 'Isı Atölyesi'],
 'klima': ['Serin Klima', 'Esinti Klima', 'Zirve Soğutma', 'Bora Klima', 'Mavi Klima', 'İklim Atölyesi', 'Nefes Klima', 'Kuzey Soğutma'],
 'beyaz_esya': ['Beyaz Atölye', 'Usta Beyaz Eşya', 'Ev Servis', 'Özen Beyaz Eşya', 'Berrak Servis', 'Düzen Beyaz Eşya', 'Pırıl Servis', 'Sağlam Beyaz Eşya'],
 'elektronik': ['Devre Teknik', 'Piksel Servis', 'Sinyal Elektronik', 'Ekran Atölyesi', 'Çip Teknik', 'Voltaj Servis', 'Işık Elektronik', 'Nokta Teknik'],
 'bilgisayar': ['Bit Servis', 'Çekirdek Bilgisayar', 'Kod Teknik', 'Veri Atölyesi', 'Nano Bilgisayar', 'Sistem Servis', 'Bayt Teknik', 'Piksel PC'],
 'tesisat': ['Akış Tesisat', 'Damla Usta', 'Mavi Tesisat', 'Pınar Tesisat', 'Derin Tesisat', 'Boru Atölyesi', 'Berrak Tesisat', 'Çözüm Su'],
 'elektrik': ['Volt Atölyesi', 'Akım Elektrik', 'Işın Elektrik', 'Gerilim Usta', 'Kıvılcım Elektrik', 'Tel Elektrik', 'Aydın Elektrik', 'Amper Servis'],
 'guvenlik': ['Kale Güvenlik', 'Gözcü Sistem', 'Kalkan Güvenlik', 'Nöbet Alarm', 'Bekçi Kamera', 'Siper Güvenlik', 'Şahin Güvenlik', 'Çelik Alarm']}
CITIES = ['İzmir', 'Ankara', 'İstanbul', 'Bursa', 'Antalya', 'Adana', 'Konya', 'Kayseri', 'Eskişehir', 'Gaziantep']


def _mix(a, b, t):
    A = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    B = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(x + (y - x) * t):02x}' for x, y in zip(A, B))


# yön: (koyu mu, zeminler, mürekkep, vurgular, yazı tipleri(başlık), gövde fontları, yarıçap, btn, kart, alan, hw, ht, label)
D = {
 'cine': dict(dark=True, bgs=['#0b0b0c', '#0a0f14', '#100b0b', '#0b100c', '#0d0b14', '#0a1210'], ink='#f5f2ec', acs=['#ff5a1f', '#22d3ee', '#f43f5e', '#a3e635', '#fbbf24', '#38bdf8', '#fb7185', '#34d399', '#f97316', '#c084fc', '#2dd4bf', '#facc15', '#60a5fa', '#ef4444', '#e879f9', '#84cc16'],
              fd=['syne', 'sora', 'spacegrotesk', 'outfit', 'bricolage', 'archivoblack'], fb=['manrope', 'figtree', 'instrument'], r=16, btn='pill', card='lift', field='box', hw=800, ht='-.04em', lbl='Sinema'),
 'edit': dict(dark=False, bgs=['#f4efe6', '#f6f2ec', '#faf7f2', '#f3f1ec', '#f7f3f0', '#eef2ef', '#f2f4f7', '#faf5ee'], ink='#1a1612', acs=['#b4531f', '#0f766e', '#1d4ed8', '#be123c', '#6d28d9', '#166534', '#c2410c', '#0369a1', '#9d174d', '#a16207', '#0e7490', '#4d7c0f', '#b91c1c', '#7c3aed', '#115e59', '#9a3412'],
              fd=['fraunces', 'playfair', 'newsreader', 'dmserif'], fb=['manrope', 'figtree', 'instrument'], r=10, btn='pill', card='lift', field='line', hw=400, ht='-.035em', lbl='Editoryal'),
 'neon': dict(dark=True, bgs=['#070a12', '#0a0814', '#06100f', '#0c0a12', '#080d18'], ink='#e8ecff', acs=['#3b82f6', '#06b6d4', '#8b5cf6', '#10b981', '#f43f5e', '#f59e0b', '#ec4899', '#14b8a6', '#6366f1', '#22d3ee', '#a855f7', '#84cc16', '#0ea5e9', '#f97316', '#d946ef'],
              fd=['sora', 'spacegrotesk', 'outfit', 'intertight'], fb=['plex', 'manrope', 'figtree'], r=22, btn='pill', card='fill', field='pill', hw=700, ht='-.04em', lbl='Neon'),
 'lux': dict(dark=True, bgs=['#0d0c0a', '#0c0b0e', '#0a0d0c', '#100d0b', '#0b0c10'], ink='#efe7d6', acs=['#d8b567', '#c9a45c', '#e0b97a', '#b8935a', '#cfae6f', '#d4a373', '#bfa06a', '#c8a96b', '#d9b99b', '#9fb8a3', '#b9c4cf', '#e6c9a8', '#c6a15b', '#d7b98e', '#caa472'],
             fd=['fraunces', 'playfair', 'newsreader', 'dmserif'], fb=['manrope', 'instrument', 'figtree'], r=2, btn='line', card='line', field='line', hw=300, ht='-.02em', lbl='Lüks'),
}
ORDERS = [
 ['pstat', 'svc', 'tool0', 'proc', 'proof', 'shop', 'faq', 'pqc', 'book'],
 ['svc', 'pmq', 'proc', 'tool0', 'why', 'proof', 'shop', 'faq', 'book', 'pqc'],
 ['brands', 'svc', 'tool0', 'pstat', 'proc', 'ba', 'proof', 'faq', 'shop', 'pqc', 'book'],
 ['svc', 'tool0', 'why', 'proc', 'tool1', 'proof', 'areas', 'shop', 'faq', 'book', 'pqc'],
]
SVC = {'cine': ['bento', 'tiles', 'index'], 'edit': ['index', 'list2', 'grid'], 'neon': ['bento', 'grid', 'tiles'], 'lux': ['list2', 'index', 'grid']}
MBAR = ['fab', 'dock', 'pill', 'one', 'split', 'bubble', 'status', 'seg']
FT = ['cols', 'big', 'min', 'cen']


def extend(R, mk):
    cnt = {k: 0 for k in D}
    for i in range(62):
        dr = list(D)[(i + i // 8) % 4]
        d = D[dr]
        sec = SECT[i % 8]
        k = cnt[dr]
        cnt[dr] += 1
        nm = NAMES[sec][(i // 8) % 8]
        bg = d['bgs'][k % len(d['bgs'])]
        ac = d['acs'][k % len(d['acs'])]
        ink = d['ink']
        if d['dark']:
            pal = (bg, ink, _mix(bg, '#ffffff', .07), _mix(bg, '#000000', .35), ac)
        else:
            pal = (bg, ink, _mix(bg, '#000000', .06), _mix(ink, bg, .1), ac)
        fd = d['fd'][(k + i // 8) % len(d['fd'])]
        fb = d['fb'][(k * 2 + i) % len(d['fb'])]
        pre = TP[sec]
        tl = TOOLN[pre]
        tools = [f'{pre}.{tl[i % len(tl)]}', f'{pre}.{tl[(i + 1 + i // 8) % len(tl)]}']
        if tools[0] == tools[1]:
            tools[1] = f'{pre}.{tl[(i + 2) % len(tl)]}'
        order = ORDERS[(k + i // 8) % 4]
        if dr == 'cine' and 'pmq' in order:
            order = [t for t in order if t != 'pmq']
        svc = SVC[dr][k % 3]
        slug = f'p{i + 1:02d}-{dr}-{sec.replace("_", "-")}'
        R.append(mk(slug=slug, sector=sec, nm=nm, city=CITIES[(i * 3 + k) % 10], pal=pal, fd=fd, fb=fb, r=d['r'], btn=d['btn'], card=d['card'], field=d['field'],
                    logo=['sq', 'ci', 'ol', 'bar', 'tx'][(k + i) % 5] if dr != 'lux' else 'tx', em=(fd in ('playfair', 'newsreader') and dr in ('edit', 'lux')),
                    nav='premium', dir=dr, hero='p_' + dr, mbar=MBAR[(i + k) % 8], ft=FT[(k + i // 8) % 4], hidx=(i + k) % 5, tools=tools, tv0='abcd'[i % 4], tv1='abcd'[(i + 1) % 4],
                    svc=svc, proc=['line', 'cards', 'big', 'vert'][(i + k) % 4], proof=['cards', 'quote', 'wall'][(i + 2 * k) % 3], br=['wall', 'pills', 'ticker'][i % 3], faq=['side', 'stack'][i % 2],
                    book=['split', 'card', 'wizard', 'strip'][(i + k) % 4], order=order, hw=d['hw'], ht=d['ht'], dark=d['dark'], premium=True, cta='Teklif alın', imv=['im', 'im2', 'im3'][(i // 4) % 3],
                    head='tight' if dr in ('cine', 'neon') else ('light' if dr in ('edit', 'lux') else 'bold'),
                    style=f'Premium · {d["lbl"]} · {sec.replace("_", " ")}'))
    # mevcut 8 temayı premium sınıfına al (hareket katmanı + Teklif alın, fiyat bölümü yok)
    UP = {'1-kombi', '2-klima', '6-guvenlik', '08-kombi-kor', '09-kombi-cam', '10-klima-buz', '11-klima-poyraz', '12-klima-okyanus'}
    for r in R:
        if r['slug'] in UP:
            r.update(premium=True, cta='Teklif alın', dir='x')
            r['order'] = [t for t in r['order'] if t != 'price'] + (['shop'] if 'shop' not in r['order'] else [])
