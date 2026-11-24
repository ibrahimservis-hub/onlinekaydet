"""Satın alma akışı: canlı fiyat, tutar güvenliği, iyzico doğrulaması, tek seferlik işleme, firma açma/yenileme, fatura, havale, hata kurtarma."""
import sys, os, re, asyncio
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
import entg_probe, notify, firms, satin_al
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-1100:]))
class R:
    def __init__(self, code=200, j=None): self.status_code = code; self._j = j or {}; self.text = str(j)
    def json(self): return self._j
IYZ = {"detay": None, "init": []}
def sahte(yontem, url, **kw):
    if "checkoutform/initialize" in url:
        import json; IYZ["init"].append(json.loads(kw["data"]))
        return R(200, {"status": "success", "token": "tok%d" % len(IYZ["init"]), "paymentPageUrl": "https://sandbox-cpp.iyzipay.com/?token=x"})
    if "checkoutform/auth/ecom/detail" in url:
        return R(200, IYZ["detay"])
    if "iyzipay" in url: return R(200, {"status": "success"})
    return R(404)
entg_probe._istek = sahte
POSTA = []
def gonder(cfg, channel, to, text, subject):
    if channel == "email": POSTA.append((to, text)); return "ok"
    return "x"
notify._dispatch = gonder
loop = asyncio.new_event_loop()
FORM = {"ad": "Ayşe Kaya", "firma": "Kaya Servis", "email": "ayse@kayaservis.com", "telefon": "05321112233", "vergi_no": "1234567890",
        "vergi_dairesi": "Çankaya", "adres": "Atatürk Bulvarı No 5 Çankaya", "il": "Ankara", "sektor": "kombi", "paket": "profesyonel", "sure": "yillik", "kabul": True}

with TestClient(s.app) as c:
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    c.cookies.clear()
    def oku(): return c.get("/api/public/satin-al/paketler").json()
    def yolla(**kw):
        satin_al._RATE.clear(); d = dict(FORM); d.update(kw); return c.post("/api/public/satin-al/siparis", json=d)
    def donus(token): return c.post("/api/public/satin-al/donus", data={"token": token}, follow_redirects=False)

    def a():
        r = oku(); p = {x["id"]: x for x in r["paketler"]}
        pr = p["profesyonel"]
        assert pr["yillik"]["matrah"] == 19900 and pr["yillik"]["kdv"] == 3980 and pr["yillik"]["toplam"] == 23880, pr["yillik"]
        assert pr["aylik"]["toplam"] == 2388.0, pr["aylik"]
        assert len(r["sektorler"]) > 40 and r["kdv"] == 20
    t("fiyat, KDV ve toplam sunucuda hesaplanıyor", a)

    def b():
        pk = c.get("/api/admin/packages", headers=A).json()["packages"]
        pk["profesyonel"]["price"] = 2500; pk["profesyonel"]["yearly"] = 24000
        assert c.put("/api/admin/packages", headers=A, json={"packages": pk}).status_code == 200
        pr = {x["id"]: x for x in oku()["paketler"]}["profesyonel"]
        assert pr["aylik"]["matrah"] == 2500 and pr["yillik"]["matrah"] == 24000 and pr["yillik"]["toplam"] == 28800, pr
        assert c.put("/api/admin/satis/ayar", headers=A, json={"kdv": 10}).json()["kdv"] == 10
        assert {x["id"]: x for x in oku()["paketler"]}["profesyonel"]["yillik"]["toplam"] == 26400
        o = yolla().json(); assert o["fiyat"]["toplam"] == 26400, o
        pk["profesyonel"]["price"] = 1990; pk["profesyonel"]["yearly"] = 19900
        c.put("/api/admin/packages", headers=A, json={"packages": pk}); c.put("/api/admin/satis/ayar", headers=A, json={"kdv": 20})
        c.post("/api/admin/satis/siparisler/%s/iptal" % o["no"], headers=A)
    t("paket fiyatı ve KDV değişince satın alma tutarı değişiyor", b)

    def d():
        assert yolla(email="kotu").status_code == 422
        assert yolla(telefon="123").status_code == 422
        assert yolla(vergi_no="12").status_code == 422
        assert yolla(kabul=False).status_code == 422
        assert yolla(sektor="yok").status_code == 422
        assert yolla(paket="yok").status_code == 422
        r = yolla(toplam=1, tutar=1, matrah=1).json()
        assert r["fiyat"]["toplam"] == 23880, "istemciden gelen tutar kabul edilmemeli"
        assert c.post("/api/public/satin-al/odeme", json={"no": r["no"], "k": "yanlis", "yontem": "kart"}).status_code == 404
        assert c.get("/api/public/satin-al/durum", params={"no": r["no"], "k": "yanlis"}).status_code == 404
    t("doğrulama, tutar güvenliği ve erişim kodu", d)

    def e():
        r = yolla(email="kapali@x.com").json()
        x = c.post("/api/public/satin-al/odeme", json={"no": r["no"], "k": r["k"], "yontem": "kart"})
        assert x.status_code == 503 and "kapalı" in x.text, x.text
    t("iyzico bağlı değilken kart ödemesi dürüstçe kapalı", e)

    c.put("/api/admin/baglanti/iyzico", headers=A, json={"keys": {"api_key": "sandbox-a", "secret": "sandbox-b", "mode": "test"}, "on": True})
    c.put("/api/admin/baglanti/havale", headers=A, json={"keys": {"iban": "TR330006100519786457841326", "unvan": "Servis Yazılım", "banka": "Banka"}, "on": True})
    c.put("/api/admin/satis/ayar", headers=A, json={"unvan": "Servis Yazılım Ltd", "vkn": "1112223334", "vergi_dairesi": "Çankaya", "adres": "Ankara", "eposta": "bilgi@onlinekaydet.com"})

    def f():
        r = yolla().json()
        x = c.post("/api/public/satin-al/odeme", json={"no": r["no"], "k": r["k"], "yontem": "kart"}).json()
        assert x["url"].startswith("https://sandbox-cpp.iyzipay.com"), x
        g = IYZ["init"][-1]
        assert g["price"] == "23880.00" and g["basketId"] == r["no"] and g["callbackUrl"].endswith("/api/public/satin-al/donus"), g
        assert g["buyer"]["gsmNumber"] == "+905321112233" and g["buyer"]["city"] == "Ankara"
        R1["r"] = r; R1["tok"] = "tok%d" % len(IYZ["init"])
    R1 = {}
    t("kart ödemesi doğru tutar ve adresle başlıyor", f)

    def g():
        r, tok = R1["r"], R1["tok"]
        IYZ["detay"] = {"status": "success", "paymentStatus": "SUCCESS", "paidPrice": "23880.00", "basketId": r["no"], "paymentId": "9001"}
        POSTA.clear()
        x = donus(tok)
        assert x.status_code == 303 and "satin-al-sonuc.html?no=%s&k=%s" % (r["no"], r["k"]) in x.headers["location"], x.headers
        st = c.get("/api/public/satin-al/durum", params={"no": r["no"], "k": r["k"]}).json()
        assert st["durum"] == "tamamlandi" and st["giris"] and st["fatura_no"].startswith("OK2026"), st
        fr = loop.run_until_complete(s.db.main().firms.find({"login_email": FORM["email"]}).to_list(5)) if False else None
        L = loop.run_until_complete(s.db.main().firms.find({"login_email": FORM["email"]}).to_list(5))
        assert len(L) == 1 and L[0]["package"] == "profesyonel" and L[0]["name"] == "Kaya Servis" and L[0]["expires_at"], L
        assert "muhasebe" in L[0]["modules"] and L[0]["sector"] == "kombi"
        assert len(POSTA) == 1 and POSTA[0][0] == FORM["email"]
        sifre = re.search(r"Şifre: (\S+)", POSTA[0][1]).group(1)
        assert c.post("/api/auth/login", json={"email": FORM["email"], "password": sifre}).status_code == 200, "e-postadaki şifreyle giriş yapılabilmeli"
        assert "fatura/%s.pdf?k=%s" % (r["no"], r["k"]) in POSTA[0][1]
        pdf = c.get("/api/public/satin-al/fatura/%s.pdf" % r["no"], params={"k": r["k"]})
        assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF", pdf.status_code
        c.cookies.clear()
        o = loop.run_until_complete(s.db.main().outbox.find_one({"kind": "satis_bilgi"}))
        assert sifre not in o["text"], "şifre kayıt defterine düz yazılmamalı"
        pm = loop.run_until_complete(s.db.main().firm_payments.find({"firm_id": L[0]["id"]}).to_list(5))
        assert len(pm) == 1 and pm[0]["amount"] == 23880
        R1["firm"] = L[0]
    t("ödeme doğrulanınca firma açılıyor, e-posta, şifre, fatura PDF ve ödeme kaydı", g)

    def h():
        r, tok = R1["r"], R1["tok"]
        POSTA.clear()
        donus(tok); donus(tok)
        L = loop.run_until_complete(s.db.main().firms.find({"login_email": FORM["email"]}).to_list(5))
        assert len(L) == 1 and not POSTA, "aynı ödeme iki kez bildirilince ikinci firma/e-posta/fatura olmamalı"
        fa = loop.run_until_complete(s.db.main().satis_fatura.find({"siparis_no": r["no"]}).to_list(5))
        assert len(fa) == 1
    t("aynı ödeme iki kez bildirilirse tek kez işleniyor", h)

    def i():
        r = yolla(email="hileli@x.com", firma="Hileli").json()
        c.post("/api/public/satin-al/odeme", json={"no": r["no"], "k": r["k"], "yontem": "kart"})
        tok = "tok%d" % len(IYZ["init"])
        IYZ["detay"] = {"status": "success", "paymentStatus": "SUCCESS", "paidPrice": "10.00", "basketId": r["no"], "paymentId": "1"}
        donus(tok)
        st = c.get("/api/public/satin-al/durum", params={"no": r["no"], "k": r["k"]}).json()
        assert st["durum"] == "basarisiz", st
        assert not loop.run_until_complete(s.db.main().firms.find_one({"login_email": "hileli@x.com"}))
        IYZ["detay"] = {"status": "failure", "errorMessage": "Kart reddedildi", "paymentStatus": "FAILURE"}
        donus(tok)
        assert "Kart reddedildi" in c.get("/api/public/satin-al/durum", params={"no": r["no"], "k": r["k"]}).json()["hata"]
        IYZ["detay"] = {"status": "success", "paymentStatus": "SUCCESS", "paidPrice": "23880.00", "basketId": r["no"], "paymentId": "2"}
        c.post("/api/public/satin-al/odeme", json={"no": r["no"], "k": r["k"], "yontem": "kart"})
        donus("tok%d" % len(IYZ["init"]))
        assert c.get("/api/public/satin-al/durum", params={"no": r["no"], "k": r["k"]}).json()["durum"] == "tamamlandi", "başarısız sonrası tekrar deneme çalışmalı"
    t("tutar uyuşmazlığı ve reddedilen kart firma açmıyor; tekrar deneme çalışıyor", i)

    def j():
        f0 = loop.run_until_complete(s.db.main().firms.find_one({"login_email": FORM["email"]}))
        r = yolla(sure="yillik").json(); assert r["tur"] == "yenileme"
        assert yolla(sure="aylik").status_code == 422
        c.post("/api/public/satin-al/odeme", json={"no": r["no"], "k": r["k"], "yontem": "kart"})
        IYZ["detay"] = {"status": "success", "paymentStatus": "SUCCESS", "paidPrice": "%.2f" % r["fiyat"]["toplam"], "basketId": r["no"], "paymentId": "3"}
        POSTA.clear(); donus("tok%d" % len(IYZ["init"]))
        L = loop.run_until_complete(s.db.main().firms.find({"login_email": FORM["email"]}).to_list(5))
        assert len(L) == 1 and L[0]["expires_at"] > f0["expires_at"], (f0["expires_at"], L[0]["expires_at"])
        d = (__import__("datetime").datetime.fromisoformat(L[0]["expires_at"]) - __import__("datetime").datetime.fromisoformat(f0["expires_at"])).days
        assert 364 <= d <= 366, d
        assert "Şifre:" not in POSTA[0][1] and "mevcut şifrenizle" in POSTA[0][1].lower()
    t("aynı e-postayla alım yeni firma açmıyor, süreyi uzatıyor", j)

    def k():
        r = yolla(email="havale@x.com", firma="Havale Ltd").json()
        x = c.post("/api/public/satin-al/odeme", json={"no": r["no"], "k": r["k"], "yontem": "havale"}).json()
        assert x["havale"]["iban"].startswith("TR33") and x["aciklama"] == r["no"]
        assert c.get("/api/public/satin-al/durum", params={"no": r["no"], "k": r["k"]}).json()["durum"] == "havale_bekliyor"
        assert c.post("/api/admin/satis/siparisler/%s/havale-onayla" % r["no"]).status_code in (401, 403)
        z = c.post("/api/admin/satis/siparisler/%s/havale-onayla" % r["no"], headers=A, json={"referans": "EFT123"}).json()
        assert z["ok"], z
        assert loop.run_until_complete(s.db.main().firms.find_one({"login_email": "havale@x.com"}))
        assert c.post("/api/admin/satis/siparisler/%s/havale-onayla" % r["no"], headers=A).status_code == 409
        l = c.get("/api/admin/satis/siparisler", headers=A).json()
        assert l["sayilar"]["tamamlandi"] >= 4 and l["ciro"] > 0 and "erisim" not in str(l["items"])
    t("havale: bekliyor, sahip onaylayınca firma açılıyor, çift onay engelli", k)

    def m():
        r = yolla(email="hata@x.com", firma="Hata Ltd").json()
        c.post("/api/public/satin-al/odeme", json={"no": r["no"], "k": r["k"], "yontem": "kart"})
        IYZ["detay"] = {"status": "success", "paymentStatus": "SUCCESS", "paidPrice": "23880.00", "basketId": r["no"], "paymentId": "7"}
        eski = firms.API["create"]
        async def patlat(*a, **k): raise RuntimeError("veritabanı hatası")
        firms.API["create"] = patlat
        donus("tok%d" % len(IYZ["init"]))
        firms.API["create"] = eski
        st = c.get("/api/public/satin-al/durum", params={"no": r["no"], "k": r["k"]}).json()
        assert st["durum"] == "isleme_hatasi", st
        z = c.post("/api/admin/satis/siparisler/%s/yeniden-isle" % r["no"], headers=A).json()
        assert z["ok"] and loop.run_until_complete(s.db.main().firms.find_one({"login_email": "hata@x.com"}))
    t("ödeme alınıp kurulum patlarsa sipariş kaybolmuyor, sahip yeniden işliyor", m)

    def n():
        o = loop.run_until_complete(s.db.main().satis_siparis.find_one({"musteri.email": FORM["email"], "tur": "yeni", "durum": "tamamlandi"}))
        no = o["no"]
        pw = c.post("/api/admin/satis/siparisler/%s/bilgi-gonder" % no, headers=A, json={"yeni_sifre": True}).json()
        assert pw.get("ok"), pw
        sifre = re.search(r"Şifre: (\S+)", POSTA[-1][1]).group(1)
        assert c.post("/api/auth/login", json={"email": FORM["email"], "password": sifre}).status_code == 200
        c.cookies.clear()
        assert c.post("/api/admin/satis/siparisler/%s/earsiv" % no, headers=A, json={"no": "GIB2026000042"}).json()["ok"]
        pdf = c.get("/api/admin/satis/fatura/%s.pdf" % no, headers=A); assert pdf.content[:4] == b"%PDF"
    t("giriş bilgisini yeniden gönderme (yeni şifre) ve resmî e-Arşiv no işleme", n)

    def iki():
        import site_kampanya
        from datetime import datetime
        col = s.db.main().site_campaigns
        loop.run_until_complete(col.delete_many({}))
        loop.run_until_complete(col.insert_one({"id": "surekli", "name": "s", "strip": "x", "active": True, "always": True}))
        # kampanya yokken (her zaman) hediye yok: 2 yıl = 730 gün, fiyat 2 x yıllık
        r = oku(); pr = {x["id"]: x for x in r["paketler"]}["profesyonel"]
        assert r["hediye"] is None and pr["iki_yil"]["gun"] == 730 and pr["iki_yil"]["matrah"] == pr["yillik"]["matrah"] * 2, pr["iki_yil"]
        # yayında tarihli kampanya: +365 gün
        now = datetime.now(site_kampanya.TR)
        loop.run_until_complete(col.insert_one({"id": "t1", "name": "Deneme", "start": now.replace(year=now.year - 1).isoformat(), "end": now.replace(year=now.year + 1).isoformat(),
                                                "strip": "x", "active": True, "yearly": False, "always": False, "gift": True}))
        r = oku(); pr = {x["id"]: x for x in r["paketler"]}["profesyonel"]
        assert r["hediye"]["gun"] == 365 and pr["iki_yil"]["gun"] == 1095 and pr["iki_yil"]["hediye_gun"] == 365, (r["hediye"], pr["iki_yil"])
        # sipariş fiyatı sunucuda; istemci hediye gönderemez
        o = yolla(email="iki@x.com", firma="Iki Ltd", sure="iki_yil", hediye_gun=9999).json()
        assert o["fiyat"]["gun"] == 1095 and o["fiyat"]["sure"] == "iki_yil", o["fiyat"]
        # hediye kapalıyken verilmez
        loop.run_until_complete(col.update_one({"id": "t1"}, {"$set": {"gift": False}}))
        assert oku()["hediye"] is None
        loop.run_until_complete(col.delete_many({}))
    t("2 yıllık alım: kampanyada +1 yıl hediye, kapalıyken yok, fiyat sunucuda", iki)

print("OK", len(ok)); [print("FAIL", n, "\n", tb) for n, tb in bad]
sys.exit(1 if bad else 0)
