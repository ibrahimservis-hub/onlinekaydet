"""İçerik motoru: tür tanımı, doğrulama, onay akışı, sıra ve siteye yansıma."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}

    def a():
        r = c.get("/api/yp/content", headers=H).json()
        ids = [x["id"] for x in r["types"]]
        for x in ("yorum", "blog", "sss", "story", "duyuru", "sube"):
            assert x in ids, "%s eksik" % x
        y = [x for x in r["types"] if x["id"] == "yorum"][0]
        assert y["moderate"] and y["n"] == 0 and y["used"], "kuaför paketinde yorum bölümü kullanılıyor"
        assert y["empty"], "boş ekran metni olmalı"
    t("içerik türleri sektöre göre listeleniyor", a)

    def b():
        r = c.post("/api/yp/content/sss", headers=H,
                   json={"q": "Randevumu nasıl iptal ederim?", "a": "Mesaj atmanız yeterli.", "group": "Randevu"})
        assert r.status_code == 200, r.text
        it = r.json()["item"]
        assert it["q"].startswith("Randevumu") and it["on"] and it["order"] == 0
        assert c.post("/api/yp/content/sss", headers=H, json={"q": "Soru"}).status_code == 422, "cevap zorunlu"
        assert c.post("/api/yp/content/yok", headers=H, json={}).status_code == 404
        g = c.get("/api/yp/content/sss", headers=H).json()
        assert g["counts"]["hepsi"] == 1 and g["type"]["name"] == "Sık sorulanlar"
        assert [f["key"] for f in g["type"]["fields"]] == ["q", "a", "group"]
    t("kayıt ekleniyor, zorunlu alan denetleniyor, tür tanımı panele gidiyor", b)

    def d():
        for n2 in range(3):
            c.post("/api/yp/content/sss", headers=H, json={"q": "Soru %d" % n2, "a": "Cevap %d" % n2})
        rows = c.get("/api/yp/content/sss", headers=H).json()["items"]
        ids = [r["id"] for r in rows]
        assert len(ids) == 4
        c.post("/api/yp/content/sss/sira", headers=H, json={"ids": list(reversed(ids))})
        yeni = [r["id"] for r in c.get("/api/yp/content/sss", headers=H).json()["items"]]
        assert yeni == list(reversed(ids)), "sıra kaydedilmeli"
    t("sıralama kaydediliyor", d)

    def e():
        r = c.post("/api/public/yp/yorum", json={"name": "Zeynep D.", "rating": 5,
                                                 "text": "Balyajım harika oldu, teşekkürler."})
        assert r.status_code == 200 and "onaylandıktan sonra" in r.json()["msg"], r.text
        g = c.get("/api/yp/content/yorum", headers=H).json()
        assert g["counts"]["onay"] == 1 and g["counts"]["yayin"] == 0
        it = g["items"][0]
        assert it["state"] == "onay" and not it["on"] and it["state_name"] == "Onay bekliyor"
        bek = c.get("/api/yp/content/yorum/bekleyen", headers=H).json()["items"]
        assert len(bek) == 1 and bek[0]["name"] == "Zeynep D."
    t("siteden gelen yorum onaya düşüyor, yayına çıkmıyor", e)

    def f():
        cid = c.get("/api/yp/content/yorum/bekleyen", headers=H).json()["items"][0]["id"]
        r = c.post("/api/yp/content/yorum/%s/onay" % cid, headers=H, json={"karar": "onay"}).json()
        assert r["item"]["on"] and r["item"]["state"] == "" and r["item"]["state_name"] == "Yayında"
        assert c.get("/api/yp/content/yorum", headers=H).json()["counts"]["yayin"] == 1
        c.post("/api/public/yp/yorum", json={"name": "Spam", "rating": 1, "text": "Reklam metni"})
        cid2 = c.get("/api/yp/content/yorum/bekleyen", headers=H).json()["items"][0]["id"]
        r2 = c.post("/api/yp/content/yorum/%s/onay" % cid2, headers=H, json={"karar": "red"}).json()
        assert not r2["item"]["on"] and r2["item"]["state"] == "red"
        assert c.post("/api/yp/content/yorum/%s/onay" % cid2, headers=H,
                      json={"karar": "belki"}).status_code == 422
    t("yorum onaylanıyor ve reddediliyor", f)

    def g():
        r = c.post("/api/yp/content/duyuru", headers=H,
                   json={"text": "Bayram boyunca kapalıyız", "link": "onlinekaydet.com", "color": "turuncu",
                         "until": "2026-12-31"})
        it = r.json()["item"]
        assert it["link"] == "https://onlinekaydet.com", "eksik şema tamamlanmalı"
        assert c.post("/api/yp/content/duyuru", headers=H,
                      json={"text": "X", "color": "mor"}).status_code == 422, "seçenek dışı renk"
        assert c.post("/api/yp/content/duyuru", headers=H,
                      json={"text": "X", "until": "31.12.2026"}).status_code == 422, "tarih biçimi"
    t("bağlantı düzeltiliyor, seçenek ve tarih denetleniyor", g)

    def h():
        import icerik
        rows = c.get("/api/yp/content/duyuru", headers=H).json()["items"]
        cid = rows[0]["id"]
        c.put("/api/yp/content/duyuru/%s" % cid, headers=H, json={"on": False})
        assert c.get("/api/yp/content/duyuru", headers=H).json()["counts"]["gizli"] == 1
        c.put("/api/yp/content/duyuru/%s" % cid, headers=H, json={"data": {"text": "Yeni metin"}, "on": True})
        it = [x for x in c.get("/api/yp/content/duyuru", headers=H).json()["items"] if x["id"] == cid][0]
        assert it["text"] == "Yeni metin" and it["color"] == "turuncu", "dokunulmayan alan korunmalı: %s" % it
        assert c.delete("/api/yp/content/duyuru/%s" % cid, headers=H).json()["ok"]
        assert c.delete("/api/yp/content/duyuru/%s" % cid, headers=H).status_code == 404
    t("gizleme, kısmi güncelleme ve silme çalışıyor", h)

    def i():
        r = c.get("/api/yp/content/yorum", headers=H, params={"q": "balyaj"}).json()
        assert len(r["items"]) == 1
        assert len(c.get("/api/yp/content/yorum", headers=H, params={"state": "yayin"}).json()["items"]) == 1
        assert len(c.get("/api/yp/content/yorum", headers=H, params={"state": "onay"}).json()["items"]) == 0
    t("arama ve durum süzgeci çalışıyor", i)

for x in ok: print("  ✓", x)
for x, e in bad: print("  ✗", x, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
