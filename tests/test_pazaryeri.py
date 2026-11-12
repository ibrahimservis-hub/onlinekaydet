"""Pazaryeri: eşleştirme, gönderim ve stok senkronu. En kritik kural: stok eksiye düşmez, çift düşmez."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import boot
os.environ["BACKGROUND_JOBS"] = "0"
import logging; logging.disable(logging.CRITICAL)
from starlette.testclient import TestClient
s = boot.server; ok, bad = [], []; S = {}
def t(n, f):
    try: f(); ok.append(n)
    except Exception:
        import traceback; bad.append((n, traceback.format_exc()[-700:]))
with TestClient(s.app) as c:
    j = c.post("/api/public/demo", json={"name": "Ayşe", "phone": "05524165755", "sector": "Kuaför"}).json()
    H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": j["email"], "password": j["password"]}).json()["token"]}
    def mk(name, stock, cat="Gömlek", brand="Nevermore", chans=None):
        return c.post("/api/yp/products", headers=H, json={
            "name": name, "price": 900, "cost": 400, "stock": stock, "cat": cat, "brand": brand,
            "channels": chans or {"trendyol": True, "hepsiburada": True}}).json()["id"]
    def a():
        r = c.get("/api/yp/channels", headers=H).json()["rows"]
        assert len(r) >= 10 and all(x["on"] is False for x in r), "başta hiçbiri bağlı değil"
        ty = [x for x in r if x["id"] == "trendyol"][0]
        assert ty["name"] == "Trendyol" and ty["commission"] == 18.0
        assert c.put("/api/yp/channels/yok", headers=H, json={"on": True}).status_code == 404
        assert c.put("/api/yp/channels/trendyol", headers=H, json={"on": True, "keys": {"api": "x", "secret": "y"}}).json()["on"]
        assert c.put("/api/yp/channels/hepsiburada", headers=H, json={"on": True, "keys": {"api": "z"}}).json()["on"]
        r2 = [x for x in c.get("/api/yp/channels", headers=H).json()["rows"] if x["id"] == "trendyol"][0]
        assert r2["on"] and r2["status"] == "bagli"
        assert "keys" not in r2, "anahtarlar listede dönmemeli"
    t("pazaryeri bağlantısı açılıyor, anahtarlar listede gizli", a)
    def b():
        S["p1"] = mk("Keten Gömlek", 10)
        S["p2"] = mk("Yün Kazak", 4, cat="Kazak")
        m = c.get("/api/yp/channels/trendyol/map", headers=H).json()
        assert m["cats_missing"] == 2 and m["brands_missing"] == 1
        assert {"local": "Gömlek", "n": 1, "remote": "", "remote_id": "", "ok": False} in m["cats"]
        c.put("/api/yp/channels/trendyol/map", headers=H, json={
            "cats": [{"local": "Gömlek", "remote_id": "411", "remote": "Kadın > Gömlek"}, {"local": "Kazak", "remote_id": ""}],
            "brands": [{"local": "Nevermore", "remote_id": "9912"}]})
        m = c.get("/api/yp/channels/trendyol/map", headers=H).json()
        assert m["cats_missing"] == 1 and m["brands_missing"] == 0
        assert [x for x in m["cats"] if x["local"] == "Gömlek"][0]["remote"] == "Kadın > Gömlek"
    t("kategori ve marka eşleştirme kaydediliyor, eksikler sayılıyor", b)
    def d():
        r = c.post("/api/yp/channels/trendyol/send", headers=H, json={}).json()
        assert r["sent"] == 1 and r["skipped_n"] == 1, r
        assert "Kazak" in r["skipped"][0]["why"], r["skipped"]
        assert c.post("/api/yp/channels/n11/send", headers=H, json={}).status_code == 422, "kapalı kanala gönderilmez"
        q = c.get("/api/yp/sync", headers=H).json()
        assert q["counts"]["bekliyor"] == 1 and q["rows"][0]["kind"] == "full"
    t("gönderim: eşleşmemiş kategorideki ürün atlanıyor, kapalı kanal reddediliyor", d)
    def e():
        r = c.post("/api/yp/stock/take", headers=H, json={
            "source": "trendyol", "ref": "TY-1001", "items": [{"product": S["p1"], "qty": 3}]}).json()
        assert r["ok"] and r["rows"][0]["taken"] == 3 and r["rows"][0]["stock"] == 7
        assert c.get("/api/yp/products/" + S["p1"], headers=H).json()["stock"] == 7
        rows = c.get("/api/yp/sync", headers=H, params={"state": "bekliyor"}).json()["rows"]
        chans = {x["channel"] for x in rows if x["kind"] == "stock"}
        assert chans == {"hepsiburada"}, "sipariş gelen kanala geri gönderilmez, diğerine gönderilir"
    t("sipariş gelince stok düşüyor ve YALNIZ diğer kanallara gönderim kuyruğa giriyor", e)
    def f():
        r = c.post("/api/yp/stock/take", headers=H, json={
            "source": "trendyol", "ref": "TY-1001", "items": [{"product": S["p1"], "qty": 3}]}).json()
        assert r["rows"][0]["repeat"] is True and r["rows"][0]["taken"] == 0, "aynı sipariş ikinci kez düşmemeli"
        assert c.get("/api/yp/products/" + S["p1"], headers=H).json()["stock"] == 7
    t("aynı sipariş iki kez gelirse stok ikinci kez düşmüyor", f)
    def g():
        r = c.post("/api/yp/stock/take", headers=H, json={
            "source": "site", "ref": "W-1", "items": [{"product": S["p1"], "qty": 99}]}).json()
        assert r["ok"] is False and r["rows"][0]["taken"] == 0 and "Stok yetersiz" in r["rows"][0]["err"]
        assert c.get("/api/yp/products/" + S["p1"], headers=H).json()["stock"] == 7, "başarısız istek stoğu bozmamalı"
        assert c.post("/api/yp/stock/take", headers=H, json={"source": "site", "ref": "W-2",
                                                              "items": [{"product": S["p1"], "qty": 0}]}).status_code == 422
    t("stok yetmezse düşülmüyor; eksiye inmiyor", g)
    def h():
        r = c.post("/api/yp/stock/take", headers=H, json={
            "source": "site", "ref": "W-3", "items": [{"product": S["p1"], "qty": 7}]}).json()
        assert r["rows"][0]["stock"] == 0
        kinds = {(x["channel"], x["kind"]) for x in c.get("/api/yp/sync", headers=H, params={"state": "bekliyor", "limit": 300}).json()["rows"]}
        assert ("trendyol", "passive") in kinds and ("hepsiburada", "passive") in kinds, "stok bitince ilan pasife alınmalı"
    t("stok sıfırlanınca tüm kanallarda ilanı pasife alma kuyruğa giriyor", h)
    def i():
        before = c.get("/api/yp/products/" + S["p2"], headers=H).json()["stock"]
        r = c.post("/api/yp/stock/set", headers=H, json={"product": S["p2"], "stock": 25}).json()
        assert r["stock"] == 25 and r["before"] == before
        assert c.post("/api/yp/stock/set", headers=H, json={"product": S["p2"], "stock": -5}).json()["stock"] == 0
        log = c.get("/api/yp/stock/log", headers=H, params={"product": S["p1"]}).json()["rows"]
        assert [x["delta"] for x in log][:2] == [-7, -3] and log[0]["after"] == 0
        assert [x["source"] for x in log] == ["site", "trendyol"]
    t("elle stok ayarı ve stok geçmişi (kim, ne zaman, kaç adet)", i)
    def k():
        q = c.get("/api/yp/sync", headers=H).json()["counts"]
        assert q["bekliyor"] > 0
        r = c.post("/api/yp/sync/run", headers=H, json={}).json()
        assert r["done"] == 0 and r["left"] == q["bekliyor"], "gönderici yokken kayıtlar beklemeli, kaybolmamalı"
        assert c.post("/api/yp/sync/retry", headers=H, json={}).json()["n"] == 0
    t("kuyruk: gönderici bağlı değilken kayıtlar kaybolmuyor", k)
print("OK" if not bad else "FAIL", len(ok), "geçti")
for n, e in bad: print("✗", n, "\n", e)
sys.exit(1 if bad else 0)
