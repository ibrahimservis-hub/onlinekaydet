"""Firma sözleşmesi PDF: bilgiler otomatik gelir, boş alanlar çizgi, özel bedel, yetki."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:500]))
def metin(b):
    open("/tmp/_sz.pdf", "wb").write(b)
    return subprocess.run(["pdftotext", "-layout", "/tmp/_sz.pdf", "-"], capture_output=True, text=True).stdout
with TestClient(s.app) as c:
    r = c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}); A = {"Authorization": "Bearer " + r.json()["token"]}
    r = c.post("/api/admin/firms", json={"name": "Deneme Firma", "email": "sz@ornek.com", "password": "Sifre123!", "contact_name": "Ayşe Yılmaz", "phone": "05321112233",
                                          "address": "Çankaya Ankara", "tax_no": "1234567890", "tax_office": "Kavaklıdere", "package": "profesyonel"}, headers=A)
    assert r.status_code in (200, 201), r.text; S["id"] = r.json()["id"]
    def pdf():
        r = c.get("/api/admin/firms/%s/sozlesme.pdf" % S["id"], headers=A); assert r.status_code == 200 and r.content[:4] == b"%PDF", r.status_code
        assert "attachment" in r.headers["content-disposition"]
        m = metin(r.content); S["m"] = m
        for x in ("Deneme Firma", "Ayşe Yılmaz", "05321112233", "sz@ornek.com", "1234567890", "Kavaklıdere", "Profesyonel", "SÖZLEŞMESİ", "19.900", "İMZALAR"): assert x in m, x
    t("PDF üretilir ve firma bilgileri gelir", pdf)
    def bos(): assert "____" in S["m"]
    t("eksik satıcı bilgisi çizgi olarak kalır", bos)
    def bedel():
        r = c.get("/api/admin/firms/%s/sozlesme.pdf?paket=tam&sure=iki_yil&bedel=12000&kdv_dahil=1" % S["id"], headers=A); assert r.status_code == 200
        m = metin(r.content); assert "12.000" in m and "Tam Paket" in m and "2 yıllık" in m and "özel bedel" in m, m[:1500]
    t("özel bedel ve 2 yıllık", bedel)
    def sureler():
        for q, et, tut in (("m6", "6 aylık", "11.940"), ("m3", "3 aylık", "5.970"), ("m36", "3 yıllık", None), ("m18", "18 aylık", None), ("aylik", "1 aylık", None)):
            r = c.get("/api/admin/firms/%s/sozlesme.pdf?paket=baslangic&sure=%s" % (S["id"], q), headers=A); assert r.status_code == 200, q
            m = metin(r.content); assert et in m, (q, et)
            if q == "m6": assert "5.940" in m or "5940" in m, m[m.index("BEDEL"):m.index("BEDEL")+200]
    t("3/6/18/36 aylık süreler", sureler)
    def font():
        import satin_al, os as _os
        orig = _os.path.exists; satin_al._FONT = None
        _os.path.exists = lambda p: False if "DejaVu" in str(p) else orig(p)
        try:
            r = c.get("/api/admin/firms/%s/sozlesme.pdf" % S["id"], headers=A)
        finally:
            _os.path.exists = orig; satin_al._FONT = None
        m = metin(r.content); assert "SÖZLEŞMESİ" in m and "Ayşe Yılmaz" in m and "SAĞLAYICI" in m, m[:300]
        assert "DejaVuSans" in subprocess.run(["pdffonts", "/tmp/_sz.pdf"], capture_output=True, text=True).stdout
    t("gömülü yazı tipi (sistem fontu yokken Türkçe)", font)
    def yetki():
        assert TestClient(s.app).get("/api/admin/firms/%s/sozlesme.pdf" % S["id"]).status_code in (401, 403)
        assert c.get("/api/admin/firms/yok/sozlesme.pdf", headers=A).status_code == 404
        assert c.get("/api/admin/firms/%s/sozlesme.pdf?bedel=abc" % S["id"], headers=A).status_code == 422
    t("yetki ve hatalar", yetki)
print("OK %d geçti" % len(ok) if not bad else "FAIL", *bad, sep="\n")
