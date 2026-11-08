# OnlineKaydet (panel çekirdeği)

ServisPlus panel kodunun ayrı çatalı. Canlı ServisPlus'a dokunmaz.

## Eklenenler
- `panel/servis_ayar.py`: firma bazlı servis ayarları (adımlar, öncesi/sonrası foto, müşteri/usta imzası), cihaz kataloğu, servis fişi PDF.
- `panel/firms.py`: paketler ve modül kapıları (`/api/admin/packages`, `/api/firm/package`), firma sahibi artık kendi veritabanında `admin`.
- `panel/server.py`: ayar kuralları `update_job` içinde uygulanır; firma ustaları giriş yapabilir (`firm_logins`); firma yöneticisi platform uçlarına giremez.
- `panel/notify.py`: İleti Merkezi sağlayıcısı.

## Test
    pip install fastapi motor mongomock-motor python-multipart pyjwt bcrypt python-dotenv requests email-validator reportlab
    python3 tests/test_servis_akis.py && python3 tests/test_sms_akis.py && python3 tests/test_paket.py
Testler sahte MongoDB (mongomock) ve sahte SMS sunucusuyla çalışır; gerçek MongoDB / gerçek SMS hesabıyla denenmedi.
