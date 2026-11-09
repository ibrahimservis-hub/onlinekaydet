# Müşteri site temaları (30)

Firmaların onlinekaydet üzerinden yayınladığı site şablonları. Her tema tek dosyalık HTML'dir (yazı tipleri ve görseller gömülü).

- `gen3.py` — 30 temayı üretir: `python3 gen3.py` → `html/*.html`, `../panel/themes.json`, `../site/themes.json`, `g3/manifest.json`.
- `g3/recipes.py` — her temanın tarifi: menü, ilk ekran, mobil alt çubuk, alt bilgi, bölüm sırası, renk, yazı tipi, düğme/kart/alan stili, sektör araçları.
- `g3/tools.py` — 34 çalışan sektör aracı (hata kodu çözücü, BTU, kablo kesiti, tamir mi yeni mi, vb.). Sonuç "ustaya ilet" formuyla `/api/public/contact`'a gider.
- `g3/heroes.py`, `navs.py`, `sections.py`, `base.py`, `content.py` — bileşen kitaplığı. `fonts/` ve `img/` gömülen kaynaklar.
- Müşteri portalı girişi temalarda yoktur. Panel `brand_site` ile `__API_URL__`, firma adı ve telefonu yerleştirir.
- `gen2.py` eski üreticidir, artık kullanılmaz.
