"""entegrasyonlar.html: panel kataloğundaki (panel/entegrasyon.py CATALOG) tüm entegrasyonları gruplu listeler.
Kullanım: python3 site/v9/entegrasyon_katalog.py  (yinelenebilir; işaretli bloğu yeniden yazar)"""
import sys, os, re, html
R = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(R, "panel"))
import entegrasyon as en
E = html.escape
GR = {"pos": ("Sanal POS ve ödeme", "Kartla, havale ile ya da kapıda ödeme alın."),
      "kargo": ("Kargo", "Gönderi oluşturun, takip numarasını müşteriye iletin."),
      "efatura": ("E-fatura ve e-arşiv", "Fatura kesme ve GİB’e iletme."),
      "erp": ("Muhasebe ve ERP", "Stok, cari ve fatura bilgisini ön muhasebe programınızla eşleyin."),
      "sms": ("SMS, WhatsApp ve e-posta", "Müşteriye randevu, sipariş ve kampanya mesajı gönderin."),
      "pazaryeri": ("Pazaryeri ve yemek platformları", "Ürün, sipariş ve stok eşleme; yemek siparişleri tek listede."),
      "olcum": ("Ölçüm, reklam ve giriş", "Ziyaretçi takibi, reklam dönüşümü ve sosyal giriş."),
      "diger": ("Diğer", "İşletmeye özel bağlantılar.")}
ORD = ["pos", "kargo", "efatura", "erp", "sms", "pazaryeri", "olcum", "diger"]
by = {g: [x for x in en.CATALOG if x["group"] == g] for g in ORD}
def ini(n):
    w = re.sub(r"[^A-Za-zÇĞİÖŞÜçğıöşü0-9 ]", "", n).split()
    return E((w[0][0] + (w[1][0] if len(w) > 1 else (w[0][1] if len(w[0]) > 1 else ""))).upper())
CSS = """<style>
.ek{padding:56px 0 8px}.ek .ekh{display:flex;flex-wrap:wrap;gap:12px 28px;align-items:end;justify-content:space-between;margin-bottom:22px}
.ek h2{font-size:clamp(26px,3.4vw,38px);line-height:1.1;margin:0 0 8px;letter-spacing:-.02em}.ek .ekh p{margin:0;max-width:640px;color:#4a5568}
.ek .ekc{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 30px}
.ek .ekc button{font:inherit;font-size:14px;padding:9px 15px;min-height:44px;border:1px solid #d5dbe4;background:#fff;border-radius:999px;cursor:pointer;color:#1f2a3a}
.ek .ekc button[aria-pressed=true]{background:#1d2433;color:#fff;border-color:#1d2433}
.ek .ekg{margin:0 0 36px}.ek .ekg>h3{font-size:20px;margin:0 0 4px}.ek .ekg>p{margin:0 0 14px;color:#5b6677;font-size:15px}
.ek .ekl{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.ek .eki{display:flex;gap:12px;align-items:flex-start;padding:14px;border:1px solid #e1e6ee;border-radius:12px;background:#fff}
.ek .eki b.ik{flex:none;width:40px;height:40px;border-radius:10px;background:#eef2f8;color:#26407a;display:grid;place-items:center;font-size:14px}
.ek .eki strong{display:block;font-size:15px;margin-bottom:2px}.ek .eki span{display:block;font-size:13.5px;line-height:1.4;color:#5b6677}
.ek .ekn{margin:6px 0 0;font-size:14px;color:#5b6677}
@media(max-width:560px){.ek{padding-top:36px}.ek .ekl{grid-template-columns:1fr}}
</style>"""
tot = sum(len(v) for v in by.values())
o = ['<!--EKB-->', CSS, '<section class="ek" id="katalog"><div class="w"><div class="ekh"><div><h2>Bağlanabilen tüm entegrasyonlar</h2><p>Panelin Bağlantı ekranındaki listenin tamamı: %d entegrasyon, %d grup. Her biri için bilgileri siz girersiniz; bağlantıyı panelde “Test et” ile denersiniz.</p></div></div>' % (tot, len(ORD))]
o.append('<div class="ekc" role="group" aria-label="Entegrasyon türü"><button type="button" data-f="" aria-pressed="true">Hepsi (%d)</button>' % tot + "".join('<button type="button" data-f="%s" aria-pressed="false">%s (%d)</button>' % (g, E(GR[g][0]), len(by[g])) for g in ORD) + '</div>')
for g in ORD:
    o.append('<div class="ekg" data-g="%s"><h3>%s</h3><p>%s</p><div class="ekl">' % (g, E(GR[g][0]), E(GR[g][1])))
    for x in by[g]:
        o.append('<div class="eki"><b class="ik" aria-hidden="true">%s</b><div><strong>%s</strong><span>%s</span></div></div>' % (ini(x["name"]), E(x["name"]), E(x.get("desc") or "")))
    o.append('</div></div>')
o.append('<p class="ekn">Listede olmayan bir program ya da servis kullanıyorsanız bize yazın; Webhook / API ile bağlanıp bağlanamayacağını birlikte bakarız.</p></div></section>')
o.append("<script>(function(){var s=document.getElementById('katalog');if(!s)return;var b=s.querySelectorAll('.ekc button'),g=s.querySelectorAll('.ekg');b.forEach(function(x){x.addEventListener('click',function(){b.forEach(function(y){y.setAttribute('aria-pressed',y===x?'true':'false')});var f=x.getAttribute('data-f');g.forEach(function(e){e.style.display=(!f||e.getAttribute('data-g')===f)?'':'none'})})})})();</script><!--/EKB-->")
blok = "\n".join(o)
for p in ("site/entegrasyonlar.html", "site/v9/kaynak/eski/entegrasyonlar.html"):
    p = os.path.join(R, p)
    if not os.path.exists(p): continue
    s = open(p, encoding="utf-8").read()
    s = re.sub(r"<!--EKB-->.*?<!--/EKB-->", "", s, flags=re.S)
    k = s.find('<section class="tint">')
    assert k > 0, p
    s = s[:k] + blok + s[k:]
    open(p, "w", encoding="utf-8").write(s); print("yazıldı", p, tot)
