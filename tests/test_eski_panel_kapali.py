"""Eski personel paneli kimseye görünmez (yeni panele gider); müşteri sayfaları (teklif, ödeme, portal...) çalışır."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
ok = bad = 0
with TestClient(boot.server.app, follow_redirects=False) as c:
    for p in ("/admin", "/admin/jobs", "/panel", "/login", "/giris", "/tech", "/tech/jobs", "/jobs", "/customers", "/settings", "/dashboard"):
        r = c.get(p); good = r.status_code == 302 and r.headers["location"] == "/salon"; ok += good; bad += not good; print("  +" if good else "  -", p, r.status_code)
    for p in ("/teklif/abc", "/odeme/abc", "/portal", "/uye-girisi", "/bakim/abc"):
        r = c.get(p); good = r.status_code == 200; ok += good; bad += not good; print("  +" if good else "  -", p, r.status_code)
    r = c.get("/salon"); good = r.status_code == 200; ok += good; bad += not good; print("  +" if good else "  -", "/salon", r.status_code)
    r = c.get("/yonetim"); good = r.status_code == 200; ok += good; bad += not good; print("  +" if good else "  -", "/yonetim", r.status_code)
print("OK", ok, "FAIL", bad)
