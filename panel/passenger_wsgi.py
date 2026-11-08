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
    try:
        for chunk in resp:
            yield chunk
    finally:
        close = getattr(resp, "close", None)
        if close:
            close()
        _drain(loop)


def _patch_assets():
    """Panel arayuz paketi baska bir sitenin API adresine gomulu gelirse (bayi.servisplus.net.tr),
    istekleri bu sitenin kendi /api adresine cevirir. Her acilista calisir, tekrar calistirmak zararsizdir."""
    try:
        js = os.path.join(HERE, "public_panel", "static", "js")
        for n in sorted(os.listdir(js)):
            if not (n.startswith("main.") and n.endswith(".js")):
                continue
            p = os.path.join(js, n)
            with open(p, "rb") as fh:
                b = fh.read()
            o = b
            b = b.replace(b'"https://bayi.servisplus.net.tr/api"', b'"/api"')
            b = b.replace(b'"https://bayi.servisplus.net.tr"', b'""')
            if b != o:
                with open(p, "wb") as fh:
                    fh.write(b)
                _progress("arayuz paketi duzeltildi: " + n)
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
        _done.set()
    except BaseException as exc:                 # noqa: BLE001
        _state["error"] = exc
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


def _ensure_started():
    """Passenger uygulamayi once on yukleyip sonra catallayabilir (iplikler cocuga gecmez);
    bu yuzden baslatma, istegi karsilayan surecte ve ilk istekte yapilir."""
    pid = os.getpid()
    if _started["pid"] == pid:
        return
    with _lock:
        if _started["pid"] == pid:
            return
        _started["pid"] = pid
        _state.update(ready=False, error=None, app=None)
        threading.Thread(target=_boot, name="panel-boot", daemon=True).start()


def application(environ, start_response):
    _ensure_started()
    if not _state["ready"] and _state["error"] is None:
        # Bu hosting arka plan islerini istekler arasinda durduruyor olabilir; bu yuzden
        # istegi acik tutup baslatmanin ilerlemesini bekleriz (uzun bir bekleme degil, 25 sn).
        _done.wait(25)
    if _state["ready"]:
        return _wrap(_state["app"](environ, start_response), _state["loop"])
    if _state["error"] is not None:
        msg = "Panel baslatilamadi. onlinekaydet_app/startup-error.log dosyasina bakin."
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
    else:
        msg = "Panel basliyor (ilk acilis 1-3 dakika surebilir). Birkac dakika sonra sayfayi yenileyin.\n\n--- durum (pid %s) ---\n%s" % (os.getpid(), "\n".join(_mem) or "(henuz kayit yok)")
        start_response("503 Service Unavailable", [("Content-Type", "text/plain; charset=utf-8"), ("Retry-After", "20")])
    return [msg.encode("utf-8")]
