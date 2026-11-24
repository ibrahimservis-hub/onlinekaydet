"""Sitedeki izle.js: açık ölçüm etiketlerini yükler, talep gönderilince dönüşümü sayar; kapalıysa hiçbir şey yüklemez."""
import json, sys
from playwright.sync_api import sync_playwright
JS = open("site/izle.js", encoding="utf-8").read()
def calis(olcum, dnt=False):
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = br.new_context(java_script_enabled=True).new_page()
        istek = []
        pg.route("**/*", lambda r: (istek.append(r.request.url), r.fulfill(status=200, content_type="application/json" if "/api/" in r.request.url else "text/javascript",
                                  body=json.dumps(olcum) if "/api/public/olcum" in r.request.url else ("{}" if "/api/" in r.request.url else "")))[1])
        pg.goto("http://x.test/"); pg.set_content("<html><head></head><body></body></html>")
        if dnt: pg.evaluate("Object.defineProperty(navigator,'doNotTrack',{get:()=>'1'})")
        pg.add_script_tag(content=JS); pg.wait_for_timeout(800)
        sonuc = pg.evaluate("""()=>{window.__g=[];if(window.gtag){var o=window.dataLayer.length}; window.OKTrack&&window.OKTrack.event('form_submit'); return {dl:(window.dataLayer||[]).map(function(a){return Array.prototype.slice.call(a).map(String)}),fbq:typeof window.fbq,ttq:typeof window.ttq,cl:typeof window.clarity}}""")
        pg.wait_for_timeout(300); br.close(); return istek, sonuc
i, r = calis({"ga4": {"id": "G-ABC123DEF4"}, "meta_pixel": {"id": "123456"}, "clarity": {"id": "abcd1234"}, "tiktok_pixel": {"id": "CABC123456"}})
assert any("googletagmanager.com/gtag/js?id=G-ABC123DEF4" in u for u in i), i
assert any("connect.facebook.net" in u and "fbevents" in u for u in i), i
assert any("clarity.ms/tag/abcd1234" in u for u in i), i
assert any("analytics.tiktok.com" in u for u in i), i
flat = json.dumps(r["dl"]); assert "generate_lead" in flat and "G-ABC123DEF4" in flat, flat
assert r["fbq"] == "function" and r["ttq"] == "object" and r["cl"] == "function", r
i2, r2 = calis({})
assert not any("googletagmanager" in u or "facebook" in u for u in i2), i2
i3, _ = calis({"ga4": {"id": "G-ABC123DEF4"}}, dnt=True)
assert not any("googletagmanager" in u for u in i3), "İzleme kapalıysa yüklenmemeli"
print("OK 3")
