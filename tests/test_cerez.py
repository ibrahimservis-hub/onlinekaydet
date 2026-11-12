"""Çerez bandı: tek tuşla açılır, politika sayfası kendiliğinden gelir, ölçüm betiği onay bekler."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-500:]))

import cerez

def a():
    c = cerez.temizle({"on": True, "pos": "yok", "ay": 99, "link": "javascript:kotu()"})
    assert c["pos"] == "alt" and c["ay"] == 24 and c["link"] == "/cerez-politikasi"
    c2 = cerez.temizle({"link": "https://ornek.com/cerez"}); assert c2["link"] == "https://ornek.com/cerez"
    c3 = cerez.temizle({"link": "/gizlilik-kvkk"}); assert c3["link"] == "/gizlilik-kvkk"
    assert cerez.temizle({"ay": 0})["ay"] == 1
t("ayarlar temizlenir: konum, süre, bağlantı (javascript: engellenir)", a)

def b():
    assert cerez.band(cerez.temizle({"on": False})) == "", "kapalıyken band üretilmemeli"
    h = cerez.ekle("<body>x</body>", cerez.temizle({"on": False}))
    assert h == "<body>x</body>"
t("kapalıyken siteye hiçbir şey eklenmez", b)

def c_():
    cfg = cerez.temizle({"on": True, "text": "<script>kotu()</script> & yazı", "accept": "Tamam <b>"})
    bd = cerez.band(cfg)
    assert "&lt;script&gt;" in bd and "<script>kotu" not in bd, "metin kaçırılmalı"
    assert "Tamam &lt;b&gt;" in bd
t("müşterinin yazdığı metin siteye betik olarak geçemez", c_)

def d_():
    bd = cerez.band(cerez.temizle({"on": True, "pos": "ortada pencere"}))
    assert '<div id="okc-ov">' in bd, "ortada pencere arka planı olmalı"
    bd2 = cerez.band(cerez.temizle({"on": True, "pos": "üst"}))
    assert "top:16px" in bd2 and '<div id="okc-ov">' not in bd2
    bd3 = cerez.band(cerez.temizle({"on": True, "pos": "alt"}))
    assert "bottom:16px" in bd3
t("üç konum da doğru üretilir", d_)

def e():
    bd = cerez.band(cerez.temizle({"on": True}), accent="#b4600a")
    assert "#b4600a" in bd, "düğme temanın rengini almalı"
    assert 'B=["olcum","pazarlama"]' in bd, "ölçüm ve pazarlama onaya bağlanmalı"
    bd2 = cerez.band(cerez.temizle({"on": True, "olcum": False, "pazarlama": False}))
    assert "B=[]" in bd2, "hiçbiri bağlı değilse liste boş"
    assert "localStorage" in bd and "document.cookie" not in bd, "band kendisi çerez kurmamalı"
t("düğme tema rengini alır; band çerez kurmaz, onayı yerel depolar", e)

def f():
    cfg = cerez.temizle({"on": True, "reject": ""})
    assert 'data-ok-cerez="red"' not in cerez.band(cfg), "reddet yazısı boşsa düğme çıkmamalı"
    assert 'data-ok-cerez="kabul"' in cerez.band(cfg)
t("reddet düğmesi isteğe bağlı", f)

with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Can Demir", "phone": "05524165788", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}

    def g():
        d = c.get("/api/yp/cerez", headers=H); assert d.status_code == 200, d.text
        v = d.json(); assert v["cfg"]["on"] is False and "alt" in v["konumlar"]
        assert v["bekleyen"] == ["olcum", "pazarlama"]
    t("panel ayarları okur; band varsayılan olarak kapalıdır", g)

    def h_():
        h1 = c.get("/api/site/preview", headers=H).text
        assert 'id="okc"' not in h1 and "okCerez" not in h1, "kapalıyken sitede görünmemeli"
        assert c.get("/api/site/preview?path=/cerez-politikasi", headers=H).status_code == 404, "kapalıyken politika sayfası da olmamalı"
    t("kapalıyken ne band ne politika sayfası vardır", h_)

    def i():
        r = c.put("/api/yp/cerez", headers=H, json={"on": True, "text": "Çerez kullanıyoruz.", "pos": "alt"})
        assert r.status_code == 200 and r.json()["cfg"]["on"] is True
        h1 = c.get("/api/site/preview", headers=H).text
        assert 'id="okc"' in h1 and "Çerez kullanıyoruz." in h1, "band siteye eklenmeli"
        assert "spx-credit" in h1, "OnlineKaydet bağlantısı yerinde kalmalı"
    t("tek tuşla açılır, band her sayfaya eklenir, alt bilgi bağlantısı bozulmaz", i)

    def k():
        r = c.get("/api/site/preview?path=/cerez-politikasi", headers=H)
        assert r.status_code == 200, "politika sayfası kendiliğinden açılmalı"
        assert "erez" in r.text
        assert c.get("/api/site/preview?path=/gizlilik-kvkk", headers=H).status_code == 200
        h1 = c.get("/api/site/preview", headers=H).text
        assert "/cerez-politikasi" in h1, "alt bilgide politika bağlantısı olmalı"
    t("çerez politikası ve KVKK metni mağazasız sitede de açılır, alt bilgiden bağlanır", k)

    def m():
        h1 = c.get("/api/site/preview", headers=H).text
        i1 = h1.find('id="okc"')
        assert h1.find("okCerez", i1) > 0, "betik banddan sonra gelmeli"
        assert "window.okCerez" in h1 and "izin:function" in h1, "betikleri bekletecek arayüz olmalı"
    t("ölçüm betikleri için bekletme arayüzü (window.okCerez) siteye konur", m)

print("\n".join("  ✓ " + n for n in ok))
for n, e in bad: print("  ✗ " + n + "\n" + e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA: %d/%d" % (len(bad), len(ok) + len(bad))))
sys.exit(1 if bad else 0)
