"""v7 çıktısından kök (onlinekaydet.com/) paketini üretir: ../ kalkar, noindex kalkar, giriş bağlantıları /uye-girisi olur."""
import os,re,sys,shutil
SRC=os.path.dirname(os.path.abspath(__file__));OUT=sys.argv[1] if len(sys.argv)>1 else '/tmp/v7root'
shutil.rmtree(OUT,ignore_errors=True);os.makedirs(OUT)
for f in os.listdir(SRC):
    p=os.path.join(SRC,f)
    if not os.path.isfile(p) or f.endswith(('.py','.sh','.pyc')) or f.startswith('.'):continue
    if f.endswith('.html'):
        s=open(p,encoding='utf-8').read()
        s=s.replace('="../','="').replace("('../","('").replace('<meta name="robots" content="noindex">','')
        s=s.replace('href="/giris"','href="/uye-girisi"').replace('href="giris"','href="/uye-girisi"')
        open(os.path.join(OUT,f),'w',encoding='utf-8').write(s)
    else:shutil.copy(p,os.path.join(OUT,f))
if os.path.isdir(os.path.join(SRC,'tema')):shutil.copytree(os.path.join(SRC,'tema'),os.path.join(OUT,'tema'))
print(len(os.listdir(OUT)))
