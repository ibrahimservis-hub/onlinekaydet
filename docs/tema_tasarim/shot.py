import os,sys
from playwright.sync_api import sync_playwright
H=os.path.dirname(os.path.abspath(__file__));O=os.path.join(H,'out')
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    for k in ['kuafor','cekici','avukat','eticaret']:
        pg=b.new_page(viewport={'width':1440,'height':900});pg.goto('file://'+O+'/'+k+'.html');pg.wait_for_timeout(500)
        pg.add_style_tag(content='.rv{opacity:1!important;transform:none!important}.tick div{animation:none!important;padding-left:0!important}')
        h=pg.evaluate('document.documentElement.scrollHeight');print(k,h)
        pg.screenshot(path=f'{O}/{k}-1.png',clip={'x':0,'y':0,'width':1440,'height':900})
        pg.evaluate('window.scrollTo(0,0)')
        pg.screenshot(path=f'{O}/{k}-tam.png',full_page=True)
        m=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);m.goto('file://'+O+'/'+k+'.html');m.wait_for_timeout(400)
        m.add_style_tag(content='.rv{opacity:1!important;transform:none!important}.tick div{animation:none!important;padding-left:0!important}')
        m.screenshot(path=f'{O}/{k}-mob.png')
    b.close()
