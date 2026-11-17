"""Müşteri paneli: rol başına menü ve ekranlar (403 yok)."""
import sys, os, threading, time, socket
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import boot
os.environ["BACKGROUND_JOBS"]="0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests
from playwright.sync_api import sync_playwright
import demo; demo.GUNLUK_LIMIT=10**6
port=socket.socket(); port.bind(("127.0.0.1",0)); PORT=port.getsockname()[1]; port.close()
srv=uvicorn.Server(uvicorn.Config(boot.server.app,host="127.0.0.1",port=PORT,log_level="critical")); threading.Thread(target=srv.run,daemon=True).start()
for _ in range(60):
    try: socket.create_connection(("127.0.0.1",PORT),0.3).close(); break
    except OSError: time.sleep(0.2)
U="http://127.0.0.1:%d"%PORT
d=requests.post(U+"/api/public/demo",json={"name":"Deneme Kisi","phone":"05530001234","sector":"kuafor"}).json()
tk=requests.post(U+"/api/auth/login",json={"email":d["email"],"password":d["password"]}).json()["token"]
H={"Authorization":"Bearer "+tk}
uid=requests.post(U+"/api/firm/users",headers=H,json={"email":"r@deneme.com","password":"Sifre12345","name":"R"}).json()["id"]
N={}
with sync_playwright() as pw:
    br=pw.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    for rol in ("manager","accounting","operations","site_editor","viewer"):
        requests.put(U+"/api/firm/users/"+uid,headers=H,json={"rol":rol}); None
        ctx=br.new_context(viewport={"width":1280,"height":900}); pg=ctx.new_page(); bad=[]; errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.on("response",lambda r:bad.append((r.status,r.url.split("/api")[-1][:40])) if r.status in (401,403) and "/api/" in r.url else None)
        pg.goto(U+"/salon"); pg.wait_for_selector("#lf"); pg.fill("#lf input[name=email]","r@deneme.com"); pg.fill("#lf input[name=password]","Sifre12345"); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])",timeout=15000); pg.wait_for_timeout(1500)
        navs=pg.eval_on_selector_all("#nav a","e=>e.map(x=>x.dataset.rs.split(',')[0])")
        rs=pg.eval_on_selector_all("#nav a","e=>e.flatMap(x=>x.dataset.rs.split(','))")
        bad.clear()
        for r in rs:
            pg.evaluate("location.hash='#%s'"%r); pg.wait_for_timeout(700)
        print(rol,len(rs),"ekran | 401/403:",sorted(set(bad))[:14],"| js:",errs[:2])
        assert not bad and not errs, (rol,bad,errs)
        N[rol]=len(rs)
        ctx.close()

assert N["manager"]>N["accounting"]>0 and N["site_editor"]<N["operations"]<N["manager"] and N["viewer"]==N["manager"], N
print("OK menüler rol başına daralır, hiçbir ekranda 403 yok", N)
