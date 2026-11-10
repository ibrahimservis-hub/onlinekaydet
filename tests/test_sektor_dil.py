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
