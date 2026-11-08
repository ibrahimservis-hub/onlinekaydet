"""Kurumsal akışlar: ödeme linki (iyzico taklit), teklif onay linki, müşteri portalı, arayan numara, e-arşiv, firma ön ekli herkese açık bağlantılar."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception as e: bad.append((n, repr(e)[:400]))
def tok(c, e, p): r = c.post("/api/auth/login", json={"email": e, "password": p}); assert r.status_code == 200, r.text; return {"Authorization": "Bearer " + r.json()["token"]}
with TestClient(s.app) as c:
    A = tok(c, "admin@servis.com", "admin123")
    fids = {}
    for k, n in (("kurumsal", "K Firma"), ("tam", "T Firma")):
        r = c.post("/api/admin/firms", headers=A, json={"name": n, "email": f"{k}@x.com", "password": "sifre12345", "package": k}); assert r.status_code == 200, r.text
        fids[k] = r.json()["id"]; S[k] = tok(c, f"{k}@x.com", "sifre12345")
    O = S["kurumsal"]; F = fids["kurumsal"]
    CU = c.post("/api/customers", headers=O, json={"name": "Ayşe Yılmaz", "phone": "0532 111 22 33", "address": "Kazımdirik 123/4", "district": "Bornova", "city": "İzmir"}).json()
    J = c.post("/api/jobs", headers=O, json={"customer_id": CU["id"], "fault_description": "Isıtmıyor"}).json()
    r = c.put(f"/api/jobs/{J['id']}", headers=O, json={"labor_fee": 1150}); assert r.status_code == 200, r.text
    S["job"] = c.get(f"/api/jobs/{J['id']}", headers=O).json(); assert float(S["job"].get("total_amount", 0)) == 1150, S["job"].get("total_amount")
    calls = []
    async def fake_iy(path, body):
        calls.append((path, body))
        if "initialize" in path: return {"status": "success", "token": "ITOK1", "paymentPageUrl": "https://sandbox.iyzipay.com/pay/ITOK1"}
        if "detail" in path: return {"status": "success", "paymentStatus": "SUCCESS", "paidPrice": body.get("_paid", 1150.0), "paymentId": "P1"}
        return {"status": "success"}
    s.app.state.kurumsal_iyzico = fake_iy
    def pt(tk): return f"{F}~{tk}"
    def a():
        r = c.post(f"/api/pay/jobs/{J['id']}/link", headers=O, json={}); assert r.status_code == 200, r.text
        S["url"] = r.json()["url"]; S["ptok"] = S["url"].rsplit("/", 1)[1]; assert S["ptok"].startswith(F + "~") and r.json()["amount"] == 1150
        assert c.post(f"/api/pay/jobs/{J['id']}/link", headers=O, json={"amount": 5000}).status_code == 400, "borçtan fazla tutar"
    t("ödeme linki üretilir (firma ön ekli), borcu aşan tutar reddedilir", a)
    def b():
        r = c.get(f"/api/public/pay/{S['ptok']}"); assert r.status_code == 200 and r.json()["amount"] == 1150 and r.json()["firm"] == "K Firma", r.text
        assert r.json()["can_pay"] is False, "iyzico anahtarı yokken ödeme kapalı görünmeli"
        r = c.get("/odeme/" + S["ptok"]); assert r.status_code == 200 and "Servis ödemesi" in r.text
    t("herkese açık ödeme sayfası ve uç firmayı ön ekten bulur; anahtar yokken ödeme kapalı", b)
    # firma veritabanına iyzico anahtarı yaz (sp_modules)
    import asyncio, tenant
    def seed_iyzico(fid):
        async def go():
            tk = tenant.set_firm(s.db.firm_db_name(fid))
            try: await s.db.app_settings.update_one({"_id": "sp_modules"}, {"$set": {"config": {"iyzico": {"api_key": "k", "secret_key": "sec", "sandbox": "1"}}}}, upsert=True)
            finally: tenant.reset(tk)
        c.portal.call(go)
    seed_iyzico(F)
    def e():
        assert c.get(f"/api/public/pay/{S['ptok']}").json()["can_pay"] is True
        r = c.post(f"/api/public/pay/{S['ptok']}/init"); assert r.status_code == 200 and r.json()["url"].endswith("ITOK1"), r.text
        body = [b for p, b in calls if "initialize" in p][-1]; assert body["price"] == "1150.00" and f"/api/public/pay/{S['ptok']}/callback" in body["callbackUrl"]
    t("anahtar tanımlıyken iyzico ödeme formu açılır; callback adresi firma ön ekli", e)
    def f():
        r = c.post(f"/api/public/pay/{S['ptok']}/callback", data={"token": "YANLIS"}, follow_redirects=False); assert r.status_code == 303 and "s=hata" in r.headers["location"]
        assert c.get(f"/api/public/pay/{S['ptok']}").json()["status"] == "pending"
        r = c.post(f"/api/public/pay/{S['ptok']}/callback", data={"token": "ITOK1"}, follow_redirects=False); assert r.status_code == 303 and "s=ok" in r.headers["location"], r.headers
        j = c.get(f"/api/jobs/{J['id']}", headers=O).json(); assert j["payment"]["status"] == "odendi" and j["payment"]["paid"] == 1150 and j["payment"]["history"][-1]["method"] == "kart", j.get("payment")
        c.post(f"/api/public/pay/{S['ptok']}/callback", data={"token": "ITOK1"}, follow_redirects=False)
        j = c.get(f"/api/jobs/{J['id']}", headers=O).json(); assert j["payment"]["paid"] == 1150 and len(j["payment"]["history"]) == 1, "çift callback tahsilatı ikiye katlamamalı"
        assert c.get(f"/api/public/pay/{S['ptok']}").json()["status"] == "paid"
    t("yanlış jeton reddedilir; doğru callback tahsilatı işler ve tekrarı çift saymaz", f)
    def g():
        tk = S["ptok"].split("~")[1]
        r = c.get(f"/api/public/pay/{fids['tam']}~{tk}"); assert r.status_code in (403, 404), r.status_code
        assert c.get(f"/api/public/pay/{'0'*12}~{tk}").status_code == 404
    t("başka firmanın ön ekiyle jeton çalışmaz (firmalar arası sızıntı yok)", g)
    def h():
        r = c.post("/api/pay/test", headers=O); assert r.status_code == 200 and r.json()["ok"]
        r = c.post(f"/api/pay/jobs/{J['id']}/link", headers=S["tam"], json={}); assert r.status_code == 403
    t("iyzico bağlantı testi çalışır; Tam Paket'te ödeme linki kilitli", h)
    # ---- teklif
    def i():
        r = c.post("/api/quotes", headers=O, json={"customer_name": "Murat Şen", "customer_phone": "05330001122", "device_brand_name": "Baymak", "device_model": "Luna", "fault_description": "Sensör", "target_total": 1150, "labor_fee": 500, "parts": [{"name": "Sensör", "qty": 1, "unit_price": 650}]})
        assert r.status_code == 200, r.text; S["q"] = r.json()
        r = c.post(f"/api/quotes/{S['q']['id']}/share", headers=O, json={}); assert r.status_code == 200, r.text
        S["qt"] = r.json()["url"].rsplit("/", 1)[1]; assert S["qt"].startswith(F + "~")
        r = c.get(f"/api/public/quote/{S['qt']}"); assert r.status_code == 200 and r.json()["total"] == 1150 and r.json()["decision"] == "", r.text
        assert "technician" not in r.text.lower()
        assert abs(sum(l["total"] for l in r.json()["lines"]) - 1150) < 0.01, r.json()["lines"]
    t("teklif paylaşım linki üretilir; herkese açık görünümde teknisyen bilgisi sızmaz", i)
    def j():
        assert c.post(f"/api/public/quote/{S['qt']}/decision", json={"decision": "belki"}).status_code == 422
        r = c.post(f"/api/public/quote/{S['qt']}/decision", json={"decision": "onay", "note": "Tamam"}); assert r.status_code == 200 and r.json()["decision"] == "onaylandi", r.text
        assert c.post(f"/api/public/quote/{S['qt']}/decision", json={"decision": "red"}).status_code == 409
        q = [x for x in c.get("/api/quotes", headers=O).json() if x["id"] == S["q"]["id"]][0]; assert q["customer_decision"] == "onaylandi" and q["customer_note"] == "Tamam"
        assert c.get("/teklif/" + S["qt"]).status_code == 200
    t("müşteri teklifi onaylar; ikinci karar reddedilir; karar teklif kaydına işlenir", j)
    def k():
        assert c.post(f"/api/quotes/{S['q']['id']}/share", headers=S["tam"], json={}).status_code == 403
    t("Tam Paket'te teklif paylaşımı kilitli", k)
    # ---- portal
    def l():
        T = f"{F}~giris"
        assert c.post(f"/api/public/portal/{T}/login", json={"phone": "123"}).status_code == 422
        assert c.post(f"/api/public/portal/{T}/login", json={"phone": "05321112233"}).status_code == 200
        assert c.post(f"/api/public/portal/{T}/login", json={"phone": "05999999999"}).status_code == 200, "kayıtsız numara da aynı yanıtı almalı"
        async def code():
            tk = tenant.set_firm(s.db.firm_db_name(F))
            try: return await s.db.portal_codes.find_one({"phone": "5321112233"}, {"_id": 0})
            finally: tenant.reset(tk)
        row = c.portal.call(code); assert row, "kayıtlı müşteri için kod üretilmeli"
        async def nocode():
            tk = tenant.set_firm(s.db.firm_db_name(F))
            try: return await s.db.portal_codes.find_one({"phone": "5999999999"})
            finally: tenant.reset(tk)
        assert c.portal.call(nocode) is None, "kayıtsız numaraya kod üretilmemeli"
        S["T"] = T
    t("portal girişi: kayıtlı numaraya kod üretilir, kayıtsıza üretilmez ama yanıt aynı", l)
    def m():
        T = S["T"]
        import hashlib
        async def setcode():
            tk = tenant.set_firm(s.db.firm_db_name(F))
            try: await s.db.portal_codes.update_one({"phone": "5321112233"}, {"$set": {"code_hash": hashlib.sha256(("123456" + "5321112233").encode()).hexdigest()}})
            finally: tenant.reset(tk)
        c.portal.call(setcode)
        assert c.post(f"/api/public/portal/{T}/verify", json={"phone": "05321112233", "code": "000000"}).status_code == 400
        r = c.post(f"/api/public/portal/{T}/verify", json={"phone": "05321112233", "code": "123456"}); assert r.status_code == 200, r.text; S["sess"] = r.json()["session"]
        assert c.post(f"/api/public/portal/{T}/verify", json={"phone": "05321112233", "code": "123456"}).status_code == 400, "kod tek kullanımlık"
        assert c.get(f"/api/public/portal/{T}/me").status_code == 401
        r = c.get(f"/api/public/portal/{T}/me", headers={"X-Portal": S["sess"]}); assert r.status_code == 200, r.text
        d = r.json(); assert d["name"] == "Ayşe" and len(d["jobs"]) == 1 and d["jobs"][0]["total"] == 1150, d
        r = c.post(f"/api/public/portal/{T}/request", headers={"X-Portal": S["sess"]}, json={"fault": "Su akıtıyor"}); assert r.status_code == 200, r.text
        assert c.post(f"/api/public/portal/{T}/request", headers={"X-Portal": S["sess"]}, json={"fault": "a"}).status_code == 422
        assert c.get("/portal/" + T).status_code == 200
    t("portal: yanlış kod reddedilir, doğru kodla oturum açılır, kayıtlarım görünür, talep gider", m)
    def n():
        T = f"{fids['tam']}~giris"
        assert c.post(f"/api/public/portal/{T}/login", json={"phone": "05321112233"}).status_code == 403
    t("Tam Paket'te portal kapalı", n)
    # ---- arayan numara
    def o():
        r = c.get("/api/caller/lookup", params={"phone": "+90 532 111 22 33"}, headers=O); assert r.status_code == 200, r.text
        d = r.json(); assert d["known"] and d["customer"]["name"] == "Ayşe Yılmaz" and d["open_jobs"] == 1 and len(d["last_jobs"]) == 1, d
        assert c.get("/api/caller/lookup", params={"phone": "05001234567"}, headers=O).json()["known"] is False
        assert c.get("/api/caller/lookup", params={"phone": "05321112233"}, headers=S["tam"]).status_code == 403
    t("arayan numara: boşluklu kayıtla eşleşir, bilinmeyen numara bilinmiyor döner, Tam Paket'te kilitli", o)
    # ---- e-arşiv
    def p():
        assert c.post("/api/einvoice/test", headers=O).status_code == 400
        c.put("/api/finance/plus/settings", headers=O, json={"invoice": {"webhook_url": "https://entegrator.test/hook", "webhook_headers": "X-Key: abc"}})
    t("e-arşiv testi: webhook tanımsızken açık hata verir", p)
    def q():
        import finance_plus
        class R:
            status_code = 200; text = "{}"
            def json(self): return {"id": "ENT-1"}
        sent = []
        orig = finance_plus.requests.post
        finance_plus.requests.post = lambda url, json=None, headers=None, timeout=0: (sent.append((url, json, headers)), R())[1]
        try:
            async def setset():
                tk = tenant.set_firm(s.db.firm_db_name(F))
                try: await s.db.app_settings.update_one({"_id": "global"}, {"$set": {"finance_plus.invoice.webhook_url": "https://entegrator.test/hook", "finance_plus.invoice.webhook_headers": "X-Key: abc"}}, upsert=True)
                finally: tenant.reset(tk)
            c.portal.call(setset)
            r = c.post("/api/einvoice/test", headers=O); assert r.status_code == 200 and r.json()["ok"], r.text
            assert sent[-1][1].get("test") is True and sent[-1][2].get("X-Key") == "abc"
            r = c.post(f"/api/einvoice/jobs/{J['id']}/issue", headers=O, json={}); assert r.status_code == 200, r.text
            inv = r.json(); assert inv["status"] == "gonderildi" and inv["provider_ref"] == "ENT-1" and inv["total"] == 1150, inv
            n0 = len(sent); r2 = c.post(f"/api/einvoice/jobs/{J['id']}/issue", headers=O, json={}); assert r2.json()["id"] == inv["id"] and len(sent) == n0, "aynı iş için ikinci fatura kesilmemeli"
            assert c.post(f"/api/einvoice/jobs/{J['id']}/issue", headers=S["tam"], json={}).status_code == 403
        finally:
            finance_plus.requests.post = orig
    t("e-arşiv: bağlantı testi, tek tıkla kes ve gönder, ikinci kez kesmez; Tam Paket'te kilitli", q)
    # ---- mevcut herkese açık bağlantılar firma ön ekiyle
    def r_():
        async def seed():
            tk = tenant.set_firm(s.db.firm_db_name(F))
            try: await s.db.service_jobs.update_one({"id": J["id"]}, {"$set": {"track_token": "TRK1234567890abcdef"}})
            finally: tenant.reset(tk)
        c.portal.call(seed)
        r = c.get(f"/api/public/track/{F}~TRK1234567890abcdef"); assert r.status_code == 200, r.text
        assert c.get(f"/takip/{F}~TRK1234567890abcdef").status_code == 200
        assert c.get("/api/public/track/TRK1234567890abcdef").status_code == 404, "ön eksiz istek ana veritabanına gider; firma verisi görünmemeli"
    t("mevcut takip bağlantısı firma ön ekiyle de çalışır", r_)
print(f"GEÇTİ {len(ok)}/{len(ok)+len(bad)}")
for a in bad: print("BAŞARISIZ", a)
