import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'panel'))
import sektor_dil as d
import sektor


def test_every_sector_has_language():
    for k in sektor.SECTORS:
        assert k in d.ROWS or k in d.SADE or k not in d.ROWS, k


def test_labels_sector_specific():
    t = d.labels('kuafor')
    assert 'usta' not in ' '.join(t.values()).lower()
    assert t['Ustadan Para Aldım'] == 'Uzmandan Tahsilat'
    assert d.labels('nakliye')['Ustadan Para Aldım'] == 'Ekip Üyesinden Tahsilat'


def test_lex_shape():
    L = d.lex('avukat')
    assert L['kisi'][0] == 'Avukat' and len(L['cihaz']) == 2


def test_module_view():
    lab, hid = d.module_view('kuafor')
    assert lab['personel'] == 'Uzman / personel takibi' and 'bayi' in hid and 'qr' in hid
    assert d.module_view('kombi') == ({}, [])          # teknik servis değişmez
    assert d.module_view('oto_cekici')[0]['takip'] == 'Canlı araç takibi'
    for k in d.ROWS:
        if k in d.SADE: continue
        l, h = d.module_view(k)
        assert l.get('servis'), k
        if d.family(k) in ('randevu', 'siparis', 'yol', 'proje', 'kurs'): assert 'usta' not in ' '.join(l.values()).lower(), k


def test_randevu_family_panel_texts():
    """Kuaför/güzellik panelinde ana sayfa, sayfa başlıkları ve tablolarda teknik servis metni kalmamalı."""
    t = d.labels('kuafor')
    for src in ('Saha Operasyon Merkezi', 'Servis İş Emirleri', 'Marka Kütüphanesi', 'Yeni Marka', 'Yeni Parça', 'Yedek parça yok', 'Garanti Bitiş', 'Garanti talebi yok'):
        assert src in t, src
    joined = ' '.join(t.values()).lower()
    for bad in ('usta', 'garanti', 'servis', 'atölye', 'parça', 'marka', 'saha'):
        assert bad not in joined, (bad, [v for v in t.values() if bad in v.lower()])
    # klinik/diğer randevu işleri de 'salon' kelimesi görmesin (nötr dil)
    assert 'salon' not in ' '.join(d.labels('dis_klinigi').values()).lower()
    h = d.hide('kuafor')
    for x in ('Talep Rehberi', 'Atölye (Hizmet Teslim)', 'Bayi Portalı', 'Yeni bayilik başvurusu', 'Uzmandan Para Aldım'):
        assert x in h, x
    assert d.hide('kombi') == [] and 'Talep Rehberi' not in d.hide('oto_servis')


def test_randevu_no_chained_labels():
    """Bir etiketin karşılığı başka bir etiketin anahtarı olmamalı (zincirleme çeviri 'Online Online' gibi çift ad üretir)."""
    for k in ('kuafor', 'guzellik', 'tirnak_studyo', 'spa_hamam', 'dis_klinigi'):
        t = d.labels(k)
        for src, dst in t.items():
            assert dst not in t or dst == src, (k, src, dst)
    r = d.rx('kuafor')
    import re
    assert re.sub(r[0][0], r[0][1], 'Servis ₺3.600,00 • Diğer ₺0,00') == 'Hizmet ₺3.600,00 • Diğer ₺0,00'
    assert re.sub(r[1][0], r[1][1].replace('$1', r'\1'), '2 değerlendirilen servis') == '2 değerlendirilen randevu'
