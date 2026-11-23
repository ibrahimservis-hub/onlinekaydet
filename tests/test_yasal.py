"""Yasal metinler: modüle göre otomatik gelir, firma bilgisiyle dolar, müşteri düzenleyebilir, footer'a düşer."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server
with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    def firma(ad, em, sec, pk="tam"):
        r = c.post("/api/admin/firms", headers=A, json={"name": ad, "email": em, "password": "sifre12345", "package": pk, "phone": "05321112233", "address": "Moda Cd. 5 Kadıköy", "tax_no": "1234567890", "tax_office": "Kadıköy"}); assert r.status_code == 200, r.text
        H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": em, "password": "sifre12345"}).json()["token"]}
        c.post("/api/yp/sectors/" + sec, headers=H, json={}); return H
    He = firma("Mavi Butik Ltd", "ye@x.com", "eticaret", "kurumsal")
    Hk = firma("Gül Kuaför", "yk@x.com", "kuafor")
    r = c.get("/api/yp/yasal", headers=He).json()
    sl = [d["slug"] for d in r["docs"]]
    assert r["shop"] and "mesafeli-satis-sozlesmesi" in sl and "uyelik-sozlesmesi" in sl and "ticari-ileti-izni" in sl and "gizlilik-guvenlik" in sl, sl
    b = {x["k"]: x for x in r["bilgi"]}
    assert b["seller_title"]["v"] == "Mavi Butik Ltd" and b["seller_title"]["kaynak"] == "oto" and b["tax_no"]["v"] == "1234567890", b
    assert "Mavi Butik Ltd" in [d for d in r["docs"] if d["slug"] == "mesafeli-satis-sozlesmesi"][0]["html"]
    k = c.get("/api/yp/yasal", headers=Hk).json()
    ks = [d["slug"] for d in k["docs"]]
    assert not k["shop"] and "mesafeli-satis-sozlesmesi" not in ks and "randevu-iptal-kosullari" in ks and "gizlilik-kvkk" in ks, ks
    # müşteri bilgi ve metin düzenler
    assert c.put("/api/yp/yasal/bilgi", headers=He, json={"seller_title": "Mavi Butik Ticaret Ltd. Şti.", "mersis": "0123456789012345"}).status_code == 200
    r = c.get("/api/yp/yasal", headers=He).json(); b = {x["k"]: x for x in r["bilgi"]}
    assert b["seller_title"]["kaynak"] == "elle" and b["mersis"]["v"] == "0123456789012345"
    assert c.put("/api/yp/yasal/bilgi", headers=He, json={"seller_title": ""}).status_code == 200
    assert {x["k"]: x for x in c.get("/api/yp/yasal", headers=He).json()["bilgi"]}["seller_title"]["v"] == "Mavi Butik Ltd"
    ozel = "<h2>Özel iade</h2><p>Ürünler 30 gün içinde ücretsiz iade edilir. Kargo bizden.</p>"
    assert c.put("/api/yp/yasal/iptal-iade-cayma", headers=He, json={"html": ozel}).status_code == 200
    assert c.put("/api/yp/yasal/iptal-iade-cayma", headers=He, json={"html": "<script>x</script>" + ozel}).status_code == 422
    d = [x for x in c.get("/api/yp/yasal", headers=He).json()["docs"] if x["slug"] == "iptal-iade-cayma"][0]
    assert d["custom"] and "30 gün" in d["html"]
    assert c.put("/api/yp/yasal/iptal-iade-cayma", headers=He, json={"reset": True}).status_code == 200
    assert not [x for x in c.get("/api/yp/yasal", headers=He).json()["docs"] if x["slug"] == "iptal-iade-cayma"][0]["custom"]
    # footer'dan gizle
    c.put("/api/yp/yasal/ticari-ileti-izni", headers=He, json={"gizli": True})
    assert [x for x in c.get("/api/yp/yasal", headers=He).json()["docs"] if x["slug"] == "ticari-ileti-izni"][0]["gizli"]
    # sitede: footer bağlantıları ve sayfa
    for H_, sec_ in ((He, "eticaret"), (Hk, "kuafor")):
        br = c.get("/api/brand", headers=H_).json()
        th = next(t["slug"] for t in br["themes"] if t["sector"] == sec_) if any(t["sector"] == sec_ for t in br["themes"]) else br["themes"][0]["slug"]
        assert c.put("/api/brand", headers=H_, json={**br["brand"], "theme": th}).status_code == 200
    c.put("/api/site/features", headers=He, json={"shop_enabled": True})
    pv = c.get("/api/site/preview?path=/", headers=He)
    assert pv.status_code == 200, pv.text[:200]
    for slug in ("mesafeli-satis-sozlesmesi", "uyelik-sozlesmesi", "gizlilik-guvenlik", "gizlilik-kvkk"):
        assert "/" + slug in pv.text, slug
    assert "ticari-ileti-izni" not in pv.text            # gizlendi
    pg = c.get("/api/site/preview?path=/uyelik-sozlesmesi", headers=He)
    assert pg.status_code == 200 and "Mavi Butik Ltd" in pg.text and "Üyelik Sözleşmesi" in pg.text, pg.text[:300]
    pk = c.get("/api/site/preview?path=/", headers=Hk).text
    assert "/randevu-iptal-kosullari" in pk and "/mesafeli-satis-sozlesmesi" not in pk
print("OK")
