"""cPanel "Setup Python App" (Passenger) giriş dosyası.

Passenger WSGI konuşur, panel ise FastAPI (ASGI). Bu dosya a2wsgi ile ikisini bağlar ve
FastAPI'nin başlangıç işlerini (indeksler, yönetici hesabı, zamanlayıcı) bir kez çalıştırır.
Motor (MongoDB istemcisi) tek bir olay döngüsüne bağlı kalmalıdır; bu yüzden sunucu modülü
ve tüm istekler aynı arka plan döngüsünde çalışır.
"""
import asyncio
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
os.chdir(HERE)

# Motor, her veritabani cagrisini kendi iplik havuzunda calistirir; varsayilan cok yuksektir (cekirdek x 5) ve es zamanli
# istekte surec basina 15+ iplik acar. Hosting hesap kotasi dolunca "can't start new thread" ve 503 olusur.
os.environ.setdefault("MOTOR_MAX_WORKERS", "4")


def _preload():
    """Agir kutuphaneleri surec catallanmadan ONCE yukler: sunucu ayni anda gelen istekler icin yeni kopya (cocuk surec)
    actiginda bu moduller hazir gelir, her kopya bastan yuklemez. Yalnizca kutuphane; baglanti/iplik/dongu acilmaz."""
    for m in ("asyncio", "json", "fastapi", "fastapi.routing", "fastapi.openapi.models", "fastapi.responses", "starlette.middleware.cors",
              "starlette.middleware.gzip", "starlette.middleware.base", "pydantic", "email_validator", "anyio", "a2wsgi", "motor.motor_asyncio",
              "pymongo", "bson.json_util", "requests", "jwt", "bcrypt", "dotenv", "bs4", "segno", "zoneinfo"):
        try:
            __import__(m)
        except Exception:       # noqa: BLE001
            pass


_PRE = {"server": False, "s": 0.0}
if os.environ.get("SPX_PRELOAD", "1") != "0":
    import time as _t0m
    _t0 = _t0m.time()
    _preload()
    if os.environ.get("SPX_PRELOAD", "1") != "lib":
        # Uygulama modulunu de surec catallanmadan once yukle (yalnizca kod: baglanti/iplik acilmaz, Motor ilk kullanimda baglanir).
        # Sunucu es zamanli istekler icin yeni kopya actiginda 1-5 sn'lik yukleme tekrarlanmaz.
        try:
            import server as _pre_server       # noqa: F401
            _PRE["server"] = True
        except BaseException:                  # noqa: BLE001  (hata olursa normal yol: _boot icinde yuklenir ve gunluge yazilir)
            sys.modules.pop("server", None)
    _PRE["s"] = _t0m.time() - _t0


def _fail(exc):
    """Başlatma hatasını dosyaya yazar (şifre/ortam bilgisi yazılmaz) ve sade bir hata sayfası döndürür."""
    import traceback
    try:
        with open(os.path.join(HERE, "startup-error.log"), "w", encoding="utf-8") as fh:
            fh.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    except Exception:       # noqa: BLE001
        pass

    def app(environ, start_response):
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return ["Panel baslatilamadi. onlinekaydet_app/startup-error.log dosyasina bakin.".encode("utf-8")]
    return app


_state = {"ready": False, "error": None, "app": None}
_done = threading.Event()   # hazir ya da hata: bekleyen istekleri uyandirir
_mem = []          # son ilerleme satirlari (dosyaya yazilamasa bile sayfada gosterilir)


def _progress(msg):
    """Adim adim ilerleme (sifre yazilmaz): servisplus-panel/startup-progress.log"""
    import time
    line = time.strftime("%H:%M:%S ") + msg
    _mem.append(line)
    del _mem[:-40]
    try:
        with open(os.path.join(HERE, "startup-progress.log"), "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception as e:       # noqa: BLE001
        _mem.append("   (gunluk dosyasi yazilamadi: %s)" % e)


def _watchdog():
    """Her 10 sn'de bellek kullanimi ve yukleme ipliginin bulundugu satiri yazar (teshis)."""
    import time
    import traceback
    while not _state["ready"] and _state["error"] is None:
        time.sleep(10)
        try:
            rss = "?"
            with open("/proc/self/status") as fh:
                for ln in fh:
                    if ln.startswith("VmRSS"):
                        rss = ln.split(":")[1].strip()
            where = "-"
            for t in threading.enumerate():
                if t.name == "panel-loop":
                    fr = sys._current_frames().get(t.ident)
                    if fr is not None:
                        st = traceback.extract_stack(fr)[-3:]
                        where = " < ".join("%s:%s" % (os.path.basename(f.filename), f.lineno) for f in reversed(st))
            _progress("... bellek=%s  yer=%s" % (rss, where))
        except Exception:       # noqa: BLE001
            pass


_pending = set()
_ACT = {"n": 0, "last": 0.0}


def _janitor():
    """Hesabin iplik kotasini koru: (1) son yeniden baslatmadan ONCE acilmis eski surecleri kapat,
    (2) bosta kalan fazla surecleri kapat (bir 'ana' surec her zaman sicak kalir). Aktif istegi olan surece dokunulmaz."""
    import time, glob, signal
    try:
        import fcntl
    except Exception:       # noqa: BLE001
        fcntl = None
    idle_s = float(os.environ.get("SPX_IDLE_EXIT_S", "90"))
    lock_fh = None
    me = os.getpid()
    marker = os.path.join(HERE, "tmp", "restart.txt")
    clk = os.sysconf("SC_CLK_TCK")
    try:
        btime = [int(l.split()[1]) for l in open("/proc/stat") if l.startswith("btime")][0]
    except Exception:       # noqa: BLE001
        btime = 0
    _ACT["last"] = time.time()
    while True:
        time.sleep(30)
        try:
            # (1) eski surecler
            if btime and os.path.isfile(marker):
                mt = os.path.getmtime(marker)
                cwd = os.path.realpath(HERE)
                anc, p = {me}, me
                for _ in range(6):
                    try:
                        p = int(open("/proc/%d/stat" % p).read().rsplit(")", 1)[1].split()[1])
                    except Exception:       # noqa: BLE001
                        break
                    if p <= 1:
                        break
                    anc.add(p)
                uid = os.getuid()
                for d in glob.glob("/proc/[0-9]*"):
                    try:
                        pid = int(d.rsplit("/", 1)[1])
                        if pid in anc:
                            continue
                        if ("Uid:\t%d" % uid) not in open(d + "/status").read():
                            continue
                        if os.path.realpath(os.readlink(d + "/cwd")) != cwd:
                            continue
                        st = int(open(d + "/stat").read().rsplit(")", 1)[1].split()[19])
                        if btime + st / clk < mt - 5:
                            os.kill(pid, signal.SIGTERM)
                            _progress("eski surec kapatildi: %s" % pid)
                    except Exception:       # noqa: BLE001
                        continue
            # (2) bosta fazla surec
            if fcntl is not None and _ACT["n"] <= 0 and time.time() - _ACT["last"] > idle_s:
                if lock_fh is None:
                    try:
                        os.makedirs(os.path.join(HERE, "tmp"), exist_ok=True)
                        fh = open(os.path.join(HERE, "tmp", "primary.lock"), "a+")
                        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        lock_fh = fh           # ana surec: sicak kalir
                    except Exception:       # noqa: BLE001
                        _progress("bosta fazla surec kapaniyor (%s)" % me)
                        os._exit(0)
        except Exception:       # noqa: BLE001
            pass


def _track_tasks():
    """Istekten sonra baslatilan arka plan isleri (bildirim, SMS, e-posta) bu hostingte
    istekler arasinda donabildigi icin takip edilir; istek bitmeden kisa sure beklenir."""
    orig = asyncio.create_task

    def tracked(coro, *a, **k):
        import time
        t = orig(coro, *a, **k)
        try:
            t._spx_until = time.monotonic() + 8      # bu is en fazla 8 sn boyunca istekleri bekletebilir
        except Exception:       # noqa: BLE001
            pass
        _pending.add(t)
        t.add_done_callback(_pending.discard)
        return t
    asyncio.create_task = tracked


async def _wait_pending():
    """Yalnizca yeni baslamis (ilk 8 sn) arka plan islerini bekler. Uzun suren bir is (site denetimi,
    yavas SMS/webhook) eskiden her istegi 8 sn bekletiyordu; artik suresi dolan is beklenmez."""
    import time
    now = time.monotonic()
    ps = [t for t in list(_pending) if not t.done() and getattr(t, "_spx_until", 0) > now]
    if ps:
        left = max(0.05, min(8.0, max(getattr(t, "_spx_until", now) for t in ps) - now))
        await asyncio.wait(ps, timeout=left)


def _drain(loop):
    try:
        asyncio.run_coroutine_threadsafe(_wait_pending(), loop).result(10)
    except Exception:       # noqa: BLE001
        pass


def _wrap(resp, loop):
    _ACT["n"] += 1
    try:
        for chunk in resp:
            yield chunk
    finally:
        _ACT["n"] -= 1
        import time as _tt
        _ACT["last"] = _tt.time()
        close = getattr(resp, "close", None)
        if close:
            close()
        _drain(loop)


def _patch_assets():
    """Panel arayuzu baska bir markanin paketinden geldiginde (ServisPlus): gomulu API adresini bu sitenin
    /api adresine, marka adini OnlineKaydet'e cevirir, ucuncu taraf analiz adresini kapatir.
    Her acilista calisir; degisecek bir sey kalmadiysa dosyaya dokunmaz."""
    try:
        import re as _re
        pp = os.path.join(HERE, "public_panel")
        rep = [
            (b'"https://bayi.servisplus.net.tr/api"', b'"/api"'),
            (b'"https://bayi.servisplus.net.tr"', b'""'),
            (b'https://bayi.servisplus.net.tr/logo-servisplus.jpg', b'https://onlinekaydet.com/logo-servisplus.jpg'),
            (b'https://servisplus.net.tr/images/logo.png', b'/logo-servisplus.jpg'),
            (b'us-assets.i.posthog.com', b'posthog.invalid'),
            (b'us.i.posthog.com', b'posthog.invalid'),
            (b'ServisPlus', b'OnlineKaydet'),
        ]
        files = []
        js = os.path.join(pp, "static", "js")
        if os.path.isdir(js):
            files += [os.path.join(js, n) for n in sorted(os.listdir(js)) if n.startswith("main.") and n.endswith(".js")]
        files += [os.path.join(pp, n) for n in ("panel-ek.js", "belge.js", "spx-sw.js", "sw.js", "index.html", "manifest.json")]
        for p in files:
            if not os.path.isfile(p):
                continue
            with open(p, "rb") as fh:
                b = fh.read()
            o = b
            for a, z in rep:
                b = b.replace(a, z)
            if b != o:
                with open(p, "wb") as fh:
                    fh.write(b)
                _progress("marka/adres duzeltildi: " + os.path.basename(p))
        idx = os.path.join(pp, "index.html")
        if os.path.isfile(idx):                    # onbellekteki eski ek dosyalar yenilensin: surum = dosya zamani
            with open(idx, "rb") as fh:
                h = fh.read()
            o = h
            for n in ("panel-ek.js", "belge.js"):
                f = os.path.join(pp, n)
                if os.path.isfile(f):
                    h = _re.sub(n.replace(".", r"\.").encode() + rb"\?v=[0-9a-z]+", (n + "?v=" + str(int(os.path.getmtime(f)))).encode(), h)
            if h != o:
                with open(idx, "wb") as fh:
                    fh.write(h)
    except Exception as e:       # noqa: BLE001
        _progress("arayuz duzeltme atlandi: %s" % e)


def _boot():
    """Yükleme + başlangıç işlerini arka planda yapar; web sunucusu beklemeden yanıt verebilsin."""
    try:
        try:
            os.remove(os.path.join(HERE, "startup-progress.log"))
        except OSError:
            pass
        import time as _tm
        _t_boot = _tm.time()
        _progress("surec basladi (pid %s)" % os.getpid())
        _patch_assets()
        threading.Thread(target=_watchdog, name="panel-watch", daemon=True).start()
        _loop = asyncio.new_event_loop()
        ready = threading.Event()
        box = {}

        def run():
            asyncio.set_event_loop(_loop)
            try:
                _progress("server modulu yukleniyor")
                import server as _server        # Motor istemcisi bu döngüde oluşur
                _server.PROGRESS = _progress
                try:                            # on-yuklenmis modul: Motor'u bu surecin dongusune bagla, sayaclari sifirla
                    _server.client._io_loop = None
                    import time as _tq
                    _server.speed._T0 = _tq.time()
                    _server.speed._REQS[0] = 0
                    _server.speed._STATS.clear()
                except Exception:               # noqa: BLE001
                    pass
                _progress("server modulu yuklendi (on-yukleme: %s, %.1f sn)" % ("evet" if _PRE["server"] else "hayir", _PRE["s"]))
                box["server"] = _server
            except BaseException as e:           # noqa: BLE001
                box["error"] = e
                ready.set()
                return
            ready.set()
            _loop.run_forever()

        threading.Thread(target=run, name="panel-loop", daemon=True).start()
        ready.wait(300)
        if "error" in box:
            raise box["error"]
        if "server" not in box:
            raise RuntimeError("Sunucu modulu yuklenemedi (MONGO_URL / bagimliliklari kontrol edin)")
        server = box["server"]
        async def _run_startup():
            r = server.app.router
            if hasattr(r, "startup"):            # eski Starlette
                await r.startup()
            else:                                # yeni Starlette: on_event isleyicileri lifespan ile calisir
                box["lifespan"] = r.lifespan_context(server.app)
                await box["lifespan"].__aenter__()
        asyncio.run_coroutine_threadsafe(_run_startup(), _loop).result(600)
        from a2wsgi import ASGIMiddleware
        _state["app"] = ASGIMiddleware(server.app, loop=_loop)
        _state["loop"] = _loop
        _track_tasks()
        _state["ready"] = True
        try:
            os.environ["SPX_BOOT_S"] = "%.1f" % (_tm.time() - _t_boot)      # /api/speed ciktisinda gorunur (acilis suresi)
            os.environ["SPX_PRE"] = "%s/%.1f" % ("evet" if _PRE["server"] else "hayir", _PRE["s"])
        except Exception:       # noqa: BLE001
            pass
        _progress("HAZIR (%s sn)" % os.environ.get("SPX_BOOT_S", "?"))
        if os.environ.get("SPX_JANITOR", "1") != "0":
            threading.Thread(target=_janitor, name="panel-janitor", daemon=True).start()
        _done.set()
    except BaseException as exc:                 # noqa: BLE001
        _state["error"] = exc
        _ERR["t"] = __import__("time").time()
        _progress("HATA: %s: %s" % (type(exc).__name__, str(exc)[:300].replace(os.environ.get("MONGO_URL", "\0"), "***")))
        _write_error(exc)
        _done.set()


def _write_error(exc):
    import traceback
    try:
        with open(os.path.join(HERE, "startup-error.log"), "w", encoding="utf-8") as fh:
            fh.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    except Exception:       # noqa: BLE001
        pass


_started = {"pid": None}
_lock = threading.Lock()


_ERR = {"t": 0.0, "n": 0}


def _ensure_started():
    """Passenger uygulamayi once on yukleyip sonra catallayabilir (iplikler cocuga gecmez);
    bu yuzden baslatma, istegi karsilayan surecte ve ilk istekte yapilir.
    Gecici hata (ornegin hesabin iplik kotasi doluyken "can't start new thread") surecin sonsuza dek
    'Panel baslatilamadi' vermesine yol acmaz: 6 sn sonra yeniden denenir; 4 denemede de olmazsa
    surec kapanir ve sunucu temiz bir surec baslatir."""
    import time
    pid = os.getpid()
    if _started["pid"] == pid and (_state["error"] is None or time.time() - _ERR["t"] < 6):
        return
    with _lock:
        if _started["pid"] == pid:
            if _state["error"] is None or time.time() - _ERR["t"] < 6:
                return
            if _ERR["n"] >= 4:
                os._exit(1)
            _ERR["n"] += 1
        _started["pid"] = pid
        _state.update(ready=False, error=None, app=None)
        _done.clear()
        threading.Thread(target=_boot, name="panel-boot", daemon=True).start()


import mimetypes as _mt
_SITE = os.environ.get("SITE_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "onlinekaydet.com")
if not os.path.isdir(_SITE):
    _SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
_RESERVED = ("/api", "/static", "/giris", "/login", "/panel", "/uploads", "/brand", "/fonts", "/pdfjs", "/rehber")


def _site_file(path):
    """Satis sitesi (statik) dosyasini bul; panel yollarina dokunma."""
    if path == "/" or path == "":
        cand = "index.html"
    else:
        if path.startswith(_RESERVED):
            return None
        cand = path.lstrip("/")
    cand = os.path.normpath(cand)
    if cand.startswith("..") or os.path.isabs(cand):
        return None
    for c in (cand, cand + ".html", os.path.join(cand, "index.html")):
        fp = os.path.join(_SITE, c)
        if os.path.isfile(fp):
            return fp
    return None


_OVR = os.environ.get("ANASITE_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "anasite_ozel")


def _ovr_file(path):
    """Yönetim panelinden düzenlenen ana site sayfası / yüklenen görsel."""
    if path.startswith("/anasite-gorsel/"):
        fn = os.path.basename(path)
        fp = os.path.join(_OVR, "img", fn)
        return fp if os.path.isfile(fp) else None
    if path.startswith(_RESERVED):
        return None
    cand = "index.html" if path in ("/", "") else path.lstrip("/")
    cand = os.path.basename(cand)
    for c in (cand, cand + ".html"):
        fp = os.path.join(_OVR, c)
        if c.endswith(".html") and os.path.isfile(fp):
            return fp
    return None


def _serve_site(environ, start_response):
    if environ.get("REQUEST_METHOD") not in ("GET", "HEAD"):
        return None
    _p = environ.get("PATH_INFO", "/") or "/"
    fp = _ovr_file(_p) or _site_file(_p)
    if not fp:
        return None
    ctype = _mt.guess_type(fp)[0] or "application/octet-stream"
    if ctype.startswith("text/") or ctype in ("application/javascript", "application/json", "application/xml"):
        ctype += "; charset=utf-8"
    with open(fp, "rb") as f:
        data = f.read()
    cc = "no-cache" if fp.endswith(".html") else "public, max-age=86400"
    start_response("200 OK", [("Content-Type", ctype), ("Content-Length", str(len(data))), ("Cache-Control", cc)])
    return [] if environ.get("REQUEST_METHOD") == "HEAD" else [data]


def _owner_redirect(environ, start_response):
    """Platform sahibi (firmasiz admin) panel sayfalarina gelirse /yonetim paneline yolla."""
    if environ.get("REQUEST_METHOD") != "GET":
        return None
    path = environ.get("PATH_INFO", "") or ""
    if not (path in ("/admin", "/giris", "/login", "/tech") or path.startswith(("/admin/", "/tech/"))):
        return None
    try:
        import base64, json
        from http.cookies import SimpleCookie
        ck = SimpleCookie(environ.get("HTTP_COOKIE", ""))
        tok = ck["access_token"].value if "access_token" in ck else ""
        if not tok:
            return None
        seg = tok.split(".")[1]
        c = json.loads(base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4)))
        if c.get("role") == "admin" and not c.get("firm"):
            start_response("302 Found", [("Location", "/yonetim"), ("Cache-Control", "no-store"), ("Content-Length", "0")])
            return []
    except Exception:
        return None
    return None

_DOMMAP = {"t": 0.0, "m": {}}
_PANEL_PATHS = ("/api", "/salon", "/static", "/uploads", "/brand", "/fonts", "/pdfjs", "/rehber", "/giris", "/login", "/panel", "/admin", "/tech",
                "/takip", "/cihaz", "/bakim", "/odeme", "/teklif", "/portal", "/uye-girisi", "/manifest.json", "/spx-sw.js", "/panel-ek.js",
                "/giris-skin.js", "/belge.js", "/favicon.ico", "/apple-touch-icon.png", "/icon-192.png", "/icon-512.png", "/asset-manifest.json")


def _custom_host(environ):
    """Müşterinin kendi alan adından gelen istek mi? (firm_domains.json, panel tarafından yazılır)"""
    host = (environ.get("HTTP_X_FORWARDED_HOST") or environ.get("HTTP_HOST") or "").lower().split(":")[0]
    if not host or host == "onlinekaydet.com" or host.endswith(".onlinekaydet.com") or host in ("localhost", "127.0.0.1"):
        return False
    try:
        import json, time
        fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "firm_domains.json")
        if time.time() - _DOMMAP["t"] > 20:
            _DOMMAP["m"] = json.load(open(fp, encoding="utf-8")) if os.path.isfile(fp) else {}
            _DOMMAP["t"] = time.time()
        return host in _DOMMAP["m"]
    except Exception:
        return False


def application(environ, start_response):
    import time as _ta
    _ACT["last"] = _ta.time()
    if _custom_host(environ):
        p = environ.get("PATH_INFO", "") or "/"
        if environ.get("REQUEST_METHOD") in ("GET", "HEAD") and not p.startswith(_PANEL_PATHS):
            environ["PATH_INFO"] = "/api/public/hosted-site"        # firmanın temalı sitesi
            environ["REQUEST_URI"] = "/api/public/hosted-site"
            import urllib.parse as _up
            environ["QUERY_STRING"] = "p=" + _up.quote(p)
        _ensure_started()
        if not _state["ready"] and _state["error"] is None:
            _done.wait(25)
        if _state["ready"]:
            if (environ.get("PATH_INFO", "").rstrip("/") == "/uye-girisi"):
                environ["PATH_INFO"] = "/giris"
            return _wrap(_state["app"](environ, start_response), _state["loop"])
    if (environ.get("PATH_INFO", "") or "").rstrip("/") == "/uye-girisi":
        environ["PATH_INFO"] = "/giris"            # uye girisi: musteri paneli giris ekrani (adres cubugunda /giris kalir)
        environ["REQUEST_URI"] = "/giris"
        environ["OK_UYE_GIRISI"] = "1"
    _r = None if environ.get("OK_UYE_GIRISI") else _owner_redirect(environ, start_response)
    if _r is not None:
        return _r
    _r = _serve_site(environ, start_response)
    if _r is not None:
        return _r
    _ensure_started()
    if not _state["ready"] and _state["error"] is None:
        # Bu hosting arka plan islerini istekler arasinda durduruyor olabilir; bu yuzden
        # istegi acik tutup baslatmanin ilerlemesini bekleriz (uzun bir bekleme degil, 25 sn).
        _done.wait(25)
    if _state["ready"]:
        return _wrap(_state["app"](environ, start_response), _state["loop"])
    if _state["error"] is not None:
        msg = "Panel baslatilamadi. onlinekaydet_app/startup-error.log dosyasina bakin."
        start_response("503 Service Unavailable", [("Content-Type", "text/plain; charset=utf-8"), ("Retry-After", "6")])
    else:
        msg = "Panel basliyor (ilk acilis 1-3 dakika surebilir). Birkac dakika sonra sayfayi yenileyin.\n\n--- durum (pid %s) ---\n%s" % (os.getpid(), "\n".join(_mem) or "(henuz kayit yok)")
        start_response("503 Service Unavailable", [("Content-Type", "text/plain; charset=utf-8"), ("Retry-After", "20")])
    return [msg.encode("utf-8")]
