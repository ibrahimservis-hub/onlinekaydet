import re,colorsys
import sys
FILES=sys.argv[1].split(',')
src=''.join(open('../'+f+'.css').read() for f in FILES)
def parse(h):
    h=h[1:]
    if len(h)in(3,4): h=''.join(c*2 for c in h)
    r,g,b=int(h[0:2],16),int(h[2:4],16),int(h[4:6],16); a=h[6:8] if len(h)==8 else ''
    return r,g,b,a
def hexs(r,g,b,a): return '#%02x%02x%02x%s'%(round(r),round(g),round(b),a)
def lerp(c1,c2,t): return tuple(c1[i]+(c2[i]-c1[i])*t for i in range(3))
INK=(20,22,26);G0=(10,12,15);G2=(22,26,33);IV=(243,240,232);IV2=(233,228,216);BR=(138,109,47);CH=(201,174,117)
def conv(m):
    r,g,b,a=parse(m.group(0))
    h,l,s=colorsys.rgb_to_hls(r/255,g/255,b/255);h*=360
    if s<.10: return m.group(0)
    # warm accents (orange/amber/red-orange)
    if 8<=h<=50 and s>.35:
        if l>.88: c=(245,238,224)
        elif l>.62: c=CH
        else: c=BR
        return hexs(*c,a)
    # blue / violet / indigo family -> graphite or ivory
    if 185<=h<=300:
        if l>.93: c=(247,245,239)
        elif l>.84: c=IV
        elif l>.72: c=(214,208,194)
        elif s>.55 and .38<l<.72: c=BR   # saturated blue accents
        elif l>.5: c=(124,128,136)
        elif l>.3: c=(64,68,76)
        elif l>.14: c=G2
        else: c=G0
        return hexs(*c,a)
    if 95<=h<185 and s>.25:
        if l>.9: c=(238,243,238)
        elif l>.75: c=(214,228,219)
        elif l>.45: c=(111,150,130)
        else: c=(62,98,80)
        return hexs(*c,a)
    return m.group(0)
css=re.sub(r'#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b',conv,src)
css=re.sub(r'rgba?\(\s*(\d+)[ ,]+(\d+)[ ,]+(\d+)',lambda m:'rgba(%s'%','.join(map(str,[m.group(1),m.group(2),m.group(3)])),css) if False else css
css=re.sub(r'border-radius:\s*(\d+)px',lambda m:'border-radius:%dpx'%(min(int(m.group(1)),3) if int(m.group(1))<900 else 2),css)
css=re.sub(r'border-radius:\s*999px','border-radius:2px',css)
css=re.sub(r'box-shadow:(?!none)[^;}]*','box-shadow:none',css)
open('base.'+sys.argv[2]+'.css','w').write(css)
print(len(src),len(css))
