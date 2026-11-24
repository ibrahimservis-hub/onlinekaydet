"""İç sayfalara (<!--nxh--> kabuğu olanlar) menünün üstüne kampanya şeridi ekler. Tekrar çalıştırılabilir."""
import pathlib,re
M='<!--KST-->'
HEAD='<link rel="stylesheet" href="/v9/kampanya-serit.css?v=4"><script src="/v9/kampanya.js?v=4" defer></script>'
SERIT=M+'<div class="kst2" data-kamp role="region" aria-label="Kampanya"><div class="in"><span class="et" data-k="bt">KAMPANYA</span><a class="tx" href="/fiyatlar.html#paketler" data-k="strip">7 gün ücretsiz demo · Kart bilgisi gerekmez</a><b data-kc></b><a class="lk" href="/fiyatlar.html#paketler" data-k="cta">Ücretsiz deneyin</a></div><button type="button" aria-label="Kampanya şeridini kapat">×</button></div>'
ATLA={'index.html','fiyatlar.html'}
n=0
for f in pathlib.Path('.').glob('*.html'):
    if f.name in ATLA: continue
    t=f.read_text(encoding='utf-8')
    if '<!--nxh-->' not in t: continue
    t=re.sub(re.escape(M)+r'<div class="kst2".*?</button></div>','',t,flags=re.S)
    t=re.sub(r'<link rel="stylesheet" href="/v9/kampanya-serit\.css[^"]*"><script src="/v9/kampanya\.js[^"]*" defer></script>','',t)
    t=t.replace('<!--nxh-->',SERIT+'<!--nxh-->',1).replace('</head>',HEAD+'</head>',1)
    f.write_text(t,encoding='utf-8');n+=1
print(n,'sayfa')
