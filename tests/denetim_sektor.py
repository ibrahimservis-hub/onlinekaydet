"""Tüm sektörler: demo aç, giriş, panel verisi, site ana sayfası ve alt sayfalar, 3 temaya geçiş, alan adıyla yayın."""
import sys, os, json, re, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "panel"))
import sektor, sektor_dil, demo
demo.GUNLUK_LIMIT = 10 ** 6
TH = json.load(open(os.path.join(os.path.dirname(__file__), "..", "panel", "themes.json"), encoding="utf-8"))
KEYS = list(sektor.SECTORS)
if len(sys.argv) > 1: KEYS = sys.argv[1].split(",")
BAD = re.compile(r"\{\{|\}\}|undefined|\bNone\b|\[object|NaN|Traceback|%s|\$\{")
rep = []
def note(k, m): rep.append((k, m)); print("SORUN", k, m, flush=True)
with TestClient(boot.server.app) as c:
    OW = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    for i, k in enumerate(KEYS):
        demo._RATE.clear()
        r = c.post("/api/public/demo", json={"name": "Deneme Kisi", "phone": "0553%07d" % (3000 + i), "sector": k})
        if r.status_code != 200: note(k, "demo açılmadı %s %s" % (r.status_code, r.text[:80])); continue
        d = r.json(); lg = c.post("/api/auth/login", json={"email": d["email"], "password": d["password"]})
        if lg.status_code != 200: note(k, "giriş olmadı"); continue
        H = {"Authorization": "Bearer " + lg.json()["token"]}
        fam = sektor_dil.family(k)
        for ep in ("/api/yp/boot", "/api/sector-terms", "/api/jobs", "/api/technicians", "/api/customers", "/api/cash/summary", "/api/parts", "/api/quotes", "/api/appointments", "/api/yp/rapor", "/api/site/edit", "/api/settings", "/api/yp/customers"):
            x = c.get(ep, headers=H)
            if x.status_code >= 400 and not (ep in ("/api/parts", "/api/quotes") and False): note(k, "%s -> %s %s" % (ep, x.status_code, x.text[:70]))
        # panel: yeni kayıt
        if fam in ("", "yol", "proje"):
            tid = c.get("/api/technicians", headers=H).json()
            q = c.post("/api/jobs/quick", headers=H, json={"customer_name": "Denetim Müşteri", "customer_phone": "05321110000", "fault_description": "Denetim kaydı", "assigned_technician_id": tid[0]["id"] if tid else ""})
            if q.status_code != 200: note(k, "iş kaydı oluşmadı %s %s" % (q.status_code, q.text[:80]))
        # site
        e = c.get("/api/site/edit", headers=H).json(); home = e.get("html", "")
        if len(home) < 3000: note(k, "ana sayfa çok kısa %d" % len(home))
        m = BAD.search(re.sub(r"\{\{H\}\}|<script.*?</script>|<style.*?</style>", "", home, flags=re.S))
        if m: note(k, "ana sayfada şüpheli metin: %r" % home[max(0, home.find(m.group(0)) - 30):home.find(m.group(0)) + 30])
        for p in (e.get("pages") or [])[:12]:
            pr = c.get("/api/site/edit", headers=H, params={"page": p["slug"]})
            if pr.status_code != 200 or len(pr.json().get("html", "")) < 800: note(k, "alt sayfa %s -> %s" % (p["slug"], pr.status_code))
        # tema değişimi (aynı sektörün ilk 3 teması)
        ths = [t for t in TH if t.get("sector") in (k, k.replace("_", "-"))][:3] or TH[:2]
        for t in ths:
            pu = c.put("/api/brand", headers=H, json={"theme": t["slug"], "dark": t.get("dark"), "accent": t.get("accent"), "radius": t.get("radius", 12)})
            if pu.status_code == 403: continue
            if pu.status_code >= 400: note(k, "tema kaydedilmedi %s %s" % (t["slug"], pu.status_code)); continue
            h2 = c.get("/api/site/edit", headers=H).json().get("html", "")
            if len(h2) < 3000: note(k, "tema %s sonrası ana sayfa boş" % t["slug"])
        # alan adı ile yayın
        dom = "denetim%d-site.com" % i
        if c.post("/api/firm/domain", headers=H, json={"domain": dom}).status_code != 200: note(k, "alan adı eklenemedi"); continue
        c.put("/api/admin/domains/%s/status" % dom, headers=OW, json={"status": "yayinda"})
        for pth in ["/"] + ["/" + p["slug"] for p in (e.get("pages") or [])[:4]]:
            hs = c.get("/api/public/hosted-site", params={"p": pth}, headers={"Host": dom})
            if hs.status_code != 200 or "<html" not in hs.text.lower(): note(k, "yayında %s -> %s" % (pth, hs.status_code))
            else:
                mm = BAD.search(re.sub(r"<script.*?</script>|<style.*?</style>", "", hs.text, flags=re.S))
                if mm: note(k, "yayındaki %s sayfada şüpheli metin: %r" % (pth, hs.text[max(0, hs.text.find(mm.group(0)) - 30):hs.text.find(mm.group(0)) + 30]))
                if "{{H}}" in hs.text: note(k, "yayındaki %s sayfada {{H}} yer tutucusu kaldı" % pth)
        if k in ("kombi", "kuafor", "lokanta", "oto_cekici", "avukat", "eticaret"): print("ok", k, "sayfa", len(e.get("pages") or []), flush=True)
print("SEKTOR", len(KEYS), "SORUN", len(rep))
