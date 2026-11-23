"""Her bölüm tek tek gizlenince tema betiği hata vermez (null.addEventListener vb.). Kullanım: test_tema_gizle_js.py [tema-adı-parçası ...]"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
from playwright.sync_api import sync_playwright
s = boot.server; import kurumsal as K, domains
only = sys.argv[1:]; bad = {}; n = 0
SH = os.environ.get('SHARD'); SH = tuple(int(x) for x in SH.split('/')) if SH else None
with TestClient(s.app) as c:
    tok = lambda e, p: {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": e, "password": p}).json()["token"]}
    A = tok("admin@servis.com", "admin123")
    F = c.post("/api/admin/firms", headers=A, json={"name": "Gizle Js", "email": "gj@x.com", "password": "sifre12345", "package": "tam"}).json()["id"]; O = tok("gj@x.com", "sifre12345")
    async def setup():
        f = await s.db.main().firms.find_one({"id": F}, {"_id": 0, "db": 1})
        await s.db.main().firm_domains.insert_one({"id": "gj1", "domain": "gj-test.com", "firm_id": F, "db": f["db"], "status": "yayinda"}); return f["db"]
    DB = c.portal.call(setup)
    async def tema(slug):
        S = s.db.firm(DB); await S.app_settings.update_one({"_id": "brand"}, {"$set": {"theme": slug}}, upsert=True); await S.app_settings.delete_one({"_id": "site_profile"})
    domains._cache["t"] = 0
    G = lambda: c.get("/api/public/hosted-site?p=%2F", headers={"Host": "gj-test.com"}).text
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); pg = br.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:140] + " @" + ",".join(__import__("re").findall(r":(\d+:\d+)", getattr(e, "stack", "") or "")[:2])))
        def yukle(h):
            errs.clear(); pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
            try: pg.set_content(h, wait_until="domcontentloaded", timeout=60000)
            except Exception: return list(errs)
            pg.wait_for_timeout(700); return list(errs)
        for ti, th in enumerate(K.THEMES):
            sl = th["slug"]
            if SH and ti % SH[1] != SH[0]: continue
            if only and not any(o in sl for o in only): continue
            if os.environ.get('ORNEK') and not (sl.split('-')[0].isdigit() or sl.startswith('k') or re.match(r'p(0[1-9]|1[0-2])-', sl)): continue
            c.portal.call(tema, sl); domains._cache["t"] = 0
            pr = c.get("/api/site/profile", headers=O).json()["profile"]
            blocks = c.get("/api/site/blocks", headers=O).json()["blocks"]
            base = yukle(G())
            for b in blocks:
                if b["hidden"]: continue
                pr["layout"] = {"order": [], "hidden": [b["name"]]}; c.put("/api/site/profile", headers=O, json=pr)
                h = G(); r1 = [x for x in yukle(h) if x not in base]; n += 1
                e = r1
                if r1:                      # yük altında dalgalanan hatalar elenir: üç yüklemede de aynı hata çıkmalı
                    for _ in range(2):
                        r2 = yukle(h); e = [x for x in e if x in r2]
                        if not e: break
                if e: bad.setdefault(sl, {})[b["name"]] = e[0]
            pr["layout"] = {"order": [], "hidden": []}; c.put("/api/site/profile", headers=O, json=pr)
        br.close()
print("denenen", n, "hatalı tema", len(bad))
for k, v in bad.items(): print(k, v)
