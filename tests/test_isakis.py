"""Sektörel iş akışları ve destek talepleri: alanlar, adımlar, imza, belge."""
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
IMZA = "data:image/png;base64," + "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}

    def a():
        r = c.get("/api/yp/is", headers=H).json()
        assert r["flows"] == [], "kuaförde sektörel iş akışı yok"
        c.post("/api/yp/sectors/teknik", headers=H, json={})
        r2 = c.get("/api/yp/is", headers=H).json()
        ids = [f["id"] for f in r2["flows"]]
        assert ids == ["servis"], ids
        fl = r2["flows"][0]
        assert fl["sign"] and fl["parts"] and fl["money"]
        assert [x["id"] for x in fl["steps"]][:3] == ["yeni", "yolda", "islemde"]
        assert any(x["key"] == "seri" for x in fl["fields"]), "seri numarası alanı olmalı"
    t("akış sektöre göre geliyor; teknik serviste servis formu açılıyor", a)

    def b():
        r = c.post("/api/yp/is/servis", headers=H, json={
            "customer": {"name": "Mehmet Yıldız", "phone": "05321112233", "address": "Kadıköy"},
            "data": {"cihaz": "Kombi", "marka": "DemirDöküm", "model": "Nitron", "seri": "DD-99120",
                     "garanti": "Garanti dışı", "sikayet": "Isıtmıyor, ekranda arıza kodu var"},
            "parts": [{"name": "Genleşme tankı", "code": "GT-8", "qty": 1, "price": 850},
                      {"name": "Conta", "qty": 2, "price": 45}],
            "labor": 600, "staff": "Usta Ali"})
        assert r.status_code == 200, r.text
        it = r.json()["item"]
        assert it["no"].startswith("SER-") and it["step"] == "yeni" and it["step_name"] == "Kayıt açıldı"
        assert it["parts_total"] == 940.0 and it["total"] == 1540.0, it
        assert not it["signed"]
        assert c.post("/api/yp/is/servis", headers=H, json={"customer": {}, "data": {}}).status_code == 422
        assert c.post("/api/yp/is/servis", headers=H, json={
            "customer": {"name": "X"}, "data": {"cihaz": "Kombi"}}).status_code == 422, "şikâyet zorunlu"
    t("servis kaydı açılıyor, parça ve işçilik toplanıyor, zorunlu alan denetleniyor", b)

    def d():
        rid = c.get("/api/yp/is/servis", headers=H).json()["items"][0]["id"]
        assert c.post("/api/yp/is/servis/%s/adim" % rid, headers=H,
                      json={"step": "yolda"}).json()["item"]["step"] == "yolda"
        assert c.post("/api/yp/is/servis/%s/adim" % rid, headers=H,
                      json={"step": "ucan"}).status_code == 422, "akışta olmayan adım"
        r = c.post("/api/yp/is/servis/%s/adim" % rid, headers=H, json={"step": "bitti"})
        assert r.status_code == 422 and "imza" in r.json()["detail"], r.json()
        assert c.post("/api/yp/is/servis/%s/imza" % rid, headers=H,
                      json={"sign": "abc"}).status_code == 422, "geçersiz imza"
        im = c.post("/api/yp/is/servis/%s/imza" % rid, headers=H,
                    json={"sign": IMZA, "by": "Mehmet Yıldız"}).json()["item"]
        assert im["signed"] and im["sign_by"] == "Mehmet Yıldız"
        bit = c.post("/api/yp/is/servis/%s/adim" % rid, headers=H, json={"step": "bitti"}).json()["item"]
        assert bit["step"] == "bitti" and len(bit["timeline"]) >= 3
    t("imzasız form tamamlanmıyor, imza alınınca kapanıyor", d)

    def e():
        rid = c.get("/api/yp/is/servis", headers=H).json()["items"][0]["id"]
        h = c.post("/api/yp/is/servis/%s/belge" % rid, headers=H).json()["html"]
        for x in ("Servis formu", "Mehmet Yıldız", "DD-99120", "Genleşme tankı", "Müşteri imzası"):
            assert x in h, "belgede %s olmalı" % x
        assert "data:image/png;base64" in h, "imza belgeye basılmalı"
        assert "1540" in h and "600" in h, "toplam ve işçilik belgede"
        assert "0532 111 22 33" in h, "telefon okunur biçimde"
        assert "window.print" in h
    t("servis belgesi kaydın kendisinden üretiliyor, imza basılıyor", e)

    def f():
        c.post("/api/yp/sectors/avukat", headers=H, json={})
        r = c.get("/api/yp/is", headers=H).json()
        assert [x["id"] for x in r["flows"]] == ["dosya"], r["flows"]
        fl = r["flows"][0]
        assert not fl["sign"], "dosya akışı imza istemez"
        assert any(x["key"] == "esas" for x in fl["fields"])
        d = c.post("/api/yp/is/dosya", headers=H, json={
            "customer": {"name": "Ali Vural"},
            "data": {"dosya_no": "2026/88", "mahkeme": "İstanbul 3. Asliye Hukuk", "esas": "2026/1234",
                     "tur": "Hukuk", "konu": "Alacak davası", "durusma": "2026-12-04"}}).json()["item"]
        assert d["no"].startswith("DOS-") and d["step"] == "acik"
        bit = c.post("/api/yp/is/dosya/%s/adim" % d["id"], headers=H, json={"step": "kapandi"}).json()["item"]
        assert bit["step"] == "kapandi", "imza istemeyen akış doğrudan kapanabilir"
        h = c.post("/api/yp/is/dosya/%s/belge" % d["id"], headers=H).json()["html"]
        assert "2026/1234" in h and "Müşteri imzası" not in h, "dosya belgesinde imza alanı olmaz"
        assert c.post("/api/yp/is/dosya/%s/imza" % d["id"], headers=H,
                      json={"sign": IMZA}).status_code == 422
    t("avukat dosyası tamamen farklı alanlarla, imzasız çalışıyor", f)

    def g():
        d = c.get("/api/yp/is/dosya", headers=H).json()
        assert d["counts"]["hepsi"] == 1 and d["counts"]["kapandi"] == 1
        assert len(c.get("/api/yp/is/dosya", headers=H, params={"q": "asliye"}).json()["items"]) == 1
        rid = d["items"][0]["id"]
        up = c.put("/api/yp/is/dosya/%s" % rid, headers=H,
                   json={"data": {"asama": "Bilirkişi raporu bekleniyor"}}).json()["item"]
        assert up["data"]["asama"].startswith("Bilirkişi") and up["data"]["esas"] == "2026/1234", "diğer alanlar korunmalı"
        assert c.delete("/api/yp/is/dosya/%s" % rid, headers=H).json()["ok"]
    t("arama, sayaç, kısmi güncelleme ve silme çalışıyor", g)

    # ---- destek talepleri
    def h():
        r = c.post("/api/yp/destek", headers=H, json={
            "subject": "Kargo fişinde barkod çıkmıyor", "category": "hata", "priority": "yuksek",
            "screen": "Siparişler",
            "body": "Siparişi seçip kargo fişi yazdırdığımda barkod boş geliyor. Ekran görüntüsü ekte.",
            "files": [{"url": "/api/files/x/1.png", "name": "ekran.png"},
                      {"url": "https://baska-site.com/kotu.png", "name": "dis"}]})
        assert r.status_code == 200, r.text
        it = r.json()["item"]
        assert it["no"].startswith("DT-") and it["state"] == "acik" and it["state_name"] == "Açık"
        ek = it["messages"][0]["files"]
        assert len(ek) == 1 and ek[0]["url"].startswith("/api/files/"), "dış bağlantı eklenmemeli: %s" % ek
        assert c.post("/api/yp/destek", headers=H, json={"subject": "kısa"}).status_code == 422
        assert c.post("/api/yp/destek", headers=H,
                      json={"subject": "Yeterince uzun konu", "body": "kısa", "category": "hata"}).status_code == 422
        assert c.post("/api/yp/destek", headers=H, json={
            "subject": "Yeterince uzun konu", "body": "Yeterince uzun bir açıklama metni",
            "category": "olmayan"}).status_code == 422
    t("destek talebi açılıyor, dış bağlantılı ek reddediliyor", h)

    def i():
        tid = c.get("/api/yp/destek", headers=H).json()["items"][0]["id"]
        r = c.post("/api/yp/destek/%s/mesaj" % tid, headers=H, json={"text": "Bir de şunu fark ettim"}).json()
        assert r["item"]["n_mesaj"] == 2
        assert c.post("/api/yp/destek/%s/mesaj" % tid, headers=H, json={}).status_code == 422
        k = c.post("/api/yp/destek/%s/kapat" % tid, headers=H, json={"rating": 5}).json()["item"]
        assert k["state"] == "kapandi" and k["rating"] == 5
        son = c.post("/api/yp/destek/%s/mesaj" % tid, headers=H, json={"text": "tekrar"})
        assert son.status_code == 422 and "yeni talep" in son.json()["detail"], son.json()
        lst = c.get("/api/yp/destek", headers=H).json()
        assert lst["counts"]["kapandi"] == 1 and lst["counts"]["acik"] == 0
    t("talebe mesaj ekleniyor, kapanan talep yeniden açılmıyor", i)

for x in ok: print("  ✓", x)
for x, e in bad: print("  ✗", x, "\n", e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA %d/%d" % (len(bad), len(ok) + len(bad))))
