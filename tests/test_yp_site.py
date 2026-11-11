"""Yeni panel Web Sitem: logo, fotoğraf, galeri, bölüm resmi değiştirme, footer yazısı; tema ile uyum."""
import sys, os, base64, io, re
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
from PIL import Image
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-700:]))
def png(col):
    b = io.BytesIO(); Image.new("RGB", (400, 300), col).save(b, "PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Salon Deneme", "email": "sd@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    assert c.put("/api/admin/firms/%s" % r.json()["id"], headers=A, json={"premium_themes": True}).status_code == 200
    H = tok(c, "sd@x.com", "sifre12345")
    def th():
        r = c.put("/api/brand", headers=H, json={"theme": "k6-butik-kuafor", "dark": "#1a1a1a", "accent": "#b08d57", "radius": 8})
        if r.status_code != 200:   # premium onayı yok: sahip onayını doğrudan yaz
            import asyncio
            raise AssertionError("tema seçilemedi: %s %s" % (r.status_code, r.text[:200]))
    t("tema seçilir", th)
    def bl():
        r = c.get("/api/site/blocks", headers=H); assert r.status_code == 200, r.text
        b = r.json()["blocks"]; S["b"] = b
        g = [x for x in b if x["name"] == "Galeri"]; assert g and g[0]["ni"] >= 5, b
    t("bölüm listesinde Galeri ve resim sayısı görünür", bl)
    def bi():
        r = c.get("/api/site/block-images?name=Galeri", headers=H); assert r.status_code == 200, r.text
        S["imgs"] = r.json()["images"]; assert len(S["imgs"]) >= 5 and S["imgs"][0]["thumb"].startswith("https://images.pexels.com/"), S["imgs"][:1]
    t("Galeri bölümünün resimleri listelenir", bi)
    def rep():
        r = c.post("/api/site/image", headers=H, json={"data": png("red"), "kind": "slides"}); assert r.status_code == 200, r.text
        S["k"] = r.json()["k"]
        p = c.get("/api/site/profile", headers=H).json()["profile"]
        p["imgedits"] = {"k6-butik-kuafor": {"Galeri": {"0": S["k"]}}}
        assert c.put("/api/site/profile", headers=H, json=p).status_code == 200
        h = c.get("/api/site/preview?path=/", headers=H).text
        assert "u" + S["k"] in h and "data:image/jpeg;base64" in h, "resim yerleşmedi"
        assert "window.__OKI" in h and "window.__OKI[i]" in h, "lightbox yaması yok"
        # yayında kalıcı adres
        import asyncio
    t("Galeri resmi değiştirilir; önizlemede görünür, lightbox yamalı", rep)
    def keep():
        p = c.get("/api/site/profile", headers=H).json()["profile"]
        assert p["imgedits"]["k6-butik-kuafor"]["Galeri"]["0"] == S["k"]
        p2 = dict(p); p2.pop("imgedits")           # eski panel bu alanı göndermez
        assert c.put("/api/site/profile", headers=H, json=p2).status_code == 200
        p = c.get("/api/site/profile", headers=H).json()["profile"]; assert p["imgedits"]["k6-butik-kuafor"]["Galeri"]["0"] == S["k"], "silindi"
        assert c.get("/api/public/site-img/" + S["k"]).status_code == 200, "resim temizlendi"
    t("eski panel profili kaydedince resim değişikliği silinmez", keep)
    def idx():
        p = c.get("/api/site/profile", headers=H).json()["profile"]
        r = c.get("/api/site/block-images?name=Galeri", headers=H).json()["images"]
        assert r[0]["k"] == S["k"] and r[1]["k"] == "" and len(r) == len(S["imgs"]), "sıra kaydı bozuldu"
    t("değişen resim sırası korunur, özgün sayım bozulmaz", idx)
    def logo():
        assert c.put("/api/site/logo", headers=H, json={"data": png("blue")}).status_code == 200
        h = c.get("/api/site/preview?path=/", headers=H).text; assert "spx-logo" in h, "logo yok"
        assert c.put("/api/site/logo", headers=H, json={"data": ""}).status_code == 200
    t("logo yüklenir ve temada görünür", logo)
    def gal():
        k2 = c.post("/api/site/image", headers=H, json={"data": png("green"), "kind": "gallery"}).json()["k"]
        p = c.get("/api/site/profile", headers=H).json()["profile"]; p["gallery"] = [{"k": k2}]; p["slides"] = [{"k": S["k"]}]
        assert c.put("/api/site/profile", headers=H, json=p).status_code == 200
        pr = c.get("/api/site/profile", headers=H).json(); assert any(x["kind"] == "gallery" for x in pr["pages"]), pr["pages"]
        h = c.get("/api/site/preview?path=/", headers=H).text; assert "spx-s" in h, "slayt yok"
    t("galeri ve slayt fotoğrafı eklenir, galeri sayfası açılır", gal)
    def foot():
        r = c.get("/api/site/block-text?name=Alt bilgi", headers=H); assert r.status_code == 200, r.text
        tx = r.json()["texts"]; assert tx, "footer yazısı yok"
        i = tx[0]["i"]
        p = c.get("/api/site/profile", headers=H).json()["profile"]
        p["edits"] = {"k6-butik-kuafor": {"Alt bilgi": {str(i): "Footer deneme metni"}}}
        assert c.put("/api/site/profile", headers=H, json=p).status_code == 200
        h = c.get("/api/site/preview?path=/", headers=H).text; assert "Footer deneme metni" in h, "footer yazısı işlenmedi"
    t("footer yazısı değiştirilir", foot)
    def soc():
        p = c.get("/api/site/profile", headers=H).json()["profile"]
        p["social"] = {"instagram": "https://instagram.com/x", "facebook": "https://facebook.com/x"}; p["address"] = "Deneme Mah. 5"; p["hours"] = "Her gün 10-20"
        assert c.put("/api/site/profile", headers=H, json=p).status_code == 200
        h = c.get("/api/site/preview?path=/", headers=H).text
        assert "instagram.com/x" in h and "Deneme Mah. 5" in h, "sosyal/adres yok"
    t("sosyal medya, adres, saat siteye işlenir", soc)
    def tim():
        r = c.get("/api/site/theme-images", headers=H); assert r.status_code == 200, r.text
        im = r.json()["images"]; assert len(im) >= 10, len(im)
        k = c.post("/api/site/image", headers=H, json={"data": png("orange"), "kind": "slides"}).json()["k"]
        p = c.get("/api/site/profile", headers=H).json()["profile"]
        p["imgmap"] = {"k6-butik-kuafor": {im[0]["pid"]: k, im[5]["pid"]: k}}
        assert c.put("/api/site/profile", headers=H, json=p).status_code == 200
        h = c.get("/api/site/preview?path=/", headers=H).text
        assert "window.__OKI" in h and '"%s"' % im[0]["pid"] in h and "window.__OKI[i]" in h, "tema resmi yerleşmedi"
        p2 = c.get("/api/site/profile", headers=H).json()["profile"]; p2.pop("imgmap", None)
        assert c.put("/api/site/profile", headers=H, json=p2).status_code == 200
        assert c.get("/api/site/profile", headers=H).json()["profile"]["imgmap"]["k6-butik-kuafor"][im[0]["pid"]] == k, "eski panel sildi"
        assert c.get("/api/site/theme-images", headers=H).json()["images"][0]["k"] == k
    t("tema resimleri listelenir, kimlik bazlı değiştirilir (galeri/lightbox dahil), eski panel silmez", tim)
    def lay():
        p = c.get("/api/site/profile", headers=H).json()["profile"]; p["layout"] = {"order": ["Galeri", "Ekip"], "hidden": ["Kampanyalar"]}
        assert c.put("/api/site/profile", headers=H, json=p).status_code == 200
        assert c.put("/api/brand", headers=H, json={"theme": "k5-atolye-kuafor", "dark": "#1a1a1a", "accent": "#b08d57", "radius": 8}).status_code == 200
        p = c.get("/api/site/profile", headers=H).json()["profile"]; assert p["layout"] == {"order": [], "hidden": []}, p["layout"]
        assert c.put("/api/site/logo", headers=H, json={"data": png("blue")}).status_code == 200
        h = c.get("/api/site/preview?path=/", headers=H).text
        assert re.search(r'<a class="lg[^"]*"[^>]*><img class="spx-logo"', h), "k5 başlığında logo yok"
        assert c.put("/api/brand", headers=H, json={"theme": "k5-atolye-kuafor", "dark": "#1a1a1a", "accent": "#b08d57", "radius": 9}).status_code == 200
    t("tema değişince bölüm düzeni sıfırlanır; k5 başlığında logo görünür", lay)
    def mn():
        assert c.put("/api/brand", headers=H, json={"theme": "k6-butik-kuafor", "dark": "#1a1a1a", "accent": "#b08d57", "radius": 8}).status_code == 200
        r = c.get("/api/site/menu", headers=H); assert r.status_code == 200, r.text
        it = r.json()["items"]; assert any(x["h"] == "#galeri" for x in it), it
        p = c.get("/api/site/profile", headers=H).json()["profile"]
        p["menu"] = {"edits": {"#galeri": {"l": "Fotoğraflarımız"}, "#ekip": {"off": True}}, "extra": [{"l": "Blog", "h": "https://blog.example.com"}, {"l": "Kötü", "h": "javascript:alert(1)"}]}
        assert c.put("/api/site/profile", headers=H, json=p).status_code == 200
        m = c.get("/api/site/profile", headers=H).json()["profile"]["menu"]; assert len(m["extra"]) == 1 and m["edits"]["#ekip"]["off"], m
        h = c.get("/api/site/preview?path=/", headers=H).text
        assert "Fotoğraflarımız" in h and ">Blog<" in h and 'href="#ekip">Ekip<' not in h.split('id="sn"')[1].split("</nav>")[0], "menü düzenlemesi sitede yok"
        # eski panel (menu alanı yok) menüyü silmez
        p.pop("menu"); assert c.put("/api/site/profile", headers=H, json=p).status_code == 200
        assert c.get("/api/site/profile", headers=H).json()["profile"]["menu"]["extra"], "menü silindi"
        assert "window.YPF" in h and "/api/public/yp/book" in h and "Randevunuz iletildi" in h, "randevu ekip/hizmet verisine bağlı değil"
        assert c.put("/api/brand", headers=H, json={"theme": "k5-atolye-kuafor", "dark": "#1a1a1a", "accent": "#b08d57", "radius": 9}).status_code == 200
        assert not c.get("/api/site/profile", headers=H).json()["profile"]["menu"]["extra"], "tema değişince menü sıfırlanmalı"
    t("menü düzenlenir (ad, gizle, ek bağlantı), güvenli adres, tema değişince sıfırlanır; randevu paneldeki ekibe bağlanır", mn)
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" -", n); print(e)
sys.exit(1 if bad else 0)
