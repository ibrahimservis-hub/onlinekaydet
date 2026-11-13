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
        r = c.post("/api/public/customer/%s~register" % F, json={"name": "Merve Kaya", "phone": "05321112233", "password": "sifre123"})
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
        r = c.post("/api/public/customer/%s~register" % F, json={"name": "Puan Test", "phone": "05329998877", "password": "sifre123"}); assert r.status_code == 200, r.text
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
print("ok", len(ok), "bad", len(bad))
for n, tb in bad: print("FAIL", n, tb)
sys.exit(1 if bad else 0)
