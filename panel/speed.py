"""Hız iyileştirmeleri: eksik indeksler + kısa ömürlü ayar önbelleği. Yalnızca ekleme; veriyi değiştirmez."""
import time

_CACHE = {}
_USERS = {}
_STATS = {}
_T0 = time.time()          # bu işlemin (sürecin) başladığı an
_REQS = [0]


def user_cache_get(uid, ttl=10.0):
    e = _USERS.get(uid)
    if e and time.monotonic() - e[0] < ttl:
        return dict(e[1])
    return None


def user_cache_put(uid, user):
    if len(_USERS) > 500:
        _USERS.clear()
    _USERS[uid] = (time.monotonic(), dict(user))


def proc_info():
    import os
    d = {"pid": os.getpid(), "uptime_s": round(time.time() - _T0, 1), "reqs": _REQS[0]}
    try:
        d["boot_s"] = float(os.environ.get("SPX_BOOT_S", "0") or 0)
        d["pre"] = os.environ.get("SPX_PRE", "")
        d["ppid"] = os.getppid()
    except Exception:                                # noqa: BLE001
        pass
    return d


def record(route, ms):
    _REQS[0] += 1
    a = _STATS.setdefault(route, [0, 0.0, 0.0])
    a[0] += 1
    a[1] += ms
    if ms > a[2]:
        a[2] = ms


async def cached_global(db, ttl=5.0):
    """app_settings/global belgesini kısa süre bellekte tutar (her istekte tekrar okunmaz)."""
    import tenant
    ck = "g:" + str(tenant.current() or "")          # firma başına ayrı önbellek (veri karışmasın)
    e = _CACHE.get(ck)
    if e and time.monotonic() - e[0] < ttl:
        return e[1]
    d = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
    _CACHE[ck] = (time.monotonic(), d)
    return d


def invalidate():
    _CACHE.clear()


INDEXES = [
    ("service_jobs", [("assigned_technician_id", 1), ("status", 1)]),
    ("service_jobs", [("status", 1), ("created_at", -1)]),
    ("service_jobs", [("created_at", -1)]),
    ("service_jobs", [("customer_id", 1)]),
    ("service_jobs", [("device_id", 1)]),
    ("service_jobs", [("completed_at", -1)]),
    ("service_jobs", [("track_token", 1)]),
    ("customers", [("phone", 1)]),
    ("customers", [("created_at", -1)]),
    ("devices", [("customer_id", 1)]),
    ("devices", [("qr_token", 1)]),
    ("users", [("role", 1)]),
    ("cash_transactions", [("date", -1)]),
    ("cash_transactions", [("job_id", 1)]),
    ("appointments", [("date", 1)]),
    ("contact_messages", [("status", 1), ("created_at", -1)]),
    ("price_quotes", [("created_at", -1)]),
    ("price_quotes", [("technician_id", 1)]),
    ("chat_messages", [("created_at", -1)]),
    ("announcements", [("created_at", -1)]),
    ("shop_orders", [("created_at", -1)]),
    ("shop_products", [("slug", 1)]),
    ("audit_log", [("user_id", 1), ("at", -1)]),
    ("push_subs", [("user_id", 1)]),
    ("service_jobs", [("scheduled_at", 1)]),
    ("outbox", [("kind", 1), ("ref", 1)]),
]


async def ensure_indexes(db):
    for coll, keys in INDEXES:
        try:
            await db[coll].create_index(keys, background=True)
        except Exception:                                # noqa: BLE001  (aynı indeks farklı seçenekle varsa atla)
            pass


def register(api_router, db):
    import asyncio
    import os
    from fastapi import HTTPException

    @api_router.get("/speed")
    async def speed_test(k: str = ""):
        """Hız teşhisi (anahtarla): veritabanı gecikmesi, sorgu süreleri, işlem döngüsü gecikmesi. Gizli veri döndürmez."""
        if k != os.environ.get("SPEED_KEY", "SPYENI2026"):
            raise HTTPException(404, "Not Found")
        out = {"surec": proc_info()}
        t = time.perf_counter()
        try:
            await db.command("ping")
        except Exception:                                # noqa: BLE001
            pass
        out["mongo_ping_ms"] = round((time.perf_counter() - t) * 1000, 1)
        res = {}
        for name, coro in (
            ("kullanici_okuma", lambda: db.users.find_one({"role": "admin"}, {"_id": 0, "id": 1})),
            ("is_sayisi", lambda: db.service_jobs.estimated_document_count()),
            ("son_50_is", lambda: db.service_jobs.find({}, {"_id": 0, "id": 1}).sort("created_at", -1).to_list(50)),
            ("usta_isleri", lambda: db.service_jobs.find({"assigned_technician_id": "x", "status": "atandi"}, {"_id": 0, "id": 1}).to_list(50)),
        ):
            t = time.perf_counter()
            try:
                await coro()
            except Exception:                            # noqa: BLE001
                pass
            res[name] = round((time.perf_counter() - t) * 1000, 1)
        out["sorgu_ms"] = res
        t = time.perf_counter()
        await asyncio.sleep(0)
        for _ in range(5):
            await asyncio.sleep(0.01)
        out["dongu_gecikme_ms"] = round(((time.perf_counter() - t) - 0.05) * 1000, 1)
        out["koleksiyon_boyutu"] = {}
        for c in ("service_jobs", "customers", "audit_log", "outbox", "pageviews", "visitor_sessions", "error_log", "contact_messages"):
            try:
                out["koleksiyon_boyutu"][c] = await db[c].estimated_document_count()
            except Exception:                            # noqa: BLE001
                pass
        try:
            out["cpu"] = os.cpu_count()
            with open("/proc/self/status") as fh:
                for ln in fh:
                    if ln.startswith("VmRSS"):
                        out["bellek_mb"] = round(int(ln.split()[1]) / 1024)
        except Exception:                                # noqa: BLE001
            pass
        out["en_yavas_istekler"] = [{"istek": r, "adet": v[0], "ort_ms": round(v[1] / v[0]), "max_ms": round(v[2])}
                                    for r, v in sorted(_STATS.items(), key=lambda kv: -kv[1][1] / max(kv[1][0], 1))[:15]]
        out["yorum"] = ("mongo_ping_ms > 50: veritabanı uzak/yavaş (en büyük yavaşlık nedeni). "
                        "sorgu_ms > 100: indeks/veri sorunu. dongu_gecikme_ms > 50: sunucu CPU'su yetersiz/meşgul.")
        return out

    @api_router.get("/speed/ping")
    async def speed_ping(k: str = "", db_: int = 0):
        """Uçtan uca hız testi için en hafif uç: süreç kimliği + çalışma süresi (db_=1 ise tek veritabanı okuması)."""
        if k != os.environ.get("SPEED_KEY", "SPYENI2026"):
            raise HTTPException(404, "Not Found")
        t = time.perf_counter()
        if db_:
            try:
                await db.app_settings.find_one({"_id": "boot"}, {"_id": 1})
            except Exception:                            # noqa: BLE001
                pass
        return dict(proc_info(), app_ms=round((time.perf_counter() - t) * 1000, 1))

    @api_router.get("/speed/test")
    async def speed_page(k: str = ""):
        if k != os.environ.get("SPEED_KEY", "SPYENI2026"):
            raise HTTPException(404, "Not Found")
        from fastapi.responses import HTMLResponse
        return HTMLResponse(_TEST_HTML.replace("__K__", k), headers={"Cache-Control": "no-store"})


_TEST_HTML = """<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hız testi</title>
<body style="font:14px/1.5 ui-monospace,Consolas,monospace;margin:16px;color:#111;background:#fff"><h3 style="margin:0 0 8px">ServisPlus uçtan uca hız testi</h3>
<div id="st">Çalışıyor… (1-2 dakika sürebilir, "Bitti" yazana kadar bekleyin)</div><pre id="o" style="white-space:pre-wrap"></pre>
<script>
(async function(){
var K='__K__',o=document.getElementById('o'),L=[];function p(t){L.push(t);o.textContent=L.join('\\n');}
async function hit(u,opt){var t=performance.now(),ac=new AbortController(),tm=setTimeout(function(){ac.abort()},45000);try{var r=await fetch(u,Object.assign({cache:'no-store',signal:ac.signal},opt||{}));var ttfb=performance.now()-t;var b=await r.text();var ms=performance.now()-t;var j=null;try{j=JSON.parse(b)}catch(e){}
 clearTimeout(tm);return {ok:r.status,ms:Math.round(ms),ttfb:Math.round(ttfb),kb:Math.round(b.length/1024),j:j,xs:r.headers.get('x-spx')||'',body:(r.status!==200?b.slice(0,700):'')};}catch(e){clearTimeout(tm);return {ok:'HATA',ms:Math.round(performance.now()-t),ttfb:0,kb:0,j:null,xs:String(e),body:'(45 sn içinde yanıt gelmedi ya da bağlantı koptu: '+e+')'};}}
function row(n,x){var j=x.j||{};if(x.ok!==200)return (n+'').padEnd(4)+(' '+x.ok).padEnd(6)+(x.ms+' ms').padEnd(10)+' >>> '+String(x.body||'').replace(/\\s+/g,' ');return (n+'').padEnd(4)+(' '+x.ok).padEnd(6)+(x.ms+' ms').padEnd(10)+('ilk bayt '+x.ttfb+' ms').padEnd(20)+('uygulama '+(j.app_ms!=null?j.app_ms:'?')+' ms').padEnd(20)+('süreç '+(j.pid||'?')).padEnd(16)+('açık '+(j.uptime_s!=null?j.uptime_s:'?')+' sn').padEnd(16)+('istek# '+(j.reqs!=null?j.reqs:'?'));}
var pids={};function note(x){if(x.j&&x.j.pid)pids[x.j.pid]=x.j;}
p('Tarih: '+new Date().toLocaleString('tr-TR')+'   Tarayıcı bağlantısı: '+((navigator.connection&&navigator.connection.effectiveType)||'?'));
p('');p('1) Art arda 10 hafif istek (veritabanı yok):');
for(var i=1;i<=10;i++){var x=await hit('/api/speed/ping?k='+K+'&_='+i);note(x);p(row(i,x));}
p('');p('2) Art arda 5 istek (tek veritabanı okuması):');
for(i=1;i<=5;i++){x=await hit('/api/speed/ping?k='+K+'&db_=1&_='+i);note(x);p(row(i,x));}
p('');p('3) AYNI ANDA 8 istek (panel sayfası açılışı gibi):');
p('   (yanıtlar geldikçe yazılır; en fazla 45 sn beklenir)');
var t0=performance.now();var rs=await Promise.all([1,2,3,4,5,6,7,8].map(function(i){return hit('/api/speed/ping?k='+K+'&db_=1&p='+i).then(function(x){note(x);p(row(i,x)+'   [+'+Math.round(performance.now()-t0)+' ms]');return x;});}));
p('   toplam: '+Math.round(performance.now()-t0)+' ms');
p('');p('3b) Aynı anda 8 istek TEKRAR (kopyalar artık açık olmalı):');
t0=performance.now();rs=await Promise.all([1,2,3,4,5,6,7,8].map(function(i){return hit('/api/speed/ping?k='+K+'&db_=1&q='+i).then(function(x){note(x);p(row(i,x)+'   [+'+Math.round(performance.now()-t0)+' ms]');return x;});}));
p('   toplam: '+Math.round(performance.now()-t0)+' ms');
p('');p('4) Panel dosyaları (önbelleksiz indirme):');
var h=await hit('/');p('   ana sayfa (index.html): '+h.ok+'  '+h.ms+' ms  '+h.kb+' KB');
try{var d=await (await fetch('/',{cache:'no-store'})).text();var m=d.match(/\\/static\\/js\\/main[^"']+\\.js/);var c=d.match(/\\/static\\/css\\/main[^"']+\\.css/);
if(m){x=await hit(m[0]);p('   ana JS: '+x.ok+'  '+x.ms+' ms  ilk bayt '+x.ttfb+' ms  '+x.kb+' KB (açılmış boyut)');}
if(c){x=await hit(c[0]);p('   ana CSS: '+x.ok+'  '+x.ms+' ms  '+x.kb+' KB');}
x=await hit('/panel-ek.js');p('   panel-ek.js: '+x.ok+'  '+x.ms+' ms  '+x.kb+' KB');}catch(e){p('   dosya testi hatası: '+e);}
p('');p('5) Gerçek panel istekleri (oturum açıksa):');
var tk=null;try{tk=localStorage.getItem('token')}catch(e){}
if(tk){var H={headers:{Authorization:'Bearer '+tk}};var us=['/api/auth/me','/api/jobs','/api/customers','/api/technicians','/api/brands','/api/dashboard/admin'];
for(i=0;i<us.length;i++){x=await hit(us[i],H);p('   '+us[i].padEnd(24)+(' '+x.ok).padEnd(6)+(x.ms+' ms').padEnd(10)+('ilk bayt '+x.ttfb+' ms').padEnd(20)+x.kb+' KB   '+x.xs);}
t0=performance.now();rs=await Promise.all(us.map(function(u){return hit(u,H);}));p('   aynı anda 6 istek toplam: '+Math.round(performance.now()-t0)+' ms  ('+rs.map(function(x){return x.ms}).join(', ')+')');}
else p('   (bu tarayıcıda panel oturumu yok — önce panele giriş yapıp bu sayfayı yenileyin)');
p('');var ks=Object.keys(pids);p('ÖZET: '+ks.length+' farklı süreç yanıt verdi: '+ks.map(function(k){return k+' (açık '+pids[k].uptime_s+' sn, açılış '+(pids[k].boot_s||'?')+' sn, ön-yükleme '+(pids[k].pre||'?')+', üst süreç '+(pids[k].ppid||'?')+')';}).join(' | '));
document.getElementById('st').textContent='Bitti. Bu sayfanın ekran görüntüsünü gönderin.';
})();
</script></body></html>"""
