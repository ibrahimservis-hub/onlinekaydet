"""Çek-senet, ekstre, kur, müşavir bağlantısı, depo/lot/SKT, sayım, toplu fiyat, hızlı satış, ihracat, açık API, geri bildirim."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import muhasebe_ek as me
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-900:]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
TCMB = b'<?xml version="1.0"?><Tarih_Date Tarih="17.11.2026"><Currency Kod="USD" CurrencyCode="USD"><Unit>1</Unit><ForexBuying>40.5</ForexBuying><ForexSelling>40.6</ForexSelling></Currency><Currency Kod="JPY"><Unit>100</Unit><ForexBuying>27</ForexBuying><ForexSelling>27.2</ForexSelling></Currency></Tarih_Date>'
import xml_ice
xml_ice.fetch_bytes = lambda url, timeout=40: TCMB
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Ek Firma", "email": "ek@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    O = tok(c, "ek@x.com", "sifre12345")
    FID = r.json().get("id") or r.json().get("firm", {}).get("id")
    acc = c.get("/api/finance/accounts", headers=O).json()
    acc = acc if isinstance(acc, list) else acc.get("accounts") or acc.get("rows")
    AID = acc[0]["id"]
    S = {}
    kl = c.get("/api/yp/api-anahtar", headers=O).json(); PV, GB = kl["taban"], kl["form"]
    def cek():
        r = c.post("/api/yp/cek-senet", headers=O, json={"type": "cek", "direction": "alacak", "party": "ABC Ltd", "amount": "1.500,50", "due": "2026-11-20", "no": "C1"}); assert r.status_code == 200, r.text
        S["cs"] = r.json()["id"]; assert r.json()["status"] == "portfoy"
        assert c.post("/api/yp/cek-senet", headers=O, json={"type": "senet", "direction": "alacak", "party": "X", "amount": 0, "due": "2026-11-20"}).status_code == 422
        assert c.post("/api/yp/cek-senet", headers=O, json={"party": "X", "amount": 5}).status_code == 422
        l = c.get("/api/yp/cek-senet", headers=O).json(); assert l["ozet"]["portfoy_alacak"] == 1500.5
        assert c.post("/api/yp/cek-senet/%s/durum" % S["cs"], headers=O, json={"status": "tahsil"}).status_code == 422
        assert c.post("/api/yp/cek-senet/%s/durum" % S["cs"], headers=O, json={"status": "tahsil", "account_id": AID}).status_code == 200
        assert c.post("/api/yp/cek-senet/%s/durum" % S["cs"], headers=O, json={"status": "iade"}).status_code == 409
        assert c.delete("/api/yp/cek-senet/%s" % S["cs"], headers=O).status_code == 409
        b = [a for a in c.get("/api/finance/accounts", headers=O).json() if a["id"] == AID] if isinstance(c.get("/api/finance/accounts", headers=O).json(), list) else []
        r = c.post("/api/yp/cek-senet", headers=O, json={"type": "cek", "direction": "borc", "party": "T", "amount": 100, "due": "2026-12-01"}); assert r.json()["status"] == "bekliyor"
    t("cek-senet", cek)
    def ekstre():
        csvt = "Tarih;Açıklama;Tutar\n01.11.2026;EFT Gelen;1.000,00\n02.11.2026;Kira;-500,00\n"
        r = c.post("/api/yp/banka/ekstre", headers=O, json={"account_id": AID, "csv": csvt}); assert r.status_code == 200 and r.json()["eklenen"] == 2, r.text
        r = c.post("/api/yp/banka/ekstre", headers=O, json={"account_id": AID, "csv": csvt}); assert r.json()["eklenen"] == 0 and r.json()["tekrar_atlanan"] == 2
        assert c.post("/api/yp/banka/ekstre", headers=O, json={"account_id": AID, "csv": "a;b\n1;2"}).status_code == 422
        r = c.post("/api/yp/banka/ekstre", headers=O, json={"account_id": AID, "csv": "Tarih,Borç,Alacak\n2026-11-03,200,\n2026-11-04,,300\n"}); assert r.json()["eklenen"] == 2
    t("banka ekstresi", ekstre)
    def kur():
        r = c.get("/api/yp/kur?yenile=true", headers=O); assert r.status_code == 200, r.text
        k = r.json()["kurlar"]; assert k["USD"]["satis"] == 40.6 and k["JPY"]["satis"] == 0.272, k
        assert c.get("/api/yp/kur/cevir?tutar=10&para=USD", headers=O).json()["tl"] == 406.0
    t("kur", kur)
    def mus():
        r = c.post("/api/yp/musavir", headers=O, json={"ad": "Ali Bey", "gun": 7}); assert r.status_code == 200, r.text
        yol = r.json()["yol"]
        o = c.get(yol + "/ozet?ay=2026-11"); assert o.status_code == 200 and o.json()["gelir"] >= 1500.5, o.text
        assert "Tarih;Tür" in c.get(yol + "/csv?ay=2026-11").text
        assert "Mali müşavir" in c.get(yol + "?ay=2026-11").text
        assert c.get("/api/public/musavir/yanlis/ozet").status_code == 404
        mid = c.get("/api/yp/musavir", headers=O).json()["rows"][0]["id"]
        assert "token_hash" not in c.get("/api/yp/musavir", headers=O).json()["rows"][0]
        c.delete("/api/yp/musavir/" + mid, headers=O); assert c.get(yol + "/ozet").status_code == 404
    t("mali müşavir", mus)
    def urun():
        r = c.post("/api/yp/products", headers=O, json={"name": "Süt 1L", "price": 30, "stock": 10, "barcode": "869111", "sku": "SUT1", "cat": "Gıda", "brand": "X"})
        assert r.status_code in (200, 201), r.text; S["p"] = r.json().get("id") or r.json().get("product", {}).get("id")
        assert S["p"]
    t("ürün oluştur", urun)
    def depo_lot():
        d = c.post("/api/yp/depo", headers=O, json={"name": "Ana depo"}).json(); d2 = c.post("/api/yp/depo", headers=O, json={"name": "Şube"}).json()
        assert c.post("/api/yp/depo", headers=O, json={"name": "Ana depo"}).status_code == 409
        r = c.post("/api/yp/stok/lot", headers=O, json={"barcode": "869111", "qty": 5, "skt": "2026-11-25", "depo_id": d["id"], "lot": "L1"}); assert r.status_code == 200, r.text
        S["lot"] = r.json()["id"]
        assert c.post("/api/yp/stok/lot", headers=O, json={"barcode": "869111", "qty": 1, "skt": "25.11.2026"}).status_code == 422
        sk = c.get("/api/yp/stok/skt?gun=30", headers=O).json(); assert any(x["lot"] == "L1" for x in sk["rows"])
        assert c.post("/api/yp/stok/transfer", headers=O, json={"lot_id": S["lot"], "to_depo": d2["id"], "qty": 9}).status_code == 422
        assert c.post("/api/yp/stok/transfer", headers=O, json={"lot_id": S["lot"], "to_depo": d2["id"], "qty": 2}).status_code == 200
        assert c.delete("/api/yp/depo/" + d["id"], headers=O).status_code == 409
        assert c.get("/api/yp/hizli/bul?kod=869111", headers=O).json()["urun"]["stock"] == 15
        assert c.post("/api/yp/stok/lot/%s/dusur" % S["lot"], headers=O, json={"qty": 1}).json()["dusen"] == 1
    t("depo/lot/skt/transfer", depo_lot)
    def sayim():
        r = c.post("/api/yp/stok/sayim", headers=O, json={"items": [{"barcode": "869111", "sayilan": 10}, {"barcode": "yok", "sayilan": 1}]}).json()
        assert r["farklar"][0]["fark"] == -4 and not r["uygulandi"] and r["eksik_toplam"] == 4, r
        r = c.post("/api/yp/stok/sayim", headers=O, json={"uygula": True, "items": [{"barcode": "869111", "sayilan": 10}]}).json(); assert r["duzeltilen"] == 1
        assert c.get("/api/yp/hizli/bul?kod=SUT1", headers=O).json()["urun"]["stock"] == 10
    t("sayım", sayim)
    def toplu():
        r = c.post("/api/yp/stok/toplu-fiyat", headers=O, json={"mod": "yuzde", "deger": 10, "category": "Gıda"}).json(); assert r["onizleme"] and r["ornek"][0]["yeni"] == 33.0, r
        assert c.get("/api/yp/hizli/bul?kod=SUT1", headers=O).json()["urun"]["fiyat"] == 30
        r = c.post("/api/yp/stok/toplu-fiyat", headers=O, json={"mod": "yuzde", "deger": 10, "category": "Gıda", "onizle": False, "yuvarla": "99"}).json(); assert r["adet"] == 1
        assert c.get("/api/yp/hizli/bul?kod=SUT1", headers=O).json()["urun"]["fiyat"] == 32.99
        assert c.post("/api/yp/stok/toplu-fiyat/%s/geri-al" % r["geri_al_kodu"], headers=O).status_code == 200
        assert c.get("/api/yp/hizli/bul?kod=SUT1", headers=O).json()["urun"]["fiyat"] == 30
        assert c.post("/api/yp/stok/toplu-fiyat", headers=O, json={"mod": "yuzde", "deger": 5000}).status_code == 422
    t("toplu fiyat + geri al", toplu)
    def hizli():
        r = c.post("/api/yp/hizli/sat", headers=O, json={"items": [{"barcode": "869111", "qty": 2}], "odeme": "nakit", "account_id": AID, "indirim": 5}); assert r.status_code == 200, r.text
        assert r.json()["toplam"] == 55.0
        assert c.get("/api/yp/hizli/bul?kod=SUT1", headers=O).json()["urun"]["stock"] == 8
        assert c.post("/api/yp/hizli/sat", headers=O, json={"items": [{"barcode": "869111", "qty": 99}], "odeme": "kart", "account_id": AID}).status_code == 409
        assert c.get("/api/yp/hizli/bul?kod=SUT1", headers=O).json()["urun"]["stock"] == 8
        assert c.get("/api/yp/hizli/gecmis", headers=O).json()["bugun_toplam"] == 55.0
        assert c.get("/api/yp/hizli/bul?kod=Süt", headers=O).json()["oneriler"]
    t("hızlı satış", hizli)
    def ihr():
        assert c.put("/api/yp/ihracat", headers=O, json={"aktif": True, "para": "USD", "firma": {"unvan": "Ek AŞ"}, "ulkeler": ["Almanya"]}).status_code == 200
        c.put("/api/yp/ihracat/urun/" + S["p"], headers=O, json={"gtip": "0401.20", "agirlik_kg": 1.1})
        r = c.post("/api/yp/ihracat/proforma", headers=O, json={"items": [{"barcode": "869111", "qty": 10}], "alici": "<b>Hans</b>", "ulke": "Almanya"}); assert r.status_code == 200, r.text
        assert "0401.20" in r.text and "&lt;b&gt;" in r.text and "PROFORMA" in r.text
    t("e-ihracat proforma", ihr)
    def api():
        k = c.post("/api/yp/api-anahtar", headers=O, json={"ad": "Test"}).json(); R = {"X-API-Key": k["anahtar"]}
        assert c.get(PV + "/urunler").status_code == 401
        r = c.get(PV + "/urunler?q=süt", headers=R); assert r.status_code == 200 and r.json()["toplam"] == 1, r.text
        assert c.get(PV + "/urunler/SUT1", headers=R).json()["stok"] == 8
        assert c.put(PV + "/urunler/SUT1", headers=R, json={"stok": 3}).status_code == 403
        w = c.post("/api/yp/api-anahtar", headers=O, json={"ad": "Yaz", "yazma": True}).json(); W = {"X-API-Key": w["anahtar"]}
        assert c.put(PV + "/urunler/SUT1", headers=W, json={"stok": 3, "fiyat": 31}).json()["stok"] == 3
        assert c.put(PV + "/urunler/SUT1", headers=W, json={"stok": -1}).status_code == 422
        assert "hash" not in str(c.get("/api/yp/api-anahtar", headers=O).json())
        c.delete("/api/yp/api-anahtar/" + k["id"], headers=O); assert c.get(PV + "/urunler", headers=R).status_code == 401
    t("açık API", api)
    def gb():
        assert c.post(GB, json={"tur": "sikayet", "mesaj": "kısa"}).status_code == 422
        r = c.post(GB, json={"tur": "sikayet", "ad": "A", "mesaj": "Servis geç geldi, bilgi verilmedi."}); assert r.status_code == 200 and r.json()["takip_no"]
        assert c.post(GB, json={"website": "bot", "mesaj": "x" * 20}).json()["ok"]
        l = c.get("/api/yp/geri-bildirim", headers=O).json(); assert l["yeni"] == 1
        assert c.post("/api/yp/geri-bildirim/" + l["rows"][0]["id"], headers=O, json={"durum": "cozuldu", "cevap": "Özür dileriz"}).status_code == 200
        for _ in range(6): last = c.post(GB, json={"mesaj": "yeterince uzun mesaj"}).status_code
        assert last == 429
    t("geri bildirim", gb)
    def yetki():
        c.cookies.clear()
        for u in ("/api/yp/cek-senet", "/api/yp/kur", "/api/yp/depo", "/api/yp/musavir", "/api/yp/api-anahtar", "/api/yp/geri-bildirim", "/api/yp/hizli/gecmis"):
            assert c.get(u).status_code in (401, 403), u
    t("yetkisiz erişim", yetki)
print("OK", len(ok), ok if not bad else "")
for n, e in bad: print("HATA", n, e)
sys.exit(1 if bad else 0)
