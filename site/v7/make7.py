import subprocess,re,glob,os
sets={}
for f in glob.glob('../*.html'):
    b=os.path.basename(f)
    if b in('yeni-ana-sayfa.html','a-onizleme.html','index.html') or b.startswith('yon'):continue
    ls=re.findall(r'<link rel="stylesheet" href="([^"]+)\.css"',open(f).read())
    sets['-'.join(ls)]=ls
over=open('inner.over.css').read()
for k,ls in sets.items():
    subprocess.run(['python3','build_css.py',','.join(ls),k],check=True,stdout=subprocess.DEVNULL)
    open('inner.%s.css'%k,'w').write(open('base.%s.css'%k).read()+over)
subprocess.run(['python3','gen7.py'],check=True)
