"""Gerçek ücretsiz (Pexels lisansı) fotoğrafları indirir -> themes/img/<sektor>[2|3].jpg
İnternet erişimi olan makinede (hosting sunucusu) çalıştırılır:  python3 fetch_photos.py
Pexels lisansı: ticari kullanım serbest, atıf zorunlu değil. Kaynak kimlikleri PHOTOS içinde."""
import os, io, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'img')
PHOTOS = {  # sektör: [pexels foto id, ...] (ilk 3 kullanılır)
 'oto_servis': [8985615, 8986119, 32152037, 29284925, 4116224, 8985455],
 'oto_cekici': [17429097, 8931961, 10061763],
 'kuafor':     [13138585],
 'nakliye':    [7464232, 7464687],
 'tekstil':    [31047139, 31047138, 236748, 3965543],
 'eticaret':   [7857532, 7857542, 7289727, 7289725],
 'temizlik':   [6195273, 6197111],
 'guzellik':   [15866050],
}
def get(pid):
    u = 'https://images.pexels.com/photos/%d/pexels-photo-%d.jpeg?auto=compress&cs=tinysrgb&w=1600' % (pid, pid)
    r = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(r, timeout=40).read()
def main():
    from PIL import Image
    ok = 0
    for sec, ids in PHOTOS.items():
        got = []
        for pid in ids:
            if len(got) == 3: break
            try:
                im = Image.open(io.BytesIO(get(pid))).convert('RGB')
                w, h = im.size; t = 1280 / 800
                if w / h > t: nw = int(h * t); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
                else: nh = int(w / t); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
                got.append(im.resize((1280, 800)))
            except Exception as e:
                print('atlandı', sec, pid, e, file=sys.stderr)
        while got and len(got) < 3: got.append(got[len(got) % len(got)])
        for i, im in enumerate(got):
            im.save(os.path.join(OUT, sec + ('' if i == 0 else str(i + 1)) + '.jpg'), quality=82, optimize=True)
            ok += 1
    if ok: open(os.path.join(OUT, '.real'), 'w').write('1')
    print('yazılan dosya:', ok)
if __name__ == '__main__':
    main()
