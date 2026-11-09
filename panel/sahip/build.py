"""src.html + ikonlar + logolar -> index.html (tek dosya). Çalıştır: python3 build.py"""
import base64, os, re
H = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(H, "..", "..", "assets")
from PIL import Image
def small(n):
    t = Image.open(os.path.join(A, n)); t = t.resize((420, int(t.height * 420 / t.width)), Image.LANCZOS)
    import io; b = io.BytesIO(); t.save(b, "PNG", optimize=True); return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
icons = re.search(r"const P=\{.*?\};", open(os.path.join(H, "icons.js")).read(), re.S).group(0) if os.path.exists(os.path.join(H, "icons.js")) else ""
src = open(os.path.join(H, "src.html")).read().replace("/*ICONS*/", icons)
src = src.replace('const LOGO="/*LOGO*/";', 'const LOGO_D="%s",LOGO_L="%s";' % (small("ok-logo-acik.png"), small("ok-logo-renkli.png")))
src = src.replace('<img src="${LOGO}" alt="OnlineKaydet">', '<img src="${LOGO_D}" alt="OnlineKaydet">').replace('<img class="lgl" src="${LOGO}"', '<img class="lgl" src="${LOGO_D}"')
import io as _io
_b=_io.BytesIO(); _im=Image.open(os.path.join(A,"giris-gorsel.webp")).convert("RGB"); _im.save(_b,"WEBP",quality=80)
src = src.replace("/*LOGINBG*/", "data:image/webp;base64,"+base64.b64encode(_b.getvalue()).decode())
open(os.path.join(H, "index.html"), "w").write(src)
