import asyncio, html as H
from playwright.async_api import async_playwright
I = {
 'user': '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
 'cal': '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
 'scissors': '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4 8.12 15.88M14.47 14.48 20 20M8.12 8.12 12 12"/>',
 'pkg': '<path d="M16.5 9.4 7.5 4.21M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.27 6.96 12 12.01l8.73-5.05M12 22.08V12"/>',
 'truck': '<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.62l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/>',
 'pin': '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
 'file': '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>',
 'check': '<path d="M20 6 9 17l-5-5"/>', 'card': '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
 'phone': '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/>',
 'scale': '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1ZM2 16l3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1ZM7 21h10M12 3v18M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
}
def ic(n, s=18): return f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{I[n]}</svg>'
CSS = '''*{box-sizing:border-box;margin:0}body{width:1440px;height:900px;background:#f3f5f9;font:14px/1.45 "Source Sans 3","Segoe UI",Arial,sans-serif;color:#1c2433;display:flex}
.sb{width:230px;background:#fff;border-right:1px solid #e1e6ee;padding:18px 14px;flex:none}.sb .lg{font-weight:800;font-size:17px;color:#1155cc;margin:2px 8px 4px}.sb small{display:block;margin:0 8px 16px;color:#7a8497;letter-spacing:.1em;font-size:10.5px;text-transform:uppercase}
.sb a{display:flex;gap:10px;align-items:center;padding:9px 10px;border-radius:8px;color:#4b556a;margin-bottom:2px}.sb a.on{background:#e8f0fd;color:#1155cc;font-weight:700}.sb hr{border:0;border-top:1px solid #e9edf3;margin:10px 0}
.main{flex:1;padding:22px 28px;min-width:0}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}.top .bk{color:#667189}.top h1{font-size:25px;margin-top:2px}.top .mt{color:#667189;margin-top:2px}
.btns{display:flex;gap:8px}.b{border:1px solid #d5dbe6;background:#fff;border-radius:8px;padding:8px 13px;font-weight:600;color:#2a3345;display:flex;gap:7px;align-items:center}.b.p{background:#1155cc;border-color:#1155cc;color:#fff}.b.d{color:#b42318}
.st{display:flex;background:#fff;border:1px solid #e1e6ee;border-radius:12px;padding:14px 18px;margin-bottom:16px}.st div{flex:1;display:flex;align-items:center;gap:10px;position:relative;color:#8a93a6}.st div:not(:last-child):after{content:"";flex:1;height:2px;background:#dfe4ec;margin:0 12px}
.st i{width:28px;height:28px;border-radius:50%;border:2px solid #cfd6e2;display:grid;place-items:center;font-style:normal;font-weight:700;font-size:12.5px;flex:none;background:#fff}.st .ok{color:#1b6b3a}.st .ok i{background:#1b8a4b;border-color:#1b8a4b;color:#fff}.st .now{color:#1155cc;font-weight:700}.st .now i{border-color:#1155cc;color:#1155cc;box-shadow:0 0 0 4px #e0ebfd}.st .ok:after{background:#1b8a4b!important}
.g{display:grid;grid-template-columns:1fr 340px;gap:16px}.card{background:#fff;border:1px solid #e1e6ee;border-radius:12px;padding:16px 18px;margin-bottom:14px}.card h3{font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:#6a7488;margin-bottom:11px;display:flex;justify-content:space-between;align-items:center}
.f{display:grid;grid-template-columns:repeat(3,1fr);gap:11px 14px}.f.two{grid-template-columns:repeat(2,1fr)}label{display:block;font-size:12px;color:#6a7488;margin-bottom:4px;font-weight:600}.in{border:1px solid #d5dbe6;border-radius:8px;padding:8px 11px;background:#fff;min-height:37px}.in.ro{background:#f6f8fb}
table{width:100%;border-collapse:collapse}th{text-align:left;font-size:11.5px;color:#7a8497;font-weight:600;padding:6px 8px;border-bottom:1px solid #e6eaf1}td{padding:9px 8px;border-bottom:1px solid #f0f2f7}td.r,th.r{text-align:right}
.tag{display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;font-weight:600;background:#eef2f9;color:#44506a;margin:0 5px 5px 0}.tag.on{background:#e0ebfd;color:#1155cc}.tag.w{background:#fdf1dc;color:#9a5b00}.tag.g{background:#e3f4ea;color:#1b6b3a}
.sum .row{display:flex;justify-content:space-between;padding:6px 0;color:#4b556a}.sum .tot{font-size:22px;font-weight:800;color:#1c2433;border-top:1px solid #e6eaf1;margin-top:6px;padding-top:11px}.pay{display:flex;gap:7px;margin:10px 0}.pay span{flex:1;border:1px solid #d5dbe6;border-radius:8px;padding:8px;text-align:center;font-weight:600;color:#4b556a}.pay .on{border-color:#1155cc;background:#e8f0fd;color:#1155cc}
.big{width:100%;background:#e8710a;color:#fff;border-radius:9px;padding:12px;text-align:center;font-weight:800;font-size:15px;margin-top:6px}.note{background:#fff7e6;border:1px solid #f3dcae;border-radius:9px;padding:10px 12px;color:#7a5200;font-size:13px}
.chk div{display:flex;gap:9px;align-items:center;padding:5px 0}.chk i{width:17px;height:17px;border:1.5px solid #b5bfd0;border-radius:4px;display:grid;place-items:center;flex:none}.chk i.y{background:#1155cc;border-color:#1155cc;color:#fff}
.cap{position:absolute;right:20px;bottom:12px;color:#8a93a6;font-size:12px}'''
def sb(items, on, name, sub):
    h = f'<div class="sb"><div class="lg">{name}</div><small>{sub}</small>'
    for k, (ico, t) in enumerate(items):
        if t == '-': h += '<hr>'; continue
        h += f'<a class="{"on" if t == on else ""}">{ic(ico)}<span>{t}</span></a>'
    return h + '</div>'
def stepper(steps, cur):
    h = '<div class="st">'
    for i, t in enumerate(steps):
        c = 'ok' if i < cur else ('now' if i == cur else '')
        h += f'<div class="{c}"><i>{ic("check",14) if i < cur else i+1}</i><span>{t}</span></div>'
    return h + '</div>'
def fields(lst, cls=''):
    return f'<div class="f {cls}">' + ''.join(f'<div><label>{a}</label><div class="in {"ro" if r else ""}">{b}</div></div>' for a, b, *rest in [(x + (False,))[:3] if len(x) == 2 else x for x in lst] for r in [rest[0]]) + '</div>'
def tbl(head, rows, rcols=()):
    h = '<table><tr>' + ''.join(f'<th class="{"r" if i in rcols else ""}">{x}</th>' for i, x in enumerate(head)) + '</tr>'
    for r in rows: h += '<tr>' + ''.join(f'<td class="{"r" if i in rcols else ""}">{x}</td>' for i, x in enumerate(r)) + '</tr>'
    return h + '</table>'
def page(side, title, meta, btns, steps, cur, left, right, cap):
    b = ''.join(f'<div class="b {c}">{t}</div>' for t, c in btns)
    return f'<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{side}<div class="main"><div class="top"><div><div class="bk">← {cap[0]}</div><h1>{title}</h1><div class="mt">{meta}</div></div><div class="btns">{b}</div></div>{stepper(steps, cur)}<div class="g"><div>{left}</div><div>{right}</div></div></div></body></html>'
def card(t, body, extra=''): return f'<div class="card"><h3>{t}{extra}</h3>{body}</div>'
def tags(l, on=()): return ''.join(f'<span class="tag {"on" if x in on else ""}">{x}</span>' for x in l)
def sumcard(rows, total, pay, btn, extra=''):
    return card('Hesap', '<div class="sum">' + ''.join(f'<div class="row"><span>{a}</span><span>{b}</span></div>' for a, b in rows) + f'<div class="row tot"><span>Toplam</span><span>{total}</span></div></div><div class="pay">' + ''.join(f'<span class="{"on" if p == pay else ""}">{p}</span>' for p in ('Nakit', 'Kart', 'Havale')) + f'</div><div class="big">{btn}</div>') + extra

P = {}
# 1 KUAFOR / RANDEVU
P['1-randevu-kuafor'] = page(
 sb([('cal','Randevu Defteri'),('user','Müşteriler'),('scissors','Hizmet ve Fiyatlar'),('pkg','Ürün ve Sarf Stoku'),('cal','Günün Randevuları'),('-','-'),('user','Uzmanlar'),('card','Uzman Primleri'),('file','Raporlar')], 'Randevu Defteri', 'Demo Kuaför', 'YÖNETİM PANELİ'),
 'Randevu RD-1042', 'Ayşe Yıldız · 0541 373 27 45 · bugün 14:30 – 16:00 · Koltuk 2', [('Müşteriye mesaj',''),('Ertele',''),('Gelmedi','d'),('Kaydet','p')],
 ['Randevu alındı','Geldi','İşlemde','Ödeme','Tamamlandı'], 2,
 card('Müşteri ve randevu', fields([('Müşteri','Ayşe Yıldız'),('Uzman','Murat Kaya'),('Koltuk','Koltuk 2'),('Tarih','10 Kas 2026'),('Başlangıç','14:30'),('Süre','90 dk'),('Müşteri kaynağı','Telefon'),('Hatırlatma SMS','1 saat önce')]))
 + card('Hizmetler', tbl(['Hizmet','Uzman','Süre','Fiyat'], [('Boya – kök dipleri','Murat Kaya','60 dk','1.200,00 ₺'),('Fön ve şekillendirme','Murat Kaya','30 dk','250,00 ₺')], (3,)) + '<div style="margin-top:10px;color:#1155cc;font-weight:600">+ Hizmet ekle</div>')
 + card('Kullanılan ürün', tbl(['Ürün','Miktar','Tutar'], [('Boya 7.1 (60 ml) + oksidan','1','180,00 ₺')], (2,)))
 + card('Müşteri kartı', f'<div class="chk"><div><i class="y">{ic("check",12)}</i>Alerji / hassasiyet sorusu soruldu</div><div><i class="y">{ic("check",12)}</i>Önceki boya formülü kartta</div><div><i></i>İşlem sonrası fotoğraf (isteğe bağlı)</div></div><div style="margin-top:8px"><label>Formül / not</label><div class="in" style="min-height:52px">7.1 + 20 vol (1:1.5), 35 dk bekleme. Geçen sefer ucu fazla açtı.</div></div>'),
 sumcard([('Hizmetler','1.450,00 ₺'),('Ürün','180,00 ₺'),('İndirim (sadakat)','−100,00 ₺')], '1.530,00 ₺', 'Kart', 'Ödemeyi al ve kapat')
 + card('Uzman primi', '<div class="sum"><div class="row"><span>Murat Kaya · hizmet primi %30</span><span>435,00 ₺</span></div><div class="row"><span>Ürün satışı primi %10</span><span>0,00 ₺</span></div></div>')
 + card('Sonraki randevu', '<div class="note">Kök boya 5–6 hafta sonra. Önerilen: 22 Ara, 14:00</div>'),
 ('Randevu Defteri',))
# 2 SIPARIS / TEKSTIL
P['2-siparis-tekstil'] = page(
 sb([('pkg','Siparişler'),('user','Müşteriler'),('pkg','Ürünler ve Stok'),('truck','Kargo Takibi'),('card','İade ve Değişim'),('-','-'),('file','Faturalar'),('card','Tahsilat'),('file','Raporlar')], 'Siparişler', 'Demo Tekstil', 'YÖNETİM PANELİ'),
 'Sipariş SP-3081', 'İplik Perakende Ltd. · 0532 118 40 22 · web sitesinden · 10 Kas 2026 11:42', [('Fatura kes',''),('Yazdır',''),('İptal / İade','d'),('Kaydet','p')],
 ['Yeni sipariş','Ödeme onayı','Hazırlanıyor','Kargoda','Teslim edildi'], 2,
 card('Sipariş kalemleri', tbl(['Ürün','Beden / Renk','Adet','Birim','Tutar'], [('Penye tişört (12\'li koli)','S-M-L / Lacivert','3 koli','1.260,00 ₺','3.780,00 ₺'),('Eşofman altı (10\'lu koli)','M-L / Antrasit','2 koli','1.840,00 ₺','3.680,00 ₺'),('Çorap seti (24\'lü)','Standart / Karışık','4','310,00 ₺','1.240,00 ₺')], (2,3,4)) + '<div style="margin-top:10px;color:#1155cc;font-weight:600">+ Ürün ekle · Stoktan seç</div>')
 + card('Teslimat', fields([('Teslim alan','Selin Arda'),('Telefon','0532 118 40 22'),('Adres','Organize Sanayi 4. Cd. No:18, Bursa',False),('Kargo firması','Yurtiçi Kargo'),('Takip no','YK 7745 2210 38'),('Tahmini teslim','12 Kas 2026')]))
 + card('Paketleme', f'<div class="chk"><div><i class="y">{ic("check",12)}</i>Stok düşüldü (3 kalem)</div><div><i class="y">{ic("check",12)}</i>Koli etiketi basıldı</div><div><i></i>Kargo barkodu</div><div><i></i>Fatura koliye eklendi</div></div>')
 + card('Not', '<div class="in" style="min-height:48px">Faturaya "toptan satış" notu eklensin. Cuma gününe kadar sevk.</div>'),
 sumcard([('Ara toplam','8.700,00 ₺'),('Toplu alım indirimi %5','−435,00 ₺'),('KDV %10','827,00 ₺'),('Kargo','0,00 ₺')], '9.092,00 ₺', 'Havale', 'Kargoya ver')
 + card('Ödeme', '<div class="sum"><div class="row"><span>Havale / EFT</span><span class="tag g">Onaylandı</span></div><div class="row"><span>Banka açıklaması</span><span>SP-3081</span></div></div>')
 + card('İade koşulu', '<div class="note">Teslimden sonra 14 gün içinde iade. Kolide hasar varsa fotoğraflı bildirim.</div>'),
 ('Siparişler',))
# 3 YOL / CEKICI
P['3-yol-cekici'] = page(
 sb([('phone','Çağrılar'),('truck','Araç ve Sürücüler'),('pin','Canlı Harita'),('user','Müşteriler'),('card','Kasa ve Tahsilat'),('-','-'),('file','Anlaşmalı Servisler'),('file','Sigorta Dosyaları'),('file','Raporlar')], 'Çağrılar', 'Demo Çekici', 'YÖNETİM PANELİ'),
 'Çağrı CK-2207', 'Mehmet Kaya · 0541 888 01 22 · 10 Kas 2026 18:51 · telefon', [('Konum SMS gönder',''),('Sürücüyü ara',''),('İptal','d'),('Kaydet','p')],
 ['Çağrı alındı','Araç yönlendirildi','Yolda','Yükleme / Taşıma','Teslim edildi'], 2,
 card('Araç ve sorun', fields([('Plaka','06 ABC 482'),('Araç','Fiat Egea 1.4'),('Araç durumu','Çalışmıyor, vites boşta'),('Sorun','Akü bitti'),('Yardım türü','Çekici'),('Sigorta','Yok')]) + '<div style="margin-top:10px">' + tags(['Kaza sonrası','Akü bitti','Lastik patlak','Yakıt bitti','Kilitli kaldı'], ('Akü bitti',)) + '</div>')
 + card('Güzergâh', '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px"><div><label>Alış noktası</label><div class="in">Eskişehir Yolu 7. km, Ankara</div></div><div><label>Bırakış noktası</label><div class="in">Anlaşmalı servis – Ostim</div></div></div><svg viewBox="0 0 640 110" style="width:100%;margin-top:10px;background:#eef2f9;border-radius:8px"><path d="M40 78 C170 20 250 96 360 52 S560 30 600 40" fill="none" stroke="#1155cc" stroke-width="4" stroke-linecap="round" stroke-dasharray="1 9"/><circle cx="40" cy="78" r="8" fill="#e8710a"/><circle cx="600" cy="40" r="8" fill="#1b8a4b"/></svg><div style="display:flex;gap:26px;margin-top:8px;color:#4b556a"><span><b>18,4 km</b> mesafe</span><span><b>~32 dk</b> tahmini süre</span><span><b>Sürücü:</b> Hasan Demir · 06 CK 441</span></div>')
 + card('Yükleme kontrolü', f'<div class="chk"><div><i class="y">{ic("check",12)}</i>Araç fotoğrafı (önden / arkadan)</div><div><i class="y">{ic("check",12)}</i>Mevcut hasar işaretlendi</div><div><i></i>Teslim imzası</div></div>'),
 sumcard([('Çekici çıkış','350,00 ₺'),('Kilometre (18,4 km × 22 ₺)','404,80 ₺'),('Gece tarifesi','0,00 ₺'),('Otoyol / köprü','0,00 ₺')], '754,80 ₺', 'Nakit', 'Teslim et ve tahsil et')
 + card('Sürücü primi', '<div class="sum"><div class="row"><span>Hasan Demir · %25</span><span>188,70 ₺</span></div></div>')
 + card('Müşteri', '<div class="note">Konum linki SMS ile gönderildi. Müşteri sürücüyü haritada izleyebilir.</div>'),
 ('Çağrılar',))
# 4 PROJE / AVUKAT
P['4-proje-avukat'] = page(
 sb([('scale','Dosyalar'),('user','Müvekkiller'),('cal','Duruşma Takvimi'),('file','Evrak Arşivi'),('card','Vekalet Ücretleri'),('-','-'),('file','Süre Takibi'),('user','Avukatlar'),('file','Raporlar')], 'Dosyalar', 'Demo Hukuk Bürosu', 'YÖNETİM PANELİ'),
 'Dosya 2026/118', 'Fatma Demir · 0532 441 90 77 · Boşanma (anlaşmalı) · açılış 02 Eki 2026', [('Müvekkile mesaj',''),('Evrak ekle',''),('Dosyayı kapat','d'),('Kaydet','p')],
 ['Görüşme','Vekalet','Dava açıldı','Duruşma','Karar / kapanış'], 3,
 card('Dosya bilgisi', fields([('Dosya türü','Boşanma – anlaşmalı'),('Mahkeme','Ankara 7. Aile Mahkemesi'),('Esas no','2026/412'),('Karşı taraf','Ali Demir'),('Sorumlu avukat','Av. Selin Aydın'),('Karşı vekil','Av. Kemal Tuna')]))
 + card('Duruşmalar ve süreler', tbl(['Tarih','İşlem','Durum'], [('18 Kas 2026 · 10:30','Ön inceleme duruşması','<span class="tag w">Yaklaşıyor</span>'),('05 Kas 2026','Dilekçe cevap süresi','<span class="tag g">Verildi</span>'),('02 Ara 2026','Tanık listesi son gün','<span class="tag">Bekliyor</span>')]))
 + card('Evrak listesi', f'<div class="chk"><div><i class="y">{ic("check",12)}</i>Vekâletname (noter onaylı)</div><div><i class="y">{ic("check",12)}</i>Nüfus kayıt örneği</div><div><i class="y">{ic("check",12)}</i>Protokol imzalı</div><div><i></i>Mal paylaşımı belgeleri</div></div>')
 + card('Dosya notu', '<div class="in" style="min-height:52px">Müvekkil çocuğun velayetinde mutabık. Protokolde nafaka tutarı netleşecek.</div>'),
 sumcard([('Vekalet ücreti','36.000,00 ₺'),('Tahsil edilen','24.000,00 ₺'),('Kalan','12.000,00 ₺')], '12.000,00 ₺', 'Havale', 'Tahsilat ekle').replace('>Toplam<','>Kalan bakiye<')
 + card('Taksit planı', tbl(['Tarih','Tutar','Durum'], [('02 Eki','12.000 ₺','<span class="tag g">Ödendi</span>'),('02 Kas','12.000 ₺','<span class="tag g">Ödendi</span>'),('02 Ara','12.000 ₺','<span class="tag w">Bekliyor</span>')], (1,)))
 + card('Hatırlatma', '<div class="note">Duruşmadan 2 gün önce müvekkile SMS gider.</div>'),
 ('Dosyalar',))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 1440, 'height': 900})
        for k, h in P.items():
            await pg.set_content(h); await pg.wait_for_timeout(250)
            await pg.screenshot(path=f'{k}.png')
        await b.close()
asyncio.run(main())
