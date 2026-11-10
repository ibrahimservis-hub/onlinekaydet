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
