import sys,os
sys.path.insert(0,os.path.dirname(__file__)); import boot
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s=boot.server
with TestClient(s.app) as c:
    r=c.get("/api/public/packages"); assert r.status_code==200,r.text
    P=r.json()["packages"]; assert [p["id"] for p in P]==["baslangic","profesyonel","tam","kurumsal"],P
    assert P[0]["price"]==990 and P[0]["yearly"]==9900 and P[0]["features"]
    A={"Authorization":"Bearer "+c.post("/api/auth/login",json={"email":"admin@servis.com","password":"admin123"}).json()["token"]}
    g=c.get("/api/admin/packages",headers=A).json()["packages"]
    g["baslangic"]["price"]=1111; g["baslangic"]["features"]=["Deneme madde"]; g["baslangic"]["tagline"]="Yeni açıklama"
    assert c.put("/api/admin/packages",headers=A,json={"packages":g}).status_code==200
    q=c.get("/api/public/packages").json()["packages"][0]
    assert q["price"]==1111 and q["yearly"]==9900 and q["features"]==["Deneme madde"] and q["tagline"]=="Yeni açıklama",q
print("OK")
