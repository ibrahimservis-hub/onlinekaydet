"""ServisPlus panel - otomatik duman testi (GitHub Actions).
Gercek veritabani/.env KULLANMAZ: bellek ici sahte Mongo (mongomock) ile sunucuyu acar,
1) parametresiz tum GET uclarinda 500 olmadigini, 2) temel is akisini dener. Hata varsa cikis kodu 1."""
import os, sys, threading, time, random, socket
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.update(MONGO_URL="mongodb://ci", DB_NAME="ci_test", JWT_SECRET="c" * 40, UPLOAD_DIR="/tmp/ci_up", CORS_ORIGINS="*",
                  STORAGE_MODE="local", ADMIN_EMAIL="admin@test.com", ADMIN_PASSWORD="Test12345!")
import motor.motor_asyncio as mm
from mongomock_motor import AsyncMongoMockClient
mm.AsyncIOMotorClient = AsyncMongoMockClient
sys.path.insert(0, os.path.join(ROOT, "panel"))
import server, uvicorn, requests

s = socket.socket(); s.bind(("127.0.0.1", 0)); PORT = s.getsockname()[1]; s.close()
B = f"http://127.0.0.1:{PORT}/api"
threading.Thread(target=lambda: uvicorn.run(server.app, host="127.0.0.1", port=PORT, log_level="warning"), daemon=True).start()
for _ in range(120):
    try:
        if requests.get(B + "/health", timeout=2).ok:
            break
    except Exception:
        pass
    time.sleep(1)
else:
    print("SUNUCU ACILMADI"); sys.exit(1)
tok = None
for _ in range(60):                      # admin tohumu acilista arka planda olusur
    r = requests.post(B + "/auth/login", json={"email": "admin@test.com", "password": "Test12345!"})
    if r.ok:
        tok = r.json()["token"]; break
    time.sleep(1)
if not tok:
    print("ADMIN GIRISI OLMADI"); sys.exit(1)
H = {"Authorization": "Bearer " + tok}
# Gece 22:00-07:00 ustaya is gizleme kurali testi saate bagimli yapiyordu: test boyunca kapat (kural kodu degismez)
requests.put(B + "/settings", json={"tech_visibility": {"enabled": False}}, headers=H)
FAIL = []

# 1) GET taramasi
SKIP = ("/api/speed", "/api/admin/gsc", "/api/public/shop", "/api/public/feeds", "/api/backup", "/api/export")
spec = requests.get(f"http://127.0.0.1:{PORT}/openapi.json").json()
n = 0
for p, ops in spec["paths"].items():
    if "get" not in ops or "{" in p or p.startswith(SKIP) or "stream" in p:
        continue
    try:
        r = requests.get(f"http://127.0.0.1:{PORT}" + p, headers=H, timeout=60); n += 1
        if r.status_code >= 500:
            FAIL.append(f"GET {p} -> {r.status_code} {r.text[:120]}")
    except Exception as e:
        FAIL.append(f"GET {p} -> {e}")
print(f"GET taramasi: {n} uc")

# 2) is akisi
def ck(name, r, ok=(200, 201)):
    if r.status_code not in ok:
        FAIL.append(f"AKIS {name} -> {r.status_code} {r.text[:150]}")
    try:
        return r.json()
    except Exception:
        return {}
u = str(random.randint(100000, 999999))
ck("usta ekle", requests.post(B + "/technicians", json={"name": "CI Usta", "email": f"ci{u}@x.com", "phone": "0533" + u + "1", "password": "Usta12345!"}, headers=H))
tl = requests.post(B + "/auth/login", json={"email": f"ci{u}@x.com", "password": "Usta12345!"}); ck("usta giris", tl)
HT = {"Authorization": "Bearer " + tl.json().get("token", "")}
tid = next((t["id"] for t in requests.get(B + "/technicians", headers=H).json() if t.get("email") == f"ci{u}@x.com"), "")
br = (requests.get(B + "/brands", headers=H).json() or [{}])[0].get("id", "")
j = ck("is ac", requests.post(B + "/jobs/quick", json={"customer_name": "CI Musteri", "customer_phone": "0532" + u + "9", "brand_id": br, "device_type": "kombi", "fault_description": "test", "priority": "normal"}, headers=H))
jid = j.get("id", "x")
ck("usta ata", requests.put(B + f"/jobs/{jid}", json={"assigned_technician_id": tid, "status": "atandi"}, headers=H))
lst = requests.get(B + "/jobs", headers=HT).json()
if not any(x.get("id") == jid for x in (lst if isinstance(lst, list) else [])):
    FAIL.append("AKIS usta atanan isi goremiyor")
ck("yolda", requests.post(B + f"/jobs/{jid}/on-the-way", json={"eta_minutes": 20}, headers=HT))
ck("basladi", requests.put(B + f"/jobs/{jid}", json={"status": "devam_ediyor"}, headers=HT))
ck("tamamlandi", requests.put(B + f"/jobs/{jid}", json={"status": "tamamlandi", "work_done": "ok", "total_amount": 1000, "labor_cost": 1000}, headers=HT))
ck("tahsilat", requests.put(B + f"/accounting/jobs/{jid}/collection", json={"amount": 1000, "method": "nakit", "collected_by": "technician"}, headers=H))
tk = ck("takip linki", requests.post(B + f"/jobs/{jid}/track-link", headers=H)).get("token", "x")
ck("musteri takip", requests.get(B + f"/public/track/{tk}"))
ck("anket", requests.post(B + f"/public/track/{tk}/survey", json={"rating": 5, "comment": "iyi"}))
ck("teklif", requests.post(B + "/quotes", json={"customer_name": "CI", "target_total": 500}, headers=H))
ck("randevu", requests.post(B + "/appointments", json={"title": "CI", "start_at": "2030-01-01T10:00:00"}, headers=H))
ck("site formu", requests.post(B + "/public/contact", json={"name": "CI Form", "phone": "05321112233", "message": "test", "sid": "ci" + u + "xx", "source": "form"}))
for e in ("ozet", "musteri", "usta", "site", "finans"):
    ck("rapor " + e, requests.get(B + f"/rapor/{e}?days=30", headers=H))
ck("kurulum", requests.get(B + "/admin/kurulum", headers=H))
if requests.get(B + "/admin/kurulum", headers=HT).status_code != 403:
    FAIL.append("GUVENLIK usta yonetici kurulum sayfasini acabiliyor")
if requests.get(B + "/jobs").status_code != 401:
    FAIL.append("GUVENLIK girissiz is listesi aciliyor")

print("\n".join(FAIL) if FAIL else "TUM TESTLER GECTI")
sys.exit(1 if FAIL else 0)
