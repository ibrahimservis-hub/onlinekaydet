"""Modern site modülleri: duyuru + dürüst geri sayım, hikâye çubuğu, mega menü, fırsatlar, paketler, kayarak belirme.
Hepsi tema değişkenlerini (--ac, --dk, --r ...) kullanır; her blok panelden açılıp kapanır (.ed data-nm).
Geri sayım DÜRÜSTTÜR: bitiş tarihi sayfaya yazılıdır (yenileyince sıfırlanmaz), süre dolunca bölüm kendini gizler."""
import datetime, os
from .base import ic

DAYS = 21          # kampanyanın varsayılan süresi (üretim tarihinden itibaren)


def _end():
    v = os.environ.get('OK_CAMPAIGN_END')
    if v:
        return v
    return (datetime.date.today() + datetime.timedelta(days=DAYS)).strftime('%Y-%m-%dT23:59:00')


def _ed(nm, h, off=False):
    return f'<div class="ed" data-nm="{nm}"' + (' data-dflt="off"' if off else '') + f'>{h}</div>'


CSS = """
.rv{opacity:0;transform:translateY(22px);transition:opacity .6s ease,transform .6s ease}.rv.in{opacity:1;transform:none}
@media(prefers-reduced-motion:reduce){.rv{opacity:1;transform:none;transition:none}}
.ann{background:var(--dk);color:#fff;font:600 .85rem/1.3 var(--fb);position:relative;z-index:80}
.ann .w{display:flex;align-items:center;justify-content:center;gap:14px;padding:9px 44px 9px 0;flex-wrap:wrap;text-align:center}
.ann a{color:var(--ac);font-weight:700;text-decoration:underline;text-underline-offset:3px}
.ann .cd2{display:inline-flex;gap:6px;font:700 .82rem/1 var(--fm,var(--fb));font-variant-numeric:tabular-nums}
.ann .cd2 b{background:#ffffff1f;border-radius:6px;padding:5px 7px;min-width:34px;text-align:center}
.ann .x{position:absolute;right:max(10px,calc((100vw - var(--wmax,1180px))/2));top:50%;transform:translateY(-50%);width:44px;height:44px;display:grid;place-items:center;background:none;border:0;color:#fff;cursor:pointer;opacity:.7}
.ann .x:hover{opacity:1}
@media(max-width:560px){.ann .w{gap:4px 10px;padding:6px 44px 6px 12px;font-size:.78rem}.ann .cd2 b{padding:4px 5px;min-width:28px}}
.stq{padding:clamp(18px,3vw,30px) 0 0}.stq .row{display:flex;gap:clamp(14px,2.4vw,26px);overflow-x:auto;padding:6px 2px 12px;scrollbar-width:none;-webkit-overflow-scrolling:touch}.stq .row::-webkit-scrollbar{display:none}
.stq button.st{flex:none;display:grid;justify-items:center;gap:8px;background:none;border:0;cursor:pointer;color:var(--ink);font:600 .78rem/1.2 var(--fb);width:78px}
.stq .ring{width:68px;height:68px;border-radius:50%;padding:3px;background:conic-gradient(var(--ac),color-mix(in srgb,var(--ac) 30%,var(--dk)),var(--ac));display:grid;place-items:center;transition:transform .2s}
.stq button.st:hover .ring{transform:scale(1.06)}.stq button.st.seen .ring{background:var(--ln)}
.stq .ring span{width:100%;height:100%;border-radius:50%;background:var(--dk);color:#fff;display:grid;place-items:center;border:3px solid var(--bg)}
.stv{position:fixed;inset:0;z-index:300;background:#000d;display:none;align-items:center;justify-content:center}.stv.on{display:flex}
.stv .card{position:relative;width:min(420px,100vw);height:min(760px,100dvh);background:linear-gradient(160deg,var(--dk),color-mix(in srgb,var(--ac) 55%,var(--dk)));color:#fff;border-radius:calc(var(--r)*1.3);display:flex;flex-direction:column;justify-content:flex-end;padding:30px 26px 34px;overflow:hidden}
@media(max-width:520px){.stv .card{border-radius:0}}
.stv .bars{position:absolute;top:14px;left:14px;right:14px;display:flex;gap:5px}.stv .bars i{flex:1;height:3px;background:#ffffff40;border-radius:3px;overflow:hidden}.stv .bars i b{display:block;height:100%;width:0;background:#fff}
.stv .bars i.done b{width:100%}.stv .bars i.run b{animation:stb var(--dur,6s) linear forwards}@keyframes stb{to{width:100%}}
.stv .big{font:800 clamp(1.7rem,6vw,2.2rem)/1.1 var(--fd);margin:18px 0 10px}.stv p{font-size:1.02rem;opacity:.92;line-height:1.5;margin-bottom:22px}.stv .ico{opacity:.9}
.stv .cl{position:absolute;top:26px;right:12px;width:44px;height:44px;display:grid;place-items:center;background:none;border:0;color:#fff;font-size:1.6rem;cursor:pointer;z-index:3}
.stv .nx,.stv .pv{position:absolute;top:70px;bottom:120px;width:36%;background:none;border:0;cursor:pointer;z-index:2}.stv .nx{right:0}.stv .pv{left:0}
.stv .go{z-index:3;position:relative}
.mega{position:fixed;left:50%;transform:translate(-50%,8px);width:min(960px,calc(100vw - 32px));background:var(--bg);color:var(--ink);border:1px solid var(--ln);border-radius:calc(var(--r)*1.3);box-shadow:0 30px 70px -28px #0007;padding:22px;display:grid;grid-template-columns:1.6fr 1fr;gap:22px;z-index:90;opacity:0;visibility:hidden;transition:opacity .18s,transform .18s,visibility .18s}
.mega.on{opacity:1;visibility:visible;transform:translate(-50%,0)}.mega .ls{display:grid;grid-template-columns:1fr 1fr;gap:4px}
.mega .ls a{display:flex;gap:12px;padding:12px;border-radius:calc(var(--r)*.8);align-items:flex-start;transition:background .15s}.mega .ls a:hover,.mega .ls a:focus-visible{background:var(--sf)}
.mega .ls .mi{flex:none;width:40px;height:40px;border-radius:calc(var(--r)*.7);background:var(--ac);color:var(--on-ac);display:grid;place-items:center}
.mega .ls b{display:block;font:700 .95rem/1.2 var(--fb);margin-bottom:3px}.mega .ls small{color:var(--mut);font-size:.8rem;line-height:1.35;display:block}
.mega .pr{background:var(--dk);color:#fff;border-radius:calc(var(--r)*1.1);padding:22px;display:flex;flex-direction:column;justify-content:space-between;gap:16px}.mega .pr small{opacity:.75;font-size:.78rem;letter-spacing:.08em;text-transform:uppercase}
.mega .pr b{font:800 1.3rem/1.2 var(--fd);display:block;margin-top:6px}.mega .pr .btn{align-self:flex-start}
@media(max-width:900px){.mega{display:none}}
.deal .tm{display:inline-flex;gap:8px;font:800 clamp(1.3rem,3vw,1.9rem)/1 var(--fm,var(--fd));font-variant-numeric:tabular-nums;margin-top:10px}.deal .tm span{display:grid;justify-items:center;gap:5px;min-width:58px;background:var(--dk);color:#fff;border-radius:calc(var(--r)*.7);padding:11px 8px}
.deal .tm small{font:600 .62rem/1 var(--fb);letter-spacing:.1em;text-transform:uppercase;opacity:.7}
.deal .gr{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;margin-top:26px}
.deal .it{position:relative;border:1px solid var(--ln);border-radius:calc(var(--r)*1.2);background:var(--fbg);padding:22px;display:grid;gap:10px;align-content:start;transition:transform .25s,box-shadow .25s}.deal .it:hover{transform:translateY(-4px);box-shadow:0 20px 40px -26px #0006}
.deal .bd{position:absolute;top:14px;right:14px;background:var(--ac);color:var(--on-ac);font:800 .82rem/1 var(--fb);padding:7px 10px;border-radius:99px}
.deal .it .ph2{height:110px;border-radius:calc(var(--r)*.9);background:var(--sf);color:var(--ac);display:grid;place-items:center}
.deal .it h3{font-size:1.08rem}.deal .it p{color:var(--mut);font-size:.9rem}.deal .pz{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}.deal .pz s{color:var(--mut)}.deal .pz b{font:800 1.25rem/1 var(--fd);color:var(--ink)}
.deal .it .btn{justify-self:start;min-height:44px}
.pk .gr{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px;margin-top:26px;align-items:stretch}
.pk .it{border:1px solid var(--ln);border-radius:calc(var(--r)*1.3);background:var(--fbg);padding:clamp(22px,2.6vw,32px);display:flex;flex-direction:column;gap:14px;position:relative}
.pk .it.rc{background:var(--dk);color:#fff;border-color:var(--dk);--hc:#fff}.pk .it.rc li{color:#ffffffd0}.pk .it.rc .tg{background:var(--ac);color:var(--on-ac)}
.pk .tg{position:absolute;top:-12px;left:22px;background:var(--sf);font:700 .72rem/1 var(--fb);padding:7px 12px;border-radius:99px;letter-spacing:.06em;text-transform:uppercase}
.pk h3{font-size:1.25rem}.pk ul{list-style:none;display:grid;gap:9px;flex:1}.pk li{display:flex;gap:10px;font-size:.92rem;color:var(--mut)}.pk li svg{flex:none;color:var(--ac);margin-top:2px}
.pk .it .btn{width:100%;justify-content:center}
"""

JS = r"""
(function(){
var rm=window.matchMedia&&matchMedia('(prefers-reduced-motion:reduce)').matches;
function $(s,r){return (r||document).querySelector(s)}function $$(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))}
function p2(n){return (n<10?'0':'')+n}
/* geri sayım: bitiş tarihi sayfaya yazılı, yenilemeyle sıfırlanmaz; süre dolunca bölüm/çubuk gizlenir */
function tick(el){var end=new Date(el.getAttribute('data-end')).getTime();var host=el.closest('[data-cd-host]')||el;
 function run(){var d=end-Date.now();if(!(d>0)){host.style.display='none';return false}var s=Math.floor(d/1000);
  var g=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60),c=s%60;
  var f=el.getAttribute('data-fmt');
  if(f==='box'){el.innerHTML='<span>'+g+'<small>gün</small></span><span>'+p2(h)+'<small>saat</small></span><span>'+p2(m)+'<small>dk</small></span><span>'+p2(c)+'<small>sn</small></span>'}
  else{el.innerHTML='<b>'+g+' g</b><b>'+p2(h)+' sa</b><b>'+p2(m)+' dk</b><b>'+p2(c)+' sn</b>'}return true}
 if(run())var t=setInterval(function(){if(!run())clearInterval(t)},1000)}
$$('[data-end]').forEach(tick);
$$('.ann .x').forEach(function(b){b.addEventListener('click',function(){var a=b.closest('.ann');a.style.display='none';annH();try{sessionStorage.setItem('annx','1')}catch(e){}})});
try{if(sessionStorage.getItem('annx'))$$('.ann').forEach(function(a){a.style.display='none'})}catch(e){}
function annH(){var a=document.querySelector('.ann'),h=0;if(a&&a.style.display!=='none')h=a.offsetHeight;document.documentElement.style.setProperty('--annh',h+'px')}annH();window.addEventListener('resize',annH);
/* kayarak belirme */
var rv=$$('.rv');if('IntersectionObserver' in window&&!rm){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.12});rv.forEach(function(e){io.observe(e)})}else rv.forEach(function(e){e.classList.add('in')});
/* hikâyeler */
var V=$('.stv');if(V){var items=$$('.stq .st'),data=items.map(function(b){return {t:b.getAttribute('data-t'),d:b.getAttribute('data-d'),i:b.querySelector('.ring span').innerHTML,l:b.getAttribute('data-l')||'#randevu',c:b.getAttribute('data-c')||'Randevu al'}});
 var cur=0,tm=null,DUR=6000;
 function show(n){if(n<0)n=0;if(n>=data.length){close();return}cur=n;var s=data[n];items[n].classList.add('seen');
  V.querySelector('.bars').innerHTML=data.map(function(_,k){return '<i class="'+(k<n?'done':k===n?'run':'')+'"><b></b></i>'}).join('');
  V.querySelector('.ico').innerHTML=s.i;V.querySelector('.big').textContent=s.t;V.querySelector('.tx').textContent=s.d;var g=V.querySelector('.go');g.textContent=s.c;g.setAttribute('href',s.l);
  clearTimeout(tm);if(!rm)tm=setTimeout(function(){show(cur+1)},DUR)}
 function close(){V.classList.remove('on');clearTimeout(tm);document.body.style.overflow=''}
 items.forEach(function(b,k){b.addEventListener('click',function(){V.classList.add('on');document.body.style.overflow='hidden';show(k);V.querySelector('.cl').focus()})});
 V.querySelector('.nx').addEventListener('click',function(){show(cur+1)});V.querySelector('.pv').addEventListener('click',function(){show(cur-1)});V.querySelector('.cl').addEventListener('click',close);
 V.querySelector('.go').addEventListener('click',close);
 document.addEventListener('keydown',function(e){if(!V.classList.contains('on'))return;if(e.key==='Escape')close();if(e.key==='ArrowRight')show(cur+1);if(e.key==='ArrowLeft')show(cur-1)})}
/* mega menü */
var M=$('.mega');if(M){var host=$$('.nv nav a, header nav a').filter(function(a){var h=a.getAttribute('href');return h==='#hizmet'||h==='#urunler'})[0];
 if(host&&host.offsetParent!==null){var to=null;
  function pos(){var nv=host.closest('.nv,header')||host;var r=nv.getBoundingClientRect();M.style.top=Math.max(r.bottom,0)+'px'}
  function open(){clearTimeout(to);pos();M.classList.add('on');host.setAttribute('aria-expanded','true')}
  function shut(){to=setTimeout(function(){M.classList.remove('on');host.setAttribute('aria-expanded','false')},140)}
  host.setAttribute('aria-haspopup','true');host.setAttribute('aria-expanded','false');
  host.addEventListener('mouseenter',open);host.addEventListener('focus',open);host.addEventListener('mouseleave',shut);M.addEventListener('mouseenter',function(){clearTimeout(to)});M.addEventListener('mouseleave',shut);
  document.addEventListener('keydown',function(e){if(e.key==='Escape'){M.classList.remove('on')}});
  M.addEventListener('focusout',function(e){if(!M.contains(e.relatedTarget)&&e.relatedTarget!==host)shut()});
  $$('a',M).forEach(function(a){a.addEventListener('click',function(){M.classList.remove('on')})});
  window.addEventListener('scroll',function(){if(M.classList.contains('on'))pos()},{passive:true})}else M.remove()}
})();
"""


def _sector_offers(x):
    """Sektöre göre kampanya/paket başlıkları. Fiyat uydurmaz: indirim oranı ve koşul işletmeye ait, panelden değişir."""
    S = x.c['services']
    shop = x.r['sector'] in ('eticaret', 'tekstil')
    return S, shop


def announce(x):
    end = _end()
    return _ed('Duyuru çubuğu', f'<div class="ann" data-cd-host="1"><div class="w"><span>{x.c["label"]} için kampanya dönemi</span>'
               f'<span class="cd2" data-end="{end}"></span><a href="#firsat">Fırsatları gör</a></div>'
               f'<button class="x" type="button" aria-label="Duyuruyu kapat">{ic("x", 18) if _has("x") else "&times;"}</button></div>')


def _has(n):
    from .base import P
    return n in P


def stories(x):
    S, shop = _sector_offers(x)
    items = [(t, d, i) for t, d, i in S[:5]]
    extra = ('Kampanyalar', 'Güncel fırsatları ve paketleri inceleyin.', 'st', '#firsat', 'Fırsatları gör')
    btns = ''
    for t, d, i in [extra[:3]] + items:
        lk, cta = ('#firsat', 'Fırsatları gör') if t == 'Kampanyalar' else ('#randevu', 'Randevu al')
        btns += (f'<button class="st" type="button" data-t="{t}" data-d="{d}" data-l="{lk}" data-c="{cta}" aria-label="{t} hikâyesini aç">'
                 f'<span class="ring"><span>{ic(i if _has(i) else "st", 26)}</span></span><span>{t}</span></button>')
    viewer = ('<div class="stv" role="dialog" aria-modal="true" aria-label="Hikâyeler"><div class="card"><div class="bars"></div>'
              '<button class="cl" type="button" aria-label="Kapat">&times;</button><button class="pv" type="button" aria-label="Önceki"></button><button class="nx" type="button" aria-label="Sonraki"></button>'
              '<div class="ico"></div><div class="big"></div><p class="tx"></p><a class="btn go" href="#randevu">Randevu al</a></div></div>')
    return _ed('Hikâye çubuğu', f'<section class="stq" aria-label="Öne çıkanlar"><div class="w"><div class="row">{btns}</div></div>{viewer}</section>')


def mega(x):
    S, shop = _sector_offers(x)
    ls = ''.join(f'<a href="#hizmet"><span class="mi">{ic(i if _has(i) else "st", 20)}</span><span><b>{t}</b><small>{d}</small></span></a>' for t, d, i in S[:6])
    return (f'<div class="mega" role="region" aria-label="Hizmet menüsü"><div class="ls">{ls}</div>'
            f'<div class="pr"><div><small>Güncel</small><b>Kampanya ve paketleri inceleyin</b></div>'
            f'<a class="btn" href="#firsat">Fırsatlar</a></div></div>')


def deals(x):
    S, shop = _sector_offers(x)
    end = _end()
    rates = (10, 15, 20, 10)
    cards = ''
    for k, (t, d, i) in enumerate(S[:4]):
        cards += (f'<article class="it rv"><span class="bd">%{rates[k]} indirim</span><div class="ph2">{ic(i if _has(i) else "st", 44)}</div><h3>{t}</h3><p>{d}</p>'
                  f'<div class="pz"><b>Fiyat için arayın</b></div><a class="btn" href="#randevu">{"Sipariş ver" if shop else "Fırsattan yararlan"}</a></article>')
    head = ('<span class="eyebrow">' + ('Fırsat ürünleri' if shop else 'Kampanyalar') + '</span><h2>' + ('İndirimli ürünler' if shop else 'Bu döneme özel fırsatlar') + '</h2>'
            '<p>Süre dolmadan yararlanın. Kampanya koşulları için bizi arayın.</p>')
    return _ed('Fırsatlar', f'<section class="sec deal" id="firsat" data-cd-host="1"><div class="w"><div class="sh">{head}</div>'
               f'<div class="tm" data-end="{end}" data-fmt="box" aria-label="Kampanyanın bitmesine kalan süre"></div><div class="gr">{cards}</div></div></section>')


def packages(x):
    S, shop = _sector_offers(x)
    names = [S[k][0] for k in range(min(len(S), 6))]
    tiers = [('Temel', names[:2], False), ('Önerilen', names[:4], True), ('Kapsamlı', names[:6], False)]
    cards = ''
    for t, lst, rc in tiers:
        li = ''.join(f'<li>{ic("ok" if _has("ok") else "st", 18)}<span>{n}</span></li>' for n in lst)
        cards += (f'<article class="it rv{" rc" if rc else ""}">' + ('<span class="tg">Çok tercih edilen</span>' if rc else '') +
                  f'<h3>{t} paket</h3><ul>{li}</ul><a class="btn" href="#randevu">Teklif iste</a></article>')
    head = '<span class="eyebrow">Paketler</span><h2>İhtiyacınıza göre paket seçin</h2><p>Paket içeriği ve fiyat, ihtiyacınıza göre yazılı olarak netleştirilir.</p>'
    return _ed('Paketler', f'<section class="sec pk" id="paket"><div class="w"><div class="sh">{head}</div><div class="gr">{cards}</div></div></section>')


def apply(x, parts):
    """parts: gövde parçaları listesi (nav, drawer, hero, bölümler..., footer, mbar). Yeni bölümleri yerleştirir."""
    x.css('mod.all', CSS)
    nav_kind = x.r.get('nav')
    out = list(parts)
    # hero'dan sonra hikâyeler
    hero_i = 2
    out.insert(hero_i + 1, stories(x))
    # randevu bölümünden önce fırsat + paket
    bi = next((k for k, p in enumerate(out) if 'id="randevu"' in p and 'class="ed"' in p), len(out) - 2)
    out[bi:bi] = [deals(x), packages(x)]
    # duyuru çubuğu (üstü yapışmayan menülerde en üste)
    if nav_kind not in ('min', 'rail'):
        out.insert(0, announce(x))
    out.insert(1 if nav_kind in ('min', 'rail') else 2, mega(x))
    # kayarak belirme: bölümlere rv sınıfı
    out = [p.replace('<section class="sec', '<section class="rv sec') if ('class="sec' in p and 'id="firsat"' not in p and 'id="paket"' not in p and 'id="randevu"' not in p) else p for p in out]
    return out
