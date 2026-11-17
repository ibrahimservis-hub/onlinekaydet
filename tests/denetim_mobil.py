"""Müşteri paneli mobil taraması: her sektörden bir demo, tüm menü rotaları 390px (JS hatası, 4xx/5xx, yatay taşma)."""
import sys, os, threading, time, json
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
import uvicorn, requests as rq
import demo; demo.GUNLUK_LIMIT = 10 ** 6
srv = uvicorn.Server(uvicorn.Config(boot.server.app, host="127.0.0.1", port=8799, log_level="critical")); threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    try:
        if rq.get("http://127.0.0.1:8799/api/health", timeout=2).status_code < 500: break
    except Exception: time.sleep(0.2)
U = "http://127.0.0.1:8799"; B = U + "/api"
from playwright.sync_api import sync_playwright
SEK = sys.argv[1].split(",") if len(sys.argv) > 1 else ["kombi", "kuafor", "lokanta", "oto_cekici", "avukat", "eticaret"]
rep = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for i, sk in enumerate(SEK):
        demo._RATE.clear()
        d = rq.post(B + "/public/demo", json={"name": "Mobil Deneme", "phone": "05531%06d" % (700 + i), "sector": sk}).json()
        if "email" not in d: rep.append((sk, "-", "DEMO AÇILMADI", str(d)[:100])); continue
        ctx = br.new_context(viewport={"width": 390, "height": 800}, device_scale_factor=1, is_mobile=True, has_touch=True); pg = ctx.new_page()
        errs, bad = [], []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.on("response", lambda r: bad.append("%s %s" % (r.status, r.url.replace(U, "")[:80])) if r.status >= 400 and "/api/" in r.url and "/auth/me" not in r.url else None)
        pg.goto(U + "/salon"); pg.wait_for_selector("#lf", timeout=15000)
        pg.fill("#lf input[name=email]", d["email"]); pg.fill("#lf input[name=password]", d["password"]); pg.click("#lb"); pg.wait_for_selector("#app:not([hidden])", timeout=15000); pg.wait_for_timeout(800)
        routes = pg.evaluate("NAV.map(x=>x[0]).concat(EXTRA||[])"); seen = set()
        for r in routes:
            if r in seen: continue
            seen.add(r); errs.clear(); bad.clear()
            pg.evaluate("location.hash='#%s'" % r); pg.wait_for_timeout(900)
            m = pg.evaluate("""()=>{const de=document.documentElement,o=[],IW=390;document.querySelectorAll('#main *').forEach(e=>{const b=e.getBoundingClientRect();if(b.width>0&&b.right>IW+3&&getComputedStyle(e).position!=='fixed'){let p=e.parentElement,sc=false;while(p&&p.id!=='main'){const ov=getComputedStyle(p).overflowX;if(ov==='auto'||ov==='scroll'||ov==='hidden'){sc=true;break}p=p.parentElement}if(!sc&&o.length<3)o.push(e.tagName+'.'+String(e.className).slice(0,20)+' '+Math.round(b.right))}});
              return {sw:de.scrollWidth,iw:IW,o:o,load:(document.querySelector('#main')||{}).innerText?.indexOf('Yükleniyor')>-1,empty:((document.querySelector('#main')||{}).innerText||'').trim().length<5}}""")
            prob = []
            if m["sw"] > m["iw"] + 2: prob.append("sayfa yatay taşıyor %d>%d" % (m["sw"], m["iw"]))
            if m["o"]: prob.append("taşan: " + "; ".join(m["o"]))
            if m["load"]: prob.append("Yükleniyor'da kaldı")
            if m["empty"]: prob.append("boş ekran")
            if errs: prob.append("JS: " + errs[0])
            if bad: prob.append("API: " + ", ".join(sorted(set(bad))[:3]))
            if prob:
                rep.append((sk, r, " | ".join(prob), ""))
                if any("taş" in x for x in prob): pg.screenshot(path="/tmp/mob/%s-%s.png" % (sk, r))
        print(sk, "rota:", len(seen), flush=True); ctx.close()
    br.close()
for x in rep: print("SORUN", x[0], x[1], x[2], x[3])
print("TOPLAM SORUN", len(rep))
