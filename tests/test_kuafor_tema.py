"""Kuaför temaları (k6–k10): panel bloklarına bölünür, firma bilgisi yerleşir, paket (sahip ekranı) modülleri belirler,
randevu gerçek API ile çalışır, başka sektörün (avukat/muhasebe) dili kuaför sitesine sızmaz."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from datetime import date, timedelta
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
ROOT = os.path.join(os.path.dirname(__file__), "..")
SLUGS = ["k6-butik-kuafor", "k7-kesimhane-kuafor", "k8-sakin-kuafor", "k9-kagit-kuafor", "k10-atolye-kuafor"]
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-500:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
FOREIGN = re.compile(r"avukat|müvekkil|mükellef|mali müşavir|esas no|mahkeme|dava dosya|noter|yedek parça|arıza|kombi|klima", re.I)
sys.path.insert(0, os.path.join(ROOT, "panel")); import sitegen
THEMES = {x["slug"]: x for x in json.load(open(os.path.join(ROOT, "panel", "themes.json"), encoding="utf-8"))}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    def mkctx(th, mods, shop=False):
        return {"th": th, "name": "Aslı Kuaför", "tel": "05551234567", "p": sitegen.effective({}, "kuafor"), "sector": "kuafor", "logo": "", "city": "", "legal": [],
                "shop_on": shop, "img": (lambda k: ""), "logo_abs": "", "modules": mods}
    def a():
        for sl in SLUGS:
            th = THEMES[sl]; assert th["sector"] == "kuafor"
            raw = open(os.path.join(ROOT, "themes", "html", sl + ".html"), encoding="utf-8").read()
            pr = sitegen.split_blocks(raw); assert pr and len(pr[1]) >= 5, sl
            names = [b[0] for b in pr[1]]; assert len(set(names)) == len(names), (sl, names)
            assert {"Menü", "Alt bilgi", "Mobil bar", "Kampanyalar", "Ürünler"} <= set(names), (sl, names)
    t("5 kuaför teması panel bloklarına bölünür (benzersiz adlar, sabit + modül blokları)", a)
    def b():
        for sl in SLUGS:
            raw = open(os.path.join(ROOT, "themes", "html", sl + ".html"), encoding="utf-8").read()
            h = sitegen.apply_profile(raw, THEMES[sl], mkctx(THEMES[sl], None))
            assert "Aslı Kuaför" in h and "0555 123 45 67" in h and "0532 000" not in h and "905320000000" not in h, sl
            txt = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
            m = FOREIGN.search(re.sub(r"<[^>]+>", " ", txt)); assert not m, (sl, m and m.group(0))
            assert "window.__OKLIVE=true" in h, "randevu gerçek API'ye bağlı olmalı"
    t("firma adı/telefon yerleşir; başka sektörün sözcüğü (avukat, mükellef, yedek parça...) kuaför sitesinde çıkmaz", b)
    def g():
        for sl in SLUGS:
            raw = open(os.path.join(ROOT, "themes", "html", sl + ".html"), encoding="utf-8").read()
            def names(mods, shop=False):
                h = sitegen.apply_profile(raw, THEMES[sl], mkctx(THEMES[sl], mods, shop)); return re.findall(r'data-nm="([^"]*)"', h), h
            n, h = names(["servis", "site"])
            assert "Kampanyalar" not in n and "Ürünler" not in n and 'id="kampanya"' not in h and 'id="urunler"' not in h, (sl, "boş paket: kampanya/mağaza olmamalı")
            n, h = names(["servis", "site", "pazarlama"])
            assert "Kampanyalar" in n and "Ürünler" not in n, sl
            n, h = names(["servis", "site", "magaza"], True)
            assert "Ürünler" in n and "Kampanyalar" not in n, (sl, n)
            n, h = names(["servis", "site", "magaza", "pazarlama"], False)    # mağaza paketi var ama site mağazası kapalı
            assert "Ürünler" not in n and "Kampanyalar" in n, sl
            n, h = names(["servis", "site", "pazarlama"], True)                # eski bayrak açık kalsa da paket yoksa mağaza çıkmaz
            assert "Ürünler" not in n, (sl, n)
            n, h = names(None, True)
            assert "Ürünler" in n and "Kampanyalar" in n, (sl, "paket sınırı yoksa hepsi açık")
    t("paket → tema bölümleri: boş pakette kampanya/mağaza yok; pazarlama→kampanya; mağaza→ürünler", g)
    def ed():
        sl = SLUGS[0]; raw = open(os.path.join(ROOT, "themes", "html", sl + ".html"), encoding="utf-8").read()
        ctx = mkctx(THEMES[sl], ["servis", "site"]); ctx["p"]["edits"] = {sl: {"Hizmetler": {"0": "ÖZEL BAŞLIK XYZ"}}}
        h0 = sitegen.apply_profile(raw, THEMES[sl], mkctx(THEMES[sl], ["servis", "site"]))
        blk = [x for x in sitegen.split_blocks(h0)[1] if x[0] == "Hizmetler"][0][1]
        assert re.search(r"<h2[^>]*>", blk), "Hizmetler bloğunda düzenlenebilir başlık olmalı"
        ctx["p"]["layout"] = {"hidden": ["Galeri"], "order": ["Paketler", "Hizmetler"]}
        h = sitegen.apply_profile(raw, THEMES[sl], ctx); n = re.findall(r'data-nm="([^"]*)"', h)
        assert "Galeri" not in n and n.index("Paketler") < n.index("Hizmetler") and n[0] == "Menü" and n[-1] == "Mobil bar", n
    t("bölüm gizle/sırala kuaför temasında çalışır, sabit parçalar yerinde kalır", ed)
    # ---- gerçek uygulama: sahip paketi → firma → herkese açık site + randevu
    def mk(name, email, mods):
        r = c.post("/api/admin/firms", headers=A, json={"name": name, "email": email, "password": "sifre12345", "package": "baslangic", "sector": "kuafor"}); assert r.status_code == 200, r.text
        fid = r.json()["id"]
        assert c.put(f"/api/admin/firms/{fid}", headers=A, json={"modules": mods, "premium_themes": True}).status_code == 200   # premium tema onayı sahipte
        return fid, tok(c, email, "sifre12345")
    def dom(fid, host):
        async def go():
            await s.db.main().firm_domains.insert_one({"id": "d-" + host, "domain": host, "firm_id": fid, "db": s.db.firm_db_name(fid), "status": "yayinda"})
        c.portal.call(go)
        import domains; domains._cache["t"] = 0
    def pub(host, p="/"): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers={"Host": host})
    def h():
        S["a"], S["Ha"] = mk("Boş Paket Kuaför", "a@kuafor.com", ["site"])
        S["b"], S["Hb"] = mk("Tam Paket Kuaför", "b@kuafor.com", ["site", "pazarlama", "magaza"])
        dom(S["a"], "bos-kuafor.com"); dom(S["b"], "tam-kuafor.com")
        for H in (S["Ha"], S["Hb"]):
            r = c.put("/api/brand", headers=H, json={"theme": "k6-butik-kuafor", "dark": "#3a2328", "accent": "#b5476b", "radius": 14}); assert r.status_code == 200, r.text
        ra = pub("bos-kuafor.com"); rb = pub("tam-kuafor.com")
        assert ra.status_code == 200 and rb.status_code == 200
        assert 'id="kampanya"' not in ra.text and 'id="urunler"' not in ra.text and 'id="f-c"' not in ra.text and 'id="kupf"' not in ra.text, "boş pakette kampanya/mağaza görünmemeli"
        assert 'id="kampanya"' in rb.text and 'id="f-c"' in rb.text, "pazarlama paketinde kampanya + randevuda kupon alanı görünmeli"
        assert 'id="urunler"' in rb.text, "mağaza paketi verilince site mağazası da açılır (sync_shop) -> ürünler görünür"
        assert c.put("/api/site/features", headers=S["Hb"], json={"shop_enabled": False}).status_code == 200
        assert 'id="urunler"' not in pub("tam-kuafor.com").text, "firma mağazayı kapatınca ürünler kalkar"
    t("sahip paketi → yayındaki site: boş pakette kampanya/mağaza yok, tam pakette kampanya var", h)
    def sh():
        r = c.put("/api/site/features", headers=S["Ha"], json={"shop_enabled": True}); assert r.status_code == 403 and "paketinizde yok" in r.text, (r.status_code, r.text)
        r = c.put("/api/site/features", headers=S["Hb"], json={"shop_enabled": True}); assert r.status_code == 200, r.text
        assert 'id="urunler"' in pub("tam-kuafor.com").text, "mağaza açılınca ürünler bölümü görünür"
        assert c.get("/api/public/shop/products", headers={"Host": "bos-kuafor.com"}).status_code in (403, 404)
        # paket düşürülünce mağaza hem sitede hem API'de kapanır
        assert c.put(f"/api/admin/firms/{S['b']}", headers=A, json={"modules": ["site", "pazarlama"]}).status_code == 200
        assert 'id="urunler"' not in pub("tam-kuafor.com").text, "paket düşünce mağaza bölümü kalkmalı"
        assert 'id="kampanya"' in pub("tam-kuafor.com").text
        assert c.put(f"/api/admin/firms/{S['b']}", headers=A, json={"modules": ["site"]}).status_code == 200
        assert 'id="kampanya"' not in pub("tam-kuafor.com").text, "pazarlama kalkınca kampanya bölümü kalkmalı"
    t("e-ticaret: pakette yoksa açılamaz; paket düşünce site ve API'den çekilir; kampanya pazarlamaya bağlı", sh)
    def bk():
        d = (date.today() + timedelta(days=1))
        while d.weekday() == 6: d += timedelta(days=1)
        # randevu ayarı yalnız 'randevu' (ya da pazarlama) paketi olan firmada yönetilebilir
        r = c.get("/api/growth/settings", headers=S["Ha"]); assert r.status_code == 403, "randevu/pazarlama paketi olmayan ayar yönetemez"
        assert c.put(f"/api/admin/firms/{S['a']}", headers=A, json={"modules": ["site", "randevu"]}).status_code == 200
        r = c.get("/api/growth/settings", headers=S["Ha"]); assert r.status_code == 200, r.text
        cfg = r.json(); cfg["booking"]["enabled"] = True; cfg["booking"]["capacity"] = 2; cfg["booking"]["min_notice_hours"] = 0
        r = c.put("/api/growth/settings", headers=S["Ha"], json=cfg); assert r.status_code == 200, r.text
        assert c.get("/api/growth/coupons", headers=S["Ha"]).status_code == 403, "randevu paketi kupon/pazarlama açmaz"
        H = {"Host": "bos-kuafor.com"}
        cf = c.get("/api/public/booking/config", headers=H).json(); assert cf["enabled"] and cf["days"], cf
        day = cf["days"][2]; sl = c.get("/api/public/booking/slots?date=" + day, headers=H).json()["slots"]; free = [x for x in sl if x["available"]]; assert free, sl
        tm = free[0]["time"]
        r = c.post("/api/public/booking", headers=H, json={"name": "Deneme Müşteri", "phone": "0532 111 22 33", "date": day, "time": tm, "device_type": "Kesim ve fön", "fault": "Hizmet: Kesim ve fön · Uzman: Elif"}); assert r.status_code == 200, r.text
        bks = c.get("/api/growth/bookings", headers=S["Ha"]).json(); assert any(x["time"] == tm and x["date"] == day and "Elif" in x["fault"] for x in bks), bks
        assert 'window.__OKLIVE=true' in pub("bos-kuafor.com").text
    t("randevu: sahip 'Online randevu' açınca tema günleri/saatleri API'den gelir, kayıt panele düşer; pazarlama açılmaz", bk)
    def hdr():
        # sahip ekranı paket listesi: Online randevu modülü seçilebilir
        r = c.get("/api/admin/packages", headers=A).json(); assert "randevu" in r["modules"] and "randevu" in r["packages"]["tam"]["modules"]
    t("sahip ekranında 'Online randevu' modülü paketlere eklenebilir", hdr)
print("OK", len(ok), "FAIL", len(bad))
for n, e in bad: print("-", n, "\n", e)
sys.exit(1 if bad else 0)
