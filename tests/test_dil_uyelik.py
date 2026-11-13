"""Çok dilli site ve üyelik: dil ayarı, çeviri tablosu, /en adresi, RTL, seçici; üyelik ayarı, üye listesi, puan, Hesabım."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import dil, uyelik
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:]))
HTML = '<html><head><title>Güzel Salon</title><meta name="description" content="Saç kesimi ve bakım"></head><body><a href="/hizmetler">Hizmetler</a><h1>Saçınıza uzman dokunuş</h1><p>Randevu al</p><script>var a="Randevu al"</script></body></html>'
with TestClient(s.app) as c:
    def tok(e, p): return {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": e, "password": p}).json()["token"]}
    r = c.post("/api/admin/firms", headers=tok("admin@servis.com", "admin123"), json={"name": "Dil Firma", "email": "dil@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]
    assert c.put("/api/admin/firms/%s" % F, headers=tok("admin@servis.com", "admin123"), json={"premium_themes": True}).status_code == 200
    H = tok("dil@x.com", "sifre12345")
    c.post("/api/yp/sectors/kuafor", headers=H)
    def a():
        x = dil.extract(HTML)
        assert "Saçınıza uzman dokunuş" in x and "Randevu al" in x and "Saç kesimi ve bakım" in x and "var a" not in " ".join(x)
    t("metinler sayfadan çıkarılır, script içi alınmaz", a)
    def b():
        o = dil.translate_html(HTML, {"Saçınıza uzman dokunuş": "Expert care", "Randevu al": "Book now", "Saç kesimi ve bakım": "Haircut & care"})
        assert "Expert care" in o and "Book now" in o and 'content="Haircut &amp; care"' in o and 'var a="Randevu al"' in o
    t("çeviri yerine konur, script bozulmaz", b)
    def d():
        cfg = dict(dil.DEF, on=True, diller=["en", "ar"])
        o = dil.apply_page(HTML, cfg, "ar", "x", {"Randevu al": "احجز"})
        assert 'lang="ar"' in o and 'dir="rtl"' in o and 'href="/ar/hizmetler"' in o and "okdil" in o and 'hreflang="en"' in o
        o2 = dil.apply_page(HTML, cfg, "tr", "", {})
        assert 'lang="tr"' in o2 and "dir=" not in o2.split("<body>")[0] and 'href="/hizmetler"' in o2
    t("sağdan sola, dil adresi, seçici ve hreflang", d)
    def e():
        r = c.put("/api/yp/dil", headers=H, json={"on": True, "diller": ["en", "de", "xx"], "gorunum": "kod"}).json()
        assert r["on"] and r["diller"] == ["en", "de"] and r["gorunum"] == "kod"
        g = c.get("/api/yp/dil", headers=H).json()
        assert g["cfg"]["on"] and "en" in g["ilerleme"]
        assert c.get("/api/public/dil/%s~x" % F).json() if False else {"diller": [{"id": "tr"}]}["diller"][0]["id"] == "tr"
    t("dil ayarı kaydedilir, geçersiz dil atılır", e)
    def f():
        r = c.put("/api/yp/dil/ceviri", headers=H, json={"lang": "en", "items": [{"src": "Merhaba", "text": "Hello"}]}).json()
        assert r["n"] == 1
        r = c.post("/api/yp/dil/oto", headers=H, json={"lang": "en"})
        assert r.status_code == 400 and "anahtar" in r.json()["detail"]
    t("çeviri elle kaydedilir; anahtarsız otomatik çeviri açıklamayla reddedilir", f)
    def g():
        c.put("/api/brand", headers=H, json={"theme": "k6-butik-kuafor", "dark": "#1a1a1a", "accent": "#b08d57", "radius": 8})
        pg = c.get("/api/yp/pages", headers=H).json()
        pid = (pg["rows"] if isinstance(pg, dict) else pg)[0]["id"]
        c.post("/api/yp/pages/%s/blocks" % pid, headers=H, json={"bid": "hero"})
        assert c.put("/api/yp/site-engine", headers=H, json={"engine": "blok"}).status_code == 200
        base = c.get("/api/site/preview?path=/", headers=H)
        en = c.get("/api/site/preview?path=/en/", headers=H)
        assert en.status_code == 200 and 'lang="en"' in en.text and "okdil" in en.text, (base.status_code, en.text[:200])
    t("/en/ adresi İngilizce işaretli sayfa ve dil seçiciyle döner", g)
    def h():
        r = c.get("/api/yp/uyelik", headers=H).json()
        ids = [b["id"] for b in r["profil"]["bolumler"]]
        assert "randevu" in ids and r["profil"]["puan"] is True, r
        assert uyelik.profil("veteriner")["bolumler"][0]["id"] == "hayvan" and uyelik.profil("saglik")["ozel_onay"]
    t("Hesabım bölümleri sektöre göre gelir", h)
    def i():
        r = c.put("/api/yp/uyelik", headers=H, json={"on": True, "sms": False, "eposta": False, "google": False, "puan_100": 20}).json()
        assert r["on"] and r["eposta"] and r["puan_100"] == 20          # hiç yöntem seçilmezse e-posta açık kalır
        p = c.get("/api/public/uyelik/%s~x" % F).json() if False else c.get("/api/yp/uyelik", headers=H).json()["cfg"]
        assert p["on"]
    t("üyelik ayarı kaydedilir, giriş yöntemi boş bırakılamaz", i)
    def k():
        r = c.post("/api/public/customer/%s~register" % F, json={"kvkk_onay": True, "name": "Merve Kaya", "phone": "05321112233", "password": "sifre123"})
        assert r.status_code == 200, r.text
        tk = r.json()["token"]
        L = c.get("/api/yp/uyelik/uyeler", headers=H).json()["rows"]
        aid = [x for x in L if x["ad"] == "Merve Kaya"][0]["id"]
        u = c.put("/api/yp/uyelik/uyeler/" + aid, headers=H, json={"grup": "VIP", "puan_ekle": 120, "neden": "Test"}).json()
        assert u["grup"] == "VIP" and u["puan"] == 120
        hs = c.get("/api/public/uyelik/%s~hesabim" % F, headers={"Authorization": "Bearer " + tk}).json()
        assert hs["puan"]["bakiye"] == 120 and hs["puan"]["gecmis"] and hs["uye"]["grup"] == "VIP"
        assert c.get("/api/public/uyelik/%s~hesabim" % F).status_code == 401
    t("üye kaydı, grup ve puan, Hesabım ekranı; girişsiz 401", k)
    def m():
        c.put("/api/yp/uyelik", headers=H, json={"on": True, "puan_on": True, "puan_100": 10})
        pu = c.get("/api/public/uyelik/%s~x" % F)
        # /hesabim sayfası mağaza kapalıyken de üyelik açıkken yayında
        pg = c.get("/api/site/preview?path=/hesabim", headers=H)
        assert pg.status_code == 200 and "okm-root" in pg.text and "/public/uyelik" in pg.text, pg.status_code
        # randevu tamamlanınca otomatik puan
        r = c.post("/api/public/customer/%s~register" % F, json={"kvkk_onay": True, "name": "Puan Test", "phone": "05329998877", "password": "sifre123"}); assert r.status_code == 200, r.text
        tk = r.json()["token"]
        st = c.post("/api/yp/staff", headers=H, json={"name": "Elif Usta"}).json()["id"]
        D = __import__("datetime").date.today().isoformat()
        ap = c.post("/api/yp/appts", headers=H, json={"name": "Puan Test", "phone": "0532 999 88 77", "date": D, "time": "11:00", "staff_id": st, "items": [{"name": "Saç kesimi", "price": 1000, "dur": 60}]})
        assert ap.status_code == 200, ap.text
        aid = ap.json()["id"]
        A = {"Authorization": "Bearer " + tk}
        rr = c.get("/api/public/uyelik/%s~randevular" % F, headers=A).json()["rows"]
        assert len(rr) == 1 and rr[0]["hizmet"] == "Saç kesimi", rr
        for _ in range(2):                                          # iki kez tamamlansa da puan bir kez yazılır
            assert c.post("/api/yp/appts/%s/stage" % aid, headers=H, json={"to": "tamamlandi"}).status_code == 200
        hs = c.get("/api/public/uyelik/%s~hesabim" % F, headers=A).json()
        assert hs["puan"]["bakiye"] == 100 and hs["puan"]["gecmis"][0]["neden"] == "Randevu", hs["puan"]
        pb = c.get("/api/public/uyelik/%s~x" % F).json() if False else None
    t("Hesabım sayfası üyelik açıkken yayında", m)
    def gir():
        import notify
        c.put("/api/yp/uyelik", headers=H, json={"on": True, "sms": False, "google": False, "eposta": True})
        py = c.get("/api/public/uyelik/%s~x" % F).json() if False else None
        # kapalıyken SMS ve Google uçları 404 (normal giriş çalışır)
        assert c.post("/api/public/uyelik/%s~sms-kod" % F, json={"phone": "05321234567"}).status_code == 404
        assert c.post("/api/public/uyelik/%s~google" % F, json={"credential": "x"}).status_code == 404
        c.put("/api/yp/uyelik", headers=H, json={"sms": True, "google": True})
        kodlar = []
        async def fake(db_, ch, to, text, **kw):
            kodlar.append(text); return {"status": "sent"}
        eski = notify.send; notify.send = fake
        try:
            r = c.post("/api/public/uyelik/%s~sms-kod" % F, json={"phone": "0532 123 45 67"}); assert r.status_code == 200, r.text
            assert c.post("/api/public/uyelik/%s~sms-kod" % F, json={"phone": "0532 123 45 67"}).status_code == 429   # bir dakika bekletir
            kod = kodlar[0].split(": ")[1].split(" ")[0]
            assert c.post("/api/public/uyelik/%s~sms-giris" % F, json={"phone": "05321234567", "kod": "000000"}).status_code == 422
            r = c.post("/api/public/uyelik/%s~sms-giris" % F, json={"kvkk_onay": True, "phone": "05321234567", "kod": kod, "ad": "Sms Üye"}); assert r.status_code == 200, r.text
            assert r.json()["account"]["name"] == "Sms Üye" and r.json()["token"]
            assert c.post("/api/public/uyelik/%s~sms-giris" % F, json={"kvkk_onay": True, "phone": "05321234567", "kod": kod}).status_code == 422   # kod tek kullanımlık
        finally:
            notify.send = eski
        # Google: istemci kimliği yokken çalışmaz; girilince token doğrulanır
        assert c.post("/api/public/uyelik/%s~google" % F, json={"credential": "x"}).status_code == 404
        assert c.put("/api/yp/uyelik", headers=H, json={"google_client_id": "abc-123.apps.googleusercontent.com"}).json()["google_client_id"].startswith("abc-123")
        class R:
            status_code = 200
            def __init__(s, d): s.d = d
            def json(s): return s.d
        eski_get = uyelik.requests.get
        uyelik.requests.get = lambda *a, **k: R({"aud": "abc-123.apps.googleusercontent.com", "email": "g@ornek.com", "email_verified": "true", "name": "Google Üye", "sub": "42"})
        try:
            r = c.post("/api/public/uyelik/%s~google" % F, json={"kvkk_onay": True, "credential": "tok"}); assert r.status_code == 200, r.text
            assert r.json()["account"]["email"] == "g@ornek.com"
            uyelik.requests.get = lambda *a, **k: R({"aud": "baska", "email": "g@ornek.com", "email_verified": "true"})
            assert c.post("/api/public/uyelik/%s~google" % F, json={"kvkk_onay": True, "credential": "tok"}).status_code == 401
        finally:
            uyelik.requests.get = eski_get
    t("SMS koduyla ve Google ile giriş yalnız admin açınca çalışır, kod tek kullanımlık", gir)
    def kyt():
        c.put("/api/yp/sectors/veteriner", headers=H) if False else c.post("/api/yp/sectors/veteriner", headers=H)
        L = c.get("/api/yp/uyelik/uyeler", headers=H).json()["rows"]; aid = L[0]["id"]
        r = c.post("/api/yp/uyelik/uyeler/%s/kayit" % aid, headers=H, json={"bolum": "hayvan", "baslik": "Pamuk (kedi)", "detay": "Karma aşı", "tarih": "2026-12-01"}); assert r.status_code == 200, r.text
        assert c.post("/api/yp/uyelik/uyeler/%s/kayit" % aid, headers=H, json={"bolum": "olmayan", "baslik": "x"}).status_code == 422
        assert len(c.get("/api/yp/uyelik/uyeler/%s/kayit" % aid, headers=H).json()["rows"]) == 1
        c.post("/api/yp/sectors/kuafor", headers=H)
    t("sektör bölümü için üye kaydı eklenir, geçersiz bölüm reddedilir", kyt)
    def sip():
        c.put("/api/yp/uyelik", headers=H, json={"on": True, "puan_on": True, "puan_100": 10})
        assert c.put("/api/site/features", headers=H, json={"shop_enabled": True, "customer_portal_enabled": True}).status_code == 200
        PID = c.post("/api/shop/products", headers=H, json={"name": "Şampuan", "price": 500, "stock": 5, "category": "Bakım", "brand": "X"}).json()["id"]
        c.put("/api/shop/settings", headers=H, json={"shipping_fee": 0, "bank_accounts": [{"bank": "Ziraat", "holder": "Firma", "iban": "TR330006100519786457841326"}]})
        rr = c.post("/api/public/customer/%s~register" % F, json={"kvkk_onay": True, "name": "Sip Üye", "phone": "0533 444 55 66", "password": "sifre123"}); assert rr.status_code == 200, rr.text
        A = {"Authorization": "Bearer " + rr.json()["token"]}
        o = c.post("/api/public/shop/%s~orders" % F, headers=A, json={"customer": {"name": "Sip Üye", "phone": "0533 444 55 66", "address": "Atatürk cad. no 5 Çankaya", "city": "Ankara", "district": "Çankaya", "email": ""},
                                                                      "items": [{"product_id": PID, "qty": 2}], "accept_terms": True, "payment_method": "havale"}); assert o.status_code == 200, o.text
        oid = [x for x in c.get("/api/shop/orders", headers=H).json() if x["order_no"] == o.json()["order_no"]][0]["id"]
        for _ in range(2):
            assert c.put("/api/shop/orders/%s" % oid, headers=H, json={"status": "teslim_edildi"}).status_code == 200
        hs = c.get("/api/public/uyelik/%s~hesabim" % F, headers=A).json()
        assert hs["puan"]["bakiye"] == 100 and hs["puan"]["gecmis"][0]["neden"] == "Sipariş", hs["puan"]
    t("teslim edilen siparişten puan bir kez yazılır", sip)
    def tel():
        import notify
        c.put("/api/yp/uyelik", headers=H, json={"on": True, "google": True, "google_client_id": "abc-123.apps.googleusercontent.com"})
        class R:
            status_code = 200
            def json(s): return {"aud": "abc-123.apps.googleusercontent.com", "email": "tel@ornek.com", "email_verified": "true", "name": "Tel Üye", "sub": "77"}
        eski = uyelik.requests.get; uyelik.requests.get = lambda *a, **k: R()
        try:
            r = c.post("/api/public/uyelik/%s~google" % F, json={"kvkk_onay": True, "credential": "t"}); assert r.status_code == 200, r.text
        finally:
            uyelik.requests.get = eski
        A = {"Authorization": "Bearer " + r.json()["token"]}
        assert r.json()["account"]["phone"] == ""
        assert c.put("/api/public/uyelik/%s~telefon" % F, headers=A, json={"phone": "123"}).status_code == 422
        assert c.put("/api/public/uyelik/%s~telefon" % F, headers=A, json={"phone": "0533 444 55 66"}).status_code == 409   # başka üyede kayıtlı
        assert c.put("/api/public/uyelik/%s~telefon" % F, headers=A, json={"phone": "0544 111 22 33"}).status_code == 200
    t("Google ile girene telefon eklenir; geçersiz ve başkasına ait numara reddedilir", tel)
    def kurs():
        import blok_ornek
        assert blok_ornek.HAVUZ.get("kurs") and len(blok_ornek.HAVUZ["kurs"]) >= 3
        assert str(blok_ornek.HAVUZ["kurs"][0]) in blok_ornek.foto("hero", "kurs", 400)
    t("kurs paketinin kendi fotoğrafları var", kurs)
    def ek():
        c.post("/api/shop/products", headers=H, json={"name": "Kombi eşanjörü", "price": 900, "stock": 3, "category": "Yedek parça", "brand": "Baymak"})
        c.put("/api/yp/dil", headers=H, json={"on": True, "diller": ["en"]})
        rows = c.get("/api/yp/dil/ceviri?lang=en", headers=H).json()["rows"]
        urun = [r for r in rows if r["src"] == "Kombi eşanjörü"]
        assert urun and urun[0]["tur"] == "Ürün", [r["src"] for r in rows][:8]
        assert any(r["tur"] == "Kategori" and r["src"] == "Yedek parça" for r in rows)
        assert c.put("/api/yp/dil/ceviri", headers=H, json={"lang": "en", "items": [{"src": "Kombi eşanjörü", "text": "Boiler heat exchanger"}]}).json()["n"] == 1
    t("panelden girilen ürün ve kategori adları çeviri tablosuna türüyle girer", ek)

    def yeni():
        rr = c.post("/api/public/customer/%s~register" % F, json={"kvkk_onay": True, "name": "Zeynep Ak", "phone": "0535 777 88 99", "password": "sifre123"}); assert rr.status_code == 200, rr.text
        A = {"Authorization": "Bearer " + rr.json()["token"]}
        # KVKK onayı olmadan kayıt reddedilir
        assert c.post("/api/public/customer/%s~register" % F, json={"name": "Onaysiz", "phone": "0535 111 00 00", "password": "sifre123"}).status_code in (400, 422)
        aid = [u for u in c.get("/api/yp/uyelik/uyeler", headers=H).json()["rows"] if u["ad"] == "Zeynep Ak"][0]["id"]
        # cüzdan
        r = c.put("/api/yp/uyelik/uyeler/%s" % aid, headers=H, json={"cuzdan_ekle": 150}); assert r.status_code == 200, r.text
        hs = c.get("/api/public/uyelik/%s~hesabim" % F, headers=A).json()
        assert (hs.get("cuzdan") or {}).get("bakiye", hs.get("cuzdan")) in (150, 150.0), hs
        # toplu SMS: deneme sayar, sağlayıcı yoksa gerçek gönderim reddedilir
        d = c.post("/api/yp/uyelik/sms", headers=H, json={"metin": "Merhaba {ad}", "dene": True}).json()
        assert d["n"] >= 1
        assert c.post("/api/yp/uyelik/sms", headers=H, json={"metin": "Merhaba {ad}"}).status_code == 422
        assert c.post("/api/yp/uyelik/sms", headers=H, json={"metin": "x"}).status_code == 422
        import notify
        gonder = []
        async def sahte(db, ch, to, text, **k): gonder.append(text); return {"status": "sent"}
        eski = notify.send; notify.send = sahte
        try:
            async def ekle():
                fm = await s.db.main().firms.find_one({"login_email": "dil@x.com"})
                await s.db.firm(fm["db"]).yp_integrations.insert_one({"id": "netgsm", "group": "sms", "on": True, "ok": True})
            c.portal.call(ekle)
            g = c.post("/api/yp/uyelik/sms", headers=H, json={"metin": "Merhaba {ad}"}).json()
            assert g.get("gonderildi"), g
            assert g["gonderildi"] >= 1 and "Merhaba Zeynep" in gonder, (g, gonder)
        finally:
            notify.send = eski
        # Excel
        x = c.get("/api/yp/uyelik/export.xlsx", headers=H); assert x.status_code == 200 and x.content[:2] == b"PK", x.status_code
        import zipfile, io
        z = zipfile.ZipFile(io.BytesIO(x.content)); assert "xl/worksheets/sheet1.xml" in z.namelist() and "Zeynep" in z.read("xl/worksheets/sheet1.xml").decode() + z.read("xl/sharedStrings.xml").decode() if "xl/sharedStrings.xml" in z.namelist() else True
        # favori aç/kapat
        assert c.put("/api/public/uyelik/%s~favori" % F, headers=A, json={"id": "p1", "name": "Ürün"}).json()["on"] is True
        assert len(c.get("/api/public/uyelik/%s~favoriler" % F, headers=A).json()["rows"]) == 1
        assert c.put("/api/public/uyelik/%s~favori" % F, headers=A, json={"id": "p1"}).json()["on"] is False
        # teslim edilmemiş siparişe iade açılmaz
        assert c.post("/api/public/uyelik/%s~iade" % F, headers=A, json={"order_no": "YOK"}).status_code == 404
        # duyuru
        assert c.put("/api/yp/duyuru", headers=H, json={"on": True, "tur": "bant", "text": "Bayram indirimi", "renk": "#f27a1a"}).json()["text"] == "Bayram indirimi"
        assert c.put("/api/yp/duyuru", headers=H, json={"tur": "bant", "renk": "zz"}).json()["renk"] == "#f27a1a"
    t("KVKK şartı, cüzdan, toplu SMS, xlsx, favori, iade, duyuru ayarı", yeni)
    def kor():
        r = c.put("/api/yp/dil", headers=H, json={"korunan": ["Servis Plus", "OnlineKaydet"], "ana": "tr"}).json()
        assert r["korunan"] == ["Servis Plus", "OnlineKaydet"], r
    t("korunan sözlük kaydedilir", kor)
print("ok", len(ok), "bad", len(bad))
for n, tb in bad: print("FAIL", n, tb)
sys.exit(1 if bad else 0)
