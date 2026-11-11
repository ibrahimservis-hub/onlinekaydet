import os
from playwright.sync_api import sync_playwright
H = os.path.dirname(os.path.abspath(__file__))
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    for i, s in enumerate(['bugun', 'takvim', 'kasa', 'ekip', 'rapor', 'site'], 1):
        pg = b.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=1.5)
        pg.goto('file://' + H + '/tasarim.html?s=' + s); pg.wait_for_timeout(400)
        pg.screenshot(path=f'{H}/{i}-{s}.png', full_page=True); pg.close()
    m = b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
    m.goto('file://' + H + '/tasarim.html?s=bugun&m=1'); m.wait_for_timeout(400)
    m.screenshot(path=f'{H}/7-mobil.png'); b.close()
