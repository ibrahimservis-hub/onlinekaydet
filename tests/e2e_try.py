import sys,os,json;sys.path.insert(0,os.path.dirname(__file__));import boot
os.environ["BACKGROUND_JOBS"]="0"
from starlette.testclient import TestClient
s=boot.server
with TestClient(s.app) as c:
    r=c.post("/api/auth/login",json={"email":"admin@servis.com","password":"admin123"});print("admin login",r.status_code,list(r.json())[:5])
    H={"Authorization":"Bearer "+r.json().get("token",r.json().get("access_token",""))}
    r=c.post("/api/admin/firms",headers=H,json={"name":"Ege Kombi","email":"hasan@egekombi.com","password":"sifre12345","features":{}});print("firma",r.status_code,r.text[:200])
    r=c.post("/api/auth/login",json={"email":"hasan@egekombi.com","password":"sifre12345"});print("firma login",r.status_code,r.text[:200])
