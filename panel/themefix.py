# -*- coding: utf-8 -*-
"""Yayına çıkan her tema sayfasına uygulanan düzeltmeler (önizleme + firma siteleri; eski ve yeni tüm temalar).

1) Kampanya/duyuru çubuğu varken sabit ya da üstte duran menü, çubuğun altına iner (logo/menü örtülmez).
2) Mobil alt çubuğunda '.hl' sınıf çakışması (tüm ekranı kaplayan 'Randevu' düğmesi).
3) Kanıtlanamayan sayılar (müşteri/puan/varış süresi/yıl deneyimi) ve sahte 'canlı durum' kartları kaldırılır:
   firmanın kendi sitesinde olmayan bir rakam yazmak yanıltıcıdır."""
import re

MARK = "<!--okfix-->"

CSS = ("<style id=\"okfix\">select option,select optgroup{background-color:#fff!important;color:#14171c!important}select{color-scheme:light dark}.mb a.hl,.mb1 a.hl{min-height:0!important;align-items:center!important}"
       "@media(max-width:560px){.ann .w{gap:4px 10px!important;padding:6px 44px 6px 12px!important;font-size:.78rem!important}"
       ".ann .cd2 b{padding:4px 5px!important;min-width:28px!important}}</style>")

JS = r"""<script>(function(){var ann=document.querySelector('.ann');if(!ann)return;
var sel='[data-nm="Menü"] header,[data-nm="Menü"]>header,[data-nm="Menü"] .pnv,[data-nm="Menü"]>nav,header.pnv,header#top,.nv,.hd',hs=[],seen=[];
document.querySelectorAll(sel).forEach(function(e){if(ann.contains(e)||seen.indexOf(e)>-1)return;var p=getComputedStyle(e).position;if(p==='static'||p==='relative')return;seen.push(e);e._t0=parseFloat(getComputedStyle(e).top)||0;hs.push(e)});
if(!hs.length)return;
function upd(){var vis=ann.style.display!=='none'&&ann.offsetHeight>0,r=vis?ann.getBoundingClientRect():null,b=vis?Math.max(0,r.bottom):0,h=vis?ann.offsetHeight:0;
hs.forEach(function(e){var p=getComputedStyle(e).position;e.style.top=(e._t0+(p==='absolute'?h:b))+'px'})}
upd();window.addEventListener('scroll',upd,{passive:true});window.addEventListener('resize',upd);
var x=ann.querySelector('.x');if(x)x.addEventListener('click',function(){setTimeout(upd,0)});
})();</script>"""


POP_CSS = ("<style id=\"okpop-css\">#okpop{position:fixed;inset:0;z-index:2147483000;display:none;align-items:flex-start;justify-content:center;background:rgba(10,12,16,.62);"
           "overflow-y:auto;-webkit-overflow-scrolling:touch;padding:max(14px,env(safe-area-inset-top)) 12px 28px}#okpop.on{display:flex}"
           "#okpop .okbox{position:relative;width:100%;max-width:760px;margin:auto;border-radius:18px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.45);animation:okin .22s ease-out}"
           "#okpop .okbox>section{margin:0!important;min-height:0!important}#okpop .okx{position:absolute;top:10px;right:10px;z-index:5;width:44px;height:44px;border-radius:50%;border:0;"
           "background:rgba(0,0,0,.55);color:#fff;font-size:26px;line-height:1;cursor:pointer}#okpop .okx:focus-visible{outline:3px solid #fff;outline-offset:2px}"
           "@keyframes okin{from{opacity:0;transform:translateY(14px) scale(.98)}to{opacity:1;transform:none}}@media(prefers-reduced-motion:reduce){#okpop .okbox{animation:none}}</style>")

POP_JS = r"""<script id="okpopjs">(function(){var sec=document.getElementById('randevu');if(!sec)return;
var ph=document.createComment('okpop'),box,ov;
function build(){ov=document.createElement('div');ov.id='okpop';ov.setAttribute('role','dialog');ov.setAttribute('aria-modal','true');ov.setAttribute('aria-label','Randevu formu');
box=document.createElement('div');box.className='okbox';var x=document.createElement('button');x.type='button';x.className='okx';x.setAttribute('aria-label','Kapat');x.innerHTML='&times;';
box.appendChild(x);ov.appendChild(box);document.body.appendChild(ov);x.addEventListener('click',close);ov.addEventListener('mousedown',function(e){if(e.target===ov)close()})}
var last;function open(e){if(e)e.preventDefault();if(!ov)build();if(!ov.classList.contains('on')){last=document.activeElement;var pc=getComputedStyle(sec.parentNode),sc=getComputedStyle(sec);box.style.color=pc.color;box.style.fontFamily=pc.fontFamily;box.style.fontSize=pc.fontSize;box.style.lineHeight=pc.lineHeight;var bg=sc.backgroundColor;if(!bg||bg==='transparent'||/rgba\(.*, 0\)$/.test(bg))bg=pc.backgroundColor;if(!bg||/rgba\(.*, 0\)$/.test(bg)||bg==='transparent')bg=getComputedStyle(document.body).backgroundColor;box.style.background=bg;sec.parentNode.insertBefore(ph,sec);box.appendChild(sec);ov.classList.add('on');document.documentElement.style.overflow='hidden';
var f=sec.querySelector('input,select,textarea');if(f)setTimeout(function(){f.focus({preventScroll:true})},60)}}
function close(){if(!ov||!ov.classList.contains('on'))return;ov.classList.remove('on');document.documentElement.style.overflow='';if(ph.parentNode)ph.parentNode.insertBefore(sec,ph);if(last&&last.focus)last.focus()}
document.addEventListener('keydown',function(e){if(e.key==='Escape')close()});
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href="#randevu"],a[href="#teklif"],a[href="#bkf"]');if(!a||sec.contains(a)||(ov&&ov.contains(a)))return;
if(a.getAttribute('href')!=='#randevu'&&!document.getElementById(a.getAttribute('href').slice(1)))return;open(e)},true);
if(location.hash==='#randevu'){setTimeout(open,50)}})();</script>"""

# ---- sahte rakamlar
_CELL = re.compile(r'<div><b class="cnt"[^>]*>[^<]*</b><small>(?:Kurulum ve onarım|Ortalama varış|Müşteri puanı|İş garantisi|Çözülen talep|Ortalama yanıt|Memnuniyet)</small></div>')
_GLASS = re.compile(r'<div class="glass"><small>(?:Çözülen talep|Ortalama yanıt)</small><strong>.*?</strong></div>', re.S)
_ASIDE = re.compile(r'<aside class="pcd[^"]*"><small>Canlı durum</small>.*?</aside>', re.S)
_BADGE = re.compile(r'<div class="st">15 yıl<small>Sahada deneyim</small></div>')
_MQ = re.compile(r'<span>✦</span><span>15 YIL DENEYİM</span>')
_LBL = re.compile(r'\s*[·•]\s*15 yıllık deneyim')
_EMPTY = [re.compile(r'<div class="stt">\s*</div>'), re.compile(r'<section class="pst"><div class="w"><div class="g">\s*</div></div></section>')]


def clean_claims(h: str) -> str:
    h = _ASIDE.sub("", h)
    h = _GLASS.sub("", h)
    h = _CELL.sub("", h)
    h = _BADGE.sub("", h)
    h = _MQ.sub("", h)
    h = _LBL.sub("", h)
    for rx in _EMPTY:
        h = rx.sub("", h)
    return h


def fix(h: str) -> str:
    if not h or MARK in h or "</body>" not in h:
        return h
    h = clean_claims(h)
    try:
        import shopdetail
        h = shopdetail.apply(h)
        import realimg
        h = realimg.apply(h)
    except Exception:                                                     # noqa: BLE001
        pass
    h = h.replace("</head>", CSS + POP_CSS + "</head>", 1) if "</head>" in h else h
    i = h.rfind("</body>")
    return h[:i] + MARK + JS + (POP_JS if 'id="randevu"' in h else "") + h[i:]
