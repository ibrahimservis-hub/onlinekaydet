# -*- coding: utf-8 -*-
"""Kurumsal paket modülleri: ödeme linki (iyzico), teklif onay linki, müşteri portalı, arayan numara.

Herkese açık bağlantılar /<sayfa>/<firma_id>~<jeton> biçimindedir; server.py ara katmanı firmayı ön ekten bulur ve ön eki atar.
Modül kapısı (firms.GATE) yalnız oturumlu uçlarda çalışır; herkese açık uçlar paket kontrolünü burada kendisi yapar.
"""
import asyncio
import base64
import hashlib
import hmac
import json
import random
import re
import secrets
import time
from datetime import datetime, timedelta, timezone

import requests
from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

import notify
import tenant

PANEL_URL_DEFAULT = "https://onlinekaydet.com"


def _now():
    return datetime.now(timezone.utc).isoformat()


def pkey(p):
    d = re.sub(r"\D", "", p or "")
    return d[-10:] if len(d) >= 10 else d


def rx(ph):
    """Telefonu boşluk/tire/parantezli kayıtlarla da eşleştirir."""
    return "".join(c + r"\D*" for c in ph) + "$"


def _h(tok):
    return hashlib.sha256(str(tok).encode()).hexdigest()


def _f(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


_RATE = {}


def _limit(key, n, sec):
    now = time.time()
    h = [t for t in _RATE.get(key, []) if now - t < sec]
    if len(h) >= n:
        raise HTTPException(429, "Çok fazla deneme, biraz sonra tekrar deneyin")
    h.append(now)
    _RATE[key] = h


def _ip(request):
    return (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))


_CSS = ("<style>:root{--nv:#0a1f44;--bl:#1155cc;--or:#f27a1a;--ink:#273142;--mu:#6b7280;--ln:#e6e8ec;--bg:#f5f8fd;--ok:#0f9d58}"
        "*{box-sizing:border-box}body{margin:0;background:var(--bg);font:15px/1.5 Inter,system-ui,Segoe UI,Roboto,sans-serif;color:var(--ink)}"
        ".top{background:var(--hd);color:var(--on-hd);padding:14px 16px;font-weight:800;display:flex;align-items:center;gap:10px;border-bottom:3px solid var(--or)}.top i{font-style:normal;width:28px;height:28px;border-radius:var(--rd);background:var(--or);color:var(--on-or);display:grid;place-items:center;font-size:14px}"
        ".w{max-width:520px;margin:0 auto;padding:16px}.cd{background:#fff;border:1px solid var(--ln);border-radius:calc(var(--rd) + 2px);padding:18px;margin-bottom:14px}"
        "h1{font-size:22px;margin:6px 0 4px;color:var(--nv)}h2{font-size:16px;margin:0 0 10px;color:var(--nv)}.mu{color:var(--mu);font-size:14px}"
        ".kv{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px dashed var(--ln)}.kv:last-child{border:0}"
        ".big{font-size:34px;font-weight:800;color:var(--nv);letter-spacing:-1px}.bt{display:block;width:100%;border:0;border-radius:var(--rd);padding:14px;font:700 16px inherit;"
        "background:var(--or);color:var(--on-or);cursor:pointer;margin-top:10px}.bt.g{background:#fff;color:var(--ink);border:1px solid var(--ln)}.bt.ok{background:var(--ok)}"
        ".bt:disabled{opacity:.5}.msg{padding:12px;border-radius:12px;margin-top:10px;font-weight:600}.msg.g{background:#e5f5ec;color:#0b7a44}.msg.r{background:#fde8e8;color:#b42318}"
        "input,textarea{width:100%;padding:12px;border:1px solid var(--ln);border-radius:10px;font:inherit;margin-top:8px}</style>")


import html as _html, json as _json, os as _os, re as _re
_HEX = _re.compile(r"^#[0-9a-fA-F]{6}$")
DEFAULT_BRAND = {"theme": "", "dark": "#0a1f44", "accent": "#f27a1a", "radius": 14}
try:
    THEMES = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "themes.json"), encoding="utf-8"))
except Exception:
    THEMES = []


def _lum(h):
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _mix(h, k):
    """h rengini beyazla karıştır (k = renk payı)."""
    c = [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(255 - (255 - v) * k) for v in c)


def brand_css(b):
    b = {**DEFAULT_BRAND, **(b or {})}
    d, a = b["dark"], b["accent"]
    on_a = "#1b1b1b" if _lum(a) > 0.6 else "#fff"
    on_d = "#1b1b1b" if _lum(d) > 0.6 else "#fff"
    # düz mavi yerine temanın vurgusu; koyu temada başlık metni açık kalmasın diye başlıklar --nv (koyu) kullanır
    ink_h = d if _lum(d) < 0.45 else "#1f2937"
    r = max(4, min(24, int(b.get("radius") or 14)))
    return ("<style>:root{--nv:" + ink_h + ";--hd:" + d + ";--on-hd:" + on_d + ";--or:" + a + ";--on-or:" + on_a + ";--bl:" + a + ";--bg:" + _mix(a, 0.07) + ";--rd:" + str(r) + "px}</style>")


def _clean_brand(p):
    out = {"theme": str(p.get("theme") or "")[:40]}
    for k in ("dark", "accent"):
        v = str(p.get(k) or DEFAULT_BRAND[k])
        if not _HEX.match(v):
            raise HTTPException(422, "Renk #rrggbb biçiminde olmalı")
        out[k] = v.lower()
    try:
        out["radius"] = max(4, min(24, int(p.get("radius", 14))))
    except Exception:
        raise HTTPException(422, "Köşe değeri geçersiz")
    return out


def _page(title, body_js, brand=None, firm=None):
    return ('<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex,nofollow"><title>' + title + '</title>' + _CSS + brand_css(brand) + '</head><body><div class="top"><i id="mk">' + _html.escape((firm or 'O')[:1].upper()) + '</i><span id="fn">' + _html.escape(firm or 'OnlineKaydet') + '</span></div>'
            '<div class="w" id="a"><div class="cd mu">Yükleniyor…</div></div><script>'
            "var _fn=document.getElementById('fn');new MutationObserver(function(){document.getElementById('mk').textContent=(_fn.textContent||'O').trim().charAt(0).toUpperCase()}).observe(_fn,{childList:true,characterData:true,subtree:true});var T=location.pathname.split('/').filter(Boolean).pop(),A=document.getElementById('a');"
            "function e(s){return String(s==null?'':s).replace(/[&<>\"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]})}"
            "function tl(n){return Number(n||0).toLocaleString('tr-TR',{minimumFractionDigits:2,maximumFractionDigits:2})+' ₺'}"
            "function J(u,o){return fetch(u,o).then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok)throw new Error(j.detail||'Hata');return j})})}"
            + body_js + '</script></body></html>')


_PAY_JS = r"""
function load(){J('/api/public/pay/'+T).then(function(d){document.getElementById('fn').textContent=d.firm||'OnlineKaydet';
 var h='<div class="cd"><h1>Servis ödemesi</h1><div class="mu">'+e(d.firm)+'</div><div class="kv"><span>Servis</span><b>'+e(d.job_number)+'</b></div><div class="kv"><span>Cihaz</span><b>'+e(d.device||'-')+'</b></div></div>';
 if(d.status==='paid'){h+='<div class="cd"><div class="msg g">✔ Ödemeniz alındı. Teşekkür ederiz.</div></div>'}
 else{h+='<div class="cd"><div class="mu">Ödenecek tutar</div><div class="big">'+tl(d.amount)+'</div>'+(d.can_pay?'<button class="bt" id="pb">Kartla öde</button>':'<div class="msg r">Online ödeme bu firma için şu an açık değil. Lütfen firmayla iletişime geçin.</div>')+'<div id="m"></div></div>'}
 A.innerHTML=h;var b=document.getElementById('pb');if(b)b.onclick=function(){b.disabled=true;J('/api/public/pay/'+T+'/init',{method:'POST'}).then(function(j){location.href=j.url}).catch(function(x){document.getElementById('m').innerHTML='<div class="msg r">'+e(x.message)+'</div>';b.disabled=false})}
}).catch(function(x){A.innerHTML='<div class="cd"><div class="msg r">'+e(x.message)+'</div></div>'})}
load();"""

_QUOTE_JS = r"""
function load(){J('/api/public/quote/'+T).then(function(d){document.getElementById('fn').textContent=d.firm||'OnlineKaydet';
 var h='<div class="cd"><h1>Fiyat teklifi</h1><div class="mu">'+e(d.firm)+' · '+e(d.quote_number)+'</div><div class="kv"><span>Cihaz</span><b>'+e(d.device||'-')+'</b></div><div class="kv"><span>Arıza</span><b>'+e(d.fault||'-')+'</b></div></div>';
 h+='<div class="cd"><h2>Kalemler</h2>'+d.lines.map(function(l){return '<div class="kv"><span>'+e(l.name)+'</span><b>'+tl(l.total)+'</b></div>'}).join('')+'<div class="kv"><span><b>Toplam</b></span><span class="big" style="font-size:24px">'+tl(d.total)+'</span></div></div>';
 if(d.decision){h+='<div class="cd"><div class="msg '+(d.decision==='onaylandi'?'g':'r')+'">'+(d.decision==='onaylandi'?'✔ Teklifi onayladınız.':'Teklifi reddettiniz.')+'</div></div>'}
 else{h+='<div class="cd"><textarea id="nt" rows="2" placeholder="Not (isteğe bağlı)"></textarea><button class="bt ok" id="ok">Teklifi onaylıyorum</button><button class="bt g" id="no">Reddet</button><div id="m"></div></div>'}
 A.innerHTML=h;function go(k){J('/api/public/quote/'+T+'/decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({decision:k,note:document.getElementById('nt').value})}).then(load).catch(function(x){document.getElementById('m').innerHTML='<div class="msg r">'+e(x.message)+'</div>'})}
 var a=document.getElementById('ok'),b=document.getElementById('no');if(a){a.onclick=function(){go('onay')};b.onclick=function(){go('red')}}
}).catch(function(x){A.innerHTML='<div class="cd"><div class="msg r">'+e(x.message)+'</div></div>'})}
load();"""

_PORTAL_JS = r"""
var S=sessionStorage.getItem('pt_'+T)||'';
function login(){A.innerHTML='<div class="cd"><h1>Müşteri portalı</h1><div class="mu">Telefon numaranıza gönderilen kodla giriş yapın.</div><input id="ph" inputmode="tel" placeholder="05xx xxx xx xx"><button class="bt" id="gb">Kod gönder</button><div id="m"></div></div>';
 document.getElementById('gb').onclick=function(){J('/api/public/portal/'+T+'/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:document.getElementById('ph').value})}).then(function(){var ph=document.getElementById('ph').value;
  A.innerHTML='<div class="cd"><h1>Kodu girin</h1><div class="mu">SMS ile gelen 6 haneli kod</div><input id="cd" inputmode="numeric" maxlength="6"><button class="bt" id="vb">Giriş yap</button><div id="m"></div></div>';
  document.getElementById('vb').onclick=function(){J('/api/public/portal/'+T+'/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:ph,code:document.getElementById('cd').value})}).then(function(j){S=j.session;sessionStorage.setItem('pt_'+T,S);home()}).catch(function(x){document.getElementById('m').innerHTML='<div class="msg r">'+e(x.message)+'</div>'})}
 }).catch(function(x){document.getElementById('m').innerHTML='<div class="msg r">'+e(x.message)+'</div>'})}}
var ST={yeni:'Yeni',atandi:'Atandı',yolda:'Yolda',basladi:'Başladı',tamamlandi:'Tamamlandı',faturalandi:'Faturalandı',iptal:'İptal'};
function home(){J('/api/public/portal/'+T+'/me',{headers:{'X-Portal':S}}).then(function(d){document.getElementById('fn').textContent=d.firm||'OnlineKaydet';
 var h='<div class="cd"><h1>Merhaba '+e(d.name||'')+'</h1><div class="mu">Servis geçmişiniz ve belgeleriniz</div></div>';
 h+=d.jobs.length?d.jobs.map(function(j){return '<div class="cd"><div class="kv"><b>'+e(j.job_number)+'</b><span>'+e(ST[j.status]||j.status)+'</span></div><div class="kv"><span>Cihaz</span><span>'+e(j.device||'-')+'</span></div><div class="kv"><span>Tutar</span><b>'+tl(j.total)+'</b></div>'+(j.track_url?'<a href="'+e(j.track_url)+'">Servisi takip et</a>':'')+(j.pay_url?' · <a href="'+e(j.pay_url)+'">Ödeme yap</a>':'')+'</div>'}).join(''):'<div class="cd mu">Kayıtlı servisiniz bulunmuyor.</div>';
 h+=(d.quotes.length?'<div class="cd"><h2>Bekleyen teklifler</h2>'+d.quotes.map(function(q){return '<div class="kv"><span>'+e(q.quote_number)+'</span><a href="'+e(q.url)+'">'+tl(q.total)+' · İncele</a></div>'}).join('')+'</div>':'');
 h+='<div class="cd"><h2>Yeni servis talebi</h2><textarea id="ft" rows="3" placeholder="Arızayı kısaca yazın"></textarea><button class="bt" id="rb">Talep gönder</button><div id="m"></div></div>';
 A.innerHTML=h;document.getElementById('rb').onclick=function(){J('/api/public/portal/'+T+'/request',{method:'POST',headers:{'Content-Type':'application/json','X-Portal':S},body:JSON.stringify({fault:document.getElementById('ft').value})}).then(function(){document.getElementById('m').innerHTML='<div class="msg g">✔ Talebiniz alındı. Sizi arayacağız.</div>'}).catch(function(x){document.getElementById('m').innerHTML='<div class="msg r">'+e(x.message)+'</div>'})}
}).catch(function(){sessionStorage.removeItem('pt_'+T);S='';login()})}
S?home():login();"""


_TOOLS_JS = r"""
var TK=localStorage.getItem('token')||'';
function C(u,o){o=o||{};o.headers=Object.assign({'Authorization':'Bearer '+TK,'Content-Type':'application/json'},o.headers||{});return J(u,o)}
var TAB=location.hash.slice(1)||'odeme';
function nav(){return '<div class="cd" style="display:flex;gap:8px;flex-wrap:wrap">'+[['odeme','Ödeme linki'],['teklif','Teklifler'],['efatura','E-arşiv'],['arayan','Arayan no'],['portal','Portal'],['marka','Marka']].map(function(t){return '<a href="#'+t[0]+'" onclick="TAB=\''+t[0]+'\';setTimeout(go,0)" style="padding:8px 14px;border-radius:20px;border:1px solid var(--ln);text-decoration:none;font-weight:700;color:'+(TAB===t[0]?'#fff':'var(--nv)')+';background:'+(TAB===t[0]?'var(--nv)':'#fff')+'">'+t[1]+'</a>'}).join('')+'</div>'}
function fail(x){A.innerHTML=nav()+'<div class="cd"><div class="msg r">'+e(x.message==='Unauthorized'?'Oturum yok. Önce panele giriş yapın.':x.message)+'</div></div>'}
function copy(u){try{navigator.clipboard.writeText(u)}catch(_){}prompt&&0}
function row(k,v){return '<div class="kv"><span>'+k+'</span><span>'+v+'</span></div>'}
function go(){if(!TK){return fail({message:'Oturum yok. Önce panele giriş yapın.'})}
 if(TAB==='odeme')C('/api/jobs').then(function(js){js=js.filter(function(j){var p=j.payment||{};return Number(j.total_amount||0)>Number(p.paid||0)}).slice(0,40);
  A.innerHTML=nav()+'<div class="cd"><h2>Ödeme bekleyen servisler</h2>'+(js.length?js.map(function(j){var d=Number(j.total_amount||0)-Number((j.payment||{}).paid||0);return '<div class="kv"><span><b>'+e(j.job_number)+'</b> · '+e(j.customer_name)+'<br><span class="mu">Kalan '+tl(d)+'</span></span><span><button class="bt" style="padding:8px 12px;font-size:14px;margin:0" onclick="mk(\''+j.id+'\')">Link + SMS</button></span></div>'}).join(''):'<div class="mu">Ödeme bekleyen servis yok.</div>')+'<div id="m"></div></div>'}).catch(fail);
 if(TAB==='teklif')C('/api/quotes').then(function(qs){qs=qs.slice(0,40);A.innerHTML=nav()+'<div class="cd"><h2>Teklifler</h2>'+(qs.length?qs.map(function(q){return '<div class="kv"><span><b>'+e(q.quote_number)+'</b> · '+e(q.customer_name)+'<br><span class="mu">'+tl(q.target_total)+' · '+e(q.customer_decision||q.status)+'</span></span><span><button class="bt" style="padding:8px 12px;font-size:14px;margin:0" onclick="sq(\''+q.id+'\')">Link + SMS</button></span></div>'}).join(''):'<div class="mu">Teklif yok.</div>')+'<div id="m"></div></div>'}).catch(fail);
 if(TAB==='efatura')C('/api/jobs').then(function(js){js=js.filter(function(j){return Number(j.total_amount||0)>0}).slice(0,40);A.innerHTML=nav()+'<div class="cd"><h2>E-arşiv fatura</h2><div class="mu">Entegratör adresi Muhasebe → KDV & Fatura → Ayarlar bölümünden girilir.</div><button class="bt g" onclick="et()">Bağlantıyı test et</button><div id="m"></div></div><div class="cd"><h2>Servislerden fatura kes</h2>'+js.map(function(j){return '<div class="kv"><span><b>'+e(j.job_number)+'</b> · '+e(j.customer_name)+'<br><span class="mu">'+tl(j.total_amount)+(j.invoice_number?' · '+e(j.invoice_number):'')+'</span></span><span><button class="bt" style="padding:8px 12px;font-size:14px;margin:0" onclick="ei(\''+j.id+'\')">Kes ve gönder</button></span></div>'}).join('')+'</div>'}).catch(fail);
 if(TAB==='arayan')A.innerHTML=nav()+'<div class="cd"><h2>Arayan numara</h2><input id="cp" inputmode="tel" placeholder="Telefon numarası"><button class="bt" onclick="cl()">Sorgula</button><div id="m"></div></div>';
 if(TAB==='marka')C('/api/brand').then(function(d){var b=d.brand,th=d.themes;
  A.innerHTML=nav()+'<div class="cd"><h2>Müşteri sayfalarının görünümü</h2><div class="mu">Ödeme, teklif ve portal sayfaları bu renklerle açılır. Sitenizin temasını seçin ya da renkleri kendiniz verin.</div>'+
  '<div id="sw" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:8px;margin-top:12px">'+th.map(function(t){return '<button type="button" data-s="'+t.slug+'" style="border:2px solid '+(b.theme===t.slug?'var(--or)':'var(--ln)')+';background:#fff;border-radius:10px;padding:6px;cursor:pointer;font:600 11px inherit;text-align:left"><span style="display:flex;height:22px;border-radius:6px;overflow:hidden;margin-bottom:5px"><i style="flex:2;background:'+t.dark+'"></i><i style="flex:1;background:'+t.accent+'"></i></span>'+e(t.slug.replace(/^\d+-/,''))+'</button>'}).join('')+'</div>'+
  '<div class="kv"><span>Koyu renk</span><input id="bd" type="color" value="'+b.dark+'" style="width:60px;margin:0;padding:2px"></div><div class="kv"><span>Vurgu rengi</span><input id="ba" type="color" value="'+b.accent+'" style="width:60px;margin:0;padding:2px"></div>'+
  '<div class="kv"><span>Köşe yuvarlaklığı</span><input id="br" type="range" min="4" max="24" value="'+b.radius+'" style="width:140px;margin:0"></div><button class="bt" id="bs">Kaydet</button><div id="m"></div></div>';
  var cur=b.theme;function pv(){var r=document.documentElement.style;r.setProperty('--hd',document.getElementById('bd').value);r.setProperty('--or',document.getElementById('ba').value);r.setProperty('--rd',document.getElementById('br').value+'px')}
  ['bd','ba','br'].forEach(function(i){document.getElementById(i).oninput=function(){cur='';pv()}});
  document.getElementById('sw').onclick=function(ev){var t=ev.target.closest('button');if(!t)return;var x=th.filter(function(q){return q.slug===t.dataset.s})[0];cur=x.slug;document.getElementById('bd').value=x.dark;document.getElementById('ba').value=x.accent;document.getElementById('br').value=x.radius;pv();Array.prototype.forEach.call(document.querySelectorAll('#sw button'),function(q){q.style.borderColor=q===t?'var(--or)':'var(--ln)'})};
  document.getElementById('bs').onclick=function(){C('/api/brand',{method:'PUT',body:JSON.stringify({theme:cur,dark:document.getElementById('bd').value,accent:document.getElementById('ba').value,radius:Number(document.getElementById('br').value)})}).then(function(){msg('Kaydedildi. Yeni açılan müşteri sayfaları bu görünümde olacak.',1)}).catch(function(x){msg(e(x.message))})}}).catch(fail);
 if(TAB==='portal')C('/api/portal-admin/link').then(function(d){A.innerHTML=nav()+'<div class="cd"><h2>Müşteri portalı bağlantısı</h2><div class="mu">Bu adresi müşterilerinize SMS veya sitenizle paylaşın. Müşteri telefon numarasıyla ve SMS koduyla girer.</div><input readonly value="'+e(d.url)+'" onclick="this.select()"></div>'}).catch(fail)}
function msg(h,ok){document.getElementById('m').innerHTML='<div class="msg '+(ok?'g':'r')+'">'+h+'</div>'}
function mk(id){C('/api/pay/jobs/'+id+'/link',{method:'POST',body:JSON.stringify({send_sms:true})}).then(function(d){msg('Ödeme linki hazır'+(d.sms_sent?' ve SMS gönderildi':' (SMS gönderilemedi)')+':<br>'+e(d.url),1)}).catch(function(x){msg(e(x.message))})}
function sq(id){C('/api/quotes/'+id+'/share',{method:'POST',body:JSON.stringify({send_sms:true})}).then(function(d){msg('Teklif linki hazır'+(d.sms_sent?' ve SMS gönderildi':' (SMS gönderilemedi)')+':<br>'+e(d.url),1)}).catch(function(x){msg(e(x.message))})}
function et(){C('/api/einvoice/test',{method:'POST'}).then(function(d){msg(e(d.message),d.ok)}).catch(function(x){msg(e(x.message))})}
function ei(id){C('/api/einvoice/jobs/'+id+'/issue',{method:'POST',body:'{}'}).then(function(d){msg('Fatura '+e(d.number)+' · durum: '+e(d.status),1)}).catch(function(x){msg(e(x.message))})}
function cl(){C('/api/caller/lookup?phone='+encodeURIComponent(document.getElementById('cp').value)).then(function(d){msg(d.known?('<b>'+e((d.customer||{}).name||'Kayıtlı müşteri')+'</b><br>Açık servis: '+d.open_jobs+d.last_jobs.map(function(j){return '<br>'+e(j.job_number)+' · '+e(j.status)}).join('')):'Bu numara kayıtlı değil.',d.known)}).catch(function(x){msg(e(x.message))})}
go();"""


def register(api_router, db, deps, app):
    require_admin = deps["require_admin"]

    async def firm_doc():
        d = tenant.current()
        return (await db.main().firms.find_one({"db": d}, {"_id": 0, "name": 1, "modules": 1, "status": 1, "premium_themes": 1})) if d else None

    async def need(module):
        """Herkese açık uçlar için paket kontrolü. Firma bağlamı yoksa (tek kiracılı kurulum) kısıt yok."""
        f = await firm_doc()
        if f is None:
            return
        mods = f.get("modules")
        if mods is not None and module not in mods:
            raise HTTPException(403, "Bu özellik firmanın paketinde yok")

    async def brand():
        d = await db.app_settings.find_one({"_id": "brand"}, {"_id": 0}) or {}
        return d

    async def premium_ok():
        """Premium temalar yalnızca platform sahibi onayladığı firmalarda açılır (firma bağlamı yoksa sahip: serbest)."""
        f = await firm_doc()
        return True if f is None else bool(f.get("premium_themes"))

    @api_router.get("/brand")
    async def brand_get(_: dict = Depends(require_admin)):
        b = {**DEFAULT_BRAND, **(await brand())}
        ok = await premium_ok()
        return {"brand": b, "premium_ok": ok, "themes": [t for t in THEMES if ok or not t.get("premium") or t["slug"] == b.get("theme")]}

    @api_router.put("/brand")
    async def brand_put(payload: dict, _: dict = Depends(require_admin)):
        b = _clean_brand(payload)
        if b["theme"] and not any(t["slug"] == b["theme"] for t in THEMES):
            raise HTTPException(422, "Tema bulunamadı")
        _th = next((t for t in THEMES if t["slug"] == b["theme"]), None)
        if _th and _th.get("premium") and not await premium_ok() and b["theme"] != (await brand()).get("theme"):
            raise HTTPException(403, "Premium temalar için onay gerekir. Onay için bizimle iletişime geçin.")
        if b["theme"] and b["theme"] != (await brand()).get("theme"):
            # bölüm sırası/gizli bölüm adları temaya özgüdür: tema değişince yeni temanın kendi düzeni açılır (yazı ve resim değişiklikleri temaya göre saklı kalır)
            await db.app_settings.update_one({"_id": "site_profile"}, {"$set": {"layout": {"order": [], "hidden": []}}})
        await db.app_settings.update_one({"_id": "brand"}, {"$set": b}, upsert=True)
        return {"brand": b}

    @api_router.get("/brand/site/{slug}")
    async def brand_site(slug: str, _: dict = Depends(require_admin)):
        """Seçilen site temasını, firmanın adı, telefonu ve form adresi yerleştirilmiş halde döndürür."""
        if not any(t["slug"] == slug for t in THEMES):
            raise HTTPException(404, "Tema bulunamadı")
        f = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "themes", "html", slug + ".html")
        try:
            html = open(f, encoding="utf-8").read()
        except OSError:
            raise HTTPException(404, "Tema dosyası yok")
        name, tel, base = await company()
        th = next(t for t in THEMES if t["slug"] == slug)
        html = html.replace("__API_URL__", f"{base}/api").replace("__PORTAL_URL__", "#")
        if th.get("name") and name:
            html = html.replace(th["name"], name)
        digits = "".join(ch for ch in (tel or "") if ch.isdigit())
        if len(digits) >= 10:
            d = digits[-10:]
            html = html.replace("905320000000", "90" + d).replace("0532 000 00 00", f"0{d[:3]} {d[3:6]} {d[6:8]} {d[8:]}")
        return HTMLResponse(html)

    async def company():
        s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        f = await firm_doc()
        name = s.get("company_name") or (f or {}).get("name") or "OnlineKaydet"
        return name, s.get("company_phone", ""), (s.get("base_url") or PANEL_URL_DEFAULT).rstrip("/")

    # ------------------------------------------------------------ iyzico (firmanın kendi anahtarlarıyla)
    async def iy_cfg():
        d = await db.app_settings.find_one({"_id": "sp_modules"}, {"_id": 0}) or {}
        c = dict((d.get("config") or {}).get("iyzico", {}) or {})
        if not (c.get("api_key") and c.get("secret_key")):
            # "Entegrasyonlar" ekranından girilen ödeme bilgisi (iyzico) de geçerli sayılır
            ig = (await db.app_settings.find_one({"_id": "integrations"}, {"_id": 0}) or {}).get("payment") or {}
            if ig.get("provider") == "iyzico" and ig.get("api_key") and ig.get("secret"):
                c = {"api_key": ig["api_key"], "secret_key": ig["secret"], "sandbox": str(ig.get("sandbox", "0"))}
        return c

    async def iyzico_call(path, body):
        c = await iy_cfg()
        if not (c.get("api_key") and c.get("secret_key")):
            raise HTTPException(400, "iyzico anahtarları girilmemiş")
        base = "https://sandbox-api.iyzipay.com" if str(c.get("sandbox", "1")) not in ("0", "false", "") else "https://api.iyzipay.com"
        raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        rnd = str(int(time.time() * 1000)) + str(random.randint(100000, 999999))
        sig = hmac.new(c["secret_key"].encode(), (rnd + path + raw).encode(), hashlib.sha256).hexdigest()
        auth = base64.b64encode(f"apiKey:{c['api_key']}&randomKey:{rnd}&signature:{sig}".encode()).decode()
        try:
            r = await asyncio.to_thread(lambda: requests.post(base + path, data=raw.encode("utf-8"), timeout=25, headers={
                "Authorization": "IYZWSv2 " + auth, "x-iyzi-rnd": rnd, "Content-Type": "application/json", "Accept": "application/json"}))
            return r.json()
        except HTTPException:
            raise
        except Exception as ex:                      # noqa: BLE001
            raise HTTPException(502, f"iyzico'ya bağlanılamadı: {str(ex)[:120]}")

    app.state.kurumsal_iyzico = iyzico_call          # testlerde taklit edilebilsin

    async def call_iy(path, body):
        return await app.state.kurumsal_iyzico(path, body)

    async def can_pay():
        c = await iy_cfg()
        return bool(c.get("api_key") and c.get("secret_key"))

    # ------------------------------------------------------------ ÖDEME LİNKİ
    def due_of(job):
        p = job.get("payment") or {}
        return round(max(0.0, _f(job.get("total_amount")) - _f(p.get("paid"))), 2)

    @api_router.post("/pay/jobs/{job_id}/link")
    async def pay_link_create(job_id: str, payload: dict, user: dict = Depends(require_admin)):
        job = await db.service_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            raise HTTPException(404, "Servis kaydı bulunamadı")
        due = due_of(job)
        amt = round(_f((payload or {}).get("amount")) or due, 2)
        if amt <= 0 or amt > due + 0.009:
            raise HTTPException(400, f"Tutar 0 ile kalan borç ({due:.2f}) arasında olmalı")
        tok = secrets.token_urlsafe(14)
        await db.pay_links.insert_one({"id": tok[:10], "token": tok, "job_id": job_id, "amount": amt, "status": "bekliyor", "created_at": _now(), "created_by": user["id"]})
        name, tel, base = await company()
        url = f"{base}/odeme/{tenant.public_token(tok)}"
        sent = None
        if (payload or {}).get("send_sms") and notify.norm_msisdn(job.get("customer_phone", "")):
            cn = await notify.get_settings(db)
            first = (job.get("customer_name") or "").split(" ")[0] or "Müşterimiz"
            res = await notify.send(db, "sms", job["customer_phone"], f"Merhaba {first}, {name} servis ödemeniz ({amt:.2f} TL) için güvenli ödeme bağlantısı: {url}",
                                    kind="pay_link", ref=job_id, cfg=cn)
            sent = bool(res and res.get("status") == "sent")
        return {"url": url, "amount": amt, "sms_sent": sent}

    @api_router.get("/pay/links")
    async def pay_links(job_id: str = "", _: dict = Depends(require_admin)):
        q = {"job_id": job_id} if job_id else {}
        rows = await db.pay_links.find(q, {"_id": 0, "token": 0}).sort("created_at", -1).to_list(200)
        return rows

    @api_router.post("/pay/test")
    async def pay_test(_: dict = Depends(require_admin)):
        res = await call_iy("/payment/bin/check", {"locale": "tr", "conversationId": "test", "binNumber": "554960"})
        return {"ok": res.get("status") == "success", "message": res.get("errorMessage") or "Bağlantı başarılı"}

    async def get_link(token):
        if len(token) < 10:
            raise HTTPException(404, "Bağlantı geçersiz")
        lk = await db.pay_links.find_one({"token": token}, {"_id": 0})
        if not lk:
            raise HTTPException(404, "Bağlantı geçersiz")
        return lk

    @api_router.get("/public/pay/{token}")
    async def pay_public(token: str):
        await need("odeme")
        lk = await get_link(token)
        job = await db.service_jobs.find_one({"id": lk["job_id"]}, {"_id": 0}) or {}
        name, _, _ = await company()
        dev = " ".join(x for x in [job.get("device_brand_name", ""), job.get("device_model", "")] if x)
        return {"firm": name, "job_number": job.get("job_number", ""), "device": dev, "amount": lk["amount"], "status": "paid" if lk["status"] == "odendi" else "pending",
                "can_pay": await can_pay()}

    @api_router.post("/public/pay/{token}/init")
    async def pay_init(token: str, request: Request):
        await need("odeme")
        _limit("payinit:" + _ip(request), 10, 600)
        lk = await get_link(token)
        if lk["status"] == "odendi":
            raise HTTPException(409, "Bu ödeme zaten alınmış")
        job = await db.service_jobs.find_one({"id": lk["job_id"]}, {"_id": 0}) or {}
        if lk["amount"] > due_of(job) + 0.009:
            raise HTTPException(409, "Kalan borç değişmiş, yeni bağlantı isteyin")
        _, _, base = await company()
        nm = (job.get("customer_name") or "Müşteri").split()
        total = f"{lk['amount']:.2f}"
        addr = {"contactName": job.get("customer_name") or "Müşteri", "city": job.get("customer_city") or "İstanbul", "country": "Turkey", "address": job.get("customer_address") or "Adres"}
        cb = f"{base}/api/public/pay/{tenant.public_token(token)}/callback"
        body = {"locale": "tr", "conversationId": lk["id"], "price": total, "paidPrice": total, "currency": "TRY", "basketId": lk["id"], "paymentGroup": "PRODUCT",
                "callbackUrl": cb, "enabledInstallments": [1],
                "buyer": {"id": job.get("id", "x")[:20], "name": nm[0], "surname": " ".join(nm[1:]) or "-", "gsmNumber": "+90" + pkey(job.get("customer_phone", "")),
                          "email": "musteri@onlinekaydet.com", "identityNumber": "11111111111", "registrationAddress": addr["address"], "ip": _ip(request) or "85.34.78.112",
                          "city": addr["city"], "country": "Turkey"},
                "shippingAddress": addr, "billingAddress": addr,
                "basketItems": [{"id": job.get("job_number", "servis"), "name": ("Servis " + str(job.get("job_number", "")))[:60], "category1": "Servis", "itemType": "VIRTUAL", "price": total}]}
        res = await call_iy("/payment/iyzipos/checkoutform/initialize/auth/ecom", body)
        if res.get("status") != "success":
            raise HTTPException(502, res.get("errorMessage") or "Ödeme formu açılamadı")
        await db.pay_links.update_one({"token": token}, {"$set": {"iyzico_token": res.get("token")}})
        return {"ok": True, "url": res.get("paymentPageUrl")}

    @api_router.post("/public/pay/{token}/callback")
    async def pay_callback(token: str, request: Request):
        await need("odeme")
        lk = await get_link(token)
        form = await request.form()
        itok = str(form.get("token") or "")
        _, _, base = await company()
        back = f"{base}/odeme/{tenant.public_token(token)}"
        if not itok or itok != lk.get("iyzico_token"):
            return RedirectResponse(back + "?s=hata", status_code=303)
        res = await call_iy("/payment/iyzipos/checkoutform/auth/ecom/detail", {"locale": "tr", "conversationId": lk["id"], "token": itok})
        ok = res.get("status") == "success" and res.get("paymentStatus") == "SUCCESS" and abs(_f(res.get("paidPrice")) - lk["amount"]) < 0.01
        if ok and lk["status"] != "odendi":
            claim = await db.pay_links.update_one({"token": token, "status": {"$ne": "odendi"}}, {"$set": {"status": "odendi", "paid_at": _now(), "payment_id": str(res.get("paymentId", ""))}})
            if claim.modified_count:
                job = await db.service_jobs.find_one({"id": lk["job_id"]}, {"_id": 0}) or {}
                p = job.get("payment") or {"status": "odenmedi", "paid": 0.0, "due_date": "", "history": []}
                paid = round(_f(p.get("paid")) + lk["amount"], 2)
                p = {**p, "paid": paid, "status": "odendi" if paid >= _f(job.get("total_amount")) - 0.009 else "kismi",
                     "history": [*p.get("history", []), {"amount": lk["amount"], "method": "kart", "provider": "iyzico", "at": _now(), "by": "odeme-linki"}]}
                await db.service_jobs.update_one({"id": lk["job_id"]}, {"$set": {"payment": p}})
                try:
                    await notify.notify_owner(db, f"Online ödeme alındı: {job.get('job_number', '')} · {lk['amount']:.2f} ₺", kind="payment")
                except Exception:                      # noqa: BLE001
                    pass
        return RedirectResponse(back + ("?s=ok" if ok else "?s=hata"), status_code=303)

    @app.get("/odeme/{token}", include_in_schema=False)
    async def pay_page(token: str):
        return HTMLResponse(_page("Servis ödemesi", _PAY_JS, await brand(), (await company())[0]), headers={"Cache-Control": "no-store"})

    # ------------------------------------------------------------ TEKLİF ONAY LİNKİ
    @api_router.post("/quotes/{quote_id}/share")
    async def quote_share(quote_id: str, payload: dict, _: dict = Depends(require_admin)):
        q = await db.price_quotes.find_one({"id": quote_id}, {"_id": 0})
        if not q:
            raise HTTPException(404, "Teklif bulunamadı")
        tok = q.get("approve_token") or secrets.token_urlsafe(14)
        await db.price_quotes.update_one({"id": quote_id}, {"$set": {"approve_token": tok}})
        name, tel, base = await company()
        url = f"{base}/teklif/{tenant.public_token(tok)}"
        sent = None
        if (payload or {}).get("send_sms") and notify.norm_msisdn(q.get("customer_phone", "")):
            cn = await notify.get_settings(db)
            first = (q.get("customer_name") or "").split(" ")[0] or "Müşterimiz"
            res = await notify.send(db, "sms", q["customer_phone"], f"Merhaba {first}, {name} fiyat teklifiniz hazır ({q['target_total']:.2f} TL). İnceleyip onaylamak için: {url}",
                                    kind="quote_link", ref=quote_id, cfg=cn)
            sent = bool(res and res.get("status") == "sent")
        return {"url": url, "sms_sent": sent}

    async def get_quote_by_tok(token):
        if len(token) < 10:
            raise HTTPException(404, "Bağlantı geçersiz")
        q = await db.price_quotes.find_one({"approve_token": token}, {"_id": 0})
        if not q:
            raise HTTPException(404, "Bağlantı geçersiz")
        return q

    @api_router.get("/public/quote/{token}")
    async def quote_public(token: str):
        await need("teklif")
        q = await get_quote_by_tok(token)
        name, _, _ = await company()
        lines = [{"name": p.get("name", ""), "total": _f(p.get("amount"))} for p in q.get("parts", [])]
        if _f(q.get("labor_fee")) > 0:
            lines.append({"name": "İşçilik", "total": _f(q["labor_fee"])})
        dec = q.get("customer_decision") or ""
        return {"firm": name, "quote_number": q.get("quote_number", ""), "device": " ".join(x for x in [q.get("device_brand_name", ""), q.get("device_model", "")] if x),
                "fault": q.get("fault_description", ""), "lines": lines, "total": _f(q.get("target_total")), "decision": dec}

    @api_router.post("/public/quote/{token}/decision")
    async def quote_decision(token: str, payload: dict, request: Request):
        await need("teklif")
        _limit("qdec:" + _ip(request), 10, 600)
        q = await get_quote_by_tok(token)
        if q.get("customer_decision"):
            raise HTTPException(409, "Bu teklif için karar zaten verilmiş")
        if q.get("status") not in ("beklemede", ""):
            raise HTTPException(409, "Bu teklif artık beklemede değil")
        dec = "onaylandi" if (payload or {}).get("decision") == "onay" else ("reddedildi" if (payload or {}).get("decision") == "red" else "")
        if not dec:
            raise HTTPException(422, "Karar geçersiz")
        note = str((payload or {}).get("note") or "")[:300]
        await db.price_quotes.update_one({"id": q["id"]}, {"$set": {"customer_decision": dec, "customer_note": note, "decided_at": _now(), "decided_ip": _ip(request), "updated_at": _now()}})
        try:
            await notify.notify_owner(db, f"Teklif {q.get('quote_number', '')} müşteri tarafından {'ONAYLANDI' if dec == 'onaylandi' else 'REDDEDİLDİ'}: {q.get('customer_name', '')}", kind="quote")
        except Exception:                              # noqa: BLE001
            pass
        return {"ok": True, "decision": dec}

    @app.get("/teklif/{token}", include_in_schema=False)
    async def quote_page(token: str):
        return HTMLResponse(_page("Fiyat teklifi", _QUOTE_JS, await brand(), (await company())[0]), headers={"Cache-Control": "no-store"})

    # ------------------------------------------------------------ MÜŞTERİ PORTALI (telefon + SMS kodu)
    @api_router.post("/public/portal/{token}/login")
    async def portal_login(token: str, payload: dict, request: Request):
        await need("portal")
        ph = pkey((payload or {}).get("phone", ""))
        if len(ph) != 10:
            raise HTTPException(422, "Geçerli bir cep telefonu girin")
        _limit("plog:" + _ip(request), 8, 900)
        _limit("plogp:" + ph, 3, 600)
        has = await db.service_jobs.find_one({"customer_phone": {"$regex": rx(ph)}}, {"_id": 1}) or await db.customers.find_one({"phone": {"$regex": rx(ph)}}, {"_id": 1})
        if has:                                         # kayıtlı olup olmadığını belli etmemek için yanıt hep aynı
            code = f"{secrets.randbelow(10**6):06d}"
            await db.portal_codes.update_one({"phone": ph}, {"$set": {"phone": ph, "code_hash": _h(code + ph), "exp": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(), "tries": 0}}, upsert=True)
            name, _, _ = await company()
            cn = await notify.get_settings(db)
            await notify.send(db, "sms", ph, f"{name} müşteri portalı giriş kodunuz: {code}", kind="portal_code", ref=ph, cfg=cn, store_text="Portal giriş kodu ******")
        return {"ok": True}

    @api_router.post("/public/portal/{token}/verify")
    async def portal_verify(token: str, payload: dict, request: Request):
        await need("portal")
        ph = pkey((payload or {}).get("phone", ""))
        code = re.sub(r"\D", "", str((payload or {}).get("code", "")))
        _limit("pver:" + _ip(request), 15, 900)
        row = await db.portal_codes.find_one({"phone": ph}, {"_id": 0})
        if not row or row["exp"] < _now() or row.get("tries", 0) >= 5:
            raise HTTPException(400, "Kod geçersiz veya süresi dolmuş")
        if not hmac.compare_digest(row["code_hash"], _h(code + ph)):
            await db.portal_codes.update_one({"phone": ph}, {"$inc": {"tries": 1}})
            raise HTTPException(400, "Kod hatalı")
        await db.portal_codes.delete_one({"phone": ph})
        sess = secrets.token_urlsafe(24)
        await db.portal_sessions.insert_one({"h": _h(sess), "phone": ph, "exp": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()})
        return {"session": sess}

    async def sess_phone(request):
        s = request.headers.get("X-Portal", "")
        row = await db.portal_sessions.find_one({"h": _h(s)}, {"_id": 0}) if s else None
        if not row or row["exp"] < _now():
            raise HTTPException(401, "Oturum geçersiz")
        return row["phone"]

    @api_router.get("/public/portal/{token}/me")
    async def portal_me(token: str, request: Request):
        await need("portal")
        ph = await sess_phone(request)
        name, _, base = await company()
        jobs = await db.service_jobs.find({"customer_phone": {"$regex": rx(ph)}}, {"_id": 0}).sort("created_at", -1).to_list(30)
        out = []
        for j in jobs:
            lk = await db.pay_links.find_one({"job_id": j["id"], "status": "bekliyor"}, {"_id": 0, "token": 1}, sort=[("created_at", -1)])
            out.append({"job_number": j.get("job_number", ""), "status": j.get("status", ""), "device": " ".join(x for x in [j.get("device_brand_name", ""), j.get("device_model", "")] if x),
                        "total": _f(j.get("total_amount")), "created_at": j.get("created_at", ""),
                        "track_url": f"{base}/takip/{tenant.public_token(j['track_token'])}" if j.get("track_token") else "",
                        "pay_url": f"{base}/odeme/{tenant.public_token(lk['token'])}" if lk else ""})
        qs = await db.price_quotes.find({"customer_phone": {"$regex": rx(ph)}, "status": "beklemede", "customer_decision": {"$in": [None, ""]}, "approve_token": {"$exists": True}}, {"_id": 0}).to_list(10)
        cust = await db.customers.find_one({"phone": {"$regex": rx(ph)}}, {"_id": 0, "name": 1}) or {}
        nm = ((cust.get("name") or (jobs[0].get("customer_name") if jobs else "")) or "").split(" ")[0]
        return {"firm": name, "name": nm, "jobs": out,
                "quotes": [{"quote_number": q.get("quote_number", ""), "total": _f(q.get("target_total")), "url": f"{base}/teklif/{tenant.public_token(q['approve_token'])}"} for q in qs]}

    @api_router.post("/public/portal/{token}/request")
    async def portal_request(token: str, payload: dict, request: Request):
        await need("portal")
        ph = await sess_phone(request)
        _limit("preq:" + ph, 5, 3600)
        fault = str((payload or {}).get("fault") or "").strip()[:400]
        if len(fault) < 3:
            raise HTTPException(422, "Arızayı kısaca yazın")
        c = await db.customers.find_one({"phone": {"$regex": rx(ph)}}, {"_id": 0, "name": 1}) or {}
        await db.contact_messages.insert_one({"id": secrets.token_hex(8), "type": "portal_talep", "name": c.get("name", ""), "phone": ph, "email": "", "message": fault,
                                              "status": "yeni", "created_at": _now()})
        return {"ok": True}

    @app.get("/portal/{token}", include_in_schema=False)
    async def portal_page(token: str):
        return HTMLResponse(_page("Müşteri portalı", _PORTAL_JS, await brand(), (await company())[0]), headers={"Cache-Control": "no-store"})

    @api_router.get("/portal-admin/link")
    async def portal_link(_: dict = Depends(require_admin)):
        _, _, base = await company()
        return {"url": f"{base}/portal/{tenant.public_token('giris')}"}

    # ------------------------------------------------------------ ARAYAN NUMARA
    @api_router.get("/caller/lookup")
    async def caller_lookup(phone: str, _: dict = Depends(require_admin)):
        ph = pkey(phone)
        if len(ph) < 7:
            raise HTTPException(422, "Telefon numarası geçersiz")
        c = await db.customers.find_one({"phone": {"$regex": rx(ph)}}, {"_id": 0, "id": 1, "name": 1, "phone": 1, "address": 1})
        jobs = await db.service_jobs.find({"customer_phone": {"$regex": rx(ph)}}, {"_id": 0, "id": 1, "job_number": 1, "status": 1, "created_at": 1,
                                                                                      "device_brand_name": 1, "device_model": 1, "total_amount": 1}).sort("created_at", -1).to_list(5)
        open_n = await db.service_jobs.count_documents({"customer_phone": {"$regex": rx(ph)}, "status": {"$nin": ["tamamlandi", "faturalandi", "iptal"]}})
        return {"known": bool(c or jobs), "customer": c, "open_jobs": open_n, "last_jobs": jobs}

    @app.get("/araclar", include_in_schema=False)
    async def tools_page():
        return HTMLResponse(_page("Kurumsal araçlar", _TOOLS_JS, await brand()), headers={"Cache-Control": "no-store"})
