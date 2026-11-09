import json,html
import gen7
E=html.escape
ICONS={
'file':'<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4M10 12h5M10 16h5"/>',
'wrench':'<path d="M14.5 6.5a4 4 0 0 0-5 5L4 17l3 3 5.5-5.5a4 4 0 0 0 5-5l-2.5 2.5-2-.5-.5-2z"/>',
'chat':'<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9.5h8M8 12.5h5"/>',
'receipt':'<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/>',
'wallet':'<path d="M3 7h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 7l12-3v3M16 13.5h2"/>',
'chart':'<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
'users':'<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.4 2.7-6 6-6s6 2.6 6 6"/><path d="M16 5a3 3 0 0 1 0 6M18 14c2 .7 3 2.6 3 6"/>',
'globe':'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
'bag':'<path d="M5 8h14l-1 12H6z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
'phone':'<rect x="7" y="2.5" width="10" height="19" rx="2"/><path d="M11 18.5h2"/>',
'shield':'<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
'key':'<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M16 7l3 3"/>',
'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
'camera':'<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
'pen':'<path d="M4 20l1-5L16 4l4 4L9 19z"/><path d="M14 6l4 4"/>',
'list':'<path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01"/>',
'link':'<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
'cart':'<circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M3 4h3l2.5 11h10L21 8H7"/>',
'card':'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M7 15h4"/>',
'table':'<rect x="3" y="4" width="18" height="16" rx="1"/><path d="M3 10h18M3 15h18M9 4v16"/>',
'search':'<circle cx="11" cy="11" r="6.5"/><path d="M16 16l5 5"/>',
'bell':'<path d="M6 17V11a6 6 0 0 1 12 0v6l2 2H4z"/><path d="M10 21h4"/>',
'box':'<path d="M3 8l9-5 9 5v8l-9 5-9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
'map':'<path d="M12 21s7-6 7-11a7 7 0 0 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
'tag':'<path d="M3 12V3h9l9 9-9 9z"/><circle cx="7.5" cy="7.5" r="1.3"/>',
'check':'<circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/>',
'cal':'<rect x="3" y="5" width="18" height="16" rx="1"/><path d="M3 10h18M8 3v4M16 3v4"/>',
'upload':'<path d="M12 16V4M7 9l5-5 5 5M4 20h16"/>',
'star':'<path d="M12 3l2.7 5.8 6.3.8-4.6 4.3 1.2 6.3L12 17l-5.6 3.2 1.2-6.3L3 9.6l6.3-.8z"/>',
}
ARR='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
def ic(n): return '<svg viewBox="0 0 24 24" aria-hidden="true">%s</svg>'%ICONS[n]
FORM_OPTS=''.join('<option>%s</option>'%s for s in ['Kombi','Klima','Beyaz eşya','Elektronik','Bilgisayar','Tesisat','Elektrik','Güvenlik','Diğer'])
def page(fn,title,desc,body,ld='',noindex=True):
    doc=('<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><meta name="theme-color" content="#0a0c0f">'
    '<link rel="icon" href="../favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="../favicon-32.png"><link rel="apple-touch-icon" href="../apple-touch-icon.png">'
    '<title>%s | OnlineKaydet</title><meta name="description" content="%s">%s'
    '<link rel="stylesheet" href="shell.css"><link rel="stylesheet" href="rich.css"></head><body class="o7r">%s<main id="icerik">%s</main>%s%s'
    '<script>document.documentElement.classList.add("js")</script><script src="../site.js"></script><script src="../lead.js"></script><script src="ok7.js"></script></body></html>')%(
    E(title),E(desc),ld,gen7.header(fn),body,gen7.FOOT,gen7.VB)
    open(fn,'w',encoding='utf-8').write(doc)
def crumbs(items):
    out='<a href="index.html">Ana sayfa</a>'
    for h,t in items:
        out+=' <span>/</span> '+('<a href="%s">%s</a>'%(h,E(t)) if h else '<span>%s</span>'%E(t))
    return '<nav class="r7-crumb" aria-label="Sayfa yolu">%s</nav>'%out
def hero(cr,h1,lede,vis='',fine=None,ctas=None):
    ctas=ctas or [('index.html#kayit','Ücretsiz deneyin',''),('tel:05444444004','0544 444 40 04','o')]
    acts=''.join('<a class="btn%s" href="%s">%s</a>'%(' '+c if c else '',h,E(t)) for h,t,c in ctas)
    fn=''.join('<span>%s</span>'%E(x) for x in fine) if fine else ''
    return ('<section class="r7-hero%s"><div class="o7w"><div>%s<h1>%s</h1><p class="lede">%s</p><div class="acts">%s</div>%s</div>%s</div></section>'
        %(' two' if vis else '',crumbs(cr),h1,lede,acts,('<div class="fine">%s</div>'%fn) if fn else '','<div class="vis">%s</div>'%vis if vis else ''))
def strip(items):
    return '<div class="r7-strip"><div class="o7w">%s</div></div>'%''.join('<div class="it"><b>%s</b><span>%s</span></div>'%(a,E(b)) for a,b in items)
def sec(inner,last=False,id=''):
    return '<section class="r7-sec%s"%s><div class="o7w">%s</div></section>'%(' last' if last else '',(' id="%s"'%id) if id else '','%s'%inner)
def head(k,h2,p=''):
    return '<div class="r7-head"><span class="r7-k">%s</span><h2 class="r7-h2">%s</h2>%s</div>'%(E(k),h2,('<p class="r7-p">%s</p>'%p) if p else '')
def split(k,h2,p,bul,vis,rev=False,link=None):
    t='<div class="tx"><span class="r7-k">%s</span><h2>%s</h2><p>%s</p>%s%s</div>'%(E(k),h2,p,('<ul class="r7-ticks">%s</ul>'%''.join('<li>%s</li>'%x for x in bul)) if bul else '',('<a class="r7-link" href="%s">%s%s</a>'%(link[0],E(link[1]),ARR)) if link else '')
    return sec('<div class="r7-split%s">%s<div class="vi">%s</div></div>'%(' rev' if rev else '',t,vis))
def cards(items,cols=3):
    c=''
    for it in items:
        icn,t,p=it[0],it[1],it[2]; href=it[3] if len(it)>3 else None
        inner='<span class="ic">%s</span><h3>%s</h3><p>%s</p>%s'%(ic(icn),E(t),p,'<span class="more">Ayrıntıya bak →</span>' if href else '')
        c+=('<a class="r7-card" href="%s">%s</a>'%(href,inner)) if href else '<div class="r7-card">%s</div>'%inner
    return '<div class="r7-cards%s">%s</div>'%({2:' c2',4:' c4'}.get(cols,''),c)
def steps(items):
    return '<div class="r7-steps" style="--n:%d">%s</div>'%(len(items),''.join('<div class="r7-step"><h3>%s</h3><p>%s</p></div>'%(E(t),p) for t,p in items))
def band(h,p,btn=('index.html#kayit','Ücretsiz deneyin')):
    return sec('<div class="r7-band"><div><h2>%s</h2><p>%s</p></div><a class="btn" href="%s">%s</a></div>'%(h,p,btn[0],E(btn[1])))
def table(head_,rows,hot=None):
    th=''.join('<th%s>%s</th>'%(' class="hot"' if hot is not None and i==hot else '',E(x)) for i,x in enumerate(head_))
    def cell(i,x):
        cls=' class="hot"' if hot is not None and i==hot else ''
        x2='<span class="r7-y">✓</span>' if x=='+' else ('<span class="r7-n">—</span>' if x=='-' else x)
        return '<td%s>%s</td>'%(cls,x2)
    tr=''.join('<tr><th scope="row">%s</th>%s</tr>'%(E(r[0]),''.join(cell(i+1,x) for i,x in enumerate(r[1:]))) for r in rows)
    return '<div class="r7-tw"><table class="r7-tb"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'%(th,tr)
def faq(items):
    return '<div class="r7-faq">%s</div>'%''.join('<details><summary>%s</summary><p>%s</p></details>'%(E(q),a) for q,a in items)
def faq_ld(items):
    import re
    return '<script type="application/ld+json">%s</script>'%json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":re.sub('<[^>]+>','',a)}} for q,a in items]},ensure_ascii=False)
def related(items):
    return '<div class="r7-rel">%s</div>'%''.join('<a href="%s"><b>%s</b><small>%s</small></a>'%(h,E(t),E(s)) for h,t,s in items)
def cta(h='Servis işinizi bu hafta düzene sokalım',p='Formu doldurun, uzmanımız sektörünüze göre kurulumu sizinle birlikte planlasın. İlk ay ücretsiz, kart bilgisi istenmez.'):
    return ('<section id="kayit" class="r7-cta"><div class="o7w"><div><h2>%s</h2><p>%s</p><a class="big" href="tel:05444444004">0544 444 40 04</a></div>'
    '<div class="frm"><div><label for="f1">Ad soyad</label><input id="f1" autocomplete="name"></div><div><label for="f2">Telefon</label><input id="f2" type="tel" autocomplete="tel"></div>'
    '<div><label for="f3">Firma adı</label><input id="f3" autocomplete="organization"></div><div><label for="f4">Sektör</label><select id="f4"><option>Seçiniz</option>%s</select></div>'
    '<a class="bt" href="#">Beni arayın</a><small>Bilgileriniz yalnızca sizinle iletişim için kullanılır (KVKK).</small></div></div></section>')%(h,p,FORM_OPTS)
# ---- mockuplar ----
def mk(title,inner,right=''):
    return '<div class="mk"><div class="bar"><i></i><i></i><i></i><b>%s</b>%s</div>%s</div>'%(E(title),('<em>%s</em>'%E(right)) if right else '',inner)
def mk_list(title,rows,right='Örnek'):
    r=''.join('<div class="row"><div><b>%s</b><small>%s</small></div><span class="chip %s">%s</span></div>'%(E(a),E(b),c,E(d)) for a,b,d,c in rows)
    return mk(title,'<div class="bd">%s</div>'%r,right)
def mk_kv(title,rows,right='Örnek',total=None):
    r='<dl class="kv">%s</dl>'%''.join('<dt>%s</dt><dd>%s</dd>'%(E(k),v) for k,v in rows)
    if total: r+='<div class="tot"><span>%s</span><em>%s</em></div>'%(E(total[0]),E(total[1]))
    return mk(title,r,right)
def mk_chat(title,msgs,right='Örnek'):
    m=''.join('<div class="msg%s"><small>%s</small>%s</div>'%(' me' if me else '',E(w),E(t)) for w,t,me in msgs)
    return mk(title,'<div class="chat">%s</div>'%m,right)
def mk_bars(title,bars,right='Örnek'):
    b=''.join('<div class="brw"><span style="text-align:left">%s</span><i style="--w:%s%%"></i><span>%s</span></div>'%(E(l),w,E(v)) for l,w,v in bars)
    return mk(title,'<div class="bars">%s</div>'%b,right)
def mk_toggles(title,rows,right='Örnek'):
    r=''.join('<div class="tgr"><span>%s</span><span class="sw%s"></span></div>'%(E(l),' on' if on else '') for l,on in rows)
    return mk(title,'<div class="tg">%s</div>'%r,right)
def mk_receipt(lines,sig='Ayşe Yılmaz',title='Servis fişi'):
    r=''
    for l in lines:
        if l=='-': r+='<hr>'
        elif isinstance(l,tuple): r+='<div class="l"><span>%s</span><span>%s</span></div>'%(E(l[0]),E(l[1]))
        else: r+='<div>%s</div>'%E(l)
    r+='<div class="sig">%s</div>'%E(sig)
    return mk(title,'<div class="recp">%s</div>'%r,'A4 · 80 mm')
def phone(title,jobs):
    j=''
    for a,b,btn,o in jobs:
        j+='<div class="jb"><b>%s</b><small>%s</small>%s</div>'%(E(a),E(b),('<span class="bt2%s">%s</span>'%(' o' if o else '',E(btn))) if btn else '')
    return '<div class="ph7"><div class="scr"><div class="st"><span>09:41</span><span>Usta</span></div><div class="tt">%s</div>%s<div style="height:8px"></div></div></div>'%(E(title),j)
