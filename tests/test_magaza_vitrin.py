"""Yayındaki sitede gerçek mağaza (/magaza) ve müşteri paneli (/hesabim)."""
import sys, os, re, subprocess, tempfile
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:500]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    r = c.post("/api/admin/firms", headers=A, json={"name": "Vitrin Firma", "email": "vt@x.com", "password": "sifre12345", "package": "tam"}); assert r.status_code == 200, r.text
    F = r.json()["id"]; O = tok(c, "vt@x.com", "sifre12345")
    async def setup():
        f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
        await s.db.firm(f["db"]).app_settings.update_one({"_id": "brand"}, {"$set": {"theme": "p01-cine-kombi"}}, upsert=True)
        await s.db.main().firm_domains.insert_one({"id": "dv1", "domain": "vitrin-test.com", "firm_id": F, "db": f["db"], "status": "yayinda"})
    c.portal.call(setup)
    import domains; domains._cache["t"] = 0
    H = {"Host": "vitrin-test.com"}
    def get(p): return c.get("/api/public/hosted-site?p=" + p.replace("/", "%2F"), headers=H)
    def off():
        c.put("/api/site/features", headers=O, json={"shop_enabled": False, "customer_portal_enabled": False})
        assert 'id="okm-root"' not in get("/magaza").text, "mağaza kapalıyken mağaza sayfası yok"
        assert 'd.className="spx-ab"' not in get("/").text, "mağaza kapalıyken hesap simgesi yok"
    t("mağaza kapalıyken /magaza açılmaz", off)
    def on():
        r = c.put("/api/site/features", headers=O, json={"shop_enabled": True}); assert r.status_code == 200
        assert r.json()["customer_portal_enabled"] is True, "mağaza açılınca müşteri girişi de açılır"
        for p in ("/magaza", "/hesabim"):
            r = get(p); assert r.status_code == 200 and 'id="okm-root"' in r.text, (p, r.status_code)
            assert "ServisPlus" not in r.text and "servisplus" not in r.text.lower(), "platform adı görünmemeli"
            assert "Vitrin Firma" in r.text, "firma adı temadan gelir"
        h = get("/"); assert 'href="/magaza"' in h.text and 'href="/hesabim"' in h.text, "footer/yüzen bağlantılar"
        assert 'd.className="spx-ab"' in h.text, "üst çubukta Hesabım/Sepet simgeleri"
        assert 'class="spx-credit"' in h.text and 'href="https://onlinekaydet.com"' in h.text, "OnlineKaydet kredisi sabit"
    t("mağaza açılınca /magaza ve /hesabim temalı sayfa olarak gelir, bağlantılar eklenir", on)
    def js():
        for p in ("/magaza", "/hesabim"):
            src = re.findall(r"<script>(.*?)</script>", get(p).text, re.S)
            body = "\n".join(x for x in src if "okm-root" in x)
            assert body, "okm betiği bulunamadı"
            f = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False); f.write(body); f.close()
            r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True); assert r.returncode == 0, r.stderr[:400]
    t("sayfa betikleri geçerli JavaScript", js)
print("OK", len(ok)); [print(" +", n) for n in ok]
for n, e in bad: print(" FAIL", n, e)
sys.exit(1 if bad else 0)
