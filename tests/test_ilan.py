"""İlan modülü: panel uçları, herkese açık sayfalar, resim, durum, doğrulama, yetki."""
import sys, os, re, base64
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:500]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
PNG = "data:image/png;base64," + base64.b64encode(bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082")).decode()
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Emlak Deneme", "email": "em@x.com", "password": "sifre12345", "package": "tam", "sector": "emlakci"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "em@x.com", "sifre12345")
    async def setup():
        f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
        await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": "n121-lux-emlakci"}}, upsert=True)
        await s.db.main().firm_domains.insert_one({"id": "dv9", "domain": "emlak-test.com", "firm_id": F, "db": f["db"], "status": "yayinda"})
    c.portal.call(setup)
    import domains; domains._cache["t"] = 0
    H = {"Host": "emlak-test.com"}
    def get(p): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers=H)
    L = {}
    def add():
        r = c.post("/api/admin/listings", headers=O, json={"title": "Merkezde 3+1 satılık daire", "kind": "satilik", "category": "Daire", "price": "3250000", "city": "Ankara", "district": "Çankaya", "rooms": "3+1", "m2": 135, "features": ["Asansör", "Otopark"], "description": "Geniş ve ferah.", "images": [PNG, PNG]})
        assert r.status_code == 200, r.text; L["a"] = r.json()
        r = c.post("/api/admin/listings", headers=O, json={"title": "Kiralık ofis katı", "kind": "kiralik", "category": "Ofis", "price": 45000, "status": "taslak"}); assert r.status_code == 200; L["b"] = r.json()
        r = c.post("/api/admin/listings", headers=O, json={"title": "Satılmış villa örneği", "kind": "satilik", "price": 9000000, "status": "satildi"}); assert r.status_code == 200; L["c"] = r.json()
    t("ilan ekle (resimli, taslak, satıldı)", add)
    def valid():
        assert c.post("/api/admin/listings", headers=O, json={"title": "ab"}).status_code == 400
        assert c.post("/api/admin/listings", headers=O, json={"title": "Geçerli başlık", "images": ["data:image/png;base64," + "A" * 1_000_000]}).status_code == 400
        c.cookies.clear(); assert c.post("/api/admin/listings", json={"title": "Yetkisiz başlık"}).status_code in (401, 403)
    t("doğrulama: kısa başlık, büyük resim, yetkisiz", valid)
    def pub():
        r = c.get("/api/public/listings", headers=H); assert r.status_code == 200, r.text
        ti = [x["title"] for x in r.json()]; assert "Merkezde 3+1 satılık daire" in ti and "Satılmış villa örneği" in ti and "Kiralık ofis katı" not in ti, ti
        assert all("images" not in x for x in r.json())
        assert next(x for x in r.json() if x["title"] == "Merkezde 3+1 satılık daire")["img_count"] == 2, "resim sayısı listede görünür"
        im = c.get("/api/public/listings/%s/img/1" % L["a"]["id"], headers=H); assert im.status_code == 200 and im.headers["content-type"] == "image/png" and im.content[:4] == b"\x89PNG"
        assert c.get("/api/public/listings/%s/img/5" % L["a"]["id"], headers=H).status_code == 404
        assert c.get("/api/public/listings/%s/img/0" % L["b"]["id"], headers=H).status_code == 404, "taslak resmi görünmez"
    t("herkese açık liste: taslak gizli, resim servis edilir", pub)
    def pages():
        r = get("/ilanlar"); assert r.status_code == 200 and "Merkezde 3+1 satılık daire" in r.text and "3.250.000" in r.text, r.status_code
        assert "Kiralık ofis katı" not in r.text and "Satıldı" in r.text
        assert "/img/0" in r.text, "kartta resim var"
        assert "Emlak Deneme" in r.text and "ServisPlus" not in r.text
        h = get("/"); assert 'href="/ilanlar"' in h.text, "ana sayfa menü/alt bilgide İlanlar bağlantısı"
        d = get("/ilan/" + L["a"]["slug"]); assert d.status_code == 200 and "Çankaya" in d.text and "Asansör" in d.text and 'class="b1" href="/#randevu"' in d.text
        assert "Kiralık ofis katı" not in get("/ilan/" + L["b"]["slug"]).text, "taslak sayfası yok"
        sold = get("/ilan/" + L["c"]["slug"]); assert "Bu ilan satılmıştır" in sold.text and 'class="b1" href="/#randevu"' not in sold.text
    t("/ilanlar ve /ilan/<ad> temalı sayfalar", pages)
    def edit():
        r = c.put("/api/admin/listings/" + L["b"]["id"], headers=O, json={"title": "Kiralık ofis katı", "status": "yayinda", "kind": "kiralik", "price": 47000}); assert r.status_code == 200
        assert "Kiralık ofis katı" in get("/ilanlar").text
        assert c.delete("/api/admin/listings/" + L["b"]["id"], headers=O).status_code == 200
        assert "Kiralık ofis katı" not in get("/ilan/" + L["b"]["slug"]).text and c.delete("/api/admin/listings/" + L["b"]["id"], headers=O).status_code == 404
    t("düzenle yayına al, sil", edit)
    def jsx():
        import subprocess, tempfile
        for p in ("/ilanlar", "/ilan/" + L["a"]["slug"]):
            for b in re.findall(r"<script>(.*?)</script>", get(p).text, re.S):
                if "okl" in b:
                    f = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False); f.write(b); f.close()
                    r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True); assert r.returncode == 0, r.stderr[:300]
    t("sayfa betikleri geçerli", jsx)
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" FAIL", n, e)
sys.exit(1 if bad else 0)
