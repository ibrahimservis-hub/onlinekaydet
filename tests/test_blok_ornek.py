"""Bölüm örnek içeriği: katalogda gerçek fotoğraf, eklenen bölüm örnek metin/fotoğrafla dolu, önizleme çizimi."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import blocks, blok_ornek
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-700:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    def a():
        for p in blocks.SECTOR_PACKS:
            assert blok_ornek.foto("hero", p).startswith("https://images.pexels.com/photos/"), p
    t("her paket için gerçek Pexels fotoğrafı döner", a)
    def b():
        r = c.get("/api/yp/blocks", headers=H).json()["rows"]
        assert r and all(x["photo"].startswith("https://images.pexels.com/") for x in r)
    t("katalog satırlarında fotoğraf var", b)
    def d():
        r = c.get("/api/yp/blocks/hero/onizleme", headers=H).json()
        assert "pexels" in r["html"] and len(r["html"]) > 500 and r["desc"]
    t("önizleme örnek fotoğraf ve metinle çiziliyor", d)
    def e():
        pg = c.get("/api/yp/pages", headers=H).json()
        pid = (pg["rows"] if isinstance(pg, dict) else pg)[0]["id"]
        r = c.post("/api/yp/pages/%s/blocks" % pid, headers=H, json={"bid": "hero"}).json()
        assert r["set"].get("title") and "pexels" in r["set"].get("img", "")
    t("eklenen bölüm örnek içerikle gelir", e)
print("ok", len(ok), "bad", len(bad))
for n, tb in bad: print("FAIL", n, tb)
sys.exit(1 if bad else 0)
