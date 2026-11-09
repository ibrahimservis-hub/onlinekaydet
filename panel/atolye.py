# -*- coding: utf-8 -*-
"""Atölye (cihaz teslim alma) akışı.
Usta evde cihazı onaramayınca servis kaydını atölyeye alır → fiş no + müşteri imzası + yazdırılabilir form (A4 / 80mm-58mm termal / nokta vuruşlu),
yönetici panelinde ayrıntılı görünür, ustanın ekranında 'Atölyedeki cihazlarım' listelenir.
Servis kaydının `status` alanına DOKUNULMAZ; ek `workshop` alt belgesi yazılır (mevcut panel/muhasebe akışları bozulmaz)."""
import base64
import html as _h
import re
import secrets
from datetime import datetime, timezone, timedelta

from fastapi import Depends, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:
    TR = timezone(timedelta(hours=3))

STATES = {"atolyede": "Atölyede", "hazir": "Hazır — teslim bekliyor", "teslim": "Müşteriye teslim edildi"}
REASONS = ["Parça gerekli (yerinde yapılamıyor)", "Özel ekipman gerekli", "Elektronik kart / ana kart onarımı", "Kapsamlı arıza tespiti gerekli", "Müşteri talebi", "Diğer"]
DEFAULT_TERMS = [
    "Cihaz, arıza tespiti ve onarım amacıyla atölyeye alınmıştır; yukarıda yazılı dış durum ve aksesuarlarla teslim alınmıştır.",
    "Ücretli işlem ve parça değişimi öncesinde tutar müşteriye bildirilir; müşteri onayı olmadan ücretli işlem yapılmaz.",
    "Cihaz hazır olduğunda müşteriye haber verilir; hazır bildirimi sonrasında makul süre içinde teslim alınması gerekir.",
    "Teslimde bu form (veya fiş numarası) ibraz edilir. Kişisel veriler yalnızca servis hizmeti kapsamında işlenir (KVKK).",
]
LOGO = "https://servisplus.net.tr/static/img/servisplus-logo.png"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _fd(s, t=False):
    try:
        d = datetime.fromisoformat((s or "").replace("Z", "+00:00"))
        d = d.astimezone(TR)
        return d.strftime("%d.%m.%Y %H:%M" if t else "%d.%m.%Y")
    except Exception:
        return "-"


def e(s):
    return _h.escape(str(s if s is not None else ""))


def _qr_svg(url, scale=3):
    try:
        import segno
        import io
        buf = io.BytesIO()
        segno.make(url, error="l").save(buf, kind="svg", scale=scale, border=4, xmldecl=False, svgns=True, nl=False, dark="#000", light="#fff")
        svg = buf.getvalue().decode()
        m = re.search(r'width="([0-9.]+)"[^>]*?height="([0-9.]+)"', svg)
        if m and "viewBox" not in svg[:300]:
            svg = svg.replace("<svg ", f'<svg viewBox="0 0 {m.group(1)} {m.group(2)}" preserveAspectRatio="xMidYMid meet" ', 1)
        return svg
    except Exception:
        return ""


def _pub_base(base):
    b = (base or "").rstrip("/")
    try:
        host = b.split("//", 1)[1].split("/")[0].split(":")[0]
    except Exception:
        host = ""
    if host.endswith("servisplus.net.tr"):
        return "https://" + host
    return b or "https://bayi.servisplus.net.tr"


def _view(job, g):
    w = job.get("workshop") or {}
    return {
        "no": w.get("receipt_no", ""), "token": w.get("token", ""), "state": w.get("state", ""), "state_tr": STATES.get(w.get("state"), ""),
        "taken_at": w.get("taken_at"), "taken_by": w.get("taken_by_name", ""), "reason": w.get("reason", ""), "condition": w.get("condition", ""),
        "accessories": w.get("accessories", ""), "damage": w.get("damage", ""), "est": w.get("est_ready", ""), "price": w.get("price_estimate", ""),
        "signature": w.get("signature", ""), "tech_signature": w.get("tech_signature", ""), "photos": w.get("photos", []), "note": w.get("tech_note", ""), "history": w.get("history", []),
        "customer": job.get("customer_name", ""), "phone": job.get("customer_phone", ""), "address": job.get("customer_address", ""),
        "device": " ".join(x for x in [job.get("device_brand_name"), job.get("device_model")] if x) or job.get("device_type", ""), "type": job.get("device_type", ""),
        "serial": job.get("device_serial", ""), "fault": job.get("fault_description", ""), "job_no": job.get("job_number", ""),
        "company": g.get("company_name") or "Servis", "cphone": g.get("company_phone") or "0544 444 4 004", "caddr": g.get("company_address") or "",
        "terms": [t for t in (g.get("workshop_terms") or "").split("\n") if t.strip()] or DEFAULT_TERMS,
    }


def _wrap(s, n):
    out = []
    for para in str(s or "").split("\n"):
        line = ""
        for word in para.split(" "):
            while len(word) > n:
                if line:
                    out.append(line)
                    line = ""
                out.append(word[:n])
                word = word[n:]
            if len(line) + len(word) + (1 if line else 0) > n:
                out.append(line)
                line = word
            else:
                line = (line + " " + word).strip()
        out.append(line)
    return [x for x in out if x != ""] or [""]


def _lines(v, cols, url):
    """Düz metin düzeni (nokta vuruşlu + termal için)."""
    bar = "=" * cols
    dash = "-" * cols
    L = [v["company"].upper().center(cols), "CIHAZ TESLIM ALMA FORMU".center(cols) if False else "CİHAZ TESLİM ALMA FORMU".center(cols), bar,
         f"Fiş No : {v['no']}", f"Tarih  : {_fd(v['taken_at'], True)}", f"İş No  : {v['job_no']}", dash]

    def kv(k, val):
        pre = f"{k}: "
        ws = _wrap(val or "-", max(10, cols - len(pre)))
        L.append(pre + ws[0])
        for x in ws[1:]:
            L.append(" " * len(pre) + x)
    kv("Müşteri", v["customer"])
    kv("Telefon", v["phone"])
    if v["address"]:
        kv("Adres", v["address"])
    L.append(dash)
    kv("Cihaz", v["device"])
    if v["serial"]:
        kv("Seri No", v["serial"])
    kv("Arıza", v["fault"])
    kv("Alınma nedeni", v["reason"])
    kv("Aksesuar", v["accessories"] or "Yok")
    kv("Cihaz durumu", (v["condition"] + (" / " + v["damage"] if v["damage"] else "")).strip(" /") or "Belirtilmedi")
    if v["est"]:
        kv("Tahmini teslim", v["est"])
    if v["price"]:
        kv("Ön fiyat", f"{v['price']} TL (bilgi amaçlı)")
    L.append(dash)
    for i, t in enumerate(v["terms"], 1):
        ws = _wrap(f"{i}) {t}", cols)
        L.extend(ws)
    L.append(dash)
    L += ["", "Müşteri imzası: ____________________", "", f"Teslim alan: {v['taken_by']}", "", "Durum takibi için QR / adres:", url, "", f"{v['company']}  Tel: {v['cphone']}"]
    return L


def _tr_ascii(s):
    return s.translate(str.maketrans("ğĞıİşŞçÇöÖüÜ", "gGiIsScCoOuU"))


def _escpos(v, w, cp, url):
    cols = 32 if w == 58 else 48
    out = bytearray(b"\x1b@")
    enc = (lambda s: _tr_ascii(s).encode("ascii", "replace")) if cp == "ascii" else (lambda s: s.encode("cp857", "replace"))
    if cp != "ascii":
        out += b"\x1bt\x0d"                       # kod sayfası: PC857 (Türkçe)
    out += b"\x1ba\x01\x1d!\x11" + enc(v["company"].upper()) + b"\n\x1d!\x00" + enc("CİHAZ TESLİM ALMA FORMU") + b"\n\x1ba\x00"
    body = _lines(v, cols, url)[3:-3]
    for ln in body:
        out += enc(ln) + b"\n"
    out += b"\n\x1ba\x01"
    data = url.encode()
    k = len(data) + 3
    out += b"\x1d(k\x04\x001A2\x00\x1d(k\x03\x001C\x05\x1d(k\x03\x001E1" + b"\x1d(k" + bytes([k & 255, k >> 8]) + b"1P0" + data
    out += b"\x1d(k\x03\x001Q0\n" + enc(v["company"] + "  Tel: " + v["cphone"]) + b"\n\n\n\n\x1dV\x42\x00"
    return bytes(out)


_CSS_COMMON = "*{box-sizing:border-box}body{margin:0;font-family:Inter,'Segoe UI',Arial,sans-serif;color:#111}.bar{position:sticky;top:0;background:#0a1f44;color:#fff;padding:10px 14px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;z-index:9}.bar button,.bar a{background:#f27a1a;color:#fff;border:0;border-radius:8px;padding:9px 13px;font:700 14px Inter,Arial,sans-serif;text-decoration:none;cursor:pointer}.bar a.o,.bar button.o{background:rgba(255,255,255,.16)}.bar b{margin-right:auto}.msg{padding:8px 14px;background:#fff7ed;color:#9a3412;font-size:13px}@media print{.bar,.msg{display:none!important}}"


def _bar(token, fmt, base):
    items = [("a4", "A4"), ("t80", "Termal 80mm"), ("t58", "Termal 58mm"), ("nokta", "Nokta vuruşlu")]
    sw = "".join(f'<a class="o" href="{base}/atolye/{e(token)}?fmt={k}">{n}</a>' for k, n in items if k != fmt)
    return sw


def render_page(job, g, fmt, base, auto=False):
    v = _view(job, g)
    if not v["token"]:
        raise HTTPException(404, "Kayıt yok")
    base = _pub_base(base)
    url = f"{base}/atolye/{v['token']}?fmt=durum"
    if fmt == "durum":
        return _status_html(v)
    sw = _bar(v["token"], fmt, base)
    pr = '<button onclick="window.print()">🖨 Yazdır / PDF olarak kaydet</button>'
    if fmt == "a4":
        qr = _qr_svg(url, 4) or f'<div id="qrf" data-u="{e(url)}"></div>'
        sig = f'<img src="{e(v["signature"])}" style="max-height:70px;max-width:100%">' if v["signature"] else ""
        sig2 = f'<img src="{e(v["tech_signature"])}" style="max-height:70px;max-width:100%">' if v["tech_signature"] else ""
        phs = "".join(f'<img src="{e(x)}" alt="">' for x in (v["photos"] or [])[:4])
        phb = f'<div class="ph"><small>Teslim alma anındaki cihaz fotoğrafları</small><div>{phs}</div></div>' if phs else ""
        rows = [("Müşteri", v["customer"]), ("Telefon", v["phone"]), ("Adres", v["address"]), ("Cihaz", v["device"] + (f' ({v["type"]})' if v["type"] and v["device"] != v["type"] else "")), ("Seri no", v["serial"]),
                ("Arıza (müşteri beyanı)", v["fault"]), ("Atölyeye alınma nedeni", v["reason"]), ("Teslim alınan aksesuarlar", v["accessories"] or "Yok"),
                ("Cihazın fiziksel durumu", (v["condition"] + (" — " + v["damage"] if v["damage"] else "")).strip(" —") or "Belirtilmedi"), ("Tahmini teslim", v["est"]), ("Ön fiyat bilgisi", (v["price"] + " TL (bilgi amaçlıdır, onay alınmadan işlem yapılmaz)") if v["price"] else "")]
        tr = "".join(f"<tr><th>{e(k)}</th><td>{e(x) or '—'}</td></tr>" for k, x in rows if x or k in ("Müşteri", "Cihaz", "Arıza (müşteri beyanı)"))
        terms = "".join(f"<li>{e(t)}</li>" for t in v["terms"])
        page = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cihaz Teslim Alma Formu {e(v['no'])}</title>
<style>{_CSS_COMMON}@page{{size:A4;margin:12mm}}.sheet{{width:210mm;max-width:100%;margin:0 auto;padding:14mm 14mm 10mm;background:#fff}}
.hd{{display:flex;align-items:center;justify-content:space-between;border-bottom:3px solid #0a1f44;padding-bottom:8px}}.hd img{{height:46px}}.hd .r{{text-align:right;font-size:12px;color:#444}}
h1{{font-size:20px;margin:12px 0 2px;color:#0a1f44;letter-spacing:.3px}}.no{{display:flex;gap:18px;font-size:13px;margin-bottom:8px}}.no b{{font-size:15px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}th{{width:34%;text-align:left;background:#eef2f9;padding:6px 8px;border:1px solid #cfd8e8}}td{{padding:6px 8px;border:1px solid #cfd8e8}}
.top{{display:flex;gap:14px;align-items:flex-start;margin-top:10px}}.top .q{{width:128px;text-align:center;font-size:10.5px;color:#333;line-height:1.3}}.top .q svg,.top .q img{{width:124px;height:124px;display:block;margin:0 auto 4px;shape-rendering:crispEdges}}.ph{{margin-top:10px}}.ph small{{color:#555;font-size:11px}}.ph div{{display:flex;gap:6px;margin-top:3px}}.ph img{{height:74px;width:auto;max-width:24%;object-fit:cover;border:1px solid #cfd8e8;border-radius:4px}}
ol{{font-size:11.5px;line-height:1.45;padding-left:18px;margin:6px 0}}.sg{{display:flex;gap:24px;margin-top:14px}}.sg div{{flex:1;border:1px solid #9aa8c2;border-radius:6px;height:92px;padding:6px;font-size:12px;position:relative}}.sg small{{position:absolute;bottom:4px;left:6px;color:#555}}
.ft{{margin-top:8px;font-size:11px;color:#555;text-align:center}}@media screen{{body{{background:#e8ecf3}}.sheet{{margin:12px auto;box-shadow:0 4px 20px rgba(0,0,0,.12)}}}}</style></head><body>
<div class="bar"><b>Cihaz Teslim Alma Formu — {e(v['no'])}</b>{pr}<button id="pdf">⬇ PDF indir</button>{sw}</div>
<div class="sheet" id="sheet"><div class="hd"><img src="{LOGO}" alt="" crossorigin="anonymous" onerror="this.style.display='none'"><div class="r"><b>{e(v['company'])}</b><br>Tel: {e(v['cphone'])}<br>{e(v['caddr'])}</div></div>
<h1>CİHAZ TESLİM ALMA FORMU</h1><div class="no"><span>Fiş No: <b>{e(v['no'])}</b></span><span>Tarih: <b>{_fd(v['taken_at'], True)}</b></span><span>İş No: <b>{e(v['job_no'])}</b></span></div>
<div class="top"><div style="flex:1"><table>{tr}</table></div><div class="q">{qr}<b>Cihazınızı takip edin</b><br>Telefon kameranızla okutun: cihazınızın durumu, süreç ve iletişim bilgileri açılır.</div></div>
<div class="sg"><div>Müşteri (teslim eden) — ad soyad / imza<br>{sig}<small>{e(v['customer'])}</small></div><div>Teslim alan usta — ad soyad / imza<br>{sig2}<small>{e(v['taken_by'])}</small></div></div>{phb}
<ol style="margin-top:12px">{terms}</ol><div class="ft">Bu form cihazın atölyeye alındığını gösterir. Kayıp halinde fiş numarasını (<b>{e(v['no'])}</b>) bildiriniz.</div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js"></script><script>(function(){{var h=document.getElementById('qrf');if(!h)return;function go(){{try{{var q=qrcode(0,'L');q.addData(h.getAttribute('data-u'));q.make();h.innerHTML=q.createSvgTag({{cellSize:4,margin:4,scalable:true}});}}catch(x){{h.textContent=h.getAttribute('data-u')}}}}if(window.qrcode)go();else window.addEventListener('load',function(){{window.qrcode?go():(h.textContent=h.getAttribute('data-u'))}});}})();</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js" defer></script><script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js" defer></script>
<script>document.getElementById('pdf').onclick=function(){{var b=this;if(!window.html2canvas||!window.jspdf){{alert('PDF kütüphanesi yüklenemedi. "Yazdır / PDF olarak kaydet" düğmesini kullanın.');return}}b.textContent='Hazırlanıyor…';
html2canvas(document.getElementById('sheet'),{{scale:2,useCORS:true,backgroundColor:'#fff'}}).then(function(c){{var P=new window.jspdf.jsPDF('p','mm','a4'),w=210,h=c.height*w/c.width;if(h>297){{w=w*297/h;h=297}}P.addImage(c.toDataURL('image/jpeg',.92),'JPEG',(210-w)/2,0,w,h);P.save('atolye-formu-{e(v['no'])}.pdf');b.textContent='⬇ PDF indir'}}).catch(function(){{b.textContent='⬇ PDF indir';alert('PDF oluşturulamadı; Yazdır düğmesinden PDF olarak kaydedin.')}})}};
{'window.addEventListener("load",function(){setTimeout(function(){window.print()},500)});' if auto else ''}</script></body></html>"""
        return HTMLResponse(page, headers={"Cache-Control": "no-store"})
    if fmt in ("t80", "t58"):
        w = 80 if fmt == "t80" else 58
        cols = 48 if w == 80 else 32
        txt = "\n".join(_lines(v, cols, url))
        page = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fiş {e(v['no'])}</title>
<style>{_CSS_COMMON}@page{{size:{w}mm auto;margin:2mm}}pre{{font:bold {9.4 if w == 80 else 10.4}px/1.3 'Courier New',monospace;white-space:pre;overflow:hidden;margin:0;padding:6px;width:{w - 4}mm;max-width:100%;margin:0 auto}}.qr{{text-align:center}}.qr svg{{width:30mm;height:30mm}}
@media screen{{body{{background:#e8ecf3}}.paper{{width:{w}mm;max-width:100%;margin:10px auto;background:#fff;padding:3mm;box-shadow:0 2px 10px rgba(0,0,0,.15)}}}}</style></head><body>
<div class="bar"><b>Termal {w} mm — {e(v['no'])}</b>{pr}<button id="bt">🔵 Bluetooth yazıcıya gönder</button><a id="rb" href="#">RawBT ile yazdır</a>
<label style="font-size:12px"><input type="checkbox" id="asc"> Türkçe harfsiz (ASCII)</label>{sw}</div><div class="msg" id="m">Telefondan Bluetooth termal yazıcı: Chrome (Android) ile "Bluetooth yazıcıya gönder" veya RawBT uygulaması. Olmazsa "Yazdır" ile yazıcı uygulamanızı seçin.</div>
<div class="paper"><pre>{e(txt)}</pre><div class="qr">{_qr_svg(url, 2)}</div></div>
<script>var T={e(v['token'])!r},W={w};function esc(a){{return new Promise(function(r,j){{var c=document.getElementById('asc').checked?'ascii':'857';fetch('/api/public/atolye/'+T+'/escpos?w='+W+'&cp='+c).then(function(x){{return x.json()}}).then(r,j)}})}}
function b64(s){{var b=atob(s),u=new Uint8Array(b.length);for(var i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u}}
document.getElementById('rb').onclick=function(ev){{ev.preventDefault();esc().then(function(d){{location.href='rawbt:base64,'+d.b64}})}};
document.getElementById('bt').onclick=function(){{var m=document.getElementById('m');if(!navigator.bluetooth){{m.textContent='Bu tarayıcı Bluetooth desteklemiyor (Android Chrome gerekir). RawBT veya Yazdır düğmesini kullanın.';return}}
esc().then(function(d){{var bytes=b64(d.b64);return navigator.bluetooth.requestDevice({{acceptAllDevices:true,optionalServices:['000018f0-0000-1000-8000-00805f9b34fb','0000ff00-0000-1000-8000-00805f9b34fb','e7810a71-73ae-499d-8c15-faa9aef0c3f2','49535343-fe7d-4ae5-8fa9-9fafd205e455','0000ae30-0000-1000-8000-00805f9b34fb','0000fee7-0000-1000-8000-00805f9b34fb']}}).then(function(dev){{m.textContent='Bağlanılıyor: '+dev.name;return dev.gatt.connect()}}).then(function(srv){{return srv.getPrimaryServices()}}).then(function(svcs){{var chain=Promise.reject(),found=null;
 return Promise.all(svcs.map(function(s){{return s.getCharacteristics().then(function(cs){{cs.forEach(function(c){{if(!found&&(c.properties.write||c.properties.writeWithoutResponse))found=c}})}})}})).then(function(){{if(!found)throw new Error('Yazılabilir kanal bulunamadı');return found}})}}).then(function(ch){{var i=0;function nx(){{if(i>=bytes.length){{m.textContent='Gönderildi ✔';return}}var part=bytes.slice(i,i+120);i+=120;return(ch.properties.writeWithoutResponse?ch.writeValueWithoutResponse(part):ch.writeValue(part)).then(function(){{return new Promise(function(r){{setTimeout(r,25)}})}}).then(nx)}}return nx()}})}}).catch(function(x){{m.textContent='Bluetooth yazdırma olmadı: '+(x&&x.message||x)+' — RawBT veya Yazdır düğmesini deneyin.'}})}};
{'window.addEventListener("load",function(){setTimeout(function(){window.print()},500)});' if auto else ''}</script></body></html>"""
        return HTMLResponse(page, headers={"Cache-Control": "no-store"})
    # nokta vuruşlu: yalnızca metin, 80 sütun, siyah-beyaz
    txt = "\n".join(_lines(v, 80, url))
    page = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nokta vuruşlu {e(v['no'])}</title>
<style>{_CSS_COMMON}@page{{size:A4;margin:10mm 8mm}}pre{{font:12pt/1.2 'Courier New',Courier,monospace;color:#000;white-space:pre;margin:0;padding:10px}}@media screen{{body{{background:#fff}}}}</style></head><body>
<div class="bar"><b>Nokta vuruşlu yazıcı — {e(v['no'])}</b>{pr}<a class="o" href="/api/public/atolye/{e(v['token'])}/text?cols=80" download="atolye-{e(v['no'])}.txt">Metin dosyası (.txt)</a>{sw}</div>
<div class="msg">Yazıcı penceresinde: kâğıt boyutunu/sürekli formu seçin, "Üst bilgi/alt bilgi"yi kapatın, ölçek %100. Düz metin olduğu için 24 iğneli nokta vuruşlu yazıcılarda hızlı (Taslak/Draft) basar.</div>
<pre>{e(txt)}</pre><script>{'window.addEventListener("load",function(){setTimeout(function(){window.print()},400)});' if auto else ''}</script></body></html>"""
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})


def _mask(n):
    ps = str(n or "").split()
    return " ".join([ps[0]] + [x[0] + "***" for x in ps[1:]]) if ps else ""


def _status_html(v):
    st = v["state"]
    order = ["atolyede", "hazir", "teslim"]
    idx = order.index(st) if st in order else 0
    info = {
        "atolyede": ("Cihazınız atölyemizde", "Cihazınız teslim alındı; uzman ekibimiz arıza tespiti ve onarım çalışmasını yürütüyor. Ücretli işlem veya parça değişimi gerekirse önce size bilgi verilir, onayınız olmadan işlem yapılmaz.", "#b45309"),
        "hazir": ("Cihazınız hazır", "Onarım tamamlandı. Cihazınızı bu formla (veya fiş numarasıyla) teslim alabilirsiniz. Gelmeden önce bizi arayarak uygun saati öğrenebilirsiniz.", "#0f766e"),
        "teslim": ("Cihazınız teslim edildi", "Cihazınız size teslim edilmiştir. Bizi tercih ettiğiniz için teşekkür ederiz. Cihazla ilgili bir sorun yaşarsanız bu fiş numarasıyla bize ulaşabilirsiniz.", "#166534"),
    }
    title, text, col = info.get(st, info["atolyede"])
    labels = [("Teslim alındı", "Cihazınız atölyeye alındı"), ("Onarım tamamlandı", "Cihazınız teslime hazır"), ("Teslim edildi", "Cihazınız size teslim edildi")]
    dots = ""
    for k, (a, b) in enumerate(labels):
        done = k <= idx
        dots += (f'<div style="display:flex;gap:12px;align-items:flex-start;margin-bottom:12px"><div style="width:26px;height:26px;border-radius:50%;background:{col if done else "#e2e8f0"};color:#fff;'
                 f'display:flex;align-items:center;justify-content:center;font-weight:800;flex:none">{"✓" if done else k + 1}</div><div><b style="color:{"#0f172a" if done else "#94a3b8"}">{a}</b><br><span style="font-size:13px;color:#64748b">{b}</span></div></div>')
    hist = "".join(f'<div style="padding:7px 0;border-top:1px solid #eef2f6;font-size:14px"><b>{_fd(x.get("at"), True)}</b> — {e(STATES.get(x.get("state"), x.get("state")))}{(": " + e(x.get("note"))) if x.get("note") and x.get("public") else ""}</div>' for x in reversed(v["history"]))
    ph = "".join(f'<img src="{e(x)}" alt="" style="width:31%;height:80px;object-fit:cover;border-radius:8px;border:1px solid #e2e8f0">' for x in (v["photos"] or [])[:6])
    rows = [("Fiş numarası", v["no"]), ("Teslim alındığı tarih", _fd(v["taken_at"], True)), ("Cihaz", v["device"]), ("Müşteri", _mask(v["customer"])), ("Atölyeye alınma nedeni", v["reason"]),
            ("Teslim alınan aksesuarlar", v["accessories"] or "Yok"), ("Tahmini teslim", v["est"]), ("Ön fiyat bilgisi", (v["price"] + " TL — bilgi amaçlıdır, onayınız olmadan ücretli işlem yapılmaz") if v["price"] else "")]
    tbl = "".join(f'<div style="display:flex;gap:10px;padding:8px 0;border-top:1px solid #eef2f6"><div style="width:42%;color:#64748b;font-size:14px">{a}</div><div style="flex:1;font-size:15px"><b>{e(b)}</b></div></div>' for a, b in rows if b)
    tel = re.sub(r"[^0-9+]", "", v["cphone"])
    wa = re.sub(r"[^0-9]", "", v["cphone"])
    wa = ("9" + wa if wa.startswith("0") else wa)
    return HTMLResponse(f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Cihaz Durumu — {e(v['no'])}</title>
<style>body{{margin:0;background:#f1f5f9;font:16px/1.5 Inter,Arial,sans-serif;color:#1e293b}}.w{{max-width:520px;margin:0 auto;padding:14px}}.c{{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:16px;margin-bottom:12px}}.b{{display:block;text-align:center;padding:13px;border-radius:12px;font-weight:800;text-decoration:none;margin-top:8px}}h2{{margin:0 0 8px;font-size:17px}}</style></head><body><div class="w">
<div style="display:flex;align-items:center;gap:10px;margin:4px 0 12px"><img src="{LOGO}" alt="" style="height:38px" onerror="this.style.display='none'"><b style="font-size:18px">{e(v['company'])}</b></div>
<div class="c" style="border-color:{col}"><div style="display:inline-block;background:{col};color:#fff;border-radius:20px;padding:5px 14px;font-weight:800;font-size:14px">{e(v['state_tr'])}</div>
<h1 style="margin:10px 0 6px;font-size:22px">{title}</h1><div style="font-size:15px;color:#334155">{text}</div></div>
<div class="c"><h2>Süreç</h2>{dots}</div>
<div class="c"><h2>Cihaz ve teslim bilgileri</h2>{tbl}{('<div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap">' + ph + '</div>') if ph else ''}</div>
{('<div class="c"><h2>Hareketler</h2>' + hist + '</div>') if hist else ''}
<div class="c"><h2>Cihazınızı teslim alırken</h2><div style="font-size:15px">Size verilen formu veya <b>{e(v['no'])}</b> fiş numarasını yanınızda getirin. Teslim alacak kişinin kimlik bilgisi istenebilir.</div></div>
<div class="c"><h2>Bize ulaşın</h2><div style="font-size:15px">{e(v['company'])}{(' — ' + e(v['caddr'])) if v['caddr'] else ''}</div><a class="b" style="background:#0a1f44;color:#fff" href="tel:{tel}">📞 Ara: {e(v['cphone'])}</a><a class="b" style="background:#16a34a;color:#fff" href="https://wa.me/{wa}?text=Fi%C5%9F%20no%3A%20{e(v['no'])}">💬 WhatsApp ile yaz</a></div>
<div style="text-align:center;color:#94a3b8;font-size:12px;margin:8px 0 20px">Bu sayfa cihaz teslim alma fişinize özeldir.</div></div></body></html>""", headers={"Cache-Control": "no-store"})


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]
    import fieldops

    async def _g():
        return await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}

    async def _job(jid, user):
        j = await db.service_jobs.find_one({"id": jid}, {"_id": 0})
        if not j:
            raise HTTPException(404, "Servis kaydı bulunamadı")
        if user.get("role") != "admin" and j.get("assigned_technician_id") != user.get("id"):
            raise HTTPException(403, "Bu kayıt size atanmamış")
        return j

    async def _admins():
        return [u["id"] async for u in db.users.find({"role": "admin"}, {"_id": 0, "id": 1})]

    def _clean_sig(s):
        s = str(s or "")
        if s.startswith("data:image/") and ";base64," in s[:40] and len(s) <= 260_000:
            return s
        return ""

    def _clean_photos(ph):
        out, tot = [], 0
        for x in (ph if isinstance(ph, list) else [])[:6]:
            x = str(x or "")
            if x.startswith("data:image/") and ";base64," in x[:40] and len(x) <= 450_000 and tot + len(x) <= 1_800_000:
                out.append(x)
                tot += len(x)
        return out

    def _summary(j, techs):
        w = j.get("workshop") or {}
        taken = w.get("taken_at")
        days = 0
        try:
            end = datetime.fromisoformat(w["delivered_at"]) if w.get("delivered_at") else datetime.now(timezone.utc)
            days = max(0, (end - datetime.fromisoformat(taken)).days)
        except Exception:
            pass
        return {"id": j["id"], "job_number": j.get("job_number"), "customer": j.get("customer_name"), "phone": j.get("customer_phone"), "address": j.get("customer_address"),
                "device": " ".join(x for x in [j.get("device_brand_name"), j.get("device_model"), j.get("device_type")] if x), "serial": j.get("device_serial"), "fault": (j.get("fault_description") or "")[:200],
                "tech": techs.get(w.get("taken_by_id") or j.get("assigned_technician_id"), w.get("taken_by_name", "")), "tech_id": j.get("assigned_technician_id"), "job_status": j.get("status"),
                "state": w.get("state"), "state_tr": STATES.get(w.get("state"), ""), "receipt_no": w.get("receipt_no"), "token": w.get("token"), "taken_at": taken, "reason": w.get("reason"),
                "condition": w.get("condition"), "accessories": w.get("accessories"), "damage": w.get("damage"), "est_ready": w.get("est_ready"), "price_estimate": w.get("price_estimate"),
                "days": days, "late": bool(w.get("state") == "atolyede" and days >= 7), "ready_at": w.get("ready_at"), "delivered_at": w.get("delivered_at"), "tech_note": w.get("tech_note", ""),
                "has_signature": bool(w.get("signature")), "has_tech_signature": bool(w.get("tech_signature")), "photo_count": len(w.get("photos") or []), "history": w.get("history", [])}

    async def _techs():
        return {u["id"]: u.get("name", "") async for u in db.users.find({"role": "technician"}, {"_id": 0, "id": 1, "name": 1})}

    @api_router.post("/workshop/{jid}/intake")
    async def intake(jid: str, payload: dict, user: dict = Depends(get_current_user)):
        j = await _job(jid, user)
        old = j.get("workshop") or {}
        if user.get("role") != "admin" and j.get("status") != "basladi":
            raise HTTPException(400, "Atölyeye almak için önce müşteride işe başlayın (adımları ilerletin)")
        if old.get("state") in ("atolyede", "hazir"):
            raise HTTPException(400, "Bu cihaz zaten atölyede kayıtlı")
        reason = str(payload.get("reason") or "").strip()[:200]
        if not reason:
            raise HTTPException(422, "Atölyeye alınma nedenini seçin")
        csig, tsig = _clean_sig(payload.get("signature")), _clean_sig(payload.get("tech_signature"))
        if not csig:
            raise HTTPException(422, "Müşteri imzası zorunlu")
        if not tsig:
            raise HTTPException(422, "Teknisyen imzası zorunlu")
        photos = _clean_photos(payload.get("photos"))
        if not photos:
            raise HTTPException(422, "Cihazın en az bir fotoğrafı zorunlu")
        if not payload.get("consent"):
            raise HTTPException(422, "Müşteri onayı (cihazın alınmasını kabul) işaretlenmeli")
        now = datetime.now(TR)
        n = await db.service_jobs.count_documents({"workshop.receipt_no": {"$regex": "^ATL-" + now.strftime("%y%m%d")}})
        rno = f"ATL-{now.strftime('%y%m%d')}-{n + 1:03d}"
        w = {"state": "atolyede", "receipt_no": rno, "token": secrets.token_urlsafe(14), "taken_at": _now(), "taken_by_id": user["id"], "taken_by_name": user.get("name", ""),
             "reason": reason, "condition": str(payload.get("condition") or "")[:500], "accessories": str(payload.get("accessories") or "")[:300], "damage": str(payload.get("damage") or "")[:500],
             "est_ready": str(payload.get("est_ready") or "")[:60], "price_estimate": str(payload.get("price_estimate") or "")[:30], "tech_note": str(payload.get("note") or "")[:500],
             "signature": csig, "tech_signature": tsig, "photos": photos, "history": [{"at": _now(), "state": "atolyede", "by": user.get("name", ""), "note": reason, "public": False}]}
        await db.service_jobs.update_one({"id": jid}, {"$set": {"workshop": w, "updated_at": _now()}})
        await fieldops.push_to(db, await _admins(), "🔧 Cihaz atölyeye alındı", f"{rno} · {j.get('customer_name', '')} · {j.get('device_type', '')} · {user.get('name', '')}", "/admin?ek=atolye")
        return {"ok": True, "receipt_no": rno, "token": w["token"], "print": f"/atolye/{w['token']}?fmt=a4"}

    @api_router.post("/workshop/{jid}/state")
    async def set_state(jid: str, payload: dict, user: dict = Depends(get_current_user)):
        j = await _job(jid, user)
        w = j.get("workshop") or {}
        st = payload.get("state")
        if not w or st not in STATES:
            raise HTTPException(422, "Geçersiz durum")
        note = str(payload.get("note") or "")[:300]
        upd = {"workshop.state": st, "updated_at": _now()}
        if st == "hazir":
            upd["workshop.ready_at"] = _now()
        if st == "teslim":
            upd["workshop.delivered_at"] = _now()
            sig = _clean_sig(payload.get("signature"))
            if sig:
                upd["workshop.delivery_signature"] = sig
        hist = {"at": _now(), "state": st, "by": user.get("name", ""), "note": note, "public": bool(payload.get("public", False))}
        await db.service_jobs.update_one({"id": jid}, {"$set": upd, "$push": {"workshop.history": hist}})
        if st == "hazir":
            await fieldops.push_to(db, await _admins(), "✅ Atölyedeki cihaz hazır", f"{w.get('receipt_no')} · {j.get('customer_name', '')} — müşteriye haber verin", "/admin?ek=atolye")
        return {"ok": True, "state": st}

    @api_router.post("/workshop/{jid}/note")
    async def add_note(jid: str, payload: dict, user: dict = Depends(get_current_user)):
        j = await _job(jid, user)
        if not j.get("workshop"):
            raise HTTPException(404, "Atölye kaydı yok")
        txt = str(payload.get("note") or "").strip()[:300]
        if not txt:
            raise HTTPException(422, "Not boş")
        await db.service_jobs.update_one({"id": jid}, {"$push": {"workshop.history": {"at": _now(), "state": (j["workshop"].get("state")), "by": user.get("name", ""), "note": txt, "public": bool(payload.get("public"))}}})
        return {"ok": True}

    @api_router.get("/workshop")
    async def wlist(state: str = "", user: dict = Depends(get_current_user)):
        q = {"workshop.state": {"$in": [state] if state in STATES else ["atolyede", "hazir"]}}
        if user.get("role") != "admin":
            q["assigned_technician_id"] = user["id"]
        elif state == "teslim":
            q["workshop.delivered_at"] = {"$gte": (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()}
        rows = await db.service_jobs.find(q, {"_id": 0, "photos_before": 0, "photos_after": 0, "signature_url": 0, "tech_signature_url": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.photos": 0, "workshop.delivery_signature": 0}).to_list(2000)
        techs = await _techs()
        out = [_summary(j, techs) for j in rows]
        out.sort(key=lambda r: r.get("taken_at") or "", reverse=True)
        if user.get("role") != "admin":
            for r in out:
                r.pop("history", None)
        return {"rows": out, "counts": {"atolyede": sum(1 for r in out if r["state"] == "atolyede"), "hazir": sum(1 for r in out if r["state"] == "hazir"), "late": sum(1 for r in out if r["late"])}, "reasons": REASONS}

    @api_router.get("/workshop/{jid}")
    async def wget(jid: str, user: dict = Depends(get_current_user)):
        j = await _job(jid, user)
        return {"workshop": _summary(j, await _techs()) if j.get("workshop") else None, "reasons": REASONS, "job": {"id": j["id"], "customer": j.get("customer_name"), "phone": j.get("customer_phone"), "device": " ".join(x for x in [j.get("device_brand_name"), j.get("device_model"), j.get("device_type")] if x), "status": j.get("status")}}

    @api_router.get("/workshop/{jid}/photos")
    async def wphotos(jid: str, user: dict = Depends(get_current_user)):
        j = await _job(jid, user)
        w = j.get("workshop") or {}
        return {"photos": w.get("photos", []), "signature": w.get("signature", ""), "tech_signature": w.get("tech_signature", ""), "delivery_signature": w.get("delivery_signature", "")}

    # ---- belirteçle açılan herkese açık (QR/yazdırma) uçları
    @api_router.get("/public/atolye/{token}/escpos")
    async def pub_escpos(token: str, w: int = 58, cp: str = "857", base: str = ""):
        j = await db.service_jobs.find_one({"workshop.token": token}, {"_id": 0})
        if not j:
            raise HTTPException(404, "Kayıt yok")
        v = _view(j, await _g())
        data = _escpos(v, 80 if w == 80 else 58, "ascii" if cp == "ascii" else "857", f"https://bayi.servisplus.net.tr/atolye/{token}?fmt=durum")
        return {"b64": base64.b64encode(data).decode(), "bytes": len(data)}

    @api_router.get("/public/atolye/{token}/text")
    async def pub_text(token: str, cols: int = 80):
        j = await db.service_jobs.find_one({"workshop.token": token}, {"_id": 0})
        if not j:
            raise HTTPException(404, "Kayıt yok")
        v = _view(j, await _g())
        cols = max(32, min(cols, 96))
        return PlainTextResponse("\n".join(_lines(v, cols, f"https://bayi.servisplus.net.tr/atolye/{token}?fmt=durum")), headers={"Cache-Control": "no-store"})


def page_handler(db):
    async def handler(token: str, fmt: str = "a4", auto: int = 0, request=None):
        j = await db.service_jobs.find_one({"workshop.token": token}, {"_id": 0})
        if not j:
            return HTMLResponse("<meta charset=utf-8><body style='font:16px sans-serif;padding:24px'>Bu bağlantı geçersiz.</body>", status_code=404)
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        base = f"{request.url.scheme}://{request.headers.get('host', request.url.netloc)}" if request else ""
        return render_page(j, g, fmt if fmt in ("a4", "t80", "t58", "nokta", "durum") else "a4", base, bool(auto))
    return handler


async def ensure_indexes(db):
    try:
        await db.service_jobs.create_index("workshop.token", sparse=True)
        await db.service_jobs.create_index("workshop.state", sparse=True)
    except Exception:
        pass
