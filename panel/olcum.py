# -*- coding: utf-8 -*-
"""Firma sitesinde ölçüm ve reklam etiketleri.

Panelde "Entegrasyonlar" ekranından girilen kimlikleri (Google Etiket Yöneticisi, GA4, Google Ads,
Meta Pixel, TikTok Pixel, Search Console doğrulaması) yayındaki her sayfanın <head> bölümüne basar.

- Çerez bandı açıksa ölçüm betikleri `olcum`, reklam betikleri `pazarlama` onayına kadar yüklenmez.
- `window.okTrack(ad, veri)` mağaza olaylarını (view_item_list, view_item, add_to_cart, begin_checkout, purchase)
  dataLayer'a ve açık olan her kanala gönderir. Onay gelmeden gönderilen olaylar bekletilir, onaydan sonra iletilir.
- Satın alma olayında `transaction_id` Meta için `eventID` olarak da gider; sunucu tarafı Conversions API
  (`meta_capi.py`) aynı kimlikle gönderdiği için Meta tekrar saymaz.
"""
import html as _h
import json
import re

KIMLIKLER = ("gtm", "ga4", "google_ads", "meta_pixel", "tiktok_pixel", "search_console")


def _temiz(v, n=60):
    return re.sub(r"[^A-Za-z0-9_\-./]", "", str(v or ""))[:n]


async def ayar(db):
    """Açık ve doldurulmuş kimlikleri döndürür: {gtm, ga4, ads, adl, fb, tt, sc}."""
    out = {}
    try:
        rows = await db.yp_integrations.find({"id": {"$in": list(KIMLIKLER)}, "on": True}, {"_id": 0, "id": 1, "keys": 1}).to_list(10)
    except Exception:                                              # noqa: BLE001
        return out
    for r in rows:
        k = r.get("keys") or {}
        pid = r.get("id")
        v = _temiz(k.get("id"))
        if not v:
            continue
        if pid == "gtm" and re.fullmatch(r"GTM-[A-Z0-9]{4,10}", v.upper()):
            out["gtm"] = v.upper()
        elif pid == "ga4" and re.fullmatch(r"G-[A-Z0-9]{4,}", v.upper()):
            out["ga4"] = v.upper()
        elif pid == "google_ads" and re.fullmatch(r"AW-\d{6,}", v.upper()):
            out["ads"] = v.upper()
            out["adl"] = _temiz(k.get("label"), 80)
        elif pid == "meta_pixel" and v.isdigit():
            out["fb"] = v
        elif pid == "tiktok_pixel" and re.fullmatch(r"[A-Za-z0-9]{6,32}", v):
            out["tt"] = v
        elif pid == "search_console":
            out["sc"] = _temiz(k.get("id"), 120)
    return out


JS = r"""(function(){
var T=__T__;
window.dataLayer=window.dataLayer||[];
function gtag(){dataLayer.push(arguments)}
var S={o:0,p:0},B={o:[],p:[]};
function izin(b){return window.okCerez?window.okCerez.izin(b):true}
function yukle(u){var s=document.createElement('script');s.async=true;s.src=u;document.head.appendChild(s)}
function para(d){return {currency:d.currency||'TRY',value:Number(d.value||0)}}
function ids(d){return (d.items||[]).map(function(i){return String(i.item_id)})}
function cts(d){return (d.items||[]).map(function(i){return {id:String(i.item_id),quantity:i.quantity||1,item_price:i.price||0}})}
function ga(n,d){
  if(T.gtm){dataLayer.push({ecommerce:null});dataLayer.push({event:n,ecommerce:d});return}
  if(T.ga4||T.ads){gtag('event',n,d)}
  if(n==='purchase'&&T.ads&&T.adl){gtag('event','conversion',{send_to:T.ads+'/'+T.adl,value:d.value,currency:d.currency||'TRY',transaction_id:d.transaction_id})}
}
function fb(n,d){
  if(!window.fbq)return;
  var m={view_item:'ViewContent',add_to_cart:'AddToCart',begin_checkout:'InitiateCheckout',purchase:'Purchase'}[n];
  if(!m)return;
  var p=para(d);p.content_ids=ids(d);p.content_type='product';p.contents=cts(d);p.num_items=(d.items||[]).length;
  if(n==='purchase'&&d.transaction_id)fbq('track',m,p,{eventID:String(d.transaction_id)});else fbq('track',m,p);
}
function tt(n,d){
  if(!window.ttq)return;
  var m={view_item:'ViewContent',add_to_cart:'AddToCart',begin_checkout:'InitiateCheckout',purchase:'CompletePayment'}[n];
  if(!m)return;
  var p=para(d);p.content_type='product';p.contents=(d.items||[]).map(function(i){return {content_id:String(i.item_id),content_name:i.item_name,quantity:i.quantity||1,price:i.price||0}});
  ttq.track(m,p);
}
function olcumBasla(){
  if(S.o||!izin('olcum'))return;S.o=1;
  if(T.gtm){dataLayer.push({'gtm.start':Date.now(),event:'gtm.js'});yukle('https://www.googletagmanager.com/gtm.js?id='+T.gtm)}
  else if(T.ga4||T.ads){yukle('https://www.googletagmanager.com/gtag/js?id='+(T.ga4||T.ads));gtag('js',new Date());if(T.ga4)gtag('config',T.ga4);if(T.ads)gtag('config',T.ads)}
  B.o.splice(0).forEach(function(x){ga(x[0],x[1])});
}
function reklamBasla(){
  if(S.p||!izin('pazarlama'))return;S.p=1;
  if(T.fb){
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    fbq('init',T.fb);fbq('track','PageView');
  }
  if(T.tt){
    !function(w,d,t){w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];ttq.methods=['page','track','identify','instances','debug','on','off','once','ready','alias','group','enableCookie','disableCookie'];ttq.setAndDefer=function(t,e){t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}};for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);ttq.load=function(e){var n=d.createElement('script');n.src='https://analytics.tiktok.com/i18n/pixel/events.js?sdkid='+e+'&lib='+t;n.async=!0;d.head.appendChild(n)};ttq.load(T.tt);ttq.page()}(window,document,'ttq');
  }
  B.p.splice(0).forEach(function(x){fb(x[0],x[1]);tt(x[0],x[1])});
}
function basla(){olcumBasla();reklamBasla()}
window.okTrack=function(n,d){
  d=d||{};
  if(S.o)ga(n,d);else if(T.gtm||T.ga4||T.ads)B.o.push([n,d]);
  if(S.p){fb(n,d);tt(n,d)}else if(T.fb||T.tt)B.p.push([n,d]);
};
window.okTrackIds=T;
window.addEventListener('ok-cerez',basla);
if(document.readyState!=='loading')basla();else document.addEventListener('DOMContentLoaded',basla);
})();"""


def head_html(cfg):
    """<head> sonuna eklenecek parça. Hiç kimlik yoksa yine de okTrack boş işlev olarak tanımlanır."""
    cfg = cfg or {}
    parts = []
    if cfg.get("sc"):
        parts.append('<meta name="google-site-verification" content="%s">' % _h.escape(cfg["sc"], quote=True))
    t = {k: cfg[k] for k in ("gtm", "ga4", "ads", "adl", "fb", "tt") if cfg.get(k)}
    parts.append('<script id="okolc">' + JS.replace("__T__", json.dumps(t, ensure_ascii=False).replace("</", "<\\/")) + "</script>")
    return "".join(parts)


def body_html(cfg):
    """GTM <noscript> yedeği (betik kapalı tarayıcılar için)."""
    if (cfg or {}).get("gtm"):
        return ('<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=%s" height="0" width="0" '
                'style="display:none;visibility:hidden"></iframe></noscript>' % _h.escape(cfg["gtm"], quote=True))
    return ""


def ekle(h, cfg):
    """Üretilmiş sayfaya etiketleri ekler (iki kez eklemez)."""
    if not h or 'id="okolc"' in h or "</head>" not in h:
        return h
    h = h.replace("</head>", head_html(cfg) + "</head>", 1)
    nb = body_html(cfg)
    if nb:
        h = re.sub(r"(<body\b[^>]*>)", lambda m: m.group(1) + nb, h, 1)
    return h
