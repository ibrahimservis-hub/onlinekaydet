import sys, os, json, threading, time
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import notify, uvicorn, requests as rq
class R:
    status_code = 200
    def __init__(s, j): s._j = j; s.text = json.dumps(j)
    def json(s): return s._j
_real = rq.post
def fake(url, json=None, **k):
    if "iletimerkezi" in url: return R({"response": {"status": {"code": 200, "message": "ok"}, "order": {"id": "1"}, "balance": {"sms": "250"}}})
    return _real(url, json=json, **k)
notify.requests.post = fake
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8765, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if _real("http://127.0.0.1:8765/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}, timeout=2).status_code == 200: break
    except Exception: time.sleep(0.2)
B = "http://127.0.0.1:8765/api"
T = _real(B + "/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]; H = {"Authorization": "Bearer " + T}
def post(p, j): return rq.request("POST", B + p, json=j, headers=H)
rq.request("PUT", B + "/governance/notify-settings", json={"provider": "iletimerkezi", "iletimerkezi": {"key": "k", "hash": "x", "sender": "ONLINEKYDT"}}, headers=H)
for n, e, ph, sec, pk, d in [("Ege Kombi Servisi", "hasan@egekombi.com", "05321112233", "kombi", "profesyonel", 30), ("Anka Klima", "anka@klima.com", "05320000002", "klima", "baslangic", 9),
                              ("Yıldız Beyaz Eşya", "yildiz@be.com", "05320000003", "beyaz_esya", "tam", 200), ("Güvenli Kamera", "guv@kamera.com", "05320000004", "guvenlik", "profesyonel", 4)]:
    r = post("/admin/firms", {"name": n, "email": e, "password": "sifre12345", "phone": ph, "sector": sec, "package": pk, "usage_days": d, "contact_name": n.split()[0]}).json()
    post(f"/admin/firms/{r['id']}/payments", {"amount": 1200 if d > 20 else 600, "extend_days": 0, "note": "Aylık"})
print("HAZIR", flush=True)
while True: time.sleep(60)
