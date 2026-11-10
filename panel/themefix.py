# -*- coding: utf-8 -*-
"""Yayına çıkan her tema sayfasına uygulanan düzeltmeler (önizleme + firma siteleri; eski ve yeni tüm temalar).

1) Kampanya/duyuru çubuğu varken sabit ya da üstte duran menü, çubuğun altına iner (logo/menü örtülmez).
2) Mobil alt çubuğunda '.hl' sınıf çakışması (tüm ekranı kaplayan 'Randevu' düğmesi).
3) Kanıtlanamayan sayılar (müşteri/puan/varış süresi/yıl deneyimi) ve sahte 'canlı durum' kartları kaldırılır:
   firmanın kendi sitesinde olmayan bir rakam yazmak yanıltıcıdır."""
import re

MARK = "<!--okfix-->"

CSS = ("<style id=\"okfix\">.mb a.hl,.mb1 a.hl{min-height:0!important;align-items:center!important}"
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
    h = h.replace("</head>", CSS + "</head>", 1) if "</head>" in h else h
    i = h.rfind("</body>")
    return h[:i] + MARK + JS + h[i:]
