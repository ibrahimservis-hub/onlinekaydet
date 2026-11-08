# Site temaları (30)

- `gen2.py` — 30 temayı üretir: `python3 gen2.py` (10 düzen × 8 sektör; her tema kendi renk, köşe ve yazı tipiyle). `panel/themes.json` aynı koşuda yazılır.
- `html/` — üretilmiş temalar. Bölümler `.ed data-nm` ile panelden düzenlenir; `__PORTAL_URL__` yayında firmanın müşteri portalı adresiyle değişir.
- `img/` — sektör görselleri (demo). Gerçek fotoğraf paketi gelince bu dosyalar aynı adlarla değiştirilir ve `gen2.py` yeniden çalıştırılır.
- `gen.py`, `t.css`, `t.js` — eski üretici (kullanımdan kalktı).
- Düzenler: Klasik Usta, Tam Fotoğraf, Editoryal, Teknik Katalog, Acil Hat, Fiyat Listesi, Önce/Sonra, Güven Rozetli, Bölge Odaklı, Parça Mağaza.
