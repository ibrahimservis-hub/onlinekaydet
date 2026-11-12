"""Bölüm motoru: katalog süzme, sayfa ve bölüm örnekleri, ayarlar, rozetler, sektör paketi."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import blocks
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-700:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    def a():
        assert len(blocks.BLOCKS) >= 120 and len({b["id"] for b in blocks.BLOCKS}) == len(blocks.BLOCKS), "benzersiz id"
        assert len(blocks.SECTOR_PACKS) >= 16
        for b in blocks.BLOCKS:                                      # her alan geçerli tipte ve etiketli
            assert b["cat"] in blocks.CAT_NAMES, b["id"]
            for f in b["fields"]:
                assert f["t"] in blocks.TYPES, (b["id"], f)
                assert f.get("l"), (b["id"], f)
        for p in blocks.SECTOR_PACKS.values():                       # paketlerdeki bölümler gerçekten var
            for bid in p["blocks"]:
                assert bid in blocks.BY_ID, (p["id"], bid)
    t("katalog tutarlı: benzersiz id, geçerli alan tipleri, paketler var olan bölümleri gösteriyor", a)
    def b():
        r = c.get("/api/yp/blocks", headers=H).json()
        S["sector"] = r["sector"]
        ids = {x["id"] for x in r["rows"]}
        assert "hero" in ids and "mobil_bar" in ids
        assert "v_indirim" not in ids, "shop modülü kapalıyken ürün vitrini gelmemeli"
        assert "qr_menu" not in ids, "lokanta bölümü kuaförde görünmemeli"
        assert r["cats"] and sum(x["n"] for x in r["cats"]) == r["total"]
        assert c.get("/api/yp/blocks", headers=H, params={"q": "mobil"}).json()["rows"]
        assert all(x["cat"] == "yapi" for x in c.get("/api/yp/blocks", headers=H, params={"cat": "yapi"}).json()["rows"])
    t("katalog sektöre ve açık modüllere göre süzülüyor, arama ve kategori çalışıyor", b)
    def d():
        assert c.post("/api/yp/sectors/eticaret", headers=H).status_code == 200
        r = c.get("/api/yp/blocks", headers=H).json()
        ids = {x["id"] for x in r["rows"]}
        assert "v_indirim" in ids and "guvence" in ids and "siparis_takip" in ids, "e-ticaret paketi vitrinleri açmalı"
        assert r["sector_name"] == "E-ticaret"
        sec = c.get("/api/yp/sectors", headers=H).json()
        assert [x for x in sec["rows"] if x["on"]][0]["id"] == "eticaret"
        assert [x for x in sec["rows"] if x["id"] == "kuafor"][0]["terms"]["kisi"] == "Uzman"
    t("sektör paketi uygulanınca modüller ve bölümler kendiliğinden açılıyor", d)
    def e():
        r = c.get("/api/yp/pages", headers=H).json()
        assert len(r["rows"]) == 1 and r["rows"][0]["home"] and r["rows"][0]["n"] > 0, r
        S["home"] = r["rows"][0]["id"]
        n = c.post("/api/yp/pages", headers=H, json={"title": "Gelin Paketi", "footer": True}).json()
        assert n["slug"] == "gelin-paketi" and n["menu"]["footer"] and n["status"] == "live"
        S["p2"] = n["id"]
        cp = c.post("/api/yp/pages", headers=H, json={"title": "Kasım Kampanyası", "copy_of": S["home"], "draft": True}).json()
        assert cp["n"] == r["rows"][0]["n"] and cp["status"] == "draft", "çoğaltma bölümleri de kopyalamalı"
        b1 = c.get("/api/yp/pages/%s/blocks" % S["home"], headers=H).json()["rows"]
        b2 = c.get("/api/yp/pages/%s/blocks" % cp["id"], headers=H).json()["rows"]
        assert {x["iid"] for x in b1} & {x["iid"] for x in b2} == set(), "kopyada yeni kimlikler olmalı"
        assert c.post("/api/yp/pages", headers=H, json={"title": "Gelin Paketi"}).json()["slug"] != "gelin-paketi"
        assert c.put("/api/yp/pages/%s" % S["p2"], headers=H, json={"slug": "api"}).status_code == 422, "ayrılmış adres"
        assert c.delete("/api/yp/pages/%s" % S["home"], headers=H).status_code == 422, "ana sayfa silinemez"
    t("sayfa ekleme, çoğaltma, taslak, adres çakışması ve ana sayfa koruması", e)
    def f():
        bad_ = c.post("/api/yp/pages/%s/blocks" % S["home"], headers=H, json={"bid": "yok"})
        assert bad_.status_code == 404
        r = c.post("/api/yp/pages/%s/blocks" % S["home"], headers=H, json={"bid": "v_indirim", "at": 0})
        assert r.status_code == 200, r.text
        iid = r.json()["iid"]; S["iid"] = iid
        assert r.json()["at"] == 0 and r.json()["set"]["rule"] == "indirim" and r.json()["set"]["cols"] == 4
        rows = c.get("/api/yp/pages/%s/blocks" % S["home"], headers=H).json()["rows"]
        assert rows[0]["iid"] == iid and rows[0]["name"] == "İndirimli ürünler" and rows[0]["manage"] == "Ürünler"
        assert c.post("/api/yp/pages/%s/blocks" % S["home"], headers=H, json={"bid": "qr_menu"}).status_code == 403
    t("bölüm ekleme: sıraya yerleştirme, varsayılan ayarlar, sektör dışı bölüm reddi", f)
    def g():
        u = "/api/yp/pages/%s/blocks/%s" % (S["home"], S["iid"])
        r = c.put(u, headers=H, json={"set": {"title": "Kaçırılmayacak indirimler", "cols": 6, "radius": 999,
                                               "bg": "kırmızı", "anim_auto": 1, "yok": "x"}}).json()
        assert r["set"]["title"] == "Kaçırılmayacak indirimler" and r["set"]["cols"] == "6"
        assert r["set"]["radius"] == 24, "slider üst sınıra çekilmeli"
        assert "bg" not in r["set"], "geçersiz renk kaydedilmemeli"
        assert r["set"]["anim_auto"] is True and "yok" not in r["set"], "tanımsız alan kaydedilmemeli"
        r = c.put(u, headers=H, json={"set_m": {"cols_m": "kaydırmalı"}}).json()
        assert r["set_m"]["cols_m"] == "kaydırmalı" and r["set"]["cols"] == "6", "telefon ayarı bilgisayarı bozmamalı"
        r = c.put(u, headers=H, json={"badges": ["indirim", "son_adet", "uydurma"]}).json()
        assert r["badges"] == ["indirim", "son_adet"]
        assert c.put(u, headers=H, json={"on": False}).json()["on"] is False
        assert c.put("/api/yp/pages/%s/blocks/yok" % S["home"], headers=H, json={"on": True}).status_code == 404
    t("ayarlar süzülerek kaydediliyor; telefon ayarı ayrı tutuluyor; rozetler doğrulanıyor", g)
    def h():
        rows = c.get("/api/yp/pages/%s/blocks" % S["home"], headers=H).json()["rows"]
        ids = [x["iid"] for x in rows][::-1]
        assert c.post("/api/yp/pages/%s/blocks/order" % S["home"], headers=H, json={"ids": ids}).json()["ids"] == ids
        assert [x["iid"] for x in c.get("/api/yp/pages/%s/blocks" % S["home"], headers=H).json()["rows"]] == ids
        assert c.delete("/api/yp/pages/%s/blocks/%s" % (S["home"], S["iid"]), headers=H).status_code == 200
        assert S["iid"] not in [x["iid"] for x in c.get("/api/yp/pages/%s/blocks" % S["home"], headers=H).json()["rows"]]
    t("bölüm sıralama ve silme", h)
    def i():
        r = c.get("/api/yp/badges", headers=H).json()
        assert len(r["rows"]) == 8 and r["rows"][0]["id"] == "indirim"
        rows = r["rows"] + [{"id": "el_yapimi", "name": "El yapımı", "color": "#0b7a4b", "pos": "tr", "motion": True, "custom": True},
                            {"name": "", "custom": True}]
        assert c.put("/api/yp/badges", headers=H, json={"rows": rows}).json()["rows"][-1]["name"] == "El yapımı"
        assert len(c.get("/api/yp/badges", headers=H).json()["rows"]) == 9, "adsız rozet eklenmemeli"
        b = c.get("/api/yp/blocks/v_indirim", headers=H).json()
        assert b["block"]["resp"] and any(f["t"] == "urun" for f in b["fields"]) and len(b["badges"]) == 9
    t("rozetler: hazır 8 rozet, kendi rozetini tanımlama, bölüm alanlarıyla birlikte dönüyor", i)
    def k():
        c.put("/api/yp/pages/%s" % S["p2"], headers=H, json={"menu": {"top": False, "footer": True, "mobile": False, "label": "Gelin"}})
        nav = c.get("/api/yp/site/nav", headers=H).json()
        assert {"label": "Gelin", "href": "/gelin-paketi", "parent": ""} in nav["footer"]
        assert all(x["href"] != "/gelin-paketi" for x in nav["top"]), "üst menüde olmamalı"
        assert all("kasim" not in x["href"] for x in nav["top"]), "taslak sayfa menüde olmamalı"
    t("menü sayfalardan üretiliyor: üst / footer / mobil ayrı, taslak görünmüyor", k)
print("OK" if not bad else "FAIL", len(ok), "geçti")
for n, e in bad: print("✗", n, "\n", e)
sys.exit(1 if bad else 0)
