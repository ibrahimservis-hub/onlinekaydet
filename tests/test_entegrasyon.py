"""Entegrasyon merkezi: izin, anahtar gizliliği, deneme ve hata mesajları."""
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
        r = c.get("/api/yp/integrations", headers=H).json()
        ids = [i["id"] for i in r["items"]]
        assert "netgsm" in ids and "google_isletme" in ids, ids
        assert "trendyol" not in ids and "nebim" not in ids, "kuaförde pazaryeri/ERP görünmemeli: %s" % ids
        assert all(i["state"] == "yok" for i in r["items"])
        assert r["counts"]["bagli"] == 0
    t("panelde yalnız sektör paketindeki entegrasyonlar görünüyor", a)

    def b():
        c.post("/api/yp/sectors/eticaret", headers=H, json={})
        r = c.get("/api/yp/integrations", headers=H).json()
        ids = [i["id"] for i in r["items"]]
        for x in ("iyzico", "aras", "parasut", "nebim", "trendyol", "ga4"):
            assert x in ids, "%s eksik" % x
        gr = {g["id"]: g for g in r["groups"]}
        assert gr["pos"]["n"] >= 3 and gr["kargo"]["n"] >= 4 and gr["erp"]["n"] >= 4, gr
        assert c.get("/api/yp/integrations?group=kargo", headers=H).json()["items"][0]["group"] == "kargo"
    t("e-ticaret paketinde POS, kargo, e-fatura, ERP ve pazaryeri açılıyor", b)

    def d():
        r = c.put("/api/yp/integrations/netgsm", headers=H,
                  json={"keys": {"user": "8503030000", "pass": "gizli123", "header": "ONLINEKAYD"}, "on": True})
        assert r.status_code == 200 and r.json()["ok"], r.text
        it = r.json()["item"]
        assert it["state"] == "bagli" and it["mode"] == "test"
        gizli = [f for f in it["fields"] if f["key"] == "pass"][0]
        assert gizli["value"] == "••••i123" or gizli["value"].startswith("••••"), gizli
        assert "gizli123" not in r.text, "şifre düz metin dönmemeli"
        lst = c.get("/api/yp/integrations", headers=H).text
        assert "gizli123" not in lst, "listede de dönmemeli"
    t("anahtar kaydediliyor ama hiçbir uçta düz metin dönmüyor", d)

    def e():
        r = c.put("/api/yp/integrations/netgsm", headers=H, json={"keys": {"header": "YENIBASLIK"}})
        it = r.json()["item"]
        assert [f for f in it["fields"] if f["key"] == "header"][0]["value"] == "YENIBASLIK"
        assert [f for f in it["fields"] if f["key"] == "pass"][0]["filled"], "boş gönderilen şifre silinmemeli"
        r2 = c.put("/api/yp/integrations/netgsm", headers=H, json={"keys": {"pass": "••••i123"}})
        assert [f for f in r2.json()["item"]["fields"] if f["key"] == "pass"][0]["filled"], "maskeli değer kaydedilmemeli"
        assert c.post("/api/yp/integrations/netgsm/test", headers=H).json()["ok"], "deneme geçmeli"
    t("boş veya maskeli gönderilen gizli alan eski değeri koruyor", e)

    def f():
        r = c.put("/api/yp/integrations/ga4", headers=H, json={"keys": {"id": "UA-12345"}, "on": True})
        assert not r.json()["ok"] and "G-" in r.json()["err"], r.json()
        it = c.get("/api/yp/integrations/ga4", headers=H).json()["item"]
        assert it["state"] == "hata" and it["err"], it
        r2 = c.put("/api/yp/integrations/ga4", headers=H, json={"keys": {"id": "G-ABC123DEF4"}})
        assert r2.json()["ok"] and r2.json()["item"]["state"] == "bagli"
    t("yanlış biçimdeki anahtar hemen sebebiyle reddediliyor", f)

    def g():
        r = c.put("/api/yp/integrations/aras", headers=H, json={"keys": {"user": "ABC"}, "on": True})
        assert not r.json()["ok"] and "Şifre" in r.json()["err"], r.json()
        r2 = c.put("/api/yp/integrations/smtp", headers=H,
                   json={"keys": {"host": "mail.x.com", "port": "123", "user": "a", "pass": "b", "from": "a@x.com"}})
        assert "Kapı numarası" in r2.json()["err"], r2.json()
        r3 = c.put("/api/yp/integrations/havale", headers=H, json={"keys": {"iban": "TR12", "unvan": "X"}})
        assert "IBAN" in r3.json()["err"], r3.json()
        r4 = c.put("/api/yp/integrations/gib_earsiv", headers=H, json={"keys": {"vkn": "123", "pass": "x"}})
        assert "VKN" in r4.json()["err"], r4.json()
        r5 = c.put("/api/yp/integrations/nebim", headers=H,
                   json={"keys": {"url": "erp.firma.com", "user": "a", "pass": "b"}})
        assert "http" in r5.json()["err"], r5.json()
    t("eksik alan, kapı, IBAN, VKN ve sunucu adresi anlaşılır hatayla dönüyor", g)

    def h():
        r = c.put("/api/yp/integrations/iyzico", headers=H, json={
            "keys": {"merchant": "1", "api_key": "sandbox-abc", "api_secret": "sandbox-xyz"}, "mode": "canli"})
        assert not r.json()["ok"] and "test anahtar" in r.json()["err"], r.json()
        r2 = c.put("/api/yp/integrations/iyzico", headers=H, json={
            "keys": {"api_key": "canli-abc", "api_secret": "canli-xyz"}, "mode": "canli", "on": True})
        assert r2.json()["ok"] and r2.json()["item"]["mode"] == "canli", r2.json()
    t("canlı moda test anahtarıyla geçilemiyor", h)

    def i():
        assert c.put("/api/yp/integrations/yok", headers=H, json={"keys": {}}).status_code == 404
        assert c.put("/api/yp/integrations/netgsm", headers=H, json={"keys": {}, "mode": "yarin"}).status_code == 422
        assert c.post("/api/yp/integrations/parasut/test", headers=H).status_code == 422, "kaydetmeden deneme olmaz"
        c.post("/api/yp/sectors/kuafor", headers=H, json={})
        assert c.put("/api/yp/integrations/nebim", headers=H, json={"keys": {}}).status_code == 403, "paket dışı"
        assert c.get("/api/yp/integrations/nebim", headers=H).status_code == 403

    def j():
        c.post("/api/yp/sectors/eticaret", headers=H, json={})
        u = c.get("/api/yp/integrations/netgsm", headers=H).json()["uses"]
        adlar = [x["name"] for x in u]
        assert adlar, "SMS entegrasyonunun nerede kullanıldığı listelenmeli"
        assert not [a for a in adlar if a.startswith("Randevu")], "e-ticarette randevu bildirimi gösterilmemeli: %s" % adlar
        k2 = c.get("/api/yp/integrations/aras", headers=H).json()["uses"]
        assert any("Kargo fişi" in x["name"] for x in k2), k2
    t("paket dışı ve hatalı istekler reddediliyor", i)
    t("entegrasyonun nerede kullanıldığı pakete göre listeleniyor", j)

    def k():
        c.post("/api/yp/sectors/eticaret", headers=H, json={})
        r = c.get("/api/yp/integrations/log/son", headers=H).json()
        assert len(r["items"]) >= 5
        assert r["items"][0]["name"] and r["items"][0]["event"]
        assert all("pass" not in str(x.get("note", "")) for x in r["items"])
        assert c.delete("/api/yp/integrations/ga4", headers=H).json()["ok"]
        assert c.get("/api/yp/integrations/ga4", headers=H).json()["item"]["state"] == "yok"
    t("işlem kaydı tutuluyor, bağlantı kaldırılabiliyor", k)

for x in ok: print("  ✓", x)
for x, e in bad: print("  ✗", x, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
