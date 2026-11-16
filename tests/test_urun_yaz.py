"""Ürün metni önerisi: anahtarsız şablon, uzunluk sınırları, sahte yapay zekâ yanıtı, limit dolunca şablon."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import urun_yaz
s = boot.server; ok, bad = [], []
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-800:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ali", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    P = {"name": "Vaillant ecoTEC Pure 24 kW Kombi Sirkülasyon Pompası Orijinal Yedek Parça", "brand": "Vaillant", "cat": "Kombi Yedek Parça",
         "specs": [{"k": "Güç", "v": "24 kW"}, {"k": "Uyumlu model", "v": "ecoTEC Pure"}], "ship": {"gun": 2, "ucretsiz": True}}
    def a():
        d = urun_yaz.sablon(P)
        assert len(d["seo_title"]) <= 70 and len(d["seo_desc"]) <= 160 and len(d["short"]) <= 160, d
        assert "24 kW" in d["desc"] and "garanti" not in d["desc"].lower() and "2 iş gününde" in d["desc"]
    t("şablon: sınırlar, yalnız verilen bilgi", a)
    def b():
        r = c.post("/api/yp/products/ai-text", headers=H, json={"product": P}).json()
        assert r["ok"] and r["kaynak"] == "sablon" and r["oneri"]["seo_title"], r
        r = c.post("/api/yp/products/ai-text", headers=H, json={"product": P, "alanlar": ["short"]}).json()
        assert list(r["oneri"]) == ["short"]
        assert c.post("/api/yp/products/ai-text", headers=H, json={"product": {"name": ""}}).status_code == 422
    t("anahtar yokken şablon döner, ad zorunlu", b)
    def d():
        h = s.api_router.ai_helpers
        async def guard(u): return {}
        async def chat(cf, m, **k):
            assert "uydurma" in m[0]["content"]
            return '{"short":"Sessiz pompa","seo_title":"%s","desc":"Paragraf bir.\\n\\n<b>Paragraf</b> iki."}' % ("A" * 200)
        old = dict(h); h["guard"], h["chat"] = guard, chat
        try:
            r = c.post("/api/yp/products/ai-text", headers=H, json={"product": P}).json()
        finally:
            h.update(old)
        assert r["kaynak"] == "ai" and r["oneri"]["short"] == "Sessiz pompa"
        assert len(r["oneri"]["seo_title"]) <= 70 and "<b>" not in r["oneri"]["desc"], r["oneri"]
        assert r["oneri"]["seo_desc"], "AI'nın vermediği alan şablondan dolar"
    t("yapay zekâ yanıtı: temizlenir, sınırlanır, eksik alan şablondan", d)
    def e():
        from fastapi import HTTPException
        h = s.api_router.ai_helpers
        async def guard(u): raise HTTPException(429, "Günlük yapay zekâ limiti doldu")
        old = dict(h); h["guard"] = guard
        try:
            r = c.post("/api/yp/products/ai-text", headers=H, json={"product": P}).json()
        finally:
            h.update(old)
        assert r["kaynak"] == "sablon" and "limit" in r["uyari"]
    t("limit dolunca hata yerine şablon", e)
for n in ok: print("  ✓", n)
for n, x in bad: print("  ✗", n, "\n", x)
print("OK %d FAIL %d" % (len(ok), len(bad)))
