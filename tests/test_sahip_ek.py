"""Sahip paneli: talepler (düzenle/not/sil/toplu/CSV/firma bağı), platform muhasebesi, destek girişi, ziyaretçi izleme."""
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
    r = c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}); A = {"Authorization": "Bearer " + r.json()["token"]}
    S = {}
    def demo():
        r = c.post("/api/public/demo", json={"name": "Ahmet Yılmaz", "phone": "05321112233", "sector": "kuafor"}); assert r.status_code == 200, r.text
        r = c.post("/api/public/lead", json={"name": "Ayşe", "phone": "05329998877", "form": "iletisim", "extra": {"mesaj": "x" * 300}}); assert r.status_code == 200
        c.post("/api/public/lead", json={"name": "Veli", "phone": "05328887766", "form": "sikayet-ve-oneri", "extra": {"mesaj": "Şikayet metni"}})
    t("demo ve lead kayıt", demo)
    def liste():
        r = c.get("/api/admin/talepler", headers=A).json(); L = r["leads"]
        d = [l for l in L if l.get("form") == "demo-hesabi"][0]
        assert d.get("firm_id") and d["firm_demo"], d
        S["demo"], S["firm"] = d["id"], d["firm_id"]
        assert "iletisim" in r["formlar"] and "sikayet-ve-oneri" in r["formlar"], r["formlar"]
        assert len([l for l in L if l.get("form") == "iletisim"][0]["extra"]["mesaj"]) == 300
        assert len(c.get("/api/admin/talepler?form=iletisim", headers=A).json()["leads"]) == 1
        assert len(c.get("/api/admin/talepler?q=ayşe", headers=A).json()["leads"]) == 1
    t("liste, form süzgeci, firma bağı", liste)
    def duz():
        L = {l["name"]: l for l in c.get("/api/admin/talepler", headers=A).json()["leads"]}; i = L["Ayşe"]["id"]; S["a"] = i
        assert c.put("/api/admin/talepler/" + i, headers=A, json={"name": "Ayşe K", "phone": "0 532 999 88 11", "note": "arayacağım", "status": "arandi"}).status_code == 200
        assert c.put("/api/admin/talepler/" + i, headers=A, json={"phone": "123"}).status_code == 422
        n = c.post("/api/admin/talepler/%s/not" % i, headers=A, json={"metin": "Pazartesi demo"}); assert n.status_code == 200
        assert c.post("/api/admin/talepler/%s/not" % i, headers=A, json={"metin": " "}).status_code == 422
        l = [x for x in c.get("/api/admin/talepler", headers=A).json()["leads"] if x["id"] == i][0]
        assert l["name"] == "Ayşe K" and l["phone"] == "5329998811" and len(l["notlar"]) == 1 and l["status"] == "arandi"
        assert c.delete("/api/admin/talepler/%s/not/%s" % (i, n.json()["id"]), headers=A).status_code == 200
    t("düzenle ve not", duz)
    def toplu_csv():
        csvt = c.get("/api/admin/talepler.csv", headers=A); assert csvt.status_code == 200 and "Ayşe K" in csvt.text and "Şikayet" not in csvt.text.split("\n")[0]
        ids = [l["id"] for l in c.get("/api/admin/talepler?form=sikayet-ve-oneri", headers=A).json()["leads"]]
        assert c.post("/api/admin/talepler/toplu", headers=A, json={"ids": ids, "islem": "durum", "durum": "olumsuz"}).json()["adet"] == 1
        assert c.post("/api/admin/talepler/toplu", headers=A, json={"ids": ids, "islem": "sil"}).json()["adet"] == 1
        assert c.delete("/api/admin/talepler/" + S["a"], headers=A).status_code == 200
        assert c.delete("/api/admin/talepler/" + S["a"], headers=A).status_code == 404
        assert c.post("/api/admin/talepler/toplu", headers=A, json={"ids": [], "islem": "sil"}).status_code == 422
    t("toplu, CSV, silme", toplu_csv)
    def muh():
        assert c.post("/api/admin/firms/%s/payments" % S["firm"], headers=A, json={"amount": 1500, "method": "havale", "extend_days": 30}).status_code == 200
        bu = __import__("datetime").datetime.now().strftime("%Y-%m")
        r = c.post("/api/admin/muhasebe", headers=A, json={"tur": "gider", "tutar": "300,50", "kategori": "Reklam", "aciklama": "Google Ads"}); assert r.status_code == 200, r.text; eid = r.json()["id"]
        assert c.post("/api/admin/muhasebe", headers=A, json={"tur": "gider", "tutar": 0}).status_code == 422
        assert c.post("/api/admin/muhasebe", headers=A, json={"tur": "x", "tutar": 5}).status_code == 422
        m = c.get("/api/admin/muhasebe?ay=" + bu, headers=A).json()
        assert m["gelir"] == 1500 and m["gider"] == 300.5 and m["net"] == 1199.5 and len(m["seri"]) == 12 and m["seri"][-1]["ay"] == bu, m
        assert "Google Ads" in c.get("/api/admin/muhasebe.csv?ay=" + bu, headers=A).text
        pid = [k["id"] for k in m["kayitlar"] if k["kaynak"] == "odeme"][0]
        assert c.delete("/api/admin/muhasebe/" + pid, headers=A).status_code == 404
        assert c.delete("/api/admin/muhasebe/" + eid, headers=A).status_code == 200
    t("platform muhasebesi", muh)
    def destek():
        u = c.post("/api/admin/firms/%s/support-link" % S["firm"], headers=A, json={"to": "salon", "h": "site"}).json()["url"]
        r = c.get(u, follow_redirects=False); assert r.status_code == 200 and '"/salon#site"' in r.text and "ypt" in r.text, r.text[:400]
        u2 = c.post("/api/admin/firms/%s/support-link" % S["firm"], headers=A).json()["url"]
        assert '"/admin"' in c.get(u2).text
        u3 = c.post("/api/admin/firms/%s/support-link" % S["firm"], headers=A, json={"to": "salon", "h": "x\"><script>"}).json()["url"]
        assert "<script>" not in c.get(u3).text.split("location.replace")[1]
    t("destek girişi salon/hash", destek)
    def izle():
        H = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/604.1"}
        c.cookies.clear()
        assert c.post("/api/public/track", headers=H, json={"sid": "abcdefgh12345", "event": "pageview", "path": "/muhasebe-ve-stok.html", "referrer": "https://www.google.com/", "host": "onlinekaydet.com", "search": "?utm_source=google&utm_medium=cpc"}).status_code == 200
        c.post("/api/public/track", headers=H, json={"sid": "abcdefgh12345", "event": "event", "label": "form_submit", "path": "/iletisim.html"})
        live = c.get("/api/analytics/live", headers=A).json(); assert live["active"] >= 1, live
        ss = [x for x in live["sessions"] if x["id"] == "abcdefgh12345"][0]; assert ss["conv_form"] == 1 and ss["current_page"].startswith("/muhasebe"), ss
        assert c.get("/api/analytics/overview?days=7", headers=A).status_code == 200
    t("ziyaretçi izleme", izle)
    t("yetkisiz", lambda: [(c.cookies.clear(), None) and None, [None for u in ("/api/admin/talepler", "/api/admin/muhasebe", "/api/admin/talepler.csv") if c.get(u).status_code not in (401, 403) and (_ for _ in ()).throw(AssertionError(u))]])
print("OK", len(ok), ok if not bad else "")
for n, e in bad: print("HATA", n, e)
sys.exit(1 if bad else 0)
