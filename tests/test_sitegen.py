"""Otomatik site: profil bilgileri temaya yerleşir, iç sayfalar üretilir, slider/galeri/logo, sitemap, düzenleyici uyumu."""
import sys, os, base64, io
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-600:]))
def png(color):
    from PIL import Image
    b = io.BytesIO(); Image.new("RGB", (900, 500), color).save(b, "PNG"); return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ali Veli", "phone": "05524165755", "sector": "Kombi"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    ADM = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    def dom():
        fid = [f for f in c.get("/api/admin/firms", headers=ADM).json().get("firms", []) if f.get("demo")][0]
        async def go():
            await s.db.main().firm_domains.insert_one({"id": "d9", "domain": "otomatik-site.com", "firm_id": fid["id"], "db": s.db.firm_db_name(fid["id"]), "status": "yayinda"})
        c.portal.call(go)
        import domains; domains._cache["t"] = 0
    dom()
    def pub(p): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers={"Host": "otomatik-site.com"})
    def a():
        r = c.get("/api/site/profile", headers=H); assert r.status_code == 200, r.text
        d = r.json(); assert d["has_theme"] and d["sector"] == "kombi" and len(d["default_services"]) >= 5
        names = [p["kind"] for p in d["pages"]]; assert "about" in names and "contact" in names and names.count("service") >= 5, names
        assert len(d["pages"]) >= 10, len(d["pages"])
        assert pub("/nasil-calisiyoruz").status_code == 200
    t("profil okunur; sektör varsayılanlarıyla 10+ sayfa üretilir", a)
    def b():
        r = pub("/"); assert r.status_code == 200 and "905524165755" in r.text and "905320000000" not in r.text
        assert "wa.me/905524165755" in r.text
    t("ana sayfada telefon ve WhatsApp otomatik yerleşir", b)
    def lg():
        assert c.put("/api/site/logo", headers=H, json={"data": png("red")}).status_code == 200
        r = pub("/"); assert 'class="spx-logo"' in r.text and "/api/public/site-logo?v=" in r.text
        r = c.get("/api/public/site-logo", headers={"Host": "otomatik-site.com"}); assert r.status_code == 200 and r.headers["content-type"].startswith("image/png"), r.status_code
    t("logo yüklenince başlıkta otomatik görünür ve adresten servis edilir", lg)
    def pr():
        s1 = c.post("/api/site/image", headers=H, json={"data": png("blue")}).json(); s2 = c.post("/api/site/image", headers=H, json={"data": png("green"), "kind": "gallery"}).json()
        assert len(s1["k"]) == 16; S["k1"], S["k2"] = s1["k"], s2["k"]
        body = {"whatsapp": "0555 111 22 33", "email": "a@b.com", "address": "Cumhuriyet Mah. 5. Sok. No:3, Bornova İzmir", "hours": "Her gün 09:00 – 20:00", "slogan": "Kombiniz bizde emin ellerde", "city": "İzmir",
                "about": "Biz iyi servisiz.\n\nİkinci paragraf.", "services": [{"t": "Kombi bakımı", "d": "Yıllık bakım yaparız."}, {"t": "Petek temizliği", "d": "Cihazla."}],
                "faq": [{"q": "Kaça yapıyorsunuz?", "a": "Arayın."}], "regions": "Bornova, Karşıyaka\\nBuca".replace("\\n", "\n"),
                "social": {"instagram": "instagram.com/firma", "evil": "x"}, "slides": [{"k": S["k1"], "t": "Kış kampanyası", "d": "Bakım %20 indirimli"}, {"k": "0" * 16}], "gallery": [{"k": S["k2"]}]}
        r = c.put("/api/site/profile", headers=H, json=body); assert r.status_code == 200, r.text
        d = c.get("/api/site/profile", headers=H).json(); assert len(d["profile"]["slides"]) == 1 and d["profile"]["regions"] == ["Bornova", "Karşıyaka", "Buca"] and "evil" not in d["profile"]["social"]
    t("profil kaydedilir (geçersiz resim/alan ayıklanır)", pr)
    def home():
        r = pub("/").text
        assert "wa.me/905551112233" in r and "Cumhuriyet Mah. 5. Sok. No:3, Bornova İzmir" in r and "Her gün 09:00 – 20:00" in r
        assert "Kombiniz bizde emin ellerde" in r and 'class="spx-sl"' in r and "Kış kampanyası" in r and "/api/public/site-img/" + S["k1"] in r
        assert 'href="/hakkimizda"' in r and "instagram.com/firma" in r
    t("slogan, adres, saat, slider ve menü bağlantıları ana sayfaya yerleşir", home)
    def pages():
        for p, needle in [("/hakkimizda", "Biz iyi servisiz"), ("/hizmetlerimiz", "Petek temizliği"), ("/sss", "Kaça yapıyorsunuz"), ("/iletisim", "a@b.com"), ("/galeri", "site-img/" + S["k2"]),
                          ("/hizmet-bolgeleri", "Bornova"), ("/hizmet-kombi-bakimi", "Yıllık bakım yaparız"), ("/bolge-bornova", "Bornova bölgesinde"), ("/bolge-buca", "Buca")]:
            r = pub(p); assert r.status_code == 200 and needle in r.text, (p, r.status_code)
            assert 'id="mn"' in r.text and "Alt bilgi" in r.text and "Hemen arayın" in r.text, p
        r = pub("/iletisim").text; assert "maps.google.com/maps?q=" in r and 'href="/#randevu"' in r
    t("hakkımızda/hizmetler/SSS/iletişim/galeri/bölge/hizmet sayfaları yayınlanır (tema menüsüyle)", pages)
    def sm():
        r = pub("/sitemap.xml"); assert r.status_code == 200 and "application/xml" in r.headers["content-type"] and "https://otomatik-site.com/bolge-buca" in r.text and r.text.count("<loc>") >= 10
        assert "Sitemap: https://otomatik-site.com/sitemap.xml" in pub("/robots.txt").text
    t("sitemap.xml ve robots.txt üretilir", sm)
    def pv():
        r = c.get("/api/site/preview?path=/", headers=H); assert r.status_code == 200 and "data:image/jpeg;base64" in r.text and "/api/public/site-img/" not in r.text
        r = c.get("/api/site/preview?path=/hakkimizda", headers=H); assert r.status_code == 200 and "Biz iyi servisiz" in r.text
        assert c.get("/api/site/preview?path=/yok-boyle", headers=H).status_code == 404
    t("panel önizlemesi görselleri gömülü verir", pv)
    def ed():
        d = c.get("/api/site/edit?page=hakkimizda", headers=H).json(); assert not d["custom"] and "Biz iyi servisiz" in d["html"]
        assert any(p.get("auto") for p in d["pages"])
        h = d["html"].replace("Biz iyi servisiz", "DEĞİŞTİ METİN")
        assert c.put("/api/site/edit", headers=H, json={"page": "hakkimizda", "html": h}).status_code == 200
        assert "DEĞİŞTİ METİN" in pub("/hakkimizda").text
        d = c.get("/api/site/edit", headers=H).json(); assert not d["custom"] and "data:image/jpeg;base64" in d["html"]
        h2 = d["html"].replace("Kış kampanyası", "Yaz kampanyası")
        assert c.put("/api/site/edit", headers=H, json={"html": h2}).status_code == 200
        r = pub("/").text
        assert "Yaz kampanyası" in r and 'src="data:image/jpeg' not in r and "/api/public/site-img/" + S["k1"] in r
        assert 'href="/sss"' in pub("/hakkimizda").text
    t("otomatik sayfa düzenleyicide açılıp kaydedilir; görseller kaydederken kısa adrese döner", ed)
    def rs():
        assert c.delete("/api/site/edit?page=hakkimizda", headers=H).status_code == 200
        assert "Biz iyi servisiz" in pub("/hakkimizda").text
    t("sayfa sıfırlanınca otomatik haline döner", rs)
    def lay():
        c.delete("/api/site/edit", headers=H)
        bl = c.get("/api/site/blocks", headers=H).json()["blocks"]; names = [b["name"] for b in bl]
        assert "Hizmetler" in names and "Slider" in names and len(names) >= 6, names
        S["names"] = names
        d = c.get("/api/site/profile", headers=H).json()["profile"]
        hide = "Yorumlar" if "Yorumlar" in names else names[-1]; S["hide"] = hide
        order = [n for n in names if n != "Slider"]; order.insert(0, "Slider")
        d["layout"] = {"order": order, "hidden": [hide]}
        assert c.put("/api/site/profile", headers=H, json=d).status_code == 200
        r = pub("/").text
        assert 'data-nm="%s"' % hide not in r and r.index('data-nm="Slider"') < r.index('data-nm="Hizmetler"')
        assert 'data-nm="Menü"' in r and 'data-nm="Alt bilgi"' in r
        bl2 = c.get("/api/site/blocks", headers=H).json()["blocks"]; assert bl2[0]["name"] == "Slider" and [b for b in bl2 if b["name"] == hide][0]["hidden"]
    t("bölümler sürüklenip sıralanır, gizlenir; menü/alt bilgi sabit kalır", lay)
    def txt():
        tx = c.get("/api/site/block-text?name=Hizmetler", headers=H).json()["texts"]; assert len(tx) >= 3
        i = tx[0]["i"]; old = tx[0]["text"]
        d = c.get("/api/site/profile", headers=H).json()["profile"]
        th = c.get("/api/brand", headers=H).json()["brand"]["theme"]
        d["edits"] = {th: {"Hizmetler": {str(i): "ÖZEL BAŞLIK METNİ"}}}
        assert c.put("/api/site/profile", headers=H, json=d).status_code == 200
        assert "ÖZEL BAŞLIK METNİ" in pub("/").text
        tx2 = c.get("/api/site/block-text?name=Hizmetler", headers=H).json()["texts"]; assert tx2[0]["text"] == "ÖZEL BAŞLIK METNİ" and tx2[0]["orig"] == old
        d["edits"] = {}; c.put("/api/site/profile", headers=H, json=d); assert "ÖZEL BAŞLIK METNİ" not in pub("/").text
    t("temanın herhangi bir bölümündeki metin düzenlenir ve eski haline getirilir", txt)
    def ex():
        d = c.get("/api/site/profile", headers=H).json()["profile"]
        d["extra_pages"] = [{"title": "Kampanyalar", "body": "Bu ay bakım %20 indirimli.\n\nDetay için arayın.", "menu": True}]
        d["hidden_pages"] = ["nasil-calisiyoruz"]
        assert c.put("/api/site/profile", headers=H, json=d).status_code == 200
        r = pub("/kampanyalar"); assert r.status_code == 200 and "%20 indirimli" in r.text
        assert 'href="/kampanyalar"' in pub("/").text or 'href="/kampanyalar"' in pub("/hakkimizda").text
        assert "Nasıl Çalışıyoruz" not in pub("/hakkimizda").text
        pg = c.get("/api/site/profile", headers=H).json()["pages"]; assert any(p["slug"] == "nasil-calisiyoruz" and p["hidden"] for p in pg) and any(p["slug"] == "kampanyalar" for p in pg)
    t("müşteri yeni sayfa ekler, otomatik sayfayı gizler", ex)
    def nochip():
        assert "Müşteri girişi" not in pub("/").text and "Servis takibi" not in pub("/").text
        assert "Müşteri girişi" not in c.get("/api/site/preview?path=/", headers=H).text
    t("sitede 'Servis takibi · Müşteri girişi' etiketi yok", nochip)
    def clr():
        d = c.get("/api/site/profile", headers=H).json()["profile"]
        d.update({"whatsapp": "", "address": "", "hours": ""})
        assert c.put("/api/site/profile", headers=H, json=d).status_code == 200
        r = pub("/").text
        for bad_ in ["Atatürk Cad", "Hafta içi 08:30", "Vergi No: [firma bilgisi]", "Acil: 7/24", "Pzt–Cmt 08:30", "Cumartesi", "cumartesi", "7/24", "0532 000"]:
            assert bad_ not in r, bad_
        r2 = pub("/iletisim").text
        assert 'href="https://onlinekaydet.com"' in r and "© 2026" not in r and "Bu site OnlineKaydet ile yayınlanır" in r
        assert "Atatürk Cad" not in r2 and "Hafta içi 08:30" not in r2
    t("boş bırakılan adres/saat temadan kalkar", clr)
    def seo():
        d = c.get("/api/site/profile", headers=H).json()["profile"]
        d["social"] = {"instagram": "instagram.com/firma", "youtube": "https://youtube.com/@firma"}
        assert c.put("/api/site/profile", headers=H, json=d).status_code == 200
        r = pub("/").text
        assert 'rel="canonical" href="https://otomatik-site.com/"' in r and "application/ld+json" in r and "LocalBusiness" in r and "sameAs" in r
        assert 'class="spx-soc"' in r and 'aria-label="Instagram"' in r and 'aria-label="YouTube"' in r
        f = pub("/sss").text; assert "FAQPage" in f and "BreadcrumbList" in f and 'href="https://otomatik-site.com/sss"' in f
        sv = [x for x in c.get("/api/site/profile", headers=H).json()["pages"] if x["kind"] == "service"][0]["slug"]
        assert '"Service"' in pub("/" + sv).text
        d["seo_title"] = "Özel Başlık"; d["seo_desc"] = "Özel açıklama metni"
        assert c.put("/api/site/profile", headers=H, json=d).status_code == 200
        h = pub("/").text; assert "<title>Özel Başlık</title>" in h and "Özel açıklama metni" in h
        sm = pub("/sitemap.xml").text; assert "<priority>" in sm and "otomatik-site.com/sss" in sm
        pv = c.get("/api/site/preview?path=/", headers=H).text; assert "{{H}}" not in pv and 'rel="canonical"' not in pv
    t("temaya özgü SEO: canonical, OG, JSON-LD, sosyal ikonlar, sitemap", seo)
    def drift():
        # editörde kaydedilen sayfa, tema değişince yeni temanın menü/alt bilgisiyle gelir
        r = c.post("/api/site/pages", headers=H, json={"title": "Sertifikalarımız"}); assert r.status_code == 200, r.text
        sl = r.json()["slug"]
        e = c.get("/api/site/edit?page=" + sl, headers=H).json(); assert e["custom"]
        assert c.put("/api/site/edit", headers=H, json={"html": e["html"], "page": sl}).status_code == 200
        before = pub("/" + sl).text
        assert "spx-ph" in before and "Sertifikalarımız" in before
        bd = c.get("/api/brand", headers=H).json(); cur = bd["brand"]["theme"]
        other = next(t_ for t_ in bd["themes"] if t_["slug"] != cur and t_.get("dark") != bd["brand"].get("dark"))
        assert c.put("/api/brand", headers=H, json={**bd["brand"], "theme": other["slug"], "dark": other["dark"], "accent": other["accent"]}).status_code == 200
        import domains; domains._cache["t"] = 0
        after = pub("/" + sl).text
        assert after != before and "Sertifikalarımız" in after and "spx-ph" in after
        assert "application/ld+json" in after
    t("editörde kaydedilen sayfa güncel tema kabuğuyla servis edilir", drift)
print("OK %d/%d" % (len(ok), len(ok) + len(bad)))
for n in ok: print("  ✔", n)
for n, e in bad: print("  ✘", n, "\n", e)
sys.exit(1 if bad else 0)
