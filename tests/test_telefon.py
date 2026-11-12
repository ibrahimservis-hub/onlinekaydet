"""Telefon görünümü: bölüm sırası, gizleme ve yazılar telefona ayrı tutulur; bilgisayar etkilenmez."""
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

import sitegen

def ua():
    assert sitegen.is_phone("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1 Mobile/15E148")
    assert sitegen.is_phone("Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36")
    assert not sitegen.is_phone("Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1 Mobile/15E148"), "tablet telefon sayılmamalı"
    assert not sitegen.is_phone("Mozilla/5.0 (Linux; Android 13; SM-X200) AppleWebKit/537.36 Chrome/120 Safari/537.36"), "Android tablet telefon sayılmamalı"
    assert not sitegen.is_phone("Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36")
    assert not sitegen.is_phone("")
t("tarayıcı imzasından telefon/bilgisayar ayrımı (tablet bilgisayar sayılır)", ua)

def over():
    ctx = {"p": {"phone": {"layout": {"order": ["B", "A"], "hidden": ["C"]}}}, "dev": "phone"}
    assert sitegen.phone_over(ctx)["layout"]["order"] == ["B", "A"]
    assert sitegen.phone_over(dict(ctx, dev="")) == {}, "bilgisayarda telefon katmanı uygulanmamalı"
t("telefon katmanı yalnız telefon görünümünde okunur", over)

with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe Yıldız", "phone": "05524165799", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    PH = {"user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1 Mobile/15E148"}

    def a():
        r = c.get("/api/site/blocks", headers=H); assert r.status_code == 200, r.text
        d = r.json(); assert d["blocks"] and d["dev"] == "web" and d["own_order"] is False
        S["ad"] = [b["name"] for b in d["blocks"]]
        assert all(b["own"] is False for b in d["blocks"])
    t("bilgisayar bölümleri listelenir (telefona özel hiçbir şey yok)", a)

    def b():
        d = c.get("/api/site/blocks?dev=phone", headers=H).json()
        assert [x["name"] for x in d["blocks"]] == S["ad"], "telefon ayarı yokken sıra bilgisayardakiyle aynı olmalı"
        assert d["dev"] == "phone" and d["own_order"] is False
    t("telefon ayarı yokken her şey bilgisayardan miras alınır", b)

    def d_():
        p = c.get("/api/site/profile", headers=H).json()["profile"]
        ters = list(reversed(S["ad"]))
        p["phone"] = {"layout": {"order": ters, "hidden": [S["ad"][0]]}}
        assert c.put("/api/site/profile", headers=H, json=p).status_code == 200
        S["ters"] = ters
        d = c.get("/api/site/blocks?dev=phone", headers=H).json()
        assert d["own_order"] is True
        gor = [x["name"] for x in d["blocks"] if not x["hidden"]]
        ikisi = [n for n in ters if n in gor][:2]
        assert len(ikisi) == 2 and gor.index(ikisi[0]) < gor.index(ikisi[1]), "telefonda sıra ters olmalı"
        wgor = [x["name"] for x in c.get("/api/site/blocks", headers=H).json()["blocks"] if not x["hidden"]]
        assert gor != wgor, "telefon sırası bilgisayardan farklı olmalı"
        assert [x for x in d["blocks"] if x["name"] == S["ad"][0]][0]["hidden"] is True
        w = c.get("/api/site/blocks", headers=H).json()
        assert [x["name"] for x in w["blocks"]] == S["ad"], "bilgisayar sırası bozulmamalı"
        assert [x for x in w["blocks"] if x["name"] == S["ad"][0]][0]["hidden"] is False, "bilgisayarda gizlenmemeli"
    t("telefona ayrı sıra ve gizleme verilir, bilgisayar etkilenmez", d_)

    def e():
        p = c.get("/api/site/profile", headers=H).json()["profile"]
        assert p.get("phone", {}).get("layout", {}).get("hidden") == [S["ad"][0]], "telefon ayarı kaydedilmeli"
        eski = dict(p); eski.pop("phone", None); eski.pop("imgedits", None)
        assert c.put("/api/site/profile", headers=H, json=eski).status_code == 200
        p2 = c.get("/api/site/profile", headers=H).json()["profile"]
        assert p2.get("phone", {}).get("layout", {}).get("order") == S["ters"], "eski panel telefon ayarını silmemeli"
    t("telefon ayarını bilmeyen eski panel kaydı onu silmez", e)

    def f():
        ad = S["ad"][1]
        r = c.get("/api/site/block-text?name=" + ad, headers=H); assert r.status_code == 200, r.text
        tx = r.json()["texts"]; assert tx, "düzenlenebilir yazı yok"
        S["blok"] = ad; S["ix"] = tx[0]["i"]; S["web0"] = tx[0]["text"]
        p = c.get("/api/site/profile", headers=H).json()["profile"]
        th = c.get("/api/brand", headers=H).json()["brand"]["theme"]; S["th"] = th
        p["phone"] = dict(p.get("phone") or {}, edits={th: {ad: {str(S["ix"]): "TELEFONA ÖZEL BAŞLIK"}}})
        assert c.put("/api/site/profile", headers=H, json=p).status_code == 200
        pt = c.get("/api/site/block-text?name=%s&dev=phone" % ad, headers=H).json()
        x = [y for y in pt["texts"] if y["i"] == S["ix"]][0]
        assert x["text"] == "TELEFONA ÖZEL BAŞLIK" and x["own"] is True and x["web"] == S["web0"]
        wt = c.get("/api/site/block-text?name=" + ad, headers=H).json()["texts"]
        assert [y for y in wt if y["i"] == S["ix"]][0]["text"] == S["web0"], "bilgisayardaki yazı değişmemeli"
    t("telefona özel yazı yazılır; bilgisayardaki yazı korunur ve geri dönüş için saklanır", f)

    def g():
        h1 = c.get("/api/site/preview?dev=phone", headers=H).text
        h2 = c.get("/api/site/preview", headers=H).text
        assert "TELEFONA ÖZEL BAŞLIK" in h1, "telefon önizlemesinde telefona özel yazı görünmeli"
        assert "TELEFONA ÖZEL BAŞLIK" not in h2, "bilgisayar önizlemesinde görünmemeli"
    t("önizleme cihaza göre doğru sürümü üretir", g)

    def h():
        p = c.get("/api/site/profile", headers=H).json()["profile"]
        p["phone"] = {"layout": {"order": ["<script>kötü</script>" * 20], "hidden": []},
                      "edits": {S["th"]: {S["blok"]: {"9e9": "x", "0": "y" * 5000}}},
                      "imgedits": {S["th"]: {S["blok"]: {"0": "kotu-anahtar"}}},
                      "ui": {"side": "sag", "cols": 2, "kotu" * 30: "z"}}
        assert c.put("/api/site/profile", headers=H, json=p).status_code == 200
        q = c.get("/api/site/profile", headers=H).json()["profile"]["phone"]
        assert len(q["layout"]["order"][0]) <= 60, "uzun ad kırpılmalı"
        assert "9e9" not in q["edits"][S["th"]][S["blok"]], "sayı olmayan sıra alınmamalı"
        assert len(q["edits"][S["th"]][S["blok"]]["0"]) <= 600, "uzun yazı kırpılmalı"
        assert not (q.get("imgedits") or {}).get(S["th"], {}).get(S["blok"]), "geçersiz resim anahtarı alınmamalı"
        assert all(len(k) <= 40 for k in q["ui"]), "uzun ayar adı kırpılmalı"
    t("telefon ayarları kaydedilirken temizlenir (uzunluk, tür, resim anahtarı)", h)

print("\n".join("  ✓ " + n for n in ok))
for n, e in bad: print("  ✗ " + n + "\n" + e)
print(("OK %d geçti" % len(ok)) if not bad else ("HATA: %d/%d" % (len(bad), len(ok) + len(bad))))
sys.exit(1 if bad else 0)
