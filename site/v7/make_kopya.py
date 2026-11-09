import sys
def patch(h):
    n=0
    def rep(a,b):
        nonlocal h,n
        assert a in h,a
        h=h.replace(a,b,1); n+=1
    rep('</head>','<meta name="robots" content="noindex,nofollow"><link rel="stylesheet" href="kopya-v7.css"></head>')
    rep('<div class="con" id="con"','<p class="k-note"><b>İlk ay ücretsiz</b> · Kart bilgisi istenmez · Kurulum bizden</p><div class="con" id="con"')
    rep('<label for="f1">Ad soyad</label>','<label for="f1">Ad soyad<i aria-hidden="true">*</i></label>')
    rep('<label for="f2">Telefon</label>','<label for="f2">Telefon<i aria-hidden="true">*</i></label>')
    rep('<script>document.documentElement.classList.add("js")</script>','<a class="k-wa" href="https://wa.me/905444444004?text=Merhaba%2C%20OnlineKaydet%20hakk%C4%B1nda%20bilgi%20almak%20istiyorum." rel="noopener" target="_blank">WhatsApp ile yazın</a><script>document.documentElement.classList.add("js")</script>')
    return h
if __name__=='__main__':
    h=open(sys.argv[1],encoding='utf-8').read(); open(sys.argv[2],'w',encoding='utf-8').write(patch(h)); print('ok')
