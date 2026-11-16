"""Excel/CSV toplu ürün yükleme: şablon, eşleme, önizleme (yazmaz), ekle/güncelle, varyant gruplama, hatalar, sınırlar."""
import sys, os, base64, io
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-900:]))
def b64(txt): return base64.b64encode(txt.encode("utf-8")).decode()
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ali", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    def up(txt, name="u.csv"): return c.post("/api/yp/products/import/parse", headers=H, json={"name": name, "data": b64(txt)})
    def prev(job, **k):
        d = {"job": job, "mapping": k.pop("mapping"), "mode": k.pop("mode", "ikisi"), "key": k.pop("key", "sku")}
        return c.post("/api/yp/products/import/preview", headers=H, json=d)
    CSV = ("Ürün adı;Stok kodu;Satış fiyatı;Stok;Ana stok kodu;Renk;Beden\n"
           "Keten Gömlek;KG-01;900,50;10;;;\n"
           "Tişört;TS-B-M;300;5;TS;Beyaz;M\n"
           ";TS-B-L;300;3;TS;Beyaz;L\n"
           "Hatalı;HT-1;abc;1;;;\n")
    S = {}
    def a():
        r = c.get("/api/yp/products/import/template", headers=H).json()
        assert r["ok"] and "Ana stok kodu" in r["csv"]
        p = up(CSV).json(); S.update(p)
        assert p["count"] == 4 and p["mapping"]["name"] == "Ürün adı" and p["mapping"]["o1v"] == "Renk" and p["mapping"]["group"] == "Ana stok kodu", p["mapping"]
    t("şablon + otomatik sütun eşleme", a)
    def b():
        r = prev(S["job"], mapping=S["mapping"]).json()
        assert r["ekle"] == 2 and r["guncelle"] == 0 and r["hata"] == 1, r
        assert r["errors"][0]["satir"] == 5 and "sayı" in r["errors"][0]["hata"]
        n = c.get("/api/yp/products", headers=H).json()
        assert not [x for x in (n["rows"]) if x.get("sku") in ("KG-01", "TS")], "önizleme yazmamalı"
    t("önizleme hiçbir şey yazmaz, hatalı satırı bildirir", b)
    def d():
        r = c.post("/api/yp/products/import/run", headers=H, json={"job": S["job"]}).json()
        assert r["ok"] and r["ekle"] == 2 and r["hata"] == 1, r
        L = c.get("/api/yp/products", headers=H).json(); L = L["rows"]
        by = {x["sku"]: x for x in L}
        assert by["KG-01"]["price"] == 900.5 and by["KG-01"]["stock"] == 10
        assert by["TS"]["variant_count"] == 2, by["TS"]
        assert c.post("/api/yp/products/import/run", headers=H, json={"job": S["job"]}).status_code == 409
        e = c.get("/api/yp/products/import/%s/errors" % S["job"], headers=H).json()
        assert e["n"] == 1 and "Satır" in e["csv"]
    t("içe aktarma: ürün + varyant grubu, ikinci çalıştırma engellenir, hata CSV", d)
    def e():
        p = up("Ürün adı;Stok kodu;Satış fiyatı;Stok\nYeni ad;KG-01;;\nYok;ZZ-9;50;2\n").json()
        mp = p["mapping"]
        r = prev(p["job"], mapping=mp).json()
        assert r["guncelle"] == 1 and r["ekle"] == 1 and r["hata"] == 0, r
        c.post("/api/yp/products/import/run", headers=H, json={"job": p["job"]})
        L = c.get("/api/yp/products", headers=H).json(); L = L["rows"]
        by = {x["sku"]: x for x in L}
        assert by["KG-01"]["name"] == "Yeni ad" and by["KG-01"]["price"] == 900.5 and by["KG-01"]["stock"] == 10, "boş hücre veriyi silmemeli"
    t("güncelleme: boş hücre mevcut değeri silmez", e)
    def f():
        p = up("Ürün adı;Stok kodu;Satış fiyatı\nA;KG-01;10\n").json()
        r = prev(p["job"], mapping=p["mapping"], mode="ekle").json()
        assert r["ekle"] == 0 and r["hata"] == 1, r
        r = prev(p["job"], mapping=p["mapping"], mode="guncelle").json()
        assert r["guncelle"] == 1, r
        p = up("Ürün adı;Satış fiyatı\nA;10\n").json()
        assert prev(p["job"], mapping=p["mapping"], mode="guncelle").status_code == 422
    t("ekle/güncelle modları ve anahtar sütun zorunluluğu", f)
    def g():
        assert up("Ürün adı\n").status_code == 422
        assert c.post("/api/yp/products/import/parse", headers=H, json={"name": "x.csv", "data": b64("a;b\n" + "x;1\n" * 5001)}).status_code == 422
        p = up("Ürün adı;Barkod;Satış fiyatı\nA;8,69E+12;5\n").json()
        r = prev(p["job"], mapping=p["mapping"], mode="ekle", key="barcode").json()
        assert r["hata"] == 1 and "bilimsel" in r["errors"][0]["hata"], r
        assert TestClient(s.app).get("/api/yp/products/import/template").status_code in (401, 403)
    t("sınırlar: boş dosya, 5000 satır, bilimsel barkod, yetkisiz", g)
    def h():
        from openpyxl import Workbook
        wb = Workbook(); ws = wb.active
        ws.append(["Ürün adı", "Stok kodu", "Satış fiyatı", "Stok"]); ws.append(["Excel Ürün", "XL-1", 120.5, 4])
        buf = io.BytesIO(); wb.save(buf)
        p = c.post("/api/yp/products/import/parse", headers=H, json={"name": "u.xlsx", "data": base64.b64encode(buf.getvalue()).decode()}).json()
        r = prev(p["job"], mapping=p["mapping"], mode="ekle").json()
        assert r["ekle"] == 1, r
    t("xlsx okunur", h)
print("OK", len(ok), "FAIL", len(bad))
for n in ok: print("  ✓", n)
for n, tb in bad: print("  ✗", n, "\n", tb)
